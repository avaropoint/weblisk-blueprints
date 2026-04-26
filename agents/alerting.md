<!-- blueprint
type: agent
kind: infrastructure
name: alerting
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/messaging, patterns/notification, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, agents/email-send]
platform: any
tier: free
port: 9752
-->

# Alerting Agent

Infrastructure agent responsible for receiving alert events from
the orchestrator, domain controllers, and other agents, then routing
notifications to the appropriate channels based on severity, source,
and subscriber preferences.

## Overview

The alerting agent is the notification hub of a Weblisk deployment.
It decouples the "something happened" event from the "tell someone
about it" delivery mechanism. Agents and domain controllers emit
structured alert events; the alerting agent decides who gets notified,
through which channel, and with what urgency.

## Specification

### Blueprint Format

```yaml
name: alerting
version: 1.0.0
description: Notification routing and delivery

capabilities:
  - agent:message

config:
  channels:
    email:
      enabled: true
      agent: email-send          # delegate to email-send agent
    webhook:
      enabled: true
      url: https://hooks.example.com/weblisk
      secret: ${WL_ALERT_WEBHOOK_SECRET}
    slack:
      enabled: false
      webhook_url: ${WL_SLACK_WEBHOOK_URL}
  
  rules:
    - severity: critical
      channels: [email, slack, webhook]
      throttle: 0                # no throttle — deliver immediately
    - severity: high
      channels: [email, webhook]
      throttle: 300              # 5-minute dedup window
    - severity: medium
      channels: [webhook]
      throttle: 900              # 15-minute dedup window
    - severity: low
      channels: []               # log only, no notification
      throttle: 3600

  subscribers:
    - email: alice@example.com
      role: admin
      severities: [critical, high, medium]
    - email: bob@example.com
      role: user
      severities: [critical]
```

### Protocol Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/health` | Health check — returns agent status |
| POST | `/describe` | Returns agent capabilities and manifest |
| POST | `/task` | Receive and process an alert event |
| POST | `/message` | Receive messages from other agents |
| POST | `/governance` | Accept governance directives |

---

## Alert Event Schema

### Inbound Alert

The alert event is delivered to the agent's `/task` endpoint.

```json
{
  "task_id": "task-a1b2c3",
  "action": "alert",
  "payload": {
    "alert_id": "alert-d4e5f6",
    "severity": "critical",
    "source": {
      "type": "agent",
      "name": "uptime-checker",
      "domain": "health"
    },
    "title": "Site unreachable",
    "message": "GET https://example.com returned 503 after 3 retries",
    "context": {
      "url": "https://example.com",
      "status_code": 503,
      "check_time": 1712160000,
      "consecutive_failures": 3
    },
    "timestamp": 1712160000
  }
}
```

### Alert Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| alert_id | string | yes | Unique ID for deduplication |
| severity | string | yes | `critical`, `high`, `medium`, `low` |
| source.type | string | yes | `agent`, `domain`, `orchestrator`, `system` |
| source.name | string | yes | Name of the emitting component |
| source.domain | string | no | Domain if source is a domain agent |
| title | string | yes | Short summary (≤ 120 chars) |
| message | string | yes | Detailed description |
| context | object | no | Structured data specific to the alert type |
| timestamp | int64 | yes | Unix epoch seconds |

### Severity Levels

| Level | Meaning | Examples |
|-------|---------|---------|
| critical | Service down or data loss risk | Site unreachable, agent crashed, storage full |
| high | Degraded service or failed workflow | Workflow failed, agent degraded, high error rate |
| medium | Notable event requiring attention | Approval backlog, federation peer disconnect |
| low | Informational | Agent registered, strategy completed, routine audit |

---

## Routing Engine

### Processing Pipeline

```
1. Receive alert event
2. Validate alert schema
3. Deduplicate:
   a. Hash: sha256(source.name + title + severity)
   b. If hash seen within throttle window → discard (log "throttled")
   c. If new → proceed
4. Match routing rules:
   a. Find the rule matching alert.severity
   b. Get channel list from rule
5. Resolve subscribers:
   a. Filter subscribers by severity preference
   b. Build per-channel recipient lists
6. Dispatch to each enabled channel
7. Store alert in alert history
8. Return task result
```

