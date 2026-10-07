"""BFF organization selection: list own organizations, start a switch through a
real authorization request, and replace the live session only when the callback
matches exactly."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from stwrd import Stwrd, StwrdConfig
from stwrd.fastapi import auth_router

from .fake_idp import ISSUER, FakeIdp
from .test_auth_router import BASE_URL, CLIENT_ID, CLIENT_SECRET, _login

ORG_A = str(uuid.uuid4())
ORG_B = str(uuid.uuid4())
ORG_OTHER = str(uuid.uuid4())


def _membership(org_id: str, name: str | None, active: bool = True) -> dict:
    return {"organization": {"id": org_id, "display_name": name}, "active": active}


@pytest.fixture
def org_config() -> StwrdConfig:
    return StwrdConfig(
        issuer=ISSUER,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        base_url=BASE_URL,
        cookie_secret="x" * 32,
        scope="openid profile email org",
    )


@pytest.fixture
async def org_stwrd(
    org_config: StwrdConfig, idp_http_client: httpx.AsyncClient
) -> AsyncIterator[Stwrd]:
    instance = Stwrd(org_config, http_client=idp_http_client)
    try:
        yield instance
    finally:
        await instance.close()


@pytest.fixture
async def client(org_stwrd: Stwrd) -> AsyncIterator[httpx.AsyncClient]:
    app = FastAPI()
    app.include_router(auth_router(org_stwrd))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=BASE_URL, follow_redirects=False
    ) as browser:
        yield browser


async def _signed_in(client: httpx.AsyncClient, fake_idp: FakeIdp) -> str:
    fake_idp.memberships = [_membership(ORG_A, "Org A"), _membership(ORG_B, "Org B")]
    response = await _login(client, fake_idp, return_to="/")
    assert response.status_code == 303
    session = (await client.get("/auth/session")).json()
    return session["csrf_token"]


async def _start_switch(client: httpx.AsyncClient, csrf: str, org: str, **extra) -> httpx.Response:
    return await client.post(
        "/auth/organization", headers={"x-csrf-token": csrf}, json={"organization_id": org, **extra}
    )


async def _finish_switch(
    client: httpx.AsyncClient, fake_idp: FakeIdp, started: httpx.Response, **issued
) -> httpx.Response:
    location = httpx.URL(started.headers["location"])
    code = fake_idp.issue_code(
        sub=issued.pop("sub", "usr_1"),
        nonce=location.params["nonce"],
        userinfo={
            "email": "persona@example.test",
            "email_verified": True,
            **issued.pop("userinfo", {}),
        },
        id_claims=issued.pop(
            "id_claims",
            {
                "org_id": location.params["organization_id"],
                "org_display_name": "Selected",
                "org_roles": ["member"],
                "org_permissions": [],
            },
        ),
    )
    return await client.get(
        "/auth/callback", params={"code": code, "state": location.params["state"]}
    )


async def test_lists_only_active_own_organizations_across_pages(client, fake_idp):
    csrf = await _signed_in(client, fake_idp)
    fake_idp.memberships = [
        _membership(ORG_A, "Org A"),
        _membership(ORG_OTHER, "Suspended", active=False),
        _membership(ORG_B, None),
    ]
    fake_idp.memberships_page_size = 1
    response = await client.get("/auth/organizations")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == {
        "organizations": [
            {"id": ORG_A, "display_name": "Org A", "current": False},
            {"id": ORG_B, "display_name": None, "current": False},
        ]
    }
    assert set(fake_idp.membership_authorizations) == {fake_idp.membership_authorizations[0]}
    assert fake_idp.membership_authorizations[0].startswith("Bearer ")
    assert csrf


async def test_requires_a_session_and_the_explicit_org_scope(
    client, fake_idp, stwrd_config, idp_http_client
):
    assert (await client.get("/auth/organizations")).status_code == 401
    assert (await client.post("/auth/organization", json={})).status_code == 401
    plain = Stwrd(stwrd_config, http_client=idp_http_client)  # default scope has no `org`
    app = FastAPI()
    app.include_router(auth_router(plain))
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url=BASE_URL
    ) as other:
        assert (await other.get("/auth/organizations")).status_code == 404
        assert (await other.post("/auth/organization", json={})).status_code == 404
    await plain.close()


async def test_idp_silence_is_503_not_an_empty_list(client, fake_idp):
    await _signed_in(client, fake_idp)
    fake_idp.memberships_status = 502
    assert (await client.get("/auth/organizations")).status_code == 503
    fake_idp.memberships_status = 403
    assert (await client.get("/auth/organizations")).status_code == 503


@pytest.mark.parametrize(
    "advertised",
    [
        {"management_base_url": "http://idp.example.com/api/v1"},
        {"management_audience": "https://other.test"},
    ],
)
async def test_untrusted_management_destination_never_receives_the_token(
    client, fake_idp, org_stwrd, advertised
):
    await _signed_in(client, fake_idp)
    for key, value in advertised.items():
        setattr(fake_idp, key, value)
    org_stwrd.oidc._discovery = None  # re-read discovery, as after a restart
    assert (await client.get("/auth/organizations")).status_code == 503
    assert fake_idp.membership_authorizations == []


async def test_switch_requires_csrf_a_uuid_and_a_current_membership(client, fake_idp):
    csrf = await _signed_in(client, fake_idp)
    assert (
        await client.post("/auth/organization", json={"organization_id": ORG_A})
    ).status_code == 403
    assert (await _start_switch(client, "wrong", ORG_A)).status_code == 403
    assert (await _start_switch(client, csrf, "not-a-uuid")).status_code == 400
    assert (await _start_switch(client, csrf, ORG_OTHER)).status_code == 404  # not a member
    assert client.cookies.get("__Host-stwrd_tx") is None


async def test_switch_starts_a_real_authorization_request_and_keeps_the_session(
    client, fake_idp, org_stwrd
):
    csrf = await _signed_in(client, fake_idp)
    before = client.cookies.get("__Host-stwrd_session")
    started = await _start_switch(client, csrf, ORG_B.upper(), return_to="https://evil.test/")
    assert started.status_code == 303
    location = httpx.URL(started.headers["location"])
    assert str(location).startswith(f"{ISSUER}/oidc/authorize")
    assert location.params["organization_id"] == ORG_B
    assert "org" in location.params["scope"].split()
    assert location.params["code_challenge_method"] == "S256"
    assert client.cookies.get("__Host-stwrd_tx") is not None
    assert client.cookies.get("__Host-stwrd_session") == before  # nothing replaced yet
    assert (await client.get("/auth/session")).json()["authenticated"] is True


async def test_form_post_also_starts_a_switch(client, fake_idp):
    csrf = await _signed_in(client, fake_idp)
    started = await client.post(
        "/auth/organization", data={"organization_id": ORG_A, "csrf_token": csrf}
    )
    assert started.status_code == 303
    assert httpx.URL(started.headers["location"]).params["organization_id"] == ORG_A


async def test_matching_callback_replaces_the_session_with_the_selected_organization(
    client, fake_idp, org_stwrd
):
    csrf = await _signed_in(client, fake_idp)
    old_cookie = client.cookies.get("__Host-stwrd_session")
    started = await _start_switch(client, csrf, ORG_B)
    finished = await _finish_switch(client, fake_idp, started)
    assert finished.status_code == 303 and finished.headers["location"] == "/"
    assert client.cookies.get("__Host-stwrd_tx") is None
    new_cookie = client.cookies.get("__Host-stwrd_session")
    assert new_cookie != old_cookie
    session = (await client.get("/auth/session")).json()
    assert session["organization"]["id"] == ORG_B
    # the previous session row is gone, not merely unreferenced
    old_payload = org_stwrd.unseal(old_cookie)
    assert await org_stwrd.sessions.get(old_payload["sid"]) is None


@pytest.mark.parametrize(
    "mismatch",
    [
        {"sub": "usr_other"},
        {
            "id_claims": {
                "org_id": ORG_A,
                "org_display_name": "A",
                "org_roles": [],
                "org_permissions": [],
            }
        },
        {"id_claims": {}},
    ],
    ids=["other person", "other organization", "no organization"],
)
async def test_a_callback_that_does_not_match_installs_nothing(
    client, fake_idp, org_stwrd, mismatch
):
    csrf = await _signed_in(client, fake_idp)
    old_cookie = client.cookies.get("__Host-stwrd_session")
    started = await _start_switch(client, csrf, ORG_B)
    finished = await _finish_switch(client, fake_idp, started, **mismatch)
    assert finished.status_code == 400
    assert client.cookies.get("__Host-stwrd_session") == old_cookie
    assert await org_stwrd.sessions.get(org_stwrd.unseal(old_cookie)["sid"]) is not None


async def test_logout_before_the_callback_is_never_undone(client, fake_idp, org_stwrd):
    csrf = await _signed_in(client, fake_idp)
    old_sid = org_stwrd.unseal(client.cookies.get("__Host-stwrd_session"))["sid"]
    started = await _start_switch(client, csrf, ORG_B)
    await org_stwrd.sessions.delete(old_sid)  # logout / back-channel logout
    finished = await _finish_switch(client, fake_idp, started)
    assert finished.status_code == 409
    assert (await client.get("/auth/session")).json()["authenticated"] is False


async def test_a_replayed_callback_cannot_install_a_second_session(client, fake_idp, org_stwrd):
    csrf = await _signed_in(client, fake_idp)
    started = await _start_switch(client, csrf, ORG_B)
    tx = client.cookies.get("__Host-stwrd_tx")
    assert (await _finish_switch(client, fake_idp, started)).status_code == 303
    client.cookies.set("__Host-stwrd_tx", tx, domain="demo.test", path="/")
    replay = await _finish_switch(client, fake_idp, started)
    assert replay.status_code == 409
