<!-- blueprint
type: domain
kind: domain
name: health
version: 1.1.0
port: 9702
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/contract, patterns/scope, patterns/policy, patterns/safety, patterns/approval, patterns/governance, patterns/security]
depends_on: []
platform: any
tier: free
-->

# Health Domain Controller

The health domain controller owns the site health monitoring business
function. It coordinates uptime checks, performance audits, SSL
certificate validation, DNS resolution, and availability reporting
across all monitored endpoints.

This domain does NOT perform health checks itself. It directs agents
that do: the [uptime-checker](../agents/uptime-checker.md) for
endpoint availability, TLS, and DNS checks, and the
[perf-auditor](../agents/perf-auditor.md) for page performance
metrics and Core Web Vitals.

---

## Overview

The health domain controller provides continuous site reliability
monitoring by orchestrating uptime checks and performance audits across
all configured endpoints. It dispatches scheduled and on-demand health
checks to the uptime-checker and perf-auditor agents, aggregates their
results into scored health reports with trend analysis, and feeds
observations into the lifecycle store for long-term regression detection
and federation health advertisement.

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
  - agent: uptime-checker
    required: true
    description: HTTP availability, response time, TLS certificate validation, DNS resolution
  - agent: perf-auditor
    required: true
    description: Page load performance, Core Web Vitals, resource analysis
```

---

## Domain Manifest

```json
{
  "name": "health",
  "type": "domain",
  "version": "1.0.0",
  "description": "Site health — uptime, performance, TLS, DNS monitoring",
  "url": "http://localhost:9702",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "endpoints", "type": "endpoint_list", "description": "URLs and hosts to monitor"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated health report with scores and trends"}
  ],
  "collaborators": [],
  "approval": "auto",
  "required_agents": ["uptime-checker", "perf-auditor"],
  "workflows": ["health-check", "health-report"]
}
```

---

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| uptime-checker | HTTP availability, response time, TLS certificate validation, DNS resolution | availability, tls-check phases |
| perf-auditor | Page load performance, Core Web Vitals, resource analysis | performance phases |

---

## Workflows

### health-check

Scheduled health check (default: every 5 minutes). Lightweight
availability-focused check for all monitored endpoints.

Trigger: `schedule: */5 * * * *` or `task.action = "check"`

```yaml
workflow: health-check
phases:
  - name: discover
    agent: self
    action: resolve_endpoints
    input:
      config: $config.endpoints
    output: endpoint_list
    timeout: 10

  - name: availability
    agent: uptime-checker
    action: check
    input:
      endpoints: $phases.discover.output.endpoints
    output: uptime_results
    depends_on: [discover]
    timeout: 30

  - name: evaluate
    agent: self
    action: evaluate_thresholds
    input:
      results: $phases.availability.output
    output: evaluations
    depends_on: [availability]

  - name: alert
    agent: self
    action: process_alerts
    input:
      evaluations: $phases.evaluate.output
    output: alert_actions
    depends_on: [evaluate]

  - name: record
    agent: self
    action: store_results
    input:
      results: $phases.availability.output
      evaluations: $phases.evaluate.output
    output: stored
    depends_on: [evaluate]
