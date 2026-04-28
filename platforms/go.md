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

Go is the ideal fit for Weblisk because it achieves **true zero
external dependencies** — the entire framework compiles from the Go
standard library alone. No package manager, no native bindings, no
external database servers. The only exception is the optional SQLite
driver for persistence, which compiles into the binary (embedded,
not an external server).

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

### Orchestrator
```
server/
  go.mod              # module server; go 1.22
  main.go             # Entry point — configure and start orchestrator
  protocol.go         # All protocol types (AgentManifest, TaskRequest, etc.)
  identity.go         # Ed25519 key management, signing, tokens
  orchestrator.go     # HTTP server with registration, routing, channels, audit
  helpers.go          # JSON helpers, utility functions
```

Build: `cd server && go build -o orchestrator .`
Run: `./orchestrator --port 9800`

### Agent
```
agents/<name>/
  go.mod              # module weblisk-agent-<name>; go 1.22
  main.go             # Entry point — configure manifest, create agent, start
  protocol.go         # Same protocol types as orchestrator (shared contract)
  identity.go         # Same identity/crypto code
  agent.go            # Agent base framework (HTTP server, registration, messaging)
  <name>.go           # Domain-specific logic (Execute + HandleMessage)
  helpers.go          # Shared utility functions
```

Build: `cd agents/<name> && go build -o <name> .`
Run: `./agents/seo --port 9710 --orch http://localhost:9800`

---

## Runtime Requirements

```yaml
runtime:
  language: Go
  version: ">=1.22"
  dependencies:
    required: []  # Zero external dependencies — Go standard library only
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

Go achieves true zero external dependencies — the entire framework
compiles from the Go standard library alone. The only exception is
an optional SQLite driver for production persistence.

See [Go-Specific Requirements](#go-specific-requirements) for
detailed stdlib package usage and conventions.

---

## Go-Specific Requirements

### Dependencies
- Zero external dependencies. Use only Go standard library.
- `crypto/ed25519` for key generation and signing
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
- All files in a single Go package (`package main` for standalone binaries)
- Shared code (protocol.go, identity.go, helpers.go) is identical between
  orchestrator and agents — copy, don't import (keeps each binary standalone)

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
# Build orchestrator
cd server && go build -o orchestrator .

# Build agent
cd agents/<name> && go build -o <name> .
```

### Run

```bash
# Run orchestrator
./server/orchestrator --port 9800

# Run agent (connects to orchestrator)
WL_AI_PROVIDER=ollama WL_AI_MODEL=llama3 ./agents/seo --orch http://localhost:9800
```

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
# Build orchestrator
cd server && go build -o orchestrator .

# Build agent
cd agents/seo && go build -o seo .

# Run orchestrator
./server/orchestrator --port 9800

# Run agent (connects to orchestrator)
WL_AI_PROVIDER=ollama WL_AI_MODEL=llama3 ./agents/seo --orch http://localhost:9800
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
domains/<name>/
  go.mod              # module weblisk-domain-<name>; go 1.22
  main.go             # Entry point — manifest, workflows, start
  protocol.go         # Same protocol types
  identity.go         # Same identity/crypto code
  agent.go            # Agent base framework (shared with work agents)
  domain.go           # Domain controller logic: workflow engine, dispatch, aggregation
  workflows.go        # Workflow definitions (parsed from embedded YAML or code)
  <name>.go           # Domain-specific aggregation rules and HandleMessage actions
  helpers.go          # Shared utility functions
```

Build: `cd domains/<name> && go build -o <name> .`
Run: `./domains/seo --port 9700 --orch http://localhost:9800`

The domain controller uses the same agent base framework as work agents
(6 protocol endpoints). The additional workflow engine lives in
`domain.go` — see [architecture/domain.md](../architecture/domain.md)
for the execution flow.

## Storage Mapping (Go / SQLite)

The Go platform uses SQLite for persistent storage. Each component
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

### SQLite Requirements
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

- `crypto/ed25519` for key generation, signing, and verification
- `crypto/rand` for all secure random generation
- `encoding/hex` for key encoding in protocol messages
- No external cryptography libraries needed

### Dependencies

- Zero external dependencies eliminates supply chain attack surface
- Exception: one SQLite driver for production persistence (auditable, well-known)
- Use `go mod verify` to validate module checksums

### Key Management

- Private keys stored as files with `0600` permissions
- Key directory created with `0700` permissions
- Environment variables for non-secret configuration only

---

## Testing

### Unit Tests

```bash
cd server && go test -v ./...
cd agents/<name> && go test -v ./...
```

Use table-driven tests for protocol validation:

```go
func TestValidateManifest(t *testing.T) {
    tests := []struct {
        name    string
        input   AgentManifest
        wantErr bool
    }{
        {"valid", AgentManifest{Name: "seo", Version: "1.0.0"}, false},
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

- All files in `package main` — shared code is copied between binaries, not imported
- Use manual `os.Args` parsing or a simple flag loop for CLI flags (no `flag` package required)
- SQLite uses WAL journal mode and `user_version` pragma for schema migrations
- When `WL_DEV=1`, fall back to in-memory maps with a printed warning
- Binaries are fully static — deploy as single file with no runtime dependencies
- Go’s `net/http` default server is production-ready (timeouts should be configured)

---

## Verification Checklist

- [ ] Zero external dependencies — only Go standard library is imported (exception: one SQLite driver for persistence)
- [ ] All source files are in `package main`; shared code (protocol.go, identity.go, helpers.go) is copied between orchestrator and agents
- [ ] `io.LimitReader` is applied on all request body reads: 1 MB for registration/messages, 10 MB for tasks, 64 KB for channels
- [ ] All registries and shared maps are protected by `sync.RWMutex` with `RLock` for reads and `Lock` for writes
- [ ] Concurrency limiter returns 429 with `Retry-After` header and structured ErrorResponse when agent is at capacity
- [ ] SQLite uses WAL journal mode and `user_version` pragma for schema migrations; tables created with `CREATE TABLE IF NOT EXISTS`
- [ ] When `WL_DEV=1`, storage falls back to in-memory maps and prints warning: `"[dev] using in-memory storage — data will not survive restart"`
- [ ] Functions return errors — HTTP handlers write error JSON responses and do not panic; registration failures are fatal
- [ ] Configuration loads from environment variables (`WL_*`), command-line flags (`--port`, `--orch`), and `.env` file from working directory
- [ ] Domain controllers use `sync.WaitGroup` + goroutines for parallel phase execution and a per-agent semaphore respecting `max_concurrent`
