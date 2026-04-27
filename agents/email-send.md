<!-- blueprint
type: agent
kind: infrastructure
name: email-send
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/retry, patterns/notification, patterns/scope, patterns/policy, patterns/safety, patterns/privacy, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent]
depends_on: []
platform: any
tier: free
port: 9754
-->

# Email Send

Transactional email sending with template rendering, queuing, and
delivery status tracking. Supports SMTP and API-based providers.

## Overview

The email agent handles all outbound transactional email for a Weblisk
server. Other agents and application code send messages to the email
agent, which renders templates, queues emails, delivers via the
configured provider (SMTP or API), and tracks delivery status. Failed
deliveries are retried automatically.

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
        - name: HealthResponse
          fields_used: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskRequest
          fields_used: [id, from, target_agent, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
    on_change:
      compatible: validate
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
          parameters: [engine, tables, indexes, relationships, constraints]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/retry
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: retry-with-backoff
          parameters: [max_retries, backoff_strategy, timeout]
        - behavior: circuit-breaker
          parameters: [failure_threshold, recovery_timeout]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/notification
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: channel-dispatch
          parameters: [channel, payload, recipient]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: identity
          parameters: [keypair, signing, verification]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: self-governance
          parameters: [reconciliation, change-assessment]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

depends_on: []
  # No runtime agent dependencies. The email agent operates independently.
  # Other agents send it messages, but it does not depend on them.
```

---

## Triggers

```yaml
triggers:
  - type: message
    action: send_email
    source: any_agent
    description: Send an email using a template and variables

  - type: message
    action: send_raw
    source: any_agent
    description: Send a raw email without a template

  - type: message
    action: check_status
    source: any_agent
    description: Check the delivery status of a sent email

  - type: schedule
    cron: "*/5 * * * *"
    action: retry_failed
    description: Retry failed emails from the queue
```

---

## Capabilities

```json
{
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:send", "resources": ["https://*"]},
    {"name": "database:read", "resources": ["email_queue", "email_templates"]},
    {"name": "database:write", "resources": ["email_queue", "email_templates"]}
  ],
  "inputs": [
    {"name": "email_request", "type": "json", "description": "Email to send with template and variables"}
  ],
  "outputs": [
    {"name": "delivery_status", "type": "json", "description": "Delivery result with message ID"}
  ],
  "collaborators": ["cron"]
}
```

### Trigger Summary

| Trigger | Description |
|---------|-------------|
| Event: `email.send` | Application requests an email be sent |
| Schedule: `*/1 * * * *` | Every minute — process queue and retry failures |

## Configuration

```yaml
config:
  provider: smtp                # smtp | sendgrid | ses | mailgun
  from_address: noreply@example.com
  from_name: My App
  queue_batch_size: 50          # emails per processing cycle
  max_retries: 3
  retry_backoff: exponential    # 1m, 2m, 4m
  rate_limit: 100               # max sends per minute

  smtp:
    host_env: SMTP_HOST
    port_env: SMTP_PORT
    username_env: SMTP_USER
    password_env: SMTP_PASS
    tls: true

  # API providers read credentials from env vars:
  # SENDGRID_API_KEY, AWS_SES_*, MAILGUN_API_KEY
```

## Execute Workflow

```
Phase 1 — Receive request:
  Parse email request: to, subject, template, variables, attachments.
  Validate required fields (to, subject, template or body).
  Queue the email with status "pending".

Phase 2 — Render template:
  If template is specified:
    Load template by name from template store.
    Render with provided variables (simple mustache-style: {{var}}).
    Set rendered HTML as email body.
  If raw body is provided:
    Use body directly (HTML or plain text).

Phase 3 — Send:
  Pick the configured provider.
  SMTP:
    Connect to SMTP server (TLS required).
    Send MIME message with headers, body, and attachments.
  API (SendGrid, SES, Mailgun):
    Build provider-specific API request.
    POST to provider endpoint with auth.

Phase 4 — Record result:
  If success:
    Store provider's message ID.
    Mark queue entry as "delivered".
  If failure:
    Mark as "failed" with error.
    Schedule retry if attempts remain.

Phase 5 — Queue processing (scheduled):
  Load pending and retryable emails from queue.
  Process in batches (up to queue_batch_size).
  Respect rate_limit — pause if limit reached.
