<!-- blueprint
type: agent
kind: infrastructure
name: incident-response
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/state-machine, patterns/messaging, patterns/notification, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, agents/alerting]
platform: any
tier: free
port: 9760
-->

# Incident Response Agent

Infrastructure agent that provides automated incident detection,
runbook execution, remediation steps, and post-incident reporting.
Works alongside the alerting agent — alerting handles notification
routing, incident-response handles what to do about it.

## Overview

The incident-response agent receives alert events and system health
signals, correlates them into incidents, executes predefined runbooks,
and tracks resolution. It bridges the gap between "something is wrong"
(alerting) and "here's how to fix it" (remediation).

This agent does NOT replace human operators for critical decisions.
It automates triage, executes safe remediation steps, and escalates
to operators when human judgment is required.

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
        - name: AlertEvent
          fields_used: [alert_id, source, type, severity, target, message, timestamp]
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

  - blueprint: agents/alerting
    version: ">=1.0.0 <2.0.0"
    bindings:
      events:
        - topic: alert.fired
          fields_used: [alert_id, source, type, severity, target, message, timestamp]
        - topic: alert.resolved
          fields_used: [alert_id, source]
    on_change:
      compatible: validate-and-adopt
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
        - behavior: flat-file-engine
          parameters: [engine, directory, format]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: state-transition
          parameters: [from, to, trigger, validates]
    on_change:
      compatible: validate
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
        - behavior: notify
          parameters: [channel, recipients, message, severity]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: auth-token
          parameters: [verify, sign, claims]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: approval-gate
          parameters: [required_approvers, timeout, auto_approve_conditions]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

depends_on: [alerting]
  # Runtime dependency on alerting agent. Incident-response receives
  # alert.fired events from alerting. If alerting is unavailable,
  # incident-response operates in degraded mode (no new alert-driven incidents).
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  Incident:
    description: A correlated incident record
    fields:
      incident_id:
        type: string
        format: "inc_{YYYYMMDD}_{seq}"
        description: Unique incident identifier
      severity:
        type: string
        enum: [critical, high, medium, low]
        description: Incident severity level
      state:
        type: string
        enum: [detected, triaging, runbook_executing, auto_resolved, escalated, awaiting_operator, resolved]
        description: Current incident state
      source:
        type: object
        fields: {alert_type: string, agent: string, domain: string}
        description: Originating alert details
      alerts:
        type: array
        items: string
        description: Correlated alert IDs
      correlation_hash:
        type: string
        description: Hash of source + type + target for deduplication
      runbook:
        type: string
        optional: true
        description: Active runbook name
      current_step:
        type: string
        optional: true
        description: Current runbook step name
      operator:
        type: string
        optional: true
        description: Assigned operator identity
      resolution:
        type: string
        optional: true
        description: Resolution summary
      timeline:
        type: array
        items: TimelineEntry
        description: Chronological event log
      created_at:
        type: int64
        auto: true
        description: Incident creation timestamp
      updated_at:
        type: int64
        auto: true
        description: Last state change timestamp
      resolved_at:
        type: int64
        optional: true
        description: Resolution timestamp
    constraints:
      - name: uq_incident_id
        type: unique
        fields: [incident_id]

  TimelineEntry:
    description: Single event in an incident timeline
    fields:
      time:
        type: string
        format: iso8601
        description: Event timestamp
      event:
        type: string
        description: Event type identifier
      detail:
        type: string
        max: 512
        description: Human-readable event description

  Runbook:
    description: Remediation procedure definition
    fields:
      name:
        type: string
        max: 64
        description: Unique runbook identifier
      description:
        type: string
        max: 256
        description: What this runbook remediates
      trigger:
        type: object
        fields: {alert_type: string, severity: array}
        description: Conditions that activate this runbook
      steps:
        type: array
        items: RunbookStep
        description: Ordered remediation steps
      escalation:
        type: object
        fields: {message: string, severity: string, notify: array}
        description: Escalation configuration

  RunbookStep:
    description: Single step in a runbook
    fields:
      name:
        type: string
        max: 64
        description: Step identifier
      action:
        type: string
        description: Action to execute
      timeout:
        type: int
        default: 30
        unit: seconds
        description: Step timeout
      requires_approval:
        type: bool
        default: false
        description: Whether operator approval is needed
      retry:
        type: int
        default: 0
        description: Retries on failure
      on_success:
        type: string
        enum: [next, auto_resolve, verify_recovery]
        description: Action on success
      on_failure:
        type: string
        enum: [next, escalate]
        description: Action on failure

  PostIncidentReport:
    description: Generated after incident resolution
    fields:
      incident_id:
        type: string
        description: Parent incident
      severity:
        type: string
        description: Incident severity
      duration_seconds:
        type: int
        description: Detection-to-resolution time
      root_cause:
        type: string
        description: Identified root cause
      resolution:
        type: string
        enum: [auto_resolved, operator_resolved, escalated]
        description: How the incident was resolved
      runbook_used:
        type: string
        optional: true
        description: Runbook executed
      steps_executed:
        type: int
        description: Total steps attempted
      steps_succeeded:
        type: int
        description: Steps completed successfully
      recommendations:
        type: array
        items: string
        description: Improvement recommendations
