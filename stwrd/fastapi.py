"""`stwrd.fastapi` — the FastAPI/Starlette extra.

Installed with the `fastapi` extra (`pip install "stwrd-auth[fastapi]"`).
Provides the `/auth/*` routes under `stwrd.config.prefix` (`auth_router`), the
dependency factories that guard an app's own routes, and the opt-in
fail-closed `protect()`.

Every dependency factory below except `auth_router` needs a `Stwrd` instance
to resolve a session against. Each factory takes `stwrd` explicitly and
returns the dependency FastAPI actually calls — `Depends(current_user(stwrd))`,
`Depends(require_role(stwrd, "org:admin"))` — rather than reading it from
`request.app.state`, which would need a registration step and silently break
if an app declared routes before that step ran. Passing the resource
explicitly is the ordinary FastAPI shape for a dependency that needs one.
"""

from __future__ import annotations

import inspect
import time
import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import asdict
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .client import ConfigError, Stwrd
from .oidc import IdpUnavailable, OidcError, RefreshUncertain, challenge_s256
from .sessions import StwrdSession, StwrdUser, Tokens, merge_userinfo
from .webhooks import DuplicateEventError, InvalidSignatureError, WebhookEvent
from .webhooks import safe_equal as _safe_equal

#: What a person is told when the IdP does not answer. One sentence for every
#: entry point: it is the same fact, and the reader cannot tell which route
#: they came through.
IDP_SILENT = "The IdP did not respond."


def _delete_cookie(response: Response, stwrd: Stwrd, name: str) -> None:
    """Deletes one of the SDK's cookies with the attributes it was set with.

    `Secure` is the one that matters: a browser refuses a deletion of a
    `__Host-` cookie that is not `Secure`, and the session cookie would
    outlive the sign-out. `Max-Age=0` and the epoch `Expires` both ask for the
    deletion (`delete_cookie` would put the current time in `Expires`).
    """
    response.set_cookie(
        name,
        "",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        path="/",
        secure=stwrd.config.cookie_secure,
        httponly=True,
        samesite="lax",
    )


def _cookie_kwargs(stwrd: Stwrd, *, max_age: int) -> dict[str, Any]:
    return {
        "httponly": True,
        "secure": stwrd.config.cookie_secure,
        "samesite": "lax",
        "path": "/",
        "max_age": max_age,
    }


def safe_target(candidate: str | None, fallback: str = "/") -> str:
    """A redirect target confined to this app — the same rule as `safeTarget`
    in the Node SDK: only an absolute path of this origin passes; anything
    else falls back.

    Rejected: empty, no leading `/` (covers `https://evil`, `javascript:`,
    `@evil`, `evil.example`), protocol-relative `//host`, and its
    backslash spelling `/\\host` — browsers normalise `\\` to `/` in the
    path of an http(s) URL, so `/\\evil` *is* `//evil` once it reaches
    `Location`. Any control character (tab, CR, LF, NUL, DEL) is rejected too:
    a URL parser drops a tab or a line break, so `/\\t/evil` resolves to
    `//evil`. Exposed so an app can apply the same rule to a target it
    read from somewhere less trustworthy (a query param, a stored value).
    """
    if not candidate or not candidate.startswith("/"):
        return fallback
    if candidate[1:2] in ("/", "\\"):
        return fallback
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in candidate):
        return fallback
    return candidate


def _return_to_url(request: Request) -> str:
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"
    return safe_target(path)


# --- the router ----------------------------------------------------------


