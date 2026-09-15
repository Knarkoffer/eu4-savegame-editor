"""Edit uncompressed Europa Universalis IV save files."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

VERSION = "1.0.0"
SAVE_ENCODING = "cp1252"
SAVE_SUFFIX = ".eu4"


class SaveGameError(Exception):
    """Raised when a save file cannot be located, read, or understood."""


@dataclass(frozen=True)
class EditOptions:
    """Requested save-game edits."""

    add_gold: float | None = None
    monarch_points: bool = False
    remove_cores: bool = False
    naturalize: bool = False
    stabilize: bool = False
    prestigious: bool = False
    gifted_monarch: bool = False
    maximize_army: bool = False

    @property
    def has_edits(self) -> bool:
        return self.add_gold is not None or any(
            (
                self.monarch_points,
                self.remove_cores,
                self.naturalize,
                self.stabilize,
                self.prestigious,
                self.gifted_monarch,
                self.maximize_army,
            )
        )


@dataclass(frozen=True)
class PlayerCountry:
    """Player-controlled country details read from a save."""

    tag: str
    name: str
    culture: str


def smart_print(message: str, *, verbose_only: bool, verbose: bool) -> None:
    """Print a message unless it is suppressed by the verbosity setting."""

    if not verbose_only or verbose:
        print(message)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--path",
        default="",
        help="directory containing save files; the newest .eu4 file is selected",
    )
    parser.add_argument(
        "-f",
        "--file",
        default="",
        help="specific .eu4 save file to edit",
    )
    parser.add_argument(
        "-ag",
        "--add-gold",
        "--addGold",
        dest="add_gold",
        help="amount of gold to add to the treasury",
    )
    parser.add_argument(
        "-mp",
        "--monarch-points",
        "--monarchPoints",
        dest="monarch_points",
        action="store_true",
        help="set administrative, diplomatic, and military points to 999",
    )
    parser.add_argument(
        "-dc",
        "--de-core",
        "--deCore",
        dest="remove_cores",
        action="store_true",
        help="remove foreign cores from provinces owned by the player",
    )
    parser.add_argument(
        "-nl",
        "--naturalize",
        action="store_true",
        help="change owned provinces to the player's primary culture",
    )
    parser.add_argument(
        "-sl",
        "--stabilize",
        action="store_true",
        help="set stability to 3 and legitimacy to 100",
    )
    parser.add_argument(
        "-pr",
        "--prestigious",
        action="store_true",
        help="set prestige to 100",
    )
    parser.add_argument(
        "-gm",
        "--gifted-monarch",
        "--giftedmonarch",
        dest="gifted_monarch",
        action="store_true",
        help="set the current monarch's attributes to 9",
    )
    parser.add_argument(
        "-ma",
        "--maximize-army",
        "--maximizearmy",
        dest="maximize_army",
        action="store_true",
        help="maximize manpower and sailors",
    )
    parser.add_argument(
        "-a",
        "--all",
        dest="edit_all",
        action="store_true",
        help="apply every supported edit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print additional details",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )
    return parser


def options_from_args(args: argparse.Namespace) -> EditOptions:
    """Translate parsed arguments into edit options."""

    if args.edit_all:
        return EditOptions(
            add_gold=150_000.0,
            monarch_points=True,
            remove_cores=True,
            naturalize=True,
            stabilize=True,
            prestigious=True,
            gifted_monarch=True,
            maximize_army=True,
        )

    # The original script ignores invalid gold while still applying other edits.
    # Keep conversion after --all, which overrides even an invalid gold value.
    add_gold = None
    if args.add_gold is not None:
        try:
            add_gold = float(args.add_gold)
        except ValueError:
            print("Gold amount must be a number; ignoring the gold option")

    return EditOptions(
        add_gold=add_gold,
        monarch_points=args.monarch_points,
        remove_cores=args.remove_cores,
        naturalize=args.naturalize,
        stabilize=args.stabilize,
        prestigious=args.prestigious,
        gifted_monarch=args.gifted_monarch,
        maximize_army=args.maximize_army,
    )


def default_windows_save_directory() -> Path | None:
    """Return the default Windows EU4 save directory when available."""

    if sys.platform != "win32":
        return None

    try:
        import winreg

        key_path = (
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            documents, _ = winreg.QueryValueEx(key, "Personal")
    except OSError:
        return None

    documents_path = Path(os.path.expandvars(documents))
    return (
        documents_path / "Paradox Interactive" / "Europa Universalis IV" / "save games"
    )


def select_save_file(file_name: str, directory_name: str) -> Path:
    """Resolve an explicitly selected save or the newest save in a directory."""

    if file_name:
        save_file = Path(file_name).expanduser()
        if not save_file.is_file():
            raise SaveGameError(
                f'File supplied with --file does not exist: "{save_file}"'
            )
        if save_file.suffix.lower() != SAVE_SUFFIX:
            raise SaveGameError("The selected file must have the .eu4 extension")
        return save_file

    if directory_name:
        save_directory = Path(directory_name).expanduser()
        if not save_directory.is_dir():
            raise SaveGameError(f'Save directory does not exist: "{save_directory}"')
    else:
        default_directory = default_windows_save_directory()
        local_directory = Path(__file__).resolve().parent / "save games"

        if default_directory is not None and default_directory.is_dir():
            save_directory = default_directory
        elif local_directory.is_dir():
            save_directory = local_directory
        else:
            raise SaveGameError(
                "No save directory was found; supply one with --path or --file"
            )

    save_files = list(save_directory.glob(f"*{SAVE_SUFFIX}"))
    if not save_files:
        raise SaveGameError(f'No .eu4 saves exist in "{save_directory}"')

    return max(save_files, key=lambda path: path.stat().st_ctime)


def assure_valid_savefile(path: Path) -> bool:
    """Return whether a path looks like an uncompressed EU4 save."""

    if path.suffix.lower() != SAVE_SUFFIX:
        return False

    try:
        with path.open(encoding=SAVE_ENCODING) as save_file:
            return save_file.readline().strip() == "EU4txt"
    except (OSError, UnicodeError):
        return False


def read_save(path: Path) -> list[str]:
    """Read a save while retaining line endings."""

    try:
        with path.open(encoding=SAVE_ENCODING) as save_file:
            return save_file.readlines()
    except (OSError, UnicodeError) as error:
        raise SaveGameError(f'Could not read save file "{path}": {error}') from error


def write_save(path: Path, lines: Iterable[str]) -> None:
    """Write an edited save using the encoding expected by EU4."""

    try:
        with path.open("w", encoding=SAVE_ENCODING, newline="") as save_file:
            save_file.writelines(lines)
    except (OSError, UnicodeError) as error:
        raise SaveGameError(f'Could not write edited save "{path}": {error}') from error


def assignment_value(line: str, name: str) -> str:
    """Extract a value using the legacy script's exact string operations."""

    return line.strip().replace(f"{name}=", "").replace('"', "").strip()


