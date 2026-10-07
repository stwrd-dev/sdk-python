"""Observable properties of the Management transport; no generated resource catalogue."""

import httpx
import pytest

from stwrd import management
from stwrd.management import (
    ManagementError,
    ManagementProtocolError,
    ManagementTransport,
    WriteOptions,
)

from .test_management import Idp, client_for, error, options


async def test_acquisition_latency_cannot_authorize_write_with_already_expired_token(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(management, "_now", lambda: now[0])
    idp = Idp()
    original = idp.handle

    async def handle(request):
        response = await original(request)
        if request.url.path == "/oidc/token":
            now[0] = 10.0
        return response

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with ManagementTransport(options(), http_client=http) as transport:
            with pytest.raises(ManagementProtocolError):
                await transport.request("POST", "/users", {"name": "not-sent"})
    assert not any(request.url.path.startswith("/api/v1/") for request in idp.requests)


async def test_confirmation_requires_explicit_second_call_with_same_intent():
    idp = Idp()
    writes = []

    async def api(request):
        writes.append(request)
        if len(writes) == 1:
            return httpx.Response(
                409, json={**error("confirmation_required"), "confirmation_token": "next"}
            )
        return httpx.Response(204)

    idp.api = api
    async with client_for(idp) as http:
        async with ManagementTransport(options(), http_client=http) as transport:
            with pytest.raises(ManagementError) as failure:
                await transport.request(
                    "DELETE",
                    "/users/person",
                    {"reason": "chosen"},
                    WriteOptions(if_match='"v1"', idempotency_key="intent"),
                )
            assert len(writes) == 1
            result = await transport.request(
                "DELETE",
                "/users/person",
                {"reason": "chosen"},
                WriteOptions(
                    if_match='"v1"',
                    idempotency_key="intent",
                    confirmation_token=failure.value.body["confirmation_token"],
                ),
            )
            assert result.data is None
    assert len(writes) == 2
    assert writes[0].content == writes[1].content
    assert writes[0].headers["Idempotency-Key"] == writes[1].headers["Idempotency-Key"] == "intent"
    assert writes[0].headers["If-Match"] == writes[1].headers["If-Match"] == '"v1"'
    assert "Confirmation-Token" not in writes[0].headers
    assert writes[1].headers["Confirmation-Token"] == "next"


async def test_resume_cursor_cycle_rejected_before_any_item_is_exposed():
    idp = Idp()
    calls = []

    async def api(request):
        calls.append(request)
        return httpx.Response(
            200, json={"items": [{"id": "person"}], "page": {"next_cursor": "resume"}}
        )

    idp.api = api
    yielded = []
    async with client_for(idp) as http:
        async with ManagementTransport(options(), http_client=http) as transport:
            with pytest.raises(ManagementProtocolError):
                async for item in transport.iterate(
                    "/users", query={"cursor": "resume", "q": "scope"}
                ):
                    yielded.append(item)
    assert yielded == [] and len(calls) == 1
    assert calls[0].url.params["cursor"] == "resume"
    assert calls[0].url.params["q"] == "scope"
