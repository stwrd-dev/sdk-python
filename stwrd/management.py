"""Server-side Management API transport; resource bindings are generated separately."""

from __future__ import annotations

import asyncio
import math
import re
import time
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Self
from urllib.parse import quote, unquote

import httpx

_now = time.monotonic
QueryPrimitive = str | int | float | bool
QueryValue = QueryPrimitive | Sequence[QueryPrimitive | None] | None
ResponseType = Literal["json", "bytes"]


class ManagementConfigError(ValueError):
    """Invalid local configuration or request intent."""


class ManagementProtocolError(RuntimeError):
    """The server did not honor the validated Management transport contract."""


class ManagementUnavailable(RuntimeError):
    """No HTTP response; callers decide whether and how to retry their operation."""


@dataclass(frozen=True)
class PublicError:
    code: str
    message: str
    request_id: str
    details: tuple[Mapping[str, str], ...]


class ManagementError(RuntimeError):
    """HTTP rejection with its typed common error and operation-specific body.

    Exception text contains only status, never submitted credentials or server payloads.
    Confirmation and other typed continuations remain available through ``body``.
    """

    def __init__(self, status: int, body: Any, request_id: str | None) -> None:
        super().__init__(f"Management request failed ({status})")
        self.status = status
        self.body = body
        self.error = _public_error(body)
        self.request_id = request_id or (self.error.request_id if self.error else None)

    @property
    def code(self) -> str | None:
        return self.error.code if self.error else None


def _public_error(body: Any) -> PublicError | None:
    if not isinstance(body, dict) or not isinstance(body.get("error"), dict):
        return None
    value = body["error"]
    if not all(isinstance(value.get(key), str) for key in ("code", "message", "request_id")):
        return None
    details = value.get("details")
    if not isinstance(details, list) or any(
        not isinstance(item, dict)
        or set(item) != {"field", "code", "message"}
        or any(not isinstance(item[key], str) for key in item)
        for item in details
    ):
        return None
    return PublicError(value["code"], value["message"], value["request_id"], tuple(details))


def _https_url(value: Any) -> httpx.URL:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise ManagementConfigError("Management destinations require valid HTTPS URLs")
    try:
        result = httpx.URL(value)
    except (httpx.InvalidURL, ValueError):
        raise ManagementConfigError("Management destinations require valid HTTPS URLs") from None
    if (
        result.scheme != "https"
        or not result.host
        or result.userinfo
        or result.query
        or result.fragment
        or "\\" in value
        or "?" in value
        or "#" in value
    ):
        raise ManagementConfigError("Management destinations require plain HTTPS URLs")
    return result


def _origin(url: httpx.URL) -> tuple[str, str, int]:
    return url.scheme, url.host, url.port if url.port is not None else 443


@dataclass(frozen=True)
class ManagementDiscovery:
    """Validated destinations shared by Management and BFF bearer callers."""

    token_endpoint: str
    base_url: str
    audience: str


def validate_management_discovery(issuer: str, body: object) -> ManagementDiscovery:
    """Validate public metadata without requests, secrets, mutation or caching."""
    issuer = str(_https_url(issuer)).rstrip("/")
    if not isinstance(body, dict) or body.get("issuer") != issuer:
        raise ManagementProtocolError("Discovery issuer mismatch")
    try:
        token = _https_url(body.get("token_endpoint"))
        base = str(_https_url(body.get("management_api_base_url"))).rstrip("/")
        audience = str(_https_url(body.get("management_api_audience"))).rstrip("/")
    except ManagementConfigError:
        raise ManagementProtocolError("Invalid Management discovery destination") from None
    if _origin(token) != _origin(_https_url(issuer)):
        raise ManagementProtocolError("Foreign token destination")
    if base != audience + "/api/v1":
        raise ManagementProtocolError("Management destination does not match audience")
    return ManagementDiscovery(str(token), base, audience)


