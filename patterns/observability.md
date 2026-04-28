<!-- blueprint
type: pattern
name: observability
version: 1.0.0
requires: [protocol/types, architecture/agent, patterns/logging]
platform: any
tier: free
-->

# Observability Pattern

Standard health endpoint, metrics envelope, component state tracking,
and alert integration for all Weblisk agents and domain controllers.
This pattern is a cross-cutting concern — every agent and domain
`extends: patterns/observability` and inherits the health contract,
state machine, and base metrics. Agents add domain-specific metrics
only.

## Overview

Every component in a Weblisk deployment must be observable:

1. **Health endpoint** — responds to `POST /v1/health` with
   structured status
2. **Component state** — online/degraded/offline with defined
   transitions
3. **Base metrics** — standard set every agent emits
4. **Alert integration** — state changes fire alert events
5. **Health probing** — how the health-monitor checks components

This pattern standardizes all five so that monitoring infrastructure
works uniformly across agents, domains, and system components.

> **Scope boundary.** This pattern defines the per-component observability
> contract — health endpoints, state machine, base metrics, and alert
> integration. For system-wide telemetry infrastructure (log shape,
> distributed trace propagation, metric collection pipeline), see
> [architecture/observability.md](../architecture/observability.md). The
> two are complementary: this pattern defines what each component emits;
> architecture/observability defines how the system collects and routes it.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, version, url]
        - name: HealthStatus
          fields_used: [name, status, version, uptime]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentState
          fields_used: [state, health, uptime]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/logging
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: LogEntry
          fields_used: [ts, level, log_type, msg, component]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Uniform health contract** — every component responds to `POST /v1/health` with an identical structure, enabling automated monitoring without per-agent configuration.
2. **State machine consistency** — all components use the same online/degraded/offline states with deterministic transitions based on latency and failure thresholds.
3. **Inherited metrics** — base metrics are emitted by every agent automatically; agents declare only additional domain-specific metrics.
4. **Alert-driven** — state changes automatically emit structured events for routing through the alerting and notification pipeline.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: health-reporting
      description: Respond to health probes with structured status, sub-checks, and metrics snapshot
      parameters:
        - name: response_timeout_ms
          type: int
          required: true
          description: Maximum time to respond to a health probe
      inherits: Health endpoint response format, sub-component check structure
      overridable: true
      override_constraints: Must respond within response_timeout_ms and include required fields

    - name: state-tracking
      description: Maintain component state via online/degraded/offline state machine
      parameters:
        - name: degraded_threshold_ms
          type: int
          required: true
          description: Latency above which component is degraded
        - name: failure_threshold
          type: int
          required: true
          description: Consecutive failures before component is offline
      inherits: State machine transitions, threshold defaults
      overridable: true
      override_constraints: Must preserve the four defined states and valid transitions

    - name: metric-emission
      description: Emit base metrics in Prometheus exposition format
      parameters:
        - name: metrics
          type: "[]MetricDefinition"
          required: false
          description: Additional domain-specific metrics beyond base set
      inherits: Base agent metrics (requests_total, duration, errors, state, uptime)
      overridable: true
      override_constraints: Must not remove or rename base metrics

  types:
    - name: HealthStatus
      description: Structured health status with state, sub-checks, and metrics snapshot
      inherited_by: Health Endpoint section
    - name: ComponentState
      description: Enum of component states — unknown, online, degraded, offline
      inherited_by: Component State Machine section
    - name: MetricsSnapshot
      description: Key metric values at response time included in health responses
      inherited_by: Base Metrics section

  endpoints:
    - path: /v1/health
      description: Health probe endpoint returning structured component status
      inherited_by: Health Endpoint section
    - path: /v1/metrics
      description: Prometheus-format metrics endpoint for monitoring systems
      inherited_by: Base Metrics section

  events:
    - topic: component.state_change
      description: Emitted when a component transitions between health states
      payload: {component, component_type, from_state, to_state, reason, timestamp}
```

---

## Health Endpoint

Every agent and domain controller MUST respond to `POST /v1/health`:

### Request

No body required. Health checks are lightweight probes.

### Response

```json
{
  "name": "<agent-name>",
  "version": "<semver>",
  "state": "online",
  "uptime_seconds": 86400,
  "checks": {
    "storage": {"state": "online", "latency_ms": 2},
    "dependencies": {"state": "online", "details": {}}
  },
  "metrics_snapshot": {
    "requests_total": 15420,
    "errors_total": 3,
    "last_activity": 1713264000
  }
}
```

### Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Agent or domain name |
| version | string | yes | Current semver version |
| state | string | yes | `online`, `degraded`, `offline` |
| uptime_seconds | int | yes | Seconds since last start |
| checks | object | no | Sub-component health checks |
| metrics_snapshot | object | no | Key metric values at response time |

### Sub-Component Checks

Agents with dependencies (storage, external APIs, other agents)
SHOULD include sub-checks:

```yaml
checks:
  storage:
    state: online | degraded | offline
    latency_ms: <int>
  dependencies:
    state: online | degraded | offline
    details:
      <dependency-name>:
        state: online | degraded | offline
        latency_ms: <int>
        last_success: <timestamp>
