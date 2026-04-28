<!-- blueprint
type: agent
kind: work
name: seo-analyzer
version: 1.1.0
port: 9710
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
extends: [patterns/observability, patterns/scope, patterns/policy, patterns/security]
depends_on: []
platform: any
tier: free
domain: seo
-->

# SEO Analyzer Agent

Work agent that performs the technical SEO analysis. Dispatched by the
SEO domain controller — never invoked directly by the orchestrator or
external clients. Scans HTML files, extracts metadata, analyzes quality
via LLM, validates findings, and proposes changes.

## Overview

The seo-analyzer agent reads HTML files, extracts SEO-relevant metadata
(title, description, Open Graph, headings, images), validates against
rule-based constraints, and optionally uses an LLM to generate
context-aware improvement recommendations. It produces structured
findings, observations with measurements, and concrete proposed changes
with diffs.

The agent supports four actions: `scan_html` (extraction + rule
validation), `analyze_metadata` (LLM-powered recommendations),
`generate_report` (unified report with proposed changes), and
`review_seo` (quick non-LLM review). These are chained by the SEO
domain controller during a full analysis workflow.

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
  analysis_timeout:
    type: int
    default: 60
    env: WL_SEO_ANALYSIS_TIMEOUT
    min: 10
    max: 300
    unit: seconds
    description: Maximum time for a single analysis task

  max_files_per_task:
    type: int
    default: 50
    env: WL_SEO_MAX_FILES
    min: 1
    max: 200
    description: Maximum HTML files accepted in a single task

  title_min_length:
    type: int
    default: 30
    env: WL_SEO_TITLE_MIN
    description: Minimum optimal title length (characters)

  title_max_length:
    type: int
    default: 60
    env: WL_SEO_TITLE_MAX
    description: Maximum optimal title length (characters)

  title_reject_min:
    type: int
    default: 10
    env: WL_SEO_TITLE_REJECT_MIN
    description: Titles shorter than this are rejected

  title_reject_max:
    type: int
    default: 80
    env: WL_SEO_TITLE_REJECT_MAX
    description: Titles longer than this are rejected

  description_min_length:
    type: int
    default: 120
    env: WL_SEO_DESC_MIN
    description: Minimum optimal description length (characters)

  description_max_length:
    type: int
    default: 160
    env: WL_SEO_DESC_MAX
    description: Maximum optimal description length (characters)

  description_reject_min:
    type: int
    default: 50
    env: WL_SEO_DESC_REJECT_MIN
    description: Descriptions shorter than this are rejected

  description_reject_max:
    type: int
    default: 200
    env: WL_SEO_DESC_REJECT_MAX
    description: Descriptions longer than this are rejected

  llm_max_tokens:
    type: int
    default: 2048
    env: WL_SEO_LLM_MAX_TOKENS
    min: 256
    max: 8192
    description: Maximum tokens for LLM response

  llm_temperature:
    type: float
    default: 0.3
    env: WL_SEO_LLM_TEMPERATURE
    min: 0.0
    max: 1.0
    description: LLM temperature (lower = more deterministic)
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  FileMetadata:
    description: Extracted metadata from a single HTML file
    fields:
      path:
        type: string
        description: Relative file path
      title:
        type: string
        description: Content of <title> tag
      meta_description:
        type: string
        description: Content of meta description tag
      lang:
        type: string
        description: Value of lang attribute on <html>
      canonical:
        type: string
        description: Canonical URL from <link rel="canonical">
      og_title:
        type: string
        description: Open Graph title
      og_description:
        type: string
        description: Open Graph description
      og_image:
        type: string
        description: Open Graph image URL
      headings:
        type: array
        description: "Heading elements: {level: int, text: string}"
      images:
        type: array
        description: "Image elements: {src: string, alt: string}"

  FileMeasurements:
    description: Quantitative measurements for a file
    fields:
      title_length:
        type: int
        description: Character count of title
      description_length:
        type: int
        description: Character count of meta description
      h1_count:
        type: int
        description: Number of h1 elements
      heading_count:
        type: int
        description: Total heading elements
      image_count:
        type: int
        description: Total images
      images_missing_alt:
        type: int
        description: Images with empty or missing alt text

  SeoFinding:
    description: A rule-based SEO issue
    fields:
      rule_id:
        type: string
        format: "seo-{element}-{detail}"
        description: Unique rule identifier
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Issue severity
      element:
        type: string
        description: HTML element or attribute affected
      current:
        type: string
        description: Current value (or empty)
      expected:
        type: string
        description: Expected constraint
      message:
        type: string
        max: 512
        description: Human-readable description
      fixable:
        type: bool
        description: Whether the agent can auto-fix this issue
      fix:
        type: string
        optional: true
        description: Suggested fix value (if fixable)

  SeoRecommendation:
    description: LLM-generated improvement recommendation
    fields:
      target:
        type: string
        description: File path
      element:
        type: string
        description: HTML element to change
      current:
        type: string
        description: Current value
      proposed:
        type: string
        description: Recommended new value
      reason:
        type: string
        description: Explanation from LLM
      priority:
        type: string
        enum: [critical, high, medium, low]
        description: Priority level
      impact:
        type: float
        min: 0.0
        max: 1.0
        description: Estimated impact score

  ProposedChange:
    description: A concrete HTML modification with diff
    fields:
      path:
        type: string
        description: File path
      action:
        type: string
        enum: [modify, insert]
        description: Whether modifying existing or inserting new
      original:
        type: string
        description: Original HTML fragment
      modified:
        type: string
        description: Modified HTML fragment
      diffs:
        type: array
        description: >
          Per-element changes: {element, before, after, reason}
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
        side_effect: emit seo.task.failed event
      - from: active
        to: degraded
        trigger: llm_unavailable
        validates: LLM service consistently failing
      - from: degraded
        to: active
        trigger: llm_recovered
        validates: LLM request succeeds
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/seo-analyzer/
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

