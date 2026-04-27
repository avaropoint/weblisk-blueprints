<!-- blueprint
type: platform
name: node
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway, patterns/deployment]
platform: node
tier: free
-->

# Node.js Platform Guide

Implementation guidance for building Weblisk servers, domain
controllers, and agents in Node.js. Covers project structure,
HTTP server setup, protocol implementation, agent lifecycle, and
Node.js-specific patterns.

## Overview

While the reference implementation is in Go (stdlib only, zero
external dependencies), Node.js is a natural fit for Weblisk —
particularly for teams already working in the JavaScript/TypeScript
ecosystem. Node's async I/O model aligns well with the agent
architecture's HTTP-based communication.

Weblisk blueprints are implementation-agnostic — they specify WHAT,
not HOW. This guide recommends specific Node.js libraries that
implement the blueprint contracts well, but these are **choices,
not requirements**. Any library that satisfies the protocol and
architecture contracts is valid. Teams may use Express instead of
Fastify, node:crypto instead of @noble/ed25519, or any SQLite
binding — as long as the contracts are met.

The only true requirement is the Node.js runtime itself (v20+) and
the weblisk-cli for project scaffolding and blueprint code
generation.

This guide assumes TypeScript. Plain JavaScript works the same way
minus the type annotations.

## Project Structure

```
weblisk-app/
├── package.json
├── tsconfig.json
├── weblisk.yaml              # Blueprint configuration
├── src/
│   ├── server.ts             # Entry point — starts orchestrator
│   ├── orchestrator/
│   │   ├── index.ts          # Orchestrator setup and routes
│   │   ├── router.ts         # Task routing logic
│   │   ├── registry.ts       # Agent registry
│   │   └── admin.ts          # Admin API endpoints
│   ├── domains/
│   │   ├── seo/
│   │   │   ├── index.ts      # Domain controller
│   │   │   └── workflows.ts  # Workflow definitions
│   │   └── content/
│   │       ├── index.ts
│   │       └── workflows.ts
│   ├── agents/
│   │   ├── seo-analyzer/
│   │   │   ├── index.ts      # Agent entry point
│   │   │   ├── handler.ts    # Task action handlers
│   │   │   └── analyze.ts    # Analysis logic
│   │   └── content-analyzer/
│   │       ├── index.ts
│   │       ├── handler.ts
│   │       └── analyze.ts
│   ├── protocol/
│   │   ├── types.ts          # Shared type definitions
│   │   ├── identity.ts       # Ed25519 identity management
│   │   ├── token.ts          # WLT token create/verify
│   │   └── endpoints.ts      # Standard endpoint handlers
│   ├── storage/
│   │   ├── interface.ts      # Storage interface definition
│   │   └── sqlite.ts         # SQLite implementation
│   └── lib/
│       ├── logger.ts         # Structured logging
│       └── config.ts         # Configuration loader
├── agents/                   # Agent blueprint YAML files
│   ├── seo-analyzer.yaml
│   └── content-analyzer.yaml
├── migrations/
│   └── 001_initial.sql
└── tests/
    ├── unit/
    └── integration/
```

## Dependencies

### Blueprint Dependencies

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

### Recommended Packages

These are the libraries used in this guide's examples. They are
**recommendations, not requirements**. Any library that satisfies
the same contract is a valid substitute. The weblisk-cli generates
projects with these defaults, but teams can swap them.

| Package | Purpose | Why | Alternatives |
|---------|---------|-----|-------------|
| `fastify` | HTTP server | Fast, schema validation built-in, plugin ecosystem | Express, Koa, Hono, node:http |
| `@noble/ed25519` | Ed25519 cryptography | Pure JS, audited, no native deps | node:crypto (Ed25519 in Node 20+), tweetnacl |
| `better-sqlite3` | SQLite storage | Synchronous API, fast, reliable | sql.js, node:sqlite (experimental), any DB driver |
| `pino` | Structured logging | JSON output, fast, Fastify-native | winston, console.log with JSON.stringify |
| `zod` | Schema validation | Runtime type checking for payloads | ajv, joi, io-ts, manual validation |
| `sharp` | Image processing | High-performance, libvips-based | jimp (pure JS), @squoosh/lib |
| `undici` | HTTP client | Node.js native, connection pooling | node:http, axios, got |

