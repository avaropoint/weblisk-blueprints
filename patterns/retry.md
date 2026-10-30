<!-- blueprint
type: pattern
name: retry
version: 2.0.1
requires: [protocol/types, architecture/agent, patterns/rate-limiting]
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
  - blueprint: protocol/types
    version: ">=1.0.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, retryable, retry_after, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <4.0.0"
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
        - name: RateLimitStatus
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
          type: enum(exponential)
          required: true
          description: The one backoff, protocol/conventions:backoff. No other formula is offered
        - name: base_delay
          type: duration
          required: true
          description: The backoff's base (protocol/conventions:backoff), default 1s
        - name: jitter
          type: boolean
          required: false
          description: Full jitter, which protocol/conventions:backoff always applies; false is refused
        - name: max_delay
          type: duration
          required: false
          description: The backoff's cap (protocol/conventions:backoff), default 30s
        - name: retryable_errors
          type: '[]string'
          required: false
          description: Error codes that trigger retry (default includes all transient codes)
        - name: non_retryable_errors
          type: '[]string'
          required: false
          description: Error codes that immediately fail without retry
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
          description: Consecutive successful probe requests to close from HALF_OPEN; HALF_OPEN allows up to success_threshold sequential probes
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
  max_attempts: 3            # protocol/conventions:max-attempts
  backoff: exponential       # protocol/conventions:backoff
  base_delay: 1s
  max_delay: 30s
  jitter: true               # full jitter, always
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

### Backoff

The delay before each retry is [`protocol/conventions`](../protocol/conventions.md#backoff)'s, with
`base_delay` and `max_delay` as its base and max, and full jitter. This
pattern adds no formula, schedule or jitter of its own, and a component
that needs another pace sets `base_delay` and `max_delay`. A `Retry-After`
the server sends on a 429 or 503 is a floor on the delay, as that rule says.

---

## Circuit Breaker

### States

```
CLOSED → (failures exceed threshold) → OPEN
OPEN → (recovery timeout expires) → HALF_OPEN
HALF_OPEN → (success_threshold probes succeed) → CLOSED
HALF_OPEN → (probe fails) → OPEN
```

| State | Behavior |
|-------|----------|
| CLOSED | Normal operation. Requests pass through. Failures are counted. |
| OPEN | All requests fail immediately without attempting. Returns cached error. |
| HALF_OPEN | Probe requests are allowed through one at a time, up to `success_threshold`. When that many succeed in a row, circuit closes. If any fails, circuit opens again. |

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
targets that are still answering.

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
| Agent → Agent (task) | `protocol/conventions:task-timeout` | Per-workflow phase |
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
    max_attempts: 5          # More attempts for email delivery
    base_delay: 5s           # Longer delays for SMTP
    max_delay: 60s
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
      base_delay: 5s
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
- Domain controllers use circuit breaker state to decide their own
  readiness. While a required agent's circuit is open, the domain
  renews its lease not ready, its `checks` naming that agent
  ([`protocol/types`](../protocol/types.md#leasestate) §LeaseState).
- The retry pattern works with the rate-limiting pattern: when a 429
  is received, its Retry-After is a floor on the backoff
  (`protocol/conventions:backoff`).
- Idempotent operations (GET, HEAD, DELETE by ID) are always safe to
  retry. Non-idempotent operations (POST) SHOULD include an
  idempotency key to prevent duplicate side effects.

## Verification Checklist

- [ ] Transient errors trigger retry with exponential backoff — [Default Retry Configuration](#default-retry-configuration), [Error Classification](#error-classification)
- [ ] Permanent errors fail immediately without retry — [Error Classification](#error-classification)
- [ ] Every retry delay is full jitter under `protocol/conventions:backoff` — [Backoff](#backoff), [`protocol/conventions`](../protocol/conventions.md#backoff)
- [ ] Max delay caps exponential growth — [Backoff](#backoff), [`protocol/conventions`](../protocol/conventions.md#backoff)
- [ ] No retry on a 429 comes before its Retry-After — [Backoff](#backoff), [`protocol/conventions`](../protocol/conventions.md#backoff)
- [ ] Circuit breaker trips after consecutive failure threshold — [States](#states), [Default Configuration](#default-configuration)
- [ ] Circuit breaker enters HALF_OPEN after recovery timeout — [States](#states), [Default Configuration](#default-configuration)
- [ ] `success_threshold` consecutive successful probes in HALF_OPEN close the circuit — [Contracts](#contracts), [States](#states)
- [ ] Failed probe in HALF_OPEN reopens circuit — [States](#states)
- [ ] Per-target circuits isolate failures — [Per-Target Circuits](#per-target-circuits)
- [ ] Circuit breaker state changes emit events to alerting — [Circuit Breaker Events](#circuit-breaker-events)
- [ ] Agent-specific overrides apply correctly — [Override Configuration](#override-configuration)
- [ ] Domain workflow phase timeouts trigger retry logic — [Domain Workflow Integration](#domain-workflow-integration)
- [ ] Metrics emit for retries, exhaustion, and circuit breaker state — [Observability](#observability)
- [ ] Timeouts cancel in-flight requests where supported — [Timeout Handling](#timeout-handling)
