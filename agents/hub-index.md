<!-- blueprint
type: agent
kind: infrastructure
name: hub-index
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, protocol/federation, architecture/agent, architecture/hub]
platform: any
tier: free
port: 9770
-->

# Hub Index Agent

Crawls, indexes, and maintains the catalog of published capability
listings across the hub network. This agent is the data backbone of
the registry role — it discovers providers, fetches their listings,
verifies signatures, and maintains a searchable index.

## Overview

When a hub operates in the registry role, it needs to know what
capabilities exist across the network. The hub-index agent handles
this by:

1. Accepting listing publications from provider hubs
2. Periodically re-crawling known providers for updates
3. Verifying Ed25519 signatures on every listing
4. Maintaining a searchable index of all verified listings
5. Pruning expired, delisted, or unresponsive listings

The index agent does NOT handle search queries (that's the hub-search
agent) or metrics collection (that's the hub-metrics agent). It
maintains the raw, verified data that other hub agents consume.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["listing_index", "provider_registry"]},
    {"name": "database:write", "resources": ["listing_index", "provider_registry"]},
    {"name": "crypto:verify", "resources": ["ed25519"]}
  ],
  "inputs": [
    {"name": "listing_entry", "type": "json", "description": "Published listing from a provider hub"},
    {"name": "crawl_request", "type": "json", "description": "On-demand crawl of a specific provider"}
  ],
  "outputs": [
    {"name": "index_status", "type": "json", "description": "Indexing result with verification status"}
  ],
  "collaborators": ["hub-verify", "hub-alert"]
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

  - blueprint: protocol/federation
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /contracts
          methods: [GET]
          description: Fetch all listings from a provider hub
        - path: /listing
          methods: [POST, DELETE]
          description: Publish or delist a capability
      types:
        - name: FederatedListing
          fields_used: [listing_id, provider, capability, signature, public_key]
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
          fields_used: [listing_id, provider, capability, tier, metrics, signature]
        - name: ProviderInfo
          fields_used: [hub_name, federation_url, public_key, last_seen]
      events:
        - topic: hub.listing.publish
          fields_used: [listing_id, provider, listing_data]
        - topic: hub.listing.delist
          fields_used: [listing_id, provider]
        - topic: hub.provider.register
          fields_used: [hub_name, federation_url, public_key]
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
          parameters: [engine, tables, indexes, relationships]
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
  # Hub-index operates independently. It notifies hub-verify and
  # hub-alert but does not degrade if they are unavailable.
```

---

## Configuration

```yaml
config:
  crawl_interval:
    type: string
    default: "0 */6 * * *"
    env: WL_HUB_INDEX_CRAWL_INTERVAL
    description: Cron expression for full provider re-crawl schedule

  crawl_timeout:
    type: int
    default: 60
    env: WL_HUB_INDEX_CRAWL_TIMEOUT
    min: 10
    max: 300
    unit: seconds
    description: Per-provider crawl timeout

  max_concurrent_crawls:
    type: int
    default: 5
    env: WL_HUB_INDEX_MAX_CRAWLS
    min: 1
    max: 50
    description: Maximum simultaneous provider crawls

  stale_threshold:
    type: int
    default: 259200
    env: WL_HUB_INDEX_STALE_THRESHOLD
    min: 3600
    unit: seconds
    description: Mark listings stale after provider unreachable for this duration (default 72h)

  stale_grace_period:
    type: int
    default: 604800
    env: WL_HUB_INDEX_STALE_GRACE
    min: 86400
    unit: seconds
    description: Remove stale listings from active index after this grace period (default 7d)

  listing_refresh_max_age:
    type: int
    default: 2592000
    env: WL_HUB_INDEX_REFRESH_MAX_AGE
    min: 86400
    unit: seconds
    description: Mark listing stale if not refreshed within this period (default 30d)

  miss_count_threshold:
    type: int
    default: 3
    env: WL_HUB_INDEX_MISS_THRESHOLD
    min: 1
    max: 10
    description: Consecutive crawl misses before marking provider listings stale

  max_listings:
    type: int
    default: 100000
    env: WL_HUB_INDEX_MAX_LISTINGS
    min: 1000
    description: Maximum active listings in index
