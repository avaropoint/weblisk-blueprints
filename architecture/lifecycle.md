<!-- blueprint
type: architecture
name: lifecycle
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/orchestrator, architecture/domain, architecture/agent, patterns/messaging, patterns/observability]
platform: any
tier: free
-->

# Continuous Optimization Lifecycle

The Weblisk architecture implements a continuous, autonomous feedback
loop. The **Lifecycle Agent** (an infrastructure agent) drives a cycle
of strategy, observation, recommendation, execution, and measurement —
compounding intelligence across every interaction.

In v2, the lifecycle is event-driven. The Lifecycle Agent subscribes
to workflow completion events (scope: `"*"`, requires `event:observe`)
and stores observations and recommendations from workflow results.
Strategies, approvals, and feedback are managed entirely by the
Lifecycle Agent — not the orchestrator.

See [agents/lifecycle.md](../agents/lifecycle.md) for the Lifecycle
Agent blueprint.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: AgentMessage
          fields_used: [from, to, type, action, payload]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskResult
          fields_used: [task_id, status, output, observations, recommendations]
        - name: Strategy
          fields_used: [id, name, objective, targets, priority, status]
        - name: Observation
          fields_used: [id, agent_name, target, measurements, findings, strategy_id]
        - name: Recommendation
          fields_used: [id, observation_id, action, priority, impact, status]
        - name: Feedback
          fields_used: [id, recommendation_id, signal, metric_before, metric_after]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ServiceDirectory
          fields_used: [agents, routing_table]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: DomainWorkflow
          fields_used: [name, phases, on_error]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentEndpoints
          fields_used: [execute, message, event, health]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: EventEnvelope
          fields_used: [topic, scope, payload, source]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: HealthStatus
          fields_used: [status, component, checks]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

### Owns
- Strategy creation, storage, decomposition, and progress tracking
- Observation capture from workflow completion events
- Recommendation lifecycle (pending → accepted/rejected → applied)
- Feedback collection and signal classification (positive/negative/neutral)
- Agent metrics aggregation (accuracy, adoption rate, impact scores)
- Approval workflow orchestration (auto-approve or human gate)
- Cycle coordination: strategize → observe → recommend → execute → measure → learn

### Does NOT Own
- Workflow execution (owned by Workflow Agent)
- Task dispatch and concurrency management (owned by Task Agent)
- Domain-specific analysis logic (owned by work agents)
- Agent registration or routing (owned by orchestrator)
- Storage implementation details (owned by platform-specific backends)

---

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| `POST /v1/message` action: `create_strategy` | HTTP | Create a new strategy with targets |
| `POST /v1/message` action: `get_strategy` | HTTP | Retrieve strategy by ID |
| `POST /v1/message` action: `set_context` | HTTP | Set entity context for the lifecycle |
| `POST /v1/message` action: `approve_recommendation` | HTTP | Approve a pending recommendation |
| `POST /v1/message` action: `reject_recommendation` | HTTP | Reject a pending recommendation |
| `POST /v1/event` topic: `workflow.completed` | Event | Receive completed workflow results (scope: `*`) |
| Published: `lifecycle.recommendation.created` | Event | Emitted when a new recommendation is stored |
| Published: `lifecycle.recommendation.accepted` | Event | Emitted when a recommendation is approved |
| Published: `lifecycle.recommendation.rejected` | Event | Emitted when a recommendation is rejected |
| Published: `workflow.trigger` | Event | Emitted to initiate a domain workflow |

---

## Data Flow

