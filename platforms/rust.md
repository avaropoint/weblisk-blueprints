<!-- blueprint
type: platform
name: rust
version: 1.0.0
requires: [protocol/identity, protocol/types, architecture/orchestrator, architecture/agent, architecture/domain, architecture/lifecycle, architecture/storage, architecture/gateway, patterns/deployment]
platform: rust
tier: free
-->

# Platform: Rust Implementation

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
mapping with rusqlite, and Rust-specific idioms for error handling,
trait-based abstractions, and type safety.

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

### Workspace Layout

Rust uses a Cargo workspace to share types and protocol code between
the orchestrator and agents without copying files. A shared library
crate (`weblisk-core`) contains all protocol types, identity handling,
and storage interfaces — each binary crate depends on it.

```
weblisk-app/
  Cargo.toml                  # Workspace root — lists all members
  weblisk-core/
    Cargo.toml                # Library crate for shared types
    src/
      lib.rs                  # Re-exports all modules
      protocol.rs             # Protocol types (AgentManifest, TaskRequest, etc.)
      identity.rs             # Ed25519 key management, signing, tokens
      storage.rs              # Storage trait + SQLite implementation
      error.rs                # Error types (thiserror)
      config.rs               # Configuration loader (env vars, CLI flags, .env)
  server/
    Cargo.toml                # Binary crate — depends on weblisk-core
    src/
      main.rs                 # Entry point — configure and start orchestrator
      orchestrator.rs         # HTTP server: registration, routing, channels, audit
      handlers.rs             # HTTP handler functions
  agents/<name>/
    Cargo.toml                # Binary crate — depends on weblisk-core
    src/
      main.rs                 # Entry point — configure manifest, create agent, start
      agent.rs                # Agent HTTP server, registration, messaging
      <name>.rs               # Domain-specific logic (execute + handle_message)
```

### Workspace Cargo.toml

```toml
[workspace]
members = [
    "weblisk-core",
    "server",
    "agents/*",
]
resolver = "2"

[workspace.dependencies]
tokio = { version = "1", features = ["full"] }
hyper = { version = "1", features = ["full"] }
hyper-util = { version = "0.1", features = ["tokio"] }
http-body-util = "0.1"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
ed25519-dalek = { version = "2", features = ["rand_core"] }
rand = "0.8"
rusqlite = { version = "0.31", features = ["bundled"] }
r2d2 = "0.8"
r2d2_sqlite = "0.24"
thiserror = "1"
anyhow = "1"
chrono = { version = "0.4", features = ["serde"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["json"] }
```

### Orchestrator

```
server/
  Cargo.toml          # [dependencies] weblisk-core = { path = "../weblisk-core" }
  src/
    main.rs           # Entry point — configure and start orchestrator
    orchestrator.rs   # HTTP routing, registration, channels, audit
    handlers.rs       # Handler functions for each endpoint
```

Build: `cargo build --release -p server`
Run: `./target/release/server --port 9800`

### Agent

```
agents/<name>/
  Cargo.toml          # [dependencies] weblisk-core = { path = "../../weblisk-core" }
  src/
    main.rs           # Entry point — configure manifest, create agent, start
    agent.rs          # Agent base: HTTP server, registration, messaging
    <name>.rs         # Domain-specific Execute + HandleMessage
```

Build: `cargo build --release -p weblisk-agent-<name>`
Run: `./target/release/weblisk-agent-seo --port 9710 --orch http://localhost:9800`

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
      - name: ed25519-dalek
        version: "2"
        purpose: Ed25519 key generation, signing, verification
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
        purpose: Embedded SQLite for production persistence
      - name: r2d2
        version: "0.8"
        purpose: Connection pooling for SQLite
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

## Build and Run

### Build

```bash
# Build entire workspace (debug)
cargo build

# Build release binaries (optimized, single binary per crate)
cargo build --release

# Build specific binary
cargo build --release -p server
cargo build --release -p weblisk-agent-seo
```

### Run

```bash
# Run orchestrator
./target/release/server --port 9800

# Run agent (connects to orchestrator)
WL_AI_PROVIDER=ollama WL_AI_MODEL=llama3 \
  ./target/release/weblisk-agent-seo --orch http://localhost:9800

# Run directly via cargo (development)
cargo run -p server -- --port 9800
cargo run -p weblisk-agent-seo -- --orch http://localhost:9800
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WL_PORT` | no | `9800` | Listen port |
| `WL_AI_PROVIDER` | yes | — | LLM provider (`ollama`, `openai`, `anthropic`) |
| `WL_AI_MODEL` | yes | — | Model name for LLM provider |
| `WL_ORCH_URL` | yes (agents) | — | Orchestrator URL for agent registration |
| `WL_DEV` | no | `0` | Set to `1` for in-memory storage mode |
| `RUST_LOG` | no | `info` | Log level filter (`tracing_subscriber`) |

### Cross-Compilation

```bash
# Install cross-compilation tool
cargo install cross

# Build for Linux from macOS
cross build --release --target x86_64-unknown-linux-musl -p server
```

Produces fully static binaries with musl — deploy as a single file
with no runtime dependencies.

---

## Platform-Specific Conventions

### Agent Trait

All agents implement a common trait. This is the Rust equivalent of
Go's interface pattern — the trait defines the contract, each agent
provides domain-specific logic.

```rust
#[async_trait::async_trait]
pub trait Agent: Send + Sync {
    fn manifest(&self) -> &AgentManifest;
    async fn execute(&self, req: TaskRequest) -> Result<TaskResponse>;
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

### Error Handling

- Use `thiserror` for defining error enums in `weblisk-core`
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
    Storage(#[from] rusqlite::Error),
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
- Include `component`, `trace_id`, and `timestamp` in all log entries
- Configure with `RUST_LOG` environment variable for level filtering

```rust
tracing_subscriber::fmt()
    .json()
    .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
    .init();

