# Detection Rule Converter — test plan

Status: APPROVED v4 baseline, 2026-10-08. Human approved the design and requested test generation from repository examples. Human authorized committing the authored tests and starting implementation on 2026-10-08.

## Coverage matrix

Exercise public convert_rule or the CLI. The human's fixture pair is the primary acceptance example: compare ConversionResult.document with the entire expected YAML mapping; assert diagnostics separately. Do not regenerate or edit the expected fixture to fit implementation. Whitespace, quoting style, and mapping key order are not contractual. Test-author-owned variants cover generalization beyond the fixture.

| Case | AC | Concrete scenario | Expected result | Level / priority |
| --- | --- | --- | --- | --- |
| T-01 | 01/03/04 | Supplied fixture pair, including omitted language | Full semantic equality with expected YAML: selection/contains-all, mapped field, status, logsource, tags, and no extra keys | Unit / must |
| T-02 | 02 | `process.name: "a" OR process.name: "b" AND process.name: "c"` | Three selections; `(selection_1 or (selection_2 and selection_3))` | Unit / must |
| T-03 | 02 | `(process.name: "a" OR process.name: "b") AND NOT process.parent.name: "c"` | Grouping, negation, and repeated fields preserved | Unit / must |
| T-04 | 02 | Lowercase operators; nested NOT; quoted spaces, escaped quotes/backslashes | Decoded strings and operator semantics preserved | Unit / must |
| T-05 | 03 | Name/description/UUID/severity/references | Exact valid mappings and `status: test` when detection is complete | Unit / must |
| T-06 | 03 | Optional metadata absent; non-UUID rule_id | Optional keys omitted; supplied invalid ID diagnosed; missing optional fields quiet | Unit / must |
| T-07 | 04 | Explicit unsupported type/language, nonempty filters/exceptions, configured suppression | Metadata survives; detection omitted/status unsupported; setting diagnosed. Absent type/language uses logged defaults | Unit / must |
| T-08 | 04 | Unquoted exact value, prefix/suffix/internal wildcards, existence, range, unknown field, trailing token, field-group OR/NOT/nesting | Metadata-only draft and query diagnostic; no surviving detection fragments; full query consumed for successful translation | Unit / must |
| T-09 | 04 | Empty value/query, unmatched parentheses, unterminated string, unsupported escape, empty wildcard literal | Draft with no detection, incomplete flag/status, and actionable diagnostics | Unit / must |
| T-10 | 03/04 | Title lengths 1/256 versus empty/257; valid versus unknown severity | Valid values preserved; invalid title gets fallback/truncation with diagnostics; invalid severity omitted and diagnosed | Unit / must |
| T-11 | 05 | Supplied input in JSON/.yaml/.yml; CLI receives only path | Exit 0; parsed document equals fixture; stderr contains valid JSONL diagnostics for assumptions and untranslated fields | Integration / must |
| T-12 | 06 | Missing file, invalid JSON/YAML, and non-object root | Exit 1, empty stdout, useful stderr diagnostics | Integration / must |
| T-13 | 07 | Convert A, B with different metadata, A again; compare deep copies | Stable document and diagnostics, input unchanged, no state leakage | Unit / must |
| T-14 | 03 | OS tags Windows/Linux/macOS; no OS tags plus mixed winlogbeat/endpoint index list | Agreed OS tag determines product; otherwise winlogbeat prefix produces windows | Unit / must |
| T-15 | 03 | Unknown/conflicting OS tags with winlogbeat index; duplicate agreeing tags | Unknown/conflicting tags diagnosed and suppress product/fallback; duplicates yield one product | Unit / must |
| T-16 | 03 | Command-line query over process fields; command-line query mixed with host.os.type; process.name-only query without hints | Category only for declared command-line/process-only heuristic; definition fallback when no product/category | Unit / must |
| T-17 | 01/02 | Different contains-group literals, reordered literals, and a single contains term | Generalized contains-all list in source order; single term uses contains scalar; standalone selection named selection | Unit / must |
| T-18 | 02 | Contains-group combined with exact comparison and NOT via outer Boolean expression | Numbered selections; contains-all retained; condition preserves Boolean structure | Unit / must |
| T-19 | 03 | Structured tactic/parent/subtechnique, duplicate IDs, parent without valid subtechniques | Tactics before techniques, stable deduplication, child suppresses parent; parent used when no valid child | Unit / must |
| T-20 | 03 | Flat ATT&CK tags with/without structured MITRE entries; unrelated/invalid metadata | Fallback only without structured entries; unknown tags diagnosed and omitted; tags omitted if empty | Unit / must |
| T-21 | 01/03 | Different title/UUID/literals; PowerShell-like title with no source hints | No hardcoded fixture values or title-based source inference | Unit / must |
| T-22 | 04/08 | Missing query/name; invalid severity/UUID and valid description in one rule | Metadata draft retains description; title fallback; no detection; status unsupported; all independent issues reported | Unit / must |
| T-23 | 08 | Unknown top-level object, risk_score, invalid reference entry, malformed threat child plus valid siblings | Stable path/code diagnostics; valid references/threat siblings translate; no silent omission | Unit / must |
| T-24 | 04/02 | Supported predicate AND/OR/NOT unsupported predicate in multiple positions | Omit entire detection; never emit a weakened condition or match-all placeholder | Unit / must |
| T-25 | 05/08 | CLI conversion with unsupported query and valid metadata | Exit 0, metadata-only YAML draft, JSONL warnings, no log text mixed into stdout | Integration / must |
| T-26 | 07/08 | Missing optional values, duplicate represented tags, lost index routing, inferred category/product | Quiet absent optional fields; handled duplicates not reported as losses; routing loss and assumptions diagnosed | Unit / must |
| T-27 | 09 | Direct Match/expression model input to shared Sigma renderer, no Elastic input object | Correct exact/contains/contains_all and Boolean output; no source-vendor fields required | Unit / must |
| T-28 | 08 | Non-string name, null severity, malformed tags/index/threat containers | Best-effort diagnostics and valid sibling metadata; no unhandled type errors | Unit / must |


