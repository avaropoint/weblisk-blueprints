<!-- blueprint
type: pattern
name: billing
version: 1.0.0
requires: [protocol/types, patterns/scope, patterns/governance]
platform: any
tier: free
adoption: opt-in
-->

# Billing Pattern

Deciding what a subject is currently entitled to, when the record of what they paid for
lives somewhere else.

## Overview

A deployment that charges for access has two facts to keep straight: what was purchased,
and what may be done right now. They are not the same fact, they change at different
times, and conflating them is how a customer who has paid is refused service while a
customer who has not continues to receive it.

This pattern separates them. **Subscription** is what a provider of record says was
purchased. **Entitlement** is what the deployment permits, computed when an operation is
attempted. Subscription state is a cache of somebody else's truth; entitlement is a
decision made fresh.

The pattern names no provider. Whether the record of purchase lives in a payments
platform, an invoicing system or a signed contract in a filing cabinet, the contracts
here are the same: something outside the deployment holds the truth, it tells the
deployment about changes unreliably, and the deployment must behave correctly while
disagreeing with it.

`adoption: opt-in`. A deployment that charges nobody serves none of this.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/governance
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **The provider of record is the truth; local state is a cache.** Every local record of
   what was purchased is a copy that may be stale, and a reconciliation exists to correct
   it. A deployment that treats its own copy as authoritative will eventually bill or
   refuse against a fact that changed hours ago.
2. **Entitlement is computed at use, never stamped at purchase.** A flag set when a
   payment succeeded is a fact that cannot expire, cannot be revoked, and cannot follow a
   downgrade. Entitlement is derived from current subscription state each time it is
   needed.
3. **Notifications arrive more than once, out of order, or not at all.** Every handler is
   idempotent on the notification's own identifier, tolerates arriving before the event it
   supersedes, and is backed by reconciliation for the case where nothing arrives.
4. **Metering is not entitlement.** What was consumed is recorded for charging and for the
   subject to see. Whether an operation may proceed is a separate decision, so a metering
   failure never silently grants or denies access.
5. **Failing to charge is not a reason to destroy.** A lapsed subscription suspends;
   it does not delete. Data outlives the commercial relationship, because the subject may
   return, may dispute, and in some jurisdictions must be able to retrieve what is theirs.
6. **A subject can always see what they are being charged for.** Usage that cannot be
   inspected cannot be disputed, and an unexplained charge is a support burden and a
   compliance problem at once.
7. **Quota refusals say what was exceeded.** A caller told only that it may not proceed
   cannot tell a limit from a fault, and will retry as though it were a fault.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: record_subscription_state
      description: Record what the provider of record says was purchased
      parameters:
        - name: subject
          type: string
          required: true
          description: Who the subscription belongs to
        - name: plan
          type: string
          required: true
          description: The plan identifier as the provider names it
        - name: status
          type: string
          required: true
          description: The lifecycle state the provider reports
        - name: period_end
          type: string
          required: true
          description: When the current paid period ends
      inherits: A local record of subscription state, understood as a cache rather than the truth
      overridable: true
      override_constraints: The record MUST retain the provider's own identifiers, or reconciliation cannot match against them

    - name: compute_entitlement
      description: Decide what a subject may do now
      parameters:
        - name: subject
          type: string
          required: true
          description: Who is attempting the operation
        - name: capability
          type: string
          required: true
          description: What is being attempted
      inherits: A decision derived from current subscription state at the moment of use
      overridable: true
      override_constraints: MUST NOT be satisfied by reading a flag written at purchase time; entitlement is derived, never stored as a conclusion

    - name: handle_lifecycle_notification
      description: Process a notification that subscription state changed
      parameters:
        - name: notification_id
          type: string
          required: true
          description: The provider's identifier for this notification
        - name: occurred_at
          type: string
          required: true
          description: When the change happened, as distinct from when it was received
      inherits: Idempotent processing keyed on the notification identifier, ordered by occurrence rather than arrival
      overridable: true
      override_constraints: A repeated notification MUST NOT apply twice; a notification older than the state it would overwrite MUST be discarded

    - name: reconcile
      description: Correct local state against the provider of record
      parameters:
        - name: since
          type: string
          required: false
          description: Reconcile subjects whose state may have changed after this point
      inherits: A scheduled correction that does not depend on any notification having arrived
      overridable: true
      override_constraints: Reconciliation MUST be able to run without prior notification, or a dropped notification is permanent

    - name: meter_usage
      description: Record what a subject consumed
      parameters:
        - name: subject
          type: string
          required: true
          description: Who consumed it
        - name: measure
          type: string
          required: true
          description: What is being counted
        - name: quantity
          type: int
          required: true
          description: How much
      inherits: A usage record the subject can inspect and the deployment can charge from
      overridable: true
      override_constraints: A metering failure MUST NOT change whether an operation proceeds

    - name: enforce_quota
      description: Refuse an operation that exceeds what the subject's plan allows
      parameters:
        - name: subject
          type: string
          required: true
          description: Who is attempting the operation
        - name: measure
          type: string
          required: true
          description: The limit being tested
      inherits: A refusal naming the measure exceeded and when it resets
      overridable: true
      override_constraints: The refusal MUST be distinguishable from a fault, so a caller does not retry a limit as though it were an error

  types:
    - name: Subscription
      description: Local record of what a provider of record says was purchased
      inherited_by: The adopting component's subscription store
    - name: Entitlement
      description: What a subject may do, as computed at use
      inherited_by: The adopting component's authorization path
    - name: UsageRecord
      description: What a subject consumed
      inherited_by: The adopting component's metering store
