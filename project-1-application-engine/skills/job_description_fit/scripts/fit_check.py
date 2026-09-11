#!/usr/bin/env python3
"""Print an inline fit table for a job description."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

from project_1_application_engine.scripts._cli_common import require_path

from shared import load_profile_bundle, parse_jd, rate_fit, render_fit_table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fit-check", description="Inline fit check for a job description"
    )
    parser.add_argument("jd", type=Path, help="Path to job description markdown file")
    parser.add_argument(
        "--bundle",
        type=Path,
        help="Path to profile-bundle.json (default: outputs/profile-bundle.json)",
    )
    args = parser.parse_args(argv)

    try:
        require_path(args.jd, "JD file")
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    bundle = load_profile_bundle(args.bundle or ROOT)
    jd_text = args.jd.read_text(encoding="utf-8")
    parsed = parse_jd(jd_text)
    result = rate_fit(parsed.required, parsed.nice_to_have, bundle)

    print(f"## Fit Check — {parsed.title} at {parsed.company}\n")
    print(render_fit_table(result).replace("## Fit Check\n\n", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
