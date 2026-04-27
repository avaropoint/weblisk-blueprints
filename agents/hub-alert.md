<!-- blueprint
type: agent
kind: infrastructure
name: hub-alert
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/messaging, patterns/notification, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/hub, agents/alerting]
platform: any
tier: free
port: 9774
-->

# Hub Alert Agent

Monitors the hub network for behavioral changes, trust violations,
listing anomalies, and federation events. Routes hub-specific alerts
to operators and affected collaborators.

## Overview

The hub-alert agent is the notification layer for hub network events.
While the general alerting agent handles infrastructure-level
notifications (agent down, disk full), the hub-alert agent handles
**network-level** events: behavioral changes in published capabilities,
signature verification failures, SLA violations, listing suspensions,
and collaborator notifications.

Hub-alert works closely with hub-verify (which detects issues) and
hub-metrics (which detects SLA breaches). It decides who to notify,
how urgently, and through which channels.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["alert_rules", "collaborator_registry", "alert_history"]},
    {"name": "database:write", "resources": ["alert_history"]}
  ],
  "inputs": [
    {"name": "hub_event", "type": "json", "description": "Network event requiring notification"}
  ],
  "outputs": [
    {"name": "alert_result", "type": "json", "description": "Notification delivery status"}
  ],
  "collaborators": ["alerting", "hub-verify", "hub-metrics"]
}
```

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
      types:
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: MessageEnvelope
          fields_used: [from, to, action, payload, trace_id]
        - name: HealthResponse
          fields_used: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
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

  - blueprint: architecture/hub
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ListingEntry
          fields_used: [listing_id, provider, capability, tier, metrics]
        - name: BehavioralChange
          fields_used: [listing_id, level, previous_version, new_version, change_summary]
        - name: CollaboratorInfo
          fields_used: [hub_name, federation_url, contact]
      events:
        - topic: hub.behavioral.change
          fields_used: [listing_id, level, details]
        - topic: hub.verification.failure
          fields_used: [listing_id, provider, reason]
        - topic: hub.sla.breach
          fields_used: [listing_id, metric, threshold, actual]
        - topic: hub.listing.suspended
          fields_used: [listing_id, reason]
        - topic: hub.peer.revoked
          fields_used: [hub_name, reason]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: agents/alerting
    version: ">=1.0.0 <2.0.0"
    bindings:
      actions:
        - name: send-notification
          parameters: [recipient, channel, severity, subject, body]
        - name: send-batch
          parameters: [notifications]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

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
          parameters: [engine, tables, indexes]
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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/notification
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: channel-routing
          parameters: [severity, channel, urgency]
        - behavior: batching
          parameters: [batch_window, max_batch_size]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: token-validation
          parameters: [issuer, audience, claims]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: reconciliation
          parameters: [on_change, self-validation, version-bump]
    on_change:
      compatible: validate
      breaking: halt-and-reconcile
      removed: halt-immediately

depends_on: [hub-verify, hub-metrics]
  # Runtime dependency on hub-verify (source of verification events)
  # and hub-metrics (source of SLA breach events). Hub-alert degrades
  # gracefully if either is unavailable — queues alerts until recovery.
```

---

## Configuration

