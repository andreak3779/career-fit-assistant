#!/usr/bin/env python3
"""
Parse Pluralsight course history HTML export and merge with data/pluralsight_learning_history.json.

Usage:
    python parse_pluralsight_html.py                         # merge: add new entries
    python parse_pluralsight_html.py --enrich                # enrich: update all existing entries with latest HTML data
    python parse_pluralsight_html.py /path/to/export.html    # explicit file path
    python parse_pluralsight_html.py /path/to/export.html --enrich

Data contract: reads a Pluralsight HTML export, merges/enriches entries against
data/pluralsight_learning_history.json (authoritative), and writes the merged
result to outputs/pluralsight_learning_history.json for review — it does not
touch pluralsight-courses.md; that file is maintained separately by the
pluralsight-updater skill. Any change to the merged entry shape must be
spot-checked against pluralsight-courses.md before running "generate bundles"
— downstream bundle validation checks cross-file facts, not this rebuild step.
"""

import glob
import json
import os
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

__version__ = "0.9.0"

SCRIPT_DIR = Path(__file__).resolve().parent

JSON_FILE = SCRIPT_DIR / "data" / "pluralsight_learning_history.json"
MD_FILE = SCRIPT_DIR / "outputs" / "pluralsight-courses.md"
OUTPUT_JSON = SCRIPT_DIR / "outputs" / "pluralsight_learning_history.json"

MIN_STRUCTURAL_ROWS = 10


class ParserError(Exception):
    """Raised for unrecoverable parser/validation errors."""


# ── File detection ─────────────────────────────────────────────────────────────


def find_html_file(args):
    for arg in args:
        if arg.endswith(".html"):
            if not os.path.isabs(arg):
                arg = str(SCRIPT_DIR / arg)
            if not os.path.exists(arg):
                raise ParserError(f"File not found: {arg}")
            return arg
    candidates = sorted(
        glob.glob(str(SCRIPT_DIR / "outputs" / "uploads" / "*.html")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not candidates:
        raise ParserError("No .html file found in outputs/uploads/")
    print(f"  Auto-detected HTML: {os.path.basename(candidates[0])}")
    return candidates[0]


# ── Structural validation ──────────────────────────────────────────────────────


def validate_structure(soup, html_path):
    errors = []
    rows = soup.find_all("tr", {"role": "row"})
    if not rows:
        errors.append("No <tr role='row'> elements found — table structure is missing")
    valid_rows = [r for r in rows if len(r.find_all("td", {"role": "gridcell"})) >= 8]
    if len(valid_rows) < MIN_STRUCTURAL_ROWS:
        errors.append(
            f"Only {len(valid_rows)} rows with 8+ gridcell columns "
            f"(expected {MIN_STRUCTURAL_ROWS}+). Possible format change or filtered export."
        )
    if not soup.find("span", string="Course") and not soup.find("span", string="Lab"):
        errors.append("No <span>Course</span> or <span>Lab</span> — type column may have changed.")
    date_times = [
        t for t in soup.find_all("time") if re.match(r"^\d{2}-\d{2}-\d{4}$", t.get("datetime", ""))
    ]
    if not date_times:
        errors.append("No <time datetime='MM-DD-YYYY'> — date column format may have changed.")
    if errors:
        header = f"STRUCTURAL VALIDATION FAILED: {os.path.basename(html_path)}"
        detail = "\n  • ".join([""] + errors).strip()
        raise ParserError(
            f"\n❌ {header}\n"
            "The Pluralsight HTML format may have changed. No output was written.\n"
            f"{detail}\n\n"
            "Next step: inspect the HTML and update the parser to match the new layout."
        )
    print(
        f"  ✓ Structure valid — {len(valid_rows)} data rows, "
        f"{len(soup.find_all('span', string='Course'))} courses, "
        f"{len(soup.find_all('span', string='Lab'))} labs, "
        f"{len(date_times)} dated entries"
    )


# ── Parsing helpers ────────────────────────────────────────────────────────────


def parse_time_text(text):
    if not text:
        return None
    text = text.strip()
    if text in ("-", ""):
        return None
    if re.match(r"^\d+[hm]", text):
        return text
    return None


def parse_progress_text(text):
    if not text:
        return None
    text = text.strip()
    if text in ("-", ""):
        return None
    if re.match(r"^\d+[hm]", text):
        return text
    if re.match(r"^\d+ of \d+", text):
        return text
    return None


def normalize_url(href):
    if not href:
        return None
    if href.startswith("https://"):
        return href
    if href.startswith("/"):
        return f"https://app.pluralsight.com{href}"
    return href


def parse_date(cell):
    time_el = cell.find("time")
    if not time_el:
        return None
    dt = time_el.get("datetime", "")
    if re.match(r"\d{2}-\d{2}-\d{4}", dt):
        m, d, y = dt.split("-")
        months = [
            "",
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]
        return f"{months[int(m)]} {int(d):02d}, {y}"
    return time_el.get_text(strip=True) or None


def parse_completion_pct(cell):
    text = cell.get_text(strip=True)
    if re.match(r"^\d+\.?\d*%$", text):
        return text
    return None


def determine_timing_profile(entry_type, duration):
    """
    Determine timing profile from entry type and duration.
      - Lab:      'Full Lab' if duration else 'Lab'
      - Course:   'Full Course' if duration totals more than 1 hour,
                 'Short Course' if duration is empty/None or <= 1h
    """
    if not duration:
        return "Lab" if entry_type == "Lab" else "Short Course"

    hours = 0
    minutes = 0
    h_match = re.search(r"(\d+)\s*h", duration)
    m_match = re.search(r"(\d+)\s*m", duration)
    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))

    total_hours = hours + minutes / 60.0

    if entry_type == "Lab":
        return "Full Lab"
    return "Full Course" if total_hours > 1 else "Short Course"


