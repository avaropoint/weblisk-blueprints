<!-- blueprint
type: agent
kind: infrastructure
name: hub-verify
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, protocol/identity, protocol/federation, architecture/agent, architecture/hub]
platform: any
tier: free
port: 9773
-->

# Hub Verify Agent

Validates hub identity, manifest signatures, behavioral integrity,
and listing authenticity across the hub network. The trust enforcement
backbone of the registry role.

## Overview

Trust in the hub network is cryptographic, not reputational. The
hub-verify agent enforces this by:

1. Verifying Ed25519 signatures on hub manifests and listings
2. Detecting behavioral changes in provider capabilities
3. Validating data contract compliance
4. Performing identity verification for provider registration
5. Flagging anomalies for review by the hub-alert agent

Every listing that enters the index passes through verification.
Every behavioral change is detected and classified. Every key rotation
is validated against the federation protocol's dual-signature rules.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["listing_index", "verification_log", "behavioral_fingerprints"]},
    {"name": "database:write", "resources": ["verification_log", "behavioral_fingerprints"]},
    {"name": "crypto:verify", "resources": ["ed25519"]}
  ],
  "inputs": [
    {"name": "verification_request", "type": "json", "description": "Item to verify (listing, manifest, behavioral sample)"}
  ],
  "outputs": [
    {"name": "verification_result", "type": "json", "description": "Pass/fail with evidence and classification"}
  ],
  "collaborators": ["hub-index", "hub-metrics", "hub-alert"]
}
```

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token, services]
        - path: /v1/message
          methods: [POST]
          request_type: MessageEnvelope
          response_fields: [status, response]
        - path: /v1/health
          methods: [GET]
          response_fields: [status, details]
      types:
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: MessageEnvelope
          fields_used: [from, to, action, payload, trace_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: KeyRotationAnnouncement
          fields_used: [hub_name, old_key, new_key, old_signature, new_signature, timestamp]
      patterns:
        - behavior: dual-signature-rotation
          parameters: [old_key, new_key, cooldown_period]
        - behavior: key-revocation
          parameters: [revoked_key, reason, revocation_list]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/federation
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /contracts
          methods: [GET]
          description: Fetch capabilities for behavioral sampling
        - path: /status
          methods: [HEAD]
          description: Availability check during fingerprinting
      types:
        - name: FederatedListing
          fields_used: [listing_id, provider, capability, signature, public_key]
        - name: DataContract
          fields_used: [inbound_fields, outbound_fields, forbidden_fields,
                        jurisdiction, retention_policy]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: startup-sequence
          parameters: [identity, storage, registration, health]
        - behavior: shutdown-sequence
          parameters: [drain, deregister, close]
        - behavior: health-reporting
          parameters: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/hub
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ListingEntry
          fields_used: [listing_id, provider, capability, signature, public_key]
        - name: BehavioralChange
          fields_used: [listing_id, level, change_details]
      events:
        - topic: hub.listing.publish
          fields_used: [listing_id, provider, listing_data]
        - topic: hub.provider.register
          fields_used: [hub_name, federation_url, public_key]
        - topic: federation.key.rotated
          fields_used: [hub_name, old_key, new_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

extends:
  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: metrics
          parameters: [gauge, counter, histogram]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: token-validation
          parameters: [issuer, audience, claims]
        - behavior: signature-verification
          parameters: [algorithm, key_source]
        - behavior: key-management
          parameters: [rotation, revocation]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: reconciliation
          parameters: [on_change, self-validation, version-bump]
    on_change:
      compatible: validate
      breaking: halt-and-reconcile
      removed: halt-immediately

depends_on: []
  # Hub-verify operates independently. It notifies hub-index (for
  # re-verification) and hub-alert (for anomaly notifications) but
  # does not degrade if either is unavailable.
```

---

## Configuration

