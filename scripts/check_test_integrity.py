#!/usr/bin/env python3
"""Detect changes to reviewer-owned files relative to a trusted test commit."""

import argparse
import re
import subprocess
import sys


PROTECTED_PATHS = (
    "tests", "scripts", ".github", "AGENTS.md", "docs/design.md",
    "docs/test-plan.md", "docs/workflow.md", "package.json",
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock",
    "bun.lockb", "pyproject.toml", "poetry.lock", "uv.lock",
    "pytest.ini", "conftest.py", "setup.cfg", "setup.py", "tox.ini",
    "requirements*.txt", "Makefile", "justfile", "Cargo.toml",
    "Cargo.lock", "go.mod", "go.sum", "vitest.config.*", "jest.config.*",
    "playwright.config.*", "tsconfig*.json", ".nycrc*",
)


def git(*arguments):
    result = subprocess.run(
        ["git", *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode(errors="replace").strip())
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="Human-provided full approved commit SHA")
    parser.add_argument(
        "--protect", action="append", default=[], metavar="PATH",
        help="Additional repository-relative fixture/config path (repeatable)",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", args.baseline):
        parser.error("Use the full reviewer-provided SHA, not HEAD or a branch.")
    if any(path.startswith(("/", ":")) or ".." in path.split("/")
           or not path for path in args.protect):
        parser.error("Extra protected paths must be repository-relative paths.")

    try:
        # Root-relative literal paths; wildcards in the defaults match configs.
        root = git("rev-parse", "--show-toplevel").decode().strip()
        paths = [f":(top,glob){path}" if "*" in path
                 else f":(top,literal){path}"
                 for path in (*PROTECTED_PATHS, *args.protect)]
        commit = git("rev-parse", "--verify", f"{args.baseline}^{{commit}}")
        if commit.decode().strip().lower() != args.baseline.lower():
            raise RuntimeError("Baseline must identify a commit directly.")
        if not git("ls-tree", "-r", "--name-only", args.baseline, "--", "tests").strip():
            raise RuntimeError("Baseline has no tests/ files; freeze reviewed tests first.")

        changed = set()
        # Check both staged and final worktree states, including deletions/renames.
        for options in ((), ("--cached",)):
            changed.update(git(
                "-C", root, "diff", *options, "--name-only", "-z",
                "--no-renames", args.baseline, "--", *paths,
            ).split(b"\0"))
        # Include ignored new files too: ignored tests/config can affect execution.
        changed.update(git(
            "-C", root, "ls-files", "--others", "-z", "--", *paths,
        ).split(b"\0"))
        changed.discard(b"")
        if changed:
            print("FAIL: protected files differ from the approved test baseline:")
            for path in sorted(changed):
                print(f"  {path.decode(errors='replace')}")
            return 1
        print("PASS: protected files match the approved test baseline.")
        return 0
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
