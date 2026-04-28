<!-- blueprint
type: agent
kind: infrastructure
name: alerting
version: 1.1.0
port: 9752
requires: [protocol/spec, protocol/types, architecture/agent, agents/email-send]
extends: [patterns/alerting, patterns/observability, patterns/storage, patterns/messaging, patterns/notification, patterns/scope, patterns/policy, patterns/safety, patterns/security, patterns/governance]
depends_on: [email-send]
platform: any
tier: free
-->

# Alerting Agent

Infrastructure agent responsible for receiving alert events from
the orchestrator, domain controllers, and other agents, then routing
notifications to the appropriate channels based on severity, source,
and subscriber preferences.

## Overview

The alerting agent is the notification hub of a Weblisk deployment.
It decouples the "something happened" event from the "tell someone
about it" delivery mechanism. Agents and domain controllers emit
structured alert events; the alerting agent decides who gets notified,
through which channel, and with what urgency.

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
        - name: HealthStatus
          fields_used: [status, details]
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
  - blueprint: agents/email-send
    version: ">=1.0.0 <2.0.0"
    bindings:
      actions:
        - name: send
          payload: {to, subject, body, priority}
        - name: send_raw
          payload: {to, subject, body, content_type}
    on_change:
      compatible: validate
      breaking: version-bump
      removed: degrade-email-channel

extends:
  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: metrics
          parameters: [gauge, counter, histogram]
        - behavior: alerts
          parameters: [condition, severity, routing]
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

  - pattern: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: publish
          parameters: [topic, payload, source]
        - behavior: subscribe
          parameters: [topic, handler, consumer_group]
        - behavior: dead-letter
          parameters: [max_retries, dlq_topic]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/notification
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: channel-dispatch
          parameters: [channel, payload, recipient]
    on_change:
      compatible: validate-and-adopt
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

depends_on:
  - agent: email-send
    reason: Delegates email notification delivery
    on_unavailable: degrade (skip email channel, continue webhook/slack)
```

---

## Configuration

```yaml
config:
  env:
    WL_ALERT_DEDUP_WINDOW:
      type: integer
      default: 300
      description: Deduplication window in seconds
    WL_ALERT_DEFAULT_CHANNEL:
      type: string
      default: log
      description: Default delivery channel when no route matches
    WL_ALERT_RETRY_MAX:
      type: integer
      default: 3
      description: Max delivery retry attempts
    WL_ALERT_RETRY_DELAY:
      type: integer
      default: 5000
      description: Initial retry delay in milliseconds
    WL_ALERT_HISTORY_TTL:
      type: integer
      default: 604800
      description: Alert history retention in seconds (7 days)
    WL_ALERT_BATCH_SIZE:
      type: integer
      default: 50
      description: Max alerts processed per batch
```

---

## Types

See [Alert Event Schema](#alert-event-schema) for the full inbound/outbound schemas.

```yaml
types:
  AlertEvent:
    fields:
      alert_id: { type: string, format: "alert-{ulid}", required: true }
      severity: { type: enum, values: [critical, high, medium, low, info], required: true }
      source: { type: AlertSource, required: true }
      message: { type: string, max_length: 1000, required: true }
      details: { type: object, required: false }
      timestamp: { type: datetime, format: ISO8601, required: true }
      fingerprint: { type: string, description: "Deduplication key", required: false }

  AlertSource:
    fields:
      type: { type: enum, values: [agent, domain, system], required: true }
      name: { type: string, required: true }
      domain: { type: string, required: false }

  AlertRecord:
    fields:
      alert_id: { type: string, required: true }
      status: { type: enum, values: [pending, delivered, failed, suppressed], required: true }
      channel: { type: string, required: true }
      delivered_at: { type: datetime, required: false }
      attempts: { type: integer, required: true }
      last_error: { type: string, required: false }
```

---

## Specification

### Blueprint Format

```yaml
name: alerting
version: 1.0.0
description: Notification routing and delivery

capabilities:
  - agent:message

