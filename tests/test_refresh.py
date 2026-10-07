"""The BFF renews tokens on its own, and when a membership is removed the
refresh fails and the local session ends.

Against `FakeIdp`'s real `grant_type=refresh_token` branch — an HTTP round
trip over `httpx.ASGITransport`, not a mock of `OidcClient` — because the
property this file pins is exactly what happens at that boundary: an
expired access token with a live `refresh_token` renews without the caller
ever touching `/auth/sign-in` again.

**Renewal fails in TWO different ways.** A rejection by the IdP — revoked,
reused, dead family — ends the local session; an IdP that does not answer —
no connection, or a 5xx — ends nothing and raises. Treating them as one would
sign out everybody who was renewing at any blip of the IdP.
"""

from __future__ import annotations

import time

import pytest

from stwrd import IdpUnavailable, Stwrd
from stwrd.sessions import StwrdSession, Tokens

from .fake_idp import FakeIdp


async def _log_in_with_refresh(
    stwrd: Stwrd,
    fake_idp: FakeIdp,
    *,
    sub: str = "usr_1",
    access_expires_in: float = 3600,
    **userinfo,
) -> StwrdSession:
    """The shape `GET /auth/callback` produces, but built directly against
    `FakeIdp.issue_code(with_refresh=True)` — this file's whole point is the
    renewal branch, not re-proving the callback flow `test_auth_router.py`
    already owns."""
    code = fake_idp.issue_code(sub=sub, with_refresh=True, userinfo=userinfo)
    token_response = await stwrd.oidc.exchange_code(
        code=code, code_verifier="whatever-verifier-the-fake-ignores"
    )
    now = time.time()
    tokens = Tokens(
        access_token=token_response["access_token"],
        id_token=token_response["id_token"],
        token_type="Bearer",
        expires_at=now + access_expires_in,
        refresh_token=token_response["refresh_token"],
    )
    session = StwrdSession(
        id=stwrd.session_id_for_sid(fake_idp._userinfo_by_token[tokens.access_token]["sid"]),
        sid_idp=fake_idp._userinfo_by_token[tokens.access_token]["sid"],
        sub=sub,
        claims={"sub": sub, **userinfo},
        tokens=tokens,
        expires_at=now + 8 * 3600,
        access_expires_at=tokens.expires_at,
    )
    await stwrd.sessions.set(session)
    return session


@pytest.mark.asyncio
async def test_an_expired_access_token_with_a_refresh_token_renews_transparently(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1, email="a@b.test")
    old_access_token = session.tokens.access_token

    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is not None
    assert not resolved.access_token_expired()
    assert resolved.tokens.access_token != old_access_token
    assert len(fake_idp.refresh_calls) == 1


@pytest.mark.asyncio
async def test_the_renewed_session_is_persisted_through_the_store(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """Without this, other workers would keep serving stale claims — `renew`
    has to actually reach the store, not just the in-memory return value."""
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)

    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    assert resolved is not None

    stored = await stwrd.sessions.get(session.id)
    assert stored is not None
    assert stored.tokens.access_token == resolved.tokens.access_token


