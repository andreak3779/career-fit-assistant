"""Deterministic fit-rating engine for job descriptions vs profile bundles."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from shared.models import GapCoachingEntry, ProfileBundle

MatchStatus = Literal["match", "portfolio", "course", "gap"]
Rating = Literal["Strong", "Good", "Stretch", "Pass"]

# Order used when ranking evidence strength.
EVIDENCE_STATUS_ORDER: tuple[MatchStatus, ...] = ("match", "portfolio", "course", "gap")


@dataclass(frozen=True)
class SkillMatch:
    skill: str
    status: MatchStatus
    evidence: str

    @property
    def is_grounded(self) -> bool:
        """True when the match is backed by production or portfolio evidence."""
        return self.status in ("match", "portfolio")

    @property
    def evidence_strength(self) -> int:
        """Higher is stronger; matches rank above portfolio, course, gap."""
        try:
            return EVIDENCE_STATUS_ORDER.index(self.status)
        except ValueError:
            return len(EVIDENCE_STATUS_ORDER)


@dataclass(frozen=True)
class FitResult:
    rating: Rating
    required: list[SkillMatch]
    nice_to_have: list[SkillMatch]
    rationale: str

    @property
    def grounded_required(self) -> list[SkillMatch]:
        """Required skills with production or portfolio evidence."""
        return [m for m in self.required if m.is_grounded]

    @property
    def ungrounded_required(self) -> list[SkillMatch]:
        """Required skills with only coursework or no evidence."""
        return [m for m in self.required if not m.is_grounded]

    def evidence_sources(self) -> list[str]:
        """Return a concise, sorted list of evidence labels used in matches.

        Labels are extracted from the portion before the colon (company or
        project name). Multi-line evidence strings are clamped to their first
        line so labels stay short and sidecars remain readable.
        """
        labels: set[str] = set()
        for m in self.required + self.nice_to_have:
            if not m.is_grounded:
                continue
            raw = (m.evidence or "").strip()
            if ":" in raw:
                label = raw.rsplit(":", 1)[0].strip().splitlines()[0]
                labels.add(label)
            elif raw:
                labels.add(raw.splitlines()[0])
        return sorted(labels)


def _load_aliases(path: Path | None = None) -> dict[str, list[str]]:
    """Load the alias registry from shared/aliases.json."""
    if path is None:
        path = Path(__file__).with_name("aliases.json")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    aliases = data.get("aliases", {})
    return {str(k).lower(): [str(v).lower() for v in vals] for k, vals in aliases.items()}


_ALIASES: dict[str, list[str]] = _load_aliases()


def _tokenize(skills: list[str]) -> list[str]:
    return [s.strip().lower() for s in skills if s.strip()]


def _normalize(skill: str) -> str:
    """Lowercase and strip noisy years-of-experience prefixes and parenthetical ranges."""
    s = skill.strip().lower()
    s = re.sub(
        r"^\d+\s*(?:[-+]|to\s*\d+)?\s*(?:years?|yrs?)\s*(?:of\s*)?", "", s, flags=re.IGNORECASE
    )
    s = re.sub(r"^\+\s*", "", s)
    s = re.sub(r"^(?:years?|yrs?)\s*(?:of\s*)?", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*\([^)]*\)", "", s)
    return s.strip(" ,./:;")


def skill_match_terms(skill: str) -> list[str]:
    """Return the normalized, alias-expanded match terms for a skill/requirement.

    Public seam around the same pipeline ``_has_skill`` uses internally
    (normalize → alias expansion → compound-phrase splitting), so other
    modules (e.g. gap-coaching heading matching in ``find_gap_coaching_entry``)
    can reuse it without reaching into this module's private helpers.
    """
    normalized = _normalize(skill)
    terms = _expand_terms(normalized)
    # Also expand any multi-token phrase into its component tokens for matching
    terms.extend(_split_compound(normalized))
    return list(dict.fromkeys(terms))


def _has_skill(profile: ProfileBundle, raw_skill: str) -> tuple[MatchStatus, str]:
    """Return (status, evidence) for a single skill against the profile."""
    skill_lower = _normalize(raw_skill)
    skill_terms = skill_match_terms(raw_skill)

    # Production experience: resume bullets mention it. Entries with no
    # company (e.g. "Professional Development & Portfolio Building" — a
    # resume section for self-directed coursework, not an employer) are
    # skipped here: their content is explicitly course/portfolio-level, and
    # counting it as production would overclaim evidence for a real job
    # requirement. Skills mentioned there still register below via the
    # technical_skills/ats_keywords course-tier check.
    for exp in profile.resume.experience:
        if not exp.company:
            continue
        joined = " ".join(exp.bullets + [exp.title, exp.company]).lower()
        if _match_terms(skill_terms, joined):
            return "match", f"{exp.company}: production"

    # Resolved framing gaps are always matches
    if any(skill_lower == g.lower() for g in profile.resolved_framing_gaps):
        return "match", "resolved framing gap"

    # Portfolio evidence
    for project in profile.portfolio_projects:
        text = f"{project.name} {' '.join(project.stack)} {project.description} {' '.join(project.skills_evidence)}".lower()
        if _match_terms(skill_terms, text):
            return "portfolio", f"{project.name}: portfolio"

    # Known genuine gaps with portfolio evidence
    for gap in profile.known_genuine_gaps:
        if gap.evidence.value == "portfolio" and _match_terms(skill_terms, gap.skill.lower()):
            return "portfolio", f"tracked gap (portfolio): {gap.skill}"

    # Coursework evidence via ATS keywords / technical skills
    skill_pool = []
    for cat in profile.resume.technical_skills:
        skill_pool.extend(cat.skills)
    for values in profile.ats_keywords.values():
        skill_pool.extend(values)
    all_skills_text = " ".join(skill_pool).lower()
    if _match_terms(skill_terms, all_skills_text):
        return "course", "coursework or self-study"

    # Known genuine gaps may already be partially addressed by coursework
    gap_pool = [g.skill for g in profile.known_genuine_gaps]
    all_gaps_text = " ".join(gap_pool).lower()
    if _match_terms(skill_terms, all_gaps_text):
        return "course", "tracked gap — partial coursework"

    return "gap", "no evidence"


def _split_compound(skill: str) -> list[str]:
    """Break compound phrases on '/', ';', 'and', 'or' to allow partial matches."""
    pieces = re.split(r"[/;]|\s+or\s+|\s+and\s+", skill)
    return [p.strip(" ,./:;") for p in pieces if len(p.strip()) > 1]


def _expand_terms(skill: str) -> list[str]:
    """Return the skill plus any registered aliases for it."""
    terms = [skill]
    for key, aliases in _ALIASES.items():
        if skill == key or skill in aliases:
            terms.extend([key] + aliases)
    return list(dict.fromkeys(terms))


def _match_terms(terms: list[str], haystack: str) -> bool:
    """Match any term against the haystack. Avoids single-letter false positives."""
    for term in terms:
        if len(term) <= 1:
            continue
        if term in haystack:
            return True
    return False


_PAREN_QUALIFIER_RE = re.compile(r"\s*\([^)]*\)")


def find_gap_coaching_entry(skill: str, entries: list[GapCoachingEntry]) -> GapCoachingEntry | None:
    """Find the gap-coaching entry whose heading best matches ``skill``.

    Headings carry a parenthetical qualifier (e.g. "Power BI (as primary
    requirement)") describing *when* the note applies, not part of the
    matchable label — stripped before comparing. Matching is bidirectional
    substring matching on the same normalize/alias-expand/split pipeline
    ``_has_skill`` uses (via ``skill_match_terms``): either the heading's
    terms appear in the skill text (catches a short heading like "Cloud /
    Azure" matching a longer JD phrase like "strong azure fundamentals"),
    or the skill's terms appear in the heading text (catches a short JD
    term like "oracle" matching a longer heading like "Oracle Databases").
    Returns the first entry in file order to match — deterministic, no LLM
    fallback. An unmatched skill returns ``None``, never a fabricated or
    approximate coaching note.
    """
    skill_lower = _normalize(skill)
    skill_terms = skill_match_terms(skill)
    for entry in entries:
        heading_stripped = _PAREN_QUALIFIER_RE.sub("", entry.heading).strip()
        heading_lower = heading_stripped.lower()
        heading_terms = skill_match_terms(heading_stripped)
        if _match_terms(heading_terms, skill_lower) or _match_terms(skill_terms, heading_lower):
            return entry
    return None


def rate_fit(required: list[str], nice_to_have: list[str], profile: ProfileBundle) -> FitResult:
    """Rate how well ``profile`` matches a JD with the given required and nice skills."""
    required_matches = [_classify(skill, profile) for skill in _tokenize(required)]
    nice_matches = [_classify(skill, profile) for skill in _tokenize(nice_to_have)]
    rating, rationale = _derive_rating(required_matches, nice_matches)
    return FitResult(
        rating=rating, required=required_matches, nice_to_have=nice_matches, rationale=rationale
    )


def _classify(skill: str, profile: ProfileBundle) -> SkillMatch:
    status, evidence = _has_skill(profile, skill)
    return SkillMatch(skill=skill, status=status, evidence=evidence)


def _derive_rating(required: list[SkillMatch], nice: list[SkillMatch]) -> tuple[Rating, str]:
    """Raw ✅/🟡/🔴 count thresholds — kept deliberately in lockstep with the
    Strong/Good/Stretch/Pass definitions documented in job_description_fit/SKILL.md
    and gap_analysis_job_description/SKILL.md. Do not reintroduce weighted/
    averaged scoring here without updating those docs to match — a prior
    weighted-average version of this function silently diverged from the
    documented rules in two ways: an all-course-only required list (3+ 🟡,
    zero 🔴) rated "Good" instead of the documented "Stretch", and a required
    list with fewer than 3 raw 🔴 but weak evidence could rate "Pass" instead
    of "Stretch" — both false positives for a system whose rating gates real
    job applications.
    """
    if not required:
        return "Pass", "No required skills provided"

    req_counts = _count_statuses(required)
    nice_counts = _count_statuses(nice)

    required_red = req_counts["gap"]
    required_yellow = req_counts["portfolio"] + req_counts["course"]
    nice_present = nice_counts["match"] + nice_counts["portfolio"] + nice_counts["course"]

    # Pass: 3+ required skills are genuine gaps.
    if required_red >= 3:
        return (
            "Pass",
            f"{required_red} genuine gaps in required skills — critical mismatch likely.",
        )
    # Stretch: 1-2 required skills are genuine gaps.
    if required_red >= 1:
        return (
            "Stretch",
            f"{required_red} gap(s) and {required_yellow} course-only signal(s) in required skills.",
        )
    # From here, required_red == 0 (no genuine gaps in required skills).
    # Stretch: 3+ required skills are course/portfolio-only (no production evidence).
    if required_yellow >= 3:
        return (
            "Stretch",
            f"All required skills present but {required_yellow} are course/portfolio-only, "
            "with no production evidence.",
        )
    # Strong: 0-2 required skills course/portfolio-only, and at least 2 nice-to-haves present.
    if required_yellow <= 2 and nice_present >= 2:
        return (
            "Strong",
            f"All {len(required)} required skills covered "
            f"({required_yellow} course/portfolio-only); {nice_present} nice-to-have(s) present.",
        )
    # Good: required skills fully covered (✅/🟡, no 🔴), but short of Strong's bar.
    return (
        "Good",
        f"All required skills covered ({required_yellow} course/portfolio-only signal(s)); "
        f"{nice_present} nice-to-have(s) present.",
    )


def _count_statuses(matches: list[SkillMatch]) -> dict[str, int]:
    counts: dict[str, int] = {"match": 0, "portfolio": 0, "course": 0, "gap": 0}
    for m in matches:
        counts[m.status] += 1
    return counts


_STATUS_EMOJI = {
    "match": "✅",
    "portfolio": "🟡",
    "course": "🟡",
    "gap": "🔴",
}


def _display_evidence(evidence: str) -> str:
    """Comma-separated display form of an evidence string for the fit table
    (e.g. "Contoso: production" -> "Contoso, production"), matching the
    ``"Fieldstone Benefits Administrators, production"`` style in job_description_fit/SKILL.md's
    Step 4 template. The stored evidence string itself keeps its colon
    separator — ``evidence_sources()``/``humanize_evidence()`` split on it —
    this only affects how the table is rendered.
    """
    return evidence.replace(": ", ", ", 1)


def render_fit_table(result: FitResult) -> str:
    """Render a FitResult as markdown suitable for CLI or skill output."""
    lines: list[str] = []
    lines.append("## Fit Check")
    lines.append("")
    lines.append("**Required Skills**")
    lines.append("| Skill | Status | Evidence |")
    lines.append("|---|---|---|")
    for m in result.required:
        lines.append(f"| {m.skill} | {_STATUS_EMOJI[m.status]} | {_display_evidence(m.evidence)} |")
    if result.nice_to_have:
        lines.append("")
        lines.append("**Nice-to-Haves**")
        lines.append("| Skill | Status | Evidence |")
        lines.append("|---|---|---|")
        for m in result.nice_to_have:
            lines.append(
                f"| {m.skill} | {_STATUS_EMOJI[m.status]} | {_display_evidence(m.evidence)} |"
            )
    lines.append("")
    lines.append(f"**Fit Rating: {result.rating}**")
    lines.append(f"{result.rationale}")
    return "\n".join(lines)


def humanize_evidence(match: SkillMatch, *, audience: str = "letter") -> str:
    """Convert a debug-grade evidence string into prose appropriate for the audience.

    ``audience="debug"`` keeps the original machine-readable evidence label.
    ``audience="letter"`` returns candidate-friendly phrasing that does not
    overclaim course/gap skills as production experience.

    Examples:
        >>> humanize_evidence(SkillMatch("Azure", "match", "Contoso: production"))
        'production evidence at Contoso'
        >>> humanize_evidence(SkillMatch("Docker", "portfolio", "RecipeBox: portfolio"))
        'portfolio evidence on RecipeBox'
        >>> humanize_evidence(SkillMatch("Kubernetes", "course", "coursework or self-study"))
        'familiar through recent coursework'
        >>> humanize_evidence(SkillMatch("Rust", "gap", "no evidence"))
        'not yet demonstrated in production'
    """
    if audience == "debug":
        return match.evidence or "no evidence"

    status = match.status
    raw = (match.evidence or "").strip()
    if status == "match":
        if ":" in raw:
            label = raw.rsplit(":", 1)[0].strip()
            return f"production evidence at {label}" if label else "production evidence"
        return "production evidence"
    if status == "portfolio":
        if ":" in raw:
            label = raw.rsplit(":", 1)[0].strip()
            return f"portfolio evidence on {label}" if label else "portfolio evidence"
        return "portfolio evidence"
    if status == "course":
        return "familiar through recent coursework"
    if status == "gap":
        return "not yet demonstrated in production"
    return raw or "evidence on file"


def profile_has_skill_text(skill: str, haystack: str) -> bool:
    """Reuse the fit-engine's alias-aware matching for callers like resume sort.

    This is the same logic that ``_has_skill`` uses internally: a skill matches
    the haystack if any of its tokens (after years-prefix normalization) or its
    registered aliases appear in the haystack. Single-character tokens are
    skipped to avoid false positives.
    """
    skill_lower = _normalize(skill)
    terms = _expand_terms(skill_lower)
    terms.extend(_split_compound(skill_lower))
    terms = list(dict.fromkeys(terms))
    return _match_terms(terms, haystack.lower())
