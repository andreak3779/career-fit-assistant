"""Tests for shared.star_bank_writer."""

from __future__ import annotations

import pytest

from shared.markdown_sources import parse_star_bank
from shared.star_bank_writer import diff_star_bank_update, render_star_bank_update

SAMPLE_STAR_BANK = """\
# STAR Story Bank

## Story 1 — Test Story

**Use for:** Problem-solving · Ownership

**JD tags:** `sql` `python` `legacy-systems`

**last_used:** April 2026
**used_for:** Test Co

**Situation:**
Single paragraph situation.

**Task:**
Single paragraph task.

**Action:**
First paragraph of action.

Second paragraph of action with more detail.

**Result:**
Result paragraph.

**Adapt when:**
- Role emphasizes Python — mention the analytical approach
- Role emphasizes ownership — lead with full ownership framing

---

## Story 2 — Multi-Paragraph Story

**Use for:** Stakeholder communication

**JD tags:** `collaboration` `agile`

**last_used:** —
**used_for:** —

**Situation:**
Only situation.

**Task:**
Only task.

**Action:**
Only action.

**Result:**
Only result.

---

## Story Selection Guide

| Question type | First choice |
|---|---|
| Setback | Story 1 |

## Adding New Stories

Template goes here.
"""


def test_update_existing_story_by_number() -> None:
    updated = render_star_bank_update(SAMPLE_STAR_BANK, story_number=1, last_used="August 2026")
    stories = parse_star_bank(updated)
    assert stories[0]["last_used"] == "August 2026"
    assert stories[1]["last_used"] == "—"


def test_update_existing_story_by_title() -> None:
    updated = render_star_bank_update(
        SAMPLE_STAR_BANK, story_title="Multi-Paragraph Story", last_used="August 2026"
    )
    stories = parse_star_bank(updated)
    assert stories[0]["last_used"] == "April 2026"
    assert stories[1]["last_used"] == "August 2026"


def test_used_for_append_replaces_unused_placeholder() -> None:
    updated = render_star_bank_update(
        SAMPLE_STAR_BANK, story_number=2, used_for_append="Acme — Senior Dev"
    )
    stories = parse_star_bank(updated)
    assert stories[1]["used_for"] == ["Acme — Senior Dev"]


def test_used_for_append_adds_to_existing_list() -> None:
    updated = render_star_bank_update(
        SAMPLE_STAR_BANK, story_number=1, used_for_append="Acme — Senior Dev"
    )
    stories = parse_star_bank(updated)
    assert stories[0]["used_for"] == ["Test Co", "Acme — Senior Dev"]


def test_used_for_append_twice_does_not_duplicate() -> None:
    once = render_star_bank_update(
        SAMPLE_STAR_BANK, story_number=1, used_for_append="Acme — Senior Dev"
    )
    twice = render_star_bank_update(once, story_number=1, used_for_append="Acme — Senior Dev")
    stories = parse_star_bank(twice)
    assert stories[0]["used_for"] == ["Test Co", "Acme — Senior Dev"]


def test_not_found_by_number_raises_value_error() -> None:
    with pytest.raises(ValueError, match="No STAR story found"):
        render_star_bank_update(SAMPLE_STAR_BANK, story_number=99, last_used="August 2026")


def test_not_found_by_title_raises_value_error() -> None:
    with pytest.raises(ValueError, match="No STAR story found"):
        render_star_bank_update(
            SAMPLE_STAR_BANK, story_title="Nonexistent Story", last_used="August 2026"
        )


def test_neither_target_nor_new_story_raises_value_error() -> None:
    with pytest.raises(ValueError):
        render_star_bank_update(SAMPLE_STAR_BANK)


def test_append_new_story_round_trips_through_parse_star_bank() -> None:
    new_story = {
        "title": "Brand New Story (Some Employer)",
        "jd_tags": ["docker", "ci-cd"],
        "use_for": ["Automation", "Ownership"],
        "situation": "The situation.",
        "task": "The task.",
        "action": "The action.",
        "result": "The result.",
        "last_used": "August 2026",
        "used_for": ["Acme — Senior Dev"],
        "adapt_when": ["Role emphasizes Docker — lead with the container work"],
    }
    updated = render_star_bank_update(SAMPLE_STAR_BANK, new_story=new_story)
    stories = parse_star_bank(updated)

    assert len(stories) == 3
    new = stories[2]
    assert new["title"] == "Brand New Story (Some Employer)"
    assert new["jd_tags"] == ["docker", "ci-cd"]
    assert new["use_for"] == ["Automation", "Ownership"]
    assert new["situation"] == "The situation."
    assert new["task"] == "The task."
    assert new["action"] == "The action."
    assert new["result"] == "The result."
    assert new["last_used"] == "August 2026"
    assert new["used_for"] == ["Acme — Senior Dev"]
    assert new["adapt_when"] == ["Role emphasizes Docker — lead with the container work"]


def test_append_new_story_inserted_before_trailing_section_not_at_eof() -> None:
    new_story = {
        "title": "Brand New Story",
        "jd_tags": [],
        "situation": "S",
        "task": "T",
        "action": "A",
        "result": "R",
    }
    updated = render_star_bank_update(SAMPLE_STAR_BANK, new_story=new_story)

    new_story_pos = updated.index("## Story 3 — Brand New Story")
    guide_pos = updated.index("## Story Selection Guide")
    adding_pos = updated.index("## Adding New Stories")
    assert new_story_pos < guide_pos < adding_pos


def test_append_new_story_uses_next_sequential_number() -> None:
    new_story = {
        "title": "Another Story",
        "jd_tags": [],
        "situation": "S",
        "task": "T",
        "action": "A",
        "result": "R",
    }
    updated = render_star_bank_update(SAMPLE_STAR_BANK, new_story=new_story)
    assert "## Story 3 — Another Story" in updated


def test_diff_star_bank_update_shows_changed_lines() -> None:
    updated = render_star_bank_update(SAMPLE_STAR_BANK, story_number=1, last_used="August 2026")
    diff = diff_star_bank_update(SAMPLE_STAR_BANK, updated)
    assert "star-bank.md (before)" in diff
    assert "star-bank.md (after)" in diff
    assert "-**last_used:** April 2026" in diff
    assert "+**last_used:** August 2026" in diff
