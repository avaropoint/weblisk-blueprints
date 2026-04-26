<!-- blueprint
type: pattern
name: interop
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent]
platform: any
tier: free
-->

# Interop Adapter Pattern

Wrap external agent frameworks (LangChain, CrewAI, AutoGen, custom
HTTP services) as Weblisk-compliant agents. The adapter handles
protocol translation — the external framework runs unmodified inside.

## Overview

Weblisk is framework-agnostic. Any process that implements the
6-endpoint agent protocol can participate in a hub. But existing
agent code built with LangChain, CrewAI, Google ADK, or plain HTTP
services shouldn't need rewriting. An interop adapter bridges the gap:

```
┌──────────────────────────────────┐
│  Weblisk Agent Shell             │
│  ┌────────────────────────────┐  │
│  │  Adapter Layer             │  │
│  │  - Protocol endpoints      │  │
│  │  - Manifest generation     │  │
│  │  - Auth / signing          │  │
│  │  - Event translation       │  │
│  ├────────────────────────────┤  │
│  │  External Framework        │  │
│  │  (LangChain / CrewAI /     │  │
│  │   ADK / custom HTTP / etc) │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

The adapter is a thin wrapper — it does NOT re-implement the external
framework's logic. It translates between Weblisk protocol calls and
the framework's native interface.

## Adapter Contract

Every adapter MUST:

1. **Expose all 6 protocol endpoints** — `/v1/describe`, `/v1/execute`,
   `/v1/health`, `/v1/message`, `/v1/services`, `/v1/event`
2. **Register with the orchestrator** — providing a valid manifest
   with Ed25519 keys
3. **Sign all outbound messages** — using the agent's Ed25519 keypair
4. **Translate TaskRequest → framework input** and
   **framework output → TaskResult**
5. **Report health** — the adapter wraps the framework's health status
   into the standard health response format

Adapters MUST NOT:

- Expose the external framework's native API alongside Weblisk endpoints
- Allow unauthenticated access to the wrapped framework
- Bypass Ed25519 signing for "convenience"

## Translation Map

### TaskRequest → Framework Input

| Weblisk Field | LangChain | CrewAI | ADK | HTTP Service |
|---------------|-----------|--------|-----|-------------|
| `task.action` | Tool name or chain name | Task description | Function name | HTTP method + path |
| `task.payload` | Chain input dict | Task context | Function args | Request body |
| `task.target` | N/A (ignored) | Agent role hint | N/A | URL path segment |
| `context.services` | Available tools | Available agents | Available tools | N/A |

### Framework Output → TaskResult

| Framework Output | Weblisk Field |
|-----------------|---------------|
| Chain result / agent response | `result.summary` |
| Structured output | `result.data` |
| Error / exception | `result.status = "failed"`, `result.error` |
| Token usage | `result.metrics.tokens_used` |
| Execution time | `result.metrics.duration_ms` |

## Adapter Types

### Type 1: In-Process Adapter

The adapter and framework run in the same process. The adapter imports
the framework as a library and calls it directly.

```
Weblisk HTTP → Adapter → framework.invoke(input) → TaskResult
```

**Best for:** Python frameworks (LangChain, CrewAI, AutoGen) where the
adapter is a Python process that imports the framework.

**Example manifest:**

```json
{
  "name": "langchain-researcher",
  "type": "agent",
  "version": "1.0.0",
  "url": "http://localhost:9830",
  "description": "Research agent powered by LangChain RAG chain",
  "capabilities": [
    {"name": "execute:research", "resources": ["*"]}
  ],
  "adapter": {
    "framework": "langchain",
    "version": "0.3.x",
    "type": "in-process"
  }
}
```

### Type 2: Sidecar Adapter

The adapter runs as a separate process alongside the framework. The
adapter forwards requests to the framework over localhost HTTP.

```
Weblisk HTTP → Adapter (port 9830) → HTTP → Framework (port 8080)
```

**Best for:** Existing HTTP services, containers, or frameworks that
already expose an HTTP API.

**Configuration:**

```bash
# Sidecar adapter configuration
WL_ADAPTER_TYPE=sidecar
WL_ADAPTER_TARGET=http://localhost:8080
WL_ADAPTER_HEALTH_PATH=/health
WL_ADAPTER_EXECUTE_PATH=/invoke
WL_ADAPTER_TIMEOUT=60
```

### Type 3: Subprocess Adapter

The adapter spawns the framework as a child process and communicates
via stdin/stdout (JSON lines).

```
Weblisk HTTP → Adapter → spawn(framework) → stdin/stdout → TaskResult
```

**Best for:** CLI tools, scripts, or frameworks that don't have an
HTTP interface.

## Event Translation

For adapters that need pub/sub participation, the adapter translates
between Weblisk events and the framework's native event model:

| Weblisk Event | Adapter Action |
|---------------|---------------|
| POST /v1/event (inbound) | Call framework's event handler / callback |
| Framework emits event | Adapter publishes via POST /v1/event to subscribers |

If the wrapped framework has no event concept, the adapter simply
drops inbound events (after acknowledging with 202) and never publishes.

## Health Mapping

The adapter combines its own health with the framework's health:

```json
{
  "status": "healthy",
  "adapter": {
    "framework": "langchain",
    "framework_version": "0.3.1",
    "adapter_type": "in-process",
    "framework_healthy": true,
    "translation_errors": 0
  },
  "uptime_seconds": 3600,
  "last_task_at": 1713264000
}
```

If the framework is unhealthy, the adapter MUST report `"degraded"`.
If the framework process has crashed, report `"unhealthy"`.

## Error Handling

| Framework Error | Weblisk Translation |
|----------------|-------------------|
| Exception / crash | TaskResult with `status: "failed"`, `error: "<message>"` |
| Timeout | TaskResult with `status: "failed"`, `error: "framework_timeout"` |
| Invalid input | 400 with `INVALID_REQUEST` error code |
| Rate limited by framework | 429 with `Retry-After` |
| Framework not ready | Health returns `"degraded"` until ready |

The adapter MUST NOT leak framework-internal stack traces in error
responses. Log them internally; return sanitized error messages.

## Configuration

```bash
# Common adapter configuration
WL_ADAPTER_TYPE=in-process|sidecar|subprocess
WL_ADAPTER_FRAMEWORK=langchain|crewai|adk|http|custom

