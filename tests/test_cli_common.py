"""Tests for project-1-application-engine/scripts/_cli_common.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from project_1_application_engine.scripts._cli_common import load_bundle_or_none, require_path

from tests.test_bundle_loader import _minimal_presence_bundle, _minimal_profile_bundle


def test_require_path_returns_path_when_it_exists(tmp_path: Path) -> None:
    f = tmp_path / "x.txt"
    f.write_text("hi", encoding="utf-8")
    assert require_path(f, "File") == f


def test_require_path_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        require_path(tmp_path / "does-not-exist.txt", "File")


def test_load_bundle_or_none_returns_bundle_for_valid_data(tmp_path: Path) -> None:
    (tmp_path / "outputs").mkdir()
    (tmp_path / "outputs" / "profile-bundle.json").write_text(
        json.dumps(_minimal_profile_bundle()), encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("# x", encoding="utf-8")
    (tmp_path / "outputs" / "presence-bundle.json").write_text(
        json.dumps(_minimal_presence_bundle()), encoding="utf-8"
    )

    bundle = load_bundle_or_none(tmp_path)

    assert bundle is not None
    assert bundle.bundle_version == 1


def test_load_bundle_or_none_returns_none_for_missing_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = load_bundle_or_none(tmp_path / "no-such-root")
    assert result is None
    err = capsys.readouterr().err
    assert "ERROR" in err
    assert "generate bundles" in err


def test_load_bundle_or_none_returns_none_for_corrupted_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "profile-bundle.json").write_text("{not valid json", encoding="utf-8")

    result = load_bundle_or_none(tmp_path)

    assert result is None
    err = capsys.readouterr().err
    assert "ERROR" in err
    assert "invalid" in err