```yaml
config:
  dedup_window:
    type: int
    default: 3600
    env: WL_HUB_ALERT_DEDUP_WINDOW
    min: 60
    max: 86400
    unit: seconds
    description: Suppress duplicate alerts for same listing + event type within this window

  max_batch_size:
    type: int
    default: 50
    env: WL_HUB_ALERT_MAX_BATCH
    min: 1
    max: 500
    description: Maximum notifications per batch delivery to alerting agent

  notification_timeout:
    type: int
    default: 30
    env: WL_HUB_ALERT_NOTIFY_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Timeout for individual notification delivery

  federation_notify_timeout:
    type: int
    default: 15
    env: WL_HUB_ALERT_FED_TIMEOUT
    min: 5
    max: 60
    unit: seconds
    description: Timeout for cross-hub federation notification delivery

  flapping_threshold:
    type: int
    default: 3
    env: WL_HUB_ALERT_FLAP_THRESHOLD
    min: 2
    max: 20
    description: State changes within dedup_window to trigger flapping consolidation

  mute_max_duration:
    type: int
    default: 86400
    env: WL_HUB_ALERT_MUTE_MAX
    min: 300
    max: 604800
    unit: seconds
    description: Maximum mute duration for a listing

  retry_max:
    type: int
    default: 3
    env: WL_HUB_ALERT_RETRY_MAX
    min: 0
    max: 10
    description: Retry attempts for failed notification delivery

  history_retention:
    type: int
    default: 2592000
    env: WL_HUB_ALERT_HISTORY_RETENTION
    min: 86400
    unit: seconds
    description: Alert history retention period (default 30 days)
```

---

## Types

```yaml
types:
  HubAlert:
    description: A hub network alert record
    fields:
      alert_id:
        type: string
        format: uuid-v7
        description: Unique alert identifier
      listing_id:
        type: string
        description: Affected listing identifier
      event_type:
        type: string
        enum: [behavioral_change, verification_failure, sla_breach,
               listing_suspended, peer_revoked, marketplace_event]
        description: Category of hub event
      severity:
        type: string
        enum: [info, warning, critical]
        description: Alert severity level
      level:
        type: string
        enum: [BENIGN, NOTABLE, BREAKING, CRITICAL]
        optional: true
        description: Behavioral change level (when event_type = behavioral_change)
      payload:
        type: object
        description: Event-specific details
      recipients:
        type: array
        items: string
        description: List of notification targets (hub names or operator IDs)
      channels:
        type: array
        items: string
        description: Delivery channels used
      status:
        type: string
        enum: [pending, delivering, delivered, failed, suppressed]
        description: Delivery status
      suppression_reason:
        type: string
        optional: true
        description: Why alert was suppressed (dedup, muted, maintenance)
      created_at:
        type: int64
        auto: true
        description: Alert creation timestamp
      delivered_at:
        type: int64
        optional: true
        description: Delivery completion timestamp
      retry_count:
        type: int
        default: 0
        description: Current retry attempt count

  AlertRule:
    description: Alert routing and threshold rule
    fields:
      rule_id:
        type: string
        format: uuid-v7
        description: Unique rule identifier
      listing_id:
        type: string
        optional: true
        description: Specific listing or null for global rule
      event_type:
        type: string
        description: Event type this rule applies to
      severity_override:
        type: string
        enum: [info, warning, critical]
        optional: true
        description: Override default severity
      channels:
        type: array
        items: string
        description: Channels for this rule
      enabled:
        type: bool
        default: true
        description: Whether rule is active
      created_by:
        type: string
        description: Operator who created the rule

  AlertMute:
    description: Temporary alert suppression for a listing
    fields:
      mute_id:
        type: string
        format: uuid-v7
        description: Unique mute identifier
      listing_id:
        type: string
        description: Muted listing
      reason:
        type: string
        max: 256
        description: Why the listing is muted
      muted_by:
        type: string
        description: Operator identity
      muted_at:
        type: int64
        auto: true
        description: Mute start timestamp
      expires_at:
        type: int64
        description: Mute expiration timestamp
    constraints:
      - name: ck_mute_duration
        type: check
        expression: expires_at - muted_at <= config.mute_max_duration
        description: Mute duration cannot exceed configured maximum
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
        trigger: subscriptions_ready
        validates: all hub event subscriptions confirmed
      - from: active
        to: degraded
        trigger: alerting_agent_unavailable
        validates: notification delivery failed after retries
      - from: degraded
        to: active
        trigger: alerting_agent_recovered
        validates: alerting agent responds to health check
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
        validates: pending notifications drained or timeout elapsed

  entity.HubAlert:
    initial: pending
    transitions:
      - from: pending
        to: suppressed
        trigger: dedup_match
        validates: duplicate within dedup_window or listing muted
        side_effect: increment suppression counter
      - from: pending
        to: delivering
        trigger: dispatch_started
        validates: recipients resolved, channels selected
      - from: delivering
        to: delivered
        trigger: delivery_confirmed
        validates: alerting agent acknowledged all notifications
        side_effect: set delivered_at timestamp
      - from: delivering
        to: failed
        trigger: delivery_failed
        validates: retries exhausted
        side_effect: log failure, emit hub_alert.delivery.failed event
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID

Step 2 — Load Identity
  Action:      Load Ed25519 keypair from .weblisk/keys/hub-alert/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema against Types
  Validates:   All tables exist, columns match type definitions
  On Fail:     Run migration → if fails EXIT with STORAGE_UNREACHABLE

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 5 — Subscribe to Hub Events
  Action:      Subscribe to hub.behavioral.change, hub.verification.failure,
               hub.sla.breach, hub.listing.suspended, hub.peer.revoked,
               hub.marketplace.event, system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED

Step 6 — Load Active Mutes and Rules
  Action:      SELECT active mutes and rules from storage
  Validates:   Query succeeds, expired mutes pruned
  On Fail:     Enter degraded state — operate without rules/mutes

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9774, active_rules: N, active_mutes: M}
```

