<!-- blueprint
type: pattern
name: domain-controller
version: 1.0.0
requires: [protocol/types, protocol/identity, architecture/domain, architecture/lifecycle, patterns/observability]
platform: any
tier: free
-->

# Domain Controller Pattern

Standard structure, lifecycle, and contracts for domain controllers.
Domain controllers are the business-function owners in a Weblisk
deployment — they receive high-level tasks, decompose them into
multi-agent workflows, dispatch work to specialized agents, aggregate
results, and feed outcomes into the continuous optimization lifecycle.

Domains `extends: patterns/domain-controller` and declare only their
unique parts: agent roster, workflows, scoring weights, domain-specific
types, and aggregation rules.

## Overview

Every domain controller follows the same structural contract:

1. **Manifest** — identity, capabilities, required agents, workflows
2. **Workflows** — phased execution plans with agent dispatch
3. **HandleMessage actions** — standard + domain-specific actions
4. **Scoring** — weighted composite score (0–100)
5. **Aggregation** — rules for merging multi-agent results
6. **Observability** — inherited from patterns/observability + domain metrics
7. **Error handling** — standard degradation model

This pattern defines the invariant parts. Domains override the
variant parts.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: IOSpec
          fields_used: [name, type, description]
        - name: TaskPayload
          fields_used: [action, payload, trace_id]
        - name: ErrorResponse
          fields_used: [error, code, category, retryable]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Identity
          fields_used: [id, public_key, verification]
        - name: WLT
          fields_used: [token, claims]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: DomainManifest
          fields_used: [name, type, version, capabilities, required_agents, workflows]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/lifecycle
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Observation
          fields_used: [target, element, value, timestamp]
        - name: Feedback
          fields_used: [before, after, metric]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: MetricDefinition
          fields_used: [name, type, description, labels]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Structural inheritance** — Domain controllers inherit a standard contract (manifest, actions, scoring, aggregation, observability, error handling) and only declare their unique parts: agent roster, workflows, scoring weights, and conflict resolution.
2. **Phased workflow execution** — All workflows follow a dependency-ordered phase model where independent phases run in parallel and dependent phases run sequentially, with timeout enforcement and approval gates.
3. **Composable scoring** — Every domain computes a weighted composite score (0–100) from declared categories, enabling consistent cross-domain comparison and lifecycle-driven optimization.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: workflow-execution
      description: Phased multi-agent workflow with dispatch, aggregation, and reporting
      parameters:
        - name: workflow
          type: string
          required: true
          description: Workflow name to execute
        - name: action
          type: string
          required: true
          description: Action that triggers the workflow
      inherits: Phase execution, parallel dispatch, timeout enforcement, approval gates
      overridable: true
      override_constraints: Must preserve phase dependency ordering and agent dispatch protocol

    - name: scoring
      description: Weighted composite score computation (0–100) from category scores
      parameters:
        - name: weights
          type: object
          required: true
          description: Category weights (must sum to 1.0)
        - name: ranges
          type: object
          required: true
          description: Score range labels (excellent, good, fair, poor, critical)
      inherits: Score formula, range labels, clamping
      overridable: true
      override_constraints: Weights must sum to 1.0, score must be clamped 0–100

    - name: aggregation
      description: Rules for combining multi-agent results with conflict resolution
      parameters:
        - name: conflict_resolution
          type: string
          required: true
          description: Strategy for resolving agent result conflicts
      inherits: Observation dedup, finding sort, recommendation priority, change grouping
      overridable: true
      override_constraints: Must declare domain-specific conflict resolution strategy

  types:
    - name: DomainManifest
      description: Domain identity, capabilities, required agents, and workflows
      inherited_by: Domain Manifest section
    - name: WorkflowDefinition
      description: Phased execution plan with agent dispatch and dependencies
      inherited_by: Workflow Structure section
    - name: ScoringTable
      description: Weighted category scores with range labels
      inherited_by: Scoring section

  endpoints:
    - path: /v1/execute
      description: Primary workflow entry point
      inherited_by: Standard HandleMessage Actions section
    - path: /v1/health (get_status)
      description: Domain health and agent availability
      inherited_by: Standard HandleMessage Actions section
