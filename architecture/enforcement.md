<!-- blueprint
type: architecture
name: enforcement
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/scope, patterns/policy, patterns/safety, architecture/orchestrator, architecture/gateway]
platform: any
tier: free
-->

# Enforcement Architecture

The platform-level sentinel that intercepts operations at system
boundaries and evaluates them against policies before execution. The
enforcement layer is non-bypassable — it sits between agents and the
resources they consume. An agent cannot reach the message bus, storage
layer, or external services without passing through enforcement.

Unlike patterns (which agents extend and opt into), the enforcement
layer is ALWAYS ACTIVE. It is not a policy engine — that belongs to
`patterns/policy`. It is not a safety classifier — that belongs to
`patterns/safety`. It is the **structural mechanism** that ensures
those patterns are actually applied, regardless of whether agents
cooperate. Agents that declare honest intents benefit from fast-path
evaluation. Agents that lie, misbehave, or drift are detected and
quarantined.

---

## Overview

The Weblisk architecture has a structural gap: patterns define rules,
but nothing forces agents to consult them. The orchestrator dispatches
— it knows what agents are available, but not what they are doing. The
gateway handles HTTP routing for end users. Neither sits in the path
between agents and their operational resources.

The enforcement layer closes this gap. It operates at three boundaries
where agents interact with the rest of the system:

1. **Message boundary** — every message between agents passes through
   enforcement before delivery. An agent cannot send a message to
   another agent without enforcement evaluating the operation against
   policies, scope, and safety constraints.

2. **Storage boundary** — every storage operation (read, write,
   delete) passes through enforcement before execution. An agent
   cannot touch its data store without enforcement verifying that
   the operation matches the agent's declared capabilities and the
   resource's scope classification.

3. **External boundary** — every outbound call to external services
   (HTTP, SMTP, webhooks, APIs) passes through enforcement before
   dispatch. An agent cannot reach the outside world without
   enforcement checking the target, the payload scope, and the
   agent's declared external capabilities.

