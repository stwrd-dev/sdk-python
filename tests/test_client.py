"""`Stwrd`: cookie sealing, CSRF, and session resolution against a plain
`MemoryStore` — no HTTP needed for any of this.
"""

from __future__ import annotations

import time

import pytest

from stwrd import ConfigError, Stwrd, StwrdSession, Tokens


@pytest.mark.asyncio
async def test_seal_and_unseal_round_trip(stwrd: Stwrd) -> None:
    value = {"sid": "abc123"}
    sealed = stwrd.seal(value)
    assert stwrd.unseal(sealed) == value


@pytest.mark.asyncio
async def test_unseal_rejects_a_tampered_cookie(stwrd: Stwrd) -> None:
    sealed = stwrd.seal({"sid": "abc123"})
    payload, _, signature = sealed.rpartition(".")
    tampered = f"{payload}x.{signature}"
    assert stwrd.unseal(tampered) is None


@pytest.mark.asyncio
async def test_unseal_rejects_garbage(stwrd: Stwrd) -> None:
    assert stwrd.unseal(None) is None
    assert stwrd.unseal("") is None
    assert stwrd.unseal("not-a-sealed-value") is None


@pytest.mark.asyncio
async def test_unseal_rejects_a_cookie_signed_by_a_different_secret(
    stwrd_config, idp_http_client
) -> None:
    other = Stwrd(stwrd_config.replace(cookie_secret="y" * 32), http_client=idp_http_client)
    try:
        sealed = other.seal({"sid": "abc123"})
    finally:
        await other.close()

    first = Stwrd(stwrd_config, http_client=idp_http_client)
    try:
        assert first.unseal(sealed) is None
    finally:
        await first.close()


@pytest.mark.asyncio
async def test_csrf_is_deterministic_for_the_same_session_id(stwrd: Stwrd) -> None:
    assert stwrd.csrf("session-1") == stwrd.csrf("session-1")
    assert stwrd.csrf("session-1") != stwrd.csrf("session-2")


@pytest.mark.asyncio
async def test_new_authorization_state_is_unique_per_call(stwrd: Stwrd) -> None:
    a = stwrd.new_authorization_state(return_to="/private")
    b = stwrd.new_authorization_state(return_to="/private")
    assert a.state != b.state
    assert a.nonce != b.nonce
    assert a.code_verifier != b.code_verifier
    assert a.return_to == "/private"


def _session(*, access_expires_in: float, session_expires_in: float = 3600) -> StwrdSession:
    now = time.time()
    return StwrdSession(
        id="s1",
        sid_idp="sid1",
        sub="usr_1",
        claims={"sub": "usr_1", "email": "a@b.test"},
        tokens=Tokens(
            access_token="at",
            id_token="idt",
            token_type="Bearer",
            expires_at=now + access_expires_in,
            refresh_token=None,
        ),
        expires_at=now + session_expires_in,
        access_expires_at=now + access_expires_in,
    )


@pytest.mark.asyncio
async def test_resolve_session_returns_a_live_session(stwrd: Stwrd) -> None:
    session = _session(access_expires_in=3600)
    await stwrd.sessions.set(session)
    cookie = stwrd.seal({"sid": session.id})

    resolved = await stwrd.resolve_session(cookie)
    assert resolved is not None
    assert resolved.id == session.id


@pytest.mark.asyncio
async def test_resolve_session_ends_when_the_access_token_expired_and_there_is_no_refresh(
    stwrd: Stwrd,
) -> None:
    # Without `offline_access` there is no renewal — with no
    # `refresh_token` on the session (`Tokens.refresh_token` defaults to
    # `None`) the credential's lifetime is still the access token's. The
    # renewal branch itself lives in `test_refresh.py`.
    session = _session(access_expires_in=-1)
    await stwrd.sessions.set(session)
    cookie = stwrd.seal({"sid": session.id})

    resolved = await stwrd.resolve_session(cookie)
    assert resolved is None
    assert await stwrd.sessions.get(session.id) is None  # the local session actually ended


@pytest.mark.asyncio
async def test_resolve_session_ends_when_the_session_itself_expired(stwrd: Stwrd) -> None:
    session = _session(access_expires_in=3600, session_expires_in=-1)
    await stwrd.sessions.set(session)
    cookie = stwrd.seal({"sid": session.id})

    assert await stwrd.resolve_session(cookie) is None


@pytest.mark.asyncio
async def test_resolve_session_with_no_cookie_is_none(stwrd: Stwrd) -> None:
    assert await stwrd.resolve_session(None) is None


@pytest.mark.asyncio
async def test_session_from_cookie_does_not_end_an_expired_access_token(stwrd: Stwrd) -> None:
    # A raw store read, with no renewal — and, by the same token, without the
    # side effect of ending the session either.
    session = _session(access_expires_in=-1)
    await stwrd.sessions.set(session)
    cookie = stwrd.seal({"sid": session.id})

    raw = await stwrd.session_from_cookie(cookie)
    assert raw is not None
    assert raw.id == session.id
    assert await stwrd.sessions.get(session.id) is not None  # still there: no side effect


