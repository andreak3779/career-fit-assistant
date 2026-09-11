#!/usr/bin/env python3
"""Generate LinkedIn profile copy.

When ``presence-bundle.md`` (the markdown bundle) is available, this renders
the same rich, 8-step draft the ``update_linkedin_profile`` SKILL.md workflow
produces conversationally — About/Open-to-Work/Experience/Skills/
Certifications/Courses/Featured, with `{fragment}` substitution and
char-limit checks — by reading the *skill's own* prose templates (fenced code
blocks in SKILL.md) rather than duplicating them here, so the two can't drift
apart the way project-1's audit found hardcoded copies do (see
project-1-application-engine/CLAUDE.md "Known limitations"). Falls back to a
thinner summary from the JSON bundle (`outputs/presence-bundle.json`) when
the markdown bundle is missing.

Two sections of the draft (Step 3's portfolio-repo hook clauses, Step 4's
derived skills list) are built with heuristics — clause-splitting, paren-
stripping — rather than real judgment. Alongside the draft, this also writes
a ``<draft>.raw-inputs.json`` sidecar with the untouched source data for
those two sections, so a caller with actual judgment available (e.g. Claude,
reading this tool's response) can re-derive them properly instead of trusting
the heuristic output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

from shared import load_presence_bundle
from shared.bundle_markdown import (
    bundle_version_and_generated,
    derive_skill_terms,
    parse_fragments,
    parse_pipe_table,
)
from shared.bundle_markdown import fenced_blocks as _fenced_blocks
from shared.bundle_markdown import section_text as _section_text
from shared.bundle_markdown import subsections as _subsections
from shared.bundle_markdown import substitute_fragments as _substitute_fragments
from shared.provenance import write_sidecar

MD_BUNDLE_PATH = ROOT / "project-3-presence-identity" / "presence-bundle.md"
SKILL_PATH = Path(__file__).resolve().parents[1] / "SKILL.md"
DRAFT_PATH = ROOT / "project-3-presence-identity" / "linkedin-update-draft.md"

TOP_5_SKILLS = ["C#", "ASP.NET Core", "Angular", "Microsoft Azure", "CI/CD"]
STATIC_FEATURED_LINKS = [
    ("GitHub Profile", "https://github.com/sarah-ashford-dev"),
    ("Pluralsight Profile", "https://app.pluralsight.com/profile/sarah-ashford-dev"),
]


# ---------------------------------------------------------------------------
# JSON-bundle path — kept for the fallback branch and for callers that only
# need a quick headline/cert summary (still used by generate_github.py's
# sibling helpers and tests/test_p3_generators.py).
# ---------------------------------------------------------------------------


def _require_bundle(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Bundle not found: {path}")
    return path


def _bullet_or_line(text: str) -> str:
    return f"• {text.strip()}" if not text.strip().startswith(("•", "-")) else text.strip()


def _headline(bundle) -> str:
    if bundle.headline:
        return bundle.headline
    summary = bundle.summary.splitlines()[0] if bundle.summary else "Engineering leader"
    return f"{summary[:80]} | Engineering profile"


def _is_sparse(bundle) -> bool:
    return not any(
        [bundle.headline, bundle.summary, bundle.differentiators, bundle.portfolio_projects]
    )


def _about_section(bundle) -> str:
    parts: list[str] = []
    if bundle.summary:
        parts.append(bundle.summary)
    elif bundle.headline:
        parts.append(bundle.headline)
    else:
        parts.append("Profile summary placeholder — update from the latest presence bundle.")
    if bundle.differentiators:
        parts.append("\nWhat sets me apart:\n")
        for d in bundle.differentiators[:8]:
            parts.append(_bullet_or_line(d))
    skills: list[str] = []
    for items in bundle.technical_skills.values():
        skills.extend(items)
    if skills:
        parts.append("\nCore specialties:\n" + ", ".join(sorted(set(skills))[:20]))
    certs = _cert_summary(bundle)
    if certs:
        parts.append(f"\n{certs}")
    return "\n".join(parts).strip()


def _experience_section(bundle) -> str:
    projects = bundle.portfolio_projects
    if not projects:
        return "Experience drawn from profile bundle; update manually from resume."
    lines: list[str] = ["Recent portfolio highlights:\n"]
    for p in projects[:6]:
        stack = ", ".join(s.strip() for s in p.stack if s.strip())
        lines.append(f"• **{p.name}** — {p.description}")
        if stack:
            lines.append(f"  Stack: {stack}")
        lines.append("")
    return "\n".join(lines).strip()


def _skills_section(bundle) -> str:
    if not bundle.technical_skills:
        return "Update skills manually from resume technical-skills section."
    lines: list[str] = []
    for category, items in bundle.technical_skills.items():
        if not items:
            continue
        lines.append(f"• **{category}:** " + ", ".join(i.strip() for i in items[:15]))
    return "\n".join(lines)


def _cert_summary(bundle) -> str:
    if not bundle.cert_registry:
        return ""
    active = [c for c in bundle.cert_registry if c.status == "certified"]
    in_progress = [c for c in bundle.cert_registry if c.status == "in_progress"]
    parts: list[str] = []
    if active:
        parts.append("Certified: " + ", ".join(c.code for c in active))
    if in_progress:
        parts.append("Preparing for: " + ", ".join(c.code for c in in_progress))
    return " · ".join(parts)


def _generic_copy(bundle) -> str:
    sections: list[str] = [
        "# LinkedIn Profile Copy\n",
        "## Headline",
        _headline(bundle) + "\n",
        "## About",
        _about_section(bundle) + "\n",
        "## Experience",
        _experience_section(bundle) + "\n",
        "## Skills",
        _skills_section(bundle) + "\n",
    ]
    return "\n".join(sections)


# ---------------------------------------------------------------------------
# Markdown-bundle parsing (presence-bundle.md) — the rich path.
# ---------------------------------------------------------------------------


@dataclass
class MdBundle:
    bundle_version: int | None
    generated: str | None
    fragments: dict[str, str]
    headline: str
    cert_rows: list[tuple[str, str]]
    skills_categories: dict[str, str]
    experience: list[dict]
    portfolio: list[dict]


def _parse_experience(block: str) -> list[dict]:
    roles: list[dict] = []
    current: dict | None = None
    for line in block.splitlines():
        if line.startswith("### "):
            if current:
                roles.append(current)
            current = {"title": line[4:].strip(), "meta": "", "bullets": []}
        elif current is not None:
            stripped = line.strip()
            if stripped.startswith("- "):
                current["bullets"].append(stripped[2:].strip())
            elif stripped.startswith("**") and not current["meta"]:
                current["meta"] = stripped
    if current:
        roles.append(current)
    return roles


def _load_md_bundle(path: Path) -> MdBundle:
    text = path.read_text(encoding="utf-8")
    version, generated = bundle_version_and_generated(text)
    fragments = parse_fragments(_section_text(text, "Copy Fragments") or "")

    headline_block = _section_text(text, "Professional Headline") or ""
    headline = next(
        (line.strip("* ").strip() for line in headline_block.splitlines() if line.strip()), ""
    )

    cert_block = _section_text(text, "Cert Status + Badge URLs") or ""
    cert_rows = [(row[0], row[1]) for row in parse_pipe_table(cert_block) if len(row) >= 2]

    skills_block = _section_text(text, "Technical Skills (flat list, ATS-formatted)") or ""
    skills_categories = _subsections(skills_block)

    experience = _parse_experience(_section_text(text, "Professional Experience") or "")

    portfolio_block = _section_text(text, "Portfolio Projects") or ""
    portfolio = [
        {"name": row[0], "stack": row[1], "description": row[2], "url": row[3]}
        for row in parse_pipe_table(portfolio_block)
        if len(row) >= 4
    ]

    return MdBundle(
        bundle_version=version,
        generated=generated,
        fragments=fragments,
        headline=headline,
        cert_rows=cert_rows,
        skills_categories=skills_categories,
        experience=experience,
        portfolio=portfolio,
    )


# ---------------------------------------------------------------------------
# Step builders — each mirrors one "## Step N" section of SKILL.md.
# ---------------------------------------------------------------------------


def _project_hook(description: str) -> str:
    first_sentence = description.split(". ")[0]
    clause = re.split(r"[;,]", first_sentence)[0]
    return clause.strip().rstrip(".")


def _clean_course_title(raw: str) -> str | None:
    title = raw.strip()
    title = re.sub(r"\s*completed\b.*$", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s*\(\d+%.*?\)\s*$", "", title)
    title = re.sub(r"\s*\d+%.*$", "", title)
    title = re.sub(r"\s*in progress.*$", "", title, flags=re.IGNORECASE)
    title = title.strip(" -:")
    if len(title) < 5 or title[:1].isdigit() or title.lower() in {"active target", "certified"}:
        return None
    return title


def _step1_about(skill_text: str, fragments: dict[str, str]) -> tuple[str, list[str]]:
    section = _section_text(skill_text, "Step 1 — About Section") or ""
    blocks = _fenced_blocks(section)
    warnings: list[str] = []
    if not blocks:
        warnings.append("Step 1 — could not find About template in SKILL.md")
        return "", warnings
    about = _substitute_fragments(blocks[0].strip("\n"), fragments)
    if len(about) > 2600:
        warnings.append(f"Step 1 About is {len(about)} chars — over the 2,600 limit, trim before pasting")
    return about, warnings


def _step2_open_to_work(skill_text: str) -> str:
    section = _section_text(skill_text, "Step 2 — Open to Work Banner") or ""
    return section.strip()


def _step3_experience_entry(
    skill_text: str, fragments: dict[str, str], portfolio: list[dict]
) -> tuple[str, list[str]]:
    section = _section_text(skill_text, "Step 3 — Add Experience Entry") or ""
    blocks = _fenced_blocks(section)
    warnings: list[str] = []
    if not blocks:
        warnings.append("Step 3 — could not find Experience template in SKILL.md")
        return "", warnings
    template = blocks[0]
    hooks = ", ".join(f"{p['name']} ({_project_hook(p['description'])})" for p in portfolio)
    lines = []
    for line in template.split("\n"):
        if "derive the repo list" in line:
            lines.append(f"- Building portfolio projects on GitHub — {hooks}.")
        else:
            lines.append(line)
    text = _substitute_fragments("\n".join(lines).strip("\n"), fragments)
    if len(text) > 2000:
        warnings.append(f"Step 3 Experience entry is {len(text)} chars — over the 2,000 limit, trim before pasting")
    return text, warnings


def _step3_5_experience_sync(experience: list[dict]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    parts: list[str] = []
    for role in experience:
        if role["title"] == "Professional Development & Portfolio Building":
            continue  # owned by Step 3
        bullets = list(role["bullets"])
        body = "\n".join(f"- {b}" for b in bullets)
        trimmed = False
        while len(body) > 2000 and bullets:
            bullets.pop()
            body = "\n".join(f"- {b}" for b in bullets)
            trimmed = True
        if trimmed:
            warnings.append(
                f"Step 3.5 — trimmed bullets for {role['title']} to fit the 2,000-char limit "
                "(dropped from the bottom; re-check against the resume before pasting)"
            )
        header = f"### {role['title']}"
        if role["meta"]:
            header += f"\n{role['meta']}"
        parts.append(f"{header}\n\n{body}\n\n_{len(body)} / 2,000 chars_")
    return "\n\n".join(parts), warnings


def _step4_skills(skill_text: str, skills_categories: dict[str, str]) -> str:
    section = _section_text(skill_text, "Step 4 — Skills") or ""
    top5_block = _fenced_blocks(section)[0] if _fenced_blocks(section) else "\n".join(TOP_5_SKILLS)
    full_list = derive_skill_terms(skills_categories, exclude=set(TOP_5_SKILLS))

    lines = [
        "**Top 5 to pin (in order):**",
        "```",
        top5_block.strip("\n"),
        "```",
        "",
        "**Full list (derived from Technical Skills, top 5 excluded):**",
        ", ".join(full_list),
    ]
    return "\n".join(lines)


_AZ900_EXAM_PREP = "Microsoft Azure Fundamentals (AZ-900): Exam Preparation"
_AI200_EXAM_PREP = "Azure AI Cloud Developer Associate (AI-200): Exam Preparation"


def _status_label(status_cell: str) -> str:
    """The row's leading bold status word (e.g. "Certified April 18, 2026" or
    "Active target"), not the whole notes cell — which contains many other
    bolded course names that can themselves contain the word "Certified"
    (e.g. "Microsoft Certified: Azure Developer Associate (AZ-204)...")."""
    m = re.match(r"^\*\*(.*?)\*\*", status_cell.strip())
    return m.group(1) if m else status_cell


def _step5_certifications(skill_text: str, cert_rows: list[tuple[str, str]]) -> tuple[str, list[str]]:
    section = _section_text(skill_text, "Step 5 — Certifications") or ""
    ai200_status = next((s for c, s in cert_rows if c == "AI-200"), "")
    warnings: list[str] = []
    if "certified" in _status_label(ai200_status).lower():
        warnings.append("AI-200 shows Certified in the bundle — SKILL.md Step 5 still says wait; add the badge now")
        section = section.replace(
            '**Do NOT add AI-200 manually** — it\'s still in progress. '
            "Wait for Microsoft to issue that credential before repeating the steps above.",
            "**AI-200 is certified with a live credential** — add it now via the Microsoft Learn "
            "credentials page → Share → Add to LinkedIn, the same way AZ-900 was added above.",
        )
    return section.strip(), warnings


def _step6_courses(cert_rows: list[tuple[str, str]]) -> str:
    courses: list[str] = []
    for code, status in cert_rows:
        label = _status_label(status).lower()
        if "certified" in label or "progress" in label or "target" in label:
            if code == "AZ-900":
                courses.append(_AZ900_EXAM_PREP)
            elif code == "AI-200":
                courses.append(_AI200_EXAM_PREP)
    ai200_status = next((s for c, s in cert_rows if c == "AI-200"), "")
    for raw in re.findall(r"\*\*(.*?)\*\*", ai200_status):
        title = _clean_course_title(raw)
        if title:
            courses.append(title)
    seen: set[str] = set()
    deduped = []
    for c in courses:
        if c not in seen:
            seen.add(c)
            deduped.append(c)
    capped = deduped[:10]
    return "\n".join(f"- {c} — Pluralsight" for c in capped)


def _step7_featured(portfolio: list[dict]) -> str:
    lines: list[str] = []
    for i, p in enumerate(portfolio, start=1):
        desc = ". ".join(p["description"].split(". ")[:2]).rstrip(".") + "."
        lines.append(f"{i}. **{p['name']}** — {p['url']}\n   {desc}")
    offset = len(portfolio)
    for i, (title, url) in enumerate(STATIC_FEATURED_LINKS, start=offset + 1):
        lines.append(f"{i}. {title} — {url}")
    return "\n".join(lines)


def _build_rich_draft(md: MdBundle, skill_text: str) -> tuple[str, list[str]]:
    warnings: list[str] = []
    char_limits = _section_text(skill_text, "Character Limits") or ""

    about, w = _step1_about(skill_text, md.fragments)
    warnings.extend(w)
    open_to_work = _step2_open_to_work(skill_text)
    exp_entry, w = _step3_experience_entry(skill_text, md.fragments, md.portfolio)
    warnings.extend(w)
    exp_sync, w = _step3_5_experience_sync(md.experience)
    warnings.extend(w)
    skills = _step4_skills(skill_text, md.skills_categories)
    certs, w = _step5_certifications(skill_text, md.cert_rows)
    warnings.extend(w)
    courses = _step6_courses(md.cert_rows)
    featured = _step7_featured(md.portfolio)

    sections = [
        "<!-- GENERATED DRAFT — regenerate via the generate_linkedin MCP tool / "
        "update_linkedin_profile skill.",
        f"     Reflects presence-bundle.md bundle_version: {md.bundle_version} "
        f"(generated {md.generated}). -->",
        "",
        "# LinkedIn Profile Update Draft",
        "",
        "## Character Limits",
        char_limits,
        "",
        "## Step 1 — About Section",
        "```",
        about,
        "```",
        f"_{len(about)} / 2,600 chars_",
        "",
        "## Step 2 — Open to Work Banner",
        open_to_work,
        "",
        "## Step 3 — Add Experience Entry",
        "```",
        exp_entry,
        "```",
        "",
        "## Step 3.5 — Sync Existing Experience Entries",
        exp_sync,
        "",
        "## Step 4 — Skills",
        skills,
        "",
        "## Step 5 — Certifications",
        certs,
        "",
        "## Step 6 — Courses Section",
        courses,
        "",
        "## Step 7 — Featured Section",
        featured,
        "",
        "## After applying",
        "Once each field above has been pasted into LinkedIn, update the "
        "\"Current State vs Target\" diff table in SKILL.md by hand — this draft "
        "has no visibility into what's actually live on LinkedIn.",
    ]
    return "\n".join(sections), warnings


# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="generate-linkedin", description="Generate LinkedIn profile copy"
    )
    parser.add_argument(
        "--out", type=Path, help="Output markdown file (default: linkedin-update-draft.md, "
        "or outputs/LinkedIn_Copy.md if presence-bundle.md is unavailable)"
    )
    args = parser.parse_args(argv)

    warnings: list[str] = []
    evidence_sources: list[str] = []
    raw_inputs_file: Path | None = None
    raw_inputs_content: dict | None = None

    if MD_BUNDLE_PATH.is_file() and SKILL_PATH.is_file():
        md = _load_md_bundle(MD_BUNDLE_PATH)
        skill_text = SKILL_PATH.read_text(encoding="utf-8")
        content, warnings = _build_rich_draft(md, skill_text)
        out_file = args.out or DRAFT_PATH
        bundle_for_sidecar = md
        evidence_sources = [p["name"] for p in md.portfolio]
        raw_inputs_file = out_file.with_name(out_file.stem + ".raw-inputs.json")
        raw_inputs_content = {
            "note": (
                "Pre-heuristic source data for the two sections of the draft that use "
                "clause-splitting/paren-stripping heuristics rather than real judgment: "
                "Step 3's portfolio-repo hook clauses and Step 4's derived skills list. "
                "An LLM refining the draft should re-derive those two sections from this "
                "raw data directly rather than trusting the heuristic output."
            ),
            "portfolio_projects": md.portfolio,
            "technical_skills_categories": md.skills_categories,
        }
    else:
        try:
            _require_bundle(ROOT / "outputs" / "presence-bundle.json")
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        try:
            bundle = load_presence_bundle(ROOT)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        content = _generic_copy(bundle)
        out_file = args.out or ROOT / "outputs" / "LinkedIn_Copy.md"
        bundle_for_sidecar = bundle
        if _is_sparse(bundle):
            warnings.append("sparse bundle — manually review public copy")
        if not bundle.headline:
            warnings.append("no bundle headline — fallback headline used")
        warnings.append(f"presence-bundle.md not found at {MD_BUNDLE_PATH} — used generic JSON-bundle copy")
        evidence_sources = [p.name for p in bundle.portfolio_projects[:6]]

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

    if raw_inputs_file is not None:
        try:
            raw_inputs_file.write_text(
                json.dumps(raw_inputs_content, indent=2) + "\n", encoding="utf-8"
            )
            print(f"Wrote {raw_inputs_file}")
        except OSError as exc:
            print(f"WARNING: could not write raw inputs file {raw_inputs_file}: {exc}", file=sys.stderr)

    sidecar = write_sidecar(
        out_file,
        script="generate_linkedin.py",
        bundle=bundle_for_sidecar,
        inputs=[],
        evidence_sources=evidence_sources,
        warnings=warnings,
    )
    print(f"Wrote {out_file}")
    print(f"Wrote {sidecar}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
