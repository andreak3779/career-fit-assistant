import pytest

from shared.pii_guard import (
    PIIViolation,
    assert_presence_safe,
    scan_structure,
    scan_text,
)


def test_scan_text_finds_email_and_phone():
    findings = scan_text("Contact me at foo@example.com or 204-555-0100")
    types = {f["type"] for f in findings}
    assert {"email", "phone"} <= types


def test_scan_structure_finds_sensitive_keys():
    data = {
        "email": "foo@example.com",
        "nested": {"phone": "204-555-0100"},
        "safe": "Python developer",
    }
    findings = scan_structure(data)
    paths = {f["source"] for f in findings}
    assert "email" in paths
    assert "nested.phone" in paths


def test_assert_presence_safe_raises_for_pii():
    with pytest.raises(PIIViolation):
        assert_presence_safe({"summary": "email me at foo@example.com"})


def test_assert_presence_safe_accepts_clean_bundle():
    assert_presence_safe(
        {
            "headline": "Senior Dev",
            "summary": "I build cloud apps",
            "technical_skills": {"backend": ["C#"]},
        }
    )


def test_scan_text_does_not_match_iso_date_segments():
    """Regression: phone regex must not flag digit runs inside ISO dates."""
    findings = scan_text("incident happened on 2026-04-18 at 13:45")
    assert findings == []


def test_scan_text_still_matches_real_phone():
    """The tightened regex must keep flagging genuine phone numbers."""
    findings = scan_text("Call me at 204-555-0100 anytime")
    types = {f["type"] for f in findings}
    assert "phone" in types
