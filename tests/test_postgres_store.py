"""PostgreSQL store: same lease contract as MemoryStore, encrypted at rest, and
safe across real processes. Needs the test PostgreSQL (STWRD_TEST_DB_URL); without
one they are skipped, or fail when STWRD_REQUIRE_DB=1 (what CI sets)."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import textwrap
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict
from psycopg_pool import AsyncConnectionPool

from stwrd import Stwrd, StwrdSession, Tokens
from stwrd.postgres import SCHEMA_SQL, Keyring, PostgresSessionStore

# The coordination scenarios run unchanged against the shared store.
from .test_session_coordination import (  # noqa: F401
    test_a_late_owner_cannot_complete_the_refresh_of_an_uncertain_session,
    test_a_late_release_of_the_owner_never_reopens_an_uncertain_session,
    test_logout_during_refresh_cannot_resurrect_the_deleted_session,
    test_lost_response_after_rotation_never_replays_the_consumed_refresh,
    test_two_instances_exchange_a_single_use_refresh_at_most_once,
    test_userinfo_recovery_uses_checkpointed_tokens_without_another_rotation,
)

ADMIN_URL = os.environ.get(
    "STWRD_TEST_DB_URL", "postgresql+psycopg://stwrd:stwrd@localhost:55432/stwrd_test"
).replace("+psycopg", "")
KEYS = {"k1": b"1" * 32, "k2": b"2" * 32}


@pytest.fixture(scope="module")
def database_url() -> Iterator[str]:
    name = f"stwrd_sdk_pg_{uuid.uuid4().hex[:10]}"
    try:
        admin = psycopg.connect(ADMIN_URL, autocommit=True, connect_timeout=5)
    except psycopg.OperationalError as error:
        info = conninfo_to_dict(ADMIN_URL)
        reason = (
            f"PostgreSQL is not reachable at {info.get('host', 'localhost')}:"
            f"{info.get('port', 5432)} ({str(error).splitlines()[0]}); "
            "set STWRD_TEST_DB_URL to run these tests"
        )
        if os.environ.get("STWRD_REQUIRE_DB") == "1":
            pytest.fail(f"{reason} (STWRD_REQUIRE_DB=1 forbids skipping them)", pytrace=False)
        pytest.skip(reason)
    with admin:
        admin.execute(f'CREATE DATABASE "{name}"')
    base = ADMIN_URL.rsplit("/", 1)[0]
    url = f"{base}/{name}"
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute(SCHEMA_SQL)
    try:
        yield url
    finally:
        with psycopg.connect(ADMIN_URL, autocommit=True) as admin:
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture
async def pool(database_url: str) -> AsyncIterator[AsyncConnectionPool]:
    async with AsyncConnectionPool(database_url, min_size=1, max_size=8, open=False) as pool:
        yield pool


@pytest.fixture
def namespace() -> str:
    return f"tenant-{uuid.uuid4().hex}/client"


@pytest.fixture
def store(pool: AsyncConnectionPool, namespace: str) -> PostgresSessionStore:
    return PostgresSessionStore(pool, namespace=namespace, keyring=Keyring(KEYS, "k1"))


@pytest.fixture
async def stwrd(stwrd_config, idp_http_client, store) -> AsyncIterator[Stwrd]:  # noqa: F811
    instance = Stwrd(stwrd_config, http_client=idp_http_client, sessions=store)
    try:
        yield instance
    finally:
        await instance.close()


def _tokens(expires_in: float = 3600) -> Tokens:
    return Tokens(
        "access-secret", "id-secret", "Bearer", time.time() + expires_in, "refresh-secret"
    )


def _session(session_id: str = "s1") -> StwrdSession:
    return StwrdSession(
        id=session_id,
        sid_idp="sid1",
        sub="usr_1",
        claims={"sub": "usr_1", "org_id": "o", "name": "old"},
        tokens=_tokens(),
        expires_at=time.time() + 3600,
        access_expires_at=time.time() - 1,
    )


async def test_round_trip_and_tokens_are_encrypted_at_rest(store, pool, namespace):
    session = _session()
    await store.set(session)
    assert await store.get("s1") == session
    async with pool.connection() as conn:
        cursor = await conn.execute(
            "SELECT payload FROM stwrd_sdk_sessions WHERE namespace = %s", (namespace,)
        )
        (payload,) = await cursor.fetchone()
    for secret in ("access-secret", "refresh-secret", "id-secret", "usr_1"):
        assert secret not in payload
    assert payload.count(".") == 4  # compact JWE
    await store.delete("s1")
    assert await store.get("s1") is None


async def test_a_row_moved_to_another_namespace_or_id_is_not_a_session(store, pool, namespace):
    await store.set(_session("s1"))
    other = PostgresSessionStore(pool, namespace=namespace + "-other", keyring=Keyring(KEYS, "k1"))
    async with pool.connection() as conn:
        await conn.execute(
            "INSERT INTO stwrd_sdk_sessions (namespace, session_id, payload, expires_at) "
            "SELECT %s, 's1', payload, expires_at FROM stwrd_sdk_sessions "
            "WHERE namespace = %s AND session_id = 's1'",
            (namespace + "-other", namespace),
        )
        await conn.execute(
            "INSERT INTO stwrd_sdk_sessions (namespace, session_id, payload, expires_at) "
            "SELECT namespace, 'renamed', payload, expires_at FROM stwrd_sdk_sessions "
            "WHERE namespace = %s AND session_id = 's1'",
            (namespace,),
        )
    assert await other.get("s1") is None  # relocated across namespaces
    assert await store.get("renamed") is None  # relocated across ids
    assert await store.get("s1") is not None
    assert (await other.claim_refresh("s1", "x", 30)).status == "gone"


async def test_keyring_rotation_reads_old_rows_and_rejects_unknown_keys(store, pool, namespace):
    await store.set(_session())
    rotated = PostgresSessionStore(pool, namespace=namespace, keyring=Keyring(KEYS, "k2"))
    assert await rotated.get("s1") is not None  # written under k1, still readable
    await rotated.set(_session())
    dropped = PostgresSessionStore(
        pool, namespace=namespace, keyring=Keyring({"k2": KEYS["k2"]}, "k2")
    )
    assert await dropped.get("s1") is not None
    wrong = PostgresSessionStore(
        pool, namespace=namespace, keyring=Keyring({"k2": b"9" * 32}, "k2")
    )
    assert await wrong.get("s1") is None


def test_keyring_validates_its_keys():
    with pytest.raises(ValueError):
        Keyring({"k": b"short"}, "k")
    with pytest.raises(ValueError):
        Keyring(KEYS, "missing")


async def test_lease_contract_matches_memory_store(store):
    await store.set(_session())
    first = await store.claim_refresh("s1", "a", 30)
    assert first.status == "granted" and first.phase == "acquired"
    assert (await store.claim_refresh("s1", "b", 30)).status == "busy"
    assert await store.mark_refresh_sent("s1", first.fence + 1) is False
    assert await store.mark_refresh_sent("s1", first.fence) is True
    assert await store.mark_refresh_sent("s1", first.fence) is False
    assert await store.checkpoint_refresh("s1", first.fence, _tokens(7200), fresh_id_token=True)
    checkpointed = await store.get("s1")
    assert checkpointed is not None
    assert "org_id" not in checkpointed.claims
    assert checkpointed.access_expires_at < time.time()
    renewed = StwrdSession(**{**checkpointed.__dict__, "claims": {"sub": "usr_1", "name": "new"}})
    assert await store.complete_refresh("s1", first.fence, renewed)
    assert await store.complete_refresh("s1", first.fence, renewed) is False
    assert (await store.claim_refresh("s1", "b", 30)).status == "granted"


async def test_expired_lease_rules_depend_on_phase_using_the_database_clock(store):
    await store.set(_session())
    await store.claim_refresh("s1", "a", 0.05)
    await asyncio.sleep(0.1)
    again = await store.claim_refresh("s1", "b", 0.05)  # owner died before sending
    assert again.status == "granted"
    assert await store.mark_refresh_sent("s1", again.fence)
    await asyncio.sleep(0.1)
    assert (await store.claim_refresh("s1", "c", 30)).status == "uncertain"
    assert (await store.claim_refresh("s1", "d", 30)).status == "uncertain"

    await store.set(_session("s2"))
    lease = await store.claim_refresh("s2", "a", 0.05)
    assert await store.mark_refresh_sent("s2", lease.fence)
    assert await store.checkpoint_refresh("s2", lease.fence, _tokens(), fresh_id_token=False)
    await asyncio.sleep(0.1)
    resumed = await store.claim_refresh("s2", "b", 30)  # owner died while hydrating
    assert resumed.status == "granted" and resumed.phase == "hydrating"


async def test_delete_defeats_every_in_flight_write(store):
    await store.set(_session())
    lease = await store.claim_refresh("s1", "a", 30)
    assert await store.mark_refresh_sent("s1", lease.fence)
    await store.delete("s1")
    assert (
        await store.checkpoint_refresh("s1", lease.fence, _tokens(), fresh_id_token=False) is False
    )
    assert await store.complete_refresh("s1", lease.fence, _session()) is False
    assert await store.get("s1") is None
    assert (await store.claim_refresh("s1", "b", 30)).status == "gone"


async def test_release_distinguishes_unsent_from_possibly_processed(store):
    await store.set(_session())
    lease = await store.claim_refresh("s1", "a", 30)
    assert await store.mark_refresh_sent("s1", lease.fence)
    await store.release_refresh("s1", lease.fence, sent=False)
    retry = await store.claim_refresh("s1", "b", 30)
    assert retry.status == "granted" and retry.phase == "acquired"
    assert await store.mark_refresh_sent("s1", retry.fence)
    await store.release_refresh("s1", retry.fence, sent=True)
    assert (await store.claim_refresh("s1", "c", 30)).status == "uncertain"


async def test_concurrent_claims_grant_exactly_one_owner(store):
    await store.set(_session())
    claims = await asyncio.gather(*(store.claim_refresh("s1", f"w{n}", 30) for n in range(8)))
    statuses = sorted(claim.status for claim in claims)
    assert statuses == ["busy"] * 7 + ["granted"]


WORKER = textwrap.dedent(
    """
    import asyncio, json, sys, time
    from psycopg_pool import AsyncConnectionPool
    from stwrd.postgres import Keyring, PostgresSessionStore

    async def main(url, namespace, owner):
        keys = {"k1": b"1" * 32}
        async with AsyncConnectionPool(url, min_size=1, max_size=2, open=False) as pool:
            store = PostgresSessionStore(pool, namespace=namespace, keyring=Keyring(keys, "k1"))
            outcome = "waited"
            while True:
                claim = await store.claim_refresh("s1", owner, 30)
                if claim.status == "granted":
                    if claim.session.access_expires_at > time.time():  # a peer finished first
                        await store.release_refresh("s1", claim.fence, sent=False)
                        break
                    assert await store.mark_refresh_sent("s1", claim.fence)
                    await asyncio.sleep(0.5)  # the exchange
                    done = claim.session.__class__(**{**claim.session.__dict__,
                        "access_expires_at": time.time() + 3600})
                    assert await store.complete_refresh("s1", claim.fence, done)
                    outcome = "exchanged"
                    break
                latest = await store.get("s1")
                if latest.access_expires_at > time.time():
                    break
                await asyncio.sleep(0.05)
        print(json.dumps({"owner": owner, "outcome": outcome}))

    asyncio.run(main(*sys.argv[1:4]))
    """
)


async def test_two_real_processes_refresh_once(store, database_url, namespace):
    await store.set(_session())
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root)}
    processes = [
        subprocess.Popen(
            [sys.executable, "-I", "-c", WORKER, database_url, namespace, f"proc-{n}"],
            env={**env, "PYTHONPATH": str(root)},
            stdout=subprocess.PIPE,
            text=True,
        )
        for n in range(2)
    ]
    outputs = [json.loads(p.communicate(timeout=30)[0]) for p in processes]
    assert all(p.returncode == 0 for p in processes)
    assert sorted(o["outcome"] for o in outputs) == ["exchanged", "waited"]


async def test_replace_session_swaps_only_a_live_session_atomically(store):
    await store.set(_session("old"))
    lease = await store.claim_refresh("old", "a", 30)
    assert await store.replace_session("old", _session("new")) is True
    assert await store.get("old") is None and await store.get("new") is not None
    assert await store.mark_refresh_sent("old", lease.fence) is False
    assert await store.replace_session("old", _session("again")) is False
    assert await store.get("again") is None


async def test_a_reborn_row_never_matches_an_old_owners_fence(store):
    await store.set(_session())
    old = await store.claim_refresh("s1", "a", 30)
    await store.delete("s1")
    await store.set(_session())
    new = await store.claim_refresh("s1", "b", 30)
    assert new.fence != old.fence
    assert await store.mark_refresh_sent("s1", old.fence) is False


async def test_purge_expired_removes_only_expired_sessions(store):
    live = _session("live")
    dead = StwrdSession(**{**_session("dead").__dict__, "expires_at": time.time() - 5})
    await store.set(live)
    await store.set(dead)
    assert await store.purge_expired() == 1
    assert await store.get("dead") is None and await store.get("live") is not None
