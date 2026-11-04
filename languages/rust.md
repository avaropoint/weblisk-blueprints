<!-- blueprint
type: language
name: rust
version: 5.0.0
requires: [protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway, patterns/deployment]
language: rust
tier: free
-->

# Language: Rust

Guidance for generating Weblisk orchestrator and agent implementations
in Rust, running as local processes. Rust is the high-performance
alternative to the Go reference implementation — delivering the same
single-binary, zero-GC deployment model with compile-time memory
safety and zero-cost abstractions.

Rust fits Weblisk because it achieves **single-binary deployment with
no runtime dependencies** — the same operational simplicity as Go,
with stronger compile-time guarantees. The borrow checker eliminates
data races at compile time, `async/await` with tokio handles concurrent
agent communication efficiently, and `serde` provides zero-copy
deserialization for high-throughput JSON protocol handling.

## Overview

This blueprint provides the Rust implementation for Weblisk. Rust
is a systems-level alternative to the Go reference platform — all
protocol types, identity management, and agent lifecycle patterns
compile to standalone binaries with no garbage collector and no
runtime overhead. This guide covers project structure (Cargo
workspace), build commands, async concurrency with tokio, storage
mapping (JSONL by default), and Rust-specific idioms for error handling,
trait-based abstractions, and type safety.

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
an implementation must use, and this table says where each one comes from on this
platform. It does not restate what the primitives are, what standard defines them,
or what parameters they take — those live in the blueprint that requires them, and
a copy here would be a second normative statement free to drift from the first.

