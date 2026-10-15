---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
review: 2026-10-15
requires:
  - {ref: protocol/types, version: ">=1.0.0 <2.0.0", bindings: [{type: RegisterRequest}]}
---
# Minimal, with CRLF line ends

The least a test blueprint holds: a header, a title, its requirements and the
checks that prove them.

## Requirements

```yaml
requirements:
  - id: answer-every-ping
    level: must
    text: A ping is answered with the time it was received.
    refs: [Pong]
```

## Verification

```yaml
verifies:
  - id: ping-is-answered
    covers: [answer-every-ping]
    check: endpoint-answers
    assertion: A ping receives a pong carrying the receive time.
```
