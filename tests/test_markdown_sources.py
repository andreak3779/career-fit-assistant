import pytest

from shared.markdown_sources import load_sources


@pytest.fixture
def repo_root(tmp_path):
    """Create a minimal monorepo structure for parser tests."""
    p2 = tmp_path / "project-2-profile-learning-hub"
    p2.mkdir(parents=True)
    (p2 / "profile-facts.md").write_text(
        "---\n"
        "certs:\n"
        "  - code: AZ-900\n"
        "    status: certified\n"
        "    date: 2026-04-18\n"
        "  - code: AI-200\n"
        "    status: in_progress\n"
        "---\n"
        "\n# Profile Facts\n\n## Cert Status\n| Cert | Status |\n|---|---|\n"
        "| AZ-900 | Certified April 18, 2026 |\n| AI-200 | Active target |\n\n"
        "## Key Differentiators\n- Full-stack depth\n- Legacy modernization\n\n"
        "## Known Genuine Gaps\n- Kubernetes\n- Python\n\n"
    )
    (p2 / "Resume_Snapshot.md").write_text(
        "# Sarah\n\n**Senior Dev | .NET**\n\n- Email: a@example.com\n"
        "- Phone: 204-555-0100\n\n---\n\n## Summary\nSenior dev.\n\n"
        "## Technical Skills\n### Backend\nC#, Python\n"
    )
    (p2 / "skills-summary.md").write_text(
        "# Skills\n**Status: 215 courses completed · 49 in progress · 27 labs · 291 total**\n\n"
        "## Key Skills for Resume / Job Applications\n**Cloud:** Azure, Cosmos DB\n\n"
        "## AI-200 Domain Coverage (Azure AI Cloud Developer Associate)\n"
        "| Domain | Status |\n|---|---|\n| RAG | Partial |\n"
    )
    (p2 / "github-repos.md").write_text(
        "# Portfolio\n\n## SampleApp\nURL: https://github.com/sarah-ashford-dev/SampleApp\n"
        "Stack: C# · .NET 10 · Blazor\nDescription: Legacy modernization demo.\n"
    )
    p1 = tmp_path / "project-1-application-engine"
    (p1 / "reference").mkdir(parents=True, exist_ok=True)
    (p1 / "reference" / "star-bank.md").write_text(
        "# STAR Story Bank\n\n## Story 1 — Test Story\n\n"
        "**Use for:** Test\n\n**JD tags:** `sql` `python`\n\n"
        "**Situation:**\n\nTest situation.\n\n"
        "**Task:**\n\nTest task.\n\n"
        "**Action:**\n\nTest action.\n\n"
        "**Result:**\n\nTest result.\n\n"
    )
    return tmp_path


def test_load_sources_smoke(repo_root):
    sources = load_sources(repo_root)
    assert sources.profile_facts["differentiators"]
    assert sources.resume_snapshot["summary"] == "Senior dev."
    assert sources.skills_summary["ai200_coverage"]
    assert sources.github_repos["repos"]


def test_yaml_certs_parsed(repo_root):
    sources = load_sources(repo_root)
    certs = sources.profile_facts["certs"]
    assert len(certs) == 2
    assert certs[0]["code"] == "AZ-900"
    assert certs[0]["status"] == "certified"
    assert str(certs[0]["date"]) == "2026-04-18"
    assert certs[1]["code"] == "AI-200"
    assert certs[1]["status"] == "in_progress"


def test_markdown_only_profile_facts_returns_empty_certs(capsys):
    """Profile-facts.md without YAML frontmatter must produce empty certs."""
    from shared.markdown_sources import parse_profile_facts

    text = (
        "# Profile Facts\n\n## Cert Status\n| Cert | Status |\n|---|---|\n"
        "| AZ-900 | Certified April 18, 2026 |\n"
    )
    parsed = parse_profile_facts(text)
    assert parsed["certs"] == []
    assert parsed["cert_status_table"][0]["Cert"] == "AZ-900"


def test_resume_contact_parsed(repo_root):
    sources = load_sources(repo_root)
    assert sources.resume_snapshot["contact"]["email"] == "a@example.com"
    assert sources.resume_snapshot["contact"]["phone"] == "204-555-0100"


def test_commented_out_repo_is_not_parsed():
    """A repo wrapped in an HTML comment (e.g. OldApp, retired-but-kept-for-later)
    must never surface as an active portfolio entry — the section-splitter has no
    concept of HTML comments on its own, so parse_github_repos must strip them first."""
    from shared.markdown_sources import parse_github_repos

    text = (
        "# Portfolio\n\n"
        "<!-- COMMENTED OUT — OldApp (restore when ready)\n"
        "## OldApp\n"
        "URL: https://github.com/sarah-ashford-dev/OldApp\n"
        "Stack: Angular\n"
        "Description: Retired.\n"
        "-->\n\n"
        "## SampleApp\n"
        "URL: https://github.com/sarah-ashford-dev/SampleApp\n"
        "Stack: C#\n"
        "Description: Active.\n"
    )
    repos = parse_github_repos(text)["repos"]
    names = [r["name"] for r in repos]
    assert "OldApp" not in names
    assert "SampleApp" in names


def test_trailing_divider_does_not_bleed_into_last_subheading():
    """A "---" divider between the last ### subheading and the next ## heading is
    part of the section body as _split_sections sees it — _extract_subheadings must
    not treat it as one more comma-split "skill" of the last subheading."""
    from shared.markdown_sources import _extract_subheadings

    section = "### Tools & Utilities\nVS Code, SonarQube\n\n---\n"
    result = _extract_subheadings(section)
    assert result["Tools & Utilities"] == ["VS Code", "SonarQube"]


