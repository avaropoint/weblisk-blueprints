<!-- blueprint
type: agent
kind: infrastructure
name: webhook
version: 1.1.0
port: 9753
requires: [protocol/spec, protocol/types, architecture/agent]
extends: [patterns/webhook, patterns/observability, patterns/storage, patterns/state-machine, patterns/scope, patterns/policy, patterns/safety, patterns/contract, patterns/security, patterns/governance]
depends_on: []
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

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token, services]
        - path: /v1/message
          methods: [POST]
          request_type: MessageEnvelope
          response_fields: [status, response]
        - path: /v1/health
          methods: [GET]
          response_fields: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskRequest
          fields_used: [id, from, target_agent, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: EventEnvelope
          fields_used: [from, to, action, payload, trace_id]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: startup-sequence
          parameters: [identity, storage, registration, health]
        - behavior: shutdown-sequence
          parameters: [drain, deregister, close]
        - behavior: health-reporting
          parameters: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

extends:
  - pattern: patterns/webhook
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: inbound-verification
          parameters: [signature_header, hmac_algorithm, secret]
        - behavior: outbound-signing
          parameters: [signing_algorithm, secret, headers]
        - behavior: delivery-tracking
          parameters: [status, attempts, response_code]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: metrics
          parameters: [gauge, counter, histogram]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes, relationships, constraints]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: state-transitions
          parameters: [states, triggers, validates]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: identity
          parameters: [keypair, signing, verification]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: self-governance
          parameters: [reconciliation, change-assessment]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

depends_on: []
  # No runtime agent dependencies. Webhook agent operates independently.
  # Retry sweep can optionally be delegated to cron agent.
```

---

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
  "collaborators": ["cron"]
}
```

### Trigger Summary

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
- [webhook pattern](../patterns/webhook.md)

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

---

## Storage

```yaml
storage:
  engine: sqlite

  tables:
    webhook_subscribers:
      description: Registered outbound webhook subscribers
      fields:
        subscriber_id: {type: string, format: uuid-v7, primary_key: true}
        url: {type: string, description: HTTPS callback URL}
        events: {type: array, description: Event types to deliver}
        secret: {type: string, description: HMAC signing secret}
        active: {type: bool, default: true}
        consecutive_failures: {type: int, default: 0}
        created_at: {type: int64, auto: true}
        updated_at: {type: int64, auto: true}
      indexes:
        - name: idx_subscriber_events
          fields: [active, events]
          type: btree
          description: Fast lookup of active subscribers by event type
        - name: idx_subscriber_url
          fields: [url]
          type: unique

    webhook_deliveries:
      description: Delivery tracking for outbound webhooks
      fields:
        delivery_id: {type: string, format: uuid-v7, primary_key: true}
        subscriber_id: {type: string, references: webhook_subscribers.subscriber_id}
        event_type: {type: string}
        payload: {type: object}
        status: {type: string, enum: [pending, delivered, failed]}
        attempts: {type: int, default: 0}
        max_retries: {type: int}
        next_retry: {type: int64, optional: true}
        response_code: {type: int, optional: true}
        duration_ms: {type: int, optional: true}
        error: {type: string, optional: true}
        created_at: {type: int64, auto: true}
        delivered_at: {type: int64, optional: true}
      indexes:
        - name: idx_delivery_status
          fields: [status, next_retry]
          type: btree
          description: Fast lookup of pending retries
        - name: idx_delivery_subscriber
          fields: [subscriber_id, created_at]
          type: btree

    webhook_inbound_log:
      description: Log of received inbound webhooks
      fields:
        log_id: {type: string, format: uuid-v7, primary_key: true}
        source: {type: string}
        event_type: {type: string}
        status: {type: string, enum: [success, rejected, filtered]}
        timestamp: {type: int64, auto: true}
      indexes:
        - name: idx_inbound_time
          fields: [timestamp]
          type: btree

  relationships:
    - name: delivery_subscriber
      from: webhook_deliveries.subscriber_id
      to: webhook_subscribers.subscriber_id
      cardinality: many-to-one
      on_delete: cascade
      description: Each delivery belongs to one subscriber

  retention:
    webhook_subscribers:
      policy: indefinite
      cleanup: manual (operator deactivates or deletes)
    webhook_deliveries:
      policy: 7 days
      cleanup: automatic sweep
    webhook_inbound_log:
      policy: config.inbound.log_retention
      cleanup: automatic sweep

  backup:
    webhook_subscribers:
      frequency: daily
      format: JSON export of all active subscribers
      path: .weblisk/backups/webhook/subscribers_{ISO8601}.json
    webhook_deliveries:
      frequency: daily
      format: JSON export (last 24 hours)
      path: .weblisk/backups/webhook/deliveries_{ISO8601}.json
    webhook_inbound_log:
      backup: false
      reason: Transient log data, not critical for restore
```

