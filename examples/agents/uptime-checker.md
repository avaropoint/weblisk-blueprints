<!-- blueprint
type: agent
kind: work
name: uptime-checker
version: 1.1.0
port: 9730
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
extends: [patterns/observability, patterns/scope, patterns/policy, patterns/security]
depends_on: []
platform: any
tier: free
domain: health
-->

# Uptime Checker Agent

Work agent that checks endpoint availability, response time, HTTP
status codes, TLS certificate status, and DNS resolution. Dispatched
by the health domain controller — never invoked directly. Designed to
be lightweight enough to run on a 5-minute schedule.

## Overview

The uptime-checker agent performs live endpoint monitoring. It resolves
DNS, validates TLS certificates, measures HTTP response times, and
evaluates results against configurable thresholds. Each endpoint
receives a status of healthy, degraded, or down based on response time
and TLS expiry thresholds. The agent uses `net:http`, `net:dns`, and
`net:tls` capabilities — it does not access the local file system.

Results are returned to the health domain controller, which stores
them as observations and triggers alerts for degraded or down endpoints.

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
          response_fields: [agent_id, token]
        - path: /v1/message
          methods: [POST]
          request_type: MessageEnvelope
          response_fields: [status, response]
        - path: /v1/health
          methods: [GET]
          response_fields: [status, details]
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
        - name: EventEnvelope
          fields_used: [from, to, action, payload, trace_id]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: startup-sequence
          parameters: [identity, registration, health]
        - behavior: shutdown-sequence
          parameters: [drain, deregister, close]
        - behavior: health-reporting
          parameters: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: task-dispatch
          parameters: [task_id, action, payload, timeout]
        - behavior: result-collection
          parameters: [task_id, status, output, findings]
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
          parameters: [counter, histogram, gauge]
        - behavior: log-envelope
          parameters: [log_type, level, fields, trace_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: capability-check
          parameters: [capability, resources]
        - behavior: token-validation
          parameters: [token, required_role]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

depends_on: []
  # Work agent — no runtime agent dependencies.
```

---

## Configuration

```yaml
config:
  check_timeout:
    type: int
    default: 30
    env: WL_UPTIME_CHECK_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Maximum time for a single endpoint check

  max_endpoints_per_task:
    type: int
    default: 50
    env: WL_UPTIME_MAX_ENDPOINTS
    min: 1
    max: 200
    description: Maximum endpoints accepted in a single task

  max_redirects:
    type: int
    default: 5
    env: WL_UPTIME_MAX_REDIRECTS
    min: 0
    max: 10
    description: Maximum redirect chain length

  response_time_warning:
    type: int
    default: 2000
    env: WL_UPTIME_RT_WARNING
    unit: milliseconds
    description: Response time threshold for warning status

  response_time_critical:
    type: int
    default: 5000
    env: WL_UPTIME_RT_CRITICAL
    unit: milliseconds
    description: Response time threshold for critical/down status

  dns_warning_ms:
    type: int
    default: 500
    env: WL_UPTIME_DNS_WARNING
    unit: milliseconds
    description: DNS resolution time warning threshold

  tls_expiry_warning_days:
    type: int
    default: 14
    env: WL_UPTIME_TLS_WARNING
    unit: days
    description: TLS certificate expiry days for warning

  tls_expiry_critical_days:
    type: int
    default: 7
    env: WL_UPTIME_TLS_CRITICAL
    unit: days
    description: TLS certificate expiry days for critical alert

  user_agent:
    type: string
    default: "Weblisk-Uptime-Checker/1.0"
    env: WL_UPTIME_USER_AGENT
    description: User-Agent header for outbound requests
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  EndpointConfig:
    description: Configuration for a single endpoint check
    fields:
      url:
        type: string
        description: URL to check
      timeout_ms:
        type: int
        optional: true
        description: Per-endpoint timeout override
      expected_status:
        type: int
        default: 200
        description: Expected HTTP status code
      thresholds:
        type: object
        optional: true
        description: >
          Per-endpoint threshold overrides:
          response_time_warning_ms, response_time_critical_ms,
          tls_expiry_warning_days, tls_expiry_critical_days

  UptimeResult:
    description: Complete check result for a single endpoint
    fields:
      url:
        type: string
        description: The checked URL
      status:
        type: string
        enum: [healthy, degraded, down]
        description: Endpoint availability status
      checked_at:
        type: string
        format: iso8601
        description: Timestamp of the check
      dns:
        type: object
        description: >
          DNS results: resolved (bool), resolution_ms (int),
          addresses (string[])
      tls:
        type: object
        optional: true
        description: >
          TLS results: valid (bool), issuer (string), expiry (string),
          expiry_days (int), grade (A/B/C/F), protocol (string),
          cipher (string)
      http:
        type: object
        description: >
          HTTP results: status_code (int), status_match (bool),
          ttfb_ms (int), response_time_ms (int),
          response_size_bytes (int), redirects (string[])
      findings:
        type: array
        items: UptimeFinding
        description: Issues detected during the check

  UptimeFinding:
    description: A single uptime check issue
    fields:
      rule_id:
        type: string
        format: "uptime-{category}-{detail}"
        description: Unique rule identifier
      severity:
        type: string
        enum: [critical, warning, info]
        description: Issue severity
      category:
        type: string
        enum: [dns, tls, http, threshold]
        description: Finding category
      message:
        type: string
        max: 512
        description: Human-readable description
      evidence:
        type: string
        optional: true
        description: Specific measurement or value

  DnsResult:
    description: DNS resolution result
    fields:
      hostname:
        type: string
        description: Hostname that was resolved
      resolved:
        type: bool
        description: Whether resolution succeeded
      resolution_ms:
        type: int
        description: Resolution time in milliseconds
      addresses:
        type: array
        items: string
        description: Resolved IP addresses
      nameservers:
        type: array
        items: string
        optional: true
        description: Authoritative nameservers

  TlsResult:
    description: TLS certificate validation result
    fields:
      valid:
        type: bool
        description: Whether certificate chain is valid
      issuer:
        type: string
        description: Certificate issuer
      subject:
        type: string
        description: Certificate subject
      san:
        type: array
        items: string
        description: Subject Alternative Names
      expiry:
        type: string
        format: iso8601
        description: Certificate expiry date
      expiry_days:
        type: int
        description: Days until expiry
      grade:
        type: string
        enum: [A, B, C, F]
        description: "A (>30d), B (14-30d), C (7-14d), F (<7d or expired)"
      protocol:
        type: string
        description: TLS protocol version
      cipher:
        type: string
        description: Cipher suite
      chain_valid:
        type: bool
        description: Whether full chain validates
      chain_length:
        type: int
        description: Number of certificates in chain
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
        validates: agent_id assigned in registration response
      - from: registered
        to: active
        trigger: health_check_passed
        validates: health endpoint returns healthy
      - from: active
        to: executing
        trigger: task_received
        validates: task payload passes input validation
      - from: executing
        to: active
        trigger: task_complete
        validates: result returned to domain controller
      - from: executing
        to: active
        trigger: task_failed
        validates: error response returned
        side_effect: emit uptime.task.failed event
      - from: active
        to: degraded
        trigger: network_error
        validates: outbound connectivity consistently failing
      - from: degraded
        to: active
        trigger: network_recovered
        validates: outbound request succeeds
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: executing
        to: retiring
        trigger: shutdown_signal
        validates: current task completes or times out first
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: no in-flight tasks
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/uptime-checker/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-2 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 4 — Subscribe to Events
  Action:      Subscribe to: system.shutdown, system.blueprint.changed
  Pre-check:   Step 3 validated
  Validates:   Subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED
  Backout:     Unsubscribe all, deregister

Step 5 — Verify Network Access
  Action:      Test DNS resolution and outbound HTTP connectivity
  Pre-check:   Steps 1-4 validated
  Validates:   Can resolve and reach at least one external host
  On Fail:     Enter degraded state — log warning, continue
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9730, capabilities: [net:http, net:dns, net:tls]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests

Step 3 — Drain In-Flight
  Action:      Wait for current checks to complete (up to config.check_timeout)
  On Timeout:  Return partial results for endpoints completed so far

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, endpoints_checked}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - outbound DNS/HTTP/TLS working
    response:
      status: healthy
      details: {state, uptime, endpoints_checked, last_task_at}

  degraded:
    conditions:
      - outbound connectivity intermittently failing
      - last task had partial failures
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - outbound connectivity completely blocked
      - registration lost
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

