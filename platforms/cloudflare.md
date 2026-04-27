<!-- blueprint
type: platform
name: cloudflare
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway, patterns/deployment]
platform: cloudflare
tier: free
-->

# Platform: Cloudflare Workers Implementation

Guidance for generating Weblisk orchestrator and agent implementations
as Cloudflare Workers. This enables edge deployment with global
distribution and zero cold starts.

Cloudflare Workers achieves **zero external dependencies** — all
APIs used (Workers KV, Durable Objects, Web Crypto, R2, etc.) are
native platform capabilities, not third-party packages. The only
`devDependencies` are Cloudflare's own tooling (wrangler) used for
deployment. Runtime dependencies are zero.

## Overview

This blueprint provides implementation guidance for deploying Weblisk
orchestrators and agents as Cloudflare Workers — serverless edge functions
running in V8 isolates across 200+ global locations. The platform maps
all Weblisk protocol contracts to Cloudflare-native APIs, achieving zero
runtime dependencies and global low-latency distribution.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, version, capabilities, actions]
        - name: TaskRequest
          fields_used: [task_id, action, payload]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Identity
          fields_used: [public_key, key_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: HealthResponse
          fields_used: [status, component, version, uptime_seconds]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Project Structure

### Orchestrator
```
server/
  wrangler.toml        # Cloudflare Worker configuration
  src/
    index.js           # Worker entry point — router + handlers
    protocol.js        # Protocol types and validation
    identity.js        # Ed25519 via Web Crypto API (crypto.subtle)
    orchestrator.js    # Registration, routing, channel brokering
  package.json         # No runtime deps — devDependencies only for wrangler
```

### Agent
```
agents/<name>/
  wrangler.toml
  src/
    index.js           # Worker entry point
    protocol.js        # Same protocol types
    identity.js        # Same identity module
    agent.js           # Agent base framework
    <name>.js          # Domain-specific logic
  package.json
```

---

## Runtime Requirements

```yaml
runtime:
  language: JavaScript
  version: "ES2022+ (Cloudflare Workers V8 runtime)"
  dependencies:
    required: []  # Zero runtime dependencies — all APIs are platform-native
    optional: []
  build_tools:
    - name: wrangler
      version: ">=3.0.0"
      purpose: Cloudflare Workers CLI for development, testing, and deployment
    - name: node
      version: ">=18.0.0"
      purpose: Required to run wrangler CLI tooling
```

Cloudflare Workers achieves zero runtime dependencies. All required
APIs (Workers KV, Durable Objects, Web Crypto, R2, D1) are native
platform capabilities. The only tooling dependency is `wrangler`
(a `devDependency`) for local development and deployment.

See [Cloudflare-Specific Requirements](#cloudflare-specific-requirements)
for detailed platform API usage.

---

## Cloudflare-Specific Requirements

### Crypto
- Use Web Crypto API (`crypto.subtle`) for Ed25519
- `crypto.subtle.generateKey("Ed25519", true, ["sign", "verify"])`
- `crypto.subtle.sign("Ed25519", privateKey, data)`
- `crypto.subtle.verify("Ed25519", publicKey, signature, data)`
- Export keys as raw ArrayBuffer, convert to hex for protocol

### State (Orchestrator)
- Use Durable Objects for agent registry (persistent, strongly consistent)
- KV for service directory cache (eventually consistent, fast reads)
- Use Durable Object alarm for channel TTL cleanup

### Request Routing
```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    if (path === '/v1/health') return handleHealth(env);
    if (path === '/v1/register') return handleRegister(request, env);
    // ... auth middleware for remaining routes
  }
}
```

### LLM Integration
- Use Cloudflare Workers AI binding for built-in models
- Or use fetch() to external APIs (OpenAI, Anthropic)
- Configure via environment variables in wrangler.toml [vars]

### wrangler.toml
```toml
name = "weblisk-orchestrator"
main = "src/index.js"
compatibility_date = "2026-01-01"

[durable_objects]
bindings = [
  { name = "REGISTRY", class_name = "AgentRegistry" }
]

[[migrations]]
tag = "v1"
new_classes = ["AgentRegistry"]

[vars]
WL_VERSION = "1.0.0"
```

### Key Storage
- Private keys stored in Cloudflare Workers Secrets
- `wrangler secret put ORCHESTRATOR_PRIVATE_KEY`
- Or generate on first Durable Object creation and store internally

---

## Build and Run

### Build

```bash
# No build step required for plain JavaScript Workers
# For TypeScript projects:
npx tsc
```

### Run

```bash
# Local development
cd server && wrangler dev

# Local development for agent
cd agents/<name> && wrangler dev
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WL_VERSION` | no | `1.0.0` | Protocol version |
| `WL_AI_KEY` | yes | — | API key for LLM provider |
| `WL_AI_PROVIDER` | no | `workers-ai` | LLM provider (`workers-ai`, `openai`, `anthropic`) |

See [Deployment](#deployment) for production deployment commands
and secret management.

---

## Deployment

```bash
# Install wrangler CLI
npm install -g wrangler

# Deploy orchestrator
cd server && wrangler deploy

# Deploy agent
cd agents/seo && wrangler deploy

# Set secrets
wrangler secret put WL_AI_KEY
```

## Differences from Local Go

| Aspect | Go (local) | Cloudflare |
|--------|-----------|------------|
| Runtime | Go binary | V8 isolate |
| State | In-memory maps | Durable Objects + KV |
| Crypto | crypto/ed25519 | crypto.subtle (Web Crypto) |
| HTTP | net/http | fetch API |
| Persistence | Memory (lost on restart) | Durable Objects (persisted) |
| Deployment | Local process | Edge (200+ locations) |
| LLM | External API calls | Workers AI or external |
| Concurrency | Goroutines + RWMutex | Single-threaded per request |

---

## Platform-Specific Conventions

### Concurrency

Cloudflare Workers are single-threaded per request. Concurrency
coordination uses Durable Objects as the single-writer synchronization
point. See [Concurrency (Cloudflare-Specific)](#concurrency-cloudflare-specific)
for the `acquireSlot`/`releaseSlot` pattern.

### IO Safety

- Request body size is limited by Cloudflare Workers runtime (128 MB paid plans)
- Use `request.json()` or `request.text()` — no raw stream parsing needed
- Subrequest limits: 50 per invocation (free), 1000 (paid)

### Error Handling

- Return `Response` objects with appropriate status codes and JSON error bodies
- Use try/catch around all async operations — never throw unhandled exceptions
- Durable Object methods must handle storage errors gracefully

### Logging

- Use `console.log()` with JSON-structured output — visible via `wrangler tail`
- Include `component`, `trace_id`, and `timestamp` in log entries
- Use Cloudflare Logpush for production log retention

---

## Project Structure: Domain Controller

```
domains/<name>/
  wrangler.toml
  src/
    index.js           # Worker entry point
    protocol.js        # Same protocol types
    identity.js        # Same identity module
    agent.js           # Agent base framework
    domain.js          # Workflow engine + dispatch logic
    workflows.js       # Workflow definitions
    <name>.js          # Domain-specific aggregation and actions
  package.json
```

## Storage Mapping (Cloudflare)

See [architecture/storage.md](../architecture/storage.md) for the
abstract storage interface.

| Store | Backend | Notes |
|-------|---------|-------|
| Agent Registry | Durable Object | Strongly consistent, single-writer |
| Strategies | Durable Object | Under same `OrchestratorState` DO |
| Observations | D1 (SQL) or KV | KV for simple append; D1 for queries |
| Recommendations | Durable Object | Needs status transitions |
| Feedback | D1 or KV | Append-only |
| Agent Metrics | Durable Object | Incremental updates |
| Audit Log | D1 | Queryable, retained 90 days |
| Entity Context | KV | Single record, fast reads |
| Channels | Durable Object | With alarm for TTL cleanup |
| Workflow Executions | D1 | Domain-scoped |

### Durable Object: OrchestratorState
Primary Durable Object that holds agent registry, recommendations,
strategies, and channels. Single-writer guarantees consistency.

```javascript
export class OrchestratorState {
  constructor(state, env) {
    this.state = state;
    this.storage = state.storage;
  }
  
  async fetch(request) {
    // Route to internal handlers based on path
  }
}
```

### D1 for Queryable Data
Observations, audit logs, and workflow executions benefit from SQL
queries (filter by agent, time range, strategy). Use D1 tables:

```toml
[[d1_databases]]
binding = "DB"
database_name = "weblisk"
database_id = "<your-d1-id>"
```

### KV for Fast Reads
Entity context and service directory cache use KV for fast edge reads:

```toml
[[kv_namespaces]]
binding = "CACHE"
id = "<your-kv-id>"
```

## Concurrency (Cloudflare-Specific)

Cloudflare Workers are single-threaded per request but handle
concurrent requests via the runtime. Concurrency limiting uses
the Durable Object as a coordination point:

```javascript
// In OrchestratorState Durable Object
async acquireSlot(agentName, maxConcurrent) {
  const key = `slots:${agentName}`;
  const current = (await this.storage.get(key)) || 0;
  if (current >= maxConcurrent) return false;
  await this.storage.put(key, current + 1);
  return true;
}

async releaseSlot(agentName) {
  const key = `slots:${agentName}`;
  const current = (await this.storage.get(key)) || 1;
  await this.storage.put(key, Math.max(0, current - 1));
}
```

Domain controllers running as Workers dispatch phases using
`Promise.all()` for parallel execution within a dependency level.

---

## Type Mapping

| Schema Type | JavaScript Type | Notes |
|-------------|-----------------|-------|
| `string` | `string` | |
| `int` | `number` | Validate with `Number.isInteger()` |
| `int64` | `number` or `bigint` | Use `number` if within safe integer range |
| `float` | `number` | IEEE 754 double precision |
| `bool` | `boolean` | |
| `object` | `object` | `Record<string, unknown>` |
| `list` | `Array<T>` | Typed arrays |
| `uuid` | `string` | Validated with regex |
| `timestamp` | `number` | Unix epoch milliseconds via `Date.now()` |

---

## Security

### Input Validation

- Validate all incoming JSON payloads before processing
- Reject requests with unexpected fields or invalid types
- Enforce maximum payload sizes at the application level for sensitive endpoints

### Cryptography

- Use Web Crypto API (`crypto.subtle`) exclusively — no external crypto libraries
- Ed25519 for identity and signing (native in Workers runtime)
- Use `crypto.getRandomValues()` for secure random generation

### Dependencies

- Zero runtime dependencies eliminates supply chain risk
- `wrangler` is the sole `devDependency` — audit with `npm audit`
- Pin `wrangler` version in `package.json` to avoid unexpected updates

### Secrets Management

- Store private keys and API keys via `wrangler secret put`
- Never place secrets in `wrangler.toml`, source code, or environment variables
- Use Workers Secrets for all sensitive configuration

---

## Testing

### Local Testing

```bash
# Run local dev server
wrangler dev

# Test endpoints
curl -X POST http://localhost:8787/v1/health
```

### Unit Testing

Use `vitest` with `miniflare` for Workers-compatible testing:

```javascript
import { describe, it, expect } from "vitest";

describe("health endpoint", () => {
  it("returns healthy status", async () => {
    const response = await fetch("http://localhost:8787/v1/health", {
      method: "POST",
    });
    const data = await response.json();
    expect(data.status).toBe("healthy");
  });
});
```

### Integration Testing

- Test Durable Object state transitions in isolation
- Verify D1 queries return expected results
- Test full request flows through Worker → Durable Object → KV/D1

---

## Implementation Notes

- Workers execute in V8 isolates — no Node.js APIs available (no `fs`, `path`, `process`)
- Use `export default { fetch }` handler pattern for Worker entry points
- Durable Objects provide single-writer semantics — ideal for agent registry consistency
- D1 is SQLite-compatible — use the same schema patterns as the Go/SQLite implementation
- KV is eventually consistent with a global replication delay of ~60 seconds
- Use `Promise.all()` for parallel subrequests within a single Worker invocation
- Alarm API in Durable Objects handles scheduled cleanup (channel TTL, expired tokens)
- Workers have a 30-second CPU time limit (paid plan) — split long-running tasks

---

## Verification Checklist

- [ ] Ed25519 operations use Web Crypto API (`crypto.subtle.generateKey`, `sign`, `verify`); keys exported as raw ArrayBuffer and hex-encoded for protocol
- [ ] Agent registry is stored in a Durable Object for strong consistency; KV is used for the service directory cache (eventually consistent)
- [ ] Durable Object alarm handles channel TTL cleanup
- [ ] Queryable data (observations, audit logs, workflow executions) is stored in D1; entity context uses KV for fast edge reads
- [ ] Zero runtime dependencies — only `devDependencies` (wrangler) exist in package.json
- [ ] Private keys are stored via `wrangler secret put`, not in wrangler.toml or source code
- [ ] Worker entry point routes requests by URL pathname with auth middleware applied to protected routes
- [ ] Concurrency limiting is coordinated through the Durable Object (`acquireSlot`/`releaseSlot` pattern) respecting agent `max_concurrent`
- [ ] Domain controllers dispatch parallel workflow phases using `Promise.all()` for independent phases within a dependency level
- [ ] wrangler.toml declares Durable Object bindings, D1 database bindings, and KV namespace bindings as required by the storage mapping
