"""`StwrdUser`, `StwrdSession`, `MemoryStore`. The shape of `user`: its keys
are always present, with `null` / `[]` when there is no data.
"""

from __future__ import annotations

import time

import pytest

from stwrd import StwrdSession, StwrdUser, Tokens
from stwrd.sessions import MemoryStore


@pytest.mark.parametrize(
    "claims,roles,org",
    [
        ({"roles": ["reader"], "permissions": []}, ["reader"], None),
        (
            {
                "org_id": "opaque",
                "org_display_name": "Example",
                "org_roles": ["reader"],
                "org_permissions": [],
            },
            [],
            "opaque",
        ),
        ({"org_roles": ["reader"]}, [], None),
        ({"roles": "reader", "permissions": []}, [], None),
        ({"roles": ["reader"], "permissions": [], "org_id": "opaque"}, [], None),
        (
            {
                "org_id": "opaque",
                "org_display_name": "",
                "org_roles": ["reader"],
                "org_permissions": [],
            },
            [],
            None,
        ),
        ({}, [], None),
    ],
)
def test_capability_families_fail_closed(claims, roles, org):
    session = StwrdSession(
        id="s",
        sid_idp=None,
        sub="u",
        claims={"sub": "u", **claims},
        tokens=_tokens(),
        expires_at=1,
        access_expires_at=1,
    )
    assert session.user.roles == roles
    assert (session.organization.id if session.organization else None) == org
    assert session.has_role("reader") is bool(roles or org)


def test_normalized_user_excludes_private_and_organization_fields():
    from dataclasses import asdict

    user = StwrdUser.from_claims({"sub": "u", "name": "Name", "picture": "avatar", "sid": "secret"})
    assert asdict(user) == {
        "id": "u",
        "email": None,
        "email_verified": False,
        "display_name": "Name",
        "avatar_url": "avatar",
        "roles": [],
        "permissions": [],
    }


def test_userinfo_cannot_inject_authority():
    from stwrd.sessions import merge_userinfo

    assert merge_userinfo({"sub": "u"}, {"sub": "u", "roles": ["admin"], "sid": "injected"}) == {
        "sub": "u"
    }


def test_userinfo_subject_must_match():
    from stwrd import OidcError
    from stwrd.sessions import merge_userinfo

    with pytest.raises(OidcError):
        merge_userinfo({"sub": "u"}, {"sub": "other"})


def _tokens(*, expires_in: float = 3600.0, refresh_token: str | None = None) -> Tokens:
    return Tokens(
        access_token="at",
        id_token="idt",
        token_type="Bearer",
        expires_at=time.time() + expires_in,
        refresh_token=refresh_token,
    )


def test_session_user_is_derived_from_claims() -> None:
    session = StwrdSession(
        id="s1",
        sid_idp="sid1",
        sub="usr_1",
        claims={"sub": "usr_1", "email": "a@b.test"},
        tokens=_tokens(),
        expires_at=time.time() + 3600,
        access_expires_at=time.time() + 3600,
    )
    assert session.user.email == "a@b.test"


def test_access_token_expired_is_independent_of_the_session_ttl() -> None:
    # The two clocks are separate on purpose (`sessions.py`): a session well
    # inside its 8h window can still have an access token that already
    # expired.
    session = StwrdSession(
        id="s1",
        sid_idp="sid1",
        sub="usr_1",
        claims={"sub": "usr_1"},
        tokens=_tokens(expires_in=-1),
        expires_at=time.time() + 3600,
        access_expires_at=time.time() - 1,
    )
    assert session.access_token_expired() is True
    assert session.is_expired() is False


@pytest.mark.asyncio
async def test_memory_store_round_trips() -> None:
    store = MemoryStore()
    session = StwrdSession(
        id="s1",
        sid_idp="sid1",
        sub="usr_1",
        claims={"sub": "usr_1"},
        tokens=_tokens(),
        expires_at=time.time() + 3600,
        access_expires_at=time.time() + 3600,
    )
    await store.set(session)
    assert await store.get("s1") is session
    await store.delete("s1")
    assert await store.get("s1") is None


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


