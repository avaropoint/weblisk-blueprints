<!-- blueprint
type: domain
kind: domain
name: security
version: 1.1.0
port: 9703
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/contract, patterns/scope, patterns/policy, patterns/safety, patterns/approval, patterns/governance, patterns/security]
depends_on: []
platform: any
tier: free
-->

# Security Domain Controller

The security domain controller owns the web application security
business function. It coordinates passive security scanning, OWASP
Top 10 analysis, dependency vulnerability auditing, CSP validation,
and security header checks across all monitored sites and applications.

This domain does NOT perform security scans itself. It directs the
[security-scanner](../agents/security-scanner.md) agent, which
performs all scan operations and returns structured findings.

---

## Overview

The security domain controller orchestrates web application security
assessment by dispatching passive scans to the security-scanner agent.
It coordinates header analysis, CSP validation, dependency vulnerability
auditing, and OWASP Top 10 static checks, then aggregates findings into
scored reports with prioritized remediation recommendations. The domain
supports full audits, quick header-only checks, and isolated dependency
scans as separate workflows.

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
  - agent: security-scanner
    required: true
    description: HTTP header analysis, CSP parsing, dependency CVE lookup, OWASP static checks
```

---

## Domain Manifest

```json
{
  "name": "security",
  "type": "domain",
  "version": "1.0.0",
  "description": "Web application security — OWASP, CSP, headers, dependency auditing",
  "url": "http://localhost:9703",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "target_urls", "type": "url_list", "description": "URLs to scan"},
    {"name": "dependency_files", "type": "file_list", "description": "Package manifests to audit"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated security report with scored findings"}
  ],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["security-scanner"],
  "workflows": ["security-audit", "security-headers-check", "dependency-audit"]
}
```

---

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| security-scanner | HTTP header analysis, CSP parsing, dependency CVE lookup, OWASP static checks, behavioral fingerprint | All scan phases |

---

## Workflows

### security-audit

Full security audit. Runs all scan types, aggregates into a scored
report with prioritized findings and remediation recommendations.

Trigger: `task.action = "audit"`

```yaml
workflow: security-audit
phases:
  - name: headers
    agent: security-scanner
    action: scan-headers
    input:
      urls: $task.payload.urls
    output: header_results
    timeout: 60

  - name: csp
    agent: security-scanner
    action: scan-csp
    input:
      urls: $task.payload.urls
    output: csp_results
    timeout: 60

  - name: dependencies
    agent: security-scanner
    action: scan-dependencies
    input:
      files: $task.payload.dependency_files
    output: dep_results
    timeout: 120

  - name: owasp
    agent: security-scanner
    action: scan-owasp
    input:
      urls: $task.payload.urls
    output: owasp_results
    timeout: 180

  - name: aggregate
    agent: self
    action: aggregate_results
    input:
      headers: $phases.headers.output
      csp: $phases.csp.output
      dependencies: $phases.dependencies.output
      owasp: $phases.owasp.output
    output: aggregated
    depends_on: [headers, csp, dependencies, owasp]

  - name: score
    agent: self
    action: calculate_security_score
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
      scored: $phases.score.output
      recommendations: $phases.recommend.output
      observations: $phases.observe.output
    output: domain_report
    depends_on: [observe]
```

Phase dependency: headers + csp + dependencies + owasp (parallel) → aggregate → score → recommend → observe → report

### security-headers-check

Quick headers-only scan. Lightweight check suitable for frequent
scheduling.

Trigger: `task.action = "check-headers"`

```yaml
workflow: security-headers-check
phases:
  - name: headers
    agent: security-scanner
    action: scan-headers
    input:
      urls: $task.payload.urls
    output: header_results
    timeout: 60

  - name: evaluate
    agent: self
    action: evaluate_headers
    input:
      results: $phases.headers.output
    output: evaluation
    depends_on: [headers]
```

### dependency-audit

Dependency-only vulnerability check. Scans package manifests against
vulnerability databases.

Trigger: `task.action = "audit-dependencies"`

```yaml
workflow: dependency-audit
phases:
  - name: scan
    agent: security-scanner
    action: scan-dependencies
    input:
      files: $task.payload.dependency_files
    output: dep_results
    timeout: 120

  - name: evaluate
    agent: self
    action: evaluate_dependencies
    input:
      results: $phases.scan.output
    output: evaluation
    depends_on: [scan]
