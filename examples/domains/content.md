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

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| content-analyzer | Readability scoring, heading hierarchy, word count, sentence complexity, link density | `analyze` action — analyze, structure phases |
| meta-checker | Title, description, Open Graph, Twitter Cards, structured data, canonical URLs | `check` action — metadata, structured-data phases |

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

## Scoring

| Metric | Weight | Source Agent |
|--------|--------|-------------|
| Readability | 30% | content-analyzer |
| Structure | 30% | content-analyzer |
| Metadata | 25% | meta-checker |
| Link quality | 15% | content-analyzer |

Content score = (readability × 0.30) + (structure × 0.30) + (metadata × 0.25) + (links × 0.15), clamped 0–100.

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

## Aggregation Rules

1. Merge observations: concat, deduplicate by (target + element)
2. Merge findings: sort by severity (critical → high → medium → low → info)
3. Merge recommendations: sort by priority desc, impact desc
4. Merge proposed changes: group by file path
5. Resolve conflicts: when content-analyzer and meta-checker disagree on
   severity for the same element, the agent with the more specific check
   wins (e.g., meta-checker wins on metadata issues, content-analyzer
   wins on readability issues)

## Strategy Alignment

| Strategy Metric | Domain Workflow | Measurement |
|----------------|-----------------|-------------|
| content_score | content-audit | Weighted composite from scoring table |
| readability_avg | content-audit | Average Flesch-Kincaid across pages |
| metadata_coverage | content-audit | % of pages with title + description + OG |
| pages_optimized | content-optimize | Count of successfully changed files |
| score_improvement | content-optimize | Before/after delta on content_score |

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_score | gauge | Latest domain score (0–100) |
| domain_findings_total | counter | Findings by category and severity |

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, workflow fails with partial results. |
| Agent timeout | Cancel timed-out phase, continue with available results if non-blocking. Log warning. |
| Agent error response | Record error in findings. Continue workflow if other phases are independent. |
| All agents unavailable | Domain status → offline. Reject new workflows with 503. |
| Aggregation conflict | Apply conflict resolution rules (see Aggregation Rules). |

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
