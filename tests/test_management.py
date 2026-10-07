"""Observable credential confinement, concurrency, effect ownership and cursor guards."""

import asyncio
import base64
import json
from urllib.parse import parse_qs

import httpx
import pytest

from stwrd import management
from stwrd.management import (
    ManagementConfigError,
    ManagementError,
    ManagementOptions,
    ManagementProtocolError,
    ManagementTransport,
    MultipartInput,
    WriteOptions,
)

ISSUER = "https://login.example.test"
ACCOUNT = "https://account.example.test"
SECRET = "secret:with unicode ☃"


def document(**patch):
    return {
        "issuer": ISSUER,
        "token_endpoint": ISSUER + "/oidc/token",
        "management_api_base_url": ACCOUNT + "/api/v1",
        "management_api_audience": ACCOUNT,
        **patch,
    }


def error(code="invalid_request"):
    return {
        "error": {
            "code": code,
            "message": "Safe server message",
            "request_id": "body-request",
            "details": [],
        }
    }


class Idp:
    def __init__(self, doc=None):
        self.doc = doc or document()
        self.requests = []
        self.tokens = 0
        self.api = None
        self.token_status = 200
        self.token_expires = 10
        self.redirect = None

    async def handle(self, request):
        self.requests.append(request)
        await asyncio.sleep(0)
        if self.redirect == request.url.path:
            return httpx.Response(307, headers={"Location": "https://attacker.invalid/stolen"})
        if request.url.path == "/.well-known/openid-configuration":
            return httpx.Response(200, json=self.doc, headers={"Cache-Control": "max-age=30"})
        if request.url.path == "/oidc/token":
            self.tokens += 1
            return httpx.Response(
                self.token_status,
                content=json.dumps(
                    {
                        "access_token": f"token{self.tokens}",
                        "token_type": "Bearer",
                        "expires_in": self.token_expires,
                    }
                ).encode(),
                headers={"Content-Type": "application/json"},
            )
        if self.api:
            return await self.api(request)
        return httpx.Response(
            200,
            json={"id": "resource"},
            headers={"ETag": '"revision"', "X-Request-ID": "header-request"},
        )


def client_for(idp):
    return httpx.AsyncClient(
        transport=httpx.MockTransport(idp.handle),
        follow_redirects=True,
        headers={
            "Authorization": "Bearer injected",
            "Cookie": "injected=session",
            "Host": "attacker.invalid",
        },
        auth=httpx.BasicAuth("injected", "secret"),
    )


def options(scopes=None):
    return ManagementOptions(ISSUER, "management-client", SECRET, scopes=scopes)


@pytest.mark.parametrize(
    "patch",
    [
        {"issuer": "https://other.invalid"},
        {"token_endpoint": "https://attacker.invalid/token"},
        {"token_endpoint": "https://login.example.test:0/oidc/token"},
        {"token_endpoint": "https://login.example.test:8443/oidc/token"},
        {"token_endpoint": "http://login.example.test/token"},
        {"management_api_base_url": ACCOUNT + "/elsewhere"},
        {"management_api_audience": "https://user:password@account.example.test"},
        {"management_api_audience": ACCOUNT + "#fragment"},
    ],
)
async def test_invalid_discovery_never_receives_credentials(patch):
    idp = Idp(document(**patch))
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises((ManagementProtocolError, ManagementConfigError)):
            await transport.request("GET", "/users")
    assert len(idp.requests) == 1
    assert (
        "Authorization" not in idp.requests[0].headers and "Cookie" not in idp.requests[0].headers
    )


@pytest.mark.parametrize(
    "destination", ["/.well-known/openid-configuration", "/oidc/token", "/api/v1/users"]
)
async def test_injected_redirect_setting_cannot_forward_credentials_or_write(destination):
    idp = Idp()
    idp.redirect = destination
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises(ManagementProtocolError, match="redirects"):
            await transport.request("POST", "/users", {"name": "once"})
    assert all(request.url.host != "attacker.invalid" for request in idp.requests)
    assert sum(request.url.path == "/api/v1/users" for request in idp.requests) <= 1


