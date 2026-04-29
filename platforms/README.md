# Platform Bindings

Platform blueprints provide implementation guidance for specific runtime
environments. Each platform binding translates the abstract framework
specifications (agents, domains, protocols) into concrete guidance for
a target language and runtime — dependencies, project structure, code
patterns, and deployment considerations.

Blueprints are implementation-agnostic. Platforms make them concrete.

## Platform Blueprints

| Platform | Runtime | Key Characteristics |
|----------|---------|---------------------|
| [go.md](go.md) | Go (stdlib only) | Single binary, local processes, SQLite embedded |
| [cloudflare.md](cloudflare.md) | Cloudflare Workers | Durable Objects, KV, Web Crypto, edge-native |
| [node.md](node.md) | Node.js / TypeScript | Fastify, better-sqlite3, Ed25519, flexible |
| [rust.md](rust.md) | Rust | tokio, hyper, serde, rusqlite, static binary |

## Zero-Dependency Principle

Each platform follows the framework's zero-external-dependency
philosophy within its ecosystem:

- **Go** — Standard library only. SQLite compiles into the binary.
- **Cloudflare** — Platform-native APIs only (Workers KV, Durable Objects, Web Crypto).
- **Node.js** — Recommended libraries (Fastify, better-sqlite3) are choices, not requirements.
- **Rust** — Minimal curated crates (tokio, hyper, serde, rusqlite). Single static binary.

## How Platforms Are Used

The CLI uses platform bindings during code generation:

```bash
weblisk server init --platform go
weblisk agent create my-agent --platform cloudflare
```

The platform blueprint tells the LLM which language features, libraries,
and project structure to use when generating code from agent/domain specs.

## Schema

Platform blueprints conform to [schemas/platform.md](../schemas/platform.md).
