# AI-assisted interview workspace

Start with [the workflow](docs/workflow.md), then fill in the
[design](docs/design.md) and [test plan](docs/test-plan.md) when the interview
feature is supplied. No application stack or feature has been assumed.

## File map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Coding agent working agreement and human review gates |
| `docs/workflow.md` | Interview steps and role prompts |
| `docs/design.md` | Feature design, file map, and human code reading guide |
| `docs/test-plan.md` | Requirement-to-test coverage and verification commands |
| `docs/progress.md` | Review decisions and red/green/commit evidence |
| `tests/AGENTS.md` | Test author and implementer ownership rules |

Application folders should be added only after the stack and design are agreed.
Test ownership is a collaboration guideline, supported by human review and Git
diffs. No test isolation tooling is required for this workflow.

## Quick start

1. Give the agent the feature brief and the design-only prompt in the workflow.
2. Review and approve the completed design and test plan.
3. Have a test author create tests, inspect the intended failures, and commit them.
4. Start implementation using the implementation prompt, testing each slice.
5. Review the final diff, run all checks, and demonstrate the feature.

The uppercase `AGENTS.md` filename follows Codex's repository instruction
convention. See the [official Codex prompting guide](https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide).