```

## Capabilities

`agent:message`, `storage:read`, `storage:write`

## HandleMessage Actions

| Action | Input | Output | Description |
|--------|-------|--------|-------------|
| process_alert | AlertEvent | IncidentAction | Receive alert, correlate, and determine response |
| execute_runbook | RunbookRequest | RunbookResult | Execute a specific runbook for an incident |
| get_incidents | IncidentQuery | IncidentList | Query active and resolved incidents |
| get_incident | {incident_id} | Incident | Get full incident details with timeline |
| acknowledge | {incident_id, operator} | Incident | Operator acknowledges incident |
| resolve | {incident_id, operator, resolution} | Incident | Operator resolves incident |
| escalate | {incident_id, reason} | Incident | Escalate incident to next tier |
| get_runbooks | {} | RunbookList | List available runbooks |

## Incident Lifecycle

```
DETECTED → TRIAGING → RUNBOOK_EXECUTING → AWAITING_OPERATOR → RESOLVED
                                        → AUTO_RESOLVED
                     → ESCALATED → AWAITING_OPERATOR → RESOLVED
```

| State | Description |
|-------|-------------|
| DETECTED | Alert received, incident created |
| TRIAGING | Correlating with other alerts and system state |
| RUNBOOK_EXECUTING | Automated runbook in progress |
| AUTO_RESOLVED | Runbook resolved the issue without human intervention |
| ESCALATED | Automated remediation insufficient, operator needed |
| AWAITING_OPERATOR | Waiting for human acknowledgment or action |
| RESOLVED | Incident closed by operator or auto-resolution confirmed |

## Alert Correlation

When an alert arrives, the agent correlates it with existing
incidents to avoid duplicate incident creation:

```
1. Hash alert (source + type + target)
2. Search active incidents for matching hash
3. If match found:
   a. Add alert to existing incident timeline
   b. Update severity if new alert is higher
   c. Skip runbook (already in progress)
4. If no match:
   a. Create new incident
   b. Look up matching runbook
   c. Begin triage
```

### Correlation Window

Alerts within a configurable window (default: 5 minutes) for the
same source and type are grouped into a single incident.

## Runbooks

Runbooks are predefined remediation procedures. Each runbook has
conditions (when to execute), steps (what to do), and escalation
criteria (when to give up and call a human).

### Runbook Structure

```yaml
runbook:
  name: agent-offline
  description: Remediate an offline agent
  trigger:
    alert_type: agent_offline
    severity: [critical, high]
  
  steps:
    - name: verify
      action: check_agent_health
      description: Confirm agent is actually offline (not a false alarm)
      timeout: 10
      on_success: next
      on_failure: escalate

    - name: check_dependencies
      action: check_agent_dependencies
      description: Verify storage, network, and upstream services
      timeout: 15
      on_success: next
      on_failure: escalate

    - name: restart
      action: request_agent_restart
      description: Request orchestrator to restart the agent
      timeout: 30
      requires_approval: false    # Safe automated action
      on_success: verify_recovery
      on_failure: escalate

    - name: verify_recovery
      action: check_agent_health
      description: Confirm agent recovered after restart
      timeout: 30
      retry: 3
      retry_delay: 10
      on_success: auto_resolve
      on_failure: escalate

  escalation:
    message: "Agent {agent_name} failed to recover after automated restart"
    severity: critical
    notify: [on-call, platform-admin]
