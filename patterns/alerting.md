<!-- blueprint
type: pattern
name: alerting
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/messaging, patterns/notification]
platform: any
tier: free
-->

# Alerting Pattern

Declarative alert evaluation, routing, and lifecycle management.
Alerting decides WHAT fires and WHO receives it; the notification
pattern handles HOW it gets delivered.

## Overview

Alerting is the evaluation and routing layer upstream of notification
delivery. Where `patterns/notification` defines channels, templates,
subscriber preferences, and delivery tracking, this pattern defines:

1. **Alert rules** — declarative conditions that trigger alerts
2. **Severity classification** — structured severity schema
3. **Routing rules** — who receives which alerts based on severity,
   source, and category
4. **Deduplication** — suppress repeated alerts within a time window
5. **Flapping detection** — detect rapidly toggling states
6. **Escalation chains** — auto-escalate unacknowledged alerts
7. **Suppression windows** — mute alerts during maintenance
8. **Alert grouping** — combine related alerts into one notification

Agents `extends: patterns/alerting` when they evaluate conditions
and emit structured alert events. The alerting agent is the primary
consumer, but any agent that needs rule-based alert evaluation can
extend this pattern.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentMessage
          fields_used: [from, to, action, payload, signature]
        - name: ErrorResponse
          fields_used: [code, message, detail]
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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/messaging
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

  - blueprint: patterns/notification
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: notification-dispatch
          parameters: [notification_id, severity, channels]
        - behavior: channel-adapter
          parameters: [channel_type]
      types:
        - name: NotificationRequest
          fields_used: [notification_id, severity, title, body, channels, template]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Separate evaluation from delivery** — Alerting decides WHAT fires and WHO receives it. Notification handles HOW it gets delivered. These concerns never mix. An alert rule never references a channel adapter; a notification template never evaluates conditions.