@pytest.mark.parametrize(
    "path",
    [
        "https://evil.invalid/users",
        "//evil.invalid",
        "/../users",
        "/%2e%2e/users",
        "/%252e%252e/users",
        "/users%2f..",
        "/users\\..",
        "/users?evil=x",
        "/users#fragment",
        "/%0ausers",
        "/users/%zz",
    ],
)
async def test_invalid_resource_path_rejected_before_discovery_or_token(path):
    idp = Idp()
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises(ManagementConfigError):
            await transport.request("POST", path, {"secret": SECRET})
    assert idp.requests == []


async def test_concurrent_calls_share_token_and_registered_scope_defaults():
    idp = Idp()
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        results = await asyncio.gather(*(transport.request("GET", "/users") for _ in range(20)))
    assert idp.tokens == 1
    assert sum(request.url.path.endswith("openid-configuration") for request in idp.requests) == 1
    token = next(request for request in idp.requests if request.url.path == "/oidc/token")
    assert parse_qs(token.content.decode()) == {"grant_type": ["client_credentials"]}
    assert (
        base64.b64decode(token.headers["Authorization"].split(" ")[1]).decode()
        == "management-client:secret%3Awith%20unicode%20%E2%98%83"
    )
    assert all(
        result.etag == '"revision"' and result.request_id == "header-request" for result in results
    )
    assert all("Cookie" not in request.headers for request in idp.requests)
    assert all(request.headers["Host"] == request.url.netloc.decode() for request in idp.requests)
    assert all(
        request.url.host == "account.example.test"
        and request.headers["Authorization"] == "Bearer token1"
        for request in idp.requests
        if request.url.path.startswith("/api/v1/")
    )


async def test_explicit_scopes_are_snapshotted_without_oidc_defaults():
    scopes = ["mgmt:users:read"]
    config = options(scopes)
    scopes.append("mgmt:users:write")
    idp = Idp()
    async with client_for(idp) as http, ManagementTransport(config, http_client=http) as transport:
        await transport.request("GET", "/users")
    token = next(request for request in idp.requests if request.url.path == "/oidc/token")
    assert parse_qs(token.content.decode())["scope"] == ["mgmt:users:read"]
    assert SECRET not in repr(config)