@pytest.mark.asyncio
async def test_refresh_lease_is_exclusive_and_fenced() -> None:
    store = MemoryStore()
    await store.set(_session())
    first = await store.claim_refresh("s1", "a", 30)
    assert first.status == "granted" and first.phase == "acquired"
    assert (await store.claim_refresh("s1", "b", 30)).status == "busy"
    assert await store.mark_refresh_sent("s1", first.fence + 1) is False
    assert await store.mark_refresh_sent("s1", first.fence) is True
    assert await store.mark_refresh_sent("s1", first.fence) is False
    new_tokens = _tokens(expires_in=7200)
    assert await store.checkpoint_refresh("s1", first.fence, new_tokens, fresh_id_token=True)
    checkpointed = await store.get("s1")
    assert checkpointed is not None
    assert checkpointed.tokens is new_tokens
    assert "org_id" not in checkpointed.claims  # authority is stale until userinfo
    assert checkpointed.access_expires_at < time.time()  # still counts as expired
    renewed = StwrdSession(**{**checkpointed.__dict__, "claims": {"sub": "usr_1", "name": "new"}})
    assert await store.complete_refresh("s1", first.fence, renewed)
    assert await store.complete_refresh("s1", first.fence, renewed) is False
    assert (await store.claim_refresh("s1", "b", 30)).status == "granted"


@pytest.mark.asyncio
async def test_expired_lease_rules_depend_on_phase() -> None:
    store = MemoryStore()
    await store.set(_session())
    unsent = await store.claim_refresh("s1", "a", 0)
    again = await store.claim_refresh("s1", "b", 0)  # owner died before sending
    assert again.status == "granted" and again.fence > unsent.fence
    assert await store.mark_refresh_sent("s1", again.fence)
    assert (await store.claim_refresh("s1", "c", 30)).status == "uncertain"
    assert (await store.claim_refresh("s1", "d", 30)).status == "uncertain"  # permanent

    await store.set(_session("s2"))
    lease = await store.claim_refresh("s2", "a", 0)
    assert await store.mark_refresh_sent("s2", lease.fence)
    assert await store.checkpoint_refresh("s2", lease.fence, _tokens(), fresh_id_token=False)
    resumed = await store.claim_refresh("s2", "b", 30)  # owner died while hydrating
    assert resumed.status == "granted" and resumed.phase == "hydrating"


@pytest.mark.asyncio
async def test_delete_defeats_every_in_flight_write() -> None:
    store = MemoryStore()
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


@pytest.mark.asyncio
async def test_release_distinguishes_unsent_from_possibly_processed() -> None:
    store = MemoryStore()
    await store.set(_session())
    lease = await store.claim_refresh("s1", "a", 30)
    assert await store.mark_refresh_sent("s1", lease.fence)
    await store.release_refresh("s1", lease.fence, sent=False)  # never left
    retry = await store.claim_refresh("s1", "b", 30)
    assert retry.status == "granted" and retry.phase == "acquired"
    assert await store.mark_refresh_sent("s1", retry.fence)
    await store.release_refresh("s1", retry.fence, sent=True)  # may have been processed
    assert (await store.claim_refresh("s1", "c", 30)).status == "uncertain"


@pytest.mark.parametrize("value", [42, {}, [], True])
def test_malformed_optional_profile_values_normalize_to_null(value):
    user = StwrdUser.from_claims(
        {"sub": "u", "email": value, "name": value, "picture": value, "email_verified": value}
    )
    assert user.email is None
    assert user.display_name is None
    assert user.avatar_url is None
    assert user.email_verified is (value is True)


@pytest.mark.parametrize("subject", [None, "", 42, {}, []])
def test_missing_or_invalid_subject_cannot_merge_userinfo(subject):
    from stwrd import OidcError
    from stwrd.sessions import merge_userinfo

    with pytest.raises(OidcError):
        merge_userinfo({"sub": subject}, {"sub": subject})


@pytest.mark.asyncio
async def test_replace_session_swaps_only_a_live_session_and_defeats_its_lease() -> None:
    store = MemoryStore()
    await store.set(_session("old"))
    lease = await store.claim_refresh("old", "a", 30)
    assert await store.replace_session("old", _session("new")) is True
    assert await store.get("old") is None and await store.get("new") is not None
    assert await store.mark_refresh_sent("old", lease.fence) is False  # no resurrection
    assert await store.replace_session("old", _session("again")) is False
    assert await store.get("again") is None
