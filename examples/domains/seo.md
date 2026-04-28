<!-- blueprint
type: domain
kind: domain
name: seo
version: 1.1.0
port: 9700
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/contract, patterns/scope, patterns/policy, patterns/safety, patterns/approval, patterns/governance, patterns/security]
depends_on: []
platform: any
tier: free
-->

# SEO Domain Controller

The SEO domain controller owns the search engine optimization and web
accessibility business function. It coordinates on-page SEO analysis,
meta tag validation, structured data checking, accessibility audits,
and optimization recommendations across all monitored pages.

This domain does NOT perform analysis itself. It directs agents that
do: the [seo-analyzer](../agents/seo-analyzer.md) for on-page SEO
and meta analysis, and the [a11y-checker](../agents/a11y-checker.md)
for WCAG accessibility compliance.

---

## Overview

The SEO domain controller provides search engine optimization and
accessibility monitoring by orchestrating audits across all configured
pages. It dispatches on-demand and scheduled SEO audits to the
seo-analyzer and a11y-checker agents, aggregates their results into
scored reports with optimization recommendations, and feeds
observations into the lifecycle store for long-term trend detection
and regression alerting.

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
          request_type: AgentMessage
          response_fields: [status, response]
        - path: /v1/health
          methods: [POST]
          response_fields: [status, details]
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
        - behavior: trend-analysis
          parameters: [windows, regression_threshold]
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

  - pattern: patterns/contract
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
  - agent: seo-analyzer
    required: true
    description: On-page SEO analysis, meta tags, structured data, keyword optimization
  - agent: a11y-checker
    required: true
    description: WCAG 2.1 accessibility compliance checks
```

---

## Domain Manifest

```json
{
  "name": "seo",
  "type": "domain",
  "version": "1.0.0",
  "description": "SEO and accessibility — on-page analysis, meta tags, structured data, WCAG",
  "url": "http://localhost:9700",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "page_urls", "type": "url_list", "description": "Pages to audit for SEO and accessibility"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated SEO/a11y report with scores and recommendations"}
  ],
  "collaborators": [],
  "approval": "auto",
  "required_agents": ["seo-analyzer", "a11y-checker"],
  "workflows": ["seo-audit", "seo-optimize"]
}
```

---

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| seo-analyzer | On-page SEO analysis, meta tags, structured data, keyword optimization | seo-analysis phases |
| a11y-checker | WCAG 2.1 accessibility compliance checks | accessibility phases |

---

## Workflows

### seo-audit

Full SEO and accessibility audit. Runs both agents, aggregates into
a scored report with optimization recommendations.

Trigger: `task.action = "audit"`

```yaml
workflow: seo-audit
phases:
  - name: discover
    agent: self
    action: resolve_pages
    input:
      config: $config.page_urls
    output: page_list
    timeout: 10

  - name: seo-analysis
    agent: seo-analyzer
    action: analyze
    input:
      urls: $phases.discover.output.pages
    output: seo_results
    depends_on: [discover]
    timeout: 120

  - name: accessibility
    agent: a11y-checker
    action: check
    input:
      urls: $phases.discover.output.pages
    output: a11y_results
    depends_on: [discover]
    timeout: 120

  - name: aggregate
    agent: self
    action: aggregate_results
    input:
      seo: $phases.seo-analysis.output
      a11y: $phases.accessibility.output
    output: aggregated
    depends_on: [seo-analysis, accessibility]

  - name: score
    agent: self
    action: calculate_seo_score
    input:
      aggregated: $phases.aggregate.output
    output: scored
    depends_on: [aggregate]

  - name: recommend
    agent: self
    action: generate_recommendations
    input:
      scored: $phases.score.output
    output: recommendations
    depends_on: [score]

  - name: observe
    agent: self
    action: record_observations
    input:
      scored: $phases.score.output
      recommendations: $phases.recommend.output
    output: observations
    depends_on: [recommend]

  - name: report
    agent: self
    action: compile_report
    input:
      seo: $phases.seo-analysis.output
      a11y: $phases.accessibility.output
      scored: $phases.score.output
      recommendations: $phases.recommend.output
      observations: $phases.observe.output
    output: domain_report
    depends_on: [observe]
