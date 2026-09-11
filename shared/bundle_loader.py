"""Load JSON bundles from the monorepo outputs directory."""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

import jsonschema

from shared.models import (
    Cert,
    CertStatus,
    Contact,
    Education,
    EvidenceLevel,
    Gap,
    GapSeverity,
    PresenceBundle,
    ProfileBundle,
    Project,
    Resume,
    SkillCategory,
    StarStory,
    WorkExperience,
)


class BundleSchemaError(Exception):
    """Raised when a bundle JSON fails schema validation."""


_SCHEMAS_DIR = Path(__file__).parent / "schemas"
_PROFILE_SCHEMA: dict[str, Any] = json.loads(
    (_SCHEMAS_DIR / "profile-bundle.schema.json").read_text(encoding="utf-8")
)
_PRESENCE_SCHEMA: dict[str, Any] = json.loads(
    (_SCHEMAS_DIR / "presence-bundle.schema.json").read_text(encoding="utf-8")
)


def _validate_schema(data: dict[str, Any], schema: dict[str, Any], bundle_name: str) -> None:
    try:
        # ``format=True`` enables format checking (e.g. ``format: date``) so a
        # bogus date string in a bundle is caught at validation time.
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        validator.validate(data)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(p) for p in exc.absolute_path) or "<root>"
        raise BundleSchemaError(
            f"{bundle_name} failed schema validation: {exc.message} at {path}"
        ) from exc


def _to_date(value: Any, *, field: str = "<unknown>") -> Any:
    """Parse an ISO date string. Returns ``None`` for empty or unparseable inputs.

    Bundle-level shape is enforced upstream by ``jsonschema`` validation; this
    helper only converts the validated ISO date string to ``datetime.date``.
    Silent type drift is no longer a concern because the schema rejects
    non-string, non-null, or non-ISO values before this function runs.
    """
    from datetime import date as _date
    from datetime import datetime as _datetime

    if value is None or value == "":
        return None
    if isinstance(value, _datetime):
        return value.date()
    try:
        return _date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        warnings.warn(f"Cannot parse date for {field}: {value!r} ({exc})", stacklevel=2)
        return None


