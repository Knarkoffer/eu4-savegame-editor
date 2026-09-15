import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from compatibility_fixtures import fixture_bytes

import eu4_savegame_editor as editor

COUNTRY = editor.PlayerCountry(tag="MNG", name="Ming", culture="jianghuai")


class SavegameTransformationTests(unittest.TestCase):
    def test_monarch_points_keep_legacy_replacements_in_extra_tokens(self):
        for original, expected in [
            ("\t123 456 789 extra \n", "\t999 999 999 extra \n"),
            ("\t1 12 3 123 \n", "\t999 9992 999 9992999 \n"),
        ]:
            with self.subTest(original=original):
                lines = [original, "}\n", "interesting_countries={\n"]
                with contextlib.redirect_stdout(io.StringIO()):
                    changed = editor.edit_monarch_points(lines, COUNTRY, verbose=False)
                self.assertTrue(changed)
                self.assertEqual(lines[0], expected)

    def test_monarch_points_preserve_the_existing_line_format(self):
        lines = [
            "\t123 456 789 \n",
            "metadata\n",
            "interesting_countries={\n",
        ]

        changed = editor.edit_monarch_points(lines, COUNTRY, verbose=False)

        self.assertTrue(changed)
        self.assertEqual(lines[0], "\t999 999 999 \n")

    def test_remove_foreign_cores_uses_the_legacy_replacement_exactly(self):
        lines = [
            '\t\tname="Example Province"\n',
            '\t\towner="MNG"\n',
            "\t\tcores={\n",
            "\t\t\tMNG ABC DEF \n",
        ]

        changed = editor.remove_foreign_cores(lines, COUNTRY, verbose=False)

        self.assertTrue(changed)
        self.assertEqual(lines[3], "\t\t\tMNG\n")

    def test_naturalize_changes_only_the_culture_value(self):
        lines = [
            '\t\tname="Example Province"\n',
            '\t\towner="MNG"\n',
            "\t\toriginal_culture=wu\n",
            "\t\tculture=wu\n",
            "\t\treligion=confucian\n",
        ]

        changed = editor.naturalize_provinces(lines, COUNTRY, verbose=False)

        self.assertTrue(changed)
        self.assertEqual(lines[3], "\t\tculture=jianghuai\n")

    def test_monarch_attributes_keep_tabs_and_line_endings(self):
        lines = [
            "\tMNG={\n",
            "\t\thuman=yes\n",
            "\t\their={\n",
            "\t\tdummy=1\n",
            "\t\tdummy=2\n",
            "\t\tdummy=3\n",
            "\t\tdummy=4\n",
            '\t\tname="Example Monarch"\n',
            '\t\tcountry="MNG"\n',
            "\t\tDIP=4\n",
            "\t\tADM=5\n",
            "\t\tMIL=6\n",
            "\t}\n",
        ]

        changed = editor.improve_monarch(lines, COUNTRY, verbose=False)

        self.assertTrue(changed)
        self.assertEqual(lines[9:12], ["\t\tDIP=9\n", "\t\tADM=9\n", "\t\tMIL=9\n"])

    def test_country_values_match_the_legacy_string_replacements(self):
        lines = [
            "\tMNG={\n",
            "\t\thuman=yes\n",
            "\t\tscore_place=1\n",
            "\t\tprestige=12.345\n",
            "\t\tstability=-1.000\n",
            "\t\ttreasury=835636.928\n",
            "\t\testimated_monthly_income=10.000\n",
            "\t\troot_out_corruption_slider=0.000\n",
            "\t\tlegitimacy=97.129\n",
            "\t\tmercantilism=0.000\n",
            "\t\t}\n",
            "\t\tmanpower=1.000\n",
            "\t\tmax_manpower=104.733\n",
            "\t\tsailors=2.000\n",
            "\t\tmax_sailors=14577.000\n",
            "\t}\n",
        ]

        self.assertTrue(
            editor.add_treasury_gold(lines, COUNTRY, 150_000.0, verbose=False)
        )
        self.assertTrue(editor.stabilize_country(lines, COUNTRY, verbose=False))
        self.assertTrue(editor.maximize_army(lines, COUNTRY, verbose=False))
        self.assertTrue(editor.maximize_prestige(lines, COUNTRY, verbose=False))

        self.assertEqual(lines[3], "\t\tprestige=100.000\n")
        self.assertEqual(lines[4], "\t\tstability=3.000\n")
        self.assertEqual(lines[5], "\t\ttreasury=985636.928\n")
        self.assertEqual(lines[8], "\t\tlegitimacy=100.000\n")
        self.assertEqual(lines[11], "\t\tmanpower=104.733\n")
        self.assertEqual(lines[13], "\t\tsailors=14577.000\n")

    def test_write_save_preserves_bytes_and_cp1252_encoding(self):
        lines = ["EU4txt\r\n", '\tname="Åland"\r\n']

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example_mod.eu4"
            editor.write_save(path, lines)

            self.assertEqual(
                path.read_bytes(),
                b'EU4txt\r\n\tname="\xc5land"\r\n',
            )

    def test_legacy_and_kebab_case_options_are_both_supported(self):
        parser = editor.build_parser()

        legacy = parser.parse_args(["--addGold", "5000", "--monarchPoints"])
        modern = parser.parse_args(["--add-gold", "5000", "--monarch-points"])

        self.assertEqual(legacy.add_gold, modern.add_gold)
        self.assertEqual(legacy.monarch_points, modern.monarch_points)


