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
- All signatures are base64url-encoded ML-DSA-65 signatures (3309 bytes)
- All public keys are base64url-encoded ML-DSA-65 public keys (1952 bytes)
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

```yaml
types:
  ErrorResponse:
    fields:
      error:
        name: Error
        type: string
        required: true
        description: "Human-readable error message"
      code:
        name: Code
        type: string
        required: false
        description: "Machine-readable error code (e.g., `AGENT_UNREACHABLE`, `INVALID_INPUT`)"
      category:
        name: Category
        type: string
        required: false
        description: "`\"transient\"`, `\"permanent\"`, or `\"partial\"`"
      retryable:
        name: Retryable
        type: bool
        required: false
        description: "Whether the caller SHOULD retry this request"
      retry_after:
        name: RetryAfter
        type: int
        required: false
        description: "Seconds to wait before retrying (present when `retryable` is true)"
      detail:
        name: Detail
        type: map
        required: false
        description: "Additional structured context (varies by error)"
```

**Categories:**
- `transient` — Temporary failure; retry is safe. Examples: network timeout, agent overloaded, upstream 503.
- `permanent` — Will not succeed on retry. Examples: invalid input, capability not available, unknown action.
- `partial` — Request partially succeeded. `detail` SHOULD include `completed` and `failed` sub-results.

**Standard error codes:**

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `INVALID_REQUEST` | 400 | permanent | Missing or malformed fields |
| `INVALID_SIGNATURE` | 401 | permanent | ML-DSA-65 signature verification failed |
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

**Enforcement error codes** (produced by `architecture/enforcement`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `ENFORCEMENT_QUARANTINED` | 403 | permanent | Agent is quarantined — all operations blocked |
| `ENFORCEMENT_POLICY_DENY` | 403 | permanent | Policy evaluation returned deny |
| `ENFORCEMENT_MISSING_INTENT` | 403 | permanent | Safety intent required but not filed |
| `ENFORCEMENT_CAPABILITY_MISMATCH` | 403 | permanent | Agent lacks declared capability for operation |
| `ENFORCEMENT_SCOPE_VIOLATION` | 403 | permanent | Resource scope exceeds agent operational scope |
| `ENFORCEMENT_SCOPE_LEAKAGE` | 403 | permanent | Payload scope exceeds target endpoint classification |
| `ENFORCEMENT_BLOCKED_TARGET` | 403 | permanent | Target is on the blocked endpoint list |
| `ENFORCEMENT_DATA_CONTRACT_VIOLATION` | 403 | permanent | Operation targets resources outside agent's declared data contract |
| `ENFORCEMENT_OUTPUT_CONTRACT_VIOLATION` | 403 | permanent | Response contains fields outside declared output contract |
| `ENFORCEMENT_OUTPUT_SCOPE_EXCEEDED` | 403 | permanent | Response scope exceeds agent's operational scope |
| `ENFORCEMENT_CALLER_SCOPE_EXCEEDED` | 403 | permanent | Response scope exceeds what the caller can receive |
| `ENFORCEMENT_CONSENT_REQUIRED` | 403 | permanent | Operation involves subject data requiring consent that is not active |

**Contract error codes** (produced by `patterns/contract`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `CONTRACT_VIOLATION` | 400 | permanent | Contract terms violated |
| `CONTRACT_UNKNOWN` | 404 | permanent | Referenced contract not found |
| `SCHEMA_INVALID` | 400 | permanent | Data does not match contract schema |

**Federation error codes** (produced by `protocol/federation`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `PEER_UNTRUSTED` | 403 | permanent | Federation peer not in trust store |
| `TRUST_EXPIRED` | 403 | permanent | Peer trust relationship has expired |
| `JURISDICTION_DENIED` | 403 | permanent | Data cannot cross jurisdiction boundary |
| `DATA_BOUNDARY_VIOLATION` | 400 | permanent | Payload violates federation data contract |

**Safety error codes** (produced by `patterns/safety`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `APPROVAL_TIMEOUT` | 408 | transient | Approval request timed out |

**Policy error codes** (produced by `patterns/policy`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `POLICY_DENIED` | 403 | permanent | Policy evaluation denied the operation |
| `POLICY_ESCALATED` | 202 | transient | Policy requires approval escalation before proceeding |
| `POLICY_NOT_FOUND` | 404 | permanent | Referenced policy does not exist |
| `POLICY_EVAL_FAILED` | 500 | transient | Policy engine encountered an internal error during evaluation |
| `POLICY_CONTEXT_INCOMPLETE` | 400 | permanent | Required policy context fields are missing — fail-closed deny |
| `POLICY_INVALID_DEFINITION` | 400 | permanent | Policy definition does not pass schema validation |
| `POLICY_LIFECYCLE_INVALID` | 409 | permanent | Invalid policy state transition (e.g., modifying an archived policy) |
| `POLICY_CONFLICT` | 409 | permanent | Conflicting active policies detected for the same scope |

**Identity error codes** (produced by `protocol/identity`):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `KEY_DECODE_ERROR` | 400 | permanent | Cryptographic key could not be decoded or parsed |

**Common error codes** (reusable across agents and components):

| Code | HTTP | Category | Description |
|------|------|----------|-------------|
| `INVALID_INPUT` | 400 | permanent | Request input fails validation (malformed, missing required fields, constraint violation) |
| `STORAGE_ERROR` | 500 | transient | Persistence layer operation failed (read, write, or query) |
| `INVALID_STATE` | 409 | permanent | Operation is invalid for the current state of the target resource |
| `TARGET_NOT_FOUND` | 404 | permanent | Dispatch target agent is not registered or unreachable |
| `DISPATCH_TIMEOUT` | 408 | transient | Task dispatch to target agent timed out before acknowledgement |
| `DISPATCH_ERROR` | 502 | transient | Task dispatch to target agent failed (transport or protocol error) |
| `PAYLOAD_TOO_LARGE` | 413 | permanent | Request payload exceeds the maximum allowed size |
| `DELIVERY_FAILED` | 502 | transient | Event or notification delivery to target failed after retries |
| `CAPABILITY_DENIED` | 403 | permanent | Peer or agent lacks the required capability grant |
| `BEHAVIORAL_CHANGE` | 403 | permanent | Entity behavior has deviated from its declared or historical pattern |
| `RETENTION_EXPIRED` | 410 | permanent | Requested data has been purged per retention policy |

#### Error Code Conventions

Error codes follow the convention: `DOMAIN_SPECIFIC_ERROR`. Domain
prefixes (`ENFORCEMENT_`, `CONTRACT_`, `POLICY_`, etc.) indicate the
originating subsystem.

**Registry vs. local codes:**
- All protocol-level, enforcement, policy, contract, federation,
  safety, identity, and common codes are registered in this central
  table. These codes may appear in any component.
- Agent-local codes (specific to a single agent's domain logic) are
  defined in the agent's own blueprint. Agent-local codes MUST NOT
  collide with registered codes and SHOULD use a descriptive name
  that indicates the agent domain (e.g., `INVALID_SCHEDULE` in the
  cron agent, `HARD_BOUNCE` in the email-send agent).
- When an agent-local code is used by two or more unrelated agents,
  it SHOULD be promoted to the common codes table in this registry.

### AgentManifest

Describes an agent's identity, capabilities, and interface contract.
Returned by `POST /v1/describe` and sent during registration.

```yaml
types:
  AgentManifest:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Agent identifier (lowercase, no spaces)"
      type:
        name: Type
        type: string
        required: false
        description: "`\"domain\"` (domain controller), `\"agent\"` (work agent, default), or `\"infrastructure\"` (system-level: task, workflow, lifecycle)"
      version:
        name: Version
        type: string
        required: true
        description: "Semver version of the agent"
      protocol_version:
        name: ProtocolVersion
        type: string
        required: false
        description: "Protocol version this agent implements (default: `\"1\"`)"
      description:
        name: Description
        type: string
        required: true
        description: "Human-readable purpose"
      url:
        name: URL
        type: string
        required: true
        description: "Agent's HTTP base URL"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 public key (1952 bytes)"
      capabilities:
        name: Capabilities
        type: "[]Capability"
        required: true
        description: "What this agent can do"
      inputs:
        name: Inputs
        type: "[]IOSpec"
        required: false
        description: "Expected input parameters"
      outputs:
        name: Outputs
        type: "[]IOSpec"
        required: false
        description: "What this agent produces"
      collaborators:
        name: Collaborators
        type: "[]string"
        required: false
        description: "Agent names this agent works with"
      approval:
        name: Approval
        type: string
        required: false
        description: "`\"required\"` or `\"auto\"` (default: `\"required\"`)"
      required_agents:
        name: RequiredAgents
        type: "[]string"
        required: false
        description: "Agents this domain needs (domain type only)"
      workflows:
        name: Workflows
        type: "[]string"
        required: false
        description: "Workflow names supported (domain type only)"
      max_concurrent:
        name: MaxConcurrent
        type: int
        required: false
        description: "Max concurrent executions (default: 1 — serial execution; 0 means unlimited)"
      publishes:
        name: Publishes
        type: "[]string"
        required: false
        description: "Namespace patterns this agent may publish to (e.g., `[\"workflow.*\"]`). The orchestrator enforces exclusive ownership — no two agents may claim the same namespace. See [spec.md — Namespace Control](spec.md#namespace-control)."
      subscriptions:
        name: Subscriptions
        type: "[]Subscription"
        required: false
        description: "Event subscription declarations. Each entry specifies a topic pattern, optional consumer group, scope, and concurrency limit. See [spec.md — Event Scoping](spec.md#event-scoping)."
