<!-- blueprint
type: agent
kind: infrastructure
name: health-monitor
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/state-machine, patterns/scope, patterns/policy, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, agents/alerting]
depends_on: [alerting]
platform: any
tier: free
port: 9755
-->

# Health Monitor Agent

Internal infrastructure health monitoring for a Weblisk hub. Tracks
agent liveness, orchestrator health, domain controller status, storage
latency, federation peer reachability, and gateway responsiveness.

Unlike the health domain controller (which monitors external endpoints
like websites), the health-monitor agent monitors **the hub itself** —
the internal components that make up a running Weblisk server.

## Overview

Every Weblisk hub needs to know whether its own components are healthy.
The health-monitor agent provides this by periodically probing all
registered agents, domain controllers, storage backends, and federation
peers. It maintains a real-time health map, computes an aggregate hub
health score, and routes alerts to the alerting agent when components
degrade or fail.

The health-monitor runs on a configurable schedule (default: every 30
seconds) and exposes a health summary endpoint for the admin dashboard,
CLI interrogation, and federation advertisement.
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
        - path: /v1/describe
          methods: [POST]
          response_fields: [name, version, capabilities]
      types:
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: MessageEnvelope
          fields_used: [from, to, action, payload, trace_id]
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
      actions:
        - name: alert
          payload: {severity, source, title, message, context, timestamp}
    on_change:
      compatible: validate
      breaking: version-bump
      removed: degrade-alerting

extends:
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
          parameters: [engine, tables, indexes]
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

depends_on:
  - agent: alerting
    reason: Dispatches health state change alerts
    on_unavailable: degrade (continue monitoring, log alerts locally)
```

---

## Configuration

```yaml
config:
  check_interval:
    type: int
    default: 30
    env: WL_HEALTHMON_CHECK_INTERVAL
    min: 5
    max: 300
    unit: seconds
    description: Time between full health sweeps

  response_timeout:
    type: int
    default: 5000
    env: WL_HEALTHMON_RESPONSE_TIMEOUT
    min: 500
    max: 30000
    unit: milliseconds
    description: Max wait for a probe response

  degraded_threshold:
    type: int
    default: 500
    env: WL_HEALTHMON_DEGRADED_THRESHOLD
    min: 100
    max: 10000
    unit: milliseconds
    description: Latency above this marks component as degraded

  failure_threshold:
    type: int
    default: 3
    env: WL_HEALTHMON_FAILURE_THRESHOLD
    min: 1
    max: 20
    description: Consecutive failures before marking offline

  alert_on_degraded:
    type: bool
    default: true
    env: WL_HEALTHMON_ALERT_DEGRADED
    description: Fire alert when component degrades

  alert_on_offline:
    type: bool
    default: true
    env: WL_HEALTHMON_ALERT_OFFLINE
    description: Fire alert when component goes offline

  alert_on_recovery:
    type: bool
    default: true
    env: WL_HEALTHMON_ALERT_RECOVERY
    description: Fire alert when component recovers

  snapshot_retention:
    type: int
    default: 604800
    env: WL_HEALTHMON_SNAPSHOT_RETENTION
    min: 3600
    unit: seconds
    description: Health snapshot retention (default 7 days)
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  ComponentHealth:
    description: Health status of a single component
    fields:
      component_id:
        type: string
        description: Unique component identifier (e.g. agents/sync)
      component_type:
        type: string
        enum: [agent, domain, storage, gateway, federation_peer]
        description: Component category
      state:
        type: string
        enum: [unknown, online, degraded, offline]
        description: Current health state
      latency_ms:
        type: int
        optional: true
        description: Latest probe latency
      last_check:
        type: int64
        description: Timestamp of last probe
      consecutive_failures:
        type: int
        default: 0
        description: Number of consecutive failed probes
      uptime_24h:
        type: float
        optional: true
        description: 24-hour uptime percentage

  HealthSnapshot:
    description: Point-in-time health snapshot for historical analysis
    fields:
      snapshot_id:
        type: string
        format: uuid-v7
        description: Unique snapshot identifier
      timestamp:
        type: int64
        description: When snapshot was taken
      hub_score:
        type: int
        min: 0
        max: 100
        description: Aggregate hub health score
      hub_state:
        type: string
        enum: [online, degraded, offline]
        description: Derived hub state
      components:
        type: object
        description: Map of component_id to ComponentHealth

  HealthAlert:
    description: Alert dispatched on state change
    fields:
      component_id:
        type: string
        description: Component that changed state
      previous_state:
        type: string
        enum: [unknown, online, degraded, offline]
      current_state:
        type: string
        enum: [unknown, online, degraded, offline]
      latency_ms:
        type: int
        optional: true
      severity:
        type: string
        enum: [info, warning, critical]
      message:
        type: string
        description: Human-readable state change description
      timestamp:
        type: int64
