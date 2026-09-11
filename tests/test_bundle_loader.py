"""Tests for shared/bundle_loader.py jsonschema validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.bundle_loader import BundleSchemaError, load_presence_bundle, load_profile_bundle


def _minimal_profile_bundle() -> dict:
    return {
        "bundle_version": 1,
        "generated": "2026-08-20",
        "sources": {},
        "contact": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "204-555-1212",
        },
        "headline": "Senior Dev",
        "summary": "Summary text",
        "cert_registry": [
            {
                "code": "AZ-900",
                "status": "certified",
                "date": "2026-04-18",
                "credential_url": None,
                "notes": None,
            },
        ],
        "differentiators": ["Full-stack depth"],
        "known_genuine_gaps": [],
        "resolved_framing_gaps": [],
        "portfolio_projects": [
            {
                "name": "Test Repo",
                "url": "https://example.com",
                "stack": ["C#"],
                "description": "Test",
                "skills_evidence": [],
            }
        ],
        "ats_keywords": {},
        "ai200_domain_coverage": [],
        "resume": {
            "headline": "Senior Dev",
            "summary": "x",
            "technical_skills": [],
            "experience": [],
        },
    }


def _minimal_presence_bundle() -> dict:
    return {
        "bundle_version": 1,
        "generated": "2026-08-20",
        "headline": "Senior Dev",
        "summary": "Public summary",
        "cert_registry": [
            {
                "code": "AZ-900",
                "status": "certified",
                "date": "2026-04-18",
                "credential_url": None,
                "notes": None,
            }
        ],
        "technical_skills": {},
        "portfolio_projects": [
            {
                "name": "Test Repo",
                "url": "https://example.com",
                "stack": ["C#"],
                "description": "Test",
            }
        ],
        "differentiators": [],
    }


def test_load_profile_bundle_accepts_valid_data(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(_minimal_profile_bundle()))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "presence-bundle.json").write_text(
        json.dumps(_minimal_presence_bundle())
    )
    bundle = load_profile_bundle(tmp_path)
    assert bundle.bundle_version == 1
    assert bundle.contact.name == "Test User"


def test_load_profile_bundle_star_story_adapt_when_round_trips(tmp_path: Path) -> None:
    data = _minimal_profile_bundle()
    data["resume"]["star_stories"] = [
        {
            "title": "Test Story",
            "jd_tags": ["sql"],
            "situation": "S",
            "task": "T",
            "action": "A",
            "result": "R",
            "adapt_when": ["Role emphasizes Python — mention the analytical approach"],
        }
    ]
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(data))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "presence-bundle.json").write_text(
        json.dumps(_minimal_presence_bundle())
    )
    bundle = load_profile_bundle(tmp_path)
    assert bundle.resume.star_stories[0].adapt_when == [
        "Role emphasizes Python — mention the analytical approach"
    ]


def test_load_profile_bundle_rejects_missing_bundle_version(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    bad = _minimal_profile_bundle()
    del bad["bundle_version"]
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(bad))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "presence-bundle.json").write_text(
        json.dumps(_minimal_presence_bundle())
    )
    with pytest.raises(BundleSchemaError):
        load_profile_bundle(tmp_path)


def test_load_profile_bundle_rejects_wrong_type_for_bundle_version(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    bad = _minimal_profile_bundle()
    bad["bundle_version"] = "one"  # string, not int
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(bad))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "presence-bundle.json").write_text(
        json.dumps(_minimal_presence_bundle())
    )
    with pytest.raises(BundleSchemaError):
        load_profile_bundle(tmp_path)


def test_load_profile_bundle_rejects_bad_date_format(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    bad = _minimal_profile_bundle()
    bad["generated"] = "yesterday"
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(bad))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "presence-bundle.json").write_text(
        json.dumps(_minimal_presence_bundle())
    )
    with pytest.raises(BundleSchemaError):
        load_profile_bundle(tmp_path)


def test_load_presence_bundle_rejects_az204_cert(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    bad = _minimal_presence_bundle()
    bad["cert_registry"] = [
        {
            "code": "AZ-204",
            "status": "not_pursuing",
            "date": None,
            "credential_url": None,
            "notes": None,
        }
    ]
    (tmp_path / "outputs" / "presence-bundle.json").write_text(json.dumps(bad))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(_minimal_profile_bundle()))
    with pytest.raises(BundleSchemaError):
        load_presence_bundle(tmp_path)


def test_load_presence_bundle_rejects_extra_pii_fields(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    bad = _minimal_presence_bundle()
    bad["cert_registry"][0]["email"] = "leak@example.com"
    (tmp_path / "outputs" / "presence-bundle.json").write_text(json.dumps(bad))
    (tmp_path / "README.md").write_text("# x")
    (tmp_path / "outputs" / "profile-bundle.json").write_text(json.dumps(_minimal_profile_bundle()))
    with pytest.raises(BundleSchemaError):
        load_presence_bundle(tmp_path)
