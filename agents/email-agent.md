<!-- blueprint
type: agent
kind: infrastructure
name: email-agent
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent]
platform: any
tier: free
-->

# Email Agent

Transactional email sending with template rendering, queuing, and
delivery status tracking. Supports SMTP and API-based providers.

## Overview

The email agent handles all outbound transactional email for a Weblisk
server. Other agents and application code send messages to the email
agent, which renders templates, queues emails, delivers via the
configured provider (SMTP or API), and tracks delivery status. Failed
deliveries are retried automatically.

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
  "collaborators": ["cron-agent"]
}
```

## Triggers

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