```

---

## Types

```yaml
types:
  IndexedListing:
    description: A verified and indexed capability listing
    fields:
      listing_id:
        type: string
        description: Unique listing identifier (provider:capability format)
      provider:
        type: string
        description: Provider hub name
      capability:
        type: object
        description: Capability definition (domain, action, version)
      tier:
        type: string
        enum: [free, pro]
        description: Availability tier
      version:
        type: string
        format: semver
        description: Listing version
      signature:
        type: string
        description: Ed25519 signature over listing content
      public_key:
        type: string
        description: Provider's public key used for signature
      status:
        type: string
        enum: [active, stale, archived, delisted]
        description: Current listing status
      indexed_at:
        type: int64
        auto: true
        description: When listing was indexed
      last_verified:
        type: int64
        description: Last successful signature verification
      last_refreshed:
        type: int64
        description: Last time listing was seen in a crawl
    constraints:
      - name: uq_listing_id
        type: unique
        fields: [listing_id]
        description: Listing IDs are globally unique

  ProviderRecord:
    description: Known provider hub in the network
    fields:
      hub_name:
        type: string
        description: Provider hub identifier
      federation_url:
        type: string
        description: Provider's federation endpoint
      public_key:
        type: string
        description: Provider's current Ed25519 public key
      last_seen:
        type: int64
        description: Last successful contact timestamp
      miss_count:
        type: int
        default: 0
        description: Consecutive failed crawl attempts
      listing_count:
        type: int
        default: 0
        description: Number of active listings from this provider
      registered_at:
        type: int64
        auto: true
        description: When provider was first discovered
    constraints:
      - name: uq_hub_name
        type: unique
        fields: [hub_name]
        description: Hub names are unique

  CrawlResult:
    description: Result of a single provider crawl attempt
    fields:
      crawl_id:
        type: string
        format: uuid-v7
        description: Unique crawl identifier
      hub_name:
        type: string
        references: ProviderRecord.hub_name
        description: Provider crawled
      started_at:
        type: int64
        description: Crawl start timestamp
      completed_at:
        type: int64
        optional: true
        description: Crawl completion timestamp
      status:
        type: string
        enum: [success, timeout, error, partial]
        description: Crawl outcome
      listings_found:
        type: int
        default: 0
        description: Number of listings returned
      listings_indexed:
        type: int
        default: 0
        description: Number of listings successfully indexed
      listings_rejected:
        type: int
        default: 0
        description: Number of listings that failed verification
      error:
        type: text
        optional: true
        description: Error message if crawl failed
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
        trigger: index_loaded
        validates: listing index readable, subscriptions active
      - from: active
        to: indexing
        trigger: crawl_started
        validates: crawl lock acquired
      - from: indexing
        to: active
        trigger: crawl_complete
        validates: all providers processed
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
        validates: signal received (SIGTERM, system.shutdown, or API)
      - from: indexing
        to: retiring
        trigger: shutdown_signal
        validates: signal received — drain current crawl
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in-flight crawls finished or timed out

  entity.IndexedListing:
    initial: active
    transitions:
      - from: active
        to: stale
        trigger: provider_unreachable
        validates: miss_count >= config.miss_count_threshold OR listing_age > config.listing_refresh_max_age
      - from: stale
        to: active
        trigger: provider_returned
        validates: listing re-verified with valid signature
      - from: stale
        to: archived
        trigger: grace_period_expired
        validates: stale for > config.stale_grace_period
      - from: active
        to: delisted
        trigger: delist_received
        validates: delist event from listing provider
      - from: active
        to: active
        trigger: version_update
        validates: new version > current version, signature valid
        side_effect: preserve version history
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
  Action:      Load Ed25519 keypair from .weblisk/keys/hub-index/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema against Types
  Validates:   All tables exist, columns match type definitions, indexes present
  On Fail:     Run migration → if fails EXIT with STORAGE_UNREACHABLE

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 5 — Subscribe to Events
  Action:      Subscribe to hub.listing.publish, hub.listing.delist,
               hub.provider.register, system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED

