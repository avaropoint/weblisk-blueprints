<!-- blueprint
type: architecture
name: agent
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, patterns/retry, patterns/messaging]
platform: any
tier: free
-->

# Weblisk Agent Blueprint

The universal blueprint every agent is built on. Every agent — regardless
of language or platform — follows this structure. The agent handles
protocol endpoints, registration, and messaging. The developer implements
only the custom logic (Execute + HandleMessage).

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /v1/execute
          methods: [POST]
        - path: /v1/message
          methods: [POST]
        - path: /v1/health
          methods: [POST]
        - path: /v1/services
          methods: [POST]
        - path: /v1/event
          methods: [POST]
      types:
        - name: TaskRequest
          fields_used: [task_id, action, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: AgentMessage
          fields_used: [from, to, type, action, payload, signature]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519KeyPair
          fields_used: [public_key, private_key]
        - name: Signature
          fields_used: [algorithm, value]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, version, url, public_key, capabilities, inputs, outputs, publishes, subscriptions]
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: RegisterResponse
          fields_used: [agent_id, token, services]
        - name: EventEnvelope
          fields_used: [event_id, topic, payload, source, scope, correlation_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/retry
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
```

---

## Responsibilities

### Owns

- HTTP server hosting the 6 protocol endpoints (describe, execute, health, message, services, event)
- Ed25519 key pair generation and message signing/verification
- Registration with the orchestrator and token management
- Service directory cache, routing table cache, and namespace map cache
- Event publishing and subscription dispatch (via the framework base)
- Backpressure and concurrency controls for inbound requests

### Does NOT Own

- Orchestrator registration logic (the orchestrator decides acceptance)
- Workflow execution or task dispatch (owned by Workflow Agent and Task Agent)
- Domain-level business rules (owned by domain controllers)
- Storage persistence (agents use platform-specific storage independently)
- Session management (owned by `architecture/client`)

---

## Interfaces

The agent’s public API surface is the 6 protocol endpoints defined in
[Protocol Endpoint Implementations](#protocol-endpoint-implementations)
and the three developer-facing methods defined in
[Agent Logic Interface](#agent-logic-interface):
`Execute(task, context)`, `HandleMessage(message, context)`, and
`HandleEvent(event)`.

---

## Data Flow

1. Agent starts: generates Ed25519 key pair, builds manifest, starts HTTP server
2. Agent registers with orchestrator via `POST /v1/register` (signed manifest)
3. Orchestrator returns token + service directory; agent caches both
4. Inbound task arrives via `POST /v1/execute` — framework parses, delegates to `Execute()`
5. Inbound message arrives via `POST /v1/message` — framework verifies signature, delegates to `HandleMessage()`
6. Inbound event arrives via `POST /v1/event` — framework checks idempotency, dispatches to matching handlers
7. Outbound messages: agent looks up target in service directory, signs payload, sends `POST /v1/message`
8. Outbound events: agent publishes via framework, which resolves subscribers from routing table
9. Service directory updates arrive via `POST /v1/services` — cache refreshed

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Agent Process                          │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  Agent Framework (base)          │   │
│  │  - HTTP server (6 endpoints)     │   │
│  │  - Registration with orchestrator│   │
│  │  - Service directory + routing   │   │
│  │  - Event publishing + receiving  │   │
│  │  - Message signing/verification  │   │
│  │  - Health reporting              │   │
│  └────────────┬─────────────────────┘   │
│               │ delegates to            │
│  ┌────────────▼─────────────────────┐   │
│  │  Agent Logic (custom)            │   │
│  │  - Execute(task) → result        │   │
│  │  - HandleMessage(msg) → response │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Agent Logic Interface

Every agent implements two methods:

### Execute(task, context) → result
The agent's core intelligence. Receives a task request with full runtime
context (identity, services, LLM provider, workspace). Returns a result
with status, summary, proposed changes, and metrics.

### HandleMessage(message, context) → response_payload
Handles direct messages from other agents. Returns a JSON-serializable
response payload. Used for collaboration and queries.

### HandleEvent(event) → void
Handles incoming pub/sub events (delivered via `POST /v1/event`). Events
are fire-and-forget — there is no return value. The framework dispatches
to registered event handlers by topic pattern. See
[patterns/messaging](../patterns/messaging.md) for the full event model.

## Agent Context

The runtime context provided to Execute and HandleMessage:
- **Identity**: agent's Ed25519 key pair (for signing)
- **Services**: list of available agents (from service directory)
- **Provider**: LLM provider (if configured via WL_AI_* env vars)
- **Workspace**: file operations (read, scan, propose changes)
- **Orch**: orchestrator info (URL, public key, version)
- **Token**: auth token from orchestrator

## Startup Sequence

```
1. Create AgentLogic implementation with domain-specific intelligence
2. Define AgentManifest (name, version, capabilities, inputs, outputs, etc.)
3. Generate Ed25519 key pair → set manifest.public_key
4. Set manifest.url to the agent's listen address
5. Configure LLM provider (if WL_AI_* env vars are set)
6. Configure workspace (current directory)
7. Register HTTP routes for all 6 protocol endpoints
8. Register event handlers (on_event bindings)
9. Start HTTP server in background
10. Wait briefly for server to accept connections
11. Register with orchestrator (if orchestrator URL provided)
12. On registration response: cache routing table and namespace map
    from service directory
13. Block indefinitely (agent is a long-running process)
```

## Registration Flow (from agent side)

```
1. Serialize manifest to JSON
2. Sign manifest JSON with agent's private key
3. Build RegisterRequest: {manifest, signature, timestamp: now()}
4. POST to orchestrator_url + /v1/register
5. If rejected: return error (log and exit or retry)
6. Parse RegisterResponse:
   a. Store auth token for future requests
   b. Store orchestrator info (URL, public key, version)
   c. Store service directory (list of available agents)
7. Print registration confirmation
```

## Protocol Endpoint Implementations

### POST /v1/describe
Simply return the agent's manifest as JSON. No auth needed.

### POST /v1/execute

See [Protocol Specification — POST /v1/execute](../protocol/spec.md)
for the endpoint contract.

**Implementation:**
```
1. Require POST method
2. Parse TaskRequest from body
3. Update services from task.context.services (if provided)
4. Update workspace root from task.context.workspace_root (if provided)
5. Call agentLogic.Execute(task, context)
6. If error → return TaskResult with status="failed", summary=error
7. Set result.task_id, result.agent_name, result.timestamp
8. Sign the result with agent's private key
9. Return result as JSON
```

### POST /v1/health

See [`patterns/observability` — Health Endpoint](../patterns/observability.md#health-endpoint)
for the full response contract. The response includes `name`, `version`,
`state` (online/degraded/offline), `uptime_seconds`, optional sub-component
`checks`, and `metrics_snapshot`.

### POST /v1/message

See [Protocol Specification — POST /v1/message](../protocol/spec.md)
for the endpoint contract and [Identity — Signing](../protocol/identity.md)
for signature verification details.

**Implementation:**
```
1. Require POST method
2. Parse AgentMessage from body
3. If message has signature AND sender's public key is known:
   Verify per identity.md signing rules
   If invalid → 401 "invalid message signature"
4. Call agentLogic.HandleMessage(message, context)
5. If error → 500 with error message
6. Build response AgentMessage:
   - from: this agent's name
   - to: original sender
   - type: "response"
   - action: same as request
   - payload: handler's response
7. Sign response per identity.md
8. Return response as JSON
```

### POST /v1/services
```
1. Require POST method
2. Parse ServiceDirectory from body
3. Update internal service list (thread-safe)
4. Update local routing table cache (thread-safe)
5. Update local namespace map cache (thread-safe)
6. Return 200 OK
```

### POST /v1/event

See [Protocol Specification — POST /v1/event](../protocol/spec.md)
for the endpoint contract and [patterns/messaging](../patterns/messaging.md)
for the full event model.

**Implementation:**
```
1. Require POST method
2. Parse EventEnvelope from body
3. Idempotency check: has event_id been processed?
   If yes → return 200 OK immediately (skip processing)
4. Match event.topic against registered event handlers (exact, *, #)
5. If no handlers match → return 200 OK (silently ignore)
6. Dispatch to matching handler(s) asynchronously
7. Return 200 OK immediately (processing continues in background)
8. On handler completion:
   a. Record event_id as processed (with TTL for cleanup)
   b. If handler publishes follow-up events → framework handles delivery
9. On handler error → log error (event is NOT re-requested)
```

## Service Discovery

The agent maintains an in-memory cache of available services, the
routing table, and the namespace map. Updated:
1. On registration (from RegisterResponse.services)
2. On service directory pushes (from orchestrator POST /v1/services)
3. On task execution (from TaskRequest.context.services)

Helper: `HasService(name) → (ServiceEntry, bool)` — look up an agent by name.

### Routing Table Cache

The local routing table (received from the service directory) is used
by the framework to resolve event subscribers when publishing. See
[patterns/messaging — Publishing](../patterns/messaging.md) for the
resolution algorithm. No call to the orchestrator is needed to publish
an event.

## Sending Messages to Other Agents

```
1. Look up target agent in service directory
2. Build AgentMessage: {from, to, type:"request", action, payload}
3. Sign: {from, to, action, payload} → signature
4. POST to target_url + /v1/message
5. Parse response AgentMessage
6. Return response payload
```

## Requesting a Channel

For authenticated direct communication:
```
1. Build ChannelRequest: {from_agent, to_agent, purpose, token, signature}
2. POST to orchestrator_url + /v1/channel
3. Parse ChannelGrant
4. Use channel_token in subsequent messages to target
```

## Manifest Structure

```json
{
  "name": "agent-name",
  "version": "1.0.0",
  "description": "What this agent does",
  "url": "http://localhost:9710",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "capability:type", "resources": ["glob/pattern/**"]}
  ],
  "inputs": [
    {"name": "input_name", "type": "file_list|json|text", "description": "..."}
  ],
  "outputs": [
    {"name": "output_name", "type": "file_list|json|text", "description": "..."}
  ],
  "collaborators": ["other-agent-name"],
  "approval": "required|auto",
  "publishes": ["namespace"],
  "subscriptions": [
    {
      "pattern": "topic.pattern.*",
      "group": "consumer-group-name",
      "scope": "self",
      "max_concurrent": 5
    }
  ]
}
```

### Manifest Fields: Publishing & Subscriptions

**publishes** ([]string, optional): Namespaces this agent will publish
events to. The orchestrator grants exclusive ownership at registration.
Only agents that publish events need this field.

**subscriptions** ([]Subscription, optional): Event topic patterns this
agent wants to receive. See [patterns/messaging — Subscribing](../patterns/messaging.md)
for the full subscription model.

See [protocol/types.md — AgentManifest](../protocol/types.md) for the
canonical type definition.

### Standard Capabilities

See [types.md — Capability](../protocol/types.md) for the canonical
list of standard capabilities and their descriptions.

## Agent Kinds

The `type` field in the manifest distinguishes three kinds of agents:

| Kind | Manifest Type | Purpose | Dispatched By |
|------|--------------|---------|---------------|
| Domain controller | `"domain"` | Directs a business function, declares workflows | Gateway or CLI (via POST /v1/execute) |
| Work agent | `"agent"` | Performs specific tasks | Task Agent (via POST /v1/execute) |
| Infrastructure agent | `"infrastructure"` | System-level utilities (workflow, task, lifecycle, cron, sync, etc.) | Any authenticated agent |

See [Domain Architecture](domain.md) for the full domain controller spec.

**Domain controllers** register with the orchestrator and declare
`required_agents` and `workflows`. They receive business-level tasks
and decompose them into multi-agent workflows.

**Work agents** perform the actual work. They are dispatched by the
Task Agent via `POST /v1/execute`. They register with the orchestrator
but business tasks should route through their owning domain.

**Infrastructure agents** (sync, cron, webhook, email) provide
reusable platform services. Any authenticated agent or domain can
message them directly.

## Port Assignment Convention

Port assignments are advisory — agents MAY run on any available port.
The registered URL in the manifest is the authoritative address.

| Range | Purpose | Examples |
|-------|---------|----------|
| 9700–9709 | Domain controllers | seo: 9700 |
| 9710–9749 | Work agents | seo-analyzer: 9710, a11y-checker: 9711, security-scanner: 9712, content-analyzer: 9720, meta-checker: 9721, uptime-checker: 9730, perf-auditor: 9731 |
| 9750–9799 | Infrastructure agents | cron: 9750, sync: 9751, alerting: 9752, webhook: 9753, email-send: 9754, health-monitor: 9755, incident-response: 9760, hub: 9770, workflow: 9780, task: 9781, lifecycle: 9782 |
| 9800 | Orchestrator | orchestrator: 9800 |
| 9820+ | Custom agents | hash(name) % 80 + 9820 |

## Addressing and Discovery

The manifest `url` field is the **sole source of truth** for reaching
an agent. Port conventions exist only for human convenience during
local development. In all deployment modes, agents:

1. Register with the orchestrator providing their `url`
2. Receive the service directory containing every other agent's `url`
3. Use the service directory to reach peers — never hardcoded ports

This means the protocol works identically whether agents run as local
processes, containers, or serverless functions.

### Deployment Modes

| Mode | Agent Address | Notes |
|------|--------------|-------|
| **Local processes** | `http://localhost:<port>` | Default dev experience. Advisory ports apply. |
| **Containers** | `http://<container-name>:<port>` | Docker/K8s DNS. Agents use service names, not IPs. |
| **Serverless / Functions** | `https://<function-url>` | Each agent is a separate function (e.g., AWS Lambda, Cloudflare Worker). URL assigned by platform. |
| **Reverse proxy** | `https://hub.example.com/agents/<name>` | All agents behind one domain. Proxy routes by path prefix to the correct process. |
| **Mixed** | Any combination | The orchestrator doesn't care — it stores whatever URL the agent provides. |

