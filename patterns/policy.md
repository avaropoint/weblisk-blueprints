<!-- blueprint
type: pattern
name: policy
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/scope]
platform: any
tier: free
-->

# Policy Pattern

Universal rules engine for the Weblisk platform. A policy is an
executable algorithm that evaluates context — scope level, environment
profile, identity claims, operation type, resource classification —
and returns a decision. Policies are generic. They are not tied to
any domain. Governance consumes policies. Safety consumes policies.
Privacy consumes policies. Any domain extends them.

## Overview

Weblisk is opt-in, not restrictive. Policies are the mechanism for
protection. A policy is declarative data — a YAML structure that any
tool can parse, validate, and evaluate without executing arbitrary code.

The policy engine answers one question: **given this context, is this
operation allowed?** It receives the full evaluation context, evaluates
all matching policies in precedence order, and returns a single
decision: allow, deny, escalate, or audit.

Policies compose. Multiple policies can target the same entity. When
they do, the most restrictive decision wins. A namespace policy can
tighten what a hub policy permits, but never loosen it. Policies only
ever add constraints — the monotonic restriction principle.

This pattern defines the WHAT and HOW of rules — structure, evaluation,
composition, lifecycle. Compliance, evidence collection, and audit
reporting belong to `patterns/governance`, which consumes this engine.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, capabilities, type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category]
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
```

---

## Design Principles

1. **Declarative rules** — Policies are data, not code. They are
   defined as YAML structures that any tool can parse, validate,
   and evaluate. No Turing-complete policy language. The evaluation
   engine is separate from the policy definition. Policies are
   portable, auditable, and safe to distribute across trust
   boundaries.

2. **Context-driven evaluation** — Every policy evaluation receives
   the full context: scope level, environment profile, identity
   claims, operation type, resource classification. The policy never
   guesses. Missing context causes a fail-closed deny. The same
   context always produces the same decision.

3. **Most-restrictive wins** — When multiple policies apply to the
   same target, the most restrictive decision prevails. A policy can
   tighten but never loosen what a higher-precedence policy restricts.
   Decision hierarchy: deny > escalate > audit > allow.

4. **Scope-activated** — Policies can declare a minimum scope level
   at which they activate. A policy for `restricted` scope doesn't
   fire for `public` data. The scope activation check is the first
   step in evaluation — non-matching policies are skipped entirely.

5. **Fail-closed** — If policy evaluation fails — missing context,
   evaluation error, timeout — the default decision is deny. The
   system never silently permits an operation it couldn't evaluate.
   Fail-closed is not configurable.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: policy-definition
      description: Declare a policy as a structured YAML document with rules, target, enforcement mode, and precedence
      parameters:
        - name: policy
          type: PolicyDefinition
          required: true
          description: Complete policy document — see PolicyDefinition type for all fields
      inherits: Policy registration, validation, precedence assignment, scope activation
      overridable: true
      override_constraints: Scope level cannot be overridden at a lower precedence; system policies are immutable from hub/namespace/agent level

    - name: policy-evaluation
      description: Evaluate all matching policies against a context and return a single decision
      parameters:
        - name: context
          type: PolicyContext
          required: true
          description: Full evaluation context — identity, scope, environment, operation, resource, agent, timestamp
        - name: policies
          type: "[]PolicyDefinition"
          required: false
          description: Explicit policy set to evaluate; if omitted, all active policies matching the context are loaded
      inherits: Context validation, scope activation filtering, precedence-ordered evaluation, most-restrictive composition
      overridable: true
      override_constraints: Evaluation MUST be fail-closed; the most-restrictive-wins rule cannot be overridden

    - name: policy-composition
      description: Combine decisions from multiple policies on the same target into a single result
      parameters:
        - name: decisions
          type: "[]PolicyDecision"
          required: true
          description: Individual decisions from each matching policy
        - name: composition_strategy
          type: enum(most_restrictive, first_match)
          required: false
          default: most_restrictive
          description: How to combine — most restrictive (default) or first match in priority order
      inherits: Decision ranking, monotonic restriction enforcement, composition audit trail
      overridable: true
      override_constraints: Most-restrictive strategy cannot be overridden to produce a LESS restrictive result than any individual decision

    - name: policy-lifecycle
      description: Manage the lifecycle of a policy from creation through archival
      parameters:
        - name: policy
          type: PolicyDefinition
          required: true
          description: The policy to manage
        - name: action
          type: enum(create, activate, update, deactivate, deprecate, archive)
          required: true
          description: Lifecycle action to perform
        - name: reason
          type: string
          required: false
          description: Human-readable reason for the action (required for deactivate, deprecate, archive)
      inherits: State validation, version bump on update, event emission, audit trail
      overridable: true
      override_constraints: Active policies cannot be deleted — they must be deactivated first; archived policies are immutable

  types:
    - name: PolicyDefinition
      description: Complete policy document with rules, target, enforcement, and metadata
      inherited_by: Policy Types section
    - name: PolicyRule
      description: Single evaluatable condition within a policy
      inherited_by: Policy Types section
    - name: PolicyContext
      description: Full evaluation context passed to every policy evaluation
      inherited_by: Policy Types section
    - name: PolicyDecision
      description: Result of evaluating a single policy against a context
      inherited_by: Policy Types section
    - name: PolicyTarget
      description: Specification of what a policy applies to
      inherited_by: Policy Types section
    - name: PolicyPrecedence
      description: Precedence level and override rules for a policy scope
      inherited_by: Policy Types section
    - name: PolicyState
      description: Lifecycle state of a policy
      inherited_by: Policy Types section

  events:
    - topic: policy.evaluated
      description: Emitted on every policy evaluation — allow or deny
      payload: {policy_name, context_summary, result, matched_rules, evaluated_at, duration_ms}
    - topic: policy.violated
      description: Emitted when enforcement=enforce and the result is deny
      payload: {policy_name, context_summary, matched_rules, enforcement, violation_id, timestamp}
    - topic: policy.updated
      description: Emitted when a policy is created, updated, deactivated, deprecated, or archived
      payload: {policy_name, action, previous_state, new_state, actor, reason, timestamp}
    - topic: policy.override
      description: Emitted when a lower-precedence policy attempts to override a higher one — always rejected
      payload: {attempting_policy, blocked_by, scope_level, reason, timestamp}
```

