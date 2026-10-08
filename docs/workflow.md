# Interview workflow

This workspace is ready for a feature brief. Keep the process proportional to
the interview: a short design, a concrete risk-based test matrix, and small
behavior slices are enough to demonstrate judgment.

## 1. Design and human feedback

Use this prompt:

> Read AGENTS.md. The feature brief is: [brief]. Inspect the existing project
> and fill docs/design.md and docs/test-plan.md. Include concrete acceptance
> criteria, tradeoffs, proposed files and interfaces, and a reading guide for
> a human. Do not implement the feature yet. Present both docs for my review.

Review behavior, edge cases, architecture, and test coverage. Give feedback;
the agent revises the docs. Explicitly approve the resulting versions, then
commit them as `docs: approve feature design and test plan`. Approval is an
actual human decision; a template or an agent-written approval is insufficient.

## 2. Write tests before code

Use a separate test-author session, or have the human write the tests:

> Act as the test author. Use the approved design and test plan. Write meaningful
> tests under tests/ through the agreed public contract. Set up the runner and
> commands, but do not implement the feature. Show each behavior test failing
> for its intended missing behavior. Submit tests and configuration for review.

A minimal interface stub may be needed to obtain assertion failures instead
of import errors. Keep it free of implementation. Review test discovery, expected
results, fixtures, and all configuration. Commit as `test: cover approved
behavior (red)` and record the expected failures in docs/progress.md.

The human obtains `git rev-parse HEAD`, records the full SHA outside the
implementation workspace, and supplies it to the implementer. Register extra
test/harness/config paths with `--protect` if the default integrity paths do
not cover the chosen stack. Lock dependency versions during this phase.

## 3. Implement one behavior slice at a time

Use this prompt in the implementation session:

> Act as the feature implementer. The human-approved design and test plan are
> in docs/. Approved test baseline: [full SHA]. Extra protected paths: [paths].
> Read AGENTS.md. Tests and their execution configuration are read-only for your
> role. Implement one acceptance criterion at a time: demonstrate red, implement,
> demonstrate green, then refactor. Run targeted tests after each meaningful
> change, and full/static checks and integrity before each green milestone.
> Commit coherent slices and log real evidence in docs/progress.md. If tests
> appear wrong, report the issue; do not change them or the baseline.

Run integrity with the exact SHA supplied by the human:

```sh
python3 scripts/check_test_integrity.py <approved-full-SHA>
# Include additional paths, for example:
python3 scripts/check_test_integrity.py <approved-full-SHA> --protect test-support --protect runner.config.json
```

Commit after a passing behavior slice or useful green refactor, typically every
10–20 minutes when there is a coherent result. Avoid timer-driven incomplete
commits. Inspect `git diff` and `git diff --cached`; stage specific paths.
Use messages such as `feat: validate request input` or `refactor: isolate IO`.
Red commits are deliberate test-author milestones, not unfinished feature slices.

## 4. Independent review and demo

Have the human or independent reviewer run the approved suite against the final
code, verify integrity using the original SHA, and inspect configuration and
the implementation for test-specific shortcuts. Hidden tests should remain
outside the implementer's workspace. Demonstrate a real happy path and one
failure path, then walk through the design's reading guide and commit history.

Handoff evidence: criteria satisfied, commands and outcomes, code reading route,
known limitations, and remaining work. Never claim comprehensive coverage just
because all existing tests pass.

## What is enforced, and what is not

`AGENTS.md` defines responsibilities; it does not restrict filesystem writes.
Separate sessions or agents with the same filesystem permissions also do not
provide isolation. The local integrity script detects protected changes when
run faithfully against the original approved commit; it cannot defend against
an implementer rewriting the script or choosing another baseline.

For a technically enforced boundary, a human configures a container/sandbox or
separate account with only production paths writable. Mount approved tests,
fixtures, runner/config, and dependency manifests read-only; keep writable
cache/output directories outside tests/. Do not provide the implementation
session elevated access or permission to alter mounts. Plain chmod under the
same file owner is insufficient because that owner can restore write access.

Also run verification in reviewer-controlled CI or an external harness using
the original baseline and guard obtained from a trusted checkout. Keep the
baseline, harness, and hidden tests outside the agent's write authority. Require
that independent check before accepting changes; repository-local CI editable
by the implementer is insufficient on its own.

This setup currently provides instructions and a local detection tool. No
read-only implementation environment, hosted CI, or application test runner has
been provisioned because the feature, stack, and hosting are not yet known.
