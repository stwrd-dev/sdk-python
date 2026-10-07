"""Standard Webhooks verification, against the shared signing vector: the exact
bytes from the client-facing contract (`docs/webhooks.md`), not a value this
suite invents.
"""

from __future__ import annotations

import pathlib
import time

import pytest

from stwrd import DuplicateEventError, InvalidSignatureError, safe_equal, verify_webhook
from stwrd.webhooks import SeenWebhookIds, verify_webhook_signature

# The webhook contract is `docs/webhooks.md`, next to `tests/` in this package
# (and in its standalone repository). Its "Shared test vector" section is the
# ONE place the vector is written down; every implementation of the scheme
# verifies the same bytes, so if one side drifts, the check fails here and not
# in production.
WEBHOOK_CONTRACT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "webhooks.md"


def _shared_vector() -> dict[str, str]:
    """The frozen vector, read from the "Shared test vector" block of the
    client-facing contract — the ONE place it is written. Reading it from the
    contract, instead of keeping a verbatim copy in each implementation's
    tests, means a scheme change cannot be "fixed" on one side alone while the
    others stay green: the only way to move the vector is to move it for
    everyone."""
    section = WEBHOOK_CONTRACT.read_text(encoding="utf-8").split("## Shared test vector", 1)[1]
    block = section.split("```", 2)[1]
    vector: dict[str, str] = {}
    key = ""
    for line in block.splitlines():
        if not line.strip():
            continue
        if line[0].isspace():
            # A wrapped value (the body spans three lines in the contract): the
            # continuation is appended with its indentation removed, and
            # nothing else — the bytes are the vector.
            vector[key] += line.strip()
        else:
            key, _, value = line.partition(":")
            vector[key.strip()] = value.strip()
    return vector


_VECTOR = _shared_vector()
VECTOR_SECRET = _VECTOR["secret"]
VECTOR_ID = _VECTOR["id"]
VECTOR_TIMESTAMP = _VECTOR["timestamp"]
VECTOR_BODY = _VECTOR["body"].encode("ascii")
VECTOR_SIGNATURE = _VECTOR["signature"]


def _headers(**overrides: str) -> dict[str, str]:
    headers = {
        "webhook-id": VECTOR_ID,
        "webhook-timestamp": VECTOR_TIMESTAMP,
        "webhook-signature": VECTOR_SIGNATURE,
    }
    headers.update(overrides)
    return headers


def test_the_shared_vector_verifies() -> None:
    # The vector's timestamp is fixed in the past (2023), so the replay
    # window is disabled here on purpose — this test is about the HMAC
    # scheme, not the clock.
    assert (
        verify_webhook_signature(VECTOR_BODY, _headers(), VECTOR_SECRET, tolerance_s=10**12)
        == VECTOR_ID
    )
    with pytest.raises(InvalidSignatureError):
        verify_webhook(VECTOR_BODY, _headers(), VECTOR_SECRET, tolerance_s=10**12)


def test_a_wrong_secret_is_rejected() -> None:
    with pytest.raises(InvalidSignatureError):
        verify_webhook(VECTOR_BODY, _headers(), "not-the-right-secret", tolerance_s=10**12)


def test_a_re_serialized_body_breaks_the_signature() -> None:
    # The body is signed exactly as sent: re-serializing the JSON changes key
    # order and whitespace, and verification starts failing on its own.
    import json

    reserialized = json.dumps(json.loads(VECTOR_BODY)).encode()
    assert reserialized != VECTOR_BODY  # sanity: the bytes actually differ
    with pytest.raises(InvalidSignatureError):
        verify_webhook(reserialized, _headers(), VECTOR_SECRET, tolerance_s=10**12)


def test_case_insensitive_headers() -> None:
    event_id = verify_webhook_signature(
        VECTOR_BODY,
        {
            "Webhook-Id": VECTOR_ID,
            "Webhook-Timestamp": VECTOR_TIMESTAMP,
            "Webhook-Signature": VECTOR_SIGNATURE,
        },
        VECTOR_SECRET,
        tolerance_s=10**12,
    )
    assert event_id == VECTOR_ID


