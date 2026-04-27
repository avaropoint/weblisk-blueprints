<!-- blueprint
type: agent
name: meta-checker
version: 1.1.0
kind: work
port: 9721
extends: [patterns/observability, patterns/security]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: content
-->

# Meta Checker Agent

Work agent that validates HTML metadata completeness and correctness.
Dispatched by the content domain controller. Checks `<head>` elements
including title, description, Open Graph tags, Twitter cards, canonical
URLs, structured data (JSON-LD), and favicon references.

## Overview

The meta-checker agent performs static metadata validation on HTML
files. It parses `<head>` elements and evaluates completeness across
five categories: required tags (title, description, viewport, canonical,
lang), Open Graph tags, Twitter Card tags, structured data (JSON-LD),
and additional metadata (favicon, charset, robots, hreflang). Each
category is scored independently and combined into an overall metadata
completeness score.

The agent is stateless — all file paths are provided in the task
payload and all results are returned to the content domain controller.

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
        - name: Finding
          fields_used: [rule_id, severity, element, message]
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
    default: 30
    env: WL_META_ANALYSIS_TIMEOUT
    min: 5
    max: 120
    unit: seconds
    description: Maximum time for a single task

  max_files_per_task:
    type: int
    default: 50
    env: WL_META_MAX_FILES
    min: 1
    max: 500
    description: Maximum files accepted in a single task

  title_min_length:
    type: int
    default: 30
    env: WL_META_TITLE_MIN
    min: 10
    max: 50
    description: Minimum acceptable title length

  title_max_length:
    type: int
    default: 60
    env: WL_META_TITLE_MAX
    min: 40
    max: 100
    description: Maximum acceptable title length

  description_min_length:
    type: int
    default: 120
    env: WL_META_DESC_MIN
    min: 50
    max: 150
    description: Minimum acceptable meta description length

  description_max_length:
    type: int
    default: 160
    env: WL_META_DESC_MAX
    min: 100
    max: 250
    description: Maximum acceptable meta description length

  og_image_min_width:
    type: int
    default: 1200
    env: WL_META_OG_IMAGE_WIDTH
    min: 600
    max: 2400
    description: Minimum Open Graph image width in pixels

  og_image_min_height:
    type: int
    default: 630
    env: WL_META_OG_IMAGE_HEIGHT
    min: 315
    max: 1260
    description: Minimum Open Graph image height in pixels

  weight_required:
    type: float
    default: 0.40
    env: WL_META_WEIGHT_REQUIRED
    description: Scoring weight for required tags category

  weight_open_graph:
    type: float
    default: 0.25
    env: WL_META_WEIGHT_OG
    description: Scoring weight for Open Graph tags category

  weight_twitter:
    type: float
    default: 0.15
    env: WL_META_WEIGHT_TWITTER
    description: Scoring weight for Twitter Card tags category

  weight_structured_data:
    type: float
    default: 0.10
    env: WL_META_WEIGHT_JSONLD
    description: Scoring weight for structured data category

  weight_additional:
    type: float
    default: 0.10
    env: WL_META_WEIGHT_ADDITIONAL
    description: Scoring weight for additional metadata category
