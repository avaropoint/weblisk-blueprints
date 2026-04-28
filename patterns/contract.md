<!-- blueprint
type: pattern
name: contract
version: 1.0.0
requires: [protocol/types, patterns/scope]
platform: any
tier: free
-->

# Contract Pattern

Formal collaboration agreement between any two parties in the
Weblisk system. A contract defines what is exchanged, under what
scope, governed by what terms, and what the receiving party is
allowed to do with the data. Contracts are the universal boundary
between components — agents, domains, hubs, and clients.

## Overview

The Weblisk protocol defines `IOSpec` as `{name, type, description}`
— a loose description of what an agent accepts. This is insufficient
for a platform where components must compose reliably across trust
boundaries. This pattern replaces loose descriptions with machine-
checkable collaboration agreements:

1. **Schema declaration** — structured definitions with typed fields
   and per-field scope classification
2. **Versioning** — backward/forward compatibility rules
3. **Validation** — envelope format with scope-aware enforcement
4. **Permission model** — what the consumer can do with received data
5. **Collaboration terms** — TTL, retention, rate limits, forwarding
6. **Policy binding** — contracts can reference governing policies
7. **Contract testing** — producer/consumer compatibility checks
8. **Discovery** — contracts are inspectable at runtime

A contract is not limited to agent I/O. Any exchange in the system
can be governed by a contract: agent↔agent, agent↔hub, hub↔hub,
agent↔client, domain↔domain. The contract is the formal boundary
where obligations are declared and enforced.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: IOSpec
          fields_used: [name, type, description]
        - name: ErrorResponse
          fields_used: [error, code, category, retryable]
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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Universal collaboration boundary** — A contract is the formal
   agreement between ANY two components that exchange information. It
   defines what is exchanged, under what scope, governed by what
   terms. Not limited to data schemas. Agent↔agent, agent↔hub,
   hub↔hub, agent↔client — every exchange follows the same model.

2. **Scope propagation** — Every contract carries scope metadata.
   When data moves through a contract, its scope level travels with
   it. The receiving party inherits the scope obligations. A single
   `restricted` field in a `public` contract makes the effective
   scope of the exchange `restricted`, following scope escalation
   rules from `patterns/scope`.

3. **Machine-checkable** — Contracts use the same type system as
   `patterns/storage` for schema fields. Compatibility is validated
   at deploy time, not runtime. If two components declare compatible
   contracts, their schemas are guaranteed to align before any
   message is exchanged.

4. **Consumer obligations** — Contracts don't just define what data
   looks like; they define what the consumer is ALLOWED TO DO with
   it. Read-only? Can transform? Can forward to third parties? Must
   expire after N hours? Permissions are declared in the contract
   and enforced by the receiving component.