---

## Triggers

```yaml
triggers:
  - name: task_message
    type: message
    endpoint: POST /v1/message
    actions: [check, check_tls, check_dns]
    description: >
      Receive uptime check tasks from the health domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "uptime-checker"
    description: Self-update if uptime-checker blueprint changed
```

---

## Actions

### check

Check availability and health of one or more endpoints.

**Purpose:** Perform DNS resolution, TLS validation, and HTTP checks
for each endpoint, evaluate against thresholds, and return status.

**Input:** `{endpoints: EndpointConfig[]}` — array of endpoint
configurations with optional per-endpoint threshold overrides.

**Processing:**

```
1. Validate input:
   a. endpoints array is non-empty
   b. Array length <= config.max_endpoints_per_task
   c. All URLs are valid HTTP/HTTPS URLs
2. For each endpoint (parallel where possible):
   a. DNS Resolution:
      → Resolve hostname to IP addresses
      → Record resolution time
      → Flag if fails or exceeds config.dns_warning_ms
   b. TLS Check (if HTTPS):
      → Validate certificate chain
      → Record expiry date, protocol, cipher
      → Grade: A (>30d), B (14-30d), C (7-14d), F (<7d or expired)
   c. HTTP Request:
      → Send GET request with configured timeout
      → Record status code, TTFB, total response time, response size
      → Follow redirects up to config.max_redirects
      → Validate status matches expected_status
   d. Threshold Evaluation:
      → Compare response time against warning/critical thresholds
      → Compare TLS expiry against warning/critical days
      → Set status: healthy | degraded | down
3. Build UptimeResult per endpoint
4. Return results to domain controller
```

