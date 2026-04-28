<!-- blueprint
type: protocol
name: federation
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/hub]
platform: any
tier: free
-->

# Weblisk Federation Protocol

Specification for multi-orchestrator collaboration, cross-tenant agent
invocation, and secure data exchange across organizational boundaries.
This protocol extends the single-orchestrator model into a federated
mesh where multiple orchestrators discover, trust, and delegate work
to each other while enforcing strict data sovereignty boundaries.

## Overview

Federation enables businesses to expose specific agent capabilities to
partners, customers, and the wider hub network — without exposing
internal systems, data, or infrastructure. Every cross-boundary
interaction is governed by data contracts, trust tiers, and behavioral
verification that go far beyond transport encryption.

The federation protocol treats data protection as a **structural
constraint**, not a policy afterthought. Data cannot leak because the
architecture makes it physically impossible for unpermitted fields to
cross a boundary.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
          request_type: RegisterRequest
          response_fields: [agent_id, token, services]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519KeyPair
          fields_used: [public_key, private_key]
        - name: WLToken
          fields_used: [header, payload, signature]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskRequest
          fields_used: [id, action, payload, context, token]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary]
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, detail, status]
        - name: AgentManifest
          fields_used: [name, type, version, public_key, capabilities]
        - name: ErrorResponse
          fields_used: [error, code, category, retryable]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/hub
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: HubManifest
          fields_used: [name, public_key, federation_url]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Conventions

- All federation endpoints are prefixed with `/v1/federation`
- All cross-boundary messages are signed by both sending and receiving orchestrator
- Trust relationships are explicit, non-transitive, and time-limited
- Data contracts are fail-closed — unknown fields are rejected, not ignored
- All timestamps are Unix epoch seconds (`int64`)
- All public keys are hex-encoded Ed25519 public keys (64 hex chars)
- Federation topic qualification uses `::` separator (e.g., `acme-corp::workflow.completed`)
- Hub-qualified topics do NOT match unqualified subscription patterns

---

## Design Principles

1. **Zero trust by default** — No orchestrator trusts another until an
   explicit trust relationship is established and cryptographically
   verified. Trust is never implied by network proximity.
2. **Data minimization by construction** — Data contracts declare the
   minimum viable data set for each collaboration. Fields not in the
   contract are stripped before crossing the boundary. This is enforced
   at the protocol level, not the application level.
3. **Behavioral integrity** — Agents are fingerprinted at registration.
   Changes to an agent's manifest, capabilities, or behavioral patterns
   are detected and flagged before they can affect cross-boundary
   interactions.
4. **Sovereignty-aware routing** — Data residency requirements are
   first-class. Tasks involving regulated data are only routed to
   agents and orchestrators operating within the permitted jurisdiction.
5. **Non-repudiation** — Every cross-boundary message is signed by
   both the sending and receiving orchestrator. The full chain of
   custody is auditable.

---

## Orchestrator Identity

Every orchestrator MUST have a cryptographic identity (Ed25519 key pair)
following the same rules as agent identity (see [identity.md](identity.md)).

### Orchestrator Manifest

```json
{
  "name": "acme-corp",
  "type": "orchestrator",
  "version": "1.0.0",
  "description": "ACME Corporation agent environment",
  "federation_url": "https://agents.acme.com/v1/federation",
  "public_key": "<hex Ed25519 public key>",
  "jurisdiction": "US",
  "published_capabilities": [
    {
      "domain": "seo",
      "actions": ["audit"],
      "data_contract": "seo-audit-v1",
      "tier": "partner"
    }
  ],
  "trust_policy": "explicit",
  "max_concurrent_federated": 20,
  "signature": "<hex Ed25519 signature>"
}
```

### Orchestrator Manifest Fields

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Unique orchestrator identifier |
| Type | string | `type` | yes | MUST be `"orchestrator"` |
| Version | string | `version` | yes | Semver version |
| Description | string | `description` | yes | Human-readable purpose |
| FederationURL | string | `federation_url` | yes | HTTPS endpoint for federation protocol |
| PublicKey | string | `public_key` | yes | Hex-encoded Ed25519 public key |
| Jurisdiction | string | `jurisdiction` | yes | ISO 3166-1 alpha-2 country code (primary data jurisdiction) |
| PublishedCapabilities | []PubCap | `published_capabilities` | no | Capabilities exposed to federation |
| TrustPolicy | string | `trust_policy` | yes | `"explicit"` (manual approval) or `"registry"` (trust via hub registry) |
| MaxConcurrentFederated | int | `max_concurrent_federated` | no | Max concurrent cross-boundary tasks (default: 20) |
| Signature | string | `signature` | yes | Self-signed manifest |

