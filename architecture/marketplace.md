<!-- blueprint
type: architecture
name: marketplace
version: 1.0.0
requires: [protocol/federation, protocol/identity, protocol/types, architecture/agent]
platform: any
-->

# Weblisk Marketplace

Architecture for the agent and capability marketplace — a federated
registry where orchestrators publish, discover, and consume agent
capabilities across organizational boundaries. The marketplace
operates on top of the federation protocol and inherits all of its
trust, data contract, and sovereignty guarantees.

## Overview

The marketplace is the discovery and commerce layer of the federation.
While the federation protocol handles trust and data boundaries, the
marketplace handles: How do I find agents that can do what I need? How
do I evaluate them? How do I pay for them?

The marketplace is itself federated — there is no single central
registry. Any orchestrator can publish capabilities. Discovery relies
on a combination of registry servers (operated by Avaropoint and, in
the future, by partners) and direct peer discovery.

## Design Principles

1. **Registry is a convenience, not a requirement** — Two orchestrators
   can peer directly without any registry. The marketplace makes
   discovery easier but is never mandatory.
2. **Trust is verified, not assumed** — Listing on a marketplace does
   not imply trust. Every consumer independently verifies the provider's
   identity, reviews data contracts, and establishes a trust relationship
   before any data flows.
3. **Transparency over reputation** — Rather than opaque reputation
   scores, the marketplace surfaces verifiable facts: uptime, response
   times, behavioral change frequency, data contract strictness, and
   audit logs.
4. **Tier separation is structural** — Free and paid capabilities differ
   in concrete terms (SLAs, concurrency, support), not in hidden quality
   gates. Free capabilities use the same security model as paid ones.

---

## Marketplace Roles

| Role | Description | Examples |
|------|-------------|---------|
| **Provider** | An orchestrator that publishes agent capabilities for others to consume | A company offering SEO analysis to partners |
| **Consumer** | An orchestrator that discovers and invokes published capabilities | A web agency consuming SEO analysis |
| **Registry** | A service that indexes published capabilities and serves search queries | Avaropoint's public registry, a private enterprise registry |

A single orchestrator can be both a provider and a consumer
simultaneously.

---

## Capability Listing

When a provider publishes a capability to the marketplace, the listing
includes verifiable metadata (not just marketing text):

### ListingEntry

```json
{
  "listing_id": "avaropoint:seo-audit",
  "provider": {
    "orchestrator_name": "avaropoint-prod",
    "public_key": "<hex Ed25519 public key>",
    "federation_url": "https://agents.avaropoint.com/v1/federation",
    "jurisdiction": "US",
    "verified": true
  },
  "capability": {
    "domain": "seo",
    "action": "audit",
    "version": "1.2.0",
    "description": "Comprehensive SEO audit with technical, content, and link analysis",
    "data_contract": "seo-audit-v1"
  },
  "tier": "pro",
  "pricing": {
    "model": "per_invocation",
    "currency": "USD",
    "unit_price": 0.05,
    "free_quota": 100,
    "billing_cycle": "monthly"
  },
  "sla": {
    "availability_target": 99.9,
    "p95_latency_ms": 5000,
    "max_concurrent": 50,
    "support_level": "business_hours"
  },
  "metrics": {
    "uptime_30d": 99.95,
    "p95_latency_30d_ms": 3200,
    "total_invocations_30d": 142000,
    "error_rate_30d": 0.002,
    "behavioral_changes_90d": 1,
    "last_behavioral_change": 1710000000,
    "last_behavioral_change_level": "BENIGN"
  },
  "compliance": {
    "data_contract_version": "1.0.0",
    "jurisdiction": "US",
    "certifications": [],
    "retention_hours": 24
  },
  "published_at": 1712160000,
  "signature": "<provider's Ed25519 signature over listing>"
}
```

