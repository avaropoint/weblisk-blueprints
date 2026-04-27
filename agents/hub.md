<!-- blueprint
type: agent
kind: infrastructure
name: hub
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, protocol/federation, architecture/hub, architecture/agent, architecture/orchestrator, patterns/messaging, patterns/caching, patterns/observability, patterns/security, patterns/interop]
platform: any
tier: free
port: 9770
-->

# Hub Agent

Unified hub infrastructure agent for the Weblisk hub network.
Handles indexing, search, metrics, verification, and alerting
across the federated catalog of published capability listings.

## Overview

The hub agent is a single infrastructure agent that manages all hub
operations: indexing listings, searching the catalog, collecting
metrics, verifying trust, and alerting on network events. These are
subsystems within one agent, not separate agents. This design
simplifies deployment, reduces inter-process communication, and
ensures all hub operations share a single identity, storage
connection, and event subscription set.

When a hub operates in the registry role, the hub agent provides:

1. **Indexing** — Crawls, indexes, and maintains the catalog of
   published capability listings. Discovers providers, fetches their
   listings, verifies signatures, and maintains a searchable index.

2. **Search** — Full-text search, faceted filtering, relevance
   ranking, and pagination over published capabilities. Supports
   browse-by-category, trending, recommendations, and autocomplete.

3. **Metrics** — Collects and aggregates verifiable performance
   metrics for every listing: uptime, latency, error rates, invocation
   volume, and behavioral change history. Metrics are observed from
   actual usage — never self-reported by providers.

4. **Verification** — Validates Ed25519 signatures on listings and
   manifests, detects behavioral changes via fingerprinting, enforces
   key rotation protocol, and validates data contracts.

5. **Alerting** — Routes hub network event notifications to operators
   and affected collaborators. Handles deduplication, muting, flapping
   detection, and cross-hub federation notifications.

The hub agent has zero external runtime dependencies beyond the
orchestrator and event bus. It communicates exclusively through the
Weblisk messaging bus and federation protocol endpoints.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["listing_index", "provider_registry", "metrics_store", "verification_log", "behavioral_fingerprints", "search_analytics", "alert_rules", "alert_history"]},
    {"name": "database:write", "resources": ["listing_index", "provider_registry", "metrics_store", "verification_log", "behavioral_fingerprints", "search_analytics", "alert_history"]},
    {"name": "crypto:verify", "resources": ["ed25519"]}
  ],
  "inputs": [
    {"name": "listing_entry", "type": "json", "description": "Published listing from a provider hub"},
    {"name": "crawl_request", "type": "json", "description": "On-demand crawl of a specific provider"},
    {"name": "search_query", "type": "json", "description": "Search parameters — filters, sort, pagination"},
    {"name": "task_completion", "type": "json", "description": "Federated task result for metrics recording"},
    {"name": "health_probe", "type": "json", "description": "Availability probe result"},
    {"name": "verification_request", "type": "json", "description": "Item to verify (listing, manifest, behavioral sample)"},
    {"name": "hub_event", "type": "json", "description": "Network event requiring notification"}
  ],
  "outputs": [
    {"name": "index_status", "type": "json", "description": "Indexing result with verification status"},
    {"name": "search_results", "type": "json", "description": "Ranked listing results with facets"},
    {"name": "listing_metrics", "type": "json", "description": "Aggregated metrics for a listing"},
    {"name": "verification_result", "type": "json", "description": "Pass/fail with evidence and classification"},
    {"name": "alert_result", "type": "json", "description": "Notification delivery status"}
  ],
  "collaborators": ["alerting"]
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
        - name: HealthResponse
          fields_used: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519Identity
          fields_used: [public_key, sign, verify]
        - name: KeyRotationAnnouncement
          fields_used: [hub_name, old_key, new_key, old_signature, new_signature, timestamp]
      patterns:
        - behavior: dual-signature-rotation
          parameters: [old_key, new_key, cooldown_period]
        - behavior: key-revocation
          parameters: [revoked_key, reason, revocation_list]
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
        - name: AgentManifest
          fields_used: [name, type, capabilities, version]
        - name: ErrorResponse
          fields_used: [error, code]
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
        - path: /status
          methods: [HEAD]
          description: Availability probe endpoint on provider hubs
      types:
        - name: FederatedListing
          fields_used: [listing_id, provider, capability, signature, public_key]
        - name: FederatedTaskResult
          fields_used: [listing_id, latency_ms, status, data_bytes_in, data_bytes_out]
        - name: DataContract
          fields_used: [inbound_fields, outbound_fields, forbidden_fields,
                        jurisdiction, retention_policy]
        - name: PeerRequest
          fields_used: [manifest, capabilities, data_contracts]
        - name: BehavioralFingerprint
          fields_used: [hash, change_level, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/hub
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ListingEntry
          fields_used: [listing_id, provider, capability, tier, metrics, signature, pricing]
        - name: ProviderInfo
          fields_used: [hub_name, federation_url, public_key, last_seen]
        - name: MetricsInfo
          fields_used: [listing_id, uptime_30d, p95_latency_30d_ms,
                        total_invocations_30d, error_rate_30d,
                        behavioral_changes_90d, data_freshness]
        - name: SearchQuery
          fields_used: [q, domain, action, tier, jurisdiction, min_uptime,
                        max_latency, max_price, sort, page, per_page]
        - name: SearchResult
          fields_used: [results, total, page, per_page, facets]
        - name: BehavioralChange
          fields_used: [listing_id, level, previous_version, new_version, change_summary]
        - name: CollaboratorInfo
          fields_used: [hub_name, federation_url, contact]
      events:
        - topic: hub.listing.publish
          fields_used: [listing_id, provider, listing_data]
        - topic: hub.listing.delist
          fields_used: [listing_id, provider]
        - topic: hub.provider.register
          fields_used: [hub_name, federation_url, public_key]
        - topic: hub.index.updated
          fields_used: [listing_id, operation]
        - topic: hub.behavioral.change
          fields_used: [listing_id, level, details]
        - topic: hub.verification.failure
          fields_used: [listing_id, provider, reason]
        - topic: hub.sla.breach
          fields_used: [listing_id, metric, threshold, actual]
        - topic: hub.listing.suspended
          fields_used: [listing_id, reason]
        - topic: hub.peer.revoked
          fields_used: [hub_name, reason]
        - topic: federation.task.completed
          fields_used: [listing_id, latency_ms, status, data_bytes_in, data_bytes_out]
        - topic: federation.task.failed
          fields_used: [listing_id, error, timestamp]
        - topic: federation.key.rotated
          fields_used: [hub_name, old_key, new_key]
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

  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token]
        - path: /v1/services
          methods: [GET]
          response_fields: [agents]
      events:
        - topic: system.agent.registered
          fields_used: [agent_name, manifest]
        - topic: system.agent.deregistered
          fields_used: [agent_name]
        - topic: system.shutdown
          fields_used: []
        - topic: system.blueprint.changed
          fields_used: [blueprint_name, version, diff]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

extends:
  - pattern: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: publish
          parameters: [topic, payload, source]
        - behavior: subscribe
          parameters: [topic, handler, consumer_group]
        - behavior: dead-letter
          parameters: [max_retries, dlq_topic]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/caching
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: ttl-cache
          parameters: [key, value, ttl]
        - behavior: cache-invalidation
          parameters: [key, reason]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: metrics
          parameters: [gauge, counter, histogram]
        - behavior: alerts
          parameters: [condition, severity, routing]
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

  - pattern: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: sqlite-engine
          parameters: [engine, tables, indexes, relationships, constraints]
        - behavior: backup-restore
          parameters: [frequency, format, path]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/notification
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: channel-routing
          parameters: [severity, channel, urgency]
        - behavior: batching
          parameters: [batch_window, max_batch_size]
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

depends_on: [alerting]
  # Runtime dependency on the alerting agent for notification delivery.
  # The hub agent degrades gracefully if alerting is unavailable —
  # queues alerts locally until recovery.
```

---

## Configuration

### Indexing Subsystem

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

### Search Subsystem

```yaml
config:
  query_result_cache_ttl:
    type: int
    default: 60
    env: WL_HUB_SEARCH_CACHE_TTL
    min: 0
    max: 600
    unit: seconds
    description: TTL for cached query results

  facet_cache_ttl:
    type: int
    default: 300
    env: WL_HUB_SEARCH_FACET_TTL
    min: 0
    max: 3600
    unit: seconds
    description: TTL for cached facet values

  trending_cache_ttl:
    type: int
    default: 900
    env: WL_HUB_SEARCH_TRENDING_TTL
    min: 60
    max: 3600
    unit: seconds
    description: TTL for trending listings cache

  autocomplete_cache_ttl:
    type: int
    default: 1800
    env: WL_HUB_SEARCH_AUTOCOMPLETE_TTL
    min: 60
    max: 7200
    unit: seconds
    description: TTL for autocomplete index cache

  max_results_per_page:
    type: int
    default: 100
    env: WL_HUB_SEARCH_MAX_PER_PAGE
    min: 10
    max: 500
    description: Maximum results per page

  default_results_per_page:
    type: int
    default: 20
    env: WL_HUB_SEARCH_DEFAULT_PER_PAGE
    min: 1
    max: 100
    description: Default results per page

  query_timeout:
    type: int
    default: 10
    env: WL_HUB_SEARCH_QUERY_TIMEOUT
    min: 1
    max: 60
    unit: seconds
    description: Maximum query execution time before returning partial results

  max_cache_entries:
    type: int
    default: 10000
    env: WL_HUB_SEARCH_MAX_CACHE
    min: 100
    max: 100000
    description: Maximum entries in query result cache
