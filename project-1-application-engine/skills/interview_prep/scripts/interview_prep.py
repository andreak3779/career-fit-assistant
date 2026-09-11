#!/usr/bin/env python3
"""Generate a tailored interview-prep DOCX from a job description and profile bundle."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[4]

from docx import Document
from docx.shared import Pt
from project_1_application_engine.scripts._cli_common import require_path

from shared import (
    DEFAULT_SIGNATURE_NAME,
    FitResult,
    load_profile_bundle,
    parse_jd,
    rate_fit,
    slugify,
)
from shared.docx_advanced import banner, callout_box, qa_card, star_card, two_column_table
from shared.docx_layout import add_paragraph, section_heading
from shared.fit_engine import find_gap_coaching_entry
from shared.markdown_sources import parse_gap_coaching
from shared.models import GapCoachingEntry
from shared.provenance import write_sidecar
from shared.star_bank_writer import diff_star_bank_update, render_star_bank_update

Stage = Literal["phone_screen", "technical_screen", "final_round"]

_STAGE_LABELS: dict[Stage, str] = {
    "phone_screen": "Phone Screen",
    "technical_screen": "Technical Screen",
    "final_round": "Final Round",
}

# Phone Screen gets a lean 2 stories; the other two stages get the full
# ranked pool (up to 5), per the SKILL.md's stage table.
_STAGE_STAR_COUNT: dict[Stage, int] = {
    "phone_screen": 2,
    "technical_screen": 5,
    "final_round": 5,
}

_STATUS_LABELS: dict[str, str] = {
    "match": "Strong Match",
    "portfolio": "Learning / Portfolio",
    "course": "Learning / Portfolio",
    "gap": "Genuine Gap",
}


def _select_star_stories(
    bundle: Any, required: list[str], nice_to_have: list[str], *, limit: int = 5
) -> list[dict[str, Any]]:
    """Return up to ``limit`` best-fitting STAR stories, ranked by JD-tag overlap."""
    pool = [s.lower() for s in required + nice_to_have]
    scored: list[tuple[int, Any]] = []
    for story in bundle.resume.star_stories:
        text = f"{story.title} {' '.join(story.jd_tags)} {story.situation} {story.action} {story.result}".lower()
        score = sum(1 for term in pool if term in text)
        if score:
            scored.append((score, story))
    scored.sort(key=lambda t: t[0], reverse=True)
    out: list[dict[str, Any]] = []
    for _, story in scored[:limit]:
        out.append(
            {
                "title": story.title,
                "tags": list(story.jd_tags),
                "situation": story.situation,
                "task": story.task,
                "action": story.action,
                "result": story.result,
                "adapt_when": list(getattr(story, "adapt_when", [])),
            }
        )
    return out


_LEADING_DESCRIPTORS_RE = re.compile(
    r"(?i)^\s*(?:strong|solid|good|expertise|experience\s+with|hands-on\s+experience\s+with|deep\s+experience\s+with)\s+"
)
_PARENS_NON_GREEDY_RE = re.compile(r"\([^)]*\)")
_SPLIT_LIST_RE = re.compile(r",|\s+and\s+|/")


def _atomic_skills(skills: list[str]) -> list[str]:
    """Split compound JD skill lines into concrete tokens (case-folded, deduped).

    Handles ``"Strong experience with Azure DevOps, GitHub Actions and Docker"``
    → ``["azure devops", "github actions", "docker"]`` (preserves first-seen
    casing while dropping near-duplicates like ``"Azure"`` / ``"azure"``).
    """
    seen: set[str] = set()
    atoms: list[str] = []
    for skill in skills:
        cleaned = _LEADING_DESCRIPTORS_RE.sub("", skill.strip())
        cleaned = _PARENS_NON_GREEDY_RE.sub("", cleaned).strip(" ,./:;")
        if "," in cleaned or "/" in cleaned or re.search(r"\s+and\s+", cleaned, re.IGNORECASE):
            parts = [p.strip(" ,./:;") for p in _SPLIT_LIST_RE.split(cleaned)]
            for p in parts:
                _maybe_add(atoms, p, seen)
        else:
            _maybe_add(atoms, cleaned, seen)
    return atoms


def _maybe_add(atoms: list[str], candidate: str, seen: set[str]) -> None:
    key = candidate.lower()
    if len(key) > 1 and key not in seen:
        seen.add(key)
        atoms.append(candidate)


def _evidence_label(evidence: str) -> str:
    """Return the evidence source label (company/project) before the colon."""
    raw = (evidence or "").strip()
    if ":" in raw:
        return raw.rsplit(":", 1)[0].strip()
    return ""


def _strip_quotes(text: str) -> str:
    """Strip a matching pair of wrapping double quotes, if present."""
    stripped = text.strip()
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        return stripped[1:-1]
    return stripped


def _attach_gap_coaching(card: dict[str, str], entry: GapCoachingEntry) -> None:
    """Layer a gap-coaching entry's tip and gap-note onto an existing Q&A card.

    Never touches the question or answer — the caller sets the answer using
    the entry's own "what to say" framing when one exists, since that's
    hand-authored, verified content and a stronger grounding than the
    generic evidence stub.
    """
    if entry.what_not_to_say:
        card["tip"] = "Avoid: " + " · ".join(entry.what_not_to_say)
    notes = [n for n in (entry.honest_floor, entry.best_star_bridge) if n]
    if notes:
        card["gap_note"] = " · ".join(notes)


def _qa_cards_and_reminders(
    result: FitResult, gap_entries: list[GapCoachingEntry]
) -> tuple[list[dict[str, str]], list[str]]:
    """Build Q&A cards for required skills, plus honesty reminders for the rest.

    A skill with a matching gap-coaching entry (any status — coaching notes
    cover both framing gaps on grounded skills, like TDD, and genuine gaps)
    gets that entry's exact "what to say" framing as the answer, its
    "what not to say" list as the Tip line, and its honest floor / best
    STAR bridge as a gap-note callout — never fabricated, always the
    reference file's own words. A grounded skill with no coaching entry
    falls back to the evidence trace as its answer. An ungrounded skill
    with no coaching entry gets a plain honesty reminder instead of a card,
    since there's no honest content to put in an answer.

    This is the one Q&A category this script generates itself; the other
    four LLM-authored categories (resume walkthrough, engineering judgment,
    collaboration, situational) merge in later via ``--qa-cards`` (Phase 5)
    — the script never fabricates prose for them.
    """
    cards: list[dict[str, str]] = []
    reminders: list[str] = []

    for m in result.grounded_required[:6]:
        entry = find_gap_coaching_entry(m.skill, gap_entries)
        label = _evidence_label(m.evidence)
        if m.status == "match" and label:
            question = f"Walk me through how you used {m.skill} at {label} in a production system."
        elif m.status == "portfolio" and label:
            question = f"Tell me about {m.skill} on {label} — what problem did it solve?"
        else:
            question = f"Tell me about a time you used {m.skill} in a real project."
        card = {
            "question": question,
            "answer": _strip_quotes(entry.what_to_say)
            if entry
            else f"Evidence on file: {m.evidence}",
        }
        if entry:
            _attach_gap_coaching(card, entry)
        cards.append(card)

    for m in result.ungrounded_required[:2]:
        entry = find_gap_coaching_entry(m.skill, gap_entries)
        if entry:
            card = {
                "question": f"How would you address {m.skill} if it comes up?",
                "answer": _strip_quotes(entry.what_to_say),
            }
            _attach_gap_coaching(card, entry)
            cards.append(card)
        else:
            reminders.append(
                f"If {m.skill} comes up, answer honestly about your current level — "
                "no production or portfolio evidence for it in the bundle."
            )

    return cards, reminders


def _experience_match_rows(result: FitResult) -> list[tuple[str, str]]:
    """Build (skill, status + evidence) rows for the Experience Match table."""
    rows: list[tuple[str, str]] = []
    for m in result.required + result.nice_to_have:
        label = _STATUS_LABELS.get(m.status, m.status)
        evidence = (
            m.evidence if m.status != "gap" else "Not present in resume, portfolio, or coursework"
        )
        rows.append((m.skill, f"{label} — {evidence}"))
    return rows


def _blank(text: str | None) -> bool:
    """True when ``text`` is ``None`` or contains only whitespace."""
    return text is None or not text.strip()


def _validate_qa_cards(qa_cards: list[dict[str, str]]) -> None:
    """Fail closed if any supplied Q&A card is missing its required fields.

    ``qa_cards`` is LLM-authored content the script never generates itself
    (see the plan's Scope Boundary) — a malformed entry must raise, not be
    silently skipped or padded with placeholder text.
    """
    for idx, card in enumerate(qa_cards, start=1):
        for key in ("question", "answer"):
            if not card.get(key):
                raise ValueError(f"qa_cards entry {idx} is missing required field {key!r}")


def generate_interview_prep(
    jd_path: Path,
    *,
    bundle: Any | None = None,
    out_path: Path | None = None,
    stage: Stage = "technical_screen",
    root: Path = ROOT,
    gap_coaching_path: Path | None = None,
    write_star_bank: bool = False,
    star_bank_path: Path | None = None,
    company_research: str | None = None,
    recruiter_briefing: str | None = None,
    qa_cards: list[dict[str, str]] | None = None,
    salary_section: str | None = None,
) -> tuple[Path, Path, FitResult]:
    """Build and write the interview-prep DOCX plus provenance sidecar.

    ``stage`` gates document scope per the SKILL.md's stage table: Phone
    Screen gets 2 STAR stories, Technical Screen and Final Round get the
    full ranked pool. Company research, recruiter briefing, the LLM-authored
    Q&A categories, and the salary section layer in later (see the plan's
    Phase 5) — this deterministic core covers only what the bundle and fit
    engine can verify without inventing content.

    ``gap_coaching_path`` defaults to ``reference/gap-coaching.md`` under
    ``root``; a test-only override (mirroring ``--bundle``) keeps tests from
    depending on the real reference file. Missing the file entirely is not
    an error — coaching notes are optional enrichment, not required input.

    ``write_star_bank`` (opt-in, default ``False``, per the plan's Phase 4
    write-back safety design) updates ``last_used``/``used_for`` on every
    STAR story actually selected in this run — the same list rendered into
    the STAR Stories section, respecting the stage-based ``limit`` — via
    ``shared.star_bank_writer``. ``star_bank_path`` defaults to
    ``reference/star-bank.md`` under ``root``; a test-only override (mirroring
    ``--bundle``/``gap_coaching_path``) keeps tests from touching the real
    reference file. A story that can't be unambiguously located raises
    ``ValueError`` before anything is written — fail closed, never guess.

    ``company_research``, ``recruiter_briefing``, ``qa_cards``, and
    ``salary_section`` are the plan's Phase 5 hybrid LLM-content inputs —
    real prose/structured content supplied from outside the script (web
    search, a pasted briefing, LLM-authored Q&A, salary research), never
    fabricated here. Each is optional and its section is omitted entirely
    (no placeholder text) when absent. ``qa_cards`` entries missing
    ``"question"`` or ``"answer"`` raise ``ValueError`` before anything is
    rendered. ``salary_section`` only renders when ``stage ==
    "final_round"``; supplying it at any other stage prints a warning and
    skips the section instead of raising — a deliberate "warn and ignore"
    exception to this function's otherwise fail-closed conventions.
    """
    if qa_cards:
        _validate_qa_cards(qa_cards)

    bundle = bundle or load_profile_bundle(root)
    jd_text = jd_path.read_text(encoding="utf-8")
    parsed = parse_jd(jd_text)
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)

    if gap_coaching_path is None:
        gap_coaching_path = root / "project-1-application-engine" / "reference" / "gap-coaching.md"
    gap_entries = (
        parse_gap_coaching(gap_coaching_path.read_text(encoding="utf-8"))
        if gap_coaching_path.exists()
        else []
    )

    if out_path is None:
        slug = slugify(parsed.company)
        out_path = root / "outputs" / f"{slug}_{slugify(parsed.title)}_InterviewPrep.docx"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    stage_label = _STAGE_LABELS[stage]
    today = date.today().strftime("%B %d, %Y")

    doc = Document()
    banner(
        doc,
        title=parsed.title,
        subtitle_lines=[
            parsed.company,
            bundle.contact.name or DEFAULT_SIGNATURE_NAME,
            f"{stage_label} · {today}",
        ],
    )

    if not _blank(recruiter_briefing):
        callout_box(doc, "Recruiter Briefing", (recruiter_briefing or "").strip())

    if not _blank(company_research):
        section_heading(doc, "Company Research")
        add_paragraph(doc, (company_research or "").strip(), space_after=Pt(6))

    section_heading(doc, "Experience Match")
    two_column_table(doc, ["They Need", "Your Evidence"], _experience_match_rows(result))

    section_heading(doc, "Anticipated Questions")
    cards, reminders = _qa_cards_and_reminders(result, gap_entries)
    for card in cards:
        qa_card(
            doc,
            card["question"],
            card["answer"],
            tip=card.get("tip"),
            gap_note=card.get("gap_note"),
        )
    for supplied in qa_cards or []:
        qa_card(doc, supplied["question"], supplied["answer"], tip=supplied.get("tip"))
    for reminder in reminders:
        add_paragraph(
            doc, reminder, italic=True, size=Pt(9.5), space_before=Pt(4), space_after=Pt(4)
        )

    section_heading(doc, "STAR Stories")
    stories = _select_star_stories(
        bundle, parsed.required, parsed.nice_to_have, limit=_STAGE_STAR_COUNT[stage]
    )
    if stories:
        for story in stories:
            star_card(
                doc,
                story["title"],
                story["tags"],
                story["situation"],
                story["task"],
                story["action"],
                story["result"],
                adapt_when=story["adapt_when"],
            )
    else:
        add_paragraph(
            doc, "No tagged STAR stories found. Add some to the profile bundle.", italic=True
        )

    if not _blank(salary_section):
        if stage == "final_round":
            section_heading(doc, "Salary / Negotiation")
            add_paragraph(doc, (salary_section or "").strip(), space_after=Pt(6))
        else:
            print("Salary section supplied but stage is not final_round — omitted.")

    section_heading(doc, "Fit Rating")
    add_paragraph(doc, f"{result.rating} — {result.rationale}", space_after=Pt(6))

    add_paragraph(
        doc,
        f"Generated {today} · {bundle.contact.name or DEFAULT_SIGNATURE_NAME} · {parsed.title} · {stage_label}",
        italic=True,
        size=Pt(9),
        space_before=Pt(16),
    )

    doc.save(str(out_path))

    if write_star_bank and stories:
        if star_bank_path is None:
            star_bank_path = root / "project-1-application-engine" / "reference" / "star-bank.md"
        original_text = star_bank_path.read_text(encoding="utf-8")
        used_for_entry = f"{parsed.company} — {parsed.title}"
        last_used_value = date.today().strftime("%B %Y")
        updated_text = original_text
        for story in stories:
            updated_text = render_star_bank_update(
                updated_text,
                story_title=story["title"],
                last_used=last_used_value,
                used_for_append=used_for_entry,
            )
        print(diff_star_bank_update(original_text, updated_text))
        star_bank_path.write_text(updated_text, encoding="utf-8")

    low_confidence = result.rating in ("Pass", "Stretch") and bool(result.ungrounded_required)
    sidecar = write_sidecar(
        out_path,
        script="interview_prep.py",
        bundle=bundle,
        inputs=[str(jd_path)],
        fit_rating=result.rating,
        evidence_sources=result.evidence_sources(),
        warnings=["low evidence — manually review before using"] if low_confidence else [],
    )
    return out_path, sidecar, result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="interview-prep", description="Generate an interview prep DOCX for a job description"
    )
    parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    parser.add_argument(
        "--stage",
        choices=["phone_screen", "technical_screen", "final_round"],
        default="technical_screen",
        help="Interview stage — gates document scope (default: technical_screen)",
    )
    parser.add_argument("--out", type=Path, help="Output DOCX file path")
    parser.add_argument("--bundle", type=Path, help="Path to profile-bundle.json")
    parser.add_argument(
        "--update-star-bank",
        action="store_true",
        help="Write updated last_used/used_for metadata back to star-bank.md "
        "for every STAR story selected in this run",
    )
    parser.add_argument(
        "--star-bank-path",
        type=Path,
        help="Override path to star-bank.md (test-only; defaults to the real reference file)",
    )
    parser.add_argument(
        "--company-research",
        type=Path,
        help="Path to a text file of company-research prose (e.g. web_search findings — "
        "never fabricated by this script)",
    )
    parser.add_argument(
        "--recruiter-briefing",
        type=Path,
        help="Path to a text file with a pasted recruiter briefing",
    )
    parser.add_argument(
        "--qa-cards",
        type=Path,
        help="Path to a JSON file of LLM-authored Q&A cards "
        '(list of {"question", "answer", optional "tip"/"category"})',
    )
    parser.add_argument(
        "--salary-section",
        type=Path,
        help="Path to a text file of salary/negotiation prose (rendered only when "
        "--stage final_round)",
    )
    args = parser.parse_args(argv)

    try:
        require_path(args.jd, "JD file")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    company_research = None
    recruiter_briefing = None
    qa_cards = None
    salary_section = None
    try:
        if args.company_research is not None:
            require_path(args.company_research, "Company research file")
            company_research = args.company_research.read_text(encoding="utf-8")
        if args.recruiter_briefing is not None:
            require_path(args.recruiter_briefing, "Recruiter briefing file")
            recruiter_briefing = args.recruiter_briefing.read_text(encoding="utf-8")
        if args.qa_cards is not None:
            require_path(args.qa_cards, "Q&A cards file")
            qa_cards = json.loads(args.qa_cards.read_text(encoding="utf-8"))
        if args.salary_section is not None:
            require_path(args.salary_section, "Salary section file")
            salary_section = args.salary_section.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in --qa-cards file: {exc}", file=sys.stderr)
        return 1

    try:
        out, sidecar, _ = generate_interview_prep(
            args.jd,
            bundle=load_profile_bundle(args.bundle or ROOT),
            out_path=args.out,
            stage=args.stage,
            write_star_bank=args.update_star_bank,
            star_bank_path=args.star_bank_path,
            company_research=company_research,
            recruiter_briefing=recruiter_briefing,
            qa_cards=qa_cards,
            salary_section=salary_section,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {out}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
