<!-- blueprint
type: agent
kind: infrastructure
name: hub-alert
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/messaging, patterns/notification, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/hub, agents/alerting]
platform: any
tier: free
port: 9774
-->

# Hub Alert Agent

Monitors the hub network for behavioral changes, trust violations,
listing anomalies, and federation events. Routes hub-specific alerts
to operators and affected collaborators.

## Overview

The hub-alert agent is the notification layer for hub network events.
While the general alerting agent handles infrastructure-level
notifications (agent down, disk full), the hub-alert agent handles
**network-level** events: behavioral changes in published capabilities,
signature verification failures, SLA violations, listing suspensions,
and collaborator notifications.

Hub-alert works closely with hub-verify (which detects issues) and
hub-metrics (which detects SLA breaches). It decides who to notify,
how urgently, and through which channels.

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["alert_rules", "collaborator_registry", "alert_history"]},
    {"name": "database:write", "resources": ["alert_history"]}
  ],
  "inputs": [
    {"name": "hub_event", "type": "json", "description": "Network event requiring notification"}
  ],
  "outputs": [
    {"name": "alert_result", "type": "json", "description": "Notification delivery status"}
  ],
  "collaborators": ["alerting", "hub-verify", "hub-metrics"]
}
```

## Triggers

| Trigger | Description |
|---------|-------------|
| Event: `hub.behavioral.change` | Behavioral change detected by hub-verify |
| Event: `hub.verification.failure` | Signature or identity verification failed |
| Event: `hub.sla.breach` | Provider SLA violation detected by hub-metrics |
| Event: `hub.listing.suspended` | Listing suspended (manual or automatic) |
| Event: `hub.peer.revoked` | Trust relationship revoked |
| Event: `hub.marketplace.event` | Marketplace transaction event requiring notification |

## HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| notify-behavioral-change | Hub Verify | Notify collaborators of capability behavioral change |
| notify-verification-failure | Hub Verify | Alert admin of signature/identity failure |
| notify-sla-breach | Hub Metrics | Alert consumer of provider SLA violation |
| notify-listing-suspension | Hub Verify/Admin | Notify all collaborators that a listing is suspended |
| notify-peer-revocation | Federation | Notify affected parties of trust revocation |
| notify-marketplace-event | Marketplace | Transaction confirmations, purchase alerts |
| notify-collaborators | Any | Send notification to all hubs using a specific listing |
| get-alert-history | Admin | Query past alerts by listing, provider, or type |
| configure-rules | Admin | Set alert thresholds and routing rules |
| mute-listing | Admin | Suppress alerts for a listing (during known maintenance) |

## Notification Routing

### Who Gets Notified

| Event | Recipients |
|-------|-----------|
| BENIGN behavioral change | Provider admin (info only) |
| NOTABLE behavioral change | Provider admin + all active collaborators |
| BREAKING behavioral change | Provider admin + all active collaborators (urgent) |
| CRITICAL behavioral change | Provider admin + all active collaborators + registry operators (critical) |
| Verification failure | Registry operator + provider admin |
| SLA breach | Consumer hub admin for affected collaborations |
| Listing suspension | All active collaborators |
| Trust revocation | Both parties (consumer + provider) |
| Marketplace purchase | Buyer + seller hubs |

### Notification Channels

Hub-alert delegates actual delivery to the alerting agent, specifying
the channel and urgency:

| Severity | Channel | Delivery |
|----------|---------|----------|
| info | In-app + email digest | Batched, next digest cycle |
| warning | In-app + email | Immediate email |
| critical | In-app + email + webhook | Immediate, all channels |

### Collaborator Notification Protocol

For cross-hub notifications, hub-alert uses the federation notification
endpoint:

```
POST {collaborator.federation_url}/notify
{
  "type": "behavioral_change",
  "listing_id": "avaropoint:seo-audit",
  "level": "NOTABLE",
  "details": {
    "previous_version": "1.2.0",
    "new_version": "1.3.0",
    "change_summary": "New optional field 'recommendations' added to response",
    "deprecation_window_days": 7
  },
  "timestamp": 1712160000,
  "signature": "<registry's Ed25519 signature>"
}
```

## Alert Deduplication

To avoid alert fatigue:

| Rule | Behavior |
|------|----------|
| Same listing + same event type within 1 hour | Suppress duplicate, increment count |
| Listing muted by admin | Suppress all non-CRITICAL alerts |
| Provider in maintenance window | Suppress availability alerts |
| Flapping detection (3+ state changes in 1 hour) | Consolidate into single "unstable" alert |

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| hub_alert_notifications_total | counter | Notifications by type, severity, and channel |
| hub_alert_delivery_duration_seconds | histogram | Time to deliver notification |
| hub_alert_suppressed_total | counter | Deduplicated or muted alerts |
| hub_alert_collaborator_notifications_total | counter | Cross-hub notifications sent |
| hub_alert_delivery_failures_total | counter | Failed notification deliveries |

## Error Handling

| Error | Handling |
|-------|---------|
| Collaborator unreachable | Queue notification. Retry 3 times with backoff. Log failure. |
| Alerting agent unavailable | Log alert locally. Retry when alerting recovers. |
| Invalid event payload | Log and discard. Do not generate false alerts. |
| Rate limit on collaborator endpoint | Respect Retry-After header. Queue remaining notifications. |

## Verification Checklist

- [ ] Agent responds to POST /v1/describe with valid AgentManifest
- [ ] Behavioral change notifications reach all active collaborators
- [ ] CRITICAL changes trigger immediate notification on all channels
- [ ] Deduplication prevents repeated alerts within suppression window
- [ ] Muted listings suppress non-CRITICAL alerts
- [ ] Cross-hub notifications use federation protocol with Ed25519 signatures
- [ ] Alert history is queryable by listing, provider, and type
- [ ] SLA breach alerts include specific violation details
- [ ] Marketplace events trigger buyer/seller notifications
- [ ] Notification delivery failures are retried with backoff
- [ ] Metrics emit for all notification operations