### Listing Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| listing_id | string | yes | `{provider}:{capability}` unique identifier |
| provider | ProviderInfo | yes | Provider orchestrator identity |
| capability | CapabilityInfo | yes | What the listing offers |
| tier | string | yes | `"free"` or `"pro"` |
| pricing | PricingInfo | yes for pro | Pricing model and rates |
| sla | SLAInfo | yes for pro | Service level commitments |
| metrics | MetricsInfo | yes | Verifiable performance data (auto-populated by registry) |
| compliance | ComplianceInfo | yes | Regulatory and data handling metadata |
| published_at | int64 | yes | Unix epoch seconds |
| signature | string | yes | Provider's signature over the listing |

---

## Free vs Pro Tiers

Tier separation is about capability scope and service levels, not
security or quality. Both tiers use the same federation protocol, data
contracts, and trust enforcement.

### Tier Comparison

| Aspect | Free | Pro |
|--------|------|-----|
| **Federation protocol** | Full | Full |
| **Data contracts** | Full enforcement | Full enforcement |
| **Behavioral verification** | Full | Full |
| **Concurrency** | Limited (5 concurrent) | Configurable (up to SLA) |
| **Rate limiting** | Strict (100/hour) | Per-contract |
| **SLA** | Best-effort | Contractual (99.9%+) |
| **Support** | Community | Business hours or 24/7 |
| **Retention** | Minimum (1 hour) | Configurable (per contract) |
| **Metering** | Usage-capped (free quota) | Pay-per-use or subscription |
| **Priority routing** | Standard | Priority queue |
| **Audit access** | Self-only | Shared audit with provider |

### Pricing Models

| Model | Description | Suited For |
|-------|-------------|------------|
| **per_invocation** | Charge per federated task execution | High-volume, low-cost tasks |
| **monthly_subscription** | Flat fee for unlimited (or capped) access | Predictable workloads |
| **tiered** | Price brackets based on volume | Variable workloads |
| **custom** | Negotiated pricing for enterprise | Large partnerships |

### Usage Metering

Both orchestrators independently track usage for reconciliation:

```json
{
  "period": "2024-04",
  "consumer_orch": "acme-corp",
  "provider_orch": "avaropoint-prod",
  "listing_id": "avaropoint:seo-audit",
  "invocations": 1247,
  "successful": 1240,
  "failed": 7,
  "total_latency_ms": 3984000,
  "data_transferred_bytes": 52428800,
  "billing": {
    "unit_price": 0.05,
    "free_quota": 100,
    "billable_invocations": 1147,
    "amount": 57.35,
    "currency": "USD"
  },
  "consumer_signature": "<consumer's signature>",
  "provider_signature": "<provider's signature>"
}
```

Both signatures on the metering record ensure neither party can
dispute the usage. Discrepancies are flagged for manual resolution.

---

## Discovery

### Registry Search

Consumers search the registry by capability, domain, jurisdiction, and
tier.

**GET /v1/marketplace/search**

```
Query Parameters:
  domain    — Filter by domain (e.g., "seo")
  action    — Filter by action (e.g., "audit")
  tier      — "free", "pro", or "all" (default: "all")
  jurisdiction — Filter by provider jurisdiction (ISO 3166-1)
  min_uptime   — Minimum 30-day uptime percentage
  max_latency  — Maximum p95 latency in ms
  sort      — "relevance", "uptime", "latency", "price", "invocations"
  page      — Page number (default: 1)
  per_page  — Results per page (default: 20, max: 100)
```

**Response:**

```json
{
  "results": [ /* array of ListingEntry */ ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

### Direct Discovery

Without a registry, an orchestrator can query another orchestrator's
published capabilities directly:

**GET /v1/federation/contracts** (from federation protocol)

Returns the data contracts and published capabilities that the target
orchestrator offers to peers at the requester's trust tier.

---

## Onboarding Flow

How a consumer starts using a marketplace capability:

```
1. DISCOVER
   Consumer searches the registry or queries a provider directly.
   Consumer reviews listing: capability, data contract, SLA, pricing,
   behavioral metrics, jurisdiction.