```yaml
config:
  fingerprint_interval:
    type: string
    default: "0 */4 * * *"
    env: WL_HUB_VERIFY_FINGERPRINT_INTERVAL
    description: Cron expression for behavioral fingerprint sampling schedule

  fingerprint_timeout:
    type: int
    default: 30
    env: WL_HUB_VERIFY_FINGERPRINT_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Timeout for individual behavioral fingerprint probe

  max_concurrent_probes:
    type: int
    default: 10
    env: WL_HUB_VERIFY_MAX_PROBES
    min: 1
    max: 50
    description: Maximum simultaneous behavioral probes

  key_rotation_cooldown:
    type: int
    default: 86400
    env: WL_HUB_VERIFY_ROTATION_COOLDOWN
    min: 3600
    unit: seconds
    description: Minimum time between key rotations (default 24h)

  verification_log_retention:
    type: int
    default: 7776000
    env: WL_HUB_VERIFY_LOG_RETENTION
    min: 2592000
    unit: seconds
    description: Verification log retention period (default 90 days)

  fingerprint_retention:
    type: int
    default: 15552000
    env: WL_HUB_VERIFY_FP_RETENTION
    min: 2592000
    unit: seconds
    description: Behavioral fingerprint retention period (default 180 days)

  response_tolerance_time_pct:
    type: float
    default: 20.0
    env: WL_HUB_VERIFY_TIME_TOLERANCE
    min: 1.0
    max: 100.0
    description: Response time change percentage threshold for BENIGN classification

  response_tolerance_size_pct:
    type: float
    default: 10.0
    env: WL_HUB_VERIFY_SIZE_TOLERANCE
    min: 1.0
    max: 100.0
    description: Response size change percentage threshold for BENIGN classification
```

---

## Types

```yaml
types:
  VerificationRecord:
    description: Result of a single verification operation
    fields:
      verification_id:
        type: string
        format: uuid-v7
        description: Unique verification identifier
      target_type:
        type: string
        enum: [listing, manifest, identity, key_rotation, data_contract, behavioral]
        description: What was verified
      target_id:
        type: string
        description: Identifier of the verified item (listing_id, hub_name, etc.)
      result:
        type: string
        enum: [pass, fail, warning]
        description: Verification outcome
      reason:
        type: string
        optional: true
        description: Failure or warning reason
      evidence:
        type: object
        optional: true
        description: Supporting evidence (signature details, diff, etc.)
      verified_at:
        type: int64
        auto: true
        description: When verification was performed
      verified_by:
        type: string
        description: Verification method or operator

  BehavioralFingerprint:
    description: Behavioral baseline for a capability
    fields:
      fingerprint_id:
        type: string
        format: uuid-v7
        description: Unique fingerprint identifier
      listing_id:
        type: string
        description: Listing being fingerprinted
      fingerprint_version:
        type: int
        min: 1
        description: Sequential fingerprint version
      captured_at:
        type: int64
        auto: true
        description: When fingerprint was captured
      schema_hash:
        type: string
        description: Hash of response field names and types
      response_fields:
        type: array
        items: string
        description: Top-level response field names
      avg_response_ms:
        type: int
        description: Average response time
      avg_response_bytes:
        type: int
        description: Average response size
      error_rate:
        type: float
        description: Error rate during sampling
      previous_fingerprint_version:
        type: int
        optional: true
        description: Previous version for comparison
      change_level:
        type: string
        enum: [BENIGN, NOTABLE, BREAKING, CRITICAL]
        optional: true
        description: Change classification if different from previous
      change_details:
        type: string
        optional: true
        description: Human-readable change summary

  KeyRotationRecord:
    description: Record of a key rotation event
    fields:
      rotation_id:
        type: string
        format: uuid-v7
        description: Unique rotation identifier
      hub_name:
        type: string
        description: Hub that rotated keys
      old_key_fingerprint:
        type: string
        description: Fingerprint of previous public key
      new_key_fingerprint:
        type: string
        description: Fingerprint of new public key
      dual_signature_valid:
        type: bool
        description: Whether both old and new key signed the announcement
      rotated_at:
        type: int64
        description: When rotation was performed
      cooldown_satisfied:
        type: bool
        description: Whether minimum cooldown period was met
```

