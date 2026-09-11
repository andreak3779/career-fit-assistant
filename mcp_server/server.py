#!/usr/bin/env python3
"""MCP server that exposes the career-fit-assistant CLI as MCP tools.

Each tool is a thin adapter: it builds the same argv list the CLI itself
would build, calls ``cli.career_fit_api.main(argv)`` with stdout/stderr
captured, and returns the captured text plus (for document-producing tools)
the generated artifact's content, read back off disk. No generation logic
lives here — see ``cli/career_fit_api.py`` and the ``project-*`` script modules
for that — with one deliberate exception: ``_require_good_fit`` re-runs the
same fit-rating check ``generate_resume.py``/``generate_cover_letter.py``
already do internally, as a *gate* before dispatching. That's a judgment
check the create-a-cover-letter-and-tailored-resume-for-job-description
skill already states as a rule ("only generate if Strong or Good") — an MCP
client calling these tools directly bypasses that skill and its prompt-level
judgment entirely, so the rule is enforced here in code instead.
"""

from __future__ import annotations

import base64
import contextlib
import io
import re
import threading
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import (
    BlobResourceContents,
    ContentBlock,
    EmbeddedResource,
    TextContent,
    TextResourceContents,
)

from cli.career_fit_api import main as cli_main
from shared.bundle_loader import load_profile_bundle
from shared.fit_engine import FitResult, rate_fit
from shared.jd_parser import parse_jd

mcp = MCPServer("career-fit-assistant")

# contextlib.redirect_stdout/stderr mutate process-global sys.stdout/sys.stderr
# for the duration of the `with` block — not thread-safe. The mcp SDK dispatches
# each tool call as its own task and runs sync tool functions (all of ours) via
# anyio.to_thread.run_sync, so two tool calls issued without waiting on each
# other genuinely execute on different threads. Without this lock, concurrent
# calls can corrupt each other's captured output. These are one-shot document
# generation calls, not a hot path, so serializing them costs nothing that matters.
_CLI_LOCK = threading.Lock()


def _run_cli(argv: list[str]) -> str:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with _CLI_LOCK:
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exit_code = cli_main(argv)
        except SystemExit as exc:
            # argparse calls sys.exit() on bad arguments (e.g. --help, missing
            # required positional) instead of returning a code.
            exit_code = exc.code if isinstance(exc.code, int) else 1

    output = stdout.getvalue()
    errors = stderr.getvalue()
    combined = output + (f"\n{errors}" if errors else "")

    if exit_code != 0:
        raise ToolError(combined.strip() or f"'{' '.join(argv)}' failed (exit {exit_code})")
    return combined.strip()


_WROTE_RE = re.compile(r"^Wrote (.+)$", re.MULTILINE)
_TEXT_SUFFIXES = {".md", ".txt", ".json"}
_TEXT_MIME_TYPES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
}
_MIME_TYPES = {
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pdf": "application/pdf",
}


