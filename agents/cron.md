<!-- blueprint
type: agent
kind: infrastructure
name: cron
version: 1.0.0
port: 9750
requires: [protocol/spec, protocol/types, architecture/agent, architecture/orchestrator, architecture/change-management]
extends: [patterns/scheduling, patterns/messaging, patterns/logging, patterns/retry, patterns/versioning, patterns/observability, patterns/storage, patterns/state-machine, patterns/scope, patterns/policy, patterns/safety, patterns/security, patterns/governance]
depends_on: []
platform: any
tier: free
-->

# Cron Agent

Scheduled task execution with cron-style expressions. Supports
one-time and recurring tasks with retry logic, execution history,
and event-driven dispatch.

## Overview

The cron agent manages scheduled work within a Weblisk server. Other
agents register tasks with cron expressions or one-time timestamps.
The cron agent evaluates schedules on a configurable tick interval,
dispatches due tasks to target agents via the event bus or direct
message, tracks execution results, and retries failed tasks according
to their configuration.

The cron agent has zero external dependencies — it runs in isolation
and communicates exclusively through the Weblisk messaging bus and
protocol endpoints.

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
          request_type: AgentMessage
          response_fields: [status, response]
        - path: /v1/health
          methods: [POST]
          response_fields: [status, details]
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
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: EventEnvelope
          fields_used: [from, to, action, payload, trace_id]
        - name: HealthStatus
          fields_used: [status, details]
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
  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token]
        - path: /v1/services
          methods: [POST]
          response_fields: [agents]
      events:
        - topic: system.agent.registered
          fields_used: [agent_name, manifest]
        - topic: system.agent.deregistered
          fields_used: [agent_name]
        - topic: system.shutdown
          fields_used: []
        - topic: system.blueprint.changed
          fields_used: [blueprint_name, version, diff]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes, relationships, constraints]
        - behavior: backup-restore
          parameters: [frequency, format, path]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/observability
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
  - blueprint: architecture/change-management
    version: ">=1.0.0 <2.0.0"
    bindings:
      events:
        - topic: system.change.assessment
          fields_used: [agent, change_id, impact, affected_bindings, recommended_action, deadline]
        - topic: system.change.rollback
          fields_used: [change_id, reason]
      patterns:
        - behavior: reconciliation
          parameters: [on_change, self-validation, version-bump]
        - behavior: blue-green
          parameters: [shadow, cutover, rollback]
    on_change:
      compatible: validate
      breaking: halt-and-reconcile
      removed: halt-immediately

extends:
  - pattern: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: publish
          parameters: [topic, payload, source]
        - behavior: subscribe
          parameters: [topic, handler, consumer_group]
        - behavior: dead-letter
          parameters: [max_retries, dlq_topic]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/logging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: log-envelope
          parameters: [log_type, level, fields, trace_id]
        - behavior: log-rotation
          parameters: [max_size, max_files]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/retry
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: retry-with-backoff
          parameters: [max_retries, backoff_strategy, timeout]
        - behavior: circuit-breaker
          parameters: [failure_threshold, recovery_timeout]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/versioning
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: schema-migration
          parameters: [diff, migrate, rollback]
        - behavior: revision-tracking
          parameters: [current_version, previous_version]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

depends_on: []
  # No runtime agent dependencies. The cron agent operates independently.
  # It dispatches to target agents, but if a target is unavailable the
  # task is retried or failed — the cron agent itself does not degrade.