Step 5 — Verify LLM Access
  Action:      Send test prompt to configured LLM provider
  Pre-check:   Steps 1-4 validated
  Validates:   LLM responds within timeout
  On Fail:     Enter degraded state — analyze_metadata disabled, log warning
  Backout:     None

Final:
  agent_state → active (or degraded if LLM unavailable)
  Log: lifecycle.ready {port: 9710, capabilities: [file:read, llm:chat, agent:message]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests

Step 3 — Drain In-Flight
  Action:      Wait for current analysis to complete (up to config.analysis_timeout)
  On Timeout:  Return partial results for completed files

Step 4 — Deregister
  Action:      DELETE /v1/register

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, files_analyzed}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - LLM service accessible
    response:
      status: healthy
      details: {state, uptime, files_analyzed, llm_status}

  degraded:
    conditions:
      - LLM service unavailable (analyze_metadata disabled)
    response:
      status: degraded
      details: {reason, disabled_actions, last_error}

  unhealthy:
    conditions:
      - registration lost
      - file system inaccessible
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
    actions: [scan_html, analyze_metadata, generate_report, review_seo]
    description: >
      Receive SEO analysis tasks from the SEO domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "seo-analyzer"
    description: Self-update if seo-analyzer blueprint changed
```

---

## Actions

### scan_html

Scan HTML files and extract SEO-relevant metadata.

**Purpose:** Read HTML files, extract metadata using regex patterns,
measure quantitative signals, and validate against rule-based
constraints.

**Input:** `{html_files: string[]}` — relative paths to HTML files.

**Processing:**

```
1. Validate input:
   a. html_files non-empty
   b. Array length <= config.max_files_per_task
2. For each file:
   a. Read file via file:read capability
   b. Extract metadata using Extraction Rules (see Implementation Notes):
      title, meta_description, lang, canonical, og_title,
      og_description, og_image, headings, images
   c. Record measurements:
      title_length, description_length, h1_count, heading_count,
      image_count, images_missing_alt
   d. Validate against Validation Rules:
      - Title: 30-60 chars optimal, reject < 10 or > 80
      - Description: 120-160 chars optimal, reject < 50 or > 200
      - Lang: must be present on <html>
      - H1: exactly one per page
      - Heading hierarchy: must not skip levels
      - Images: all must have non-empty alt text
      - og:title, og:description, canonical: should be present
   e. Build SeoFinding per validation failure
