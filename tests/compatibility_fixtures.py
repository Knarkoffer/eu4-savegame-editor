"""Synthetic saves used to characterize the original editor, including edge cases."""

BASE = (
    "EU4txt\n"
    "date=1491.11.27\n"
    'save_game="fixture.eu4"\n'
    'player="MNG"\n'
    'displayed_country_name="Fixture Country"\n'
    "provinces={\n"
    "\t-1={\n"
    '\t\tname="Åland — café €"\n'
    '\t\towner="MNG"\n'
    "\t\tcores={\n"
    "\t\t\tMNG ABC DEF \n"
    "\t\t}\n"
    "\t\toriginal_culture=wu\n"
    "\t\tculture=wu\n"
    "\t\treligion=confucian\n"
    "\t}\n"
    "\t-2={\n"
    '\t\tname="Owned, already correct"\n'
    '\t\towner="MNG"\n'
    "\t\tcores={\n"
    "\t\t\tMNG \n"
    "\t\t}\n"
    "\t\toriginal_culture=jianghuai\n"
    "\t\tculture=jianghuai\n"
    "\t\treligion=confucian\n"
    "\t}\n"
    "\t-3={\n"
    '\t\tname="Foreign Province"\n'
    '\t\towner="ABC"\n'
    "\t\tcores={\n"
    "\t\t\tABC DEF \n"
    "\t\t}\n"
    "\t\toriginal_culture=wu\n"
    "\t\tculture=wu\n"
    "\t\treligion=confucian\n"
    "\t}\n"
    "}\n"
    "countries={\n"
    "\tMNG={\n"
    "\t\thuman=yes\n"
    "\t\tprimary_culture=jianghuai\n"
    "\t\tscore_place=1\n"
    "\t\tprestige=12.345\n"
    "\t\tstability=-1.000\n"
    "\t\ttreasury=835636.928\n"
    "\t\testimated_monthly_income=10.000\n"
    "\t\troot_out_corruption_slider=0.000\n"
    "\t\tlegitimacy=97.129\n"
    "\t\tmercantilism=0.000\n"
    "\t\tarmy={\n"
    "\t\t}\n"
    "\t\tmanpower=1.000\n"
    "\t\tmax_manpower=104.733\n"
    "\t\tsailors=2.000\n"
    "\t\tmax_sailors=14577.000\n"
    "\t\their={\n"
    "\t\t\tid={\n"
    "\t\t\t\tid=1\n"
    "\t\t\t\ttype=37\n"
    "\t\t\t}\n"
    '\t\t\tname="First Monarch"\n'
    '\t\t\tcountry="MNG"\n'
    "\t\t\tDIP=1\n"
    "\t\t\tADM=2\n"
    "\t\t\tMIL=3\n"
    "\t\t}\n"
    "\t\their={\n"
    "\t\t\tid={\n"
    "\t\t\t\tid=2\n"
    "\t\t\t\ttype=37\n"
    "\t\t\t}\n"
    '\t\t\tname="Last Monarch"\n'
    '\t\t\tcountry="MNG"\n'
    "\t\t\tDIP=4\n"
    "\t\t\tADM=5\n"
    "\t\t\tMIL=6\n"
    "\t\t}\n"
    "\t}\n"
    "\tABC={\n"
    "\t\thuman=yes\n"
    "\t\tprimary_culture=wu\n"
    "\t\tscore_place=2\n"
    "\t\tprestige=12.345\n"
    "\t\tstability=-1.000\n"
    "\t\ttreasury=12.345\n"
    "\t\testimated_monthly_income=10.000\n"
    "\t}\n"
    "}\n"
    "monarch_power={\n"
    "\t123 456 789 \n"
    "}\n"
    "interesting_countries={\n"
    "\tMNG ABC \n"
    "}\n"
)


def fixture_bytes():
    """Return complete cp1252 input files without writing to disk."""
    variants = {
        "synthetic-lf": BASE,
        "synthetic-crlf": BASE.replace("\n", "\r\n"),
        "synthetic-mixed-endings": "".join(
            line.rstrip("\n") + ("\r\n" if i % 2 else "\n")
            for i, line in enumerate(BASE.splitlines(keepends=True))
        ),
        "synthetic-cr": BASE.replace("\n", "\r"),
        "synthetic-no-final-newline": BASE.rstrip("\n"),
        "synthetic-quoted-province-culture": BASE.replace(
            "\t\tculture=wu\n", '\t\tculture="wu"\n'
        ),
        "synthetic-quoted-matching-culture": BASE.replace(
            "\t\tculture=jianghuai\n", '\t\tculture="jianghuai"\n'
        ),
        "synthetic-missing-primary-culture": BASE.replace(
            "\t\tprimary_culture=jianghuai\n", ""
        ),
        "synthetic-extra-monarch-point-token": BASE.replace(
            "\t123 456 789 \n", "\t123 456 789 42 \n"
        ),
        "synthetic-overmax-monarch-points": BASE.replace(
            "\t123 456 789 \n", "\t1000 1000 1000 \n"
        ),
    }
    maximum = BASE
    for old, new in [
        ("\t123 456 789 ", "\t999 999 999 "),
        ("MNG ABC DEF ", "MNG "),
        ("\t\tculture=wu\n", "\t\tculture=jianghuai\n"),
        ("prestige=12.345", "prestige=100.000"),
        ("stability=-1.000", "stability=3.000"),
        ("legitimacy=97.129", "legitimacy=100.000"),
        ("\t\tmanpower=1.000", "\t\tmanpower=104.733"),
        ("\t\tsailors=2.000", "\t\tsailors=14577.000"),
        ("DIP=4", "DIP=9"),
        ("ADM=5", "ADM=9"),
        ("MIL=6", "MIL=9"),
    ]:
        maximum = maximum.replace(old, new)
    variants["synthetic-already-maximized"] = maximum
    variants["synthetic-quoted-matching-only"] = maximum.replace(
        "\t\tculture=jianghuai\n", '\t\tculture="jianghuai"\n'
    )
    return {name: text.encode("cp1252") for name, text in variants.items()}
