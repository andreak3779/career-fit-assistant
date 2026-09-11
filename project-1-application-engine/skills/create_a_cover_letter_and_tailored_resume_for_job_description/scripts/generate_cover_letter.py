#!/usr/bin/env python3
"""Generate a JD-tailored cover-letter DOCX from the profile bundle."""

from __future__ import annotations

import argparse
import sys
from datetime import date
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
    humanize_evidence,
    load_profile_bundle,
    name_prefix,
    parse_jd,
    profile_has_skill_text,
    rate_fit,
    slugify,
)
from shared.docx_layout import (
    BODY_SIZE,
    DEFAULT_SIGNATURE_NAME,
    add_paragraph,
    centered_contact_block,
    section_heading,
    set_margins,
)
from shared.provenance import write_sidecar


def _select_evidence(
    bundle: Any,
    parsed: Any,
    company: str,
    result: FitResult,
) -> dict[str, Any]:
    """Pick hook, bring-items, and highlights from verified bundle evidence.

    The caller passes in the precomputed ``FitResult`` so we don't double-rate.
    Only production (`match`) and portfolio evidence are used in the body.
    Coursework and gaps are omitted from the letter unless the bundle explicitly
    tracks them as planned learning (never claimed as experience).
    """
    grounded_required = result.grounded_required
    top_match = next(
        (m for m in grounded_required if m.status == "match"),
        grounded_required[0] if grounded_required else None,
    )

    # Portfolio projects that match required skills (alias-aware).
    matching_projects: list[Any] = []
    for project in bundle.portfolio_projects:
        text = f"{project.name} {' '.join(project.stack)} {project.description}"
        if profile_has_skill_text(" ".join(parsed.required), text):
            matching_projects.append(project)

    # WHAT-I-BRING: grounded required first, then grounded nice-to-have.
    bring: list[dict[str, str]] = []
    for m in grounded_required + [m for m in result.nice_to_have if m.is_grounded]:
        bring.append({"label": m.skill.title(), "body": humanize_evidence(m)})
        if len(bring) >= 5:
            break

    # Highlights: up to 2 employers / portfolio projects with required-skill overlap.
    highlights: list[dict[str, str]] = []
    for exp in bundle.resume.experience:
        bullets_joined = " ".join(exp.bullets).lower()
        score = sum(1 for req in parsed.required if req.lower() in bullets_joined)
        if score:
            best_bullet = max(
                exp.bullets,
                key=lambda b: sum(1 for r in parsed.required if r.lower() in b.lower()),
                default="",
            )
            highlights.append(
                {
                    "label": f"{exp.company} ({exp.dates or 'recent'})",
                    "body": best_bullet,
                }
            )
            if len(highlights) >= 2:
                break
    for project in matching_projects:
        if len(highlights) >= 2:
            break
        stack_text = clean_stack(project.stack, limit=4)
        highlights.append(
            {
                "label": f"{project.name} (portfolio)",
                "body": f"{project.description} Built with {stack_text}."
                if stack_text
                else project.description,
            }
        )

    # Hook: if no verified evidence, use a neutral hook rather than fabricate fit.
    top_required = parsed.required[0] if parsed.required else parsed.title
    if top_match:
        hook = (
            f"{company} is looking for {top_required} — and that is exactly where my background "
            f"fits. {humanize_evidence(top_match).capitalize()} gives me production-level depth I can "
            f"bring to the {parsed.title} role immediately."
        )
    elif matching_projects:
        p = matching_projects[0]
        stack = clean_stack(p.stack, limit=3)
        hook = (
            f"{company}’s {parsed.title} opening aligns with my recent portfolio work on {p.name}, "
            f"where I used {stack}. I’m ready to scale that impact on your team."
        )
    else:
        hook = (
            f"I’m excited about the {parsed.title} role at {company} and would welcome a "
            f"conversation about how my background could support the team."
        )

    # Closing: focus on verified skills only, falling back to neutral phrasing.
    focus_skills = [m.skill for m in grounded_required[:2]]
    if focus_skills:
        focus = ", ".join(focus_skills)
        closing = (
            f"I’m excited about the work {company} is doing and would welcome a "
            f"conversation about how my background in {focus} can support the team. "
            f"Could we schedule a brief call to explore the fit?"
        )
    else:
        closing = (
            f"I’m excited about the work {company} is doing and would welcome a "
            f"conversation about how my background could support the {parsed.title} team."
        )

    low_confidence = len(grounded_required) < 2 and not matching_projects

    return {
        "bring": bring,
        "highlights": highlights,
        "hook": hook,
        "closing": closing,
        "low_confidence": low_confidence,
    }


