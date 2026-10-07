"""`auth_router` and the dependency factories, exercised end to end against
the fake IdP (`fake_idp.py`): `/auth/session`, the routes and the dependencies.

Two `httpx.AsyncClient`s, not one `mounts=` client: a single multi-host
client is only needed by an end-to-end test with a real browser, to prove a
real browser's cookie jar carries across hosts. Here the "browser" step (hitting the demo app) and
the "back-channel" step (the SDK calling the fake IdP) are naturally
separate objects already — `Stwrd(http_client=idp_http_client)` is the
back-channel, and `demo_client` below is a second, independent client for
the app under test — so there is nothing a shared client would additionally
verify.
"""

from __future__ import annotations

import dataclasses
import time
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import Depends, FastAPI

from stwrd import Stwrd, StwrdConfig, StwrdUser
from stwrd.fastapi import (
    auth_router,
    current_user,
    optional_user,
    protect,
    require_auth,
    safe_target,
)

from .fake_idp import ISSUER, FakeIdp

CLIENT_ID = "demo-client"
CLIENT_SECRET = "demo-secret"
BASE_URL = "https://demo.test"


def _build_demo_app(stwrd: Stwrd, *, protected: bool = False) -> FastAPI:
    app = FastAPI()
    app.include_router(auth_router(stwrd))

    @app.get("/whoami")
    async def whoami(user: StwrdUser | None = Depends(optional_user(stwrd))):
        return {"sub": user.id if user else None}

    @app.get("/private")
    async def private(user: StwrdUser = Depends(current_user(stwrd))):
        return {"sub": user.id}

    @app.get("/guarded")
    async def guarded(_: None = Depends(require_auth(stwrd))):
        return {"ok": True}

    if protected:
        protect(app, stwrd, public=("/public*",))

        @app.get("/public/info")
        async def public_info():
            return {"ok": True}

        @app.get("/needs-session")
        async def needs_session():
            return {"ok": True}

    return app


@pytest.fixture
async def demo_client(stwrd: Stwrd) -> AsyncIterator[httpx.AsyncClient]:
    app = _build_demo_app(stwrd)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=BASE_URL, follow_redirects=False
    ) as client:
        yield client


async def _login(
    demo_client: httpx.AsyncClient,
    fake_idp: FakeIdp,
    *,
    return_to: str = "/private",
    userinfo: dict[str, object] | None = None,
) -> httpx.Response:
    """Drives the whole `/auth/sign-in` → fake login → `/auth/callback`
    handshake and returns the callback's response, with the session cookie
    already set on `demo_client`'s jar."""
    sign_in = await demo_client.get("/auth/sign-in", params={"return_to": return_to})
    assert sign_in.status_code == 303
    location = httpx.URL(sign_in.headers["location"])
    assert location.params["client_id"] == CLIENT_ID
    assert location.params["code_challenge_method"] == "S256"

    code = fake_idp.issue_code(
        sub="usr_1",
        nonce=location.params["nonce"],
        userinfo={
            "email": "persona@example.test",
            "email_verified": True,
            "name": "Persona",
            **(userinfo or {}),
        },
    )
    return await demo_client.get(
        "/auth/callback", params={"code": code, "state": location.params["state"]}
    )


# --- `return_to` is confined to this origin ------------------------------------

# the same table the Node
# SDK's `safeTarget` answers. One property, one parametrized test per flow
#: a new spelling of "another origin" is a row here.
RETURN_TO_TABLE: tuple[tuple[str, str], ...] = (
    # accepted: an absolute path of this app, query and fragment included
    ("/private", "/private"),
    ("/", "/"),
    ("/a/b?c=1&d=2", "/a/b?c=1&d=2"),
    ("/a#frag", "/a#frag"),
    ("/@evil", "/@evil"),  # a path, not a userinfo separator — it starts with `/`
    # rejected → `/`
    ("https://evil.example/", "/"),
    ("http://evil.example", "/"),
    ("//evil.example", "/"),
    ("//evil.example/path", "/"),
    ("/\\evil.example", "/"),
    ("javascript:alert(1)", "/"),
    ("@evil.example", "/"),
    ("evil.example", "/"),
    ("private", "/"),
    ("", "/"),
    # a control character: a URL parser drops a tab or a line break, so these
    # would resolve to `//evil.example`
    ("/\t/evil.example", "/"),
    ("/\n/evil.example", "/"),
    ("/\r\n/evil.example", "/"),
    ("/a\tb", "/"),
    ("/a\x00b", "/"),
    ("/a\x7fb", "/"),
)


