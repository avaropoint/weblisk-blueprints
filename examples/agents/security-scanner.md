<!-- blueprint
type: agent
kind: work
name: security-scanner
version: 1.1.0
port: 9712
extends: [patterns/observability, patterns/scope, patterns/policy, patterns/security]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain, architecture/gateway]
platform: any
tier: free
domain: security
-->

# Security Scanner Agent

Work agent for the security domain. Performs HTTP header analysis,
Content Security Policy validation, dependency vulnerability
auditing, and OWASP Top 10 static checks. Produces structured
findings that the security domain controller converts into
observations and recommendations.

## Overview

The security-scanner is a passive analysis agent — it reads
configuration files, fetches HTTP headers, and cross-references
dependency versions against vulnerability databases. It does NOT
send attack payloads, fuzz inputs, or perform active exploitation.

The agent supports five task actions: `scan-headers`, `scan-csp`,
`scan-dependencies`, `scan-owasp`, and `compile-report`. These may
be dispatched individually or chained by the security domain controller
during a full security audit workflow. The `compile-report` action
aggregates results from all scan phases into a weighted composite
score with an executive summary.

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

  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: outbound-http
          parameters: [url, method, headers, timeout]
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
  scan_timeout:
    type: int
    default: 120
    env: WL_SECSCAN_TIMEOUT
    min: 30
    max: 600
    unit: seconds
    description: Maximum time for a single scan task

  http_timeout:
    type: int
    default: 30
    env: WL_SECSCAN_HTTP_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Timeout for individual HTTP requests

  max_urls_per_scan:
    type: int
    default: 50
    env: WL_SECSCAN_MAX_URLS
    min: 1
    max: 200
    description: Maximum URLs in a single header/CSP/OWASP scan

  max_concurrent_http:
    type: int
    default: 50
    env: WL_SECSCAN_MAX_CONCURRENT
    min: 1
    max: 100
    description: Maximum concurrent outbound HTTP requests

  max_dependencies:
    type: int
    default: 5000
    env: WL_SECSCAN_MAX_DEPS
    min: 100
    max: 50000
    description: Maximum packages per manifest for dependency scan

  max_redirects:
    type: int
    default: 5
    env: WL_SECSCAN_MAX_REDIRECTS
    min: 0
    max: 10
    description: Maximum HTTP redirect chain length

  vulndb_url:
    type: string
    default: "file://vulndb.json"
    env: WL_VULNDB
    description: >
      Vulnerability database backend URL.
      file:// — local snapshot (default, zero-dependency);
      https://api.osv.dev — Google OSV API;
      ghsa:// — GitHub Advisory DB via CLI token;
      https://your-api.com — custom enterprise DB.

  score_weight_headers:
    type: float
    default: 0.25
    description: Weight of headers score in composite

  score_weight_csp:
    type: float
    default: 0.20
    description: Weight of CSP score in composite

  score_weight_deps:
    type: float
    default: 0.25
    description: Weight of dependencies score in composite

  score_weight_owasp:
    type: float
    default: 0.30
    description: Weight of OWASP score in composite
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  SecurityFinding:
    description: A single security finding from any scan phase
    fields:
      id:
        type: string
        format: "{phase}-{detail}-{seq}"
        description: Unique finding identifier
      category:
        type: string
        enum: [headers, csp, dependencies, owasp]
        description: Scan phase that produced this finding
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Finding severity
      title:
        type: string
        max: 256
        description: Human-readable title
      target:
        type: string
        description: URL or dependency affected
      evidence:
        type: string
        description: Specific header, directive, or version
      remediation:
        type: string
        description: Actionable fix recommendation
      cwe:
        type: string
        optional: true
        description: CWE identifier (e.g., CWE-200)
      cvss:
        type: float
        optional: true
        min: 0.0
        max: 10.0
        description: CVSS score (dependency findings only)
      references:
        type: array
        items: string
        optional: true
        description: Reference URLs (NVD, GHSA, etc.)

  ScanPhaseResult:
    description: Result from a single scan phase
    fields:
      phase:
        type: string
        enum: [headers, csp, dependencies, owasp]
        description: Phase name
      findings:
        type: array
        items: SecurityFinding
        description: Findings from this phase
      score:
        type: int
        min: 0
        max: 100
        description: Phase score

  SecurityReport:
    description: Composite security report from compile-report
    fields:
      security_score:
        type: int
        min: 0
        max: 100
        description: Weighted composite score
      grade:
        type: string
        enum: [Excellent, Good, Fair, Poor, Critical]
        description: >
          Excellent (90-100), Good (75-89), Fair (60-74),
          Poor (40-59), Critical (0-39)
      summary:
        type: string
        description: Executive summary text
      category_scores:
        type: object
        description: >
          Score per phase: headers, csp, dependencies, owasp
      findings_count:
        type: object
        description: >
          Count by severity: critical, high, medium, low, info
      findings:
        type: array
        items: SecurityFinding
        description: All findings sorted by severity
      recommendations:
        type: array
        description: >
          Prioritized recommendations: {priority, action, impact}

  Vulnerability:
    description: Vulnerability record from VulnDB
    fields:
      cve:
        type: string
        description: CVE identifier
      cvss:
        type: float
        description: CVSS base score
      affected_ranges:
        type: array
        description: Affected version ranges
      fixed_version:
        type: string
        optional: true
        description: Version with fix
      references:
        type: array
        items: string
        description: Reference URLs
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
        side_effect: emit security.task.failed event
      - from: active
        to: degraded
        trigger: vulndb_unavailable
        validates: VulnDB queries consistently failing
      - from: degraded
        to: active
        trigger: vulndb_recovered
        validates: VulnDB query succeeds
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/security-scanner/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize VulnDB
  Action:      Load or connect to vulnerability database per config.vulndb_url
  Pre-check:   Steps 1-2 validated
  Validates:   Can query VulnDB (test query for known CVE)
  On Fail:     Enter degraded state — dependency scans disabled, log warning
  Backout:     None

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-2 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 5 — Subscribe to Events
  Action:      Subscribe to: system.shutdown, system.blueprint.changed
  Pre-check:   Step 4 validated
  Validates:   Subscriptions acknowledged
  On Fail:     Deregister → EXIT with SUBSCRIPTION_FAILED
  Backout:     Unsubscribe all, deregister