### Dynamic Registration

For serverless and auto-scaling environments where agent URLs are
not known in advance:

1. The platform assigns the agent a URL at startup.
2. The agent reads its own URL from the platform environment
   (e.g., `WL_AGENT_URL` or platform-specific variable).
3. The agent registers with the orchestrator using that URL.
4. The orchestrator distributes the updated service directory to all
   agents via POST /v1/services.
5. If the URL changes (redeploy, scale event), the agent re-registers.
   The orchestrator updates the directory and pushes to all agents.

```bash
# Environment-driven addressing
WL_AGENT_URL=https://my-agent.us-east-1.lambda.amazonaws.com
WL_ORCHESTRATOR_URL=https://hub.example.com:9800
```

### Cold Start and Warm-Up

Serverless agents face cold start latency. The protocol accommodates
this:

- **Health checks** — the orchestrator SHOULD configure longer health
  check timeouts for serverless agents (30s vs 5s default).
- **Keep-warm** — the [cron agent](../agents/cron.md) MAY be configured
  to ping serverless agents on a schedule to prevent cold eviction.
- **Timeout tolerance** — the Task Agent SHOULD use the agent's
  declared `timeout` from its manifest rather than a global default.
  Serverless agents MAY declare longer timeouts.

### Service Mesh / Sidecar

