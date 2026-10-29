<!-- blueprint
type: architecture
name: notification
version: 1.2.0
requires: [protocol/types, protocol/identity, patterns/notification, patterns/retry, patterns/privacy, patterns/scope, architecture/content, architecture/orchestrator, architecture/admin, agents/email-send]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Notification

The tenant service that tells people. It is given positions and a message,
finds who holds each position in the tenant's own register, and tells each
holder in the way that person chose. It reports to its caller whom it
reached, and never reports a message that reached nobody as delivered.

## Overview

A programme's notice names **positions**, never a person and never a
channel ([`schemas/programme.md`](../schemas/programme.md#notices--who-is-told-what)).
Who holds a position is a fact about the customer's organisation, kept in
the [position-holders register](../schemas/position.md#who-holds-a-position)
in the organisation's records repository. How a person is told is that
person's own preference. This service joins the three: a **notify by
position** from the owner of the work, the holders the register names, and
each holder's preference.

[`patterns/notification`](../patterns/notification.md) describes channels,
preferences, delivery tracking and retries for any sender. This document is
the tenant service that applies that pattern to people named by position. It
is the home of four things: the notify-by-position route and its authority,
the routes on which a person reads and sets their own preferences and reads
what they were told, what this service keeps about a person and for how
long, and the rule that a notice reaching nobody is reported as such.

> **Scope boundary.** This document specifies the service. Positions, and
> the register of who holds them, are
> [`schemas/position.md`](../schemas/position.md)'s. When a notice advances,
> and whether it is muted, is
> [`architecture/programme-service`](programme-service.md#telling)'s. The
> email adapter is [`agents/email-send`](../agents/email-send.md). No
> component implements this document yet ([Known Gaps](#known-gaps)).

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    # 6.2.0 is where AuditEntry carries the authorisation and the run
    version: ">=6.2.0 <7.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, error, category, retryable]
        # actor is the owner of the work, via the component that carried it,
        # authorisation and run the work authorisation and run it came under
        - name: AuditEntry
          fields_used: [id, timestamp, actor, via, authorisation, run, action, target, status]
        # pass_routes is how the admin gateway learns which routes a person's
        # request may reach here, and what each needs. See Who May Do What
        - name: AgentManifest
          fields_used: [name, capabilities, pass_routes, publishes]
        - name: PassRoute
          fields_used: [method, path, capabilities]
        - name: Capability
          fields_used: [name, resources]
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
        # The one notice a notify names and the actors it may be carried by
        - name: WorkAuthorisation
          fields_used: [id, owner, definition, actors, capabilities, status, not_after]
        - name: WorkExchangeRequest
          fields_used: [authorisation, audience, scope, run]
        - name: WorkExchangeResponse
          fields_used: [issued, code, pass, expires_at, capabilities]
        - name: EventEnvelope
          fields_used: [topic, source, scope, correlation_id, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/identity
    # 3.1.0 is where the work pass, and its definition and run claims, exist
    version: ">=3.1.0 <4.0.0"
    bindings:
      types:
        # On a pass: a person, by identity_id, carried by the gateway in act.
        # On a work pass: the owner by identity_id, the actor in act, the
        # authorisation in cid, and its definition and run
        - name: WLToken
          fields_used: [type, aud, act, cap, cid, identity_id, definition, run]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/notification
    version: ">=2.0.0 <3.0.0"
    bindings:
      behaviors:
        - name: notification-dispatch
          usage: Holders resolved from the position-holders register stand where the pattern resolves subscribers; each holder's own preference is the subscriber preference it enforces
        - name: channel-adapter
          usage: email through agents/email-send, in_app through this service's own store; no other adapter is specified
      types:
        - name: DeliveryReceipt
          fields_used: [notification_id, channel, subscriber_id, status, delivered_at, error, attempts]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/retry
    version: ">=2.0.0 <3.0.0"
    bindings:
      behaviors:
        - name: retry-with-backoff
          usage: Reading the register, and each call to a channel adapter, as Retrying says
        - name: circuit-breaker
          usage: One circuit per channel adapter and one for content
      types:
        - name: RetryConfig
          fields_used: [max_attempts, backoff, jitter]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/privacy
    version: ">=2.0.0 <3.0.0"
    bindings:
      behaviors:
        - name: data-minimization
          usage: A delivery keeps a holder's identity id and never an address; a message carries the notice's words and the fact's ids, never a register row
        - name: erasure-cascade
          usage: A person's preference and the messages held for them are erased on request; what is kept is reported as an exception
      types:
        - name: ErasureException
          fields_used: [agent, reason, detail, retry_eligible, reported_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/scope
    version: ">=3.0.0 <4.0.0"
    bindings:
      types:
        # An enum: it declares values, not fields, so nothing is bound FROM it.
        # What this service holds about a person is restricted
        - name: ScopeLevel
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/content
    version: ">=4.0.0 <6.0.0"
    bindings:
      types:
        # The organisation's records repository, found by records and scope_path
        - name: ContentRepository
          fields_used: [id, scope_path, records]
        # The register is read as an entry, never copied
        - name: ContentEntry
          fields_used: [path, identity, scope]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    # 4.2.0 is where the orchestrator holds work authorisations and mints
    # work passes (work-exchange)
    version: ">=4.2.0 <5.0.0"
    bindings:
      behaviors:
        - name: work-exchange
          usage: Called for every request this service makes of content under a notice's authorisation, one work pass per request
        - name: token-exchange
          usage: Relied on, never called. Every pass this service accepts was minted by the exchange for a person the orchestrator judged live then
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/admin
    version: ">=4.0.0 <6.0.0"
    bindings:
      behaviors:
        - name: admin-gateway-authorization
          usage: Relied on, never called. A person's request reaches this service only on a route its manifest declares among pass_routes, on a pass naming every capability that route declares
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: agents/email-send
    version: ">=3.0.0 <4.0.0"
    bindings:
      types:
        - name: EmailRequest
          fields_used: [to, subject, body, content_type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
 programme service ──NotifyByPosition──► notification ──work pass──► content
 (the notice's owner,  (registration      │      ▲      (content:describe,  (records repository:
  or an actor on a      token, or a       │      │       content:read)       registers/position-holders.md)
  work pass under       work pass)        │      └── WorkExchange ── orchestrator
  its authorisation)                      │
                                          ├──► in_app store ──► the person, on their own pass
                                          └──► agents/email-send ──► the person's own address

 person ──► admin gateway ──pass──► notification: their own preference, what they were told
```

- **Notification tells and never decides who.** The positions are the
  caller's, from the notice. The holders are the register's. Nothing in this
  service chooses a person.
- **Notification never decides how.** Each holder's channels, quiet hours and
  digest are their own preference. A caller cannot name a channel.
- **Notification reads holders only for a notice a person allowed.** Every
  read of the register is carried on a work pass minted under the notice's
  own work authorisation, which names this service as an actor
  ([`protocol/identity`](../protocol/identity.md#the-work-pass)). It reads
  holders on no other authority.
- **Notification keeps the least it can.** It keeps each delivery by the
  holder's identity id, the preference each person set, and the messages held
  for a person to read. It keeps no copy of the register.

## Responsibilities

### Owns

- Each **notification**: one notify-by-position it accepted, the positions it
  named, how many holders each had, and its outcome
- Each **delivery**: one holder told on one channel, with its status and
  attempts
- Each person's **preference**: the channels and addresses they chose, their
  quiet hours, their digest and their time zone
- The **in_app** messages held for each person until they are read and the
  retention period ends
- Resolving each named position to its holders on the day of the fact, as
  [`schemas/position.md`](../schemas/position.md#resolving-a-position-to-its-holders)
  states the rule
- Wording the message from the notice's `says` and the fact's ids

### Does NOT Own

- **Who holds a position.** That is the register's, in content, written by a
  person ([`schemas/position.md`](../schemas/position.md#who-holds-a-position))
- **When a notice advances, and whether it is muted.** The programme
  service decides both, and calls this service only for an unmuted advance
  ([`architecture/programme-service`](programme-service.md#telling))
- **Sending email.** [`agents/email-send`](../agents/email-send.md) queues,
  sends and retries against the provider
- **The work authorisation.** A person makes it at the orchestrator, and the
  orchestrator mints every work pass
- **Any decision.** A notification asks a person nothing it records as an
  answer. A decision is made in the admin gateway's inbox, at its owner

---

## Endpoints

| Method | Path | Operation | Auth | Capability | Purpose |
|--------|------|-----------|------|------------|---------|
| POST | /v1/notification/notifications | NotifyByPosition | yes | `notification:send` | Tell the holders of each named position, under the work authorisation the request names. Answers the notification with its outcome. Never on a pass |
| GET | /v1/notification/notifications | ListNotifications | yes | `notification:read` | Notifications in scope, newest first, cursor-paginated, each with its outcome |
| GET | /v1/notification/notifications/{id} | GetNotification | yes | `notification:read` | One notification, with each position's holder count and its outcome |
| GET | /v1/notification/deliveries | ListDeliveries | yes | `notification:read` | Deliveries, narrowed by `notification`, `holder`, `channel` or `status`, cursor-paginated. Never an address |
| GET | /v1/notification/deliveries/{id} | GetDelivery | yes | `notification:read` | One delivery, with its attempts and its last error |
| GET | /v1/notification/preference | GetPreference | yes | `notification:receive` | The caller's own preference, addresses included. A pass only |
| PUT | /v1/notification/preference | SetPreference | yes | `notification:receive` | Set the caller's own preference. A pass only |
| DELETE | /v1/notification/preference | ClearPreference | yes | `notification:receive` | Erase the caller's own preference and every address in it. A pass only |
| GET | /v1/notification/received | ListReceived | yes | `notification:receive` | What the caller was told, from the in_app store, newest first, cursor-paginated. A pass only |
| POST | /v1/notification/received/{id}/seen | MarkSeen | yes | `notification:receive` | Record that the caller has seen one message held for them. A pass only |
| POST | /v1/services | Services | yes | | Accept the signed service directory the orchestrator pushes, as [`protocol/spec`](../protocol/spec.md#post-v1services) specifies |
| GET | /livez | Livez | no | | Liveness, for the supervisor that restarts the service |
| GET | /readyz | Readyz | no | | Readiness, for the supervisor waiting on its start |

**Every route but `NotifyByPosition`, `Services`, `/livez` and `/readyz` is
declared among the manifest's `pass_routes`**, with the one capability its
row gives and no body requirement. The admin gateway carries a person's
request here only on a route that list declares
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`),
so the list and the table MUST agree. `NotifyByPosition` is not a pass route:
a person does not send a programme's notice, so no person's request may reach
it.

**`GetNotification` also answers its owner.** A registration token whose
`identity_id` is the notification's `owner`, carrying `notification:send`,
is answered that notification, so that the service that asked can read the
outcome of what it asked. It is answered no other notification, and a
notification it does not own is answered `NOT_FOUND`.

**Every route that names a scope takes it as a query parameter.**
`ListNotifications` and `ListDeliveries` require `organisation`, and take
`project` to narrow. A route missing a parameter it requires is refused with
`INVALID_REQUEST`. Naming an organisation grants nothing.

**The service declares** `notification:send` and `notification:read`, which
it serves, and `content:describe`, `content:read`, `work:exchange` and
`agent:message`, with which it calls. It checks `notification:receive` and
never holds it, as [`protocol/types`](../protocol/types.md#capability)
requires of a person-only capability. It claims the `notification.*`
namespace.

---

## Interfaces

### What it is asked

`NotifyByPosition` takes a `NotifyRequest` ([Types](#types)): the work
authorisation of the notice, the `run` the caller gives this advance, the
organisation and optional project, the notice it tells (programme and `id`),
the `to` positions, the `says` text, the notice's `why`, and the fact
(`NoticeFact`). It answers `200` with the `Notification`. The answer is final
about who was reached: holders are resolved, and every in_app message is
written, before it is sent. External deliveries continue after it, and each
is read at `GetDelivery` or `ListDeliveries`.

A request whose `run` this service has already accepted from the same owner
under the same authorisation is answered the notification it made then. It
makes no second notification, reads nothing and tells nobody again
([Deduplication](#deduplication)).

### What it calls

| to | route or action | on | for |
|---|---|---|---|
| the orchestrator | `GET /v1/work/authorisations` | its own registration token | finding the authorisation a request names, its owner, definition, actors and state |
| the orchestrator | `POST /v1/token/work` (`WorkExchange`) | its own registration token, `work:exchange` | one work pass for each request it makes of content |
| content | `GET /v1/content/repositories` | a work pass, `content:describe` | the organisation's records repository: the one reported with `records: true` for its `scope_path` |
| content | `GET /v1/content/entry` | a work pass, `content:read` | the position-holders register, `registers/position-holders.md`, in that repository |
| [`agents/email-send`](../agents/email-send.md) | [`send_raw`](../agents/email-send.md#send_raw) on `POST /v1/message` | its own registration token, `agent:message` | one email to one holder's own address |
| [`agents/email-send`](../agents/email-send.md) | [`status`](../agents/email-send.md#status) on `POST /v1/message` | its own registration token, `agent:message` | the outcome of an email it queued |

### Events it publishes

| topic | when | payload |
|---|---|---|
| `notification.sent` | a delivery is `delivered` | `notification`, `delivery`, `channel`, `holder`, `delivered_at` |
| `notification.failed` | a delivery is `failed` or `unknown` after its last attempt | `notification`, `delivery`, `channel`, `holder`, `status`, `attempts` |
| `notification.unreached` | a notification's outcome is `reached_nobody`, `not_authorised` or `holders_unreadable` | `notification`, `owner`, `notice`, `outcome`, `unheld` |

`holder` is an identity id. No event carries an address, a message's text or
a row of the register ([Personal Data](#personal-data)). The first two are
[`patterns/notification`](../patterns/notification.md#contracts)'s topics,
with this service's payload; `notification.unreached` is declared here.

---

## Error Handling

| Code | When |
|---|---|
| `PASS_REQUIRED` | An operator token was presented on any route ([`protocol/identity`](../protocol/identity.md#the-pass), rule 4) |
| `PASS_AUDIENCE_MISMATCH` | A pass or a work pass addressed to another component |
| `FORBIDDEN` | The token does not carry the route's capability; a pass on `NotifyByPosition`; a token other than a pass on a route reserved to a pass; or a `NotifyByPosition` whose authorisation names an owner other than the caller ([Who May Do What](#who-may-do-what)) |
| `INVALID_REQUEST` | A body that is not a `NotifyRequest` or a `PreferenceWrite`; no position named; a preference naming a channel this build does not deliver, or `in_app`; a route missing a parameter it requires; or a `run` already accepted with a different body |
| `NOT_FOUND` | No notification, delivery or held message with that id that the caller may read |
| `STORAGE_ERROR` | An in_app message or the notification could not be written. Nothing was recorded and nothing external was sent, so the same request may be sent again ([Retrying](#retrying)) |

**A notify that reaches nobody is not an error.** It answers `200` with an
outcome that says so ([Outcomes](#outcomes)). An authorisation that is
revoked, expired, unknown or does not name this service is answered the same
way, with the outcome `not_authorised` and the work pass code that refused it
in `code`, because each is a state of the work a person can act on, not a
fault in the request.

---

## Data Flow

### Notifying

1. The programme service decides a notice has advanced and is unmuted, or
   that an occurrence has advanced under an unmuted `due-sweep`
   ([`architecture/programme-service`](programme-service.md#telling)). It
   sends `NotifyByPosition` on its own registration token, naming the
   notice's work authorisation and the `run` it gives this advance. An
   occurrence has no notice of its own: it is told as `notice` the
   `due-sweep` operation that observed it, under that operation's
   authorisation, with the obligation's `activity` as `says` and its
   `responsible` or `escalate.to` position as `positions`, and nothing in the
   request's shape changes for it. Agent work is told the same way: an
   `agent:` item's work asks the programme service, which sends
   `NotifyByPosition` naming the item as `notice`, under the item's
   authorisation, with the work's words as `says` and the event
   `instruction` ([`architecture/programme-service`](programme-service.md#what-agent-work-may-start-and-tell)).
2. This service checks the token and the authorisation
   ([Who May Do What](#who-may-do-what), rule 3). It looks the authorisation
   up in `GET /v1/work/authorisations`. An authorisation it does not find
   there, or one revoked or past its `not_after`, gives the outcome
   `not_authorised`, and nothing is read or told.
3. It resolves the holders ([Resolving holders](#resolving-holders)).
4. It words the message once, from `says`, `why` and the fact's ids.
5. For each holder, once however many of the named positions they hold, it
   writes an in_app message, and records one delivery for it, `delivered`.
   For each other channel the holder's preference names for this fact, it
   records one delivery, `queued`, or `deferred` where quiet hours or a
   digest hold it.
6. It records the notification with its outcome, records an `AuditEntry`,
   and answers.
7. It sends each queued delivery through its channel's adapter
   ([Retrying](#retrying)), and each deferred one when its quiet hours end or
   its digest is due.

### Resolving holders

1. It finds the organisation's records repository with
   `GET /v1/content/repositories`, on a work pass minted under the request's
   authorisation, addressed to content, carrying `content:describe`.
2. It reads `registers/position-holders.md` there with
   `GET /v1/content/entry`, on a second work pass carrying `content:read`.
   Each work pass carries the request's `run`, so content records the read
   with the owner as `actor`, this service as `via`, and the authorisation
   and run ([`protocol/identity`](../protocol/identity.md#the-work-pass),
   rule 10).
3. It applies [`schemas/position.md`](../schemas/position.md#resolving-a-position-to-its-holders)'s
   rule to each named position, on the date of the fact's `occurred_at`, at
   the request's project or organisation.
4. It keeps each holder's identity id for the deliveries, and nothing else
   of the register. The bytes it read are dropped when the request is
   answered.

A scope with no records repository, or a records repository without the
register, has no holder for any position, and each position is `unheld`. A
read that content refuses, or that fails after its retries, gives the
outcome `holders_unreadable`: it is not known who holds the positions, which
is a different fact from nobody holding them.

### Setting a preference

1. A person sends `PUT /v1/notification/preference` through the admin
   gateway, on their own pass carrying `notification:receive`.
2. The service records the `PreferenceWrite` as the preference of the
   pass's `identity_id`, replacing the one it held. It is never written for
   any other person.
3. It records an `AuditEntry` with the person as `actor`, naming the
   channels set and never an address.

`DELETE` erases the preference. From then on that person is told in_app
only.

### Reading what one was told

A person reads `GET /v1/notification/received` on their own pass, and is
answered the in_app messages held for their `identity_id`, and no other
person's. `POST /v1/notification/received/{id}/seen` records when they saw
one. Seeing a message decides nothing.

---

## Outcomes

A notification's `outcome` is one of:

| outcome | means | delivered |
|---|---|---|
| `reached` | every named position has at least one holder, and every holder has a `delivered` delivery | yes |
| `partly_reached` | at least one holder of some position was reached, and some named position has no holder | for the positions held |
| `reached_nobody` | no named position has a holder on the fact's date | **no** |
| `not_authorised` | the work authorisation did not admit reading holders. `code` names why: a work pass code, or that the authorisation does not name this service | **no** |
| `holders_unreadable` | the register could not be read, so it is not known who holds the positions | **no** |

**`reached_nobody`, `not_authorised` and `holders_unreadable` are never
delivered.** Each is answered to the caller as that outcome, with `unheld`
naming each position that had no holder, and published as
`notification.unreached`. A caller records it as not delivered, and never as
sent ([`architecture/programme-service`](programme-service.md#telling)).

**A holder is reached when their in_app message is written.** Every holder
is told in_app, whatever else they chose, and in_app is never deferred: it
interrupts nobody, so no quiet hours hold it. That is why a held position
nearly always reaches someone: what a person set elsewhere can delay or fail
an email, and cannot make them unreachable. An email that fails is recorded
as its own failed delivery, and does not undo that the holder was reached.

**The outcome is final when it is answered.** An external delivery that is
still queued or deferred at the answer changes its own status later, and
never the notification's outcome.

---

## Deduplication

1. **One notification per run.** The key is the owner's identity id, the
   authorisation and the `run`. A second request with the same key and the
   same body is answered the first notification; with a different body it is
   refused with `INVALID_REQUEST`. The key is kept as long as the
   notification is ([Personal Data](#personal-data)).
2. **One holder, one message.** A holder named by two positions in one
   notification is told once on each channel, and the delivery names both
   positions.
3. **No window throttle.** [`patterns/notification`](../patterns/notification.md#throttling)'s
   throttle window is not applied to a notify by position. The programme
   service tells a notice once each time it advances, so two notifications
   about one notice are two facts, and suppressing the second would drop one.
   A person who wants fewer messages sets a digest.

## Retrying

Each call follows [`patterns/retry`](../patterns/retry.md#default-retry-configuration),
with the backoff [`protocol/conventions`](../protocol/conventions.md#backoff)
gives, and a circuit per target
([`patterns/retry`](../patterns/retry.md#circuit-breaker)):

| call | attempts, base and max | each attempt |
|---|---|---|
| reading the register at content | `patterns/retry`'s defaults | mints its own work pass. A work pass is never reused for a retry, because it is for one request (`protocol/identity`, The work pass, rule 13) |
| `send_raw` at email-send | the email row of [`patterns/notification`](../patterns/notification.md#retry-behavior) | is resent only when email-send refused it before accepting it: the connection refused, or a transient `ErrorResponse` |
| `status` at email-send | as `send_raw` | reads the queued email's outcome until it is `delivered` or failed |
| writing an in_app message | one, as the in_app row says | a write that fails fails the request with `STORAGE_ERROR`, before any notification is recorded or anything external is sent, so the caller may send it again with the same `run` |

**An email whose outcome is not known is not sent again.** A `send_raw` that
timed out after the request was sent may have been queued, and email-send
takes no idempotency key, so a resend could tell the person twice. The
delivery is recorded `unknown`, published as `notification.failed`, and never
reported as delivered ([Known Gaps](#known-gaps)).

A work pass refused with a work pass code is not retried. The authorisation
ended or was never granted, and the outcome is `not_authorised`.

---

## Who May Do What

This is the person, pass and work pass rule for notification. The token rules
themselves are [`protocol/identity`](../protocol/identity.md#the-pass)'s and
[`protocol/identity`](../protocol/identity.md#the-work-pass)'s, and are not
restated here.

1. **A person reaches this service only on a pass.** Every person's request
   arrives through the admin gateway, on a pass addressed here. An operator
   token is refused on every route with `PASS_REQUIRED`.
2. **A person's preference and messages are their own.** The preference and
   received routes act on the pass's `identity_id` alone. No route reads or
   sets another person's preference, an administrator's pass included, and a
   held message for another person is `NOT_FOUND`. `notification:receive` is
   person only, so no service or agent holds it.
3. **Only the notice's owner, or an actor it authorised, may ask.**
   `NotifyByPosition` needs `notification:send`, and is admitted on one of:
   - a registration token whose `identity_id` is the `owner` of the
     authorisation the request names; or
   - a work pass whose `cid` is that authorisation and whose `identity_id` is
     its owner, so that an actor such as execution, named in it, may ask on
     the owner's behalf.
   On any other token, a pass among them, it is refused with `FORBIDDEN`.
   Naming an authorisation the caller does not own is refused the same way.
4. **This service reads holders only under the notice's authorisation.**
   Every request it makes of content is carried on a work pass minted under
   the authorisation the request names, which must list this service among
   its actors. It never reads the register on its own registration token,
   and never under another notice's authorisation.
5. **This service decides nothing.** It does not choose a person, a channel
   or a time a person did not choose. It retries a delivery, never a fact,
   and never tells a notice that was not asked of it.

Each act records an `AuditEntry`. On a pass, the person is the `actor` and the
gateway `via`. On `NotifyByPosition`, the owner is the `actor`; on a work
pass, the actor that carried it is `via`, and `authorisation` and `run` are
the pass's. On a registration token, `authorisation` and `run` are the
request's.

---

## Personal Data

This service holds data about people, and follows
[`patterns/privacy`](../patterns/privacy.md#design-principles) and
[`architecture/data-security`](data-security.md) for it.

| what | about | scope | kept |
|---|---|---|---|
| a preference: identity id, channels and addresses, quiet hours, digest, time zone | one person, who set it | `restricted`, labelled `pii` | until that person clears it |
| a delivery: holder identity id, channel, positions, status, attempts, times | one holder | `restricted`, labelled `pii` | `retention` from its notification |
| an in_app message held for a person, and when they saw it | one holder | `restricted`, labelled `pii` | `retention` from its notification |
| a notification: owner, notice, positions, holder counts, message, outcome | no person | `internal` | `retention` |

- **Purpose.** A holder's identity id and a person's addresses are used to
  tell that person what their positions are told, and for nothing else
  (`patterns/privacy` Design Principle 2). None is sent to a model, exported
  or published.
- **Minimisation.** A delivery names its holder by identity id and never by
  address. An address is answered to the person who set it, at
  `GetPreference`, and to no one else, and it reaches no event, log line or
  `AuditEntry`. The message is worded from `says`, `why` and the fact's
  `event`, `obligation`, `subject` and `due_at`, which are ids and instants;
  any other field a fact carries is not put in the message. `says` from agent
  work is a model's words, which the prompt worker sends only where what the
  model was shown may leave the tenant
  ([`architecture/prompt-worker`](prompt-worker.md#scope)); this service words
  it as it words any `says`, and reads nothing in it as an instruction. No row of the
  register is kept (`patterns/privacy` Design Principle 3).
- **A person's own act.** A person's addresses are given by that person, on
  their own pass, for this purpose alone. Clearing the preference is
  withdrawing them.
- **Erasure.** On an erasure request for a person, this service erases their
  preference and every in_app message held for them, and reports the
  deliveries naming them in an `ErasureException`, reason
  `regulatory_retention`, its `detail` saying they are the record of the
  person being told and are removed `retention` after their
  notification
  ([`patterns/privacy`](../patterns/privacy.md#erasure-cascade)).
- **Where it is kept.** The store holding preferences, deliveries and held
  messages must hold `restricted` ([`patterns/scope`](../patterns/scope.md#placement-ceilings)).
- **Leaving the tenant.** An email carries the message and the person's own
  address to email-send and, through it, to the provider. The message holds
  no register row. The address is the destination the person chose.

---

## Types

```yaml
types:
  NotifyRequest:
    description: What the owner of a notice, or an actor it authorised, asks notification to tell
    fields:
      authorisation:
        type: string
        required: true
        description: The id of the notice's work authorisation, which names notification among its actors. For an occurrence, the due-sweep operation's; for agent work, the agent item's
      run:
        type: string
        required: true
        description: The id the owner gives this advance. Carried on every work pass for the request, and with owner and authorisation the key that makes a second request answer the first
      organisation:
        type: string
        required: true
        description: The scope path of the organisation whose holders are told
      project:
        type: string
        required: false
        description: The scope path of a project below it, where the fact is about one
      notice:
        type: NoticeRef
        required: true
      positions:
        type: "[]string"
        required: true
        description: The notice's to positions, or an occurrence's responsible and escalate.to positions, by the ids programmes name them with. At least one
      says:
        type: string
        required: true
        description: The notice's says, as the adopted map gives it, an occurrence's obligation's activity, or what an agent item's work asked to say
      why:
        type: string
        required: false
        description: The notice's why
      fact:
        type: NoticeFact
        required: true
  NoticeRef:
    description: The notice a notification tells, for an occurrence the due-sweep operation that observed it, or for agent work the agent item whose work asked
    fields:
      programme:
        type: string
        required: true
      id:
        type: string
        required: true
        description: The notice's id, local to its programme, the due-sweep operation's for an occurrence, or the agent item's for agent work
  NoticeFact:
    description: The fact a notice is about. Ids and instants only
    fields:
      event:
        type: string
        required: true
        description: The on event that became true, such as obligation.overdue, or instruction where an agent item's work asked
      occurred_at:
        type: timestamp
        required: true
        description: When it became true. Holders are resolved on its date
      obligation:
        type: string
        required: false
      subject:
        type: string
        required: false
        description: The key of the register row the obligation is for, never the row
      due_at:
        type: timestamp
        required: false
  Notification:
    description: One notify by position this service accepted, and its outcome
    fields:
      id:
        type: string
        required: true
        description: Minted here, 32 lowercase hex characters, never reused
      owner:
        type: string
        required: true
        description: The identity id of the authorisation's owner
      authorisation:
        type: string
        required: true
      run:
        type: string
        required: true
      organisation:
        type: string
        required: true
      project:
        type: string
        required: false
      notice:
        type: NoticeRef
        required: true
      fact_event:
        type: string
        required: true
      positions:
        type: "[]PositionOutcome"
        required: true
      unheld:
        type: "[]string"
        required: true
        description: Each named position with no holder on the fact's date. Empty when every one had one
      subject:
        type: string
        required: true
        description: The message's subject line, worded here
      body:
        type: string
        required: true
        description: The message, worded here from says, why and the fact's ids
      outcome:
        type: string
        enum: [reached, partly_reached, reached_nobody, not_authorised, holders_unreadable]
        required: true
      code:
        type: string
        required: false
        description: Where the outcome is not_authorised or holders_unreadable, the code that refused the authorisation or the read
      created_at:
        type: timestamp
        required: true
  PositionOutcome:
    description: One named position in a notification
    fields:
      position:
        type: string
        required: true
      holders:
        type: int
        required: true
        description: How many people held it on the fact's date
      reached:
        type: int
        required: true
        description: How many of them were reached
  Delivery:
    description: One holder told on one channel. Never an address
    fields:
      id:
        type: string
        required: true
        description: Minted here, 32 lowercase hex characters, never reused
      notification:
        type: string
        required: true
      holder:
        type: string
        required: true
        description: The holder's identity id
      positions:
        type: "[]string"
        required: true
        description: Every named position the holder held, so one person is told once
      channel:
        type: string
        enum: [in_app, email]
        required: true
      status:
        type: string
        enum: [queued, deferred, sent, delivered, failed, unknown]
        required: true
        description: sent means the adapter accepted it; unknown means a send whose outcome could not be learned, which is never resent
      attempts:
        type: int
        required: true
      created_at:
        type: timestamp
        required: true
      delivered_at:
        type: timestamp
        required: false
      seen_at:
        type: timestamp
        required: false
        description: For in_app, when the holder saw it
      error_code:
        type: string
        required: false
        description: The last error's code, such as HARD_BOUNCE from email-send
  Preference:
    description: How one person chose to be told. Held for them, answered only to them
    fields:
      id:
        type: string
        required: true
        description: Minted here, 32 lowercase hex characters, never reused. One per identity_id
      identity_id:
        type: string
        required: true
        description: The person's identity id at this tenant, from the pass that set it
      channels:
        type: "[]ChannelAddress"
        required: true
        description: Each channel beyond in_app, which is always on and is never listed
      quiet_hours:
        type: QuietHours
        required: false
      digest:
        type: Digest
        required: false
      time_zone:
        type: string
        required: true
        description: An IANA time zone name, read for quiet hours and the digest
      updated_at:
        type: timestamp
        required: true
  PreferenceWrite:
    description: What a person sends to set their own preference
    fields:
      channels:
        type: "[]ChannelAddress"
        required: true
      quiet_hours:
        type: QuietHours
        required: false
      digest:
        type: Digest
        required: false
      time_zone:
        type: string
        required: true
  ChannelAddress:
    description: One channel a person is told on, and where
    fields:
      channel:
        type: string
        enum: [email]
        required: true
        description: A channel this build delivers, other than in_app
      address:
        type: string
        required: true
        description: The person's own address on that channel
      events:
        type: "[]string"
        required: false
        description: The on events told on this channel. Absent, every event
  QuietHours:
    description: When nothing but in_app is sent
    fields:
      begins:
        type: string
        required: true
        description: A time of day, HH:MM, in the preference's time zone
      ends:
        type: string
        required: true
        description: A time of day, HH:MM, in the preference's time zone
  Digest:
    description: Hold every message for a channel and send them together
    fields:
      frequency:
        type: string
        enum: [daily, weekly]
        required: true
      send_time:
        type: string
        required: true
        description: A time of day, HH:MM, in the preference's time zone; a weekly digest is sent on Mondays
```

---

## Resources

What this service holds that a person may see, declared as
[`schemas/resource`](../schemas/resource.md) says. The
`position-holder` kind is not this service's: it is declared in
[`schemas/position.md`](../schemas/position.md#who-holds-a-position).

```yaml
resources:
  - kind: notification
    owner: notification
    type: Notification
    identity: {field: id, form: minted}
    label: subject
    fields:
      - {name: id, access: read-only, present: text}
      - {name: owner, access: read-only, present: text}
      - {name: run, access: read-only, present: text}
      - {name: organisation, access: read-only, present: text}
      - {name: project, access: read-only, present: text}
      - {name: fact_event, access: read-only, present: text}
      - {name: positions, access: read-only, present: list}
      - {name: unheld, access: read-only, present: list}
      - {name: subject, access: read-only, present: text}
      - {name: body, access: read-only, present: text}
      - {name: outcome, access: read-only, present: choice}
      - {name: code, access: read-only, present: text}
      - {name: created_at, access: read-only, present: instant}
    operations:
      list: {capability: "notification:read", binds: ListNotifications, items: notifications, filters: [organisation, project, outcome]}
      get: {capability: "notification:read", binds: GetNotification}
    events: [created]

  - kind: delivery
    owner: notification
    type: Delivery
    identity: {field: id, form: minted}
    label: channel
    fields:
      - {name: id, access: read-only, present: text}
      - {name: notification, access: read-only, present: reference, kind: notification}
      - {name: holder, access: read-only, present: text}
      - {name: positions, access: read-only, present: list}
      - {name: channel, access: read-only, present: choice}
      - {name: status, access: read-only, present: choice}
      - {name: attempts, access: read-only, present: number}
      - {name: created_at, access: read-only, present: instant}
      - {name: delivered_at, access: read-only, present: instant}
      - {name: seen_at, access: read-only, present: instant}
      - {name: error_code, access: read-only, present: text}
    operations:
      list: {capability: "notification:read", binds: ListDeliveries, items: deliveries, filters: [notification, holder, channel, status]}
      get: {capability: "notification:read", binds: GetDelivery}
    # An in_app delivery is recorded delivered when its message is written,
    # and never passes through queued
    states:
      initial_state: queued
      entity_type: Delivery
      state_field: status
      states:
        queued: {description: waiting to be sent}
        deferred: {description: held by the holder's quiet hours or digest}
        sent: {description: the channel's adapter accepted it}
        delivered: {description: "the channel confirmed it, or it was written in_app", terminal: true}
        failed: {description: the channel refused it after its last attempt, terminal: true}
        unknown: {description: a send whose outcome could not be learned, never resent, terminal: true}
      transitions:
        - {name: defer, from: queued, to: deferred, trigger: quiet hours or a digest hold it, description: it waits for the holder's time}
        - {name: release, from: deferred, to: queued, trigger: the quiet hours end or the digest is due, description: it is sent}
        - {name: send, from: queued, to: sent, trigger: the adapter accepts it, description: it is on its way}
        - {name: confirm, from: [queued, sent], to: delivered, trigger: the channel confirms it, description: the holder was told}
        - {name: fail, from: [queued, sent], to: failed, trigger: the last attempt is refused, description: it did not arrive}
        - {name: lose, from: queued, to: unknown, trigger: a send times out after it was made, description: nobody can say}
    events: [created, delivered, failed, unknown]

  - kind: preference
    owner: notification
    type: Preference
    identity: {field: id, form: minted}
    label: identity_id
    fields:
      - {name: id, access: read-only, present: text}
      - {name: identity_id, access: read-only, present: text}
      - {name: channels, access: settable, present: list}
      - {name: quiet_hours, access: settable}
      - {name: digest, access: settable}
      - {name: time_zone, access: settable, present: text}
      - {name: updated_at, access: read-only, present: instant}
    operations:
      get: {capability: "notification:receive", binds: GetPreference}
      update: {capability: "notification:receive", binds: SetPreference}
      delete: {capability: "notification:receive", binds: ClearPreference}
    events: [updated, deleted]
```

Each kind answers only what its routes answer: a `preference` is answered to
the person it belongs to and no other ([Who May Do What](#who-may-do-what),
rule 2), so it has no `list`; and no `delivery` carries an address.

---

## Configuration

```yaml
config:
  retention:
    type: duration
    default: 8760h
    min: 720h
    description: How long a notification, its deliveries and the in_app messages held for it are kept, from when it was made. A preference is kept until its person clears it
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      The service trusts a person's authority only on a pass, and only over
      that person's own preference and messages. It trusts a request to tell
      positions only from the owner of the notice, or an actor that owner
      authorised, and reads who holds them only on work passes under that
      notice's authorisation, which a person made.

  boundaries:
    - boundary: Person → Notification. Only through the admin gateway, on a
        pass addressed here, acting on that person's own identity id. An
        operator token is refused
    - boundary: Owner → Notification. NotifyByPosition on the owner's
        registration token, or on a work pass under the authorisation it
        names. Positions and a message, never a person or a channel
    - boundary: Notification → Content. Reads only, each on a work pass under
        the notice's authorisation, carrying content:describe or content:read
    - boundary: Notification → Email Send. One holder's own address and the
        message, on its own registration token. Nothing else of the person

  enforcement:
    - rule: A notice that reaches nobody is never reported as delivered
      mechanism: The outcome is reached_nobody, not_authorised or
        holders_unreadable, answered to the caller and published as
        notification.unreached
    - rule: Nobody chooses for a person how they are told
      mechanism: A request names no channel; a preference is set only on the
        person's own pass
    - rule: Holders are read only for a notice a person allowed
      mechanism: Every read of content is on a work pass minted under the
        notice's authorisation, naming this service as an actor
    - rule: An address never leaves the person's own preference except to
        their own channel
      mechanism: Deliveries, events, logs and audit entries carry identity
        ids only
```

---

## Implementation Notes

- Look the authorisation up at each request. A cache of
  `GET /v1/work/authorisations` would tell a revoked notice's holders for as
  long as it lived.
- Hold each work pass in memory for its one request, and mint a new one for
  each retry ([`protocol/identity`](../protocol/identity.md#the-work-pass),
  rule 13).
- Write the in_app messages before answering, and send nothing external
  before the notification is recorded, so a crash after an email cannot
  leave the notification unrecorded.
- Resolve holders on the date of the fact's `occurred_at`, not on the date
  the request arrived, so a notice sent late still reaches whoever held the
  position when it became true.
- Report a channel this build does not deliver by name, with the channels it
  does. Never accept a preference naming one and then drop its messages.

---

## Known Gaps

**No component implements this document.** A tenant runs no notification
service, so the programme service reports every notice as not handed over
([`architecture/programme-service`](programme-service.md#known-gaps)).

**A wait cannot be told.** A request names a notice, or an occurrence by its
`due-sweep`, and the fact it is about. A wait execution holds for a person is
neither, so execution asks nothing here and a wait opens unannounced
([`architecture/execution`](execution.md#notification)). Telling one needs a
request that can name a wait, its run and its decide route.

**Only email and in_app are delivered.**
[`patterns/notification`](../patterns/notification.md#channel-types) names
webhook, chat, SMS and push channels. None has an adapter a tenant runs, so a
preference naming one is refused rather than accepted and dropped.

**email-send takes no idempotency key.** A `send_raw` whose answer was lost
cannot be safely sent again, so it is recorded `unknown`
([Retrying](#retrying)). An idempotency key on `EmailRequest` closes this, in
[`agents/email-send`](../agents/email-send.md).

**An address is not confirmed.** A person's address is used as they typed
it. A mistyped one sends their messages to a stranger; the message holds no
register row, so what leaks is the notice's own words and the fact's ids.
Confirming an address before it is used is not specified.

**A work authorisation cannot be narrowed to one register.** Its
`capabilities` are names without `resources`, so the `content:read` a
notice's authorisation carries reads whatever the owner may read in content,
not only the position-holders register. This service reads only the register
(rule 4), and content records every read it makes with its run; nothing at
content confines it further.

**This service's own registration carries what it declares.** It declares
`content:read` to receive it in work passes, and a registration is not yet an
enrolment, so its own token could read content with no authorisation behind
it ([`protocol/identity`](../protocol/identity.md#the-work-pass), the gap
there). Rule 4 is this blueprint's, and nothing outside it enforces it yet.

---

## Verification Checklist

- [ ] Every route in [Endpoints](#endpoints) but `NotifyByPosition`, `Services`, `GET /livez` and `GET /readyz` is declared among the manifest's `pass_routes`, with the one capability its row gives ([Endpoints](#endpoints))
- [ ] An operator token on any route is refused with `PASS_REQUIRED` ([Who May Do What](#who-may-do-what) rule 1, [Error Handling](#error-handling))
- [ ] `NotifyByPosition` on a pass is refused with `FORBIDDEN`, and tells nobody ([Who May Do What](#who-may-do-what) rule 3, [Error Handling](#error-handling))
- [ ] `NotifyByPosition` on a registration token whose `identity_id` is not the named authorisation's `owner` is refused with `FORBIDDEN`; on a work pass whose `cid` is that authorisation and whose `identity_id` is its owner, it is admitted ([Who May Do What](#who-may-do-what) rule 3)
- [ ] A request naming as `notice` a programme's `due-sweep` operation, under that operation's authorisation, for an occurrence is admitted and told exactly as a notice is, with no field the request shape does not declare ([Notifying](#notifying))
- [ ] A request naming as `notice` an `agent:` item, under that item's authorisation, with `fact.event` `instruction`, is admitted and told exactly as a notice is ([Notifying](#notifying))
- [ ] An authorisation that is revoked, past its `not_after`, or does not list this service among its `actors` answers `200` with outcome `not_authorised`, and no request is made of content ([Notifying](#notifying), [Outcomes](#outcomes))
- [ ] Every request this service makes of content is on a work pass minted under the request's authorisation, a new one for each retry, and none is on its own registration token ([Who May Do What](#who-may-do-what) rule 4, [Retrying](#retrying))
- [ ] Where no named position has a holder, the answer's outcome is `reached_nobody`, `unheld` names every position, and `notification.unreached` is published ([Outcomes](#outcomes))
- [ ] Where one of two named positions has holders, the outcome is `partly_reached` and `unheld` names the other ([Outcomes](#outcomes))
- [ ] A register read that fails after its retries gives `holders_unreadable`, never `reached_nobody` ([Resolving holders](#resolving-holders), [Outcomes](#outcomes))
- [ ] A holder holding two named positions receives one in_app message and one delivery per channel, each naming both positions ([Deduplication](#deduplication))
- [ ] A second `NotifyByPosition` with the same owner, authorisation and `run` and the same body answers the first notification and creates no delivery; with a different body it is refused with `INVALID_REQUEST` ([Deduplication](#deduplication), [Error Handling](#error-handling))
- [ ] Every holder has an in_app delivery `delivered` before the answer is sent, whatever their preference ([Outcomes](#outcomes), [Notifying](#notifying))
- [ ] An email inside the holder's quiet hours is `deferred` and sent when they end; the in_app message is not deferred ([Notifying](#notifying), [Outcomes](#outcomes))
- [ ] A `send_raw` that times out after it was sent is recorded `unknown` and not sent again ([Retrying](#retrying))
- [ ] Holders are resolved on the date of the fact's `occurred_at` ([Resolving holders](#resolving-holders), [Implementation Notes](#implementation-notes))
- [ ] `GET /v1/notification/preference` answers the pass's own preference, and no route answers or sets another person's ([Who May Do What](#who-may-do-what) rule 2)
- [ ] `PUT /v1/notification/preference` naming a channel other than `email` is refused with `INVALID_REQUEST` ([Error Handling](#error-handling), [Known Gaps](#known-gaps))
- [ ] After `DELETE /v1/notification/preference`, the person's addresses are gone and they are told in_app only ([Setting a preference](#setting-a-preference))
- [ ] No `Delivery`, event, log line or `AuditEntry` carries an address or a register row ([Personal Data](#personal-data), [Events it publishes](#events-it-publishes))
- [ ] The message's text is worded only from `says`, `why` and the fact's `event`, `obligation`, `subject` and `due_at` ([Personal Data](#personal-data))
- [ ] An erasure request erases the person's preference and held messages and reports each delivery naming them as an `ErasureException` ([Personal Data](#personal-data))
- [ ] A notification, its deliveries and its held messages are removed `retention` after it was made ([Configuration](#configuration), [Personal Data](#personal-data))
- [ ] The manifest declares `notification:send`, `notification:read`, `content:describe`, `content:read`, `work:exchange` and `agent:message`, and never `notification:receive` ([Endpoints](#endpoints))