5. **Backward compatible** — Agents that don't declare contracts
   continue to function (legacy mode). Contract enforcement is
   opt-in at the per-agent level but MANDATORY for scope >=
   confidential. Legacy agents exchanging confidential data MUST
   upgrade to contract-based exchange.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: contract-declaration
      description: Collaboration agreement with schema, permissions, terms, and scope
      parameters:
        - { name: contract_name, type: string, required: true }
        - { name: version, type: string, required: true }
        - { name: scope, type: "enum(public,internal,confidential,restricted,critical)", required: true }
        - { name: parties, type: "[]enum(agent,domain,hub,client,external)", required: true }
        - { name: schema, type: object, required: true, description: Typed fields with per-field scope }
        - { name: permissions, type: "[]enum(read,transform,store,forward,derive,expire)", required: true }
        - { name: terms, type: object, required: false, description: TTL, retention, forwarding }
        - { name: policies, type: "[]string", required: false, description: Governing policy names }
      inherits: Schema validation, versioning, envelope format, scope propagation, permission enforcement
      overridable: true
      override_constraints: Must preserve envelope format and semver rules. Permissions narrow only.

    - name: contract-validation
      description: Envelope validation with scope checking and permission verification
      parameters:
        - { name: contract, type: string, required: true }
        - { name: version, type: string, required: true }
        - { name: scope, type: "enum(public,internal,confidential,restricted,critical)", required: true }
        - { name: payload, type: object, required: true }
      inherits: Version check, type validation, constraint enforcement, scope verification
      overridable: false

    - name: contract-negotiation
      description: Runtime term agreement between parties for dynamic contracts
      parameters:
        - { name: initiator, type: string, required: true }
        - { name: responder, type: string, required: true }
        - { name: proposed_contract, type: object, required: true }
      inherits: Version compatibility, scope requirements
      overridable: true
      override_constraints: Scope escalates only. Permissions narrow only.

    - name: contract-lifecycle
      description: Versioning, deprecation, and migration of contracts
      parameters:
        - { name: contract_name, type: string, required: true }
        - { name: action, type: "enum(publish,deprecate,migrate,retire)", required: true }
        - { name: migration_path, type: string, required: false }
      inherits: Semver rules, compatibility checks
      overridable: false

  types:
    - name: ContractDefinition
      description: Full declaration — schema, scope, permissions, terms, policy bindings
    - name: ContractSchema
      description: Typed field definitions with per-field scope and constraints
    - name: ContractPermission
      description: "enum: read, transform, store, forward, derive, expire"
    - name: ContractTerms
      description: TTL, retention, rate limits, forwarding rules, scope minimum
    - name: ContractParty
      description: "enum: agent, domain, hub, client, external"
    - name: EventEnvelope
      description: Standard wrapper — contract, version, scope, payload
    - name: ContractViolation
      description: Violation record — contract, party, rule, severity, payload hash

  endpoints:
    - path: /v1/describe (contracts field)
      description: Runtime discovery of contract declarations

  events:
    - topic: contract.validated
      payload: { contract: string, version: string, scope: string, sender: string, receiver: string }
    - topic: contract.violated
      payload: { contract: string, party: string, rule_violated: string, severity: string, payload_hash: string }
    - topic: contract.negotiated
      payload: { contract: string, version: string, initiator: string, responder: string, scope: string }
    - topic: contract.deprecated
      payload: { contract: string, version: string, migration_target: string, deprecated_at: int }

---

## Types

All types declared in the Contracts section are defined below,
organized by concern.

### Party Types

Contracts govern exchange between any two parties. Each party type
has different trust characteristics and default permission sets:

| Party | Description | Default Trust | Typical Scope |
|-------|-------------|---------------|---------------|
| `agent` | Registered agent within a hub | High (registered + verified) | Any |
| `domain` | Domain controller aggregating agents | High (structural trust) | >= internal |
| `hub` | Orchestrator / hub instance | Varies by federation tier | >= internal |
| `client` | External client consuming agent APIs | Low (authenticated but external) | <= confidential |
| `external` | Cross-boundary party via federation | Lowest (explicit trust required) | Per federation contract |

### Party Combinations

| Exchange | Contract Required | Notes |
|----------|-------------------|-------|
| agent ↔ agent | Recommended | Required when scope >= confidential |
| agent ↔ domain | Recommended | Domain controllers validate contracts |
| agent ↔ hub | Required | Hub enforces contract at registration |
| agent ↔ client | Required | Client-facing contracts define API surface |
| hub ↔ hub | Required | Federation contracts (see `protocol/federation`) |
| domain ↔ domain | Recommended | Cross-domain exchanges within a hub |
| agent ↔ external | Required | Cross-boundary, governed by federation trust |

---

### Contract Declaration

Every component declares its contracts in its blueprint. Contracts
are organized by role — what the component accepts (inputs) and
what it produces (outputs):

```yaml
contracts:
  scope: confidential
  parties: [agent, domain]

  inputs:
    <contract-name>:
      version: <semver>
      description: <one-line>
      scope: <scope-level>
      permissions: [<allowed-actions>]
      terms:
        ttl: <seconds>
        retention: <hours>
        forwarding: <allowed|restricted|denied>
      policies: [<policy-names>]
      schema:
        <field>:
          type: <type>
          required: <bool>
          scope: <scope-level>
          description: <one-line>
          constraints: <rules>

  outputs:
    <contract-name>:
      version: <semver>
      description: <one-line>
      scope: <scope-level>
      permissions: [<allowed-actions>]
      terms:
        ttl: <seconds>
        retention: <hours>
        forwarding: <allowed|restricted|denied>
      policies: [<policy-names>]
      schema:
        <field>:
          type: <type>
          required: <bool>
          scope: <scope-level>
          description: <one-line>
          constraints: <rules>
```