---

## Types

### PolicyDefinition

The complete policy document. This is the unit of policy management —
created, versioned, activated, evaluated, and archived as a single
entity.

```yaml
PolicyDefinition:
  name: string                    # Unique within scope (e.g., "rate-limit-agents")
  description: string             # Human-readable purpose
  scope: PolicyScope              # system | hub | namespace | agent
  target: PolicyTarget            # What this policy applies to
  rules: []PolicyRule             # Ordered conditions — ALL must pass for allow
  enforcement: EnforcementMode    # enforce | audit | escalate | disabled
  priority: integer               # Evaluation order within scope (lower = first, default: 100)
  activates_at_scope: ScopeLevel  # Minimum scope level to activate (default: public)
  active: boolean                 # Whether currently active (default: true)
  version: string                 # Semantic version (default: "1.0.0")
  state: PolicyState              # Lifecycle state (draft | active | deprecated | archived)
  created_at: integer             # Unix epoch seconds
  updated_at: integer             # Unix epoch seconds
  created_by: string              # Identity of the creator
  metadata: map                   # Optional key-value pairs for domain-specific extensions
```

### PolicyScope

Enumeration of precedence levels. Higher-precedence scopes override
lower ones. System policies are the most authoritative.

```yaml
PolicyScope:
  enum:
    - system      # Platform-wide, highest precedence
    - hub         # Hub-level, applies to all namespaces and agents in the hub
    - namespace   # Namespace-level, applies to all agents in the namespace
    - agent       # Agent-level, applies to a single agent only
```

### PolicyTarget

Specification of what a policy applies to. A policy can target
agents, operations, data, messages, or resources — or any combination.

