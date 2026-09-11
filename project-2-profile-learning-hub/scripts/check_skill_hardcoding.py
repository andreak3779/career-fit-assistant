#!/usr/bin/env python3
"""Scan SKILL.md files for hardcoded facts that duplicate bundle-computed data.

Guardrail against the failure mode found in an Aug 2026 audit: skill files
stating a cert status, GitHub Copilot course count, leadership course count,
or Azure Functions course count as literal prose instead of referencing the
Copy Fragments mechanism (`{cert_status_short}`, `{github_copilot_course_count}`,
`{leadership_course_count}`, ...) or deriving the value live at generation
time. Literal numbers/statuses silently go stale as `profile-facts.md` and
`pluralsight-courses.md` change; this script re-derives the current truth and
flags any skill text that no longer matches it.

This is advisory, not a bundle-validation gate (unlike validate.py's 6 checks) —
it scans free-form prose with regex heuristics, so false positives are possible
(e.g. a deliberately-preserved historical date). Read each finding before editing.

Usage:
    python scripts/check_skill_hardcoding.py [repo_root]

Exit code 0 if no findings, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from shared import load_sources

ROOT = Path(__file__).resolve().parents[2]

CERT_CODE_RE = re.compile(r"\b(AZ-900|AZ-204|AZ-104|AI-200|DP-420)\b")

# phrase (as it would literally appear near a cert code) -> the status it implies
CERT_STATUS_WORDS: dict[str, str] = {
    "certified": "certified",
    "passed": "certified",
    "in progress": "in_progress",
    "not pursuing": "not_pursuing",
    "retired": "not_pursuing",
}

# (pattern with one capture group for the claimed number, expected-value lookup key, label)
COUNT_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"github copilot[^\n.]{0,30}?(\d+)\s*(?:dedicated\s*)?courses?", re.I),
        "github_copilot",
        "GitHub Copilot course count",
    ),
    (
        re.compile(r"leadership[^\n.]{0,40}?(\d+)\+?\s*(?:dedicated\s*)?courses?", re.I),
        "leadership",
        "leadership/communication course count",
    ),
    (
        re.compile(r"azure functions[^\n.]{0,30}?\((\d+)\s*completed\s*courses?\)", re.I),
        "azure_functions",
        "Azure Functions course count",
    ),
]


class Finding:
    def __init__(self, path: Path, line_no: int, line: str, message: str) -> None:
        self.path = path
        self.line_no = line_no
        self.line = line.strip()
        self.message = message


def _skill_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for project in (
        "project-1-application-engine",
        "project-2-profile-learning-hub",
        "project-3-presence-identity",
    ):
        skills_dir = root / project / "skills"
        if skills_dir.exists():
            files.extend(sorted(skills_dir.glob("*/SKILL.md")))
    return files


def _cert_statuses(sources: Any) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for entry in sources.profile_facts.get("certs", []) or []:
        if isinstance(entry, dict) and entry.get("code"):
            statuses[str(entry["code"])] = str(entry.get("status", ""))
    return statuses


def _differentiator_count(sources: Any, label_pattern: str) -> int | None:
    for item in sources.profile_facts.get("differentiators", []):
        match = re.search(label_pattern, item, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def _azure_functions_course_count(root: Path) -> int | None:
    path = root / "project-2-profile-learning-hub" / "pluralsight-courses.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"\[[^\]]*Azure Functions[^\]]*\]", text, re.IGNORECASE))


def _expected_counts(root: Path, sources: Any) -> dict[str, int | None]:
    return {
        "github_copilot": _differentiator_count(sources, r"GitHub Copilot:\s*(\d+)\s*courses"),
        "leadership": _differentiator_count(
            sources, r"Communication:\s*(\d+)\s*leadership/communication"
        ),
        "azure_functions": _azure_functions_course_count(root),
    }


_HEADING_RE = re.compile(r"^#{1,3}\s+(.*)$")
# Sections/callouts describing a hypothetical future/conditional state (e.g.
# "what to change once AI-200 is passed") aren't current-fact assertions —
# skip them, whether they're a whole H2/H3 section or an inline blockquote.
_CONDITIONAL_MARKER_RE = re.compile(
    r"post-exam|after passing|after accepting|once (certified|passed)", re.I
)


def _conditional_line_numbers(text: str) -> set[int]:
    """Line numbers to skip: inside a conditional section, or in a blockquote
    run that contains a conditional marker anywhere in the run."""
    lines = text.splitlines()
    skip: set[int] = set()

    in_conditional_section = False
    for line_no, line in enumerate(lines, start=1):
        heading_match = _HEADING_RE.match(line.strip())
        if heading_match:
            in_conditional_section = bool(_CONDITIONAL_MARKER_RE.search(heading_match.group(1)))
        if in_conditional_section:
            skip.add(line_no)

    block: list[int] = []
    for line_no, line in enumerate(lines, start=1):
        if line.strip().startswith(">"):
            block.append(line_no)
            continue
        if block:
            block_text = "\n".join(lines[n - 1] for n in block)
            if _CONDITIONAL_MARKER_RE.search(block_text):
                skip.update(block)
            block = []
    if block:
        block_text = "\n".join(lines[n - 1] for n in block)
        if _CONDITIONAL_MARKER_RE.search(block_text):
            skip.update(block)

    return skip


def check_cert_status_claims(path: Path, text: str, cert_statuses: dict[str, str]) -> list[Finding]:
    """Flag a cert code followed by a status word that contradicts its real status.

    The status window for a cert code is cut off at the next cert-code mention
    on the same line, so "AZ-900 certified; AI-200 in progress" doesn't let
    AI-200's "in progress" bleed into AZ-900's window (and vice versa). Lines
    inside a conditional/post-exam-checklist section or blockquote callout are
    skipped entirely — they describe a future state, not an assertion of
    current fact.
    """
    findings: list[Finding] = []
    conditional_lines = _conditional_line_numbers(text)
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no in conditional_lines:
            continue
        code_matches = list(CERT_CODE_RE.finditer(line))
        for i, code_match in enumerate(code_matches):
            code = code_match.group(1)
            actual = cert_statuses.get(code)
            if actual is None:
                continue
            next_code_start = (
                code_matches[i + 1].start() if i + 1 < len(code_matches) else len(line)
            )
            window_end = min(code_match.end() + 40, next_code_start)
            window = line[code_match.end() : window_end].lower()
            for phrase, implied_status in CERT_STATUS_WORDS.items():
                if phrase in window and implied_status != actual:
                    findings.append(
                        Finding(
                            path,
                            line_no,
                            line,
                            f"{code} stated as {phrase!r} but profile-facts.md status is "
                            f"{actual!r}",
                        )
                    )
    return findings


def check_course_count_claims(
    path: Path, text: str, expected: dict[str, int | None]
) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for pattern, key, label in COUNT_PATTERNS:
            expected_value = expected.get(key)
            if expected_value is None:
                continue
            for match in pattern.finditer(line):
                found = int(match.group(1))
                if found != expected_value:
                    findings.append(
                        Finding(
                            path,
                            line_no,
                            line,
                            f"{label} stated as {found} but current source value is "
                            f"{expected_value}",
                        )
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]).resolve() if argv else ROOT
    sources = load_sources(root)
    cert_statuses = _cert_statuses(sources)
    expected_counts = _expected_counts(root, sources)

    all_findings: list[Finding] = []
    for path in _skill_files(root):
        text = path.read_text(encoding="utf-8")
        all_findings.extend(check_cert_status_claims(path, text, cert_statuses))
        all_findings.extend(check_course_count_claims(path, text, expected_counts))

    if not all_findings:
        print("No hardcoded-fact drift detected.")
        return 0

    for finding in all_findings:
        rel = finding.path.relative_to(root)
        print(f"[STALE] {rel}:{finding.line_no}")
        print(f"        {finding.message}")
        print(f"        > {finding.line}")

    print(
        f"\n{len(all_findings)} finding(s) — heuristic, not authoritative; "
        "read each one before editing."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