```

---

## Types

Types are the single source of truth. Action inputs, outputs, and
event payloads all reference these definitions.

```yaml
types:
  MetaTagStatus:
    description: Validation status for a single meta tag
    fields:
      present:
        type: bool
        description: Whether the tag exists in the document
      value:
        type: string
        optional: true
        description: Current tag value
      length:
        type: int
        optional: true
        description: Character length of the value
      valid:
        type: bool
        description: Whether the tag passes validation rules
      url:
        type: string
        optional: true
        description: URL value for image or link tags

  MetaReport:
    description: Complete metadata analysis for a single HTML file
    fields:
      file:
        type: string
        description: Relative file path
      meta_score:
        type: int
        min: 0
        max: 100
        description: Overall metadata completeness score
      required:
        type: object
        description: >
          Status of required tags: title, description, viewport,
          canonical, lang. Each is a MetaTagStatus.
      open_graph:
        type: object
        description: >
          Status of OG tags: og:title, og:description, og:image,
          og:url, og:type, og:site_name. Each is a MetaTagStatus.
      twitter_card:
        type: object
        description: >
          Status of Twitter tags: twitter:card, twitter:title,
          twitter:description, twitter:image. Each is a MetaTagStatus.
      structured_data:
        type: object
        description: >
          JSON-LD status: present (bool), valid (bool),
          types (string[]), errors (string[])
      additional:
        type: object
        description: >
          Additional metadata: favicon, charset, robots, hreflang.
          Each has a present (bool) field.
      findings:
        type: array
        items: MetaFinding
        description: All metadata issues for this file

  MetaFinding:
    description: A single metadata validation issue
    fields:
      rule_id:
        type: string
        format: "meta-{category}-{detail}"
        description: Unique rule identifier
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Issue severity
      tag:
        type: string
        description: The meta tag involved
      file:
        type: string
        description: File where issue was found
      message:
        type: string
        max: 512
        description: Human-readable description
      current:
        type: string
        optional: true
        description: Current value
      expected:
        type: string
        optional: true
        description: Expected value or constraint

  MetaFix:
    description: A proposed metadata fix
    fields:
      type:
        type: string
        enum: [add_meta, update_meta, remove_meta]
        description: Fix type
      file:
        type: string
        description: Target file path
      tag:
        type: string
        description: Meta tag name or property
      proposed:
        type: string
        description: Proposed HTML to insert or replacement
      reason:
        type: string
        description: Explanation of why this fix is needed
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
        side_effect: emit meta.task.failed event
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
  Validates:   All config values within declared constraints;
               scoring weights sum to 1.0
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/meta-checker/
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
  Log: lifecycle.ready {port: 9721, capabilities: [file:read, agent:message]}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  Validates:   Signal recognized
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new task requests

Step 3 — Drain In-Flight
  Action:      Wait for current analysis to complete (up to config.analysis_timeout)
  On Timeout:  Return partial results

Step 4 — Deregister
  Action:      DELETE /v1/register

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
    actions: [check, apply_fix, validate_structured_data]
    description: >
      Receive metadata validation tasks from the content domain controller.

  - name: shutdown
    type: event
    topic: system.shutdown
    description: Begin graceful shutdown

  - name: blueprint_changed
    type: event
    topic: system.blueprint.changed
    filter: blueprint_name = "meta-checker"
    description: Self-update if meta-checker blueprint changed
```

---

## Actions

### check

Validate metadata completeness for a list of HTML files.

**Purpose:** Parse `<head>` elements and evaluate metadata across all
five categories: required, Open Graph, Twitter Card, structured data,
and additional tags.

**Input:** `{files: string[]}` — array of relative HTML file paths.

**Processing:**

```
1. Validate input:
   a. files array is non-empty
   b. Array length <= config.max_files_per_task
2. For each file:
   a. Read file content via file:read capability
   b. Parse <head> section
   c. CHECK required meta tags:
      - <title>: exists, length within config.title_min/max_length, unique
      - <meta name="description">: exists, length within config.description_min/max_length
      - <meta name="viewport">: exists
      - <link rel="canonical">: exists, valid URL
      - <html lang="">: language attribute set
   d. CHECK Open Graph tags:
      - og:title, og:description, og:image, og:url, og:type, og:site_name
      - og:image must be absolute URL with dimensions >= config thresholds
   e. CHECK Twitter Card tags:
      - twitter:card, twitter:title, twitter:description, twitter:image
   f. CHECK structured data (JSON-LD):
      - At least one <script type="application/ld+json"> block
      - Valid JSON, @type present and recognized, required properties present
   g. CHECK additional metadata:
      - favicon, robots, charset, hreflang
   h. SCORE completeness using configured category weights
   i. BUILD findings array
3. Return MetaReport[] to domain controller
```

**Output:** `{results: MetaReport[]}`

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

Insert or update metadata tags in an HTML file.

**Purpose:** Apply a proposed metadata fix by inserting a missing tag
or updating an existing one in the `<head>` section.

**Input:** `{file: string, fix: MetaFix}`

**Processing:**

```
1. Validate input:
   a. file exists and is readable
   b. fix.type is one of allowed enum values
   c. fix.proposed is valid HTML
2. Parse file, locate <head> section
3. Apply fix:
   a. add_meta: insert fix.proposed before </head>
   b. update_meta: find existing tag, replace content attribute
   c. remove_meta: find and remove existing tag
4. Verify fix applied (re-parse and validate)
5. Return diff
```

**Output:** `{success: bool, diff: string}`

**Errors:**

```yaml
errors:
  - code: INVALID_INPUT
    condition: Fix type invalid or proposed HTML malformed
    retryable: false
  - code: FILE_NOT_FOUND
    condition: Target file does not exist
    retryable: false
  - code: FILE_WRITE_ERROR
    condition: Cannot write modified file
    retryable: true
  - code: TAG_NOT_FOUND
    condition: Target tag for update/remove not found in file
    retryable: false
