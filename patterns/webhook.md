<!-- blueprint
type: pattern
name: webhook
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/retry]
platform: any
tier: free
-->

# Webhook Pattern

Unified inbound reception and outbound delivery of webhooks with
HMAC signature verification, retry semantics, and delivery tracking.
This pattern is a cross-cutting concern — agents that receive or send
webhooks `extends: patterns/webhook` and declare their sources,
event types, and subscriber model.

## Overview

Webhooks are the standard integration primitive for third-party
services. This pattern covers both directions:

- **Inbound**: Receive, validate, and route webhooks from external
  services (Stripe, GitHub, etc.)
- **Outbound**: Send signed webhook notifications to registered
  subscriber endpoints with retries and delivery tracking

Both directions share a common HMAC signature scheme, delivery log
format, and event type model. Agents inherit the full specification
and override only the parts they need.

---

## Shared: HMAC Signature Scheme

All webhook signatures — inbound verification and outbound signing —
use the same algorithm set and header format.

### Supported Algorithms

| Algorithm | Description |
|-----------|-------------|
| `hmac-sha256` | HMAC-SHA256 — **default and recommended** |
| `hmac-sha1` | HMAC-SHA1 (legacy support for older services) |
| `none` | No signature verification (development only) |

### Header Format

```
X-Webhook-Signature: sha256=<hex-encoded-hmac>
```

The HMAC is computed over the **raw request/response body bytes**.

### Security Requirements

- HMAC comparison MUST use **constant-time comparison** to prevent
  timing attacks.
- Secrets MUST be read from environment variables or a secrets
  manager. They MUST NOT be hardcoded in blueprints or source code.
- Implementations SHOULD support verifying against both current and
  previous secrets during rotation periods (dual-secret window).

---

## Inbound Webhooks

### Blueprint Format

```yaml
extends: patterns/webhook

inbound:
  sources:
    stripe:
      path: /webhooks/stripe
      signature:
        header: Stripe-Signature
        algorithm: hmac-sha256
        secret_env: STRIPE_WEBHOOK_SECRET
      events:
        - payment_intent.succeeded
        - invoice.paid
      event_field: body.type          # where to find event type

    github:
      path: /webhooks/github
      signature:
        header: X-Hub-Signature-256
        algorithm: hmac-sha256
        secret_env: GITHUB_WEBHOOK_SECRET
      events:
        - push
        - pull_request
      event_field: header.X-GitHub-Event

  config:
    max_payload_size: 1048576         # 1 MB
    log_retention: 604800             # 7 days in seconds
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/:source` | Receive webhook from named source |
| GET | `/webhooks/log` | View recent delivery log |

### Reception Flow

```
1. Read raw request body (preserve bytes for signature verification)
2. Enforce max_payload_size — reject with 413 if exceeded
3. Look up source configuration by path parameter
4. If unknown source → 404
5. Validate signature:
   a. Extract signature from configured header
   b. Compute HMAC of raw body using source secret
   c. Constant-time compare
   d. If invalid → 401 (log as rejected)
6. Parse JSON body
7. Extract event type from configured event_field
8. Check event type against source's allowed events list
   (if configured — skip if events list is empty)
9. If event not in list → log as filtered, return 200
10. Route to handler (async if possible)
11. Log delivery metadata (source, event, timestamp, status)
12. Return 200 OK with {"received": true}
```

### Event Filtering

If a source defines an `events` list, only matching event types are
processed. Non-matching events receive **200 OK** (to prevent sender
retry loops) but are logged with status `filtered`.

The `event_field` config tells the system where to find the event
type. Convention:
- `body.<path>` — JSON body field (e.g. `body.type` for Stripe)
- `header.<name>` — HTTP header (e.g. `header.X-GitHub-Event`)
- Default: `body.event` or `body.type`

### Error Handling

| Scenario | Response | Log Status |
|----------|----------|------------|
| Payload too large | 413 | `rejected` |
| Unknown source | 404 | not logged |
| Invalid signature | 401 | `rejected` |
| Filtered event | 200 | `filtered` |
| Handler error | 500 | `failed` |
| Success | 200 | `success` |

---

## Outbound Webhooks

### Blueprint Format

```yaml
extends: patterns/webhook

outbound:
  signing_algorithm: hmac-sha256
  max_retries: 5
  retry_backoff: exponential        # 1s, 2s, 4s, 8s, 16s
  timeout: 10                       # seconds per delivery attempt
  max_payload_size: 262144          # 256 KB
  event_types:
    - user.created
    - user.updated
    - order.placed
    - order.shipped
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/subscribers` | Register a new subscriber |
| GET | `/webhooks/subscribers` | List registered subscribers |
| DELETE | `/webhooks/subscribers/:id` | Remove a subscriber |

### Subscriber Registration (POST /webhooks/subscribers)

Request:
```json
{
  "url": "https://example.com/hooks/orders",
  "events": ["order.placed", "order.shipped"],
  "secret": "subscriber-provided-secret"
}
```

Response (201 Created):
```json
{
  "id": "a1b2c3d4...",
  "url": "https://example.com/hooks/orders",
  "events": ["order.placed", "order.shipped"],
  "created": 1713264000,
  "active": true
}
```

- `url` MUST be HTTPS in production (allow HTTP only in development)
- `events` MUST be a subset of configured `event_types`
- `secret` is stored server-side as SHA-256 hash

### Delivery Flow

