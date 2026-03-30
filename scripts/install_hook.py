#!/usr/bin/env python3
"""Install git pre-commit hook for codex-verify.

Usage:
    python3 install_hook.py --project-dir /path/to/project
"""

import argparse
import stat
import sys
from pathlib import Path

HOOK_SCRIPT = r'''#!/bin/sh
# codex-verify pre-commit hook
# Runs lightweight verification on staged files before commit

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|jsx|tsx|go|rs|java|rb|php|c|cpp|h|swift|kt)$')
if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

FILE_LIST=$(echo "$STAGED_FILES" | tr '\n' ', ' | sed 's/,$//')

echo "[codex-verify] Pre-commit check on: $FILE_LIST"

PROMPT="Review these staged files for critical issues only: $FILE_LIST

Focus ONLY on:
1. Critical bugs that would break production
2. Security vulnerabilities (injection, XSS, hardcoded secrets)
3. Obvious logic errors

Tag each finding as [FAIL] only if it is a production-breaking issue.
If everything looks fine, respond with: ALL CLEAR

Be brief and fast. Skip style, naming, and minor improvements."

RESULT=$(codex exec "$PROMPT" 2>/dev/null)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "[codex-verify] Codex CLI error (exit $EXIT_CODE), skipping check."
    exit 0
fi

if echo "$RESULT" | grep -q "\[FAIL\]"; then
    echo ""
    echo "[codex-verify] Critical issues found:"
    echo "$RESULT"
    echo ""
    echo "Commit blocked. Fix the issues above or use --no-verify to skip."
    exit 1
fi

echo "[codex-verify] Pre-commit check passed."
exit 0
'''


def install_hook(project_dir: str = ".") -> bool:
    git_dir = Path(project_dir) / ".git"
    if not git_dir.is_dir():
        print(f"Error: {git_dir} is not a git repository", file=sys.stderr)
        return False

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    if hook_path.exists():
        backup = hook_path.with_suffix(".bak")
        hook_path.rename(backup)
        print(f"Backed up existing hook to {backup}")

    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
    print(f"Installed codex-verify pre-commit hook at {hook_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Install codex-verify git pre-commit hook")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    success = install_hook(args.project_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
