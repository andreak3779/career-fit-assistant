#!/usr/bin/env python3
"""Query data/pluralsight_learning_history.json without loading the whole file into context.

The raw JSON is ~44K tokens (298 entries, each carrying a `summary` and a
`url` field that dwarf the few fields most lookups actually need). Several
skills only need duration/timing_profile for one or a handful of named
courses, a lean full listing, or the subset of entries still missing a
`summary` — none of which require reading the whole file into an LLM's
context. This script answers those three questions directly so skills can
shell out to it instead of instructing "Load data/pluralsight_learning_history.json".

Usage:
    python scripts/query_learning_history.py lookup "Course Title" ["Another Title" ...]
    python scripts/query_learning_history.py list
    python scripts/query_learning_history.py missing-summary

Each subcommand accepts an optional --root to point at a different repo root
(used by tests — never point this at anything but a fixture copy of the JSON).

Exit code 0 on success, 1 if the JSON file is missing or unreadable, or if
every name passed to `lookup` was not found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

# Fields relevant to duration/timing lookups and full listings — excludes the
# two fields (summary, url) that account for most of the file's size.
LEAN_FIELDS = ("name", "type", "duration", "timing_profile", "completed_date")


def _json_path(root: Path) -> Path:
    return root / "project-2-profile-learning-hub" / "data" / "pluralsight_learning_history.json"


def _normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().lower()


def _load(root: Path) -> list[dict[str, Any]]:
    path = _json_path(root)
    return json.loads(path.read_text(encoding="utf-8"))


def _lean(entry: dict[str, Any]) -> dict[str, Any]:
    return {k: entry.get(k) for k in LEAN_FIELDS}


def _print_entry(entry: dict[str, Any]) -> None:
    duration = entry.get("duration") or "—"
    print(
        f"{entry['name']} | {entry.get('type', '?')} | duration={duration} | "
        f"timing_profile={entry.get('timing_profile', '?')} | "
        f"completed={entry.get('completed_date', '?')}"
    )


def cmd_lookup(root: Path, names: list[str]) -> int:
    entries = _load(root)
    by_normalized = {_normalize_name(e["name"]): e for e in entries}

    found_any = False
    for name in names:
        key = _normalize_name(name)
        entry = by_normalized.get(key)
        if entry is not None:
            _print_entry(entry)
            found_any = True
            continue

        substring_matches = [e for e in entries if key in _normalize_name(e["name"])]
        if len(substring_matches) == 1:
            _print_entry(substring_matches[0])
            found_any = True
        elif len(substring_matches) > 1:
            print(f'"{name}" — {len(substring_matches)} possible matches, be more specific:')
            for e in substring_matches:
                print(f"  - {e['name']}")
        else:
            print(
                f'"{name}" — NOT FOUND in data/pluralsight_learning_history.json; use web_search.'
            )

    return 0 if found_any else 1


def cmd_list(root: Path) -> int:
    entries = _load(root)
    print(f"{len(entries)} entries (name | type | duration | timing_profile | completed_date):")
    for entry in entries:
        _print_entry(entry)
    return 0


def cmd_missing_summary(root: Path) -> int:
    entries = _load(root)
    missing = [e for e in entries if not e.get("summary")]
    print(f"{len(missing)} of {len(entries)} entries missing a summary:")
    for entry in missing:
        print(f"{entry['name']} | {entry.get('type', '?')} | {entry.get('url', '?')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="query_learning_history.py",
        description="Query data/pluralsight_learning_history.json without loading the whole file.",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="repo root (default: this repo)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_p = subparsers.add_parser(
        "lookup", help="duration/timing_profile for one or more course names"
    )
    lookup_p.add_argument("names", nargs="+", help="course/lab title(s) to look up")

    subparsers.add_parser("list", help="lean listing of every entry (no summary/url)")
    subparsers.add_parser("missing-summary", help="entries with no summary field yet")

    args = parser.parse_args(argv)

    try:
        if args.command == "lookup":
            return cmd_lookup(args.root, args.names)
        if args.command == "list":
            return cmd_list(args.root)
        if args.command == "missing-summary":
            return cmd_missing_summary(args.root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {_json_path(args.root)}: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
