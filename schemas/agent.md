# Agent Schema

Defines the complete structure for agent blueprints (`type: agent`).
Agent blueprints specify infrastructure services that run as autonomous
processes within the Weblisk framework. Every agent blueprint MUST
conform to this schema in addition to the rules in [common.md](common.md).

---

## Frontmatter

Agent blueprints require all common fields plus agent-specific fields.

```yaml
<!-- blueprint
type: agent
kind: infrastructure|work|domain
name: <agent-name>
version: <semver>
port: <9700-9999>
requires: [<type/name>, ...]
extends: [<patterns/name>, ...]
depends_on: [<agent-name>, ...] | []
platform: any|go|cloudflare|node|rust
tier: free|pro
domain: <domain-name>          # required for kind: work
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `agent` | Blueprint type |
| `kind` | enum | `infrastructure`, `work`, or `domain` | Agent classification |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `port` | integer | 9700–9999, unique across all agents | Default port assignment |
| `requires` | list | References existing blueprints | Build-time dependencies |
| `extends` | list | References pattern blueprints only | Inherited pattern contracts |
| `depends_on` | list | References agent/domain names, or `[]` | Runtime agent dependencies |
| `platform` | enum | `any`, `go`, `cloudflare`, `node`, `rust` | Target platform |
| `tier` | enum | `free` or `pro` | Availability tier |
| `domain` | string | Required for `kind: work`; must match existing domain | Domain membership |

---

## Required Section Order

Agent blueprints MUST include these sections in this exact order.
Sections marked Optional may be omitted but if present must appear
at the listed position.

| # | Section | Heading | Required | Description |
|---|---------|---------|----------|-------------|
| 1 | Frontmatter | `<!-- blueprint -->` | **Yes** | YAML metadata in HTML comment |
| 2 | Title | `# Name` | **Yes** | Level-1 heading + summary paragraph |
| 3 | Overview | `## Overview` | **Yes** | 2–5 sentence scope description |
| 4 | Dependencies | `## Dependencies` | **Yes** | Full YAML dependency contracts |
| 5 | Configuration | `## Configuration` | **Yes** | Runtime parameters in YAML |
| 6 | Types | `## Types` | **Yes** | Data structures in YAML |
| 7 | Storage | `## Storage` | Conditional | Required if agent persists data |
| 8 | State Machine | `## State Machine` | **Yes** | Agent and entity state transitions |
| 9 | Lifecycle | `## Lifecycle` | **Yes** | Startup, shutdown, health, self-update |
| 10 | Triggers | `## Triggers` | **Yes** | Events, schedules, messages that activate the agent |
| 11 | Actions | `## Actions` | **Yes** | Message handlers with full specs |
| 12 | Execute Workflow | `## Execute Workflow` | **Yes** | Core processing loop |
| 13 | Collaboration | `## Collaboration` | **Yes** | Events published/subscribed, direct messages |
| 14 | Manual Overrides | `## Manual Overrides` | **Yes** | Override policy, levels, audit |
| 15 | Constraints | `## Constraints` | **Yes** | Blast radius, forbidden actions, resource limits |
| 16 | Error Handling | `## Error Handling` | **Yes** | Permanent and transient errors |
| 17 | Observability | `## Observability` | **Yes** | Logs, metrics, alerts |
| 18 | Security | `## Security` | **Yes** | Permissions, data sensitivity, access control |
| 19 | Test Fixtures | `## Test Fixtures` | **Yes** | Happy path, error cases, edge cases |
| 20 | Scaling | `## Scaling` | **Yes** | Horizontal model, coordination, blue-green |
| 21 | Implementation Notes | `## Implementation Notes` | **Yes** | Practical guidance |
| 22 | Verification Checklist | `## Verification Checklist` | **Yes** | Testable assertions (min 10) |

### Optional Sections

These sections may be included when relevant. If present, they appear
after the section they extend:

| Section | Insert After | When Needed |
|---------|-------------|-------------|
| `## Cron Expression Format` | Execute Workflow | Agents with schedule-based triggers |
| `## Restore Procedure` | Storage | Agents with backup/restore |
| `## Examples` | Any section | Extended examples beyond test fixtures |

