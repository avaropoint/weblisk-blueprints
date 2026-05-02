<!-- blueprint
type: architecture
name: hub
version: 1.0.0
requires: [protocol/federation, protocol/identity, protocol/types, architecture/agent, architecture/gateway]
platform: any
tier: free
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

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/federation
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: OrchestratorManifest
          fields_used: [name, federation_url, public_key, published_capabilities]
        - name: DataContract
          fields_used: [inbound, outbound, forbidden, jurisdiction, retention]
        - name: BehavioralFingerprint
          fields_used: [hash, change_level, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519KeyPair
          fields_used: [public_key, sign, verify]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, capabilities, version]
        - name: ErrorResponse
          fields_used: [error, code]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentEndpoints
          fields_used: [execute, message, describe, health]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RouteTable
          fields_used: [routes, islands]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

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

A registry is itself a Weblisk hub — an orchestrator with a specialized
hub infrastructure agent that handles indexing, discovery, verification,
metrics, alerting, and marketplace operations:

| Subsystem | Agent Blueprint | Role |
|-----------|----------------|------|
| **Indexing** | [hub](../agents/hub.md) | Crawls and indexes hub manifests from known providers |
| **Search** | [hub](../agents/hub.md) | Handles discovery queries with ranking and filtering |
| **Metrics** | [hub](../agents/hub.md) | Collects and aggregates uptime, latency, and usage metrics |
| **Verification** | [hub](../agents/hub.md) | Validates hub identity, signatures, and behavioral integrity |
| **Alerting** | [hub](../agents/hub.md) | Monitors behavioral changes and notifies affected collaborators |

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
| `/v1/hub/marketplace/listings` | GET | public | Browse marketplace listings |
| `/v1/hub/marketplace/listing/{id}` | GET | public | Marketplace listing detail page data |
| `/v1/hub/marketplace/purchase` | POST | hub-auth | Initiate a marketplace purchase |
| `/v1/hub/marketplace/reviews/{id}` | GET | public | Verified reviews for a listing |
| `/v1/hub/marketplace/reviews` | POST | peer-auth | Submit a verified review |
| `/v1/hub/marketplace/seller/dashboard` | GET | hub-auth | Seller analytics and revenue |

---

## Marketplace

The hub is not only a collaboration engine — it is a **marketplace**
where hubs buy, sell, and share capabilities. Every hub can be a
seller, buyer, or both. The marketplace turns the hub network into an
ecosystem where partners, independent developers, and enterprises
monetize domain expertise, agents, blueprints, and templates.

### What Can Be Listed

| Listing Type | Description | Example |
|-------------|-------------|---------|
| **Capability** | A live, invocable agent capability hosted on a provider hub | SEO audit, compliance check, demand forecast |
| **Blueprint** | A domain controller or agent blueprint that buyers can generate into their own hub | Custom e-commerce domain, logistics optimizer |
| **Template** | A pre-configured hub template with domains, agents, and workflows ready to deploy | "SaaS Starter" with auth, billing, analytics domains |
| **Agent** | A standalone work or infrastructure agent blueprint | PDF extractor, translation agent, sentiment analyzer |
| **Data Contract** | A reusable, audited data contract for a specific business function | GDPR-compliant customer data exchange |

### Listing Types

Capabilities are **live services** — the buyer's hub invokes them over
federation. All other listing types are **installable assets** — the
buyer receives blueprint files that generate into their own hub via
the CLI.

```
Live service (capability):
  Buyer hub ──federation──► Provider hub (runs the agent)

Installable asset (blueprint, template, agent):
  Buyer hub ──download──► Blueprint files ──CLI generate──► Buyer's own code
```

This distinction is important: installable assets run **inside the
buyer's hub**, under the buyer's full control. The seller has no
ongoing access. Live capabilities run on the seller's infrastructure,
governed by data contracts and federation rules.

### Marketplace Listing

A marketplace listing extends the capability listing with commerce
and discoverability fields:

```json
{
  "marketplace_id": "mkt-avaropoint-seo-blueprint",
  "listing_type": "blueprint",
  "seller": {
    "hub_name": "avaropoint-prod",
    "public_key": "<hex Ed25519 public key>",
    "verified_seller": true,
    "seller_since": 1704067200
  },
  "product": {
    "name": "SEO Domain Controller",
    "description": "Production-ready SEO domain with seo-analyzer and a11y-checker agents",
    "category": "website-optimization",
    "tags": ["seo", "accessibility", "content-analysis"],
    "version": "1.2.0",
    "platforms": ["go", "node", "cloudflare"],
    "preview_url": "https://weblisk.dev/marketplace/avaropoint/seo-domain"
  },
  "pricing": {
    "model": "one_time",
    "currency": "USD",
    "price": 49.00,
    "free_tier": false,
    "trial_days": 14
  },
  "stats": {
    "downloads": 1240,
    "active_installations": 890,
    "avg_rating": 4.7,
    "review_count": 156,
    "last_updated": 1712160000
  },
  "support": {
    "documentation_url": "https://docs.avaropoint.com/seo-domain",
    "support_email": "support@avaropoint.com",
    "sla": "business_hours"
  },
  "signature": "<seller's Ed25519 signature over listing>"
}
```

### Pricing Models

| Model | Description | Suited For |
|-------|-------------|------------|
| **free** | No charge — open source or community contribution | Core blueprints, community agents |
| **one_time** | Single payment for permanent access | Blueprints, templates, standalone agents |
| **per_invocation** | Charge per federated task execution | Live capabilities (high-volume, low-cost) |
| **monthly_subscription** | Recurring fee for access | Live capabilities (predictable workloads) |
| **tiered** | Price brackets based on volume | Variable workloads |
| **custom** | Negotiated enterprise pricing | Large partnerships |
| **revenue_share** | Percentage of buyer's revenue from the capability | Co-investment models |

### Verified Reviews

Reviews are tied to actual usage — only hubs that have purchased or
invoked a listing can leave a review. Reviews are signed by the
reviewer's hub key to prevent forgery:

```json
{
  "review_id": "rev-acme-001",
  "marketplace_id": "mkt-avaropoint-seo-blueprint",
  "reviewer": {
    "hub_name": "acme-corp",
    "public_key": "<reviewer's Ed25519 key>"
  },
  "rating": 5,
  "title": "Production-ready out of the box",
  "body": "Generated into our Go hub in under 5 minutes. Scoring model is well-designed.",
  "verified_purchase": true,
  "usage_duration_days": 45,
  "timestamp": 1712160000,
  "signature": "<reviewer's Ed25519 signature>"
}
```

### Seller Dashboard

Sellers access analytics through the admin API:

- Revenue by listing, time period, and buyer geography
- Download and installation counts
- Active usage metrics (for live capabilities)
- Review summary and trends
- Payout history and pending settlements

### Purchase Flow

```
1. DISCOVER
   Buyer finds listing via hub search, marketplace UI, or CLI.

2. EVALUATE
   Buyer reviews:
     - Product description, version, platform support
     - Verified metrics (uptime, latency, rating, reviews)
     - Data contract (for live capabilities)
     - Pricing and trial availability

3. PURCHASE
   Buyer's hub sends purchase request:
     POST /v1/hub/marketplace/purchase
     {
       "marketplace_id": "mkt-avaropoint-seo-blueprint",
       "buyer_hub": "acme-corp",
       "accepted_terms": true,
       "signature": "<buyer's Ed25519 signature>"
     }

4. FULFILL
   For installable assets:
     - Seller's hub provides download URL (time-limited, signed)
     - Buyer downloads blueprint files
     - Buyer generates into their hub: weblisk domain create seo --from marketplace
   
   For live capabilities:
     - Federation peering flow initiates automatically
     - Data contract review and acceptance
     - Capability becomes available in buyer's workflow

5. VERIFY
   Purchase recorded on both hubs (dual-signed receipt).
   Buyer can leave a verified review after 24 hours of use.
```

### Ecosystem Building

The marketplace enables hub operators to build ecosystems:

| Strategy | Description |
|----------|-------------|
| **Partner network** | Hub publishes curated capabilities and invites partners to list complementary services |
| **Vertical marketplace** | Industry-specific registry (healthcare, logistics, finance) with domain-appropriate listings |
| **Developer community** | Open listing submission with review/approval process for quality control |
| **Enterprise catalog** | Private marketplace within an organization — internal teams publish and consume capabilities |
| **White-label** | Hub operator runs marketplace under their own brand, powered by the hub protocol |

A hub can operate a private marketplace (visible only to peered hubs),
a public marketplace (listed on weblisk.dev), or both.

