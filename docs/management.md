# Management API client

The Management API is stwrd's server-to-server API for administering a tenant.
The SDK ships a typed client for it, built on a small transport. Use Management
credentials on your server only: this client is independent of the BFF login
configuration and its OpenID scopes.

## Typed client

```python
import os

from stwrd import ManagementOptions, create_management


async def list_user_ids() -> list[str]:
    options = ManagementOptions(
        issuer=os.environ["STWRD_ISSUER"],
        client_id=os.environ["STWRD_MANAGEMENT_CLIENT_ID"],
        client_secret=os.environ["STWRD_MANAGEMENT_CLIENT_SECRET"],
    )
    async with create_management(options) as management:
        return [user["id"] async for user in management.users.iterate()]
```

Resources are grouped as attributes (`management.users`,
`management.organizations`, and so on). Collections expose `list(...)` for one
page and `iterate(...)` to traverse every page; other operations are named after
what they do (`get`, `create`, `update`, `delete`). Every call returns an
`ApiResult` with `data`, `etag` and `request_id`. The bindings are generated
from the public OpenAPI document of the Management API.

## Transport

The typed client is a `ManagementTransport`. Use the transport directly when you
need a path the bindings do not cover:

```python
import os

from stwrd.management import ManagementOptions, ManagementTransport, WriteOptions


async def update_person(user_id: str, name: str):
    options = ManagementOptions(
        issuer=os.environ["STWRD_ISSUER"],
        client_id=os.environ["STWRD_MANAGEMENT_CLIENT_ID"],
        client_secret=os.environ["STWRD_MANAGEMENT_CLIENT_SECRET"],
        scopes=("mgmt:users:read", "mgmt:users:write"),
    )
    async with ManagementTransport(options) as transport:
        observed = await transport.request("GET", f"/users/{user_id}")
        return await transport.request(
            "PATCH", f"/users/{user_id}", {"name": name},
            WriteOptions(if_match=observed.etag),
        )
```

Resource paths are relative to the discovered `/api/v1` base. Discovery must
match the configured HTTPS issuer; token acquisition stays on that issuer's
origin. The Management URL and its audience must match each other. Redirects are
refused, including when an injected `httpx.AsyncClient` enables them. The
transport owns and closes its default client; an injected client remains owned
by its caller.

## Scopes and tokens

Omitting `scopes` uses the OAuth defaults registered for the client. Explicit
scopes are snapshotted and must already be registered. The transport adds no
OpenID scopes or Management permissions. Concurrent requests share discovery and
token acquisition, and tokens expire according to a monotonic clock. A failed
refresh never sends an expired token. A 401 discards the token used by that
request; it does not retry the operation or discard a token renewed by another
request.

## Write options

`WriteOptions` carries `if_match`, `idempotency_key`, `confirmation_token` and
`step_up_token` without changing the operation. Reusing an idempotency key is
appropriate only for the same request intent. The transport performs no
automatic request retries.

## Errors

`ManagementError` exposes `status`, `request_id`, the typed `error` and `code`,
and the response `body`, including typed confirmation continuations. Its
exception text contains only the HTTP status. Network failures raise
`ManagementUnavailable`; invalid discovery or response shapes raise
`ManagementProtocolError`; invalid local configuration raises
`ManagementConfigError`.

## Files and pagination

For file publication, pass `MultipartInput(fields, files)`, where files use
httpx file tuples such as `{"document": ("terms.pdf", content, "application/pdf")}`.
Read PDFs and binary exports with `WriteOptions(response_type="bytes")`.

`iterate(path, query, identity)` on the transport traverses cursor pages and
rejects repeated cursors or resource identities. Query values of `None` are
omitted; arrays use repeated query parameters. The default identity is `id`.
The generated bindings supply schema-derived selectors for composite resources:
for example, a consent version selector combines its `consent_id` and `version`.
The transport keeps no manual resource or URL catalogue.

## Discovery validation for BFF apps

BFF apps can reuse the pure `validate_management_discovery(issuer, body)`
validator. It returns immutable `ManagementDiscovery` destinations
(`token_endpoint`, `base_url`, `audience`) without network requests or caching.
Invalid local issuers raise `ManagementConfigError`; invalid server metadata
raises `ManagementProtocolError`.