---

## Section Specifications

### Dependencies (`## Dependencies`)

Full YAML dependency contracts. See [common.md](common.md) Dependencies Section
for the complete structure. Agent blueprints MUST declare:

- **requires**: All blueprints listed in frontmatter `requires`
- **extends**: All patterns listed in frontmatter `extends`
- **depends_on**: Runtime agent dependencies or `[]`

Every agent MUST declare these minimum dependencies:
- `protocol/spec` (wire protocol)
- `protocol/types` (shared types)
- `architecture/agent` (agent framework)

### Configuration (`## Configuration`)

```yaml
config:
  parameter_name:
    type: <scalar-type>
    default: <value>
    env: WL_<AGENT>_<PARAM>
    min: <number>
    max: <number>
    enum: [val1, val2]
    unit: <unit>
    description: What this parameter controls
```

See [common.md](common.md) Configuration Section for full specification.

### Types (`## Types`)

All data structures the agent defines. See [common.md](common.md) Types Section
for the complete YAML format, scalar types, and constraint properties.

Must include a preamble:
```markdown
Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.
```

### Storage (`## Storage`)

Required if the agent persists any data. See [common.md](common.md) Storage Section
for the complete structure.

Must include:
- `engine` declaration
- `tables` with `source_type` references to Types section
- `indexes` for every query pattern used in Actions and Execute Workflow
- `relationships` between tables
- `retention` policy for every table
- `backup` configuration for every table

If followed by a `### Restore Procedure`, include numbered steps with
validation gates.

### State Machine (`## State Machine`)

Declares all valid states and transitions for the agent itself and
for any entities it manages.

```yaml
state_machine:
  agent:
    initial: <state>
    transitions:
      - from: <state>
        to: <state>
        trigger: <event-or-action>
        validates: <condition>
        side_effect: <optional-action>

  entity.<TypeName>:
    initial: <state>
    transitions:
      - from: <state>
        to: <state>
        trigger: <event-or-action>
        validates: <condition>
        side_effect: <optional-action>
```

#### Agent States (required)

Every agent MUST declare these core states:

| State | Description |
|-------|-------------|
| `created` | Process started, not yet registered |
| `registered` | Registered with orchestrator, not yet operational |
| `active` | Fully operational |
| `degraded` | Operating with reduced capability (e.g., storage errors) |
| `retiring` | Shutting down gracefully |
| `retired` | Shutdown complete |

Additional states may be added for agent-specific needs (e.g., `standby`).

#### Entity States

For each managed type that has lifecycle states, declare the state machine.
The `status` field in the type's `enum` MUST match the declared states.

#### Validation Rules

1. Every `from` and `to` state must be declared (no implicit states)
2. `initial` must be a valid state
3. Every state must be reachable from `initial`
4. `retiring` and `retired` must be reachable from all operational states
5. Triggers must reference actions, events, or system signals
6. `validates` must be a testable condition

### Lifecycle (`## Lifecycle`)

Declares the agent's startup sequence, shutdown sequence, health
reporting, and self-update behavior.

#### Startup Sequence

A numbered sequence of steps. Each step MUST include:

```
Step N — Step Name
  Action:      What the step does
  Pre-check:   What must be true before this step runs
  Validates:   How success is verified
  On Fail:     What happens on failure (RETRY, EXIT, degrade)
  Backout:     How to reverse this step if a later step fails
```

#### Shutdown Sequence

A numbered sequence of steps. Each step MUST include:

```
Step N — Step Name
  Action:      What the step does
  Validates:   How completion is verified
```

#### Health

Declares health endpoint response for each state:

```yaml
health:
  healthy:
    conditions: [list]
    response:
      status: healthy
      details: {fields}

  degraded:
    conditions: [list]
    response:
      status: degraded
      details: {fields}

  unhealthy:
    conditions: [list]
    response:
      status: unhealthy
      details: {fields}
```

#### Self-Update

How the agent responds to `system.blueprint.changed` for its own blueprint:

