"""Unit tests for the cold-call letter generator's evidence grounding."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from docx import Document

REPO_ROOT = Path(__file__).resolve().parents[1]

from project_1_application_engine.skills.cold_outreach_recruiter_letter.scripts.generate_cold_call_letter import (
    _empty_fit_result,
    _read_target_description,
    _select_evidence,
    generate_cold_call_letter,
)


def _make_bundle(
    *,
    differentiators: list[str] | None = None,
    technical_skills: list[tuple[str, list[str]]] | None = None,
    portfolio_projects: list[dict[str, Any]] | None = None,
) -> Any:
    """Build a minimal namespace bundle for testing."""
    headline = "Full-Stack Engineer"
    technical_skills = technical_skills or []
    return SimpleNamespace(
        headline=headline,
        bundle_version=1,
        generated="2026-08-20",
        differentiators=differentiators or [],
        resume=SimpleNamespace(
            headline=headline,
            technical_skills=[
                SimpleNamespace(category=cat, skills=skills) for cat, skills in technical_skills
            ],
        ),
        portfolio_projects=[
            SimpleNamespace(
                name=p.get("name", ""),
                description=p.get("description", ""),
                stack=p.get("stack", []),
            )
            for p in (portfolio_projects or [])
        ],
        contact=SimpleNamespace(
            name="Sarah Ashford",
            email="andrea@example.com",
            phone="",
            linkedin="",
            github="",
            location="",
            pluralsight="",
        ),
    )


def test_select_evidence_uses_differentiators_and_portfolio() -> None:
    bundle = _make_bundle(
        differentiators=[
            "Full-stack depth: built SPAs and APIs end to end",
            "Cloud-native with Azure",
        ],
        portfolio_projects=[
            {"name": "OldApp", "description": "A movie catalog", "stack": ["React", "Node"]}
        ],
    )
    evidence = _select_evidence(bundle, "Acme")

    assert "Acme" in evidence["hook"]
    assert "Full-stack depth" in evidence["hook"]
    assert len(evidence["bring"]) == 2
    assert evidence["bring"][0]["label"] == "Full-stack depth"
    assert "OldApp" in evidence["portfolio_highlight"]
    assert "evidence_sources" in evidence
    assert "OldApp" in evidence["evidence_sources"]
    assert not evidence["low_confidence"]


def test_select_evidence_falls_back_when_sparse() -> None:
    bundle = _make_bundle(
        technical_skills=[("Languages", ["Python", "TypeScript"])],
    )
    evidence = _select_evidence(bundle, "Acme")

    assert "interesting" in evidence["hook"] or "strong match" in evidence["hook"]
    assert len(evidence["bring"]) == 1
    assert "Background includes" in evidence["bring"][0]["body"]
    assert "Hands-on with" not in evidence["bring"][0]["body"]
    assert evidence["low_confidence"]


def test_empty_fit_result_is_stretch_with_no_matches() -> None:
    result = _empty_fit_result()
    assert result.rating == "Stretch"
    assert result.required == []
    assert result.nice_to_have == []


def test_generate_cold_call_letter_writes_sidecar(tmp_path: Path) -> None:
    bundle = _make_bundle(
        differentiators=["Full-stack depth: built SPAs and APIs end to end"],
        portfolio_projects=[
            {"name": "OldApp", "description": "A movie catalog", "stack": ["React", "Node"]}
        ],
    )
    jd_path = tmp_path / "target.md"
    jd_path.write_text("# About Acme\n\nAcme builds cloud software.", encoding="utf-8")

    out_path, sidecar_path, result = generate_cold_call_letter(
        jd_path,
        bundle=bundle,
        company="Acme",
        out_path=tmp_path / "cold.docx",
        root=tmp_path,
    )

    assert out_path.exists()
    assert sidecar_path.exists()
    meta = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert meta["script"] == "generate_cold_call_letter.py"
    assert "OldApp" in meta["evidence_sources"]
    assert meta["warnings"] == []


def test_generate_cold_call_letter_warns_when_low_confidence(capsys, tmp_path: Path) -> None:
    bundle = _make_bundle(technical_skills=[("Languages", ["Python"])])
    jd_path = tmp_path / "target.md"
    jd_path.write_text("# About Acme\n\nAcme builds cloud software.", encoding="utf-8")

    generate_cold_call_letter(
        jd_path,
        bundle=bundle,
        company="Acme",
        out_path=tmp_path / "cold.docx",
        root=tmp_path,
    )

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "low evidence" in captured.err.lower() or "manually review" in captured.err.lower()


# ── No-JD conversational flow (Phase 3: input-model fix) ────────────────────


def test_read_target_description_with_no_path_defaults_gracefully() -> None:
    company, description = _read_target_description(None)
    assert company == "Your Company"
    assert description == ""


def test_select_evidence_includes_role_type_in_hook() -> None:
    bundle = _make_bundle(
        differentiators=["Full-stack depth: built SPAs and APIs end to end"],
    )
    evidence = _select_evidence(bundle, "Acme", role_type="Senior .NET Developer roles")
    assert "Senior .NET Developer roles" in evidence["hook"]


def test_select_evidence_omits_role_clause_when_not_given() -> None:
    bundle = _make_bundle(differentiators=["Full-stack depth"])
    evidence = _select_evidence(bundle, "Acme")
    assert "roles" not in evidence["hook"].lower()


def _docx_text(path: Path) -> str:
    return "\n".join(p.text for p in Document(str(path)).paragraphs)


def test_generate_cold_call_letter_without_jd_uses_recruiter_and_role_type(
    tmp_path: Path,
) -> None:
    """The core Phase 3 fix: no JD file needed — recruiter_name/role_type
    drive the salutation, Re: line, and hook directly."""
    bundle = _make_bundle(
        differentiators=["Full-stack depth: built SPAs and APIs end to end"],
    )

    out_path, sidecar_path, result = generate_cold_call_letter(
        None,
        bundle=bundle,
        company="Acme",
        recruiter_name="Jane Doe",
        role_type="Senior .NET Developer roles",
        out_path=tmp_path / "cold.docx",
        root=tmp_path,
    )

    assert out_path.exists()
    text = _docx_text(out_path)
    assert "Dear Jane Doe," in text
    assert "Re: Senior .NET Developer roles Opportunities" in text
    assert "Senior .NET Developer roles" in text
    # No JD parsed -> no required skills -> the honest "Stretch, not assessed" default.
    assert result.rationale == "No JD provided — fit not assessed."


def test_generate_cold_call_letter_without_recruiter_name_defaults_to_hiring_team(
    tmp_path: Path,
) -> None:
    bundle = _make_bundle(differentiators=["Full-stack depth"])
    out_path, _, _ = generate_cold_call_letter(
        None,
        bundle=bundle,
        company="Acme",
        out_path=tmp_path / "cold.docx",
        root=tmp_path,
    )
    text = _docx_text(out_path)
    assert "Dear Hiring Team," in text