class OriginalOutputTests(unittest.TestCase):
    """Compare complete output files with bytes produced by commit 3df1ed2."""

    @classmethod
    def setUpClass(cls):
        cls.inputs = fixture_bytes()
        cls.golden_directory = Path(__file__).parent / "fixtures"
        cls.provenance = json.loads(
            (cls.golden_directory / "provenance.json").read_text(encoding="utf-8")
        )

    def assert_original_output(self, fixture, flags, golden, *, final_newline=True):
        source_bytes = self.inputs[fixture]
        filename = golden + ".eu4"
        expected = (self.golden_directory / filename).read_bytes()
        self.assertEqual(
            hashlib.sha256(expected).hexdigest(),
            self.provenance["files"][filename]["output_sha256"],
        )
        if not final_newline:
            expected = expected.removesuffix(b"\n")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input save.eu4"
            source.write_bytes(source_bytes)
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                status = editor.main(["--file", str(source), *flags])
            self.assertEqual(status, 0)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertEqual(
                {path.name for path in Path(directory).iterdir()},
                {"input save.eu4", "input save_mod.eu4"},
            )
            actual = (Path(directory) / "input save_mod.eu4").read_bytes()
            self.assertEqual(actual, expected)
            self.assertEqual(
                hashlib.sha256(actual).hexdigest(),
                hashlib.sha256(expected).hexdigest(),
            )

    def test_all_edits_preserve_cp1252_bytes_and_legacy_newline_handling(self):
        # The original reader normalizes CRLF, CR and mixed endings to LF.
        for ending in ("lf", "crlf", "cr", "mixed-endings", "no-final-newline"):
            with self.subTest(ending=ending):
                self.assert_original_output(
                    f"synthetic-{ending}",
                    ["--all"],
                    "all",
                    final_newline=ending != "no-final-newline",
                )

    def test_naturalize_quoted_culture_matches_original(self):
        for flags, golden in [
            (["--naturalize"], "quoted-culture-naturalize"),
            (["--all"], "quoted-culture-all"),
        ]:
            with self.subTest(flags=flags):
                self.assert_original_output(
                    "synthetic-quoted-province-culture", flags, golden
                )

    def test_quoted_matching_culture_still_creates_an_edited_file(self):
        self.assert_original_output(
            "synthetic-quoted-matching-only",
            ["--naturalize"],
            "quoted-matching-naturalize",
        )

    def test_monarch_points_accept_an_extra_token(self):
        self.assert_original_output(
            "synthetic-extra-monarch-point-token", ["-mp"], "extra-points-token"
        )

    def test_invalid_gold_keeps_other_edits_and_all_override(self):
        for alias in ("-ag", "--addGold", "--add-gold"):
            for edit, golden in [("-mp", "monarch-points"), ("--all", "all")]:
                for flags in (
                    [alias, "not-a-number", edit],
                    [edit, alias, "not-a-number"],
                ):
                    with self.subTest(flags=flags):
                        self.assert_original_output("synthetic-lf", flags, golden)

    def test_invalid_gold_alone_creates_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.eu4"
            source.write_bytes(self.inputs["synthetic-lf"])
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                editor.main(["--file", str(source), "--addGold", "not-a-number"])
            self.assertNotEqual(error.exception.code, 0)
            self.assertEqual(list(Path(directory).iterdir()), [source])
            self.assertEqual(source.read_bytes(), self.inputs["synthetic-lf"])


if __name__ == "__main__":
    unittest.main()
