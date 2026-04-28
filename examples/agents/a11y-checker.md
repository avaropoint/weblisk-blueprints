<!-- blueprint
type: agent
kind: work
name: a11y-checker
version: 1.1.0
port: 9711
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
extends: [patterns/observability, patterns/scope, patterns/policy, patterns/security]
depends_on: []
platform: any
tier: free
domain: seo
-->

# Accessibility Checker Agent

Work agent that evaluates HTML files for accessibility compliance.
Dispatched by domain controllers (primarily SEO) that need
accessibility input as part of their workflows.

## Overview

The a11y-checker agent performs static accessibility analysis on HTML
files. It evaluates alt text quality, heading hierarchy, ARIA
landmarks, form labels, language declarations, and link text against
WCAG 2.1 Level AA guidelines. The agent receives tasks from domain
controllers (primarily the SEO domain), runs its checks against the
provided file list, and returns structured findings with severity
levels and measurements.

The agent is stateless — it does not persist results. All findings
are returned to the dispatching domain controller, which is
responsible for storage, scoring, and lifecycle tracking.

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
          request_type: AgentMessage
          response_fields: [status, response]
        - path: /v1/health
          methods: [POST]
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
        - name: Finding
          fields_used: [rule_id, severity, element, message]
        - name: Observation
          fields_used: [target, measurements, findings]
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: EventEnvelope
          fields_used: [from, to, action, payload, trace_id]
        - name: HealthStatus
          fields_used: [status, details]
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
  # Work agent — no runtime agent dependencies. Dispatched by domain
  # controllers but does not depend on them being available at startup.
```

---

## Configuration

```yaml
config:
  analysis_timeout:
    type: int
    default: 30
    env: WL_A11Y_ANALYSIS_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Maximum time for a single file analysis

  max_files_per_task:
    type: int
    default: 50
    env: WL_A11Y_MAX_FILES
    min: 1
    max: 500
    description: Maximum files accepted in a single task

  alt_text_min_length:
    type: int
    default: 10
    env: WL_A11Y_ALT_MIN_LENGTH
    min: 1
    max: 50
    description: Minimum acceptable alt text length in characters

  alt_text_max_length:
    type: int
    default: 150
    env: WL_A11Y_ALT_MAX_LENGTH
    min: 50
    max: 500
    description: Maximum recommended alt text length in characters

  generic_alt_patterns:
    type: string
    default: "image,photo,banner,picture,icon,graphic,img,screenshot"
    env: WL_A11Y_GENERIC_PATTERNS
    description: Comma-separated list of generic alt text patterns to flag

  heading_skip_severity:
    type: string
    default: warning
    env: WL_A11Y_HEADING_SKIP_SEVERITY
    enum: [info, warning, critical]
    description: Severity level for heading hierarchy violations

  enable_color_contrast:
    type: bool
    default: true
    env: WL_A11Y_COLOR_CONTRAST
    description: Enable inline style color contrast checks
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  A11yFinding:
    description: A single accessibility issue detected during analysis
    fields:
      rule_id:
        type: string
        format: "a11y-{category}-{detail}"
        description: Unique rule identifier (e.g. a11y-alt-missing)
      severity:
        type: string
        enum: [critical, warning, info]
        description: Issue severity level
      element:
        type: string
        description: HTML element type (img, h1, label, etc.)
      file:
        type: string
        description: Relative path to the HTML file
      current:
        type: string
        optional: true
        description: Current value of the element attribute
      expected:
        type: string
        description: Expected value or condition
      message:
        type: string
        max: 512
        description: Human-readable description of the issue
      fixable:
        type: bool
        default: false
        description: Whether this issue can be auto-fixed
      line:
        type: int
        optional: true
        description: Line number in the source file

  A11yCategoryResult:
    description: Compliance status for a single accessibility category
    fields:
      status:
        type: string
        enum: [compliant, partial, non-compliant]
        description: Overall category compliance
      issues:
        type: int
        min: 0
        description: Number of issues found in this category

  A11yFileReport:
    description: Accessibility analysis results for a single file
    fields:
      path:
        type: string
        description: Relative file path
      score:
        type: int
        min: 0
        max: 100
        description: Accessibility compliance score
      categories:
        type: object
        description: >
          Map of category name to A11yCategoryResult.
          Categories: images, headings, language, landmarks, links, forms
      findings:
        type: array
        items: A11yFinding
        description: All findings for this file

  A11yObservation:
    description: Measurement data published for lifecycle tracking
    fields:
      target:
        type: string
        description: File path or URL analyzed
      measurements:
        type: object
        description: >
          Measurement fields: a11y_score (int), total_issues (int),
          critical_issues (int), categories_checked (int)

  AltTextReview:
    description: Result of reviewing a proposed alt text suggestion
    fields:
      file:
        type: string
        description: File containing the image
      src:
        type: string
        description: Image source path
      proposed_alt:
        type: string
        description: The proposed alt text to review
      approved:
        type: bool
        description: Whether the proposed text passes quality checks
      revision:
        type: string
        optional: true
        description: Suggested revision if not approved
      reason:
        type: string
        optional: true
        description: Explanation for rejection or revision
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
        validates: error response returned to domain controller
        side_effect: emit a11y.task.failed event
      - from: active
        to: degraded
        trigger: file_read_error
        validates: file system access consistently failing
      - from: degraded
        to: active
        trigger: file_read_recovered
        validates: file read succeeds on next attempt
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: SIGTERM, system.shutdown, or API signal received
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
  Validates:   All config values within declared min/max/enum constraints
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None (process never started)

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/a11y-checker/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-2 validated
  Validates:   HTTP 200, agent_id returned in response body
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (registration is idempotent)

