# Working agreement

Read README.md and docs/workflow.md before feature work. These instructions
apply to this repository. Keep additional directory instructions short.

## Design before implementation

- First fill docs/design.md and docs/test-plan.md for the requested feature.
- Explain the user behavior, acceptance criteria, tradeoffs, proposed files,
  dependencies, and a reading route through the code.
- Present both documents to the human. Stop feature implementation until the
  human explicitly approves their versions. Never approve your own work.
- Incorporate feedback. If scope or observable behavior changes, return for
  review before implementing that change.

## Test ownership and TDD

- The human or an explicitly assigned test author writes tests from the approved
  acceptance criteria before production code. Test authors do not implement
  the feature in that phase. Do not automatically spawn other agents.
- The feature implementer may read and run tests but must not edit, delete,
  skip, weaken, regenerate snapshots, or alter their discovery or execution.
  This includes fixtures, harnesses, dependencies, runner configuration,
  integrity checks, and CI configuration.
- Before implementation, the human records the approved test commit SHA and
  gives the implementation session that SHA as its trusted baseline.
- Demonstrate each new behavior test fails for the intended missing behavior,
  not a broken import, environment, or syntax error. Then implement the smallest
  coherent change, rerun targeted tests, and refactor while green.
- If a test appears wrong, report the evidence and proposed correction to the
  human/test author. Do not correct it as the implementer.
- Never hardcode test inputs, detect test execution to change behavior, mock
  the feature itself, suppress errors, or report unexecuted checks as passing.

## Readable code

- Use domain names, small cohesive modules, explicit interfaces, and simple
  control flow. Keep business logic separate from IO where useful.
- Follow the existing stack and conventions. Add abstractions or dependencies
  only when justified by the approved design.
- Comments explain decisions and constraints. Avoid narrating obvious code.
- Keep the design's file map and human reading guide accurate.

## Verification and progress

- Run targeted tests after every meaningful behavior change; run the full suite
  and configured lint/type/build checks before green milestones and handoff.
- Run the test integrity check against the human-provided baseline before each
  implementation commit. It supplements, not replaces, actual feature tests.
- Commit small coherent milestones: approved design, reviewed failing tests,
  each passing behavior slice, refactor, and final review fixes. A deliberate
  red-test commit must be named `test: ... (red)` and record its expected failure.
- Inspect staged diffs; stage specific files. Never commit secrets, unrelated
  work, or fabricate successful validation. Do not amend or rewrite history
  unless asked. Do not push unless requested.
- Record commands, results, requirement IDs, and commit milestones in
  docs/progress.md. Report limitations and remaining risks honestly.