@dataclass(frozen=True)
class ManagementOptions:
    issuer: str
    client_id: str
    client_secret: str = field(repr=False)
    scopes: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "issuer", str(_https_url(self.issuer)).rstrip("/"))
        if not isinstance(self.client_id, str) or not self.client_id:
            raise ManagementConfigError("Management client ID is required")
        if not isinstance(self.client_secret, str) or not self.client_secret:
            raise ManagementConfigError("Management client secret is required")
        if self.scopes is not None:
            if isinstance(self.scopes, str):
                raise ManagementConfigError("Scopes must be separate registered scope names")
            scopes = tuple(self.scopes)
            if any(
                not isinstance(scope, str) or not re.fullmatch(r"[\x21\x23-\x5b\x5d-\x7e]+", scope)
                for scope in scopes
            ) or len(set(scopes)) != len(scopes):
                raise ManagementConfigError("Scopes must be distinct registered scope names")
            object.__setattr__(self, "scopes", scopes)


@dataclass(frozen=True)
class WriteOptions:
    if_match: str | None = None
    idempotency_key: str | None = None
    confirmation_token: str | None = field(default=None, repr=False)
    step_up_token: str | None = field(default=None, repr=False)
    response_type: ResponseType = "json"

    def __post_init__(self) -> None:
        if self.response_type not in ("json", "bytes"):
            raise ManagementConfigError("Unknown response type")
        for value in (
            self.if_match,
            self.idempotency_key,
            self.confirmation_token,
            self.step_up_token,
        ):
            if value is not None and (
                not isinstance(value, str)
                or any(ord(char) < 32 or ord(char) == 127 for char in value)
            ):
                raise ManagementConfigError("Operation headers require plain strings")


@dataclass(frozen=True)
class MultipartInput:
    """Explicit form fields and httpx file tuples for consent publication."""

    fields: Mapping[str, str] = field(default_factory=dict)
    files: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApiResult[T]:
    data: T
    etag: str | None
    request_id: str | None


@dataclass(frozen=True)
class _Discovery:
    token_endpoint: str
    base_url: str
    audience: str
    valid_until: float

    @property
    def identity(self) -> tuple[str, str, str]:
        return self.token_endpoint, self.base_url, self.audience


@dataclass(frozen=True)
class _Token:
    value: str = field(repr=False)
    valid_until: float
    discovery_identity: tuple[str, str, str]


