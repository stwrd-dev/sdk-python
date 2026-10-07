"""The security policy ships with the source distribution and the public
repository, names no e-mail address (reports go through GitHub's private
vulnerability reporting) and is linked from the README."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
POLICY_URL = "https://github.com/stwrd-dev/sdk-python/security/policy"


def _policy() -> str:
    path = PACKAGE_ROOT / "SECURITY.md"
    assert path.is_file(), "SECURITY.md is missing"
    return path.read_text(encoding="utf-8")


def test_policy_names_no_email_address() -> None:
    policy = _policy()
    assert "@" not in policy
    assert not re.search(r"[\w.+-]+\s*(?:\(at\)|\[at\])\s*[\w-]+\.\w+", policy, re.IGNORECASE)


def test_policy_states_the_reporting_terms() -> None:
    policy = _policy()
    assert "Report a vulnerability" in policy
    assert "https://github.com/stwrd-dev/sdk-python" in policy
    assert "5 business days" in policy
    assert "90 days" in policy
    assert "latest minor release" in policy


def test_readme_links_to_the_policy() -> None:
    readme = (PACKAGE_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"]({POLICY_URL})" in readme


def test_policy_is_in_the_sdist_and_not_in_the_wheel() -> None:
    build = tomllib.loads((PACKAGE_ROOT / "pyproject.toml").read_text())["tool"]["hatch"]["build"]
    assert "/SECURITY.md" in build["targets"]["sdist"]["include"]
    # The wheel is an explicit package list: only `stwrd/` goes in.
    assert build["targets"]["wheel"]["packages"] == ["stwrd"]