def country_line_indices(lines: Sequence[str], country_tag: str) -> Iterable[int]:
    """Yield line indexes inside the player country's top-level block."""

    in_country = False
    country_header = f"\t{country_tag}={{\n"

    for index, line in enumerate(lines):
        if (
            index > 0
            and line.startswith("\t\thuman=yes")
            and lines[index - 1] == country_header
        ):
            in_country = True

        if in_country and line == "\t}\n":
            in_country = False
        elif in_country:
            yield index


def identify_player_country(lines: Sequence[str]) -> PlayerCountry:
    """Read the player country tag, display name, and primary culture."""

    if len(lines) < 5:
        raise SaveGameError("The save is too short to contain player country details")

    country_tag = assignment_value(lines[3], "player")
    country_name = assignment_value(lines[4], "displayed_country_name")
    culture = ""
    in_country = False

    for index, line in enumerate(lines):
        if f"\t{country_tag}={{" in line and "human=yes" in str(lines[index + 1]):
            in_country = True

        if in_country and "\tprimary_culture=" in line:
            culture = assignment_value(line, "primary_culture")
            break

    if not culture:
        raise SaveGameError(f"Could not find the primary culture for {country_name}")

    return PlayerCountry(country_tag, country_name, culture)


def edit_monarch_points(
    lines: list[str], country: PlayerCountry, *, verbose: bool
) -> bool:
    """Set the player's administrative, diplomatic, and military points to 999."""

    print("-mp switch used, setting monarch points (ADM, DIP, MIL)\n")
    marker_indexes = [
        index for index, line in enumerate(lines) if "interesting_countries={" in line
    ]
    if not marker_indexes or marker_indexes[-1] < 2:
        raise SaveGameError("Could not locate monarch points")

    points_index = marker_indexes[-1] - 2
    raw_points = lines[points_index].strip().split(" ")
    if len(raw_points) < 3:
        raise SaveGameError("Could not understand the monarch-points line")

    try:
        # Only the first three tokens control the legacy replacement operations.
        current_points = tuple(int(point) for point in raw_points[:3])
    except ValueError as error:
        raise SaveGameError("Could not understand the monarch-points values") from error

    target_points = (999, 999, 999)
    if sum(current_points) >= sum(target_points):
        smart_print(
            f"\t{country.name} already had maximum monarch points",
            verbose_only=True,
            verbose=verbose,
        )
        return False

    updated_line = lines[points_index]
    for current_point, target_point in zip(current_points, target_points, strict=True):
        updated_line = updated_line.replace(str(current_point), str(target_point))
    lines[points_index] = updated_line

    smart_print(
        "\tMonarch points changed from "
        f"ADM {current_points[0]}, DIP {current_points[1]}, MIL {current_points[2]} "
        "to 999 each\n",
        verbose_only=False,
        verbose=verbose,
    )
    return True


