<!-- blueprint
type: pattern
name: notification
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/retry, patterns/storage, patterns/secrets]
platform: any
tier: free
-->

# Notification Pattern

Multi-channel notification abstraction with pluggable channel
adapters, subscriber management, template rendering, delivery
tracking, and preference enforcement. Any agent can send
notifications; the pattern defines how channels, subscribers,
and delivery work.

## Overview

Notifications are a cross-cutting concern. The alerting agent,
domain controllers, infrastructure agents, and application code
all need to notify humans or systems. This pattern extracts the
notification mechanism into a shared contract:

1. **Channel abstraction** — pluggable delivery adapters
2. **Subscriber model** — who gets notified, through which channels
3. **Templates** — consistent formatting per channel
4. **Delivery tracking** — receipts, retries, failure handling
5. **Preferences** — subscriber-controlled opt-in/out
6. **Throttling** — deduplication and rate limiting

Agents `extends: patterns/notification` when they send notifications.
The alerting agent is a consumer of this pattern, not the owner.

---

## Channel Abstraction

### Channel Types

| Channel | Transport | Use Case |
|---------|-----------|----------|
| `email` | SMTP / API (SendGrid, SES) | Formal notifications, reports, digests |
| `webhook` | HTTP POST with HMAC | System-to-system integration |
| `slack` | Slack Incoming Webhook / API | Team notifications, ChatOps |
| `sms` | SMS API (Twilio, SNS) | Urgent alerts, on-call pages |
| `push` | Web Push / APNs / FCM | Browser and mobile notifications |
| `in_app` | Internal message store | In-application notification center |

### Channel Adapter Interface

Every channel adapter implements a standard interface:

```yaml
channel_adapter:
  name: <channel-type>
  config:
    <channel-specific-configuration>
  
  operations:
    send:
      input: NotificationRequest
      output: DeliveryReceipt
    validate_config:
      input: ChannelConfig
      output: ValidationResult
```

### Channel Configuration

```yaml
notification:
  channels:
    email:
      enabled: true
      adapter: email-send         # delegate to email-send agent
      config:
        from_address: noreply@example.com
    
    webhook:
      enabled: true
      adapter: builtin            # handled by framework
      config:
        timeout: 10
        retries: 3
        signature_algorithm: hmac-sha256
    
    slack:
      enabled: false
      adapter: builtin
      config:
        webhook_url_env: WL_SLACK_WEBHOOK_URL
    
    sms:
      enabled: false
      adapter: builtin
      config:
        provider: twilio
        from_number_env: WL_SMS_FROM
        api_key_env: WL_TWILIO_API_KEY
    
    in_app:
      enabled: true
      adapter: builtin
      config:
        retention_days: 30
        max_unread: 100
```

---

## Subscriber Model

### Subscriber Record

```yaml
types:
  Subscriber:
    fields:
      id:
        type: uuid
        required: true
      identity:
        type: string
        required: true
        description: Email, phone, user ID, or webhook URL
      channels:
        type: "[]string"
        required: true
        description: Enabled channels for this subscriber
      preferences:
        type: json
        required: false
        description: Per-severity and per-source preferences
      role:
        type: enum(admin,operator,user,system)
        required: true
      created_at:
        type: timestamp
        required: true
```

### Preference Model

Subscribers control what they receive:

```yaml
preferences:
  severities: [critical, high, medium]   # only these severities
  sources: ["*"]                          # all sources, or specific names
  channels:
    critical: [email, sms, slack]        # per-severity channel selection
    high: [email, slack]
    medium: [slack]
    low: []                              # opt out of low severity
  quiet_hours:
    enabled: true
    start: "22:00"
    end: "07:00"
    timezone: "America/New_York"
    exceptions: [critical]               # critical always delivers
  digest:
    enabled: true
    frequency: daily                     # daily | hourly | weekly
    channels: [email]
    severities: [medium, low]            # batch these into digest
```

---

## Notification Request

Any agent sends a notification using this standard format:

```json
{
  "action": "notify",
  "payload": {
    "notification_id": "ntf-a1b2c3",
    "severity": "high",
    "source": {
      "agent": "uptime-checker",
      "domain": "health"
    },
    "title": "Site unreachable",
    "body": "GET https://example.com returned 503 after 3 retries",
    "context": {
      "url": "https://example.com",
      "status_code": 503
    },
    "channels": ["email", "slack"],
    "template": "alert_default",
    "priority": "high",
    "dedup_key": "uptime-example.com-503"
  }
}
```

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| notification_id | string | yes | Unique ID for tracking |
| severity | string | yes | critical / high / medium / low |
| source.agent | string | yes | Sending agent name |
| source.domain | string | no | Owning domain if applicable |
| title | string | yes | Short summary (max 120 chars) |
| body | string | yes | Detailed message |
| context | object | no | Structured data for templates |
| channels | []string | no | Override channels (respects preferences) |
| template | string | no | Template name for rendering |
| priority | string | no | Delivery priority: high / normal / low |
| dedup_key | string | no | Deduplication key for throttling |

---

## Templates

Notifications are rendered through channel-specific templates:

### Template Structure