```

### Capability

A single thing an agent can do, with optional resource scoping.

```yaml
types:
  Capability:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Capability identifier (e.g., `file:read`)"
      resources:
        name: Resources
        type: "[]string"
        required: false
        description: "Glob patterns scoping the capability"
```

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
- `event:observe` — observe all events for a topic regardless of scope
- `realtime:publish` — publish to real-time channels

**Content capabilities:**
- `content:read` — read entries and list a content repository
- `content:write` — create, modify and remove entries
- `content:describe` — read a repository's custody class, attestations and derived ceiling
- `content:reconcile` — run custody reconciliation on a shared repository

A capability name is `family:verb`. A component that invents one is refused at
registration with `INVALID_REQUEST` — which is correct, and is why a component's
capabilities belong in this list before that component is built. The content
service was generated asking for `content.read`, with a dot and no declared
family, and the orchestrator rejected it exactly as it should.

**Administrative capabilities:**
- `admin:read` — read administrative state: overview, agents, domains, workflows, operators
- `admin:approve` — act on the approval queue
- `admin:strategy` — create, amend and retire strategies
- `admin:audit` — read the full audit log, including export
- `admin:*` — every capability in the `admin` family

Administration is expressed in capabilities like everything else, and an
operator's **role is a bundle of them** — `architecture/admin` defines `viewer` as
`admin:read`, `auditor` as `admin:read` plus `admin:audit`, and so on. This is
what allows an administrative interface to be a service that holds grants rather
than a second authority system running alongside the first: whatever asks to
administer a component presents capabilities, and the component checks them the
same way it checks `agent:message`.

`admin:*` is the only wildcard capability name. It exists because a full-access
role has to be nameable, and it denotes the whole family rather than a resource
glob — resource scoping stays in `resources`, as for every other capability.

> **Gap.** `architecture/admin`'s `admin` role relies on `admin:*` for operator
> management, agent deregistration and federation approval, none of which is
> separately nameable here. A deployment that wants an operator who may approve
> federation but not deregister agents cannot express it. Naming those is
> `architecture/admin`'s to do, and this list will follow it — inventing the
> names here would put the wrong document in charge of what administration means.

### IOSpec

Describes an input or output parameter.

```yaml
types:
  IOSpec:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Parameter name"
      type:
        name: Type
        type: string
        required: true
        description: "Data type: `file_list`, `json`, `text`"
      description:
        name: Description
        type: string
        required: true
        description: "Human-readable description"
```

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

```yaml
types:
  WorkflowDefinition:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Workflow identifier (lowercase, hyphens)"
      description:
        name: Description
        type: string
        required: true
        description: "What this workflow does"
      trigger:
        name: Trigger
        type: string
        required: true
        description: "Task action that invokes this workflow"
      phases:
        name: Phases
        type: "[]WorkflowPhase"
        required: true
        description: "Ordered execution steps"
```

### WorkflowPhase

A single step in a workflow. Each phase dispatches to one agent.

```yaml
types:
  WorkflowPhase:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Phase identifier (unique within workflow)"
      agent:
        name: Agent
        type: string
        required: true
        description: "Target agent name"
      action:
        name: Action
        type: string
        required: true
        description: "`HandleMessage` action to invoke"
      input:
        name: Input
        type: map
        required: false
        description: "Input mapping — reference expressions resolve at runtime (see [Reference Expression Syntax](../architecture/domain.md#reference-expression-syntax))"
      output:
        name: Output
        type: string
        required: false
        description: "Key name under which this phase's result is stored"
      depends_on:
        name: DependsOn
        type: "[]string"
        required: false
        description: "Phase names that must complete first. Phases without dependencies MAY run in parallel"
      timeout:
        name: Timeout
        type: int
        required: false
        description: "Phase timeout in seconds (default: 300)"
      approval:
        name: Approval
        type: string
        required: false
        description: "`\"required\"` or `\"auto\"` (default: `\"auto\"`)"
      on_error:
        name: OnError
        type: string
        required: false
        description: "`\"fail\"` (default), `\"skip\"`, or `\"retry\"`"
      max_retries:
        name: MaxRetries
        type: int
        required: false
        description: "Retry count when `on_error` = `\"retry\"` (default: 0)"
      condition:
        name: Condition
        type: string
        required: false
        description: "Expression evaluated at runtime; phase is skipped if false"
