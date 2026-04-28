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
- **Go platform** — Standard library only. SQLite compiles into the
  binary (embedded, not an external server).
- **Rust platform** — Minimal curated crates (tokio, hyper, serde,
  rusqlite). Compiles to a single static binary per agent.
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

```
protocol/           Wire protocol specifications
  spec.md             Full protocol specification (6 agent + 6 orchestrator endpoints)
  identity.md         Ed25519 crypto, tokens, signing, key rotation
  types.md            Canonical type definitions (all JSON shapes)
  federation.md       Multi-orchestrator federation and data boundaries

architecture/       System architecture
  orchestrator.md     Trust anchor — registration, namespaces, security, directory
  domain.md           Domain controller — workflow declarations, event-driven triggering
  agent.md            Agent base — 6 endpoints, capabilities, pub/sub, retry/circuit breaker
  lifecycle.md        Continuous optimization loop (event-driven)
  storage.md          Abstract persistence interface
  testing.md          Conformance test suite specification
  hub.md              Collaborative hub — discovery, tiers, commerce
  admin.md            Platform admin — operator identity, roles, separate admin gateway
  cli.md              CLI operations — interrogation, management commands
  observability.md    Structured logging, distributed tracing, metrics
  gateway.md          Application gateway — auth, ABAC, rate limiting, route protection
  client.md          Client architecture — taxonomy, trust levels, sessions, data boundary
  data-security.md    Transport security, scope-aware boundaries, opt-in data primitives
  enforcement.md      Non-bypassable boundary inspection, rogue agent detection
  threat-model.md     Attack surface analysis — 5 boundaries, OWASP mapping
  change-management.md  Versioning, migration, deprecation lifecycle

platforms/          Implementation guidance per runtime
  go.md               Go (stdlib only, local processes)
  cloudflare.md       Cloudflare Workers (Durable Objects, KV)
  node.md             Node.js/TypeScript (Fastify, Ed25519, SQLite)
  rust.md             Rust (tokio, hyper, serde, rusqlite)

agents/             Infrastructure agents (system-level services)
  workflow.md         Workflow execution engine — DAG resolution, phase coordination
  task.md             Task dispatch and tracking — priority queue, concurrency control
  lifecycle.md        Continuous optimization — strategies, observations, approvals
  alerting.md         Notification routing and delivery
  incident-response.md  Automated incident detection, runbooks, remediation
  health-monitor.md   Internal hub health — agent liveness, storage, gateway
  hub.md              Registry hub — indexing, search, metrics, verification, alerting
  sync.md             Background data sync (client ↔ server)
  cron.md             Scheduled task execution
  webhook.md          Webhook processing (inbound + outbound)
  email-send.md       Transactional email sending

patterns/           Declarative API and cross-cutting pattern specifications
  api-rest.md         REST API with CRUD, pagination, filtering, sorting
  api-ai.md           AI gateway — chat, completions, extraction, embeddings
  realtime-chat.md    WebSocket messaging with channels, presence, history
  auth-session.md     Session-based auth with secure cookies, CSRF
  auth-token.md       JWT and API key auth with refresh tokens, scopes
  user-management.md  User lifecycle — profiles, roles, password reset, OAuth
  file-upload.md      File upload, processing, CDN delivery, signed URLs
  deployment.md       CI/CD pipelines, containerization, environment management
  webhook.md          Webhook processing — inbound validation, outbound delivery
  rate-limiting.md    Token bucket, sliding window — gateway and agent rate limits
  retry.md            Retry strategies, circuit breaker, timeout management
  command.md          Agent command interface — dispatch, routing, execution
  contract.md         Collaboration agreements — schemas, scope, permissions, versioning
  scope.md            Universal classification — 5-level scope, propagation, environment profiles
  policy.md           Declarative rules engine — evaluation, composition, precedence
  safety.md           Operation classification — protection gates, kill-switch, quarantine
  approval.md         Intent-based approval — authority routing, multi-party, emergency override
  privacy.md          Consent, masking, anonymization, minimization, erasure cascade
  governance.md       Compliance profiles, evidence collection, governance directives
  domain-controller.md  Domain controller base — dispatch, aggregation, lifecycle
  logging.md          Structured JSON logging — levels, correlation, rotation
  messaging.md        HTTP-based pub/sub — event envelopes, scoping, namespace ownership
  notification.md     Multi-channel notification — email, webhook, Slack, SMS, push
  observability.md    Health endpoints, metrics envelope, component state tracking
  secrets.md          Secret lifecycle — storage, rotation, access control
  security.md         Transport security, input validation, zero-trust, threat events
  state-machine.md    Declarative state machines — transitions, guards, side effects
  storage.md          Agent-level persistence — schema, migration, backup
  caching.md          In-process caching — LRU, TTL, namespaces, AI response cache
  interop.md          Framework adapters — LangChain, CrewAI, ADK, HTTP service wrappers
  versioning.md       Semantic versioning, compatibility rules, deprecation
  workflow.md         Workflow declaration, event-driven DAG execution, approval gates
  expression.md       Expression language — guards, conditions, constraints, policy rules
  task-dispatch.md    Task submission, priority queuing, dispatch protocol, dead-letter
  alerting.md         Alert rule evaluation, severity routing, dedup, escalation, muting
  scheduling.md       Cron expressions, overlap policy, missed-tick handling, distributed locking
  offline.md          Offline operation — sync, client persistence, encryption, revocation
  incident-response.md  Incident lifecycle, runbook execution, correlation, post-mortem

schemas/            Blueprint schema governance
  README.md           Schema governance overview
  common.md           Common rules across all blueprint types
  compliance.md       Automated compliance validation rules
  agent.md            Agent blueprint schema (22 sections)
  architecture.md     Architecture blueprint schema
  domain.md           Domain controller blueprint schema
  pattern.md          Pattern blueprint schema
  platform.md         Platform blueprint schema
  protocol.md         Protocol blueprint schema

examples/           Reference domain controllers and work agents
  domains/
    seo.md            SEO domain — workflows, agents, scoring, strategy alignment
    content.md        Content quality — readability, structure, metadata scoring
    health.md         Health monitoring — uptime, performance, TLS, trend analysis
    security.md       Security domain — OWASP, CSP, headers, dependency auditing
  agents/
    seo-analyzer.md   SEO analysis work agent (domain: seo)
    a11y-checker.md   Accessibility checking work agent (domain: seo)
    content-analyzer.md  Content quality analysis work agent (domain: content)
    meta-checker.md   HTML metadata validation work agent (domain: content)
    uptime-checker.md Endpoint availability work agent (domain: health)
    perf-auditor.md   Page performance audit work agent (domain: health)
    security-scanner.md  Passive security analysis work agent (domain: security)
```

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
       ├── Operator Ed25519 Auth + MFA (always required)
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
       └── 26 more patterns (see patterns/ directory)
