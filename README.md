# AI-assisted interview workspace

Start with [the workflow](docs/workflow.md), then fill in the
[design](docs/design.md) and [test plan](docs/test-plan.md) when the interview
feature is supplied. No application stack or feature has been assumed.

## File map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Coding agent working agreement and human review gates |
| `docs/workflow.md` | Interview steps, role prompts, and enforcement limits |
| `docs/design.md` | Feature design, file map, and human code reading guide |
| `docs/test-plan.md` | Requirement-to-test coverage and verification commands |
| `docs/progress.md` | Review decisions and red/green/commit evidence |
| `tests/AGENTS.md` | Test author and implementer ownership rules |
| `scripts/check_test_integrity.py` | Detect protected file changes from an approved commit |

Application folders should be added only after the stack and design are agreed.
The integrity tool needs Python 3 and Git; it does not run application tests.

## Quick start

1. Give the agent the feature brief and the design-only prompt in the workflow.
2. Review and approve the completed design and test plan.
3. Have a test author create tests, inspect the intended failures, and commit them.
4. Record that commit's full SHA outside the implementer's editable workspace.
5. Start implementation using the implementation prompt and approved SHA.

The uppercase `AGENTS.md` filename follows Codex's repository instruction
convention. See the [official Codex prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide).