```

Phase dependency: discover → seo-analysis + accessibility (parallel) → aggregate → score → recommend → observe → report

### seo-optimize

Targeted optimization check. Runs after recommendations are applied
to measure improvement. Compares current results against previous
audit.

Trigger: `task.action = "optimize"`

```yaml
workflow: seo-optimize
phases:
  - name: discover
    agent: self
    action: resolve_pages
    input:
      config: $config.page_urls
    output: page_list
    timeout: 10

  - name: seo-analysis
    agent: seo-analyzer
    action: analyze
    input:
      urls: $phases.discover.output.pages
    output: seo_results
    depends_on: [discover]
    timeout: 120

  - name: accessibility
    agent: a11y-checker
    action: check
    input:
      urls: $phases.discover.output.pages
    output: a11y_results
    depends_on: [discover]
    timeout: 120

  - name: score
    agent: self
    action: calculate_seo_score
    input:
      seo: $phases.seo-analysis.output
      a11y: $phases.accessibility.output
    output: scored
    depends_on: [seo-analysis, accessibility]

  - name: compare
    agent: self
    action: compare_with_previous
    input:
      current: $phases.score.output
    output: comparison
    depends_on: [score]

  - name: measure
    agent: self
    action: measure_recommendation_impact
    input:
      comparison: $phases.compare.output
    output: feedback
    depends_on: [compare]