def _artifact_content_blocks(
    stdout_text: str, embed_text_as_resource: bool = False
) -> list[ContentBlock]:
    """Read back every artifact a CLI command just wrote (per its ``Wrote
    <path>`` stdout lines — the convention every generator script already
    follows) and return its content: a base64 ``EmbeddedResource`` for
    DOCX/PDF, and for markdown/text/JSON either inline text or (when
    ``embed_text_as_resource`` is set) a text ``EmbeddedResource`` too. This
    is what actually makes generated documents retrievable through the MCP
    interface, rather than leaving the client with a local filesystem path
    it can't read.

    ``embed_text_as_resource`` is for the profile-update tools
    (generate_linkedin, generate_github, generate_jobgether,
    generate_job_board, generate_pluralsight): their markdown draft is the
    whole deliverable, not a status message, so it comes back as an
    attachment in MCP clients like Claude Desktop the same way DOCX/PDF
    documents do, instead of dumping the full draft into the chat
    transcript as plain text. Other markdown-producing tools (e.g.
    gap_analysis) keep the inline-text behavior, since their content is
    meant to be read/discussed in the conversation itself.
    """
    blocks: list[ContentBlock] = []
    for match in _WROTE_RE.finditer(stdout_text):
        path = Path(match.group(1).strip())
        if not path.is_file():
            # Defensive: e.g. `build`'s "Wrote X (v29)" trailer doesn't
            # resolve to a real path — skip rather than crash.
            continue
        suffix = path.suffix.lower()
        try:
            if suffix in _TEXT_SUFFIXES:
                text = path.read_text(encoding="utf-8")
                if embed_text_as_resource:
                    # .as_uri() requires an absolute path — resolve() first
                    # so a caller-supplied relative --out doesn't raise
                    # ValueError and crash the whole tool call.
                    uri = path.resolve().as_uri()
                    mime = _TEXT_MIME_TYPES.get(suffix, "text/plain")
                    blocks.append(
                        EmbeddedResource(
                            type="resource",
                            resource=TextResourceContents(uri=uri, mime_type=mime, text=text),
                        )
                    )
                else:
                    blocks.append(TextContent(type="text", text=f"### {path.name}\n\n{text}"))
            else:
                data = base64.b64encode(path.read_bytes()).decode()
                mime = _MIME_TYPES.get(suffix, "application/octet-stream")
                uri = path.resolve().as_uri()
                blocks.append(
                    EmbeddedResource(
                        type="resource",
                        resource=BlobResourceContents(uri=uri, mime_type=mime, blob=data),
                    )
                )
        except OSError as exc:
            # Don't let one unreadable artifact (permissions, race, odd
            # encoding) take down attachments that already succeeded.
            blocks.append(TextContent(type="text", text=f"[could not attach {path.name}: {exc}]"))
    return blocks


def _run_cli_with_artifacts(
    argv: list[str], embed_text_as_resource: bool = False
) -> list[ContentBlock]:
    combined = _run_cli(argv)
    blocks: list[ContentBlock] = [TextContent(type="text", text=combined)]
    blocks.extend(_artifact_content_blocks(combined, embed_text_as_resource=embed_text_as_resource))
    return blocks


_PASSING_RATINGS = {"Strong", "Good"}


def _require_good_fit(jd_path: Path) -> FitResult:
    """Hard-gate resume/cover-letter generation on fit rating — see module
    docstring for why this lives here despite the "thin adapter" rule."""
    if not jd_path.is_file():
        raise ToolError(f"job description file not found: {jd_path}")
    bundle = load_profile_bundle()
    parsed = parse_jd(jd_path.read_text(encoding="utf-8"))
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)
    if result.rating not in _PASSING_RATINGS:
        raise ToolError(
            f"Fit rating is {result.rating} (below Good) — refusing to generate "
            f"resume/cover letter.\n{result.rationale}\n"
            "Run fit_check for the full breakdown, or supply a stronger-fit JD."
        )
    return result


@mcp.tool(description="Build profile and presence bundles")
def build_bundles() -> str:
    return _run_cli(["build"])


@mcp.tool(description="Run canonical bundle validation checks")
def validate_bundles() -> str:
    return _run_cli(["validate"])


@mcp.tool(description="Inline fit check for a job description")
def fit_check(jd: str) -> str:
    """jd: path to a job description markdown file."""
    return _run_cli(["fit-check", jd])


@mcp.tool(description="Generate a markdown gap analysis report", structured_output=False)
def gap_analysis(jd: str, out: str | None = None) -> list[ContentBlock]:
    """jd: path to a job description markdown file. out: optional output markdown path."""
    argv = ["gap-analysis", jd]
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv)


@mcp.tool(description="Generate LinkedIn profile copy", structured_output=False)
def generate_linkedin(out: str | None = None) -> list[ContentBlock]:
    """out: optional output markdown path."""
    argv = ["generate-linkedin"]
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv, embed_text_as_resource=True)


@mcp.tool(description="Generate GitHub profile README copy", structured_output=False)
def generate_github(out: str | None = None) -> list[ContentBlock]:
    """out: optional output markdown path."""
    argv = ["generate-github"]
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv, embed_text_as_resource=True)


@mcp.tool(description="Generate Jobgether profile copy", structured_output=False)
def generate_jobgether(out: str | None = None) -> list[ContentBlock]:
    """out: optional output markdown path."""
    argv = ["generate-jobgether"]
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv, embed_text_as_resource=True)


@mcp.tool(description="Generate Indeed & ZipRecruiter profile copy", structured_output=False)
def generate_job_board(out: str | None = None) -> list[ContentBlock]:
    """out: optional output markdown path."""
    argv = ["generate-job-board"]
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv, embed_text_as_resource=True)


