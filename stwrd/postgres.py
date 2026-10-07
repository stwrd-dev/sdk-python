"""A shared `SessionStore` on PostgreSQL, for deployments with several workers.

Tokens are encrypted as JWE (`dir` + `A256GCM`, via joserfc) with a keyring that
is independent of the cookie secret. The authenticated payload also carries the
namespace (tenant/client), the session id and the purpose, so a row copied to
another namespace or id is rejected on read. Lease phase, fence and expiry stay
in plain columns: coordination needs them in SQL, and they hold no secret.
Lease expiry is judged by the database clock, never by a worker's.

The schema is explicit: run `SCHEMA_SQL` from your own migration. The store
never creates tables.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from collections.abc import Mapping
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Any, Protocol

from joserfc import jwe
from joserfc.jwk import OctKey

from .sessions import AUTHORITY_KEYS, RefreshClaim, RefreshPhase, StwrdSession, Tokens

_log = logging.getLogger("stwrd.postgres")

SCHEMA_SQL = """
CREATE SEQUENCE stwrd_sdk_fence_seq;
CREATE TABLE stwrd_sdk_sessions (
    namespace text NOT NULL,
    session_id text NOT NULL,
    payload text NOT NULL,
    expires_at double precision NOT NULL,
    fence bigint NOT NULL DEFAULT nextval('stwrd_sdk_fence_seq'),
    lease_owner text,
    lease_phase text CHECK (lease_phase IN ('acquired', 'sent', 'hydrating', 'uncertain')),
    lease_expires_at timestamptz,
    fresh_id_token boolean NOT NULL DEFAULT false,
    PRIMARY KEY (namespace, session_id),
    CHECK ((lease_phase IS NULL) = (lease_owner IS NULL))
);
CREATE INDEX stwrd_sdk_sessions_expiry ON stwrd_sdk_sessions (namespace, expires_at);
"""

TABLE = "stwrd_sdk_sessions"


class ConnectionSource(Protocol):
    """`psycopg_pool.AsyncConnectionPool` satisfies this; so does any object
    whose `connection()` yields a `psycopg.AsyncConnection`."""

    def connection(self) -> AbstractAsyncContextManager[Any]: ...


@dataclass(frozen=True)
class Keyring:
    """Named 32-byte keys. `current` encrypts; every key decrypts, so a key can
    be rotated by adding the new one, switching `current`, and dropping the old
    one once no row uses it."""

    keys: Mapping[str, bytes]
    current: str

    def __post_init__(self) -> None:
        if self.current not in self.keys:
            raise ValueError("The current key id is not in the keyring.")
        if any(len(key) != 32 for key in self.keys.values()):
            raise ValueError("Every keyring key must be exactly 32 bytes.")

    def encrypt(self, plaintext: bytes) -> str:
        key = OctKey.import_key(self.keys[self.current])
        return jwe.encrypt_compact(
            {"alg": "dir", "enc": "A256GCM", "kid": self.current}, plaintext, key
        )

    def decrypt(self, token: str) -> bytes:
        # The header only selects the key; it is authenticated as AAD on decrypt.
        encoded = token.split(".", 1)[0]
        header = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        kid = header.get("kid") if isinstance(header, dict) else None
        if not isinstance(kid, str) or kid not in self.keys:
            raise ValueError("Unknown key id.")
        result = jwe.decrypt_compact(
            token, OctKey.import_key(self.keys[kid]), algorithms=["dir", "A256GCM"]
        )
        plaintext = result.plaintext
        if plaintext is None:
            raise ValueError("Empty payload.")
        return plaintext


def _dump(session: StwrdSession) -> dict[str, Any]:
    return {
        "id": session.id,
        "sid_idp": session.sid_idp,
        "sub": session.sub,
        "claims": session.claims,
        "tokens": {
            "access_token": session.tokens.access_token,
            "id_token": session.tokens.id_token,
            "token_type": session.tokens.token_type,
            "expires_at": session.tokens.expires_at,
            "refresh_token": session.tokens.refresh_token,
        },
        "expires_at": session.expires_at,
        "access_expires_at": session.access_expires_at,
    }


def _load(data: dict[str, Any]) -> StwrdSession:
    return StwrdSession(
        id=data["id"],
        sid_idp=data["sid_idp"],
        sub=data["sub"],
        claims=data["claims"],
        tokens=Tokens(**data["tokens"]),
        expires_at=data["expires_at"],
        access_expires_at=data["access_expires_at"],
    )


class PostgresSessionStore:
    def __init__(self, source: ConnectionSource, *, namespace: str, keyring: Keyring) -> None:
        if not namespace:
            raise ValueError("A namespace (tenant/client) is required.")
        self._source = source
        self._namespace = namespace
        self._keyring = keyring

    # -- sealing ---------------------------------------------------------

    def _seal(self, session: StwrdSession) -> str:
        body: dict[str, Any] = {
            "ns": self._namespace,
            "sid": session.id,
            "purpose": "session",
            "session": _dump(session),
        }
        return self._keyring.encrypt(json.dumps(body, separators=(",", ":")).encode())

    def _open(self, session_id: str, payload: str) -> StwrdSession | None:
        try:
            body = json.loads(self._keyring.decrypt(payload))
            if (
                body.get("ns") != self._namespace
                or body.get("sid") != session_id
                or body.get("purpose") != "session"
            ):
                raise ValueError("Row context does not match its location.")
            return _load(body["session"])
        except Exception:
            # Fail closed: a tampered, relocated or unreadable row is no session.
            _log.warning("Unreadable session row", exc_info=True)
            return None

    # -- SessionStore ----------------------------------------------------

    async def get(self, session_id: str) -> StwrdSession | None:
        async with self._source.connection() as conn:
            cursor = await conn.execute(
                f"SELECT payload FROM {TABLE} WHERE namespace = %s AND session_id = %s",
                (self._namespace, session_id),
            )
            row = await cursor.fetchone()
        return self._open(session_id, row[0]) if row else None

    async def set(self, session: StwrdSession) -> None:
        async with self._source.connection() as conn:
            await conn.execute(
                f"""INSERT INTO {TABLE} (namespace, session_id, payload, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (namespace, session_id) DO UPDATE SET
                      payload = EXCLUDED.payload, expires_at = EXCLUDED.expires_at,
                      fence = nextval('stwrd_sdk_fence_seq'), lease_owner = NULL,
                      lease_phase = NULL,
                      lease_expires_at = NULL, fresh_id_token = false""",
                (self._namespace, session.id, self._seal(session), session.expires_at),
            )

    async def delete(self, session_id: str) -> None:
        async with self._source.connection() as conn:
            await conn.execute(
                f"DELETE FROM {TABLE} WHERE namespace = %s AND session_id = %s",
                (self._namespace, session_id),
            )

    async def purge_expired(self) -> int:
        """Delete this namespace's sessions past their local expiry (and with
        them their stored refresh tokens). Run it periodically."""
        async with self._source.connection() as conn:
            cursor = await conn.execute(
                f"DELETE FROM {TABLE} WHERE namespace = %s AND expires_at < %s",
                (self._namespace, time.time()),
            )
            return cursor.rowcount

    async def replace_session(self, old_id: str, session: StwrdSession) -> bool:
        async with self._source.connection() as conn, conn.transaction():
            cursor = await conn.execute(
                f"DELETE FROM {TABLE} WHERE namespace = %s AND session_id = %s RETURNING 1",
                (self._namespace, old_id),
            )
            if await cursor.fetchone() is None:
                return False
            await conn.execute(
                f"""INSERT INTO {TABLE} (namespace, session_id, payload, expires_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (namespace, session_id) DO UPDATE SET
                      payload = EXCLUDED.payload, expires_at = EXCLUDED.expires_at,
                      fence = nextval('stwrd_sdk_fence_seq'), lease_owner = NULL,
                      lease_phase = NULL,
                      lease_expires_at = NULL, fresh_id_token = false""",
                (self._namespace, session.id, self._seal(session), session.expires_at),
            )
            return True

    async def claim_refresh(self, session_id: str, owner: str, lease_s: float) -> RefreshClaim:
        async with self._source.connection() as conn, conn.transaction():
            cursor = await conn.execute(
                f"""SELECT payload, fence, lease_phase, fresh_id_token,
                           coalesce(lease_expires_at <= clock_timestamp(), false)
                    FROM {TABLE} WHERE namespace = %s AND session_id = %s FOR UPDATE""",
                (self._namespace, session_id),
            )
            row = await cursor.fetchone()
            if row is None:
                return RefreshClaim("gone")
            payload, fence, phase, fresh, expired = row
            session = self._open(session_id, payload)
            if session is None:
                return RefreshClaim("gone")
            if phase == "uncertain":
                return RefreshClaim("uncertain")
            if phase is not None and not expired:
                return RefreshClaim("busy")
            if phase == "sent":
                await conn.execute(
                    f"UPDATE {TABLE} SET lease_phase = 'uncertain' "
                    "WHERE namespace = %s AND session_id = %s",
                    (self._namespace, session_id),
                )
                return RefreshClaim("uncertain")
            granted: RefreshPhase = "hydrating" if phase == "hydrating" else "acquired"
            cursor = await conn.execute(
                f"""UPDATE {TABLE} SET fence = nextval('stwrd_sdk_fence_seq'),
                      lease_owner = %s, lease_phase = %s,
                      lease_expires_at = clock_timestamp() + make_interval(secs => %s)
                    WHERE namespace = %s AND session_id = %s RETURNING fence""",
                (owner, granted, lease_s, self._namespace, session_id),
            )
            returned = await cursor.fetchone()
            assert returned is not None
            new_fence = returned[0]
            return RefreshClaim("granted", session, new_fence, granted, bool(fresh))

    async def mark_refresh_sent(self, session_id: str, fence: int) -> bool:
        async with self._source.connection() as conn:
            cursor = await conn.execute(
                f"""UPDATE {TABLE} SET lease_phase = 'sent'
                    WHERE namespace = %s AND session_id = %s AND fence = %s
                      AND lease_phase = 'acquired' RETURNING 1""",
                (self._namespace, session_id, fence),
            )
            return await cursor.fetchone() is not None

    async def checkpoint_refresh(
        self, session_id: str, fence: int, tokens: Tokens, *, fresh_id_token: bool
    ) -> bool:
        async with self._source.connection() as conn, conn.transaction():
            cursor = await conn.execute(
                f"""SELECT payload FROM {TABLE}
                    WHERE namespace = %s AND session_id = %s AND fence = %s
                      AND lease_phase = 'sent' FOR UPDATE""",
                (self._namespace, session_id, fence),
            )
            row = await cursor.fetchone()
            current = self._open(session_id, row[0]) if row else None
            if current is None:
                return False
            stripped = StwrdSession(
                id=current.id,
                sid_idp=current.sid_idp,
                sub=current.sub,
                claims={k: v for k, v in current.claims.items() if k not in AUTHORITY_KEYS},
                tokens=tokens,
                expires_at=current.expires_at,
                access_expires_at=current.access_expires_at,
            )
            await conn.execute(
                f"""UPDATE {TABLE} SET payload = %s, lease_phase = 'hydrating',
                      fresh_id_token = %s WHERE namespace = %s AND session_id = %s""",
                (self._seal(stripped), fresh_id_token, self._namespace, session_id),
            )
            return True

    async def complete_refresh(self, session_id: str, fence: int, session: StwrdSession) -> bool:
        if session.id != session_id:
            return False
        async with self._source.connection() as conn:
            cursor = await conn.execute(
                f"""UPDATE {TABLE} SET payload = %s, expires_at = %s, lease_owner = NULL,
                      lease_phase = NULL, lease_expires_at = NULL, fresh_id_token = false
                    WHERE namespace = %s AND session_id = %s AND fence = %s
                      AND lease_phase IS NOT NULL AND lease_phase <> 'uncertain' RETURNING 1""",
                (self._seal(session), session.expires_at, self._namespace, session_id, fence),
            )
            return await cursor.fetchone() is not None

    async def release_refresh(self, session_id: str, fence: int, *, sent: bool) -> None:
        async with self._source.connection() as conn:
            await conn.execute(
                f"""UPDATE {TABLE} SET
                      lease_phase = CASE
                        WHEN lease_phase = 'sent' AND %s THEN 'uncertain'
                        WHEN lease_phase = 'hydrating' THEN 'hydrating'
                        ELSE NULL END,
                      lease_owner = CASE
                        WHEN lease_phase = 'hydrating'
                          OR (lease_phase = 'sent' AND %s) THEN lease_owner
                        ELSE NULL END,
                      lease_expires_at = CASE
                        WHEN lease_phase = 'hydrating' THEN clock_timestamp()
                        WHEN lease_phase = 'sent' AND %s THEN lease_expires_at
                        ELSE NULL END
                    WHERE namespace = %s AND session_id = %s AND fence = %s
                      AND lease_phase IS NOT NULL AND lease_phase <> 'uncertain'""",
                (sent, sent, sent, self._namespace, session_id, fence),
            )


__all__ = ["SCHEMA_SQL", "ConnectionSource", "Keyring", "PostgresSessionStore"]