Step 4 — Subscribe to Events
  Action:      Subscribe to: system.shutdown, system.blueprint.changed
  Pre-check:   Step 3 validated (registered with orchestrator)
  Validates:   Subscriptions acknowledged by message bus
  On Fail:     Deregister from orchestrator → EXIT with SUBSCRIPTION_FAILED
  Backout:     Unsubscribe all, deregister

Step 5 — Verify File Access
  Action:      Test file:read capability against workspace root
  Pre-check:   Steps 1-4 validated
  Validates:   Can list files in workspace directory
  On Fail:     Enter degraded state — log warning, continue
  Backout:     None (degraded is a valid operating mode)

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9711, capabilities: [file:read, agent:message]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown event, or API call
  Validates:   Signal is recognized
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests
  Validates:   No new tasks accepted after this point

Step 3 — Drain In-Flight
  Action:      Wait for current analysis to complete (up to config.analysis_timeout)
  Validates:   in_flight = 0
  On Timeout:  Return partial results to domain controller

Step 4 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges removal

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, tasks_completed, tasks_failed}
  agent_state → retired
  Exit process
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - file system accessible
      - no in-flight task timeout in last 5 minutes
    response:
      status: healthy
      details: {state, uptime, tasks_completed, last_task_at}

  degraded:
    conditions:
      - file system intermittently failing
      - last task timed out
    response:
      status: degraded
      details: {reason, last_error, retry_count}

  unhealthy:
    conditions:
      - file system unreachable
      - registration lost
    response:
      status: unhealthy
      details: {reason, last_error, since}
```

### Self-Update

When `system.blueprint.changed` is received where `blueprint_name = "a11y-checker"`:

```
1. Validate new blueprint — parse and verify against schema
2. Check for configuration changes — apply new defaults if within range
3. Reload validation rules if changed
4. Log: lifecycle.version_updated {from, to}
```

---

## Triggers

```yaml
triggers:
  - name: task_message
    type: message
    endpoint: POST /v1/message
    actions: [check_images, check_full, review_alt_text]
    description: >
      Receive analysis tasks from domain controllers.
      Each message contains an action name and payload.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "a11y-checker"
    description: Self-update if a11y-checker blueprint changed
```

---

## Actions

### check_images

Check images for alt text quality and ARIA compliance.

**Purpose:** Evaluate a set of image elements for alt text presence,
quality, and WCAG compliance.

**Input:** `{images: [{file: string, src: string, alt: string}]}`
— array of image elements with their current alt text values.

**Processing:**

```
1. Validate input:
   a. images array is non-empty
   b. Each image has file, src fields (alt may be empty string)
2. For each image:
   a. Check if alt text is present and non-empty
      → Missing: finding a11y-alt-missing, severity critical
   b. Check if alt text is descriptive (not in config.generic_alt_patterns)
      → Generic: finding a11y-alt-generic, severity warning
   c. Check if decorative images use alt="" (intentionally empty is OK)
   d. Check alt text length against config.alt_text_min_length / max_length
      → Too short or too long: finding a11y-alt-length, severity info