### Schema Field Types

Uses the same type system as `patterns/storage`:

| Type | Description |
|------|-------------|
| `string` | UTF-8 text |
| `text` | Long-form text |
| `int` | 64-bit signed integer |
| `float` | 64-bit floating point |
| `boolean` | True/false |
| `timestamp` | Unix epoch seconds (int64) |
| `json` | Arbitrary JSON object |
| `[]<type>` | Array of type |
| `enum(<values>)` | Enumerated values |
| `uuid` | UUID string |
| `map` | Key-value map |

### Constraint Syntax

Inline constraints for schema fields:

| Constraint | Applies To | Example |
|------------|-----------|---------|
| `min:<n>` | int, float | `min:0` |
| `max:<n>` | int, float | `max:100` |
| `min_length:<n>` | string | `min_length:1` |
| `max_length:<n>` | string | `max_length:255` |
| `pattern:<regex>` | string | `pattern:^[a-z]+$` |
| `min_items:<n>` | array | `min_items:1` |
| `max_items:<n>` | array | `max_items:100` |
| `not_empty` | string, array | field must not be empty |

### Per-Field Scope

Each field can declare its own scope level. When a field's scope
exceeds the contract's base scope, the effective scope of the entire
exchange escalates to the highest field scope (following
`patterns/scope` escalation rules). See the example below —
`customer_id` at scope `confidential` escalates the exchange even
though the contract base is `internal`.

### Example: Agent-to-Agent Contract

```yaml
contracts:
  scope: internal
  parties: [agent]

  inputs:
    scan_request:
      version: 1.2.0
      description: Files to scan for SEO issues
      scope: internal
      permissions: [read, transform]
      terms: { ttl: 3600, retention: 24, forwarding: denied }
      schema:
        target_files:
          type: "[]string"
          required: true
          scope: public
          description: File paths or URLs to scan
          constraints: "min_items:1"
        scan_depth:
          type: enum(shallow,full)
          required: false
          scope: public
        max_issues:
          type: int
          required: false
          scope: public
          constraints: "min:1, max:1000"
        customer_id:
          type: uuid
          required: false
          scope: confidential
          description: Customer for personalized scanning rules

  outputs:
    scan_result:
      version: 1.2.0
      description: SEO scan findings
      scope: internal
      permissions: [read, store, forward]
      terms: { ttl: 86400, retention: 168, forwarding: restricted }
      schema:
        files_scanned:
          type: int
          required: true
          scope: public
        findings:
          type: "[]json"
          required: true
          scope: internal
        score:
          type: float
          required: true
          scope: public
          constraints: "min:0, max:100"
```

---

### Permissions

Permissions define what the consumer is allowed to do with data
received through a contract. Permissions are declared per contract
and enforced by the receiving party:

| Permission | Description |
|------------|-------------|
| `read` | Consumer can read the data. Always implied. |
| `transform` | Consumer can modify/derive from the data (e.g., summarize, aggregate). |
| `store` | Consumer can persist the data beyond the current operation. |
| `forward` | Consumer can send the data to a third party (another agent, hub, or client). |
| `derive` | Consumer can produce new data derived from this data (e.g., analytics, ML training). |
| `expire` | Consumer MUST delete the data after the TTL specified in terms. |

### Permission Rules

1. `read` is always granted — if a contract exists, the receiver
   can read the payload. Omitting `read` from the list does not
   revoke it.
2. Permissions are **additive**. Only listed permissions are granted.
   Unlisted permissions are denied.
3. `forward` requires explicit grant. Data received without
   `forward` permission MUST NOT be sent to any third party.
4. `expire` is a consumer OBLIGATION, not a permission. When present,
   the consumer MUST delete the data after `terms.ttl` seconds.
5. `derive` permits the consumer to use the data as input for
   producing new data (reports, models, aggregations). The derived
   data inherits the scope of the source data.
6. When scope >= `restricted`, `forward` is denied by default even
   if listed. It requires explicit policy override to enable
   forwarding of restricted data.

### Permission Propagation