```yaml
templates:
  alert_default:
    email:
      subject: "[{{severity | upper}}] {{title}}"
      body_html: |
        <h2>{{title}}</h2>
        <p>{{body}}</p>
        <p><strong>Source:</strong> {{source.agent}} ({{source.domain}})</p>
        <p><strong>Time:</strong> {{timestamp | datetime}}</p>
      body_text: |
        {{severity | upper}}: {{title}}
        {{body}}
        Source: {{source.agent}} ({{source.domain}})
        Time: {{timestamp | datetime}}
    
    slack:
      text: "{{severity_emoji}} *{{severity | upper}}* — {{title}}"
      blocks:
        - type: header
          text: "{{severity_emoji}} {{severity | upper}} Alert"
        - type: section
          text: "*{{title}}*\n{{body}}\n\n*Source:* {{source.agent}}"
    
    sms:
      text: "{{severity | upper}}: {{title}} — {{body | truncate:120}}"
```

### Template Variables

| Variable | Description |
|----------|-------------|
| `{{severity}}` | Notification severity |
| `{{severity_emoji}}` | Emoji for severity (critical: red_circle, high: orange_circle, etc.) |
| `{{title}}` | Notification title |
| `{{body}}` | Notification body |
| `{{source.agent}}` | Source agent name |
| `{{source.domain}}` | Source domain name |
| `{{timestamp}}` | Event timestamp |
| `{{context.*}}` | Fields from context object |

### Template Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `upper` | Uppercase | `{{severity \| upper}}` → `CRITICAL` |
| `lower` | Lowercase | `{{title \| lower}}` |
| `truncate:N` | Truncate to N chars | `{{body \| truncate:120}}` |
| `datetime` | Format Unix timestamp | `{{timestamp \| datetime}}` |
| `json` | JSON encode | `{{context \| json}}` |

---

## Delivery Pipeline

```
1. Receive notification request
2. Validate request schema
3. Deduplication check:
   a. If dedup_key provided and seen within throttle window → throttle
   b. If new → proceed
4. Resolve subscribers:
   a. Filter by severity preference
   b. Filter by source preference
   c. Apply quiet hours (except exceptions)
   d. Route to digest queue if configured
5. Resolve channels per subscriber:
   a. Merge request channels with subscriber preferences
   b. Filter by enabled channels
6. Render template per channel
7. Dispatch to each channel adapter (concurrent):
   a. Email: delegate to email-send agent
   b. Webhook: POST with HMAC signature
   c. Slack: POST to webhook URL
   d. SMS: POST to provider API
   e. Push: POST to push service
   f. In-app: write to notification store
8. Record delivery receipts
9. Return delivery summary
```

### Throttling

Deduplication prevents notification storms:

```yaml
throttle:
  window: 300                    # seconds
  key: dedup_key                 # hash of dedup_key
  strategy: first_only           # deliver first, suppress rest
  include_count: true            # include suppressed count on next
```

---

## Delivery Tracking

### Delivery Receipt

```yaml
types:
  DeliveryReceipt:
    fields:
      notification_id:
        type: uuid
        required: true
      channel:
        type: string
        required: true
      subscriber_id:
        type: uuid
        required: true
      status:
        type: enum(pending,delivered,failed,throttled)
        required: true
      delivered_at:
        type: timestamp
        required: false
      error:
        type: string
        required: false
      attempts:
        type: int
        required: true
        default: 0
```

### Retry Behavior

Failed deliveries follow `patterns/retry` defaults:

| Channel | Max Retries | Backoff | Timeout |
|---------|-------------|---------|---------|
| email | 3 | exponential (1m, 2m, 4m) | 30s |
| webhook | 3 | exponential (1s, 4s, 16s) | 10s |
| slack | 2 | exponential (1s, 4s) | 10s |
| sms | 2 | exponential (2s, 8s) | 15s |
| push | 1 | none | 10s |
| in_app | 0 | none | local |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| notification_sent_total | counter | Notifications by channel, severity |
| notification_delivered_total | counter | Successful deliveries by channel |
| notification_failed_total | counter | Failed deliveries by channel |
| notification_throttled_total | counter | Throttled notifications |
| notification_delivery_duration_seconds | histogram | Delivery time by channel |
| notification_subscribers_active | gauge | Active subscriber count |
| notification_digest_queue_size | gauge | Pending digest items |

---

## Implementation Notes

- Channel adapters are pluggable. Adding a new channel (Teams,
  Discord, PagerDuty) requires only a new adapter that implements
  the send interface.
- The email channel SHOULD delegate to the `email-send` agent
  rather than sending directly. This centralizes email configuration.
- Template rendering uses simple mustache-style interpolation. No
  logic blocks (if/for) — keep templates declarative.
- Quiet hours are subscriber-local. The notification engine must
  resolve timezone before checking.
- Digest aggregation batches notifications and delivers a summary
  at the configured frequency. Digest rendering uses a separate
  template per channel.
- In-app notifications are stored in the agent's local store and
  exposed via an API. They do not leave the system.

---

## Verification Checklist

- [ ] Notification request validates against schema
- [ ] All enabled channel adapters deliver successfully
- [ ] Subscriber preferences filter by severity and source
- [ ] Quiet hours suppress non-exception notifications
- [ ] Digest batches notifications at configured frequency
- [ ] Deduplication prevents duplicate notifications within window
- [ ] Throttled notifications include suppressed count on next delivery
- [ ] Templates render correctly for all channels
- [ ] Template filters (upper, truncate, datetime) produce correct output
- [ ] Failed deliveries retry per channel retry configuration
- [ ] Delivery receipts record status for every send attempt
- [ ] Metrics emit for sent, delivered, failed, and throttled
- [ ] New channels can be added with only an adapter implementation
- [ ] Email channel delegates to email-send agent