```

---

## Configuration

```yaml
config:
  headers_weight:
    type: float
    default: 0.25
    env: WL_SECURITY_HEADERS_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for HTTP headers component in security score

  csp_weight:
    type: float
    default: 0.20
    env: WL_SECURITY_CSP_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for CSP component in security score

  dependencies_weight:
    type: float
    default: 0.25
    env: WL_SECURITY_DEPENDENCIES_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for dependency audit component in security score

  owasp_weight:
    type: float
    default: 0.30
    env: WL_SECURITY_OWASP_WEIGHT
    min: 0.0
    max: 1.0
    description: Weight for OWASP checks component in security score

  workflow_timeout:
    type: int
    default: 600
    env: WL_SECURITY_WORKFLOW_TIMEOUT
    min: 60
    max: 1800
    unit: seconds
    description: Maximum wall-clock time for a single workflow execution

  agent_dispatch_timeout:
    type: int
    default: 180
    env: WL_SECURITY_AGENT_DISPATCH_TIMEOUT
    min: 30
    max: 600
    unit: seconds
    description: Default timeout per agent dispatch

  max_concurrent_workflows:
    type: int
    default: 2
    env: WL_SECURITY_MAX_CONCURRENT_WORKFLOWS
    min: 1
    max: 5
    description: Maximum concurrent workflow executions

  observation_retention_days:
    type: int
    default: 180
    env: WL_SECURITY_OBSERVATION_RETENTION_DAYS
    min: 30
    max: 730
    unit: days
    description: Security observation retention (longer than other domains)

  finding_severity_threshold:
    type: string
    default: low
    env: WL_SECURITY_FINDING_SEVERITY_THRESHOLD
    enum: [info, low, medium, high, critical]
    description: Minimum severity for findings included in recommendations
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  SecurityDomainResult:
    description: Aggregated domain report for security assessment
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
        const: security
        description: Domain name
      score:
        type: float
        min: 0
        max: 100
        description: Weighted security score
      headers_score:
        type: float
        min: 0
        max: 100
        description: HTTP headers sub-score
      csp_score:
        type: float
        min: 0
        max: 100
        description: CSP sub-score
      dependencies_score:
        type: float
        min: 0
        max: 100
        description: Dependency audit sub-score
      owasp_score:
        type: float
        min: 0
        max: 100
        description: OWASP checks sub-score
      grade:
        type: string
        enum: [Excellent, Good, Fair, Poor, Critical]
        description: Human-readable security grade
      urls_scanned:
        type: int
        min: 0
        description: Number of URLs scanned
      total_findings:
        type: int
        min: 0
        description: Total findings count
      critical_findings:
        type: int
        min: 0
        description: Critical severity finding count
      cve_count:
        type: int
        min: 0
        description: Known CVEs found in dependencies
      created_at:
        type: int64
        auto: true
        description: Report creation timestamp

  SecurityWorkflowResult:
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

  SecurityFinding:
    description: A single security finding
    fields:
      finding_id:
        type: string
        format: uuid-v7
        description: Unique finding identifier
      report_id:
        type: string
        format: uuid-v7
        references: SecurityDomainResult.report_id
        description: Parent report
      category:
        type: string
        enum: [headers, csp, dependencies, owasp]
        description: Finding category
      owasp_id:
        type: string
        optional: true
        description: OWASP category ID (e.g., A01, A02)
      severity:
        type: string
        enum: [critical, high, medium, low, info]
        description: Finding severity
      target:
        type: string
        description: URL, host, or package
      element:
        type: string
        optional: true
        description: Specific element (header name, directive, package)
      title:
        type: string
        max: 256
        description: Short finding description
      description:
        type: text
        optional: true
        description: Detailed explanation
      cve_id:
        type: string
        optional: true
        description: CVE identifier for dependency findings
      cvss_score:
        type: float
        optional: true
        min: 0
        max: 10
        description: CVSS score for dependency findings
      created_at:
        type: int64
        auto: true
        description: Finding creation timestamp

  SecurityObservation:
    description: Lifecycle observation for trend tracking
    fields:
      observation_id:
        type: string
        format: uuid-v7
        description: Unique observation identifier
      report_id:
        type: string
        format: uuid-v7
        references: SecurityDomainResult.report_id
        description: Parent report
      target:
        type: string
        description: URL or package observed
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
```

---

## Storage

Storage tables reference the Types section. Fields are not redefined
here — the `source_type` key links each table to its type definition.

```yaml
storage:
  engine: sqlite

  tables:
    security_reports:
      source_type: SecurityDomainResult
      primary_key: report_id
      indexes:
        - name: idx_report_workflow
          fields: [workflow_id]
          type: btree
        - name: idx_report_created
          fields: [created_at]
          type: btree
          description: Time-ordered report lookup

    security_workflow_results:
      source_type: SecurityWorkflowResult
      primary_key: result_id
      indexes:
        - name: idx_wfresult_workflow
          fields: [workflow_id]
          type: btree

    security_findings:
      source_type: SecurityFinding
      primary_key: finding_id
      indexes:
        - name: idx_finding_report
          fields: [report_id]
          type: btree
        - name: idx_finding_severity
          fields: [severity, category]
          type: btree
          description: Severity-first lookup for prioritization
        - name: idx_finding_cve
          fields: [cve_id]
          type: btree
          description: CVE lookup for dependency findings
        - name: idx_finding_owasp
          fields: [owasp_id]
          type: btree

    security_observations:
      source_type: SecurityObservation
      primary_key: observation_id
      indexes:
        - name: idx_obs_report
          fields: [report_id]
          type: btree
        - name: idx_obs_target
          fields: [target, element, timestamp]
          type: btree
          description: Trend query by target and element

  relationships:
    - name: report_findings
      from: security_findings.report_id
      to: security_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Findings belong to a report

    - name: report_observations
      from: security_observations.report_id
      to: security_reports.report_id
      cardinality: many-to-one
      on_delete: cascade
      description: Observations belong to a report

    - name: report_workflow_results
      from: security_workflow_results.workflow_id
      to: security_reports.workflow_id
      cardinality: many-to-one
      on_delete: cascade
      description: Phase results belong to a workflow/report

  retention:
    security_reports:
      policy: config.observation_retention_days
      cleanup: daily sweep deletes reports older than retention
    security_findings:
      policy: cascades from security_reports
    security_observations:
      policy: config.observation_retention_days
      cleanup: daily sweep
    security_workflow_results:
      policy: cascades from security_reports

  backup:
    security_reports:
      frequency: daily
      format: JSON export
      path: .weblisk/backups/security/reports_{ISO8601}.json
    security_findings:
      frequency: daily
      format: JSON export (critical and high only)
      path: .weblisk/backups/security/findings_{ISO8601}.json
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
        validates: security-scanner responds to health
      - from: registered
        to: degraded
        trigger: agent_unavailable
        validates: security-scanner not responding
      - from: online
        to: degraded
        trigger: agent_unavailable
        validates: health check failure on security-scanner
      - from: degraded
        to: online
        trigger: agent_recovered
        validates: security-scanner responds to health
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
        validates: security-scanner available
      - from: running
        to: completed
        trigger: all_phases_done
        validates: report phase output is valid SecurityDomainResult
      - from: running
        to: failed
        trigger: critical_phase_error
        validates: non-recoverable error in required phase
      - from: running
        to: partial
        trigger: non_critical_phase_error
        validates: some scan phases failed but others succeeded
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
  Action:      Generate or load Ed25519 keypair from .weblisk/keys/security/
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
  Action:      Query orchestrator for security-scanner
  Pre-check:   Step 4 validated (registered)
  Validates:   security-scanner registered and responding to health
  On Fail:     Enter degraded state — cannot execute workflows
  Backout:     None

