"""Without a reachable PostgreSQL the store tests are skipped, unless
STWRD_REQUIRE_DB=1, in which case they fail so CI cannot skip them silently."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
# Port 1 is never listening: the connection is refused at once.
UNREACHABLE_URL = "postgresql+psycopg://stwrd:stwrd@127.0.0.1:1/stwrd_test"


def _run_store_tests(**env: str) -> subprocess.CompletedProcess[str]:
    child_env = {k: v for k, v in os.environ.items() if k != "STWRD_REQUIRE_DB"}
    child_env.update(STWRD_TEST_DB_URL=UNREACHABLE_URL, **env)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_postgres_store.py", "-q", "-rs"],
        cwd=PACKAGE_ROOT,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_without_a_database_the_postgres_tests_are_skipped_with_a_reason():
    result = _run_store_tests()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PostgreSQL is not reachable at 127.0.0.1:1" in result.stdout
    assert "set STWRD_TEST_DB_URL to run these tests" in result.stdout
    assert "skipped" in result.stdout
    assert "error" not in result.stdout.splitlines()[-1]


def test_requiring_the_database_turns_the_skip_into_a_failure():
    result = _run_store_tests(STWRD_REQUIRE_DB="1")
    assert result.returncode != 0, result.stdout + result.stderr
    assert "PostgreSQL is not reachable at 127.0.0.1:1" in result.stdout
    assert "STWRD_REQUIRE_DB=1" in result.stdout
    assert "skipped" not in result.stdout.splitlines()[-1]