```

## HandleMessage Actions

### send

Queue an email for delivery.

- Input:
```json
{
  "to": "user@example.com",
  "subject": "Welcome!",
  "template": "welcome",
  "variables": {
    "name": "Alice",
    "activation_url": "https://example.com/activate?token=abc"
  }
}
```
- Output: `{queued: true, email_id: "...", status: "pending"}`

### send_raw

Send an email with a raw HTML or plain text body (no template).

- Input:
```json
{
  "to": "user@example.com",
  "subject": "Password Reset",
  "body": "<p>Click <a href='...'>here</a> to reset your password.</p>",
  "content_type": "html"
}
```
- Output: `{queued: true, email_id: "...", status: "pending"}`

### status

Check delivery status of an email.

- Input: `{email_id: "..."}`
- Output: `{email_id: "...", status: "delivered", provider_id: "...", sent_at: timestamp}`

### register_template

Register or update an email template.

- Input:
```json
{
  "name": "welcome",
  "subject": "Welcome to {{app_name}}!",
  "body": "<h1>Hello {{name}}</h1><p>Thanks for signing up.</p>",
  "content_type": "html"
}
```
- Output: `{template: "welcome", version: 2}`

### list_templates

List registered email templates.

- Output: `{templates: [{name, subject, content_type, version, updated_at}, ...]}`

## Template System

Templates use simple mustache-style variable substitution:

```html
<h1>Hello {{name}}</h1>
<p>Your order #{{order_id}} has been shipped.</p>
<a href="{{tracking_url}}">Track your package</a>
```

- Variables are wrapped in `{{` and `}}`
- Missing variables render as empty strings
- No logic (no conditionals, no loops) — templates are pure substitution
- Subject line also supports variables: `"Order #{{order_id}} confirmed"`

Templates are stored in the database and versioned. Each update
increments the version number.

## Types

### EmailRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| to | string | yes | Recipient email address |
| cc | []string | no | CC recipients |
| bcc | []string | no | BCC recipients |
| subject | string | yes | Email subject line |
| template | string | no | Template name (mutually exclusive with body) |
| variables | object | no | Template variables |
| body | string | no | Raw HTML or text body (mutually exclusive with template) |
| content_type | string | no | "html" or "text" (default "html") |
| reply_to | string | no | Reply-to address |

### EmailQueueEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email_id | string | yes | Unique email ID |
| to | string | yes | Recipient |
| subject | string | yes | Rendered subject |
| body | string | yes | Rendered body |
| content_type | string | yes | html or text |
| status | string | yes | pending, sending, delivered, failed |
| attempts | int | yes | Send attempt count |
| max_retries | int | yes | Max attempts allowed |
| next_retry | int64 | no | Next retry timestamp |
| provider_id | string | no | Provider's message ID |
| error | string | no | Last error message |
| created_at | int64 | yes | Queue entry creation time |
| sent_at | int64 | no | Successful delivery time |

### EmailTemplate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Template identifier |
| subject | string | yes | Subject line (with variables) |
| body | string | yes | HTML or text body (with variables) |
| content_type | string | yes | html or text |
| version | int | yes | Template version |
| updated_at | int64 | yes | Last update timestamp |

### EmailConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| provider | string | yes | smtp, sendgrid, ses, mailgun |
| from_address | string | yes | Sender email address |
| from_name | string | yes | Sender display name |
| queue_batch_size | int | yes | Emails per processing cycle |
| max_retries | int | yes | Max delivery attempts |
| rate_limit | int | yes | Max sends per minute |

---

## Storage

Storage tables reference the Types section.

```yaml
storage:
  engine: sqlite

  tables:
    email_queue:
      source_type: EmailQueueEntry
      primary_key: email_id
      indexes:
        - name: idx_queue_status
          fields: [status, next_retry]
          type: btree
          description: Fast lookup of pending and retryable emails
        - name: idx_queue_created
          fields: [created_at]
          type: btree
          description: Queue ordering

    email_templates:
      source_type: EmailTemplate
      primary_key: name
      indexes:
        - name: idx_template_updated
          fields: [updated_at]
          type: btree

  relationships:
    - name: queue_uses_template
      from: email_queue (implicit via template reference)
      to: email_templates.name
      cardinality: many-to-one
      on_delete: restrict
      description: Queued emails may reference a template by name

  retention:
    email_queue:
      policy: 30 days for delivered, 7 days for failed
      cleanup: automatic via scheduled sweep
    email_templates:
      policy: indefinite
      cleanup: manual via operator action

  backup:
    email_queue:
      frequency: daily
      format: JSON export of pending and recent emails
      path: .weblisk/backups/email-send/email_queue_{ISO8601}.json
    email_templates:
      frequency: daily
      format: JSON export of all templates
      path: .weblisk/backups/email-send/email_templates_{ISO8601}.json
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
        trigger: queue_processing_started
        validates: first queue sweep completes without error
      - from: active
        to: degraded
        trigger: provider_unreachable
        validates: SMTP/API connection failed after retries
      - from: degraded
        to: active
        trigger: provider_recovered
        validates: successful send to provider
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received (SIGTERM, system.shutdown, or API)
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in_flight sends = 0 OR drain timeout (30s) elapsed

  entity.EmailQueueEntry:
    initial: pending
    transitions:
      - from: pending
        to: sending
        trigger: queue_sweep_picks_entry
        validates: attempts < max_retries AND next_retry <= now
      - from: sending
        to: delivered
        trigger: provider_success
        validates: provider returns message ID
        side_effect: record provider_id, sent_at
      - from: sending
        to: failed
        trigger: provider_error_retryable
        validates: attempts < max_retries
        side_effect: increment attempts, compute next_retry
      - from: failed
        to: sending
        trigger: retry_sweep
        validates: next_retry <= now AND attempts < max_retries
      - from: sending
        to: permanently_failed
        trigger: provider_error_final
        validates: attempts >= max_retries
        side_effect: emit email.delivery_failed event
      - from: failed
        to: permanently_failed
        trigger: retries_exhausted
        validates: attempts >= max_retries on retry sweep
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Pre-check:   Process has read access to environment
  Validates:   All config values within declared constraints
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/email-send/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine (sqlite)
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE
  Backout:     Close any partial connection

