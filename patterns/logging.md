<!-- blueprint
type: pattern
name: logging
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, architecture/observability]
platform: any
tier: free
-->

# Logging Pattern

Standard structured logging contract for all Weblisk agents. Defines
the log envelope, required fields per event category, correlation
strategy, log levels, rotation, and retention. Agents that extend
this pattern emit consistent, machine-parseable logs that support
automated analysis, debugging, and audit compliance.

## Overview

Every agent emits structured JSON logs to stdout. This pattern
standardizes what fields appear in every log line, defines specific
log event types with required fields, and establishes the rules for
log rotation, retention, and forwarding.

This pattern builds on the structured logging section of
architecture/observability.md. Observability defines the system-wide
telemetry strategy; this pattern defines the enforceable per-agent
logging contract that agents extend.

---

## Design Principles

1. **Structured always** — Every log line is valid JSON. No free-text
   logging. Human-readable messages go in the `msg` field.
2. **Correlation by default** — Every log line carries `trace_id` and
   `component` for cross-system tracing without post-processing.
3. **Event-typed** — Logs have a `log_type` field that categorizes
   the event, enabling automated filtering and alerting.
4. **Minimal overhead** — Logging MUST NOT degrade agent performance.
   Debug-level logging is disabled by default.
5. **No vendor lock-in** — Logs go to stdout. Collection, indexing,
   and search are deployment concerns, not agent concerns.

---

## Log Envelope

Every log line emitted by an agent MUST conform to this structure:

```json
{
  "ts": "2026-04-25T10:30:01.123Z",
  "level": "info",
  "log_type": "action.completed",
  "msg": "Task registered successfully",
  "component": "cron",
  "component_type": "agent",
  "trace_id": "abc123def456789012345678",
  "span_id": "span-789",
  "task_id": "task-a1b2c3",
  "domain": "infrastructure",
  "duration_ms": 45,
  "details": {}
}
```

### Required Fields (every log line)

| Field | Type | Description |
|-------|------|-------------|
| ts | string | ISO 8601 timestamp with millisecond precision |
| level | string | `debug`, `info`, `warn`, `error` |
| log_type | string | Dot-separated event category (see Log Types) |
| msg | string | Human-readable summary (max 256 chars) |
| component | string | Agent name from blueprint metadata |
| component_type | string | `agent`, `domain`, `orchestrator` |

### Contextual Fields (when available)

| Field | Type | When Present |
|-------|------|-------------|
| trace_id | string | Always (from request context or generated) |
| span_id | string | When distributed tracing is enabled |
| task_id | string | During task or action processing |
| domain | string | When operating within a domain context |
| workflow | string | During workflow execution |
| action | string | During action processing |
| duration_ms | int | On operation completion |
| status | string | On operation completion (`success`, `failed`, `timeout`) |
| error | string | On error — error message |
| error_code | string | On error — structured error code |
| details | object | Event-specific data (typed per log_type) |

---

## Log Types

Log types categorize events for automated processing. Agents MUST
use standard log types for framework events and MAY define custom
types for agent-specific events.

### Standard Log Types

#### Lifecycle Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `lifecycle.startup` | info | Agent process starts | `{port, version, blueprint}` |
| `lifecycle.ready` | info | Agent is registered and ready | `{agent_id, orchestrator}` |
| `lifecycle.shutdown` | info | Agent begins graceful shutdown | `{reason, in_flight_count}` |
| `lifecycle.stopped` | info | Agent has fully stopped | `{uptime_seconds}` |
| `lifecycle.health_change` | warn | Health state transitions | `{from, to, reason}` |

#### Action Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `action.received` | info | Action handler invoked | `{action, input_size_bytes}` |
| `action.completed` | info | Action succeeded | `{action, duration_ms, output_size_bytes}` |
| `action.failed` | error | Action failed | `{action, error, error_code, duration_ms}` |
| `action.rejected` | warn | Action rejected (validation, auth) | `{action, reason}` |