class ManagementTransport:
    """One immutable issuer/credential context, over an optional injected AsyncClient.

    Requests only accept resource paths relative to the discovered /api/v1 base.
    The transport never replays a request, including GET or a write rejected with401.
    """

    def __init__(self, options: ManagementOptions, *, http_client: httpx.AsyncClient | None = None):
        self._options = options
        self._http = http_client or httpx.AsyncClient()
        self._owns_http = http_client is None
        self._lock = asyncio.Lock()
        self._discovery: _Discovery | None = None
        self._discovery_flight: asyncio.Task[_Discovery] | None = None
        self._token: _Token | None = None
        self._token_flight: asyncio.Task[_Token] | None = None
        self._closed = False

    @property
    def options(self) -> ManagementOptions:
        return self._options

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        async with self._lock:
            self._closed = True
            flights = [task for task in (self._discovery_flight, self._token_flight) if task]
            self._discovery = None
            self._token = None
        for task in flights:
            task.cancel()
        await asyncio.gather(*flights, return_exceptions=True)
        if self._owns_http:
            await self._http.aclose()

    def _check_open(self) -> None:
        if self._closed:
            raise ManagementConfigError("Management transport is closed")

    async def _send(
        self,
        method: str,
        url: str,
        *,
        authorization: str | None = None,
        basic_auth: httpx.BasicAuth | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        self._check_open()
        request = self._http.build_request(method, url, **kwargs)
        # Injected clients must not attach their own credentials or session cookies.
        request.headers.pop("Authorization", None)
        request.headers.pop("Cookie", None)
        request.headers["Host"] = request.url.netloc.decode("ascii")
        if authorization is not None:
            request.headers["Authorization"] = authorization
        try:
            response = await self._http.send(request, auth=basic_auth, follow_redirects=False)
        except httpx.HTTPError:
            raise ManagementUnavailable("Management server did not respond") from None
        if 300 <= response.status_code < 400 or response.history:
            raise ManagementProtocolError("Management redirects are forbidden")
        return response

    @staticmethod
    def _json(response: httpx.Response, *, required: bool = True) -> Any:
        try:
            return response.json()
        except (ValueError, UnicodeError):
            if not required:
                return None
            raise ManagementProtocolError("Invalid Management JSON response") from None

    @staticmethod
    def _raise_response(response: httpx.Response) -> None:
        if not response.is_success:
            raise ManagementError(
                response.status_code,
                ManagementTransport._json(response, required=False),
                response.headers.get("X-Request-ID"),
            )

    async def _load_discovery(self) -> _Discovery:
        try:
            response = await self._send(
                "GET", self.options.issuer + "/.well-known/openid-configuration"
            )
            self._raise_response(response)
            body = self._json(response)
            destinations = validate_management_discovery(self.options.issuer, body)
            # Public metadata is refreshed regularly; account bindings can change.
            cache_control = response.headers.get("Cache-Control", "")
            match = re.search(r"(?:^|,)\s*max-age=(\d+)", cache_control, re.IGNORECASE)
            ttl = min(60, int(match[1])) if match else 30
            if "no-store" in cache_control.lower() or "no-cache" in cache_control.lower():
                ttl = 0
            result = _Discovery(
                destinations.token_endpoint,
                destinations.base_url,
                destinations.audience,
                _now() + ttl,
            )
            async with self._lock:
                self._check_open()
                self._discovery = result
            return result
        finally:
            async with self._lock:
                if self._discovery_flight is asyncio.current_task():
                    self._discovery_flight = None

    async def _discover(self) -> _Discovery:
        self._check_open()
        async with self._lock:
            if self._discovery is not None and self._discovery.valid_until > _now():
                return self._discovery
            if self._discovery_flight is None:
                self._discovery_flight = asyncio.create_task(self._load_discovery())
            flight = self._discovery_flight
        return await asyncio.shield(flight)

    async def _load_token(self, discovery: _Discovery) -> _Token:
        try:
            payload = {"grant_type": "client_credentials"}
            if self.options.scopes:
                payload["scope"] = " ".join(self.options.scopes)
            auth = httpx.BasicAuth(
                quote(self.options.client_id, safe=""), quote(self.options.client_secret, safe="")
            )
            started_at = _now()
            response = await self._send(
                "POST", discovery.token_endpoint, basic_auth=auth, data=payload
            )
            self._raise_response(response)
            body = self._json(response)
            if not isinstance(body, dict):
                raise ManagementProtocolError("Invalid client credentials response")
            value, kind, expires = (
                body.get("access_token"),
                body.get("token_type"),
                body.get("expires_in"),
            )
            if (
                not isinstance(value, str)
                or not value
                or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value)
                or not isinstance(kind, str)
                or kind.lower() != "bearer"
                or isinstance(expires, bool)
                or not isinstance(expires, (int, float))
            ):
                raise ManagementProtocolError("Invalid client credentials response")
            try:
                duration = float(expires)
            except (ValueError, OverflowError):
                raise ManagementProtocolError("Invalid client credentials expiry") from None
            if not math.isfinite(duration) or duration <= 0:
                raise ManagementProtocolError("Invalid client credentials expiry")
            result = _Token(value, started_at + duration * 0.9, discovery.identity)
            if result.valid_until <= _now():
                raise ManagementProtocolError("Client credentials response already expired")
            async with self._lock:
                self._check_open()
                self._token = result
            return result
        finally:
            async with self._lock:
                if self._token_flight is asyncio.current_task():
                    self._token_flight = None

    async def _access_token(self, discovery: _Discovery) -> _Token:
        while True:
            self._check_open()
            async with self._lock:
                if (
                    self._token is not None
                    and self._token.valid_until > _now()
                    and self._token.discovery_identity == discovery.identity
                ):
                    return self._token
                if self._token_flight is None:
                    self._token_flight = asyncio.create_task(self._load_token(discovery))
                flight = self._token_flight
            token = await asyncio.shield(flight)
            if token.discovery_identity == discovery.identity and token.valid_until > _now():
                return token

    @staticmethod
    def _path(path: str) -> None:
        if (
            not isinstance(path, str)
            or not path.startswith("/")
            or path.startswith("//")
            or any(char.isspace() or ord(char) < 32 for char in path)
            or any(char in path for char in "\\?#")
            or re.search(r"%(?![0-9a-fA-F]{2})", path)
        ):
            raise ManagementConfigError("Invalid Management resource path")
        for segment in path.split("/"):
            try:
                decoded = unquote(segment, errors="strict")
            except UnicodeError:
                raise ManagementConfigError("Invalid Management resource path") from None
            if (
                decoded in (".", "..")
                or any(char in decoded for char in "/\\?#%")
                or any(ord(char) < 32 or ord(char) == 127 for char in decoded)
            ):
                raise ManagementConfigError("Invalid Management resource path")

    async def request(
        self,
        method: str,
        path: str,
        input: Any = None,
        options: WriteOptions | None = None,
        query: Mapping[str, QueryValue] | None = None,
    ) -> ApiResult[Any]:
        self._path(path)
        if not isinstance(method, str):
            raise ManagementConfigError("Invalid Management operation method")
        method = method.upper()
        if method not in {"GET", "HEAD", "POST", "PATCH", "PUT", "DELETE"}:
            raise ManagementConfigError("Invalid Management operation method")
        options = options or WriteOptions()
        discovery = await self._discover()
        url = httpx.URL(discovery.base_url + path)
        base = httpx.URL(discovery.base_url)
        if _origin(url) != _origin(base) or not url.path.startswith(base.path.rstrip("/") + "/"):
            raise ManagementConfigError("Foreign Management resource path")
        params = []
        for key, value in (query or {}).items():
            if not isinstance(key, str):
                raise ManagementConfigError("Invalid Management query")
            values = (
                value
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
                else (value,)
            )
            for item in values:
                if item is None:
                    continue
                if type(item) not in (str, int, float, bool) or (
                    isinstance(item, float) and not math.isfinite(item)
                ):
                    raise ManagementConfigError("Invalid Management query")
                params.append((key, str(item).lower() if isinstance(item, bool) else str(item)))
        url = url.copy_merge_params(tuple(params))
        token = await self._access_token(discovery)
        headers = {"Accept": "application/json"}
        for name, value in (
            ("If-Match", options.if_match),
            ("Idempotency-Key", options.idempotency_key),
            ("Confirmation-Token", options.confirmation_token),
            ("X-Stwrd-Step-Up", options.step_up_token),
        ):
            if value is not None:
                headers[name] = value
        body: dict[str, Any] = {}
        if isinstance(input, MultipartInput):
            body = {"data": dict(input.fields), "files": dict(input.files)}
        elif input is not None:
            body = {"json": input}
        response = await self._send(
            method, str(url), authorization=f"Bearer {token.value}", headers=headers, **body
        )
        if response.status_code == 401:
            async with self._lock:
                if self._token is token:
                    self._token = None
        self._raise_response(response)
        data = (
            None
            if response.status_code == 204 or method == "HEAD"
            else (response.content if options.response_type == "bytes" else self._json(response))
        )
        return ApiResult(data, response.headers.get("ETag"), response.headers.get("X-Request-ID"))

    async def iterate(
        self,
        path: str,
        query: Mapping[str, QueryValue] | None = None,
        identity: Callable[[Any], str | int] | None = None,
    ) -> AsyncIterator[Any]:
        cursor = (query or {}).get("cursor")
        if cursor is not None and (not isinstance(cursor, str) or not cursor):
            raise ManagementConfigError("Invalid initial cursor")
        cursors = {cursor} if cursor is not None else set()
        identities: set[str | int] = set()
        while True:
            result = await self.request("GET", path, query={**(query or {}), "cursor": cursor})
            page = result.data
            if (
                not isinstance(page, dict)
                or not isinstance(page.get("items"), list)
                or not isinstance(page.get("page"), dict)
                or "next_cursor" not in page["page"]
            ):
                raise ManagementProtocolError("Invalid Management cursor page")
            next_cursor = page["page"].get("next_cursor")
            if next_cursor is not None and (
                not isinstance(next_cursor, str) or not next_cursor or next_cursor in cursors
            ):
                raise ManagementProtocolError("Repeated or invalid Management cursor")
            batch = []
            for item in page["items"]:
                try:
                    key = identity(item) if identity else item.get("id")
                except (AttributeError, KeyError, TypeError, ValueError):
                    raise ManagementProtocolError("Invalid Management cursor resource") from None
                if type(key) not in (str, int) or key == "":
                    raise ManagementProtocolError("Invalid Management cursor resource")
                if key in identities:
                    raise ManagementProtocolError("Repeated Management cursor resource")
                identities.add(key)
                batch.append(item)
            for item in batch:
                yield item
            if next_cursor is None:
                return
            cursors.add(next_cursor)
            cursor = next_cursor
