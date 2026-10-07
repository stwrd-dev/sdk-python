"""Private session state and normalized public session projections."""

from __future__ import annotations

import time
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Tokens:
    """What the token endpoint handed back for one session.

    `refresh_token` is `None`, never a missing attribute, when the session was
    created without the `offline_access` scope: the token endpoint simply does
    not return one. `resolve_session` reads that to decide whether it can
    renew.
    """

    access_token: str
    id_token: str
    token_type: str
    expires_at: float  # epoch seconds; computed from `expires_in` on receipt
    refresh_token: str | None = None


AUTHORITY_KEYS = frozenset(
    {"roles", "permissions", "org_id", "org_display_name", "org_roles", "org_permissions"}
)
PROFILE_KEYS = frozenset({"email", "email_verified", "name", "picture", "consents"})


def merge_userinfo(claims: dict[str, Any], userinfo: dict[str, Any]) -> dict[str, Any]:
    """Only verified-token claims authorize; userinfo supplies fresh profile."""
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject or userinfo.get("sub") != subject:
        from .oidc import OidcError

        raise OidcError("Userinfo subject does not match the session.")
    result = {k: v for k, v in claims.items() if k != "consents"}
    result.update({k: v for k, v in userinfo.items() if k in PROFILE_KEYS})
    return result


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _family(claims: dict[str, Any]) -> str | None:
    individual = {"roles", "permissions"}
    organization = AUTHORITY_KEYS - individual
    present = claims.keys() & AUTHORITY_KEYS
    if present == individual and all(_strings(claims[k]) for k in individual):
        return "individual"
    if (
        present == organization
        and all(
            isinstance(claims[k], str) and bool(claims[k]) for k in ("org_id", "org_display_name")
        )
        and all(_strings(claims[k]) for k in ("org_roles", "org_permissions"))
    ):
        return "organization"
    return None


@dataclass(frozen=True)
class StwrdUser:
    """Normalized public profile and individual capabilities."""

    id: str
    email: str | None = None
    email_verified: bool = False
    display_name: str | None = None
    avatar_url: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> StwrdUser:
        individual = _family(claims) == "individual"
        return cls(
            id=claims["sub"],
            email=_optional_string(claims.get("email")),
            email_verified=claims.get("email_verified") is True,
            display_name=_optional_string(claims.get("name")),
            avatar_url=_optional_string(claims.get("picture")),
            roles=list(claims["roles"]) if individual else [],
            permissions=list(claims["permissions"]) if individual else [],
        )


@dataclass(frozen=True)
class StwrdOrganization:
    id: str
    display_name: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StwrdSession:
    """The BFF's local session row.

    `id` is this store's own opaque key (what the sealed cookie carries);
    `sid_idp` is the IdP's `sid` claim, the key of back-channel logout, kept
    as its own field because back-channel logout matches on it and must not
    depend on parsing `claims` to find it.
    """

    id: str
    sid_idp: str | None
    sub: str
    claims: dict[str, Any]
    tokens: Tokens
    expires_at: float  # epoch seconds: the local, sliding session_ttl_s window
    access_expires_at: float  # epoch seconds: when tokens.access_token expires

    @property
    def user(self) -> StwrdUser:
        return StwrdUser.from_claims(self.claims)

    @property
    def organization(self) -> StwrdOrganization | None:
        if _family(self.claims) != "organization":
            return None
        return StwrdOrganization(
            id=self.claims["org_id"],
            display_name=self.claims["org_display_name"],
            roles=list(self.claims["org_roles"]),
            permissions=list(self.claims["org_permissions"]),
        )

    @property
    def consents(self) -> dict[str, str]:
        value = self.claims.get("consents")
        if not isinstance(value, dict):
            return {}
        return {
            k: v
            for k, v in value.items()
            if isinstance(k, str)
            and isinstance(v, str)
            and v in {"accepted", "declined", "pending"}
        }

    def has_role(self, role: str) -> bool:
        context = self.organization or self.user
        return role in context.roles

    def has_permission(self, permission: str) -> bool:
        context = self.organization or self.user
        return permission in context.permissions

    def is_expired(self, *, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) >= self.expires_at

    def access_token_expired(self, *, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) >= self.access_expires_at


RefreshPhase = Literal["acquired", "sent", "hydrating", "uncertain"]


@dataclass(frozen=True)
class RefreshClaim:
    """Answer to `SessionStore.claim_refresh`.

    `granted`: the caller owns the one refresh of this session and must pass
    `fence` to every later call. `phase` is `acquired` (nothing sent yet) or
    `hydrating` (an earlier owner already rotated and checkpointed the tokens;
    only userinfo is left — the refresh token must NOT be exchanged again).
    `busy`: another owner holds a live lease. `uncertain`: a refresh request
    may have been processed without its result being stored; the refresh token
    can never be used again and the session yields no authority. `gone`: no
    such session.
    """

    status: Literal["granted", "busy", "uncertain", "gone"]
    session: StwrdSession | None = None
    fence: int = 0
    phase: RefreshPhase = "acquired"
    fresh_id_token: bool = False