config:
  channels:
    email:
      enabled: true
      agent: email-send          # delegate to email-send agent
    webhook:
      enabled: true
      url: https://hooks.example.com/weblisk
      secret: ${WL_ALERT_WEBHOOK_SECRET}
    slack:
      enabled: false
      webhook_url: ${WL_SLACK_WEBHOOK_URL}
  
  rules:
    - severity: critical
      channels: [email, slack, webhook]
      throttle: 0                # no throttle — deliver immediately
    - severity: high
      channels: [email, webhook]
      throttle: 300              # 5-minute dedup window
    - severity: medium
      channels: [webhook]
      throttle: 900              # 15-minute dedup window
    - severity: low
      channels: []               # log only, no notification
      throttle: 3600

  subscribers:
    - email: alice@example.com
      role: admin
      severities: [critical, high, medium]
    - email: bob@example.com
      role: user
      severities: [critical]
```

### Protocol Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/health` | Health check — returns agent status |
| POST | `/describe` | Returns agent capabilities and manifest |
| POST | `/task` | Receive and process an alert event |
| POST | `/message` | Receive messages from other agents |
| POST | `/governance` | Accept governance directives |

---

## Alert Event Schema

### Inbound Alert

The alert event is delivered to the agent's `/task` endpoint.

```json
{
  "task_id": "task-a1b2c3",
  "action": "alert",
  "payload": {
    "alert_id": "alert-d4e5f6",
    "severity": "critical",
    "source": {
      "type": "agent",
      "name": "uptime-checker",
      "domain": "health"
    },
    "title": "Site unreachable",
    "message": "GET https://example.com returned 503 after 3 retries",
    "context": {
      "url": "https://example.com",
      "status_code": 503,
      "check_time": 1712160000,
      "consecutive_failures": 3
    },
    "timestamp": 1712160000
  }
}
```

### Alert Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| alert_id | string | yes | Unique ID for deduplication |
| severity | string | yes | `critical`, `high`, `medium`, `low` |
| source.type | string | yes | `agent`, `domain`, `orchestrator`, `system` |
| source.name | string | yes | Name of the emitting component |
| source.domain | string | no | Domain if source is a domain agent |
| title | string | yes | Short summary (≤ 120 chars) |
| message | string | yes | Detailed description |
| context | object | no | Structured data specific to the alert type |
| timestamp | int64 | yes | Unix epoch seconds |

### Severity Levels

| Level | Meaning | Examples |
|-------|---------|---------|
| critical | Service down or data loss risk | Site unreachable, agent crashed, storage full |
| high | Degraded service or failed workflow | Workflow failed, agent degraded, high error rate |
| medium | Notable event requiring attention | Approval backlog, federation peer disconnect |
| low | Informational | Agent registered, strategy completed, routine audit |

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
        trigger: event_subscriptions_established
        validates: all subscriptions acknowledged
      - from: active
        to: degraded
        trigger: channel_unavailable
        validates: at least one delivery channel failed
      - from: degraded
        to: active
        trigger: channel_recovered
        validates: all configured channels responding
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

  entity.AlertEvent:
    initial: received
    transitions:
      - from: received
        to: validated
        trigger: schema_validation_passed
        validates: all required fields present and typed correctly
      - from: received
        to: rejected
        trigger: schema_validation_failed
        validates: validation error logged
      - from: validated
        to: throttled
        trigger: dedup_hash_match_within_window
        validates: throttle window active for this hash
        side_effect: increment suppressed_count
      - from: validated
        to: routing
        trigger: dedup_check_passed
        validates: hash not seen or throttle window expired
      - from: routing
        to: delivered
        trigger: all_channels_dispatched
        validates: at least one channel succeeded
        side_effect: write to alert_history
      - from: routing
        to: partially_delivered
        trigger: some_channels_failed
        validates: at least one channel succeeded, others failed
        side_effect: write to alert_history with partial status
      - from: routing
        to: delivery_failed
        trigger: all_channels_failed
        validates: no channel succeeded
        side_effect: write to alert_history with failed status
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Pre-check:   Process has read access to environment
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID — log which keys failed
  Backout:     None (process never started)

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/alerting/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine, verify alert_history table
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE
  Backout:     Close any partial connection

Step 4 — Validate Schema
  Action:      Compare storage tables against Types block
  Pre-check:   Step 3 validated
  Validates:   All tables exist, columns match, indexes present
  On Fail:     Run migration → if fails EXIT with MIGRATION_FAILED
  Backout:     Reverse migration steps

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 6 — Subscribe to Events
  Action:      Subscribe to: alert.*, system.agent.registered,
               system.agent.deregistered, system.shutdown,
               system.blueprint.changed
  Pre-check:   Step 5 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT
  Backout:     Unsubscribe all, deregister, close storage

