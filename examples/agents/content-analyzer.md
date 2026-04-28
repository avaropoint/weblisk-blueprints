<!-- blueprint
type: agent
kind: work
name: content-analyzer
version: 1.1.0
port: 9720
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
extends: [patterns/observability, patterns/scope, patterns/policy, patterns/security]
depends_on: []
platform: any
tier: free
domain: content
-->

# Content Analyzer Agent

Work agent that performs content quality analysis. Dispatched by the
content domain controller — never invoked directly by the orchestrator
or external clients. Scans HTML and markdown files, measures
readability, validates heading structure, checks paragraph balance,
and identifies quality issues.

## Overview

The content-analyzer agent performs static content quality analysis on
HTML and markdown files. It computes Flesch-Kincaid readability scores,
validates heading structure, measures paragraph and section balance,
detects thin content, and identifies quality signals like link density
and empty elements. The agent receives file lists from the content
domain controller, analyzes each file independently, and returns
per-file scores, findings, and optional fix suggestions.

The agent is stateless — all inputs are provided in the task payload
and all results are returned to the dispatching domain controller.

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
    env: WL_CONTENT_ANALYSIS_TIMEOUT
    min: 5
    max: 300
    unit: seconds
    description: Maximum time for a single task

  max_files_per_task:
    type: int
    default: 50
    env: WL_CONTENT_MAX_FILES
    min: 1
    max: 500
    description: Maximum files accepted in a single task

  thin_content_threshold:
    type: int
    default: 300
    env: WL_CONTENT_THIN_THRESHOLD
    min: 50
    max: 1000
    unit: words
    description: Pages below this word count flagged as thin content

  max_paragraph_words:
    type: int
    default: 150
    env: WL_CONTENT_MAX_PARAGRAPH
    min: 50
    max: 500
    unit: words
    description: Paragraph word count threshold for splitting recommendation

  section_imbalance_ratio:
    type: float
    default: 3.0
    env: WL_CONTENT_IMBALANCE_RATIO
    min: 1.5
    max: 10.0
    description: Section length ratio threshold (longest/shortest) for flagging

  readability_target_min:
    type: int
    default: 60
    env: WL_CONTENT_READABILITY_MIN
    min: 0
    max: 100
    description: Minimum Flesch-Kincaid score for web content

  score_weight_readability:
    type: float
    default: 0.5
    env: WL_CONTENT_WEIGHT_READABILITY
    min: 0.0
    max: 1.0
    description: Weight of readability in overall content score

  score_weight_structure:
    type: float
    default: 0.3
    env: WL_CONTENT_WEIGHT_STRUCTURE
    min: 0.0
    max: 1.0
    description: Weight of structure in overall content score

  score_weight_quality:
    type: float
    default: 0.2
    env: WL_CONTENT_WEIGHT_QUALITY
    min: 0.0
    max: 1.0
    description: Weight of quality signals in overall content score
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  FileAnalysis:
    description: Complete analysis result for a single file
    fields:
      file:
        type: string
        description: Relative file path
      word_count:
        type: int
        min: 0
        description: Total word count in the document
      readability:
        type: object
        description: >
          Readability metrics: flesch_kincaid (float), grade_level (string),
          avg_sentence_length (float), avg_word_length (float),
          passive_voice_pct (float), complex_word_pct (float)
      structure:
        type: object
        description: >
          Structure metrics: h1_count (int), heading_hierarchy_valid (bool),
          heading_order (string[]), section_count (int),
          avg_section_length (int), max_paragraph_words (int), list_count (int)
      quality:
        type: object
        description: >
          Quality signals: internal_links (int), external_links (int),
          images (int), images_with_alt (int), empty_elements (int),
          duplicate_fingerprint (string|null)
      content_score:
        type: int
        min: 0
        max: 100
        description: Overall content quality score
      findings:
        type: array
        items: ContentFinding
        description: Issues detected in this file

  ContentFinding:
    description: A single content quality issue
    fields:
      rule_id:
        type: string
        format: "content-{category}-{detail}"
        description: Unique rule identifier
      severity:
        type: string
        enum: [critical, high, medium, low]
        description: Issue severity
      category:
        type: string
        enum: [readability, structure, quality]
        description: Finding category
      file:
        type: string
        description: File path where issue was found
      element:
        type: string
        optional: true
        description: Specific element involved (e.g., heading tag, paragraph)
      message:
        type: string
        max: 512
        description: Human-readable description
      suggested:
        type: string
        optional: true
        description: Suggested improvement

  ScoreBreakdown:
    description: Detailed score components for a single file
    fields:
      readability_score:
        type: int
        min: 0
        max: 100
        description: Normalized readability score
      structure_score:
        type: int
        min: 0
        max: 100
        description: Structure compliance score
      quality_score:
        type: int
        min: 0
        max: 100
        description: Quality signals score
      overall:
        type: int
        min: 0
        max: 100
        description: Weighted composite score

  Fix:
    description: A proposed structural fix for a content issue
    fields:
      type:
        type: string
        enum: [heading_reorder, paragraph_split, list_conversion, empty_removal]
        description: Fix type
      file:
        type: string
        description: Target file path
      element:
        type: string
        description: CSS selector or description of target element
      current:
        type: string
        description: Current element content
      proposed:
        type: string
        description: Proposed replacement content
      reason:
        type: string
        description: Explanation of why this fix improves quality
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
        side_effect: emit content.task.failed event
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
  Validates:   All config values within declared min/max constraints;
               score weights sum to 1.0
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/content-analyzer/
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

