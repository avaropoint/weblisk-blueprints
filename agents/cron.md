<!-- blueprint
type: agent
kind: infrastructure
name: cron
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent]
platform: any
tier: free
-->

# Cron Agent

Scheduled task execution with cron-style expressions. Supports
one-time and recurring tasks with retry logic and execution history.

## Overview

The cron agent manages scheduled work within a Weblisk server. Other
agents and application code register tasks with cron expressions or
one-time timestamps. The cron agent evaluates schedules, dispatches
tasks at the correct time, tracks execution results, and retries
failed tasks according to their configuration.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "database:read", "resources": ["cron_tasks", "cron_history"]},
    {"name": "database:write", "resources": ["cron_tasks", "cron_history"]}
  ],
  "inputs": [
    {"name": "task_definition", "type": "json", "description": "Task to schedule"}
  ],
  "outputs": [
    {"name": "execution_result", "type": "json", "description": "Task execution outcome"}
  ],
  "collaborators": []
}
```

## Triggers

| Trigger | Description |
|---------|-------------|
| Schedule: `* * * * *` | Tick every minute — evaluate all pending schedules |
| Event: `cron.register` | New task registered |
| Event: `cron.cancel` | Task cancelled |

## Configuration

```yaml
config:
  tick_interval: 60            # seconds between schedule checks
  max_retries: 3               # default retries per task
  retry_backoff: exponential   # fixed | exponential
  max_concurrent: 10           # max tasks executing simultaneously
  history_retention: 604800    # 7 days in seconds
```

## Execute Workflow

```
Phase 1 — Tick:
  Load all active tasks from storage.
  For each task, evaluate whether it should fire now:
  - Cron expression: parse and check if current minute matches
  - One-time: check if scheduled time has passed and task hasn't fired

Phase 2 — Dispatch:
  For each due task (up to max_concurrent):
  - If task.target_agent is set:
      Send message to target agent via POST /v1/message
      Action: task.action, Payload: task.payload
  - If task.target_url is set:
      POST to URL with task.payload as body
  - Record execution start in history

Phase 3 — Collect results:
  Wait for responses (with timeout per task, default 30s).
  Record result in history:
  - status: success | failed | timeout
  - response: truncated response body
  - duration_ms: execution time

Phase 4 — Handle failures:
  If task failed and retries remain:
  - Decrement retry count
  - Schedule retry based on backoff strategy
  If max retries exhausted:
  - Mark task as failed
  - Log final failure

Phase 5 — Cleanup:
  For one-time tasks that succeeded: mark as completed
  For recurring tasks: compute next fire time
  Purge history entries older than history_retention
```

## HandleMessage Actions

### register

Register a new scheduled task.

- Input:
```json
{
  "name": "daily-report",
  "schedule": "0 9 * * *",
  "target_agent": "email-send",
  "action": "send_report",
  "payload": {"report_type": "daily"},
  "max_retries": 3,
  "timeout": 30
}
```
- Output: `{task_id: "...", next_fire: timestamp}`

### cancel

Cancel a scheduled task.

- Input: `{task_id: "..."}`
- Output: `{cancelled: true}`

### list

List active tasks.

- Input: `{status: "active|paused|all"}`
- Output: `{tasks: [...]}`

### history

Get execution history for a task.

- Input: `{task_id: "...", limit: 20}`
- Output: `{executions: [...]}`

### pause / resume

Pause or resume a task without deleting it.

- Input: `{task_id: "..."}`
- Output: `{task_id: "...", status: "paused|active"}`

## Cron Expression Format

Standard 5-field cron expressions:

```
┌───────── minute (0-59)
│ ┌───────── hour (0-23)
│ │ ┌───────── day of month (1-31)
│ │ │ ┌───────── month (1-12)
│ │ │ │ ┌───────── day of week (0-6, 0=Sunday)
│ │ │ │ │
* * * * *
```

Special characters: `*` (any), `,` (list), `-` (range), `/` (step).

Examples:
- `*/5 * * * *` — every 5 minutes
- `0 9 * * 1-5` — 9 AM weekdays
- `0 0 1 * *` — midnight on the 1st of each month

For one-time tasks, use `"once"` with a `fire_at` timestamp instead
of a cron expression.

## Types

### CronTask

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| task_id | string | yes | Unique task identifier |
| name | string | yes | Human-readable task name |
| schedule | string | yes | Cron expression or "once" |
| fire_at | int64 | no | One-time fire timestamp (when schedule = "once") |
| target_agent | string | no | Agent to message (mutually exclusive with target_url) |
| target_url | string | no | URL to POST to (mutually exclusive with target_agent) |
| action | string | no | Message action (when targeting agent) |
| payload | object | no | Data to send with the task |
| max_retries | int | yes | Max retry attempts |
| timeout | int | yes | Execution timeout in seconds |
| status | string | yes | active, paused, completed, failed |
| next_fire | int64 | no | Next scheduled execution |
| created_at | int64 | yes | Task creation timestamp |

### CronExecution

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| execution_id | string | yes | Unique execution ID |
| task_id | string | yes | Parent task ID |
| fired_at | int64 | yes | When execution started |
| status | string | yes | success, failed, timeout |
| duration_ms | int | no | Execution duration |
| response | string | no | Truncated response (max 1 KB) |
| attempt | int | yes | Attempt number (1-based) |

## Implementation Notes

- **Clock precision**: The tick evaluates once per `tick_interval`.
  Tasks are not guaranteed to fire at the exact second — only within
  the tick window.
- **Concurrency control**: Use `max_concurrent` to prevent overloading
  the system. Queue excess tasks for the next tick.
- **Persistence**: Task definitions and execution history MUST be
  persisted. In-memory only is not acceptable — server restarts must
  not lose schedules.
- **Timezone**: All cron expressions are evaluated in UTC. Implementations
  SHOULD document this clearly.
- **Distributed locking**: In multi-instance deployments, only one
  instance should evaluate the schedule per tick. Use a distributed
  lock or leader election.
- **Idempotency**: Task IDs prevent duplicate registrations. Re-registering
  an existing task_id updates it rather than creating a duplicate.

## Verification Checklist

- [ ] Tasks can be registered with cron expressions
- [ ] One-time tasks fire at the specified timestamp
- [ ] Recurring tasks compute the correct next fire time
- [ ] Tasks are dispatched to target agents via /v1/message
- [ ] Failed tasks are retried with configured backoff
- [ ] Max retries is enforced
- [ ] Execution history is recorded
- [ ] Tasks can be paused, resumed, and cancelled
- [ ] History is purged after retention period
- [ ] Concurrent execution limit is enforced