Step 7 — Verify Delivery Channels
  Action:      Test connectivity to each enabled channel
  Pre-check:   Configuration loaded with channel settings
  Validates:   At least one channel is reachable
  On Fail:     Enter degraded state (continue with available channels)
  Backout:     None (degraded is acceptable)

Step 8 — Initialize Deduplication Cache
  Action:      Load in-memory dedup hash table, prune expired entries
  Pre-check:   Storage connected
  Validates:   Cache loaded or empty (cold start)
  On Fail:     Continue with empty cache (duplicates possible briefly)
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9752, channels_active, dedup_entries_loaded}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown event, or API call
  Validates:   Signal is recognized
  agent_state → retiring

Step 2 — Stop Accepting Alerts
  Action:      Return 503 for new alert submissions
  Validates:   No new alerts accepted after this point

Step 3 — Drain In-Flight Deliveries
  Action:      Wait for pending channel deliveries (up to 30s)
  Validates:   in_flight count = 0
  On Timeout:  Log undelivered alerts, mark as delivery_failed

Step 4 — Flush Dedup Cache
  Action:      Persist dedup entries to storage for next startup
  Validates:   Entries written or best-effort logged

Step 5 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges removal

Step 6 — Close Storage
  Action:      Close database connection
  Validates:   Connection closed cleanly

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, alerts_processed, in_flight_drained}
  agent_state → retired
  Exit process
