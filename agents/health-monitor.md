<!-- blueprint
type: agent
kind: infrastructure
name: health-monitor
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/state-machine, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, agents/alerting]
platform: any
tier: free
port: 9755
-->

# Health Monitor Agent

Internal infrastructure health monitoring for a Weblisk hub. Tracks
agent liveness, orchestrator health, domain controller status, storage
latency, federation peer reachability, and gateway responsiveness.

Unlike the health domain controller (which monitors external endpoints
like websites), the health-monitor agent monitors **the hub itself** —
the internal components that make up a running Weblisk server.

## Overview

Every Weblisk hub needs to know whether its own components are healthy.
The health-monitor agent provides this by periodically probing all
registered agents, domain controllers, storage backends, and federation
peers. It maintains a real-time health map, computes an aggregate hub
health score, and routes alerts to the alerting agent when components
degrade or fail.

The health-monitor runs on a configurable schedule (default: every 30
seconds) and exposes a health summary endpoint for the admin dashboard,
CLI interrogation, and federation advertisement.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["http://localhost:*"]},
    {"name": "database:read", "resources": ["agent_registry", "health_snapshots"]},
    {"name": "database:write", "resources": ["health_snapshots"]}
  ],
  "inputs": [
    {"name": "health_check_request", "type": "json", "description": "Optional target filter for on-demand checks"}
  ],
  "outputs": [
    {"name": "health_report", "type": "json", "description": "Current hub health state with per-component status"}
  ],
  "collaborators": ["alerting", "cron"]
}
```

## Triggers

| Trigger | Description |
|---------|-------------|
| Schedule: `*/30 * * * * *` | Every 30 seconds — full health sweep |
| Event: `health.check` | On-demand health check (from admin/CLI) |
| Event: `agent.registered` | New agent registered — add to monitor set |
| Event: `agent.deregistered` | Agent removed — remove from monitor set |

## HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| check-all | Cron/Admin | Run full health sweep of all components |
| check-agent | Admin/CLI | Check a specific agent by name |
| check-domain | Admin/CLI | Check a specific domain controller |
| check-storage | Admin/CLI | Probe storage backend latency and availability |
| check-federation | Admin/CLI | Check federation peer reachability |
| check-gateway | Admin/CLI | Verify gateway is accepting requests |
| get-health-map | Admin/CLI | Return current health state of all components |
| get-health-history | Admin/CLI | Return health snapshots over a time range |
| get-hub-score | Admin/CLI/Federation | Return aggregate hub health score |
| configure | Admin | Update check intervals, thresholds, alert rules |

## Health Check Protocol

All health checks follow the same probe pattern:

```
1. SEND probe request to target
   - Agents: POST /v1/describe (already required by protocol/spec)
   - Domains: POST /v1/describe (domain manifest)
   - Storage: read/write test record
   - Federation: GET /v1/federation/status on peer URL
   - Gateway: HEAD / on gateway URL

2. MEASURE response
   - latency_ms: time from request to response
   - status: HTTP status code (or connection error)
   - healthy: status 2xx AND latency < threshold

3. UPDATE health map entry
   - Record timestamp, latency, status, healthy flag
   - Update consecutive_failures counter
   - Update state: online → degraded → offline

4. EVALUATE alert thresholds
   - If consecutive_failures >= threshold → fire alert
   - If latency > degraded_threshold → fire degraded alert
   - If component returns to healthy → fire recovery alert