Step 6 — Load Index Statistics
  Action:      Count active listings and known providers
  Validates:   Query succeeds
  On Fail:     Enter degraded state — index may be stale

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9770, listings: N, providers: M}
```

### Shutdown Sequence

```
Step 1 — Stop Accepting Publish Events
  Action:      Unsubscribe from listing topics
  agent_state → retiring

Step 2 — Drain In-Flight Crawls
  Action:      Wait for active crawls to complete (up to 60s)
  On Timeout:  Record partial crawl results

Step 3 — Deregister
  Action:      DELETE /v1/register

Step 4 — Close Storage
  Action:      Close database connection

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, crawls_drained}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - storage connected
      - event subscriptions active
      - last crawl completed within 2x crawl_interval
    response:
      status: healthy
      details: {storage, listings_total, providers_total, stale_listings,
                last_crawl, subscriptions}

  degraded:
    conditions:
      - storage errors (retrying)
      - last crawl failed
      - stale listings > 20% of total
    response:
      status: degraded
      details: {reason, stale_count, last_error}

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
Step 3 — Pause crawls and indexing → run migration → resume
Step 4 — Reload configuration
Log: lifecycle.version_updated {from, to}
```

---

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.listing.publish` | Provider submits a new or updated listing |
| Event: `hub.listing.delist` | Provider removes a listing |
| Schedule: `0 */6 * * *` | Every 6 hours — re-crawl all known providers |
| Event: `hub.provider.register` | New provider hub discovered |

---

## Actions

### index-listing

Index a published listing after signature verification.

**Source:** Provider Hub

**Input:** `{listing_id: string, provider: string, capability: object, tier: string, version: string, signature: string, public_key: string}`

**Processing:**

```
1. Verify Ed25519 signature over listing content
   If verification fails → reject, log, notify hub-alert
2. Validate listing schema — required fields present, version is valid semver
3. Check for duplicates:
   If listing_id exists with same version → update timestamps
   If listing_id exists with different version → version update flow
   If new → insert
4. Write to listing_index store
5. Update provider_registry with last_seen timestamp
6. Notify hub-search: index updated (cache invalidation)
7. Notify hub-metrics: new listing to track
```

**Output:** `{listing_id: string, status: "indexed" | "updated" | "rejected", reason?: string}`

**Errors:** `SIGNATURE_INVALID` (permanent), `SCHEMA_INVALID` (permanent), `STORAGE_ERROR` (transient)

---

### remove-listing

Remove a delisted capability.

**Source:** Provider Hub

**Input:** `{listing_id: string, provider: string}`

**Processing:**

```
1. Verify requester is the listing's provider
2. Update listing status → delisted
3. Notify hub-search: index updated
```

**Output:** `{listing_id: string, removed: true}`

---

### crawl-provider

Fetch all listings from a specific provider.

**Source:** Admin / Cron

**Input:** `{hub_name: string}`

**Processing:**

```
1. Look up provider in provider_registry
2. GET {federation_url}/contracts with registry bearer token
3. For each listing in response → index-listing flow
4. Mark missing listings as delisted (48h grace period)
5. Update provider last_seen and miss_count
6. Record CrawlResult
```

**Output:** `{hub_name: string, listings_found: int, listings_indexed: int, listings_rejected: int}`

---

### crawl-all

Re-crawl all known providers.

**Source:** Cron

**Input:** `{}`

**Processing:**

```
1. SELECT all providers from provider_registry
2. For each provider (up to config.max_concurrent_crawls in parallel):
   crawl-provider flow
3. After all crawls: run stale listing evaluation
```

**Output:** `{providers_crawled: int, total_listings_indexed: int}`

---

### get-listing

Retrieve a specific listing by ID.

**Source:** Hub Search / Admin

**Input:** `{listing_id: string}`

**Output:** `{listing: IndexedListing}`

**Side Effects:** None (read-only).

---

### get-listings-by-provider

All listings from a provider.

**Source:** Hub Search / Admin

**Input:** `{hub_name: string, status?: string}`

**Output:** `{listings: IndexedListing[], total: int}`

---

### get-index-stats

Index size, provider count, last crawl time.

**Source:** Admin

**Input:** `{}`

**Output:** `{total_listings: int, total_providers: int, stale_listings: int, last_crawl: int64}`

---

### prune-stale

Remove listings from unresponsive providers.

**Source:** Cron

