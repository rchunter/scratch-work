# Detection Rule Converter

Convert one Elastic Security rule in JSON or YAML into Sigma YAML, with structured diagnostics for assumptions and untranslated fields. The converter supports a deliberately small KQL subset and translates independent metadata even when detection cannot be converted.

## Install and run

Requires Python 3.11+ and PyYAML.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m rule_converter tests/fixtures/elastic-input.yaml > rule.yml 2> diagnostics.jsonl
```

The input file is the only required argument. Supported extensions: `.json`, `.yaml`, `.yml`. Standard output contains only the output YAML; standard error contains JSON Lines with `severity`, `code`, `path`, and `message`. The library performs no IO:

```python
from rule_converter import convert_rule

result = convert_rule({
    "name": "Linux command-line example",
    "type": "query",
    "language": "kuery",
    "query": "process.command_line:(*base64* AND *--decode*)",
    "tags": ["OS: Linux"],
})
print(result.document)
print(result.detection_complete)
print(result.diagnostics)
```

## Complete rules and incomplete drafts

- Supported detection: produces a Sigma document with `status: test` and `detection_complete=True` in the library result. The fixed status follows the approved example; it does not certify operational maturity.
- Missing/unsupported detection: preserves supported metadata, emits `status: unsupported`, omits `detection`, and reports warnings. This is a metadata draft, not a deployable Sigma rule. The converter never drops individual unsupported predicates to make a query look complete.
- Exit 0 means a document was produced, including an incomplete draft. Inspect diagnostics and the output status before using the result.
- Exit 1 means file, parsing, input-container, or serialization failure; no document is emitted for those failures. Normal argparse usage errors use exit 2.

The supplied [PowerShell example](tests/fixtures/elastic-input.yaml) converts to the [expected mapping](tests/fixtures/sigma-expected.yaml), with diagnostics emitted separately. For a real example that exceeds the supported subset:

```sh
.venv/bin/python -m rule_converter tests/fixtures/linux/elastic/bpf.json > draft.yml 2> diagnostics.jsonl
```

## Supported subset and limitations

- Flat Elastic `type: query`, `language: kuery` objects; absent type/language use logged defaults.
- Quoted exact comparisons on `process.name`, `process.executable`, `process.parent.name`, `process.parent.executable`, `host.os.type`, and `event.category`.
- `process.command_line: *term*` and `process.command_line:(*term* AND *other*)`, mapped to `CommandLine|contains` and `CommandLine|contains|all`.
- Outer AND/OR/NOT expressions and parentheses preserve Boolean precedence. Unsupported syntax or fields invalidate the entire detection translation.
- Title, UUID, description, severity, references, and supported ATT&CK metadata are mapped independently; invalid/unmapped fields have path-specific diagnostics.
- OS tags and the `winlogbeat-` index prefix can infer product. Process-only command-line expressions infer process creation. These are logged exercise assumptions; original index routing and backend analyzer/case semantics are not guaranteed to be preserved.
- EQL, ES|QL, new-terms/threshold rules, nonempty filters/exceptions, and suppression configurations produce incomplete drafts. No live SIEM execution is performed.

[Design v4](docs/design.md) specifies the exact grammar, mapping, and diagnostic contract. Four [Linux source comparisons](tests/fixtures/linux/README.md) are pinned for offline testing. Their Sigma counterparts are related detections, not equivalent golden outputs. The `detection-rules/` submodule is reference material and is not required to run the converter or tests.

## Architecture and verification

| File | Responsibility |
| --- | --- |
| `rule_converter/__main__.py` | File loading, serialization, stdout/stderr, exit codes |
| `rule_converter/__init__.py` | Public facade selecting Elastic |
| `rule_converter/models.py` | Adapter contract, shared expressions, results, diagnostics |
| `rule_converter/vendors/elastic.py` | Best-effort Elastic adapter and independent metadata |
| `rule_converter/vendors/kql.py` | Supported KQL tokenizer/parser |
| `rule_converter/vendors/elastic_metadata.py` | Logsource and ATT&CK mapping |
| `rule_converter/sigma.py` | Vendor-neutral selection/condition rendering |
| `rule_converter/diagnostics.py` | Stable diagnostic collection and deduplication |

A future vendor implements the adapter contract and emits the shared model. Adding vendor selection to the CLI is a separate extension; the current CLI always uses Elastic.

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python -m compileall -q rule_converter
```

All 59 reviewed test methods pass. [Progress](docs/progress.md) records the red-to-green milestones and remaining limitations. The red report and tests/README.md preserve the original test-author review snapshot; the current implementation result is recorded in [test-results-green.json](docs/test-results-green.json).

Repository changes follow [AGENTS.md](AGENTS.md) and [the workflow](docs/workflow.md). Reviewed tests, fixtures, and execution configuration require explicit human approval before modification.