```

### Health

Reported via `GET /v1/health`:

```yaml
health:
  healthy:
    conditions:
      - event_listener = running
      - storage = connected
      - at least one delivery channel = available
    response:
      status: healthy
      details: {channels_active, alerts_24h, throttled_24h, storage_status}

  degraded:
    conditions:
      - one or more channels unavailable
      - storage errors (but retrying)
    response:
      status: degraded
      details: {reason, unavailable_channels, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
      - all delivery channels unavailable
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "alerting"`:

```
Step 1 — Validate New Blueprint
  Action:      Parse new blueprint, verify against schema
  Validates:   Blueprint parses, version is newer
  On Fail:     Log warning, continue with current version

Step 2 — Check Migration
  Action:      Compare Types block against current storage schema
  Validates:   Diff computed
  On Fail:     Log error, continue with current version

Step 3 — Execute Migration (if needed)
  Action:      Pause alert processing → run migration → resume
  Pre-check:   No in-flight deliveries
  Validates:   Migration succeeds, schema matches new Types
  On Fail:     ROLLBACK → resume with old version

Step 4 — Reload Configuration
  Action:      Apply new config values (channels, rules, thresholds)
  Validates:   All values within constraints
  On Fail:     Revert to previous config

Final:
  Log: lifecycle.version_updated {from, to, migration_steps}
```

---

## Triggers

```yaml
triggers:
  - name: alert_event
    type: event
    topic: alert.*
    description: Receive alert events from any agent or domain controller

  - name: agent_registered
    type: event
    topic: system.agent.registered
    description: Update known agent list for source validation

  - name: agent_deregistered
    type: event
    topic: system.agent.deregistered
    description: Note agent removal for source context

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "alerting"
    description: Self-update if alerting blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [alert, list_alerts, get_stats, configure_rule]
    description: Agent-to-agent and operator actions
```

---

## Actions

### alert

Process an incoming alert event.

**Purpose:** Validate, deduplicate, route, and deliver an alert notification.

**Input:** `{alert_id, severity, source, title, message, context?, timestamp}`
— references `AlertEvent` type (see Alert Event Schema below).

**Processing:**

```
1. Validate input against AlertEvent schema:
   a. alert_id: non-empty string
   b. severity: one of [critical, high, medium, low]
   c. source.type: one of [agent, domain, orchestrator, system]
   d. title: non-empty, max 120 chars
   e. timestamp: valid epoch seconds
2. Deduplicate:
   a. hash = sha256(source.name + title + severity)
   b. Check dedup cache for hash within throttle window
   c. If found → increment suppressed_count, return throttled result
3. Match routing rules by severity
4. Resolve subscribers by severity preference
5. Dispatch to each enabled channel (async, non-blocking)
6. Write alert to alert_history storage
7. Return delivery summary
```

**Output:** `{alert_id: string, delivered_to: []string, throttled: bool, recipients: int}`

**Errors:**

```yaml
errors:
  - code: INVALID_ALERT
    condition: Alert payload fails schema validation
    retryable: false
  - code: STORAGE_ERROR
    condition: Failed to write alert history
    retryable: true
  - code: ALL_CHANNELS_FAILED
    condition: Every delivery channel returned an error
    retryable: true
```

**Side Effects:** Writes to `alert_history`. Sends messages to email-send agent,
webhook URLs, and Slack webhooks. Updates dedup cache.

**Idempotency:** Same `alert_id` within throttle window is deduplicated.

---

### list_alerts

Query alert history with filtering.

**Purpose:** Retrieve stored alerts for admin review.

**Input:** `{severity?: string, source_name?: string, since?: int64, limit?: int, offset?: int}`

**Processing:**

```
1. Validate filter parameters
2. Query alert_history with filters, ORDER BY timestamp DESC
3. Apply limit (default 100, max 1000) and offset
4. Return alert list with total count
```

**Output:** `{alerts: AlertRecord[], total: int}`

**Errors:** `INVALID_INPUT` if invalid severity value.

**Side Effects:** None (read-only).

---

### get_stats

Get alert statistics for a time period.

**Purpose:** Aggregate alert counts by severity, source, and delivery status.

**Input:** `{period?: string}` — default "24h", accepts "1h", "24h", "7d", "30d"

**Processing:**

```
1. Parse period into timestamp range
2. Query alert_history with aggregate counts
3. Return statistics breakdown
```

**Output:** `{period, total, by_severity, by_source, throttled, delivery_failures}`

**Errors:** `INVALID_INPUT` if invalid period.

**Side Effects:** None (read-only).

---

### configure_rule

Update a routing rule.

**Purpose:** Modify severity-to-channel mapping or throttle window.

**Input:** `{severity: string, channels?: []string, throttle?: int}`

**Processing:**

```
1. Validate severity is a known level
2. Validate channels are configured and enabled
3. Update rule in routing configuration
4. Log: action.completed {action: "configure_rule", severity}
```

**Output:** `{updated: true, rule: AlertRule}`

**Errors:** `INVALID_INPUT`, `CHANNEL_NOT_CONFIGURED`

**Side Effects:** Updates in-memory routing rules.

**Manual Override:** Operator-only action.

---

## Execute Workflow

The alerting agent processes alerts as they arrive (event-driven, no tick loop):

```
Phase 1 — Receive Alert
  Source:    Event bus (alert.* topic) or direct message (action: alert)
  Action:    Parse and validate AlertEvent payload
  Decision:  Valid → Phase 2. Invalid → reject with INVALID_ALERT

Phase 2 — Deduplicate
  Query:     Check dedup cache for sha256(source.name + title + severity)
  Decision:  Hash exists within throttle window → return throttled result
             Hash expired or new → proceed to Phase 3
  Metric:    alerting_throttled_total (if throttled)

Phase 3 — Route
  Query:     Match severity against routing rules
  Result:    List of channels and subscriber recipients
  Decision:  No channels configured for severity → log-only, skip delivery

Phase 4 — Deliver (async, parallel per channel)
  For each channel:
    Email:   Send message to email-send agent (see Delivery Channels below)
    Webhook: POST with HMAC-SHA256 signature, retry up to 3x
    Slack:   POST Block Kit payload to webhook URL
  Metric:    alerting_delivered_total per channel

Phase 5 — Record
  Write:     Insert into alert_history table
  Fields:    alert_id, severity, source, channels_delivered, delivery_status
  Metric:    alerting_received_total

Phase 6 — Cleanup (every 10 minutes)
  Action:    Prune expired entries from dedup cache
  Query:     DELETE from dedup cache WHERE first_seen < (now - max_throttle_window)
```

---

## Routing Engine

### Processing Pipeline

```
1. Receive alert event
2. Validate alert schema
3. Deduplicate:
   a. Hash: sha256(source.name + title + severity)
   b. If hash seen within throttle window → discard (log "throttled")
   c. If new → proceed
4. Match routing rules:
   a. Find the rule matching alert.severity
   b. Get channel list from rule
5. Resolve subscribers:
   a. Filter subscribers by severity preference
   b. Build per-channel recipient lists
6. Dispatch to each enabled channel
7. Store alert in alert history
8. Return task result
```

### Deduplication

The throttle window prevents alert storms. If the same alert (by
hash) fires repeatedly, only the first notification is delivered
within the throttle window. Subsequent occurrences are counted and
logged.

```json
{
  "hash": "abc123...",
  "first_seen": 1712160000,
  "last_seen": 1712160300,
  "count": 15,
  "delivered": true,
  "delivery_time": 1712160000
}
```

When the throttle window expires and the alert fires again, a new
notification is sent that includes the suppressed count:

```
"Site unreachable — 15 occurrences in the last 5 minutes"
```

---

## Delivery Channels

### Email Channel

Delegates to the `email-send` infrastructure agent via the
`agent:message` capability.

**Message to email-send:**
```json
{
  "action": "send",
  "payload": {
    "to": ["alice@example.com"],
    "subject": "[CRITICAL] Site unreachable",
    "body": "GET https://example.com returned 503 after 3 retries.\n\nSource: uptime-checker (health)\nTime: 2026-04-25 10:00:00 UTC\nConsecutive failures: 3",
    "priority": "high"
  }
}
```

**Email formatting rules:**
- Subject prefix: `[SEVERITY]` in uppercase
- Body: plain text, includes title, message, source, time, context
- Critical alerts: include `X-Priority: 1` header

### Webhook Channel

HTTP POST to a configured URL with HMAC-SHA256 signature.

**Request:**
```http
POST https://hooks.example.com/weblisk
Content-Type: application/json
X-Weblisk-Signature: sha256=<hmac>
X-Weblisk-Event: alert
X-Weblisk-Delivery: <uuid>

{
  "alert_id": "alert-d4e5f6",
  "severity": "critical",
  "source": "uptime-checker",
  "title": "Site unreachable",
  "message": "GET https://example.com returned 503 after 3 retries",
  "context": {...},
  "timestamp": 1712160000
}
```

**Signature computation:**
```
signature = HMAC-SHA256(secret, request_body)
header = "sha256=" + hex(signature)
```

**Delivery rules:**
- Timeout: 10 seconds
- Retry: 3 attempts with exponential backoff (1s, 4s, 16s)
- If all retries fail → log delivery failure, do not re-queue

### Slack Channel

HTTP POST to a Slack incoming webhook URL.

**Payload:**
```json
{
  "text": "🔴 *CRITICAL* — Site unreachable",
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "🔴 CRITICAL Alert"}
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Site unreachable*\nGET https://example.com returned 503 after 3 retries\n\n*Source:* uptime-checker (health)\n*Time:* 2026-04-25 10:00:00 UTC"
      }
    }
  ]
}
```

**Severity emoji mapping:**
- critical: 🔴
- high: 🟠
- medium: 🟡
- low: 🔵

---

## Alert History

### Storage

Alerts are stored for querying via the admin API and CLI.

| Field | Type | Description |
|-------|------|-------------|
| alert_id | string | Unique alert ID |
| severity | string | Alert severity |
| source_type | string | Source type |
| source_name | string | Source name |
| title | string | Alert title |
| message | string | Alert message |
| context | json | Alert context |
| channels_delivered | []string | Channels that received the alert |
| delivery_status | map | Per-channel delivery result |
| throttled | bool | Whether this was a throttled duplicate |
| timestamp | int64 | Alert timestamp |
| processed_at | int64 | When the alerting agent processed it |

### Retention

- Default retention: 30 days
- Critical alerts: 90 days
- Configurable via `config.retention_days`

### Query API

The admin API provides alert querying:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/admin/alerts` | List alerts with filtering |
| GET | `/v1/admin/alerts/:id` | Get alert detail |
| GET | `/v1/admin/alerts/stats` | Alert statistics |