1. Validate new blueprint
2. Check migration requirements
3. Execute migration (if needed, with rollback)
4. Reload configuration
5. Log version update

### Triggers (`## Triggers`)

All events, schedules, and messages that activate the agent.

```yaml
triggers:
  - name: <trigger-name>
    type: schedule|event|message
    # For schedule:
    interval: <config-reference>
    # For event:
    topic: <event-topic>
    filter: <optional-condition>
    # For message:
    endpoint: POST /v1/message
    actions: [action1, action2, ...]
    description: What this trigger does
```

#### Validation Rules

1. Every trigger must have `name`, `type`, and `description`
2. Schedule triggers must reference a config parameter or cron expression
3. Event triggers must reference topics declared in Dependencies
4. Message triggers must list all actions handled by this agent
5. Every action listed in the message trigger must have a corresponding
   entry in the Actions section

### Actions (`## Actions`)

Each action the agent handles via `POST /v1/message`. Every action
MUST include all of these subsections:

```markdown
### action_name

Purpose description.

**Purpose:** One-sentence description of what this action does.

**Input:** `{field: type, field: type}` — with references to Types

**Processing:**
```
Numbered steps with validation, queries, state transitions
```

**Output:** `{field: type, field: type}`

**Errors:**
```yaml
errors:
  - code: ERROR_CODE
    condition: When this error occurs
    retryable: true|false
```

**Side Effects:** Storage writes, events emitted, state changes

**Idempotency:** How duplicate calls are handled

**Manual Override:** Whether operators can invoke this (optional)
```

#### Validation Rules

1. Every action listed in the Triggers message trigger must be defined here
2. Every action must have: Purpose, Input, Processing, Output, Errors, Side Effects, Idempotency
3. Input/Output types must reference types from the Types section
4. Error codes must be declared in the Error Handling section
5. Side effects must reference storage tables, events, or state transitions from other sections
6. Processing steps must reference constraints, indexes, and relationships by name

### Execute Workflow (`## Execute Workflow`)

The agent's core processing loop. For agents with a tick/cycle model,
this is the tick loop. For event-driven agents, this is the main
event processing pipeline.

Format: Numbered phases with queries, decisions, and outcomes.

```
Phase N — Phase Name
  Query/Action:  What happens
  Decision:      Branching logic (if applicable)
  Result:        What this phase produces
```

Each phase must reference:
- Storage tables and indexes used (by name)
- Types and constraints validated
- Events published
- Metrics emitted

### Collaboration (`## Collaboration`)

Declares all event publishing, subscribing, and direct messaging.

```yaml
events_published:
  - topic: <namespace.event.name>
    payload: {field: type, ...}
    when: Condition that triggers publication

events_subscribed:
  - topic: <namespace.event.name>
    payload: {field: type, ...}
    action: What happens when this event is received

direct_messages:
  - target: <agent-name or variable>
    action: <action-name>
    when: Condition that triggers the message
    reason: Why direct messaging is needed (vs events)
```

#### Validation Rules

1. Published event topics must use namespaces owned by this agent
2. Subscribed event topics must be declared in Dependencies bindings
3. Direct message targets must be declared in `depends_on` or as dynamic references
4. Every published event must have `topic`, `payload`, and `when`
5. Every subscribed event must have `topic`, `payload`, and `action`

### Manual Overrides (`## Manual Overrides`)

```yaml
override_policy: full-auto|supervised|manual-only

override_levels:
  full-auto:     Description
  supervised:    Description
  manual-only:   Description

overridable_behaviors:
  - behavior: <behavior-name>
    default: enabled|disabled
    override: How to override
    audit: logged|silent

manual_actions:
  - action: <action-name>
    description: What this action does
    allowed: operator|admin

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: Source of identity
  why: Required|Optional
  storage: Where audit entries are stored
```

### Constraints (`## Constraints`)

```yaml
constraints:
  blast_radius:
    - MUST NOT constraint describing boundary
    - Another boundary constraint

  forbidden_actions:
    - MUST NOT do X
    - MUST NOT do Y

  resource_limits:
    memory: <limit>
    <resource>: <limit>
```

