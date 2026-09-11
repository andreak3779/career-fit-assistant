#!/usr/bin/env python3
"""Generate a cold-call (unsolicited) cover-letter DOCX from the profile bundle."""

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
    bullet_label_para,
    clean_stack,
    load_profile_bundle,
    looks_unknown,
    name_prefix,
    parse_jd,
    rate_fit,
    slugify,
    split_label_body,
)
from shared.docx_layout import (
    BODY_SIZE,
    add_paragraph,
    letter_footer,
    letter_header,
    section_heading,
)
from shared.provenance import write_sidecar


def _read_target_description(jd_path: Path | None) -> tuple[str, str]:
    """Return (company, description) from a target file if one is supplied.

    ``jd_path`` is optional — cold outreach is usually conversational, with no
    JD in hand (see ``--recruiter-name``/``--role-type`` on ``main()``). If
    ``jd_path`` points at a markdown file with a real company/title, parse it
    like a JD to get those fields. Otherwise the description is empty (or the
    raw file text, if one was given) and the company defaults to
    ``"Your Company"``.
    """
    if jd_path is None:
        return "Your Company", ""
    text = jd_path.read_text(encoding="utf-8")
    if jd_path.suffix.lower() in (".md", ".markdown"):
        parsed = parse_jd(text)
        # If parse_jd found a real company AND a real title, treat the file as
        # a proper JD. A blank ``**Company:**`` line parses to "" which we
        # treat the same as "Unknown Company".
        if not looks_unknown(parsed.company) and not looks_unknown(parsed.title):
            return parsed.company, text
    return "Your Company", text


def _select_evidence(bundle: Any, company: str, role_type: str | None = None) -> dict[str, Any]:
    """Pick a short hook, 2–3 bring-items, and a closing for a cold outreach.

    All claims are sourced from the bundle (differentiators, technical-skills
    categories, and portfolio projects). No JD-specific assertions are made.
    ``role_type`` (e.g. "Senior .NET Developer roles") names the kind of role
    being sought — the cold-outreach skill's actual intake question — and is
    threaded into the hook so the letter isn't purely company-generic.
    """
    top_differentiators = bundle.differentiators[:3]
    has_portfolio = bool(bundle.portfolio_projects)
    has_differentiators = bool(top_differentiators)

    differentiator_text = "; ".join(top_differentiators) if top_differentiators else bundle.headline
    role_clause = f" for {role_type}" if role_type else ""

    if has_differentiators or has_portfolio:
        hook = (
            f"I’m reaching out because the work {company} is doing looks like a strong match "
            f"for my background as a {bundle.resume.headline}, and I wanted to introduce myself "
            f"in case you're hiring{role_clause}. "
            f"Highlights include: {differentiator_text}."
        )
    else:
        hook = (
            f"I’m reaching out because the work {company} is doing looks interesting, "
            f"and I’d welcome a brief conversation about opportunities{role_clause} where my "
            f"background as a {bundle.resume.headline} could be relevant."
        )

    # Bring: top differentiators split into (label, body) using the shared
    # separator-aware helper. Cap at 3 items.
    bring: list[dict[str, str]] = []
    for diff in top_differentiators:
        label, body = split_label_body(diff)
        bring.append({"label": label, "body": body})
        if len(bring) >= 3:
            break

    # Fallback if differentiators are sparse: list technical-skill categories
    # without claiming hands-on production experience for every keyword.
    if not bring and bundle.resume.technical_skills:
        cat = bundle.resume.technical_skills[0]
        skills = ", ".join(cat.skills[:4])
        bring.append({"label": cat.category, "body": f"Background includes {skills}."})

    # Portfolio highlight (one only, cold letters stay short).
    portfolio_highlight = ""
    if has_portfolio:
        project = bundle.portfolio_projects[0]
        stack = clean_stack(project.stack, limit=3)
        portfolio_highlight = (
            f"A recent example is {project.name}, built with {stack}, where {project.description[:140].rstrip('.')}..."
            if stack
            else f"A recent example is {project.name}, where {project.description[:160].rstrip('.')}..."
        )

    closing = (
        f"I would welcome a brief conversation to learn more about {company}’s current challenges "
        f"and how I might contribute. Could we schedule a 15-minute intro call?"
    )

    evidence_sources = []
    if has_portfolio:
        evidence_sources.append(bundle.portfolio_projects[0].name)
    evidence_sources.extend(
        label for label, _ in (split_label_body(d) for d in top_differentiators)
    )

    low_confidence = not has_differentiators and not has_portfolio

    return {
        "bring": bring,
        "hook": hook,
        "portfolio_highlight": portfolio_highlight,
        "closing": closing,
        "evidence_sources": evidence_sources,
        "low_confidence": low_confidence,
    }