```

---

## Configuration

```yaml
config:
  tick_interval:
    type: int
    default: 60
    env: WL_CRON_TICK_INTERVAL
    min: 1
    max: 3600
    unit: seconds
    description: Schedule evaluation frequency

  max_retries:
    type: int
    default: 3
    env: WL_CRON_MAX_RETRIES
    min: 0
    max: 100
    description: Default retry attempts per task

  retry_backoff:
    type: string
    default: exponential
    env: WL_CRON_RETRY_BACKOFF
    enum: [fixed, linear, exponential]
    description: Backoff strategy between retries

  max_concurrent:
    type: int
    default: 10
    env: WL_CRON_MAX_CONCURRENT
    min: 1
    max: 100
    description: Max tasks dispatched simultaneously per tick

  history_retention:
    type: int
    default: 604800
    env: WL_CRON_HISTORY_RETENTION
    min: 0
    unit: seconds
    description: Execution history TTL (0 = disabled)

  task_timeout:
    type: int
    default: 30
    env: WL_CRON_TASK_TIMEOUT
    min: 1
    max: 300
    unit: seconds
    description: Default per-task execution timeout

  lock_ttl:
    type: int
    default: 120
    env: WL_CRON_LOCK_TTL
    min: 10
    unit: seconds
    description: Distributed tick lock TTL
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  CronTask:
    description: A scheduled task definition
    fields:
      task_id:
        type: string
        format: uuid-v7
        description: Unique task identifier
      name:
        type: string
        max: 128
        description: Human-readable task name
      schedule:
        type: string
        description: Cron expression or "once"
      fire_at:
        type: int64
        required_when: schedule = "once"
        description: One-time fire timestamp (epoch seconds)
      target_agent:
        type: string
        exclusive_with: target_url
        description: Agent name to dispatch to
      target_url:
        type: string
        exclusive_with: target_agent
        description: URL to POST to
      action:
        type: string
        required_when: target_agent
        description: Message action name for target agent
      payload:
        type: object
        optional: true
        description: Data to send with the task
      max_retries:
        type: int
        default: 3
        min: 0
        max: 100
        description: Max retry attempts for this task
      timeout:
        type: int
        default: 30
        min: 1
        max: 300
        unit: seconds
        description: Execution timeout
      status:
        type: string
        enum: [active, paused, completed, failed, cancelled]
        description: Current task state
      next_fire:
        type: int64
        optional: true
        description: Next scheduled execution timestamp
      retry_count:
        type: int
        default: 0
        description: Current retry count for latest execution
      created_at:
        type: int64
        auto: true
        description: Task creation timestamp
      updated_at:
        type: int64
        auto: true
        description: Last modification timestamp
      created_by:
        type: string
        optional: true
        description: Identity of registering agent or operator
    constraints:
      - name: uq_task_natural_key
        type: unique
        fields: [name, target_agent]
        description: Natural key for idempotent registration
      - name: ck_single_target
        type: check
        expression: (target_agent IS NOT NULL) XOR (target_url IS NOT NULL)
        description: Exactly one target type required
      - name: ck_once_needs_fire_at
        type: check
        expression: schedule != 'once' OR fire_at IS NOT NULL
        description: One-time tasks require fire_at

  CronExecution:
    description: Record of a single task execution attempt
    fields:
      execution_id:
        type: string
        format: uuid-v7
        description: Unique execution identifier
      task_id:
        type: string
        format: uuid-v7
        references: CronTask.task_id
        description: Parent task
      fired_at:
        type: int64
        description: When execution started
      completed_at:
        type: int64
        optional: true
        description: When execution finished
      status:
        type: string
        enum: [pending, success, failed, timeout]
        description: Execution outcome
      duration_ms:
        type: int
        optional: true
        description: Execution duration in milliseconds
      response:
        type: text
        max: 1024
        optional: true
        description: Truncated response body
      error:
        type: text
        optional: true
        description: Error message on failure
      error_code:
        type: string
        optional: true
        description: Structured error code
      attempt:
        type: int
        min: 1
        description: Attempt number (1-based)
      trace_id:
        type: string
        description: Trace context for correlation
    constraints:
      - name: ck_attempt_positive
        type: check
        expression: attempt >= 1

  CronLock:
    description: Distributed lock for tick coordination
    fields:
      lock_key:
        type: string
        description: Lock identifier (e.g. "tick")
      holder:
        type: string
        description: Instance ID holding the lock
      acquired_at:
        type: int64
        description: Lock acquisition timestamp
      expires_at:
        type: int64
        description: Lock expiration timestamp
```

---

## Storage

Storage tables reference the Types section. Fields are not redefined
here — the `source_type` key links each table to its type definition.

```yaml
storage:
  engine: sqlite

  tables:
    cron_tasks:
      source_type: CronTask
      primary_key: task_id
      indexes:
        - name: idx_task_natural_key
          fields: [name, target_agent]
          type: unique
        - name: idx_active_schedule
          fields: [status, next_fire]
          type: btree
          description: Fast lookup of due tasks per tick
        - name: idx_created
          fields: [created_at]
          type: btree

    cron_executions:
      source_type: CronExecution
      primary_key: execution_id
      indexes:
        - name: idx_task_history
          fields: [task_id, fired_at]
          type: btree
          description: History lookup ordered by recency
        - name: idx_exec_status
          fields: [status]
          type: btree
        - name: idx_trace
          fields: [trace_id]
          type: btree

    cron_locks:
      source_type: CronLock
      primary_key: lock_key
      indexes:
        - name: idx_lock_expiry
          fields: [expires_at]
          type: btree

  relationships:
    - name: task_executions
      from: cron_executions.task_id
      to: cron_tasks.task_id
      cardinality: many-to-one
      on_delete: cascade
      on_update: restrict
      description: Each execution belongs to exactly one task.
                   Deleting a task cascades to all its executions.

  retention:
    cron_tasks:
      policy: indefinite
      cleanup: manual via purge_completed action
    cron_executions:
      policy: config.history_retention
      cleanup: automatic every tick (Phase 7)
    cron_locks:
      policy: self-expiring via expires_at
      cleanup: automatic every tick (Phase 7)

  backup:
    cron_tasks:
      frequency: daily
      format: JSON export of all active and paused tasks
      path: .weblisk/backups/cron/cron_tasks_{ISO8601}.json
    cron_executions:
      frequency: daily
      format: JSON export (last 24 hours only)
      path: .weblisk/backups/cron/cron_executions_{ISO8601}.json
    cron_locks:
      backup: false
      reason: ephemeral — self-expiring
```

### Restore Procedure

```
1. Stop cron agent (or pause all tasks via pause_all)
2. Validate backup file:
   a. Parse JSON — must be valid
   b. Verify all required CronTask fields present per Types definition
   c. Verify all constraint checks pass (uq_task_natural_key, ck_single_target)
   d. Verify no duplicate task_ids
3. Clear existing cron_tasks table
4. Import tasks from backup file
5. Recompute next_fire for all active recurring tasks
6. Verify relationship integrity:
   a. No orphaned cron_executions (task_id must reference existing task)
