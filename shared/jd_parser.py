"""Job-description markdown parsing shared by fit-check and gap-analysis."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedJD:
    """Structured result of parsing a JD markdown file."""

    required: list[str]
    nice_to_have: list[str]
    title: str
    company: str
    location: str | None = None
    job_id: str | None = None


_REQUIRED_HEADING_RE = re.compile(
    r"(requirements?|must haves?|what you.*need|what you.?ll bring|"
    r"what we.?re looking for|essential|required skills?)",
    re.IGNORECASE,
)
_NICE_HEADING_RE = re.compile(r"(nice to have|preferred|bonus|asset|desirable)", re.IGNORECASE)
# Common non-requirement section headings that follow a requirements list in
# real-world postings (benefits/perks/company-blurb sections). Without this,
# `section` never resets once set, so a heading-shaped line the parser
# doesn't otherwise recognize (e.g. "What we offer") leaves the *following*
# section's bullets miscategorized as required/nice-to-have indefinitely —
# see tests/fixtures for a real posting that silently absorbed its entire
# benefits list as "required skills" this way.
_SECTION_END_HEADING_RE = re.compile(
    r"(what we offer|benefits?|perks|compensation|why (?:join|work)|"
    r"about (?:us|the company)|our culture|company overview)",
    re.IGNORECASE,
)
# A heading-shaped line doesn't end in sentence punctuation — "## Nice to
# Have" / "**Requirements:**" don't, but a prose sentence that happens to
# mention "a bonus" or "nice to have" in passing does. This alone can't tell
# a heading from prose in general, but it's a cheap, low-risk guard against
# the specific, demonstrated failure mode of a descriptive sentence hijacking
# section-detection mid-paragraph (see tests/test_jd_parser.py's baseline
# characterization tests).
_SENTENCE_PUNCT_RE = re.compile(r"[.!?]\s*$")
_YEARS_PREFIX_RE = re.compile(
    r"^\d+\s*(?:[-+]|to\s*\d+)?\s*(?:years?|yrs?)\s*(?:of\s*)?",
    re.IGNORECASE,
)
_LEADING_PLUS_RE = re.compile(r"^\+\s*")
_BARE_YEARS_RE = re.compile(r"^(?:years?|yrs?)\s*(?:of\s*)?", re.IGNORECASE)
_PAREN_YEARS_RE = re.compile(r"\(\d+\+?\s*years?.*\)", re.IGNORECASE)
_SPLIT_COMPOUND_RE = re.compile(r"[/;]|\s+or\s+|\s+and\s+")
_BULLET_RE = re.compile(r"^[-•]|^\d+[.)]")

_TITLE_H1_RE = re.compile(r"(?:^#\s+)([^\n]+)", re.IGNORECASE | re.MULTILINE)
_TITLE_INLINE_RE = re.compile(r"(?:job title|position|role)[:\s]+([^\n]+)", re.IGNORECASE)
_COMPANY_BOLD_RE = re.compile(r"\*\*[Cc]ompany:\*\*\s*([^\n]+)")
_COMPANY_INLINE_RE = re.compile(r"(?:company|at)[:\s]*([A-Z][A-Za-z0-9\s&,\.]+)")
_TITLE_COMPANY_SPLIT_RE = re.compile(r"\s+[—–-]\s+")
_LOCATION_BOLD_RE = re.compile(r"\*\*[Ll]ocation:\*\*\s*([^\n]+)")
_JOB_ID_BOLD_RE = re.compile(
    r"\*\*(?:[Jj]ob\s*ID|[Rr]eq(?:uisition)?\s*ID|[Jj]ob\s*Number):\*\*\s*([^\n]+)"
)


def _strip_years_prefix(item: str) -> str:
    item = _YEARS_PREFIX_RE.sub("", item).strip(" ,./:;")
    item = _LEADING_PLUS_RE.sub("", item)
    item = _BARE_YEARS_RE.sub("", item).strip(" ,./:;")
    item = _PAREN_YEARS_RE.sub("", item).strip(",. ")
    return item


def _is_bullet(line: str) -> bool:
    return bool(_BULLET_RE.match(line))


def _split_required_or_nice(item: str, section: str, required: list[str], nice: list[str]) -> None:
    for piece in _SPLIT_COMPOUND_RE.split(item):
        piece = piece.strip(" ,./:;")
        if len(piece) < 2:
            continue
        if section == "required":
            required.append(piece)
        else:
            nice.append(piece)


def parse_jd(text: str) -> ParsedJD:
    """Naively extract required, nice skills, title and company from JD text.

    Returns cleaned skill phrases that are short enough to be meaningful tokens
    for substring matching against the profile bundle.
    """
    required: list[str] = []
    nice: list[str] = []
    section: str | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        lower = stripped.lower()
        if not stripped:
            continue
        is_bullet = _is_bullet(stripped)
        # A bullet is content, never a section heading, even if its own text
        # happens to contain a heading-like phrase (e.g. a required-skill
        # bullet noting something is "nice to have but preferred").
        looks_like_heading = not is_bullet and not _SENTENCE_PUNCT_RE.search(stripped)
        if looks_like_heading and _REQUIRED_HEADING_RE.search(lower):
            section = "required"
            continue
        if looks_like_heading and _NICE_HEADING_RE.search(lower):
            section = "nice"
            continue
        # Reset the section on a "What we offer" / "Benefits" / etc. heading
        # so its following bullets (which would otherwise be absorbed into the
        # most-recent required/nice section) don't get miscategorized.
        if looks_like_heading and _SECTION_END_HEADING_RE.search(lower):
            section = None
            continue
        if section and is_bullet:
            item = stripped.lstrip("-•1234567890.) ").strip()
            item = _strip_years_prefix(item)
            _split_required_or_nice(item, section, required, nice)

    title_match = _TITLE_H1_RE.search(text) or _TITLE_INLINE_RE.search(text)
    title = title_match.group(1).strip() if title_match else "Unknown Role"
    title = _TITLE_COMPANY_SPLIT_RE.split(title, maxsplit=1)[0].strip()

    company_match = _COMPANY_BOLD_RE.search(text) or _COMPANY_INLINE_RE.search(text)
    company = company_match.group(1).strip() if company_match else "Unknown Company"
    company = _TITLE_COMPANY_SPLIT_RE.split(company, maxsplit=1)[0].strip()

    location_match = _LOCATION_BOLD_RE.search(text)
    location = location_match.group(1).strip() if location_match else None

    job_id_match = _JOB_ID_BOLD_RE.search(text)
    job_id = job_id_match.group(1).strip() if job_id_match else None

    return ParsedJD(
        required=required,
        nice_to_have=nice,
        title=title,
        company=company,
        location=location,
        job_id=job_id,
    )


def looks_unknown(value: str | None) -> bool:
    """Return True if ``value`` is an empty string or a ``Unknown …`` placeholder.

    ``parse_jd`` returns ``"Unknown Company"`` / ``"Unknown Role"`` when it
    can't extract those fields, but a JD markdown file with a blank
    ``**Company:**`` line parses to ``""``. Callers that want to treat both
    the same way (i.e. "this isn't really a JD") can use this helper.
    """
    if not value:
        return True
    return value.startswith("Unknown")