The complete data flow is documented in the
[Data Flow Summary section](#data-flow-summary). Abbreviated sequence:

1. User or system creates a strategy via `POST /v1/message` to the Lifecycle Agent
2. Lifecycle Agent maps strategy to domain and publishes `workflow.trigger`
3. Workflow Agent resolves DAG, Task Agent dispatches to work agents
4. Work agents produce observations and recommendations
5. Workflow Agent publishes `workflow.completed` (scope: `*`)
6. Lifecycle Agent captures observations and stores recommendations
7. Approval gate: auto-approve or wait for human review
8. Lifecycle Agent triggers measurement workflow after waiting period
9. Follow-up observations produce feedback entries (positive/negative/neutral)
10. Agent metrics and strategy progress are updated; cycle restarts

---

## The Cycle

```
           ┌────────────────────────────────────────────┐
           │                                            │
           ▼                                            │
  ┌─────────────────┐                                   │
  │   1. STRATEGIZE  │  Define objectives + targets      │
  └────────┬────────┘                                   │
           │                                            │
           ▼                                            │
  ┌─────────────────┐                                   │
  │   2. OBSERVE     │  Agents collect measurements      │
  └────────┬────────┘                                   │
           │                                            │
           ▼                                            │
  ┌─────────────────┐                                   │
  │   3. RECOMMEND   │  Agents propose changes           │
  └────────┬────────┘                                   │
           │                                            │
           ▼                                            │
  ┌─────────────────┐                                   │
  │   4. EXECUTE     │  Apply approved changes           │
  └────────┬────────┘                                   │
           │                                            │
           ▼                                            │
  ┌─────────────────┐                                   │
  │   5. MEASURE     │  Compare before / after           │
  └────────┬────────┘                                   │
           │                                            │
           ▼                                            │
  ┌─────────────────┐                                   │
  │   6. LEARN       │  Update metrics, refine strategy  │
  └────────┴────────────────────────────────────────────┘
```

The loop runs continuously. Each completed cycle feeds into the next:
observations from the latest execution inform the next round of
recommendations, and feedback from measurements refines future
strategy.

## Phase 1 — Strategize

A strategy is a business objective with measurable targets and a
deadline. Strategies are created by users or systems and stored by the
Lifecycle Agent.

**Who:** User or external system → Lifecycle Agent (via `POST /v1/message`
with action `create_strategy`)
**Produces:** `Strategy` with `StrategyTarget` entries

```json
{
  "id": "strat-001",
  "name": "Improve organic traffic",
  "objective": "Increase organic search traffic by 40% in Q3",
  "targets": [
    {"metric": "organic_sessions", "current": 12000, "goal": 16800, "deadline": "2026-09-30", "unit": "sessions/month", "progress": 0.0}
  ],
  "priority": 1,
  "status": "active"
}
```

**Decomposition:** The Lifecycle Agent maps strategies to domains. A
strategy targeting SEO metrics routes to the SEO domain via a
`workflow.trigger` event. The domain interprets the strategy's targets
and selects appropriate workflows.

```
Strategy               → Domain
"Improve organic traffic" → seo domain → seo-audit workflow
"Reduce page load time"   → perf domain → perf-audit workflow
"Fix compliance gaps"     → security domain → compliance-audit workflow
```

Multiple strategies can be active simultaneously. Domains prioritize
tasks from higher-priority strategies.

## Phase 2 — Observe

Agents collect structured measurements about the current state.
Observations are the raw data that the system reasons about.

**Who:** Work agents, dispatched by domains during workflow execution
**Produces:** `Observation` with `Finding` entries

```json
{
  "id": "obs-001",
  "agent_name": "seo-analyzer",
  "target": "app/index.html",
  "timestamp": "2026-04-16T10:00:00Z",
  "measurements": {
    "title_length": 4,
    "meta_description_length": 0,
    "h1_count": 0,
    "image_count": 5,
    "images_missing_alt": 3
  },
  "findings": [
    {"rule_id": "seo-title-length", "severity": "critical", "element": "title", "current": "Home", "expected": "30-60 characters", "message": "Title too short for SEO", "fixable": true, "fix": "Weblisk \u2014 Modern Web Framework"}
  ],
  "strategy_id": "strat-001"
}
```

**Data flow:**
```
Domain publishes workflow.trigger → Workflow Agent resolves DAG
  → Task Agent dispatches to work agent → Agent scans target
  → Agent returns result with measurements and findings
  → Task Agent publishes task.complete → Workflow Agent aggregates
  → Workflow Agent publishes workflow.completed (scope: domain + "*")
  → Lifecycle Agent (subscribed with scope: "*") captures observations
  → Lifecycle Agent stores in observation history
```

Observations are immutable once recorded. They represent a point-in-time
measurement. Comparing observations over time reveals trends.

## Phase 3 — Recommend

Based on observations, agents propose concrete changes with estimated
impact and priority.

**Who:** Work agents (as part of workflow), aggregated by domains
**Produces:** `Recommendation` entries

```json
{
  "id": "rec-001",
  "observation_id": "obs-001",
  "agent_name": "seo-analyzer",
  "strategy_id": "strat-001",
  "target": "app/index.html",
  "action": "modify",
  "element": "title",
  "current": "Home",
  "proposed": "Weblisk \u2014 Modern Web Framework",
  "reason": "Title under 10 chars — search engines truncate or ignore short titles",
  "priority": "critical",
  "impact": 0.8,
  "status": "pending"
}
```

**Priority logic:**
- `critical` — Violates a hard rule (missing, broken, or dangerous)
- `high` — Significant improvement with clear impact
- `medium` — Moderate improvement, good practice
- `low` — Minor optimisation, nice to have

**Impact score:** 0.0 to 1.0 estimate of how much this change affects
the strategy's target metric. Work agents estimate this based on domain
knowledge; the system refines estimates over time using feedback data.

**Approval workflow:**
```
Recommendation created (status: "pending")
  → Lifecycle Agent publishes: lifecycle.recommendation.created
  → If domain.approval = "auto" AND priority ≠ "critical":
      status → "accepted" (auto-approved)
      Lifecycle Agent publishes: lifecycle.recommendation.accepted
  → If domain.approval = "required" OR priority = "critical":
      status stays "pending" until human review
  → Human approves via POST /v1/message to Lifecycle Agent:
      status → "accepted"
      Lifecycle Agent publishes: lifecycle.recommendation.accepted
  → Human rejects: status → "rejected" (with reason)
      Lifecycle Agent publishes: lifecycle.recommendation.rejected
```

## Phase 4 — Execute

Accepted recommendations are applied. The domain controller creates
`ProposedChange` entries and applies them.

**Who:** Domain controller, with work agents for complex changes
**Produces:** `ProposedChange` entries in `TaskResult`

```
For each accepted recommendation:
  1. Resolve the target (file path, URL, resource)
  2. Apply the change:
     - File modification: read original → apply change → write modified
     - Configuration change: update config value
     - External action: API call, deployment trigger
  3. Record the change: {path, action, original, modified, diffs}
  4. Set recommendation status → "applied"
```

All changes are recorded with full before/after content so they can be
reviewed, diffed, and reverted.

## Phase 5 — Measure

After changes are applied, the system measures their effect. This
closes the observation loop.

**Who:** Same work agents that produced the original observations
**Produces:** `Feedback` entries

```
1. Wait for measurement window (configured per strategy — e.g. 24 hours)
2. Re-run the same observation workflow
3. Compare new measurements to pre-change observations
4. For each applied recommendation:
   a. Find the original observation and the new observation
   b. Compare the relevant metric before and after
   c. Create Feedback entry
```

```json
{
  "id": "fb-001",
  "recommendation_id": "rec-001",
  "type": "metric",
  "signal": "positive",
  "detail": "Title length improved from 4 to 42 characters",
  "metric_before": 4,
  "metric_after": 42,
  "metric_name": "title_length",
  "timestamp": "2026-04-17T10:00:00Z"
}
```

**Signal types:**
- `positive` — The metric moved toward the goal
- `negative` — The metric moved away from the goal
- `neutral` — No measurable change

**Feedback sources:**
- `metric` — Automated measurement (most common)
- `user` — Human feedback (thumbs up/down, comments)
- `automated` — External system feedback (analytics, search console)

## Phase 6 — Learn

The system updates its internal metrics and refines future behaviour
based on accumulated feedback.

**Who:** Lifecycle Agent + domain controllers
**Produces:** Updated `AgentMetrics`, adjusted strategy targets

### Agent Metrics Update

After each feedback entry, update the agent's running metrics:

```
AgentMetrics for "seo-analyzer":
  total_observations: +1
  total_findings: +N
  total_recommendations: +N
  adoption_rate: accepted / (accepted + rejected)
  accuracy: positive_feedback / total_feedback
  impact_score: average(actual_metric_change / estimated_impact)
  false_positive_rate: rejected_as_wrong / total_recommendations
```

These metrics are used to:
1. **Weight recommendations** — Agents with higher accuracy get higher
   priority in conflict resolution
2. **Tune thresholds** — If an agent has high false_positive_rate,
   tighten its finding rules
3. **Report confidence** — Show users how reliable each agent's
   suggestions are

### Strategy Progress Update

```
For each strategy target:
  1. Query latest observations matching this metric
  2. Update target.current to latest measurement
  3. Recalculate target.progress = (current - baseline) / (goal - baseline)
  4. If progress ≥ 1.0: strategy status → "completed"
  5. If deadline passed and progress < 1.0: flag for review
```

### Cycle Restart

The learn phase flows directly back to Strategize:
- Updated metrics inform which strategies need more attention
- Agent accuracy data adjusts which agents are preferred
- New observations may reveal new issues → new strategies

## Data Flow Summary

```
User/System
  │
  ├─ POST /v1/message to Lifecycle Agent
  │   action: create_strategy → Strategy + StrategyTarget
  ├─ POST /v1/message to Lifecycle Agent
  │   action: set_context    → EntityContext
  │
  ▼
Lifecycle Agent
  │
  ├─ Maps strategy to domain
  ├─ Publishes: workflow.trigger (scope: "workflow")
  │   payload: {workflow, source: "lifecycle", strategy_id, ...}
  │
  ▼
Workflow Agent (receives workflow.trigger)
  │
  ├─ Fetches workflow definition from domain (POST /v1/message)
  ├─ Resolves DAG, publishes task.submit for each phase
  │
  ▼
Task Agent (receives task.submit)
  │
  ├─ Dispatches: POST /v1/execute to target work agent
  ├─ Publishes: task.complete (scope: "workflow")
  │
  ▼
Workflow Agent (receives task.complete)
  │
  ├─ Advances DAG, dispatches next phases
  ├─ Publishes: workflow.completed (scope: invoker)
  │
  ▼
Lifecycle Agent (subscribed to workflow.completed, scope: "*")
  │
  ├─ Extracts observations + recommendations from result
  ├─ Stores observations in observation history
  ├─ Publishes: lifecycle.recommendation.created
  │
  ▼
Approval Gate
  │
  ├─ Auto-approved or human-reviewed via Lifecycle Agent
  ├─ Publishes: lifecycle.recommendation.accepted
  │
  ▼
Lifecycle Agent (triggers re-observation)
  │
  ├─ Publishes: workflow.trigger for measurement workflow
  ├─ Waits for measurement window
  ├─ Collects feedback from follow-up observations
  ├─ Updates AgentMetrics
  ├─ Updates Strategy progress
  └─ Cycle restarts
```

## Timing and Triggers

The lifecycle is not a single-threaded loop. Multiple cycles run
concurrently, triggered by:

| Trigger | Effect |
|---------|--------|
| New strategy created | Lifecycle Agent decomposes → workflow.trigger |
| Scheduled intervals | Cron agent triggers periodic observation |
| External event | Webhook triggers domain workflow |
| Human request | User messages Lifecycle Agent via API |
| Previous cycle complete | Feedback triggers re-observation |

## Types

### ProposedChange

Applied by domain controllers during the Execute phase.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Path | string | `path` | yes | Target resource (file path, URL, config key) |
| Action | string | `action` | yes | `modify`, `create`, `delete` |
| Original | string | `original` | no | Content before change (for modify/delete) |
| Modified | string | `modified` | no | Content after change (for modify/create) |
| Diffs | []string | `diffs` | no | Unified diff hunks |
| RecommendationID | string | `recommendation_id` | yes | Recommendation that triggered this change |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

### AgentMetrics

Running performance metrics per agent, updated incrementally from
feedback signals.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| AgentName | string | `agent_name` | yes | Agent these metrics apply to |
| TotalObservations | int | `total_observations` | yes | Cumulative observation count |
| TotalFindings | int | `total_findings` | yes | Cumulative finding count |
| TotalRecommendations | int | `total_recommendations` | yes | Cumulative recommendation count |
| AdoptionRate | float64 | `adoption_rate` | yes | accepted / (accepted + rejected) |
| Accuracy | float64 | `accuracy` | yes | positive_feedback / total_feedback |
| ImpactScore | float64 | `impact_score` | yes | avg(actual_change / estimated_impact) |
| FalsePositiveRate | float64 | `false_positive_rate` | yes | rejected_as_wrong / total_recommendations |
| LastUpdated | int64 | `last_updated` | yes | Unix epoch seconds |

---

## Implementation Notes

- **Observation storage**: Observations SHOULD be stored with enough
  history for trend analysis. At minimum, keep the last 90 days.
- **Feedback windows**: After applying changes, wait before measuring.
  The measurement window is specified per strategy target via the
  `measurement_window` field (seconds). Typical values: SEO metrics
  86400–604800 (1–7 days), performance metrics 300–3600 (5 min–1 hr).
  If unset, the Lifecycle Agent uses 86400 (24 hours) as the default.
- **Idempotent observations**: Running the same observation workflow
  twice on unchanged content should produce identical results.
- **Metric aggregation**: AgentMetrics are running aggregates, not
  recomputed from scratch each cycle. Use incremental formulas.
- **Strategy decomposition**: The Lifecycle Agent maps strategies to
  domains using metric-name-to-domain routing. The mapping is built
  from domain manifests: each domain's `workflows` declare which
  metrics they produce observations for. If a strategy target's
  `metric_name` matches an observation produced by a domain's
  workflow, the strategy is routed to that domain. When no match is
  found, the Lifecycle Agent logs a warning and skips the target.
- **Audit trail**: Every state transition (recommendation pending →
  accepted → applied → measured) MUST be logged for traceability.

## Verification Checklist

- [ ] Strategies can be created via POST /v1/message to Lifecycle Agent
- [ ] Lifecycle Agent maps strategies to domains and publishes workflow.trigger
- [ ] Observations are captured from workflow.completed events (scope: "*")
- [ ] Recommendations have priority, impact, and status
- [ ] Approval workflow transitions: pending → accepted/rejected → applied
- [ ] Lifecycle Agent publishes lifecycle.recommendation.* events
- [ ] Feedback is collected after applying changes
- [ ] Feedback signal correctly reflects metric change direction
- [ ] AgentMetrics are updated after each feedback entry
- [ ] Strategy progress is recalculated from latest observations
- [ ] Completed strategies transition to "completed" status
- [ ] Multiple lifecycle cycles can run concurrently
- [ ] Full audit trail exists for every state transition
- [ ] Lifecycle Agent does NOT require orchestrator endpoints for data storage
