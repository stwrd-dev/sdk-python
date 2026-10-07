"""Standard Webhooks verification. The scheme is Standard Webhooks, the same
one Svix, Clerk and Resend speak.

Token signing and protocol verbs are never hand-written in this package, but
HMAC-SHA256 over `"{id}.{timestamp}.{body}"` *is* the protocol here (the
scheme defines the exact byte layout), so it is implemented directly against
`hmac`/`hashlib`, the same primitives the IdP itself uses to sign, rather than
pulled in through a third dependency for one function.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

# Replay window: 300 s.
DEFAULT_TOLERANCE_S = 300

# Receivers deduplicate over a 30 h window, but that window is a convenience
# of the process, not a guarantee. `Stwrd.seen_webhook_ids` uses this as its
# pruning window.
DEDUP_WINDOW_S = 30 * 3600

_HEADER_ID = "webhook-id"
_HEADER_TIMESTAMP = "webhook-timestamp"
_HEADER_SIGNATURE = "webhook-signature"

# A timestamp is accepted if it matches `^-?\\d+$` (ASCII digits, optionally
# surrounded by whitespace) and nothing else. `re.ASCII` is not decoration
# here: Python's `\d` matches every Unicode decimal digit by default (e.g.
# fullwidth `１７...`), which is exactly what must be rejected.
_TIMESTAMP_RE = re.compile(r"^\s*-?\d+\s*$", re.ASCII)

_SIGNATURE_PREFIX = "v1,"


class InvalidSignatureError(RuntimeError):
    """The delivery is rejected: missing/malformed headers, a timestamp
    outside the replay window, or no candidate signature that matches. A bad
    header is rejected cleanly, like any other bad signature, never as a 500
    — this is the one exception every rejection raises, deliberately without
    saying which check failed in the type."""


class DuplicateEventError(RuntimeError):
    """Raised only when a `seen` collection is passed and the event `id` was
    already delivered. A receiver has to be idempotent by `id` — this is what
    lets a caller treat it as `200 {"status":"duplicate"}` instead of
    reprocessing."""

    def __init__(self, event_id: str) -> None:
        super().__init__(f"Event {event_id} was already processed.")
        self.event_id = event_id


@dataclass(frozen=True)
class WebhookEvent:
    """Strict public v1 envelope; data retains the producer's wire fields."""

    id: str
    type: str
    api_version: str
    created_at: str
    data: dict[str, Any]