# Sidecar / subprocess specific
WL_ADAPTER_TARGET=http://localhost:8080
WL_ADAPTER_COMMAND=python my_agent.py
WL_ADAPTER_TIMEOUT=60

# Manifest overrides
WL_AGENT_NAME=my-adapted-agent
WL_AGENT_URL=http://localhost:9830
WL_ORCHESTRATOR_URL=http://localhost:9800
```

## Implementation Notes

- **Language mismatch** — if the hub runs Go and the framework is
  Python, use a sidecar adapter. The Go process handles the protocol;
  the Python process runs the framework.
- **State management** — the adapter owns the Weblisk state (manifest,
  keys, service directory). The framework should be stateless from
  the protocol's perspective.
- **Multi-agent frameworks** — CrewAI and AutoGen run multiple agents
  internally. Map the entire crew/group as ONE Weblisk agent. Internal
  agent coordination is the framework's concern. Weblisk sees one
  agent with one manifest.
- **Tool bridging** — if the framework's tools need to call other
  Weblisk agents, the adapter can expose a "weblisk_message" tool
  that sends POST /v1/message to the target agent and returns the
  response as tool output.
- **Hot reload** — adapters SHOULD support reloading the framework
  configuration without restarting the agent process (for sidecar
  and subprocess types, restart only the framework process).

## Verification Checklist

- [ ] Adapter exposes all 6 protocol endpoints
- [ ] Registration with orchestrator succeeds
- [ ] Ed25519 signing works on all outbound messages
- [ ] TaskRequest is correctly translated to framework input
- [ ] Framework output is correctly translated to TaskResult
- [ ] Health endpoint reflects both adapter and framework health
- [ ] Framework errors produce valid Weblisk error responses
- [ ] No framework stack traces leak in error responses
- [ ] Event delivery works (if framework supports events)
- [ ] Adapter handles framework crash gracefully (health → unhealthy)
- [ ] Sidecar mode correctly proxies to target URL
- [ ] Subprocess mode correctly manages child process lifecycle
