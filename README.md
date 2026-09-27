# Weblisk Blueprints

[![GitHub](https://img.shields.io/badge/github-avaropoint%2Fweblisk--blueprints-blue)](https://github.com/avaropoint/weblisk-blueprints)
[![Part of Weblisk](https://img.shields.io/badge/part%20of-Weblisk-orange)](https://github.com/avaropoint/weblisk)

The specification, architecture, and domain knowledge for the
[Weblisk](https://github.com/avaropoint/weblisk) framework — the
server-side reference architecture and blueprints that power the
Weblisk platform.

## What Is Weblisk

**Weblisk** is an AI-ready collaborative platform for building
autonomous agents that work together across organizations, industries,
and economies. The framework has two parts:

- **[weblisk](https://github.com/avaropoint/weblisk)** — A zero-dependency
  client-side framework for building web interfaces
- **[weblisk-blueprints](https://github.com/avaropoint/weblisk-blueprints)**
  (this repository) — The server-side reference architecture, protocol
  specifications, and domain blueprints that define how orchestrators,
  domains, and agents operate

Together with the **[weblisk-cli](https://github.com/avaropoint/weblisk-cli)**
for code generation and the
**[weblisk-public](https://github.com/avaropoint/weblisk-public)** website,
these form the complete Weblisk platform — operated by
[Avaropoint](https://avaropoint.com/) to deliver solutions for
customers adopting the framework.

Every Weblisk deployment is a **hub** — a self-sovereign node that owns
its orchestrators, domains, agents, logic, and data. Hubs connect to
form a global network of economic intelligence where businesses
collaborate through cryptographically enforced data contracts, replacing
EDI, supply chain middleware, and traditional B2B integrations with a
native, AI-ready model.

Blueprints are implementation-agnostic specifications. They describe
**what** agents and orchestrators must do — not **how** they do it in
any particular language. Server implementations (Go, Node, Cloudflare,
Rust, etc.) build from these blueprints.

### Zero-Dependency Philosophy

Weblisk is built on a zero-external-dependency principle:

- **Client** ([weblisk](https://github.com/avaropoint/weblisk)) — Zero
  dependencies. Pure browser APIs.
- **Server** (these blueprints) — Implementation-agnostic specs. No
  external databases, no runtime package requirements, no vendor SDKs.
- **Go** and **Rust** — programming languages, in
  [`languages/`](languages/README.md). Each states its own dependency
  policy: [`languages/go.md`](languages/go.md),
  [`languages/rust.md`](languages/rust.md).
- **Cloudflare platform** — Platform-native APIs only (Workers KV,
  Durable Objects, Web Crypto). Zero runtime dependencies.
- **Node.js platform** — Recommended libraries for each capability
  (Fastify, better-sqlite3, etc.) are **choices, not requirements**.
  Any library satisfying the same contract is valid.
- **AI models** — The only layer with external dependencies (by
  necessity). Local models (Ollama) are the default; remote providers
  are optional.
- **weblisk-cli** — The single tool for scaffolding, code generation,
  and operations. Feature-parity with blueprints.

## Getting Started

New to Weblisk? Start with the **[Quickstart Guide](QUICKSTART.md)** —
it walks through setting up a hub with one orchestrator, one domain,
and work agents from scratch.

## Structure

Every folder has a README that indexes it, and this page links to them rather
than keeping a second list. The file tree that used to be here was that second
list, and measured on 2026-09-27 eleven of its paths no longer existed, 26
blueprints, schemas and skills in the folders it did list were missing from it,
and six folders were absent altogether.

| Folder | Holds |
|---|---|
| [`protocol/`](protocol/README.md) | Wire protocol — message formats, identity, endpoint contracts, federation |
| [`architecture/`](architecture/README.md) | How the system operates — its components, boundaries, security model and operations |
| [`agents/`](agents/README.md) | Infrastructure agents — system-level services every domain uses |
| [`patterns/`](patterns/README.md) | Cross-cutting pattern contracts, inherited via `extends` |
| [`languages/`](languages/README.md) | One blueprint per programming language |
| [`platforms/`](platforms/README.md) | One blueprint per runtime |
| [`frameworks/`](frameworks/README.md) | What building *with* a framework requires, including the Weblisk client framework's project guidance in `frameworks/weblisk/` |
| [`schemas/`](schemas/README.md) | The schema each blueprint type conforms to, and `kinds.md` |
| [`standards/`](standards/README.md) | Industry standards, as JSON catalogues. The Weblisk project standards it once held are now in [`frameworks/weblisk/`](frameworks/weblisk/README.md) |
| [`programmes/`](programmes/README.md) | Programmes — what a body of work requires in order to exist and to keep running |
| [`positions/`](positions/README.md) | The hand-written half of what can be said about a job somebody holds |
| [`policy-domains/`](policy-domains/README.md) | What a subject area of governance covers, and what a programme claiming it must provide |
| [`intl/`](intl/README.md) | Reserved for locale and spoken-language constructs |
| [`skills/`](skills/README.md) | Guides for a coding agent — not specifications |

Why the corpus is divided this way is [`CORPUS_SHAPE.md`](CORPUS_SHAPE.md).

### Architecture Hierarchy

```
Hub (self-sovereign deployment)
  └── Application Gateway (end-user edge security)
       ├── Browser Sessions (cryptographic session binding)
       ├── ABAC Policy Engine (attribute-based access control)
       ├── Rate Limiting (token bucket / sliding window)
       ├── Route Protection (URL → agent mediation)
       └── Response Middleware (application-configured response processing)
  └── Admin Gateway (operator edge — separate domain/network)
       ├── Operator ML-DSA-65 Auth + MFA (always required)
       ├── IP Allowlist / VPN / mTLS
       └── 4-Eyes Destructive Action Approval
  └── Orchestrator (trust anchor)
       ├── Registration + Namespace Control
       ├── Service Directory + Routing Table
       ├── Admin API (operator management, dashboard)
       ├── CLI Operations (terminal interrogation)
       ├── Observability (logging, tracing, metrics)
       └── Domain Controllers (directors)
            └── Work Agents (task executors)
       └── Infrastructure Agents (system utilities)
            ├── Workflow Agent (DAG execution engine)
            ├── Task Agent (dispatch + priority queue)
            ├── Lifecycle Agent (strategies, observations, approvals)
            ├── Alerting Agent (notification routing)
            ├── Incident Response Agent (runbooks, remediation)
            ├── Health Monitor Agent (internal hub health)
            └── Hub Agent (registry — indexing, search, metrics, verification, alerting)
  └── Marketplace (buy, sell, share capabilities, blueprints, templates)
  └── Enforcement (non-bypassable boundary inspection, rogue agent detection)
  └── Data Security (transport encryption, scope-aware boundaries, opt-in data primitives)
  └── Threat Model (attack surface analysis, OWASP coverage)
  └── Federation (hub-to-hub collaboration)
  └── Cross-Cutting Patterns (inherited via extends)
       ├── Scope (universal classification — 5-level, propagation, environments)
       ├── Policy (declarative rules engine — evaluation, precedence)
       ├── Safety (operation classification — protection gates, kill-switch, quarantine)
       ├── Approval (intent-based approval — multi-party, emergency override)
       ├── Privacy (consent, masking, anonymization, erasure cascade)
       ├── Contract (collaboration agreements — scope-aware, permissions)
       ├── Governance (compliance profiles, evidence, directives)
       ├── Security (transport, input validation, zero-trust, threat events)
       ├── Observability (health, metrics, state tracking, alerts)
       ├── Workflow (declaration, execution engine, approval gates)
       ├── Notification (multi-channel delivery, templates, throttling)
       └── and the rest — see patterns/README.md
```

### Component Descriptions

- **Hub** — A complete Weblisk deployment: orchestrator, domains, agents, data, and policies under one owner's control
- **Orchestrator** — Trust anchor: manages registration, namespace ownership, service directory distribution, channel brokering. Does NOT execute tasks or manage strategies
- **Admin** — Separate admin gateway (different domain, different network, different auth model), operator ML-DSA-65 identity, mandatory MFA, IP allowlisting, 4-eyes approval for destructive actions
- **CLI** — Terminal commands for system interrogation and management
- **Observability** — Structured JSON logs, distributed trace propagation, structured metrics
- **Gateway** — Application edge security agent: end-user authentication, ABAC authorization, rate limiting, route protection, request mediation, response sanitization. Separate from admin gateway
- **Browser Sessions** — Cryptographically-bound sessions with ML-DSA-65 signing, device binding, island-aware concurrency, and failover continuity
- **Data Security** — Transport encryption, ML-DSA-65 message integrity, scope-aware federation boundaries, response sanitization, framework audit trail. Provides opt-in data-level primitives (scope, policy, privacy, enforcement) for agents handling sensitive data
- **Threat Model** — 5-boundary attack surface analysis (38+ vectors), OWASP Top 10 mapping, attack chain analysis, residual risk register
- **Domains** — Own a business function, define workflows, publish workflow triggers, receive results via scoped events
- **Work Agents** — Perform specific tasks dispatched by the Task Agent (see the [starter template](https://github.com/avaropoint/weblisk-templates/tree/main/server/starter) for a working example)
- **Infrastructure Agents** — Provide system services (workflow execution, task dispatch, lifecycle optimization, alerting, incident response, health monitoring, hub registry, sync, cron, email, webhooks) used by any domain
- **Marketplace** — Built into the hub — buy, sell, and share capabilities, blueprints, agents, and templates. Supports live services (invoked over federation) and installable assets (generated into your own hub). [weblisk.dev](https://weblisk.dev) serves as the public directory
- **Patterns** — Cross-cutting concerns (scope, policy, safety, approval, privacy, contract, security, governance, observability, workflow, task dispatch, alerting, scheduling, data sync, incident response, notification, HTTP-based pub/sub messaging, retry, rate limiting, storage, caching, state machines, secrets, logging, versioning, command, interop adapters) and API patterns (REST, AI, auth, webhooks, real-time, file upload, user management, deployment) that apply across all agents via `extends` inheritance. Every infrastructure agent has a matching pattern that formalizes its platform-wide contract — the pattern defines WHAT, the agent implements HOW. The full list is [patterns/README.md](patterns/README.md)
- **Federation** — Hub-to-hub trust, data contracts, and cross-boundary task execution

### Free vs Pro

This repository contains all **free tier** blueprints — the complete
architecture, protocol, federation, hub collaboration, marketplace,
four reference domains (SEO, Content, Health, Security), infrastructure
agents (alerting, incident response, health monitoring, hub registry,
sync, cron, email, webhooks), API patterns (including user management,
file upload, rate limiting, retry, and deployment), enterprise security
(gateway, browser sessions, data security), operational tooling (admin
dashboard, CLI, observability), and schema governance.
These match the
[Blueprint Catalog](https://weblisk.dev/blueprints/catalog.html) and
[Agent Catalog](https://weblisk.dev/agents/catalog.html). Everything here
is open source and ships with every Weblisk hub.

Pro patterns and agents (crdt-sync, search-index,
email-transactional, ai-agent, search-agent, media-agent, analytics-agent)
are available through [Weblisk Pro](https://weblisk.dev/pro.html) or
via [Avaropoint](https://avaropoint.com/) for enterprise engagements.

## Usage

### With the Weblisk CLI

The [weblisk-cli](https://github.com/avaropoint/weblisk-cli) supports
multiple blueprint sources. This repository serves as the **core**
source — always available as a fallback. Custom, partner, and
customer-owned blueprint repos can be added alongside it.

```bash
# The CLI clones this repo automatically on first use
weblisk server init --platform go

# Generate a domain controller from an example blueprint
weblisk domain create seo --platform go

# Generate a work agent
weblisk agent create seo-analyzer --platform go

# Force re-fetch all blueprint sources
weblisk blueprint update
```

### Multiple Blueprint Sources

The CLI resolves blueprints in priority order:

1. **Local project** — `./patterns/` in the user's project
2. **Custom sources** — additional repos via configured blueprint sources
3. **Core** — this repository (always present)

Custom sources override core blueprints with the same path. For example,
a customer's `domains/checkout.md` takes precedence over the core version.

Blueprint sources are configured via runtime configuration (e.g.,
environment variable, config file, or CLI flag). Multiple sources
are separated by newlines or commas:

```yaml
# Example configuration
blueprint_sources:
  - https://github.com/acme-corp/acme-blueprints.git
  - https://github.com/acme-corp/acme-blueprints-internal.git
```

**Source format:**

| Format | Example | Notes |
|--------|---------|-------|
| HTTPS | `https://github.com/org/repo.git` | Uses git credential helper |
| SSH | `git@github.com:org/repo.git` | Uses SSH key |
| Branch/tag | `https://github.com/org/repo.git@v2.0` | Pin to ref after `@` |
| Local path | `file:///path/to/local/blueprints` | For development |

**Authentication:** The CLI uses the system's existing Git credentials —
SSH keys, credential helpers, or GitHub CLI auth. No additional configuration
is needed beyond what `git clone` already uses.

**Update behavior:** `weblisk blueprint update` performs a `git pull` on each
cached source. Sources are cached in `~/.weblisk/blueprints/`. If a source is
unreachable, the CLI uses the last cached version and logs a warning.

This supports multiple distribution models:

| Source Type | Example | Typical Access |
|---|---|---|
| Core (open source) | `avaropoint/weblisk-blueprints` | Public, always available |
| Vertical/partner | `avaropoint/weblisk-blueprints-ecommerce` | Granted per-customer |
| Customer-owned | `acme-corp/acme-blueprints` | Customer's own repo |
| Local project | `./patterns/` | Project-scoped, checked in |

Access control is handled entirely by Git — private repos require the
user's existing credentials (SSH key or GitHub CLI auth).

### Building Your Own

1. Read the [Quickstart Guide](QUICKSTART.md) to get a hub running
2. Read the [Blueprint Schema](SCHEMA.md) for the standard structure
3. Create a domain blueprint for your agent's expertise
4. Reference the protocol and architecture blueprints
5. Use the [weblisk-cli](https://github.com/avaropoint/weblisk-cli)
   or your preferred AI model to generate the implementation

## Blueprint Schema

Every blueprint follows a [standard schema](SCHEMA.md) with required sections:
metadata header, overview, specification, types, implementation notes,
and verification checklist. See the schema file for details.

## Creating Domain Controllers

Domain controllers own a business function. They define workflows, dispatch
work to agents, aggregate results, and drive the feedback loop. The sections a
domain blueprint MUST include, in order, are listed in
[schemas/domain.md](schemas/domain.md#required-section-order).

See the [starter template](https://github.com/avaropoint/weblisk-templates/tree/main/server/starter)
for a reference showing a complete domain controller. See
[architecture/domain.md](architecture/domain.md)
for the full specification.

## Creating API Patterns

API patterns define declarative specifications for common server-side
functionality. The sections a pattern blueprint MUST include, in order, are
listed in [schemas/pattern.md](schemas/pattern.md#required-section-order).

See [patterns/api-rest.md](patterns/api-rest.md) for a complete example.

## Creating Agent Definitions

Agent definitions describe work agents (domain-dispatched) or infrastructure
agents (system-level services). The sections an agent blueprint MUST include,
in order, are listed in [schemas/agent.md](schemas/agent.md#required-section-order).

See the [starter template](https://github.com/avaropoint/weblisk-templates/tree/main/server/starter)
for a working example including both a domain and a work agent. See
[agents/alerting.md](agents/alerting.md) for an infrastructure agent example.

## Related Repositories

| Repository | Description |
|---|---|
| [weblisk](https://github.com/avaropoint/weblisk) | Zero-dependency client-side framework |
| [weblisk-blueprints](https://github.com/avaropoint/weblisk-blueprints) | Server-side reference architecture and blueprints (this repo) |
| [weblisk-cli](https://github.com/avaropoint/weblisk-cli) | CLI for code generation, blueprint management, and hub operations |
| [weblisk-public](https://github.com/avaropoint/weblisk-public) | Public website — [weblisk.dev](https://weblisk.dev) |

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/my-blueprint`)
3. Follow the [Blueprint Schema](SCHEMA.md) for new blueprints
4. Commit your changes (`git commit -m 'Add new blueprint'`)
5. Push to the branch (`git push origin feature/my-blueprint`)
6. Open a Pull Request

## License

MIT