---

## State Machine

```yaml
state_machine:
  agent:
    initial: created
    transitions:
      - from: created
        to: registered
        trigger: orchestrator_ack
        validates: agent_id assigned in response
      - from: registered
        to: active
        trigger: subscriptions_ready
        validates: event subscriptions active, storage connected
      - from: active
        to: verifying
        trigger: fingerprint_cycle_started
        validates: fingerprint lock acquired
      - from: verifying
        to: active
        trigger: fingerprint_cycle_complete
        validates: all probes finished or timed out
      - from: active
        to: degraded
        trigger: storage_error
        validates: storage write failed after retries
      - from: degraded
        to: active
        trigger: storage_recovered
        validates: storage write succeeds
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: verifying
        to: retiring
        trigger: shutdown_signal
        validates: signal received — drain active probes
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in-flight verifications completed or timed out
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID

Step 2 — Load Identity
  Action:      Load Ed25519 keypair from .weblisk/keys/hub-verify/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema against Types
  Validates:   verification_log, behavioral_fingerprints tables exist
  On Fail:     Run migration → if fails EXIT with STORAGE_UNREACHABLE

Step 4 — Load Revocation List
  Action:      Load known revoked keys from storage
  Validates:   Revocation list parsed and cached in memory
  On Fail:     Enter degraded state — may accept revoked keys

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 6 — Subscribe to Events
  Action:      Subscribe to hub.listing.publish, hub.provider.register,
               federation.key.rotated, hub.verify.request,
               system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED

Step 7 — Load Fingerprint Baselines
  Action:      Load latest fingerprint per listing from storage
  Validates:   Fingerprints loaded, cache populated
  On Fail:     Enter degraded state — behavioral detection impaired

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9773, fingerprints_loaded: N, revoked_keys: M}
```

### Shutdown Sequence

```
Step 1 — Stop Accepting Verification Requests
  Action:      Unsubscribe from event topics
  agent_state → retiring

Step 2 — Drain In-Flight Verifications
  Action:      Wait for active verifications to complete (up to 30s)
  On Timeout:  Record partial results

Step 3 — Deregister
  Action:      DELETE /v1/register

Step 4 — Close Storage
  Action:      Close database connection

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, verifications_drained}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - storage connected
      - event subscriptions active
      - revocation list loaded
      - fingerprint baselines available
    response:
      status: healthy
      details: {storage, subscriptions, revocation_list_size,
                fingerprints_loaded, last_fingerprint_cycle}

  degraded:
    conditions:
      - storage errors (retrying)
      - revocation list stale
      - fingerprint cycle failed
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retries
      - no event subscriptions active
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

```
Step 1 — Validate new blueprint, verify version is newer
Step 2 — Compare Types block against current storage schema
Step 3 — Pause verification processing → run migration → resume
Step 4 — Reload configuration and revocation list
Log: lifecycle.version_updated {from, to}
```

---

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.listing.publish` | New listing needs signature verification |
| Event: `hub.provider.register` | New provider needs identity verification |
| Event: `federation.key.rotated` | Provider key change needs validation |
| Schedule: `0 */4 * * *` | Every 4 hours — behavioral fingerprint sampling |
| Event: `hub.verify.request` | On-demand verification from admin or other agents |

---

## Actions

### verify-listing

Verify Ed25519 signature on a listing.

**Source:** Hub Index

**Input:** `{listing_id: string, provider: string, signature: string, public_key: string, listing_data: object}`

**Processing:**

```
1. Check key against revocation list → if revoked, fail immediately
2. Reconstruct canonical listing bytes (deterministic serialization)
3. Verify Ed25519 signature: crypto.verify(public_key, canonical_bytes, signature)
4. Check key matches provider's registered identity
5. Record VerificationRecord
6. If fail → notify hub-alert
```