```

**Side Effects:** Modifies the target file's `<head>` section.

**Idempotency:** add_meta is not idempotent (could insert duplicates).
Guard by checking if tag already exists before inserting.

---

### validate_structured_data

Validate JSON-LD structured data in a single file.

**Purpose:** Deep validation of JSON-LD blocks — syntax, schema
compliance, and consistency with other meta tags.

**Input:** `{file: string}`

**Processing:**

```
1. Read and parse the file
2. Extract all <script type="application/ld+json"> blocks
3. For each block:
   a. Validate JSON syntax
   b. Check @type is present and recognized
   c. Validate required properties for the declared @type
   d. Check for conflicts with meta tags (e.g., name vs og:title)
4. Return validation result
```

**Output:** `{valid: bool, errors: string[]}`

**Errors:** `FILE_NOT_FOUND` (permanent), `FILE_READ_ERROR` (transient).

**Side Effects:** None — read-only.

**Idempotency:** Fully idempotent.

---

## Execute Workflow

```
1. RECEIVE task from content domain controller
   Input: {target_files: ["index.html", "about.html", ...]}

2. PARSE each HTML file — extract <head> section

3. CHECK required meta tags per file:
   a. <title> — exists, length within configured bounds, unique across site
   b. <meta name="description"> — exists, length within configured bounds
   c. <meta name="viewport"> — exists
   d. <link rel="canonical"> — exists, valid URL
   e. <html lang=""> — language attribute set

4. CHECK Open Graph tags:
   a. og:title, og:description, og:image, og:url, og:type, og:site_name
   b. og:image — absolute URL, dimensions >= configured minimums

5. CHECK Twitter Card tags:
   a. twitter:card — summary or summary_large_image
   b. twitter:title, twitter:description, twitter:image

6. CHECK structured data (JSON-LD):
   a. At least one valid block, correct @type, required properties

7. CHECK additional metadata:
   a. favicon, robots (validate if present), charset (utf-8), hreflang

8. SCORE completeness using configured category weights

9. BUILD findings array per file

10. RETURN MetaReport[] to domain controller
```

---

## Collaboration

```yaml
events_published:
  - topic: meta.check.completed
    payload: {task_id, file_count, avg_score, findings_total}
    when: check action completes successfully

  - topic: meta.critical.missing
    payload: {task_id, file, missing_tags}
    when: Required meta tags (title, description) are missing

  - topic: meta.fix.applied
    payload: {task_id, file, tag, fix_type}
    when: apply_fix action completes successfully

events_subscribed:
  - topic: system.shutdown
    payload: {}
    action: Begin graceful shutdown

  - topic: system.blueprint.changed
    payload: {blueprint_name, version}
    filter: blueprint_name = "meta-checker"
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
  full-auto:     All validation is autonomous
  supervised:    Operator can adjust length thresholds and scoring weights
  manual-only:   Not applicable for work agents

overridable_behaviors:
  - behavior: title_length_bounds
    default: 30-60 characters
    override: Set WL_META_TITLE_MIN / WL_META_TITLE_MAX
    audit: logged

  - behavior: description_length_bounds
    default: 120-160 characters
    override: Set WL_META_DESC_MIN / WL_META_DESC_MAX
    audit: logged

  - behavior: scoring_weights
    default: required 0.40, og 0.25, twitter 0.15, jsonld 0.10, additional 0.10
    override: Set WL_META_WEIGHT_* environment variables
    audit: logged

  - behavior: og_image_dimensions
    default: 1200x630
    override: Set WL_META_OG_IMAGE_WIDTH / WL_META_OG_IMAGE_HEIGHT
    audit: logged