```

### Built-in Runbooks

| Runbook | Trigger | Automated Steps | Escalation |
|---------|---------|----------------|------------|
| agent-offline | Agent unreachable | Health check → dependency check → restart request → verify | Agent won't recover |
| agent-degraded | Agent responding slowly | Health check → check load → check dependencies | Persistent degradation |
| workflow-failed | Domain workflow failure | Check agent status → check inputs → retry workflow | Repeated failures |
| site-unreachable | Uptime check failure | DNS check → TLS check → alternate path check | Confirmed outage |
| performance-regression | Performance threshold breach | Check recent deployments → check resource usage | Sustained regression |
| tls-expiring | TLS certificate <7 days | Check auto-renewal status → alert operator | <3 days remaining |
| federation-peer-down | Federation peer unreachable | Check peer health endpoint → check network → notify operator | Peer unresponsive |
| storage-failure | Storage write/read errors | Check disk space → check connections → failover check | Persistent errors |
| approval-backlog | Pending approvals exceed threshold | Notify approvers → escalate to admin | Backlog growing |

### Custom Runbooks

Operators can add custom runbooks via the admin gateway:

```
POST /v1/admin/runbooks
PUT /v1/admin/runbooks/:name
DELETE /v1/admin/runbooks/:name
GET /v1/admin/runbooks
GET /v1/admin/runbooks/:name
```

Custom runbooks follow the same YAML structure and can reference any
action the incident-response agent supports.

## Runbook Actions

Actions are the atomic operations a runbook step can perform:

| Action | Description | Approval Required |
|--------|-------------|------------------|
| check_agent_health | Query agent's /v1/health endpoint | No |
| check_agent_dependencies | Verify agent's required services | No |
| request_agent_restart | Ask orchestrator to restart an agent | No (safe) |
| check_dns | Resolve hostname and verify | No |
| check_tls | Verify TLS certificate status | No |
| retry_workflow | Re-dispatch a failed workflow | No |
| notify_operator | Send notification to operator | No |
| run_diagnostic | Execute diagnostic commands via CLI | No |
| request_failover | Request storage or service failover | Yes |
| request_rollback | Request deployment rollback | Yes |
| modify_rate_limits | Temporarily adjust rate limits | Yes |

Actions marked "Approval Required" pause the runbook and wait for
operator confirmation before proceeding.

## Incident Timeline

Every incident maintains a chronological timeline of events:

```json
{
  "incident_id": "inc_20260425_001",
  "severity": "critical",
  "state": "runbook_executing",
  "created_at": "2026-04-25T10:00:00Z",
  "source": {
    "alert_type": "agent_offline",
    "agent": "seo-analyzer",
    "domain": "seo"
  },
  "timeline": [
    {"time": "2026-04-25T10:00:00Z", "event": "incident_created", "detail": "Alert: seo-analyzer offline"},
    {"time": "2026-04-25T10:00:01Z", "event": "runbook_started", "detail": "Executing: agent-offline"},
    {"time": "2026-04-25T10:00:02Z", "event": "step_completed", "detail": "verify: confirmed offline"},
    {"time": "2026-04-25T10:00:05Z", "event": "step_completed", "detail": "check_dependencies: all healthy"},
    {"time": "2026-04-25T10:00:06Z", "event": "step_started", "detail": "restart: requesting restart"}
  ],
  "runbook": "agent-offline",
  "current_step": "restart",
  "alerts": ["alert_001", "alert_002"]
}
```

## Post-Incident Report

When an incident is resolved, the agent generates a post-incident
report:

```json
{
  "incident_id": "inc_20260425_001",
  "severity": "critical",
  "duration_seconds": 180,
  "root_cause": "Agent process crashed due to OOM",
  "resolution": "auto_resolved",
  "runbook_used": "agent-offline",
  "steps_executed": 4,
  "steps_succeeded": 4,
  "timeline_summary": "Detected → verified → dependencies OK → restarted → recovered",
  "recommendations": [
    "Increase agent memory limit",
    "Add memory usage alerting threshold"
  ]
}
```

Reports are stored and accessible via the admin gateway for trend
analysis and process improvement.

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
        trigger: runbooks_loaded
        validates: at least one runbook available
      - from: active
        to: degraded
        trigger: storage_error
        validates: retry count < max per patterns/retry
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: storage write succeeds
      - from: active
        to: degraded
        trigger: alerting_unavailable
        validates: alert.fired subscription lost
      - from: degraded
        to: active
        trigger: alerting_restored
        validates: alert.fired subscription reestablished
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
        validates: no active runbooks executing OR drain timeout (60s) elapsed

  entity.Incident:
    initial: detected
    transitions:
      - from: detected
        to: triaging
        trigger: correlation_complete
        validates: correlation hash computed, alert grouped
      - from: triaging
        to: runbook_executing
        trigger: runbook_matched
        validates: matching runbook found and started
      - from: triaging
        to: escalated
        trigger: no_runbook_available
        validates: no matching runbook for alert type
      - from: runbook_executing
        to: auto_resolved
        trigger: runbook_success
        validates: all steps succeeded, verification passed
      - from: runbook_executing
        to: escalated
        trigger: runbook_failed
        validates: step failed and on_failure = escalate
      - from: auto_resolved
        to: resolved
        trigger: stability_confirmed
        validates: no recurrence within auto_resolve_timeout
      - from: auto_resolved
        to: triaging
        trigger: recurrence_detected
        validates: same correlation hash fires within window
      - from: escalated
        to: awaiting_operator
        trigger: notification_sent
        validates: operator notified via alerting agent
      - from: awaiting_operator
        to: resolved
        trigger: operator_resolves
        validates: resolution summary provided
      - from: awaiting_operator
        to: runbook_executing
        trigger: operator_retries_runbook
        validates: operator explicitly requests retry
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/incident-response/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Open flat-file JSONL storage directory
  Validates:   Directory writable, existing files parseable
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE

Step 4 — Load Runbooks
  Action:      Parse built-in runbooks + custom runbooks from storage
  Validates:   Each runbook has valid trigger, steps, and escalation
  On Fail:     Log invalid runbooks, continue with valid subset

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 6 — Subscribe to Events
  Action:      Subscribe to: alert.fired, alert.resolved,
               system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT with SUBSCRIPTION_FAILED

Step 7 — Load Active Incidents
  Action:      Read incidents.jsonl for non-resolved incidents
  Validates:   All records parse as Incident type
  On Fail:     Enter degraded state, log warning

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9760, runbooks_loaded: N, active_incidents: N}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Alerts
  Action:      Unsubscribe from alert.fired, return 503 for new requests

Step 3 — Drain Active Runbooks
  Action:      Wait for executing runbook steps to complete (up to 60s)
  On Timeout:  Mark executing runbooks as interrupted, escalate all

Step 4 — Persist State
  Action:      Flush in-memory incident state to storage
  Validates:   All active incidents persisted

Step 5 — Deregister
  Action:      DELETE /v1/register

Step 6 — Exit
  Log: lifecycle.stopped {uptime_seconds, active_incidents_preserved}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - alerting subscription active
      - storage writable
      - active_runbooks < 80% of max_concurrent_runbooks
    response:
      status: healthy
      details: {active_incidents, active_runbooks, runbooks_loaded, storage}

  degraded:
    conditions:
      - alerting subscription lost (operating on direct messages only)
      - storage errors (retrying)
    response:
      status: degraded
      details: {reason, last_error, retry_count}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "incident-response"`:

```
1. Parse new blueprint, verify against schema
2. Reload runbook definitions from new blueprint
3. Validate all active incidents against new state machine
4. Apply new configuration values
5. Log: lifecycle.version_updated {from, to}
```

---

## Triggers

```yaml
triggers:
  - name: alert_fired
    type: event
    topic: alert.fired
    description: Incoming alert from alerting agent — primary trigger

  - name: alert_resolved
    type: event
    topic: alert.resolved
    description: External resolution signal — confirm incident closure

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "incident-response"
    description: Self-update if incident-response blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [process_alert, execute_runbook, get_incidents, get_incident,
             acknowledge, resolve, escalate, get_runbooks]
    description: Agent-to-agent and operator actions
```

---

## Actions

### process_alert

**Purpose:** Receive an alert event, correlate with existing incidents, and determine response.

**Input:** `AlertEvent` — `{alert_id, source, type, severity, target, message, timestamp}`

**Processing:**

```
1. Compute correlation_hash = hash(source + type + target)
2. Search active incidents for matching correlation_hash
3. If match found within correlation_window:
   a. Append alert to incident.alerts[]
   b. Add TimelineEntry: alert_correlated
   c. Update severity if new alert is higher
   d. Return existing incident (skip runbook — already in progress)
4. If no match:
   a. Create new Incident (state: detected)
   b. Transition: detected → triaging
   c. Match runbook by alert_type + severity
   d. If runbook found → transition: triaging → runbook_executing
   e. If no runbook → transition: triaging → escalated
5. Publish: incident.created or incident.updated
6. Return IncidentAction {incident_id, action_taken}
```

