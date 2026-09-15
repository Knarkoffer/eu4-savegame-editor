# Europa Universalis IV Savegame Editor

A command-line utility for applying selected changes to plain-text Europa Universalis IV save files.

The script can add treasury funds, maximize monarch points, remove foreign cores from owned provinces, change owned provinces to the country's primary culture, improve the monarch, maximize manpower and sailors, and set stability, legitimacy, and prestige to their maximum values.

## Requirements

- Python 3.10 or newer
- An uncompressed, plain-text `.eu4` save beginning with `EU4txt`

No third-party packages are required to run the script. On Windows, it can locate the default Europa Universalis IV save directory through the registry. On other platforms, provide a file or directory explicitly.

## Usage

Run the script with at least one editing option:

```text
python eu4_savegame_editor.py -f "C:\Games\EU4 Saves\example.eu4" --monarch-points
```

You can also point it at a save directory. When no file is specified, the script selects the newest `.eu4` file in that directory:

```text
python eu4_savegame_editor.py -p "C:\Games\EU4 Saves" --add-gold 5000
```

If neither `--file` nor `--path` is supplied, the script first tries the standard Europa Universalis IV save directory beneath the current Windows Documents folder. It then checks for a local `save games` directory beside the script.

## Editing options

- `-ag`, `--add-gold`: add the specified amount to the treasury
- `-mp`, `--monarch-points`: set administrative, diplomatic, and military monarch points to 999
- `-dc`, `--de-core`: remove other countries' cores from provinces you own
- `-nl`, `--naturalize`: change owned provinces to your primary culture
- `-sl`, `--stabilize`: set stability to 3 and legitimacy to 100
- `-pr`, `--prestigious`: set prestige to 100
- `-gm`, `--gifted-monarch`: maximize the current monarch's attributes
- `-ma`, `--maximize-army`: maximize manpower and sailors
- `-a`, `--all`: apply all supported edits
- `-v`, `--verbose`: print additional details

The original camel-case long options, such as `--addGold` and `--monarchPoints`, remain supported.

Use `python eu4_savegame_editor.py --help` for the built-in command reference.

## Output

The original save is left in place. When changes are made, the script writes a sibling file whose name ends in `_mod.eu4` using the same `cp1252` encoding expected by the original script.

Edited save files are not compatible with Ironman mode or Ironman achievements.

Back up important saves before using any savegame-editing tool. Compressed or otherwise non-text saves are rejected.

## License

GNU General Public License version 3 or later. See `LICENSE`.
