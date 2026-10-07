"""`stwrd.oidc.OidcClient`: unit tests over the pure/near-pure pieces, plus
the id_token/logout_token checks against the fake IdP's real signatures —
those need a real JWKS round trip to mean anything, so they are the one place
this file talks HTTP (over `httpx.AsyncClient` + `ASGITransport`, no socket —
see `oidc.py`'s module docstring for why the client is async).
"""

from __future__ import annotations

import time

import pytest

from stwrd.oidc import (
    JWKS_DEFAULT_TTL_S,
    JWKS_TTL_CEILING_S,
    JWKS_TTL_FLOOR_S,
    LOGOUT_EVENT_URI,
    OidcClient,
    OidcError,
    _clamp_ttl,
    challenge_s256,
    generate_verifier,
    half_hash,
)

from .fake_idp import ISSUER, FakeIdp


def _client(fake_idp: FakeIdp, http_client) -> OidcClient:
    from stwrd.config import OidcParams

    return OidcClient(
        http_client,
        OidcParams(
            issuer=ISSUER,
            client_id=fake_idp.client_id,
            client_secret=fake_idp.client_secret,
            redirect_uri=fake_idp.redirect_uri,
            scope="openid profile email offline_access",
        ),
    )


# --- pure helpers ------------------------------------------------------------


def test_pkce_challenge_is_recomputable_from_the_verifier() -> None:
    verifier = generate_verifier()
    assert 43 <= len(verifier) <= 128  # RFC 7636 §4.1
    assert challenge_s256(verifier) == challenge_s256(verifier)


def test_pkce_verifiers_are_not_reused() -> None:
    assert generate_verifier() != generate_verifier()


@pytest.mark.parametrize(
    ("cache_control", "expected"),
    [
        (None, JWKS_DEFAULT_TTL_S),
        ("garbage", JWKS_DEFAULT_TTL_S),
        ("public, max-age=0", JWKS_TTL_FLOOR_S),  # clamped up
        ("public, max-age=1", JWKS_TTL_FLOOR_S),
        ("public, max-age=60", 60),
        ("public, max-age=999999", JWKS_TTL_CEILING_S),  # clamped down
    ],
)
def test_jwks_ttl_clamped_to_the_documented_bounds(cache_control, expected) -> None:
    assert _clamp_ttl(cache_control) == expected


def test_half_hash_differs_by_algorithm() -> None:
    # sha256 half for RS256, sha512 half for EdDSA —
    # different digest sizes, so the two must not collide by construction.
    token = "some-access-token"
    assert half_hash(token, "RS256") != half_hash(token, "EdDSA")


# --- discovery + JWKS, against the fake IdP ----------------------------------


