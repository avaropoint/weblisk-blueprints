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

The pattern carries a second subject for the same reason: **a budget.** Metering says
what was spent; a budget says what may be. Where a tenant's agents acquire capabilities
as the work requires, the customer's control is not approving each acquisition — it is
bounding what any of them may consume, before they consume it.

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
8. **A budget is checked before consumption, never after.** A limit discovered once the
   spend has happened is a report. Enforcement happens at the same point in the request
   path as entitlement, so an operation that would exceed a budget does not run.
9. **A budget bounds an actor, not only a payer.** A limit that can only stop the tenant
   cannot stop one misbehaving agent without stopping the business. Budgets attach to a
   tenant, an org, a project or a single agent, and the narrowest one that applies wins.
10. **A child budget cannot exceed its parent's remainder.** The plan is the root
    allocation and every budget beneath it subdivides what is left, so the sum of
    internal limits can never authorise more than was purchased.
11. **Behaviour at the boundary is declared, not assumed.** Degrading, refusing and
    pausing are different answers, and the right one depends on what is being bounded.
    Degrading is the default: a hard stop on a customer-facing surface is usually worse
    than a narrower answer.
12. **Exhaustion is an event, not a silent condition.** A budget reached without anyone
    being told is a budget discovered by a complaint.

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
      description: Record what a subject consumed, and what consumed it on their behalf
      parameters:
        - name: subject
          type: string
          required: true
          description: Who is charged
        - name: actor
          type: string
          required: true
          description: What consumed it — the agent, connector or surface acting for the subject. A cost with no actor can be seen and not acted on
        - name: measure
          type: string
          required: true
          description: What is being counted
        - name: quantity
          type: int
          required: true
          description: How much
      inherits: A usage record attributable to both the subject charged and the actor that spent, which the subject can inspect and the deployment can charge from
      overridable: true
      override_constraints: A metering failure MUST NOT change whether an operation proceeds; `actor` MUST NOT be omitted, because stopping unexpected consumption requires knowing what to stop

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

    - name: declare_budget
      description: Bound what a scope may consume of a measure over a period
      parameters:
        - name: scope
          type: string
          required: true
          description: What the budget bounds — a tenant, an org, a project, or one agent
        - name: measure
          type: string
          required: true
          description: What is being bounded, from the same vocabulary metering uses
        - name: limit
          type: int
          required: true
          description: The allowance for one period
        - name: period
          type: string
          required: true
          description: The window the allowance covers, after which it resets
        - name: on_exhaustion
          type: string
          required: true
          description: What happens at the boundary — degrade, refuse, or pause
      inherits: A declared limit, evaluated before consumption, with a stated behaviour at its edge
      overridable: true
      override_constraints: A budget MUST NOT exceed its parent scope's remaining allowance, and on_exhaustion MUST be declared rather than defaulted silently

    - name: check_budget
      description: Decide whether an operation may consume, before it does
      parameters:
        - name: actor
          type: string
          required: true
          description: What is about to consume
        - name: measure
          type: string
          required: true
          description: What it would consume
        - name: quantity
          type: int
          required: true
          description: How much, estimated where it cannot be known exactly
      inherits: A decision evaluated at the same point as entitlement, naming the budget that bound it
      overridable: true
      override_constraints: MUST be evaluated before the operation runs. A check performed afterwards is metering, not budgeting

    - name: report_exhaustion
      description: Make a reached budget visible to the people who can act on it
      parameters:
        - name: budget
          type: string
          required: true
          description: Which budget was reached
        - name: actor
          type: string
          required: true
          description: What consumed the last of it
      inherits: An event carrying the budget, the actor and the behaviour applied, routed per patterns/alerting
      overridable: true
      override_constraints: Exhaustion MUST emit an event even where on_exhaustion is degrade, because a silently narrowed service is the hardest failure to diagnose

  types:
    - name: Budget
      description: A declared limit on what a scope may consume
      inherited_by: The adopting component's budget store
    - name: BillingSubscription
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
  BillingSubscription:
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

  Budget:
    description: A declared limit on what a scope may consume of one measure
    fields:
      scope:
        name: Scope
        type: string
        required: true
        description: "What is bounded — `tenant`, `org`, `project` or `agent`"
      scope_id:
        name: ScopeID
        type: string
        required: true
        description: "Which tenant, org, project or agent"
      measure:
        name: Measure
        type: string
        required: true
        description: "What is bounded, from the vocabulary metering uses"
      limit:
        name: Limit
        type: int
        required: true
        description: "Allowance for one period"
      period:
        name: Period
        type: string
        required: true
        description: "`hour`, `day`, `month`, or the subscription period"
      consumed:
        name: Consumed
        type: int
        required: true
        description: "Consumed so far in the current period"
      on_exhaustion:
        name: OnExhaustion
        type: string
        required: true
        description: "`degrade` — serve a narrower result; `refuse` — decline the operation; `pause` — hold work until the period resets or the limit is raised"
      parent:
        name: Parent
        type: string
        required: false
        description: "The budget this subdivides. Absent means the plan is the parent"

  UsageRecord:
    description: A recorded consumption, inspectable by the subject
    fields:
      subject:
        name: Subject
        type: string
        required: true
        description: "Who is charged"
      actor:
        name: Actor
        type: string
        required: true
        description: "What consumed it on the subject's behalf — the agent, connector or surface. Without it a rising cost is visible and not addressable"
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
  default_on_exhaustion:
    type: string
    default: degrade
    overridable: true
    description: Behaviour where a budget declares none. Degrading is the default because a hard stop on a customer-facing surface is usually worse than a narrower answer
  exhaustion_warning_fraction:
    type: float
    default: 0.8
    overridable: true
    min: 0.5
    max: 0.99
    description: Fraction of a budget at which a warning is emitted, so exhaustion is anticipated rather than discovered
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
| Budget reached, `on_exhaustion: degrade` | Serve a narrower result | Which budget, and that the result is narrowed |
| Budget reached, `on_exhaustion: refuse` | Decline this operation | Which budget, the actor, and when the period resets |
| Budget reached, `on_exhaustion: pause` | Hold the work | Which budget, and that the work resumes on reset or on the limit being raised |
| A budget declared above its parent's remainder | Refuse the declaration | Which parent, and what remains |
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
- **Estimate before an operation whose cost is not known in advance.** Inference and
  crawling cannot be priced exactly beforehand. Check against an estimate, meter the
  actual, and let the next check see the difference — a budget that can only be enforced
  on known costs does not bound the expensive operations.
- **Evaluate the narrowest applicable budget, and report which one bound the decision.**
  An operator told only that a limit was hit cannot tell whether to raise the agent's
  budget or the tenant's.
- **Warn before exhausting.** The default warning fraction exists so that a budget is
  anticipated. A limit that first announces itself by degrading service has already cost
  something.
- **Attribute every measure to an actor, not only to a payer.** A tenant whose agents
  acquire capabilities as the work requires will see costs it did not individually
  authorise, which is the intended behaviour. What makes that safe is not prior approval
  of each one — it is that unexpected consumption is visible, attributable to the agent
  that caused it, and stoppable. A usage record naming only the payer supports the first
  and neither of the others.

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
- [ ] Every usage record MUST name the actor that consumed the measure, not only the subject charged
- [ ] A budget MUST be evaluated before the operation it bounds runs
- [ ] A budget declared above its parent scope's remaining allowance MUST be refused
- [ ] Where several budgets apply, the narrowest MUST decide, and the decision MUST name it
- [ ] Reaching a budget MUST emit an event even where the behaviour is to degrade
- [ ] An operation whose cost is not knowable in advance MUST be checked against an estimate and metered on its actual consumption
- [ ] A budget bounding one agent MUST NOT stop another agent in the same tenant