```yaml
PolicyTarget:
  target_type: enum(agent, operation, data, message, resource, all)
  target_filter: string           # Pattern match — agent name, operation type, resource glob, or "*"
  target_scope: ScopeLevel        # Optional — only match targets at this scope level or above
```

### PolicyRule

A single evaluatable condition within a policy. Rules are evaluated
in order. ALL rules must pass for the policy to produce an `allow`
decision. If any rule fails, the policy produces a `deny`.

```yaml
PolicyRule:
  rule_type: RuleType             # Type of rule from the rule library
  params: map                     # Parameters specific to the rule type
  description: string             # Optional human-readable description
  negate: boolean                 # If true, inverts the rule result (default: false)
```

### PolicyContext

The full evaluation context passed to every policy evaluation. The
policy engine MUST populate all required fields before evaluation
begins. Missing required fields cause a fail-closed deny.

```yaml
PolicyContext:
  identity: IdentityContext       # Who is performing the operation
  scope_level: ScopeLevel         # Current scope classification (public → critical)
  environment: EnvironmentProfile # Active environment (development, staging, production)
  operation: OperationContext     # What operation is being performed
  resource: ResourceContext       # What resource is being accessed
  agent: AgentContext             # Which agent is involved
  timestamp: integer              # Unix epoch seconds — when the evaluation occurs
  hub_id: string                  # Hub context for hub/namespace-scoped policies
  namespace: string               # Namespace context for namespace/agent-scoped policies
```

**Sub-contexts:**

```yaml
IdentityContext:
  principal: string        # Agent name, user ID, or service account
  roles: []string          # Assigned roles
  capabilities: []string   # Declared capabilities from agent manifest
  token_claims: map        # Additional WLT token claims

OperationContext:
  type: string             # Classification: read, write, delete, execute, publish
  action: string           # Specific action name (e.g., "apply_changes")
  severity: string         # Operation severity: low, medium, high, critical

ResourceContext:
  type: string             # Resource type: file, url, api, database, message, stream
  path: string             # Resource path or identifier
  scope_level: ScopeLevel  # Resource's declared scope classification

AgentContext:
  name: string             # Agent name
  type: string             # Agent type: work, hub, meta, custom
  domain: string           # Domain the agent belongs to
  capabilities: []string   # Agent's declared capabilities
```

### PolicyDecision

Result of evaluating a single policy against a context. The decision
is one of four values, ordered by restrictiveness.

```yaml
PolicyDecision:
  result: enum(allow, audit, escalate, deny)   # Decision in order of restrictiveness
  policy_name: string             # Which policy produced this decision
  policy_scope: PolicyScope       # Precedence level of the policy
  matched_rules: []MatchedRule    # Which rules matched and their individual results
  enforcement: EnforcementMode    # The policy's enforcement mode
  evaluated_at: integer           # Unix epoch seconds
  duration_ms: integer            # Evaluation time in milliseconds
  context_summary: string         # Abbreviated context for logging

MatchedRule:
  rule_type: RuleType             # Rule that was evaluated
  result: boolean                 # Whether the rule passed (true) or failed (false)
  detail: string                  # Human-readable explanation of the result
```

### PolicyPrecedence

Defines how policy scopes relate to each other. Higher-rank scopes
are evaluated first and win ties. Lower scopes can only tighten.

```yaml
PolicyPrecedence:
  levels:
    - { scope: system,    rank: 1, override_allowed: false, desc: "Platform-wide — set by operators" }
    - { scope: hub,       rank: 2, override_allowed: false, desc: "Hub-wide — tightened by namespace" }
    - { scope: namespace, rank: 3, override_allowed: false, desc: "Namespace-wide — tightened by agent" }
    - { scope: agent,     rank: 4, override_allowed: false, desc: "Agent-specific — most granular" }
```

### EnforcementMode

How the policy engine acts on a decision.

```yaml
EnforcementMode:
  enum:
    - enforce     # Block the operation — return deny to caller
    - audit       # Log the decision but allow the operation to proceed
    - escalate    # Pause the operation and request approval from a higher authority
    - disabled    # Policy is loaded but not evaluated — useful for staged rollout
```

