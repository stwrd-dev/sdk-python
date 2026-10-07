"""The distribution is `stwrd-auth` (what `pip install` takes); the import stays `stwrd`.

PyPI project names are first come, first served: `stwrd` was taken, so the package
installs as `stwrd-auth` and imports as `stwrd`. Nothing may tell a reader to
`pip install stwrd` (that installs somebody else's package).
"""

from __future__ import annotations

import importlib
import re
import tomllib
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

# Installing the bare `stwrd` name: `pip install stwrd`, `uv add "stwrd[fastapi]"`,
# `stwrd>=1`, ... but not `stwrd-auth`, `stwrd_idp` or an import line.
BARE_INSTALL = re.compile(
    r"""(?:pip install|uv add|uv pip install)\s+(?:-\S+\s+)*["']?stwrd(?![\w-])"""
)


def test_distribution_name_is_stwrd_auth() -> None:
    project = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text())
    assert project["project"]["name"] == "stwrd-auth"


def test_import_name_is_still_stwrd() -> None:
    project = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text())
    assert project["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["stwrd"]
    stwrd = importlib.import_module("stwrd")
    assert hasattr(stwrd, "Stwrd")


def _docs() -> list[Path]:
    return [
        PACKAGE_ROOT / "README.md",
        PACKAGE_ROOT / "CHANGELOG.md",
        *(PACKAGE_ROOT / "docs").glob("*.md"),
    ]


@pytest.mark.parametrize("doc", _docs(), ids=lambda p: p.name)
def test_docs_install_stwrd_auth(doc: Path) -> None:
    hits = [line for line in doc.read_text().splitlines() if BARE_INSTALL.search(line)]
    assert hits == []


@pytest.mark.parametrize(
    "line,bare",
    [
        ("pip install stwrd", True),
        ('pip install "stwrd[fastapi]"', True),
        ('uv add "stwrd[fastapi]"', True),
        ("uv pip install -q stwrd", True),
        ('pip install "stwrd-auth[fastapi]"', False),
        ("uv add stwrd-auth", False),
        ("pip install stwrd_idp", False),
        ("import stwrd", False),
    ],
)
def test_the_sweep_tells_the_bare_name_from_the_distribution(line: str, bare: bool) -> None:
    assert bool(BARE_INSTALL.search(line)) is bare


def test_readme_says_install_name_and_import_name() -> None:
    readme = (PACKAGE_ROOT / "README.md").read_text()
    assert "installed as `stwrd-auth` and imported as `stwrd`" in readme