```

**Input reference syntax:** See [Reference Expression Syntax](../architecture/domain.md#reference-expression-syntax) for the full grammar, including nested access, array indexing (`[0]`), array expansion (`[*]`), and resolution rules.

### WorkflowExecution

Runtime state of a workflow in progress or completed.

```yaml
types:
  WorkflowExecution:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique execution identifier"
      workflow_name:
        name: WorkflowName
        type: string
        required: true
        description: "Which workflow is executing"
      domain_name:
        name: DomainName
        type: string
        required: true
        description: "Executing domain controller"
      task_id:
        name: TaskID
        type: string
        required: true
        description: "Originating task ID"
      status:
        name: Status
        type: string
        required: true
        description: "`pending`, `running`, `completed`, `failed`"
      phases:
        name: Phases
        type: "[]PhaseResult"
        required: true
        description: "Results per phase"
      started_at:
        name: StartedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      completed_at:
        name: CompletedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
```

### PhaseResult

Tracks the outcome of a single workflow phase.

```yaml
types:
  PhaseResult:
    fields:
      phase_name:
        name: PhaseName
        type: string
        required: true
        description: "Phase identifier"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Agent that executed this phase"
      status:
        name: Status
        type: string
        required: true
        description: "`pending`, `running`, `completed`, `failed`, `skipped`"
      output:
        name: Output
        type: map
        required: false
        description: "Phase output data (referenced by subsequent phases)"
      started_at:
        name: StartedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
      completed_at:
        name: CompletedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
      error:
        name: Error
        type: string
        required: false
        description: "Error message if failed"
      retries:
        name: Retries
        type: int
        required: false
        description: "Number of retry attempts"
```

---

## Strategy

A strategy declares a business objective with measurable targets.
Multiple strategies run in parallel. The orchestrator decomposes
each into prioritized tasks assigned to domain agents.

### Strategy

```yaml
types:
  Strategy:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique hex identifier"
      name:
        name: Name
        type: string
        required: true
        description: "Strategy name"
      objective:
        name: Objective
        type: string
        required: true
        description: "What this strategy aims to achieve"
      targets:
        name: Targets
        type: "[]StrategyTarget"
        required: true
        description: "Measurable goals"
      priority:
        name: Priority
        type: int
        required: true
        description: "1 = highest priority"
      status:
        name: Status
        type: string
        required: true
        description: "`active`, `paused`, `completed`"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      updated_at:
        name: UpdatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      metadata:
        name: Metadata
        type: map
        required: false
        description: "Arbitrary key-value data"
```

### StrategyTarget

```yaml
types:
  StrategyTarget:
    fields:
      metric:
        name: Metric
        type: string
        required: true
        description: "What is being measured"
      current:
        name: Current
        type: float64
        required: true
        description: "Current value"
      goal:
        name: Goal
        type: float64
        required: true
        description: "Target value"
      deadline:
        name: Deadline
        type: string
        required: true
        description: "ISO 8601 date (human-facing planning horizon, not a protocol timestamp)"
      unit:
        name: Unit
        type: string
        required: true
        description: "Unit of measurement"
      progress:
        name: Progress
        type: float64
        required: true
        description: "0.0 to 1.0"
      measurement_window:
        name: MeasurementWindow
        type: int
        required: false
        description: "Evaluation window in seconds (default: 86400)"
```

---

## Entity Context

The entity being optimized — a company, person, or project.
This grounds every agent's decisions in business reality.

### EntityContext

```yaml
types:
  EntityContext:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Entity name"
      type:
        name: Type
        type: string
        required: true
        description: "`company`, `person`, `project`, `site`"
      industry:
        name: Industry
        type: string
        required: true
        description: "Industry/sector"
      description:
        name: Description
        type: string
        required: true
        description: "What the entity does"
      positioning:
        name: Positioning
        type: string
        required: true
        description: "Market positioning statement"
      audiences:
        name: Audiences
        type: "[]Audience"
        required: false
        description: "Target audiences"
      competitors:
        name: Competitors
        type: "[]Competitor"
        required: false
        description: "Known competitors"
      keywords:
        name: Keywords
        type: "[]string"
        required: false
        description: "Core keywords/topics"
      tone:
        name: Tone
        type: string
        required: false
        description: "Brand voice (e.g., `professional`, `casual`)"
      geography:
        name: Geography
        type: string
        required: false
        description: "Primary geography"
      assets:
        name: Assets
        type: "[]Asset"
        required: false
        description: "Known digital assets"
      metadata:
        name: Metadata
        type: map
        required: false
        description: "Arbitrary key-value data"
```

### Audience

```yaml
types:
  Audience:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Audience segment name"
      description:
        name: Description
        type: string
        required: true
        description: "Who they are"
      pain_points:
        name: PainPoints
        type: "[]string"
        required: false
        description: "Their challenges"
      keywords:
        name: Keywords
        type: "[]string"
        required: false
        description: "Terms they search for"
```

### Competitor

```yaml
types:
  Competitor:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Competitor name"
      url:
        name: URL
        type: string
        required: false
        description: "Competitor URL"
      notes:
        name: Notes
        type: string
        required: false
        description: "Competitive notes"
```

### Asset

```yaml
types:
  Asset:
    fields:
      path:
        name: Path
        type: string
        required: true
        description: "File path or URL"
      type:
        name: Type
        type: string
        required: true
        description: "Asset type"
      purpose:
        name: Purpose
        type: string
        required: false
        description: "What this asset is for"
```

---

## Task Protocol

### TaskRequest

Sent to an agent's `POST /v1/execute` endpoint by the Task Agent,
or dispatched as part of a workflow phase.

```yaml
types:
  TaskRequest:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique task identifier"
      from:
        name: From
        type: string
        required: true
        description: "Who initiated (`user` or agent name)"
      action:
        name: Action
        type: string
        required: true
        description: "What to do (`execute`, custom actions)"
      payload:
        name: Payload
        type: map
        required: true
        description: "Task-specific data"
      context:
        name: Context
        type: TaskContext
        required: true
        description: "Runtime context"
      strategy_id:
        name: StrategyID
        type: string
        required: false
        description: "Associated strategy"
      token:
        name: Token
        type: string
        required: true
        description: "Auth token"
      signature:
        name: Signature
        type: string
        required: false
        description: "ML-DSA-65 signature of payload (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### TaskContext