Final:
  agent_state → active (or degraded if VulnDB unavailable)
  Log: lifecycle.ready {port: 9712, capabilities: [file:read, http:get, llm:chat]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests

Step 3 — Drain In-Flight
  Action:      Wait for current scans to complete (up to config.scan_timeout)
  On Timeout:  Return partial results for completed phases

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, scans_completed}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - VulnDB accessible
    response:
      status: healthy
      details: {state, uptime, scans_completed, vulndb_status}

  degraded:
    conditions:
      - VulnDB unavailable (dependency scans disabled)
      - HTTP outbound intermittently failing
    response:
      status: degraded
      details: {reason, disabled_actions, last_error}

  unhealthy:
    conditions:
      - registration lost
      - all outbound connectivity failed
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
    actions: [scan-headers, scan-csp, scan-dependencies, scan-owasp, compile-report]
    description: >
      Receive security scan tasks from the security domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "security-scanner"
    description: Self-update if security-scanner blueprint changed
```

---

## Actions

### scan-headers

Fetch HTTP response headers and check for security headers.

**Purpose:** Evaluate presence and correctness of HTTP security
headers (HSTS, X-Content-Type-Options, X-Frame-Options,
Referrer-Policy, Permissions-Policy, etc.).

**Input:** `{urls: string[]}` — URLs to scan.

**Processing:**

```
1. Validate input: urls non-empty, <= config.max_urls_per_scan
2. For each URL:
   a. Send HEAD request (follow redirects up to config.max_redirects)
   b. If HEAD not supported, fall back to GET
   c. Collect response headers
   d. Check each security header against expected values:
      - Strict-Transport-Security (HSTS)
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY or SAMEORIGIN
      - Referrer-Policy
      - Permissions-Policy
      - Content-Security-Policy (presence check — deep analysis in scan-csp)
      - X-XSS-Protection (deprecated but flagged if absent)
   e. Generate SecurityFinding for each missing/misconfigured header