```

---

## Storage

```yaml
storage:
  engine: sqlite

  tables:
    health_snapshots:
      source_type: HealthSnapshot
      primary_key: snapshot_id
      indexes:
        - name: idx_snapshot_time
          fields: [timestamp]
          type: btree
          description: Time-ordered snapshot lookup
        - name: idx_snapshot_score
          fields: [hub_score]
          type: btree

  retention:
    health_snapshots:
      policy: config.snapshot_retention
      cleanup: automatic every sweep cycle

  backup:
    health_snapshots:
      frequency: daily
      format: JSON export (last 24 hours)
      path: .weblisk/backups/health-monitor/snapshots_{ISO8601}.json
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
        trigger: first_sweep_completed
        validates: at least one component probed successfully
      - from: active
        to: degraded
        trigger: storage_error
        validates: snapshot writes failing
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: snapshot write succeeds
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
        validates: current sweep finished or timeout

  entity.ComponentHealth:
    initial: unknown
    transitions:
      - from: unknown
        to: online
        trigger: successful_probe
        validates: response 2xx AND latency < degraded_threshold
      - from: unknown
        to: offline
        trigger: failed_probe
        validates: no response or error response
      - from: online
        to: degraded
        trigger: high_latency_probe
        validates: response 2xx AND latency >= degraded_threshold
      - from: online
        to: offline
        trigger: consecutive_failures_exceeded
        validates: consecutive_failures >= config.failure_threshold
        side_effect: dispatch critical alert to alerting agent
      - from: degraded
        to: online
        trigger: latency_recovered
        validates: latency < degraded_threshold
        side_effect: dispatch recovery alert
      - from: degraded
        to: offline
        trigger: consecutive_failures_exceeded
        validates: consecutive_failures >= config.failure_threshold
        side_effect: dispatch critical alert
      - from: offline
        to: online
        trigger: successful_probe
        validates: response 2xx AND latency < degraded_threshold
        side_effect: dispatch recovery alert, reset consecutive_failures
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults
  Pre-check:   Process has read access to environment
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/health-monitor/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x → EXIT with STORAGE_UNREACHABLE
  Backout:     Close partial connection

Step 4 — Validate Schema
  Action:      Verify health_snapshots table
  Pre-check:   Step 3 validated
  Validates:   Table exists with correct schema
  On Fail:     Run migration → if fails EXIT with MIGRATION_FAILED
  Backout:     Reverse migration

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 6 — Subscribe to Events
  Action:      Subscribe to: system.agent.registered,
               system.agent.deregistered, system.shutdown,
               system.blueprint.changed, health.check
  Pre-check:   Step 5 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT
  Backout:     Unsubscribe all, deregister, close storage

Step 7 — Build Component Registry
  Action:      Query orchestrator for all registered agents and domains
  Pre-check:   Step 5 validated
  Validates:   Component list retrieved
  On Fail:     Start with empty registry, populate on first events
  Backout:     None

Step 8 — Start Health Sweep Timer
  Action:      Begin interval timer at config.check_interval
  Pre-check:   Steps 1-7 validated
  Validates:   First sweep completes
  On Fail:     Stop timer → reverse all → EXIT
  Backout:     Full reverse

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9755, components_monitored: N}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Sweep Timer
  Action:      Cancel interval timer
  Validates:   No new sweeps start

Step 3 — Complete Current Sweep
  Action:      If sweep in progress, wait for completion (up to 30s)
  Validates:   Current sweep finished or timed out

Step 4 — Write Final Snapshot
  Action:      Persist current health map to storage
  Validates:   Snapshot written

