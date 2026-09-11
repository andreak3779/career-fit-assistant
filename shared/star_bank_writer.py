"""Write-back helpers for ``reference/star-bank.md``.

The star bank is a hand-maintained reference file, not disposable generated
output — its ``last_used``/``used_for`` metadata is meant to stay current so
future interview-prep runs can rotate stories instead of repeating the same
one across consecutive applications. Nothing in this repo writes to it today;
this module is the one write path, built narrow and fail-closed on purpose
(see the plan's "star-bank.md write-back safety" design decision): every
function here operates on in-memory text and returns new text — callers
decide when (and whether) to actually touch the file — and a target that
can't be unambiguously located raises rather than silently no-oping or
guessing, since a wrong guess here means quietly corrupting hand-authored
interview material.

Both the update-existing-story and append-new-story renderers must produce
text that ``shared.markdown_sources.parse_star_bank()`` can parse back
correctly — round-trip safety is the module's core contract, not a nice-to-have.
"""

from __future__ import annotations

import difflib
import re
from typing import Any

_STORY_HEADING_RE = re.compile(r"^##\s+Story\s+(\d+)\s+—\s+(.+?)\s*$", re.MULTILINE)
_LAST_USED_FIELD_RE = re.compile(r"^(\*\*last_used:\*\*)(.*)$", re.MULTILINE)
_USED_FOR_FIELD_RE = re.compile(r"^(\*\*used_for:\*\*)(.*)$", re.MULTILINE)
_NEXT_H2_RE = re.compile(r"^##\s+", re.MULTILINE)

_UNUSED_PLACEHOLDER = "—"


def render_star_bank_update(
    text: str,
    *,
    story_number: int | None = None,
    story_title: str | None = None,
    last_used: str | None = None,
    used_for_append: str | None = None,
    new_story: dict[str, Any] | None = None,
) -> str:
    """Return updated star-bank.md text — either editing one story's metadata
    or appending a brand-new story block.

    Update-existing-story mode (``new_story`` is ``None``): locates the
    ``## Story N — Title`` block matching ``story_number`` (preferred) or
    falling back to an exact ``story_title`` match, and rewrites its
    ``last_used``/``used_for`` fields in place. Raises ``ValueError`` if no
    block matches — never guesses which story the caller meant.

    Append-new-story mode (``new_story`` given, shaped like a
    ``parse_star_bank()`` entry): renders a new ``## Story N — Title`` block
    (N = highest existing story number + 1) and inserts it immediately after
    the last existing story block, before any trailing non-story section
    (e.g. "## Story Selection Guide") — never at raw end-of-file, since the
    real reference file has template/guide content after the last story.
    This mode is a capability of this module only; ``interview_prep.py``
    never calls it automatically (authoring new S/T/A/R prose is an LLM
    judgment call, out of scope for this deterministic script — see the
    plan's Scope Boundary).
    """
    if new_story is not None:
        return _append_new_story(text, new_story)

    if story_number is None and story_title is None:
        raise ValueError(
            "render_star_bank_update requires story_number and/or story_title "
            "(to update an existing story) or new_story (to append one) — got neither"
        )

    matches = list(_STORY_HEADING_RE.finditer(text))
    target_idx: int | None = None
    if story_number is not None:
        for i, m in enumerate(matches):
            if int(m.group(1)) == story_number:
                target_idx = i
                break
    if target_idx is None and story_title is not None:
        for i, m in enumerate(matches):
            if m.group(2).strip() == story_title:
                target_idx = i
                break

    if target_idx is None:
        raise ValueError(
            "No STAR story found matching "
            f"story_number={story_number!r}, story_title={story_title!r}"
        )

    start = matches[target_idx].end()
    end = matches[target_idx + 1].start() if target_idx + 1 < len(matches) else len(text)
    block = text[start:end]
    updated_block = _apply_metadata_updates(
        block, last_used=last_used, used_for_append=used_for_append
    )
    return text[:start] + updated_block + text[end:]


def diff_star_bank_update(old_text: str, new_text: str) -> str:
    """Return a unified diff of a star-bank.md edit, for informational display."""
    diff = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile="star-bank.md (before)",
        tofile="star-bank.md (after)",
    )
    return "".join(diff)


def _apply_metadata_updates(
    block: str, *, last_used: str | None, used_for_append: str | None
) -> str:
    if last_used is not None:
        if not _LAST_USED_FIELD_RE.search(block):
            raise ValueError("Matched story block has no **last_used:** field to update")
        block = _LAST_USED_FIELD_RE.sub(lambda m: f"{m.group(1)} {last_used}", block, count=1)

    if used_for_append is not None:
        match = _USED_FOR_FIELD_RE.search(block)
        if not match:
            raise ValueError("Matched story block has no **used_for:** field to update")
        current = match.group(2).strip()
        entries = [
            e.strip() for e in current.split(",") if e.strip() and e.strip() != _UNUSED_PLACEHOLDER
        ]
        if used_for_append not in entries:
            entries.append(used_for_append)
        new_value = ", ".join(entries)
        block = _USED_FOR_FIELD_RE.sub(lambda m: f"{m.group(1)} {new_value}", block, count=1)

    return block


def _append_new_story(text: str, new_story: dict[str, Any]) -> str:
    matches = list(_STORY_HEADING_RE.finditer(text))
    next_number = max((int(m.group(1)) for m in matches), default=0) + 1
    new_block = _render_new_story_block(next_number, new_story)

    if matches:
        next_heading = _NEXT_H2_RE.search(text, matches[-1].end())
        insert_pos = next_heading.start() if next_heading else len(text)
    else:
        insert_pos = len(text)

    return text[:insert_pos] + new_block + text[insert_pos:]


def _render_new_story_block(number: int, story: dict[str, Any]) -> str:
    title = story["title"]
    use_for = " · ".join(story.get("use_for") or [])
    jd_tags = " ".join(f"`{t}`" for t in story.get("jd_tags") or [])
    last_used = story.get("last_used") or _UNUSED_PLACEHOLDER
    used_for_list = story.get("used_for") or []
    used_for = ", ".join(used_for_list) if used_for_list else _UNUSED_PLACEHOLDER

    lines = [
        f"## Story {number} — {title}",
        "",
        f"**Use for:** {use_for}",
        "",
        f"**JD tags:** {jd_tags}",
        "",
        f"**last_used:** {last_used}",
        f"**used_for:** {used_for}",
        "",
        "**Situation:**",
        story.get("situation", ""),
        "",
        "**Task:**",
        story.get("task", ""),
        "",
        "**Action:**",
        story.get("action", ""),
        "",
        "**Result:**",
        story.get("result", ""),
    ]

    adapt_when = story.get("adapt_when") or []
    if adapt_when:
        lines.append("")
        lines.append("**Adapt when:**")
        lines.extend(f"- {item}" for item in adapt_when)

    lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines) + "\n"