def auth_router(
    stwrd: Stwrd,
    *,
    on_user_registered: Callable[[StwrdUser], Any] | None = None,
    on_event: Callable[[WebhookEvent], Any] | None = None,
) -> APIRouter:
    """Mounts the `/auth/*` routes under `stwrd.config.prefix`.

    `on_user_registered(user)` runs once per successful `/auth/callback`.
    Whether this is the very first login for that `sub` is the app's own
    question — it owns the mapping from `user.id` to its own records — so the
    hook fires on every login, and an idempotent upsert on the app's side is
    what makes "registered" mean the first one. `on_event(event)` runs once
    per accepted `/auth/webhook` delivery, after dedup.
    """
    router = APIRouter(prefix=stwrd.config.prefix)

    # `jti` replay guard for back-channel logout. Process-local and pruned by
    # the `logout_token`'s own 2-minute `exp` — a
    # token that lived longer than that could not pass `validate_logout_token`
    # anyway, so nothing needs to survive it.
    _seen_logout_jti: dict[str, float] = {}

    def _prune_logout_jti() -> None:
        cutoff = time.time() - 120
        for jti in [k for k, seen_at in _seen_logout_jti.items() if seen_at < cutoff]:
            del _seen_logout_jti[jti]

    @router.get("/sign-in")
    async def sign_in(request: Request, return_to: str = "/") -> Any:
        # Open-redirect guard: the destination is confined *before* either branch uses it, so the
        # copy sealed into the transaction is already safe and the callback
        # cannot be talked into a foreign origin either.
        return_to = safe_target(return_to)
        cookie = request.cookies.get(stwrd.config.session_cookie)
        try:
            session = await stwrd.resolve_session(cookie)
        except RefreshUncertain:
            # That session can never be refreshed: signing in again is the way out.
            session = None
        except IdpUnavailable:
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None
        if session is not None:
            return RedirectResponse(return_to, status_code=303)

        try:
            await stwrd.oidc.discover()
        except IdpUnavailable:
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None
        except OidcError:
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None

        state = stwrd.new_authorization_state(return_to=return_to)
        url = await stwrd.oidc.authorize_url(
            state=state.state,
            nonce=state.nonce,
            code_challenge=challenge_s256(state.code_verifier),
        )
        response = RedirectResponse(url, status_code=303)
        response.set_cookie(
            stwrd.config.tx_cookie,
            stwrd.seal(
                {
                    "state": state.state,
                    "nonce": state.nonce,
                    "code_verifier": state.code_verifier,
                    "return_to": state.return_to,
                }
            ),
            **_cookie_kwargs(stwrd, max_age=stwrd.config.transaction_ttl_s),
        )
        return response

    @router.get("/callback")
    async def callback(request: Request, code: str | None = None, state: str | None = None) -> Any:
        tx = stwrd.unseal(request.cookies.get(stwrd.config.tx_cookie))
        if not tx or not isinstance(tx, dict):
            return PlainTextResponse("There is no login transaction in progress.", status_code=400)
        if not code or not state or state != tx.get("state"):
            return PlainTextResponse("The state does not match.", status_code=400)

        try:
            token_response = await stwrd.oidc.exchange_code(
                code=code, code_verifier=tx["code_verifier"]
            )
            access_token = token_response["access_token"]
            id_claims = await stwrd.oidc.validate_id_token(
                token_response["id_token"], nonce=tx["nonce"], access_token=access_token
            )
            userinfo_claims = await stwrd.oidc.userinfo(access_token)
        except IdpUnavailable:
            # 503 and not 400: a login that could not be attempted is not a
            # rejected login, and answering 400 to someone returning from the
            # IdP hides that the failure is on the server side and that
            # retrying helps.
            return PlainTextResponse(IDP_SILENT, status_code=503)
        except (OidcError, KeyError) as exc:
            return PlainTextResponse(f"The login failed: {exc}", status_code=400)

        # `email`/`email_verified` only ever come from userinfo;
        # everything else prefers the `id_token`,
        # which is what a step-up or an `amr`/`acr` change actually refreshed.
        try:
            claims = merge_userinfo(id_claims, userinfo_claims)
        except OidcError as exc:
            return PlainTextResponse(f"The login failed: {exc}", status_code=400)

        now = time.time()
        expires_in = token_response.get("expires_in", 3600)
        tokens = Tokens(
            access_token=access_token,
            id_token=token_response["id_token"],
            token_type=token_response.get("token_type", "Bearer"),
            expires_at=now + float(expires_in),
            # The token endpoint does not mint one yet — see
            # `sessions.py::Tokens`.
            refresh_token=token_response.get("refresh_token"),
        )
        # Derived from the IdP's `sid`, not random: it is what lets
        # back-channel logout find this row later (`Stwrd.session_id_for_sid`).
        # The fallback exists only for a token without `sid` — stwrd always
        # emits one, but a session that cannot be reached by logout is better
        # than no session at all, and it stays unreachable *loudly* because the
        # `sid_idp` below is then `None` too.
        sid_claim = claims.get("sid")
        session = StwrdSession(
            id=stwrd.session_id_for_sid(sid_claim) if sid_claim else _new_session_id(),
            sid_idp=sid_claim,
            sub=claims["sub"],
            claims=claims,
            tokens=tokens,
            expires_at=now + stwrd.config.session_ttl_s,
            access_expires_at=tokens.expires_at,
        )
        switch = tx.get("switch")
        if switch is None:
            await stwrd.sessions.set(session)
            if on_user_registered is not None:
                result = on_user_registered(session.user)
                if inspect.isawaitable(result):
                    await result
        else:
            # An organization switch only ever replaces the live session it
            # started from, for the same person and exactly the selected
            # organization, under a new IdP session id. A callback that no
            # longer matches (late, replayed, other person) installs nothing.
            if (
                not isinstance(switch, dict)
                or claims.get("sub") != switch.get("sub")
                or not _same_uuid(claims.get("org_id"), switch.get("org"))
                or not sid_claim
                or sid_claim == switch.get("sid")
            ):
                return PlainTextResponse("The organization switch did not match.", status_code=400)
            if not await stwrd.sessions.replace_session(str(switch.get("from")), session):
                return PlainTextResponse(
                    "The session this selection started from is gone.", status_code=409
                )

        # Re-checked here too: the transaction is sealed, but a target that
        # somehow got in unchecked (an older SDK's cookie, a custom store)
        # must not become a redirect to another origin.
        destination = safe_target(tx.get("return_to"), stwrd.config.post_login_redirect)
        response = RedirectResponse(destination, status_code=303)
        _delete_cookie(response, stwrd, stwrd.config.tx_cookie)
        response.set_cookie(
            stwrd.config.session_cookie,
            stwrd.seal({"sid": session.id}),
            **_cookie_kwargs(stwrd, max_age=stwrd.config.session_ttl_s),
        )
        return response

    @router.post("/sign-out")
    async def sign_out(request: Request) -> Any:
        cookie = request.cookies.get(stwrd.config.session_cookie)
        session = await stwrd.session_from_cookie(cookie)
        if session is None:
            # Without a session, 303 to the post-logout destination.
            return RedirectResponse(stwrd.config.post_logout_redirect_uri, status_code=303)

        csrf_token = request.headers.get("x-csrf-token")
        if not csrf_token:
            try:
                form = await request.form()
                value = form.get("csrf_token")
                csrf_token = str(value) if value is not None else None
            except Exception:  # noqa: BLE001 - a body that isn't form data is just "no token"
                csrf_token = None
        if not csrf_token or not _safe_equal(csrf_token, stwrd.csrf(session.id)):
            raise HTTPException(status_code=403, detail="Invalid CSRF token.")

        await stwrd.sessions.delete(session.id)

        if await stwrd.oidc.supports_end_session():
            discovery = await stwrd.oidc.discover()
            assert discovery.end_session_endpoint is not None
            destination = str(
                httpx.URL(
                    discovery.end_session_endpoint,
                    params={
                        "id_token_hint": session.tokens.id_token,
                        "post_logout_redirect_uri": stwrd.config.post_logout_redirect_uri,
                    },
                )
            )
        else:
            # Normally sign-out clears the local session and goes to the
            # IdP's end-session endpoint with `id_token_hint`. When
            # `end_session_endpoint` is not advertised, the router degrades
            # (decided by discovery, not by a flag): it only clears the local
            # session and answers 303 to the post-logout redirect. Once the
            # IdP advertises the endpoint this branch stops being reachable
            # and the one above becomes the only path — no SDK change needed.
            destination = stwrd.config.post_logout_redirect_uri

        response = RedirectResponse(destination, status_code=303)
        _delete_cookie(response, stwrd, stwrd.config.session_cookie)
        return response

    @router.get("/session")
    async def session_status(request: Request) -> Any:
        try:
            session = await stwrd.resolve_session(request.cookies.get(stwrd.config.session_cookie))
        except IdpUnavailable:
            return JSONResponse(
                {"detail": IDP_SILENT}, status_code=503, headers={"Cache-Control": "no-store"}
            )
        body = {
            "authenticated": session is not None,
            "user": asdict(session.user) if session else None,
            "organization": asdict(session.organization)
            if session and session.organization
            else None,
            "consents": session.consents if session else {},
            "csrf_token": stwrd.csrf(session.id) if session else None,
            "account_url": stwrd.config.account_url,
        }
        return JSONResponse(body, headers={"Cache-Control": "no-store"})

    @router.get("/organizations")
    async def organizations(request: Request) -> Any:
        headers = {"Cache-Control": "no-store"}
        if not stwrd.organization_selection_enabled():
            return JSONResponse(
                {"detail": "Organization selection is not enabled."},
                status_code=404,
                headers=headers,
            )
        try:
            session = await stwrd.resolve_session(request.cookies.get(stwrd.config.session_cookie))
            if session is None:
                return JSONResponse(
                    {"detail": "Not authenticated."}, status_code=401, headers=headers
                )
            owned = await stwrd.list_organizations(session)
        except IdpUnavailable:
            return JSONResponse({"detail": IDP_SILENT}, status_code=503, headers=headers)
        current = session.organization.id if session.organization else None
        return JSONResponse(
            {
                "organizations": [
                    {"id": org.id, "display_name": org.display_name, "current": org.id == current}
                    for org in owned
                ]
            },
            headers=headers,
        )

    @router.post("/organization")
    async def select_organization(request: Request) -> Any:
        if not stwrd.organization_selection_enabled():
            raise HTTPException(status_code=404, detail="Organization selection is not enabled.")
        try:
            session = await stwrd.resolve_session(request.cookies.get(stwrd.config.session_cookie))
        except IdpUnavailable:
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None
        if session is None:
            raise HTTPException(status_code=401, detail="Not authenticated.")
        values: dict[str, Any] = {}
        try:
            if "json" in request.headers.get("content-type", ""):
                body = await request.json()
                values = body if isinstance(body, dict) else {}
            else:
                values = dict(await request.form())
        except Exception:  # noqa: BLE001 - an unreadable body is just "no values"
            values = {}
        csrf_token = request.headers.get("x-csrf-token") or values.get("csrf_token")
        if not isinstance(csrf_token, str) or not _safe_equal(csrf_token, stwrd.csrf(session.id)):
            raise HTTPException(status_code=403, detail="Invalid CSRF token.")
        try:
            selected = str(uuid.UUID(str(values.get("organization_id"))))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid organization_id.") from None
        try:
            owned = await stwrd.list_organizations(session)
        except IdpUnavailable:
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None
        if selected not in {org.id for org in owned}:
            raise HTTPException(status_code=404, detail="Not found.")
        return_to = safe_target(
            values.get("return_to") if isinstance(values.get("return_to"), str) else None,
            stwrd.config.post_login_redirect,
        )
        state = stwrd.new_authorization_state(return_to=return_to)
        url = await stwrd.oidc.authorize_url(
            state=state.state,
            nonce=state.nonce,
            code_challenge=challenge_s256(state.code_verifier),
            organization_id=selected,
        )
        response = RedirectResponse(url, status_code=303)
        response.set_cookie(
            stwrd.config.tx_cookie,
            stwrd.seal(
                {
                    "state": state.state,
                    "nonce": state.nonce,
                    "code_verifier": state.code_verifier,
                    "return_to": state.return_to,
                    "switch": {
                        "from": session.id,
                        "sid": session.sid_idp,
                        "sub": session.sub,
                        "org": selected,
                    },
                }
            ),
            **_cookie_kwargs(stwrd, max_age=stwrd.config.transaction_ttl_s),
        )
        return response

    @router.post("/back-channel")
    async def back_channel(request: Request) -> Any:
        try:
            form = await request.form()
            logout_token = form.get("logout_token")
        except Exception:  # noqa: BLE001 - malformed body is just "no token"
            logout_token = None
        if not logout_token:
            return JSONResponse(
                {"error": "invalid_request"}, status_code=400, headers={"Cache-Control": "no-store"}
            )

        try:
            claims = await stwrd.oidc.validate_logout_token(str(logout_token))
        except IdpUnavailable:
            # 503 and not 400: the issuer retries a notice on a 5xx (same
            # policy as webhooks), whereas a 400 would tell it "this notice
            # is invalid, stop sending it" over a failure on the receiver's side.
            return JSONResponse(
                {"error": "idp_unavailable"},
                status_code=503,
                headers={"Cache-Control": "no-store"},
            )
        except OidcError as exc:
            return JSONResponse(
                {"error": str(exc)}, status_code=400, headers={"Cache-Control": "no-store"}
            )

        _prune_logout_jti()
        jti = claims["jti"]
        if jti in _seen_logout_jti:
            return JSONResponse(
                {"error": "replay"}, status_code=400, headers={"Cache-Control": "no-store"}
            )

        # `iss`/`aud` were already checked by `validate_logout_token`; what is
        # left is ending the local session. The store is keyed by the BFF's own
        # id and the notice only carries `sid`, so the id is *derived* from the
        # `sid` at login (`Stwrd.session_id_for_sid`) and the deletion is the
        # plain `delete(id)` of the store protocol — every store, including a
        # third-party one, terminates sessions correctly with no extra method
        # and no secondary index.
        sid = claims.get("sid")
        if sid:
            await stwrd.sessions.delete(stwrd.session_id_for_sid(sid))

        # The `jti` is marked seen only AFTER the deletion succeeded: if the
        # store is down the 500 makes the IdP retry, and the retry has to
        # find the `jti` unseen. Marking first turned that retry into a 400
        # "replay", which the IdP does not retry — the local session would
        # stay alive for good.
        _seen_logout_jti[jti] = time.time()

        return JSONResponse({"status": "ok"}, headers={"Cache-Control": "no-store"})

    @router.post("/webhook")
    async def webhook(request: Request) -> Any:
        body = await request.body()
        try:
            event = stwrd.verify_webhook(body, dict(request.headers))
        except ConfigError:
            return JSONResponse({"error": "webhook_not_configured"}, status_code=503)
        except DuplicateEventError:
            return JSONResponse({"status": "duplicate"})
        except InvalidSignatureError:
            return JSONResponse({"error": "invalid_signature"}, status_code=400)

        if on_event is not None:
            result = on_event(event)
            if inspect.isawaitable(result):
                await result
        return JSONResponse({"status": "ok"})

    return router