```

### Metrics Subsystem

```yaml
config:
  probe_interval:
    type: string
    default: "*/5 * * * *"
    env: WL_HUB_METRICS_PROBE_INTERVAL
    description: Cron expression for availability probe schedule

  probe_timeout:
    type: int
    default: 10
    env: WL_HUB_METRICS_PROBE_TIMEOUT
    min: 1
    max: 60
    unit: seconds
    description: Timeout for individual availability probe

  aggregation_interval:
    type: string
    default: "0 * * * *"
    env: WL_HUB_METRICS_AGG_INTERVAL
    description: Cron expression for rolling aggregate recomputation

  max_concurrent_probes:
    type: int
    default: 20
    env: WL_HUB_METRICS_MAX_PROBES
    min: 1
    max: 100
    description: Maximum simultaneous availability probes

  retention_hourly:
    type: int
    default: 172800
    env: WL_HUB_METRICS_RETENTION_HOURLY
    min: 3600
    unit: seconds
    description: Hourly data retention (default 48h)

  retention_daily:
    type: int
    default: 7776000
    env: WL_HUB_METRICS_RETENTION_DAILY
    min: 86400
    unit: seconds
    description: Daily aggregate retention (default 90d)

  retention_weekly:
    type: int
    default: 31536000
    env: WL_HUB_METRICS_RETENTION_WEEKLY
    min: 604800
    unit: seconds
    description: Weekly aggregate retention (default 1 year)

  retention_monthly:
    type: int
    default: 63072000
    env: WL_HUB_METRICS_RETENTION_MONTHLY
    min: 2592000
    unit: seconds
    description: Monthly aggregate retention (default 2 years)

  sla_uptime_threshold:
    type: float
    default: 99.0
    env: WL_HUB_METRICS_SLA_UPTIME
    min: 0.0
    max: 100.0
    description: Uptime percentage below which SLA breach is triggered
```

### Verification Subsystem

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

  max_concurrent_fingerprint_probes:
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

### Alerting Subsystem

```yaml
config:
  dedup_window:
    type: int
    default: 3600
    env: WL_HUB_ALERT_DEDUP_WINDOW
    min: 60
    max: 86400
    unit: seconds
    description: Suppress duplicate alerts for same listing + event type within this window

  max_batch_size:
    type: int
    default: 50
    env: WL_HUB_ALERT_MAX_BATCH
    min: 1
    max: 500
    description: Maximum notifications per batch delivery to alerting agent

  notification_timeout:
    type: int
    default: 30
    env: WL_HUB_ALERT_NOTIFY_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Timeout for individual notification delivery

  federation_notify_timeout:
    type: int
    default: 15
    env: WL_HUB_ALERT_FED_TIMEOUT
    min: 5
    max: 60
    unit: seconds
    description: Timeout for cross-hub federation notification delivery

  flapping_threshold:
    type: int
    default: 3
    env: WL_HUB_ALERT_FLAP_THRESHOLD
    min: 2
    max: 20
    description: State changes within dedup_window to trigger flapping consolidation

  mute_max_duration:
    type: int
    default: 86400
    env: WL_HUB_ALERT_MUTE_MAX
    min: 300
    max: 604800
    unit: seconds
    description: Maximum mute duration for a listing

  alert_retry_max:
    type: int
    default: 3
    env: WL_HUB_ALERT_RETRY_MAX
    min: 0
    max: 10
    description: Retry attempts for failed notification delivery

  alert_history_retention:
    type: int
    default: 2592000
    env: WL_HUB_ALERT_HISTORY_RETENTION
    min: 86400
    unit: seconds
    description: Alert history retention period (default 30 days)
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

### Indexing Types

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

### Search Types

```yaml
types:
  SearchRequest:
    description: Search query parameters
    fields:
      q:
        type: string
        optional: true
        max: 256
        description: Free-text search query
      domain:
        type: string
        optional: true
        description: Filter by domain name
      action:
        type: string
        optional: true
        description: Filter by capability action
      tier:
        type: string
        enum: [free, pro, all]
        default: all
        description: Filter by availability tier
      jurisdiction:
        type: string
        optional: true
        description: ISO 3166-1 country code filter
      min_uptime:
        type: float
        optional: true
        min: 0.0
        max: 100.0
        description: Minimum 30-day uptime percentage
      max_latency:
        type: int
        optional: true
        min: 0
        description: Maximum p95 latency in milliseconds
      max_price:
        type: float
        optional: true
        min: 0.0
        description: Maximum price per invocation
      sort:
        type: string
        enum: [relevance, uptime, latency, invocations, newest]
        default: relevance
        description: Sort order for results
      page:
        type: int
        default: 1
        min: 1
        description: Page number
      per_page:
        type: int
        default: 20
        min: 1
        max: 100
        description: Results per page

  SearchResponse:
    description: Search result envelope
    fields:
      results:
        type: array
        items: SearchResultEntry
        description: Matching listings
      total:
        type: int
        description: Total matching results
      page:
        type: int
        description: Current page number
      per_page:
        type: int
        description: Results per page
      facets:
        type: object
        optional: true
        description: Faceted counts (domains, tiers, jurisdictions)

  SearchResultEntry:
    description: Single search result
    fields:
      listing_id:
        type: string
        description: Listing identifier
      provider:
        type: string
        description: Provider hub name
      capability:
        type: object
        description: Capability definition
      tier:
        type: string
        description: Availability tier
      metrics:
        type: object
        description: MetricsInfo snapshot (uptime, latency, invocations)
      score:
        type: float
        description: Relevance score (0.0-1.0)
      indexed_at:
        type: int64
        description: When listing was indexed

  SearchAnalyticsEntry:
    description: Search query analytics record
    fields:
      query_id:
        type: string
        format: uuid-v7
        description: Unique query identifier
      q:
        type: string
        optional: true
        description: Search query text
      filters:
        type: object
        description: Applied filters
      results_returned:
        type: int
        description: Number of results returned
      total_results:
        type: int
        description: Total matching results
      duration_ms:
        type: int
        description: Query execution time
      timestamp:
        type: int64
        auto: true
        description: Query timestamp
```

### Metrics Types

```yaml
types:
  InvocationRecord:
    description: Single federated task invocation measurement
    fields:
      record_id:
        type: string
        format: uuid-v7
        description: Unique record identifier
      listing_id:
        type: string
        description: Listing that was invoked
      timestamp:
        type: int64
        description: Invocation timestamp
      latency_ms:
        type: int
        min: 0
        description: End-to-end latency in milliseconds
      status:
        type: string
        enum: [success, error, timeout]
        description: Invocation outcome
      data_bytes_in:
        type: int
        min: 0
        description: Request payload size
      data_bytes_out:
        type: int
        min: 0
        description: Response payload size

  ProbeResult:
    description: Availability probe measurement
    fields:
      probe_id:
        type: string
        format: uuid-v7
        description: Unique probe identifier
      listing_id:
        type: string
        description: Probed listing
      timestamp:
        type: int64
        description: Probe timestamp
      available:
        type: bool
        description: Whether provider responded within timeout
      response_ms:
        type: int
        optional: true
        description: Response time if available

  ListingAggregate:
    description: Rolling aggregate metrics for a listing
    fields:
      listing_id:
        type: string
        description: Listing identifier
      window:
        type: string
        enum: [1h, 24h, 7d, 30d]
        description: Aggregation window
      uptime_pct:
        type: float
        description: Availability percentage
      p95_latency_ms:
        type: int
        description: 95th percentile latency
      total_invocations:
        type: int
        description: Total invocations in window
      error_rate:
        type: float
        description: Error rate as fraction (0.0-1.0)
      behavioral_changes:
        type: int
        description: Behavioral changes in window
      computed_at:
        type: int64
        auto: true
        description: When aggregate was computed
    constraints:
      - name: uq_listing_window
        type: unique
        fields: [listing_id, window]
        description: One aggregate per listing per window

  NetworkAggregate:
    description: Network-wide aggregate statistics
    fields:
      total_listings:
        type: int
        description: Total active listings
      total_providers:
        type: int
        description: Total active providers
      total_invocations_30d:
        type: int
        description: Total invocations across all listings
      avg_uptime_30d:
        type: float
        description: Average uptime across all listings
      avg_p95_latency_30d_ms:
        type: int
        description: Average p95 latency across all listings
      computed_at:
        type: int64
        auto: true
        description: When aggregate was computed
```

### Verification Types

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

### Alerting Types

