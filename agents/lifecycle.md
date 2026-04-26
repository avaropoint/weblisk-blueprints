<!-- blueprint
type: agent
subtype: infrastructure
name: lifecycle
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, architecture/lifecycle, patterns/messaging]
platform: any
tier: free
port: 9782
-->

# Lifecycle Agent

Infrastructure agent that owns the continuous optimization loop.
Manages strategies, entity context, observations, recommendations,
approvals, feedback, and agent metrics. Subscribes globally
(scope: `"*"`) to workflow completion events to capture results
across the entire hub.

See [architecture/lifecycle.md](../architecture/lifecycle.md) for the
full lifecycle specification.

## Identity

| Field | Value |
|-------|-------|
| Name | `lifecycle` |
| Type | `infrastructure` |
| Port | `9782` (advisory) |
| Namespace | `lifecycle.*` |

## Capabilities

```json
{
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []},
    {"name": "event:observe", "resources": []}
  ]
}
```

`event:observe` is required because the Lifecycle Agent subscribes to
`workflow.completed` and `workflow.failed` with scope `"*"` — it needs
to observe ALL workflow results, not just ones addressed to it.

## Events

### Published (namespace: `lifecycle`)

| Topic | Scope | Payload | When |
|-------|-------|---------|------|
| `lifecycle.observation.recorded` | `*` | `{observation_id, agent, target}` | Observation stored |
| `lifecycle.recommendation.created` | `*` | `{recommendation_id, priority, target}` | New recommendation |
| `lifecycle.recommendation.accepted` | invoker | `{recommendation_id}` | Approved |
| `lifecycle.recommendation.rejected` | invoker | `{recommendation_id, reason}` | Rejected |
| `lifecycle.recommendation.applied` | invoker | `{recommendation_id}` | Change applied |
| `lifecycle.strategy.updated` | `*` | `{strategy_id, progress}` | Strategy progress changed |
| `lifecycle.feedback.recorded` | `*` | `{feedback_id, signal}` | Feedback captured |

### Subscribed

| Pattern | Scope | Group | Purpose |
|---------|-------|-------|---------|
| `workflow.completed` | `*` | `lifecycle` | Capture observations + recommendations |
| `workflow.failed` | `*` | `lifecycle` | Record failure observations |
| `system.agent.registered` | `self` | `lifecycle` | Track new agents for metrics |
| `system.agent.deregistered` | `self` | `lifecycle` | Update agent status |

## Manifest

```json
{
  "name": "lifecycle",
  "type": "infrastructure",
  "version": "2.0.0",
  "description": "Continuous optimization — strategies, observations, recommendations, approvals, feedback, agent metrics",
  "url": "http://localhost:9782",
  "public_key": "<hex>",
  "capabilities": [
    {"name": "task:execute", "resources": []},
    {"name": "agent:message", "resources": []},
    {"name": "event:observe", "resources": []}
  ],
  "publishes": ["lifecycle"],
  "subscriptions": [
    {"pattern": "workflow.completed", "scope": "*", "group": "lifecycle", "max_concurrent": 10},
    {"pattern": "workflow.failed", "scope": "*", "group": "lifecycle"},
    {"pattern": "system.agent.registered", "scope": "self"},
    {"pattern": "system.agent.deregistered", "scope": "self"}
  ]
}
```

## Core Logic

### HandleEvent: workflow.completed

```
1. Parse WorkflowResult from event payload

2. Extract observations:
   For each phase result that contains observations:
     Store observation in observation history
     Link to strategy_id (if present in workflow trigger)
     Publish: lifecycle.observation.recorded (scope: "*")

3. Extract recommendations:
   For each phase result that contains recommendations:
     Create Recommendation entry:
       status: "pending"
       observation_id: linked observation
       strategy_id: from workflow context
     Apply auto-approval rules:
       If source domain approval == "auto" AND priority != "critical":
         status → "accepted"
         Publish: lifecycle.recommendation.accepted (scope: invoker)
       Else:
         Publish: lifecycle.recommendation.created (scope: "*")
         Await human review

4. Update agent metrics:
   For each agent that participated:
     Increment total_observations
     Increment total_findings
     Increment total_recommendations

5. Update strategy progress:
   If strategy_id present:
     Query latest observations for strategy targets
     Recalculate target.progress
     If progress changed:
       Publish: lifecycle.strategy.updated (scope: "*")
     If progress >= 1.0:
       Set strategy status → "completed"
```

### HandleEvent: workflow.failed