def _same_uuid(left: Any, right: Any) -> bool:
    try:
        return uuid.UUID(str(left)) == uuid.UUID(str(right))
    except ValueError:
        return False


def _new_session_id() -> str:
    import secrets

    return secrets.token_urlsafe(32)


# --- dependencies ----------------------------------------------------------


def _wants_json(request: Request) -> bool:
    """Everything that is not a navigation gets a JSON 401. `api_mode`
    forces this regardless of `Accept`; absent that, a request that accepts
    `text/html` is treated as a navigation and gets the redirect instead."""
    if getattr(request.state, "stwrd_api_mode", False):
        return True
    return "text/html" not in request.headers.get("accept", "")


def _deny(request: Request, stwrd: Stwrd) -> None:
    if _wants_json(request):
        raise HTTPException(status_code=401, detail="No session.")
    location = f"{stwrd.config.prefix}/sign-in?return_to={quote(_return_to_url(request))}"
    raise HTTPException(status_code=303, headers={"Location": location})


def api_mode(stwrd: Stwrd) -> Callable[[Request], Awaitable[None]]:
    """`Depends(api_mode(stwrd))` alongside another dependency below: forces
    a 401 JSON denial on this route even for a browser navigation, for an
    API endpoint that must never answer with a redirect."""

    async def _dep(request: Request) -> None:
        request.state.stwrd_api_mode = True

    return _dep


