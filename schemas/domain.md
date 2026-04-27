# Domain Schema

Defines the complete structure for domain controller blueprints
(`type: domain`). Domain controllers own a business function — they
receive high-level tasks, decompose them into multi-agent workflows,
dispatch work to specialized agents, aggregate results, and manage
the continuous optimization lifecycle.

Domain controllers share most structural requirements with agents
(they are agent processes) but add workflow orchestration, agent
dispatch, aggregation, and domain-specific intelligence. This schema
inherits from the agent schema and extends it with domain-specific
sections.

---

## Frontmatter

```yaml
<!-- blueprint
type: domain
kind: domain
name: <domain-name>
version: <semver>
port: <9700-9999>
requires: [<type/name>, ...]
extends: [patterns/domain-controller, <patterns/name>, ...]
depends_on: [<agent-name>, ...]
platform: any|<specific>
tier: free|pro
-->
```

### Required Fields

| Field | Type | Constraint | Description |
|-------|------|-----------|-------------|
| `type` | enum | Must be `domain` | Blueprint type |
| `kind` | enum | Must be `domain` | Domain controllers are always kind `domain` |
| `name` | string | `[a-z][a-z0-9-]*`, max 64, matches filename | Unique identifier |
| `version` | semver | `MAJOR.MINOR.PATCH` | Blueprint version |
| `port` | integer | 9700–9999, unique across all agents/domains | Default port |
| `requires` | list | References existing blueprints | Build-time dependencies |
| `extends` | list | Must include `patterns/domain-controller` | Inherited patterns |
| `depends_on` | list | Agent names required at runtime | Runtime agent dependencies |
| `platform` | enum | `any`, `go`, `cloudflare`, `node`, `rust` | Target platform |
| `tier` | enum | `free` or `pro` | Availability tier |

### Special Constraints

- `extends` MUST include `patterns/domain-controller`
- `depends_on` MUST list at least one agent (domains dispatch work)
- `kind` is always `domain` for this type

---

## Required Section Order

Domain controllers follow the agent section order with additional
domain-specific sections inserted.

| # | Section | Heading | Required | Description |
|---|---------|---------|----------|-------------|
| 1 | Frontmatter | `<!-- blueprint -->` | **Yes** | YAML metadata |
| 2 | Title | `# Name` | **Yes** | Level-1 heading + summary |
| 3 | Overview | `## Overview` | **Yes** | Scope description |
| 4 | Dependencies | `## Dependencies` | **Yes** | Full YAML dependency contracts |
| 5 | Domain Manifest | `## Domain Manifest` | **Yes** | JSON manifest with capabilities, inputs, outputs, required agents |
| 6 | Required Agents | `## Required Agents` | **Yes** | Table of agents this domain dispatches to |
| 7 | Workflows | `## Workflows` | **Yes** | Workflow definitions with phases |
| 8 | Configuration | `## Configuration` | **Yes** | Runtime parameters in YAML |
| 9 | Types | `## Types` | **Yes** | Data structures in YAML |
| 10 | Storage | `## Storage` | **Yes** | Domain controllers always persist data |
| 11 | State Machine | `## State Machine` | **Yes** | Domain and workflow state transitions |
| 12 | Lifecycle | `## Lifecycle` | **Yes** | Startup, shutdown, health, self-update |
| 13 | Triggers | `## Triggers` | **Yes** | Events, schedules, messages |
| 14 | Actions | `## Actions` | **Yes** | Message handlers |
| 15 | Aggregation | `## Aggregation` | **Yes** | How results from agents are combined |
| 16 | Scoring | `## Scoring` | Conditional | Required if domain produces scored reports |
| 17 | Feedback Loop | `## Feedback Loop` | **Yes** | Continuous improvement cycle |
| 18 | Collaboration | `## Collaboration` | **Yes** | Events, messages, agent coordination |
| 19 | Manual Overrides | `## Manual Overrides` | **Yes** | Override policy, audit |
| 20 | Constraints | `## Constraints` | **Yes** | Boundaries, forbidden actions, limits |
| 21 | Error Handling | `## Error Handling` | **Yes** | Permanent and transient errors |
| 22 | Observability | `## Observability` | **Yes** | Logs, metrics, alerts |
| 23 | Security | `## Security` | **Yes** | Permissions, data sensitivity, access control |
| 24 | Test Fixtures | `## Test Fixtures` | **Yes** | Happy path, errors, edge cases |
| 25 | Scaling | `## Scaling` | **Yes** | Horizontal model, coordination |
| 26 | Implementation Notes | `## Implementation Notes` | **Yes** | Practical guidance |
| 27 | Verification Checklist | `## Verification Checklist` | **Yes** | Testable assertions (min 10) |