When data flows through a chain of contracts (A → B → C), permissions
narrow at each hop. B cannot grant C more permissions than A granted
B:

```
A grants B: [read, transform, store, forward]
B grants C: [read, transform]  ← valid (subset)
B grants C: [read, derive]     ← INVALID (derive not in A→B)
```

---

### Terms

Collaboration terms define operational constraints on the exchange:

```yaml
terms:
  ttl: 3600             # Payload expires after 3600 seconds
  retention: 24         # Consumer may retain data for 24 hours
  rate_limit: 100       # Max 100 exchanges per minute
  forwarding: denied    # Consumer must not forward to third parties
  scope_minimum: internal  # Exchange requires at least internal scope
```

### Terms Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ttl` | int | 0 (no expiry) | Seconds until payload expires. 0 = no expiry. |
| `retention` | int | 0 (no retention) | Hours the consumer may retain data. 0 = process and discard. |
| `rate_limit` | int | 0 (unlimited) | Max exchanges per minute under this contract. 0 = unlimited. |
| `forwarding` | enum | `denied` | `allowed` — unrestricted forwarding. `restricted` — forwarding only to parties that meet scope_minimum. `denied` — no forwarding. |
| `scope_minimum` | enum | `public` | Minimum scope level required for this exchange. Parties below this scope level cannot participate. |

### Terms Enforcement

- `ttl`: Receiver MUST discard payload after TTL. Stored copies
  also expire at TTL.
- `retention`: Governs stored copy persistence. Must be >= TTL.
- `rate_limit`: Enforced at sender. Exceeding → CONTRACT_RATE_EXCEEDED.
- `forwarding`: Enforced at receiver. Forwarding when `denied` is
  a contract violation.
- `scope_minimum`: Checked at validation. Below minimum →
  CONTRACT_SCOPE_INSUFFICIENT.

---

## Policy Binding

Contracts can reference policies from `patterns/policy` that govern
the exchange, inheriting complex rule sets without duplication.
Bind policies by name in the contract declaration:

```yaml
policies:
  - data-retention-policy
  - pii-handling-policy
  - audit-required-policy
```

### Policy Binding Rules

1. Named policies MUST exist in the policy registry. Unknown
   references cause CONTRACT_POLICY_UNKNOWN at validation time.
2. All bound policies are evaluated during contract validation.
   Any `deny` decision rejects the exchange.
3. Policies apply to ALL fields in the contract's schema.
   Per-field policies are not supported — use per-field scope.
4. During federation, the receiving hub evaluates its own policies
   in addition to contract-declared policies. Most restrictive wins.

---

### Message Envelope

All contract-governed data exchange uses a standard envelope that
references the contract and carries scope metadata:

```json
{
  "contract": "<contract-name>",
  "version": "<semver>",
  "scope": "<scope-level>",
  "payload": { ... }
}
```

### Envelope Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `contract` | string | yes | Contract name from declaration |
| `version` | string | yes | Schema version of this payload |
| `scope` | string | yes | Effective scope of this exchange |
| `payload` | object | yes | The actual data conforming to the schema |

### Scope in Envelope

The `scope` field is the EFFECTIVE scope — the highest scope of any
populated field:

```
effective_scope = max(contract.scope, max(field.scope for each populated field))
```

The receiver validates that declared scope matches expected effective
scope. A mismatch is a contract violation.

### Envelope Validation

When a party receives a message with a contract envelope:

```
1. Look up contract by name in party's declared inputs
2. If contract unknown → reject with CONTRACT_UNKNOWN
3. Check version compatibility (see Versioning)
4. Validate scope:
   a. Check effective scope meets contract's scope_minimum
   b. Check receiver is authorized for the declared scope
   c. Check per-field scope levels are consistent
5. Evaluate bound policies (if any):
   a. Load referenced policies from policy registry
   b. Evaluate each policy with exchange context
   c. If any policy returns deny → reject with CONTRACT_POLICY_DENIED
6. Validate payload against schema:
   a. Check all required fields are present
   b. Check field types match declarations
   c. Check constraints are satisfied
7. Verify permissions are compatible:
   a. Check sender's granted permissions cover receiver's needs
8. If validation fails → reject with CONTRACT_VIOLATION
9. Emit contract.validated event
10. Pass validated payload to handler
```