@pytest.mark.asyncio
async def test_discover_returns_the_documented_endpoints(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    discovery = await client.discover()
    assert discovery.issuer == ISSUER
    assert discovery.token_endpoint == f"{ISSUER}/oidc/token"
    assert discovery.jwks_uri == f"{ISSUER}/.well-known/jwks.json"
    assert discovery.end_session_endpoint is None  # fake_idp default: not advertised


@pytest.mark.asyncio
async def test_unknown_kid_triggers_an_immediate_refetch(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    await client._fetch_jwks()
    calls_before = client._jwks.fetched_at
    # A `kid` the cached JWKS does not have forces `_keyset_for` to refetch
    # rather than fail closed and reject a legitimately-rotated key.
    from stwrd.oidc import _keyset_has_kid

    keyset = await client._keyset_for("some-kid-not-in-the-cache")
    assert not _keyset_has_kid(keyset, "some-kid-not-in-the-cache")  # fake IdP never minted it
    assert client._jwks.fetched_at >= calls_before


# --- id_token validation ------------------------------------------------------


async def _issue_and_exchange(
    fake_idp: FakeIdp, client: OidcClient, *, nonce: str = "n1", **userinfo
):
    code = fake_idp.issue_code(sub="usr_1", nonce=nonce, userinfo=userinfo)
    return await client.exchange_code(code=code, code_verifier="whatever-verifier-the-fake-ignores")


@pytest.mark.asyncio
async def test_validate_id_token_accepts_a_well_formed_token(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    token_response = await _issue_and_exchange(fake_idp, client, email="a@b.test")
    claims = await client.validate_id_token(
        token_response["id_token"], nonce="n1", access_token=token_response["access_token"]
    )
    assert claims["sub"] == "usr_1"
    assert claims["iss"] == ISSUER
    assert claims["aud"] == [fake_idp.client_id]


@pytest.mark.asyncio
async def test_validate_id_token_rejects_a_mismatched_nonce(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    token_response = await _issue_and_exchange(fake_idp, client, nonce="n1")
    with pytest.raises(OidcError):
        await client.validate_id_token(
            token_response["id_token"],
            nonce="not-the-same-nonce",
            access_token=token_response["access_token"],
        )


@pytest.mark.asyncio
async def test_validate_id_token_rejects_a_tampered_at_hash(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    token_response = await _issue_and_exchange(fake_idp, client)
    with pytest.raises(OidcError):
        await client.validate_id_token(
            token_response["id_token"], nonce="n1", access_token="a-different-access-token"
        )


@pytest.mark.asyncio
async def test_validate_id_token_rejects_wrong_audience(fake_idp: FakeIdp, idp_http_client) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    now = int(time.time())
    token = fake_idp.sign(
        {
            "iss": ISSUER,
            "aud": ["someone-elses-client"],
            "sub": "usr_1",
            "iat": now,
            "exp": now + 3600,
            "sid": "s1",
            "at_hash": half_hash("at", "RS256"),
        }
    )
    with pytest.raises(OidcError):
        await client.validate_id_token(token, nonce="n1", access_token="at")


@pytest.mark.asyncio
async def test_validate_id_token_rejects_an_expired_token(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    now = int(time.time())
    token = fake_idp.sign(
        {
            "iss": ISSUER,
            "aud": [fake_idp.client_id],
            "sub": "usr_1",
            "iat": now - 7200,
            "exp": now - 3600,
            "sid": "s1",
            "at_hash": half_hash("at", "RS256"),
        }
    )
    with pytest.raises(OidcError):
        await client.validate_id_token(token, nonce="n1", access_token="at")


# --- logout_token validation --------------------------------------------------


def _valid_logout_claims(fake_idp: FakeIdp, **overrides) -> dict:
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": [fake_idp.client_id],
        "iat": now,
        "exp": now + 120,
        "jti": "logout-1",
        "sid": "s1",
        "events": {LOGOUT_EVENT_URI: {}},
    }
    claims.update(overrides)
    return claims


@pytest.mark.asyncio
async def test_validate_logout_token_accepts_a_well_formed_token(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    token = fake_idp.sign(_valid_logout_claims(fake_idp))
    claims = await client.validate_logout_token(token)
    assert claims["sid"] == "s1"
    assert claims["jti"] == "logout-1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"events": {"some.other.event": {}}},  # missing the frozen event URI
        {"nonce": "must-not-be-here"},  # RFC forbids `nonce` on a logout_token
        {"jti": None},  # no replay id, nothing to reject a replay with
        {"aud": ["someone-elses-client"]},
    ],
)
async def test_validate_logout_token_rejects_malformed_claims(
    fake_idp: FakeIdp, idp_http_client, overrides: dict
) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    claims = _valid_logout_claims(fake_idp, **overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    token = fake_idp.sign(claims)
    with pytest.raises(OidcError):
        await client.validate_logout_token(token)


@pytest.mark.asyncio
async def test_validate_logout_token_rejects_missing_sid_and_sub(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    claims = _valid_logout_claims(fake_idp)
    del claims["sid"]
    token = fake_idp.sign(claims)
    with pytest.raises(OidcError):
        await client.validate_logout_token(token)


# --- signature verification never trusts the token's own `alg` ---------------
#
# `_verify_jws` used to read `alg` straight out of the unverified header and
# hand it to `joserfc_jwt.decode(..., algorithms=[alg])` — a token signer
# choosing its own algorithm, the JWS `alg: none` attack. `SUPPORTED_ALGS` is
# now the only list ever passed to `decode`, and the header's `alg` is
# checked against it before the key is even resolved.


@pytest.mark.asyncio
async def test_validate_logout_token_rejects_alg_none(fake_idp: FakeIdp, idp_http_client) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    token = fake_idp.forge_unsigned(_valid_logout_claims(fake_idp), alg="none")
    with pytest.raises(OidcError):
        await client.validate_logout_token(token)


@pytest.mark.asyncio
async def test_validate_id_token_rejects_alg_none(fake_idp: FakeIdp, idp_http_client) -> None:
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    now = int(time.time())
    token = fake_idp.forge_unsigned(
        {
            "iss": ISSUER,
            "aud": [fake_idp.client_id],
            "sub": "usr_1",
            "iat": now,
            "exp": now + 3600,
            "nonce": "n1",
            "sid": "s1",
            "at_hash": half_hash("at", "RS256"),
        },
        alg="none",
    )
    with pytest.raises(OidcError):
        await client.validate_id_token(token, nonce="n1", access_token="at")


@pytest.mark.asyncio
async def test_validate_logout_token_rejects_algorithm_confusion(
    fake_idp: FakeIdp, idp_http_client
) -> None:
    # `alg` in `SUPPORTED_ALGS` (`EdDSA`) but the real key behind this `kid`
    # is RSA — a signer that got the `alg` wrong on purpose does not get to
    # pick which algorithm verifies its key.
    client = _client(fake_idp, idp_http_client)
    await client.discover()
    token = fake_idp.forge_unsigned(_valid_logout_claims(fake_idp), alg="EdDSA")
    with pytest.raises(OidcError):
        await client.validate_logout_token(token)
