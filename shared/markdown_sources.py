"""Parse canonical markdown source files into structured data.

The career data lives in four Project 2 files:
    - profile-facts.md
    - Resume_Snapshot.md
    - skills-summary.md
    - github-repos.md

This module extracts tables, sections, and lists deterministically so that
build_bundles.py can map them into typed models.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from shared.models import GapCoachingEntry


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Extract a YAML frontmatter block from the top of a markdown file.

    Returns ``{}`` if no frontmatter is present. Logs a warning to stderr when
    a frontmatter block is present but fails to parse — the rest of the file
    still loads via the legacy markdown parsers in that case.
    """
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    try:
        loaded = yaml.safe_load(block) or {}
        if not isinstance(loaded, dict):
            print(
                "[WARN] markdown_sources._parse_frontmatter: frontmatter is not a mapping",
                file=sys.stderr,
            )
            return {}
        return loaded
    except yaml.YAMLError as exc:
        print(
            f"[WARN] markdown_sources._parse_frontmatter: YAML parse failed: {exc}",
            file=sys.stderr,
        )
        return {}


@dataclass
class ParsedSources:
    """All raw, structured source sections used by the bundle builder."""

    profile_facts: dict[str, Any] = field(default_factory=dict)
    resume_snapshot: dict[str, Any] = field(default_factory=dict)
    skills_summary: dict[str, Any] = field(default_factory=dict)
    github_repos: dict[str, Any] = field(default_factory=dict)
    star_bank: list[dict[str, Any]] = field(default_factory=list)


def load_sources(root: Path) -> ParsedSources:
    """Load and parse all canonical markdown sources."""
    p2 = root / "project-2-profile-learning-hub"
    p1 = root / "project-1-application-engine"
    return ParsedSources(
        profile_facts=parse_profile_facts(read_file(p2 / "profile-facts.md")),
        resume_snapshot=parse_resume_snapshot(read_file(p2 / "Resume_Snapshot.md")),
        skills_summary=parse_skills_summary(read_file(p2 / "skills-summary.md")),
        github_repos=parse_github_repos(read_file(p2 / "github-repos.md")),
        star_bank=parse_star_bank(read_file(p1 / "reference" / "star-bank.md")),
    )


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_profile_facts(text: str) -> dict[str, Any]:
    """Extract cert status, differentiators, gaps, portfolio projects.

    The cert list now lives in a YAML frontmatter block at the top of the file
    (``certs: [{code, status, date, credential_url}, ...]``). The other
    sections remain in their original markdown form.
    """
    sections = _split_sections(text)
    frontmatter = _parse_frontmatter(text)
    return {
        "certs": frontmatter.get("certs", []),
        "cert_status_table": _extract_table(sections.get("Cert Status", "")),
        "differentiators": _extract_bullet_list(sections.get("Key Differentiators", "")),
        "known_genuine_gaps": _extract_bullet_list(_find_section(sections, "Known Genuine Gaps")),
        "resolved_framing_gaps": _extract_bullet_list(
            sections.get("Resolved Framing Gaps — Never Re-flag", "")
        ),
        "portfolio_projects": _extract_table(sections.get("Portfolio Projects", "")),
        "impact_notes": _extract_paragraphs(sections.get("Impact on Known Genuine Gaps", "")),
    }


def parse_resume_snapshot(text: str) -> dict[str, Any]:
    """Extract contact, summary, skills, experience, and education."""
    sections = _split_sections(text)
    preamble = _extract_preamble(text)
    return {
        "title": _first_line(text),
        "contact": _extract_contact_lines(sections.get("Contact Information", "") or preamble),
        "summary": _join_paragraphs(sections.get("Summary", "")),
        "technical_skills": _extract_subheadings(sections.get("Technical Skills", "")),
        "experience": _extract_experience_sections(text),
        "education": _extract_education_sections(text),
    }


def _extract_preamble(text: str) -> str:
    """Return the markdown between the title and the first h2 heading."""
    match = re.search(r"^##\s+", text, re.MULTILINE)
    if not match:
        return text
    return text[: match.start()]