Agents behind a service mesh (Istio, Linkerd, etc.) register their
mesh-accessible URL. The mesh handles mTLS, load balancing, and
retries transparently. The Weblisk protocol doesn't need to know —
it just sends HTTP to the registered URL.

## Concurrency and Backpressure

Agents MUST protect themselves from overload. The orchestrator and
domain controllers MUST respect agent capacity limits.

### Agent-Side Limits

Every agent SHOULD enforce a maximum number of concurrent executions.
Defaults:

| Agent Kind | Default Max Concurrent | Configurable Via |
|------------|----------------------|------------------|
| Domain controller | 10 | `WL_MAX_CONCURRENT` env var |
| Work agent | 5 | `WL_MAX_CONCURRENT` env var |
| Infrastructure agent | 20 | `WL_MAX_CONCURRENT` env var |

When at capacity, agents MUST return `429 Too Many Requests` with
a structured error:

```json
{
  "error": "agent at capacity — 5 concurrent tasks running",
  "code": "RATE_LIMITED",
  "category": "transient",
  "retryable": true
}
```

The response SHOULD include a `Retry-After` header (seconds):
```
HTTP/1.1 429 Too Many Requests
Retry-After: 5
Content-Type: application/json
```

### Manifest Capacity Declaration

Agents MAY declare their concurrency limit in the manifest so callers
can make informed scheduling decisions:

```json
{
  "name": "seo-analyzer",
  "max_concurrent": 5,
  ...
}
```

This is advisory — callers SHOULD respect it but MUST also handle 429.

### Domain-Side Scheduling

Domain controllers dispatch phases concurrently within a dependency
level. When dispatching, domains MUST:

1. Check the target agent's declared `max_concurrent` (from manifest)
2. Track how many in-flight requests exist per agent
3. If at limit, queue the phase and dispatch when a slot frees
4. If 429 received, apply exponential backoff: 1s, 2s, 4s, 8s (max 30s)
5. After 3 consecutive 429s for the same agent, degrade gracefully:
   serialize remaining phases for that agent instead of parallel dispatch

### Orchestrator-Side Protection

The orchestrator SHOULD enforce:

1. **Per-agent task rate**: Max 60 tasks/minute per target agent (configurable)
2. **Global task rate**: Max 200 tasks/minute total (configurable)
3. **Request body limits** (already specified in spec.md):
   - Registration: 1 MB
   - Task execution: 10 MB
   - Messages: 1 MB
   - Channel requests: 64 KB

When the orchestrator rate-limits a request, it returns 429 with
`Retry-After`.

## Default Timeouts and Resilience

All agents inherit retry behavior from
[`patterns/retry`](../patterns/retry.md), which is the authoritative
source for backoff algorithms, circuit breaker logic, and error
classification. The table below lists agent-level defaults that feed
into the retry pattern:

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| Task timeout | 30s | `WL_TASK_TIMEOUT` | Max execution time per task |
| HTTP outbound timeout | 10s | `WL_HTTP_TIMEOUT` | Per-request timeout for outbound calls |
| Retry attempts | 3 | `WL_RETRY_MAX` | Max retries on transient failure |
| Backoff base | 1s | `WL_BACKOFF_BASE` | Exponential backoff: base × 2^attempt |
| Backoff max | 30s | `WL_BACKOFF_MAX` | Cap on backoff delay |
| Outbound rate limit | 50 req/s | `WL_OUTBOUND_RATE` | Max outbound HTTP requests per second |

