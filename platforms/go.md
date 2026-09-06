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
          fields_used: [status, name, version, uptime]
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

The **tenant folder is the module root.** Everything a tenant owns is scoped to
that one directory — its configuration, its keys, its adopted blueprints, and
its code.

```
<tenant>/                     # the tenant IS the root, and the module root
  .weblisk/                   # configuration, keys, grants, data
  blueprints/                 # SOURCE — per standards/project-structure
  assets/                     # physical media
  agents/<name>/agent.yaml    # the blueprints this tenant adopted
  domains/<name>/domain.yaml

  go.mod                      # module <tenant>; go 1.22
  go.sum

  cmd/                        # one directory per BINARY
    orchestrator/main.go      #   <- architecture/orchestrator
    admin/main.go             #   <- architecture/admin
    <name>/main.go            #   <- agents/<name> or a domain controller

  internal/                   # one directory per LIBRARY
    protocol/                 #   <- protocol/types, protocol/spec
    identity/                 #   <- protocol/identity
    storage/                  #   <- architecture/storage
    observability/            #   <- architecture/observability
    orchestrator/             #   <- architecture/orchestrator
    admin/                    #   <- architecture/admin
    agent/                    #   <- architecture/agent  (the framework)
    domain/                   #   <- architecture/domain (the framework)
    agents/<name>/            #   <- agents/<name>       (one agent's logic)
    domains/<name>/

  bin/                        # compiled binaries
  public/                     # generated client output — a build artifact
```

Prepare: `go mod tidy`
Build: `go build -o bin/orchestrator ./cmd/orchestrator`
Run: `./bin/orchestrator --port 9800`

The prepare step is not optional and not part of the build. `go.mod` declares the
dependencies; `go.sum` records their checksums, and Go refuses to build without
it. Writing source files cannot produce it — only resolution can. A generator
that emits a correct `go.mod` and a correct identity package and then builds will
fail with "missing go.sum entry", naming a source file that has nothing wrong
with it. `go.mod` sits at the tenant root, so `go mod tidy` runs there.

### The package is named after the blueprint that specifies it

Every directory above is named after a blueprint, and nothing is named after
anything else. That is the rule, and it is what makes the layout derivable rather
than a matter of taste:

| The blueprint | Is it a running thing? | Where its code goes |
|---|---|---|
| `architecture/orchestrator` | yes | `cmd/orchestrator` + `internal/orchestrator` |
| `architecture/admin` | yes | `cmd/admin` + `internal/admin` |
| `agents/<name>` | yes | `cmd/<name>` + `internal/agents/<name>` |
| `architecture/agent` | no — a framework | `internal/agent` |
| `architecture/domain` | no — a framework | `internal/domain` |
| `protocol/identity` | no — a library | `internal/identity` |
| `protocol/types`, `protocol/spec` | no — a library | `internal/protocol` |
| `architecture/storage` | no — a library | `internal/storage` |
| `architecture/observability` | no — a library | `internal/observability` |

Two consequences worth stating, because both were got wrong before this rule
existed.

**There is no `server/`.** The artifact is an *orchestrator* — that is the
blueprint's name and the binary's name. `server` corresponds to no blueprint, so
a reader who finds it cannot trace it back to anything, and a generator has to be
told where it goes instead of deriving it.

**`architecture/agent` and `agents/<name>` are different things.** The first is
the framework every agent imports and it is a library. The second is one agent
and it is a binary. Their blueprint paths already say so; the code layout now
says the same.

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

A component is a directory holding a `main` package, plus whatever it imports
from `internal/`. This document names no component beyond the orchestrator and
the administrative service, because no other is required: which agents and
domain controllers a tenant has is chosen by adopting their blueprints. An
agent's behaviour comes from [`architecture/agent`](../architecture/agent.md)
and its own blueprint; this document says only how a Go binary for one is laid
out and built.

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
| `protocol/identity` — signature algorithm | `github.com/cloudflare/circl/sign/mldsa/mldsa65` | **required** |
| `protocol/identity` — backup signature algorithm | `github.com/cloudflare/circl/sign/slhdsa` | only if backup signing is implemented |
| `protocol/identity` — key-derivation function | `golang.org/x/crypto/argon2` | **required** |
| `protocol/identity` — symmetric encryption | stdlib `crypto/aes`, `crypto/cipher` | stdlib |
| `protocol/identity` — random source | stdlib `crypto/rand` | stdlib |
| `protocol/identity` — non-echoing passphrase channel | `golang.org/x/term` | **only if the implementation prompts** — a headless service takes an injected credential and needs no terminal |
| `protocol/types` — canonical JSON | stdlib `encoding/json` + canonicalisation | stdlib |
| `protocol/spec` — HTTP transport | stdlib `net/http` | stdlib |
| `architecture/storage` — default backend | stdlib `os`, `encoding/json` | stdlib |
| `architecture/storage` — non-default backend | a driver for the chosen engine | **only if chosen** |