---

## State Machine

```yaml
state_machine:
  agent:
    initial: created
    transitions:
      - from: created
        to: registered
        trigger: orchestrator_ack
        validates: agent_id assigned in response
      - from: registered
        to: active
        trigger: event_processing_started
        validates: inbound listener and retry sweep running
      - from: active
        to: degraded
        trigger: storage_error
        validates: delivery tracking or subscriber lookup failing
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: successful storage operation
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received (SIGTERM, system.shutdown, or API)
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in_flight deliveries = 0 OR drain timeout (30s) elapsed

  entity.WebhookDelivery:
    initial: pending
    transitions:
      - from: pending
        to: delivered
        trigger: http_2xx_response
        validates: response status code 200-299
        side_effect: record response_code, duration_ms, delivered_at
      - from: pending
        to: pending
        trigger: http_error_retryable
        validates: attempts < max_retries
        side_effect: increment attempts, compute next_retry with backoff
      - from: pending
        to: failed
        trigger: retries_exhausted
        validates: attempts >= max_retries
        side_effect: emit webhook.delivery.failed event
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults
  Pre-check:   Process has read access to environment
  Validates:   All config values within constraints
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/webhook/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE
  Backout:     Close partial connection

Step 4 — Validate Schema
  Action:      Verify webhook_subscribers, webhook_deliveries, webhook_inbound_log tables
  Pre-check:   Step 3 validated
  Validates:   Tables exist with correct schema and indexes
  On Fail:     Run migration → if fails EXIT with MIGRATION_FAILED
  Backout:     Reverse migration

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 6 — Subscribe to Events
  Action:      Subscribe to: webhook.received, webhook.send,
               system.shutdown, system.blueprint.changed
  Pre-check:   Step 5 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT
  Backout:     Unsubscribe all, deregister, close storage

Step 7 — Start Retry Sweep Timer
  Action:      Begin interval timer (every 60s)
  Pre-check:   Steps 1-6 validated
  Validates:   Timer starts
  On Fail:     Continue without retry sweep (manual retries only)
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9753, subscribers_active: N, pending_deliveries: N}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Webhooks
  Action:      Return 503 for new inbound/outbound requests
  Validates:   No new events accepted

Step 3 — Stop Retry Sweep
  Action:      Cancel sweep timer
  Validates:   Timer cancelled

Step 4 — Drain In-Flight Deliveries
  Action:      Wait for active HTTP sends to complete (up to 30s)
  Validates:   in_flight = 0
  On Timeout:  Mark in-flight as pending for retry on restart

Step 5 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges

Step 6 — Close Storage
  Action:      Close database connection

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, deliveries_sent, deliveries_pending}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - event_listener = running
      - retry_sweep = running
      - storage = connected
    response:
      status: healthy
      details: {subscribers_active, pending_deliveries, retry_queue_depth}

  degraded:
    conditions:
      - storage errors (but retrying)
      - high delivery failure rate (> 50%)
    response:
      status: degraded
      details: {reason, last_error, failure_rate}

  unhealthy:
    conditions:
      - storage unreachable after retries
      - event listener stopped
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

```
Step 1 — Validate new blueprint
Step 2 — Check migration requirements
Step 3 — Execute migration (pause processing, migrate, resume)
Step 4 — Reload configuration
Final:  Log lifecycle.version_updated {from, to}
```

---

## Implementation Notes

- **Separation of concerns**: The webhook blueprints define the API
  contract. This agent implements the background processing. The HTTP
  endpoints may live in the main server; the agent handles async work.
- **Collaboration with cron**: The retry sweep can be delegated
  to the cron agent for scheduling instead of running its own timer.
- **Signature verification**: Always verify on the raw bytes. JSON
  re-serialization may change field order and break signatures.
- **Subscriber deactivation**: If a subscriber fails N consecutive
  events (e.g. 3), consider auto-deactivating and notifying the
  subscriber owner.
- **Observability**: Expose delivery metrics (success rate, avg
  latency, failure rate) via the health endpoint.

---

## Triggers

```yaml
triggers:
  - name: inbound_received
    type: event
    topic: webhook.received
    description: Inbound webhook arrives from external source

  - name: outbound_send
    type: event
    topic: webhook.send
    description: Application emits event for outbound delivery

  - name: retry_sweep
    type: schedule
    interval: 60
    description: Every minute — retry failed deliveries

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "webhook"
    description: Self-update if webhook blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [process_inbound, send_event, register_subscriber,
             list_subscribers, delivery_status, deactivate_subscriber]
    description: Agent-to-agent and operator actions
