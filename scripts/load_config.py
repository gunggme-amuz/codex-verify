#!/usr/bin/env python3
"""Load .codex-verify.yml project configuration.

Usage:
    python3 load_config.py --project-dir /path/to/project
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULTS = {
    "max_rounds": 3,
    "language": "ko",
    "verify_types": ["code-review"],
    "ignore_patterns": [],
    "severity_threshold": "FAIL",
    "custom_rules": [],
    "report_format": "md",
    "auto_verify": True,
    "timeout": 300,
}

VALID_LANGUAGES = {"ko", "en"}
VALID_THRESHOLDS = {"WARN", "FAIL"}
VALID_TYPES = {"code-review", "test-verify", "plan-verify", "security-check"}
VALID_FORMATS = {"md", "html"}


def load_config(project_dir: str = ".") -> dict:
    """Load config from .codex-verify.yml, merge with defaults."""
    config_path = Path(project_dir) / ".codex-verify.yml"
    if not config_path.exists():
        return DEFAULTS.copy()

    try:
        import yaml
        with open(config_path, encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: simple key-value parser for flat YAML
        user_config = _parse_simple_yaml(config_path)
    except Exception as e:
        print(f"Warning: failed to parse {config_path}: {e}", file=sys.stderr)
        return DEFAULTS.copy()

    merged = {**DEFAULTS, **user_config}
    errors = _validate(merged)
    if errors:
        for err in errors:
            print(f"Config warning: {err}", file=sys.stderr)

    return merged


def _parse_simple_yaml(path: Path) -> dict:
    """Minimal YAML parser for flat key-value pairs (no nested structures)."""
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value.lower() in ("true", "false"):
                    result[key] = value.lower() == "true"
                elif value.isdigit():
                    result[key] = int(value)
                elif value:
                    result[key] = value
    return result


def _validate(config: dict) -> list:
    """Validate config values, return list of error messages."""
    errors = []
    if not isinstance(config.get("max_rounds"), int) or not 1 <= config["max_rounds"] <= 10:
        errors.append("max_rounds must be 1-10, using default 3")
        config["max_rounds"] = DEFAULTS["max_rounds"]
    if config.get("language") not in VALID_LANGUAGES:
        errors.append(f"language must be one of {VALID_LANGUAGES}, using default")
        config["language"] = DEFAULTS["language"]
    if config.get("severity_threshold") not in VALID_THRESHOLDS:
        errors.append(f"severity_threshold must be one of {VALID_THRESHOLDS}")
        config["severity_threshold"] = DEFAULTS["severity_threshold"]
    if config.get("report_format") not in VALID_FORMATS:
        config["report_format"] = DEFAULTS["report_format"]
    if isinstance(config.get("verify_types"), list):
        invalid = [t for t in config["verify_types"] if t not in VALID_TYPES]
        if invalid:
            errors.append(f"Invalid verify_types: {invalid}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Load codex-verify configuration")
    parser.add_argument("--project-dir", default=".", help="Project root directory")
    args = parser.parse_args()

    config = load_config(args.project_dir)
    json.dump(config, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