Step 6 — Subscribe to Events
  Action:      Subscribe to: system.agent.registered,
               system.agent.deregistered, system.shutdown,
               domain.security.task, system.blueprint.changed
  Pre-check:   Step 4 validated
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial, deregister, EXIT
  Backout:     Unsubscribe all, deregister, close storage

Final:
  domain_state → online (or degraded if security-scanner unavailable)
  Log: lifecycle.ready {port: 9703, agents: {security-scanner: up|down}}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API shutdown
  domain_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new workflow requests

Step 3 — Drain In-Flight Workflows
  Action:      Wait for running workflows to complete (up to 90s)
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
      - security-scanner available
      - storage connected
      - in_flight_workflows < max_concurrent_workflows
    response:
      status: online
      details: {agents: {security-scanner: up},
                storage: connected, in_flight: N}

  degraded:
    conditions:
      - security-scanner unavailable
      - or storage errors (retrying)
    response:
      status: degraded
      details: {reason, last_error}

  offline:
    conditions:
      - security-scanner unavailable and no cached results
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
        - task.action in ["audit", "check-headers", "audit-dependencies"]
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
      description: Update security-scanner availability

    - topic: system.agent.deregistered
      handler: on_agent_deregistered
      description: Update domain status when security-scanner goes offline

    - topic: system.shutdown
      handler: on_shutdown
      description: Begin graceful shutdown sequence

    - topic: system.blueprint.changed
      handler: on_blueprint_changed
      description: Handle blueprint version changes

  schedule:
    - cron: "0 4 * * *"
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
    input: {headers: ScanResult, csp: ScanResult, dependencies: ScanResult, owasp: ScanResult}
    output: AggregatedResults
    description: Combine all scan type outputs

  calculate_security_score:
    source: [internal]
    input: AggregatedResults
    output: ScoredResults
    description: Weighted composite from scoring formula

  generate_recommendations:
    source: [internal]
    input: ScoredResults
    output: RecommendationList
    description: Prioritize findings into remediation steps

  record_observations:
    source: [internal]
    input: {scored: ScoredResults, recommendations: RecommendationList}
    output: ObservationList
    description: Feed results into lifecycle observation store

  evaluate_headers:
    source: [internal]
    input: HeaderScanResults
    output: HeaderEvaluation
    description: Quick header compliance check

  evaluate_dependencies:
    source: [internal]
    input: DependencyScanResults
    output: DependencyEvaluation
    description: Dependency vulnerability assessment

  compile_report:
    source: [internal]
    input: AllPhaseOutputs
    output: SecurityDomainReport
    description: Build comprehensive security report

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
| aggregate_results | Internal | Combine all scan type outputs |
| calculate_security_score | Internal | Weighted composite from scoring formula |
| generate_recommendations | Internal | Prioritize findings into remediation steps |
| record_observations | Internal | Feed results into lifecycle as observations |
| evaluate_headers | Internal | Quick header compliance check |
| evaluate_dependencies | Internal | Dependency vulnerability assessment |
| compile_report | Internal | Build SecurityDomainReport |
| get_status | Orchestrator/Admin | Domain health and agent availability |
| get_workflows | Orchestrator/Admin | Available workflow definitions |
| workflow_history | Admin | Recent workflow executions with results |

