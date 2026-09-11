"""Stdlib smoke tests for project-2-profile-learning-hub/pdf-template.py."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "project-2-profile-learning-hub" / "pdf-template.py"
_spec = importlib.util.spec_from_file_location("pdf_template", _SCRIPT)
assert _spec is not None and _spec.loader is not None
pdf_template = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pdf_template)
pdf_template_main = pdf_template.main


class PdfTemplateSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="pdf-template-smoke-"))
        self.example = (
            Path(__file__).resolve().parents[1]
            / "project-2-profile-learning-hub"
            / "roles"
            / "_example.json"
        )
        self.assertTrue(self.example.exists(), "roles/_example.json fixture missing")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_config(self) -> Path:
        cfg = json.loads(self.example.read_text(encoding="utf-8"))
        cfg["output"] = str(self.tmp / "smoke.pdf")
        cfg_path = self.tmp / "smoke.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
        return cfg_path

    def test_builds_pdf_from_example_role(self) -> None:
        cfg_path = self._make_config()
        rc = pdf_template_main([str(cfg_path)])
        self.assertEqual(rc, 0)
        out = Path(cfg_path).parent / "smoke.pdf"
        self.assertTrue(out.exists(), "PDF output file was not created")
        self.assertGreater(out.stat().st_size, 0, "PDF output file is empty")

    def test_missing_config_file_returns_nonzero(self) -> None:
        rc = pdf_template_main([str(self.tmp / "does-not-exist.json")])
        self.assertEqual(rc, 1)

    def test_invalid_json_returns_nonzero(self) -> None:
        bad_path = self.tmp / "bad.json"
        bad_path.write_text("not json", encoding="utf-8")
        rc = pdf_template_main([str(bad_path)])
        self.assertEqual(rc, 1)

    def test_empty_plan_returns_nonzero(self) -> None:
        cfg = json.loads(self.example.read_text(encoding="utf-8"))
        cfg["output"] = str(self.tmp / "empty-plan.pdf")
        cfg["plan"] = []
        cfg_path = self.tmp / "empty-plan.json"
        cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
        rc = pdf_template_main([str(cfg_path)])
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