#### Validation Rules

1. `blast_radius` must have at least 2 constraints
2. `forbidden_actions` must have at least 2 constraints
3. `resource_limits` must declare `memory` at minimum
4. All constraints must use RFC 2119 language (MUST, MUST NOT)

### Error Handling (`## Error Handling`)

```yaml
errors:
  permanent:
    - code: ERROR_CODE
      description: When this error occurs

  transient:
    - code: ERROR_CODE
      description: When this error occurs
      fallback: What happens when this error occurs
```

#### Validation Rules

1. Every error code referenced in Actions must be declared here
2. Permanent errors must not have `fallback` (they are terminal)
3. Transient errors MUST have `fallback`
4. Error codes must be UPPER_SNAKE_CASE

### Observability (`## Observability`)

```yaml
custom_log_types:
  - log_type: <agent.event.name>
    level: debug|info|warn|error
    when: Condition
    fields: {field1, field2}

metrics:
  - name: wl_<agent>_<metric>
    type: gauge|counter|histogram
    labels: [label1, label2]
    description: What this metric measures

alerts:
  - condition: Alert condition
    severity: warn|high|critical
    routing: <target-agent>
```

#### Naming Conventions

- Log types: `<agent>.<event>.<detail>` (lowercase, dot-separated)
- Metrics: `wl_<agent>_<metric>` (lowercase, underscore-separated, `wl_` prefix)
- Alert routing: Must reference the alerting agent or a declared collaborator

### Security (`## Security`)

```yaml
security:
  permissions:
    - capability: <capability-name>
      resources: [resource-list]
      description: Why this capability is needed

  data_sensitivity:
    - data: What data
      classification: low|medium|high|critical
      handling: How it is handled

  access_control:
    - caller: <caller-identity>
      actions: [action-list]
    - caller: Unauthenticated
      actions: []
      note: Explanation of why blocked
```

#### Validation Rules

1. `permissions` must list every capability the agent uses
2. `data_sensitivity` must classify every data type stored or processed
3. `access_control` must have an entry for every caller type
4. `access_control` MUST include a `caller: Unauthenticated` entry with `actions: []`
5. Resources must reference actual tables, agents, or namespaces
6. See [compliance.md](compliance.md) SEC001–SEC012 for security validation rules

### Test Fixtures (`## Test Fixtures`)

Organized into three subsections:

```markdown
### Happy Path
```yaml
tests:
  - name: Test name
    action: action_name
    input: {fields}
    expected: {fields}
    validates: [what this test proves]
```

### Error Cases
```yaml
  - name: Test name
    action: action_name
    input: {fields}
    expected_error: ERROR_CODE
    validates: [what this test proves]
```

### Edge Cases
```yaml
  - name: Test name
    action|trigger: action_name|trigger_name
    condition: Special circumstance
    expected: Behavior
    validates: [what this test proves]
```
```

#### Validation Rules

1. Must include all three subsections (Happy Path, Error Cases, Edge Cases)
2. Happy path tests must cover at least every action
3. Error case tests must cover at least every permanent error code
4. Edge case tests must cover at least: idempotency, concurrent access, resource limits

### Scaling (`## Scaling`)

```yaml
scaling:
  model: horizontal|vertical|none
  min_instances: <int>
  max_instances: <int>|unbounded

  inter_agent:
    protocol: message-bus-only|direct-http-allowed
    routing: <routing-strategy>
    reason: Why this routing model

  intra_agent:
    coordination: shared-storage|shared-nothing|leader-election
    leader_election:
      mechanism: <how leader is chosen>
      leader: [responsibilities]
      follower: [responsibilities]
      promotion: <how follower becomes leader>
    state_sharing:
      mechanism: <how state is shared>
      consistency_window: <duration>
      conflict_resolution: <strategy>

  event_handling:
    consumer_group: <group-name>
    delivery: one-per-group|broadcast
    description: Delivery semantics

  blue_green:
    strategy: immediate|gradual
    shadow_duration: <seconds>
    shadow_events_required: <count>
    cutover_watch_period: <seconds>
    storage_sharing: <strategy>
    consumer_groups:
      shadow_phase: <group-config>
      after_cutover: <group-config>
```

