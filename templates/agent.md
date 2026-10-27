---
family: schemas/agent@2
version: 1.0.0
requires:
  - {ref: protocol/types, version: ">=4.0.0 <5.0.0"}
kind: infrastructure
port: 9700
runs_with: [architecture/orchestrator]
tier: free
retired: []
---
# Agent name

One sentence: what this agent does, and the one thing it is for.

## Overview

Two to five sentences on what it covers and where its scope ends. Every slot
this template leaves out is declared in
[`schemas/agent`](../schemas/agent.md#sections); add one only when there is
something to say in it.

## Requirements

```yaml
requirements:
  - id: example-rule-holds
    level: must
    text: An example rule every implementation keeps, stated so that a check can prove it.
```

## Configuration

```yaml
config:
  example_interval: {type: duration, required: false, default: "60s", description: How often the agent does its work.}
```

## Types

```yaml
types:
  ExampleRecord:
    description: A record the agent declares.
    fields:
      subject: {type: string, description: What the record is about.}
```

## Triggers

The events, schedules and messages that start the agent's work.

## Actions

Each message the agent handles: what it takes, what it does, what it answers.

## Verification

```yaml
verifies:
  - id: example-rule-is-kept
    covers: [example-rule-holds]
    check: endpoint-answers
    assertion: What an implementation is observed to do that shows the rule held.
```

## Operation: example

<!-- wl:explains example-rule-holds -->
Why the requirement it explains holds: the reason a reader needs to keep the
rule when the circumstances change. It states no rule of its own.

## Implementation Notes

- Practical guidance for whoever builds to it.