def optional_user(stwrd: Stwrd) -> Callable[[Request], Awaitable[StwrdUser | None]]:
    """`None` means there is no session, and nothing else does.

    When the IdP does not answer, this raises 503 instead of returning `None`,
    even though the dependency is called "optional": returning `None` would
    turn "cannot tell" into "anonymous", which for a page that renders
    differently depending on who is looking is a silent sign-out — without
    even an error anyone can see.
    """

    async def _dep(request: Request) -> StwrdUser | None:
        cookie = request.cookies.get(stwrd.config.session_cookie)
        try:
            session = await stwrd.resolve_session(cookie)
        except IdpUnavailable:
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None
        request.state.stwrd_user = session.user if session else None
        request.state.stwrd_organization = session.organization if session else None
        request.state.stwrd_consents = session.consents if session else {}
        return session.user if session is not None else None

    return _dep


def current_user(stwrd: Stwrd) -> Callable[[Request], Awaitable[StwrdUser]]:
    async def _dep(request: Request) -> StwrdUser:
        cookie = request.cookies.get(stwrd.config.session_cookie)
        try:
            session = await stwrd.resolve_session(cookie)
        except IdpUnavailable:
            # 503 and not the 401 of `_deny`: a 401 sends the person to sign
            # in again, which is exactly what must not happen to someone
            # whose session is still alive.
            raise HTTPException(status_code=503, detail=IDP_SILENT) from None
        if session is None:
            _deny(request, stwrd)
        assert session is not None  # `_deny` always raises
        request.state.stwrd_session = session
        request.state.stwrd_user = session.user
        request.state.stwrd_organization = session.organization
        request.state.stwrd_consents = session.consents
        return session.user

    return _dep