3. Calculate headers phase score
4. Return {urls_scanned, findings, score}
```

**Output:** `{urls_scanned: int, findings: SecurityFinding[], score: int}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty URL list, exceeds limit, or invalid URLs
    retryable: false
  - code: HTTP_ERROR
    condition: Target URL returns error or connection refused
    retryable: true
  - code: HTTP_TIMEOUT
    condition: Request exceeds config.http_timeout
    retryable: true
```

**Side Effects:** Makes outbound HEAD/GET requests. No storage writes.

**Idempotency:** Deterministic for the same input and server state.

---

### scan-csp

Parse and validate Content Security Policy.

**Purpose:** Deep analysis of CSP headers and meta tags for unsafe
directives, wildcards, missing protections, and reporting config.

**Input:** `{urls: string[]}` — URLs to scan.

**Processing:**

```
1. Validate input
2. For each URL:
   a. GET request (need body for meta-tag CSP)
   b. Extract CSP from header and meta tags; merge per spec
   c. Parse into directive map: {directive: [sources]}
   d. Check each directive:
      - unsafe-inline in script-src?
      - unsafe-eval in script-src?
      - wildcard * in script-src?
      - default-src present?
      - frame-ancestors present?
      - base-uri restricted?
      - form-action restricted?
      - report-uri / report-to configured?
   e. Generate SecurityFinding per failed check
3. Return {urls_scanned, csp_present, directives_found, findings, score}
```

**Output:** `{urls_scanned: int, csp_present: bool, directives_found: string[], findings: SecurityFinding[], score: int}`

**Errors:** `INVALID_INPUT` (permanent), `HTTP_ERROR` (transient),
`HTTP_TIMEOUT` (transient).

**Side Effects:** Makes outbound GET requests. No storage writes.

**Idempotency:** Deterministic for the same input and server state.

---

### scan-dependencies

Read dependency manifests and check for known vulnerabilities.

**Purpose:** Cross-reference project dependencies against the
configured vulnerability database (VulnDB).

**Input:** `{manifest_paths: string[]}` — paths to manifest/lock
files. If omitted, auto-detect by scanning for known manifest
filenames in the project root.

**Processing:**

```
1. Read manifest files via file:read capability
2. Parse dependency tree with locked versions
3. For each dependency (batched queries):
   a. Query VulnDB: Query(ecosystem, package, version)
   b. Match version against affected ranges
   c. If vulnerable → create SecurityFinding with CVE, CVSS, fix version
4. Cap at config.max_dependencies per manifest
5. Calculate dependency phase score
6. Return {manifests_scanned, total_dependencies, vulnerable, findings, score}
```

**Output:** `{manifests_scanned: string[], total_dependencies: int, vulnerable: int, findings: SecurityFinding[], score: int}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: No manifest files found or specified
    retryable: false
  - code: VULNDB_UNAVAILABLE
    condition: Cannot connect to vulnerability database
    retryable: true
  - code: MANIFEST_PARSE_ERROR
    condition: Manifest file is malformed
    retryable: false
  - code: FILE_NOT_FOUND
    condition: Specified manifest path does not exist
    retryable: false
```

**Side Effects:** Reads manifest files via file:read. May make
outbound HTTP requests if VulnDB is a remote API.

**Idempotency:** Deterministic for the same input, modulo VulnDB updates.

---

### scan-owasp

Static checks for OWASP Top 10 categories.

**Purpose:** Passive checks for automatable OWASP categories:
Broken Access Control (A01), Cryptographic Failures (A02),
Security Misconfiguration (A05), and Auth Failures (A07).

**Input:** `{urls: string[], check_categories: string[]}` — URLs
to scan and optional category filter. If `check_categories` is
omitted, all automatable categories are checked.

**Processing:**

```
1. Validate input
2. For each URL:
   A01 — Broken Access Control:
     → Check CORS headers (Access-Control-Allow-Origin)
     → Check for directory listing (GET common paths)
     → Check for sensitive path exposure (/admin, /.env, /.git)
   A02 — Cryptographic Failures:
     → Check TLS version (must be >= 1.2)
     → Check for mixed content
     → Check cookie Secure flag
   A05 — Security Misconfiguration:
     → Check for server version disclosure (Server header)
     → Check for default error pages (trigger 404, inspect body)
     → Check for debug info disclosure (X-Powered-By, etc.)
   A07 — Auth Failures:
     → Check cookie HttpOnly flag
     → Check cookie SameSite attribute
     → Check session ID entropy (if observable)