Step 4 — Validate Schema
  Action:      Compare storage tables against Types block
  Pre-check:   Step 3 validated
  Validates:   email_queue and email_templates tables exist with correct schema
  On Fail:     Run migration → if fails EXIT with MIGRATION_FAILED
  Backout:     Reverse migration steps

Step 5 — Verify Provider Connectivity
  Action:      Test connection to configured email provider
  Pre-check:   SMTP/API credentials loaded from environment
  Validates:   SMTP EHLO succeeds or API auth returns 200
  On Fail:     Enter degraded state (queue emails, retry later)
  Backout:     None (degraded is acceptable at startup)

Step 6 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 7 — Subscribe to Events
  Action:      Subscribe to: email.send, system.shutdown,
               system.blueprint.changed
  Pre-check:   Step 6 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT
  Backout:     Unsubscribe all, deregister, close storage

Step 8 — Start Queue Processor
  Action:      Begin queue sweep interval (every 60s)
  Pre-check:   Steps 1-7 validated
  Validates:   First sweep completes without unhandled error
  On Fail:     Stop timer → unsubscribe → deregister → EXIT
  Backout:     Full reverse

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9754, provider, queue_pending}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  Validates:   Signal recognized
  agent_state → retiring

Step 2 — Stop Accepting Emails
  Action:      Return 503 for new send/send_raw requests
  Validates:   No new emails queued

Step 3 — Stop Queue Processor
  Action:      Cancel sweep timer
  Validates:   Timer cancelled

Step 4 — Drain In-Flight Sends
  Action:      Wait for active SMTP/API calls to complete (up to 30s)
  Validates:   in_flight = 0
  On Timeout:  Mark in-flight as failed, schedule for retry on restart

Step 5 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges

Step 6 — Close Storage
  Action:      Close database connection
  Validates:   Connection closed

