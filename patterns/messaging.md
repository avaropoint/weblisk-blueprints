<!-- blueprint
type: pattern
name: messaging
version: 1.0.0
requires: [protocol/types, architecture/agent, patterns/retry]
platform: any
tier: free
-->

# Messaging Pattern

HTTP-based pub/sub event system for decoupled agent coordination.
Agents publish events to namespaced topics and receive events via
standard HTTP endpoints. The protocol uses HTTP as the sole transport
— no separate message broker, queue service, or bus infrastructure.

## Overview

Weblisk agents coordinate through events. Instead of calling each other
directly, agents publish typed events to namespaced topics. The framework
resolves subscribers from a locally-cached routing table and delivers
events via `POST /v1/event` — standard HTTP.

This pattern is a cross-cutting concern. Agents declare what they
publish (namespace ownership) and subscribe to (topic patterns with
scope) in their manifest. The orchestrator builds the routing table
at registration time and distributes it to all agents as part of the
service directory.

For synchronous request/response communication (when the caller needs
a reply), agents use `POST /v1/message` directly. Events are
fire-and-forget — the publisher does not wait for processing to
complete.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: EventEnvelope
          fields_used: [event_id, topic, source, scope, correlation_id, timestamp, trace_id, version, payload, token]
        - name: AgentManifest
          fields_used: [name, subscriptions, namespace]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentState
          fields_used: [state, url, subscriptions]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/retry
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RetryConfig
          fields_used: [max_attempts, backoff, jitter]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **One protocol** — HTTP is the only transport. No separate message
   broker or queue infrastructure to deploy and maintain.
2. **Typed events** — Every event has a schema. Publishers and
   subscribers agree on the shape. Malformed events are rejected.
3. **Namespace ownership** — Each top-level namespace is exclusively
   owned by one agent. The orchestrator enforces this at registration,
   making event collision structurally impossible.
4. **Scoped delivery** — Events carry a `scope` field that limits
   which subscribers receive them. Agents only get events addressed
   to them unless they have explicit permission for global observation.
5. **At-least-once delivery** — The framework retries failed HTTP
   deliveries. Subscribers MUST be idempotent.
6. **Dead-letter safety** — Events that fail delivery after all retries
   are stored locally for inspection and replay, never discarded.