### Shutdown Sequence

```
Step 1 — Stop Accepting Events
  Action:      Unsubscribe from hub event topics
  agent_state → retiring

Step 2 — Drain Pending Notifications
  Action:      Deliver queued alerts (up to 30s)
  On Timeout:  Persist undelivered alerts to storage for next startup

Step 3 — Deregister
  Action:      DELETE /v1/register

Step 4 — Close Storage
  Action:      Close database connection

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, alerts_drained, alerts_persisted}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - alerting agent reachable
      - storage connected
      - event subscriptions active
    response:
      status: healthy
      details: {alerting_agent, storage, subscriptions, pending_alerts,
                active_rules, active_mutes}

  degraded:
    conditions:
      - alerting agent unreachable (queuing locally)
      - storage errors (retrying)
    response:
      status: degraded
      details: {reason, queued_alerts, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retries
      - no event subscriptions active
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

```
Step 1 — Validate new blueprint, verify version is newer
Step 2 — Compare Types block against current storage schema
Step 3 — Pause event processing → run migration → resume
Step 4 — Reload configuration, rules, and mutes
Log: lifecycle.version_updated {from, to}
```

---

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.behavioral.change` | Behavioral change detected by hub-verify |
| Event: `hub.verification.failure` | Signature or identity verification failed |
| Event: `hub.sla.breach` | Provider SLA violation detected by hub-metrics |
| Event: `hub.listing.suspended` | Listing suspended (manual or automatic) |
| Event: `hub.peer.revoked` | Trust relationship revoked |
| Event: `hub.marketplace.event` | Marketplace transaction event requiring notification |

---

## Actions

### notify-behavioral-change

Notify collaborators of capability behavioral change.

**Source:** Hub Verify

**Input:** `{listing_id: string, level: string, details: BehavioralChange}`

**Processing:**

```
1. Look up listing in index — resolve provider and active collaborators
2. Determine severity from change level:
   BENIGN → info, NOTABLE → warning, BREAKING → critical, CRITICAL → critical
3. Check deduplication: same listing + behavioral_change within dedup_window → suppress
4. Check mute status: listing muted → suppress non-CRITICAL
5. Check flapping: 3+ changes in dedup_window → consolidate
6. Resolve recipients per Notification Routing table
7. Create HubAlert record with status = pending
8. Dispatch to alerting agent for delivery
9. For cross-hub recipients: POST federation notify endpoint
10. Update HubAlert status based on delivery result
```

**Output:** `{alert_id: string, recipients_notified: int, suppressed: bool}`

**Errors:** `LISTING_NOT_FOUND` (permanent), `DELIVERY_FAILED` (transient)