Step 7 — Exit
  Log: lifecycle.stopped {uptime_seconds, emails_sent, emails_pending}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - queue_processor = running
      - storage = connected
      - provider = reachable
    response:
      status: healthy
      details: {queue_pending, queue_failed, provider_status, rate_remaining}

  degraded:
    conditions:
      - provider unreachable (but queuing emails)
      - storage errors (but retrying)
      - rate limit approaching (> 80%)
    response:
      status: degraded
      details: {reason, last_error, queue_pending}

  unhealthy:
    conditions:
      - storage unreachable after retry exhaustion
      - queue processor stopped
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "email-send"`:

```
Step 1 — Validate new blueprint, verify version is newer
Step 2 — Compare Types block against current storage schema
Step 3 — Execute migration if needed (pause queue, migrate, resume)
Step 4 — Reload configuration (provider, rate limits, etc.)
Final:  Log lifecycle.version_updated {from, to}
```

---

## Implementation Notes

- **Credentials from env**: All provider credentials MUST be read from
  environment variables, never hardcoded.
- **TLS required**: SMTP connections MUST use TLS. Reject plaintext
  SMTP in production.
- **Email validation**: Validate recipient addresses with basic format
  checking (RFC 5322). Do not attempt full MX validation.
- **Rate limiting**: Respect both the configured rate limit and the
  provider's rate limits. Queue excess emails rather than dropping.
- **Bounce handling**: Track bounces if the provider supports it.
  After N hard bounces to the same address, stop sending.
- **Content sanitization**: When rendering templates, escape variables
  to prevent injection. HTML entities in variables MUST be escaped.
- **Queue persistence**: The email queue MUST be persistent. In-memory
  queues lose emails on restart.
- **Retry timing**: Use exponential backoff: 1 minute, 2 minutes,
  4 minutes. Do not retry immediately.

---

## Actions

### send

Queue an email for delivery using a template.

**Purpose:** Accept an email request, render the template, and queue for delivery.

**Input:** `{to, subject?, template, variables?, cc?, bcc?, reply_to?}`
— references `EmailRequest` type.

**Processing:**

```
1. Validate input against EmailRequest type constraints:
   a. to: valid email format (RFC 5322 basic)
   b. template: exists in email_templates table
   c. template XOR body (mutually exclusive)
2. Load template from email_templates by name
3. Render subject and body with variable substitution
4. Escape HTML entities in variables to prevent injection
5. Generate email_id (UUID v7)
6. Insert EmailQueueEntry with status = "pending"
7. Log: action.completed {action: "send", email_id}
8. Return {queued: true, email_id, status: "pending"}
```

**Output:** `{queued: bool, email_id: string, status: string}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Missing required fields or invalid email format
    retryable: false
  - code: TEMPLATE_NOT_FOUND
    condition: Referenced template does not exist
    retryable: false
  - code: STORAGE_ERROR
    condition: Failed to write to email_queue
    retryable: true
```

**Side Effects:** Writes to `email_queue`.

**Idempotency:** Each call generates a new email_id. Callers should deduplicate upstream.

---

### send_raw

Queue an email with raw body content.

**Purpose:** Send an email without template rendering.

**Input:** `{to, subject, body, content_type?, cc?, bcc?, reply_to?}`

**Processing:**

```
1. Validate input (to, subject, body required)
2. Generate email_id (UUID v7)
3. Insert EmailQueueEntry with rendered body
4. Return {queued: true, email_id, status: "pending"}
```

**Output:** `{queued: bool, email_id: string, status: string}`

**Errors:** `INVALID_INPUT` (permanent), `STORAGE_ERROR` (transient)

**Side Effects:** Writes to `email_queue`.

---

### status

Check delivery status of an email.

**Purpose:** Query the current state of a queued email.

**Input:** `{email_id: string}`

**Processing:**

```
1. Look up email_id in email_queue (by PK)
2. If not found → NOT_FOUND
3. Return current status and metadata
```

**Output:** `{email_id, status, provider_id?, sent_at?, error?, attempts}`

**Errors:** `NOT_FOUND` (permanent)

**Side Effects:** None (read-only).

---

### register_template

Register or update an email template.

**Purpose:** Store a reusable email template with variable placeholders.

**Input:** `{name, subject, body, content_type}`

**Processing:**

```
1. Validate template name (non-empty, max 128 chars)
2. If template exists → increment version, update body/subject
3. If new → insert with version = 1
4. Return template metadata
```

**Output:** `{template: string, version: int}`

**Errors:** `INVALID_INPUT` (permanent), `STORAGE_ERROR` (transient)

**Side Effects:** Writes to `email_templates`.

**Idempotency:** Same name updates existing template (version incremented).

**Manual Override:** Operator can register templates via CLI.

---

### list_templates

List registered email templates.

**Purpose:** Query all available templates.

**Input:** None

**Output:** `{templates: EmailTemplate[]}`

**Side Effects:** None (read-only).

---

## Collaboration

```yaml
events_published:
  - topic: email.queued
    payload: {email_id, to, subject, template}
    when: New email queued for delivery

  - topic: email.delivered
    payload: {email_id, provider_id, duration_ms}
    when: Email successfully delivered by provider

  - topic: email.delivery_failed
    payload: {email_id, error, attempts}
    when: All retries exhausted for an email

  - topic: email.bounce
    payload: {email_id, to, bounce_type}
    when: Provider reports a bounce (if supported)