```

---

## Actions

### process_inbound

Process an inbound webhook.

**Purpose:** Verify signature, route event to handler, log result.

**Input:** `{source: string, headers: object, body: string, raw_body: bytes}`

**Processing:**

```
1. Look up source configuration by URL path
2. Extract signature from configured header
3. Compute HMAC-SHA256 over raw_body using source secret
4. Constant-time compare signatures
   If mismatch → reject with SIGNATURE_INVALID
5. Parse JSON body
6. Extract event type
7. If event in source's allowed list (or list empty) → route to handler
   Else → log as filtered, return success
8. Log to webhook_inbound_log
9. Return result
```

**Output:** `{status: "success" | "rejected" | "filtered", delivery_id: string}`

**Errors:**

```yaml
errors:
  - code: SIGNATURE_INVALID
    condition: HMAC signature verification failed
    retryable: false
  - code: SOURCE_NOT_CONFIGURED
    condition: No configuration for inbound source
    retryable: false
  - code: PAYLOAD_TOO_LARGE
    condition: Body exceeds config.inbound.max_payload_size
    retryable: false
```

**Side Effects:** Writes to `webhook_inbound_log`. May send message to handler agent.

**Idempotency:** Inbound webhooks are processed at-least-once (caller should handle duplicates).

---

### send_event

Queue an outbound event for delivery.

**Purpose:** Fan out an application event to all matching subscribers.

**Input:** `{event: string, data: object}`

**Processing:**

```
1. Query webhook_subscribers WHERE active = true AND event IN events
2. For each matching subscriber:
   a. Build payload: {id, event, timestamp, data}
   b. Create WebhookDelivery record with status = pending
3. Return count of queued deliveries
4. (Async) For each delivery:
   a. Sign payload with subscriber secret (HMAC-SHA256)
   b. POST to subscriber URL with signature headers
   c. Record result in webhook_deliveries