7. **Zero infrastructure** — The routing table IS the service
   directory. No external broker needed. The framework resolves
   subscribers locally and delivers via HTTP POST.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: event-publishing
      description: Publish typed events to namespaced topics with scope-based delivery
      parameters:
        - name: topic
          type: string
          required: true
          description: Dot-separated topic in an owned namespace
        - name: payload
          type: object
          required: true
          description: Event data conforming to topic schema
        - name: scope
          type: string
          required: true
          description: Target agent name or "*" for global broadcast
      inherits: Namespace ownership validation, subscriber resolution, delivery pipeline
      overridable: true
      override_constraints: Must validate namespace ownership and deliver via HTTP POST

    - name: event-subscribing
      description: Declare topic subscriptions and receive events via POST /v1/event
      parameters:
        - name: pattern
          type: string
          required: true
          description: Topic or wildcard pattern to subscribe to
        - name: scope
          type: string
          required: false
          description: Scope filter — self, *, or specific agent name
      inherits: Pattern matching (exact, *, #), consumer groups, idempotent handling
      overridable: true
      override_constraints: Must handle duplicate event_ids idempotently

    - name: dead-letter-handling
      description: Store events that fail delivery after retry exhaustion
      parameters:
        - name: ttl
          type: int
          required: false
          description: Seconds before dead-lettering undelivered events
      inherits: Local dead-letter storage, replay capability
      overridable: true
      override_constraints: Must never discard failed events silently

  types:
    - name: EventEnvelope
      description: Standard event wrapper with id, topic, source, scope, trace context, and typed payload
      inherited_by: Event Envelope section
    - name: Subscription
      description: Agent subscription declaration with pattern, group, scope, and concurrency limit
      inherited_by: Subscribing section
    - name: RoutingTable
      description: Local mapping of topic patterns to subscriber endpoints
      inherited_by: Publishing section

  endpoints:
    - path: /v1/event
      description: Receive published events for processing by registered handlers
      inherited_by: Event Envelope section

  events:
    - topic: messaging.dead_lettered
      description: Emitted when an event is moved to the dead-letter store after retry exhaustion
      payload: {event_id, topic, target, attempts, last_error}
```

---

## Event Envelope

Every event is wrapped in a standard envelope, delivered as the JSON
body of `POST /v1/event`:

```json
{
  "event_id": "evt-a1b2c3d4e5f6",
  "topic": "workflow.completed",
  "source": "workflow",
  "scope": "seo",
  "correlation_id": "wf-exec-001",
  "timestamp": 1712160001,
  "trace_id": "abc123def456789012345678",
  "version": "1.0.0",
  "payload": {
    "workflow": "seo-audit",
    "status": "completed",
    "result": { }
  },
  "token": "<auth token>"
}
```

### Envelope Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| event_id | string | yes | Globally unique identifier (UUID v7 recommended — time-sortable) |
| topic | string | yes | Dot-separated topic name |
| source | string | yes | Name of the publishing agent |
| scope | string | yes | Target agent name, or `"*"` for global |
| correlation_id | string | no | Links all events in one execution chain |
| timestamp | int64 | yes | Unix epoch seconds |
| trace_id | string | yes | Distributed trace context |
| version | string | yes | Schema version of the payload |
| payload | object | yes | Event-specific typed data |
| token | string | no | Auth token for delivery verification |

See [types.md — EventEnvelope](../protocol/types.md) for the canonical
type definition.

### Event ID Generation

Event IDs MUST be unique across the entire hub. Recommended format
is UUID v7 (time-sortable). The event_id is the idempotency key —
subscribers use it to detect and skip duplicate deliveries.

---

## Topics

Topics are dot-separated hierarchical names following a namespace
ownership model.

### Topic Naming Convention

```
<namespace>.<entity>.<action>
```

Examples:
- `workflow.trigger` — request to start a workflow
- `workflow.phase.complete` — a workflow phase finished
- `task.submit` — new task submitted for dispatch
- `task.complete` — task execution finished
- `lifecycle.recommendation.created` — new recommendation proposed
- `health.agent.state_change` — agent health state changed
- `seo.audit.result` — SEO domain audit result callback

### Topic Matching

| Pattern | Matches |
|---------|---------|
| `workflow.completed` | Exact match only |
| `workflow.*` | Any single segment under workflow |
| `workflow.#` | Anything under workflow (any depth) |
| `*.*.created` | Any created event in any namespace/entity |

`*` matches exactly one segment. `#` matches zero or more segments.

### Namespace Ownership

The top-level segment of a topic is its **namespace**. Namespaces are
exclusively owned by one agent. The orchestrator enforces ownership
at registration — no two agents can publish to the same namespace.

See [spec.md — Namespace Control](../protocol/spec.md#namespace-control)
for the full enforcement rules.

### Standard Namespaces

| Namespace | Owner | Description |
|-----------|-------|-------------|
| `system` | orchestrator | Agent lifecycle (registered, deregistered, shutdown) |
| `workflow` | workflow agent | Workflow triggers, phases, completion |
| `task` | task agent | Task submission, dispatch, tracking |
| `lifecycle` | lifecycle agent | Strategies, observations, recommendations |

Domain controllers and work agents own their own namespaces
(e.g., `seo.*`, `content.*`, `health.*`).

### Federation Topic Qualification

When events cross hub boundaries via federation, topics are prefixed
with the originating hub's identity:

```
Local:       workflow.completed
Federated:   acme-corp::workflow.completed
```

The `::` separator distinguishes hub-qualified topics from local ones.
See [spec.md — Federation Namespace Qualification](../protocol/spec.md#federation-namespace-qualification).

---

## Publishing

### Publish API

Agents publish events through the framework client:

```
publish(topic, payload, scope, options)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic | string | yes | Topic to publish to (must be in owned namespace) |
| payload | object | yes | Event data (must match topic schema) |
| scope | string | yes | Target agent name, or `"*"` for global |
| options.correlation_id | string | no | Execution chain identifier |
| options.priority | string | no | `low`, `normal`, `high`, `critical` (default: `normal`) |
| options.ttl | int | no | Seconds before dead-lettering undelivered (default: 86400) |

### Publish Flow

```
1. Validate namespace ownership:
   Topic "workflow.completed" → namespace "workflow"
   Check: does this agent own "workflow"? (from local namespace map)
   If no → reject locally, log error. Event is NOT sent.

2. Build EventEnvelope:
   event_id:       UUID v7
   topic:          provided topic
   source:         this agent's name
   scope:          provided scope
   correlation_id: provided or inherited from current context
   trace_id:       inherited from current trace context
   timestamp:      now (Unix epoch seconds)
   version:        agent's event schema version
   payload:        provided payload
   token:          this agent's auth token

3. Resolve subscribers from local routing table:
   a. Match topic against subscription patterns (exact, *, #)
   b. Apply scope filtering:
      - subscriber.scope == "*" → include
      - subscriber.scope == "self" → include ONLY IF scope == subscriber.agent_name
      - subscriber.scope == "<name>" → include ONLY IF scope == "<name>"
   c. Consumer groups: select one subscriber per group (round-robin)
   d. Non-grouped: include all matching subscribers

4. Deliver to each resolved subscriber:
   HTTP POST to subscriber.url (agent's base URL + /v1/event)
   Body: EventEnvelope as JSON
   Headers:
     Content-Type: application/json
     X-Event-Id: <event_id>
     X-Trace-Id: <trace_id>

5. Handle responses:
   2xx → acknowledged, proceed
   429 → respect Retry-After header, queue for retry
   Other failure → retry per patterns/retry (exponential backoff)
   Retry exhaustion → dead-letter locally
```

### Publish Guarantees

- Publishing is local — the framework resolves subscribers from its
  own routing table. No call to the orchestrator is needed.
- The routing table is kept current by `POST /v1/services` broadcasts
  from the orchestrator on every registration/deregistration.
- Published events are immutable. Once published, the payload cannot
  be modified or retracted.

### Blueprint Declaration

Agents declare published events in their blueprint:

```markdown
## Collaboration

### Events Published
| Topic | Payload Type | Trigger Condition |
|-------|-------------|-------------------|
| health.agent.state_change | HealthStateChange | Agent state transition detected |
| health.hub.score_updated | HubHealthScore | Hub score recalculated |
```

---

## Subscribing

### Manifest Declaration

Agents declare subscriptions in their manifest at registration:

```json
{
  "subscriptions": [
    {
      "pattern": "workflow.completed",
      "group": "seo",
      "scope": "self",
      "max_concurrent": 5
    },
    {
      "pattern": "system.agent.registered",
      "scope": "self"
    }
  ]
}
```

### Subscription Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| pattern | string | yes | — | Topic or wildcard pattern |
| group | string | no | agent name | Consumer group for load balancing |
| scope | string | no | `"self"` | Scope filter (see Event Scoping below) |
| max_concurrent | int | no | 5 | Max parallel event processing |

### Consumer Groups

When multiple instances of the same agent are running, they form a
consumer group. Each event is delivered to exactly one member of the
group (round-robin load balancing). Different groups each receive
every event (fan-out).

```
Topic: task.complete, scope: "workflow"

Group "workflow":
  Workflow Instance 1 ← receives event A, C  (load-balanced)
  Workflow Instance 2 ← receives event B, D

Group "lifecycle" (scope: "*"):
  Lifecycle Instance 1 ← receives ALL events A, B, C, D
```

Group name defaults to the agent's `name` from its manifest.

### Event Handling

Agents register event handlers during startup:

```
on_event("workflow.completed", handler)
on_event("task.*", handler)
```

When `POST /v1/event` is received, the framework:
1. Parses the `EventEnvelope`
2. Checks idempotency: has `event_id` been processed? If yes, return
   200 OK immediately.
3. Matches `topic` against registered handlers
4. Dispatches to matching handler(s) asynchronously
5. Returns 200 OK immediately (processing continues in background)
6. On handler success: records `event_id` as processed
7. On handler failure: logs error (event is NOT re-requested — the
   publisher already handled retry at delivery time)

### Blueprint Declaration

```markdown
## Collaboration

### Events Subscribed
| Pattern | Payload Type | Processing Summary |
|---------|-------------|-------------------|
| workflow.completed | WorkflowResult | Store observations, update strategy progress |
| lifecycle.recommendation.approved | Recommendation | Resume paused workflow if applicable |
```

---

## Event Scoping

Scoping ensures agents only receive events meant for them. This
prevents noise (irrelevant events), enforces data isolation, and
reduces network traffic.

### How Scope Works

Every event has a `scope` field (set by publisher). Every subscription
has a `scope` field (set at registration). The framework filters
deliveries by matching both:

| Event Scope | Subscription Scope | Delivered? |
|-------------|-------------------|------------|
| `"seo"` | `"self"` (subscriber is `seo`) | **Yes** — matches own name |
| `"seo"` | `"self"` (subscriber is `content`) | **No** — not addressed to content |
| `"seo"` | `"*"` | **Yes** — global observer |
| `"seo"` | `"seo"` (explicit) | **Yes** — explicit match |
| `"*"` | `"self"` | **Yes** — global events reach everyone |
| `"*"` | `"*"` | **Yes** — global observer on global event |

### Scope Permissions

The orchestrator validates scope at registration:

| Subscription Scope | Allowed? | Requirement |
|-------------------|----------|-------------|
| `"self"` | Always | Default, no permission needed |
| `"*"` | Restricted | Agent must have `event:observe` capability |
| `"<agent-name>"` | Restricted | Must be declared in `collaborators` or target agent lists this agent as collaborator |

### Scope Propagation in Execution Chains

Infrastructure agents propagate scope through event chains so that
results return to the correct invoker:

```
1. SEO domain → workflow.trigger  (scope: "workflow")
   Workflow Agent records: invoker = "seo"

2. Workflow Agent → task.submit   (scope: "task")
   Task Agent records: requester = "workflow"

3. Task Agent → task.complete     (scope: "workflow")
   Addressed back to Workflow Agent

4. Workflow Agent → workflow.completed (scope: "seo")
   Addressed back to original invoker

Result: only SEO domain and global observers get the completion event.
Content domain never sees it.
```

---

## Delivery Guarantees

### At-Least-Once

The publishing agent's framework retries failed HTTP deliveries.
Subscribers MUST handle duplicate events gracefully.

### Idempotency

Subscribers MUST track processed `event_id` values to skip duplicates:

```
1. Receive event via POST /v1/event
2. Check: has event_id been processed?
   a. Yes → return 200 OK, skip processing
   b. No → process event, record event_id, return 200 OK
3. Event ID storage: in-memory set with TTL matching topic retention
   (for high throughput) or persistent storage (for critical events)
```

### Ordering

Events within a single topic from a single publisher are delivered
in publish order (publisher sends sequentially per topic). When
multiple publishers write to the same topic, ordering is by
timestamp (best-effort, not strict).

### Delivery Retry

When a subscriber returns a non-2xx response, the publishing agent's
framework retries using [patterns/retry](retry.md) configuration:

```yaml
event_delivery_retry:
  max_attempts: 3
  backoff: exponential
  base_delay: 1000
  max_delay: 30000
```

429 responses respect the `Retry-After` header specifically.

---

## Dead-Letter Handling

Events that fail delivery after all retry attempts are stored locally
by the publishing agent's framework in a dead-letter log.

### Dead-Letter Entry Structure

```json
{
  "original_event": { },
  "failure_reason": "UNREACHABLE",
  "last_error": "connection refused",
  "attempts": 3,
  "first_attempt": 1712160001,
  "last_attempt": 1712160035,
  "subscriber": "alerting"
}
```

See [types.md — DeadLetterEntry](../protocol/types.md) for the full
type definition.

### Dead-Letter Management

Each agent's framework exposes dead-letter data for local inspection:

| Operation | Mechanism |
|-----------|-----------|
| List | Framework API: `list_dead_letters(topic?, since?)` |
| Replay | Framework API: `replay_dead_letter(event_id)` — re-attempt delivery |
| Purge | Framework API: `purge_dead_letters(topic?, older_than?)` |

Dead-letter retention: 7 days by default (`WL_DLQ_RETENTION`).

### Centralized Dead-Letter (Optional)

For centralized visibility, a hub MAY deploy a dead-letter
infrastructure agent. Publishing agents emit a `system.dead_letter`
event when dead-lettering occurs, and the DLQ agent collects these
for dashboard and alerting purposes.

---

## Backpressure

### Publisher-Side

Publishers are not self-throttled. If delivery fails (subscriber
returns 429 or is unreachable), the framework retries with backoff.
If the publisher itself cannot send (network, memory), the publish
call fails and the agent applies its own retry logic.

### Subscriber-Side

When a subscriber cannot keep up:

1. **Concurrent limit**: `max_concurrent` on the subscription caps
   parallel handler invocations. Events queue locally until a slot
   opens.
2. **429 response**: When the agent's event processing queue is full,
   `POST /v1/event` returns 429 with `Retry-After`. The publisher
   respects this.
3. **Consumer groups**: If one group member is slow, the round-robin
   in the publishing framework routes to other members, naturally
   load-balancing.

---

## Interaction with Direct Messages

Events and direct messages coexist for different purposes:

| Use Case | Mechanism | Why |
|----------|-----------|-----|
| Fire-and-forget notification | `POST /v1/event` | Publisher doesn't need response |
| Fan-out to multiple agents | `POST /v1/event` | Multiple subscribers per topic |
| Workflow coordination | `POST /v1/event` | Decoupled phase progression |
| Request data from another agent | `POST /v1/message` | Caller needs synchronous response |
| Fetch workflow definition | `POST /v1/message` | Caller blocks until definition returned |
| Health check | `POST /v1/health` | Dedicated endpoint |

**Rule of thumb:** if the sender doesn't need a response, publish an
event. If the sender blocks until a response arrives, use direct
message.

---

## Configuration

```yaml
messaging:
  default_ttl: 86400            # 24 hours — event expiry for dead-letter
  dlq_retention: 604800         # 7 days — dead-letter entry retention
  delivery_retry_max: 3         # Max delivery attempts per subscriber
  delivery_retry_base: 1000     # Base delay (ms) for exponential backoff
  delivery_retry_max_delay: 30000  # Max delay (ms) cap
  idempotency_window: 86400     # Seconds to track processed event_ids
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_EVENT_DEFAULT_TTL` | `86400` | Default event TTL (seconds) |
| `WL_DLQ_RETENTION` | `604800` | Dead-letter entry retention (seconds) |
| `WL_EVENT_RETRY_MAX` | `3` | Max delivery retry attempts |
| `WL_EVENT_IDEMPOTENCY_WINDOW` | `86400` | Processed event_id tracking window (seconds) |

---

## Implementation Notes

- Event delivery is HTTP POST to subscriber's `/v1/event` endpoint — no external message broker required
- Agents resolve subscribers from their local routing table copy — no call to the orchestrator needed
- Consumer groups enable load balancing — the framework selects one subscriber per group using round-robin
- Idempotency requires tracking processed `event_id` values for at least `WL_EVENT_IDEMPOTENCY_WINDOW` seconds
- Dead-letter entries should be periodically reviewed and replayed or purged
- Event ordering is best-effort — agents should not depend on strict ordering across topics
- CloudEvents alignment enables future interop with external systems via simple field mapping

---

## Standards Alignment: CloudEvents v1.0

The Weblisk event envelope is intentionally compatible with the
[CloudEvents v1.0 specification](https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/spec.md).

| Weblisk Field | CloudEvents Attribute | Notes |
|---------------|----------------------|-------|
| `event_id` | `id` (REQUIRED) | Both are globally unique identifiers |
| `topic` | `type` (REQUIRED) | Weblisk uses dot notation; CloudEvents uses reverse-DNS |
| `source` | `source` (REQUIRED) | Both identify the producer |
| `timestamp` | `time` (OPTIONAL) | Both use timestamp; Weblisk makes it required |
| `version` | `dataschemaversion` | Weblisk versions the payload schema |
| `payload` | `data` | Event-specific content |
| `trace_id` | Extension: `traceparent` | Distributed tracing context |
| `scope` | Extension: custom | Weblisk-specific delivery scoping |
| `correlation_id` | Extension: custom | Weblisk-specific execution chain linking |
| — | `specversion` (REQUIRED) | CloudEvents requires `"1.0"`; Weblisk omits (implied) |
| — | `datacontenttype` | CloudEvents declares media type; Weblisk is always JSON |

### Interoperability

To emit CloudEvents-compatible envelopes for external consumers:

```json
{
  "specversion": "1.0",
  "id": "<event_id>",
  "type": "io.weblisk.<topic>",
  "source": "weblisk://<hub-id>/agents/<source>",
  "time": "<timestamp as ISO 8601>",
  "datacontenttype": "application/json",
  "data": "<payload>"
}
```

This mapping is OPTIONAL. Internal event delivery uses the native
Weblisk envelope. Federation bridges or external integrations MAY
perform the conversion.

---

## Verification Checklist

- [ ] Events published with complete envelope (event_id, topic, source, scope, timestamp, trace_id, version, payload)
- [ ] Event IDs are globally unique (UUID v7)
- [ ] Framework validates namespace ownership before publishing
- [ ] Framework resolves subscribers from local routing table (no orchestrator call)
- [ ] Scope filtering applied: self-scoped subscribers only get their own events
- [ ] Global observers (scope: "*") require `event:observe` capability
- [ ] Consumer groups load-balance events across instances (round-robin)
- [ ] Different consumer groups each receive matching events (fan-out)
- [ ] Duplicate events (same event_id) detected and skipped by subscribers
- [ ] Failed deliveries retried with exponential backoff
- [ ] Exhausted retries result in dead-letter storage (not discard)
- [ ] 429 responses from subscribers respected with Retry-After
- [ ] Correlation ID propagated through execution chains
- [ ] Trace ID propagated through all events and downstream calls
