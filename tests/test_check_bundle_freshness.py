"""Tests for project-2-profile-learning-hub/scripts/check_bundle_freshness.py.

The module lives under scripts/, outside the installed package tree, so it's
loaded by file path rather than imported by dotted name (same pattern as
test_render_md_bundles.py).
"""

from __future__ import annotations

import importlib.util
import os
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "project-2-profile-learning-hub" / "scripts" / "check_bundle_freshness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_bundle_freshness", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def m():
    return _load_module()


def _touch(path: Path, when: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("content", encoding="utf-8")
    os.utime(path, (when, when))


def _setup_repo(tmp_path: Path, *, bundle_mtime: float, source_mtimes: dict[str, float]) -> Path:
    p2 = tmp_path / "project-2-profile-learning-hub"
    for name, mtime in source_mtimes.items():
        _touch(p2 / name, mtime)
    p1 = tmp_path / "project-1-application-engine"
    _touch(p1 / "app-engine-bundle.md", bundle_mtime)
    return tmp_path


def test_fresh_when_bundle_newer_than_all_sources(m, tmp_path):
    now = time.time()
    root = _setup_repo(
        tmp_path,
        bundle_mtime=now,
        source_mtimes={
            "profile-facts.md": now - 100,
            "Resume_Snapshot.md": now - 100,
            "skills-summary.md": now - 100,
            "github-repos.md": now - 100,
        },
    )
    result = m.check_bundle_freshness(
        root, "project-1-application-engine/app-engine-bundle.md", "app-engine-bundle.md"
    )
    assert result.status == "FRESH"


def test_stale_when_a_source_is_newer_than_bundle(m, tmp_path):
    now = time.time()
    root = _setup_repo(
        tmp_path,
        bundle_mtime=now - 100,
        source_mtimes={
            "profile-facts.md": now,  # edited after the bundle was written
            "Resume_Snapshot.md": now - 200,
            "skills-summary.md": now - 200,
            "github-repos.md": now - 200,
        },
    )
    result = m.check_bundle_freshness(
        root, "project-1-application-engine/app-engine-bundle.md", "app-engine-bundle.md"
    )
    assert result.status == "STALE"
    assert any("profile-facts.md" in d for d in result.details)


def test_skip_when_bundle_not_generated_yet(m, tmp_path):
    result = m.check_bundle_freshness(
        tmp_path, "project-1-application-engine/app-engine-bundle.md", "app-engine-bundle.md"
    )
    assert result.status == "SKIP"


def test_main_returns_zero_when_no_bundles_present(m, tmp_path, capsys):
    rc = m.main([str(tmp_path)])
    assert rc == 0
    assert "All present bundles are fresh" in capsys.readouterr().out


def test_main_returns_nonzero_when_a_bundle_is_stale(m, tmp_path, capsys):
    now = time.time()
    p1 = tmp_path / "project-1-application-engine"
    _touch(p1 / "app-engine-bundle.md", now - 100)
    p2 = tmp_path / "project-2-profile-learning-hub"
    _touch(p2 / "profile-facts.md", now)

    rc = m.main([str(tmp_path)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "[STALE]" in out
    assert "1 bundle(s) stale" in out
