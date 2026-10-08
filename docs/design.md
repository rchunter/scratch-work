# Detection Rule Converter — design

Status: APPROVED v4, 2026-10-08. Human approved the design and requested test generation; this session is now the explicitly assigned test author.

## Goal and scope

Translate as much as possible from one potentially incomplete Elastic Security rule supplied as JSON or YAML into a Sigma rule or an explicitly incomplete YAML draft, logging every untranslated source field. The primary acceptance example is `tests/fixtures/elastic-input.yaml` → `tests/fixtures/sigma-expected.yaml`. Expected output is compared as parsed YAML, including detection structure and metadata; whitespace, quoting style, and mapping key order are not contractual.

Use Python 3.11+, argparse/json/unittest from the standard library, and PyYAML for safe loading and serialization. The 60-minute exercise covers a small query subset, metadata mapping, diagnostics, CLI, and explicit incomplete-result handling. No service, UI, runtime network access, or backend execution is required.

Accept a flat object even when fields are absent or have unexpected types. For detection translation, accept `type: query` and `language: kuery`; when either is absent, assume the supported query/KQL subset and log that assumption. Explicit other types or languages prevent detection translation but do not prevent metadata conversion. Nested repository envelopes, TOML, NDJSON, and batches remain unsupported as input containers. The `detection-rules/` submodule is reference material, not an input adapter or runtime dependency.

## User interface

```sh
python -m rule_converter tests/fixtures/elastic-input.yaml > rule.yml
```

The rule file is the only required input; no product/category flags or sidecar configuration. Read UTF-8 `.json`, `.yaml`, or `.yml`. Write the translated rule or incomplete draft to stdout. Write diagnostics as JSON Lines to stderr, one object per issue. Both outputs are deterministic; build and serialize the entire result before writing stdout.

Exit 0 means an output document was produced, possibly with warnings. Exit 1 is reserved for unreadable files, invalid JSON/YAML, a non-object root, or serialization failure, with no output document. Warnings do not fail the command. The library returns diagnostics rather than logging directly:

```python
convert_rule(rule: dict) -> ConversionResult
# ConversionResult(document: dict, diagnostics: list[Diagnostic],
#                  detection_complete: bool)
# Diagnostic(severity: str, code: str, path: str, message: str)
```

`convert_rule` remains the Elastic-compatible public facade for this version. It delegates to the Elastic adapter and shared Sigma writer. The result is pure, deterministic, and does not mutate input. Expected conversion gaps become diagnostics, not exceptions. Fatal container/IO failures are handled at the CLI boundary; unexpected programming errors are not disguised as successful conversion.

## Best-effort behavior and diagnostics

Translate independent fields even if other fields cannot be handled. Missing optional fields do not generate noise. A present invalid or unmapped field generates a diagnostic identifying its source path and the reason. For example:

```json
{"severity":"warning","code":"unmapped_field","path":"risk_score","message":"No Sigma mapping; field omitted."}
{"severity":"warning","code":"invalid_value","path":"severity","message":"Unsupported level; field omitted."}
{"severity":"warning","code":"unsupported_query","path":"query","message":"Unsupported field at character 24; detection omitted."}
```

Use dotted paths and zero-based array indexes, such as `threat[0].technique[0].subtechnique[0].id`. Unknown source objects may be reported once at their highest unhandled path; handled objects are inspected for unhandled children. Log each issue once in stable path/code order. Messages describe fields and reasons without copying entire input values or queries.

Fatal CLI diagnostics use severity `error`, code `input_error` or `output_error`, and path `$` for the document or file boundary. Recoverable diagnostic codes: `unmapped_field`, `invalid_value`, `missing_required`, `assumed_value`, `unsupported_query`, `unsupported_semantics`, and `incomplete_detection`. Severity is `info` for assumptions and intentionally superseded/redundant metadata, `warning` for omitted information or incomplete detection. Duplicates and data represented by another mapped source count as handled. For example, the fixture's flat Execution/T1059.001 tags are already represented by its structured threat mapping. Parent technique metadata superseded by a valid subtechnique is handled; unrelated vendor tags or unused threat children are reported. Index-to-product inference is lossy: log that routing was not preserved. Unsupported scheduling/actions/risk scores/authors/dates and unknown top-level fields are logged as omitted, not silently dropped.

Detection is an atomic translation boundary. If a query is missing, malformed, or contains an unsupported field/operator anywhere, retain translated metadata but omit the entire `detection` section. Do not remove individual predicates: dropping a condition under AND, OR, or NOT changes meaning. Report the first query failure with position/field when available; exhaustive parser recovery is outside the timebox. Likewise, nonempty filters/exceptions, non-null suppression, or an explicit unsupported rule type/language make detection incomplete. Continue converting all independent metadata and collecting their diagnostics.