def parse_skills_summary(text: str) -> dict[str, Any]:
    """Extract AI-200 coverage, skill category lists, and the top-of-file status line."""
    sections = _split_sections(text)
    return {
        "status_line": _extract_status_line(text),
        "ai200_coverage": _extract_table(
            sections.get("AI-200 Domain Coverage (Azure AI Cloud Developer Associate)", "")
        ),
        "course_summary_table": _extract_table(
            sections.get("Pluralsight Course Summary by Category", "")
        ),
        "key_skills": _extract_subheadings(
            sections.get("Key Skills for Resume / Job Applications", "")
        ),
    }


_STATUS_LINE_RE = re.compile(r"^\*\*Status:[^*]+\*\*", re.MULTILINE)


def _extract_status_line(text: str) -> str:
    """Return the ``**Status: ...**`` line that lives at the top of skills-summary.md."""
    match = _STATUS_LINE_RE.search(text)
    return match.group(0) if match else ""


_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def parse_github_repos(text: str) -> dict[str, Any]:
    """Extract portfolio repo metadata.

    Repos are commented out with ``<!-- ... -->`` when retired or not yet
    ready to surface (e.g. OldApp). Strip those blocks before splitting
    into sections, or a commented-out repo's ``## Heading`` still gets
    parsed as if it were a live entry — ``_split_sections`` only looks for
    ``^##`` and has no concept of HTML comments.
    """
    sections = _split_sections(_HTML_COMMENT_RE.sub("", text))
    repos: list[dict[str, str]] = []
    for heading, body in sections.items():
        if heading in ("Quick Reference — Skills by Repo", ""):
            continue
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        repo: dict[str, str] = {"name": heading.strip()}
        for line in lines:
            if line.startswith("URL:"):
                repo["url"] = line.replace("URL:", "").strip()
            elif line.startswith("Stack:"):
                repo["stack"] = line.replace("Stack:", "").strip()
            elif line.startswith("Description:"):
                repo["description"] = line.replace("Description:", "").strip()
            elif line.startswith("Status:"):
                repo["status"] = line.replace("Status:", "").strip()
        if "url" in repo:
            repos.append(repo)
    return {"repos": repos}


def parse_gap_coaching(text: str) -> list[GapCoachingEntry]:
    """Parse ``reference/gap-coaching.md`` into typed coaching entries.

    Each ``## <Gap Type>`` section has bold-labeled fields: ``**Status:**``,
    ``**What to say:**`` (quoted framing on the following line(s)),
    ``**What not to say:**`` (usually a bullet list, occasionally a single
    inline sentence when the gap needs no hedging \u2014 see the TDD/CI-CD
    entries), ``**Best STAR bridge:**``, and ``**Honest floor:**`` (both
    inline). The trailing "Notes on Using This File" section is authoring
    guidance, not a coaching entry, and is skipped.
    """
    sections = _split_sections(text)
    entries: list[GapCoachingEntry] = []
    for heading, body in sections.items():
        if heading in ("Notes on Using This File", ""):
            continue
        entries.append(_parse_gap_coaching_block(heading, body))
    return entries


def _parse_gap_coaching_block(heading: str, block: str) -> GapCoachingEntry:
    status = ""
    what_to_say_lines: list[str] = []
    what_not_to_say: list[str] = []
    best_star_bridge = ""
    honest_floor = ""
    current_field: str | None = None

    for raw_line in block.splitlines():
        stripped = raw_line.strip()
        field_match = _STAR_FIELD_RE.match(stripped)
        if field_match:
            key, value = field_match.group(1).strip(), field_match.group(2).strip()
            key_lower = key.lower()
            current_field = None
            if key_lower == "status":
                status = value
            elif key_lower == "what to say":
                current_field = "what_to_say"
                if value:
                    what_to_say_lines.append(value)
            elif key_lower == "what not to say":
                if value:
                    what_not_to_say.append(value)
                else:
                    current_field = "what_not_to_say"
            elif key_lower == "best star bridge":
                best_star_bridge = value
            elif key_lower == "honest floor":
                honest_floor = value
        elif not stripped:
            continue
        elif current_field == "what_to_say":
            what_to_say_lines.append(stripped)
        elif current_field == "what_not_to_say" and stripped.startswith(("-", "*")):
            item = stripped.lstrip("-* ").strip()
            if item:
                what_not_to_say.append(item)

    return GapCoachingEntry(
        heading=heading,
        status=status,
        what_to_say=" ".join(what_to_say_lines).strip(),
        what_not_to_say=what_not_to_say,
        best_star_bridge=best_star_bridge,
        honest_floor=honest_floor,
    )