**Output:** `{result: "pass" | "fail", verification_id: string, reason?: string}`

**Errors:** `KEY_REVOKED` (permanent), `SIGNATURE_INVALID` (permanent), `STORAGE_ERROR` (transient)

---

### verify-manifest

Verify a provider's orchestrator manifest.

**Source:** Hub Index

**Input:** `{hub_name: string, manifest: object, signature: string, public_key: string}`

**Processing:**

```
1. Same signature verification as verify-listing
2. Additionally verify manifest structure and required fields
3. Record VerificationRecord
```

**Output:** `{result: "pass" | "fail", verification_id: string}`

---

### verify-identity

Validate provider identity (key, domain, TLS).

**Source:** Admin / Hub Index

**Input:** `{hub_name: string, federation_url: string, public_key: string}`

**Processing:**

```
1. Verify federation_url uses HTTPS
2. Fetch provider's public key from federation endpoint
3. Compare with claimed public_key
4. Verify TLS certificate validity
5. Record VerificationRecord
```

**Output:** `{result: "pass" | "fail", verification_id: string, details: object}`

---

### verify-key-rotation

Validate key rotation with dual-signature proof.

**Source:** Federation

**Input:** `{hub_name: string, old_key: string, new_key: string, old_signature: string, new_signature: string, timestamp: int64}`

**Processing:**

```
1. Verify old key signature on rotation announcement
2. Verify new key signature on rotation announcement (dual-signature)
3. Check rotation cooldown: minimum config.key_rotation_cooldown since last rotation
4. Record KeyRotationRecord
5. If valid → notify hub-index to re-verify all listings with new key
6. If invalid → reject, notify hub-alert as potential compromise
```

**Output:** `{result: "pass" | "fail", rotation_id: string}`

---

### fingerprint-behavior

Sample a capability and compare to baseline.

**Source:** Cron

**Input:** `{listing_id: string}`

**Processing:**

```
1. Select capability to probe
2. Send standard test input (deterministic, per capability type)
3. Record response structure: schema, size, timing, errors
4. Compare to latest BehavioralFingerprint baseline
5. If different → classify change level
6. Store new BehavioralFingerprint
7. If BREAKING or CRITICAL → emit hub.behavioral.change event
```

**Output:** `{listing_id: string, change_detected: bool, level?: string}`

---

### classify-change

Classify behavioral change level.

**Source:** Internal

**Input:** `{listing_id: string, old_fingerprint: BehavioralFingerprint, new_fingerprint: BehavioralFingerprint}`

**Processing:**

```
1. Compare schema_hash → if different, check field changes
2. Compare response_fields → added fields = NOTABLE, removed = BREAKING
3. Compare avg_response_ms → within tolerance = BENIGN, >50% change = NOTABLE
4. Compare error_rate → increase from <1% to >5% = CRITICAL
5. Return highest level from all comparisons
```

**Output:** `{level: "BENIGN" | "NOTABLE" | "BREAKING" | "CRITICAL", details: string}`

---

### get-verification-log

Verification history for a listing or provider.

**Source:** Admin

**Input:** `{target_id?: string, target_type?: string, limit?: int, offset?: int}`

**Output:** `{records: VerificationRecord[], total: int}`

**Side Effects:** None (read-only).

---

### get-fingerprint

Current behavioral fingerprint for a capability.

**Source:** Admin / Consumer

**Input:** `{listing_id: string}`

**Output:** `{fingerprint: BehavioralFingerprint}`

---

### verify-data-contract

Validate a data contract's integrity and terms.

**Source:** Consumer Hub

**Input:** `{listing_id: string, contract: DataContract}`

**Processing:**

```
1. Verify signature on data contract
2. Validate structure: inbound/outbound/forbidden fields, jurisdiction, retention
3. Check consistency with listing claims
4. Record VerificationRecord
```