tracing::info!(component = "orchestrator", "server started on port {}", port);
```

### Configuration

- Use environment variables (`WL_AI_*`, `WL_ORCH_*`) via `std::env::var`
- Support command-line flags (`--port`, `--orch`) via manual `std::env::args` parsing
- Load `.env` file from working directory if present (manual parser or `dotenvy` crate)

---

## Project Structure: Domain Controller

```
domains/<name>/
  Cargo.toml           # [dependencies] weblisk-core = { path = "../../weblisk-core" }
  src/
    main.rs            # Entry point — manifest, workflows, start
    domain.rs          # Domain controller: workflow engine, dispatch, aggregation
    workflows.rs       # Workflow definitions (parsed from embedded YAML or code)
    <name>.rs          # Domain-specific aggregation rules and HandleMessage
```

Build: `cargo build --release -p weblisk-domain-<name>`
Run: `./target/release/weblisk-domain-seo --port 9700 --orch http://localhost:9800`

The domain controller uses the same agent trait as work agents (6
protocol endpoints). The workflow engine lives in `domain.rs` — see
[architecture/domain.md](../architecture/domain.md) for the execution flow.

---

## Storage Mapping (Rust / SQLite)

The Rust platform uses SQLite via `rusqlite` for persistent storage.
Each component gets its own database file under `.weblisk/data/`.

See [architecture/storage.md](../architecture/storage.md) for the
abstract storage interface.

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
            return Ok(error_response(429, ErrorResponse {
                error: "agent at capacity".into(),
                code: "RATE_LIMITED".into(),
                category: "transient".into(),
                retryable: true,
            }));
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

async fn dispatch_phase(tasks: Vec<TaskRequest>, agents: &AgentRegistry) -> Vec<TaskResponse> {
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
            Ok(Err(e)) => tracing::error!("task failed: {}", e),
            Err(e) => tracing::error!("join error: {}", e),
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
| `int64` | `i64` | Used for timestamps |
| `float` | `f64` | |
| `bool` | `bool` | |
| `object` | `HashMap<String, serde_json::Value>` | Or typed struct with `#[derive(Deserialize)]` |
| `list` | `Vec<T>` | Typed vector |
| `uuid` | `String` | Validated format; or `uuid::Uuid` crate |
| `timestamp` | `i64` | Unix epoch seconds via `chrono::Utc::now().timestamp()` |
| `optional` | `Option<T>` | `#[serde(skip_serializing_if = "Option::is_none")]` |
| `json` | `serde_json::Value` | Arbitrary JSON payload |

### Protocol Type Definitions

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentManifest {
    pub name: String,
    pub version: String,
    pub capabilities: Vec<String>,
    pub actions: Vec<Action>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskRequest {
    pub task_id: String,
    pub action: String,
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResponse {
    pub task_id: String,
    pub status: String,
    pub result: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    pub status: String,
    pub component: String,
    pub version: String,
    pub uptime_seconds: i64,
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

- `ed25519-dalek` for key generation, signing, and verification
- `rand` crate with `OsRng` for all secure random generation
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
cargo test -p weblisk-core
cargo test -p server
cargo test -p weblisk-agent-seo

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
            name: "seo".into(),
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
server/
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

    let resp = reqwest::get(format!("{}/health", agent.url)).await.unwrap();
    assert_eq!(resp.status(), 200);

    let health: HealthStatus = resp.json().await.unwrap();
    assert_eq!(health.status, "healthy");
}
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

- Cargo workspace shares code via the `weblisk-core` library crate — no file
  copying between binaries (unlike Go's copy-each-file approach)
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

- [ ] Cargo workspace contains `weblisk-core` library crate, `server` binary crate, and one or more `agents/<name>` binary crates — all listed in root `Cargo.toml` `[workspace]` members
- [ ] All protocol types (`AgentManifest`, `TaskRequest`, `TaskResponse`, `HealthStatus`, `ErrorResponse`) are defined in `weblisk-core` with `#[derive(Serialize, Deserialize)]` and shared across all binary crates
- [ ] `http_body_util::Limited` is applied on all request body reads: 1 MB for registration/messages, 10 MB for tasks, 64 KB for channels
- [ ] All shared state is wrapped in `Arc<tokio::sync::RwLock<T>>` or `Arc<tokio::sync::Mutex<T>>` — no raw `Mutex` or unprotected shared mutable state
- [ ] Concurrency limiter uses `tokio::sync::Semaphore` and returns 429 with `Retry-After` header and structured `ErrorResponse` when agent is at capacity
- [ ] `rusqlite` uses `WAL` journal mode and `user_version` pragma for schema migrations; tables created with `CREATE TABLE IF NOT EXISTS`
- [ ] When `WL_DEV=1`, storage falls back to in-memory `HashMap` and prints warning: `"[dev] using in-memory storage — data will not survive restart"`
- [ ] All fallible functions return `Result<T, E>` — no `unwrap()` or `expect()` in production code paths; HTTP handlers convert errors to JSON `ErrorResponse`
- [ ] No `unsafe` blocks in any application code — all memory safety enforced by the borrow checker
- [ ] Configuration loads from environment variables (`WL_*`), command-line flags (`--port`, `--orch`), and `.env` file from working directory
- [ ] Domain controllers use `tokio::task::JoinSet` for parallel phase execution and a per-agent `Semaphore` respecting `max_concurrent`
- [ ] `cargo fmt --check`, `cargo clippy -- -D warnings`, and `cargo audit` pass in CI
