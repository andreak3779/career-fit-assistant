#!/usr/bin/env python3
"""Generate typed JSON bundles from canonical Project 2 markdown sources.

Outputs:
    outputs/profile-bundle.json   (PII allowed; consumed by Project 1)
    outputs/presence-bundle.json  (PII-scanned; consumed by Project 3)
"""

from __future__ import annotations

import json
import sys
import warnings
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]

from shared import (
    PUBLIC_CERTS,
    Cert,
    CertStatus,
    Contact,
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
    assert_presence_safe,
    load_sources,
)


def _file_mtime(path: Path) -> date:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts).date()


def build(root: Path) -> tuple[ProfileBundle, PresenceBundle]:
    sources = load_sources(root)
    today = date.today()

    source_mtimes = {
        "profile-facts": _file_mtime(root / "project-2-profile-learning-hub" / "profile-facts.md"),
        "Resume_Snapshot": _file_mtime(
            root / "project-2-profile-learning-hub" / "Resume_Snapshot.md"
        ),
        "skills-summary": _file_mtime(
            root / "project-2-profile-learning-hub" / "skills-summary.md"
        ),
        "github-repos": _file_mtime(root / "project-2-profile-learning-hub" / "github-repos.md"),
    }

    certs = _build_certs(sources)
    gaps = _build_genuine_gaps(sources)
    resolved = sources.profile_facts["resolved_framing_gaps"]
    projects = _build_projects(sources)
    ats_keywords = sources.skills_summary["key_skills"]
    ai200 = [
        {"domain": row.get("Domain", ""), "status": row.get("Status", "")}
        for row in sources.skills_summary["ai200_coverage"]
    ]
    star_stories = _build_star_stories(sources)
    resume = _build_resume(sources, star_stories)

    contact_dict = sources.resume_snapshot["contact"]
    contact = Contact(
        name=contact_dict.get("name", ""),
        email=contact_dict.get("email", ""),
        phone=contact_dict.get("phone", ""),
        location=contact_dict.get("location", ""),
        linkedin=contact_dict.get("linkedin", ""),
        github=contact_dict.get("github", ""),
        pluralsight=contact_dict.get("pluralsight", ""),
    )
    profile = ProfileBundle(
        bundle_version=_next_bundle_version(root),
        generated=today,
        sources=source_mtimes,
        contact=contact,
        headline=sources.resume_snapshot["title"],
        summary=sources.resume_snapshot["summary"],
        cert_registry=certs,
        differentiators=sources.profile_facts["differentiators"],
        known_genuine_gaps=gaps,
        resolved_framing_gaps=resolved,
        portfolio_projects=projects,
        ats_keywords=ats_keywords,
        ai200_domain_coverage=ai200,
        resume=resume,
    )

    presence = PresenceBundle(
        bundle_version=profile.bundle_version,
        generated=today,
        headline=profile.headline,
        summary=_scrub_summary(profile.summary),
        cert_registry=[c for c in certs if c.code in PUBLIC_CERTS],
        technical_skills={cat.category: cat.skills for cat in resume.technical_skills},
        portfolio_projects=projects,
        differentiators=profile.differentiators,
        experience=resume.experience,
    )

    assert_presence_safe(presence.to_dict())

    return profile, presence


def _next_bundle_version(root: Path) -> int:
    profile_path = root / "outputs" / "profile-bundle.json"
    if not profile_path.exists():
        return 1
    try:
        text = profile_path.read_text(encoding="utf-8")
    except OSError:
        return 1
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        warnings.warn(
            f"Existing {profile_path} is invalid JSON; starting version at 1", stacklevel=2
        )
        return 1
    try:
        return int(data.get("bundle_version", 0)) + 1
    except (TypeError, ValueError):
        warnings.warn(
            f"Existing {profile_path} has missing/invalid bundle_version; starting at 1",
            stacklevel=2,
        )
        return 1


def _to_iso_date(value: Any) -> date | None:
    """Coerce YAML/JSON date value to ``datetime.date``.

    YAML parses unquoted ISO dates (e.g. ``date: 2026-04-18``) into native
    ``datetime.date`` objects; JSON keeps them as strings. Accept both.
    """
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _build_certs(sources: Any) -> list[Cert]:
    """Build Cert objects from the YAML frontmatter in profile-facts.md.

    The cert table is now declared as YAML at the top of profile-facts.md:
        certs:
          - code: AZ-900
            status: certified
            date: 2026-04-18
            credential_url: https://learn.microsoft.com/...
    Rows with an unrecognised status are skipped silently; malformed dates
    are coerced to None rather than raising so the build doesn't fail on a
    single bad row.
    """
    entries = sources.profile_facts.get("certs", []) or []
    certs: list[Cert] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "")).strip()
        if not code:
            continue
        raw_status = entry.get("status")
        try:
            status = CertStatus(raw_status)
        except (ValueError, KeyError, TypeError):
            warnings.warn(
                f"Skipping cert {code!r}: unrecognized status {raw_status!r}", stacklevel=2
            )
            continue
        cert_date = _to_iso_date(entry.get("date"))
        if cert_date is None and entry.get("date") is not None:
            warnings.warn(
                f"Cert {code!r} has malformed date {entry.get('date')!r}; using None",
                stacklevel=2,
            )
        certs.append(
            Cert(
                code=code,
                status=status,
                date=cert_date,
                credential_url=entry.get("credential_url"),
                notes=entry.get("notes"),
            )
        )
    return certs