2. REVIEW DATA CONTRACT
   Consumer downloads the data contract for the capability.
   Consumer reviews:
     - What inbound data is required/permitted
     - What outbound data will be returned
     - What fields are forbidden (what the provider will NEVER receive)
     - Jurisdiction requirements
     - Retention policy
   Consumer's legal/compliance team approves the contract.

3. INITIATE PEERING
   Consumer's orchestrator sends a peering request to the provider
   (POST /v1/federation/peer) with:
     - Consumer's orchestrator manifest
     - Requested capabilities
     - Accepted data contracts
   
4. PROVIDER REVIEW
   Provider reviews the request:
     - Consumer's identity (public key)
     - Consumer's jurisdiction (compatible?)
     - Requested capabilities (authorized for consumer's tier?)
   Provider approves or rejects.

5. TRUST ESTABLISHED
   Provider sends peer-accept. Both orchestrators exchange manifests
   and public keys. Federation link is live.

6. FIRST INVOCATION
   Consumer's domain controller includes the federated capability in
   its workflow. First federated task executes with full data contract
   enforcement, behavioral verification, and audit logging.

7. MONITORING
   Both parties monitor:
     - Usage against quotas and SLAs
     - Behavioral fingerprint stability
     - Data contract compliance
     - Error rates and latency
```

---

## Behavioral Change in a Marketplace Context

Behavioral integrity is especially critical in the marketplace because
consumers rely on capabilities they do not own or control.

### Provider Obligations

When a provider updates an agent that backs a marketplace capability:

1. **Compute behavioral change level** (BENIGN/NOTABLE/BREAKING/CRITICAL)
   per the federation protocol's change detection rules.

2. **For BENIGN changes:** Publish updated metrics. No disruption.

3. **For NOTABLE changes:**
   - Update the marketplace listing with new version
   - Notify all consumers via `POST /v1/federation/notify`
   - Allow 7-day parallel running of old + new version

4. **For BREAKING changes:**
   - Publish new listing version alongside old
   - Notify all consumers with detailed changelog
   - Provide 30-day deprecation window for old version
   - Consumers must explicitly opt-in to new version

5. **For CRITICAL changes:**
   - Immediately suspend the listing from marketplace
   - Notify all consumers: `BEHAVIORAL_CHANGE_CRITICAL`
   - Require re-approval from all active consumers
   - Registry flags the listing with a change alert

### Consumer Protections

- **Version pinning:** Consumer can pin to a specific version. Provider
  MUST continue serving the pinned version during deprecation.
- **Change notifications:** All changes above BENIGN trigger a
  notification to the consumer's orchestrator.
- **Automatic suspension:** If a provider's agent triggers a CRITICAL
  behavioral change, the consumer's orchestrator automatically suspends
  federated tasks to that agent until admin review.
- **Audit trail:** Full history of behavioral changes is visible in the
  listing's metrics.

---

## Revocation and Removal

### Consumer Disconnects

A consumer can revoke trust at any time:

```
POST /v1/federation/peer-revoke
```

- All in-flight federated tasks are allowed to complete (with timeout)
- No new tasks are dispatched
- Metering finalizes at revocation timestamp
- Data retention clock starts on both sides

### Provider Delists

A provider can remove a listing from the marketplace:

```
POST /v1/marketplace/delist
```

- All active consumers notified with 30-day warning
- New peering requests rejected immediately
- Existing peers continue for deprecation window
- After deprecation: trust relationships expire
- Listing removed from registry search results

### Emergency Revocation

In case of a security incident (compromised key, data breach, malicious
behavior):

```
POST /v1/federation/peer-revoke
{
  "reason": "security_incident",
  "immediate": true
}
```

- All in-flight tasks are immediately cancelled
- Trust relationship terminated with no grace period
- All cross-boundary data purged (per retention policy)
- Incident logged in both audit trails
- Registry notified (listing flagged for review)

---

## Registry Architecture

The registry itself is a Weblisk orchestrator with specialized agents:

| Component | Role |
|-----------|------|
| **Index Agent** | Crawls and indexes orchestrator manifests from known providers |
| **Search Agent** | Handles search queries with ranking and filtering |
| **Metrics Agent** | Collects and aggregates uptime, latency, and usage metrics |
| **Verification Agent** | Validates provider identity and manifest signatures |
| **Alert Agent** | Monitors behavioral changes and notifies affected consumers |

The registry NEVER handles actual federated task data. It only indexes
metadata (listings, metrics, contracts). All data exchange happens
directly between consumer and provider through the federation protocol.

### Registry Federation

Multiple registries can federate with each other, sharing listing
indexes. This prevents a single point of failure and supports regional
or vertical-specific registries:

```
Global Registry (Avaropoint)
  ├── EU Registry (regional)
  ├── APAC Registry (regional)
  └── Healthcare Registry (vertical)
```

Each registry independently verifies provider signatures. A listing
appearing in multiple registries carries the same cryptographic proof
regardless of which registry serves it.

---

## Marketplace Endpoints

Registry-specific endpoints (in addition to federation endpoints):

| Path | Method | Auth | Purpose |
|------|--------|------|---------|
| `/v1/marketplace/search` | GET | public | Search capability listings |
| `/v1/marketplace/listing/{id}` | GET | public | Get listing details |
| `/v1/marketplace/publish` | POST | provider-auth | Publish or update a listing |
| `/v1/marketplace/delist` | POST | provider-auth | Remove a listing |
| `/v1/marketplace/metrics/{id}` | GET | public | Get listing performance metrics |
| `/v1/marketplace/contracts/{name}` | GET | public | Download a data contract |
| `/v1/marketplace/notify` | POST | provider-auth | Send change notification to consumers |
| `/v1/marketplace/usage` | GET | peer-auth | Usage metering for billing period |

---

## Security Considerations

The marketplace layer adds these security concerns beyond the
federation protocol:

1. **Listing integrity** — Listings are signed by the provider.
   Registries verify signatures before indexing. Consumers verify
   signatures before peering. A tampered listing is cryptographically
   detectable.

2. **Sybil resistance** — A malicious actor cannot flood the registry
   with fake listings because each listing requires a valid orchestrator
   identity with a verifiable key pair. Registry operators MAY require
   additional identity verification (domain ownership, organization
   verification) for higher trust tiers.

3. **Price manipulation** — Usage metering is dual-signed by both
   consumer and provider. Neither party can unilaterally alter usage
   records.

4. **Bait-and-switch** — Behavioral fingerprinting detects when a
   provider changes their agent's behavior after establishing trust.
   BREAKING and CRITICAL changes automatically trigger consumer
   notifications and potential suspension.

5. **Data harvesting** — Data contracts are enforced by the consumer's
   own orchestrator before any data crosses the boundary. A malicious
   provider cannot request more data than the contract permits because
   the data is stripped before it leaves.

6. **Supply chain attacks** — If a provider's orchestrator is
   compromised, the behavioral change detection layer flags anomalies.
   Key rotation requires dual-signature proof. Emergency revocation
   enables immediate disconnection.

## Verification Checklist

- [ ] Listings are signed by provider's Ed25519 key
- [ ] Registry verifies listing signatures before indexing
- [ ] Consumer can search by domain, action, tier, jurisdiction
- [ ] Free tier uses the same security model as pro tier
- [ ] Usage metering is dual-signed (consumer + provider)
- [ ] Onboarding requires explicit data contract review
- [ ] BREAKING changes require 30-day deprecation window
- [ ] CRITICAL changes trigger immediate listing suspension
- [ ] Consumers can pin to a specific capability version
- [ ] Emergency revocation purges all cross-boundary data
- [ ] Registry never handles actual task data
- [ ] Multiple registries can federate for redundancy
- [ ] Listing removes respect deprecation window for active consumers