**Output:** `{incident_id, action_taken: "created"|"correlated"|"runbook_started"|"escalated"}`

**Errors:** `STORAGE_ERROR` (transient), `INVALID_ALERT` (permanent)

---

### execute_runbook

**Purpose:** Execute a specific runbook against an incident.

**Input:** `{incident_id, runbook_name}`

**Processing:**

```
1. Look up incident and runbook
2. Validate incident state allows runbook execution
3. Execute steps sequentially:
   For each step:
     a. Check requires_approval — pause if true
     b. Execute step.action with step.timeout
     c. On success → follow on_success path
     d. On failure → retry up to step.retry times → follow on_failure path
4. Record result in incident timeline
5. If all steps succeed → transition to auto_resolved
6. If escalation triggered → transition to escalated
```

**Output:** `RunbookResult {incident_id, runbook, steps_executed, outcome}`

**Errors:** `NOT_FOUND` (permanent), `INVALID_STATE` (permanent), `STEP_TIMEOUT` (transient)

---

### acknowledge

**Purpose:** Operator acknowledges an incident.

**Input:** `{incident_id, operator}`

**Processing:**

```
1. Validate incident exists and state is escalated or awaiting_operator
2. Record operator assignment
3. Add TimelineEntry: operator_acknowledged
4. Publish: incident.acknowledged
```

**Output:** Updated `Incident`

---

### resolve

**Purpose:** Operator resolves an incident.

**Input:** `{incident_id, operator, resolution}`

**Processing:**

```
1. Validate incident exists, state allows resolution
2. Transition: * → resolved
3. Set resolved_at, resolution summary
4. Generate PostIncidentReport
5. Publish: incident.resolved
```

**Output:** Updated `Incident` + `PostIncidentReport`

---

### escalate

**Purpose:** Manually escalate an incident to next tier.

**Input:** `{incident_id, reason}`

**Processing:**

```
1. Validate incident exists
2. Transition: * → escalated (if not already)
3. Add TimelineEntry: manual_escalation
4. Notify on-call and platform-admin via alerting agent
5. Publish: incident.escalated
```

**Output:** Updated `Incident`

---

## Execute Workflow

The core incident processing loop runs reactively on alert events:

```
Phase 1 — Alert Reception
  Trigger:   alert.fired event received
  Action:    Parse AlertEvent from event payload
  Validate:  Required fields present (alert_id, source, type, severity)

Phase 2 — Correlation
  Action:    Compute correlation_hash = hash(source + type + target)
  Query:     Search active incidents WHERE correlation_hash matches
             AND created_at > (now - config.correlation_window)
  If match:  Append to existing incident, skip to Phase 6
  If new:    Create Incident record, proceed

Phase 3 — Runbook Selection
  Action:    Match alert_type and severity against runbook triggers
  If match:  Select highest-priority matching runbook
  If none:   Escalate immediately → skip to Phase 5

Phase 4 — Runbook Execution
  For each step in runbook.steps:
    a. Execute step action with timeout
    b. Record step result in timeline
    c. Follow on_success / on_failure path
    d. If on_failure = escalate → break to Phase 5
  If all steps succeed:
    Transition: runbook_executing → auto_resolved
    Start stability timer (config.auto_resolve_timeout)
    Skip to Phase 6

Phase 5 — Escalation
  Action:    Transition to escalated
  Notify:    Send to on-call via alerting agent
  Timeline:  Record escalation reason and notified parties

Phase 6 — State Persistence
  Action:    Append updated Incident to incidents.jsonl
  Emit:      Metrics (incident_total, incident_active)
  Publish:   Appropriate incident.* event
```

---

## Collaboration

```yaml
events_published:
  - topic: incident.created
    payload: {incident_id, severity, source, correlation_hash}
    when: New incident created from alert

  - topic: incident.updated
    payload: {incident_id, severity, state, alerts_count}
    when: Existing incident updated with correlated alert

  - topic: incident.escalated
    payload: {incident_id, severity, reason, runbook}
    when: Incident escalated to operator

  - topic: incident.acknowledged
    payload: {incident_id, operator}
    when: Operator acknowledges incident

  - topic: incident.resolved
    payload: {incident_id, resolution, duration_seconds}
    when: Incident resolved (auto or operator)

  - topic: incident.runbook.started
    payload: {incident_id, runbook_name}
    when: Runbook execution begins

  - topic: incident.runbook.completed
    payload: {incident_id, runbook_name, outcome}
    when: Runbook execution finishes

events_subscribed:
  - topic: alert.fired
    payload: AlertEvent
    action: Process alert, create or update incident

  - topic: alert.resolved
    payload: {alert_id, source}
    action: Confirm resolution of correlated incident

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "incident-response"
    action: Self-update procedure

direct_messages:
  - target: alerting
    action: send_notification
    when: Escalation requires operator notification
    reason: Alerting owns notification routing
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Runbooks execute and auto-resolve without operator input
  supervised:    Runbooks execute; critical incidents always escalate
  manual-only:   All incidents escalate to operator immediately

overridable_behaviors:
  - behavior: automatic_runbook_execution
    default: enabled
    override: Set WL_INCIDENT_AUTO_RUNBOOK=false
    audit: logged

  - behavior: auto_resolution
    default: enabled
    override: Set WL_INCIDENT_AUTO_RESOLVE=false
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: acknowledge
    description: Operator acknowledges incident
    allowed: operator

  - action: resolve
    description: Operator resolves incident with summary
    allowed: operator

  - action: escalate
    description: Force-escalate any incident
    allowed: operator

  - action: add_runbook
    description: Add or update custom runbook
    allowed: operator

  - action: delete_runbook
    description: Remove custom runbook
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
    - MUST NOT restart agents directly — only request via orchestrator
    - MUST NOT modify data owned by other agents
    - Runbook actions limited to declared action set (no arbitrary execution)

  forbidden_actions:
    - MUST NOT execute shell commands or arbitrary code
    - MUST NOT bypass approval gates on requires_approval steps
    - MUST NOT auto-resolve critical-severity incidents without verification
    - MUST NOT delete incidents — only transition to resolved

  resource_limits:
    memory: 256 MB (process limit)
    max_active_incidents: 10000
    max_concurrent_runbooks: 10
    max_timeline_entries_per_incident: 500
    incident_storage: governed by config.history_retention
```

---