7. Resume cron agent
8. Log: lifecycle.restored with {backup_file, tasks_imported, orphans_cleaned}
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
        trigger: tick_loop_started
        validates: first tick completes without unhandled error
      - from: active
        to: degraded
        trigger: storage_error
        validates: retry count < max per patterns/retry
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: SELECT 1 succeeds within 5 seconds
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
        validates: in_flight = 0 OR drain timeout (30s) elapsed

  entity.CronTask:
    initial: active
    transitions:
      - from: active
        to: paused
        trigger: pause action
        validates: task exists and status = active
        side_effect: clear next_fire
      - from: paused
        to: active
        trigger: resume action
        validates: next_fire recomputed from schedule
        side_effect: set next_fire
      - from: active
        to: completed
        trigger: one-time task execution succeeds
        validates: execution status = success AND schedule = "once"
        side_effect: record final CronExecution
      - from: active
        to: failed
        trigger: retries exhausted
        validates: retry_count >= CronTask.max_retries
        side_effect: emit cron.task.failed event
      - from: active
        to: cancelled
        trigger: cancel action
        validates: in-flight execution drained or timed out
        side_effect: clear next_fire
      - from: paused
        to: cancelled
        trigger: cancel action
        validates: task exists
        side_effect: clear next_fire
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Pre-check:   Process has read access to environment
  Validates:   All config values within declared min/max/enum constraints
  On Fail:     EXIT with CONFIG_INVALID — log which keys failed validation
  Backout:     None (nothing to reverse — process never started)

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/cron/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine (config.engine)
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE
  Backout:     Close any partial connection

Step 4 — Validate Schema
  Action:      Compare storage tables against Types block
  Pre-check:   Step 3 validated (storage connected)
  Validates:   All tables exist, all columns match type definitions,
               all indexes present, all constraints enforced,
               all relationships have valid FK references
  On Fail:     Run migration (per patterns/versioning)
               If migration fails → ROLLBACK migration steps in
               reverse order → EXIT with MIGRATION_FAILED
  Backout:     Reverse migration steps, restore previous schema version

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned in response body
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (registration is idempotent)

Step 6 — Subscribe to Events
  Action:      Subscribe to: system.agent.registered,
               system.agent.deregistered, system.shutdown,
               system.blueprint.changed
  Pre-check:   Step 5 validated (registered with orchestrator)
  Validates:   All 4 subscriptions acknowledged by message bus
  On Fail:     Unsubscribe any partial subscriptions →
               deregister from orchestrator (reverse step 5) →
               EXIT with SUBSCRIPTION_FAILED
  Backout:     Unsubscribe all, deregister, close storage

Step 7 — Acquire Tick Lock
  Action:      INSERT into cron_locks with lock_key = "tick"
  Pre-check:   Steps 3-4 validated (storage with schema)
  Validates:   Lock acquired OR another instance holds it (standby)
  On Fail:     Continue as standby — not a failure. Log and wait.
  Backout:     None (standby is a valid operating mode)

Step 8 — Load Active Tasks
  Action:      SELECT * FROM cron_tasks WHERE status = 'active'
  Pre-check:   Step 3 validated (storage accessible)
  Validates:   Query succeeds, all rows parse as CronTask type,
               all constraint checks pass
  On Fail:     Enter degraded state, retry on first tick
  Backout:     None (read-only operation)

Step 9 — Start Tick Loop
  Action:      Begin interval timer at config.tick_interval
  Pre-check:   Steps 1-8 validated (or standby for step 7)
  Validates:   First tick completes without unhandled error
  On Fail:     Stop timer → unsubscribe events → deregister →
               close storage → EXIT with TICK_LOOP_FAILED
  Backout:     Full reverse: stop timer, unsubscribe, deregister,
               close storage, exit

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9750, tasks_loaded: N, mode: leader|standby}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown event, or API call
  Validates:   Signal is recognized
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new register/cancel/pause/resume requests
  Validates:   No new tasks accepted after this point

Step 3 — Stop Tick Loop
  Action:      Cancel interval timer — no new dispatches
  Validates:   Timer cancelled, no new Phase 1 starts

Step 4 — Drain In-Flight
  Action:      Wait for executing tasks to complete (up to 30s)
  Validates:   in_flight count = 0
  On Timeout:  Record remaining executions as "timeout" in
               cron_executions. Tasks remain active — will retry
               on next startup.

Step 5 — Release Lock
  Action:      DELETE from cron_locks WHERE lock_key = "tick"
               AND holder = this_instance
  Validates:   Lock released or already expired

Step 6 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges removal

Step 7 — Close Storage
  Action:      Close database connection
  Validates:   Connection closed cleanly

Step 8 — Exit
  Log: lifecycle.stopped {uptime_seconds, in_flight_drained, tasks_timed_out}
  agent_state → retired
  Exit process
```

### Health

Reported via `POST /v1/health`:

```yaml
health:
  healthy:
    conditions:
      - tick_loop = running
      - storage = connected
      - in_flight < 80% of config.max_concurrent
    response:
      status: healthy
      details: {tick_loop, storage, active_tasks, in_flight,
                max_concurrent, last_tick, lock_held}

  degraded:
    conditions:
      - storage errors (but retrying)
      - in_flight >= 80% of config.max_concurrent
      - lock contention (standby mode)
    response:
      status: degraded
      details: {reason, last_error, retry_count}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
      - tick loop stopped unexpectedly
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "cron"`:

```
Step 1 — Validate New Blueprint
  Action:      Parse new blueprint, verify against schema
  Validates:   Blueprint parses, version is newer than current
  On Fail:     Log warning, continue with current version

