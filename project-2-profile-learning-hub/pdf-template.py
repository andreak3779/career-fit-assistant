"""
Learning Plan PDF Generator

Data-driven engine: reads role-specific content from
`roles/<role>.json` and renders a Learning Plan PDF.

Workflow:
  1. Create or update `roles/<your-role>.json` (copy from
     `roles/_example.json` and fill in).
  2. Run:  python pdf-template.py roles/<your-role>.json
  3. PDF is written to the path declared in the JSON's `output` key.

The PDF layout (colours, styles, card grid, page structure) is
defined here and is intentionally NOT editable per role — only data
is role-specific. See `skills/learning_plan_gap_analysis_SKILL.md`
for how role configs are produced from `profile-facts.md` and
`course-urls.md`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

__version__ = "0.9.0"

# ── Palette (whitelisted for `color` keys in role JSON) ──────────────────────
PALETTE: dict[str, colors.Color] = {
    "NAVY": colors.HexColor("#1B2A4A"),
    "RED": colors.HexColor("#DC2626"),
    "AMBER": colors.HexColor("#D97706"),
    "GREEN": colors.HexColor("#16A34A"),
    "PURP": colors.HexColor("#7C3AED"),
    "BLUE": colors.HexColor("#2563EB"),
    "LGRAY": colors.HexColor("#F1F5F9"),
    "MGRAY": colors.HexColor("#CBD5E1"),
    "WHITE": colors.white,
}


# ── Styles ──────────────────────────────────────────────────────────────────
def _S(name, **kw):
    return ParagraphStyle(name, **kw)


title_s = _S(
    "T",
    fontName="Helvetica-Bold",
    fontSize=18,
    textColor=PALETTE["WHITE"],
    alignment=TA_CENTER,
    spaceAfter=8,
)
_SUBTITLE_TEXT = colors.HexColor("#BFDBFE")
_BODY_TEXT = colors.HexColor("#1E293B")
_NOTE_TEXT = colors.HexColor("#64748B")
_LINK_TEXT = PALETTE["BLUE"]
_WARN_TEXT = PALETTE["RED"]

sub_s = _S(
    "Su",
    fontName="Helvetica",
    fontSize=9.5,
    textColor=_SUBTITLE_TEXT,
    alignment=TA_CENTER,
    spaceAfter=4,
)
body_s = _S("Bo", fontName="Helvetica", fontSize=9, textColor=_BODY_TEXT, leading=14)
link_s = _S("Li", fontName="Helvetica", fontSize=8, textColor=_LINK_TEXT, leading=13)
note_s = _S("No", fontName="Helvetica-Oblique", fontSize=8, textColor=_NOTE_TEXT, leading=12)
warn_s = _S("Wa", fontName="Helvetica-Bold", fontSize=9, textColor=_WARN_TEXT, leading=13)
sec_s = _S(
    "Se",
    fontName="Helvetica-Bold",
    fontSize=13,
    textColor=PALETTE["NAVY"],
    spaceBefore=14,
    spaceAfter=5,
)
ssec_s = _S(
    "SS",
    fontName="Helvetica-Bold",
    fontSize=10,
    textColor=PALETTE["BLUE"],
    spaceBefore=10,
    spaceAfter=3,
)


def _badge(label, colour):
    return _S(f"b{label}", fontName="Helvetica-Bold", fontSize=8, textColor=colour)


def _c(name: str) -> colors.Color:
    """Resolve a whitelisted palette name → reportlab Color. Unknown → ValueError."""
    if name not in PALETTE:
        raise ValueError(f"Unknown color '{name}'. Allowed: {sorted(PALETTE)}")
    return PALETTE[name]


# ── Card builder ────────────────────────────────────────────────────────────
def _course_card(num, source, colour, title, url, gap, hrs, W):
    inner = Table(
        [
            [Paragraph(f"<b>{num}. {title}</b>", body_s)],
            [Paragraph(f'<link href="{url}" color="{_LINK_TEXT.hexval()}">{url}</link>', link_s)],
            [Paragraph(f"Closes: {gap}", note_s)],
            [Paragraph(f"Est: {hrs}", note_s)],
        ],
        colWidths=[W - 1.05 * inch],
    )
    inner.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]
        )
    )
    badge_tbl = Table([[Paragraph(source, _badge(num, colour))]], colWidths=[0.95 * inch])
    badge_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALETTE["LGRAY"]),
                ("ROWPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    row = Table([[badge_tbl, inner]], colWidths=[1.0 * inch, W - 1.0 * inch])
    row.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALETTE["WHITE"]),
                ("BOX", (0, 0), (-1, -1), 0.5, PALETTE["MGRAY"]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEABOVE", (0, 0), (-1, 0), 1, colour),
            ]
        )
    )
    return row


# ── Document assembly ───────────────────────────────────────────────────────
def _build(cfg: dict) -> Path:
    output = Path(cfg["output"])
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: cannot create output directory {output.parent}: {exc}", file=sys.stderr)
        raise

    doc = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    W = letter[0] - 1.3 * inch
    story: list = []

    # Banner
    banner_cfg = cfg["banner"]
    banner = Table(
        [
            [Paragraph(banner_cfg["title"], title_s)],
            [Paragraph(banner_cfg["subtitle"], sub_s)],
            [Paragraph(banner_cfg["meta"], sub_s)],
        ],
        colWidths=[W],
    )
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALETTE["NAVY"]),
                ("TOPPADDING", (0, 0), (-1, 0), 16),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 1), (-1, 1), 4),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
                ("TOPPADDING", (0, 2), (-1, 2), 4),
                ("BOTTOMPADDING", (0, 2), (-1, -1), 16),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    story.append(banner)
    story.append(Spacer(1, 16))

    # Urgency (optional)
    _URGENCY_BG = colors.HexColor("#FEF2F2")
    urgency = cfg.get("urgency_text")
    if urgency:
        warn = Table([[Paragraph(f"<b>URGENT — </b>{urgency}", warn_s)]], colWidths=[W])
        warn.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), _URGENCY_BG),
                    ("BOX", (0, 0), (-1, -1), 1, PALETTE["RED"]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(warn)
        story.append(Spacer(1, 8))

    # Legend
    legend_entries = cfg.get("legend", [])
    if legend_entries:
        leg_cells = [
            Paragraph(f"<b>{e['label']}</b>", _badge(f"l{i}", _c(e["color"])))
            for i, e in enumerate(legend_entries)
        ]
        leg = Table([leg_cells], colWidths=[W / len(legend_entries)] * len(legend_entries))
        leg.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PALETTE["LGRAY"]),
                    ("ROWPADDING", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.4, PALETTE["MGRAY"]),
                ]
            )
        )
        story.append(leg)
        story.append(Spacer(1, 10))

    # About
    story.append(Paragraph("About This Plan", sec_s))
    story.append(HRFlowable(width=W, thickness=1, color=PALETTE["MGRAY"], spaceAfter=5))
    story.append(Paragraph(cfg["about_text"], body_s))
    story.append(Spacer(1, 10))

    # Plan
    story.append(Paragraph("Course + Applied Skills Details", sec_s))
    story.append(HRFlowable(width=W, thickness=1, color=PALETTE["MGRAY"], spaceAfter=6))
    for item in cfg["plan"]:
        kind = item.get("type", "course")
        if kind == "head":
            colour = _c(item["color"])
            story.append(Spacer(1, 6))
            story.append(Paragraph(item["heading"], ssec_s))
            story.append(HRFlowable(width=W, thickness=0.5, color=PALETTE["MGRAY"], spaceAfter=4))
        else:
            colour = _c(item["color"])
            story.append(
                _course_card(
                    item["num"],
                    item["source"],
                    colour,
                    item["title"],
                    item["url"],
                    item["gap"],
                    item["hrs"],
                    W,
                )
            )
            story.append(Spacer(1, 5))

    # Key Links
    story.append(PageBreak())
    story.append(Paragraph("Key Links", sec_s))
    story.append(HRFlowable(width=W, thickness=1, color=PALETTE["MGRAY"], spaceAfter=6))
    for entry in cfg.get("key_links", []):
        story.append(
            Paragraph(
                f"<b>{entry['label']}:</b> "
                f'<link href="{entry["url"]}" color="{_LINK_TEXT.hexval()}">'
                f"{entry['url']}</link>",
                body_s,
            )
        )
        story.append(Spacer(1, 3))

    # Footer
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width=W, thickness=0.5, color=PALETTE["MGRAY"], spaceAfter=5))
    story.append(Paragraph(cfg["footer"], note_s))

    doc.build(story)
    return output


# ── Config loader & CLI ─────────────────────────────────────────────────────
def load_config(path: Path) -> dict:
    """Validate the role JSON before handing it to the engine."""
    cfg = json.loads(path.read_text(encoding="utf-8"))

    for key in ("output", "banner", "about_text", "plan", "footer"):
        if key not in cfg:
            raise ValueError(f"Config missing required key: '{key}'")

    for key in ("title", "subtitle", "meta"):
        if key not in cfg["banner"]:
            raise ValueError(f"banner.{key} missing")

    if not isinstance(cfg["plan"], list) or not cfg["plan"]:
        raise ValueError("'plan' must be a non-empty list")

    for i, item in enumerate(cfg["plan"]):
        kind = item.get("type")
        if kind not in ("head", "course"):
            raise ValueError(f"plan[{i}] has invalid 'type' {kind!r}; expected 'head' or 'course'")
        if kind == "head":
            for key in ("color", "heading"):
                if key not in item:
                    raise ValueError(f"plan[{i}] (head) missing '{key}'")
        else:
            for key in ("source", "color", "num", "title", "url", "gap", "hrs"):
                if key not in item:
                    raise ValueError(f"plan[{i}] (course) missing '{key}'")

    for key in ("legend", "key_links"):
        if key in cfg and not isinstance(cfg[key], list):
            raise ValueError(f"'{key}' must be a list")

    return cfg


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="pdf-template.py",
        description="Render a role-specific Learning Plan PDF from JSON.",
    )
    parser.add_argument("role_json", help="Path to role JSON config (see roles/_example.json)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    cfg_path = Path(args.role_json)
    if not cfg_path.exists():
        print(f"ERROR: config file not found: {cfg_path}", file=sys.stderr)
        return 1

    try:
        cfg = load_config(cfg_path)
        out = _build(cfg)
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON parse error in {cfg_path}: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