def remove_foreign_cores(
    lines: list[str], country: PlayerCountry, *, verbose: bool
) -> bool:
    """Remove other countries' cores from player-owned provinces."""

    del verbose
    print("-dc switch used, removing foreign cores from owned provinces\n")
    owned_province = False
    province_name = ""
    owned_count = 0
    edited_count = 0

    for index, current_line in enumerate(lines):
        if index > 0 and 'owner="' in current_line and 'name="' in lines[index - 1]:
            province_name = assignment_value(lines[index - 1], "name")
            owned_province = f'"{country.tag}"' in current_line
            if owned_province:
                owned_count += 1

        if owned_province and index > 0 and lines[index - 1].rstrip() == "\t\tcores={":
            foreign_cores = [
                tag for tag in current_line.strip().split() if tag != country.tag
            ]
            for tag in foreign_cores:
                print(f"\t{province_name} had a core from {tag} removed")
                lines[index] = lines[index].replace(tag, "")
            lines[index] = lines[index].replace(" ", "")
            if foreign_cores:
                edited_count += 1

    print(
        f"\n\tA total of {edited_count} of {owned_count} owned provinces were de-cored\n"
    )
    return edited_count > 0


def naturalize_provinces(
    lines: list[str], country: PlayerCountry, *, verbose: bool
) -> bool:
    """Change player-owned provinces to the player's primary culture."""

    print("-nl switch used, naturalizing owned provinces\n")
    print(f"\tPrimary culture identified as {country.culture}\n")
    owned_province = False
    province_fixed = False
    province_name = ""
    owned_count = 0
    edited_count = 0

    for index, current_line in enumerate(lines):
        if index > 0 and '\towner="' in current_line and 'name="' in lines[index - 1]:
            province_name = assignment_value(lines[index - 1], "name")
            owned_province = f'"{country.tag}"' in current_line
            province_fixed = not owned_province
            if owned_province:
                owned_count += 1

        if (
            not owned_province
            or province_fixed
            or not current_line.startswith("\t\tculture=")
        ):
            continue
        if index == 0 or index + 1 >= len(lines):
            continue
        if not lines[index - 1].startswith("\t\toriginal_culture="):
            continue
        if not lines[index + 1].startswith("\t\treligion="):
            continue

        if current_line.strip() == f"culture={country.culture}":
            province_fixed = True
            continue

        # Quotes and spaces are significant here: replace the raw legacy value.
        current_culture = current_line.strip().split("=")[1].strip()
        lines[index] = current_line.replace(current_culture, country.culture)
        readable_culture = " ".join(
            word.capitalize() for word in current_culture.split("_")
        )
        smart_print(
            f"\t{province_name} ({readable_culture}) found",
            verbose_only=False,
            verbose=verbose,
        )
        province_fixed = True
        edited_count += 1

    if edited_count:
        print(
            f"\n\tA total of {edited_count} of {owned_count} owned provinces were naturalized\n"
        )
    else:
        smart_print(
            "No provinces needed naturalizing",
            verbose_only=True,
            verbose=verbose,
        )
    return edited_count > 0


