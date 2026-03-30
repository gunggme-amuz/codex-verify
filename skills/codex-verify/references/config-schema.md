# .codex-verify.yml Configuration Schema

Place this file at the root of your project to customize verification behavior.

## Full Example

```yaml
# .codex-verify.yml
max_rounds: 3                   # Max verification loop iterations (1-10)
language: ko                    # Prompt language: ko | en
verify_types:                   # Which checks to run
  - code-review
  - security-check
ignore_patterns:                # Glob patterns for files to skip
  - "*.test.js"
  - "*.spec.ts"
  - "migrations/**"
  - "vendor/**"
severity_threshold: FAIL        # FAIL = loop only on FAIL; WARN = also loop on WARN
custom_rules:                   # Project-specific review criteria injected into Codex prompt
  - "All API endpoints must have rate limiting"
  - "Database queries must use parameterized statements"
  - "No console.log in production code"
report_format: html             # md | html
auto_verify: true               # Auto-trigger after file edits
timeout: 300                    # Codex exec timeout in seconds
```

## Field Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rounds` | int | 3 | Maximum verification loop iterations (1-10) |
| `language` | string | "ko" | Prompt language: "ko" (Korean) or "en" (English) |
| `verify_types` | list | ["code-review"] | Checks to run: code-review, test-verify, plan-verify, security-check |
| `ignore_patterns` | list | [] | Glob patterns for files excluded from verification |
| `severity_threshold` | string | "FAIL" | "FAIL" = only re-loop on FAIL; "WARN" = also re-loop on WARN |
| `custom_rules` | list | [] | Project-specific criteria appended to Codex review prompt |
| `report_format` | string | "md" | Report output format: "md" or "html" |
| `auto_verify` | bool | true | Whether to auto-trigger verification after edits |
| `timeout` | int | 300 | Codex CLI execution timeout in seconds |

## Notes

- If `.codex-verify.yml` does not exist, all defaults are used
- If PyYAML is not installed, only flat key-value pairs are parsed (lists won't work)
- `custom_rules` is the most impactful field — it lets you enforce project-specific standards