Set `detection_complete: false`, emit `status: unsupported`, and add an `incomplete_detection` warning when detection cannot be translated. This output is a **metadata draft, not a valid deployable Sigma detection rule**. Never fabricate a match-all or empty selection. Otherwise set `detection_complete: true` and preserve the fixture's `status: test`. That flag means the supported source detection was translated, not that live backend equivalence or testing has been proven.

Missing/blank/non-string name uses `title: Untitled converted rule` with a diagnostic; names over 256 characters are truncated with a diagnostic. Invalid optional values are omitted with diagnostics. Missing type/language and inferred logsource generate assumption diagnostics. Your supplied output mapping stays unchanged, while its conversion additionally logs omitted risk_score, assumed language, and logsource assumptions on stderr.

## Modular architecture

Keep format loading, vendor interpretation, and Sigma rendering separate:

1. The CLI loader turns JSON/YAML into a mapping without vendor knowledge.
2. A `VendorAdapter` interface exposes `translate(source: dict) -> Translation`. Only `ElasticAdapter` is implemented now; it owns Elastic fields, metadata, logsource heuristics, and the KQL parser.
3. `Translation` holds target metadata, an optional vendor-neutral detection expression, a detection-complete flag, and diagnostics. Shared expression types are Match(field, operator, values), And, Or, and Not; match operators are exact, contains, and contains_all. A missing expression represents incomplete detection.
4. The shared Sigma writer turns this model into selections, conditions, and the final document. It does not inspect Elastic fields, source query text, or vendor names. The facade combines the document and diagnostics in ConversionResult.

No dynamic plugin discovery, runtime imports, or vendor autodetection is needed for one vendor. The current file-only facade selects Elastic explicitly. A later vendor adds an adapter/parser that emits the shared model; selecting that vendor in the CLI is a future reviewed interface decision. Do not pretend an arbitrary unknown rule is Elastic based on weak field-name guesses. Keep the adapter contract small and avoid a general SIEM framework.

## Query conversion

Retain Boolean AND/OR/NOT and parentheses from v2, and add the specific field-scoped wildcard conjunction needed by the example:

```text
expression := or_expr
or_expr    := and_expr (OR and_expr)*
and_expr   := unary (AND unary)*
unary      := NOT unary | '(' expression ')' | comparison
comparison := field ':' quoted_string
            | field ':' contains_term
            | field ':' '(' contains_term (AND contains_term)+ ')'
contains_term := '*' literal '*'
```

Operators are case-insensitive, with NOT > AND > OR precedence. A contains-term literal is nonempty and contains no whitespace, parentheses, colon, quotes, backslash, `*`, or `?`; dots and hyphens are allowed. Thus `*Net.WebClient*` is supported. Only surrounding stars are stripped, preserving literal spelling and order. Prefix-only, suffix-only, embedded wildcards, existence queries, OR/NOT inside a field group, nested field groups, ranges, and free text remain unsupported. Full Boolean expressions outside field groups remain supported.

Quoted strings are nonempty, contain no wildcards, and support escaped double quotes and escaped backslashes only. Unquoted exact values are unsupported. Consume the entire query; any unsupported token makes detection incomplete and produces a diagnostic with its position.

Supported fields:

| Elastic field | Output field | Supported comparisons |
| --- | --- | --- |
| `process.command_line` | `CommandLine` | Contains term or contains-AND group only |
| `process.name`, `process.executable` | Same ECS name | Quoted exact value |
| `process.parent.name`, `process.parent.executable` | Same ECS name | Quoted exact value |
| `host.os.type`, `event.category` | Same ECS name | Quoted exact value |

This is deliberately a partial field mapping. The example uses Sigma's CommandLine convention; retained ECS fields in other rules require a compatible backend pipeline. Exact command-line matching and comprehensive ECS-to-Sigma field mapping are deferred.

The Elastic adapter tokenizes and parses via recursive descent and maps supported comparisons into the shared Match/And/Or/Not model. Do not split raw query text on operators. The vendor-independent Sigma writer applies these emission rules:

- One standalone comparison/group uses selection name `selection` and condition `selection`.
- A contains term emits `CommandLine|contains: literal`.
- A contains-AND group emits `CommandLine|contains|all: [literal, ...]` in query order. Do not collapse multiple terms to a plain list, which would lose the all-terms requirement.
- A larger Boolean expression emits `selection_1`, `selection_2`, etc. for each comparison/group in traversal order, with fully parenthesized conditions. Preserve repeated fields, grouping, and negation without overwriting selections.

