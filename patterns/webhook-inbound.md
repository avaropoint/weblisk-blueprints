<!-- blueprint
type: pattern
name: webhook-inbound
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Webhook Inbound Blueprint

Receive, validate, and route inbound webhooks from third-party
services. Define your webhook sources and handlers once, then
generate a secure ingestion layer on any Weblisk server implementation.

## Overview

The `webhook-inbound` blueprint generates endpoints that receive
webhook payloads from external services (e.g. Stripe, GitHub, Twilio).
Each source is configured with its own validation scheme (HMAC
signatures, IP allowlists, etc.) and routed to a handler. Failed
deliveries are logged for debugging.

## Specification

### Blueprint Format

```yaml
name: webhook-inbound
version: 1.0.0
description: Receive and validate inbound webhooks

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

  github:
    path: /webhooks/github
    signature:
      header: X-Hub-Signature-256
      algorithm: hmac-sha256
      secret_env: GITHUB_WEBHOOK_SECRET
    events:
      - push
      - pull_request
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/webhooks/:source` | Receive webhook from named source |
| GET | `/webhooks/log` | View recent webhook delivery log |

### Webhook Reception (POST /webhooks/:source)

Processing flow:

```
1. Read raw request body (preserve for signature verification)
2. Look up source configuration by path parameter
3. If unknown source → 404
4. Validate signature:
   a. Extract signature from configured header
   b. Compute HMAC of raw body using source secret
   c. Compare signatures (constant-time)
   d. If invalid → 401 (log the attempt)
5. Parse JSON body
6. Check event type against source's allowed events list
   (if configured — skip if events list is empty)
7. Log the delivery (source, event, timestamp, status)
8. Route to handler (async if possible)
9. Return 200 OK with {"received": true}
```

### Signature Verification

Supported algorithms:

| Algorithm | Description |
|-----------|-------------|
| `hmac-sha256` | HMAC-SHA256 of raw body, compared against header |
| `hmac-sha1` | HMAC-SHA1 (legacy support for older services) |
| `none` | No signature verification (development only) |

**HMAC verification MUST use constant-time comparison** to prevent
timing attacks.

Secrets are read from environment variables (specified in `secret_env`).
They MUST NOT be hardcoded in the blueprint or source code.

### Delivery Log

The delivery log stores recent webhook deliveries for debugging:

```json
{
  "deliveries": [
    {
      "id": "a1b2c3d4...",
      "source": "stripe",
      "event": "payment_intent.succeeded",
      "timestamp": 1713264000,
      "status": "success",
      "response_code": 200
    }
  ],
  "pagination": {
    "next_cursor": "...",
    "has_more": false
  }
}
```

Log entries MUST NOT contain the full payload (to avoid storing
sensitive data). Store only metadata.

### Event Filtering

If a source defines an `events` list, only matching event types are
processed. Non-matching events receive 200 OK (to prevent retry loops)
but are logged with status `filtered`.

Event type is extracted from the parsed body. The field varies by
source:
- Stripe: `body.type`
- GitHub: `X-GitHub-Event` header
- Generic: `body.event` or `body.type`

Implementations SHOULD allow configuring the event field per source.

### Error Handling

| Scenario | Response | Log Status |
|----------|----------|------------|
| Unknown source | 404 | not logged |
| Invalid signature | 401 | `rejected` |
| Filtered event | 200 | `filtered` |
| Handler error | 500 | `failed` |
| Success | 200 | `success` |

Return 200 for filtered events to prevent the sending service from
retrying deliveries the server intentionally ignores.

## Types

### WebhookSource

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | string | yes | URL path for this source |
| signature | SignatureConfig | no | Signature verification config |
| events | []string | no | Allowed event types (empty = all) |

### SignatureConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| header | string | yes | HTTP header containing the signature |
| algorithm | string | yes | Verification algorithm |
| secret_env | string | yes | Environment variable with the secret |

### DeliveryLog

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique delivery ID |
| source | string | yes | Source name |
| event | string | no | Event type |
| timestamp | int64 | yes | Reception time |
| status | string | yes | success, rejected, filtered, failed |
| response_code | int | yes | HTTP status returned |

## Implementation Notes

- **Raw body preservation**: Read the raw body BEFORE parsing JSON.
  Signature verification MUST be performed on the raw bytes, not a
  re-serialized version.
- **Secret rotation**: Implementations SHOULD support verifying against
  both current and previous secrets during rotation periods.
- **Idempotency**: Webhook senders may retry. Implementations SHOULD
  track delivery IDs to deduplicate repeated deliveries.
- **Async processing**: Return 200 immediately and process the webhook
  asynchronously. Long-running handlers will cause the sender to retry.
- **Log retention**: Keep delivery logs for a configurable period
  (default 7 days). Purge older entries automatically.
- **IP allowlisting**: For additional security, implementations MAY
  support IP allowlists per source (e.g. Stripe's published IP ranges).
- **Payload size**: Reject bodies larger than 1 MB to prevent abuse.

## Verification Checklist

- [ ] Webhook endpoint receives POST and validates signature
- [ ] HMAC comparison uses constant-time algorithm
- [ ] Secrets are read from environment variables, not hardcoded
- [ ] Unknown sources return 404
- [ ] Invalid signatures return 401 and log as rejected
- [ ] Filtered events return 200 and log as filtered
- [ ] Delivery log records metadata (not full payloads)
- [ ] Event filtering works per source configuration
- [ ] Raw body is preserved for signature verification
- [ ] Payload size limit is enforced
