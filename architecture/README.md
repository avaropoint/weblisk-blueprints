# System Architecture

The architecture blueprints define how the Weblisk framework operates
as a system — the components, their relationships, boundaries, security
model, and operational behavior. These are the foundational
specifications that all implementations must satisfy.

## Core Components

| Blueprint | Purpose |
|-----------|---------|
| [orchestrator.md](orchestrator.md) | Trust anchor — registration, namespaces, security, directory |
| [domain.md](domain.md) | Domain controller — a tenant's own business domain: workflow declarations that execution runs, event-driven triggering |
| [agent.md](agent.md) | Agent base — 7 endpoints, capabilities, pub/sub, retry/circuit breaker |
| [hub.md](hub.md) | Collaborative hub — discovery, tiers, commerce |
| [gateway.md](gateway.md) | Application gateway — auth, ABAC, rate limiting, route protection |
| [client.md](client.md) | Client architecture — taxonomy, trust levels, sessions, data boundary |
| [storage.md](storage.md) | Abstract persistence interface, and how a chained log is sealed so anyone can verify it offline |
| [content.md](content.md) | Content repository — authored text held as files whose bytes are their identity, with a sealed change log per repository |
| [prompt-worker.md](prompt-worker.md) | Prompt worker — the tenant's one runner of `agent:` instructions: the tools a `needs:` ceiling gives, each an owner's API on a work pass, the model asked through the model service, and writes only as proposals |
| [fabric.md](fabric.md) | Relationship fabric — the tenant's one append-only ledger of what implements what; agent work proposes a relationship and a person decides it, and a client's copy is a cache |
| [execution.md](execution.md) | Execution — cron, task and workflow merged: every start, run, step, wait and timer in one ledger, a person's step decided only by a person holding its position, and the workflow runs group of the admin API |
| [programme-service.md](programme-service.md) | Programme service — the operations, workflows and notices an adopted programme installs, who may switch them, and what execution, notification and the prompt worker are handed |
| [notification.md](notification.md) | Notification — tells the people who hold a notice's positions, each their own way, and reports a notice that reached nobody as such |
| [model-service.md](model-service.md) | Model service — the one place a tenant component asks the tenant's model for unattended work: the model gateway's service route, its audit and the usage each completion reports |
| [tenancy.md](tenancy.md) | Many hubs on shared infrastructure, without the host joining any tenant's trust boundary; and what any tenant is rebuilt from |
| [mcp.md](mcp.md) | Model Context Protocol surface — how an external AI agent reaches a hub's capabilities |

## Operations

| Blueprint | Purpose |
|-----------|---------|
| [cli.md](cli.md) | CLI specification — scaffolding, code generation, operations |
| [admin.md](admin.md) | Platform admin — operator identity, roles, and the admin gateway, a component of every tenant (kind `admin`) |
| [observability.md](observability.md) | Structured logging, distributed tracing, metrics |
| [lifecycle.md](lifecycle.md) | Continuous optimization loop (event-driven) |
| [testing.md](testing.md) | Conformance test suite specification |
| [generation.md](generation.md) | Producing an implementation from blueprints — prompt contract, generation loop, verification gate |
| [change-management.md](change-management.md) | Versioning, migration, deprecation lifecycle |

## Security

| Blueprint | Purpose |
|-----------|---------|
| [enforcement.md](enforcement.md) | Non-bypassable boundary inspection, rogue agent detection |
| [data-security.md](data-security.md) | Transport security, scope-aware boundaries, opt-in data primitives |
| [threat-model.md](threat-model.md) | Attack surface analysis — 5 boundaries, OWASP mapping |

## Schema

Architecture blueprints conform to [schemas/architecture.md](../schemas/architecture.md).