### PolicyState

Lifecycle state of a policy definition.

```yaml
PolicyState:
  enum:
    - draft       # Policy is defined but not yet active — not evaluated
    - active      # Policy is live and evaluated on every matching context
    - deprecated  # Policy is active but scheduled for removal — emits deprecation warnings
    - archived    # Policy is no longer evaluated — retained for audit history only
```

---

## Rule Types

The rule type library defines the evaluatable conditions available
in policies. Each rule type has a fixed set of parameters. Domains
can extend the library with `custom` rules, but all built-in rules
are available to every policy regardless of domain.

### Rule Type Reference

| Rule Type | Description | Parameters |
|-----------|-------------|------------|
| `scope_required` | Entity must be at or above a scope level | `min_level: ScopeLevel` |
| `scope_denied` | Entity must NOT be at or above a scope level | `max_level: ScopeLevel` |
| `capability_required` | Agent must have a declared capability | `capability: string` |
| `capability_denied` | Agent must NOT have a capability | `capability: string` |
| `resource_scope` | Restrict access to resource patterns | `allowed: []glob, denied: []glob` |
| `operation_type` | Restrict by operation classification | `allowed_operations: []string` |
| `rate_limit` | Maximum operations per time window | `max: integer, window_seconds: integer, key: string` |
| `time_window` | Restrict to specific time periods | `allowed_hours: []string, timezone: string` |
| `environment_match` | Only applies in specific environments | `environments: []string` |
| `identity_match` | Only applies to specific identities/roles | `roles: []string, agents: []string` |
| `approval_required` | Force approval for matching operations | `authority_level: string` |
| `custom` | Domain-defined rule with custom evaluator | `evaluator: string, params: map` |

### Rule Evaluation Semantics

Each rule type follows the same contract: receive context and params,
return PASS or FAIL. Rules that cannot be evaluated FAIL (fail-closed).

```yaml
rule_evaluation:
  scope_required:    "PASS if context.scope_level >= min_level"
  scope_denied:      "PASS if context.scope_level < max_level"
  capability_required: "PASS if capability in context.agent.capabilities"
  capability_denied: "PASS if capability not in context.agent.capabilities"
  resource_scope:    "PASS if path matches allowed[] AND not denied[]; denied takes precedence"
  operation_type:    "PASS if context.operation.type in allowed_operations[]"
  rate_limit:        "PASS if count(ops in window for key) < max"
  time_window:       "PASS if current time in timezone within any allowed_hours[] range"
  environment_match: "PASS if context.environment.environment_name in environments[]"
  identity_match:    "PASS if principal in agents[] OR any role in roles[]"
  approval_required: "Always produces ESCALATE; pauses until authority approves"
  custom:            "Delegates to registered evaluator; unregistered evaluator FAILS"
```

---

## Policy Precedence

Policies are evaluated in precedence order. System-level policies
are evaluated first and cannot be overridden. Each subsequent level
can only ADD restrictions — never remove them.

### Precedence Table

```
┌──────────────────────────────────────────────────────────────┐
│                    EVALUATION ORDER                          │
├──────────┬──────────┬────────────────────────────────────────┤
│ Priority │ Scope    │ Authority                              │
├──────────┼──────────┼────────────────────────────────────────┤
│ 1 (high) │ system   │ Platform operator — global rules       │
│ 2        │ hub      │ Hub administrator — hub-wide rules     │
│ 3        │ namespace│ Namespace owner — namespace rules      │
│ 4 (low)  │ agent    │ Agent operator — agent-specific rules  │
└──────────┴──────────┴────────────────────────────────────────┘
```

**Within the same scope level**, policies are evaluated by their
`priority` field (lower number = higher priority). If two policies
at the same scope have the same priority, they are evaluated in
alphabetical order by name (deterministic, reproducible).

### Override Rules

1. A lower-precedence policy CANNOT produce a more permissive
   decision than a higher-precedence policy already decided.