Runtime context provided with every task execution.

```yaml
types:
  TaskContext:
    fields:
      workspace_root:
        name: WorkspaceRoot
        type: string
        required: true
        description: "Absolute path to project root"
      services:
        name: Services
        type: "[]ServiceEntry"
        required: true
        description: "Current service directory"
      entity:
        name: Entity
        type: EntityContext
        required: false
        description: "Entity being optimized"
      config:
        name: Config
        type: map
        required: false
        description: "Additional configuration"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "Correlation ID for distributed tracing (propagated through all downstream calls)"
```

### TaskResult

Returned by an agent after task execution.

```yaml
types:
  TaskResult:
    fields:
      task_id:
        name: TaskID
        type: string
        required: true
        description: "Matches request ID"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Which agent produced this"
      status:
        name: Status
        type: string
        required: true
        description: "`success`, `failed`, `pending_approval`"
      summary:
        name: Summary
        type: string
        required: true
        description: "Human-readable summary"
      changes:
        name: Changes
        type: "[]ProposedChange"
        required: false
        description: "File modifications"
      observations:
        name: Observations
        type: "[]Observation"
        required: false
        description: "Measurements taken"
      recommendations:
        name: Recommendations
        type: "[]Recommendation"
        required: false
        description: "Suggested actions"
      metrics:
        name: Metrics
        type: map
        required: false
        description: "Execution metrics"
      signature:
        name: Signature
        type: string
        required: false
        description: "ML-DSA-65 signature (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### ProposedChange

A file modification proposed by an agent.

```yaml
types:
  ProposedChange:
    fields:
      path:
        name: Path
        type: string
        required: true
        description: "Relative file path"
      action:
        name: Action
        type: string
        required: true
        description: "`create`, `modify`, `delete`"
      original:
        name: Original
        type: string
        required: false
        description: "Original file content"
      modified:
        name: Modified
        type: string
        required: false
        description: "Modified file content"
      diffs:
        name: Diffs
        type: "[]ChangeDiff"
        required: false
        description: "Element-level changes"
```

### ChangeDiff

```yaml
types:
  ChangeDiff:
    fields:
      element:
        name: Element
        type: string
        required: true
        description: "What changed (e.g., `title`)"
      before:
        name: Before
        type: string
        required: true
        description: "Previous value"
      after:
        name: After
        type: string
        required: true
        description: "New value"
      reason:
        name: Reason
        type: string
        required: true
        description: "Why this change was made"
```

---

## Observations

Structured measurements captured every time an agent runs.

### Observation

```yaml
types:
  Observation:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Which agent observed"
      target:
        name: Target
        type: string
        required: true
        description: "What was observed (file path, URL)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      measurements:
        name: Measurements
        type: "map[string]float64"
        required: true
        description: "Numeric measurements"
      findings:
        name: Findings
        type: "[]Finding"
        required: false
        description: "Issues discovered"
      content_hash:
        name: ContentHash
        type: string
        required: false
        description: "Hash of observed content"
      strategy_id:
        name: StrategyID
        type: string
        required: false
        description: "Associated strategy"
```

### Finding

```yaml
types:
  Finding:
    fields:
      rule_id:
        name: RuleID
        type: string
        required: true
        description: "Which rule triggered"
      severity:
        name: Severity
        type: string
        required: true
        description: "`critical`, `warning`, `info`"
      element:
        name: Element
        type: string
        required: true
        description: "What element is affected"
      current:
        name: Current
        type: string
        required: true
        description: "Current value"
      expected:
        name: Expected
        type: string
        required: true
        description: "Expected value"
      message:
        name: Message
        type: string
        required: true
        description: "Human-readable description"
      fixable:
        name: Fixable
        type: bool
        required: true
        description: "Whether auto-fix is available"
      fix:
        name: Fix
        type: string
        required: false
        description: "Suggested fix value"
```

---

## Recommendations

### Recommendation

```yaml
types:
  Recommendation:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      observation_id:
        name: ObservationID
        type: string
        required: true
        description: "Source observation"
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Recommending agent"
      strategy_id:
        name: StrategyID
        type: string
        required: false
        description: "Associated strategy"
      target:
        name: Target
        type: string
        required: true
        description: "Target file/resource"
      action:
        name: Action
        type: string
        required: true
        description: "What to do"
      element:
        name: Element
        type: string
        required: true
        description: "Target element"
      current:
        name: Current
        type: string
        required: true
        description: "Current value"
      proposed:
        name: Proposed
        type: string
        required: true
        description: "Proposed value"
      reason:
        name: Reason
        type: string
        required: true
        description: Justification
      priority:
        name: Priority
        type: string
        required: true
        description: "`critical`, `high`, `medium`, `low`"
      impact:
        name: Impact
        type: float64
        required: true
        description: "Estimated impact score"
      status:
        name: Status
        type: string
        required: true
        description: "`pending`, `accepted`, `rejected`, `applied`"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      resolved_at:
        name: ResolvedAt
        type: int64
        required: false
        description: "Unix epoch seconds"
```

---

## Approvals

### ApprovalRequest

Submitted by a user or external system to approve or reject one or
more pending recommendations or workflow phases.

```yaml
types:
  ApprovalRequest:
    fields:
      recommendation_ids:
        name: RecommendationIDs
        type: "[]string"
        required: true
        description: "IDs of recommendations to resolve"
      decision:
        name: Decision
        type: string
        required: true
        description: "`\"accept\"` or `\"reject\"`"
      reason:
        name: Reason
        type: string
        required: false
        description: "Human-provided justification (required for rejections)"
      token:
        name: Token
        type: string
        required: true
        description: "Auth token"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### ApprovalResponse

```yaml
types:
  ApprovalResponse:
    fields:
      updated:
        name: Updated
        type: int
        required: true
        description: "Count of recommendations updated"
      results:
        name: Results
        type: "[]ApprovalResult"
        required: true
        description: "Per-recommendation outcome"
```

### ApprovalResult

```yaml
types:
  ApprovalResult:
    fields:
      recommendation_id:
        name: RecommendationID
        type: string
        required: true
        description: "Which recommendation"
      previous_status:
        name: PreviousStatus
        type: string
        required: true
        description: "Status before this action"
      new_status:
        name: NewStatus
        type: string
        required: true
        description: "Status after this action"
      error:
        name: Error
        type: string
        required: false
        description: "Error if this one failed (e.g., already resolved)"
```