**Output:** `{results: UptimeResult[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty endpoint list, exceeds limit, or invalid URLs
    retryable: false
  - code: DNS_RESOLUTION_FAILED
    condition: Hostname cannot be resolved
    retryable: true
  - code: TLS_VALIDATION_FAILED
    condition: Certificate chain invalid or expired
    retryable: false
  - code: HTTP_ERROR
    condition: Connection refused or HTTP error status
    retryable: true
  - code: CHECK_TIMEOUT
    condition: Endpoint check exceeds timeout
    retryable: true
  - code: TOO_MANY_REDIRECTS
    condition: Redirect chain exceeds config.max_redirects
    retryable: false
```

**Side Effects:** Makes outbound DNS, TLS, and HTTP requests.
No storage writes.

**Idempotency:** Results may vary between runs due to endpoint
state changes, network conditions, and TLS certificate updates.

---

### check_tls

Validate TLS certificate for a specific host and port.

**Purpose:** Deep TLS certificate inspection — chain validation,
expiry, protocol version, cipher suite, and SAN matching.

**Input:** `{host: string, port: number}`

**Processing:**

```
1. Connect to host:port with TLS
2. Validate full certificate chain
3. Record issuer, subject, SAN, expiry, protocol, cipher
4. Grade certificate based on expiry
5. Return TlsResult
```

**Output:** `{tls: TlsResult}`

**Errors:** `INVALID_INPUT` (permanent), `TLS_VALIDATION_FAILED`
(permanent for expired, transient for connection failure).

**Side Effects:** Makes outbound TLS connection. No storage writes.

---

### check_dns

Resolve hostname and return DNS details.

**Purpose:** DNS resolution diagnostics — resolution time, IP
addresses, and nameserver information.

**Input:** `{hostname: string}`

**Processing:**

```
1. Resolve hostname to IP addresses
2. Record resolution time
3. Query for authoritative nameservers
4. Return DnsResult
```

**Output:** `{dns: DnsResult}`

**Errors:** `INVALID_INPUT` (permanent), `DNS_RESOLUTION_FAILED`
(transient).

**Side Effects:** Makes outbound DNS queries. No storage writes.

---

## Execute Workflow