3. Return {files: [{path, metadata, measurements}], findings: SeoFinding[]}
```

**Output:** `{files: [{path: string, metadata: FileMetadata, measurements: FileMeasurements}], findings: SeoFinding[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty file list or exceeds limit
    retryable: false
  - code: FILE_NOT_FOUND
    condition: HTML file does not exist
    retryable: false
  - code: FILE_READ_ERROR
    condition: Cannot read file (permissions, encoding)
    retryable: false
  - code: PARSE_ERROR
    condition: HTML is severely malformed (cannot extract any metadata)
    retryable: false
```

**Side Effects:** Reads HTML files via file:read. No writes.

**Idempotency:** Deterministic for the same input files.

---

### analyze_metadata

Analyze extracted metadata using LLM.

**Purpose:** Send extracted metadata and entity context to an LLM
for context-aware improvement recommendations.

**Input:** `{metadata: FileMetadata[], entity: {name, industry, keywords, tone}}`

**Processing:**

```
1. Build LLM prompt with entity context and metadata
   (see LLM System Prompt in Implementation Notes)
2. Send to configured LLM provider (config.llm_max_tokens, config.llm_temperature)
3. Parse LLM response as JSON array of suggestions
4. Validate each suggestion:
   a. Reject if file, element, or suggested value is empty
   b. Reject titles outside config.title_reject_min – config.title_reject_max
   c. Reject descriptions outside config.description_reject_min – config.description_reject_max
   d. Reject if current == suggested (no change)
5. Convert validated suggestions to SeoRecommendation entries
6. Return {recommendations: SeoRecommendation[], observations: [{target, measurements, findings}]}
```

**Output:** `{recommendations: SeoRecommendation[], observations: [{target: string, measurements: FileMeasurements, findings: SeoFinding[]}]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty metadata array or missing entity context
    retryable: false
  - code: LLM_UNAVAILABLE
    condition: LLM service unreachable
    retryable: true
  - code: LLM_PARSE_ERROR
    condition: LLM response is not valid JSON
    retryable: true
  - code: LLM_TIMEOUT
    condition: LLM request exceeds timeout
    retryable: true
```

**Side Effects:** Sends metadata (not raw HTML) to LLM provider.
No file writes.

**Idempotency:** LLM responses may vary between calls.

---

### generate_report

Produce a unified SEO report from analysis and accessibility results.

**Purpose:** Merge scan findings, LLM recommendations, and optional
accessibility results into a single report with proposed HTML changes.

**Input:** `{analysis: object, a11y: object}` — output from
analyze_metadata and (optionally) a11y-checker results.

**Processing:**

```
1. Merge findings from analysis and a11y results
2. Calculate overall SEO score
3. Build proposed changes with HTML diffs per Modification Rules
   (see Implementation Notes)
4. Return {score, summary, recommendations, proposed_changes}
```

**Output:** `{score: int, summary: string, recommendations: SeoRecommendation[], proposed_changes: ProposedChange[]}`

**Errors:** `INVALID_INPUT` (permanent).

**Side Effects:** None. Pure computation on already-collected data.

**Idempotency:** Deterministic for the same input.

---

### review_seo

Quick SEO review of raw HTML content without LLM.

**Purpose:** Provide a fast, rule-based SEO review without requiring
LLM access. Used by other agents that need a quick assessment.

**Input:** `{content: string}` — raw HTML string.

**Processing:**

```
1. Extract metadata from HTML string (same rules as scan_html)
2. Validate against rule-based constraints
3. Return metadata and findings (no LLM, no recommendations)
```

**Output:** `{metadata: FileMetadata, findings: SeoFinding[]}`

**Errors:** `INVALID_INPUT` (permanent), `PARSE_ERROR` (permanent).

**Side Effects:** None. Operates on provided string.

**Idempotency:** Deterministic.

---

## Execute Workflow

```
1. RECEIVE task from SEO domain controller
   Input: {action, payload}

2. DISPATCH to appropriate action handler

3. FULL SEO AUDIT WORKFLOW (when domain controller chains actions):
   Phase 1: scan_html({html_files: [...]})
            → {files, findings}

   Phase 2: analyze_metadata({
              metadata: phase1.files.map(f => f.metadata),
              entity: {name, industry, keywords, tone}
            })
            → {recommendations, observations}

   Phase 3: generate_report({
              analysis: phase2,
              a11y: (optional a11y-checker results)
            })
            → {score, summary, recommendations, proposed_changes}

4. RETURN result to SEO domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: seo.scan.completed
    payload: {task_id, file_count, finding_count}
    when: scan_html action completes

  - topic: seo.analysis.completed
    payload: {task_id, recommendation_count}
    when: analyze_metadata action completes

  - topic: seo.report.ready
    payload: {task_id, score, summary, change_count}
    when: generate_report action completes

  - topic: seo.finding.critical
    payload: {task_id, rule_id, file, element, message}
    when: Critical SEO finding detected

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "seo-analyzer"
    action: Self-update procedure

direct_messages:
  - target: variable (dispatching domain controller)
    action: TaskResult response
    when: Task completes
    reason: Domain controller expects synchronous response.
```

---

## Manual Overrides

```yaml
override_policy: full-auto

override_levels:
  full-auto:     All analysis is autonomous
  supervised:    Operator can adjust LLM parameters and validation thresholds
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: title_length_constraints
    default: optimal 30-60, reject < 10 or > 80
    override: Set WL_SEO_TITLE_MIN / WL_SEO_TITLE_MAX / WL_SEO_TITLE_REJECT_*
    audit: logged

  - behavior: description_length_constraints
    default: optimal 120-160, reject < 50 or > 200
    override: Set WL_SEO_DESC_MIN / WL_SEO_DESC_MAX / WL_SEO_DESC_REJECT_*
    audit: logged

  - behavior: llm_parameters
    default: temperature 0.3, max_tokens 2048
    override: Set WL_SEO_LLM_TEMPERATURE / WL_SEO_LLM_MAX_TOKENS
    audit: logged

manual_actions:
  - action: run_scan
    description: Manually trigger an SEO scan via CLI
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
    - MUST NOT write to the file system (reads only — changes are proposed, not applied)
    - MUST NOT send raw HTML content to the LLM (metadata only)
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT modify HTML files directly (proposed changes are returned to controller)
    - MUST NOT make outbound HTTP requests (file-based analysis only)
    - MUST NOT send user-identifiable content to external services

  resource_limits:
    memory: 256 MB (process limit)
    max_files_per_task: config.max_files_per_task (default 50)
    analysis_timeout: config.analysis_timeout per task
    llm_max_tokens: config.llm_max_tokens per request
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: INVALID_INPUT
      description: Empty file list, exceeds limit, or missing required fields
    - code: FILE_NOT_FOUND
      description: HTML file does not exist at specified path
    - code: FILE_READ_ERROR
      description: Cannot read file due to permissions or encoding
    - code: PARSE_ERROR
      description: HTML is severely malformed (no recoverable metadata)
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: LLM_UNAVAILABLE
      description: LLM service unreachable
      fallback: Enter degraded state; analyze_metadata disabled
    - code: LLM_PARSE_ERROR
      description: LLM response is not valid JSON
      fallback: Retry once with stricter prompt; fall back to rule-based only
    - code: LLM_TIMEOUT
      description: LLM request exceeds timeout
      fallback: Retry once; fall back to rule-based only
    - code: REGISTRATION_FAILED
      description: Could not register with orchestrator
      fallback: Retry 3x with exponential backoff, then exit
```

---

## Observability

```yaml
custom_log_types:
  - log_type: seo.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, file_count, trace_id}

  - log_type: seo.scan.completed
    level: info
    when: scan_html completed
    fields: {task_id, file_count, finding_count, duration_ms}

  - log_type: seo.llm.request
    level: debug
    when: LLM request sent
    fields: {task_id, prompt_tokens, temperature}

  - log_type: seo.llm.response
    level: debug
    when: LLM response received
    fields: {task_id, response_tokens, suggestion_count, duration_ms}

  - log_type: seo.llm.validation_rejected
    level: info
    when: LLM suggestion rejected by validation
    fields: {task_id, element, reason}

  - log_type: seo.report.ready
    level: info
    when: generate_report completed
    fields: {task_id, score, recommendation_count, change_count}

metrics:
  - name: wl_seo_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks by action and outcome

  - name: wl_seo_findings_total
    type: counter
    labels: [rule_id, severity]
    description: SEO findings by rule and severity

  - name: wl_seo_llm_requests_total
    type: counter
    labels: [status]
    description: LLM requests by outcome

  - name: wl_seo_llm_duration_seconds
    type: histogram
    description: LLM request latency

  - name: wl_seo_llm_suggestions_rejected_total
    type: counter
    labels: [reason]
    description: LLM suggestions rejected by validation

  - name: wl_seo_score
    type: gauge
    description: Most recent SEO report score

  - name: wl_seo_scan_duration_seconds
    type: histogram
    labels: [action]
    description: Scan duration by action

alerts:
  - condition: LLM unavailable for > 10 minutes
    severity: warn
    routing: alerting agent

  - condition: > 50% of LLM suggestions rejected by validation
    severity: warn
    routing: alerting agent

  - condition: SEO score < 30
    severity: high
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: file:read
      resources: ["**/*.html"]
      description: Read HTML files for metadata extraction

    - capability: llm:chat
      resources: ["*"]
      description: Send metadata to LLM for analysis recommendations

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTML file content
      classification: medium
      handling: >
        Read locally for metadata extraction. Raw HTML is
        NOT sent to the LLM — only extracted metadata
        (title, description, heading text, image alt text).

    - data: Entity context (name, keywords, industry)
      classification: low
      handling: Sent to LLM as context for recommendations

    - data: LLM suggestions
      classification: low
      handling: Validated locally, returned to domain controller

  access_control:
    - caller: Domain controller (seo)
      actions: [scan_html, analyze_metadata, generate_report, review_seo]

    - caller: Operator (auth token with operator role)
      actions: [scan_html, analyze_metadata, generate_report, review_seo]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Scan HTML files
    action: scan_html
    input:
      html_files: ["app/index.html", "app/about.html"]
    expected:
      files:
        - path: "app/index.html"
          metadata: {title: "Home Page | Example"}
          measurements: {title_length: 19}
      findings: []
    validates:
      - Metadata extracted from all files
      - Measurements recorded correctly
      - Well-formed files produce no findings

  - name: Analyze with LLM
    action: analyze_metadata
    input:
      metadata:
        - {path: "app/index.html", title: "Home", meta_description: ""}
      entity: {name: "Example Corp", industry: "technology", keywords: ["web"]}
    expected:
      recommendations:
        - target: "app/index.html"
          element: "title"
          proposed: "<non-empty, 30-60 chars>"
    validates:
      - LLM suggestions generated and validated
      - Short title flagged for improvement

  - name: Quick review without LLM
    action: review_seo
    input: {content: "<html lang='en'><head><title>Test</title></head><body><h1>Hello</h1></body></html>"}
    expected:
      metadata: {title: "Test", lang: "en", h1_count: 1}
      findings: [{rule_id: "seo-title-short"}]
    validates:
      - Rule-based review works without LLM
```

### Error Cases

```yaml
  - name: Empty file list
    action: scan_html
    input: {html_files: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: File not found
    action: scan_html
    input: {html_files: ["nonexistent.html"]}
    expected_error: FILE_NOT_FOUND
    validates: [Missing file produces clear error]

  - name: LLM unavailable
    action: analyze_metadata
    input:
      metadata: [{path: "app/index.html", title: "Home"}]
      entity: {name: "Test"}
    condition: LLM service unreachable
    expected_error: LLM_UNAVAILABLE
    validates: [LLM failure handled gracefully]
```

### Edge Cases

```yaml
  - name: Missing title tag
    action: scan_html
    input: {html_files: ["app/no-title.html"]}
    condition: File has no <title> tag
    expected:
      findings: [{rule_id: "seo-title-missing", severity: "critical"}]
    validates: [Missing title detected as critical]

  - name: Multiple h1 tags
    action: scan_html
    input: {html_files: ["app/two-h1s.html"]}
    condition: File has two <h1> elements
    expected:
      findings: [{rule_id: "seo-h1-multiple", severity: "high"}]
    validates: [Multiple h1 flagged]

  - name: LLM suggestion rejected by validation
    action: analyze_metadata
    input:
      metadata: [{path: "app/index.html", title: "Home"}]
      entity: {name: "Test"}
    condition: LLM suggests title with 5 characters
    expected:
      recommendations: "Does not include rejected suggestion"
    validates: [Validation filters out invalid LLM suggestions]

  - name: HTML with no SEO metadata at all
    action: scan_html
    input: {html_files: ["app/bare.html"]}
    condition: File contains only <html><body>Hello</body></html>
    expected:
      findings:
        - {rule_id: "seo-title-missing", severity: "critical"}
        - {rule_id: "seo-description-missing", severity: "critical"}
        - {rule_id: "seo-lang-missing", severity: "high"}
        - {rule_id: "seo-h1-missing", severity: "high"}
    validates: [All missing elements detected]
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
        Stateless agent. Each analysis task is self-contained
        with all file paths or metadata in the payload.

  event_handling:
    consumer_group: seo-analyzer
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "seo-analyzer@vN+1"
      after_cutover: "seo-analyzer"
```

---

## Implementation Notes

### Metadata Extraction Rules

Regex patterns (case-insensitive, dotall where needed):

| Element | Pattern |
|---------|---------|
| title | `<title[^>]*>(.*?)</title>` (strip inner HTML tags) |
| meta description | `<meta\s+name=["']description["']\s+content=["'](.*?)["']` |
| meta description (alt) | `<meta\s+content=["'](.*?)["']\s+name=["']description["']` |
| lang | `<html[^>]*\slang=["'](.*?)["']` |
| canonical | `<link[^>]*rel=["']canonical["'][^>]*href=["'](.*?)["']` |
| og:title | `<meta\s+property=["']og:title["']\s+content=["'](.*?)["']` |
| og:description | `<meta\s+property=["']og:description["']\s+content=["'](.*?)["']` |
| og:image | `<meta\s+property=["']og:image["']\s+content=["'](.*?)["']` |
| headings | `<(h[1-6])[^>]*>(.*?)</h[1-6]>` (level from tag, strip inner HTML) |
| images | `<img\s[^>]*>` then extract `src=["'](.*?)["']` and `alt=["'](.*?)["']` |

### Validation Rules

| Element | Constraint | Severity |
|---------|-----------|----------|
| title | 30–60 chars optimal, reject < 10 or > 80 | critical if missing, high if bad length |
| meta_description | 120–160 chars optimal, reject < 50 or > 200 | critical if missing, high if bad length |
| lang | must be present on `<html>` tag | high |
| h1 | exactly one per page | high if 0 or > 1 |
| heading hierarchy | must not skip levels (h1→h2→h3) | medium |
| images | all `<img>` must have non-empty alt | medium per image |
| og:title | should be present | low |
| og:description | should be present | low |
| canonical | should be present | medium |

### LLM System Prompt

```
You are an SEO optimization agent for a web project.
Analyze the provided HTML file metadata and suggest concrete improvements.

Rules:
- Page titles: 30-60 characters, include primary keywords, unique per page
- Meta descriptions: 120-160 characters, compelling, action-oriented, unique per page
- Every page MUST have exactly one <h1> tag
- Heading hierarchy must not skip levels (h1 → h2 → h3, never h1 → h3)
- All <img> tags must have descriptive, non-empty alt text
- Pages should declare lang attribute on <html>
- Canonical URLs should be present
- Open Graph tags (og:title, og:description) should be present for social sharing

Respond with a JSON array of suggestions. Each item:
{
  "file": "relative/path.html",
  "element": "title|meta_description|h1|heading_hierarchy|img_alt|lang|canonical|og_title|og_description|og_image",
  "current": "current value or empty string",
  "suggested": "the improved value",
  "reason": "brief explanation",
  "priority": "high|medium|low"
}

Only suggest changes that would GENUINELY improve SEO.
Do NOT suggest changes where the current value is already good.
Respond ONLY with the JSON array — no markdown fences, no explanation.
```

### HTML Modification Rules

How to apply each type of change:

| Element | Strategy |
|---------|----------|
| title | Replace `<title>...</title>` content, or insert before `</head>` |
| meta_description | Replace content attr in existing meta, or insert before `</head>` |
| og_title | Replace content attr in existing og:title, or insert before `</head>` |
| og_description | Replace content attr, or insert before `</head>` |
| lang | Replace lang attr on `<html>`, or add `lang="X"` to existing tag |
| canonical | Replace href in existing canonical link, or insert before `</head>` |

General rule: if the element exists, replace in-place. If absent, insert
new tag before `</head>` with 4-space indentation.

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: seo, port: 9710
- [ ] Scans HTML files and extracts all metadata fields
- [ ] Validates findings against all constraint rules
- [ ] Sends extracted metadata (not raw HTML) to LLM for analysis
- [ ] Parses LLM response and validates suggestions against length/quality rules
- [ ] Rejects LLM suggestions where current == suggested
- [ ] Returns structured Observations with measurements
- [ ] Returns structured Recommendations with priority and impact
- [ ] Generates ProposedChange entries with full diffs
- [ ] Handles review_seo action without LLM
- [ ] Respects entity context (keywords, tone) in LLM prompts
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded (LLM down), and retiring states
- [ ] Startup sequence verifies LLM access; degrades gracefully if unavailable
- [ ] Shutdown drains in-flight tasks before deregistering
- [ ] Health endpoint reports LLM status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for tasks, findings, LLM requests, and rejections
- [ ] Security permissions limited to file:read, llm:chat, agent:message
- [ ] Constraints: no file writes, no raw HTML sent to LLM
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