---

### notify-verification-failure

Alert admin of signature/identity verification failure.

**Source:** Hub Verify

**Input:** `{listing_id: string, provider: string, reason: string}`

**Processing:**

```
1. Set severity = critical (verification failures are always critical)
2. Check deduplication
3. Notify registry operator + provider admin
4. Create HubAlert record, dispatch via alerting agent
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

### notify-sla-breach

Alert consumer of provider SLA violation.

**Source:** Hub Metrics

**Input:** `{listing_id: string, metric: string, threshold: float, actual: float}`

**Processing:**

```
1. Look up affected collaborations for listing
2. Notify consumer hub admins for active collaborations
3. Check deduplication and mute status
4. Create HubAlert record, dispatch via alerting agent
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

### notify-listing-suspension

Notify all collaborators that a listing is suspended.

**Source:** Hub Verify / Admin

**Input:** `{listing_id: string, reason: string}`

**Processing:**

```
1. Resolve all active collaborators for listing
2. Set severity = critical
3. Create HubAlert, dispatch to all collaborators
4. Include federation notifications for cross-hub collaborators
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

### notify-peer-revocation

Notify affected parties of trust revocation.

**Source:** Federation

**Input:** `{hub_name: string, reason: string}`

**Processing:**

```
1. Resolve both parties (consumer + provider hubs)
2. Set severity = critical
3. Create HubAlert record, dispatch notifications
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

### notify-marketplace-event

Transaction confirmations and purchase alerts.

**Source:** Marketplace

**Input:** `{listing_id: string, event_subtype: string, buyer: string, seller: string}`

**Processing:**

```
1. Notify buyer and seller hubs
2. Set severity = info
3. Create HubAlert record, dispatch notifications
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

### notify-collaborators

Send notification to all hubs using a specific listing.

**Source:** Any

**Input:** `{listing_id: string, subject: string, body: string, severity: string}`

**Output:** `{alert_id: string, recipients_notified: int, suppressed: int}`

---

### get-alert-history

Query past alerts by listing, provider, or type.

**Source:** Admin

**Input:** `{listing_id?: string, event_type?: string, limit?: int, offset?: int}`

**Output:** `{alerts: HubAlert[], total: int}`

**Side Effects:** None (read-only).

---

### configure-rules

Set alert thresholds and routing rules.

**Source:** Admin

**Input:** `{rule: AlertRule}`

**Output:** `{rule_id: string, created: bool}`

**Side Effects:** Writes to alert_rules store.

---

### mute-listing

Suppress alerts for a listing during known maintenance.

**Source:** Admin

**Input:** `{listing_id: string, reason: string, duration: int}`

**Output:** `{mute_id: string, expires_at: int64}`

**Side Effects:** Writes to alert_mutes store.

---

## Notification Routing

### Who Gets Notified

| Event | Recipients |
|-------|-----------|
| BENIGN behavioral change | Provider admin (info only) |
| NOTABLE behavioral change | Provider admin + all active collaborators |
| BREAKING behavioral change | Provider admin + all active collaborators (urgent) |
| CRITICAL behavioral change | Provider admin + all active collaborators + registry operators (critical) |
| Verification failure | Registry operator + provider admin |
| SLA breach | Consumer hub admin for affected collaborations |
| Listing suspension | All active collaborators |
| Trust revocation | Both parties (consumer + provider) |
| Marketplace purchase | Buyer + seller hubs |

### Notification Channels

Hub-alert delegates actual delivery to the alerting agent, specifying
the channel and urgency:

| Severity | Channel | Delivery |
|----------|---------|----------|
| info | In-app + email digest | Batched, next digest cycle |
| warning | In-app + email | Immediate email |
| critical | In-app + email + webhook | Immediate, all channels |

### Collaborator Notification Protocol

For cross-hub notifications, hub-alert uses the federation notification
endpoint:

```
POST {collaborator.federation_url}/notify
{
  "type": "behavioral_change",
  "listing_id": "avaropoint:seo-audit",
  "level": "NOTABLE",
  "details": {
    "previous_version": "1.2.0",
    "new_version": "1.3.0",
    "change_summary": "New optional field 'recommendations' added to response",
    "deprecation_window_days": 7
  },
  "timestamp": 1712160000,
  "signature": "<registry's Ed25519 signature>"
}
```

---

## Alert Deduplication

To avoid alert fatigue:

| Rule | Behavior |
|------|----------|
| Same listing + same event type within 1 hour | Suppress duplicate, increment count |
| Listing muted by admin | Suppress all non-CRITICAL alerts |
| Provider in maintenance window | Suppress availability alerts |
| Flapping detection (3+ state changes in 1 hour) | Consolidate into single "unstable" alert |

---

## Execute Workflow

The core alert processing loop for incoming hub events:

```
Phase 1 — Receive Event
  Accept event from bus (hub.behavioral.change, hub.sla.breach, etc.)
  Parse event payload, validate against expected schema
  If malformed → log and discard, do not generate false alerts

