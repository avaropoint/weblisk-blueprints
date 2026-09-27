# Platform Bindings

Platform blueprints provide implementation guidance for specific runtime
environments. Each platform binding translates the abstract framework
specifications (agents, domains, protocols) into concrete guidance for
a target runtime — dependencies, project structure, code patterns, and
deployment considerations.

Go and Rust are not here. They are programming languages whose runtime is a
binary, and their blueprints are in [`languages/`](../languages/README.md) — see
that page for why they moved and Node did not.

## Server, Not Client

**These blueprints govern server-side components** — how an orchestrator, an
agent, a domain controller or an administrative service is laid out, named,
built and run in one language.

**Client output is a framework's concern** — the HTML, CSS and JavaScript a
browser receives, in `frameworks/<name>/`. Those conventions are different in kind: `frameworks/weblisk/code.md` declares
`file_naming: kebab-case`, which is right for a stylesheet and wrong for Go.

A platform blueprint's job is translation. The specification blueprints state
requirements in terms of algorithms, formats and behaviour; a platform blueprint
says what those become on one runtime, and names the package for each blueprint
that specifies it.


Blueprints are implementation-agnostic. Platforms make them concrete.

## A platform is not a provider

A **platform** is the runtime a component is generated *for* — Node, Cloudflare
Workers. It answers *where does this code execute, and what does that offer.*
What the code is written in is a **language**, in
[`languages/`](../languages/README.md).

A **provider** is a service an organisation uses and applies policy to —
Microsoft 365, Google Workspace, AWS, Cloudflare. It answers *whose service is
this, and does its configuration satisfy our policy.* Providers are a kind, in
[`schemas/kinds.md`](../schemas/kinds.md); platforms are not.

**One vendor can be both**, and Cloudflare is the clearest case: a platform when
you generate Workers for it, a provider when you govern the account. Two
relationships with one company, asking two different questions — which is why
they are two words rather than one.

## Platform Blueprints

| Platform | Runtime | Key Characteristics |
|----------|---------|---------------------|
| [cloudflare.md](cloudflare.md) | Cloudflare Workers | Durable Objects, KV, Web Crypto, edge-native |
| [node.md](node.md) | Node.js / TypeScript | Fastify, better-sqlite3, ML-DSA-65, flexible |

The Go and Rust bindings are [`languages/go.md`](../languages/go.md) and
[`languages/rust.md`](../languages/rust.md).

## Zero-Dependency Principle

Each platform follows the framework's zero-external-dependency
philosophy within its ecosystem:

- **Cloudflare** — Platform-native APIs only (Workers KV, Durable Objects, Web Crypto).
- **Node.js** — Recommended libraries (Fastify, better-sqlite3) are choices, not requirements.

A language blueprint states its own dependency policy — Go's and Rust's are in
[`languages/`](../languages/README.md).

## How Platforms Are Used

The CLI uses platform bindings during code generation:

```bash
weblisk server init --platform node
weblisk agent create my-agent --platform cloudflare
```

The platform blueprint tells the LLM which language features, libraries,
and project structure to use when generating code from agent/domain specs.

The flag still selects a language too: `--platform go` and `--platform rust`
resolve to [`languages/go.md`](../languages/go.md) and
[`languages/rust.md`](../languages/rust.md). Separate `--language` and
`--platform` flags are step 3 of [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md), not
yet done.

## Schema

Platform blueprints conform to [schemas/platform.md](../schemas/platform.md).
