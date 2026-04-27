<!-- blueprint
type: pattern
name: retry
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, patterns/rate-limiting]
platform: any
tier: free
-->

# Retry & Circuit Breaker Pattern

Unified retry semantics, backoff strategies, and circuit breaker
behavior for the Weblisk framework. Defines how agents handle
transient failures when communicating with other agents, external
services, or storage.

This pattern is a cross-cutting concern — it applies to all
inter-component communication. Individual agents inherit these
defaults and MAY override them for domain-specific requirements.

## Overview

The framework provides three layers of failure handling:

1. **Retry** — Automatically retry failed requests with backoff
2. **Circuit Breaker** — Stop retrying when a target is consistently
   failing, allowing it to recover
3. **Timeout** — Bound how long any single request can take

These work together: a request that times out triggers a retry. Too
many retries trip the circuit breaker. The circuit breaker
periodically allows a probe request to check if the target recovered.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, retryable, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, retryable, retry_after]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentConfig
          fields_used: [name, retry, circuit_breaker]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/rate-limiting
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RateLimitResponse
          fields_used: [retry_after, status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Retry transient, fail permanent** — Transient errors trigger retries with backoff; permanent errors fail immediately without wasting resources.
2. **Backoff prevents thundering herd** — Exponential backoff with jitter prevents coordinated retry storms when shared dependencies recover.
3. **Circuit breakers isolate failures** — Per-target circuit breakers stop retrying consistently-failing targets, protecting the caller and allowing the target to recover.
4. **Framework-level, not application-level** — Retry and circuit breaker behavior is provided by the framework for all inter-component communication, not reimplemented by each agent.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: retry-with-backoff
      description: Automatically retry failed requests with configurable backoff strategy
      parameters:
        - name: max_attempts
          type: int
          required: true
          description: Total number of attempts including the original request
        - name: backoff
          type: enum(exponential, linear, fixed)
          required: true
          description: Backoff algorithm for delay calculation
        - name: base_delay
          type: int
          required: true
          description: Base delay in milliseconds between retry attempts
        - name: jitter
          type: boolean
          required: false
          description: Apply randomized jitter to prevent thundering herd
      inherits: Default retry configuration for all inter-agent communication
      overridable: true
      override_constraints: max_attempts >= 1; base_delay > 0; max_delay >= base_delay
    - name: circuit-breaker
      description: Stop retrying consistently-failing targets and allow recovery
      parameters:
        - name: failure_threshold
          type: int
          required: true
          description: Consecutive failures before tripping the circuit
        - name: recovery_timeout
          type: int
          required: true
          description: Milliseconds before transitioning to HALF_OPEN
        - name: success_threshold
          type: int
          required: true
          description: Consecutive successes to close from HALF_OPEN
      inherits: Per-target circuit breaker with CLOSED/OPEN/HALF_OPEN states
      overridable: true
      override_constraints: failure_threshold >= 1; recovery_timeout > 0
  types:
    - name: RetryConfig
      description: Retry strategy configuration with backoff and jitter settings
      inherited_by: Types section
    - name: CircuitBreakerConfig
      description: Circuit breaker thresholds and recovery parameters
      inherited_by: Types section
  events:
    - topic: system.circuit_breaker_state_change
      description: Emitted when a circuit breaker transitions between states
      payload: {target, from_state, to_state, failure_count, last_error, timestamp}
```

---

## Retry Strategy

### Default Retry Configuration

```yaml
retry:
  max_attempts: 3            # Total attempts (1 original + 2 retries)
  backoff: exponential       # exponential | linear | fixed
  base_delay: 1000           # milliseconds
  max_delay: 30000           # milliseconds
  jitter: true               # Add randomized jitter to prevent thundering herd
  retryable_errors:
    - TIMEOUT
    - CONNECTION_REFUSED
    - SERVICE_UNAVAILABLE     # 503
    - TOO_MANY_REQUESTS       # 429 (respects Retry-After header)
    - GATEWAY_TIMEOUT         # 504
  non_retryable_errors:
    - BAD_REQUEST             # 400
    - UNAUTHORIZED            # 401
    - FORBIDDEN               # 403
    - NOT_FOUND               # 404
    - CONFLICT                # 409
    - VALIDATION_ERROR
    - PERMANENT_FAILURE
```

### Backoff Algorithms

#### Exponential (Default)

```
delay = min(base_delay × 2^(attempt - 1), max_delay)
```

| Attempt | Base Delay | Calculated | With Jitter (±25%) |
|---------|-----------|------------|-------------------|
| 1 | 1000ms | 1000ms | 750–1250ms |
| 2 | 1000ms | 2000ms | 1500–2500ms |
| 3 | 1000ms | 4000ms | 3000–5000ms |
| 4 | 1000ms | 8000ms | 6000–10000ms |

#### Linear

```
delay = min(base_delay × attempt, max_delay)
```

#### Fixed

```
delay = base_delay  (constant, no escalation)
```

### Jitter

Always enabled by default. Prevents thundering herd when multiple
agents retry simultaneously after a shared dependency recovers.

```
jittered_delay = delay × (0.75 + random() × 0.5)
```

### Retry-After Respect

When a 429 response includes a `Retry-After` header, the retry delay
MUST use the server-specified value instead of the calculated backoff:

```
if response.status == 429 && response.headers["Retry-After"]:
    delay = parse_retry_after(response.headers["Retry-After"])
else:
    delay = calculate_backoff(attempt)
```

---

## Circuit Breaker

### States

```
CLOSED → (failures exceed threshold) → OPEN
OPEN → (recovery timeout expires) → HALF_OPEN
HALF_OPEN → (probe succeeds) → CLOSED
HALF_OPEN → (probe fails) → OPEN
```

| State | Behavior |
|-------|----------|
| CLOSED | Normal operation. Requests pass through. Failures are counted. |
| OPEN | All requests fail immediately without attempting. Returns cached error. |
| HALF_OPEN | One probe request is allowed through. If it succeeds, circuit closes. If it fails, circuit opens again. |

### Default Configuration

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 5       # Consecutive failures to trip
  recovery_timeout: 30000    # milliseconds before HALF_OPEN
  success_threshold: 2       # Consecutive successes to close from HALF_OPEN
  monitored_errors:
    - TIMEOUT
    - CONNECTION_REFUSED
    - SERVICE_UNAVAILABLE
```

### Per-Target Circuits

Each agent maintains a separate circuit breaker per communication
target:

| Target | Circuit Key |
|--------|------------|
| Another agent | `agent:{agent_name}` |
| External API | `external:{service_name}` |
| Storage | `storage:{store_name}` |
| Orchestrator | `orchestrator` |

This prevents one failing dependency from blocking communication with
healthy targets.

### Circuit Breaker Events

When a circuit breaker changes state, it emits an event:

```json
{
  "event": "circuit_breaker_state_change",
  "target": "agent:seo-analyzer",
  "from_state": "closed",
  "to_state": "open",
  "failure_count": 5,
  "last_error": "TIMEOUT",
  "timestamp": "2026-04-25T10:00:00Z"
}
```

These events are routed to the alerting agent. Circuit breaker trips
on agent-to-agent communication generate `high` severity alerts.

---

## Timeouts

### Default Timeouts

| Communication | Default | Configurable |
|--------------|---------|-------------|
| Agent → Agent (task) | 30s | Per-workflow phase |
| Agent → Agent (direct message) | 10s | Per-agent config |
| Agent → Orchestrator | 5s | Agent config |
| Agent → Storage | 5s | Agent config |
| Agent → External API | 30s | Per-service config |
| Gateway → Agent | 30s | Per-route config |
| Domain → Agent (workflow phase) | Phase-specific | Workflow definition |

### Timeout Handling

When a request times out:

1. The request is cancelled (if the transport supports cancellation)
2. A TIMEOUT error is returned to the caller
3. The timeout counts as a failure for circuit breaker tracking
4. The retry logic determines whether to retry based on remaining
   attempts and the retryable_errors list

---

## Agent Integration

### Default Behavior

Every agent gets retry and circuit breaker behavior automatically
for all inter-agent communication. The defaults from this pattern
apply unless explicitly overridden.

### Override Configuration

Agents can override defaults in their configuration:

```yaml
# Agent-specific retry overrides
agent:
  name: email-send
  retry:
    max_attempts: 5          # More retries for email delivery
    base_delay: 5000         # Longer delays for SMTP
    max_delay: 60000
  circuit_breaker:
    failure_threshold: 3     # Trip faster for email
    recovery_timeout: 60000  # Wait longer before retry
```

### Domain Workflow Integration

Domain workflows specify timeouts per phase. When a phase times out,
the domain controller applies the retry logic before marking the
phase as failed:

```yaml
phases:
  - name: scan
    agent: seo-analyzer
    action: scan_html
    timeout: 60              # Phase timeout
    retry:
      max_attempts: 2        # Override for this phase
      backoff: fixed
      base_delay: 5000
```

---

## Error Classification

The retry pattern relies on the framework's standard error
classification (see protocol/types):

| Category | Retryable | Action |
|----------|-----------|--------|
| transient | Yes | Retry with backoff |
| permanent | No | Fail immediately, return error |
| partial | Depends | Retry if retry_hint is true |

The `retryable` field in ErrorResponse is authoritative. If present,
it overrides the category-based default.

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| agent_retry_total | counter | Retry attempts by target, attempt_number, result |
| agent_retry_exhausted_total | counter | Retries exhausted (all attempts failed) by target |
| agent_circuit_breaker_state | gauge | Current state (0=closed, 1=open, 2=half_open) by target |
| agent_circuit_breaker_trips_total | counter | Circuit breaker trips by target |
| agent_request_timeout_total | counter | Timed-out requests by target |
| agent_request_duration_seconds | histogram | Request duration including retries |

---

## Implementation Notes

- Retry and circuit breaker are framework-level behaviors, not
  application-level. Every agent gets them by default for
  inter-component communication.
- Agents calling external APIs (LLM providers, SMTP servers, etc.)
  SHOULD configure service-specific retry parameters rather than
  relying on the defaults.
- Circuit breaker state is in-memory per agent process. It resets on
  agent restart, which is acceptable — if an agent restarts, its view
  of dependency health should be fresh.
- Domain controllers use circuit breaker state to determine their own
  health status. If a required agent's circuit is open, the domain
  reports as degraded.
- The retry pattern works with the rate-limiting pattern: when a 429
  is received, the Retry-After header takes precedence over
  calculated backoff.
- Idempotent operations (GET, HEAD, DELETE by ID) are always safe to
  retry. Non-idempotent operations (POST) SHOULD include an
  idempotency key to prevent duplicate side effects.

## Verification Checklist

- [ ] Transient errors trigger retry with exponential backoff
- [ ] Permanent errors fail immediately without retry
- [ ] Jitter is applied to all retry delays
- [ ] Max delay caps exponential growth
- [ ] Retry-After header overrides calculated backoff on 429
- [ ] Circuit breaker trips after consecutive failure threshold
- [ ] Circuit breaker enters HALF_OPEN after recovery timeout
- [ ] Successful probe in HALF_OPEN closes circuit
- [ ] Failed probe in HALF_OPEN reopens circuit
- [ ] Per-target circuits isolate failures
- [ ] Circuit breaker state changes emit events to alerting
- [ ] Agent-specific overrides apply correctly
- [ ] Domain workflow phase timeouts trigger retry logic
- [ ] Metrics emit for retries, exhaustion, and circuit breaker state
- [ ] Timeouts cancel in-flight requests where supported