```yaml
types:
  HubAlert:
    description: A hub network alert record
    fields:
      alert_id:
        type: string
        format: uuid-v7
        description: Unique alert identifier
      listing_id:
        type: string
        description: Affected listing identifier
      event_type:
        type: string
        enum: [behavioral_change, verification_failure, sla_breach,
               listing_suspended, peer_revoked, marketplace_event]
        description: Category of hub event
      severity:
        type: string
        enum: [info, warning, critical]
        description: Alert severity level
      level:
        type: string
        enum: [BENIGN, NOTABLE, BREAKING, CRITICAL]
        optional: true
        description: Behavioral change level (when event_type = behavioral_change)
      payload:
        type: object
        description: Event-specific details
      recipients:
        type: array
        items: string
        description: List of notification targets (hub names or operator IDs)
      channels:
        type: array
        items: string
        description: Delivery channels used
      status:
        type: string
        enum: [pending, delivering, delivered, failed, suppressed]
        description: Delivery status
      suppression_reason:
        type: string
        optional: true
        description: Why alert was suppressed (dedup, muted, maintenance)
      created_at:
        type: int64
        auto: true
        description: Alert creation timestamp
      delivered_at:
        type: int64
        optional: true
        description: Delivery completion timestamp
      retry_count:
        type: int
        default: 0
        description: Current retry attempt count

  AlertRule:
    description: Alert routing and threshold rule
    fields:
      rule_id:
        type: string
        format: uuid-v7
        description: Unique rule identifier
      listing_id:
        type: string
        optional: true
        description: Specific listing or null for global rule
      event_type:
        type: string
        description: Event type this rule applies to
      severity_override:
        type: string
        enum: [info, warning, critical]
        optional: true
        description: Override default severity
      channels:
        type: array
        items: string
        description: Channels for this rule
      enabled:
        type: bool
        default: true
        description: Whether rule is active
      created_by:
        type: string
        description: Operator who created the rule

  AlertMute:
    description: Temporary alert suppression for a listing
    fields:
      mute_id:
        type: string
        format: uuid-v7
        description: Unique mute identifier
      listing_id:
        type: string
        description: Muted listing
      reason:
        type: string
        max: 256
        description: Why the listing is muted
      muted_by:
        type: string
        description: Operator identity
      muted_at:
        type: int64
        auto: true
        description: Mute start timestamp
      expires_at:
        type: int64
        description: Mute expiration timestamp
    constraints:
      - name: ck_mute_duration
        type: check
        expression: expires_at - muted_at <= config.mute_max_duration
        description: Mute duration cannot exceed configured maximum
```

---

## Storage

Storage tables reference the Types section. Fields are not redefined
here — the `source_type` key links each table to its type definition.

```yaml
storage:
  engine: sqlite

  tables:
    listing_index:
      source_type: IndexedListing
      primary_key: listing_id
      indexes:
        - name: idx_listing_provider
          fields: [provider]
          type: btree
        - name: idx_listing_status
          fields: [status]
          type: btree
        - name: idx_listing_indexed_at
          fields: [indexed_at]
          type: btree
        - name: idx_listing_capability
          fields: [capability]
          type: gin
          description: Full-text search on capability content

    provider_registry:
      source_type: ProviderRecord
      primary_key: hub_name
      indexes:
        - name: idx_provider_last_seen
          fields: [last_seen]
          type: btree
        - name: idx_provider_miss_count
          fields: [miss_count]
          type: btree

    crawl_history:
      source_type: CrawlResult
      primary_key: crawl_id
      indexes:
        - name: idx_crawl_provider
          fields: [hub_name, started_at]
          type: btree
        - name: idx_crawl_status
          fields: [status]
          type: btree

    metrics_store:
      source_type: InvocationRecord
      primary_key: record_id
      indexes:
        - name: idx_invocation_listing
          fields: [listing_id, timestamp]
          type: btree
          description: Per-listing time-series lookup
        - name: idx_invocation_status
          fields: [status]
          type: btree

    probe_results:
      source_type: ProbeResult
      primary_key: probe_id
      indexes:
        - name: idx_probe_listing
          fields: [listing_id, timestamp]
          type: btree

    listing_aggregates:
      source_type: ListingAggregate
      primary_key: [listing_id, window]
      indexes:
        - name: idx_aggregate_computed
          fields: [computed_at]
          type: btree

    verification_log:
      source_type: VerificationRecord
      primary_key: verification_id
      indexes:
        - name: idx_verification_target
          fields: [target_type, target_id]
          type: btree
        - name: idx_verification_result
          fields: [result]
          type: btree
        - name: idx_verification_time
          fields: [verified_at]
          type: btree

    behavioral_fingerprints:
      source_type: BehavioralFingerprint
      primary_key: fingerprint_id
      indexes:
        - name: idx_fingerprint_listing
          fields: [listing_id, fingerprint_version]
          type: btree
          description: Latest fingerprint per listing
        - name: idx_fingerprint_change
          fields: [change_level]
          type: btree

    search_analytics:
      source_type: SearchAnalyticsEntry
      primary_key: query_id
      indexes:
        - name: idx_analytics_timestamp
          fields: [timestamp]
          type: btree

    alert_rules:
      source_type: AlertRule
      primary_key: rule_id
      indexes:
        - name: idx_rule_listing
          fields: [listing_id, event_type]
          type: btree
        - name: idx_rule_enabled
          fields: [enabled]
          type: btree

    alert_history:
      source_type: HubAlert
      primary_key: alert_id
      indexes:
        - name: idx_alert_listing
          fields: [listing_id, event_type]
          type: btree
        - name: idx_alert_created
          fields: [created_at]
          type: btree
        - name: idx_alert_status
          fields: [status]
          type: btree

    alert_mutes:
      source_type: AlertMute
      primary_key: mute_id
      indexes:
        - name: idx_mute_listing
          fields: [listing_id]
          type: btree
        - name: idx_mute_expires
          fields: [expires_at]
          type: btree

  relationships:
    - name: crawl_provider
      from: crawl_history.hub_name
      to: provider_registry.hub_name
      cardinality: many-to-one
      on_delete: cascade
      description: Each crawl belongs to a provider

    - name: fingerprint_listing
      from: behavioral_fingerprints.listing_id
      to: listing_index.listing_id
      cardinality: many-to-one
      on_delete: cascade
      description: Fingerprints belong to a listing

    - name: invocation_listing
      from: metrics_store.listing_id
      to: listing_index.listing_id
      cardinality: many-to-one
      on_delete: cascade
      description: Invocation records belong to a listing

    - name: alert_listing
      from: alert_history.listing_id
      to: listing_index.listing_id
      cardinality: many-to-one
      on_delete: set-null
      description: Alerts reference a listing (nullable for peer events)

  retention:
    listing_index:
      policy: indefinite
      cleanup: stale evaluation per config.stale_grace_period
    provider_registry:
      policy: indefinite
      cleanup: manual via admin action
    crawl_history:
      policy: 30 days
      cleanup: automatic after aggregation cycle
    metrics_store:
      policy: config.retention_hourly
      cleanup: automatic after aggregation cycle
    probe_results:
      policy: config.retention_hourly
      cleanup: automatic after aggregation cycle
    listing_aggregates:
      policy: per-window retention (hourly→48h, daily→90d, weekly→1y, monthly→2y)
      cleanup: automatic after aggregation cycle
    verification_log:
      policy: config.verification_log_retention
      cleanup: automatic daily
    behavioral_fingerprints:
      policy: config.fingerprint_retention
      cleanup: automatic daily
    search_analytics:
      policy: 30 days
      cleanup: automatic daily
    alert_rules:
      policy: indefinite
      cleanup: manual via admin action
    alert_history:
      policy: config.alert_history_retention
      cleanup: automatic daily
    alert_mutes:
      policy: self-expiring via expires_at
      cleanup: automatic on access

  backup:
    listing_index:
      frequency: daily
      format: JSON export of active listings
      path: .weblisk/backups/hub/listing_index_{ISO8601}.json
    provider_registry:
      frequency: daily
      format: JSON export of all providers
      path: .weblisk/backups/hub/provider_registry_{ISO8601}.json
    alert_rules:
      frequency: daily
      format: JSON export of all rules
      path: .weblisk/backups/hub/alert_rules_{ISO8601}.json
    verification_log:
      backup: false
      reason: Append-only log, not critical for restore
    metrics_store:
      backup: false
      reason: Derived from live data, re-collected after restart
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
        trigger: subsystems_ready
        validates: all 5 subsystems initialized, subscriptions active
      - from: active
        to: indexing
        trigger: crawl_started
        validates: crawl lock acquired
      - from: indexing
        to: active
        trigger: crawl_complete
        validates: all providers processed
      - from: active
        to: collecting
        trigger: probe_cycle_started
        validates: probe lock acquired
      - from: collecting
        to: active
        trigger: probe_cycle_complete
        validates: all probes finished or timed out
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
        validates: signal received (SIGTERM, system.shutdown, or API)
      - from: indexing
        to: retiring
        trigger: shutdown_signal
        validates: signal received — drain current crawl
      - from: collecting
        to: retiring
        trigger: shutdown_signal
        validates: signal received — drain active probes
      - from: verifying
        to: retiring
        trigger: shutdown_signal
        validates: signal received — drain active verifications
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: all in-flight operations finished or timed out

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

  entity.HubAlert:
    initial: pending
    transitions:
      - from: pending
        to: suppressed
        trigger: dedup_match
        validates: duplicate within dedup_window or listing muted
        side_effect: increment suppression counter
      - from: pending
        to: delivering
        trigger: dispatch_started
        validates: recipients resolved, channels selected
      - from: delivering
        to: delivered
        trigger: delivery_confirmed
        validates: alerting agent acknowledged all notifications
        side_effect: set delivered_at timestamp
      - from: delivering
        to: failed
        trigger: delivery_failed
        validates: retries exhausted
        side_effect: log failure, emit hub_alert.delivery.failed event
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables for all 5 subsystems, apply defaults
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID — log which keys failed validation

Step 2 — Load Identity
  Action:      Load Ed25519 keypair from .weblisk/keys/hub/
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema against all Types blocks
  Validates:   All tables exist (listing_index, provider_registry, metrics_store,
               verification_log, behavioral_fingerprints, search_analytics,
               alert_rules, alert_history, alert_mutes, probe_results,
               listing_aggregates, crawl_history), columns match, indexes present
  On Fail:     Run migration → if fails EXIT with STORAGE_UNREACHABLE

Step 4 — Load Revocation List
  Action:      Load known revoked keys from verification_log
  Validates:   Revocation list parsed and cached in memory
  On Fail:     Enter degraded state — may accept revoked keys

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 6 — Subscribe to Events
  Action:      Subscribe to all hub and federation topics:
               hub.listing.publish, hub.listing.delist,
               hub.provider.register, hub.verify.request,
               federation.task.completed, federation.task.failed,
               federation.key.rotated,
               hub.behavioral.change, hub.verification.failure,
               hub.sla.breach, hub.listing.suspended,
               hub.peer.revoked, hub.marketplace.event,
               system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED

Step 7 — Initialize Subsystems
  Action:      Load index statistics, active listings for probing,
               fingerprint baselines, alert rules and mutes,
               warm search caches
  Validates:   All subsystem init queries succeed
  On Fail:     Enter degraded state — subsystems initialize lazily

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9770, listings: N, providers: M,
       fingerprints: F, active_rules: R, active_mutes: U}
```