The supplied query produces exactly:

```yaml
detection:
  selection:
    CommandLine|contains|all:
      - powershell
      - IEX
      - Net.WebClient
  condition: selection
```

Nonempty `filters` or `exceptions_list`, and non-null `alert_suppression`, produce unsupported-semantics diagnostics and metadata-only drafts. Scheduling, risk scores, and alert actions are omitted with diagnostics.

## Log-source policy

To reproduce the example with only its file, adopt explicit exercise heuristics:

1. Recognize `OS: Windows`, `OS: Linux`, and `OS: macOS` tags as product hints. If OS tags exist, use their single agreed mapped product; conflicting or unknown OS tags leave product unset and disable index fallback.
2. With no OS tags, any index pattern beginning `winlogbeat-` supplies the `windows` hint, even alongside other patterns. This assumes the rule targets Windows telemetry; the example's mixed index list does not prove that restriction.
3. If the query contains a `process.command_line` comparison/group and every comparison is on a `process.*` field, emit `category: process_creation`. This assumes process telemetry represents process creation. It is an exercise convention, not a conclusion established by a command-line field alone.
4. Emit available product/category fields and omit service. If neither is available, emit a definition beginning `Elastic rule using ECS fields.` and, for a nonempty index list, append ` Source index patterns: ` plus the patterns in original order, comma-separated. Otherwise omit definition, matching the fixture.

Do not infer a platform from PowerShell text, executable names, or titles. These heuristics generalize over fields/index prefixes rather than hardcoding the example's title, UUID, or query literals. Source routing is not preserved exactly across backends; production deployment requires review of these assumptions. Log each applied heuristic with an assumed_value diagnostic; exact index routing is not translated. Invalid index/tag entries are omitted with path-specific diagnostics. A future stricter mode is outside this exercise.

## Metadata and ATT&CK mapping

| Input | Output | Policy |
| --- | --- | --- |
| `name` | `title` | Preserve 1–256 characters; otherwise use the fallback/truncation policy and log |
| `rule_id` | `id` | Preserve canonical UUID; otherwise omit and log if present |
| `description` | `description` | Preserve nonempty strings; omit invalid supplied values and log |
| `severity` | `level` | Preserve low/medium/high/critical; omit absent; omit and log invalid values |
| `references` | `references` | Preserve valid nonempty string entries; omit/log invalid entries; omit key if empty |
| No source field | `status: test` | For complete detection; use unsupported for incomplete drafts; not evidence of executed validation |
| `threat`, fallback `tags` | `tags` | Mapping below |

For structured `threat` entries whose framework is `MITRE ATT&CK`, emit tactic tags first, then technique tags, preserving source order within each group and deduplicating output. Map recognized tactic names to their lowercase underscore form (`Execution` → `attack.execution`; recognize standard enterprise tactic names only). For each technique, emit valid subtechnique IDs when supplied; otherwise emit the parent technique ID. Lowercase and prefix IDs with `attack.`. Technique IDs must match `T` plus four digits, optionally followed by a dot and three digits. A subtechnique ID must include that suffix. Recognized tactic names are Reconnaissance, Resource Development, Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command and Control, Exfiltration, and Impact (case-insensitive exact names). Omit and diagnose unknown tactic names/invalid IDs rather than invent tags; process valid siblings independently.

If there are no structured MITRE ATT&CK entries, apply the same recognized tactic-name/technique-ID mapping to flat tags. Omit and diagnose other vendor tags. If structured entries exist, do not merge flat tags; report flat tags not already represented by the mapped structured metadata. Omit the tags key if no tags were mapped. Do not emit parent technique tags when valid subtechniques exist: the example yields `attack.execution` and `attack.t1059.001`, without `attack.t1059`.

Omit and log authors, dates, risk_score, and other unmapped vendor metadata. Invalid threat containers/entries are diagnosed at their source paths while valid sibling entries continue converting.

## Acceptance criteria

| ID | Observable result |
| --- | --- |
| AC-01 | Supported exact/contains comparisons map to a single selection; the supplied fixture pair matches completely as parsed YAML |
| AC-02 | Boolean operators, precedence, parentheses, and field-scoped contains-AND preserve the intended logic |
| AC-03 | Metadata, complete/incomplete status, ATT&CK tags, and logsource follow the explicit best-effort policies above |
| AC-04 | Unsupported/missing detection yields a metadata-only draft, status unsupported, detection_complete false, and diagnostics; independent fields still convert |
| AC-05 | JSON and YAML files with only a positional path produce equivalent documents and JSONL diagnostics; exit 0 even with warnings |
| AC-06 | Unreadable/unparseable/non-object inputs produce exit 1, readable stderr diagnostics, and empty stdout |
| AC-07 | Repeated calls produce deterministic documents/diagnostics, preserve input, and retain no state |
| AC-08 | Invalid/unmapped fields and assumptions have path-specific diagnostics; valid siblings translate; missing optional fields are quiet |
| AC-09 | Elastic interpretation is isolated behind the adapter; shared Sigma rendering accepts vendor-neutral expressions without importing Elastic |