Step 5 — Verify File Access
  Action:      Test file:read capability against workspace root
  Pre-check:   Steps 1-4 validated
  Validates:   Can list files in workspace directory
  On Fail:     Enter degraded state — log warning, continue
  Backout:     None

Final:
  agent_state → active
  Log: lifecycle.ready {port: 9720, capabilities: [file:read, agent:message]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  Validates:   Signal recognized
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests
  Validates:   No new tasks accepted

Step 3 — Drain In-Flight
  Action:      Wait for current analysis to complete (up to config.analysis_timeout)
  Validates:   in_flight = 0
  On Timeout:  Return partial results to domain controller

Step 4 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges removal

Step 5 — Exit
  Log: lifecycle.stopped {uptime_seconds, tasks_completed}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions:
      - agent_state = active
      - file system accessible
      - no task timeouts in last 5 minutes
    response:
      status: healthy
      details: {state, uptime, tasks_completed, last_task_at}

  degraded:
    conditions:
      - file system intermittently failing
      - last task timed out
    response:
      status: degraded
      details: {reason, last_error}

  unhealthy:
    conditions:
      - file system unreachable
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
    actions: [analyze, apply_fix, score]
    description: >
      Receive content analysis tasks from the content domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "content-analyzer"
    description: Self-update if content-analyzer blueprint changed
```

---

## Actions

### analyze

Analyze content quality for a list of files.

**Purpose:** Perform comprehensive readability, structure, and quality
analysis on HTML or markdown files.

**Input:** `{files: string[]}` — array of relative file paths.

**Processing:**

```
1. Validate input:
   a. files array is non-empty
   b. Array length <= config.max_files_per_task
2. For each file:
   a. Read file content via file:read capability
   b. Extract text content (strip HTML tags for readability analysis)
   c. Parse document structure (heading hierarchy, sections, paragraphs)
   d. Compute readability metrics (Flesch-Kincaid, sentence/word length,
      passive voice, complex word ratio)
   e. Validate structure (heading hierarchy, h1 count, section balance,
      paragraph length, list opportunities)
   f. Analyze quality signals (word count, link density, image-to-text
      ratio, empty elements, duplicate fingerprinting)
   g. Compute per-file content_score using configured weights
   h. Build findings array with severity and category
3. Return FileAnalysis[] to domain controller
```

**Output:** `{results: FileAnalysis[]}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Empty file list or exceeds max_files_per_task
    retryable: false
  - code: FILE_NOT_FOUND
    condition: Referenced file does not exist
    retryable: false
  - code: FILE_READ_ERROR
    condition: File exists but cannot be read
    retryable: true
  - code: ANALYSIS_TIMEOUT
    condition: Total analysis exceeds config.analysis_timeout
    retryable: true
```

**Side Effects:** None — pure analysis.

**Idempotency:** Fully idempotent. Same files produce same results.

---

### apply_fix

Apply a structural fix to a content file.

**Purpose:** Apply a proposed structural change (heading reorder,
paragraph split, etc.) to improve content quality.

**Input:** `{file: string, fix: Fix}` — file path and fix to apply.

**Processing:**

```
1. Validate input:
   a. file exists and is readable
   b. fix.type is one of allowed enum values
   c. fix.element can be located in the file
   d. fix.current matches actual element content (guard against stale fix)
2. Apply the fix:
   a. heading_reorder: Change heading level tag
   b. paragraph_split: Insert paragraph break at optimal point
   c. list_conversion: Convert consecutive short sentences to list
   d. empty_removal: Remove empty elements
3. Verify fix applied correctly (re-parse and validate)
4. Return diff showing before/after
```

**Output:** `{success: bool, diff: string}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Fix type invalid or element not found
    retryable: false
  - code: STALE_FIX
    condition: fix.current does not match actual content
    retryable: false
  - code: FILE_WRITE_ERROR
    condition: Cannot write modified file
    retryable: true
```

**Side Effects:** Modifies the target file. Only structural changes
— never alters content text.

**Idempotency:** Not idempotent — applying the same fix twice may
produce different results. Guard via fix.current match.

---

### score

Score a single file without full analysis.

**Purpose:** Quick scoring of a single file, useful for progress
tracking after fixes are applied.

**Input:** `{file: string}` — relative file path.

**Processing:**

```
1. Read and parse the file
2. Compute readability, structure, and quality sub-scores
3. Compute overall content_score using configured weights
4. Return score and breakdown without detailed findings
```

**Output:** `{content_score: int, breakdown: ScoreBreakdown}`

**Errors:** `FILE_NOT_FOUND` (permanent), `FILE_READ_ERROR` (transient).

**Side Effects:** None — read-only.

**Idempotency:** Fully idempotent.

---

## Execute Workflow

```
1. RECEIVE task from content domain controller
   Input: {target_files: ["index.html", "about.html", ...]}

2. READ each file
   Extract text content (strip HTML tags for readability analysis)
   Parse document structure (heading hierarchy, sections, paragraphs)

3. ANALYZE readability per file:
   a. Flesch-Kincaid readability ease
   b. Average sentence length (words per sentence)
   c. Average word length (syllables per word)
   d. Passive voice percentage
   e. Complex word ratio (3+ syllables)

4. ANALYZE structure per file:
   a. Heading hierarchy — does h1 → h2 → h3 follow correct order?
   b. Heading count — is there exactly one h1?
   c. Section balance — are sections roughly similar length?
   d. Paragraph length — flag paragraphs > config.max_paragraph_words
   e. List usage — are there opportunities for lists in dense paragraphs?

5. ANALYZE quality signals:
   a. Word count (flag pages < config.thin_content_threshold as thin)
   b. Link density — internal/external ratio
   c. Image-to-text ratio
   d. Empty elements (empty paragraphs, empty headings)
   e. Duplicate content detection (via text fingerprinting)

6. SCORE each file:
   readability_score = normalize(flesch_kincaid, 0, 100)
   structure_score = deductions from hierarchy/balance violations
   overall = weighted(readability: config.score_weight_readability,
                      structure: config.score_weight_structure,
                      quality: config.score_weight_quality)

7. BUILD findings array:
   Each finding = {file, severity, category, element, message, suggested}

8. RETURN FileAnalysis[] to domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: content.analysis.completed
    payload: {task_id, file_count, avg_score, findings_total}
    when: analyze action completes successfully

  - topic: content.quality.low
    payload: {task_id, file, content_score, findings}
    when: File scores below 40 on content quality

  - topic: content.fix.applied
    payload: {task_id, file, fix_type, diff_size}
    when: apply_fix action completes successfully

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "content-analyzer"
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
  full-auto:     All analysis is autonomous
  supervised:    Operator can adjust thresholds and scoring weights
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: thin_content_threshold
    default: 300 words
    override: Set WL_CONTENT_THIN_THRESHOLD
    audit: logged

  - behavior: scoring_weights
    default: readability 0.5, structure 0.3, quality 0.2
    override: Set WL_CONTENT_WEIGHT_* environment variables
    audit: logged

  - behavior: paragraph_length_threshold
    default: 150 words
    override: Set WL_CONTENT_MAX_PARAGRAPH
    audit: logged

manual_actions:
  - action: run_analysis
    description: Manually trigger analysis via CLI
    allowed: operator

  - action: recalibrate_weights
    description: Adjust scoring weights without redeployment
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
    - MUST NOT access files outside the workspace directory
    - MUST NOT modify file content during analyze or score actions
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT alter content text (apply_fix only changes structure)
    - MUST NOT make network requests (file-based analysis only)
    - MUST NOT cache analysis results between tasks

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
      description: Referenced file does not exist in workspace
    - code: STALE_FIX
      description: Fix target content has changed since fix was proposed
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: FILE_READ_ERROR
      description: File exists but read failed (permissions, I/O error)
      fallback: Skip file, include in partial results with error note
    - code: FILE_WRITE_ERROR
      description: Cannot write modified file during apply_fix
      fallback: Return error, no partial write
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
  - log_type: content.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, file_count, trace_id}

  - log_type: content.task.completed
    level: info
    when: Analysis completed successfully
    fields: {task_id, file_count, avg_score, duration_ms}

  - log_type: content.task.failed
    level: warn
    when: Analysis failed
    fields: {task_id, error_code, files_completed, files_failed}

  - log_type: content.fix.applied
    level: info
    when: Structural fix applied to a file
    fields: {task_id, file, fix_type}

  - log_type: content.quality.low
    level: warn
    when: File scores below 40
    fields: {task_id, file, content_score}