```

### Component States

| State | Condition | Description |
|-------|-----------|-------------|
| online | Healthy response within latency threshold | Component operating normally |
| degraded | Healthy response but latency > degraded_threshold | Component slow but functional |
| offline | No response or error response | Component unreachable or failing |
| unknown | No check performed yet | Component registered but not yet probed |

### State Transitions

```
unknown → online      First successful probe
unknown → offline     First failed probe
online → degraded     Latency exceeds degraded_threshold
online → offline      consecutive_failures >= failure_threshold
degraded → online     Latency returns below degraded_threshold
degraded → offline    consecutive_failures >= failure_threshold
offline → online      Successful probe after failures
```

## Health Map

The health-monitor maintains a real-time map of all components:

```json
{
  "hub_id": "my-hub",
  "timestamp": 1712160000,
  "hub_score": 94,
  "hub_state": "online",
  "components": {
    "orchestrator": {
      "state": "online",
      "latency_ms": 2,
      "last_check": 1712160000,
      "consecutive_failures": 0,
      "uptime_24h": 100.0
    },
    "agents": {
      "alerting": {
        "state": "online",
        "latency_ms": 5,
        "last_check": 1712160000,
        "consecutive_failures": 0,
        "port": 9752,
        "uptime_24h": 99.98
      },
      "sync": {
        "state": "degraded",
        "latency_ms": 850,
        "last_check": 1712160000,
        "consecutive_failures": 0,
        "port": 9751,
        "uptime_24h": 97.2
      }
    },
    "domains": {
      "seo": {
        "state": "online",
        "latency_ms": 12,
        "last_check": 1712160000,
        "consecutive_failures": 0,
        "port": 9700,
        "uptime_24h": 100.0
      }
    },
    "storage": {
      "state": "online",
      "read_latency_ms": 1,
      "write_latency_ms": 3,
      "last_check": 1712160000
    },
    "federation_peers": {
      "partner-hub": {
        "state": "online",
        "latency_ms": 45,
        "last_check": 1712160000,
        "peer_url": "https://partner.example.com/v1/federation"
      }
    },
    "gateway": {
      "state": "online",
      "latency_ms": 3,
      "last_check": 1712160000
    }
  }
}
```

## Hub Health Score

Aggregate hub health computed from component states:

| Component Type | Weight | Scoring |
|---------------|--------|---------|
| Orchestrator | 30% | 100 if online, 50 if degraded, 0 if offline |
| Agents (avg) | 25% | Average score across all registered agents |
| Domains (avg) | 20% | Average score across all registered domains |
| Storage | 15% | 100 if online, 50 if degraded, 0 if offline |
| Gateway | 10% | 100 if online, 50 if degraded, 0 if offline |

Hub score = weighted sum, clamped 0–100.

Federation peers are NOT included in the hub score — they are external
and their health is not the hub's responsibility. Peer health is
reported separately.

### Hub State Derivation

| Hub Score | Hub State |
|-----------|-----------|
| 90–100 | online |
| 50–89 | degraded |
| 0–49 | offline |

The hub state is advertised to federation peers and registries.

## Default Thresholds

| Parameter | Default | Description |
|-----------|---------|-------------|
| check_interval_seconds | 30 | Time between full health sweeps |
| response_timeout_ms | 5000 | Max wait for a probe response |
| degraded_threshold_ms | 500 | Latency above this → degraded |
| failure_threshold | 3 | Consecutive failures before offline |
| alert_on_degraded | true | Fire alert when component degrades |
| alert_on_offline | true | Fire alert when component goes offline |
| alert_on_recovery | true | Fire alert when component recovers |
| snapshot_retention_hours | 168 | Keep health snapshots for 7 days |

Thresholds are configurable per component type and per individual
component via the `configure` action.

## Alert Integration

When a component changes state, the health-monitor dispatches to the
alerting agent:

```json
{
  "action": "send",
  "payload": {
    "alert_type": "health_state_change",
    "component": "agents/sync",
    "previous_state": "online",
    "current_state": "degraded",
    "latency_ms": 850,
    "consecutive_failures": 0,
    "timestamp": 1712160000,
    "severity": "warning",
    "message": "Agent 'sync' degraded — latency 850ms exceeds threshold 500ms"
  }
}
```

Severity mapping:
- `info` — recovery (offline/degraded → online)
- `warning` — degradation (online → degraded)
- `critical` — failure (any → offline)

## Federation Health Advertisement

The hub score and state are included in federation status responses
and registry listings. This allows peers and registries to make
informed decisions about collaboration:

```json
{
  "hub_health": {
    "score": 94,
    "state": "online",
    "components_online": 8,
    "components_degraded": 1,
    "components_offline": 0,
    "last_check": 1712160000
  }
}
```

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| health_check_duration_seconds | histogram | Time to complete a probe by component type |
| health_check_total | counter | Probes by component, target, and result |
| health_state_changes_total | counter | State transitions by component and direction |
| hub_health_score | gauge | Current aggregate hub health score |
| component_latency_ms | gauge | Latest probe latency by component |
| component_uptime_ratio | gauge | 24-hour uptime ratio by component |
| health_alerts_fired_total | counter | Alerts dispatched by severity |

## Error Handling

| Error | Handling |
|-------|---------|
| Probe timeout | Mark component probe as failed. Increment consecutive_failures. |
| Probe connection refused | Mark offline. Agent likely not running. |
| Alerting agent unavailable | Log alert locally. Retry on next sweep. Do NOT block health monitoring. |
| Storage unavailable | Continue probing in-memory. Persist snapshots when storage recovers. |
| All components offline | Hub state → offline. Health-monitor itself remains running. |
| Self-check paradox | Health-monitor does NOT probe itself. Its liveness is inferred by the orchestrator receiving health reports. |

## Implementation Notes

- The health-monitor MUST NOT depend on any other agent to function.
  If the alerting agent is down, health-monitoring still runs — it just
  can't dispatch alerts until alerting recovers.
- Probes use the existing `/v1/describe` endpoint that every agent
  already implements per protocol/spec. No additional endpoints needed.
- Storage probes use a dedicated test key (`_health_check`) with TTL
  to avoid polluting the data store.
- The health map is kept in memory for fast access. Periodic snapshots
  are written to storage for historical analysis.

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] check-all probes all registered agents, domains, storage, and gateway
- [ ] Component state transitions follow the defined state machine
- [ ] Consecutive failure counter resets on successful probe
- [ ] Hub health score reflects weighted component formula
- [ ] Alerts fire on state changes (degraded, offline, recovery)
- [ ] Health map is queryable via get-health-map action
- [ ] Health history returns snapshots within requested time range
- [ ] Federation advertisement includes hub health summary
- [ ] Health-monitor continues operating when alerting agent is down
- [ ] Probes use /v1/describe — no additional endpoints required
- [ ] Default thresholds are applied; custom thresholds are respected
- [ ] Metrics emit for all probes and state changes