**Output:** `{result: "pass" | "fail" | "warning", details: object}`

---

### bulk-verify

Re-verify all listings from a specific provider.

**Source:** Admin

**Input:** `{hub_name: string}`

**Output:** `{verified: int, passed: int, failed: int}`

---

## Signature Verification

### Listing Verification

```
1. EXTRACT public_key from listing.provider
2. RECONSTRUCT canonical listing bytes
   - Serialize listing fields (excluding signature) in deterministic order
   - UTF-8 encode
3. VERIFY Ed25519 signature
   - crypto.verify(public_key, canonical_bytes, listing.signature)
4. CHECK key validity
   - Key not in revocation list
   - Key matches provider's registered identity
5. RETURN verification result
```

### Manifest Verification

Same process applied to the provider's orchestrator manifest. The
manifest signature proves the provider controls the claimed identity.

### Key Rotation Verification

When a provider rotates keys per `protocol/identity.md`:

```
1. RECEIVE rotation announcement (signed by OLD key)
2. VERIFY old key signature on announcement
3. VERIFY new key signature on announcement (dual-signature)
4. CHECK rotation cooldown (minimum 24h between rotations)
5. UPDATE provider's registered key
6. NOTIFY hub-index to re-verify all listings with new key
7. LOG rotation event in verification log
```

---

## Behavioral Fingerprinting

The verify agent periodically samples published capabilities to detect
behavioral changes:

```
1. SELECT capability to probe
2. SEND standard test input (deterministic, per capability type)
3. RECORD response structure
   - Response schema (field names, types, nesting)
   - Response size range
   - Response time range
   - Error handling behavior
4. COMPARE to baseline fingerprint
5. CLASSIFY change level if different
```

### Change Classification

| Level | Criteria | Example |
|-------|----------|---------|
| BENIGN | Response time ±20%, size ±10%, same schema | Performance optimization |
| NOTABLE | New optional fields, different scoring range | Feature addition |
| BREAKING | Required fields removed, schema restructured | API redesign |
| CRITICAL | Unexpected errors, data contract violation, key mismatch | Compromise or major bug |

### Fingerprint Storage

```json
{
  "listing_id": "avaropoint:seo-audit",
  "fingerprint_version": 3,
  "captured_at": 1712160000,
  "schema_hash": "a1b2c3d4...",
  "response_fields": ["score", "findings", "recommendations"],
  "avg_response_ms": 3200,
  "avg_response_bytes": 8192,
  "error_rate": 0.002,
  "previous_fingerprint_version": 2,
  "change_level": "BENIGN",
  "change_details": "Response time improved by 15%"
}
```

---

## Data Contract Verification

When a consumer hub requests data contract validation:

```
1. FETCH data contract from provider
2. VERIFY signature on data contract
3. VALIDATE contract structure
   - Inbound fields defined
   - Outbound fields defined
   - Forbidden fields explicitly listed
   - Jurisdiction declared
   - Retention policy present
4. CHECK consistency with listing claims
5. RETURN verification result with any warnings
```

---

## Execute Workflow

The core verification processing loop:

```
Phase 1 — Receive Verification Request
  Accept event from bus (listing publish, key rotation, verify request)
  Determine verification type from event topic
  If malformed → log and discard

Phase 2 — Key Validation
  Load provider's registered public key
  Check against revocation list → if revoked, fail immediately
  For key rotation: validate dual-signature proof

Phase 3 — Signature Verification
  Reconstruct canonical bytes from target content
  Verify Ed25519 signature
  Record result in VerificationRecord

Phase 4 — Classification (for behavioral fingerprinting)
  If fingerprint cycle:
    For each listing (up to config.max_concurrent_probes):
      Send test input, record response
      Compare to baseline fingerprint
      Classify change level
      Store new BehavioralFingerprint

Phase 5 — Notification
  If verification failed:
    Emit hub.verification.failure → hub-alert
  If BREAKING or CRITICAL behavioral change:
    Emit hub.behavioral.change → hub-alert
    If CRITICAL: emit hub.listing.suspended
  If key rotation valid:
    Notify hub-index to re-verify all provider listings

Phase 6 — Record and Emit
  Store VerificationRecord in verification_log
  Store BehavioralFingerprint in behavioral_fingerprints
  Emit metrics: hub_verify_operations_total
```

