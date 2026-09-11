"""Shared CLI helpers for project-1 generator scripts."""

from __future__ import annotations

from pathlib import Path


def require_path(path: Path, label: str = "File") -> Path:
    """Return ``path`` if it exists, otherwise raise FileNotFoundError."""
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path
