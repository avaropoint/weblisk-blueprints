<!-- blueprint
type: agent
kind: infrastructure
name: hub-metrics
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, protocol/federation, architecture/agent, architecture/hub]
platform: any
tier: free
port: 9772
-->

# Hub Metrics Agent

Collects, aggregates, and serves verifiable performance metrics for
published capability listings. Provides the data that backs the
`metrics` field in every listing and powers the marketplace's
transparency guarantees.

## Overview

The hub architecture promises transparent, verifiable metrics for every
listing: uptime, latency, error rates, invocation volume, and
behavioral change history. The hub-metrics agent is responsible for
collecting this data from live federated task execution, computing
rolling aggregates, and serving metrics to the hub-search agent,
marketplace UI, and consumer hubs evaluating potential partners.

Metrics are computed from actual usage data — not self-reported by
providers. This is a key trust property of the hub network.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["metrics_store", "listing_index"]},
    {"name": "database:write", "resources": ["metrics_store"]}
  ],
  "inputs": [
    {"name": "task_completion", "type": "json", "description": "Federated task result for metrics recording"},
    {"name": "health_probe", "type": "json", "description": "Availability probe result"}
  ],
  "outputs": [
    {"name": "listing_metrics", "type": "json", "description": "Aggregated metrics for a listing"}
  ],
  "collaborators": ["hub-index", "hub-alert"]
}
```

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `federation.task.completed` | Federated task finished — record latency, status |
| Event: `federation.task.failed` | Federated task failed — record error |
| Schedule: `*/5 * * * *` | Every 5 minutes — probe listed capabilities for uptime |
| Schedule: `0 * * * *` | Hourly — recompute rolling aggregates |
| Event: `hub.listing.indexed` | New listing — start tracking metrics |

## HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| record-invocation | Federation Layer | Record a completed federated task (latency, status, size) |
| record-error | Federation Layer | Record a failed federated task |
| probe-availability | Cron | Uptime probe for a specific listing |
| probe-all | Cron | Uptime probe for all active listings |
| get-metrics | Hub Search/Consumer/Admin | Retrieve current metrics for a listing |
| get-metrics-history | Admin/Consumer | Time-series metrics over a date range |
| get-aggregate | Marketplace | Network-wide aggregate statistics |
| record-behavioral-change | Hub Verify | Record a behavioral change event |
| recompute | Admin/Cron | Force recompute of rolling aggregates |

## Metrics Collection

### Invocation Metrics

Every federated task completion generates a metrics event:

```json
{
  "listing_id": "avaropoint:seo-audit",
  "timestamp": 1712160000,
  "latency_ms": 3200,
  "status": "success",
  "data_bytes_in": 1024,
  "data_bytes_out": 8192
}
```

These are recorded individually and aggregated into rolling windows.

### Availability Probes

The metrics agent probes each listed capability's federation endpoint
every 5 minutes:

```
HEAD {provider.federation_url}/status
```

Response within 10 seconds = available. Timeout or error = unavailable.

### Rolling Windows

| Window | Retention | Used For |
|--------|-----------|----------|
| 1 hour | 48 hours | Real-time dashboards |
| 24 hours | 90 days | Listing metrics display |
| 7 days | 1 year | Trend analysis |
| 30 days | 2 years | Listing card metrics, SLA verification |

## Listing Metrics Output

The metrics served for each listing match the `MetricsInfo` type
defined in `architecture/hub.md`:

```json
{
  "listing_id": "avaropoint:seo-audit",
  "uptime_30d": 99.95,
  "p95_latency_30d_ms": 3200,
  "total_invocations_30d": 142000,
  "error_rate_30d": 0.002,
  "behavioral_changes_90d": 1,
  "last_behavioral_change": 1710000000,
  "last_behavioral_change_level": "BENIGN",
  "data_freshness": 1712160000,
  "probe_count_30d": 8640
}
```

## Network Aggregate Statistics

For marketplace overview and health dashboards:

```json
{
  "total_listings": 1247,
  "total_providers": 89,
  "total_invocations_30d": 12400000,
  "avg_uptime_30d": 99.7,
  "avg_p95_latency_30d_ms": 4100,
  "listings_by_tier": {"free": 890, "pro": 357},
  "top_domains": ["seo", "security", "logistics", "compliance", "analytics"]
}
```

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_metrics_invocations_recorded_total | counter | Invocation events recorded |
| hub_metrics_probes_total | counter | Availability probes by result (up/down) |
| hub_metrics_probe_duration_seconds | histogram | Probe response time |
| hub_metrics_aggregation_duration_seconds | histogram | Time to recompute rolling aggregates |
| hub_metrics_storage_bytes | gauge | Total metrics storage size |

## Error Handling

| Error | Handling |
|-------|---------|
| Probe timeout | Record as unavailable for this interval |
| Storage full | Prune oldest hourly data beyond retention. Alert admin. |
| Invocation event malformed | Log and discard. Do not corrupt aggregates. |
| Aggregation failure | Retry on next scheduled run. Serve stale data with staleness indicator. |

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Invocation events are recorded from federated task completions
- [ ] Availability probes run on schedule for all active listings
- [ ] Rolling aggregates are computed correctly for all windows
- [ ] Metrics output matches MetricsInfo schema from hub.md
- [ ] Network aggregate statistics reflect actual index and usage
- [ ] Stale data is flagged with data_freshness timestamp
- [ ] Retention policies are enforced (prune old data)
- [ ] Behavioral change events are recorded from hub-verify
- [ ] Metrics emit for all collection and aggregation operations
