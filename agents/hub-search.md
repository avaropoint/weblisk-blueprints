<!-- blueprint
type: agent
kind: infrastructure
name: hub-search
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/hub]
platform: any
tier: free
port: 9771
-->

# Hub Search Agent

Handles discovery queries against the hub's listing index. Provides
ranked, filtered search over published capabilities for consumer hubs,
the marketplace UI, and the CLI.

## Overview

The hub-search agent sits between the listing index (maintained by
hub-index) and consumers looking for capabilities. It handles the
`GET /v1/hub/search` endpoint defined in the hub architecture,
providing full-text search, faceted filtering, relevance ranking,
and result pagination.

For marketplace scenarios, the search agent also supports browsing
by category, trending listings, and recommended capabilities based
on the querying hub's existing domains.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "database:read", "resources": ["listing_index", "search_analytics"]},
    {"name": "database:write", "resources": ["search_analytics"]}
  ],
  "inputs": [
    {"name": "search_query", "type": "json", "description": "Search parameters — filters, sort, pagination"}
  ],
  "outputs": [
    {"name": "search_results", "type": "json", "description": "Ranked listing results with facets"}
  ],
  "collaborators": ["hub-index"]
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
          fields_used: [listing_id, provider, capability, tier, metrics, pricing]
        - name: MetricsInfo
          fields_used: [uptime_30d, p95_latency_30d_ms, total_invocations_30d, error_rate_30d]
        - name: SearchQuery
          fields_used: [q, domain, action, tier, jurisdiction, min_uptime,
                        max_latency, max_price, sort, page, per_page]
        - name: SearchResult
          fields_used: [results, total, page, per_page, facets]
      events:
        - topic: hub.index.updated
          fields_used: [listing_id, operation]
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
  # Hub-search reads from listing_index (maintained by hub-index)
  # but operates independently. If hub-index is down, search serves
  # cached results or stale index data.
```

---

## Configuration

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

---

## Types

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
        description: Maximum unit price
      category:
        type: string
        optional: true
        description: Marketplace category tag
      provider:
        type: string
        optional: true
        description: Filter by provider hub name
      sort:
        type: string
        enum: [relevance, uptime, latency, price, invocations, newest]
        default: relevance
        description: Sort order
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

  SearchResultEntry:
    description: Single search result
    fields:
      listing_id:
        type: string
        description: Listing identifier
      provider:
        type: object
        description: Provider info (hub_name, verified status)
      capability:
        type: object
        description: Capability definition (domain, action, version)
      tier:
        type: string
        enum: [free, pro]
        description: Availability tier
      pricing:
        type: object
        optional: true
        description: Pricing model and unit price
      metrics:
        type: object
        description: Listing metrics (uptime, latency)
      relevance_score:
        type: float
        min: 0.0
        max: 1.0
        description: Relevance score for this result

  SearchResponse:
    description: Complete search response
    fields:
      results:
        type: array
        items: SearchResultEntry
        description: Ranked search results
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
        description: Available filter facets with counts

  SearchAnalyticsEntry:
    description: Search query analytics record
    fields:
      query_id:
        type: string
        format: uuid-v7
        description: Unique query identifier
      query_text:
        type: string
        optional: true
        description: Search text (anonymized)
      filters_used:
        type: array
        items: string
        description: Which filters were applied
      result_count:
        type: int
        description: Number of results returned
      duration_ms:
        type: int
        description: Query execution time
      timestamp:
        type: int64
        auto: true
        description: When query was executed
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
        trigger: index_accessible
        validates: listing_index readable, cache initialized
      - from: active
        to: searching
        trigger: query_received
        validates: query parsed and validated
      - from: searching
        to: active
        trigger: query_complete
        validates: results returned or timeout
      - from: active
        to: degraded
        trigger: index_unavailable
        validates: listing_index read failed after retries
      - from: degraded
        to: active
        trigger: index_recovered
        validates: listing_index readable
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in-flight queries completed or timed out
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
  Action:      Load Ed25519 keypair from .weblisk/keys/hub-search/
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema
  Validates:   search_analytics table exists
  On Fail:     Run migration → if fails EXIT with STORAGE_UNREACHABLE

Step 4 — Verify Index Access
  Action:      Test read from listing_index (owned by hub-index)
  Validates:   Query returns without error
  On Fail:     Enter degraded state — will serve empty results

Step 5 — Initialize Cache
  Action:      Allocate in-memory cache structures
  Validates:   Cache allocated within memory limits
  On Fail:     Continue without cache — all queries hit index directly

Step 6 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 7 — Subscribe to Events
  Action:      Subscribe to hub.index.updated, hub.search, hub.browse,
               hub.recommend, system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9771, cache_size: N, index_listings: M}
```