Step 2 — Check Migration
  Action:      Compare Types block against current storage schema
  Validates:   Diff computed (per patterns/versioning)
  On Fail:     Log error, continue with current version

Step 3 — Execute Migration (if needed)
  Action:      Pause tick loop → run migration steps → resume
  Pre-check:   No in-flight tasks
  Validates:   All migration steps succeed, schema matches new Types
  On Fail:     ROLLBACK migration → resume tick loop with old version
  Backout:     Reverse migration steps in order, restore old schema

Step 4 — Reload Configuration
  Action:      Apply new config values
  Validates:   All config values within constraints
  On Fail:     Revert to previous config, log warning

Final:
  Log: lifecycle.version_updated {from, to, migration_steps}
  Emit: cron.blueprint.updated event
```

---

## Triggers

```yaml
triggers:
  - name: tick_timer
    type: schedule
    interval: config.tick_interval
    description: Evaluate all active schedules

  - name: agent_registered
    type: event
    topic: system.agent.registered
    description: Update local agent availability cache

  - name: agent_deregistered
    type: event
    topic: system.agent.deregistered
    description: Flag tasks targeting removed agents

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "cron"
    description: Self-update if cron blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [register, cancel, pause, resume, list, history, purge_completed]
    description: Agent-to-agent and operator actions
```

---

## Actions

### register

Register a new scheduled task.

**Purpose:** Schedule a recurring or one-time task for execution.

**Input:** Subset of `CronTask` fields:
`{name, schedule, fire_at?, target_agent?, target_url?, action?, payload?, max_retries?, timeout?}`

**Processing:**

```
1. Validate input against CronTask type constraints:
   a. name: non-empty, max 128 chars
   b. schedule: valid cron expression OR "once"
   c. ck_once_needs_fire_at: if "once", fire_at is required and in the future
   d. ck_single_target: exactly one of target_agent or target_url
   e. If target_agent: action is required
   f. If target_agent: verify agent exists in service directory
2. Check uq_task_natural_key constraint:
   a. If name + target_agent already exists → UPDATE existing task (idempotent)
   b. Otherwise → INSERT new task
3. Generate task_id (UUID v7) if new
4. Compute next_fire:
   a. Cron expression → next matching minute from now (UTC)
   b. "once" → fire_at value
5. Write CronTask to cron_tasks
6. Log: action.completed {action: "register", task_id}
7. Publish: cron.task.registered {task_id, name, schedule}
8. Return {task_id, next_fire}
```

**Output:** `{task_id: string, next_fire: int64}`

**Errors:**

```yaml
errors:
  - code: INVALID_SCHEDULE
    condition: Cron expression is malformed
    retryable: false
  - code: INVALID_INPUT
    condition: Missing required fields or constraint violation
    retryable: false
  - code: TARGET_NOT_FOUND
    condition: target_agent not in service directory
    retryable: false
  - code: STORAGE_ERROR
    condition: Failed to write task
    retryable: true
  - code: TASK_LIMIT_EXCEEDED
    condition: cron_tasks row count >= 100,000
    retryable: false
```

**Side Effects:** Writes to `cron_tasks`. Emits `cron.task.registered`.

**Idempotency:** Same `name` + `target_agent` updates existing task.

**Manual Override:** Yes — operators can register tasks via CLI or API.

---

### cancel

Cancel a scheduled task.

**Purpose:** Remove a task from the schedule permanently.

**Input:** `{task_id: string}` — references `CronTask.task_id`

**Processing:**

```
1. Look up task_id in cron_tasks (by PK)
2. If not found → NOT_FOUND
3. If in-flight execution exists:
   a. Wait for completion (up to CronTask.timeout)
   b. Record execution result in cron_executions