Step 5 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges

Step 6 — Close Storage
  Action:      Close database connection

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, sweeps_completed, alerts_fired}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - sweep_timer = running
      - storage = connected
    response:
      status: healthy
      details: {sweep_timer, components_monitored, hub_score, last_sweep}

  degraded:
    conditions:
      - storage errors (snapshots not persisting)
      - alerting agent unavailable
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retries
      - sweep timer stopped
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

```
Step 1 — Validate new blueprint
Step 2 — Check migration requirements
Step 3 — Execute migration (pause sweeps, migrate, resume)
Step 4 — Reload configuration (thresholds, intervals)
Final:  Log lifecycle.version_updated {from, to}
```

---
## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["http://localhost:*"]},
    {"name": "database:read", "resources": ["agent_registry", "health_snapshots"]},
    {"name": "database:write", "resources": ["health_snapshots"]}
  ],
  "inputs": [
    {"name": "health_check_request", "type": "json", "description": "Optional target filter for on-demand checks"}
  ],
  "outputs": [
    {"name": "health_report", "type": "json", "description": "Current hub health state with per-component status"}
  ],
  "collaborators": ["alerting", "cron"]
}
```

### Trigger Summary

| Trigger | Description |
|---------|-------------|
| Schedule: `*/30 * * * * *` | Every 30 seconds — full health sweep |
| Event: `health.check` | On-demand health check (from admin/CLI) |
| Event: `agent.registered` | New agent registered — add to monitor set |
| Event: `agent.deregistered` | Agent removed — remove from monitor set |

## HandleMessage Actions

> **Note:** Formal action specifications with input/output schemas are
> defined in the Actions section below. This table provides a quick
> reference.

| Action | Source | Description |
|--------|--------|-------------|
| check-all | Cron/Admin | Run full health sweep of all components |
| check-agent | Admin/CLI | Check a specific agent by name |
| check-domain | Admin/CLI | Check a specific domain controller |
| check-storage | Admin/CLI | Probe storage backend latency and availability |
| check-federation | Admin/CLI | Check federation peer reachability |
| check-gateway | Admin/CLI | Verify gateway is accepting requests |
| get-health-map | Admin/CLI | Return current health state of all components |
| get-health-history | Admin/CLI | Return health snapshots over a time range |
| get-hub-score | Admin/CLI/Federation | Return aggregate hub health score |
| configure | Admin | Update check intervals, thresholds, alert rules |

## Health Check Protocol

All health checks follow the same probe pattern:

```
1. SEND probe request to target
   - Agents: POST /v1/describe (already required by protocol/spec)
   - Domains: POST /v1/describe (domain manifest)
   - Storage: read/write test record
   - Federation: GET /v1/federation/status on peer URL
   - Gateway: HEAD / on gateway URL

2. MEASURE response
   - latency_ms: time from request to response
   - status: HTTP status code (or connection error)
   - healthy: status 2xx AND latency < threshold

3. UPDATE health map entry
   - Record timestamp, latency, status, healthy flag
   - Update consecutive_failures counter
   - Update state: online → degraded → offline

4. EVALUATE alert thresholds
   - If consecutive_failures >= threshold → fire alert
   - If latency > degraded_threshold → fire degraded alert
   - If component returns to healthy → fire recovery alert