---

## Feedback

### Feedback

```yaml
types:
  Feedback:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      recommendation_id:
        name: RecommendationID
        type: string
        required: true
        description: "Which recommendation"
      type:
        name: Type
        type: string
        required: true
        description: "`metric`, `user`, `automated`"
      signal:
        name: Signal
        type: string
        required: true
        description: "`positive`, `negative`, `neutral`"
      detail:
        name: Detail
        type: string
        required: true
        description: "What happened"
      metric_before:
        name: MetricBefore
        type: float64
        required: false
        description: "Metric value before"
      metric_after:
        name: MetricAfter
        type: float64
        required: false
        description: "Metric value after"
      metric_name:
        name: MetricName
        type: string
        required: false
        description: "Which metric"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

---

## Agent Metrics

### AgentMetrics

```yaml
types:
  AgentMetrics:
    fields:
      agent_name:
        name: AgentName
        type: string
        required: true
        description: "Agent identifier"
      total_observations:
        name: TotalObservations
        type: int
        required: true
        description: "Cumulative count"
      total_findings:
        name: TotalFindings
        type: int
        required: true
        description: "Cumulative count"
      total_recommendations:
        name: TotalRecommendations
        type: int
        required: true
        description: "Cumulative count"
      adoption_rate:
        name: AdoptionRate
        type: float64
        required: true
        description: "% of accepted recommendations"
      accuracy:
        name: Accuracy
        type: float64
        required: true
        description: "% of correct findings"
      impact_score:
        name: ImpactScore
        type: float64
        required: true
        description: "Cumulative impact"
      false_positive_rate:
        name: FalsePositiveRate
        type: float64
        required: true
        description: "% of false positives"
```

---

## Messaging

### AgentMessage

Direct agent-to-agent or orchestrator-to-agent message.

```yaml
types:
  AgentMessage:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Message identifier"
      from:
        name: From
        type: string
        required: true
        description: "Sender agent name"
      to:
        name: To
        type: string
        required: true
        description: "Recipient agent name"
      type:
        name: Type
        type: string
        required: true
        description: "`request` or `response`"
      action:
        name: Action
        type: string
        required: true
        description: "Message action name"
      payload:
        name: Payload
        type: map
        required: true
        description: "Message data"
      token:
        name: Token
        type: string
        required: false
        description: "Auth or channel token"
      signature:
        name: Signature
        type: string
        required: false
        description: "ML-DSA-65 signature (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "Correlation ID (propagated from TaskContext)"
```

**Signature covers:** `canonicalize({from, to, action, payload})` per
[RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785)

---

## Service Directory

### ServiceEntry

```yaml
types:
  ServiceEntry:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Agent name"
      url:
        name: URL
        type: string
        required: true
        description: "Agent base URL"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 public key (1952 bytes)"
      capabilities:
        name: Capabilities
        type: "[]string"
        required: true
        description: "Capability names"
      status:
        name: Status
        type: string
        required: true
        description: "`online`, `offline`, `degraded`"
```

### ServiceDirectory

```yaml
types:
  ServiceDirectory:
    fields:
      services:
        name: Services
        type: "[]ServiceEntry"
        required: true
        description: "All registered agents"
      routing_table:
        name: RoutingTable
        type: "map[string][]RouteEntry"
        required: true
        description: "Topic pattern → list of subscriber routes. Used by the framework to resolve event delivery targets locally."
      namespaces:
        name: Namespaces
        type: "map[string]string"
        required: true
        description: "Namespace → owning agent name. Used to validate publish rights."
      updated_at:
        name: UpdatedAt
        type: int64
        required: true
        description: "Unix epoch seconds"
      signature:
        name: Signature
        type: string
        required: false
        description: "Orchestrator signature"
```

---

## Registration

### RegisterRequest

```yaml
types:
  RegisterRequest:
    fields:
      manifest:
        name: Manifest
        type: AgentManifest
        required: true
        description: "Agent's full manifest"
      signature:
        name: Signature
        type: string
        required: true
        description: "ML-DSA-65 signature of JSON(manifest) (3309 bytes, base64url-encoded)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### RegisterResponse

```yaml
types:
  RegisterResponse:
    fields:
      agent_id:
        name: AgentID
        type: string
        required: true
        description: "Assigned unique identifier"
      token:
        name: Token
        type: string
        required: true
        description: "Auth token (WLT format)"
      expires_at:
        name: ExpiresAt
        type: int64
        required: true
        description: "Token expiry (Unix epoch)"
      services:
        name: Services
        type: ServiceDirectory
        required: true
        description: "Current service directory"
      orchestrator:
        name: Orchestrator
        type: OrchestratorInfo
        required: true
        description: "Orchestrator info"
      protocol_version:
        name: ProtocolVersion
        type: string
        required: true
        description: "Negotiated protocol version (e.g., `\"1\"`)"
```

### OrchestratorInfo

```yaml
types:
  OrchestratorInfo:
    fields:
      url:
        name: URL
        type: string
        required: true
        description: "Orchestrator base URL"
      public_key:
        name: PublicKey
        type: string
        required: true
        description: "Base64url-encoded ML-DSA-65 public key (1952 bytes)"
      version:
        name: Version
        type: string
        required: true
        description: "Orchestrator software version"
      supported_versions:
        name: SupportedVersions
        type: "[]string"
        required: true
        description: "Protocol versions this orchestrator supports (e.g., `[\"1\"]`)"
```

**Version negotiation:** On registration, the orchestrator reads the
agent's `manifest.protocol_version` (default `"1"` if omitted). If the
orchestrator supports that version, registration succeeds and
`RegisterResponse.protocol_version` confirms the negotiated version.
If the requested version is not in `supported_versions`, the
orchestrator rejects with 400 and error code `UNSUPPORTED_VERSION`.

---

## Channels

### ChannelRequest

```yaml
types:
  ChannelRequest:
    fields:
      from_agent:
        name: FromAgent
        type: string
        required: true
        description: "Requesting agent name"
      to_agent:
        name: ToAgent
        type: string
        required: true
        description: "Target agent name"
      purpose:
        name: Purpose
        type: string
        required: true
        description: "Why the channel is needed"
      token:
        name: Token
        type: string
        required: true
        description: "Requestor's auth token"
      signature:
        name: Signature
        type: string
        required: true
        description: "ML-DSA-65 signature over `canonicalize({from_agent, to_agent, purpose})` (3309 bytes, base64url-encoded)"
