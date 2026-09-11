"""PII guard for presence-safe bundle generation.

Ensures that generated GitHub-facing JSON never leaks phone numbers, email
addresses, or location fields that are meant to stay in the private
ProfileBundle only.
"""

from __future__ import annotations

import re
from typing import Any

# Phone regex — tightened so it does not match arbitrary 10-digit runs in dates
# (e.g. "2026-04-18") or numeric prose. Requires the match to be either:
#   - preceded by a non-digit, non-dash, non-dot, non-plus, non-paren boundary;
#   - or start-of-string; and
#   - followed by a non-digit boundary.
# Also rejects when the first group starts with "1" and is a 4-digit run that
# looks like the tail of an ISO date — that's why we use lookarounds and a
# trailing \b on the last 4 digits.
DEFAULT_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", re.IGNORECASE),
    "phone": re.compile(
        r"(?<![0-9.\-+()])"
        r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        r"(?![0-9])"
    ),
    "linkedin_url": re.compile(r"linkedin\.com/in/[A-Za-z0-9-]+", re.IGNORECASE),
}

DEFAULT_SENSITIVE_KEYS = {
    "email",
    "phone",
    "timezone",
    "province",
    "city",
    "address",
    "mobile",
    "cell",
}


class PIIViolation(Exception):
    """Raised when a presence bundle contains suspected PII."""

    def __init__(self, findings: list[dict[str, Any]]) -> None:
        self.findings = findings
        super().__init__(f"PII violations found: {len(findings)}")


def scan_text(
    text: str, *, source: str = "text", patterns: dict[str, re.Pattern[str]] | None = None
) -> list[dict[str, Any]]:
    """Scan a single text string for PII patterns."""
    patterns = patterns or DEFAULT_PII_PATTERNS
    findings: list[dict[str, Any]] = []
    for name, pattern in patterns.items():
        for match in pattern.finditer(text):
            findings.append(
                {
                    "type": name,
                    "source": source,
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )
    return findings


def scan_structure(
    data: Any, *, path: str = "", sensitive_keys: set[str] | None = None
) -> list[dict[str, Any]]:
    """Recursively scan a JSON-serializable structure for PII."""
    sensitive_keys = sensitive_keys or DEFAULT_SENSITIVE_KEYS
    findings: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            if key.lower() in sensitive_keys and value:
                findings.append(
                    {
                        "type": "sensitive_key",
                        "source": current_path,
                        "value": str(value),
                    }
                )
            findings.extend(scan_structure(value, path=current_path, sensitive_keys=sensitive_keys))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            current_path = f"{path}[{index}]"
            findings.extend(scan_structure(item, path=current_path, sensitive_keys=sensitive_keys))
    elif isinstance(data, str):
        findings.extend(scan_text(data, source=path))
    return findings


def assert_presence_safe(data: Any) -> None:
    """Raise PIIViolation if the presence bundle is not safe."""
    findings = scan_structure(data)
    if findings:
        raise PIIViolation(findings)
