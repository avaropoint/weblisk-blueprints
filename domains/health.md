<!-- blueprint
type: domain
name: health
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/domain, architecture/agent]
platform: any
tier: free
-->

# Health Domain

Domain controller for site health monitoring. Coordinates uptime
checks, performance audits, SSL certificate validation, and
availability reporting. Produces actionable health reports with
severity-graded findings and trend data over time.

## Description

The health domain monitors the operational health of a Weblisk
deployment and any external endpoints it depends on. It runs on a
schedule (via the cron agent) and can also be triggered on demand.
Results feed into dashboards, alerts, and federation health
advertisements — hubs can share their health score with peers so the
network can route around degraded nodes.

## Domain Manifest

```json
{
  "name": "health",
  "version": "1.0.0",
  "port": 9720,
  "description": "Site health monitoring and availability reporting",
  "agents": {
    "required": [
      {"name": "uptime-checker", "kind": "work"},
      {"name": "perf-auditor", "kind": "work"}
    ],
    "optional": []
  },
  "workflows": {
    "health-check": {
      "trigger": "schedule",
      "cron": "*/5 * * * *",
      "description": "Periodic health check of all monitored endpoints"
    },
    "health-report": {
      "trigger": "manual",
      "description": "Full health audit with performance metrics and trend analysis"
    }
  }
}
```

## Required Agents

| Agent | Kind | Description |
|-------|------|-------------|
| uptime-checker | work | Checks endpoint availability, response time, status codes, SSL certificates |
| perf-auditor | work | Measures page load performance, TTFB, resource sizes, Core Web Vitals |

## Workflows

### health-check

Periodic health check on a 5-minute schedule. Lightweight — only
checks availability and response time. Designed to run frequently
with minimal resource consumption.

```
Phase 1: Endpoint Discovery
  → Read monitored endpoints from health domain config
  → Include the Weblisk server itself + any configured external URLs

Phase 2: Availability Check
  → Dispatch uptime-checker for each endpoint
  → Collect HTTP status, response time, TLS certificate expiry

Phase 3: Threshold Evaluation
  → Compare metrics against configured thresholds
  → Flag degraded endpoints (response time > threshold, non-2xx status)
  → Flag certificate expiry warnings (< 14 days, < 7 days, < 1 day)

Phase 4: Alert & Record
  → Append results to health history (rolling 24h window)
  → Emit alert events for any newly degraded or recovered endpoints
  → Update health score for federation advertisement
```

### health-report

Full health audit triggered manually or on a daily schedule. Includes
performance metrics, trend analysis, and actionable recommendations.

```
Phase 1: Endpoint Discovery
  → Same as health-check Phase 1

Phase 2: Deep Health Check
  → Dispatch uptime-checker — full mode (includes TLS chain, DNS, redirects)
  → Dispatch perf-auditor — full page load metrics for HTML endpoints

Phase 3: Trend Analysis
  → Query health history (24h, 7d, 30d windows)
  → Calculate uptime percentage per endpoint
  → Identify response time trends (improving, stable, degrading)
  → Calculate availability SLA compliance

Phase 4: Score & Report
  → Compute overall health score (0–100)
  → Generate findings with severity levels
  → Produce HealthDomainReport

Phase 5: Distribute
  → Store report in domain state
  → Emit health.report event for downstream consumers
  → Update federation health advertisement
```

## Types

### HealthDomainReport

```json
{
  "domain": "health",
  "timestamp": "2025-01-15T10:30:00Z",
  "health_score": 94,
  "endpoints": [
    {
      "url": "https://example.com",
      "status": "healthy",
      "response_time_ms": 142,
      "uptime_24h": 99.98,
      "uptime_7d": 99.95,
      "tls_expiry_days": 67,
      "findings": []
    }
  ],
  "performance": {
    "avg_ttfb_ms": 85,
    "avg_fcp_ms": 420,
    "avg_lcp_ms": 1200,
    "avg_cls": 0.02
  },
  "findings": [],
  "trends": {
    "health_score_7d": [94, 95, 93, 94, 96, 94, 94],
    "direction": "stable"
  }
}
```

### EndpointConfig

```json
{
  "url": "https://example.com",
  "name": "Production",
  "check_interval": "5m",
  "timeout_ms": 10000,
  "expected_status": 200,
  "thresholds": {
    "response_time_warning_ms": 2000,
    "response_time_critical_ms": 5000,
    "tls_expiry_warning_days": 14,
    "tls_expiry_critical_days": 7
  }
}
```

## Scoring

Health score is computed from endpoint availability and performance:

| Component | Weight | Metric |
|-----------|--------|--------|
| Availability | 40% | Percentage of endpoints returning expected status |
| Response time | 25% | Percentage of endpoints within response time threshold |
| TLS health | 15% | Certificate validity and expiry margin |
| Performance | 20% | Core Web Vitals pass rate |

### Finding Categories

| Category | Examples |
|----------|----------|
| availability | Endpoint down, timeout, unexpected status code |
| performance | Slow TTFB, high LCP, poor CLS |
| tls | Certificate expiring, weak cipher, chain incomplete |
| dns | Slow DNS resolution, missing records |

### Severity Levels

| Severity | Trigger |
|----------|---------|
| critical | Endpoint unreachable or certificate expired |
| high | Response time > critical threshold, certificate < 7 days |
| medium | Response time > warning threshold, certificate < 14 days |
| low | Minor performance degradation, non-critical missing headers |
| info | Observations, trend changes |

## Federation Health Advertisement

When federation is enabled, the health domain publishes a summary
health score via the `/v1/hub/health` endpoint. Peer hubs use this
to make routing decisions — degraded hubs receive fewer delegated
tasks until they recover.

```json
{
  "hub_id": "hub_abc123",
  "health_score": 94,
  "status": "healthy",
  "checked_at": "2025-01-15T10:30:00Z",
  "endpoints_total": 5,
  "endpoints_healthy": 5,
  "uptime_24h": 99.98
}
```

Status values: `healthy` (score ≥ 80), `degraded` (score 50–79), `unhealthy` (score < 50).

## Strategy Alignment

| Strategy | Health Domain Behavior |
|----------|----------------------|
| `observe` | Run health checks, collect metrics, report status |
| `recommend` | Flag degraded endpoints, suggest performance optimizations |
| `execute` | Emit alert events, update federation health advertisement |
| `auto` | All of the above, automatically restart failed checks |