3. Compute measurements: total_images, images_missing_alt,
   images_generic_alt, images_compliant
4. Return findings and measurements
```

**Output:** `{findings: A11yFinding[], measurements: {total_images, images_missing_alt, images_generic_alt, images_compliant}}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: images array is empty or missing required fields
    retryable: false
  - code: ANALYSIS_TIMEOUT
    condition: Processing exceeds config.analysis_timeout
    retryable: true
```

**Side Effects:** None — pure analysis, no storage writes.

**Idempotency:** Fully idempotent. Same input always produces same output.

---

### check_full

Full accessibility audit of HTML files.

**Purpose:** Perform comprehensive WCAG 2.1 Level AA analysis across
all accessibility categories for the provided HTML files.

**Input:** `{html_files: string[]}` — array of relative file paths to analyze.

**Processing:**

```
1. Validate input:
   a. html_files array is non-empty
   b. Array length <= config.max_files_per_task
2. For each file:
   a. Read file content via file:read capability
   b. Parse HTML structure
   c. Check Images: alt text presence and quality (same rules as check_images)
   d. Check Headings: hierarchy must not skip levels (h1→h2→h3)
      → Skipped level: a11y-heading-skip, severity config.heading_skip_severity
      → Missing h1: a11y-heading-no-h1, severity critical
   e. Check Language: <html> must have lang attribute
      → Missing: a11y-lang-missing, severity critical
   f. Check Landmarks: page should have <main>, <nav>, <header>, <footer>
      → Missing <main>: a11y-landmark-missing, severity warning
   g. Check Links: anchor text must be descriptive
      → Generic text: a11y-link-generic, severity warning
   h. Check Forms: inputs must have associated <label> elements
      → Missing label: a11y-form-label-missing, severity critical
      → Missing aria-required: a11y-form-aria-required, severity warning
   i. Check Color Contrast (if config.enable_color_contrast):
      → Low contrast inline styles: a11y-contrast-low, severity warning
3. Score each category: compliant (0 issues), partial (warnings only),
   non-compliant (any critical)
4. Compute overall a11y_score per file:
   score = 100 - (critical × 15) - (warning × 5) - (info × 1)
   Clamped to [0, 100]
