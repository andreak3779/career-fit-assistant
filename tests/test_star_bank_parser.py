"""Tests for shared.markdown_sources.parse_star_bank."""

from __future__ import annotations

from shared.markdown_sources import parse_star_bank

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

## Story 2 — Multi-Paragraph Story

**Use for:** Stakeholder communication

**JD tags:** `collaboration` `agile`

**Situation:**
Only situation.

**Task:**
Only task.

**Action:**
Only action.

**Result:**
Only result.
"""


def test_parses_multiple_stories() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    assert len(stories) == 2
    assert stories[0]["title"] == "Test Story"
    assert stories[1]["title"] == "Multi-Paragraph Story"


def test_jd_tags_extracted() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    assert stories[0]["jd_tags"] == ["sql", "python", "legacy-systems"]
    assert stories[1]["jd_tags"] == ["collaboration", "agile"]


def test_star_fields_populated() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    story = stories[0]
    assert story["situation"] == "Single paragraph situation."
    assert story["task"] == "Single paragraph task."
    assert "First paragraph" in story["action"]
    assert "Second paragraph" in story["action"]
    assert story["result"] == "Result paragraph."


def test_paragraph_breaks_preserved() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    # The action has two paragraphs separated by a blank line in source.
    assert "\n\n" in stories[0]["action"]
    parts = stories[0]["action"].split("\n\n")
    assert len(parts) == 2
    assert parts[0].startswith("First paragraph")
    assert parts[1].startswith("Second paragraph")


def test_metadata_extracted() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    story = stories[0]
    assert story["last_used"] == "April 2026"
    assert story["used_for"] == ["Test Co"]
    assert "Problem-solving" in story["use_for"][0]


def test_returns_empty_for_blank_input() -> None:
    assert parse_star_bank("# Just a header\n\nno stories here\n") == []


def test_adapt_when_bullets_extracted() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    assert stories[0]["adapt_when"] == [
        "Role emphasizes Python — mention the analytical approach",
        "Role emphasizes ownership — lead with full ownership framing",
    ]


def test_adapt_when_defaults_to_empty_list_when_absent() -> None:
    stories = parse_star_bank(SAMPLE_STAR_BANK)
    assert stories[1]["adapt_when"] == []
