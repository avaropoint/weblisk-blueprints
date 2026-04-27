<!-- blueprint
type: pattern
name: incident-response
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/alerting, patterns/state-machine]
platform: any
tier: free
-->

# Incident Response Pattern

Incident lifecycle management, runbook execution, alert correlation,
and post-incident review as a cross-cutting contract. This pattern
formalizes the platform-wide contract for how incidents are created,
triaged, remediated, and closed. The incident-response agent is the
primary executor, but any agent that manages incidents extends this
pattern and inherits its types, events, and lifecycle rules.

## Overview

Incident response sits downstream of alerting. Where `patterns/alerting`
defines WHAT fires and WHO receives it, this pattern defines:

1. **Incident severity matrix** — structured severity schema with
   response time expectations and escalation thresholds
2. **Incident lifecycle** — state machine from detection through
   post-mortem to closure
3. **Alert correlation** — rules for grouping related alerts into
   a single incident instead of creating duplicates
4. **Runbook declaration** — declarative YAML format for remediation
   procedures with steps, conditions, and rollback
5. **Remediation steps** — individual actions classified as safe
   (auto-execute) or dangerous (require human approval)
6. **Escalation policy** — when automated remediation gives way to
   human operators, with configurable thresholds
7. **Post-incident review** — automatic timeline generation and
   structured report template for every resolved incident

Agents `extends: patterns/incident-response` when they need to
create, manage, or respond to incidents. The incident-response agent
is the primary consumer, but domain-specific agents may extend this
pattern for specialized incident handling.

### Boundary with Alerting

| Concern | Owner |
|---------|-------|
| Alert rule evaluation | `patterns/alerting` |
| Alert routing and deduplication | `patterns/alerting` |
| Alert-to-incident correlation | `patterns/incident-response` |
| Runbook matching and execution | `patterns/incident-response` |
| Safe remediation automation | `patterns/incident-response` |
| Escalation to human operators | `patterns/incident-response` |
| Post-incident report generation | `patterns/incident-response` |
| Notification delivery | `patterns/notification` (via alerting) |

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
        - name: AlertEvent
          fields_used: [alert_id, source, type, severity, target, message, timestamp]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/alerting
    version: ">=1.0.0 <2.0.0"
    bindings:
      events:
        - topic: alert.fired
          fields_used: [alert_id, severity, source, category, message, fingerprint, timestamp]
        - topic: alert.resolved
          fields_used: [alert_id, resolved_by, resolution, timestamp]
      types:
        - name: AlertEvent
          fields_used: [alert_id, severity, source, category, message, fingerprint]
        - name: AlertSeverity
          fields_used: [critical, error, warning, info]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: state-transition
          parameters: [from, to, trigger, validates]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Automation-First, Human-Final** — Automate triage, correlation, and safe remediation steps without human involvement. Escalate to human operators only for dangerous actions, ambiguous root causes, or when automated steps fail. The goal is fast MTTR for routine incidents and human judgment for novel ones.
