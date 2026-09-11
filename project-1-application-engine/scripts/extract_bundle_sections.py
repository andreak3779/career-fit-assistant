#!/usr/bin/env python3
"""Extract a slice of app-engine-bundle.md instead of loading the whole file.

`app-engine-bundle.md` is ~46KB / ~11.5K tokens, and roughly a third of that
(the `## Resume` heading onward — Professional Experience, Continuous Learning,
Education, a second "Key Differentiators" section written as resume bullets,
References) is career-history prose meant for document generation. Several
skills only need the "facts" portion above it (Copy Fragments, Cert Registry,
Key Differentiators, Known Genuine Gaps, Resolved Framing Gaps, Portfolio
Projects, Skills — ATS Keywords, AI-200 Domain Coverage) or a single named
section — not the whole file. This script prints just what's asked for.

Note the bundle has two headings both named "## Key Differentiators": a short
gap-analysis-oriented list in the facts section, and a longer resume-bullet
version embedded later, under "## Resume". `section` always matches the
*first* occurrence, which is the one every current caller wants — the facts
list, not the resume-bullet one.

Usage:
    python scripts/extract_bundle_sections.py facts
    python scripts/extract_bundle_sections.py section "Cert Registry" ["Key Differentiators" ...]
    python scripts/extract_bundle_sections.py contact

Each subcommand accepts --root (repo root, default: this repo), --file (bundle
filename, default: app-engine-bundle.md), and --project (project directory the
file lives under, default: project-1-application-engine). presence-bundle.md
also works for the same subcommands via
--file presence-bundle.md --project project-3-presence-identity.

Exit code 0 on success, 1 if the bundle file is missing, or if every
requested section name was not found.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RESUME_HEADING = "## Resume"
CONTACT_MARKER = "**Contact Information**"


def _bundle_path(root: Path, project: str, filename: str) -> Path:
    return root / project / filename


def _read(root: Path, project: str, filename: str) -> str:
    path = _bundle_path(root, project, filename)
    if not path.exists():
        raise FileNotFoundError(f"bundle not found: {path}")
    return path.read_text(encoding="utf-8")


def _sections(text: str) -> list[tuple[str, int, int]]:
    """Return (heading_text, start_line, end_line) for every top-level '## ' heading."""
    lines = text.split("\n")
    headings = [(i, line) for i, line in enumerate(lines) if line.startswith("## ")]
    headings.append((len(lines), ""))
    return [
        (headings[i][1][3:].strip(), headings[i][0], headings[i + 1][0])
        for i in range(len(headings) - 1)
    ]


def cmd_facts(root: Path, project: str, filename: str) -> int:
    text = _read(root, project, filename)
    idx = text.find(f"\n{RESUME_HEADING}\n")
    if idx == -1:
        idx = text.find(f"\n{RESUME_HEADING}")  # tolerate EOF with no trailing newline
    if idx == -1:
        print(text)  # no Resume heading found — nothing to cut, print everything
        return 0
    print(text[: idx + 1].rstrip())
    return 0


def cmd_section(root: Path, project: str, filename: str, names: list[str]) -> int:
    text = _read(root, project, filename)
    lines = text.split("\n")
    sections = _sections(text)
    by_name: dict[str, tuple[int, int]] = {}
    for heading, start, end in sections:
        key = heading.lower()
        if key not in by_name:  # first occurrence wins
            by_name[key] = (start, end)

    found_any = False
    for name in names:
        match = by_name.get(name.strip().lower())
        if match is None:
            print(f'"{name}" — SECTION NOT FOUND (no "## {name}" heading in {filename})')
            continue
        start, end = match
        print("\n".join(lines[start:end]).rstrip())
        print()
        found_any = True
    return 0 if found_any else 1


def cmd_contact(root: Path, project: str, filename: str) -> int:
    text = _read(root, project, filename)
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.strip() == CONTACT_MARKER), None)
    if start is None:
        print(f"Contact Information block not found in {filename}")
        return 1
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].strip() == "---"),
        len(lines),
    )
    print("\n".join(lines[start:end]).rstrip())
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="extract_bundle_sections.py",
        description="Extract a slice of app-engine-bundle.md instead of loading the whole file.",
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="repo root (default: this repo)")
    parser.add_argument(
        "--file",
        default="app-engine-bundle.md",
        help="bundle filename (default: app-engine-bundle.md)",
    )
    parser.add_argument(
        "--project",
        default="project-1-application-engine",
        help="project directory the bundle lives under (default: project-1-application-engine; "
        "use project-3-presence-identity for presence-bundle.md)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("facts", help="everything before the '## Resume' heading")
    section_p = subparsers.add_parser(
        "section", help="one or more named '## ' sections (first occurrence)"
    )
    section_p.add_argument("names", nargs="+", help='heading text, e.g. "Cert Registry"')
    subparsers.add_parser("contact", help="just the Contact Information block")

    args = parser.parse_args(argv)

    try:
        if args.command == "facts":
            return cmd_facts(args.root, args.project, args.file)
        if args.command == "section":
            return cmd_section(args.root, args.project, args.file, args.names)
        if args.command == "contact":
            return cmd_contact(args.root, args.project, args.file)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