---

## Versioning

Contracts follow semantic versioning with compatibility rules:

### Version Rules

| Change | Version Bump | Compatibility |
|--------|-------------|---------------|
| Add optional field | MINOR | Backward compatible |
| Add new constraint to optional field | MINOR | Backward compatible |
| Relax a constraint | MINOR | Backward compatible |
| Add new permission to grant | MINOR | Backward compatible |
| Extend TTL or retention | MINOR | Backward compatible |
| Remove optional field | MAJOR | Breaking |
| Add required field | MAJOR | Breaking |
| Change field type | MAJOR | Breaking |
| Tighten a constraint | MAJOR | Breaking |
| Rename a field | MAJOR | Breaking |
| Remove a permission | MAJOR | Breaking |
| Reduce TTL or retention | MAJOR | Breaking |
| Escalate scope level | MAJOR | Breaking |
| Change forwarding from allowed to denied | MAJOR | Breaking |

### Compatibility Check

A consumer at version X can accept a producer at version Y if:

```
Major(X) == Major(Y) AND Minor(Y) >= Minor(X)
```

The consumer declares the minimum version it supports. The producer
advertises its current version. If the major versions don't match,
the exchange is rejected.

### Version Negotiation

During exchange, the initiating party checks contract compatibility:

```
1. Producer declares output contract version
2. Consumer declares expected input contract version
3. If compatible → proceed
4. If incompatible → fail with CONTRACT_VERSION_MISMATCH
```

---

## Contract Negotiation

For dynamic exchanges where contracts are not pre-declared in
blueprints, parties negotiate terms at runtime:

### Negotiation Flow

```
A (initiator)                              B (responder)
─────────────                              ─────────────
1. Propose {name, version, scope,
   schema, permissions, terms}     ──────►
                                           2. Evaluate: schema, scope,
                                              permissions, terms
                                   ◄────── 3a. Accept → emit contract.negotiated
                                   ◄────── 3b. Counter (narrower terms only)
4. Evaluate counter-proposal       ──────► 5. Repeat until agreement or rejection
```

### Negotiation Rules

1. Scope can only be ESCALATED during negotiation, never relaxed.
   If A proposes `internal`, B can counter with `confidential`
   but not `public`.
2. Permissions can only be NARROWED. B can remove permissions
   from A's proposal but not add new ones.
3. TTL and retention can only be SHORTENED. Terms become more
   restrictive, never less.
4. Forwarding can only become MORE restrictive:
   `allowed` → `restricted` → `denied`.
5. Maximum 5 negotiation rounds. If no agreement after 5 rounds,
   the negotiation fails with CONTRACT_NEGOTIATION_FAILED.
6. All negotiation messages are signed and auditable.

---

## Contract Lifecycle

Contracts evolve over time. The lifecycle defines how contracts are
published, deprecated, and retired:

### Lifecycle States

| State | Description |
|-------|-------------|
| `draft` | Contract defined but not published. Not available for exchange. |
| `active` | Published and available for exchange. |
| `deprecated` | Still functional but consumers should migrate. Emits contract.deprecated event. |
| `retired` | No longer functional. Exchanges rejected with CONTRACT_RETIRED. |

### Deprecation and Migration

```
1. Publisher marks version deprecated, declares migration path
2. contract.deprecated event emitted, grace period begins (default: 30 days)
3. During grace period: contract validates but responses include Deprecation header
4. After grace period: transitions to retired, all exchanges rejected
```

Deprecated contracts MUST declare a migration path:

```yaml
lifecycle:
  scan_request:
    version: 1.0.0
    status: deprecated
    deprecated_at: 1750000000
    migration:
      target_contract: scan_request
      target_version: 2.0.0
      guide: |
        - target_files renamed to targets
        - scan_depth removed, use scan_options.depth
        - max_issues moved to scan_options.limits.issues
```

---

## Contract Testing

Contracts are testable at deploy time without running the components:

### Static Validation

