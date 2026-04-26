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

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.listing.publish` | Provider submits a new or updated listing |
| Event: `hub.listing.delist` | Provider removes a listing |
| Schedule: `0 */6 * * *` | Every 6 hours — re-crawl all known providers |
| Event: `hub.provider.register` | New provider hub discovered |

## HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| index-listing | Provider Hub | Index a published listing after signature verification |
| remove-listing | Provider Hub | Remove a delisted capability |
| crawl-provider | Admin/Cron | Fetch all listings from a specific provider |
| crawl-all | Cron | Re-crawl all known providers |
| get-listing | Hub Search/Admin | Retrieve a specific listing by ID |
| get-listings-by-provider | Hub Search/Admin | All listings from a provider |
| get-index-stats | Admin | Index size, provider count, last crawl time |
| prune-stale | Cron | Remove listings from unresponsive providers |
| reindex | Admin | Force full reindex of all providers |

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

## Stale Listing Rules

| Condition | Action |
|-----------|--------|
| Provider unreachable for 72+ hours | Mark all listings stale |
| Listing not refreshed in 30+ days | Mark listing stale |
| Stale for 7+ days after marking | Remove from active index, move to archive |
| Provider returns after stale | Re-verify and restore listings |

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_index_listings_total | gauge | Total active listings in index |
| hub_index_providers_total | gauge | Total known providers |
| hub_index_operations_total | counter | Index operations by type (add, update, remove, prune) |
| hub_index_crawl_duration_seconds | histogram | Time to crawl a provider |
| hub_index_verification_failures_total | counter | Signature verification failures |
| hub_index_stale_listings | gauge | Currently stale listings |

## Error Handling

| Error | Handling |
|-------|---------|
| Signature verification failure | Reject listing. Log with provider details. Notify hub-alert. |
| Invalid listing schema | Reject with validation errors. Do not index. |
| Storage unavailable | Queue indexing operations in memory. Flush when storage recovers. |
| Crawl timeout | Log timeout. Retry on next scheduled crawl. |
| Duplicate listing conflict | Latest timestamp wins. Preserve version history. |

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
