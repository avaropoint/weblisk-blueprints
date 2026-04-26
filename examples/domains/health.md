<!-- blueprint
type: domain
kind: domain
name: health
version: 1.1.0
port: 9702
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/data-contract, patterns/governance, patterns/security]
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
platform: any
tier: free
-->

# Health Domain Controller

The health domain controller owns the site health monitoring business
function. It coordinates uptime checks, performance audits, SSL
certificate validation, DNS resolution, and availability reporting
across all monitored endpoints.

This domain does NOT perform health checks itself. It directs agents
that do: the [uptime-checker](../agents/uptime-checker.md) for
endpoint availability, TLS, and DNS checks, and the
[perf-auditor](../agents/perf-auditor.md) for page performance
metrics and Core Web Vitals.

## Domain Manifest

```json
{
  "name": "health",
  "type": "domain",
  "version": "1.0.0",
  "description": "Site health — uptime, performance, TLS, DNS monitoring",
  "url": "http://localhost:9702",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "endpoints", "type": "endpoint_list", "description": "URLs and hosts to monitor"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated health report with scores and trends"}
  ],
  "collaborators": [],
  "approval": "auto",
  "required_agents": ["uptime-checker", "perf-auditor"],
  "workflows": ["health-check", "health-report"]
}
```

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| uptime-checker | HTTP availability, response time, TLS certificate validation, DNS resolution | availability, tls-check phases |
| perf-auditor | Page load performance, Core Web Vitals, resource analysis | performance phases |

## Workflows

### health-check

Scheduled health check (default: every 5 minutes). Lightweight
availability-focused check for all monitored endpoints.

Trigger: `schedule: */5 * * * *` or `task.action = "check"`

```yaml
workflow: health-check
phases:
  - name: discover
    agent: self
    action: resolve_endpoints
    input:
      config: $config.endpoints
    output: endpoint_list
    timeout: 10

  - name: availability
    agent: uptime-checker
    action: check
    input:
      endpoints: $phases.discover.output.endpoints
    output: uptime_results
    depends_on: [discover]
    timeout: 30

  - name: evaluate
    agent: self
    action: evaluate_thresholds
    input:
      results: $phases.availability.output
    output: evaluations
    depends_on: [availability]

  - name: alert
    agent: self
    action: process_alerts
    input:
      evaluations: $phases.evaluate.output
    output: alert_actions
    depends_on: [evaluate]

  - name: record
    agent: self
    action: store_results
    input:
      results: $phases.availability.output
      evaluations: $phases.evaluate.output
    output: stored
    depends_on: [evaluate]
```

Phase dependency: discover → availability → evaluate → alert + record (parallel)

### health-report

Deep health report with performance data and trend analysis. Runs on
schedule (daily) or on demand.

Trigger: `schedule: 0 6 * * *` or `task.action = "report"`

```yaml
workflow: health-report
phases:
  - name: discover
    agent: self
    action: resolve_endpoints
    input:
      config: $config.endpoints
    output: endpoint_list
    timeout: 10

  - name: availability
    agent: uptime-checker
    action: check
    input:
      endpoints: $phases.discover.output.endpoints
    output: uptime_results
    depends_on: [discover]
    timeout: 60

  - name: tls-check
    agent: uptime-checker
    action: check_tls
    input:
      hosts: $phases.discover.output.hosts
    output: tls_results
    depends_on: [discover]
    timeout: 30

  - name: performance
    agent: perf-auditor
    action: audit
    input:
      urls: $phases.discover.output.page_urls
    output: perf_results
    depends_on: [discover]
    timeout: 120

  - name: trends
    agent: self
    action: analyze_trends
    input:
      current_uptime: $phases.availability.output
      current_perf: $phases.performance.output
    output: trend_data
    depends_on: [availability, performance]

  - name: score
    agent: self
    action: calculate_health_score
    input:
      uptime: $phases.availability.output
      tls: $phases.tls-check.output
      performance: $phases.performance.output
      trends: $phases.trends.output
    output: health_score
    depends_on: [trends, tls-check]

  - name: observe
    agent: self
    action: record_observations
    input:
      score: $phases.score.output
      trends: $phases.trends.output
    output: observations
    depends_on: [score]

  - name: report
    agent: self
    action: compile_report
    input:
      uptime: $phases.availability.output
      tls: $phases.tls-check.output
      performance: $phases.performance.output
      trends: $phases.trends.output
      score: $phases.score.output
    output: domain_report
    depends_on: [observe]
```

