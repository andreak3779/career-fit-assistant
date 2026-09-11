"""Tests for project-2-profile-learning-hub/parse_pluralsight_html.py.

The module lives outside the installed package tree and hardcodes its I/O
paths (JSON_FILE, MD_FILE, OUTPUT_JSON) relative to its own SCRIPT_DIR rather
than a repo-root argument (unlike build_bundles.py / render_md_bundles.py).
Any test that calls main() must monkeypatch those three module attributes to
tmp_path locations first — otherwise it would read/write the real personal
learning-history data in project-2-profile-learning-hub/data/.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "project-2-profile-learning-hub" / "parse_pluralsight_html.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("parse_pluralsight_html", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p():
    return _load_module()


# ── Small parsing helpers ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "text,expected",
    [
        (None, None),
        ("", None),
        ("-", None),
        ("2h 30m", "2h 30m"),
        ("45m", "45m"),
        ("garbage", None),
    ],
)
def test_parse_time_text(p, text, expected):
    assert p.parse_time_text(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        (None, None),
        ("-", None),
        ("45m", "45m"),
        ("3 of 10 modules", "3 of 10 modules"),
        ("nonsense", None),
    ],
)
def test_parse_progress_text(p, text, expected):
    assert p.parse_progress_text(text) == expected


@pytest.mark.parametrize(
    "href,expected",
    [
        (None, None),
        ("", None),
        ("https://app.pluralsight.com/course/x", "https://app.pluralsight.com/course/x"),
        ("/course/x", "https://app.pluralsight.com/course/x"),
        ("mailto:x@example.com", "mailto:x@example.com"),
    ],
)
def test_normalize_url(p, href, expected):
    assert p.normalize_url(href) == expected


def test_parse_completion_pct(p):
    cell = BeautifulSoup("<td>45.0%</td>", "lxml").td
    assert p.parse_completion_pct(cell) == "45.0%"
    cell = BeautifulSoup("<td>-</td>", "lxml").td
    assert p.parse_completion_pct(cell) is None


def test_parse_date_formats_mm_dd_yyyy(p):
    cell = BeautifulSoup('<td><time datetime="08-15-2026">08/15/2026</time></td>', "lxml").td
    assert p.parse_date(cell) == "Aug 15, 2026"


def test_parse_date_missing_time_element(p):
    cell = BeautifulSoup("<td>-</td>", "lxml").td
    assert p.parse_date(cell) is None


@pytest.mark.parametrize(
    "entry_type,duration,expected",
    [
        ("Lab", None, "Lab"),
        ("Lab", "45m", "Full Lab"),
        ("Course", None, "Short Course"),
        ("Course", "45m", "Short Course"),
        ("Course", "1h", "Short Course"),
        ("Course", "1h 1m", "Full Course"),
        ("Course", "2h 30m", "Full Course"),
    ],
)
def test_determine_timing_profile(p, entry_type, duration, expected):
    assert p.determine_timing_profile(entry_type, duration) == expected


def test_normalize_name_collapses_whitespace_and_case(p):
    assert p.normalize_name("  Building   APIs  \nWith  ASP.NET  ") == "building apis with asp.net"


# ── Merge helpers (pure list/dict logic) ─────────────────────────────────────


def test_find_new_courses_returns_only_unseen_names(p):
    existing = [{"name": "Course A"}, {"name": "Course B"}]
    html_courses = [{"name": "course a"}, {"name": "Course C"}]
    new = p.find_new_courses(html_courses, existing)
    assert [c["name"] for c in new] == ["Course C"]


def test_enrich_existing_updates_completion_and_backfills(p):
    existing = [
        {
            "name": "Course A",
            "completion_percentage": "45.0%",
            "timing_profile": "Short Course",
            "progress": None,
            "view_time": None,
        }
    ]
    html_courses = [
        {
            "name": "Course A",
            "completion_percentage": "100.0%",
            "timing_profile": "Full Course",
            "progress": "10 of 10",
            "view_time": "2h",
        }
    ]
    enriched = p.enrich_existing(html_courses, existing)
    assert enriched[0]["completion_percentage"] == "100.0%"
    assert enriched[0]["timing_profile"] == "Full Course"
    assert enriched[0]["progress"] == "10 of 10"
    assert enriched[0]["view_time"] == "2h"


def test_enrich_existing_defaults_missing_entry_to_complete(p):
    existing = [{"name": "Retired Course", "progress": None, "view_time": None}]
    enriched = p.enrich_existing([], existing)
    assert enriched[0]["completion_percentage"] == "100.0%"


def test_detect_completed_transitions_flags_100pct_in_progress_courses(p, tmp_path):
    md_path = tmp_path / "pluralsight-courses.md"
    md_path.write_text(
        "| [Course A](https://app.pluralsight.com/course/a) | 45% |\n"
        "| [Course B](https://app.pluralsight.com/course/b) | 10% |\n"
    )
    all_courses = [
        {"name": "Course A", "completion_percentage": "100.0%"},
        {"name": "Course B", "completion_percentage": "50.0%"},
    ]
    transitions = p.detect_completed_transitions(all_courses, md_path)
    assert [name for name, _ in transitions] == ["Course A"]


def test_detect_completed_transitions_missing_md_file_returns_empty(p, tmp_path):
    assert p.detect_completed_transitions([], tmp_path / "does-not-exist.md") == []


# ── HTML structural validation + parse_html ─────────────────────────────────


def _row(
    name, entry_type, view_time, progress, duration, completion_pct, date_mmddyyyy, href="/course/x"
):
    view_cell = f"<time>{view_time}</time>" if view_time else "-"
    date_cell = f'<time datetime="{date_mmddyyyy}">{date_mmddyyyy}</time>' if date_mmddyyyy else "-"
    return (
        '<tr role="row">'
        '<td role="gridcell"></td>'
        f'<td role="gridcell"><a href="{href}">{name}</a></td>'
        f'<td role="gridcell"><span>{entry_type}</span></td>'
        f'<td role="gridcell">{view_cell}</td>'
        f'<td role="gridcell">{progress or "-"}</td>'
        f'<td role="gridcell">{duration or "-"}</td>'
        f'<td role="gridcell">{completion_pct or "-"}</td>'
        f'<td role="gridcell">{date_cell}</td>'
        "</tr>"
    )


def _fixture_html(rows: list[str]) -> str:
    return f"<html><body><table>{''.join(rows)}</table></body></html>"


def _valid_rows(n=10):
    return [
        _row(
            f"Course {i}",
            "Course" if i % 3 else "Lab",
            "1h 30m",
            "-",
            "1h 30m" if i % 3 else None,
            "100.0%",
            "08-15-2026",
            href=f"/course/{i}",
        )
        for i in range(n)
    ]


def test_validate_structure_passes_on_well_formed_table(p):
    soup = BeautifulSoup(_fixture_html(_valid_rows()), "lxml")
    p.validate_structure(soup, "fixture.html")  # must not raise


def test_validate_structure_raises_on_too_few_rows(p):
    soup = BeautifulSoup(_fixture_html(_valid_rows(3)), "lxml")
    with pytest.raises(p.ParserError, match="STRUCTURAL VALIDATION FAILED"):
        p.validate_structure(soup, "fixture.html")


def test_validate_structure_raises_when_no_course_or_lab_span(p):
    rows = [
        r.replace("<span>Course</span>", "<span>Other</span>").replace(
            "<span>Lab</span>", "<span>Other</span>"
        )
        for r in _valid_rows()
    ]
    soup = BeautifulSoup(_fixture_html(rows), "lxml")
    with pytest.raises(p.ParserError, match="type column may have changed"):
        p.validate_structure(soup, "fixture.html")


def test_parse_html_extracts_expected_fields(p, tmp_path):
    html_path = tmp_path / "export.html"
    html_path.write_text(_fixture_html(_valid_rows()), encoding="utf-8")
    courses = p.parse_html(str(html_path))
    assert len(courses) == 10
    first = courses[0]
    assert first["name"] == "Course 0"
    assert first["type"] == "Lab"  # i % 3 == 0 -> Lab per _valid_rows
    assert first["completed_date"] == "Aug 15, 2026"
    assert first["timing_profile"] == "Lab"  # duration None for Lab rows in fixture


def test_parse_html_skips_rows_with_no_name_link(p, tmp_path):
    rows = _valid_rows(10)
    broken_row = (
        '<tr role="row">'
        '<td role="gridcell"></td>'
        '<td role="gridcell">no link here</td>'
        '<td role="gridcell"><span>Course</span></td>'
        '<td role="gridcell">-</td>'
        '<td role="gridcell">-</td>'
        '<td role="gridcell">-</td>'
        '<td role="gridcell">-</td>'
        '<td role="gridcell">-</td>'
        "</tr>"
    )
    html_path = tmp_path / "export.html"
    html_path.write_text(_fixture_html([*rows, broken_row]), encoding="utf-8")
    courses = p.parse_html(str(html_path))
    assert len(courses) == 10  # the broken row is skipped, not counted


# ── main() end-to-end (paths monkeypatched away from real data) ─────────────


def test_main_merges_new_courses_and_writes_output(p, tmp_path, monkeypatch, capsys):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()

    json_file = data_dir / "pluralsight_learning_history.json"
    json_file.write_text(
        json.dumps([{"name": "Existing Course", "completion_percentage": "100.0%"}])
    )
    output_json = outputs_dir / "pluralsight_learning_history.json"
    md_file = outputs_dir / "pluralsight-courses.md"

    monkeypatch.setattr(p, "JSON_FILE", json_file)
    monkeypatch.setattr(p, "OUTPUT_JSON", output_json)
    monkeypatch.setattr(p, "MD_FILE", md_file)

    html_path = tmp_path / "export.html"
    html_path.write_text(_fixture_html(_valid_rows()), encoding="utf-8")

    import sys as _sys

    old_argv = _sys.argv
    try:
        _sys.argv = ["parse_pluralsight_html.py", str(html_path)]
        rc = p.main()
    finally:
        _sys.argv = old_argv

    assert rc == 0
    written = json.loads(output_json.read_text())
    names = {c["name"] for c in written}
    assert "Existing Course" in names
    assert "Course 0" in names
    assert len(written) == 11  # 1 existing + 10 new from fixture

    out = capsys.readouterr().out
    assert "NEW ENTRIES (10)" in out


def test_main_returns_nonzero_on_structural_failure(p, tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    json_file = data_dir / "pluralsight_learning_history.json"
    json_file.write_text("[]")
    monkeypatch.setattr(p, "JSON_FILE", json_file)
    monkeypatch.setattr(
        p, "OUTPUT_JSON", tmp_path / "outputs" / "pluralsight_learning_history.json"
    )
    monkeypatch.setattr(p, "MD_FILE", tmp_path / "outputs" / "pluralsight-courses.md")

    html_path = tmp_path / "export.html"
    html_path.write_text(_fixture_html(_valid_rows(2)), encoding="utf-8")  # too few rows

    import sys as _sys

    old_argv = _sys.argv
    try:
        _sys.argv = ["parse_pluralsight_html.py", str(html_path)]
        rc = p.main()
    finally:
        _sys.argv = old_argv

    assert rc == 1