A slot marked **UNFILLED** is a stated gap, not a detail — see
[`schemas/platform`](../schemas/platform.md#an-unfilled-slot-is-a-stated-gap).

| Primitive required by | Provided in Rust by | Status |
|---|---|---|
| `protocol/identity` — signature algorithm | a post-quantum signature crate | **UNFILLED** — the RustCrypto `ml-dsa` crate is the candidate; confirm its maturity before commissioning |
| `protocol/identity` — key-derivation function | `argon2` (RustCrypto) | required |
| `protocol/identity` — symmetric encryption | `aes-gcm` (RustCrypto) | required |
| `protocol/identity` — random source | `getrandom` or `rand` | required |
| `protocol/types` — canonical JSON | `serde_json` plus canonicalisation | required |
| `protocol/spec` — HTTP transport | std or a minimal HTTP crate | required |
| `architecture/storage` — default backend | `std::fs` — flat-file JSONL | std |
| `architecture/storage` — non-default backend | a driver for the chosen engine | only if chosen |

Rust's standard library carries no cryptography, so every primitive above is a
crate. That is a property of the platform, not a relaxation of the dependency
discipline: the set is fixed here and nothing outside it is permitted.

---

## Project Structure

### One workspace, one crate per blueprint

The tenant folder is the workspace root. Every crate is named after the
blueprint that specifies it, exactly as [`languages/go`](go.md#the-package-is-named-after-the-blueprint-that-specifies-it)
names a package, so the layout is derived rather than chosen: a library crate
under `crates/`, one per blueprint whose requirements some code answers, and a
binary crate under `bins/`, one per component, named as the component
registers. There is no `server` and no `weblisk-core`: neither corresponds to a
blueprint, so a reader who finds one cannot trace it back to anything.

```
<tenant>/                       # the tenant IS the root, and the workspace root
  .weblisk/  blueprints/  assets/
  Cargo.toml                    # [workspace]: members, and every dependency's version, once
  Cargo.lock
  crates/
    protocol/                   #   <- the contract: every declared name, and protocol/*
    identity/                   #   <- protocol/identity
    storage/                    #   <- architecture/storage
    orchestrator/               #   <- architecture/orchestrator
    content/                    #   <- architecture/content
    content_git/                #   <- patterns/content-git
    agent/                      #   <- architecture/agent  (the framework)
    domain/                     #   <- architecture/domain (the framework)
    agents/<name>/              #   <- agents/<name>       (one agent's logic)
    domains/<name>/
  bins/
    orchestrator/src/main.rs    # one binary crate per component, named as it registers
    <service>/src/main.rs
  target/                       # build output
```

The block below is the layout, in the form
[`schemas/language`](../schemas/language.md#the-layout-block) declares.

```yaml
layout:
  module_root: "."
  manifest: Cargo.toml
  name: snake
  contract:
    package: crates/protocol
    holds: [type, enum-constant, path-constant, request-type, response-type, error-code]
  packages:
    - {from: "protocol/{name}", package: crates/protocol, role: contract}
    - {from: "agents/{name}", package: "crates/agents/{name}", role: component}
    - {from: "domains/{name}", package: "crates/domains/{name}", role: component}
    - {from: "architecture/{name}", package: "crates/{name}", role: component, when: component}
    - {from: "architecture/{name}", package: "crates/{name}", role: library}
    - {from: "patterns/{name}", package: "crates/{name}", role: library}
  entry: "bins/{service}/src/main.rs"
  imports:
    entry: [own-component, library, contract]
    component: [library, contract]
    library: [required-library, contract]
    contract: []
  rules:
    - id: rust-declared-names-in-contract
      text: >-
        Every type a yaml:types block declares, in any blueprint the tenant's
        components are built from, is a struct or an enum in the crate
        crates/protocol, with serde's Serialize and Deserialize; so is every
        PATH_<OPERATION> constant, for every endpoint of every component, every
        <Operation>Request and <Operation>Response type, and the registry of
        error codes protocol/types declares, each code with its status and
        category. None of them is declared in any other crate.
    - id: rust-handler-in-serving-component
      text: >-
        A handler, handle_<operation>, is in the crate of the component that
        serves the endpoint, and so are the component's one route table and the
        one function that builds its router from it.
    - id: rust-requirement-in-its-blueprints-crate
      text: >-
        Code that answers a requirement of a library blueprint is written in
        that blueprint's crate, and a component calls it there; code that
        answers a requirement a protocol/* blueprint states of every
        implementation is written in crates/protocol. A component's crate
        holds what answers its own blueprint's requirements and the handlers
        it serves, and nothing a library's requirement asks for.
    - id: rust-client-in-caller
      text: >-
        Code that calls another component's endpoint is written in the calling
        crate, against the contract's path constant and types. No crate depends
        on the crate of a component other than its own.
    - id: rust-entry-holds-main
      text: >-
        bins/<service>/src/main.rs holds main and the parsing of its
        arguments; it constructs the component from the component's crate and
        runs it, and declares nothing a library crate could hold. Its package
        is named <service>, so its binary is target/release/<service>.
    - id: rust-crate-only-where-code-is
      text: >-
        A crate exists only where the plan writes code into it. A blueprint
        whose requirements no code answers has no crate.
    - id: rust-one-definition
      text: >-
        A name the contract holds is declared in crates/protocol alone, and a
        public name of a library crate in that crate alone; neither is
        declared again in any other crate, under its own name or a copy's.
    - id: rust-imports-acyclic
      text: >-
        A library crate depends on crates/protocol and the crates of the
        library blueprints its own blueprint requires, and none other. Where
        requires is cyclic among library blueprints, the crates in the cycle
        do not depend on one another (Cargo refuses a cyclic dependency); code
        one of them needs from another is a corpus fault to report, never a
        reason to merge them.
    - id: rust-workspace-dependencies
      text: >-
        Every crate is a member of the root workspace, and every dependency's
        version is stated once, under the root Cargo.toml's
        [workspace.dependencies], and named in a crate with workspace = true.
```

**`{name}` is spelled `snake`**: every `-` becomes `_`, for the directory and
the crate's package name alike, so `patterns/content-git` is
`crates/content_git`, crate `content_git`, as Rust code names it. A binary
crate's directory and package keep the service's own spelling
(`bins/fabric-service`), since its name is the binary's.

**Why one crate per blueprint, and not one shared crate.** A single
`weblisk-core` holding every type and every library is the Go layout's
"everything in one package" fault in another language: three types defined in
three places, nothing to say which blueprint a module answers, and every
component recompiled for any change.

---

## Runtime Requirements

```yaml
runtime:
  language: Rust
  version: ">=1.75.0"
  edition: "2021"
  dependencies:
    required:
      - name: tokio
        version: "1"
        purpose: Async runtime for HTTP and concurrent agent operations
      - name: hyper
        version: "1"
        purpose: HTTP server and client (low-level, no framework bloat)
      - name: serde
        version: "1"
        purpose: Serialization/deserialization for JSON protocol
      - name: serde_json
        version: "1"
        purpose: JSON parsing and generation
      # The signature algorithm's crate is UNFILLED in the Primitive Mapping.
      # pqcrypto-dilithium, named here before, implements Dilithium's third
      # round, not FIPS 204's ML-DSA-65, and its signatures do not verify as
      # ML-DSA-65's do.
      - name: argon2
        version: "0.5"
        purpose: The key-derivation function protocol/identity requires
      - name: aes-gcm
        version: "0.10"
        purpose: The symmetric encryption protocol/identity requires
      - name: getrandom
        version: "0.2"
        purpose: The operating system's secure random source
      - name: thiserror
        version: "1"
        purpose: Ergonomic error type definitions
      - name: anyhow
        version: "1"
        purpose: Application-level error handling
    optional:
      - name: rusqlite
        version: "0.31"
        features: ["bundled"]
        purpose: Embedded SQLite, only if SQLite was chosen
      - name: r2d2
        version: "0.8"
        purpose: Connection pooling for SQLite, only if SQLite was chosen
      - name: chrono
        version: "0.4"
        purpose: Timestamp formatting and parsing
      - name: tracing
        version: "0.1"
        purpose: Structured logging and diagnostics
      - name: axum
        version: "0.7"
        purpose: Optional thin routing layer over hyper
  build_tools:
    - name: cargo
      version: ">=1.75.0"
      purpose: Rust build system and package manager
    - name: rustfmt
      version: stable
      purpose: Code formatting
    - name: clippy
      version: stable
      purpose: Lint checks
```

MSRV (minimum supported Rust version) is 1.75.0 for stable
`async fn` in traits. The `edition = "2021"` is required in all
`Cargo.toml` files. The `rusqlite` `bundled` feature compiles SQLite
into the binary — no system SQLite library needed.

---

### The module block

What the workspace manifest may name, as
[`schemas/language`](../schemas/language.md#runtime-requirements-the-module-block)
declares it: the engine writes `Cargo.toml` from it and `cargo generate-lockfile`
resolves the versions. The signature algorithm's crate is absent because the
[Primitive Mapping](#primitive-mapping) leaves it UNFILLED, so until it is
named a generation for Rust is refused before any model call, naming that row.

```yaml
module:
  manifest: Cargo.toml
  language_version: "2021"
  requires:
    - {name: tokio, when: always}
    - {name: hyper, when: always}
    - {name: hyper-util, when: always}
    - {name: http-body-util, when: always}
    - {name: serde, when: always}
    - {name: serde_json, when: always}
    - {name: thiserror, when: always}
    - {name: anyhow, when: always}
    - {name: argon2, when: always}
    - {name: aes-gcm, when: always}
    - {name: getrandom, when: always}
    - {name: chrono, when: always}
    - {name: tracing, when: always}
    - {name: tracing-subscriber, when: always}
    - {name: rusqlite, when: the SQLite backend was chosen}
    - {name: r2d2, when: the SQLite backend was chosen}
    - {name: r2d2_sqlite, when: the SQLite backend was chosen}
    - {name: axum, when: the implementation chose axum's router over a match on bare hyper}
  versions: resolved
  written_by: engine
```

`language_version` is the Rust edition every crate's manifest states.

---

## Build and Run

### Build

```bash
# Build entire workspace (debug)
cargo build

# Build release binaries (optimized, single binary per crate)
cargo build --release

# Build specific binary
cargo build --release -p orchestrator
cargo build --release -p <service>
```

### Run

```bash
# Run orchestrator
./target/release/orchestrator --port 9800

# Run agent (connects to orchestrator)
./target/release/<service> --orch http://localhost:9800

# Run directly via cargo (development)
cargo run -p orchestrator -- --port 9800
cargo run -p <service> -- --orch http://localhost:9800
```

### Toolchain and diagnostics

As [`schemas/language`](../schemas/language.md#the-toolchain-block) declares
them. Cargo writes its diagnostics as JSON with `--message-format=json`, so
they are read by pointer rather than by a pattern over rustc's human output.

```yaml
toolchain:
  version: ">=1.75.0"
  probe: {command: [rustc, --version], version: '^rustc ([0-9]+\.[0-9]+\.[0-9]+)'}
  prepare: [[cargo, generate-lockfile]]
  build: [cargo, build, --release, --workspace, --message-format=json]
  build_component: [cargo, build, --release, -p, "{service}", --message-format=json]
  run: ["target/release/{service}"]
  vet: [cargo, clippy, --workspace, --all-targets, --message-format=json, --, -D, warnings]
  env: {CARGO_TERM_COLOR: never}
```

```yaml
diagnostics:
  format: json-lines
  select: {/reason: compiler-message, /message/level: error}
  fields: {message: /message/message, code: /message/code/code, level: /message/level}
  span: {list: /message/spans, where: {/is_primary: true}, file: /file_name, line: /line_start, col: /column_start}
  symbols:
    - {kind: undefined, pattern: '^cannot find (?:value|function|type|struct|trait|macro|module|crate) `(?P<symbol>\w+)`'}
    - {kind: undefined, pattern: '^unresolved import `(?P<symbol>[\w:]+)`'}
    - {kind: redeclared, pattern: '^the name `(?P<symbol>\w+)` is defined multiple times'}
    - {kind: not-implemented, pattern: '^not all trait items implemented, missing: `(?P<symbol>\w+)`'}
    - {kind: method-redeclared, pattern: '^duplicate definitions with name `(?P<symbol>\w+)`'}
  load_failure:
    - "failed to parse manifest"
    - "could not find `Cargo.toml`"
    - "cyclic package dependency"
    - "no targets specified in the manifest"
    - "failed to load manifest for workspace member"
    - "current package believes it's in a workspace when it's not"
  dependency_fault:
    markers:
      - "no matching package named"
      - "failed to select a version for"
      - "failed to load source for dependency"
      - "the lock file needs to be updated"
      - "cannot be built because it requires rustc"
    fix: [[cargo, generate-lockfile]]
  mechanism_failure: '^error: (?:could not compile|linker `[^`]+` not found)'
```

The JSON lines name only rustc's findings. A failure Cargo reports before
rustc runs (a manifest it cannot parse, a dependency it cannot resolve) is on
standard error as text, which is what `load_failure` and `dependency_fault`
read.

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WL_PORT` | no | `9800` | Listen port |
| `WL_ORCH_URL` | for an agent, where an orchestrator is named or running | — | Orchestrator URL for agent registration; the CLI sets it, with `--orch`, only where an orchestrator is named or running ([A component starts with a clean environment](../architecture/cli.md#a-component-starts-with-a-clean-environment)) |
| `WL_DEV` | no | `0` | Set to `1` for in-memory storage mode |
| `RUST_LOG` | no | `info` | Log level filter (`tracing_subscriber`) |

### Cross-Compilation

```bash
# Install cross-compilation tool
cargo install cross

# Build for Linux from macOS
cross build --release --target x86_64-unknown-linux-musl -p orchestrator
```

Produces fully static binaries with musl — deploy as a single file
with no runtime dependencies.

---

## Language Conventions

### Agent Trait

All agents implement a common trait. This is the Rust equivalent of
Go's interface pattern — the trait defines the contract, each agent
provides domain-specific logic.

```rust
#[async_trait::async_trait]
pub trait Agent: Send + Sync {
    fn manifest(&self) -> &AgentManifest;
    async fn execute(&self, req: TaskRequest) -> Result<TaskResult>;
    async fn handle_message(&self, msg: Message) -> Result<()>;
}
```

### Concurrency

- `tokio::spawn` for concurrent agent operations and fire-and-forget tasks
- `tokio::sync::RwLock` for shared registries (agents, channels)
- `tokio::sync::mpsc` for event channels and internal message passing
- `Arc<T>` for shared ownership across async tasks
- No `unsafe` blocks — all concurrency is safe by construction
- HTTP handlers are inherently concurrent (hyper spawns a task per connection)

### IO Safety

- Read request bodies with a size limit enforced via `http_body_util::Limited`
  - Registration/messages: 1 MB (`1 << 20`)
  - Task execution: 10 MB (`10 << 20`)
  - Channel requests: 64 KB (`1 << 16`)
- Apply `tokio::time::timeout` on all outbound HTTP requests

### The HTTP Surface

**Every symbol is spelled from the endpoint's `Operation`.** The architecture
blueprint's `## Endpoints` table declares the operation — `Register`, `Livez`,
`AdminOverview` — and this is how that one name becomes Rust:

| Symbol | Spelling | Example |
|---|---|---|
| Path constant | `pub const PATH_<OPERATION>` in `crates/protocol` | `PATH_REGISTER` |
| Handler | `handle_<operation>` in snake_case | `handle_register` |
| Request type | `<Operation>Request` | `RegisterRequest` |
| Response type | `<Operation>Response` | `RegisterResponse` |

No other spelling is permitted, and no symbol may be named from the path or the
purpose. See [`schemas/common`](../schemas/common.md#declared-names).

The four neutral rules — no path literal, one route table, method matched by
the router, and 405/404 as a structured `ErrorResponse` — are stated once in
[`schemas/platform`](../schemas/platform.md#the-rules-every-platforms-http-surface-obeys).
What follows is only how Rust satisfies them.

**One route table per component.** A component declares its routes as data —
method, path, handler — and one function turns that table into the router,
whether that is a `match` over `(method, path)` on bare hyper or an
`axum::Router` built from the same list. Routing MUST NOT be spread across the
modules that define the handlers.

**Rule 4 is answered by the fallback arm** of the `match`, or by
`axum::Router::fallback`. hyper's own default is an empty body.

**Path parameters are extracted once.** A single helper reads a parameter from a
matched pattern; handlers MUST NOT re-split `uri.path()` themselves, because two
splitters disagree about a trailing slash long before anybody notices.

### Error Handling

- Use `thiserror` for defining error enums in the crate of the blueprint that declares them; the error-code registry is `crates/protocol`'s
- Use `anyhow` for application-level error propagation in binary crates
- Return `Result<T, E>` from all fallible functions — never `unwrap()` or
  `expect()` in production code paths
- HTTP handlers convert errors to structured JSON `ErrorResponse`
- Registration failures are fatal (`std::process::exit(1)`)
- Service broadcast failures are logged and ignored

```rust
#[derive(thiserror::Error, Debug)]
pub enum WebliskError {
    #[error("agent not found: {0}")]
    AgentNotFound(String),
    #[error("task execution failed: {0}")]
    TaskFailed(String),
    #[error("storage error: {0}")]
    Storage(String),
    #[error("serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    #[error("identity error: {0}")]
    Identity(String),
    #[error("rate limited")]
    RateLimited,
}
```

### Logging

- Use `tracing` crate with `tracing-subscriber` for structured JSON logging
- Write the `LogEntry` envelope [`patterns/logging`](../patterns/logging.md) defines, on standard output,
  through a formatter that writes its keys (`ts`, `level` in lower case, `msg`) rather than the crate's own
- Configure with `RUST_LOG` environment variable for level filtering

```rust
tracing_subscriber::fmt()
    .json()
    .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
    .init();

tracing::info!(component = "orchestrator", log_type = "process.startup", port, "server started on port {}", port);
```

### Configuration

- Read the environment variables [listed above](#environment-variables) and those the component's own blueprint declares, via `std::env::var`, and nothing else; a component the CLI starts holds only those ([A component starts with a clean environment](../architecture/cli.md#a-component-starts-with-a-clean-environment))
- Support command-line flags (`--port`, `--orch`) via manual `std::env::args` parsing
- Read no model provider, model name or key from the component's own environment; a component reaches a model only through the tenant's model gateway ([the tenant's model](../architecture/orchestrator.md#the-tenants-model))

---

## Project Structure: Domain Controller

```
bins/<name>/src/main.rs   # entry point — manifest, workflows, start
crates/domains/<name>/    # this controller's aggregation rules and handlers
crates/domain/            # the workflow engine — architecture/domain
crates/agent/             # the same framework a work agent uses
```

Build: `cargo build --release -p <name>`
Run: `./target/release/<name> --port 9700 --orch http://localhost:9800`

The domain controller uses the same agent trait as work agents (6
protocol endpoints). The workflow engine is `crates/domain`'s — see
[architecture/domain.md](../architecture/domain.md) for the execution flow.

---

## Storage Mapping (Rust)

The default backend is **flat-file JSONL** under `.weblisk/data/`, per the
Primitive Mapping table. It satisfies `architecture/storage`'s contract using
`std::fs` alone.

The table below maps each store to a file, and the SQLite layout that follows it
applies **only when SQLite was chosen** when the implementation was commissioned.
An implementation is non-conformant only if it fails the storage contract, never
for the backend it satisfies it with.

See [architecture/storage.md](../architecture/storage.md) for the contract every
backend must meet.

| Store | File | Table |
|-------|------|-------|
| Agent Registry | `.weblisk/data/orchestrator.db` | `agents` |
| Audit Log | `.weblisk/data/orchestrator.db` | `audit_log` |
| Channels | In-memory `HashMap` (short-lived, 1h TTL) | — |
| Strategies | `.weblisk/data/lifecycle.db` | `strategies` |
| Observations | `.weblisk/data/lifecycle.db` | `observations` |
| Recommendations | `.weblisk/data/lifecycle.db` | `recommendations` |
| Feedback | `.weblisk/data/lifecycle.db` | `feedback` |
| Agent Metrics | `.weblisk/data/lifecycle.db` | `agent_metrics` |
| Entity Context | `.weblisk/data/lifecycle.db` | `entity_context` |
| Workflow Executions | `.weblisk/data/workflow.db` | `executions` |
| Task Records | `.weblisk/data/task.db` | `tasks` |

### SQLite Requirements

- Use `rusqlite` with the `bundled` feature (compiles SQLite into the binary,
  no system dependency needed)
- Use `r2d2` + `r2d2_sqlite` for connection pooling across async tasks
- Use `WAL` journal mode for concurrent reads during writes
- Apply `user_version` pragma for schema migrations
- Schema creation on first open (`CREATE TABLE IF NOT EXISTS`)

```rust
use rusqlite::Connection;

fn init_db(path: &str) -> Result<Connection> {
    let conn = Connection::open(path)?;
    conn.pragma_update(None, "journal_mode", "WAL")?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS agents (
            name TEXT PRIMARY KEY,
            version TEXT NOT NULL,
            url TEXT NOT NULL,
            registered_at INTEGER NOT NULL
        );"
    )?;
    Ok(conn)
}
```

### Connection Pooling

```rust
use r2d2::Pool;
use r2d2_sqlite::SqliteConnectionManager;

fn create_pool(path: &str) -> Result<Pool<SqliteConnectionManager>> {
    let manager = SqliteConnectionManager::file(path)
        .with_init(|conn| {
            conn.pragma_update(None, "journal_mode", "WAL")?;
            Ok(())
        });
    let pool = Pool::builder()
        .max_size(8)
        .build(manager)?;
    Ok(pool)
}
```

### Development Mode

When `WL_DEV=1` is set, storage MAY fall back to in-memory `HashMap`
maps for fast iteration. A warning MUST be printed:
`"[dev] using in-memory storage — data will not survive restart"`.

---

## Concurrency (Rust-Specific)

### Agent Concurrency Limiter

```rust
use tokio::sync::Semaphore;
use std::sync::Arc;

pub struct ConcurrencyLimiter {
    semaphore: Arc<Semaphore>,
}

impl ConcurrencyLimiter {
    pub fn new(max: usize) -> Self {
        Self {
            semaphore: Arc::new(Semaphore::new(max)),
        }
    }

    pub fn try_acquire(&self) -> Option<tokio::sync::SemaphorePermit<'_>> {
        self.semaphore.try_acquire().ok()
    }
}
```

Apply in execute/message handlers:

```rust
async fn handle_execute(
    limiter: &ConcurrencyLimiter,
    req: TaskRequest,
) -> Result<hyper::Response<String>> {
    let _permit = match limiter.try_acquire() {
        Some(permit) => permit,
        None => {
            let mut resp = error_response(429, ErrorResponse {
                error: "agent at capacity".into(),
                code: "RATE_LIMITED".into(),
                category: "transient".into(),
                retryable: true,
            });
            resp.headers_mut().insert("Retry-After", hyper::header::HeaderValue::from_static("5"));
            return Ok(resp);
        }
    };
    // ... execute task, permit drops automatically at scope end
}
```

### Domain Dispatch Parallelism

Use `tokio::task::JoinSet` for parallel phase execution within a
dependency level. Use a per-agent semaphore to respect `max_concurrent`
declarations.

```rust
use tokio::task::JoinSet;

async fn dispatch_phase(tasks: Vec<TaskRequest>, agents: &AgentRegistry) -> Vec<TaskResult> {
    let mut set = JoinSet::new();
    for task in tasks {
        let agent = agents.get(&task.target).cloned();
        set.spawn(async move {
            match agent {
                Some(a) => a.execute(task).await,
                None => Err(anyhow::anyhow!("agent not found")),
            }
        });
    }

    let mut results = Vec::new();
    while let Some(res) = set.join_next().await {
        match res {
            Ok(Ok(response)) => results.push(response),
            Ok(Err(e)) => tracing::error!(log_type = "execute.failed", "task failed: {}", e),
            Err(e) => tracing::error!(log_type = "error.unhandled", "join error: {}", e),
        }
    }
    results
}
```

---

## Type Mapping

| Schema Type | Rust Type | Notes |
|-------------|-----------|-------|
| `string` | `String` | Owned string; `&str` for borrows |
| `int` | `i32` | |
| `int64` | `i64` | |
| `integer` | `i64` | No stated width, so the widest (`schemas/common`) |
| `float` | `f64` | |
| `bool` | `bool` | |
| `object` | a struct with `#[derive(Deserialize)]` | Its fields are the declared ones; `HashMap<String, serde_json::Value>` only where none are declared |
| `map` | `HashMap<String, serde_json::Value>` | Its members are undeclared and its values any JSON (`schemas/common`) |
| `list` | `Vec<T>` | Typed vector |
| `uuid` | `String` | Validated format; or `uuid::Uuid` crate |
| `timestamp` | `String` | RFC 3339 UTC with milliseconds (`protocol/conventions:instant`) via `chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Millis, true)` |
| `optional` | `Option<T>` | `#[serde(skip_serializing_if = "Option::is_none")]` |
| `json` | `serde_json::Value` | Arbitrary JSON payload |

### Protocol Type Definitions

```rust
use serde::{Deserialize, Serialize};

// A type's name and fields are protocol/types', under their JSON keys. The
// three below are not restated here: each carries every field protocol/types
// declares for it, and a TaskResult is signed (architecture/agent, POST /v1/execute).

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentManifest { /* every field of protocol/types' AgentManifest */ }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskRequest { /* every field of protocol/types' TaskRequest */ }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResult { /* every field of protocol/types' TaskResult */ }

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Liveness {
    pub live: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Readiness {
    pub ready: bool,
}

/// Sent to POST /v1/lease on the cadence protocol/types (LeaseRenewal) sets
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LeaseRenewal {
    pub ready: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub checks: Option<std::collections::HashMap<String, String>>,
    pub timestamp: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorResponse {
    pub error: String,
    pub code: String,
    pub category: String,
    pub retryable: bool,
}
```

---

## Security

### Memory Safety

- Rust's borrow checker eliminates use-after-free, double-free, and data races
  at compile time — no runtime cost
- No `unsafe` blocks in application code; all memory management is safe by default
- Buffer overflows are caught at compile time via bounds-checked indexing

### Input Validation

- Enforce body size limits on all request reads via `http_body_util::Limited`
  (see IO Safety above)
- Validate JSON structure with `serde` — unknown fields rejected by default
  when `#[serde(deny_unknown_fields)]` is applied
- Enforce maximum sizes per endpoint type

### Cryptography

- The signature algorithm's crate is UNFILLED ([Primitive Mapping](#primitive-mapping)); a generation for Rust is refused until it is named
- `getrandom` for all secure random generation
- Hex encoding via the `hex` crate or manual implementation
- No custom cryptography — use audited crates only

### TLS

- Use `rustls` for TLS termination (pure Rust, no OpenSSL dependency)
- In production: TLS required for all orchestrator ↔ agent communication
- `hyper-rustls` integrates rustls with hyper for HTTPS serving and client

### Dependencies

- All crate dependencies are auditable via `cargo audit`
- Use `cargo deny` to enforce license and vulnerability policies
- `rusqlite` with `bundled` feature eliminates system SQLite dependency
- Pin workspace dependency versions in root `Cargo.toml`

### Key Management

- Private keys stored as files with `0o600` permissions
  (`std::fs::set_permissions`)
- Key directory created with `0o700` permissions
- Environment variables for non-secret configuration only

---

## Testing

### Unit Tests

Rust's built-in test framework — tests live alongside source code:

```bash
# Run all tests
cargo test

# Run tests for a specific crate
cargo test -p protocol
cargo test -p orchestrator
cargo test -p <service>

# Run with output
cargo test -- --nocapture
```

Use parameterized tests for protocol validation:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_manifest_valid() {
        let manifest = AgentManifest {
            name: "example".into(),
            version: "1.0.0".into(),
            capabilities: vec!["analyze".into()],
            actions: vec![],
        };
        assert!(validate_manifest(&manifest).is_ok());
    }

    #[test]
    fn test_validate_manifest_missing_name() {
        let manifest = AgentManifest {
            name: "".into(),
            version: "1.0.0".into(),
            capabilities: vec![],
            actions: vec![],
        };
        assert!(validate_manifest(&manifest).is_err());
    }

    #[tokio::test]
    async fn test_execute_returns_result() {
        let agent = SeoAgent::new();
        let req = TaskRequest {
            task_id: "test-1".into(),
            action: "analyze".into(),
            payload: serde_json::json!({"url": "https://example.com"}),
        };
        let resp = agent.execute(req).await.unwrap();
        assert_eq!(resp.status, "completed");
    }
}
```

### Integration Tests

Integration tests live in a separate `tests/` directory per crate:

```
bins/orchestrator/
  tests/
    registration.rs    # Test agent registration flow end-to-end
    task_routing.rs    # Test task routing to agents
```

- Start orchestrator and agent on random ports in test
- Test task execution end-to-end
- Use `hyper::Client` for HTTP assertions against running servers

```rust
#[tokio::test]
async fn test_registration_flow() {
    let orch = start_test_orchestrator().await;
    let agent = start_test_agent(&orch.url).await;

    let resp = reqwest::get(format!("{}/livez", agent.url)).await.unwrap();
    assert_eq!(resp.status(), 200);

    let liveness: Liveness = resp.json().await.unwrap();
    assert!(liveness.live);
}
```

### Translated tests

A test translated from a criterion
([`schemas/language`](../schemas/language.md#the-tests-block)) is an
integration test of the component's binary crate: one file per criterion under
`bins/{service}/tests/`, which Cargo builds as its own test target with no
manifest change. It is an HTTP black-box test using only the standard library
(`std::net::TcpStream`, HTTP/1.1) and `serde_json`, already a dependency, and
`crates/protocol`'s declared types. It reads the component's address from
`WL_TEST_URL`, and fails, never passes, when that is unset. Cargo's test
output has no stable JSON form, so its result is read from the text lines.

```yaml
tests:
  owns: "bins/*/tests/**"
  path: "bins/{service}/tests/{criterion}.rs"
  name: snake
  header: "// weblisk:criterion {ref} digest {digest} action {action}"
  function: "{criterion}"
  target: WL_TEST_URL
  vectors: testdata/weblisk-vectors/
  command: [cargo, test, -p, "{service}", --test, "{criterion}", --, --exact, "{criterion}"]
  result:
    format: text
    line: '^test (?P<test>\S+) \.\.\. (?P<outcome>ok|FAILED|ignored)$'
    test: test
    outcome: outcome
    pass: ok
    fail: FAILED
    skip: ignored
  stub: >-
    The plan's declared names in crates/protocol, and each component's binary
    answering every route its blueprint declares with 501 and an
    ErrorResponse; a translated test run against it must fail.
```

### CI

```bash
# Format check
cargo fmt --all -- --check

# Lint
cargo clippy --all-targets --all-features -- -D warnings

# Test with race detection (Rust's borrow checker prevents data races,
# but this catches logic errors in concurrent test scenarios)
cargo test

# Security audit
cargo audit
```

---

## Implementation Notes

- The Cargo workspace shares code by depending on the crate of the blueprint
  that specifies it — never by copying a file between crates
- Use `std::env::args` for CLI flag parsing or the `clap` crate if richer
  argument handling is needed
- `rusqlite` with `bundled` compiles SQLite from source — no system library needed
- When `WL_DEV=1`, fall back to in-memory `HashMap` with `tokio::sync::RwLock`
  and print a warning
- Release binaries are optimized — add `[profile.release] lto = true` and
  `strip = true` in workspace `Cargo.toml` for minimal binary size
- `hyper` 1.x is the low-level HTTP implementation; `axum` may be used as
  an optional thin routing layer (document the choice in `Cargo.toml` comments)
- All `async fn` use `tokio` runtime — start with `#[tokio::main]`
- Prefer `Arc<RwLock<T>>` for read-heavy shared state, `Arc<Mutex<T>>` only
  when write contention is expected

### Release Profile

```toml
[profile.release]
lto = true
strip = true
codegen-units = 1
opt-level = 3
```

---

## Verification Checklist

- [ ] One workspace rooted at the tenant folder: a library crate under `crates/` for each blueprint the plan writes code for, named as the layout block gives, and a binary crate under `bins/` for each component, named as it registers — all members of the root `Cargo.toml` `[workspace]`, every dependency's version stated once under `[workspace.dependencies]` ([One workspace, one crate per blueprint](#one-workspace-one-crate-per-blueprint) `rust-workspace-dependencies`, `rust-entry-holds-main`) <!-- wl:check cargo-workspace-contains-weblisk-core-library -->
- [ ] Every routed path is a `pub const PATH_<OPERATION>` in `crates/protocol`; no path literal appears at a registration site, in a client, or in a test ([The HTTP Surface](#the-http-surface)) <!-- wl:check routed-path-pub-const-path-operation -->
- [ ] Each component declares its routes as one table and builds its router from it in one function; no module registers routes beside its handlers ([The HTTP Surface](#the-http-surface)) <!-- wl:check component-declares-routes-table-builds-router -->
- [ ] A wrong method answers 405 with an `Allow` header and an unmatched path answers 404, both as a structured `ErrorResponse` with a registered error code ([The HTTP Surface](#the-http-surface), [`schemas/platform`](../schemas/platform.md#the-rules-every-platforms-http-surface-obeys)) <!-- wl:check wrong-method-answers-405-allow-header -->
- [ ] Path parameters are read through one helper; no handler splits `uri.path()` itself ([The HTTP Surface](#the-http-surface)) <!-- wl:check path-parameters-read-through-helper -->
- [ ] All protocol types (`AgentManifest`, `TaskRequest`, `TaskResult`, `Liveness`, `Readiness`, `LeaseRenewal`, `ErrorResponse`) are defined in `crates/protocol` with `#[derive(Serialize, Deserialize)]`, in no other crate, and shared by every crate that needs them ([Protocol Type Definitions](#protocol-type-definitions), [One workspace, one crate per blueprint](#one-workspace-one-crate-per-blueprint) `rust-declared-names-in-contract`, `rust-one-definition`) <!-- wl:check protocol-types-agentmanifest-taskrequest -->
- [ ] `http_body_util::Limited` is applied on all request body reads, at the limit [IO Safety](#io-safety) gives each kind of request <!-- wl:check http-body-util-limited-applied-request -->
- [ ] All shared state is wrapped in `Arc<tokio::sync::RwLock<T>>` or `Arc<tokio::sync::Mutex<T>>` — no raw `Mutex` or unprotected shared mutable state ([Concurrency](#concurrency), [Implementation Notes](#implementation-notes)) <!-- wl:check shared-state-wrapped-arc-tokio-sync -->
- [ ] Concurrency limiter uses `tokio::sync::Semaphore` and returns 429 with `Retry-After` header and structured `ErrorResponse` when agent is at capacity ([Agent Concurrency Limiter](#agent-concurrency-limiter), [`architecture/agent`](../architecture/agent.md#agent-side-limits)) <!-- wl:check concurrency-limiter-uses-tokio-sync-semaphore -->
- [ ] IF SQLite was chosen: `rusqlite` uses `WAL` journal mode and `user_version` pragma for schema migrations; tables created with `CREATE TABLE IF NOT EXISTS` ([SQLite Requirements](#sqlite-requirements), [Storage Mapping (Rust)](#storage-mapping-rust)) <!-- wl:check sqlite-chosen-rusqlite-uses-wal-journal -->
- [ ] When `WL_DEV=1`, storage falls back to in-memory `HashMap` and prints warning: `"[dev] using in-memory storage — data will not survive restart"` ([Development Mode](#development-mode)) <!-- wl:check when-wl-dev-1-storage-falls -->
- [ ] All fallible functions return `Result<T, E>` — no `unwrap()` or `expect()` in production code paths; HTTP handlers convert errors to JSON `ErrorResponse` ([Error Handling](#error-handling)) <!-- wl:check fallible-functions-return-result-t-e -->
- [ ] No `unsafe` blocks in any application code — all memory safety enforced by the borrow checker ([Memory Safety](#memory-safety), [Concurrency](#concurrency)) <!-- wl:check no-unsafe-blocks-application-code-memory -->
- [ ] Configuration loads from the environment variables this document lists and the component's blueprint declares, and from command-line flags (`--port`, `--orch`); nothing reads a `.env` file, and no model provider, model name or key is read from the environment ([Configuration](#configuration), [Environment Variables](#environment-variables)) <!-- wl:check configuration-loads-environment-variables -->
- [ ] Domain controllers use `tokio::task::JoinSet` for parallel phase execution and a per-agent `Semaphore` respecting `max_concurrent` ([Domain Dispatch Parallelism](#domain-dispatch-parallelism)) <!-- wl:check domain-controllers-use-tokio-task-joinset -->
- [ ] `cargo fmt --check`, `cargo clippy -- -D warnings`, and `cargo audit` pass in CI ([CI](#ci)) <!-- wl:check cargo-fmt-check-cargo-clippy-d -->
