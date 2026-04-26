<!-- blueprint
type: platform
name: cloudflare
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway]
platform: cloudflare
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