---

## Trust Establishment

### Trust Tiers

| Tier | Trust Level | Discovery | Auth Model | Data Boundary |
|------|-------------|-----------|------------|---------------|
| **Private** | Full | Pre-configured | Shared signing authority | Minimal filtering (same org) |
| **Partner** | Scoped | Explicit peering | Mutual key exchange | Full data contract enforcement |
| **Public** | Minimal | Hub registry | Per-invocation auth | Strict data contracts + metering |

### Peering Flow (Partner Tier)

Two orchestrators establish a trust relationship through a mutual
exchange:

```
Orchestrator A                        Orchestrator B
───────────────                       ───────────────
1. Admin initiates peering
   with B's federation_url
                              
2. POST /v1/federation/peer ──────►
   {
     manifest: A's orchestrator manifest,
     requested_capabilities: ["seo:audit"],
     data_contracts: ["seo-audit-v1"],
     signature: signed(manifest)
   }
                              
                              ◄────── 3. B validates:
                                         a. Verify A's signature
                                         b. Check A's jurisdiction
                                         c. Review requested capabilities
                                         d. Admin approves or rejects
                              
                              ◄────── 4. POST /v1/federation/peer-accept
                                      {
                                        manifest: B's orchestrator manifest,
                                        granted_capabilities: ["seo:audit"],
                                        data_contracts: ["seo-audit-v1"],
                                        trust_tier: "partner",
                                        expires_at: <Unix epoch>,
                                        signature: signed(grant)
                                      }

5. A validates B's signature
6. A stores B's public key +
   granted capabilities
7. Federation link established
```

Trust relationships:
- MUST have an explicit expiry (default: 90 days)
- MUST be renewable without disruption
- CAN be revoked immediately by either party
- Are NOT transitive (A trusts B, B trusts C → A does NOT trust C)

### Key Rotation

When an orchestrator rotates its Ed25519 key pair:

```
1. Generate new key pair
2. Sign a KeyRotation message with the OLD key:
   {old_public_key, new_public_key, effective_at, signature_old}
3. Counter-sign with the NEW key:
   {old_public_key, new_public_key, effective_at, signature_old, signature_new}
4. Distribute to all peers via POST /v1/federation/key-rotate
5. Peers verify BOTH signatures
6. Peers update stored public key after effective_at
7. Grace period: accept both keys for 24 hours after rotation
```

---

## Data Boundary Contracts

The most critical component of federation. A data contract defines
exactly what data MAY cross a trust boundary and in what form.

### Contract Structure

```json
{
  "name": "seo-audit-v1",
  "version": "1.0.0",
  "description": "Contract for cross-boundary SEO audit requests",
  "direction": "bidirectional",
  
  "inbound": {
    "required": [
      {"name": "html_content", "type": "text", "constraints": "max_length:1048576"},
    ],
    "permitted": [
      {"name": "url", "type": "string"},
      {"name": "language", "type": "string"}
    ],
    "forbidden": [
      {"pattern": "*.customer_id"},
      {"pattern": "*.email"},
      {"pattern": "*.pii.*"},
      {"pattern": "*.internal_*"},
      {"pattern": "*.credentials.*"},
      {"pattern": "*.api_key*"}
    ],
    "transformations": [
      {"type": "strip", "target": "url", "config": {"strip": "query_params", "reason": "Query params may contain tracking data"}}
    ]
  },

  "outbound": {
    "required": [
      {"name": "seo_score", "type": "number"},
      {"name": "findings", "type": "list"}
    ],
    "permitted": [
      {"name": "findings[*].severity", "type": "string"},
      {"name": "findings[*].element", "type": "string"},
      {"name": "findings[*].message", "type": "string"},
      {"name": "recommendations[*].priority", "type": "string"},
      {"name": "recommendations[*].proposed", "type": "string"}
    ],
    "forbidden": [
      {"pattern": "*.raw_content"},
      {"pattern": "*.internal_notes"},
      {"pattern": "*.agent_logs"},
      {"pattern": "*.debug_*"}
    ]
  },

  "data_retention": {
    "max_hours": 24,
    "delete_on_revoke": true,
    "audit_trail": true
  },

  "jurisdiction_requirements": {
    "country_codes": ["US", "CA", "GB"],
    "storage_constraint": "must_reside",
    "gdpr_applicable": true
  },

  "signature": "<signed by contract author>"
}
```