4. CronTask state transition: * → cancelled
5. Clear next_fire
6. Log: action.completed {action: "cancel", task_id}
7. Publish: cron.task.cancelled {task_id}
8. Return {cancelled: true, task_id}
```

**Output:** `{cancelled: bool, task_id: string}`

**Errors:** `NOT_FOUND` (permanent), `STORAGE_ERROR` (transient)

**Side Effects:** Updates `cron_tasks` status. Cascading: related `cron_executions` retained (cancel does not delete history). Emits `cron.task.cancelled`.

**Idempotency:** Cancelling already-cancelled task returns success.

---

### pause

Pause a scheduled task without deleting it.

**Purpose:** Temporarily stop a task from firing.

**Input:** `{task_id: string}` — references `CronTask.task_id`

**Processing:**

```
1. Look up task_id in cron_tasks (by PK)
2. If not found → NOT_FOUND
3. Validate state transition: active → paused (reject others as INVALID_STATE)
4. Update status → "paused", clear next_fire
5. Log: action.completed {action: "pause", task_id}
6. Publish: cron.task.paused {task_id}
7. Return {task_id, status: "paused"}
```

**Output:** `{task_id: string, status: "paused"}`

**Errors:** `NOT_FOUND` (permanent), `INVALID_STATE` (permanent)

**Side Effects:** Updates `cron_tasks`. Emits `cron.task.paused`.

**Idempotency:** Pausing already-paused task returns INVALID_STATE.

---

### resume

Resume a paused task.

**Purpose:** Restart a paused task's schedule.

**Input:** `{task_id: string}` — references `CronTask.task_id`

**Processing:**

```
1. Look up task_id in cron_tasks (by PK)
2. If not found → NOT_FOUND
3. Validate state transition: paused → active (reject others as INVALID_STATE)
4. Recompute next_fire from schedule
5. Update status → "active", set next_fire
6. Log: action.completed {action: "resume", task_id}
7. Publish: cron.task.resumed {task_id}
8. Return {task_id, status: "active", next_fire}
```

**Output:** `{task_id: string, status: "active", next_fire: int64}`

**Errors:** `NOT_FOUND` (permanent), `INVALID_STATE` (permanent)

**Side Effects:** Updates `cron_tasks`. Emits `cron.task.resumed`.

**Idempotency:** Resuming already-active task returns INVALID_STATE.

---

### list

List tasks matching a filter.

**Purpose:** Query registered tasks.

**Input:** `{status?: string, limit?: int, offset?: int}`

- `status`: `active`, `paused`, `completed`, `failed`, `cancelled`, `all` (default: `all`)
- `limit`: default 100, max 1000
- `offset`: default 0

**Processing:**

```
1. Validate status is one of allowed enum values
2. Query cron_tasks with filter, ORDER BY created_at DESC
3. Apply limit and offset
4. Return task list with total count
```

**Output:** `{tasks: CronTask[], total: int}`

**Errors:** `INVALID_INPUT` if invalid status value.

**Side Effects:** None (read-only).

---

### history

Get execution history for a task.

**Purpose:** Query past executions using the `task_executions` relationship.

**Input:** `{task_id: string, limit?: int}` — limit default 20, max 100

**Processing:**

```
1. Verify task_id exists in cron_tasks (FK validation)
2. Query cron_executions WHERE task_id = ? ORDER BY fired_at DESC
   (uses idx_task_history index, follows task_executions relationship)
3. Apply limit
4. Return execution list
```

**Output:** `{executions: CronExecution[], task_id: string}`

**Errors:** `NOT_FOUND` if task_id does not exist.

**Side Effects:** None (read-only).

---

### purge_completed

Remove completed and failed tasks older than a threshold.

**Purpose:** Manual cleanup of finished tasks and their related executions.

**Input:** `{older_than: int64, include_failed?: bool}`

- `older_than`: Unix timestamp — purge tasks with updated_at before this
- `include_failed`: also purge failed tasks (default: false)

**Processing:**

```
1. Validate older_than is not in the future
2. Query cron_tasks WHERE status IN ("completed", optionally "failed")
   AND updated_at < older_than
3. For each matching task:
   a. Delete related cron_executions (cascaded via task_executions relationship)
   b. Delete the cron_task row
4. Log: action.completed {action: "purge_completed", purged_count}
5. Return {purged: count}
```

**Output:** `{purged: int}`

**Errors:** `INVALID_INPUT` if older_than is in the future.

**Side Effects:** Deletes from `cron_tasks` and `cron_executions` (cascade).

**Idempotency:** Purging already-purged data is a no-op.

**Manual Override:** Operator-only action (requires operator role).

---

## Execute Workflow

The core tick loop runs every `config.tick_interval` seconds:

```
Phase 1 — Acquire Lock
  Query:     INSERT into cron_locks WHERE lock_key = "tick"
             (with expires_at = now + config.lock_ttl)
  If held:   Log cron.tick.skipped {lock_holder} → exit tick
  If acquired: proceed

Phase 2 — Evaluate Schedules
  Query:     SELECT * FROM cron_tasks
             WHERE status = 'active' AND next_fire <= now
             (uses idx_active_schedule)
  For each task:
    If cron expression → verify current minute (UTC) matches
    If "once" → verify fire_at <= now
  Result:    List of due tasks

Phase 3 — Dispatch (up to config.max_concurrent)
  For each due task:
    INSERT CronExecution with status = "pending" into cron_executions
    (sets task_id FK → validates task_executions relationship)
    If target_agent:
      Publish: cron.task.fired {task_id, target_agent, action, payload}
      Direct: POST /v1/message to target_agent
    If target_url:
      POST to URL with payload, timeout = CronTask.timeout
    Log: cron.task.fired {task_id, target}

Phase 4 — Collect Results
  Wait for responses (timeout per CronTask.timeout)
  For each response:
    UPDATE cron_executions SET status, duration_ms,
           response (truncated to 1 KB), completed_at
    If success:
      Log: cron.task.completed {task_id, duration_ms}
    If failed or timeout:
      Log: cron.task.failed {task_id, error, attempt}
      Publish: cron.task.execution_failed {task_id, error, attempt}

Phase 5 — Handle Failures
  For each failed task:
    If retry_count < CronTask.max_retries:
      Increment retry_count on cron_tasks
      Compute retry delay (per patterns/retry backoff strategy)
      Set next_fire = now + retry_delay
      Log: cron.task.retry {task_id, attempt, next_retry}
    If retry_count >= CronTask.max_retries:
      CronTask state transition: active → failed
      Publish: cron.task.failed {task_id, final: true, total_attempts}
      Log: cron.task.exhausted {task_id, total_attempts}