**The import paths above are exact.** They are the whole reason a platform
blueprint exists: the specification names a primitive, and this document says
what to type. A generated hub once imported
`github.com/cloudflare/circl/sign/mldsa65` — a plausible path that does not
exist — and `go mod tidy` refused the build with "module found, but does not
contain package". Nothing in the source was wrong; the import was guessed
because this table gave a module and not a package.

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
- The signature algorithm comes from `github.com/cloudflare/circl/sign/mldsa/mldsa65`
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
- One module rooted at the tenant. Every binary is a `package main` under
  `cmd/<name>`, every library is a package under `internal/<name>`, and each
  name comes from the blueprint that specifies it
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
bin/<name> ./cmd/<name>` — and run with the flags its own blueprint defines. This document names no component beyond the orchestrator on purpose;
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
go build ./...                                 # every binary in the module
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

### The HTTP Surface

An architecture blueprint declares endpoints as protocol facts — `POST
/v1/register`, `GET /v1/health`. This is how they become routes, and it is
stated so that two builds of the same blueprints produce the same arrangement.

**Every symbol is spelled from the endpoint's `Operation`.** The architecture
blueprint's `## Endpoints` table declares the operation — `Register`, `Health`,
`AdminOverview` — and this is how that one name becomes Go:

| Symbol | Spelling | Example |
|---|---|---|
| Path constant | `Path<Operation>`, exported, in `internal/protocol` | `PathRegister` |
| Handler | `handle<Operation>`, unexported method on the server | `handleRegister` |
| Request type | `<Operation>Request` | `RegisterRequest` |
| Response type | `<Operation>Response` | `RegisterResponse` |

