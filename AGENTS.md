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
  This includes fixtures, harnesses, and runner/CI configuration. Explain any
  proposed test or execution change and obtain explicit human approval before
  applying it. Record approved corrections separately from the production fix.
- Demonstrate each new behavior test fails for the intended missing behavior.
  Broken setup, discovery, dependencies, or syntax do not count as red TDD. Then implement the smallest
  coherent change, rerun targeted tests, and refactor while green.
- If a test appears wrong, report the evidence and proposed correction to the
  human/test author. Apply a correction only after explicit human approval.
- Never hardcode test inputs, detect test execution to change behavior, mock
  the feature itself, suppress errors, or report unexecuted checks as passing.

## Readable code

- Use domain names, small cohesive modules, explicit interfaces, and simple
  control flow. Keep business logic separate from IO where useful.
- Follow the existing stack and conventions. Add abstractions or dependencies
  only when justified by the approved design.
- Comments explain decisions and constraints. Avoid narrating obvious code.
- Keep the design's file map and human reading guide accurate. Documentation
  clarifications may proceed; changed scope or behavior needs human review.

## Verification and progress

- Run targeted tests after every meaningful behavior change. Run the full suite
  and applicable lint/type/build checks before implementation milestones.
- A slice is green when its tests and existing regressions pass. Tests for later
  slices may remain red: log their expected failures by case ID and allow no new
  failures. Never skip them to claim success. Final acceptance requires the full
  suite and applicable checks to pass, with no unexplained skips or missing tests.
- Commit small coherent milestones: approved design, reviewed failing tests,
  each passing behavior slice, refactor, and final review fixes. A deliberate
  red-test commit must be named `test: ... (red)` and record its expected failure.
- Inspect staged diffs; stage specific files. Never commit secrets, unrelated
  work, or fabricate successful validation. Do not amend or rewrite history
  unless asked. Do not push unless requested.
- Record commands, results, requirement IDs, and commit milestones in
  docs/progress.md. Report limitations and remaining risks honestly.
