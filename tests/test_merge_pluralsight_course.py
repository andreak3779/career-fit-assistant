"""Tests for project-2-profile-learning-hub/scripts/merge_pluralsight_course.py.

Same by-path-import pattern as the other project-2 script tests. All tests run
against a small fixture built from a representative slice of the real
pluralsight-courses.md structure (one section with labs, one without, the
Summary table, the header block) — never the real 587-line file.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "project-2-profile-learning-hub" / "scripts" / "merge_pluralsight_course.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("merge_pluralsight_course", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # dataclasses + `from __future__ import annotations` need the module
    # registered in sys.modules before exec, to resolve string annotations.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def m():
    return _load_module()


FIXTURE_MD = """# Pluralsight Courses — Sarah Ashford

**Status:** 2 courses completed | 0 courses in progress | 1 labs (1 completed, 0 in progress)
**Last updated:** Aug 01, 2026 (initial fixture)
**Totals:** 2 courses · 1 labs
**Format:** Full Course Details (Course | Completed Date | Duration | Timing Profile)

---

## ✅ Completed Courses (2 Courses · 1 Labs)

### ☁️ Microsoft Azure (1 Courses · 1 Labs)

| Course | Completed Date | Duration | Timing Profile |
|--------|-----------------|----------|-----------------|
| [Azure Fundamentals](https://app.pluralsight.com/library/courses/azure-fundamentals) | Jan 10, 2026 | 1h 0m | Full Course |

**☁️ Microsoft Azure Labs**

| Lab | Completed Date | Duration | Timing Profile |
|-----|-----------------|----------|-----------------|
| Plain Text Lab Title | Jan 15, 2026 | — | Lab |

---

### 🔷 ASP.NET Core & .NET (1 Courses · 0 Labs)

| Course | Completed Date | Duration | Timing Profile |
|--------|-----------------|----------|-----------------|
| [ASP.NET Core Basics](https://app.pluralsight.com/library/courses/aspnet-core-basics) | Feb 01, 2026 | 2h 0m | Full Course |

---

## Summary

| Area | Completed Courses | Completed Labs | In-Progress Courses | In-Progress Labs |
|------|--------------------|-----------------|----------------------|-------------------|
| ☁️ Microsoft Azure | 1 | 1 | 0 | 0 |
| 🔷 ASP.NET Core & .NET | 1 | 0 | 0 | 0 |
| **TOTAL** | **2** | **1** | **0** | **0** |

---
"""


@pytest.fixture
def fixture_root(tmp_path):
    project_dir = tmp_path / "project-2-profile-learning-hub"
    project_dir.mkdir(parents=True)
    (project_dir / "pluralsight-courses.md").write_text(FIXTURE_MD, encoding="utf-8")
    return tmp_path


def _md_text(fixture_root):
    return (fixture_root / "project-2-profile-learning-hub" / "pluralsight-courses.md").read_text(
        encoding="utf-8"
    )


def _add_args(**overrides):
    base = dict(
        title="Azure Networking Deep Dive",
        url="https://app.pluralsight.com/library/courses/azure-networking-deep-dive",
        type="Course",
        section="☁️ Microsoft Azure",
        completed_date="Jan 20, 2026",
        duration="2h 0m",
        timing_profile="Full Course",
        note="Added Azure networking course.",
        updated_date="Sep 10, 2026",
        dry_run=False,
    )
    base.update(overrides)
    return base


def test_add_course_chronological_insertion(m, fixture_root):
    rc = m._run(
        fixture_root,
        [
            m.Entry(
                title="Azure Networking Deep Dive",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="2h 0m",
                timing_profile="Full Course",
                url="https://x/azure-networking",
            )
        ],
        "Added Azure networking course.",
        "Sep 10, 2026",
        dry_run=False,
    )
    assert rc == 0
    text = _md_text(fixture_root)
    lines = text.split("\n")
    azure_idx = next(i for i, ln in enumerate(lines) if "Azure Fundamentals" in ln)
    networking_idx = next(i for i, ln in enumerate(lines) if "Azure Networking Deep Dive" in ln)
    assert networking_idx == azure_idx + 1  # inserted right after (later date)


def test_add_course_before_existing_row(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="Azure Basics Primer",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 05, 2026",
                duration="1h 0m",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    lines = _md_text(fixture_root).split("\n")
    primer_idx = next(i for i, ln in enumerate(lines) if "Azure Basics Primer" in ln)
    fundamentals_idx = next(i for i, ln in enumerate(lines) if "Azure Fundamentals" in ln)
    assert primer_idx < fundamentals_idx  # earlier date comes first


def test_add_course_bumps_section_and_completed_headings(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="New Course",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    text = _md_text(fixture_root)
    assert "### ☁️ Microsoft Azure (2 Courses · 1 Labs)" in text
    assert "## ✅ Completed Courses (3 Courses · 1 Labs)" in text


def test_add_lab_to_existing_labs_table(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="Second Azure Lab",
                type="Lab",
                section="☁️ Microsoft Azure",
                completed_date="Jan 16, 2026",
                duration="—",
                timing_profile="Lab",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    text = _md_text(fixture_root)
    assert "### ☁️ Microsoft Azure (1 Courses · 2 Labs)" in text
    lines = text.split("\n")
    plain_idx = next(i for i, ln in enumerate(lines) if "Plain Text Lab Title" in ln)
    second_idx = next(i for i, ln in enumerate(lines) if "Second Azure Lab" in ln)
    assert second_idx == plain_idx + 1


def test_add_lab_creates_new_labs_table(m, fixture_root):
    rc = m._run(
        fixture_root,
        [
            m.Entry(
                title="First .NET Lab",
                type="Lab",
                section="🔷 ASP.NET Core & .NET",
                completed_date="Feb 10, 2026",
                duration="—",
                timing_profile="Lab",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    assert rc == 0
    text = _md_text(fixture_root)
    assert "**🔷 ASP.NET Core & .NET Labs**" in text
    assert "First .NET Lab" in text
    assert "### 🔷 ASP.NET Core & .NET (1 Courses · 1 Labs)" in text


def test_add_without_url_renders_plain_title(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="No Link Course",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
                url=None,
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    text = _md_text(fixture_root)
    assert "| No Link Course | Jan 20, 2026 | 1h | Full Course |" in text


def test_duplicate_title_rejected(m, fixture_root, capsys):
    rc = m._run(
        fixture_root,
        [
            m.Entry(
                title="Azure Fundamentals",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    assert rc == 1
    assert "already exists" in capsys.readouterr().err
    assert _md_text(fixture_root) == FIXTURE_MD  # untouched


def test_section_not_found_lists_valid_sections(m, fixture_root, capsys):
    rc = m._run(
        fixture_root,
        [
            m.Entry(
                title="Something New",
                type="Course",
                section="🐍 Python 3",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found" in err
    assert "☁️ Microsoft Azure" in err


def test_dry_run_writes_nothing(m, fixture_root, capsys):
    rc = m._run(
        fixture_root,
        [
            m.Entry(
                title="Should Not Persist",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=True,
    )
    assert rc == 0
    assert "[DRY RUN]" in capsys.readouterr().out
    assert _md_text(fixture_root) == FIXTURE_MD


def test_status_totals_and_last_updated_lines_updated(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="New Course",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "Sarah completed a new course.",
        "Sep 10, 2026",
        dry_run=False,
    )
    text = _md_text(fixture_root)
    assert (
        "**Status:** 3 courses completed | 0 courses in progress | 1 labs (1 completed, 0 in progress)"
        in text
    )
    assert "**Totals:** 3 courses · 1 labs" in text
    assert "**Last updated:** Sep 10, 2026 (Sarah completed a new course.)" in text


def test_summary_table_bumped_for_section_and_total(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="New Course",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    lines = _md_text(fixture_root).split("\n")
    azure_row = next(ln for ln in lines if ln.startswith("| ☁️ Microsoft Azure |"))
    total_row = next(ln for ln in lines if ln.startswith("| **TOTAL** |"))
    assert azure_row == "| ☁️ Microsoft Azure | 2 | 1 | 0 | 0 |"
    assert total_row == "| **TOTAL** | **3** | **1** | **0** | **0** |"


def test_add_batch_two_entries_same_section(m, fixture_root):
    entries = [
        m.Entry(
            title="Batch Course One",
            type="Course",
            section="☁️ Microsoft Azure",
            completed_date="Jan 20, 2026",
            duration="1h",
            timing_profile="Full Course",
        ),
        m.Entry(
            title="Batch Course Two",
            type="Course",
            section="☁️ Microsoft Azure",
            completed_date="Jan 21, 2026",
            duration="1h",
            timing_profile="Full Course",
        ),
    ]
    rc = m._run(fixture_root, entries, "Two new Azure courses.", "Sep 10, 2026", dry_run=False)
    assert rc == 0
    text = _md_text(fixture_root)
    assert "### ☁️ Microsoft Azure (3 Courses · 1 Labs)" in text
    azure_row = next(ln for ln in text.split("\n") if ln.startswith("| ☁️ Microsoft Azure |"))
    assert azure_row == "| ☁️ Microsoft Azure | 3 | 1 | 0 | 0 |"


def test_add_batch_rejects_intra_batch_duplicate(m, fixture_root, tmp_path, capsys):
    entries_file = tmp_path / "batch.json"
    entries_file.write_text(
        json.dumps(
            [
                {
                    "title": "Same Title",
                    "type": "Course",
                    "section": "☁️ Microsoft Azure",
                    "completed_date": "Jan 20, 2026",
                    "duration": "1h",
                    "timing_profile": "Full Course",
                },
                {
                    "title": "Same Title",
                    "type": "Course",
                    "section": "☁️ Microsoft Azure",
                    "completed_date": "Jan 21, 2026",
                    "duration": "1h",
                    "timing_profile": "Full Course",
                },
            ]
        ),
        encoding="utf-8",
    )
    import argparse

    args = argparse.Namespace(
        root=fixture_root,
        entries_file=entries_file,
        note="note",
        updated_date="Sep 10, 2026",
        dry_run=False,
    )
    rc = m.cmd_add_batch(args)
    assert rc == 1
    assert "duplicate title" in capsys.readouterr().err


def test_unparseable_date_is_hard_error(m, fixture_root, capsys):
    rc = m._run(
        fixture_root,
        [
            m.Entry(
                title="Bad Date Course",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="2026-01-20",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err


def test_missing_file_reports_error(m, tmp_path, capsys):
    rc = m._run(
        tmp_path,
        [
            m.Entry(
                title="X",
                type="Course",
                section="Y",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err


def test_writes_backup_file(m, fixture_root):
    m._run(
        fixture_root,
        [
            m.Entry(
                title="New Course",
                type="Course",
                section="☁️ Microsoft Azure",
                completed_date="Jan 20, 2026",
                duration="1h",
                timing_profile="Full Course",
            )
        ],
        "note",
        "Sep 10, 2026",
        dry_run=False,
    )
    backup = (
        fixture_root / "project-2-profile-learning-hub" / "outputs" / "pluralsight-courses.md.bak"
    )
    assert backup.is_file()
    assert backup.read_text(encoding="utf-8") == FIXTURE_MD


def test_main_add_via_cli_args(m, fixture_root):
    rc = m.main(
        [
            "--root",
            str(fixture_root),
            "add",
            "--title",
            "CLI Course",
            "--type",
            "Course",
            "--section",
            "☁️ Microsoft Azure",
            "--completed-date",
            "Jan 20, 2026",
            "--duration",
            "1h",
            "--timing-profile",
            "Full Course",
            "--note",
            "via cli",
            "--updated-date",
            "Sep 10, 2026",
        ]
    )
    assert rc == 0
    assert "CLI Course" in _md_text(fixture_root)