metrics:
  - name: wl_content_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks processed by action and outcome

  - name: wl_content_task_duration_seconds
    type: histogram
    labels: [action]
    description: Task processing duration

  - name: wl_content_findings_total
    type: counter
    labels: [severity, category]
    description: Findings by severity and category

  - name: wl_content_score_distribution
    type: histogram
    description: Distribution of content scores (0-100)

  - name: wl_content_readability_distribution
    type: histogram
    description: Distribution of Flesch-Kincaid readability scores

alerts:
  - condition: Error rate > 20% of tasks in 10-minute window
    severity: warn
    routing: alerting agent

  - condition: All tasks failing for 5+ minutes
    severity: critical
    routing: alerting agent

  - condition: Average content score dropping below 40 across files
    severity: warn
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: file:read
      resources: ["**/*.html", "**/*.md"]
      description: Read HTML and markdown files for analysis

    - capability: file:write
      resources: ["**/*.html", "**/*.md"]
      description: Write structural fixes via apply_fix action only

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: File content
      classification: low
      handling: Read in memory, discarded after analysis

    - data: Analysis findings
      classification: low
      handling: Returned to domain controller, not stored locally

    - data: Applied diffs
      classification: low
      handling: Logged as fix metadata, full diff returned to controller

  access_control:
    - caller: Domain controller (content)
      actions: [analyze, apply_fix, score]

    - caller: Operator (auth token with operator role)
      actions: [analyze, apply_fix, score]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Analyze well-structured content
    action: analyze
    input:
      files: ["well-structured.html"]
    expected:
      results:
        - file: "well-structured.html"
          content_score: ">= 80"
          readability: {flesch_kincaid: ">= 60"}
          structure: {heading_hierarchy_valid: true}
    validates:
      - High-quality content scores above 80
      - Flesch-Kincaid computed correctly
      - Valid heading hierarchy detected

  - name: Score single file
    action: score
    input: {file: "about.html"}
    expected:
      content_score: ">= 0"
      breakdown: {readability_score: ">= 0", structure_score: ">= 0", quality_score: ">= 0"}
    validates:
      - Score action returns breakdown without full findings

  - name: Apply heading fix
    action: apply_fix
    input:
      file: "about.html"
      fix: {type: "heading_reorder", file: "about.html", element: "h3:nth-child(2)",
            current: "<h3>Our Mission</h3>", proposed: "<h2>Our Mission</h2>",
            reason: "h3 follows h1 — missing h2 level"}
    expected: {success: true, diff: "<non-empty>"}
    validates:
      - Structural fix applied correctly
      - Diff shows before/after