```

### Component States

| State | Condition | Description |
|-------|-----------|-------------|
| online | Healthy response within latency threshold | Component operating normally |
| degraded | Healthy response but latency > degraded_threshold | Component slow but functional |
| offline | No response or error response | Component unreachable or failing |
| unknown | No check performed yet | Component registered but not yet probed |

### State Transitions

```
unknown → online      First successful probe
unknown → offline     First failed probe
online → degraded     Latency exceeds degraded_threshold
online → offline      consecutive_failures >= failure_threshold
degraded → online     Latency returns below degraded_threshold
degraded → offline    consecutive_failures >= failure_threshold
offline → online      Successful probe after failures
```

## Health Map

The health-monitor maintains a real-time map of all components:

```json
{
  "hub_id": "my-hub",
  "timestamp": 1712160000,
  "hub_score": 94,
  "hub_state": "online",
  "components": {
    "orchestrator": {
      "state": "online",
      "latency_ms": 2,
      "last_check": 1712160000,
      "consecutive_failures": 0,
      "uptime_24h": 100.0
    },
    "agents": {
      "alerting": {
        "state": "online",
        "latency_ms": 5,
        "last_check": 1712160000,
        "consecutive_failures": 0,
        "port": 9752,
        "uptime_24h": 99.98
      },
      "sync": {
        "state": "degraded",
        "latency_ms": 850,
        "last_check": 1712160000,
        "consecutive_failures": 0,
        "port": 9751,
        "uptime_24h": 97.2
      }
    },
    "domains": {
      "seo": {
        "state": "online",
        "latency_ms": 12,
        "last_check": 1712160000,
        "consecutive_failures": 0,
        "port": 9700,
        "uptime_24h": 100.0
      }
    },
    "storage": {
      "state": "online",
      "read_latency_ms": 1,
      "write_latency_ms": 3,
      "last_check": 1712160000
    },
    "federation_peers": {
      "partner-hub": {
        "state": "online",
        "latency_ms": 45,
        "last_check": 1712160000,
        "peer_url": "https://partner.example.com/v1/federation"
      }
    },
    "gateway": {
      "state": "online",
      "latency_ms": 3,
      "last_check": 1712160000
    }
  }
}
```

## Hub Health Score

Aggregate hub health computed from component states:

| Component Type | Weight | Scoring |
|---------------|--------|---------|
| Orchestrator | 30% | 100 if online, 50 if degraded, 0 if offline |
| Agents (avg) | 25% | Average score across all registered agents |
| Domains (avg) | 20% | Average score across all registered domains |
| Storage | 15% | 100 if online, 50 if degraded, 0 if offline |
| Gateway | 10% | 100 if online, 50 if degraded, 0 if offline |

Hub score = weighted sum, clamped 0–100.

Federation peers are NOT included in the hub score — they are external
and their health is not the hub's responsibility. Peer health is
reported separately.

### Hub State Derivation

| Hub Score | Hub State |
|-----------|-----------|
| 90–100 | online |
| 50–89 | degraded |
| 0–49 | offline |

The hub state is advertised to federation peers and registries.

## Default Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| check_interval_seconds | 30 | Time between full health sweeps |
| response_timeout_ms | 5000 | Max wait for a probe response |
| degraded_threshold_ms | 500 | Latency above this → degraded |
| failure_threshold | 3 | Consecutive failures before offline |
| alert_on_degraded | true | Fire alert when component degrades |
| alert_on_offline | true | Fire alert when component goes offline |
| alert_on_recovery | true | Fire alert when component recovers |
| snapshot_retention_hours | 168 | Keep health snapshots for 7 days |

Thresholds are configurable per component type and per individual
component via the `configure` action.

## Alert Integration

When a component changes state, the health-monitor dispatches to the
alerting agent:

```json
{
  "action": "send",
  "payload": {
    "alert_type": "health_state_change",
    "component": "agents/sync",
    "previous_state": "online",
    "current_state": "degraded",
    "latency_ms": 850,
    "consecutive_failures": 0,
    "timestamp": 1712160000,
    "severity": "warning",
    "message": "Agent 'sync' degraded — latency 850ms exceeds threshold 500ms"
  }
}
```

Severity mapping:
- `info` — recovery (offline/degraded → online)
- `warning` — degradation (online → degraded)
- `critical` — failure (any → offline)

## Federation Health Advertisement

The hub score and state are included in federation status responses
and registry listings. This allows peers and registries to make
informed decisions about collaboration:

```json
{
  "hub_health": {
    "score": 94,
    "state": "online",
    "components_online": 8,
    "components_degraded": 1,
    "components_offline": 0,
    "last_check": 1712160000
  }
}
```

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| health_check_duration_seconds | histogram | Time to complete a probe by component type |
| health_check_total | counter | Probes by component, target, and result |
| health_state_changes_total | counter | State transitions by component and direction |
| hub_health_score | gauge | Current aggregate hub health score |
| component_latency_ms | gauge | Latest probe latency by component |
| component_uptime_ratio | gauge | 24-hour uptime ratio by component |
| health_alerts_fired_total | counter | Alerts dispatched by severity |

---

## Triggers

```yaml
triggers:
  - name: sweep_timer
    type: schedule
    interval: config.check_interval
    description: Full health sweep of all registered components

  - name: health_check_request
    type: event
    topic: health.check
    description: On-demand health check from admin or CLI

  - name: agent_registered
    type: event
    topic: system.agent.registered
    description: Add new agent to monitoring set

  - name: agent_deregistered
    type: event
    topic: system.agent.deregistered
    description: Remove agent from monitoring set

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "health-monitor"
    description: Self-update if health-monitor blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [check-all, check-agent, check-domain, check-storage,
             check-federation, check-gateway, get-health-map,
             get-health-history, get-hub-score, configure]
    description: Agent-to-agent and operator actions