_STAR_HEADING_RE = re.compile(r"^##\s+Story\s+(\d+)\s+\u2014\s+(.+?)\s*$", re.MULTILINE)
_STAR_FIELD_RE = re.compile(r"^\*\*([^*]+):\*\*\s*(.*)$")
_STAR_SECTIONS = {
    "Situation": "S",
    "Task": "T",
    "Action": "A",
    "Result": "R",
}


def parse_star_bank(text: str) -> list[dict[str, Any]]:
    """Parse ``reference/star-bank.md`` into a list of STAR-story dicts.

    Each story block begins with ``## Story N — Title`` and contains ``**Use for:**``,
    ``**JD tags:**``, ``**Situation:**``, ``**Task:**``, ``**Action:**``,
    ``**Result:**``, and optional ``**last_used:**`` / ``**used_for:**``.

    Section bodies preserve paragraph breaks: consecutive non-blank lines are
    joined into one paragraph; blank lines start a new paragraph within the
    same section.
    """
    stories: list[dict[str, Any]] = []
    matches = list(_STAR_HEADING_RE.finditer(text))
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        story = _parse_star_block(block)
        story["title"] = title
        stories.append(story)
    return stories


def _parse_star_block(block: str) -> dict[str, Any]:
    """Parse one STAR story block into a dict keyed S/T/A/R."""
    parsed_story: dict[str, Any] = {"jd_tags": [], "use_for": [], "adapt_when": []}
    section_letter: str | None = None
    in_adapt_when = False
    paragraphs: list[str] = []
    current: list[str] = []
    star_text: dict[str, list[str]] = {"S": [], "T": [], "A": [], "R": []}

    def flush_paragraph() -> None:
        if current:
            paragraphs.append(" ".join(current).strip())
            current.clear()

    def flush_section() -> None:
        flush_paragraph()
        if section_letter is not None and paragraphs:
            star_text[section_letter].append("\n\n".join(paragraphs).strip())
            paragraphs.clear()

    for raw_line in block.splitlines():
        stripped = raw_line.strip()
        field_match = _STAR_FIELD_RE.match(stripped)
        if field_match:
            flush_section()
            section_letter = None
            in_adapt_when = False
            key, value = field_match.group(1).strip(), field_match.group(2).strip()
            key_lower = key.lower()
            if key in _STAR_SECTIONS:
                section_letter = _STAR_SECTIONS[key]
                if value:
                    current.append(value)
            elif key_lower == "jd tags":
                parsed_story["jd_tags"] = _parse_backtick_tags(value)
            elif key_lower == "use for":
                parsed_story["use_for"] = [v.strip() for v in value.split("·") if v.strip()]
            elif key_lower == "last_used":
                parsed_story["last_used"] = value
            elif key_lower == "used_for":
                parsed_story["used_for"] = [v.strip() for v in value.split(",") if v.strip()]
            elif key_lower == "adapt when":
                in_adapt_when = True
        elif not stripped:
            if section_letter is not None and current:
                flush_paragraph()
        elif in_adapt_when and stripped.startswith(("-", "*")):
            item = stripped.lstrip("-* ").strip()
            if item:
                parsed_story["adapt_when"].append(item)
        elif section_letter is not None:
            current.append(stripped)
    flush_section()

    parsed_story["situation"] = "\n\n".join(star_text["S"]).strip()
    parsed_story["task"] = "\n\n".join(star_text["T"]).strip()
    parsed_story["action"] = "\n\n".join(star_text["A"]).strip()
    parsed_story["result"] = "\n\n".join(star_text["R"]).strip()
    return parsed_story


def _parse_backtick_tags(value: str) -> list[str]:
    """Parse ```tag1` `tag2` `` style strings."""
    return [t.strip("`").strip() for t in value.split() if t.strip("`").strip()]


