<!-- blueprint
type: architecture
name: observability
version: 2.0.0
requires: [protocol/types, architecture/orchestrator, architecture/agent]
platform: any
tier: free
-->

# Observability

Structured logging, distributed tracing, and metrics collection for
Weblisk deployments. This blueprint defines the conventions that all
components (orchestrator, domain controllers, agents) follow to
produce consistent, queryable telemetry.

## Overview

Observability in Weblisk has three pillars:

1. **Structured logs** — one envelope, JSON lines on standard output
   ([`patterns/logging`](../patterns/logging.md))
2. **Distributed traces** — one trace context carried on every request
   and inside every envelope, so a request can be followed from the
   component that started it to every component it reached
3. **Metrics** — Counters, gauges, and histograms exposed in a
   standard format for scraping or push-based collection

All three pillars share a common set of context fields that tie
events to specific tasks, agents, domains, and workflows.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=3.0.0 <6.0.0"
    bindings:
      types:
        - name: TraceContext
          fields_used: [trace_id, span_id, parent_span_id, sampled]
        - name: Span
          fields_used: [trace_id, span_id, parent_span_id, name, kind, component, start, end, status, attributes]
        - name: ServiceDirectory
          fields_used: [services]
        - name: ServiceEntry
          fields_used: [name, lease_state]
        - name: AuditEntry
          fields_used: [timestamp, actor, action]
        - name: TaskResult
          fields_used: [task_id, status, duration_ms]
        - name: ErrorResponse
          fields_used: [error, code]
        - name: AgentManifest
          fields_used: [name, type, version]
        - name: TaskRequest
          fields_used: [id, action]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    # 3.0.0 is the first version whose AgentEntry holds a lease rather than an
    # online, offline or degraded status
    version: ">=3.0.0 <4.0.0"
    bindings:
      types:
        # wl_agents_registered counts the registry's entries, and
        # wl_agents_status counts them by lease state (Orchestrator Metrics)
        - name: AgentEntry
          fields_used: [lease, last_renewal]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=2.0.0 <3.0.0"
    bindings:
      types:
        # Where an agent serves the probes Health Endpoint points to
        - name: AgentEndpoints
          fields_used: [livez, readyz]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

Three pillars over one rule: observability reads, and never calls back into what
it observes.

```
   Components ──emit──► ┌──────────────────────────┐
                        │ OBSERVABILITY            │
                        │  logs · metrics · traces │
                        │  redaction at emission   │
                        │  audit: append-only      │
                        └────────────┬─────────────┘
                                     │ scoped reads
                                     ▼
                                  Reader
```

**Responsibilities.** Metric declarations, trace correlation, and an append-only
audit with a hash chain. The record envelope and redaction at emission are
`patterns/logging`'s.

**Not responsibilities.** Acting on what it observes — that is
`architecture/lifecycle`. Deciding a record's classification, which is
`patterns/scope`. Where records are collected and indexed, which is the platform's
and the deployment's.

---

## Responsibilities

