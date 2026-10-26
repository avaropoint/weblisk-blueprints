---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
owner: platform-team
---
# Header schema

A header key the family does not declare is refused, once, at the header.

## Requirements

```yaml
requirements:
  - id: header-keys-are-declared
    level: must
    text: A header holds only the keys its family declares.
```

## Verification

```yaml
verifies:
  - id: unknown-key-refused
    covers: [header-keys-are-declared]
    assertion: The owner key above is refused by the header schema.
```