#### Task Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `task.received` | info | Execute handler invoked | `{task_id, action}` |
| `task.completed` | info | Task succeeded | `{task_id, duration_ms, changes_count}` |
| `task.failed` | error | Task failed | `{task_id, error, error_code}` |

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

#### Error Events

| Log Type | Level | When | Required Details |
|----------|-------|------|-----------------|
| `error.unhandled` | error | Unexpected error caught | `{error, stack_trace}` |
| `error.panic` | error | Process panic/crash | `{error, stack_trace}` |

### Custom Log Types

Agents MAY define custom log types using the pattern:

```
<agent_name>.<entity>.<action>
```

Example: `cron.task.fired`, `alerting.notification.sent`

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

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_LOG_LEVEL` | `info` | Minimum log level |
| `WL_LOG_LEVEL_OVERRIDES` | `""` | Comma-separated `component=level` pairs |
| `WL_LOG_FORMAT` | `json` | Output format: `json` or `text` (dev only) |
| `WL_LOG_OUTPUT` | `stdout` | Output target: `stdout`, `stderr`, or file path |

### Text Format (Development Only)

For local development, `WL_LOG_FORMAT=text` produces human-readable
output:

```
2026-04-25 10:30:01.123 INFO  [cron] action.completed — Task registered successfully (45ms)
```

Text format MUST NOT be used in production. Automated log consumers
expect JSON.

---

## Correlation

### Trace ID Propagation

Every log line MUST include `trace_id` when processing a request that
carries trace context. Trace IDs propagate via HTTP headers (see
architecture/observability) and event envelopes (see patterns/messaging).

```
Incoming request (X-Trace-Id: abc123)
  → All log lines during processing include trace_id: "abc123"
  → All events published include trace_id: "abc123"
  → Downstream agents inherit trace_id: "abc123"
```

When no trace context exists (e.g., timer-triggered actions), the
agent MUST generate a new trace_id.

### Correlation Fields

For debugging a specific flow across multiple agents:

```
grep trace_id=abc123 *.log
```

Returns every log line from every component involved in that request.

---

## Log Rotation

### File-Based Rotation

When `WL_LOG_OUTPUT` is a file path:

```yaml
rotation:
  max_size: 100MB              # Rotate when file exceeds size
  max_age: 7                   # Days to retain rotated files
  max_backups: 5               # Max rotated files to keep
  compress: true               # Gzip rotated files
```

### Stdout (Default)

When logging to stdout (default), rotation is the responsibility of
the container runtime or process manager. The agent does not manage
rotation for stdout output.

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

Agents SHOULD implement a log sanitizer that strips or redacts
sensitive fields before emission.

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

- Log emission MUST be non-blocking. If stdout is backed up, logs
  MAY be dropped rather than blocking the agent's event loop. Dropped
  logs SHOULD increment a `wl_logs_dropped_total` counter.
- Timestamp precision matters. Use the highest precision available
  (milliseconds minimum, microseconds if supported) for accurate
  duration calculations.
- The `details` field is typed per `log_type`. Implementations SHOULD
  validate that details match the expected schema in debug builds.
- Stack traces in error logs SHOULD be truncated to 20 frames maximum.
- Log lines SHOULD NOT exceed 8 KB. Oversized payloads in `details`
  SHOULD be truncated with a `truncated: true` flag.

## Verification Checklist

- [ ] All log lines are valid JSON with required fields (ts, level, log_type, msg, component, component_type)
- [ ] Trace ID is present in all log lines during request processing
- [ ] Trace ID is generated for timer-triggered operations
- [ ] Standard lifecycle log types emit at correct points (startup, ready, shutdown, stopped)
- [ ] Standard action log types emit for every action (received, completed, failed)
- [ ] Error logs include error code and message
- [ ] Log level filtering works (debug disabled by default)
- [ ] Per-component level overrides work
- [ ] Sensitive data (tokens, keys, PII) is never logged
- [ ] Custom log types follow the naming convention
- [ ] Log rotation works when file output is configured
- [ ] Text format works for development
- [ ] Log lines do not exceed 8 KB
