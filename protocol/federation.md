<!-- blueprint
type: protocol
name: federation
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types]
platform: any
-->

# Weblisk Federation Protocol

Specification for multi-orchestrator collaboration, cross-tenant agent
invocation, and secure data exchange across organizational boundaries.
This protocol extends the single-orchestrator model into a federated
mesh where multiple orchestrators discover, trust, and delegate work
to each other while enforcing strict data sovereignty boundaries.

## Overview

Federation enables businesses to expose specific agent capabilities to
partners, customers, and the open marketplace — without exposing
internal systems, data, or infrastructure. Every cross-boundary
interaction is governed by data contracts, trust tiers, and behavioral
verification that go far beyond transport encryption.

The federation protocol treats data protection as a **structural
constraint**, not a policy afterthought. Data cannot leak because the
architecture makes it physically impossible for unpermitted fields to
cross a boundary.

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
| TrustPolicy | string | `trust_policy` | yes | `"explicit"` (manual approval) or `"registry"` (trust via marketplace) |
| MaxConcurrentFederated | int | `max_concurrent_federated` | no | Max concurrent cross-boundary tasks (default: 20) |
| Signature | string | `signature` | yes | Self-signed manifest |

---

## Trust Establishment

### Trust Tiers

| Tier | Trust Level | Discovery | Auth Model | Data Boundary |
|------|-------------|-----------|------------|---------------|
| **Private** | Full | Pre-configured | Shared signing authority | Minimal filtering (same org) |
| **Partner** | Scoped | Explicit peering | Mutual key exchange | Full data contract enforcement |
| **Public** | Minimal | Marketplace registry | Per-invocation auth | Strict data contracts + metering |

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
      {"field": "html_content", "type": "text", "max_size": "1MB", "description": "HTML to audit"}
    ],
    "permitted": [
      {"field": "url", "type": "string", "description": "Source URL for context"},
      {"field": "language", "type": "string", "description": "Content language code"}
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
      {"field": "url", "action": "strip_query_params", "reason": "Query params may contain tracking data"}
    ]
  },

  "outbound": {
    "required": [
      {"field": "seo_score", "type": "number"},
      {"field": "findings", "type": "array"}
    ],
    "permitted": [
      {"field": "findings[*].severity", "type": "string"},
      {"field": "findings[*].element", "type": "string"},
      {"field": "findings[*].message", "type": "string"},
      {"field": "recommendations[*].priority", "type": "string"},
      {"field": "recommendations[*].proposed", "type": "string"}
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
    "action": "delete",
    "audit_required": true
  },

  "jurisdiction_requirements": {
    "allowed": ["US", "CA", "GB", "EU"],
    "forbidden": [],
    "data_residency": "origin"
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
  3. Apply transformations (strip_query_params, hash, redact, etc.)
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

| Path | Method | Auth | Purpose |
|------|--------|------|---------|
| `/v1/federation/manifest` | GET | no | Return orchestrator manifest |
| `/v1/federation/peer` | POST | signature | Initiate peering request |
| `/v1/federation/peer-accept` | POST | signature | Accept peering request |
| `/v1/federation/peer-revoke` | POST | signature | Revoke trust relationship |
| `/v1/federation/key-rotate` | POST | dual-signature | Notify peers of key rotation |
| `/v1/federation/task` | POST | peer-auth | Execute a federated task |
| `/v1/federation/status` | GET | peer-auth | Federation health and peer status |
| `/v1/federation/contracts` | GET | peer-auth | List available data contracts |
| `/v1/federation/audit` | GET | peer-auth | Cross-boundary audit trail |

---

## Data Sovereignty

### Jurisdiction Enforcement

Every orchestrator declares its primary jurisdiction. Data contracts
declare jurisdiction requirements. The federation layer enforces both:

```
Before routing a federated task:
  1. Check data contract jurisdiction_requirements.allowed
  2. Check target orchestrator's jurisdiction
  3. If target jurisdiction is not in allowed list → REJECT
  4. If data_residency = "origin":
     Data MUST NOT be persisted by the receiving orchestrator
     beyond the processing window (max_hours from retention policy)
  5. If data_residency = "any":
     No residency restriction (but retention policy still applies)
```

### Retention Enforcement

Cross-boundary data has an explicit lifecycle:

```
1. Data arrives at receiving orchestrator
2. Clock starts: data_retention.max_hours
3. Task executes, result returned
4. On result delivery OR retention expiry (whichever is first):
   a. If action = "delete": purge all cross-boundary data
   b. If action = "anonymize": strip identifying fields, keep metrics
   c. If audit_required = true: log deletion/anonymization event
5. Receiving orchestrator MUST NOT retain cross-boundary data in:
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
