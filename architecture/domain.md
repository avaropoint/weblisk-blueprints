<!-- blueprint
type: architecture
name: domain
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/agent, architecture/orchestrator]
platform: any
-->

# Weblisk Domain Controller Architecture

A domain controller is the business intelligence layer of the Weblisk
architecture. It sits between the orchestrator and work agents —
receiving business-level tasks, decomposing them into discrete work
units, dispatching those units to specialised agents, aggregating
results, and feeding outcomes back into the continuous optimization
lifecycle.

Nothing enters or leaves a business function without the domain
controller's knowledge and approval. It is the director: it
understands the process, the rules, the data contracts, and the
quality gates that make each business function operate correctly.

## Relationship to Other Components

```
┌──────────────────────────────────────────────────────┐
│                    Orchestrator                       │
│    Registration · Routing · Security · Discovery      │
└────────────┬────────────────────┬────────────────────┘
             │ task               │ task
             ▼                    ▼
  ┌─────────────────┐  ┌─────────────────┐
  │  SEO Domain      │  │  Ops Domain      │
  │  (controller)    │  │  (controller)    │
  └──┬──────┬───────┘  └──┬──────┬───────┘
     │      │              │      │
     ▼      ▼              ▼      ▼
  ┌─────┐┌─────┐       ┌─────┐┌─────┐
  │ seo ││a11y │       │ cron││email│
  │ anlz││chkr │       │ agnt││agnt │
  └─────┘└─────┘       └─────┘└─────┘
   work     work       infra   infra
  agents   agents      agents  agents
```

**Orchestrator** — Coordinates between domains. Manages registration,
discovery, security, and audit for the entire system.

**Domain controller** — Directs a business function. Owns one or more
workflows, dispatches to agents, aggregates results, enforces quality
gates. A domain IS an agent (implements the same 5 protocol endpoints)
but with additional responsibilities.

**Work agents** — Perform specific tasks dispatched by a domain. They
have no independent initiative — they receive input, execute, return
output.

**Infrastructure agents** — System-level utilities (sync, cron, webhook,
email). Any domain or the orchestrator can use them. They are not owned
by a specific domain.

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
  "workflows": ["seo-audit", "seo-optimize"]
}
```

### Domain-Specific Manifest Fields

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Type | string | `type` | yes | MUST be `"domain"` |
| RequiredAgents | []string | `required_agents` | yes | Agent names this domain dispatches to |
| Workflows | []string | `workflows` | yes | Workflow names this domain supports |

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

When a domain controller receives a task via `POST /v1/execute`:

```
Phase 1 — Select workflow:
  Match task.action against workflow triggers.
  If no match → return failed result: "unknown action"

Phase 2 — Initialize execution:
  Create WorkflowExecution record:
    id: generateID()
    workflow_name: matched workflow name
    domain_name: this domain's name
    task_id: task.id
    status: "running"
    started_at: now()
    phases: [] (populated as phases complete)

Phase 3 — Resolve execution order:
  Topological sort of phases by depends_on.
  Group into execution levels: L0 (no deps), L1 (depend on L0), etc.
  Verify no cycles (fail if circular dependency detected).

Phase 4 — Execute levels:
  For each level (L0, L1, L2, ...):
    For each phase in this level (concurrently):

      a. Check condition (if set) — skip if falsy
      b. Resolve input references from task payload + previous outputs
      c. If agent = "self":
           Execute domain's own HandleMessage(action, resolved_input)
         Else:
           Look up agent in service directory
           If not found → fail phase or retry
           Build AgentMessage:
             from: this domain's name
             to: agent name
             action: phase.action
             payload: resolved_input
           Sign message with domain's private key
           POST to agent_url + /v1/message
           Wait for response (with timeout)
      d. Store phase result:
           {phase_name, agent_name, status, result, started_at, completed_at}
      e. If failed:
           Apply on_error strategy (fail workflow / skip / retry)

