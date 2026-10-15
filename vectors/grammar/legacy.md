---
family: test-blueprint@1
version: 1.0.0
id: legacy-sample
---
# Legacy keys and spellings

A file written before grammar 1: a self-id in its header, an old type
spelling, an unknown one, and a section no slot declares.

## Requirements

```yaml
requirements:
  - id: count-in-sixty-four-bits
    level: must
    text: A counter holds any value a signed 64-bit integer can.
```

## Types

```yaml
types:
  Counter:
    fields:
      value: {type: int64, required: true}
      wide:  {type: int128}
```

## Background

Older files carried their own id; a file's id is now its path.

## Verification

```yaml
verifies:
  - id: counter-range
    covers: [count-in-sixty-four-bits]
    assertion: A counter stores and returns the largest signed 64-bit value.
```