@mcp.tool(description="Generate Pluralsight profile copy", structured_output=False)
def generate_pluralsight(out: str | None = None) -> list[ContentBlock]:
    """out: optional output markdown path."""
    argv = ["generate-pluralsight"]
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv, embed_text_as_resource=True)


def _letter_argv(command: str, jd: str, company: str | None, out: str | None) -> list[str]:
    argv = [command, jd]
    if company:
        argv.extend(["--company", company])
    if out:
        argv.extend(["--out", out])
    return argv


def _letter_tool(command: str, jd: str, company: str | None, out: str | None) -> list[ContentBlock]:
    return _run_cli_with_artifacts(_letter_argv(command, jd, company, out))


def _gated_letter_tool(
    command: str, jd: str, company: str | None, out: str | None
) -> list[ContentBlock]:
    fit = _require_good_fit(Path(jd))
    blocks: list[ContentBlock] = [
        TextContent(type="text", text=f"Fit Rating: {fit.rating} — {fit.rationale}")
    ]
    blocks.extend(_run_cli_with_artifacts(_letter_argv(command, jd, company, out)))
    return blocks


@mcp.tool(
    description="Generate a tailored resume DOCX (refuses if fit rating is below Good)",
    structured_output=False,
)
def generate_resume(
    jd: str, company: str | None = None, out: str | None = None
) -> list[ContentBlock]:
    """jd: path to a job description markdown file. company: optional filename
    override. out: optional output DOCX path. Refuses to generate (raises a
    tool error) when the computed fit rating is below Good — call fit_check
    first to see the rating without generating a document."""
    return _gated_letter_tool("generate-resume", jd, company, out)


@mcp.tool(
    description="Generate a tailored cover-letter DOCX (refuses if fit rating is below Good)",
    structured_output=False,
)
def generate_cover_letter(
    jd: str, company: str | None = None, out: str | None = None
) -> list[ContentBlock]:
    """jd: path to a job description markdown file. company: optional filename
    override. out: optional output DOCX path. Refuses to generate (raises a
    tool error) when the computed fit rating is below Good — call fit_check
    first to see the rating without generating a document."""
    return _gated_letter_tool("generate-cover-letter", jd, company, out)


@mcp.tool(
    description="Generate a tailored resume and cover letter for a job description in one "
    "call (refuses if fit rating is below Good)",
    structured_output=False,
)
def generate_application_documents(jd: str, company: str | None = None) -> list[ContentBlock]:
    """jd: path to a job description markdown file. company: optional filename
    override applied to both documents. Refuses to generate (raises a tool
    error) when the computed fit rating is below Good — call fit_check first
    to see the rating without generating documents. Both documents land in
    their normal default outputs/ location; use generate_resume /
    generate_cover_letter individually for a custom output path."""
    fit = _require_good_fit(Path(jd))
    blocks: list[ContentBlock] = [
        TextContent(type="text", text=f"Fit Rating: {fit.rating} — {fit.rationale}")
    ]
    blocks.extend(_run_cli_with_artifacts(_letter_argv("generate-resume", jd, company, None)))
    blocks.extend(_run_cli_with_artifacts(_letter_argv("generate-cover-letter", jd, company, None)))
    return blocks


@mcp.tool(description="Generate a short cold-call cover-letter DOCX", structured_output=False)
def generate_cold_call(
    jd: str | None = None,
    company: str | None = None,
    recruiter_name: str | None = None,
    role_type: str | None = None,
    out: str | None = None,
) -> list[ContentBlock]:
    """jd: optional path to a target company description or JD markdown file
    — cold outreach is usually conversational, with no JD in hand; prefer
    recruiter_name/role_type instead. company: optional filename/salutation
    override. recruiter_name: salutation name, e.g. "Jane Doe" (default
    "Hiring Team"). role_type: target role type, e.g. "Senior .NET Developer
    roles". out: optional output DOCX path."""
    argv = ["generate-cold-call"]
    if jd:
        argv.append(jd)
    if company:
        argv.extend(["--company", company])
    if recruiter_name:
        argv.extend(["--recruiter-name", recruiter_name])
    if role_type:
        argv.extend(["--role-type", role_type])
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv)