```

Phase dependency: discover → availability → evaluate → alert + record (parallel)

### health-report

Deep health report with performance data and trend analysis. Runs on
schedule (daily) or on demand.

Trigger: `schedule: 0 6 * * *` or `task.action = "report"`

```yaml
workflow: health-report
phases:
  - name: discover
    agent: self
    action: resolve_endpoints
    input:
      config: $config.endpoints
    output: endpoint_list
    timeout: 10

  - name: availability
    agent: uptime-checker
    action: check
    input:
      endpoints: $phases.discover.output.endpoints
    output: uptime_results
    depends_on: [discover]
    timeout: 60

  - name: tls-check
    agent: uptime-checker
    action: check_tls
    input:
      hosts: $phases.discover.output.hosts
    output: tls_results
    depends_on: [discover]
    timeout: 30

  - name: performance
    agent: perf-auditor
    action: audit
    input:
      urls: $phases.discover.output.page_urls
    output: perf_results
    depends_on: [discover]
    timeout: 120

  - name: trends
    agent: self
    action: analyze_trends
    input:
      current_uptime: $phases.availability.output
      current_perf: $phases.performance.output
    output: trend_data
    depends_on: [availability, performance]

  - name: score
    agent: self
    action: calculate_health_score
    input:
      uptime: $phases.availability.output
      tls: $phases.tls-check.output
      performance: $phases.performance.output
      trends: $phases.trends.output
    output: health_score
    depends_on: [trends, tls-check]

  - name: observe
    agent: self
    action: record_observations
    input:
      score: $phases.score.output
      trends: $phases.trends.output
    output: observations
    depends_on: [score]

  - name: report
    agent: self
    action: compile_report
    input:
      uptime: $phases.availability.output
      tls: $phases.tls-check.output
      performance: $phases.performance.output
      trends: $phases.trends.output
      score: $phases.score.output
    output: domain_report
    depends_on: [observe]
```

Phase dependency: discover → availability + tls-check + performance (parallel) → trends → score → observe → report

---

## Configuration

```yaml
config:
  availability_weight:
    type: float
    default: 0.40
    env: WL_HEALTH_AVAILABILITY_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for availability component in health score

  response_time_weight:
    type: float
    default: 0.25
    env: WL_HEALTH_RESPONSE_TIME_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for response time component in health score

  tls_weight:
    type: float
    default: 0.15
    env: WL_HEALTH_TLS_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for TLS health component in health score

  performance_weight:
    type: float
    default: 0.20
    env: WL_HEALTH_PERFORMANCE_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for performance component in health score

  check_interval:
    type: int
    default: 300
    env: WL_HEALTH_CHECK_INTERVAL
    min: 60
    max: 3600
    unit: seconds
    description: Interval between scheduled health-check workflows

  workflow_timeout:
    type: int
    default: 180
    env: WL_HEALTH_WORKFLOW_TIMEOUT
    min: 30
    max: 600
    unit: seconds
    description: Maximum wall-clock time for a single workflow execution

  agent_dispatch_timeout:
    type: int
    default: 60
    env: WL_HEALTH_AGENT_DISPATCH_TIMEOUT
    min: 10
    max: 300
    unit: seconds
    description: Default timeout per agent dispatch

  max_concurrent_workflows:
    type: int
    default: 3
    env: WL_HEALTH_MAX_CONCURRENT_WORKFLOWS
    min: 1
    max: 10
    description: Maximum concurrent workflow executions

  observation_retention_days:
    type: int
    default: 90
    env: WL_HEALTH_OBSERVATION_RETENTION_DAYS
    min: 7
    max: 365
    unit: days
    description: Observation storage retention period

  regression_threshold:
    type: float
    default: 10.0
    env: WL_HEALTH_REGRESSION_THRESHOLD
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
  HealthDomainResult:
    description: Aggregated domain report for site health
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
        const: health
        description: Domain name
      score:
        type: float
        min: 0
        max: 100
        description: Weighted health score
      availability_score:
        type: float
        min: 0
        max: 100
        description: Availability sub-score
      response_time_score:
        type: float
        min: 0
        max: 100
        description: Response time sub-score
      tls_score:
        type: float
        min: 0
        max: 100
        description: TLS health sub-score
      performance_score:
        type: float
        min: 0
        max: 100
        description: Performance sub-score
      endpoints_monitored:
        type: int
        min: 0
        description: Number of endpoints checked
      endpoints_healthy:
        type: int
        min: 0
        description: Number of healthy endpoints
      created_at:
        type: int64
        auto: true
        description: Report creation timestamp

  HealthWorkflowResult:
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

  HealthObservation:
    description: Lifecycle observation for trend tracking
    fields:
      observation_id:
        type: string
        format: uuid-v7
        description: Unique observation identifier
      report_id:
        type: string
        format: uuid-v7
        references: HealthDomainResult.report_id
        description: Parent report
      target:
        type: string
        description: Endpoint URL or host observed
      element:
        type: string
        description: What was measured (e.g., response_time, tls_expiry)
      measurement:
        type: float
        description: Measured value
      unit:
        type: string
        optional: true
        description: Measurement unit (ms, percent, days)
      timestamp:
        type: int64
        auto: true
        description: Observation timestamp

  HealthMetric:
    description: Time-series health metric for trend windows
    fields:
      metric_id:
        type: string
        format: uuid-v7
        description: Unique metric identifier
      endpoint:
        type: string
        description: Endpoint URL or host
      metric_name:
        type: string
        enum: [availability, response_time_ms, tls_days_remaining, perf_score, health_score]
        description: Metric type
      value:
        type: float
        description: Metric value
      timestamp:
        type: int64
        auto: true
        description: Metric recording timestamp
