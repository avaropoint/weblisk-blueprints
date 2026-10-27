<!-- blueprint
type: protocol
name: conventions
version: 1.0.0
requires: []
platform: any
tier: free
-->
<!-- wl:ids complete -->

# Wire Conventions

The one home of the rules every Weblisk value on the wire follows, whatever
component, language or platform carries it: how an instant, an id, a length of
time and an integer are written, how many times a failed call is tried and how
long to wait between tries, how a path names its parameters, and how long a
task may run. Each rule has an id, `protocol/conventions:<id>`, and every other
file cites the rule by that id and does not restate it. The worked values are
[`vectors/conventions.json`](../vectors/conventions.json), which every language
and platform mapping must reproduce.

## Overview

A rule stated twice is a rule two implementations can read two ways, and a
difference on the wire is found only when two of them meet. So each rule below
is stated once. Where an external authority defines the form — RFC 3339 for an
instant, RFC 9562 for a UUID — the rule names it and adds only the choices that
authority leaves open.

## Dependencies

```yaml
requires: []
  # protocol/conventions depends on nothing. protocol/spec requires it, so
  # every build carries it.
```

## Conventions

### Instant

<!-- wl:id instant -->
A field of type `timestamp` is an instant, carried as a JSON string in RFC 3339
`date-time` form, in UTC, written `Z`, with exactly three fractional digits:
`2026-01-02T03:04:05.123Z`. A sender MUST write that form and no other: no
offset other than `Z`, no lower-case `t` or `z`, no more or fewer fractional
digits. A receiver MUST refuse any other form rather than read it, so two
implementations never hold different bytes for one instant, and a digest or
signature over a body names one value. Ordering two instants in this form is
ordering the strings.

