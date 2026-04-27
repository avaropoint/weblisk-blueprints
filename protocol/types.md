<!-- blueprint
type: protocol
name: types
version: 1.0.0
requires: []
platform: any
tier: free
-->

# Weblisk Protocol Types

Canonical type definitions for the Weblisk Agent Protocol v1. Every
implementation — regardless of language — MUST use these exact field
names, types, and JSON serialization keys. These types define the
universal contract between agents, orchestrators, and tools.

## Overview

All types are defined in language-agnostic notation. JSON is the
wire format. Implementations MUST serialize to and deserialize from
JSON using the exact field names shown in the `json` column.

## Conventions

- All timestamps are Unix epoch seconds (`int64`)
- All IDs are 32-character hex strings (16 random bytes)
- All signatures are hex-encoded Ed25519 signatures (128 hex chars)
- All public keys are hex-encoded Ed25519 public keys (64 hex chars)
- Optional fields MAY be omitted from JSON when empty/null
- Unknown fields MUST be ignored (forward compatibility)

---

## Dependencies

```yaml
requires: []
  # protocol/types is the root type registry — it has no dependencies.
  # All other blueprints depend on this file.
```

---

## Errors

All error responses use a structured format. Simple error strings
(`{"error": "message"}`) are still valid for backward compatibility,
but implementations SHOULD use the full `ErrorResponse` when
category and retry information are available.

### ErrorResponse

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Error | string | `error` | yes | Human-readable error message |
| Code | string | `code` | no | Machine-readable error code (e.g., `AGENT_UNREACHABLE`, `INVALID_INPUT`) |
| Category | string | `category` | no | `"transient"`, `"permanent"`, or `"partial"` |
| Retryable | bool | `retryable` | no | Whether the caller SHOULD retry this request |
| Detail | map | `detail` | no | Additional structured context (varies by error) |

**Categories:**
- `transient` — Temporary failure; retry is safe. Examples: network timeout, agent overloaded, upstream 503.
- `permanent` — Will not succeed on retry. Examples: invalid input, capability not available, unknown action.
- `partial` — Request partially succeeded. `detail` SHOULD include `completed` and `failed` sub-results.

**Standard error codes:**

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `INVALID_REQUEST` | 400 | permanent | Missing or malformed fields |
| `INVALID_SIGNATURE` | 401 | permanent | Ed25519 signature verification failed |
| `TOKEN_EXPIRED` | 401 | transient | Token past expiry — re-register to get a new one |
| `FORBIDDEN` | 403 | permanent | Missing required capability |
| `NOT_FOUND` | 404 | permanent | Agent or resource not in registry |
| `RATE_LIMITED` | 429 | transient | Too many requests — respect `Retry-After` header |
| `INTERNAL_ERROR` | 500 | transient | Unexpected server error |
| `AGENT_UNREACHABLE` | 502 | transient | Orchestrator could not reach target agent |
| `AGENT_TIMEOUT` | 504 | transient | Target agent did not respond within timeout |
| `UNSUPPORTED_VERSION` | 400 | permanent | Agent requested an unsupported protocol version |
| `NAMESPACE_CONFLICT` | 409 | permanent | Requested publish namespace already owned by another agent |
| `NAMESPACE_RESERVED` | 403 | permanent | Requested namespace is reserved (e.g., `system.*`) |
| `SCOPE_UNAUTHORIZED` | 403 | permanent | Subscription scope requires missing capability or collaborator relationship |
| `EVENT_REJECTED` | 400 | permanent | Event envelope is malformed or topic is unowned |
| `PHASE_FAILED` | 500 | varies | Workflow phase failed — check `detail.phase_name` |
| `PARTIAL_FAILURE` | 207 | partial | Some phases succeeded, some failed |

### AgentManifest