Phase 5 — Aggregate:
  Collect all phase results.
  Build final TaskResult:
    task_id: original task ID
    agent_name: this domain's name
    status: "success" | "failed" | "pending_approval"
    summary: human-readable summary of all phases
    changes: merged ProposedChange list from all phases
    observations: merged Observation list from all phases
    recommendations: merged Recommendation list from all phases
    metrics: {phases_total, phases_completed, phases_failed, duration_ms}
  Sign result with domain's private key.

Phase 6 — Record:
  Store WorkflowExecution with all phase results.
  Emit observations and recommendations (for lifecycle tracking).
  Return TaskResult.
```

## Agent Dispatch

When a domain dispatches work to an agent, it uses direct messaging
(`POST /v1/message`), not the orchestrator's task endpoint. This
keeps the orchestrator as a coordinator and the domain as the executor.

```
Domain dispatch to agent:
  1. Look up agent in service directory (populated during registration
     and updated via /v1/services broadcasts)
  2. Build AgentMessage:
     - from: domain name
     - to: agent name
     - type: "request"
     - action: the workflow phase action
     - payload: resolved input data
  3. Sign: JSON.stringify({from, to, action, payload})
  4. POST to agent_url + /v1/message
  5. Parse response AgentMessage
  6. Extract response.payload as phase output
  7. If agent unreachable:
     a. Check if channel exists → use channel
     b. Request new channel from orchestrator → retry
     c. If still unreachable → fail phase
```

If a domain needs authenticated communication, it requests a channel
through the orchestrator (`POST /v1/channel`) and uses the channel
token for subsequent messages.

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

Invoked by the orchestrator via `POST /v1/execute`. Runs a named
workflow and returns aggregated results. This is the primary entry point.

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

### get_workflows

Returns full workflow definitions. This is the runtime introspection
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
| (future domains) | 9701–9709 |

Work agents use ports 9710+. Infrastructure agents use 9750+.
Orchestrator: 9800.

## Implementation Notes

- **Domain as agent**: A domain controller implements the same 5
  protocol endpoints as any agent. The additional workflow logic
  lives in `Execute` and `HandleMessage`.
- **Workflow engine**: The workflow execution loop (resolve order,
  dispatch phases, collect results) is generic. A single implementation
  can serve any domain — only the workflow definitions and aggregation
  rules are domain-specific.
- **Parallelism**: Phases at the same dependency level SHOULD execute
  concurrently. This is critical for performance — a domain with 4
  independent phases should not serialize them.
- **State**: Workflow execution state SHOULD be persisted so that
  workflows survive restarts. At minimum, log completed phase results
  so a restarted workflow can skip already-completed phases.
- **Timeout cascade**: A workflow-level timeout SHOULD be enforced in
  addition to per-phase timeouts. If the entire workflow exceeds its
  timeout, all remaining phases are cancelled.
- **Idempotency**: Phases SHOULD be idempotent. If a phase is retried
  (due to error or restart), the agent should produce the same output
  for the same input.
- **No bypass**: Business tasks MUST flow through domain controllers.
  Work agents do not accept tasks from arbitrary sources — only from
  their owning domain. Infrastructure agents accept tasks from any
  authenticated source.

## Verification Checklist

- [ ] Domain registers with `type: "domain"` in manifest
- [ ] Orchestrator tracks domain status based on required_agents availability
- [ ] Domain dispatches phases to agents via `POST /v1/message`
- [ ] Phases with `depends_on` wait for dependencies before executing
- [ ] Phases at the same level execute concurrently
- [ ] Phase outputs are resolvable via `$phases.<name>.output` references
- [ ] Failed phases respect `on_error` strategy (fail, skip, retry)
- [ ] `agent: "self"` phases execute within the domain controller
- [ ] Results from all phases are aggregated into a single TaskResult
- [ ] Observations and recommendations are emitted per workflow
- [ ] Domain responds to `get_status` with agent availability
- [ ] Domain responds to `get_workflows` with available workflows
- [ ] WorkflowExecution is recorded with all phase results
- [ ] Workflow timeout cancels all remaining phases
- [ ] Approval gates pause execution until approval is received
