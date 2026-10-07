"""The relying-party OIDC client the BFF profile needs, and nothing more.

No protocol or cryptographic primitives are reimplemented here. Signature
verification is `joserfc` — the same JOSE library the identity provider (IdP)
signs with — never a hand-rolled base64/HMAC/RSA check. This module only adds
the relying-party bookkeeping the library does not do: PKCE, `state`/`nonce`,
the discovery and JWKS caches, and the specific claim checks (`iss`, `aud`,
`exp`/`iat`, `nonce`, `at_hash`).

The HTTP transport is injected (`Stwrd(..., http_client=...)`), so the whole
back-channel (token, JWKS, userinfo, discovery) can be pointed at an
in-process ASGI app in tests, with no socket involved.

**A deliberate choice: `httpx.AsyncClient`, not the sync
`httpx.Client`.** `httpx.ASGITransport` — the thing that lets a test mount an
ASGI app with no socket — has only ever implemented `handle_async_request`;
there is no version of httpx where a sync `Client` can use it (`Client.get()`
raises `AttributeError: 'ASGITransport' object has no attribute
'handle_request'`, verified against 0.27.2 and 0.28.1). Every FastAPI route
in `stwrd.fastapi` is already `async def`, so making the back-channel async
too costs nothing there and is the correct behaviour anyway — a sync HTTP
call from inside an async route blocks the whole event loop, not just that
request.
"""

from __future__ import annotations

import base64
import hashlib
import re
import secrets
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import httpx
from joserfc import jwt as joserfc_jwt
from joserfc.jwk import KeySet

from .config import OidcParams

# --- JWKS cache bounds --------------------------------------------------------
# The TTL comes from the issuer's `Cache-Control`, clamped. Lower bound
# because `max-age=0` would turn every validation into a network round trip
# (an amplifier against the issuer, and an RP that falls over when the IdP
# blips); upper bound because past the longest access token's lifetime the
# cache buys nothing.
JWKS_TTL_FLOOR_S = 10
JWKS_TTL_CEILING_S = 3600
JWKS_DEFAULT_TTL_S = 300  # no `Cache-Control`, or unreadable.

# On an unknown `kid` the JWKS is refetched right away, but at most once per
# this many seconds, so a token with a made-up `kid` cannot be used to amplify
# requests against the issuer.
JWKS_UNKNOWN_KID_REFETCH_FLOOR_S = 10

# The only algorithms this SDK accepts when verifying a signature: the two the
# IdP signs with. The list is fixed and never taken from the token's own
# unverified header: reading `alg` from there and passing it as `algorithms=`
# lets whoever forges the token choose the algorithm — for example `none`, or
# one whose public key doubles as an HMAC secret in an algorithm-confusion
# attack.
SUPPORTED_ALGS = ("RS256", "EdDSA")

_MAX_AGE_RE = re.compile(r"max-age=(\d+)")

# The `events` member every `logout_token` must carry.
LOGOUT_EVENT_URI = "http://schemas.openid.net/event/backchannel-logout"


class OidcError(RuntimeError):
    """The exchange itself is rejected: bad `state`, a code that will not
    be exchanged, an `id_token` that fails any of its checks.

    **The IdP ANSWERED, and the answer was no.** Its sibling below is the
    case where it did not answer at all, and the difference is the whole
    point of having two classes.
    """


#: Per-request timeout of the refresh exchange; the store lease is longer.
REFRESH_REQUEST_TIMEOUT_S = 10.0
#: The 4xx statuses that are not a rejection of the grant but a "not now":
#: request timeout (408), too early to retry this body (425) and rate limiting
#: (429, `{"error": "slow_down"}` with `Retry-After`). They are treated as
#: silence for the same reason as a 5xx: the IdP never looked at the credential.
RETRY_STATUSES: frozenset[int] = frozenset({408, 425, 429})