```

---

## Storage

Storage tables reference the Types section. Fields are not redefined
here — the `source_type` key links each table to its type definition.

```yaml
storage:
  engine: sqlite

  tables:
    health_reports:
      source_type: HealthDomainResult
      primary_key: report_id
      indexes:
        - name: idx_report_workflow
          fields: [workflow_id]
          type: btree
        - name: idx_report_created
          fields: [created_at]
          type: btree
          description: Time-ordered report lookup

    health_workflow_results:
      source_type: HealthWorkflowResult
      primary_key: result_id
      indexes:
        - name: idx_wfresult_workflow
          fields: [workflow_id]
          type: btree

    health_observations:
      source_type: HealthObservation
      primary_key: observation_id
      indexes:
        - name: idx_obs_report
          fields: [report_id]
          type: btree
        - name: idx_obs_target
          fields: [target, element, timestamp]
          type: btree
          description: Trend query by target and element

    health_metrics:
      source_type: HealthMetric
      primary_key: metric_id
      indexes:
        - name: idx_metric_endpoint
          fields: [endpoint, metric_name, timestamp]
          type: btree
          description: Time-series lookup per endpoint and metric
        - name: idx_metric_timestamp
          fields: [timestamp]
          type: btree
          description: Global time-ordered cleanup

  relationships:
    - name: report_observations
      from: health_observations.report_id
      to: health_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Observations belong to a report

    - name: report_workflow_results
      from: health_workflow_results.workflow_id
      to: health_reports.workflow_id
      cardinality: many-to-one
      on_delete: cascade
      description: Phase results belong to a workflow/report

  retention:
    health_reports:
      policy: config.observation_retention_days
      cleanup: daily sweep deletes reports older than retention
    health_observations:
      policy: config.observation_retention_days
      cleanup: daily sweep
    health_metrics:
      policy: config.observation_retention_days
      cleanup: daily sweep
    health_workflow_results:
      policy: cascades from health_reports

  backup:
    health_reports:
      frequency: daily
      format: JSON export
      path: .weblisk/backups/health/reports_{ISO8601}.json
    health_metrics:
      frequency: daily
      format: JSON export (last 24 hours)
      path: .weblisk/backups/health/metrics_{ISO8601}.json
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
        validates: uptime-checker and perf-auditor respond to health
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
        validates: at least uptime-checker available for health-check
      - from: running
        to: completed
        trigger: all_phases_done
        validates: report phase output is valid HealthDomainResult
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/health/
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
  Action:      Query orchestrator for uptime-checker, perf-auditor
  Pre-check:   Step 4 validated (registered)
  Validates:   Both agents registered and responding to health
  On Fail:     Enter degraded state — health-check can still run
               with cached results; health-report requires perf-auditor
  Backout:     None

Step 6 — Subscribe to Events
  Action:      Subscribe to: system.agent.registered,
               system.agent.deregistered, system.shutdown,
               domain.health.task, system.blueprint.changed
  Pre-check:   Step 4 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial, deregister, EXIT
  Backout:     Unsubscribe all, deregister, close storage