```

---

## Actions

### check-all

Run full health sweep of all components.

**Purpose:** Probe all registered agents, domains, storage, gateway, and federation peers.

**Input:** `{}` (no parameters)

**Processing:**

```
1. Iterate component registry by type
2. For each component: send probe per Health Check Protocol
3. Update health map with results
4. Evaluate alert thresholds for state changes
5. Compute hub score
6. Write health snapshot to storage
7. Return health map summary
```

**Output:** `{hub_score: int, hub_state: string, components_checked: int, state_changes: int}`

**Errors:** `STORAGE_ERROR` (transient)

**Side Effects:** Updates health map, writes snapshot, may dispatch alerts.

---

### check-agent

Probe a specific agent.

**Purpose:** On-demand health check for a named agent.

**Input:** `{agent_name: string}`

**Output:** `{component_id, state, latency_ms, consecutive_failures}`

**Errors:** `NOT_FOUND` if agent not in registry.

---

### get-health-map

Return current health state of all components.

**Purpose:** Provide a complete view of hub health.

**Input:** `{}`

**Output:** Full health map (see Health Map section)

**Side Effects:** None (read-only).

---

### get-health-history

Return historical health snapshots.

**Purpose:** Query past health states for analysis.

**Input:** `{since: int64, until?: int64, limit?: int}`

**Output:** `{snapshots: HealthSnapshot[]}`

**Errors:** `INVALID_INPUT` if invalid time range.

---

### get-hub-score

Return aggregate hub health score.

**Purpose:** Provide a single number representing overall hub health.

**Input:** `{}`

**Output:** `{score: int, state: string, components_online, components_degraded, components_offline}`

---

### configure

Update thresholds or check intervals.

**Purpose:** Runtime configuration adjustment.

**Input:** `{component_id?: string, check_interval?, degraded_threshold?, failure_threshold?}`

**Output:** `{updated: true}`

**Manual Override:** Operator-only action.

---

## Execute Workflow

The core health sweep runs every `config.check_interval` seconds:

```
Phase 1 — Build Probe List
  Query:     Component registry (in-memory)
  Result:    List of components grouped by type

Phase 2 — Probe Components (parallel by type)
  For each component:
    Agents/Domains: POST /v1/describe, measure latency
    Storage:        Read/write test key (_health_check)
    Gateway:        HEAD / on gateway URL
    Federation:     GET /v1/federation/status on peer URL
  Result:    Probe response with latency, status code, healthy flag

Phase 3 — Update Health Map
  For each probe result:
    Update ComponentHealth state per state machine transitions
    Reset or increment consecutive_failures
    Update latency_ms and last_check

Phase 4 — Evaluate Alerts
  For each state change:
    If config.alert_on_degraded AND online → degraded: dispatch warning
    If config.alert_on_offline AND * → offline: dispatch critical
    If config.alert_on_recovery AND offline/degraded → online: dispatch info
  Dispatch via direct message to alerting agent

Phase 5 — Compute Hub Score
  Apply weighted formula per Hub Health Score table
  Derive hub_state from score thresholds

Phase 6 — Persist Snapshot
  Write HealthSnapshot to health_snapshots table
  Cleanup snapshots older than config.snapshot_retention

Phase 7 — Report
  Emit metrics: hub_health_score, component_latency_ms,
                health_check_duration_seconds
