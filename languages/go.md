<!-- blueprint
type: language
name: go
version: 5.2.1
requires: [protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway, patterns/deployment]
language: go
tier: free
-->

# Language: Go

What is essential when building in Go: dependency policy, project layout,
error handling, concurrency, and the primitives the standard library does and
does not supply.

It applies to **anything a blueprint specifies** — an orchestrator, an agent, a
content service, a CLI that drives a provider — and says nothing about what is
being built or where it runs. Go is this framework's reference language.

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

  - blueprint: patterns/principal-identity
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        - name: Identity
          fields_used: [id, public_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```yaml
requires:
  - blueprint: protocol/identity
    version: ">=1.0.0 <4.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=3.0.0 <7.0.0"
    bindings:
      types:
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
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

## Primitive Mapping

This is the whole job of a language blueprint: the protocol names the primitives
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
| `architecture/admin` — verifying a step-up passkey's assertion (COSE `-7`, ES256; `-8`, EdDSA) | stdlib `crypto/ecdsa` with `crypto/elliptic`'s P-256, and `crypto/ed25519` | stdlib, **only in the code that verifies a step-up passkey**. A passkey proves a live session and signs nothing kept ([`protocol/identity`](../protocol/identity.md#post-quantum-cryptography)), so these are not a second signature algorithm for anything this table's first row covers, and nothing else imports them |
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

## Project Structure

### One module, one definition of everything

The **tenant folder is the module root.** Everything a tenant owns is scoped to
that one directory — its configuration, its keys, its adopted blueprints, and
its code.

```
<tenant>/                     # the tenant IS the root, and the module root
  .weblisk/                   # configuration, keys, grants, data
  blueprints/                 # SOURCE — per frameworks/weblisk/project-structure
  assets/                     # physical media
  agents/<name>/agent.yaml    # the blueprints this tenant adopted
  domains/<name>/domain.yaml

  go.mod                      # module <tenant>; go 1.27
  go.sum

  cmd/                        # one directory per BINARY
    orchestrator/main.go      #   <- architecture/orchestrator
    admin/main.go             #   <- architecture/admin
    <name>/main.go            #   <- agents/<name> or a domain controller

  internal/                   # one directory per PACKAGE
    protocol/                 #   <- the contract: every declared name, and protocol/*
    identity/                 #   <- protocol/identity
    storage/                  #   <- architecture/storage
    observability/            #   <- architecture/observability
    scope/                    #   <- patterns/scope
    logging/                  #   <- patterns/logging
    orchestrator/             #   <- architecture/orchestrator
    admin/                    #   <- architecture/admin
    content/                  #   <- architecture/content
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

The port on the Run line is an EXAMPLE. Whoever starts the component supplies
the port, so a plan records the run command without it — and without any
`--orch` flag, for the same reason. The run command must be a plain command,
not a shell line: the process it starts IS the component, so that stopping it
shuts the component down in an orderly way rather than killing a wrapper.

The prepare step is not optional and not part of the build. `go.mod` declares the
dependencies; `go.sum` records their checksums, and Go refuses to build without
it. Writing source files cannot produce it — only resolution can. A generator
that emits a correct `go.mod` and a correct identity package and then builds will
fail with "missing go.sum entry", naming a source file that has nothing wrong
with it. `go.mod` sits at the tenant root, so `go mod tidy` runs there.

### The package is named after the blueprint that specifies it

Every directory above is named after a blueprint, and nothing is named after
anything else. That is the rule, and it is what makes the layout derivable rather
than a matter of taste. The tree is an illustration; the block below is the
layout, in the form [`schemas/language`](../schemas/language.md#the-layout-block)
declares, and a generator derives a component's package plan from it before it
asks a model for anything
([`architecture/generation`](../architecture/generation.md#the-plan)).

```yaml
layout:
  module_root: "."
  manifest: go.mod
  module_path: "{hub}"
  name: drop-hyphens
  contract:
    package: internal/protocol
    holds: [type, enum-constant, path-constant, request-type, response-type, error-code]
  packages:
    - {from: "protocol/{name}", package: internal/protocol, role: contract}
    - {from: "agents/{name}", package: "internal/agents/{name}", role: component}
    - {from: "domains/{name}", package: "internal/domains/{name}", role: component}
    - {from: "architecture/{name}", package: "internal/{name}", role: component, when: component}
    - {from: "architecture/{name}", package: "internal/{name}", role: library}
    - {from: "patterns/{name}", package: "internal/{name}", role: library}
  entry: "cmd/{service}/main.go"
  imports:
    entry: [own-component, library, contract]
    component: [library, contract]
    library: [required-library, contract]
    contract: []
  rules:
    - id: go-declared-names-in-contract
      text: >-
        Every type a yaml:types block declares, in any blueprint the tenant's
        components are built from, is a struct or a named type in
        internal/protocol, with its enum constants; so is every Path<Operation>
        constant, for every endpoint of every component, every
        <Operation>Request and <Operation>Response type, and the registry of
        error codes protocol/types declares, each code with its status and
        category. None of them is declared in any other package.
    - id: go-handler-in-serving-component
      text: >-
        A handler, handle<Operation>, is a method on the server of the
        component that serves the endpoint, in that component's package, and
        so are the component's one route table and its Routes() function.
    - id: go-requirement-in-its-blueprints-package
      text: >-
        Code that answers a requirement of a library blueprint, one whose
        role is library above, is written in that blueprint's package, and a
        component calls it there; code that answers a requirement a
        protocol/* blueprint states of every implementation, such as
        canonical JSON or writing an ErrorResponse, is written in
        internal/protocol. What a handler does to serve its endpoint is
        go-handler-in-serving-component's, whichever blueprint states it. A
        component's package holds what answers its own blueprint's
        requirements and the handlers it serves, and nothing a library's
        requirement asks for.
    - id: go-client-in-caller
      text: >-
        Code that calls another component's endpoint is written in the
        calling package, against the contract's path constant and types. No
        package imports the package of a component other than its own.
    - id: go-entry-holds-main
      text: >-
        cmd/<service>/main.go is package main and holds main and the parsing
        of its arguments; it constructs the component from the component's
        package and runs it, and declares nothing a package could hold.
    - id: go-package-only-where-code-is
      text: >-
        A package exists only where the plan writes code into it. A blueprint
        whose requirements no code answers, such as one the component reads
        and implements nothing of, has no package.
    - id: go-one-definition
      text: >-
        A name the contract holds is declared in internal/protocol alone, and
        an exported name of a library package in that package alone; neither
        is declared again in any other package, under its own name or a
        copy's.
    - id: go-imports-acyclic
      text: >-
        A library package imports internal/protocol and the packages of the
        library blueprints its own blueprint requires, and none other. Where
        requires is cyclic among library blueprints, the packages in the
        cycle do not import one another; code one of them needs from another
        is a corpus fault to report, never a reason to merge them.
```

**What each key means** is [`schemas/language`](../schemas/language.md#the-layout-block)'s.
Read in Go:

- **`{name}`** is the blueprint's own name with every `-` removed, for the
  directory and the package clause alike: `patterns/content-git` is
  `internal/contentgit`, package `contentgit`. A package clause cannot hold a
  hyphen, and a directory spelled otherwise than its clause is a second name.
- **`{service}`** is the name the component registers under, from
  [`schemas/programme`](../schemas/programme.md#the-services-in-the-order-they-are-built)'s
  services table, an agent's or a domain's own name. A binary's directory may
  hold a hyphen, since `package main` names nothing: the fabric service is
  `cmd/fabric-service`, its package `internal/fabric`.
- **`when: component`** holds for the blueprint a row of that services table
  names, where the service runs in a process of its own, and for
  `architecture/gateway`, which [`schemas/config`](../schemas/config.md)'s
  `gateway` section declares. The model service runs in the orchestrator's
  process ([`architecture/model-service`](../architecture/model-service.md#architecture)),
  so it has no entry of its own and its package is a library the
  orchestrator's entry imports.
- **Why every declared name is in one package.** A declared type is the wire
  contract, and a contract with two definitions is two contracts that nothing
  makes agree. Measured on the development tenant, a plan that kept protocol
  types in the orchestrator's package left `ErrorResponse`, `PathRegister`,
  `AuditEntry` and `ScopeLevel` each defined in three packages, and thirty
  repairs, each of one file, could not move them. With the contract in one
  package that imports nothing of the tenant's, no import cycle can form
  through a type, even where two components' blueprints require each other,
  as the orchestrator's and the admin gateway's do.

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
  version: ">=1.27"
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
      version: ">=1.27"
      purpose: Go compiler and toolchain
```


## Go-Specific Requirements

### Dependencies
- Standard library only, except the modules in the Primitive Mapping table: the two it marks **required**, and those it marks for a choice only where that choice was made
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
- The packages, what goes in each and what each may import are the
  [layout block](#the-package-is-named-after-the-blueprint-that-specifies-it),
  and nothing here adds to it
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
- Read the environment variables [listed below](#environment-variables) and
  those the component's own blueprint declares, via os.Getenv, and nothing
  else; a component the CLI starts holds only those ([A component starts with a clean environment](../architecture/cli.md#a-component-starts-with-a-clean-environment))
- Support command-line flags (--port, --orch) via manual arg parsing
- Read no model provider, model name or key from the component's own
  environment; a component reaches a model only through the tenant's model gateway ([the tenant's model](../architecture/orchestrator.md#the-tenants-model))

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

### Toolchain and diagnostics

The commands above, and how a failed build's output is read, as
[`schemas/language`](../schemas/language.md#the-toolchain-block) declares
them. `GOFLAGS=-gcflags=all=-e` makes the compiler report every error rather
than stopping at ten, so one build gives a repair every finding.

```yaml
toolchain:
  version: ">=1.27"
  probe: {command: [go, env, GOVERSION], version: '^go([0-9]+\.[0-9]+(?:\.[0-9]+)?)'}
  prepare: [[go, mod, tidy]]
  build: [go, build, ./...]
  build_component: [go, build, -o, "bin/{service}", "./cmd/{service}"]
  run: ["bin/{service}"]
  vet: [go, vet, ./...]
  env: {GOFLAGS: "-gcflags=all=-e"}
```

```yaml
diagnostics:
  format: text
  line: '^\.?/?(?P<file>[\w./-]+\.go):(?P<line>\d+):(?:(?P<col>\d+):)?\s*(?P<message>.+)$'
  continuation: '^(\t|    )'
  reset: '^# '
  drop: ['^too many errors$']
  symbols:
    - {kind: undefined, pattern: 'undefined: (?P<symbol>\w+)'}
    - {kind: redeclared, pattern: '^(?P<symbol>\w+) redeclared in this block'}
    - {kind: redeclared, pattern: '(?P<other_file>[\w./-]+\.go):\d+:\d+: other declaration of (?P<symbol>\w+)'}
    - {kind: method-redeclared, pattern: 'method (?P<type>\w+)\.(?P<symbol>\w+) already declared at (?P<other_file>[\w./-]+\.go):'}
    - {kind: not-implemented, pattern: '\*?(?P<symbol>\w+) does not implement \*?(?P<other>\w+)'}
    - {kind: unused, pattern: '^declared and not used: (?P<symbol>\w+)'}
  load_failure:
    - "found packages "
    - "import cycle not allowed"
    - "is a program, not an importable package"
    - "build constraints exclude all Go files"
    - "no Go files in"
    - "no non-test Go files in"
    - "is not in std"
  dependency_fault:
    markers:
      - "missing go.sum entry"
      - "no required module provides package"
      - "updates to go.mod needed"
      - "inconsistent vendoring"
      - "module lookup disabled"
    fix: [[go, mod, tidy]]
  mechanism_failure: '^go: '
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WL_PORT` | no | the component's own, from [`schemas/config`](../schemas/config.md#port-conventions) (`9800` for the orchestrator, `9802` for the content service) | Listen port |
| `WL_ORCH_URL` | for an agent, where an orchestrator is named or running | — | Orchestrator URL for agent registration; the CLI sets it, with `--orch`, only where an orchestrator is named or running ([A component starts with a clean environment](../architecture/cli.md#a-component-starts-with-a-clean-environment)) |
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

The module is the tenant's ([One module, one definition of everything](#one-module-one-definition-of-everything)),
and `go.mod` is written by the engine from this block, never by a model. Its
module path is the tenant's `hub.name` ([`schemas/config`](../schemas/config.md)),
which is already a valid Go module path, so two builds of one tenant never name
the module differently. Its `go` directive is the toolchain's minimum. It
requires the two modules the [Primitive Mapping](#primitive-mapping) marks
**required**, `golang.org/x/term` only where the implementation prompts, and a
storage driver only where a backend other than the default was chosen; nothing
else. Versions are never written by generation: `go mod tidy`, the prepare
step, resolves them and writes `go.sum`.

```yaml
module:
  manifest: go.mod
  language_version: "1.27"
  requires:
    - {name: github.com/cloudflare/circl, when: always}
    - {name: golang.org/x/crypto, when: always}
    - {name: golang.org/x/term, when: the implementation prompts for a passphrase}
    - {name: modernc.org/sqlite, when: the SQLite backend was chosen and CGo is not used}
    - {name: github.com/mattn/go-sqlite3, when: the SQLite backend was chosen with CGo}
  versions: resolved
  written_by: engine
```

Written out for a tenant whose `hub.name` is `demo-hub`, before `go mod tidy`
adds versions:

```
module demo-hub

go 1.27

require (
    github.com/cloudflare/circl <resolved>
    golang.org/x/crypto <resolved>
)
```

---

## Language Conventions

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

- One `LogEntry` per line on standard output, in the envelope
  [`patterns/logging`](../patterns/logging.md) defines
- Use `log/slog` with a JSON handler on `os.Stdout` whose `ReplaceAttr` writes
  `LogEntry`'s keys: `time` as `ts`, `level` in lower case

### The HTTP Surface

An architecture blueprint declares endpoints as protocol facts — `POST
/v1/register`, `GET /livez`. This is how they become routes, and it is
stated so that two builds of the same blueprints produce the same arrangement.

**Every symbol is spelled from the endpoint's `Operation`.** The architecture
blueprint's `## Endpoints` table declares the operation — `Register`, `Livez`,
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

**Method and path are matched by the mux, not inside the handler.** A pattern
carries its method — `mux.HandleFunc("POST "+protocol.PathRegister, h)`
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
`type: "domain"`, and serves the same seven protocol endpoints. It adds the
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

### Injected Passphrase

The channel [`protocol/identity`](../protocol/identity.md#encryption-scheme)
leaves to the platform. A service whose key file is `kdf = argon2id` reads its
passphrase once, at start and before it binds a port, as one line from
standard input, ended by a line feed or by the end of input, of at most
1024 bytes, within 10 seconds; it then closes standard input and zeroises the
passphrase once the key is open. No line, a longer one, or one that does not
open the key is `identity.key_decrypt_failed` and exit code 2
([`protocol/identity`](../protocol/identity.md#key-categories) rule 5). A key with `kdf = none` reads nothing from standard input, and
outside `WL_DEV=1` is refused (rule 6). Nothing reads a passphrase from an
argument, an environment variable or a terminal prompt. [`architecture/cli`](../architecture/cli.md#weblisk-server-start)
is what writes that line.

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
    // A header set after the status is written is never sent.
    w.Header().Set("Retry-After", "5")
    writeError(w, 429, ErrorResponse{
        Error:     "agent at capacity",
        Code:      "RATE_LIMITED",
        Category:  "transient",
        Retryable: true,
    })
    return
}
defer limiter.Release()
```

### Domain Dispatch Parallelism
Use `sync.WaitGroup` + goroutines for parallel phase execution within
a dependency level. Use a semaphore per target agent to respect
`max_concurrent` declarations.

---

## Reading a Blueprint into Go

[`architecture/generation`](../architecture/generation.md#how-a-blueprint-is-read)
says which parts of a blueprint bind. This says what each becomes in Go, so the
step between "this is the contract" and "this is the code" is not a judgement
made afresh on every file.

| Blueprint form | Becomes | Rule |
|---|---|---|
| `yaml:types` — a type with fields | a `struct` in `internal/protocol` (`go-declared-names-in-contract`) | One exported field per declared field, with a `json:` tag carrying the declared key exactly. A field the block does not declare is not added. `omitempty` is on exactly the fields the block does not require, as [What this rules out](#what-this-rules-out) says |
| `yaml:types` — a named string enum | a `type X string` and one `const` per value, in `internal/protocol` | The constant's value is the declared string; the constant's name is the type's name followed by the value in PascalCase: `OperatorRole`'s `viewer` is `OperatorRoleViewer`. Every enum shares one package, so a constant named from its value alone collides as soon as two enums share a value |
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
- **An `omitempty` on a required field, or none on an optional one.**
  [`protocol/types`](../protocol/types.md#conventions) leaves an optional
  field that holds no value out of the JSON and always writes a required one,
  and says which is which. So a required field carries no `omitempty`, and
  its zero value is written; an optional one carries `omitempty`, on a
  pointer where it is a scalar, so absent and zero stay distinct. Nothing
  else decides it, Go convention included.
- **A declared name placed outside the package the layout gives it**, however
  natural the grouping looks
  ([The package is named after the blueprint that specifies it](#the-package-is-named-after-the-blueprint-that-specifies-it)).

### Where the Go type is not obvious

The Primitive Mapping table above binds the protocol's primitives, and the
[Type Mapping](#type-mapping) below binds each declared field type. Beyond them:

| Declared | Go |
|---|---|
| an optional scalar | a pointer, so absent and zero are distinguishable |
| a duration | `time.Duration`, parsed from the declared unit at the boundary |
| an opaque cursor | `string`, never decoded — the blueprint says implementations may use offsets, timestamps or encoded keys, so nothing may depend on its content |

---

## Type Mapping

| Schema Type | Go Type | Notes |
|-------------|---------|-------|
| `string` | `string` | |
| `int` | `int32` | 32-bit, as `schemas/common` declares it |
| `int64` | `int64` | |
| `integer` | `int64` | No stated width, so the widest: a count crossing the wire never narrows |
| `float` | `float64` | |
| `bool` | `bool` | |
| `object` | a struct | A struct whose fields are the declared ones; `map[string]any` only where none are declared |
| `map` | `map[string]any` | Its members are undeclared and its values any JSON (`schemas/common`), so there is no `T` to type it on |
| `list` | `[]T` | Typed slice |
| `uuid` | `string` | Validated format |
| `timestamp` | `string` | RFC 3339 UTC with milliseconds (`protocol/conventions:instant`) via `t.UTC().Format("2006-01-02T15:04:05.000Z")`; read back with `time.Parse` on the same layout |

---

## Security

### Input Validation

- `io.LimitReader` on all request body reads (see IO Safety above)
- Validate JSON structure before processing. An unknown field is ignored,
  never rejected, and an object that is signed or forwarded is kept as it
  arrived, its unknown fields included ([`protocol/types`](../protocol/types.md#conventions),
  [`protocol/spec`](../protocol/spec.md#signing-input)); no decoder is set to
  refuse unknown fields
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

### Translated tests

A test translated from a criterion
([`schemas/language`](../schemas/language.md#the-tests-block)) is an HTTP
black-box test in a package of its own under `test/`, one file per criterion,
using only the standard library and `internal/protocol`'s declared types. It
reads the component's address from `WL_TEST_URL`, and fails, never skips, when
that is unset.

```yaml
tests:
  owns: "test/**"
  path: "test/{service}/{criterion}_test.go"
  name: snake
  header: "// weblisk:criterion {ref} digest {digest} action {action}"
  package: conformance
  function: "Test_{criterion}"
  target: WL_TEST_URL
  vectors: testdata/weblisk-vectors/
  command: [go, test, -count=1, -json, -run, "^Test_{criterion}$", "./test/{service}"]
  result:
    format: json-lines
    test: /Test
    outcome: /Action
    pass: pass
    fail: fail
    skip: skip
  stub: >-
    The plan's declared names in internal/protocol, and each component's entry
    answering every route its blueprint declares with 501 and an ErrorResponse;
    a translated test run against it must fail.
```

---

## Structure Queries

A `structure` check ([`schemas/blocks`](../schemas/blocks.md#checks)) names a
query and never holds its text, because a query is a question about one
language's parse tree. These are Go's, in the form
[`schemas/language`](../schemas/language.md#the-structure-block) declares. A
check naming a query this block does not declare is **unread** for Go, never
passed.

```yaml
structure:
  parser: {grammar: tree-sitter-go, version: ">=0.23.0"}
  files: "**/*.go"
  queries:
    path-literal:
      text: >-
        A string literal that begins with a versioned path, /v and a digit.
        Outside internal/protocol, a path reaches a route, a client or a test
        only through a Path<Operation> constant.
      query: |
        ([(interpreted_string_literal) (raw_string_literal)] @value
          (#match? @value "^[\"`]/v[0-9]+(/|[\"`])"))
    method-less-pattern:
      text: >-
        A pattern given to Handle or HandleFunc that does not begin with a
        method and is not exactly "/". A pattern held in a variable or a
        constant is unread here; the topology check starts-unattended is what
        settles it, since net/http panics on the conflict at startup.
      query: |
        (call_expression
          function: (selector_expression field: (field_identifier) @_f (#match? @_f "^Handle(Func)?$"))
          arguments: (argument_list . (interpreted_string_literal) @value
            (#not-match? @value "^\"((GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS) |/\"$)")))
        (call_expression
          function: (selector_expression field: (field_identifier) @_f (#match? @_f "^Handle(Func)?$"))
          arguments: (argument_list . (binary_expression left: (interpreted_string_literal) @value)
            (#not-match? @value "^\"(GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS) ")))
        (call_expression
          function: (selector_expression field: (field_identifier) @_f (#match? @_f "^Handle(Func)?$"))
          arguments: (argument_list . [(identifier) (selector_expression)] @unread))
    type-wire-keys:
      text: >-
        The wire keys of the struct named ${type}: the name in each field's
        json tag. The tag is authority, never the field's name.
      query: |
        (type_spec name: (type_identifier) @_t (#eq? @_t "${type}")
          type: (struct_type (field_declaration_list
            (field_declaration tag: (raw_string_literal) @value))))
      value: 'json:"([^",]*)'
    error-code-use:
      text: >-
        A string literal shaped as an error code, SCREAMING_SNAKE with at
        least one underscore. A literal passed to os.Getenv or os.LookupEnv
        names an environment variable and is excluded.
      query: |
        ((interpreted_string_literal) @value
          (#match? @value "^\"[A-Z][A-Z0-9]*(_[A-Z0-9]+)+\"$"))
        (call_expression
          function: (selector_expression operand: (identifier) @_p field: (field_identifier) @_f
            (#eq? @_p "os") (#match? @_f "^(Getenv|LookupEnv)$"))
          arguments: (argument_list (interpreted_string_literal) @exclude))
      value: '^"(.*)"$'
    error-code-registered:
      text: >-
        A key of a map literal in the contract package: the central registry
        of error codes, each with its status and category.
      query: |
        (composite_literal type: (map_type)
          body: (literal_value (keyed_element . (literal_element (interpreted_string_literal) @value))))
      value: '^"(.*)"$'
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

- [ ] Every import of a required module uses the exact package path in the Primitive Mapping table ([Primitive Mapping](#primitive-mapping)) <!-- wl:check import-required-module-uses-exact-package -->
- [ ] No dependency outside the Primitive Mapping table — `github.com/cloudflare/circl`, `golang.org/x/crypto`, `golang.org/x/term`, and a storage driver only if a backend other than the JSONL default was chosen; every dependency declared in go.mod ([Primitive Mapping](#primitive-mapping), [Runtime Requirements](#runtime-requirements)) <!-- wl:check no-dependency-outside-primitive-mapping-table -->
- [ ] One module rooted at the tenant folder, with `go.mod` at that root ([One module, one definition of everything](#one-module-one-definition-of-everything)) <!-- wl:check module-rooted-tenant-folder-go-mod -->
- [ ] Every package is the one the layout block gives the blueprint its code answers, spelled with every `-` removed; no directory is named after anything else, and no package exists that the plan writes no code into ([The package is named after the blueprint that specifies it](#the-package-is-named-after-the-blueprint-that-specifies-it) `go-requirement-in-its-blueprints-package`, `go-package-only-where-code-is`) <!-- wl:check package-layout-block-gives-blueprint-code -->
- [ ] Each component's entry is `cmd/<service>/main.go`, `package main`, holding `main` and its argument parsing alone; every other file is a package under `internal/` ([The package is named after the blueprint that specifies it](#the-package-is-named-after-the-blueprint-that-specifies-it) `go-entry-holds-main`) <!-- wl:check components-entry-cmd-service-main-go -->
- [ ] A domain controller imports the same `internal/agent` framework as a work agent, and registers with `type: "domain"` ([Project Structure: Domain Controller](#project-structure-domain-controller)) <!-- wl:check domain-controller-imports-internal-agent -->
- [ ] Every declared type, enum constant, `Path<Operation>` constant, `<Operation>Request` and `<Operation>Response` type and the error-code registry is declared in `internal/protocol` and in no other package, and no exported name of a library package is declared in another package ([The package is named after the blueprint that specifies it](#the-package-is-named-after-the-blueprint-that-specifies-it) `go-declared-names-in-contract`, `go-one-definition`; [Why one module, and not a copy per binary](#why-one-module-and-not-a-copy-per-binary)) <!-- wl:check declared-type-enum-constant-path-operation -->
- [ ] No package imports the package of a component other than its own; a library package imports only `internal/protocol` and the packages of the library blueprints its blueprint requires, and none in a `requires` cycle with it ([The package is named after the blueprint that specifies it](#the-package-is-named-after-the-blueprint-that-specifies-it) `go-client-in-caller`, `go-imports-acyclic`) <!-- wl:check no-package-imports-package-component-other -->
- [ ] Every handler `handle<Operation>`, the component's route table and its `Routes()` are in the package of the component that serves the endpoint ([The package is named after the blueprint that specifies it](#the-package-is-named-after-the-blueprint-that-specifies-it) `go-handler-in-serving-component`) <!-- wl:check handler-handle-operation-components-route-table -->
- [ ] The blueprint names no specific agent or domain; which components exist is chosen by adopting their blueprints ([A component's shape](#a-components-shape), [Run](#run)) <!-- wl:check blueprint-names-no-specific-agent-domain -->
- [ ] `io.LimitReader` is applied on all request body reads, at the limit [IO Safety](#io-safety) gives each kind of request <!-- wl:check io-limitreader-applied-request-body-reads -->
- [ ] All registries and shared maps are protected by `sync.RWMutex` with `RLock` for reads and `Lock` for writes ([Concurrency](#concurrency), [Concurrency](#concurrency-1)) <!-- wl:check registries-shared-maps-protected-sync-rwmutex -->
- [ ] Concurrency limiter returns 429 with `Retry-After` header and structured ErrorResponse when agent is at capacity ([Agent Concurrency Limiter](#agent-concurrency-limiter)) <!-- wl:check concurrency-limiter-returns-429-retry -->
- [ ] The storage contract in architecture/storage is satisfied — every declared operation exists and survives a restart ([`architecture/storage`](../architecture/storage.md#contracts), [Storage Mapping (Go)](#storage-mapping-go)) <!-- wl:check storage-contract-architecture-storage-satisfied -->
- [ ] IF SQLite was chosen: WAL journal mode, `user_version` pragma for migrations, tables created with `CREATE TABLE IF NOT EXISTS` ([SQLite Requirements — only when SQLite was chosen](#sqlite-requirements--only-when-sqlite-was-chosen)) <!-- wl:check sqlite-chosen-wal-journal-mode-user -->
- [ ] When `WL_DEV=1`, storage falls back to in-memory maps and prints warning: `"[dev] using in-memory storage — data will not survive restart"` ([Development Mode](#development-mode)) <!-- wl:check when-wl-dev-1-storage-falls -->
- [ ] Functions return errors — HTTP handlers write error JSON responses and do not panic; registration failures are fatal ([Error Handling](#error-handling)) <!-- wl:check functions-return-errors-http-handlers-write -->
- [ ] Configuration loads from the environment variables this document lists and the component's blueprint declares, and from command-line flags (`--port`, `--orch`); nothing reads a `.env` file, and no model provider, model name or key is read from the environment ([Configuration](#configuration), [Environment Variables](#environment-variables)) <!-- wl:check configuration-loads-environment-variables -->
- [ ] Every routed path is an exported `Path<Operation>` constant in `internal/protocol`; no path literal appears at a registration site, in a client, or in a test ([The HTTP Surface](#the-http-surface)) <!-- wl:check routed-path-exported-path-operation-constant -->
- [ ] Each component declares its routes as one table and registers them in one `Routes()` function; no registration happens in the file that defines a handler ([The HTTP Surface](#the-http-surface)) <!-- wl:check component-declares-routes-table-registers-them -->
- [ ] Routes are registered with Go's method-and-pattern syntax, and path parameters are read with `r.PathValue`; no handler switches on `r.Method` to choose its behaviour ([The HTTP Surface](#the-http-surface)) <!-- wl:check routes-registered-gos-method-pattern-syntax -->
- [ ] A wrong method answers 405 with an `Allow` header and an unmatched path answers 404, both as a structured `ErrorResponse` carrying a registered error code ([The HTTP Surface](#the-http-surface), [`schemas/platform`](../schemas/platform.md#the-rules-every-platforms-http-surface-obeys)) <!-- wl:check wrong-method-answers-405-allow-header -->
- [ ] 405 and 404 are decided by the single `"/"` handler matching the route table; no method-less pattern is registered anywhere — `net/http` panics at startup when one sits beside a wildcard sibling ([The HTTP Surface](#the-http-surface)) <!-- wl:check 405-404-decided-single-handler-matching -->
- [ ] The process binds its port and answers `GET /livez` when started with no terminal attached ([`architecture/orchestrator`](../architecture/orchestrator.md#declared-checks) `starts-unattended`) <!-- wl:check process-binds-port-answers-get-livez -->
- [ ] Every struct field carries a `json:` tag matching the declared key exactly; no field is added that its type block does not declare, and `omitempty` is on every optional field and on no required one ([Reading a Blueprint into Go](#reading-a-blueprint-into-go), [What this rules out](#what-this-rules-out)) <!-- wl:check struct-field-carries-json-tag-matching -->
- [ ] Every field's Go type is the one [Type Mapping](#type-mapping) gives its declared type, and an optional scalar is a pointer ([Where the Go type is not obvious](#where-the-go-type-is-not-obvious)) <!-- wl:check fields-go-type-type-mapping-gives -->
- [ ] A cursor is carried as an opaque string and never decoded ([Where the Go type is not obvious](#where-the-go-type-is-not-obvious)) <!-- wl:check cursor-carried-opaque-string-never-decoded -->

### Domain Controllers
- [ ] Domain controllers use `sync.WaitGroup` + goroutines for parallel phase execution and a per-agent semaphore respecting `max_concurrent` ([Domain Dispatch Parallelism](#domain-dispatch-parallelism)) <!-- wl:check domain-controllers-use-sync-waitgroup-goroutines -->
