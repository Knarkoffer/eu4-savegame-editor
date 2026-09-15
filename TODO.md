# Compatibility testing

The compatibility audit resumed and was completed on 2026-09-14. There are no
outstanding items from the paused test plan. Results and limitations are in
[`COMPATIBILITY_TEST_REPORT.md`](COMPATIBILITY_TEST_REPORT.md).

## Completed coverage

- [x] Finish and deduplicate the 12,288-case synthetic flag matrix.
- [x] Exercise aliases, numeric values, repeated flags, ordering, and file
  selection in 139 additional cases.
- [x] Run benchmark and individual edit modes against all nine representative
  save inputs.
- [x] Run all 256 combinations of the eight edit flags against one real save.
- [x] Verify source and all 21 input checksums after the audit.
- [x] Run permanent tests with native Windows Python using the cp1252 locale.
- [x] Run final Black, Ruff, unit-test, and Git diff checks.
- [x] Record aggregate results, known CLI exit-code differences, and privacy
  scan scope.

## After future transformation changes

- [ ] Rerun `python -m unittest discover -s tests -v` on Windows.
- [ ] Create a new ignored evidence directory and run
  `tests/compatibility_audit.py --phase suite` against the original source.
- [ ] Compare raw output bytes and SHA-256 checksums, verify inputs remained
  unchanged, and update the compatibility report.
- [ ] Scan both the nonignored working tree and all Git objects reachable from
  local refs for private names before committing.
