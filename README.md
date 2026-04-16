# Weblisk Blueprints

[![GitHub](https://img.shields.io/badge/github-avaropoint%2Fweblisk--blueprints-blue)](https://github.com/avaropoint/weblisk-blueprints)
[![Part of Weblisk](https://img.shields.io/badge/part%20of-Weblisk-orange)](https://github.com/avaropoint/weblisk)

The specification, architecture, and domain knowledge for the
[Weblisk](https://github.com/avaropoint/weblisk) server framework.

This repository is part of the **Weblisk** project — an open-source
server framework for building autonomous, collaborative AI agents.
The [weblisk](https://github.com/avaropoint/weblisk) repository contains
the server runtime and CLI; this repository provides the blueprints that
drive code generation and define protocol compliance.

Blueprints are implementation-agnostic specifications. They describe
**what** agents and orchestrators must do — not **how** they do it in
any particular language. Server implementations (Go, Node, Cloudflare,
Rust, etc.) build from these blueprints.

## Structure

```
protocol/           Wire protocol specifications
  spec.md             Full protocol specification v1
  identity.md         Ed25519 crypto, tokens, signing
  types.md            Canonical type definitions (all JSON shapes)

architecture/       System architecture
  orchestrator.md     Central coordinator — routing, security, audit
  domain.md           Domain controller — workflows, dispatch, aggregation
  agent.md            Agent base — kinds, capabilities, ports
  lifecycle.md        Continuous optimization loop
  storage.md          Abstract persistence interface
  testing.md          Conformance test suite specification

platforms/          Implementation guidance per runtime
  go.md               Go (stdlib only, local processes)
  cloudflare.md       Cloudflare Workers (Durable Objects, KV)

domains/            Domain controller specifications
  seo.md              SEO domain — workflows, required agents, scoring

agents/             Work agents and infrastructure services (Free tier)
  seo-analyzer.md     SEO analysis work agent (domain: seo)
  a11y-checker.md     Accessibility checking work agent (domain: seo)
  sync-agent.md       Background data sync (infrastructure)
  cron-agent.md       Scheduled task execution (infrastructure)
  webhook-agent.md    Webhook processing (infrastructure)
  email-agent.md      Transactional email (infrastructure)

patterns/           Declarative API pattern specifications (Free tier)
  api-rest.md         REST API with CRUD, pagination, filtering, sorting
  realtime-chat.md    WebSocket messaging with channels, presence, history
  auth-session.md     Session-based auth with secure cookies, CSRF
  auth-token.md       JWT and API key auth with refresh tokens, scopes
  webhook-inbound.md  Receive and validate inbound webhooks
  webhook-outbound.md Send webhooks with retries and delivery tracking
```

### Architecture Hierarchy

```
Orchestrator (coordinator)
  └── Domain Controllers (directors)
       └── Work Agents (task executors)
  └── Infrastructure Agents (system utilities)
```

- **Orchestrator** — Routes tasks, manages security, brokers channels, tracks the lifecycle
- **Domains** — Own a business function, define workflows, dispatch to agents, aggregate results
- **Work Agents** — Perform specific tasks under a domain's direction
- **Infrastructure Agents** — Provide system services (sync, cron, email, webhooks) used by any domain

### Free vs Pro

This repository contains all **free tier** blueprints — the complete
architecture, protocol, one reference domain (SEO), infrastructure agents,
and API patterns. These match the
[Blueprint Catalog](https://weblisk.dev/blueprints/catalog.html) and
[Agent Catalog](https://weblisk.dev/agents/catalog.html). Everything here
is open source and ships with every Weblisk server implementation.

Pro patterns and agents (file-storage, crdt-sync, search-index,
email-transactional, ai-agent, search-agent, media-agent, analytics-agent)
are available through [Weblisk Pro](https://weblisk.dev/pro.html) or
via [Avaropoint](https://avaropoint.com/) for enterprise engagements.

## Usage

### With the Weblisk CLI

The CLI supports multiple blueprint sources. This repository serves as the
**core** source — always available as a fallback. Custom, partner, and
customer-owned blueprint repos can be added alongside it.

```bash
# The CLI clones this repo automatically on first use
weblisk server init --platform go

# Generate an agent from a domain blueprint
weblisk agent create seo --platform go

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

1. Read the [Blueprint Schema](SCHEMA.md) for the standard structure
2. Create a domain blueprint for your agent's expertise
3. Reference the protocol and architecture blueprints
4. Use the Weblisk CLI or your preferred AI model to generate the implementation

## Blueprint Schema

Every blueprint follows a [standard schema](SCHEMA.md) with required sections:
metadata header, overview, specification, types, implementation notes,
and verification checklist. See the schema file for details.

## Creating Domain Controllers

Domain controllers own a business function. They define workflows, dispatch
work to agents, aggregate results, and drive the feedback loop. They MUST include:

1. **Required Agents** — Which work agents this domain dispatches to
2. **Workflows** — Multi-phase processes with agent dispatch, data flow, and error handling
3. **Strategy Alignment** — How business objectives map to domain workflows
4. **Aggregation Rules** — How agent results are combined and scored
5. **Feedback Collection** — What observations, recommendations, and metrics the domain tracks

See [domains/seo.md](domains/seo.md) for a complete example.
See [architecture/domain.md](architecture/domain.md) for the full specification.

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
5. **Validation Rules** — Domain-specific constraints and checks
6. **Verification Checklist** — Testable compliance checks

See [agents/seo-analyzer.md](agents/seo-analyzer.md) for a work agent example.
See [agents/sync-agent.md](agents/sync-agent.md) for an infrastructure agent example.

## Related Repositories

| Repository | Description |
|---|---|
| [weblisk](https://github.com/avaropoint/weblisk) | Server framework runtime and CLI |
| [weblisk-blueprints](https://github.com/avaropoint/weblisk-blueprints) | Specifications and domain knowledge (this repo) |

## Contributing

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/my-blueprint`)
3. Follow the [Blueprint Schema](SCHEMA.md) for new blueprints
4. Commit your changes (`git commit -m 'Add new blueprint'`)
5. Push to the branch (`git push origin feature/my-blueprint`)
6. Open a Pull Request

## License

MIT