**Stats response:**
```json
{
  "period": "24h",
  "total": 45,
  "by_severity": {
    "critical": 2,
    "high": 8,
    "medium": 20,
    "low": 15
  },
  "by_source": {
    "uptime-checker": 12,
    "seo-analyzer": 8,
    "perf-auditor": 5
  },
  "throttled": 30,
  "delivery_failures": 1
}
```

---

## Alert Sources

### Built-in Alert Triggers

The following events generate alerts automatically:

| Source | Severity | Title | Trigger |
|--------|----------|-------|---------|
| orchestrator | critical | Agent offline | Agent health check fails 3 consecutive times |
| orchestrator | high | Agent degraded | Agent health check returns degraded status |
| orchestrator | low | Agent registered | New agent completes registration |
| orchestrator | medium | Approval backlog | > 20 pending recommendations for > 1 hour |
| domain | high | Workflow failed | Workflow execution fails |
| domain | medium | Domain degraded | Required agent unavailable |
| uptime-checker | critical | Site unreachable | HTTP check fails after retries |
| perf-auditor | high | Performance regression | Page load time exceeds threshold |
| federation | medium | Peer disconnected | Federation peer unreachable |
| federation | low | Peer request | New federation peering request |

### Custom Alerts

Any agent can emit a custom alert by sending a message to the
alerting agent:

