"""Tests for project-1-application-engine/skills/gap_analysis_job_description/scripts/gap_analysis.py.

The module lives outside the installed package tree (its dir name doesn't
follow the `skills.<name>` package convention cleanly for dotted import in
tests elsewhere in this repo), so it's loaded by file path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from shared.fit_engine import FitResult, SkillMatch

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = (
    ROOT
    / "project-1-application-engine"
    / "skills"
    / "gap_analysis_job_description"
    / "scripts"
    / "gap_analysis.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("gap_analysis", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def g():
    return _load_module()


def test_format_header_meta_omits_absent_parts(g):
    assert g._format_header_meta("Contoso", None, None) == "Contoso"
    assert g._format_header_meta("Contoso", "Remote", None) == "Contoso — Remote"
    assert g._format_header_meta("Contoso", None, "REQ-1") == "Contoso — REQ-1"
    assert g._format_header_meta("Contoso", "Remote", "REQ-1") == "Contoso — Remote · REQ-1"


def test_render_report_header_includes_location_and_job_id(g):
    result = FitResult(rating="Strong", required=[], nice_to_have=[], rationale="")
    report = g._render_report("Backend Dev", "Contoso", result, "Remote", "REQ-1")
    assert "**Contoso — Remote · REQ-1**" in report


def test_render_report_header_omits_location_and_job_id_gracefully(g):
    result = FitResult(rating="Strong", required=[], nice_to_have=[], rationale="")
    report = g._render_report("Backend Dev", "Contoso", result)
    assert "**Contoso**" in report
    assert " — " not in report.splitlines()[1]


def test_how_to_frame_the_application_differs_across_skill_sets(g):
    """The old version emitted identical boilerplate for every job; this must
    now be genuinely per-application content."""
    result_a = FitResult(
        rating="Strong",
        required=[
            SkillMatch("Azure", "match", "Contoso: production"),
            SkillMatch("Kubernetes", "gap", "no evidence"),
        ],
        nice_to_have=[],
        rationale="",
    )
    result_b = FitResult(
        rating="Good",
        required=[
            SkillMatch("Python", "course", "coursework or self-study"),
            SkillMatch("React", "portfolio", "Demo: portfolio"),
        ],
        nice_to_have=[SkillMatch("GraphQL", "portfolio", "Demo: portfolio")],
        rationale="",
    )
    report_a = g._render_report("Role A", "Company A", result_a)
    report_b = g._render_report("Role B", "Company B", result_b)

    def _how_to_frame(report: str) -> str:
        return report.split("## How to Frame the Application")[1]

    frame_a = _how_to_frame(report_a)
    frame_b = _how_to_frame(report_b)
    assert frame_a != frame_b
    assert "Azure" in frame_a
    assert "Kubernetes" in frame_a
    assert "Python" in frame_b or "React" in frame_b


def test_resume_tailoring_priorities_name_actual_skills_not_boilerplate(g):
    recs = {
        "close_with_portfolio": ["Kubernetes"],
        "close_with_course": ["Python"],
        "position_as_nice_to_have": ["GraphQL"],
    }
    result = FitResult(
        rating="Good",
        required=[
            SkillMatch("Azure", "match", "Contoso: production"),
            SkillMatch("Python", "course", "coursework or self-study"),
            SkillMatch("Kubernetes", "gap", "no evidence"),
        ],
        nice_to_have=[SkillMatch("GraphQL", "portfolio", "Demo: portfolio")],
        rationale="",
    )
    actions = g._resume_tailoring_priorities(result, recs)
    joined = " ".join(actions)
    assert "Azure" in joined
    assert "Python" in joined
    assert "Kubernetes" in joined
    assert "GraphQL" in joined
    # No leftover fixed boilerplate from the old version.
    assert "Lead with production evidence that maps to required skills." not in actions


def test_cover_letter_angle_uses_matched_skill_and_evidence_sources_not_fixed_template(g):
    result = FitResult(
        rating="Strong",
        required=[SkillMatch("Azure", "match", "Contoso: production")],
        nice_to_have=[],
        rationale="",
    )
    angle = g._cover_letter_angle("Contoso", result)
    assert "Azure" in angle
    assert "Contoso" in angle
    # No leftover fixed boilerplate sentence from the old version.
    assert "2–3 proof points from production or portfolio work" not in angle