### Shutdown Sequence

```
Step 1 — Stop Accepting Queries
  Action:      Return 503 for new search requests
  agent_state → retiring

Step 2 — Drain In-Flight Queries
  Action:      Wait for active queries to complete (up to 15s)
  On Timeout:  Return partial results for remaining queries

Step 3 — Flush Analytics
  Action:      Write pending search analytics to storage

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Close Storage
  Action:      Close database connection

Step 6 — Exit
  Log: lifecycle.stopped {uptime_seconds, queries_drained}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - listing_index readable
      - event subscriptions active
      - cache operational
    response:
      status: healthy
      details: {index_access, cache_hit_ratio, cache_entries,
                queries_per_minute, subscriptions}

  degraded:
    conditions:
      - listing_index unreachable (serving cached results)
      - cache disabled or corrupted
      - high query latency (>5s average)
    response:
      status: degraded
      details: {reason, cache_status, avg_query_ms}

  unhealthy:
    conditions:
      - listing_index unreachable AND cache empty
      - storage unreachable
    response:
      status: unhealthy
      details: {reason, since}
```

### Self-Update

```
Step 1 — Validate new blueprint, verify version is newer
Step 2 — Compare Types block against current storage schema
Step 3 — Pause query processing → run migration → clear cache → resume
Step 4 — Reload configuration
Log: lifecycle.version_updated {from, to}
```

---

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.search` | Search query from consumer hub, marketplace, or CLI |
| Event: `hub.browse` | Category browse request from marketplace |
| Event: `hub.recommend` | Recommendation request based on hub profile |
| Event: `hub.index.updated` | Index changed — invalidate search cache |

---

## Actions

### search

Full search with filters, sort, and pagination.

**Source:** Consumer Hub / Marketplace / CLI

**Input:** `SearchRequest`

**Processing:**

```
1. Validate input against SearchRequest type constraints
2. Check query result cache — if hit, return cached result
3. Build query against listing_index:
   a. Apply text search on q field
   b. Apply filters: domain, action, tier, jurisdiction, provider, category
   c. Apply metric filters: min_uptime, max_latency, max_price