def _empty_fit_result() -> FitResult:
    """Honest ``FitResult`` for cold calls where we couldn't parse a JD.

    We deliberately do NOT rate the candidate against their own headline
    (that's a self-fit and always Strong), nor against an arbitrary fallback
    — the rating would be noise. Return ``"Stretch"`` as a reasonable default
    since cold outreach is by definition speculative.
    """
    return FitResult(
        rating="Stretch",
        required=[],
        nice_to_have=[],
        rationale="No JD provided — fit not assessed.",
    )


def generate_cold_call_letter(
    jd_path: Path | None = None,
    *,
    bundle: Any | None = None,
    company: str | None = None,
    recruiter_name: str | None = None,
    role_type: str | None = None,
    out_path: Path | None = None,
    root: Path = ROOT,
) -> tuple[Path, Path, FitResult]:
    """Build and write a cold-call cover-letter DOCX plus provenance sidecar.

    ``jd_path`` is optional — cold outreach is normally conversational, with
    no JD in hand. If a file is given and contains a company description, we
    use it; otherwise (the common case) supply ``recruiter_name``/
    ``role_type`` directly instead of synthesizing a throwaway JD file just to
    invoke this function.
    """
    bundle = bundle or load_profile_bundle(root)

    target_company, description = _read_target_description(jd_path)
    company = company or target_company

    # Compute a fit rating against the description so the sidecar is meaningful.
    # Only record the JD as an input when we actually parsed real skills from it.
    parsed = parse_jd(description)
    if parsed.required:
        result = rate_fit(parsed.required, parsed.nice_to_have, bundle)
        sidecar_inputs = [str(jd_path)]
    else:
        # No parseable JD skills — don't rate the candidate against themselves.
        result = _empty_fit_result()
        sidecar_inputs = []

    evidence = _select_evidence(bundle, company, role_type)

    if out_path is None:
        slug = slugify(company)
        out_path = root / "outputs" / f"{name_prefix(bundle.contact.name)}_ColdCall_{slug}.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    letter_header(
        doc,
        bundle.contact,
        company=company,
        tagline=bundle.resume.headline,
        salutation=f"Dear {recruiter_name}," if recruiter_name else "Dear Hiring Team,",
        re_line=f"Re: {role_type} Opportunities" if role_type else None,
    )

    add_paragraph(doc, evidence["hook"], size=BODY_SIZE, space_before=Pt(8))

    section_heading(doc, "Why I’m a Fit")
    for item in evidence["bring"]:
        bullet_label_para(doc, item["label"], item["body"])

    if evidence["portfolio_highlight"]:
        add_paragraph(
            doc,
            evidence["portfolio_highlight"],
            size=BODY_SIZE,
            space_before=Pt(6),
        )

    add_paragraph(doc, evidence["closing"], size=BODY_SIZE, space_before=Pt(8))
    letter_footer(doc, bundle.contact)

    doc.save(str(out_path))

    if evidence["low_confidence"]:
        print(
            "WARNING: cold-call letter has no differentiators or portfolio projects; "
            "draft is generic — manually review before sending.",
            file=sys.stderr,
        )

    sidecar = write_sidecar(
        out_path,
        script="generate_cold_call_letter.py",
        bundle=bundle,
        inputs=sidecar_inputs,
        fit_rating=result.rating,
        evidence_sources=evidence["evidence_sources"],
        warnings=["low evidence — manually review before sending"]
        if evidence["low_confidence"]
        else [],
    )
    return out_path, sidecar, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-cold-call",
        description="Generate a short cold-call cover-letter DOCX",
    )
    parser.add_argument(
        "jd",
        type=Path,
        nargs="?",
        default=None,
        help="Optional path to a target company description or JD markdown file. "
        "Cold outreach is usually conversational — omit this and use "
        "--recruiter-name/--role-type instead.",
    )
    parser.add_argument("--company", help="Override company name used in filename and salutation")
    parser.add_argument(
        "--recruiter-name", help='Salutation name, e.g. "Jane Doe" (default: "Hiring Team")'
    )
    parser.add_argument("--role-type", help='Target role type, e.g. "Senior .NET Developer roles"')
    parser.add_argument("--out", type=Path, help="Output DOCX path")
    parser.add_argument("--bundle", type=Path, help="Path to profile-bundle.json")
    args = parser.parse_args(argv)

    if args.jd is not None:
        try:
            require_path(args.jd, "JD file")
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    out, sidecar, _ = generate_cold_call_letter(
        args.jd,
        bundle=load_profile_bundle(args.bundle or ROOT),
        company=args.company,
        recruiter_name=args.recruiter_name,
        role_type=args.role_type,
        out_path=args.out,
    )
    print(f"Wrote {out}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
