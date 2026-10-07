from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest

from stwrd import Stwrd, StwrdConfig

from .fake_idp import ISSUER, FakeIdp

CLIENT_ID = "demo-client"
CLIENT_SECRET = "demo-secret"
BASE_URL = "https://demo.test"
REDIRECT_URI = f"{BASE_URL}/auth/callback"


@pytest.fixture
def fake_idp() -> FakeIdp:
    return FakeIdp(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)


@pytest.fixture
async def idp_http_client(fake_idp: FakeIdp) -> AsyncIterator[httpx.AsyncClient]:
    # `httpx.ASGITransport` only ever implements `handle_async_request` — see
    # `stwrd/oidc.py`'s module docstring — so the injected client has to be
    # `httpx.AsyncClient`, never the sync `httpx.Client`.
    transport = httpx.ASGITransport(app=fake_idp.app)
    async with httpx.AsyncClient(transport=transport, base_url=ISSUER) as client:
        yield client


@pytest.fixture
def stwrd_config() -> StwrdConfig:
    return StwrdConfig(
        issuer=ISSUER,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        base_url=BASE_URL,
        cookie_secret="x" * 32,
        webhook_secret="whsec-shared-test-secret",
    )


@pytest.fixture
async def stwrd(
    stwrd_config: StwrdConfig, idp_http_client: httpx.AsyncClient
) -> AsyncIterator[Stwrd]:
    instance = Stwrd(stwrd_config, http_client=idp_http_client)
    try:
        yield instance
    finally:
        await instance.close()
