<!-- blueprint
type: platform
name: cloudflare
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/agent, architecture/orchestrator]
platform: cloudflare
-->

# Platform: Cloudflare Workers Implementation

Guidance for generating Weblisk orchestrator and agent implementations
as Cloudflare Workers. This enables edge deployment with global
distribution and zero cold starts.

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
