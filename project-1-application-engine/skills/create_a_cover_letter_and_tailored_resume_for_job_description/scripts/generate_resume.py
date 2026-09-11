#!/usr/bin/env python3
"""Generate a JD-tailored resume DOCX from the profile bundle."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]

from docx import Document
from docx.shared import Inches, Pt
from project_1_application_engine.scripts._cli_common import require_path

from shared import (
    FitResult,
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
    SUMMARY_SIZE,
    add_paragraph,
    centered_contact_block,
    section_heading,
    set_margins,
)
from shared.provenance import write_sidecar

_PAGE2_HEADER_SIZE = Pt(9)


def _add_page2_header(doc: Document, contact: Any) -> None:
    """Mirror templates/resume-template.js's page-2+ running header.

    Resumes here run 1-2 pages by design. If content spills to a second
    page, python-docx's default behavior repeats nothing at the top of it —
    the reader loses the name/contact line that page 1 carries in its
    centered contact block. The JS template solves this with Word's native
    odd/even header split (``evenAndOddHeaderAndFooters`` + an explicit
    ``even`` header, "needed so page 2 (even) inherits the running header");
    this reproduces the same mechanism via python-docx's equivalent APIs.
    Page 1 keeps an empty header (its own contact block already covers it);
    page 2 (even) and any page 3+ (odd, default) get a compact one-line
    "Name | email | phone | location | linkedin | github | pluralsight"
    header — same content as the JS version, not merely a warning.
    """
    doc.settings.odd_and_even_pages_header_footer = True

    section = doc.sections[0]
    section.different_first_page_header_footer = True

    parts = [
        (contact.name or DEFAULT_SIGNATURE_NAME).upper(),
        contact.email,
        contact.phone,
        contact.location,
        contact.linkedin,
        contact.github,
        contact.pluralsight,
    ]
    line = "  |  ".join(p for p in parts if p)

    for header in (section.header, section.even_page_header):
        header.is_linked_to_previous = False
        p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        p.text = ""
        run = p.add_run(line)
        run.font.name = "Carlito"
        run.font.size = _PAGE2_HEADER_SIZE

    section.first_page_header.is_linked_to_previous = False
    for p in list(section.first_page_header.paragraphs):
        p.text = ""


def _skill_score(skill: str, jd_pool: str) -> int:
    """Count how many JD tokens/aliases this resume skill overlaps.

    Uses the fit engine's alias expansion so a resume skill like
    ``"Azure (AZ-900)"`` boosts against a JD asking for ``"AZ-900"``.
    """
    return 1 if profile_has_skill_text(skill, jd_pool) else 0


def _bullet_score(bullet: str, jd_pool: str) -> int:
    """Score a bullet by alias-aware matches against the JD pool.

    Each unique JD skill that hits this bullet (after alias expansion)
    contributes one point. Counts are bounded by the number of JD skills so
    longer bullets don't get a free length boost.
    """
    jd_terms = {t.lower() for t in re.split(r"[/;,\s]+", jd_pool) if len(t) > 1}
    if not jd_terms:
        return 0
    return sum(1 for t in jd_terms if profile_has_skill_text(t, bullet))


def _skill_lines(doc: Document, bundle: Any, parsed: Any) -> None:
    """Emit technical-skills categories, ordering by JD relevance."""
    jd_pool = " ".join(parsed.required + parsed.nice_to_have)
    categories = list(bundle.resume.technical_skills)
    categories.sort(
        key=lambda cat: sum(_skill_score(s, jd_pool) for s in cat.skills),
        reverse=True,
    )
    for cat in categories:
        skills = ", ".join(cat.skills)
        p = add_paragraph(
            doc,
            f"{cat.category}: ",
            bold=True,
            size=BODY_SIZE,
            space_after=Pt(2),
        )
        p.add_run(skills).font.size = BODY_SIZE


def _experience(doc: Document, bundle: Any, parsed: Any) -> None:
    jd_pool = " ".join(parsed.required + parsed.nice_to_have)

    for job in bundle.resume.experience:
        bullets = sorted(job.bullets, key=lambda b: _bullet_score(b, jd_pool), reverse=True)
        left = job.title
        if job.company:
            left += f" | {job.company}"
        if job.location:
            left += f", {job.location}"
        p = add_paragraph(
            doc,
            left,
            bold=True,
            size=SUMMARY_SIZE,
            space_before=Pt(6),
            keep_next=True,
        )
        if job.dates:
            p.add_run(f"\t{job.dates}").font.italic = True
            # Right-align dates at the page edge (page width minus side margins).
            right_tab = Inches(8.5 - 0.75 - 0.5)
            p.paragraph_format.tab_stops.add_tab_stop(right_tab, 2)
        for b in bullets:
            bp = add_paragraph(
                doc,
                f"\u2022  {b}",
                size=BODY_SIZE,
                space_after=Pt(2),
            )
            bp.paragraph_format.left_indent = Inches(0.25)
            bp.paragraph_format.first_line_indent = Inches(-0.15)


def _certifications(doc: Document, bundle: Any) -> None:
    certs = {c.code: c for c in bundle.cert_registry}
    az900 = certs.get("AZ-900")
    ai200 = certs.get("AI-200")
    if az900:
        note = az900.notes or az900.status.value
        add_paragraph(
            doc,
            f"\u2022  Microsoft Azure Fundamentals (AZ-900) — {note}",
            size=BODY_SIZE,
        )
    if ai200:
        note = ai200.notes or ai200.status.value
        add_paragraph(
            doc,
            f"\u2022  Azure AI Cloud Developer Associate (AI-200) — {note}",
            size=BODY_SIZE,
        )
    for c in bundle.resume.certifications:
        add_paragraph(doc, f"\u2022  {c.code} — {c.status.value}", size=BODY_SIZE)


def _education(doc: Document, bundle: Any) -> None:
    for edu in bundle.resume.education:
        line = f"{edu.credential} — {edu.institution}"
        if edu.dates:
            line += f", {edu.dates}"
        add_paragraph(doc, f"\u2022  {line}", size=BODY_SIZE)


def _build_tagline(parsed: Any, bundle: Any) -> str:
    """Compose a JD-aware tagline from role title + top skills."""
    title = parsed.title
    top_skills = parsed.required[:3]
    if not top_skills and bundle.resume.technical_skills:
        first_cat = bundle.resume.technical_skills[0]
        top_skills = first_cat.skills[:3]
    skills_text = " · ".join(top_skills)
    return f"{title} | {skills_text}" if skills_text else title


def generate_resume(
    jd_path: Path,
    *,
    bundle: Any | None = None,
    company: str | None = None,
    out_path: Path | None = None,
    root: Path = ROOT,
) -> tuple[Path, Path, FitResult]:
    """Build and write a tailored resume DOCX plus provenance sidecar.

    Returns ``(docx_path, sidecar_path, fit_result)``. The bundle is *not*
    mutated: a per-call copy of ``bundle.resume`` is created with the
    JD-specific headline.
    """
    bundle = bundle or load_profile_bundle(root)
    jd_text = jd_path.read_text(encoding="utf-8")
    parsed = parse_jd(jd_text)
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)

    company = company or parsed.company
    if out_path is None:
        slug = slugify(company)
        out_path = root / "outputs" / f"{name_prefix(bundle.contact.name)}_Resume_{slug}.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Local copy of the resume so successive calls don't see a stale headline.
    resume = replace(bundle.resume, headline=_build_tagline(parsed, bundle))

    doc = Document()
    set_margins(doc.sections[0])
    _add_page2_header(doc, bundle.contact)

    centered_contact_block(doc, bundle.contact, tagline=resume.headline)

    section_heading(doc, "Professional Summary")
    summary_lines = resume.summary.splitlines() if resume.summary else [""]
    for line in summary_lines[:2]:
        add_paragraph(doc, line.strip(), size=SUMMARY_SIZE, space_after=Pt(2))

    section_heading(doc, "Technical Skills")
    _skill_lines(doc, bundle, parsed)

    section_heading(doc, "Professional Experience")
    _experience(doc, bundle, parsed)

    if resume.education:
        section_heading(doc, "Education")
        _education(doc, bundle)

    section_heading(doc, "Certifications")
    _certifications(doc, bundle)

    doc.save(str(out_path))

    sidecar = write_sidecar(
        out_path,
        script="generate_resume.py",
        bundle=bundle,
        inputs=[str(jd_path)],
        fit_rating=result.rating,
    )
    return out_path, sidecar, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-resume", description="Generate a tailored resume DOCX"
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

    root = ROOT
    bundle = load_profile_bundle(args.bundle or root)
    out, sidecar, _ = generate_resume(
        args.jd,
        bundle=bundle,
        company=args.company,
        out_path=args.out,
        root=root,
    )
    print(f"Wrote {out}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
