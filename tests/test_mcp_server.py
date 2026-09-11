"""Smoke tests for the MCP server tool wrappers.

Calls each tool function directly (the ``@mcp.tool()`` decorator leaves the
underlying function callable) rather than over a live MCP transport, mirroring
the pattern in ``tests/test_cli_commands.py``.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ContentBlock, EmbeddedResource, TextContent

from mcp_server.server import (
    build_bundles,
    fit_check,
    gap_analysis,
    generate_application_documents,
    generate_cold_call,
    generate_cover_letter,
    generate_github,
    generate_job_site_letter,
    generate_learning_plan,
    generate_linkedin,
    generate_resume,
    generate_thank_you,
    interview_prep,
    validate_bundles,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_JD = REPO_ROOT / "tests" / "fixtures" / "sample-jd.md"
# sample-jd.md rates Stretch against the real bundle — used throughout this
# file for the many tools that don't gate on fit (unchanged from before).
# strong-fit-jd.md rates Strong — required for generate_resume /
# generate_cover_letter / generate_application_documents, which now refuse
# to generate below Good.
STRONG_FIXTURE_JD = REPO_ROOT / "tests" / "fixtures" / "strong-fit-jd.md"


def _embedded_resources(blocks: list[ContentBlock]) -> list[EmbeddedResource]:
    return [b for b in blocks if isinstance(b, EmbeddedResource)]


def _text_blocks(blocks: list[ContentBlock]) -> list[TextContent]:
    return [b for b in blocks if isinstance(b, TextContent)]


def test_fit_check_returns_rating() -> None:
    out = fit_check(str(FIXTURE_JD))
    assert "Fit Check" in out
    assert "Fit Rating:" in out


def test_fit_check_missing_file_raises_tool_error() -> None:
    with pytest.raises(ToolError):
        fit_check(str(REPO_ROOT / "tests" / "fixtures" / "does-not-exist.md"))


def test_validate_bundles_runs() -> None:
    out = validate_bundles()
    assert "Alias registry" in out or "OK" in out


def test_build_bundles_delegates_to_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    """The real build is covered against a fixture repo in test_build_bundles.py.

    Calling it for real here rewrites this repo's own committed bundles, since
    the CLI's `build` resolves its root from __file__ and takes no override.
    """
    calls: list[list[str]] = []

    def fake_run_cli(argv: list[str]) -> str:
        calls.append(argv)
        return "wrote profile-bundle.json"

    monkeypatch.setattr("mcp_server.server._run_cli", fake_run_cli)

    out = build_bundles()

    assert calls == [["build"]]
    assert out == "wrote profile-bundle.json"


def test_gap_analysis_writes_markdown_report(tmp_path: Path) -> None:
    out_file = tmp_path / "GapAnalysis.md"
    blocks = gap_analysis(str(FIXTURE_JD), out=str(out_file))
    assert out_file.exists()
    assert "# Gap Analysis:" in out_file.read_text(encoding="utf-8")
    # The report content itself must come back inline through MCP, not just
    # a "Wrote <path>" status string the client can't do anything with.
    text_blocks = _text_blocks(blocks)
    assert any("# Gap Analysis:" in b.text for b in text_blocks)


def test_generate_linkedin_writes_copy(tmp_path: Path) -> None:
    out_file = tmp_path / "LinkedIn.md"
    blocks = generate_linkedin(out=str(out_file))
    assert out_file.exists()
    assert "# LinkedIn Profile Update Draft" in out_file.read_text(encoding="utf-8")
    # Profile-update tools attach their markdown as a text EmbeddedResource
    # (so MCP clients like Claude Desktop show it as a document rather than
    # dumping it into the chat transcript), not as a plain TextContent block.
    resources = _embedded_resources(blocks)
    assert any(
        r.resource.mime_type == "text/markdown"
        and "# LinkedIn Profile Update Draft" in r.resource.text
        for r in resources
    )
    assert not any("# LinkedIn Profile Update Draft" in b.text for b in _text_blocks(blocks))


def test_generate_github_writes_readme(tmp_path: Path) -> None:
    out_file = tmp_path / "GitHub.md"
    blocks = generate_github(out=str(out_file))
    assert out_file.exists()
    assert "# Hi there" in out_file.read_text(encoding="utf-8")
    resources = _embedded_resources(blocks)
    assert any(
        r.resource.mime_type == "text/markdown" and "# Hi there" in r.resource.text
        for r in resources
    )


def test_generate_resume_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "resume.docx"
    blocks = generate_resume(str(STRONG_FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert out_file.exists() and out_file.stat().st_size > 0
    resources = _embedded_resources(blocks)
    assert len(resources) == 1
    assert resources[0].resource.mime_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert base64.b64decode(resources[0].resource.blob) == out_file.read_bytes()


def test_generate_cover_letter_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "cover.docx"
    blocks = generate_cover_letter(str(STRONG_FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert out_file.exists() and out_file.stat().st_size > 0
    resources = _embedded_resources(blocks)
    assert len(resources) == 1
    assert base64.b64decode(resources[0].resource.blob) == out_file.read_bytes()


def test_generate_resume_below_good_fit_raises_tool_error(tmp_path: Path) -> None:
    out_file = tmp_path / "resume_fail.docx"
    with pytest.raises(ToolError):
        generate_resume(str(FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert not out_file.exists()


def test_generate_cover_letter_below_good_fit_raises_tool_error(tmp_path: Path) -> None:
    out_file = tmp_path / "cover_fail.docx"
    with pytest.raises(ToolError):
        generate_cover_letter(str(FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert not out_file.exists()


def test_generate_application_documents_returns_both_docs() -> None:
    blocks = generate_application_documents(str(STRONG_FIXTURE_JD), company="SampleCo")
    resources = _embedded_resources(blocks)
    assert len(resources) == 2
    for resource in resources:
        assert resource.resource.mime_type == (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert len(resource.resource.blob) > 0
    text_blocks = _text_blocks(blocks)
    assert any(b.text.startswith("Fit Rating: Strong") for b in text_blocks)


def test_generate_application_documents_below_good_fit_raises_tool_error() -> None:
    with pytest.raises(ToolError):
        generate_application_documents(str(FIXTURE_JD), company="SampleCo")


def test_generate_cold_call_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "cold_call.docx"
    generate_cold_call(str(FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert out_file.exists() and out_file.stat().st_size > 0


def test_generate_cold_call_without_jd_uses_recruiter_and_role_type(tmp_path: Path) -> None:
    """The Phase 3 fix: no JD needed via MCP either."""
    out_file = tmp_path / "cold_call_no_jd.docx"
    generate_cold_call(
        recruiter_name="Jane Doe",
        role_type="Senior .NET Developer roles",
        out=str(out_file),
    )
    assert out_file.exists() and out_file.stat().st_size > 0


def test_generate_job_site_letter_writes_txt(tmp_path: Path) -> None:
    out_file = tmp_path / "job_site.txt"
    generate_job_site_letter(str(FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert out_file.exists() and len(out_file.read_text(encoding="utf-8")) > 0


def test_generate_thank_you_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "thank_you.docx"
    generate_thank_you(
        str(FIXTURE_JD),
        company="SampleCo",
        discussion_points=["We discussed the team's roadmap."],
        out=str(out_file),
    )
    assert out_file.exists() and out_file.stat().st_size > 0


def test_generate_thank_you_without_discussion_points_raises_tool_error(tmp_path: Path) -> None:
    out_file = tmp_path / "thank_you_fail.docx"
    with pytest.raises(ToolError):
        generate_thank_you(str(FIXTURE_JD), company="SampleCo", out=str(out_file))
    assert not out_file.exists()


def test_generate_thank_you_without_jd_uses_recruiter_style_inputs(tmp_path: Path) -> None:
    out_file = tmp_path / "thank_you_no_jd.docx"
    generate_thank_you(
        company="SampleCo",
        role="Senior .NET Developer",
        interviewers=["Jane Doe"],
        date="August 25, 2026",
        discussion_points=["We discussed the team's roadmap."],
        out=str(out_file),
    )
    assert out_file.exists() and out_file.stat().st_size > 0


def test_interview_prep_writes_docx(tmp_path: Path) -> None:
    out_file = tmp_path / "InterviewPrep.docx"
    interview_prep(str(FIXTURE_JD), out=str(out_file))
    assert out_file.exists() and out_file.stat().st_size > 0


def test_interview_prep_stage_flag_accepted(tmp_path: Path) -> None:
    out_file = tmp_path / "InterviewPrep.docx"
    interview_prep(str(FIXTURE_JD), stage="phone_screen", out=str(out_file))
    assert out_file.exists() and out_file.stat().st_size > 0


def test_interview_prep_update_star_bank_flags_accepted(tmp_path: Path) -> None:
    """A tmp copy of the real star-bank.md so any story the real bundle
    selects has a matching title to update against — never the real file."""
    real_star_bank = REPO_ROOT / "project-1-application-engine" / "reference" / "star-bank.md"
    star_bank_copy = tmp_path / "star-bank.md"
    star_bank_copy.write_text(real_star_bank.read_text(encoding="utf-8"), encoding="utf-8")
    out_file = tmp_path / "InterviewPrep.docx"

    interview_prep(
        str(FIXTURE_JD),
        out=str(out_file),
        update_star_bank=True,
        star_bank_path=str(star_bank_copy),
    )
    assert out_file.exists() and out_file.stat().st_size > 0


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

    interview_prep(
        str(FIXTURE_JD),
        out=str(out_file),
        stage="final_round",
        company_research_path=str(company_research_file),
        recruiter_briefing_path=str(recruiter_briefing_file),
        qa_cards_path=str(qa_cards_file),
        salary_section_path=str(salary_section_file),
    )
    assert out_file.exists() and out_file.stat().st_size > 0


def test_interview_prep_malformed_qa_cards_json_raises_tool_error(tmp_path: Path) -> None:
    qa_cards_file = tmp_path / "qa-cards.json"
    qa_cards_file.write_text("{not valid json", encoding="utf-8")
    out_file = tmp_path / "InterviewPrep.docx"

    with pytest.raises(ToolError):
        interview_prep(str(FIXTURE_JD), out=str(out_file), qa_cards_path=str(qa_cards_file))
    assert not out_file.exists()


def test_generate_learning_plan_returns_pdf_bytes(tmp_path: Path) -> None:
    example = REPO_ROOT / "project-2-profile-learning-hub" / "roles" / "_example.json"
    cfg = json.loads(example.read_text(encoding="utf-8"))
    cfg["output"] = str(tmp_path / "smoke.pdf")
    cfg_path = tmp_path / "smoke.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")

    blocks = generate_learning_plan(str(cfg_path))
    out_file = tmp_path / "smoke.pdf"
    assert out_file.exists() and out_file.stat().st_size > 0

    resources = _embedded_resources(blocks)
    assert len(resources) == 1
    assert resources[0].resource.mime_type == "application/pdf"
    assert base64.b64decode(resources[0].resource.blob).startswith(b"%PDF")