### Shutdown Sequence

```
Step 1 — Stop Accepting Events
  Action:      Unsubscribe from all topics
  agent_state → retiring

Step 2 — Drain In-Flight Operations
  Action:      Wait for active crawls, probes, verifications to complete (up to 60s)
  On Timeout:  Record partial results for all in-flight operations

Step 3 — Final Aggregation
  Action:      Compute final rolling aggregates with latest data

Step 4 — Persist Pending Alerts
  Action:      Write undelivered alerts to storage for next startup

Step 5 — Deregister
  Action:      DELETE /v1/register

Step 6 — Close Storage
  Action:      Close database connection

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, crawls_drained, probes_drained,
       verifications_drained, alerts_persisted}
  agent_state → retired
```

### Health

Reported via `GET /v1/health`:

```yaml
health:
  healthy:
    conditions:
      - storage connected
      - event subscriptions active
      - last crawl completed within 2x crawl_interval
      - probes running on schedule
      - revocation list loaded
      - fingerprint baselines available
      - alerting agent reachable
    response:
      status: healthy
      details: {storage, listings_total, providers_total, stale_listings,
                tracked_listings, last_crawl, last_probe_cycle,
                last_aggregation, last_fingerprint_cycle,
                revocation_list_size, fingerprints_loaded,
                active_rules, active_mutes, pending_alerts, subscriptions}

  degraded:
    conditions:
      - storage errors (retrying)
      - last crawl failed
      - stale listings > 20% of total
      - probe failures > 50% of listings
      - aggregation stale (missed 2+ cycles)
      - revocation list stale
      - fingerprint cycle failed
      - alerting agent unreachable (queuing locally)
    response:
      status: degraded
      details: {reason, stale_count, probe_failure_rate,
                queued_alerts, last_error}

  unhealthy:
    conditions:
      - storage unreachable after retries
      - no event subscriptions active
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "hub"`:

```
Step 1 — Validate new blueprint, verify version is newer
Step 2 — Compare Types block against current storage schema
Step 3 — Pause all subsystem processing → run migration → resume
Step 4 — Reload configuration, revocation list, rules, mutes, caches
Log: lifecycle.version_updated {from, to}
```

---

## Triggers

```yaml
triggers:
  # Indexing triggers
  - name: listing_publish
    type: event
    topic: hub.listing.publish
    description: Provider submits a new or updated listing

  - name: listing_delist
    type: event
    topic: hub.listing.delist
    description: Provider removes a listing

  - name: provider_register
    type: event
    topic: hub.provider.register
    description: New provider hub discovered — trigger initial crawl

  - name: crawl_schedule
    type: schedule
    expression: "0 */6 * * *"
    description: Every 6 hours — re-crawl all known providers

  # Metrics triggers
  - name: task_completed
    type: event
    topic: federation.task.completed
    description: Federated task finished — record latency, status

  - name: task_failed
    type: event
    topic: federation.task.failed
    description: Federated task failed — record error

  - name: listing_indexed
    type: event
    topic: hub.listing.indexed
    description: New listing — start tracking metrics

  - name: probe_schedule
    type: schedule
    expression: "*/5 * * * *"
    description: Every 5 minutes — probe listed capabilities for uptime

  - name: aggregation_schedule
    type: schedule
    expression: "0 * * * *"
    description: Hourly — recompute rolling aggregates

  # Verification triggers
  - name: key_rotated
    type: event
    topic: federation.key.rotated
    description: Provider key change needs validation

  - name: verify_request
    type: event
    topic: hub.verify.request
    description: On-demand verification from admin or other agents

  - name: fingerprint_schedule
    type: schedule
    expression: "0 */4 * * *"
    description: Every 4 hours — behavioral fingerprint sampling

  # Alerting triggers
  - name: behavioral_change
    type: event
    topic: hub.behavioral.change
    description: Behavioral change detected by verification subsystem

  - name: verification_failure
    type: event
    topic: hub.verification.failure
    description: Signature or identity verification failed

  - name: sla_breach
    type: event
    topic: hub.sla.breach
    description: Provider SLA violation detected by metrics subsystem

  - name: listing_suspended
    type: event
    topic: hub.listing.suspended
    description: Listing suspended (manual or automatic)

  - name: peer_revoked
    type: event
    topic: hub.peer.revoked
    description: Trust relationship revoked

  - name: marketplace_event
    type: event
    topic: hub.marketplace.event
    description: Marketplace transaction event requiring notification

  # System triggers
  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "hub"
    description: Self-update if hub blueprint changed

  - name: direct_message
    type: message
    endpoint: POST /v1/message
    actions: [index-listing, remove-listing, crawl-provider, crawl-all,
              get-listing, prune-stale, reindex,
              search, browse, trending, recommend, autocomplete, get-facets,
              record-invocation, record-error, probe-availability, probe-all,
              get-metrics, get-metrics-history, get-aggregate,
              verify-listing, verify-manifest, verify-identity,
              verify-key-rotation, fingerprint-behavior, classify-change,
              verify-data-contract,
              notify-behavioral-change, notify-verification-failure,
              notify-sla-breach, notify-listing-suspension,
              notify-peer-revocation, notify-marketplace-event,
              get-alert-history, configure-rules, mute-listing]
    description: Agent-to-agent and operator actions
```

---

## Actions

### Indexing Actions

#### index-listing

Index a published listing after signature verification.

**Source:** Provider Hub

**Input:** `{listing_id: string, provider: string, capability: object, tier: string, version: string, signature: string, public_key: string}`

**Processing:**

```
1. Verify Ed25519 signature over listing content
   If verification fails → reject, log, emit hub.verification.failure
2. Validate listing schema — required fields present, version is valid semver
3. Check for duplicates:
   If listing_id exists with same version → update timestamps
   If listing_id exists with different version → version update flow
   If new → insert
4. Write to listing_index store
5. Update provider_registry with last_seen timestamp
6. Invalidate search cache for affected facets
7. Start tracking metrics for new listings
```

**Output:** `{listing_id: string, status: "indexed" | "updated" | "rejected", reason?: string}`

**Errors:** `SIGNATURE_INVALID` (permanent), `SCHEMA_INVALID` (permanent), `STORAGE_ERROR` (transient)

---

#### remove-listing

Remove a delisted capability.

**Source:** Provider Hub

**Input:** `{listing_id: string, provider: string}`

**Processing:**

```
1. Verify requester is the listing's provider
2. Update listing status → delisted
3. Invalidate search cache
```

**Output:** `{listing_id: string, removed: true}`

---

#### crawl-provider

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

#### crawl-all

Re-crawl all known providers.

**Source:** Cron

**Input:** `{}`

**Processing:**

```
1. Acquire crawl lock
2. SELECT all providers from provider_registry
3. For each provider (up to config.max_concurrent_crawls in parallel):
   crawl-provider flow
4. After all crawls: run stale listing evaluation
5. Release crawl lock
```

**Output:** `{providers_crawled: int, total_listings_indexed: int}`

---

