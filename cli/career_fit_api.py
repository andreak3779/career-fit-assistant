#!/usr/bin/env python3
"""CLI entry point for career-fit-assistant, registered as the career-fit-api command."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import cast


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_pdf_template() -> ModuleType:
    """Load project-2's pdf-template.py and cache it in sys.modules.

    Its dashed filename blocks normal dotted import (same reason
    tests/test_pdf_template.py uses spec_from_file_location) — but unlike a
    one-shot CLI process, the MCP server that also calls this dispatcher is
    long-running, so re-parsing/re-exec'ing the module (incl. its reportlab
    imports) on every call would be wasted work after the first.
    """
    if "pdf_template" in sys.modules:
        return sys.modules["pdf_template"]
    script = _root() / "project-2-profile-learning-hub" / "pdf-template.py"
    spec = importlib.util.spec_from_file_location("pdf_template", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["pdf_template"] = module
    spec.loader.exec_module(module)
    return module


def _generate_learning_plan(role_json: Path) -> int:
    return cast(int, _load_pdf_template().main([str(role_json)]))


def _build(project_root: Path | None = None) -> int:
    project_root = project_root if project_root is not None else _root()
    # bootstrap removed: project_2 now a real package
    from project_2_profile_learning_hub.skills.profile_hub_bundle_generator.scripts.build_bundles import (
        build,
        write,
    )
    from project_2_profile_learning_hub.skills.profile_hub_bundle_generator.scripts.render_md_bundles import (
        main as render_md_bundles_main,
    )

    profile, presence = build(project_root)
    write(project_root, profile, presence)
    # Also refresh app-engine-bundle.md / presence-bundle.md — every SKILL.md
    # workflow reads those markdown files, not the JSON this writes above, so
    # skipping this step leaves them silently stale after a "build".
    return cast(int, render_md_bundles_main([str(project_root)]))


def _validate() -> int:
    project_root = _root()
    # bootstrap removed: project_2 now a real package
    from project_2_profile_learning_hub.scripts.validate import main as validate_main

    # Also validate the alias registry shape.
    from shared.fit_engine import _load_aliases

    aliases = _load_aliases()
    if not aliases:
        print("[WARN] Alias registry is empty or missing", file=sys.stderr)
    else:
        bad = {
            k: v
            for k, v in aliases.items()
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v)
        }
        if bad:
            print(
                f"[ERROR] Alias registry has invalid entries: {list(bad.keys())}", file=sys.stderr
            )
            return 1
        print(f"[OK] Alias registry loaded ({len(aliases)} entries)")

    return cast(int, validate_main([str(project_root)]))


def _fit_check(jd_path: Path) -> int:
    from project_1_application_engine.skills.job_description_fit.scripts.fit_check import (
        main as fit_check_main,
    )

    return cast(int, fit_check_main([str(jd_path)]))


def _gap_analysis(jd_path: Path, out_path: Path | None) -> int:
    from project_1_application_engine.skills.gap_analysis_job_description.scripts.gap_analysis import (
        main as gap_main,
    )

    args = [str(jd_path)]
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, gap_main(args))


def _generate_linkedin(out_path: Path | None) -> int:
    from project_3_presence_identity.skills.update_linkedin_profile.scripts.generate_linkedin import (
        main as linkedin_main,
    )

    args: list[str] = []
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, linkedin_main(args))


def _generate_github(out_path: Path | None) -> int:
    from project_3_presence_identity.skills.update_github_profile.scripts.generate_github import (
        main as github_main,
    )

    args: list[str] = []
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, github_main(args))


def _generate_jobgether(out_path: Path | None) -> int:
    from project_3_presence_identity.skills.update_jobgether_profile.scripts.generate_jobgether import (
        main as jobgether_main,
    )

    args: list[str] = []
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, jobgether_main(args))


def _generate_job_board(out_path: Path | None) -> int:
    from project_3_presence_identity.skills.update_job_board_profiles.scripts.generate_job_board import (
        main as job_board_main,
    )

    args: list[str] = []
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, job_board_main(args))


def _generate_pluralsight(out_path: Path | None) -> int:
    from project_3_presence_identity.skills.update_pluralsight_profile.scripts.generate_pluralsight import (
        main as pluralsight_main,
    )

    args: list[str] = []
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, pluralsight_main(args))


# Map CLI subcommand → underlying script module's full dotted path. These
# three take the same (jd, optional --company, optional --out) arguments, so
# they share a dispatcher. generate-cold-call and generate-thank-you are the
# exceptions — both have optional jd plus extra per-application flags (see
# _generate_cold_call / _generate_thank_you below), so each is dispatched
# separately.
_LETTER_GENERATORS = {
    "generate-resume": (
        "project_1_application_engine.skills."
        "create_a_cover_letter_and_tailored_resume_for_job_description.scripts.generate_resume"
    ),
    "generate-cover-letter": (
        "project_1_application_engine.skills."
        "create_a_cover_letter_and_tailored_resume_for_job_description.scripts.generate_cover_letter"
    ),
    "generate-job-site": "project_1_application_engine.scripts.generate_job_site_letter",
}


def _generate_letter(
    command: str,
    jd_path: Path,
    company: str | None,
    out_path: Path | None,
) -> int:
    # Import the script module under its full name. Using a runtime
    # ``importlib.import_module`` here is intentional: the scripts are
    # discovered from the static ``_LETTER_GENERATORS`` mapping below, and
    # failing closed (loud ``ImportError``) when a new generator is added
    # but not listed is the right behavior.
    module = importlib.import_module(_LETTER_GENERATORS[command])
    args: list[str] = [str(jd_path)]
    if company:
        args.extend(["--company", company])
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, module.main(args))


def _generate_cold_call(
    jd_path: Path | None,
    company: str | None,
    recruiter_name: str | None,
    role_type: str | None,
    out_path: Path | None,
) -> int:
    from project_1_application_engine.skills.cold_outreach_recruiter_letter.scripts.generate_cold_call_letter import (
        main as cold_call_main,
    )

    args: list[str] = [str(jd_path)] if jd_path is not None else []
    if company:
        args.extend(["--company", company])
    if recruiter_name:
        args.extend(["--recruiter-name", recruiter_name])
    if role_type:
        args.extend(["--role-type", role_type])
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, cold_call_main(args))


def _generate_thank_you(
    jd_path: Path | None,
    company: str | None,
    role: str | None,
    interviewers: list[str] | None,
    date: str | None,
    discussion_points: list[str] | None,
    out_path: Path | None,
) -> int:
    from project_1_application_engine.skills.post_interview_thank_you_letter.scripts.generate_thank_you_letter import (
        main as thank_you_main,
    )

    args: list[str] = [str(jd_path)] if jd_path is not None else []
    if company:
        args.extend(["--company", company])
    if role:
        args.extend(["--role", role])
    for interviewer in interviewers or []:
        args.extend(["--interviewer", interviewer])
    if date:
        args.extend(["--date", date])
    for point in discussion_points or []:
        args.extend(["--discussion-point", point])
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    return cast(int, thank_you_main(args))


def _interview_prep(
    jd_path: Path,
    out_path: Path | None,
    stage: str | None,
    update_star_bank: bool = False,
    star_bank_path: Path | None = None,
    company_research_path: Path | None = None,
    recruiter_briefing_path: Path | None = None,
    qa_cards_path: Path | None = None,
    salary_section_path: Path | None = None,
) -> int:
    from project_1_application_engine.skills.interview_prep.scripts.interview_prep import (
        main as interview_main,
    )

    args = [str(jd_path)]
    if stage:
        args.extend(["--stage", stage])
    if out_path is not None:
        args.extend(["--out", str(out_path)])
    if update_star_bank:
        args.append("--update-star-bank")
    if star_bank_path is not None:
        args.extend(["--star-bank-path", str(star_bank_path)])
    if company_research_path is not None:
        args.extend(["--company-research", str(company_research_path)])
    if recruiter_briefing_path is not None:
        args.extend(["--recruiter-briefing", str(recruiter_briefing_path)])
    if qa_cards_path is not None:
        args.extend(["--qa-cards", str(qa_cards_path)])
    if salary_section_path is not None:
        args.extend(["--salary-section", str(salary_section_path)])
    return cast(int, interview_main(args))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="career-fit-api", description="Monorepo bundle tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="Build profile and presence bundles")
    subparsers.add_parser("validate", help="Run canonical bundle validation checks")

    fit_parser = subparsers.add_parser("fit-check", help="Inline fit check for a job description")
    fit_parser.add_argument("jd", type=Path, help="Path to job description markdown file")

    gap_parser = subparsers.add_parser(
        "gap-analysis", help="Generate a markdown gap analysis report"
    )
    gap_parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    gap_parser.add_argument("--out", type=Path, help="Output markdown file path")

    linkedin_parser = subparsers.add_parser(
        "generate-linkedin", help="Generate LinkedIn profile copy"
    )
    linkedin_parser.add_argument("--out", type=Path, help="Output markdown file path")

    github_parser = subparsers.add_parser(
        "generate-github", help="Generate GitHub profile README copy"
    )
    github_parser.add_argument("--out", type=Path, help="Output markdown file path")

    jobgether_parser = subparsers.add_parser(
        "generate-jobgether", help="Generate Jobgether profile copy"
    )
    jobgether_parser.add_argument("--out", type=Path, help="Output markdown file path")

    job_board_parser = subparsers.add_parser(
        "generate-job-board", help="Generate Indeed & ZipRecruiter profile copy"
    )
    job_board_parser.add_argument("--out", type=Path, help="Output markdown file path")

    pluralsight_parser = subparsers.add_parser(
        "generate-pluralsight", help="Generate Pluralsight profile copy"
    )
    pluralsight_parser.add_argument("--out", type=Path, help="Output markdown file path")

    resume_parser = subparsers.add_parser("generate-resume", help="Generate a tailored resume DOCX")
    resume_parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    resume_parser.add_argument("--company", help="Override company name used in filename")
    resume_parser.add_argument("--out", type=Path, help="Output DOCX path")

    cover_parser = subparsers.add_parser(
        "generate-cover-letter", help="Generate a tailored cover-letter DOCX"
    )
    cover_parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    cover_parser.add_argument("--company", help="Override company name used in filename")
    cover_parser.add_argument("--out", type=Path, help="Output DOCX path")

    cold_parser = subparsers.add_parser(
        "generate-cold-call", help="Generate a short cold-call cover-letter DOCX"
    )
    cold_parser.add_argument(
        "jd",
        type=Path,
        nargs="?",
        default=None,
        help="Optional path to a target company description or JD markdown file. "
        "Cold outreach is usually conversational — omit this and use "
        "--recruiter-name/--role-type instead.",
    )
    cold_parser.add_argument("--company", help="Override company name used in filename")
    cold_parser.add_argument(
        "--recruiter-name", help='Salutation name, e.g. "Jane Doe" (default: "Hiring Team")'
    )
    cold_parser.add_argument(
        "--role-type", help='Target role type, e.g. "Senior .NET Developer roles"'
    )
    cold_parser.add_argument("--out", type=Path, help="Output DOCX path")

    job_site_parser = subparsers.add_parser(
        "generate-job-site", help="Generate a short job-site cover letter (default: .txt)"
    )
    job_site_parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    job_site_parser.add_argument("--company", help="Override company name used in filename")
    job_site_parser.add_argument(
        "--out", type=Path, help="Output path (default .txt; use .docx for DOCX)"
    )

    thank_you_parser = subparsers.add_parser(
        "generate-thank-you", help="Generate a post-interview thank-you letter DOCX"
    )
    thank_you_parser.add_argument(
        "jd",
        type=Path,
        nargs="?",
        default=None,
        help="Optional path to a job description markdown file, for company/role/"
        "skills-fit context. Never a substitute for --discussion-point.",
    )
    thank_you_parser.add_argument(
        "--company", help="Override company name used in filename and salutation"
    )
    thank_you_parser.add_argument(
        "--role", help='Role interviewed for, e.g. "Senior .NET Developer"'
    )
    thank_you_parser.add_argument(
        "--interviewer",
        action="append",
        dest="interviewers",
        help="Interviewer name (repeatable)",
    )
    thank_you_parser.add_argument("--date", help="Interview date")
    thank_you_parser.add_argument(
        "--discussion-point",
        action="append",
        dest="discussion_points",
        help="A specific detail from the actual interview (repeatable, required — "
        "1-2 points). Generation refuses without at least one.",
    )
    thank_you_parser.add_argument("--out", type=Path, help="Output DOCX path")

    interview_parser = subparsers.add_parser(
        "interview-prep", help="Generate an interview prep DOCX for a JD"
    )
    interview_parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    interview_parser.add_argument(
        "--stage",
        choices=["phone_screen", "technical_screen", "final_round"],
        help="Interview stage — gates document scope (default: technical_screen)",
    )
    interview_parser.add_argument("--out", type=Path, help="Output DOCX file path")
    interview_parser.add_argument(
        "--update-star-bank",
        action="store_true",
        help="Write updated last_used/used_for metadata back to star-bank.md "
        "for every STAR story selected in this run",
    )
    interview_parser.add_argument(
        "--star-bank-path",
        type=Path,
        help="Override path to star-bank.md (test-only; defaults to the real reference file)",
    )
    interview_parser.add_argument(
        "--company-research",
        type=Path,
        help="Path to a text file of company-research prose (e.g. web_search findings)",
    )
    interview_parser.add_argument(
        "--recruiter-briefing",
        type=Path,
        help="Path to a text file with a pasted recruiter briefing",
    )
    interview_parser.add_argument(
        "--qa-cards",
        type=Path,
        help="Path to a JSON file of LLM-authored Q&A cards",
    )
    interview_parser.add_argument(
        "--salary-section",
        type=Path,
        help="Path to a text file of salary/negotiation prose (final_round stage only)",
    )

    learning_plan_parser = subparsers.add_parser(
        "generate-learning-plan", help="Render a role-specific Learning Plan PDF from a JSON config"
    )
    learning_plan_parser.add_argument(
        "role_json",
        type=Path,
        help="Path to a role config JSON (see project-2-profile-learning-hub/roles/_example.json)",
    )

    args = parser.parse_args(argv)

    if args.command == "build":
        return _build()
    if args.command == "validate":
        return _validate()
    if args.command == "fit-check":
        return _fit_check(args.jd)
    if args.command == "gap-analysis":
        return _gap_analysis(args.jd, getattr(args, "out", None))
    if args.command == "generate-linkedin":
        return _generate_linkedin(getattr(args, "out", None))
    if args.command == "generate-github":
        return _generate_github(getattr(args, "out", None))
    if args.command == "generate-jobgether":
        return _generate_jobgether(getattr(args, "out", None))
    if args.command == "generate-job-board":
        return _generate_job_board(getattr(args, "out", None))
    if args.command == "generate-pluralsight":
        return _generate_pluralsight(getattr(args, "out", None))
    if args.command in _LETTER_GENERATORS:
        return _generate_letter(
            args.command,
            args.jd,
            getattr(args, "company", None),
            getattr(args, "out", None),
        )
    if args.command == "generate-cold-call":
        return _generate_cold_call(
            args.jd,
            getattr(args, "company", None),
            getattr(args, "recruiter_name", None),
            getattr(args, "role_type", None),
            getattr(args, "out", None),
        )
    if args.command == "generate-thank-you":
        return _generate_thank_you(
            args.jd,
            getattr(args, "company", None),
            getattr(args, "role", None),
            getattr(args, "interviewers", None),
            getattr(args, "date", None),
            getattr(args, "discussion_points", None),
            getattr(args, "out", None),
        )
    if args.command == "interview-prep":
        return _interview_prep(
            args.jd,
            getattr(args, "out", None),
            getattr(args, "stage", None),
            getattr(args, "update_star_bank", False),
            getattr(args, "star_bank_path", None),
            getattr(args, "company_research", None),
            getattr(args, "recruiter_briefing", None),
            getattr(args, "qa_cards", None),
            getattr(args, "salary_section", None),
        )
    if args.command == "generate-learning-plan":
        return _generate_learning_plan(args.role_json)
    parser.error("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