# ── Regression tests: _extract_experience_sections scoping/lookahead bug ────
#
# The previous version ran its regex over the *whole* Resume_Snapshot.md
# (not scoped to "## Professional Experience"), so a "### " heading earlier
# in the file (e.g. a Technical Skills subheading) could match first and
# lazily swallow everything up to the next real "**Company | Loc | Dates**"
# line as a bogus "title" — and the end-of-body lookahead matched "###" as a
# substring of "#### ", so a bullet sub-heading inside a job's body could
# prematurely end that entry and be misread as the start of the next one.
# Confirmed against the real Resume_Snapshot.md this silently turned
# course-only skills (GraphQL, Terraform, Kubernetes, ...) into spurious
# "production match" evidence via shared.fit_engine._has_skill, since it
# reads each job's title + bullets for skill terms.

_EXPERIENCE_BUG_FIXTURE = (
    "# Sarah\n\n**Senior Dev | .NET**\n\n---\n\n"
    "## Summary\nSenior dev.\n\n---\n\n"
    "## Technical Skills\n\n"
    "### Backend Development\n"
    "C#, ASP.NET Core, GraphQL (course-level)\n\n"
    "### Cloud & Azure\n"
    "Azure, Terraform (course-level)\n\n"
    "---\n\n"
    "## Professional Experience\n\n"
    "### Senior Developer\n"
    "**Acme Corp | Remote | Jan 2023 – Present**\n\n"
    "#### Backend Work\n"
    "- Built APIs with C# and ASP.NET Core\n"
    "#### Frontend Work\n"
    "- Built UI with Angular\n\n"
    "### Junior Developer\n"
    "**Beta Inc | Remote | Jan 2020 – Dec 2022**\n\n"
    "- Wrote SQL queries\n\n"
    "---\n\n"
    "## Education and Certifications\n\nSome school.\n"
)


def test_experience_extraction_is_scoped_to_professional_experience_section():
    """A Technical Skills "### " subheading earlier in the file must not be
    picked up as a phantom job entry, and must not contaminate the first
    real job's title."""
    from shared.markdown_sources import _extract_experience_sections

    jobs = _extract_experience_sections(_EXPERIENCE_BUG_FIXTURE)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Senior Developer"
    assert jobs[0]["company"] == "Acme Corp"
    assert "Backend Development" not in jobs[0]["title"]
    assert "GraphQL" not in jobs[0]["title"]


def test_experience_extraction_does_not_split_on_bullet_subheadings():
    """A "#### " bullet sub-heading inside a job's body (e.g. "#### Backend
    Work") must not end that job entry early or be misread as a new "### "
    job heading — both bullet groups belong to the first job."""
    from shared.markdown_sources import _extract_experience_sections

    jobs = _extract_experience_sections(_EXPERIENCE_BUG_FIXTURE)
    assert len(jobs) == 2
    bullets = " ".join(jobs[0]["bullets"])
    assert "C#" in bullets
    assert "Angular" in bullets  # from the second #### subsection, same job
    assert jobs[1]["title"] == "Junior Developer"
    assert jobs[1]["company"] == "Beta Inc"


def test_experience_extraction_handles_date_only_header_no_pipes():
    """A job block whose header has no "|" fields (e.g. the non-employer
    "Professional Development & Portfolio Building" resume entry, which is
    just "**May 2025 - Present**") must parse as its own entry with empty
    company/location and the bold line as dates — never reach past its own
    block into the next "### " job's "**Company | Location | Dates**" line."""
    from shared.markdown_sources import _extract_experience_sections

    text = (
        "## Professional Experience\n\n"
        "### Professional Development & Portfolio Building\n"
        "**May 2025 - Present**\n\n"
        "**Azure & Cloud Services:** Cosmos DB, Redis, and Azure Functions "
        "through targeted coursework.\n\n"
        "---\n\n"
        "### Senior Developer\n"
        "**Acme Corp | Remote | Jan 2023 - Present**\n\n"
        "- Built APIs with C#\n\n"
        "## Education and Certifications\n\nSome school.\n"
    )
    jobs = _extract_experience_sections(text)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Professional Development & Portfolio Building"
    assert jobs[0]["company"] == ""
    assert jobs[0]["location"] == ""
    assert jobs[0]["dates"] == "May 2025 - Present"
    assert jobs[0]["bullets"] == [
        "**Azure & Cloud Services:** Cosmos DB, Redis, and Azure Functions "
        "through targeted coursework."
    ]
    assert jobs[1]["title"] == "Senior Developer"
    assert jobs[1]["company"] == "Acme Corp"
    assert jobs[1]["location"] == "Remote"
    assert jobs[1]["dates"] == "Jan 2023 - Present"
    assert jobs[1]["bullets"] == ["Built APIs with C#"]


def test_extract_bullet_list_preserves_bold_label_opening_marker():
    """A bold-labeled paragraph bullet like "**Label:** text" must keep its
    opening "**" — the old char-set lstrip("-* ") ate both leading asterisks
    (mistaking them for repeated bullet markers) while leaving the closing
    "**" before "text" untouched, corrupting the item to "Label:** text"."""
    from shared.markdown_sources import _extract_bullet_list

    section = "**Azure & Cloud Services:** Cosmos DB, Redis, and Azure Functions.\n"
    assert _extract_bullet_list(section) == [
        "**Azure & Cloud Services:** Cosmos DB, Redis, and Azure Functions."
    ]


def test_extract_bullet_list_still_strips_real_dash_and_star_markers():
    """Genuine "- " and "* " list markers are still stripped as before."""
    from shared.markdown_sources import _extract_bullet_list

    section = "- Built APIs with C#\n* Wrote SQL queries\n"
    assert _extract_bullet_list(section) == ["Built APIs with C#", "Wrote SQL queries"]