Enforcement does not define policies, classify scopes, or determine
safety intents. It consumes those patterns and applies them
structurally. It is the difference between "here are the rules" and
"the rules are enforced."

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, capabilities, publishes, subscriptions]
        - name: AgentMessage
          fields_used: [from, to, action, payload, signature, metadata]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target, detail, status]
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
        - name: OperationIntent
          fields_used: [agent, operation_type, target, scope, environment, justification]
        - name: ProtectionGate
          fields_used: [decision, required_authority, escalation_path]
        - name: QuarantineOrder
          fields_used: [agent_name, reason, severity, issued_by, correlation_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ServiceDirectory
          fields_used: [agents, routing_table, namespaces]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [tls, internal_headers]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    Agents                        │
│  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ Agent A │  │ Agent B │  │ Agent C │            │
│  └───┬─┬──┘  └──┬──┬──┘  └──┬──┬──┘            │
│      │ │        │  │        │  │                 │
│  ════╪═╪════════╪══╪════════╪══╪═══════════════  │
│  ║   ENFORCEMENT LAYER (always active)        ║  │
│  ║  ┌──────────┐ ┌───────────┐ ┌────────────┐║  │
│  ║  │ Message  │ │  Storage  │ │  External  │║  │
│  ║  │ Boundary │ │  Boundary │ │  Boundary  │║  │
│  ║  └────┬─────┘ └─────┬─────┘ └─────┬──────┘║  │
│  ║       │              │              │       ║  │
│  ║  ┌────┴──────────────┴──────────────┴────┐ ║  │
│  ║  │         Inspection Engine             │ ║  │
│  ║  │  ┌─────────┐ ┌──────────┐ ┌────────┐ │ ║  │
│  ║  │  │ Policy  │ │ Behavior │ │ Audit  │ │ ║  │
│  ║  │  │Evaluator│ │ Analyzer │ │ Writer │ │ ║  │
│  ║  │  └─────────┘ └──────────┘ └────────┘ │ ║  │
│  ║  └───────────────────────────────────────┘ ║  │
│  ║       │              │              │       ║  │
│  ║  ┌────┴────┐  ┌──────┴────┐  ┌─────┴─────┐║  │
│  ║  │Quarantin│  │ Decision  │  │ Violation │║  │
│  ║  │  Store  │  │   Cache   │  │   Queue   │║  │
│  ║  └─────────┘  └───────────┘  └───────────┘║  │
│  ═════════════════════════════════════════════   │
│      │ │        │  │        │  │                 │
│  ┌───┴─┴──┐  ┌──┴──┴──┐  ┌──┴──┴──┐            │
│  │Messages│  │Storage │  │External│              │
│  │ Bus    │  │ Layer  │  │Services│              │
│  └────────┘  └────────┘  └────────┘              │
└─────────────────────────────────────────────────┘
```

### Sub-Components

**Message Boundary** — Intercepts every agent-to-agent message before
it reaches the message bus. Extracts the sender identity, recipient,
action type, and payload scope from the message envelope. Passes the
extracted context to the inspection engine for evaluation. If the
inspection engine returns `allow`, the message is forwarded to the
bus. If it returns `deny`, the message is dropped and a violation is
emitted. If it returns `require_approval`, the message is held pending
approval via `patterns/approval`.

**Storage Boundary** — Intercepts every storage operation before it
reaches the storage layer. Extracts the agent identity, operation type
(read, write, delete), target resource path, and resource scope
classification. Passes the extracted context to the inspection engine.
Enforces that the agent's declared capabilities include the operation
type and that the resource scope does not exceed the agent's
operational scope.

**External Boundary** — Intercepts every outbound call before it
leaves the platform. Extracts the agent identity, target URL/service,
protocol (HTTP, SMTP, webhook), and payload scope. Verifies that the
agent has declared the external capability and that the target is not
on a blocked list. Evaluates payload scope to prevent scope leakage
— restricted-scope data cannot be sent to unclassified external
endpoints.

**Inspection Engine** — The shared evaluation core used by all three
boundaries. Receives the intercepted operation context, builds a
`PolicyContext` from the extracted metadata, evaluates all matching
policies via `patterns/policy`, checks safety intent requirements via
`patterns/safety`, resolves the effective scope via `patterns/scope`,
and returns a single decision: `allow`, `require_approval`, `deny`,
or `quarantine`. The inspection engine also feeds behavioral signals
to the behavior analyzer.

**Policy Evaluator** — Delegates to the policy engine defined in
`patterns/policy`. Loads all active policies that match the operation
context, evaluates them in precedence order, and composes the results
using the most-restrictive-wins rule. The enforcement layer does not
define policies — it calls the engine that does.

**Behavior Analyzer** — Accumulates behavioral signals from all
intercepted operations and detects anomalies that indicate rogue
agent behavior. Operates on rolling windows and historical baselines.
Does not block operations directly — it raises detection events that
the inspection engine consumes on subsequent evaluations.

**Audit Writer** — Records every enforcement decision in the
append-only audit log. Every decision includes: correlation ID, agent
identity, operation type, target, scope level, policies evaluated,
decision result, and timestamp. Blocked operations additionally
include the specific policy that triggered the block.

**Quarantine Store** — Maintains the list of currently quarantined
agents. When an agent is quarantined, its entry is added to this
store. All three boundaries check the quarantine store before
evaluating policies — quarantined agents are blocked immediately
without policy evaluation. The quarantine store is persistent across
enforcement layer restarts.

**Decision Cache** — Short-lived cache of recent enforcement
decisions for identical operation signatures. Reduces policy
evaluation overhead for repeated identical operations (e.g., an agent
reading the same resource in a tight loop). Cache entries are
invalidated on policy change, scope change, or quarantine state
change. Cache TTL is configurable but defaults to 5 seconds.

**Violation Queue** — Buffered queue of enforcement violations
waiting for processing. Violations are emitted asynchronously to
avoid blocking the enforcement decision path. Consumers include the
behavior analyzer, the audit writer, operator notification channels,
and the alerting agent.

---

## Responsibilities

### Owns

- **Policy evaluation at boundaries** — Intercepting operations at
  message, storage, and external boundaries and evaluating them
  against the policy engine before allowing execution
- **Rogue agent detection** — Behavioral analysis across all
  intercepted operations to detect capability mismatch, scope
  violation, volume anomaly, and pattern deviation
- **Quarantine enforcement** — Blocking all communication to and from
  quarantined agents across all three boundaries, preserving agent
  state for investigation
- **Enforcement decision audit trail** — Recording every enforcement
  decision with full context, traceable via correlation ID
- **Kill-switch execution** — When the kill-switch is triggered via
  `patterns/safety`, the enforcement layer executes it by blocking
  all operations for the targeted agent across all boundaries
- **Decision caching** — Short-lived caching of enforcement decisions
  to reduce repeated policy evaluation for identical operations
- **Violation emission** — Producing structured violation events for
  every blocked or quarantined operation

### Does NOT Own

- **Policy definition** — Owned by `patterns/policy`. The enforcement
  layer evaluates policies; it does not create, modify, or manage
  them.
- **Scope classification** — Owned by `patterns/scope`. The
  enforcement layer reads scope levels from resource metadata and
  message envelopes; it does not assign them.
- **Operation intent declaration** — Owned by `patterns/safety`.
  Agents declare intents via the safety pattern; enforcement checks
  whether intents exist and match observed behavior.
- **Approval routing** — Owned by `patterns/approval`. When
  enforcement returns `require_approval`, it defers to the approval
  pattern for routing, decision, and escalation.
- **Transport security** — Owned by `architecture/data-security`.
  TLS, message signing, and federation boundary encryption are
  transport concerns, not enforcement concerns.
- **Agent registration** — Owned by `architecture/orchestrator`.
  Enforcement reads the service directory to resolve agent manifests;
  it does not manage registration.
- **HTTP routing** — Owned by `architecture/gateway`. The gateway
  routes end-user HTTP requests; enforcement operates on agent-level
  operations at system boundaries.
- **Storage engine implementation** — Enforcement wraps the storage
  interface with a proxy; it does not implement storage itself.

---

## Interfaces

### Message Interception

Wraps the existing messaging protocol. Every message routed between
agents passes through this interface before reaching the message bus.

```yaml
message_interception:
  intercept_message:
    description: Intercept an agent-to-agent message before delivery
    input:
      message: AgentMessage        # Full message with envelope metadata
      routing_context:
        sender_manifest: AgentManifest
        recipient_manifest: AgentManifest
        channel_id: string         # From orchestrator channel grant
    output:
      decision: enum(allow, require_approval, deny, quarantine)
      correlation_id: string
      violation: ViolationRecord | null
      approval_request: ApprovalContext | null  # Populated when decision is require_approval
    behavior:
      - Extract sender identity, action, payload scope from message
      - Check quarantine store — if sender or recipient quarantined → deny
      - Build PolicyContext from message metadata and manifests
      - Evaluate policies via patterns/policy
      - Check safety intent — if required but missing → deny + violation
      - Verify sender has declared capability for the action type
      - Feed behavioral signals to behavior analyzer
      - Log decision to audit writer
      - Return decision
    errors:
      - code: ENFORCEMENT_QUARANTINED
        when: Sender or recipient is in quarantine store
      - code: ENFORCEMENT_POLICY_DENY
        when: Policy evaluation returns deny
      - code: ENFORCEMENT_MISSING_INTENT
        when: Safety intent is required but not declared
      - code: ENFORCEMENT_CAPABILITY_MISMATCH
        when: Agent attempts action not in declared capabilities
```

### Storage Proxy

Wraps the existing storage interface. Every storage operation issued
by an agent passes through this proxy before reaching the storage
layer.

```yaml
storage_proxy:
  intercept_storage:
    description: Intercept a storage operation before execution
    input:
      agent: AgentManifest         # Agent issuing the operation
      operation:
        type: enum(read, write, delete, list, query)
        resource_path: string      # Storage path or key
        resource_scope: ScopeLevel # Scope classification of the target resource
        payload_size: integer      # Bytes (for volume tracking)
    output:
      decision: enum(allow, require_approval, deny, quarantine)
      correlation_id: string
      violation: ViolationRecord | null
    behavior:
      - Check quarantine store — if agent quarantined → deny
      - Resolve resource scope from resource metadata
      - Build PolicyContext from agent manifest, operation, resource scope
      - Evaluate policies via patterns/policy
      - Verify agent capabilities include the operation type
      - Verify resource scope does not exceed agent operational scope
      - For write/delete: check safety intent requirement
      - Feed behavioral signals to behavior analyzer
      - Log decision to audit writer
      - Return decision
    errors:
      - code: ENFORCEMENT_QUARANTINED
        when: Agent is in quarantine store
      - code: ENFORCEMENT_SCOPE_VIOLATION
        when: Resource scope exceeds agent operational scope
      - code: ENFORCEMENT_POLICY_DENY
        when: Policy evaluation returns deny
      - code: ENFORCEMENT_CAPABILITY_MISMATCH
        when: Agent lacks declared capability for operation type
```

### External Proxy

Wraps outbound HTTP, SMTP, webhook, and other external service calls.
Every outbound request from an agent passes through this proxy before
leaving the platform.

```yaml
external_proxy:
  intercept_external:
    description: Intercept an outbound call before dispatch
    input:
      agent: AgentManifest         # Agent making the outbound call
      request:
        protocol: enum(http, https, smtp, webhook, grpc)
        target: string             # URL, email address, or endpoint
        method: string             # GET, POST, SEND, etc.
        payload_scope: ScopeLevel  # Highest scope in outbound payload
        payload_size: integer      # Bytes
    output:
      decision: enum(allow, require_approval, deny, quarantine)
      correlation_id: string
      violation: ViolationRecord | null
    behavior:
      - Check quarantine store — if agent quarantined → deny
      - Verify agent has declared external capability for the protocol
      - Check target against blocked endpoint list
      - Evaluate payload scope — restricted+ data to unclassified endpoints → deny
      - Build PolicyContext from agent, target, scope
      - Evaluate policies via patterns/policy
      - Feed behavioral signals to behavior analyzer
      - Log decision to audit writer
      - Return decision
    errors:
      - code: ENFORCEMENT_QUARANTINED
        when: Agent is in quarantine store
      - code: ENFORCEMENT_BLOCKED_TARGET
        when: Target is on the blocked endpoint list
      - code: ENFORCEMENT_SCOPE_LEAKAGE
        when: Payload scope exceeds target endpoint classification
      - code: ENFORCEMENT_CAPABILITY_MISMATCH
        when: Agent lacks declared external capability
```

### Quarantine API

Manages the lifecycle of agent quarantine — enter, exit, list, and
inspect quarantined agents.

```yaml
quarantine_api:
  enter_quarantine:
    description: Place an agent into quarantine
    input:
      order: QuarantineOrder       # From patterns/safety or rogue detection
    output:
      quarantine_id: string
      effective_at: timestamp
      blocked_boundaries: [message, storage, external]
    behavior:
      - Validate quarantine order (agent exists, reason provided)
      - Add agent to quarantine store with timestamp and reason
      - All three boundaries immediately begin blocking the agent
      - Preserve agent state snapshot for investigation
      - Emit quarantine.entered event to system namespace
      - Notify operators via alerting channels
      - Log to audit writer

  exit_quarantine:
    description: Release an agent from quarantine
    input:
      quarantine_id: string
      released_by: string          # Operator or admin identity
      reason: string               # Justification for release
    output:
      released_at: timestamp
    behavior:
      - Validate release authority (admin or higher required)
      - Remove agent from quarantine store
      - All three boundaries immediately resume normal evaluation
      - Emit quarantine.exited event to system namespace
      - Log to audit writer with release justification

  list_quarantined:
    description: List all currently quarantined agents
    input:
      filter:
        severity: enum(low, medium, high, critical) | null
        since: timestamp | null
    output:
      agents:
        - agent_name: string
          quarantine_id: string
          reason: string
          severity: enum(low, medium, high, critical)
          entered_at: timestamp
          blocked_boundaries: [message, storage, external]
          violation_count: integer
```

### Enforcement Report API

Query enforcement decisions, violations, and rogue agent detections.

```yaml
enforcement_report:
  query_decisions:
    description: Query enforcement decisions by agent, time range, or decision type
    input:
      filter:
        agent_name: string | null
        boundary: enum(message, storage, external) | null
        decision: enum(allow, require_approval, deny, quarantine) | null
        since: timestamp
        until: timestamp
        correlation_id: string | null
    output:
      decisions:
        - correlation_id: string
          timestamp: timestamp
          agent: string
          boundary: enum(message, storage, external)
          operation_type: string
          target: string
          scope_level: ScopeLevel
          decision: enum(allow, require_approval, deny, quarantine)
          policies_evaluated: []string
          triggering_policy: string | null
      total_count: integer

  query_violations:
    description: Query enforcement violations by type, severity, or agent
    input:
      filter:
        agent_name: string | null
        violation_type: enum(capability_mismatch, scope_violation, volume_anomaly, pattern_deviation, missing_intent, scope_leakage, blocked_target) | null
        severity: enum(low, medium, high, critical) | null
        since: timestamp
        until: timestamp
    output:
      violations:
        - violation_id: string
          correlation_id: string
          timestamp: timestamp
          agent: string
          violation_type: string
          severity: enum(low, medium, high, critical)
          detail: string
          triggering_policy: string
          action_taken: enum(audit, block, quarantine)
      total_count: integer

  query_rogue_detections:
    description: Query rogue agent detection events
    input:
      filter:
        agent_name: string | null
        detection_type: enum(capability_mismatch, scope_violation, volume_anomaly, pattern_deviation) | null
        since: timestamp
        until: timestamp
    output:
      detections:
        - detection_id: string
          timestamp: timestamp
          agent: string
          detection_type: string
          evidence: string
          action_taken: enum(audit_alert, quarantine)
          resolved: boolean
      total_count: integer
```

---

## Data Flow

### 1. Message Flow

```
Agent A sends message to Agent B
  │
  ▼
Message Boundary intercepts
  │
  ├─ Check quarantine store for Agent A and Agent B
  │  └─ If quarantined → DENY (skip all further evaluation)
  │
  ├─ Extract: sender, recipient, action, payload scope
  │
  ├─ Resolve Agent A manifest from service directory
  │
  ├─ Verify Agent A has capability for declared action
  │  └─ If missing → DENY + capability_mismatch violation
  │
  ├─ Build PolicyContext:
  │    identity: Agent A
  │    scope_level: max(payload scope, recipient scope)
  │    environment: current environment profile
  │    operation: message.send
  │    resource: Agent B namespace
  │    agent: Agent A manifest
  │
  ├─ Evaluate policies (patterns/policy)
  │  ├─ allow → forward message to bus
  │  ├─ require_approval → hold, defer to patterns/approval
  │  ├─ deny → drop message + emit violation
  │  └─ quarantine → enter_quarantine + drop message
  │
  ├─ Feed signals to behavior analyzer:
  │    [action_type, target, scope, timestamp, payload_size]
  │
  └─ Log decision to audit writer
```

### 2. Storage Flow

```
Agent issues storage operation (write to /data/reports/q4)
  │
  ▼
Storage Boundary intercepts
  │
  ├─ Check quarantine store for agent
  │  └─ If quarantined → DENY
  │
  ├─ Extract: agent, operation type (write), resource path, payload size
  │
  ├─ Resolve resource scope from storage metadata
  │    /data/reports/q4 → scope: confidential
  │
  ├─ Resolve agent operational scope from manifest
  │    Agent declared scope: internal
  │
  ├─ Compare: confidential > internal → SCOPE VIOLATION
  │  └─ DENY + scope_violation event + escalate
  │
  │  (If scope check passes:)
  │
  ├─ Verify agent capability includes "storage:write"
  │  └─ If missing → DENY + capability_mismatch violation
  │
  ├─ Check safety intent for write operations:
  │  └─ If intent required but not declared → DENY + missing_intent violation
  │
  ├─ Build PolicyContext and evaluate policies
  │  ├─ allow → execute storage operation
  │  ├─ require_approval → hold pending approval
  │  └─ deny → reject operation + emit violation
  │
  ├─ Feed signals to behavior analyzer
  │
  └─ Log decision to audit writer
```

### 3. External Flow

```
Agent makes outbound HTTP POST to https://api.example.com/webhook
  │
  ▼
External Boundary intercepts
  │
  ├─ Check quarantine store for agent
  │  └─ If quarantined → DENY
  │
  ├─ Extract: agent, protocol (https), target URL, method (POST),
  │           payload scope (restricted), payload size
  │
  ├─ Verify agent has declared "external:http" capability
  │  └─ If missing → DENY + capability_mismatch violation
  │
  ├─ Check target against blocked endpoint list
  │  └─ If blocked → DENY + blocked_target violation
  │
  ├─ Evaluate scope leakage:
  │    Payload scope: restricted
  │    Target classification: unclassified (external)
  │  └─ restricted → unclassified = SCOPE LEAKAGE → DENY
  │
  │  (If scope check passes:)
  │
  ├─ Build PolicyContext and evaluate policies
  │  ├─ allow → forward request to external service
  │  ├─ require_approval → hold pending approval
  │  └─ deny → reject request + emit violation
  │
  ├─ Feed signals to behavior analyzer
  │
  └─ Log decision to audit writer
```

### 4. Rogue Detection Flow

```
Behavior Analyzer receives signals continuously from all boundaries
  │
  ▼
Accumulate signals per agent in rolling windows
  │
  ├─ Capability Mismatch Detection:
  │    Agent declares: [storage:read, message:send]
  │    Agent attempts: storage:write
  │  └─ IMMEDIATE violation → block + escalate
  │
  ├─ Scope Violation Detection:
  │    Agent operational scope: internal
  │    Agent accesses: restricted resource
  │  └─ IMMEDIATE violation → block + escalate
  │
  ├─ Volume Anomaly Detection:
  │    Rolling average (1h window): 50 ops/min
  │    Current rate: 600 ops/min (12x average)
  │  └─ If > 10x → audit alert
  │  └─ If sustained > 5 minutes → quarantine
  │
  ├─ Pattern Deviation Detection:
  │    Historical baseline: 90% reads, 10% writes
  │    Current window: 20% reads, 80% writes
  │  └─ If deviation > 3 standard deviations → audit alert
  │  └─ If sustained > 10 minutes → escalate to operator
  │
  └─ On quarantine trigger:
       Issue QuarantineOrder via patterns/safety
       Execute via quarantine_api.enter_quarantine
```

---

## Inspection Protocol

For every intercepted operation at any boundary, the enforcement
layer follows a fixed evaluation sequence. This sequence is not
configurable — it is the structural guarantee that enforcement
provides.

### Evaluation Sequence

```
1. QUARANTINE CHECK
   - Is the agent in the quarantine store?
   - Yes → DENY immediately. No policy evaluation. Log and return.
   - No → proceed.

2. IDENTITY RESOLUTION
   - Resolve the agent's manifest from the service directory
   - Extract: agent name, type, capabilities, declared scope
   - If manifest not found → DENY (unregistered agent)

3. CAPABILITY VERIFICATION
   - Extract the operation type from the intercepted request
   - Verify the operation type exists in the agent's declared capabilities
   - If missing → DENY + emit capability_mismatch violation

4. SCOPE RESOLUTION
   - Resolve the effective scope of the operation:
     - Message boundary: max(payload scope, recipient scope)
     - Storage boundary: resource scope from storage metadata
     - External boundary: payload scope
   - Compare against agent's operational scope
   - If resource scope > agent scope → DENY + emit scope_violation

5. SAFETY INTENT CHECK
   - Determine if the operation requires a safety intent
     (based on operation type and scope — from patterns/safety)
   - If required: check that the agent has filed an OperationIntent
     matching this operation
   - If intent missing → DENY + emit missing_intent violation
   - If intent present but mismatched → DENY + emit intent_mismatch violation

6. POLICY EVALUATION
   - Build PolicyContext from resolved metadata:
     identity, scope_level, environment, operation, resource, agent
   - Evaluate all matching policies via patterns/policy
   - Compose results using most-restrictive-wins
   - Result: allow, require_approval, deny, or escalate

7. DECISION MAPPING
   - allow → forward operation to target (bus, storage, external)
   - require_approval → hold operation, create ApprovalContext,
     defer to patterns/approval
   - deny → drop operation, emit violation with triggering policy
   - escalate → treat as require_approval with elevated authority
   - quarantine → execute quarantine_api.enter_quarantine, drop operation

8. BEHAVIORAL SIGNAL EMISSION
   - Regardless of decision, emit behavioral signal to analyzer:
     [agent, boundary, operation_type, target, scope, decision,
      timestamp, payload_size]

9. AUDIT LOGGING
   - Record complete decision context to audit writer:
     [correlation_id, agent, boundary, operation_type, target,
      scope_level, policies_evaluated, decision, triggering_policy,
      timestamp]
```

### Decision Priority

When multiple signals contribute to a decision, the most restrictive
wins:

```
quarantine > deny > require_approval > allow
```

If any check in the sequence produces a more restrictive result than
the current decision, the more restrictive result replaces it. A
`deny` from capability verification is not overridden by an `allow`
from policy evaluation.

---

## Rogue Agent Detection

The behavior analyzer operates continuously, consuming signals from
all three boundaries. It maintains per-agent behavioral profiles and
detects deviations that indicate malicious, compromised, or
malfunctioning agents.

### Behavioral Signals

Every intercepted operation produces a signal:

```yaml
behavioral_signal:
  agent: string                  # Agent identity
  boundary: enum(message, storage, external)
  operation_type: string         # read, write, delete, send, etc.
  target: string                 # Recipient, resource path, or URL
  scope_level: ScopeLevel        # Resolved scope
  decision: enum(allow, deny, require_approval, quarantine)
  timestamp: timestamp
  payload_size: integer          # Bytes
```

### Detection Rules

**capability_mismatch** — Agent attempts an operation not in its
declared capabilities.

```yaml
capability_mismatch:
  trigger: agent attempts operation_type not in manifest.capabilities
  severity: high
  action: immediate_violation
  response: block operation + emit violation + escalate to operator
  threshold: single occurrence (zero tolerance)
```

**scope_violation** — Agent accesses a resource above its operational
scope.

```yaml
scope_violation:
  trigger: resource scope > agent operational scope
  severity: high
  action: immediate_violation
  response: block operation + emit violation + escalate to operator
  threshold: single occurrence (zero tolerance)
```

**volume_anomaly** — Agent operation rate exceeds normal volume.

```yaml
volume_anomaly:
  trigger: operation rate > 10x rolling average (1-hour window)
  severity: medium → high (if sustained)
  action: graduated_response
  response:
    - stage_1: rate > 10x average → audit alert
    - stage_2: sustained > 5 minutes → quarantine
  threshold:
    window: 1 hour rolling
    multiplier: 10x
    sustain_period: 5 minutes
  notes: >
    Rolling average is recalculated every minute. New agents with
    insufficient history use the platform-wide average for their
    agent type as baseline. The 10x multiplier and 5-minute sustain
    period are configurable per environment.
```

**pattern_deviation** — Agent behavior changes significantly from
its historical baseline.

```yaml
pattern_deviation:
  trigger: operation distribution deviates > 3σ from historical baseline
  severity: low → medium (if sustained)
  action: graduated_response
  response:
    - stage_1: deviation detected → audit alert
    - stage_2: sustained > 10 minutes → escalate to operator
    - stage_3: operator confirms anomaly → quarantine (manual)
  threshold:
    baseline_window: 24 hours rolling
    deviation: 3 standard deviations
    sustain_period: 10 minutes
  notes: >
    Baseline is built from the agent's operation distribution over
    the last 24 hours: percentage of reads vs writes, message
    frequency, external call patterns. Deviation is calculated as
    the Euclidean distance between the current window distribution
    and the baseline distribution, normalized by standard deviation.
    Pattern deviation alone never triggers automatic quarantine —
    it always escalates to an operator for confirmation.
```

### Agent Behavioral Profile

The behavior analyzer maintains a profile for each registered agent:

```yaml
agent_profile:
  agent_name: string
  registered_at: timestamp
  capabilities: []string          # From manifest
  operational_scope: ScopeLevel   # From manifest
  baseline:
    operation_distribution:       # Percentage by operation type
      read: float
      write: float
      delete: float
      send: float
      external: float
    average_rate: float           # Operations per minute (1h rolling)
    peak_rate: float              # Highest observed rate
    common_targets: []string      # Most-accessed resources/agents
  current_window:
    operation_distribution: {}    # Same structure, current 5-min window
    current_rate: float
    anomaly_flags: []string       # Active anomaly indicators
  violation_history:
    total_violations: integer
    last_violation: timestamp
    violation_types: {}           # Count by type
  quarantine_history:
    times_quarantined: integer
    last_quarantine: timestamp
```

---

## Quarantine Enforcement

When quarantine is triggered — either by rogue detection, safety
kill-switch, or operator action — the enforcement layer executes a
complete isolation of the targeted agent across all three boundaries.

### Quarantine Sequence

```
1. Receive QuarantineOrder (from safety.md or rogue detection)
   - Validate: agent exists, reason provided, issuer authorized

2. Add to quarantine store:
   {agent_name, quarantine_id, reason, severity, issued_by,
    entered_at, correlation_id}

3. Message boundary:
   - Stop routing messages TO the quarantined agent
   - Stop routing messages FROM the quarantined agent
   - Messages in-flight at quarantine time are allowed to complete
   - New messages are dropped with ENFORCEMENT_QUARANTINED

4. Storage boundary:
   - Block all write and delete operations from the quarantined agent
   - Read operations: configurable (default: allow reads, block writes)
     Rationale: investigation may require the agent's stored data
   - New write/delete operations are rejected with ENFORCEMENT_QUARANTINED

5. External boundary:
   - Block all outbound calls from the quarantined agent
   - No exceptions — quarantined agents cannot reach external services
   - Pending outbound requests are cancelled

6. State preservation:
   - Snapshot the agent's behavioral profile at quarantine time
   - Preserve the violation history and detection evidence
   - Mark the snapshot as investigation material (scope: restricted)

7. Notification:
   - Emit quarantine.entered event to system.* namespace
   - Notify operators via configured alerting channels
   - Include: agent name, reason, severity, evidence summary,
     correlation_id linking to the triggering violation

8. Audit:
   - Log quarantine entry to audit writer
   - Classification: restricted scope (quarantine events are sensitive)
```

### Quarantine Release

```
1. Operator or admin requests release via quarantine API

2. Validate authority:
   - Severity low/medium → operator can release
   - Severity high/critical → admin required

3. Remove from quarantine store

4. All boundaries resume normal policy evaluation for the agent

5. Emit quarantine.exited event to system.* namespace

6. Log release to audit writer with justification

7. Agent behavioral profile is reset to current baseline
   (not historical — post-quarantine behavior establishes a new baseline)
```

---

## Security

### Trust Model

The enforcement layer is a privileged platform component. It has
read access to agent manifests, policy definitions, scope
classifications, and safety intents. It does NOT have write access
to any of these — it consumes them, never modifies them.

The enforcement layer is the only component that can:
- Block agent operations across all three boundaries
- Execute quarantine (complete agent isolation)
- Execute kill-switch (permanent agent shutdown)

No agent — including infrastructure agents — can disable, bypass, or
modify enforcement behavior. The enforcement layer is not registered
as an agent. It is not in the service directory. It has no message
endpoint. Agents cannot send messages to it. It is structurally
invisible to agents — they interact with the message bus, storage
layer, and external services, which are proxied through enforcement
without agents' awareness.

### Attack Surface

| Threat | Mitigation |
|--------|------------|
| Agent spoofs identity to bypass capability check | Identity is resolved from authenticated token, not agent-supplied metadata |
| Agent sends high-volume to overwhelm enforcement | Volume anomaly detection triggers quarantine; enforcement has higher resource priority than any agent |
| Agent attempts to access quarantine API | Quarantine API is admin-only; agents have no route to it |
| Malicious policy injected to allow dangerous operations | Policy lifecycle is managed via `patterns/policy` with admin authority; enforcement reads policies, never writes them |
| Enforcement layer itself is compromised | Enforcement runs in a separate trust domain from agents; compromise requires platform-level access |
| Agent exploits decision cache to replay stale allows | Cache entries are invalidated on policy, scope, or quarantine changes; TTL is max 5 seconds |

### Fail-Closed Guarantees

The enforcement layer is fail-closed at every stage:

- Policy evaluation error → deny
- Scope resolution failure → deny
- Manifest not found → deny
- Safety intent lookup failure → deny
- Quarantine store unavailable → deny all (full lockdown)
- Decision cache miss → full evaluation (no stale allows)
- Behavior analyzer failure → enforcement continues without
  behavioral signals (detection degrades, enforcement does not)

---

## Implementation Notes

### Boundary Integration

The enforcement layer integrates by **wrapping** existing interfaces,
not by modifying them. The message bus, storage layer, and external
service clients continue to operate as defined in their respective
blueprints. Enforcement inserts a proxy between the agent and each
resource:

- **Message boundary**: The agent's message send function is wrapped.
  The wrapper calls enforcement before forwarding to the bus. The bus
  is unaware of enforcement.
- **Storage boundary**: The agent's storage client is wrapped. The
  wrapper calls enforcement before executing the storage operation.
  The storage layer is unaware of enforcement.
- **External boundary**: The agent's HTTP/SMTP client is wrapped. The
  wrapper calls enforcement before dispatching the request. The
  external service is unaware of enforcement.

This wrapping approach means enforcement can be added to an existing
Weblisk deployment without modifying the message bus, storage engine,
or external service adapters.

### Performance Budget

Enforcement adds latency to every operation. The performance budget:

| Boundary | Target Overhead | Max Overhead |
|----------|----------------|-------------|
| Message  | < 1ms          | 5ms         |
| Storage  | < 2ms          | 10ms        |
| External | < 1ms          | 5ms         |

To meet these targets:
- Decision cache eliminates repeated policy evaluation
- Quarantine check is a single hash lookup (sub-microsecond)
- Capability check is a set membership test (sub-microsecond)
- Scope comparison is a numeric comparison (sub-microsecond)
- Policy evaluation (the expensive step) is the only operation
  that may approach the target overhead
- Behavioral signal emission is asynchronous (non-blocking)
- Audit writing is asynchronous (non-blocking)

### Startup Sequence

```
1. Load quarantine store from persistent storage
2. Load agent manifests from service directory
3. Initialize decision cache (empty)
4. Initialize behavior analyzer with persisted agent profiles
5. Initialize violation queue
6. Start audit writer consumer
7. Wrap message bus with message boundary proxy
8. Wrap storage layer with storage boundary proxy
9. Wrap external clients with external boundary proxy
10. Enforcement is now active — all operations are intercepted
```

### Graceful Degradation

If the enforcement layer experiences partial failure:

| Component Failed | Behavior |
|-----------------|----------|
| Decision cache | Full evaluation on every operation (slower, not less secure) |
| Behavior analyzer | Enforcement continues; rogue detection disabled (violations still detected by capability/scope checks) |
| Audit writer | Enforcement continues; decisions buffered in violation queue; alert operators of audit gap |
| Violation queue | Violations logged synchronously (slower but not lost) |
| Policy evaluator | Fail-closed: deny all operations until policy evaluation is restored |
| Quarantine store | Fail-closed: deny all operations (cannot verify quarantine state) |

### Platform-Specific Considerations

| Platform | Enforcement Strategy |
|----------|---------------------|
| Cloudflare Workers | Enforcement runs as middleware in the Worker pipeline; decision cache uses Workers KV; quarantine store uses Durable Objects |
| Node.js | Enforcement runs as middleware wrapping message/storage/external adapters; in-process decision cache; quarantine store in configured persistence |
| Go | Enforcement as interceptor middleware; concurrent-safe decision cache with sync.Map; quarantine store in configured persistence |
| Rust | Enforcement as tower middleware layer; lock-free decision cache; quarantine store in configured persistence |

---

## Verification Checklist

1. **Message boundary intercepts all messages** — Send a message
   between two agents. Verify that the enforcement layer intercepts
   the message, evaluates policies, and logs the decision before the
   message reaches the recipient.

2. **Storage boundary blocks scope violations** — Configure an agent
   with `internal` operational scope. Attempt to write to a
   `restricted` resource. Verify that enforcement blocks the operation
   with `ENFORCEMENT_SCOPE_VIOLATION`.

3. **External boundary prevents scope leakage** — Configure an agent
   to send `restricted`-scope data to an unclassified external
   endpoint. Verify that enforcement blocks the request with
   `ENFORCEMENT_SCOPE_LEAKAGE`.

4. **Quarantine blocks all three boundaries** — Quarantine an agent.
   Verify that messages to/from the agent are blocked, storage
   write/delete operations are rejected, and external calls are
   cancelled.

5. **Capability mismatch detected immediately** — Register an agent
   with `[storage:read]` capability. Attempt a `storage:write`
   operation. Verify that enforcement blocks the operation and emits
   a `capability_mismatch` violation.

6. **Volume anomaly triggers graduated response** — Generate
   operation volume exceeding 10x the rolling average. Verify that
   an audit alert is emitted. Sustain the volume for 5 minutes.
   Verify that the agent is quarantined.

7. **Fail-closed on policy evaluation error** — Simulate a policy
   evaluation failure. Verify that enforcement denies the operation
   rather than allowing it.

8. **Audit trail is complete** — Execute a sequence of operations
   across all three boundaries (some allowed, some denied). Query
   the enforcement report API. Verify that every decision is logged
   with correlation ID, agent, boundary, operation, scope, policies
   evaluated, and decision result.

9. **Decision cache invalidation** — Allow an operation that hits
   the decision cache. Change the applicable policy to deny. Verify
   that the next identical operation is denied (cache invalidated).

10. **Quarantine release requires appropriate authority** — Quarantine
    an agent with `high` severity. Attempt release with operator
    authority. Verify rejection. Release with admin authority. Verify
    success. Verify the agent resumes normal operation across all
    boundaries.
