"""Shared DOCX layout helpers for resume and cover-letter scripts.

Mirrors the JS helpers in ``project-1-application-engine/templates/_layout.js``
so the Python and JavaScript templates share the same brand colors and margins.
"""

from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any

from docx import Document

if TYPE_CHECKING:
    from shared.models import Contact

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

_SLUGIFY_RE = re.compile(r"[^a-z0-9]+")


BLUE = RGBColor(0x2E, 0x6D, 0xA4)
MARGIN_TOP_BOT = Inches(0.5)
MARGIN_SIDES = Inches(0.75)
BODY_SIZE = Pt(11)
SUMMARY_SIZE = Pt(10.5)
SECTION_SIZE = Pt(11)
NAME_SIZE = Pt(16)

# Fallback signature when a Contact has no name. Single source of truth so
# future forks / templates don't have to hunt through every script.
DEFAULT_SIGNATURE_NAME = "Sarah Ashford"


def set_margins(section: Any) -> None:
    """Set US-Letter margins matching the JS template."""
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = MARGIN_TOP_BOT
    section.bottom_margin = MARGIN_TOP_BOT
    section.left_margin = MARGIN_SIDES
    section.right_margin = MARGIN_SIDES


def add_paragraph(
    doc: Document,
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    align: Any = WD_ALIGN_PARAGRAPH.LEFT,
    size: Any = BODY_SIZE,
    color: Any = None,
    space_before: Any = Pt(0),
    space_after: Any = Pt(0),
    keep_next: bool = False,
) -> Any:
    """Add a single-run paragraph with the standard font."""
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = space_before
    p.paragraph_format.space_after = space_after
    p.paragraph_format.keep_with_next = keep_next
    run = p.add_run(text)
    run.font.name = "Carlito"
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = color
    return p


def section_heading(doc: Document, text: str) -> Any:
    """ALL CAPS blue section heading with bottom border."""
    p = add_paragraph(
        doc,
        text.upper(),
        bold=True,
        color=BLUE,
        size=SECTION_SIZE,
        space_before=Pt(8),
        space_after=Pt(2),
    )
    p.paragraph_format.border_bottom = True
    p.paragraph_format.border_bottom_color = BLUE
    p.paragraph_format.border_bottom_width = Pt(1)
    return p


def centered_contact_block(
    doc: Document,
    contact: Contact,
    tagline: str,
    *,
    space_after: Any = Pt(4),
) -> None:
    """Render the name/tagline/contact-lines header used on resume + cover letter.

    ``contact`` is a typed ``shared.models.Contact``. The function tolerates
    empty strings so older bundles without every field still render.
    """
    name = (contact.name or DEFAULT_SIGNATURE_NAME).upper()
    email = contact.email or ""
    phone = contact.phone or ""
    location = contact.location or ""
    linkedin = contact.linkedin or ""
    github = contact.github or ""
    pluralsight = contact.pluralsight or ""

    add_paragraph(doc, name, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=NAME_SIZE)
    if tagline:
        add_paragraph(doc, tagline, align=WD_ALIGN_PARAGRAPH.CENTER, size=BODY_SIZE)
    line1 = "  |  ".join(p for p in [email, phone, location] if p)
    line2 = "  |  ".join(p for p in [linkedin, github, pluralsight] if p)
    add_paragraph(doc, line1, align=WD_ALIGN_PARAGRAPH.CENTER, size=Pt(9.5))
    add_paragraph(
        doc,
        line2,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        size=Pt(9.5),
        space_after=space_after,
    )


def slugify(name: str) -> str:
    """Lowercase, collapse non-alnum runs to single underscores, strip edges.

    Centralized so output filenames stay consistent across all generators.
    """
    return _SLUGIFY_RE.sub("_", name.lower()).strip("_")


def name_prefix(name: str | None) -> str:
    """Return a CamelCase, space-free filename prefix for the candidate's name.

    Falls back to ``DEFAULT_SIGNATURE_NAME`` when ``name`` is empty so no
    generator ever hardcodes a literal candidate name in an output filename
    (e.g. ``f"{name_prefix(bundle.contact.name)}_Resume_{slug}.docx"``).
    """
    source = name or DEFAULT_SIGNATURE_NAME
    return "".join(part for part in source.split() if part)