```

The agent's top-level `state` is derived from sub-checks:
- All checks `online` → agent `online`
- Any check `degraded` → agent `degraded`
- Any critical check `offline` → agent `offline`

---

## Component State Machine

All agents and domains use the same state model:

```
         ┌─────────────────────────────────┐
         │                                 │
         v                                 │
    ┌─────────┐   latency > threshold  ┌──────────┐
    │  online  │ ────────────────────> │ degraded  │
    └─────────┘                        └──────────┘
         ^                                 │
         │   latency returns normal        │
         │ <──────────────────────────────-┘
         │                                 │
         │   consecutive_failures          │
         │   >= threshold                  │   consecutive_failures
         │                                 │   >= threshold
         │        ┌─────────┐              │
         └──────  │ offline │ <────────────┘
     successful   └─────────┘
     probe             ^
                       │
                  ┌─────────┐
                  │ unknown  │  (initial state)
                  └─────────┘
```

### States

| State | Condition | Description |
|-------|-----------|-------------|
| `unknown` | No health check performed yet | Initial state after registration |
| `online` | Healthy response within latency threshold | Operating normally |
| `degraded` | Healthy response but latency > threshold | Functional but slow |
| `offline` | No response or error after threshold failures | Unreachable or failing |

### State Transitions

| From | To | Trigger |
|------|----|---------|
| `unknown` | `online` | First successful probe |
| `unknown` | `offline` | First failed probe |
| `online` | `degraded` | Latency exceeds `degraded_threshold_ms` |
| `online` | `offline` | `consecutive_failures >= failure_threshold` |
| `degraded` | `online` | Latency returns below `degraded_threshold_ms` |
| `degraded` | `offline` | `consecutive_failures >= failure_threshold` |
| `offline` | `online` | Successful probe after failures |

### Default Thresholds

```yaml
observability:
  thresholds:
    response_timeout_ms: 5000        # max wait for health response
    degraded_threshold_ms: 500       # latency above this → degraded
    failure_threshold: 3             # consecutive failures → offline
    alert_on_degraded: true
    alert_on_offline: true
    alert_on_recovery: true
```

Thresholds are configurable per agent via the agent's config section.

---

## Base Metrics

Every agent and domain MUST emit these metrics. They are inherited —
agents do not need to redeclare them.

### Agent Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `agent_requests_total` | counter | `action`, `status` | Total requests processed |
| `agent_request_duration_seconds` | histogram | `action` | Request processing time |
| `agent_errors_total` | counter | `action`, `error_type` | Errors by type |
| `agent_state` | gauge | — | Current state (1=online, 0.5=degraded, 0=offline) |
| `agent_uptime_seconds` | gauge | — | Time since last start |
| `agent_last_activity_timestamp` | gauge | — | Unix timestamp of last processed request |

### Domain Metrics (additional)

Domains inherit agent metrics plus the domain-specific set from
`patterns/domain-controller`:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `domain_workflow_duration_seconds` | histogram | `workflow`, `status` | Workflow execution time |
| `domain_workflow_total` | counter | `workflow`, `status` | Workflow completions |
| `domain_agent_dispatch_total` | counter | `agent`, `action` | Agent dispatches |
| `domain_agent_dispatch_duration_seconds` | histogram | `agent` | Agent response time |
| `domain_score` | gauge | — | Latest domain score (0–100) |
| `domain_findings_total` | counter | `category`, `severity` | Findings produced |

### Metrics Format

Metrics use the Prometheus exposition format:

```
# HELP agent_requests_total Total requests processed
# TYPE agent_requests_total counter
agent_requests_total{action="check",status="success"} 1542
agent_requests_total{action="check",status="error"} 3

# HELP agent_request_duration_seconds Request processing time
# TYPE agent_request_duration_seconds histogram
agent_request_duration_seconds_bucket{action="check",le="0.1"} 1200
agent_request_duration_seconds_bucket{action="check",le="0.5"} 1500
agent_request_duration_seconds_bucket{action="check",le="1.0"} 1540
agent_request_duration_seconds_bucket{action="check",le="+Inf"} 1542
```

### Metrics Endpoint

Agents SHOULD expose metrics at `GET /v1/metrics` in Prometheus
format. This endpoint is called by the health-monitor agent and
any external monitoring system.

---

## Alert Integration

When a component's state changes, it MUST emit a structured alert
event to the message bus:

```json
{
  "event": "component.state_change",
  "source": "<agent-name>",
  "data": {
    "component": "<agent-name>",
    "component_type": "agent",
    "from_state": "online",
    "to_state": "degraded",
    "reason": "Latency 850ms exceeds threshold 500ms",
    "timestamp": 1713264000
  }
}
```

The alerting agent receives these events and routes notifications
based on severity (see `agents/alerting.md`):

| Transition | Alert Severity |
|------------|---------------|
| `* → online` (recovery) | `info` |
| `online → degraded` | `medium` |
| `degraded → offline` | `critical` |
| `online → offline` | `critical` |

---

## Health Probe Protocol

The health-monitor agent probes components using a standard protocol.
Components do not need to implement anything beyond the `/v1/health`
endpoint — probing is the monitor's responsibility.

```
1. SEND: POST /v1/health to component
2. MEASURE: latency_ms from request to response
3. EVALUATE:
   - Response 2xx AND latency < threshold → online
   - Response 2xx AND latency > degraded_threshold → degraded
   - No response OR non-2xx → increment failure counter
   - If consecutive_failures >= failure_threshold → offline