```

**Output:** `{queued: int, delivery_ids: []string}`

**Errors:** `STORAGE_ERROR` (transient)

**Side Effects:** Writes to `webhook_deliveries`. HTTP POSTs to subscriber URLs.

---

### register_subscriber

Register a new outbound webhook subscriber.

**Purpose:** Add a URL to receive webhook events.

**Input:** `{url: string, events: []string, secret: string}`

**Processing:**

```
1. Validate URL is HTTPS
2. Validate events list is non-empty
3. Check for duplicate URL (idx_subscriber_url unique index)
4. Generate subscriber_id (UUID v7)
5. Insert into webhook_subscribers
6. Return subscriber metadata
```

**Output:** `{subscriber_id: string, active: true}`

**Errors:** `INVALID_INPUT` (non-HTTPS URL), `DUPLICATE_URL` (URL already registered)

**Side Effects:** Writes to `webhook_subscribers`.

**Idempotency:** Duplicate URL returns DUPLICATE_URL error.

**Manual Override:** Operator can register subscribers via CLI.

---

### list_subscribers

List registered subscribers.

**Purpose:** Query all webhook subscribers.

**Input:** `{active_only?: bool}` (default true)

**Output:** `{subscribers: WebhookSubscriber[]}`

**Side Effects:** None (read-only).

---

### delivery_status

Check delivery status.

**Purpose:** Query delivery records for a specific event or subscriber.

**Input:** `{delivery_id?: string, subscriber_id?: string, limit?: int}`

**Output:** `{deliveries: WebhookDelivery[]}`

**Errors:** `NOT_FOUND` if delivery_id does not exist.

**Side Effects:** None (read-only).

---

### deactivate_subscriber

Deactivate a subscriber.

**Purpose:** Stop delivering events to a subscriber without deleting records.

**Input:** `{subscriber_id: string}`

**Output:** `{deactivated: true, subscriber_id}`

**Errors:** `NOT_FOUND`

**Manual Override:** Operator-only action.

---

## Collaboration

```yaml
events_published:
  - topic: webhook.inbound.processed
    payload: {source, event_type, status}
    when: Inbound webhook processed

  - topic: webhook.outbound.delivered
    payload: {delivery_id, subscriber_id, event_type, duration_ms}
    when: Outbound delivery succeeded

  - topic: webhook.delivery.failed
    payload: {delivery_id, subscriber_id, error, attempts}
    when: All retries exhausted for an outbound delivery

  - topic: webhook.subscriber.deactivated
    payload: {subscriber_id, reason}
    when: Subscriber deactivated (manual or auto after consecutive failures)

events_subscribed:
  - topic: webhook.received
    payload: {source, headers, body, raw_body}
    action: Process inbound webhook

  - topic: webhook.send
    payload: {event, data}
    action: Fan out to matching subscribers

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "webhook"
    action: Self-update procedure

direct_messages:
  - target: variable (handler agent from inbound routing)
    action: variable (per source configuration)
    when: Inbound webhook routed to handler
    reason: Handler may require synchronous confirmation
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All webhook processing and retries are autonomous
  supervised:    Processing automatic; subscriber management requires operator
  manual-only:   All actions require operator invocation

overridable_behaviors:
  - behavior: automatic_retry
    default: enabled
    override: Set max_retries = 0 per subscriber or globally
    audit: logged

  - behavior: subscriber_auto_deactivation
    default: enabled (after 3 consecutive failures per subscriber)
    override: Set consecutive_failure_threshold = 0 to disable
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: register_subscriber
    description: Register a new webhook subscriber
    allowed: operator

  - action: deactivate_subscriber
    description: Deactivate a subscriber
    allowed: operator

  - action: retry_delivery
    description: Force retry a specific failed delivery
    allowed: operator

  - action: purge_deliveries
    description: Delete delivery records older than threshold
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Required
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT send webhooks to URLs not in the subscriber list
    - MUST NOT modify event payloads after creation
    - Outbound delivery rate bounded by subscriber count and retry config

  forbidden_actions:
    - MUST NOT accept inbound webhooks without signature verification
    - MUST NOT log subscriber secrets
    - MUST NOT register subscribers with non-HTTPS URLs
    - MUST NOT re-serialize JSON for signature verification (use raw bytes)

  resource_limits:
    memory: 256 MB (process limit)
    webhook_subscribers: 10000 max
    webhook_deliveries: governed by retention policy (7 days)
    inbound_payload: config.inbound.max_payload_size
    outbound_payload: config.outbound.max_payload_size
    concurrent_deliveries: 50 max parallel outbound requests
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: SIGNATURE_INVALID
      description: HMAC signature verification failed for inbound webhook
    - code: SOURCE_NOT_CONFIGURED
      description: No configuration for the inbound webhook source
    - code: PAYLOAD_TOO_LARGE
      description: Request body exceeds max_payload_size
    - code: INVALID_INPUT
      description: Missing required fields or invalid subscriber URL
    - code: DUPLICATE_URL
      description: Subscriber URL already registered
    - code: NOT_FOUND
      description: Referenced subscriber or delivery does not exist

  transient:
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Enter degraded state, retry on next cycle
    - code: DELIVERY_TIMEOUT
      description: Subscriber did not respond within config.outbound.timeout
      fallback: Schedule retry with backoff
    - code: DELIVERY_ERROR
      description: Subscriber returned non-2xx response
      fallback: Schedule retry with backoff
    - code: HANDLER_UNAVAILABLE
      description: Inbound handler agent not reachable
      fallback: Log event, return success to sender (best-effort routing)