### Deduplication

The throttle window prevents alert storms. If the same alert (by
hash) fires repeatedly, only the first notification is delivered
within the throttle window. Subsequent occurrences are counted and
logged.

```json
{
  "hash": "abc123...",
  "first_seen": 1712160000,
  "last_seen": 1712160300,
  "count": 15,
  "delivered": true,
  "delivery_time": 1712160000
}
```

When the throttle window expires and the alert fires again, a new
notification is sent that includes the suppressed count:

```
"Site unreachable — 15 occurrences in the last 5 minutes"
```

---

## Delivery Channels

### Email Channel

Delegates to the `email-send` infrastructure agent via the
`agent:message` capability.

**Message to email-send:**
```json
{
  "action": "send",
  "payload": {
    "to": ["alice@example.com"],
    "subject": "[CRITICAL] Site unreachable",
    "body": "GET https://example.com returned 503 after 3 retries.\n\nSource: uptime-checker (health)\nTime: 2026-04-25 10:00:00 UTC\nConsecutive failures: 3",
    "priority": "high"
  }
}
```

**Email formatting rules:**
- Subject prefix: `[SEVERITY]` in uppercase
- Body: plain text, includes title, message, source, time, context
- Critical alerts: include `X-Priority: 1` header

### Webhook Channel

HTTP POST to a configured URL with HMAC-SHA256 signature.

**Request:**
```http
POST https://hooks.example.com/weblisk
Content-Type: application/json
X-Weblisk-Signature: sha256=<hmac>
X-Weblisk-Event: alert
X-Weblisk-Delivery: <uuid>

{
  "alert_id": "alert-d4e5f6",
  "severity": "critical",
  "source": "uptime-checker",
  "title": "Site unreachable",
  "message": "GET https://example.com returned 503 after 3 retries",
  "context": {...},
  "timestamp": 1712160000
}
```

**Signature computation:**
```
signature = HMAC-SHA256(secret, request_body)
header = "sha256=" + hex(signature)
```

**Delivery rules:**
- Timeout: 10 seconds
- Retry: 3 attempts with exponential backoff (1s, 4s, 16s)
- If all retries fail → log delivery failure, do not re-queue

### Slack Channel

HTTP POST to a Slack incoming webhook URL.

**Payload:**
```json
{
  "text": "🔴 *CRITICAL* — Site unreachable",
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "🔴 CRITICAL Alert"}
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Site unreachable*\nGET https://example.com returned 503 after 3 retries\n\n*Source:* uptime-checker (health)\n*Time:* 2026-04-25 10:00:00 UTC"
      }
    }
  ]
}
```

**Severity emoji mapping:**
- critical: 🔴
- high: 🟠
- medium: 🟡
- low: 🔵

---

## Alert History

### Storage

Alerts are stored for querying via the admin API and CLI.

| Field | Type | Description |
|-------|------|-------------|
| alert_id | string | Unique alert ID |
| severity | string | Alert severity |
| source_type | string | Source type |
| source_name | string | Source name |
| title | string | Alert title |
| message | string | Alert message |
| context | json | Alert context |
| channels_delivered | []string | Channels that received the alert |
| delivery_status | map | Per-channel delivery result |
| throttled | bool | Whether this was a throttled duplicate |
| timestamp | int64 | Alert timestamp |
| processed_at | int64 | When the alerting agent processed it |

### Retention

- Default retention: 30 days
- Critical alerts: 90 days
- Configurable via `config.retention_days`

### Query API