class SessionStore(Protocol):
    """Where sessions live. Every method is async: a real store does I/O.

    Refresh is coordinated through a durable lease with fencing so that, across
    processes, one refresh token is exchanged at most once: `claim_refresh`
    hands the lease to one owner; `mark_refresh_sent` is written BEFORE the
    exchange leaves; `checkpoint_refresh` stores the rotated tokens before any
    further network call; `complete_refresh` stores the final session.
    Each of the last three is a compare-and-set on `(session_id, fence)` and
    returns False when the lease was lost or the session deleted, so a
    deleted session is never resurrected. A lease whose owner died after
    `mark_refresh_sent` is `uncertain`: the exchange may have rotated the
    token, so it is never replayed.
    """

    async def get(self, session_id: str) -> StwrdSession | None: ...

    async def set(self, session: StwrdSession) -> None: ...

    async def delete(self, session_id: str) -> None: ...

    async def replace_session(self, old_id: str, session: StwrdSession) -> bool:
        """Atomically install `session` and retire `old_id`, only if `old_id`
        still exists. False (nothing written) when it was deleted meanwhile, so
        a logout between the start of an organization switch and its callback
        is never undone."""
        ...

    async def claim_refresh(self, session_id: str, owner: str, lease_s: float) -> RefreshClaim: ...

    async def mark_refresh_sent(self, session_id: str, fence: int) -> bool: ...

    async def checkpoint_refresh(
        self, session_id: str, fence: int, tokens: Tokens, *, fresh_id_token: bool
    ) -> bool:
        """Store the rotated `tokens`; access expiry stays as it was (still
        expired), authority claims are dropped (stale until userinfo is read
        again), phase becomes `hydrating`, the lease stays with the owner."""
        ...

    async def complete_refresh(self, session_id: str, fence: int, session: StwrdSession) -> bool:
        """Store the final session and clear the lease."""
        ...

    async def release_refresh(self, session_id: str, fence: int, *, sent: bool) -> None:
        """Give the lease up after a failure. `sent=False` (the request never
        left, or nothing was rotated) clears it; `sent=True` while still in
        the `sent` phase marks the session `uncertain`; in `hydrating` the
        checkpointed tokens are kept for a later userinfo-only retry. On a
        session that is already `uncertain` it does nothing: the owner that
        sent the request is gone and nothing it says now can reopen it."""
        ...


@dataclass
class _Lease:
    owner: str
    fence: int
    phase: RefreshPhase
    expires_at: float
    fresh_id_token: bool = False


class MemoryStore:
    """The default `SessionStore`: an in-process dict.

    Fine for a single-process demo or dev server; a deployment with more than
    one worker needs a shared store implementing the same lease contract.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, StwrdSession] = {}
        self._leases: dict[str, _Lease] = {}
        self._fence = 0

    async def get(self, session_id: str) -> StwrdSession | None:
        return self._sessions.get(session_id)

    async def set(self, session: StwrdSession) -> None:
        self._sessions[session.id] = session
        self._leases.pop(session.id, None)

    async def delete(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
        self._leases.pop(session_id, None)

    async def replace_session(self, old_id: str, session: StwrdSession) -> bool:
        if old_id not in self._sessions:
            return False
        await self.delete(old_id)
        await self.set(session)
        return True

    async def claim_refresh(self, session_id: str, owner: str, lease_s: float) -> RefreshClaim:
        session = self._sessions.get(session_id)
        if session is None:
            return RefreshClaim("gone")
        now = time.time()
        lease = self._leases.get(session_id)
        if lease is not None:
            if lease.phase == "uncertain":
                return RefreshClaim("uncertain")
            if lease.expires_at > now:
                return RefreshClaim("busy")
            if lease.phase == "sent":
                lease.phase = "uncertain"
                return RefreshClaim("uncertain")
        phase: RefreshPhase = lease.phase if lease is not None else "acquired"
        fresh = lease.fresh_id_token if lease is not None else False
        self._fence += 1
        self._leases[session_id] = _Lease(owner, self._fence, phase, now + lease_s, fresh)
        return RefreshClaim("granted", session, self._fence, phase, fresh)

    def _held(self, session_id: str, fence: int) -> _Lease | None:
        lease = self._leases.get(session_id)
        if lease is None or lease.fence != fence or session_id not in self._sessions:
            return None
        return lease

    async def mark_refresh_sent(self, session_id: str, fence: int) -> bool:
        lease = self._held(session_id, fence)
        if lease is None or lease.phase != "acquired":
            return False
        lease.phase = "sent"
        return True

    async def checkpoint_refresh(
        self, session_id: str, fence: int, tokens: Tokens, *, fresh_id_token: bool
    ) -> bool:
        lease = self._held(session_id, fence)
        if lease is None or lease.phase != "sent":
            return False
        current = self._sessions[session_id]
        self._sessions[session_id] = replace(
            current,
            tokens=tokens,
            claims={k: v for k, v in current.claims.items() if k not in AUTHORITY_KEYS},
        )
        lease.phase = "hydrating"
        lease.fresh_id_token = fresh_id_token
        return True

    async def complete_refresh(self, session_id: str, fence: int, session: StwrdSession) -> bool:
        lease = self._held(session_id, fence)
        if lease is None or lease.phase == "uncertain" or session.id != session_id:
            return False
        self._sessions[session_id] = session
        del self._leases[session_id]
        return True

    async def release_refresh(self, session_id: str, fence: int, *, sent: bool) -> None:
        lease = self._held(session_id, fence)
        # An `uncertain` session stays so: the owner that sent the request is
        # gone and nothing it says now can reopen the consumed refresh token.
        if lease is None or lease.phase == "uncertain":
            return
        if lease.phase == "hydrating":
            lease.expires_at = 0.0
        elif lease.phase == "sent" and sent:
            lease.phase = "uncertain"
        else:
            del self._leases[session_id]


__all__ = [
    "MemoryStore",
    "RefreshClaim",
    "RefreshPhase",
    "SessionStore",
    "StwrdSession",
    "StwrdOrganization",
    "StwrdUser",
    "Tokens",
]