class IdpUnavailable(RuntimeError):
    """The IdP could not answer: no connection, a timeout, or a 5xx.

    **Not a rejection, and that is the entire distinction.** A rejected
    grant is the IdP
    exercising its authority: it looked at the credential and said no, and the
    only correct move is to end the local session. Silence is not an answer.
    Treating it as one converts every blip of the IdP —a restart, a node
    rotating, a second of packet loss— into a logout of everybody who happened
    to be renewing, which is a self-inflicted outage that buys nothing: an
    attacker who can make the IdP unreachable gains only the logout.

    **A 5xx counts as silence, and that is the case that actually bites.** An
    IdP under load answering `502` through the edge is not saying "this grant
    is bad"; it is saying nothing, loudly.

    **Three 4xx statuses count as silence too** (`RETRY_STATUSES`). The line
    is not "4xx = rejection": RFC 6749 section 5.2 lists grant rejections
    under 400 and does not promote every 4xx. A `429` from the token endpoint
    is `{"error": "slow_down"}` with `Retry-After` — the IdP saying "not
    now", not "this credential is invalid". Treating it as a rejection
    causes the very outage this class exists to prevent: the endpoint's rate
    limit is per `client_id`, so a large relying party that crosses it would
    sign out everyone who was renewing, and those users would return to
    `/authorize` and amplify the load that triggered the limit.

    What this class must NEVER be used to justify is serving stale claims:
    that is the hole to avoid. The caller's move is to answer 503 and
    keep the session, so the next request —seconds later, IdP back— renews and
    nobody noticed.

    `request_sent` says whether the IdP may have processed the request: False
    when it never left (connection phase) or the IdP said "not now" (503 and
    `RETRY_STATUSES`); True otherwise. A refresh whose request may have been
    processed must never be replayed: the token may already be rotated.
    """

    def __init__(self, message: str = "", *, request_sent: bool = True) -> None:
        super().__init__(message)
        self.request_sent = request_sent


class RefreshUncertain(IdpUnavailable):
    """An earlier refresh may have been processed without its result stored:
    the consumed refresh token is never replayed. The session yields no
    authority (503) but a new sign-in is allowed and replaces it."""


def _clamp_ttl(cache_control: str | None) -> int:
    if not cache_control:
        return JWKS_DEFAULT_TTL_S
    match = _MAX_AGE_RE.search(cache_control.lower())
    if not match:
        return JWKS_DEFAULT_TTL_S
    seconds = int(match.group(1))
    return max(JWKS_TTL_FLOOR_S, min(seconds, JWKS_TTL_CEILING_S))


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _keyset_has_kid(keyset: KeySet, kid: str) -> bool:
    # `KeySet.get_by_kid` raises `InvalidKeyIdError` for a `kid` it does not
    # have rather than returning `None` — a membership check, not a lookup.
    try:
        keyset.get_by_kid(kid)
    except Exception:  # noqa: BLE001 - joserfc's own error hierarchy
        return False
    return True


# --- PKCE + state/nonce --------------------------------------------------------

VERIFIER_BYTES = 32  # 43 base64url chars once encoded, inside RFC 7636's 43-128.


def generate_verifier() -> str:
    return _b64url(secrets.token_bytes(VERIFIER_BYTES))


def challenge_s256(verifier: str) -> str:
    return _b64url(hashlib.sha256(verifier.encode("ascii")).digest())


def new_state() -> str:
    return _b64url(secrets.token_bytes(24))


def new_nonce() -> str:
    return _b64url(secrets.token_bytes(24))


