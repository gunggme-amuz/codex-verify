# codex-verify

Claude Code plugin that automatically verifies code changes and plans using [OpenAI Codex CLI](https://github.com/openai/codex) as an independent reviewer.

## What it does

Whenever Claude Code edits a file or creates an implementation plan, this skill automatically triggers Codex CLI (`codex exec`) to perform an independent review covering:

- **Code Review** - correctness, security, performance, readability
- **Test Verification** - test execution, coverage, missing edge cases
- **Plan Verification** - feasibility, completeness, dependency order, risks
- **Security Check** - OWASP Top 10 vulnerability patterns

Results are tagged as `[PASS]`, `[WARN]`, or `[FAIL]`. If `[FAIL]` issues are found, Claude fixes them and re-verifies in a loop (max 3 rounds).

### Loop exit conditions

| # | Condition | Description |
|---|-----------|-------------|
| 1 | ALL CLEAR | All checks passed |
| 2 | Max iterations | 3 rounds (prevents infinite loops) |
| 3 | No progress | Same issue found 2 rounds in a row |
| 4 | No FAILs | Only WARNs remain (advisory only) |
| 5 | User abort | User says stop |
| 6 | Codex error | CLI error or timeout after 1 retry |

## Prerequisites

- [Codex CLI](https://github.com/openai/codex) installed (`npm i -g @openai/codex` or `brew install --cask codex`)
- OpenAI authentication configured (API key or ChatGPT login)

## Installation

### Via Claude Code CLI

```bash
claude plugin add gh:gunggme-amuz/codex-verify
```

### Manual

Clone and add to your Claude Code settings:

```bash
git clone https://github.com/gunggme-amuz/codex-verify.git ~/.claude/plugins/codex-verify
```

Then add to `~/.claude/settings.json`:

```json
{
  "plugins": [
    "~/.claude/plugins/codex-verify"
  ]
}
```

## License

MIT
