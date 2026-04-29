# Patterns

Patterns are cross-cutting implementation contracts that apply across
agents, domains, and platforms. Each pattern defines a reusable
capability — its interface, behavior, configuration, and verification
criteria — without prescribing a specific implementation language.

Agents and domain controllers reference patterns via `extends` in their
frontmatter. A pattern is a dependency that provides a known contract.

## API & Communication

| Pattern | Purpose |
|---------|---------|
| [api-rest.md](api-rest.md) | REST API with CRUD, pagination, filtering, sorting |
| [api-ai.md](api-ai.md) | AI gateway — chat, completions, extraction, embeddings |
| [realtime-chat.md](realtime-chat.md) | WebSocket messaging with channels, presence, history |
| [webhook.md](webhook.md) | Webhook processing — inbound validation, outbound delivery |
| [command.md](command.md) | Agent command interface — dispatch, routing, execution |
| [messaging.md](messaging.md) | HTTP-based pub/sub — event envelopes, scoping, namespace ownership |
| [notification.md](notification.md) | Multi-channel notification — email, webhook, Slack, SMS, push |

## Authentication & Security

| Pattern | Purpose |
|---------|---------|
| [auth-session.md](auth-session.md) | Session-based auth with secure cookies, CSRF |
| [auth-token.md](auth-token.md) | JWT and API key auth with refresh tokens, scopes |
| [user-management.md](user-management.md) | User lifecycle — profiles, roles, password reset, OAuth |
| [security.md](security.md) | Transport security, input validation, zero-trust, threat events |
| [secrets.md](secrets.md) | Secret lifecycle — storage, rotation, access control |

## Governance

| Pattern | Purpose |
|---------|---------|
| [contract.md](contract.md) | Collaboration agreements — schemas, scope, permissions, versioning |
| [scope.md](scope.md) | Universal classification — 5-level scope, propagation, environment profiles |
| [policy.md](policy.md) | Declarative rules engine — evaluation, composition, precedence |
| [safety.md](safety.md) | Operation classification — protection gates, kill-switch, quarantine |
| [approval.md](approval.md) | Intent-based approval — authority routing, multi-party, emergency override |
| [privacy.md](privacy.md) | Consent, masking, anonymization, minimization, erasure cascade |
| [governance.md](governance.md) | Compliance profiles, evidence collection, governance directives |

## Infrastructure

| Pattern | Purpose |
|---------|---------|
| [storage.md](storage.md) | Agent-level persistence — schema, migration, backup |
| [caching.md](caching.md) | In-process caching — LRU, TTL, namespaces, AI response cache |
| [logging.md](logging.md) | Structured JSON logging — levels, correlation, rotation |
| [observability.md](observability.md) | Health endpoints, metrics envelope, component state tracking |
| [rate-limiting.md](rate-limiting.md) | Token bucket, sliding window — gateway and agent rate limits |
| [retry.md](retry.md) | Retry strategies, circuit breaker, timeout management |

## Workflows & Orchestration

| Pattern | Purpose |
|---------|---------|
| [workflow.md](workflow.md) | Workflow declaration, event-driven DAG execution, approval gates |
| [state-machine.md](state-machine.md) | Declarative state machines — transitions, guards, side effects |
| [task-dispatch.md](task-dispatch.md) | Task submission, priority queuing, dispatch protocol, dead-letter |
| [scheduling.md](scheduling.md) | Cron expressions, overlap policy, missed-tick handling, distributed locking |
| [expression.md](expression.md) | Expression language — guards, conditions, constraints, policy rules |

## Operations

| Pattern | Purpose |
|---------|---------|
| [deployment.md](deployment.md) | CI/CD pipelines, containerization, environment management |
| [file-upload.md](file-upload.md) | File upload, processing, CDN delivery, signed URLs |
| [alerting.md](alerting.md) | Alert rule evaluation, severity routing, dedup, escalation, muting |
| [incident-response.md](incident-response.md) | Incident lifecycle, runbook execution, correlation, post-mortem |
| [offline.md](offline.md) | Offline operation — sync, client persistence, encryption, revocation |
| [versioning.md](versioning.md) | Semantic versioning, compatibility rules, deprecation |
| [domain-controller.md](domain-controller.md) | Domain controller base — dispatch, aggregation, lifecycle |
| [interop.md](interop.md) | Framework adapters — LangChain, CrewAI, ADK, HTTP service wrappers |

## Schema

All pattern blueprints conform to [schemas/pattern.md](../schemas/pattern.md).