def _bullet_para(doc: Document, label: str, body: str) -> None:
    """Backward-compatible thin wrapper. Prefer ``bullet_label_para`` directly."""
    bullet_label_para(doc, label, body)


def generate_cover_letter(
    jd_path: Path,
    *,
    bundle: Any | None = None,
    company: str | None = None,
    out_path: Path | None = None,
    root: Path = ROOT,
) -> tuple[Path, Path, FitResult]:
    """Build and write a tailored cover-letter DOCX plus provenance sidecar."""
    bundle = bundle or load_profile_bundle(root)
    jd_text = jd_path.read_text(encoding="utf-8")
    parsed = parse_jd(jd_text)
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)
    company = company or parsed.company
    evidence = _select_evidence(bundle, parsed, company, result)

    if out_path is None:
        slug = slugify(company)
        out_path = root / "outputs" / f"{name_prefix(bundle.contact.name)}_CoverLetter_{slug}.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    set_margins(doc.sections[0])
    centered_contact_block(doc, bundle.contact, tagline=bundle.resume.headline, space_after=Pt(8))

    add_paragraph(
        doc,
        date.today().strftime("%B %d, %Y"),
        size=BODY_SIZE,
        space_before=Pt(8),
    )
    add_paragraph(
        doc,
        f"Re: {parsed.title} — {company}",
        bold=True,
        size=BODY_SIZE,
        space_before=Pt(8),
    )
    add_paragraph(
        doc,
        f"Dear {company} Hiring Team,",
        size=BODY_SIZE,
        space_after=Pt(4),
    )

    add_paragraph(doc, evidence["hook"], size=BODY_SIZE, space_before=Pt(8))

    section_heading(doc, "What I Bring")
    for item in evidence["bring"]:
        _bullet_para(doc, item["label"], item["body"])

    section_heading(doc, "Two Relevant Highlights")
    for item in evidence["highlights"]:
        _bullet_para(doc, item["label"], item["body"])

    add_paragraph(doc, evidence["closing"], size=BODY_SIZE, space_before=Pt(8))
    add_paragraph(doc, "Sincerely,", size=BODY_SIZE, space_before=Pt(12))
    add_paragraph(
        doc,
        (bundle.contact.name or DEFAULT_SIGNATURE_NAME).upper(),
        size=BODY_SIZE,
        space_before=Pt(18),
    )

    doc.save(str(out_path))

    if evidence["low_confidence"]:
        print(
            f"WARNING: only {len(result.grounded_required)} required skill(s) have verified evidence; "
            "letter drafted cautiously.",
            file=sys.stderr,
        )

    sidecar = write_sidecar(
        out_path,
        script="generate_cover_letter.py",
        bundle=bundle,
        inputs=[str(jd_path)],
        fit_rating=result.rating,
        evidence_sources=result.evidence_sources(),
        warnings=["low evidence — manually review before sending"]
        if evidence["low_confidence"]
        else [],
    )
    return out_path, sidecar, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-cover-letter", description="Generate a tailored cover-letter DOCX"
    )
    parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    parser.add_argument("--company", help="Override company name used in filename")
    parser.add_argument("--out", type=Path, help="Output DOCX path")
    parser.add_argument("--bundle", type=Path, help="Path to profile-bundle.json")
    args = parser.parse_args(argv)

    try:
        require_path(args.jd, "JD file")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out, sidecar, _ = generate_cover_letter(
        args.jd,
        bundle=load_profile_bundle(args.bundle or ROOT),
        company=args.company,
        out_path=args.out,
    )
    print(f"Wrote {out}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
