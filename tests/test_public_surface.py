"""The SDK's public surface: every name of the surface really imports.

One test per property, parametrized over the whole surface table: a name added to
the surface adds a row here, not a new test function.
"""

from __future__ import annotations

import importlib

import pytest

# Only what this release ships:
# the shapes for organisations/MFA/refresh are frozen ahead
# of time so later phases are additive, but this release does not implement
# refresh, and there is nothing else in the `stwrd` module beyond this list.
CORE_SURFACE = (
    "Stwrd",
    "StwrdConfig",
    "StwrdUser",
    "StwrdSession",
    "SessionStore",
    "MemoryStore",
    "Tokens",
    "WebhookEvent",
    "ConfigError",
    "OidcError",
    "InvalidSignatureError",
    "DuplicateEventError",
    "verify_webhook",
    "verify_webhook_signature",
    "safe_equal",
)

# `stwrd.fastapi`:
FASTAPI_SURFACE = (
    "auth_router",
    "current_user",
    "optional_user",
    "require_auth",
    "api_mode",
    "require_role",
    "require_org",
    "require_permission",
    "protect",
    "safe_target",
)


@pytest.mark.parametrize("name", CORE_SURFACE)
def test_core_surface_name_importable(name: str) -> None:
    import stwrd

    assert hasattr(stwrd, name), f"stwrd.{name} no existe"
    assert name in stwrd.__all__, f"stwrd.{name} exists but is not in __all__"


@pytest.mark.parametrize("name", FASTAPI_SURFACE)
def test_fastapi_surface_name_importable(name: str) -> None:
    fastapi_extra = importlib.import_module("stwrd.fastapi")

    assert hasattr(fastapi_extra, name), f"stwrd.fastapi.{name} no existe"
    assert name in fastapi_extra.__all__, f"stwrd.fastapi.{name} is not in __all__"


def test_stwrd_config_shape() -> None:
    """`StwrdConfig(issuer, client_id, client_secret, base_url,
    cookie_secret, scope=…, webhook_secret="", prefix="/auth",
    session_cookie=…, tx_cookie=…, session_ttl_s=28800,
    transaction_ttl_s=600, cookie_secure=True, post_login_redirect="/",
    post_logout_redirect="/")` — every one of those names is a field, not an
    implementation detail a refactor is free to rename.
    """
    from stwrd import StwrdConfig

    fields = set(StwrdConfig.__dataclass_fields__)
    expected = {
        "issuer",
        "client_id",
        "client_secret",
        "base_url",
        "cookie_secret",
        "scope",
        "webhook_secret",
        "prefix",
        "session_cookie",
        "tx_cookie",
        "session_ttl_s",
        "transaction_ttl_s",
        "cookie_secure",
        "post_login_redirect",
        "post_logout_redirect",
        "connect_to",
    }
    assert expected <= fields

    for method in ("redirect_uri", "post_logout_redirect_uri", "account_url", "oidc", "replace"):
        assert hasattr(StwrdConfig, method), f"StwrdConfig.{method} no existe"
    assert hasattr(StwrdConfig, "from_env")


def test_stwrd_user_shape() -> None:
    """`StwrdUser(sub, email, email_verified, name, avatar, sid,
    org_id, org_display_name, org_roles, org_permissions, consents, claims)`."""
    from stwrd import StwrdUser

    fields = set(StwrdUser.__dataclass_fields__)
    assert fields == {
        "id",
        "email",
        "email_verified",
        "display_name",
        "avatar_url",
        "roles",
        "permissions",
    }
    assert not hasattr(StwrdUser, "has_role")


def test_stwrd_session_shape() -> None:
    """`StwrdSession(id, sid_idp, sub, claims, tokens, expires_at,
    access_expires_at) · .user`."""
    from stwrd import StwrdSession

    fields = set(StwrdSession.__dataclass_fields__)
    expected = {"id", "sid_idp", "sub", "claims", "tokens", "expires_at", "access_expires_at"}
    assert expected <= fields
    assert isinstance(StwrdSession.user, property)


@pytest.mark.asyncio
async def test_stwrd_instance_surface() -> None:
    """`.config · .oidc · .sessions · .seen_webhook_ids` plus
    `.close() · .seal(v) · .unseal(cookie) · .csrf(session_id)`,
    `.resolve_session(cookie)`, `.session_from_cookie(cookie)`,
    `.new_authorization_state()`, `.verify_webhook(body, headers)`."""
    from stwrd import Stwrd, StwrdConfig

    config = StwrdConfig(
        issuer="https://idp.example.com",
        client_id="c1",
        client_secret="secret",
        base_url="https://demo.test",
        cookie_secret="x" * 32,
    )
    instance = Stwrd(config)
    try:
        for attribute in ("config", "oidc", "sessions", "seen_webhook_ids"):
            assert hasattr(instance, attribute), f"Stwrd().{attribute} no existe"
        for method in (
            "close",
            "seal",
            "unseal",
            "csrf",
            "resolve_session",
            "session_from_cookie",
            "new_authorization_state",
            "verify_webhook",
        ):
            assert hasattr(instance, method), f"Stwrd().{method} no existe"
    finally:
        await instance.close()
