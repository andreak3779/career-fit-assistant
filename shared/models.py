"""Typed data models for claude-projects bundles.

ProfileBundle is the full consumer-facing package used by Project 1.
PresenceBundle is the GitHub-safe subset used by Project 3.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class CertStatus(str, Enum):
    CERTIFIED = "certified"
    IN_PROGRESS = "in_progress"
    NOT_PURSUING = "not_pursuing"


class GapSeverity(str, Enum):
    GENUINE = "genuine"
    FRAMING = "framing"
    RESOLVED = "resolved"


class EvidenceLevel(str, Enum):
    PRODUCTION = "production"
    PORTFOLIO = "portfolio"
    COURSE = "course"
    NONE = "none"


# Cert codes whose status may appear in the public-safe presence bundle.
# Single source of truth — referenced by build_bundles.py, validate.py,
# presence-bundle schema, and tests.
PUBLIC_CERTS: frozenset[str] = frozenset({"AZ-900", "AI-200"})


@dataclass
class Cert:
    code: str
    status: CertStatus
    date: date | None = None
    credential_url: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class Gap:
    skill: str
    severity: GapSeverity
    evidence: EvidenceLevel = EvidenceLevel.NONE
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class Project:
    name: str
    url: str
    stack: list[str]
    description: str
    skills_evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class SkillCategory:
    category: str
    skills: list[str]

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class WorkExperience:
    title: str
    company: str
    location: str | None = None
    dates: str | None = None
    bullets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class Education:
    institution: str
    credential: str
    dates: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class GapCoachingEntry:
    """A hand-authored coaching note for one skill gap.

    Source: ``project-1-application-engine/reference/gap-coaching.md``. Not
    part of any bundle — read and parsed directly by ``interview_prep.py``,
    since it's reference material for a single skill, not a career fact.
    """

    heading: str
    status: str
    what_to_say: str
    what_not_to_say: list[str] = field(default_factory=list)
    best_star_bridge: str = ""
    honest_floor: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class StarStory:
    """A Situation/Task/Action/Result story from the STAR bank.

    Source: ``project-1-application-engine/reference/star-bank.md``.
    The bundle builder parses that file into ``list[StarStory]`` and exposes
    it on ``Resume.star_stories``.
    """

    title: str
    jd_tags: list[str]
    use_for: list[str] = field(default_factory=list)
    situation: str = ""
    task: str = ""
    action: str = ""
    result: str = ""
    last_used: str | None = None
    used_for: list[str] = field(default_factory=list)
    adapt_when: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class Contact:
    """Typed contact block. Replaces the unconstrained ``dict[str, str]``.

    Keys are stable so resume/cover-letter templates can rely on them without
    ``.get(..., default)`` chains for every field.
    """

    name: str
    email: str
    phone: str
    location: str = ""
    linkedin: str = ""
    github: str = ""
    pluralsight: str = ""

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class Resume:
    headline: str
    summary: str
    technical_skills: list[SkillCategory]
    experience: list[WorkExperience]
    education: list[Education] = field(default_factory=list)
    certifications: list[Cert] = field(default_factory=list)
    star_stories: list[StarStory] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class ProfileBundle:
    """Full bundle consumed by Project 1. May contain PII (email/phone).

    .. warning::
       ``raw_sections`` is reserved for opaque markdown dumps and is **not**
       covered by the default PII guard allow-list. Bundles that populate
       ``raw_sections`` must either scrub PII before populating, or extend
       ``shared.pii_guard.assert_presence_safe`` with a narrower allow-list.
       The current builder leaves this field empty.
    """

    bundle_version: int
    generated: date
    sources: dict[str, date]
    contact: Contact
    headline: str
    summary: str
    cert_registry: list[Cert]
    differentiators: list[str]
    known_genuine_gaps: list[Gap]
    resolved_framing_gaps: list[str]
    portfolio_projects: list[Project]
    ats_keywords: dict[str, list[str]]
    ai200_domain_coverage: list[dict[str, Any]]
    resume: Resume
    raw_sections: dict[str, str] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


@dataclass
class PresenceBundle:
    """GitHub-safe bundle consumed by Project 3. Must never contain phone/email."""

    bundle_version: int
    generated: date
    headline: str
    summary: str
    cert_registry: list[Cert]
    technical_skills: dict[str, list[str]]
    portfolio_projects: list[Project]
    differentiators: list[str]
    experience: list[WorkExperience] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return _serialize(self)


def _serialize(obj: Any) -> Any:
    """Serialize dataclasses, dates, and enums for JSON output."""
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    return obj