2. **Runbooks Are Data** — Runbook steps are declarative YAML structures, not embedded code or scripts. This makes runbooks versionable, auditable, validatable at load time, and portable across implementations. The pattern defines the runbook schema; agents interpret and execute it.
3. **Correlation Over Duplication** — Related alerts form one incident, not many. Correlation rules match on source, category, and time window to group alerts. A correlated incident has a single timeline, a single runbook execution, and a single owner. Duplicate incidents create confusion and waste operator attention.
4. **Every Incident Has a Post-Mortem** — No incident transitions to `closed` without a post-incident report. The report is generated automatically from the incident timeline, runbook execution results, and resolution metadata. Human operators may annotate with root cause analysis and recommendations, but the baseline report is always produced.
5. **Safe by Default** — Every remediation step is classified as `safe` or `dangerous`. Safe steps (health checks, diagnostic queries, service restarts) auto-execute without approval. Dangerous steps (failovers, rollbacks, rate limit changes) pause the runbook and wait for human approval. The default classification is `safe: false` — steps must explicitly opt in to auto-execution.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: alert-correlation
      description: Correlate incoming alerts into incidents using configurable rules to prevent duplicate incidents
      parameters:
        - name: correlation_rules
          type: "[]CorrelationRule"
          required: true
          description: Rules defining how alerts group into incidents
        - name: correlation_window
          type: int
          required: false
          default: 300
          description: Time window in seconds for correlating alerts into the same incident
        - name: max_alerts_per_incident
          type: int
          required: false
          default: 100
          description: Maximum correlated alerts before forcing a new incident
      inherits: Correlation engine, hash computation, incident grouping
      overridable: true
      override_constraints: Must use deterministic hashing; correlation window must be > 0

    - name: runbook-execution
      description: Match incidents to runbooks and execute remediation steps with approval gates
      parameters:
        - name: runbooks
          type: "[]Runbook"
          required: true
          description: Declarative runbook definitions with trigger conditions and steps
        - name: max_concurrent_runbooks
          type: int
          required: false
          default: 5
          description: Maximum runbooks executing simultaneously
        - name: step_timeout_default
          type: int
          required: false
          default: 30
          description: Default timeout in seconds for runbook steps without explicit timeout
      inherits: Runbook matching, step sequencing, approval gates, rollback execution
      overridable: true
      override_constraints: Must respect step safety classification; dangerous steps must always require approval

    - name: escalation-policy
      description: Escalate incidents to human operators when automated remediation is insufficient
      parameters:
        - name: policies
          type: "[]EscalationPolicy"
          required: true
          description: Named escalation policies with severity thresholds and notification targets
        - name: auto_escalate_on_failure
          type: boolean
          required: false
          default: true
          description: Automatically escalate when a runbook step fails with on_failure=escalate
        - name: max_auto_actions
          type: int
          required: false
          default: 10
          description: Maximum automated actions before mandatory escalation regardless of step outcomes
      inherits: Escalation timer, operator notification, handoff tracking
      overridable: true
      override_constraints: Critical incidents must always have an escalation path; max_auto_actions must be >= 1

    - name: incident-lifecycle
      description: Manage incident state transitions from detection through closure with post-mortem
      parameters:
        - name: auto_resolve_timeout
          type: int
          required: false
          default: 300
          description: Seconds to wait after auto-resolution before confirming (guards against recurrence)
        - name: post_mortem_required
          type: boolean
          required: false
          default: true
          description: Whether a post-incident report is required before closing
        - name: stale_incident_timeout
          type: int
          required: false
          default: 86400
          description: Seconds before an idle incident is flagged as stale
      inherits: State machine transitions, timeline tracking, post-mortem generation
      overridable: true
      override_constraints: Post-mortem generation cannot be disabled for critical incidents

    - name: post-incident-review
      description: Generate structured post-incident reports from incident timelines and runbook results
      parameters:
        - name: include_timeline
          type: boolean
          required: false
          default: true
          description: Include full chronological timeline in report
        - name: include_recommendations
          type: boolean
          required: false
          default: true
          description: Generate improvement recommendations based on incident data
        - name: report_retention
          type: int
          required: false
          default: 7776000
          description: Report retention in seconds (default 90 days)
      inherits: Timeline aggregation, report template, recommendation engine
      overridable: true
      override_constraints: Reports must always include incident_id, severity, duration, and resolution method

  types:
    - name: IncidentSeverity
      description: Severity classification for incidents with response time expectations
      inherited_by: Types section
    - name: IncidentStatus
      description: Incident lifecycle state enum
      inherited_by: Types section
    - name: Incident
      description: Correlated incident record with timeline, runbook state, and assignment
      inherited_by: Types section
    - name: Runbook
      description: Declarative remediation procedure with trigger conditions and ordered steps
      inherited_by: Types section
    - name: RunbookStep
      description: Individual remediation action with safety classification and rollback
      inherited_by: Types section
    - name: CorrelationRule
      description: Rule for grouping related alerts into a single incident
      inherited_by: Types section
    - name: EscalationPolicy
      description: Policy defining when and how to hand off to human operators
      inherited_by: Types section
    - name: PostIncidentReport
      description: Structured report generated after incident resolution
      inherited_by: Types section
    - name: TimelineEntry
      description: Single chronological event in an incident timeline
      inherited_by: Types section

  events:
    - topic: incident.detected
      description: New incident created from correlated alerts
      payload: {incident_id, severity, source, alert_ids, correlation_hash, timestamp}
    - topic: incident.triaging
      description: Incident triage started — correlating alerts and matching runbooks
      payload: {incident_id, severity, alert_count, timestamp}
    - topic: incident.mitigating
      description: Runbook execution in progress for this incident
      payload: {incident_id, runbook_name, current_step, timestamp}
    - topic: incident.escalated
      description: Incident escalated to human operator
      payload: {incident_id, severity, reason, escalation_policy, targets, timestamp}
    - topic: incident.resolved
      description: Incident resolved (auto or operator)
      payload: {incident_id, resolution_method, resolution_summary, duration_seconds, timestamp}
    - topic: incident.post-mortem
      description: Post-mortem review phase entered
      payload: {incident_id, report_id, timestamp}
    - topic: incident.closed
      description: Incident fully closed after post-mortem review
      payload: {incident_id, report_id, closed_by, timestamp}