```

### Component Descriptions

- **Hub** — A complete Weblisk deployment: orchestrator, domains, agents, data, and policies under one owner's control
- **Orchestrator** — Trust anchor: manages registration, namespace ownership, service directory distribution, channel brokering. Does NOT execute tasks or manage strategies
- **Admin** — Separate admin gateway (different domain, different network, different auth model), operator Ed25519 identity, mandatory MFA, IP allowlisting, 4-eyes approval for destructive actions
- **CLI** — Terminal commands for system interrogation and management
- **Observability** — Structured JSON logs, distributed trace propagation, Prometheus metrics
- **Gateway** — Application edge security agent: end-user authentication, ABAC authorization, rate limiting, route protection, request mediation, response sanitization. Separate from admin gateway
- **Browser Sessions** — Cryptographically-bound sessions with Ed25519 signing, device binding, island-aware concurrency, and failover continuity
- **Data Security** — Transport encryption, Ed25519 message integrity, scope-aware federation boundaries, response sanitization, framework audit trail. Provides opt-in data-level primitives (scope, policy, privacy, enforcement) for agents handling sensitive data
- **Threat Model** — 5-boundary attack surface analysis (38+ vectors), OWASP Top 10 mapping, attack chain analysis, residual risk register
- **Domains** — Own a business function, define workflows, publish workflow triggers, receive results via scoped events
- **Work Agents** — Perform specific tasks dispatched by the Task Agent (see [examples/](examples/) for reference implementations)
- **Infrastructure Agents** — Provide system services (workflow execution, task dispatch, lifecycle optimization, alerting, incident response, health monitoring, hub registry, sync, cron, email, webhooks) used by any domain
- **Marketplace** — Built into the hub — buy, sell, and share capabilities, blueprints, agents, and templates. Supports live services (invoked over federation) and installable assets (generated into your own hub). [weblisk.dev](https://weblisk.dev) serves as the public directory
- **Patterns** — 37 cross-cutting concerns (scope, policy, safety, approval, privacy, contract, security, governance, observability, workflow, task dispatch, alerting, scheduling, data sync, incident response, notification, HTTP-based pub/sub messaging, retry, rate limiting, storage, caching, state machines, secrets, logging, versioning, command, interop adapters) and API patterns (REST, AI, auth, webhooks, real-time, file upload, user management, deployment) that apply across all agents via `extends` inheritance. Every infrastructure agent has a matching pattern that formalizes its platform-wide contract — the pattern defines WHAT, the agent implements HOW
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
weblisk blueprints update
```