@pytest.mark.asyncio
async def test_verify_webhook_without_a_configured_secret_raises_config_error(
    stwrd_config, idp_http_client
) -> None:
    instance = Stwrd(stwrd_config.replace(webhook_secret=""), http_client=idp_http_client)
    try:
        with pytest.raises(ConfigError):
            instance.verify_webhook(b"{}", {})
    finally:
        await instance.close()


@pytest.mark.asyncio
async def test_verify_webhook_dedups_against_seen_webhook_ids(stwrd: Stwrd) -> None:
    import base64
    import hashlib
    import hmac
    import json

    body = json.dumps(
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "type": "user.created",
            "api_version": "v1",
            "created_at": "2026-01-01T00:00:00Z",
            "data": {},
        },
        separators=(",", ":"),
    ).encode()
    timestamp = str(int(time.time()))
    signed = f"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee.{timestamp}.".encode() + body
    signature = (
        "v1,"
        + base64.b64encode(
            hmac.new(stwrd.config.webhook_secret.encode(), signed, hashlib.sha256).digest()
        ).decode()
    )
    headers = {
        "webhook-id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "webhook-timestamp": timestamp,
        "webhook-signature": signature,
    }

    first = stwrd.verify_webhook(body, headers)
    assert first.id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    from stwrd import DuplicateEventError

    with pytest.raises(DuplicateEventError):
        stwrd.verify_webhook(body, headers)


def test_back_channel_logout_reaches_the_session_the_store_already_has(stwrd: Stwrd) -> None:
    """The property that makes back-channel logout useful: the notice carries
    the IdP's `sid` while the store is keyed by the BFF's id, so the id has to
    be derivable from the `sid` — otherwise the notice arrives and kills
    nothing.
    """
    sid = "a-session-at-the-idp"

    first = stwrd.session_id_for_sid(sid)

    assert first == stwrd.session_id_for_sid(sid), "the derivation has to be stable"
    assert first != stwrd.session_id_for_sid("another-session")
    # Keyed: a leaked `sid` does not let anyone guess the local id.
    assert sid not in first


def test_a_different_cookie_secret_derives_a_different_session_id():
    """Rotating the secret changes the derivation, and that costs nothing: the
    same rotation already invalidated every sealed cookie, so those sessions
    were unreachable anyway.
    """
    from stwrd import Stwrd, StwrdConfig

    def build(secret: str) -> Stwrd:
        return Stwrd(
            StwrdConfig(
                issuer="https://idp.example.com",
                client_id="demo",
                client_secret="s3cret",
                base_url="https://demo.test",
                cookie_secret=secret,
            )
        )

    assert build("a" * 32).session_id_for_sid("s") != build("b" * 32).session_id_for_sid("s")


# --- `connect_to`: connect there, keep the issuer's `Host` -----------------------


@pytest.mark.asyncio
async def test_connect_to_rewrites_the_connection_and_keeps_the_issuer_host(
    stwrd_config,
) -> None:
    """The IdP routes the tenant by `Host`, so the SDK has to reach `127.0.0.1:3005`
    AS `idp.example.com`. Observed at the transport: where the request
    connects, and which `Host` it carries."""
    import httpx

    from stwrd import connect_to_hook

    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((str(request.url), request.headers["host"]))
        return httpx.Response(200, json={})

    config = stwrd_config.replace(connect_to="http://127.0.0.1:3005")
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        event_hooks={"request": [connect_to_hook(config.connect_to)]},
    )
    async with client:
        await client.get(f"{config.issuer}/.well-known/openid-configuration?x=1")

    assert seen == [
        (
            "http://127.0.0.1:3005/.well-known/openid-configuration?x=1",
            "idp.example.com",
        )
    ]


@pytest.mark.asyncio
async def test_a_stwrd_built_with_connect_to_owns_a_client_that_connects_there(
    stwrd_config,
) -> None:
    """The first-class path: no `http_client` injected, `connect_to` set —
    discovery goes to the loopback target with the issuer's `Host`."""
    import httpx

    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.host, request.headers["host"]))
        return httpx.Response(404)

    instance = Stwrd(stwrd_config.replace(connect_to="http://127.0.0.1:3005"))
    # Swap only the wire; the hook the SDK installed stays.
    instance._http._transport = httpx.MockTransport(handler)  # noqa: SLF001 - the wire, not the hook
    try:
        with pytest.raises(Exception):  # noqa: B017 - a 404 discovery is an error either way
            await instance.oidc.discover()
    finally:
        await instance.close()

    assert seen and seen[0] == ("127.0.0.1", "idp.example.com")
