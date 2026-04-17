<!-- blueprint
type: architecture
name: hub
version: 1.0.0
requires: [protocol/federation, protocol/identity, protocol/types, architecture/agent]
platform: any
-->

# Weblisk Hub

Architecture for the collaborative hub — the federated layer where
orchestrators publish, discover, and consume agent capabilities across
organizational boundaries. Every Weblisk deployment is a hub. Hubs
connect to form a network of interconnected orchestrators, domain
knowledge, and agents that work collaboratively across businesses,
industries, and economies.

The hub operates on top of the federation protocol and inherits all of
its trust, data contract, and sovereignty guarantees.

## Vision

Traditional business integration (EDI, supply chain middleware, B2B
gateways) forces organizations to share data through opaque, brittle
pipelines that no one fully understands or controls. Weblisk replaces
this with **hubs** — self-sovereign nodes where every business owns
its orchestrators, domains, agents, logic, and data. Hubs collaborate
with each other through cryptographically enforced data contracts that
give both parties complete visibility and control over what is
exchanged, how it is used, and when it is deleted.

When every business runs a hub, the result is a global network of
economic intelligence: supply chains, logistics, procurement, finance,
compliance, and every other business function — all interconnected
through agents that understand context, enforce boundaries, and
operate autonomously under human-approved policies.

This is the **Weblisk Hub Network** — a decentralized, AI-ready
infrastructure for the entire business chain.

## Overview

The hub is the collaboration and discovery layer of the federation.
While the federation protocol handles trust and data boundaries, the
hub handles:

- **Discovery** — How do I find agents and capabilities that complement
  my own?
- **Collaboration** — How do my agents work with agents from another
  organization?
- **Commerce** — How do I offer capabilities to the network and how do
  I consume capabilities from others?
- **Intelligence** — How does knowledge flow between hubs without
  leaking proprietary data?

Hubs are federated by design — there is no single central authority.
Any orchestrator is a hub. Discovery relies on a combination of
registry servers (operated by Avaropoint and, in the future, by
partners) and direct peer discovery between hubs.

## Design Principles

1. **Every deployment is a hub** — Running Weblisk makes you a
   participant in the network. You choose what to publish, who to
   collaborate with, and what data contracts to accept. There is no
   opt-in — the architecture is collaborative by default, private by
   default.
2. **Own everything** — Every hub owns its orchestrators, domain
   controllers, agents, logic, data, and policies. No external entity
   can access, modify, or observe any part of a hub without an explicit
   trust relationship and a signed data contract.
3. **Trust is verified, not assumed** — Publishing a capability to the
   network does not grant anyone access. Every collaborator independently
   verifies the other's identity, reviews data contracts, and
   establishes a trust relationship before any data flows.
4. **Transparency over reputation** — Rather than opaque scores, the
   hub surfaces verifiable facts: uptime, response times, behavioral
   change frequency, data contract strictness, and audit logs.
5. **Replace, don't wrap** — The hub is not a wrapper around EDI or
   existing B2B protocols. It replaces them with a native, AI-ready
   model where agents negotiate, execute, and verify business processes
   directly.

---

## Hub Roles

| Role | Description | Examples |
|------|-------------|---------|
| **Provider** | A hub that publishes agent capabilities for others to consume | A logistics company offering shipment tracking to partners |
| **Consumer** | A hub that discovers and invokes capabilities from other hubs | A retailer consuming shipment tracking from a logistics partner |
| **Registry** | A hub that indexes published capabilities and serves discovery queries | Avaropoint's global registry, a regional or vertical registry |

Every hub can be a provider, consumer, and registry simultaneously.
A manufacturing hub might provide inventory intelligence to retail
hubs, consume compliance checking from an audit hub, and operate a
private registry for its supplier network.

---

## Capability Listing

When a hub publishes a capability to the network, the listing includes
verifiable metadata — not marketing text, but cryptographically signed
facts:

### ListingEntry