```

Phase dependency: discover → seo-analysis + accessibility (parallel) → score → compare → measure

---

## Configuration

```yaml
config:
  meta_weight:
    type: float
    default: 0.30
    env: WL_SEO_META_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for meta tags / on-page SEO in overall score

  structure_weight:
    type: float
    default: 0.25
    env: WL_SEO_STRUCTURE_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for page structure (headings, semantics) in score

  accessibility_weight:
    type: float
    default: 0.25
    env: WL_SEO_ACCESSIBILITY_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for WCAG accessibility in overall score

  structured_data_weight:
    type: float
    default: 0.20
    env: WL_SEO_STRUCTURED_DATA_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for JSON-LD/schema.org data in overall score

  workflow_timeout:
    type: int
    default: 300
    env: WL_SEO_WORKFLOW_TIMEOUT
    min: 60
    max: 900
    unit: seconds
    description: Maximum wall-clock time for a single workflow execution

  agent_dispatch_timeout:
    type: int
    default: 120
    env: WL_SEO_AGENT_DISPATCH_TIMEOUT
    min: 30
    max: 600
    unit: seconds
    description: Default timeout per agent dispatch

  max_concurrent_workflows:
    type: int
    default: 2
    env: WL_SEO_MAX_CONCURRENT_WORKFLOWS
    min: 1
    max: 5
    description: Maximum concurrent workflow executions

  observation_retention_days:
    type: int
    default: 90
    env: WL_SEO_OBSERVATION_RETENTION_DAYS
    min: 7
    max: 365
    unit: days
    description: Observation storage retention period

  regression_threshold:
    type: float
    default: 10.0
    env: WL_SEO_REGRESSION_THRESHOLD
    min: 1.0
    max: 50.0
    unit: percent
    description: Score drop percentage that triggers automatic alert
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  SeoDomainResult:
    description: Aggregated domain report for SEO and accessibility
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
        const: seo
        description: Domain name
      score:
        type: float
        min: 0
        max: 100
        description: Weighted SEO/a11y score
      meta_score:
        type: float
        min: 0
        max: 100
        description: Meta tags / on-page SEO sub-score
      structure_score:
        type: float
        min: 0
        max: 100
        description: Page structure sub-score
      accessibility_score:
        type: float
        min: 0
        max: 100
        description: WCAG accessibility sub-score
      structured_data_score:
        type: float
        min: 0
        max: 100
        description: Structured data sub-score
      pages_audited:
        type: int
        min: 0
        description: Number of pages checked
      total_findings:
        type: int
        min: 0
        description: Total findings count
      total_recommendations:
        type: int
        min: 0
        description: Recommendations generated
      created_at:
        type: int64
        auto: true
        description: Report creation timestamp

  SeoWorkflowResult:
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

  SeoFinding:
    description: A single SEO or accessibility finding
    fields:
      finding_id:
        type: string
        format: uuid-v7
        description: Unique finding identifier
      report_id:
        type: string
        format: uuid-v7
        references: SeoDomainResult.report_id
        description: Parent report
      category:
        type: string
        enum: [meta, structure, accessibility, structured_data]
        description: Finding category
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Finding severity
      target:
        type: string
        description: Page URL
      element:
        type: string
        optional: true
        description: Specific element (tag, heading, aria attribute)
      title:
        type: string
        max: 256
        description: Short finding description
      description:
        type: text
        optional: true
        description: Detailed explanation
      wcag_criterion:
        type: string
        optional: true
        description: WCAG success criterion (e.g., 1.1.1, 2.4.1)
      created_at:
        type: int64
        auto: true
        description: Finding creation timestamp

  SeoObservation:
    description: Lifecycle observation for trend tracking
    fields:
      observation_id:
        type: string
        format: uuid-v7
        description: Unique observation identifier
      report_id:
        type: string
        format: uuid-v7
        references: SeoDomainResult.report_id
        description: Parent report
      target:
        type: string
        description: Page URL observed
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

  SeoRecommendation:
    description: Prioritized optimization recommendation
    fields:
      recommendation_id:
        type: string
        format: uuid-v7
        description: Unique recommendation identifier
      report_id:
        type: string
        format: uuid-v7
        references: SeoDomainResult.report_id
        description: Parent report
      category:
        type: string
        enum: [meta, structure, accessibility, structured_data]
        description: Recommendation category
      priority:
        type: string
        enum: [critical, high, medium, low]
        description: Implementation priority
      title:
        type: string
        max: 256
        description: Short recommendation title
      description:
        type: text
        description: Detailed recommendation with steps
      impact:
        type: string
        enum: [high, medium, low]
        description: Expected impact on score
      effort:
        type: string
        enum: [trivial, small, medium, large]
        description: Estimated implementation effort
      target:
        type: string
        description: Page URL this recommendation applies to
      status:
        type: string
        enum: [pending, approved, rejected, implemented, measured]
        default: pending
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
    seo_reports:
      source_type: SeoDomainResult
      primary_key: report_id
      indexes:
        - name: idx_report_workflow
          fields: [workflow_id]
          type: btree
        - name: idx_report_created
          fields: [created_at]
          type: btree
          description: Time-ordered report lookup

    seo_workflow_results:
      source_type: SeoWorkflowResult
      primary_key: result_id
      indexes:
        - name: idx_wfresult_workflow
          fields: [workflow_id]
          type: btree

    seo_findings:
      source_type: SeoFinding
      primary_key: finding_id
      indexes:
        - name: idx_finding_report
          fields: [report_id]
          type: btree
        - name: idx_finding_severity
          fields: [severity, category]
          type: btree
          description: Severity-first lookup for prioritization
        - name: idx_finding_wcag
          fields: [wcag_criterion]
          type: btree
          description: WCAG criterion lookup

    seo_observations:
      source_type: SeoObservation
      primary_key: observation_id
      indexes:
        - name: idx_obs_report
          fields: [report_id]
          type: btree
        - name: idx_obs_target
          fields: [target, element, timestamp]
          type: btree
          description: Trend query by page URL and element

    seo_recommendations:
      source_type: SeoRecommendation
      primary_key: recommendation_id
      indexes:
        - name: idx_rec_report
          fields: [report_id]
          type: btree
        - name: idx_rec_status
          fields: [status, priority]
          type: btree
          description: Active recommendation lookup

  relationships:
    - name: report_findings
      from: seo_findings.report_id
      to: seo_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Findings belong to a report

    - name: report_observations
      from: seo_observations.report_id
      to: seo_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Observations belong to a report

    - name: report_recommendations
      from: seo_recommendations.report_id
      to: seo_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Recommendations belong to a report

    - name: report_workflow_results
      from: seo_workflow_results.workflow_id
      to: seo_reports.workflow_id
      cardinality: many-to-one
      on_delete: cascade
      description: Phase results belong to a workflow/report

  retention:
    seo_reports:
      policy: config.observation_retention_days
      cleanup: daily sweep deletes reports older than retention
    seo_findings:
      policy: cascades from seo_reports
    seo_observations:
      policy: config.observation_retention_days
      cleanup: daily sweep
    seo_recommendations:
      policy: retained until measured or rejected, then 30 days
    seo_workflow_results:
      policy: cascades from seo_reports

  backup:
    seo_reports:
      frequency: daily
      format: JSON export
      path: .weblisk/backups/seo/reports_{ISO8601}.json
    seo_recommendations:
      frequency: daily
      format: JSON export (pending and approved only)
      path: .weblisk/backups/seo/recommendations_{ISO8601}.json
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
        validates: seo-analyzer and a11y-checker respond to health
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
        validates: both agents respond to health
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
        validates: at least one agent available
      - from: running
        to: completed
        trigger: all_phases_done
        validates: report phase output is valid SeoDomainResult
      - from: running
        to: failed
        trigger: critical_phase_error
        validates: non-recoverable error in required phase
      - from: running
        to: partial
        trigger: non_critical_phase_error
        validates: one agent failed but other succeeded
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/seo/
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
  Action:      Query orchestrator for seo-analyzer, a11y-checker
  Pre-check:   Step 4 validated (registered)
  Validates:   Both agents registered and responding to health
  On Fail:     Enter degraded state — seo-audit runs partial
               (SEO-only or a11y-only depending on which agent is up)
  Backout:     None

