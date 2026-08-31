<!-- blueprint
type: platform
name: go
version: 1.0.0
requires: [protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway, patterns/deployment]
platform: go
tier: free
-->

# Platform: Go Implementation

Guidance for generating Weblisk orchestrator and agent implementations
in Go, running as local processes. This is the default platform and
the reference implementation for all Weblisk blueprints.

Go is the ideal fit for Weblisk because it needs **almost nothing beyond
its own standard library** — no framework, no router, no middleware
stack, no logging library, no package manager at runtime, no native
bindings and no external database server. Two modules are required,
each because Go does not ship the primitive the protocol calls for; see
the Primitive Mapping table below. A storage driver is optional and
compiles into the binary — embedded, never an external server.

"Zero external dependencies" was the earlier phrasing, and it was an
overclaim that mattered: it was written as an unconditional acceptance
criterion, and an implementation that correctly reached for a primitive
Go does not have was then reported as violating its own platform's
dependency policy.

## Overview

This blueprint provides the reference implementation for Weblisk in Go.
Go is the default platform — all protocol types, identity management,
and agent lifecycle patterns are designed to compile from the Go standard
library alone. This guide covers project structure, build commands,
concurrency patterns, and storage mapping for both development and
production deployments.

---

## Dependencies

```yaml
requires:
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
        - name: HealthStatus
          fields_used: [status, component, version, uptime_seconds]
        - name: AgentManifest
          fields_used: [name, version, capabilities, actions]
        - name: TaskRequest
          fields_used: [task_id, action, payload]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Project Structure

### One module, one definition of everything

```
<tenant>/
  go.mod                    # module <tenant>; go 1.22
  go.sum
  cmd/
    orchestrator/
      main.go               # entry point — configure and serve
    <component>/
      main.go               # one directory per binary
  internal/
    protocol/               # wire types, error registry — ONE definition
    identity/               # keys, signing, tokens, replay protection
    storage/                # the storage contract and its backends
    observability/          # logging, metrics, tracing
    orchestrator/           # registry, routing, channels, audit, admin
    agent/                  # the agent framework, for components that are agents
  bin/                      # build output, not source
```

Prepare: `go mod tidy`
Build: `go build -o bin/orchestrator ./cmd/orchestrator`
Run: `./bin/orchestrator --port 9800`

The prepare step is not optional and not part of the build. `go.mod` declares the
dependencies; `go.sum` records their checksums, and Go refuses to build without
it. Writing source files cannot produce it — only resolution can. A generator
that emits a correct `go.mod` and a correct identity package and then builds will
fail with "missing go.sum entry", naming a source file that has nothing wrong
with it.

### Why one module, and not a copy per binary

An earlier version of this document specified a module per component with
`package main` throughout, and said of the shared files: *"copy, don't import
(keeps each binary standalone)."*

That rationale does not hold. Go static-links: `go build ./cmd/orchestrator`
produces a single binary with no runtime dependency on anything, whether its
source was imported or copied. **Standalone is a property of the binary, not of
the source layout.** Copying buys nothing it does not already have.

What copying costs is exact:

- **Definitions drift.** The same type exists in N places and nothing makes them
  agree. The wire contract stops being one thing.
- **Impact analysis is defeated.** `architecture/change-management` computes
  impact at binding level, then every component's copy of the protocol file
  changes on any type change — so versioning fires for components that consume
  nothing that moved.
- **Dead code becomes mandatory.** A copied file must serve every component that
  copies it, so it must carry every type any of them needs. A generated
  orchestrator carried task, workflow and observation types it never referenced,
  for exactly this reason, and it was right to: the blueprint told it the file was
  shared by copying.

With one module, `internal/protocol` is defined once and imported. Each binary
links only what it reaches, the compiler removes the rest, and a change to a type
nobody imports touches nobody.

### A component's shape

A component is a directory under `cmd/` and whatever it imports. This document
does not name any component beyond the orchestrator, because none is required:
which agents and domain controllers a deployment has is chosen by adopting their
blueprints, not by this file. An agent's structure comes from
[`architecture/agent`](../architecture/agent.md); this document says only how a
Go binary for one is laid out and built.

---

## Runtime Requirements

```yaml
runtime:
  language: Go
  version: ">=1.22"
  dependencies:
    required:
      - github.com/cloudflare/circl   # signature algorithm; not in the stdlib
      - golang.org/x/crypto           # key-derivation function; not in the stdlib
    optional:
      - name: modernc.org/sqlite
        version: "latest"
        purpose: Pure Go SQLite driver for production persistence
      - name: mattn/go-sqlite3
        version: "latest"
        purpose: CGo SQLite driver (faster, requires CGo)
  build_tools:
    - name: go
      version: ">=1.22"
      purpose: Go compiler and toolchain