### weblisk.dev Public Directory

[weblisk.dev](https://weblisk.dev) serves as the **public directory**
for the hub network. It aggregates listings from registries that opt
into public visibility, providing:

- **Marketplace UI** — Browse, search, and evaluate listings from all
  public registries
- **Hub directory** — Discover hubs by industry, capability, or
  geography
- **Provider profiles** — Verified seller pages with metrics, listings,
  and reviews
- **Blueprint catalog** — All open-source blueprints from this
  repository, plus community-contributed blueprints
- **Agent catalog** — Browsable catalog of available agents (free and
  pro)

weblisk.dev is itself a Weblisk hub running the registry role. It
indexes listings from participating registries via standard federation,
applying the same verification, behavioral fingerprinting, and trust
rules as any other hub.

**Public vs Private:**

| Visibility | Discovery | Listed on weblisk.dev | Access |
|-----------|-----------|----------------------|--------|
| Public | Anyone can find via search | Yes | Open or gated (free/paid) |
| Partner | Visible to peered hubs only | No | Requires peering relationship |
| Private | Visible within organization only | No | Internal hub network only |

Hubs choose their visibility per listing. A hub can publish some
capabilities publicly (to attract new partners) while keeping others
private (internal tools) or partner-only (premium services).

### Marketplace Operations

The marketplace is not a separate system — it is orchestrated by the
hub's existing infrastructure agents. Every marketplace operation maps
to a sequence of agent messages coordinated by the orchestrator.

#### Hub Agent Subsystem Roles in Marketplace Operations

| Operation | Subsystems Involved | Flow |
|-----------|---------------------|------|
| **Publish listing** | verify → index → alert | Seller's hub signs listing → hub agent verifies identity and signature → indexes listing → notifies subscribed searchers |
| **Purchase (live capability)** | search → verify → federation → metrics → alert | Buyer discovers → hub agent verifies both parties → federation peering initiated → metrics collection begins → collaborators notified |
| **Purchase (installable asset)** | search → verify → alert | Buyer discovers → hub agent verifies seller and asset signature → download URL issued → buyer notified of fulfillment |
| **Leave review** | verify → index → alert | Hub agent verifies purchase proof → review indexed → seller notified |
| **Behavioral change detected** | metrics → verify → alert | Metrics probe detects anomaly → verify classifies change → alert notifies all affected collaborators |
| **Delist** | index → alert → metrics | Listing marked for deprecation → collaborators notified → metrics archived |

#### Publish Flow (Seller Side)

When a hub operator publishes a capability or asset to the marketplace:

```
Seller Hub                           Registry Hub
─────────                           ────────────
1. Operator runs:
   weblisk marketplace publish
   --type capability
   --name "demand-forecast"
   --pricing per_invocation
   --price 0.02

2. Seller's orchestrator:
   a. Builds marketplace listing JSON
   b. Signs listing with hub's Ed25519 key
   c. POST /v1/hub/publish ──────────► 3. Registry orchestrator:
                                          a. Hub agent verification
                                             → verify-listing (signature check)
                                             → verify-identity (hub identity check)
                                          b. If verified, hub agent indexing
                                             → index-listing (adds to catalog)
                                          c. Hub agent alerting
                                             → notify-marketplace-event
                                               (new listing notification)
                                       ◄── 4. Returns listing ID and status

5. Seller's hub stores listing
   reference for management
```

#### Purchase Flow (Live Capability)

When a hub wants to consume a live capability from another hub:

```
Buyer Hub                Registry Hub              Seller Hub
─────────                ────────────              ──────────
1. Search/browse:
   GET /v1/hub/search ──► 2. Hub agent search returns
                             ranked results
                          ◄──

3. Evaluate listing:
   GET /v1/hub/listing/{id} ► 4. Hub agent index returns
                                 listing + metrics
                               ◄──

5. Review data contract:
   GET /v1/hub/contracts/{name} ► 6. Returns contract
                                     definition
                                   ◄──

7. Operator approves:
   weblisk marketplace buy mkt-xxx
   --accept-contract
   --accept-pricing

8. Purchase request:
   POST /v1/hub/marketplace ─► 9. Registry orchestrator:
   /purchase                      a. Hub agent verify: verify buyer
                                     identity and signature
                                  b. Hub agent verify: verify seller
                                     is still active
                                  c. Generate dual-signed
                                     purchase receipt
                                  d. Hub agent alert: notify seller
                               ◄── 10. Returns receipt + status

11. Federation peering         ────────────────────► 12. Seller hub receives
    auto-initiates:                                      peering request:
    POST {seller}/v1/peer                                a. Verifies buyer identity
    with purchase receipt                                b. Reviews data contract
    as proof of purchase                                 c. Accepts/rejects peering
                               ◄────────────────────
13. Peering established.
    Buyer can now invoke:
    POST {seller}/v1/execute
    with federated auth

14. Hub agent metrics      ─► 15. Registry records
    begins recording            usage metrics for both
    invocations                 parties
```

#### Purchase Flow (Installable Asset)

When a hub wants to install a blueprint, template, or agent from the marketplace:

```
Buyer Hub                Registry Hub              Seller Hub
─────────                ────────────              ──────────
1-7. Same discovery and
     approval as above

8. Purchase request:
   POST /v1/hub/marketplace ─► 9. Registry orchestrator:
   /purchase                      a. Hub agent verify: verify buyer
                                  b. Generate purchase receipt
                                  c. Request download URL
                                     from seller
                               ──────────────────────► 10. Seller generates:
                                                           a. Time-limited
                                                              signed download URL
                                                           b. Asset signature
                               ◄──────────────────────
                               ◄── 11. Returns receipt
                                       + download URL

12. CLI downloads asset:
    weblisk marketplace install mkt-xxx
    a. Downloads blueprint files
    b. Verifies seller signature
       against registry's verified
       public key
    c. Verifies file integrity
       (SHA-256 hash in receipt)

13. CLI generates into hub:
    weblisk domain create forecast
    --from marketplace
    a. Generates domain controller
    b. Generates agent stubs
    c. Registers with orchestrator

14. Asset runs LOCALLY in
    buyer's hub. Seller has
    no ongoing access.
```

#### Collaboration Lifecycle

Once two hubs are peered (via marketplace purchase or direct federation),
the collaboration follows this lifecycle:

```
  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ DISCOVER │────►│ EVALUATE │────►│ ONBOARD  │────►│  ACTIVE  │
  └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                           │
                                                     ┌─────┴─────┐
                                                     │           │
                                                     ▼           ▼
                                               ┌──────────┐ ┌──────────┐
                                               │  RENEW   │ │TERMINATE │
                                               └──────────┘ └──────────┘
```

| Phase | What Happens | Hub Agent Subsystems |
|-------|-------------|----------------------|
| **Discover** | Buyer searches marketplace, browses listings, reads reviews | search, indexing |
| **Evaluate** | Buyer reviews metrics, data contracts, pricing. May request a trial. | metrics, verification |
| **Onboard** | Purchase, federation peering, data contract acceptance, initial capability test | verification, alerting, federation protocol |
| **Active** | Ongoing invocations, usage metering, behavioral monitoring, SLA tracking | metrics, verification, alerting |
| **Renew** | Contract renewal, pricing renegotiation, version upgrades | verification, alerting |
| **Terminate** | Graceful shutdown: deprecation notice → drain active tasks → revoke peering → archive metrics | alerting, indexing, metrics |

#### Termination Protocol

Collaboration termination follows a structured wind-down:

```
1. INITIATE   Either party sends termination notice
              via POST /v1/hub/notify {type: "terminate"}

2. GRACE      30-day grace period (or contract minimum):
              - New tasks are rejected after day 1
              - In-flight tasks complete normally
              - Usage metering continues
              - Buyer should migrate to alternative provider

3. DRAIN      After grace period:
              - All pending tasks are force-completed or failed
              - Final usage report generated (dual-signed)
              - Final invoice/settlement

4. REVOKE     Federation peering revoked:
              - Keys removed from both hub registries
              - Data contracts archived (not deleted — for audit)
              - Buyer's hub removes provider from service directory

5. ARCHIVE    Registry updates:
              - Collaboration marked as terminated
              - Metrics archived but queryable for 2 years
              - Reviews remain visible (with "no longer active" badge)
```

#### CLI Commands for Marketplace

```bash
# Seller operations
weblisk marketplace publish --type capability --config listing.yaml
weblisk marketplace update mkt-xxx --price 0.03
weblisk marketplace delist mkt-xxx --reason "end of life"
weblisk marketplace dashboard                # revenue, downloads, ratings
weblisk marketplace reviews mkt-xxx          # view reviews for your listing

# Buyer operations
weblisk marketplace search "demand forecasting"
weblisk marketplace describe mkt-xxx          # detailed listing + metrics
weblisk marketplace buy mkt-xxx --accept-contract --accept-pricing
weblisk marketplace install mkt-xxx          # download + generate installable asset
weblisk marketplace review mkt-xxx --rating 5 --title "Excellent"
weblisk marketplace list                     # list active purchases

# Collaboration management
weblisk marketplace collaborations           # list all active collaborations
weblisk marketplace usage mkt-xxx            # usage metrics for a collaboration
weblisk marketplace terminate mkt-xxx        # initiate termination protocol
```

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

7. **Marketplace fraud** — Purchase receipts are dual-signed by buyer
   and seller. Verified reviews require proof of purchase. Rating
   manipulation is detectable because reviews are cryptographically
   tied to hub identities. Seller verification (domain ownership,
   organizational identity) is required for paid listings.

8. **Asset tampering** — Installable assets (blueprints, templates,
   agents) are signed by the seller's Ed25519 key. The CLI verifies
   signatures before generation. A tampered asset is cryptographically
   detectable before any code is generated.

## Responsibilities

### Owns
- Capability listing publication, indexing, and signature verification
- Hub-to-hub discovery (registry search and direct peer queries)
- Collaboration lifecycle (peering, trust establishment, monitoring, revocation)
- Usage metering with dual-signed reconciliation
- Behavioral change detection and collaborator notification
- Free vs pro tier enforcement (concurrency, rate limits, SLA)
- Marketplace operations (listings, purchases, reviews, installable assets)

### Does NOT Own
- Federation protocol mechanics (owned by protocol/federation)
- Agent registration or orchestration (owned by architecture/orchestrator)
- Data contract schema definition (owned by protocol/federation)
- Individual agent execution logic (owned by work agents)
- Internal routing of tasks within a deployment (owned by orchestrator + domains)

---

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| `GET /v1/hub/search` | HTTP | Registry search — query by domain, action, tier, jurisdiction |
| `POST /v1/federation/peer` | HTTP | Initiate peering with another hub |
| `GET /v1/federation/contracts` | HTTP | List published data contracts and capabilities |
| `POST /v1/hub/publish` | HTTP | Publish a capability listing to the network |
| `GET /v1/hub/listings` | HTTP | List own published capabilities |
| `POST /v1/marketplace/purchase` | HTTP | Purchase a marketplace listing |
| `GET /v1/marketplace/search` | HTTP | Search marketplace listings |
| `POST /v1/marketplace/review` | HTTP | Submit a verified review |
| System events | Pub/Sub | `hub.peer.connected`, `hub.peer.revoked`, `hub.listing.published` |

---

## Data Flow

1. Provider hub signs and publishes a `ListingEntry` to the registry
2. Consumer hub searches the registry via `GET /v1/hub/search`
3. Consumer reviews listing metadata, data contract, SLA, and pricing
4. Consumer sends peering request via `POST /v1/federation/peer`
5. Provider reviews and approves the peering request
6. Both hubs exchange manifests and public keys — federation link is live
7. Consumer's domain controller includes federated capability in a workflow
8. First federated task executes with full data contract enforcement
9. Both hubs independently meter usage with dual-signed records
10. Ongoing monitoring tracks SLA compliance, behavioral stability, and error rates

---

## Implementation Notes

- Hub federation is opt-in — deployments without federation operate as isolated instances
- Marketplace listings are cryptographically signed; the CLI verifies signatures before code generation
- Usage metering is dual-signed (consumer + provider) to prevent billing disputes
- Behavioral change detection uses fingerprinting — not exact payload comparison
- Free tier enforces lower concurrency and rate limits but uses identical security controls
- Peering trust is directional — hub A trusting hub B does not imply hub B trusts hub A

---

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
- [ ] Marketplace purchases generate dual-signed receipts
- [ ] Verified reviews require proof of purchase and hub identity
- [ ] Installable assets are signature-verified before generation
- [ ] Marketplace endpoints enforce proper authentication (hub-auth, peer-auth)
- [ ] Seller dashboard data is scoped to the authenticated hub