2. A lower-precedence policy CAN add additional restrictions.
3. If a system policy denies an operation, no hub/namespace/agent
   policy can allow it.
4. If a system policy allows an operation, a hub policy can still
   deny it.
5. Override attempts emit a `policy.override` event and are rejected.

---

## Policy Evaluation Algorithm

The evaluation algorithm is the core of the policy engine. It
receives a context, finds all matching policies, evaluates them in
precedence order, and returns a single composed decision.

### Algorithm (Pseudocode)

```
FUNCTION evaluate_policies(context: PolicyContext) -> PolicyDecision:

    # Step 1: Validate context — fail closed on missing required fields
    IF NOT validate_context(context):
        RETURN PolicyDecision{
            result: deny,
            policy_name: "_system_fail_closed",
            matched_rules: [],
            detail: "Invalid or incomplete context"
        }

    # Step 2: Load all active policies
    all_policies = load_active_policies()

    # Step 3: Filter to policies that match this context
    matching_policies = []
    FOR EACH policy IN all_policies:
        # Skip disabled policies
        IF policy.enforcement == disabled:
            CONTINUE

        # Skip policies that don't activate at this scope level
        IF context.scope_level < policy.activates_at_scope:
            CONTINUE

        # Skip policies whose target doesn't match the context
        IF NOT matches_target(policy.target, context):
            CONTINUE

        matching_policies.APPEND(policy)

    # Step 4: Sort by precedence (scope rank first, then priority, then name)
    matching_policies.SORT_BY(
        policy.scope.rank ASC,
        policy.priority ASC,
        policy.name ASC
    )

    # Step 5: Evaluate each policy and collect decisions
    decisions = []
    FOR EACH policy IN matching_policies:
        decision = evaluate_single_policy(policy, context)
        decisions.APPEND(decision)

        # Emit evaluation event
        EMIT event("policy.evaluated", {
            policy_name: policy.name,
            result: decision.result,
            context_summary: summarize(context),
            evaluated_at: now()
        })

    # Step 6: Compose decisions — most restrictive wins
    IF decisions IS EMPTY:
        # No matching policies — allow by default (opt-in model)
        RETURN PolicyDecision{result: allow, policy_name: "_default_allow"}

    final_decision = compose_decisions(decisions)

    # Step 7: Apply enforcement
    IF final_decision.result == deny AND final_decision.enforcement == enforce:
        EMIT event("policy.violated", {
            policy_name: final_decision.policy_name,
            context_summary: summarize(context),
            matched_rules: final_decision.matched_rules
        })

    RETURN final_decision


FUNCTION evaluate_single_policy(policy, context) -> PolicyDecision:
    FOR EACH rule IN policy.rules:
        result = evaluate_rule(rule, context)
        IF NOT result.passed:
            RETURN PolicyDecision{
                result: map_enforcement(policy.enforcement),
                policy_name: policy.name,
                matched_rules: collected_results
            }
    RETURN PolicyDecision{result: allow, policy_name: policy.name}


FUNCTION compose_decisions(decisions) -> PolicyDecision:
    # Restrictiveness: deny(4) > escalate(3) > audit(2) > allow(1)
    RETURN decision with highest restrictiveness rank


FUNCTION map_enforcement(enforcement) -> DecisionResult:
    enforce → deny | audit → audit | escalate → escalate | disabled → allow
```

---

## Policy Composition

When multiple policies target the same entity, the policy engine
composes their decisions. This section demonstrates how composition
works with concrete examples.

### Composition Rules

1. **All matching policies are evaluated** — even after a deny is
   found, remaining policies are still evaluated for audit completeness.
2. **Most restrictive wins** — the final decision is the single
   most restrictive decision from all evaluated policies.
3. **Decision hierarchy**: deny > escalate > audit > allow.
4. **Audit trail preserved** — the final decision includes references
   to all individual decisions that contributed to it.

### Composition Example

Three policies apply to the same agent performing a write in production:

```yaml
# Policy 1: System — rate limit all agents
policy_1: { name: global-rate-limit, scope: system, enforcement: enforce, priority: 10 }
  rules: [{ rule_type: rate_limit, params: { max: 1000, window_seconds: 3600, key: agent } }]

# Policy 2: Hub — restrict writes in production
policy_2: { name: production-write-guard, scope: hub, enforcement: escalate, priority: 50 }
  rules:
    - { rule_type: environment_match, params: { environments: [production] } }
    - { rule_type: approval_required, params: { authority_level: hub_admin } }

# Policy 3: Namespace — audit restricted data operations
policy_3: { name: restricted-data-audit, scope: namespace, enforcement: audit, priority: 100 }
  rules: [{ rule_type: scope_required, params: { min_level: restricted } }]
```

**Evaluation flow:**

```
Context: agent="seo-analyzer", operation=write, env=production, scope=restricted

1. global-rate-limit (system)  → rate_limit: 50 < 1000 → allow
2. production-write-guard (hub) → env_match: PASS → approval_required → escalate
3. restricted-data-audit (ns)   → scope_required: PASS → audit

Composition: escalate > audit > allow → ESCALATE (hub_admin approval required)
```

---

## Policy Lifecycle

Policies move through a defined lifecycle. State transitions are
validated — not all transitions are permitted.

### State Machine

```
                    ┌─────────┐
                    │  draft  │
                    └────┬────┘
                         │ activate
                         ▼
                    ┌─────────┐
              ┌────►│ active  │◄────┐
              │     └──┬───┬──┘     │
              │        │   │        │
              │  depr. │   │ deact. │ reactivate
              │        ▼   ▼        │
              │  ┌─────────────┐    │
              │  │ deprecated  │────┘
              │  └──────┬──────┘
              │         │ archive
              │         ▼
              │  ┌─────────────┐
              │  │  archived   │
              │  └─────────────┘
              │
              └── update (version bump, stays active)
```

### Permitted Transitions

| From | To | Action | Requirements |
|------|----|--------|-------------|
| draft | active | activate | All rules must validate; target must exist |
| active | active | update | Version bump required; new version re-validates |
| active | deprecated | deprecate | Reason required; deprecation warning emitted |
| active | archived | — | NOT permitted — must deprecate first |
| deprecated | active | reactivate | Re-validation required |
| deprecated | archived | archive | Reason required; policy becomes immutable |
| archived | — | — | Terminal state — no transitions permitted |

### Version Management

Every update to an active policy increments the version. The previous
version is retained for audit purposes. Version history is not
unlimited — implementations SHOULD retain at least the last 10
versions and MAY compress older versions into a summary record.

```yaml
version_history:
  - { version: "1.0.0", state: archived, change: "Initial creation" }
  - { version: "1.1.0", state: archived, change: "Added time_window rule" }
  - { version: "2.0.0", state: active, change: "Enforcement changed from audit to enforce" }
```

---

## Example Policies

### Rate Limiting an Agent

Prevent any single agent from exceeding 500 operations per minute.
Applied at system level — no agent can override this.

```yaml
policy:
  name: agent-operation-rate-limit
  description: >
    Prevent any single agent from exceeding 500 operations per
    minute. Protects platform stability and prevents runaway agents.
  scope: system
  target:
    target_type: agent
    target_filter: "*"
  rules:
    - rule_type: rate_limit
      params:
        max: 500
        window_seconds: 60
        key: agent
      description: Max 500 operations per minute per agent
  enforcement: enforce
  priority: 1
  activates_at_scope: public
  active: true
  version: "1.0.0"
  state: active
```

### Requiring Approval for Destructive Operations in Production

Any delete or execute operation in a production environment on
confidential-or-higher data requires hub administrator approval.

```yaml
policy:
  name: production-destructive-approval
  description: >
    Destructive operations (delete, execute) on confidential-or-higher
    data in production require hub administrator approval.
  scope: hub
  target:
    target_type: operation
    target_filter: "*"
  rules:
    - rule_type: environment_match
      params:
        environments: [production]
      description: Only applies in production
    - rule_type: operation_type
      params:
        allowed_operations: [delete, execute]
      negate: true
      description: Matches delete and execute operations (negated — blocks them)
    - rule_type: scope_required
      params:
        min_level: confidential
      description: Only applies to confidential-or-higher data
    - rule_type: approval_required
      params:
        authority_level: hub_admin
      description: Requires hub admin approval
  enforcement: escalate
  priority: 10
  activates_at_scope: confidential
  active: true
  version: "1.0.0"
  state: active
```

