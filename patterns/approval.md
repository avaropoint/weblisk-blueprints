<!-- blueprint
type: pattern
name: approval
version: 1.0.0
requires: [protocol/types, patterns/scope, patterns/policy, patterns/safety]
platform: any
tier: free
-->

# Approval Pattern

Human-in-the-loop confirmation for operations that exceed automatic
authorization. This pattern handles the full lifecycle of approval
requests — routing, decision, escalation, multi-party consensus,
emergency override, and audit trail. Approval is the bridge between
safety classification and human judgment.

## Overview

When `patterns/safety` evaluates an operation intent and the
protection gate returns `require_approval` or `escalate`, the
operation pauses. Something must happen before it can proceed. This
pattern defines what happens: an approval request is filed, routed
to the appropriate authority, decided, and recorded.

Approval is a standalone pattern because it is consumed everywhere:

- **Safety** — protection gates produce `require_approval` decisions.
  This pattern handles the approval flow that follows.
- **Contracts** — collaboration terms between agents may require
  operator sign-off before activation.
- **Workflows** — phase transitions in multi-step workflows may
  require human approval at critical checkpoints.
- **Governance** — policy overrides and compliance exceptions require
  formal approval chains.
- **Any domain** — any operation in any domain that needs human
  confirmation routes through this pattern.

The approval pipeline has six stages:

1. **Request** — an approval request is filed with full intent
   context, scope, justification, and urgency.
2. **Routing** — the request is routed to the correct authority
   level based on operation class, resource class, scope, and
   environment.
3. **Decision** — the authority accepts, rejects, defers, or
   delegates the request.
4. **Escalation** — unanswered requests escalate automatically up
   the authority chain after configurable timeouts.
5. **Multi-party** — critical operations may require N-of-M
   approvers before proceeding.
6. **Audit** — every request, decision, escalation, and override
   is recorded with full context.