events_subscribed:
  - topic: email.send
    payload: {to, subject, template, variables}
    action: Queue email for delivery (equivalent to send action)

  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "email-send"
    action: Self-update procedure

direct_messages:
  - target: none
    reason: Email agent does not initiate messages to other agents
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     Queue processing, delivery, and retries are autonomous
  supervised:    Delivery automatic; template management requires operator
  manual-only:   All sends require operator invocation

overridable_behaviors:
  - behavior: automatic_retry
    default: enabled
    override: Set max_retries = 0 per email or globally
    audit: logged

  - behavior: queue_processing
    default: enabled
    override: pause_queue manual action
    audit: logged

  - behavior: rate_limiting
    default: enabled
    override: Adjust config.rate_limit
    audit: logged

  - behavior: self_update
    default: enabled
    override: WL_AUTO_UPDATE=false
    audit: logged

manual_actions:
  - action: pause_queue
    description: Stop processing queued emails
    allowed: operator

  - action: resume_queue
    description: Resume queue processing
    allowed: operator

  - action: retry_email
    description: Force retry a specific failed email
    allowed: operator

  - action: purge_queue
    description: Delete delivered/failed emails older than threshold
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Required
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT send emails to addresses not specified in the request
    - MUST NOT modify email content after queuing (immutable queue entries)
    - Send rate bounded by config.rate_limit per minute

  forbidden_actions:
    - MUST NOT log email body content (log subject and recipient only)
    - MUST NOT store provider credentials in the database
    - MUST NOT send emails without TLS (reject plaintext SMTP)
    - MUST NOT retry permanently failed emails (hard bounces)

  resource_limits:
    memory: 256 MB (process limit)
    email_queue_rows: governed by retention policy
    outbound_per_minute: config.rate_limit
    attachment_size: 10 MB per email
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: Missing required fields or invalid email format
    - code: TEMPLATE_NOT_FOUND
      description: Referenced template does not exist in email_templates
    - code: NOT_FOUND
      description: Referenced email_id does not exist in email_queue
    - code: HARD_BOUNCE
      description: Provider reports permanent delivery failure (bad address)

  transient:
    - code: STORAGE_ERROR
      description: Storage read/write failure
      fallback: Enter degraded state, retry next sweep
    - code: PROVIDER_ERROR
      description: SMTP/API connection or send failure
      fallback: Queue email for retry with exponential backoff
    - code: RATE_LIMITED
      description: Provider or local rate limit reached
      fallback: Pause sending, resume next sweep cycle
    - code: PROVIDER_TIMEOUT
      description: Provider did not respond within timeout
      fallback: Mark as failed, schedule retry
```

---

## Observability

```yaml
custom_log_types:
  - log_type: email.queued
    level: info
    when: Email added to queue
    fields: {email_id, to, subject, template}

  - log_type: email.delivered
    level: info
    when: Provider confirmed delivery
    fields: {email_id, provider_id, duration_ms}

  - log_type: email.delivery_failed
    level: warn
    when: Send attempt failed
    fields: {email_id, error, attempt}

  - log_type: email.retries_exhausted
    level: error
    when: All retries exhausted
    fields: {email_id, total_attempts}

metrics:
  - name: wl_email_queued_total
    type: counter
    description: Emails queued

  - name: wl_email_delivered_total
    type: counter
    labels: [provider]
    description: Emails successfully delivered

  - name: wl_email_failed_total
    type: counter
    labels: [error_type]
    description: Failed deliveries

  - name: wl_email_send_duration_seconds
    type: histogram
    labels: [provider]
    description: Time to deliver per email

  - name: wl_email_queue_depth
    type: gauge
    labels: [status]
    description: Current queue depth by status

  - name: wl_email_rate_remaining
    type: gauge
    description: Remaining sends in current rate window