### Contract Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Contract identifier (lowercase, hyphens) |
| version | string | yes | Semver version |
| direction | string | yes | `"inbound"`, `"outbound"`, or `"bidirectional"` |
| inbound | BoundarySpec | yes | Rules for data entering your boundary |
| outbound | BoundarySpec | yes | Rules for data leaving your boundary |
| data_retention | RetentionPolicy | yes | How long cross-boundary data may persist |
| jurisdiction_requirements | JurisdictionSpec | no | Data residency rules |
| signature | string | yes | Author's signature over the contract |

### BoundarySpec

| Field | Type | Description |
|-------|------|-------------|
| required | []FieldSpec | Fields that MUST be present |
| permitted | []FieldSpec | Fields that MAY be present |
| forbidden | []PatternSpec | Patterns that MUST be stripped |
| transformations | []Transform | Mutations applied before crossing |

### Enforcement

Data contract enforcement is NOT optional. The domain controller (which
already controls all data flow) applies contracts at the boundary:

```
Before sending data to a federated agent:
  1. Serialize the outbound payload
  2. Apply forbidden patterns — recursively walk the JSON and remove
     any field matching a forbidden pattern
  3. Apply transformations (strip, hash, redact, truncate, rename)
  4. Validate required fields are present
  5. Validate remaining fields are in the permitted set
  6. If any forbidden field was present, log a DATA_BOUNDARY_VIOLATION
     audit entry (the data was stripped, not sent — this is a warning
     that the upstream workflow is producing data it shouldn't)
  7. Sign the sanitized payload
  8. Send

Before accepting data from a federated agent:
  1. Verify the sender's signature
  2. Apply forbidden patterns — strip inbound forbidden fields
  3. Validate required fields are present
  4. Validate all fields are in required or permitted set
  5. Reject unknown fields entirely (fail-closed, not fail-open)
  6. Log audit entry with field counts (received, stripped, accepted)
```

**Critical rule:** Enforcement is fail-closed. If a field is not
explicitly `required` or `permitted`, it is rejected. This prevents
any data leakage through new fields added by an updated agent.

---

## Behavioral Integrity

Trust is not just about identity — it's about behavior. An agent's
manifest is a promise about what it will do. If an agent's behavior
changes, that promise may be broken.

### Agent Behavioral Fingerprint

When an agent registers, the orchestrator computes a behavioral
fingerprint from its manifest:

```json
{
  "agent_name": "seo-analyzer",
  "fingerprint_version": 1,
  "manifest_hash": "<SHA-256 of canonical JSON manifest>",
  "capability_set": ["file:read", "llm:chat", "agent:message"],
  "input_schema_hash": "<SHA-256 of inputs JSON>",
  "output_schema_hash": "<SHA-256 of outputs JSON>",
  "version": "1.0.0",
  "computed_at": 1712160000
}
```

### Change Detection

On every re-registration or manifest update:

```
1. Compute new fingerprint
2. Compare against stored fingerprint
3. Classify changes:

   BENIGN (auto-accept):
     - version patch bump (1.0.0 → 1.0.1)
     - description text change
     - no capability/schema changes

   NOTABLE (log + notify):
     - version minor bump (1.0.0 → 1.1.0)
     - new capabilities ADDED (expansion)
     - new input/output fields ADDED

   BREAKING (require review):
     - version major bump (1.0.0 → 2.0.0)
     - capabilities REMOVED
     - input/output fields REMOVED or type-changed
     - public key changed (identity rotation)

   CRITICAL (block until admin review):
     - capability scope WIDENED (e.g., file:read["*.html"] → file:read["*"])
     - forbidden field patterns no longer match
     - jurisdiction changed
     - any change to an agent involved in active federation

4. For BREAKING or CRITICAL changes on federated agents:
   a. Immediately SUSPEND the agent from federated workflows
   b. Notify all peer orchestrators that trust this agent
   c. Log BEHAVIORAL_CHANGE audit entry with full diff
   d. Require admin re-approval before resuming federation
```

