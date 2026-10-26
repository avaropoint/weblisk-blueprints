---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# Errors as yaml

The same errors as the table vector, written as a yaml block. Each entry's
digest is the table's, because a digest is over the value.

## Requirements

```yaml
requirements:
  - id: errors-are-coded
    level: must
    text: Every refusal carries a declared error code.
```

## Errors

```yaml
errors:
  - {code: LEASE_EXPIRED, http: 410, category: permanent, description: The lease has expired}
  - code: HOLDER_BUSY
    http: 503
    category: transient
    description: The holder is busy; try again
```

## Verification

```yaml
verifies:
  - id: refusal-codes-declared
    covers: [errors-are-coded]
    assertion: Each refusal's code is one the errors block declares.
```