**Input:** `{}`

**Processing:**

```
1. Query stale listings past grace period
2. Move to archive, remove from active index
3. Notify hub-search of index changes
```

**Output:** `{pruned: int}`

---

### reindex

Force full reindex of all providers.

**Source:** Admin

**Input:** `{}`

**Output:** `{providers_reindexed: int, listings_reindexed: int}`

**Side Effects:** Triggers crawl-all with forced re-verification.

---

## Indexing Flow

```
1. RECEIVE listing (via publish event or crawl)
2. VERIFY signature
   - Extract provider's public_key from listing
   - Verify Ed25519 signature over listing content
   - If verification fails → reject, log, notify hub-alert
3. VALIDATE listing schema
   - Required fields present (listing_id, provider, capability, tier)
   - Version is valid semver
   - Data contract referenced exists
4. CHECK for duplicates
   - If listing_id already exists with same version → update
   - If listing_id exists with different version → version update flow
5. STORE in index
   - Write to listing_index store
   - Update provider_registry with last_seen timestamp
6. NOTIFY dependents
   - hub-search agent: index updated (for cache invalidation)
   - hub-metrics agent: new listing to track
```

---

## Crawl Protocol

When crawling a provider, the index agent uses the federation endpoint:

```
GET {provider.federation_url}/contracts
Authorization: Bearer {registry_wlt_token}
```

The response includes all capabilities the provider publishes. Each
listing is individually signature-verified before indexing.

### Crawl Behavior

| Scenario | Action |
|----------|--------|
| Provider responds with updated listings | Update index entries |
| Provider responds with fewer listings | Mark missing as delisted (grace period: 48h) |
| Provider unreachable | Increment miss_count. After 3 consecutive misses, mark all listings stale |
| Provider key changed | Re-verify all listings with new key. Flag for hub-verify review |

---

## Stale Listing Rules

| Condition | Action |
|-----------|--------|
| Provider unreachable for 72+ hours | Mark all listings stale |
| Listing not refreshed in 30+ days | Mark listing stale |
| Stale for 7+ days after marking | Remove from active index, move to archive |
| Provider returns after stale | Re-verify and restore listings |

---

## Execute Workflow

The core indexing processing loop:

```
Phase 1 — Event Intake
  Accept listing publish/delist events from bus
  Accept crawl triggers from cron or admin
  Validate event payload against expected schema

Phase 2 — Signature Verification
  For each listing:
    Extract provider public_key
    Reconstruct canonical listing bytes (deterministic serialization)
    Verify Ed25519 signature
    If invalid → reject, emit hub.verification.failure event

Phase 3 — Schema Validation
  Validate required fields: listing_id, provider, capability, tier, version
  Validate version format (semver)
  Validate capability structure

Phase 4 — Deduplication and Versioning
  Query listing_index for existing listing_id
  If exists with same version → update timestamps only
  If exists with older version → replace, preserve history
  If new → insert new IndexedListing

Phase 5 — Store and Index
  Write to listing_index table
  Update provider_registry (last_seen, listing_count)
  Record CrawlResult if part of a crawl operation

Phase 6 — Notify Dependents
  Emit hub.index.updated event (hub-search cache invalidation)
  Emit hub.listing.indexed event (hub-metrics tracking)
  If verification failed → emit hub.verification.failure (hub-alert)

Phase 7 — Stale Evaluation (periodic)
  Query providers with miss_count >= threshold
  Mark their listings stale
  Query stale listings past grace period → archive
  Emit metrics: stale_listings gauge
```

---

## Collaboration

