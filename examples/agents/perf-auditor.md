<!-- blueprint
type: agent
kind: work
name: perf-auditor
version: 1.1.0
port: 9731
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
extends: [patterns/observability, patterns/scope, patterns/policy, patterns/security]
depends_on: []
platform: any
tier: free
domain: health
-->

# Performance Auditor Agent

Work agent that measures page load performance, resource efficiency,
and Core Web Vitals. Dispatched by the health domain controller during
the `health-report` workflow. Produces per-page performance scores
with actionable recommendations.

## Overview

The perf-auditor agent performs HTTP-based performance analysis on URLs.
It measures timing milestones (TTFB, FCP, LCP), evaluates Core Web
Vitals, catalogs page resources by type and size, checks compression
and caching, and evaluates performance budgets. The agent uses `net:http`
capabilities to fetch pages and their sub-resources — it does not access
the local file system.

Results are returned to the health domain controller, which aggregates
them into the overall health report and lifecycle observations.

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
      types:
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
          parameters: [counter, histogram]
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
  audit_timeout:
    type: int
    default: 60
    env: WL_PERF_AUDIT_TIMEOUT
    min: 10
    max: 300
    unit: seconds
    description: Maximum time for a single URL audit

  max_urls_per_task:
    type: int
    default: 20
    env: WL_PERF_MAX_URLS
    min: 1
    max: 100
    description: Maximum URLs accepted in a single task

  http_timeout:
    type: int
    default: 30
    env: WL_PERF_HTTP_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Timeout for individual HTTP requests

  max_redirects:
    type: int
    default: 5
    env: WL_PERF_MAX_REDIRECTS
    min: 0
    max: 10
    description: Maximum redirect chain length

  budget_total_weight:
    type: int
    default: 1048576
    env: WL_PERF_BUDGET_TOTAL
    unit: bytes
    description: Total page weight budget (default 1 MB)

  budget_js_weight:
    type: int
    default: 307200
    env: WL_PERF_BUDGET_JS
    unit: bytes
    description: JavaScript budget (default 300 KB)

  budget_image_weight:
    type: int
    default: 524288
    env: WL_PERF_BUDGET_IMAGE
    unit: bytes
    description: Image budget (default 500 KB)

  budget_request_count:
    type: int
    default: 50
    env: WL_PERF_BUDGET_REQUESTS
    min: 10
    max: 200
    description: Maximum number of requests per page

  lcp_good_threshold:
    type: int
    default: 2500
    env: WL_PERF_LCP_GOOD
    unit: milliseconds
    description: LCP threshold for "good" rating

  lcp_poor_threshold:
    type: int
    default: 4000
    env: WL_PERF_LCP_POOR
    unit: milliseconds
    description: LCP threshold for "poor" rating
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  PerfResult:
    description: Complete performance audit result for a single URL
    fields:
      url:
        type: string
        description: The audited URL
      performance_score:
        type: int
        min: 0
        max: 100
        description: Weighted performance score
      timing:
        type: object
        description: >
          Timing milestones in milliseconds: dns_ms, tcp_ms, tls_ms,
          ttfb_ms, fcp_ms, lcp_ms, dom_content_loaded_ms, full_load_ms
      core_web_vitals:
        type: object
        description: >
          CWV ratings: lcp {value_ms, rating}, fid_estimate {value_ms, rating},
          cls {value, rating}. Rating is good|needs-improvement|poor.
      resources:
        type: object
        description: >
          Resource catalog: total_count, total_size_bytes,
          total_compressed_bytes, by_type {html, css, js, image, font}
      budget:
        type: object
        description: >
          Budget checks: total_weight, js_weight, image_weight,
          request_count. Each has budget, actual, pass fields.
      findings:
        type: array
        items: PerfFinding
        description: Performance issues and recommendations

  PerfFinding:
    description: A single performance issue or recommendation
    fields:
      rule_id:
        type: string
        format: "perf-{category}-{detail}"
        description: Unique rule identifier
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Issue severity
      category:
        type: string
        enum: [timing, cwv, resources, budget, optimization]
        description: Finding category
      url:
        type: string
        description: URL where issue was detected
      message:
        type: string
        max: 512
        description: Human-readable description
      evidence:
        type: string
        optional: true
        description: Specific measurement or resource causing the issue
      recommendation:
        type: string
        optional: true
        description: Actionable improvement suggestion

  ResourceBreakdown:
    description: Detailed resource catalog for a single URL
    fields:
      url:
        type: string
        description: The page URL
      resources:
        type: array
        description: >
          Each resource: url, type, size_bytes, compressed_bytes,
          compression, cache_control, render_blocking
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
        side_effect: emit perf.task.failed event
      - from: active
        to: degraded
        trigger: network_error
        validates: outbound HTTP consistently failing
      - from: degraded
        to: active
        trigger: network_recovered
        validates: HTTP request succeeds
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/perf-auditor/
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
  Action:      Test outbound HTTP connectivity
  Pre-check:   Steps 1-4 validated
  Validates:   Can reach at least one external URL
  On Fail:     Enter degraded state — log warning, continue
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9731, capabilities: [net:http, agent:message]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests

Step 3 — Drain In-Flight
  Action:      Wait for current audits to complete (up to config.audit_timeout)
  On Timeout:  Return partial results for URLs completed so far

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, urls_audited}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - outbound HTTP working
    response:
      status: healthy
      details: {state, uptime, urls_audited, last_task_at}

  degraded:
    conditions:
      - outbound HTTP intermittently failing
      - last audit timed out
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - outbound HTTP completely blocked
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
    actions: [audit, audit_resources]
    description: >
      Receive performance audit tasks from the health domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "perf-auditor"
    description: Self-update if perf-auditor blueprint changed
```

---

## Actions

### audit

Full performance audit of one or more URLs.

**Purpose:** Measure timing, Core Web Vitals, resource efficiency,
and budget compliance for each URL.

**Input:** `{urls: string[]}` — array of URLs to audit.

**Processing:**

```
1. Validate input:
   a. urls array is non-empty
   b. Array length <= config.max_urls_per_task
   c. All URLs are valid HTTP/HTTPS URLs
2. For each URL:
   a. Fetch page and all sub-resources (up to config.http_timeout per request)
   b. Record timing milestones: DNS, TCP, TLS, TTFB, FCP, LCP,
      DOM Content Loaded, full page load
   c. Assess Core Web Vitals:
      - LCP against config.lcp_good/poor thresholds
      - FID/INP estimated from script execution time
      - CLS from layout-shifting elements
   d. Catalog resources: count, size, compression, cache headers per type
   e. Check performance budgets against config.budget_* thresholds
   f. Identify optimization opportunities (uncompressed resources,
      render-blocking scripts, images without dimensions)
   g. Compute performance_score using weighted formula
   h. Build findings array
