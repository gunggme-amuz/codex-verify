#!/usr/bin/env python3
"""Generate verification reports with round-over-round delta analysis.

Usage:
    python3 generate_report.py --add-result parsed.json --project-dir .
    python3 generate_report.py --report --format md --project-dir .
    python3 generate_report.py --report --format html --project-dir .
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HISTORY_FILE = ".codex-verify-history.json"


def load_history(project_dir: Path) -> list:
    path = project_dir / HISTORY_FILE
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_history(history: list, project_dir: Path):
    path = project_dir / HISTORY_FILE
    path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def add_result(result_path: str, project_dir: Path) -> dict:
    """Append a parsed result to history, return the result with delta info."""
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    history = load_history(project_dir)

    # Compute delta from previous round
    if history:
        prev = history[-1]
        result["delta"] = {
            "PASS": result["counts"]["PASS"] - prev["counts"]["PASS"],
            "WARN": result["counts"]["WARN"] - prev["counts"]["WARN"],
            "FAIL": result["counts"]["FAIL"] - prev["counts"]["FAIL"],
            "prev_verdict": prev["verdict"],
        }
        # Identify resolved and new issues
        prev_details = {i["detail"][:80] for i in prev.get("items", [])}
        curr_details = {i["detail"][:80] for i in result.get("items", [])}
        result["delta"]["resolved"] = len(prev_details - curr_details)
        result["delta"]["new_issues"] = len(curr_details - prev_details)
    else:
        result["delta"] = None

    history.append(result)
    save_history(history, project_dir)
    return result


def generate_markdown(project_dir: Path) -> str:
    """Generate markdown report from verification history."""
    history = load_history(project_dir)
    if not history:
        return "No verification history found."

    lines = [
        "# Codex Verify Report",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Summary",
        "",
        "| Round | Type | Verdict | PASS | WARN | FAIL | Delta |",
        "|-------|------|---------|------|------|------|-------|",
    ]

    for r in history:
        delta_str = ""
        if r.get("delta"):
            d = r["delta"]
            parts = []
            if d["FAIL"] < 0:
                parts.append(f"FAIL {d['FAIL']}")
            if d["FAIL"] > 0:
                parts.append(f"FAIL +{d['FAIL']}")
            if d.get("resolved"):
                parts.append(f"{d['resolved']} resolved")
            if d.get("new_issues"):
                parts.append(f"{d['new_issues']} new")
            delta_str = ", ".join(parts) if parts else "no change"
        else:
            delta_str = "baseline"

        verdict_icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "**FAIL**"}
        lines.append(
            f"| {r['round']} | {r['verify_type']} | {verdict_icon.get(r['verdict'], r['verdict'])} "
            f"| {r['counts']['PASS']} | {r['counts']['WARN']} | {r['counts']['FAIL']} | {delta_str} |"
        )

    # Latest round details
    latest = history[-1]
    lines.extend([
        "",
        "## Latest Round Details",
        "",
    ])
    for item in latest.get("items", []):
        icon = {"PASS": "[PASS]", "WARN": "[WARN]", "FAIL": "[FAIL]"}
        lines.append(f"- {icon.get(item['tag'], item['tag'])} **{item['category']}**: {item['detail'][:200]}")
        if item.get("files"):
            lines.append(f"  - Files: {', '.join(item['files'][:3])}")

    if latest.get("delta") and latest["delta"].get("resolved"):
        lines.extend(["", f"Resolved from previous round: {latest['delta']['resolved']} issue(s)"])

    lines.append("")
    return "\n".join(lines)


def generate_html(project_dir: Path, output_path: Path) -> None:
    """Generate self-contained HTML report."""
    history = load_history(project_dir)
    if not history:
        output_path.write_text("<html><body><p>No verification history.</p></body></html>")
        return

    latest = history[-1]
    verdict_color = {"PASS": "#22c55e", "WARN": "#f59e0b", "FAIL": "#ef4444"}

    rows_html = ""
    for r in history:
        delta_str = "baseline"
        if r.get("delta"):
            d = r["delta"]
            parts = []
            if d["FAIL"] < 0:
                parts.append(f'<span style="color:#22c55e">FAIL {d["FAIL"]}</span>')
            if d["FAIL"] > 0:
                parts.append(f'<span style="color:#ef4444">FAIL +{d["FAIL"]}</span>')
            if d.get("resolved"):
                parts.append(f'{d["resolved"]} resolved')
            if d.get("new_issues"):
                parts.append(f'{d["new_issues"]} new')
            delta_str = ", ".join(parts) if parts else "no change"

        vc = verdict_color.get(r["verdict"], "#888")
        rows_html += f"""<tr>
            <td>{r['round']}</td><td>{r['verify_type']}</td>
            <td style="color:{vc};font-weight:bold">{r['verdict']}</td>
            <td>{r['counts']['PASS']}</td><td>{r['counts']['WARN']}</td><td>{r['counts']['FAIL']}</td>
            <td>{delta_str}</td>
        </tr>\n"""

    items_html = ""
    for item in latest.get("items", []):
        tc = verdict_color.get(item["tag"], "#888")
        files = ", ".join(item.get("files", [])[:3])
        files_line = f'<div style="color:#666;font-size:0.85em">Files: {files}</div>' if files else ""
        items_html += f"""<div style="border-left:3px solid {tc};padding:8px 12px;margin:6px 0;background:#fafafa;border-radius:4px">
            <strong style="color:{tc}">[{item['tag']}]</strong> <strong>{item['category']}</strong>
            <div style="margin-top:4px">{item['detail'][:300]}</div>{files_line}
        </div>\n"""

    vc = verdict_color.get(latest["verdict"], "#888")
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Codex Verify Report</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:24px;background:#fff;color:#1a1a1a}}
  h1{{font-size:1.5em;margin-bottom:4px}} h2{{font-size:1.15em;margin:20px 0 10px;color:#333}}
  .meta{{color:#666;font-size:0.9em;margin-bottom:20px}}
  .verdict-card{{display:inline-block;padding:10px 24px;border-radius:8px;font-size:1.3em;font-weight:bold;color:#fff;background:{vc};margin-bottom:20px}}
  table{{width:100%;border-collapse:collapse;margin:10px 0}} th,td{{padding:8px 12px;text-align:left;border-bottom:1px solid #e5e7eb}}
  th{{background:#f9fafb;font-weight:600;font-size:0.9em;color:#555}}
  .footer{{margin-top:30px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:0.85em;color:#888}}
</style></head><body>
<h1>Codex Verify Report</h1>
<div class="meta">Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} | Rounds: {len(history)}</div>
<div class="verdict-card">{latest['verdict']}</div>

<h2>Round History</h2>
<table><tr><th>Round</th><th>Type</th><th>Verdict</th><th>PASS</th><th>WARN</th><th>FAIL</th><th>Delta</th></tr>
{rows_html}</table>

<h2>Latest Round ({latest['round']}) Details</h2>
{items_html}

<div class="footer">codex-verify v2.0.0 — Cross-model verification powered by OpenAI Codex CLI</div>
</body></html>"""

    output_path.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate codex-verify reports")
    parser.add_argument("--add-result", help="Path to parsed result JSON to append to history")
    parser.add_argument("--report", action="store_true", help="Generate report from history")
    parser.add_argument("--format", choices=["md", "html"], default="md", help="Report format")
    parser.add_argument("--output", help="Output path for HTML report (default: .codex-verify-report.html)")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    project_dir = Path(args.project_dir)

    if args.add_result:
        result = add_result(args.add_result, project_dir)
        json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
        print()

    if args.report:
        if args.format == "md":
            print(generate_markdown(project_dir))
        else:
            output = Path(args.output) if args.output else project_dir / ".codex-verify-report.html"
            generate_html(project_dir, output)
            print(f"HTML report generated: {output}")

    if not args.add_result and not args.report:
        parser.print_help()


if __name__ == "__main__":
    main()