### Behavioral Monitoring (Runtime)

Beyond manifest changes, the system SHOULD monitor runtime behavior:

| Signal | What It Detects | Action |
|--------|----------------|--------|
| Output field expansion | Agent returning fields not in its manifest outputs | Log warning, strip unknown fields |
| Data volume anomaly | Agent returning 10x normal data volume | Rate-limit, alert admin |
| Error rate spike | Agent failing > 50% of requests (was < 5%) | Mark degraded, suspend from federation |
| Latency anomaly | Agent response time 5x baseline | Log, consider timeout reduction |
| Capability creep | Agent requesting capabilities not in manifest | Reject, log CAPABILITY_VIOLATION |

---

## Cross-Boundary Task Execution

When an orchestrator delegates a task to a peer's agent through
federation:

```
Orchestrator A (requester)            Orchestrator B (provider)
──────────────────────                ──────────────────────

1. Domain controller selects
   federated agent for a phase

2. Build FederatedTaskRequest:
   - task payload (data-contract-filtered)
   - contract_name: "seo-audit-v1"
   - requester: A's identity
   - trace_id: propagated from workflow
   - signed by A's key

3. POST /v1/federation/task ──────►

                                      4. Verify A's signature
                                      5. Verify A is a trusted peer
                                      6. Verify contract_name matches
                                         a granted capability
                                      7. Apply INBOUND data contract:
                                         strip forbidden, validate required
                                      8. Route to internal domain/agent
                                      9. Execute task
                                      10. Apply OUTBOUND data contract:
                                          strip forbidden, validate required
                                      11. Sign result with B's key

                              ◄────── 12. Return FederatedTaskResult

13. Verify B's signature
14. Apply INBOUND data contract
    (on the result)
15. Return sanitized result to
    domain workflow
16. Log federation audit entry
    on both sides
```

### FederatedTaskRequest

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| TaskID | string | `task_id` | yes | Unique task identifier |
| ContractName | string | `contract_name` | yes | Data contract governing this exchange |
| RequesterOrch | string | `requester_orch` | yes | Requesting orchestrator name |
| Payload | map | `payload` | yes | Task data (pre-filtered by data contract) |
| TraceID | string | `trace_id` | no | Correlation ID |
| Signature | string | `signature` | yes | Requester's Ed25519 signature |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

### FederatedTaskResult

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| TaskID | string | `task_id` | yes | Matching request task ID |
| ProviderOrch | string | `provider_orch` | yes | Providing orchestrator name |
| Status | string | `status` | yes | `success`, `failed`, `rejected` |
| Result | map | `result` | no | Task output (filtered by outbound contract) |
| Error | ErrorResponse | `error` | no | Error details if failed/rejected |
| Signature | string | `signature` | yes | Provider's Ed25519 signature |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

---

## Federation Endpoints

Added to the orchestrator when federation is enabled:

| Path | Method | Auth | Request | Response | Purpose |
|------|--------|------|---------|----------|---------|
| `/v1/federation/manifest` | GET | no | — | `OrchestratorManifest` | Return orchestrator manifest |
| `/v1/federation/peer` | POST | signature | `PeerRequest` | `PeerResponse` | Initiate peering request |
| `/v1/federation/peer-accept` | POST | signature | `PeerAcceptance` | `PeerResponse` | Accept peering request |
| `/v1/federation/peer-revoke` | POST | signature | `{peer_name, reason, signature}` | 200 OK | Revoke trust relationship |
| `/v1/federation/key-rotate` | POST | dual-signature | `KeyRotationRequest` | 200 OK | Notify peers of key rotation |
| `/v1/federation/task` | POST | peer-auth | `FederatedTaskRequest` | `FederatedTaskResult` | Execute a federated task |
| `/v1/federation/status` | GET | peer-auth | — | `FederationStatus` | Federation health and peer status |
| `/v1/federation/contracts` | GET | peer-auth | — | `list<DataContract>` | List available data contracts |
| `/v1/federation/audit` | GET | peer-auth | — | `list<AuditEntry>` | Cross-boundary audit trail |