2. **Rule-based routing** — Alert destinations are determined by declarative routing rules matching on severity, source, and category. No hardcoded routing logic. New routes are added by declaring rules, not by modifying code.
3. **Noise reduction** — Deduplication windows, suppression rules, flapping detection, and alert grouping work together to prevent alert fatigue. Every alert passes through the noise reduction pipeline before reaching notification dispatch.
4. **Escalation by default** — Unacknowledged alerts ALWAYS escalate through the configured escalation chain. There are no silent failures. If an alert fires and nobody acknowledges it, someone higher in the chain will be notified.
5. **Extensible channels** — New delivery channels (Slack, PagerDuty, SMS) are added by extending `patterns/notification` with new channel adapters. The alerting pattern routes to logical targets; notification resolves those targets to physical channels.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: alert-evaluation
      description: Evaluate conditions against alert rules and emit alert events when thresholds are met
      parameters:
        - name: rules
          type: "[]AlertRule"
          required: true
          description: Declarative alert rules with conditions, severity, and targets
        - name: evaluation_interval
          type: int
          required: false
          default: 60
          description: Evaluation interval in seconds for polling-based rules
      inherits: Rule evaluation engine, condition matching, severity assignment
      overridable: true
      override_constraints: Must preserve severity classification schema; custom conditions must be serializable

    - name: alert-routing
      description: Route fired alerts to targets based on declarative routing rules
      parameters:
        - name: routing_rules
          type: "[]RoutingRule"
          required: true
          description: Rules matching alerts to notification targets
        - name: default_target
          type: string
          required: false
          default: log
          description: Fallback target when no routing rule matches
      inherits: Routing engine, rule matching, target resolution
      overridable: true
      override_constraints: Must evaluate rules in declared order; must always have a fallback

    - name: deduplication
      description: Suppress duplicate alerts within a configurable time window using fingerprint hashing
      parameters:
        - name: dedup_window
          type: int
          required: true
          default: 300
          description: Deduplication window in seconds
        - name: fingerprint_fields
          type: "[]string"
          required: false
          default: "[source, severity, category, message]"
          description: Fields used to compute the deduplication fingerprint
      inherits: Fingerprint computation, dedup cache, suppression counting
      overridable: true
      override_constraints: Must use consistent hashing; window must be >= 0

    - name: flapping-detection
      description: Detect rapidly toggling alert states and suppress notifications until stable
      parameters:
        - name: flap_window
          type: int
          required: true
          default: 600
          description: Window in seconds to count state transitions
        - name: flap_threshold
          type: int
          required: true
          default: 5
          description: Number of transitions within window to trigger flapping state
        - name: stabilization_period
          type: int
          required: true
          default: 300
          description: Seconds of stable state required to exit flapping
      inherits: Transition counter, flapping state machine, stabilization timer
      overridable: true
      override_constraints: Threshold must be >= 2; stabilization_period must be > 0

    - name: escalation
      description: Escalate unacknowledged alerts through an ordered chain of targets with timeouts
      parameters:
        - name: escalation_chains
          type: "[]EscalationChain"
          required: false
          description: Named escalation chains with ordered steps and timeouts
        - name: default_chain
          type: string
          required: false
          description: Default escalation chain name for alerts without explicit assignment
      inherits: Escalation timer, acknowledgment tracking, chain progression
      overridable: true
      override_constraints: Each chain must have at least one step; timeout must be > 0

    - name: suppression
      description: Mute alerts matching suppression rules during maintenance windows or manual silencing
      parameters:
        - name: suppression_windows
          type: "[]SuppressionWindow"
          required: false
          description: Time-based or rule-based suppression windows
      inherits: Suppression rule engine, window scheduling, override logic
      overridable: true
      override_constraints: Critical alerts may only be suppressed with explicit critical_override flag

    - name: alert-grouping
      description: Group related alerts into a single notification to reduce noise
      parameters:
        - name: group_by
          type: "[]string"
          required: false
          default: "[source, category]"
          description: Fields used to group related alerts
        - name: group_window
          type: int
          required: true
          default: 120
          description: Window in seconds to collect alerts into a group
        - name: max_group_size
          type: int
          required: false
          default: 50
          description: Maximum alerts per group before forcing delivery
      inherits: Grouping engine, group lifecycle, batched notification dispatch
      overridable: true
      override_constraints: group_window must be > 0; max_group_size must be >= 1

  types:
    - name: AlertRule
      description: Declarative alert rule with condition, severity, and target assignment
      inherited_by: Types section
    - name: AlertEvent
      description: Structured alert envelope emitted when a rule fires
      inherited_by: Types section
    - name: AlertSeverity
      description: Severity classification enum
      inherited_by: Types section
    - name: AlertState
      description: Alert lifecycle state enum
      inherited_by: Types section
    - name: RoutingRule
      description: Declarative rule mapping alerts to notification targets
      inherited_by: Types section
    - name: EscalationChain
      description: Ordered escalation steps with timeouts and targets
      inherited_by: Types section
    - name: SuppressionWindow
      description: Time-based or rule-based alert muting configuration
      inherited_by: Types section
    - name: AlertGroup
      description: Collection of related alerts combined into a single notification
      inherited_by: Types section

  events:
    - topic: alert.fired
      description: New alert triggered by rule evaluation
      payload: {alert_id, severity, source, category, message, fingerprint, timestamp}
    - topic: alert.acknowledged
      description: Operator acknowledged a firing alert
      payload: {alert_id, acknowledged_by, timestamp}
    - topic: alert.resolved
      description: Alert condition cleared (automatically or manually)
      payload: {alert_id, resolved_by, resolution, timestamp}
    - topic: alert.escalated
      description: Alert escalated to next step in escalation chain
      payload: {alert_id, chain_name, step, target, timestamp}
    - topic: alert.silenced
      description: Alert suppressed by a suppression window or mute rule
      payload: {alert_id, suppression_id, reason, expires_at, timestamp}
    - topic: alert.grouped
      description: Alert added to an existing alert group
      payload: {alert_id, group_id, group_size, timestamp}
