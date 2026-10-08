# Converter tests — awaiting human review

These tests were authored from approved design v4. Production behavior is not implemented. `rule_converter/` currently contains data contracts and deliberately failing public-interface stubs only.

## Run locally

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Current result: 59 test methods discovered; 3 fixture-integrity methods pass and 56 behavior methods are intentionally red. Parameterized subtests produce 10 assertion failures and 109 NotImplementedError reports. There are no skips. Do not treat these as green implementation checks. The per-method record is in `docs/test-results-red.json`.

## Reading route

1. `fixtures/elastic-input.yaml` and `fixtures/sigma-expected.yaml`: human-provided exact success pair.
2. `test_converter.py`: conversion semantics, metadata, diagnostics, incomplete drafts, generalized Linux example.
3. `test_sigma.py`: vendor-neutral expression rendering without Elastic input fields.
4. `fixtures/linux/README.md` and `manifest.json`: four pinned Elastic/Sigma comparisons, provenance, and differences.
5. `test_linux_references.py`: real Elastic inputs must return diagnosed metadata drafts under the approved subset; Sigma files are comparison references, not expected converted output.
6. `test_cli.py`: real subprocesses and temporary files, JSON/YAML loading, stdout/stderr separation, exit behavior, safe YAML loading.
7. `helpers.py`: baseline input builder and restricted test-owned Boolean evaluator, with no eval or production parser dependency.

Target individual modules with `.venv/bin/python -m unittest tests.test_converter -v` (or `tests.test_sigma`, `tests.test_cli`, `tests.test_linux_references`). Run only the currently green corpus checks with `.venv/bin/python -m unittest tests.test_linux_references.ReferenceIntegrityTests -v`.

## Review boundaries

The human must review the tests, configuration, data contracts, and intended failures before feature implementation. Test authors preserve the human's example fixtures. During implementation, changes to any tests, fixtures, helpers, or execution settings require explicit human approval.

Full EQL/ES|QL support or successful translation of the selected upstream Linux queries would extend v4. Do not simplify the real queries or copy the related Sigma detections merely to get passing conversion tests.