def clean_stack(stack: list[str], *, limit: int | None = None) -> str:
    """Return a comma-joined stack string with whitespace-stripped tokens.

    Bundles occasionally serialize stack items with leading/trailing spaces;
    joining without ``.strip()`` produces ``"Angular ,  ASP.NET Core Web API"``.
    Empty entries are dropped so callers don't see dangling commas.
    """
    items = [s.strip() for s in stack if s and s.strip()]
    if limit is not None:
        items = items[:limit]
    return ", ".join(items)


def letter_header(
    doc: Document,
    contact: Contact,
    *,
    company: str,
    tagline: str,
    salutation: str = "Dear {company} Hiring Team,",
    re_line: str | None = None,
    contact_space_after: Any = Pt(8),
    salutation_space_after: Any = Pt(4),
) -> None:
    """Render the canonical top-of-letter block.

    Sets page margins, then emits: contact block, today's date, optional
    ``Re: <title> — <company>`` line, and the salutation.

    Use :func:`letter_footer` to emit the matching closing block.
    """
    set_margins(doc.sections[0])
    centered_contact_block(doc, contact, tagline=tagline, space_after=contact_space_after)
    add_paragraph(
        doc,
        date.today().strftime("%B %d, %Y"),
        size=BODY_SIZE,
        space_before=Pt(8),
    )
    if re_line:
        add_paragraph(doc, re_line, bold=True, size=BODY_SIZE, space_before=Pt(8))
    add_paragraph(
        doc,
        salutation.format(company=company),
        size=BODY_SIZE,
        space_after=salutation_space_after,
    )


def letter_footer(
    doc: Document,
    contact: Contact,
    *,
    close_phrase: str = "Sincerely,",
    close_space_before: Any = Pt(12),
    name_space_before: Any = Pt(18),
) -> None:
    """Render the canonical closing block: ``Sincerely,`` + uppercase name."""
    add_paragraph(doc, close_phrase, size=BODY_SIZE, space_before=close_space_before)
    add_paragraph(
        doc,
        (contact.name or DEFAULT_SIGNATURE_NAME).upper(),
        size=BODY_SIZE,
        space_before=name_space_before,
    )


def bullet_label_para(
    doc: Document,
    label: str,
    body: str,
    *,
    indent: Any = Inches(0.25),
    hanging: Any = Inches(-0.15),
    space_after: Any = Pt(6),
) -> Any:
    """Render a hanging-indent bullet: ``•  **Label:** body``.

    Used by the cover-letter and cold-call "what I bring" / "why I'm a fit"
    sections. The label is bold; the body is regular weight.
    """
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = indent
    p.paragraph_format.first_line_indent = hanging
    p.paragraph_format.space_after = space_after
    bullet = p.add_run("\u2022  ")
    bullet.font.name = "Carlito"
    bullet.font.size = BODY_SIZE
    label_run = p.add_run(f"{label}: ")
    label_run.font.name = "Carlito"
    label_run.font.size = BODY_SIZE
    label_run.bold = True
    body_run = p.add_run(body)
    body_run.font.name = "Carlito"
    body_run.font.size = BODY_SIZE
    return p


def split_label_body(text: str) -> tuple[str, str]:
    """Split a differentiator string into ``(label, body)``.

    Accepts colon, semicolon, en dash, em dash, or a *spaced* hyphen as the
    separator. A hyphen embedded in a word like ``"Full-stack"`` is *not* a
    separator — we only break on ``-`` when it's surrounded by whitespace.
    If no separator is present the full string is returned as both label
    and body so callers always get a non-empty label.
    """
    sep = re.search(r"\s*[:;\u2013\u2014]|\s+-\s+", text)
    if not sep:
        return text.strip(), text.strip()
    label = text[: sep.start()].strip()
    body = text[sep.end() :].strip()
    return (label or text.strip()), (body or text.strip())