```

---

## Collaboration

```yaml
events_published:
  - topic: health.sweep.completed
    payload: {hub_score, hub_state, components_checked, state_changes}
    when: Health sweep completes

  - topic: health.component.state_changed
    payload: {component_id, previous_state, current_state, latency_ms}
    when: Component changes health state

  - topic: health.hub.state_changed
    payload: {previous_state, current_state, score}
    when: Aggregate hub state changes

events_subscribed:
  - topic: system.agent.registered
    payload: {agent_name, manifest}
    action: Add agent to monitoring set

  - topic: system.agent.deregistered
    payload: {agent_name}
    action: Remove agent from monitoring set

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "health-monitor"
    action: Self-update procedure

  - topic: health.check
    payload: {target?: string}
    action: On-demand health check

direct_messages:
  - target: alerting
    action: alert
    when: Component state changes and alert thresholds met
    reason: Requires reliable delivery of health alerts
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All probing, alerting, and scoring is autonomous
  supervised:    Probing automatic; threshold changes require operator
  manual-only:   All sweeps triggered manually

overridable_behaviors:
  - behavior: automatic_sweep
    default: enabled
    override: Stop sweep timer via pause_sweeps manual action
    audit: logged

  - behavior: alert_dispatch
    default: enabled
    override: Set alert_on_degraded/offline/recovery = false
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: check-all
    description: Trigger immediate full health sweep
    allowed: operator

  - action: check-agent
    description: Probe a specific agent
    allowed: operator

  - action: configure
    description: Update thresholds and intervals
    allowed: operator

  - action: pause_sweeps
    description: Stop automatic health sweeps
    allowed: operator

  - action: resume_sweeps
    description: Resume automatic health sweeps
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
    - MUST NOT modify data owned by other agents
    - MUST NOT send messages to agents other than alerting for alerts
    - Probe rate bounded by config.check_interval (no faster than 5s)

  forbidden_actions:
    - MUST NOT restart or stop other agents (monitoring only)
    - MUST NOT modify component state directly (only observes via probes)
    - MUST NOT probe itself (self-check paradox; orchestrator infers liveness)
    - MUST NOT block on alerting agent availability

  resource_limits:
    memory: 256 MB (process limit)
    health_snapshots: governed by config.snapshot_retention TTL
    concurrent_probes: 50 max parallel probe requests
    probe_timeout: config.response_timeout per probe
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Probe timeout | Mark component probe as failed. Increment consecutive_failures. |
| Probe connection refused | Mark offline. Agent likely not running. |
| Alerting agent unavailable | Log alert locally. Retry on next sweep. Do NOT block health monitoring. |
| Storage unavailable | Continue probing in-memory. Persist snapshots when storage recovers. |
| All components offline | Hub state → offline. Health-monitor itself remains running. |
| Self-check paradox | Health-monitor does NOT probe itself. Its liveness is inferred by the orchestrator receiving health reports. |

## Implementation Notes

- The health-monitor MUST NOT depend on any other agent to function.
  If the alerting agent is down, health-monitoring still runs — it just
  can't dispatch alerts until alerting recovers.
- Probes use the existing `/v1/describe` endpoint that every agent
  already implements per protocol/spec. No additional endpoints needed.
- Storage probes use a dedicated test key (`_health_check`) with TTL
  to avoid polluting the data store.
- The health map is kept in memory for fast access. Periodic snapshots
  are written to storage for historical analysis.

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send probe requests to any registered agent and alerts to alerting

    - capability: http:send
      resources: ["http://localhost:*", "https://*"]
      description: Probe local agents and federation peers

    - capability: database:read
      resources: [health_snapshots]
      description: Read own tables

    - capability: database:write
      resources: [health_snapshots]
      description: Write own tables

  data_sensitivity:
    - data: Component health status and latency
      classification: low
      handling: Logged freely, included in metrics

    - data: Hub health score
      classification: low
      handling: Advertised to federation peers

    - data: Agent manifest details (from /v1/describe)
      classification: medium
      handling: Cached in memory, not persisted in snapshots

  access_control:
    - caller: Any registered agent
      actions: [get-health-map, get-hub-score]

    - caller: Operator (auth token with operator role)
      actions: [check-all, check-agent, check-domain, check-storage,
                check-federation, check-gateway, get-health-map,
                get-health-history, get-hub-score, configure,
                pause_sweeps, resume_sweeps]

    - caller: Federation peer
      actions: [get-hub-score]
      note: Score only, not full health map

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Full sweep with all components online
    action: check-all
    input: {}
    expected:
      hub_score: 100
      hub_state: online
      components_checked: N
      state_changes: 0
    validates:
      - All components probed successfully
      - Hub score computed correctly
      - Snapshot written to storage

  - name: Get hub score
    action: get-hub-score
    input: {}
    expected: {score: 94, state: online}
    validates:
      - Weighted formula applied
      - State derived from score

  - name: Health history query
    action: get-health-history
    input: {since: 1712073600, limit: 10}
    expected: {snapshots: [...]}
    validates:
      - Snapshots ordered by timestamp DESC