#### get-listing

Retrieve a specific listing by ID.

**Source:** Search subsystem / Admin

**Input:** `{listing_id: string}`

**Output:** `{listing: IndexedListing}`

**Side Effects:** None (read-only).

---

#### prune-stale

Remove listings from unresponsive providers.

**Source:** Cron

**Input:** `{}`

**Processing:**

```
1. Query stale listings past grace period
2. Move to archive, remove from active index
3. Invalidate search cache
```

**Output:** `{pruned: int}`

---

#### reindex

Force full reindex of all providers.

**Source:** Admin

**Input:** `{}`

**Output:** `{providers_reindexed: int, listings_reindexed: int}`

**Side Effects:** Triggers crawl-all with forced re-verification.

---

### Search Actions

#### search

Full-text search over the listing index.

**Source:** Consumer Hub / Marketplace / CLI

**Input:** `SearchRequest`

**Processing:**

```
1. Check query result cache → return if hit and TTL valid
2. Parse search query, apply filters
3. Execute full-text search against listing_index
4. Join with listing_aggregates for metrics data
5. Rank by relevance (text match + metrics quality)
6. Apply pagination
7. Compute facets (domains, tiers, jurisdictions)
8. Cache result with config.query_result_cache_ttl
9. Record SearchAnalyticsEntry
```

**Output:** `SearchResponse`

---

#### browse

Browse listings by category/domain.

**Source:** Marketplace

**Input:** `{domain?: string, tier?: string, sort?: string, page?: int, per_page?: int}`

**Output:** `SearchResponse`

---

#### trending

Get trending listings by invocation volume and growth.

**Source:** Marketplace

**Input:** `{limit?: int}`

**Processing:**

```
1. Check trending cache → return if hit and TTL valid
2. Query listing_aggregates for top listings by invocation growth
3. Cache result with config.trending_cache_ttl
```

**Output:** `{listings: SearchResultEntry[]}`

---

#### recommend

Recommend capabilities based on querying hub's existing domains.

**Source:** Consumer Hub

**Input:** `{hub_domains: string[], limit?: int}`

**Output:** `{recommendations: SearchResultEntry[]}`

---

#### autocomplete

Prefix-based suggestion for search input.

**Source:** Marketplace UI

**Input:** `{prefix: string, limit?: int}`

**Processing:**

```
1. Check autocomplete cache → return if hit and TTL valid
2. Query listing_index for capability names matching prefix
3. Cache result with config.autocomplete_cache_ttl
```

**Output:** `{suggestions: string[]}`

---

#### get-facets

Get available facet values for search filtering.

**Source:** Marketplace UI

**Input:** `{}`

**Processing:**

```
1. Check facet cache → return if hit and TTL valid
2. Compute facet counts from listing_index
3. Cache result with config.facet_cache_ttl
```

**Output:** `{domains: object, tiers: object, jurisdictions: object}`

---

### Metrics Actions

#### record-invocation

Record a completed federated task for metrics.

**Source:** Federation Layer

**Input:** `{listing_id: string, timestamp: int64, latency_ms: int, status: string, data_bytes_in: int, data_bytes_out: int}`

**Processing:**

```
1. Validate input against InvocationRecord type
2. Insert into metrics_store table
3. If status = error or timeout → check SLA thresholds
4. Emit metrics: hub_metrics_invocations_recorded_total
```

**Output:** `{recorded: true, record_id: string}`

**Errors:** `INVALID_INPUT` (permanent), `STORAGE_ERROR` (transient)

---

#### record-error

Record a failed federated task.

**Source:** Federation Layer

**Input:** `{listing_id: string, error: string, timestamp: int64}`

**Processing:**

```
1. Insert error record into metrics_store with status = error
2. Check error rate threshold — if SLA breached, emit hub.sla.breach
```

**Output:** `{recorded: true}`

---

#### probe-availability

Uptime probe for a specific listing.

**Source:** Cron

**Input:** `{listing_id: string}`

**Processing:**

```
1. Look up provider federation_url for listing
2. HEAD {federation_url}/status with config.probe_timeout
3. Record ProbeResult (available = response within timeout)
4. If unavailable → check consecutive failures for SLA breach
```

**Output:** `{listing_id: string, available: bool, response_ms?: int}`

---

#### probe-all

Uptime probe for all active listings.

**Source:** Cron

**Input:** `{}`

**Processing:**

```
1. Acquire probe lock
2. Query all active listings from listing_index
3. For each listing (up to config.max_concurrent_probes in parallel):
   probe-availability flow
4. Run SLA evaluation after all probes
5. Release probe lock
6. Emit batch metrics
```

**Output:** `{probed: int, available: int, unavailable: int}`

---

#### get-metrics

Retrieve current metrics for a listing.

**Source:** Search subsystem / Consumer / Admin

**Input:** `{listing_id: string}`

**Output:** `{metrics: ListingAggregate}` — matches MetricsInfo schema from hub.md

**Side Effects:** None (read-only).

---

#### get-metrics-history

Time-series metrics over a date range.

**Source:** Admin / Consumer

**Input:** `{listing_id: string, from: int64, to: int64, window: string}`

**Output:** `{data_points: ListingAggregate[]}`

---

#### get-aggregate

Network-wide aggregate statistics.

**Source:** Marketplace

**Input:** `{}`

**Output:** `{aggregate: NetworkAggregate}`

---

### Verification Actions

#### verify-listing

Verify Ed25519 signature on a listing.

**Source:** Indexing subsystem

**Input:** `{listing_id: string, provider: string, signature: string, public_key: string, listing_data: object}`

**Processing:**

```
1. Check key against revocation list → if revoked, fail immediately
2. Reconstruct canonical listing bytes (deterministic serialization)
3. Verify Ed25519 signature: crypto.verify(public_key, canonical_bytes, signature)
4. Check key matches provider's registered identity
5. Record VerificationRecord
6. If fail → emit hub.verification.failure
```

**Output:** `{result: "pass" | "fail", verification_id: string, reason?: string}`

**Errors:** `KEY_REVOKED` (permanent), `SIGNATURE_INVALID` (permanent), `STORAGE_ERROR` (transient)

---

#### verify-manifest

Verify a provider's orchestrator manifest.

**Source:** Indexing subsystem

**Input:** `{hub_name: string, manifest: object, signature: string, public_key: string}`

**Processing:**

```
1. Same signature verification as verify-listing
2. Additionally verify manifest structure and required fields
3. Record VerificationRecord
```

**Output:** `{result: "pass" | "fail", verification_id: string}`

---

#### verify-identity

Validate provider identity (key, domain, TLS).

**Source:** Admin / Indexing subsystem

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

#### verify-key-rotation

Validate key rotation with dual-signature proof.

**Source:** Federation

**Input:** `{hub_name: string, old_key: string, new_key: string, old_signature: string, new_signature: string, timestamp: int64}`

**Processing:**

```
1. Verify old key signature on rotation announcement
2. Verify new key signature on rotation announcement (dual-signature)
3. Check rotation cooldown: minimum config.key_rotation_cooldown since last rotation
4. Record KeyRotationRecord
5. If valid → trigger re-verification of all listings with new key
6. If invalid → reject, emit hub.verification.failure as potential compromise
```

**Output:** `{result: "pass" | "fail", rotation_id: string}`

---

#### fingerprint-behavior

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

#### classify-change

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

#### verify-data-contract

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

### Alerting Actions

#### notify-behavioral-change

Notify collaborators of capability behavioral change.

**Source:** Verification subsystem

**Input:** `{listing_id: string, level: string, details: BehavioralChange}`

**Processing:**

```
1. Look up listing in index — resolve provider and active collaborators
2. Determine severity from change level:
   BENIGN → info, NOTABLE → warning, BREAKING → critical, CRITICAL → critical
3. Check deduplication: same listing + behavioral_change within dedup_window → suppress
4. Check mute status: listing muted → suppress non-CRITICAL
5. Check flapping: 3+ changes in dedup_window → consolidate
6. Resolve recipients per notification routing
7. Create HubAlert record with status = pending
8. Dispatch to alerting agent for delivery
9. For cross-hub recipients: POST federation notify endpoint
10. Update HubAlert status based on delivery result
```

**Output:** `{alert_id: string, recipients_notified: int, suppressed: bool}`

**Errors:** `LISTING_NOT_FOUND` (permanent), `DELIVERY_FAILED` (transient)

---

#### notify-verification-failure

Alert admin of signature/identity verification failure.

**Source:** Verification subsystem

**Input:** `{listing_id: string, provider: string, reason: string}`

**Processing:**

```
1. Set severity = critical (verification failures are always critical)
2. Check deduplication
3. Notify registry operator + provider admin
4. Create HubAlert record, dispatch via alerting agent
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

#### notify-sla-breach

Alert consumer of provider SLA violation.

**Source:** Metrics subsystem

**Input:** `{listing_id: string, metric: string, threshold: float, actual: float}`

**Processing:**

```
1. Look up affected collaborations for listing
2. Notify consumer hub admins for active collaborations
3. Check deduplication and mute status
4. Create HubAlert record, dispatch via alerting agent
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

#### notify-listing-suspension

