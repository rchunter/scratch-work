# Interview workflow

Use a short design, a concrete risk-based test plan, and small behavior slices.
Timebox planning to fit the interview and agree on a small demonstrable scope.
Test ownership is a working agreement supported by human review and Git diffs.

## 1. Design and human feedback

> Read AGENTS.md. The feature brief is: [brief]. Inspect the existing project
> and fill docs/design.md and docs/test-plan.md. Include acceptance criteria,
> tradeoffs, proposed files and interfaces, and a human code reading guide.
> Do not implement the feature yet. Present both docs for my review.

Review the behavior, approach, edge cases, and coverage. The agent incorporates
feedback; the human explicitly approves the resulting design and test plan.
Commit as `docs: approve feature design and test plan`. An agent must never
write its own approval. Changing scope or behavior requires renewed review.

## 2. Write and review tests before code

The human or an explicitly assigned test author writes the tests. This can be
a separate session or a distinct test-author phase of the same session.

> Act as the test author. Use the approved design and test plan. Write meaningful
> tests through the agreed public contract. Set up the runner and commands, but
> do not implement the feature. Show intended missing-behavior failures and
> submit tests and configuration for human review.

Review test discovery, concrete expected results, fixtures, and configuration.
Setup, syntax, or dependency failures do not establish red TDD. Use a minimal
interface stub only if needed by the chosen stack. Record expected failures by
case ID and commit as `test: cover approved behavior (red)`.

## 3. Implement in small TDD slices

> Act as the feature implementer. Read AGENTS.md and the approved docs. Read and
> run the reviewed tests; do not weaken or change tests or execution settings
> without explicit human approval. Implement one acceptance criterion at a time:
> demonstrate red, implement, demonstrate green, then refactor. Test frequently,
> commit coherent milestones, and log real evidence in docs/progress.md. If a
> test seems wrong, explain the evidence and proposed change for human review.

Run targeted tests after each meaningful change and the full suite and applicable
static/build checks at each implementation milestone. A slice is green when
its tests and existing regressions pass. Tests for later slices may remain red:
record those expected failures by case ID, and allow no new failures. Never skip
them to claim success. Final acceptance requires all approved cases to pass.

Commit a passing behavior slice or useful refactor, typically every 10–20 minutes
when there is a coherent result. Inspect `git diff` and `git diff --cached` and
stage specific files. Use messages such as `feat: validate request input`.
Record actual checks and remaining red cases; label intentional red-test commits
clearly. Do not push unless requested.

Keep the design's file map and reading guide accurate as paths become concrete.
Documentation clarifications do not need another approval gate; changes to
observable behavior or scope do.

## 4. Review and demo

Review the final diff, including any test, fixture, snapshot, or runner changes.
The implementer must explain proposed test changes before applying them and get
human approval. If approved, record the reason and make the test change a
separate commit from the production fix. Tests must never be weakened merely
to make a broken implementation pass.

Run the full suite and applicable lint/type/build checks. Verify that the expected
tests were collected and there are no unexplained skips. Demonstrate a real
happy path and one failure path, then walk through the design's code reading
guide and commit history. Report completed criteria, actual check results, and
remaining limitations. Passing tests alone do not establish comprehensive coverage.

If time runs short, agree with the human on reduced scope and update the design
and test plan. Preserve final verification rather than declaring unfinished
behavior complete.