```

---

## Types

```yaml
types:
  AlertSeverity:
    type: enum
    values: [critical, error, warning, info]
    description: Severity classification for alert events
    semantics:
      critical: Service down, data loss risk, or security breach — immediate action required
      error: Degraded service, failed operation — action required within minutes
      warning: Anomalous condition, approaching threshold — action required within hours
      info: Notable event for awareness — no action required

  AlertState:
    type: enum
    values: [firing, acknowledged, resolved, silenced]
    description: Lifecycle state of an alert instance
    semantics:
      firing: Condition active, notifications dispatched, escalation timer running
      acknowledged: Operator acknowledged — escalation paused, condition still active
      resolved: Condition cleared — either automatically or by manual resolution
      silenced: Alert suppressed by a suppression window — not delivered

  AlertRule:
    fields:
      rule_id:
        type: string
        required: true
        description: Unique identifier for the rule
      name:
        type: string
        required: true
        description: Human-readable rule name
      condition:
        type: string
        required: true
        description: >
          Evaluation expression. Format depends on implementation —
          may be a CEL expression, threshold comparison, or pattern match.
          Example: "error_rate > 0.05 for 5m"
      severity:
        type: AlertSeverity
        required: true
        description: Severity assigned when this rule fires
      category:
        type: string
        required: false
        description: Alert category for routing (e.g., "uptime", "security", "performance")
      source_filter:
        type: string
        required: false
        description: Restrict rule to alerts from a specific source pattern (glob)
      target:
        type: string
        required: false
        description: Explicit routing target override (bypasses routing rules)
      throttle:
        type: int
        required: false
        default: 300
        description: Minimum seconds between firings for this rule
      escalation_chain:
        type: string
        required: false
        description: Named escalation chain for alerts from this rule
      enabled:
        type: boolean
        required: true
        default: true
        description: Whether this rule is active
      labels:
        type: "map[string]string"
        required: false
        description: Arbitrary key-value labels for routing and grouping

  AlertEvent:
    fields:
      alert_id:
        type: string
        format: "alert-{ulid}"
        required: true
        description: Unique alert instance identifier
      rule_id:
        type: string
        required: true
        description: Rule that triggered this alert
      severity:
        type: AlertSeverity
        required: true
      state:
        type: AlertState
        required: true
      source:
        type: AlertSource
        required: true
      category:
        type: string
        required: false
      message:
        type: string
        max_length: 1000
        required: true
        description: Human-readable alert summary
      context:
        type: object
        required: false
        description: Structured data specific to the alert (metrics, URLs, error details)
      fingerprint:
        type: string
        required: true
        description: Hash of deduplicated fields for suppression matching
      labels:
        type: "map[string]string"
        required: false
      fired_at:
        type: datetime
        format: ISO8601
        required: true
      resolved_at:
        type: datetime
        format: ISO8601
        required: false
      acknowledged_at:
        type: datetime
        format: ISO8601
        required: false
      acknowledged_by:
        type: string
        required: false

  AlertSource:
    fields:
      type:
        type: enum
        values: [agent, domain, system, orchestrator]
        required: true
      name:
        type: string
        required: true
        description: Name of the emitting component
      domain:
        type: string
        required: false
        description: Domain if source is a domain agent

  RoutingRule:
    fields:
      rule_id:
        type: string
        required: true
      name:
        type: string
        required: true
      match:
        type: RoutingMatch
        required: true
        description: Conditions that determine if this rule applies
      targets:
        type: "[]string"
        required: true
        description: Notification targets (subscriber IDs, roles, or channel names)
      channels:
        type: "[]string"
        required: false
        description: Override channels for matched alerts
      priority:
        type: int
        required: false
        default: 0
        description: Rule evaluation order (higher = evaluated first)
      enabled:
        type: boolean
        required: true
        default: true

  RoutingMatch:
    fields:
      severities:
        type: "[]AlertSeverity"
        required: false
        description: Match alerts with these severities (empty = all)
      sources:
        type: "[]string"
        required: false
        description: Match alerts from these sources (glob patterns)
      categories:
        type: "[]string"
        required: false
        description: Match alerts with these categories
      labels:
        type: "map[string]string"
        required: false
        description: Match alerts with these label key-value pairs

  EscalationChain:
    fields:
      chain_id:
        type: string
        required: true
      name:
        type: string
        required: true
      steps:
        type: "[]EscalationStep"
        required: true
        description: Ordered list of escalation steps
      repeat:
        type: boolean
        required: false
        default: false
        description: Whether to restart the chain after the last step

  EscalationStep:
    fields:
      step:
        type: int
        required: true
        description: Step order (1-based)
      targets:
        type: "[]string"
        required: true
        description: Notification targets for this step
      channels:
        type: "[]string"
        required: false
        description: Override channels for this step
      timeout:
        type: int
        required: true
        description: Seconds to wait for acknowledgment before escalating

  SuppressionWindow:
    fields:
      suppression_id:
        type: string
        required: true
      name:
        type: string
        required: true
      match:
        type: RoutingMatch
        required: false
        description: Which alerts to suppress (empty = all alerts)
      start:
        type: datetime
        format: ISO8601
        required: true
      end:
        type: datetime
        format: ISO8601
        required: true
      critical_override:
        type: boolean
        required: false
        default: false
        description: If true, also suppress critical alerts (requires explicit opt-in)
      created_by:
        type: string
        required: true
        description: Identity that created the suppression window
      reason:
        type: string
        required: true
        description: Why this suppression window exists (e.g., "scheduled maintenance")

  AlertGroup:
    fields:
      group_id:
        type: string
        format: "agrp-{ulid}"
        required: true
      group_key:
        type: string
        required: true
        description: Computed key from group_by fields
      alerts:
        type: "[]string"
        required: true
        description: Alert IDs in this group
      severity:
        type: AlertSeverity
        required: true
        description: Highest severity among grouped alerts
      count:
        type: int
        required: true
      first_fired_at:
        type: datetime
        format: ISO8601
        required: true
      last_fired_at:
        type: datetime
        format: ISO8601
        required: true
      state:
        type: enum
        values: [collecting, dispatched, resolved]
        required: true
        description: Group lifecycle state