Phase dependency: discover → availability + tls-check + performance (parallel) → trends → score → observe → report

## Domain HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| execute_workflow | Orchestrator | Primary entry point via POST /v1/execute |
| resolve_endpoints | Internal | Load endpoint configuration and resolve targets |
| evaluate_thresholds | Internal | Compare results against warning/critical thresholds |
| process_alerts | Internal | Generate alert events for threshold violations |
| store_results | Internal | Persist check results for trend analysis |
| analyze_trends | Internal | Compare current vs. historical (24h, 7d, 30d windows) |
| calculate_health_score | Internal | Weighted composite score from all checks |
| record_observations | Internal | Feed results into lifecycle as observations |
| compile_report | Internal | Build HealthDomainReport with all data |
| get_status | Orchestrator/Admin | Domain health and agent availability |
| get_workflows | Orchestrator/Admin | Available workflow definitions |
| workflow_history | Admin | Recent workflow executions with results |

## Scoring

| Component | Weight | Source Agent |
|-----------|--------|-------------|
| Availability | 40% | uptime-checker |
| Response time | 25% | uptime-checker |
| TLS health | 15% | uptime-checker |
| Performance | 20% | perf-auditor |

Health score = (availability × 0.40) + (response_time × 0.25) + (tls × 0.15) + (performance × 0.20), clamped 0–100.

### Score Ranges

| Range | Status | Federation Advertisement |
|-------|--------|------------------------|
| 90–100 | Excellent | healthy |
| 80–89 | Good | healthy |
| 50–79 | Degraded | degraded |
| 0–49 | Unhealthy | unhealthy |

## Trend Analysis

The health domain maintains rolling windows for trend comparison:

| Window | Purpose |
|--------|---------|
| 24 hours | Short-term regression detection |
| 7 days | Weekly pattern recognition |
| 30 days | Long-term trend identification |

Trend data is stored in the domain's local storage and used for
lifecycle observations. Significant regressions (>10% score drop
within 24h) trigger automatic alerts.

## Federation Health Advertisement

The health domain advertises hub health status to federation peers
as part of the hub's public profile:

```json
{
  "hub_health": {
    "status": "healthy",
    "score": 94,
    "uptime_30d": 99.97,
    "last_check": "2026-04-25T10:00:00Z",
    "endpoints_monitored": 12,
    "endpoints_healthy": 12
  }
}
```

Federation peers use this to make routing and trust decisions.

## Aggregation Rules

1. Merge uptime results: group by endpoint, latest result wins
2. Merge TLS results: group by host, flag any degraded certificates
3. Merge performance results: group by URL, median of metrics
4. Resolve conflicts: when uptime-checker and perf-auditor disagree
   on endpoint health (e.g., HTTP 200 but terrible performance),
   the lower score wins — conservative health assessment
5. Score calculation uses weighted formula above

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_health_score | gauge | Latest health score (0–100) |
| domain_endpoint_status | gauge | Per-endpoint status (1=healthy, 0.5=degraded, 0=down) |
| domain_check_total | counter | Health checks by result status |
| domain_alert_total | counter | Alerts generated by severity |

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, use last known results with staleness warning. |
| Agent timeout | Use last known results for timed-out checks. Flag as stale in report. |
| DNS resolution failure | Mark endpoint as unreachable. Generate critical alert. |
| All agents unavailable | Domain status → offline. Continue using cached results. Generate critical alert. |
| Storage failure | Continue checking (results are transient). Log error. Alert on persistence loss. |

## Verification Checklist

- [ ] Domain registers with orchestrator and receives WLT token
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] health-check workflow runs on 5-minute schedule via cron agent
- [ ] health-report workflow runs on daily schedule and on-demand
- [ ] availability and performance phases run in parallel
- [ ] Scoring formula produces 0–100 clamped result
- [ ] Trend analysis compares against 24h, 7d, 30d windows
- [ ] Federation health advertisement reflects current score
- [ ] Threshold violations generate alerts via alerting agent
- [ ] Observations feed into lifecycle store
- [ ] Cached results used when agents are unavailable (graceful degradation)
- [ ] Metrics emit for all workflow executions and agent dispatches

Port: 9702