## Proposed files and reading route

| Path | Responsibility |
| --- | --- |
| `rule_converter/__init__.py` | Public convert_rule facade selecting Elastic and combining translation/rendering |
| `rule_converter/models.py` | Diagnostic, ConversionResult, Translation, VendorAdapter Protocol, shared expression dataclasses |
| `rule_converter/vendors/elastic.py` | ElasticAdapter: field/metadata/logsource/ATT&CK mapping and diagnostics |
| `rule_converter/vendors/kql.py` | Elastic KQL tokenizer/parser and source-position errors |
| `rule_converter/sigma.py` | Vendor-neutral render_sigma: selection/condition emission and draft assembly |
| `rule_converter/__main__.py` | File-only CLI, safe loading, YAML stdout, JSONL stderr, fatal errors |
| `requirements.txt` | PyYAML pinned to tested version by test author |
| `tests/test_converter.py` | Facade cases, fixture-pair assertion, best-effort diagnostics |
| `tests/test_sigma.py` | Direct shared-model rendering tests without Elastic source input |
| `tests/test_cli.py`, `tests/__init__.py` | CLI integration tests and test discovery |
| `tests/fixtures/elastic-input.yaml`, `tests/fixtures/sigma-expected.yaml` | Human-authored primary example; preserve contents |
| `README.md` | Install/run instructions, incomplete-draft behavior and inference assumptions |
| `docs/progress.md` | Reviews and actual validation evidence |

Read the fixture pair, then `__main__.py:main`, the facade, `models.py`, `vendors/elastic.py:ElasticAdapter.translate`, `vendors/kql.py`, and `sigma.py:render_sigma`. The example loads without language, records its assumption, parses the command-line group into Match(CommandLine, contains_all, values), derives metadata/logsource, and renders the unchanged expected document plus separate diagnostics. Follow an unsupported-query case to see metadata retained without a detection section.

To add a vendor, implement VendorAdapter and its parser, returning shared expressions/metadata/diagnostics; the Sigma writer remains unchanged for existing operators. Verify the renderer directly with shared-model test inputs, not a production fake adapter. No second vendor is implemented in this exercise.

Changes to supported syntax, mapping, or inference policy require updated acceptance criteria and human review before tests and implementation.

## Tradeoffs, schedule, and validation

The example defines a useful interview slice but requires assumptions absent from the source. We explicitly accept missing-language, telemetry, and status conventions to match it. Preserving query structure does not guarantee analyzer/case equivalence across Elastic and every Sigma backend. No live SIEM equivalence or full vendor coverage is claimed.

Suggested 60 minutes: 10 design/review, 10 test authoring/red review, 25 implementation, 10 verification/demo, 5 buffer. The broader v4 scope may require reducing secondary features through human review if the timebox becomes tight.

Slices: query conversion (AC-01/02); metadata/logsource/diagnostics (AC-03/04/07/08); CLI and fixture integration (AC-05/06); shared-model rendering checks (AC-09); full checks and demo. Use [test plan](test-plan.md). Tests are written by the human or an explicitly assigned test author before production code. Revert production slices if necessary; do not weaken reviewed tests.

## Sources

- [Elastic KQL reference](https://www.elastic.co/docs/reference/query-languages/kql): Boolean, grouping, and wildcard syntax; this design supports a subset only.
- [Sigma modifiers](https://sigmahq.io/docs/basics/modifiers.html): contains/all output semantics.
- [Sigma rules specification](https://sigmahq.io/sigma-specification/specification/sigma-rules-specification.html) and [tag conventions](https://sigmahq.io/sigma-specification/specification/sigma-appendix-tags.html): output structure and tag namespaces.

## Human review

- Approved version: v4.
- Human direction: align with the example, translate incomplete inputs best-effort with logs, and keep vendor parsing modular.
- Human approval evidence (2026-10-08): “The design looks good. Lets start by generating test cases.”
- Test author: this Codex session, explicitly assigned by the same request. Production implementation remains outside this phase.
- Main assumptions to review: JSONL diagnostics on stderr; metadata-only drafts for incomplete detection; exit 0 for produced drafts; title fallback; small adapter interface; prior fixture/inference conventions retained.