```
For each component in the deployment:
  For each workflow that references this component:
    For each phase that dispatches to this component:
      1. Resolve the phase's input references (structurally)
      2. Match resolved structure against component's input contract
      3. Match component's output contract against downstream consumers
      4. Verify scope compatibility across the chain
      5. Verify permission propagation is valid (no escalation)
      6. Verify terms are satisfiable (TTL chain, retention chain)
      7. Verify bound policies exist in the policy registry
      8. Report mismatches as deployment errors
```

### Contract Compatibility Matrix

For a deployment with components A and B where A produces output
consumed by B:

| Check | Validates |
|-------|-----------|
| A.outputs.X exists | Producer declares the contract |
| B.inputs.Y exists | Consumer declares the contract |
| A.outputs.X.version compatible with B.inputs.Y.version | Versions align |
| A.outputs.X.schema covers B.inputs.Y.schema required fields | Required fields present |
| Field types match | Type safety |
| A.outputs.X.scope <= B's authorized scope | Scope authorization |
| A.outputs.X.permissions cover B's declared needs | Permission sufficiency |
| A.outputs.X.terms satisfiable by B | Terms compatibility |
| Bound policies resolvable | Policy references valid |

---

## Runtime Discovery

Contracts are discoverable via the `/v1/describe` endpoint. The
manifest `contracts` field includes full metadata — scope, parties,
inputs, outputs, each with version, permissions, terms, and schema.
This extends the existing `AgentManifest`. The `inputs`/`outputs`
IOSpec fields remain for human-readable descriptions; `contracts`
adds machine-checkable schemas, permissions, and terms.

```json
{
  "name": "seo-analyzer",
  "contracts": {
    "scope": "internal",
    "parties": ["agent"],
    "inputs": {
      "scan_request": { "version": "1.2.0", "scope": "internal", "permissions": ["read", "transform"], "terms": { "ttl": 3600, "forwarding": "denied" }, "schema": {} }
    },
    "outputs": {
      "scan_result": { "version": "1.2.0", "scope": "internal", "permissions": ["read", "store", "forward"], "terms": { "ttl": 86400, "forwarding": "restricted" }, "schema": {} }
    }
  }
}
```

---

## Scope Propagation

When data moves through a chain of contracts, scope is tracked and
enforced at every hop:

### Propagation Rules

1. **Never downgrade** — Data at scope X cannot be reclassified
   lower at any downstream hop.
2. **Escalation to maximum** — Effective scope of a composite
   message is the highest scope of any populated field.
3. **Scope in derived data** — Transformed data inherits the scope
   of the highest-scope input field that contributed to it.
4. **Cross-boundary enforcement** — At federation boundaries, the
   receiving hub verifies its trust tier permits the declared scope.
   Partner-tier may permit up to `confidential`. Public-tier is
   limited to `public` and `internal`.

### Example: Scope Chain

```
A (public) → produces report with customer_context (confidential)
  → effective scope escalates to confidential → envelope.scope = "confidential"
B receives (authorized for confidential) → transforms → summary inherits confidential
  → forwards to C → B must have forward permission from A's contract
  → if B lacks forward → CONTRACT_VIOLATION
```

---

## Federation Compatibility

This pattern is compatible with `protocol/federation` data boundary
contracts. Federation contracts are a specialized case of the
general contract pattern, with additional fields for cross-boundary
exchange:

| General Contract | Federation Extension |
|-----------------|---------------------|
| `scope` | Maps to federation trust tier requirements |
| `permissions` | Maps to federation `inbound`/`outbound` rules |
| `terms.forwarding` | Maps to federation boundary enforcement |
| `terms.retention` | Maps to federation `data_retention` |
| `schema.field.scope` | Maps to federation `forbidden` patterns |
| `policies` | Maps to federation jurisdiction requirements |

Federation contracts ADD:
- `jurisdiction_requirements` — geographic data residency
- `forbidden` field patterns — PII/credential stripping
- `transformations` — mutations before crossing boundary
- Dual orchestrator signatures

An agent that declares contracts compatible with this pattern
automatically satisfies the data contract requirements for
federation. The federation layer adds its cross-boundary
enforcement on top.

---