Step 7 — Register Scheduled Checks
  Action:      Register health-check cron (config.check_interval) and
               health-report cron (daily 06:00) with cron agent
  Pre-check:   Step 4 validated
  Validates:   Cron registrations acknowledged
  On Fail:     Log warning, continue — on-demand workflows still work

Final:
  domain_state → online (or degraded if agents unavailable)
  Log: lifecycle.ready {port: 9702, agents: {uptime-checker: up|down, perf-auditor: up|down}}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API shutdown
  domain_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new workflow requests

Step 3 — Cancel Scheduled Checks
  Action:      Deregister cron tasks for health-check and health-report

Step 4 — Drain In-Flight Workflows
  Action:      Wait for running workflows to complete (up to 60s)
  On Timeout:  Mark running workflows as failed with partial results

Step 5 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges removal

Step 6 — Close Storage
  Action:      Close database connection

Step 7 — Exit
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
      details: {agents: {uptime-checker: up, perf-auditor: up},
                storage: connected, in_flight: N, last_check: timestamp}

  degraded:
    conditions:
      - one or more required agents unavailable
      - or storage errors (retrying)
      - or using stale/cached results
    response:
      status: degraded
      details: {reason, unavailable_agents, last_error, stale_since}

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
        - task.action in ["check", "report"]
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
    - cron: "*/5 * * * *"
      action: execute_workflow
      payload: {action: "check"}
      description: Scheduled health check every 5 minutes

    - cron: "0 6 * * *"
      action: execute_workflow
      payload: {action: "report"}
      description: Daily deep health report at 06:00

    - cron: "0 3 * * *"
      action: retention_cleanup
      description: Daily cleanup of expired observations and metrics
```

---

## Actions

Domain actions are formalized from the message handler table below.
See [Domain HandleMessage Actions](#domain-handlemessage-actions) for
the complete action reference with input/output specifications.

```yaml
actions:
  execute_workflow:
    source: [orchestrator, cron]
    input: TaskRequest
    output: TaskResult
    description: Route task to appropriate workflow based on task.action

  resolve_endpoints:
    source: [internal]
    input: EndpointConfig
    output: EndpointList
    description: Load and resolve endpoint configuration

  evaluate_thresholds:
    source: [internal]
    input: UptimeResults
    output: ThresholdEvaluations
    description: Compare results against warning/critical thresholds

  process_alerts:
    source: [internal]
    input: ThresholdEvaluations
    output: AlertActions
    description: Generate alert events for threshold violations

  store_results:
    source: [internal]
    input: {results: UptimeResults, evaluations: ThresholdEvaluations}
    output: StoredResults
    description: Persist check results for trend analysis

  analyze_trends:
    source: [internal]
    input: {current_uptime: UptimeResults, current_perf: PerfResults}
    output: TrendData
    description: Compare current vs. historical (24h, 7d, 30d windows)

  calculate_health_score:
    source: [internal]
    input: {uptime: UptimeResults, tls: TlsResults, performance: PerfResults, trends: TrendData}
    output: HealthScore
    description: Weighted composite score from all checks

  record_observations:
    source: [internal]
    input: {score: HealthScore, trends: TrendData}
    output: ObservationList
    description: Feed results into lifecycle observation store

  compile_report:
    source: [internal]
    input: AllPhaseOutputs
    output: HealthDomainReport
    description: Build comprehensive health report

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
| resolve_endpoints | Internal | Load endpoint configuration and resolve targets |
| evaluate_thresholds | Internal | Compare results against warning/critical thresholds |
| process_alerts | Internal | Generate alert events for threshold violations |
| store_results | Internal | Persist check results for trend analysis |
| analyze_trends | Internal | Compare current vs. historical (24h, 7d, 30d windows) |
| calculate_health_score | Internal | Weighted composite score from all checks |
| record_observations | Internal | Feed results into lifecycle as observations |
| compile_report | Internal | Build HealthDomainReport with all data |
| get_status | Orchestrator/Admin | Domain health and agent availability |
| get_workflows | Orchestrator/Admin | Available workflow definitions |
| workflow_history | Admin | Recent workflow executions with results |