```

### ChannelGrant

```yaml
types:
  ChannelGrant:
    fields:
      channel_id:
        name: ChannelID
        type: string
        required: true
        description: "Unique channel identifier"
      from_agent:
        name: FromAgent
        type: string
        required: true
        description: "Requesting agent"
      to_agent:
        name: ToAgent
        type: string
        required: true
        description: "Target agent"
      target_url:
        name: TargetURL
        type: string
        required: true
        description: "Target agent's URL"
      target_pub_key:
        name: TargetPubKey
        type: string
        required: true
        description: "Target's public key"
      channel_token:
        name: ChannelToken
        type: string
        required: true
        description: "Scoped channel token"
      expires_at:
        name: ExpiresAt
        type: int64
        required: true
        description: "Expiry (Unix epoch)"
      signature:
        name: Signature
        type: string
        required: true
        description: "Orchestrator signature"
```

### ChannelEntry

Stored record of an active channel in the orchestrator's channel registry.

```yaml
types:
  ChannelEntry:
    fields:
      channel_id:
        name: ChannelID
        type: string
        required: true
        description: "Unique channel identifier"
      from_agent:
        name: FromAgent
        type: string
        required: true
        description: "Requesting agent name"
      to_agent:
        name: ToAgent
        type: string
        required: true
        description: "Target agent name"
      purpose:
        name: Purpose
        type: string
        required: true
        description: "Why the channel was created"
      token:
        name: Token
        type: string
        required: true
        description: "Scoped channel token"
      created_at:
        name: CreatedAt
        type: int64
        required: true
        description: "Unix epoch of creation"
      expires_at:
        name: ExpiresAt
        type: int64
        required: true
        description: "Unix epoch of expiry"
```

---

## Health

### HealthStatus

```yaml
types:
  HealthStatus:
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Component name"
      status:
        name: Status
        type: string
        required: true
        description: "`healthy`, `degraded`, `unhealthy`"
      version:
        name: Version
        type: string
        required: true
        description: "Component version"
      uptime:
        name: Uptime
        type: int64
        required: true
        description: "Seconds since start"
      checks:
        name: Checks
        type: map
        required: false
        description: "Per-subsystem health: subsystem name → `ok`, `degraded` or `failed`. A component that names a failing subsystem says WHERE it is unwell; one that reports only `status` says that it is"
      metrics:
        name: Metrics
        type: map
        required: false
        description: "Component-specific metrics"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

The component's own name is `name` and its age is `uptime`. Neither is
`component` nor `uptime_seconds`: those were bound by
[`architecture/observability`](../architecture/observability.md) from this type
for a while, and since this type never had them, a generated orchestrator
emitted the observability names, satisfied observability's assertion, and failed
`L1-01` against this definition. **This table is the authority and every other
blueprint binds the names in it.**

---

## Audit

### AuditEntry

```yaml
types:
  AuditEntry:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique identifier"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      actor:
        name: Actor
        type: string
        required: true
        description: "Who performed the action"
      action:
        name: Action
        type: string
        required: true
        description: "Action type (see below)"
      target:
        name: Target
        type: string
        required: true
        description: "Affected resource"
      detail:
        name: Detail
        type: string
        required: true
        description: "Human-readable description"
      status:
        name: Status
        type: string
        required: true
        description: "`ok`, `denied`, `failed`"
      previous_hash:
        name: PreviousHash
        type: string
        required: true
        description: "SHA-256 hex digest of the previous entry's canonical JSON bytes; `\"0000...0000\"` (64 zeros) for the first entry — see [storage.md — Hash Chain Integrity](../architecture/storage.md#hash-chain-integrity)"
```

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

```yaml
types:
  EventEnvelope:
    fields:
      event_id:
        name: EventID
        type: string
        required: true
        description: "Globally unique event identifier (UUID v7 recommended — time-sortable)"
      topic:
        name: Topic
        type: string
        required: true
        description: "Dot-separated topic name (e.g., `workflow.completed`)"
      source:
        name: Source
        type: string
        required: true
        description: "Name of the publishing agent"
      scope:
        name: Scope
        type: string
        required: true
        description: "Target agent name, or `\"*\"` for global delivery"
      correlation_id:
        name: CorrelationID
        type: string
        required: false
        description: "Links all events in a single execution chain (e.g., one workflow run)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "Distributed trace context (propagated through all downstream operations)"
      version:
        name: Version
        type: string
        required: true
        description: "Schema version of the payload"
      payload:
        name: Payload
        type: map
        required: true
        description: "Event-specific data, typed per topic"
      token:
        name: Token
        type: string
        required: false
        description: "Auth token for delivery verification"
```

### Subscription

Declared in the agent manifest. Each entry registers interest in a
topic pattern with scope and concurrency controls.

```yaml
types:
  Subscription:
    fields:
      pattern:
        name: Pattern
        type: string
        required: true
        description: "Topic or wildcard pattern (supports `*` for single segment, `#` for multi-segment)"
      group:
        name: Group
        type: string
        required: false
        description: "Consumer group name. Events are load-balanced within a group. Defaults to agent name."
      scope:
        name: Scope
        type: string
        required: false
        description: "`\"self\"` (default), `\"*\"` (requires `event:observe`), or a specific agent name"
      max_concurrent:
        name: MaxConcurrent
        type: int
        required: false
        description: "Max parallel event processing for this subscription (default: 1)"
```

### RouteEntry

A single entry in the routing table. Represents one subscriber for a
topic pattern.

```yaml
types:
  RouteEntry:
    fields:
      agent:
        name: Agent
        type: string
        required: true
        description: "Subscriber agent name"
      url:
        name: URL
        type: string
        required: true
        description: "Subscriber's event endpoint (agent URL + `/v1/event`)"
      group:
        name: Group
        type: string
        required: false
        description: "Consumer group name"
      scope:
        name: Scope
        type: string
        required: true
        description: "Scope filter for this subscriber"
```

### DeadLetterEntry

An event that could not be delivered after all retry attempts.

```yaml
types:
  DeadLetterEntry:
    fields:
      original_event:
        name: OriginalEvent
        type: EventEnvelope
        required: true
        description: "The event that failed delivery"
      failure_reason:
        name: FailureReason
        type: string
        required: true
        description: "Error category (`HANDLER_ERROR`, `UNREACHABLE`, `TIMEOUT`, `REJECTED`)"
      last_error:
        name: LastError
        type: string
        required: true
        description: "Last error message from delivery attempt"
      attempts:
        name: Attempts
        type: int
        required: true
        description: "Total delivery attempts"
      first_attempt:
        name: FirstAttempt
        type: int64
        required: true
        description: "Unix epoch seconds of first attempt"
      last_attempt:
        name: LastAttempt
        type: int64
        required: true
        description: "Unix epoch seconds of final attempt"
      subscriber:
        name: Subscriber
        type: string
        required: true
        description: "Name of the subscriber that could not receive"
