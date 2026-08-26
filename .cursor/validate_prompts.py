#!/usr/bin/env python3
"""Validate the prompt datasets shipped by this repository.

The repository ships its prompts as JSON arrays (`prompts-zh.json` and
`prompts-zh-TW.json`) that downstream tools consume. This script is the
"build/test" step for that data: it fails loudly on malformed JSON, missing
fields, empty values, or duplicate entries so broken data never lands.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASETS = ["prompts-zh.json", "prompts-zh-TW.json"]
REQUIRED_FIELDS = ("act", "prompt")


def validate_dataset(path: Path) -> tuple[int, list[str]]:
    """Return (entry_count, errors) for a single dataset file."""
    errors: list[str] = []

    if not path.exists():
        return 0, [f"{path.name}: file not found"]

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return 0, [f"{path.name}: invalid JSON ({exc})"]

    if not isinstance(data, list):
        return 0, [f"{path.name}: top-level value must be a list, got {type(data).__name__}"]

    seen_acts: set[str] = set()
    for index, entry in enumerate(data):
        where = f"{path.name}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{where}: entry must be an object, got {type(entry).__name__}")
            continue
        for field in REQUIRED_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{where}: field '{field}' must be a non-empty string")
        act = entry.get("act")
        if isinstance(act, str) and act.strip():
            key = act.strip()
            if key in seen_acts:
                errors.append(f"{where}: duplicate act '{key}'")
            seen_acts.add(key)

    return len(data), errors


def main() -> int:
    all_errors: list[str] = []
    counts: dict[str, int] = {}

    for name in DATASETS:
        count, errors = validate_dataset(REPO_ROOT / name)
        counts[name] = count
        all_errors.extend(errors)
        status = "OK" if not errors else f"{len(errors)} error(s)"
        print(f"{name}: {count} prompts -> {status}")

    distinct_counts = {c for c in counts.values() if c}
    if len(distinct_counts) > 1:
        print(f"WARNING: datasets have different prompt counts: {counts}")

    if all_errors:
        print("\nValidation failed:")
        for error in all_errors:
            print(f"  - {error}")
        return 1

    print("\nAll prompt datasets are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
