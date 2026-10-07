# stwrd-auth

[![PyPI version](https://img.shields.io/pypi/v/stwrd-auth)](https://pypi.org/project/stwrd-auth/)
[![Python versions](https://img.shields.io/pypi/pyversions/stwrd-auth)](https://pypi.org/project/stwrd-auth/)
[![License: MIT](https://img.shields.io/pypi/l/stwrd-auth)](https://github.com/stwrd-dev/sdk-python/blob/main/LICENSE)
![Types included](https://img.shields.io/badge/types-included-blue)

Python SDK for [stwrd](https://stwrd.dev): OpenID Connect sign-in, server-side
sessions, FastAPI dependencies and webhook verification.

The package implements the backend-for-frontend (BFF) profile. It mounts the
`/auth/*` routes on a FastAPI app, keeps the session on the server and exposes
dependencies to protect your own routes. The browser only receives a signed
cookie; access, refresh and ID tokens never leave your process. The
framework-independent parts (OIDC client, session store, webhook verification,
Management API client) work without FastAPI.

This is the Python counterpart of `@stwrd-auth/node`: same routes, same
responses, same `/auth/session` JSON and same environment variables. The
browser client is `@stwrd-auth/react`.

## Installation

The package is installed as `stwrd-auth` and imported as `stwrd`.

```bash
# with uv
uv add "stwrd-auth[fastapi]"

# with pip
pip install "stwrd-auth[fastapi]"
```

| Extra | Adds | Needed for |
|---|---|---|
| `fastapi` | `fastapi`, `starlette`, `python-multipart` | `stwrd.fastapi`: the router, the dependencies and `protect()` |
| `postgres` | `psycopg[pool]` | `stwrd.postgres.PostgresSessionStore`, a session store shared by several workers |

Without extras you get the OIDC client, the session types, webhook
verification and the Management API client, which depend only on `httpx` and
`joserfc`.

Requires Python 3.12 or newer.

## Quick start

Register an application in stwrd, allow `{STWRD_BASE_URL}/auth/callback` as a
redirect URI, and export the required settings:

```bash
export STWRD_ISSUER=https://idp.example.com
export STWRD_CLIENT_ID=your-client-id
export STWRD_CLIENT_SECRET=your-client-secret
export STWRD_BASE_URL=https://app.example.com
export STWRD_COOKIE_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

Then create the app:

```python
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from stwrd import Stwrd, StwrdUser
from stwrd.fastapi import auth_router, current_user, optional_user

stwrd = Stwrd.from_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await stwrd.close()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router(stwrd))


@app.get("/")
async def home(user: StwrdUser | None = Depends(optional_user(stwrd))):
    if user is None:
        return {"signed_in": False, "sign_in": "/auth/sign-in?return_to=/me"}
    return {"signed_in": True, "email": user.email}


@app.get("/me")
async def me(user: StwrdUser = Depends(current_user(stwrd))):
    return {"id": user.id, "email": user.email, "roles": user.roles}
```

Run it with `uvicorn main:app`. Opening `/auth/sign-in?return_to=/me` redirects
to stwrd, and `/auth/callback` completes the sign-in and returns the person to
`/me`. `GET /auth/session` returns the JSON that `@stwrd-auth/react` consumes:

```json
{"authenticated": true,
 "user": {"id": "…", "email": "…", "email_verified": true,
          "display_name": null, "avatar_url": null, "roles": [], "permissions": []},
 "organization": null, "consents": {},
 "csrf_token": "…", "account_url": "https://idp.example.com/me"}
```

### Roles, permissions, sign-out and webhooks

```python
from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse

from stwrd import Stwrd, StwrdUser, WebhookEvent
from stwrd.fastapi import (
    auth_router, current_user, optional_user, require_permission, require_role,
)

stwrd = Stwrd.from_env()


async def on_event(event: WebhookEvent) -> None:
    # `event.type` is the event name; `event.data`, its payload.
    print("webhook", event.type, event.data)


app = FastAPI()
app.include_router(auth_router(stwrd, on_event=on_event))


@app.get("/", response_class=HTMLResponse)
async def home(user: StwrdUser | None = Depends(optional_user(stwrd))):
    if user is None:
        return '<a href="/auth/sign-in?return_to=/private">Sign in</a>'
    return f'<p>Hello, {user.email}.</p><a href="/private">Private area</a>'


@app.get("/private", response_class=HTMLResponse)
async def private(request: Request, user: StwrdUser = Depends(current_user(stwrd))):
    # Sign-out is a POST with a CSRF token derived from the local session
    # (the same value `GET /auth/session` returns as `csrf_token`).
    session = await stwrd.session_from_cookie(request.cookies.get(stwrd.config.session_cookie))
    csrf = stwrd.csrf(session.id)
    return (
        f"<p>Welcome, {user.email}. Your id is {user.id}.</p>"
        '<form method="post" action="/auth/sign-out">'
        f'<input type="hidden" name="csrf_token" value="{csrf}"><button>Sign out</button></form>'
    )


@app.get("/admin")
async def admin(user: StwrdUser = Depends(require_role(stwrd, "org:admin"))):
    return {"actor_id": user.id}


@app.post("/invitations")
async def invite(user: StwrdUser = Depends(require_permission(stwrd, "members:invite"))):
    return {"invited_by": user.id}
```

`org:admin` and `members:invite` are examples: use the role and permission names
defined in your tenant. Organization roles need the `org` scope, see
[Scopes](#scopes).

### Without a framework

Webhook verification does not depend on FastAPI. This receiver works with any
web framework: pass it the raw request body and the headers.

```python
import os
from collections.abc import Mapping

from stwrd import DuplicateEventError, InvalidSignatureError, verify_webhook
from stwrd.webhooks import SeenWebhookIds

WEBHOOK_SECRET = os.environ["STWRD_WEBHOOK_SECRET"]
seen = SeenWebhookIds()  # in-memory; keep your own record of processed ids too


def receive(body: bytes, headers: Mapping[str, str]) -> int:
    """Return the HTTP status code to answer with."""
    try:
        event = verify_webhook(body, headers, WEBHOOK_SECRET, seen=seen)
    except DuplicateEventError:
        return 200  # already processed
    except InvalidSignatureError:
        return 400
    print("webhook", event.type, event.data)
    return 200
```

Sessions work the same way outside FastAPI: `await stwrd.resolve_session(cookie_value)`
returns the current `StwrdSession` or `None`. See the [API reference](#api-reference).

## Configuration

`Stwrd.from_env()` and `StwrdConfig.from_env()` read these variables. The same
names are read by `@stwrd-auth/node`, so an app can switch languages without
touching its `.env`. Every setting is also a field of `StwrdConfig`, and
keyword arguments to `from_env()` override the environment.

| Variable | Required | Default | Description |
|---|---|---|---|
| `STWRD_ISSUER` | yes | | Issuer URL of the tenant, for example `https://idp.example.com`. |
| `STWRD_CLIENT_ID` | yes | | OIDC client registered for this application. |
| `STWRD_CLIENT_SECRET` | yes | | Secret of that client. |
| `STWRD_BASE_URL` | yes | | Public URL of this app. `{base_url}{prefix}/callback` is the redirect URI. |
| `STWRD_COOKIE_SECRET` | yes | | HMAC key for the session cookie, **at least 32 characters**. |
| `STWRD_SCOPE` | no | `openid profile email offline_access` | Requested scopes, see [Scopes](#scopes). |
| `STWRD_WEBHOOK_SECRET` | no | | Signing secret for `/auth/webhook`. Without it the route answers 503. |
| `STWRD_PREFIX` | no | `/auth` | Path prefix of the routes. |
| `STWRD_SESSION_TTL_S` | no | `28800` (8 h) | Sliding lifetime of the local session. |
| `STWRD_COOKIE_SECURE` | no | `true` | Set to `false` only for plain-HTTP local development. |
| `STWRD_POST_LOGIN_REDIRECT` | no | `/` | Where to go after sign-in when no `return_to` was given. |
| `STWRD_POST_LOGOUT_REDIRECT` | no | `/` | Where to go after sign-out. |
| `STWRD_CONNECT_TO` | no | | Connect elsewhere while keeping the issuer's `Host`, see [Developing against a local server](#developing-against-a-local-server). |

If a required variable is missing or `STWRD_COOKIE_SECRET` is too short,
`from_env()` raises `ConfigError` and the process does not start. That is on
purpose: a misconfigured integration fails at startup, not on the third request.

Fields without a variable: `session_cookie` (default `__Host-stwrd_session`),
`tx_cookie` (default `__Host-stwrd_tx`) and `transaction_ttl_s` (default `600`).
Browsers reject a `__Host-` cookie that is not `Secure`, so when you set
`STWRD_COOKIE_SECURE=false` for local development also pass cookie names
without that prefix:
`Stwrd.from_env(session_cookie="stwrd_session", tx_cookie="stwrd_tx")`.

## Routes

`auth_router(stwrd)` mounts these routes under the prefix (default `/auth`):

| Route | Purpose |
|---|---|
| `GET /sign-in?return_to=…` | Starts the authorization-code flow with PKCE. `return_to` accepts only a relative path of this app; anything else falls back to `/`. |
| `GET /callback` | Completes sign-in, creates the local session and sets the cookie. |
| `POST /sign-out` | Ends the local session and signs out at stwrd. Requires the CSRF token (`csrf_token` form field or `X-CSRF-Token` header). |
| `GET /session` | Current session as JSON (anonymous shape when there is none). |
| `GET /organizations`, `POST /organization` | List the person's organizations and switch the active one. Available only when the `org` scope is requested. |
| `POST /back-channel` | Receives back-channel logout notices from stwrd. |
| `POST /webhook` | Receives and verifies webhooks. |

`auth_router` also accepts two hooks: `on_user_registered(user)`, called on every
successful sign-in (make it an idempotent upsert), and `on_event(event)`, called
once per accepted webhook delivery. Both may be sync or async.

## Protecting routes

All dependencies are factories: they take the `Stwrd` instance and return the
callable FastAPI runs under `Depends(...)`. There is no implicit registration
in `app.state`.

| Factory | Returns | If it does not hold |
|---|---|---|
| `optional_user(stwrd)` | `StwrdUser \| None` | never fails; `None` means no session |
| `current_user(stwrd)` | `StwrdUser` | 303 to sign-in, or 401 for API requests |
| `require_auth(stwrd)` | `None` | 303 to sign-in, or 401 for API requests |
| `require_role(stwrd, role)` | `StwrdUser` | 403 `Missing role {role}.` |
| `require_org(stwrd)` | `StwrdUser` | 403 `The session has no organization.` |
| `require_permission(stwrd, permission)` | `StwrdUser` | 403 `Missing permission {permission}.` |
| `api_mode(stwrd)` | `None` | makes that route answer a JSON 401 instead of a 303 |

`protect(app, stwrd, public=("/", "/static/*"))` is the opt-in fail-closed mode:
it requires a session on every path not declared public. Everything under the
auth prefix is always public, and `*` is a wildcard only at the end of a pattern.

`require_role` and `require_permission` evaluate the session's coherent
organization or individual capability family and never combine the two.
`require_org` raises `ConfigError` when it is built without the `org` scope.
Dependencies also store `request.state.stwrd_user`, `stwrd_organization` and
`stwrd_consents`.

When stwrd does not answer, every entry point responds 503 and keeps the
stored session: an unreachable server never looks like a signed-out user.

## Scopes

The default scope is `openid profile email offline_access`. It does not include
`org`; organization claims, `require_org` and the organization routes need it
requested explicitly, in two places:

1. In the app: `STWRD_SCOPE="openid profile email offline_access org"`.
2. In stwrd: the scope must be allowed for the client.

Requesting a scope the client is not allowed to use makes the authorization
request fail with `invalid_scope`; it is not trimmed silently. Without
`offline_access` there is no refresh token and the local session lasts as long
as the access token.

## Sessions and session stores

Tokens and claims are stored server-side in a `SessionStore`; the cookie only
carries an opaque session id. Expired access tokens are renewed with the
refresh token on the next request, and a renewal that stwrd rejects ends the
session.

| Store | Use |
|---|---|
| `MemoryStore` (default) | One process. Sessions are lost on restart and not shared between workers. |
| `stwrd.postgres.PostgresSessionStore` | Several workers or restarts. Requires the `postgres` extra. |

`PostgresSessionStore` encrypts the stored tokens (JWE, `A256GCM`) with a
keyring you provide and coordinates refresh across processes, so a refresh token
is exchanged at most once. Create the table by running `stwrd.postgres.SCHEMA_SQL`
from your own migration; the store never creates tables.

```python
from psycopg_pool import AsyncConnectionPool

from stwrd import Stwrd
from stwrd.postgres import Keyring, PostgresSessionStore

pool = AsyncConnectionPool("postgresql://user:password@db.example.com/app", open=False)
keyring = Keyring({"k1": key_bytes_32}, current="k1")  # 32 random bytes per key
stwrd = Stwrd.from_env(sessions=PostgresSessionStore(pool, namespace="my-app", keyring=keyring))
```

Open the pool during application startup (`await pool.open()`). Any object that
implements the `SessionStore` protocol can be used instead.

## Webhooks

`auth_router` verifies webhooks at `POST /auth/webhook` when
`STWRD_WEBHOOK_SECRET` is set. To receive them in your own code, or to
implement a receiver in another language, see the
[webhook contract](https://github.com/stwrd-dev/sdk-python/blob/main/docs/webhooks.md):
headers, signature scheme, replay window, retries and a test vector.

## Management API

`create_management(ManagementOptions(...))` returns a typed, server-side client
for the Management API, authenticated with client credentials. Keep these
credentials on your server.

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

Configuration, ETags and write options, file uploads and cursor traversal are
covered in the [Management transport guide](https://github.com/stwrd-dev/sdk-python/blob/main/docs/management.md).

## Developing against a local server

The server resolves the tenant from the `Host` header, so an SDK talking to a
server on `127.0.0.1` has to do it *as* the tenant's host. `connect_to` (or
`STWRD_CONNECT_TO`) does exactly that for discovery, token, JWKS and userinfo
requests: it connects to the given address while keeping the issuer's URL and
`Host`, with no DNS or `/etc/hosts` changes.

```bash
STWRD_ISSUER=https://tenant.example.com
STWRD_CONNECT_TO=http://127.0.0.1:3005
```

If the app builds its own `httpx.AsyncClient` (a proxy, a custom transport),
`connect_to_hook(connect_to)` is the same request hook:
`httpx.AsyncClient(event_hooks={"request": [connect_to_hook(...)]})`.

`connect_to` does not affect the front channel: the browser still has to resolve
the issuer's host. For browserless tests, mount the server and the app with
`httpx.ASGITransport` instead.

## Running the tests

```bash
uv sync --all-extras --all-groups
uv run pytest tests/
```

The PostgreSQL session-store tests need a PostgreSQL server whose user can
create and drop databases (each test module gets its own throwaway database).
They look for it at `postgresql+psycopg://stwrd:stwrd@localhost:55432/stwrd_test`;
set `STWRD_TEST_DB_URL` to point somewhere else. If no server is reachable those
tests are skipped with a message saying so, and everything else still runs.
Set `STWRD_REQUIRE_DB=1` to make an unreachable server a failure instead of a
skip, which is what a CI pipeline should do. A throwaway server:

```bash
docker run --rm -d --name stwrd-test-pg -p 55432:5432 \
  -e POSTGRES_USER=stwrd -e POSTGRES_PASSWORD=stwrd -e POSTGRES_DB=stwrd_test \
  postgres:16
```

## API reference

Everything below is importable from `stwrd` unless noted.

### Client and configuration

| Name | Description |
|---|---|
| `Stwrd(config, *, sessions=None, http_client=None)` | The object an app builds once. `Stwrd.from_env(environ=None, **overrides)` builds it from the environment. |
| `Stwrd.resolve_session(cookie)` | Current `StwrdSession` or `None`; renews tokens when possible. Raises `IdpUnavailable` when stwrd cannot be reached. |
| `Stwrd.session_from_cookie(cookie)` | Raw store lookup: no renewal, no expiry side effects. |
| `Stwrd.csrf(session_id)` | CSRF token for a session. |
| `Stwrd.seal(value)` / `Stwrd.unseal(cookie)` | Sign and verify the opaque cookie value. |
| `Stwrd.verify_webhook(body, headers)` | Verify a webhook with the configured secret and de-duplicate it. |
| `Stwrd.close()` | Close the HTTP client, if the instance created it. |
| `StwrdConfig` | Frozen configuration; fields as in [Configuration](#configuration). `StwrdConfig.from_env()`, `replace(**changes)`. |
| `connect_to_hook(connect_to)` | `httpx` request hook behind `connect_to`. |

### Session types and stores

| Name | Description |
|---|---|
| `StwrdSession` | `id`, `sub`, `claims`, `tokens`, `expires_at`; `user`, `organization` and `consents` projections; `has_role()` and `has_permission()`. |
| `StwrdUser` | `id`, `email`, `email_verified`, `display_name`, `avatar_url`, `roles`, `permissions`. |
| `StwrdOrganization` | `id`, `display_name`, `roles`, `permissions`. |
| `Tokens` | `access_token`, `id_token`, `token_type`, `expires_at`, `refresh_token`. |
| `SessionStore` | Protocol for session storage. |
| `MemoryStore` | In-process implementation. |
| `stwrd.postgres.PostgresSessionStore`, `Keyring`, `SCHEMA_SQL` | Shared store, see [Sessions and session stores](#sessions-and-session-stores). |

### FastAPI (`stwrd.fastapi`)

`auth_router`, `optional_user`, `current_user`, `require_auth`, `require_role`,
`require_org`, `require_permission`, `api_mode`, `protect` and `safe_target`.
`safe_target(candidate, fallback="/")` applies the redirect rule used by
`return_to` and is exported for apps that handle redirect targets of their own.

### Webhooks

| Name | Description |
|---|---|
| `verify_webhook(body, headers, secret, tolerance_s=300, *, seen=None)` | Verify the signature and parse a v1 event into a `WebhookEvent`. |
| `verify_webhook_signature(body, headers, secret, tolerance_s=300)` | Verify the signature only and return the event id. |
| `WebhookEvent` | `id`, `type`, `api_version`, `created_at`, `data`. |
| `safe_equal(a, b)` | Constant-time string comparison. |

### Management

`create_management`, `ManagementClient`, `ManagementOptions`, `WriteOptions`,
`ApiResult` and `ManagementError`; the lower-level `ManagementTransport` and
`validate_management_discovery` live in `stwrd.management`.

## Security

- **Tokens stay on the server.** The browser only holds an HMAC-signed cookie
  with an opaque session id: `__Host-` prefixed, `HttpOnly`, `Secure`,
  `SameSite=Lax`, path `/`.
- **Authorization code flow with PKCE (S256).** `state`, `nonce` and the PKCE
  verifier live in a short-lived signed transaction cookie.
- **ID tokens are verified.** Signature (RS256 and EdDSA only, never taken from
  the token header), `iss`, `aud`, `exp`, `nonce` and `at_hash`. Capabilities
  such as roles and permissions come only from verified ID tokens, never from
  userinfo.
- **CSRF.** `sign-out` and organization switching require a token derived from
  the session; `GET /auth/session` returns it as `csrf_token`.
- **Open redirects.** `return_to` accepts only an absolute path of this app,
  and rejects `//host`, backslash forms, control characters and schemes.
- **Refresh.** A refresh token is exchanged at most once across workers when a
  shared store is used. A silent server never ends a session, and a request
  that may have consumed a refresh token is never replayed.
- **Webhooks.** HMAC-SHA256 over the raw body, constant-time comparison,
  300-second replay window and de-duplication by event id.
- **No hand-written cryptography.** JOSE operations use `joserfc`.
- **Secrets.** Load `STWRD_COOKIE_SECRET`, `STWRD_CLIENT_SECRET` and
  `STWRD_WEBHOOK_SECRET` from your secret manager, never from source control.
  Rotating the cookie secret signs everyone out. Management credentials belong
  on the server only, and the Management client refuses to follow redirects.
- **Reporting a vulnerability.** See the
  [security policy](https://github.com/stwrd-dev/sdk-python/security/policy)
  for supported versions and how to report a problem privately.

## Errors and troubleshooting

| Situation | Response |
|---|---|
| No session, navigation (`Accept: text/html`) | 303 to `{prefix}/sign-in?return_to=…` |
| No session, API request (or `api_mode`) | 401 `{"detail": "No session."}` |
| Role missing | 403 `{"detail": "Missing role org:admin."}` |
| Permission missing | 403 `{"detail": "Missing permission members:invite."}` |
| No organization (`require_org`) | 403 `{"detail": "The session has no organization."}` |
| `POST /auth/sign-out` without a valid CSRF token | 403 `{"detail": "Invalid CSRF token."}` |
| stwrd does not answer (any route that needs it) | 503 `{"detail": "The IdP did not respond."}`; the session is kept |
| `GET /auth/callback` rejected (state, signature, nonce…) | 400 plain text |
| `POST /auth/webhook` | 200 `{"status":"ok"}` · 200 `{"status":"duplicate"}` · 400 `{"error":"invalid_signature"}` · 503 `{"error":"webhook_not_configured"}` |
| `POST /auth/back-channel` invalid | 400 `{"error": …}` |
| Refresh rejected by stwrd | The local session ends; the request looks like "no session". |
| Incomplete configuration or a short cookie secret | `ConfigError` at construction |

Exceptions, all importable from `stwrd`: `ConfigError` (invalid configuration),
`OidcError` (stwrd answered and rejected the request), `IdpUnavailable` (stwrd
did not answer: connection error, timeout, 5xx, 408, 425 or 429),
`RefreshUncertain` (a refresh may have been processed without its result being
stored; the person must sign in again), `InvalidSignatureError` and
`DuplicateEventError` (webhooks), and `ManagementError` (HTTP errors from the
Management API, with `status`, `request_id`, `error` and `body`).

Common problems:

- **Sign-in loops back to the login page on `http://localhost`.** The default
  cookies are `Secure` and `__Host-` prefixed. See the note under
  [Configuration](#configuration) for local development.
- **`invalid_scope` when starting sign-in.** The scope is requested by the app
  but not allowed for the client, see [Scopes](#scopes).
- **Users are signed out when the app restarts or scales to several workers.**
  `MemoryStore` is per process; use `PostgresSessionStore`.
- **503 from every protected route.** The app cannot reach stwrd; check
  `STWRD_ISSUER` and the network. Sessions are preserved meanwhile.

## Compatibility

- Python 3.12, 3.13 and 3.14.
- FastAPI 0.115 or newer and Starlette 0.40 or newer (the `fastapi` extra).
- `httpx` 0.27 or newer and `joserfc` 1.0 or newer.
- PostgreSQL through `psycopg` 3.2 or newer (the `postgres` extra).
- Type hints throughout; the package ships a `py.typed` marker.

## Versioning

The package follows [Semantic Versioning](https://semver.org/). Before 1.0, minor
releases may contain breaking changes; they are listed in the
[changelog](https://github.com/stwrd-dev/sdk-python/blob/main/CHANGELOG.md).
Pin an exact or compatible-release version, for example `stwrd-auth~=0.1.0`.

## License

[MIT](https://github.com/stwrd-dev/sdk-python/blob/main/LICENSE). Copyright (c) 2026 stwrd.
