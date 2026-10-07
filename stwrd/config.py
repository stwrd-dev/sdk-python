"""`StwrdConfig` — the frozen configuration surface of the Python SDK.

`STWRD_COOKIE_SECRET` has a minimum of 32 characters in both SDKs, checked when
the configuration is built: it is the HMAC key of the session cookie, and a
deployment with a short key must refuse to start rather than start silently.
Every other rule below exists for the same reason: a misconfigured
integration must fail at construction time, not three requests later with a
confusing 500.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace

# The default scope of the SDKs. `org` is deliberately absent — it
# is not in the SDK default and cannot be, because raising the SDK version
# must never silently start asking for a scope a client might not have
# registered.
DEFAULT_SCOPE = "openid profile email offline_access"

DEFAULT_PREFIX = "/auth"
# `__Host-` cookies: the
# prefix forbids the `Domain` attribute, so a browser never sends one
# tenant's cookie to another tenant's host.
DEFAULT_SESSION_COOKIE = "__Host-stwrd_session"
DEFAULT_TX_COOKIE = "__Host-stwrd_tx"
DEFAULT_SESSION_TTL_S = 8 * 3600
DEFAULT_TRANSACTION_TTL_S = 600

# The HMAC key that seals the session cookie, the same minimum in both SDKs.
COOKIE_SECRET_MIN_LEN = 32

# `STWRD_*` names the SDK reads from the environment. Deliberately the same
# names as `@stwrd-auth/node`, so an app can switch languages without touching
# its `.env`.
REQUIRED_ENV = ("ISSUER", "CLIENT_ID", "CLIENT_SECRET", "BASE_URL", "COOKIE_SECRET")


class ConfigError(RuntimeError):
    """The SDK refuses to build a `StwrdConfig` from this input.

    A dedicated exception, not a bare `ValueError`: an app that wants to catch
    "my own config is wrong" separately from "the IdP rejected something"
    needs the two to be distinguishable types (`OidcError` is the other one).
    """


@dataclass(frozen=True)
class StwrdConfig:
    """Everything the BFF profile needs to talk to one IdP tenant.

    Frozen: a config that could mutate under a request in flight is exactly
    the kind of state bug `replace()` exists to avoid — building a derived
    config is an explicit new object, never an in-place edit.
    """

    issuer: str
    client_id: str
    client_secret: str
    base_url: str
    cookie_secret: str

    scope: str = DEFAULT_SCOPE
    webhook_secret: str = ""
    prefix: str = DEFAULT_PREFIX
    session_cookie: str = DEFAULT_SESSION_COOKIE
    tx_cookie: str = DEFAULT_TX_COOKIE
    session_ttl_s: int = DEFAULT_SESSION_TTL_S
    transaction_ttl_s: int = DEFAULT_TRANSACTION_TTL_S
    cookie_secure: bool = True
    post_login_redirect: str = "/"
    post_logout_redirect: str = "/"
    #: where the
    #: back-channel calls (discovery, token, JWKS, userinfo) actually
    #: CONNECT — `http://127.0.0.1:3005` — while the URL and the `Host`
    #: header keep the issuer's host, which is what the IdP routes the tenant
    #: by. `None` (the default) connects to the issuer itself.
    connect_to: str | None = None

    def __post_init__(self) -> None:
        missing = [
            name
            for name, value in (
                ("issuer", self.issuer),
                ("client_id", self.client_id),
                ("client_secret", self.client_secret),
                ("base_url", self.base_url),
                ("cookie_secret", self.cookie_secret),
            )
            if not value
        ]
        if missing:
            raise ConfigError("Missing required fields in StwrdConfig: " + ", ".join(missing))
        if len(self.cookie_secret) < COOKIE_SECRET_MIN_LEN:
            raise ConfigError(
                f"cookie_secret has {len(self.cookie_secret)} characters and needs "
                f"at least {COOKIE_SECRET_MIN_LEN}: it is the session cookie's HMAC "
                "key, and a short key must stop startup, not start "
                "silently."
            )
        if self.session_ttl_s <= 0 or self.transaction_ttl_s <= 0:
            raise ConfigError("session_ttl_s and transaction_ttl_s must be positive.")
        if not self.prefix.startswith("/"):
            raise ConfigError(f'prefix must start with "/": {self.prefix!r}')
        if self.connect_to is not None:
            from urllib.parse import urlsplit

            parts = urlsplit(self.connect_to)
            if parts.scheme not in {"http", "https"} or not parts.hostname:
                raise ConfigError(
                    f"connect_to must be an http(s) URL with a host: {self.connect_to!r}"
                )

    # --- derived values, never stored twice ----------------------------------

    @property
    def redirect_uri(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.prefix}/callback"

    @property
    def post_logout_redirect_uri(self) -> str:
        return f"{self.base_url.rstrip('/')}{self.post_logout_redirect}"

    @property
    def account_url(self) -> str:
        # The account page of the issuer: `{issuer}/me`.
        return f"{self.issuer.rstrip('/')}/me"

    def oidc(self) -> OidcParams:
        """The subset of the config the OIDC client needs.

        A separate value instead of handing the whole `StwrdConfig` to
        `OidcClient`: the client's constructor should not be able to reach
        the cookie secret or the webhook secret just because they happen to
        live on the same object.
        """
        return OidcParams(
            issuer=self.issuer,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
        )

    def replace(self, **changes: object) -> StwrdConfig:
        return replace(self, **changes)  # type: ignore[arg-type]

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        env_prefix: str = "STWRD_",
        **overrides: object,
    ) -> StwrdConfig:
        """Build from the environment, `STWRD_*` unless `env_prefix` says
        otherwise. `overrides` wins over the environment, which wins over the
        dataclass defaults — the same precedence `from_env` gives in
        `@stwrd-auth/node`, so porting an app between the two SDKs does not also
        require reordering how a value gets picked.
        """
        import os

        source: Mapping[str, str] = os.environ if environ is None else environ

        def read(name: str) -> str | None:
            return source.get(f"{env_prefix}{name}")

        # env name -> dataclass field. `REQUIRED_ENV` names the five that have
        # no default; the rest are optional and only override the dataclass
        # default when present.
        field_by_env = {
            "ISSUER": "issuer",
            "CLIENT_ID": "client_id",
            "CLIENT_SECRET": "client_secret",
            "BASE_URL": "base_url",
            "COOKIE_SECRET": "cookie_secret",
            "WEBHOOK_SECRET": "webhook_secret",
            "SCOPE": "scope",
            "PREFIX": "prefix",
            "POST_LOGIN_REDIRECT": "post_login_redirect",
            "POST_LOGOUT_REDIRECT": "post_logout_redirect",
            "CONNECT_TO": "connect_to",
        }
        values: dict[str, object] = {}
        for env_name, field_name in field_by_env.items():
            value = read(env_name)
            if value is not None:
                values[field_name] = value

        session_ttl = read("SESSION_TTL_S")
        if session_ttl is not None:
            values["session_ttl_s"] = int(session_ttl)

        cookie_secure = read("COOKIE_SECURE")
        if cookie_secure is not None:
            values["cookie_secure"] = cookie_secure.strip().lower() not in {
                "0",
                "false",
                "no",
                "",
            }

        values.update(overrides)

        missing = [name for name in REQUIRED_ENV if field_by_env[name] not in values]
        if missing:
            raise ConfigError(
                "Missing required environment variables: "
                + ", ".join(f"{env_prefix}{name}" for name in missing)
            )
        return cls(**values)  # type: ignore[arg-type]


@dataclass(frozen=True)
class OidcParams:
    """What `OidcClient` needs, and nothing it does not:
    `.oidc()` on `StwrdConfig`."""

    issuer: str
    client_id: str
    client_secret: str
    redirect_uri: str
    scope: str


__all__ = [
    "COOKIE_SECRET_MIN_LEN",
    "DEFAULT_PREFIX",
    "DEFAULT_SCOPE",
    "DEFAULT_SESSION_COOKIE",
    "DEFAULT_SESSION_TTL_S",
    "DEFAULT_TRANSACTION_TTL_S",
    "DEFAULT_TX_COOKIE",
    "REQUIRED_ENV",
    "ConfigError",
    "OidcParams",
    "StwrdConfig",
]