```json
{
  "action": "alert",
  "payload": {
    "severity": "medium",
    "title": "Custom event",
    "message": "Application-specific alert details"
  }
}
```

---

## Task Result

The alerting agent returns a task result summarizing delivery:

```json
{
  "task_id": "task-a1b2c3",
  "status": "completed",
  "output": {
    "alert_id": "alert-d4e5f6",
    "delivered_to": ["email", "slack"],
    "throttled": false,
    "recipients": 2
  }
}
```

If the alert was throttled:
```json
{
  "task_id": "task-a1b2c3",
  "status": "completed",
  "output": {
    "alert_id": "alert-d4e5f6",
    "throttled": true,
    "suppressed_count": 15,
    "next_delivery_eligible": 1712160600
  }
}
```

---

## Collaboration

```yaml
events_published:
  - topic: alerting.alert.received
    payload: {alert_id, severity, source_name, title}
    when: New alert passes schema validation

  - topic: alerting.alert.delivered
    payload: {alert_id, channels, recipients}
    when: Alert successfully delivered to at least one channel

  - topic: alerting.alert.throttled
    payload: {alert_id, hash, suppressed_count}
    when: Duplicate alert suppressed within throttle window

  - topic: alerting.alert.delivery_failed
    payload: {alert_id, channels_failed, error}
    when: All delivery channels failed for an alert

  - topic: alerting.channel.degraded
    payload: {channel, error, since}
    when: A delivery channel becomes unreachable

  - topic: alerting.channel.recovered
    payload: {channel, downtime_seconds}
    when: A previously degraded channel recovers

events_subscribed:
  - topic: alert.*
    payload: {alert_id, severity, source, title, message, context, timestamp}
    action: Process alert through routing engine

  - topic: system.agent.registered
    payload: {agent_name, manifest}
    action: Update known agent list for source validation

  - topic: system.agent.deregistered
    payload: {agent_name}
    action: Note agent removal

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "alerting"
    action: Self-update procedure

direct_messages:
  - target: email-send
    action: send
    when: Alert routed to email channel
    reason: Email delivery requires synchronous queuing confirmation
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All alert routing and delivery is autonomous
  supervised:    Alert processing automatic; rule changes require operator
  manual-only:   All actions require operator invocation

overridable_behaviors:
  - behavior: automatic_throttling
    default: enabled
    override: Set throttle = 0 for a severity level
    audit: logged

  - behavior: channel_dispatch
    default: enabled
    override: Disable specific channels via configure_rule
    audit: logged

  - behavior: alert_history_cleanup
    default: enabled
    override: Set config.retention_days = 0
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: configure_rule
    description: Update routing rules for a severity level
    allowed: operator

  - action: purge_history
    description: Delete alert history older than threshold
    allowed: operator

  - action: test_channel
    description: Send a test alert through a specific channel
    allowed: operator

  - action: disable_channel
    description: Temporarily disable a delivery channel
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Required — operator must provide reason
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT modify data owned by other agents
    - MUST NOT send notifications to recipients not in the subscriber list
    - MUST NOT deliver alerts for severity levels with empty channel lists
    - Delivery rate bounded by per-channel rate limits

  forbidden_actions:
    - MUST NOT execute arbitrary code in alert payloads
    - MUST NOT log full webhook secrets or API keys
    - MUST NOT bypass deduplication for any alert source
    - MUST NOT block on delivery — all channel dispatches are async

  resource_limits:
    memory: 256 MB (process limit)
    alert_history_rows: governed by config.retention_days TTL
    dedup_cache: 100000 entries max (LRU eviction)
    outbound_per_minute: sum of per-channel rate limits
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_ALERT
      description: Alert payload fails schema validation (missing fields, bad types)
    - code: INVALID_INPUT
      description: Action input fails validation
    - code: CHANNEL_NOT_CONFIGURED
      description: Referenced channel not in configuration
    - code: INVALID_SEVERITY
      description: Severity level not in [critical, high, medium, low]

  transient:
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Continue delivery, retry history write next cycle
    - code: EMAIL_CHANNEL_ERROR
      description: email-send agent unavailable or returned error
      fallback: Skip email, attempt other channels
    - code: WEBHOOK_DELIVERY_ERROR
      description: Webhook POST failed or timed out
      fallback: Retry up to 3x with exponential backoff
    - code: SLACK_DELIVERY_ERROR
      description: Slack webhook POST failed
      fallback: Retry up to 3x with exponential backoff
    - code: ALL_CHANNELS_FAILED
      description: Every configured channel failed for this alert
      fallback: Log error, alert stored in history as delivery_failed
```