```
1. RECEIVE endpoint list from health domain controller
   Input: {endpoints: [{url, timeout_ms, expected_status, thresholds}]}

2. FOR EACH endpoint (parallel where possible):

   a. DNS Resolution
      → Resolve hostname, record resolution time and addresses
      → Flag if fails or exceeds config.dns_warning_ms

   b. TLS Check (if HTTPS)
      → Validate certificate chain, record expiry and grade
      → Grade: A (>30d), B (14-30d), C (7-14d), F (<7d or expired)

   c. HTTP Request
      → GET with timeout, record status/TTFB/response time/size
      → Follow redirects, validate expected_status

   d. Threshold Evaluation
      → Response time vs warning/critical thresholds
      → TLS expiry vs warning/critical days
      → Set endpoint status: healthy | degraded | down

3. BUILD UptimeResult per endpoint

4. RETURN results to health domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: uptime.check.completed
    payload: {task_id, endpoint_count, healthy_count, degraded_count, down_count}
    when: check action completes successfully

  - topic: uptime.endpoint.down
    payload: {task_id, url, status_code, error, response_time_ms}
    when: Endpoint is down (connection refused, timeout, or wrong status)

  - topic: uptime.tls.expiring
    payload: {task_id, host, expiry_days, grade}
    when: TLS certificate expiry_days < config.tls_expiry_warning_days

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "uptime-checker"
    action: Self-update procedure

direct_messages:
  - target: variable (dispatching domain controller)
    action: TaskResult response
    when: Task completes
    reason: Domain controller expects synchronous response with results.
```

---

## Manual Overrides

```yaml
override_policy: full-auto

override_levels:
  full-auto:     All checks are autonomous
  supervised:    Operator can adjust thresholds
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: response_time_thresholds
    default: warning >2000ms, critical >5000ms
    override: Set WL_UPTIME_RT_WARNING / WL_UPTIME_RT_CRITICAL
    audit: logged

  - behavior: tls_expiry_thresholds
    default: warning <14 days, critical <7 days
    override: Set WL_UPTIME_TLS_WARNING / WL_UPTIME_TLS_CRITICAL
    audit: logged

  - behavior: dns_warning_threshold
    default: 500ms
    override: Set WL_UPTIME_DNS_WARNING
    audit: logged

manual_actions:
  - action: run_check
    description: Manually trigger an uptime check via CLI
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Optional
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT access the local file system (network-based checks only)
    - MUST NOT send messages to agents other than the dispatching controller
    - MUST NOT modify any remote resources

  forbidden_actions:
    - MUST NOT POST, PUT, or DELETE to target URLs (GET and HEAD only)
    - MUST NOT send authentication credentials to target endpoints
    - MUST NOT follow redirects to non-HTTPS URLs
    - MUST NOT cache check results between tasks

  resource_limits:
    memory: 128 MB (process limit)
    max_endpoints_per_task: config.max_endpoints_per_task (default 50)
    max_concurrent_checks: 10 (parallel endpoint checks)
    check_timeout: config.check_timeout per endpoint
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: Endpoint list empty, exceeds limit, or contains invalid URLs
    - code: TLS_VALIDATION_FAILED
      description: Certificate expired or chain invalid (not a transient issue)
    - code: TOO_MANY_REDIRECTS
      description: Redirect chain exceeds config.max_redirects
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: DNS_RESOLUTION_FAILED
      description: Hostname cannot be resolved
      fallback: Mark endpoint as down, include in results with error note
    - code: HTTP_ERROR
      description: Connection refused or HTTP error
      fallback: Mark endpoint as down, include in results with error note
    - code: CHECK_TIMEOUT
      description: Check exceeds timeout
      fallback: Mark endpoint as down with timeout note
    - code: REGISTRATION_FAILED
      description: Could not register with orchestrator
      fallback: Retry 3x with exponential backoff, then exit
```

---

## Observability

