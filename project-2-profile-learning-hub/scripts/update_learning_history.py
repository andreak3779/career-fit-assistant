#!/usr/bin/env python3
"""Merge a small batch of course/lab summaries into data/pluralsight_learning_history.json
without loading the whole ~44K-token file into an LLM's context.

The pluralsight-summary-enricher skill generates a `summary` field for a batch of
~25 entries at a time (see its SKILL.md). Previously it had to re-emit the ENTIRE
298-entry JSON file via the Write tool after every batch to checkpoint progress —
this script does that merge server-side instead: the caller only ever needs to hold
the batch's own {name: summary} pairs, not the untouched majority of the file.

Writes IN PLACE to data/pluralsight_learning_history.json (unlike
parse_pluralsight_html.py's stage-to-outputs/-then-promote convention). This is
deliberate: query_learning_history.py's `missing-summary` resume check reads
data/pluralsight_learning_history.json directly, so a backfill's checkpoint must
land there too, or an interrupted run can't resume correctly. Use --dry-run for
the "review before it lands" step instead.

Usage:
    python scripts/update_learning_history.py apply --summaries-file batch.json
    python scripts/update_learning_history.py apply --summaries-file batch.json --dry-run

batch.json is a flat JSON object: {"Course or Lab Name": "Summary text.", ...}

Matching is exact-normalized-name only (collapse whitespace, lowercase, strip) —
no fuzzy/substring fallback like query_learning_history.py's read-side `lookup`
uses, since a wrong fuzzy match here would silently attach a summary to the wrong
entry. Apply is partial: every name that matches is written; names that don't are
reported as NOT FOUND without blocking the rest of the batch.

Exit code 0 if at least one summary was applied (or would be, in --dry-run), 1 if
the summaries file or the JSON file is missing/invalid, or if zero names matched.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def _json_path(root: Path) -> Path:
    return root / "project-2-profile-learning-hub" / "data" / "pluralsight_learning_history.json"


def _backup_path(root: Path) -> Path:
    return (
        root
        / "project-2-profile-learning-hub"
        / "outputs"
        / "pluralsight_learning_history.json.bak"
    )


def normalize_name(name: str) -> str:
    """Collapse all internal whitespace for matching — must stay logically
    identical to parse_pluralsight_html.py's normalize_name."""
    return re.sub(r"\s+", " ", name).lower().strip()


def _load_entries(root: Path) -> list[dict[str, Any]]:
    path = _json_path(root)
    return json.loads(path.read_text(encoding="utf-8"))


def _load_summaries(summaries_file: Path) -> dict[str, str]:
    raw = json.loads(summaries_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in raw.items()
    ):
        raise ValueError("expected a flat {name: summary} object")
    return raw


def _truncate(text: str, limit: int = 80) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def cmd_apply(root: Path, summaries_file: Path, dry_run: bool) -> int:
    try:
        summaries = _load_summaries(summaries_file)
    except FileNotFoundError:
        print(f"ERROR: summaries file not found: {summaries_file}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: invalid summaries file {summaries_file}: {exc}", file=sys.stderr)
        return 1

    try:
        entries = _load_entries(root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {_json_path(root)}: {exc}", file=sys.stderr)
        return 1

    by_normalized: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        by_normalized.setdefault(normalize_name(entry["name"]), []).append(entry)

    # Collapse raw keys that normalize to the same key (different whitespace) —
    # last value wins, warn rather than error since JSON itself forbids literal
    # duplicate keys.
    deduped: dict[str, tuple[str, str]] = {}
    for raw_name, summary in summaries.items():
        key = normalize_name(raw_name)
        if key in deduped and deduped[key][0] != raw_name:
            print(
                f'  ⚠  "{raw_name}" normalizes the same as "{deduped[key][0]}" — '
                "using this batch's later value",
                file=sys.stderr,
            )
        deduped[key] = (raw_name, summary)

    applied, added, updated, not_found, rejected = [], [], [], [], []

    for key, (raw_name, summary) in deduped.items():
        if not summary.strip():
            rejected.append(raw_name)
            continue
        matches = by_normalized.get(key)
        if not matches:
            not_found.append(raw_name)
            continue
        if len(matches) > 1:
            print(
                f'  ⚠  "{raw_name}" — {len(matches)} entries share this normalized name, '
                "skipping (ambiguous)",
                file=sys.stderr,
            )
            not_found.append(raw_name)
            continue
        entry = matches[0]
        had_summary = bool(entry.get("summary"))
        old_summary = entry.get("summary")
        entry["summary"] = summary
        applied.append(entry["name"])
        (updated if had_summary else added).append((entry["name"], old_summary, summary))

    if rejected:
        print(f"REJECTED ({len(rejected)}) — empty summary text, not applied:", file=sys.stderr)
        for name in rejected:
            print(f"  - {name}", file=sys.stderr)

    prefix = "[DRY RUN] " if dry_run else ""
    total = len(deduped) - len(rejected)
    print(f"{prefix}Matched {len(applied)} of {total} entries in {_json_path(root).name}")
    for name, _old, new in added:
        print(f'  + added   "{name}": {_truncate(new)}')
    for name, old, new in updated:
        print(f'  ~ updated "{name}": {_truncate(old or "")} -> {_truncate(new)}')

    if not_found:
        print(
            f"NOT FOUND ({len(not_found)}) — not written, check for typos or re-run "
            "missing-summary:"
        )
        for name in not_found:
            print(f"  - {name}")

    if not applied:
        return 1

    if dry_run:
        print(f"\n{prefix}No file written.")
        return 0

    json_path = _json_path(root)
    backup_path = _backup_path(root)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(json_path, backup_path)

    fd, tmp_name = tempfile.mkstemp(dir=json_path.parent, suffix=".json.tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
            f.write("\n")
        Path(tmp_name).replace(json_path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise

    print(f"\nWritten to: {json_path}")
    print(f"Backup:     {backup_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="update_learning_history.py",
        description="Merge a batch of summaries into data/pluralsight_learning_history.json "
        "without loading the whole file.",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="repo root (default: this repo)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    apply_p = subparsers.add_parser("apply", help="merge a batch of {name: summary} pairs")
    apply_p.add_argument(
        "--summaries-file", type=Path, required=True, help="JSON file: {name: summary, ...}"
    )
    apply_p.add_argument(
        "--dry-run", action="store_true", help="show what would change, write nothing"
    )

    args = parser.parse_args(argv)

    if args.command == "apply":
        return cmd_apply(args.root, args.summaries_file, args.dry_run)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
