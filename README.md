# Europa Universalis IV Savegame Editor Script

A command-line utility for applying selected changes to plain-text Europa Universalis IV save files.

The main script can add treasury funds, maximize monarch points, remove foreign cores from owned provinces, change owned provinces to the country's primary culture, improve the monarch, maximize manpower and sailors, and set stability, legitimacy, and prestige to their maximum values.

## Requirements

- Windows
- Python 3
- An uncompressed, plain-text `.eu4` save beginning with `EU4txt`

The script uses only modules included with Python, including the Windows-specific `winreg` module. No third-party packages are required.

## Usage

Run the script with at least one editing option:

```text
python euiv-savegame-editor.py -f "C:\Games\EU4 Saves\example.eu4" --monarchPoints
```

You can also point it at a save directory. When no file is specified, the script selects the newest `.eu4` file in that directory:

```text
python euiv-savegame-editor.py -p "C:\Games\EU4 Saves" --addGold 5000
```

If neither `--file` nor `--path` is supplied, the script attempts to locate the standard Europa Universalis IV save directory beneath the current Windows Documents folder.

## Editing options

- `-ag`, `--addGold`: add the specified amount to the treasury
- `-mp`, `--monarchPoints`: set administrative, diplomatic, and military monarch points to 999
- `-dc`, `--deCore`: remove other countries' cores from provinces you own
- `-nl`, `--naturalize`: change owned provinces to your primary culture
- `-sl`, `--stabilize`: set stability to 3 and legitimacy to 100
- `-pr`, `--prestigious`: set prestige to 100
- `-gm`, `--giftedmonarch`: maximize the current monarch's attributes
- `-ma`, `--maximizearmy`: maximize manpower and sailors
- `-a`, `--all`: apply all supported edits
- `-v`, `--verbose`: print additional details

Use `python euiv-savegame-editor.py --help` for the built-in command reference.

## Output

The original save is left in place. When changes are made, the script writes a sibling file whose name ends in `_mod.eu4`.

Back up important saves before using any savegame-editing tool. Compressed or otherwise non-text saves are rejected.

## License

GNU General Public License version 3 or later. See `LICENSE`.
