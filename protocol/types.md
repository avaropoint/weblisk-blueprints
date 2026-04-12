<!-- blueprint
type: protocol
name: types
version: 1.0.0
requires: []
platform: any
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

## Agent Identity

### AgentManifest

Describes an agent's identity, capabilities, and interface contract.
Returned by `POST /v1/describe` and sent during registration.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Agent identifier (lowercase, no spaces) |
| Version | string | `version` | yes | Semver version |
| Description | string | `description` | yes | Human-readable purpose |
| URL | string | `url` | yes | Agent's HTTP base URL |
| PublicKey | string | `public_key` | yes | Hex-encoded Ed25519 public key |
| Capabilities | []Capability | `capabilities` | yes | What this agent can do |
| Inputs | []IOSpec | `inputs` | no | Expected input parameters |
| Outputs | []IOSpec | `outputs` | no | What this agent produces |
| Collaborators | []string | `collaborators` | no | Agent names this agent works with |
| Approval | string | `approval` | no | `"required"` or `"auto"` (default: `"required"`) |

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
- `http:get` — make external HTTP requests

### IOSpec

Describes an input or output parameter.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Name | string | `name` | yes | Parameter name |
| Type | string | `type` | yes | Data type: `file_list`, `json`, `text` |
| Description | string | `description` | yes | Human-readable description |

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
| CreatedAt | datetime | `created_at` | yes | ISO 8601 timestamp |
| UpdatedAt | datetime | `updated_at` | yes | ISO 8601 timestamp |
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

Sent by the orchestrator to an agent's `POST /v1/execute` endpoint,
or submitted to the orchestrator's `POST /v1/task` endpoint.

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
| Timestamp | datetime | `timestamp` | yes | When observed |
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
| CreatedAt | datetime | `created_at` | yes | When created |
| ResolvedAt | datetime | `resolved_at` | no | When resolved |

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
| Timestamp | datetime | `timestamp` | yes | When recorded |

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

### OrchestratorInfo

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| URL | string | `url` | yes | Orchestrator base URL |
| PublicKey | string | `public_key` | yes | Hex Ed25519 public key |
| Version | string | `version` | yes | Protocol version |

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
| Timestamp | datetime | `timestamp` | yes | ISO 8601 timestamp |
| Actor | string | `actor` | yes | Who performed the action |
| Action | string | `action` | yes | Action type (see below) |
| Target | string | `target` | yes | Affected resource |
| Detail | string | `detail` | yes | Human-readable description |
| Status | string | `status` | yes | `ok`, `denied`, `failed` |

**Action types:** `register`, `deregister`, `task`, `channel`, `message`,
`observation`, `recommendation`, `feedback`, `strategy`

---

## Protocol Paths

All paths are prefixed with `/v1`.

| Path | Method | Auth | Component | Purpose |
|------|--------|------|-----------|---------|
| `/v1/describe` | POST | no | agent | Return manifest |
| `/v1/execute` | POST | yes | agent | Execute task |
| `/v1/health` | GET | no | both | Health check |
| `/v1/message` | POST | yes | agent | Agent messaging |
| `/v1/services` | GET/POST | yes | both | Service directory |
| `/v1/register` | POST | no | orchestrator | Agent registration |
| `/v1/register` | DELETE | yes | orchestrator | Agent deregistration |
| `/v1/task` | POST | yes | orchestrator | Submit task |
| `/v1/channel` | POST | yes | orchestrator | Broker channel |
| `/v1/audit` | GET | yes | orchestrator | Audit log |
| `/v1/strategy` | GET/POST | yes | orchestrator | Strategy management |
| `/v1/observations` | GET | yes | orchestrator | Observation history |
| `/v1/context` | GET/POST | yes | orchestrator | Entity context |