---

## Aggregation

Aggregation combines results from the four scan types into a unified
security assessment. See [Aggregation Rules](#aggregation-rules) for
the complete merge and conflict resolution logic.

## Aggregation Rules

1. Merge findings: deduplicate by (check_type + target + element)
2. Sort by severity (critical → high → medium → low → info)
3. Group by OWASP category where applicable
4. Resolve conflicts: when the same issue is found by multiple scan
   types (e.g., headers scan and OWASP scan both flag missing HSTS),
   keep the more specific finding and merge context from both
5. Dependency findings include CVE IDs and CVSS scores when available

---

## Scoring

| Category | Weight | Source |
|----------|--------|--------|
| HTTP Headers | 25% | scan-headers |
| CSP | 20% | scan-csp |
| Dependencies | 25% | scan-dependencies |
| OWASP | 30% | scan-owasp |

Security score = (headers × 0.25) + (csp × 0.20) + (deps × 0.25) + (owasp × 0.30), clamped 0–100.

### Score Ranges

| Range | Grade | Description |
|-------|-------|-------------|
| 90–100 | Excellent | No critical or high findings |
| 75–89 | Good | Minor issues, no critical findings |
| 50–74 | Fair | Significant issues requiring attention |
| 25–49 | Poor | Critical issues present |
| 0–24 | Critical | Multiple critical vulnerabilities |

---

## HTTP Headers Checks

| Header | Expected | Severity if Missing |
|--------|----------|-------------------|
| Strict-Transport-Security | max-age≥31536000; includeSubDomains | High |
| X-Content-Type-Options | nosniff | Medium |
| X-Frame-Options | DENY or SAMEORIGIN | Medium |
| Content-Security-Policy | Present, no unsafe-inline in script-src | High |
| Referrer-Policy | strict-origin-when-cross-origin or stricter | Low |
| Permissions-Policy | Present | Low |
| Cross-Origin-Opener-Policy | same-origin | Medium |
| Cross-Origin-Resource-Policy | same-origin or same-site | Medium |

---

## CSP Validation Rules

| Rule | Severity |
|------|----------|
| No `unsafe-inline` in `script-src` | Critical |
| No `unsafe-eval` in `script-src` | Critical |
| No wildcard `*` in `script-src` | High |
| `default-src` is set | High |
| No `data:` in `script-src` | High |
| `frame-ancestors` is set | Medium |
| `base-uri` is restricted | Medium |
| `form-action` is restricted | Low |

---

## Dependency Audit

Supported package manifest formats:

| File | Ecosystem |
|------|-----------|
| package.json / package-lock.json | npm |
| go.mod / go.sum | Go |
| requirements.txt / Pipfile.lock | Python |
| Cargo.toml / Cargo.lock | Rust |

Vulnerability lookup uses the VulnDB abstract interface defined in
the security-scanner agent (local DB, OSV, GitHub Advisory, custom).

---

## OWASP Top 10 Checks

| ID | Category | Check Type |
|----|----------|------------|
| A01 | Broken Access Control | Static analysis — missing auth headers, open redirects |
| A02 | Cryptographic Failures | TLS version, cipher strength, mixed content |
| A03 | Injection | Input handling patterns, parameterized queries |
| A05 | Security Misconfiguration | Headers, default credentials, error disclosure |
| A06 | Vulnerable Components | Dependency audit cross-reference |
| A07 | Auth Failures | Session handling, password policy, brute force protection |
| A09 | Logging Failures | Security event logging presence |

A04 (Insecure Design), A08 (Software Integrity), A10 (SSRF) require
manual review or runtime analysis — flagged as "manual review required."

---

## Feedback Loop

The security domain tracks vulnerability remediation through a
continuous feedback cycle.

```yaml
feedback_loop:
  observation:
    trigger: security-audit workflow completes
    action: Record SecurityObservation entries for each scanned target
    store: security_observations table
    retention: config.observation_retention_days

  finding_tracking:
    trigger: aggregate phase produces security findings
    action: Record findings with severity, category, and CVE data
    store: security_findings table
    tracking: findings are compared across audits to detect new vs. recurring

  remediation_measurement:
    trigger: subsequent audit after remediation
    action: Compare current findings to previous audit findings
    produces: Delta report showing resolved, new, and persistent findings
    metrics:
      - metric_name: security_score
        direction: higher_is_better
      - metric_name: critical_findings
        direction: lower_is_better
      - metric_name: cve_count
        direction: lower_is_better

  regression_detection:
    trigger: score comparison across audits
    action: Alert if security score regresses significantly
    threshold: >10% score drop flags a regression alert
```

---

## Collaboration

```yaml
collaboration:
  publishes:
    - event: domain.security.report.completed
      payload: {report_id, domain, score, grade, urls_scanned, total_findings, critical_findings}
      consumers: [orchestrator, lifecycle, hub]
      description: Emitted when a security-audit workflow completes

    - event: domain.security.headers.completed
      payload: {report_id, urls_checked, findings_count}
      consumers: [orchestrator]
      description: Emitted when a headers-check workflow completes

    - event: domain.security.alert
      payload: {severity, category, owasp_id, message, target}
      consumers: [alerting, hub]
      description: Emitted when critical security findings detected

    - event: domain.security.cve.found
      payload: {cve_id, cvss_score, package, ecosystem, severity}
      consumers: [alerting, hub]
      description: Emitted when known CVE found in dependencies

  subscribes:
    - event: system.agent.registered
      handler: on_agent_registered
      description: Track security-scanner availability

    - event: system.agent.deregistered
      handler: on_agent_deregistered
      description: Update domain status when security-scanner goes offline

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
    description: Override default security scoring weights at runtime
    method: PUT /v1/config/scoring-weights
    auth: admin WLT with domain:config capability
    payload:
      headers_weight: float (0.0-1.0)
      csp_weight: float (0.0-1.0)
      dependencies_weight: float (0.0-1.0)
      owasp_weight: float (0.0-1.0)
    validation: Weights must sum to 1.0 (±0.01 tolerance)
    audit: Logged as config.override with before/after values and operator identity
    revert: PUT /v1/config/scoring-weights/reset restores defaults

  scan_bypass:
    description: Skip specific scan types for a workflow execution
    method: POST /v1/execute with override.skip_scans field
    auth: admin WLT with domain:override capability
    constraints:
      - Cannot skip all scan types (at least one must execute)
      - Skipped categories scored as N/A in report
    audit: Logged as workflow.override with skipped scans and reason

  finding_suppress:
    description: Suppress specific CVEs or finding categories from scoring
    method: PUT /v1/config/suppress-findings
    auth: admin WLT with domain:config capability
    payload:
      cve_ids: list of CVE IDs to suppress
      categories: list of finding categories to suppress
    audit: Logged with operator identity and suppressed items
    note: Suppressed findings still recorded but excluded from score
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    max_urls_per_audit: 100
    max_dependency_files_per_audit: 20
    description: Audit workflows limited to prevent agent overload

  forbidden_actions:
    - action: active_exploitation
      description: Security domain performs passive scanning only; no exploitation
    - action: modify_targets
      description: Security domain is read-only; it scans but never modifies
    - action: credential_testing
      description: No brute force or credential stuffing
    - action: external_vuln_db_write
      description: Domain only reads from vulnerability databases

  rate_limits:
    max_audits_per_hour: 10
    max_header_checks_per_hour: 30
    max_agent_dispatches_per_minute: 20
    description: Prevent excessive scanning load

  data_boundaries:
    max_response_body_stored: 4KB
    max_findings_per_report: 1000
    description: Upper bounds on stored data per audit
```

---

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, workflow fails with partial results. |
| Agent timeout | Cancel timed-out scan phase. Continue with available results. Mark missing categories in report. |
| VulnDB unavailable | Fall back to local database. Flag results as potentially incomplete. |
| Target unreachable | Mark URL as unreachable in findings. Continue scanning other targets. |
| All agents unavailable | Domain status → offline. Reject new workflows with 503. |

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_security_score | gauge | Latest security score (0–100) |
| domain_findings_total | counter | Findings by category and severity |
| domain_vulnerabilities_total | counter | Known vulnerabilities by ecosystem and severity |

---

## Security

```yaml
security:
  data_classification:
    scan_results: confidential
    findings: confidential
    cve_data: internal
    observations: internal
    description: Security findings are classified as confidential.
                 They reveal vulnerabilities that could be exploited.

  access_control:
    workflow_execution:
      required_capability: domain:execute
      auth: WLT token verification
    report_access:
      required_capability: domain:read:security
      auth: WLT with security-read scope
      note: Security reports require elevated read permission
    config_override:
      required_capability: domain:config
      auth: WLT with admin scope
    agent_dispatch:
      method: Signed message envelope with domain's Ed25519 key
      verification: Target agent verifies signature

  network:
    inbound: orchestrator and admin only via WLT-authenticated requests
    outbound: agent dispatch via localhost message bus only
    no_external: true
    description: Security domain has no direct external network access;
                 the security-scanner agent performs all external checks

  secrets:
    private_key:
      storage: .weblisk/keys/security/private.key
      permissions: 0600
      rotation: manual via key-rotation procedure

  audit_trail:
    all_scan_results: logged with trace_id
    finding_access: logged with requester identity
    config_changes: logged with before/after values
```

---

## Test Fixtures

```yaml
test_fixtures:
  - name: security_audit_happy_path
    description: Full security-audit with all scan types returning results
    input:
      action: audit
      payload:
        urls: ["https://example.com"]
        dependency_files: ["package.json"]
    mock_agents:
      security-scanner:
        scan-headers:
          status: success
          output:
            findings: [{category: headers, severity: medium, title: "Missing X-Frame-Options"}]
        scan-csp:
          status: success
          output:
            findings: [{category: csp, severity: high, title: "unsafe-inline in script-src"}]
        scan-dependencies:
          status: success
          output:
            findings: [{category: dependencies, severity: critical, cve_id: "CVE-2024-1234", cvss_score: 9.1}]
        scan-owasp:
          status: success
          output:
            findings: [{category: owasp, owasp_id: "A05", severity: medium}]
    expected:
      status: completed
      score_range: [30, 60]
      critical_findings_min: 1
      grade: Fair

  - name: security_headers_check_clean
    description: Quick headers-only check with all headers present
    input:
      action: check-headers
      payload:
        urls: ["https://secure.example.com"]
    mock_agents:
      security-scanner:
        scan-headers:
          status: success
          output:
            findings: []
    expected:
      status: completed
      finding_count: 0

  - name: security_audit_partial_timeout
    description: OWASP scan times out, other scans complete
    input:
      action: audit
      payload:
        urls: ["https://complex.example.com"]
        dependency_files: []
    mock_agents:
      security-scanner:
        scan-headers:
          status: success
          output: {findings: []}
        scan-csp:
          status: success
          output: {findings: []}
        scan-dependencies:
          status: success
          output: {findings: []}
        scan-owasp:
          status: timeout
          after_ms: 200000
    expected:
      status: partial
      owasp_score: null
      categories_completed: [headers, csp, dependencies]

  - name: dependency_audit_critical_cves
    description: Dependency-only audit finds multiple critical CVEs
    input:
      action: audit-dependencies
      payload:
        dependency_files: ["package.json", "go.mod"]
    mock_agents:
      security-scanner:
        scan-dependencies:
          status: success
          output:
            findings:
              - {category: dependencies, severity: critical, cve_id: "CVE-2024-5678", cvss_score: 9.8, element: "lodash@4.17.20"}
              - {category: dependencies, severity: critical, cve_id: "CVE-2024-9012", cvss_score: 8.5, element: "express@4.17.1"}
    expected:
      status: completed
      cve_count: 2
      alert_generated: true
```

---

## Scaling

```yaml
scaling:
  model: single-instance
  description: >
    Security domain controllers are designed as single-instance processes.
    Each Weblisk server runs one security domain controller that
    coordinates its local security-scanner agent.

  concurrency:
    max_concurrent_workflows: config.max_concurrent_workflows (default 2)
    workflow_queueing: FIFO when at capacity
    agent_dispatch: parallel within phases (all 4 scan types), sequential across phases

  horizontal:
    supported: false
    reason: >
      Domain controllers maintain local state (findings, observations)
      and coordinate local agents. Horizontal scaling is achieved
      at the hub level — each hub runs its own security domain controller.

  vertical:
    memory: ~60MB baseline + ~5MB per concurrent workflow
    cpu: Low — mostly I/O-bound (waiting for agent responses)
    storage: Grows with observation_retention_days setting;
             security uses longer retention (180 days default)
```

---

## Implementation Notes

- Scoring weight validation: verify weights sum to 1.0 on startup and
  after any config override. Reject invalid weight combinations.
- Security findings are classified as confidential. Access to reports
  requires elevated `domain:read:security` capability, not just
  `domain:read`.
- CVE deduplication: when the same CVE appears in multiple dependency
  files, record it once but note all affected packages.
- OWASP category mapping: findings are tagged with OWASP IDs (A01-A10)
  when applicable. Some findings map to multiple categories; use the
  primary category for scoring.
- Longer retention: security observations default to 180 days
  (vs. 90 for other domains) because security trends require longer
  baselines for meaningful regression detection.
- Partial results: when individual scan phases fail, the domain produces
  a partial report with available results rather than failing entirely.
  Missing categories are clearly marked in the report and scored as N/A.

---

## Verification Checklist

- [ ] Domain registers with orchestrator and receives WLT token
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] security-audit workflow executes all 4 scan phases in parallel
- [ ] Scoring formula produces 0–100 clamped result matching weight table
- [ ] security-headers-check workflow runs independently of full audit
- [ ] dependency-audit workflow handles all 4 supported manifest formats
- [ ] OWASP checks map to correct category IDs
- [ ] Conflict resolution deduplicates cross-scan findings
- [ ] Observations feed into lifecycle store
- [ ] Workflow history is queryable via workflow_history action
- [ ] Metrics emit for all workflow executions and agent dispatches
- [ ] Partial results returned when individual scan phases fail

Port: 9703