```

---

## Types

```yaml
types:
  IncidentSeverity:
    type: enum
    values: [critical, high, medium, low]
    description: Severity classification for incidents
    semantics:
      critical: >
        Service down, data loss risk, or security breach.
        Response: immediate. Escalation: auto after 5 minutes.
        Example: primary database unreachable, authentication service down.
      high: >
        Degraded service affecting users, failed critical workflow.
        Response: within 15 minutes. Escalation: auto after 30 minutes.
        Example: agent offline, elevated error rate, TLS expiring < 24h.
      medium: >
        Non-critical degradation, approaching thresholds.
        Response: within 1 hour. Escalation: auto after 2 hours.
        Example: performance regression, disk usage > 80%, queue backlog.
      low: >
        Minor issue, informational anomaly.
        Response: within 24 hours. Escalation: manual only.
        Example: non-critical agent slow, cosmetic errors, stale cache.

  IncidentStatus:
    type: enum
    values: [detected, triaging, mitigating, resolved, post-mortem, closed]
    description: Incident lifecycle state
    semantics:
      detected: Alert received, incident record created, awaiting triage
      triaging: Correlating with other alerts, matching runbooks, assessing severity
      mitigating: Runbook executing or operator performing remediation
      resolved: Incident resolved — awaiting stability confirmation and post-mortem
      post-mortem: Post-incident review in progress, report being generated or annotated
      closed: Post-mortem complete, incident archived

  Incident:
    description: Correlated incident record
    fields:
      incident_id:
        type: string
        format: "inc_{YYYYMMDD}_{seq}"
        required: true
        description: Unique incident identifier
      severity:
        type: IncidentSeverity
        required: true
        description: Current incident severity (may be upgraded during correlation)
      status:
        type: IncidentStatus
        required: true
        description: Current lifecycle state
      source:
        type: object
        fields:
          alert_type: {type: string, description: "Originating alert type"}
          agent: {type: string, description: "Source agent name"}
          domain: {type: string, description: "Source domain if applicable"}
        required: true
        description: Originating alert source details
      alerts:
        type: "[]string"
        required: true
        description: Correlated alert IDs
      correlation_hash:
        type: string
        required: true
        description: Hash of source + type + target for deduplication
      runbook:
        type: string
        required: false
        description: Active runbook name (null if no runbook matched)
      current_step:
        type: string
        required: false
        description: Current runbook step name
      assignee:
        type: string
        required: false
        description: Assigned operator identity (null until escalated)
      resolution:
        type: string
        required: false
        description: Resolution summary (populated on resolve)
      timeline:
        type: "[]TimelineEntry"
        required: true
        description: Chronological event log
      report_id:
        type: string
        required: false
        description: Post-incident report ID (populated after post-mortem)
      created_at:
        type: datetime
        format: ISO8601
        required: true
        description: Incident creation timestamp
      updated_at:
        type: datetime
        format: ISO8601
        required: true
        description: Last state change timestamp
      resolved_at:
        type: datetime
        format: ISO8601
        required: false
        description: Resolution timestamp

  TimelineEntry:
    description: Single chronological event in an incident timeline
    fields:
      time:
        type: datetime
        format: ISO8601
        required: true
        description: Event timestamp
      event:
        type: string
        required: true
        description: Event type identifier (e.g., incident_created, runbook_started, step_completed)
      detail:
        type: string
        max_length: 512
        required: true
        description: Human-readable event description
      actor:
        type: string
        required: false
        description: Identity that caused this event (system, agent, or operator)

  Runbook:
    description: Declarative remediation procedure
    fields:
      name:
        type: string
        max_length: 64
        required: true
        description: Unique runbook identifier
      description:
        type: string
        max_length: 256
        required: true
        description: What this runbook remediates
      trigger:
        type: RunbookTrigger
        required: true
        description: Conditions that activate this runbook
      steps:
        type: "[]RunbookStep"
        required: true
        description: Ordered remediation steps
      rollback:
        type: "[]RunbookStep"
        required: false
        description: Rollback steps executed if remediation fails
      escalation:
        type: object
        fields:
          message: {type: string, description: "Escalation notification message"}
          severity: {type: IncidentSeverity, description: "Escalation severity"}
          notify: {type: "[]string", description: "Notification targets"}
        required: true
        description: Escalation configuration when runbook fails
      enabled:
        type: boolean
        required: true
        default: true
        description: Whether this runbook is active

  RunbookTrigger:
    description: Conditions that activate a runbook
    fields:
      alert_type:
        type: string
        required: true
        description: Alert type pattern to match (exact or glob)
      severity:
        type: "[]IncidentSeverity"
        required: false
        description: Severity levels that activate this runbook (empty = all)
      source_filter:
        type: string
        required: false
        description: Source pattern filter (glob)
      category:
        type: string
        required: false
        description: Alert category filter

  RunbookStep:
    description: Individual remediation action
    fields:
      name:
        type: string
        max_length: 64
        required: true
        description: Step identifier
      action:
        type: string
        required: true
        description: Action to execute (references a registered action handler)
      description:
        type: string
        max_length: 256
        required: false
        description: Human-readable description of what this step does
      safe:
        type: boolean
        required: true
        default: false
        description: >
          Whether this step auto-executes without approval.
          Safe steps: health checks, diagnostics, service restarts.
          Dangerous steps: failovers, rollbacks, configuration changes.
      timeout:
        type: int
        required: false
        default: 30
        unit: seconds
        description: Step execution timeout
      retry:
        type: int
        required: false
        default: 0
        description: Number of retries on failure
      retry_delay:
        type: int
        required: false
        default: 5
        unit: seconds
        description: Delay between retries
      on_success:
        type: enum
        values: [next, auto_resolve, verify_recovery]
        required: true
        description: Action when step succeeds
      on_failure:
        type: enum
        values: [next, escalate, rollback]
        required: true
        description: Action when step fails
      rollback_action:
        type: string
        required: false
        description: Action to execute if this step needs to be rolled back

  CorrelationRule:
    description: Rule for grouping related alerts into a single incident
    fields:
      rule_id:
        type: string
        required: true
        description: Unique rule identifier
      name:
        type: string
        required: true
        description: Human-readable rule name
      match:
        type: object
        fields:
          sources: {type: "[]string", description: "Source patterns to match (glob)"}
          categories: {type: "[]string", description: "Alert categories to match"}
          alert_types: {type: "[]string", description: "Alert type patterns to match"}
          severities: {type: "[]IncidentSeverity", description: "Severity levels to match"}
        required: true
        description: Conditions for alert matching
      window:
        type: int
        required: true
        default: 300
        unit: seconds
        description: Time window for correlation — alerts within this window are grouped
      hash_fields:
        type: "[]string"
        required: true
        default: "[source, alert_type, category]"
        description: Fields used to compute the correlation hash
      priority:
        type: int
        required: false
        default: 0
        description: Rule evaluation order (higher = evaluated first)
      enabled:
        type: boolean
        required: true
        default: true

  EscalationPolicy:
    description: Policy defining when and how to escalate to human operators
    fields:
      policy_id:
        type: string
        required: true
        description: Unique policy identifier
      name:
        type: string
        required: true
        description: Human-readable policy name
      severity_threshold:
        type: IncidentSeverity
        required: true
        description: Minimum severity that triggers this policy
      auto_escalate_after:
        type: int
        required: true
        unit: seconds
        description: Seconds before auto-escalation if incident is not resolved
      max_auto_actions:
        type: int
        required: false
        default: 10
        description: Maximum automated actions before mandatory escalation
      targets:
        type: "[]EscalationTarget"
        required: true
        description: Ordered escalation targets
      repeat:
        type: boolean
        required: false
        default: false
        description: Whether to restart the escalation chain after exhausting all targets

  EscalationTarget:
    description: Single target in an escalation chain
    fields:
      step:
        type: int
        required: true
        description: Escalation step order (1-based)
      targets:
        type: "[]string"
        required: true
        description: Notification targets (roles, identities, or channel names)
      timeout:
        type: int
        required: true
        unit: seconds
        description: Seconds to wait for acknowledgment before escalating to next step
      channels:
        type: "[]string"
        required: false
        description: Override notification channels for this step

  PostIncidentReport:
    description: Structured report generated after incident resolution
    fields:
      report_id:
        type: string
        format: "pir_{YYYYMMDD}_{seq}"
        required: true
        description: Unique report identifier
      incident_id:
        type: string
        required: true
        description: Parent incident
      severity:
        type: IncidentSeverity
        required: true
        description: Incident severity at resolution
      duration_seconds:
        type: int
        required: true
        description: Detection-to-resolution time in seconds
      root_cause:
        type: string
        required: false
        description: Identified root cause (may be populated by operator)
      resolution_method:
        type: enum
        values: [auto_resolved, operator_resolved, escalated_and_resolved]
        required: true
        description: How the incident was resolved
      runbook_used:
        type: string
        required: false
        description: Runbook executed (null if no runbook)
      steps_executed:
        type: int
        required: true
        description: Total runbook steps attempted
      steps_succeeded:
        type: int
        required: true
        description: Steps completed successfully
      timeline:
        type: "[]TimelineEntry"
        required: true
        description: Full incident timeline
      recommendations:
        type: "[]string"
        required: false
        description: Improvement recommendations
      created_at:
        type: datetime
        format: ISO8601
        required: true
        description: Report generation timestamp
      reviewed_by:
        type: string
        required: false
        description: Operator who reviewed and annotated the report
      reviewed_at:
        type: datetime
        format: ISO8601
        required: false
        description: Review timestamp