Step 6 — Subscribe to Events
  Action:      Subscribe to: system.agent.registered,
               system.agent.deregistered, system.shutdown,
               domain.seo.task, system.blueprint.changed
  Pre-check:   Step 4 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial, deregister, EXIT
  Backout:     Unsubscribe all, deregister, close storage

Final:
  domain_state → online (or degraded if agents unavailable)
  Log: lifecycle.ready {port: 9700, agents: {seo-analyzer: up|down, a11y-checker: up|down}}
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

Reported via `POST /v1/health`:

```yaml
health:
  online:
    conditions:
      - all required agents available
      - storage connected
      - in_flight_workflows < max_concurrent_workflows
    response:
      status: online
      details: {agents: {seo-analyzer: up, a11y-checker: up},
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
      response: HealthStatus

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
    - cron: "0 3 * * *"
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

  resolve_pages:
    source: [internal]
    input: PageConfig
    output: PageList
    description: Load and resolve page URL configuration

  aggregate_results:
    source: [internal]
    input: {seo: SeoResults, a11y: A11yResults}
    output: AggregatedResults
    description: Combine SEO and accessibility results

  calculate_seo_score:
    source: [internal]
    input: AggregatedResults
    output: ScoredResults
    description: Weighted composite from scoring formula

  generate_recommendations:
    source: [internal]
    input: ScoredResults
    output: RecommendationList
    description: Prioritize findings into optimization steps

  record_observations:
    source: [internal]
    input: {scored: ScoredResults, recommendations: RecommendationList}
    output: ObservationList
    description: Feed results into lifecycle observation store

  compile_report:
    source: [internal]
    input: AllPhaseOutputs
    output: SeoDomainReport
    description: Build comprehensive SEO/a11y report

  compare_with_previous:
    source: [internal]
    input: CurrentScore
    output: Comparison
    description: Compare current results against most recent audit

  measure_recommendation_impact:
    source: [internal]
    input: Comparison
    output: FeedbackList
    description: Measure impact of implemented recommendations

  get_status:
    source: [orchestrator, admin]
    input: null
    output: HealthStatus
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
| resolve_pages | Internal | Load and resolve page URL configuration |
| aggregate_results | Internal | Combine SEO and accessibility results |
| calculate_seo_score | Internal | Weighted composite from scoring formula |
| generate_recommendations | Internal | Prioritize findings into optimization steps |
| record_observations | Internal | Feed results into lifecycle as observations |
| compile_report | Internal | Build SeoDomainReport with all data |
| compare_with_previous | Internal | Compare current vs. previous audit results |
| measure_recommendation_impact | Internal | Measure recommendation effectiveness |
| get_status | Orchestrator/Admin | Domain health and agent availability |
| get_workflows | Orchestrator/Admin | Available workflow definitions |
| workflow_history | Admin | Recent workflow executions with results |

---

## Scoring

| Component | Weight | Source Agent |
|-----------|--------|-------------|
| Meta / On-page SEO | 30% | seo-analyzer |
| Page Structure | 25% | seo-analyzer |
| Accessibility (WCAG) | 25% | a11y-checker |
| Structured Data | 20% | seo-analyzer |

SEO score = (meta × 0.30) + (structure × 0.25) + (accessibility × 0.25) + (structured_data × 0.20), clamped 0–100.

### Score Ranges

| Range | Grade | Description |
|-------|-------|-------------|
| 90–100 | Excellent | Well-optimized, WCAG compliant |
| 75–89 | Good | Minor optimization opportunities |
| 50–74 | Needs Work | Significant SEO or accessibility gaps |
| 0–49 | Poor | Major issues requiring immediate attention |

---

## Aggregation

Aggregation combines results from seo-analyzer and a11y-checker into
a unified assessment. See [Aggregation Rules](#aggregation-rules) for
the complete merge and conflict resolution logic.

## Aggregation Rules

1. Merge SEO findings: group by page URL and finding category
2. Merge a11y findings: group by page URL and WCAG criterion
3. Deduplicate overlapping findings (e.g., missing alt text found
   by both agents): keep the more specific finding, merge context
4. Prioritize by impact: critical accessibility issues take priority
   over low-severity SEO optimizations
5. Generate cross-domain recommendations when findings from both
   agents indicate related issues (e.g., heading structure affects
   both SEO and a11y)

---

## Strategy Alignment

The SEO domain integrates with the broader Weblisk strategy:

- **Quality signals**: SEO scores feed into content quality assessment
- **Accessibility compliance**: WCAG results inform regulatory compliance
- **Performance correlation**: SEO insights complement health domain
  performance data
- **Content optimization**: Recommendations drive content improvement cycles

---

## Feedback Loop

The SEO domain tracks optimization effectiveness through a continuous
recommendation-measurement cycle.

```yaml
feedback_loop:
  observation:
    trigger: seo-audit workflow completes
    action: Record SeoObservation entries for each audited page
    store: seo_observations table
    retention: config.observation_retention_days

  recommendation_lifecycle:
    trigger: recommendations generated in seo-audit
    action: Store SeoRecommendation with pending status
    states: pending → approved → implemented → measured
    store: seo_recommendations table

  impact_measurement:
    trigger: seo-optimize workflow compares current vs. previous
    action: Match implemented recommendations to score changes
    produces: Feedback entries with metric_before/metric_after
    scoring: Recommendations that improved score are marked effective

  trend_detection:
    trigger: observation comparison across audits
    action: Compare current scores against 7d and 30d averages
    threshold: config.regression_threshold (default 10%)
    produces: Alerts when score regresses below threshold

  learning:
    trigger: Accumulated feedback data
    action: Reorder recommendation priorities based on measured impact
    effect: High-impact recommendations promoted in future audits
