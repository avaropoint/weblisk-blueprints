---
family: schemas/pattern@2
version: 1.0.0
requires:
  - {ref: protocol/types, version: ">=4.0.0 <5.0.0"}
tier: free
retired: []
---
# Pattern name

One sentence: the concern this pattern settles once for everything that
extends it.

## Overview

Two to five sentences on what it covers and where its scope ends. Every slot
this template leaves out is declared in
[`schemas/pattern`](../schemas/pattern.md#sections); add one only when there is
something to say in it.

## Requirements

```yaml
requirements:
  - id: example-rule-holds
    level: must
    text: An example rule every implementation keeps, stated so that a check can prove it.
```

## Design Principles

1. Each decision the pattern makes, and the reason it is made once here.

## Types

```yaml
types:
  ExampleRecord:
    description: A record the pattern declares.
    fields:
      subject: {type: string, description: What the record is about.}
```

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