### Multiple Blueprint Sources

The CLI resolves blueprints in priority order:

1. **Local project** — `./patterns/` in the user's project
2. **Custom sources** — additional repos via `WL_BLUEPRINT_SOURCES`
3. **Core** — this repository (always present)

Custom sources override core blueprints with the same path. For example,
a customer's `domains/checkout.md` takes precedence over the core version.

```bash
# .env — add additional blueprint repositories
WL_BLUEPRINT_SOURCES=https://github.com/acme-corp/acme-blueprints.git
```

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
work to agents, aggregate results, and drive the feedback loop. They MUST include:

1. **Domain Manifest** — Registration manifest with required agents and workflows
2. **Required Agents** — Which work agents this domain dispatches to
3. **Workflows** — Multi-phase processes with agent dispatch, reference expressions, and error handling
4. **HandleMessage Actions** — All message types the controller responds to
5. **Scoring** — Weighted formula for computing domain scores
6. **Aggregation Rules** — How agent results are combined, with conflict resolution
7. **Strategy Alignment** — How business objectives map to domain workflows
8. **Observability** — Domain-specific metrics
9. **Error Handling** — Failure modes and degradation behavior
10. **Verification Checklist** — Testable compliance checks

See [examples/domains/seo.md](examples/domains/seo.md) for the reference
domain controller. See [architecture/domain.md](architecture/domain.md)
for the full specification.

## Creating API Patterns

API patterns define declarative specifications for common server-side
functionality. They MUST include:

1. **Pattern Format** — YAML structure the CLI consumes
2. **Endpoints** — All generated HTTP endpoints
3. **Request/Response Shapes** — JSON schemas for each endpoint
4. **Types** — All data structures used
5. **Verification Checklist** — Testable compliance checks

See [patterns/api-rest.md](patterns/api-rest.md) for a complete example.

## Creating Agent Definitions

Agent definitions describe work agents (domain-dispatched) or infrastructure
agents (system-level services). They MUST include:

1. **Kind** — `work` (dispatched by a domain) or `infrastructure` (independent)
2. **Capabilities** — Resources the agent can access
3. **Execute Workflow** — Step-by-step processing logic
4. **HandleMessage Actions** — Message types the agent responds to
5. **Observability** — Agent-specific metrics
6. **Error Handling** — Failure modes and recovery
7. **Verification Checklist** — Testable compliance checks

See [examples/agents/seo-analyzer.md](examples/agents/seo-analyzer.md)
for a work agent example. See
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