async def test_refresh503_never_sends_expired_bearer(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(management, "_now", lambda: now[0])
    idp = Idp()
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        await transport.request("GET", "/users")
        now[0] = 10.0
        idp.token_status = 503
        with pytest.raises(ManagementError) as failure:
            await transport.request("POST", "/users", {"name": "not-sent"})
        assert failure.value.status == 503
        assert sum(request.url.path == "/api/v1/users" for request in idp.requests) == 1
        idp.token_status = 200
        await transport.request("GET", "/users")
    assert idp.requests[-1].headers["Authorization"] == "Bearer token3"


async def test_401_evicts_token_without_replaying_write():
    idp = Idp()
    writes = []

    async def api(request):
        writes.append(request)
        return httpx.Response(
            401 if len(writes) == 1 else 200,
            json=error("invalid_token"),
            headers={"X-Request-ID": "correlation"},
        )

    idp.api = api
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises(ManagementError) as failure:
            await transport.request(
                "POST", "/users", {"name": "one"}, WriteOptions(idempotency_key="intent")
            )
        assert len(writes) == 1 and failure.value.request_id == "correlation"
        await transport.request("GET", "/users")
    assert idp.tokens == 2 and writes[0].headers["Idempotency-Key"] == "intent"
    assert writes[1].headers["Authorization"] == "Bearer token2"


async def test_late401_does_not_evict_newer_token(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(management, "_now", lambda: now[0])
    entered = asyncio.Event()
    release = asyncio.Event()
    idp = Idp()

    async def api(request):
        if request.url.path.endswith("/old"):
            entered.set()
            await release.wait()
            return httpx.Response(401, json=error())
        return httpx.Response(200, json={"id": "new"})

    idp.api = api
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        first = asyncio.create_task(transport.request("GET", "/users/old"))
        await entered.wait()
        now[0] = 10.0
        await transport.request("GET", "/users/new")
        release.set()
        with pytest.raises(ManagementError):
            await first
        await transport.request("GET", "/users/new")
    assert idp.tokens == 2


async def test_binary_multipart_headers_and_typed_error_extensions():
    idp = Idp()
    bodies = []

    async def api(request):
        bodies.append(request)
        if request.method == "GET":
            return httpx.Response(
                200,
                content=b"%PDF-1.4 legal",
                headers={"Content-Type": "application/pdf", "ETag": '"pdf"'},
            )
        return httpx.Response(
            409, json={**error("confirmation_required"), "confirmation_token": "continuation"}
        )

    idp.api = api
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        result = await transport.request(
            "GET", "/consent-documents/digest", options=WriteOptions(response_type="bytes")
        )
        assert result.data == b"%PDF-1.4 legal" and result.etag == '"pdf"'
        with pytest.raises(ManagementError) as failure:
            await transport.request(
                "POST",
                "/applications/id/consents/id/versions",
                MultipartInput(
                    {"effective_at": "2026-10-06T00:00:00Z"},
                    {"document": ("legal.pdf", b"PDF", "application/pdf")},
                ),
                WriteOptions(
                    if_match='"term"',
                    idempotency_key="intent",
                    confirmation_token="confirm",
                    step_up_token="step",
                ),
            )
        assert (
            failure.value.code == "confirmation_required"
            and failure.value.request_id == "body-request"
        )
        assert failure.value.body["confirmation_token"] == "continuation"
        assert "continuation" not in str(failure.value) and SECRET not in str(failure.value)
    upload = bodies[-1]
    assert upload.headers["Content-Type"].startswith("multipart/form-data; boundary=")
    assert b'filename="legal.pdf"' in upload.content and b"effective_at" in upload.content
    assert [
        upload.headers[name]
        for name in ("If-Match", "Idempotency-Key", "Confirmation-Token", "X-Stwrd-Step-Up")
    ] == ['"term"', "intent", "confirm", "step"]


async def test_nullable_queries_omitted_and_arrays_repeated():
    idp = Idp()
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        await transport.request(
            "GET", "/users", query={"q": None, "include_total": True, "roles": ["one", None, "two"]}
        )
    assert idp.requests[-1].url.params.multi_items() == [
        ("include_total", "true"),
        ("roles", "one"),
        ("roles", "two"),
    ]


@pytest.mark.parametrize(
    "bad_page",
    [
        {"items": [{"id": "two"}], "page": {"next_cursor": "same"}},
        {"items": [{"id": "one"}], "page": {"next_cursor": None}},
        {"items": [{"id": "two"}], "page": {}},
    ],
)
async def test_iterator_rejects_cycles_duplicates_and_missing_cursor(bad_page):
    idp = Idp()
    calls = []

    async def api(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={"items": [{"id": "one"}], "page": {"next_cursor": "same"}}
            if len(calls) == 1
            else bad_page,
        )

    idp.api = api
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises(ManagementProtocolError):
            _ = [item async for item in transport.iterate("/users")]
    assert len(calls) == 2


async def test_iterator_uses_schema_derived_composite_identity():
    idp = Idp()
    calls = []

    async def api(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "items": [{"consent_id": "term", "version": len(calls)}],
                "page": {"next_cursor": "next" if len(calls) == 1 else None},
            },
        )

    idp.api = api
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        items = [
            item
            async for item in transport.iterate(
                "/applications/app/consents/term/versions",
                identity=lambda item: f"{item['consent_id']}:{item['version']}",
            )
        ]
    assert [item["version"] for item in items] == [1, 2] and calls[1].url.params["cursor"] == "next"


async def test_failed_concurrent_token_refresh_is_one_flight_and_never_replays():
    idp = Idp()
    idp.token_status = 503
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        results = await asyncio.gather(
            *(transport.request("POST", "/users", {"name": "not-sent"}) for _ in range(12)),
            return_exceptions=True,
        )
        assert all(
            isinstance(result, ManagementError) and result.status == 503 for result in results
        )
        assert idp.tokens == 1
        assert not any(request.url.path.startswith("/api/v1/") for request in idp.requests)
        idp.token_status = 200
        await transport.request("GET", "/users")
    assert idp.tokens == 2


async def test_cancelled_waiter_does_not_cancel_shared_token_acquisition():
    idp = Idp()
    entered, release = asyncio.Event(), asyncio.Event()
    original = idp.handle

    async def handle(request):
        if request.url.path == "/oidc/token":
            entered.set()
            await release.wait()
        return await original(request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with ManagementTransport(options(), http_client=http) as transport:
            first = asyncio.create_task(transport.request("GET", "/users"))
            await entered.wait()
            second = asyncio.create_task(transport.request("GET", "/users"))
            await asyncio.sleep(0)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            release.set()
            assert (await second).data["id"] == "resource"
    assert idp.tokens == 1


async def test_expired_discovery_rebinds_token_before_new_account_destination(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(management, "_now", lambda: now[0])
    idp = Idp()
    idp.token_expires = 600
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        await transport.request("GET", "/users")
        now[0] = 31.0
        idp.doc = document(
            management_api_audience="https://new-account.example.test",
            management_api_base_url="https://new-account.example.test/api/v1",
        )
        await transport.request("GET", "/users")
    assert idp.tokens == 2
    assert idp.requests[-1].url.host == "new-account.example.test"
    assert idp.requests[-1].headers["Authorization"] == "Bearer token2"


@pytest.mark.parametrize("expires", [True, 0, -1, None, float("inf"), "300"])
async def test_invalid_token_response_cannot_be_used_at_management_endpoint(expires):
    idp = Idp()
    idp.token_expires = expires
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises(ManagementProtocolError):
            await transport.request("POST", "/users", {"name": "not-sent"})
    assert not any(request.url.path.startswith("/api/v1/") for request in idp.requests)


async def test_network_error_never_retries_write_or_exposes_query_payload():
    from stwrd.management import ManagementUnavailable

    idp = Idp()
    writes = []

    async def api(request):
        writes.append(request)
        raise httpx.ReadTimeout("private payload " + SECRET)

    idp.api = api
    async with (
        client_for(idp) as http,
        ManagementTransport(options(), http_client=http) as transport,
    ):
        with pytest.raises(ManagementUnavailable) as failure:
            await transport.request("POST", "/users", {"secret": SECRET}, query={"q": SECRET})
        assert SECRET not in str(failure.value)
        assert failure.value.__suppress_context__
        assert len(writes) == 1
        await transport.close()
        assert not http.is_closed


def test_pure_discovery_validation_is_immutable_and_does_not_mutate_metadata():
    body = document()
    snapshot = dict(body)
    result = management.validate_management_discovery(ISSUER + "/", body)
    assert result == management.ManagementDiscovery(
        ISSUER + "/oidc/token", ACCOUNT + "/api/v1", ACCOUNT
    )
    assert body == snapshot
    with pytest.raises(AttributeError):
        result.base_url = "https://foreign.test/api/v1"


@pytest.mark.parametrize(
    "body",
    [
        None,
        [],
        document(token_endpoint="https://login.example.test:0/token"),
        document(management_api_audience="https://foreign.test"),
    ],
)
def test_pure_discovery_rejects_invalid_server_metadata(body):
    with pytest.raises(ManagementProtocolError):
        management.validate_management_discovery(ISSUER, body)


def test_pure_discovery_rejects_invalid_local_issuer():
    with pytest.raises(ManagementConfigError):
        management.validate_management_discovery("http://login.example.test", document())
