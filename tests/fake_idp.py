"""A minimal OIDC provider that follows the standard — a test double, not a
second IdP.

It lets `test_auth_router.py` and `test_oidc.py` exercise the router's real
HTTP behaviour — discovery, JWKS, the code exchange, `id_token` validation,
userinfo — without depending on a running identity provider, so this
package's suite runs on its own.

**Not** an `/oidc/authorize` implementation: a real login screen is not part
of it, so this server has no such route. `issue_code()` stands in for "the
login screen finished and is redirecting back with a code" — a test calls it
directly instead of driving a fake login UI.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from joserfc import jwt as joserfc_jwt
from joserfc.jwk import RSAKey

ISSUER = "https://idp.example.com"
KID = "test-kid-1"
ALG = "RS256"


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def half_hash(token: str) -> str:
    digest = hashlib.sha256(token.encode("ascii")).digest()
    return _b64url(digest[: len(digest) // 2])


@dataclass
class FakeIdp:
    client_id: str
    client_secret: str
    redirect_uri: str
    advertise_end_session: bool = False

    # The refresh grant. `None` means "reject every
    # refresh_token grant with invalid_grant" — the default, so a test that
    # never asks for `with_refresh` on `issue_code` never accidentally gets
    # one either.
    refresh_status_code: int = 200

    #: `GET /api/v1/me/memberships` items (`{"organization": {"id", "display_name"},
    #: "active"}`), served `memberships_page_size` at a time, or the given status.
    memberships: list[dict[str, Any]] = field(default_factory=list)
    memberships_page_size: int = 200
    memberships_status: int = 200
    #: Management destination advertised by discovery; tests override it.
    management_base_url: str = f"{ISSUER}/api/v1"
    management_audience: str = ISSUER

    key: RSAKey = field(init=False, repr=False)
    public_jwk: dict[str, Any] = field(init=False)
    app: FastAPI = field(init=False, repr=False)
    _codes: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    _userinfo_by_token: dict[str, dict[str, Any]] = field(
        default_factory=dict, init=False, repr=False
    )
    _refresh_tokens: dict[str, dict[str, Any]] = field(default_factory=dict, init=False, repr=False)
    #: presented refresh_token values, in order — what a test asserts calls on.
    refresh_calls: list[str] = field(default_factory=list, init=False, repr=False)
    #: Authorization headers presented to the memberships endpoint.
    membership_authorizations: list[str] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.key = RSAKey.generate_key(2048, private=True)
        public = dict(self.key.as_dict(private=False))
        public["kid"] = KID
        public["alg"] = ALG
        public["use"] = "sig"
        self.public_jwk = public
        self.app = self._build_app()

    def issue_code(
        self,
        *,
        sub: str,
        nonce: str | None = None,
        userinfo: dict[str, Any] | None = None,
        with_refresh: bool = False,
        id_claims: dict[str, Any] | None = None,
    ) -> str:
        """A one-time code bound to `sub`, the `nonce` the fake authorize
        request would have carried, and the body the fake `/oidc/userinfo`
        will answer for the access token this code turns into.

        `with_refresh=True`: the exchange also mints a
        `refresh_token`, standing in for a real authorize that asked for
        `offline_access`.
        """
        code = secrets.token_urlsafe(16)
        body = {"sub": sub, **(userinfo or {})}
        body.setdefault("sub", sub)
        self._codes[code] = {
            "sub": sub,
            "nonce": nonce,
            "userinfo": body,
            "with_refresh": with_refresh,
            "id_claims": id_claims or {},
        }
        return code

    def sign(self, claims: dict[str, Any], *, alg: str = ALG) -> str:
        """Exposed for tests that need a hand-built token — an expired one,
        one with the wrong `aud`, a `logout_token` — signed with this same
        key so `OidcClient`'s JWKS-backed verification is what is exercised.
        """
        return joserfc_jwt.encode({"alg": alg, "kid": KID}, claims, self.key)

    def forge_unsigned(self, claims: dict[str, Any], *, alg: str = "none", kid: str = KID) -> str:
        """A hand-assembled `header.payload.` with an empty signature —
        `joserfc_jwt.encode` refuses to mint `alg: none` on purpose
        (`UnsupportedAlgorithmError`), so this bypasses it the way an
        attacker would: build the three JWS segments directly. Exists to
        prove `OidcClient` rejects a token whose `alg` it is told to trust
        blindly (a CVE-2015-9235-shaped attack)."""
        header = {"alg": alg, "kid": kid}
        header_b64 = _b64url(json.dumps(header).encode("ascii"))
        payload_b64 = _b64url(json.dumps(claims).encode("ascii"))
        return f"{header_b64}.{payload_b64}."

    def _build_app(self) -> FastAPI:
        app = FastAPI()

        @app.get("/.well-known/openid-configuration")
        async def discovery() -> dict[str, Any]:
            doc: dict[str, Any] = {
                "issuer": ISSUER,
                "authorization_endpoint": f"{ISSUER}/oidc/authorize",
                "token_endpoint": f"{ISSUER}/oidc/token",
                "userinfo_endpoint": f"{ISSUER}/oidc/userinfo",
                "jwks_uri": f"{ISSUER}/.well-known/jwks.json",
                "management_api_base_url": self.management_base_url,
                "management_api_audience": self.management_audience,
            }
            if self.advertise_end_session:
                doc["end_session_endpoint"] = f"{ISSUER}/oidc/end-session"
            return doc

        @app.get("/.well-known/jwks.json")
        async def jwks() -> JSONResponse:
            return JSONResponse(
                {"keys": [self.public_jwk]},
                headers={"Cache-Control": "public, max-age=60"},
            )

        def _mint(
            *,
            sub: str,
            userinfo: dict[str, Any],
            nonce: str | None,
            sid: str,
            authority: dict[str, Any],
        ) -> dict[str, Any]:
            now = int(time.time())
            access_token = secrets.token_urlsafe(24)
            id_claims: dict[str, Any] = {
                "iss": ISSUER,
                "aud": [self.client_id],
                "sub": sub,
                "iat": now,
                "exp": now + 3600,
                "auth_time": now,
                "sid": sid,
                "at_hash": half_hash(access_token),
            }
            id_claims.update(authority)
            if nonce:
                id_claims["nonce"] = nonce
            self._userinfo_by_token[access_token] = {"sid": sid, **userinfo}
            return {
                "access_token": access_token,
                "id_token": self.sign(id_claims),
                "token_type": "Bearer",
                "expires_in": 3600,
            }

        @app.post("/oidc/token")
        async def token(request: Request) -> Any:
            form = await request.form()
            grant_type = form.get("grant_type")

            if grant_type == "refresh_token":
                # the whole grant. `refresh_calls`
                # records the presented value so a test can pin the
                # promise that a rejected refresh burns
                # the credential — the fake never re-accepts a value once it
                # is consumed, same as the real rotation.
                presented = str(form.get("refresh_token", ""))
                self.refresh_calls.append(presented)
                entry = self._refresh_tokens.pop(presented, None)
                if (
                    entry is None
                    or self.refresh_status_code != 200
                    or form.get("client_id") != self.client_id
                    or form.get("client_secret") != self.client_secret
                ):
                    return JSONResponse(
                        {"error": "invalid_grant"}, status_code=self.refresh_status_code or 400
                    )
                minted = _mint(
                    sub=entry["sub"],
                    userinfo=entry["userinfo"],
                    nonce=None,
                    sid=entry["sid"],
                    authority=entry["id_claims"],
                )
                new_refresh = secrets.token_urlsafe(24)
                self._refresh_tokens[new_refresh] = entry
                minted["refresh_token"] = new_refresh
                return minted

            code = str(form.get("code", ""))
            entry = self._codes.pop(code, None)
            if (
                entry is None
                or form.get("client_id") != self.client_id
                or form.get("client_secret") != self.client_secret
                or form.get("redirect_uri") != self.redirect_uri
            ):
                return JSONResponse({"error": "invalid_grant"}, status_code=400)

            sid = secrets.token_urlsafe(12)
            minted = _mint(
                sub=entry["sub"],
                userinfo=entry["userinfo"],
                nonce=entry["nonce"],
                sid=sid,
                authority=entry["id_claims"],
            )
            if entry["with_refresh"]:
                refresh_token = secrets.token_urlsafe(24)
                self._refresh_tokens[refresh_token] = {
                    "sub": entry["sub"],
                    "userinfo": entry["userinfo"],
                    "id_claims": entry["id_claims"],
                    "sid": sid,
                }
                minted["refresh_token"] = refresh_token
            return minted

        @app.get("/oidc/userinfo")
        async def userinfo(request: Request) -> Any:
            auth = request.headers.get("authorization", "")
            if not auth.startswith("Bearer "):
                return JSONResponse({"error": "invalid_token"}, status_code=401)
            entry = self._userinfo_by_token.get(auth[len("Bearer ") :])
            if entry is None:
                return JSONResponse({"error": "invalid_token"}, status_code=401)
            return entry

        @app.get("/api/v1/me/memberships")
        async def me_memberships(request: Request) -> Any:
            self.membership_authorizations.append(request.headers.get("authorization", ""))
            if self.memberships_status != 200:
                return JSONResponse({"detail": "x"}, status_code=self.memberships_status)
            start = int(request.query_params.get("cursor") or 0)
            end = start + self.memberships_page_size
            return {
                "items": self.memberships[start:end],
                "page": {
                    "next_cursor": str(end) if end < len(self.memberships) else None,
                    "total": None,
                },
            }

        @app.get("/oidc/end-session")
        async def end_session(request: Request) -> RedirectResponse:
            destination = request.query_params.get("post_logout_redirect_uri", "/")
            return RedirectResponse(destination, status_code=302)

        return app


__all__ = ["ALG", "ISSUER", "KID", "FakeIdp", "half_hash"]
