---
family: test-blueprint@1
version: 1.0.0
---
# Errors as a table

A table read by column name: its columns are in another order than the
catalogue lists them, and one is a column the catalogue does not name.

## Requirements

```yaml
requirements:
  - id: errors-are-coded
    level: must
    text: Every refusal carries a declared error code.
```

## Errors

| Description | Code | Category | HTTP | Owner |
|---|---|---|---|---|
| The lease has expired | `LEASE_EXPIRED` | permanent | 410 | lifecycle |
| The holder is busy; try again | `HOLDER_BUSY` | transient | 503 | lifecycle |

## Verification

```yaml
verifies:
  - id: refusal-codes-declared
    covers: [errors-are-coded]
    assertion: Each refusal's code is one the errors block declares.
```
