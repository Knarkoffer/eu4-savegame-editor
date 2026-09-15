"""Independent fresh-process verification, without the runpy batch runner."""

import argparse
import hashlib
import json
import locale
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def execute(root):
    assert not sys.flags.utf8_mode, "Use -X utf8=0 for legacy input encoding"
    assert sys.platform == "win32"
    assert locale.getencoding() == "cp1252"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for version in ("legacy", "current"):
        assert (
            hashlib.sha256((root / f"{version}.py").read_bytes()).hexdigest()
            == manifest[f"{version}_sha256"]
        )
    cases = [
        ("plain-all", "synthetic-lf", ["--all"]),
        (
            "quoted-culture-naturalize",
            "synthetic-quoted-province-culture",
            ["--naturalize"],
        ),
        ("quoted-culture-all", "synthetic-quoted-province-culture", ["--all"]),
        (
            "quoted-matching-naturalize",
            "synthetic-quoted-matching-only",
            ["--naturalize"],
        ),
        ("missing-culture-gold", "synthetic-missing-primary-culture", ["-ag", "5000"]),
        ("missing-culture-points", "synthetic-missing-primary-culture", ["-mp"]),
        ("extra-points-token", "synthetic-extra-monarch-point-token", ["-mp"]),
        ("invalid-gold-all", "synthetic-lf", ["--addGold", "not-a-number", "--all"]),
        ("invalid-gold-points", "synthetic-lf", ["--addGold", "not-a-number", "-mp"]),
        ("invalid-gold-alone", "synthetic-lf", ["--addGold", "not-a-number"]),
        ("missing-gold-value", "synthetic-lf", ["--addGold"]),
        ("unknown-flag", "synthetic-lf", ["--unknown"]),
        ("version", "synthetic-lf", ["--version"]),
        ("help", "synthetic-lf", ["--help"]),
        ("no-edit-flags", "synthetic-lf", []),
        ("verbose-only", "synthetic-lf", ["--verbose"]),
        ("all-before-gold", "synthetic-lf", ["--all", "--addGold", "1"]),
        ("repeat-switch", "synthetic-lf", ["-mp", "-mp"]),
    ]
    records = []
    artifacts = root / "direct-artifacts"
    artifacts.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="eu4-direct-audit-") as directory:
        work = Path(directory)
        for version in ("legacy", "current"):
            shutil.copyfile(root / f"{version}.py", work / f"{version}.py")
        for name, fixture, flags in cases:
            source = root / "fixtures" / f"{fixture}.eu4"
            input_path = work / "input.eu4"
            shutil.copyfile(source, input_path)
            input_hash = hashlib.sha256(input_path.read_bytes()).hexdigest()
            output_path = work / "input_mod.eu4"
            row = {
                "case": name,
                "source": fixture,
                "flags": flags,
                "input_sha256": input_hash,
            }
            outputs = []
            for version in ("legacy", "current"):
                assert not output_path.exists()
                result = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8=0",
                        str(work / f"{version}.py"),
                        "--file",
                        str(input_path),
                        *flags,
                    ],
                    cwd=work,
                    capture_output=True,
                    timeout=60,
                )
                data = output_path.read_bytes() if output_path.exists() else None
                outputs.append(data)
                row[version] = {
                    "exit": result.returncode,
                    "output_sha256": (
                        hashlib.sha256(data).hexdigest() if data is not None else None
                    ),
                    "output_bytes": len(data) if data is not None else None,
                }
                (artifacts / f"{name}-{version}.stdout").write_bytes(result.stdout)
                (artifacts / f"{name}-{version}.stderr").write_bytes(result.stderr)
                if data is not None:
                    (artifacts / f"{name}-{version}.eu4").write_bytes(data)
                output_path.unlink(missing_ok=True)
                assert hashlib.sha256(input_path.read_bytes()).hexdigest() == input_hash
            row["bytes_equal"] = outputs[0] == outputs[1]
            row["input_unchanged"] = True
            records.append(row)
            print(json.dumps(row), flush=True)
    (root / "direct-checks.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )
    assert all(row["bytes_equal"] for row in records), "Output compatibility failed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    execute(parser.parse_args().output.resolve())