---

## Aggregation

Aggregation combines results from uptime-checker and perf-auditor
into a unified health assessment. See [Aggregation Rules](#aggregation-rules)
for the complete merge and conflict resolution logic.

## Aggregation Rules

1. Merge uptime results: group by endpoint, latest result wins
2. Merge TLS results: group by host, flag any degraded certificates
3. Merge performance results: group by URL, median of metrics
4. Resolve conflicts: when uptime-checker and perf-auditor disagree
   on endpoint health (e.g., HTTP 200 but terrible performance),
   the lower score wins — conservative health assessment
5. Score calculation uses weighted formula above

---

## Scoring

| Component | Weight | Source Agent |
|-----------|--------|-------------|
| Availability | 40% | uptime-checker |
| Response time | 25% | uptime-checker |
| TLS health | 15% | uptime-checker |
| Performance | 20% | perf-auditor |

Health score = (availability × 0.40) + (response_time × 0.25) + (tls × 0.15) + (performance × 0.20), clamped 0–100.

### Score Ranges

| Range | Status | Federation Advertisement |
|-------|--------|------------------------|
| 90–100 | Excellent | healthy |
| 80–89 | Good | healthy |
| 50–79 | Degraded | degraded |
| 0–49 | Unhealthy | unhealthy |

---

## Feedback Loop

The health domain tracks endpoint reliability trends through a
continuous observation cycle.

```yaml
feedback_loop:
  observation:
    trigger: Every health-check or health-report workflow completion
    action: Record HealthObservation and HealthMetric entries per endpoint
    store: health_observations and health_metrics tables
    retention: config.observation_retention_days

  trend_detection:
    trigger: health-report workflow analyze_trends phase
    action: Compare current metrics against 24h, 7d, 30d rolling windows
    threshold: config.regression_threshold (default 10%)
    produces: Trend alerts when regression detected

  alerting:
    trigger: Threshold violation or trend regression
    action: Emit domain.health.alert event with severity and context
    escalation:
      - warning: score drop 5-10% in 24h window
      - critical: score drop >10% in 24h window or endpoint down

  federation:
    trigger: health-report workflow completes
    action: Update hub health advertisement for federation peers
    data: {status, score, uptime_30d, last_check, endpoints_monitored, endpoints_healthy}
```

---

## Trend Analysis

The health domain maintains rolling windows for trend comparison:

| Window | Purpose |
|--------|---------|
| 24 hours | Short-term regression detection |
| 7 days | Weekly pattern recognition |
| 30 days | Long-term trend identification |

Trend data is stored in the domain's local storage and used for
lifecycle observations. Significant regressions (>10% score drop
within 24h) trigger automatic alerts.

---

## Federation Health Advertisement

The health domain advertises hub health status to federation peers
as part of the hub's public profile:

```json
{
  "hub_health": {
    "status": "healthy",
    "score": 94,
    "uptime_30d": 99.97,
    "last_check": "2026-04-25T10:00:00Z",
    "endpoints_monitored": 12,
    "endpoints_healthy": 12
  }
}
```

Federation peers use this to make routing and trust decisions.

---

## Collaboration

```yaml
collaboration:
  publishes:
    - event: domain.health.report.completed
      payload: {report_id, domain, score, endpoints_monitored, endpoints_healthy}
      consumers: [orchestrator, lifecycle, hub]
      description: Emitted when a health-report workflow completes

    - event: domain.health.check.completed
      payload: {report_id, score, endpoints_checked, alerts_generated}
      consumers: [orchestrator]
      description: Emitted when a health-check workflow completes

    - event: domain.health.alert
      payload: {severity, endpoint, metric, threshold, current_value}
      consumers: [alerting, hub]
      description: Emitted when threshold violations or regressions detected

    - event: domain.health.federation
      payload: {status, score, uptime_30d, last_check}
      consumers: [hub, federation]
      description: Updated hub health advertisement for federation

  subscribes:
    - event: system.agent.registered
      handler: on_agent_registered
      description: Track uptime-checker and perf-auditor availability

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
    failure_mode: use cached results if agent unrecoverable
```

---

## Manual Overrides

```yaml
manual_overrides:
  scoring_weights:
    description: Override default health scoring weights at runtime
    method: PUT /v1/config/scoring-weights
    auth: admin WLT with domain:config capability
    payload:
      availability_weight: float (0.0-1.0)
      response_time_weight: float (0.0-1.0)
      tls_weight: float (0.0-1.0)
      performance_weight: float (0.0-1.0)
    validation: Weights must sum to 1.0 (±0.01 tolerance)
    audit: Logged as config.override with before/after values and operator identity
    revert: PUT /v1/config/scoring-weights/reset restores defaults

  agent_bypass:
    description: Bypass perf-auditor for lightweight checks
    method: POST /v1/execute with override.skip_agents field
    auth: admin WLT with domain:override capability
    constraints:
      - Cannot skip uptime-checker (required for all health workflows)
      - Bypassed agent components scored as N/A in report
    audit: Logged as workflow.override with skipped agents and reason

  threshold_override:
    description: Override alert thresholds for specific endpoints
    method: PUT /v1/config/thresholds/{endpoint}
    auth: admin WLT with domain:config capability
    payload:
      warning_threshold: float
      critical_threshold: float
    audit: Logged with operator identity and endpoint

  endpoint_suppress:
    description: Temporarily suppress monitoring for specific endpoints
    method: PUT /v1/config/suppress-endpoints
    auth: admin WLT with domain:config capability
    payload:
      endpoints: list of endpoint URLs to suppress
      duration: int (seconds, 0 = indefinite)
    audit: Logged with operator identity and suppressed endpoints
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    max_endpoints_per_check: 100
    description: Health checks limited to 100 endpoints per execution
    reason: Prevent agent overload from large endpoint lists

  forbidden_actions:
    - action: modify_endpoints
      description: Health domain is read-only; it monitors but never modifies
    - action: external_write
      description: Health domain does not write to external systems
    - action: active_probing
      description: Only passive checks; no penetration testing or active vulnerability scanning

  rate_limits:
    max_checks_per_hour: 60
    max_reports_per_hour: 5
    max_agent_dispatches_per_minute: 30
    description: Prevent excessive monitoring load

  data_boundaries:
    max_response_body_stored: 1KB
    max_endpoints_monitored: 500
    description: Upper bounds on stored data per check
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, use last known results with staleness warning. |
| Agent timeout | Use last known results for timed-out checks. Flag as stale in report. |
| DNS resolution failure | Mark endpoint as unreachable. Generate critical alert. |
| All agents unavailable | Domain status → offline. Continue using cached results. Generate critical alert. |
| Storage failure | Continue checking (results are transient). Log error. Alert on persistence loss. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_health_score | gauge | Latest health score (0–100) |
| domain_endpoint_status | gauge | Per-endpoint status (1=healthy, 0.5=degraded, 0=down) |
| domain_check_total | counter | Health checks by result status |
| domain_alert_total | counter | Alerts generated by severity |

---

## Security

```yaml
security:
  data_classification:
    check_results: internal
    reports: internal
    metrics: internal
    endpoint_config: internal
    description: All health domain data is classified as internal.
                 Endpoint URLs may be sensitive (internal infrastructure).

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
    description: Health domain has no direct external network access;
                 agents perform all external checks

  secrets:
    private_key:
      storage: .weblisk/keys/health/private.key
      permissions: 0600
      rotation: manual via key-rotation procedure
```

---

## Test Fixtures

```yaml
test_fixtures:
  - name: health_check_happy_path
    description: Scheduled health-check with all endpoints healthy
    input:
      action: check
      payload:
        endpoints: ["https://example.com", "https://api.example.com"]
    mock_agents:
      uptime-checker:
        status: success
        output:
          endpoints:
            - url: "https://example.com"
              status: 200
              response_time_ms: 145
            - url: "https://api.example.com"
              status: 200
              response_time_ms: 89
    expected:
      status: completed
      endpoints_healthy: 2
      alerts_generated: 0

  - name: health_report_with_degraded_endpoint
    description: Deep health report with one endpoint showing degraded performance
    input:
      action: report
      payload:
        endpoints: ["https://example.com", "https://slow.example.com"]
    mock_agents:
      uptime-checker:
        status: success
        output:
          endpoints:
            - url: "https://example.com"
              status: 200
              response_time_ms: 120
            - url: "https://slow.example.com"
              status: 200
              response_time_ms: 4500
          tls:
            - host: "example.com"
              valid: true
              days_remaining: 245
      perf-auditor:
        status: success
        output:
          pages:
            - url: "https://example.com"
              lcp_ms: 1200
              cls: 0.05
            - url: "https://slow.example.com"
              lcp_ms: 8500
              cls: 0.32
    expected:
      status: completed
      score_range: [50, 80]
      alerts_generated_min: 1

  - name: health_check_agent_timeout
    description: uptime-checker times out, use cached results
    input:
      action: check
      payload:
        endpoints: ["https://example.com"]
    mock_agents:
      uptime-checker:
        status: timeout
        after_ms: 35000
    expected:
      status: partial
      stale_results: true

  - name: health_check_endpoint_down
    description: Endpoint returns 503, critical alert generated
    input:
      action: check
      payload:
        endpoints: ["https://down.example.com"]
    mock_agents:
      uptime-checker:
        status: success
        output:
          endpoints:
            - url: "https://down.example.com"
              status: 503
              response_time_ms: 45
    expected:
      status: completed
      endpoints_healthy: 0
      alert_severity: critical
```

---

## Scaling

```yaml
scaling:
  model: single-instance
  description: >
    Health domain controllers are designed as single-instance processes.
    Each Weblisk server runs one health domain controller that
    coordinates its local uptime-checker and perf-auditor agents.

  concurrency:
    max_concurrent_workflows: config.max_concurrent_workflows (default 3)
    workflow_queueing: FIFO when at capacity
    agent_dispatch: parallel within phases, sequential across phases
    note: health-check and health-report can run concurrently

  horizontal:
    supported: false
    reason: >
      Domain controllers maintain local state (metrics, observations)
      and coordinate local agents. Horizontal scaling is achieved
      at the hub level — each hub runs its own health domain controller.

  vertical:
    memory: ~40MB baseline + ~1MB per concurrent workflow
    cpu: Low — mostly I/O-bound (waiting for agent responses)
    storage: Grows with observation_retention_days and endpoint count
```

---

## Implementation Notes

- Scoring weight validation: verify weights sum to 1.0 on startup and
  after any config override. Reject invalid weight combinations.
- Graceful degradation: when agents are unavailable, the health domain
  continues using cached/stale results rather than failing completely.
  Reports flag stale data clearly.
- Trend windows (24h, 7d, 30d) are computed from the health_metrics
  table using time-range queries. Index on (endpoint, metric_name,
  timestamp) is critical for performance.
- Federation health advertisement updates on every health-report
  completion. The hub advertises the latest score and uptime percentage.
- Cron registration happens at startup. If the cron agent is unavailable,
  the health domain logs a warning but remains operational for on-demand
  checks.
- Conservative conflict resolution: when uptime says healthy but perf
  says degraded, always take the worse assessment.

---

## Verification Checklist

- [ ] Domain registers with orchestrator and receives WLT token
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] health-check workflow runs on 5-minute schedule via cron agent
- [ ] health-report workflow runs on daily schedule and on-demand
- [ ] availability and performance phases run in parallel
- [ ] Scoring formula produces 0–100 clamped result
- [ ] Trend analysis compares against 24h, 7d, 30d windows
- [ ] Federation health advertisement reflects current score
- [ ] Threshold violations generate alerts via alerting agent
- [ ] Observations feed into lifecycle store
- [ ] Cached results used when agents are unavailable (graceful degradation)
- [ ] Metrics emit for all workflow executions and agent dispatches

Port: 9702