def _build_genuine_gaps(sources: Any) -> list[Gap]:
    impact_notes = sources.profile_facts.get("impact_notes", [])
    gaps: list[Gap] = []
    for paragraph in impact_notes:
        # Lines starting with "- " inside the impact section name skills.
        for line in paragraph.split("\n"):
            stripped = line.strip()
            if stripped.startswith("-"):
                skill = stripped.lstrip("- ").split("—")[0].strip().lower()
                note = stripped
                if "portfolio" in note:
                    evidence = EvidenceLevel.PORTFOLIO
                elif "course" in note or "lab" in note:
                    evidence = EvidenceLevel.COURSE
                else:
                    evidence = EvidenceLevel.NONE
                gaps.append(
                    Gap(skill=skill, severity=GapSeverity.GENUINE, evidence=evidence, notes=note)
                )
    # Add the explicit "Known Genuine Gaps" bullets too.
    for bullet in sources.profile_facts.get("known_genuine_gaps", []):
        if "—" in bullet:
            skill = bullet.split("—")[0].strip().lower()
        else:
            skill = bullet.split()[0].lower()
        note = bullet
        if "portfolio" in note:
            evidence = EvidenceLevel.PORTFOLIO
        elif "course" in note or "lab" in note:
            evidence = EvidenceLevel.COURSE
        else:
            evidence = EvidenceLevel.NONE
        gaps.append(Gap(skill=skill, severity=GapSeverity.GENUINE, evidence=evidence, notes=note))
    return gaps


def _build_projects(sources: Any) -> list[Project]:
    repos = sources.github_repos.get("repos", [])
    projects: list[Project] = []
    for i, repo in enumerate(repos):
        if not isinstance(repo, dict):
            warnings.warn(
                f"Skipping repo entry {i}: expected dict, got {type(repo).__name__}",
                stacklevel=2,
            )
            continue
        required = ("name", "url", "description")
        missing = [k for k in required if not repo.get(k)]
        if missing:
            warnings.warn(
                f"Skipping repo {repo.get('name', f'entry {i}')!r}: "
                f"missing required fields {missing}",
                stacklevel=2,
            )
            continue
        stack_raw = repo.get("stack", "")
        skills_raw = repo.get("skills_evidence", "")
        projects.append(
            Project(
                name=repo["name"],
                url=repo["url"],
                stack=[s.strip() for s in stack_raw.replace("·", ",").split(",")]
                if stack_raw
                else [],
                description=repo["description"],
                skills_evidence=(
                    [s.strip() for s in skills_raw.replace("·", ",").split(",")]
                    if skills_raw
                    else []
                ),
            )
        )
    return projects


def _build_star_stories(sources: Any) -> list[StarStory]:
    """Convert parsed star-bank dicts into typed ``StarStory`` objects."""
    return [
        StarStory(
            title=s["title"],
            jd_tags=s.get("jd_tags", []),
            use_for=s.get("use_for", []),
            situation=s.get("situation", ""),
            task=s.get("task", ""),
            action=s.get("action", ""),
            result=s.get("result", ""),
            last_used=s.get("last_used"),
            used_for=s.get("used_for", []),
            adapt_when=s.get("adapt_when", []),
        )
        for s in sources.star_bank
    ]


def _build_resume(sources: Any, star_stories: list[StarStory]) -> Resume:
    snap = sources.resume_snapshot
    skills = [
        SkillCategory(category=cat, skills=skills_list)
        for cat, skills_list in snap.get("technical_skills", {}).items()
    ]
    experience = [
        WorkExperience(
            title=e["title"],
            company=e["company"],
            location=e.get("location"),
            dates=e.get("dates"),
            bullets=e.get("bullets", []),
        )
        for e in snap.get("experience", [])
    ]
    return Resume(
        headline=snap["title"],
        summary=snap["summary"],
        technical_skills=skills,
        experience=experience,
        education=[],
        star_stories=star_stories,
    )


def _scrub_summary(summary: str) -> str:
    """Remove explicit contact lines from presence-safe summary."""
    # The summary should already be clean, but belt-and-braces.
    for token in ("Email:", "Phone:", "Timezone:", "Province:", "City:"):
        summary = summary.split(token)[0]
    return summary.strip()


def write(root: Path, profile: ProfileBundle, presence: PresenceBundle) -> None:
    out_dir = root / "outputs"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: cannot create outputs directory {out_dir}: {exc}", file=sys.stderr)
        raise
    try:
        (out_dir / "profile-bundle.json").write_text(
            json.dumps(profile.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (out_dir / "presence-bundle.json").write_text(
            json.dumps(presence.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"ERROR: failed to write bundle JSON: {exc}", file=sys.stderr)
        raise


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]).resolve() if argv else ROOT
    try:
        profile, presence = build(root)
        write(root, profile, presence)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote outputs/profile-bundle.json v{profile.bundle_version}")
    print(f"Wrote outputs/presence-bundle.json v{presence.bundle_version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
