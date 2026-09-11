#!/usr/bin/env python3
"""Generate a post-interview thank-you / follow-up letter from the profile bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]

from docx import Document
from docx.shared import Pt
from project_1_application_engine.scripts._cli_common import require_path

from shared import (
    FitResult,
    load_profile_bundle,
    looks_unknown,
    name_prefix,
    parse_jd,
    rate_fit,
    slugify,
)
from shared.docx_layout import (
    BODY_SIZE,
    add_paragraph,
    letter_footer,
    letter_header,
    section_heading,
)
from shared.provenance import write_sidecar


def _select_star_story(bundle: Any, required: list[str], nice_to_have: list[str]) -> Any | None:
    """Return the best-fitting STAR story, if any, based on JD-tag overlap."""
    pool = [s.lower() for s in required + nice_to_have]
    scored: list[tuple[int, Any]] = []
    for story in bundle.resume.star_stories:
        text = f"{story.title} {' '.join(story.jd_tags)} {story.situation} {story.action} {story.result}".lower()
        score = sum(1 for term in pool if term in text)
        if score:
            scored.append((score, story))
    scored.sort(key=lambda t: t[0], reverse=True)
    return scored[0][1] if scored else None


def _build_letter(
    company: str,
    role: str,
    interviewer_names: list[str],
    interview_date: str | None,
    discussion_points: list[str],
    result: FitResult,
    bundle: Any,
    parsed: Any,
) -> dict[str, Any]:
    """Compose opening, KEY TAKEAWAYS, and closing.

    ``discussion_points`` — real details from the actual interview — are the
    primary content, per the skill's grounding rule ("must come from the
    user's actual account of the interview... do not substitute generic
    differentiators"). Grounded-skill evidence and a matching STAR story are
    secondary: a short reinforcing clause and an optional example, never the
    letter's main substance.
    """
    who = ", ".join(interviewer_names) if interviewer_names else None
    date_clause = f" on {interview_date}" if interview_date else " today"
    opening = (
        f"Thank you, {who}, for taking the time to speak with me{date_clause} "
        f"about the {role} role at {company}."
        if who
        else f"Thank you for taking the time to speak with me{date_clause} "
        f"about the {role} role at {company}."
    )

    grounded = result.grounded_required[:2]
    if grounded:
        req_text = ", ".join(m.skill for m in grounded)
        opening += (
            f" Our conversation reinforced how well my background in {req_text} "
            f"lines up with what the team needs."
        )

    # STAR story anchor — secondary and optional, sourced from the bundle.
    star = _select_star_story(bundle, parsed.required, parsed.nice_to_have)
    star_para = ""
    if star:
        star_summary = f"{star.situation} {star.task} {star.action} {star.result}".strip()
        star_para = (
            f"One example from my experience that may be relevant: {star.title.lower()} — "
            f"{star_summary[:220].rstrip('.')}... I’d be glad to walk through the full story in a follow-up conversation."
        )

    closing = (
        "Please don’t hesitate to reach out if I can provide any additional information. "
        "I’m very interested in the opportunity and look forward to hearing about next steps."
    )

    return {
        "opening": opening,
        "key_takeaways": list(discussion_points),
        "star": star_para,
        "closing": closing,
    }


def generate_thank_you_letter(
    jd_path: Path | None = None,
    *,
    bundle: Any | None = None,
    company: str | None = None,
    role: str | None = None,
    interviewer_names: list[str] | None = None,
    interview_date: str | None = None,
    discussion_points: list[str] | None = None,
    out_path: Path | None = None,
    root: Path = ROOT,
) -> tuple[Path, Path, FitResult]:
    """Build and write a thank-you letter DOCX plus provenance sidecar.

    ``discussion_points`` is required — at least one specific detail from the
    actual interview conversation. This letter must never be generated from
    generic differentiators as a stand-in (see the skill's grounding rule);
    unlike ``company``/``role``, which fall back to generic phrasing when
    absent, there's no honest generic substitute for "what did you actually
    discuss," so this fails closed instead.

    ``jd_path`` is optional and, when given, only supplies company/role/
    skills-fit context as a convenience — it never substitutes for real
    discussion points.
    """
    if not discussion_points:
        raise ValueError(
            "discussion_points is required: at least one specific detail from the actual "
            "interview conversation. Ask the user what was discussed — do not substitute "
            "generic differentiators."
        )

    bundle = bundle or load_profile_bundle(root)
    jd_text = jd_path.read_text(encoding="utf-8") if jd_path is not None else ""
    parsed = parse_jd(jd_text)
    if parsed.required:
        result = rate_fit(parsed.required, parsed.nice_to_have, bundle)
    else:
        result = FitResult(
            rating="Stretch",
            required=[],
            nice_to_have=[],
            rationale="No JD provided — fit not assessed.",
        )
    company = company or (parsed.company if not looks_unknown(parsed.company) else "your company")
    role = role or (parsed.title if not looks_unknown(parsed.title) else "the role")
    interviewer_names = interviewer_names or []

    if out_path is None:
        slug = slugify(company)
        out_path = root / "outputs" / f"{name_prefix(bundle.contact.name)}_ThankYou_{slug}.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    letter = _build_letter(
        company, role, interviewer_names, interview_date, discussion_points, result, bundle, parsed
    )

    salutation = (
        f"Dear {', '.join(interviewer_names)},"
        if interviewer_names
        else "Dear {company} Hiring Team,"
    )
    doc = Document()
    letter_header(
        doc,
        bundle.contact,
        company=company,
        tagline=bundle.resume.headline,
        salutation=salutation,
        re_line=f"Re: Thank You — {role} Interview, {company}",
    )

    add_paragraph(doc, letter["opening"], size=BODY_SIZE, space_before=Pt(8))

    section_heading(doc, "Key Takeaways")
    for point in letter["key_takeaways"]:
        add_paragraph(doc, f"•  {point}", size=BODY_SIZE, space_before=Pt(4))

    if letter["star"]:
        add_paragraph(doc, letter["star"], size=BODY_SIZE, space_before=Pt(8))

    add_paragraph(doc, letter["closing"], size=BODY_SIZE, space_before=Pt(8))
    letter_footer(doc, bundle.contact)

    doc.save(str(out_path))

    low_confidence = not result.grounded_required
    if low_confidence:
        print(
            "WARNING: thank-you letter has no grounded required-skill evidence; "
            "the reinforcing clause is omitted — the letter still rests on the real "
            "discussion points supplied, but manually review before sending.",
            file=sys.stderr,
        )

    sidecar = write_sidecar(
        out_path,
        script="generate_thank_you_letter.py",
        bundle=bundle,
        inputs=[str(jd_path)] if jd_path is not None else [],
        fit_rating=result.rating,
        evidence_sources=result.evidence_sources(),
        warnings=["low evidence — manually review before sending"] if low_confidence else [],
    )
    return out_path, sidecar, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-thank-you",
        description="Generate a post-interview thank-you letter DOCX",
    )
    parser.add_argument(
        "jd",
        type=Path,
        nargs="?",
        default=None,
        help="Optional path to a job description markdown file, for company/role/"
        "skills-fit context. Never a substitute for --discussion-point.",
    )
    parser.add_argument("--company", help="Override company name used in filename and salutation")
    parser.add_argument("--role", help='Role interviewed for, e.g. "Senior .NET Developer"')
    parser.add_argument(
        "--interviewer",
        action="append",
        dest="interviewers",
        help='Interviewer name (repeatable), e.g. --interviewer "Jane Doe"',
    )
    parser.add_argument("--date", help='Interview date, e.g. "August 25, 2026"')
    parser.add_argument(
        "--discussion-point",
        action="append",
        dest="discussion_points",
        help="A specific detail from the actual interview conversation (repeatable, "
        "required — 1-2 points). This letter refuses to generate without at least one.",
    )
    parser.add_argument("--out", type=Path, help="Output DOCX path")
    parser.add_argument("--bundle", type=Path, help="Path to profile-bundle.json")
    args = parser.parse_args(argv)

    if args.jd is not None:
        try:
            require_path(args.jd, "JD file")
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    try:
        out, sidecar, _ = generate_thank_you_letter(
            args.jd,
            bundle=load_profile_bundle(args.bundle or ROOT),
            company=args.company,
            role=args.role,
            interviewer_names=args.interviewers,
            interview_date=args.date,
            discussion_points=args.discussion_points,
            out_path=args.out,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {out}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