```

### Error Cases

```yaml
  - name: Empty file list
    action: analyze
    input: {files: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: Non-existent file
    action: analyze
    input: {files: ["missing.html"]}
    expected_error: FILE_NOT_FOUND
    validates: [Missing files produce permanent error]

  - name: Stale fix rejected
    action: apply_fix
    input:
      file: "about.html"
      fix: {type: "heading_reorder", current: "<h3>Old Content</h3>", proposed: "<h2>Old Content</h2>"}
    expected_error: STALE_FIX
    validates: [Fix rejected when target content has changed]
```

### Edge Cases

```yaml
  - name: Thin content detection
    action: analyze
    input: {files: ["thin-page.html"]}
    condition: File has < 300 words
    expected:
      findings: [{rule_id: "content-quality-thin", severity: "medium"}]
    validates: [Thin content threshold enforced]

  - name: Maximum files per task
    action: analyze
    input: {files: ["f1.html", ..., "f50.html"]}
    condition: Exactly config.max_files_per_task files
    expected: All files analyzed
    validates: [Boundary at max limit accepted]

  - name: File with no headings
    action: analyze
    input: {files: ["no-headings.html"]}
    expected:
      findings:
        - {rule_id: "content-structure-no-h1", severity: "critical"}
    validates: [Missing h1 detected as critical]

  - name: Markdown file analysis
    action: analyze
    input: {files: ["readme.md"]}
    expected: Analysis includes readability metrics for markdown content
    validates: [Markdown files processed alongside HTML]
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
      Stateless work agent — any instance can handle any task.

  intra_agent:
    coordination: shared-nothing
    state_sharing:
      mechanism: none
      reason: >
        Stateless agent. Each task is self-contained.

  event_handling:
    consumer_group: content-analyzer
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "content-analyzer@vN+1"
      after_cutover: "content-analyzer"
```

---

## Implementation Notes

### Readability Calculation

Flesch-Kincaid readability ease:
```
206.835 - 1.015 × (total_words / total_sentences)
        - 84.6  × (total_syllables / total_words)
```

Score ranges:
- 90–100: Very easy (5th grade)
- 60–70: Standard (8th–9th grade) — target for web content
- 30–50: Difficult (college level)
- 0–30: Very difficult (graduate level)

### Syllable Counting

Use a dictionary-based approach with fallback heuristic:
1. Check a syllable dictionary first (covers common words)
2. Fallback: count vowel groups, subtract silent-e, add for
   -le/-les endings

### Structure Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| No h1 | critical | Every page needs exactly one h1 |
| Multiple h1 | high | Only one h1 per page |
| Skipped heading level | high | h1 → h3 (missing h2) |
| Paragraph > 150 words | medium | Consider splitting for readability |
| Section imbalance > 3x | medium | One section is 3x longer than the shortest |
| No lists in dense content | low | 3+ consecutive short sentences could be a list |

### Duplicate Detection

Text fingerprinting via shingle-based hashing:
1. Extract normalized text (lowercase, strip punctuation)
2. Generate 3-word shingles
3. Hash each shingle
4. Compare MinHash signatures across files
5. Similarity > 0.8 → flag as potential duplicate

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: content, port: 9720
- [ ] Reads HTML and markdown files via file:read capability
- [ ] Computes Flesch-Kincaid readability score for each file
- [ ] Validates heading hierarchy (h1 → h2 → h3 order)
- [ ] Flags pages below config.thin_content_threshold as thin content
- [ ] Generates findings with severity and category
- [ ] apply_fix only modifies structure (never changes content text)
- [ ] Returns FileAnalysis per file with all required fields
- [ ] Content score is 0–100 scale with configurable weights
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded, and retiring states
- [ ] Startup sequence has pre-check, validates, on-fail for each step
- [ ] Shutdown drains in-flight tasks before deregistering
- [ ] Health endpoint reports accurate status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for tasks, findings, scores, and readability
- [ ] Security permissions limited to file:read, file:write, agent:message
- [ ] Constraints enforce analysis-only for analyze/score actions
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
