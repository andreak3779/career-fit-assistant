#!/usr/bin/env python3
"""Generate a very short job-site cover letter (plain text) from the profile bundle.

This generator is the deliberate exception to the DOCX-only rule: job sites
usually want plain text for their paste-box. It defaults to a ``.txt`` file.
If ``--out`` ends in ``.docx`` we still produce a DOCX using the shared helpers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from docx import Document
from docx.shared import Pt
from project_1_application_engine.scripts._cli_common import require_path

from shared import (
    FitResult,
    clean_stack,
    humanize_evidence,
    load_profile_bundle,
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
)
from shared.provenance import write_sidecar


def _build_plain_text(
    company: str,
    title: str,
    result: FitResult,
    bundle: Any,
) -> str:
    """Return a 2-paragraph job-site paste-box cover letter as plain text.

    The hook routes evidence through ``humanize_evidence`` so the prose reads
    naturally (``"production evidence at Fieldstone Benefits Administrators"``) instead of the raw
    debug-grade ``"<skill> (<company>: production)"`` strings. We dedupe by
    lower-cased phrase to avoid repeating the same evidence form twice
    (e.g. two consecutive ``"production evidence at …"`` fragments).
    """
    top_matches = [m for m in result.required if m.status in ("match", "portfolio")][:2]
    if top_matches:
        seen: set[str] = set()
        evidence_bits: list[str] = []
        for m in top_matches:
            phrase = humanize_evidence(m)
            key = phrase.lower()
            if key not in seen:
                seen.add(key)
                evidence_bits.append(phrase)
        evidence_phrase = " and ".join(evidence_bits)
        hook = (
            f"I’m excited to apply for the {title} role at {company}. "
            f"My background includes {evidence_phrase}, and I’m eager to bring that depth to your team."
        )
    else:
        hook = (
            f"I’m excited to apply for the {title} role at {company}. "
            f"I’d welcome the opportunity to discuss how my background could support the team."
        )

    # Paragraph 2: concise closing + portfolio anchor.
    portfolio = ""
    if bundle.portfolio_projects:
        project = bundle.portfolio_projects[0]
        stack = clean_stack(project.stack, limit=3)
        portfolio = (
            f" You can see a recent example in {project.name} ({stack})."
            if stack
            else f" You can see a recent example in {project.name}."
        )

    closing = (
        f"I’d welcome the opportunity to discuss how my skills can support {company}’s goals.{portfolio} "
        "Thank you for your consideration."
    )

    return f"{hook}\n\n{closing}"


def _build_docx(
    company: str,
    title: str,
    text: str,
    bundle: Any,
    result: FitResult,
    out_path: Path,
    jd_path: Path,
) -> tuple[Path, Path, FitResult]:
    """Build a DOCX when the caller explicitly requests ``.docx``.

    Splits the plain-text body on blank lines and renders each chunk as a
    separate paragraph. The first paragraph sits flush against the date
    header; subsequent paragraphs get extra ``space_before`` so the DOCX
    visually matches the ``\\n\\n`` separation of the .txt version.
    """
    doc = Document()
    letter_header(
        doc,
        bundle.contact,
        company=company,
        tagline=bundle.resume.headline,
        re_line=f"Re: {title} — {company}",
    )
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    for i, paragraph in enumerate(paragraphs):
        space_before = Pt(8) if i == 0 else Pt(6)
        add_paragraph(doc, paragraph, size=BODY_SIZE, space_before=space_before)
    letter_footer(doc, bundle.contact)

    doc.save(str(out_path))

    sidecar = write_sidecar(
        out_path,
        script="generate_job_site_letter.py",
        bundle=bundle,
        inputs=[str(jd_path)],
        fit_rating=result.rating,
    )
    return out_path, sidecar, result


def generate_job_site_letter(
    jd_path: Path,
    *,
    bundle: Any | None = None,
    company: str | None = None,
    out_path: Path | None = None,
    root: Path = ROOT,
) -> tuple[Path, Path, FitResult]:
    """Build and write a short job-site cover letter plus provenance sidecar."""
    bundle = bundle or load_profile_bundle(root)
    jd_text = jd_path.read_text(encoding="utf-8")
    parsed = parse_jd(jd_text)
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)
    company = company or parsed.company

    if out_path is None:
        slug = slugify(company)
        out_path = root / "outputs" / f"{name_prefix(bundle.contact.name)}_JobSite_{slug}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    plain_text = _build_plain_text(company, parsed.title, result, bundle)

    if out_path.suffix.lower() == ".docx":
        return _build_docx(company, parsed.title, plain_text, bundle, result, out_path, jd_path)

    out_path.write_text(plain_text, encoding="utf-8")

    sidecar = write_sidecar(
        out_path,
        script="generate_job_site_letter.py",
        bundle=bundle,
        inputs=[str(jd_path)],
        fit_rating=result.rating,
    )
    return out_path, sidecar, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-job-site",
        description="Generate a short job-site cover letter (default: plain-text .txt)",
    )
    parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    parser.add_argument("--company", help="Override company name used in filename")
    parser.add_argument("--out", type=Path, help="Output path (default .txt; use .docx for DOCX)")
    parser.add_argument("--bundle", type=Path, help="Path to profile-bundle.json")
    args = parser.parse_args(argv)

    try:
        require_path(args.jd, "JD file")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out, sidecar, _ = generate_job_site_letter(
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