---

## Implementation Notes

- The alerting agent MUST NOT block on delivery — use async dispatch
  for channels and return the task result immediately
- Webhook secrets MUST be loaded from environment variables, never
  hardcoded in configuration
- The deduplication hash table should be pruned periodically (every
  10 minutes) to remove expired entries
- If the email-send agent is unavailable, the alerting agent should
  log the failure and attempt webhook/Slack delivery (graceful
  degradation)
- Alert history writes should be async — a failed history write
  MUST NOT prevent notification delivery

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| alerting_received_total | counter | Alerts received by severity |
| alerting_delivered_total | counter | Notifications delivered by channel and severity |
| alerting_throttled_total | counter | Alerts throttled (deduplicated) |
| alerting_delivery_failed_total | counter | Failed deliveries by channel |
| alerting_delivery_duration_seconds | histogram | Time to deliver per channel |
| alerting_active_rules | gauge | Number of active routing rules |
| alerting_history_size | gauge | Number of alerts in history store |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["email-send"]
      description: Send email delivery requests to email-send agent

    - capability: http:send
      resources: ["https://*"]
      description: POST to webhook and Slack URLs

    - capability: database:read
      resources: [alert_history, dedup_cache]
      description: Read own tables

    - capability: database:write
      resources: [alert_history, dedup_cache]
      description: Write own tables

  data_sensitivity:
    - data: Alert payloads (title, message, context)
      classification: medium
      handling: Stored encrypted at rest, context logged as summary only

    - data: Webhook secrets
      classification: critical
      handling: Loaded from environment variables, never logged or stored in DB

    - data: Subscriber email addresses
      classification: medium
      handling: Stored in config, not logged in alert history

    - data: Alert metadata (severity, source, timestamp)
      classification: low
      handling: Logged freely, included in metrics labels

  access_control:
    - caller: Any registered agent
      actions: [alert]

    - caller: Operator (auth token with operator role)
      actions: [alert, list_alerts, get_stats, configure_rule,
                purge_history, test_channel, disable_channel]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Critical alert delivered to all channels
    action: alert
    input:
      alert_id: alert-test-001
      severity: critical
      source: {type: agent, name: uptime-checker, domain: health}
      title: Site unreachable
      message: "GET https://example.com returned 503"
      timestamp: 1712160000
    expected:
      delivered_to: [email, webhook, slack]
      throttled: false
      recipients: 2
    validates:
      - AlertEvent validated and routed
      - All channels for critical severity dispatched
      - Alert written to alert_history

  - name: Low severity alert logged only
    action: alert
    input:
      alert_id: alert-test-002
      severity: low
      source: {type: system, name: orchestrator}
      title: Agent registered
      message: "Agent email-send registered successfully"
      timestamp: 1712160100
    expected:
      delivered_to: []
      throttled: false
    validates:
      - Low severity routes to empty channel list
      - Alert still written to history

  - name: List alerts with severity filter
    action: list_alerts
    input: {severity: critical, limit: 10}
    expected: {alerts: [...], total: N}
    validates:
      - Filtering by severity works
      - Results ordered by timestamp DESC