### Restricting Scope Access by Agent Type

Work agents cannot access critical-scope data. Only meta agents
with explicit `critical_access` capability are permitted.

```yaml
policy:
  name: critical-scope-restriction
  description: >
    Only agents with the critical_access capability may access
    critical-scope data. All other agents are denied.
  scope: system
  target:
    target_type: data
    target_filter: "*"
  rules:
    - rule_type: scope_required
      params:
        min_level: critical
      description: Only activates for critical-scope data
    - rule_type: capability_required
      params:
        capability: critical_access
      description: Agent must have critical_access capability
  enforcement: enforce
  priority: 5
  activates_at_scope: critical
  active: true
  version: "1.0.0"
  state: active
```

### Business Hours Only for Content Modifications

Content domain agents can only modify content during business hours.
Outside business hours, operations are audited but not blocked.

```yaml
policy:
  name: content-business-hours
  description: >
    Content modifications restricted to business hours (09:00-18:00
    UTC). Outside this window, operations are audited, not blocked.
  scope: namespace
  target:
    target_type: agent
    target_filter: "content-*"
  rules:
    - rule_type: time_window
      params:
        allowed_hours: ["09:00-18:00"]
        timezone: "UTC"
  enforcement: audit
  priority: 50
  activates_at_scope: internal
  active: true
  version: "1.0.0"
  state: active
```

### Namespace-Level Resource Boundary

Agents in the `seo` namespace can only access files under their
domain root. System directories are always denied.

```yaml
policy:
  name: seo-resource-boundary
  description: >
    SEO agents restricted to domain directory. System directories
    always denied.
  scope: namespace
  target:
    target_type: resource
    target_filter: "*"
  rules:
    - rule_type: resource_scope
      params:
        allowed: ["$domain_root/**"]
        denied: [".weblisk/**", "config/**", "secrets/**"]
  enforcement: enforce
  priority: 20
  activates_at_scope: public
  active: true
  version: "1.0.0"
  state: active
```

---

## Integration Points

### Scope (`patterns/scope`)

The policy engine reads scope classifications from `patterns/scope`.
Scope determines which policies activate (`activates_at_scope`),
which targets match (`target_scope`), and which rules evaluate
(`scope_required`, `scope_denied`). Policies consume scope — they
never modify it. Scope classification is a separate concern.

### Governance (`patterns/governance`)

`patterns/governance` consumes the policy engine for compliance
profiles (which policies must be active), evidence collection
(`policy.evaluated` and `policy.violated` events), audit reporting,
and capability enforcement. The policy engine provides the rules.
Governance provides the compliance layer on top.

### Domain Extension

Any domain can extend the policy engine by registering custom rule
types via the `custom` rule, defining domain-specific policies at
namespace or agent scope, and consuming policy decisions in domain
workflows. Domains do NOT modify the evaluation algorithm or
composition rules.

---

## Conformance

### MUST

- Policy definitions MUST be valid YAML conforming to PolicyDefinition.
- Evaluation MUST be fail-closed — missing context, errors, and timeouts produce deny.
- Multiple policies on the same target MUST compose using most-restrictive-wins.
- Lower-precedence policies MUST NOT override higher-precedence decisions.
- Every evaluation MUST emit a `policy.evaluated` event.
- `enforce` MUST block on deny; `audit` MUST log but allow; `escalate` MUST pause and request approval.
- Lifecycle transitions MUST follow the permitted transition table.
- Archived policies MUST be immutable.

### SHOULD

- Evaluate all matching policies even after a deny, for audit completeness.
- Retain at least 10 versions of policy history for audit.
- Support sub-second evaluation for fewer than 50 matching policies.
- `policy.violated` events SHOULD include sufficient context for operators.