```

---

## Domain Manifest

Every domain controller MUST register with a manifest following this
structure:

```yaml
manifest:
  name: <domain-name>
  type: domain
  version: <semver>
  description: <one-line description>
  url: http://localhost:<port>
  public_key: <hex Ed25519 public key>

  capabilities:
    - name: agent:message
      resources: []
    - name: workflow:execute
      resources: []

  inputs:
    - name: <primary-input>
      type: <file_list | url_list | json>
      description: <what the domain accepts>

  outputs:
    - name: domain_report
      type: json
      description: <what the domain produces>

  collaborators: []
  approval: required                   # or "auto"
  required_agents: [<agent-names>]
  workflows: [<workflow-names>]
```

Domains declare their own `inputs`, `required_agents`, and
`workflows`. The rest of the manifest structure is inherited.

---

## Standard HandleMessage Actions

Every domain controller MUST implement these actions. They are
inherited — domains do not need to redeclare them unless overriding
behavior.

| Action | Source | Description |
|--------|--------|-------------|
| execute_workflow | Any caller | Primary entry point via `POST /v1/execute`. Publishes `workflow.trigger` for matched action. |
| aggregate_results | Internal | Combine outputs from multiple agent phases into a unified result. |
| generate_recommendations | Internal | Prioritize findings into actionable items sorted by impact × priority. |
| record_observations | Internal | Feed results into the lifecycle store as Observation entries. |
| compile_report | Internal | Build the domain report from aggregated results, recommendations, and observations. |
| apply_changes | Internal | Apply approved changes to target files. Used by optimize workflows. |
| compare_before_after | Internal | Measure score improvement, produce Feedback entries with before/after metrics. |
| get_status | Orchestrator/Admin | Domain health, agent availability, current state (online/degraded/offline). |
| get_workflows | Orchestrator/Admin | Available workflow definitions with phase counts. |
| workflow_history | Admin | Recent workflow executions with results and durations. |

Domains MAY add domain-specific actions (e.g. `evaluate_headers`
in security, `analyze_trends` in health).

---

## Workflow Structure

All domain workflows follow the same phased execution model:

```yaml
workflow: <name>
description: <one-line>
trigger: action = "<action-name>"

phases:
  - name: <phase-name>
    agent: <agent-name> | self
    action: <action-name>
    input:
      <key>: $task.payload.<field>
      <key>: $phases.<prior-phase>.output.<field>
    output: <output-variable>
    timeout: <seconds>
    depends_on: [<prior-phases>]     # optional — phases without depends_on run first
    approval: required               # optional — pause for human approval
```

### Workflow Conventions

1. **Audit workflows** (action: `audit`) — scan/analyze → aggregate →
   recommend → observe → report
2. **Optimize workflows** (action: `optimize`) — plan → execute →
   verify → measure
3. **Lightweight workflows** (action: `check-*`) — scan → evaluate
4. Independent phases without `depends_on` run in **parallel**
5. Phase outputs are referenced as `$phases.<name>.output`
6. `agent: self` dispatches to the domain's own HandleMessage actions

---

## Scoring

Every domain computes a composite score from weighted categories.
The formula is always:

```
score = Σ(category_score × weight), clamped 0–100
```

Domains declare their scoring table:

```yaml
scoring:
  weights:
    <category>: <weight>     # weights MUST sum to 1.0
    <category>: <weight>
  
  ranges:
    excellent: [90, 100]
    good: [75, 89]           # or [80, 89] — domain-specific
    fair: [50, 74]           # or "degraded" label
    poor: [25, 49]
    critical: [0, 24]
```

Score ranges MAY use domain-appropriate labels (e.g. `degraded`
instead of `fair` for health domains).

---

## Aggregation Rules

When combining results from multiple agents, domains follow these
standard rules plus domain-specific overrides:

```yaml
aggregation:
  # Standard rules (inherited):
  observations: concat_deduplicate    # deduplicate by (target + element)
  findings: sort_by_severity          # critical > high > medium > low > info
  recommendations: sort_by_priority   # priority desc, impact desc
  proposed_changes: group_by_file     # group by file path, apply in order

  # Domain-specific conflict resolution (MUST be declared):
  conflict_resolution: <strategy>
  # Examples:
  #   "prefer_specific_agent"  — meta-checker wins on metadata, content-analyzer on readability
  #   "prefer_higher_accuracy" — use AgentMetrics accuracy
  #   "prefer_lower_score"     — conservative (health domain)
