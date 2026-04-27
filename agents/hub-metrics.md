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
        - path: /status
          methods: [HEAD]
          description: Availability probe endpoint on provider hubs
      types:
        - name: FederatedTaskResult
          fields_used: [listing_id, latency_ms, status, data_bytes_in, data_bytes_out]
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
        - name: MetricsInfo
          fields_used: [listing_id, uptime_30d, p95_latency_30d_ms,
                        total_invocations_30d, error_rate_30d,
                        behavioral_changes_90d, data_freshness]
        - name: ListingEntry
          fields_used: [listing_id, provider, federation_url]
      events:
        - topic: federation.task.completed
          fields_used: [listing_id, latency_ms, status, data_bytes_in, data_bytes_out]
        - topic: federation.task.failed
          fields_used: [listing_id, error, timestamp]
        - topic: hub.listing.indexed
          fields_used: [listing_id, provider]
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
  # Hub-metrics operates independently. It reads from listing_index
  # (maintained by hub-index) and emits SLA breach events consumed
  # by hub-alert, but does not degrade if either is unavailable.
```

---

## Configuration

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

---

## Types

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
        trigger: subscriptions_ready
        validates: federation event subscriptions active
      - from: active
        to: collecting
        trigger: probe_cycle_started
        validates: probe lock acquired
      - from: collecting
        to: active
        trigger: probe_cycle_complete
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
        validates: signal received
      - from: collecting
        to: retiring
        trigger: shutdown_signal
        validates: signal received — drain active probes
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in-flight probes completed or timed out
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
  Action:      Load Ed25519 keypair from .weblisk/keys/hub-metrics/
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema against Types
  Validates:   All tables exist, columns match type definitions
  On Fail:     Run migration → if fails EXIT with STORAGE_UNREACHABLE

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED

Step 5 — Subscribe to Events
  Action:      Subscribe to federation.task.completed, federation.task.failed,
               hub.listing.indexed, system.shutdown, system.blueprint.changed
  Validates:   All subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED

Step 6 — Load Active Listings
  Action:      Query listing_index for all active listings to probe
  Validates:   Query succeeds
  On Fail:     Enter degraded state — probes will fail gracefully

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9772, tracked_listings: N}
```

### Shutdown Sequence

```
Step 1 — Stop Accepting Events
  Action:      Unsubscribe from federation topics
  agent_state → retiring

Step 2 — Drain Active Probes
  Action:      Wait for in-flight probes to complete (up to 30s)
  On Timeout:  Record partial probe results

Step 3 — Final Aggregation
  Action:      Compute final rolling aggregates with latest data

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Close Storage
  Action:      Close database connection

Step 6 — Exit
  Log: lifecycle.stopped {uptime_seconds, probes_drained}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - storage connected
      - event subscriptions active
      - probes running on schedule
    response:
      status: healthy
      details: {storage, tracked_listings, last_probe_cycle,
                last_aggregation, subscriptions}

  degraded:
    conditions:
      - storage errors (retrying)
      - probe failures > 50% of listings
      - aggregation stale (missed 2+ cycles)
    response:
      status: degraded
      details: {reason, probe_failure_rate, last_error}

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
Step 3 — Pause probe cycle → run migration → resume
Step 4 — Reload configuration
Log: lifecycle.version_updated {from, to}
```

---

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `federation.task.completed` | Federated task finished — record latency, status |
| Event: `federation.task.failed` | Federated task failed — record error |
| Schedule: `*/5 * * * *` | Every 5 minutes — probe listed capabilities for uptime |
| Schedule: `0 * * * *` | Hourly — recompute rolling aggregates |
| Event: `hub.listing.indexed` | New listing — start tracking metrics |

---

## Actions

### record-invocation

Record a completed federated task for metrics.

**Source:** Federation Layer

**Input:** `{listing_id: string, timestamp: int64, latency_ms: int, status: string, data_bytes_in: int, data_bytes_out: int}`

**Processing:**