```

---

## Configuration

```yaml
config:
  correlation_window:
    type: int
    default: 300
    overridable: true
    min: 30
    max: 3600
    description: Default time window in seconds for correlating alerts into incidents

  max_alerts_per_incident:
    type: int
    default: 100
    overridable: true
    min: 1
    max: 1000
    description: Maximum correlated alerts per incident before forcing a new incident

  max_concurrent_runbooks:
    type: int
    default: 5
    overridable: true
    min: 1
    max: 50
    description: Maximum runbooks executing simultaneously

  step_timeout_default:
    type: int
    default: 30
    overridable: true
    min: 5
    max: 600
    description: Default timeout in seconds for runbook steps

  auto_resolve_timeout:
    type: int
    default: 300
    overridable: true
    min: 60
    max: 3600
    description: >
      Seconds to wait after auto-resolution before confirming.
      Guards against recurrence — if the same correlation hash
      fires within this window, the incident re-opens.

  stale_incident_timeout:
    type: int
    default: 86400
    overridable: true
    min: 3600
    max: 604800
    description: Seconds before an idle incident is flagged as stale

  max_auto_actions:
    type: int
    default: 10
    overridable: true
    min: 1
    max: 100
    description: >
      Maximum automated actions per incident before mandatory
      escalation, regardless of individual step outcomes

  report_retention:
    type: int
    default: 7776000
    overridable: true
    min: 604800
    max: 31536000
    description: Post-incident report retention in seconds (default 90 days)

  incident_history_retention:
    type: int
    default: 2592000
    overridable: true
    min: 604800
    max: 31536000
    description: Closed incident retention in seconds (default 30 days)
