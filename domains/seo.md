<!-- blueprint
type: domain
name: seo
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
platform: any
-->

# SEO Domain Controller

The SEO domain controller owns the search engine optimization business
function. It receives high-level tasks ("audit this site's SEO",
"optimize these pages"), decomposes them into multi-agent workflows,
dispatches work to specialized agents, aggregates results, and feeds
outcomes back into the continuous optimization lifecycle.

This domain does NOT perform SEO analysis itself. It directs agents
that do: the [seo-analyzer](../agents/seo-analyzer.md) for technical
SEO work and the [a11y-checker](../agents/a11y-checker.md) for
accessibility input that impacts SEO quality.

## Domain Manifest

```json
{
  "name": "seo",
  "type": "domain",
  "version": "1.0.0",
  "description": "SEO optimization — audits, recommendations, and automated fixes",
  "url": "http://localhost:9700",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "target_files", "type": "file_list", "description": "HTML files to audit or optimize"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated SEO report with recommendations and proposed changes"}
  ],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["seo-analyzer", "a11y-checker"],
  "workflows": ["seo-audit", "seo-optimize"]
}
```

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| [seo-analyzer](../agents/seo-analyzer.md) | HTML scanning, metadata extraction, LLM analysis, report generation | scan, analyze, report phases |
| [a11y-checker](../agents/a11y-checker.md) | Alt text validation, accessibility checks that affect SEO | accessibility, alt text review phases |

## Workflows

### seo-audit

Full SEO audit of a set of HTML files. Produces a scored report with
findings, recommendations, and proposed changes.

**Trigger:** `task.action = "audit"`

```yaml
workflow: seo-audit
description: Full SEO audit — scan, analyze, check accessibility, report
trigger: action = "audit"

phases:
  - name: scan
    agent: seo-analyzer
    action: scan_html
    input:
      html_files: $task.payload.files
    output: scan_results
    timeout: 60

  - name: analyze
    agent: seo-analyzer
    action: analyze_metadata
    input:
      metadata: $phases.scan.output.files
      entity: $task.context.entity
    output: analysis_results
    timeout: 120
    depends_on: [scan]

  - name: accessibility
    agent: a11y-checker
    action: check_images
    input:
      images: $phases.scan.output.files[*].metadata.images
    output: a11y_results
    timeout: 60
    depends_on: [scan]

  - name: report
    agent: seo-analyzer
    action: generate_report
    input:
      analysis: $phases.analyze.output
      a11y: $phases.accessibility.output
    output: final_report
    timeout: 60
    depends_on: [analyze, accessibility]
    approval: required
```

**Phase dependency graph:**
```
scan ──┬── analyze ───┬── report
       └── accessibility ─┘
```

`analyze` and `accessibility` run in parallel after `scan` completes.
`report` waits for both.

**Inputs:**
```json
{
  "files": ["app/index.html", "app/about.html", "app/pricing.html"]
}
```

**Outputs (aggregated TaskResult):**
```json
{
  "task_id": "...",
  "agent_name": "seo",
  "status": "pending_approval",
  "summary": "Scanned 3 files — 12 issues found (3 critical, 5 high, 4 medium). SEO score: 45/100.",
  "changes": [
    {
      "path": "app/index.html",
      "action": "modify",
      "original": "<title>Home</title>",
      "modified": "<title>Weblisk — Modern Web Framework</title>",
      "diffs": [{"element": "title", "before": "Home", "after": "Weblisk — Modern Web Framework", "reason": "Title too short for SEO"}]
    }
  ],
  "observations": [...],
  "recommendations": [...],
  "metrics": {
    "files_scanned": 3,
    "total_issues": 12,
    "critical_issues": 3,
    "seo_score": 45,
    "phases_completed": 4,
    "duration_ms": 8500
  }
}
```

### seo-optimize

Apply previously approved SEO recommendations to files. This workflow
runs AFTER an audit's recommendations have been reviewed and accepted.

**Trigger:** `task.action = "optimize"`

```yaml
workflow: seo-optimize
description: Apply approved SEO changes and verify
trigger: action = "optimize"

phases:
  - name: apply
    agent: self
    action: apply_changes
    input:
      changes: $task.payload.approved_changes
    output: applied_results
    timeout: 60

  - name: verify
    agent: seo-analyzer
    action: scan_html
    input:
      html_files: $task.payload.files
    output: verification_results
    timeout: 60
    depends_on: [apply]

  - name: measure
    agent: self
    action: compare_before_after
    input:
      before: $task.payload.baseline_observations
      after: $phases.verify.output
    output: feedback
    depends_on: [verify]
```