The admin API provides alert querying:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/admin/alerts` | List alerts with filtering |
| GET | `/v1/admin/alerts/:id` | Get alert detail |
| GET | `/v1/admin/alerts/stats` | Alert statistics |

**Stats response:**
```json
{
  "period": "24h",
  "total": 45,
  "by_severity": {
    "critical": 2,
    "high": 8,
    "medium": 20,
    "low": 15
  },
  "by_source": {
    "uptime-checker": 12,
    "seo-analyzer": 8,
    "perf-auditor": 5
  },
  "throttled": 30,
  "delivery_failures": 1
}
```

---

## Alert Sources

### Built-in Alert Triggers

The following events generate alerts automatically:

| Source | Severity | Title | Trigger |
|--------|----------|-------|---------|
| orchestrator | critical | Agent offline | Agent health check fails 3 consecutive times |
| orchestrator | high | Agent degraded | Agent health check returns degraded status |
| orchestrator | low | Agent registered | New agent completes registration |
| orchestrator | medium | Approval backlog | > 20 pending recommendations for > 1 hour |
| domain | high | Workflow failed | Workflow execution fails |
| domain | medium | Domain degraded | Required agent unavailable |
| uptime-checker | critical | Site unreachable | HTTP check fails after retries |
| perf-auditor | high | Performance regression | Page load time exceeds threshold |
| federation | medium | Peer disconnected | Federation peer unreachable |
| federation | low | Peer request | New federation peering request |

### Custom Alerts

Any agent can emit a custom alert by sending a message to the
alerting agent:

```json
{
  "action": "alert",
  "payload": {
    "severity": "medium",
    "title": "Custom event",
    "message": "Application-specific alert details"
  }
}
```

---

## Task Result

The alerting agent returns a task result summarizing delivery:

```json
{
  "task_id": "task-a1b2c3",
  "status": "completed",
  "output": {
    "alert_id": "alert-d4e5f6",
    "delivered_to": ["email", "slack"],
    "throttled": false,
    "recipients": 2
  }
}
```

If the alert was throttled:
```json
{
  "task_id": "task-a1b2c3",
  "status": "completed",
  "output": {
    "alert_id": "alert-d4e5f6",
    "throttled": true,
    "suppressed_count": 15,
    "next_delivery_eligible": 1712160600
  }
}
```

---

## Implementation Notes

- The alerting agent MUST NOT block on delivery — use async dispatch
  for channels and return the task result immediately
- Webhook secrets MUST be loaded from environment variables, never
  hardcoded in configuration
- The deduplication hash table should be pruned periodically (every
  10 minutes) to remove expired entries
- If the email-send agent is unavailable, the alerting agent should
  log the failure and attempt webhook/Slack delivery (graceful
  degradation)
- Alert history writes should be async — a failed history write
  MUST NOT prevent notification delivery

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| alerting_received_total | counter | Alerts received by severity |
| alerting_delivered_total | counter | Notifications delivered by channel and severity |
| alerting_throttled_total | counter | Alerts throttled (deduplicated) |
| alerting_delivery_failed_total | counter | Failed deliveries by channel |
| alerting_delivery_duration_seconds | histogram | Time to deliver per channel |
| alerting_active_rules | gauge | Number of active routing rules |
| alerting_history_size | gauge | Number of alerts in history store |

## Verification Checklist

- [ ] Agent registers with orchestrator and receives WLT token
- [ ] Alert events are validated against schema
- [ ] Routing rules match alerts to correct channels by severity
- [ ] Deduplication prevents duplicate notifications within throttle window
- [ ] Throttled alerts include suppressed count on next delivery
- [ ] Email channel delegates to email-send agent correctly
- [ ] Webhook channel includes HMAC-SHA256 signature
- [ ] Webhook retries 3 times with exponential backoff on failure
- [ ] Slack channel sends Block Kit formatted messages
- [ ] Alert history is stored and queryable via admin API
- [ ] Stats endpoint returns correct counts by severity and source
- [ ] Custom alerts from any agent are accepted and routed
- [ ] Graceful degradation when email-send agent is unavailable
- [ ] Metrics emit for received, delivered, throttled, and failed alerts
- [ ] Health endpoint returns agent status

Port: 9752