---

## Domain-Specific Section Specifications

Sections shared with the agent schema (Dependencies, Configuration,
Types, Storage, State Machine, Lifecycle, Triggers, Actions,
Collaboration, Manual Overrides, Constraints, Error Handling,
Observability, Security, Test Fixtures, Scaling, Implementation Notes,
Verification Checklist) follow the same specifications as
[agent.md](agent.md). The sections below are domain-specific.

### Domain Manifest (`## Domain Manifest`)

A JSON block declaring the domain's identity, capabilities, inputs,
outputs, required agents, and workflows.

```json
{
  "name": "<domain-name>",
  "type": "domain",
  "version": "<semver>",
  "description": "<one-line description>",
  "url": "http://localhost:<port>",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "<capability>", "resources": []}
  ],
  "inputs": [
    {"name": "<input>", "type": "<type>", "description": "<what>"}
  ],
  "outputs": [
    {"name": "<output>", "type": "<type>", "description": "<what>"}
  ],
  "collaborators": [],
  "approval": "required|auto",
  "required_agents": ["<agent-name>"],
  "workflows": ["<workflow-name>"]
}
```

#### Validation Rules

1. `name` must match frontmatter `name`
2. `type` must be `"domain"`
3. `required_agents` must match frontmatter `depends_on`
4. `workflows` must match workflow names in the Workflows section
5. `capabilities` must match Security section permissions

### Required Agents (`## Required Agents`)

Table listing every agent the domain dispatches work to:

```markdown
| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| [agent-name](../agents/agent.md) | What this agent does | Which workflow phases use it |
```

#### Validation Rules

1. Every agent must be listed in frontmatter `depends_on`
2. Every agent must have a corresponding blueprint in the repository
3. "Dispatched For" must reference phases from the Workflows section

### Workflows (`## Workflows`)

Each workflow the domain controller executes:

```yaml
workflow: <workflow-name>
description: <what-this-workflow-does>
trigger: <action-or-event-that-starts-it>

phases:
  - name: <phase-name>
    agent: <agent-name>
    action: <action-to-invoke>
    input:
      <field>: <source — $task.payload, $prev_phase.output, literal>
    output: <variable-name>
    on_error: <fail|skip|retry>
    timeout: <seconds>

  - name: <next-phase>
    agent: <agent-name>
    action: <action>
    input:
      <field>: $<prev-phase>.output.<field>
    output: <variable-name>

aggregation:
  strategy: <merge|score|select>
  output: <final-output-type>
```

#### Phase Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Phase identifier (unique within workflow) |
| `agent` | string | yes | Agent to dispatch to (must be in Required Agents) |
| `action` | string | yes | Action to invoke on the agent |
| `input` | object | yes | Input fields — may reference `$task.payload`, `$<phase>.output`, or literals |
| `output` | string | yes | Variable name for phase results |
| `on_error` | enum | yes | `fail` (abort workflow), `skip` (continue), `retry` (with backoff) |
| `timeout` | integer | no | Phase timeout in seconds (default: agent's default timeout) |

#### Reference Expressions

Inputs may use reference expressions to pass data between phases:

| Expression | Resolves To |
|-----------|-------------|
| `$task.payload.<field>` | Field from the original task request |
| `$<phase>.output.<field>` | Field from a completed phase's output |
| `$config.<param>` | Config parameter value |
| Literal value | Used as-is |

#### Validation Rules

1. Every workflow must have `workflow`, `description`, `trigger`, and `phases`
2. Every phase must reference an agent from Required Agents
3. Phase `action` must be a valid action on the target agent
4. Phase inputs referencing other phases must reference earlier phases (no forward references)
5. `aggregation` must be declared
6. `on_error` must be one of: `fail`, `skip`, `retry`

### Aggregation (`## Aggregation`)

How results from multiple agents and phases are combined:

```yaml
aggregation:
  strategy: <merge|score|weighted|select>
  description: <how-results-are-combined>
  inputs:
    - source: $<phase>.output
      weight: <0.0-1.0>  # for weighted strategy
      fields: [<fields-to-include>]
  output:
    type: <TypeName>
    fields:
      - field: <description-of-aggregated-field>
  conflict_resolution: <last-wins|highest-score|manual>
```

### Scoring (`## Scoring`)

If the domain produces scored reports (e.g., SEO score, performance score):

```yaml
scoring:
  scale: <0-100|0-1|letter-grade>
  components:
    - name: <component>
      weight: <0.0-1.0>
      source: $<phase>.output.<field>
      scoring_rule: <how-the-raw-value-maps-to-a-score>
  formula: <how-component-scores-combine>
  thresholds:
    - label: <excellent|good|needs-work|critical>
      range: <min-max>
```

### Feedback Loop (`## Feedback Loop`)

How the domain learns from results and improves over time:

```yaml
feedback:
  triggers:
    - event: <when-feedback-is-collected>
      source: <where-it-comes-from>
  storage:
    - metric: <what-is-tracked>
      retention: <how-long>
  adaptation:
    - when: <condition>
      action: <what-changes>
      description: <why>
```

---

## Complete Template

````markdown
<!-- blueprint
type: domain
kind: domain
name: <domain-name>
version: 1.0.0
port: <9700-9999>
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/data-contract, patterns/governance, patterns/security]
depends_on: [<agent-name>, <agent-name>]
platform: any
tier: free
-->

