---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# Slot order

Verification written ahead of the requirements it covers: each slot is read,
and the order is reported, never refused.

## Verification

```yaml
verifies:
  - id: order-is-reported
    covers: [slots-keep-their-order]
    assertion: The verification slot above is reported as out of order.
```

## Requirements

```yaml
requirements:
  - id: slots-keep-their-order
    level: should
    text: Slots are written in the order their family declares them.
```