No other spelling is permitted, and no symbol may be named from the path or the
purpose. This table is the whole of the mapping so that two generations of the
same blueprint produce the same symbols; see
[`schemas/common`](../schemas/common.md#declared-names).

The four neutral rules — no path literal, one route table, method matched by
the router, and 405/404 as a structured `ErrorResponse` — are stated once in
[`schemas/platform`](../schemas/platform.md#the-rules-every-platforms-http-surface-obeys).
What follows is only how Go satisfies them.

**One route table per component, in one function.** A component declares its
routes as data — pattern, methods, handler — and a single `Routes()` function
turns that table into a `*http.ServeMux`. Registration MUST NOT be scattered
across the files that define the handlers. The table is the component's HTTP
surface written down, so what a component serves can be read without executing
it, and adding an endpoint changes one list rather than one file per endpoint.

**Method and path are matched by the mux, not inside the handler.** Go 1.22
patterns carry the method — `mux.HandleFunc("POST "+protocol.PathRegister, h)`
— and path parameters are read with `r.PathValue("name")`. A handler that
switches on `r.Method` to decide what it is doing is two handlers sharing a
name.

**Rule 4 is answered by the root handler.** `mux.HandleFunc("/", ...)` is
registered once and decides between `405` and `404` by matching the request
path against the route table.

Because the root handler does the matching, it needs a segment comparison that
understands the table's wildcards — `/v1/admin/operators/{name}` matches
`/v1/admin/operators/alice` — and it MUST collect the methods the table declares
for a matched pattern to fill the `Allow` header.

> **A method-less pattern MUST NOT be registered.** Registering the bare path
> alongside `METHOD /path` to catch a wrong method is the obvious arrangement
> and it does not start:
>
> ```
> panic: pattern "/v1/admin/operators/register" conflicts with pattern
> "GET /v1/admin/operators/{name}": /v1/admin/operators/register matches more
> methods than GET /v1/admin/operators/{name}, but has a more specific path
> pattern
> ```
>
> `net/http`'s precedence rule is that one pattern must be strictly more
> specific than the other. A method-less literal is more specific in its PATH
> and less specific in its METHODS than a wildcard sibling under the same
> prefix, so neither dominates — and the conflict is a **startup panic**, not a
> registration error. A generated hub built exactly this way compiled, passed
> conformance, reported "started", and died before it bound the port.
>
> This is precisely what a platform blueprint is for: the requirement ("a wrong
> method answers 405") is the protocol's, and the arrangement that satisfies it
> is this language's business.

The **spelling** of a pattern is deliberately unconstrained. Constants,
concatenation and a derived prefix are all correct Go, and a platform blueprint
exists to make the artifact good — not to make it convenient for a tool to
read. Tooling that inspects the surface is required to resolve these; see
[`architecture/testing`](../architecture/testing.md), "A check that cannot read
the artifact MUST say so".

See [Go-Specific Requirements](#go-specific-requirements) for full
conventions including package organization and configuration.

---

## Project Structure: Domain Controller

```
cmd/<name>/main.go        # entry point — manifest with type: "domain", workflows, start
internal/domains/<name>/  # this controller's aggregation rules and handlers
internal/domain/          # the workflow engine — architecture/domain
internal/agent/           # the same framework a work agent uses
```

Build: `go build -o bin/<name> ./cmd/<name>`
Run: `./bin/<name> --port 9700 --orch http://localhost:9800`

A domain controller registers with the same `AgentManifest` as any agent, with
`type: "domain"`, and serves the same six protocol endpoints. It adds the
workflow engine from `internal/domain` — see
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

## Evaluating a Declared Check in Go

A blueprint's `declaration.checks:` names an expectation. The name is
platform-neutral; **how it is evaluated is this platform's**, exactly as a
declared name is neutral and its spelling is this platform's.

| Check | Evaluated in Go by |
|---|---|
| `no-path-literals` | Walking the AST for a string literal beginning `/v` passed to `HandleFunc`, `Handle`, or assigned to a `pattern` field. A path reaches a route only through a `protocol.Path*` constant |
| `no-method-less-pattern` | Every `HandleFunc` first argument resolves to a string beginning with a method name, or is exactly `"/"`. A bare path beside a wildcard sibling is a startup panic, not an error |
| `endpoint-routed` | Resolving the route table's patterns — constants, local aliases and concatenation — and matching the declared `endpoint`. A pattern the resolver cannot read is reported as unread, never as absent |
| `type-has-keys` | Parsing the named struct and comparing its `json:` tags against the declared `keys`. The tag is authority, not the field name |
| `error-codes-registered` | Every SCREAMING_SNAKE string literal used as a code appears as a key of the central registry map. Environment variable names are excluded — they are found in `os.Getenv` calls, not guessed at by shape |
| `starts-unattended` | Running the built binary with no terminal attached and requiring an answer on the health endpoint. It catches a mux conflict and a passphrase prompt, and neither is visible in source review |

A check this platform cannot evaluate is reported as **unevaluated**, never as
passed. "We did not check this" and "this is correct" are different facts, and a
platform that conflates them makes every check it does run worth less.

---

## Reading a Blueprint into Go

[`architecture/generation`](../architecture/generation.md#how-a-blueprint-is-read)
says which parts of a blueprint bind. This says what each becomes in Go, so the
step between "this is the contract" and "this is the code" is not a judgement
made afresh on every file.

| Blueprint form | Becomes | Rule |
|---|---|---|
| `yaml:types` — a type with fields | a `struct` in the package the plan assigns | One exported field per declared field, with a `json:` tag carrying the declared key exactly. A field the block does not declare is not added |
| `yaml:types` — a named string enum | a `type X string` and one `const` per value | The constant's value is the declared string; the constant's name is the value in PascalCase |
| `table` — an endpoints table | a route-table entry and a handler | Path constant, handler, request and response types all spelled from the `Operation` column per the mapping above |
| `table` — any other | whatever the section specifies | Read by column NAME. A table that gains a column moves nothing |
| `yaml:security` — `enforcement` | a check on the path it names | Each `rule` is a refusal that must be reachable; the `mechanism` says where it lives |
| `yaml:contracts` — `behaviors` | the behaviour's rules, enforced | Each `rules` entry is an assertion the component owes, whether or not the Verification Checklist repeats it |
| `narrative` | nothing, EXCEPT a MUST sentence | A MUST anywhere is binding. It is often the only statement of a rule that no table carries |

### What this rules out

- **A field invented because Go convention suggests it.** `CreatedAt` is not
  added to a type whose block does not declare it. The wire shape is the
  contract, and a struct with an extra serialised field produces a payload the
  other end rejects.
- **A JSON tag derived from the Go field name.** The declared key is authority;
  `agent_id` does not become `agentId` because that is idiomatic elsewhere.
- **An `omitempty` nobody declared.** It changes the wire shape: a required
  field with a zero value disappears from the payload.
- **A type placed in a package the plan did not name**, however natural the
  grouping looks.

### Where the Go type is not obvious

The Primitive Mapping table above binds the protocol's primitives. Beyond it:

| Declared | Go |
|---|---|
| an integer field with no stated width | `int64` — timestamps and counts cross the wire and must not narrow by platform |
| an optional scalar | a pointer, so absent and zero are distinguishable |
| a map with declared value shape | `map[string]T`, never `map[string]any` |
| a duration | `time.Duration`, parsed from the declared unit at the boundary |
| an opaque cursor | `string`, never decoded — the blueprint says implementations may use offsets, timestamps or encoded keys, so nothing may depend on its content |

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

- Each component is `package main` in its own directory; shared code is imported from `internal/`, never copied
- Use manual `os.Args` parsing or a simple flag loop for CLI flags (no `flag` package required)
- If SQLite was chosen: WAL journal mode and `user_version` pragma for schema migrations
- When `WL_DEV=1`, fall back to in-memory maps with a printed warning
- Binaries are fully static — deploy as single file with no runtime dependencies
- Go’s `net/http` default server is production-ready (timeouts should be configured)

---

## Verification Checklist

Assertions here apply to any Go implementation unless a group narrows them to one
component. See `schemas/common.md` for what a group heading means.

- [ ] Every import of a required module uses the exact package path in the Primitive Mapping table
- [ ] No dependency outside the Primitive Mapping table — `github.com/cloudflare/circl`, `golang.org/x/crypto`, `golang.org/x/term`, and a storage driver only if a backend other than the JSONL default was chosen; every dependency declared in go.mod
- [ ] One module rooted at the tenant folder, with `go.mod` at that root
- [ ] Every package is named after the blueprint that specifies it; no directory is named after anything else
- [ ] Binaries are `package main` under `cmd/<name>`; libraries are packages under `internal/<name>`
- [ ] A domain controller imports the same `internal/agent` framework as a work agent, and registers with `type: "domain"`
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
- [ ] Every routed path is an exported `Path<Operation>` constant in `internal/protocol`; no path literal appears at a registration site, in a client, or in a test
- [ ] Each component declares its routes as one table and registers them in one `Routes()` function; no registration happens in the file that defines a handler
- [ ] Routes are registered with Go 1.22 method-and-pattern syntax, and path parameters are read with `r.PathValue`; no handler switches on `r.Method` to choose its behaviour
- [ ] A wrong method answers 405 with an `Allow` header and an unmatched path answers 404, both as a structured `ErrorResponse` carrying a registered error code
- [ ] 405 and 404 are decided by the single `"/"` handler matching the route table; no method-less pattern is registered anywhere — `net/http` panics at startup when one sits beside a wildcard sibling
- [ ] The process binds its port and answers `GET /v1/health` when started with no terminal attached
- [ ] Every struct field carries a `json:` tag matching the declared key exactly; no field is added that its type block does not declare, and no `omitempty` appears that the blueprint did not state
- [ ] An integer field with no stated width is `int64`; an optional scalar is a pointer; a declared map is typed on its value shape and never `map[string]any`
- [ ] A cursor is carried as an opaque string and never decoded

### Domain Controllers
- [ ] Domain controllers use `sync.WaitGroup` + goroutines for parallel phase execution and a per-agent semaphore respecting `max_concurrent`