```yaml
events_published:
  - topic: hub.index.updated
    payload: {listing_id, operation, provider}
    when: Index entry added, updated, or removed

  - topic: hub.listing.indexed
    payload: {listing_id, provider, capability, version}
    when: New listing successfully indexed

  - topic: hub.verification.failure
    payload: {listing_id, provider, reason}
    when: Signature verification failed during indexing

  - topic: hub.provider.stale
    payload: {hub_name, miss_count, last_seen}
    when: Provider marked as stale

events_subscribed:
  - topic: hub.listing.publish
    payload: {listing_id, provider, listing_data}
    action: index-listing

  - topic: hub.listing.delist
    payload: {listing_id, provider}
    action: remove-listing

  - topic: hub.provider.register
    payload: {hub_name, federation_url, public_key}
    action: Register new provider, trigger initial crawl

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "hub-index"
    action: Self-update procedure

direct_messages:
  - target: hub-verify
    action: verify-listing
    when: Delegating complex verification (key rotation, identity checks)
    reason: Hub-index does basic signature checks; hub-verify handles edge cases

  - target: hub-alert
    action: notify-verification-failure
    when: Signature verification fails
    reason: Alert operator and affected collaborators
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Crawling, indexing, and pruning are fully autonomous
  supervised:    Reindex and bulk operations require operator
  manual-only:   All indexing requires operator trigger

overridable_behaviors:
  - behavior: automatic_crawling
    default: enabled
    override: Set WL_HUB_INDEX_CRAWL_ENABLED=false
    audit: logged

  - behavior: automatic_pruning
    default: enabled
    override: Set stale_grace_period to very high value
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: reindex
    description: Force full reindex of all providers
    allowed: operator

  - action: crawl-provider
    description: Trigger on-demand crawl of specific provider
    allowed: operator

  - action: prune-stale
    description: Force stale listing cleanup
    allowed: operator

  - action: restore-listing
    description: Restore an archived listing
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
    - MUST NOT modify provider hub data — index is read-only mirror
    - MUST NOT accept listings without valid Ed25519 signature
    - Crawl rate bounded by config.max_concurrent_crawls

  forbidden_actions:
    - MUST NOT index unsigned or unverified listings
    - MUST NOT bypass signature verification for any reason
    - MUST NOT expose provider private keys or internal endpoints
    - MUST NOT delete listings without delist event or stale expiry

  resource_limits:
    memory: 512 MB (process limit)
    listing_index_rows: config.max_listings
    concurrent_crawls: config.max_concurrent_crawls
    crawl_timeout_per_provider: config.crawl_timeout
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Signature verification failure | Reject listing. Log with provider details. Notify hub-alert. |
| Invalid listing schema | Reject with validation errors. Do not index. |
| Storage unavailable | Queue indexing operations in memory. Flush when storage recovers. |
| Crawl timeout | Log timeout. Retry on next scheduled crawl. |
| Duplicate listing conflict | Latest timestamp wins. Preserve version history. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_index_listings_total | gauge | Total active listings in index |
| hub_index_providers_total | gauge | Total known providers |
| hub_index_operations_total | counter | Index operations by type (add, update, remove, prune) |
| hub_index_crawl_duration_seconds | histogram | Time to crawl a provider |
| hub_index_verification_failures_total | counter | Signature verification failures |
| hub_index_stale_listings | gauge | Currently stale listings |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send messages to hub-verify, hub-alert, hub-search

    - capability: http:send
      resources: ["https://*"]
      description: Crawl provider federation endpoints

    - capability: database:read
      resources: [listing_index, provider_registry]
      description: Read index and provider data

    - capability: database:write
      resources: [listing_index, provider_registry]
      description: Write index entries and provider records

    - capability: crypto:verify
      resources: [ed25519]
      description: Verify listing and manifest signatures

  data_sensitivity:
    - data: Listing content
      classification: low
      handling: Public data — listings are meant to be discoverable

    - data: Provider public keys
      classification: low
      handling: Public keys are shared openly per federation protocol

    - data: Provider federation URLs
      classification: medium
      handling: Internal routing — not exposed to end users

    - data: Crawl authentication tokens
      classification: high
      handling: Registry bearer tokens — never logged, rotated regularly

  access_control:
    - caller: Provider hub (authenticated via federation)
      actions: [index-listing, remove-listing]

    - caller: hub-search
      actions: [get-listing, get-listings-by-provider]

    - caller: Cron agent
      actions: [crawl-all, prune-stale]

    - caller: Operator (auth token with operator role)
      actions: [crawl-provider, crawl-all, reindex, prune-stale,
                get-index-stats, restore-listing]

    - caller: Unauthenticated
      actions: []
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Index a valid listing
    action: index-listing
    input:
      listing_id: "avaropoint:seo-audit"
      provider: "avaropoint-prod"
      capability: {domain: "seo", action: "audit", version: "1.2.0"}
      tier: pro
      version: "1.2.0"
      signature: "<valid-ed25519-signature>"
      public_key: "<provider-public-key>"
    expected:
      listing_id: "avaropoint:seo-audit"
      status: indexed
    validates:
      - IndexedListing created in listing_index
      - hub.index.updated event emitted
      - Provider last_seen updated

  - name: Crawl a provider
    action: crawl-provider
    input: {hub_name: "partner-hub"}
    expected:
      listings_found: 5
      listings_indexed: 5
      listings_rejected: 0
    validates:
      - All provider listings indexed
      - CrawlResult recorded with status = success
```

