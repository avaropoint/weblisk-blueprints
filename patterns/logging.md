<!-- blueprint
type: pattern
name: logging
version: 2.0.0
requires: [protocol/types, architecture/agent]
platform: any
tier: free
-->

# Logging Pattern

## Overview

Every component writes each log record as one JSON line on standard output,
always, and pushes the same record as an OpenTelemetry log record (OTLP) where
telemetry is deployed; a runtime with no process standard output writes to the
console stream its platform blueprint names. Collection, indexing and search
are the deployment's. This pattern is the one home for what a record looks
like, which log types exist, how a record maps to the OpenTelemetry log data
model, what must never be written, and where a record is redacted.

The fields are [`LogEntry`](../protocol/types.md#logentry)'s.
[`architecture/observability`](../architecture/observability.md#structured-logging)
and [`protocol/spec`](../protocol/spec.md#structured-log-format) point here and
state none of it.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=2.0.0 <3.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version]
        - name: EventEnvelope
          fields_used: [trace_id, span_id, event_id, source]
        - name: LogEntry
          fields_used: [ts, level, log_type, msg, component, component_type, trace_id, span_id, task_id, domain, workflow, action, duration_ms, status, error, error_code, details]
        - name: TraceContext
          fields_used: [trace_id, span_id, sampled]
        - name: Span
          fields_used: [trace_id, span_id, parent_span_id, name, kind, component, start, end, status, attributes]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, detail, status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Structured always** — Every log line is valid JSON. No free-text
   logging. Human-readable messages go in the `msg` field.
2. **Correlation by default** — Every log line written while a request is
   served carries its `trace_id` and `span_id`, and every line carries
   `component`, for cross-system tracing without post-processing.
3. **Event-typed** — Logs have a `log_type` field that categorizes
   the event, enabling automated filtering and alerting.
4. **Minimal overhead** — Logging MUST NOT degrade agent performance.
   Debug-level logging is disabled by default.
5. **No vendor lock-in** — The envelope maps onto the OpenTelemetry log data
   model, and standard output works with no collector at all.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: structured-logging
      description: Write each log record as one JSON line on standard output in the one envelope, and push it as an OpenTelemetry log record where telemetry is deployed
      parameters:
        - name: level
          type: string
          required: true
          description: Minimum log level — debug, info, warn, error
        - name: log_type
          type: string
          required: true
          description: Dot-separated event category for automated filtering
      inherits: Log envelope structure, required fields, contextual fields, standard log types
      overridable: true
      override_constraints: Must preserve required fields (ts, level, log_type, msg, component, component_type)

    - name: trace-correlation
      description: Carry the trace_id and span_id being served on every log line written while a request is served
      parameters:
        - name: trace_id
          type: string
          required: true
          description: The trace being served, as protocol/spec's Trace Propagation gives it or starts it
      inherits: Trace correlation rules, correlation field strategy
      overridable: false

    - name: redaction-at-emission
      description: Redact a record where it is emitted, before it is written or pushed
      required: true
      rules:
        - A log line, span or metric label MUST NOT carry what Sensitive Data forbids
        - A record carrying data above its scope is redacted where it is emitted, using the scope read from the payload, because a record once written cannot be un-leaked
        - Redaction is the emitting component's act, and nothing downstream is trusted to remove what was written

  types:
    - name: LogEntry
      description: The log envelope, as protocol/types declares it, provided to extenders
      inherited_by: Log Envelope section
    - name: LogType
      description: The one log_type vocabulary — process, action, execute, collaboration, storage, security, audit, error and trace events
      inherited_by: Log Types section

  events:
    - topic: logging.level_changed
      description: Emitted when the log level is changed at runtime
      payload: {component, from_level, to_level}
```

---

## Log Envelope

Every log line a component writes is one `LogEntry`:

```json
{
  "ts": "2026-04-25T10:30:01.123Z",
  "level": "info",
  "log_type": "action.completed",
  "msg": "Task registered successfully",
  "component": "cron",
  "component_type": "agent",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "task_id": "task-a1b2c3",
  "domain": "infrastructure",
  "duration_ms": 45,
  "details": {}
}
```

### Fields

Each field, its type and whether it is required are
[`LogEntry`](../protocol/types.md#logentry)'s, `ts`'s format among them. This
pattern adds when each optional field is present:

| Field | When Present |
|-------|-------------|
| trace_id, span_id | While a request is being served, always |
| task_id | During task or action processing |
| domain | When operating within a domain context |
| workflow | During workflow execution |
| action | During action processing |
| duration_ms, status | On operation completion |
| error, error_code | On error |
| details | When the log type declares details |

### OpenTelemetry Log Data Model

A record pushed as OTLP is the same record, field for field:

| LogEntry | OpenTelemetry log record |
|----------|--------------------------|
| `ts` | `Timestamp` |
| `level` | `SeverityText`, and `SeverityNumber` 5, 9, 13 or 17 for `debug`, `info`, `warn` or `error` |
| `log_type` | `EventName` |
| `msg` | `Body` |
| `component` | the resource attribute `service.name` |
| `component_type` | the resource attribute `weblisk.component_type` |
| `trace_id`, `span_id` | `TraceId`, `SpanId`; `TraceFlags` is the trace's sampled flag |
| `error` | the attribute `exception.message` |
| `error_code` | the attribute `error.type` |
| `task_id`, `domain`, `workflow`, `action`, `duration_ms`, `status` | attributes of the same name under `weblisk.` |
| `details` | attributes under `weblisk.details.` |

---

## Log Types

Log types categorize records for automated processing. Agents MUST
use standard log types for framework events and MAY define custom
types for agent-specific events.

### Standard Log Types

A standard type's first segment is never an event namespace a component owns
([`protocol/spec`](../protocol/spec.md#namespace-control)): every component
writes these, and a reader filtering on a namespace must get that namespace's
owner alone.

#### Process Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `process.startup` | info | Process starts | `{port, version, blueprint}` |
| `process.ready` | info | Registered and ready | `{agent_id, orchestrator}` |
| `process.shutdown` | info | Graceful shutdown begins | `{reason, in_flight_count}` |
| `process.stopped` | info | Fully stopped | `{uptime_seconds}` |
| `process.health_change` | warn | Health state transitions | `{from, to, reason}` |
| `process.version_updated` | info | Moved to a new blueprint version | `{from, to}` |
| `process.version_rollback` | warn | Rolled back to a previous blueprint version | `{from, to, reason}` |
| `process.version_retired` | info | An old version retired after a validated cutover | `{retired_version, active_version, uptime}` |
| `process.restored` | info | State restored from a backup | `{backup_file}` |

#### Action Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `action.received` | info | Action handler invoked | `{action, input_size_bytes}` |
| `action.completed` | info | Action succeeded | `{action, duration_ms, output_size_bytes}` |
| `action.failed` | error | Action failed | `{action, error, error_code, duration_ms}` |
| `action.rejected` | warn | Action rejected (validation, auth) | `{action, reason}` |

#### Execute Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `execute.received` | info | Execute handler invoked | `{task_id, action}` |
| `execute.completed` | info | Task succeeded | `{task_id, duration_ms, changes_count}` |
| `execute.failed` | error | Task failed | `{task_id, error, error_code}` |

#### Collaboration Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `event.published` | debug | Event published to bus | `{topic, event_id}` |
| `event.received` | debug | Event received from bus | `{topic, event_id, source}` |
| `event.processed` | debug | Event processing completed | `{topic, event_id, duration_ms}` |
| `event.failed` | warn | Event processing failed | `{topic, event_id, error, attempt}` |
| `message.sent` | debug | Direct message sent | `{target, action}` |
| `message.received` | debug | Direct message received | `{source, action}` |

#### Storage Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `storage.read` | debug | Storage read operation | `{table, duration_ms}` |
| `storage.write` | debug | Storage write operation | `{table, duration_ms, rows_affected}` |
| `storage.error` | error | Storage operation failed | `{table, operation, error}` |

#### Security Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `security.auth_success` | debug | Request authenticated | `{method, identity}` |
| `security.auth_failure` | warn | Authentication failed | `{method, reason, source_ip}` |
| `security.permission_denied` | warn | Authorization failed | `{action, required, actual}` |
| `security.override` | info | Manual override applied | `{operator, action, reason}` |

#### Audit Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `audit` | info | An entry was appended to the orchestrator's audit log | The `AuditEntry` ([`protocol/types`](../protocol/types.md#auditentry)) |

The audit log itself is the orchestrator's chained record; this line is only
its echo.

#### Error Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `error.unhandled` | error | Unexpected error caught | `{error, stack_trace}` |
| `error.panic` | error | Process panic/crash | `{error, stack_trace}` |

#### Trace Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `span` | info | A sampled span closed ([`architecture/observability`](../architecture/observability.md#distributed-tracing)) | The `Span` ([`protocol/types`](../protocol/types.md#span)) |

A span line's own `trace_id` and `span_id` are the span's.

### Custom Log Types

Agents MAY define custom log types using the pattern:

```
<agent_name>.<entity>.<action>
```

Example: `cron.task.fired`, `alerting.notification.sent`

`<agent_name>` is the agent's own event namespace, so a filter on a namespace
still returns its owner alone. An agent never defines a type under a
namespace it does not own; the rule for standard types above is about types
every component writes.

Custom log types MUST be documented in the agent's blueprint under
the Observability section.

---

## Log Levels

| Level | Usage | Default State |
|-------|-------|--------------|
| debug | Verbose diagnostic detail — individual storage reads, event processing | Disabled in production |
| info | Normal operations — startup, action completion, state changes | Always enabled |
| warn | Recoverable issues — retries, degraded state, auth failures | Always enabled |
| error | Failures — task failed, storage error, unhandled exception | Always enabled |

### Level Configuration

```yaml
logging:
  level: info                    # Global minimum level
  level_overrides:               # Per-component overrides
    seo-analyzer: debug
    orchestrator: warn
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Log level | `info` | Minimum log level |
| Log level overrides | `""` | Per-component level overrides (component=level pairs) |

There is no output setting and no text format. Records are JSON lines on
standard output, and a person reads them through a tool that renders them.

---

## Correlation

### Trace Correlation

Every log line written while a request is served MUST include its `trace_id`,
and the `span_id` of the span open when it was written. How a trace arrives,
starts and is sent on is
[`protocol/spec`](../protocol/spec.md#trace-propagation)'s.

```
Incoming request (traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01)
  → every log line written while serving it carries trace_id 4bf92f3577b34da6a3ce929d0e0e4736
  → and the span_id of the span open at the time
```

### Correlation Fields

For debugging a specific flow across multiple agents:

```
jq 'select(.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736")' captured-stdout.jsonl
```

Returns every log line from every component involved in that request.

---

## Log Rotation

Rotation is the responsibility of the container runtime or process manager
that captures standard output. A component does not manage rotation, and
writes to no log file of its own.

---

## Sensitive Data

Logs MUST NOT contain:

| Forbidden | Alternative |
|-----------|-------------|
| Authentication tokens | `token: "***"` or omit entirely |
| Private keys | Never log |
| Passwords | Never log |
| PII (email, phone, address) | Hash or redact: `email: "a***@example.com"` |
| Full request/response bodies | Log size only: `input_size_bytes: 1024` |

A record, a span's attributes and a metric's labels are redacted where they
are emitted (`redaction-at-emission`, [Contracts](#contracts)). A blueprint
whose records must be redacted points here.

---

## Blueprint Declaration

Agents extending this pattern declare their custom log types:

```markdown
extends: [patterns/logging]

## Observability

### Custom Log Types
| Log Type | Level | When | Details |
|----------|-------|------|---------|
| cron.task.fired | info | Scheduled task dispatched | {task_id, target_agent} |
| cron.task.retry | warn | Task retry scheduled | {task_id, attempt, next_retry} |
```

All standard log types are inherited automatically. Only
agent-specific custom types need to be declared.

---

## Implementation Notes

- Log emission MUST be non-blocking. If stdout is backed up, or a push to
  telemetry cannot be sent, logs MAY be dropped rather than blocking the
  agent's event loop. Dropped logs SHOULD increment a dropped logs counter.
- `ts` carries milliseconds, the precision its one format fixes; use
  `duration_ms` for a duration rather than subtracting two timestamps.
- The `details` field is typed per `log_type`. Implementations SHOULD
  validate that details match the expected schema in debug builds.
- Stack traces in error logs SHOULD be truncated to 20 frames maximum.
- Log lines SHOULD NOT exceed 8 KB. Oversized payloads in `details`
  SHOULD be truncated with a `truncated: true` flag.

## Verification Checklist

- [ ] Every log line is one JSON object on standard output with the required `LogEntry` fields (`ts`, `level`, `log_type`, `msg`, `component`, `component_type`)
- [ ] Where telemetry is deployed, every record is also pushed as an OpenTelemetry log record mapped as the OpenTelemetry Log Data Model table says
- [ ] Every log line written while a request is served carries its `trace_id` and the `span_id` open at the time
- [ ] Standard `process.*` log types emit at correct points (`process.startup`, `process.ready`, `process.shutdown`, `process.stopped`)
- [ ] Standard action log types emit for every action (received, completed, failed)
- [ ] No standard log type's first segment is an event namespace a component owns
- [ ] Error logs include error code and message
- [ ] Log level filtering works (debug disabled by default)
- [ ] Per-component level overrides work
- [ ] Sensitive data (tokens, keys, PII) is never logged, and a record is redacted where it is emitted (`redaction-at-emission`)
- [ ] Custom log types follow the naming convention
- [ ] Log lines do not exceed 8 KB