```json
{
  "listing_id": "avaropoint:seo-audit",
  "provider": {
    "hub_name": "avaropoint-prod",
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
| listing_id | string | yes | `{hub}:{capability}` unique identifier |
| provider | ProviderInfo | yes | Provider hub identity |
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

Both hubs independently track usage for reconciliation:

```json
{
  "period": "2024-04",
  "consumer_hub": "acme-corp",
  "provider_hub": "avaropoint-prod",
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

Hubs search the registry by capability, domain, jurisdiction, and tier.

**GET /v1/hub/search**

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

Without a registry, one hub can query another hub's published
capabilities directly:

**GET /v1/federation/contracts** (from federation protocol)

Returns the data contracts and published capabilities that the target
hub offers to peers at the requester's trust tier.

---

## Collaboration Flow

How a hub starts collaborating with another hub:

```
1. DISCOVER
   Consumer hub searches the registry or queries a provider directly.
   Reviews listing: capability, data contract, SLA, pricing,
   behavioral metrics, jurisdiction.

2. REVIEW DATA CONTRACT
   Consumer downloads the data contract for the capability.
   Reviews:
     - What inbound data is required/permitted
     - What outbound data will be returned
     - What fields are forbidden (what the provider will NEVER receive)
     - Jurisdiction requirements
     - Retention policy
   Legal/compliance team approves the contract.

3. INITIATE PEERING
   Consumer hub sends a peering request to the provider hub
   (POST /v1/federation/peer) with:
     - Consumer's orchestrator manifest
     - Requested capabilities
     - Accepted data contracts
   
4. PROVIDER REVIEW
   Provider hub reviews the request:
     - Consumer's identity (public key)
     - Consumer's jurisdiction (compatible?)
     - Requested capabilities (authorized for consumer's tier?)
   Provider approves or rejects.

5. TRUST ESTABLISHED
   Provider sends peer-accept. Both hubs exchange manifests and
   public keys. Federation link is live.

6. FIRST COLLABORATION
   Consumer's domain controller includes the federated capability in
   its workflow. First federated task executes with full data contract
   enforcement, behavioral verification, and audit logging.

7. ONGOING MONITORING
   Both hubs monitor:
     - Usage against quotas and SLAs
     - Behavioral fingerprint stability
     - Data contract compliance
     - Error rates and latency
```

---

## Behavioral Change in a Hub Network

Behavioral integrity is especially critical across hubs because each
hub relies on capabilities it does not own or control.

### Provider Obligations

When a provider updates an agent that backs a published capability:

1. **Compute behavioral change level** (BENIGN/NOTABLE/BREAKING/CRITICAL)
   per the federation protocol's change detection rules.

2. **For BENIGN changes:** Publish updated metrics. No disruption.

3. **For NOTABLE changes:**
   - Update the hub listing with new version
   - Notify all collaborating hubs via `POST /v1/federation/notify`
   - Allow 7-day parallel running of old + new version

4. **For BREAKING changes:**
   - Publish new listing version alongside old
   - Notify all collaborating hubs with detailed changelog
   - Provide 30-day deprecation window for old version
   - Collaborators must explicitly opt-in to new version

5. **For CRITICAL changes:**
   - Immediately suspend the listing from the hub
   - Notify all collaborators: `BEHAVIORAL_CHANGE_CRITICAL`
   - Require re-approval from all active collaborators
   - Registry flags the listing with a change alert

### Collaborator Protections

- **Version pinning:** Collaborator can pin to a specific version.
  Provider MUST continue serving the pinned version during deprecation.
- **Change notifications:** All changes above BENIGN trigger a
  notification to the collaborator's hub.
- **Automatic suspension:** If a provider's agent triggers a CRITICAL
  behavioral change, the collaborating hub automatically suspends
  federated tasks to that agent until admin review.
- **Audit trail:** Full history of behavioral changes is visible in the
  listing's metrics.

---

## Revocation and Removal

### Collaborator Disconnects

A collaborator can revoke trust at any time:

```
POST /v1/federation/peer-revoke
```

- All in-flight federated tasks are allowed to complete (with timeout)
- No new tasks are dispatched
- Metering finalizes at revocation timestamp
- Data retention clock starts on both sides

### Provider Delists

A provider can remove a capability from its hub:

```
POST /v1/hub/delist
```

- All active collaborators notified with 30-day warning
- New peering requests rejected immediately
- Existing collaborators continue for deprecation window
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

A registry is itself a Weblisk hub — an orchestrator with specialized
agents dedicated to indexing and discovery:

| Component | Role |
|-----------|------|
| **Index Agent** | Crawls and indexes hub manifests from known providers |
| **Search Agent** | Handles discovery queries with ranking and filtering |
| **Metrics Agent** | Collects and aggregates uptime, latency, and usage metrics |
| **Verification Agent** | Validates hub identity and manifest signatures |
| **Alert Agent** | Monitors behavioral changes and notifies affected collaborators |

The registry NEVER handles actual federated task data. It only indexes
metadata (listings, metrics, contracts). All data exchange happens
directly between hubs through the federation protocol.

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

Each registry independently verifies hub signatures. A listing
appearing in multiple registries carries the same cryptographic proof
regardless of which registry serves it.

---

## Hub Network Architecture

At scale, the hub network forms a topology analogous to the internet
itself — decentralized, resilient, and self-organizing:

```
                  ┌─────────────────────┐
                  │  Avaropoint Global  │
                  │      Registry       │
                  └────────┬────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │ EU Registry │  │APAC Registry│  │ Healthcare  │
   │  (regional) │  │ (regional)  │  │ (vertical)  │
   └──────┬──────┘  └─────┬──────┘  └──────┬──────┘
          │               │                │
   ┌──────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
   │ Manufacturer│  │  Logistics  │  │  Hospital   │
   │    Hub      │◄─►    Hub     │  │    Hub      │
   └──────┬──────┘  └─────┬──────┘  └─────────────┘
          │               │
   ┌──────▼──────┐  ┌─────▼──────┐
   │  Supplier   │  │  Retailer  │
   │    Hub      │  │    Hub     │
   └─────────────┘  └────────────┘
```

**Key properties of the hub network:**

- **No single point of failure** — If any hub or registry goes offline,
  the remaining network continues. Existing trust relationships are
  peer-to-peer and do not depend on the registry.
- **Organic growth** — New hubs join by peering with existing hubs.
  No central authority approves membership.
- **Domain specialization** — Each hub excels at its own domains. A
  logistics hub has deep supply chain intelligence; a compliance hub
  has regulatory expertise. Collaboration lets every hub access
  capabilities beyond its own specialization.
- **Data stays home** — Each hub processes data within its own
  jurisdiction. Only the minimum required data (per data contracts)
  crosses boundaries, and it is cryptographically controlled at every
  step.

---

## Replacing EDI and Traditional B2B

The hub model directly replaces traditional electronic data interchange
and B2B middleware with a model that is:

| Traditional (EDI/B2B) | Weblisk Hub Network |
|----------------------|---------------------|
| Fixed message formats (X12, EDIFACT) | Flexible data contracts with explicit boundaries |
| Point-to-point VAN connections | Federated mesh with peer discovery |
| Opaque data pipelines | Full audit trail on both sides |
| No behavioral guarantees | Behavioral fingerprinting and change detection |
| Manual integration per partner | Agents negotiate and execute autonomously |
| Data ownership unclear | Data ownership explicit in every contract |
| Months to onboard a partner | Peering flow: discover → review → connect |
| No AI-native processing | Agents understand content, context, and intent |
| Vendor lock-in | Open protocol, self-sovereign hubs |

### Supply Chain Example

A manufacturer, its suppliers, logistics providers, and retailers — each
running their own Weblisk hub:

```
Supplier Hub                   Manufacturer Hub              Retailer Hub
──────────                     ────────────────              ────────────
Domains:                       Domains:                      Domains:
 - inventory                    - procurement                 - catalog
 - quality                      - production                  - fulfillment
                                - logistics                   - analytics

Agents:                        Agents:                       Agents:
 - inventory-tracker            - purchase-order              - catalog-sync
 - quality-inspector            - production-planner          - demand-forecast
 - shipping-prep                - logistics-coordinator       - order-manager

Published capabilities:        Published capabilities:       Published capabilities:
 - inventory:check              - order:status                - demand:forecast
 - quality:certify              - logistics:track             - order:place
```

Each hub publishes what it chooses. Data contracts define exactly what
crosses each boundary. The manufacturer's procurement agent can invoke
the supplier's `inventory:check` without the supplier ever seeing the
manufacturer's production schedule. The retailer's `demand:forecast`
flows to the manufacturer's `production-planner` with only the
minimum required fields — category, quantity range, timeframe — and
nothing that reveals the retailer's pricing strategy or customer data.

---

## Hub Endpoints

Hub-specific endpoints (in addition to federation endpoints):

| Path | Method | Auth | Purpose |
|------|--------|------|---------|
| `/v1/hub/search` | GET | public | Search capability listings across the network |
| `/v1/hub/listing/{id}` | GET | public | Get listing details |
| `/v1/hub/publish` | POST | hub-auth | Publish or update a capability listing |
| `/v1/hub/delist` | POST | hub-auth | Remove a listing |
| `/v1/hub/metrics/{id}` | GET | public | Get listing performance metrics |
| `/v1/hub/contracts/{name}` | GET | public | Download a data contract |
| `/v1/hub/notify` | POST | hub-auth | Send change notification to collaborators |
| `/v1/hub/usage` | GET | peer-auth | Usage metering for billing period |

---

## Security Considerations

The hub layer adds these security concerns beyond the federation
protocol:

1. **Listing integrity** — Listings are signed by the provider hub.
   Registries verify signatures before indexing. Collaborators verify
   signatures before peering. A tampered listing is cryptographically
   detectable.

2. **Sybil resistance** — A malicious actor cannot flood the network
   with fake listings because each listing requires a valid hub
   identity with a verifiable key pair. Registry operators MAY require
   additional identity verification (domain ownership, organization
   verification) for higher trust tiers.

3. **Price manipulation** — Usage metering is dual-signed by both
   hubs. Neither party can unilaterally alter usage records.

4. **Bait-and-switch** — Behavioral fingerprinting detects when a
   provider changes their agent's behavior after establishing trust.
   BREAKING and CRITICAL changes automatically trigger collaborator
   notifications and potential suspension.

5. **Data harvesting** — Data contracts are enforced by the consumer's
   own hub before any data crosses the boundary. A malicious provider
   cannot request more data than the contract permits because the data
   is stripped before it leaves.

6. **Supply chain attacks** — If a provider hub is compromised, the
   behavioral change detection layer flags anomalies. Key rotation
   requires dual-signature proof. Emergency revocation enables immediate
   disconnection.

## Verification Checklist

- [ ] Listings are signed by provider hub's Ed25519 key
- [ ] Registry verifies listing signatures before indexing
- [ ] Hubs can search by domain, action, tier, jurisdiction
- [ ] Free tier uses the same security model as pro tier
- [ ] Usage metering is dual-signed (consumer + provider)
- [ ] Collaboration requires explicit data contract review
- [ ] BREAKING changes require 30-day deprecation window
- [ ] CRITICAL changes trigger immediate listing suspension
- [ ] Collaborators can pin to a specific capability version
- [ ] Emergency revocation purges all cross-boundary data
- [ ] Registry never handles actual task data
- [ ] Multiple registries can federate for redundancy
- [ ] Delisting respects deprecation window for active collaborators
