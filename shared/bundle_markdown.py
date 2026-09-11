"""Generic parsing helpers for reading `presence-bundle.md` and a skill's own
SKILL.md prose templates directly, rather than a separate hand-maintained
copy of the same content in Python. Shared by every Project 3 profile-update
generator (LinkedIn, GitHub, Jobgether, Indeed/ZipRecruiter, Pluralsight) so
the section/fragment/table parsing logic exists in exactly one place — see
project-3-presence-identity/CLAUDE.md's "Known limitations" note about
hardcoded copies drifting from the bundle for why duplicating this per
generator is the failure mode to avoid.
"""

from __future__ import annotations

import re
from pathlib import Path

_BUNDLE_VERSION_RE = re.compile(r"bundle_version:\s*(\d+)")
_BUNDLE_GENERATED_RE = re.compile(r"generated:\s*(\S+)")
_FRAGMENT_LINE_RE = re.compile(r'^(\w+):\s*"(.*)"\s*$')


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def bundle_version_and_generated(text: str) -> tuple[int | None, str | None]:
    version_m = _BUNDLE_VERSION_RE.search(text)
    gen_m = _BUNDLE_GENERATED_RE.search(text)
    return (int(version_m.group(1)) if version_m else None, gen_m.group(1) if gen_m else None)


def md_sections(text: str) -> list[tuple[str, int, int]]:
    """Return (heading, start_line, end_line) for every top-level '## ' heading."""
    lines = text.split("\n")
    headings = [(i, line) for i, line in enumerate(lines) if line.startswith("## ")]
    headings.append((len(lines), ""))
    return [
        (headings[i][1][3:].strip(), headings[i][0], headings[i + 1][0])
        for i in range(len(headings) - 1)
    ]


def section_text(text: str, name: str) -> str | None:
    lines = text.split("\n")
    for heading, start, end in md_sections(text):
        if heading.lower() == name.lower():
            return "\n".join(lines[start + 1 : end]).strip()
    return None


def subsections(block: str) -> dict[str, str]:
    """Same as md_sections but for '### ' headings within an already-sliced block."""
    lines = block.split("\n")
    idxs = [(i, line) for i, line in enumerate(lines) if line.startswith("### ")]
    idxs.append((len(lines), ""))
    result: dict[str, str] = {}
    for i in range(len(idxs) - 1):
        name = idxs[i][1][4:].strip()
        result[name] = "\n".join(lines[idxs[i][0] + 1 : idxs[i + 1][0]]).strip()
    return result


def fenced_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] | None = None
    for line in text.split("\n"):
        if line.strip().startswith("```"):
            if current is None:
                current = []
            else:
                blocks.append("\n".join(current))
                current = None
            continue
        if current is not None:
            current.append(line)
    return blocks


def parse_fragments(block: str) -> dict[str, str]:
    fragments: dict[str, str] = {}
    for line in block.splitlines():
        m = _FRAGMENT_LINE_RE.match(line.strip())
        if m:
            fragments[m.group(1)] = m.group(2)
    return fragments


def parse_pipe_table(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        if set(stripped.replace("|", "").replace(":", "").strip()) <= {"-", ""}:
            continue  # separator row
        rows.append([c.strip() for c in stripped.strip("|").split("|")])
    return rows[1:] if rows else rows  # drop header row


def substitute_fragments(text: str, fragments: dict[str, str]) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: fragments.get(m.group(1), m.group(0)), text)


def split_top_level_commas(text: str) -> list[str]:
    """Split on commas that aren't inside parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def clean_skill_term(raw: str) -> str | None:
    term = re.sub(r"\s*\([^)]*\)\s*$", "", raw).strip()
    if not term or len(term.split()) > 4:
        return None
    return term


def load_fragments_and_skills(bundle_text: str) -> tuple[dict[str, str], dict[str, str]]:
    """Convenience for the common case (Jobgether, Indeed/ZipRecruiter): a
    generator that only needs the Copy Fragments and the per-category
    Technical Skills blocks, not the fuller experience/portfolio/cert data
    the LinkedIn generator also parses.
    """
    fragments = parse_fragments(section_text(bundle_text, "Copy Fragments") or "")
    skills_block = section_text(bundle_text, "Technical Skills (flat list, ATS-formatted)") or ""
    skills_categories = subsections(skills_block)
    return fragments, skills_categories


def derive_skill_terms(
    skills_categories: dict[str, str], *, exclude: set[str] = frozenset(), limit: int | None = None
) -> list[str]:
    """Flatten every category's comma-separated terms into a deduped,
    cleaned, LinkedIn/ATS-taggable list — dropping ``(course-level)``
    qualifiers and multi-clause phrases, and anything already in ``exclude``
    (case-insensitive). Shared by every profile-update skill that derives a
    skills list from presence-bundle.md's ``## Technical Skills`` section
    rather than reusing a fixed list.
    """
    seen = {t.strip().lower() for t in exclude}
    result: list[str] = []
    for items_text in skills_categories.values():
        for raw in split_top_level_commas(items_text):
            term = clean_skill_term(raw)
            if term and term.lower() not in seen:
                seen.add(term.lower())
                result.append(term)
    return result[:limit] if limit is not None else result