```

---

## Error Handling

### Correlation Errors

| Scenario | Behavior |
|----------|----------|
| Correlation rule parse failure | Log error, skip rule, evaluate remaining rules |
| Hash computation failure | Use alert_id as fallback hash (creates new incident) |
| Max alerts per incident exceeded | Create new incident for overflow alerts, link to parent |
| No correlation rule matches | Create standalone incident from the single alert |

### Runbook Errors

| Scenario | Behavior |
|----------|----------|
| No matching runbook found | Escalate immediately — no automated remediation available |
| Runbook step timeout | Mark step as failed, execute on_failure action (next or escalate) |
| Runbook step action unknown | Log error, skip step, escalate if no remaining safe steps |
| Multiple runbooks match | Select highest-priority runbook; log alternatives for operator review |
| Concurrent runbook limit reached | Queue incident for runbook execution; do not drop |

### Escalation Errors

| Scenario | Behavior |
|----------|----------|
| Escalation policy not found | Use default policy; if none, log critical warning and retry |
| All escalation targets exhausted | If `repeat: true`, restart chain; otherwise emit critical alert |
| Operator notification failure | Retry notification via alerting pattern; log delivery failure |
| Acknowledgment tracking unavailable | Continue escalation timer — prefer over-notify to silent failure |

### Lifecycle Errors

| Scenario | Behavior |
|----------|----------|
| Invalid state transition attempted | Reject transition, log error, preserve current state |
| Post-mortem generation failure | Log error, allow manual report creation, do not block closure |
| Timeline append failure | Log error, continue incident processing — timeline is best-effort |
| Storage unavailable | Retry with backoff; operate in degraded mode with in-memory state |

---

## Implementation Notes

- **Correlation pipeline**: When an alert arrives, process it through
  correlation rules in priority order. Compute the correlation hash
  from the configured `hash_fields`. Search active incidents for a
  matching hash within the `correlation_window`. If found, append the
  alert to the existing incident and upgrade severity if the new alert
  is higher. If no match, create a new incident.

- **Correlation hash**: Use SHA-256 over the concatenated hash fields
  with deterministic key ordering (sort alphabetically). The hash is
  stable across implementations and agent restarts.

- **Runbook matching**: After correlation, match the incident against
  runbook triggers. Match criteria: alert_type (exact or glob),
  severity (if specified), source_filter (if specified). If multiple
  runbooks match, select the one with the most specific trigger. If
  still ambiguous, select the first declared.

- **Step safety classification**: The `safe` field on RunbookStep is
  the gating mechanism. Steps with `safe: true` auto-execute. Steps
  with `safe: false` (the default) pause the runbook and emit
  `incident.escalated` with the step details. The operator must
  explicitly approve before the step executes.

- **Approval gates**: When a dangerous step is reached, the runbook
  enters a waiting state. The incident status remains `mitigating`
  but the timeline records `step_awaiting_approval`. Approval is
  granted via the `acknowledge` action on the incident-response agent.
  If no approval arrives within the step timeout, the step's
  `on_failure` action executes.

- **Rollback execution**: When a step specifies `on_failure: rollback`,
  the runbook reverses completed steps in reverse order using each
  step's `rollback_action`. Rollback steps are always classified as
  safe (they undo previous actions). If rollback fails, escalate.

- **Auto-resolve confirmation**: When a runbook completes successfully
  and the final step returns `auto_resolve`, the incident enters
  `resolved` status but remains monitored for `auto_resolve_timeout`
  seconds. If the same correlation hash fires within that window, the
  incident re-opens and transitions back to `triaging`.

- **Post-mortem generation**: When an incident reaches `resolved`
  status and stability is confirmed, automatically generate a
  PostIncidentReport from the incident timeline. Include: duration,
  resolution method, runbook used, steps executed/succeeded, and
  the full timeline. Recommendations are generated based on patterns
  (e.g., "runbook step X failed — consider adding a retry" or
  "incident recurred — investigate root cause").

- **Timeline immutability**: Timeline entries are append-only. Once
  written, a timeline entry is never modified or deleted. This ensures
  the incident record is a reliable audit trail.

- **Escalation timers**: Use durable timers (persisted to storage),
  not in-memory timeouts. If the agent restarts, escalation timers
  must survive. Store the current escalation step and next escalation
  time in the incident record.

- **Severity upgrade**: During correlation, if a new alert has higher
  severity than the current incident, upgrade the incident severity.
  Never downgrade severity automatically — downgrades require explicit
  operator action.

- **Concurrent runbook limit**: Track active runbook count. When the
  limit is reached, queue new incidents for runbook execution rather
  than dropping them. Process the queue in severity order (critical
  first).

---

## Verification Checklist

- [ ] Incoming alerts are correlated using configurable rules with deterministic hash computation
- [ ] Related alerts within the correlation window merge into a single incident instead of creating duplicates
- [ ] Incident severity is upgraded (never downgraded) when higher-severity alerts correlate
- [ ] Runbook steps with `safe: true` auto-execute without operator approval
- [ ] Runbook steps with `safe: false` pause execution and emit `incident.escalated`
- [ ] Operator approval is required before dangerous steps execute
- [ ] Runbook rollback executes completed steps in reverse order on failure
- [ ] Incidents auto-escalate to human operators after configurable thresholds (time, action count)
- [ ] Auto-resolved incidents are monitored for recurrence during the `auto_resolve_timeout` window
- [ ] Every resolved incident generates a PostIncidentReport with timeline, duration, and resolution method
- [ ] No incident transitions to `closed` without a post-incident report (when `post_mortem_required: true`)
- [ ] All incident lifecycle events (`incident.detected` through `incident.closed`) are emitted on the messaging bus
- [ ] Escalation timers survive agent restart (durable storage, not in-memory)
- [ ] Concurrent runbook execution respects the configured limit, with overflow queued by severity
- [ ] Invalid state transitions are rejected and logged without corrupting incident state
