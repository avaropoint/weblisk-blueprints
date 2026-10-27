---
family: schemas/domain@2
version: 1.0.0
requires:
  - {ref: protocol/types, version: ">=4.0.0 <5.0.0"}
port: 9800
depends_on: [agents/example]
extends: [patterns/domain-controller]
tier: free
retired: []
---
# Domain name

One sentence: the business function this domain controller owns.

## Overview

Two to five sentences on what it covers and where its scope ends. Every slot
this template leaves out is declared in
[`schemas/domain`](../schemas/domain.md#sections); add one only when there is
something to say in it.

## Requirements

```yaml
requirements:
  - id: example-rule-holds
    level: must
    text: An example rule every implementation keeps, stated so that a check can prove it.
```

## Required Agents

The agents this domain dispatches work to, and what it asks of each.

## Workflows

Each workflow, its phases, and which agent each phase dispatches to.

## Types

```yaml
types:
  ExampleRecord:
    description: A record the domain declares.
    fields:
      subject: {type: string, description: What the record is about.}
```

## Aggregation

How the agents' results are combined into the domain's answer.

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