def safe_equal(a: str, b: str) -> bool:
    """Constant-time comparison, for anyone signing their own payloads
    against a stwrd secret; it is public surface for that purpose, on top of
    what `verify_webhook` already does internally."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _get_header(headers: Mapping[str, str], name: str) -> str | None:
    # Case-insensitive lookup without assuming the mapping itself is
    # case-insensitive (a plain `dict` from `request.headers` sometimes is,
    # sometimes is not, depending on the framework it came from).
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


def _candidate_signatures(header_value: str) -> list[str]:
    candidates = []
    for token in header_value.split():
        if token.startswith(_SIGNATURE_PREFIX):
            candidates.append(token[len(_SIGNATURE_PREFIX) :])
    return candidates


def verify_webhook_signature(
    body: bytes,
    headers: Mapping[str, str],
    secret: str,
    tolerance_s: int = DEFAULT_TOLERANCE_S,
) -> str:
    """Verify raw signed bytes without parsing or adapting any event envelope."""
    event_id = _get_header(headers, _HEADER_ID)
    timestamp_raw = _get_header(headers, _HEADER_TIMESTAMP)
    signature_header = _get_header(headers, _HEADER_SIGNATURE)
    if not event_id or not timestamp_raw or not signature_header:
        raise InvalidSignatureError("Missing webhook-id/timestamp/signature headers.")

    if not _TIMESTAMP_RE.match(timestamp_raw):
        raise InvalidSignatureError("webhook-timestamp is not a valid ASCII integer.")
    timestamp = int(timestamp_raw)
    if abs(time.time() - timestamp) > tolerance_s:
        raise InvalidSignatureError("The delivery is outside the replay window.")

    # The timestamp enters the HMAC as the exact header string, not as the
    # parsed integer — `timestamp_raw`, not `str(timestamp)`.
    signed_content = f"{event_id}.{timestamp_raw}.".encode() + body
    expected = base64.b64encode(
        hmac.new(secret.encode("utf-8"), signed_content, hashlib.sha256).digest()
    ).decode("ascii")

    candidates = _candidate_signatures(signature_header)
    matched = False
    for candidate in candidates:
        # Never short-circuits on the first match, and a candidate with
        # non-ASCII bytes fails the comparison cleanly instead of raising: it
        # is a 400 `invalid_signature` like any other bad signature, not a
        # 500.
        try:
            if hmac.compare_digest(candidate.encode("ascii"), expected.encode("ascii")):
                matched = True
        except UnicodeEncodeError:
            continue
    if not matched:
        raise InvalidSignatureError("No signature matches.")

    return event_id


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I | re.ASCII
)
_UTC_DATE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$", re.ASCII
)


def _same_uuid(value: Any, header: str) -> bool:
    if (
        not isinstance(value, str)
        or not _UUID_RE.fullmatch(value)
        or not _UUID_RE.fullmatch(header)
    ):
        return False
    return value == header


def _utc_instant(value: Any) -> bool:
    if not isinstance(value, str) or not _UTC_DATE_RE.fullmatch(value):
        return False
    try:
        instant = datetime.fromisoformat(value)
    except ValueError:
        return False
    return instant.utcoffset() == timedelta(0)


def verify_webhook(
    body: bytes,
    headers: Mapping[str, str],
    secret: str,
    tolerance_s: int = DEFAULT_TOLERANCE_S,
    *,
    seen: Any = None,
) -> WebhookEvent:
    event_id = verify_webhook_signature(body, headers, secret, tolerance_s=tolerance_s)
    import json

    try:
        doc = json.loads(body)
    except ValueError as exc:
        raise InvalidSignatureError("The body is not valid JSON.") from exc

    if (
        not isinstance(doc, dict)
        or set(doc) != {"id", "type", "created_at", "api_version", "data"}
        or not _same_uuid(doc.get("id"), event_id)
        or not isinstance(doc.get("type"), str)
        or not doc["type"]
        or doc.get("api_version") != "v1"
        or not _utc_instant(doc.get("created_at"))
        or not isinstance(doc.get("data"), dict)
    ):
        raise InvalidSignatureError("The body is not a v1 webhook event.")

    if seen is not None:
        if event_id in seen:
            raise DuplicateEventError(event_id)
        seen.add(event_id)

    return WebhookEvent(
        id=doc["id"],
        type=doc["type"],
        api_version=doc["api_version"],
        created_at=doc["created_at"],
        data=doc.get("data", {}),
    )


class SeenWebhookIds:
    """`Stwrd.seen_webhook_ids`: an in-process, self-pruning dedup set.

    The window is a convenience of the process (in memory, lost on restart),
    not a guarantee — so this is deliberately not persisted anywhere; a
    receiver's real idempotence has to come from its own storage, keyed by
    `id`.
    """

    def __init__(self, window_s: int = DEDUP_WINDOW_S) -> None:
        self._window_s = window_s
        self._seen: dict[str, float] = {}

    def __contains__(self, event_id: str) -> bool:
        self._prune()
        return event_id in self._seen

    def add(self, event_id: str) -> None:
        self._prune()
        self._seen[event_id] = time.time()

    def _prune(self) -> None:
        cutoff = time.time() - self._window_s
        expired = [k for k, seen_at in self._seen.items() if seen_at < cutoff]
        for key in expired:
            del self._seen[key]


__all__ = [
    "DEDUP_WINDOW_S",
    "DEFAULT_TOLERANCE_S",
    "DuplicateEventError",
    "InvalidSignatureError",
    "SeenWebhookIds",
    "WebhookEvent",
    "safe_equal",
    "verify_webhook",
    "verify_webhook_signature",
]