# <Domain Name> Domain Controller

<One-sentence summary.>

## Overview

<2–5 sentences. Must explain: what business function, which agents
it dispatches to, what it produces.>

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
      types:
        - name: AgentManifest
          fields_used: [name, version, port, capabilities, public_key, url]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  # Additional requires...

extends:
  - pattern: patterns/domain-controller
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: workflow-execution
          parameters: [phases, dispatch, aggregation]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  # Additional extends...

depends_on: [<agent-name>]
```

---

## Domain Manifest

```json
{
  "name": "<domain>",
  "type": "domain",
  "version": "1.0.0",
  "description": "<description>",
  "url": "http://localhost:<port>",
  "public_key": "<hex>",
  "capabilities": [],
  "inputs": [],
  "outputs": [],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["<agent>"],
  "workflows": ["<workflow>"]
}
```

---

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| [<agent>](../agents/<agent>.md) | <purpose> | <phases> |

---

## Workflows

### <workflow-name>

```yaml
workflow: <name>
description: <description>
trigger: action = "<action>"

phases:
  - name: <phase>
    agent: <agent>
    action: <action>
    input:
      <field>: $task.payload.<field>
    output: <output-var>
    on_error: fail

aggregation:
  strategy: merge
  output: <TypeName>
```

---

## Configuration

```yaml
config:
  # <parameters>
```

---

## Types

```yaml
types:
  # <type-definitions>
```

---

## Storage

```yaml
storage:
  engine: sqlite
  tables:
    # <tables>
  relationships:
    # <relationships>
  retention:
    # <policies>
  backup:
    # <config>
```

---

## State Machine

```yaml
state_machine:
  agent:
    initial: created
    transitions:
      # <agent-state-transitions>

  workflow.<workflow-name>:
    initial: pending
    transitions:
      - from: pending
        to: running
        trigger: dispatch_started
      - from: running
        to: completed
        trigger: all_phases_succeeded
      - from: running
        to: failed
        trigger: phase_failed_and_on_error_is_fail
```

---

## Lifecycle

### Startup Sequence
```
<numbered-steps per agent schema>
```

### Shutdown Sequence
```
<numbered-steps per agent schema>
```

### Health
```yaml
health:
  # <per agent schema>
```

---

## Triggers

```yaml
triggers:
  # <triggers per agent schema>
```

---

## Actions

### <action>
<per agent schema action specification>

---

## Aggregation

```yaml
aggregation:
  strategy: <strategy>
  description: <how-results-combine>
```

---

## Feedback Loop

```yaml
feedback:
  triggers:
    - event: <trigger>
  adaptation:
    - when: <condition>
      action: <response>
```

---

## Collaboration

```yaml
events_published:
  # <events>
events_subscribed:
  # <events>
direct_messages:
  # <messages>
```

---

## Manual Overrides

```yaml
override_policy: supervised
# <per agent schema>
```

---

## Constraints

```yaml
constraints:
  # <per agent schema>
```

---

## Error Handling

```yaml
errors:
  # <per agent schema>
```

---

## Observability

```yaml
# <per agent schema>
```

---

## Security

```yaml
security:
  # <per agent schema>
```

---

## Test Fixtures

### Happy Path
```yaml
tests:
  # <tests>
```

### Error Cases
```yaml
  # <tests>
```

### Edge Cases
```yaml
  # <tests>
```

---

## Scaling

```yaml
scaling:
  # <per agent schema>
```

---

## Implementation Notes

- <Key design decisions>

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