```yaml
custom_log_types:
  - log_type: uptime.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, endpoint_count, trace_id}

  - log_type: uptime.check.completed
    level: info
    when: All endpoint checks completed
    fields: {task_id, endpoint_count, healthy, degraded, down, duration_ms}

  - log_type: uptime.endpoint.down
    level: warn
    when: Endpoint is down
    fields: {url, error, response_time_ms}

  - log_type: uptime.tls.expiring
    level: warn
    when: TLS certificate nearing expiry
    fields: {host, expiry_days, grade}

  - log_type: uptime.dns.slow
    level: info
    when: DNS resolution exceeds warning threshold
    fields: {hostname, resolution_ms}

metrics:
  - name: wl_uptime_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks by action and outcome

  - name: wl_uptime_endpoints_total
    type: counter
    labels: [status]
    description: Endpoints checked by status (healthy/degraded/down)

  - name: wl_uptime_response_time_seconds
    type: histogram
    description: HTTP response time distribution

  - name: wl_uptime_dns_resolution_seconds
    type: histogram
    description: DNS resolution time distribution

  - name: wl_uptime_tls_expiry_days
    type: gauge
    labels: [host]
    description: Days until TLS certificate expiry per host

  - name: wl_uptime_check_duration_seconds
    type: histogram
    description: Per-task check duration

alerts:
  - condition: Endpoint down for 2+ consecutive checks
    severity: critical
    routing: alerting agent

  - condition: TLS certificate expiry < 7 days
    severity: critical
    routing: alerting agent

  - condition: TLS certificate expiry < 14 days
    severity: warn
    routing: alerting agent

  - condition: Response time > critical threshold for 3+ consecutive checks
    severity: high
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: net:http
      resources: ["*"]
      description: Make outbound HTTP GET/HEAD requests to target endpoints

    - capability: net:dns
      resources: ["*"]
      description: Perform DNS resolution for target hostnames

    - capability: net:tls
      resources: ["*"]
      description: Establish TLS connections for certificate validation

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTTP response headers
      classification: low
      handling: Analyzed in memory, not persisted

    - data: TLS certificate details
      classification: low
      handling: Returned to domain controller, not stored locally

    - data: DNS resolution results
      classification: low
      handling: Returned to domain controller, not stored locally

    - data: Target URLs and hostnames
      classification: low
      handling: Logged in check records

  access_control:
    - caller: Domain controller (health)
      actions: [check, check_tls, check_dns]

    - caller: Operator (auth token with operator role)
      actions: [check, check_tls, check_dns]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Check healthy endpoint
    action: check
    input:
      endpoints:
        - {url: "https://example.com", expected_status: 200}
    expected:
      results:
        - url: "https://example.com"
          status: "healthy"
          dns: {resolved: true}
          tls: {valid: true, grade: "A"}
          http: {status_code: 200, status_match: true}
    validates:
      - Healthy endpoint returns healthy status
      - DNS, TLS, and HTTP all checked
      - TLS grade assigned based on expiry

  - name: Check TLS certificate
    action: check_tls
    input: {host: "example.com", port: 443}
    expected:
      tls: {valid: true, protocol: "TLSv1.3"}
    validates:
      - TLS chain validated
      - Protocol and cipher recorded

  - name: Check DNS resolution
    action: check_dns
    input: {hostname: "example.com"}
    expected:
      dns: {resolved: true, addresses: ["<non-empty>"]}
    validates:
      - Hostname resolves to IP addresses
```

### Error Cases

```yaml
  - name: Empty endpoint list
    action: check
    input: {endpoints: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: Unreachable hostname
    action: check
    input:
      endpoints:
        - {url: "https://does-not-exist.example.com"}
    expected:
      results:
        - status: "down"
          dns: {resolved: false}
    validates: [DNS failure marks endpoint as down]

  - name: Expired TLS certificate
    action: check_tls
    input: {host: "expired.badssl.com", port: 443}
    expected:
      tls: {valid: false, grade: "F"}
    validates: [Expired certificate detected and graded F]
```

### Edge Cases