Emergency overrides exist for situations where the normal approval
flow is too slow. They bypass the routing and decision stages but
trigger maximum alerting and mandatory post-incident review.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category]
        - name: AgentManifest
          fields_used: [name, capabilities, type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ScopeLevel
          fields_used: [public, internal, confidential, restricted, critical]
        - name: EnvironmentProfile
          fields_used: [name, enforcement_level, scope_overrides]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/policy
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: PolicyContext
          fields_used: [identity, scope_level, environment, operation, resource, agent]
        - name: PolicyDecision
          fields_used: [result, policy_name, matched_rules, enforcement]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/safety
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: OperationClass
          fields_used: [read, create, modify, delete, destroy]
        - name: ResourceClass
          fields_used: [ephemeral, application, system, critical]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Authority matches risk** — The higher the scope and the more
   destructive the operation, the higher the authority level required.
   Auto-approval handles the mundane; human judgment handles the
   critical. A low-risk create on public data is auto-approved. A
   destroy on critical data in production requires an administrator.
   Authority is never underallocated — the routing matrix ensures
   the right level of judgment for every operation.

2. **Separation of duties** — No entity can approve its own actions.
   This is enforced structurally, not by policy — the system rejects
   self-approvals regardless of authority level. An agent cannot
   approve its own recommendation. A domain controller cannot approve
   cross-domain changes it initiated. Critical changes require a
   different approver than the requester. This is not configurable.

3. **Escalation by default** — Unanswered approval requests escalate
   automatically. The system never blocks indefinitely waiting for
   approval. If an operator does not respond within the configured
   timeout, the request escalates to admin. If admin does not
   respond, the system denies the request and emits an expiration
   event. Silence is never consent.

4. **Audit completeness** — Every approval decision — including
   auto-approvals and emergency overrides — is recorded with full
   context for post-incident review. The audit trail includes the
   request, the routing decision, the authority's response, any
   escalations, and the final outcome. Audit records for approvals
   are classified at `confidential` scope minimum and cannot be
   deleted by any authority below admin.

5. **Break-glass exists** — Emergency overrides are a feature, not
   a bug. Production incidents cannot wait for approval chains.
   But emergency overrides trigger maximum alerting — every
   operator, every admin, every monitoring system is notified. And
   they create a mandatory post-incident review obligation that
   cannot be dismissed. The system trusts operators to act in
   emergencies but holds them accountable after.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: approval-routing
      description: Route an approval request to the correct authority based on operation, scope, environment, and policy
      parameters:
        - name: request
          type: ApprovalRequest
          required: true
          description: Complete approval request with intent context, scope, justification, and urgency
        - name: environment
          type: EnvironmentProfile
          required: true
          description: Active environment profile — modifies routing strictness
        - name: routing_rules
          type: "[]ApprovalRoutingRule"
          required: false
          description: Explicit routing rules; if omitted, the default routing matrix is used
      inherits: Authority level resolution, separation-of-duties validation, routing event emission
      overridable: true
      override_constraints: Routing cannot produce a LOWER authority level than the default matrix requires; custom rules can only tighten

    - name: approval-decision
      description: Record an authority's decision on an approval request — accept, reject, defer, or delegate
      parameters:
        - name: request_id
          type: string
          required: true
          description: ID of the approval request being decided
        - name: decider
          type: string
          required: true
          description: Identity of the authority making the decision
        - name: result
          type: enum(accept, reject, defer, delegate)
          required: true
          description: The decision outcome
        - name: reason
          type: string
          required: true
          description: Human-readable justification for the decision
        - name: delegate_to
          type: string
          required: false
          description: Required when result is delegate — identity of the delegated authority
        - name: conditions
          type: "[]string"
          required: false
          description: Optional conditions attached to an accept decision (e.g., "only in maintenance window")
      inherits: Self-approval rejection, decision validation, audit trail, event emission
      overridable: true
      override_constraints: Self-approval rejection cannot be overridden; accepted requests with conditions MUST be re-validated at execution time

    - name: escalation
      description: Escalate an unanswered approval request to a higher authority after timeout
      parameters:
        - name: request_id
          type: string
          required: true
          description: ID of the approval request to escalate
        - name: escalation_rule
          type: EscalationRule
          required: true
          description: The escalation configuration — timeout, target authority, notification channels
      inherits: Timeout monitoring, authority promotion, notification dispatch, escalation audit
      overridable: true
      override_constraints: Maximum escalation count cannot exceed 3; final escalation denial cannot be overridden

    - name: emergency-override
      description: Break-glass procedure for bypassing normal approval flow in critical situations
      parameters:
        - name: request_id
          type: string
          required: true
          description: ID of the approval request being overridden (may be null for new emergency actions)
        - name: operator
          type: string
          required: true
          description: Identity of the operator invoking the override
        - name: reason
          type: string
          required: true
          description: Justification for the emergency override — must be substantive
        - name: mfa_confirmed
          type: boolean
          required: true
          description: Whether multi-factor authentication was completed — MUST be true
      inherits: MFA validation, maximum alerting, mandatory review creation, override audit
      overridable: false
      override_constraints: Emergency override is not overridable — it is an emergency mechanism with fixed behavior

  types:
    - name: AuthorityLevel
      description: Enumeration of approval authority tiers
      inherited_by: Types section
    - name: ApprovalRequest
      description: Formal request for approval with full intent context
      inherited_by: Types section
    - name: ApprovalDecision
      description: Authority's decision on an approval request
      inherited_by: Types section
    - name: ApprovalRoutingRule
      description: Rule for routing requests to the correct authority
      inherited_by: Types section
    - name: EscalationRule
      description: Configuration for timeout-based escalation
      inherited_by: Types section
    - name: MultiPartyRequirement
      description: Configuration for multi-approver consensus
      inherited_by: Types section
    - name: EmergencyOverride
      description: Record of an emergency break-glass override
      inherited_by: Types section

  events:
    - topic: approval.requested
      description: Emitted when a new approval request is filed
      payload: {request_id, intent_id, requester, operation, scope, authority_required, urgency, requested_at}
    - topic: approval.decided
      description: Emitted when an authority accepts or rejects a request
      payload: {request_id, authority, decider, result, reason, conditions, decided_at}
    - topic: approval.escalated
      description: Emitted when an unanswered request escalates to higher authority
      payload: {request_id, from_authority, to_authority, escalation_count, escalated_at}
    - topic: approval.expired
      description: Emitted when a request expires without a decision after all escalations
      payload: {request_id, final_authority, escalation_count, expired_at}
    - topic: approval.override
      description: Emitted when an emergency override is invoked — triggers maximum alerting
      payload: {request_id, operator, reason, mfa_confirmed, override_at, review_required_by}
    - topic: approval.delegated
      description: Emitted when an authority delegates a decision to another authority
      payload: {request_id, delegator, delegate_to, reason, delegated_at}
```

---

## Types

All types declared in the Contracts section are defined below,
organized by concern.

### Authority Levels

The approval system defines four authority levels. Each level
represents a class of decider with increasing trust, scope, and
responsibility. Authority levels are ordered — a higher level can
always decide what a lower level can, but not vice versa.

### Authority Level Definitions

| Level | Ordinal | Who | Can Approve | Limitations |
|-------|---------|-----|-------------|-------------|
| `auto` | 0 | System | Low-risk changes matching auto-approval rules | Cannot approve anything above its rule set |
| `agent` | 1 | Domain controller | Medium-risk changes within its own domain scope | Cannot approve cross-domain or high-risk changes |
| `operator` | 2 | Human operator | High-risk changes, cross-domain changes | Cannot approve critical changes or policy overrides |
| `admin` | 3 | Administrator | Critical changes, policy overrides, system-level changes | No limitations — final authority |

```yaml
AuthorityLevel:
  description: Approval authority tiers ordered by trust and scope
  values:
    - name: auto
      ordinal: 0
      decider: system
      description: >
        Automatic approval for low-risk operations that match
        predefined rules. The system evaluates the request against
        auto-approval criteria (scope, severity, confidence) and
        approves without human intervention. Auto-approval is audited
        identically to human approval.
      constraints:
        - Only approves operations matching explicit auto-approval rules
        - Cannot approve operations above severity "low"
        - Cannot approve operations with confidence below configured threshold
        - Cannot approve cross-domain operations
        - Cannot approve operations in production on system or critical resources

    - name: agent
      ordinal: 1
      decider: domain_controller
      description: >
        Domain controller approval for medium-risk operations within
        the controller's own domain. The domain controller evaluates
        the request using domain-specific knowledge and approves or
        rejects. Agent-level approval is limited to the controller's
        own domain boundary.
      constraints:
        - Only approves operations within the agent's own domain
        - Cannot approve cross-domain operations
        - Cannot approve operations above severity "medium"
        - Cannot approve operations on system or critical resources in production

    - name: operator
      ordinal: 2
      decider: human_operator
      description: >
        Human operator approval for high-risk and cross-domain
        operations. Operators have visibility across domains and can
        approve operations that domain controllers cannot. Operator
        approval requires human judgment and is never automated.
      constraints:
        - Cannot approve critical-severity operations
        - Cannot approve policy overrides
        - Cannot approve system-level configuration changes

    - name: admin
      ordinal: 3
      decider: administrator
      description: >
        Administrator approval for critical operations, policy
        overrides, and system-level changes. Admin is the final
        authority in the approval chain. Admin approval requires
        MFA confirmation for critical-severity operations.
      constraints:
        - No functional limitations — final authority
        - Critical operations require MFA confirmation
        - All admin decisions are audited at critical scope
  comparison: ordinal-based; higher ordinal = higher authority
```

---

### Approval Request

When an operation requires approval — triggered by a `require_approval`
or `escalate` decision from `patterns/safety` — the requesting
component files an approval request. The request carries the full
context needed for the authority to make an informed decision.

### Request Structure

```yaml
ApprovalRequest:
  description: Formal request for approval with full intent context
  fields:
    - name: id
      type: string
      required: true
      description: Unique approval request identifier (generated by the approval engine)
    - name: intent_id
      type: string
      required: true
      description: >
        Reference to the OperationIntent from patterns/safety that
        triggered the approval requirement. The authority can inspect
        the full intent for operation details.
    - name: requester
      type: string
      required: true
      description: >
        Identity of the entity requesting approval — agent name,
        domain controller name, or operator identity. Used for
        separation-of-duties enforcement.
    - name: operation
      type: string
      required: true
      description: >
        Human-readable summary of the operation being requested.
        E.g., "Delete 47 expired user records from production database"
    - name: operation_class
      type: OperationClass
      required: true
      description: Safety classification of the operation (from patterns/safety)
    - name: resource_class
      type: ResourceClass
      required: true
      description: Criticality of the target resource (from patterns/safety)
    - name: scope
      type: ScopeLevel
      required: true
      description: Scope classification of the target (from patterns/scope)
    - name: environment
      type: string
      required: true
      description: Active environment — development, staging, production
    - name: authority_required
      type: AuthorityLevel
      required: true
      description: Minimum authority level required — determined by routing
    - name: justification
      type: string
      required: true
      description: >
        Why this operation is needed. Must be substantive — single-word
        justifications are rejected. The authority uses this to evaluate
        the business case for the operation.
    - name: urgency
      type: enum(normal, urgent, emergency)
      required: true
      description: >
        Request urgency. Normal requests follow standard routing and
        timeouts. Urgent requests have shortened timeouts and priority
        notification. Emergency requests trigger the break-glass flow.
    - name: requested_at
      type: int64
      required: true
      description: Unix epoch seconds when the request was filed
    - name: expires_at
      type: int64
      required: true
      description: >
        Unix epoch seconds when the request expires if not decided.
        Default is requested_at + escalation timeout. Expired requests
        are automatically denied and emit an approval.expired event.
    - name: correlation_id
      type: string
      required: false
      description: Trace ID linking this request to a workflow or task execution
    - name: metadata
      type: map
      required: false
      description: Additional context for domain-specific approval evaluation
```

### Request Example

```yaml
request:
  id: "approval-20260427-001"
  intent_id: "intent-20260427-042"
  requester: "lifecycle-agent"
  operation: "Delete 47 expired user records from production database"
  operation_class: delete
  resource_class: application
  scope: restricted
  environment: production
  authority_required: operator
  justification: >
    Retention policy expired for 47 user records. Data is older than
    90 days and consent has been withdrawn. GDPR compliance requires
    deletion within 30 days of consent withdrawal. 12 days remain.
  urgency: normal
  requested_at: 1777449600
  expires_at: 1777453200
  correlation_id: "workflow-exec-9f2a"
```

---

## Approval Routing

When an approval request is filed, the routing engine determines
which authority level should decide. Routing considers four
dimensions: operation class, resource class, scope level, and
environment. The routing matrix maps these dimensions to the minimum
authority level required.

### Routing Matrix

The base routing matrix uses scope level and operation class as
primary axes. Resource class and environment amplify the result —
they can increase the required authority but never decrease it.

#### Base Authority by Scope × Operation

| Operation | Public | Internal | Confidential | Restricted | Critical |
|-----------|--------|----------|--------------|------------|----------|
| read | auto | auto | auto | agent | operator |
| create | auto | auto | agent | operator | operator |
| modify | auto | agent | operator | operator | admin |
| delete | agent | operator | operator | admin | admin |
| destroy | operator | operator | admin | admin | admin |

#### Environment Amplification

| Environment | Effect |
|-------------|--------|
| development | No amplification — base matrix applies |
| staging | Amplify `auto` → `agent` for delete/destroy operations |
| production | Amplify one level for all operations above `read` on `system` and `critical` resources |

#### Cross-Domain Amplification

Operations that cross domain boundaries are amplified by one
authority level. A cross-domain `modify` that would normally require
`agent` approval is amplified to `operator`. Cross-domain `destroy`
always requires `admin`.

### Routing Algorithm

```
route_approval(request):
  # 1. Lookup base authority from scope × operation matrix
  base_authority = routing_matrix[request.scope][request.operation_class]

  # 2. Amplify for environment
  IF request.environment == "production":
    IF request.resource_class IN [system, critical] AND request.operation_class.ordinal > 0:
      base_authority = amplify(base_authority, 1)
  ELSE IF request.environment == "staging":
    IF request.operation_class IN [delete, destroy]:
      IF base_authority == auto:
        base_authority = agent

  # 3. Amplify for cross-domain
  IF request.metadata.cross_domain == true:
    base_authority = amplify(base_authority, 1)
    IF request.operation_class == destroy:
      base_authority = admin

  # 4. Apply custom routing rules (can only tighten)
  FOR rule IN routing_rules:
    IF rule.matches(request):
      IF rule.authority.ordinal > base_authority.ordinal:
        base_authority = rule.authority

  # 5. Enforce ceiling
  base_authority = min(base_authority, admin)

  # 6. Validate separation of duties
  IF request.requester == candidate_decider(base_authority):
    base_authority = amplify(base_authority, 1)

  request.authority_required = base_authority
  EMIT event("approval.requested", request)
  RETURN request
```

### Routing Rule Structure

```yaml
ApprovalRoutingRule:
  description: Custom rule for routing requests to specific authorities
  fields:
    - name: name
      type: string
      required: true
      description: Human-readable rule name for audit purposes
    - name: condition
      type: string
      required: true
      description: >
        Boolean expression evaluated against request context.
        Supports field references, comparisons, and logical operators.
        E.g., "scope == 'critical' AND operation_class == 'destroy'"
    - name: authority
      type: AuthorityLevel
      required: true
      description: Authority level to route to when condition matches
    - name: priority
      type: int
      required: false
      default: 100
      description: Rule priority — lower number = higher priority. Default rules are priority 1000.
    - name: environment
      type: string
      required: false
      description: If set, rule only applies in this environment
```

### Default Routing Rules

```yaml
approval_routing:
  default_rules:
    - name: low-severity-auto
      condition: "severity == 'low' AND confidence > 0.9"
      authority: auto
      priority: 100

    - name: medium-severity-operator
      condition: "severity == 'medium'"
      authority: operator
      priority: 200

    - name: high-severity-operator
      condition: "severity == 'high'"
      authority: operator
      priority: 200

    - name: critical-severity-admin
      condition: "severity == 'critical'"
      authority: admin
      priority: 50

    - name: cross-domain-admin
      condition: "scope == 'cross-domain'"
      authority: admin
      priority: 50

    - name: bulk-changes-operator
      condition: "changes > 20"
      authority: operator
      priority: 300

    - name: production-destroy-admin
      condition: "environment == 'production' AND operation_class == 'destroy'"
      authority: admin
      priority: 10
```

---

### Approval Decision

When a request reaches the assigned authority, the authority reviews
the request context and makes a decision. Four outcomes are possible:

| Decision | Effect | Next Step |
|----------|--------|-----------|
| `accept` | Operation is authorized to proceed | Execute the operation within the intent validity window |
| `reject` | Operation is denied | Requester is notified; operation does not proceed |
| `defer` | Decision postponed | Request remains pending; escalation timer resets |
| `delegate` | Decision transferred to another authority | New authority receives the request at the same or higher level |

### Decision Structure

```yaml
ApprovalDecision:
  description: Authority's decision on an approval request
  fields:
    - name: request_id
      type: string
      required: true
      description: ID of the approval request being decided
    - name: authority
      type: AuthorityLevel
      required: true
      description: Authority level at which the decision was made
    - name: decider
      type: string
      required: true
      description: >
        Identity of the authority making the decision. For auto-approval,
        this is "system". For all other levels, this is a named identity.
    - name: result
      type: enum(accept, reject, defer, delegate)
      required: true
      description: The decision outcome
    - name: reason
      type: string
      required: true
      description: >
        Justification for the decision. Required for all outcomes —
        including accept. The reason is part of the audit trail and
        MUST be substantive.
    - name: conditions
      type: "[]string"
      required: false
      description: >
        Conditions attached to an accept decision. If present, the
        operation MUST be re-validated against these conditions at
        execution time. E.g., ["execute only during maintenance window",
        "notify sre-team before execution"]
    - name: delegate_to
      type: string
      required: false
      description: >
        Required when result is delegate. Identity of the authority
        receiving the delegation. The delegate MUST be at the same
        or higher authority level.
    - name: decided_at
      type: int64
      required: true
      description: Unix epoch seconds when the decision was made
    - name: multi_party_position
      type: int
      required: false
      description: >
        For multi-party approvals, which position this decision
        fills (1 of N). Omitted for single-authority decisions.
```

### Decision Flow

```
decide_approval(request_id, decider, result, reason):
  request = load_request(request_id)

  # 1. Validate request is still pending
  IF request.status != "pending":
    RETURN error("Request is no longer pending — status: " + request.status)

  # 2. Enforce separation of duties
  IF decider == request.requester:
    RETURN error("Self-approval denied — requester and decider must differ")

  # 3. Validate authority level
  IF decider.authority_level.ordinal < request.authority_required.ordinal:
    RETURN error("Insufficient authority — required: " + request.authority_required)

  # 4. Record the decision
  decision = ApprovalDecision(
    request_id:  request_id,
    authority:   decider.authority_level,
    decider:     decider.identity,
    result:      result,
    reason:      reason,
    decided_at:  now()
  )

  # 5. Handle multi-party requirement
  IF request.multi_party IS NOT NULL:
    record_multi_party_vote(request, decision)
    IF NOT multi_party_threshold_met(request):
      EMIT event("approval.decided", decision)
      RETURN status("pending — awaiting additional approvers")

  # 6. Execute the decision
  IF result == "accept":
    request.status = "approved"
    authorize_intent(request.intent_id)
  ELSE IF result == "reject":
    request.status = "rejected"
    deny_intent(request.intent_id, reason)
  ELSE IF result == "defer":
    request.status = "pending"
    reset_escalation_timer(request)
  ELSE IF result == "delegate":
    request.status = "delegated"
    reroute_request(request, decision.delegate_to)
    EMIT event("approval.delegated", {request_id, decider, delegate_to, reason})

  EMIT event("approval.decided", decision)
  RETURN decision
```

### Auto-Approval

Auto-approval is not a bypass. It is a decision made by the system
using predefined rules. Auto-approvals are audited identically to
human approvals — the same event is emitted, the same audit record
is created, the same decision structure is stored. The only
difference is the decider is "system" instead of a named identity.

```yaml
auto_approval:
  rules:
    - condition: "operation_class == 'create' AND scope IN ['public', 'internal'] AND environment == 'development'"
      max_confidence: 0.0    # no confidence threshold for dev creates
    - condition: "operation_class == 'modify' AND scope == 'public' AND confidence > 0.95"
      max_confidence: 0.95
    - condition: "operation_class == 'read'"
      max_confidence: 0.0    # reads are always auto-approved at the approval level

  constraints:
    - Auto-approval NEVER applies to delete or destroy operations
    - Auto-approval NEVER applies in production for system or critical resources
    - Auto-approval NEVER applies to cross-domain operations
    - Auto-approval rules are evaluated BEFORE routing — if no rule matches, routing proceeds normally
```

---

## Escalation

Approval requests do not wait forever. Every pending request has an
escalation timer. When the timer expires, the request escalates to
the next authority level. If the highest authority does not respond,
the request is denied and expires.

### Escalation Rules

```yaml
EscalationRule:
  description: Configuration for timeout-based approval escalation
  fields:
    - name: timeout_seconds
      type: int
      required: true
      description: >
        Seconds to wait for a decision before escalating. Default
        values by urgency: normal=3600 (1 hour), urgent=900 (15 min),
        emergency=300 (5 min).
    - name: escalate_to
      type: AuthorityLevel
      required: true
      description: Authority level to escalate to — must be higher than current level
    - name: notify
      type: "[]string"
      required: true
      description: >
        Notification channels to alert on escalation. Always includes
        the alerting agent. May include email, SMS, or pager channels.
    - name: max_escalations
      type: int
      required: true
      default: 3
      description: >
        Maximum number of escalation steps before the request is
        auto-denied. Default is 3 (auto → agent → operator → admin).
        After max escalations, the request expires.
```

### Escalation Chain

The default escalation chain follows the authority level ordering:

```
auto → agent → operator → admin → DENY (expired)
```

Each step has a configurable timeout. When a request escalates, the
previous authority loses decision rights — only the new authority
can decide.

### Escalation Flow

```
escalation_monitor():
  EVERY 60 SECONDS:
    pending = load_pending_requests()
    FOR request IN pending:
      elapsed = now() - request.last_activity_at
      rule = get_escalation_rule(request.authority_required, request.urgency)

      IF elapsed > rule.timeout_seconds:
        IF request.escalation_count >= rule.max_escalations:
          # Final escalation — deny and expire
          request.status = "expired"
          EMIT event("approval.expired", {
            request_id: request.id,
            final_authority: request.authority_required,
            escalation_count: request.escalation_count,
            expired_at: now()
          })
          deny_intent(request.intent_id, "Approval expired after " + request.escalation_count + " escalations")
        ELSE:
          # Escalate to next authority
          previous_authority = request.authority_required
          request.authority_required = next_authority(request.authority_required)
          request.escalation_count += 1
          request.last_activity_at = now()
          notify_channels(rule.notify, request)

          EMIT event("approval.escalated", {
            request_id: request.id,
            from_authority: previous_authority,
            to_authority: request.authority_required,
            escalation_count: request.escalation_count,
            escalated_at: now()
          })
```

### Default Timeouts by Urgency

| Urgency | Auto → Agent | Agent → Operator | Operator → Admin | Admin → Deny |
|---------|-------------|-----------------|-----------------|-------------|
| normal | 3600s (1h) | 3600s (1h) | 3600s (1h) | 7200s (2h) |
| urgent | 300s (5m) | 600s (10m) | 900s (15m) | 1800s (30m) |
| emergency | 60s (1m) | 120s (2m) | 300s (5m) | 600s (10m) |

---

### Multi-Party Approval

Critical operations may require approval from multiple independent
authorities. Multi-party approval ensures that no single person can
authorize the most dangerous operations. It adds consensus to the
decision — N of M designated approvers must agree before the
operation proceeds.

### Multi-Party Requirement

```yaml
MultiPartyRequirement:
  description: Configuration for multi-approver consensus
  fields:
    - name: min_approvers
      type: int
      required: true
      description: >
        Minimum number of approvers required. Must be >= 2 for
        multi-party. The request is approved when min_approvers
        accept. It is rejected when (pool_size - min_approvers + 1)
        reject — meaning approval becomes mathematically impossible.
    - name: from_pool
      type: "[]string"
      required: true
      description: >
        Pool of eligible approvers by identity. All must be at or
        above the required authority level. The requester is
        automatically excluded from the pool.
    - name: timeout_per_approver
      type: int
      required: true
      default: 3600
      description: >
        Seconds to wait for each individual approver before the
        request escalates. Independent of the overall escalation timer.
    - name: require_unanimous
      type: boolean
      required: false
      default: false
      description: >
        If true, ALL pool members must approve (min_approvers = pool
        size). If false, only min_approvers must approve.
```

### Multi-Party Triggers

Multi-party approval is triggered by routing rules, not by request.
The routing matrix determines when multi-party is required:

```yaml
multi_party_rules:
  - condition: "scope == 'critical' AND operation_class == 'destroy'"
    min_approvers: 2
    from_pool: [admin_pool]
    require_unanimous: true

  - condition: "scope == 'critical' AND operation_class == 'delete' AND environment == 'production'"
    min_approvers: 2
    from_pool: [admin_pool]

  - condition: "resource_class == 'critical' AND operation_class IN ['modify', 'delete', 'destroy']"
    min_approvers: 2
    from_pool: [operator_pool, admin_pool]

  - condition: "metadata.policy_override == true"
    min_approvers: 2
    from_pool: [admin_pool]
    require_unanimous: true
```

### Multi-Party Decision Logic

```
multi_party_evaluate(request, decision):
  votes = load_votes(request.id)
  accepts = count(votes WHERE result == "accept")
  rejects = count(votes WHERE result == "reject")
  pool_size = length(request.multi_party.from_pool) - excluded_count

  # Check if approval threshold met
  IF accepts >= request.multi_party.min_approvers:
    RETURN "approved"

  # Check if rejection is mathematically certain
  remaining = pool_size - accepts - rejects
  IF accepts + remaining < request.multi_party.min_approvers:
    RETURN "rejected"

  # Still pending
  RETURN "pending"
```

---

## Separation of Duties

Separation of duties is not a policy — it is a structural
constraint enforced by the approval engine. No configuration can
disable it. No authority level can override it. The system rejects
self-approvals at the protocol level.

### Rules

| Rule | Who | Cannot Approve | Enforcement |
|------|-----|---------------|-------------|
| Self-approval prohibition | Any entity | Its own requests | Approval engine rejects before routing |
| Domain boundary | Domain controller | Cross-domain changes it initiated | Routing amplifies to operator minimum |
| Requester exclusion | Any requester | Requests where it is the sole authority | Escalation promotes to next level |
| Critical separation | Any single entity | Critical operations it requested | Multi-party pool excludes the requester |

### Enforcement Logic

```
validate_separation_of_duties(request, decider):
  # Rule 1: Self-approval is always rejected
  IF decider.identity == request.requester:
    RETURN reject("Self-approval prohibited — requester and decider must differ")

  # Rule 2: Domain controllers cannot approve their own cross-domain requests
  IF decider.type == "domain_controller" AND request.metadata.cross_domain == true:
    IF decider.domain == request.metadata.source_domain:
      RETURN reject("Domain controller cannot approve cross-domain changes from its own domain")

  # Rule 3: For multi-party, requester is excluded from the pool
  IF request.multi_party IS NOT NULL:
    IF decider.identity IN request.multi_party.from_pool:
      IF decider.identity == request.requester:
        RETURN reject("Requester excluded from multi-party approval pool")

  RETURN allow()
```

---

### Emergency Override

Emergency overrides exist because production incidents do not wait
for approval chains. When a critical system is failing and the fix
requires an operation that normally needs admin approval, operators
need a way to act immediately. The emergency override is that
mechanism.

Emergency overrides are not a loophole. They are a controlled
break-glass procedure with maximum accountability:

1. **MFA required** — the operator must complete multi-factor
   authentication before the override is accepted.
2. **Maximum alerting** — every operator, every admin, and every
   configured monitoring channel is notified immediately.
3. **Mandatory review** — the override creates a review obligation
   that must be fulfilled within a configured window (default 24
   hours). The review cannot be dismissed or auto-closed.
4. **Full audit** — the override is recorded at `critical` scope
   with the operator's identity, justification, MFA confirmation,
   and timestamp.

### Override Structure

```yaml
EmergencyOverride:
  description: Record of an emergency break-glass override
  fields:
    - name: id
      type: string
      required: true
      description: Unique override identifier
    - name: request_id
      type: string
      required: false
      description: >
        ID of the approval request being overridden. May be null if
        the override is for an emergency action that was never
        formally requested.
    - name: operator
      type: string
      required: true
      description: Identity of the operator invoking the override
    - name: reason
      type: string
      required: true
      description: >
        Justification for the emergency override. Must be substantive.
        Single-word reasons are rejected. The review board uses this
        to evaluate the override's appropriateness.
    - name: mfa_confirmed
      type: boolean
      required: true
      description: Whether multi-factor authentication was completed — MUST be true
    - name: override_at
      type: int64
      required: true
      description: Unix epoch seconds when the override was invoked
    - name: review_required_by
      type: int64
      required: true
      description: >
        Unix epoch seconds by which the post-incident review must be
        completed. Default is override_at + 86400 (24 hours).
    - name: review_completed
      type: boolean
      required: false
      default: false
      description: Whether the mandatory review has been completed
    - name: review_outcome
      type: enum(justified, unjustified, inconclusive)
      required: false
      description: Outcome of the post-incident review, when completed
```

### Override Flow

```
emergency_override(operator, request_id, reason):
  # 1. Validate MFA
  IF NOT verify_mfa(operator):
    RETURN error("Emergency override requires MFA confirmation")

  # 2. Validate reason is substantive
  IF length(reason) < 20 OR word_count(reason) < 5:
    RETURN error("Override reason must be substantive — minimum 5 words, 20 characters")

  # 3. Create override record
  override = EmergencyOverride(
    id:                  generate_id("override"),
    request_id:          request_id,
    operator:            operator.identity,
    reason:              reason,
    mfa_confirmed:       true,
    override_at:         now(),
    review_required_by:  now() + 86400,
    review_completed:    false
  )

  # 4. Authorize the intent immediately
  IF request_id IS NOT NULL:
    request = load_request(request_id)
    request.status = "overridden"
    authorize_intent(request.intent_id)

  # 5. Maximum alerting — notify everyone
  notify_all_operators(override)
  notify_all_admins(override)
  notify_channels(["alerting", "pager", "email"], override)

  # 6. Create mandatory review obligation
  create_review_obligation(override)

  # 7. Emit override event
  EMIT event("approval.override", {
    request_id:         request_id,
    operator:           operator.identity,
    reason:             reason,
    mfa_confirmed:      true,
    override_at:        now(),
    review_required_by: override.review_required_by
  })

  RETURN override
```

### Override Constraints

- Emergency overrides are available to `operator` and `admin` only.
  Agents and domain controllers cannot invoke emergency overrides.
- MFA is non-negotiable. If MFA infrastructure is unavailable, the
  override cannot proceed. This is intentional — MFA unavailability
  during an incident is itself a critical issue.
- The mandatory review window is configurable but defaults to 24
  hours. If the review is not completed within the window, a
  `review_overdue` alert is emitted every hour until completion.
- Repeated emergency overrides by the same operator within a short
  window (default: 4 hours) trigger an additional admin alert.
  This is not a block — it is a signal that the operator may need
  assistance.

---

## Approval Audit Trail

Every approval action is recorded in an immutable audit trail. The
audit trail covers the complete lifecycle of each request — from
filing through final disposition, including all escalations, votes,
overrides, and reviews.

### Audit Records

| Event | Recorded Fields | Scope |
|-------|----------------|-------|
| Request filed | request_id, intent_id, requester, operation, scope, authority, urgency, timestamp | confidential |
| Auto-approved | request_id, rules_matched, confidence, timestamp | confidential |
| Decision made | request_id, decider, authority, result, reason, conditions, timestamp | confidential |
| Escalated | request_id, from_authority, to_authority, escalation_count, timestamp | confidential |
| Delegated | request_id, delegator, delegate_to, reason, timestamp | confidential |
| Expired | request_id, final_authority, escalation_count, timestamp | confidential |
| Multi-party vote | request_id, voter, position, result, votes_so_far, threshold, timestamp | confidential |
| Emergency override | request_id, operator, reason, mfa_confirmed, timestamp | critical |
| Override review | override_id, reviewer, outcome, timestamp | critical |

### Audit Retention

- Approval audit records are classified at `confidential` scope
  minimum. Emergency override records are classified at `critical`
  scope.
- Audit records MUST be retained for a minimum of 365 days.
- Audit records cannot be deleted by any authority below `admin`.
- Override audit records cannot be deleted by any authority — they
  are permanently retained.
- Audit records are append-only. Existing records cannot be modified
  — corrections are recorded as new entries referencing the original.

---

## Integration Points

### Safety (`patterns/safety`)

Safety is the primary trigger for approval requests. When the safety
engine evaluates an OperationIntent and the protection gate returns
`require_approval` or `escalate`, the intent is paused and an
approval request is filed with this pattern. The approval request
carries the intent_id as a reference. When the approval is decided,
this pattern either authorizes or denies the intent, allowing the
safety engine to proceed or block the operation.

### Scope (`patterns/scope`)

Scope levels feed directly into the routing matrix. Higher scope
levels route to higher authority levels. Scope propagation rules
apply to approval requests — a request inherits the scope of the
operation it guards. Cross-scope operations (where source and target
have different scope levels) use the higher scope for routing.

### Policy (`patterns/policy`)

Policy evaluation may produce `escalate` decisions that trigger
approval requests. Custom routing rules are expressed as policy-like
conditions. The approval engine consumes policy decisions but does
not duplicate the policy evaluation engine — it delegates to
`patterns/policy` for condition evaluation.

### Governance (`patterns/governance`)

This pattern was extracted from governance and replaces the Approval
Authority section (authority levels, approval matrix, separation of
duties, escalation). Governance retains compliance profiles, evidence
collection, and behavioral boundaries. Governance consumes this
pattern for approval-related compliance reporting.

### Workflows (`patterns/workflow`)

Workflow phase transitions may require approval at critical
checkpoints. Workflows file approval requests for phase transitions
that cross risk boundaries. The workflow pauses at the approval gate
and resumes when the decision is received.

### Contracts (`patterns/contract`)

Contract activation between agents may require operator approval,
especially for contracts that grant elevated capabilities or cross
domain boundaries. The contract engine files approval requests
through this pattern when contract policy requires sign-off.

---

## Error Handling

All errors use the standard `ErrorResponse` format from
`protocol/types`:

```json
{
  "error": "Self-approval denied — requester and decider must differ",
  "code": "APPROVAL_SELF_DENIED",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "request_id": "approval-20260427-001",
    "requester": "lifecycle-agent",
    "decider": "lifecycle-agent",
    "action": "A different authority must approve this request"
  }
}
```

```json
{
  "error": "Insufficient authority level for this approval",
  "code": "APPROVAL_AUTHORITY_INSUFFICIENT",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "request_id": "approval-20260427-002",
    "required_authority": "admin",
    "actual_authority": "operator",
    "action": "Request requires admin-level approval"
  }
}
```

```json
{
  "error": "Approval request expired after maximum escalations",
  "code": "APPROVAL_EXPIRED",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "request_id": "approval-20260427-003",
    "escalation_count": 3,
    "final_authority": "admin",
    "action": "Re-file the approval request or use emergency override if critical"
  }
}
```

```json
{
  "error": "Emergency override requires MFA confirmation",
  "code": "APPROVAL_OVERRIDE_MFA_REQUIRED",
  "category": "permanent",
  "retryable": true,
  "detail": {
    "operator": "ops-01",
    "action": "Complete MFA authentication and retry the override"
  }
}
```

---

## Implementation Notes

- Approval is a gate, not a queue. Pending requests are actively
  monitored for escalation — they are not fire-and-forget. The
  escalation monitor runs on a configurable interval (default 60s).
- Approval state is persisted to durable storage. If the hub
  restarts, pending requests are restored and escalation timers
  resume from where they left off. Requests do not silently expire
  on system restart.
- Auto-approval evaluation SHOULD complete in under 10ms. Routing
  matrix lookup SHOULD complete in under 20ms. Human decision
  latency is unbounded but capped by escalation timeouts.
- The routing matrix is loaded at startup from configuration.
  Changes to the routing matrix require a configuration reload.
  Mid-request routing changes are not permitted — a request routed
  to `operator` stays with `operator` even if the matrix changes.
- Multi-party approval pools SHOULD be resolved at request filing
  time, not at decision time. Pool membership changes after filing
  do not affect in-flight requests.
- Separation of duties is enforced at the approval engine level,
  not at the application level. Implementations cannot bypass it
  by calling lower-level APIs. The engine rejects self-approvals
  before any business logic executes.
- Emergency override MFA verification SHOULD use the platform's
  existing MFA infrastructure. If no MFA is configured, the
  platform MUST reject emergency overrides entirely — operating
  without MFA is itself a safety concern.
- Approval events are emitted via `patterns/messaging` to the
  standard event bus. Consumers include `patterns/alerting` for
  notification, `patterns/observability` for metrics, and
  `patterns/governance` for compliance reporting.

---

## Conformance

### MUST

- Every `require_approval` and `escalate` decision from safety MUST result in an ApprovalRequest.
- Approval routing MUST use the routing matrix — custom rules can tighten but never loosen.
- Self-approval MUST be rejected structurally — no configuration can disable separation of duties.
- Every approval decision MUST include a substantive reason.
- Every approval decision MUST emit an `approval.decided` event.
- Escalation MUST be automatic — unanswered requests escalate after configured timeouts.
- Escalation MUST stop after max_escalations and deny the request.
- Emergency overrides MUST require MFA confirmation.
- Emergency overrides MUST trigger notification to all operators and admins.
- Emergency overrides MUST create a mandatory post-incident review obligation.
- Audit records MUST be append-only and retained for minimum 365 days.
- Override audit records MUST be permanently retained — no authority can delete them.
- Multi-party approvals MUST exclude the requester from the approval pool.
- Approval state MUST be persisted to durable storage and survive hub restarts.

### SHOULD

- Auto-approval evaluation SHOULD complete in under 10ms.
- Routing matrix lookup SHOULD complete in under 20ms.
- Escalation monitor SHOULD run at 60-second intervals.
- Operators SHOULD receive real-time alerts on escalations and emergency overrides.
- Multi-party pools SHOULD be resolved at request filing time.
- Approval metrics SHOULD be exposed via the observability pipeline.
- Override review deadlines SHOULD be enforced with recurring alerts.

### MAY

- Implementations MAY cache routing matrix lookups for performance (recommended TTL: 60s max).
- Implementations MAY extend AuthorityLevel with domain-specific levels that map to a base level.
- Implementations MAY implement the approval engine as a separate service or in-process library.
- Implementations MAY add custom auto-approval rules scoped to specific domains.
- Implementations MAY support configurable multi-party pool resolution strategies.
- Implementations MAY integrate with external identity providers for MFA verification.

---

## Verification Checklist

- [ ] `require_approval` decisions from safety produce an ApprovalRequest
- [ ] `escalate` decisions from safety produce an ApprovalRequest
- [ ] Routing matrix maps scope × operation to correct authority level
- [ ] Environment amplification increases authority for production system/critical resources
- [ ] Cross-domain operations amplify authority by one level
- [ ] Self-approval is rejected — requester cannot approve own request
- [ ] Domain controllers cannot approve cross-domain changes from their own domain
- [ ] Auto-approval matches only explicitly configured low-risk rules
- [ ] Auto-approvals are audited identically to human approvals
- [ ] Escalation fires after configured timeout per authority level
- [ ] Escalation promotes to next authority level in chain
- [ ] Maximum escalations result in denial and expiration event
- [ ] Multi-party approval requires N-of-M acceptances
- [ ] Multi-party pool excludes the requester
- [ ] Multi-party rejection is detected when approval becomes mathematically impossible
- [ ] Emergency override requires MFA
- [ ] Emergency override notifies all operators and admins
- [ ] Emergency override creates mandatory review obligation
- [ ] Override review deadline triggers recurring alerts if overdue
- [ ] All approval events are emitted to the event bus
- [ ] Audit records are append-only and classified at confidential minimum
- [ ] Override audit records are classified at critical scope
- [ ] Approval state persists across hub restarts
- [ ] Expired requests are automatically denied
- [ ] Delegated requests transfer to same-or-higher authority
- [ ] Conditions on accept decisions are re-validated at execution time
