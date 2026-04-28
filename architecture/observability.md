<!-- blueprint
type: architecture
name: observability
version: 1.0.0
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

1. **Structured logs** — JSON-formatted, leveled, with consistent
   fields for correlation
2. **Distributed traces** — Trace ID propagation from orchestrator
   through domains to agents, enabling end-to-end request tracking
3. **Metrics** — Counters, gauges, and histograms exposed in a
   standard format for scraping or push-based collection

All three pillars share a common set of context fields that tie
events to specific tasks, agents, domains, and workflows.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
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
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ServiceDirectory
          fields_used: [agents]
        - name: AuditEntry
          fields_used: [timestamp, actor, action]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: HealthStatus
          fields_used: [status, component, version, uptime_seconds, checks]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

### Owns
- Structured log format definition (JSON shape, required fields, levels)
- Distributed trace context propagation rules (X-Trace-Id, X-Span-Id headers)
- Trace ID generation and span lifecycle conventions
- Metrics endpoint contract (Prometheus exposition format, `wl_` prefix)
- Standard metric definitions for orchestrator, domain controllers, and agents
- Health endpoint response schema and status semantics
- Correlation patterns for end-to-end debugging

### Does NOT Own
- Log aggregation infrastructure (deployment-specific: Loki, ELK, CloudWatch)
- Metrics scraping configuration (deployment-specific: Prometheus, Datadog)
- Alerting rules and thresholds (owned by agents/alerting and patterns/observability)
- Per-agent health check logic (owned by each agent's implementation)
- Agent-level health contract and state machine (owned by patterns/observability)

---

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| `GET /metrics` | HTTP (per-component) | Prometheus exposition format metrics endpoint (no auth required) |
| `GET /v1/health` | HTTP (per-component) | Structured health status with checks map |
| `X-Trace-Id` header | HTTP header | 32 hex char trace identifier propagated on all inter-component requests |
| `X-Span-Id` header | HTTP header | 16 hex char span identifier for trace tree construction |
| `X-Parent-Span-Id` header | HTTP header | Parent span reference for child span linking |
| stdout (JSON lines) | Stream | Structured log and span output consumed by runtime log capture |
| OTLP export | HTTP/protobuf | Optional trace export to OpenTelemetry Collector |

---

## Data Flow

1. Client request arrives at the orchestrator (or gateway); trace ID is generated or preserved from incoming `X-Trace-Id`
2. Orchestrator creates root span, logs request with trace context fields
3. Orchestrator forwards request to domain controller with `X-Trace-Id`, `X-Span-Id`, `X-Parent-Span-Id` headers
4. Domain controller creates child span, logs operation, forwards to agent with updated span headers
5. Agent creates child span, executes task, logs measurements and findings
6. Agent completes span (records duration, status), returns response to domain
7. Domain completes span, returns aggregated response to orchestrator
8. Orchestrator completes root span, emits final log with total duration
9. All spans are written to stdout as JSON (type: span) and optionally exported via OTLP
10. Metrics counters and histograms are updated at each component throughout the flow

---

## Design Principles

> **Scope boundary.** This document defines system-wide observability
> conventions — log shape, trace propagation, and metric collection
> infrastructure. For the agent-level health endpoint contract, component
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
   Prometheus scraping and OTLP export are optional integrations —
   the system works without them.
4. **Opt-in depth** — Basic logging is always on. Tracing and metrics
   can be enabled per-deployment.

---

## Structured Logging

### Log Format

All components emit JSON logs to stdout, one object per line.

```json
{
  "ts": "2026-04-25T10:30:01.123Z",
  "level": "info",
  "msg": "Task completed",
  "component": "seo-analyzer",
  "component_type": "agent",
  "trace_id": "abc123def456",
  "span_id": "span-789",
  "task_id": "task-a1b2c3",
  "domain": "seo",
  "duration_ms": 2100,
  "status": "completed"
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| ts | string | ISO 8601 timestamp with milliseconds |
| level | string | `debug`, `info`, `warn`, `error` |
| msg | string | Human-readable message |
| component | string | Name of the emitting component |
| component_type | string | `orchestrator`, `domain`, `agent` |

### Contextual Fields

These fields are included when available:

| Field | Type | When Present |
|-------|------|-------------|
| trace_id | string | Always (generated at request entry) |
| span_id | string | When tracing is enabled |
| parent_span_id | string | For child spans |
| task_id | string | During task processing |
| domain | string | When operating within a domain |
| workflow | string | During workflow execution |
| agent | string | When the log relates to a specific agent |
| duration_ms | int | On operation completion |
| status | string | On operation completion |
| error | string | On error (level=error) |
| error_code | string | Structured error classification |

### Log Levels

| Level | Usage |
|-------|-------|
| debug | Verbose diagnostic information (disabled in production by default) |
| info | Normal operations — task started, completed, agent registered |
| warn | Recoverable issues — retry, degraded state, approaching limit |
| error | Failures — task failed, agent unreachable, storage error |

### Level Configuration

```json
{
  "log_level": "info",
  "log_level_overrides": {
    "seo-analyzer": "debug",
    "orchestrator": "warn"
  }
}
```

---

## Distributed Tracing

### Trace Context Propagation

Weblisk uses a simplified trace context that propagates through the
system via the `X-Trace-Id` and `X-Span-Id` HTTP headers.

```
Client Request
  → Orchestrator (generates trace_id, root span)
    → Domain Controller (inherits trace_id, creates child span)
      → Agent (inherits trace_id, creates child span)
      ← Agent returns (span completed)
    ← Domain returns (span completed)
  ← Orchestrator returns (root span completed)
```

### Headers

| Header | Description |
|--------|-------------|
| `X-Trace-Id` | 16-byte hex trace identifier (32 chars) |
| `X-Span-Id` | 8-byte hex span identifier (16 chars) |
| `X-Parent-Span-Id` | Parent span for child spans |

### Span Model

```json
{
  "trace_id": "abc123def456789012345678",
  "span_id": "span1234abcd",
  "parent_span_id": null,
  "name": "orchestrator.handle_task",
  "component": "orchestrator",
  "start_time": "2026-04-25T10:30:01.000Z",
  "end_time": "2026-04-25T10:30:03.100Z",
  "duration_ms": 2100,
  "status": "ok",
  "attributes": {
    "task_id": "task-a1b2c3",
    "domain": "seo",
    "workflow": "seo-audit"
  },
  "events": [
    {
      "name": "agent.dispatch",
      "time": "2026-04-25T10:30:01.050Z",
      "attributes": {"agent": "seo-analyzer"}
    }
  ]
}
```

### Trace ID Generation

- Generated by the orchestrator at request entry point
- Format: 32 hex characters (128-bit random)
- Source: `crypto/rand` (not `math/rand`)
- If an incoming request already carries `X-Trace-Id`, the
  orchestrator preserves it (for federation or external integration)

### Span Lifecycle

```
1. On entry to a component:
   a. Read X-Trace-Id from incoming request (or generate if missing)
   b. Read X-Span-Id as parent_span_id
   c. Generate new span_id
   d. Record start_time
   e. Set span name = "<component>.<operation>"
2. On outgoing requests to other components:
   a. Set X-Trace-Id = trace_id
   b. Set X-Span-Id = new span_id for this call
   c. Set X-Parent-Span-Id = current span_id
3. On exit from component:
   a. Record end_time and duration
   b. Set status (ok, error)
   c. Emit span to configured exporter
```

### Trace Export

Spans are emitted as structured JSON logs by default (same stdout
stream, with `"type": "span"`). For production deployments, spans
can be exported to:

- **OTLP endpoint**: Set `OTEL_EXPORTER_OTLP_ENDPOINT` environment
  variable. The component pushes spans via HTTP/protobuf.
- **File**: Set `WL_TRACE_FILE=/path/to/traces.jsonl` to write
  spans to a file (one JSON object per line).

---

## Metrics

### Metrics Endpoint

Every component exposes `GET /metrics` returning metrics in
Prometheus exposition format.

```
# HELP wl_tasks_total Total tasks processed
# TYPE wl_tasks_total counter
wl_tasks_total{component="seo-analyzer",status="completed"} 45
wl_tasks_total{component="seo-analyzer",status="failed"} 2

# HELP wl_task_duration_seconds Task processing duration
# TYPE wl_task_duration_seconds histogram
wl_task_duration_seconds_bucket{component="seo-analyzer",le="0.5"} 5
wl_task_duration_seconds_bucket{component="seo-analyzer",le="1"} 15
wl_task_duration_seconds_bucket{component="seo-analyzer",le="5"} 40
wl_task_duration_seconds_bucket{component="seo-analyzer",le="10"} 45
wl_task_duration_seconds_bucket{component="seo-analyzer",le="+Inf"} 47
wl_task_duration_seconds_sum{component="seo-analyzer"} 108.5
wl_task_duration_seconds_count{component="seo-analyzer"} 47
```

### Standard Metrics

#### Orchestrator Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `wl_agents_registered` | gauge | — | Total registered agents |
| `wl_agents_status` | gauge | `status` | Agents by status (online/degraded/offline) |
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

Every component's `/health` endpoint returns structured health data
suitable for monitoring:

```json
{
  "status": "healthy",
  "component": "seo-analyzer",
  "version": "1.0.0",
  "uptime_seconds": 172800,
  "checks": {
    "storage": "ok",
    "llm": "ok",
    "dependencies": "ok"
  },
  "metrics_snapshot": {
    "tasks_24h": 45,
    "error_rate": 0.04,
    "avg_latency_ms": 2300
  }
}
```

### Health Status Values

| Status | Meaning | HTTP Code |
|--------|---------|-----------|
| healthy | All systems operational | 200 |
| degraded | Functioning with reduced capability | 200 |
| unhealthy | Not functioning correctly | 503 |

---

## Correlation Patterns

### End-to-End Task Trace

Given a `task_id`, you can reconstruct the full execution path:

```
1. grep logs for task_id → find trace_id
2. grep logs for trace_id → get all log lines across all components
3. Sort by timestamp → chronological execution flow
4. Filter by type=span → get span tree for timing analysis
```

### Agent Debugging

```bash
# All errors from a specific agent in the last hour
cat logs.jsonl | jq 'select(.component == "seo-analyzer" and .level == "error")'

# Slow tasks (>5s) across all agents
cat logs.jsonl | jq 'select(.duration_ms > 5000 and .msg == "Task completed")'

# Trace a specific workflow execution
cat logs.jsonl | jq 'select(.trace_id == "abc123...")'
```

### Dashboard Queries

For deployments using a log aggregation service (Loki, Elasticsearch,
CloudWatch Logs):

```
# Error rate by agent (last 24h)
count_over_time({component_type="agent"} | json | level="error" [24h])
  / count_over_time({component_type="agent"} [24h])

# P95 task duration by domain
histogram_quantile(0.95, sum(rate(wl_task_duration_seconds_bucket[5m])) by (le, domain))

# Active agents
wl_agents_status{status="online"}
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_LOG_LEVEL` | `info` | Global log level |
| `WL_LOG_FORMAT` | `json` | `json` or `text` (text for local dev) |
| `WL_TRACE_ENABLED` | `false` | Enable distributed tracing |
| `WL_TRACE_SAMPLE_RATE` | `1.0` | Trace sampling rate (0.0–1.0) |
| `WL_TRACE_FILE` | — | File path for span export |
| `WL_METRICS_ENABLED` | `true` | Expose /metrics endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector URL for trace export |

### Local Development

In development mode (`weblisk dev`):
- Log format defaults to `text` (human-readable, colorized)
- Tracing is disabled (less noise)
- Metrics endpoint is available at each component's port + `/metrics`
- All components log to their own stdout (visible in terminal)

### Production

In production:
- Log format: `json` (parseable by log aggregation)
- Tracing: enabled with sampling (0.1 = 10% of requests)
- Metrics: scraped by Prometheus or compatible collector
- Components write to stdout; container runtime captures logs

---

## Implementation Notes

- Structured logging MUST be the default — never use unstructured
  `fmt.Println` or equivalent for operational events
- Trace IDs MUST be propagated on ALL inter-component HTTP requests,
  including health checks and governance calls
- The `/metrics` endpoint MUST NOT require authentication (standard
  Prometheus convention)
- Metrics MUST NOT include PII or sensitive data in labels
- Log rotation is the responsibility of the runtime environment
  (container, systemd, etc.), not the application
- Components SHOULD limit log output to ~100 lines per task at
  `info` level to prevent log flooding
- Span events (within a span) should be used sparingly — major
  milestones only, not every function call

## Verification Checklist

- [ ] All components emit JSON logs to stdout with required fields: ts (ISO 8601), level, msg, component, component_type
- [ ] Log levels are configurable globally via WL_LOG_LEVEL and per-component via log_level_overrides
- [ ] Trace ID (X-Trace-Id, 32 hex chars from crypto/rand) is propagated on ALL inter-component HTTP requests
- [ ] Incoming requests with an existing X-Trace-Id preserve it; new trace IDs are generated only when missing
- [ ] Each component creates child spans with X-Span-Id and X-Parent-Span-Id on outgoing requests
- [ ] GET /metrics returns Prometheus exposition format with wl_ prefix and does NOT require authentication
- [ ] Orchestrator exposes wl_agents_registered, wl_tasks_total, wl_task_duration_seconds, and wl_http_requests_total metrics
- [ ] Agent metrics include wl_tasks_total by action/status, wl_llm_calls_total, and wl_llm_tokens_total by model/type
- [ ] Metrics labels do NOT include high-cardinality values (user_id, URL) or PII
- [ ] Health endpoint returns structured JSON with status, component, version, uptime_seconds, and checks map
- [ ] Spans are emitted as structured JSON logs (type: span) by default and exportable to OTLP when OTEL_EXPORTER_OTLP_ENDPOINT is set
- [ ] Components limit log output to ~100 lines per task at info level to prevent log flooding