```

### Error Cases

```yaml
  - name: Check non-existent agent
    action: check-agent
    input: {agent_name: nonexistent}
    expected_error: NOT_FOUND
    validates: Agent validated against registry

  - name: Probe timeout
    trigger: sweep_timer
    condition: Agent does not respond within response_timeout
    expected: Component marked as failed probe, consecutive_failures incremented
    validates: Timeout handled gracefully
```

### Edge Cases

```yaml
  - name: Agent goes offline then recovers
    trigger: sweep_timer
    condition: Agent fails 3 consecutive probes then succeeds
    expected: |
      State transitions: online → offline (after 3 failures)
      Then: offline → online (on success)
      Alerts: critical fired on offline, info fired on recovery
    validates:
      - State machine transitions correct
      - consecutive_failures resets on recovery
      - Both alerts dispatched

  - name: Alerting agent unavailable during state change
    trigger: sweep_timer
    condition: Component goes offline, alerting agent is also offline
    expected: Alert logged locally, monitoring continues
    validates: Health-monitor does not depend on alerting to function

  - name: All components offline
    trigger: sweep_timer
    condition: Every component fails probes
    expected: hub_state = offline, hub_score = 0, health-monitor stays running
    validates: Health-monitor remains operational even with full hub failure

  - name: Storage unavailable during snapshot
    trigger: sweep_timer
    condition: Storage unreachable when persisting snapshot
    expected: Continue probing in-memory, persist when storage recovers
    validates: Monitoring not blocked by storage failures
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
    direct_http: allowed-for-probes-only
    routing: by agent name for messages, direct HTTP for probes
    reason: >
      Probes must reach specific instances via their ports.
      All other communication goes through the message bus.

  intra_agent:
    coordination: leader-election
    leader_election:
      mechanism: shared storage lock (similar to cron agent)
      leader: [sweep_execution, alert_dispatch, snapshot_persistence]
      follower: [health_reporting, action_handling, standby]
      promotion: automatic when leader lock expires
    state_sharing:
      mechanism: shared sqlite database (health_snapshots)
      consistency_window: config.check_interval
      conflict_resolution: >
        Leader performs sweeps and writes snapshots. Followers serve
        cached health map for read requests. On leader failure,
        a follower promotes and takes over sweeps.

  event_handling:
    consumer_group: health-monitor
    delivery: one-per-group
    description: >
      system.agent.registered/deregistered events delivered to one
      instance. Leader processes and updates shared registry.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 3
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same database. Schema migrations
      additive-only during shadow phase.
    consumer_groups:
      shadow_phase: "health-monitor@vN+1"
      after_cutover: "health-monitor"
```

---

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] check-all probes all registered agents, domains, storage, and gateway
- [ ] Component state transitions follow the defined state machine
- [ ] Consecutive failure counter resets on successful probe
- [ ] Hub health score reflects weighted component formula
- [ ] Alerts fire on state changes (degraded, offline, recovery)
- [ ] Health map is queryable via get-health-map action
- [ ] Health history returns snapshots within requested time range
- [ ] Federation advertisement includes hub health summary
- [ ] Health-monitor continues operating when alerting agent is down
- [ ] Probes use /v1/describe — no additional endpoints required
- [ ] Default thresholds are applied; custom thresholds are respected
- [ ] Metrics emit for all probes and state changes
