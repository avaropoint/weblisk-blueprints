<!-- blueprint
type: pattern
name: privacy
version: 1.0.0
requires: [protocol/types, patterns/scope, patterns/policy, patterns/contract]
platform: any
tier: free
-->

# Privacy Pattern

Universal privacy primitives for the Weblisk platform. Privacy is
not tied to any specific data type, domain, or regulation. It defines
consent, masking, anonymization, data minimization, right-to-erasure,
and lineage tracking as composable primitives that any component can
extend. Privacy is driven by scope — higher scope levels trigger
stricter privacy protections automatically.

## Overview

Before this pattern, the Weblisk framework deferred all privacy
responsibility to applications (`architecture/data-security`). The
framework provided secure transport; applications provided their own
consent, masking, retention, and erasure mechanisms. This worked for
simple cases but failed at scale — every agent reinvented the same
primitives, with inconsistent enforcement and no composability.

This pattern changes that. The framework now provides a universal
privacy layer:

1. **Consent model** — purpose-bound, revocable, auditable consent
   records that govern data collection and processing
2. **Field masking** — scope-driven masking at enforcement boundaries
   based on consumer identity and authority level
3. **Anonymization** — irreversible transformation of identifying data
   for aggregate analysis and reporting
4. **Data minimization** — contracts declare minimum required fields;
   extra fields are stripped at the boundary
5. **Right to erasure** — cascading deletion through the lineage graph
   with verification across all stores
6. **Lineage tracking** — every data exchange is recorded for audit,
   cascading operations, and compliance

Privacy composes with existing patterns. Scope provides the activation
threshold. Policy provides the rules engine. Contracts carry the
consent and minimization requirements. Federation boundaries enforce
masking and field stripping. Every privacy primitive references scope
and activates proportionally.