Phase 6 — Advance Schedules
  One-time tasks that succeeded:
    CronTask state transition: active → completed
  Recurring tasks:
    Compute next_fire from cron expression
    Reset retry_count to 0
    UPDATE cron_tasks

Phase 7 — Cleanup
  DELETE FROM cron_executions
    WHERE fired_at < (now - config.history_retention)
    (respects retention policy)
  DELETE FROM cron_locks WHERE expires_at < now
  Release tick lock

Phase 8 — Report
  Emit metrics:
    wl_cron_tasks_total (by status)
    wl_cron_executions_total (by status)
    wl_cron_tick_duration_seconds
```

---

## Cron Expression Format

Standard 5-field cron expressions (all times UTC):

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

For one-time tasks, set `schedule: "once"` with a `fire_at` timestamp.

---

## Collaboration

```yaml
events_published:
  - topic: cron.task.registered
    payload: {task_id, name, schedule, target_agent}
    when: New task registered

  - topic: cron.task.cancelled
    payload: {task_id}
    when: Task cancelled

  - topic: cron.task.paused
    payload: {task_id}
    when: Task paused

  - topic: cron.task.resumed
    payload: {task_id}
    when: Task resumed

  - topic: cron.task.fired
    payload: {task_id, target_agent, action, payload}
    when: Task dispatched to target

  - topic: cron.task.completed
    payload: {task_id, execution_id, duration_ms}
    when: Task execution succeeded

  - topic: cron.task.execution_failed
    payload: {task_id, error, attempt}
    when: Single execution attempt failed

  - topic: cron.task.failed
    payload: {task_id, final: true, total_attempts}
    when: All retries exhausted

events_subscribed:
  - topic: system.agent.registered
    payload: {agent_name, manifest}
    action: Update local agent availability cache

  - topic: system.agent.deregistered
    payload: {agent_name}
    action: Flag tasks targeting this agent

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "cron"
    action: Self-update procedure

direct_messages:
  - target: variable (CronTask.target_agent)
    action: CronTask.action
    when: Task dispatch (Phase 3)
    reason: Requires synchronous response to track success/failure
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All task management is autonomous
  supervised:    Task registration open; purge/backup/restore require operator
  manual-only:   All actions require operator invocation

overridable_behaviors:
  - behavior: automatic_task_retry
    default: enabled
    override: Set max_retries=0 per task
    audit: logged

  - behavior: history_cleanup
    default: enabled
    override: Set config.history_retention = 0
    audit: logged

  - behavior: tick_evaluation
    default: enabled
    override: pause_all manual action
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: pause_all
    description: Suspend tick loop — no tasks fire
    allowed: operator

  - action: resume_all
    description: Resume tick loop
    allowed: operator

  - action: force_tick
    description: Trigger immediate schedule evaluation
    allowed: operator

  - action: purge_completed
    description: Remove completed/failed tasks older than threshold
    allowed: operator

  - action: backup
    description: Export tasks to backup file
    allowed: operator

  - action: restore
    description: Import tasks from backup file
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
    - MUST NOT modify data owned by other agents
    - MUST NOT send messages to agents not listed as target_agent
      in a registered task
    - Task dispatch rate bounded by config.max_concurrent × config.tick_interval

  forbidden_actions:
    - MUST NOT execute arbitrary code — only dispatches to declared targets
    - MUST NOT modify task payloads after registration
    - MUST NOT bypass distributed lock in multi-instance deployments
    - MUST NOT fire tasks targeting deregistered agents (flag and skip)

  resource_limits:
    memory: 256 MB (process limit)
    cron_tasks_rows: 100000 (reject register if exceeded)
    cron_executions: governed by config.history_retention TTL
    outbound_per_tick: config.max_concurrent
```

---

## Error Handling

Retry and circuit breaker behavior inherited from `patterns/retry`.
This section defines cron-specific error types only.

```yaml
errors:
  permanent:
    - code: INVALID_SCHEDULE
      description: Cron expression is malformed
    - code: INVALID_INPUT
      description: Missing required fields or constraint violation
    - code: TARGET_NOT_FOUND
      description: target_agent not in service directory
    - code: DUPLICATE_NAME
      description: Task name + target_agent combination exists
    - code: NOT_FOUND
      description: Referenced task_id does not exist in cron_tasks
    - code: INVALID_STATE
      description: Action not valid for current CronTask state
    - code: TASK_LIMIT_EXCEEDED
      description: cron_tasks row count >= constraints.cron_tasks_rows

  transient:
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Enter degraded state, skip tick, retry next interval
    - code: DISPATCH_TIMEOUT
      description: Target agent did not respond within CronTask.timeout
      fallback: Record failed CronExecution, schedule retry
    - code: DISPATCH_ERROR
      description: Target agent returned error response
      fallback: Record failed CronExecution, schedule retry
    - code: LOCK_CONTENTION
      description: Could not acquire tick lock
      fallback: Skip tick (another instance handles it)