# ── Name normalization ─────────────────────────────────────────────────────────


def normalize_name(name):
    """Collapse all internal whitespace for matching."""
    return re.sub(r"\s+", " ", name).lower().strip()


# ── Main HTML parser ───────────────────────────────────────────────────────────


def parse_html(html_path):
    with open(html_path, encoding="utf-8") as f:
        content = f.read()
    soup = BeautifulSoup(content, "lxml")
    validate_structure(soup, html_path)

    rows = soup.find_all("tr", {"role": "row"})
    courses, skipped = [], 0

    for row in rows:
        cells = row.find_all("td", {"role": "gridcell"})
        if len(cells) < 8:
            continue

        name_link = cells[1].find("a")
        if not name_link:
            skipped += 1
            continue
        name = re.sub(r"\s+", " ", name_link.get_text(strip=True))  # collapse whitespace
        if not name:
            skipped += 1
            continue
        url = normalize_url(name_link.get("href", ""))

        type_span = cells[2].find("span")
        entry_type = type_span.get_text(strip=True) if type_span else "Course"

        col4_time = cells[3].find("time")
        view_time = parse_time_text(col4_time.get_text(strip=True) if col4_time else None)

        col5_text = cells[4].get_text(strip=True)
        progress_raw = (
            None
            if col5_text == "-"
            else (
                cells[4].find("time").get_text(strip=True) if cells[4].find("time") else col5_text
            )
        )
        progress = parse_progress_text(progress_raw)

        col6_text = cells[5].get_text(strip=True)
        if col6_text == "-":
            duration = None
        else:
            col6_time = cells[5].find("time")
            duration = parse_time_text(col6_time.get_text(strip=True) if col6_time else col6_text)

        completion_pct = parse_completion_pct(cells[6])
        completed_date = parse_date(cells[7])
        timing_profile = determine_timing_profile(entry_type, duration)

        courses.append(
            {
                "name": name,
                "type": entry_type,
                "url": url,
                "view_time": view_time,
                "progress": progress if entry_type == "Course" else None,
                "duration": duration,
                "completion_percentage": completion_pct,
                "completed_date": completed_date,
                "timing_profile": timing_profile,
            }
        )

    if skipped:
        print(f"  ⚠  Skipped {skipped} rows with no name link")
    return courses


# ── Merge helpers ──────────────────────────────────────────────────────────────


def load_existing_json(json_path):
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def find_new_courses(html_courses, existing):
    existing_names = {normalize_name(c["name"]) for c in existing}
    return [c for c in html_courses if normalize_name(c["name"]) not in existing_names]