```

---

## Collaboration

```yaml
collaboration:
  publishes:
    - event: domain.seo.report.completed
      payload: {report_id, domain, score, pages_audited, total_findings, total_recommendations}
      consumers: [orchestrator, lifecycle, hub]
      description: Emitted when a seo-audit workflow completes

    - event: domain.seo.optimize.completed
      payload: {report_id, score_before, score_after, recommendations_measured}
      consumers: [orchestrator, lifecycle]
      description: Emitted when a seo-optimize workflow completes

    - event: domain.seo.alert
      payload: {severity, category, message, target}
      consumers: [alerting, hub]
      description: Emitted when significant SEO or a11y regressions detected

  subscribes:
    - event: system.agent.registered
      handler: on_agent_registered
      description: Track seo-analyzer and a11y-checker availability

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
    failure_mode: use partial results if one agent unrecoverable
```

---

## Manual Overrides

```yaml
manual_overrides:
  scoring_weights:
    description: Override default SEO scoring weights at runtime
    method: PUT /v1/config/scoring-weights
    auth: admin WLT with domain:config capability
    payload:
      meta_weight: float (0.0-1.0)
      structure_weight: float (0.0-1.0)
      accessibility_weight: float (0.0-1.0)
      structured_data_weight: float (0.0-1.0)
    validation: Weights must sum to 1.0 (±0.01 tolerance)
    audit: Logged as config.override with before/after values and operator identity
    revert: PUT /v1/config/scoring-weights/reset restores defaults

  agent_bypass:
    description: Bypass a11y-checker for SEO-only audits
    method: POST /v1/execute with override.skip_agents field
    auth: admin WLT with domain:override capability
    constraints:
      - Cannot skip seo-analyzer (required for all SEO workflows)
      - Bypassed agent components scored as N/A in report
    audit: Logged as workflow.override with skipped agents and reason

  recommendation_override:
    description: Approve or reject recommendations manually
    method: PUT /v1/recommendations/{id}/status
    auth: admin WLT with domain:config capability
    payload:
      status: approved | rejected
      reason: string
    audit: Logged with operator identity and recommendation ID
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    max_pages_per_audit: 200
    description: Audit workflows limited to 200 pages per execution
    reason: Prevent agent overload from large site crawls

  forbidden_actions:
    - action: modify_content
      description: SEO domain is read-only; it analyzes but never modifies pages
    - action: submit_sitemap
      description: SEO domain does not submit sitemaps to search engines
    - action: external_api_write
      description: Domain does not write to external APIs or services

  rate_limits:
    max_audits_per_hour: 10
    max_optimize_per_hour: 20
    max_agent_dispatches_per_minute: 20
    description: Prevent excessive scanning load

  data_boundaries:
    max_page_content_stored: 10KB
    max_findings_per_report: 2000
    description: Upper bounds on stored data per audit
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If seo-analyzer down, run a11y-only partial audit (and vice versa). |
| Agent timeout | Cancel timed-out analysis phase. Continue with available results. Mark missing category as N/A. |
| Both agents unavailable | Domain status → offline. Reject new workflows with 503. |
| Page unreachable | Mark page as unreachable in findings. Continue auditing other pages. |
| Storage failure | Continue auditing (results are transient). Log error. Alert on persistence loss. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_seo_score | gauge | Latest SEO score (0–100) |
| domain_pages_audited | counter | Pages audited by workflow |
| domain_findings_total | counter | Findings by category and severity |
| domain_recommendations_total | counter | Recommendations by status and priority |
| domain_recommendation_effectiveness | gauge | Percentage of recommendations that improved scores |