```

---

## Observability

Standard log envelope and types inherited from `patterns/logging`.

```yaml
custom_log_types:
  - log_type: cron.task.fired
    level: info
    when: Task dispatched
    fields: {task_id, target_agent, action}

  - log_type: cron.task.completed
    level: info
    when: Execution succeeded
    fields: {task_id, duration_ms}

  - log_type: cron.task.failed
    level: warn
    when: Execution attempt failed
    fields: {task_id, error, attempt}

  - log_type: cron.task.exhausted
    level: error
    when: All retries exhausted
    fields: {task_id, total_attempts}

  - log_type: cron.task.retry
    level: warn
    when: Retry scheduled
    fields: {task_id, attempt, next_retry}

  - log_type: cron.tick.skipped
    level: debug
    when: Tick skipped due to lock
    fields: {lock_holder}

  - log_type: cron.tick.completed
    level: debug
    when: Tick cycle finished
    fields: {tasks_evaluated, tasks_fired, duration_ms}

metrics:
  - name: wl_cron_tasks_total
    type: gauge
    labels: [status]
    description: Tasks by status

  - name: wl_cron_executions_total
    type: counter
    labels: [status]
    description: Executions by outcome

  - name: wl_cron_tick_duration_seconds
    type: histogram
    description: Tick cycle duration

  - name: wl_cron_dispatch_duration_seconds
    type: histogram
    labels: [target_agent]
    description: Per-dispatch duration

  - name: wl_cron_retries_total
    type: counter
    description: Total retry attempts

  - name: wl_cron_in_flight
    type: gauge
    description: Currently executing tasks

alerts:
  - condition: Task retries exhausted
    severity: high
    routing: alerting agent

  - condition: Storage errors for 3+ consecutive ticks
    severity: critical
    routing: alerting agent

  - condition: in_flight > 80% of config.max_concurrent
    severity: warn
    routing: alerting agent

  - condition: Tick loop stopped unexpectedly
    severity: critical
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send messages to any registered agent

    - capability: database:read
      resources: [cron_tasks, cron_executions, cron_locks]
      description: Read own tables

    - capability: database:write
      resources: [cron_tasks, cron_executions, cron_locks]
      description: Write own tables

  data_sensitivity:
    - data: Task payloads
      classification: variable
      handling: Encrypted at rest, logged as size only

    - data: Execution responses
      classification: variable
      handling: Truncated to 1 KB, encrypted at rest

    - data: Task schedules
      classification: low
      handling: Logged freely

    - data: Agent names
      classification: low
      handling: Logged freely

  access_control:
    - caller: Any registered agent
      actions: [register, cancel, pause, resume, list, history]

    - caller: Operator (auth token with operator role)
      actions: [register, cancel, pause, resume, list, history,
                purge_completed, backup, restore, pause_all,
                resume_all, force_tick]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Register recurring task
    action: register
    input:
      name: daily-report
      schedule: "0 9 * * *"
      target_agent: email-send
      action: send_report
      payload: {report_type: daily}
    expected:
      task_id: "<uuid-v7>"
      next_fire: "<next 9am UTC>"
    validates:
      - CronTask inserted into cron_tasks
      - uq_task_natural_key not violated
      - cron.task.registered event published

  - name: Register one-time task
    action: register
    input:
      name: one-shot
      schedule: once
      fire_at: 1745582400
      target_agent: email-send
      action: send_notification
      payload: {}
    expected:
      task_id: "<uuid-v7>"
      next_fire: 1745582400
    validates:
      - ck_once_needs_fire_at constraint passes
      - CronTask.status = active

  - name: List active tasks
    action: list
    input: {status: active}
    expected: {tasks: [...], total: N}
```

### Error Cases

```yaml
  - name: Invalid cron expression
    action: register
    input: {name: bad, schedule: not-a-cron, target_agent: email-send, action: test}
    expected_error: INVALID_SCHEDULE

  - name: Missing target
    action: register
    input: {name: no-target, schedule: "* * * * *"}
    expected_error: INVALID_INPUT
    validates: ck_single_target constraint caught

  - name: Cancel non-existent task
    action: cancel
    input: {task_id: non-existent}
    expected_error: NOT_FOUND

  - name: Pause a completed task
    action: pause
    input: {task_id: "<completed-task-id>"}
    expected_error: INVALID_STATE
    validates: State machine rejects completed → paused
```

### Edge Cases

```yaml
  - name: Idempotent re-register
    action: register
    input: {name: daily-report, target_agent: email-send, schedule: "0 10 * * *", action: send_report}
    expected: Existing task updated (uq_task_natural_key match)
    validates: No duplicate row created

  - name: Cancel with in-flight execution
    action: cancel
    input: {task_id: "<in-flight-task-id>"}
    expected: Waits for completion, then cancels
    validates: CronExecution recorded before cancel, relationship integrity preserved

  - name: Tick during storage outage
    trigger: tick_timer
    condition: Storage unreachable
    expected: Agent enters degraded state, retries next tick
    validates: No data loss, agent_state = degraded

  - name: Burst exceeds max_concurrent
    trigger: tick_timer
    condition: 100 tasks due, config.max_concurrent = 10
    expected: 10 dispatched, 90 remain for next tick
    validates: Dispatch queue respects constraint

  - name: One-time task in the past
    action: register
    input: {name: late, schedule: once, fire_at: 1000000000, target_agent: test, action: ping}
    expected: Fires immediately on next tick

  - name: Resume after target deregistered
    action: resume
    input: {task_id: "<task-targeting-removed-agent>"}
    expected: Task resumes, next dispatch will fail and retry
    validates: Task not auto-cancelled, target flagged
