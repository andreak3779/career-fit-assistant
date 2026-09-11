"""Provenance sidecar helpers for generated artifacts."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.models import PresenceBundle, ProfileBundle


@dataclass
class Provenance:
    """Traceability metadata written alongside generated artifacts."""

    generated_at: str
    script: str
    bundle_version: int
    bundle_generated: str | None
    inputs: list[str]
    fit_rating: str | None = None
    command: str | None = None
    evidence_sources: list[str] | None = None
    warnings: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "generated_at": self.generated_at,
            "script": self.script,
            "bundle_version": self.bundle_version,
            "bundle_generated": self.bundle_generated,
            "inputs": self.inputs,
            "fit_rating": self.fit_rating,
            "command": self.command,
        }
        if self.evidence_sources is not None:
            result["evidence_sources"] = self.evidence_sources
        if self.warnings is not None:
            result["warnings"] = self.warnings
        return result


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def write_sidecar(
    artifact_path: Path,
    *,
    script: str,
    bundle: ProfileBundle | PresenceBundle,
    inputs: list[str],
    fit_rating: str | None = None,
    command: str | None = None,
    evidence_sources: list[str] | None = None,
    warnings: list[str] | None = None,
) -> Path:
    """Write ``<artifact>.meta.json`` next to the artifact it describes.

    The ``command`` argument defaults to ``sys.argv`` so callers don't have to
    plumb it manually; pass an explicit value to override.
    """
    if command is None:
        command = " ".join(sys.argv)
    sidecar = artifact_path.parent / (artifact_path.name + ".meta.json")
    prov = Provenance(
        generated_at=now_iso(),
        script=script,
        bundle_version=bundle.bundle_version,
        bundle_generated=_serialize_value(bundle.generated),
        inputs=list(inputs),
        fit_rating=fit_rating,
        command=command,
        evidence_sources=evidence_sources,
        warnings=warnings,
    )
    sidecar.write_text(json.dumps(prov.to_dict(), indent=2) + "\n", encoding="utf-8")
    return sidecar