---

## Security

```yaml
security:
  data_classification:
    audit_results: internal
    findings: internal
    recommendations: internal
    page_content: internal
    description: All SEO domain data is classified as internal.
                 Page content excerpts may contain sensitive data.

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
    recommendation_management:
      required_capability: domain:config
      auth: WLT with admin scope
    agent_dispatch:
      method: Signed message envelope with domain's Ed25519 key
      verification: Target agent verifies signature

  network:
    inbound: orchestrator and admin only via WLT-authenticated requests
    outbound: agent dispatch via localhost message bus only
    no_external: true
    description: SEO domain has no direct external network access;
                 agents perform all page fetching and analysis

  secrets:
    private_key:
      storage: .weblisk/keys/seo/private.key
      permissions: 0600
      rotation: manual via key-rotation procedure
```

---

## Test Fixtures

```yaml
test_fixtures:
  - name: seo_audit_happy_path
    description: Full SEO audit with both agents returning results
    input:
      action: audit
      payload:
        page_urls: ["https://example.com", "https://example.com/about"]
    mock_agents:
      seo-analyzer:
        status: success
        output:
          pages:
            - url: "https://example.com"
              meta_score: 85
              structure_score: 90
              structured_data_score: 70
              findings: [{category: meta, severity: medium, title: "Description too short"}]
            - url: "https://example.com/about"
              meta_score: 92
              structure_score: 88
              structured_data_score: 80
              findings: []
      a11y-checker:
        status: success
        output:
          pages:
            - url: "https://example.com"
              accessibility_score: 78
              findings: [{category: accessibility, severity: high, wcag_criterion: "1.1.1", title: "Missing alt text on hero image"}]
            - url: "https://example.com/about"
              accessibility_score: 95
              findings: []
    expected:
      status: completed
      score_range: [75, 90]
      total_findings: 2
      recommendations_min: 1

  - name: seo_audit_a11y_agent_down
    description: a11y-checker unavailable, SEO-only partial audit
    input:
      action: audit
      payload:
        page_urls: ["https://example.com"]
    mock_agents:
      seo-analyzer:
        status: success
        output:
          pages:
            - url: "https://example.com"
              meta_score: 85
              structure_score: 90
              structured_data_score: 70
      a11y-checker:
        status: unavailable
    expected:
      status: partial
      accessibility_score: null
      categories_completed: [meta, structure, structured_data]

  - name: seo_optimize_improvement_measured
    description: Optimization check shows score improvement
    input:
      action: optimize
      payload:
        page_urls: ["https://example.com"]
    mock_agents:
      seo-analyzer:
        status: success
        output:
          pages:
            - url: "https://example.com"
              meta_score: 95
              structure_score: 92
              structured_data_score: 88
      a11y-checker:
        status: success
        output:
          pages:
            - url: "https://example.com"
              accessibility_score: 90
    mock_previous:
      score: 72
    expected:
      status: completed
      score_improved: true
      score_delta_min: 10

  - name: seo_audit_all_pages_unreachable
    description: All pages return errors, findings generated per page
    input:
      action: audit
      payload:
        page_urls: ["https://down.example.com"]
    mock_agents:
      seo-analyzer:
        status: success
        output:
          pages:
            - url: "https://down.example.com"
              error: "Connection refused"
      a11y-checker:
        status: success
        output:
          pages:
            - url: "https://down.example.com"
              error: "Connection refused"
    expected:
      status: completed
      score: 0
      findings_include: "Page unreachable"
```