@pytest.mark.parametrize(
    "timestamp",
    ["+1700000000", "1_700_000_000", "１７００００００００", "not-a-number", ""],
)
def test_a_malformed_timestamp_is_rejected(timestamp: str) -> None:
    # The timestamp must match `^-?\\d+$` and nothing else: no `+1700000000`,
    # no thousands separators, no Unicode digits.
    with pytest.raises(InvalidSignatureError):
        verify_webhook(VECTOR_BODY, _headers(**{"webhook-timestamp": timestamp}), VECTOR_SECRET)


def test_a_timestamp_outside_the_replay_window_is_rejected() -> None:
    with pytest.raises(InvalidSignatureError):
        verify_webhook(VECTOR_BODY, _headers(), VECTOR_SECRET, tolerance_s=300)


def test_current_delivery_within_the_default_tolerance_is_accepted() -> None:
    import base64
    import hashlib
    import hmac
    import json

    body = json.dumps(
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "type": "user.created",
            "api_version": "v1",
            "created_at": "2026-01-01T00:00:00Z",
            "data": {"user_id": "usr_2"},
        },
        separators=(",", ":"),
    ).encode()
    timestamp = str(int(time.time()))
    signed = f"{'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'}.{timestamp}.".encode() + body
    signature = (
        "v1,"
        + base64.b64encode(
            hmac.new(VECTOR_SECRET.encode(), signed, hashlib.sha256).digest()
        ).decode()
    )
    event = verify_webhook(
        body,
        {
            "webhook-id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "webhook-timestamp": timestamp,
            "webhook-signature": signature,
        },
        VECTOR_SECRET,
    )
    assert event.type == "user.created"


def test_multiple_candidates_accepts_if_any_matches() -> None:
    # The signature header carries one or more space-separated signatures and
    # the delivery is accepted if any of them matches.
    header = f"v1,not-the-right-signature== {VECTOR_SIGNATURE}"
    event_id = verify_webhook_signature(
        VECTOR_BODY,
        _headers(**{"webhook-signature": header}),
        VECTOR_SECRET,
        tolerance_s=10**12,
    )
    assert event_id == VECTOR_ID


def test_a_candidate_with_non_ascii_bytes_fails_cleanly() -> None:
    # A signature with non-ASCII bytes gives a 400 `invalid_signature` like any
    # other bad signature, not a 500.
    with pytest.raises(InvalidSignatureError):
        verify_webhook(
            VECTOR_BODY,
            _headers(**{"webhook-signature": "v1,\u00e9\u00e9\u00e9=="}),
            VECTOR_SECRET,
            tolerance_s=10**12,
        )


def test_dedup_raises_on_a_repeated_id() -> None:
    seen: set[str] = set()
    body, headers = _signed_event()
    verify_webhook(body, headers, VECTOR_SECRET, seen=seen)
    with pytest.raises(DuplicateEventError):
        verify_webhook(body, headers, VECTOR_SECRET, seen=seen)


def test_seen_webhook_ids_prunes_after_its_window() -> None:
    seen = SeenWebhookIds(window_s=0)
    seen.add(VECTOR_ID)
    # A zero-second window means the entry is immediately stale.
    assert VECTOR_ID not in seen


def test_safe_equal_is_true_only_for_equal_strings() -> None:
    assert safe_equal("abc", "abc") is True
    assert safe_equal("abc", "abd") is False


def _signed_event(**overrides):
    import base64
    import hashlib
    import hmac
    import json

    event_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    doc = {
        "id": event_id,
        "type": "user.created",
        "api_version": "v1",
        "created_at": "2026-10-06T00:00:00Z",
        "data": {"user_id": "usr_2"},
        **overrides,
    }
    body = json.dumps(doc).encode()
    timestamp = str(int(time.time()))
    event_id = str(doc["id"])
    signature = (
        "v1,"
        + base64.b64encode(
            hmac.new(
                VECTOR_SECRET.encode(), f"{event_id}.{timestamp}.".encode() + body, hashlib.sha256
            ).digest()
        ).decode()
    )
    return body, {
        "webhook-id": event_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": signature,
    }


