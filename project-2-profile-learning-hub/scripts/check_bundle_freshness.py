#!/usr/bin/env python3
"""Check whether generated bundles are current relative to their Project 2 sources.

Neither `app-engine-bundle.md` (Project 1, gitignored — regenerated locally)
nor `presence-bundle.md` (Project 3, committed) carries any signal that says
"a Project 2 source changed after I was written." This script closes that gap
by comparing each bundle file's own mtime against the mtime of the four
Project 2 files build_bundles.py reads (`profile-facts.md`,
`Resume_Snapshot.md`, `skills-summary.md`, `github-repos.md`) — the same set
already recorded as `sources` inside `outputs/profile-bundle.json`. If any
source was modified more recently than the bundle file itself, the bundle is
stale and needs regenerating via the profile-hub-bundle-generator skill
("generate bundles").

Mtime-based, deliberately: comparing a bundle's own file mtime against its
sources' mtimes is stable across a fresh `git clone` (checkout stamps every
file — bundle and sources alike — with the same moment, so nothing looks
falsely stale), unlike comparing against a parsed `generated:` date, which
would flag every source as newer than a bundle generated on a different day
or machine. It does NOT need git history and works identically for the
gitignored app-engine-bundle.md and the tracked presence-bundle.md.

This is advisory/heuristic like check_skill_hardcoding.py, not a bundle-content
gate like validate.py's 6 checks: it only tells you *a source changed since
the bundle was last written*, not what changed or whether it matters.

Usage:
    python scripts/check_bundle_freshness.py [repo_root]

Exit code 0 if all present bundles are fresh (a bundle that hasn't been
generated locally yet is skipped, not treated as a failure), 1 if any
present bundle is stale.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCE_FILES = [
    "profile-facts.md",
    "Resume_Snapshot.md",
    "skills-summary.md",
    "github-repos.md",
]

BUNDLES = [
    ("project-1-application-engine/app-engine-bundle.md", "app-engine-bundle.md (Project 1)"),
    ("project-3-presence-identity/presence-bundle.md", "presence-bundle.md (Project 3)"),
]


class FreshnessResult:
    def __init__(self, label: str, status: str, details: list[str]) -> None:
        self.label = label
        self.status = status  # "FRESH" | "STALE" | "SKIP"
        self.details = details


def _fmt(mtime: float) -> str:
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")


def check_bundle_freshness(root: Path, rel_path: str, label: str) -> FreshnessResult:
    bundle_path = root / rel_path
    if not bundle_path.exists():
        return FreshnessResult(
            label, "SKIP", [f"{rel_path} not generated locally — nothing to check"]
        )

    bundle_mtime = bundle_path.stat().st_mtime
    stale: list[str] = []
    for name in SOURCE_FILES:
        source_path = root / "project-2-profile-learning-hub" / name
        if not source_path.exists():
            continue
        source_mtime = source_path.stat().st_mtime
        if source_mtime > bundle_mtime:
            stale.append(
                f"{name} (edited {_fmt(source_mtime)}, bundle last written {_fmt(bundle_mtime)})"
            )

    if stale:
        return FreshnessResult(
            label,
            "STALE",
            [f"newer than bundle: {s}" for s in stale]
            + ['run the profile-hub-bundle-generator skill ("generate bundles") to refresh'],
        )
    return FreshnessResult(label, "FRESH", [f"last written {_fmt(bundle_mtime)}, no source newer"])


def run_all(root: Path) -> list[FreshnessResult]:
    return [check_bundle_freshness(root, rel_path, label) for rel_path, label in BUNDLES]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    root = Path(argv[0]).resolve() if argv else ROOT
    results = run_all(root)
    failed = 0
    for result in results:
        print(f"[{result.status}] {result.label}")
        for detail in result.details:
            print(f"       - {detail}")
        if result.status == "STALE":
            failed += 1
    print()
    if failed:
        print(f"{failed} bundle(s) stale — see above")
        return 1
    print("All present bundles are fresh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
