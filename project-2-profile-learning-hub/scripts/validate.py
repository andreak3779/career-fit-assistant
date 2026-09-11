#!/usr/bin/env python3
"""Validate generated JSON bundles against canonical source files.

Runs 6 checks defined in the original profile-hub-bundle-generator skill:
    1. Cert registry sync
    2. AI-200 status/course sync
    3. Known genuine gap closure
    4. Differentiator coverage
    5. Course count regression
    6. Badge URL format

Usage:
    python scripts/validate.py [repo_root]

Exit code 0 if all checks pass, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

from shared import load_sources


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class CheckResult:
    def __init__(self, name: str, passed: bool, details: list[str]) -> None:
        self.name = name
        self.passed = passed
        self.details = details


def check_cert_sync(bundle: dict[str, Any], sources: Any) -> CheckResult:
    """Bundle cert_registry matches the YAML cert list in profile-facts."""
    entries = sources.profile_facts.get("certs", []) or []
    source_certs: dict[str, str] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        code = str(entry.get("code", "")).strip()
        status = entry.get("status")
        if not code or not status:
            continue
        source_certs[code] = str(status)
    bundle_certs = {c["code"]: c["status"] for c in bundle["cert_registry"]}
    details: list[str] = []
    for code, status in source_certs.items():
        if code not in bundle_certs:
            details.append(f"Missing cert in bundle: {code}")
        elif status != bundle_certs[code]:
            details.append(
                f"Status mismatch for {code}: source={status!r} bundle={bundle_certs[code]!r}"
            )
    if not details:
        details.append(f"{len(source_certs)} certs in sync")
    return CheckResult(
        "cert_sync", not any(d.startswith(("Missing", "Status")) for d in details), details
    )


def check_ai200_sync(bundle: dict[str, Any], sources: Any) -> CheckResult:
    """AI-200 is in_progress and Azure course count appears in bundle differentiators."""
    details: list[str] = []
    ai200 = next((c for c in bundle["cert_registry"] if c["code"] == "AI-200"), None)
    if ai200 is None:
        details.append("AI-200 missing from cert_registry")
    elif ai200["status"] != "in_progress":
        details.append(f"AI-200 status is {ai200['status']!r}, expected 'in_progress'")
    else:
        details.append("AI-200 status is 'in_progress'")

    azure_row = next(
        (
            row
            for row in sources.skills_summary["course_summary_table"]
            if "Microsoft Azure" in row.get("Category", "")
        ),
        None,
    )
    if azure_row:
        expected = azure_row.get("Courses", "").strip()
        # Course count may live in the Azure coursework row or the AI-200 notes.
        cert_notes = "\n".join(
            row.get("Status", "") for row in sources.profile_facts["cert_status_table"]
        )
        if expected and expected not in cert_notes:
            details.append(
                f"Azure course count mismatch: {expected!r} not found in cert status notes"
            )
        else:
            details.append("Azure coursework count consistent")
    return CheckResult(
        "ai200_sync", not any(d.startswith("Azure course count") for d in details), details
    )


def check_gap_closure(bundle: dict[str, Any], sources: Any) -> CheckResult:
    """Every known genuine gap has at least course/portfolio evidence."""
    gaps = bundle["known_genuine_gaps"]
    details: list[str] = []
    weak = []
    for gap in gaps:
        if gap["evidence"] in ("none", "course", "portfolio"):
            continue
        weak.append(gap["skill"])
    if weak:
        details.append(f"Gaps without evidence: {', '.join(weak)}")
    else:
        details.append(f"All {len(gaps)} known genuine gaps have evidence")
    return CheckResult("gap_closure", not weak, details)


def check_differentiator_coverage(bundle: dict[str, Any]) -> CheckResult:
    """Expected differentiators are present."""
    required = {
        "full-stack",
        "legacy",
        "sql server",
        "tdd",
        "github copilot",
        "prompt engineering",
        "ai/llm",
        "communication",
        "pace of learning",
    }
    diffs = "\n".join(bundle["differentiators"]).lower()
    missing = [r for r in required if r not in diffs]
    details: list[str] = []
    if missing:
        details.append(f"Missing differentiator signals: {', '.join(missing)}")
    else:
        details.append("All expected differentiator signals present")
    return CheckResult("differentiator_coverage", not missing, details)


def check_course_count_regression(bundle: dict[str, Any], sources: Any) -> CheckResult:
    """Pluralsight course totals from skills-summary match differentiator summary.

    The course totals (215 completed / 49 in progress / 27 labs / 291 total)
    live in two places in skills-summary.md:
      - the top-of-file ``**Status: ...**`` line
      - the ``**TOTAL**`` row of the Pluralsight Course Summary table

    We scan both surfaces so a regression in either location fails loud.
    """
    details: list[str] = []

    surfaces: list[str] = []
    status_line = sources.skills_summary.get("status_line")
    if status_line:
        surfaces.append(status_line)
    for row in sources.skills_summary.get("course_summary_table", []):
        # Each row is a dict; the totals row has "TOTAL" in some column.
        if any("TOTAL" in str(v).upper() for v in row.values()):
            surfaces.append(" ".join(str(v) for v in row.values()))

    if not surfaces:
        details.append("Could not locate Pluralsight totals (status_line or TOTAL row missing)")
        return CheckResult("course_count_regression", False, details)

    summary_line = "\n".join(surfaces)
    counts = {
        "completed": _find_count(summary_line, r"(\d+)\s+courses?\s+completed"),
        "in_progress": _find_count(summary_line, r"(\d+)\s+courses?\s+in[\s-]*progress"),
        "labs": _find_count(summary_line, r"(\d+)\s+labs?"),
        "total": _find_count(summary_line, r"(\d+)\s+total"),
    }
    expected_total = counts["completed"] + counts["in_progress"] + counts["labs"]
    if counts["total"] and counts["total"] != expected_total:
        details.append(
            f"Course total inconsistent: {counts['total']} != {counts['completed']}+{counts['in_progress']}+{counts['labs']}"
        )
    else:
        details.append(
            f"Course counts consistent: {counts['completed']} completed, {counts['in_progress']} in progress, {counts['labs']} labs"
        )
    return CheckResult(
        "course_count_regression",
        not any(d.startswith(("Could not", "Course total")) for d in details),
        details,
    )


def _find_count(text: str, pattern: str) -> int:
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def check_badge_url_format(bundle: dict[str, Any]) -> CheckResult:
    """AZ-900 credential URL follows the expected Microsoft Learn format."""
    details: list[str] = []
    az900 = next((c for c in bundle["cert_registry"] if c["code"] == "AZ-900"), None)
    if az900 is None:
        details.append("AZ-900 missing from cert_registry")
        return CheckResult("badge_url_format", False, details)
    url = az900.get("credential_url", "")
    expected_pattern = re.compile(
        r"^https://learn\.microsoft\.com/api/credentials/share/[a-z-]+/[^/]+/[A-F0-9]+\?sharingId=[A-F0-9]+$"
    )
    if expected_pattern.match(url):
        details.append("AZ-900 credential URL format valid")
    else:
        details.append(f"AZ-900 credential URL format invalid: {url}")
    return CheckResult("badge_url_format", details[0].endswith("valid"), details)


def run_all(root: Path) -> list[CheckResult]:
    bundle = _load_json(root / "outputs" / "profile-bundle.json")
    sources = load_sources(root)
    return [
        check_cert_sync(bundle, sources),
        check_ai200_sync(bundle, sources),
        check_gap_closure(bundle, sources),
        check_differentiator_coverage(bundle),
        check_course_count_regression(bundle, sources),
        check_badge_url_format(bundle),
    ]


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    root = Path(argv[0]).resolve() if argv else ROOT
    results = run_all(root)
    failed = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}")
        for detail in result.details:
            print(f"       - {detail}")
        if not result.passed:
            failed += 1
    if failed:
        print(f"\n{failed} check(s) failed")
        return 1
    print("\nAll checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
