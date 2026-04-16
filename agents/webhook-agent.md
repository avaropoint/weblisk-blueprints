<!-- blueprint
type: agent
kind: infrastructure
name: webhook-agent
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, patterns/webhook-inbound, patterns/webhook-outbound]
platform: any
tier: free
-->

# Webhook Agent

Inbound and outbound webhook processing with signature verification,
retries, and delivery tracking. Combines the webhook-inbound and
webhook-outbound blueprints into an autonomous agent that manages
the full webhook lifecycle.

## Overview

The webhook agent is the runtime counterpart to the webhook-inbound
and webhook-outbound blueprints. While those blueprints define the
API surface, this agent handles the asynchronous work: verifying
inbound signatures, routing events to handlers, sending outbound
webhooks with retries, and tracking delivery status. It runs as a
background process alongside the main server.

## Capabilities

```json
{
  "capabilities": [
    {"name": "http:receive", "resources": ["/webhooks/*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["webhook_subscribers", "webhook_deliveries"]},
    {"name": "database:write", "resources": ["webhook_subscribers", "webhook_deliveries"]},
    {"name": "agent:message", "resources": ["*"]}
  ],
  "inputs": [
    {"name": "webhook_event", "type": "json", "description": "Inbound webhook payload or outbound event to deliver"}
  ],
  "outputs": [
    {"name": "delivery_result", "type": "json", "description": "Delivery status and tracking info"}
  ],
  "collaborators": ["cron-agent"]
}
```

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `webhook.received` | Inbound webhook arrives |
| Event: `webhook.send` | Application emits an event for outbound delivery |
| Schedule: `*/1 * * * *` | Every minute — retry failed deliveries |

## Configuration

```yaml
config:
  inbound:
    max_payload_size: 1048576     # 1 MB
    log_retention: 604800         # 7 days

  outbound:
    signing_algorithm: hmac-sha256
    max_retries: 5
    retry_backoff: exponential
    timeout: 10
    max_payload_size: 262144      # 256 KB
```

## Execute Workflow

### Inbound Flow

```
Phase 1 — Receive:
  Read raw request body (preserve bytes for signature check).
  Look up source configuration by URL path.

Phase 2 — Verify:
  Extract signature from configured header.
  Compute HMAC over raw body using source secret.
  Constant-time compare. Reject if mismatch.

Phase 3 — Route:
  Parse JSON body.
  Extract event type.
  If event is in source's allowed list (or list is empty):
    Route to registered handler (agent message or callback).
  Else:
    Log as filtered, return 200.

Phase 4 — Log:
  Record delivery in log: source, event, status, timestamp.
  Respond 200 to sender.
```

### Outbound Flow

```
Phase 1 — Receive event:
  Application emits an event (e.g. "order.placed" with data).

Phase 2 — Fan out:
  Query subscriber store for all active subscribers matching
  this event type.

Phase 3 — Deliver:
  For each subscriber:
  - Build payload: {id, event, timestamp, data}
  - Sign payload with subscriber's secret (HMAC-SHA256)
  - POST to subscriber URL with signature headers
  - Record attempt

Phase 4 — Handle result:
  If 2xx → mark delivered
  If non-2xx or timeout → schedule retry (respect backoff)
  After max_retries → mark failed

Phase 5 — Track:
  Update delivery record with status, response code, duration.
```

### Retry Sweep (scheduled)

```
Phase 1 — Query pending retries:
  Load deliveries with status=pending and next_retry <= now.

Phase 2 — Reattempt:
  For each pending delivery:
  - Re-sign and re-send
  - Update attempt count
  - If success → mark delivered
  - If fail and retries remain → schedule next retry
  - If fail and no retries → mark failed
```

## HandleMessage Actions

### process_inbound

Process an inbound webhook that was received by the HTTP layer.

- Input: `{source, headers, body, raw_body}`
- Output: `{status: "success|rejected|filtered", delivery_id: "..."}`

### send_event

Queue an outbound event for delivery to subscribers.

- Input: `{event: "order.placed", data: {...}}`
- Output: `{queued: N, delivery_ids: [...]}`

### register_subscriber

Register a new outbound webhook subscriber.

- Input: `{url, events, secret}`
- Output: `{subscriber_id: "...", active: true}`

### list_subscribers

List registered subscribers.

- Output: `{subscribers: [...]}`

### delivery_status

Check delivery status for a specific event or subscriber.

- Input: `{delivery_id: "..."}` or `{subscriber_id: "..."}`
- Output: `{deliveries: [...]}`

## Types

See types defined in:
- [webhook-inbound pattern](../patterns/webhook-inbound.md)
- [webhook-outbound pattern](../patterns/webhook-outbound.md)

### WebhookAgentConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| inbound | InboundConfig | yes | Inbound webhook settings |
| outbound | OutboundConfig | yes | Outbound webhook settings |

### InboundConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| max_payload_size | int | yes | Max inbound body size in bytes |
| log_retention | int | yes | Log retention in seconds |

### OutboundConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| signing_algorithm | string | yes | HMAC algorithm for signing |
| max_retries | int | yes | Max delivery attempts |
| retry_backoff | string | yes | Backoff strategy |
| timeout | int | yes | Per-delivery timeout in seconds |
| max_payload_size | int | yes | Max outbound payload in bytes |

## Implementation Notes

- **Separation of concerns**: The webhook blueprints define the API
  contract. This agent implements the background processing. The HTTP
  endpoints may live in the main server; the agent handles async work.
- **Collaboration with cron-agent**: The retry sweep can be delegated
  to the cron-agent for scheduling instead of running its own timer.
- **Signature verification**: Always verify on the raw bytes. JSON
  re-serialization may change field order and break signatures.
- **Subscriber deactivation**: If a subscriber fails N consecutive
  events (e.g. 3), consider auto-deactivating and notifying the
  subscriber owner.
- **Observability**: Expose delivery metrics (success rate, avg
  latency, failure rate) via the health endpoint.

## Verification Checklist

- [ ] Inbound webhooks are verified with HMAC signature
- [ ] Rejected webhooks are logged with status "rejected"
- [ ] Filtered events return 200 and are logged
- [ ] Outbound events fan out to all matching subscribers
- [ ] Outbound deliveries include HMAC signature headers
- [ ] Failed deliveries are retried with exponential backoff
- [ ] Retry sweep processes pending retries on schedule
- [ ] Delivery tracking records all attempts
- [ ] Max retries exhausted marks delivery as failed
- [ ] Subscriber registration validates HTTPS URLs