5. Build observations with measurements for lifecycle tracking
```

**Output:** `{files: A11yFileReport[], findings: A11yFinding[], observations: A11yObservation[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty file list or exceeds max_files_per_task
    retryable: false
  - code: FILE_NOT_FOUND
    condition: Referenced file does not exist in workspace
    retryable: false
  - code: FILE_READ_ERROR
    condition: File exists but cannot be read
    retryable: true
  - code: ANALYSIS_TIMEOUT
    condition: Total analysis exceeds config.analysis_timeout
    retryable: true
  - code: PARSE_ERROR
    condition: HTML cannot be parsed (malformed beyond recovery)
    retryable: false
```

**Side Effects:** None — pure analysis. Observations returned to domain
controller for lifecycle tracking.

**Idempotency:** Fully idempotent. Same files produce same findings.

---

### review_alt_text

Review proposed alt text suggestions from another agent.

**Purpose:** Validate alt text quality before it is applied to images.
Other agents (e.g., seo-analyzer) may generate alt text suggestions
and request accessibility review.

**Input:** `{suggestions: [{file: string, src: string, proposed_alt: string}]}`

**Processing:**

```
1. Validate input:
   a. suggestions array is non-empty
   b. Each suggestion has file, src, proposed_alt fields
2. For each suggestion:
   a. Check proposed alt text is not empty
   b. Check it is not in config.generic_alt_patterns
   c. Check length is within config.alt_text_min_length / max_length
   d. Check it describes purpose, not just appearance
      (heuristic: reject if it starts with "a photo of", "an image of")
3. If approved: return {approved: true}
4. If rejected: return {approved: false, revision, reason}
```

**Output:** `{reviewed: AltTextReview[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: suggestions array is empty or missing required fields
    retryable: false
```

**Side Effects:** None — pure validation.

**Idempotency:** Fully idempotent. Same suggestions produce same reviews.

---

## Execute Workflow

The a11y-checker processes tasks on demand — there is no tick loop.
Each task follows this pipeline:

```
Phase 1 — Receive Task
  Input:       AgentMessage from domain controller
  Validation:  action is one of [check_images, check_full, review_alt_text]
               payload matches expected schema for the action
               trace_id is present for correlation
  Result:      Validated task ready for dispatch to action handler

Phase 2 — Execute Action
  Action:      Route to the appropriate action handler
  Tracking:    Set agent_state → executing
               Start timer for config.analysis_timeout
  Result:      Action handler returns output or error

Phase 3 — Build Response
  Action:      Wrap action output in TaskResult envelope
               Include: task_id, agent_name, status, summary, timestamp
  Metrics:     Emit wl_a11y_task_duration_seconds histogram
               Emit wl_a11y_findings_total counter (by severity)
  Result:      Complete TaskResult ready for return

Phase 4 — Return Result
  Action:      Send TaskResult back to domain controller
               Set agent_state → active
  On Error:    If domain controller unreachable, log and discard
               (work agent does not retry delivery)
  Result:      Task complete
```

---

## Collaboration

```yaml
events_published:
  - topic: a11y.analysis.completed
    payload: {task_id, file_count, total_findings, critical_count, score_avg}
    when: check_full action completes successfully

  - topic: a11y.findings.critical
    payload: {task_id, file, findings}
    when: Critical accessibility issues found during analysis

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "a11y-checker"
    action: Self-update procedure

direct_messages:
  - target: variable (dispatching domain controller)
    action: TaskResult response
    when: Task analysis completes
    reason: >
      Domain controller dispatched the task and expects a synchronous
      response with findings and observations.
```

---

## Manual Overrides

```yaml
override_policy: full-auto

override_levels:
  full-auto:     All analysis is autonomous — no operator intervention needed
  supervised:    Operator can adjust thresholds and enable/disable rules
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: color_contrast_checking
    default: enabled
    override: Set WL_A11Y_COLOR_CONTRAST=false
    audit: logged

  - behavior: heading_skip_severity
    default: warning
    override: Set WL_A11Y_HEADING_SKIP_SEVERITY to info or critical
    audit: logged

  - behavior: generic_alt_patterns
    default: built-in list
    override: Set WL_A11Y_GENERIC_PATTERNS to custom comma-separated list
    audit: logged

manual_actions:
  - action: run_check
    description: Manually trigger a check_full analysis via CLI
    allowed: operator

  - action: update_rules
    description: Reload validation rules from updated blueprint
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Operator identity from auth token
  why: Optional — work agent overrides are typically configuration changes
  storage: Appended to system audit log
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT write to any files — read-only analysis only
    - MUST NOT access files outside the workspace directory
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT modify HTML content (analysis only, no auto-fix)
    - MUST NOT make network requests (file-based analysis only)
    - MUST NOT cache findings between tasks (stateless)

  resource_limits:
    memory: 128 MB (process limit)
    max_files_per_task: config.max_files_per_task (default 50)
    max_file_size: 5 MB per file (skip larger files with warning)
    analysis_timeout: config.analysis_timeout per task
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: Action payload missing required fields or invalid format
    - code: FILE_NOT_FOUND
      description: Referenced HTML file does not exist in workspace
    - code: PARSE_ERROR
      description: HTML is malformed beyond recovery — cannot extract structure
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: FILE_READ_ERROR
      description: File exists but read failed (permissions, I/O error)
      fallback: Skip file, include in partial results with error note
    - code: ANALYSIS_TIMEOUT
      description: Analysis exceeded config.analysis_timeout
      fallback: Return partial results for files completed so far
    - code: REGISTRATION_FAILED
      description: Could not register with orchestrator
      fallback: Retry 3x with exponential backoff, then exit
```

---

## Observability

```yaml
custom_log_types:
  - log_type: a11y.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, file_count, trace_id}

  - log_type: a11y.task.completed
    level: info
    when: Analysis completed successfully
    fields: {task_id, file_count, findings_total, duration_ms}

  - log_type: a11y.task.failed
    level: warn
    when: Analysis failed or partially failed
    fields: {task_id, error_code, files_completed, files_failed}

  - log_type: a11y.file.skipped
    level: warn
    when: File skipped due to read error or size limit
    fields: {file, reason}

  - log_type: a11y.findings.critical
    level: warn
    when: Critical accessibility issues found
    fields: {task_id, file, critical_count}

metrics:
  - name: wl_a11y_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks processed by action and outcome

  - name: wl_a11y_task_duration_seconds
    type: histogram
    labels: [action]
    description: Task processing duration

  - name: wl_a11y_findings_total
    type: counter
    labels: [severity, category]
    description: Findings by severity and category

  - name: wl_a11y_files_analyzed_total
    type: counter
    description: Total files analyzed across all tasks

  - name: wl_a11y_score_distribution
    type: histogram
    description: Distribution of accessibility scores (0-100)

alerts:
  - condition: Error rate > 20% of tasks in 10-minute window
    severity: warn
    routing: alerting agent

  - condition: All tasks failing (100% error rate for 5+ minutes)
    severity: critical
    routing: alerting agent

  - condition: Average task duration > 80% of config.analysis_timeout
    severity: warn
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: file:read
      resources: ["**/*.html"]
      description: Read HTML files in the workspace for analysis

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTML file content
      classification: low
      handling: Read in memory, never persisted, discarded after analysis

    - data: Analysis findings
      classification: low
      handling: Returned to domain controller, not stored locally

    - data: Alt text content
      classification: low
      handling: Analyzed for quality, not stored

  access_control:
    - caller: Domain controller (seo, content)
      actions: [check_images, check_full, review_alt_text]

    - caller: Operator (auth token with operator role)
      actions: [check_images, check_full, review_alt_text]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token from registered agent or operator
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Check images with mixed alt text quality
    action: check_images
    input:
      images:
        - {file: "index.html", src: "/logo.png", alt: ""}
        - {file: "index.html", src: "/hero.jpg", alt: "hero image"}
        - {file: "index.html", src: "/team.jpg", alt: "Development team collaborating around a whiteboard"}
    expected:
      findings_count: 2
      findings:
        - {rule_id: "a11y-alt-missing", severity: "critical"}
        - {rule_id: "a11y-alt-generic", severity: "warning"}
      measurements:
        total_images: 3
        images_missing_alt: 1
        images_generic_alt: 1
        images_compliant: 1
    validates:
      - Missing alt text detected as critical
      - Generic alt text detected as warning
      - Compliant images not flagged

  - name: Full audit on compliant page
    action: check_full
    input:
      html_files: ["compliant.html"]
    expected:
      files:
        - path: "compliant.html"
          score: 100
          categories:
            images: {status: "compliant"}
            headings: {status: "compliant"}
            language: {status: "compliant"}
    validates:
      - Compliant page scores 100
      - All categories report compliant status

  - name: Review valid alt text suggestion
    action: review_alt_text
    input:
      suggestions:
        - {file: "index.html", src: "/logo.png", proposed_alt: "Weblisk company logo"}
    expected:
      reviewed:
        - {file: "index.html", src: "/logo.png", approved: true}
    validates:
      - Descriptive alt text approved without revision
```

### Error Cases

```yaml
  - name: Empty file list rejected
    action: check_full
    input: {html_files: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected with permanent error]

  - name: Non-existent file
    action: check_full
    input: {html_files: ["nonexistent.html"]}
    expected_error: FILE_NOT_FOUND
    validates: [Missing files produce permanent error]

  - name: Malformed HTML
    action: check_full
    input: {html_files: ["malformed.html"]}
    expected_error: PARSE_ERROR
    validates: [Unparseable HTML produces permanent error]
```

### Edge Cases

```yaml
  - name: Decorative image with intentionally empty alt
    action: check_images
    input:
      images:
        - {file: "index.html", src: "/divider.png", alt: ""}
    condition: Image is decorative (role="presentation" or aria-hidden="true")
    expected: No finding — intentionally empty alt is valid for decorative images
    validates: [Decorative images not flagged as missing alt text]

  - name: File exceeds max size limit
    action: check_full
    input: {html_files: ["huge-page.html"]}
    condition: File is > 5 MB
    expected: File skipped with warning, partial results returned
    validates: [Resource limits enforced, partial results supported]

  - name: Task at max_files_per_task boundary
    action: check_full
    input: {html_files: ["file1.html", ..., "file50.html"]}
    condition: Exactly config.max_files_per_task files
    expected: All files analyzed successfully
    validates: [Boundary condition at max limit accepted]

  - name: Concurrent task while already executing
    trigger: task_message
    condition: Agent already executing a task
    expected: Second task queued or rejected with 503
    validates: [Agent handles concurrent dispatch safely]
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
    reason: >
      Work agents are stateless — any instance can handle any task.
      The message bus routes to the least-loaded healthy instance.

  intra_agent:
    coordination: shared-nothing
    state_sharing:
      mechanism: none
      reason: >
        Stateless agent — no shared state between instances.
        Each task is self-contained with all inputs provided
        in the task payload.

  event_handling:
    consumer_group: a11y-checker
    delivery: one-per-group
    description: >
      Each task message delivered to exactly one instance.
      No deduplication needed — tasks are idempotent.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    shadow_events_required: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "a11y-checker@vN+1"
      after_cutover: "a11y-checker"
```

---

## Implementation Notes

- **HTML Parsing**: Use a tolerant HTML parser that handles malformed
  markup. Do not reject files with minor syntax issues — extract what
  is possible and note parse warnings in findings.
- **Alt Text Heuristics**: The generic alt text check uses substring
  matching against `config.generic_alt_patterns`. This catches common
  patterns but may produce false positives for legitimate descriptions
  containing those words in context (e.g., "photo gallery navigation").
  Severity is `warning`, not `critical`, for this reason.
- **Heading Hierarchy**: Check heading order in document order, not DOM
  nesting. A page with `h1 → h3` (missing h2) is flagged regardless
  of whether they are in the same section.
- **Color Contrast**: The inline style check is a best-effort heuristic.
  It parses `color` and `background-color` from `style` attributes
  and computes WCAG contrast ratio. It cannot detect styles from
  external CSS files — that requires browser rendering.
- **Scoring Formula**: `score = 100 - (critical × 15) - (warning × 5) - (info × 1)`,
  clamped to [0, 100]. This weights critical issues heavily while
  still reflecting the cumulative impact of warnings.
- **Stateless Design**: The agent holds no state between tasks. Each
  task receives all required file paths and data in the payload.
  This simplifies scaling and eliminates coordination overhead.

### Validation Rules Reference

| Category | Rule | Severity |
|----------|------|----------|
| Images | All `<img>` must have alt attribute | critical |
| Images | Alt text must not be generic ("image", "photo", "banner") | warning |
| Images | Alt text should be 10-150 characters | info |
| Headings | Page must have exactly one `<h1>` | critical |
| Headings | Heading levels must not skip (h1→h3 without h2) | warning |
| Language | `<html>` must have `lang` attribute | critical |
| Landmarks | Page should have `<main>` element | warning |
| Links | Link text must not be "click here" or "read more" | warning |
| Links | Links must be distinguishable (not just color) | warning |
| Forms | All `<input>` must have associated `<label>` | critical |
| Forms | Required fields must have `aria-required="true"` | warning |

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: seo, port: 9711
- [ ] Checks all images for alt text presence — a11y-alt-missing finding
- [ ] Identifies generic alt text values from config.generic_alt_patterns
- [ ] Validates heading hierarchy — flags skipped levels
- [ ] Checks for lang attribute on `<html>` element
- [ ] Identifies missing landmark elements (`<main>`, `<nav>`, etc.)
- [ ] Validates form label associations — `<input>` with `<label>`
- [ ] Scores each file by accessibility compliance (0-100 scale)
- [ ] Returns structured findings with severity (critical/warning/info)
- [ ] review_alt_text action validates alt text quality and returns approval/revision
- [ ] Returns observations with measurements for lifecycle tracking
- [ ] Dependency contracts declare version ranges and bindings
- [ ] on_change rules defined for all dependencies
- [ ] State machine covers all transitions including degraded and retiring
- [ ] Startup sequence has pre-check, validates, on-fail for each step
- [ ] Shutdown drains in-flight tasks before deregistering
- [ ] Health endpoint reports accurate status per health criteria
- [ ] All errors classified as permanent or transient with correct codes
- [ ] Metrics emitted for tasks, findings, duration, and score distribution
- [ ] Security permissions limited to file:read and agent:message
- [ ] Constraints enforce read-only analysis — no file writes, no network calls
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model, any instance handles any task