def enrich_existing(html_courses, existing):
    """
    Update all existing JSON entries with fresh HTML data:
      - updates timing_profile using the new determine_timing_profile logic
      - adds/updates completion_percentage
      - backfills null progress / view_time where HTML has a value
    Returns the enriched list (same order as existing, new entries appended).
    """
    html_lookup = {normalize_name(c["name"]): c for c in html_courses}
    enriched, missing = [], []

    for entry in existing:
        key = normalize_name(entry["name"])
        html = html_lookup.get(key)
        if html:
            entry["completion_percentage"] = html["completion_percentage"]
            entry["timing_profile"] = html["timing_profile"]  # re-derive from new logic
            if entry.get("progress") is None and html.get("progress"):
                entry["progress"] = html["progress"]
            if entry.get("view_time") is None and html.get("view_time"):
                entry["view_time"] = html["view_time"]
        else:
            entry.setdefault("completion_percentage", "100.0%")
            missing.append(entry["name"])
        enriched.append(entry)

    if missing:
        print(f"  ⚠  {len(missing)} existing entries not found in HTML (timing_profile unchanged):")
        for n in missing[:5]:
            print(f"     {n}")
        if len(missing) > 5:
            print(f"     … and {len(missing) - 5} more")

    return enriched


# ── In-progress transition detection ──────────────────────────────────────────


def detect_completed_transitions(all_json_courses, md_path):
    try:
        with open(md_path, encoding="utf-8") as f:
            md = f.read()
    except FileNotFoundError:
        return []
    in_progress_names = re.findall(r"\[([^\]]+)\]\(https://[^)]+\)\s*\|\s*\d+%", md)
    # Only flag transitions where the HTML now shows 100%
    completed_lookup = {
        normalize_name(c["name"]): c
        for c in all_json_courses
        if c.get("completion_percentage") == "100.0%"
    }
    return [
        (name, completed_lookup[normalize_name(name)])
        for name in in_progress_names
        if normalize_name(name) in completed_lookup
    ]


# ── Entry point ────────────────────────────────────────────────────────────────


def main():
    print(f"Pluralsight HTML parser v{__version__}")
    args = sys.argv[1:]
    enrich_mode = "--enrich" in args
    args = [a for a in args if a != "--enrich"]

    try:
        html_path = find_html_file(args)
        print(f"\nParsing: {os.path.basename(html_path)}")
        html_courses = parse_html(html_path)
        print(f"  Extracted {len(html_courses)} entries from HTML")

        print(f"\nLoading existing JSON: {JSON_FILE.name}")
        existing = load_existing_json(JSON_FILE)
        print(f"  {len(existing)} existing entries")

        if enrich_mode:
            print("\n── Enrich mode: updating all entries with latest HTML data ──")
            enriched = enrich_existing(html_courses, existing)
            new_courses = find_new_courses(html_courses, existing)
            merged = new_courses + enriched
            print(f"  Updated {len(enriched)} entries | {len(new_courses)} new entries added")
        else:
            new_courses = find_new_courses(html_courses, existing)
            merged = new_courses + existing

        if new_courses:
            print(f"\n=== NEW ENTRIES ({len(new_courses)}) ===")
            for c in new_courses:
                print(
                    f"  [{c['timing_profile']:12}] {c['completion_percentage']:8} {c['name']} — {c['completed_date']}"
                )
        else:
            print("\n✓ No new entries — JSON is already up to date")

        transitions = detect_completed_transitions(merged, MD_FILE)
        if transitions:
            print(f"\n=== MOVE FROM IN-PROGRESS TO COMPLETED ({len(transitions)}) ===")
            for name, entry in transitions:
                print(f"  ↗  {name}")
                print(
                    f"       completed: {entry['completed_date']} | {entry.get('completion_percentage', '?')}"
                )
        else:
            print("\n✓ No in-progress → completed transitions detected")

        OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"\n{'─' * 60}")
        print(f"Output:  {OUTPUT_JSON}")
        print(f"Total:   {len(merged)} entries")
        mode_label = "enriched+merged" if enrich_mode else "merged"
        print(f"Mode:    {mode_label}")
        if transitions:
            print(
                f"Action:  Move {len(transitions)} course(s) from in-progress → completed in pluralsight-courses.md"
            )
    except ParserError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