---

## Types

```yaml
types:
  OrchestratorManifest:
    description: Identity and capability declaration for a federated orchestrator
    fields:
      name:
        type: string
        description: Unique orchestrator identifier
      type:
        type: string
        description: Must be "orchestrator"
        constraints:
          enum: [orchestrator]
      version:
        type: string
        format: semver
        description: Semver version
      description:
        type: string
        description: Human-readable purpose
      federation_url:
        type: string
        format: url
        description: HTTPS endpoint for federation protocol
      public_key:
        type: string
        format: hex
        description: Hex-encoded Ed25519 public key
      jurisdiction:
        type: string
        description: ISO 3166-1 alpha-2 country code
      published_capabilities:
        type: "list<PublishedCapability>"
        description: Capabilities exposed to federation
        required: false
      trust_policy:
        type: string
        description: Trust establishment model
        constraints:
          enum: [explicit, registry]
      max_concurrent_federated:
        type: int
        description: Max concurrent cross-boundary tasks
        constraints:
          default: 20
      signature:
        type: string
        format: hex
        description: Self-signed manifest

  PublishedCapability:
    description: A capability exposed to federation peers
    fields:
      domain:
        type: string
        description: Domain name providing the capability
      actions:
        type: "list<string>"
        description: Available actions
      data_contract:
        type: string
        description: Data contract governing this capability
      tier:
        type: string
        description: Trust tier required
        constraints:
          enum: [private, partner, public]

  DataContract:
    description: Defines exactly what data may cross a trust boundary
    fields:
      name:
        type: string
        description: Contract identifier
      version:
        type: string
        format: semver
      direction:
        type: string
        constraints:
          enum: [inbound, outbound, bidirectional]
      inbound:
        type: BoundarySpec
        description: Rules for data entering the boundary
      outbound:
        type: BoundarySpec
        description: Rules for data leaving the boundary
      data_retention:
        type: RetentionPolicy
      jurisdiction_requirements:
        type: JurisdictionSpec
        required: false
      signature:
        type: string
        format: hex

  BoundarySpec:
    description: Field rules for one direction of a data boundary
    fields:
      required:
        type: "list<FieldSpec>"
        description: Fields that MUST be present
      permitted:
        type: "list<FieldSpec>"
        description: Fields that MAY be present
      forbidden:
        type: "list<PatternSpec>"
        description: Patterns that MUST be stripped
      transformations:
        type: "list<Transform>"
        description: Mutations applied before crossing
        required: false

  FederatedTaskRequest:
    description: Cross-boundary task execution request
    fields:
      task_id:
        type: string
        format: hex-id
      contract_name:
        type: string
        description: Governing data contract
      requester_orch:
        type: string
        description: Requesting orchestrator name
      payload:
        type: map
        description: Task data (pre-filtered by data contract)
      trace_id:
        type: string
        required: false
      signature:
        type: string
        format: hex
      timestamp:
        type: int64

  FederatedTaskResult:
    description: Cross-boundary task execution result
    fields:
      task_id:
        type: string
        format: hex-id
      provider_orch:
        type: string
        description: Providing orchestrator name
      status:
        type: string
        constraints:
          enum: [success, failed, rejected]
      result:
        type: map
        required: false
      error:
        type: ErrorResponse
        required: false
      signature:
        type: string
        format: hex
      timestamp:
        type: int64

  BehavioralFingerprint:
    description: Computed behavioral snapshot of an agent
    fields:
      agent_name:
        type: string
      fingerprint_version:
        type: int
      manifest_hash:
        type: string
        description: SHA-256 of canonical JSON manifest
      capability_set:
        type: "list<string>"
      input_schema_hash:
        type: string
      output_schema_hash:
        type: string
      version:
        type: string
        format: semver
      computed_at:
        type: int64

  RetentionPolicy:
    description: How long cross-boundary data may persist
    fields:
      max_hours:
        type: int
        description: Maximum retention duration in hours
        constraints:
          min: 1
      delete_on_revoke:
        type: bool
        description: Whether to purge data when peering is revoked
        constraints:
          default: true
      audit_trail:
        type: bool
        description: Whether deletion must be logged for compliance
        constraints:
          default: true

  JurisdictionSpec:
    description: Data residency and jurisdictional constraints
    fields:
      country_codes:
        type: "list<string>"
        description: ISO 3166-1 alpha-2 codes where data may reside
      storage_constraint:
        type: string
        description: Residency enforcement model
        constraints:
          enum: [must_reside, must_not_reside, prefer]
      gdpr_applicable:
        type: bool
        description: Whether GDPR-style data subject rights apply
        required: false

  FieldSpec:
    description: Specification of a required or permitted field in boundary data
    fields:
      name:
        type: string
        description: Field name or dot-path (e.g. "payload.url")
      type:
        type: string
        description: Expected type (string, int, bool, object, list)
        required: false
      constraints:
        type: string
        description: Optional validation rule (max_length, pattern, etc.)
        required: false

  PatternSpec:
    description: Pattern identifying data that must be stripped at boundaries
    fields:
      pattern:
        type: string
        description: Regex or glob pattern to match against field names or values
      scope:
        type: string
        description: Where to apply the pattern
        constraints:
          enum: [field_name, field_value, both]
          default: field_name

  Transform:
    description: Mutation applied to data before crossing a trust boundary
    fields:
      type:
        type: string
        description: Transform operation
        constraints:
          enum: [strip, hash, redact, truncate, rename]
      target:
        type: string
        description: Field name or pattern to transform
      config:
        type: object
        description: Operation-specific configuration (e.g. hash algorithm, max_length)
        required: false
```

