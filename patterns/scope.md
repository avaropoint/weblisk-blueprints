<!-- blueprint
type: pattern
name: scope
version: 2.5.1
requires: [protocol/types]
platform: any
tier: free
-->

# Scope Pattern

Universal classification primitive that determines protection level
for any entity in the system — data fields, operations, messages,
agents, resources, and environments. Scope is the foundation that
policies, safety, privacy, and contracts all reference.

## Overview

Scope is the most foundational pattern in Weblisk. It provides a
five-level classification model — public, internal, confidential,
restricted, critical — that can be applied to anything. When an entity
is classified, protections activate automatically based on the level.

Weblisk is not a restrictive platform. Scope is opt-in protection.
Agents, domains, and operators choose what classification to apply.
The more sensitive the scope, the more policies activate — audit
logging, encryption, masking, approval gates, retention rules. Scope
is never silently dropped: when data moves between agents, hubs, or
clients, its scope travels with it.

This pattern is consumed by every other pattern in the system.
Messaging reads scope to filter delivery. Workflows read scope to
enforce approval gates. Storage reads scope to select encryption
strategies. Observability reads scope to control log redaction.
Scope is the primitive; everything else is a consumer.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.13.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category]
        - name: AgentManifest
          fields_used: [name, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Universal applicability** — Scope applies to ANY entity in the
   system: data fields, operations, messages, agents, resources,
   environments. It is not "data scope" or "agent scope" — it is
   scope, period. Every entity type uses the same classification
   model and the same enforcement pipeline.

2. **Propagation by default** — Scope is never silently dropped.
   When data moves between components — agent to agent, hub to hub,
   hub to client — its scope moves with it. The receiving component
   MUST honor the declared scope or reject the transfer. Silent
   scope loss is a conformance violation.

3. **Escalation to maximum** — In any composite entity (a message
   containing multiple data fields, a workflow spanning multiple
   agents, a response aggregating multiple sources), the effective
   scope is the HIGHEST scope of any component. A single restricted
   field in a public message makes the entire message restricted.

4. **Environment-relative enforcement** — The same scope level may
   be enforced differently in development vs production. Environments
   modify enforcement strictness, not classification. A field
   classified as `restricted` is always `restricted` — but in dev
   the enforcement may be audit-only, while in production it is
   fully enforced.

5. **Opt-in extensibility** — The five built-in levels cover most
   use cases. Domains MAY define custom labels, each registered with
   the least level it may be declared with. Custom labels extend —
   they never replace — the built-in model: every declaration carries
   one of the five levels beside its labels, so a component that does
   not know a label enforces the level declared with it (see
   [A label and its level](#a-label-and-its-level)).

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: scope-declaration
      description: Declare a scope level on any entity — data field, operation, message, agent, or resource
      parameters:
        - name: level
          type: enum(public, internal, confidential, restricted, critical)
          required: true
          description: Classification level from the built-in five-level model
        - name: context
          type: string
          required: false
          description: Domain or subsystem that owns the classification decision
        - name: propagation_rule
          type: enum(inherit, fixed, escalate)
          required: false
          default: inherit
          description: How scope behaves when the entity is composed or transferred
        - name: custom_labels
          type: "[]string"
          required: false
          description: Domain-specific labels carried beside the level. Never a level; a registered label's maps_to is the least level it may be declared with
      inherits: Scope metadata attachment, level validation, propagation rule assignment
      overridable: true
      override_constraints: Level must be one of the five built-in values, and at least the maps_to of every registered custom label the declaration carries

    - name: scope-propagation
      description: Carry scope across component boundaries — agent-to-agent, hub-to-hub, hub-to-client
      parameters:
        - name: source_scope
          type: ScopeDeclaration
          required: true
          description: Scope of the entity being transferred
        - name: target_component
          type: string
          required: true
          description: Identifier of the receiving component (agent name, hub ID, client ID)
        - name: transfer_mode
          type: enum(copy, reference)
          required: false
          default: copy
          description: Whether the receiving component gets a full scope copy or a reference to the source
      inherits: Envelope-level scope metadata, cross-boundary validation, rejection on scope mismatch
      overridable: true
      override_constraints: Must never silently drop scope; receiving component must validate or reject

    - name: scope-escalation
      description: Compute the effective scope of a composite entity from its components
      parameters:
        - name: components
          type: "[]ScopeDeclaration"
          required: true
          description: Scope declarations of all component parts
        - name: escalation_strategy
          type: enum(maximum, explicit)
          required: false
          default: maximum
          description: How to compute composite scope — maximum of components or explicitly declared
      inherits: Automatic highest-level computation, escalation event emission
      overridable: true
      override_constraints: Maximum strategy cannot be overridden to produce a LOWER scope than any component

    - name: scope-evaluation
      description: Compute the effective scope of an entity given its declaration, environment, and context
      parameters:
        - name: entity
          type: string
          required: true
          description: Identifier of the entity being evaluated
        - name: declared_scope
          type: ScopeDeclaration
          required: true
          description: The entity's declared scope level
        - name: environment
          type: EnvironmentProfile
          required: false
          description: Active environment profile that may modify enforcement
      inherits: Effective scope computation, environment overlay, enforcement level resolution
      overridable: true
      override_constraints: Evaluation must never produce an effective scope LOWER than declared scope

    - name: environment-profiling
      description: Define how environments modify scope enforcement without changing classification
      parameters:
        - name: environment_name
          type: enum(development, staging, production, custom)
          required: true
          description: Target environment identifier
        - name: enforcement_level
          type: enum(permissive, moderate, strict)
          required: true
          description: Base enforcement strictness for this environment
        - name: scope_overrides
          type: map
          required: false
          description: Per-level enforcement overrides (audit, enforce, block)
      inherits: Environment-aware enforcement pipeline, override resolution
      overridable: true
      override_constraints: Production environment must always enforce at strict level; overrides cannot weaken production enforcement; no profile makes the destination gate audit-only

    - name: destination-gate
      description: Decide whether content may be sent to a destination outside the store that holds it — see Destination Ceilings
      parameters:
        - name: payload_scope
          type: ScopeLevel
          required: false
          description: The highest scope of everything that would be sent. Absent when any part of it is undeclared
        - name: destination_ceiling
          type: ScopeLevel
          required: true
          description: The highest scope the destination may receive
      inherits: Allow, or a refusal carrying a DestinationRefusal — SCOPE_MISSING when payload_scope is absent, SCOPE_CEILING_EXCEEDED when it is above destination_ceiling — in every environment profile. architecture/content's replica declaration is the one sender with codes of its own, named under The gate
      overridable: false
      override_constraints: Not overridable — a gate an extender could loosen, or a profile could make audit-only, lets content leave that has not come back

  types:
    - name: ScopeLevel
      description: Enumeration of the five built-in classification levels
      inherited_by: Scope Types section
    - name: ScopeDeclaration
      description: Complete scope metadata for any entity
      inherited_by: Scope Types section
    - name: ScopeEvaluation
      description: Result of evaluating an entity's effective scope in context
      inherited_by: Scope Types section
    - name: EnvironmentProfile
      description: Environment configuration that modifies scope enforcement
      inherited_by: Scope Types section
    - name: ScopeViolation
      description: Record of a scope boundary violation
      inherited_by: Scope Types section
    - name: ProviderAgreement
      description: The tenant's record of the agreement that raises a model provider's ceiling
      inherited_by: Scope Types section
    - name: ProviderCeiling
      description: What a model backend may be sent now
      inherited_by: Scope Types section
    - name: DestinationRefusal
      description: Why the destination gate refused a send
      inherited_by: Scope Types section

  events:
    - topic: scope.violation
      description: Emitted when an entity's scope is accessed beyond its allowed level
      payload: {entity, expected_scope, actual_scope, component, action_taken, timestamp}
    - topic: scope.escalation
      description: Emitted when a composite's scope is escalated due to a higher-scoped component
      payload: {composite_entity, previous_scope, escalated_scope, escalation_source, timestamp}
    - topic: scope.override
      description: Emitted when an environment profile modifies scope enforcement
      payload: {entity, declared_scope, effective_enforcement, environment, reason, timestamp}
```

---

## Scope Levels

The five built-in levels form a strict hierarchy. Each level inherits
all protections from the levels below it. Higher levels add additional
protections — they never remove protections from lower levels.

### Level Hierarchy

```
critical > restricted > confidential > internal > public
```

Numeric values for programmatic comparison:

| Level | Ordinal | Description |
|-------|---------|-------------|
| `public` | 0 | Unrestricted; safe for external consumption |
| `internal` | 1 | Organization-internal; not for external exposure |
| `confidential` | 2 | Sensitive; requires access control and audit |
| `restricted` | 3 | Highly sensitive; requires encryption, masking, approval |
| `critical` | 4 | Regulatory or safety-critical; maximum protection |

### Scope Inheritance Table

Each level activates specific protections. Higher levels include all
protections from lower levels plus additional requirements:

| Level | Audit | Encryption | Masking | Approval | Retention |
|-------|-------|-----------|---------|----------|-----------|
| public | no | transport | none | none | default |
| internal | basic | transport | none | none | default |
| confidential | full | transport + at-rest | field-level | auto | policy-driven |
| restricted | full | transport + at-rest + field | full masking | operator | strict |
| critical | full + tamper-evident | transport + at-rest + field + envelope | full masking | admin + MFA | regulatory |

**Column definitions:**

- **Audit** — What level of audit logging is required. `basic` logs
  access events. `full` logs access + mutations + context.
  `full + tamper-evident` adds cryptographic audit trail integrity.
- **Encryption** — Required encryption layers. `transport` = TLS.
  `at-rest` = storage encryption. `field` = per-field encryption.
  `envelope` = entire message envelope encrypted.
- **Masking** — How the entity appears in logs, UI, and API responses
  when the accessor lacks sufficient clearance. `field-level` masks
  specific fields. `full masking` masks the entire value.
- **Approval** — What approval is needed to access or modify the
  entity. `auto` = system-level policy check. `operator` = human
  operator approval. `admin + MFA` = administrator with multi-factor
  authentication.
- **Retention** — How long the entity is retained. `default` = system
  default. `policy-driven` = domain-specific retention policy.
  `strict` = minimum necessary retention. `regulatory` = retention
  per applicable regulatory requirements.

---

## Placement Ceilings

A classification states how sensitive content is. It does not state whether the
place holding that content can support it.

Where content is stored on a backend that concedes access to another authority,
the highest level that may be placed there is capped by what that backend can
demonstrate — not by what the content deserves. A `restricted` document placed
on a share whose principals cannot be enumerated is `restricted` in name only:
nothing enforces the access control the level requires.

[`architecture/content`](../architecture/content.md) defines custody classes,
the attestation properties a backend must demonstrate, and the ceiling derived
from them. A write above the ceiling is refused, never downgraded — a level the
system quietly lowered is a classification nobody made, and the record would
then understate the sensitivity of its own content.

---

## Destination Ceilings

A **destination** is a place outside the store holding some content, which
that content is sent to and which has a **ceiling**: the highest level it may
receive. A placement ceiling caps what a place may hold; a destination ceiling
caps what may be sent to one. These are the destinations with a ceiling, and a
blueprint that names another says how its ceiling is derived and where it is
read:

| Destination | Ceiling derived by | Read by a client from |
|---|---|---|
| A replica of a content repository | [`architecture/content`](../architecture/content.md#derived-scope-ceiling), Derived Scope Ceiling | `GET /v1/content/repositories/{repository}/replicas` |
| A model provider | [Model providers](#model-providers), below | `GET /v1/admin/model/ceiling` on a person's token, and `GET /v1/model/ceiling` on a registered component's ([`architecture/orchestrator`](../architecture/orchestrator.md#a-model-is-a-destination)) |
| A caller of a hub's MCP surface | Always `internal`, as [`architecture/mcp`](../architecture/mcp.md#the-destination-gate) says: its caller is a model whose provider the tenant cannot see, so it is a model provider no agreement can name | Not read by a client: the MCP surface applies it to every tool result |

> **Gap — a tenant component on another host has no ceiling yet.** A tenant
> component on a host other than the one holding the content takes its
> ceiling from the custody that host has demonstrated, and never from
> `ServiceEntry.address_provenance`, which says where a component is and not
> who can read its bytes. No blueprint yet specifies how a host
> demonstrates custody, so no such row stands in the table above, and what
> the content service serves a component, `content:read` included, is bounded
> today by that component's grant and scope alone, wherever it runs. A tenant
> that places a component that reads content on another host
> ([`architecture/orchestrator`](../architecture/orchestrator.md#a-tenants-components-may-be-distributed))
> therefore sends that host whatever the component may read, `restricted`
> included, with nothing demonstrated about who else can read it there.
> Closing it is a custody demonstration for a component's host, with a
> ceiling derived from it as a replica's is, and the gate above applied to
> every read served across hosts.

### The gate

Anything a tenant holds may be sent to a destination only when both of these
hold:

1. **Its scope is declared.** The configured `default_level` says how an
   undeclared entity is treated where it is. It is never a declaration, and it
   never lets anything leave. Undeclared content is refused with
   `SCOPE_MISSING`, whatever `reject_unscoped` says.
2. **Its scope is at or below the destination's ceiling.** What is sent is at
   the highest scope of everything it carries, as
   [Scope Escalation](#scope-escalation) computes it. Above the ceiling, it is
   refused with `SCOPE_CEILING_EXCEEDED`.

**One set of codes.** Every sender refuses with these two codes, each
carrying a `DestinationRefusal`: a model route, an api-ai endpoint and the
external boundary of
[`architecture/enforcement`](../architecture/enforcement.md#external-proxy)
alike. One exception is named here, as
[A label and its level](#a-label-and-its-level) names one for a declaration:
[`architecture/content`](../architecture/content.md#replica-declaration-flow)
refuses a replica declaration with its own `CONTENT_SCOPE_UNDECLARED` and
`CONTENT_CUSTODY_CEILING_EXCEEDED`, carrying the `ReplicaCensus`, which names
the destination, its prospective ceiling and each path above it or
unclassified — everything a `DestinationRefusal` carries — and it holds a
replica's later sends rather than refusing them. No other component names a
code of its own for this gate.

**For content, the unit is the entry.** Any part of an entry in a content
repository — a row, a section, a column, a quoted line, a summary of it — is
at the scope of the whole entry, as
[`architecture/content`](../architecture/content.md#the-recorded-scope)
reports it in `ContentEntry.scope`, and has no level of its own. Any part of
an unclassified entry is undeclared. A prompt that quotes one row of a
`restricted` register is `restricted`.

Content no tenant holds, such as a published corpus read outside any tenant,
is outside this gate, because there is no tenant to report its level or attest
a ceiling. A level its own bytes declare still binds whoever sends it.

**It is never audit-only.** The gate resolves to deny in every environment
profile. No profile, built-in or custom, makes it audit-only or lets through
what it refuses, as no profile makes `critical` audit-only
([Built-in Profiles](#built-in-profiles)). A profile says how strictly a level
is enforced where the content is held. What has been sent somewhere else does
not come back.

**Refuse, and never make it fit.** A sender that would exceed a destination's
ceiling refuses. It MUST NOT drop, mask, summarise or otherwise redact the part
above the ceiling and send the rest. A payload changed to fit is one nobody
asked to send, and whoever asked believes all of it went. The refusal says
why, as a `DestinationRefusal`: the destination, its ceiling, and each item
above it with its level, or that the item's level is undeclared. It emits
`scope.violation`. A person may then send what is at or below the ceiling, as a
new request of their own, told what it leaves out.

> **Gap — a register is not yet masked by column for a model provider.**
> A register sent to a model provider is meant to have the columns its
> schema declares above the provider's ceiling masked, rather than the whole
> register refused, with the masking following
> [`patterns/privacy`](privacy.md)'s activation matrix. Nothing here does that
> yet, so today a register with one column declared above the ceiling is
> refused whole. A sender cannot do it: a model route cannot see where the
> text in a prompt came from, and a client takes a level only from what the
> tenant reported with it, which is the whole entry's. Only the tenant can,
> because it alone holds what a column's level is: a column `scope` is
> declared on the register's spec
> ([`schemas/programme`](../schemas/programme.md#scope)) and the entry's bytes
> carry only the register's level, so
> [`architecture/content`](../architecture/content.md#the-recorded-scope)
> records no column's. What closes it is a read the tenant answers with the
> register less every column declared above a named ceiling, reported at the
> scope of what remains and naming each column it left out, so that the
> removal is the tenant's declared act, shown to whoever asked and audited,
> and never a sender's silent one. That read is a different item from the
> entry, at its own scope, and the gate and the rule above apply to it
> unchanged. A register whose spec, rather than a column, puts it at
> `restricted` or above stays refused whole.

**Every sender, a client included.** The gate binds whatever sends: a
component, an agent, a gateway, and a client outside the tenant, such as an
operator console or the CLI, that holds content it read from the tenant and is
about to pass it on. A client takes the scope of what it would send from what
the tenant reported with it, and never from its own reading of the text. It
takes a destination's ceiling from the tenant too, by the route the table
above names. A client that cannot learn a level treats the content as
undeclared. One that cannot learn a ceiling uses the ceiling the destination
has with nothing demonstrated or attested.

**Where the tenant applies it.**

- A model is reached only through the tenant's **model route**: the endpoints
  of [`patterns/api-ai`](api-ai.md#destination-ceilings), and
  `POST /v1/admin/complete`
  ([`architecture/orchestrator`](../architecture/orchestrator.md#a-model-is-a-destination)).
  Each applies the gate itself before it sends, and the component serving it
  declares `model:route` ([`protocol/types`](../protocol/types.md)), which is
  how a boundary tells it from anything else. A model backend that runs as a
  program on the tenant's host makes no outbound call a boundary can see.
- A component's outbound call to a model provider's endpoint also passes the
  external boundary of
  [`architecture/enforcement`](../architecture/enforcement.md#external-proxy),
  which recognises the endpoint by the address `GET /v1/model/ceiling` reports,
  applies the gate with the provider's ceiling, and refuses a call made around
  the model route: one from a caller whose manifest does not declare
  `model:route`.
- A tool result is checked by a hub's MCP surface before it is returned to
  its caller, as [`architecture/mcp`](../architecture/mcp.md#the-destination-gate)
  says. Its caller is a model, so nothing `restricted` or above is returned
  to one ([Model providers](#model-providers)).
- A replica is checked by the content service, when it is declared and before
  every send, as [`architecture/content`](../architecture/content.md#replicas)
  says.

**Another destination is another gate.** Whatever chooses where a request
goes — resolving a model by name, a fallback chain, a failover when the first
provider fails, a budget downgrade, a caller's override — may choose only a
destination whose ceiling covers what is sent. With none, the request is
refused. It never goes, transparently or otherwise, to a destination whose
ceiling is below it, and the response names the destination that received
it. A copy sent on to a second place is checked against that place.

### Model providers

A **model provider** is the party that runs the model a request reaches: the
organisation whose systems receive what is sent. It is never the program or
the configuration name that reaches it. A backend that runs as a program on
the tenant's host and sends the request on to a service, such as a vendor's
command-line client, is that service's, however local the program is. Two
backends that reach one organisation reach one provider. A model the tenant
runs on a component of its own has the tenant as its provider.

A model provider's ceiling is `internal`, until a person at the tenant records
an **agreement attestation** for it.

- **What it is.** A `ProviderAgreement`: the tenant's record that an agreement
  with the party governs what the party does with what it is sent — what it
  keeps, whether it trains on it, to whom it discloses it — and covers content
  up to a stated level, `internal` or `confidential`. It names the party, every
  name under which the tenant's model configuration reaches it (`backends`),
  the agreement, the SHA-256 of the tenant's own copy of it, the level, who
  recorded it, and when it lapses. Where the tenant runs the model itself, it
  names the component.
- **How a request finds its provider.** By the name the tenant's model
  configuration gives the backend the request reaches: the `provider` value
  `GET /v1/admin/model` reports, or the provider's key under `patterns/api-ai`'s
  `providers:`. The name is compared exactly as the configuration spells it.
  A backend no current agreement lists has the ceiling `internal`, so a name
  nobody listed is never given more, and the ceiling routes answer every name
  that way, one the tenant's model configuration does not know included. A
  backend is listed by at most one current agreement.
- **What an agreement does not bind.** It binds a name, never what the name
  reaches. So changing what a listed name reaches ends the agreement where
  the tenant can see the change. The orchestrator holds both the model
  configuration and the agreements, and `PUT /v1/admin/model` withdraws every
  current agreement listing a name whose backend the request changes
  ([`architecture/orchestrator`](../architecture/orchestrator.md#a-model-is-a-destination)),
  so the name falls to `internal` until a person holding `model:attest`
  records a new one. An api-ai `providers:` entry is configured where the
  orchestrator cannot see it: changing its endpoint keeps the agreement's
  level, and content up to that level would go to a party no agreement
  covers. Until an agreement records what each name it lists reaches, whoever
  changes a listed `providers:` entry withdraws that agreement first, and the
  tenant cannot check that they did.
- **Who records it.** A person, on their own operator token, holding
  `model:attest`. [`protocol/types`](../protocol/types.md) marks it *person
  only*, and the mechanism that list names keeps it from every service
  subject, every token minted for one and every agent
  ([`patterns/principal-identity`](principal-identity.md),
  `service-subject-constraints` and `agent-delegation`). `admin:*` does not
  include it. The tenant takes who recorded it from the token's `identity_id`
  ([`protocol/identity`](../protocol/identity.md#payload-claims)), and
  withdrawing one takes the same capability.
- **Where it is held.** At the tenant, beside the model configuration it
  qualifies, through the routes
  [`architecture/orchestrator`](../architecture/orchestrator.md#a-model-is-a-destination)
  declares. It is a fact about the tenant, so a client never keeps one, never
  infers one, and never treats a setting of its own as one.
- **What it changes.** While it is current, the provider's ceiling is the
  level it names. It lapses at `not_after`, which is no more than 90 days after
  it is recorded, or when a person withdraws it. From that moment the ceiling
  is `internal` again.

**Nothing `restricted` or above is sent to a model provider, whatever its
ceiling,** a model the tenant runs itself and the model behind an MCP caller
included. That is why an agreement names `confidential` at most. A request
that carries any part of an entry whose `ContentEntry.scope` is `restricted`
or `critical` is refused, whichever of its rows, sections or columns the
request drew on.

---

## Types

```yaml
types:
  ScopeLevel:
    description: Enumeration of the five built-in classification levels
    values:
      - name: public
        ordinal: 0
        description: Unrestricted; safe for external consumption
      - name: internal
        ordinal: 1
        description: Organization-internal; not for external exposure
      - name: confidential
        ordinal: 2
        description: Sensitive; requires access control and audit
      - name: restricted
        ordinal: 3
        description: Highly sensitive; requires encryption, masking, approval
      - name: critical
        ordinal: 4
        description: Regulatory or safety-critical; maximum protection
    comparison: ordinal-based; higher ordinal = more restrictive scope

  ScopeDeclaration:
    description: Complete scope metadata attached to any entity
    fields:
      - name: level
        type: ScopeLevel
        required: true
        description: Classification level from built-in model
      - name: context
        type: string
        required: false
        description: Domain or subsystem that owns the classification (e.g., "seo", "billing", "identity")
      - name: propagation_rule
        type: enum(inherit, fixed, escalate)
        required: false
        default: inherit
        description: |
          How scope behaves during composition or transfer:
          - inherit: receiving component adopts the source scope
          - fixed: scope is locked and cannot be escalated by composition
          - escalate: scope participates in composite escalation (default behavior)
      - name: custom_labels
        type: "[]string"
        required: false
        description: Domain-specific labels carried beside level (e.g., ["pii", "financial", "hipaa"]). Never a level. See A label and its level
      - name: declared_by
        type: string
        required: false
        description: Identifier of the agent or domain that applied this classification
      - name: declared_at
        type: int64
        required: false
        description: Unix epoch seconds when scope was declared

  ScopeEvaluation:
    description: Result of evaluating an entity's effective scope in context
    fields:
      - name: entity
        type: string
        required: true
        description: Identifier of the entity being evaluated
      - name: declared_scope
        type: ScopeDeclaration
        required: true
        description: The entity's declared scope
      - name: effective_scope
        type: ScopeLevel
        required: true
        description: Computed scope after environment and escalation rules
      - name: effective_enforcement
        type: enum(audit, enforce, block)
        required: true
        description: |
          How the effective scope is enforced in the current environment:
          - audit: log violations but allow access
          - enforce: deny access on violation
          - block: deny access and quarantine the entity
      - name: escalation_source
        type: string
        required: false
        description: If scope was escalated, the component that caused escalation
      - name: environment
        type: string
        required: false
        description: Environment name used for evaluation (dev, staging, production)

  EnvironmentProfile:
    description: Environment configuration that modifies scope enforcement
    fields:
      - name: name
        type: enum(development, staging, production, custom)
        required: true
        description: Environment identifier
      - name: enforcement_level
        type: enum(permissive, moderate, strict)
        required: true
        description: |
          Base enforcement strictness:
          - permissive: audit-only for most levels; enforce only critical
          - moderate: enforce confidential and above; audit internal
          - strict: enforce all levels at maximum
      - name: scope_overrides
        type: map[ScopeLevel → EnforcementOverride]
        required: false
        description: Per-level enforcement overrides that take precedence over base level
      - name: custom_name
        type: string
        required: false
        description: Human-readable name for custom environments

  EnforcementOverride:
    description: Per-level enforcement configuration within an environment
    fields:
      - name: enforcement
        type: enum(audit, enforce, block)
        required: true
        description: Override enforcement action for this scope level
      - name: reason
        type: string
        required: false
        description: Justification for the override (logged in scope.override events)

  ScopeViolation:
    description: Record of a scope boundary violation
    fields:
      - name: entity
        type: string
        required: true
        description: Identifier of the entity whose scope was violated
      - name: expected_scope
        type: ScopeLevel
        required: true
        description: Scope level the entity requires
      - name: actual_scope
        type: ScopeLevel
        required: true
        description: Scope level the accessor presented
      - name: accessor
        type: string
        required: true
        description: Identifier of the component that attempted access
      - name: action_taken
        type: enum(audit, deny, quarantine)
        required: true
        description: Enforcement action applied
      - name: timestamp
        type: int64
        required: true
        description: Unix epoch seconds when the violation occurred
      - name: environment
        type: string
        required: false
        description: Environment where the violation occurred

  ProviderAgreement:
    description: |
      The tenant's record that an agreement governs what a model provider
      does with what it is sent, and the ceiling that gives the provider.
      Held by the tenant, recorded by a person. See Model providers
    fields:
      - name: id
        type: string
        required: true
        description: Assigned by the tenant when it is recorded. Stable and never reused
      - name: party
        type: string
        required: true
        description: The organisation that runs the model, as the agreement names it. Where the tenant runs the model itself, the tenant
      - name: backends
        type: "[]string"
        required: true
        description: Every name under which the tenant's model configuration reaches the party, spelled as the configuration spells it. At least one. A name a current agreement already lists is refused
      - name: component
        type: string
        required: false
        description: The tenant's own component that runs the model, where the tenant runs it itself
      - name: agreement
        type: string
        required: true
        description: The agreement, as the tenant names it — its title and reference
      - name: agreement_digest
        type: string
        required: true
        description: The SHA-256 of the tenant's own copy of the agreement, written sha256:<64 hex>, so the copy can be checked with sha256sum and nothing else
      - name: level
        type: ScopeLevel
        required: true
        description: The ceiling it gives the provider, internal or confidential. Any other value is refused
      - name: recorded_by
        type: string
        required: true
        description: The identity id of the person who recorded it, from their verified operator token. Never taken from a request body
      - name: recorded_at
        type: int64
        required: true
        description: Unix epoch seconds when it was recorded
      - name: not_after
        type: int64
        required: true
        description: Unix epoch seconds when it lapses — the end, or the next review, of the agreement. In the future when recorded, and no more than 90 days after, the cap architecture/admin puts on every attestation a hub records. After it, the ceiling is internal
      - name: withdrawn_by
        type: string
        required: false
        description: The identity id of the person who withdrew it, from their verified operator token
      - name: withdrawn_at
        type: int64
        required: false
        description: Unix epoch seconds when it was withdrawn. From then, the ceiling is internal

  ProviderCeiling:
    description: |
      What a model backend may be sent now, as the tenant answers it. What a
      client reads before it sends. See Model providers
    fields:
      - name: backend
        type: string
        required: true
        description: The name asked about — the backend GET /v1/admin/model reports, or the name ?backend= gave, which may be an api-ai providers key the tenant's model configuration does not know
      - name: ceiling
        type: ScopeLevel
        required: true
        description: internal, or the level of the current agreement that lists the backend
      - name: agreement
        type: string
        required: false
        description: The id of the current agreement that gives the ceiling. Absent when none does
      - name: not_after
        type: int64
        required: false
        description: When that agreement lapses. Absent when none gives the ceiling
      - name: address
        type: string
        required: false
        description: Where the backend is reached, as the base URL of its endpoint, so that an external boundary can recognise a call to it. Absent for a backend that runs as a program on the tenant's host, and for a name the tenant's model configuration gives no address

  DestinationRefusal:
    description: |
      Why the destination gate refused a send. Carried in the detail of
      SCOPE_MISSING and SCOPE_CEILING_EXCEEDED. See The gate
    fields:
      - name: destination
        type: string
        required: true
        description: The destination refused, as the gate that refused it names it — a replica's id, a model backend's or an api-ai provider's name, `mcp` for the caller of a hub's MCP surface, or the target an external boundary refused
      - name: ceiling
        type: ScopeLevel
        required: true
        description: The destination's ceiling when the request was refused
      - name: items
        type: "[]DestinationItem"
        required: true
        description: Each item that was to be sent above the ceiling or undeclared, and nothing else

  DestinationItem:
    description: One item a destination refused
    fields:
      - name: ref
        type: string
        required: true
        description: What the item is, as the sender knows it — for a content entry, its repository and path
      - name: scope
        type: ScopeLevel
        required: false
        description: Its scope. Absent when it is undeclared
```

---

## Scope Propagation

Scope travels with the entity through every boundary crossing. This
section defines the rules for how scope propagates between components.

### Propagation Rules

When an entity crosses a boundary (agent-to-agent, hub-to-hub,
hub-to-client), its scope metadata is carried in the transfer
envelope. The receiving component MUST:

1. **Read** the scope metadata from the envelope
2. **Validate** that it is authorized to handle data at this scope level
3. **Adopt** the scope for all local operations on this data
4. **Propagate** the scope on any further transfers

If the receiving component is not authorized for the declared scope,
it MUST reject the transfer and emit a `scope.violation` event.

### Cross-Boundary Scenarios

**Agent A sends confidential-scoped data to Agent B:**

```
Agent A                          Agent B
  │                                │
  │ POST /v1/message               │
  │ { scope: "confidential",       │
  │   payload: { ... } }           │
  │ ───────────────────────────►   │
  │                                │ 1. Read scope: confidential
  │                                │ 2. Validate: agent authorized
  │                                │    for confidential? Yes.
  │                                │ 3. Process at confidential level
  │                                │ 4. Any output carries scope ≥
  │                                │    confidential
```

**Workflow combines public + restricted data:**

```
Phase 1 output: { scope: public,     data: "..." }
Phase 2 output: { scope: restricted, data: "..." }

Workflow result: { scope: restricted }
  ↑ Escalation: highest component scope wins
```

**Hub A sends data to Hub B (federation):**

```
Hub A                            Hub B
  │                                │
  │ Federated transfer             │
  │ envelope.scope: restricted     │
  │ ───────────────────────────►   │
  │                                │ 1. Read scope from envelope
  │                                │ 2. Validate against local
  │                                │    policies
  │                                │ 3. Apply local enforcement
  │                                │    (may be stricter)
```

**Client requests data:**

```
Agent                            Client SDK
  │                                │
  │ Response                       │
  │ { scope: "confidential",       │
  │   display_rules: {             │
  │     mask_fields: ["email"],    │
  │     log_access: true } }       │
  │ ───────────────────────────►   │
  │                                │ Client SDK enforces
  │                                │ display_rules locally
```

### Propagation in Message Envelopes

Scope metadata is carried in a standard `scope` field on all message
and event envelopes:

```json
{
  "event_id": "evt-a1b2c3d4e5f6",
  "topic": "task.complete",
  "source": "content-analyzer",
  "scope": "confidential",
  "scope_metadata": {
    "level": "confidential",
    "context": "content",
    "propagation_rule": "inherit",
    "custom_labels": ["pii"],
    "declared_by": "content-analyzer",
    "declared_at": 1712160001
  },
  "payload": { }
}
```

The `scope` field (string) provides backward-compatible simple scoping.
The `scope_metadata` field (object) carries full `ScopeDeclaration`
for components that support the scope pattern. Components that do not
support the scope pattern MUST still preserve both fields on any
forwarding or re-publishing.

---

## Scope Escalation

When multiple entities are composed — a message with multiple fields,
a workflow aggregating phase outputs, a response combining data from
multiple agents — the composite inherits the highest scope of any
component.

### Escalation Algorithm

```
function compute_effective_scope(components):
    max_level = public

    for each component in components:
        if component.scope.propagation_rule == "fixed":
            continue  # fixed-scope components are excluded from escalation
        if component.scope.level > max_level:
            max_level = component.scope.level
            escalation_source = component.identifier

    if max_level > composite.declared_scope:
        emit scope.escalation event
        composite.effective_scope = max_level

    return max_level
```

### Escalation Examples

**Message with mixed-scope fields:**

```yaml
message:
  effective_scope: restricted  # highest of all payload fields
  payload:
    user_name:
      value: "Alice"
      scope: public
    email:
      value: "alice@example.com"
      scope: restricted
    department:
      value: "Engineering"
      scope: internal
```

The message contains fields at public, internal, and restricted levels.
The effective scope is `restricted` — the highest component scope.

**Workflow with mixed-scope phases:**

```yaml
workflow_execution:
  effective_scope: confidential
  phases:
    - name: fetch-public-data
      output_scope: public
    - name: analyze-with-pii
      output_scope: confidential
    - name: format-results
      output_scope: public
  # Phase "analyze-with-pii" escalates the entire workflow to confidential
```

---

## Scope Evaluation

Scope evaluation computes the effective enforcement for an entity by
combining its declared scope with the active environment profile.

### Evaluation Algorithm

```
function evaluate_scope(entity, environment):
    declared = entity.scope.level
    profile = environment

    # Check for per-level override
    if declared in profile.scope_overrides:
        enforcement = profile.scope_overrides[declared].enforcement
    else:
        enforcement = resolve_from_base(declared, profile.enforcement_level)

    return ScopeEvaluation {
        entity: entity.id,
        declared_scope: entity.scope,
        effective_scope: declared,  # classification never changes
        effective_enforcement: enforcement,
        environment: profile.name
    }

function resolve_from_base(level, base_enforcement):
    if base_enforcement == "strict":
        return "enforce"  # all levels enforced
    if base_enforcement == "moderate":
        if level >= confidential:
            return "enforce"
        return "audit"
    if base_enforcement == "permissive":
        if level >= critical:
            return "enforce"
        return "audit"
```

### Key Distinction: Classification vs Enforcement

Classification is permanent. A field declared `restricted` is always
`restricted`, in every environment. Enforcement varies:

| | Development | Staging | Production |
|---|---|---|---|
| **Classification** | restricted | restricted | restricted |
| **Enforcement** | audit (log only) | enforce (deny) | enforce (deny) |

This separation allows developers to work with realistic data
classifications without being blocked in development, while
maintaining full protection in production.

---

## Environment Profiles

Environment profiles define how scope enforcement varies across
deployment environments. Classification is constant; enforcement
adapts.

### Built-in Profiles

```yaml
environments:
  development:
    enforcement_level: permissive
    scope_overrides:
      restricted:
        enforcement: audit
        reason: "Allow development access; log for awareness"
      critical:
        enforcement: enforce
        reason: "Critical data is always enforced, even in dev"

  staging:
    enforcement_level: moderate
    scope_overrides:
      confidential:
        enforcement: enforce
        reason: "Staging mirrors production for confidential+"

  production:
    enforcement_level: strict
    # No overrides — all scope levels enforced at maximum
```

### Enforcement Resolution

The enforcement for a specific scope level in a specific environment
is resolved as:

1. Check `scope_overrides` for the level → if present, use override
2. Fall back to `enforcement_level` base rules
3. Production MUST always resolve to `enforce` or `block` — never `audit`
4. The destination gate is not resolved from a profile. It denies in every
   environment ([The gate](#the-gate))

### Custom Environments

Operators MAY define custom environment profiles:

```yaml
environments:
  qa-automated:
    enforcement_level: moderate
    custom_name: "QA Automated Testing"
    scope_overrides:
      restricted:
        enforcement: audit
        reason: "Automated tests need access to restricted test data"

  dr-failover:
    enforcement_level: strict
    custom_name: "Disaster Recovery Failover"
    # Mirrors production enforcement
```

---

## Configuration

```yaml
scope:
  default_level: internal                # applied when no scope is declared
  propagation_mode: inherit              # default propagation rule
  escalation_strategy: maximum           # default escalation strategy
  violation_action: deny                 # default action on scope violation
  environment: production                # active environment profile
  custom_labels: {}                      # labels this component registers (Label Registration)
  audit:
    log_all_access: false                # log every access, not just violations
    tamper_evident: false                # enable cryptographic audit integrity
  enforcement:
    reject_unscoped: false               # reject entities without scope declaration
    strict_propagation: true             # fail if scope cannot be propagated
```

### Runtime Configuration

The following configuration parameters control scope behavior at runtime:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Default scope level | `internal` | Scope applied to unclassified entities |
| Active environment | `production` | Active environment profile |
| Violation action | `deny` | Default enforcement on violation (`audit`, `deny`, `block`) |
| Reject unscoped | `false` | Whether to reject entities without scope declaration |
| Strict propagation | `true` | Whether to fail if scope cannot be propagated |

How these parameters are supplied (environment variables, configuration
files, secrets manager) is platform-specific — see the relevant
`platforms/*.md` blueprint.

---

## Scope Application Examples

Scope is universal. The same classification model applies to every
entity type. Here are practical examples of scope declarations on
different entity types.

### Data Fields

Individual fields in a data model carry their own scope:

```yaml
fields:
  email:
    type: string
    scope: restricted
    scope_metadata:
      custom_labels: ["pii"]
      propagation_rule: inherit
  display_name:
    type: string
    scope: public
  ssn:
    type: string
    scope: critical
    scope_metadata:
      custom_labels: ["pii", "regulatory"]
      propagation_rule: inherit
  department:
    type: string
    scope: internal
  salary:
    type: number
    scope: confidential
    scope_metadata:
      custom_labels: ["financial"]
      propagation_rule: inherit
```

### Operations

Operations carry scope that determines who can invoke them and what
approval is required:

```yaml
operations:
  delete_database:
    scope: critical
    scope_metadata:
      context: "infrastructure"
      custom_labels: ["destructive"]
  export_user_data:
    scope: restricted
    scope_metadata:
      context: "compliance"
      custom_labels: ["pii", "bulk-export"]
  read_record:
    scope: internal
  list_public_pages:
    scope: public
  update_billing:
    scope: confidential
    scope_metadata:
      context: "billing"
      custom_labels: ["financial"]
```

### Messages

Messages carry an effective scope computed from their payload fields:

```yaml
message:
  effective_scope: restricted  # highest of all payload fields
  payload:
    user_name:
      value: "Alice"
      scope: public
    email:
      value: "alice@example.com"
      scope: restricted
    preferences:
      value: { theme: "dark" }
      scope: internal
```

### Agents

Agents declare their operational scope — the maximum scope level
they are authorized to handle:

```yaml
agent:
  name: content-analyzer
  operational_scope: confidential
  scope_metadata:
    context: "content analysis pipeline"
    # This agent can handle public, internal, and confidential data
    # It MUST reject restricted or critical data
```

When an agent receives data above its operational scope, it MUST
reject the request and emit a `scope.violation` event:

```
content-analyzer receives restricted-scoped data
→ agent.operational_scope (confidential) < data.scope (restricted)
→ REJECT: emit scope.violation event
→ Return ErrorResponse { code: "SCOPE_EXCEEDED", category: "permanent" }
```

### Resources

Infrastructure resources carry scope to determine access controls:

```yaml
resources:
  user_database:
    scope: restricted
    scope_metadata:
      custom_labels: ["pii", "persistence"]
  cache_layer:
    scope: internal
  cdn_assets:
    scope: public
  encryption_keys:
    scope: critical
    scope_metadata:
      custom_labels: ["key-material"]
```

---

## Custom Scope Labels

The five built-in levels cover most classification needs. For
domain-specific requirements, custom labels extend the model without
replacing it.

### Label Registration

Custom labels are registered in the `scope.custom_labels` configuration of
the component that enforces them: a domain's for what that domain enforces,
and the content service's for every repository it holds
([`architecture/content`](../architecture/content.md#an-entrys-scope), where
the tenant registers a label). Each names in `maps_to` the least level it may
be declared with:

```yaml
custom_labels:
  pii:
    maps_to: restricted
    description: "Personally identifiable information"
  hipaa:
    maps_to: critical
    description: "Data subject to HIPAA regulations"
  financial:
    maps_to: confidential
    description: "Financial data requiring audit trail"
  export_controlled:
    maps_to: restricted
    description: "Data subject to export control regulations"
  telemetry:
    maps_to: internal
    description: "System telemetry and metrics data"
```

### A label and its level

A label is never a level. It is carried beside one, and these rules decide how
the two combine, for every entity including a content entry:

1. **The level is always one of the five.** A declaration whose level is a
   label, registered or not, or any other value, is refused with
   `SCOPE_INVALID_LEVEL`. A label with no level beside it declares no level;
   rule 4 says what a registered one gives where nothing checked it.
2. **A registered label sets the least level it may be declared with.** Its
   `maps_to` is that level. A declaration whose level is below the `maps_to` of
   a registered label it carries is refused, and never raised to fit. The
   refusal names the label and both levels. This pattern's code for it is
   `SCOPE_INVALID_LEVEL`. A component whose contract names its own code for a
   declaration below what applies to it uses that one, as
   [`architecture/content`](../architecture/content.md#a-scope-only-rises)
   uses `CONTENT_SCOPE_LOWERED`.
3. **A label the component has not registered sets nothing.** It is carried
   and preserved, and the declared level is enforced.
4. **Where nothing checked a declaration, a registered label still sets its
   least level.** A level a component reads from something rule 2 was never
   applied to — bytes it did not write, a version kept from before it held
   them, a copy it observed — is the higher of the level declared beside the
   label and the label's `maps_to`, and a registered label with no level
   beside it gives its `maps_to`. What rule 2 would have refused is never
   classified below the label, so an entity that carries a registered label
   is never sent, copied or recorded below its `maps_to`.

So `scope: confidential` with `pii`, where `pii` is registered as above, is
refused, and `scope: restricted` with `pii` is `restricted`. Found in bytes
nothing checked, the first is `restricted`, and so is `pii` with no level
beside it. Where `pii` is not registered, the first is `confidential`,
carrying `pii`.

`pii` is also a label the platform acts on, registered or not:
[`architecture/content`](../architecture/content.md#where-an-entry-labelled-pii-is-kept)
keeps an entry carrying it in a records repository.

### Label Resolution

When a component encounters a custom label it does not recognize, it
enforces the level declared beside it:

```
Entity scope: { level: critical, custom_labels: ["hipaa"] }

Component A (knows "hipaa"): applies HIPAA-specific protections
Component B (doesn't know "hipaa"): enforces "critical", the declared level
```

This ensures interoperability: custom labels add context for components that
understand them, and every component enforces the level. Where `hipaa` is
registered, that level is at least its `maps_to`: rule 2 was checked where it
was declared, and rule 4 sets it where nothing checked it.

---

## Scope in Federation

When entities cross hub boundaries via federation, scope is preserved
in the federation envelope:

```yaml
federation_transfer:
  source_hub: "acme-corp"
  target_hub: "partner-org"
  entity_scope:
    level: confidential
    custom_labels: ["financial"]
    declared_by: "acme-corp::content-analyzer"
  federation_policy:
    allow_scope_levels: [public, internal, confidential]
    deny_scope_levels: [restricted, critical]
```

### Federation Scope Rules

1. **Hub-level scope policy** — Hubs declare which scope levels they
   accept from federated peers. A hub may refuse restricted or
   critical data from external hubs.
2. **Scope preservation** — The receiving hub preserves the original
   scope declaration. It does not reclassify incoming data.
3. **Enforcement stacking** — The receiving hub applies its own
   environment profile on top of the preserved scope. If the
   receiving hub's policies are stricter, the stricter rules apply.
4. **Custom label passthrough** — Unknown custom labels are preserved
   in metadata, and the level declared beside them is enforced.

---

## Error Handling

### Scope-Related Errors

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `SCOPE_EXCEEDED` | 403 | permanent | Entity scope exceeds component's operational scope |
| `SCOPE_PROPAGATION_FAILED` | 500 | transient | Scope metadata could not be attached to transfer envelope |
| `SCOPE_INVALID_LEVEL` | 400 | permanent | Declared scope level is not one of the five built-in levels, or is below the `maps_to` of a registered custom label the declaration carries ([A label and its level](#a-label-and-its-level)) |
| `SCOPE_FEDERATION_DENIED` | 403 | permanent | Receiving hub does not accept this scope level from federated peers |

`SCOPE_MISSING` and `SCOPE_CEILING_EXCEEDED` are registered with their HTTP
status in [`protocol/types`](../protocol/types.md#errorresponse), because
every sender [The gate](#the-gate) binds answers with them, whatever component
it is. [The gate](#the-gate), and `reject_unscoped` under
[Configuration](#configuration), say when each is answered, and a refusal at
a destination carries a `DestinationRefusal` as its detail.

### Error Response Examples

```json
{
  "error": "Entity scope (restricted) exceeds agent operational scope (confidential)",
  "code": "SCOPE_EXCEEDED",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "entity_scope": "restricted",
    "agent_scope": "confidential",
    "agent": "content-analyzer"
  }
}
```

```json
{
  "error": "Entity has no scope declaration",
  "code": "SCOPE_MISSING",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "entity": "record-12345",
    "config": "reject_unscoped=true"
  }
}
```

---

## Implementation Notes

- Scope is metadata, not access control. Scope classifies entities;
  other patterns (auth, policies, governance) consume the classification
  to make access decisions. Scope itself does not authenticate or
  authorize — it informs.
- The `scope` string field on envelopes provides backward compatibility
  with components that predate the scope pattern. The `scope_metadata`
  object carries the full `ScopeDeclaration`. Both MUST be present on
  all envelopes.
- Scope evaluation SHOULD be performed once at the boundary (when data
  enters a component) and cached for the duration of the request.
  Re-evaluating scope on every field access is unnecessary overhead.
- The configured default scope level applies only to entities
  that have no explicit scope declaration. Implementations SHOULD
  log a warning when defaulting is applied, as it may indicate a
  missing classification.
- A label never stands in for the level during a cross-boundary
  transfer: the level travels beside it. Components SHOULD preserve
  unknown labels in metadata for downstream components that may
  understand them.
- Environment profiles are loaded at component startup from
  configuration. Profile changes require a component restart or
  configuration reload — they do not change mid-request.
- Scope escalation in composites is computed at composition time, not
  at access time. When a message is assembled from multiple fields,
  the effective scope is computed once and attached to the message
  envelope.
- Federation scope policies are declared in the hub's configuration.
  They are evaluated at the federation boundary, before the entity
  enters the receiving hub's internal routing.
- Tamper-evident audit (for critical scope) uses cryptographic hashing
  of audit entries. The specific hash algorithm is implementation-
  dependent but MUST be collision-resistant (SHA-256 minimum).

---

## Verification Checklist

- [ ] Every entity type (data field, operation, message, agent, resource) can declare a scope level
- [ ] Scope levels form a strict ordinal hierarchy: public < internal < confidential < restricted < critical
- [ ] Undeclared entities receive the configured default scope level with a logged warning
- [ ] Scope metadata propagates across agent-to-agent transfers via message/event envelopes
- [ ] Scope metadata propagates across hub-to-hub transfers via federation envelopes
- [ ] Receiving components validate incoming scope against their operational scope
- [ ] Components reject entities that exceed their operational scope with `SCOPE_EXCEEDED` error
- [ ] Composite entities escalate to the highest scope of any non-fixed component
- [ ] Escalation emits a `scope.escalation` event with the escalation source
- [ ] Fixed propagation rule (`propagation_rule: fixed`) excludes a component from escalation
- [ ] Environment profiles modify enforcement without changing classification
- [ ] Development environment permits audit-only enforcement for restricted scope
- [ ] Production environment enforces all scope levels at maximum strictness
- [ ] Critical scope is enforced (not just audited) in ALL environments including development
- [ ] A declaration whose level is a custom label, or anything but one of the five built-in levels, is refused with `SCOPE_INVALID_LEVEL`
- [ ] A declaration whose level is below the `maps_to` of a registered custom label it carries is refused, naming the label and both levels, and is never raised to fit
- [ ] Bytes a component did not write, carrying a registered label whose `maps_to` is `restricted` beside `scope: internal` or beside no level, are classified `restricted` wherever the component records, copies or sends them
- [ ] A component that does not know a custom label preserves it and enforces the level declared beside it, during cross-boundary transfers included
- [ ] `scope.violation` events are emitted on every scope boundary violation
- [ ] `scope.override` events are emitted when environment profiles modify enforcement
- [ ] Both `scope` (string) and `scope_metadata` (object) fields present on all envelopes
- [ ] Scope-related errors use standard ErrorResponse format with appropriate codes
- [ ] Federation transfers preserve scope and apply receiving hub's enforcement policies
- [ ] Nothing undeclared is sent to a destination, whatever `reject_unscoped` says, and the refusal is `SCOPE_MISSING`
- [ ] A sender refuses content above a destination's ceiling, naming the destination, its ceiling and each item above it, and sends nothing: it never drops, masks or redacts part of the content to send the rest
- [ ] A client takes the scope of what it would send, and a destination's ceiling, from the tenant; a level it cannot learn is undeclared, and a ceiling it cannot learn is the one the destination has with nothing attested
- [ ] The destination gate denies in every environment profile, `development` included, and no profile makes it audit-only
- [ ] A model provider with no current agreement attestation has the ceiling `internal`, and a `confidential` request to it is refused with `SCOPE_CEILING_EXCEEDED`
- [ ] A `ProviderAgreement` is recorded or withdrawn only on a person's operator token holding `model:attest`; a token holding `admin:*` and not `model:attest` is refused; one naming a level above `confidential`, or a `not_after` more than 90 days ahead, is refused; and after `not_after` or withdrawal the provider's ceiling is `internal`
- [ ] A `PUT /v1/admin/model` that changes the backend a name a current agreement lists reaches withdraws that agreement, and the ceiling routes then answer that name `internal`; one that keeps the name and changes only the model asked for withdraws nothing
- [ ] A backend is found by the name the tenant's model configuration spells, and a name no current agreement lists has the ceiling `internal`
- [ ] Nothing `restricted` or `critical` is sent to a model provider, whatever its ceiling, a model the tenant runs itself included
- [ ] Any part of a content entry is sent at that entry's `ContentEntry.scope`, and any part of an unclassified entry is refused with `SCOPE_MISSING`
- [ ] Resolution, fallback, failover, budget downgrade and a caller's override each choose only a destination whose ceiling covers what is sent, refuse when none does, and never send to a lower-ceiling destination transparently