### Implementation Notes (`## Implementation Notes`)

Prose section (not YAML). Must cover:
1. Key design decisions and rationale
2. Common pitfalls and how to avoid them
3. Performance considerations
4. Security requirements specific to this agent
5. Testing approach
6. Relationship integrity notes (if Storage is declared)

### Verification Checklist (`## Verification Checklist`)

Minimum 10 items. Must cover:
- Happy path for every action
- State machine transitions
- Constraint enforcement
- Security boundaries
- Lifecycle startup/shutdown
- Dependency contract validation
- Scaling behavior
- Blue-green deployment
- Error handling and recovery

---

## Complete Template

Copy this template to create a new agent blueprint. Replace all
`<placeholder>` values and fill in all sections.

````markdown
<!-- blueprint
type: agent
kind: <infrastructure|work|domain>
name: <agent-name>
version: 1.0.0
port: <9700-9999>
requires: [protocol/spec, protocol/types, architecture/agent]
extends: [patterns/observability, patterns/security, patterns/governance]
depends_on: []
platform: any
tier: free
-->

# <Agent Name>

<One-sentence summary of what this agent does.>

## Overview

<2–5 sentences describing the agent's purpose, scope, and design
philosophy. Must be self-contained.>

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST, DELETE]
          request_type: AgentManifest
          response_fields: [agent_id, token, services]
        - path: /v1/message
          methods: [POST]
          request_type: AgentMessage
          response_fields: [status, response]
        - path: /v1/health
          methods: [POST]
          response_fields: [status, details]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TaskRequest
          fields_used: [id, from, target_agent, payload, context]
        - name: TaskResult
          fields_used: [task_id, agent_name, status, summary, timestamp]
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
        - name: EventEnvelope
          fields_used: [from, to, action, payload, trace_id]
        - name: HealthStatus
          fields_used: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: startup-sequence
          parameters: [identity, storage, registration, health]
        - behavior: shutdown-sequence
          parameters: [drain, deregister, close]
        - behavior: health-reporting
          parameters: [status, details]
    on_change:
      compatible: validate
      breaking: version-bump
      removed: halt-immediately

  # Add additional requires entries as needed...

extends:
  - pattern: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: health-endpoint
          parameters: [status, details]
        - behavior: metrics
          parameters: [gauge, counter, histogram]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: capability-enforcement
          parameters: [permissions, access_control]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - pattern: patterns/governance
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: policy-enforcement
          parameters: [override_policy, audit]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  # Add additional extends entries as needed...

depends_on: []
  # List runtime agent dependencies, or [] if none.
```

---

## Configuration

```yaml
config:
  # example_param:
  #   type: int
  #   default: 60
  #   env: WL_<AGENT>_EXAMPLE_PARAM
  #   min: 1
  #   max: 3600
  #   unit: seconds
  #   description: What this parameter controls
```

---

## Types

Types are the single source of truth. Storage tables, action inputs,
and event payloads all reference these definitions.

```yaml
types:
  # ExampleType:
  #   description: What this type represents
  #   fields:
  #     id:
  #       type: string
  #       format: uuid-v7
  #       description: Unique identifier
  #   constraints:
  #     - name: constraint_name
  #       type: unique
  #       fields: [field1]
  #       description: Why this constraint exists
```

---

## Storage

```yaml
storage:
  engine: sqlite

  tables:
    # table_name:
    #   source_type: TypeName
    #   primary_key: field_name
    #   indexes:
    #     - name: idx_name
    #       fields: [field1]
    #       type: btree
    #       description: Why this index exists

  relationships:
    # - name: relationship_name
    #   from: table.field
    #   to: table.field
    #   cardinality: many-to-one
    #   on_delete: cascade
    #   on_update: restrict
    #   description: Why this relationship exists

  retention:
    # table_name:
    #   policy: indefinite
    #   cleanup: manual

  backup:
    # table_name:
    #   frequency: daily
    #   format: JSON
    #   path: .weblisk/backups/<agent>/<table>_{ISO8601}.json