4. UPDATE: component state in health map
5. ALERT: if state changed, emit component.state_change event
```

---

## Agent Declaration

Agents that extend this pattern declare only their additional
domain-specific metrics:

```yaml
extends: patterns/observability

observability:
  metrics:
    - name: cron_jobs_executed_total
      type: counter
      labels: [schedule_type, status]
      description: Cron jobs executed by type and result

    - name: cron_job_duration_seconds
      type: histogram
      labels: [schedule_type]
      description: Time to execute scheduled jobs

  thresholds:
    degraded_threshold_ms: 1000      # override default 500ms
```

---

## Implementation Notes

- **Health checks are lightweight**: The `/v1/health` endpoint MUST
  respond within the `response_timeout_ms` threshold. Do not perform
  expensive operations in health checks.
- **Metric cardinality**: Keep label cardinality low. Do not use
  unbounded values (e.g. user IDs) as labels.
- **Clock sync**: Timestamps in metrics and alerts use Unix epoch
  seconds. Components SHOULD use NTP-synced clocks.
- **Graceful degradation**: Components should continue serving
  requests in `degraded` state. Only `offline` means unavailable.
- **Startup grace period**: New components start in `unknown` state.
  The first successful health check moves them to `online`. Do not
  alert on `unknown` → `online` transitions.

## Standards Alignment: OpenTelemetry & W3C Trace Context

Weblisk observability aligns with
[OpenTelemetry](https://opentelemetry.io/) semantics and
[W3C Trace Context](https://www.w3.org/TR/trace-context/) for
distributed tracing.

### Trace Context Propagation

The `trace_id` field in `TaskContext` and `AgentMessage` maps to the
W3C `traceparent` header format:

```
traceparent: 00-<trace_id>-<span_id>-<trace_flags>
```

| W3C Field | Weblisk Equivalent | Notes |
|-----------|-------------------|-------|
| `trace-id` | `trace_id` in TaskContext | 32-char hex (16 bytes) |
| `parent-id` (span) | Not yet modeled | Implementations MAY generate per-phase span IDs |
| `trace-flags` | Not yet modeled | Default `01` (sampled) |
| `tracestate` | Not yet modeled | Vendor-specific; reserved for future use |

### Span Model (Recommended)

Implementations SHOULD generate spans for key operations:

| Operation | Span Name | Attributes |
|-----------|-----------|------------|
| Task execution | `agent.execute` | `agent.name`, `task.action`, `task.id` |
| Workflow phase | `workflow.phase` | `workflow.name`, `phase.name`, `phase.agent` |
| Agent message | `agent.message` | `from`, `to`, `action` |
| Health probe | `health.probe` | `target`, `result` |

Span IDs are generated per operation and linked via parent span ID
to form a trace tree. The trace_id remains constant across the
entire workflow execution.

### Metrics Convention

Base metrics follow OpenTelemetry semantic conventions where
applicable:

| Weblisk Metric | OTel Convention |
|---------------|----------------|
| `agent_request_duration_seconds` | `http.server.request.duration` |
| `agent_requests_total` | `http.server.request.count` |
| `agent_errors_total` | `http.server.error.count` |

Implementations that export to OTel collectors SHOULD use the OTel
semantic convention names. Internal Prometheus exposition uses the
Weblisk names.

### IETF Health Check Draft

The health endpoint response structure aligns with the
[IETF Health Check Response draft](https://datatracker.ietf.org/doc/html/draft-inadarei-api-health-check):

| IETF Field | Weblisk Field | Notes |
|------------|--------------|-------|
| `status` | `state` | IETF uses pass/fail/warn; Weblisk uses online/degraded/offline |
| `version` | `version` | Same |
| `checks` | `checks` | Same structure concept |
| `output` | `metrics_snapshot` | Similar purpose |

---

## Verification Checklist

- [ ] Agent responds to POST /v1/health with valid JSON
- [ ] Health response includes name, version, state, uptime
- [ ] State transitions follow the defined state machine
- [ ] Base metrics (requests, duration, errors, state) are emitted
- [ ] Metrics exposed at GET /v1/metrics in Prometheus format
- [ ] State changes emit component.state_change events
- [ ] Degraded threshold is configurable per agent
- [ ] Failure threshold triggers offline state
- [ ] Recovery from offline emits info-level alert
- [ ] Health checks complete within response_timeout_ms
