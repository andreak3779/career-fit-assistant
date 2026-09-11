#!/usr/bin/env python3
"""Generate Jobgether profile copy.

Renders the same draft the ``update_jobgether_profile`` SKILL.md workflow
produces conversationally — Title/Headline, About/Bio, Skills, and Job
Preferences, with `{fragment}` substitution and a resume-freshness check —
by reading the skill's own prose templates (fenced code blocks / tables in
SKILL.md) rather than duplicating them here, so the two can't drift apart.
See ``generate_linkedin.py`` for the fuller version of this pattern.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

from shared.bundle_markdown import (
    bundle_version_and_generated,
    derive_skill_terms,
    fenced_blocks,
    load_fragments_and_skills,
    section_text,
    substitute_fragments,
)
from shared.provenance import write_sidecar
from shared.resume_freshness import resume_freshness_lines

MD_BUNDLE_PATH = ROOT / "project-3-presence-identity" / "presence-bundle.md"
SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"
DRAFT_PATH = ROOT / "project-3-presence-identity" / "jobgether-profile-update-draft.md"

_SKILLS_CAP = 20


@dataclass
class MdBundle:
    bundle_version: int | None
    generated: str | None
    fragments: dict[str, str]
    skills_categories: dict[str, str]


def _load_md_bundle(path: Path) -> MdBundle:
    text = path.read_text(encoding="utf-8")
    version, generated = bundle_version_and_generated(text)
    fragments, skills_categories = load_fragments_and_skills(text)
    return MdBundle(
        bundle_version=version,
        generated=generated,
        fragments=fragments,
        skills_categories=skills_categories,
    )


def _step1_title(skill_text: str, fragments: dict[str, str]) -> tuple[str, list[str]]:
    section = section_text(skill_text, "Step 1 — Title / Headline") or ""
    blocks = fenced_blocks(section)
    if not blocks:
        return "", ["Step 1 — could not find Title template in SKILL.md"]
    return substitute_fragments(blocks[0].strip("\n"), fragments), []


def _step2_about(skill_text: str, fragments: dict[str, str]) -> tuple[str, list[str]]:
    section = section_text(skill_text, "Step 2 — About / Bio") or ""
    blocks = fenced_blocks(section)
    warnings: list[str] = []
    if not blocks:
        warnings.append("Step 2 — could not find About/Bio template in SKILL.md")
        return "", warnings
    about = substitute_fragments(blocks[0].strip("\n"), fragments)
    if len(about) > 1500:
        warnings.append(
            f"Step 2 About/Bio is {len(about)} chars — over the ~1,500-char practical "
            "target (no published hard limit), consider trimming"
        )
    return about, warnings


def _step3_skills(skills_categories: dict[str, str]) -> str:
    return ", ".join(derive_skill_terms(skills_categories, limit=_SKILLS_CAP))


def _step4_job_preferences(skill_text: str) -> str:
    return (section_text(skill_text, "Step 4 — Job Preferences") or "").strip()


def _build_draft(root: Path, md: MdBundle, skill_text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    char_limits = section_text(skill_text, "Character Limits") or ""
    resume_check = resume_freshness_lines(root)

    title, w = _step1_title(skill_text, md.fragments)
    warnings.extend(w)
    about, w = _step2_about(skill_text, md.fragments)
    warnings.extend(w)
    skills = _step3_skills(md.skills_categories)
    preferences = _step4_job_preferences(skill_text)

    sections = [
        "<!-- GENERATED DRAFT — regenerate via the generate_jobgether MCP tool / "
        "update_jobgether_profile skill.",
        f"     Reflects presence-bundle.md bundle_version: {md.bundle_version} "
        f"(generated {md.generated}). -->",
        "",
        "# Jobgether Profile Update Draft",
        "",
        "## Character Limits",
        char_limits,
        "",
        "## Resume File Dependency Check",
        "\n".join(f"- {line}" for line in resume_check),
        "",
        "## Step 1 — Title / Headline",
        "```",
        title,
        "```",
        "",
        "## Step 2 — About / Bio",
        "```",
        about,
        "```",
        f"_{len(about)} / ~1,500 chars (practical target)_",
        "",
        "## Step 3 — Skills",
        skills,
        "",
        "## Step 4 — Job Preferences",
        preferences,
        "",
        "## After applying",
        "Once each field above has been pasted into Jobgether, update the "
        '"Current State vs Target" diff table in SKILL.md by hand — this draft '
        "has no visibility into what's actually live on Jobgether.",
    ]
    return "\n".join(sections), warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-jobgether", description="Generate Jobgether profile copy"
    )
    parser.add_argument(
        "--out", type=Path, help="Output markdown file (default: jobgether-profile-update-draft.md)"
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
    content, warnings = _build_draft(ROOT, md, skill_text)

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
        script="generate_jobgether.py",
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