Describes an agent's identity, capabilities, and interface contract.
Returned by `POST /v1/describe` and sent during registration.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Agent identifier (lowercase, no spaces) |
| Type | string | `type` | no | `"domain"`, `"agent"` (default), or `"infrastructure"` |
| Version | string | `version` | yes | Semver version of the agent |
| ProtocolVersion | string | `protocol_version` | no | Protocol version this agent implements (default: `"1"`) |
| Description | string | `description` | yes | Human-readable purpose |
| URL | string | `url` | yes | Agent's HTTP base URL |
| PublicKey | string | `public_key` | yes | Hex-encoded Ed25519 public key |
| Capabilities | []Capability | `capabilities` | yes | What this agent can do |
| Inputs | []IOSpec | `inputs` | no | Expected input parameters |
| Outputs | []IOSpec | `outputs` | no | What this agent produces |
| Collaborators | []string | `collaborators` | no | Agent names this agent works with |
| Approval | string | `approval` | no | `"required"` or `"auto"` (default: `"required"`) |
| RequiredAgents | []string | `required_agents` | no | Agents this domain needs (domain type only) |
| Workflows | []string | `workflows` | no | Workflow names supported (domain type only) |
| MaxConcurrent | int | `max_concurrent` | no | Max concurrent executions (advisory; default: 5) |
| Publishes | []string | `publishes` | no | Namespace patterns this agent may publish to (e.g., `["workflow.*"]`). The orchestrator enforces exclusive ownership — no two agents may claim the same namespace. See [spec.md — Namespace Control](spec.md#namespace-control). |
| Subscriptions | []Subscription | `subscriptions` | no | Event subscription declarations. Each entry specifies a topic pattern, optional consumer group, scope, and concurrency limit. See [spec.md — Event Scoping](spec.md#event-scoping). |

### Capability

A single thing an agent can do, with optional resource scoping.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Capability identifier (e.g., `file:read`) |
| Resources | []string | `resources` | no | Glob patterns scoping the capability |

**Standard capabilities:**
- `file:read` — read files (resources: glob patterns)
- `file:write` — write/modify files
- `llm:chat` — use LLM for analysis
- `agent:message` — communicate with other agents
- `workflow:execute` — execute multi-agent workflows (domain controllers)
- `http:get` — make external HTTP requests
- `http:send` — make outbound HTTP requests
- `http:receive` — receive inbound HTTP requests
- `database:read` — read from data store
- `database:write` — write to data store
- `realtime:publish` — publish to real-time channels

### IOSpec

Describes an input or output parameter.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Parameter name |
| Type | string | `type` | yes | Data type: `file_list`, `json`, `text` |
| Description | string | `description` | yes | Human-readable description |

---

## Workflows

Types used by domain controllers to define and execute multi-phase,
multi-agent workflows. [`patterns/workflow`](../patterns/workflow.md)
is the authoritative source for workflow declaration format, reference
expression grammar, execution engine, error strategies, and state
machine. See `architecture/domain.md` for the domain controller
specification that consumes these types.

### WorkflowDefinition

Declared in domain blueprint files. Describes a multi-phase process
that a domain controller can execute.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Workflow identifier (lowercase, hyphens) |
| Description | string | `description` | yes | What this workflow does |
| Trigger | string | `trigger` | yes | Task action that invokes this workflow |
| Phases | []WorkflowPhase | `phases` | yes | Ordered execution steps |

### WorkflowPhase

A single step in a workflow. Each phase dispatches to one agent.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Phase identifier (unique within workflow) |
| Agent | string | `agent` | yes | Target agent name |
| Action | string | `action` | yes | `HandleMessage` action to invoke |
| Input | map | `input` | no | Input mapping — reference expressions resolve at runtime (see [Reference Expression Syntax](../architecture/domain.md#reference-expression-syntax)) |
| Output | string | `output` | no | Key name under which this phase's result is stored |
| DependsOn | []string | `depends_on` | no | Phase names that must complete first. Phases without dependencies MAY run in parallel |
| Timeout | int | `timeout` | no | Phase timeout in seconds (default: 300) |
| Approval | string | `approval` | no | `"required"` or `"auto"` (default: `"auto"`) |
| OnError | string | `on_error` | no | `"fail"` (default), `"skip"`, or `"retry"` |
| MaxRetries | int | `max_retries` | no | Retry count when `on_error` = `"retry"` (default: 0) |
| Condition | string | `condition` | no | Expression evaluated at runtime; phase is skipped if false |

**Input reference syntax:** See [Reference Expression Syntax](../architecture/domain.md#reference-expression-syntax) for the full grammar, including nested access, array indexing (`[0]`), array expansion (`[*]`), and resolution rules.

### WorkflowExecution

Runtime state of a workflow in progress or completed.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique execution identifier |
| WorkflowName | string | `workflow_name` | yes | Which workflow is executing |
| DomainName | string | `domain_name` | yes | Executing domain controller |
| TaskID | string | `task_id` | yes | Originating task ID |
| Status | string | `status` | yes | `pending`, `running`, `completed`, `failed` |
| Phases | []PhaseResult | `phases` | yes | Results per phase |
| StartedAt | int64 | `started_at` | yes | Unix epoch seconds |
| CompletedAt | int64 | `completed_at` | no | Unix epoch seconds |

### PhaseResult

Tracks the outcome of a single workflow phase.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| PhaseName | string | `phase_name` | yes | Phase identifier |
| AgentName | string | `agent_name` | yes | Agent that executed this phase |
| Status | string | `status` | yes | `pending`, `running`, `completed`, `failed`, `skipped` |
| Output | map | `output` | no | Phase output data (referenced by subsequent phases) |
| StartedAt | int64 | `started_at` | no | Unix epoch seconds |
| CompletedAt | int64 | `completed_at` | no | Unix epoch seconds |
| Error | string | `error` | no | Error message if failed |
| Retries | int | `retries` | no | Number of retry attempts |

---

## Strategy

A strategy declares a business objective with measurable targets.
Multiple strategies run in parallel. The orchestrator decomposes
each into prioritized tasks assigned to domain agents.

### Strategy

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique hex identifier |
| Name | string | `name` | yes | Strategy name |
| Objective | string | `objective` | yes | What this strategy aims to achieve |
| Targets | []StrategyTarget | `targets` | yes | Measurable goals |
| Priority | int | `priority` | yes | 1 = highest priority |
| Status | string | `status` | yes | `active`, `paused`, `completed` |
| CreatedAt | int64 | `created_at` | yes | Unix epoch seconds |
| UpdatedAt | int64 | `updated_at` | yes | Unix epoch seconds |
| Metadata | map | `metadata` | no | Arbitrary key-value data |

### StrategyTarget

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Metric | string | `metric` | yes | What is being measured |
| Current | float64 | `current` | yes | Current value |
| Goal | float64 | `goal` | yes | Target value |
| Deadline | string | `deadline` | yes | ISO 8601 date |
| Unit | string | `unit` | yes | Unit of measurement |
| Progress | float64 | `progress` | yes | 0.0 to 1.0 |

---

## Entity Context

The entity being optimized — a company, person, or project.
This grounds every agent's decisions in business reality.

### EntityContext

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Entity name |
| Type | string | `type` | yes | `company`, `person`, `project`, `site` |
| Industry | string | `industry` | yes | Industry/sector |
| Description | string | `description` | yes | What the entity does |
| Positioning | string | `positioning` | yes | Market positioning statement |
| Audiences | []Audience | `audiences` | no | Target audiences |
| Competitors | []Competitor | `competitors` | no | Known competitors |
| Keywords | []string | `keywords` | no | Core keywords/topics |
| Tone | string | `tone` | no | Brand voice (e.g., `professional`, `casual`) |
| Geography | string | `geography` | no | Primary geography |
| Assets | []Asset | `assets` | no | Known digital assets |
| Metadata | map | `metadata` | no | Arbitrary key-value data |

### Audience

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Audience segment name |
| Description | string | `description` | yes | Who they are |
| PainPoints | []string | `pain_points` | no | Their challenges |
| Keywords | []string | `keywords` | no | Terms they search for |

### Competitor

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Competitor name |
| URL | string | `url` | no | Competitor URL |
| Notes | string | `notes` | no | Competitive notes |

### Asset

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Path | string | `path` | yes | File path or URL |
| Type | string | `type` | yes | Asset type |
| Purpose | string | `purpose` | no | What this asset is for |

---

## Task Protocol

### TaskRequest

Sent to an agent's `POST /v1/execute` endpoint by the Task Agent,
or dispatched as part of a workflow phase.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique task identifier |
| From | string | `from` | yes | Who initiated (`user` or agent name) |
| Action | string | `action` | yes | What to do (`execute`, custom actions) |
| Payload | map | `payload` | yes | Task-specific data |
| Context | TaskContext | `context` | yes | Runtime context |
| StrategyID | string | `strategy_id` | no | Associated strategy |
| Token | string | `token` | yes | Auth token |
| Signature | string | `signature` | no | Ed25519 signature of payload |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

### TaskContext

Runtime context provided with every task execution.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| WorkspaceRoot | string | `workspace_root` | yes | Absolute path to project root |
| Services | []ServiceEntry | `services` | yes | Current service directory |
| Entity | EntityContext | `entity` | no | Entity being optimized |
| Config | map | `config` | no | Additional configuration |
| TraceID | string | `trace_id` | no | Correlation ID for distributed tracing (propagated through all downstream calls) |

### TaskResult

Returned by an agent after task execution.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| TaskID | string | `task_id` | yes | Matches request ID |
| AgentName | string | `agent_name` | yes | Which agent produced this |
| Status | string | `status` | yes | `success`, `failed`, `pending_approval` |
| Summary | string | `summary` | yes | Human-readable summary |
| Changes | []ProposedChange | `changes` | no | File modifications |
| Observations | []Observation | `observations` | no | Measurements taken |
| Recommendations | []Recommendation | `recommendations` | no | Suggested actions |
| Metrics | map | `metrics` | no | Execution metrics |
| Signature | string | `signature` | no | Ed25519 signature |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

### ProposedChange

A file modification proposed by an agent.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Path | string | `path` | yes | Relative file path |
| Action | string | `action` | yes | `create`, `modify`, `delete` |
| Original | string | `original` | no | Original file content |
| Modified | string | `modified` | no | Modified file content |
| Diffs | []ChangeDiff | `diffs` | no | Element-level changes |

### ChangeDiff

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Element | string | `element` | yes | What changed (e.g., `title`) |
| Before | string | `before` | yes | Previous value |
| After | string | `after` | yes | New value |
| Reason | string | `reason` | yes | Why this change was made |

---

## Observations

Structured measurements captured every time an agent runs.

### Observation

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique identifier |
| AgentName | string | `agent_name` | yes | Which agent observed |
| Target | string | `target` | yes | What was observed (file path, URL) |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |
| Measurements | map[string]float64 | `measurements` | yes | Numeric measurements |
| Findings | []Finding | `findings` | no | Issues discovered |
| ContentHash | string | `content_hash` | no | Hash of observed content |
| StrategyID | string | `strategy_id` | no | Associated strategy |

### Finding

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| RuleID | string | `rule_id` | yes | Which rule triggered |
| Severity | string | `severity` | yes | `critical`, `warning`, `info` |
| Element | string | `element` | yes | What element is affected |
| Current | string | `current` | yes | Current value |
| Expected | string | `expected` | yes | Expected value |
| Message | string | `message` | yes | Human-readable description |
| Fixable | bool | `fixable` | yes | Whether auto-fix is available |
| Fix | string | `fix` | no | Suggested fix value |

---

## Recommendations

### Recommendation

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique identifier |
| ObservationID | string | `observation_id` | yes | Source observation |
| AgentName | string | `agent_name` | yes | Recommending agent |
| StrategyID | string | `strategy_id` | no | Associated strategy |
| Target | string | `target` | yes | Target file/resource |
| Action | string | `action` | yes | What to do |
| Element | string | `element` | yes | Target element |
| Current | string | `current` | yes | Current value |
| Proposed | string | `proposed` | yes | Proposed value |
| Reason | string | `reason` | yes | Justification |
| Priority | string | `priority` | yes | `critical`, `high`, `medium`, `low` |
| Impact | float64 | `impact` | yes | Estimated impact score |
| Status | string | `status` | yes | `pending`, `accepted`, `rejected`, `applied` |
| CreatedAt | int64 | `created_at` | yes | Unix epoch seconds |
| ResolvedAt | int64 | `resolved_at` | no | Unix epoch seconds |

---

## Approvals

### ApprovalRequest

Submitted by a user or external system to approve or reject one or
more pending recommendations or workflow phases.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| RecommendationIDs | []string | `recommendation_ids` | yes | IDs of recommendations to resolve |
| Decision | string | `decision` | yes | `"accept"` or `"reject"` |
| Reason | string | `reason` | no | Human-provided justification (required for rejections) |
| Token | string | `token` | yes | Auth token |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

### ApprovalResponse

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Updated | int | `updated` | yes | Count of recommendations updated |
| Results | []ApprovalResult | `results` | yes | Per-recommendation outcome |

### ApprovalResult

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| RecommendationID | string | `recommendation_id` | yes | Which recommendation |
| PreviousStatus | string | `previous_status` | yes | Status before this action |
| NewStatus | string | `new_status` | yes | Status after this action |
| Error | string | `error` | no | Error if this one failed (e.g., already resolved) |

---

## Feedback

### Feedback

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique identifier |
| RecommendationID | string | `recommendation_id` | yes | Which recommendation |
| Type | string | `type` | yes | `metric`, `user`, `automated` |
| Signal | string | `signal` | yes | `positive`, `negative`, `neutral` |
| Detail | string | `detail` | yes | What happened |
| MetricBefore | float64 | `metric_before` | no | Metric value before |
| MetricAfter | float64 | `metric_after` | no | Metric value after |
| MetricName | string | `metric_name` | no | Which metric |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

---

## Agent Metrics

### AgentMetrics

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| AgentName | string | `agent_name` | yes | Agent identifier |
| TotalObservations | int | `total_observations` | yes | Cumulative count |
| TotalFindings | int | `total_findings` | yes | Cumulative count |
| TotalRecommendations | int | `total_recommendations` | yes | Cumulative count |
| AdoptionRate | float64 | `adoption_rate` | yes | % of accepted recommendations |
| Accuracy | float64 | `accuracy` | yes | % of correct findings |
| ImpactScore | float64 | `impact_score` | yes | Cumulative impact |
| FalsePositiveRate | float64 | `false_positive_rate` | yes | % of false positives |

---

## Messaging

### AgentMessage

Direct agent-to-agent or orchestrator-to-agent message.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Message identifier |
| From | string | `from` | yes | Sender agent name |
| To | string | `to` | yes | Recipient agent name |
| Type | string | `type` | yes | `request` or `response` |
| Action | string | `action` | yes | Message action name |
| Payload | map | `payload` | yes | Message data |
| Token | string | `token` | no | Auth or channel token |
| Signature | string | `signature` | no | Ed25519 signature |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |
| TraceID | string | `trace_id` | no | Correlation ID (propagated from TaskContext) |

**Signature covers:** `JSON.stringify({from, to, action, payload})`

---

## Service Directory

### ServiceEntry

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Agent name |
| URL | string | `url` | yes | Agent base URL |
| PublicKey | string | `public_key` | yes | Hex Ed25519 public key |
| Capabilities | []string | `capabilities` | yes | Capability names |
| Status | string | `status` | yes | `online`, `offline`, `degraded` |

### ServiceDirectory

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Services | []ServiceEntry | `services` | yes | All registered agents |
| RoutingTable | map[string][]RouteEntry | `routing_table` | yes | Topic pattern → list of subscriber routes. Used by the framework to resolve event delivery targets locally. |
| Namespaces | map[string]string | `namespaces` | yes | Namespace → owning agent name. Used to validate publish rights. |
| UpdatedAt | int64 | `updated_at` | yes | Unix epoch seconds |
| Signature | string | `signature` | no | Orchestrator signature |

---

## Registration

### RegisterRequest

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Manifest | AgentManifest | `manifest` | yes | Agent's full manifest |
| Signature | string | `signature` | yes | Ed25519 signature of JSON(manifest) |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

### RegisterResponse

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| AgentID | string | `agent_id` | yes | Assigned unique identifier |
| Token | string | `token` | yes | Auth token (WLT format) |
| ExpiresAt | int64 | `expires_at` | yes | Token expiry (Unix epoch) |
| Services | ServiceDirectory | `services` | yes | Current service directory |
| Orchestrator | OrchestratorInfo | `orchestrator` | yes | Orchestrator info |
| ProtocolVersion | string | `protocol_version` | yes | Negotiated protocol version (e.g., `"1"`) |

### OrchestratorInfo

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| URL | string | `url` | yes | Orchestrator base URL |
| PublicKey | string | `public_key` | yes | Hex Ed25519 public key |
| Version | string | `version` | yes | Orchestrator software version |
| SupportedVersions | []string | `supported_versions` | yes | Protocol versions this orchestrator supports (e.g., `["1"]`) |

**Version negotiation:** On registration, the orchestrator reads the
agent's `manifest.protocol_version` (default `"1"` if omitted). If the
orchestrator supports that version, registration succeeds and
`RegisterResponse.protocol_version` confirms the negotiated version.
If the requested version is not in `supported_versions`, the
orchestrator rejects with 400 and error code `UNSUPPORTED_VERSION`.

---

## Channels

### ChannelRequest

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| FromAgent | string | `from_agent` | yes | Requesting agent name |
| ToAgent | string | `to_agent` | yes | Target agent name |
| Purpose | string | `purpose` | yes | Why the channel is needed |
| Token | string | `token` | yes | Requestor's auth token |
| Signature | string | `signature` | yes | Ed25519 signature |

### ChannelGrant

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ChannelID | string | `channel_id` | yes | Unique channel identifier |
| FromAgent | string | `from_agent` | yes | Requesting agent |
| ToAgent | string | `to_agent` | yes | Target agent |
| TargetURL | string | `target_url` | yes | Target agent's URL |
| TargetPubKey | string | `target_pub_key` | yes | Target's public key |
| ChannelToken | string | `channel_token` | yes | Scoped channel token |
| ExpiresAt | int64 | `expires_at` | yes | Expiry (Unix epoch) |
| Signature | string | `signature` | yes | Orchestrator signature |

---

## Health

### HealthStatus

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Component name |
| Status | string | `status` | yes | `healthy`, `degraded`, `unhealthy` |
| Version | string | `version` | yes | Component version |
| Uptime | int64 | `uptime` | yes | Seconds since start |
| Metrics | map | `metrics` | no | Component-specific metrics |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |

---

## Audit

### AuditEntry

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | Unique identifier |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |
| Actor | string | `actor` | yes | Who performed the action |
| Action | string | `action` | yes | Action type (see below) |
| Target | string | `target` | yes | Affected resource |
| Detail | string | `detail` | yes | Human-readable description |
| Status | string | `status` | yes | `ok`, `denied`, `failed` |

**Action types:** `register`, `deregister`, `channel`, `message`,
`event`, `namespace_grant`, `namespace_release`

---

## Events

Types used by the HTTP-based pub/sub event system. Events are the
primary coordination mechanism between agents. See
[spec.md — Event Publishing](spec.md#event-publishing-framework-behavior)
for the delivery protocol and
[spec.md — Event Scoping](spec.md#event-scoping) for scope semantics.

### EventEnvelope

The standard wrapper for all events delivered via `POST /v1/event`.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| EventID | string | `event_id` | yes | Globally unique event identifier (UUID v7 recommended — time-sortable) |
| Topic | string | `topic` | yes | Dot-separated topic name (e.g., `workflow.completed`) |
| Source | string | `source` | yes | Name of the publishing agent |
| Scope | string | `scope` | yes | Target agent name, or `"*"` for global delivery |
| CorrelationID | string | `correlation_id` | no | Links all events in a single execution chain (e.g., one workflow run) |
| Timestamp | int64 | `timestamp` | yes | Unix epoch seconds |
| TraceID | string | `trace_id` | yes | Distributed trace context (propagated through all downstream operations) |
| Version | string | `version` | yes | Schema version of the payload |
| Payload | map | `payload` | yes | Event-specific data, typed per topic |
| Token | string | `token` | no | Auth token for delivery verification |

### Subscription

Declared in the agent manifest. Each entry registers interest in a
topic pattern with scope and concurrency controls.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Pattern | string | `pattern` | yes | Topic or wildcard pattern (supports `*` for single segment, `#` for multi-segment) |
| Group | string | `group` | no | Consumer group name. Events are load-balanced within a group. Defaults to agent name. |
| Scope | string | `scope` | no | `"self"` (default), `"*"` (requires `event:observe`), or a specific agent name |
| MaxConcurrent | int | `max_concurrent` | no | Max parallel event processing for this subscription (default: 5) |

### RouteEntry

A single entry in the routing table. Represents one subscriber for a
topic pattern.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Agent | string | `agent` | yes | Subscriber agent name |
| URL | string | `url` | yes | Subscriber's event endpoint (agent URL + `/v1/event`) |
| Group | string | `group` | no | Consumer group name |
| Scope | string | `scope` | yes | Scope filter for this subscriber |

### DeadLetterEntry

An event that could not be delivered after all retry attempts.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| OriginalEvent | EventEnvelope | `original_event` | yes | The event that failed delivery |
| FailureReason | string | `failure_reason` | yes | Error category (`HANDLER_ERROR`, `UNREACHABLE`, `TIMEOUT`, `REJECTED`) |
| LastError | string | `last_error` | yes | Last error message from delivery attempt |
| Attempts | int | `attempts` | yes | Total delivery attempts |
| FirstAttempt | int64 | `first_attempt` | yes | Unix epoch seconds of first attempt |
| LastAttempt | int64 | `last_attempt` | yes | Unix epoch seconds of final attempt |
| Subscriber | string | `subscriber` | yes | Name of the subscriber that could not receive |

---

## Protocol Paths

All paths are prefixed with `/v1`.

| Path | Method | Auth | Component | Purpose |
|------|--------|------|-----------|---------|
| `/v1/describe` | POST | no | agent | Return manifest |
| `/v1/execute` | POST | yes | agent | Execute task |
| `/v1/health` | POST | no | agent | Health check |
| `/v1/message` | POST | yes | agent | Synchronous request/response |
| `/v1/services` | POST | yes | agent | Receive service directory updates |
| `/v1/event` | POST | yes | agent | Receive event delivery (pub/sub) |
| `/v1/register` | POST | no | orchestrator | Agent registration |
| `/v1/register` | DELETE | yes | orchestrator | Agent deregistration |
| `/v1/services` | GET | yes | orchestrator | Service directory + routing table |
| `/v1/channel` | POST | yes | orchestrator | Broker channel |
| `/v1/health` | GET | no | orchestrator | Orchestrator health |
| `/v1/audit` | GET | yes | orchestrator | Audit log |

---

## Error Handling

All errors across the protocol use the `ErrorResponse` type defined in the
Errors section above. Error categories (`transient`, `permanent`, `partial`)
determine retry behavior. Standard error codes are enumerated in the
ErrorResponse section with their HTTP status mappings.

Implementations MUST:
- Always return at minimum `{"error": "message"}`
- Include `code` and `category` when the information is available
- Use exact error codes from the standard table (no custom codes without extension)
- Map error codes to the correct HTTP status codes

---

## Security

```yaml
security:
  transport:
    - Types are serialized as JSON over HTTP
    - All string fields MUST be validated for maximum length before processing
    - No executable content in any type field
  signing:
    algorithm: Ed25519
    key_type: 32-byte public / 64-byte private
    process: Signature fields contain hex-encoded Ed25519 signatures
  verification:
    process: All signature fields verified against sender public key
  type_safety:
    - Required fields MUST be validated before processing
    - Enum fields MUST be validated against allowed values
    - IDs MUST be validated as 32-char hex strings
    - Timestamps MUST be validated as positive integers
    - Unknown fields MUST be silently ignored (forward compatibility)
```

---

## Implementation Notes

- Types are language-agnostic — implementations map to native types
- JSON is the sole wire format; field names in the `json` column are canonical
- Optional fields omitted from JSON are treated as zero values (empty string, 0, null, false)
- The `map` type serializes as a JSON object with string keys
- `int64` timestamps MUST NOT use floating point — JSON `number` with no decimal
- Protocol Paths table is the single source of truth for endpoint definitions
- Types are versioned with the protocol — all types share the blueprint version

---

## Verification Checklist

- [ ] All IDs are 32-character hex strings (16 random bytes) and all timestamps are Unix epoch seconds (int64)
- [ ] Ed25519 signatures serialize as 128 hex characters; public keys serialize as 64 hex characters
- [ ] ErrorResponse includes `error` (required), `code`, `category`, `retryable`, and `detail` fields with exact JSON keys
- [ ] Error categories are constrained to `transient`, `permanent`, or `partial` and each standard error code maps to the correct HTTP status
- [ ] Unknown JSON fields are silently ignored on deserialization (forward compatibility); optional fields are omitted when empty/null
- [ ] AgentManifest requires `name`, `version`, `description`, `url`, `public_key`, and `capabilities`; includes `publishes` and `subscriptions` for event system
- [ ] EventEnvelope requires `event_id`, `topic`, `source`, `scope`, `timestamp`, `trace_id`, `version`, and `payload`
- [ ] Subscription requires `pattern`; `scope` defaults to `"self"`; `group` defaults to agent name
- [ ] RouteEntry requires `agent`, `url`, and `scope`
- [ ] ServiceDirectory includes `services`, `routing_table`, and `namespaces`
- [ ] WorkflowPhase `on_error` supports `fail`, `skip`, and `retry`; `max_retries` applies only when `on_error` = `"retry"`
- [ ] WorkflowExecution `status` transitions follow `pending` → `running` → `completed` | `failed`; PhaseResult adds `skipped`
- [ ] TaskRequest requires `id`, `from`, `action`, `payload`, `context`, `token`, and `timestamp`; TaskResult status is `success`, `failed`, or `pending_approval`
- [ ] AgentMessage `signature` covers `JSON.stringify({from, to, action, payload})` and `trace_id` propagates through downstream calls
- [ ] Finding includes all required fields: `rule_id`, `severity`, `element`, `current`, `expected`, `message`, and `fixable`
- [ ] RegisterResponse includes `agent_id`, `token`, `expires_at`, `services`, `orchestrator`, and negotiated `protocol_version`
- [ ] ChannelGrant includes `channel_id`, scoped `channel_token`, `target_url`, `target_pub_key`, and `expires_at`
- [ ] Protocol paths are all prefixed with `/v1` and method/auth requirements match the Protocol Paths table
- [ ] DeadLetterEntry includes `original_event`, `failure_reason`, `last_error`, `attempts`, and `subscriber`