```

### Primitive Mapping

This is the whole job of a platform blueprint: the protocol names the primitives
an implementation must use, and this table says where each one comes from in Go.
It does not restate what the primitives are, what standard defines them, or what
parameters they take. Those live in the blueprint that requires them, and a copy
here would be a second thing to keep right.

| Primitive required by | Provided in Go by | Status |
|---|---|---|
| `protocol/identity` — signature algorithm | `github.com/cloudflare/circl` | **required** |
| `protocol/identity` — key-derivation function | `golang.org/x/crypto` | **required** |
| `protocol/identity` — symmetric encryption | stdlib `crypto/aes`, `crypto/cipher` | stdlib |
| `protocol/identity` — random source | stdlib `crypto/rand` | stdlib |
| `protocol/identity` — non-echoing passphrase channel | `golang.org/x/term` | **only if the implementation prompts** — a headless service takes an injected credential and needs no terminal |
| `protocol/types` — canonical JSON | stdlib `encoding/json` + canonicalisation | stdlib |
| `protocol/spec` — HTTP transport | stdlib `net/http` | stdlib |
| `architecture/storage` — default backend | stdlib `os`, `encoding/json` | stdlib |
| `architecture/storage` — non-default backend | a driver for the chosen engine | **only if chosen** |

Both required modules MUST appear in `go.mod`. Everything else Weblisk needs, Go
already ships.

Two primitives are not in the standard library and cannot be. Go has no
post-quantum signature implementation and no memory-hard key-derivation function,
and the alternative to a module for either is writing original cryptographic code,
which is the worst place in a system to do it. `github.com/cloudflare/circl` and
`golang.org/x/crypto` are both maintained under public cryptographic review;
`golang.org/x/crypto` is maintained by the Go project itself.

Beyond those two: no framework, no router, no middleware stack, no logging
library, no database engine, and no package manager at runtime.

See [Go-Specific Requirements](#go-specific-requirements) for
detailed stdlib package usage and conventions.

---

## Go-Specific Requirements

### Dependencies
- Standard library only, except the two modules in the Primitive Mapping table
- The signature algorithm comes from `github.com/cloudflare/circl`
- The key-derivation function comes from `golang.org/x/crypto/argon2`
- `crypto/rand` for secure random generation  
- `encoding/json` for JSON serialization
- `encoding/hex` for hex encoding
- `encoding/base64` for base64url encoding in tokens
- `net/http` for HTTP server and client
- `sync` for thread-safe concurrent access (RWMutex)
- `time` for timestamps and durations
- `io` for reading request bodies (with LimitReader for safety)
- `os` for environment variables and file I/O
- `path/filepath` for path operations
- `fmt` for formatting and printing

### Concurrency
- All registries (agents, channels) protected by `sync.RWMutex`
- Use `RLock` for reads, `Lock` for writes
- Service broadcasts are fire-and-forget goroutines
- HTTP handlers are inherently concurrent (net/http serves each in a goroutine)

### IO Safety
- Use `io.LimitReader` on all request body reads
  - Registration: 1 MB limit (`1 << 20`)
  - Task execution: 10 MB limit (`10 << 20`)
  - Messages: 1 MB limit
  - Channel requests: 64 KB limit (`1 << 16`)
  - Service updates: 1 MB limit

### Package Organization
- One module for the deployment. Each binary is a `package main` under `cmd/`,
  and everything else is a package under `internal/`
- Shared code is **imported, never copied**. One definition of every wire type,
  reached by import path — see "Why one module, and not a copy per binary"
- A package under `internal/` cannot be imported from outside the module, which
  is what keeps the deployment's internals out of anyone else's dependency graph

### Error Handling
- Return errors from functions, don't panic
- HTTP handlers write error JSON responses, don't crash
- Registration failures are fatal (agent can't operate without orchestrator)
- Service broadcast failures are logged and ignored

### Configuration
- Use environment variables (WL_AI_*, WL_ORCH_*) via os.Getenv
- Support command-line flags (--port, --orch) via manual arg parsing
- Load .env file from working directory if present

---

## Build and Run

### Build

```bash
go mod tidy                                    # once, and after any import change
go build -o bin/orchestrator ./cmd/orchestrator
go build ./...                                 # every binary in the module
```

### Run

```bash
./bin/orchestrator --port 9800
```

A component other than the orchestrator is built the same way — `go build -o
bin/<component> ./cmd/<component>` — and run with the flags its own blueprint
defines. This document names no component beyond the orchestrator on purpose;
which ones a deployment has is decided by adopting their blueprints.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WL_PORT` | no | `9800` | Listen port |
| `WL_AI_PROVIDER` | yes | — | LLM provider (`ollama`, `openai`, `anthropic`) |
| `WL_AI_MODEL` | yes | — | Model name for LLM provider |
| `WL_ORCH_URL` | yes (agents) | — | Orchestrator URL for agent registration |
| `WL_DEV` | no | `0` | Set to `1` for in-memory storage mode |

