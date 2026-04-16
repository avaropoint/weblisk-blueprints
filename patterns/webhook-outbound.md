<!-- blueprint
type: pattern
name: webhook-outbound
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Webhook Outbound Blueprint

Send webhooks with retries, HMAC signatures, and delivery tracking.
Define your event types and subscriber endpoints once, then generate a
complete outbound webhook system on any Weblisk server implementation.

## Overview

The `webhook-outbound` blueprint generates a system for sending webhook
notifications to registered subscriber endpoints. Events are signed
with HMAC for integrity, delivered with exponential backoff retries,
and tracked for observability. Subscribers register via API and receive
only the event types they subscribe to.

## Specification

### Blueprint Format

```yaml
name: webhook-outbound
version: 1.0.0
description: Send webhooks with retries and delivery tracking

config:
  signing_algorithm: hmac-sha256
  max_retries: 5
  retry_backoff: exponential   # 1s, 2s, 4s, 8s, 16s
  timeout: 10                  # seconds per delivery attempt
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

- `url` MUST be HTTPS (reject plain HTTP in production)
- `events` MUST be a subset of configured `event_types`
- `secret` is stored server-side for signing deliveries

### Sending a Webhook

When an event occurs, the system delivers it to all matching subscribers:

```
1. Find all active subscribers subscribed to the event type
2. For each subscriber:
   a. Build payload: {id, event, timestamp, data}
   b. Compute HMAC-SHA256 of JSON payload using subscriber's secret
   c. POST to subscriber URL with:
      - Content-Type: application/json
      - X-Webhook-Signature: sha256=<hex-hmac>
      - X-Webhook-ID: <delivery-id>
      - X-Webhook-Timestamp: <unix-timestamp>
   d. If response is 2xx → mark delivered
   e. If response is non-2xx or timeout → schedule retry
3. Log delivery attempt (subscriber, event, status, response code)
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

After `max_retries` failures, the delivery is marked as `failed` and
the subscriber MAY be deactivated if failures persist (e.g. 3
consecutive events all fail).

### Delivery Tracking

Each delivery attempt is recorded:

```json
{
  "delivery_id": "a1b2c3d4...",
  "subscriber_id": "e5f6g7h8...",
  "event": "order.placed",
  "attempt": 2,
  "timestamp": 1713264002,
  "status": "success",
  "response_code": 200,
  "duration_ms": 145
}
```

Delivery logs are queryable via the subscriber list endpoint
(implementation-dependent).

### Signature Format

The signature header contains:

```
X-Webhook-Signature: sha256=<hex-encoded-hmac>
```

The HMAC is computed over the raw JSON payload body using the
subscriber's stored secret.

Subscribers verify by:
1. Reading the raw request body
2. Computing HMAC-SHA256 with their secret
3. Comparing (constant-time) against the header value

## Types

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
| delivery_id | string | yes | Unique delivery ID |
| subscriber_id | string | yes | Target subscriber |
| event | string | yes | Event type |
| attempt | int | yes | Attempt number (1-based) |
| timestamp | int64 | yes | Attempt timestamp |
| status | string | yes | pending, success, failed |
| response_code | int | no | HTTP response from subscriber |
| duration_ms | int | no | Round-trip time in milliseconds |

### WebhookPayload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Delivery ID |
| event | string | yes | Event type |
| timestamp | int64 | yes | Event timestamp |
| data | object | yes | Event-specific data |

## Implementation Notes

- **Async delivery**: Webhook sending MUST be asynchronous. Never block
  the event producer to wait for subscriber responses.
- **HTTPS enforcement**: Reject HTTP subscriber URLs in production.
  Allow HTTP only in development mode.
- **Secret storage**: Store subscriber secrets as SHA-256 hashes. Read
  the raw secret only during delivery signing (keep in memory briefly).
  Alternatively, encrypt at rest with a server-side key.
- **Timeout**: Each delivery attempt has a hard timeout (default 10s).
  Slow subscribers MUST NOT block other deliveries.
- **Ordering**: Webhook deliveries are best-effort ordered. Subscribers
  MUST NOT rely on delivery order — use timestamps for sequencing.
- **Deduplication**: Include `X-Webhook-ID` so subscribers can
  deduplicate retried deliveries.
- **Payload size**: Limit payload to 256 KB. For larger data, include
  a reference URL instead of inline data.

## Verification Checklist

- [ ] Subscribers register with URL, events, and secret
- [ ] Only HTTPS URLs are accepted in production
- [ ] Events are delivered to all matching subscribers
- [ ] Payload is signed with HMAC-SHA256 using subscriber's secret
- [ ] Signature is sent in X-Webhook-Signature header
- [ ] Failed deliveries are retried with exponential backoff
- [ ] Delivery attempts are logged with status and response code
- [ ] Max retries is enforced
- [ ] Delivery timeout prevents slow subscribers from blocking
- [ ] X-Webhook-ID enables subscriber-side deduplication
