# Changelog

All notable changes to this package are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Before 1.0, minor releases may contain breaking changes.

## [0.1.0] - Unreleased

Initial release.

### Added

- `Stwrd` client and `Stwrd.from_env()` / `StwrdConfig.from_env()` configuration
  loaders that fail at startup on missing or invalid settings.
- FastAPI integration (`stwrd.fastapi`, installed with the `fastapi` extra):
  `auth_router()` mounting `/auth/sign-in`, `/auth/callback`, `/auth/sign-out`,
  `/auth/session`, `/auth/organizations`, `/auth/organization`,
  `/auth/back-channel` and `/auth/webhook`.
- FastAPI dependencies `optional_user`, `current_user`, `require_auth`,
  `require_role`, `require_org`, `require_permission` and `api_mode`, and
  `protect()` for fail-closed protection of an entire app by path.
- Authorization code flow with PKCE, state and nonce; ID token validation
  (signature, issuer, audience, expiry, nonce and `at_hash`) with JWKS caching.
- Server-side sessions behind a cookie that carries only an opaque, signed
  session id, with CSRF protection for sign-out and organization switching.
- Automatic token refresh that exchanges each refresh token at most once across
  workers, and treats an unreachable server as unavailable instead of signing
  users out.
- Session stores: in-memory `MemoryStore` and, with the `postgres` extra,
  `PostgresSessionStore` with encrypted token storage and key rotation.
- Capabilities (roles and permissions) taken only from verified ID tokens, for
  individual and organization contexts, and organization selection through the
  `org` scope.
- Back-channel logout and Standard Webhooks verification (`verify_webhook`,
  `verify_webhook_signature`, `WebhookEvent`) with replay-window enforcement and
  de-duplication.
- Typed Management API client (`create_management`) for server-side use, with
  ETags, idempotency keys, step-up tokens, file uploads and cursor iteration.
- `connect_to` and `connect_to_hook` for developing against a local server
  without DNS or `/etc/hosts` changes.
- `py.typed` marker; support for Python 3.12, 3.13 and 3.14.