Phase 2 — Evaluate Suppression
  Check deduplication:
    Query alert_history for same listing_id + event_type
    within config.dedup_window → suppress if match found
  Check mute status:
    Query alert_mutes for listing_id with non-expired mute
    If muted AND severity != critical → suppress
  Check flapping:
    Count state changes for listing within config.dedup_window
    If count >= config.flapping_threshold → consolidate

Phase 3 — Resolve Recipients
  Query collaborator_registry for active collaborations on listing
  Apply routing rules from AlertRule table
  Determine channels per severity level

Phase 4 — Create Alert Record
  Insert HubAlert with status = pending
  Include all resolved recipients and channels

Phase 5 — Dispatch Notifications
  For local recipients:
    Send to alerting agent: {recipient, channel, severity, subject, body}
    Batch when multiple recipients share the same channel
  For federation recipients:
    POST {federation_url}/notify with signed payload
    Timeout: config.federation_notify_timeout

Phase 6 — Record Result
  Update HubAlert status: delivered | failed | suppressed
  Set delivered_at timestamp on success
  On failure: schedule retry (up to config.retry_max)

Phase 7 — Emit Metrics
  hub_alert_notifications_total by type, severity, channel
  hub_alert_suppressed_total by reason
  hub_alert_delivery_duration_seconds
```

---

## Collaboration

```yaml
events_published:
  - topic: hub_alert.delivered
    payload: {alert_id, listing_id, event_type, recipients_notified}
    when: Alert successfully delivered to all recipients

  - topic: hub_alert.delivery.failed
    payload: {alert_id, listing_id, event_type, error}
    when: Alert delivery failed after retries

  - topic: hub_alert.suppressed
    payload: {alert_id, listing_id, reason}
    when: Alert suppressed by dedup, mute, or flapping rule

  - topic: hub_alert.listing.muted
    payload: {mute_id, listing_id, duration, muted_by}
    when: Operator mutes alerts for a listing

events_subscribed:
  - topic: hub.behavioral.change
    payload: {listing_id, level, details}
    action: notify-behavioral-change

  - topic: hub.verification.failure
    payload: {listing_id, provider, reason}
    action: notify-verification-failure

  - topic: hub.sla.breach
    payload: {listing_id, metric, threshold, actual}
    action: notify-sla-breach

  - topic: hub.listing.suspended
    payload: {listing_id, reason}
    action: notify-listing-suspension

  - topic: hub.peer.revoked
    payload: {hub_name, reason}
    action: notify-peer-revocation

  - topic: hub.marketplace.event
    payload: {listing_id, event_subtype, buyer, seller}
    action: notify-marketplace-event

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "hub-alert"
    action: Self-update procedure

direct_messages:
  - target: alerting
    action: send-notification
    when: Delegating notification delivery
    reason: Hub-alert determines what to notify; alerting handles how
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All alert routing and suppression is autonomous
  supervised:    Muting and rule changes require operator
  manual-only:   All notification dispatch requires operator approval

