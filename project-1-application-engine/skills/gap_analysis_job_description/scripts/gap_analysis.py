#!/usr/bin/env python3
"""Generate a markdown gap analysis report from a job description."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

from project_1_application_engine.scripts._cli_common import require_path

from shared import SkillMatch, load_profile_bundle, parse_jd, rate_fit


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _recommendations(required: list[SkillMatch], nice: list[SkillMatch]) -> dict[str, list[str]]:
    """Group skills by recommended next action."""
    recs: dict[str, list[str]] = {
        "close_with_portfolio": [],
        "close_with_course": [],
        "position_as_nice_to_have": [],
    }
    for m in required + nice:
        if m.status == "gap":
            recs["close_with_portfolio"].append(m.skill)
        elif m.status == "course":
            recs["close_with_course"].append(m.skill)
        elif m.status == "portfolio" and m in nice:
            recs["position_as_nice_to_have"].append(m.skill)
    return recs


def _resume_tailoring_priorities(result, recs: dict[str, list[str]]) -> list[str]:
    """Per-application resume actions built from this JD's actual skill names.

    Uses the same recommendation buckets `_recommendations()` already
    computes — not fixed boilerplate — so two JDs with different skill
    profiles produce different priorities.
    """
    actions: list[str] = []
    matched_required = [m.skill for m in result.required if m.status == "match"]
    if matched_required:
        shown = ", ".join(matched_required[:4])
        actions.append(
            f"Lead with production evidence for {shown} — these map directly to required skills."
        )
    if recs["close_with_course"]:
        shown = ", ".join(recs["close_with_course"][:4])
        actions.append(
            f"Upgrade course-only signal to portfolio/production evidence where possible: {shown}."
        )
    if recs["close_with_portfolio"]:
        shown = ", ".join(recs["close_with_portfolio"][:4])
        actions.append(
            f"Close genuine gaps with a focused portfolio spike, or highlight adjacent "
            f"experience if any exists: {shown}."
        )
    if recs["position_as_nice_to_have"]:
        shown = ", ".join(recs["position_as_nice_to_have"][:4])
        actions.append(f"Emphasize nice-to-have strengths with portfolio evidence: {shown}.")
    if not actions:
        actions.append(
            "No specific tailoring signal found for this JD's parsed requirements — "
            "review the Summary Table above and tailor manually."
        )
    return actions


def _cover_letter_angle(company: str, result) -> str:
    """Hook + proof points + company framing, built from this JD's actual
    matched skills and evidence sources rather than a fixed template sentence."""
    matched_required = [m.skill for m in result.required if m.status == "match"]
    hook_skill = matched_required[0] if matched_required else None
    hook = (
        f"production experience with {hook_skill}"
        if hook_skill
        else "relevant production and portfolio experience"
    )
    sources = result.evidence_sources()
    points = (
        f"proof points from {', '.join(sources[:3])}"
        if sources
        else "2-3 concrete proof points from production or portfolio work"
    )
    gaps = [m.skill for m in result.required if m.status == "gap"]
    gap_clause = f"; a concise plan for closing {', '.join(gaps[:2])}" if gaps else ""
    return f"Hook: {hook}, directly aligned with {company}'s stated requirements; {points}{gap_clause}."


def _sanitize_evidence(evidence: str, max_len: int = 120) -> str:
    """Collapse whitespace and keep evidence strings readable in a markdown table cell."""
    evidence = re.sub(r"\s+", " ", evidence or "").strip()
    if len(evidence) <= max_len:
        return evidence
    truncated = evidence[:max_len].rsplit(" ", 1)[0]
    return truncated + " …"


def _format_header_meta(company: str, location: str | None, job_id: str | None) -> str:
    """ "[Company] — [Location] · [Job ID]", omitting whichever parts are absent."""
    extras = [p for p in (location, job_id) if p]
    return f"{company} — {' · '.join(extras)}" if extras else company


def _render_report(
    title: str,
    company: str,
    result,
    location: str | None = None,
    job_id: str | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"# Gap Analysis: {title}")
    lines.append(
        f"**{_format_header_meta(company, location, job_id)}** · {date.today().strftime('%B %Y')}"
    )
    lines.append("")
    lines.append(f"## Overall Fit: {result.rating}")
    lines.append(f"{result.rationale}")
    lines.append("")
    lines.append("## Summary Table")
    lines.append("| Requirement | Status | Evidence |")
    lines.append("|---|---|---|")
    for m in result.required:
        status = {
            "match": "✅ Match",
            "portfolio": "🟡 Portfolio",
            "course": "🟡 Coursework",
            "gap": "🔴 Gap",
        }[m.status]
        evidence = _sanitize_evidence(m.evidence)
        lines.append(f"| {m.skill} | {status} | {evidence} |")
    if result.nice_to_have:
        lines.append("")
        lines.append("### Nice-to-Have Skills")
        lines.append("| Skill | Status | Evidence |")
        lines.append("|---|---|---|")
        for m in result.nice_to_have:
            status = {
                "match": "✅ Match",
                "portfolio": "🟡 Portfolio",
                "course": "🟡 Coursework",
                "gap": "🔴 Gap",
            }[m.status]
            evidence = _sanitize_evidence(m.evidence)
            lines.append(f"| {m.skill} | {status} | {evidence} |")
    lines.append("")
    lines.append("## ✅ Strong Matches")
    for m in result.required + result.nice_to_have:
        if m.status == "match":
            lines.append(f"- **{m.skill}** — {m.evidence}")
    if not any(m.status == "match" for m in result.required + result.nice_to_have):
        lines.append("- None identified")
    lines.append("")
    lines.append("## 🟡 Framing Gaps")
    for m in result.required:
        if m.status in ("portfolio", "course"):
            lines.append(f"- **{m.skill}** — {m.evidence}")
    if not any(m.status in ("portfolio", "course") for m in result.required):
        lines.append("- None identified")
    lines.append("")
    lines.append("## 🔴 Genuine Gaps")
    for m in result.required:
        if m.status == "gap":
            lines.append(
                f"- **{m.skill}** — no evidence; consider focused learning or a portfolio spike"
            )
    if not any(m.status == "gap" for m in result.required):
        lines.append("- None identified")
    lines.append("")

    recs = _recommendations(result.required, result.nice_to_have)
    lines.append("## Recommendations")
    if recs["close_with_portfolio"]:
        lines.append("### Close with portfolio evidence")
        lines.append(
            "These required skills are genuine gaps. Pick 1–2 and build or extend a portfolio project that demonstrates them:"
        )
        for skill in recs["close_with_portfolio"]:
            lines.append(f"- {skill}")
        lines.append("")
    if recs["close_with_course"]:
        lines.append("### Close with coursework or lab")
        lines.append(
            "These skills are course-only. Add a small hands-on project or cert lab to upgrade them to portfolio/production evidence:"
        )
        for skill in recs["close_with_course"]:
            lines.append(f"- {skill}")
        lines.append("")
    if recs["position_as_nice_to_have"]:
        lines.append("### Emphasize in application narrative")
        lines.append(
            "These nice-to-have skills have portfolio evidence. Mention them explicitly in the cover letter:"
        )
        for skill in recs["position_as_nice_to_have"]:
            lines.append(f"- {skill}")
        lines.append("")
    lines.append("## How to Frame the Application")
    lines.append("### Resume tailoring priorities")
    for i, action in enumerate(_resume_tailoring_priorities(result, recs), start=1):
        lines.append(f"{i}. {action}")
    lines.append("")
    lines.append("### Cover letter angle")
    lines.append(_cover_letter_angle(company, result))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gap-analysis", description="Generate a JD gap analysis report"
    )
    parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    parser.add_argument(
        "--out",
        type=Path,
        help="Output markdown file (default: outputs/<Company>_<Role>_GapAnalysis.md)",
    )
    args = parser.parse_args(argv)

    try:
        require_path(args.jd, "JD file")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    bundle = load_profile_bundle(ROOT)
    jd_text = args.jd.read_text(encoding="utf-8")
    parsed = parse_jd(jd_text)
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)

    out_file = (
        args.out
        or ROOT / "outputs" / f"{_slugify(parsed.company)}_{_slugify(parsed.title)}_GapAnalysis.md"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        out_file.write_text(
            _render_report(parsed.title, parsed.company, result, parsed.location, parsed.job_id),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"ERROR: failed to write {out_file}: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