### Owns
- When a span is opened and closed, and what it is named ([Distributed Tracing](#distributed-tracing)). The carrier and where sampling is decided are `protocol/spec`'s, the identifiers `protocol/types`'
- Metrics endpoint contract (standard structured format, `wl_` prefix)
- Standard metric definitions for orchestrator, domain controllers, and agents
- Health endpoint response schema and status semantics
- Correlation patterns for end-to-end debugging

### Does NOT Own
- The log envelope, its fields and levels (`protocol/types` LogEntry and `patterns/logging`)
- Log aggregation infrastructure (deployment-specific: Loki, ELK, CloudWatch)
- Metrics scraping configuration (deployment-specific)
- Alerting rules and thresholds (owned by agents/alerting and patterns/observability)
- Per-agent health check logic (owned by each agent's implementation)
- Agent-level health contract and state machine (owned by patterns/observability)

---

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| `GET /metrics` | HTTP (per-component) | Structured metrics endpoint (no auth required) |
| `GET /livez` / `GET /readyz` | HTTP (per-component) | Liveness and readiness, `live` or `ready` alone ([`protocol/types`](../protocol/types.md#health)) |
| `traceparent`, and an envelope's `trace_id` and `span_id` | HTTP header and envelope fields | The one trace carrier ([`protocol/spec`](../protocol/spec.md#trace-propagation)) |
| stdout (JSON lines) | Stream | Log and span lines, in the one envelope ([`patterns/logging`](../patterns/logging.md)) |
| OTLP | HTTP/protobuf | The same logs and spans, pushed to telemetry where it is deployed |

---

## Data Flow

1. A request reaches the first component (the gateway, the orchestrator, or an agent's own timer), and its trace is continued or started as [`protocol/spec`](../protocol/spec.md#trace-propagation)'s Trace Propagation says
2. Every component opens a span for the work it does, and a child span for each request it sends ([Span Lifecycle](#span-lifecycle))
3. Each component closes its spans as its work ends, and writes every sampled span as one log line on standard output, pushing it as OTLP where telemetry is deployed ([Trace Export](#trace-export))
4. Every log line written while a span is open carries that span's `trace_id` and `span_id`, so a trace gathers the log lines it caused
5. Metrics counters and histograms are updated at each component throughout the flow

---

## Design Principles

> **Scope boundary.** This document defines when spans open and close and
> what they are named, and the metric collection infrastructure. The log
> envelope is [`patterns/logging`](../patterns/logging.md)'s and
> [`protocol/types`](../protocol/types.md#logentry)'s; the trace carrier is
> [`protocol/spec`](../protocol/spec.md#trace-propagation)'s. For the agent-level health endpoint contract, component
> state machine, base metrics envelope, and alert integration, see
> [patterns/observability.md](../patterns/observability.md). The two are
> complementary: architecture/observability defines the telemetry pipeline;
> patterns/observability defines the per-component contract that feeds it.

1. **Convention over configuration** — Components emit telemetry in
   a standard shape. No per-agent configuration needed.
2. **Correlation by default** — Every log line, trace span, and
   metric point includes enough context to correlate across the
   system.
3. **Zero-dependency core** — The observability contract is based on
   plain JSON logs and HTTP endpoints. No vendor SDK is required.
   External metrics collection and trace export are optional integrations —
   the system works without them.
4. **Opt-in depth** — Basic logging is always on. Tracing and metrics
   can be enabled per-deployment.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: trace-propagation
      description: Carry a trace on every request a component serves and every request and envelope it sends, and open, name and close spans as Distributed Tracing says
      required: true
      rules:
        - A component MUST carry, continue and start traces exactly as protocol/spec's Trace Propagation states; those rules are stated there and nowhere else
        - A component MUST name, open and close its spans as Distributed Tracing below says
```

---

## Structured Logging

Every component writes [`LogEntry`](../protocol/types.md#logentry) as
[`patterns/logging`](../patterns/logging.md) says.

---

## Distributed Tracing

The carrier is [`protocol/spec`](../protocol/spec.md#trace-propagation)'s
(`traceparent` on every HTTP request, `trace_id` and `span_id` inside every
envelope) and the identifiers and the `Span` record are
[`protocol/types`](../protocol/types.md#tracecontext)'. This section says when a
span exists and what it is called; a component binds both as
`trace-propagation` ([Contracts](#contracts)).

### Span Lifecycle

```
1. On receiving a request: open a span (kind server, or consumer for an event)
   with a new span_id and start = now. Its trace_id and parent_span_id are what
   Trace Propagation (protocol/spec) gives it
2. On sending a request to another component: open a child span (kind client,
   or producer for a publish), carry it as Trace Propagation says, and close it
   when the answer arrives or the call fails
3. On finishing the work: set end and status (ok or error), and record the span
   if the trace is sampled
```

### Span Names

A span is named for what was done, never for who did it; `component` says who.
An HTTP span takes OpenTelemetry's name for it. Attribute names follow
OpenTelemetry semantic conventions where one exists, and otherwise sit under
`weblisk.`, as a log record's do
([`patterns/logging`](../patterns/logging.md#opentelemetry-log-data-model)).

| Name | Opened by | Attributes |
|------|-----------|------------|
| `{method} {route}`, such as `GET /v1/services` | A component, for each request it serves that no name below covers | `http.route`, `http.request.method`, `http.response.status_code` |
| `{method}` | A component, for each request it sends that no name below covers | `server.address`, `http.request.method` |
| `agent.execute` | An agent, serving `POST /v1/execute` | `weblisk.task_id`, `weblisk.action` |
| `agent.message` | An agent, serving `POST /v1/message` | `weblisk.from`, `weblisk.to`, `weblisk.action` |
| `event.deliver` | A subscriber, serving `POST /v1/event` | `messaging.destination.name` (the topic), `messaging.message.id` (the `event_id`), `weblisk.source` |
| `workflow.phase` | The workflow agent, for each phase | `weblisk.workflow`, `weblisk.phase`, `weblisk.phase_agent` |
| `lease.renew` | A component, for each renewal it sends to `POST /v1/lease` | `weblisk.ready` |

A line between two components is a span whose `parent_span_id` names a span
another component opened. That is all a reader needs to draw who called whom,
and it is why every envelope carries `span_id`.

### Trace Export

Each sampled span is written on standard output as one log line whose
`log_type` is `span` ([`patterns/logging`](../patterns/logging.md#trace-events)),
and pushed as an OTLP span where telemetry is deployed. Nothing a component
does depends on the push arriving.

---

## Metrics

### Metrics Endpoint

Every component exposes `GET /metrics` returning metrics in a
structured format. The endpoint MUST support counter, gauge, and
histogram metric types with the labels defined in the standard
metric tables below. The wire format is deployment-specific.

### Standard Metrics

#### Orchestrator Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `wl_agents_registered` | gauge | — | Total registered agents |
| `wl_agents_status` | gauge | `lease_state` | Agents by lease state (`ready`, `not_ready`, `unknown`) |
| `wl_tasks_total` | counter | `domain`, `status` | Tasks processed |
| `wl_task_duration_seconds` | histogram | `domain` | Task duration |
| `wl_approvals_pending` | gauge | — | Pending recommendations |
| `wl_federation_peers` | gauge | `status` | Federation peers by status |
| `wl_http_requests_total` | counter | `method`, `path`, `status_code` | HTTP requests |
| `wl_http_request_duration_seconds` | histogram | `method`, `path` | HTTP latency |

#### Domain Controller Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `wl_workflows_total` | counter | `workflow`, `status` | Workflow executions |
| `wl_workflow_duration_seconds` | histogram | `workflow` | Workflow duration |
| `wl_observations_total` | counter | `type` | Observations created |
| `wl_recommendations_total` | counter | `status` | Recommendations by status |

#### Agent Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `wl_tasks_total` | counter | `action`, `status` | Tasks by action |
| `wl_task_duration_seconds` | histogram | `action` | Duration by action |
| `wl_llm_calls_total` | counter | `model` | LLM API calls |
| `wl_llm_tokens_total` | counter | `model`, `type` | Tokens used (prompt/completion) |
| `wl_file_reads_total` | counter | — | File read operations |
| `wl_http_outbound_total` | counter | `host`, `status_code` | Outbound HTTP requests |

### Metric Naming Conventions

- Prefix: `wl_` (Weblisk)
- Suffix: `_total` for counters, `_seconds` for durations,
  no suffix for gauges
- Labels: lowercase, underscore-separated
- Keep cardinality low — don't use high-cardinality labels like
  `user_id` or `url`

---

## Health Endpoint

Health is liveness and readiness only, and this blueprint owns neither.
`GET /livez`, `GET /readyz`, the lease that carries readiness and its three
states are [`protocol/types`](../protocol/types.md#health)'s, served as
[`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz) says.
Observability reads the lease states the orchestrator's directory publishes
([`architecture/orchestrator`](orchestrator.md#presence)) and never probes a
registered component for them. How a component is serving its users — latency,
errors, the subsystems it uses — is a metric, never a health answer.

---

## Correlation Patterns

### End-to-End Task Trace

Given a `task_id`, you can reconstruct the full execution path:

```
1. grep logs for task_id → find trace_id
2. grep logs for trace_id → get all log lines across all components
3. Sort by `ts` → chronological execution flow
4. Filter by log_type=span → get span tree for timing analysis
```

### Agent Debugging

```bash
# All errors from a specific agent in the last hour
cat logs.jsonl | jq 'select(.component == "seo-analyzer" and .level == "error")'

# Slow tasks (>5s) across all agents
cat logs.jsonl | jq 'select(.duration_ms > 5000 and .msg == "Task completed")'

# Trace a specific workflow execution
cat logs.jsonl | jq 'select(.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736")'
```

### Dashboard Queries

Deployments using a log aggregation or metrics service SHOULD build
dashboards for these key queries:

- **Error rate by agent** — ratio of error-level log entries to total
  entries per agent over a rolling window (e.g., 24h)
- **P95 task duration by domain** — 95th percentile of
  `wl_task_duration_seconds` grouped by domain
- **Ready agents** — current value of `wl_agents_status` where
  `lease_state` is `ready`

---

## Configuration

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Log level | `info` | [`schemas/config`](../schemas/config.md)'s `observability.log_level` |
| Tracing enabled | `false` | Record sampled spans. Trace context is carried whether or not this is set |
| Trace sample rate | `1.0` | Trace sampling rate (0.0–1.0), applied where a trace starts |
| Trace export target | — | Where sampled spans are exported, where telemetry is deployed |
| Metrics enabled | `true` | Expose /metrics endpoint |

### Local Development

In development mode:
- Tracing is disabled (less noise)
- Metrics endpoint is available at each component's port + `/metrics`
- All components write logs to the runtime's own log stream, wherever a developer sees it

### Production

In production:
- Tracing: enabled with sampling (0.1 = 10% of requests)
- Metrics: scraped by a compatible metrics collector
- Components write to stdout; container runtime captures logs

---

## Security

```yaml
security:
  trust_model:
    description: |
      Observability reads and never writes to the systems it observes. Its own
      records are trusted as evidence only because they are append-only and
      attributable; anything a component asserts about itself is recorded as its
      assertion rather than as fact. Its greatest risk is disclosure: a log is
      where scoped data leaks when nobody is watching.
  boundaries:
    - boundary: Component → Observability. Components emit; observability never
        calls back into them to act
    - boundary: Log record → Scope. Redacted at emission, as
        patterns/logging's Sensitive Data states
    - boundary: Audit record → Mutation. Append-only. An audit record is never
        amended or deleted
    - boundary: Observability → Reader. What a reader sees is bounded by their
        scope, including in aggregates
  enforcement:
    - rule: A log record is redacted at emission
      mechanism: patterns/logging's redaction-at-emission
    - rule: An audit record is never modified or removed
      mechanism: Append-only store with a hash chain over entries
    - rule: A trace identifier propagates without carrying payload data
      mechanism: protocol/spec's Trace Propagation, bound as trace-propagation
    - rule: An aggregate does not disclose what its inputs would not
      mechanism: Aggregates computed within the reader's scope, not filtered
        after computation
```

---

## Implementation Notes

- Structured logging MUST be the default — never use unstructured
  print statements for operational events
- Trace context is carried on every inter-component HTTP request, probes
  and governance calls included (`trace-propagation`)
- The `/metrics` endpoint MUST NOT require authentication (standard
  metrics collection convention)
- Metrics MUST NOT include PII or sensitive data in labels
- Log rotation is the responsibility of the runtime environment
  (container, systemd, etc.), not the application
- Components SHOULD limit log output to ~100 lines per task at
  `info` level to prevent log flooding
- Span events (within a span) should be used sparingly — major
  milestones only, not every function call

## Verification Checklist

- [ ] All components write the one log envelope `patterns/logging` defines
- [ ] The log level is `schemas/config`'s `observability.log_level`
- [ ] Trace context is carried, continued and started as `protocol/spec`'s Trace Propagation says (`trace-propagation`)
- [ ] Every span takes its name from the Span Names table, and opens and closes as Span Lifecycle says
- [ ] GET /metrics returns structured metrics with wl_ prefix and does NOT require authentication
- [ ] Orchestrator exposes wl_agents_registered, wl_tasks_total, wl_task_duration_seconds, and wl_http_requests_total metrics
- [ ] Agent metrics include wl_tasks_total by action/status, wl_llm_calls_total, and wl_llm_tokens_total by model/type
- [ ] Metrics labels do NOT include high-cardinality values (user_id, URL) or PII
- [ ] No component answers a health request with more than `live` or `ready`, and observability counts agents by `lease_state` without probing any
- [ ] Each sampled span is written as one log line whose `log_type` is `span`, and pushed as OTLP where telemetry is deployed
- [ ] Components limit log output to ~100 lines per task at info level to prevent log flooding