overridable_behaviors:
  - behavior: automatic_deduplication
    default: enabled
    override: Set config.dedup_window = 0
    audit: logged

  - behavior: automatic_flapping_consolidation
    default: enabled
    override: Set config.flapping_threshold to high value
    audit: logged

  - behavior: federation_notifications
    default: enabled
    override: Disable via WL_HUB_ALERT_FED_ENABLED=false
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: mute-listing
    description: Suppress alerts for a listing during maintenance
    allowed: operator

  - action: configure-rules
    description: Create or modify alert routing rules
    allowed: operator

  - action: force-notify
    description: Send immediate notification bypassing dedup/mute
    allowed: operator

  - action: clear-mutes
    description: Remove all active mutes
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
    - MUST NOT send notifications to hubs not in collaborator_registry
    - MUST NOT modify listing data — read-only access to index
    - Notification rate bounded by config.max_batch_size per dispatch cycle

  forbidden_actions:
    - MUST NOT suspend or modify listings — only notify about suspensions
    - MUST NOT bypass deduplication for non-operator callers
    - MUST NOT send federation notifications without valid Ed25519 signature
    - MUST NOT expose alert payload details to unauthorized recipients

  resource_limits:
    memory: 256 MB (process limit)
    alert_history_rows: governed by config.history_retention
    max_active_mutes: 10000
    outbound_per_minute: 500 notifications
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Collaborator unreachable | Queue notification. Retry 3 times with backoff. Log failure. |
| Alerting agent unavailable | Log alert locally. Retry when alerting recovers. |
| Invalid event payload | Log and discard. Do not generate false alerts. |
| Rate limit on collaborator endpoint | Respect Retry-After header. Queue remaining notifications. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_alert_notifications_total | counter | Notifications by type, severity, and channel |
| hub_alert_delivery_duration_seconds | histogram | Time to deliver notification |
| hub_alert_suppressed_total | counter | Deduplicated or muted alerts |
| hub_alert_collaborator_notifications_total | counter | Cross-hub notifications sent |
| hub_alert_delivery_failures_total | counter | Failed notification deliveries |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send messages to alerting agent and respond to queries

    - capability: http:send
      resources: ["https://*"]
      description: Federation notification delivery to collaborator hubs

    - capability: database:read
      resources: [alert_rules, collaborator_registry, alert_history]
      description: Read rules, collaborators, and history

    - capability: database:write
      resources: [alert_history]
      description: Write alert records and mute entries

  data_sensitivity:
    - data: Alert payloads
      classification: medium
      handling: May contain listing details — encrypted at rest

    - data: Collaborator contact info
      classification: medium
      handling: Federation URLs and operator contacts — encrypted at rest

    - data: Alert history
      classification: low
      handling: Logged and queryable by admin

    - data: Federation notification signatures
      classification: high
      handling: Ed25519 private key never logged or transmitted

  access_control:
    - caller: hub-verify
      actions: [notify-behavioral-change, notify-verification-failure,
                notify-listing-suspension]

    - caller: hub-metrics
      actions: [notify-sla-breach]

    - caller: Any registered agent
      actions: [notify-collaborators, get-alert-history]

    - caller: Operator (auth token with operator role)
      actions: [configure-rules, mute-listing, get-alert-history,
                force-notify, clear-mutes]

    - caller: Unauthenticated
      actions: []
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Behavioral change notification
    action: notify-behavioral-change
    input:
      listing_id: "avaropoint:seo-audit"
      level: NOTABLE
      details:
        previous_version: "1.2.0"
        new_version: "1.3.0"
        change_summary: "New optional field added"
    expected:
      alert_id: "<uuid-v7>"
      recipients_notified: 3
      suppressed: false
    validates:
      - HubAlert created with status = delivered
      - Provider admin and all collaborators notified
      - Federation notifications sent with Ed25519 signature

  - name: SLA breach notification
    action: notify-sla-breach
    input:
      listing_id: "partner:api-gateway"
      metric: uptime_30d
      threshold: 99.5
      actual: 98.2
    expected:
      alert_id: "<uuid-v7>"
      recipients_notified: 1
    validates:
      - Consumer hub admin notified
      - Alert severity = warning
