---
name: rust
description: Rust-only facts for a tenant generated with --platform rust — the Cargo workspace layout, the shared-crate rule, and the error and concurrency rules that fail review. Use before editing routing, handlers, or anything under weblisk-core in a Rust tenant.
---

# Rust

`platforms/rust.md` is the specification. This skill is the facts that
fail a build or a review, plus the workspace the generator already
followed.

## Layout

**A Cargo workspace, not a crate.** The root `Cargo.toml` lists every
member. `weblisk-core` is a library crate holding all protocol types,
identity, storage traits, errors and config; `server` and each
`agents/<name>` are binary crates that depend on it.

Shared code is depended on, never copied. A protocol type defined twice
in two binary crates is two types, and they will not interoperate.

## Rules that bite

**1. Protocol types live in `weblisk-core`.** `AgentManifest`,
`TaskRequest`, `TaskResponse`, `HealthStatus` and `ErrorResponse` are
defined once, with `#[derive(Serialize, Deserialize)]`, and shared.

**2. No path literals reach routing.** Paths are `pub const
PATH_<OPERATION>` in `weblisk-core`. Each component builds its router
from one route table in one function.

**3. No `unwrap()` or `expect()` on a production path.** Every fallible
function returns `Result<T, E>`; handlers convert errors into a JSON
`ErrorResponse`. A panic in a handler takes the task with it.

**4. No `unsafe`.** Memory safety is the borrow checker's job here.

**5. Shared state is `Arc<tokio::sync::RwLock<T>>` or
`Arc<tokio::sync::Mutex<T>>`** — never a raw `std::sync::Mutex` held
across an await, which deadlocks the runtime.

**6. Bound every request body.** `http_body_util::Limited`: 1 MB for
registration and messages, 10 MB for tasks, 64 KB for channels.

## Before you say it works

```
cargo build --release && cargo clippy -- -D warnings && cargo fmt --check
weblisk server verify
```