```

---

## State Machine

```yaml
state_machine:
  agent:
    initial: created
    transitions:
      - from: created
        to: registered
        trigger: orchestrator_ack
        validates: agent_id assigned in response
      - from: registered
        to: active
        trigger: initialization_complete
        validates: all startup steps passed
      - from: active
        to: degraded
        trigger: <degradation-condition>
        validates: <condition>
      - from: degraded
        to: active
        trigger: <recovery-condition>
        validates: <condition>
      - from: active
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: degraded
        to: retiring
        trigger: shutdown_signal
        validates: signal received
      - from: retiring
        to: retired
        trigger: drain_complete
        validates: in_flight = 0 or timeout
```

---

## Lifecycle

### Startup Sequence

```
Step 1 — Load Configuration
  Action:      Read environment variables, apply defaults from config block
  Pre-check:   Process has read access to environment
  Validates:   All config values within declared min/max/enum constraints
  On Fail:     EXIT with CONFIG_INVALID
  Backout:     None

Step 2 — Load Identity
  Action:      Generate or load Ed25519 keypair
  Pre-check:   .weblisk/keys/ directory exists and is writable
  Validates:   Public key is 32 bytes
  On Fail:     EXIT with IDENTITY_FAILED
  Backout:     None

Step 3 — Initialize Storage
  Action:      Connect to storage engine
  Pre-check:   Storage engine available
  Validates:   SELECT 1 succeeds within 5 seconds
  On Fail:     RETRY 3x → EXIT with STORAGE_UNREACHABLE
  Backout:     Close partial connection

Step 4 — Validate Schema
  Action:      Compare storage tables against Types block
  Pre-check:   Storage connected
  Validates:   Tables, columns, indexes, constraints, relationships match
  On Fail:     Run migration → if fails, ROLLBACK → EXIT
  Backout:     Reverse migration steps

Step 5 — Register with Orchestrator
  Action:      POST /v1/register with AgentManifest
  Pre-check:   Steps 1-4 validated
  Validates:   HTTP 200, agent_id returned
  On Fail:     RETRY 3x → EXIT with REGISTRATION_FAILED
  Backout:     None (idempotent)

Step 6 — Subscribe to Events
  Action:      Subscribe to declared event topics
  Pre-check:   Registered with orchestrator
  Validates:   All subscriptions acknowledged
  On Fail:     Unsubscribe partial → deregister → EXIT
  Backout:     Unsubscribe all, deregister, close storage

<Add agent-specific startup steps here>

Final:
  agent_state → active
  Log: lifecycle.ready {port, <agent-specific-fields>}
```

### Shutdown Sequence

```
Step 1 — Receive Signal
  Action:      Accept SIGTERM, system.shutdown, or API call
  Validates:   Signal recognized
  agent_state → retiring

Step 2 — Stop Accepting Work
  Action:      Return 503 for new requests
  Validates:   No new work accepted

<Add agent-specific drain steps here>

Step N-2 — Deregister
  Action:      DELETE /v1/register
  Validates:   Orchestrator acknowledges

Step N-1 — Close Storage
  Action:      Close database connection
  Validates:   Connection closed

Step N — Exit
  Log: lifecycle.stopped {uptime, <metrics>}
  agent_state → retired
```

### Health

```yaml
health:
  healthy:
    conditions: [<condition-list>]
    response:
      status: healthy
      details: {<field-list>}

  degraded:
    conditions: [<condition-list>]
    response:
      status: degraded
      details: {<field-list>}

  unhealthy:
    conditions: [<condition-list>]
    response:
      status: unhealthy
      details: {<field-list>}
```

### Self-Update

```
Step 1 — Validate New Blueprint
Step 2 — Check Migration
Step 3 — Execute Migration (if needed, with rollback)
Step 4 — Reload Configuration
Final: Log lifecycle.version_updated
```

---

## Triggers

```yaml
triggers:
  - name: <trigger-name>
    type: <schedule|event|message>
    description: <what-this-trigger-does>