```yaml
  - name: Slow response triggers degraded status
    action: check
    input:
      endpoints:
        - {url: "https://slow.example.com"}
    condition: Response time > config.response_time_warning
    expected:
      results:
        - status: "degraded"
          findings: [{rule_id: "uptime-threshold-response-slow", severity: "warning"}]
    validates: [Slow response correctly classified as degraded]

  - name: TLS certificate expiring within warning window
    action: check
    input:
      endpoints:
        - {url: "https://expiring-soon.example.com"}
    condition: TLS expiry in 10 days
    expected:
      results:
        - tls: {grade: "C"}
          findings: [{rule_id: "uptime-tls-expiring", severity: "warning"}]
    validates: [Expiring certificate flagged with correct grade]

  - name: Redirect chain within limits
    action: check
    input:
      endpoints:
        - {url: "https://redirect.example.com"}
    condition: 3 redirects (within config.max_redirects)
    expected:
      results:
        - status: "healthy"
          http: {redirects: ["url1", "url2", "url3"]}
    validates: [Redirects followed and recorded]

  - name: Parallel endpoint checking
    action: check
    input:
      endpoints:
        - {url: "https://site1.com"}
        - {url: "https://site2.com"}
        - {url: "https://site3.com"}
    expected: All three checked, total time < 3 × single check time
    validates: [Parallel execution reduces total check time]
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
    routing: by agent name, any healthy instance
    reason: Stateless work agent — any instance handles any task.

  intra_agent:
    coordination: shared-nothing
    state_sharing:
      mechanism: none
      reason: >
        Stateless agent. Each check task is self-contained
        with all endpoint configs in the payload.

  event_handling:
    consumer_group: uptime-checker
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "uptime-checker@vN+1"
      after_cutover: "uptime-checker"
```

---

## Implementation Notes

- **Parallel Checks**: Endpoints within a task are checked in parallel
  (up to 10 concurrent) to minimize total task duration. This is
  important for the 5-minute health check schedule.
- **DNS Resolution**: Use the system resolver by default. Record both
  resolution time and all returned addresses. For HTTPS URLs, the
  resolved address is used for the subsequent TLS and HTTP checks.
- **TLS Grading**: Grade is based solely on certificate expiry:
  A (>30 days), B (14-30 days), C (7-14 days), F (<7 days or expired).
  Protocol and cipher information is recorded but does not affect grade.
- **Redirect Following**: Redirects are followed up to `config.max_redirects`.
  Each redirect URL is recorded in the redirect chain. The agent
  MUST NOT follow redirects from HTTPS to HTTP.
- **Response Size**: Only the response headers and first 1 KB of body
  are read — the agent does not download full page content. Size is
  recorded from the `Content-Length` header when available.
- **Status Determination**: An endpoint is `healthy` if DNS resolves,
  TLS validates (grade A or B), HTTP status matches expected, and
  response time is below warning threshold. It is `degraded` if
  response time exceeds warning but not critical, or TLS grade is C.
  It is `down` if DNS fails, TLS is invalid (F), HTTP connection
  fails, status mismatches, or response time exceeds critical.
- **Lightweight Design**: The agent is designed for high-frequency
  execution (every 5 minutes). It avoids heavy operations like full
  page rendering, JavaScript execution, or resource cataloging. For
  those capabilities, use perf-auditor instead.

### Threshold Rules Reference

| Check | Warning | Critical |
|-------|---------|----------|
| Response time | > 2000ms | > 5000ms |
| DNS resolution | > 500ms | Failure |
| TLS expiry | < 14 days | < 7 days |
| TLS protocol | TLSv1.2 | TLSv1.1 or lower |
| Status code | Non-matching | Connection refused |

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: health, port: 9730
- [ ] Uses net:http, net:dns, net:tls capabilities (no file system access)
- [ ] Checks DNS resolution time and records addresses
- [ ] Validates full TLS certificate chain
- [ ] Grades TLS status (A/B/C/F based on expiry)
- [ ] Records HTTP status, TTFB, and total response time
- [ ] Follows and records redirect chains
- [ ] Evaluates thresholds to set endpoint status (healthy/degraded/down)
- [ ] Runs within configured timeout per endpoint
- [ ] Returns UptimeResult per endpoint with all required fields
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded, and retiring states
- [ ] Startup sequence has pre-check, validates, on-fail for each step
- [ ] Shutdown drains in-flight checks before deregistering
- [ ] Health endpoint reports accurate status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for endpoints, response times, DNS, TLS expiry
- [ ] Security permissions limited to net:http, net:dns, net:tls, agent:message
- [ ] Constraints enforce GET/HEAD only — no POST to target endpoints
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
