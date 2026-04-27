<!-- blueprint
type: domain
kind: domain
name: content
version: 1.1.0
port: 9701
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/data-contract, patterns/governance, patterns/security]
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
platform: any
tier: free
-->

# Content Domain Controller

The content domain controller owns the content quality business
function. It receives high-level tasks ("audit this site's content",
"optimize these pages"), decomposes them into multi-agent workflows,
dispatches work to specialized agents, aggregates results, and feeds
outcomes back into the continuous optimization lifecycle.

This domain does NOT perform content analysis itself. It directs agents
that do: the [content-analyzer](../agents/content-analyzer.md) for
readability, structure, and link quality, and the
[meta-checker](../agents/meta-checker.md) for metadata validation
including Open Graph, Twitter Cards, and structured data.

## Overview

The content domain controller orchestrates content quality assessment
and optimization across monitored sites. It decomposes high-level
audit and optimize tasks into phased workflows dispatched to the
content-analyzer and meta-checker agents, aggregates their findings
into scored reports, generates prioritized recommendations, and feeds
results back into the lifecycle observation store for continuous
improvement tracking.

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

  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WLT
          fields_used: [sub, iss, aud, exp, capabilities]
      patterns:
        - behavior: token-verification
          parameters: [public_key, claims, expiry]
    on_change:
      compatible: validate
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
        - name: Observation
          fields_used: [target, element, measurement, timestamp]
        - name: Recommendation
          fields_used: [id, category, severity, title, description, priority, impact]
        - name: Feedback
          fields_used: [recommendation_id, type, signal, metric_before, metric_after]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: workflow-orchestration
          parameters: [phases, dependencies, timeout, aggregation]
        - behavior: agent-dispatch
          parameters: [target_agent, action, payload, timeout]
        - behavior: domain-scoring
          parameters: [weights, formula, clamp]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/lifecycle
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: observation-store
          parameters: [record, query, retention]
        - behavior: recommendation-tracking
          parameters: [create, approve, reject, measure]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