@mcp.tool(
    description="Generate a short job-site cover letter (default: .txt)",
    structured_output=False,
)
def generate_job_site_letter(
    jd: str, company: str | None = None, out: str | None = None
) -> list[ContentBlock]:
    """jd: path to a job description markdown file. company: optional filename override. out: optional output path (.txt default, .docx for DOCX)."""
    return _letter_tool("generate-job-site", jd, company, out)


@mcp.tool(description="Generate a post-interview thank-you letter DOCX", structured_output=False)
def generate_thank_you(
    jd: str | None = None,
    company: str | None = None,
    role: str | None = None,
    interviewers: list[str] | None = None,
    date: str | None = None,
    discussion_points: list[str] | None = None,
    out: str | None = None,
) -> list[ContentBlock]:
    """jd: optional path to a job description markdown file, for company/role/
    skills-fit context — never a substitute for discussion_points. company:
    optional filename/salutation override. role: role interviewed for.
    interviewers: interviewer name(s) — drives the salutation. date: interview
    date. discussion_points: specific details from the actual interview
    (required — at least one; generation refuses without it). out: optional
    output DOCX path."""
    argv = ["generate-thank-you"]
    if jd:
        argv.append(jd)
    if company:
        argv.extend(["--company", company])
    if role:
        argv.extend(["--role", role])
    for interviewer in interviewers or []:
        argv.extend(["--interviewer", interviewer])
    if date:
        argv.extend(["--date", date])
    for point in discussion_points or []:
        argv.extend(["--discussion-point", point])
    if out:
        argv.extend(["--out", out])
    return _run_cli_with_artifacts(argv)


@mcp.tool(description="Generate an interview prep DOCX for a JD", structured_output=False)
def interview_prep(
    jd: str,
    stage: str | None = None,
    out: str | None = None,
    update_star_bank: bool = False,
    star_bank_path: str | None = None,
    company_research_path: str | None = None,
    recruiter_briefing_path: str | None = None,
    qa_cards_path: str | None = None,
    salary_section_path: str | None = None,
) -> list[ContentBlock]:
    """jd: path to a job description markdown file.
    stage: optional interview stage (phone_screen, technical_screen, final_round;
    default: technical_screen) — gates document scope. out: optional output DOCX path.
    update_star_bank: when true, writes updated last_used/used_for metadata back
    to star-bank.md for every STAR story selected in this run. star_bank_path:
    test-only override for star-bank.md's location; defaults to the real
    reference file. company_research_path: optional path to a text file of
    company-research prose (e.g. web_search findings — never fabricated).
    recruiter_briefing_path: optional path to a text file with a pasted
    recruiter briefing. qa_cards_path: optional path to a JSON file of
    LLM-authored Q&A cards (list of {"question", "answer", optional
    "tip"/"category"}) — merged in after the script's own grounded-evidence
    cards. salary_section_path: optional path to a text file of
    salary/negotiation prose; only rendered when stage is final_round,
    otherwise a warning is printed and it's omitted."""
    argv = ["interview-prep", jd]
    if stage:
        argv.extend(["--stage", stage])
    if out:
        argv.extend(["--out", out])
    if update_star_bank:
        argv.append("--update-star-bank")
    if star_bank_path:
        argv.extend(["--star-bank-path", star_bank_path])
    if company_research_path:
        argv.extend(["--company-research", company_research_path])
    if recruiter_briefing_path:
        argv.extend(["--recruiter-briefing", recruiter_briefing_path])
    if qa_cards_path:
        argv.extend(["--qa-cards", qa_cards_path])
    if salary_section_path:
        argv.extend(["--salary-section", salary_section_path])
    return _run_cli_with_artifacts(argv)


@mcp.tool(
    description="Render a role-specific Learning Plan PDF from a JSON config",
    structured_output=False,
)
def generate_learning_plan(role_json: str) -> list[ContentBlock]:
    """role_json: path to a role config JSON — see
    project-2-profile-learning-hub/roles/_example.json for the schema. The
    config must already exist (authored by the cert-learning-plan /
    learning-plan-gap-analysis skill); this only renders it to PDF. The
    config's own "output" path is resolved relative to this server's working
    directory — prefer an absolute path there, or one relative to the repo
    root."""
    return _run_cli_with_artifacts(["generate-learning-plan", role_json])


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
