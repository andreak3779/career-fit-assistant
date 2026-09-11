#!/usr/bin/env python3
"""Generate Pluralsight profile copy.

Renders the same draft the ``update_pluralsight_profile`` SKILL.md workflow
produces conversationally — Bio/Tagline and Profile Fields, with `{fragment}`
substitution — by reading the skill's own prose templates (fenced code
blocks / tables in SKILL.md) rather than duplicating them here, so the two
can't drift apart. See ``generate_linkedin.py`` for the fuller version of
this pattern.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

from shared.bundle_markdown import (
    bundle_version_and_generated,
    fenced_blocks,
    parse_fragments,
    section_text,
    substitute_fragments,
)
from shared.provenance import write_sidecar

MD_BUNDLE_PATH = ROOT / "project-3-presence-identity" / "presence-bundle.md"
SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"
DRAFT_PATH = ROOT / "project-3-presence-identity" / "pluralsight-profile-update-draft.md"

_BIO_PRACTICAL_TARGET = 150


@dataclass
class MdBundle:
    bundle_version: int | None
    generated: str | None
    fragments: dict[str, str]


def _load_md_bundle(path: Path) -> MdBundle:
    text = path.read_text(encoding="utf-8")
    version, generated = bundle_version_and_generated(text)
    fragments = parse_fragments(section_text(text, "Copy Fragments") or "")
    return MdBundle(bundle_version=version, generated=generated, fragments=fragments)


def _step1_bio(skill_text: str, fragments: dict[str, str]) -> tuple[str, list[str]]:
    section = section_text(skill_text, "Step 1 — Bio / Tagline") or ""
    blocks = fenced_blocks(section)
    warnings: list[str] = []
    if not blocks:
        warnings.append("Step 1 — could not find Bio template in SKILL.md")
        return "", warnings
    bio = substitute_fragments(blocks[0].strip("\n"), fragments)
    if len(bio) > _BIO_PRACTICAL_TARGET:
        warnings.append(
            f"Step 1 Bio is {len(bio)} chars — over the ~{_BIO_PRACTICAL_TARGET}-char "
            "practical target (no published hard limit), consider trimming"
        )
    return bio, warnings


def _step2_profile_fields(skill_text: str) -> str:
    section = section_text(skill_text, "Step 2 — Profile Fields") or ""
    return section.strip()


def _build_draft(md: MdBundle, skill_text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    char_limits = section_text(skill_text, "Character Limits") or ""

    bio, w = _step1_bio(skill_text, md.fragments)
    warnings.extend(w)
    fields = _step2_profile_fields(skill_text)

    sections = [
        "<!-- GENERATED DRAFT — regenerate via the generate_pluralsight MCP tool / "
        "update_pluralsight_profile skill.",
        f"     Reflects presence-bundle.md bundle_version: {md.bundle_version} "
        f"(generated {md.generated}). -->",
        "",
        "# Pluralsight Profile Update Draft",
        "",
        "## Character Limits",
        char_limits,
        "",
        "## Step 1 — Bio / Tagline",
        "```",
        bio,
        "```",
        f"_{len(bio)} chars (practical target: ~{_BIO_PRACTICAL_TARGET})_",
        "",
        "## Step 2 — Profile Fields",
        fields,
        "",
        "## After applying",
        "Once each field above has been pasted into Pluralsight, update the "
        '"Current State vs Target" diff table in SKILL.md by hand — this draft '
        "has no visibility into what's actually live on Pluralsight.",
    ]
    return "\n".join(sections), warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-pluralsight", description="Generate Pluralsight profile copy"
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Output markdown file (default: pluralsight-profile-update-draft.md)",
    )
    args = parser.parse_args(argv)

    if not MD_BUNDLE_PATH.is_file():
        print(f"ERROR: Bundle not found: {MD_BUNDLE_PATH}", file=sys.stderr)
        return 1
    if not SKILL_PATH.is_file():
        print(f"ERROR: SKILL.md not found: {SKILL_PATH}", file=sys.stderr)
        return 1

    md = _load_md_bundle(MD_BUNDLE_PATH)
    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    content, warnings = _build_draft(md, skill_text)

    out_file = args.out or DRAFT_PATH
    try:
        out_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: cannot create output directory {out_file.parent}: {exc}", file=sys.stderr)
        return 1
    try:
        out_file.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot write output file {out_file}: {exc}", file=sys.stderr)
        return 1

    sidecar = write_sidecar(
        out_file,
        script="generate_pluralsight.py",
        bundle=md,
        inputs=[],
        evidence_sources=[],
        warnings=warnings,
    )
    print(f"Wrote {out_file}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