3. Return PerfResult[] to domain controller
```

**Output:** `{results: PerfResult[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty URL list, exceeds max_urls_per_task, or invalid URLs
    retryable: false
  - code: HTTP_ERROR
    condition: Target URL returns 4xx/5xx or connection refused
    retryable: true
  - code: HTTP_TIMEOUT
    condition: Request exceeds config.http_timeout
    retryable: true
  - code: AUDIT_TIMEOUT
    condition: Total audit exceeds config.audit_timeout
    retryable: true
  - code: TOO_MANY_REDIRECTS
    condition: Redirect chain exceeds config.max_redirects
    retryable: false
```

**Side Effects:** Makes outbound HTTP requests to target URLs.
No storage writes.

**Idempotency:** Results may vary between runs due to network
conditions, server response times, and content changes.

---

### audit_resources

Detailed resource breakdown for a single URL.

**Purpose:** Catalog all page resources with compression, caching,
and render-blocking details.

**Input:** `{url: string}` — single URL to analyze.

**Processing:**

```
1. Validate input: url is a valid HTTP/HTTPS URL
2. Fetch page and discover all sub-resources
3. For each resource:
   a. Record: URL, type, size, compressed size, compression method
   b. Record: cache-control header, render-blocking status
4. Return detailed resource list
```

**Output:** `{resources: ResourceBreakdown}`

**Errors:** `INVALID_INPUT` (permanent), `HTTP_ERROR` (transient),
`HTTP_TIMEOUT` (transient).

**Side Effects:** Makes outbound HTTP requests. No storage writes.

**Idempotency:** Results may vary between runs.

---

## Execute Workflow

```
1. RECEIVE URL list from health domain controller
   Input: {urls: ["https://example.com", "https://example.com/about"]}

2. FOR EACH URL:

   a. Load & Timing
      → Fetch the page and all sub-resources
      → Record timing milestones:
        DNS, TCP, TLS, TTFB, FCP, LCP, DOM Content Loaded, full load

   b. Core Web Vitals Assessment
      → LCP against configured thresholds
      → FID/INP estimated from script execution time
      → CLS from layout-shifting elements

   c. Resource Analysis
      → Catalog all resources by type
      → Check compression and cache headers
      → Flag uncompressed or uncached resources

   d. Performance Budget Check
      → Compare against config.budget_* thresholds

   e. Optimization Opportunities
      → Images without dimensions, unoptimized formats
      → Render-blocking scripts and CSS
      → Missing font preloads

3. SCORE each page using weighted formula

4. BUILD findings array with severity and recommendations

5. RETURN PerfResult[] to health domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: perf.audit.completed
    payload: {task_id, url_count, avg_score, cwv_summary}
    when: audit action completes successfully

  - topic: perf.score.poor
    payload: {task_id, url, performance_score, lcp_ms, cls}
    when: URL scores below 50 on performance

  - topic: perf.budget.exceeded
    payload: {task_id, url, budget_type, budget, actual}
    when: Performance budget exceeded for a URL

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "perf-auditor"
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
  full-auto:     All auditing is autonomous
  supervised:    Operator can adjust budgets and thresholds
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: performance_budgets
    default: total 1MB, JS 300KB, images 500KB, 50 requests
    override: Set WL_PERF_BUDGET_* environment variables
    audit: logged

  - behavior: cwv_thresholds
    default: LCP good ≤2500ms, poor >4000ms
    override: Set WL_PERF_LCP_GOOD / WL_PERF_LCP_POOR
    audit: logged

  - behavior: http_timeout
    default: 30 seconds
    override: Set WL_PERF_HTTP_TIMEOUT
    audit: logged

manual_actions:
  - action: run_audit
    description: Manually trigger a performance audit via CLI
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
    - MUST NOT access the local file system (network-based auditing only)
    - MUST NOT send attack payloads or perform active exploitation
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT modify any remote resources
    - MUST NOT POST, PUT, or DELETE to target URLs (GET and HEAD only)
    - MUST NOT follow redirects to non-HTTPS URLs
    - MUST NOT cache audit results between tasks

  resource_limits:
    memory: 256 MB (process limit)
    max_urls_per_task: config.max_urls_per_task (default 20)
    max_concurrent_http: 10 per URL (sub-resource fetches)
    http_timeout: config.http_timeout per request
    audit_timeout: config.audit_timeout per task
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: URL list empty, exceeds limit, or contains invalid URLs
    - code: TOO_MANY_REDIRECTS
      description: Redirect chain exceeds config.max_redirects
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: HTTP_ERROR
      description: Target URL returns error status or connection refused
      fallback: Skip URL, include in partial results with error note
    - code: HTTP_TIMEOUT
      description: Request exceeds config.http_timeout
      fallback: Skip URL, include in partial results with timeout note
    - code: AUDIT_TIMEOUT
      description: Total audit exceeds config.audit_timeout
      fallback: Return partial results for URLs completed so far
    - code: REGISTRATION_FAILED
      description: Could not register with orchestrator
      fallback: Retry 3x with exponential backoff, then exit
    - code: DNS_RESOLUTION_FAILED
      description: Could not resolve hostname for target URL
      fallback: Skip URL with DNS error note
```

---

## Observability

```yaml
custom_log_types:
  - log_type: perf.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, url_count, trace_id}

  - log_type: perf.audit.completed
    level: info
    when: Audit completed for a URL
    fields: {task_id, url, performance_score, lcp_ms, duration_ms}

  - log_type: perf.task.failed
    level: warn
    when: Audit failed for a URL
    fields: {task_id, url, error_code}

  - log_type: perf.budget.exceeded
    level: warn
    when: Performance budget exceeded
    fields: {url, budget_type, budget, actual}

metrics:
  - name: wl_perf_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks by action and outcome

  - name: wl_perf_audit_duration_seconds
    type: histogram
    description: Per-URL audit duration

  - name: wl_perf_score_distribution
    type: histogram
    description: Distribution of performance scores (0-100)

  - name: wl_perf_lcp_seconds
    type: histogram
    description: LCP measurements across audited URLs

  - name: wl_perf_page_weight_bytes
    type: histogram
    description: Total page weight across audited URLs

  - name: wl_perf_budget_violations_total
    type: counter
    labels: [budget_type]
    description: Budget violations by type

alerts:
  - condition: Error rate > 30% of URLs in a task
    severity: warn
    routing: alerting agent

  - condition: All URLs failing (network outage)
    severity: critical
    routing: alerting agent

  - condition: Average LCP > 4000ms across last 10 audits
    severity: warn
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: net:http
      resources: ["*"]
      description: Make outbound HTTP GET/HEAD requests to target URLs

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTTP response headers
      classification: low
      handling: Analyzed in memory, not persisted

    - data: HTTP response bodies
      classification: low
      handling: Parsed for resource discovery, not stored

    - data: Timing measurements
      classification: low
      handling: Returned to domain controller in PerfResult

    - data: Target URLs
      classification: low
      handling: Logged in audit records

  access_control:
    - caller: Domain controller (health)
      actions: [audit, audit_resources]

    - caller: Operator (auth token with operator role)
      actions: [audit, audit_resources]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Audit fast page
    action: audit
    input:
      urls: ["https://example.com"]
    expected:
      results:
        - url: "https://example.com"
          performance_score: ">= 80"
          core_web_vitals:
            lcp: {rating: "good"}
          budget: {total_weight: {pass: true}}
    validates:
      - Fast page scores above 80
      - CWV rated correctly
      - Budget check passes

  - name: Audit resources breakdown
    action: audit_resources
    input: {url: "https://example.com"}
    expected:
      resources:
        url: "https://example.com"
        resources: [{type: "html"}, {type: "css"}]
    validates:
      - Resources cataloged by type with size and compression
```

### Error Cases

```yaml
  - name: Empty URL list
    action: audit
    input: {urls: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: Unreachable URL
    action: audit
    input: {urls: ["https://does-not-exist.example.com"]}
    expected_error: DNS_RESOLUTION_FAILED
    validates: [DNS failure produces transient error]

  - name: Too many redirects
    action: audit
    input: {urls: ["https://redirect-loop.example.com"]}
    expected_error: TOO_MANY_REDIRECTS
    validates: [Redirect chain limit enforced]
```

### Edge Cases

```yaml
  - name: URL with slow LCP
    action: audit
    input: {urls: ["https://slow-page.example.com"]}
    condition: LCP > 4000ms
    expected:
      results:
        - core_web_vitals: {lcp: {rating: "poor"}}
          findings: [{rule_id: "perf-cwv-lcp-poor", severity: "high"}]
    validates: [Poor LCP detected and reported]

  - name: Budget exceeded
    action: audit
    input: {urls: ["https://heavy-page.example.com"]}
    condition: Total page weight > 1 MB
    expected:
      results:
        - budget: {total_weight: {pass: false}}
    validates: [Budget violation detected]

  - name: Mixed HTTP/HTTPS resources
    action: audit
    input: {urls: ["https://mixed-content.example.com"]}
    expected:
      findings: [{rule_id: "perf-resources-mixed-content", severity: "high"}]
    validates: [Mixed content flagged as security/performance issue]

  - name: Partial results on timeout
    action: audit
    input: {urls: ["https://url1.com", "https://url2.com", "https://url3.com"]}
    condition: Third URL times out
    expected: Results for first two URLs returned, third has error note
    validates: [Partial results returned on timeout]
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
        Stateless agent. Each audit is independent with all
        inputs in the task payload.

  event_handling:
    consumer_group: perf-auditor
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "perf-auditor@vN+1"
      after_cutover: "perf-auditor"
```

---

## Implementation Notes

- **Timing Measurement**: Use high-resolution timers for all timing
  milestones. DNS, TCP, and TLS times are measured from the initial
  connection. FCP and LCP require parsing the response to identify
  the first contentful element and the largest element.
- **CLS Estimation**: Without a real browser, CLS is estimated by
  identifying common layout-shift causes: images without explicit
  width/height attributes, dynamically loaded fonts, and content
  injected above the fold. This is a heuristic — real CLS requires
  browser rendering.
- **FID/INP Estimation**: Estimated from total JavaScript execution
  time and script size. Long tasks (>50ms script execution) contribute
  to estimated input delay. This is an approximation — real FID
  requires user interaction measurement.
- **Resource Discovery**: Sub-resources are discovered by parsing HTML
  for `<link>`, `<script>`, `<img>`, and `<style>` elements. CSS
  `@import` and JavaScript dynamic imports are not followed.
- **Compression Detection**: Check `Content-Encoding` response header
  for gzip, brotli, or deflate. Resources without compression are
  flagged if they exceed 1 KB.
- **Scoring Formula**: `performance_score = weighted(lcp: 0.25,
  fcp: 0.15, ttfb: 0.15, cls: 0.15, page_weight: 0.15,
  request_count: 0.15)`. Each component normalized to 0-100 based
  on threshold ranges.
- **User-Agent**: All requests include `User-Agent: Weblisk-Perf-Auditor/1.0`.

### Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤ 2500ms | 2500–4000ms | > 4000ms |
| FID/INP | ≤ 100ms | 100–300ms | > 300ms |
| CLS | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| TTFB | ≤ 800ms | 800–1800ms | > 1800ms |
| FCP | ≤ 1800ms | 1800–3000ms | > 3000ms |

### Performance Budget Defaults

| Resource | Budget | Severity if exceeded |
|----------|--------|---------------------|
| Total page weight | 1 MB | high |
| JavaScript | 300 KB | high |
| Images | 500 KB | medium |
| CSS | 100 KB | medium |
| Fonts | 200 KB | low |
| Total requests | 50 | medium |

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: health, port: 9731
- [ ] Uses net:http capability (no file system access)
- [ ] Measures TTFB, FCP, LCP, and CLS for each URL
- [ ] Catalogs all page resources by type and size
- [ ] Checks resource compression (gzip/brotli)
- [ ] Evaluates performance budgets against configured thresholds
- [ ] Identifies render-blocking resources
- [ ] Flags images without dimensions (CLS contributors)
- [ ] Scores pages on 0–100 scale with weighted components
- [ ] Returns PerfResult per URL with all required fields
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded, and retiring states
- [ ] Startup sequence has pre-check, validates, on-fail for each step
- [ ] Shutdown drains in-flight audits before deregistering
- [ ] Health endpoint reports accurate status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for tasks, scores, LCP, page weight, and budget violations
- [ ] Security permissions limited to net:http and agent:message
- [ ] Constraints enforce GET/HEAD only — no POST/PUT/DELETE to targets
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
    min: 10
    max: 200
    description: Maximum number of requests per page

  lcp_good_threshold:
    type: int
    default: 2500
    env: WL_PERF_LCP_GOOD
    unit: milliseconds
    description: LCP threshold for "good" rating

  lcp_poor_threshold:
    type: int
    default: 4000
    env: WL_PERF_LCP_POOR
    unit: milliseconds
    description: LCP threshold for "poor" rating
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  PerfResult:
    description: Complete performance audit result for a single URL
    fields:
      url:
        type: string
        description: The audited URL
      performance_score:
        type: int
        min: 0
        max: 100
        description: Weighted performance score
      timing:
        type: object
        description: >
          Timing milestones in milliseconds: dns_ms, tcp_ms, tls_ms,
          ttfb_ms, fcp_ms, lcp_ms, dom_content_loaded_ms, full_load_ms
      core_web_vitals:
        type: object
        description: >
          CWV ratings: lcp {value_ms, rating}, fid_estimate {value_ms, rating},
          cls {value, rating}. Rating is good|needs-improvement|poor.
      resources:
        type: object
        description: >
          Resource catalog: total_count, total_size_bytes,
          total_compressed_bytes, by_type {html, css, js, image, font}
      budget:
        type: object
        description: >
          Budget checks: total_weight, js_weight, image_weight,
          request_count. Each has budget, actual, pass fields.
      findings:
        type: array
        items: PerfFinding
        description: Performance issues and recommendations

  PerfFinding:
    description: A single performance issue or recommendation
    fields:
      rule_id:
        type: string
        format: "perf-{category}-{detail}"
        description: Unique rule identifier
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Issue severity
      category:
        type: string
        enum: [timing, cwv, resources, budget, optimization]
        description: Finding category
      url:
        type: string
        description: URL where issue was detected
      message:
        type: string
        max: 512
        description: Human-readable description
      evidence:
        type: string
        optional: true
        description: Specific measurement or resource causing the issue
      recommendation:
        type: string
        optional: true
        description: Actionable improvement suggestion

  ResourceBreakdown:
    description: Detailed resource catalog for a single URL
    fields:
      url:
        type: string
        description: The page URL
      resources:
        type: array
        description: >
          Each resource: url, type, size_bytes, compressed_bytes,
          compression, cache_control, render_blocking
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
        side_effect: emit perf.task.failed event
      - from: active
        to: degraded
        trigger: network_error
        validates: outbound HTTP consistently failing
      - from: degraded
        to: active
        trigger: network_recovered
        validates: HTTP request succeeds
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/perf-auditor/
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
  Action:      Test outbound HTTP connectivity
  Pre-check:   Steps 1-4 validated
  Validates:   Can reach at least one external URL
  On Fail:     Enter degraded state — log warning, continue
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9731, capabilities: [net:http, agent:message]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests

Step 3 — Drain In-Flight
  Action:      Wait for current audits to complete (up to config.audit_timeout)
  On Timeout:  Return partial results for URLs completed so far

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, urls_audited}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - outbound HTTP working
    response:
      status: healthy
      details: {state, uptime, urls_audited, last_task_at}

  degraded:
    conditions:
      - outbound HTTP intermittently failing
      - last audit timed out
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - outbound HTTP completely blocked
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
    actions: [audit, audit_resources]
    description: >
      Receive performance audit tasks from the health domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "perf-auditor"
    description: Self-update if perf-auditor blueprint changed
```

---

## Actions

### audit

Full performance audit of one or more URLs.

**Purpose:** Measure timing, Core Web Vitals, resource efficiency,
and budget compliance for each URL.

**Input:** `{urls: string[]}` — array of URLs to audit.

**Processing:**

```
1. Validate input:
   a. urls array is non-empty
   b. Array length <= config.max_urls_per_task
   c. All URLs are valid HTTP/HTTPS URLs
2. For each URL:
   a. Fetch page and all sub-resources (up to config.http_timeout per request)
   b. Record timing milestones: DNS, TCP, TLS, TTFB, FCP, LCP,
      DOM Content Loaded, full page load
   c. Assess Core Web Vitals:
      - LCP against config.lcp_good/poor thresholds
      - FID/INP estimated from script execution time
      - CLS from layout-shifting elements
   d. Catalog resources: count, size, compression, cache headers per type
   e. Check performance budgets against config.budget_* thresholds
   f. Identify optimization opportunities (uncompressed resources,
      render-blocking scripts, images without dimensions)
   g. Compute performance_score using weighted formula
   h. Build findings array
3. Return PerfResult[] to domain controller
```

**Output:** `{results: PerfResult[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty URL list, exceeds max_urls_per_task, or invalid URLs
    retryable: false
  - code: HTTP_ERROR
    condition: Target URL returns 4xx/5xx or connection refused
    retryable: true
  - code: HTTP_TIMEOUT
    condition: Request exceeds config.http_timeout
    retryable: true
  - code: AUDIT_TIMEOUT
    condition: Total audit exceeds config.audit_timeout
    retryable: true
  - code: TOO_MANY_REDIRECTS
    condition: Redirect chain exceeds config.max_redirects
    retryable: false
```

**Side Effects:** Makes outbound HTTP requests to target URLs.
No storage writes.

**Idempotency:** Results may vary between runs due to network
conditions, server response times, and content changes.

---

### audit_resources

Detailed resource breakdown for a single URL.

**Purpose:** Catalog all page resources with compression, caching,
and render-blocking details.

**Input:** `{url: string}` — single URL to analyze.

**Processing:**

```
1. Validate input: url is a valid HTTP/HTTPS URL
2. Fetch page and discover all sub-resources
3. For each resource:
   a. Record: URL, type, size, compressed size, compression method
   b. Record: cache-control header, render-blocking status
4. Return detailed resource list
```

**Output:** `{resources: ResourceBreakdown}`

**Errors:** `INVALID_INPUT` (permanent), `HTTP_ERROR` (transient),
`HTTP_TIMEOUT` (transient).

**Side Effects:** Makes outbound HTTP requests. No storage writes.

**Idempotency:** Results may vary between runs.

---

## Execute Workflow

```
1. RECEIVE URL list from health domain controller
   Input: {urls: ["https://example.com", "https://example.com/about"]}

2. FOR EACH URL:

   a. Load & Timing
      → Fetch the page and all sub-resources
      → Record timing milestones:
        DNS, TCP, TLS, TTFB, FCP, LCP, DOM Content Loaded, full load

   b. Core Web Vitals Assessment
      → LCP against configured thresholds
      → FID/INP estimated from script execution time
      → CLS from layout-shifting elements

   c. Resource Analysis
      → Catalog all resources by type
      → Check compression and cache headers
      → Flag uncompressed or uncached resources

   d. Performance Budget Check
      → Compare against config.budget_* thresholds

   e. Optimization Opportunities
      → Images without dimensions, unoptimized formats
      → Render-blocking scripts and CSS
      → Missing font preloads

3. SCORE each page using weighted formula

4. BUILD findings array with severity and recommendations

5. RETURN PerfResult[] to health domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: perf.audit.completed
    payload: {task_id, url_count, avg_score, cwv_summary}
    when: audit action completes successfully

  - topic: perf.score.poor
    payload: {task_id, url, performance_score, lcp_ms, cls}
    when: URL scores below 50 on performance

  - topic: perf.budget.exceeded
    payload: {task_id, url, budget_type, budget, actual}
    when: Performance budget exceeded for a URL

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "perf-auditor"
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
  full-auto:     All auditing is autonomous
  supervised:    Operator can adjust budgets and thresholds
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: performance_budgets
    default: total 1MB, JS 300KB, images 500KB, 50 requests
    override: Set WL_PERF_BUDGET_* environment variables
    audit: logged

  - behavior: cwv_thresholds
    default: LCP good ≤2500ms, poor >4000ms
    override: Set WL_PERF_LCP_GOOD / WL_PERF_LCP_POOR
    audit: logged

  - behavior: http_timeout
    default: 30 seconds
    override: Set WL_PERF_HTTP_TIMEOUT
    audit: logged

manual_actions:
  - action: run_audit
    description: Manually trigger a performance audit via CLI
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
    - MUST NOT access the local file system (network-based auditing only)
    - MUST NOT send attack payloads or perform active exploitation
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT modify any remote resources
    - MUST NOT POST, PUT, or DELETE to target URLs (GET and HEAD only)
    - MUST NOT follow redirects to non-HTTPS URLs
    - MUST NOT cache audit results between tasks

  resource_limits:
    memory: 256 MB (process limit)
    max_urls_per_task: config.max_urls_per_task (default 20)
    max_concurrent_http: 10 per URL (sub-resource fetches)
    http_timeout: config.http_timeout per request
    audit_timeout: config.audit_timeout per task
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: URL list empty, exceeds limit, or contains invalid URLs
    - code: TOO_MANY_REDIRECTS
      description: Redirect chain exceeds config.max_redirects
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: HTTP_ERROR
      description: Target URL returns error status or connection refused
      fallback: Skip URL, include in partial results with error note
    - code: HTTP_TIMEOUT
      description: Request exceeds config.http_timeout
      fallback: Skip URL, include in partial results with timeout note
    - code: AUDIT_TIMEOUT
      description: Total audit exceeds config.audit_timeout
      fallback: Return partial results for URLs completed so far
    - code: REGISTRATION_FAILED
      description: Could not register with orchestrator
      fallback: Retry 3x with exponential backoff, then exit
    - code: DNS_RESOLUTION_FAILED
      description: Could not resolve hostname for target URL
      fallback: Skip URL with DNS error note
```

---

## Observability

```yaml
custom_log_types:
  - log_type: perf.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, url_count, trace_id}

  - log_type: perf.audit.completed
    level: info
    when: Audit completed for a URL
    fields: {task_id, url, performance_score, lcp_ms, duration_ms}

  - log_type: perf.task.failed
    level: warn
    when: Audit failed for a URL
    fields: {task_id, url, error_code}

  - log_type: perf.budget.exceeded
    level: warn
    when: Performance budget exceeded
    fields: {url, budget_type, budget, actual}

metrics:
  - name: wl_perf_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks by action and outcome

  - name: wl_perf_audit_duration_seconds
    type: histogram
    description: Per-URL audit duration

  - name: wl_perf_score_distribution
    type: histogram
    description: Distribution of performance scores (0-100)

  - name: wl_perf_lcp_seconds
    type: histogram
    description: LCP measurements across audited URLs

  - name: wl_perf_page_weight_bytes
    type: histogram
    description: Total page weight across audited URLs

  - name: wl_perf_budget_violations_total
    type: counter
    labels: [budget_type]
    description: Budget violations by type

alerts:
  - condition: Error rate > 30% of URLs in a task
    severity: warn
    routing: alerting agent

  - condition: All URLs failing (network outage)
    severity: critical
    routing: alerting agent

  - condition: Average LCP > 4000ms across last 10 audits
    severity: warn
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: net:http
      resources: ["*"]
      description: Make outbound HTTP GET/HEAD requests to target URLs

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTTP response headers
      classification: low
      handling: Analyzed in memory, not persisted

    - data: HTTP response bodies
      classification: low
      handling: Parsed for resource discovery, not stored

    - data: Timing measurements
      classification: low
      handling: Returned to domain controller in PerfResult

    - data: Target URLs
      classification: low
      handling: Logged in audit records

  access_control:
    - caller: Domain controller (health)
      actions: [audit, audit_resources]

    - caller: Operator (auth token with operator role)
      actions: [audit, audit_resources]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Audit fast page
    action: audit
    input:
      urls: ["https://example.com"]
    expected:
      results:
        - url: "https://example.com"
          performance_score: ">= 80"
          core_web_vitals:
            lcp: {rating: "good"}
          budget: {total_weight: {pass: true}}
    validates:
      - Fast page scores above 80
      - CWV rated correctly
      - Budget check passes

  - name: Audit resources breakdown
    action: audit_resources
    input: {url: "https://example.com"}
    expected:
      resources:
        url: "https://example.com"
        resources: [{type: "html"}, {type: "css"}]
    validates:
      - Resources cataloged by type with size and compression
```

### Error Cases

```yaml
  - name: Empty URL list
    action: audit
    input: {urls: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: Unreachable URL
    action: audit
    input: {urls: ["https://does-not-exist.example.com"]}
    expected_error: DNS_RESOLUTION_FAILED
    validates: [DNS failure produces transient error]

  - name: Too many redirects
    action: audit
    input: {urls: ["https://redirect-loop.example.com"]}
    expected_error: TOO_MANY_REDIRECTS
    validates: [Redirect chain limit enforced]
```

### Edge Cases

```yaml
  - name: URL with slow LCP
    action: audit
    input: {urls: ["https://slow-page.example.com"]}
    condition: LCP > 4000ms
    expected:
      results:
        - core_web_vitals: {lcp: {rating: "poor"}}
          findings: [{rule_id: "perf-cwv-lcp-poor", severity: "high"}]
    validates: [Poor LCP detected and reported]

  - name: Budget exceeded
    action: audit
    input: {urls: ["https://heavy-page.example.com"]}
    condition: Total page weight > 1 MB
    expected:
      results:
        - budget: {total_weight: {pass: false}}
    validates: [Budget violation detected]

  - name: Mixed HTTP/HTTPS resources
    action: audit
    input: {urls: ["https://mixed-content.example.com"]}
    expected:
      findings: [{rule_id: "perf-resources-mixed-content", severity: "high"}]
    validates: [Mixed content flagged as security/performance issue]

  - name: Partial results on timeout
    action: audit
    input: {urls: ["https://url1.com", "https://url2.com", "https://url3.com"]}
    condition: Third URL times out
    expected: Results for first two URLs returned, third has error note
    validates: [Partial results returned on timeout]
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
        Stateless agent. Each audit is independent with all
        inputs in the task payload.

  event_handling:
    consumer_group: perf-auditor
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "perf-auditor@vN+1"
      after_cutover: "perf-auditor"
```

---

## Implementation Notes

- **Timing Measurement**: Use high-resolution timers for all timing
  milestones. DNS, TCP, and TLS times are measured from the initial
  connection. FCP and LCP require parsing the response to identify
  the first contentful element and the largest element.
- **CLS Estimation**: Without a real browser, CLS is estimated by
  identifying common layout-shift causes: images without explicit
  width/height attributes, dynamically loaded fonts, and content
  injected above the fold. This is a heuristic — real CLS requires
  browser rendering.
- **FID/INP Estimation**: Estimated from total JavaScript execution
  time and script size. Long tasks (>50ms script execution) contribute
  to estimated input delay. This is an approximation — real FID
  requires user interaction measurement.
- **Resource Discovery**: Sub-resources are discovered by parsing HTML
  for `<link>`, `<script>`, `<img>`, and `<style>` elements. CSS
  `@import` and JavaScript dynamic imports are not followed.
- **Compression Detection**: Check `Content-Encoding` response header
  for gzip, brotli, or deflate. Resources without compression are
  flagged if they exceed 1 KB.
- **Scoring Formula**: `performance_score = weighted(lcp: 0.25,
  fcp: 0.15, ttfb: 0.15, cls: 0.15, page_weight: 0.15,
  request_count: 0.15)`. Each component normalized to 0-100 based
  on threshold ranges.
- **User-Agent**: All requests include `User-Agent: Weblisk-Perf-Auditor/1.0`.

### Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤ 2500ms | 2500–4000ms | > 4000ms |
| FID/INP | ≤ 100ms | 100–300ms | > 300ms |
| CLS | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| TTFB | ≤ 800ms | 800–1800ms | > 1800ms |
| FCP | ≤ 1800ms | 1800–3000ms | > 3000ms |

### Performance Budget Defaults

| Resource | Budget | Severity if exceeded |
|----------|--------|---------------------|
| Total page weight | 1 MB | high |
| JavaScript | 300 KB | high |
| Images | 500 KB | medium |
| CSS | 100 KB | medium |
| Fonts | 200 KB | low |
| Total requests | 50 | medium |

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: health, port: 9731
- [ ] Uses net:http capability (no file system access)
- [ ] Measures TTFB, FCP, LCP, and CLS for each URL
- [ ] Catalogs all page resources by type and size
- [ ] Checks resource compression (gzip/brotli)
- [ ] Evaluates performance budgets against configured thresholds
- [ ] Identifies render-blocking resources
- [ ] Flags images without dimensions (CLS contributors)
- [ ] Scores pages on 0–100 scale with weighted components
- [ ] Returns PerfResult per URL with all required fields
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded, and retiring states
- [ ] Startup sequence has pre-check, validates, on-fail for each step
- [ ] Shutdown drains in-flight audits before deregistering
- [ ] Health endpoint reports accurate status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for tasks, scores, LCP, page weight, and budget violations
- [ ] Security permissions limited to net:http and agent:message
- [ ] Constraints enforce GET/HEAD only — no POST/PUT/DELETE to targets
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