# ---------------------------------------------------------------------------
# Low-level extraction helpers
# ---------------------------------------------------------------------------


def _first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def _split_sections(text: str) -> dict[str, str]:
    """Split markdown into h2 sections."""
    pattern = re.compile(r"^##\s+(.*?)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()
    return sections


def _extract_table(section: str) -> list[dict[str, str]]:
    """Parse a simple markdown table with header row and separator row."""
    rows: list[dict[str, str]] = []
    lines = [line.strip() for line in section.splitlines() if line.strip()]
    if len(lines) < 2:
        return rows
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    for line in lines[2:]:
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")][1:-1]
        if len(cells) >= len(headers):
            rows.append(dict(zip(headers, cells)))  # noqa: B905 - len guard above ensures equal lengths
    return rows


_BULLET_MARKER_RE = re.compile(r"^[-*]\s+")


def _extract_bullet_list(section: str) -> list[str]:
    """Extract list items from ``- `` / ``* `` markdown bullet lines.

    Only strips a genuine list marker (a single leading ``-`` or ``*``
    followed by whitespace). A bold-labeled paragraph line like
    ``**Azure & Cloud Services:** ...`` also starts with ``*`` but has no
    space after the second ``*`` — ``lstrip("-* ")``'s old char-set strip
    would eat both leading asterisks (its opening bold marker) while
    leaving the closing ``**`` before "Cosmos DB" untouched, corrupting the
    text. The anchored regex only matches a true marker, so such lines pass
    through unchanged and are still collected as items (e.g. job-experience
    bullets that use bold labels instead of dashes). A ``---``/``***`` divider
    line also starts with ``-``/``*`` but is excluded via ``_HR_RE`` — under
    the old char-set lstrip it stripped down to empty and was implicitly
    dropped, so the anchored marker regex (which doesn't touch it, since a
    divider has no whitespace after its first character) needs an explicit
    check to keep that same behavior.
    """
    items: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("-", "*")) or _HR_RE.match(stripped):
            continue
        item = _BULLET_MARKER_RE.sub("", stripped, count=1).strip()
        if item:
            items.append(item)
    return items


def _find_section(sections: dict[str, str], prefix: str) -> str:
    """Return the first section whose heading starts with ``prefix``."""
    for heading, body in sections.items():
        if heading.startswith(prefix):
            return body
    return ""