### MAY

- Cache evaluation results for identical contexts (recommended TTL: 30s max).
- Extend the rule library with domain-specific rules via `custom`.
- Implement evaluation as a separate service or in-process library.
- Add custom metadata fields to PolicyDefinition for domain extensions.

---

## Error Handling

| Code | HTTP | Description |
|------|------|-------------|
| `POLICY_EVAL_FAILED` | 500 | Policy evaluation failed due to internal error |
| `POLICY_CONTEXT_INCOMPLETE` | 400 | Required context fields missing for evaluation |
| `POLICY_INVALID_DEFINITION` | 422 | Policy YAML does not conform to PolicyDefinition schema |
| `POLICY_NOT_FOUND` | 404 | Referenced policy name does not exist |
| `POLICY_DENIED` | 403 | Operation denied by policy evaluation (enforcement = enforce) |
| `POLICY_ESCALATED` | 202 | Operation paused pending approval (enforcement = escalate) |
| `POLICY_LIFECYCLE_INVALID` | 409 | Invalid lifecycle state transition attempted |
| `POLICY_CONFLICT` | 409 | Policy conflicts with existing active policy on same target |

All error responses follow the standard `ErrorResponse` format from
`protocol/types`.

---

## Implementation Notes

- Policy evaluation MUST complete in bounded time. Set a hard timeout
  (recommended: 100ms per policy, 500ms total per evaluation). On
  timeout, fail-closed with deny.
- Cache evaluation results keyed on `{policy_version, context_hash}`.
  Recommended TTL: 30 seconds. Invalidate on `policy.updated` events.
- Store policies in the agent's local storage using the standard
  storage pattern. Index by `scope`, `target`, and `state` for
  fast lookup during evaluation.
- Custom rules (`rule: custom`) MUST be sandboxed. They receive a
  read-only context and return a boolean. They MUST NOT perform I/O,
  modify state, or access resources outside the context.
- Policy hot-reload: active policies can be updated via governance
  directives (patterns/governance) without agent restart. The agent
  re-evaluates its policy cache on `policy_update` directive receipt.
- Version history: retain at least 10 previous versions of each
  policy for audit rollback. Older versions can be archived to
  cold storage.
- The `most-restrictive-wins` composition rule means: if ANY matching
  policy denies, the final decision is deny — regardless of other
  policies that allow. This is defense-in-depth by design.
- Policy precedence rank (system=0, hub=1, namespace=2, agent=3)
  determines evaluation order but NOT override power. A
  namespace-scoped policy cannot allow what a system-scoped policy
  denies.
- For environments with high policy counts (>100 active), consider
  pre-computing a policy decision tree at policy update time rather
  than evaluating all policies per request.

---

## Verification Checklist

- [ ] PolicyDefinition schema validates all required fields (name, description, scope, target, rules, enforcement, state)
- [ ] Evaluation is fail-closed — missing context, errors, and timeouts produce deny
- [ ] Multiple policies on the same target compose using most-restrictive-wins
- [ ] Lower-precedence policies do not override higher-precedence decisions
- [ ] Every evaluation emits a `policy.evaluated` event with full context
- [ ] `enforce` blocks on deny; `audit` logs but allows; `escalate` pauses and requests approval
- [ ] Lifecycle transitions follow the permitted transition table (draft→active→deprecated→archived)
- [ ] Archived policies are immutable — updates are rejected with POLICY_LIFECYCLE_INVALID
- [ ] Custom rules execute in a sandbox with read-only context and no I/O
- [ ] Policy cache invalidates on `policy.updated` events
- [ ] Evaluation completes within the configured timeout (default 500ms total)
- [ ] Error responses use standard ErrorResponse format with appropriate POLICY_* codes
- [ ] Policy version history retains at least 10 previous versions
- [ ] All 12 rule types evaluate correctly against their documented parameters
- [ ] Policy YAML that does not conform to PolicyDefinition schema is rejected with POLICY_INVALID_DEFINITION