```

---

## Actions

### <action_name>

**Purpose:** <description>

**Input:** `{<fields>}`

**Processing:**
```
1. Step one
2. Step two
```

**Output:** `{<fields>}`

**Errors:**
```yaml
errors:
  - code: <ERROR_CODE>
    condition: <when>
    retryable: <true|false>
```

**Side Effects:** <storage, events, state changes>

**Idempotency:** <how duplicates are handled>

---

## Execute Workflow

```
Phase 1 — <Phase Name>
  <Description>

Phase 2 — <Phase Name>
  <Description>
```

---

## Collaboration

```yaml
events_published:
  - topic: <agent>.<event>.<detail>
    payload: {<fields>}
    when: <condition>

events_subscribed:
  - topic: <namespace>.<event>
    payload: {<fields>}
    action: <handler>

direct_messages:
  - target: <agent-name>
    action: <action>
    when: <condition>
    reason: <why-not-events>
```

---

## Manual Overrides

```yaml
override_policy: supervised

override_levels:
  full-auto:     <description>
  supervised:    <description>
  manual-only:   <description>

overridable_behaviors:
  - behavior: <name>
    default: enabled
    override: <how>
    audit: logged

manual_actions:
  - action: <name>
    description: <what>
    allowed: operator

override_audit:
  fields: [who, what, when, why, previous_state, new_state]
  who: <identity-source>
  why: Required
  storage: <audit-log-location>
```

---

## Constraints

```yaml
constraints:
  blast_radius:
    - MUST NOT <boundary-constraint>
    - MUST NOT <boundary-constraint>

  forbidden_actions:
    - MUST NOT <forbidden-action>
    - MUST NOT <forbidden-action>

  resource_limits:
    memory: <limit>
```

---

## Error Handling

```yaml
errors:
  permanent:
    - code: <ERROR_CODE>
      description: <condition>

  transient:
    - code: <ERROR_CODE>
      description: <condition>
      fallback: <behavior>
```

---

## Observability

```yaml
custom_log_types:
  - log_type: <agent>.<event>
    level: <level>
    when: <condition>
    fields: {<fields>}

metrics:
  - name: wl_<agent>_<metric>
    type: <gauge|counter|histogram>
    labels: [<labels>]
    description: <what>

alerts:
  - condition: <alert-condition>
    severity: <warn|high|critical>
    routing: <target-agent>
```

---

## Security

```yaml
security:
  permissions:
    - capability: <capability>
      resources: [<resources>]
      description: <why>

  data_sensitivity:
    - data: <what>
      classification: <low|medium|high|critical>
      handling: <how>

  access_control:
    - caller: <identity>
      actions: [<actions>]
    - caller: Unauthenticated
      actions: []
      note: All endpoints require valid token
```

---

## Test Fixtures

### Happy Path

```yaml
tests:
  - name: <test-name>
    action: <action>
    input: {<fields>}
    expected: {<fields>}
    validates: [<assertions>]
```

### Error Cases

```yaml
  - name: <test-name>
    action: <action>
    input: {<fields>}
    expected_error: <ERROR_CODE>
    validates: [<assertions>]
```

### Edge Cases

```yaml
  - name: <test-name>
    action|trigger: <name>
    condition: <circumstance>
    expected: <behavior>
    validates: [<assertions>]
```

---

## Scaling

```yaml
scaling:
  model: horizontal
  min_instances: 1
  max_instances: unbounded

  inter_agent:
    protocol: message-bus-only
    routing: <strategy>
    reason: <rationale>

  intra_agent:
    coordination: <strategy>

  event_handling:
    consumer_group: <name>
    delivery: one-per-group

  blue_green:
    strategy: <immediate|gradual>
    shadow_duration: <seconds>
    cutover_watch_period: <seconds>
```

---

## Implementation Notes

- <Key design decisions>
- <Common pitfalls>
- <Performance considerations>
- <Security specifics>
- <Testing approach>

---

## Verification Checklist

- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
- [ ] <Testable assertion>
````
