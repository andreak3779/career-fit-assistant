"""Render a certification's status as the same markdown cell text the bundle
renderer puts in its "Cert Status + Badge URLs" table — split out so
consumers (LinkedIn draft generation) can derive it directly from a loaded
bundle's ``cert_registry`` instead of re-parsing that table out of rendered
markdown.
"""

from __future__ import annotations

from shared.models import Cert, CertStatus


def cert_status_short(cert_registry: list[Cert]) -> str:
    """Compact "AZ-900 Certified · AI-200 in progress" form.

    Skips NOT_PURSUING entries — they would only add noise to draft copy.
    Split out so the bundle renderer and the JSON-pipeline consumers
    (LinkedIn draft generation) agree on the exact wording.
    """
    parts: list[str] = []
    for c in cert_registry:
        if c.status == CertStatus.CERTIFIED:
            parts.append(f"{c.code} Certified")
        elif c.status == CertStatus.IN_PROGRESS:
            parts.append(f"{c.code} in progress")
    return " · ".join(parts)


def cert_status_cell(c: Cert) -> str:
    if c.status == CertStatus.CERTIFIED:
        date_str = f"{c.date:%B} {c.date.day}, {c.date.year}" if c.date else ""
        cred = f" — [Credential]({c.credential_url})" if c.credential_url else ""
        return f"**Certified {date_str}**{cred}"
    if c.status == CertStatus.IN_PROGRESS:
        return f"**Active target** — {c.notes or ''}"
    return c.notes or "Not pursuing"


def cert_status_rows(cert_registry: list[Cert]) -> list[tuple[str, str]]:
    return [(c.code, cert_status_cell(c)) for c in cert_registry]
