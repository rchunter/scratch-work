# Repository and workflow red-team review

Reviewed: 2026-10-08, repository setup commit `3f9639c`.

Verdict: useful collaboration scaffolding, but it does not yet meet the goal
that an implementation agent cannot manipulate tests. The documented isolation
limits are candid. The local checker also has false passes beyond those limits.
No feature, application runner, independent CI, or enforced sandbox exists yet.

## Findings, in priority order

### 1. P1: No implemented boundary prevents test manipulation

Location: `docs/workflow.md:87–102`.

The workflow describes a read-only environment and independent verification,
but neither exists. An implementer with the current workspace write permissions
can edit tests, the checker, the evidence log, and runner configuration. Role
prompts and separate chats do not make that impossible. This is explicitly
disclosed in the docs, but remains an unmet part of the original objective.

Fix: before claiming prevention, configure a separate write-limited implementation
environment and reviewer-owned execution. Until then describe this as a
cooperative workflow with change detection. Have the reviewer own the baseline,
protected-path manifest, runtime, execution command, and authoritative results.

### 2. P1: Git index flags hide changed test bytes

Location: `scripts/check_test_integrity.py:60–64`.

Reproduced in a disposable repository with an unchanged checker and the original
approved SHA:

```sh
git update-index --assume-unchanged tests/test_feature.py
# Change the tracked test from `assert False` to `assert True`.
python3 /trusted/path/check_test_integrity.py <original-approved-SHA>
# Returns 0: PASS.
```

Both staged and worktree diffs can report no changes while the file on disk is
different. Running a trusted copy of this checker against the manipulated
workspace does not resolve this bypass. A clean independent checkout avoids
that particular index state, provided only committed candidate code is tested.

Fix: compare protected filesystem bytes/types/modes directly with trusted Git
objects or a reviewer-owned manifest, independent of index hints. Use a clean
reviewer-owned checkout and disable replacement objects/untrusted Git config
when extracting the baseline. Keep adversarial regression tests for the guard.

### 3. P1: Protected symlinks do not protect their targets

Location: `scripts/check_test_integrity.py:49–51` and `PROTECTED_PATHS`.

Reproduced: approve `tests/input.txt -> ../fixtures/input.txt`, then change the
tracked `fixtures/input.txt`. The checker returns PASS because the symlink itself
has not changed and its target is not automatically protected. Tests reading
that fixture observe different bytes. Read-only mounting just the symlink also
does not protect a writable target.

Fix: reject symlinks in protected inputs, or explicitly validate and freeze all
resolved targets within a controlled tree. Reject external targets and submodule
inputs unless independently pinned and verified. Treat fixtures as test inputs,
even when they live outside tests/.

### 4. P2: The default denylist misses execution control outside root paths

Location: `scripts/check_test_integrity.py:10–19`.

Reproduced: adding `src/conftest.py` or `.env` returns PASS. Root `conftest.py`
correctly fails as a control. A nested conftest can affect tests collected below
its directory when a future stack uses colocated tests; environment files can
affect runners that load them. These files do not affect every possible stack,
but the generic guard cannot establish that execution is unchanged.

The same inventory issue applies to other stacks, nested manifests, plugins,
installed dependencies, and executable/import lookup paths. Optional `--protect`
arguments leave correctness dependent on an easily missed inventory step.

Fix: prefer a reviewer-approved writable-path allowlist and protected execution
manifest tailored to the actual stack. Fix runtime/dependencies and invocation
in independent execution. Prevent omitted extra paths from silently narrowing
the protection policy.

### 5. P2: A baseline with no executable tests passes

Location: `scripts/check_test_integrity.py:55–56`.

Reproduced: a baseline containing only `tests/AGENTS.md` returns PASS. The
existing setup commit meets this condition despite having no application tests.
The check establishes directory contents, not that tests exist or ran.

Fix: label this strictly as file integrity. Have independent execution require
a nonzero expected test inventory, report collected/passed/failed/skipped cases,
and reject missing or unexpected skipped tests. Record per-case identities
against the approved acceptance criteria. Integrity success alone must never
authorize implementation or acceptance.

### 6. P2: The TDD milestone rules conflict with a fully frozen red suite

Location: `AGENTS.md:46–52`, `docs/workflow.md:25–28,47–65`.

All feature tests are written and frozen before implementation. The implementer
must then commit passing behavior slices and run the full suite before green
milestones. Early slices necessarily leave other approved feature tests failing.
There is no definition of allowed pending failures, so an agent may stall,
implement the whole feature in one large change, or skip remaining tests to
claim green.

Fix: choose an explicit policy. For the interview, freeze the full suite and
define slice-green as that slice plus existing regressions passing. Still run
the full suite; log expected remaining red cases by ID, and permit no new
failures. Require all approved cases and applicable static/build checks to pass
at final acceptance. Never turn pending cases into skips. Alternatively have
the independent test author release reviewed tests one slice at a time.

### 7. P2: The frozen design cannot stay current as instructed

Location: `AGENTS.md:42`, `scripts/check_test_integrity.py:11–12`.

The implementer is told to keep the design's file map accurate, but the design
is protected by the integrity baseline. Updating a path or reading guide causes
integrity failure. A test-author correction workflow exists, but the comparable
documentation correction process is undefined.

Fix: freeze the approved behavioral contract; keep an editable implementation
reading guide separately. Route genuine contract changes to human review and
new reviewed tests. If a baseline must change, explicitly review the diff from
the previous baseline and never silently legitimize intervening test edits.

## Additional workflow risks

- Evidence in docs/progress.md is agent-authored. It is useful narration, not
  proof. Save reviewer-owned runner output tied to the tested commit/artifact;
  ensure acceptance runs test the exact committed result with a clean tree.
- Immutable tests do not prevent production code from terminating the runner,
  monkeypatching assertions, or behaving differently under test. Independent
  invocation, expected case counts, code review, and hidden cases address
  different parts of this risk; hidden cases alone cannot guarantee correctness.
- The original ten verification cases were ephemeral. Their results are recorded,
  but they cannot be rerun from the repo. Preserve an executable regression suite
  for this security-relevant checker, including the false-pass cases above.
- Rejecting every red result except assertion failures is too strict across
  stacks. Specify accepted missing-behavior failures per case; exclude syntax,
  dependency, discovery, and environment failures without forcing artificial
  stubs solely to change failure type.
- Timebox the initial design/review and choose the smallest meaningful feature.
  Define a time-pressure fallback that reduces scope with human agreement while
  retaining final verification; repeated freezes and role handoffs can consume
  an interview before a working feature is demonstrated.

## Verification scope

Read all tracked workspace documents, the guard, and repository status. Ran six
checks in a disposable Git repository: instruction-only baseline passed;
assume-unchanged modification passed; symlink-target modification passed;
root configuration change failed as expected; nested configuration addition
passed; environment file addition passed. These are integrity reproductions,
not claims that an unspecified application runner loaded those configuration
files. No feature code or application tests exist to assess.

No safeguards were changed in this review. Recommended order: resolve milestone
semantics, choose the actual stack and execution inventory, fix guard false
passes with reproducible tests, then provision independent verification and
write restrictions before making a prevention claim.