```

### Error Cases

```yaml
  - name: Invalid alert missing severity
    action: alert
    input: {alert_id: bad-001, title: "Test", message: "No severity"}
    expected_error: INVALID_ALERT
    validates: Schema validation catches missing required field

  - name: Invalid severity value
    action: alert
    input:
      alert_id: bad-002
      severity: urgent
      source: {type: agent, name: test}
      title: "Test"
      message: "Bad severity"
      timestamp: 1712160000
    expected_error: INVALID_ALERT
    validates: Severity enum validation

  - name: Configure rule with unknown channel
    action: configure_rule
    input: {severity: high, channels: [email, telegram]}
    expected_error: CHANNEL_NOT_CONFIGURED
    validates: Channel validation against config
```

### Edge Cases

```yaml
  - name: Duplicate alert within throttle window
    action: alert
    input:
      alert_id: alert-dup-001
      severity: critical
      source: {type: agent, name: uptime-checker}
      title: Site unreachable
      message: "Same alert fired again"
      timestamp: 1712160060
    condition: Same source+title+severity fired 60s ago (within 0s throttle)
    expected: {throttled: false}
    validates: Critical alerts have throttle=0, always delivered

  - name: Email channel unavailable
    action: alert
    input:
      alert_id: alert-degrade-001
      severity: high
      source: {type: agent, name: perf-auditor}
      title: Performance regression
      message: "Page load > 5s"
      timestamp: 1712160200
    condition: email-send agent is offline
    expected:
      delivered_to: [webhook]
      throttled: false
    validates: Graceful degradation — other channels still deliver

  - name: All channels failed
    action: alert
    condition: email-send offline, webhook URL unreachable, Slack disabled
    expected: Alert stored in history with delivery_failed status
    validates: Alert not lost, delivery_failed state recorded

  - name: Throttle window expiry includes suppressed count
    action: alert
    condition: 15 duplicate alerts suppressed, throttle window expires
    expected: Next delivery includes "15 occurrences in the last N minutes"
    validates: Suppressed count aggregated and reported
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
    routing: by agent name, never by instance address
    reason: >
      The message bus resolves agent names to healthy instances.
      During blue-green deploys, the bus handles traffic shifting.

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: not required — all instances can process independently
      leader: [dedup_cache_cleanup]
      follower: [alert_processing, delivery]
      promotion: any instance handles cleanup if no recent cleanup recorded
    state_sharing:
      mechanism: shared sqlite database (alert_history)
      consistency_window: eventual (dedup cache is per-instance)
      conflict_resolution: >
        Each instance maintains its own dedup cache. In rare cases,
        a duplicate may be delivered if two instances receive the same
        alert simultaneously. This is acceptable — at-least-once delivery.

  event_handling:
    consumer_group: alerting
    delivery: one-per-group
    description: >
      Bus delivers each alert event to ONE instance in the "alerting"
      consumer group. Prevents duplicate processing.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same alert_history database.
      Schema migrations are additive-only during shadow phase.
    consumer_groups:
      shadow_phase: "alerting@vN+1" (separate group, receives copies)
      after_cutover: "alerting" (takes over primary group)
```

---

## Verification Checklist

- [ ] Agent registers with orchestrator and receives WLT token
- [ ] Alert events are validated against schema
- [ ] Routing rules match alerts to correct channels by severity
- [ ] Deduplication prevents duplicate notifications within throttle window
- [ ] Throttled alerts include suppressed count on next delivery
- [ ] Email channel delegates to email-send agent correctly
- [ ] Webhook channel includes HMAC-SHA256 signature
- [ ] Webhook retries 3 times with exponential backoff on failure
- [ ] Slack channel sends Block Kit formatted messages
- [ ] Alert history is stored and queryable via admin API
- [ ] Stats endpoint returns correct counts by severity and source
- [ ] Custom alerts from any agent are accepted and routed
- [ ] Graceful degradation when email-send agent is unavailable
- [ ] Metrics emit for received, delivered, throttled, and failed alerts
- [ ] Health endpoint returns agent status

Port: 9752