```

---

## Observability

```yaml
custom_log_types:
  - log_type: webhook.inbound.received
    level: info
    when: Inbound webhook received
    fields: {source, event_type}

  - log_type: webhook.inbound.rejected
    level: warn
    when: Signature verification failed
    fields: {source, reason}

  - log_type: webhook.outbound.delivered
    level: info
    when: Outbound delivery succeeded
    fields: {delivery_id, subscriber_id, duration_ms}

  - log_type: webhook.outbound.failed
    level: warn
    when: Outbound delivery attempt failed
    fields: {delivery_id, error, attempt}

  - log_type: webhook.outbound.exhausted
    level: error
    when: All retries exhausted
    fields: {delivery_id, subscriber_id, total_attempts}

metrics:
  - name: wl_webhook_inbound_total
    type: counter
    labels: [source, status]
    description: Inbound webhooks by source and result

  - name: wl_webhook_outbound_total
    type: counter
    labels: [status]
    description: Outbound deliveries by result

  - name: wl_webhook_delivery_duration_seconds
    type: histogram
    labels: [subscriber_id]
    description: Per-delivery HTTP request duration

  - name: wl_webhook_retry_total
    type: counter
    description: Total retry attempts

  - name: wl_webhook_subscribers_active
    type: gauge
    description: Number of active subscribers

  - name: wl_webhook_pending_deliveries
    type: gauge
    description: Deliveries awaiting retry

alerts:
  - condition: Delivery failure rate > 50% in last hour
    severity: high
    routing: alerting agent

  - condition: Subscriber auto-deactivated
    severity: warn
    routing: alerting agent

  - condition: Storage errors for 3+ consecutive cycles
    severity: critical
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: http:receive
      resources: ["/webhooks/*"]
      description: Accept inbound webhook HTTP requests

    - capability: http:send
      resources: ["https://*"]
      description: POST outbound webhooks to subscriber URLs

    - capability: database:read
      resources: [webhook_subscribers, webhook_deliveries, webhook_inbound_log]
      description: Read own tables

    - capability: database:write
      resources: [webhook_subscribers, webhook_deliveries, webhook_inbound_log]
      description: Write own tables

    - capability: agent:message
      resources: ["*"]
      description: Route inbound events to handler agents

  data_sensitivity:
    - data: Subscriber secrets (HMAC keys)
      classification: critical
      handling: Stored encrypted, never logged, loaded into memory for signing only

    - data: Webhook payloads (event data)
      classification: medium
      handling: Logged as event type and size only, not full content

    - data: Subscriber URLs
      classification: low
      handling: Logged freely, used in delivery tracking

    - data: Inbound webhook bodies
      classification: medium
      handling: Verified on raw bytes, parsed payload not persisted

  access_control:
    - caller: Any registered agent
      actions: [send_event, delivery_status]

    - caller: Operator (auth token with operator role)
      actions: [process_inbound, send_event, register_subscriber,
                list_subscribers, delivery_status, deactivate_subscriber,
                retry_delivery, purge_deliveries]

    - caller: External (webhook sender with valid signature)
      actions: [process_inbound]
      note: Verified via HMAC signature, not agent auth token

    - caller: Unauthenticated
      actions: []
      note: All internal endpoints require valid token;
            inbound webhooks require valid signature
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Inbound webhook with valid signature
    action: process_inbound
    input:
      source: stripe
      headers: {X-Stripe-Signature: "sha256=valid"}
      body: '{"type": "payment.completed", "data": {}}'
      raw_body: '<bytes>'
    expected:
      status: success
      delivery_id: "<uuid-v7>"
    validates:
      - Signature verified
      - Event routed to handler
      - Logged in webhook_inbound_log

  - name: Outbound event to subscribers
    action: send_event
    input:
      event: order.placed
      data: {order_id: "ord-123", amount: 99.99}
    expected:
      queued: 2
      delivery_ids: ["<uuid>", "<uuid>"]
    validates:
      - Fan-out to all matching active subscribers
      - Delivery records created
      - HMAC signatures computed per subscriber secret

  - name: Register subscriber
    action: register_subscriber
    input:
      url: "https://hooks.example.com/events"
      events: ["order.placed", "order.shipped"]
      secret: "whsec_abc123"
    expected:
      subscriber_id: "<uuid-v7>"
      active: true