---

## Collaboration

```yaml
events_published:
  - topic: hub.verification.failure
    payload: {listing_id, provider, reason, verification_id}
    when: Signature or identity verification failed

  - topic: hub.behavioral.change
    payload: {listing_id, level, previous_version, new_version, change_summary}
    when: Behavioral fingerprint detected change (NOTABLE or higher)

  - topic: hub.listing.suspended
    payload: {listing_id, reason}
    when: CRITICAL behavioral change or verification failure warrants suspension

  - topic: hub.verify.completed
    payload: {verification_id, target_type, target_id, result}
    when: Any verification operation completed

events_subscribed:
  - topic: hub.listing.publish
    payload: {listing_id, provider, listing_data}
    action: verify-listing

  - topic: hub.provider.register
    payload: {hub_name, federation_url, public_key}
    action: verify-identity

  - topic: federation.key.rotated
    payload: {hub_name, old_key, new_key, old_signature, new_signature}
    action: verify-key-rotation

  - topic: hub.verify.request
    payload: {target_type, target_id, data}
    action: Route to appropriate verify action

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "hub-verify"
    action: Self-update procedure

direct_messages:
  - target: hub-index
    action: reindex
    when: Key rotation validated — provider listings need re-verification
    reason: New key means all existing signatures must be re-verified

  - target: hub-alert
    action: notify-verification-failure
    when: Verification failure detected
    reason: Operator and affected collaborators must be notified

  - target: hub-alert
    action: notify-behavioral-change
    when: Behavioral change at NOTABLE level or higher
    reason: Collaborators need awareness of capability changes
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All verification and fingerprinting is autonomous
  supervised:    Bulk operations and suspension require operator
  manual-only:   All verification requires operator trigger

overridable_behaviors:
  - behavior: automatic_fingerprinting
    default: enabled
    override: Set WL_HUB_VERIFY_FINGERPRINT_ENABLED=false
    audit: logged

  - behavior: automatic_suspension
    default: enabled
    override: Set WL_HUB_VERIFY_AUTO_SUSPEND=false
    audit: logged
    note: CRITICAL changes will still be flagged but not auto-suspended

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: bulk-verify
    description: Re-verify all listings from a provider
    allowed: operator

  - action: add-to-revocation-list
    description: Manually revoke a provider key
    allowed: operator

  - action: force-fingerprint
    description: Trigger immediate behavioral fingerprint cycle
    allowed: operator

  - action: override-suspension
    description: Lift automatic listing suspension after review
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Required — operator must provide reason
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT modify listing content — only verify and classify
    - MUST NOT approve listings that fail signature verification
    - Fingerprint probe rate bounded by config.max_concurrent_probes

  forbidden_actions:
    - MUST NOT bypass Ed25519 signature verification for any reason
    - MUST NOT accept key rotations without dual-signature proof
    - MUST NOT accept key rotations within cooldown period
    - MUST NOT expose provider private keys or internal state
    - MUST NOT fabricate fingerprints or verification results

  resource_limits:
    memory: 512 MB (process limit)
    verification_log: governed by config.verification_log_retention
    behavioral_fingerprints: governed by config.fingerprint_retention
    concurrent_probes: config.max_concurrent_probes
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Signature verification failure | Reject item. Notify hub-alert. Log with full context. |
| Provider unreachable during fingerprint | Skip this cycle. Flag if unreachable for 3+ cycles. |
| Key rotation without dual signature | Reject rotation. Flag as potential compromise. Notify hub-alert. |
| Behavioral CRITICAL change | Immediately notify hub-alert. Suspend listing pending review. |
| Storage unavailable | Queue verification results. Process when storage recovers. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_verify_operations_total | counter | Verifications by type and result (pass/fail) |
| hub_verify_duration_seconds | histogram | Verification execution time |
| hub_verify_signature_failures_total | counter | Signature verification failures |
| hub_verify_behavioral_changes_total | counter | Behavioral changes detected by level |
| hub_verify_fingerprints_total | gauge | Active behavioral fingerprints |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send messages to hub-index, hub-alert, and respond to queries

    - capability: http:send
      resources: ["https://*"]
      description: Probe provider endpoints for behavioral fingerprinting

    - capability: database:read
      resources: [listing_index, verification_log, behavioral_fingerprints]
      description: Read index, verification history, and fingerprint baselines

    - capability: database:write
      resources: [verification_log, behavioral_fingerprints]
      description: Write verification records and fingerprints

    - capability: crypto:verify
      resources: [ed25519]
      description: Verify signatures on listings, manifests, and key rotations

  data_sensitivity:
    - data: Verification results
      classification: medium
      handling: Contains pass/fail decisions — logged and queryable by admin

    - data: Behavioral fingerprints
      classification: medium
      handling: Contains response structure analysis — encrypted at rest

    - data: Revocation list
      classification: high
      handling: Key revocations affect trust decisions — integrity-critical

    - data: Provider public keys
      classification: low
      handling: Public data per federation protocol

    - data: Test inputs for fingerprinting
      classification: low
      handling: Deterministic, non-sensitive test payloads

  access_control:
    - caller: hub-index
      actions: [verify-listing, verify-manifest, verify-identity]

    - caller: Federation layer
      actions: [verify-key-rotation]

    - caller: Consumer hub (authenticated)
      actions: [verify-data-contract, get-fingerprint]

    - caller: Cron agent
      actions: [fingerprint-behavior]

    - caller: Operator (auth token with operator role)
      actions: [bulk-verify, get-verification-log, get-fingerprint,
                add-to-revocation-list, force-fingerprint,
                override-suspension]

    - caller: Unauthenticated
      actions: []
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Valid listing passes verification
    action: verify-listing
    input:
      listing_id: "avaropoint:seo-audit"
      provider: "avaropoint-prod"
      signature: "<valid-ed25519-signature>"
      public_key: "<provider-public-key>"
      listing_data: {capability: {domain: "seo", action: "audit"}}
    expected:
      result: pass
      verification_id: "<uuid-v7>"
    validates:
      - VerificationRecord created with result = pass
      - No hub-alert notification sent

  - name: Valid key rotation with dual signature
    action: verify-key-rotation
    input:
      hub_name: "partner-hub"
      old_key: "<old-public-key>"
      new_key: "<new-public-key>"
      old_signature: "<old-key-signs-announcement>"
      new_signature: "<new-key-signs-announcement>"
    expected:
      result: pass
      rotation_id: "<uuid-v7>"
    validates:
      - KeyRotationRecord created
      - hub-index notified to re-verify listings

  - name: Behavioral fingerprint no change
    action: fingerprint-behavior
    input: {listing_id: "stable:capability"}
    expected: {change_detected: false}
    validates:
      - BehavioralFingerprint stored
      - No hub.behavioral.change event emitted
```