def _assert_deletes(response: httpx.Response, name: str) -> None:
    line = next(
        value for value in response.headers.get_list("set-cookie") if value.startswith(f"{name}=")
    )
    attributes = {part.strip().lower() for part in line.split(";")[1:]}
    assert "secure" in attributes
    assert "max-age=0" in attributes
    assert "path=/" in attributes
    assert "expires=thu, 01 jan 1970 00:00:00 gmt" in attributes


@pytest.mark.parametrize(("candidate", "expected"), RETURN_TO_TABLE)
def test_safe_target_confines_to_this_origin(candidate: str, expected: str) -> None:
    assert safe_target(candidate) == expected
    # `None` and the explicit fallback: `deny` builds the redirect with these.
    assert safe_target(None, "/x") == "/x"


@pytest.mark.parametrize(("candidate", "expected"), RETURN_TO_TABLE)
@pytest.mark.asyncio
async def test_sign_in_with_a_session_only_redirects_within_this_origin(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp, candidate: str, expected: str
) -> None:
    await _login(demo_client, fake_idp)
    response = await demo_client.get("/auth/sign-in", params={"return_to": candidate})
    assert response.status_code == 303
    assert response.headers["location"] == expected


@pytest.mark.parametrize(("candidate", "expected"), RETURN_TO_TABLE)
@pytest.mark.asyncio
async def test_callback_only_redirects_within_this_origin(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp, candidate: str, expected: str
) -> None:
    # No session yet: the destination travels sealed in the transaction and
    # is honoured after the callback — that path must be confined too.
    response = await _login(demo_client, fake_idp, return_to=candidate)
    assert response.status_code == 303
    assert response.headers["location"] == expected


# --- the routes ------------------------------------------------------------


@pytest.mark.asyncio
async def test_sign_in_redirects_to_the_authorize_endpoint(demo_client: httpx.AsyncClient) -> None:
    response = await demo_client.get("/auth/sign-in", params={"return_to": "/private"})
    assert response.status_code == 303
    location = httpx.URL(response.headers["location"])
    assert str(location).startswith(f"{ISSUER}/oidc/authorize")
    assert demo_client.cookies.get("__Host-stwrd_tx") is not None


@pytest.mark.parametrize(
    "extra",
    [
        {"hint": "ana@example.com", "ui_locales": "es"},
        {"prompt": "none", "max_age": "0", "scope": "admin", "acr_values": "2"},
        {"organization_id": "00000000-0000-4000-8000-000000000000", "next": "/elsewhere"},
    ],
)
@pytest.mark.asyncio
async def test_sign_in_forwards_no_query_parameter_to_the_authorize_endpoint(
    demo_client: httpx.AsyncClient, extra: dict[str, str]
) -> None:
    """Only the destination (`return_to`) is read; nothing else the visitor
    puts on the link reaches the authorization request."""
    baseline = await demo_client.get("/auth/sign-in", params={"return_to": "/private"})
    expected = httpx.URL(baseline.headers["location"]).params
    # Negative control: the baseline really is an authorize request, so the
    # comparison of keys below can fail if a parameter leaks.
    assert {"state", "nonce", "code_challenge", "scope"} <= set(expected.keys())

    response = await demo_client.get("/auth/sign-in", params={"return_to": "/private", **extra})
    assert response.status_code == 303
    sent = httpx.URL(response.headers["location"]).params
    assert set(sent.keys()) == set(expected.keys())
    assert sent["scope"] == expected["scope"]