A calendar date that is not an instant is a `date`
([`schemas/blocks`](../schemas/blocks.md#types)), never a `timestamp`. Every
field that holds an instant is typed `timestamp`, whatever spelling it was
declared with before (`int64`, `datetime`, a `string` of RFC 3339). A field
whose form an external authority fixes keeps that form and cites it: a token's
`iat` and `exp` are RFC 7519 NumericDate. A fixed-form statement carries an
instant as its registered layout gives it
([`protocol/identity`](identity.md#fixed-form-statements)); each layout
registered since this rule writes it in this form.

### UUID

<!-- wl:id uuid -->
A field of type `uuid` holds a version 7 UUID (RFC 9562, section 5.7), written
in lower-case hexadecimal as 8-4-4-4-12 digits with hyphens. A component that
mints one MUST mint version 7, from a millisecond clock and random bits. A
receiver refuses any other spelling. It never reads a time out of a UUID it did
not mint: the embedded time is for ordering, not a statement of when.

### Duration

<!-- wl:id duration -->
A length of time — a field of type `duration`, or a configuration key that
holds one — is a string of one or more `<digits><unit>` parts with units `h`,
`m`, `s` and `ms`, each at most once and in that order: `30s`, `5m`, `1h30m`,
`250ms`, `0s`. No sign, no fraction, no other unit. A bare number is not a
duration. A key that holds one is a retired form, and the files that still
carry it are listed, each with what its keys mean until it is rewritten, in
[`RETIRED.md`](../RETIRED.md); no other file may hold one.

### Integer

<!-- wl:id integer -->
A field of type `integer` is a signed 64-bit integer, carried as a JSON number
with no fraction or exponent. A receiver whose JSON numbers are binary64 MUST
read an integer exactly or refuse it; it never rounds one outside
±(2^53 − 1). An integer in a body that is signed or digested is within
±(2^53 − 1), because RFC 8785 writes every number as a binary64
([`protocol/identity`](identity.md#sign-json)).

### Attempts

<!-- wl:id max-attempts -->
A limit on retrying is stated as `max_attempts`: the **total** number of
attempts, the first included. `max_attempts: 3` is one attempt and up to two
retries. The default is 3; `1` means no retry, and `0` is refused. A count of
attempts already made is `attempts`. Nothing states a limit as a number of
retries.

### Backoff

<!-- wl:id backoff -->
After attempt *n* fails (*n* = 1 for the first), a caller that will try again
waits a delay drawn uniformly from `[0, min(base × 2^(n−1), max)]` ("full
jitter"), with `base` 1s and `max` 30s by default. A `Retry-After` the server
sends is a floor on that delay. A channel or component that needs another pace
sets its own `base` and `max`, as durations, and cites this rule; it never
states a second formula or a schedule of its own.

### Path parameters

<!-- wl:id path-param -->
A route template names a parameter as `{name}`, in lower snake case:
`/v1/agents/{agent_id}`. The `:name` form is not used.

### Task timeout

<!-- wl:id task-timeout -->
A task runs for at most 300s unless a shorter limit is set
([`protocol/spec`](spec.md#task-execution-timeouts), `task_timeout_seconds` and
the manifest's `timeout`). An agent that sets no limit of its own is held to
that one; no file states another default.

## Contracts

Each rule above is a behaviour a blueprint binds by its id, so a build is told
which conventions it follows and a change to one is a change to what binds it.

```yaml
contracts:
  behaviors:
    - name: instant
      description: Write and read every timestamp as RFC 3339 UTC with milliseconds (Instant)
    - name: uuid
      description: Mint version 7 UUIDs, written lower case (UUID)
    - name: duration
      description: Write every length of time as a duration string (Duration)
    - name: integer
      description: Carry every integer as signed 64-bit, never rounded (Integer)
    - name: max-attempts
      description: State a retry limit as total attempts, default 3 (Attempts)
    - name: backoff
      description: Wait a full-jitter delay capped at min(base × 2^(n−1), max) before each retry (Backoff)
    - name: path-param
      description: Name route parameters as {name} (Path parameters)
    - name: task-timeout
      description: End a task at 300s unless a shorter limit is set (Task timeout)
```

## Error Handling

```yaml
error_codes: []
  # These rules add no error code. A value that breaks one is refused with the
  # code the receiving endpoint already uses for a malformed request
  # (protocol/types, Errors).
```

## Security

```yaml
security:
  canonical_forms:
    - requirement: One instant, id, duration and integer has exactly one
        spelling on the wire, so a digest or a signature over a body that
        carries one names one value (protocol/identity, Sign JSON)
  retries:
    - requirement: Full jitter and a cap keep the clients of a recovering
        service from retrying in step
```

## Implementation Notes

- A language or platform mapping states how it writes and reads each type here
  in its type table, and is checked against `vectors/conventions.json`
  ([`checks/timestamp-wire.py`](../checks/timestamp-wire.py)).
- An instant from a clock with finer resolution is truncated to the
  millisecond, never rounded, so an instant is never written later than it was
  read.

## Verification Checklist

- [ ] Every `timestamp` written matches `YYYY-MM-DDTHH:MM:SS.sssZ`, and a value in any other form is refused <!-- wl:check instant-form covers instant -->
- [ ] Every minted `uuid` is version 7 and lower case, and the UUID vectors read as `vectors/conventions.json` says <!-- wl:check uuid-v7 covers uuid -->
- [ ] Every `duration` parses by this grammar to the vectors' milliseconds, and each invalid vector is refused <!-- wl:check duration-grammar covers duration -->
- [ ] An `integer` outside the signed 64-bit range is refused, and none is rounded <!-- wl:check integer-range covers integer -->
- [ ] `max_attempts: 3` makes at most three attempts, the first included <!-- wl:check attempts-total covers max-attempts -->
- [ ] Each retry's delay is within `[0, min(base × 2^(n−1), max)]` for the vectors' `n` <!-- wl:check backoff-bounds covers backoff -->
- [ ] Every route template names its parameters as `{name}` <!-- wl:check path-param-form covers path-param -->
- [ ] A task with no shorter limit is ended at 300s <!-- wl:check task-timeout-default covers task-timeout -->