### package.json

```json
{
  "name": "weblisk-app",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "tsx watch src/server.ts",
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "fastify": "^4.28.0",
    "@noble/ed25519": "^2.1.0",
    "better-sqlite3": "^11.0.0",
    "pino": "^9.0.0",
    "zod": "^3.23.0",
    "undici": "^6.18.0"
  },
  "devDependencies": {
    "typescript": "^5.5.0",
    "tsx": "^4.16.0",
    "vitest": "^2.0.0",
    "@types/better-sqlite3": "^7.6.0",
    "@types/node": "^20.14.0"
  }
}
```

---

## Runtime Requirements

```yaml
runtime:
  language: TypeScript / JavaScript
  version: "Node.js >=20.0.0"
  dependencies:
    required:
      - name: fastify
        version: "^4.28.0"
        purpose: HTTP server with schema validation
      - name: "@noble/ed25519"
        version: "^2.1.0"
        purpose: Ed25519 cryptography (pure JS, audited)
      - name: better-sqlite3
        version: "^11.0.0"
        purpose: SQLite storage with synchronous API
    optional:
      - name: sharp
        version: "^0.33.0"
        purpose: High-performance image processing
      - name: undici
        version: "^6.18.0"
        purpose: HTTP client with connection pooling
  build_tools:
    - name: typescript
      version: "^5.5.0"
      purpose: TypeScript compiler
    - name: tsx
      version: "^4.16.0"
      purpose: TypeScript execution for development (watch mode)
    - name: vitest
      version: "^2.0.0"
      purpose: Test framework
```

---

## Build and Run

### Build

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run build
```

### Run

```bash
# Development (with watch mode)
npm run dev

# Production
npm start
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WL_PORT` | no | `9800` | Listen port |
| `WL_AGENT_PORT` | no | `9710` | Agent listen port |
| `WL_AI_PROVIDER` | yes | — | LLM provider |
| `WL_AI_MODEL` | yes | — | Model name |
| `WL_LOG_LEVEL` | no | `info` | Log level (`debug`, `info`, `warn`, `error`) |
| `WL_LOG_FORMAT` | no | `json` | Log format (`json`, `text`) |
| `WL_COMPONENT` | no | `unknown` | Component name for logging |

---

## Protocol Implementation

### Types (src/protocol/types.ts)

```typescript
export interface AgentManifest {
  name: string;
  version: string;
  capabilities: string[];
  actions: string[];
}

export interface TaskRequest {
  task_id: string;
  action: string;
  payload: Record<string, unknown>;
  trace_id?: string;
}

export interface TaskResult {
  task_id: string;
  status: "completed" | "failed";
  output?: Record<string, unknown>;
  error?: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  component: string;
  version: string;
  uptime_seconds: number;
}

