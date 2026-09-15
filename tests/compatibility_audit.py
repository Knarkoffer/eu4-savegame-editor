"""Run the untouched historical and current CLI against isolated real files.

Prepare on Linux; execute on Windows so the historical default encoding and
winreg import are genuine. No editor functions, I/O, or imports are mocked.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import gc
import hashlib
import io
import json
import locale
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

from compatibility_fixtures import fixture_bytes

SHORT = ["-ag", "-mp", "-dc", "-nl", "-sl", "-pr", "-gm", "-ma"]
OLD = [
    "--addGold",
    "--monarchPoints",
    "--deCore",
    "--naturalize",
    "--stabilize",
    "--prestigious",
    "--giftedmonarch",
    "--maximizearmy",
]
NEW = [
    "--add-gold",
    "--monarch-points",
    "--de-core",
    "--naturalize",
    "--stabilize",
    "--prestigious",
    "--gifted-monarch",
    "--maximize-army",
]
STATE = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    return checksum.hexdigest()


def prepare(root, repo):
    root.mkdir(parents=True, exist_ok=True)
    ref = subprocess.check_output(
        ["git", "rev-parse", "3df1ed2"], cwd=repo, text=True
    ).strip()
    baseline = subprocess.check_output(
        ["git", "show", f"{ref}:euiv-savegame-editor.py"], cwd=repo
    )
    (root / "legacy.py").write_bytes(baseline)
    current = (repo / "eu4_savegame_editor.py").read_bytes()
    (root / "current.py").write_bytes(current)
    sources = []
    seen = {}
    for path in sorted((repo / "save games").rglob("*.eu4")):
        data = path.read_bytes()
        checksum = digest(data)
        entry = {
            "id": f"save-{len(sources)+1:02}",
            "relative_path": path.relative_to(repo / "save games").as_posix(),
            "sha256": checksum,
            "bytes": len(data),
            "crlf": data.count(b"\r\n"),
            "lf": data.count(b"\n"),
            "non_ascii_bytes": sum(b >= 128 for b in data),
        }
        if checksum in seen:
            entry["duplicate_of"] = seen[checksum]
        else:
            seen[checksum] = entry["id"]
        sources.append(entry)
    fixtures = root / "fixtures"
    fixtures.mkdir(exist_ok=True)
    for name, data in fixture_bytes().items():
        (fixtures / f"{name}.eu4").write_bytes(data)
        sources.append(
            {"id": name, "sha256": digest(data), "bytes": len(data), "synthetic": True}
        )
    manifest = {
        "baseline_commit": ref,
        "legacy_sha256": digest(baseline),
        "current_sha256": digest(current),
        "sources": sources,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


def flags(mask, names, amount="5000"):
    result = []
    for bit, name in enumerate(names):
        if mask & (1 << bit):
            result.append(name)
            if bit == 0:
                result.append(amount)
    if mask & 256:
        result.append("-a" if names == SHORT else "--all")
    if mask & 512:
        result.append("-v" if names == SHORT else "--verbose")
    return result


def initialize(root, repo, native_root):
    root = Path(root)
    worker = Path(native_root) / str(os.getpid())
    worker.mkdir()
    for name in ("legacy.py", "current.py"):
        shutil.copyfile(root / name, worker / name)
    STATE.update(root=root, repo=Path(repo), worker=worker, inputs={}, saved_failures=0)
    os.chdir(worker)


def run_script(script, argv):
    output = io.StringIO()
    errors = io.StringIO()
    start = time.perf_counter()
    status = 0
    exception = None
    old_argv = sys.argv
    sys.argv = [str(script), *argv]
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
        try:
            runpy.run_path(str(script), run_name="__main__")
        except SystemExit as error:
            status = (
                error.code
                if isinstance(error.code, int)
                else (0 if error.code is None else 1)
            )
            if isinstance(error.code, str):
                print(error.code, file=sys.stderr)
        except Exception as error:
            status = 1
            exception = type(error).__name__
            traceback.print_exc()
    sys.argv = old_argv
    gc.collect()
    return {
        "exit": status,
        "exception": exception,
        "seconds": round(time.perf_counter() - start, 4),
        "stdout": output.getvalue(),
        "stderr": errors.getvalue(),
    }


def first_difference(left, right):
    limit = min(len(left), len(right))
    offset = limit
    for start in range(0, limit, 65536):
        a, b = left[start : start + 65536], right[start : start + 65536]
        if a != b:
            offset = start + next(
                i for i, (x, y) in enumerate(zip(a, b, strict=False)) if x != y
            )
            break
    line_start = left.rfind(b"\n", 0, offset) + 1
    line_end = left.find(b"\n", offset)
    other_start = right.rfind(b"\n", 0, offset) + 1
    other_end = right.find(b"\n", offset)
    return {
        "offset_zero_based": offset,
        "line_one_based": left.count(b"\n", 0, offset) + 1,
        "legacy_context_hex": left[max(0, offset - 40) : offset + 80].hex(),
        "current_context_hex": right[max(0, offset - 40) : offset + 80].hex(),
        "legacy_line": repr(left[line_start : line_end + 1]),
        "current_line": repr(right[other_start : other_end + 1]),
    }


def run_case(source, case):
    if source["id"] not in STATE["inputs"]:
        folder = STATE["worker"] / source["id"]
        folder.mkdir()
        path = folder / "input save.eu4"
        original = (
            STATE["root"] / "fixtures" / f'{source["id"]}.eu4'
            if source.get("synthetic")
            else STATE["repo"] / "save games" / source["relative_path"]
        )
        shutil.copyfile(original, path)
        assert file_digest(path) == source["sha256"]
        STATE["inputs"][source["id"]] = path
    path = STATE["inputs"][source["id"]]
    if case.get("uppercase"):
        path = path.with_suffix(".EU4")
        if not path.exists():
            shutil.copyfile(STATE["inputs"][source["id"]], path)
    output_path = path.with_name(path.stem + "_mod" + path.suffix)
    assert not output_path.exists()
    old_flags = case["old_flags"]
    new_flags = case.get("new_flags", old_flags)
    selector = case.get("selector", "file")
    if selector == "path":
        old_selector, new_selector = ["-p", str(path.parent)], [
            "--path",
            str(path.parent),
        ]
    elif selector == "both":
        old_selector, new_selector = [
            "-p",
            str(path.parent / "nonexistent"),
            "-f",
            str(path),
        ], ["--path", str(path.parent / "nonexistent"), "--file", str(path)]
    else:
        old_selector, new_selector = ["-f", str(path)], ["--file", str(path)]
    if case.get("bare"):
        old_selector, new_selector = [], []
    record = {
        "source": source["id"],
        "case": case["id"],
        "selector": selector,
        "old_flags": old_flags,
        "new_flags": new_flags,
        "input_sha256": source["sha256"],
    }
    old_result = run_script(STATE["worker"] / "legacy.py", old_selector + old_flags)
    old_bytes = output_path.read_bytes() if output_path.exists() else None
    output_path.unlink(missing_ok=True)
    new_result = run_script(STATE["worker"] / "current.py", new_selector + new_flags)
    new_bytes = output_path.read_bytes() if output_path.exists() else None
    output_path.unlink(missing_ok=True)
    for key, result, data in [
        ("legacy", old_result, old_bytes),
        ("current", new_result, new_bytes),
    ]:
        result["output_sha256"] = digest(data) if data is not None else None
        result["output_bytes"] = len(data) if data is not None else None
        record[key] = {k: v for k, v in result.items() if k not in ("stdout", "stderr")}
    record["input_unchanged"] = file_digest(path) == source["sha256"]
    record["bytes_equal"] = old_bytes == new_bytes
    if old_bytes is not None and new_bytes is not None and old_bytes != new_bytes:
        record["difference"] = first_difference(old_bytes, new_bytes)
    if not record["input_unchanged"]:
        record["classification"] = "INPUT_MODIFIED"
    elif old_bytes != new_bytes:
        record["classification"] = "OUTPUT_MISMATCH"
    elif old_result["exit"] == 0 and new_result["exit"] == 0:
        record["classification"] = (
            "IDENTICAL_OUTPUT" if old_bytes is not None else "IDENTICAL_NO_OUTPUT"
        )
    elif old_result["exit"] != 0 and new_result["exit"] != 0 and old_bytes is None:
        record["classification"] = "BOTH_REJECTED"
    else:
        record["classification"] = "EXIT_MISMATCH"
    if record["classification"] not in ("IDENTICAL_OUTPUT", "IDENTICAL_NO_OUTPUT"):
        record["legacy"]["stderr"] = old_result["stderr"][-4000:]
        record["current"]["stderr"] = new_result["stderr"][-4000:]
    if (
        record["classification"]
        in (
            "INPUT_MODIFIED",
            "OUTPUT_MISMATCH",
            "EXIT_MISMATCH",
        )
        and STATE["saved_failures"] < 2
    ):
        folder = (
            STATE["root"] / "failures" / f'{source["id"]}-{case["id"]}-{os.getpid()}'
        )
        folder.mkdir(parents=True, exist_ok=True)
        for name, data in [("legacy.eu4", old_bytes), ("current.eu4", new_bytes)]:
            if data is not None:
                (folder / name).write_bytes(data)
        for name, result in [("legacy", old_result), ("current", new_result)]:
            (folder / f"{name}.log").write_text(
                result["stdout"] + result["stderr"], encoding="utf-8"
            )
        STATE["saved_failures"] += 1
    return record


def batch(job):
    source, cases = job
    records = []
    for case in cases:
        records.append(run_case(source, case))
    return records


def matrix_cases(bits):
    return [
        {
            "id": f"matrix-{mask:04}",
            "old_flags": flags(mask, OLD),
            "new_flags": flags(mask, NEW),
            "selector": "path" if mask % 2 else "file",
        }
        for mask in range(1 << bits)
    ]


def extra_cases():
    cases = []
    for style, names in [("short", SHORT), ("old-long", OLD), ("new-long", NEW)]:
        for mask in [*(1 << b for b in range(10)), 255, 511, 767, 1023]:
            cases.append(
                {
                    "id": f"alias-{style}-{mask}",
                    "old_flags": flags(mask, OLD if names == NEW else names),
                    "new_flags": flags(mask, names),
                }
            )
    for amount in [
        "0",
        "-0",
        "-5000",
        "0.001",
        "0.0004",
        "0.0005",
        "1.23456",
        "1e6",
        "150000",
        "1e308",
        "nan",
        "inf",
    ]:
        for mask in [1, 255, 257, 1023]:
            cases.append(
                {
                    "id": f"gold-{amount}-{mask}",
                    "old_flags": flags(mask, OLD, amount),
                    "new_flags": flags(mask, NEW, amount),
                }
            )
    for selector in ["file", "path", "both"]:
        for mask in [*(1 << b for b in range(10)), 255, 511, 767, 1023]:
            cases.append(
                {
                    "id": f"selector-{selector}-{mask}",
                    "old_flags": flags(mask, SHORT),
                    "new_flags": flags(mask, NEW),
                    "selector": selector,
                }
            )
    cases += [
        {
            "id": "reversed-all-edits",
            "old_flags": list(reversed(OLD[1:])) + [OLD[0], "5000"],
            "new_flags": list(reversed(NEW[1:])) + [NEW[0], "5000"],
        },
        {
            "id": "repeat-gold-last-wins",
            "old_flags": ["-ag", "1", "-ag", "2"],
            "new_flags": ["-ag", "1", "-ag", "2"],
        },
        {"id": "upper-extension", "old_flags": ["--all"], "uppercase": True},
        {"id": "help-short", "old_flags": ["-h"], "bare": True},
        {"id": "help-long", "old_flags": ["--help"], "bare": True},
        {"id": "no-arguments", "old_flags": [], "bare": True},
        {"id": "verbose-only", "old_flags": ["-v"], "bare": True},
    ]
    return cases


def execute(root, repo, phase, workers, bits, selected):
    assert sys.platform == "win32", "Use native Windows Python for baseline fidelity"
    assert not sys.flags.utf8_mode, "Use -X utf8=0 for legacy input encoding"
    assert locale.getencoding().lower() == "cp1252", locale.getencoding()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    sources = [s for s in manifest["sources"] if not s.get("duplicate_of")]
    if selected == "synthetic":
        sources = [s for s in sources if s.get("synthetic")]
    elif selected:
        sources = [s for s in sources if s["id"] in selected.split(",")]
    else:
        sources = [s for s in sources if not s.get("synthetic")]
    assert sources, "No inputs selected"
    assert file_digest(root / "legacy.py") == manifest["legacy_sha256"]
    assert file_digest(root / "current.py") == manifest["current_sha256"]
    assert file_digest(repo / "eu4_savegame_editor.py") == manifest["current_sha256"]
    if phase == "benchmark":
        cases = [
            {"id": "bench-all", "old_flags": ["--all"]},
            {"id": "bench-gold", "old_flags": ["-ag", "5000"]},
            {"id": "bench-naturalize", "old_flags": ["-nl"]},
        ]
    elif phase == "extra":
        cases = extra_cases()
    elif phase == "singles":
        cases = [
            {
                "id": f"full-single-{mask}",
                "old_flags": flags(mask, SHORT),
                "new_flags": flags(mask, NEW),
            }
            for mask in [*(1 << b for b in range(10)), 255, 767, 1023]
        ]
    else:
        cases = matrix_cases(bits)
    jobs = [
        (source, cases[start : start + 8])
        for source in sources
        for start in range(0, len(cases), 8)
    ]
    native_root = Path(tempfile.mkdtemp(prefix="eu4-byte-audit-"))
    metadata = {
        "python": sys.version,
        "encoding": locale.getencoding(),
        "platform": sys.platform,
        "phase": phase,
        "matrix_bits": bits,
        "workers": workers,
        "native_scratch": str(native_root),
        "sources": [s["id"] for s in sources],
        "case_count": len(cases) * len(sources),
        "legacy_sha256": file_digest(root / "legacy.py"),
        "current_sha256": file_digest(root / "current.py"),
    }
    report_name = f'{phase}-{bits}-{selected or "all"}'
    (root / f"{report_name}-environment.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata), flush=True)
    counts = {}
    done = 0
    printed_failures = 0
    start = time.perf_counter()
    with (
        (root / f"{report_name}.jsonl").open("w", encoding="utf-8") as report,
        concurrent.futures.ProcessPoolExecutor(
            max_workers=workers,
            initializer=initialize,
            initargs=(str(root), str(repo), str(native_root)),
        ) as pool,
    ):
        futures = [pool.submit(batch, job) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            for record in future.result():
                report.write(json.dumps(record) + "\n")
                category = record["classification"]
                counts[category] = counts.get(category, 0) + 1
                done += 1
                if (
                    phase == "benchmark"
                    or category
                    in (
                        "OUTPUT_MISMATCH",
                        "EXIT_MISMATCH",
                        "INPUT_MODIFIED",
                    )
                ) and printed_failures < 12:
                    print(json.dumps(record), flush=True)
                    printed_failures += 1
            report.flush()
            if done % 128 and done != metadata["case_count"]:
                continue
            print(
                json.dumps(
                    {
                        "completed": done,
                        "total": metadata["case_count"],
                        "counts": counts,
                        "elapsed_seconds": round(time.perf_counter() - start, 1),
                    }
                ),
                flush=True,
            )
    metadata.update(
        counts=counts,
        seconds=round(time.perf_counter() - start, 1),
        original_inputs_unchanged=all(
            file_digest(
                root / "fixtures" / f"{s['id']}.eu4"
                if s.get("synthetic")
                else repo / "save games" / s["relative_path"]
            )
            == s["sha256"]
            for s in sources
        ),
        current_source_unchanged=file_digest(repo / "eu4_savegame_editor.py")
        == manifest["current_sha256"],
    )
    (root / f"{report_name}-summary.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata), flush=True)
    # Only the isolated test inputs/scripts are removed; mismatches and reports remain.
    shutil.rmtree(native_root)
    assert metadata["original_inputs_unchanged"]
    assert metadata["current_source_unchanged"]
    if counts.get("OUTPUT_MISMATCH") or counts.get("INPUT_MODIFIED"):
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument(
        "--phase",
        choices=["benchmark", "matrix", "extra", "singles", "suite"],
        default="benchmark",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--bits", type=int, choices=[8, 10], default=8)
    parser.add_argument("--sources", default="")
    parser.add_argument(
        "--output", type=Path, required=True, help="private evidence directory"
    )
    args = parser.parse_args()
    root = args.output.resolve()
    if args.prepare:
        prepare(root, args.repo)
    elif args.phase == "suite":
        from compatibility_direct import execute as direct_checks

        direct_checks(root)
        for phase, bits, sources in [
            ("matrix", 10, "synthetic"),
            ("extra", 8, "synthetic-lf"),
            ("benchmark", 8, ""),
            ("singles", 8, ""),
            ("matrix", 8, "save-01"),
        ]:
            execute(root, args.repo, phase, args.workers, bits, sources)
    else:
        execute(root, args.repo, args.phase, args.workers, args.bits, args.sources)


if __name__ == "__main__":
    main()