def improve_monarch(lines: list[str], country: PlayerCountry, *, verbose: bool) -> bool:
    """Set the current monarch's DIP, ADM, and MIL attributes to 9."""

    print("-gm switch used, improving the current monarch\n")
    monarch_line: int | None = None
    monarch_name = ""

    for index in country_line_indices(lines, country.tag):
        if "\their={" in lines[index] and country.tag in lines[index + 6]:
            monarch_line = index + 5
            monarch_name = assignment_value(lines[monarch_line], "name")
            smart_print(
                f"Found monarch {monarch_name} at line {index + 1}",
                verbose_only=True,
                verbose=verbose,
            )

    if monarch_line is None:
        smart_print(
            f"Could not find a monarch for {country.name}",
            verbose_only=True,
            verbose=verbose,
        )
        return False

    stat_lines = {
        "DIP": monarch_line + 2,
        "ADM": monarch_line + 3,
        "MIL": monarch_line + 4,
    }
    current_stats = {
        stat: int(assignment_value(lines[index], stat))
        for stat, index in stat_lines.items()
    }
    if sum(current_stats.values()) >= 27:
        smart_print(
            f"No need to edit monarch {monarch_name}",
            verbose_only=True,
            verbose=verbose,
        )
        return False

    for stat, index in stat_lines.items():
        lines[index] = lines[index].replace(str(current_stats[stat]), "9")

    smart_print(
        f"\tMonarch {monarch_name} changed from ADM {current_stats['ADM']}, "
        f"DIP {current_stats['DIP']}, MIL {current_stats['MIL']} to 9 each\n",
        verbose_only=False,
        verbose=verbose,
    )
    return True


def add_treasury_gold(
    lines: list[str], country: PlayerCountry, amount: float, *, verbose: bool
) -> bool:
    """Add an amount to the player's treasury."""

    print("-ag switch used, adding gold to the treasury\n")
    edited = False

    for index in country_line_indices(lines, country.tag):
        if index == 0 or index + 1 >= len(lines):
            continue
        current_line = lines[index]
        if not (
            current_line.startswith("\t\ttreasury=")
            and lines[index - 1].startswith("\t\tstability=")
            and lines[index + 1].startswith("\t\testimated_monthly_income=")
        ):
            continue

        current_treasury = float(current_line.strip().replace("treasury=", ""))
        target_treasury = round(current_treasury + amount, 3)
        current_text = str(current_treasury)
        amount_text = str(float(amount))
        target_text = str(target_treasury)
        lines[index] = current_line.replace(current_text, target_text)
        smart_print(
            f"\t{country.name} had {current_text} gold; added {amount_text} for a "
            f"new treasury of {target_treasury}\n",
            verbose_only=False,
            verbose=verbose,
        )
        edited = True

    return edited


def stabilize_country(
    lines: list[str], country: PlayerCountry, *, verbose: bool
) -> bool:
    """Set the player's stability and legitimacy to their maximum values."""

    print("-sl switch used, stabilizing the country\n")
    edited = False

    for index in country_line_indices(lines, country.tag):
        if index == 0 or index + 1 >= len(lines):
            continue
        current_line = lines[index]

        if (
            current_line.startswith("\t\tstability=")
            and lines[index - 1].startswith("\t\tprestige=")
            and lines[index + 1].startswith("\t\ttreasury=")
        ):
            current_stability = assignment_value(current_line, "stability")
            if current_stability != "3.000":
                lines[index] = current_line.replace(current_stability, "3.000")
                smart_print(
                    f"\t{country.name} stability changed from {current_stability} to 3.000\n",
                    verbose_only=False,
                    verbose=verbose,
                )
                edited = True
            else:
                smart_print(
                    f"\t{country.name} already had maximum stability",
                    verbose_only=True,
                    verbose=verbose,
                )

        if (
            current_line.startswith("\t\tlegitimacy=")
            and lines[index - 1].startswith("\t\troot_out_corruption_slider=")
            and lines[index + 1].startswith("\t\tmercantilism=")
        ):
            current_legitimacy = assignment_value(current_line, "legitimacy")
            if current_legitimacy != "100.000":
                lines[index] = current_line.replace(current_legitimacy, "100.000")
                smart_print(
                    f"\t{country.name} legitimacy changed from "
                    f"{current_legitimacy} to 100.000\n",
                    verbose_only=False,
                    verbose=verbose,
                )
                edited = True
            else:
                smart_print(
                    f"\t{country.name} already had maximum legitimacy",
                    verbose_only=True,
                    verbose=verbose,
                )

    return edited


