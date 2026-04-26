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

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.listing.publish` | New listing needs signature verification |
| Event: `hub.provider.register` | New provider needs identity verification |
| Event: `federation.key.rotated` | Provider key change needs validation |
| Schedule: `0 */4 * * *` | Every 4 hours — behavioral fingerprint sampling |
| Event: `hub.verify.request` | On-demand verification from admin or other agents |

## HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| verify-listing | Hub Index | Verify Ed25519 signature on a listing |
| verify-manifest | Hub Index | Verify a provider's orchestrator manifest |
| verify-identity | Admin/Hub Index | Validate provider identity (key, domain, TLS) |
| verify-key-rotation | Federation | Validate key rotation with dual-signature proof |
| fingerprint-behavior | Cron | Sample a capability and compare to baseline |
| classify-change | Internal | Classify behavioral change level (BENIGN/NOTABLE/BREAKING/CRITICAL) |
| get-verification-log | Admin | Verification history for a listing or provider |
| get-fingerprint | Admin/Consumer | Current behavioral fingerprint for a capability |
| verify-data-contract | Consumer Hub | Validate a data contract's integrity and terms |
| bulk-verify | Admin | Re-verify all listings from a specific provider |

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

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_verify_operations_total | counter | Verifications by type and result (pass/fail) |
| hub_verify_duration_seconds | histogram | Verification execution time |
| hub_verify_signature_failures_total | counter | Signature verification failures |
| hub_verify_behavioral_changes_total | counter | Behavioral changes detected by level |
| hub_verify_fingerprints_total | gauge | Active behavioral fingerprints |

## Error Handling

| Error | Handling |
|-------|---------|
| Signature verification failure | Reject item. Notify hub-alert. Log with full context. |
| Provider unreachable during fingerprint | Skip this cycle. Flag if unreachable for 3+ cycles. |
| Key rotation without dual signature | Reject rotation. Flag as potential compromise. Notify hub-alert. |
| Behavioral CRITICAL change | Immediately notify hub-alert. Suspend listing pending review. |
| Storage unavailable | Queue verification results. Process when storage recovers. |

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