def require_auth(stwrd: Stwrd) -> Callable[[Request], Awaitable[None]]:
    """A guard with no return value, for a route that only needs "must be
    signed in" and does not read the user."""
    _current = current_user(stwrd)

    async def _dep(request: Request) -> None:
        await _current(request)

    return _dep


def require_role(stwrd: Stwrd, role: str) -> Callable[[Request], Awaitable[StwrdUser]]:
    """`require_role("org:admin")`. `org_roles`
    is an open registry — membership, never set equality."""
    _current = current_user(stwrd)

    async def _dep(request: Request) -> StwrdUser:
        user = await _current(request)
        if not request.state.stwrd_session.has_role(role):
            raise HTTPException(status_code=403, detail=f"Missing role {role}.")
        return user

    return _dep


def require_org(stwrd: Stwrd) -> Callable[[Request], Awaitable[StwrdUser]]:
    if "org" not in stwrd.config.scope.split():
        raise ConfigError("require_org needs the org scope.")
    _current = current_user(stwrd)

    async def _dep(request: Request) -> StwrdUser:
        user = await _current(request)
        if request.state.stwrd_session.organization is None:
            raise HTTPException(status_code=403, detail="The session has no organization.")
        return user

    return _dep


def require_permission(stwrd: Stwrd, permission: str) -> Callable[[Request], Awaitable[StwrdUser]]:
    _current = current_user(stwrd)

    async def _dep(request: Request) -> StwrdUser:
        user = await _current(request)
        if not request.state.stwrd_session.has_permission(permission):
            raise HTTPException(status_code=403, detail=f"Missing permission {permission}.")
        return user

    return _dep


