"""The distribution and the import are both `stwrd`."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def test_distribution_name_is_stwrd() -> None:
    project = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text())
    assert project["project"]["name"] == "stwrd"


def test_import_name_is_stwrd() -> None:
    project = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text())
    assert project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["stwrd"]
    stwrd = importlib.import_module("stwrd")
    assert hasattr(stwrd, "Stwrd")


def test_readme_says_install_name_and_import_name() -> None:
    readme = (PACKAGE_ROOT / "README.md").read_text()
    assert "installed as `stwrd` and imported as `stwrd`" in readme