See [Build Commands](#build-commands) for additional build examples.

---

## Build Commands

```bash
go mod tidy
go build ./...                                 # every binary under cmd/
go vet ./...
go test -race -count=1 ./...
./bin/orchestrator --port 9800
```

## Go Module File

```
module weblisk-server

go 1.22
```

No `require` statements needed — stdlib only.

---

## Platform-Specific Conventions

### Concurrency

All registries and shared maps are protected by `sync.RWMutex` with
`RLock` for reads and `Lock` for writes. HTTP handlers are inherently
concurrent (`net/http` serves each request in a goroutine). See
[Concurrency (Go-Specific)](#concurrency-go-specific) for the
channel-based semaphore and `WaitGroup` dispatch patterns.

### IO Safety

- `io.LimitReader` on all request body reads
  - Registration/messages: 1 MB (`1 << 20`)
  - Task execution: 10 MB (`10 << 20`)
  - Channel requests: 64 KB (`1 << 16`)

### Error Handling

- Return errors from functions — never panic
- HTTP handlers write JSON error responses with structured `ErrorResponse`
- Registration failures are fatal; service broadcast failures are logged and ignored

### Logging

- Structured JSON logging to stdout
- Include `component`, `trace_id`, and `timestamp` in all log entries
- Use `log/slog` (Go 1.21+) or `fmt.Fprintf(os.Stderr, ...)` for minimal logging

See [Go-Specific Requirements](#go-specific-requirements) for full
conventions including package organization and configuration.

---

## Project Structure: Domain Controller

```
cmd/<domain-controller>/
  main.go             # entry point — manifest, workflows, start
internal/
  domain/             # workflow engine, dispatch, aggregation
  agent/              # the same agent framework work agents use
```

Build: `go build -o bin/<domain-controller> ./cmd/<domain-controller>`
Run: `./bin/<domain-controller> --port 9700 --orch http://localhost:9800`

A domain controller uses the same agent framework as a work agent (6 protocol
endpoints) and adds the workflow engine in `internal/domain` — see
[architecture/domain.md](../architecture/domain.md) for the execution flow.
Its own aggregation rules live in the package its blueprint defines; this
document does not name one.

## Storage Mapping (Go)

The default backend is **flat-file JSONL**, per
[architecture/storage](../architecture/storage.md): append-only files under the
instance's own directory, readable with `cat`, needing nothing beyond
`encoding/json` and `os`.

Any other backend is valid the moment it satisfies the storage contract. SQLite,
an embedded key-value store, a relational or object store — that is a choice made
when the implementation is commissioned, stated at that point, and never
required by this blueprint. The sections below describe SQLite because it is the
most common such choice, and they apply only when it has been made.

Each component
gets its own database file under `.weblisk/data/`.

See [architecture/storage.md](../architecture/storage.md) for the
abstract storage interface.

| Store | File | Table |
|-------|------|-------|
| Agent Registry | `.weblisk/data/orchestrator.db` | `agents` |
| Audit Log | `.weblisk/data/orchestrator.db` | `audit_log` |
| Channels | In-memory map (short-lived, 1h TTL) | — |
| Strategies | `.weblisk/data/lifecycle.db` | `strategies` |
| Observations | `.weblisk/data/lifecycle.db` | `observations` |
| Recommendations | `.weblisk/data/lifecycle.db` | `recommendations` |
| Feedback | `.weblisk/data/lifecycle.db` | `feedback` |
| Agent Metrics | `.weblisk/data/lifecycle.db` | `agent_metrics` |
| Entity Context | `.weblisk/data/lifecycle.db` | `entity_context` |
| Workflow Executions | `.weblisk/data/workflow.db` | `executions` |
| Task Records | `.weblisk/data/task.db` | `tasks` |

### SQLite Requirements — only when SQLite was chosen
- Use `database/sql` with `modernc.org/sqlite` (pure Go, no CGo) or
  `mattn/go-sqlite3` (CGo, faster).
- Exception to zero-dependency rule: one SQLite driver dependency is
  acceptable for production persistence.
- Use `WAL` journal mode for concurrent reads during writes.
- Apply `user_version` pragma for schema migrations.
- Schema creation on first open (CREATE TABLE IF NOT EXISTS).

### Development Mode

When `WL_DEV=1` is set, storage MAY fall back to in-memory maps
(as in the current implementation) for fast iteration. A warning
MUST be printed: `"[dev] using in-memory storage — data will not survive restart"`.

## Concurrency (Go-Specific)

### Agent Concurrency Limiter
```go
type ConcurrencyLimiter struct {
    sem chan struct{}
}

func NewConcurrencyLimiter(max int) *ConcurrencyLimiter {
    return &ConcurrencyLimiter{sem: make(chan struct{}, max)}
}

func (l *ConcurrencyLimiter) Acquire() bool {
    select {
    case l.sem <- struct{}{}:
        return true
    default:
        return false // at capacity → return 429
    }
}

func (l *ConcurrencyLimiter) Release() {
    <-l.sem
}
```

Apply in execute/message handlers:
```go
if !limiter.Acquire() {
    writeError(w, 429, ErrorResponse{
        Error:     "agent at capacity",
        Code:      "RATE_LIMITED",
        Category:  "transient",
        Retryable: true,
    })
    w.Header().Set("Retry-After", "5")
    return
}
defer limiter.Release()
```

### Domain Dispatch Parallelism
Use `sync.WaitGroup` + goroutines for parallel phase execution within
a dependency level. Use a semaphore per target agent to respect
`max_concurrent` declarations.

---

## Type Mapping

| Schema Type | Go Type | Notes |
|-------------|---------|-------|
| `string` | `string` | |
| `int` | `int32` | |
| `int64` | `int64` | Used for timestamps |
| `float` | `float64` | |
| `bool` | `bool` | |
| `object` | `map[string]any` | Or typed struct |
| `list` | `[]T` | Typed slice |
| `uuid` | `string` | Validated format |
| `timestamp` | `int64` | Unix epoch seconds via `time.Now().Unix()` |

---

## Security

### Input Validation

- `io.LimitReader` on all request body reads (see IO Safety above)
- Validate JSON structure before processing — reject unknown fields
- Enforce maximum sizes per endpoint type

### Cryptography

- The signature algorithm `protocol/identity` requires comes from `circl` — key generation, signing and verification
- The key-derivation function it requires comes from `golang.org/x/crypto/argon2`
- `crypto/rand` for all secure random generation
- `encoding/hex` for key encoding in protocol messages
- No other external cryptography libraries — algorithms, standards and parameters are `protocol/identity`'s to state, not this document's

### Dependencies

- Two modules, both for primitives Go does not ship; see the Primitive Mapping table
- Nothing beyond them: a minimal dependency set is a minimal supply chain attack surface
- Exception: a storage driver, only when a backend other than the JSONL default was chosen
- Use `go mod verify` to validate module checksums

### Key Management

- Private keys stored as files with `0600` permissions
- Key directory created with `0700` permissions
- Environment variables for non-secret configuration only

---

## Testing

### Unit Tests

```bash
go test ./...                 # the whole module
go test ./internal/protocol   # one package
```

Use table-driven tests for protocol validation:

```go
func TestValidateManifest(t *testing.T) {
    tests := []struct {
        name    string
        input   AgentManifest
        wantErr bool
    }{
        {"valid", AgentManifest{Name: "example", Version: "1.0.0"}, false},
        {"missing name", AgentManifest{Version: "1.0.0"}, true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := validateManifest(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("validateManifest() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### Integration Tests

- Start orchestrator and agent in test, verify registration flow
- Test task execution end-to-end
- Use `httptest.NewServer` for isolated HTTP testing

### CI

```bash
go vet ./...
go test -race -count=1 ./...
```

---

## Implementation Notes

- Binaries are `package main` under `cmd/`; shared code is imported from `internal/`, never copied
- Use manual `os.Args` parsing or a simple flag loop for CLI flags (no `flag` package required)
- If SQLite was chosen: WAL journal mode and `user_version` pragma for schema migrations
- When `WL_DEV=1`, fall back to in-memory maps with a printed warning
- Binaries are fully static — deploy as single file with no runtime dependencies
- Go’s `net/http` default server is production-ready (timeouts should be configured)

---

## Verification Checklist

Assertions here apply to any Go implementation unless a group narrows them to one
component. See `schemas/common.md` for what a group heading means.

- [ ] No dependency outside the Primitive Mapping table — `github.com/cloudflare/circl`, `golang.org/x/crypto`, `golang.org/x/term`, and a storage driver only if a backend other than the JSONL default was chosen; every dependency declared in go.mod
- [ ] One module for the deployment; each binary is `package main` under `cmd/` and shared code is a package under `internal/`
- [ ] No type, constant or function is defined in more than one place — shared code is imported, never copied
- [ ] The blueprint names no specific agent or domain; which components exist is chosen by adopting their blueprints
- [ ] `io.LimitReader` is applied on all request body reads: 1 MB for registration/messages, 10 MB for tasks, 64 KB for channels
- [ ] All registries and shared maps are protected by `sync.RWMutex` with `RLock` for reads and `Lock` for writes
- [ ] Concurrency limiter returns 429 with `Retry-After` header and structured ErrorResponse when agent is at capacity
- [ ] The storage contract in architecture/storage is satisfied — every declared operation exists and survives a restart
- [ ] IF SQLite was chosen: WAL journal mode, `user_version` pragma for migrations, tables created with `CREATE TABLE IF NOT EXISTS`
- [ ] When `WL_DEV=1`, storage falls back to in-memory maps and prints warning: `"[dev] using in-memory storage — data will not survive restart"`
- [ ] Functions return errors — HTTP handlers write error JSON responses and do not panic; registration failures are fatal
- [ ] Configuration loads from environment variables (`WL_*`), command-line flags (`--port`, `--orch`), and `.env` file from working directory

### Domain Controllers
- [ ] Domain controllers use `sync.WaitGroup` + goroutines for parallel phase execution and a per-agent semaphore respecting `max_concurrent`