alerts:
  - condition: Queue depth > 1000 pending emails
    severity: warn
    routing: alerting agent

  - condition: Provider unreachable for 3+ consecutive sweeps
    severity: critical
    routing: alerting agent

  - condition: Delivery failure rate > 10% in last hour
    severity: high
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: http:send
      resources: ["smtp://*", "https://*"]
      description: Connect to SMTP servers and email API providers

    - capability: database:read
      resources: [email_queue, email_templates]
      description: Read own tables

    - capability: database:write
      resources: [email_queue, email_templates]
      description: Write own tables

  data_sensitivity:
    - data: Email body content
      classification: high
      handling: Not logged, encrypted at rest, purged per retention

    - data: Recipient email addresses
      classification: medium
      handling: Logged in send events, not in metrics labels

    - data: SMTP/API credentials
      classification: critical
      handling: Loaded from environment variables only, never logged or stored in DB

    - data: Template content
      classification: low
      handling: Stored in DB, logged freely

  access_control:
    - caller: Any registered agent
      actions: [send, send_raw, status]

    - caller: Operator (auth token with operator role)
      actions: [send, send_raw, status, register_template,
                list_templates, pause_queue, resume_queue,
                retry_email, purge_queue]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Send email via template
    action: send
    input:
      to: user@example.com
      template: welcome
      variables: {name: Alice, activation_url: "https://example.com/activate"}
    expected:
      queued: true
      email_id: "<uuid-v7>"
      status: pending
    validates:
      - EmailQueueEntry inserted
      - Template rendered with variables
      - email.queued event published

  - name: Send raw email
    action: send_raw
    input:
      to: admin@example.com
      subject: "System Alert"
      body: "<p>Alert details here</p>"
      content_type: html
    expected:
      queued: true
      email_id: "<uuid-v7>"
    validates:
      - Raw body stored directly
      - No template lookup needed

  - name: Check delivery status
    action: status
    input: {email_id: "<existing-id>"}
    expected: {status: delivered, provider_id: "<provider-msg-id>"}
```

### Error Cases

```yaml
  - name: Send with non-existent template
    action: send
    input: {to: user@example.com, template: nonexistent}
    expected_error: TEMPLATE_NOT_FOUND
    validates: Template existence validated before queuing

  - name: Send with invalid email address
    action: send
    input: {to: not-an-email, template: welcome}
    expected_error: INVALID_INPUT
    validates: RFC 5322 basic format check

  - name: Status for non-existent email
    action: status
    input: {email_id: nonexistent}
    expected_error: NOT_FOUND
```

### Edge Cases

```yaml
  - name: Provider unreachable at startup
    trigger: startup
    condition: SMTP server unreachable
    expected: Agent starts in degraded state, queues emails
    validates: Emails not lost, delivery retried when provider recovers

  - name: Rate limit reached mid-batch
    trigger: queue_sweep
    condition: 80 emails pending, rate_limit = 50/min
    expected: 50 sent, 30 remain for next sweep
    validates: Rate limit respected, excess emails not dropped

  - name: Template variable missing
    action: send
    input: {to: user@example.com, template: welcome, variables: {}}
    expected: Email queued with empty strings for missing variables
    validates: Missing variables render as empty, no error

  - name: Concurrent sends to same recipient
    action: send (x2)
    condition: Two agents send to the same address simultaneously
    expected: Both emails queued independently
    validates: No deduplication at email agent level (caller responsibility)
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
    routing: by agent name
    reason: Message bus routes to healthy instances

  intra_agent:
    coordination: shared-storage
    leader_election:
      mechanism: not required — queue entries claimed with optimistic locking
      leader: []
      follower: [queue_processing, send_handling]
      promotion: n/a
    state_sharing:
      mechanism: shared sqlite database
      consistency_window: immediate (queue is the coordination mechanism)
      conflict_resolution: >
        Queue entries use optimistic locking (status = pending → sending).
        Only one instance processes each email. If two instances race,
        the first UPDATE wins, the second sees zero rows affected and skips.

  event_handling:
    consumer_group: email-send
    delivery: one-per-group
    description: >
      Each email.send event delivered to one instance.
      Queue-based processing ensures at-most-once delivery.

  blue_green:
    strategy: immediate
    shadow_duration: 60
    shadow_events_required: 5
    cutover_watch_period: 120
    storage_sharing: >
      vN and vN+1 share the same queue database.
      Schema migrations additive-only during shadow.
    consumer_groups:
      shadow_phase: "email-send@vN+1"
      after_cutover: "email-send"
```

---

## Verification Checklist

- [ ] Emails can be queued via the send action
- [ ] Templates are rendered with variable substitution
- [ ] SMTP delivery works with TLS
- [ ] At least one API provider is supported
- [ ] Failed deliveries are retried with backoff
- [ ] Max retries is enforced
- [ ] Queue is processed in batches
- [ ] Rate limit is respected
- [ ] Delivery status is tracked and queryable
- [ ] Credentials are read from environment variables
- [ ] Templates are versioned and stored persistently