Agents that make outbound HTTP calls (security-scanner, uptime-checker,
perf-auditor, etc.) MUST respect the outbound rate limit to avoid
overwhelming targets. Agents performing LLM calls inherit timeout and
retry settings from the api-ai pattern configuration.

## Implementation Notes

- The agent framework is the foundation layer — every running process in Weblisk is an agent
- Registration is mandatory before any work can be done; unregistered agents receive no tasks
- The Ed25519 key pair is generated once at first startup and persisted for the agent's lifetime
- Service directory caching avoids repeated calls to the orchestrator for agent-to-agent communication
- Backpressure via concurrent task limiting prevents overload; rejected tasks return 429 to the orchestrator
- Health checks should complete within the configured timeout; slow health responses degrade system-wide visibility

---

## Verification Checklist

- [ ] POST /v1/describe returns the agent manifest as JSON without requiring authentication
- [ ] POST /v1/execute parses TaskRequest, calls Execute, and returns a signed TaskResult with task_id, agent_name, and timestamp
- [ ] POST /v1/execute returns status=failed with the error summary when Execute returns an error
- [ ] POST /v1/health returns the health response per patterns/observability
- [ ] POST /v1/message verifies the sender's Ed25519 signature when present and returns 401 on invalid signature
- [ ] POST /v1/message builds a signed response with from=self, to=original sender, type=response
- [ ] POST /v1/services updates the internal service list, routing table, and namespace map (thread-safe)
- [ ] POST /v1/event checks idempotency (event_id), dispatches to matching handlers, returns 200 immediately
- [ ] POST /v1/event skips duplicate events (same event_id) with 200 OK
- [ ] Event handlers registered via on_event(pattern, handler) with topic matching (exact, *, #)
- [ ] Framework resolves subscribers from local routing table when publishing (no orchestrator call)
- [ ] Manifest declares publishes and subscriptions for namespace ownership and event routing
- [ ] Registration flow signs the manifest JSON with the agent's Ed25519 private key and includes a timestamp
- [ ] Agent returns 429 Too Many Requests with Retry-After header and retryable error body when at max concurrent capacity
- [ ] Default max concurrent limits are enforced: domain=10, work=5, infrastructure=20 (configurable via WL_MAX_CONCURRENT)
- [ ] Outbound HTTP calls respect the WL_OUTBOUND_RATE limit (default 50 req/s)
- [ ] Agent startup sequence generates Ed25519 keys, registers HTTP routes (6 endpoints), starts server, and registers with orchestrator