3. Flag non-automatable categories for manual_review:
   A03, A04, A06, A08, A09, A10
4. Return {categories_checked, findings, manual_review, score}
```

**Output:** `{categories_checked: string[], findings: SecurityFinding[], manual_review: string[], score: int}`

**Errors:** `INVALID_INPUT` (permanent), `HTTP_ERROR` (transient).

**Side Effects:** Makes outbound GET requests. No storage writes.

**Idempotency:** Deterministic for the same input and server state.

---

### compile-report

Aggregate findings from all scan phases into a security report.

**Purpose:** Merge, deduplicate, and score findings from all phases
into a single composite report with recommendations.

**Input:** `{phase_results: ScanPhaseResult[]}` — results from
each scan phase.

**Processing:**

```
1. Merge all findings, deduplicate by ID
2. Calculate composite score:
   composite = (headers × 0.25) + (csp × 0.20)
             + (deps × 0.25) + (owasp × 0.30)
3. Assign grade: Excellent (90-100), Good (75-89), Fair (60-74),
   Poor (40-59), Critical (0-39)
4. Sort findings by severity (critical → info)
5. Generate executive summary (LLM if available, template otherwise)
6. Build prioritized recommendations
7. Return SecurityReport
```

**Output:** `{SecurityReport}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty phase_results or malformed results
    retryable: false
  - code: LLM_UNAVAILABLE
    condition: LLM not available for summary generation
    retryable: false
    fallback: Use template-based summary
```

**Side Effects:** May invoke LLM for summary. No storage writes.

**Idempotency:** Deterministic for the same input (LLM summary may
vary slightly between calls).

---

## Execute Workflow

```
1. RECEIVE scan task from security domain controller
   Input: {action, payload}

2. DISPATCH to appropriate action handler:
   a. scan-headers  → fetch headers, check security headers
   b. scan-csp      → fetch CSP, parse directives, validate
   c. scan-dependencies → read manifests, query VulnDB
   d. scan-owasp    → check automatable OWASP categories
   e. compile-report → aggregate phase results into SecurityReport

3. FULL AUDIT WORKFLOW (when domain controller chains all phases):
   Phase 1: scan-headers  → ScanPhaseResult (headers)
   Phase 2: scan-csp      → ScanPhaseResult (csp)
   Phase 3: scan-dependencies → ScanPhaseResult (dependencies)
   Phase 4: scan-owasp    → ScanPhaseResult (owasp)
   Phase 5: compile-report({phase_results: [1, 2, 3, 4]})
            → SecurityReport with composite score

4. RETURN result to security domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: security.scan.completed
    payload: {task_id, action, score, finding_count}
    when: Any scan action completes

  - topic: security.finding.critical
    payload: {task_id, finding_id, title, target, cvss}
    when: Critical severity finding detected

  - topic: security.report.ready
    payload: {task_id, security_score, grade, critical_count}
    when: compile-report completes

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "security-scanner"
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
  full-auto:     All scanning is autonomous
  supervised:    Operator can adjust VulnDB source and score weights
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: vulndb_backend
    default: "file://vulndb.json"
    override: Set WL_VULNDB environment variable
    audit: logged

  - behavior: score_weights
    default: headers 0.25, csp 0.20, deps 0.25, owasp 0.30
    override: Update config.score_weight_* values
    audit: logged

  - behavior: scan_limits
    default: 50 URLs, 5000 dependencies
    override: Set WL_SECSCAN_MAX_URLS / WL_SECSCAN_MAX_DEPS
    audit: logged