Notify all collaborators that a listing is suspended.

**Source:** Verification subsystem / Admin

**Input:** `{listing_id: string, reason: string}`

**Processing:**

```
1. Resolve all active collaborators for listing
2. Set severity = critical
3. Create HubAlert, dispatch to all collaborators
4. Include federation notifications for cross-hub collaborators
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

#### notify-peer-revocation

Notify affected parties of trust revocation.

**Source:** Federation

**Input:** `{hub_name: string, reason: string}`

**Processing:**

```
1. Resolve both parties (consumer + provider hubs)
2. Set severity = critical
3. Create HubAlert record, dispatch notifications
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

#### notify-marketplace-event

Transaction confirmations and purchase alerts.

**Source:** Marketplace

**Input:** `{listing_id: string, event_subtype: string, buyer: string, seller: string}`

**Processing:**

```
1. Notify buyer and seller hubs
2. Set severity = info
3. Create HubAlert record, dispatch notifications
```

**Output:** `{alert_id: string, recipients_notified: int}`

---

#### get-alert-history

Query past alerts by listing, provider, or type.

**Source:** Admin

**Input:** `{listing_id?: string, event_type?: string, limit?: int, offset?: int}`

**Output:** `{alerts: HubAlert[], total: int}`

**Side Effects:** None (read-only).

---

#### configure-rules

Set alert thresholds and routing rules.

**Source:** Admin

**Input:** `{rule: AlertRule}`

**Output:** `{rule_id: string, created: bool}`

**Side Effects:** Writes to alert_rules store.

---

#### mute-listing

Suppress alerts for a listing during known maintenance.

**Source:** Admin

**Input:** `{listing_id: string, reason: string, duration: int}`

**Output:** `{mute_id: string, expires_at: int64}`

**Side Effects:** Writes to alert_mutes store.

---

## Execute Workflow

The hub agent routes incoming tasks to subsystems based on action name
and event topic. Each subsystem has its own processing loop.

### Task Router

```
Phase 1 — Receive Task
  Accept event from bus or direct message
  Parse action name and payload
  Route to subsystem:
    index-listing, remove-listing, crawl-*, get-listing,
      prune-stale, reindex                           → Indexing
    search, browse, trending, recommend,
      autocomplete, get-facets                       → Search
    record-*, probe-*, get-metrics*, get-aggregate   → Metrics
    verify-*, fingerprint-*, classify-change          → Verification
    notify-*, get-alert-history, configure-rules,
      mute-listing                                   → Alerting

Phase 2 — Execute Subsystem Action
  Dispatch to appropriate action handler
  Each handler follows its defined Processing steps
  Record result

Phase 3 — Cross-Subsystem Coordination
  Indexing → emits hub.index.updated (invalidates search cache)
  Indexing → emits hub.listing.indexed (metrics starts tracking)
  Indexing → calls verify-listing internally for signature checks
  Metrics → emits hub.sla.breach (alerting sends notifications)
  Verification → emits hub.behavioral.change (alerting sends notifications)
  Verification → emits hub.verification.failure (alerting sends notifications)
  Verification → emits hub.listing.suspended (alerting sends notifications)
```

### Indexing Loop (scheduled)

```
Phase 1 — Acquire crawl lock
Phase 2 — Crawl all known providers (up to max_concurrent_crawls)
Phase 3 — Verify signatures on each listing
Phase 4 — Index verified listings, reject invalid
Phase 5 — Evaluate stale listings, prune past grace period
Phase 6 — Release crawl lock, emit metrics
```

### Probe Cycle (every 5 minutes)

```
Phase 1 — Acquire probe lock
Phase 2 — Query active listings
Phase 3 — HEAD probe each listing (up to max_concurrent_probes)
Phase 4 — Record probe results
Phase 5 — SLA evaluation: check uptime/error thresholds
Phase 6 — Release probe lock, emit metrics
```

### Aggregation Cycle (hourly)

```
Phase 1 — For each active listing: compute ListingAggregate per window
Phase 2 — Compute NetworkAggregate
Phase 3 — Retention cleanup: prune data beyond retention policies
Phase 4 — Emit storage metrics
```

### Fingerprint Cycle (every 4 hours)

```
Phase 1 — Acquire fingerprint lock
Phase 2 — For each listing (up to max_concurrent_fingerprint_probes):
           Send deterministic test input, record response
Phase 3 — Compare to baseline, classify changes
Phase 4 — Emit behavioral change events for NOTABLE+
Phase 5 — Store new fingerprints, release lock
```

### Alert Processing (continuous)

```
Phase 1 — Receive hub event (behavioral change, SLA breach, etc.)
Phase 2 — Evaluate suppression (dedup, mute, flapping)
Phase 3 — Resolve recipients and channels
Phase 4 — Create HubAlert record
Phase 5 — Dispatch to alerting agent (local) and federation (cross-hub)
Phase 6 — Record delivery result, emit metrics
```

---

## Collaboration