```

---

## Configuration

```yaml
config:
  dedup_window:
    type: int
    default: 300
    overridable: true
    min: 0
    max: 86400
    description: Default deduplication window in seconds

  flap_window:
    type: int
    default: 600
    overridable: true
    min: 60
    max: 3600
    description: Window in seconds for counting state transitions

  flap_threshold:
    type: int
    default: 5
    overridable: true
    min: 2
    max: 100
    description: Transitions within flap_window to trigger flapping state

  stabilization_period:
    type: int
    default: 300
    overridable: true
    min: 60
    max: 3600
    description: Seconds of stable state required to exit flapping

  group_window:
    type: int
    default: 120
    overridable: true
    min: 10
    max: 3600
    description: Window in seconds to collect alerts into a group

  max_group_size:
    type: int
    default: 50
    overridable: true
    min: 1
    max: 500
    description: Maximum alerts in a single group before forcing dispatch

  default_escalation_timeout:
    type: int
    default: 900
    overridable: true
    min: 60
    max: 86400
    description: Default seconds before escalation if no chain-specific timeout

  history_retention:
    type: int
    default: 604800
    overridable: true
    min: 3600
    max: 2592000
    description: Alert history retention in seconds (default 7 days)

  default_routing_target:
    type: string
    default: log
    overridable: true
    description: Fallback target when no routing rule matches
