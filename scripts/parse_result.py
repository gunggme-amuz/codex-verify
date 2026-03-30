#!/usr/bin/env python3
"""Parse Codex CLI verification output into structured JSON.

Usage:
    codex exec "..." 2>/dev/null | python3 parse_result.py --round 1 --type code-review
    python3 parse_result.py --raw-file /tmp/codex_out.txt --round 1 --type code-review
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone


KNOWN_CATEGORIES = {
    "정확성", "보안", "성능", "엣지 케이스", "코드 품질",
    "accuracy", "correctness", "security", "performance",
    "edge cases", "code quality", "maintainability",
}


def parse_codex_output(raw: str, round_num: int = 1, verify_type: str = "code-review") -> dict:
    """Parse raw Codex output text into structured JSON result."""
    items = []
    parse_warnings = []

    # Match [TAG] followed by text until next [TAG] or end of string
    pattern = r"\[(PASS|WARN|FAIL)\]\s*(.+?)(?=\[(?:PASS|WARN|FAIL)\]|\Z)"
    matches = list(re.finditer(pattern, raw, re.DOTALL))

    if not matches and raw.strip():
        parse_warnings.append("No [PASS]/[WARN]/[FAIL] tags found in non-empty output")

    for match in matches:
        tag = match.group(1)
        text = match.group(2).strip()
        category, detail = _split_category(text)
        # Extract file references if present
        files = re.findall(r"[\w/.-]+\.\w{1,10}(?:#L\d+)?", text)

        items.append({
            "tag": tag,
            "category": category,
            "detail": detail,
            "files": files[:5],
        })

    all_clear = bool(re.search(r"ALL\s*CLEAR", raw, re.IGNORECASE))
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for item in items:
        counts[item["tag"]] += 1

    if all_clear or counts["FAIL"] == 0:
        verdict = "PASS" if counts["WARN"] == 0 else "WARN"
    else:
        verdict = "FAIL"

    return {
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "round": round_num,
        "verify_type": verify_type,
        "verdict": verdict,
        "all_clear": all_clear,
        "counts": counts,
        "total_items": len(items),
        "items": items,
        "parse_warnings": parse_warnings,
        "raw_length": len(raw),
    }


def _split_category(text: str) -> tuple:
    """Split 'Category: detail' or '카테고리: detail' from text."""
    m = re.match(r"^([가-힣A-Za-z\s]{2,25})[:：]\s*(.+)", text, re.DOTALL)
    if m:
        cat = m.group(1).strip().lower()
        # Normalize to known category if close match
        for known in KNOWN_CATEGORIES:
            if known.lower() in cat or cat in known.lower():
                return known, m.group(2).strip()
        return m.group(1).strip(), m.group(2).strip()
    return "general", text


def main():
    parser = argparse.ArgumentParser(description="Parse Codex verification output to JSON")
    parser.add_argument("--raw-file", help="Path to raw Codex output file (default: stdin)")
    parser.add_argument("--round", type=int, default=1, help="Verification round number")
    parser.add_argument("--type", default="code-review",
                        choices=["code-review", "test-verify", "plan-verify", "security-check"],
                        help="Verification type")
    args = parser.parse_args()

    if args.raw_file:
        with open(args.raw_file, encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    result = parse_codex_output(raw, round_num=args.round, verify_type=args.type)
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
