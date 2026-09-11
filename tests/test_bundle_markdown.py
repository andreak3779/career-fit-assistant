"""Unit tests for shared/bundle_markdown.py — the generic presence-bundle.md
and SKILL.md prose-template parsing helpers shared by every Project 3
profile-update generator (LinkedIn, GitHub, Jobgether, Indeed/ZipRecruiter,
Pluralsight)."""

from __future__ import annotations

from shared.bundle_markdown import (
    bundle_version_and_generated,
    clean_skill_term,
    derive_skill_terms,
    fenced_blocks,
    load_fragments_and_skills,
    parse_fragments,
    parse_pipe_table,
    section_text,
    split_top_level_commas,
    subsections,
    substitute_fragments,
)

SAMPLE_BUNDLE = """\
<!-- GENERATED FILE -->
# Presence Bundle — Test
bundle_version: 42
generated: 2026-01-15

---
## Copy Fragments
```
cert_status_short: "AZ-900 Certified"
github_copilot_course_count: "7"
```

## Technical Skills (flat list, ATS-formatted)
### Backend
C#, ASP.NET Core, Entity Framework Core (course-level), SOLID principles and design patterns

### Frontend
Angular, TypeScript, RxJS

## Cert Status + Badge URLs
| Cert | Status |
|---|---|
| AZ-900 | **Certified April 18, 2026** |
| AI-200 | **Active target** |
"""


def test_bundle_version_and_generated() -> None:
    version, generated = bundle_version_and_generated(SAMPLE_BUNDLE)
    assert version == 42
    assert generated == "2026-01-15"


def test_bundle_version_and_generated_missing() -> None:
    version, generated = bundle_version_and_generated("no metadata here")
    assert version is None
    assert generated is None


def test_section_text_extracts_named_section() -> None:
    block = section_text(SAMPLE_BUNDLE, "Cert Status + Badge URLs")
    assert block is not None
    assert "AZ-900" in block
    assert "Copy Fragments" not in block


def test_section_text_missing_returns_none() -> None:
    assert section_text(SAMPLE_BUNDLE, "Nonexistent Section") is None


def test_subsections_splits_on_h3() -> None:
    block = section_text(SAMPLE_BUNDLE, "Technical Skills (flat list, ATS-formatted)")
    assert block is not None
    categories = subsections(block)
    assert set(categories) == {"Backend", "Frontend"}
    assert "C#" in categories["Backend"]
    assert "Angular" in categories["Frontend"]


def test_fenced_blocks_extracts_code_block_content() -> None:
    block = section_text(SAMPLE_BUNDLE, "Copy Fragments")
    assert block is not None
    blocks = fenced_blocks(block)
    assert len(blocks) == 1
    assert 'cert_status_short: "AZ-900 Certified"' in blocks[0]


def test_parse_fragments() -> None:
    block = section_text(SAMPLE_BUNDLE, "Copy Fragments")
    assert block is not None
    fragments = parse_fragments(fenced_blocks(block)[0])
    assert fragments == {
        "cert_status_short": "AZ-900 Certified",
        "github_copilot_course_count": "7",
    }


def test_parse_pipe_table_drops_header_and_separator() -> None:
    block = section_text(SAMPLE_BUNDLE, "Cert Status + Badge URLs")
    assert block is not None
    rows = parse_pipe_table(block)
    assert rows == [
        ["AZ-900", "**Certified April 18, 2026**"],
        ["AI-200", "**Active target**"],
    ]


def test_substitute_fragments_replaces_known_and_leaves_unknown() -> None:
    text = "{cert_status_short} and {unknown_fragment}"
    result = substitute_fragments(text, {"cert_status_short": "AZ-900 Certified"})
    assert result == "AZ-900 Certified and {unknown_fragment}"


def test_split_top_level_commas_respects_parens() -> None:
    parts = split_top_level_commas("C#, Entity Framework Core (v6, v8), Angular")
    assert parts == ["C#", "Entity Framework Core (v6, v8)", "Angular"]


def test_clean_skill_term_strips_trailing_parens() -> None:
    assert clean_skill_term("Entity Framework Core (course-level)") == "Entity Framework Core"


def test_clean_skill_term_drops_long_multiclause_phrases() -> None:
    assert clean_skill_term("SOLID principles and design patterns") is None


def test_derive_skill_terms_dedupes_cleans_and_excludes() -> None:
    block = section_text(SAMPLE_BUNDLE, "Technical Skills (flat list, ATS-formatted)")
    assert block is not None
    categories = subsections(block)
    terms = derive_skill_terms(categories, exclude={"C#"})
    assert "C#" not in terms
    assert "Entity Framework Core" in terms
    assert "SOLID principles and design patterns" not in terms
    assert "Angular" in terms


def test_derive_skill_terms_respects_limit() -> None:
    block = section_text(SAMPLE_BUNDLE, "Technical Skills (flat list, ATS-formatted)")
    assert block is not None
    categories = subsections(block)
    terms = derive_skill_terms(categories, limit=2)
    assert len(terms) == 2


def test_load_fragments_and_skills() -> None:
    fragments, skills_categories = load_fragments_and_skills(SAMPLE_BUNDLE)
    assert fragments["cert_status_short"] == "AZ-900 Certified"
    assert "Backend" in skills_categories
    assert "Frontend" in skills_categories
