"""`StwrdConfig`: fail-closed construction. `STWRD_COOKIE_SECRET` has a
minimum of 32 characters, verified when the configuration is built.
"""

from __future__ import annotations

import pytest

from stwrd import ConfigError, StwrdConfig
from stwrd.config import COOKIE_SECRET_MIN_LEN, DEFAULT_SCOPE

VALID_KWARGS = {
    "issuer": "https://idp.example.com",
    "client_id": "demo",
    "client_secret": "s3cret",
    "base_url": "https://demo.test",
    "cookie_secret": "x" * 32,
}


def test_builds_with_the_required_fields() -> None:
    config = StwrdConfig(**VALID_KWARGS)
    assert config.scope == DEFAULT_SCOPE
    assert config.cookie_secure is True


@pytest.mark.parametrize(
    "missing", ["issuer", "client_id", "client_secret", "base_url", "cookie_secret"]
)
def test_refuses_a_missing_required_field(missing: str) -> None:
    kwargs = dict(VALID_KWARGS)
    kwargs[missing] = ""
    with pytest.raises(ConfigError):
        StwrdConfig(**kwargs)


def test_refuses_a_short_cookie_secret() -> None:
    kwargs = dict(VALID_KWARGS)
    kwargs["cookie_secret"] = "x" * (COOKIE_SECRET_MIN_LEN - 1)
    with pytest.raises(ConfigError):
        StwrdConfig(**kwargs)


def test_accepts_a_cookie_secret_at_the_minimum_length() -> None:
    kwargs = dict(VALID_KWARGS)
    kwargs["cookie_secret"] = "x" * COOKIE_SECRET_MIN_LEN
    StwrdConfig(**kwargs)  # does not raise


def test_derived_urls() -> None:
    config = StwrdConfig(**VALID_KWARGS)
    assert config.redirect_uri == "https://demo.test/auth/callback"
    assert config.post_logout_redirect_uri == "https://demo.test/"
    assert config.account_url == "https://idp.example.com/me"


def test_oidc_params_carry_no_secret_beyond_client_secret() -> None:
    config = StwrdConfig(**VALID_KWARGS, webhook_secret="whsec-x")
    params = config.oidc()
    assert params.client_id == "demo"
    assert params.redirect_uri == config.redirect_uri
    assert not hasattr(params, "webhook_secret")
    assert not hasattr(params, "cookie_secret")


def test_replace_builds_a_new_object() -> None:
    config = StwrdConfig(**VALID_KWARGS)
    other = config.replace(scope="openid")
    assert other.scope == "openid"
    assert config.scope == DEFAULT_SCOPE  # the original is untouched


def test_from_env_reads_stwrd_prefixed_variables() -> None:
    env = {
        "STWRD_ISSUER": "https://idp.example.com",
        "STWRD_CLIENT_ID": "demo",
        "STWRD_CLIENT_SECRET": "s3cret",
        "STWRD_BASE_URL": "https://demo.test",
        "STWRD_COOKIE_SECRET": "x" * 32,
        "STWRD_COOKIE_SECURE": "false",
    }
    config = StwrdConfig.from_env(env)
    assert config.issuer == "https://idp.example.com"
    assert config.cookie_secure is False


def test_from_env_fails_closed_on_missing_variables() -> None:
    with pytest.raises(ConfigError):
        StwrdConfig.from_env({})


def test_from_env_overrides_win_over_environment() -> None:
    env = dict(
        STWRD_ISSUER="https://idp.example.com",
        STWRD_CLIENT_ID="demo",
        STWRD_CLIENT_SECRET="s3cret",
        STWRD_BASE_URL="https://demo.test",
        STWRD_COOKIE_SECRET="x" * 32,
    )
    config = StwrdConfig.from_env(env, client_id="overridden")
    assert config.client_id == "overridden"


# --- `connect_to` ---


def test_connect_to_is_optional_and_read_from_the_environment() -> None:
    from stwrd import StwrdConfig

    environ = {
        "STWRD_ISSUER": "https://tenant.example.com",
        "STWRD_CLIENT_ID": "c",
        "STWRD_CLIENT_SECRET": "s",
        "STWRD_BASE_URL": "http://localhost:8001",
        "STWRD_COOKIE_SECRET": "x" * 32,
    }
    assert StwrdConfig.from_env(environ).connect_to is None
    assert (
        StwrdConfig.from_env({**environ, "STWRD_CONNECT_TO": "http://127.0.0.1:3005"}).connect_to
        == "http://127.0.0.1:3005"
    )


@pytest.mark.parametrize("bad", ["127.0.0.1:3005", "ftp://127.0.0.1", "http://"])
def test_connect_to_must_be_an_http_url_with_a_host(bad: str) -> None:
    from stwrd import ConfigError, StwrdConfig

    with pytest.raises(ConfigError):
        StwrdConfig(
            issuer="https://tenant.example.com",
            client_id="c",
            client_secret="s",
            base_url="http://localhost:8001",
            cookie_secret="x" * 32,
            connect_to=bad,
        )