```
1. Validate input against InvocationRecord type
2. Insert into invocation_records table
3. If status = error or timeout → check SLA thresholds
4. Emit metrics: hub_metrics_invocations_recorded_total
```

**Output:** `{recorded: true, record_id: string}`

**Errors:** `INVALID_INPUT` (permanent), `STORAGE_ERROR` (transient)

---

### record-error

Record a failed federated task.

**Source:** Federation Layer

**Input:** `{listing_id: string, error: string, timestamp: int64}`

**Processing:**

```
1. Insert error record into invocation_records with status = error
2. Check error rate threshold — if SLA breached, emit hub.sla.breach
```

**Output:** `{recorded: true}`

---

### probe-availability

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

### probe-all

Uptime probe for all active listings.

**Source:** Cron

**Input:** `{}`

**Processing:**

```
1. Query all active listings from listing_index
2. For each listing (up to config.max_concurrent_probes in parallel):
   probe-availability flow
3. Emit batch metrics
```

**Output:** `{probed: int, available: int, unavailable: int}`

---

### get-metrics

Retrieve current metrics for a listing.

**Source:** Hub Search / Consumer / Admin

**Input:** `{listing_id: string}`

**Output:** `{metrics: ListingAggregate}` — matches MetricsInfo schema from hub.md

**Side Effects:** None (read-only).

---

### get-metrics-history

Time-series metrics over a date range.

**Source:** Admin / Consumer

**Input:** `{listing_id: string, from: int64, to: int64, window: string}`

**Output:** `{data_points: ListingAggregate[]}`

---

### get-aggregate

Network-wide aggregate statistics.

**Source:** Marketplace

**Input:** `{}`

**Output:** `{aggregate: NetworkAggregate}`

---

### record-behavioral-change

Record a behavioral change event for metrics.

**Source:** Hub Verify

**Input:** `{listing_id: string, level: string, timestamp: int64}`

**Output:** `{recorded: true}`

---

### recompute

Force recompute of rolling aggregates.

**Source:** Admin / Cron

**Input:** `{listing_id?: string}` — if omitted, recompute all

**Output:** `{recomputed: int}`

---

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

---

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

---

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

---

## Execute Workflow

The core metrics collection and aggregation loop:

```
Phase 1 — Record Invocations (continuous)
  Accept federation.task.completed and federation.task.failed events
  Validate event payload against InvocationRecord type
  Insert into invocation_records table
  If malformed → log and discard

Phase 2 — Probe Cycle (every 5 minutes)
  Acquire probe lock (prevent duplicate cycles in multi-instance)
  Query all active listings from listing_index
  For each listing (up to config.max_concurrent_probes):
    HEAD {federation_url}/status
    Record ProbeResult: available/unavailable + response_ms
  Release probe lock
  Emit: hub_metrics_probes_total by result

Phase 3 — SLA Evaluation (after each probe cycle)
  For each listing:
    Compute rolling uptime from ProbeResults in 30d window
    If uptime < config.sla_uptime_threshold:
      Emit hub.sla.breach event → hub-alert handles notification
    Check error rate from InvocationRecords
    If error_rate > threshold: emit hub.sla.breach

Phase 4 — Aggregate Computation (hourly)
  For each active listing:
    Compute ListingAggregate for each window (1h, 24h, 7d, 30d):
      uptime_pct: available_probes / total_probes
      p95_latency_ms: 95th percentile from InvocationRecords
      total_invocations: count of InvocationRecords
      error_rate: error_count / total_invocations
      behavioral_changes: count from hub-verify records
    Upsert into listing_aggregates table
  Compute NetworkAggregate from all listing aggregates

Phase 5 — Retention Cleanup (after aggregation)
  Delete hourly data older than config.retention_hourly
  Delete daily aggregates older than config.retention_daily
  Delete weekly aggregates older than config.retention_weekly
  Emit: hub_metrics_storage_bytes gauge
```

---

## Collaboration