## Standard Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| CONTRACT_UNKNOWN | 400 | Referenced contract not declared by party |
| CONTRACT_VIOLATION | 422 | Payload fails schema or permission validation |
| CONTRACT_VERSION_MISMATCH | 409 | Incompatible contract versions |
| CONTRACT_SCOPE_INSUFFICIENT | 403 | Exchange scope below contract minimum |
| CONTRACT_PERMISSION_DENIED | 403 | Consumer lacks required permission |
| CONTRACT_POLICY_DENIED | 403 | Bound policy returned deny decision |
| CONTRACT_POLICY_UNKNOWN | 400 | Referenced policy not found in registry |
| CONTRACT_RATE_EXCEEDED | 429 | Rate limit from contract terms exceeded |
| CONTRACT_EXPIRED | 410 | Contract payload TTL has expired |
| CONTRACT_RETIRED | 410 | Contract version has been retired |
| CONTRACT_NEGOTIATION_FAILED | 409 | Parties failed to agree on terms |

Error responses MUST use the standard `ErrorResponse` format with
`detail` containing specific validation failures:

```json
{
  "error": "Contract violation: scan_request v1.2.0",
  "code": "CONTRACT_VIOLATION",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "contract": "scan_request",
    "version": "1.2.0",
    "party": "seo-analyzer",
    "violations": [
      {"field": "target_files", "rule": "required", "message": "field is required"},
      {"field": "max_issues", "rule": "min:1", "message": "value 0 is below minimum 1"},
      {"field": "customer_id", "rule": "scope", "message": "field scope confidential exceeds party authorization"}
    ]
  }
}
```

---

## Violation Tracking

When a contract violation occurs, a `ContractViolation` record is
created and `contract.violated` is emitted:

```json
{
  "contract": "scan_request",
  "version": "1.2.0",
  "party": "rogue-agent",
  "rule_violated": "forwarding:denied",
  "severity": "critical",
  "payload_hash": "sha256:abc123...",
  "timestamp": 1750000000
}
```

| Severity | Description | Action |
|----------|-------------|--------|
| `info` | Minor non-compliance, no data exposure | Log only |
| `warning` | Policy violation, potential exposure | Log + alert |
| `critical` | Scope/forwarding/permission breach | Log + alert + block |

Critical violations trigger automatic contract suspension — the
violating party is blocked until reviewed.

---

## Implementation Notes

- Validation happens at the receiver, not the sender. MUST execute
  before any processing logic.
- Legacy mode (no contracts): envelope validation skipped, raw
  payloads accepted. NOT permitted for scope >= confidential.
- The `contracts` manifest field is optional for public/internal
  scope, required for confidential/restricted/critical.
- Schemas use the `patterns/storage` type system, intentionally
  simpler than JSON Schema.
- Permission enforcement is the receiver's responsibility.
- Policy bindings are resolved at validation time. Modified policies
  apply to subsequent validations.
- At hub boundaries, the federation layer automatically extends
  contracts with jurisdiction, forbidden patterns, and
  transformations.

---

## Verification Checklist

- [ ] Component declares input/output contracts with version, scope, description, schema
- [ ] Schema fields have type, required flag, scope, description; constraints validate correctly
- [ ] Per-field scope declared for fields above contract base scope
- [ ] Permissions declared per contract; terms declared with TTL, retention, forwarding
- [ ] Policy bindings reference existing policies in registry
- [ ] Envelope includes contract, version, scope, payload; effective scope computed correctly
- [ ] Error codes enforced: CONTRACT_UNKNOWN, CONTRACT_VIOLATION, CONTRACT_SCOPE_INSUFFICIENT, CONTRACT_PERMISSION_DENIED, CONTRACT_POLICY_DENIED, CONTRACT_VERSION_MISMATCH, CONTRACT_RATE_EXCEEDED, CONTRACT_EXPIRED
- [ ] Error responses include specific validation failure details
- [ ] Contracts discoverable via describe endpoint
- [ ] Static contract testing validates deployment compatibility
- [ ] Permission propagation narrows across contract chains
- [ ] Scope propagation never downgrades across contract chains
- [ ] Legacy agents without contracts function (scope < confidential)
- [ ] Negotiation follows monotonic restriction rules
- [ ] Deprecated contracts include migration paths; retired contracts reject all exchanges
- [ ] Violation tracking emits contract.violated; critical violations suspend contract
- [ ] Federation contracts extend general contracts with boundary metadata
