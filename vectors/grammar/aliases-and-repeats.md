---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# Aliases and repeats

A slot found by its alias, and a repeatable slot keyed by its markers.

## Requirements

```yaml
requirements:
  - id: lease-is-renewed
    level: must
    text: A lease is renewed before it expires.
    refs: [Lease]
  - id: drain-before-stop
    level: should
    text: A component drains its work before it stops.
```

## Data Types

```yaml
types:
  Lease:
    description: A time-bounded grant.
    fields:
      holder:  {type: string, required: true}
      expires: {type: timestamp, required: true}
      renewed: {type: "list<timestamp>"}
```

## Verification

```yaml
verifies:
  - id: lease-renewal-observed
    covers: [lease-is-renewed]
    assertion: A lease is renewed at least once before it expires.
```

## Operation: renew

<!-- wl:explains lease-is-renewed -->
Renewal comes before expiry because an expired lease is a second registration.

## Operation: drain

<!-- wl:explains drain-before-stop -->
Draining first means no accepted work is lost when the process exits.

## Operation: stop

Stopping has no marker, so this occurrence has no key.