```

---

## Types

```yaml
types:
  Subscription:
    description: A cache of what the provider of record says was purchased
    fields:
      subject:
        name: Subject
        type: string
        required: true
        description: "Who the subscription belongs to"
      provider_reference:
        name: ProviderReference
        type: string
        required: true
        description: "The provider's own identifier, used to reconcile"
      plan:
        name: Plan
        type: string
        required: true
        description: "Plan identifier"
      status:
        name: Status
        type: string
        required: true
        description: "`trialing`, `active`, `past_due`, `suspended`, `cancelled`"
      period_end:
        name: PeriodEnd
        type: string
        required: true
        description: "RFC 3339 timestamp when the current paid period ends"
      observed_at:
        name: ObservedAt
        type: string
        required: true
        description: "When this cache entry was last confirmed against the provider"

  Entitlement:
    description: What a subject may do now, derived rather than stored
    fields:
      subject:
        name: Subject
        type: string
        required: true
        description: "Who this was computed for"
      capability:
        name: Capability
        type: string
        required: true
        description: "What was asked about"
      permitted:
        name: Permitted
        type: bool
        required: true
        description: "Whether it may proceed"
      reason:
        name: Reason
        type: string
        required: false
        description: "Why not, when it may not — a lapsed subscription, an exceeded quota, or a plan that excludes it"

  UsageRecord:
    description: A recorded consumption, inspectable by the subject
    fields:
      subject:
        name: Subject
        type: string
        required: true
        description: "Who consumed it"
      measure:
        name: Measure
        type: string
        required: true
        description: "What was counted"
      quantity:
        name: Quantity
        type: int
        required: true
        description: "How much"
      occurred_at:
        name: OccurredAt
        type: string
        required: true
        description: "RFC 3339 timestamp"
```

---

## Configuration

```yaml
config:
  grace_period_seconds:
    type: int
    default: 259200
    overridable: true
    description: How long a lapsed subscription continues to be served before suspension
  reconcile_interval_seconds:
    type: int
    default: 3600
    overridable: true
    min: 300
    description: How often local subscription state is corrected against the provider
  notification_replay_window_seconds:
    type: int
    default: 604800
    overridable: true
    description: How long a notification identifier is remembered for idempotency
  suspend_on_lapse:
    type: bool
    default: true
    overridable: true
    description: Whether a lapsed subscription suspends access; deletion is never automatic
```

---

## Error Handling

| Condition | Behaviour | Carries |
|---|---|---|
| Notification already processed | Succeed without applying it again | Nothing; a repeat is normal |
| Notification older than current state | Discard | Recorded, not surfaced as an error |
| Provider unreachable during reconciliation | Retain current state, retry, alert | Nothing to the subject |
| Subscription lapsed, within grace | Serve normally | A warning the subject can see |
| Subscription lapsed, past grace | Suspend | Which subscription lapsed and how to restore it |
| Quota exceeded | Refuse this operation | The measure exceeded and when it resets |
| Metering write failed | Proceed with the operation; retry the write | Nothing to the caller |

---

## Implementation Notes

- **Key idempotency on the provider's notification identifier**, not on the subject or the
  event type. Two different changes to one subscription are two notifications, and
  collapsing them loses one.
- **Order by when the change occurred, not when it arrived.** Out-of-order delivery is
  normal, and applying a stale notification last is how a cancelled subscription becomes
  active again.
- **Reconciliation must work with no notifications at all.** Build it that way from the
  start: a system that only corrects what it was told about cannot correct what it was
  never told.
- **Compute entitlement in the request path**, from subscription state, quota usage and
  plan. If that is too slow, cache the inputs rather than the conclusion.
- **Suspension and deletion are different operations with different authority.** Automatic
  suspension for non-payment is reasonable; automatic deletion is not.
- **Show usage before it is charged, not after.** A subject who can see consumption
  accumulating disputes far less than one who receives a total.

---

## Verification Checklist

- [ ] A repeated notification carrying the same identifier MUST NOT be applied twice
- [ ] A notification older than the state it would overwrite MUST be discarded
- [ ] Reconciliation MUST correct local state without any notification having been received
- [ ] Entitlement MUST be derived from current subscription state at the moment of use
- [ ] A subject whose payment succeeded MUST be entitled without waiting for a notification
- [ ] A lapsed subscription MUST suspend rather than delete
- [ ] A metering failure MUST NOT change whether an operation proceeds
- [ ] A quota refusal MUST name the measure exceeded and when it resets
- [ ] A quota refusal MUST be distinguishable by the caller from a transient fault
- [ ] A subject MUST be able to retrieve the usage records they are charged from
