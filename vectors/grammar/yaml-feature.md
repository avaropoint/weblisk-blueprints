---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# YAML features

A block that uses an anchor and an alias is refused, once, and its value is
not read.

## Requirements

```yaml
requirements:
  - id: renew-before-expiry
    level: must
    text: &renew A lease is renewed before it expires.
  - id: renew-is-logged
    level: should
    text: *renew
```

## Verification

```yaml
verifies:
  - id: anchor-refused
    covers: [renew-before-expiry]
    assertion: The requirements block above is refused for its anchor.
```