For T-02/T-03/T-18 use an independent test-owned Boolean evaluator over selection truth assignments to check the emitted condition against intended truth tables. Do not use eval. For contains-all, exercise synthetic command lines containing all, some, or none of the literals using a small test-owned interpretation of the agreed modifier semantics. These checks validate translation structure and meaning, not live SIEM execution.

## Test ownership and red evidence

The human approves both documents and assigns a test author before executable tests are written. The existing fixture contents are human authored. A test author may create minimal public-interface stubs raising NotImplementedError to permit successful discovery, but does not implement the feature during that phase. Review tests and runner configuration before production implementation.

Record each behavior's intended assertion/unimplemented-contract failure, collected case count, and case ID. Import, dependency, syntax, or discovery failures do not count as red TDD. Log expected failures for later slices while earlier cases become green. The feature implementer may read/run tests but cannot change tests, fixtures, snapshots, or their execution without explicit human approval; approved corrections are separate from production fixes.

Temporary files isolate CLI IO; use the active interpreter for subprocess tests. No runtime network, mocking conversion, or fixture regeneration. Tests must generalize beyond the exact sample values. Unknown/unsupported values are tested for explicit diagnostics and independent-field recovery. Unsupported detection must never turn into silently simplified logic. Assert diagnostic codes/paths and reason content without coupling tests to punctuation.

## Proposed commands

The commands below have been used for test-author verification where recorded in progress.md. The feature suite is deliberately red against interface stubs.

| Check | Command | Scope |
| --- | --- | --- |
| Runtime | `python3 --version` | Python 3.11+ |
| Setup | `python3 -m venv .venv` then `.venv/bin/python -m pip install -r requirements.txt` | PyYAML pinned by test author |
| Targeted library | `.venv/bin/python -m unittest tests.test_converter -v` | Library cases |
| Shared rendering | `.venv/bin/python -m unittest tests.test_sigma -v` | Vendor-neutral model contract |
| Targeted CLI | `.venv/bin/python -m unittest tests.test_cli -v` | File-only CLI contract |
| Full suite | `.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v` | All cases, count checked against reviewed manifest |
| Syntax | `.venv/bin/python -m compileall -q rule_converter` | Production syntax |
| Diff hygiene | `git diff --check` | Whitespace errors |

Test author supplies tests/__init__.py for module discovery. There is no build step. Separate lint/type tools are deferred to limit setup; compilation is not a substitute for tests.

Concurrency, authorization, accessibility, load, and network recovery do not apply to this stateless local tool. Incomplete mappings and wrong field types are in scope; malformed JSON/YAML and non-object roots get a fatal input diagnostic. Safe YAML loading is required. No external Sigma validator or live backend equivalence is promised. Source inference and missing-language conventions are verified as declared heuristics, not inferred facts about telemetry.

## Human review

- Design/test-plan baseline: v4 / v4. Human approved proceeding to test generation on 2026-10-08.
- Human direction: example alignment, best-effort conversion with logs, and modular vendor parsing. Fixtures remain unchanged.
- Test author: this session, assigned by the human. Human authorized the tests/configuration/contracts and implementation: “Commit the test structure and start implmentation.”
- Final acceptance: all reviewed cases pass without unexplained skips, syntax/diff checks pass, complete example, incomplete draft, and fatal-input CLI demos recorded in docs/progress.md.

## Repository-derived cases and authored test evidence — 2026-10-08

The human requested Elastic repository examples and matching Sigma Linux rules. Four pinned comparisons are documented in [the corpus guide](../tests/fixtures/linux/README.md). No exact semantic equivalent was established among these pairs; the Sigma references are not golden converted outputs.

| Case | AC | Real source / expected approved behavior |
| --- | --- | --- |
| R-01 | 03/04/08 | Base64 ES|QL: preserve metadata, log unsupported semantics, emit no detection; do not substitute Sigma's simpler base64 rule |
| R-02 | 03/04/08 | Chattr EQL: preserve metadata and report incomplete detection; retain distinction between attribute removal/addition and exclusions |
| R-03 | 03/04/08 | Insmod EQL: report incomplete detection; do not replace process logic with Sigma auditd syscall predicates |
| R-04 | 03/04/08 | BPF KQL: query uses fields/syntax outside v4; report query limitation without dropping dataset/process constraints |

The complete original Elastic [rule] objects were serialized from TOML to JSON for the approved file contract. No query normalization/simplification was performed. Fixture-integrity tests verify pinned bytes and query hashes offline. A separate explicitly synthetic Linux KQL case is a successful conversion test.

59 test methods are authored across test_converter.py, test_sigma.py, test_cli.py, and test_linux_references.py. On Python 3.14.6 with PyYAML 6.0.3, 3 corpus-integrity methods pass; all 56 behavior methods are expected red. Parameterized variants produce 10 assertion-failure reports and 109 NotImplementedError reports. Zero skips; no import/dependency/syntax failures establish the red evidence. The 56 red methods fail because the public contracts are intentionally unimplemented. Exact per-method results and case IDs are in [test-results-red.json](test-results-red.json).

Data-only models and NotImplementedError stubs enable valid discovery. They do not implement conversion. Test-author review of source comparisons and discovered failures is complete; human subsequently approved committing the test structure and starting implementation on 2026-10-08. This closes the test-review gate.