extends:
  - pattern: patterns/domain-controller
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: workflow-execution
          parameters: [phases, dispatch, aggregate, report]
        - behavior: domain-health
          parameters: [agent_availability, status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: metrics
          parameters: [gauge, counter, histogram]
        - behavior: alerts
          parameters: [condition, severity, routing]
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
        - behavior: backup-restore
          parameters: [frequency, format, path]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/workflow
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: phase-execution
          parameters: [agent, action, input, output, timeout, depends_on]
        - behavior: workflow-state
          parameters: [pending, running, completed, failed]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/data-contract
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: schema-validation
          parameters: [input_schema, output_schema]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: approval-gate
          parameters: [require_approval, auto_approve]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: token-auth
          parameters: [verify_wlt, required_capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

depends_on:
  - agent: content-analyzer
    required: true
    description: Readability scoring, heading hierarchy, word count, sentence complexity, link density
  - agent: meta-checker
    required: true
    description: Title, description, Open Graph, Twitter Cards, structured data, canonical URLs
```

---

## Domain Manifest

```json
{
  "name": "content",
  "type": "domain",
  "version": "1.0.0",
  "description": "Content quality — readability, structure, metadata, link quality",
  "url": "http://localhost:9701",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "target_files", "type": "file_list", "description": "HTML files to audit or optimize"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated content quality report with recommendations"}
  ],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["content-analyzer", "meta-checker"],
  "workflows": ["content-audit", "content-optimize"]
}
```

---

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| content-analyzer | Readability scoring, heading hierarchy, word count, sentence complexity, link density | `analyze` action — analyze, structure phases |
| meta-checker | Title, description, Open Graph, Twitter Cards, structured data, canonical URLs | `check` action — metadata, structured-data phases |

---

## Workflows

### content-audit

Full content quality audit of a set of HTML files. Produces a scored
report with findings, recommendations, and proposed changes.

Trigger: `task.action = "audit"`

```yaml
workflow: content-audit
phases:
  - name: analyze
    agent: content-analyzer
    action: analyze
    input:
      html_files: $task.payload.files
    output: content_results
    timeout: 120

  - name: metadata
    agent: meta-checker
    action: check
    input:
      html_files: $task.payload.files
    output: metadata_results
    timeout: 60

  - name: aggregate
    agent: self
    action: aggregate_results
    input:
      content: $phases.analyze.output
      metadata: $phases.metadata.output
    output: aggregated
    depends_on: [analyze, metadata]

  - name: recommend
    agent: self
    action: generate_recommendations
    input:
      aggregated: $phases.aggregate.output
    output: recommendations
    depends_on: [aggregate]

  - name: observe
    agent: self
    action: record_observations
    input:
      results: $phases.aggregate.output
      recommendations: $phases.recommend.output
    output: observations
    depends_on: [recommend]

  - name: report
    agent: self
    action: compile_report
    input:
      aggregated: $phases.aggregate.output
      recommendations: $phases.recommend.output
      observations: $phases.observe.output
    output: domain_report
    depends_on: [observe]
```

Phase dependency: analyze + metadata (parallel) → aggregate → recommend → observe → report

### content-optimize

Apply previously approved content recommendations. Runs AFTER audit
recommendations are reviewed and accepted.

Trigger: `task.action = "optimize"`

```yaml
workflow: content-optimize
phases:
  - name: plan
    agent: self
    action: select_optimizations
    input:
      approved: $task.payload.approved_recommendations
    output: optimization_plan
    timeout: 30

  - name: execute
    agent: self
    action: apply_changes
    input:
      plan: $phases.plan.output
      files: $task.payload.files
    output: applied_changes
    depends_on: [plan]
    timeout: 120

  - name: verify
    agent: content-analyzer
    action: analyze
    input:
      html_files: $phases.execute.output.modified_files
    output: verification_results
    depends_on: [execute]
    timeout: 120

  - name: measure
    agent: self
    action: compare_before_after
    input:
      before: $task.payload.original_scores
      after: $phases.verify.output
    output: improvement_metrics
    depends_on: [verify]
```

Phase dependency: plan → execute → verify → measure

---

## Configuration

```yaml
config:
  readability_weight:
    type: float
    default: 0.30
    env: WL_CONTENT_READABILITY_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for readability component in content score

  structure_weight:
    type: float
    default: 0.30
    env: WL_CONTENT_STRUCTURE_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for structure component in content score

  metadata_weight:
    type: float
    default: 0.25
    env: WL_CONTENT_METADATA_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for metadata component in content score

  link_quality_weight:
    type: float
    default: 0.15
    env: WL_CONTENT_LINK_QUALITY_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for link quality component in content score

  workflow_timeout:
    type: int
    default: 300
    env: WL_CONTENT_WORKFLOW_TIMEOUT
    min: 30
    max: 900
    unit: seconds
    description: Maximum wall-clock time for a single workflow execution

  agent_dispatch_timeout:
    type: int
    default: 120
    env: WL_CONTENT_AGENT_DISPATCH_TIMEOUT
    min: 10
    max: 300
    unit: seconds
    description: Default timeout per agent dispatch

  max_concurrent_workflows:
    type: int
    default: 2
    env: WL_CONTENT_MAX_CONCURRENT_WORKFLOWS
    min: 1
    max: 10
    description: Maximum concurrent workflow executions

  observation_retention_days:
    type: int
    default: 90
    env: WL_CONTENT_OBSERVATION_RETENTION_DAYS
    min: 7
    max: 365
    unit: days
    description: Observation storage retention period

  finding_severity_threshold:
    type: string
    default: medium
    env: WL_CONTENT_FINDING_SEVERITY_THRESHOLD
    enum: [info, low, medium, high, critical]
    description: Minimum severity for findings included in recommendations
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  ContentDomainResult:
    description: Aggregated domain report for content quality
    fields:
      report_id:
        type: string
        format: uuid-v7
        description: Unique report identifier
      workflow_id:
        type: string
        format: uuid-v7
        description: Workflow execution that produced this report
      domain:
        type: string
        const: content
        description: Domain name
      score:
        type: float
        min: 0
        max: 100
        description: Weighted content quality score
      readability_score:
        type: float
        min: 0
        max: 100
        description: Readability sub-score
      structure_score:
        type: float
        min: 0
        max: 100
        description: Structure sub-score
      metadata_score:
        type: float
        min: 0
        max: 100
        description: Metadata sub-score
      link_quality_score:
        type: float
        min: 0
        max: 100
        description: Link quality sub-score
      files_scanned:
        type: int
        min: 0
        description: Number of files analyzed
      total_findings:
        type: int
        min: 0
        description: Total findings count
      critical_findings:
        type: int
        min: 0
        description: Critical severity finding count
      created_at:
        type: int64
        auto: true
        description: Report creation timestamp

  ContentWorkflowResult:
    description: Single workflow phase result
    fields:
      result_id:
        type: string
        format: uuid-v7
        description: Unique result identifier
      workflow_id:
        type: string
        format: uuid-v7
        description: Parent workflow execution
      phase:
        type: string
        description: Workflow phase name
      agent:
        type: string
        description: Agent that produced this result
      status:
        type: string
        enum: [success, failed, timeout, skipped]
        description: Phase execution status
      duration_ms:
        type: int
        optional: true
        description: Phase execution duration
      output:
        type: object
        optional: true
        description: Phase output data
      error:
        type: text
        optional: true
        description: Error message on failure
      created_at:
        type: int64
        auto: true
        description: Result creation timestamp

  ContentFinding:
    description: A single content quality finding
    fields:
      finding_id:
        type: string
        format: uuid-v7
        description: Unique finding identifier
      report_id:
        type: string
        format: uuid-v7
        references: ContentDomainResult.report_id
        description: Parent report
      category:
        type: string
        enum: [readability, structure, metadata, links, formatting, structured-data, social]
        description: Finding category
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Finding severity
      target:
        type: string
        description: File path or URL
      element:
        type: string
        optional: true
        description: Specific element (e.g., tag name, selector)
      title:
        type: string
        max: 256
        description: Short finding description
      description:
        type: text
        optional: true
        description: Detailed explanation
      source_agent:
        type: string
        description: Agent that produced this finding
      created_at:
        type: int64
        auto: true
        description: Finding creation timestamp

  ContentObservation:
    description: Lifecycle observation for trend tracking
    fields:
      observation_id:
        type: string
        format: uuid-v7
        description: Unique observation identifier
      report_id:
        type: string
        format: uuid-v7
        references: ContentDomainResult.report_id
        description: Parent report
      target:
        type: string
        description: File path or URL observed
      element:
        type: string
        description: What was measured
      measurement:
        type: float
        description: Measured value
      unit:
        type: string
        optional: true
        description: Measurement unit
      timestamp:
        type: int64
        auto: true
        description: Observation timestamp

  ContentRecommendation:
    description: Actionable recommendation from analysis
    fields:
      recommendation_id:
        type: string
        format: uuid-v7
        description: Unique recommendation identifier
      report_id:
        type: string
        format: uuid-v7
        references: ContentDomainResult.report_id
        description: Parent report
      category:
        type: string
        enum: [readability, structure, metadata, links, formatting, structured-data, social]
        description: Recommendation category
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Associated severity
      title:
        type: string
        max: 256
        description: Short recommendation title
      description:
        type: text
        description: Detailed recommendation
      priority:
        type: int
        min: 1
        max: 100
        description: Priority score (higher = more important)
      impact:
        type: float
        min: 0
        max: 100
        description: Estimated score impact if applied
      status:
        type: string
        enum: [pending, approved, rejected, applied, measured]
        description: Recommendation lifecycle status
      created_at:
        type: int64
        auto: true
        description: Recommendation creation timestamp
```

---

## Storage

Storage tables reference the Types section. Fields are not redefined
here — the `source_type` key links each table to its type definition.

```yaml
storage:
  engine: sqlite

  tables:
    content_reports:
      source_type: ContentDomainResult
      primary_key: report_id
      indexes:
        - name: idx_report_workflow
          fields: [workflow_id]
          type: btree
        - name: idx_report_created
          fields: [created_at]
          type: btree
          description: Time-ordered report lookup

    content_workflow_results:
      source_type: ContentWorkflowResult
      primary_key: result_id
      indexes:
        - name: idx_wfresult_workflow
          fields: [workflow_id]
          type: btree
        - name: idx_wfresult_phase
          fields: [workflow_id, phase]
          type: btree

    content_findings:
      source_type: ContentFinding
      primary_key: finding_id
      indexes:
        - name: idx_finding_report
          fields: [report_id]
          type: btree
        - name: idx_finding_severity
          fields: [severity, category]
          type: btree
          description: Severity-first lookup for prioritization
        - name: idx_finding_target
          fields: [target]
          type: btree

    content_observations:
      source_type: ContentObservation
      primary_key: observation_id
      indexes:
        - name: idx_obs_report
          fields: [report_id]
          type: btree
        - name: idx_obs_target
          fields: [target, element, timestamp]
          type: btree
          description: Trend query by target and element

    content_recommendations:
      source_type: ContentRecommendation
      primary_key: recommendation_id
      indexes:
        - name: idx_rec_report
          fields: [report_id]
          type: btree
        - name: idx_rec_status
          fields: [status]
          type: btree
        - name: idx_rec_priority
          fields: [priority]
          type: btree

  relationships:
    - name: report_findings
      from: content_findings.report_id
      to: content_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Findings belong to a report

    - name: report_observations
      from: content_observations.report_id
      to: content_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Observations belong to a report

    - name: report_recommendations
      from: content_recommendations.report_id
      to: content_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Recommendations belong to a report

    - name: report_workflow_results
      from: content_workflow_results.workflow_id
      to: content_reports.workflow_id
      cardinality: many-to-one
      on_delete: cascade
      description: Phase results belong to a workflow/report

  retention:
    content_reports:
      policy: config.observation_retention_days
      cleanup: daily sweep deletes reports older than retention
    content_findings:
      policy: cascades from content_reports
    content_observations:
      policy: config.observation_retention_days
      cleanup: daily sweep
    content_recommendations:
      policy: indefinite for approved/applied; config.observation_retention_days for others
    content_workflow_results:
      policy: cascades from content_reports

  backup:
    content_reports:
      frequency: daily
      format: JSON export
      path: .weblisk/backups/content/reports_{ISO8601}.json
    content_recommendations:
      frequency: daily
      format: JSON export (pending and approved only)
      path: .weblisk/backups/content/recommendations_{ISO8601}.json
```

---

## State Machine

```yaml
state_machine:
  domain:
    initial: created
    transitions:
      - from: created
        to: registered
        trigger: orchestrator_ack
        validates: agent_id assigned, WLT token received
      - from: registered
        to: online
        trigger: all_agents_available
        validates: content-analyzer and meta-checker respond to health
      - from: registered
        to: degraded
        trigger: partial_agents_available
        validates: at least one required agent unavailable
      - from: online
        to: degraded
        trigger: agent_unavailable
        validates: health check failure on required agent
      - from: degraded
        to: online
        trigger: all_agents_recovered
        validates: all required agents respond to health
      - from: online
        to: retiring
        trigger: shutdown_signal
        validates: SIGTERM, system.shutdown, or API
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: SIGTERM, system.shutdown, or API
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in-flight workflows finished or timed out

  workflow:
    initial: pending
    transitions:
      - from: pending
        to: running
        trigger: workflow_started
        validates: all required agents available (or degraded mode accepted)
      - from: running
        to: completed
        trigger: all_phases_done
        validates: report phase output is valid ContentDomainResult
      - from: running
        to: failed
        trigger: critical_phase_error
        validates: non-recoverable error in required phase
      - from: running
        to: partial
        trigger: non_critical_phase_error
        validates: optional phase failed but report can be generated
      - from: pending
        to: rejected
        trigger: domain_offline
        validates: domain status is offline
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Pre-check:   Process has read access to environment
  Validates:   All config values within declared min/max/enum constraints
               Scoring weights sum to 1.0 (±0.01 tolerance)
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/content/
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes, private key decrypts test payload
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine, validate schema against Types
  Pre-check:   Storage engine available
  Validates:   All tables exist with correct schema; run migrations if needed
  On Fail:     RETRY 3x with 2s backoff → EXIT with STORAGE_UNREACHABLE
  Backout:     Rollback partial migrations

Step 4 — Register with Orchestrator
  Action:      POST /v1/register with domain manifest
  Pre-check:   Steps 1-3 validated
  Validates:   HTTP 200, agent_id and WLT token returned
  On Fail:     RETRY 3x exponential → EXIT with REGISTRATION_FAILED
  Backout:     None (registration is idempotent)

Step 5 — Discover Required Agents
  Action:      Query orchestrator for content-analyzer, meta-checker
  Pre-check:   Step 4 validated (registered)
  Validates:   Both agents registered and responding to health
  On Fail:     Enter degraded state — domain operational but cannot
               execute workflows until agents become available
  Backout:     None

Step 6 — Subscribe to Events
  Action:      Subscribe to: system.agent.registered,
               system.agent.deregistered, system.shutdown,
               domain.content.task, system.blueprint.changed
  Pre-check:   Step 4 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial, deregister, EXIT
  Backout:     Unsubscribe all, deregister, close storage

Final:
  domain_state → online (or degraded if agents unavailable)
  Log: lifecycle.ready {port: 9701, agents: {content-analyzer: up|down, meta-checker: up|down}}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API shutdown
  domain_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new workflow requests

Step 3 — Drain In-Flight Workflows
  Action:      Wait for running workflows to complete (up to 60s)
  On Timeout:  Mark running workflows as failed with partial results

Step 4 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges removal

Step 5 — Close Storage
  Action:      Close database connection

Step 6 — Exit
  Log: lifecycle.stopped {uptime_seconds, workflows_drained, workflows_timed_out}
  domain_state → retired
```

### Health

Reported via `GET /v1/health`:

```yaml
health:
  online:
    conditions:
      - all required agents available
      - storage connected
      - in_flight_workflows < max_concurrent_workflows
    response:
      status: online
      details: {agents: {content-analyzer: up, meta-checker: up},
                storage: connected, in_flight: N}

  degraded:
    conditions:
      - one or more required agents unavailable
      - or storage errors (retrying)
    response:
      status: degraded
      details: {reason, unavailable_agents, last_error}

  offline:
    conditions:
      - all required agents unavailable
      - or storage unreachable after retries
    response:
      status: offline
      details: {reason, since}
```

---

## Triggers

```yaml
triggers:
  message:
    - source: orchestrator
      action: execute_workflow
      description: Primary entry point — orchestrator dispatches task
      payload_type: TaskRequest
      conditions:
        - task.action in ["audit", "optimize"]
      response: TaskResult

    - source: orchestrator
      action: get_status
      description: Domain health and agent availability query
      payload_type: null
      response: HealthResponse

    - source: admin
      action: get_workflows
      description: List available workflow definitions
      payload_type: null
      response: WorkflowList

    - source: admin
      action: workflow_history
      description: Recent workflow executions with results
      payload_type: QueryParams
      response: WorkflowHistoryList

  event:
    - topic: system.agent.registered
      handler: on_agent_registered
      description: Update agent availability when new agent comes online

    - topic: system.agent.deregistered
      handler: on_agent_deregistered
      description: Update agent availability when agent goes offline

    - topic: system.shutdown
      handler: on_shutdown
      description: Begin graceful shutdown sequence

    - topic: system.blueprint.changed
      handler: on_blueprint_changed
      description: Handle blueprint version changes

  schedule:
    - cron: "0 2 * * *"
      action: retention_cleanup
      description: Daily cleanup of expired observations and reports
```

---

## Actions

Domain actions are formalized from the message handler table below.
See [Domain HandleMessage Actions](#domain-handlemessage-actions) for
the complete action reference with input/output specifications.

```yaml
actions:
  execute_workflow:
    source: [orchestrator]
    input: TaskRequest
    output: TaskResult
    description: Route task to appropriate workflow based on task.action

  aggregate_results:
    source: [internal]
    input: {content: AgentResult, metadata: AgentResult}
    output: AggregatedResults
    description: Merge content-analyzer and meta-checker outputs

  generate_recommendations:
    source: [internal]
    input: AggregatedResults
    output: RecommendationList
    description: Prioritize findings into actionable recommendations

  record_observations:
    source: [internal]
    input: {results: AggregatedResults, recommendations: RecommendationList}
    output: ObservationList
    description: Feed results into lifecycle observation store

  select_optimizations:
    source: [internal]
    input: ApprovedRecommendations
    output: OptimizationPlan
    description: Filter and order approved recommendations for execution

  apply_changes:
    source: [internal]
    input: OptimizationPlan
    output: AppliedChanges
    description: Apply approved changes to target files

  compare_before_after:
    source: [internal]
    input: {before: Observations, after: AgentResult}
    output: FeedbackList
    description: Measure score improvement and produce Feedback entries

  get_status:
    source: [orchestrator, admin]
    input: null
    output: HealthResponse
    description: Domain health and agent availability

  get_workflows:
    source: [orchestrator, admin]
    input: null
    output: WorkflowList
    description: Available workflow definitions

  workflow_history:
    source: [admin]
    input: QueryParams
    output: WorkflowHistoryList
    description: Recent workflow executions with results
```

## Domain HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| execute_workflow | Orchestrator | Primary entry point via POST /v1/execute |
| aggregate_results | Internal | Combine content-analyzer + meta-checker outputs |
| generate_recommendations | Internal | Prioritize findings into actionable items |
| record_observations | Internal | Feed results into lifecycle as observations |
| select_optimizations | Internal | Filter approved recommendations for execution |
| apply_changes | Internal | Apply approved changes to files |
| compare_before_after | Internal | Measure score improvement with Feedback entries |
| get_status | Orchestrator/Admin | Domain health and agent availability |
| get_workflows | Orchestrator/Admin | Available workflow definitions |
| workflow_history | Admin | Recent workflow executions with results |

---

## Aggregation

Aggregation combines results from content-analyzer and meta-checker
into a unified report. See [Aggregation Rules](#aggregation-rules)
for the complete merge and conflict resolution logic.

## Aggregation Rules

1. Merge observations: concat, deduplicate by (target + element)
2. Merge findings: sort by severity (critical → high → medium → low → info)
3. Merge recommendations: sort by priority desc, impact desc
4. Merge proposed changes: group by file path
5. Resolve conflicts: when content-analyzer and meta-checker disagree on
   severity for the same element, the agent with the more specific check
   wins (e.g., meta-checker wins on metadata issues, content-analyzer
   wins on readability issues)

---

## Scoring

| Metric | Weight | Source Agent |
|--------|--------|-------------|
| Readability | 30% | content-analyzer |
| Structure | 30% | content-analyzer |
| Metadata | 25% | meta-checker |
| Link quality | 15% | content-analyzer |

Content score = (readability × 0.30) + (structure × 0.30) + (metadata × 0.25) + (links × 0.15), clamped 0–100.

---

## Finding Categories

| Category | Agent | Examples |
|----------|-------|---------|
| readability | content-analyzer | Flesch-Kincaid score, sentence complexity, passive voice |
| structure | content-analyzer | Heading hierarchy, missing H1, skipped levels |
| metadata | meta-checker | Missing title, description too long, no canonical |
| links | content-analyzer | Broken links, excessive link density, no-follow ratio |
| formatting | content-analyzer | Empty paragraphs, orphaned elements |
| structured-data | meta-checker | Invalid JSON-LD, missing required properties |
| social | meta-checker | Missing Open Graph, incomplete Twitter Cards |

---

## Feedback Loop

The content domain tracks recommendation outcomes through a continuous
feedback cycle.

```yaml
feedback_loop:
  observation:
    trigger: content-audit workflow completes
    action: Record ContentObservation entries for each measured element
    store: content_observations table
    retention: config.observation_retention_days

  recommendation:
    trigger: aggregate phase produces findings above severity threshold
    action: Generate ContentRecommendation with priority and impact
    store: content_recommendations table
    status_flow: pending → approved → applied → measured

  application:
    trigger: content-optimize workflow executes approved changes
    action: Apply changes to files, record before/after hashes
    store: content_workflow_results table

  measurement:
    trigger: compare_before_after action in optimize workflow
    action: Compare baseline observations to post-change observations
    produces: Feedback entries with signal (positive/negative/neutral)
    metrics:
      - metric_name: content_score
        direction: higher_is_better
      - metric_name: readability_score
        direction: higher_is_better
      - metric_name: critical_findings
        direction: lower_is_better

  learning:
    trigger: Feedback entries accumulated
    action: Adjust recommendation priority weights based on
            historical positive/negative signal ratio
    constraint: Weight adjustments capped at ±10% per cycle
```

---

## Collaboration

```yaml
collaboration:
  publishes:
    - event: domain.content.report.completed
      payload: {report_id, domain, score, files_scanned, total_findings}
      consumers: [orchestrator, lifecycle, hub]
      description: Emitted when a content-audit workflow completes

    - event: domain.content.optimization.completed
      payload: {report_id, changes_applied, score_before, score_after}
      consumers: [orchestrator, lifecycle]
      description: Emitted when a content-optimize workflow completes

    - event: domain.content.alert
      payload: {severity, category, message, target}
      consumers: [alerting, hub]
      description: Emitted when critical findings detected

  subscribes:
    - event: system.agent.registered
      handler: on_agent_registered
      description: Track content-analyzer and meta-checker availability

    - event: system.agent.deregistered
      handler: on_agent_deregistered
      description: Update domain status when agents go offline

    - event: system.shutdown
      handler: on_shutdown
      description: Begin graceful shutdown

    - event: system.blueprint.changed
      handler: on_blueprint_changed
      description: Handle blueprint updates for self or dependencies

  agent_coordination:
    dispatch_pattern: request-response via POST /v1/message
    timeout: config.agent_dispatch_timeout
    retry: 3 attempts with exponential backoff
    failure_mode: workflow fails with partial results if agent unrecoverable
```

---

## Manual Overrides

```yaml
manual_overrides:
  scoring_weights:
    description: Override default scoring weights at runtime
    method: PUT /v1/config/scoring-weights
    auth: admin WLT with domain:config capability
    payload:
      readability_weight: float (0.0-1.0)
      structure_weight: float (0.0-1.0)
      metadata_weight: float (0.0-1.0)
      link_quality_weight: float (0.0-1.0)
    validation: Weights must sum to 1.0 (±0.01 tolerance)
    audit: Logged as config.override with before/after values and operator identity
    revert: PUT /v1/config/scoring-weights/reset restores defaults

  agent_bypass:
    description: Bypass a required agent for specific workflow executions
    method: POST /v1/execute with override.skip_agents field
    auth: admin WLT with domain:override capability
    constraints:
      - Cannot skip all agents (at least one must execute)
      - Bypassed agent categories scored as N/A in report
    audit: Logged as workflow.override with skipped agents and reason

  finding_suppress:
    description: Suppress specific finding categories from scoring
    method: PUT /v1/config/suppress-findings
    auth: admin WLT with domain:config capability
    payload:
      categories: list of finding categories to suppress
    audit: Logged with operator identity and suppressed categories

  recommendation_force:
    description: Force-approve or force-reject a recommendation
    method: PUT /v1/recommendations/{id}/status
    auth: admin WLT with domain:override capability
    audit: Logged with operator identity and reason
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    max_files_per_optimize: 50
    description: Optimization workflows limited to 50 files per execution
    reason: Prevent unbounded file modifications

  forbidden_actions:
    - action: delete_files
      description: Content domain never deletes files
    - action: modify_non_html
      description: Content domain only modifies HTML files
    - action: external_requests
      description: Content domain does not make external HTTP requests;
                   agents perform all external I/O

  rate_limits:
    max_workflows_per_hour: 20
    max_agent_dispatches_per_minute: 30
    description: Prevent resource exhaustion from rapid workflow requests

  data_boundaries:
    max_file_size: 10MB
    max_files_per_audit: 500
    description: Upper bounds on input data size
```

---

## Strategy Alignment

| Strategy Metric | Domain Workflow | Measurement |
|----------------|-----------------|-------------|
| content_score | content-audit | Weighted composite from scoring table |
| readability_avg | content-audit | Average Flesch-Kincaid across pages |
| metadata_coverage | content-audit | % of pages with title + description + OG |
| pages_optimized | content-optimize | Count of successfully changed files |
| score_improvement | content-optimize | Before/after delta on content_score |

---

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, workflow fails with partial results. |
| Agent timeout | Cancel timed-out phase, continue with available results if non-blocking. Log warning. |
| Agent error response | Record error in findings. Continue workflow if other phases are independent. |
| All agents unavailable | Domain status → offline. Reject new workflows with 503. |
| Aggregation conflict | Apply conflict resolution rules (see Aggregation Rules). |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_score | gauge | Latest domain score (0–100) |
| domain_findings_total | counter | Findings by category and severity |

---

## Security

```yaml
security:
  data_classification:
    input_files: internal
    reports: internal
    observations: internal
    recommendations: internal
    description: All content domain data is classified as internal.
                 No PII is processed or stored.

  access_control:
    workflow_execution:
      required_capability: domain:execute
      auth: WLT token verification
    config_override:
      required_capability: domain:config
      auth: WLT with admin scope
    workflow_history:
      required_capability: domain:read
      auth: WLT token verification
    agent_dispatch:
      method: Signed message envelope with domain's Ed25519 key
      verification: Target agent verifies signature

  network:
    inbound: orchestrator and admin only via WLT-authenticated requests
    outbound: agent dispatch via localhost message bus only
    no_external: true
    description: Content domain has no external network access

  secrets:
    private_key:
      storage: .weblisk/keys/content/private.key
      permissions: 0600
      rotation: manual via key-rotation procedure
```

---

## Test Fixtures

```yaml
test_fixtures:
  - name: content_audit_happy_path
    description: Full content-audit workflow with both agents returning results
    input:
      action: audit
      payload:
        files: ["test/fixtures/good-page.html", "test/fixtures/needs-work.html"]
    mock_agents:
      content-analyzer:
        status: success
        output:
          readability_score: 78
          structure_score: 85
          findings: [{category: readability, severity: medium, title: "Long sentences detected"}]
      meta-checker:
        status: success
        output:
          metadata_score: 92
          findings: [{category: metadata, severity: low, title: "Description could be longer"}]
    expected:
      status: completed
      score_range: [75, 90]
      finding_count_min: 2
      recommendations_generated: true

  - name: content_audit_agent_timeout
    description: content-analyzer times out, workflow completes with partial results
    input:
      action: audit
      payload:
        files: ["test/fixtures/slow-page.html"]
    mock_agents:
      content-analyzer:
        status: timeout
        after_ms: 130000
      meta-checker:
        status: success
        output:
          metadata_score: 88
          findings: []
    expected:
      status: partial
      readability_score: null
      structure_score: null
      metadata_score: 88

  - name: content_optimize_happy_path
    description: Apply approved recommendations and verify improvement
    input:
      action: optimize
      payload:
        files: ["test/fixtures/needs-work.html"]
        approved_recommendations: [{id: "rec-001", category: metadata}]
        original_scores: {content_score: 65}
    mock_agents:
      content-analyzer:
        status: success
        output:
          readability_score: 82
          structure_score: 85
    expected:
      status: completed
      score_after_gt: 65
      feedback_entries_min: 1

  - name: content_audit_all_agents_down
    description: Both agents unavailable, workflow rejected
    input:
      action: audit
      payload:
        files: ["test/fixtures/good-page.html"]
    mock_agents:
      content-analyzer:
        status: unavailable
      meta-checker:
        status: unavailable
    expected:
      status: rejected
      error_code: DOMAIN_OFFLINE

  - name: content_audit_conflict_resolution
    description: Both agents flag same element with different severities
    input:
      action: audit
      payload:
        files: ["test/fixtures/conflict-page.html"]
    mock_agents:
      content-analyzer:
        status: success
        output:
          findings: [{category: metadata, severity: medium, target: "index.html", element: "title"}]
      meta-checker:
        status: success
        output:
          findings: [{category: metadata, severity: high, target: "index.html", element: "title"}]
    expected:
      status: completed
      deduplicated_findings: 1
      winning_severity: high
      winning_agent: meta-checker
```

---

## Scaling

```yaml
scaling:
  model: single-instance
  description: >
    Content domain controllers are designed as single-instance
    processes. Each Weblisk server runs one content domain controller
    that coordinates its local content-analyzer and meta-checker agents.

  concurrency:
    max_concurrent_workflows: config.max_concurrent_workflows (default 2)
    workflow_queueing: FIFO when at capacity
    agent_dispatch: parallel within phases, sequential across phases

  horizontal:
    supported: false
    reason: >
      Domain controllers maintain local state (observations,
      recommendations) and coordinate local agents. Horizontal
      scaling is achieved at the hub level — each hub runs its
      own content domain controller.

  vertical:
    memory: ~50MB baseline + ~2MB per concurrent workflow
    cpu: Low — mostly I/O-bound (waiting for agent responses)
    storage: Grows with observation_retention_days setting
```

---

## Implementation Notes

- Scoring weight validation: verify weights sum to 1.0 on startup and
  after any config override. Reject invalid weight combinations.
- Phase timeout enforcement: each agent dispatch carries an explicit
  timeout. The domain controller is responsible for cancelling
  timed-out dispatches and recording the timeout in workflow results.
- Conflict resolution is deterministic: agent specificity is defined
  by category ownership (meta-checker owns metadata, content-analyzer
  owns readability/structure/links). Document the mapping clearly.
- Observation deduplication uses (target + element) as the natural key.
  When the same element is observed multiple times, the latest
  observation replaces the previous one within the same report.
- The optimize workflow requires explicit approval — never auto-apply
  changes. The governance pattern enforces this gate.
- Backup files use ISO 8601 timestamps in filenames for easy sorting
  and retention management.

---

## Verification Checklist

- [ ] Domain registers with orchestrator and receives WLT token
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] content-audit workflow executes all phases in correct dependency order
- [ ] analyze and metadata phases run in parallel
- [ ] content-optimize workflow rejects unapproved recommendations
- [ ] Scoring formula produces 0–100 clamped result
- [ ] Conflict resolution applies domain-specific rules
- [ ] Observations feed into lifecycle store
- [ ] Workflow history is queryable via workflow_history action
- [ ] Metrics emit for all workflow executions and agent dispatches

Port: 9701