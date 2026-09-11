"""Unit tests for Project 3 presence/identity generators."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

from project_3_presence_identity.skills.update_github_profile.scripts.generate_github import (
    _build_readme,
)
from project_3_presence_identity.skills.update_github_profile.scripts.generate_github import (
    _cert_summary as github_cert_summary,
)
from project_3_presence_identity.skills.update_github_profile.scripts.generate_github import (
    _is_sparse as github_is_sparse,
)
from project_3_presence_identity.skills.update_linkedin_profile.scripts.generate_linkedin import (
    _cert_summary,
    _headline,
    _is_sparse,
)


def _make_bundle(
    *,
    headline: str | None = None,
    summary: str | None = None,
    differentiators: list[str] | None = None,
    technical_skills: dict[str, list[str]] | None = None,
    portfolio_projects: list[dict[str, Any]] | None = None,
    cert_registry: list[dict[str, Any]] | None = None,
) -> Any:
    """Build a minimal presence bundle for testing."""
    return SimpleNamespace(
        bundle_version=1,
        generated="2026-08-20",
        headline=headline,
        summary=summary,
        differentiators=differentiators or [],
        technical_skills=technical_skills or {},
        portfolio_projects=[
            SimpleNamespace(
                name=p.get("name", ""),
                description=p.get("description", ""),
                stack=p.get("stack", []),
                url=p.get("url", ""),
            )
            for p in (portfolio_projects or [])
        ],
        cert_registry=[
            SimpleNamespace(code=c.get("code", ""), status=c.get("status", ""))
            for c in (cert_registry or [])
        ],
    )


def test_linkedin_headline_uses_bundle_headline() -> None:
    bundle = _make_bundle(headline="Cloud Engineer | .NET | Azure")
    assert _headline(bundle) == "Cloud Engineer | .NET | Azure"


def test_linkedin_headline_falls_back_to_summary() -> None:
    bundle = _make_bundle(summary="Engineering leader with cloud focus\nMore detail")
    assert _headline(bundle) == "Engineering leader with cloud focus | Engineering profile"
    assert "Azure" not in _headline(bundle)
    assert ".NET" not in _headline(bundle)


def test_linkedin_headline_falls_back_when_empty() -> None:
    bundle = _make_bundle()
    assert _headline(bundle) == "Engineering leader | Engineering profile"


def test_linkedin_is_sparse() -> None:
    assert _is_sparse(_make_bundle()) is True
    assert _is_sparse(_make_bundle(headline="H")) is False
    assert _is_sparse(_make_bundle(summary="S")) is False
    assert _is_sparse(_make_bundle(differentiators=["D"])) is False
    assert _is_sparse(_make_bundle(portfolio_projects=[{"name": "P"}])) is False


def test_linkedin_cert_summary_phrasing() -> None:
    bundle = _make_bundle(
        cert_registry=[
            {"code": "AZ-104", "status": "certified"},
            {"code": "AI-200", "status": "in_progress"},
        ]
    )
    summary = _cert_summary(bundle)
    assert "Certified: AZ-104" in summary
    assert "Preparing for: AI-200" in summary
    assert "In progress" not in summary


def _write_minimal_bundle(path: Path) -> None:
    minimal = {
        "bundle_version": 1,
        "generated": "2026-08-20",
        "headline": "",
        "summary": "",
        "cert_registry": [],
        "technical_skills": {},
        "portfolio_projects": [],
        "differentiators": [],
    }
    path.write_text(json.dumps(minimal), encoding="utf-8")


def test_github_is_sparse() -> None:
    assert github_is_sparse(_make_bundle()) is True
    assert github_is_sparse(_make_bundle(summary="S")) is False


def test_github_cert_summary_phrasing() -> None:
    bundle = _make_bundle(cert_registry=[{"code": "AI-200", "status": "in_progress"}])
    assert "Preparing for: AI-200" in github_cert_summary(bundle)
    assert "In progress" not in github_cert_summary(bundle)


def test_github_readme_uses_headline_when_no_summary() -> None:
    bundle = _make_bundle(headline="Backend Engineer")
    readme = _build_readme(bundle)
    assert "Backend Engineer" in readme
    assert "placeholder" not in readme


def test_github_readme_falls_back_to_placeholder() -> None:
    bundle = _make_bundle()
    readme = _build_readme(bundle)
    assert "Profile summary placeholder" in readme


def test_github_main_writes_sidecar_with_evidence(tmp_path: Path) -> None:
    import project_3_presence_identity.skills.update_github_profile.scripts.generate_github as github_module

    original_root = github_module.ROOT
    root = tmp_path / "project3"
    out_dir = root / "outputs"
    out_dir.mkdir(parents=True)

    _write_minimal_bundle(out_dir / "presence-bundle.json")

    github_module.ROOT = root
    try:
        out_file = out_dir / "GitHub_Readme.md"
        rc = github_module.main(["--out", str(out_file)])
        assert rc == 0
        assert out_file.exists()
        sidecar_path = out_file.with_suffix(out_file.suffix + ".meta.json")
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert sidecar["script"] == "generate_github.py"
        assert sidecar["evidence_sources"] == []
        assert any("sparse bundle" in w for w in sidecar["warnings"])
    finally:
        github_module.ROOT = original_root