```yaml
events_published:
  # Indexing events
  - topic: hub.index.updated
    payload: {listing_id, operation, provider}
    when: Index entry added, updated, or removed

  - topic: hub.listing.indexed
    payload: {listing_id, provider, capability, version}
    when: New listing successfully indexed

  - topic: hub.provider.stale
    payload: {hub_name, miss_count, last_seen}
    when: Provider marked as stale

  # Metrics events
  - topic: hub.sla.breach
    payload: {listing_id, metric, threshold, actual}
    when: Listing metrics fall below SLA thresholds

  - topic: hub.metrics.updated
    payload: {listing_id, window, computed_at}
    when: Rolling aggregates recomputed for a listing

  # Verification events
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

  # Alerting events
  - topic: hub_alert.delivered
    payload: {alert_id, listing_id, event_type, recipients_notified}
    when: Alert successfully delivered to all recipients

  - topic: hub_alert.delivery.failed
    payload: {alert_id, listing_id, event_type, error}
    when: Alert delivery failed after retries

  - topic: hub_alert.suppressed
    payload: {alert_id, listing_id, reason}
    when: Alert suppressed by dedup, mute, or flapping rule

events_subscribed:
  - topic: hub.listing.publish
    payload: {listing_id, provider, listing_data}
    action: index-listing

  - topic: hub.listing.delist
    payload: {listing_id, provider}
    action: remove-listing

  - topic: hub.provider.register
    payload: {hub_name, federation_url, public_key}
    action: Register provider, trigger initial crawl

  - topic: federation.task.completed
    payload: {listing_id, latency_ms, status, data_bytes_in, data_bytes_out}
    action: record-invocation

  - topic: federation.task.failed
    payload: {listing_id, error, timestamp}
    action: record-error

  - topic: hub.listing.indexed
    payload: {listing_id, provider}
    action: Start tracking metrics for new listing

  - topic: hub.verify.behavioral_change
    payload: {listing_id, level, timestamp}
    action: record-behavioral-change (metrics)

  - topic: federation.key.rotated
    payload: {hub_name, old_key, new_key, old_signature, new_signature}
    action: verify-key-rotation

  - topic: hub.verify.request
    payload: {target_type, target_id, data}
    action: Route to appropriate verify action

  - topic: hub.behavioral.change
    payload: {listing_id, level, details}
    action: notify-behavioral-change

  - topic: hub.verification.failure
    payload: {listing_id, provider, reason}
    action: notify-verification-failure

  - topic: hub.sla.breach
    payload: {listing_id, metric, threshold, actual}
    action: notify-sla-breach

  - topic: hub.listing.suspended
    payload: {listing_id, reason}
    action: notify-listing-suspension

  - topic: hub.peer.revoked
    payload: {hub_name, reason}
    action: notify-peer-revocation

  - topic: hub.marketplace.event
    payload: {listing_id, event_subtype, buyer, seller}
    action: notify-marketplace-event

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "hub"
    action: Self-update procedure

direct_messages:
  - target: alerting
    action: send-notification
    when: Delegating notification delivery
    reason: Hub agent determines what to notify; alerting handles how
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     All subsystems operate autonomously
  supervised:    Bulk operations, muting, rule changes require operator
  manual-only:   All operations require operator trigger

overridable_behaviors:
  # Indexing
  - behavior: automatic_crawling
    default: enabled
    override: Set WL_HUB_INDEX_CRAWL_ENABLED=false
    audit: logged

  - behavior: automatic_pruning
    default: enabled
    override: Set stale_grace_period to very high value
    audit: logged

  # Metrics
  - behavior: automatic_probing
    default: enabled
    override: Set WL_HUB_METRICS_PROBES_ENABLED=false
    audit: logged

  - behavior: automatic_aggregation
    default: enabled
    override: Set WL_HUB_METRICS_AGG_ENABLED=false
    audit: logged

  - behavior: sla_breach_detection
    default: enabled
    override: Set sla_uptime_threshold = 0
    audit: logged

  # Verification
  - behavior: automatic_fingerprinting
    default: enabled
    override: Set WL_HUB_VERIFY_FINGERPRINT_ENABLED=false
    audit: logged

  - behavior: automatic_suspension
    default: enabled
    override: Set WL_HUB_VERIFY_AUTO_SUSPEND=false
    audit: logged
    note: CRITICAL changes will still be flagged but not auto-suspended

  # Alerting
  - behavior: automatic_deduplication
    default: enabled
    override: Set config.dedup_window = 0
    audit: logged

  - behavior: automatic_flapping_consolidation
    default: enabled
    override: Set config.flapping_threshold to high value
    audit: logged

  - behavior: federation_notifications
    default: enabled
    override: Disable via WL_HUB_ALERT_FED_ENABLED=false
    audit: logged

  # System
  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  # Indexing
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

  # Metrics
  - action: recompute
    description: Force recompute of all rolling aggregates
    allowed: operator

  - action: probe-all
    description: Trigger immediate probe cycle
    allowed: operator

  - action: purge-old-data
    description: Force retention cleanup
    allowed: operator

  # Verification
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

  # Alerting
  - action: mute-listing
    description: Suppress alerts for a listing during maintenance
    allowed: operator

  - action: configure-rules
    description: Create or modify alert routing rules
    allowed: operator

  - action: force-notify
    description: Send immediate notification bypassing dedup/mute
    allowed: operator

  - action: clear-mutes
    description: Remove all active mutes
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
    - MUST NOT modify provider hub data — index is a read-only mirror
    - MUST NOT accept listings without valid Ed25519 signature
    - MUST NOT fabricate or alter metrics data
    - MUST NOT send notifications to hubs not in collaborator registry
    - Crawl rate bounded by config.max_concurrent_crawls
    - Probe rate bounded by config.max_concurrent_probes
    - Notification rate bounded by config.max_batch_size per dispatch cycle

  forbidden_actions:
    - MUST NOT index unsigned or unverified listings
    - MUST NOT bypass Ed25519 signature verification for any reason
    - MUST NOT accept key rotations without dual-signature proof
    - MUST NOT accept key rotations within cooldown period
    - MUST NOT self-report provider metrics — only record observed data
    - MUST NOT skip probe results (even if unfavorable to providers)
    - MUST NOT expose raw invocation data to unauthorized consumers
    - MUST NOT expose provider private keys or internal state
    - MUST NOT send federation notifications without valid Ed25519 signature
    - MUST NOT bypass deduplication for non-operator callers

  resource_limits:
    memory: 1024 MB (process limit — consolidated from 5 agents)
    listing_index_rows: config.max_listings
    concurrent_crawls: config.max_concurrent_crawls
    concurrent_probes: config.max_concurrent_probes
    concurrent_fingerprints: config.max_concurrent_fingerprint_probes
    alert_history_rows: governed by config.alert_history_retention
    max_active_mutes: 10000
    outbound_per_minute: 500 notifications
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: SIGNATURE_INVALID
      description: Ed25519 signature verification failed
      subsystem: indexing, verification
    - code: SCHEMA_INVALID
      description: Listing schema validation failed
      subsystem: indexing
    - code: KEY_REVOKED
      description: Provider key is on revocation list
      subsystem: verification
    - code: COOLDOWN_NOT_SATISFIED
      description: Key rotation within cooldown period
      subsystem: verification
    - code: LISTING_NOT_FOUND
      description: Referenced listing not in index
      subsystem: search, alerting
    - code: INVALID_INPUT
      description: Malformed request payload
      subsystem: all

  transient:
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Queue operations, retry on recovery
      subsystem: all
    - code: CRAWL_TIMEOUT
      description: Provider did not respond within crawl_timeout
      fallback: Retry on next scheduled crawl, increment miss_count
      subsystem: indexing
    - code: PROBE_TIMEOUT
      description: Provider did not respond within probe_timeout
      fallback: Record as unavailable for this interval
      subsystem: metrics
    - code: DELIVERY_FAILED
      description: Notification delivery failed
      fallback: Queue locally, retry up to config.alert_retry_max
      subsystem: alerting
    - code: AGGREGATION_FAILED
      description: Rolling aggregate computation failed
      fallback: Retry on next scheduled run, serve stale data
      subsystem: metrics

error_handling_rules:
  - error: Signature verification failure
    handling: Reject item. Emit hub.verification.failure. Log with full context.
  - error: Invalid listing schema
    handling: Reject with validation errors. Do not index.
  - error: Provider unreachable during crawl
    handling: Log timeout. Increment miss_count. Retry on next crawl.
  - error: Provider unreachable during fingerprint
    handling: Skip this cycle. Flag if unreachable for 3+ cycles.
  - error: Key rotation without dual signature
    handling: Reject rotation. Flag as potential compromise. Emit alert.
  - error: Behavioral CRITICAL change
    handling: Immediately emit alert. Suspend listing pending review.
  - error: Invocation event malformed
    handling: Log and discard. Do not corrupt aggregates.
  - error: Collaborator unreachable
    handling: Queue notification. Retry 3 times with backoff. Log failure.
  - error: Alerting agent unavailable
    handling: Log alert locally. Retry when alerting recovers.
  - error: Rate limit on collaborator endpoint
    handling: Respect Retry-After header. Queue remaining notifications.
  - error: Storage full
    handling: Prune oldest hourly data beyond retention. Alert admin.
```

---

## Observability

```yaml
custom_log_types:
  # Indexing logs
  - log_type: hub.index.listing_indexed
    level: info
    fields: {listing_id, provider, version, operation}

  - log_type: hub.index.crawl_completed
    level: info
    fields: {hub_name, listings_found, listings_indexed, duration_ms}

  - log_type: hub.index.verification_failed
    level: warn
    fields: {listing_id, provider, reason}

  - log_type: hub.index.stale_pruned
    level: info
    fields: {pruned_count}

  # Search logs
  - log_type: hub.search.query
    level: debug
    fields: {query_id, q, filters, results_returned, duration_ms}

  # Metrics logs
  - log_type: hub.metrics.probe_cycle
    level: info
    fields: {probed, available, unavailable, duration_ms}

  - log_type: hub.metrics.sla_breach
    level: warn
    fields: {listing_id, metric, threshold, actual}

  - log_type: hub.metrics.aggregation
    level: debug
    fields: {listings_computed, duration_ms}

  # Verification logs
  - log_type: hub.verify.result
    level: info
    fields: {verification_id, target_type, target_id, result}

  - log_type: hub.verify.behavioral_change
    level: warn
    fields: {listing_id, level, change_details}

  - log_type: hub.verify.key_rotation
    level: info
    fields: {hub_name, result, dual_signature_valid}

  # Alerting logs
  - log_type: hub.alert.dispatched
    level: info
    fields: {alert_id, listing_id, event_type, severity, recipients}

  - log_type: hub.alert.suppressed
    level: debug
    fields: {alert_id, listing_id, reason}

  - log_type: hub.alert.delivery_failed
    level: warn
    fields: {alert_id, listing_id, error}

metrics:
  # Indexing metrics
  - name: hub_index_listings_total
    type: gauge
    labels: [status]
    description: Total listings in index by status

  - name: hub_index_providers_total
    type: gauge
    description: Total known providers

  - name: hub_index_operations_total
    type: counter
    labels: [operation]
    description: Index operations (add, update, remove, prune)

  - name: hub_index_crawl_duration_seconds
    type: histogram
    description: Time to crawl a provider

  - name: hub_index_verification_failures_total
    type: counter
    description: Signature verification failures during indexing

  - name: hub_index_stale_listings
    type: gauge
    description: Currently stale listings

  # Search metrics
  - name: hub_search_queries_total
    type: counter
    labels: [type]
    description: Search queries by type (search, browse, trending, autocomplete)

  - name: hub_search_duration_seconds
    type: histogram
    description: Query execution time

  - name: hub_search_cache_hits_total
    type: counter
    description: Query result cache hits

  # Metrics subsystem metrics
  - name: hub_metrics_invocations_recorded_total
    type: counter
    description: Invocation events recorded

  - name: hub_metrics_probes_total
    type: counter
    labels: [result]
    description: Availability probes by result (up/down)

  - name: hub_metrics_probe_duration_seconds
    type: histogram
    description: Probe response time

  - name: hub_metrics_aggregation_duration_seconds
    type: histogram
    description: Time to recompute rolling aggregates

  - name: hub_metrics_storage_bytes
    type: gauge
    description: Total metrics storage size

  # Verification metrics
  - name: hub_verify_operations_total
    type: counter
    labels: [type, result]
    description: Verifications by type and result

  - name: hub_verify_duration_seconds
    type: histogram
    description: Verification execution time

  - name: hub_verify_signature_failures_total
    type: counter
    description: Signature verification failures

  - name: hub_verify_behavioral_changes_total
    type: counter
    labels: [level]
    description: Behavioral changes detected by level

  - name: hub_verify_fingerprints_total
    type: gauge
    description: Active behavioral fingerprints

  # Alerting metrics
  - name: hub_alert_notifications_total
    type: counter
    labels: [type, severity, channel]
    description: Notifications by type, severity, and channel

  - name: hub_alert_delivery_duration_seconds
    type: histogram
    description: Time to deliver notification

  - name: hub_alert_suppressed_total
    type: counter
    labels: [reason]
    description: Deduplicated or muted alerts

  - name: hub_alert_delivery_failures_total
    type: counter
    description: Failed notification deliveries

alerts:
  - condition: Signature verification failures > 10 in 1 hour
    severity: critical
    routing: alerting agent

  - condition: Storage errors for 3+ consecutive cycles
    severity: critical
    routing: alerting agent

  - condition: SLA breaches for multiple listings simultaneously
    severity: high
    routing: alerting agent

  - condition: Probe failure rate > 50% of tracked listings
    severity: high
    routing: alerting agent

  - condition: Aggregation stale (missed 2+ scheduled cycles)
    severity: warn
    routing: alerting agent

  - condition: CRITICAL behavioral change detected
    severity: critical
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send messages to alerting agent and respond to queries

    - capability: http:send
      resources: ["https://*"]
      description: Crawl provider federation endpoints, probe availability,
                   behavioral fingerprinting, federation notifications

    - capability: database:read
      resources: [listing_index, provider_registry, metrics_store,
                  verification_log, behavioral_fingerprints,
                  search_analytics, alert_rules, alert_history]
      description: Read all hub data stores

    - capability: database:write
      resources: [listing_index, provider_registry, metrics_store,
                  verification_log, behavioral_fingerprints,
                  search_analytics, alert_history]
      description: Write to all hub data stores

    - capability: crypto:verify
      resources: [ed25519]
      description: Verify signatures on listings, manifests, key rotations,
                   and data contracts

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

    - data: Invocation records
      classification: medium
      handling: Contains usage patterns — encrypted at rest, aggregated before serving

    - data: Probe results
      classification: low
      handling: Availability is public information per marketplace transparency

    - data: Listing aggregates
      classification: low
      handling: Public metrics — served to marketplace and consumer hubs

    - data: Verification results
      classification: medium
      handling: Contains pass/fail decisions — logged and queryable by admin

    - data: Behavioral fingerprints
      classification: medium
      handling: Contains response structure analysis — encrypted at rest

    - data: Revocation list
      classification: high
      handling: Key revocations affect trust decisions — integrity-critical

    - data: Alert payloads
      classification: medium
      handling: May contain listing details — encrypted at rest

    - data: Collaborator contact info
      classification: medium
      handling: Federation URLs and operator contacts — encrypted at rest

    - data: Federation notification signatures
      classification: high
      handling: Ed25519 private key never logged or transmitted

  access_control:
    # Indexing
    - caller: Provider hub (authenticated via federation)
      actions: [index-listing, remove-listing]

    # Search
    - caller: Consumer hub (authenticated)
      actions: [search, browse, trending, recommend, autocomplete, get-facets,
                get-metrics, get-metrics-history, verify-data-contract,
                get-fingerprint]

    - caller: Marketplace
      actions: [search, browse, trending, autocomplete, get-facets,
                get-metrics, get-aggregate]

    # Metrics
    - caller: Federation layer
      actions: [record-invocation, record-error]

    # Verification
    - caller: Federation layer
      actions: [verify-key-rotation]

    # Admin
    - caller: Cron agent
      actions: [crawl-all, prune-stale, probe-all, fingerprint-behavior]

    - caller: Operator (auth token with operator role)
      actions: [crawl-provider, crawl-all, reindex, prune-stale,
                probe-all, recompute, purge-old-data,
                bulk-verify, add-to-revocation-list, force-fingerprint,
                override-suspension, get-verification-log,
                get-alert-history, configure-rules, mute-listing,
                force-notify, clear-mutes]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Indexing — Happy Path

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
      - Search cache invalidated
      - Metrics tracking started
```