def maximize_army(lines: list[str], country: PlayerCountry, *, verbose: bool) -> bool:
    """Set the player's manpower and sailors to their maximum values."""

    del verbose
    print("-ma switch used, maximizing available manpower and sailors\n")
    edited = False

    for index in country_line_indices(lines, country.tag):
        if index == 0 or index + 1 >= len(lines):
            continue
        current_line = lines[index]

        if (
            current_line.startswith("\t\tmanpower=")
            and lines[index - 1].rstrip() == "\t\t}"
            and lines[index + 1].startswith("\t\tmax_manpower=")
        ):
            current_manpower = assignment_value(current_line, "manpower")
            max_manpower = assignment_value(lines[index + 1], "max_manpower")
            if current_manpower != max_manpower:
                lines[index] = current_line.replace(current_manpower, max_manpower)
                readable_manpower = str(float(max_manpower) * 1000).split(".")[0]
                print(f"\tMaximized {country.name} manpower to {readable_manpower}\n")
                edited = True
            else:
                print(f"\t{country.name} already had maximum manpower\n")

        if (
            current_line.startswith("\t\tsailors=")
            and lines[index - 1].startswith("\t\tmax_manpower=")
            and lines[index + 1].startswith("\t\tmax_sailors=")
        ):
            current_sailors = assignment_value(current_line, "sailors")
            max_sailors = assignment_value(lines[index + 1], "max_sailors")
            if current_sailors != max_sailors:
                lines[index] = current_line.replace(current_sailors, max_sailors)
                print(
                    f"\tMaximized {country.name} sailors to {max_sailors.split('.')[0]}\n"
                )
                edited = True
            else:
                print(f"\t{country.name} already had maximum sailors\n")

    return edited


def maximize_prestige(
    lines: list[str], country: PlayerCountry, *, verbose: bool
) -> bool:
    """Set the player's prestige to 100."""

    del verbose
    print("-pr switch used, granting maximum prestige\n")

    edited = False

    for index in country_line_indices(lines, country.tag):
        if index == 0 or index + 1 >= len(lines):
            continue
        current_line = lines[index]
        if not (
            current_line.startswith("\t\tprestige=")
            and lines[index - 1].startswith("\t\tscore_place=")
            and lines[index + 1].startswith("\t\tstability=")
        ):
            continue

        current_prestige = assignment_value(current_line, "prestige")
        if current_prestige == "100.000":
            print(f"\t{country.name} already had maximum prestige\n")
            continue

        lines[index] = current_line.replace(current_prestige, "100.000")
        print(f"\t{country.name} prestige changed from {current_prestige} to 100.000\n")
        edited = True

    return edited


def apply_edits(lines: list[str], options: EditOptions, *, verbose: bool) -> bool:
    """Apply all selected edits and report whether the save changed."""

    country = identify_player_country(lines)
    changed = False

    if options.monarch_points:
        changed |= edit_monarch_points(lines, country, verbose=verbose)
    if options.remove_cores:
        changed |= remove_foreign_cores(lines, country, verbose=verbose)
    if options.naturalize:
        changed |= naturalize_provinces(lines, country, verbose=verbose)
    if options.gifted_monarch:
        changed |= improve_monarch(lines, country, verbose=verbose)
    if options.add_gold is not None:
        changed |= add_treasury_gold(lines, country, options.add_gold, verbose=verbose)
    if options.stabilize:
        changed |= stabilize_country(lines, country, verbose=verbose)
    if options.maximize_army:
        changed |= maximize_army(lines, country, verbose=verbose)
    if options.prestigious:
        changed |= maximize_prestige(lines, country, verbose=verbose)

    return changed


def edited_save_path(source_path: Path) -> Path:
    """Return the sibling output path used for an edited save."""

    return source_path.with_name(f"{source_path.stem}_mod{source_path.suffix}")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line application."""

    parser = build_parser()
    args = parser.parse_args(argv)
    options = options_from_args(args)
    if not options.has_edits:
        parser.error("no editing options selected; see --help")

    print("\nEuropa Universalis IV Savegame Editor")
    print("Copyright (c) Knarkoffer 2015\n")

    try:
        source_path = select_save_file(args.file, args.path)
        print(f"Selected savegame {source_path.name}\n")

        if not assure_valid_savefile(source_path):
            raise SaveGameError(
                "The selected file is not an uncompressed, plain-text EU4 save"
            )

        lines = read_save(source_path)
        changed = apply_edits(lines, options, verbose=args.verbose)
        if changed:
            output_path = edited_save_path(source_path)
            write_save(output_path, lines)
            print(f"Save edited; created {output_path.name}")
        else:
            print("Nothing changed; no edited save was created")
    except SaveGameError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print("\nThe End!\nThanks for using my script!\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