@pytest.mark.asyncio
async def test_callback_opens_a_session_and_redirects_to_return_to(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    response = await _login(demo_client, fake_idp, return_to="/private")
    assert response.status_code == 303
    assert response.headers["location"] == "/private"
    assert demo_client.cookies.get("__Host-stwrd_session") is not None
    assert demo_client.cookies.get("__Host-stwrd_tx") is None  # cleared
    # Deleted with `Secure` and `Max-Age=0`: a browser refuses to delete a
    # `__Host-` cookie that is not `Secure`.
    _assert_deletes(response, "__Host-stwrd_tx")


@pytest.mark.asyncio
async def test_callback_rejects_a_state_that_does_not_match(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    sign_in = await demo_client.get("/auth/sign-in", params={"return_to": "/"})
    location = httpx.URL(sign_in.headers["location"])
    code = fake_idp.issue_code(sub="usr_1", nonce=location.params["nonce"])

    response = await demo_client.get(
        "/auth/callback", params={"code": code, "state": "not-the-right-state"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_callback_with_no_transaction_cookie_is_rejected(
    demo_client: httpx.AsyncClient,
) -> None:
    response = await demo_client.get("/auth/callback", params={"code": "x", "state": "y"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_me_reports_the_session_after_login(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    await _login(demo_client, fake_idp)
    response = await demo_client.get("/auth/session")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["authenticated"] is True
    assert body["user"]["id"] == "usr_1"
    assert body["user"]["email"] == "persona@example.test"
    assert body["csrf_token"]
    assert body["account_url"] == f"{ISSUER}/me"


@pytest.mark.asyncio
async def test_me_reports_consents_from_userinfo(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    # The app sees state, not versions: `consents` travels through userinfo
    # like any other claim this SDK didn't invent, and defaults to `{}` when
    # userinfo carries none.
    await _login(
        demo_client, fake_idp, userinfo={"consents": {"terms": "accepted", "marketing": "pending"}}
    )
    response = await demo_client.get("/auth/session")
    body = response.json()
    assert body["consents"] == {"terms": "accepted", "marketing": "pending"}


@pytest.mark.asyncio
async def test_me_without_a_session_has_the_same_shape(demo_client: httpx.AsyncClient) -> None:
    # The shape does not change — same keys, `authenticated: false`.
    response = await demo_client.get("/auth/session")
    body = response.json()
    assert body == {
        "authenticated": False,
        "user": None,
        "csrf_token": None,
        "organization": None,
        "consents": {},
        "account_url": f"{ISSUER}/me",
    }


@pytest.mark.asyncio
async def test_sign_out_requires_csrf(demo_client: httpx.AsyncClient, fake_idp: FakeIdp) -> None:
    await _login(demo_client, fake_idp)
    response = await demo_client.post("/auth/sign-out")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_sign_out_clears_the_session_with_a_valid_csrf(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    await _login(demo_client, fake_idp)
    me = (await demo_client.get("/auth/session")).json()

    response = await demo_client.post("/auth/sign-out", headers={"x-csrf-token": me["csrf_token"]})
    assert response.status_code == 303
    # No `end_session_endpoint` advertised (fake_idp default): degrades to
    # the local post-logout redirect.
    assert response.headers["location"] == f"{BASE_URL}/"
    assert demo_client.cookies.get("__Host-stwrd_session") is None
    _assert_deletes(response, "__Host-stwrd_session")

    after = (await demo_client.get("/auth/session")).json()
    assert after["authenticated"] is False


@pytest.mark.asyncio
async def test_sign_out_with_no_session_redirects_without_requiring_csrf(
    demo_client: httpx.AsyncClient,
) -> None:
    response = await demo_client.post("/auth/sign-out")
    assert response.status_code == 303


@pytest.mark.asyncio
async def test_sign_out_goes_to_end_session_when_advertised(stwrd_config: StwrdConfig) -> None:
    fake_idp = FakeIdp(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=stwrd_config.redirect_uri,
        advertise_end_session=True,
    )
    idp_transport = httpx.ASGITransport(app=fake_idp.app)
    async with httpx.AsyncClient(transport=idp_transport, base_url=ISSUER) as idp_client:
        instance = Stwrd(stwrd_config, http_client=idp_client)
        try:
            app = _build_demo_app(instance)
            demo_transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=demo_transport, base_url=BASE_URL, follow_redirects=False
            ) as demo_client:
                await _login(demo_client, fake_idp)
                me = (await demo_client.get("/auth/session")).json()
                response = await demo_client.post(
                    "/auth/sign-out", headers={"x-csrf-token": me["csrf_token"]}
                )
                assert response.status_code == 303
                assert response.headers["location"].startswith(f"{ISSUER}/oidc/end-session")
        finally:
            await instance.close()


@pytest.mark.asyncio
async def test_webhook_without_a_secret_configured_is_503(
    stwrd_config: StwrdConfig, idp_http_client: httpx.AsyncClient
) -> None:
    instance = Stwrd(stwrd_config.replace(webhook_secret=""), http_client=idp_http_client)
    try:
        app = _build_demo_app(instance)
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=BASE_URL) as client:
            response = await client.post("/auth/webhook", content=b"{}")
            assert response.status_code == 503
            assert response.json() == {"error": "webhook_not_configured"}
    finally:
        await instance.close()


@pytest.mark.asyncio
async def test_webhook_rejects_a_bad_signature(demo_client: httpx.AsyncClient) -> None:
    response = await demo_client.post(
        "/auth/webhook",
        content=b'{"id":"x","type":"user.created","api_version":"v1","created_at":"2026-01-01T00:00:00Z","data":{}}',
        headers={
            "webhook-id": "x",
            "webhook-timestamp": "123",
            "webhook-signature": "v1,not-a-real-signature==",
        },
    )
    assert response.status_code == 400
    assert response.json() == {"error": "invalid_signature"}


@pytest.mark.asyncio
async def test_back_channel_rejects_a_missing_token(demo_client: httpx.AsyncClient) -> None:
    response = await demo_client.post("/auth/back-channel")
    assert response.status_code == 400
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_back_channel_accepts_a_well_formed_logout_token(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    import time

    from stwrd.oidc import LOGOUT_EVENT_URI, half_hash

    now = int(time.time())
    token = fake_idp.sign(
        {
            "iss": ISSUER,
            "aud": [CLIENT_ID],
            "iat": now,
            "exp": now + 120,
            "jti": "logout-1",
            "sid": "s1",
            "events": {LOGOUT_EVENT_URI: {}},
        }
    )
    response = await demo_client.post("/auth/back-channel", data={"logout_token": token})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # A replay of the same `jti` is rejected.
    replay = await demo_client.post("/auth/back-channel", data={"logout_token": token})
    assert replay.status_code == 400
    _ = half_hash  # imported only to document where the claim shape comes from


@pytest.mark.asyncio
async def test_back_channel_actually_ends_the_local_session(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp, stwrd: Stwrd
) -> None:
    """The property, not the 200 response: the IdP's notice has to leave the
    local session dead.

    Validating the token and answering "ok" without ending anything is exactly
    the failure mode that made back-channel logout useless: the IdP believes
    it closed the session and the app keeps letting the user through until the
    access token expires. The local id is derived from the `sid`
    (`Stwrd.session_id_for_sid`), which is why the store protocol's
    `delete(id)` is enough.
    """
    import time

    from stwrd.oidc import LOGOUT_EVENT_URI
    from stwrd.sessions import StwrdSession, Tokens

    sid = "s-live"
    session_id = stwrd.session_id_for_sid(sid)
    now = time.time()
    await stwrd.sessions.set(
        StwrdSession(
            id=session_id,
            sid_idp=sid,
            sub="user-1",
            claims={"sub": "user-1", "sid": sid},
            tokens=Tokens(
                access_token="a", id_token="i", token_type="Bearer", expires_at=now + 600
            ),
            expires_at=now + 600,
            access_expires_at=now + 600,
        )
    )
    assert await stwrd.sessions.get(session_id) is not None

    token = fake_idp.sign(
        {
            "iss": ISSUER,
            "aud": [CLIENT_ID],
            "iat": int(now),
            "exp": int(now) + 120,
            "jti": "logout-kills",
            "sid": sid,
            "events": {LOGOUT_EVENT_URI: {}},
        }
    )
    response = await demo_client.post("/auth/back-channel", data={"logout_token": token})

    assert response.status_code == 200
    assert await stwrd.sessions.get(session_id) is None, (
        "the notice was validated and answered ok, but the local session is still alive"
    )


@pytest.mark.asyncio
async def test_back_channel_failed_deletion_leaves_the_jti_unseen_so_the_retry_works(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp, stwrd: Stwrd
) -> None:
    """The issuer retries a 5xx but not a 4xx: if the `jti` were marked before
    the deletion, the retry would get a 400 "replay" and the local session
    would stay alive forever."""
    from stwrd.oidc import LOGOUT_EVENT_URI
    from stwrd.sessions import StwrdSession, Tokens

    sid = "s-retry"
    session_id = stwrd.session_id_for_sid(sid)
    now = time.time()
    await stwrd.sessions.set(
        StwrdSession(
            id=session_id,
            sid_idp=sid,
            sub="user-1",
            claims={"sub": "user-1", "sid": sid},
            tokens=Tokens(
                access_token="a", id_token="i", token_type="Bearer", expires_at=now + 600
            ),
            expires_at=now + 600,
            access_expires_at=now + 600,
        )
    )

    real_delete = stwrd.sessions.delete
    failures_left = [1]

    async def flaky_delete(id: str) -> None:
        if failures_left[0] > 0:
            failures_left[0] -= 1
            raise RuntimeError("store down")
        await real_delete(id)

    stwrd.sessions.delete = flaky_delete  # type: ignore[method-assign]

    token = fake_idp.sign(
        {
            "iss": ISSUER,
            "aud": [CLIENT_ID],
            "iat": int(now),
            "exp": int(now) + 120,
            "jti": "logout-retry",
            "sid": sid,
            "events": {LOGOUT_EVENT_URI: {}},
        }
    )
    # The unhandled store error is what the server turns into a 500.
    with pytest.raises(RuntimeError, match="store down"):
        await demo_client.post("/auth/back-channel", data={"logout_token": token})
    assert await stwrd.sessions.get(session_id) is not None

    retry = await demo_client.post("/auth/back-channel", data={"logout_token": token})
    assert retry.status_code == 200
    assert await stwrd.sessions.get(session_id) is None

    # Once the session is really gone the jti is burned: a third delivery is a replay.
    third = await demo_client.post("/auth/back-channel", data={"logout_token": token})
    assert third.status_code == 400


# --- dependencies ----------------------------------------------------------


@pytest.mark.asyncio
async def test_optional_user_is_none_without_a_session(demo_client: httpx.AsyncClient) -> None:
    response = await demo_client.get("/whoami")
    assert response.json() == {"sub": None}


@pytest.mark.asyncio
async def test_optional_user_after_login(demo_client: httpx.AsyncClient, fake_idp: FakeIdp) -> None:
    await _login(demo_client, fake_idp)
    response = await demo_client.get("/whoami")
    assert response.json() == {"sub": "usr_1"}


@pytest.mark.asyncio
async def test_current_user_redirects_a_navigation_without_a_session(
    demo_client: httpx.AsyncClient,
) -> None:
    response = await demo_client.get("/private", headers={"accept": "text/html"})
    assert response.status_code == 303
    assert "/auth/sign-in" in response.headers["location"]


@pytest.mark.asyncio
async def test_current_user_answers_401_json_for_a_non_navigation(
    demo_client: httpx.AsyncClient,
) -> None:
    response = await demo_client.get("/private", headers={"accept": "application/json"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_current_user_returns_the_user_once_signed_in(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    await _login(demo_client, fake_idp)
    response = await demo_client.get("/private")
    assert response.status_code == 200
    assert response.json() == {"sub": "usr_1"}


@pytest.mark.asyncio
async def test_require_auth_guards_without_returning_a_user(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp
) -> None:
    denied = await demo_client.get("/guarded", headers={"accept": "application/json"})
    assert denied.status_code == 401

    await _login(demo_client, fake_idp)
    allowed = await demo_client.get("/guarded")
    assert allowed.status_code == 200


# --- protect() ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_protect_allows_the_public_allowlist_and_the_auth_prefix(stwrd: Stwrd) -> None:
    app = _build_demo_app(stwrd, protected=True)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=BASE_URL, follow_redirects=False
    ) as client:
        assert (await client.get("/public/info")).status_code == 200
        # Everything under the auth prefix is public without being listed —
        # otherwise the redirect target itself would need a
        # session, and the webhook receiver would 401 forever.
        me = await client.get("/auth/session")
        assert me.status_code == 200


@pytest.mark.asyncio
async def test_protect_denies_everything_else_by_default(stwrd: Stwrd) -> None:
    app = _build_demo_app(stwrd, protected=True)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=BASE_URL, follow_redirects=False
    ) as client:
        navigation = await client.get("/needs-session", headers={"accept": "text/html"})
        assert navigation.status_code == 303
        assert "/auth/sign-in" in navigation.headers["location"]

        api_call = await client.get("/needs-session", headers={"accept": "application/json"})
        assert api_call.status_code == 401


# --- a silent IdP: no entry point turns it into "no session" ---------------


async def _due_for_renewal(stwrd: Stwrd) -> str:
    """Leave the freshly created session with an expired access token and a
    refresh token, the only state in which a request needs the IdP.

    The value of the refresh token does not matter — the IdP goes silent
    before anyone looks at it — so none the fake knows is built: what is
    exercised is what each entry point does when the call does not arrive, not
    what the IdP answers. Returns the session `id` so it can be checked
    afterwards that it is still there.
    """
    session_id = next(iter(stwrd.sessions._sessions))  # type: ignore[attr-defined]
    stored = await stwrd.sessions.get(session_id)
    assert stored is not None
    past = time.time() - 1
    await stwrd.sessions.set(
        dataclasses.replace(
            stored,
            tokens=dataclasses.replace(
                stored.tokens, expires_at=past, refresh_token="rt-nobody-will-look"
            ),
            access_expires_at=past,
        )
    )
    return session_id


def _silence_the_idp(stwrd: Stwrd) -> None:
    """Make the IdP refuse connections, AFTER the login."""

    class _BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused", request=request)

    stwrd.oidc._http = httpx.AsyncClient(transport=_BrokenTransport(), base_url=ISSUER)


#: The entry points through which a request with a live session goes through
#: `resolve_session`, and what each one answered BEFORE silence was told apart
#: from rejection. The second column is what did the damage: each one had its
#: own way of telling "you are gone" to someone who had not gone anywhere.
ENTRY_POINTS = [
    pytest.param(
        "/whoami", "optional_user returned None: the page rendered anonymous", id="optional_user"
    ),
    pytest.param(
        "/private",
        "current_user answered 401: the person was sent back to sign-in",
        id="current_user",
    ),
    pytest.param("/guarded", "require_auth answered 401", id="require_auth"),
    pytest.param("/auth/session", "/auth/session said authenticated:false", id="/auth/session"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("path,damage", ENTRY_POINTS)
async def test_no_door_turns_a_silent_idp_into_a_lost_session(
    stwrd: Stwrd, fake_idp: FakeIdp, demo_client: httpx.AsyncClient, path: str, damage: str
) -> None:
    """With a live session and a silent IdP, **every** entry point answers 503.

    Parametrized over the entry points rather than one test each because it is
    ONE property: "cannot tell" is never translated to "no session". Each one
    broke it in its own way — `optional_user` returning `None`, `current_user`
    with a 401 that sends the person to sign-in, `/auth/session` with
    `authenticated: false` that draws the sign-in screen for someone already
    inside — and all of them are the same defect.

    And the session **stays in the store** at the end: if an entry point
    deleted it, the 503 would be honest and the damage would be done anyway.
    """
    await _login(demo_client, fake_idp, return_to="/private")
    session_id = await _due_for_renewal(stwrd)
    _silence_the_idp(stwrd)
    response = await demo_client.get(path)

    assert response.status_code == 503, (
        f"{path} answered {response.status_code} with a silent IdP. Before: {damage}"
    )
    assert await stwrd.sessions.get(session_id) is not None, (
        f"{path} deleted the local session over a network failure"
    )


@pytest.mark.asyncio
async def test_the_protect_middleware_does_not_bounce_a_live_session_to_the_login(
    stwrd: Stwrd, fake_idp: FakeIdp
) -> None:
    """The fifth entry point, which is not a dependency but the middleware, and
    which used to bounce to sign-in with a 303 — the most visible form of the
    defect: the person sees the sign-in screen and believes their session
    ended."""
    app = _build_demo_app(stwrd, protected=True)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url=BASE_URL, follow_redirects=False
    ) as client:
        await _login(client, fake_idp, return_to="/needs-session")
        session_id = await _due_for_renewal(stwrd)
        _silence_the_idp(stwrd)
        response = await client.get("/needs-session")

    assert response.status_code == 503, (
        f"the middleware answered {response.status_code}: a 303 to sign-in tells "
        "someone with a live session that they lost it"
    )
    assert await stwrd.sessions.get(session_id) is not None


@pytest.mark.asyncio
async def test_back_channel_answers_503_not_400_when_the_jwks_is_unreachable(
    stwrd: Stwrd, fake_idp: FakeIdp, demo_client: httpx.AsyncClient
) -> None:
    """A transport failure or a 5xx while fetching the JWKS answers 5xx (which
    the issuer does retry), not 400. The issuer does NOT retry a 4xx: if this
    endpoint answered 400 because it could not fetch the JWKS, the sign-out
    notice would be lost forever and the local session would stay alive until
    it expires on its own. The Node SDK's router has the same lock.
    """
    from stwrd.oidc import LOGOUT_EVENT_URI

    now = int(time.time())
    token = fake_idp.sign(
        {
            "iss": ISSUER,
            "aud": [CLIENT_ID],
            "iat": now,
            "exp": now + 120,
            "jti": "logout-silent",
            "sid": "s-any",
            "events": {LOGOUT_EVENT_URI: {}},
        }
    )
    _silence_the_idp(stwrd)

    response = await demo_client.post("/auth/back-channel", data={"logout_token": token})

    assert response.status_code == 503, (
        f"answered {response.status_code}: a 4xx here loses the notice forever"
    )
    assert response.json() == {"error": "idp_unavailable"}
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.asyncio
async def test_back_channel_rejects_a_genuinely_invalid_token_with_400(
    demo_client: httpx.AsyncClient,
) -> None:
    """The contrast with the test above: a `logout_token` the IdP never signed
    is still a rejection, not silence, and the issuer has no reason to retry
    it."""
    response = await demo_client.post("/auth/back-channel", data={"logout_token": "not-a-jwt"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_previous_browser_endpoint_is_absent(demo_client):
    assert (await demo_client.get("/auth/me")).status_code == 404


@pytest.mark.asyncio
async def test_browser_session_exact_allowlist_and_no_userinfo_authority(demo_client, fake_idp):
    await _login(
        demo_client,
        fake_idp,
        userinfo={"roles": ["admin"], "permissions": ["write"], "sid": "evil"},
    )
    body = (await demo_client.get("/auth/session")).json()
    assert set(body) == {
        "authenticated",
        "user",
        "organization",
        "consents",
        "csrf_token",
        "account_url",
    }
    assert set(body["user"]) == {
        "id",
        "email",
        "email_verified",
        "display_name",
        "avatar_url",
        "roles",
        "permissions",
    }
    assert body["user"]["roles"] == []
    assert body["organization"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "claims,status",
    [
        ({"roles": ["reader"], "permissions": []}, 200),
        (
            {
                "org_id": "o",
                "org_display_name": "Org",
                "org_roles": ["reader"],
                "org_permissions": [],
            },
            200,
        ),
        ({"roles": ["reader"], "permissions": [], "org_roles": ["reader"]}, 403),
        ({"org_roles": ["reader"]}, 403),
    ],
)
async def test_role_guard_uses_complete_coherent_session(stwrd, claims, status):
    from stwrd import StwrdSession, Tokens
    from stwrd.fastapi import require_role

    now = time.time()
    stored = StwrdSession(
        id="s",
        sid_idp=None,
        sub="u",
        claims={"sub": "u", **claims},
        tokens=Tokens("a", "i", "Bearer", now + 100),
        expires_at=now + 100,
        access_expires_at=now + 100,
    )
    await stwrd.sessions.set(stored)
    app = FastAPI()

    @app.get("/")
    async def guarded(user: StwrdUser = Depends(require_role(stwrd, "reader"))):
        return {"id": user.id, "roles": user.roles}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=BASE_URL
    ) as browser:
        browser.cookies.set(stwrd.config.session_cookie, stwrd.seal({"sid": "s"}))
        response = await browser.get("/")
    assert response.status_code == status
    if status == 200 and "org_id" in claims:
        assert response.json() == {"id": "u", "roles": []}


def test_require_org_rejects_configuration_without_org_scope(stwrd_config):
    from stwrd import ConfigError
    from stwrd.fastapi import require_org

    with pytest.raises(ConfigError):
        require_org(Stwrd(stwrd_config))


@pytest.mark.asyncio
@pytest.mark.parametrize("subject", [None, "", 42, {}, []])
async def test_callback_bad_subject_rejected_before_persistence_or_jit(
    stwrd, fake_idp, monkeypatch, subject
):
    registrations = []
    writes = []
    original_set = stwrd.sessions.set

    async def track_set(session):
        writes.append(session)
        await original_set(session)

    async def invalid_claims(*args, **kwargs):
        return {"sub": subject}

    async def invalid_userinfo(*args, **kwargs):
        return {"sub": subject}

    monkeypatch.setattr(stwrd.sessions, "set", track_set)
    monkeypatch.setattr(stwrd.oidc, "validate_id_token", invalid_claims)
    monkeypatch.setattr(stwrd.oidc, "userinfo", invalid_userinfo)
    app = FastAPI()
    app.include_router(auth_router(stwrd, on_user_registered=registrations.append))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=BASE_URL
    ) as browser:
        response = await _login(browser, fake_idp)
    assert response.status_code == 400
    assert writes == []
    assert registrations == []


@pytest.mark.asyncio
async def test_browser_profile_malformed_values_have_safe_json_shape(demo_client, fake_idp):
    await _login(
        demo_client,
        fake_idp,
        userinfo={"email": 42, "name": {}, "picture": [], "email_verified": 1},
    )
    response = await demo_client.get("/auth/session")
    assert response.status_code == 200
    user = response.json()["user"]
    assert user["email"] is None
    assert user["display_name"] is None
    assert user["avatar_url"] is None
    assert user["email_verified"] is False


@pytest.mark.asyncio
async def test_sign_in_is_the_way_out_of_an_uncertain_refresh(
    demo_client: httpx.AsyncClient, fake_idp: FakeIdp, stwrd: Stwrd
) -> None:
    await _login(demo_client, fake_idp, userinfo={})
    old_cookie = demo_client.cookies.get("__Host-stwrd_session")
    sid = stwrd.unseal(old_cookie)["sid"]
    session = await stwrd.sessions.get(sid)
    await stwrd.sessions.set(
        dataclasses.replace(
            session,
            tokens=dataclasses.replace(session.tokens, refresh_token="rt"),
            access_expires_at=time.time() - 1,
        )
    )
    lease = await stwrd.sessions.claim_refresh(sid, "dead-worker", 30)
    await stwrd.sessions.mark_refresh_sent(sid, lease.fence)
    await stwrd.sessions.release_refresh(sid, lease.fence, sent=True)  # outcome unknown

    assert (await demo_client.get("/auth/session")).status_code == 503  # no authority
    started = await demo_client.get("/auth/sign-in", params={"return_to": "/private"})
    assert started.status_code == 303
    assert str(started.headers["location"]).startswith(f"{ISSUER}/oidc/authorize")