### Error Cases

```yaml
  - name: Invalid signature rejected
    action: verify-listing
    input:
      listing_id: "bad:listing"
      signature: "<invalid-signature>"
      public_key: "<provider-key>"
    expected:
      result: fail
      reason: "SIGNATURE_INVALID"
    validates:
      - hub-alert notified of verification failure
      - Listing NOT approved for indexing

  - name: Key rotation without dual signature
    action: verify-key-rotation
    input:
      hub_name: "suspicious-hub"
      old_signature: "<valid>"
      new_signature: "<missing>"
    expected:
      result: fail
    validates:
      - Rotation rejected
      - Flagged as potential compromise
```

### Edge Cases

```yaml
  - name: Revoked key immediately rejected
    action: verify-listing
    input: {public_key: "<revoked-key>", signature: "<valid-for-revoked>"}
    expected: {result: fail, reason: "KEY_REVOKED"}
    validates: Revocation list checked before signature verification

  - name: CRITICAL behavioral change triggers suspension
    action: fingerprint-behavior
    condition: Response returns unexpected errors, error_rate jumps to 50%
    expected:
      change_detected: true
      level: CRITICAL
    validates:
      - hub.behavioral.change event emitted with level = CRITICAL
      - hub.listing.suspended event emitted
      - hub-alert receives immediate notification

  - name: Key rotation within cooldown rejected
    action: verify-key-rotation
    condition: Last rotation was 12 hours ago, cooldown is 24h
    expected: {result: fail, reason: "COOLDOWN_NOT_SATISFIED"}
    validates: Cooldown enforced per config.key_rotation_cooldown
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: unbounded

  inter_agent:
    protocol: message-bus-only
    direct_http: forbidden
    routing: by agent name, never by instance address

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: fingerprint_lock in storage
      leader: [fingerprint-behavior cycle, bulk-verify]
      follower: [verify-listing, verify-manifest, verify-identity,
                 verify-key-rotation, health reporting]
      promotion: automatic when fingerprint lock expires
    state_sharing:
      mechanism: shared sqlite database
      conflict_resolution: >
        Verification records are append-only — no write conflicts.
        Fingerprint lock prevents duplicate behavioral sampling.
        Revocation list changes are idempotent.

  event_handling:
    consumer_group: hub-verify
    delivery: one-per-group
    description: >
      Bus delivers each verification event to ONE instance in the
      hub-verify consumer group.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 10
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share verification_log and behavioral_fingerprints
      database. Schema migrations are additive-only during shadow.
```

