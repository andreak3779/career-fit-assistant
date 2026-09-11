#!/usr/bin/env python3
"""Render the human/skill-readable .md bundles from the typed JSON bundles.

Replaces the old workflow where a fresh Claude session hand-authored
``app-engine-bundle.md`` and ``presence-bundle.md`` by following ~300 lines of
SKILL.md prose from scratch each time — a process with no enforcement other
than "read carefully and don't typo a number." Now the JSON bundles (written
by ``build_bundles.py``, gated by ``validate.py``) are the single computed
source of truth, and this script deterministically renders the two .md files
skills actually read. Both files share one ``bundle_version`` (the
ProfileBundle's), so they can no longer skew apart.

Pipeline: build_bundles.py (compute) -> validate.py (gate) -> render_md_bundles.py (render)

Usage:
    python scripts/render_md_bundles.py [repo_root]

Requires outputs/profile-bundle.json and outputs/presence-bundle.json to
already exist and pass validation.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from shared import load_presence_bundle, load_profile_bundle
from shared.docx_layout import DEFAULT_SIGNATURE_NAME
from shared.models import Cert, CertStatus, PresenceBundle, ProfileBundle
from shared.pii_guard import scan_text

ROOT = Path(__file__).resolve().parents[4]

_SOURCE_LABEL_ORDER = ["profile-facts", "Resume_Snapshot", "github-repos", "skills-summary"]


# ---------------------------------------------------------------------------
# Copy Fragments — computed once, shared by both bundles
# ---------------------------------------------------------------------------


def _cert_status_short(cert_registry: list[Cert]) -> str:
    parts: list[str] = []
    for c in cert_registry:
        if c.status == CertStatus.CERTIFIED:
            parts.append(f"{c.code} Certified")
        elif c.status == CertStatus.IN_PROGRESS:
            parts.append(f"{c.code} in progress")
    return " · ".join(parts)


def _differentiator_match(differentiators: list[str], pattern: str) -> re.Match[str] | None:
    for item in differentiators:
        match = re.search(pattern, item, re.IGNORECASE)
        if match:
            return match
    return None


def compute_copy_fragments(
    differentiators: list[str], cert_registry: list[Cert], root: Path
) -> dict[str, str]:
    fragments: dict[str, str] = {"cert_status_short": _cert_status_short(cert_registry)}

    copilot = _differentiator_match(differentiators, r"GitHub Copilot:\s*(\d+)\s*courses")
    fragments["github_copilot_course_count"] = copilot.group(1) if copilot else ""

    leadership = _differentiator_match(
        differentiators, r"Communication:\s*(\d+)\s*leadership/communication"
    )
    fragments["leadership_course_count"] = leadership.group(1) if leadership else ""

    azure = _azure_coursework_counts(root)
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


def _fragments_block(fragments: dict[str, str]) -> str:
    keys = [
        "course_count_sentence",
        "cert_status_short",
        "azure_course_lab_sentence",
        "github_copilot_course_count",
        "leadership_course_count",
    ]
    return "\n".join(f'{k}: "{fragments.get(k, "")}"' for k in keys)


# ---------------------------------------------------------------------------
# Shared rendering helpers
# ---------------------------------------------------------------------------


def _cert_row(c: Cert) -> str:
    if c.status == CertStatus.CERTIFIED:
        date_str = f"{c.date:%B} {c.date.day}, {c.date.year}" if c.date else ""
        cred = f" — [Credential]({c.credential_url})" if c.credential_url else ""
        return f"| {c.code} | **Certified {date_str}**{cred} |"
    if c.status == CertStatus.IN_PROGRESS:
        return f"| {c.code} | **Active target** — {c.notes or ''} |"
    return f"| {c.code} | {c.notes or 'Not pursuing'} |"


def _render_cert_table(
    cert_registry: list[Cert], azure_coursework_cell: str | None, include_azure_row: bool
) -> str:
    rows = ["| Cert | Status |", "|---|---|"]
    rows.extend(_cert_row(c) for c in cert_registry)
    if include_azure_row and azure_coursework_cell:
        rows.append(f"| Azure coursework | {azure_coursework_cell} |")
    return "\n".join(rows)


def _render_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip("\n")


_LAST_MODIFIED_LINE_RE = re.compile(r"^\*\*Last Modified:.*\*\*\s*$\n?", re.MULTILINE)


def _strip_last_modified_line(text: str) -> str:
    """Drop Resume_Snapshot.md's own "Last Modified" line when embedding it.

    Per the original bundle spec this line is excluded — the bundle's own
    `generated:` manifest header replaces it, so embedding both would state
    two different "as of" dates for the same document.
    """
    return _LAST_MODIFIED_LINE_RE.sub("", text)


def _candidate_name(text: str) -> str:
    """Return the candidate's name from Resume_Snapshot.md's leading ``# Name`` heading.

    Falls back to ``DEFAULT_SIGNATURE_NAME`` (shared/docx_layout.py) so the
    bundles never hardcode a literal name — the source-of-truth resume is the
    only place the name should be spelled out.
    """
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return DEFAULT_SIGNATURE_NAME


def _second_nonblank_line(text: str) -> str:
    """Return the second non-blank, non-heading line (a title's tagline)."""
    seen_first = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not seen_first:
            seen_first = True
            continue
        return stripped
    return ""


_AZURE_COURSEWORK_ROW_RE = re.compile(r"\|\s*Azure coursework\s*\|\s*(.+?)\s*\|", re.IGNORECASE)
_AZURE_COUNTS_RE = re.compile(r"(\d+)\s*courses?\s*\+\s*(\d+)\s*labs", re.IGNORECASE)


def _azure_coursework_cell(root: Path) -> str | None:
    """Read the full "Azure coursework" summary-row cell from profile-facts.md.

    This row lives only in profile-facts.md's markdown Cert Status table, not
    in the YAML frontmatter `certs:` list that the typed pipeline otherwise
    reads — so it isn't available anywhere in the JSON bundle. Reading it here
    (rather than teaching the typed model a one-off field for a single summary
    row) keeps the schema focused on real certs.
    """
    path = root / "project-2-profile-learning-hub" / "profile-facts.md"
    if not path.exists():
        return None
    match = _AZURE_COURSEWORK_ROW_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _azure_coursework_counts(root: Path) -> tuple[str, str] | None:
    """Extract just the (courses, labs) counts, for the Copy Fragment sentence."""
    cell = _azure_coursework_cell(root)
    if not cell:
        return None
    match = _AZURE_COUNTS_RE.search(cell)
    return (match.group(1), match.group(2)) if match else None


def _read_prior_changelog(path: Path, max_entries: int = 4) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    match = re.search(r"change_log:\n((?:  - .*\n?)+)", text)
    if not match:
        return []
    return [line for line in match.group(1).splitlines() if line.strip()][:max_entries]


# ---------------------------------------------------------------------------
# app-engine-bundle.md
# ---------------------------------------------------------------------------


def render_app_engine_bundle(profile: ProfileBundle, root: Path) -> str:
    fragments = compute_copy_fragments(profile.differentiators, profile.cert_registry, root)
    target_path = root / "project-1-application-engine" / "app-engine-bundle.md"

    prior = _read_prior_changelog(target_path)
    new_entry = (
        f"  - v{profile.bundle_version}: regenerated from source files "
        f"(profile-facts {profile.sources.get('profile-facts')}, "
        f"Resume_Snapshot {profile.sources.get('Resume_Snapshot')}, "
        f"github-repos {profile.sources.get('github-repos')}, "
        f"skills-summary {profile.sources.get('skills-summary')}) — {profile.generated.isoformat()}"
    )
    changelog = "\n".join([new_entry, *prior])

    sources_block = "\n".join(
        f"  {label + ':':<19}last_modified {profile.sources.get(label)}"
        for label in _SOURCE_LABEL_ORDER
    )

    github_repos_raw = _read_file(root / "project-2-profile-learning-hub" / "github-repos.md")
    resume_snapshot_raw_full = _read_file(
        root / "project-2-profile-learning-hub" / "Resume_Snapshot.md"
    )
    candidate_name = _candidate_name(resume_snapshot_raw_full)
    resume_snapshot_raw = _strip_last_modified_line(resume_snapshot_raw_full)

    gap_bullets = _render_bullets([g.notes or g.skill for g in profile.known_genuine_gaps])
    resolved_bullets = _render_bullets(profile.resolved_framing_gaps)

    ats_blocks = "\n\n".join(
        f"**{category}:** " + ", ".join(items) for category, items in profile.ats_keywords.items()
    )

    ai200_rows = "\n".join(
        f"| {row['domain']} | {row['status']} |" for row in profile.ai200_domain_coverage
    )
    ai200_table = "| Domain | Status |\n|--------|--------|\n" + ai200_rows

    return f"""<!-- GENERATED FILE — do not hand-edit. Regenerate via profile-hub-bundle-generator skill. -->
# App Engine Bundle — {candidate_name}
bundle_version: {profile.bundle_version}
generated: {profile.generated.isoformat()}
sources:
{sources_block}
change_log:
{changelog}

---
## Copy Fragments
{_fragments_block(fragments)}

---
## Cert Registry
{_render_cert_table(profile.cert_registry, _azure_coursework_cell(root), include_azure_row=True)}

---

## Key Differentiators
Surface these when the JD references them:
{_render_bullets(profile.differentiators)}

---

## Known Genuine Gaps
These are gaps unless the JD marks them optional:
{gap_bullets}

## Resolved Framing Gaps — Never Re-flag
Treat all of these as ✅ Strong Match in every gap analysis:
{resolved_bullets}

---

## Portfolio Projects
{github_repos_raw}

---

## Skills — ATS Keywords
{ats_blocks}

---

## AI-200 Domain Coverage
{ai200_table}

---

## Resume
{resume_snapshot_raw}
"""


# ---------------------------------------------------------------------------
# presence-bundle.md
# ---------------------------------------------------------------------------


def render_presence_bundle(presence: PresenceBundle, root: Path) -> str:
    fragments = compute_copy_fragments(presence.differentiators, presence.cert_registry, root)

    resume_snapshot_raw = _read_file(root / "project-2-profile-learning-hub" / "Resume_Snapshot.md")
    candidate_name = _candidate_name(resume_snapshot_raw)
    tagline = _second_nonblank_line(resume_snapshot_raw)

    tech_skill_blocks = "\n\n".join(
        f"### {category}\n" + ", ".join(items)
        for category, items in presence.technical_skills.items()
    )

    portfolio_rows = "\n".join(
        f"| {p.name} | {' · '.join(p.stack)} | {p.description} | {p.url} |"
        for p in presence.portfolio_projects
    )
    portfolio_table = (
        "| Project | Stack | Description | URL |\n|---|---|---|---|\n" + portfolio_rows
    )

    experience_blocks = "\n\n".join(
        f"### {job.title}\n"
        f"**{' | '.join(f for f in (job.company, job.location, job.dates) if f)}**\n\n"
        + _render_bullets(job.bullets)
        for job in presence.experience
    )

    return f"""<!-- GENERATED FILE — do not hand-edit. Regenerate via profile-hub-bundle-generator skill. -->
# Presence Bundle — {candidate_name}
bundle_version: {presence.bundle_version}
generated: {presence.generated.isoformat()}

---
## Copy Fragments
{_fragments_block(fragments)}

---
## Professional Headline

{presence.headline}

{tagline}

## Summary / About

{presence.summary}

## Cert Status + Badge URLs

{_render_cert_table(presence.cert_registry, None, include_azure_row=False)}

## Technical Skills (flat list, ATS-formatted)

{tech_skill_blocks}

## Professional Experience

{experience_blocks}

## Portfolio Projects

{portfolio_table}

## Key Differentiators

{_render_bullets(presence.differentiators)}
"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]).resolve() if argv else ROOT

    try:
        profile = load_profile_bundle(root)
        presence = load_presence_bundle(root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Run build_bundles.py (and validate.py as a gate) first.", file=sys.stderr)
        return 1

    app_engine_path = root / "project-1-application-engine" / "app-engine-bundle.md"
    presence_path = root / "project-3-presence-identity" / "presence-bundle.md"

    presence_md = render_presence_bundle(presence, root)

    # presence-bundle.md is committed to a public repo and must never contain
    # phone/email/etc — build_bundles.py already gates the JSON with
    # assert_presence_safe(), but this script also reads a couple of fields
    # (the headline tagline, the Azure-coursework cell) directly from raw
    # source markdown rather than through that gate. Scan the fully rendered
    # output as a last line of defense, not just the structured JSON fields.
    findings = scan_text(presence_md, source="presence-bundle.md")
    if findings:
        print(
            "ERROR: presence-bundle.md failed the PII scan — refusing to write it.", file=sys.stderr
        )
        for f in findings:
            print(f"  - {f['type']}: {f['value']!r} at offset {f['start']}", file=sys.stderr)
        print(
            "Fix the source data (likely Resume_Snapshot.md or profile-facts.md) and re-run "
            "the pipeline from build_bundles.py.",
            file=sys.stderr,
        )
        return 1

    app_engine_path.write_text(render_app_engine_bundle(profile, root), encoding="utf-8")
    presence_path.write_text(presence_md, encoding="utf-8")

    print(f"Wrote {app_engine_path.relative_to(root)} (v{profile.bundle_version})")
    print(f"Wrote {presence_path.relative_to(root)} (v{presence.bundle_version}) — PII scan clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