# --- protect(): the opt-in fail-closed guard --------------------------------


class _ProtectMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, app: ASGIApp, *, stwrd: Stwrd, public: Iterable[str], auth_prefix: str
    ) -> None:
        super().__init__(app)
        self._stwrd = stwrd
        self._public = tuple(public)
        self._auth_prefix = auth_prefix

    def _is_public(self, path: str) -> bool:
        # Everything under the auth router's prefix is always public, without
        # being listed — the redirect target and the webhook receiver must be
        # reachable with no session.
        if path == self._auth_prefix or path.startswith(f"{self._auth_prefix}/"):
            return True
        for entry in self._public:
            if entry.endswith("*"):
                # Only a trailing `*` is a prefix match; a `*` anywhere else is
                # a literal character, not a wildcard.
                if path.startswith(entry[:-1]):
                    return True
            elif path == entry:
                return True
        return False

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if self._is_public(request.url.path):
            return await call_next(request)
        cookie = request.cookies.get(self._stwrd.config.session_cookie)
        try:
            session = await self._stwrd.resolve_session(cookie)
        except IdpUnavailable:
            # Neither the 401 nor the redirect to sign-in: both tell someone
            # with a live session that they lost it.
            return JSONResponse(
                {"detail": IDP_SILENT},
                status_code=503,
                headers={"Retry-After": "5"},
            )
        if session is not None:
            return await call_next(request)
        if _wants_json(request):
            return JSONResponse({"detail": "No session."}, status_code=401)
        location = f"{self._stwrd.config.prefix}/sign-in?return_to={quote(_return_to_url(request))}"
        return RedirectResponse(location, status_code=303)


def protect(
    app: Any,
    stwrd: Stwrd,
    *,
    public: Iterable[str] = (),
    prefix: str | None = None,
) -> None:
    """Fail-closed mode is opt-in (`protect(app)`): it requires a session on
    every path that is not declared public. `prefix` overrides
    which path is always public for the auth router itself, in case it was
    mounted somewhere other than `stwrd.config.prefix`.
    """
    auth_prefix = prefix if prefix is not None else stwrd.config.prefix
    app.add_middleware(_ProtectMiddleware, stwrd=stwrd, public=public, auth_prefix=auth_prefix)


__all__ = [
    "api_mode",
    "auth_router",
    "current_user",
    "optional_user",
    "protect",
    "require_auth",
    "require_org",
    "require_permission",
    "require_role",
    "safe_target",
]