manual_actions:
  - action: run_scan
    description: Manually trigger a security scan via CLI
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
    - MUST NOT send attack payloads, fuzz inputs, or perform active exploitation
    - MUST NOT modify any target resources
    - MUST NOT write to the local file system (reads only)
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT POST, PUT, or DELETE to target URLs (GET and HEAD only)
    - MUST NOT follow redirects to non-HTTPS URLs
    - MUST NOT exfiltrate sensitive data from manifest files
    - MUST NOT send dependency names or versions to third parties
      (unless using explicitly configured remote VulnDB)

  resource_limits:
    memory: 512 MB (process limit)
    max_urls_per_scan: config.max_urls_per_scan (default 50)
    max_concurrent_http: config.max_concurrent_http (default 50)
    max_dependencies: config.max_dependencies (default 5000)
    http_timeout: config.http_timeout per request (default 30s)
    scan_timeout: config.scan_timeout per task (default 120s)
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: Invalid URLs, empty input, or exceeds limits
    - code: MANIFEST_PARSE_ERROR
      description: Dependency manifest is malformed
    - code: FILE_NOT_FOUND
      description: Specified manifest path does not exist
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: HTTP_ERROR
      description: Target URL returns error or connection refused
      fallback: Skip URL, include in partial results with error note
    - code: HTTP_TIMEOUT
      description: Request exceeds config.http_timeout
      fallback: Skip URL with timeout note
    - code: VULNDB_UNAVAILABLE
      description: Cannot reach vulnerability database
      fallback: Skip dependency scan, enter degraded state
    - code: LLM_UNAVAILABLE
      description: LLM service unreachable for report summary
      fallback: Generate template-based summary
    - code: REGISTRATION_FAILED
      description: Could not register with orchestrator
      fallback: Retry 3x with exponential backoff, then exit
    - code: SCAN_TIMEOUT
      description: Total scan exceeds config.scan_timeout
      fallback: Return partial results for completed phases
```

---

## Observability

```yaml
custom_log_types:
  - log_type: security.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, trace_id}

  - log_type: security.scan.completed
    level: info
    when: Scan phase completed
    fields: {task_id, action, finding_count, score, duration_ms}

  - log_type: security.finding.critical
    level: warn
    when: Critical finding detected
    fields: {task_id, finding_id, title, target, cvss}

  - log_type: security.vulndb.query
    level: debug
    when: VulnDB queried
    fields: {ecosystem, package, version, vulnerabilities_found}

  - log_type: security.report.ready
    level: info
    when: compile-report completes
    fields: {task_id, security_score, grade, total_findings}

metrics:
  - name: wl_secscan_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks by action and outcome

  - name: wl_secscan_findings_total
    type: counter
    labels: [category, severity]
    description: Findings by category and severity

  - name: wl_secscan_score
    type: gauge
    labels: [phase]
    description: Most recent score per phase

  - name: wl_secscan_scan_duration_seconds
    type: histogram
    labels: [action]
    description: Scan duration by action

  - name: wl_secscan_vulndb_query_duration_seconds
    type: histogram
    description: VulnDB query latency

  - name: wl_secscan_vulnerable_deps_total
    type: counter
    labels: [ecosystem, severity]
    description: Vulnerable dependencies by ecosystem and severity