---

## Scaling

```yaml
scaling:
  model: single-instance
  description: >
    SEO domain controllers are designed as single-instance processes.
    Each Weblisk server runs one SEO domain controller that
    coordinates its local seo-analyzer and a11y-checker agents.

  concurrency:
    max_concurrent_workflows: config.max_concurrent_workflows (default 2)
    workflow_queueing: FIFO when at capacity
    agent_dispatch: parallel within phases (SEO + a11y), sequential across phases

  horizontal:
    supported: false
    reason: >
      Domain controllers maintain local state (findings, observations,
      recommendations) and coordinate local agents. Horizontal scaling
      is achieved at the hub level — each hub runs its own SEO
      domain controller.

  vertical:
    memory: ~50MB baseline + ~3MB per concurrent workflow
    cpu: Low — mostly I/O-bound (waiting for agent responses)
    storage: Grows with observation_retention_days and page count;
             recommendations retained longer than observations
```

---

## Implementation Notes

- Scoring weight validation: verify weights sum to 1.0 on startup and
  after any config override. Reject invalid weight combinations.
- Recommendation lifecycle: recommendations track from pending through
  approved/rejected to implemented and measured. The seo-optimize
  workflow closes the loop by measuring impact.
- WCAG criterion tracking: accessibility findings link to specific
  WCAG success criteria (e.g., 1.1.1 for images, 2.4.1 for bypass
  blocks). This enables filtering and compliance reporting.
- Cross-agent deduplication: when both agents find the same issue
  (e.g., missing alt text impacts both SEO and a11y), keep the
  finding with more context and merge metadata from both.
- Partial audits: when one agent is unavailable, the domain runs a
  partial audit with the available agent rather than failing entirely.
  Missing categories are clearly marked as N/A in the report.
- Recommendation prioritization considers both severity and estimated
  effort. Quick wins (high impact, low effort) are promoted.

---

## Port Assignment

SEO domain controller uses port 9700. This is the first domain
controller in the Weblisk port range (9700–9799).

---

## Verification Checklist

- [ ] Domain registers with orchestrator and receives WLT token
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] seo-audit workflow runs both agents in parallel
- [ ] seo-optimize workflow compares against previous audit
- [ ] Scoring formula produces 0–100 clamped result matching weight table
- [ ] Partial audits work when one agent is unavailable
- [ ] Recommendations track through full lifecycle (pending → measured)
- [ ] Feedback loop measures recommendation effectiveness
- [ ] Observations feed into lifecycle store
- [ ] WCAG criterion linked to accessibility findings
- [ ] Cross-agent finding deduplication works correctly
- [ ] Metrics emit for all workflow executions and agent dispatches

Port: 9700