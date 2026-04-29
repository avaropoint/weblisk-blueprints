# System Architecture

The architecture blueprints define how the Weblisk framework operates
as a system — the components, their relationships, boundaries, security
model, and operational behavior. These are the foundational
specifications that all implementations must satisfy.

## Core Components

| Blueprint | Purpose |
|-----------|---------|
| [orchestrator.md](orchestrator.md) | Trust anchor — registration, namespaces, security, directory |
| [domain.md](domain.md) | Domain controller — workflow declarations, event-driven triggering |
| [agent.md](agent.md) | Agent base — 6 endpoints, capabilities, pub/sub, retry/circuit breaker |
| [hub.md](hub.md) | Collaborative hub — discovery, tiers, commerce |
| [gateway.md](gateway.md) | Application gateway — auth, ABAC, rate limiting, route protection |
| [client.md](client.md) | Client architecture — taxonomy, trust levels, sessions, data boundary |
| [storage.md](storage.md) | Abstract persistence interface |

## Operations

| Blueprint | Purpose |
|-----------|---------|
| [cli.md](cli.md) | CLI specification — scaffolding, code generation, operations |
| [admin.md](admin.md) | Platform admin — operator identity, roles, separate admin gateway |
| [observability.md](observability.md) | Structured logging, distributed tracing, metrics |
| [lifecycle.md](lifecycle.md) | Continuous optimization loop (event-driven) |
| [testing.md](testing.md) | Conformance test suite specification |
| [change-management.md](change-management.md) | Versioning, migration, deprecation lifecycle |

## Security

| Blueprint | Purpose |
|-----------|---------|
| [enforcement.md](enforcement.md) | Non-bypassable boundary inspection, rogue agent detection |
| [data-security.md](data-security.md) | Transport security, scope-aware boundaries, opt-in data primitives |
| [threat-model.md](threat-model.md) | Attack surface analysis — 5 boundaries, OWASP mapping |

## Schema

Architecture blueprints conform to [schemas/architecture.md](../schemas/architecture.md).