## Configuration
  correlation_window: 300      # seconds — group related alerts
  auto_resolve_timeout: 600    # seconds — auto-close if stable after resolution
  max_runbook_duration: 300    # seconds — max time for a runbook to complete
  escalation_timeout: 900      # seconds — escalate if no operator response
  history_retention: 90        # days — keep resolved incidents
```

---

## Observability
|--------|------|-------------|
| incident_total | counter | Incidents by severity, state, and runbook |
| incident_duration_seconds | histogram | Time from detection to resolution |
| incident_active | gauge | Currently active incidents by severity |
| runbook_execution_total | counter | Runbook executions by name and result |
| runbook_step_duration_seconds | histogram | Time per runbook step |
| runbook_auto_resolve_total | counter | Incidents auto-resolved without human |
| runbook_escalation_total | counter | Incidents escalated to operators |

---

## Error Handling
|-------|---------|
| Runbook step fails | Move to on_failure path (usually escalate) |
| Runbook timeout | Cancel remaining steps, escalate to operator |
| Alerting agent unavailable | Queue notifications, retry when available |
| Storage unavailable | Continue operation in-memory, persist when storage recovers |
| Concurrent runbooks for same target | Queue second runbook, execute after first completes |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["alerting"]
      description: Send escalation notifications via alerting agent

    - capability: storage:read
      resources: [incidents, runbooks, reports]
      description: Read own data stores

    - capability: storage:write
      resources: [incidents, runbooks, reports]
      description: Write own data stores

  data_sensitivity:
    - data: Incident details
      classification: high
      handling: Contains system internals and potential vulnerability info

    - data: Runbook definitions
      classification: medium
      handling: Remediation procedures are sensitive operational data

    - data: Post-incident reports
      classification: high
      handling: Root cause analysis may reveal security weaknesses

    - data: Operator identities
      classification: medium
      handling: Logged in audit trail, not exposed in events

  access_control:
    - caller: alerting agent
      actions: [process_alert]
      note: Primary trigger source

    - caller: Any registered agent
      actions: [get_incidents, get_incident, get_runbooks]
      note: Read-only incident status

    - caller: Operator (auth token with operator role)
      actions: [process_alert, execute_runbook, get_incidents, get_incident,
                acknowledge, resolve, escalate, get_runbooks,
                add_runbook, delete_runbook]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Alert creates new incident
    trigger: alert.fired
    input:
      alert_id: alert_001
      source: health-monitor
      type: agent_offline
      severity: critical
      target: seo-analyzer
    expected:
      incident created with state: detected
      correlation_hash computed
      runbook "agent-offline" matched and started
    validates:
      - Incident record persisted to storage
      - incident.created event published
      - State transition: detected → triaging → runbook_executing

  - name: Runbook auto-resolves incident
    action: execute_runbook
    input: {incident_id: inc_001, runbook_name: agent-offline}
    precondition: All runbook steps succeed
    expected:
      state: auto_resolved
      PostIncidentReport generated
    validates:
      - All steps recorded in timeline
      - incident.resolved event published after stability timeout

  - name: Operator resolves escalated incident
    action: resolve
    input: {incident_id: inc_002, operator: admin@example.com, resolution: "Increased memory limit"}
    expected:
      state: resolved
      PostIncidentReport generated
    validates:
      - Resolution summary stored
      - incident.resolved event published
```

### Error Cases

```yaml
  - name: Runbook step fails and escalates
    trigger: alert.fired with runbook that has failing step
    expected:
      state: escalated
      on_failure path followed
    validates:
      - Step failure recorded in timeline
      - Escalation notification sent via alerting agent

  - name: No matching runbook
    trigger: alert.fired with unknown alert_type
    expected:
      state: escalated
      no runbook execution attempted
    validates:
      - Incident created, immediately escalated
      - incident.escalated event published

  - name: Resolve non-existent incident
    action: resolve
    input: {incident_id: non_existent}
    expected_error: NOT_FOUND
```

### Edge Cases