export interface Observation {
  type: "observation";
  domain: string;
  source: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export interface Recommendation {
  type: "recommendation";
  domain: string;
  source: string;
  data: {
    action: string;
    target: string;
    current: unknown;
    proposed: unknown;
    reason: string;
    impact_estimate: number;
  };
  timestamp: number;
}
```

### Identity (src/protocol/identity.ts)

```typescript
import * as ed from "@noble/ed25519";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { randomBytes } from "node:crypto";

export interface Identity {
  privateKey: Uint8Array;
  publicKey: Uint8Array;
  keyId: string;
}

export async function generateIdentity(
  keyDir: string
): Promise<Identity> {
  mkdirSync(keyDir, { recursive: true, mode: 0o700 });
  const privateKey = ed.utils.randomPrivateKey();
  const publicKey = await ed.getPublicKeyAsync(privateKey);
  const keyId = Buffer.from(publicKey.slice(0, 16)).toString("hex");

  writeFileSync(join(keyDir, "private.key"), privateKey, {
    mode: 0o600,
  });
  writeFileSync(join(keyDir, "public.key"), publicKey, {
    mode: 0o644,
  });

  return { privateKey, publicKey, keyId };
}

export async function loadIdentity(keyDir: string): Promise<Identity> {
  const privateKey = new Uint8Array(
    readFileSync(join(keyDir, "private.key"))
  );
  const publicKey = await ed.getPublicKeyAsync(privateKey);
  const keyId = Buffer.from(publicKey.slice(0, 16)).toString("hex");
  return { privateKey, publicKey, keyId };
}

export async function sign(
  data: Uint8Array,
  privateKey: Uint8Array
): Promise<Uint8Array> {
  return ed.signAsync(data, privateKey);
}

export async function verify(
  signature: Uint8Array,
  data: Uint8Array,
  publicKey: Uint8Array
): Promise<boolean> {
  return ed.verifyAsync(signature, data, publicKey);
}
```

### Standard Endpoints (src/protocol/endpoints.ts)

```typescript
import type { FastifyInstance } from "fastify";
import type { AgentManifest, HealthResponse, TaskRequest } from "./types.js";

interface EndpointConfig {
  manifest: AgentManifest;
  startTime: number;
  onTask: (req: TaskRequest) => Promise<Record<string, unknown>>;
  onMessage?: (msg: Record<string, unknown>) => Promise<void>;
}

export function registerEndpoints(
  app: FastifyInstance,
  config: EndpointConfig
) {
  const { manifest, startTime, onTask, onMessage } = config;

  // Health
  app.post("/health", async () => {
    const uptime = Math.floor((Date.now() - startTime) / 1000);
    const response: HealthResponse = {
      status: "healthy",
      component: manifest.name,
      version: manifest.version,
      uptime_seconds: uptime,
    };
    return response;
  });

  // Describe
  app.post("/describe", async () => {
    return { manifest };
  });

  // Task
  app.post<{ Body: TaskRequest }>("/task", async (request, reply) => {
    const task = request.body;
    try {
      const output = await onTask(task);
      return {
        task_id: task.task_id,
        status: "completed",
        output,
      };
    } catch (err) {
      reply.status(500);
      return {
        task_id: task.task_id,
        status: "failed",
        error: err instanceof Error ? err.message : "Unknown error",
      };
    }
  });

  // Message
  app.post("/message", async (request) => {
    if (onMessage) {
      await onMessage(request.body as Record<string, unknown>);
    }
    return { received: true };
  });

  // Governance
  app.post("/governance", async (request) => {
    // Accept and acknowledge governance directives
    return { acknowledged: true };
  });
}
```

---

## Agent Implementation

### Agent Entry Point (src/agents/seo-analyzer/index.ts)

```typescript
import Fastify from "fastify";
import { registerEndpoints } from "../../protocol/endpoints.js";
import { loadIdentity } from "../../protocol/identity.js";
import { handleTask } from "./handler.js";
import { logger } from "../../lib/logger.js";

const PORT = parseInt(process.env.WL_AGENT_PORT || "9710", 10);

async function start() {
  const app = Fastify({ logger });
  const identity = await loadIdentity("./.weblisk/keys/seo-analyzer");
  const startTime = Date.now();

  registerEndpoints(app, {
    manifest: {
      name: "seo-analyzer",
      version: "1.0.0",
      capabilities: ["file:read", "llm:chat"],
      actions: ["analyze", "audit"],
    },
    startTime,
    onTask: handleTask,
  });

  await app.listen({ port: PORT, host: "0.0.0.0" });
  logger.info({ port: PORT, agent: "seo-analyzer" }, "Agent started");
}

start().catch((err) => {
  logger.error(err, "Failed to start agent");
  process.exit(1);
});
```

### Task Handler (src/agents/seo-analyzer/handler.ts)

```typescript
import type { TaskRequest } from "../../protocol/types.js";
import { analyzeSeo } from "./analyze.js";

export async function handleTask(
  task: TaskRequest
): Promise<Record<string, unknown>> {
  switch (task.action) {
    case "analyze":
      return analyzeSeo(task.payload);
    case "audit":
      return analyzeSeo({ ...task.payload, full_audit: true });
    default:
      throw new Error(`Unknown action: ${task.action}`);
  }
}
```

---

## Structured Logging

### Logger Setup (src/lib/logger.ts)

```typescript
import pino from "pino";

export const logger = pino({
  level: process.env.WL_LOG_LEVEL || "info",
  transport:
    process.env.WL_LOG_FORMAT === "text"
      ? { target: "pino-pretty" }
      : undefined,
  base: {
    component: process.env.WL_COMPONENT || "unknown",
    component_type: process.env.WL_COMPONENT_TYPE || "agent",
  },
});
```

### Usage

```typescript
// Info with context
logger.info({ task_id: task.task_id, action: task.action }, "Task started");

// Error with error object
logger.error({ err, task_id: task.task_id }, "Task failed");

// Trace context
logger.info(
  { trace_id: req.headers["x-trace-id"], span_id: newSpanId },
  "Processing request"
);
```

---

## Storage

### SQLite Implementation (src/storage/sqlite.ts)

```typescript
import Database from "better-sqlite3";

export function createStorage(dbPath: string) {
  const db = new Database(dbPath);
  db.pragma("journal_mode = WAL");
  db.pragma("foreign_keys = ON");

  return {
    get<T>(sql: string, ...params: unknown[]): T | undefined {
      return db.prepare(sql).get(...params) as T | undefined;
    },

    all<T>(sql: string, ...params: unknown[]): T[] {
      return db.prepare(sql).all(...params) as T[];
    },

    run(sql: string, ...params: unknown[]) {
      return db.prepare(sql).run(...params);
    },

    transaction<T>(fn: () => T): T {
      return db.transaction(fn)();
    },

    close() {
      db.close();
    },
  };
}
```

---

## Platform-Specific Conventions

### Concurrency

- Node.js uses a single-threaded event loop with async/await for
  concurrent I/O operations
- CPU-intensive tasks should be offloaded to `node:worker_threads`
- No mutex needed — single-threaded execution prevents data races
  within a single event loop tick

### IO Safety

- Validate and limit request body sizes via Fastify schema validation
- Use `undici` Agent with connection pooling for outbound HTTP
- Set appropriate `--max-old-space-size` for memory-constrained environments

### Error Handling

- Use async/await with try/catch — never leave promises unhandled
- Task handlers return structured `{ task_id, status, output | error }`
- Use `process.on('unhandledRejection', ...)` as a safety net

### Logging

- Structured JSON logging via pino with `component` and `component_type` base fields
- Use pino-pretty for development (`WL_LOG_FORMAT=text`)
- Include `trace_id` in all log entries for request correlation

See [Node.js-Specific Considerations](#nodejs-specific-considerations)
for process management, performance, and security details.

---

## Type Mapping

| Schema Type | TypeScript Type | Notes |
|-------------|-----------------|-------|
| `string` | `string` | |
| `int` | `number` | Validate with `Number.isInteger()` |
| `int64` | `number` or `bigint` | Use `number` if within safe integer range |
| `float` | `number` | IEEE 754 double precision |
| `bool` | `boolean` | |
| `object` | `Record<string, unknown>` | Or typed interface |
| `list` | `T[]` | Typed array |
| `uuid` | `string` | Validated with zod or regex |
| `timestamp` | `number` | Unix epoch milliseconds via `Date.now()` |

---

## Security

### Input Validation

- Validate all request payloads with zod schemas — never trust raw `request.body`
- Use Fastify’s built-in schema validation for HTTP layer enforcement
- Enforce maximum body sizes per endpoint type

### Cryptography

- `@noble/ed25519` for Ed25519 operations (pure JS, audited)
- Alternative: `node:crypto` Ed25519 support (Node 20+)
- Private keys stored with file mode `0o600`

### Dependencies

- Pin dependency versions in `package-lock.json` (committed to repo)
- Production Docker uses `npm ci --omit=dev` for minimal installs
- Run `npm audit` regularly for vulnerability scanning

### Runtime Hardening

- Start Node with `--disable-proto=delete` to prevent prototype pollution
- Use `helmet` Fastify plugin for security headers
- Never expose stack traces in production error responses

---

## Testing

### Unit Tests (vitest)

```typescript
import { describe, it, expect } from "vitest";
import { analyzeSeo } from "../src/agents/seo-analyzer/analyze.js";

describe("seo-analyzer", () => {
  it("should detect missing title tag", async () => {
    const result = await analyzeSeo({
      html: "<html><head></head><body></body></html>",
    });

    expect(result.findings).toContainEqual(
      expect.objectContaining({
        type: "missing_title",
        severity: "critical",
      })
    );
  });
});
```

### Integration Tests

```typescript
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import Fastify from "fastify";

describe("agent endpoints", () => {
  let app: ReturnType<typeof Fastify>;

  beforeAll(async () => {
    app = Fastify();
    // Register agent routes...
    await app.listen({ port: 0 });
  });

  afterAll(async () => {
    await app.close();
  });

  it("should respond to health check", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/health",
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().status).toBe("healthy");
  });

