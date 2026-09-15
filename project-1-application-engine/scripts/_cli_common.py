"""Shared CLI helpers for project-1 generator scripts."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from shared import load_profile_bundle
from shared.bundle_loader import BundleSchemaError

if TYPE_CHECKING:
    from shared.models import ProfileBundle


def require_path(path: Path, label: str = "File") -> Path:
    """Return ``path`` if it exists, otherwise raise FileNotFoundError."""
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def load_bundle_or_none(root: Path) -> ProfileBundle | None:
    """Load the profile bundle, printing a clean ERROR and returning ``None``
    on failure instead of letting a missing/unbuilt/corrupted
    outputs/profile-bundle.json crash the caller with a raw traceback.

    Every CLI script's ``main()`` needs the exact same behavior here — a
    fresh checkout (or a build that silently failed) means this file simply
    doesn't exist yet, and that's an ordinary, expected failure mode, not a
    bug. Callers: ``bundle = load_bundle_or_none(root); if bundle is None:
    return 1``.
    """
    try:
        return load_profile_bundle(root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Run 'generate bundles' (python -m cli.career_fit_api build) first.", file=sys.stderr)
        return None
    except (json.JSONDecodeError, BundleSchemaError) as exc:
        print(f"ERROR: profile-bundle.json is invalid: {exc}", file=sys.stderr)
        return None


def print_wrote(*paths: Path) -> None:
    """Print "Wrote <path>" for each output artifact, in order."""
    for p in paths:
        print(f"Wrote {p}")


def run_and_report(fn: Callable[..., tuple[Path, Path, Any]], *args: Any, **kwargs: Any) -> int:
    """Call a generator function that returns (out_path, sidecar_path, ...),
    catch ValueError as a clean ERROR + exit 1 (the one exception class core
    generator functions in this project use for expected validation
    failures — e.g. interview_prep's missing qa_cards fields, thank-you's
    missing discussion points), and print the standard "Wrote" lines on
    success. Extra tuple elements beyond (out_path, sidecar_path) are
    ignored.
    """
    try:
        result = fn(*args, **kwargs)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    out, sidecar = result[0], result[1]
    print_wrote(out, sidecar)
    return 0
