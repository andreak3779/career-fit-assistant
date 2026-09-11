"""Tests for project-1-application-engine/scripts/extract_bundle_sections.py.

The module lives under scripts/, outside the installed package tree, so it's
loaded by file path (same pattern as the project-2 script tests). All tests
point --root at a tmp_path fixture bundle — never at the real (gitignored)
app-engine-bundle.md.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = ROOT / "project-1-application-engine" / "scripts" / "extract_bundle_sections.py"

_FIXTURE_BUNDLE = """<!-- GENERATED FILE — do not hand-edit. -->
# App Engine Bundle — Test User
bundle_version: 1
generated: 2026-08-25

---
## Copy Fragments
course_count_sentence: "10 courses completed"

---
## Cert Registry
| Cert | Status |
|---|---|
| AZ-900 | Certified |

---
## Key Differentiators
Surface these when the JD references them:
- Full-stack depth: ASP.NET Core + Angular

---
## Known Genuine Gaps
- Kubernetes — course-level

---
## Resume
# Test User

**Senior Dev | .NET**

---

**Contact Information**

- Email: test@example.com
- Phone: 555-1212
- LinkedIn: https://linkedin.com/in/test
---

---
## Summary

Senior dev with experience.

---
## Key Differentiators

- **Legacy Modernization:** resume-bullet version, not the facts one
"""


def _load_module():
    spec = importlib.util.spec_from_file_location("extract_bundle_sections", _MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def x():
    return _load_module()


@pytest.fixture
def fixture_root(tmp_path):
    p1 = tmp_path / "project-1-application-engine"
    p1.mkdir(parents=True)
    (p1 / "app-engine-bundle.md").write_text(_FIXTURE_BUNDLE, encoding="utf-8")
    return tmp_path


def test_facts_stops_before_resume_heading(x, fixture_root, capsys):
    rc = x.cmd_facts(fixture_root, "project-1-application-engine", "app-engine-bundle.md")
    assert rc == 0
    out = capsys.readouterr().out
    assert "Cert Registry" in out
    assert "Known Genuine Gaps" in out
    assert "## Resume" not in out
    assert "Contact Information" not in out
    assert "Senior dev with experience" not in out


def test_section_returns_named_heading_only(x, fixture_root, capsys):
    rc = x.cmd_section(
        fixture_root, "project-1-application-engine", "app-engine-bundle.md", ["Cert Registry"]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "AZ-900" in out
    assert "Copy Fragments" not in out
    assert "Known Genuine Gaps" not in out


def test_section_matches_first_occurrence_of_duplicate_heading(x, fixture_root, capsys):
    rc = x.cmd_section(
        fixture_root,
        "project-1-application-engine",
        "app-engine-bundle.md",
        ["Key Differentiators"],
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "Full-stack depth" in out  # the facts-section version
    assert "Legacy Modernization" not in out  # the resume-bullet version, must NOT appear


def test_section_multiple_names_in_one_call(x, fixture_root, capsys):
    rc = x.cmd_section(
        fixture_root,
        "project-1-application-engine",
        "app-engine-bundle.md",
        ["Cert Registry", "Known Genuine Gaps"],
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "AZ-900" in out
    assert "Kubernetes" in out


def test_section_not_found(x, fixture_root, capsys):
    rc = x.cmd_section(
        fixture_root,
        "project-1-application-engine",
        "app-engine-bundle.md",
        ["Nonexistent Section"],
    )
    assert rc == 1
    assert "SECTION NOT FOUND" in capsys.readouterr().out


def test_contact_extracts_only_the_contact_block(x, fixture_root, capsys):
    rc = x.cmd_contact(fixture_root, "project-1-application-engine", "app-engine-bundle.md")
    assert rc == 0
    out = capsys.readouterr().out
    assert "test@example.com" in out
    assert "555-1212" in out
    assert "Summary" not in out
    assert "Senior dev with experience" not in out


def test_main_missing_bundle_returns_nonzero(x, tmp_path, capsys):
    rc = x.main(["--root", str(tmp_path), "facts"])
    assert rc == 1
    assert "ERROR" in capsys.readouterr().err


def test_project_flag_routes_to_a_different_project_dir(x, tmp_path, capsys):
    p3 = tmp_path / "project-3-presence-identity"
    p3.mkdir(parents=True)
    (p3 / "presence-bundle.md").write_text(
        '## Copy Fragments\ncert_status_short: "AZ-900 Certified"\n\n---\n'
        "## Cert Status + Badge URLs\n| AZ-900 | Certified |\n",
        encoding="utf-8",
    )
    rc = x.main(
        [
            "--root",
            str(tmp_path),
            "--project",
            "project-3-presence-identity",
            "--file",
            "presence-bundle.md",
            "section",
            "Copy Fragments",
        ]
    )
    assert rc == 0
    assert "cert_status_short" in capsys.readouterr().out


def test_project_flag_default_still_targets_project_1(x, fixture_root, capsys):
    rc = x.main(["--root", str(fixture_root), "facts"])
    assert rc == 0
    assert "Cert Registry" in capsys.readouterr().out
