<!-- blueprint
type: architecture
name: domain
version: 1.0.0
requires: [protocol/identity, protocol/types, architecture/agent, architecture/orchestrator, patterns/messaging, patterns/workflow]
platform: any
tier: free
-->

# Weblisk Domain Controller Architecture

A domain controller is the business intelligence layer of the Weblisk
architecture. It owns the workflow definitions, entity context, and
business rules for a specific function. When triggered, it publishes
a `workflow.trigger` event — the Workflow Agent handles the actual
DAG execution and phase dispatch.

The domain controller knows WHAT needs to happen and WHY. The
infrastructure agents (Workflow, Task, Lifecycle) know HOW to
execute, dispatch, and optimise. This separation means domains are
pure business logic — no embedded execution engine.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519KeyPair
          fields_used: [public_key, private_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /v1/execute
          methods: [POST]
        - path: /v1/message
          methods: [POST]
        - path: /v1/event
          methods: [POST]
      types:
        - name: TaskRequest
          fields_used: [task_id, action, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary]
        - name: AgentManifest
          fields_used: [name, version, type, url, public_key, capabilities, required_agents, workflows, publishes, subscriptions]
        - name: EventEnvelope
          fields_used: [event_id, topic, payload, source, scope, correlation_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentContext
          fields_used: [identity, services, provider, workspace, token]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /v1/services
          methods: [POST]
      events:
        - topic: system.agent.registered
          fields_used: [agent_name, manifest]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/messaging
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: publish
          parameters: [topic, payload, source, scope]
        - behavior: subscribe
          parameters: [topic, handler, scope]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/workflow
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: workflow-declaration
          parameters: [phases, triggers, reference_expressions]
        - behavior: workflow-execution
          parameters: [dag_resolution, phase_dispatch, error_strategies]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

### Owns

- Workflow definitions (phase declarations, triggers, reference expressions)
- Entity context and domain-specific business rules
- Publishing `workflow.trigger` events to initiate multi-agent workflows
- Post-processing of workflow results (validation, conflict resolution, quality gates)
- Domain-specific HandleMessage actions (get_workflows, get_status, trigger_workflow)
- Domain manifest fields (`type: "domain"`, `required_agents`, `workflows`, `publishes`)

### Does NOT Own

- Workflow DAG execution (owned by Workflow Agent via `agents/workflow.md`)
- Task dispatch to work agents (owned by Task Agent via `agents/task.md`)
- Strategy management and lifecycle optimization (owned by Lifecycle Agent via `agents/lifecycle.md`)
- Agent registration or namespace enforcement (owned by orchestrator)
- Work agent implementation (each work agent is independently developed)

---

## Interfaces

The domain controller’s public API is the standard 6 protocol endpoints
(inherited from `architecture/agent`) plus domain-specific
`HandleMessage` actions defined in
[Domain HandleMessage Actions](#domain-handlemessage-actions):
`get_workflows`, `get_status`, `trigger_workflow`, `get_entity`,
`get_config`.

---

## Data Flow

See [Workflow Execution Flow](#workflow-execution-flow) for the full
sequence. Summary:

1. Domain receives task via `POST /v1/execute` with `action` field
2. Domain matches `action` against workflow triggers
3. Domain publishes `workflow.trigger` event (scope: workflow agent)
4. Returns immediate acknowledgment (`status: "accepted"`)
5. Workflow Agent resolves the DAG, Task Agent dispatches phases to work agents
6. Work agents execute via `POST /v1/execute` and return results
7. Domain receives `workflow.completed` event (scope: self) with aggregated output
8. Domain applies post-processing (validation, conflict resolution, quality gates)
9. Domain publishes domain-specific result event (e.g., `seo.audit.completed`)

---

## Relationship to Other Components

```
┌──────────────────────────────────────────────────────┐
│                    Orchestrator                       │
│    Registration · Namespaces · Security · Discovery    │
└────────────────────────┬─────────────────────────────┘
                         │ registers
     ┌─────────────────┬─────────┼──────────────────────┐
     ▼                 ▼         ▼                      ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐
│ SEO     │  │Workflow │  │ Task    │  │ Work Agents   │
│ Domain  │  │ Agent   │  │ Agent   │  │ (seo-analyzer,│
│(domain) │  │(infra)  │  │(infra)  │  │  a11y-checker)│
└────┬────┘  └────┬────┘  └────┬────┘  └───────────────┘
     │           │           │              ▲
     │ workflow.  │ task.     │ POST         │
     │ trigger    │ submit    │ /v1/execute  │
     └───────────►└───────────►└─────────────┘
              events           events     HTTP
```

**Orchestrator** — Trust anchor. Manages registration, namespace
ownership, security, and service directory distribution.

**Domain controller** — Directs a business function. Owns workflow
definitions and publishes `workflow.trigger` events. Receives results
via scoped `workflow.completed` events. A domain IS an agent
(implements the same 6 protocol endpoints) but with additional
responsibilities.

**Infrastructure agents** — Workflow Agent executes DAGs, Task Agent
dispatches individual phases, Lifecycle Agent manages strategies and
observations. They register like any other agent.

**Work agents** — Perform specific tasks dispatched by the Task Agent
via `POST /v1/execute`. They have no independent initiative — they
receive input, execute, return output.

## Domain Manifest

A domain controller registers with the orchestrator using the standard
`POST /v1/register` flow. Its manifest uses the same `AgentManifest`
structure with domain-specific fields:

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
    {"name": "target_files", "type": "file_list", "description": "Files to optimize"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated results with recommendations"}
  ],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["seo-analyzer", "a11y-checker"],
  "workflows": ["seo-audit", "seo-optimize"],
  "publishes": ["seo"],
  "subscriptions": [
    {"pattern": "workflow.completed", "scope": "self"},
    {"pattern": "workflow.failed", "scope": "self"},
    {"pattern": "system.agent.registered", "scope": "self"}
  ]
}
```

### Domain-Specific Manifest Fields

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Type | string | `type` | yes | MUST be `"domain"` |
| RequiredAgents | []string | `required_agents` | yes | Agent names this domain dispatches to |
| Workflows | []string | `workflows` | yes | Workflow names this domain supports |
| Publishes | []string | `publishes` | yes | Event namespaces (e.g., `["seo"]`) |
| Subscriptions | []Subscription | `subscriptions` | yes | Event patterns to receive |

The `type` field distinguishes domains from work agents (`"agent"`) and
infrastructure agents (`"infrastructure"`). The orchestrator uses this
for routing decisions and dependency tracking.

## Registration and Dependency Verification

Domain registration follows the standard protocol with additional
orchestrator behaviour:

```
1. Domain sends RegisterRequest (same as any agent)
2. Orchestrator verifies signature and identity (standard flow)
3. Orchestrator reads manifest.type = "domain"
4. Orchestrator reads manifest.required_agents
5. For each required agent:
   a. Check if agent is in the registry
   b. If ALL present: domain status = "online"
   c. If ANY missing: domain status = "degraded"
      Log warning: "domain 'seo' registered but missing agents: [a11y-checker]"
6. Issue token and respond (standard flow)
7. Broadcast service directory (standard flow)
```

When a missing agent registers later:
```
1. Agent registers normally
2. Orchestrator checks if any domain requires this agent
3. If yes and domain was "degraded":
   a. Re-evaluate: are all required agents now present?
   b. If yes: update domain status to "online"
   c. Notify domain via POST /v1/services with updated directory
```

This allows agents and domains to start in any order.

## Workflow Specification

> **Authoritative source:** [`patterns/workflow`](../patterns/workflow.md)
> defines the complete workflow declaration format, reference expression
> grammar, execution engine (6 phases), error strategies, approval
> gates, and workflow state machine. This section shows how domain
> controllers USE workflows — the pattern defines how they WORK.

Every domain defines one or more workflows — multi-step, multi-agent
processes that accomplish a business function. Workflows are defined in
the domain's blueprint file (in `domains/`), not in the runtime manifest
(which only lists workflow names).

### Workflow Structure

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
      metadata: $phases.scan.output.metadata
    output: analysis_results
    timeout: 120
    depends_on: [scan]

  - name: accessibility
    agent: a11y-checker
    action: check_images
    input:
      images: $phases.scan.output.images
    output: a11y_results
    timeout: 60
    depends_on: [scan]

  - name: synthesize
    agent: self
    action: aggregate_results
    input:
      analysis: $phases.analyze.output
      a11y: $phases.accessibility.output
    output: final_report
    depends_on: [analyze, accessibility]
    approval: required
```

### Reference Expression Syntax

Phase inputs use reference expressions to bind data from the task,
previous phase outputs, entity context, or domain configuration.

#### Grammar

```
expression   = "$" root "." path
root         = "task" | "phases" | "entity" | "config"
path         = segment ( "." segment )*
segment      = identifier | identifier "[" index "]" | identifier "[*]"
identifier   = [a-z_][a-z0-9_]*
index        = non-negative integer
```

#### Roots

| Root | Resolves to |
|------|-------------|
| `$task.payload.<key>` | Field from the original `TaskRequest.payload` |
| `$task.context.<key>` | Field from the `TaskContext` |
| `$phases.<name>.output` | Full output map of a completed phase |
| `$phases.<name>.output.<key>` | Specific key from a phase's output map |
| `$entity.<key>` | Field from `EntityContext` (injected via task context) |
| `$config.<key>` | Domain-specific configuration value (set at domain startup) |

#### Nested Path Access

Dot-separated segments traverse nested maps:

```
$phases.scan.output.files         → full "files" value
$phases.scan.output.summary.score → nested key "score" inside "summary"
```

#### Array Indexing

Bracket notation accesses array elements:

```
$phases.scan.output.files[0]      → first element
$phases.scan.output.files[2]      → third element
```

Index out of bounds resolves to `null`.

#### Array Expansion

The `[*]` wildcard expands all elements of an array, collecting a
nested field from each element into a new array:

```
$phases.scan.output.files[*].metadata.images
```

This collects the `metadata.images` value from every element in the
`files` array, producing a flat array of all images across all files.

If the source is not an array, `[*]` resolves to `null`.

#### Resolution Rules

1. Expressions MUST start with `$` — literal strings without `$` are
   passed through as-is (this allows mixing references with constants).
2. If a reference cannot be resolved (missing key, null intermediate,
   index out of bounds), the value resolves to `null`.
3. `null` resolution is NOT an error — the receiving agent MUST handle
   missing optional inputs gracefully.
4. If a required input resolves to `null`, the domain controller SHOULD
   fail the phase with error: `"unresolved reference: <expression>"`.
5. No type coercion is performed — the resolved JSON value is passed
   as-is. If an agent expects a string and receives an array, the agent
   returns an error.
6. Circular references (a phase referencing its own output) are
   impossible by construction — `depends_on` creates a DAG.

#### Examples

```yaml
input:
  # Literal value (no $ prefix) — passed as-is
  mode: "full"

  # Task payload field
  html_files: $task.payload.files

  # Nested access into a phase output
  metadata: $phases.scan.output.files

  # Single element
  first_file: $phases.scan.output.files[0]

  # Array expansion — collect images from all scanned files
  all_images: $phases.scan.output.files[*].metadata.images

  # Entity context
  brand_tone: $entity.tone

  # Domain config
  max_issues: $config.max_issues_per_file
```

### Phase Fields

See [WorkflowPhase](../protocol/types.md) for the canonical type
definition. The table below summarises fields with domain-specific
usage notes; types.md is authoritative for field names, types, and
JSON keys.

| Field | Required | Domain Usage Notes |
|-------|----------|--------------------|
| name | yes | Unique identifier within this workflow |
| agent | yes | Target agent name, or `"self"` for domain-internal logic |
| action | yes | `HandleMessage` action to invoke on target |
| input | yes | Reference expressions (see grammar above) |
| output | yes | Key name for phase result — used in `$phases.<output>` references |
| depends_on | no | Phases that must complete first; drives execution order |
| timeout | no | Phase timeout in seconds (default: 300) |
| approval | no | `"required"` or `"auto"` (default: `"auto"`) |
| on_error | no | `"fail"` (default), `"skip"`, or `"retry"` |
| max_retries | no | Retry count when on_error = `"retry"` (default: 0; see types.md) |
| condition | no | Expression that must be truthy to execute phase |

### Execution Order

Phases execute in dependency order:

1. Phases with no `depends_on` run first (in parallel if multiple)
2. A phase starts only after ALL of its `depends_on` phases complete
3. If a phase fails and `on_error` = `"fail"`, the entire workflow fails
4. If `on_error` = `"skip"`, the phase is marked skipped and dependents
   proceed without its output
5. If `on_error` = `"retry"`, the phase retries up to `max_retries`
   with 1-second, 2-second, 4-second backoff
6. Phases with `agent: "self"` execute within the domain controller
   itself (for aggregation, validation, and decision logic)
7. If `approval: "required"`, execution pauses until approval is
   received before exposing results

## Workflow Execution Flow

When a domain controller receives a task via `POST /v1/execute`, it
publishes a `workflow.trigger` event. The Workflow Agent handles all
DAG execution. The domain receives the result via a scoped
`workflow.completed` event.

```
Phase 1 — Select workflow:
  Match task.action against workflow triggers.
  If no match → return failed result: "unknown action"

Phase 2 — Publish workflow trigger:
  publish("workflow.trigger", {
    workflow: matched_workflow_name,
    source_domain: this domain's name,
    input: task.payload,
    callback_topic: "<domain>.workflow.result",
    entity: entity_context,
    config: domain_config
  }, scope: "workflow", correlation_id: task.id)

Phase 3 — Return acknowledgment:
  Return TaskResult:
    task_id: task.id
    agent_name: this domain's name
    status: "accepted"
    summary: "Workflow '<name>' triggered, awaiting completion"

Phase 4 — Receive result (async):
  The domain subscribes to workflow.completed (scope: "self").
  When the Workflow Agent finishes the DAG, it publishes:
    workflow.completed (scope: domain_name)
  The domain's event handler receives the aggregated result.

Phase 5 — Post-processing:
  Apply domain-specific validation rules to the result:
  - Reject conflicting recommendations
  - Enforce business constraints
  - Apply quality gates
  Publish domain-specific result event if needed:
    seo.audit.completed (scope: as needed)
```

See [patterns/workflow](../patterns/workflow.md) for the complete
workflow execution engine specification.

## Agent Dispatch

Domains do NOT dispatch work to agents directly.
The domain publishes a `workflow.trigger` event, the Workflow Agent
resolves the DAG, and the Task Agent dispatches individual phases to
work agents via `POST /v1/execute`.

Domains still use `POST /v1/message` for:
- Responding to introspection queries (get_workflows, get_status)
- `agent: "self"` phases (the Workflow Agent messages the domain
  for domain-internal aggregation logic)
- Ad-hoc collaboration with other agents or domains

If a domain needs authenticated communication with another agent, it
requests a channel through the orchestrator (`POST /v1/channel`) and
uses the channel token for subsequent messages.

## Result Aggregation

The domain controller is responsible for merging results from multiple
agents into a coherent outcome. Aggregation rules are domain-specific
but follow a standard pattern:

```
1. Collect all phase outputs
2. Merge observations: concatenate, deduplicate by target+element
3. Merge recommendations: concatenate, sort by priority, deduplicate
4. Merge proposed changes: group by file path, apply in order
5. Compute summary metrics:
   - Total observations across all agents
   - Total recommendations by priority
   - Total proposed changes by action type
   - Workflow duration, agent response times
6. Apply domain-specific validation rules:
   - Reject conflicting recommendations
   - Enforce business constraints
   - Apply quality gates
7. Set overall status:
   - "success" if all phases completed and no approval needed
   - "pending_approval" if any phase or the workflow requires approval
   - "failed" if any critical phase failed
```

## Domain HandleMessage Actions

Every domain controller MUST implement these standard actions:

### execute_workflow

Invoked via `POST /v1/execute`. Publishes a `workflow.trigger` event
for the matched workflow and returns an acknowledgment. The Workflow
Agent handles execution and publishes `workflow.completed` back to
the domain.

### get_status

Returns the domain's current state:
```json
{
  "status": "online",
  "required_agents": {"seo-analyzer": "online", "a11y-checker": "online"},
  "active_workflows": 2,
  "completed_workflows": 47,
  "failed_workflows": 3
}
```

### get_workflow

Returns a specific workflow definition by name. Used by the Workflow
Agent to fetch the DAG definition when executing a triggered workflow.

**Request payload:** `{"name": "seo-audit"}`
**Response:** Single `WorkflowDefinition` object.

### get_workflows

Returns all workflow definitions. This is the runtime introspection
endpoint — it allows the orchestrator, CLI, and external tools to
discover a domain's capabilities without parsing markdown blueprints.

**Response:** Array of `WorkflowDefinition` objects (see [types.md](../protocol/types.md)):

```json
{
  "workflows": [
    {
      "name": "seo-audit",
      "description": "Full SEO audit — scan, analyze, check accessibility, report",
      "trigger": "audit",
      "phases": [
        {"name": "scan", "agent": "seo-analyzer", "action": "scan_html", "depends_on": [], "timeout": 60},
        {"name": "analyze", "agent": "seo-analyzer", "action": "analyze_metadata", "depends_on": ["scan"], "timeout": 120},
        {"name": "accessibility", "agent": "a11y-checker", "action": "check_images", "depends_on": ["scan"], "timeout": 60},
        {"name": "report", "agent": "seo-analyzer", "action": "generate_report", "depends_on": ["analyze", "accessibility"], "approval": "required"}
      ]
    }
  ]
}
```

Domain controllers that serve as HTTP endpoints MAY also expose this
as `GET /v1/workflows` (no auth required) for static discovery:

```
GET /v1/workflows → {"workflows": [...WorkflowDefinition]}
```

This is optional — the `get_workflows` message action is the canonical
introspection mechanism.

### workflow_history

Returns recent workflow executions with results:
```json
{
  "executions": [
    {"id": "abc123", "workflow": "seo-audit", "status": "success", "started_at": 1713264000}
  ]
}
```

Custom actions are domain-specific and defined in each domain's
blueprint file.

## Domain Context

Domains operate within the context of a business entity. The
`EntityContext` (see [protocol/types.md](../protocol/types.md)) provides:

- Entity identity (name, type, industry)
- Market positioning and brand voice
- Target audiences and their pain points
- Competitors
- Core keywords and topics
- Digital assets

Every domain SHOULD use entity context to ground its decisions in
business reality. For example, an SEO domain uses keywords and
audiences to evaluate whether page titles target the right terms.

Entity context is injected via `TaskContext.entity` on every task
execution.

## Domain Configuration

Domains MAY accept configuration values at startup via environment
variables or configuration files. These values are accessible in
workflow reference expressions as `$config.<key>`.

```bash
# Environment variables (prefix WL_DOMAIN_)
WL_DOMAIN_MAX_ISSUES_PER_FILE=50
WL_DOMAIN_SCORE_THRESHOLD=70
WL_DOMAIN_MEASUREMENT_WINDOW=86400
```

Within the domain controller, configuration is stored as a flat
`map[string]any` and made available to the reference resolver:

```yaml
input:
  max_issues: $config.max_issues_per_file
  threshold: $config.score_threshold
```

Domain configuration is NOT part of the manifest or wire protocol —
it is local to the domain process. Each domain blueprint SHOULD
document its supported configuration keys.

## Port Assignment Convention

Domains use ports in the 9700–9709 range:

| Domain | Port |
|--------|------|
| seo | 9700 |
| content | 9701 |
| health | 9702 |
| security | 9703 |
| (custom domains) | 9704–9709 |

Work agents use ports 9710+. Infrastructure agents use 9750+.
Orchestrator: 9800.

## Types

### DomainWorkflow

A workflow definition owned by a domain controller. Specifies the
business process as a set of phases that the Workflow Agent executes.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Workflow identifier (unique within domain) |
| Description | string | `description` | no | Human-readable purpose |
| Trigger | string | `trigger` | yes | Action name that initiates this workflow |
| Phases | []WorkflowPhase | `phases` | yes | Ordered list of execution phases |
| OnError | string | `on_error` | no | Default phase error strategy: `fail`, `skip`, `retry` (default: `fail`) |

### DomainManifest

Extended manifest fields specific to domain controllers. These fields
augment the base `AgentManifest` when `type` is `"domain"`.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| RequiredAgents | []string | `required_agents` | yes | Work agents this domain depends on |
| Workflows | []string | `workflows` | yes | Workflow names this domain supports |
| EntityTypes | []string | `entity_types` | no | Entity types this domain manages |

---

## Implementation Notes

- **Domain as agent**: A domain controller implements the same 6
  protocol endpoints as any agent. The additional business logic
  lives in `Execute` (workflow triggering) and `HandleMessage`
  (introspection, self-phases) and `HandleEvent` (receiving
  workflow results).
- **No embedded workflow engine**: Domains declare workflows but do
  not execute them. The Workflow Agent fetches definitions via
  `get_workflow` message and handles DAG resolution, phase dispatch,
  and result aggregation.
- **Event-driven results**: Domains subscribe to `workflow.completed`
  and `workflow.failed` (scope: self) to receive execution results
  asynchronously.
- **State**: Workflow execution state is owned by the Workflow Agent.
  Domains store domain-specific state (entity context, configuration,
  business rules) in flat-file storage.
- **Idempotency**: Workflow triggers SHOULD be idempotent. The domain
  generates a correlation_id per trigger that the Workflow Agent uses
  to detect duplicate requests.
- **No bypass**: Business tasks SHOULD flow through domain controllers.
  Work agents accept tasks from the Task Agent (dispatched as part of
  a workflow) or from direct messages for ad-hoc collaboration.

## Verification Checklist

- [ ] Domain registers with `type: "domain"` and `publishes` namespace in manifest
- [ ] Orchestrator tracks domain status based on required_agents availability
- [ ] Domain publishes `workflow.trigger` event for matched task actions
- [ ] Domain subscribes to `workflow.completed` and `workflow.failed` (scope: self)
- [ ] Domain responds to `get_workflow` with a specific workflow definition
- [ ] Domain responds to `get_workflows` with all available workflows
- [ ] Domain responds to `get_status` with agent availability
- [ ] Domain applies post-processing validation to workflow results
- [ ] Domain publishes domain-specific result events when appropriate
- [ ] Entity context grounded in business reality via EntityContext
- [ ] Domain configuration accessible via `$config.<key>` references
- [ ] HandleEvent processes workflow.completed and workflow.failed events
