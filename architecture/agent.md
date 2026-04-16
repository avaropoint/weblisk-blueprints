<!-- blueprint
type: architecture
name: agent
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types]
platform: any
-->

# Weblisk Agent Blueprint

The universal blueprint every agent is built on. Every agent — regardless
of language or platform — follows this structure. The agent handles
protocol endpoints, registration, and messaging. The developer implements
only the custom logic (Execute + HandleMessage).

## Architecture

```
┌─────────────────────────────────────────┐
│  Agent Process                          │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  Agent Framework (base)          │   │
│  │  - HTTP server (5 endpoints)     │   │
│  │  - Registration with orchestrator│   │
│  │  - Service directory tracking    │   │
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
7. Register HTTP routes for all 5 protocol endpoints
8. Start HTTP server in background
9. Wait briefly for server to accept connections
10. Register with orchestrator (if orchestrator URL provided)
11. Block indefinitely (agent is a long-running process)
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

### GET /v1/health
Return HealthStatus with:
- name: agent name
- status: "healthy"
- version: agent version
- uptime: seconds since start
- metrics: {services_known: count}

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
4. Return 200 OK
```

## Service Discovery

The agent maintains an in-memory list of available services, updated:
1. On registration (from RegisterResponse.services)
2. On service directory pushes (from orchestrator POST /v1/services)
3. On task execution (from TaskRequest.context.services)

Helper: `HasService(name) → (ServiceEntry, bool)` — look up an agent by name.

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
  "approval": "required|auto"
}
```

### Standard Capabilities

See [types.md — Capability](../protocol/types.md) for the canonical
list of standard capabilities and their descriptions.

## Agent Kinds

The `type` field in the manifest distinguishes three kinds of agents:

| Kind | Manifest Type | Purpose | Dispatched By |
|------|--------------|---------|---------------|
| Domain controller | `"domain"` | Directs a business function, owns workflows | Orchestrator |
| Work agent | `"agent"` | Performs specific tasks | Domain controller |
| Infrastructure agent | `"infrastructure"` | System-level utilities | Any authenticated agent |

See [Domain Architecture](domain.md) for the full domain controller spec.

**Domain controllers** register with the orchestrator and declare
`required_agents` and `workflows`. They receive business-level tasks
and decompose them into multi-agent workflows.

**Work agents** perform the actual work. They are dispatched by domain
controllers via `POST /v1/message`. They register with the orchestrator
but business tasks should route through their owning domain.

**Infrastructure agents** (sync, cron, webhook, email) provide
reusable platform services. Any authenticated agent or domain can
message them directly.

## Port Assignment Convention

| Range | Purpose | Examples |
|-------|---------|----------|
| 9700–9709 | Domain controllers | seo: 9700 |
| 9710–9749 | Work agents | seo-analyzer: 9710, a11y-checker: 9711 |
| 9750–9799 | Infrastructure agents | sync: 9750, cron: 9751, webhook: 9752, email: 9753 |
| 9800 | Orchestrator | orchestrator: 9800 |
| 9820+ | Custom agents | hash(name) % 80 + 9820 |

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
