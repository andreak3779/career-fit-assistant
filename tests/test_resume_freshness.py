"""Unit tests for shared/resume_freshness.py — the mtime-based resume
freshness check shared by the Jobgether and Indeed/ZipRecruiter profile-update
generators. Always points at a tmp_path root, never the real repo, since the
real resume DOCX lives in a gitignored outputs/ folder anyway.

The resume file is located by glob (`*_Resume_*.docx`) rather than a fixed
filename, since the platform resume's exact name is a local build artifact —
fixtures below use the repo's canonical `SarahAshford_Resume_*.docx` naming
convention (see project-1-application-engine/skills/fullstack_net_profile_resume)
but any name matching the glob would do.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from shared.resume_freshness import resume_freshness_lines

_RESUME_DIR_PARTS = ("project-1-application-engine", "outputs")
_RESUME_NAME = "SarahAshford_Resume_SeniorFullStackNET.docx"


def _write(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_missing_resume_reports_not_found(tmp_path: Path) -> None:
    lines = resume_freshness_lines(tmp_path)
    assert any("No resume file found" in line for line in lines)
    assert any("fullstack_net_profile_resume" in line for line in lines)


def test_fresh_resume_reports_current(tmp_path: Path) -> None:
    resume_path = tmp_path.joinpath(*_RESUME_DIR_PARTS, _RESUME_NAME)
    _write(tmp_path / "project-2-profile-learning-hub" / "profile-facts.md")
    _write(tmp_path / "project-2-profile-learning-hub" / "Resume_Snapshot.md")
    _write(tmp_path / "project-2-profile-learning-hub" / "skills-summary.md")
    # Resume written after the sources — filesystem mtime resolution can be
    # coarse, so nudge sources' mtimes into the past explicitly rather than
    # relying on write ordering alone.
    past = time.time() - 100
    for name in ("profile-facts.md", "Resume_Snapshot.md", "skills-summary.md"):
        p = tmp_path / "project-2-profile-learning-hub" / name
        os.utime(p, (past, past))
    _write(resume_path)

    lines = resume_freshness_lines(tmp_path)
    assert any("current" in line for line in lines)
    assert not any("STALE" in line for line in lines)


def test_stale_resume_reports_stale_sources(tmp_path: Path) -> None:
    resume_path = tmp_path.joinpath(*_RESUME_DIR_PARTS, _RESUME_NAME)
    _write(resume_path)
    past = time.time() - 100
    os.utime(resume_path, (past, past))

    _write(tmp_path / "project-2-profile-learning-hub" / "profile-facts.md")
    _write(tmp_path / "project-2-profile-learning-hub" / "Resume_Snapshot.md")
    _write(tmp_path / "project-2-profile-learning-hub" / "skills-summary.md")

    lines = resume_freshness_lines(tmp_path)
    assert any("STALE" in line for line in lines)
    assert any("profile-facts.md" in line for line in lines)
    assert any("Resume_Snapshot.md" in line for line in lines)
    assert any("skills-summary.md" in line for line in lines)


def test_missing_source_files_are_skipped_not_fatal(tmp_path: Path) -> None:
    resume_path = tmp_path.joinpath(*_RESUME_DIR_PARTS, _RESUME_NAME)
    _write(resume_path)
    # No project-2-profile-learning-hub directory at all.
    lines = resume_freshness_lines(tmp_path)
    assert any("current" in line for line in lines)


def test_picks_most_recent_match_when_multiple_resumes_present(tmp_path: Path) -> None:
    older = tmp_path.joinpath(*_RESUME_DIR_PARTS, "SarahAshford_Resume_Draft1.docx")
    newer = tmp_path.joinpath(*_RESUME_DIR_PARTS, "SarahAshford_Resume_SeniorFullStackNET.docx")
    _write(older)
    _write(newer)

    lines = resume_freshness_lines(tmp_path)
    assert any(newer.name in line for line in lines)