def test_v1_preserves_producer_data_without_legacy_aliases():
    body, headers = _signed_event(data={"extension": {"value": 3}})
    event = verify_webhook(body, headers, VECTOR_SECRET)
    assert event.type == "user.created"
    assert event.api_version == "v1"
    assert event.data == {"extension": {"value": 3}}
    assert not hasattr(event, "event")


@pytest.mark.parametrize(
    "overrides",
    [
        {"event": "User.Created"},
        {"api_version": "v2"},
        {"type": ""},
        {"data": []},
        {"data": None},
        {"id": "other"},
    ],
)
def test_signed_invalid_envelope_is_rejected_before_dedup(overrides):
    body, headers = _signed_event(**overrides)
    seen = set()
    with pytest.raises(InvalidSignatureError):
        verify_webhook(body, headers, VECTOR_SECRET, seen=seen)
    assert not seen


@pytest.mark.parametrize(
    "event_id", ["aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE"]
)
def test_v1_preserves_canonical_uuid_and_utc_offset(event_id):
    body, headers = _signed_event(id=event_id, created_at="2026-10-06T00:00:00.123456+00:00")
    assert verify_webhook(body, headers, VECTOR_SECRET).id == event_id


@pytest.mark.parametrize(
    "created_at",
    [
        "2026-02-30T00:00:00Z",
        "2025-02-29T00:00:00Z",
        "2026-13-01T00:00:00Z",
        "2026-10-06T24:00:00Z",
        "2026-10-06T00:00:00",
        "2026-10-06T00:00:00+01:00",
        "garbage",
        "",
        None,
        7,
    ],
)
def test_v1_rejects_non_utc_or_impossible_date(created_at):
    body, headers = _signed_event(created_at=created_at)
    with pytest.raises(InvalidSignatureError):
        verify_webhook(body, headers, VECTOR_SECRET)


@pytest.mark.parametrize(
    "event_id",
    [
        "aaaaaaaabbbbccccddddeeeeeeeeeeee",
        "urn:uuid:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "evt-1",
        None,
        7,
    ],
)
def test_v1_rejects_noncanonical_uuid_but_raw_verifies(event_id):
    body, headers = _signed_event(id=event_id)
    assert verify_webhook_signature(body, headers, VECTOR_SECRET) == str(event_id)
    with pytest.raises(InvalidSignatureError):
        verify_webhook(body, headers, VECTOR_SECRET)


def test_v1_rejects_header_uuid_case_mismatch_while_raw_remains_valid():
    import base64
    import hashlib
    import hmac

    body, headers = _signed_event(id="AAAAAAAA-BBBB-CCCC-DDDD-EEEEEEEEEEEE")
    headers["webhook-id"] = headers["webhook-id"].lower()
    signed = f"{headers['webhook-id']}.{headers['webhook-timestamp']}.".encode() + body
    headers["webhook-signature"] = (
        "v1,"
        + base64.b64encode(
            hmac.new(VECTOR_SECRET.encode(), signed, hashlib.sha256).digest()
        ).decode()
    )
    assert verify_webhook_signature(body, headers, VECTOR_SECRET) == headers["webhook-id"]
    with pytest.raises(InvalidSignatureError):
        verify_webhook(body, headers, VECTOR_SECRET)


def test_raw_verification_accepts_arbitrary_signed_bytes_and_header_identifier():
    import base64
    import hashlib
    import hmac

    body = b"\xff\x00."
    event_id = "evt-1"
    timestamp = str(int(time.time()))
    signature = (
        "v1,"
        + base64.b64encode(
            hmac.new(
                VECTOR_SECRET.encode(), f"{event_id}.{timestamp}.".encode() + body, hashlib.sha256
            ).digest()
        ).decode()
    )
    headers = {
        "webhook-id": event_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": signature,
    }
    assert verify_webhook_signature(body, headers, VECTOR_SECRET) == event_id
    with pytest.raises(InvalidSignatureError):
        verify_webhook(body, headers, VECTOR_SECRET)