---

## Authentication

```yaml
authentication:
  mechanism: signature
  models:
    peering:
      description: Mutual Ed25519 signature verification during trust establishment
      flow:
        - step: Initiator signs manifest with own private key
        - step: Responder verifies initiator signature with initiator public key
        - step: Responder signs acceptance with own private key
        - step: Initiator verifies responder signature
    task_execution:
      description: Per-request signature on federated task payloads
      flow:
        - step: Requester signs FederatedTaskRequest with own key
        - step: Provider verifies requester signature against stored peer key
        - step: Provider verifies requester is a trusted peer with granted capability
        - step: Provider signs FederatedTaskResult with own key
        - step: Requester verifies provider signature
    key_rotation:
      description: Dual-signature (old + new key) for zero-downtime rotation
      flow:
        - step: Sign rotation request with OLD key
        - step: Counter-sign with NEW key
        - step: Peers verify BOTH signatures
        - step: 24-hour grace period accepting both keys
```

---

## Data Sovereignty

### Jurisdiction Enforcement

Every orchestrator declares its primary jurisdiction. Data contracts
declare jurisdiction requirements. The federation layer enforces both:

```
Before routing a federated task:
  1. Check data contract jurisdiction_requirements.country_codes
  2. Check target orchestrator's declared jurisdiction
  3. If target jurisdiction is not in country_codes → REJECT
  4. If storage_constraint = "must_reside":
     Data MUST NOT be persisted by the receiving orchestrator
     beyond the processing window (max_hours from retention policy)
  5. If storage_constraint = "prefer":
     Prefer in-jurisdiction routing but allow fallback
  6. If storage_constraint = "must_not_reside":
     Data MUST NOT be stored in the listed jurisdictions
  7. If gdpr_applicable = true:
     Enforce data subject rights (erasure, portability) on
     cross-boundary data per the retention policy
```

### Retention Enforcement

Cross-boundary data has an explicit lifecycle:

```
1. Data arrives at receiving orchestrator
2. Clock starts: data_retention.max_hours
3. Task executes, result returned
4. On result delivery OR retention expiry (whichever is first):
   a. Purge all cross-boundary data (delete is the only action)
   b. If audit_trail = true: log deletion event with timestamp and contract name
5. On peering revocation (if delete_on_revoke = true):
   a. Immediately purge all data received under this contract
   b. Log purge event regardless of audit_trail setting
6. Receiving orchestrator MUST NOT retain cross-boundary data in:
   - Observation store
   - Recommendation store
   - Any persistent cache
   - Backup systems (must be excluded from backup scope)
```

### Data Residency Markers

Fields in cross-boundary payloads SHOULD carry residency markers:

```json
{
  "html_content": "...",
  "_meta": {
    "origin_jurisdiction": "US",
    "data_classification": "business_confidential",
    "retention_expires": 1712246400,
    "contract": "seo-audit-v1"
  }
}
```

The `_meta` object is protocol-level metadata — it MUST be preserved
through the processing pipeline and MUST NOT be forwarded to agents.
Only the orchestrator and domain controller read `_meta`.

---

## Security Layers Summary

Federation security is defense-in-depth — seven layers, each
independent, all enforced concurrently:

| Layer | What It Protects | Mechanism |
|-------|-----------------|-----------|
| **1. Transport** | Data in transit | TLS 1.3 required for all federation endpoints |
| **2. Identity** | Authenticity | Ed25519 signatures on every message |
| **3. Trust** | Authorization | Explicit peering with expiry, non-transitive |
| **4. Data contracts** | Data minimization | Fail-closed field filtering at every boundary |
| **5. Behavioral integrity** | Agent reliability | Manifest fingerprinting + change detection |
| **6. Jurisdiction** | Data sovereignty | Routing rules based on declared jurisdiction |
| **7. Retention** | Data lifecycle | Automatic purge with audit trail |

No single layer is sufficient alone. Together, they make data leakage
structurally impossible rather than policy-dependent.

---

## Error Handling

```yaml
error_codes:
  - code: PEER_UNTRUSTED
    status: 403
    description: Requesting orchestrator is not a trusted peer
    retryable: false
  - code: CONTRACT_VIOLATION
    status: 400
    description: Request payload violates data contract
    retryable: false
  - code: JURISDICTION_DENIED
    status: 403
    description: Target jurisdiction not in allowed list
    retryable: false
  - code: TRUST_EXPIRED
    status: 403
    description: Trust relationship has expired
    retryable: false
  - code: CAPABILITY_DENIED
    status: 403
    description: Requested capability not granted to this peer
    retryable: false
  - code: BEHAVIORAL_CHANGE
    status: 409
    description: Agent has pending behavioral change review
    retryable: false
  - code: DATA_BOUNDARY_VIOLATION
    status: 400
    description: Forbidden fields detected in cross-boundary payload
    retryable: false
  - code: RETENTION_EXPIRED
    status: 410
    description: Cross-boundary data has been purged per retention policy
    retryable: false
```

---

## Implementation Notes

- Federation is optional — a single-orchestrator deployment does not need this protocol
- All federation endpoints require HTTPS (TLS 1.3) in production
- Trust relationships default to 90-day expiry to force periodic review
- Data contracts are versioned independently of the protocol
- Behavioral fingerprints should be recomputed on every agent re-registration
- Key rotation uses a 24-hour grace period to handle clock skew and propagation
- The `_meta` object in cross-boundary payloads is protocol-level — never forwarded to agents
- Dead-lettered federated events follow the same DLQ pattern as local events
- Federated namespace qualification (`::`) is applied at the boundary, not by agents
- Contract enforcement is fail-closed by design: unknown fields are rejected, not ignored

---

## Verification Checklist

- [ ] Orchestrator generates and stores Ed25519 identity
- [ ] Orchestrator manifest is self-signed and verifiable
- [ ] Peering flow requires mutual signature verification
- [ ] Trust relationships have explicit expiry (default: 90 days)
- [ ] Trust is non-transitive (A↔B + B↔C ≠ A↔C)
- [ ] Peering can be revoked immediately by either party
- [ ] Key rotation uses dual-signature (old + new key)
- [ ] Data contracts are enforced fail-closed (unknown fields rejected)
- [ ] Forbidden field patterns are recursively applied to all JSON
- [ ] DATA_BOUNDARY_VIOLATION logged when forbidden fields are stripped
- [ ] Behavioral fingerprint computed on every registration
- [ ] BREAKING/CRITICAL changes suspend agent from federation
- [ ] Peer orchestrators notified of behavioral changes
- [ ] Federated task payloads are signed by both orchestrators
- [ ] Jurisdiction checked before routing federated tasks
- [ ] Cross-boundary data purged within retention window
- [ ] Retention deletion/anonymization logged in audit
- [ ] TLS 1.3 required for all federation endpoints
- [ ] Full cross-boundary audit trail on both sides