def load_profile_bundle(root: Path | None = None) -> ProfileBundle:
    """Load ``outputs/profile-bundle.json`` into a typed ProfileBundle."""
    root = root or _find_repo_root()
    data = json.loads((root / "outputs" / "profile-bundle.json").read_text())
    _validate_schema(data, _PROFILE_SCHEMA, "profile-bundle.json")

    def cert_from_dict(c: dict[str, Any]) -> Cert:
        return Cert(
            code=c["code"],
            status=CertStatus(c["status"]),
            date=_to_date(c.get("date"), field=f"cert[{c['code']!r}].date"),
            credential_url=c.get("credential_url"),
            notes=c.get("notes"),
        )

    def gap_from_dict(g: dict[str, Any]) -> Gap:
        return Gap(
            skill=g["skill"],
            severity=GapSeverity(g["severity"]),
            evidence=EvidenceLevel(g["evidence"]),
            notes=g.get("notes"),
        )

    def project_from_dict(p: dict[str, Any]) -> Project:
        return Project(
            name=p["name"],
            url=p["url"],
            stack=p["stack"],
            description=p["description"],
            skills_evidence=p.get("skills_evidence", []),
        )

    def skill_category_from_dict(d: dict[str, Any]) -> SkillCategory:
        return SkillCategory(category=d["category"], skills=d["skills"])

    def work_exp_from_dict(d: dict[str, Any]) -> WorkExperience:
        return WorkExperience(
            title=d["title"],
            company=d["company"],
            location=d.get("location"),
            dates=d.get("dates"),
            bullets=d.get("bullets", []),
        )

    def education_from_dict(d: dict[str, Any]) -> Education:
        return Education(
            institution=d.get("institution", ""),
            credential=d["credential"],
            dates=d.get("dates"),
        )

    def star_story_from_dict(d: dict[str, Any]) -> StarStory:
        return StarStory(
            title=d["title"],
            jd_tags=list(d.get("jd_tags", [])),
            use_for=list(d.get("use_for", [])),
            situation=d.get("situation", ""),
            task=d.get("task", ""),
            action=d.get("action", ""),
            result=d.get("result", ""),
            last_used=d.get("last_used"),
            used_for=list(d.get("used_for", [])),
            adapt_when=list(d.get("adapt_when", [])),
        )

    def contact_from_dict(d: dict[str, Any] | str | None) -> Contact:
        """Coerce legacy ``dict[str, str]`` and new typed payloads.

        Earlier bundles serialized ``contact`` as a plain dict with lowercased
        keys (``email``, ``phone``). New bundles serialize the typed ``Contact``
        dataclass which uses the same field names. This loader accepts both.
        """
        if isinstance(d, str):
            # Defensive: if contact somehow serializes as a JSON string, parse it.
            d = json.loads(d)
        d = d or {}
        # ``d`` is now a dict (either originally or after json.loads). mypy
        # needs a runtime narrowing it can't infer from the union above.
        assert isinstance(d, dict)
        return Contact(
            name=d.get("name", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            location=d.get("location", ""),
            linkedin=d.get("linkedin", ""),
            github=d.get("github", ""),
            pluralsight=d.get("pluralsight", ""),
        )

    resume_data = data["resume"]
    resume = Resume(
        headline=resume_data["headline"],
        summary=resume_data["summary"],
        technical_skills=[skill_category_from_dict(s) for s in resume_data["technical_skills"]],
        experience=[work_exp_from_dict(e) for e in resume_data["experience"]],
        education=[education_from_dict(e) for e in resume_data.get("education", [])],
        certifications=[cert_from_dict(c) for c in resume_data.get("certifications", [])],
        star_stories=[star_story_from_dict(s) for s in resume_data.get("star_stories", [])],
    )

    return ProfileBundle(
        bundle_version=data["bundle_version"],
        generated=_to_date(data["generated"], field="generated"),
        sources={k: _to_date(v, field=f"sources[{k!r}]") for k, v in data["sources"].items()},
        contact=contact_from_dict(data["contact"]),
        headline=data["headline"],
        summary=data["summary"],
        cert_registry=[cert_from_dict(c) for c in data["cert_registry"]],
        differentiators=data["differentiators"],
        known_genuine_gaps=[gap_from_dict(g) for g in data["known_genuine_gaps"]],
        resolved_framing_gaps=data["resolved_framing_gaps"],
        portfolio_projects=[project_from_dict(p) for p in data["portfolio_projects"]],
        ats_keywords=data["ats_keywords"],
        ai200_domain_coverage=data["ai200_domain_coverage"],
        resume=resume,
        raw_sections=data.get("raw_sections", {}),
    )


def load_presence_bundle(root: Path | None = None) -> PresenceBundle:
    """Load ``outputs/presence-bundle.json`` into a typed PresenceBundle."""
    root = root or _find_repo_root()
    data = json.loads((root / "outputs" / "presence-bundle.json").read_text())
    _validate_schema(data, _PRESENCE_SCHEMA, "presence-bundle.json")

    def cert_from_dict(c: dict[str, Any]) -> Cert:
        return Cert(
            code=c["code"],
            status=CertStatus(c["status"]),
            date=_to_date(c.get("date"), field=f"cert[{c['code']!r}].date"),
            credential_url=c.get("credential_url"),
            notes=c.get("notes"),
        )

    def project_from_dict(p: dict[str, Any]) -> Project:
        return Project(
            name=p["name"],
            url=p["url"],
            stack=p["stack"],
            description=p["description"],
            skills_evidence=p.get("skills_evidence", []),
        )

    def work_exp_from_dict(d: dict[str, Any]) -> WorkExperience:
        return WorkExperience(
            title=d["title"],
            company=d["company"],
            location=d.get("location"),
            dates=d.get("dates"),
            bullets=d.get("bullets", []),
        )

    return PresenceBundle(
        bundle_version=data["bundle_version"],
        generated=_to_date(data["generated"], field="generated"),
        headline=data["headline"],
        summary=data["summary"],
        cert_registry=[cert_from_dict(c) for c in data["cert_registry"]],
        technical_skills=data["technical_skills"],
        portfolio_projects=[project_from_dict(p) for p in data["portfolio_projects"]],
        differentiators=data["differentiators"],
        experience=[work_exp_from_dict(e) for e in data.get("experience", [])],
    )


def _find_repo_root() -> Path:
    """Walk upward looking for the monorepo root (contains README.md and outputs/)."""
    here = Path.cwd().resolve()
    for parent in [here, *here.parents]:
        if (parent / "README.md").exists() and (parent / "outputs").exists():
            return parent
    raise FileNotFoundError("Could not locate monorepo root containing README.md and outputs/")