  it("should process a task", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/task",
      payload: {
        task_id: "test-001",
        action: "analyze",
        payload: { url: "https://example.com" },
      },
    });
    expect(res.statusCode).toBe(200);
    expect(res.json().status).toBe("completed");
  });
});
```

---

## Node.js-Specific Considerations

### Process Management

- Use `node --enable-source-maps` for readable stack traces in
  production (with source maps from TypeScript)
- Handle SIGTERM for graceful shutdown:

```typescript
process.on("SIGTERM", async () => {
  logger.info("Shutting down gracefully");
  await app.close();
  storage.close();
  process.exit(0);
});
```

### Performance

- **Connection pooling**: Use `undici` Agent with `connections` and
  `pipelining` for outbound HTTP to other agents
- **Worker threads**: For CPU-intensive tasks (image processing, HTML
  parsing), offload to worker threads via `node:worker_threads`
- **Memory**: Monitor `process.memoryUsage()` and set
  `--max-old-space-size` appropriately

### Security

- Use `node --disable-proto=delete` to prevent prototype pollution
- Use `helmet` Fastify plugin for security headers
- Validate all input with `zod` schemas — never trust raw
  `request.body`
- Pin dependency versions in `package-lock.json` (committed to repo)

### vs. Go Implementation

| Aspect | Go | Node.js |
|--------|-----|---------|
| Concurrency | Goroutines | async/await + event loop |
| Binary | Single static binary | Node runtime + source |
| Startup | ~50ms | ~200ms |
| Memory | ~10MB base | ~30MB base |
| npm ecosystem | N/A | Full access |
| Type safety | Compile-time | TypeScript (optional) |
| Image processing | External tools | sharp (libvips) |

Choose Go for lightweight, single-binary deployments. Choose Node.js
for teams with JavaScript expertise and projects that benefit from
the npm ecosystem.

---

## Implementation Notes

- Use ES modules (`"type": "module"` in package.json) — avoid CommonJS
- Use `tsx` for development (watch mode with TypeScript) and compile
  to JavaScript for production
- Fastify's schema validation can enforce the protocol types at the
  HTTP layer — define JSON Schema for each endpoint
- `better-sqlite3` is synchronous but fast — for high-concurrency
  production workloads, consider `libsql` or PostgreSQL with `pg`
- When building Docker images for Node.js, use `node:22-alpine` as
  the runtime base and run `npm ci --omit=dev` for production deps
  only

## Verification Checklist

- [ ] Project uses Node.js 20+ with ES modules (`"type": "module"` in package.json) and TypeScript compiled to JavaScript for production
- [ ] Ed25519 keys are generated and verified via `@noble/ed25519` (or `node:crypto`); private keys stored with mode 0o600
- [ ] SQLite is configured with `pragma journal_mode = WAL` and `pragma foreign_keys = ON`
- [ ] Structured logging uses pino with JSON output in production; log entries include `component` and `component_type` base fields
- [ ] SIGTERM triggers graceful shutdown: Fastify server closes, storage closes, then process exits
- [ ] All request payloads are validated with zod schemas — raw `request.body` is never trusted directly
- [ ] Dependency versions are pinned in `package-lock.json` (committed to repo); production Docker uses `npm ci --omit=dev`
- [ ] Node is started with `--disable-proto=delete` to prevent prototype pollution
- [ ] Agent entry point registers all 6 protocol endpoints (health, describe, execute, message, services, event) via `registerEndpoints`
- [ ] Task handler dispatches by `action` field and returns structured `{ task_id, status, output }` or `{ task_id, status, error }`
- [ ] Integration tests verify health returns 200 with `status: "healthy"` and task endpoint returns `status: "completed"` for valid actions