def half_hash(token: str, alg: str) -> str:
    """`at_hash`: half of the digest of `token`, base64url with no padding.

    The hash is that of the access token from the same response (sha256 with
    RS256, sha512 with EdDSA). The digest algorithm
    tracks the `id_token`'s signing algorithm, not a fixed choice — a client
    that signs with EdDSA gets a sha512-based `at_hash`, same as the IdP that
    minted the token.
    """
    digest = (
        hashlib.sha256(token.encode("ascii"))
        if alg == "RS256"
        else hashlib.sha512(token.encode("ascii"))
    )
    raw = digest.digest()
    return _b64url(raw[: len(raw) // 2])


# --- discovery -----------------------------------------------------------------


@dataclass(frozen=True)
class Discovery:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    end_session_endpoint: str | None
    revocation_endpoint: str | None
    #: The raw discovery document, for consumers that validate extra metadata
    #: (the Management destination) with their own rules.
    document: Mapping[str, Any] = field(default_factory=dict, compare=False)


@dataclass
class _JwksEntry:
    keyset: KeySet
    fetched_at: float
    ttl_s: int


class OidcClient:
    """One tenant's worth of OIDC plumbing, over an injected
    `httpx.AsyncClient`."""

    def __init__(self, http_client: httpx.AsyncClient, params: OidcParams) -> None:
        self._http = http_client
        self.params = params
        self._discovery: Discovery | None = None
        self._jwks: _JwksEntry | None = None
        self._jwks_last_refetch: float = 0.0

    # -- discovery --------------------------------------------------------

    async def _ask(self, method: str, url: str, *, what: str, **kwargs: Any) -> httpx.Response:
        """Every call to the IdP goes through here, so the split between "did
        not respond" and "responded no" is written ONCE.

        Four copies of this `try` would be four chances to forget one, and the
        forgotten one is the one that signs everybody out the day the IdP
        restarts. Returns the response for the caller to judge; raises
        `IdpUnavailable` when there is nothing to judge.
        """
        try:
            response = await self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise IdpUnavailable(
                f"{what}: the IdP did not respond ({exc.__class__.__name__}).",
                request_sent=not isinstance(
                    exc, (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)
                ),
            ) from exc
        if response.status_code >= 500 or response.status_code in RETRY_STATUSES:
            raise IdpUnavailable(
                f"{what}: the IdP responded {response.status_code}.",
                request_sent=not (
                    response.status_code == 503 or response.status_code in RETRY_STATUSES
                ),
            )
        return response

    async def discover(self, *, force: bool = False) -> Discovery:
        if self._discovery is not None and not force:
            return self._discovery
        url = f"{self.params.issuer.rstrip('/')}/.well-known/openid-configuration"
        response = await self._ask("GET", url, what="Discovery")
        if response.status_code != 200:
            raise OidcError(f"Discovery at {self.params.issuer} responded {response.status_code}.")
        doc = response.json()
        try:
            self._discovery = Discovery(
                issuer=doc["issuer"],
                authorization_endpoint=doc["authorization_endpoint"],
                token_endpoint=doc["token_endpoint"],
                userinfo_endpoint=doc["userinfo_endpoint"],
                jwks_uri=doc["jwks_uri"],
                end_session_endpoint=doc.get("end_session_endpoint"),
                revocation_endpoint=doc.get("revocation_endpoint"),
                document=doc,
            )
        except KeyError as exc:
            raise OidcError(f"The discovery document does not include {exc}.") from exc
        return self._discovery

    async def supports_end_session(self) -> bool:
        """Whether the IdP advertises an `end_session_endpoint`. The router
        degrades on this instead of assuming one, so the day the endpoint is
        advertised the behaviour needs no SDK change."""
        discovery = await self.discover()
        return discovery.end_session_endpoint is not None

    # -- JWKS, cached by the issuer's Cache-Control ------------------------

    async def _fetch_jwks(self) -> _JwksEntry:
        discovery = await self.discover()
        response = await self._ask("GET", discovery.jwks_uri, what="JWKS")
        if response.status_code != 200:
            raise OidcError(f"The JWKS responded {response.status_code}.")
        ttl = _clamp_ttl(response.headers.get("cache-control"))
        keyset = KeySet.import_key_set(response.json())
        entry = _JwksEntry(keyset=keyset, fetched_at=time.monotonic(), ttl_s=ttl)
        self._jwks = entry
        self._jwks_last_refetch = entry.fetched_at
        return entry

    async def _keyset_for(self, kid: str) -> KeySet:
        entry = self._jwks
        now = time.monotonic()
        if entry is None or now - entry.fetched_at >= entry.ttl_s:
            entry = await self._fetch_jwks()
        if not _keyset_has_kid(entry.keyset, kid):
            if now - self._jwks_last_refetch >= JWKS_UNKNOWN_KID_REFETCH_FLOOR_S:
                entry = await self._fetch_jwks()
        return entry.keyset

    # -- PKCE + authorize URL ----------------------------------------------

    async def authorize_url(
        self,
        *,
        state: str,
        nonce: str,
        code_challenge: str,
        organization_id: str | None = None,
    ) -> str:
        discovery = await self.discover()
        query = {
            "response_type": "code",
            "client_id": self.params.client_id,
            "redirect_uri": self.params.redirect_uri,
            "scope": self.params.scope,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if organization_id:
            query["organization_id"] = organization_id
        return str(httpx.URL(discovery.authorization_endpoint, params=query))

    # -- code exchange -------------------------------------------------------

    async def exchange_code(self, *, code: str, code_verifier: str) -> dict[str, Any]:
        discovery = await self.discover()
        response = await self._ask(
            "POST",
            discovery.token_endpoint,
            what="Code exchange",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.params.redirect_uri,
                "client_id": self.params.client_id,
                "client_secret": self.params.client_secret,
                "code_verifier": code_verifier,
            },
        )
        if response.status_code != 200:
            raise OidcError(f"The code exchange failed with {response.status_code}.")
        return response.json()

    # -- refresh ---------------------------------------------------------

    async def exchange_refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """The refresh exchange, used by `Stwrd.resolve_session` when the
        access token has expired and the session holds a `refresh_token`.

        **Two exceptions, and which one is raised decides whether anyone is
        signed out.**
        `OidcError` is a rejection the IdP issued —a revoked refresh, a reused
        one, a dead family— and the caller's move is to end the local session.
        `IdpUnavailable` is no answer at all (connection, timeout, 5xx), and
        the caller's move is to keep the session and fail the request: the IdP
        never said this credential was bad.
        """
        discovery = await self.discover()
        response = await self._ask(
            "POST",
            discovery.token_endpoint,
            what="Refresh token renewal",
            # Shorter than the store lease, so a hung IdP cannot outlive it.
            timeout=REFRESH_REQUEST_TIMEOUT_S,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.params.client_id,
                "client_secret": self.params.client_secret,
            },
        )
        if response.status_code != 200:
            raise OidcError(f"The refresh_token renewal failed with {response.status_code}.")
        return response.json()

    # -- id_token validation ---------------------------------------------

    async def validate_id_token(
        self, id_token: str, *, nonce: str | None, access_token: str
    ) -> dict[str, Any]:
        """Signature, `iss`, `aud`, `exp`/`iat`, `nonce`, `at_hash`.

        Used by `GET /auth/callback`. Any rejection is `OidcError`; the
        router turns that into a 400.
        """
        claims, alg = await self._verify_jws(id_token, what="id_token")
        discovery = await self.discover()
        if claims.get("iss") != discovery.issuer:
            raise OidcError("The id_token carries an iss different from the tenant's issuer.")
        aud = claims.get("aud")
        aud_list = aud if isinstance(aud, list) else [aud]
        if self.params.client_id not in aud_list:
            raise OidcError("The id_token does not carry this client_id in aud.")
        exp = claims.get("exp")
        iat = claims.get("iat")
        if not isinstance(exp, int | float) or not isinstance(iat, int | float):
            raise OidcError("The id_token does not carry exp/iat.")
        if time.time() >= exp:
            raise OidcError("The id_token is expired.")
        if claims.get("nonce") != nonce:
            raise OidcError("The id_token nonce does not match the transaction's.")
        expected_at_hash = half_hash(access_token, alg)
        if not secrets.compare_digest(claims.get("at_hash", ""), expected_at_hash):
            raise OidcError("The id_token at_hash does not match the access_token.")
        return claims

    # -- userinfo -----------------------------------------------------------

    async def userinfo(self, access_token: str) -> dict[str, Any]:
        """Userinfo is not optional for the BFF profile: the email address
        does not travel in the `id_token`, so the SDK queries userinfo on each
        issuance."""
        discovery = await self.discover()
        response = await self._ask(
            "GET",
            discovery.userinfo_endpoint,
            what="userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise OidcError(f"userinfo responded {response.status_code}.")
        return response.json()

    # -- back-channel logout_token -------------------------------------------

    async def validate_logout_token(self, logout_token: str) -> dict[str, Any]:
        """Same signature (same issuer/algorithm as the `id_token`),
        `iss`, `aud`,
        `exp`, the `events` member naming
        `http://schemas.openid.net/event/backchannel-logout`, `sid` or
        `sub`, and the absence of `nonce` (OpenID Connect Back-Channel Logout
        forbids it). Replay of `jti` is the router's job (`auth_router`
        keeps the seen set; this method only asserts `jti` is present).
        """
        claims, _alg = await self._verify_jws(logout_token, what="logout_token")
        discovery = await self.discover()
        if claims.get("iss") != discovery.issuer:
            raise OidcError("The logout_token carries an iss different from the tenant's issuer.")
        aud = claims.get("aud")
        aud_list = aud if isinstance(aud, list) else [aud]
        if self.params.client_id not in aud_list:
            raise OidcError("The logout_token does not carry this client_id in aud.")
        exp = claims.get("exp")
        if not isinstance(exp, int | float) or time.time() >= exp:
            raise OidcError("The logout_token is expired or does not carry exp.")
        if "nonce" in claims:
            raise OidcError("The logout_token must not carry a nonce (the RFC forbids it).")
        events = claims.get("events")
        if not isinstance(events, dict) or LOGOUT_EVENT_URI not in events:
            raise OidcError(f"The logout_token does not declare the {LOGOUT_EVENT_URI!r} event.")
        if not claims.get("sid") and not claims.get("sub"):
            raise OidcError("The logout_token does not carry sid or sub.")
        if not claims.get("jti"):
            raise OidcError("The logout_token does not carry jti.")
        return claims

    # -- shared signature verification --------------------------------------

    async def _verify_jws(self, token: str, *, what: str) -> tuple[dict[str, Any], str]:
        """Peeks the unverified header for `kid`/`alg`, resolves the key
        against the JWKS, verifies the signature and returns `(claims,
        alg)`. Shared by `validate_id_token` and `validate_logout_token`: the
        `logout_token` is signed by the same issuer with the same algorithms
        as the `id_token`, so the same machinery verifies both.

        The unverified header's `alg` is only used to pick which half of
        `at_hash` applies (see `half_hash`) — never as the list of allowed
        algorithms for `joserfc_jwt.decode`, which is always the fixed
        constant `SUPPORTED_ALGS`. Trusting the header for that would let
        whoever signs the token choose its own algorithm (`none`, or an
        RS256/EdDSA confusion).
        """
        unverified = _unverified_header(token)
        kid = unverified.get("kid")
        alg = unverified.get("alg")
        if not kid or alg not in SUPPORTED_ALGS:
            raise OidcError(f"The {what} does not carry a recognizable kid/alg in the header.")
        keyset = await self._keyset_for(kid)
        try:
            decoded = joserfc_jwt.decode(token, key=keyset, algorithms=list(SUPPORTED_ALGS))
        except Exception as exc:  # joserfc raises its own hierarchy
            raise OidcError(f"The {what} signature does not verify: {exc}") from exc
        return decoded.claims, alg


def _unverified_header(token: str) -> dict[str, Any]:
    import json

    try:
        header_b64 = token.split(".", 1)[0]
        padded = header_b64 + "=" * (-len(header_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception as exc:  # noqa: BLE001 - any malformed token is one error
        raise OidcError(f"The id_token is not a valid JWT: {exc}") from exc


__all__ = [
    "JWKS_DEFAULT_TTL_S",
    "JWKS_TTL_CEILING_S",
    "JWKS_TTL_FLOOR_S",
    "JWKS_UNKNOWN_KID_REFETCH_FLOOR_S",
    "LOGOUT_EVENT_URI",
    "SUPPORTED_ALGS",
    "Discovery",
    "RETRY_STATUSES",
    "RefreshUncertain",
    "IdpUnavailable",
    "OidcClient",
    "OidcError",
    "challenge_s256",
    "generate_verifier",
    "half_hash",
    "new_nonce",
    "new_state",
]