```
1. Parse failure info from event payload
2. Record failure observation:
   { agent_name, target, status: "failed", error, timestamp }
3. Publish: lifecycle.observation.recorded (scope: "*")
4. Update agent metrics: increment failure count
```

### HandleMessage: create_strategy

```
Request: { name, objective, targets: [], priority, status }

1. Validate: name, objective, targets must be non-empty
2. Generate strategy ID
3. Store strategy in strategy store
4. Return stored strategy with ID

5. Optionally trigger initial workflow:
   Map strategy targets to domains (metric_name → domain)
   For each mapped domain:
     Publish: workflow.trigger (scope: "workflow")
       payload: { workflow: inferred_workflow, source_domain: domain,
                  strategy_id, ... }
```

### HandleMessage: approve_recommendation

```
Request: { recommendation_id, decision: "accept"|"reject", reason }

1. Look up recommendation by ID
2. If not found → error
3. If already decided → error (immutable decisions)

4. Update status:
   "accept" → "accepted"
   "reject" → "rejected" (store reason)

5. Publish:
   lifecycle.recommendation.accepted or .rejected (scope: invoker)

6. If accepted and recommendation belongs to a paused workflow:
   Publish: workflow.approval.decision (scope: "workflow")
     payload: { workflow_id, phase, decision: "accept" }
```

### HandleMessage: set_context

```
Request: EntityContext object

1. Validate structure
2. Store as the hub's entity context
3. Return stored context
```

### HandleMessage: get_context

```
1. Return current EntityContext
```

### Additional HandleMessage Actions

| Action | Purpose |
|--------|---------|
| `get_strategy` | Return a strategy by ID |
| `list_strategies` | List strategies (filterable by status, priority) |
| `get_observations` | Query observation history (by agent, target, strategy, time range) |
| `get_recommendations` | Query recommendations (by status, priority, agent) |
| `get_feedback` | Query feedback entries |
| `get_agent_metrics` | Return AgentMetrics for a specific agent or all agents |
| `record_feedback` | Manually record feedback for a recommendation |

## Storage

All data stored in flat-file JSONL:

```
.weblisk/data/lifecycle/
  strategies.jsonl          # Strategy records
  observations.jsonl        # Observation history
  recommendations.jsonl     # Recommendation records
  feedback.jsonl            # Feedback entries
  agent_metrics.jsonl       # Running agent metrics
  entity_context.json       # Current entity context (single file)
```

Retention defaults:
- Observations: 90 days
- Recommendations: 90 days
- Feedback: 180 days
- Strategies: indefinite
- Agent metrics: indefinite (running aggregates)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_LIFECYCLE_PORT` | `9782` | Listen port |
| `WL_LIFECYCLE_MAX_CONCURRENT` | `20` | Max concurrent event processing |
| `WL_LIFECYCLE_DATA_DIR` | `.weblisk/data/lifecycle` | Storage directory |
| `WL_LIFECYCLE_OBS_RETENTION` | `7776000` | Observation retention (seconds, 90d) |
| `WL_LIFECYCLE_REC_RETENTION` | `7776000` | Recommendation retention (seconds, 90d) |
| `WL_LIFECYCLE_FB_RETENTION` | `15552000` | Feedback retention (seconds, 180d) |

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| `lifecycle_observations_total` | counter | Observations recorded by agent |
| `lifecycle_recommendations_total` | counter | Recommendations by status and priority |
| `lifecycle_approvals_total` | counter | Approval decisions by outcome |
| `lifecycle_feedback_total` | counter | Feedback entries by signal type |
| `lifecycle_strategy_progress` | gauge | Current progress per strategy |
| `lifecycle_agent_accuracy` | gauge | Per-agent recommendation accuracy |

## Verification Checklist

- [ ] Subscribes to workflow.completed (scope: "*") and extracts observations + recommendations
- [ ] Subscribes to workflow.failed (scope: "*") and records failure observations
- [ ] Strategies created via create_strategy message action
- [ ] Strategy decomposition maps targets to domains and publishes workflow.trigger
- [ ] Observations stored with measurements, findings, and strategy links
- [ ] Recommendations created with priority, impact, and pending status
- [ ] Auto-approval applied when domain approval is "auto" and priority != "critical"
- [ ] Human approval via approve_recommendation message action
- [ ] Accepted recommendations trigger workflow.approval.decision for paused workflows
- [ ] Agent metrics updated after every workflow completion
- [ ] Strategy progress recalculated from latest observations
- [ ] Entity context stored and retrievable via set_context/get_context
- [ ] All data persisted to flat-file JSONL storage
- [ ] Lifecycle events published for every state transition
