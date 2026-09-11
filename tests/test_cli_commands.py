"""Smoke tests for the career_fit_api CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"
FIXTURE_JD = FIXTURES_DIR / "sample-jd.md"


from project_1_application_engine.skills.gap_analysis_job_description.scripts.gap_analysis import (
    main as gap_analysis_main,
)
from project_1_application_engine.skills.job_description_fit.scripts.fit_check import (
    main as fit_check_main,
)
from project_3_presence_identity.skills.update_github_profile.scripts.generate_github import (
    main as github_main,
)
from project_3_presence_identity.skills.update_linkedin_profile.scripts.generate_linkedin import (
    main as linkedin_main,
)

from cli.career_fit_api import _build as cli_build
from cli.career_fit_api import main as cli_main


def test_build_refreshes_markdown_bundles_not_just_json(tmp_path: Path) -> None:
    """`build` must also refresh app-engine-bundle.md / presence-bundle.md,
    not just outputs/*.json — every SKILL.md workflow reads the markdown,
    and a prior version of `_build()` silently left it stale."""
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

    app_engine_bundle = p1 / "app-engine-bundle.md"
    presence_bundle = p3 / "presence-bundle.md"
    assert not app_engine_bundle.exists()
    assert not presence_bundle.exists()

    assert cli_build(tmp_path) == 0

    assert (tmp_path / "outputs" / "profile-bundle.json").exists()
    assert app_engine_bundle.exists()
    assert presence_bundle.exists()
    assert "bundle_version:" in app_engine_bundle.read_text(encoding="utf-8")
    assert "bundle_version:" in presence_bundle.read_text(encoding="utf-8")


def test_fit_check_runs_on_sample_jd(capsys) -> None:
    assert FIXTURE_JD.exists()
    assert fit_check_main([str(FIXTURE_JD)]) == 0
    out = capsys.readouterr().out
    assert "Fit Check" in out
    assert "Fit Rating:" in out
    assert "Contoso Cloud Solutions" in out


def test_gap_analysis_writes_markdown_report(tmp_path: Path) -> None:
    out_file = tmp_path / "GapAnalysis.md"
    assert gap_analysis_main([str(FIXTURE_JD), "--out", str(out_file)]) == 0
    assert out_file.exists()
    text = out_file.read_text(encoding="utf-8")
    assert "# Gap Analysis:" in text
    assert "Summary Table" in text
    assert "Contoso Cloud Solutions" in text


def test_generate_linkedin_writes_copy(tmp_path: Path) -> None:
    out_file = tmp_path / "LinkedIn.md"
    assert linkedin_main(["--out", str(out_file)]) == 0
    assert out_file.exists()
    text = out_file.read_text(encoding="utf-8")
    assert "# LinkedIn Profile Update Draft" in text


def test_generate_github_writes_readme(tmp_path: Path) -> None:
    out_file = tmp_path / "GitHub.md"
    assert github_main(["--out", str(out_file)]) == 0
    assert out_file.exists()
    text = out_file.read_text(encoding="utf-8")
    assert "# Hi there" in text
    assert "## Stack" in text


def _run_cli_command(command: str, out_file: Path, company: str = "SampleCo") -> int:
    if command in {"generate-linkedin", "generate-github"}:
        return cli_main([command, "--out", str(out_file)])
    argv = [command, str(FIXTURE_JD), "--company", company, "--out", str(out_file)]
    return cli_main(argv)


def _assert_docx_created(out_file: Path) -> None:
    assert out_file.exists()
    assert out_file.stat().st_size > 0


def test_generate_resume_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "resume.docx"
    assert _run_cli_command("generate-resume", out_file) == 0
    _assert_docx_created(out_file)


def test_generate_cover_letter_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "cover.docx"
    assert _run_cli_command("generate-cover-letter", out_file) == 0
    _assert_docx_created(out_file)


def test_generate_cold_call_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "cold_call.docx"
    assert _run_cli_command("generate-cold-call", out_file) == 0
    _assert_docx_created(out_file)


def test_generate_cold_call_without_jd_uses_recruiter_and_role_type(tmp_path: Path) -> None:
    """The Phase 3 fix: no JD file needed on the CLI either."""
    out_file = tmp_path / "cold_call_no_jd.docx"
    assert (
        cli_main(
            [
                "generate-cold-call",
                "--recruiter-name",
                "Jane Doe",
                "--role-type",
                "Senior .NET Developer roles",
                "--out",
                str(out_file),
            ]
        )
        == 0
    )
    _assert_docx_created(out_file)


def test_generate_job_site_writes_txt(tmp_path: Path) -> None:
    out_file = tmp_path / "job_site.txt"
    assert _run_cli_command("generate-job-site", out_file) == 0
    assert out_file.exists()
    text = out_file.read_text(encoding="utf-8")
    assert len(text) > 0
    assert "Senior Full-Stack .NET Developer" in text


def test_generate_thank_you_writes_docx(tmp_path: Path) -> None:
    # Unlike the other letter generators, generate-thank-you requires
    # --discussion-point regardless of whether a JD is given (Phase 4 fix) —
    # doesn't fit the shared _run_cli_command helper's uniform argv shape.
    out_file = tmp_path / "thank_you.docx"
    assert (
        cli_main(
            [
                "generate-thank-you",
                str(FIXTURE_JD),
                "--company",
                "SampleCo",
                "--discussion-point",
                "We discussed the team's roadmap.",
                "--out",
                str(out_file),
            ]
        )
        == 0
    )
    _assert_docx_created(out_file)


def test_generate_thank_you_without_discussion_point_fails_closed(tmp_path: Path) -> None:
    out_file = tmp_path / "thank_you_fail.docx"
    assert (
        cli_main(
            ["generate-thank-you", str(FIXTURE_JD), "--company", "SampleCo", "--out", str(out_file)]
        )
        == 1
    )
    assert not out_file.exists()


def test_interview_prep_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "InterviewPrep.docx"
    assert cli_main(["interview-prep", str(FIXTURE_JD), "--out", str(out_file)]) == 0
    _assert_docx_created(out_file)


def test_interview_prep_stage_flag_accepted(tmp_path: Path) -> None:
    out_file = tmp_path / "InterviewPrep.docx"
    assert (
        cli_main(
            [
                "interview-prep",
                str(FIXTURE_JD),
                "--stage",
                "phone_screen",
                "--out",
                str(out_file),
            ]
        )
        == 0
    )
    _assert_docx_created(out_file)


def test_interview_prep_update_star_bank_flags_accepted(tmp_path: Path) -> None:
    """A tmp copy of the real star-bank.md so any story the real bundle
    selects has a matching title to update against — never the real file."""
    real_star_bank = REPO_ROOT / "project-1-application-engine" / "reference" / "star-bank.md"
    star_bank_copy = tmp_path / "star-bank.md"
    star_bank_copy.write_text(real_star_bank.read_text(encoding="utf-8"), encoding="utf-8")
    out_file = tmp_path / "InterviewPrep.docx"

    assert (
        cli_main(
            [
                "interview-prep",
                str(FIXTURE_JD),
                "--out",
                str(out_file),
                "--update-star-bank",
                "--star-bank-path",
                str(star_bank_copy),
            ]
        )
        == 0
    )
    _assert_docx_created(out_file)


def test_interview_prep_hybrid_content_flags_accepted(tmp_path: Path) -> None:
    company_research_file = tmp_path / "company-research.md"
    company_research_file.write_text("SampleCo just closed a Series B.", encoding="utf-8")
    recruiter_briefing_file = tmp_path / "recruiter-briefing.md"
    recruiter_briefing_file.write_text("Two rounds, technical then panel.", encoding="utf-8")
    qa_cards_file = tmp_path / "qa-cards.json"
    qa_cards_file.write_text(
        json.dumps([{"question": "Walk me through your resume.", "answer": "..."}]),
        encoding="utf-8",
    )
    salary_section_file = tmp_path / "salary.md"
    salary_section_file.write_text("Target range: $120K-$140K CAD.", encoding="utf-8")
    out_file = tmp_path / "InterviewPrep.docx"

    assert (
        cli_main(
            [
                "interview-prep",
                str(FIXTURE_JD),
                "--out",
                str(out_file),
                "--stage",
                "final_round",
                "--company-research",
                str(company_research_file),
                "--recruiter-briefing",
                str(recruiter_briefing_file),
                "--qa-cards",
                str(qa_cards_file),
                "--salary-section",
                str(salary_section_file),
            ]
        )
        == 0
    )
    _assert_docx_created(out_file)


def test_interview_prep_malformed_qa_cards_json_fails_closed(tmp_path: Path) -> None:
    qa_cards_file = tmp_path / "qa-cards.json"
    qa_cards_file.write_text("{not valid json", encoding="utf-8")
    out_file = tmp_path / "InterviewPrep.docx"

    assert (
        cli_main(
            [
                "interview-prep",
                str(FIXTURE_JD),
                "--out",
                str(out_file),
                "--qa-cards",
                str(qa_cards_file),
            ]
        )
        == 1
    )
    assert not out_file.exists()


def test_generate_learning_plan_writes_pdf(tmp_path: Path) -> None:
    example = (
        Path(__file__).resolve().parents[1]
        / "project-2-profile-learning-hub"
        / "roles"
        / "_example.json"
    )
    cfg = json.loads(example.read_text(encoding="utf-8"))
    out_file = tmp_path / "smoke.pdf"
    cfg["output"] = str(out_file)
    cfg_path = tmp_path / "smoke.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    assert cli_main(["generate-learning-plan", str(cfg_path)]) == 0
    assert out_file.exists() and out_file.stat().st_size > 0


@pytest.mark.parametrize(
    "fixture,expected_rating",
    [
        ("sample-jd.md", "Stretch"),
        ("data-engineer-jd.md", "Pass"),
        # This example persona's Professional Experience has no
        # self-employment/portfolio-building entry (unlike the real resume
        # this codebase was built against), so it doesn't exercise the
        # production-vs-coursework distinction that JD used to regression-test
        # — it lands on 3 genuine required-skill gaps against this persona's
        # skill set, computing "Pass" rather than "Stretch".
        ("cloud-devops-jd.md", "Pass"),
        ("frontend-angular-jd.md", "Pass"),
    ],
)
def test_fit_check_various_jds(capsys, fixture: str, expected_rating: str) -> None:
    jd_path = FIXTURES_DIR / fixture
    assert jd_path.exists()
    assert fit_check_main([str(jd_path)]) == 0
    out = capsys.readouterr().out
    assert "Fit Check" in out
    assert "Fit Rating:" in out
    assert f"Fit Rating: {expected_rating}" in out, f"expected {expected_rating} in:\n{out}"