```

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
| `/v1/rotate-key` | POST | yes | orchestrator | Key rotation (see identity.md) |

---

## Error Handling

All errors across the protocol use the `ErrorResponse` type defined in the
Errors section above. Error categories (`transient`, `permanent`, `partial`)
determine retry behavior. Standard error codes are enumerated in the
ErrorResponse section with their HTTP status mappings.

Implementations MUST:
- Always return at minimum `{"error": "message"}`
- Include `code` and `category` when the information is available
- Use exact error codes from the central registry (agent-local codes are permitted — see Error Code Conventions)
- Map error codes to the correct HTTP status codes

---

## Scope

### ScopeLevel

Enumeration of universal scope levels. Scope classifies any resource,
operation, message, or data field.

| Value | Ordinal | Description |
|-------|---------|-------------|
| `public` | 0 | No restrictions — visible to anyone |
| `internal` | 1 | Visible within the hub only |
| `confidential` | 2 | Need-to-know basis with audit trail |
| `restricted` | 3 | Limited to authorized agents/roles |
| `critical` | 4 | Highest protection — requires approval for access |

### ScopeDeclaration

Attached to any resource, field, message, or operation to declare
its scope level.

```yaml
types:
  ScopeDeclaration:
    fields:
      target:
        name: Target
        type: string
        required: true
        description: "What is being scoped (field path, resource ID, operation name)"
      level:
        name: Level
        type: string
        required: true
        description: "ScopeLevel value"
      declared_by:
        name: DeclaredBy
        type: string
        required: true
        description: "Agent or system that declared the scope"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "When the scope was declared"
      justification:
        name: Justification
        type: string
        required: false
        description: "Why this scope level was chosen"
```

---

## Policy

### PolicyRule

A single declarative rule within a policy definition.

```yaml
types:
  PolicyRule:
    fields:
      rule:
        name: Rule
        type: string
        required: true
        description: "Rule type (e.g., `scope_required`, `rate_limit`, `capability_required`)"
      params:
        name: Params
        type: map
        required: true
        description: "Rule-specific parameters"
```

### PolicyDecision

Result of evaluating a policy against an operation context.

```yaml
types:
  PolicyDecision:
    fields:
      policy_name:
        name: PolicyName
        type: string
        required: true
        description: "Which policy was evaluated"
      decision:
        name: Decision
        type: DecisionResult
        required: true
        description: "Policy evaluation result — uses the canonical `DecisionResult` enum"
      rule_matched:
        name: RuleMatched
        type: string
        required: false
        description: "Which rule triggered the decision"
      reason:
        name: Reason
        type: string
        required: false
        description: "Human-readable explanation"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "When the decision was made"
```

---

## Safety

### OperationIntent

Pre-flight declaration of what an operation intends to do,
evaluated before the operation executes.

```yaml
types:
  OperationIntent:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique intent identifier"
      agent:
        name: Agent
        type: string
        required: true
        description: "Agent requesting the operation"
      operation:
        name: Operation
        type: string
        required: true
        description: "Operation class: `read`, `list`, `query`, `create`, `modify`, `delete`, `destroy`"
      resource:
        name: Resource
        type: string
        required: true
        description: "Target resource identifier"
      resource_class:
        name: ResourceClass
        type: string
        required: true
        description: "`ephemeral`, `application`, `system`, `critical`"
      scope:
        name: Scope
        type: string
        required: true
        description: "ScopeLevel of the target resource"
      environment:
        name: Environment
        type: string
        required: true
        description: "`development`, `staging`, `production`"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

### IntentDecision

Response to an OperationIntent — whether the operation may proceed.

```yaml
types:
  IntentDecision:
    fields:
      intent_id:
        name: IntentID
        type: string
        required: true
        description: "Which intent this decides"
      decision:
        name: Decision
        type: DecisionResult
        required: true
        description: "Canonical decision outcome (see Decision Taxonomy)"
      authority:
        name: Authority
        type: string
        required: true
        description: "Who/what made the decision"
      conditions:
        name: Conditions
        type: "[]string"
        required: false
        description: "Conditions attached to approval"
      reason:
        name: Reason
        type: string
        required: false
        description: Explanation
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

---

## Decision Taxonomy

All components that produce access decisions — enforcement boundaries,
safety gates, and policy evaluators — use a unified decision vocabulary.
Each component produces decisions from its own subset; enforcement
resolves them into a final action using most-restrictive-wins.

### DecisionResult

Canonical decision outcomes across all evaluation layers.

| Value | Ordinal | Description | Produced By |
|-------|---------|-------------|-------------|
| `allow` | 0 | Operation permitted | enforcement, safety, policy |
| `audit` | 1 | Operation permitted but logged for review | policy |
| `require_approval` | 2 | Operation held pending operator/admin approval | enforcement, safety |
| `escalate` | 3 | Operation held pending elevated authority approval | safety, policy |
| `deny` | 4 | Operation rejected | enforcement, safety, policy |
| `quarantine` | 5 | Operation rejected and agent isolated | enforcement |

Comparison: ordinal-based; higher ordinal = more restrictive.
Most-restrictive-wins: when multiple evaluations produce different
decisions, the highest ordinal prevails.

### Decision Mapping

When combining decisions from different layers, enforcement maps
each layer's output to the canonical DecisionResult:

| Layer | Layer Decision | Maps To |
|-------|---------------|---------|
| Policy | `allow` | `allow` |
| Policy | `audit` | `audit` — operation proceeds, decision logged for review |
| Policy | `escalate` | `escalate` — treated as `require_approval` with elevated authority |
| Policy | `deny` | `deny` |
| Safety | `allow` | `allow` |
| Safety | `require_approval` | `require_approval` |
| Safety | `deny` | `deny` |
| Safety | `escalate` | `escalate` |
| Enforcement | `allow` | `allow` |
| Enforcement | `require_approval` | `require_approval` |
| Enforcement | `deny` | `deny` |
| Enforcement | `quarantine` | `quarantine` — only enforcement can issue quarantine |

### Severity

Unified severity levels used by enforcement violations, security
events, and safety classifications.

| Value | Description |
|-------|-------------|
| `info` | Informational — no action required |
| `low` | Minor issue — logged |
| `medium` | Notable issue — may trigger alerts |
| `high` | Serious issue — immediate escalation |
| `critical` | Emergency — may trigger quarantine or kill-switch |

---

## Enforcement

### EnforcementDecision

Result of boundary inspection by the enforcement layer.

```yaml
types:
  EnforcementDecision:
    fields:
      id:
        name: ID
        type: string
        required: true
        description: "Unique decision identifier"
      boundary:
        name: Boundary
        type: string
        required: true
        description: "`message`, `storage`, `external`, `response`"
      agent:
        name: Agent
        type: string
        required: true
        description: "Agent whose operation was inspected"
      action:
        name: Action
        type: string
        required: true
        description: "DecisionResult value"
      violations:
        name: Violations
        type: "[]string"
        required: false
        description: "Policy/scope/privacy violations detected"
      privacy_actions:
        name: PrivacyActions
        type: "[]string"
        required: false
        description: "Privacy actions applied (masking, minimization)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "Correlation with distributed trace"
