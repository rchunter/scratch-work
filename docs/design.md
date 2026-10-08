# Feature design

Status: DRAFT — feature brief not yet supplied; implementation not approved.

## Problem and scope

- User and task: TBD
- Desired observable behavior: TBD
- In scope / out of scope: TBD
- Constraints (time, stack, compatibility, dependencies): TBD
- Open questions and assumptions requiring human agreement: TBD

## Acceptance criteria

Assign stable IDs so design, tests, and implementation can be traced.

| ID | Given / when | Expected observable result |
| --- | --- | --- |
| AC-01 | TBD | TBD |

## Proposed approach

Describe the entry point, data flow, domain rules, inputs/outputs, error behavior,
state ownership, and external boundaries. Include security/privacy, concurrency,
and performance only where relevant. State alternatives and why this approach
fits the time and scope. Define the public contract before tests are written.

## Project structure and files

Replace this table with concrete paths before approval. Use only layers the
feature needs; a small feature may fit in one module.

| Proposed path | Responsibility | Public interface / dependencies | Why separate |
| --- | --- | --- | --- |
| TBD entry point | Parse input and invoke feature | TBD | TBD |
| TBD domain module | Feature rules | TBD | TBD |
| TBD IO adapter, if needed | External IO | TBD | TBD |
| TBD test paths | Observable behavior verification | TBD | TBD |

## Human reading guide

Provide exact paths and relevant symbols, then walk one real input through them:

1. Start at the public entry point: TBD.
2. Follow the main domain operation and its invariants: TBD.
3. Inspect external dependencies and error handling: TBD.
4. Read the acceptance tests that demonstrate this flow: TBD.
5. Explain how to safely add a related behavior: TBD.

## Implementation slices and validation

List small behavior slices with their AC IDs and corresponding test cases.
Link [the test plan](test-plan.md). Define exact test/lint/type/build commands
once the stack is known. Identify risks, rollback approach, and deferred work.

## Human review

- Document version/commit reviewed: pending
- Reviewer and explicit approval evidence: pending
- Feedback and how each item was resolved: pending
- Approved scope and unresolved limitations: pending

Only the human supplies approval. A changed contract needs renewed review.