```

### Error Cases

```yaml
  - name: Inbound with invalid signature
    action: process_inbound
    input:
      source: stripe
      headers: {X-Stripe-Signature: "sha256=invalid"}
      body: '{"type": "payment.completed"}'
    expected_error: SIGNATURE_INVALID
    validates: Constant-time comparison rejects mismatch

  - name: Register subscriber with HTTP URL
    action: register_subscriber
    input: {url: "http://insecure.example.com", events: ["test"], secret: "s"}
    expected_error: INVALID_INPUT
    validates: HTTPS-only enforcement

  - name: Duplicate subscriber URL
    action: register_subscriber
    input: {url: "https://hooks.example.com/events", events: ["test"], secret: "s"}
    expected_error: DUPLICATE_URL
    validates: idx_subscriber_url unique constraint
```

### Edge Cases

```yaml
  - name: Delivery retry exhaustion
    trigger: retry_sweep
    condition: Subscriber returns 500 for 5 consecutive attempts
    expected: Delivery marked as failed, webhook.delivery.failed event published
    validates: Max retries enforced, subscriber not auto-deactivated until threshold

  - name: Subscriber auto-deactivation
    trigger: retry_sweep
    condition: 3 consecutive events all fail delivery
    expected: Subscriber deactivated, webhook.subscriber.deactivated published
    validates: Auto-deactivation threshold works

  - name: Inbound payload too large
    action: process_inbound
    condition: Body exceeds config.inbound.max_payload_size
    expected_error: PAYLOAD_TOO_LARGE
    validates: Size check before signature verification (avoid HMAC on huge bodies)

  - name: Concurrent outbound fan-out
    action: send_event
    condition: 100 active subscribers for this event type
    expected: Deliveries capped at concurrent_deliveries limit, rest queued
    validates: Concurrency constraint respected
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: unbounded

  inter_agent:
    protocol: message-bus-only
    direct_http: forbidden
    routing: by agent name
    reason: Message bus routes to healthy instances

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: not required — delivery records use optimistic locking
      leader: []
      follower: [inbound_processing, outbound_delivery, retry_sweep]
      promotion: n/a
    state_sharing:
      mechanism: shared sqlite database
      consistency_window: immediate (transactional)
      conflict_resolution: >
        Delivery records use status-based optimistic locking
        (pending → in_progress). Only one instance processes each
        delivery. Retry sweep uses SELECT FOR UPDATE semantics.

  event_handling:
    consumer_group: webhook
    delivery: one-per-group
    description: >
      Each webhook.received and webhook.send event delivered to
      one instance. Database ensures no duplicate processing.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same database. Schema migrations
      additive-only during shadow phase.
    consumer_groups:
      shadow_phase: "webhook@vN+1"
      after_cutover: "webhook"
```

---

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