```yaml
  - name: Duplicate alerts within correlation window
    trigger: Two alert.fired events with same source+type+target within 5 minutes
    expected:
      Single incident with 2 alerts
      Runbook not restarted
    validates:
      - correlation_hash deduplication works
      - Second alert appended to timeline

  - name: Concurrent runbooks for same target
    trigger: Two different alert types for same agent
    expected:
      Two separate incidents
      Second runbook queued until first completes
    validates:
      - max_concurrent_runbooks constraint respected

  - name: Storage unavailable during alert processing
    trigger: alert.fired while storage unreachable
    expected:
      Incident processed in-memory
      Persisted when storage recovers
    validates:
      - No alert lost
      - Agent enters degraded state
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: 3

  inter_agent:
    protocol: message-bus-only
    direct_http: forbidden
    routing: by agent name, never by instance address
    reason: >
      Message bus resolves agent names to healthy instances.
      During blue-green deploys, bus handles traffic shifting.

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: file lock with TTL
      leader: [runbook_execution, alert_correlation]
      follower: [health_reporting, action_handling, read_queries]
      promotion: automatic when leader lock expires
    state_sharing:
      mechanism: shared flat-file storage directory
      consistency_window: 5 seconds
      conflict_resolution: >
        Incident IDs are globally unique (timestamp + sequence).
        Leader election prevents duplicate runbook execution.
        Correlation hash prevents duplicate incident creation.

  event_handling:
    consumer_group: incident-response
    delivery: one-per-group
    description: >
      Bus delivers each alert.fired event to ONE instance in the
      "incident-response" consumer group. Prevents duplicate
      incident creation from the same alert.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same storage directory. Schema changes
      are additive-only during shadow phase.
    consumer_groups:
      shadow_phase: "incident-response@vN+1"
      after_cutover: "incident-response"
```

---

## Implementation Notes

- **Correlation hash**: Use SHA-256 of `source + "|" + type + "|" + target`.
  Truncate to 16 hex characters for storage efficiency.
- **Runbook isolation**: Each runbook step executes in its own timeout
  context. A hanging step does not block the entire agent.
- **Timeline append**: Timeline entries are append-only. Never modify
  existing entries. Cap at 500 entries per incident; older entries
  summarized into a single "history_truncated" entry.
- **Post-incident reports**: Generated asynchronously after resolution.
  Report generation failure does not block incident closure.
- **Persistence**: Active incidents MUST be persisted to durable storage.
  In-memory only is not acceptable — agent restarts MUST preserve
  active incident state.
- **Escalation timeout**: If no operator response within
  `config.escalation_timeout`, re-escalate with increased severity.
- **Custom runbooks**: Operators can add runbooks at runtime. Custom
  runbooks persist across restarts. Built-in runbooks cannot be
  deleted but can be overridden by custom runbooks with the same name.

---

## Verification Checklist

- [ ] Agent registers with orchestrator and receives WLT token
- [ ] Alert events are received and correlated into incidents
- [ ] Duplicate alerts within correlation window join existing incidents
- [ ] Runbooks execute steps in sequence with correct timeout handling
- [ ] Failed steps follow on_failure path (next or escalate)
- [ ] Approval-required steps pause and wait for operator
- [ ] Auto-resolved incidents confirm stability before closing
- [ ] Post-incident reports generate for all resolved incidents
- [ ] Custom runbooks can be added via admin API
- [ ] Incident timeline records all events chronologically
- [ ] Metrics emit for incidents, runbooks, and escalations
- [ ] Graceful degradation when alerting agent or storage is unavailable
- [ ] Dependencies declare version ranges and specific bindings
- [ ] on_change rules defined for all dependencies
- [ ] State machine transitions validated — no implicit states
- [ ] Startup sequence validation gates — each step has validates/on-fail
- [ ] Shutdown drains active runbooks before exit
- [ ] Scaling: inter-agent communication via message bus only
- [ ] Scaling: leader election prevents duplicate runbook execution
- [ ] Scaling: consumer group ensures one-per-alert delivery
- [ ] Override audit records who, what, when, why
- [ ] Constraints enforced — max_concurrent_runbooks, max_active_incidents
- [ ] Security: all endpoints require valid token
- [ ] Custom runbooks persist across restarts

Port: 9760
