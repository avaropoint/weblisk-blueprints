---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# Multi-root fence

A fence that holds two root keys is not a block of either.

## Requirements

```yaml
requirements:
  - id: one-root-per-fence
    level: must
    text: A fence holds one root key.
notes:
  - Two root keys make this fence no block at all.
```

## Verification

```yaml
verifies:
  - id: second-root-refused
    covers: [one-root-per-fence]
    assertion: The fence above is refused as multi-root.
```
