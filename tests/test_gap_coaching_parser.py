"""Tests for shared.markdown_sources.parse_gap_coaching and
shared.fit_engine.find_gap_coaching_entry."""

from __future__ import annotations

from pathlib import Path

from shared.fit_engine import find_gap_coaching_entry
from shared.markdown_sources import parse_gap_coaching

REAL_GAP_COACHING = (
    Path(__file__).resolve().parents[1]
    / "project-1-application-engine"
    / "reference"
    / "gap-coaching.md"
).read_text(encoding="utf-8")

SAMPLE_GAP_COACHING = """\
# Gap Coaching Reference — Test

## Bulleted Skill

**Status:** 🟡 Course only — some coursework, no production use

**What to say:**
"This is the framing to use for bulleted skill."

**What not to say:**
- Overstated claim one
- Overstated claim two

**Best STAR bridge:** Story 9 (Example)

**Honest floor:** Coursework only.

---

## Inline Skill (as primary requirement)

**Status:** 🔴 Genuine Gap — no exposure at all

**What to say:**
"This is the framing for the inline-what-not-to-say skill."

**What not to say:** Nothing — lead with this confidently.

**Best STAR bridge:** Story 3 (Example)

**Honest floor:** Zero exposure.

---

## Notes on Using This File

- Always embed the framing.
"""


def test_parses_all_headings_excluding_notes_section() -> None:
    entries = parse_gap_coaching(SAMPLE_GAP_COACHING)
    headings = [e.heading for e in entries]
    assert headings == ["Bulleted Skill", "Inline Skill (as primary requirement)"]


def test_bulleted_what_not_to_say_parsed_as_list() -> None:
    entries = parse_gap_coaching(SAMPLE_GAP_COACHING)
    entry = entries[0]
    assert entry.what_not_to_say == ["Overstated claim one", "Overstated claim two"]


def test_inline_what_not_to_say_parsed_as_single_item_list() -> None:
    entries = parse_gap_coaching(SAMPLE_GAP_COACHING)
    entry = entries[1]
    assert entry.what_not_to_say == ["Nothing — lead with this confidently."]


def test_status_what_to_say_best_star_bridge_honest_floor_all_parsed() -> None:
    entries = parse_gap_coaching(SAMPLE_GAP_COACHING)
    entry = entries[0]
    assert entry.status == "🟡 Course only — some coursework, no production use"
    assert entry.what_to_say == '"This is the framing to use for bulleted skill."'
    assert entry.best_star_bridge == "Story 9 (Example)"
    assert entry.honest_floor == "Coursework only."


def test_returns_empty_for_blank_input() -> None:
    assert parse_gap_coaching("# Just a header\n\nno entries here\n") == []


class TestRealGapCoachingFile:
    def test_all_seven_entries_parse(self) -> None:
        entries = parse_gap_coaching(REAL_GAP_COACHING)
        headings = [e.heading for e in entries]
        assert headings == [
            "Python (Production Experience)",
            "Oracle Databases",
            "Cognos",
            "Power BI (as primary requirement)",
            "CI/CD Pipelines (as primary must-have)",
            "Unit Testing / TDD (if flagged as must-have)",
            "Cloud / Azure (if flagged as must-have beyond fundamentals)",
        ]

    def test_every_entry_has_all_fields_populated(self) -> None:
        entries = parse_gap_coaching(REAL_GAP_COACHING)
        for entry in entries:
            assert entry.status
            assert entry.what_to_say
            assert entry.what_not_to_say
            assert entry.best_star_bridge
            assert entry.honest_floor


class TestFindGapCoachingEntry:
    def test_finds_entry_for_short_skill_against_longer_heading(self) -> None:
        entries = parse_gap_coaching(REAL_GAP_COACHING)
        entry = find_gap_coaching_entry("oracle", entries)
        assert entry is not None
        assert entry.heading == "Oracle Databases"

    def test_finds_entry_for_longer_skill_against_short_heading(self) -> None:
        entries = parse_gap_coaching(REAL_GAP_COACHING)
        entry = find_gap_coaching_entry(
            "strong azure fundamentals (app service, azure functions, cosmos db)", entries
        )
        assert entry is not None
        assert entry.heading == "Cloud / Azure (if flagged as must-have beyond fundamentals)"

    def test_parenthetical_qualifier_does_not_block_matching(self) -> None:
        entries = parse_gap_coaching(REAL_GAP_COACHING)
        entry = find_gap_coaching_entry("power bi", entries)
        assert entry is not None
        assert entry.heading == "Power BI (as primary requirement)"

    def test_deliberate_no_match_returns_none_not_fabricated(self) -> None:
        entries = parse_gap_coaching(REAL_GAP_COACHING)
        entry = find_gap_coaching_entry("kubernetes", entries)
        assert entry is None

    def test_no_match_against_empty_entries_list(self) -> None:
        assert find_gap_coaching_entry("python", []) is None