```yaml
events_published:
  - topic: hub.sla.breach
    payload: {listing_id, metric, threshold, actual}
    when: Listing metrics fall below SLA thresholds

  - topic: hub.metrics.updated
    payload: {listing_id, window, computed_at}
    when: Rolling aggregates recomputed for a listing

events_subscribed:
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
    action: record-behavioral-change

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "hub-metrics"
    action: Self-update procedure

direct_messages:
  - target: hub-alert
    action: notify-sla-breach
    when: SLA breach detected during probe cycle or aggregation
    reason: Metrics agent detects breach; alert agent handles notification
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Probing, recording, and aggregation are fully autonomous
  supervised:    Recompute and retention changes require operator
  manual-only:   All probe cycles require operator trigger

overridable_behaviors:
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

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: recompute
    description: Force recompute of all rolling aggregates
    allowed: operator

  - action: probe-all
    description: Trigger immediate probe cycle
    allowed: operator

  - action: purge-old-data
    description: Force retention cleanup
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
    - MUST NOT modify listing data — read-only access to index
    - MUST NOT fabricate or alter metrics data
    - Probe rate bounded by config.max_concurrent_probes

  forbidden_actions:
    - MUST NOT self-report provider metrics — only record observed data
    - MUST NOT skip probe results (even if unfavorable to providers)
    - MUST NOT expose raw invocation data to unauthorized consumers
    - MUST NOT modify listing_index — owned by hub-index agent

  resource_limits:
    memory: 512 MB (process limit)
    invocation_records: governed by retention policies
    probe_results: governed by retention policies
    concurrent_probes: config.max_concurrent_probes
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Probe timeout | Record as unavailable for this interval |
| Storage full | Prune oldest hourly data beyond retention. Alert admin. |
| Invocation event malformed | Log and discard. Do not corrupt aggregates. |
| Aggregation failure | Retry on next scheduled run. Serve stale data with staleness indicator. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_metrics_invocations_recorded_total | counter | Invocation events recorded |
| hub_metrics_probes_total | counter | Availability probes by result (up/down) |
| hub_metrics_probe_duration_seconds | histogram | Probe response time |
| hub_metrics_aggregation_duration_seconds | histogram | Time to recompute rolling aggregates |
| hub_metrics_storage_bytes | gauge | Total metrics storage size |

---

## Security

```yaml
security:
  permissions:
    - capability: agent:message
      resources: ["*"]
      description: Send messages to hub-alert and respond to queries

    - capability: http:send
      resources: ["https://*"]
      description: Probe provider federation endpoints for availability

    - capability: database:read
      resources: [metrics_store, listing_index]
      description: Read metrics data and listing information

    - capability: database:write
      resources: [metrics_store]
      description: Write invocation records, probe results, and aggregates

  data_sensitivity:
    - data: Invocation records
      classification: medium
      handling: Contains usage patterns — encrypted at rest, aggregated before serving

    - data: Probe results
      classification: low
      handling: Availability is public information per marketplace transparency

    - data: Listing aggregates
      classification: low
      handling: Public metrics — served to marketplace and consumer hubs

    - data: Raw invocation payloads
      classification: n/a
      handling: Hub-metrics does NOT store request/response payloads, only sizes

  access_control:
    - caller: Federation layer
      actions: [record-invocation, record-error]

    - caller: hub-search
      actions: [get-metrics]

    - caller: hub-verify
      actions: [record-behavioral-change]

    - caller: Consumer hub (authenticated)
      actions: [get-metrics, get-metrics-history]

    - caller: Marketplace
      actions: [get-metrics, get-aggregate]

    - caller: Operator (auth token with operator role)
      actions: [get-metrics, get-metrics-history, get-aggregate,
                recompute, probe-all, purge-old-data]

    - caller: Unauthenticated
      actions: []
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Record successful invocation
    action: record-invocation
    input:
      listing_id: "avaropoint:seo-audit"
      timestamp: 1712160000
      latency_ms: 3200
      status: success
      data_bytes_in: 1024
      data_bytes_out: 8192
    expected:
      recorded: true
      record_id: "<uuid-v7>"
    validates:
      - InvocationRecord inserted into metrics_store
      - hub_metrics_invocations_recorded_total incremented

  - name: Get listing metrics
    action: get-metrics
    input: {listing_id: "avaropoint:seo-audit"}
    expected:
      metrics:
        uptime_30d: 99.95
        p95_latency_30d_ms: 3200
        total_invocations_30d: 142000
    validates:
      - MetricsInfo schema matches architecture/hub.md
      - data_freshness reflects last aggregation time