### Error Cases

```yaml
  - name: Invalid signature rejected
    action: index-listing
    input:
      listing_id: "bad:listing"
      signature: "<invalid-signature>"
    expected_error: SIGNATURE_INVALID
    validates:
      - Listing NOT added to index
      - hub.verification.failure event emitted

  - name: Malformed listing schema
    action: index-listing
    input: {listing_id: "no-capability"}
    expected_error: SCHEMA_INVALID
    validates: Listing rejected with validation details
```

### Edge Cases

```yaml
  - name: Version update preserves history
    action: index-listing
    input: {listing_id: "existing:cap", version: "2.0.0", signature: "<valid>"}
    expected: {status: updated}
    validates: Previous version preserved, new version active

  - name: Stale provider recovery
    condition: Provider unreachable for 72h then returns
    expected: All listings re-verified and restored to active
    validates: Stale → active transition, miss_count reset

  - name: Crawl discovers delisted capability
    action: crawl-provider
    condition: Provider returns fewer listings than indexed
    expected: Missing listings marked delisted with 48h grace
    validates: Grace period before permanent removal
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
      mechanism: crawl lock in storage
      leader: [crawl-all, prune-stale, stale evaluation]
      follower: [index-listing, get-listing, health reporting]
      promotion: automatic when crawl lock expires
    state_sharing:
      mechanism: shared sqlite database
      conflict_resolution: >
        Listing uq_listing_id constraint prevents duplicates.
        Crawl lock prevents simultaneous full crawls.
        Individual listing operations are idempotent.

  event_handling:
    consumer_group: hub-index
    delivery: one-per-group
    description: >
      Bus delivers each publish/delist event to ONE instance in
      the hub-index consumer group.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 10
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share listing_index database. Schema migrations
      are additive-only during shadow phase.
```

---

## Implementation Notes

- **Signature-first**: Every listing MUST pass Ed25519 verification
  before indexing. No exceptions, no override. This is the core trust
  property of the hub network.
- **Crawl vs push**: Listings arrive via push (hub.listing.publish
  events) and pull (scheduled crawls). Both paths converge on the
  same verification and indexing logic.
- **Stale grace periods**: Providers go offline temporarily. The
  72-hour unreachable threshold and 7-day archive grace period
  prevent premature removal of valid listings.
- **Version history**: When a listing version changes, the previous
  version is preserved in an archive table. This supports behavioral
  change detection by hub-verify.
- **Idempotency**: Re-indexing the same listing+version updates
  timestamps only. The uq_listing_id constraint prevents duplicates.
- **Crawl concurrency**: `config.max_concurrent_crawls` prevents
  overwhelming provider hubs. Crawls are staggered across the
  6-hour interval.

---

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Listings are signature-verified before indexing
- [ ] Invalid signatures are rejected and logged
- [ ] Crawl discovers and indexes all provider listings
- [ ] Stale listings are pruned after grace period
- [ ] Index stats are accurate (listing count, provider count)
- [ ] Duplicate listings are handled by version/timestamp
- [ ] Provider key rotation triggers re-verification
- [ ] Index operations emit metrics
- [ ] Crawl failures do not corrupt existing index entries
- [ ] Delisted capabilities are removed from active index
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] State machine validates listing status transitions
- [ ] Startup sequence gates each step with pre-check/validates/on-fail
- [ ] Shutdown drains in-flight crawls before exit
- [ ] Configuration values validated against declared constraints
- [ ] Override audit records who, what, when, why
- [ ] Scaling: crawl lock prevents duplicate full crawls
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Blue-green: shadow phase validates events without side effects
