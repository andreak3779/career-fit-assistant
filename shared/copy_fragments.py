"""Compute the "Copy Fragments" — course-count sentence, cert status short
form, etc. — that Project 3's profile-update generators splice into draft
copy instead of hand-embedding a number that goes stale.

Split out of ``render_md_bundles.py`` so generators can call it directly from
a loaded bundle (``shared.bundle_loader.load_presence_bundle``) without going
through the rendered markdown bundle as an intermediary — the markdown
render is no longer the only path to this data.
"""

from __future__ import annotations

import re
from pathlib import Path

from shared.cert_status import cert_status_short
from shared.models import Cert

_AZURE_COUNTS_RE = re.compile(r"(\d+)\s*courses?\s*\+\s*(\d+)\s*labs", re.IGNORECASE)
_AZURE_COURSEWORK_ROW_RE = re.compile(
    r"\|\s*Azure coursework\s*\|\s*(.+?)\s*\|", re.IGNORECASE
)

FRAGMENT_KEYS = [
    "course_count_sentence",
    "cert_status_short",
    "azure_course_lab_sentence",
    "github_copilot_course_count",
    "leadership_course_count",
]


def _differentiator_match(differentiators: list[str], pattern: str) -> re.Match[str] | None:
    for item in differentiators:
        match = re.search(pattern, item, re.IGNORECASE)
        if match:
            return match
    return None


def _azure_coursework_counts(cell: str | None) -> tuple[str, str] | None:
    if not cell:
        return None
    match = _AZURE_COUNTS_RE.search(cell)
    return (match.group(1), match.group(2)) if match else None


def compute_copy_fragments(
    differentiators: list[str], cert_registry: list[Cert], azure_coursework: str | None
) -> dict[str, str]:
    fragments: dict[str, str] = {"cert_status_short": cert_status_short(cert_registry)}

    copilot = _differentiator_match(differentiators, r"GitHub Copilot:\s*(\d+)\s*courses")
    fragments["github_copilot_course_count"] = copilot.group(1) if copilot else ""

    leadership = _differentiator_match(
        differentiators, r"Communication:\s*(\d+)\s*leadership/communication"
    )
    fragments["leadership_course_count"] = leadership.group(1) if leadership else ""

    azure = _azure_coursework_counts(azure_coursework)
    if azure:
        courses, labs = azure
        fragments["azure_course_lab_sentence"] = (
            f"{courses} Pluralsight courses and {labs} hands-on labs across Azure"
        )
    else:
        fragments["azure_course_lab_sentence"] = ""

    pace = _differentiator_match(
        differentiators,
        r"Pace of learning:\s*(\d+)\s*courses completed \+\s*(\d+)\s*in progress \+\s*"
        r"(\d+)\s*labs\s*\((\d+)\s*completed,\s*(\d+)\s*in progress\)\s*=\s*\*{0,2}(\d+)\s*total",
    )
    if pace:
        completed, in_progress, labs, labs_done, labs_wip, total = pace.groups()
        fragments["course_count_sentence"] = (
            f"{completed} Pluralsight courses completed and {in_progress} more in progress, "
            f"plus {labs} hands-on labs ({labs_done} completed, {labs_wip} in progress) — {total} total"
        )
    else:
        fragments["course_count_sentence"] = ""

    return fragments


def fragments_block(fragments: dict[str, str]) -> str:
    return "\n".join(f'{k}: "{fragments.get(k, "")}"' for k in FRAGMENT_KEYS)


def azure_coursework_cell(root: Path) -> str | None:
    """Read the "Azure coursework" summary-row cell from profile-facts.md.

    This row lives only in profile-facts.md's markdown Cert Status table,
    not in the YAML frontmatter ``certs:`` list that the typed pipeline
    otherwise reads — so when the JSON bundle doesn't carry an
    ``azure_coursework`` field, the renderer (or any other call site) can
    still recover the cell by reading the source file once here. Used by
    ``compute_copy_fragments_by_root`` and exposed for the same reason the
    other helpers are: one place to read this regex.
    """
    path = root / "project-2-profile-learning-hub" / "profile-facts.md"
    if not path.exists():
        return None
    match = _AZURE_COURSEWORK_ROW_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def compute_copy_fragments_by_root(
    differentiators: list[str], cert_registry: list[Cert], root: Path
) -> dict[str, str]:
    """Bundle-path-friendly wrapper: read Azure coursework from disk first,
    then call :func:`compute_copy_fragments`.

    Used by the markdown renderer (which doesn't carry the
    ``azure_coursework`` field on its bundles) and any other call site
    that prefers "give me a repo root" over "give me the pre-extracted
    string." Returns the same dict shape.
    """
    return compute_copy_fragments(
        differentiators, cert_registry, azure_coursework_cell(root)
    )
