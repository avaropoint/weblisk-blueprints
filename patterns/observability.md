<!-- blueprint
type: pattern
name: observability
version: 2.0.0
requires: [protocol/types, architecture/agent, patterns/logging]
platform: any
tier: free
-->

# Observability Pattern

Health — liveness and readiness — and the base metrics envelope for all
Weblisk agents and domain controllers. This pattern is a cross-cutting
concern — every agent and domain `extends: patterns/observability` and
inherits the health contract and base metrics. Agents add domain-specific
metrics only.

## Overview

Every component in a Weblisk deployment must be observable:

1. **Health** — serves `GET /livez` and `GET /readyz`, and renews its lease
   with the orchestrator carrying its readiness
2. **Base metrics** — standard set every agent emits

This pattern standardizes both so that monitoring infrastructure works
uniformly across agents, domains, and system components. "Health" means
liveness and readiness and nothing else: there is no component state machine,
no latency threshold and no probe of one component by another.

> **Scope boundary.** This pattern defines the per-component observability
> contract — health and base metrics. For system-wide telemetry infrastructure (log shape,
> distributed trace propagation, metric collection pipeline), see
> [architecture/observability.md](../architecture/observability.md). The
> two are complementary: this pattern defines what each component emits;
> architecture/observability defines how the system collects and routes it.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=2.0.0 <3.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, version, url]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        - name: AgentState
          fields_used: [state]
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

1. **Uniform health contract** — every component serves `GET /livez` and `GET /readyz` with the same two answers and renews its lease the same way, so no component needs per-component configuration to be restarted or found.
2. **Nothing polls** — presence is the lease a component renews, never a probe another component sends; a probe would be a second presence fact that can disagree with the first.
3. **Inherited metrics** — base metrics are emitted by every agent automatically; agents declare only additional domain-specific metrics.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: health-reporting
      description: Serve liveness and readiness, and renew the lease with the orchestrator carrying readiness
      parameters: []
      inherits: The Health section — GET /livez and GET /readyz answers, the liveness independence rule, lease renewal within a third of its duration
      overridable: false
      override_constraints: None. Health is liveness and readiness, the same for every component

    - name: metric-emission
      description: Emit base metrics in structured format
      parameters:
        - name: metrics
          type: "[]MetricDefinition"
          required: false
          description: Additional domain-specific metrics beyond base set
      inherits: Base agent metrics (requests_total, duration, errors, state, uptime)
      overridable: true
      override_constraints: Must not remove or rename base metrics

  types:
    - name: MetricsSnapshot
      description: Key metric values at one moment, as a component reports them
      inherited_by: Base Metrics section

  endpoints:
    - path: /livez
      description: Liveness, for the supervisor that restarts the component
      inherited_by: Health Endpoint section
    - path: /readyz
      description: Readiness, for the supervisor waiting on a start
      inherited_by: Health Endpoint section
    - path: /v1/metrics
      description: Structured metrics endpoint for monitoring systems
      inherited_by: Base Metrics section
```

---

## Health Endpoint

Every agent and domain controller MUST:

1. Serve `GET /livez` and `GET /readyz` on its listener, as
   [`protocol/types`](../protocol/types.md#liveness) and
   [`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz) define them,
   the rule that liveness depends on nothing outside the process included.
2. Renew its lease at `POST /v1/lease`, carrying `ready` and `checks`, as
   [`protocol/types`](../protocol/types.md#leaserenewal) sets the cadence and
   the renewals of a component that is draining.

What each answer means, and the three lease states a reader sees, are
[`protocol/types`](../protocol/types.md#health)'s. A component's version is in
its manifest; its uptime, latency and error counts are metrics (Base Metrics,
below). None of them is part of health.

---

## Component State Machine

There is none to implement. A component's state, as every other party sees
it, is its lease state in the orchestrator's directory: `ready`, `not_ready`
or `unknown` ([`protocol/types`](../protocol/types.md#leasestate)). It changes
when the component renews or its lease lapses, never because another component
measured it. There is no `online`, `degraded` or `offline`, no latency
threshold and no failure count.

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
| `agent_ready` | gauge | — | 1 while the component would answer `GET /readyz` with `ready: true`, 0 otherwise |
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

Metrics use a structured exposition format. The wire format is
deployment-specific; the metric names, types, and labels are
the specification contract:

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

Agents SHOULD expose metrics at `GET /v1/metrics` in a structured
format. This endpoint is called by any external monitoring system.

---

## Alert Integration

A component emits no event when its health changes, and nothing probes it to
find one. A lease that lapses or recovers is the directory entry's
`lease_state`, which the orchestrator broadcasts
([`architecture/orchestrator`](../architecture/orchestrator.md#presence)); a
rule that should page on it is telemetry's, evaluated over the lease states and
the metrics a component pushes.

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
```

---

## Types

```yaml
types:

  MetricDefinition:
    description: A metric a component declares, so a reader knows what it measures before reading it
    fields:
      name:
        type: string
        description: Metric name
      type:
        type: string
        description: What kind of measurement it is
        constraints:
          enum: [counter, gauge, histogram]
      description:
        type: string
        description: What it measures, in terms independent of how it is collected
      labels:
        type: array
        items: string
        description: Label names this metric carries. A label whose values are unbounded makes the metric unusable
```

---

## Implementation Notes

- **Probes are cheap**: `GET /livez` and `GET /readyz` read state the
  process already holds. Neither calls a store, a peer or a provider while
  answering.
- **Metric cardinality**: Keep label cardinality low. Do not use
  unbounded values (e.g. user IDs) as labels.
- **Clock sync**: Timestamps in metrics and alerts use Unix epoch
  seconds. Components SHOULD use NTP-synced clocks.
- **Starting and draining**: a component is `not_ready` from registration
  until its first renewal says `ready: true`, and again while it drains.
  Neither is a fault.

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
| Lease renewal | `lease.renew` | `agent.name`, `ready` |

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
semantic convention names. Internal metrics exposition uses the
Weblisk names.

### Kubernetes Probes and Leases

Health follows Kubernetes probe semantics: `/livez` answers whether the
process must be restarted and `/readyz` whether it can serve. Presence follows
the Kubernetes Lease: the holder renews, a lapse is visible to every reader,
and nobody probes. The IETF health-check response draft, which this pattern
used to follow, carried a status, a version, checks and output in one
unauthenticated answer; none of that is health here.

---

## Verification Checklist

- [ ] Agent serves `GET /livez` and `GET /readyz` without authentication, each answering with `live` or `ready` alone
- [ ] `GET /livez` stays 200 while a store or a peer the agent depends on is down, and `GET /readyz` answers 503
- [ ] Agent renews its lease at `POST /v1/lease` within a third of its `duration`, with `checks` naming what it is short of when `ready` is false
- [ ] Agent renews with `ready: false` while draining, then deregisters
- [ ] Base metrics (requests, duration, errors, readiness) are emitted
- [ ] Metrics exposed at GET /v1/metrics in structured format
- [ ] No component sends a request to another to learn its health, and none emits a health state-change event