Weblisk remains opt-in. Public-scope data has minimal privacy overhead.
As scope increases, privacy protections activate automatically. The
system scales privacy proportionally — not uniformly.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category]
        - name: AgentManifest
          fields_used: [name, capabilities, type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ScopeLevel
          fields_used: [public, internal, confidential, restricted, critical]
        - name: ScopeDeclaration
          fields_used: [level, context, propagation_rule, custom_labels]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/policy
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: PolicyDefinition
          fields_used: [name, scope, target, rules, enforcement, activates_at_scope]
        - name: PolicyContext
          fields_used: [identity, scope_level, environment, operation, resource, agent]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/contract
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ContractDefinition
          fields_used: [contract_name, version, scope, schema, permissions, terms]
        - name: ContractTerms
          fields_used: [ttl, retention, forwarding_rules]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Scope-driven activation** — Privacy protections activate based
   on scope level. Public-scope data has minimal privacy overhead.
   Internal-scope data gets basic lineage tracking. Confidential-scope
   data requires consent and masking. Restricted and critical data
   get full consent, masking, anonymization, and erasure support.
   The system scales privacy proportionally to sensitivity — it never
   applies maximum protection uniformly.

2. **Purpose limitation** — Data is collected and processed for a
   declared purpose. Consent is granted for that purpose only. When
   the purpose expires or consent is revoked, the data is eligible
   for erasure. No indefinite retention without explicit, auditable
   justification. Purpose is a first-class attribute, not a metadata
   afterthought.

3. **Minimization by default** — Components receive only the data
   their contracts require. Extra fields are stripped at the boundary
   by the enforcement layer — not trusted to be ignored by the
   consumer. This extends the contract pattern's permission model
   with field-level stripping based on purpose and consent.

4. **Consent is typed** — Consent is not a boolean checkbox. It is a
   structured record with purpose, scope, fields, expiry, and
   revocation mechanism. Consent can be granted per-field, per-
   purpose, per-consumer. Blanket consent is not supported — every
   grant must declare what it covers and why.

5. **Erasure is complete** — When erasure is triggered, it cascades
   through the entire lineage graph. Every agent that received the
   data is notified and must confirm deletion. Erasure is not
   "mark as deleted" — it is cryptographic confirmation that the
   data no longer exists in any store. Exceptions (legal holds,
   regulatory retention) are explicit and audited.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: consent-management
      description: Grant, track, query, and revoke purpose-bound consent records
      parameters:
        - name: action
          type: enum(grant, revoke, query, verify)
          required: true
          description: Consent lifecycle action to perform
        - name: consent
          type: ConsentRecord
          required: true
          description: The consent record to act on — see ConsentRecord type
        - name: subject_id
          type: string
          required: true
          description: Identifier of the data subject granting or revoking consent
        - name: actor
          type: string
          required: false
          description: Identity of the agent or operator performing the action on behalf of the subject
      inherits: Purpose-bound consent tracking, revocation cascade, audit logging
      overridable: true
      override_constraints: |
        Consent is always opt-in — defaults cannot be overridden to assume consent.
        Revocation must always trigger erasure evaluation.
        Consent query must return the full grant history, not just current state.

    - name: field-masking
      description: Apply scope-driven field masking to data at enforcement boundaries
      parameters:
        - name: data
          type: object
          required: true
          description: The data payload to mask
        - name: masking_rules
          type: "[]MaskingRule"
          required: true
          description: Rules that define which fields to mask and how
        - name: consumer_scope
          type: ScopeLevel
          required: true
          description: The consumer's authority level — determines which fields are visible
        - name: context
          type: PolicyContext
          required: false
          description: Full policy context for rule evaluation — identity, scope, environment
      inherits: Field-level masking, scope-based rule activation, strategy selection
      overridable: true
      override_constraints: |
        Masking rules can only be made MORE restrictive by overrides.
        A consumer at a lower scope level cannot override masking to see more data.
        Masking happens at the boundary — never at the data source.

    - name: data-minimization
      description: Strip excess fields from data at boundaries based on contract and purpose
      parameters:
        - name: data
          type: object
          required: true
          description: The data payload to minimize
        - name: contract
          type: ContractDefinition
          required: true
          description: The governing contract that declares required fields
        - name: purpose
          type: string
          required: true
          description: The declared purpose of the data exchange
        - name: minimization_rules
          type: "[]MinimizationRule"
          required: false
          description: Additional minimization rules beyond contract requirements
      inherits: Contract-driven field stripping, purpose-bound retention, transmission minimization
      overridable: true
      override_constraints: |
        Minimization can only REMOVE fields, never add them.
        Fields not declared in the contract are always stripped.
        Purpose must match a valid consent record for the subject.

    - name: erasure-cascade
      description: Propagate erasure requests through the lineage graph with verification
      parameters:
        - name: request
          type: ErasureRequest
          required: true
          description: The erasure request — subject, reason, scope
        - name: lineage
          type: "[]LineageEntry"
          required: true
          description: Lineage graph entries for the subject's data
        - name: verification_mode
          type: enum(async, sync, best_effort)
          required: false
          default: async
          description: |
            How to verify deletion across agents:
            - sync: wait for all confirmations before completing
            - async: fire requests and track confirmations over time
            - best_effort: fire requests, do not block on confirmation
      inherits: Cascading deletion, agent notification, confirmation tracking, exception handling
      overridable: true
      override_constraints: |
        Erasure cannot be overridden to skip agents in the lineage graph.
        Legal holds must be respected — held data is not deleted but is flagged.
        Erasure verification cannot be disabled for scope >= restricted.

    - name: lineage-tracking
      description: Record data movement across agents, contracts, and boundaries
      parameters:
        - name: entry
          type: LineageEntry
          required: true
          description: The lineage record to store — source, destination, contract, scope, purpose
        - name: tracking_mode
          type: enum(full, summary, disabled)
          required: false
          default: full
          description: |
            Level of lineage detail:
            - full: complete field-level tracking with payload hashes
            - summary: agent-to-agent movement without field detail
            - disabled: no tracking (only allowed for public-scope data)
      inherits: Data movement audit trail, lineage graph construction, scope propagation tracking
      overridable: true
      override_constraints: |
        Lineage tracking cannot be disabled for scope >= confidential.
        Lineage records are immutable once written — append-only.
        Lineage retention outlives data retention — kept for audit even after erasure.

  types:
    - name: ConsentRecord
      description: Purpose-bound consent grant with scope, fields, expiry, and revocation
      inherited_by: Privacy Types section
    - name: MaskingRule
      description: Field-level masking rule with strategy, scope activation, and parameters
      inherited_by: Privacy Types section
    - name: MaskingStrategy
      description: Enumeration of masking strategies with per-strategy parameters
      inherited_by: Privacy Types section
    - name: ErasureRequest
      description: Formal request to delete a subject's data across all stores
      inherited_by: Privacy Types section
    - name: ErasureResult
      description: Outcome of an erasure cascade — confirmations, pending, exceptions
      inherited_by: Privacy Types section
    - name: LineageEntry
      description: Record of data movement between agents through a contract
      inherited_by: Privacy Types section
    - name: MinimizationRule
      description: Rule for stripping excess fields based on context and purpose
      inherited_by: Privacy Types section
    - name: ErasureException
      description: Record of a field or store that could not be erased, with reason
      inherited_by: Types section

  events:
    - topic: privacy.consent_granted
      description: Emitted when a consent record is created for a subject
      payload: {subject_id, purpose, scope, fields, granted_at, expires_at, agent}
    - topic: privacy.consent_revoked
      description: Emitted when a consent record is revoked — triggers erasure evaluation
      payload: {subject_id, purpose, scope, revoked_at, revoked_by, erasure_triggered}
    - topic: privacy.masking_applied
      description: Emitted when field masking is applied to a data payload at a boundary
      payload: {consumer, scope, fields_masked, strategy, contract, timestamp}
    - topic: privacy.erasure_requested
      description: Emitted when an erasure request is initiated for a subject
      payload: {request_id, subject_id, reason, requested_by, cascading, agents_count, timestamp}
    - topic: privacy.erasure_completed
      description: Emitted when all agents in the lineage graph confirm deletion
      payload: {request_id, subject_id, agents_confirmed, exceptions, completed_at, duration_ms}
    - topic: privacy.lineage_recorded
      description: Emitted when a data movement is recorded in the lineage graph
      payload: {data_id, source_agent, destination_agent, contract, scope, purpose, timestamp}
```

---

## Scope-Privacy Activation Matrix

Privacy protections activate based on scope level. Each level includes
all protections from the levels below it. Higher levels add additional
requirements — they never remove protections from lower levels.

| Level | Consent | Masking | Minimization | Lineage | Erasure | Anonymization |
|-------|---------|---------|--------------|---------|---------|---------------|
| public | not required | none | optional | disabled | not applicable | not applicable |
| internal | not required | none | recommended | summary | on request | not applicable |
| confidential | required | field-level | required | full | required | on aggregate |
| restricted | required + per-field | full | required | full + field-level | required + cascading | required for export |
| critical | required + per-field + per-purpose | full + envelope | required | full + tamper-evident | required + verified | required always |

**Column definitions:**

- **Consent** — Whether consent records are required before processing.
  `per-field` means consent must enumerate specific fields. `per-
  purpose` means separate consent for each declared processing purpose.
- **Masking** — What masking applies when data crosses boundaries.
  `field-level` masks specific classified fields. `full` masks all
  non-public fields. `envelope` masks the entire message envelope.
- **Minimization** — Whether excess field stripping is enforced.
  `optional` means agents may transmit extra fields. `recommended`
  means agents should minimize. `required` means the enforcement
  layer strips undeclared fields.
- **Lineage** — Level of data movement tracking. `disabled` means
  no tracking. `summary` tracks agent-to-agent movement. `full`
  tracks with field detail and payload hashes. `tamper-evident` adds
  cryptographic integrity to lineage records.
- **Erasure** — Whether erasure requests are supported. `on request`
  means agents should honor erasure requests. `required` means agents
  must honor them. `cascading` means erasure propagates through the
  lineage graph. `verified` means all agents must confirm deletion.
- **Anonymization** — Whether identifying data must be anonymized.
  `on aggregate` means aggregate queries must anonymize. `for export`
  means data exported across boundaries must be anonymized. `always`
  means identifying data is anonymized at rest.

---

## Types

### ConsentRecord

A consent record is the formal grant of permission from a data subject
for a specific purpose. Consent is never blanket — it declares exactly
what it covers, for how long, and how it can be revoked.

```yaml
ConsentRecord:
  description: Purpose-bound consent grant with scope, fields, expiry, and revocation
  fields:
    - name: id
      type: string
      required: true
      description: Unique consent record identifier (generated by the consent engine)
    - name: subject_id
      type: string
      required: true
      description: Identifier of the data subject — the person whose data is being processed
    - name: purpose
      type: string
      required: true
      description: |
        Declared processing purpose — must match a registered purpose in the system.
        Examples: "analytics", "personalization", "marketing", "service_delivery".
        Purpose is not freeform — it must be from a controlled vocabulary.
    - name: scope
      type: ScopeLevel
      required: true
      description: Minimum scope level this consent applies to — consent at restricted level covers restricted and below
    - name: fields
      type: "[]string"
      required: false
      description: |
        Specific fields this consent covers. If empty, consent applies to all fields
        the contract declares for the purpose. Per-field consent is REQUIRED for
        scope >= restricted.
    - name: consumer
      type: string
      required: false
      description: Specific agent or component this consent is granted to. If empty, consent applies to any consumer with a valid contract for the purpose.
    - name: granted_at
      type: int64
      required: true
      description: Unix epoch seconds when consent was granted
    - name: expires_at
      type: int64
      required: false
      description: Unix epoch seconds when consent expires. If null, consent is indefinite but still revocable. Indefinite consent requires scope <= confidential.
    - name: revocable
      type: boolean
      required: true
      default: true
      description: Whether this consent can be revoked. Must be true for scope >= confidential. Irrevocable consent is only valid for public/internal scope with explicit justification.
    - name: revoked_at
      type: int64
      required: false
      description: Unix epoch seconds when consent was revoked. Null if still active.
    - name: revoked_by
      type: string
      required: false
      description: Identity of the actor who revoked consent — subject, operator, or system
    - name: metadata
      type: map
      required: false
      description: Additional context — regulation reference, consent source (UI, API, import), version
```

### Consent Rules

```yaml
consent_rules:
  # Scope-driven consent requirements
  public:
    consent_required: false
    description: No consent required for public-scope data processing
  internal:
    consent_required: false
    description: No consent required but recommended for audit completeness
  confidential:
    consent_required: true
    per_field: false
    per_purpose: true
    expiry_required: false
    revocable: true
    description: Consent required per purpose; revocation must be supported
  restricted:
    consent_required: true
    per_field: true
    per_purpose: true
    expiry_required: true
    revocable: true
    description: Consent required per field and per purpose with mandatory expiry
  critical:
    consent_required: true
    per_field: true
    per_purpose: true
    expiry_required: true
    revocable: true
    max_expiry_days: 365
    description: Consent required per field and per purpose; maximum 365-day expiry; annual renewal required
```

---

### MaskingRule

A masking rule defines how a specific field pattern is transformed
when data crosses a boundary and the consumer lacks sufficient scope
authority.

```yaml
MaskingRule:
  description: Field-level masking rule with strategy, scope activation, and parameters
  fields:
    - name: id
      type: string
      required: true
      description: Unique rule identifier
    - name: field_pattern
      type: string
      required: true
      description: |
        Glob or regex pattern matching field names in the payload.
        Examples: "email", "*.phone", "address.*", "ssn"
    - name: strategy
      type: MaskingStrategy
      required: true
      description: How the field value is transformed — redact, hash, truncate, generalize, noise
    - name: activates_at_scope
      type: ScopeLevel
      required: true
      default: confidential
      description: Minimum scope level at which this rule activates. Rules for lower scopes are skipped.
    - name: applies_when
      type: string
      required: false
      description: |
        Additional condition for rule activation — policy expression evaluated
        against the consumer's context. Example: "consumer.scope < field.scope"
    - name: params
      type: map
      required: false
      description: Strategy-specific parameters — see MaskingStrategy for details
    - name: preserve_type
      type: boolean
      required: false
      default: true
      description: Whether the masked value preserves the original data type (e.g., string → masked string, not null)
```

### MaskingStrategy

```yaml
MaskingStrategy:
  description: Enumeration of masking strategies with per-strategy parameters
  values:
    - name: redact
      description: Replace the entire value with a fixed placeholder
      params:
        placeholder:
          type: string
          default: "[REDACTED]"
          description: The replacement string
      example:
        input: "alice@example.com"
        output: "[REDACTED]"

    - name: hash
      description: Replace the value with a cryptographic hash (one-way, deterministic)
      params:
        algorithm:
          type: enum(sha256, sha512, blake3)
          default: sha256
          description: Hash algorithm to use
        salt:
          type: string
          required: true
          description: Per-deployment salt to prevent rainbow table attacks
      example:
        input: "alice@example.com"
        output: "a3f2b8c1..."

    - name: truncate
      description: Keep only the first N characters, replace the rest
      params:
        keep_chars:
          type: integer
          default: 3
          description: Number of leading characters to preserve
        replacement:
          type: string
          default: "***"
          description: String appended after the kept characters
      example:
        input: "alice@example.com"
        output: "ali***"

    - name: generalize
      description: Replace precise values with a broader category
      params:
        generalization_map:
          type: map
          description: |
            Mapping from value ranges or patterns to generalized labels.
            Example: age 25 → "20-30", zip 10001 → "100XX"
        precision:
          type: integer
          required: false
          description: For numeric values, the rounding precision
      example:
        input: "25"
        output: "20-30"

    - name: noise
      description: Add random noise to numeric values to preserve statistical properties while hiding individuals
      params:
        distribution:
          type: enum(gaussian, uniform, laplace)
          default: laplace
          description: Noise distribution — laplace provides differential privacy guarantees
        epsilon:
          type: float
          required: true
          description: Privacy budget parameter — lower epsilon = more noise = more privacy
        bounds:
          type: object
          required: false
          description: "{ min, max } — clamp noised values to valid range"
      example:
        input: 25
        output: 27
```

### Masking Application Order

When multiple masking rules match the same field, the most restrictive
strategy wins. Strategy restrictiveness order:

```
redact > hash > noise > generalize > truncate
```

If two rules with the same strategy match, the one with the higher
`activates_at_scope` takes precedence. Ties are broken by rule `id`
(lexicographic order) for determinism.

Masking happens at the **enforcement boundary** — the gateway, the
contract validation layer, or the federation bridge. It never happens
at the data source. The source stores unmasked data; the boundary
transforms it for the consumer. This ensures that authorized consumers
see the original data while unauthorized consumers see masked values.

---

### ErasureRequest

```yaml
ErasureRequest:
  description: Formal request to delete a data subject's data across all stores
  fields:
    - name: id
      type: string
      required: true
      description: Unique erasure request identifier
    - name: subject_id
      type: string
      required: true
      description: Identifier of the data subject requesting erasure
    - name: reason
      type: enum(consent_revoked, subject_request, purpose_expired, policy_enforcement, operator_action)
      required: true
      description: |
        Why erasure was triggered:
        - consent_revoked: subject withdrew consent
        - subject_request: explicit GDPR/CCPA-style deletion request
        - purpose_expired: the declared purpose has expired
        - policy_enforcement: a privacy policy triggered automatic erasure
        - operator_action: manual erasure by a platform operator
    - name: requested_by
      type: string
      required: true
      description: Identity of the actor who initiated the request — subject, operator, system
    - name: cascading
      type: boolean
      required: true
      default: true
      description: Whether to propagate erasure through the lineage graph to all downstream agents
    - name: legal_hold
      type: boolean
      required: false
      default: false
      description: If true, data is flagged but NOT deleted — legal hold overrides erasure
    - name: hold_reference
      type: string
      required: false
      description: Reference to the legal hold order — required when legal_hold is true
    - name: requested_at
      type: int64
      required: true
      description: Unix epoch seconds when the erasure request was initiated
    - name: deadline_at
      type: int64
      required: false
      description: Unix epoch seconds by which erasure must complete — regulatory deadline
    - name: scope_filter
      type: ScopeLevel
      required: false
      description: Only erase data at or above this scope level — if null, erase all scopes
    - name: metadata
      type: map
      required: false
      description: Additional context — regulation reference, ticket ID, justification
```

### ErasureResult

```yaml
ErasureResult:
  description: Outcome of an erasure cascade — tracks confirmation from every agent in the lineage graph
  fields:
    - name: request_id
      type: string
      required: true
      description: Reference to the originating ErasureRequest
    - name: subject_id
      type: string
      required: true
      description: The data subject whose data was erased
    - name: status
      type: enum(pending, in_progress, completed, completed_with_exceptions, failed)
      required: true
      description: Overall erasure status
    - name: agents_notified
      type: "[]string"
      required: true
      description: List of agents that received the erasure notification
    - name: agents_confirmed
      type: "[]string"
      required: true
      description: List of agents that confirmed successful deletion
    - name: agents_pending
      type: "[]string"
      required: true
      description: List of agents that have not yet confirmed
    - name: exceptions
      type: "[]ErasureException"
      required: false
      description: Agents that could not delete — legal hold, technical failure, retention requirement
    - name: started_at
      type: int64
      required: true
      description: Unix epoch seconds when the cascade began
    - name: completed_at
      type: int64
      required: false
      description: Unix epoch seconds when the last agent confirmed or the request timed out
```

### ErasureException

```yaml
ErasureException:
  description: Record of an agent that could not complete erasure
  fields:
    - name: agent
      type: string
      required: true
      description: Agent that could not delete the data
    - name: reason
      type: enum(legal_hold, regulatory_retention, technical_failure, not_found, timeout)
      required: true
      description: Why deletion could not be completed
    - name: detail
      type: string
      required: false
      description: Human-readable detail — hold reference, error message, retention policy
    - name: retry_eligible
      type: boolean
      required: true
      description: Whether the erasure can be retried for this agent
    - name: reported_at
      type: int64
      required: true
      description: Unix epoch seconds when the exception was reported
```

---

### LineageEntry

Every data exchange between agents is recorded as a lineage entry.
The lineage graph enables cascading operations — erasure, scope
changes, consent propagation — and provides the audit trail for
compliance.

```yaml
LineageEntry:
  description: Record of data movement between agents through a contract
  fields:
    - name: id
      type: string
      required: true
      description: Unique lineage entry identifier
    - name: data_id
      type: string
      required: true
      description: Identifier of the data entity being tracked — payload hash or record ID
    - name: subject_id
      type: string
      required: false
      description: Identifier of the data subject if the data is personal — enables subject-scoped lineage queries
    - name: source_agent
      type: string
      required: true
      description: Agent that sent the data
    - name: destination_agent
      type: string
      required: true
      description: Agent that received the data
    - name: contract
      type: string
      required: true
      description: Name of the governing contract for this exchange
    - name: contract_version
      type: string
      required: true
      description: Version of the governing contract
    - name: scope
      type: ScopeLevel
      required: true
      description: Scope level of the data at the time of exchange
    - name: purpose
      type: string
      required: true
      description: Declared purpose of the exchange — must match an active consent record for scope >= confidential
    - name: fields_transferred
      type: "[]string"
      required: false
      description: List of field names transferred — populated when lineage tracking is set to full
    - name: payload_hash
      type: string
      required: false
      description: SHA-256 hash of the transferred payload — for integrity verification
    - name: timestamp
      type: int64
      required: true
      description: Unix epoch seconds when the exchange occurred
    - name: metadata
      type: map
      required: false
      description: Additional context — correlation ID, federation peer, environment
```

### Lineage Retention Rules

Lineage records outlive data records. When data is erased, the lineage
entry is NOT deleted — it is marked as `data_erased: true`. This
preserves the audit trail for compliance while confirming that the
underlying data no longer exists.

```yaml
lineage_retention:
  public:
    retention: 30d
    description: Public data lineage retained for 30 days
  internal:
    retention: 90d
    description: Internal data lineage retained for 90 days
  confidential:
    retention: 1y
    description: Confidential data lineage retained for 1 year
  restricted:
    retention: 3y
    description: Restricted data lineage retained for 3 years
  critical:
    retention: 7y
    description: Critical data lineage retained for 7 years — regulatory minimum
  after_erasure:
    retain_lineage: true
    mark_as: data_erased
    description: Lineage entries survive data erasure — marked with erasure timestamp
```

---

### MinimizationRule

```yaml
MinimizationRule:
  description: Rule for stripping excess fields based on context, purpose, and contract
  fields:
    - name: id
      type: string
      required: true
      description: Unique rule identifier
    - name: context
      type: string
      required: true
      description: |
        Where this rule applies — contract name, agent name, boundary type.
        Example: "contract:user-profile-read", "boundary:federation", "agent:analytics-*"
    - name: required_fields
      type: "[]string"
      required: true
      description: Fields that MUST be present — these pass through unchanged
    - name: strip_fields
      type: "[]string"
      required: false
      description: |
        Fields that MUST be removed. If empty, all fields not in required_fields
        are stripped (allowlist mode). If populated, only these specific fields
        are stripped (denylist mode). Allowlist mode is REQUIRED for scope >= restricted.
    - name: retention_purpose
      type: string
      required: true
      description: Purpose that justifies retaining the required fields — must match an active consent record
    - name: retention_ttl
      type: string
      required: false
      description: |
        How long the receiving agent may retain the data — duration string (e.g., "30d", "1y").
        After TTL expiry, the agent must delete the data. Required for scope >= confidential.
    - name: activates_at_scope
      type: ScopeLevel
      required: false
      default: internal
      description: Minimum scope level at which this minimization rule activates
```

---

## Anonymization

Anonymization is the irreversible transformation of identifying data.
Unlike masking (which is reversible — the source retains the original),
anonymization permanently removes the ability to identify individuals.
Anonymization is required for aggregate analysis, reporting, and any
data export that crosses trust boundaries at restricted scope or above.

### Anonymization vs Pseudonymization

| Property | Pseudonymization | Anonymization |
|----------|------------------|---------------|
| Reversible | Yes (with key) | No |
| Identifying | With key access | Never |
| Regulated as personal data | Yes | No |
| Use case | Internal processing | Aggregate analysis, export |
| Key management | Required | Not applicable |

Pseudonymization replaces identifiers with tokens. The mapping from
token to identifier is stored separately and can be used to re-
identify. Pseudonymized data is still personal data under GDPR and
subject to all privacy protections.

Anonymization destroys the mapping permanently. Anonymized data is
not personal data and is exempt from erasure requests. The
transformation must be irreversible — if re-identification is possible
from the output, the data is pseudonymized, not anonymized.

### Anonymization Techniques

```yaml
anonymization_techniques:
  k_anonymity:
    description: |
      Ensure that every record in a dataset is indistinguishable from
      at least k-1 other records on quasi-identifier fields. Prevents
      singling out individuals from aggregate data.
    params:
      k:
        type: integer
        minimum: 5
        default: 10
        description: Minimum group size — records are generalized until groups of at least k exist
      quasi_identifiers:
        type: "[]string"
        required: true
        description: Fields that could identify individuals in combination — age, zip, gender
    activates_at_scope: confidential

  aggregation_threshold:
    description: |
      Refuse to release aggregate results for groups smaller than the
      threshold. Prevents inference attacks on small populations.
    params:
      minimum_group_size:
        type: integer
        minimum: 5
        default: 10
        description: Minimum count in any group before results are released
      suppression_value:
        type: string
        default: "<suppressed>"
        description: Replacement for suppressed group values
    activates_at_scope: confidential

  differential_privacy:
    description: |
      Add calibrated noise to query results so that the inclusion or
      exclusion of any single individual does not significantly affect
      the output. Provides mathematical privacy guarantees.
    params:
      epsilon:
        type: float
        default: 1.0
        description: Privacy budget — lower = more privacy, more noise
      delta:
        type: float
        default: 0.00001
        description: Probability bound for privacy guarantee failure
      mechanism:
        type: enum(laplace, gaussian)
        default: laplace
        description: Noise mechanism — laplace for pure DP, gaussian for approximate DP
    activates_at_scope: restricted
```

---

## Erasure Cascade

When an erasure request is initiated, the privacy engine traverses
the lineage graph to find every agent that holds the subject's data.
Each agent receives an erasure notification and must confirm deletion.

### Cascade Flow

```
1. Erasure request received
   ├─ Validate: subject exists, requestor authorized, no active legal hold
   ├─ Query lineage graph for all entries matching subject_id
   └─ Build agent set: unique agents that received the subject's data

2. Fan-out notifications
   ├─ For each agent in the set:
   │   ├─ Send erasure notification with request_id, subject_id, fields
   │   ├─ Agent deletes subject's data from all stores
   │   └─ Agent confirms deletion with timestamp and store list
   └─ Track confirmations in ErasureResult

3. Verification
   ├─ All agents confirmed → status: completed
   ├─ Some agents confirmed, others excepted → status: completed_with_exceptions
   ├─ Timeout reached with pending agents → retry pending agents
   └─ All agents failed → status: failed, escalate to operator

4. Post-erasure
   ├─ Mark lineage entries as data_erased (do NOT delete lineage)
   ├─ Emit privacy.erasure_completed event
   └─ Archive erasure result for audit
```

### Legal Holds

A legal hold prevents erasure of specific data even when the subject
requests deletion. Legal holds are explicit — they reference a hold
order and are time-bounded. When a legal hold is active:

- The erasure request is recorded but NOT executed for held data
- The subject is notified that their request is partially blocked
- The exception is logged with the hold reference
- When the hold expires, pending erasure requests are re-evaluated

```yaml
legal_hold:
  hold_reference: string    # External reference to the legal hold order
  subject_id: string        # Data subject affected by the hold
  scope_filter: ScopeLevel  # Scope level of held data (or null for all)
  created_at: int64         # When the hold was created
  expires_at: int64         # When the hold expires (null = indefinite, requires review)
  created_by: string        # Operator who created the hold
  review_interval_days: 90  # How often indefinite holds must be reviewed
```

---

## Privacy Policies

Privacy policies are standard `patterns/policy` definitions that
target privacy-related operations. They use the same policy engine,
evaluation context, and most-restrictive-wins composition.

### Default Privacy Policies

```yaml
default_privacy_policies:
  - name: consent-required-confidential
    description: Require consent for processing confidential data
    scope: system
    target:
      entity_type: data
      scope_level: confidential
    rules:
      - condition: "consent.active == false"
        result: deny
        message: "Processing confidential data requires active consent"
    enforcement: enforce
    activates_at_scope: confidential

  - name: masking-restricted-fields
    description: Mask restricted fields for consumers below restricted scope
    scope: system
    target:
      entity_type: field
      scope_level: restricted
    rules:
      - condition: "consumer.scope < field.scope"
        result: mask
        message: "Consumer scope insufficient — field will be masked"
    enforcement: enforce
    activates_at_scope: restricted

  - name: minimization-at-boundary
    description: Strip undeclared fields at contract boundaries
    scope: system
    target:
      entity_type: contract_exchange
      scope_level: confidential
    rules:
      - condition: "field NOT IN contract.declared_fields"
        result: strip
        message: "Field not declared in contract — stripped at boundary"
    enforcement: enforce
    activates_at_scope: confidential

  - name: lineage-required-confidential
    description: Require lineage tracking for confidential data exchanges
    scope: system
    target:
      entity_type: data_exchange
      scope_level: confidential
    rules:
      - condition: "lineage.tracking == disabled"
        result: deny
        message: "Lineage tracking required for confidential data exchanges"
    enforcement: enforce
    activates_at_scope: confidential

  - name: erasure-cascade-restricted
    description: Require cascading erasure for restricted data
    scope: system
    target:
      entity_type: erasure_request
      scope_level: restricted
    rules:
      - condition: "request.cascading == false"
        result: deny
        message: "Erasure for restricted data must cascade through lineage graph"
    enforcement: enforce
    activates_at_scope: restricted

  - name: retention-purpose-bound
    description: Data retained beyond purpose expiry must be erased
    scope: system
    target:
      entity_type: data
      scope_level: internal
    rules:
      - condition: "purpose.expired == true AND consent.active == false"
        result: erasure
        message: "Purpose expired and no active consent — data eligible for erasure"
    enforcement: audit
    activates_at_scope: internal
```

---

## Integration Points

### With patterns/scope

Scope is the activation signal for all privacy protections. Every
privacy primitive checks the scope level before activating:

- **Consent**: not required below confidential; required at and above
- **Masking**: not applied below confidential; field-level at
  confidential; full at restricted; envelope at critical
- **Minimization**: optional below confidential; required at and above
- **Lineage**: disabled for public; summary for internal; full for
  confidential and above
- **Erasure**: on-request for internal; required for confidential
  and above; verified for critical
- **Anonymization**: on-aggregate for confidential; required for
  restricted export; always for critical

When scope escalation occurs (a composite entity contains a higher-
scoped component), privacy protections escalate to match the new
effective scope. A message containing one restricted field gets
restricted-level privacy protections for the entire message.

### With patterns/contract

Contracts carry consent and minimization requirements:

- **Consent binding**: contracts can declare that processing requires
  active consent for specific purposes. The contract validation layer
  checks for active consent before allowing the exchange.
- **Field declarations**: contracts declare required fields. Fields
  not declared in the contract are stripped by the minimization layer
  at the enforcement boundary.
- **Permission extension**: the contract permission model (read,
  transform, store, forward, derive, expire) is extended with
  `consent_required` — a flag that binds the permission to an active
  consent record.
- **Retention terms**: contract terms include `retention_ttl` — how
  long the consumer may hold the data. After expiry, the consumer
  must delete the data. Retention is tied to purpose, not time alone.

### With patterns/policy

Privacy policies feed into the standard policy engine:

- Privacy policies use `PolicyDefinition` with privacy-specific
  conditions (consent state, lineage tracking, masking requirements)
- Policy evaluation context (`PolicyContext`) is extended with
  privacy attributes: `consent_active`, `lineage_tracked`,
  `masking_applied`, `subject_id`
- Privacy policies follow the same most-restrictive-wins composition
  — a privacy deny cannot be overridden by a non-privacy allow
- Privacy policy violations emit `policy.violated` events with
  privacy-specific detail

### With protocol/federation

Federation boundaries are the most critical enforcement points for
privacy:

- **Field stripping**: federation already defines forbidden field
  patterns for cross-hub data contracts. Privacy extends this model
  to ALL boundaries — not just federation. Any boundary where data
  crosses a trust perimeter applies minimization rules.
- **Masking at boundaries**: when data is forwarded to a federated
  peer, masking is applied based on the peer's trust tier and the
  data's scope level. Lower-trust peers see more masking.
- **Lineage across federation**: lineage entries for federated
  exchanges include the peer hub identifier, enabling cross-hub
  lineage graphs for cascading erasure.
- **Consent portability**: consent records can be declared as
  `portable` — when data is forwarded to a federated peer, the
  consent record travels with it. The peer must honor the consent
  terms or reject the exchange.

### With patterns/file-upload

File upload already strips EXIF metadata as a privacy mechanism.
This pattern generalizes that approach:

- **Metadata stripping**: any file metadata (EXIF, PDF metadata,
  document properties) is treated as a privacy-sensitive field
  subject to the same masking and minimization rules.
- **Scope-driven stripping**: public files may retain metadata.
  Confidential files have metadata stripped by default. Restricted
  files have all non-essential metadata removed unconditionally.

---

## Implementation Notes

### Enforcement Boundary

Privacy enforcement happens at the **boundary**, not at the source.
The source stores data in its original form. When data crosses a
boundary — agent-to-agent, agent-to-client, hub-to-federation —
the enforcement layer applies masking, minimization, and consent
checks.

This design ensures:
- Sources do not lose data by premature masking
- Different consumers see different views based on their authority
- Masking is consistent — applied by one layer, not scattered
  across every source
- Audit trails reference the original data, not the masked version

The enforcement boundary is the same layer described in
`architecture/enforcement` — the gateway, contract validation
middleware, or federation bridge. Privacy hooks into the existing
enforcement pipeline; it does not create a parallel one.

### Consent Storage

Consent records are stored by the consent engine — a system-level
service that agents query. Agents do not store consent locally.
This ensures:
- A single source of truth for consent state
- Revocation takes effect immediately across all agents
- Consent queries are consistent regardless of which agent asks
- Audit trails for consent are centralized

The consent engine exposes a query API: given a subject_id, purpose,
and consumer, return the active consent records. Agents call this
API at the enforcement boundary before processing data that requires
consent.

### Lineage Graph Storage

Lineage entries are append-only. Once written, they cannot be
modified or deleted. The lineage graph is stored by the lineage
engine — a system-level service separate from agent storage.

For tamper-evident lineage (required at critical scope), entries
are chained using cryptographic hashes — each entry includes the
hash of the previous entry, forming an integrity chain that detects
retroactive modification.

### Performance Considerations

Privacy adds overhead at boundaries. The overhead scales with scope:

| Level | Overhead | Dominant Cost |
|-------|----------|---------------|
| public | negligible | No privacy operations |
| internal | minimal | Summary lineage write |
| confidential | moderate | Consent check + full lineage + minimization |
| restricted | significant | All of above + field masking + per-field consent |
| critical | highest | All of above + tamper-evident lineage + verified erasure |

To mitigate overhead:
- **Consent caching**: active consent records are cached at the
  enforcement boundary with short TTL (consent engine pushes
  revocations to invalidate caches immediately)
- **Masking rule compilation**: masking rules are compiled into
  efficient field matchers at deploy time, not re-parsed per request
- **Lineage batching**: lineage writes are batched within a
  configurable time window (default: 100ms) to reduce write
  amplification
- **Scope short-circuit**: public-scope data bypasses the entire
  privacy pipeline — no consent check, no masking, no lineage

---

## Conformance

### Required for All Agents

- MUST propagate scope metadata on all data exchanges
- MUST honor masking rules at enforcement boundaries
- MUST respond to erasure notifications within the configured deadline
- MUST NOT process data beyond the declared purpose in the contract

### Required for Scope >= Confidential

- MUST check consent before processing subject data
- MUST track lineage for all data exchanges
- MUST strip undeclared fields at contract boundaries
- MUST support right-to-erasure requests

### Required for Scope >= Restricted

- MUST require per-field consent
- MUST apply full masking to unauthorized consumers
- MUST cascade erasure through the lineage graph
- MUST anonymize data before aggregate export

### Required for Scope = Critical

- MUST require per-field, per-purpose consent with expiry
- MUST maintain tamper-evident lineage
- MUST verify erasure completion across all agents
- MUST anonymize data at rest for all non-operational access

---

## Examples

### Consent Grant

```yaml
consent:
  id: "consent-20260427-001"
  subject_id: "user-42"
  purpose: "personalization"
  scope: confidential
  fields: ["name", "email", "preferences"]
  consumer: "recommendation-agent"
  granted_at: 1745740800
  expires_at: 1777276800
  revocable: true
```

### Masking Rule

```yaml
masking_rule:
  id: "mask-email-restricted"
  field_pattern: "*.email"
  strategy: truncate
  activates_at_scope: restricted
  applies_when: "consumer.scope < restricted"
  params:
    keep_chars: 3
    replacement: "***@***.***"
  preserve_type: true
```

### Erasure Request

```yaml
erasure:
  id: "erasure-20260427-001"
  subject_id: "user-42"
  reason: subject_request
  requested_by: "user-42"
  cascading: true
  legal_hold: false
  requested_at: 1745740800
  deadline_at: 1748332800
```

### Minimization Rule

```yaml
minimization:
  id: "min-analytics-profile"
  context: "contract:analytics-profile-read"
  required_fields: ["age_range", "region", "preference_category"]
  strip_fields: ["name", "email", "phone", "address", "ssn"]
  retention_purpose: "aggregate_analytics"
  retention_ttl: "90d"
  activates_at_scope: confidential
```

### Lineage Entry

```yaml
lineage:
  id: "lineage-20260427-001"
  data_id: "payload-hash-abc123"
  subject_id: "user-42"
  source_agent: "profile-agent"
  destination_agent: "recommendation-agent"
  contract: "user-profile-read"
  contract_version: "1.2.0"
  scope: confidential
  purpose: "personalization"
  fields_transferred: ["name", "email", "preferences"]
  payload_hash: "sha256:a3f2b8c1d4e5f6..."
  timestamp: 1745740800
```

---

## Verification Checklist

- [ ] ConsentRecord schema validates all required fields (subject_id, purpose, scope, consented_fields, granted_at, expires_at)
- [ ] Consent is evaluated before any data access — missing or expired consent produces deny
- [ ] Masking rules activate at the correct scope level (public=none, internal=pseudonymize, confidential=hash/redact, restricted/critical=redact)
- [ ] MaskingStrategy parameters are validated (e.g. hash requires algorithm + salt, pattern requires regex + replacement)
- [ ] Erasure cascades propagate to all stores holding subject data — no orphaned records remain
- [ ] ErasureResult includes confirmations for every store, plus exceptions for stores that could not erase
- [ ] Legal-hold subjects are excluded from erasure — request returns hold_active exception
- [ ] LineageEntry records are immutable (append-only) and survive data erasure
- [ ] Lineage tracking cannot be disabled for scope >= confidential
- [ ] MinimizationRule strips undeclared fields before data crosses contract boundaries
- [ ] `privacy.consent_revoked` event triggers downstream cleanup within the configured deadline
- [ ] `privacy.erasure_completed` event includes full ErasureResult with per-store outcomes
- [ ] Consent record expiry is enforced — expired consent is functionally equivalent to revoked
- [ ] Data purpose restriction is enforced — data accessed under one purpose cannot be used for another
- [ ] All privacy events follow the standard event envelope from protocol/spec
