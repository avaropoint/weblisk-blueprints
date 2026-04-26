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

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.search` | Search query from consumer hub, marketplace, or CLI |
| Event: `hub.browse` | Category browse request from marketplace |
| Event: `hub.recommend` | Recommendation request based on hub profile |
| Event: `hub.index.updated` | Index changed — invalidate search cache |

## HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| search | Consumer Hub/Marketplace/CLI | Full search with filters, sort, and pagination |
| browse | Marketplace | Browse listings by category/domain |
| trending | Marketplace | Top listings by recent invocation volume |
| recommend | Consumer Hub | Suggested capabilities based on hub's existing domains |
| autocomplete | Marketplace/CLI | Prefix search for domain and action names |
| get-facets | Marketplace | Available filter values (domains, tiers, jurisdictions) |
| invalidate-cache | Hub Index | Clear cached results after index update |
| get-search-stats | Admin | Query volume, popular searches, cache hit ratio |

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

## Caching

Search results are cached in memory with a short TTL to handle
repeated queries without re-reading the index:

| Cache Layer | TTL | Invalidation |
|------------|-----|-------------|
| Query result cache | 60 seconds | On index update notification |
| Facet cache | 5 minutes | On index update notification |
| Trending cache | 15 minutes | On metrics refresh |
| Autocomplete index | 30 minutes | On index update notification |

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_search_queries_total | counter | Search queries by type (search, browse, recommend) |
| hub_search_duration_seconds | histogram | Query execution time |
| hub_search_results_total | histogram | Result count per query |
| hub_search_cache_hit_ratio | gauge | Cache hit percentage |
| hub_search_empty_results_total | counter | Queries returning zero results |

## Error Handling

| Error | Handling |
|-------|---------|
| Index unavailable | Return cached results if available, else 503 |
| Malformed query | Return 400 with specific validation errors |
| Timeout on large result set | Return partial results with `truncated: true` |
| Cache corruption | Clear cache, serve from index directly |

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
