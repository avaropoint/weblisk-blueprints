<!-- blueprint
type: pattern
name: scheduling
version: 1.0.0
requires: [protocol/types, patterns/messaging, patterns/state-machine, patterns/storage]
platform: any
tier: free
-->

# Scheduling Pattern

Declarative schedule registration and execution contract for
time-based work across all Weblisk agents and domains. This pattern
defines the platform-wide specification for cron expressions, schedule
lifecycle, overlap control, missed-tick handling, and distributed
locking. The cron agent is the executor — this pattern is the
contract that all schedule producers and consumers share.

## Overview

Any agent or domain can register scheduled work. The scheduling
pattern provides the declarative contract that governs how schedules
are defined, evaluated, and executed:

- **Cron expression format** — 5-field standard with extensions
- **Schedule registration** — the API shape for declaring scheduled work
- **One-time vs recurring** — semantics for both modes
- **Timezone handling** — explicit timezone on every schedule
- **Overlap control** — what happens when a tick fires while the
  previous execution is still running
- **Missed-tick policy** — what happens when the executor misses
  one or more scheduled ticks
- **Distributed locking** — single-executor guarantee across replicas
- **Schedule lifecycle** — active, paused, expired, disabled states

Agents that produce or consume scheduled work
`extends: patterns/scheduling` and declare their schedules,
policies, and target actions.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: EventEnvelope
          fields_used: [event_id, topic, source, scope, timestamp, payload]
        - name: ErrorResponse
          fields_used: [code, message, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/messaging
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
  - blueprint: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: state-transitions
          parameters: [initial, transitions, side_effects]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TypeDefinition
          fields_used: [name, fields, description]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Declarative Schedules** — Schedules are data, not code. Agents register YAML declarations with expressions, targets, and policies. The executor interprets them uniformly.
2. **Single Executor** — One schedule fires once per tick, even in multi-replica deployments. Distributed locking guarantees exactly-one execution per scheduled instant.
3. **Missed-Tick Awareness** — Every schedule declares what happens when ticks are missed (fire-once, fire-all, skip). The executor never silently drops or duplicates work.
4. **Timezone-Explicit** — All schedules declare a timezone. No implicit UTC assumptions. The executor evaluates cron expressions in the declared timezone, including DST transitions.
5. **Overlap Control** — Every recurring schedule declares its concurrency policy. The executor enforces skip-if-running, queue, or allow-parallel before dispatching.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: schedule-registration
      description: Register a declarative schedule definition with the executor
      parameters:
        - name: definition
          type: ScheduleDefinition
          required: true
          description: Complete schedule declaration including expression, target, and policies
        - name: idempotency_key
          type: string
          required: false
          description: Optional key for idempotent registration (default is name + target)
      inherits: Schedule validation, lifecycle management, and execution tracking
      overridable: true
      override_constraints: Must preserve all required ScheduleDefinition fields; may add custom payload fields

    - name: schedule-evaluation
      description: Evaluate all active schedules against the current tick and dispatch due work
      parameters:
        - name: tick_time
          type: int64
          required: true
          description: Current evaluation timestamp (epoch seconds)
        - name: max_concurrent
          type: int
          required: false
          default: 10
          description: Maximum concurrent dispatches per tick
      inherits: Cron expression parsing, overlap enforcement, and missed-tick handling
      overridable: false
      override_constraints: Evaluation logic is not overridable — policies are declarative

    - name: distributed-locking
      description: Acquire and release distributed locks for single-executor guarantee
      parameters:
        - name: lock_key
          type: string
          required: true
          description: Lock identifier scoped to the schedule or tick
        - name: ttl
          type: int
          required: true
          description: Lock time-to-live in seconds
        - name: holder
          type: string
          required: true
          description: Instance identifier of the lock holder
      inherits: Lock acquisition, renewal, expiration, and contention handling
      overridable: false
      override_constraints: Locking semantics are not overridable — single-executor is a guarantee

  types:
    - name: ScheduleDefinition
      description: Complete schedule registration envelope with expression, target, and policies
      inherited_by: Types section
    - name: CronExpression
      description: 5-field cron expression specification with extensions
      inherited_by: Types section
    - name: ScheduleStatus
      description: Enum of schedule lifecycle states
      inherited_by: Types section
    - name: OverlapPolicy
      description: Enum of concurrency policies for recurring schedules
      inherited_by: Types section
    - name: MissedTickPolicy
      description: Enum of missed-tick handling strategies
      inherited_by: Types section
    - name: ScheduleExecution
      description: Record of a single tick execution attempt
      inherited_by: Types section
    - name: ScheduleLock
      description: Distributed lock record for single-executor guarantee
      inherited_by: Types section

  events:
    - topic: schedule.registered
      description: New schedule created or updated via idempotent registration
      payload: {schedule_id, name, expression, target, timezone, timestamp}
    - topic: schedule.fired
      description: Scheduled tick executed — work dispatched to target
      payload: {schedule_id, execution_id, target, fired_at, trace_id}
    - topic: schedule.skipped
      description: Tick skipped due to overlap policy or missed-tick policy
      payload: {schedule_id, reason, policy, skipped_at}
    - topic: schedule.paused
      description: Schedule paused — no further ticks until resumed
      payload: {schedule_id, paused_by, timestamp}
    - topic: schedule.resumed
      description: Schedule resumed — next tick recomputed
      payload: {schedule_id, resumed_by, next_fire, timestamp}
    - topic: schedule.expired
      description: Schedule reached its declared end date and became inactive
      payload: {schedule_id, expires_at, total_executions, timestamp}
    - topic: schedule.failed
      description: Execution target failed after all retry attempts exhausted
      payload: {schedule_id, execution_id, error, total_attempts, timestamp}
```

---

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

### Special Characters

| Character | Meaning | Example |
|-----------|---------|---------|
| `*` | Any value | `* * * * *` — every minute |
| `,` | List | `1,15 * * * *` — minute 1 and 15 |
| `-` | Range | `0 9-17 * * *` — every hour 9 AM–5 PM |
| `/` | Step | `*/5 * * * *` — every 5 minutes |

### Extensions

| Alias | Equivalent | Description |
|-------|------------|-------------|
| `@yearly` | `0 0 1 1 *` | Once a year (midnight Jan 1) |
| `@monthly` | `0 0 1 * *` | Once a month (midnight 1st) |
| `@weekly` | `0 0 * * 0` | Once a week (midnight Sunday) |
| `@daily` | `0 0 * * *` | Once a day (midnight) |
| `@hourly` | `0 * * * *` | Once an hour (top of hour) |

### One-Time Schedules

For one-time execution, set `expression: "once"` with a `fire_at`
timestamp. One-time schedules transition to `expired` after execution.

### Timezone Evaluation

Cron expressions are evaluated in the schedule's declared `timezone`.
During DST transitions:

- **Spring forward** (e.g. 2:00 AM skipped): Schedules targeting
  the skipped hour fire at the next valid minute after the transition.
- **Fall back** (e.g. 2:00 AM repeated): Schedules fire once during
  the first occurrence of the ambiguous hour. They do NOT fire twice.

---

## Types

```yaml
types:
  ScheduleDefinition:
    description: Complete schedule registration envelope
    fields:
      schedule_id:
        type: string
        format: uuid-v7
        description: Unique schedule identifier (generated on registration)
      name:
        type: string
        max: 128
        description: Human-readable schedule name
      expression:
        type: string
        description: Cron expression, alias (@daily, etc.), or "once"
      fire_at:
        type: int64
        required_when: expression = "once"
        description: One-time fire timestamp (epoch seconds)
      timezone:
        type: string
        default: "UTC"
        description: IANA timezone identifier (e.g. "America/New_York")
      target_agent:
        type: string
        exclusive_with: target_url
        description: Agent name to dispatch to via messaging bus
      target_url:
        type: string
        exclusive_with: target_agent
        description: URL to POST to on each tick
      action:
        type: string
        required_when: target_agent
        description: Message action name for target agent
      payload:
        type: object
        optional: true
        description: Data to send with each execution
      overlap_policy:
        type: string
        enum: [skip-if-running, queue, allow-parallel]
        default: skip-if-running
        description: What to do when a tick fires while previous execution is running
      missed_tick_policy:
        type: string
        enum: [fire-once, fire-all, skip]
        default: fire-once
        description: What to do when ticks are missed
      max_retries:
        type: int
        default: 3
        min: 0
        max: 100
        description: Retry attempts per execution
      timeout:
        type: int
        default: 30
        min: 1
        max: 300
        unit: seconds
        description: Per-execution timeout
      status:
        type: string
        enum: [active, paused, expired, disabled]
        default: active
        description: Current schedule lifecycle state
      expires_at:
        type: int64
        optional: true
        description: Schedule end date (epoch seconds). Null means no expiry.
      next_fire:
        type: int64
        optional: true
        description: Next scheduled execution timestamp
      created_at:
        type: int64
        auto: true
        description: Schedule creation timestamp
      updated_at:
        type: int64
        auto: true
        description: Last modification timestamp
      created_by:
        type: string
        optional: true
        description: Identity of registering agent or operator
    constraints:
      - name: ck_single_target
        type: check
        expression: (target_agent IS NOT NULL) XOR (target_url IS NOT NULL)
        description: Exactly one target type required
      - name: ck_once_needs_fire_at
        type: check
        expression: expression != 'once' OR fire_at IS NOT NULL
        description: One-time schedules require fire_at
      - name: ck_timezone_valid
        type: check
        expression: timezone IN (IANA_TZ_DATABASE)
        description: Timezone must be a valid IANA identifier
      - name: uq_schedule_natural_key
        type: unique
        fields: [name, target_agent]
        description: Natural key for idempotent registration

  CronExpression:
    description: Parsed 5-field cron expression
    fields:
      minute:
        type: string
        description: "Minute field (0-59, *, */N, ranges, lists)"
      hour:
        type: string
        description: "Hour field (0-23, *, */N, ranges, lists)"
      day_of_month:
        type: string
        description: "Day of month field (1-31, *, */N, ranges, lists)"
      month:
        type: string
        description: "Month field (1-12, *, */N, ranges, lists)"
      day_of_week:
        type: string
        description: "Day of week field (0-6 where 0=Sunday, *, */N, ranges, lists)"
      raw:
        type: string
        description: Original expression string before parsing

  ScheduleStatus:
    description: Schedule lifecycle states
    enum:
      - value: active
        description: Schedule is evaluated on every tick
      - value: paused
        description: Schedule is temporarily suspended — no ticks fire
      - value: expired
        description: Schedule reached its expires_at date or one-time completed
      - value: disabled
        description: Schedule is permanently deactivated by operator action

  OverlapPolicy:
    description: Concurrency policy for recurring schedules
    enum:
      - value: skip-if-running
        description: Skip this tick if the previous execution has not completed
      - value: queue
        description: Queue this tick for execution after the current one completes
      - value: allow-parallel
        description: Dispatch immediately regardless of in-flight executions

  MissedTickPolicy:
    description: Handling strategy for ticks missed during executor downtime
    enum:
      - value: fire-once
        description: Fire a single catch-up execution regardless of how many ticks were missed
      - value: fire-all
        description: Fire one execution per missed tick in sequence
      - value: skip
        description: Discard all missed ticks and resume from the next future tick

  ScheduleExecution:
    description: Record of a single tick execution attempt
    fields:
      execution_id:
        type: string
        format: uuid-v7
        description: Unique execution identifier
      schedule_id:
        type: string
        format: uuid-v7
        references: ScheduleDefinition.schedule_id
        description: Parent schedule
      fired_at:
        type: int64
        description: When execution was dispatched
      completed_at:
        type: int64
        optional: true
        description: When execution finished (null if pending)
      status:
        type: string
        enum: [pending, success, failed, timeout, skipped]
        description: Execution outcome
      duration_ms:
        type: int
        optional: true
        description: Execution duration in milliseconds
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
      overlap_action:
        type: string
        optional: true
        description: "Action taken by overlap policy: skipped, queued, or parallel"
      trace_id:
        type: string
        description: Trace context for correlation

  ScheduleLock:
    description: Distributed lock for single-executor guarantee
    fields:
      lock_key:
        type: string
        description: Lock identifier (e.g. "tick" or schedule-scoped key)
      holder:
        type: string
        description: Instance ID holding the lock
      acquired_at:
        type: int64
        description: Lock acquisition timestamp
      expires_at:
        type: int64
        description: Lock expiration timestamp (TTL-based)
    constraints:
      - name: ck_lock_ttl
        type: check
        expression: expires_at > acquired_at
        description: Expiration must be after acquisition
```

---

## Schedule Lifecycle

```yaml
state_machine:
  entity.ScheduleDefinition:
    initial: active
    transitions:
      - from: active
        to: paused
        trigger: pause action
        validates: schedule exists and status = active
        side_effect: clear next_fire, emit schedule.paused
      - from: paused
        to: active
        trigger: resume action
        validates: next_fire recomputed from expression in declared timezone
        side_effect: set next_fire, emit schedule.resumed
      - from: active
        to: expired
        trigger: expires_at reached OR one-time execution completed
        validates: current time >= expires_at OR (expression = "once" AND execution succeeded)
        side_effect: clear next_fire, emit schedule.expired
      - from: active
        to: disabled
        trigger: disable action (operator)
        validates: operator identity confirmed
        side_effect: clear next_fire, emit schedule.disabled
      - from: paused
        to: disabled
        trigger: disable action (operator)
        validates: operator identity confirmed
        side_effect: emit schedule.disabled
      - from: disabled
        to: active
        trigger: enable action (operator)
        validates: next_fire recomputed, expires_at not in the past
        side_effect: set next_fire, emit schedule.resumed
```

---

## Evaluation Flow

The executor evaluates schedules on each tick:

```
Phase 1 — Acquire Tick Lock
  Action:     INSERT ScheduleLock with lock_key = "tick",
              holder = instance_id, expires_at = now + lock_ttl
  If held:    Log schedule.tick.skipped {lock_holder} → exit tick
  If acquired: proceed

Phase 2 — Evaluate Due Schedules
  Query:      SELECT * FROM schedules
              WHERE status = 'active' AND next_fire <= now
  For each schedule:
    Parse expression in schedule's declared timezone
    Verify current instant matches (or is overdue for missed-tick)

Phase 3 — Apply Overlap Policy
  For each due schedule:
    If overlap_policy = skip-if-running:
      Check for pending ScheduleExecution → skip if found
      Emit schedule.skipped {reason: "overlap", policy: "skip-if-running"}
    If overlap_policy = queue:
      Check for pending → queue behind current execution
    If overlap_policy = allow-parallel:
      Dispatch immediately

Phase 4 — Apply Missed-Tick Policy
  For each due schedule where next_fire < now - tick_interval:
    If missed_tick_policy = fire-once:
      Dispatch single execution for the latest missed tick
    If missed_tick_policy = fire-all:
      Dispatch one execution per missed tick in chronological order
    If missed_tick_policy = skip:
      Discard missed ticks, emit schedule.skipped {reason: "missed", policy: "skip"}

Phase 5 — Dispatch
  For each approved execution (up to max_concurrent):
    INSERT ScheduleExecution with status = "pending"
    If target_agent:
      Publish via messaging bus to target agent
    If target_url:
      POST to URL with payload and timeout
    Emit schedule.fired {schedule_id, execution_id}

Phase 6 — Collect Results
  Wait for responses (per schedule timeout)
  For each response:
    UPDATE ScheduleExecution with status, duration_ms, completed_at
    If failed and attempt < max_retries:
      Schedule retry with backoff
    If failed and attempt >= max_retries:
      Emit schedule.failed {schedule_id, execution_id, total_attempts}

Phase 7 — Advance Schedules
  One-time schedules that succeeded:
    Transition: active → expired
  Recurring schedules:
    Compute next_fire from expression in declared timezone
    UPDATE schedule with new next_fire

Phase 8 — Release Lock
  DELETE ScheduleLock WHERE lock_key = "tick" AND holder = instance_id
```

---

## Configuration

```yaml
config:
  tick_interval:
    type: int
    default: 60
    min: 1
    max: 3600
    unit: seconds
    description: Schedule evaluation frequency

  lock_ttl:
    type: int
    default: 120
    min: 10
    unit: seconds
    description: Distributed tick lock TTL — must be > tick_interval

  max_concurrent:
    type: int
    default: 10
    min: 1
    max: 100
    description: Maximum dispatches per tick

  default_timezone:
    type: string
    default: "UTC"
    description: Fallback timezone if a schedule omits timezone (validation warning issued)

  max_queue_depth:
    type: int
    default: 100
    min: 1
    max: 10000
    description: Maximum queued executions per schedule (for queue overlap policy)

  missed_tick_lookback:
    type: int
    default: 3600
    min: 60
    max: 86400
    unit: seconds
    description: Maximum lookback window for missed-tick evaluation
```

---

## Error Handling

| Error Code | Condition | Retryable | Action |
|------------|-----------|-----------|--------|
| `INVALID_EXPRESSION` | Cron expression fails parsing | No | Reject registration |
| `INVALID_TIMEZONE` | Timezone not in IANA database | No | Reject registration |
| `INVALID_TARGET` | Neither target_agent nor target_url provided | No | Reject registration |
| `TARGET_UNREACHABLE` | Target agent or URL not responding | Yes | Retry per max_retries with backoff |
| `EXECUTION_TIMEOUT` | Execution exceeded timeout | Yes | Retry per max_retries |
| `LOCK_CONTENTION` | Another instance holds the tick lock | No | Skip tick — standby mode |
| `OVERLAP_SKIPPED` | Tick skipped due to skip-if-running policy | No | Log and emit schedule.skipped |
| `QUEUE_FULL` | Queue depth exceeded for queue overlap policy | No | Skip tick, emit schedule.skipped |
| `SCHEDULE_EXPIRED` | Schedule past expires_at during registration | No | Reject registration |
| `STORAGE_ERROR` | Failed to read/write schedule data | Yes | Retry with backoff |

### Retry Strategy

Failed executions are retried with exponential backoff per
`patterns/retry`:

| Attempt | Delay |
|---------|-------|
| 1 | Immediate (within current tick) |
| 2 | 2 seconds |
| 3 | 4 seconds |
| 4 | 8 seconds |
| 5 | 16 seconds |

After `max_retries` exhausted, the execution is marked `failed`
and `schedule.failed` is emitted. The schedule itself remains
`active` — only the individual execution fails. The next tick
dispatches a fresh execution with attempt = 1.

---

## Implementation Notes

- **Timezone library**: Implementations MUST use a robust IANA
  timezone database (e.g. `time/tzdata` in Go, `Intl` in Node,
  `chrono-tz` in Rust). Do NOT hand-roll DST logic.
- **Expression parsing**: Validate cron expressions at registration
  time, not at evaluation time. Reject malformed expressions early.
- **Lock TTL sizing**: `lock_ttl` MUST be greater than `tick_interval`
  to prevent lock expiration mid-tick. Recommended: 2× tick_interval.
- **Missed-tick window**: The `missed_tick_lookback` config bounds
  how far back the executor checks for missed ticks. Without a bound,
  `fire-all` could dispatch thousands of executions after extended
  downtime.
- **Queue depth**: Schedules with `overlap_policy: queue` accumulate
  pending executions. The `max_queue_depth` config prevents unbounded
  growth. When exceeded, new ticks are skipped with `QUEUE_FULL`.
- **Idempotent registration**: Same `name` + `target_agent` updates
  the existing schedule rather than creating a duplicate. This matches
  the cron agent's natural key constraint.
- **Payload immutability**: The `payload` field is stored at
  registration time and sent unchanged on every tick. Dynamic payloads
  require the target agent to fetch current data on execution.
- **Clock skew**: In distributed deployments, executor instances
  SHOULD use NTP-synchronized clocks. Lock TTLs absorb minor skew,
  but skew exceeding `tick_interval` may cause duplicate firings.
- **Ordering**: Missed-tick `fire-all` dispatches are sent in
  chronological order but delivery is best-effort. Targets MUST NOT
  depend on strict ordering — use the `fired_at` timestamp to
  sequence.

---

## Verification Checklist

- [ ] Schedule registration validates cron expression syntax before persisting
- [ ] Schedule registration rejects missing timezone or invalid IANA identifier
- [ ] One-time schedules require `fire_at` and transition to `expired` after execution
- [ ] Recurring schedules compute `next_fire` in the declared timezone, including DST transitions
- [ ] Overlap policy `skip-if-running` prevents dispatch when a pending execution exists
- [ ] Overlap policy `queue` respects `max_queue_depth` and rejects when full
- [ ] Missed-tick `fire-once` dispatches exactly one catch-up execution
- [ ] Missed-tick `fire-all` dispatches one execution per missed tick in order
- [ ] Missed-tick `skip` discards all missed ticks without dispatch
- [ ] Distributed lock guarantees only one executor instance dispatches per tick
- [ ] Lock TTL exceeds tick interval to prevent mid-tick expiration
- [ ] `schedule.fired` event emitted on every successful dispatch
- [ ] `schedule.skipped` event emitted with reason and policy on every skip
- [ ] `schedule.expired` event emitted when schedule reaches `expires_at`
- [ ] Failed executions retry with backoff up to `max_retries` before emitting `schedule.failed`
- [ ] Schedule lifecycle transitions match the declared state machine (no illegal transitions)