```

---

## Implementation Notes

- **Clock precision**: Tick evaluates once per `config.tick_interval`.
  Tasks fire within the tick window, not at the exact second. For
  sub-minute precision, reduce `tick_interval` (min: 1s).
- **Concurrency control**: `config.max_concurrent` prevents overloading
  target agents. Excess tasks queue for the next tick cycle.
- **Persistence**: Task definitions and execution history MUST be
  persisted to durable storage. In-memory only is not acceptable —
  server restarts MUST NOT lose schedules.
- **Timezone**: All cron expressions evaluated in UTC.
- **Distributed locking**: Multi-instance deployments — only one instance
  evaluates per tick. Uses `cron_locks` table with TTL-based expiry.
  If holder crashes, lock expires after `config.lock_ttl` and another
  instance takes over.
- **Idempotency**: `uq_task_natural_key` (name + target_agent) prevents
  duplicates. Re-registering updates the existing task.
- **Target validation**: The cron agent caches the service directory.
  On `system.agent.deregistered`, tasks targeting that agent are flagged
  but not cancelled — the agent may return.
- **Relationship integrity**: All `cron_executions` rows reference a valid
  `cron_tasks` row via the `task_executions` relationship. The `cascade`
  delete rule ensures no orphaned execution records exist after task
  deletion (via `purge_completed` or manual cleanup).

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: unbounded

  inter_agent:
    protocol: message-bus-only
    direct_http: forbidden
    routing: by agent name, never by instance address
    reason: >
      The message bus resolves agent names to healthy instances.
      During blue-green deploys, the bus handles traffic shifting
      between versions transparently. Direct HTTP would bypass
      this and break version cutover.

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: cron_locks table with TTL
      leader: [tick_evaluation, schedule_advancement, cleanup]
      follower: [health_reporting, action_handling, standby]
      promotion: automatic when leader lock expires
    state_sharing:
      mechanism: shared sqlite database
      consistency_window: config.tick_interval
      conflict_resolution: >
        Storage constraints (uq_task_natural_key, ck_single_target)
        prevent invalid concurrent writes. Leader election prevents
        duplicate tick processing.

  event_handling:
    consumer_group: cron
    delivery: one-per-group
    description: >
      Bus delivers each event to ONE instance in the "cron"
      consumer group. All instances subscribe, but only one
      processes each event. Prevents duplicate handling.
    direct_messages:
      routing: any healthy instance
      deduplication: via storage constraints (idempotent actions)

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 10
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same database. Schema migrations
      are additive-only during shadow phase. Destructive steps
      (column removal, constraint tightening) execute only after
      cutover confirmation.
    consumer_groups:
      shadow_phase: "cron@vN+1" (separate group, receives copies)
      after_cutover: "cron" (takes over primary group)
```

---

## Verification Checklist

- [ ] Tasks registered with cron expressions — CronTask created, constraints validated
- [ ] Tasks registered as one-time — ck_once_needs_fire_at enforced
- [ ] Cron expression validation — malformed → INVALID_SCHEDULE
- [ ] ck_single_target — exactly one of target_agent or target_url
- [ ] uq_task_natural_key — duplicate name+target updates instead of inserting
- [ ] target_agent validated against service directory
- [ ] One-time tasks fire at specified timestamp
- [ ] Recurring tasks compute correct next_fire
- [ ] Dispatch via POST /v1/message to target_agent
- [ ] config.max_concurrent enforced per tick
- [ ] Excess tasks queued for next tick
- [ ] Failed tasks retried with patterns/retry backoff
- [ ] CronTask.max_retries enforced — state transition active → failed
- [ ] cron.task.failed event published when retries exhausted
- [ ] CronExecution records created with valid task_executions FK
- [ ] History purged per config.history_retention
- [ ] task_executions cascade — deleting task deletes all executions
- [ ] No orphaned cron_executions after purge_completed
- [ ] Pause/resume state transitions validated by state machine
- [ ] Cancel works with in-flight execution (drain then cancel)
- [ ] Distributed lock prevents duplicate tick evaluation
- [ ] Lock expires after config.lock_ttl if holder crashes
- [ ] Graceful shutdown drains in-flight per shutdown sequence
- [ ] Health endpoint reports accurate status per health criteria
- [ ] Self-update triggers on system.blueprint.changed
- [ ] All events published to bus with correct topic names
- [ ] Backup/restore preserves relationship integrity
- [ ] Override audit records who, what, when, why
- [ ] Startup sequence validation gates — each step has pre-check/validates/on-fail
- [ ] Startup backout — failed step reverses prior steps correctly
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] on_change rules defined for all dependencies (compatible/breaking/removed)
- [ ] system.change.assessment triggers self-governance reconciliation
- [ ] Blue-green: shadow phase validates events without side effects
- [ ] Blue-green: cutover shifts traffic via message bus, not direct HTTP
- [ ] Blue-green: rollback restores previous version within watch period
- [ ] Scaling: inter-agent communication via message bus only
- [ ] Scaling: leader election via cron_locks prevents duplicate ticks
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Scaling: vN and vN+1 share database during blue-green
