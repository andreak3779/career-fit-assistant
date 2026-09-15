"""Tests for skills/profile_hub_bundle_generator/scripts/render_md_bundles.py.

The module lives under skills/.../scripts/, outside the installed package
tree (same as build_bundles.py), so it's loaded by file path rather than
imported by dotted name.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from shared.models import Cert, CertStatus

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = (
    ROOT
    / "project-2-profile-learning-hub"
    / "skills"
    / "profile_hub_bundle_generator"
    / "scripts"
    / "render_md_bundles.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("render_md_bundles", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def r():
    return _load_module()


def test_cert_status_short_skips_not_pursuing():
    from shared.cert_status import cert_status_short

    certs = [
        Cert(code="AZ-900", status=CertStatus.CERTIFIED, date=date(2026, 4, 18)),
        Cert(code="AI-200", status=CertStatus.IN_PROGRESS),
        Cert(code="AZ-204", status=CertStatus.NOT_PURSUING),
    ]
    assert cert_status_short(certs) == "AZ-900 Certified · AI-200 in progress"


def test_cert_row_certified_uses_date_not_notes(r):
    c = Cert(
        code="AZ-900",
        status=CertStatus.CERTIFIED,
        date=date(2026, 4, 18),
        credential_url="https://example.com/cred",
        notes="should not appear",
    )
    row = r._cert_row(c)
    assert "Certified April 18, 2026" in row
    assert "[Credential](https://example.com/cred)" in row
    assert "should not appear" not in row


def test_cert_row_not_pursuing_uses_notes_verbatim(r):
    c = Cert(code="AZ-204", status=CertStatus.NOT_PURSUING, notes="Not pursuing — retired")
    assert r._cert_row(c) == "| AZ-204 | Not pursuing — retired |"


def test_course_count_sentence_parses_pace_of_learning_bullet():
    from shared.copy_fragments import compute_copy_fragments

    differentiators = [
        "Pace of learning: 218 courses completed + 53 in progress + 27 labs "
        "(26 completed, 1 in progress) = **298 total** since Oct 2025"
    ]
    fragments = compute_copy_fragments(differentiators, [], None)
    assert fragments["course_count_sentence"] == (
        "218 Pluralsight courses completed and 53 more in progress, "
        "plus 27 hands-on labs (26 completed, 1 in progress) — 298 total"
    )


def test_github_copilot_and_leadership_counts_extracted():
    from shared.copy_fragments import compute_copy_fragments

    differentiators = [
        "GitHub Copilot: 19 courses — enterprise, CI/CD, security, AI agents",
        "Communication: 19 leadership/communication Pluralsight courses",
    ]
    fragments = compute_copy_fragments(differentiators, [], None)
    assert fragments["github_copilot_course_count"] == "19"
    assert fragments["leadership_course_count"] == "19"


def test_strip_last_modified_line_removes_only_that_line(r):
    text = "# Sarah\n\n---\n\n**Last Modified: August 23, 2026**\n\n---\n\n## Summary\nHi.\n"
    stripped = r._strip_last_modified_line(text)
    assert "Last Modified" not in stripped
    assert "## Summary" in stripped
    assert "Hi." in stripped


def test_second_nonblank_line_skips_headings_and_blanks(r):
    text = "# Sarah\n\n**Senior Dev | .NET**\n\nTechnology expert.\n\n## Summary\n"
    assert r._second_nonblank_line(text) == "Technology expert."


def test_pipeline_end_to_end_writes_matching_versions_and_clean_pii(tmp_path):
    """Full build_bundles.py -> render_md_bundles.py run against a minimal fixture
    repo: both .md bundles must share one bundle_version and pass the PII gate."""
    p2 = tmp_path / "project-2-profile-learning-hub"
    p2.mkdir(parents=True)
    (p2 / "profile-facts.md").write_text(
        "---\n"
        "certs:\n"
        "  - code: AZ-900\n"
        "    status: certified\n"
        "    date: 2026-04-18\n"
        "    credential_url: https://learn.microsoft.com/api/credentials/share/en-ca/x/1?sharingId=2\n"
        "  - code: AI-200\n"
        "    status: in_progress\n"
        "---\n"
        "\n# Profile Facts\n\n## Cert Status\n| Cert | Status |\n|---|---|\n"
        "| AZ-900 | Certified April 18, 2026 |\n| AI-200 | Active target |\n"
        "| Azure coursework | 10 courses + 2 labs completed |\n\n"
        "## Key Differentiators\n"
        "- Full-stack depth: ASP.NET Core + Angular\n"
        "- Legacy modernization: one migration\n"
        "- SQL Server: 10+ years\n"
        "- TDD: xUnit\n"
        "- GitHub Copilot: 5 courses\n"
        "- Prompt Engineering: 1 course\n"
        "- AI/LLM depth: none\n"
        "- Communication: 3 leadership/communication Pluralsight courses\n"
        "- Pace of learning: 10 courses completed + 2 in progress + 1 labs "
        "(1 completed, 0 in progress) = **13 total**\n\n"
        "## Known Genuine Gaps\n- Kubernetes — course-level\n\n"
    )
    (p2 / "Resume_Snapshot.md").write_text(
        "# Sarah Test\n\n**Senior Dev | .NET**\n\nTagline here.\n\n"
        "- Email: a@example.com\n- Phone: 204-555-0100\n\n---\n\n"
        "**Last Modified: August 23, 2026**\n\n---\n\n"
        "## Summary\nSenior dev.\n\n## Technical Skills\n### Backend\nC#, Python\n"
    )
    (p2 / "skills-summary.md").write_text(
        "# Skills\n**Status: 10 courses completed · 2 in progress · 1 labs · 13 total**\n\n"
        "## Key Skills for Resume / Job Applications\n**Cloud:** Azure\n\n"
        "## AI-200 Domain Coverage (Azure AI Cloud Developer Associate)\n"
        "| Domain | Status |\n|---|---|\n| RAG | Partial |\n"
    )
    (p2 / "github-repos.md").write_text(
        "# Portfolio\n\n## SampleApp\nURL: https://github.com/sarah-ashford-dev/SampleApp\n"
        "Stack: C# · .NET 10\nDescription: Legacy modernization demo.\n"
    )
    p1 = tmp_path / "project-1-application-engine"
    p1.mkdir(parents=True)
    p3 = tmp_path / "project-3-presence-identity"
    p3.mkdir(parents=True)
    (p1 / "reference").mkdir(parents=True, exist_ok=True)
    (p1 / "reference" / "star-bank.md").write_text("")

    build_script = (
        ROOT
        / "project-2-profile-learning-hub"
        / "skills"
        / "profile_hub_bundle_generator"
        / "scripts"
        / "build_bundles.py"
    )
    subprocess.run([sys.executable, str(build_script), str(tmp_path)], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(_MODULE_PATH), str(tmp_path)], cwd=ROOT, check=True)

    app_engine_text = (p1 / "app-engine-bundle.md").read_text()
    presence_text = (p3 / "presence-bundle.md").read_text()

    def _version(text: str) -> str:
        for line in text.splitlines():
            if line.startswith("bundle_version:"):
                return line.split(":", 1)[1].strip()
        raise AssertionError("bundle_version line not found")

    assert _version(app_engine_text) == _version(presence_text)
    assert "a@example.com" not in presence_text
    assert "204-555-0100" not in presence_text
