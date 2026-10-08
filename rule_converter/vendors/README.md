# Vendor parsers

This directory contains Elastic-specific rule interpretation. The shared expression model and Sigma writer live one level above it. The converter currently selects Elastic; other vendors are future extensions.

For the KQL parser's grammar, algorithms, examples, and extension guide, read [KQL design and implementation](KQL_DESIGN.md).

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| [kql.py](kql.py) | Tokenize the supported KQL subset, enforce field/comparison policy, and build shared expression nodes |
| [elastic.py](elastic.py) | Interpret an Elastic rule, validate detection settings, preserve independent metadata, and turn query errors into diagnostics |
| [elastic_metadata.py](elastic_metadata.py) | Derive logsource hints and map ATT&CK metadata |
| [../models.py](../models.py) | Expression nodes, VendorAdapter protocol, Translation, and ConversionResult |
| [../sigma.py](../sigma.py) | Convert shared expressions into Sigma selections and conditions |

## Use the parser directly

Run this Python example from the repository root in the configured environment:

```python
from rule_converter.vendors.kql import parse_query

expression = parse_query(
    'process.command_line:(*powershell* AND *IEX* AND *Net.WebClient*)'
)
print(expression)
```

Result:

```text
Match(field='CommandLine', operator='contains_all', values=('powershell', 'IEX', 'Net.WebClient'))
```

`parse_query` takes the query string itself, after JSON/YAML decoding. It returns an expression, not a Sigma document. Use `rule_converter.convert_rule` when you have a full rule and want metadata, logsource, and diagnostics as well.

## Supported query forms

| Form | Example |
| --- | --- |
| Exact comparison | `process.name: "bash"` |
| Single substring | `process.command_line: *curl*` |
| All substrings on one field | `process.command_line:(*curl* AND *example.org*)` |
| Boolean composition | `process.name: "bash" OR process.name: "sh"` |
| Grouping and negation | `(process.name: "bash" OR process.name: "sh") AND NOT process.parent.name: "trusted"` |

Operators are case-insensitive; precedence is NOT, then AND, then OR. Exact comparisons use the six-field allowlist in [the detailed guide](KQL_DESIGN.md#field-and-value-policy). Command-line comparisons support only the substring forms shown above.

This is a bounded KQL-to-expression translator. Unquoted exact values, arbitrary fields, field-level OR groups, ranges, existence queries, and general wildcard patterns are unsupported. EQL and ES|QL need different parsers.

## Errors and best effort

A supported parse consumes the whole query. Otherwise `QueryError` identifies a zero-based character offset and explains the failure without echoing the query value. The Elastic adapter catches this expected error, logs diagnostics, retains metadata, and omits the entire detection. It never removes one failed condition from an otherwise usable query.

The CLI emits diagnostics as JSON Lines on stderr. Unsupported detections produce metadata drafts with `status: unsupported`; they are not deployable Sigma detections. See the [main usage guide](../../README.md#complete-rules-and-incomplete-drafts) for exit behavior.

## Read, verify, and extend

Read `parse_query`, `_tokens`, `_Parser.expression`, `_Parser.conjunction`, `_Parser.unary`, and `_Parser.comparison`, then follow the result into `sigma.py`. The [implementation walkthrough](KQL_DESIGN.md#implementation-walkthrough) explains each stage.

From the repository root:

```sh
.venv/bin/python -m unittest tests.test_converter tests.test_sigma -v
```

The detailed guide links existing cases and separates their assertions from untested limits. Before expanding the accepted language, update the feature design, obtain human approval, and have the assigned test author add cases. Existing tests, fixtures, and execution settings are review-owned. Add another vendor through the shared adapter/model contract rather than teaching the KQL parser another language.
