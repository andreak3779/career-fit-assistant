#!/usr/bin/env python3
"""End-to-end tests for build_bundles.py."""

import os
from pathlib import Path

import pytest


@pytest.fixture
def repo_root(tmp_path):
    """Create a minimal monorepo and run the bundle builder."""
    p2 = tmp_path / "project-2-profile-learning-hub"
    p2.mkdir(parents=True)
    p2.joinpath("scripts").mkdir(parents=True)

    (p2 / "profile-facts.md").write_text(
        "---\n"
        "certs:\n"
        "  - code: AZ-900\n"
        "    status: certified\n"
        "    date: 2026-04-18\n"
        "    credential_url: https://learn.microsoft.com/api/credentials/share/en-ca/SarahAshford-1234/7A3C2E19B4F0D821?sharingId=4C91E7A2B0D3F5C6\n"
        "  - code: AI-200\n"
        "    status: in_progress\n"
        "---\n"
        "\n# Profile Facts\n\n## Cert Status\n| Cert | Status |\n|---|---|\n"
        "| AZ-900 | Certified April 18, 2026 — [Credential](https://learn.microsoft.com/api/credentials/share/en-ca/SarahAshford-1234/7A3C2E19B4F0D821?sharingId=4C91E7A2B0D3F5C6) |\n"
        "| AI-200 | Active target |\n\n"
        "## Key Differentiators\n- Full-stack depth\n- Legacy modernization\n- Pace of learning: 215 courses completed + 49 in progress + 27 labs = 291 total\n\n"
        "## Known Genuine Gaps\n- Kubernetes — course-level coverage\n\n"
    )
    (p2 / "Resume_Snapshot.md").write_text(
        "# Sarah\n\n**Senior Dev | .NET**\n\n- Email: a@example.com\n"
        "- Phone: 204-555-0100\n\n---\n\n## Summary\nSenior dev.\n\n"
        "## Technical Skills\n### Backend\nC#, Python\n"
    )
    (p2 / "skills-summary.md").write_text(
        "# Skills\n\n## Key Skills for Resume / Job Applications\n**Cloud:** Azure, Cosmos DB\n\n"
        "## AI-200 Domain Coverage (Azure AI Cloud Developer Associate)\n"
        "| Domain | Status |\n|---|---|\n| RAG | Partial |\n"
    )
    (p2 / "github-repos.md").write_text(
        "# Portfolio\n\n## SampleApp\nURL: https://github.com/sarah-ashford-dev/SampleApp\n"
        "Stack: C# · .NET 10 · Blazor\nDescription: Legacy modernization demo.\n"
    )

    p1 = tmp_path / "project-1-application-engine"
    (p1 / "reference").mkdir(parents=True)
    (p1 / "reference" / "star-bank.md").write_text(
        "# STAR Story Bank\n\n## Story 1 — Test Story\n\n"
        "**Use for:** Test\n\n**JD tags:** `sql` `python`\n\n"
        "**Situation:**\n\nTest situation.\n\n"
        "**Task:**\n\nTest task.\n\n"
        "**Action:**\n\nTest action.\n\n"
        "**Result:**\n\nTest result.\n\n"
        "**Adapt when:**\n- Role emphasizes Python — mention the analytical approach\n"
    )

    script_src = (
        Path(__file__).resolve().parents[1]
        / "project-2-profile-learning-hub"
        / "skills"
        / "profile_hub_bundle_generator"
        / "scripts"
        / "build_bundles.py"
    )
    script_dst = p2 / "scripts" / "build_bundles.py"
    script_dst.write_text(script_src.read_text())

    import subprocess
    import sys

    project_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(project_root) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, str(script_dst), str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return tmp_path


def test_profile_bundle_created_from_fixture(repo_root):
    assert (repo_root / "outputs" / "profile-bundle.json").exists()


def test_project_stack_items_are_stripped_of_whitespace(repo_root):
    """Regression test: splitting "C# · .NET 10 · Blazor" on "·" then "," left
    every item but the first with a leading space (" .NET 10", " Blazor") —
    invisible in JSON but produces doubled spaces ("C#  ·  .NET 10") wherever
    a renderer rejoins the list with " · "."""
    import json

    data = json.loads((repo_root / "outputs" / "profile-bundle.json").read_text())
    stack = data["portfolio_projects"][0]["stack"]
    assert stack == [s.strip() for s in stack]


def test_presence_bundle_safe_from_fixture(repo_root):
    import json

    data = json.loads((repo_root / "outputs" / "presence-bundle.json").read_text())
    assert "email" not in str(data)
    assert "phone" not in str(data)
    assert data["cert_registry"][0]["code"] == "AZ-900"


def test_profile_bundle_resume_has_star_stories_from_fixture(repo_root):
    """Regression test for duplicated star_stories construction bug.

    Before the refactor, build() built star_stories twice and the second
    inline construction was never assigned to Resume, so
    ``profile.resume.star_stories`` was always empty. This test ensures the
    typed StarStory list flows into the bundle and is serialised.
    """
    import json

    data = json.loads((repo_root / "outputs" / "profile-bundle.json").read_text())
    assert data["resume"]["star_stories"]
    assert data["resume"]["star_stories"][0]["title"] == "Test Story"


def test_profile_bundle_star_story_adapt_when_round_trips(repo_root):
    """``adapt_when`` bullets parsed from star-bank.md must survive the
    markdown -> StarStory -> JSON bundle pipeline, not just the parser."""
    import json

    data = json.loads((repo_root / "outputs" / "profile-bundle.json").read_text())
    story = data["resume"]["star_stories"][0]
    assert story["adapt_when"] == ["Role emphasizes Python — mention the analytical approach"]
    assert "python" in data["resume"]["star_stories"][0]["jd_tags"]