```

---

## Identity

### KeyRotationRequest

Defined in [protocol/identity.md](identity.md#key-rotation). Included
here for completeness — identity.md is the authoritative source.

```yaml
types:
  KeyRotationRequest:
    fields:
      agent_id:
        name: AgentID
        type: string
        required: true
        description: "Agent ID (32 hex chars)"
      new_public_key:
        name: NewPublicKey
        type: string
        required: true
        description: "New ML-DSA-65 public key (base64url-encoded, 1952 bytes)"
      current_signature:
        name: CurrentSignature
        type: string
        required: true
        description: "Agent manifest signed with current private key (base64url-encoded, 3309 bytes)"
      new_signature:
        name: NewSignature
        type: string
        required: true
        description: "Same manifest signed with new private key (base64url-encoded, 3309 bytes)"
      timestamp:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds"
```

---

## Logging

### LogEntry

Structured log entry emitted by agents. See [patterns/logging](../patterns/logging.md)
for the full logging specification.

```yaml
types:
  LogEntry:
    fields:
      ts:
        name: Timestamp
        type: int64
        required: true
        description: "Unix epoch seconds (consistent with all protocol timestamps)"
      level:
        name: Level
        type: string
        required: true
        description: "`debug`, `info`, `warn`, `error`, `fatal`"
      log_type:
        name: LogType
        type: string
        required: true
        description: "`app`, `access`, `audit`, `security`"
      msg:
        name: Message
        type: string
        required: true
        description: "Human-readable log message"
      component:
        name: Component
        type: string
        required: true
        description: "Agent or subsystem name"
      component_type:
        name: ComponentType
        type: string
        required: true
        description: "`agent`, `orchestrator`, `gateway`"
      trace_id:
        name: TraceID
        type: string
        required: false
        description: "Distributed trace correlation"
      span_id:
        name: SpanID
        type: string
        required: false
        description: "Span within trace"
      error:
        name: Error
        type: string
        required: false
        description: "Error message (when level is error/fatal)"
```

### TraceContext

Distributed trace propagation context (W3C Trace Context compatible).

```yaml
types:
  TraceContext:
    fields:
      trace_id:
        name: TraceID
        type: string
        required: true
        description: "32-char hex trace identifier"
      span_id:
        name: SpanID
        type: string
        required: true
        description: "16-char hex span identifier"
      parent_span_id:
        name: ParentSpanID
        type: string
        required: false
        description: "Parent span for nesting"
      sampled:
        name: Sampled
        type: bool
        required: false
        description: "Whether this trace is sampled (default: true)"
```

---

## Security

```yaml
security:
  transport:
    - Types are serialized as JSON over HTTP
    - All string fields MUST be validated for maximum length before processing
    - No executable content in any type field
  signing:
    algorithm: ML-DSA-65
    key_type: 1952-byte public / 4032-byte private (FIPS 204)
    process: Signature fields contain base64url-encoded ML-DSA-65 signatures
  verification:
    process: All signature fields verified against sender public key
  type_safety:
    - Required fields MUST be validated before processing
    - Enum fields MUST be validated against allowed values
    - IDs MUST be validated as 32-char hex strings
    - Timestamps MUST be validated as positive integers
    - Unknown fields MUST be silently ignored (forward compatibility)
  string_limits:
    - Identifiers (name, agent_name, topic, action): max 128 characters
    - Descriptions and messages: max 1024 characters
    - Payload fields (JSON objects): max 1 MiB serialized
    - URL fields: max 2048 characters
    - Base64url-encoded keys/signatures: validated by expected decoded byte lengths (1952 for public keys, 3309 for signatures)
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
- [ ] ML-DSA-65 signatures serialize as base64url-encoded 3309 bytes; public keys serialize as base64url-encoded 1952 bytes
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
- [ ] AgentMessage `signature` covers `canonicalize({from, to, action, payload})` per RFC 8785 and `trace_id` propagates through downstream calls
- [ ] Finding includes all required fields: `rule_id`, `severity`, `element`, `current`, `expected`, `message`, and `fixable`
- [ ] RegisterResponse includes `agent_id`, `token`, `expires_at`, `services`, `orchestrator`, and negotiated `protocol_version`
- [ ] ChannelGrant includes `channel_id`, scoped `channel_token`, `target_url`, `target_pub_key`, and `expires_at`
- [ ] Protocol paths are all prefixed with `/v1` and method/auth requirements match the Protocol Paths table
- [ ] DeadLetterEntry includes `original_event`, `failure_reason`, `last_error`, `attempts`, and `subscriber`
- [ ] ScopeLevel enum is constrained to `public`, `internal`, `confidential`, `restricted`, `critical`
- [ ] ScopeDeclaration requires `target`, `level`, `declared_by`, and `timestamp`
- [ ] PolicyDecision requires `policy_name`, `decision`, and `timestamp`; decision uses DecisionResult enum
- [ ] OperationIntent requires `id`, `agent`, `operation`, `resource`, `resource_class`, `scope`, `environment`, and `timestamp`; operation includes `list` and `query`
- [ ] IntentDecision requires `intent_id`, `decision`, `authority`, and `timestamp`; decision uses DecisionResult enum
- [ ] EnforcementDecision requires `id`, `boundary`, `agent`, `action`, `timestamp`, and `trace_id`; boundary includes `response`
- [ ] DecisionResult enum is constrained to `allow`, `audit`, `require_approval`, `escalate`, `deny`, `quarantine` with ordinal-based comparison
- [ ] Severity enum is constrained to `info`, `low`, `medium`, `high`, `critical` — used consistently across enforcement, security, and safety
- [ ] Decision mapping table resolves policy/safety/enforcement decisions to canonical DecisionResult using most-restrictive-wins
- [ ] All protocol-level error codes (standard, enforcement, contract, federation, safety, policy, identity, common) are registered centrally; agent-local codes use domain-descriptive names and do not collide with registered codes
- [ ] Administrative authority is expressed as `admin:` capabilities in the standard list — not as a separate role model — and `admin:*` denotes the whole family
