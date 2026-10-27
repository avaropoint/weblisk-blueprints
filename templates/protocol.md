---
family: schemas/protocol@2
version: 1.0.0
requires:
  - {ref: protocol/types, version: ">=4.0.0 <5.0.0"}
tier: free
retired: []
---
# Protocol name

One sentence: what this protocol carries, and between whom.

## Overview

Two to five sentences on what it covers and where its scope ends. Every slot
this template leaves out is declared in
[`schemas/protocol`](../schemas/protocol.md#sections); add one only when there is
something to say in it.

## Requirements

```yaml
requirements:
  - id: example-rule-holds
    level: must
    text: An example rule every implementation keeps, stated so that a check can prove it.
```

## Conventions

The wire conventions this protocol relies on, each cited from where it is
stated rather than restated.

## Types

```yaml
types:
  ExampleRecord:
    description: A record the protocol declares.
    fields:
      subject: {type: string, description: What the record is about.}
```

## Error Handling

```yaml
errors:
  - {code: EXAMPLE_REFUSED, http: 422, category: permanent, description: The request names no subject.}
```

## Security

What is signed, what is verified, and what a receiver trusts and why.

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
