#!/usr/bin/env python3
"""Insert one or more newly-completed courses/labs into pluralsight-courses.md
without loading the whole ~15.5K-token file into an LLM's context.

The pluralsight-updater skill's most frequently triggered workflow ("I just
finished X") previously required the model to know the entire current file (to
place the row, bump every count) and re-emit it whole via the Write tool. This
script does that merge server-side: the caller only supplies the resolved fields
for the new entry (title, section, date, duration, timing_profile — already
looked up via query_learning_history.py, parse_pluralsight_html.py, or
web_search) and the script handles insertion, section/heading/Summary-table
count bumps, and the "Last updated" line.

Scope: only touches the "## Completed Courses" region + the "## Summary" table
+ the top Status/Totals/Last-updated lines. It does NOT touch the AI-200
in-progress table, the "Other In-Progress Courses" table, "Planned / Not
Started", or "Dropped in rebuild" — moving an in-progress item to completed, or
adding a new section, remains a manual/separate step.

Writes IN PLACE to pluralsight-courses.md (a deliberate deviation from
parse_pluralsight_html.py's stage-to-outputs/-then-promote convention — the
current skill text never actually promotes outputs/pluralsight-courses.md to
the real file, so following that convention here would just formalize an
existing gap). Use --dry-run to preview the diff before committing.

Usage:
    python scripts/merge_pluralsight_course.py add \\
        --title "Course Title" [--url "https://..."] --type Course \\
        --section "☁️ Microsoft Azure" --completed-date "Sep 10, 2026" \\
        --duration "1h 15m" --timing-profile "Full Course" \\
        --note "Completed the new Azure networking course."
    python scripts/merge_pluralsight_course.py add-batch \\
        --entries-file batch.json --note "3 new completions from Sept sync."

--section must exactly match an existing "### <emoji> <name>" heading (minus
its trailing count suffix) — this script never creates a new section or
guesses a close match. Duplicate titles are rejected across the whole
Completed Courses region, not just the target section.

Exit code 0 on success (or a valid --dry-run preview); 1 for a missing file,
section-not-found, a duplicate title, or an unparseable date.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

VALID_TIMING_PROFILES = {"Full Course", "Short Course", "Full Lab", "Lab"}

SECTION_HEADING_RE = re.compile(
    r"^### (?P<name>.+) \((?P<c_num>\d+) (?P<c_word>Courses?) · (?P<l_num>\d+) (?P<l_word>Labs?)\)$"
)
COMPLETED_HEADING_RE = re.compile(
    r"^## ✅ Completed Courses \((?P<c_num>\d+) Courses · (?P<l_num>\d+) Labs\)$"
)
STATUS_RE = re.compile(
    r"^\*\*Status:\*\* (?P<courses>\d+) courses completed \| "
    r"(?P<courses_ip>\d+) courses in progress \| "
    r"(?P<labs>\d+) labs \((?P<labs_c>\d+) completed, (?P<labs_ip>\d+) in progress\)$"
)
TOTALS_RE = re.compile(r"^\*\*Totals:\*\* (?P<courses>\d+) courses · (?P<labs>\d+) labs$")
LAST_UPDATED_RE = re.compile(r"^\*\*Last updated:\*\*")
LABS_BOLD_RE = re.compile(r"^\*\*(?P<name>.+) Labs\*\*$")
TITLE_LINK_RE = re.compile(r"^\[(?P<title>.+)\]\((?P<url>[^)]+)\)$")
SUMMARY_HEADING_RE = re.compile(r"^## Summary$")
BOLD_NUM_RE = re.compile(r"^\*\*(\d+)\*\*$")


class MergeError(Exception):
    pass


def _md_path(root: Path) -> Path:
    return root / "project-2-profile-learning-hub" / "pluralsight-courses.md"


def _backup_path(root: Path) -> Path:
    return root / "project-2-profile-learning-hub" / "outputs" / "pluralsight-courses.md.bak"


def _split_row(line: str) -> list[str]:
    inner = line.strip()
    return [c.strip() for c in inner[1:-1].split("|")]


def _join_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _title_cell(title: str, url: str | None) -> str:
    return f"[{title}]({url})" if url else title


def _row_title(cells: list[str]) -> str:
    m = TITLE_LINK_RE.match(cells[0])
    return m.group("title") if m else cells[0]


def _parse_row_date(cells: list[str]) -> date:
    return datetime.strptime(cells[1], "%b %d, %Y").date()


@dataclass
class Entry:
    title: str
    type: str
    section: str
    completed_date: str
    duration: str
    timing_profile: str
    url: str | None = None
    warnings: list[str] = field(default_factory=list)


def _entry_from_dict(d: dict[str, Any]) -> Entry:
    required = ["title", "type", "section", "completed_date", "duration", "timing_profile"]
    missing = [k for k in required if not d.get(k)]
    if missing:
        raise MergeError(f"entry missing required field(s): {', '.join(missing)}")
    return Entry(
        title=d["title"],
        type=d["type"],
        section=d["section"],
        completed_date=d["completed_date"],
        duration=d["duration"],
        timing_profile=d["timing_profile"],
        url=d.get("url"),
    )


def _validate_entry(entry: Entry) -> None:
    if entry.type not in ("Course", "Lab"):
        raise MergeError(f'--type must be "Course" or "Lab", got "{entry.type}"')
    try:
        datetime.strptime(entry.completed_date, "%b %d, %Y")
    except ValueError as exc:
        raise MergeError(
            f'--completed-date "{entry.completed_date}" must match "Mon DD, YYYY" (e.g. "Sep 10, 2026")'
        ) from exc
    full_profiles = {"Course": "Full Course", "Lab": "Full Lab"}
    short_profiles = {"Course": "Short Course", "Lab": "Lab"}
    if entry.timing_profile not in VALID_TIMING_PROFILES:
        entry.warnings.append(
            f'timing_profile "{entry.timing_profile}" is not one of {sorted(VALID_TIMING_PROFILES)}'
        )
    elif entry.duration == "—" and entry.timing_profile == full_profiles[entry.type]:
        entry.warnings.append(
            f'timing_profile "{entry.timing_profile}" usually has a real duration, got "—"'
        )
    elif entry.duration != "—" and entry.timing_profile == short_profiles[entry.type]:
        entry.warnings.append(
            f'timing_profile "{entry.timing_profile}" usually has duration "—", got "{entry.duration}"'
        )


def _find_completed_region(lines: list[str]) -> tuple[int, int]:
    start = next((i for i, ln in enumerate(lines) if COMPLETED_HEADING_RE.match(ln)), None)
    if start is None:
        raise MergeError('"## ✅ Completed Courses (...)" heading not found')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


def _find_sections(lines: list[str], start: int, end: int) -> list[tuple[int, re.Match]]:
    return [
        (i, SECTION_HEADING_RE.match(lines[i]))
        for i in range(start, end)
        if SECTION_HEADING_RE.match(lines[i])
    ]


def _section_span(
    sections: list[tuple[int, re.Match]], idx: int, region_end: int
) -> tuple[int, int]:
    pos = next(k for k, (i, _) in enumerate(sections) if i == idx)
    next_start = sections[pos + 1][0] if pos + 1 < len(sections) else region_end
    return idx, next_start


def _find_table(
    lines: list[str], start: int, end: int, header_first_cell: str
) -> tuple[int, int] | None:
    """Return (rows_start, rows_end) for a table whose header's first cell matches,
    searching lines[start:end]. rows_end is exclusive (first blank/non-row line)."""
    for i in range(start, end):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|"):
            cells = _split_row(line)
            if cells and cells[0] == header_first_cell:
                rows_start = i + 2  # skip header + separator
                j = rows_start
                while (
                    j < end and lines[j].strip().startswith("|") and lines[j].strip().endswith("|")
                ):
                    j += 1
                return rows_start, j
    return None


def _find_labs_bold(lines: list[str], start: int, end: int) -> int | None:
    for i in range(start, end):
        if LABS_BOLD_RE.match(lines[i].strip()):
            return i
    return None


def _insertion_index(
    lines: list[str], rows_start: int, rows_end: int, new_date: date
) -> tuple[int, str | None]:
    """Where to insert, plus a description of the row it lands after (or None if first)."""
    after_row_desc = None
    idx = rows_start
    for i in range(rows_start, rows_end):
        cells = _split_row(lines[i])
        if _parse_row_date(cells) <= new_date:
            idx = i + 1
            after_row_desc = f"{_row_title(cells)} ({cells[1]})"
        else:
            break
    return idx, after_row_desc


def _check_duplicate(
    lines: list[str], region_start: int, region_end: int, title: str
) -> str | None:
    """Return the section name a duplicate title was found in, or None."""
    sections = _find_sections(lines, region_start, region_end)
    for idx, m in sections:
        sec_start, sec_end = _section_span(sections, idx, region_end)
        for header_cell in ("Course", "Lab"):
            table = _find_table(lines, sec_start, sec_end, header_cell)
            if not table:
                continue
            rows_start, rows_end = table
            for i in range(rows_start, rows_end):
                if _row_title(_split_row(lines[i])) == title:
                    return m.group("name")
    return None


def _bump_section_heading(lines: list[str], idx: int, entry_type: str) -> tuple[str, str]:
    m = SECTION_HEADING_RE.match(lines[idx])
    c_num, c_word, l_num, l_word = (
        int(m.group("c_num")),
        m.group("c_word"),
        int(m.group("l_num")),
        m.group("l_word"),
    )
    old = f"{c_num} {c_word} · {l_num} {l_word}"
    if entry_type == "Course":
        c_num += 1
    else:
        l_num += 1
    new = f"{c_num} {c_word} · {l_num} {l_word}"
    lines[idx] = f"### {m.group('name')} ({new})"
    return old, new


@dataclass
class InsertResult:
    entry: Entry
    section_before: str
    section_after: str
    after_row_desc: str | None
    created_labs_table: bool


def _insert_one(lines: list[str], entry: Entry) -> InsertResult:
    region_start, region_end = _find_completed_region(lines)
    sections = _find_sections(lines, region_start, region_end)
    match = next((m for _, m in sections if m.group("name") == entry.section), None)
    if match is None:
        valid = "\n".join(f"  - {m.group('name')}" for _, m in sections)
        raise MergeError(f'section "{entry.section}" not found. Valid sections:\n{valid}')
    section_idx = next(i for i, m in sections if m.group("name") == entry.section)

    dup_section = _check_duplicate(lines, region_start, region_end, entry.title)
    if dup_section:
        raise MergeError(
            f'"{entry.title}" already exists in section "{dup_section}" — refusing to insert a duplicate.'
        )

    sec_start, sec_end = _section_span(sections, section_idx, region_end)
    new_date = datetime.strptime(entry.completed_date, "%b %d, %Y").date()
    row = _join_row(
        [
            _title_cell(entry.title, entry.url),
            entry.completed_date,
            entry.duration,
            entry.timing_profile,
        ]
    )

    created_labs_table = False
    if entry.type == "Course":
        table = _find_table(lines, sec_start, sec_end, "Course")
        if table is None:
            raise MergeError(f'section "{entry.section}" has no Courses table')
        rows_start, rows_end = table
        insert_at, after_desc = _insertion_index(lines, rows_start, rows_end, new_date)
        lines.insert(insert_at, row)
    else:
        labs_bold_idx = _find_labs_bold(lines, sec_start, sec_end)
        if labs_bold_idx is not None:
            table = _find_table(lines, labs_bold_idx, sec_end, "Lab")
            rows_start, rows_end = table
            insert_at, after_desc = _insertion_index(lines, rows_start, rows_end, new_date)
            lines.insert(insert_at, row)
        else:
            # No Labs sub-table yet — create one right after the Courses table's
            # trailing blank line (i.e. at the section's current end, before the
            # closing blank+"---"/next-heading boundary).
            courses_table = _find_table(lines, sec_start, sec_end, "Course")
            insert_at = courses_table[1] if courses_table else sec_start + 1
            # skip the single blank line that follows the courses table
            if insert_at < sec_end and lines[insert_at].strip() == "":
                insert_at += 1
            block = [
                f"**{entry.section} Labs**",
                "",
                "| Lab | Completed Date | Duration | Timing Profile |",
                "|-----|-----------------|----------|-----------------|",
                row,
                "",
            ]
            lines[insert_at:insert_at] = block
            after_desc = None
            created_labs_table = True

    old, new = _bump_section_heading(lines, section_idx, entry.type)
    return InsertResult(entry, old, new, after_desc, created_labs_table)


def _bump_completed_heading(lines: list[str], entry_type: str) -> tuple[str, str]:
    idx = next(i for i, ln in enumerate(lines) if COMPLETED_HEADING_RE.match(ln))
    m = COMPLETED_HEADING_RE.match(lines[idx])
    c_num, l_num = int(m.group("c_num")), int(m.group("l_num"))
    old = f"{c_num} Courses · {l_num} Labs"
    if entry_type == "Course":
        c_num += 1
    else:
        l_num += 1
    new = f"{c_num} Courses · {l_num} Labs"
    lines[idx] = f"## ✅ Completed Courses ({new})"
    return old, new


def _bump_status_and_totals(lines: list[str], course_delta: int, lab_delta: int) -> tuple[str, str]:
    status_idx = next(i for i, ln in enumerate(lines) if STATUS_RE.match(ln))
    m = STATUS_RE.match(lines[status_idx])
    courses = int(m.group("courses")) + course_delta
    courses_ip = int(m.group("courses_ip"))
    labs = int(m.group("labs")) + lab_delta
    labs_c = int(m.group("labs_c")) + lab_delta
    labs_ip = int(m.group("labs_ip"))
    old_status = lines[status_idx]
    lines[status_idx] = (
        f"**Status:** {courses} courses completed | {courses_ip} courses in progress | "
        f"{labs} labs ({labs_c} completed, {labs_ip} in progress)"
    )

    totals_idx = next(i for i, ln in enumerate(lines) if TOTALS_RE.match(ln))
    lines[totals_idx] = f"**Totals:** {courses + courses_ip} courses · {labs} labs"
    return old_status, lines[status_idx]


def _replace_last_updated(lines: list[str], updated_date: str, note: str) -> None:
    idx = next(i for i, ln in enumerate(lines) if LAST_UPDATED_RE.match(ln))
    lines[idx] = f"**Last updated:** {updated_date} ({note})"


def _bump_summary_table(lines: list[str], section: str, entry_type: str) -> None:
    idx = next((i for i, ln in enumerate(lines) if SUMMARY_HEADING_RE.match(ln)), None)
    if idx is None:
        return  # tolerate a fixture/file with no Summary table rather than crash
    col = 1 if entry_type == "Course" else 2  # Completed Courses | Completed Labs
    i = idx + 1
    started = False
    while i < len(lines):
        line = lines[i].strip()
        if not (line.startswith("|") and line.endswith("|")):
            if started:
                break  # blank/"---" line after the table — done
            i += 1  # blank line before the table — keep looking
            continue
        started = True
        if set(line.replace("|", "").strip()) <= {"-"}:
            i += 1  # separator row
            continue
        cells = _split_row(line)
        if cells[0] == "Area":
            i += 1  # header row
            continue
        if cells[0] == section:
            cells[col] = str(int(cells[col]) + 1)
            lines[i] = _join_row(cells)
        elif cells[0] == "**TOTAL**":
            m = BOLD_NUM_RE.match(cells[col])
            if m:
                cells[col] = f"**{int(m.group(1)) + 1}**"
                lines[i] = _join_row(cells)
        i += 1


def _print_report(
    results: list[InsertResult], dry_run: bool, written_to: Path | None, backup: Path | None
) -> None:
    prefix = "[DRY RUN] " if dry_run else ""
    print(f"{prefix}merge_pluralsight_course.py — pluralsight-courses.md\n")
    for r in results:
        e = r.entry
        print(
            f"+ {_title_cell(e.title, e.url)} | {e.completed_date} | {e.duration} | {e.timing_profile}"
        )
        where = f'after "{r.after_row_desc}"' if r.after_row_desc else "as first row"
        note = "  (created new Labs sub-table)" if r.created_labs_table else ""
        print(f"  section: {e.section} — inserted {where}{note}")
        print(f"  section header: {r.section_before}  ->  {r.section_after}")
        for w in e.warnings:
            print(f"  ⚠  {w}")
    if written_to:
        print(f"\nWritten to: {written_to}")
        print(f"Backup:     {backup}")
    elif dry_run:
        print(f"\n{prefix}No file written.")


def _run(root: Path, entries: list[Entry], note: str, updated_date: str, dry_run: bool) -> int:
    path = _md_path(root)
    if not path.is_file():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if trailing_newline:
        lines = lines[:-1]

    results: list[InsertResult] = []
    for entry in entries:
        try:
            _validate_entry(entry)
            results.append(_insert_one(lines, entry))
        except MergeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    course_delta = sum(1 for e in entries if e.type == "Course")
    lab_delta = sum(1 for e in entries if e.type == "Lab")
    for _ in range(course_delta):
        _bump_completed_heading(lines, "Course")
    for _ in range(lab_delta):
        _bump_completed_heading(lines, "Lab")
    _bump_status_and_totals(lines, course_delta, lab_delta)
    _replace_last_updated(lines, updated_date, note)
    for entry in entries:
        _bump_summary_table(lines, entry.section, entry.type)

    if dry_run:
        _print_report(results, dry_run=True, written_to=None, backup=None)
        return 0

    backup_path = _backup_path(root)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)

    new_text = "\n".join(lines) + ("\n" if trailing_newline else "")
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, suffix=".md.tmp")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(new_text)
        Path(tmp_name).replace(path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise

    _print_report(results, dry_run=False, written_to=path, backup=backup_path)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    entry = Entry(
        title=args.title,
        type=args.type,
        section=args.section,
        completed_date=args.completed_date,
        duration=args.duration,
        timing_profile=args.timing_profile,
        url=args.url,
    )
    updated_date = args.updated_date or date.today().strftime("%b %d, %Y")
    return _run(args.root, [entry], args.note, updated_date, args.dry_run)


def cmd_add_batch(args: argparse.Namespace) -> int:
    try:
        raw = json.loads(args.entries_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: entries file not found: {args.entries_file}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in {args.entries_file}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(raw, list) or not raw:
        print(f"ERROR: {args.entries_file} must be a non-empty JSON array", file=sys.stderr)
        return 1
    try:
        entries = [_entry_from_dict(d) for d in raw]
    except MergeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    seen: dict[str, int] = {}
    for i, e in enumerate(entries):
        if e.title in seen:
            print(
                f'ERROR: duplicate title "{e.title}" within this batch '
                f"(entries {seen[e.title]} and {i})",
                file=sys.stderr,
            )
            return 1
        seen[e.title] = i

    updated_date = args.updated_date or date.today().strftime("%b %d, %Y")
    return _run(args.root, entries, args.note, updated_date, args.dry_run)


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="merge_pluralsight_course.py",
        description="Insert new completed course(s)/lab(s) into pluralsight-courses.md "
        "without loading the whole file.",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="repo root (default: this repo)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_p = subparsers.add_parser("add", help="insert a single completed course/lab")
    add_p.add_argument("--title", required=True)
    add_p.add_argument("--url", default=None)
    add_p.add_argument("--type", required=True, choices=["Course", "Lab"])
    add_p.add_argument("--section", required=True, help='exact "### <emoji> <name>" heading text')
    add_p.add_argument("--completed-date", required=True, help='e.g. "Sep 10, 2026"')
    add_p.add_argument("--duration", required=True, help='e.g. "1h 15m" or "—"')
    add_p.add_argument("--timing-profile", required=True)
    add_p.add_argument("--note", required=True, help="Last-updated changelog sentence")
    add_p.add_argument("--updated-date", default=None, help="override today's date (for tests)")
    add_p.add_argument("--dry-run", action="store_true")

    batch_p = subparsers.add_parser("add-batch", help="insert multiple completed courses/labs")
    batch_p.add_argument("--entries-file", type=Path, required=True)
    batch_p.add_argument("--note", required=True, help="Last-updated changelog sentence")
    batch_p.add_argument("--updated-date", default=None, help="override today's date (for tests)")
    batch_p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "add":
        return cmd_add(args)
    if args.command == "add-batch":
        return cmd_add_batch(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
