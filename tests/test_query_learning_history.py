"""Tests for project-2-profile-learning-hub/scripts/query_learning_history.py.

The module lives under scripts/, outside the installed package tree, so it's
loaded by file path (same pattern as the other project-2 script tests). All
tests point --root at a tmp_path fixture — never at the real repo — since the
whole point of this script is safe, narrow access to the real learning
history without an LLM (or a test) needing to read the whole file.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "project-2-profile-learning-hub" / "scripts" / "query_learning_history.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("query_learning_history", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def q():
    return _load_module()


@pytest.fixture
def fixture_root(tmp_path):
    data_dir = tmp_path / "project-2-profile-learning-hub" / "data"
    data_dir.mkdir(parents=True)
    entries = [
        {
            "name": "Advanced Claude Code",
            "type": "Course",
            "url": "https://app.pluralsight.com/library/courses/advanced-claude-code",
            "view_time": "1h 52m",
            "progress": "1h 27m",
            "duration": "1h 27m",
            "completion_percentage": "100.0%",
            "completed_date": "Jul 04, 2026",
            "timing_profile": "Full Course",
            "summary": "Covers advanced Claude Code techniques.",
        },
        {
            "name": "Claude Code in Practice",
            "type": "Course",
            "url": "https://app.pluralsight.com/library/courses/claude-code-in-practice",
            "view_time": "45m",
            "progress": None,
            "duration": None,
            "completion_percentage": "100.0%",
            "completed_date": "Jun 01, 2026",
            "timing_profile": "Short Course",
            "summary": "",  # missing
        },
        {
            "name": "Redis Fundamentals",
            "type": "Lab",
            "url": "https://app.pluralsight.com/ilx/redis-fundamentals",
            "view_time": "30m",
            "progress": None,
            "duration": "30m",
            "completion_percentage": "100.0%",
            "completed_date": "May 15, 2026",
            "timing_profile": "Full Lab",
            "summary": None,  # missing
        },
    ]
    (data_dir / "pluralsight_learning_history.json").write_text(
        json.dumps(entries), encoding="utf-8"
    )
    return tmp_path


def test_lookup_exact_match(q, fixture_root, capsys):
    rc = q.cmd_lookup(fixture_root, ["Advanced Claude Code"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "duration=1h 27m" in out
    assert "timing_profile=Full Course" in out


def test_lookup_is_case_and_whitespace_insensitive(q, fixture_root, capsys):
    rc = q.cmd_lookup(fixture_root, ["  advanced   claude code  "])
    assert rc == 0
    assert "Advanced Claude Code" in capsys.readouterr().out


def test_lookup_ambiguous_substring_lists_candidates(q, fixture_root, capsys):
    rc = q.cmd_lookup(fixture_root, ["Claude Code"])
    assert rc == 1  # nothing definitively found
    out = capsys.readouterr().out
    assert "2 possible matches" in out
    assert "Advanced Claude Code" in out
    assert "Claude Code in Practice" in out


def test_lookup_not_found_suggests_web_search(q, fixture_root, capsys):
    rc = q.cmd_lookup(fixture_root, ["Totally Made Up Course"])
    assert rc == 1
    out = capsys.readouterr().out
    assert "NOT FOUND" in out
    assert "web_search" in out


def test_lookup_multiple_names_mixed_results(q, fixture_root, capsys):
    rc = q.cmd_lookup(fixture_root, ["Advanced Claude Code", "Nonexistent Course"])
    assert rc == 0  # at least one found
    out = capsys.readouterr().out
    assert "duration=1h 27m" in out
    assert "NOT FOUND" in out


def test_list_omits_summary_and_url(q, fixture_root, capsys):
    rc = q.cmd_list(fixture_root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "3 entries" in out
    assert "Redis Fundamentals" in out
    assert "app.pluralsight.com" not in out  # url field excluded
    assert "Covers advanced" not in out  # summary field excluded


def test_missing_summary_finds_empty_and_null(q, fixture_root, capsys):
    rc = q.cmd_missing_summary(fixture_root)
    assert rc == 0
    out = capsys.readouterr().out
    assert "2 of 3 entries missing a summary" in out
    assert "Claude Code in Practice" in out
    assert "Redis Fundamentals" in out
    assert "Advanced Claude Code" not in out  # this one has a summary


def test_main_lookup_via_cli_args(q, fixture_root, capsys):
    rc = q.main(["--root", str(fixture_root), "lookup", "Redis Fundamentals"])
    assert rc == 0
    assert "timing_profile=Full Lab" in capsys.readouterr().out


def test_main_missing_json_file_returns_nonzero(q, tmp_path, capsys):
    rc = q.main(["--root", str(tmp_path), "list"])
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err