alerts:
  - condition: Critical finding detected
    severity: critical
    routing: alerting agent

  - condition: VulnDB unavailable for > 10 minutes
    severity: warn
    routing: alerting agent

  - condition: Security score < 40 (Critical grade)
    severity: high
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: file:read
      resources: ["**/*.json", "**/*.lock", "**/*.toml", "**/*.txt", "**/*.mod", "**/*.sum"]
      description: Read dependency manifests and lock files

    - capability: http:get
      resources: ["*"]
      description: Fetch HTTP headers and page content for analysis

    - capability: llm:chat
      resources: ["*"]
      description: Generate executive summaries for reports (optional)

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTTP response headers
      classification: low
      handling: Analyzed in memory, included in findings

    - data: CSP directives
      classification: low
      handling: Parsed and validated, included in findings

    - data: Dependency names and versions
      classification: medium
      handling: >
        Read from local manifests. Sent to VulnDB for lookup
        only if config.vulndb_url is a remote API. Never sent
        to any other external service.

    - data: Vulnerability details (CVE, CVSS)
      classification: low
      handling: Retrieved from VulnDB, included in findings

    - data: Cookie attributes
      classification: medium
      handling: >
        Only security-relevant attributes checked (HttpOnly,
        Secure, SameSite). Cookie values are NOT read or logged.

  access_control:
    - caller: Domain controller (security)
      actions: [scan-headers, scan-csp, scan-dependencies, scan-owasp, compile-report]

    - caller: Operator (auth token with operator role)
      actions: [scan-headers, scan-csp, scan-dependencies, scan-owasp, compile-report]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Scan headers on secure site
    action: scan-headers
    input:
      urls: ["https://secure-example.com"]
    expected:
      urls_scanned: 1
      score: ">= 90"
      findings: []
    validates:
      - All security headers present and correctly configured

  - name: Scan dependencies with no vulnerabilities
    action: scan-dependencies
    input:
      manifest_paths: ["package.json", "package-lock.json"]
    expected:
      vulnerable: 0
      score: 100
    validates:
      - Clean dependency tree produces perfect score

  - name: Compile full report
    action: compile-report
    input:
      phase_results:
        - {phase: "headers", findings: [], score: 95}
        - {phase: "csp", findings: [], score: 90}
        - {phase: "dependencies", findings: [], score: 100}
        - {phase: "owasp", findings: [], score: 85}
    expected:
      security_score: 92
      grade: "Excellent"
    validates:
      - Weighted score calculated correctly
      - Grade assigned based on score range
