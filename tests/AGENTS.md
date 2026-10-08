# Test ownership

Read the root working agreement. The feature implementer may inspect and run
these files. Changes to tests, fixtures, snapshots, or test configuration need
explicit human approval before the implementer applies them.

The human or an explicitly assigned test author writes tests from the approved
design/test plan before implementation and submits them for human review.
An implementer must explain suspected defects and proposed corrections before
changing tests. Approved corrections belong in a separate commit from the
production fix. Never weaken assertions, add skips, or alter discovery simply
to make broken feature code pass.

These instructions are collaboration guidelines.