```

---

## Strategy Alignment

Domains respond to lifecycle strategies by mapping strategy metrics
to their audit workflows:

```yaml
strategy_alignment:
  metrics:
    - name: <metric-name>
      workflow: <workflow-name>
      measurement: <how-to-compute>
```

Standard strategy modes and domain behavior:

| Mode | Behavior |
|------|----------|
| `observe` | Run audit workflows, collect metrics, report status |
| `recommend` | Flag issues, suggest improvements, prioritize by impact |
| `execute` | Apply approved changes, emit events, update lifecycle |
| `auto` | All of the above — fully autonomous operation |

---

## Observability

Domains inherit the standard metrics from `patterns/observability`.
Additionally, every domain MUST emit these domain-level metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `domain_workflow_duration_seconds` | histogram | Time to complete a workflow |
| `domain_workflow_total` | counter | Workflow executions by name and status |
| `domain_agent_dispatch_total` | counter | Dispatches by target agent and action |
| `domain_agent_dispatch_duration_seconds` | histogram | Time waiting for agent response |
| `domain_score` | gauge | Latest domain score (0–100) |
| `domain_findings_total` | counter | Findings by category and severity |

Domains MAY add domain-specific metrics (e.g. `domain_vulnerabilities_total`
for security, `domain_alert_total` for health).

---

## Error Handling

Standard error handling model — inherited by all domains:

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, workflow fails with partial results. |
| Agent timeout | Cancel timed-out phase. Continue with available results if non-blocking. Log warning. |
| Agent error response | Record error in findings. Continue workflow if other phases are independent. |
| All agents unavailable | Domain status → offline. Reject new workflows with 503. |
| Aggregation conflict | Apply domain-specific conflict resolution rules. |

Domains MAY override or extend with domain-specific handling
(e.g. health domain uses cached results on agent timeout).

---

## Implementation Notes

- Domain controllers are agents with `type: domain` — they implement all 6 protocol endpoints
- The domain manifest is returned as part of `POST /v1/describe` alongside the AgentManifest
- Workflow phases should be dispatched in dependency order; independent phases may run in parallel
- Scoring weights must sum to 1.0; implementations should validate at startup
- Domain controllers should cache agent availability to avoid redundant health checks during workflow execution
- Observation and recommendation storage should use the patterns/storage schema for consistency

---

## Verification Checklist

Every domain MUST pass these checks. Domains inherit them and add
domain-specific items.

- [ ] Registers with orchestrator and receives WLT token
- [ ] Manifest declares type: domain with required_agents and workflows
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] execute_workflow routes to correct workflow by task.action
- [ ] Workflow phases execute in correct dependency order
- [ ] Independent phases run in parallel
- [ ] Scoring formula produces 0–100 clamped result matching weight table
- [ ] Conflict resolution applies domain-specific rules
- [ ] Observations feed into lifecycle store
- [ ] Recommendations sorted by priority and impact
- [ ] Workflow history queryable via workflow_history action
- [ ] Metrics emit for all workflow executions and agent dispatches
- [ ] Optimize workflows reject unapproved recommendations
- [ ] compare_before_after produces Feedback entries

---

## Domain Declaration Example

A domain that extends this pattern only needs to declare its unique
configuration:

```yaml
# In domain frontmatter:
# extends: patterns/domain-controller

required_agents: [seo-analyzer, a11y-checker]

scoring:
  weights:
    technical_seo: 0.40
    metadata: 0.25
    accessibility: 0.20
    performance: 0.15
  ranges:
    excellent: [90, 100]
    good: [75, 89]
    fair: [50, 74]
    poor: [25, 49]
    critical: [0, 24]

aggregation:
  conflict_resolution: prefer_higher_accuracy

strategy_alignment:
  metrics:
    - name: seo_score
      workflow: seo-audit
      measurement: weighted composite from scoring table
    - name: pages_optimized
      workflow: seo-optimize
      measurement: count of successfully changed files

# Then only the workflows and domain-specific types/actions follow
```
