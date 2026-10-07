"""`Stwrd` — the object an app builds once and hands to `auth_router`.

Ties `StwrdConfig`, the `OidcClient`, a `SessionStore` and the webhook dedup
set together, and owns the cookie sealing that keeps every secret (tokens,
`id_token` claims) on the server side — the browser only ever sees an opaque,
HMAC-signed cookie value.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import math
import secrets
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx

from .config import ConfigError, StwrdConfig
from .oidc import (
    IdpUnavailable,
    OidcClient,
    OidcError,
    RefreshUncertain,
    generate_verifier,
    new_nonce,
    new_state,
)
from .organizations import OwnOrganization, list_own_organizations
from .sessions import (
    AUTHORITY_KEYS,
    MemoryStore,
    RefreshClaim,
    SessionStore,
    StwrdSession,
    Tokens,
    merge_userinfo,
)
from .webhooks import DuplicateEventError, InvalidSignatureError, SeenWebhookIds, WebhookEvent
from .webhooks import safe_equal as _safe_equal
from .webhooks import verify_webhook as _verify_webhook

# Longer than the IdP HTTP timeout so a live exchange never loses its lease; a
# waiting worker polls for the lease holder's result for at most REFRESH_WAIT_S.
REFRESH_LEASE_S = 30.0
REFRESH_WAIT_S = 10.0


def _finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Non-finite expiry.")
    return value


@dataclass(frozen=True)
class AuthorizationState:
    """The pending-login transaction: `state`, `nonce` and the PKCE verifier
    are kept server-side, and the browser only carries an opaque blob. This
    is that state, sealed into the `tx_cookie`; the browser round-trips only
    the sealed value.
    """

    state: str
    nonce: str
    code_verifier: str
    return_to: str
    created_at: float


def connect_to_hook(connect_to: str) -> Callable[[httpx.Request], Awaitable[None]]:
    """The `httpx` request hook behind `StwrdConfig.connect_to`: every
    request goes to `connect_to`'s scheme/host/port while its path, query
    and `Host` header stay the issuer's — the IdP routes the tenant by
    `Host`, so this is how an app talks to an IdP on `127.0.0.1` AS
    `app.example.com` without DNS or `/etc/hosts`. Public so that an app
    that builds its own `httpx.AsyncClient` (a proxy, a custom transport)
    can install the same hook instead of re-deriving it.
    """
    parts = urlsplit(connect_to)
    scheme = parts.scheme
    host = parts.hostname or ""
    port = parts.port

    async def to_target(request: httpx.Request) -> None:
        # `httpx` fixed `Host` from the original URL when it built the
        # request; `copy_with` on the URL leaves the header alone.
        request.url = request.url.copy_with(scheme=scheme, host=host, port=port)

    return to_target


def _own_http_client(config: StwrdConfig) -> httpx.AsyncClient:
    if config.connect_to is None:
        return httpx.AsyncClient()
    return httpx.AsyncClient(event_hooks={"request": [connect_to_hook(config.connect_to)]})


class Stwrd:
    """`Stwrd(config, *, sessions=None, http_client=None)`.

    `http_client` is injected — an `httpx.AsyncClient` — which is what makes
    the end-to-end flow testable without sockets: a test mounts it against an
    in-process ASGI app with `ASGITransport` and every back-channel call
    (discovery, token, JWKS, userinfo) goes through it with no network
    involved. It is an `AsyncClient` and not the sync `httpx.Client` because
    `ASGITransport` only implements async requests.
    """

    def __init__(
        self,
        config: StwrdConfig,
        *,
        sessions: SessionStore | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config
        self.sessions: SessionStore = sessions if sessions is not None else MemoryStore()
        self._http_owned = http_client is None
        self._http: httpx.AsyncClient = (
            http_client if http_client is not None else _own_http_client(config)
        )
        self.oidc = OidcClient(self._http, config.oidc())
        self.seen_webhook_ids = SeenWebhookIds()

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        **overrides: object,
    ) -> Stwrd:
        """`StwrdConfig.from_env` builds the config; `sessions`/`http_client`
        are runtime objects, not environment values, so they are pulled out
        of `overrides` before the rest reaches `StwrdConfig.from_env`."""
        sessions = overrides.pop("sessions", None)  # type: ignore[assignment]
        http_client = overrides.pop("http_client", None)  # type: ignore[assignment]
        config = StwrdConfig.from_env(environ, **overrides)  # type: ignore[arg-type]
        return cls(config, sessions=sessions, http_client=http_client)  # type: ignore[arg-type]

    async def close(self) -> None:
        """Close the HTTP client, but only if this instance created it.

        Closing an injected client would surprise whoever owns it.
        """
        if self._http_owned:
            await self._http.aclose()

    # --- cookie sealing -------------------------------------------------

    def _sign(self, data: str) -> str:
        key = self.config.cookie_secret.encode("utf-8")
        mac = hmac.new(key, data.encode("utf-8"), hashlib.sha256)
        return base64.urlsafe_b64encode(mac.digest()).rstrip(b"=").decode("ascii")

    def seal(self, value: Any) -> str:
        """HMAC-signed, base64url cookie value. Not encryption — nothing
        sealed carries a secret the browser must not read (session ids,
        `state`/`nonce`/PKCE verifier are all opaque already); what this
        buys is tamper-evidence, so a forged cookie unseals to nothing."""
        payload = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
        return f"{payload_b64}.{self._sign(payload_b64)}"

    def unseal(self, cookie: str | None) -> Any | None:
        """`None` on anything wrong — missing cookie, bad signature, bad
        JSON. The caller (the router) always treats that the same as "no
        session"/"no transaction", never as an error to surface."""
        if not cookie or "." not in cookie:
            return None
        payload_b64, _, signature = cookie.rpartition(".")
        if not signature or not _safe_equal(signature, self._sign(payload_b64)):
            return None
        try:
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            return json.loads(base64.urlsafe_b64decode(padded))
        except (ValueError, UnicodeDecodeError):
            return None

    def session_id_for_sid(self, sid: str) -> str:
        """The local session id for an IdP session — derived, never random.

        This is what makes back-channel logout able to actually end the local
        session. The IdP's notice only carries `sid`; the `SessionStore`
        protocol looks sessions up by the BFF's own opaque id. Deriving one
        from the other closes that gap **without extending the protocol**:
        logout becomes `store.delete(session_id_for_sid(sid))` using the
        `delete(id)` every store already implements, including third-party
        ones. The alternative — adding `delete_by_sid` — would break existing
        stores and cost a secondary index (and one extra write per login) in
        every real store.

        The derivation is keyed, so the id is not guessable from a `sid` that
        leaked. Rotating `cookie_secret` changes it and orphans the mapping —
        which costs nothing, because that same rotation already invalidates
        every sealed cookie, so those sessions are unreachable anyway.
        """
        return self._sign(f"sid:{sid}")

    def csrf(self, session_id: str) -> str:
        """A CSRF token derived from the session id, not stored separately —
        recomputing it is a comparison, never a lookup. CSRF protection is mandatory."""
        return self._sign(f"csrf:{session_id}")

    # --- authorization state (the sign-in transaction) -------------------

    def new_authorization_state(self, *, return_to: str = "/") -> AuthorizationState:
        return AuthorizationState(
            state=new_state(),
            nonce=new_nonce(),
            code_verifier=generate_verifier(),
            return_to=return_to,
            created_at=time.time(),
        )

    # --- organizations -----------------------------------------------------

    def organization_selection_enabled(self) -> bool:
        """Organization selection needs the `org` scope to be requested
        explicitly; it is never added automatically."""
        return "org" in self.config.scope.split()

    async def list_organizations(self, session: StwrdSession) -> list[OwnOrganization]:
        """The person's own usable organizations, read with their access token."""
        discovery = await self.oidc.discover()
        return await list_own_organizations(
            self._http, self.config.issuer, discovery, session.tokens.access_token
        )

    # --- sessions ----------------------------------------------------------

    async def resolve_session(self, cookie: str | None) -> StwrdSession | None:
        """The session ready to authorize with — renews tokens if the store
        and the session support it.

        **The refresh branch.** With no `refresh_token` on the
        session (no `offline_access` at login), the credential's lifetime is
        still the access token's — unchanged. With one, an
        expired access token is renewed against the token endpoint instead
        of ending the session outright; a **rejection** of that renewal
        (revoked, reused, a dead family) still ends the local session,
        because at that point the SDK can no longer vouch for the claims it
        is holding; carrying on with the old ones would be the hole.

        **An IdP that does not answer is not a rejection, so it ends
        nothing.** `IdpUnavailable` propagates to the caller instead of
        becoming `None`: the IdP did not say the credential is invalid, it
        said nothing. Turning silence into "no session" would sign out
        everyone who was renewing every time the IdP restarted, and would buy
        no security — the hole is serving stale claims, and this does not:
        it returns no session, it raises. The caller answers 503 and the
        session stays for the next attempt.
        """
        payload = self.unseal(cookie)
        if not payload or not isinstance(payload, dict) or "sid" not in payload:
            return None
        session = await self.sessions.get(payload["sid"])
        if session is None:
            return None
        if session.is_expired():
            await self.sessions.delete(session.id)
            return None
        if session.access_token_expired():
            if not session.tokens.refresh_token:
                # Without `offline_access` there is no renewal: the
                # credential's lifetime is the access token's.
                await self.sessions.delete(session.id)
                return None
            # `_renew` raises `IdpUnavailable` and it is deliberately NOT
            # caught here: that exception is the difference between "no
            # session" and "cannot tell right now", and catching it would
            # delete the session.
            renewed = await self._renew(session)
            if renewed is None:
                await self.sessions.delete(session.id)
                return None
            return renewed
        return session

    async def _renew(self, session: StwrdSession) -> StwrdSession | None:
        """Refresh `session` under the store's lease: across every worker the
        refresh token is exchanged at most once.

        `None` when the IdP REJECTED the renewal (revoked, reused, dead
        family, unreadable answer) or the session was deleted meanwhile;
        `resolve_session` then ends the local session.

        `IdpUnavailable` propagates when nothing can be vouched for right now:
        the IdP is silent, another worker holds the lease for too long, or an
        earlier exchange may have rotated the refresh token without its result
        being stored (`uncertain`). The last case is permanent for that
        session: the consumed token is never replayed, so the user signs in
        again. A request that provably never left (`request_sent=False`)
        releases the lease and the next request simply retries.
        """
        owner = secrets.token_urlsafe(16)
        deadline = time.monotonic() + REFRESH_WAIT_S
        current = session
        while True:
            claim = await self.sessions.claim_refresh(current.id, owner, REFRESH_LEASE_S)
            if claim.status == "granted":
                return await self._renew_owned(claim)
            if claim.status == "gone":
                return None
            if claim.status == "uncertain":
                raise RefreshUncertain(
                    "A refresh may have been processed without its result; sign in again."
                )
            if time.monotonic() >= deadline:
                raise IdpUnavailable("Another worker is still refreshing this session.")
            await asyncio.sleep(0.05)
            latest = await self.sessions.get(current.id)
            if latest is None or latest.is_expired():
                return None
            if not latest.access_token_expired():
                return latest
            current = latest

    async def _renew_owned(self, claim: RefreshClaim) -> StwrdSession | None:
        assert claim.session is not None
        session, fence = claim.session, claim.fence
        if claim.phase == "acquired":
            if not session.access_token_expired():
                await self.sessions.release_refresh(session.id, fence, sent=False)
                return session
            if not session.tokens.refresh_token:
                await self.sessions.release_refresh(session.id, fence, sent=False)
                return None
            try:
                # Discovery is read before anything is marked as sent: a failure
                # here proves nothing left for the token endpoint.
                await self.oidc.discover()
            except IdpUnavailable:
                await self.sessions.release_refresh(session.id, fence, sent=False)
                raise
            except OidcError:
                await self.sessions.release_refresh(session.id, fence, sent=False)
                raise IdpUnavailable("The IdP discovery document is unusable.") from None
            if not await self.sessions.mark_refresh_sent(session.id, fence):
                raise IdpUnavailable("The refresh lease was lost; try again.")
            try:
                token_response = await self.oidc.exchange_refresh_token(
                    session.tokens.refresh_token
                )
            except IdpUnavailable as exc:
                await self.sessions.release_refresh(session.id, fence, sent=exc.request_sent)
                raise
            except (OidcError, KeyError):
                return None
            now = time.time()
            try:
                tokens = Tokens(
                    access_token=token_response["access_token"],
                    id_token=token_response.get("id_token", session.tokens.id_token),
                    token_type=token_response.get("token_type", "Bearer"),
                    expires_at=_finite(now + float(token_response.get("expires_in", 3600))),
                    refresh_token=token_response.get("refresh_token"),
                )
            except (KeyError, TypeError, ValueError):
                return None
            fresh_id_token = bool(token_response.get("id_token"))
            # The exchange happened: the old refresh token is consumed. Store
            # the rotation before any further network call. If the lease was
            # lost (logout, takeover) the session ends instead of resurrecting.
            if not await self.sessions.checkpoint_refresh(
                session.id, fence, tokens, fresh_id_token=fresh_id_token
            ):
                return await self._lease_lost(session.id)
            access_token = tokens.access_token
        else:
            tokens = session.tokens
            fresh_id_token = claim.fresh_id_token
            access_token = tokens.access_token
            now = time.time()

        try:
            userinfo_claims = await self.oidc.userinfo(access_token)
            id_claims: dict[str, Any] = {}
            if fresh_id_token:
                id_claims = await self.oidc.validate_id_token(
                    tokens.id_token, nonce=None, access_token=access_token
                )
        except IdpUnavailable:
            # Tokens are checkpointed: a later claim retries userinfo only.
            await self.sessions.release_refresh(session.id, fence, sent=True)
            raise
        except (OidcError, KeyError):
            return None

        if id_claims and id_claims.get("sub") != session.sub:
            return None
        base = (
            id_claims
            if fresh_id_token
            else {k: v for k, v in session.claims.items() if k not in AUTHORITY_KEYS}
        )
        try:
            claims = merge_userinfo(base, userinfo_claims)
        except OidcError:
            return None
        renewed = StwrdSession(
            id=session.id,
            sid_idp=claims.get("sid", session.sid_idp),
            sub=session.sub,
            claims=claims,
            tokens=tokens,
            expires_at=now + self.config.session_ttl_s,
            access_expires_at=tokens.expires_at,
        )
        if not await self.sessions.complete_refresh(session.id, fence, renewed):
            return await self._lease_lost(session.id)
        return renewed

    async def _lease_lost(self, session_id: str) -> None:
        """A lost lease is not a rejection: only a session that no longer
        exists ends (logout). One that is still there, possibly re-created by a
        new sign-in, must not be deleted by a stale owner."""
        if await self.sessions.get(session_id) is None:
            return None
        raise IdpUnavailable("The refresh lease was lost; try again.")

    async def session_from_cookie(self, cookie: str | None) -> StwrdSession | None:
        """Raw store read: unseals the cookie and looks the session up, with
        no renewal and no expiry side effects.

        This is async like the rest of `SessionStore`, so a real store — Redis,
        a database table — can do I/O.
        """
        payload = self.unseal(cookie)
        if not payload or not isinstance(payload, dict) or "sid" not in payload:
            return None
        return await self.sessions.get(payload["sid"])

    # --- webhooks -----------------------------------------------------

    def verify_webhook(self, body: bytes, headers: Mapping[str, str]) -> WebhookEvent:
        """`POST /auth/webhook`. Deduplicates against
        `self.seen_webhook_ids` (a 30-hour window). Raises `ConfigError` if no
        `webhook_secret` is configured — the router turns that into a 503."""
        if not self.config.webhook_secret:
            raise ConfigError(
                "STWRD_WEBHOOK_SECRET is not configured: no webhook can be "
                "verified without a secret."
            )
        return _verify_webhook(
            body,
            headers,
            self.config.webhook_secret,
            seen=self.seen_webhook_ids,
        )


__all__ = [
    "AuthorizationState",
    "ConfigError",
    "DuplicateEventError",
    "InvalidSignatureError",
    "OidcError",
    "Stwrd",
    "connect_to_hook",
]