manual_actions:
  - action: run_check
    description: Manually trigger metadata check via CLI
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
    - MUST NOT modify file content during check or validate_structured_data actions
    - MUST NOT send messages to agents other than the dispatching controller

  forbidden_actions:
    - MUST NOT modify existing tag content during check (flags and suggests only)
    - MUST NOT make network requests (file-based analysis only)
    - MUST NOT validate external URLs referenced in meta tags (canonical, og:image)

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
    - code: TAG_NOT_FOUND
      description: Target tag for update/remove not found in file
    - code: CONFIG_INVALID
      description: Configuration values outside declared constraints

  transient:
    - code: FILE_READ_ERROR
      description: File exists but read failed
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
  - log_type: meta.task.received
    level: info
    when: Task received from domain controller
    fields: {task_id, action, file_count, trace_id}

  - log_type: meta.task.completed
    level: info
    when: Metadata check completed
    fields: {task_id, file_count, avg_score, duration_ms}

  - log_type: meta.task.failed
    level: warn
    when: Metadata check failed
    fields: {task_id, error_code}

  - log_type: meta.critical.missing
    level: warn
    when: Required meta tags missing from a file
    fields: {file, missing_tags}

  - log_type: meta.fix.applied
    level: info
    when: Metadata fix applied
    fields: {task_id, file, tag, fix_type}

metrics:
  - name: wl_meta_tasks_total
    type: counter
    labels: [action, status]
    description: Total tasks processed by action and outcome

  - name: wl_meta_task_duration_seconds
    type: histogram
    labels: [action]
    description: Task processing duration

  - name: wl_meta_findings_total
    type: counter
    labels: [severity, tag]
    description: Findings by severity and tag name

  - name: wl_meta_score_distribution
    type: histogram
    description: Distribution of metadata completeness scores

  - name: wl_meta_tags_present_ratio
    type: gauge
    labels: [category]
    description: Ratio of present tags per category across analyzed files

alerts:
  - condition: Error rate > 20% of tasks in 10-minute window
    severity: warn
    routing: alerting agent

  - condition: All tasks failing for 5+ minutes
    severity: critical
    routing: alerting agent
```

---

## Security

```yaml
security:
  permissions:
    - capability: file:read
      resources: ["**/*.html"]
      description: Read HTML files for metadata validation

    - capability: file:write
      resources: ["**/*.html"]
      description: Write metadata fixes via apply_fix action only

    - capability: agent:message
      resources: ["*"]
      description: Receive tasks from and return results to domain controllers

  data_sensitivity:
    - data: HTML head content
      classification: low
      handling: Read in memory, discarded after analysis

    - data: Meta tag values (titles, descriptions)
      classification: low
      handling: Returned to domain controller in MetaReport

    - data: JSON-LD structured data
      classification: low
      handling: Validated in memory, not stored

  access_control:
    - caller: Domain controller (content)
      actions: [check, apply_fix, validate_structured_data]

    - caller: Operator (auth token with operator role)
      actions: [check, apply_fix, validate_structured_data]

    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: Check fully tagged page
    action: check
    input:
      files: ["fully-tagged.html"]
    expected:
      results:
        - file: "fully-tagged.html"
          meta_score: ">= 90"
          required: {title: {present: true, valid: true}}
          open_graph: {og:title: {present: true, valid: true}}
    validates:
      - Complete metadata scores above 90
      - All required tags detected and validated

  - name: Validate valid JSON-LD
    action: validate_structured_data
    input: {file: "with-jsonld.html"}
    expected: {valid: true, errors: []}
    validates:
      - Valid JSON-LD block passes validation

  - name: Apply missing og:site_name fix
    action: apply_fix
    input:
      file: "about.html"
      fix: {type: "add_meta", tag: "og:site_name",
            proposed: '<meta property="og:site_name" content="Weblisk">',
            reason: "Missing og:site_name for social sharing"}
    expected: {success: true, diff: "<non-empty>"}
    validates:
      - Meta tag inserted before </head>
```

### Error Cases

```yaml
  - name: Empty file list
    action: check
    input: {files: []}
    expected_error: INVALID_INPUT
    validates: [Empty input rejected]

  - name: Non-existent file
    action: check
    input: {files: ["missing.html"]}
    expected_error: FILE_NOT_FOUND
    validates: [Missing files produce permanent error]

  - name: Invalid JSON-LD
    action: validate_structured_data
    input: {file: "bad-jsonld.html"}
    expected: {valid: false, errors: ["Invalid JSON syntax"]}
    validates: [Malformed JSON-LD detected and reported]