@pytest.mark.asyncio
async def test_userinfo_is_refetched_on_renewal_so_a_lost_membership_disappears(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """Whoever lost a membership stops seeing it here without waiting for the
    next refresh — the refresh IS that moment for a BFF session that only ever
    reads its own store."""
    session = await _log_in_with_refresh(
        stwrd, fake_idp, access_expires_in=-1, org_id="org-1", org_roles=["org:admin"]
    )
    # The membership was pulled between login and this renewal — the fake's
    # userinfo answer for the NEW access token no longer carries it.
    entry = fake_idp._refresh_tokens[session.tokens.refresh_token]
    entry["userinfo"] = {k: v for k, v in entry["userinfo"].items() if not k.startswith("org_")}

    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is not None
    assert resolved.claims.get("org_id") is None


@pytest.mark.asyncio
async def test_a_rejected_refresh_ends_the_local_session(stwrd: Stwrd, fake_idp: FakeIdp) -> None:
    """If the refresh fails, the BFF's local session ends and the app sees "no
    session". Exercised against the fake's real `invalid_grant` response, not a
    raised exception — the same shape a revoked or reused refresh produces for
    real."""
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    fake_idp.refresh_status_code = 400

    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is None
    assert await stwrd.sessions.get(session.id) is None


#: The ways the IdP **does not answer**. To the SDK they are one thing, hence
#: the parametrization: there is no connection, or there is and it returns a
#: 5xx. The second is the one that bites in production — an IdP under load
#: answering 502 through the edge — and the one a bare `except httpx.HTTPError`
#: does not see.
SILENCES = [
    pytest.param("transport", id="the IdP does not accept the connection"),
    pytest.param(502, id="the IdP answers 502 through the edge"),
    pytest.param(503, id="the IdP answers 503"),
    # The three 4xx statuses that are not a rejection either
    # (`oidc.RETRY_STATUSES`). The 429 is the one that bites: the token
    # endpoint's rate limit is PER `client_id`, so a large relying party that
    # crosses it would sign out everyone who was renewing — and those users go
    # back to `/authorize`, so the limit would amplify the load that triggered it.
    pytest.param(408, id="the IdP times out (408)"),
    pytest.param(425, id="too early (425)"),
    pytest.param(429, id="token endpoint rate limit: slow_down (429)"),
]


def _silence_the_idp(stwrd: Stwrd, fake_idp: FakeIdp, mode) -> None:
    """Make the IdP mute in the way `mode` asks, AFTER the login: what is
    exercised is the RENEWAL call finding nobody, not the login."""
    import httpx

    if mode == "transport":

        class _BrokenTransport(httpx.AsyncBaseTransport):
            async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
                raise httpx.ConnectError("connection refused", request=request)

        stwrd.oidc._http = httpx.AsyncClient(
            transport=_BrokenTransport(), base_url="https://x.test"
        )
    else:
        fake_idp.refresh_status_code = mode


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", SILENCES)
async def test_an_idp_that_never_answers_does_not_end_the_local_session(
    stwrd: Stwrd, fake_idp: FakeIdp, mode
) -> None:
    """**Silence is not a rejection**, and that is the whole property.

    An earlier behavior put "the IdP did not answer" in the same bag as a
    revoked refresh, and the SDK deleted the local session in both cases. The
    argument "the SDK can no longer vouch for the claims" holds for a
    rejection, where the IdP looked at the credential and said no; it does not
    hold for silence, where it said nothing. Treating them alike turned any
    blip of the IdP into a sign-out of everyone who was renewing, buying
    nothing: whoever can take the IdP down gains nothing more than that.

    Both halves matter separately:

    * it **raises** instead of returning `None` — returning `None` means "no
      session", which is the lie that signed people out;
    * **the session stays in the store** — that is what lets the next
      attempt, seconds later with the IdP back, renew without anyone noticing.

    What it does NOT do is serve the old claims. It returns no session at all.
    """
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    _silence_the_idp(stwrd, fake_idp, mode)

    with pytest.raises(IdpUnavailable):
        await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert await stwrd.sessions.get(session.id) is not None, (
        "the IdP did not answer and the SDK deleted the session anyway: this is "
        "the sign-out this lock exists to prevent"
    )


@pytest.mark.asyncio
async def test_a_silence_after_the_exchange_never_leaves_the_consumed_refresh_behind(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """The most dangerous window in this file.

    The exchange succeeds — the IdP has already rotated: the old refresh token
    is consumed — and only then does `userinfo` go silent. If the session kept
    the old refresh token, the next attempt would be a REUSE, and reuse of a
    rotated refresh token kills the whole family. The blip these locks exist
    to survive would then cost MORE than before — it takes down the entire
    family and raises a reuse alarm.

    What is asserted is that the store holds the NEW refresh token — not
    "some" token: the one the exchange just returned, which is the only way
    the retry is not a reuse.

    There is a second, quieter requirement. Storing the NEW expiry next to the
    OLD claims would make the access token look "live" to `resolve_session`,
    so the next attempt would NOT enter `_renew` again and would never query
    `userinfo` again until that new expiry (an hour, by default) arrived on its
    own. Someone whose membership was removed during the outage would keep
    being served it. So the session must still count as expired here.
    """
    session = await _log_in_with_refresh(
        stwrd, fake_idp, access_expires_in=-1, org_id="org-1", org_roles=["org:admin"]
    )
    consumed = session.tokens.refresh_token

    # The exchange answers; userinfo does not. `fake_idp.refresh_status_code`
    # would silence the exchange too, so the silence goes on the next call.
    original_userinfo = stwrd.oidc.userinfo

    async def _silent_userinfo(_access_token):
        raise IdpUnavailable("userinfo: the IdP did not respond (test).")

    stwrd.oidc.userinfo = _silent_userinfo  # type: ignore[method-assign]
    try:
        with pytest.raises(IdpUnavailable):
            await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    finally:
        stwrd.oidc.userinfo = original_userinfo  # type: ignore[method-assign]

    stored = await stwrd.sessions.get(session.id)
    assert stored is not None, "the session was deleted although the IdP rejected nothing"
    assert stored.tokens.refresh_token != consumed, (
        "the store kept the refresh token the exchange ALREADY consumed: the "
        "next attempt is a reuse and kills the whole family"
    )
    assert stored.access_token_expired(), (
        "the early save marked the access token as live: the next request does "
        "not renew again and serves the old claims until the new expiry "
        "arrives on its own"
    )

    # The membership was removed during the outage. If the next attempt does
    # not REALLY query `userinfo` again, this is never noticed.
    assert stored.tokens.refresh_token is not None
    entry = fake_idp._userinfo_by_token[stored.tokens.access_token]
    fake_idp._userinfo_by_token[stored.tokens.access_token] = {
        k: v for k, v in entry.items() if not k.startswith("org_")
    }

    # And the proof that it works: with the IdP back, it renews for real —
    # without reuse, and with the lost membership already out of the claims.
    renewed = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    assert renewed is not None
    # The retry only repeats `userinfo` with the stored tokens: exchanging the
    # refresh token again would be a reuse (the store's lease contract).
    assert len(fake_idp.refresh_calls) == 1
    assert renewed.claims.get("org_id") is None


#: A 200 that does not carry what `_renew` needs. It is not silence — the IdP
#: answered — so it is a REJECTION like any other.
MALFORMED_BODIES = [
    pytest.param({"token_type": "Bearer"}, id="no access_token"),
    pytest.param({"access_token": "tok", "expires_in": "soon"}, id="non-numeric expires_in"),
    pytest.param({"access_token": "tok", "expires_in": None}, id="null expires_in"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("body", MALFORMED_BODIES)
async def test_a_malformed_200_during_the_exchange_ends_the_session_without_crashing(
    stwrd: Stwrd, fake_idp: FakeIdp, body: dict
) -> None:
    """The early save moved the construction of `Tokens` out of the only `try`
    that covered it: an IdP or a proxy returning 200 with such a body would
    raise the raw `KeyError`/`TypeError`/`ValueError` up to the endpoint — a
    generic 500, with no 401 or 503, and without deleting the session —
    although the docstring of `_renew` promises `None`.

    It also kept the two SDKs from behaving alike: both must end up in the same
    place for the same malformed body — session ended, nothing that blows up
    all the way to the endpoint.
    """
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    original_exchange = stwrd.oidc.exchange_refresh_token

    async def _malformed_exchange(_refresh_token):
        return body

    stwrd.oidc.exchange_refresh_token = _malformed_exchange  # type: ignore[method-assign]
    try:
        resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    finally:
        stwrd.oidc.exchange_refresh_token = original_exchange  # type: ignore[method-assign]

    assert resolved is None
    assert await stwrd.sessions.get(session.id) is None


@pytest.mark.asyncio
async def test_the_session_renews_normally_once_the_idp_answers_again(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """The consequence that matters to the person using the app, and that none
    of the locks above asserts: the outage was a gap, not an ending.

    Without this, "does not delete the session" could coexist with a session
    left unusable — a consumed token, a half-written state — and the test
    would pass while the person still cannot get in.
    """
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    original = stwrd.oidc._http
    _silence_the_idp(stwrd, fake_idp, "transport")

    with pytest.raises(IdpUnavailable):
        await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    # The IdP comes back.
    stwrd.oidc._http = original
    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is not None, "the IdP came back and the session could not be renewed"
    assert resolved.id == session.id


@pytest.mark.asyncio
async def test_a_successful_renewal_slides_the_local_session_ttl_forward(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """The TTL is 8 h and renewal slides it forward: `expires_at` must not stay
    untouched on a renewal. The IdP, not this local window,
    governs the outer bound — every renewal already demanded a live refresh
    token inside its family's absolute `family_expires_at` — so sliding the
    local TTL here never loosens anything the IdP did not already re-check a
    moment ago.
    """
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    # Move the session close to the end of its local window — exactly the
    # case a non-sliding TTL would let expire out from under someone mid-use
    # even though the refresh that just happened succeeded.
    near_expiry = time.time() + 5
    await stwrd.sessions.set(
        StwrdSession(
            id=session.id,
            sid_idp=session.sid_idp,
            sub=session.sub,
            claims=session.claims,
            tokens=session.tokens,
            expires_at=near_expiry,
            access_expires_at=session.access_expires_at,
        )
    )

    before = time.time()
    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is not None
    assert resolved.expires_at > near_expiry
    assert resolved.expires_at >= before + stwrd.config.session_ttl_s - 5

    # Persisted, not just the in-process return value — the next request (or
    # another worker) has to see the same slid deadline.
    stored = await stwrd.sessions.get(session.id)
    assert stored is not None
    assert stored.expires_at == resolved.expires_at


@pytest.mark.asyncio
async def test_a_live_access_token_is_served_without_touching_the_network(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=3600)

    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is not None
    assert resolved.tokens.access_token == session.tokens.access_token
    assert fake_idp.refresh_calls == []


@pytest.mark.asyncio
async def test_without_offline_access_expiry_still_ends_the_session_not_renews(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """The shape is unchanged for a session that never got a
    `refresh_token` in the first place."""
    code = fake_idp.issue_code(sub="usr_1", with_refresh=False)
    token_response = await stwrd.oidc.exchange_code(
        code=code, code_verifier="whatever-verifier-the-fake-ignores"
    )
    now = time.time()
    session = StwrdSession(
        id="s-no-refresh",
        sid_idp="sid-1",
        sub="usr_1",
        claims={"sub": "usr_1"},
        tokens=Tokens(
            access_token=token_response["access_token"],
            id_token=token_response["id_token"],
            token_type="Bearer",
            expires_at=now - 1,
            refresh_token=None,
        ),
        expires_at=now + 3600,
        access_expires_at=now - 1,
    )
    await stwrd.sessions.set(session)

    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))

    assert resolved is None
    assert fake_idp.refresh_calls == []
    assert await stwrd.sessions.get(session.id) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("new_id_token", [False, True])
async def test_refresh_replaces_authority_without_userinfo_injection(
    stwrd, fake_idp, monkeypatch, new_id_token
):
    session = await _log_in_with_refresh(
        stwrd, fake_idp, access_expires_in=-1, roles=["admin"], permissions=["write"]
    )
    exchange = stwrd.oidc.exchange_refresh_token

    async def replace_refresh(token):
        response = await exchange(token)
        if not new_id_token:
            response.pop("id_token")
        return response

    monkeypatch.setattr(stwrd.oidc, "exchange_refresh_token", replace_refresh)
    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    assert resolved is not None
    assert resolved.claims.get("roles", []) == []
    assert resolved.claims.get("permissions", []) == []
    assert resolved.organization is None
    assert not resolved.has_role("admin")


@pytest.mark.asyncio
async def test_refresh_id_token_subject_mismatch_ends_session(stwrd, fake_idp, monkeypatch):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    validate = stwrd.oidc.validate_id_token

    async def different_subject(*args, **kwargs):
        claims = await validate(*args, **kwargs)
        return {**claims, "sub": "different"}

    monkeypatch.setattr(stwrd.oidc, "validate_id_token", different_subject)
    assert await stwrd.resolve_session(stwrd.seal({"sid": session.id})) is None
    assert await stwrd.sessions.get(session.id) is None


@pytest.mark.asyncio
async def test_rotated_credentials_and_cleared_authority_are_durable_on_userinfo_outage(
    stwrd, fake_idp, monkeypatch
):
    session = await _log_in_with_refresh(
        stwrd, fake_idp, access_expires_in=-1, roles=["admin"], permissions=["write"]
    )

    async def unavailable(_token):
        raise IdpUnavailable("offline")

    monkeypatch.setattr(stwrd.oidc, "userinfo", unavailable)
    with pytest.raises(IdpUnavailable):
        await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    second = Stwrd(stwrd.config, sessions=stwrd.sessions, http_client=stwrd._http)
    persisted = await second.session_from_cookie(stwrd.seal({"sid": session.id}))
    assert persisted is not None
    assert persisted.tokens.refresh_token != session.tokens.refresh_token
    assert persisted.user.roles == []
    assert persisted.user.permissions == []
    assert persisted.access_token_expired()


@pytest.mark.asyncio
async def test_refresh_verified_id_token_replaces_capability_family(stwrd, fake_idp):
    session = await _log_in_with_refresh(
        stwrd, fake_idp, access_expires_in=-1, roles=["old"], permissions=["old:write"]
    )
    entry = fake_idp._refresh_tokens[session.tokens.refresh_token]
    entry["id_claims"] = {
        "org_id": "opaque",
        "org_display_name": "New Org",
        "org_roles": ["new"],
        "org_permissions": ["new:write"],
    }
    entry["userinfo"].update({"roles": ["injected"], "permissions": ["injected:write"]})
    resolved = await stwrd.resolve_session(stwrd.seal({"sid": session.id}))
    assert resolved is not None
    assert resolved.user.roles == []
    assert resolved.organization.id == "opaque"
    assert resolved.has_role("new")
    assert resolved.has_permission("new:write")
    assert not resolved.has_role("old")
    assert not resolved.has_role("injected")
