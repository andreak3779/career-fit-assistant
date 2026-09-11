"""Tests for project-2-profile-learning-hub/scripts/update_learning_history.py.

Same pattern as test_query_learning_history.py: loaded by file path, all tests
point --root at a tmp_path fixture — never at the real repo, since this script
writes to data/pluralsight_learning_history.json.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "project-2-profile-learning-hub" / "scripts" / "update_learning_history.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("update_learning_history", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def u():
    return _load_module()


def _entry(name, **overrides):
    base = {
        "name": name,
        "type": "Course",
        "url": f"https://app.pluralsight.com/library/courses/{name.lower().replace(' ', '-')}",
        "view_time": "1h",
        "progress": None,
        "duration": "1h",
        "completion_percentage": "100.0%",
        "completed_date": "Jul 04, 2026",
        "timing_profile": "Full Course",
    }
    base.update(overrides)
    return base


@pytest.fixture
def fixture_root(tmp_path):
    data_dir = tmp_path / "project-2-profile-learning-hub" / "data"
    data_dir.mkdir(parents=True)
    entries = [
        _entry("Advanced Claude Code", summary="Existing summary."),
        _entry("Claude Code in Practice", summary=""),
        _entry("Redis Fundamentals", type="Lab", summary=None),
    ]
    (data_dir / "pluralsight_learning_history.json").write_text(
        json.dumps(entries, indent=2), encoding="utf-8"
    )
    return tmp_path


def _write_summaries(tmp_path, mapping):
    path = tmp_path / "batch-summaries.json"
    path.write_text(json.dumps(mapping), encoding="utf-8")
    return path


def _load_entries(fixture_root):
    path = (
        fixture_root
        / "project-2-profile-learning-hub"
        / "data"
        / "pluralsight_learning_history.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_apply_adds_new_summary(u, fixture_root, tmp_path, capsys):
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": "Covers Redis basics."})
    rc = u.cmd_apply(fixture_root, batch, dry_run=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "+ added" in out
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Redis Fundamentals"]["summary"] == "Covers Redis basics."


def test_apply_updates_existing_summary(u, fixture_root, tmp_path, capsys):
    batch = _write_summaries(tmp_path, {"Advanced Claude Code": "Rewritten summary."})
    rc = u.cmd_apply(fixture_root, batch, dry_run=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "~ updated" in out
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Advanced Claude Code"]["summary"] == "Rewritten summary."


def test_apply_is_case_and_whitespace_insensitive(u, fixture_root, tmp_path):
    batch = _write_summaries(tmp_path, {"  redis   fundamentals  ": "Matched despite casing."})
    rc = u.cmd_apply(fixture_root, batch, dry_run=False)
    assert rc == 0
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Redis Fundamentals"]["summary"] == "Matched despite casing."


def test_apply_partial_batch_one_typo_does_not_block_others(u, fixture_root, tmp_path, capsys):
    batch = _write_summaries(
        tmp_path,
        {
            "Redis Fundamentals": "Covers Redis basics.",
            "Kubernetes Depoyment Basics": "Typo — should not match.",
        },
    )
    rc = u.cmd_apply(fixture_root, batch, dry_run=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "NOT FOUND (1)" in out
    assert "Kubernetes Depoyment Basics" in out
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Redis Fundamentals"]["summary"] == "Covers Redis basics."


def test_apply_dry_run_writes_nothing(u, fixture_root, tmp_path, capsys):
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": "Should not be written."})
    rc = u.cmd_apply(fixture_root, batch, dry_run=True)
    assert rc == 0
    assert "[DRY RUN]" in capsys.readouterr().out
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Redis Fundamentals"]["summary"] is None


def test_apply_rejects_empty_summary_value(u, fixture_root, tmp_path, capsys):
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": ""})
    rc = u.cmd_apply(fixture_root, batch, dry_run=False)
    assert rc == 1  # nothing applied
    err = capsys.readouterr().err
    assert "REJECTED" in err
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Redis Fundamentals"]["summary"] is None


def test_apply_zero_matches_returns_nonzero(u, fixture_root, tmp_path):
    batch = _write_summaries(tmp_path, {"Totally Made Up Course": "No match."})
    rc = u.cmd_apply(fixture_root, batch, dry_run=False)
    assert rc == 1


def test_apply_invalid_summaries_file_shape_reports_error(u, fixture_root, tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(["not", "a", "flat", "object"]), encoding="utf-8")
    rc = u.cmd_apply(fixture_root, path, dry_run=False)
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err


def test_apply_missing_summaries_file_reports_error(u, fixture_root, tmp_path, capsys):
    rc = u.cmd_apply(fixture_root, tmp_path / "does-not-exist.json", dry_run=False)
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err


def test_apply_missing_json_file_reports_error(u, tmp_path, capsys):
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": "x"})
    rc = u.cmd_apply(tmp_path, batch, dry_run=False)
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err


def test_apply_writes_backup_file(u, fixture_root, tmp_path):
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": "Covers Redis basics."})
    u.cmd_apply(fixture_root, batch, dry_run=False)
    backup = (
        fixture_root
        / "project-2-profile-learning-hub"
        / "outputs"
        / "pluralsight_learning_history.json.bak"
    )
    assert backup.is_file()


def test_apply_preserves_other_entries_untouched(u, fixture_root, tmp_path):
    before = _load_entries(fixture_root)
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": "Covers Redis basics."})
    u.cmd_apply(fixture_root, batch, dry_run=False)
    after = {e["name"]: e for e in _load_entries(fixture_root)}
    untouched = next(e for e in before if e["name"] == "Advanced Claude Code")
    assert after["Advanced Claude Code"] == untouched


def test_main_apply_via_cli_args(u, fixture_root, tmp_path):
    batch = _write_summaries(tmp_path, {"Redis Fundamentals": "Via CLI."})
    rc = u.main(["--root", str(fixture_root), "apply", "--summaries-file", str(batch)])
    assert rc == 0
    entries = {e["name"]: e for e in _load_entries(fixture_root)}
    assert entries["Redis Fundamentals"]["summary"] == "Via CLI."