```

---

## Error Handling

### Evaluation Errors

| Scenario | Behavior |
|----------|----------|
| Rule condition parse failure | Log error, skip rule, continue evaluating remaining rules |
| Rule references unknown source | Log warning, skip rule |
| Evaluation timeout | Log timeout, mark rule as stale, retry next interval |

### Routing Errors

| Scenario | Behavior |
|----------|----------|
| No routing rule matches | Route to `default_routing_target` (log) |
| Target resolution failure | Log error, attempt remaining targets |
| All targets fail | Emit `alert.fired` event anyway — delivery failure is a notification concern |

### Deduplication Errors

| Scenario | Behavior |
|----------|----------|
| Dedup cache unavailable | Continue without dedup (allow duplicates rather than drop alerts) |
| Fingerprint computation failure | Use alert_id as fingerprint fallback |

### Escalation Errors

| Scenario | Behavior |
|----------|----------|
| Escalation chain not found | Use default chain; if none, log error and skip escalation |
| All escalation steps exhausted | If `repeat: true`, restart chain; otherwise log critical warning |
| Acknowledgment tracking unavailable | Continue escalation timer — prefer over-notify to silent failure |

### Suppression Errors

| Scenario | Behavior |
|----------|----------|
| Suppression window has invalid times | Log error, ignore window (alerts deliver normally) |
| Clock skew between nodes | Use server-local time; document that suppression windows are best-effort |

---

## Implementation Notes

- **Alert pipeline order**: Every alert passes through the pipeline in
  this order: evaluation → deduplication → suppression check →
  flapping check → grouping → routing → escalation setup →
  notification dispatch. Short-circuit at any stage that suppresses.
- **Fingerprint hashing**: Compute fingerprints using a stable hash
  (SHA-256) of the concatenated deduplicated fields. Field order must
  be deterministic (sort keys alphabetically before hashing).
- **Dedup cache**: Use an in-memory hash map with TTL eviction. Persist
  to storage on shutdown; reload on startup. If the cache is cold
  (first boot), accept potential duplicates rather than blocking.
- **Flapping state machine**: Track per-fingerprint transition counts.
  When a fingerprint exceeds `flap_threshold` transitions within
  `flap_window`, enter flapping state. Suppress notifications until
  the state is stable for `stabilization_period`. Emit a single
  summary notification when flapping resolves.
- **Escalation timers**: Use durable timers (not in-memory timeouts)
  for escalation. If the agent restarts, timers must survive. Store
  escalation state (current step, next escalation time) in the
  alert record.
- **Suppression window evaluation**: Check suppression windows before
  routing. A suppressed alert enters the `silenced` state and emits
  `alert.silenced`. Critical alerts bypass suppression windows
  unless `critical_override: true` is explicitly set.
- **Group lifecycle**: A group is created on the first alert matching
  a group key. Subsequent alerts within `group_window` are added to
  the group. When `group_window` expires or `max_group_size` is
  reached, the group is dispatched as a single notification. The
  notification severity is the highest severity in the group.
- **Separation from notification**: Alerting produces an AlertEvent
  and routes it to targets. The actual delivery (channel selection,
  template rendering, subscriber preferences) is handled by the
  notification pattern. Alerting calls `notification-dispatch` with
  the resolved targets and alert data.
- **Idempotent acknowledgment**: Acknowledging an already-acknowledged
  alert is a no-op. Acknowledging a resolved alert is a no-op. Both
  return success to avoid error handling in operator tooling.
- **Clock considerations**: Alert timestamps use the evaluating node's
  clock. Suppression windows and escalation timeouts use server-local
  time. Document that multi-node deployments should use NTP.

---

## Verification Checklist

- [ ] Alert rules are declared in YAML and evaluated by the rule engine without hardcoded logic
- [ ] Severity classification uses the four-level enum (critical, error, warning, info) — no custom levels
- [ ] Routing rules are evaluated in priority order with a guaranteed fallback target
- [ ] Deduplication suppresses repeated alerts within the configured window using fingerprint matching
- [ ] Suppressed alerts increment the suppressed count and do not trigger notifications
- [ ] Flapping detection enters flapping state after threshold transitions and suppresses until stable
- [ ] A summary notification is emitted when flapping resolves
- [ ] Unacknowledged alerts escalate through the configured chain after the timeout expires
- [ ] Escalation state survives agent restart (durable storage, not in-memory timers)
- [ ] Suppression windows prevent notification delivery for matched alerts during the window
- [ ] Critical alerts bypass suppression windows unless `critical_override: true` is set
- [ ] Alert grouping combines related alerts into a single notification within the group window
- [ ] Group severity is the highest severity among grouped alerts
- [ ] All alert lifecycle events (`alert.fired`, `alert.acknowledged`, `alert.resolved`, `alert.escalated`, `alert.silenced`, `alert.grouped`) are emitted on the messaging bus
- [ ] Alerting never references channel adapters directly — delivery is delegated to `patterns/notification`