```

### Error Cases

```yaml
  - name: Malformed event payload
    trigger: hub.behavioral.change
    input: {invalid: true}
    expected: Logged and discarded, no alert created
    validates: No false alerts generated

  - name: Alerting agent down
    action: notify-behavioral-change
    condition: Alerting agent unreachable
    expected: Alert queued locally, retried on recovery
    validates: Agent enters degraded state
```

### Edge Cases

```yaml
  - name: Deduplication suppression
    action: notify-behavioral-change
    condition: Same listing + behavioral_change within dedup_window
    expected: {suppressed: true}
    validates: Counter incremented, no duplicate notification sent

  - name: Critical alert bypasses mute
    action: notify-behavioral-change
    input: {listing_id: "<muted-listing>", level: CRITICAL}
    expected: Alert delivered despite mute
    validates: CRITICAL severity bypasses mute suppression

  - name: Flapping consolidation
    condition: 4 behavioral changes for same listing in 1 hour
    expected: Single "unstable" alert sent
    validates: Flapping detection triggers consolidation
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

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: not required — all instances can process alerts
      description: >
        Alert processing is idempotent via dedup. Multiple instances
        can process different events concurrently. Dedup window
        prevents duplicate notifications from concurrent processing.
    state_sharing:
      mechanism: shared sqlite database
      conflict_resolution: >
        Deduplication uses alert_history table. First writer wins.
        Subsequent attempts for same listing + event_type within
        window are suppressed.

  event_handling:
    consumer_group: hub-alert
    delivery: one-per-group
    description: >
      Bus delivers each hub event to ONE instance in the hub-alert
      consumer group. Prevents duplicate alert processing.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share alert_history database. Schema migrations
      are additive-only during shadow phase.
```

---

## Implementation Notes

- **Delegation model**: Hub-alert decides _who_ and _when_ to notify.
  The alerting agent handles _how_ (channel selection, formatting,
  delivery). This separation keeps hub-alert focused on hub logic.
- **Federation signing**: All cross-hub notifications MUST be signed
  with the registry's Ed25519 key. Receiving hubs verify the signature
  before displaying the alert.
- **Mute safety**: CRITICAL alerts always bypass mutes. This prevents
  operators from accidentally silencing security-critical events.
- **Deduplication window**: The default 1-hour window is tunable per
  deployment. High-traffic hubs may need shorter windows to avoid
  stale suppression.
- **Batch delivery**: When multiple collaborators need the same
  notification, hub-alert batches them in a single message to the
  alerting agent to reduce overhead.
- **History pruning**: Alert history older than `config.history_retention`
  is pruned automatically on a background schedule.

---

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Behavioral change notifications reach all active collaborators
- [ ] CRITICAL changes trigger immediate notification on all channels
- [ ] Deduplication prevents repeated alerts within suppression window
- [ ] Muted listings suppress non-CRITICAL alerts
- [ ] Cross-hub notifications use federation protocol with Ed25519 signatures
- [ ] Alert history is queryable by listing, provider, and type
- [ ] SLA breach alerts include specific violation details
- [ ] Marketplace events trigger buyer/seller notifications
- [ ] Notification delivery failures are retried with backoff
- [ ] Metrics emit for all notification operations
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] State machine validates alert delivery transitions
- [ ] Startup sequence gates each step with pre-check/validates/on-fail
- [ ] Shutdown drains pending notifications before exit
- [ ] Configuration values validated against declared constraints
- [ ] Override audit records who, what, when, why
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Scaling: dedup prevents duplicate notifications across instances
- [ ] Blue-green: shadow phase validates events without side effects