---

## Implementation Notes

- **Zero tolerance for unverified content**: Every listing, manifest,
  and key rotation MUST pass Ed25519 verification. There is no
  override, no bypass, no exception. This is the foundational trust
  property of the hub network.
- **Deterministic test inputs**: Behavioral fingerprinting uses
  capability-specific deterministic test inputs. The same input always
  produces the same test conditions, making change detection reliable.
- **Change classification conservatism**: When in doubt, classify
  higher. A change that could be NOTABLE or BREAKING should be
  classified as BREAKING. False positives are preferable to missed
  breaking changes.
- **Dual-signature requirement**: Key rotation requires both old and
  new keys to sign the announcement. This prevents key theft — an
  attacker with only the new key cannot complete rotation without
  the old key.
- **Cooldown period**: The 24-hour minimum between key rotations
  prevents rapid key cycling that could indicate compromise or abuse.
- **Revocation is permanent**: Once a key is added to the revocation
  list, it is never removed. Revoked keys are rejected immediately
  without attempting signature verification.

---

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Ed25519 signatures are correctly verified for listings and manifests
- [ ] Invalid signatures are rejected with detailed error
- [ ] Key rotation requires valid dual-signature proof
- [ ] Behavioral fingerprints are sampled on schedule
- [ ] Change classification follows defined criteria (BENIGN/NOTABLE/BREAKING/CRITICAL)
- [ ] CRITICAL changes trigger immediate listing suspension
- [ ] Data contract verification validates all required sections
- [ ] Verification log is queryable by listing and provider
- [ ] All verification operations emit metrics
- [ ] Revoked keys are rejected immediately
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] State machine validates verification processing transitions
- [ ] Startup sequence gates each step with pre-check/validates/on-fail
- [ ] Shutdown drains in-flight verifications before exit
- [ ] Configuration values validated against declared constraints
- [ ] Override audit records who, what, when, why
- [ ] Scaling: fingerprint lock prevents duplicate behavioral cycles
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Blue-green: shadow phase validates events without side effects