def _extract_paragraphs(section: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in section.splitlines():
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                paragraphs.append(" ".join(current))
                current = []
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _join_paragraphs(section: str) -> str:
    paragraphs = _extract_paragraphs(section)
    return "\n\n".join(paragraphs)


def _extract_contact_lines(section: str) -> dict[str, str]:
    contact: dict[str, str] = {}
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            text = stripped.lstrip("- ").strip()
            if ":" in text:
                key, value = text.split(":", 1)
                contact[key.strip().lower().replace(" ", "_")] = value.strip()
    return contact


def _extract_subheadings(section: str) -> dict[str, list[str]]:
    """Extract subheadings and the comma-separated skills that follow.

    Supports two heading styles:
    - ``### Heading`` (markdown h3)
    - ``**Heading:** ...`` (bold-prefix on a single line)
    """
    result: dict[str, list[str]] = {}
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if _HR_RE.match(stripped):
            # A trailing "---"/"***" divider between this section and the
            # next H2 heading is part of the section body as far as
            # _split_sections is concerned — don't let it get swallowed as
            # a trailing "skill" of the last subheading.
            continue
        bold_heading = _BOLD_HEADING_RE.match(stripped)
        if stripped.startswith("### "):
            if current_heading and current_lines:
                result[current_heading] = _split_skill_line(" ".join(current_lines))
            current_heading = stripped.replace("###", "").strip()
            current_lines = []
        elif bold_heading:
            # Flush previous heading before starting a new bold-prefixed one.
            if current_heading and current_lines:
                result[current_heading] = _split_skill_line(" ".join(current_lines))
            current_heading = bold_heading.group(1).strip()
            remainder = bold_heading.group(2)
            current_lines = [remainder] if remainder else []
        elif stripped and not stripped.startswith("#"):
            current_lines.append(stripped)
    if current_heading and current_lines:
        result[current_heading] = _split_skill_line(" ".join(current_lines))
    return result


_BOLD_HEADING_RE = re.compile(r"^\*\*([^*]+):\*\*\s*(.*)$")
_HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")


def _split_skill_line(text: str) -> list[str]:
    """Split a comma/semi/newline separated skill list."""
    parts = re.split(r"[,;·|]", text)
    return [p.strip() for p in parts if p.strip()]


_JOB_HEADING_RE = re.compile(r"^###[ \t]+(.*)$", re.MULTILINE)
_JOB_HEADER_LINE_RE = re.compile(r"^\*\*(.*)\*\*\s*$")


def _extract_experience_sections(text: str) -> list[dict[str, Any]]:
    """Extract ### job entries from the Professional Experience block.

    Scoped to the "## Professional Experience" h2 section via
    ``_split_sections`` — the previous version searched the *whole* document,
    so an unrelated ``### `` heading elsewhere (e.g. "### Backend Development"
    under Technical Skills, which appears earlier in the file) could match
    first and lazily swallow everything up to the next real
    ``**Company | Location | Dates**`` line as its own bogus "title". The
    ``^###[ \\t]+`` anchor (with MULTILINE) additionally ensures a ``#### ``
    bullet sub-heading within a job's body no longer prematurely ends a job
    entry or gets misread as the start of the next one.

    Entries are split on ``### `` boundaries *first*, then each block's
    header line is parsed independently. This matters because not every
    entry follows the ``**Company | Location | Dates**`` shape — the
    "Professional Development & Portfolio Building" entry has a date-only
    header (``**May 2025 – Present**``, no pipes). A single regex spanning
    from one entry's ``### `` heading to its own pipe-delimited header line
    (the previous approach) would, for a pipe-less entry, keep matching
    lazily *past* that entry's boundary and latch onto the *next* real job's
    pipe line instead — silently merging two entries into one bogus record
    (wrong company, and the intervening entry's bullets misattributed to
    it). Splitting on heading boundaries first makes that impossible: each
    block's header is parsed only within its own slice.
    """
    sections = _split_sections(text)
    section_text = sections.get("Professional Experience", "")
    headings = list(_JOB_HEADING_RE.finditer(section_text))
    jobs: list[dict[str, Any]] = []
    for i, heading in enumerate(headings):
        block_end = headings[i + 1].start() if i + 1 < len(headings) else len(section_text)
        block = section_text[heading.end() : block_end]
        company, location, dates, body = _parse_job_header(block)
        jobs.append(
            {
                "title": heading.group(1).strip(),
                "company": company,
                "location": location,
                "dates": dates,
                "bullets": _extract_bullet_list(body),
            }
        )
    return jobs


def _parse_job_header(block: str) -> tuple[str, str, str, str]:
    """Parse a job block's leading bold header line into (company, location, dates, body).

    Handles both header shapes seen in Resume_Snapshot.md: a real employer's
    ``**Company | Location | Dates**`` (3 pipe-separated fields), and the
    non-employer "Professional Development & Portfolio Building" entry's
    date-only ``**Dates**`` (no pipes) — which yields empty company/location.
    Only the first non-blank line of the block is treated as the header, so
    this never reaches past the block it was given.
    """
    lines = block.splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1
    if idx >= len(lines):
        return "", "", "", block

    header_match = _JOB_HEADER_LINE_RE.match(lines[idx].strip())
    if not header_match:
        return "", "", "", block

    fields = [f.strip() for f in header_match.group(1).split("|")]
    body = "\n".join(lines[idx + 1 :])
    if len(fields) >= 3:
        return fields[0], fields[1], fields[2], body
    return "", "", fields[0], body


def _extract_education_sections(text: str) -> list[dict[str, str]]:
    """Extract education entries under a dedicated section."""
    sections = _split_sections(text)
    edu_section = sections.get("Education", "")
    entries: list[dict[str, str]] = []
    for line in edu_section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("-"):
            entries.append({"credential": stripped.lstrip("- ").strip()})
        elif entries:
            entries[-1]["notes"] = stripped
    return entries