### Search — Query with Facets

```yaml
  - name: Full-text search with facets
    action: search
    input:
      q: "seo audit"
      tier: pro
      min_uptime: 99.0
      sort: relevance
      page: 1
      per_page: 20
    expected:
      results: [...]
      total: 12
      facets: {domains: {seo: 8, security: 4}}
    validates:
      - Results ranked by relevance
      - Facets computed from matching results
      - SearchAnalyticsEntry recorded
```

### Metrics — SLA Breach Detection

```yaml
  - name: SLA breach triggers alert
    action: probe-availability
    condition: Listing uptime drops below config.sla_uptime_threshold
    expected: hub.sla.breach event emitted
    validates:
      - ProbeResult recorded with available = false
      - Alerting subsystem receives breach notification
      - Consumer hub admins notified
```

### Verification — Dual-Signature Key Rotation

```yaml
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
      - All provider listings re-verified with new key
      - Cooldown period checked
```

### Alerting — Deduplication and Muting

```yaml
  - name: Critical alert bypasses mute
    action: notify-behavioral-change
    input:
      listing_id: "<muted-listing>"
      level: CRITICAL
      details: {change_summary: "Unexpected error rate spike to 50%"}
    expected:
      alert_id: "<uuid-v7>"
      recipients_notified: 5
      suppressed: false
    validates:
      - CRITICAL severity bypasses mute suppression
      - All collaborators and registry operators notified
      - Federation notifications sent with Ed25519 signature
```

---

## Implementation Notes

- **Unified identity**: The hub agent uses a single Ed25519 keypair
  for all subsystems. This eliminates cross-agent authentication
  overhead and simplifies key management.

- **Subsystem coordination**: Subsystems communicate internally via
  direct function calls, not message bus events. When the verification
  subsystem detects a behavioral change, it directly invokes the
  alerting subsystem — no IPC latency. Events are still emitted to
  the bus for external consumers.

- **Signature-first**: Every listing MUST pass Ed25519 verification
  before indexing. No exceptions, no override. This is the core trust
  property of the hub network.

- **Observed metrics, not reported**: Metrics are derived from actual
  federated task execution and active probing — never from provider
  self-reports. This is the trust foundation of marketplace transparency.

- **Deterministic fingerprinting**: Behavioral fingerprinting uses
  capability-specific deterministic test inputs. The same input always
  produces the same test conditions, making change detection reliable.

- **Change classification conservatism**: When in doubt, classify
  higher. A change that could be NOTABLE or BREAKING should be
  classified as BREAKING. False positives are preferable to missed
  breaking changes.

- **Mute safety**: CRITICAL alerts always bypass mutes. This prevents
  operators from accidentally silencing security-critical events.

- **Delegation model for alerting**: The hub agent determines _who_
  and _when_ to notify. The external alerting agent handles _how_
  (channel selection, formatting, delivery). This keeps hub logic
  focused.

- **Stale grace periods**: Providers go offline temporarily. The
  72-hour unreachable threshold and 7-day archive grace period
  prevent premature removal of valid listings.

- **Shared storage**: All subsystems share the same SQLite database.
  This eliminates cross-agent storage coordination and enables
  transactional consistency across subsystems (e.g., index a listing
  and start metrics tracking in one transaction).

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
      mechanism: operation locks in storage (crawl_lock, probe_lock, fingerprint_lock)
      leader: [crawl-all, probe-all, fingerprint-behavior cycle,
               aggregation, retention cleanup, prune-stale]
      follower: [index-listing, search, get-metrics, verify-listing,
                 notify-*, health reporting]
      promotion: automatic when lock expires
    state_sharing:
      mechanism: shared sqlite database
      conflict_resolution: >
        Listing uq_listing_id constraint prevents duplicates.
        Operation locks prevent duplicate scheduled cycles.
        Invocation and verification records are append-only.
        Alert deduplication uses alert_history table — first writer wins.

  event_handling:
    consumer_group: hub
    delivery: one-per-group
    description: >
      Bus delivers each event to ONE instance in the hub consumer
      group. Prevents duplicate event processing across instances.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 10
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same database. Schema migrations are
      additive-only during shadow phase. Destructive steps execute
      only after cutover confirmation.
```

---

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Listings are signature-verified before indexing (no exceptions)
- [ ] Invalid signatures are rejected and logged
- [ ] Crawl discovers and indexes all provider listings
- [ ] Stale listings are pruned after grace period
- [ ] Full-text search returns ranked, paginated results with facets
- [ ] Search cache invalidated on index changes
- [ ] Availability probes run on schedule for all active listings
- [ ] Rolling aggregates computed correctly for all windows (1h, 24h, 7d, 30d)
- [ ] SLA breach detection triggers alerts within one probe cycle
- [ ] Ed25519 signatures verified for listings, manifests, and key rotations
- [ ] Key rotation requires valid dual-signature proof
- [ ] Behavioral fingerprints sampled on schedule with change classification
- [ ] CRITICAL changes trigger immediate listing suspension
- [ ] Behavioral change notifications reach all active collaborators
- [ ] Deduplication prevents repeated alerts within suppression window
- [ ] Muted listings suppress non-CRITICAL alerts
- [ ] CRITICAL alerts bypass mute suppression
- [ ] Cross-hub notifications use federation protocol with Ed25519 signatures
- [ ] Revoked keys are rejected immediately
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] State machine validates all entity transitions
- [ ] Startup sequence initializes all 5 subsystems with pre-check/validates/on-fail
- [ ] Shutdown drains all in-flight operations before exit
- [ ] Configuration values validated against declared constraints
- [ ] Override audit records who, what, when, why
- [ ] Scaling: operation locks prevent duplicate scheduled cycles
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Blue-green: shadow phase validates events without side effects