```
1. Receive event (e.g. "order.placed" with data payload)
2. Find all active subscribers matching the event type
3. For each subscriber:
   a. Build payload: {id, event, timestamp, data}
   b. Enforce max_payload_size — truncate or use reference URL
   c. Compute HMAC-SHA256 of JSON payload using subscriber secret
   d. POST to subscriber URL with headers:
      - Content-Type: application/json
      - X-Webhook-Signature: sha256=<hex-hmac>
      - X-Webhook-ID: <delivery-id>
      - X-Webhook-Timestamp: <unix-timestamp>
   e. If 2xx → mark delivered
   f. If non-2xx or timeout → schedule retry
4. Log delivery attempt (subscriber, event, status, response code)
```

### Delivery Payload

```json
{
  "id": "delivery-id-hex",
  "event": "order.placed",
  "timestamp": 1713264000,
  "data": {
    "order_id": "...",
    "total": 99.99
  }
}
```

### Retry Strategy

Failed deliveries are retried with exponential backoff:

| Attempt | Delay |
|---------|-------|
| 1 | 1 second |
| 2 | 2 seconds |
| 3 | 4 seconds |
| 4 | 8 seconds |
| 5 | 16 seconds |

After `max_retries` failures, the delivery is marked `failed`.
If 3 consecutive events all fail for a subscriber, the subscriber
MAY be deactivated automatically.

---

## Shared: Delivery Log

Both inbound and outbound directions use the same delivery log
format for observability and debugging.

### Log Entry

```json
{
  "id": "a1b2c3d4...",
  "direction": "inbound",
  "source": "stripe",
  "event": "payment_intent.succeeded",
  "timestamp": 1713264000,
  "status": "success",
  "response_code": 200,
  "duration_ms": 12,
  "attempt": 1
}
```

Log entries MUST NOT contain the full payload (to avoid storing
sensitive data). Store only metadata.

**Retention**: Keep delivery logs for a configurable period
(default 7 days). Purge older entries automatically.

---

## Types

### WebhookSource

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | string | yes | URL path for this source |
| signature | SignatureConfig | no | Signature verification config |
| events | []string | no | Allowed event types (empty = all) |
| event_field | string | no | Where to extract event type from |

### SignatureConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| header | string | yes | HTTP header containing the signature |
| algorithm | string | yes | `hmac-sha256`, `hmac-sha1`, `none` |
| secret_env | string | yes | Environment variable with the secret |

### Subscriber

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique subscriber ID |
| url | string | yes | Delivery endpoint URL (HTTPS) |
| events | []string | yes | Subscribed event types |
| secret_hash | string | yes | SHA-256 hash of subscriber secret |
| created | int64 | yes | Registration timestamp |
| active | boolean | yes | Whether subscriber is active |

### WebhookDelivery

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique delivery ID |
| direction | string | yes | `inbound` or `outbound` |
| source | string | yes | Source name (inbound) or subscriber ID (outbound) |
| event | string | no | Event type |
| attempt | int | yes | Attempt number (1-based) |
| timestamp | int64 | yes | Attempt timestamp |
| status | string | yes | `pending`, `success`, `rejected`, `filtered`, `failed` |
| response_code | int | no | HTTP status code |
| duration_ms | int | no | Round-trip time in milliseconds |

### WebhookPayload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Delivery ID |
| event | string | yes | Event type |
| timestamp | int64 | yes | Event timestamp |
| data | object | yes | Event-specific data |

---

## Implementation Notes

- **Raw body preservation**: Read the raw body BEFORE parsing JSON.
  Signature verification MUST use the raw bytes, not re-serialized.
- **Async processing**: Inbound — return 200 immediately, process
  async. Outbound — never block the event producer.
- **HTTPS enforcement**: Reject HTTP subscriber URLs in production.
- **Secret storage**: Store subscriber secrets as SHA-256 hashes.
  Read raw secret only during signing (keep in memory briefly).
- **Idempotency**: Webhook senders may retry. Track delivery IDs
  to deduplicate repeated inbound deliveries. Include `X-Webhook-ID`
  so outbound subscribers can deduplicate too.
- **Ordering**: Best-effort ordered. Subscribers MUST NOT rely on
  delivery order — use timestamps for sequencing.
- **IP allowlisting**: Implementations MAY support IP allowlists
  per inbound source (e.g. Stripe's published IP ranges).
- **Timeout**: Each outbound delivery attempt has a hard timeout
  (default 10s). Slow subscribers MUST NOT block other deliveries.

## Verification Checklist

### Inbound

- [ ] Webhook endpoint receives POST and validates signature
- [ ] HMAC comparison uses constant-time algorithm
- [ ] Secrets are read from environment variables, not hardcoded
- [ ] Unknown sources return 404
- [ ] Invalid signatures return 401 and log as rejected
- [ ] Filtered events return 200 and log as filtered
- [ ] Delivery log records metadata (not full payloads)
- [ ] Event filtering works per source configuration
- [ ] Raw body is preserved for signature verification
- [ ] Payload size limit is enforced (413 if exceeded)

### Outbound

- [ ] Subscribers register with URL, events, and secret
- [ ] Only HTTPS URLs accepted in production
- [ ] Events delivered to all matching subscribers
- [ ] Payload signed with HMAC-SHA256 using subscriber secret
- [ ] Signature sent in X-Webhook-Signature header
- [ ] Failed deliveries retried with exponential backoff
- [ ] Delivery attempts logged with status and response code
- [ ] Max retries enforced
- [ ] Delivery timeout prevents slow subscribers from blocking
- [ ] X-Webhook-ID enables subscriber-side deduplication
