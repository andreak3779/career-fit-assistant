"""Tests for shared.jd_parser."""

from __future__ import annotations

from pathlib import Path

from shared.jd_parser import parse_jd

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

SAMPLE_JD = """\
# Senior Full-Stack .NET Developer

**Company:** Contoso Cloud Solutions
**Location:** Remote

## Required Skills
- 5+ years C# / .NET Core / ASP.NET Core Web API
- Strong Azure fundamentals (App Service, Azure Functions, Cosmos DB)
- Angular or React frontend development
- SQL Server / T-SQL query optimization
- CI/CD with GitHub Actions and Docker
- Unit testing with xUnit and integration testing
- REST API design and microservices architecture
- Legacy system modernization experience

## Nice to Have
- Azure AI / OpenAI integration
- Blazor WebAssembly
- Kubernetes / container orchestration
- Python scripting for automation
- GitHub Copilot and prompt engineering experience
- MongoDB or other NoSQL databases
"""


def test_required_and_nice_separated() -> None:
    parsed = parse_jd(SAMPLE_JD)
    joined_required = " ".join(parsed.required)
    joined_nice = " ".join(parsed.nice_to_have)
    assert "Azure fundamentals" in joined_required
    assert "Kubernetes" in joined_nice
    assert "Azure AI" in joined_nice
    assert "Blazor WebAssembly" in joined_nice


def test_years_prefix_stripped() -> None:
    parsed = parse_jd(SAMPLE_JD)
    # The 5+ years prefix on the first item should be gone.
    assert not any(item.lower().startswith("5") for item in parsed.required)


def test_compound_phrases_split() -> None:
    parsed = parse_jd(SAMPLE_JD)
    # "Angular or React frontend development" splits on "or".
    assert "Angular" in parsed.required or "React" in parsed.required
    # "C# / .NET Core / ASP.NET Core Web API" splits on "/".
    assert any("C#" in item for item in parsed.required)
    assert any(".NET Core" in item for item in parsed.required)


def test_title_and_company_extracted() -> None:
    parsed = parse_jd(SAMPLE_JD)
    assert parsed.title == "Senior Full-Stack .NET Developer"
    assert parsed.company == "Contoso Cloud Solutions"


def test_unknown_role_when_no_title() -> None:
    parsed = parse_jd("Some prose with no heading or company line.")
    assert parsed.title == "Unknown Role"
    assert parsed.company == "Unknown Company"


def test_location_extracted_from_bold_line() -> None:
    parsed = parse_jd(SAMPLE_JD)
    assert parsed.location == "Remote"


def test_location_is_none_when_absent() -> None:
    parsed = parse_jd("Some prose with no location line.")
    assert parsed.location is None


def test_job_id_extracted_from_bold_line() -> None:
    text = (
        "# Senior Developer\n\n**Company:** Acme Corp\n**Location:** Remote\n"
        "**Job ID:** REQ-4821\n\n## Required Skills\n- C#\n"
    )
    parsed = parse_jd(text)
    assert parsed.job_id == "REQ-4821"


def test_job_id_is_none_when_absent() -> None:
    parsed = parse_jd(SAMPLE_JD)
    assert parsed.job_id is None


# ── Regression tests for atypical-JD-formatting fixes ───────────────────────
#
# job_description_fit's readiness plan found three concrete failure modes on
# atypically-formatted real JDs. Two are fixed here (heading regexes broadened
# for unconventional phrasing; a line that's already a bullet, or that ends
# in sentence punctuation, is never treated as a section-heading trigger even
# if it contains a heading-like word). The third — a JD with no recognizable
# section headings at all — is a known, accepted limitation: it now fails
# safely (nothing captured) instead of the old behavior (silently
# miscategorizing every bullet as nice-to-have). A general-purpose rewrite to
# handle heading-less prose JDs is out of scope; `parse_jd`'s docstring
# self-describes as "Naively extract..." for a reason.


def test_prose_paragraph_with_bonus_keyword_no_longer_hijacks_the_nice_heading() -> None:
    """A prose sentence mentioning "a bonus" ends in a period, so the
    sentence-punctuation guard now keeps it from being misread as a Nice to
    Have heading. This JD has no real section headings at all, so nothing is
    captured — a safe, honest failure mode, not the old miscategorization
    into nice_to_have."""
    text = (FIXTURES_DIR / "atypical-no-headings-jd.md").read_text(encoding="utf-8")
    parsed = parse_jd(text)
    assert parsed.required == []
    assert parsed.nice_to_have == []


def test_unconventional_heading_phrasing_is_recognized() -> None:
    """ "What You'll Bring" now matches the broadened `_REQUIRED_HEADING_RE`,
    so its bullets are captured as required skills instead of silently
    dropped."""
    text = (FIXTURES_DIR / "atypical-whatyoullbring-jd.md").read_text(encoding="utf-8")
    parsed = parse_jd(text)
    joined_required = " ".join(parsed.required)
    assert "ASP.NET Core" in joined_required
    assert "Azure" in joined_required
    assert "SQL Server" in joined_required
    assert "Kubernetes" in " ".join(parsed.nice_to_have)


def test_nested_nice_to_have_phrase_no_longer_flips_section_mid_required_list() -> None:
    """A required-section bullet containing the phrase "nice to have" (e.g.
    "Kubernetes experience is nice to have but strongly preferred") is a
    bullet, not a heading, so it no longer flips `section` — every bullet in
    the Required Skills list, including that one, stays required. Whether
    that specific skill should really count as required is exactly the kind
    of judgment call left to the SKILL.md's sanity-check fallback, not
    something the parser should resolve with keyword heuristics."""
    text = (FIXTURES_DIR / "atypical-nested-nice-to-have-jd.md").read_text(encoding="utf-8")
    parsed = parse_jd(text)
    joined_required = " ".join(parsed.required)
    assert "Kubernetes" in joined_required
    assert "SQL Server" in joined_required
    assert "GitHub Actions" in joined_required
    assert parsed.nice_to_have == ["Python scripting for automation"]