```

### Edge Cases

```yaml
  - name: Page with no <head> section
    action: check
    input: {files: ["no-head.html"]}
    expected:
      results:
        - meta_score: 0
          findings: [{severity: "critical", message: "No <head> section found"}]
    validates: [Missing head section handled gracefully]

  - name: Duplicate og:title tags
    action: check
    input: {files: ["duplicate-og.html"]}
    condition: File has two og:title meta tags
    expected: Finding warns about duplicate tags
    validates: [Duplicate meta tags detected]

  - name: Title at exact boundary
    action: check
    input: {files: ["boundary-title.html"]}
    condition: Title is exactly 30 characters (config.title_min_length)
    expected: Title passes validation
    validates: [Boundary values accepted]

  - name: Accidental noindex in robots
    action: check
    input: {files: ["noindex.html"]}
    condition: <meta name="robots" content="noindex">
    expected: Finding with severity info warns about noindex
    validates: [Accidental noindex flagged for review]
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
      reason: Stateless agent. Each task is self-contained.

  event_handling:
    consumer_group: meta-checker
    delivery: one-per-group
    description: Each task delivered to exactly one instance.

  blue_green:
    strategy: immediate
    shadow_duration: 0
    cutover_watch_period: 60
    storage_sharing: not-applicable
    consumer_groups:
      shadow_phase: "meta-checker@vN+1"
      after_cutover: "meta-checker"
```

---

## Implementation Notes

- **HTML Parsing**: Use a tolerant parser for the `<head>` section.
  Handle both `<meta name=... content=...>` and `<meta content=... name=...>`
  attribute orders. Both formats appear in the wild.
- **Open Graph Validation**: og:image URL validation is syntactic only
  (absolute URL check). The agent does not fetch the image to verify
  dimensions — that would require network access. Image dimension
  checks are best-effort when width/height are declared in markup.
- **JSON-LD Validation**: The agent validates JSON syntax and checks
  for required properties per `@type`. Supported types include
  WebSite, Article, Product, Organization, and BreadcrumbList. Unknown
  types are flagged as info-level findings, not errors.
- **Tag Uniqueness**: Title uniqueness checking requires the domain
  controller to provide context about other pages. The meta-checker
  flags duplicate titles only when multiple files in the same task
  share the same title.
- **Scoring**: Each category contributes its configured weight. Within
  a category, score = (tags_present_and_valid / total_tags) × 100.
  The overall score is the weighted sum across categories.

### Validation Rules Reference

| Tag | Severity | Validation |
|-----|----------|------------|
| title | critical | Must exist, 30–60 chars |
| meta description | critical | Must exist, 120–160 chars |
| viewport | high | Must exist |
| canonical | high | Must exist, valid absolute URL |
| og:title | medium | Must exist for social sharing |
| og:description | medium | Must exist for social sharing |
| og:image | medium | Must exist, absolute URL |
| twitter:card | medium | Must exist for Twitter previews |
| JSON-LD | medium | Must be valid JSON, correct @type |
| charset | low | Should be utf-8 |
| favicon | low | Should exist for browser tabs |
| robots | info | Validate if present (no accidental noindex) |

### Length Constraints Reference

| Tag | Min | Max | Optimal |
|-----|-----|-----|---------|
| title | 30 | 60 | 50–60 |
| meta description | 120 | 160 | 150–160 |
| og:title | 30 | 60 | 50–60 |
| og:description | 55 | 200 | 120–160 |
| twitter:title | 30 | 70 | 50–60 |
| twitter:description | 55 | 200 | 120–160 |

---

## Verification Checklist

- [ ] Agent registers with kind: work, domain: content, port: 9721
- [ ] Reads only HTML files via file:read capability
- [ ] Validates all 5 required meta tag categories
- [ ] Checks Open Graph completeness (6 tags)
- [ ] Checks Twitter Card completeness (4 tags)
- [ ] Validates JSON-LD syntax and required @type properties
- [ ] Scores metadata completeness on 0–100 scale with configured weights
- [ ] apply_fix inserts missing tags into `<head>` section correctly
- [ ] Findings include severity levels matching validation table
- [ ] Does not modify existing tag content during check — only flags and suggests
- [ ] Dependency contracts declare version ranges and bindings
- [ ] State machine covers executing, degraded, and retiring states
- [ ] Startup sequence has pre-check, validates, on-fail for each step
- [ ] Shutdown drains in-flight tasks before deregistering
- [ ] Health endpoint reports accurate status
- [ ] All errors classified as permanent or transient
- [ ] Metrics emitted for tasks, findings, scores, and tag presence ratios
- [ ] Security permissions limited to file:read, file:write, agent:message
- [ ] Constraints enforce read-only for check and validate_structured_data actions
- [ ] Test fixtures cover happy path, error cases, and edge cases
- [ ] Scaling: stateless shared-nothing model
