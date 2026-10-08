# Feature test plan

Status: DRAFT — complete after the feature brief and before implementation.

## Coverage matrix

Replace TBD rows with concrete inputs and outcomes. Include every acceptance
criterion, prioritize by risk, and explain categories that do not apply.

| Case | AC ID | Scenario / concrete input | Expected result | Level | Priority |
| --- | --- | --- | --- | --- | --- |
| T-01 | AC-01 | Primary successful flow: TBD | TBD | TBD | Must |
| T-02 | TBD | Empty/missing/malformed input: TBD | TBD | TBD | TBD |
| T-03 | TBD | Minimum/maximum/off-by-one boundaries: TBD | TBD | TBD | TBD |
| T-04 | TBD | Dependency failure and recovery: TBD | TBD | TBD | TBD |
| T-05 | TBD | Repeated operations/state transitions: TBD | TBD | TBD | TBD |
| T-06 | TBD | Existing behavior regression: TBD | TBD | TBD | TBD |

Consider authorization, unsafe input, concurrent requests, timeout/cancellation,
accessibility, and performance when the feature makes these relevant. Use
integration tests for real boundaries and a small end-to-end smoke test where
valuable. Avoid tests that only mirror private implementation details.

## Test design and trustworthy failures

- Test through public contracts; assert meaningful outputs and side effects.
- Fix time/randomness and isolate state. Mock external boundaries only; do not
  mock the behavior being verified. Avoid arbitrary sleeps and network reliance.
- Confirm setup and discovery work. Record expected assertion failures before
  implementation; an environment failure does not demonstrate red TDD.
- Make each criterion independently diagnosable. Use hidden reviewer-owned
  cases or mutation checks for important rules when time permits.
- The test author handles additions/corrections through independent review,
  including snapshot changes. The implementer reports requests with evidence.

## Commands and environment

Fill these in before implementation. No application suite exists yet.

| Check | Exact command | Expected scope |
| --- | --- | --- |
| Setup | TBD | Runtime/version/dependencies |
| Targeted test | TBD | Current behavior slice |
| Full suite | TBD | All feature and regression tests |
| Lint / type / build | TBD or justified N/A | Applicable static/build checks |
| Integrity | `python3 scripts/check_test_integrity.py <approved-full-SHA>` | Protected paths |

## Approval and freeze

- Human-approved design version: pending
- Test plan approval evidence: pending
- Test author: pending
- Reviewed red-test evidence and test count: pending
- Approved test commit full SHA (also held by reviewer outside workspace): pending
- Runner/fixture/config paths passed as extra protected paths: pending

Freeze tests, fixtures, snapshots, runner configuration, lockfiles, manifests,
CI, and this plan before implementation. Keep runtime test output in ignored
directories outside `tests/`. Do not omit checks merely to get a green result.