4. Score and rank results per Relevance Ranking model
5. Apply sort order (relevance, uptime, latency, price, invocations, newest)
6. Apply pagination (page, per_page)
7. Compute facets from matching result set
8. Cache result with config.query_result_cache_ttl
9. Record SearchAnalyticsEntry
10. Return SearchResponse
```

**Output:** `SearchResponse`

**Errors:** `INVALID_QUERY` (permanent), `INDEX_UNAVAILABLE` (transient), `QUERY_TIMEOUT` (transient)

---

### browse

Browse listings by category/domain.

**Source:** Marketplace

**Input:** `{category?: string, domain?: string, page?: int, per_page?: int}`

**Output:** `SearchResponse` — pre-filtered by category or domain

---

### trending

Top listings by recent invocation volume.

**Source:** Marketplace

**Input:** `{limit?: int}` — default 10, max 50

**Output:** `{listings: SearchResultEntry[]}`

---

### recommend

Suggested capabilities based on hub's existing domains.

**Source:** Consumer Hub

**Input:** `{hub_domains: string[], limit?: int}`

**Processing:**

```
1. Analyze hub's existing domains
2. Find complementary capabilities in index
3. Rank by relevance to existing domain portfolio
4. Exclude capabilities the hub already uses
```

**Output:** `{recommendations: SearchResultEntry[]}`

---

### autocomplete

Prefix search for domain and action names.

**Source:** Marketplace / CLI

**Input:** `{prefix: string, limit?: int}` — limit default 10

**Output:** `{suggestions: [{text: string, type: string, count: int}]}`

---

### get-facets

Available filter values (domains, tiers, jurisdictions).

**Source:** Marketplace

**Input:** `{}`

**Output:** `{facets: {domains: [{name, count}], tiers: [{name, count}], jurisdictions: [{name, count}]}}`

---

### invalidate-cache

Clear cached results after index update.

**Source:** Hub Index

**Input:** `{listing_id?: string}` — if omitted, clear all caches

**Output:** `{cleared: true}`

---

### get-search-stats

Query volume, popular searches, cache hit ratio.

**Source:** Admin

**Input:** `{period?: string}` — default "24h"

**Output:** `{total_queries: int, popular_terms: string[], cache_hit_ratio: float, avg_duration_ms: int}`

---

## Search Parameters

The search agent implements the query interface defined in
`architecture/hub.md`:

| Parameter | Type | Description |
|-----------|------|-------------|
| q | string | Free-text search across listing fields |
| domain | string | Filter by domain name |
| action | string | Filter by capability action |
| tier | string | `"free"`, `"pro"`, or `"all"` (default: `"all"`) |
| jurisdiction | string | ISO 3166-1 country code |
| min_uptime | float | Minimum 30-day uptime percentage |
| max_latency | int | Maximum p95 latency in ms |
| max_price | float | Maximum unit price (for per_invocation pricing) |
| category | string | Marketplace category tag |
| provider | string | Filter by provider hub name |
| sort | string | `"relevance"`, `"uptime"`, `"latency"`, `"price"`, `"invocations"`, `"newest"` |
| page | int | Page number (default: 1) |
| per_page | int | Results per page (default: 20, max: 100) |

---

## Relevance Ranking

When `sort = "relevance"` (default), results are ranked by:

| Signal | Weight | Description |
|--------|--------|-------------|
| Text match | 40% | How well the listing matches the query text |
| Uptime | 20% | 30-day availability — higher is better |
| Invocations | 15% | 30-day usage volume — social proof |
| Latency (inverse) | 10% | Lower latency scores higher |
| Behavioral stability | 10% | Fewer behavioral changes scores higher |
| Recency | 5% | More recently updated listings score higher |

---

## Search Response

```json
{
  "results": [
    {
      "listing_id": "avaropoint:seo-audit",
      "provider": {"hub_name": "avaropoint-prod", "verified": true},
      "capability": {"domain": "seo", "action": "audit", "version": "1.2.0"},
      "tier": "pro",
      "pricing": {"model": "per_invocation", "unit_price": 0.05},
      "metrics": {"uptime_30d": 99.95, "p95_latency_30d_ms": 3200},
      "relevance_score": 0.92
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20,
  "facets": {
    "domains": [{"name": "seo", "count": 15}, {"name": "security", "count": 8}],
    "tiers": [{"name": "free", "count": 28}, {"name": "pro", "count": 14}],
    "jurisdictions": [{"name": "US", "count": 20}, {"name": "EU", "count": 12}]
  }
}
```

---

## Caching

Search results are cached in memory with a short TTL to handle
repeated queries without re-reading the index:

| Cache Layer | TTL | Invalidation |
|------------|-----|-------------|
| Query result cache | 60 seconds | On index update notification |
| Facet cache | 5 minutes | On index update notification |
| Trending cache | 15 minutes | On metrics refresh |
| Autocomplete index | 30 minutes | On index update notification |

---

## Execute Workflow

The core search query processing loop:

```
Phase 1 — Parse and Validate
  Accept search query from event bus or direct message
  Validate against SearchRequest type constraints
  Normalize text query (lowercase, trim, sanitize)
  If invalid → return 400 with specific validation errors

Phase 2 — Cache Lookup
  Compute cache key from normalized query + filters + sort + page
  Check query result cache → if hit, return cached result
  Check facet cache → if hit, attach cached facets

Phase 3 — Index Query
  Build query against listing_index:
    Text search: tokenize q, match against listing fields
    Filters: apply all specified filters as WHERE clauses
    Metric filters: join with metrics data, apply thresholds
  Set query timeout: config.query_timeout
  If timeout → return partial results with truncated: true

Phase 4 — Scoring and Ranking
  For each matching listing:
    Compute relevance_score using weighted signals
    Apply sort order
  If sort != relevance: sort by specified field

Phase 5 — Pagination
  Apply page and per_page to sorted results
  Compute total matching count
  Validate page doesn't exceed total pages

Phase 6 — Facet Computation
  Aggregate facets from full result set (pre-pagination):
    domains: count by domain
    tiers: count by tier
    jurisdictions: count by jurisdiction

Phase 7 — Cache and Record
  Store result in query result cache
  Record SearchAnalyticsEntry (query text, filters, result count, duration)
  Return SearchResponse
```

---

## Collaboration

```yaml
events_published:
  - topic: hub.search.completed
    payload: {query_id, result_count, duration_ms}
    when: Search query completed

  - topic: hub.search.trending.updated
    payload: {top_listings}
    when: Trending cache refreshed

events_subscribed:
  - topic: hub.search
    payload: SearchRequest
    action: search

  - topic: hub.browse
    payload: {category, domain}
    action: browse

  - topic: hub.recommend
    payload: {hub_domains}
    action: recommend

  - topic: hub.index.updated
    payload: {listing_id, operation}
    action: invalidate-cache

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "hub-search"
    action: Self-update procedure

direct_messages:
  - target: hub-index
    action: get-listing
    when: Fetching full listing details for search results
    reason: Search index may contain summary data; full details from hub-index

  - target: hub-metrics
    action: get-metrics
    when: Enriching search results with live metrics
    reason: Metrics freshness affects relevance ranking
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Search, caching, and analytics are fully autonomous
  supervised:    Cache clearing and ranking weight changes require operator
  manual-only:   Not applicable — search is a read-only service

overridable_behaviors:
  - behavior: query_result_caching
    default: enabled
    override: Set config.query_result_cache_ttl = 0
    audit: logged

  - behavior: search_analytics
    default: enabled
    override: Set WL_HUB_SEARCH_ANALYTICS_ENABLED=false
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: invalidate-cache
    description: Force clear all search caches
    allowed: operator

  - action: get-search-stats
    description: View search analytics and performance
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
    - MUST NOT modify listing_index — read-only access
    - MUST NOT modify listing data or metrics
    - Query rate bounded by available memory for caching

  forbidden_actions:
    - MUST NOT write to listing_index (owned by hub-index)
    - MUST NOT fabricate search results or rankings
    - MUST NOT log raw search queries containing PII
    - MUST NOT return results for listings with status != active

  resource_limits:
    memory: 512 MB (process limit, includes cache)
    max_cache_entries: config.max_cache_entries
    max_results_per_page: config.max_results_per_page
    query_timeout: config.query_timeout
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Index unavailable | Return cached results if available, else 503 |
| Malformed query | Return 400 with specific validation errors |
| Timeout on large result set | Return partial results with `truncated: true` |
| Cache corruption | Clear cache, serve from index directly |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_search_queries_total | counter | Search queries by type (search, browse, recommend) |
| hub_search_duration_seconds | histogram | Query execution time |
| hub_search_results_total | histogram | Result count per query |
| hub_search_cache_hit_ratio | gauge | Cache hit percentage |
| hub_search_empty_results_total | counter | Queries returning zero results |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Respond to search queries and request data from hub-index

    - capability: database:read
      resources: [listing_index, search_analytics]
      description: Read listing index and search analytics

    - capability: database:write
      resources: [search_analytics]
      description: Write search query analytics

  data_sensitivity:
    - data: Search queries
      classification: medium
      handling: Query text may reveal business intent — anonymize in analytics

    - data: Search results
      classification: low
      handling: Listing data is public by design

    - data: Search analytics
      classification: medium
      handling: Aggregated query patterns — no PII stored

    - data: Relevance scores
      classification: low
      handling: Computed values, not sensitive

  access_control:
    - caller: Consumer hub (authenticated)
      actions: [search, browse, recommend, autocomplete, get-facets]

    - caller: Marketplace UI (authenticated)
      actions: [search, browse, trending, autocomplete, get-facets]

    - caller: CLI (authenticated)
      actions: [search, autocomplete]

    - caller: hub-index
      actions: [invalidate-cache]

    - caller: Operator (auth token with operator role)
      actions: [search, browse, trending, recommend, autocomplete,
                get-facets, invalidate-cache, get-search-stats]

    - caller: Unauthenticated
      actions: []
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Text search returns relevant results
    action: search
    input:
      q: "seo audit"
      tier: all
      sort: relevance
      page: 1
      per_page: 20
    expected:
      total: ">0"
      results: [{listing_id: "avaropoint:seo-audit", relevance_score: ">0.8"}]
    validates:
      - Results ranked by relevance
      - Facets computed from result set
      - SearchAnalyticsEntry recorded

  - name: Filter by domain and tier
    action: search
    input: {domain: "security", tier: "pro"}
    expected:
      results: "all results have domain=security and tier=pro"
    validates:
      - Filters applied correctly
      - No free-tier results in output

  - name: Browse by category
    action: browse
    input: {category: "analytics"}
    expected:
      total: ">0"
    validates:
      - Results filtered by category
```

### Error Cases

```yaml
  - name: Malformed query parameters
    action: search
    input: {per_page: 999, page: -1}
    expected_error: INVALID_QUERY
    validates: Validation catches out-of-range parameters

  - name: Index unavailable with cache
    action: search
    condition: listing_index unreachable, cache populated
    expected: Cached results returned with stale indicator
    validates: Graceful degradation to cached data
```

### Edge Cases

```yaml
  - name: Empty query returns browsable results
    action: search
    input: {q: ""}
    expected: {total: ">0"}
    validates: Empty query is not an error — returns all listings

  - name: Pagination beyond result set
    action: search
    input: {q: "seo", page: 1000}
    expected: {results: [], total: 42}
    validates: Empty page returned, total still accurate

  - name: Cache invalidation on index update
    trigger: hub.index.updated
    expected: Query cache cleared for affected listing
    validates: Next search query hits index directly
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
    coordination: independent
    leader_election:
      mechanism: not required
      description: >
        All instances serve queries independently. Each maintains
        its own in-memory cache. Cache coherence is eventual —
        index update events invalidate all instances' caches.
    state_sharing:
      mechanism: shared listing_index (read-only) + per-instance cache
      conflict_resolution: >
        No write conflicts — search is read-only against listing_index.
        Each instance maintains independent cache. Analytics writes
        are append-only (no conflicts).

  event_handling:
    consumer_group: hub-search
    delivery: one-per-group
    description: >
      Index update events delivered to ONE instance per group
      for cache invalidation. Search queries can be delivered
      to ANY instance.

  blue_green:
    strategy: immediate
    shadow_duration: 30
    shadow_events_required: 5
    cutover_watch_period: 60
    storage_sharing: >
      vN and vN+1 share listing_index (read-only). Each version
      maintains independent cache. Analytics table shared with
      additive-only schema.
```

---

## Implementation Notes

- **Read-only service**: Hub-search never writes to the listing index.
  It reads from the shared database maintained by hub-index. This
  simplifies scaling and eliminates write contention.
- **Cache hierarchy**: Four cache layers with increasing TTLs handle
  different query patterns. Frequent identical queries hit the 60s
  result cache. Facets change less often (5min). Trending is
  deliberately stale (15min) to reduce computation.
- **Relevance model**: The weighted scoring model is deliberately
  simple. Text match dominates (40%), with quality signals (uptime,
  invocations) providing tie-breaking. This avoids opaque ranking
  that providers can't understand.
- **Analytics privacy**: Search query text is anonymized before storage.
  Only aggregate patterns (popular terms, zero-result queries) are
  retained for improving search quality.
- **Partial results**: When a query times out, partial results are
  returned with a `truncated: true` flag. This is better than a
  timeout error for the user experience.
- **Facet computation**: Facets are computed from the full matching
  result set before pagination. This ensures facet counts are
  accurate regardless of page number.

---

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Search returns relevant results for text queries
- [ ] Filters narrow results correctly (domain, tier, jurisdiction)
- [ ] Sort options produce correct ordering
- [ ] Pagination returns consistent, non-overlapping pages
- [ ] Facets reflect actual index content
- [ ] Cache invalidates on index update
- [ ] Empty query returns browsable results (not an error)
- [ ] Relevance ranking prioritizes quality and match
- [ ] Search stats track query volume and popular terms
- [ ] Metrics emit for all search operations
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] State machine validates query processing transitions
- [ ] Startup sequence gates each step with pre-check/validates/on-fail
- [ ] Shutdown flushes analytics and drains queries
- [ ] Configuration values validated against declared constraints
- [ ] Override audit records who, what, when, why
- [ ] Scaling: each instance serves queries independently
- [ ] Scaling: cache invalidation propagates via events
- [ ] Blue-green: shadow phase validates queries without side effects
