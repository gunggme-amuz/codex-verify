# codex-verify v2

Cross-model code verification plugin for [Claude Code](https://claude.ai/code) using [OpenAI Codex CLI](https://github.com/openai/codex).

> Research shows multi-model verification catches ~50% more bugs than single-model review. This plugin makes Claude and Codex work together as reviewer and counter-reviewer.

## What's different (v2)

| Feature | v1 | v2 |
|---------|----|----|
| Result format | Raw text | Structured JSON with `parse_result.py` |
| Round tracking | Manual | Auto delta analysis (resolved/new issues) |
| Reports | None | HTML & Markdown with history |
| Project config | None | `.codex-verify.yml` with custom rules |
| Git integration | None | Pre-commit hook |
| Prompts | Korean only | Korean + English |

## How it works

```
Code Change → Codex CLI Review → JSON Parse → Delta Track → Fix Loop → Report
```

1. Claude edits code or writes a plan
2. Codex CLI independently reviews the changes
3. Results are parsed into structured JSON (`[PASS]`, `[WARN]`, `[FAIL]`)
4. Delta is computed against previous round (what got fixed, what's new)
5. If `[FAIL]` found: Claude fixes → Codex re-reviews (max 3 rounds)
6. Final report generated (HTML or Markdown)

## Prerequisites

- [Codex CLI](https://github.com/openai/codex) (`npm i -g @openai/codex` or `brew install --cask codex`)
- OpenAI authentication (API key or ChatGPT login)
- Python 3.8+

## Installation

```bash
claude plugin add gh:gunggme-amuz/codex-verify
```

Or manually:

```bash
git clone https://github.com/gunggme-amuz/codex-verify.git ~/.claude/plugins/codex-verify
```

## Project Configuration

Create `.codex-verify.yml` in your project root:

```yaml
max_rounds: 3
language: en                    # ko | en
verify_types:
  - code-review
  - security-check
ignore_patterns:
  - "*.test.js"
  - "migrations/**"
severity_threshold: FAIL        # FAIL | WARN
custom_rules:                   # project-specific review criteria
  - "All API endpoints must have rate limiting"
  - "Database queries must use parameterized statements"
report_format: html             # md | html
timeout: 300
```

All fields are optional. See [config-schema.md](skills/codex-verify/references/config-schema.md) for full reference.

## Git Pre-commit Hook

Block commits with critical issues:

```bash
python3 scripts/install_hook.py --project-dir .
```

The hook runs a lightweight Codex check on staged files. Only `[FAIL]`-level issues block the commit.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/parse_result.py` | Parse Codex output → structured JSON |
| `scripts/generate_report.py` | History tracking + HTML/MD reports |
| `scripts/load_config.py` | Load `.codex-verify.yml` with defaults |
| `scripts/install_hook.py` | Install git pre-commit hook |

## Plugin Structure

```
codex-verify/
├── manifest.json
├── .claude-plugin/plugin.json
├── skills/codex-verify/
│   ├── SKILL.md                     # Skill definition
│   └── references/config-schema.md  # Config documentation
└── scripts/
    ├── parse_result.py
    ├── generate_report.py
    ├── load_config.py
    └── install_hook.py
```

## License

MIT
