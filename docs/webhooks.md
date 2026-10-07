# Receiving stwrd webhooks

stwrd notifies your application of account events (a user changed their email,
a membership was revoked, and so on) by sending an HTTP `POST` to the webhook
URLs you registered for the application. The scheme is
[Standard Webhooks](https://www.standardwebhooks.com/), the same one Svix,
Clerk and Resend use: a receiver written against that specification, or any
existing library for it, verifies a stwrd event without an adapter. This page
is what you need to write a receiver yourself. The SDKs (`stwrd-auth` for
Python, `@stwrd-auth/node` for Node) already do all of it in `verify_webhook` /
`verifyWebhook`.

## Using the SDK

In Python, `verify_webhook` checks the signature and the replay window and
parses the event. Pass it the raw body and the headers.

```python
from stwrd import DuplicateEventError, InvalidSignatureError, verify_webhook
from stwrd.webhooks import SeenWebhookIds

seen = SeenWebhookIds()


def handle(body: bytes, headers: dict[str, str], secret: str) -> int:
    try:
        event = verify_webhook(body, headers, secret, seen=seen)
    except DuplicateEventError:
        return 200  # already processed
    except InvalidSignatureError:
        return 400
    print(event.type, event.data)
    return 200
```

With the FastAPI router, `auth_router(stwrd, on_event=...)` exposes
`POST /auth/webhook` and does the same.

## Registering receivers

An application can have multiple receivers. Use its administrative UUID as
`application_id` when creating `/api/v1/webhook-endpoints`; the OAuth `client_id`
is not the administrative identity. Each receiver selects explicit event types
from `/api/v1/webhook-event-types?application_id=...`. An empty `subscriptions`
array receives no events. Creation returns metadata, never a signing secret.
A person can reveal the secret in a separate step-up confirmation; an API
client rotates it and receives the new secret once.

Changes to the destination use `/api/v1/webhook-endpoints/{id}/destination-changes`
and rotate the secret atomically. Versioned writes require the current ETag in
`If-Match`. After `412` or `428`, read the resource again and explicitly start a
new change. Repeat an idempotency key only when retrying a lost transport result.
Never store or log returned signing secrets.

## The request

```
POST {your webhook URL}
Content-Type: application/json
webhook-id:        <event id, a UUID>
webhook-timestamp: <Unix time in seconds>
webhook-signature: v1,<base64 signature>
```

The current event body is a strict v1 JSON object:

```json
{"id": "…", "type": "user.email_updated", "api_version": "v1", "created_at": "2026-07-26T12:00:00Z", "data": {"user_id": "…"}}
```

`id` is a canonical hyphenated UUID matching the `webhook-id` header
(case-insensitively); the parser preserves its original spelling.
`created_at` is a valid ISO UTC instant with `Z` or `+00:00`, never a local
time or an impossible calendar date. Header names are sent in
lowercase; read them case-insensitively, since proxies and HTTP/2 can change
their case. New event types and new fields in `data` can be added at any time:
ignore the ones you do not know.

The webhook URL must be `https` and must resolve to a public address. stwrd
does not deliver over plain `http` or to private network addresses.

## How the signature is built

1. Build the signed content by joining three parts with dots:

   ```
   {webhook-id}.{webhook-timestamp}.{body}
   ```

   - `webhook-id` and `webhook-timestamp` are the header values **as strings,
     exactly as received**. Do not parse the timestamp into a number and print
     it back.
   - `body` is the **raw bytes of the request body**, exactly as received.
     Parsing the JSON and serialising it again changes key order and
     whitespace, and the signature stops matching. Read the raw body before
     your framework parses it.
2. Compute `HMAC-SHA256` of the signed content. The key is your webhook secret
   as issued, encoded as UTF-8 and used verbatim (it is not base64-decoded).
3. Encode the digest in standard base64 (alphabet `+/` with `=` padding, not the
   URL-safe variant).
4. Prepend the version prefix `v1,`.

The result is the value that appears in `webhook-signature`.

## Verifying a delivery

Do these in order, and answer any failure with a `400`.

1. **Headers present.** `webhook-id`, `webhook-timestamp` and
   `webhook-signature` must all be there.
2. **Timestamp format.** It must be a decimal integer made of ASCII digits, with
   an optional leading `-` and optional surrounding spaces, and nothing else: no
   `+` sign, no thousands separators, no non-ASCII digits.
3. **Replay window.** Reject a delivery whose timestamp is more than **300
   seconds** away from your clock, even if the signature is valid. Keep your
   server clock synchronised.
4. **Signature.** `webhook-signature` holds **one or more signatures separated
   by spaces**, each starting with `v1,`. Compute the expected signature as
   above and accept the delivery if **any** candidate matches. Ignore a
   candidate that does not start with `v1,`. If none matches, reject (fail
   closed).
5. **Constant-time comparison.** Compare each candidate with the expected value
   using a constant-time function (`hmac.compare_digest` in Python,
   `crypto.timingSafeEqual` in Node), and do not stop at the first match. A
   signature containing non-ASCII bytes is a bad signature like any other:
   answer `400`, not a server error.
6. **De-duplicate** by `webhook-id` (see below).

## Secret rotation: more than one signature

When a webhook secret is rotated, the previous secret keeps signing for **24
hours**. During that time every delivery carries two signatures in the same
header, the current secret first:

```
webhook-signature: v1,<signed with the new secret> v1,<signed with the old secret>
```

You switch your configuration to the new secret whenever it suits you inside that
window and lose no events. The receiver needs no special mode: it is the same
loop over the candidates. A rotation requested with an API credential rather
than by a person signed in to the dashboard opens no overlap: the previous
secret stops signing immediately.

## Delivery guarantees

**At least once.** The same event can arrive more than once, for example when
your response is lost and stwrd retries. Your receiver must be idempotent by
`webhook-id`: record the ids you have processed and, on a repeat, answer `2xx`
without processing it again. The SDKs keep a 30-hour, in-memory window of seen
ids as a convenience. It is lost when the process restarts, so it does not
replace your own storage.

**No ordering.** Events can arrive in a different order than they happened, and
an event that failed and is waiting for a retry can arrive hours after a later
one. Use `created_at` (in the body) to order them or, better, treat each event
as a signal to fetch the current state through the API.

**Retries.** Answer with a `2xx` status to acknowledge a delivery. A response
with status `400` or above, or no response, is retried, up to 8 attempts in
total, on this schedule:

| Retry | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| Wait after the previous failure | 1 min | 5 min | 30 min | 2 h | 5 h | 10 h | 10 h |

The last attempt happens about 27.6 hours after the first, which is how long a
receiver that is down has to come back without losing events. After that the
delivery is marked as exhausted and can be retried manually from the dashboard.
Each attempt is signed again, with a fresh timestamp.

The raw signature helpers `verify_webhook_signature` / `verifyWebhookSignature`
verify bytes without parsing an envelope. The vector below is a raw-signature
vector: its body is not a v1 event envelope, so raw verification accepts it
while the strict v1 event parsers reject it. Never reserialize or adapt a body
before verifying.

## Shared test vector

Use this vector to check your implementation. The stwrd SDKs and the stwrd
service are all verified against this exact input and output, so a receiver
that reproduces this signature computes the same bytes stwrd does.

```
secret:    whsec-shared-test-vector
id:        0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0
timestamp: 1700000000
body:      {"id":"0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0","event":"User.EmailChanged",
            "created_at":"2023-11-14T22:13:20Z","data":{"sub":"usr_vector",
            "previous_email":"old@example.com","email":"new@example.com"}}
signature: v1,y1IHsA+qHnO6lboJU4ecv86+dtwmeKm4da6G5z1qH2w=
```

The body is a single line with no spaces: it is wrapped above only for reading.
Join the three lines, dropping the indentation and adding nothing, and the signed
content is `0f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0.1700000000.` followed by that
body.

The timestamp is far outside the replay window, so check the signature
computation on its own rather than through a full delivery check, or pass a
tolerance large enough to admit it.