```

### Error Cases

```yaml
  - name: Empty URL list
    action: scan-headers
    input: {urls: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: Manifest file not found
    action: scan-dependencies
    input: {manifest_paths: ["nonexistent.json"]}
    expected_error: FILE_NOT_FOUND
    validates: [Missing file produces clear error]

  - name: VulnDB unavailable
    action: scan-dependencies
    input: {manifest_paths: ["package.json"]}
    condition: VulnDB endpoint unreachable
    expected_error: VULNDB_UNAVAILABLE
    validates: [VulnDB failure handled gracefully]
```

### Edge Cases

```yaml
  - name: CSP with unsafe-inline
    action: scan-csp
    input: {urls: ["https://unsafe-csp.example.com"]}
    condition: CSP contains unsafe-inline in script-src
    expected:
      findings: [{id: "csp-unsafe-inline-001", severity: "high"}]
    validates: [unsafe-inline detected and flagged]

  - name: Dependency with known CVE
    action: scan-dependencies
    input: {manifest_paths: ["package-lock.json"]}
    condition: lodash@4.17.20 installed (CVE-2024-1234)
    expected:
      vulnerable: ">= 1"
      findings: [{category: "dependencies", severity: "critical", cvss: 9.8}]
    validates: [Known vulnerability detected with CVE and fix version]

  - name: OWASP with partial category filter
    action: scan-owasp
    input: {urls: ["https://example.com"], check_categories: ["A01", "A05"]}
    expected:
      categories_checked: ["A01", "A05"]
      manual_review: ["A02", "A03", "A04", "A06", "A07", "A08", "A09", "A10"]
    validates: [Only requested categories checked, others listed as manual_review]

  - name: Report without LLM
    action: compile-report
    input:
      phase_results:
        - {phase: "headers", findings: [{severity: "high"}], score: 60}
    condition: LLM capability not available
    expected:
      summary: "Template-based summary present"
    validates: [Report generated with template summary when LLM unavailable]
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
        Stateless agent. Each scan task is self-contained.
        VulnDB is an external data source, not shared state.

  event_handling:
    consumer_group: security-scanner
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "security-scanner@vN+1"
      after_cutover: "security-scanner"
```

---

## Implementation Notes

- **HEAD vs GET**: Header scans use HEAD requests (faster, less data)
  but fall back to GET for servers that don't support HEAD. CSP and
  OWASP scans require GET to inspect response bodies and meta tags.
- **CSP Merging**: CSP parsing must handle both header-based and
  meta-tag-based policies and merge them correctly per the CSP Level 3
  specification. When both sources exist, the most restrictive policy
  applies.
- **Dependency Batching**: VulnDB lookups should be batched (not one
  HTTP request per package) using bulk query APIs where available.
  The OSV API supports batch queries of up to 1000 packages.
- **LLM Summary**: The `compile-report` LLM call is optional. If no
  `llm:chat` capability is available, the agent generates a
  template-based summary from finding counts and scores.
- **User-Agent**: All outbound HTTP requests include
  `User-Agent: Weblisk-Security-Scanner/1.0`.
- **HTTPS Only**: The agent MUST NOT follow redirects from HTTPS to HTTP.
- **Determinism**: Scan results are deterministic for the same input,
  modulo vulnerability database updates and LLM variation.
- **Auto-Detection**: When `manifest_paths` is omitted from
  `scan-dependencies`, the agent scans the project root for known
  manifest filenames: `package.json`, `package-lock.json`, `yarn.lock`,
  `pnpm-lock.yaml`, `Cargo.lock`, `Cargo.toml`, `go.mod`, `go.sum`,
  `requirements.txt`, `Pipfile.lock`, `poetry.lock`.

### Vulnerability Database Interface

The VulnDB backend is configured via `WL_VULNDB`:

| Backend | Configuration | Use Case |
|---------|--------------|----------|
| Local snapshot | `file://vulndb.json` | Offline, air-gapped, zero-dependency |
| OSV API | `https://api.osv.dev` | Google's open vulnerability DB (free) |
| GitHub Advisory DB | `ghsa://` | Via `weblisk-cli` GitHub token |
| Custom | `https://your-api.com` | Enterprise internal DB |

```
VulnDB Interface:
  Query(ecosystem string, package string, version string)
    → []Vulnerability{CVE, CVSS, affected_ranges, fixed_version, references}
```

The weblisk-cli ships a bundled OSV snapshot usable offline. It
updates on `weblisk update`.

### Score Formula

```
composite = (headers × 0.25) + (csp × 0.20) + (deps × 0.25) + (owasp × 0.30)
```

Grade bands: Excellent (90-100), Good (75-89), Fair (60-74),
Poor (40-59), Critical (0-39).

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: security, port: 9712
- [ ] Agent is passive — reads files and fetches headers only, no attack payloads
- [ ] scan-headers uses HEAD with GET fallback; checks all standard security headers
- [ ] scan-csp detects unsafe-inline, unsafe-eval, wildcard *, missing default-src, frame-ancestors, base-uri
- [ ] scan-dependencies auto-detects manifests when paths omitted; queries VulnDB with CVE, CVSS, fix version
- [ ] scan-owasp checks automatable categories; returns manual_review list for others
- [ ] compile-report uses weighted formula and deduplicates findings by ID
- [ ] All outbound HTTP requests include User-Agent: Weblisk-Security-Scanner/1.0
- [ ] Agent does NOT follow redirects to non-HTTPS URLs
- [ ] Scan results deterministic for same input (modulo VulnDB/LLM)
- [ ] HTTP requests limited to config.max_concurrent_http with timeout
- [ ] Dependency parsing caps at config.max_dependencies per manifest
- [ ] LLM call for report summary is optional — template fallback works
- [ ] Each finding includes id, category, severity, title, target, evidence, remediation
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded, and retiring states
- [ ] Startup sequence validates VulnDB connectivity; degrades gracefully if unavailable
- [ ] Shutdown drains in-flight scans before deregistering
- [ ] Health endpoint reports VulnDB status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for tasks, findings, scores, and VulnDB query latency
- [ ] Security permissions limited to file:read, http:get, llm:chat, agent:message
- [ ] Constraints enforce passive-only scanning — no POST/PUT/DELETE to targets
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