**Inputs:**
```json
{
  "files": ["app/index.html"],
  "approved_changes": [...],
  "baseline_observations": [...]
}
```

**Outputs:**
```json
{
  "status": "success",
  "summary": "Applied 5 changes to 2 files. SEO score improved from 45 to 78.",
  "feedback": [
    {"recommendation_id": "rec-001", "type": "metric", "signal": "positive", "metric_before": 4, "metric_after": 42, "metric_name": "title_length"}
  ],
  "metrics": {
    "changes_applied": 5,
    "score_before": 45,
    "score_after": 78,
    "improvement": 33
  }
}
```

## Domain HandleMessage Actions

### execute_workflow

Primary entry point — invoked by the orchestrator via `POST /v1/execute`.
Selects and runs a workflow based on `task.action`.

### apply_changes

Domain-internal action for the `seo-optimize` workflow. Applies approved
`ProposedChange` entries to files.

```
1. For each change in approved_changes:
   a. Read the target file
   b. Apply modifications (see seo-analyzer HTML Modification Rules)
   c. Write the modified file
   d. Record: {path, action, original_hash, modified_hash}
2. Return applied results
```

### compare_before_after

Domain-internal action for measuring improvement. Compares baseline
observations to post-change observations.

```
1. For each file in baseline:
   a. Find matching file in after observations
   b. Compare measurements: title_length, description_length, h1_count, etc.
   c. For each applied recommendation:
      Create Feedback entry with before/after metric values
      Determine signal: positive if metric moved toward target
2. Return array of Feedback entries
```

### get_status

Returns domain health and agent availability.

### get_workflows

Returns available workflow definitions with phase counts.

### workflow_history

Returns recent workflow executions with results.

## Strategy Alignment

The SEO domain responds to strategies with metrics such as:

| Strategy Metric | Domain Workflow | Measurement |
|----------------|-----------------|-------------|
| organic_sessions | seo-audit | Cannot directly measure (external analytics) |
| seo_score | seo-audit → seo-optimize | Computed from finding severity counts |
| pages_optimized | seo-optimize | Count of successfully changed files |
| critical_issues | seo-audit | Count of critical-severity findings |
| meta_coverage | seo-audit | % of pages with title + description + canonical |

The domain maps strategy targets to its audit metrics. For example,
a strategy targeting `meta_coverage > 95%` drives the domain to run
`seo-audit` on all pages and prioritize pages missing meta tags.

## Aggregation Rules

When combining results from multiple agents:

```
1. Merge observations: concat, deduplicate by (target + element)
2. Merge findings: concat, sort by severity (critical > high > medium > low)
3. Merge recommendations: concat, sort by (priority desc, impact desc)
4. Merge proposed changes: group by file path, apply in file order
5. Resolve conflicts:
   - If two agents recommend different values for the same element:
     Prefer the agent with higher accuracy in AgentMetrics
   - If equal: prefer the recommendation with higher impact score
6. Compute SEO score:
   score = 100 - (critical_issues * 15) - (high_issues * 5) - (medium_issues * 2)
   Clamp to 0-100 range
```

## Port Assignment

SEO domain controller: 9700

## Verification Checklist

- [ ] Registers with `type: "domain"` and declares required agents
- [ ] Routes `action: "audit"` to the seo-audit workflow
- [ ] Routes `action: "optimize"` to the seo-optimize workflow
- [ ] scan phase dispatches to seo-analyzer via POST /v1/message
- [ ] analyze and accessibility phases run in parallel after scan
- [ ] report phase waits for both analyze and accessibility
- [ ] Results from all phases are aggregated into single TaskResult
- [ ] Observations include measurements per file
- [ ] Recommendations include priority and impact scores
- [ ] ProposedChanges include full before/after diffs
- [ ] seo-optimize applies changes and re-verifies
- [ ] compare_before_after produces Feedback entries
- [ ] SEO score is computed from finding severity counts
- [ ] Conflicting recommendations are resolved by agent accuracy
- [ ] Domain responds to get_status with agent availability