```

### Error Cases

```yaml
  - name: Malformed invocation event
    action: record-invocation
    input: {listing_id: "bad", latency_ms: -1}
    expected: Logged and discarded
    validates: Invalid data does not corrupt aggregates

  - name: Probe timeout
    action: probe-availability
    condition: Provider does not respond within 10s
    expected: ProbeResult with available = false
    validates: Unavailable recorded, uptime metric adjusted
```

### Edge Cases

```yaml
  - name: SLA breach triggers alert
    condition: Listing uptime drops below config.sla_uptime_threshold
    expected: hub.sla.breach event emitted
    validates: Hub-alert receives breach notification

  - name: Retention pruning under storage pressure
    condition: Storage exceeds 90% capacity
    expected: Oldest hourly data pruned first
    validates: Aggregates preserved, raw data pruned

  - name: New listing starts with empty metrics
    trigger: hub.listing.indexed
    expected: ListingAggregate created with zero values
    validates: get-metrics returns valid (empty) metrics
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
      mechanism: probe_lock in storage
      leader: [probe-all, aggregation, retention cleanup]
      follower: [record-invocation, get-metrics, health reporting]
      promotion: automatic when probe lock expires
    state_sharing:
      mechanism: shared sqlite database
      conflict_resolution: >
        Invocation recording is append-only — no conflicts.
        Probe lock prevents duplicate probe cycles.
        Aggregation lock prevents duplicate computation.

  event_handling:
    consumer_group: hub-metrics
    delivery: one-per-group
    description: >
      Bus delivers each federation task event to ONE instance
      in the hub-metrics consumer group.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 10
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share metrics_store database. Schema migrations
      are additive-only during shadow phase.
```

---

## Implementation Notes

- **Observed, not reported**: Metrics are derived from actual federated
  task execution and active probing — never from provider self-reports.
  This is the trust foundation of marketplace transparency.
- **Probe protocol**: HEAD requests to `/status` minimize overhead.
  The 10-second timeout is generous — most providers respond in <1s.
  Timeout = unavailable, no exceptions.
- **Aggregation windows**: Rolling windows overlap. The 30-day window
  used for listing cards is the primary consumer-facing metric. Hourly
  data supports real-time dashboards but has short retention.
- **SLA detection**: Breach detection runs after every probe cycle,
  not just during hourly aggregation. This ensures timely alerts for
  sudden outages.
- **Storage pressure**: Retention policies are enforced strictly.
  Under storage pressure, hourly raw data is pruned first (least
  aggregated value), preserving the more valuable daily/weekly/monthly
  aggregates.
- **Data freshness**: Every metrics response includes `data_freshness`
  (last aggregation timestamp). Consumers can decide whether to trust
  stale data or wait for the next aggregation cycle.

---

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
- [ ] Dependency contracts declare version ranges and specific bindings
- [ ] State machine validates agent and collection transitions
- [ ] Startup sequence gates each step with pre-check/validates/on-fail
- [ ] Shutdown runs final aggregation before exit
- [ ] Configuration values validated against declared constraints
- [ ] Override audit records who, what, when, why
- [ ] Scaling: probe lock prevents duplicate probe cycles
- [ ] Scaling: consumer group ensures one-per-event delivery
- [ ] Blue-green: shadow phase validates events without side effects
- [ ] SLA breach detection triggers hub.sla.breach event
