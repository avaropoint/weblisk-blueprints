<!-- blueprint
type: architecture
name: testing
version: 1.0.0
requires: [protocol/identity, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
-->

# Weblisk Conformance Testing

A specification for verifying that an implementation of the Weblisk
Agent Protocol is correct. This document defines test fixtures, a mock
orchestrator, a mock agent, and the standard conformance flow that
every implementation MUST pass.

## Overview

Conformance testing verifies three things:

1. **Protocol compliance** — endpoints accept/return the right shapes
2. **Security compliance** — signatures, tokens, replay protection work
3. **Lifecycle compliance** — the full observe → recommend → approve →
   execute → feedback loop produces correct state transitions

Tests are black-box: they exercise HTTP endpoints and verify responses.
Implementations in any language can run the same test suite.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: SigningKeyPair
          fields_used: [public_key, private_key, sign, verify]
        - name: SignatureVerification
          fields_used: [verify_signature, check_replay]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: RegisterResponse
          fields_used: [agent_id, token, expires_at, services]
        - name: TaskRequest
          fields_used: [id, action, input]
        - name: TaskResult
          fields_used: [task_id, status, agent_name, output]
        - name: AgentManifest
          fields_used: [name, type, version, url, public_key, capabilities]
        - name: AgentMessage
          fields_used: [from, to, type, action, payload, signature]
        - name: ErrorResponse
          fields_used: [error, code]
        - name: ServiceDirectory
          fields_used: [services, routing_table, namespaces]
        - name: ChannelGrant
          fields_used: [channel_id, token, target_url]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentEndpoints
          fields_used: [describe, execute, message, health, services]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: DomainManifest
          fields_used: [required_agents, workflows]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

### Owns
- Conformance test suite definition (Level 1: protocol, Level 2: security, Level 3: lifecycle)
- Test fixture definitions (deterministic ML-DSA-65 key pairs, manifest fixtures)
- Mock orchestrator specification and behavior contract
- Mock agent specification and configurable response contract
- Test execution CLI interface (`weblisk test conformance`)
- Pass/fail criteria and assertion format for each test case

### Does NOT Own
- Implementation of the components under test (owned by platform documents)
- Production orchestrator or agent behavior (owned by their respective blueprints)
- Performance/load testing (out of scope — this is conformance testing only)
- Integration with external CI/CD systems (deployment-specific)

---

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| `weblisk test conformance --orch <url>` | CLI | Run full conformance suite against a running system |
| `weblisk test conformance --level <n>` | CLI | Run specific test level (1, 2, or 3) |
| `weblisk test conformance --test <id>` | CLI | Run a single test by ID (e.g., L1-03) |
| `weblisk test mock-orchestrator --port <n>` | CLI | Start mock orchestrator on specified port |
| Mock Orchestrator: `POST /v1/register` | HTTP | Accept valid registrations, return token |
| Mock Orchestrator: `GET /v1/health` | HTTP | Return healthy status |
| Mock Agent: `POST /v1/execute` | HTTP | Return configurable `TaskResult` |
| Mock Agent: `POST /v1/message` | HTTP | Return configurable response payload |

---

## Data Flow

1. Test harness starts mock orchestrator on port 19800
2. System under test (agent or orchestrator) is started on its configured port
3. Test harness builds a `RegisterRequest` with deterministic test keys
4. Test harness sends registration request and validates the `RegisterResponse`
5. Test harness sends task/message requests with valid tokens and verifies responses
6. For Level 2: test harness sends malformed signatures, expired tokens, and oversized payloads — verifies rejection
7. For Level 3: test harness starts full system (orchestrator + domain + agent) and executes end-to-end workflow
8. Workflow produces observations, recommendations, and feedback — test harness verifies state transitions
9. Test harness collects results and reports pass/fail per test ID
10. All assertions include test ID in failure messages for triage

---

## Test Fixtures

### Identity Fixtures

Fixed ML-DSA-65 key pairs for deterministic testing. These are TEST KEYS
ONLY — never use in production.

```
Test Orchestrator:
  name: "test-orchestrator"
  private_key: "0000000000000000000000000000000000000000000000000000000000000001" (test only)
  public_key:  derived from private key via ML-DSA-65

Test Agent (work):
  name: "test-agent"
  private_key: "0000000000000000000000000000000000000000000000000000000000000002" (test only)
  public_key:  derived from private key via ML-DSA-65

Test Domain:
  name: "test-domain"
  private_key: "0000000000000000000000000000000000000000000000000000000000000003" (test only)
  public_key:  derived from private key via ML-DSA-65
```

Implementations MUST support a `--test-keys` flag or equivalent
configuration option that loads these deterministic keys instead of
generating random ones. This enables reproducible tests.

### Manifest Fixtures

**Test work agent manifest:**
```json
{
  "name": "test-agent",
  "type": "agent",
  "version": "1.0.0",
  "description": "Conformance test agent",
  "url": "http://localhost:9710",
  "public_key": "<derived from test key 2>",
  "capabilities": [
    {"name": "file:read", "resources": ["**/*.html"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [{"name": "files", "type": "file_list", "description": "Files to process"}],
  "outputs": [{"name": "report", "type": "json", "description": "Processing report"}],
  "max_concurrent": 5
}
```

**Test domain manifest:**
```json
{
  "name": "test-domain",
  "type": "domain",
  "version": "1.0.0",
  "description": "Conformance test domain",
  "url": "http://localhost:9700",
  "public_key": "<derived from test key 3>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "required_agents": ["test-agent"],
  "workflows": ["test-workflow"],
  "max_concurrent": 10
}
```

---

## Mock Orchestrator

A minimal orchestrator implementation for testing agents in isolation.
Implements only the endpoints agents call during their lifecycle.

### Endpoints

| Endpoint | Behavior |
|----------|----------|
| `POST /v1/register` | Accept any valid registration, return token + empty service directory |
| `GET /v1/health` | Return `{"name": "mock-orchestrator", "status": "healthy", ...}` |
| `POST /v1/channel` | Return a channel grant with a test channel token |
| `GET /v1/services` | Return the current registered agents |

### Behavior

- Accepts all valid signatures (verifies format but uses the provided public key)
- Issues tokens with 24h TTL using test orchestrator keys
- Stores registrations in memory
- Does NOT forward tasks (mock only)

### What the mock cannot establish

The mock is deliberately permissive, which makes it useful for developing an
agent and useless for concluding that the agent can register. Reusing the
provided public key means a signature verifies whatever bytes were signed;
accepting any valid registration means the manifest is never judged against the
registry's vocabulary.

Every one of these passes against the mock and is refused by a real
orchestrator:

| Fault | Why the mock misses it |
|---|---|
| Signature over different bytes than the verifier canonicalizes | The mock verifies with the key the caller supplied, over the caller's own payload |
| A manifest field the registry's type does not define | The mock does not re-canonicalize a parse, so no asymmetry arises |
| A capability name outside `protocol/types` | The mock enforces no vocabulary |
| A subscription scope that is not `self`, `*` or an agent name | Not validated |
| `protocol_version` that is not the wire version | Not negotiated |
| Registering at a path the orchestrator does not serve | The mock is mounted wherever the test mounts it |

**A component MUST NOT be signed off as conformant on the strength of the mock
alone.** Level 4 is where registration is actually established, and until it
passes, "registers successfully" is an untested claim. The mock's value is that
it fails fast during development; it is not evidence.

### Usage

```bash
# Start mock orchestrator on test port
weblisk test mock-orchestrator --port 19800

# Or programmatically in test code
mockOrch := weblisk.NewMockOrchestrator(19800, testOrchestratorKey)
mockOrch.Start()
defer mockOrch.Stop()
```

---

## Mock Agent

A minimal agent for testing domain controllers and the orchestrator.
Responds to execute and message with configurable responses.

### Endpoints

| Endpoint | Behavior |
|----------|----------|
| `POST /v1/describe` | Return the test agent manifest |
| `POST /v1/execute` | Return a configurable `TaskResult` |
| `POST /v1/message` | Return a configurable response payload |
| `POST /v1/health` | Return healthy status |
| `POST /v1/services` | Accept and store |

### Configurable Responses

The mock agent supports pre-programmed responses:

```
mockAgent.OnExecute(func(task TaskRequest) TaskResult {
  return TaskResult{
    Status: "success",
    Summary: "processed",
    Observations: [...],
    Recommendations: [...],
  }
})

mockAgent.OnMessage("scan_html", func(payload map) map {
  return {"files": [...], "measurements": {...}}
})
```

---

## Conformance Test Suite

### Level 1: Protocol Compliance

These tests verify basic endpoint behavior. Every implementation MUST pass every
Level 1 test **that applies to it**.

Each test names the components it applies to. A test addressed to an agent is
not a failure of an orchestrator: they serve different endpoints, and running
every test against every component reports a correct implementation as broken —
the same fault the Verification Checklists had before their groups were read.

#### L1-01: Health Check

Applies to: **orchestrator**, **agent**. Method differs by component —
`protocol/spec` gives the orchestrator `GET /v1/health` and an agent
`POST /v1/health`.

```
GET /v1/health  (orchestrator)   → 200
POST /v1/health (agent)          → 200
No auth required.
Response MUST be a HealthStatus: name, status, version, uptime, timestamp
status MUST be one of: healthy, degraded, unhealthy
```

This test previously read `POST /v1/health`, required fields `state` and
`uptime_seconds`, and demanded `state == "online"`. `protocol/types` defines
HealthStatus with `status`, `uptime` and the values healthy/degraded/unhealthy,
and `protocol/spec` gives the orchestrator GET. A conformant implementation
failed the test, which is the wrong way round: **the type definition is the
authority and a test asserts it**, never the reverse.

#### L1-02: Describe

Applies to: **agent** only — the orchestrator does not serve `/v1/describe`.
```
POST /v1/describe → 200
Response MUST be a valid AgentManifest
Response MUST contain: name, version, url, public_key, capabilities
```

#### L1-03: Registration

Applies to: **orchestrator** only — it is the registry.
```
1. Build RegisterRequest with valid manifest + signature
2. POST /v1/register → 200
3. Response MUST contain: agent_id, token, expires_at, services
4. Token MUST be valid WLT format
5. agent_id MUST be 32 hex chars
```

#### L1-04: Registration Rejects Bad Signature

Applies to: **orchestrator** only.
```
1. Build RegisterRequest with wrong signature
2. POST /v1/register → 401
3. Response MUST contain error field
```

#### L1-05: Registration Rejects Stale Timestamp

Applies to: **orchestrator** only.
```
1. Build RegisterRequest with timestamp = now - 600 seconds
2. POST /v1/register → 401
3. Response.error MUST mention replay or timestamp
```

#### L1-06: Execute Task

Applies to: **agent** only.
```
1. Register agent (get token)
2. Build TaskRequest with valid token
3. POST /v1/execute → 200
4. Response MUST be valid TaskResult
5. Response.task_id MUST match request.id
6. Response.agent_name MUST match manifest.name
```

#### L1-07: Protected Endpoints Require Auth

Applies to: **orchestrator**, **agent** — against each component's own protected endpoints.
```
For each protected endpoint (/v1/services, /v1/execute, /v1/audit, etc.):
  1. Send request without token → 401
  2. Send request with expired token → 401
  3. Send request with valid token → not 401
```

#### L1-08: Message Handling

Applies to: **agent** only.
```
1. Register agent
2. Build AgentMessage: {from: "test", to: agent.name, type: "request", action: "scan_html", payload: {...}}
3. Sign message
4. POST /v1/message → 200
5. Response MUST be AgentMessage with type: "response"
6. Response.from MUST be agent.name
```

#### L1-09: Service Directory Update

Applies to: **agent** only — the orchestrator PUBLISHES the directory.
```
1. Register agent
2. POST /v1/services with ServiceDirectory → 200
3. Agent's internal service list MUST be updated
```

#### L1-10: Error Response Format

Applies to: **orchestrator**, **agent** — every component.
```
For any 4xx/5xx response:
  Body MUST be JSON
  Body MUST contain "error" field (string)
  Body SHOULD contain "code" field when applicable
```

### Level 2: Security Compliance

#### L2-01: Signature Verification on Messages
```
1. Send AgentMessage with invalid signature to agent
2. Agent MUST return 401
```

#### L2-02: Token Expiry Enforcement
```
1. Create token with exp = now - 1
2. Send request with expired token
3. Must receive 401
```

#### L2-03: Channel Token Scoping
```
1. Request channel between agent-A and agent-B
2. Use channel token to message agent-B → success
3. Use channel token to message agent-C → fail (wrong scope)
```

#### L2-04: Request Body Size Limits
```
1. Send registration body > 1 MB → must reject (413 or 400)
2. Send task body > 10 MB → must reject
3. Send message body > 1 MB → must reject
```

#### L2-05: Replay Protection
```
1. Record a valid registration request
2. Replay same request after 300+ seconds → 401
```

### Level 3: Lifecycle Compliance

Tests the full feedback loop. Requires orchestrator + domain + agent.

#### L3-01: Full Audit Workflow
```
1. Start orchestrator
2. Register domain (type: "domain", required_agents: ["test-agent"])
3. Domain status → "degraded" (test-agent not registered yet)
4. Register test-agent
5. Domain status → "online"
6. Submit task to domain targeting action "test-workflow"
7. Domain publishes workflow.trigger event:
   a. Workflow Agent resolves DAG
   b. Task Agent dispatches phase to test-agent via /v1/execute
   c. Workflow Agent aggregates results
   d. Publishes workflow.completed (scope: domain)
8. Lifecycle Agent captures observations from workflow.completed event
9. Lifecycle Agent stores recommendations
10. Approve recommendation (POST /v1/message to Lifecycle Agent, action: approve_recommendation)
11. Recommendation status transitions pending → accepted
12. Verify audit log contains: register (x4), event, approval entries
```

#### L3-02: Strategy Lifecycle
```
1. Create strategy (POST /v1/message to Lifecycle Agent, action: create_strategy)
2. Verify strategy stored (POST /v1/message to Lifecycle Agent, action: get_strategy)
3. Lifecycle Agent publishes workflow.trigger linked to strategy
4. Verify observations reference the strategy_id
5. After feedback, verify strategy target.progress is updated
```

#### L3-03: Workflow Error Handling
```
1. Configure mock agent to fail on "analyze" action
2. Submit task that triggers a workflow with on_error: "skip"
3. Verify: failed phase is skipped, dependent phases proceed
4. Verify: WorkflowExecution records the skipped phase

5. Configure mock agent to fail on "scan" action
6. Submit task with on_error: "fail"
7. Verify: entire workflow fails
8. Verify: TaskResult status = "failed"
```

#### L3-04: Concurrency Enforcement
```
1. Set mock agent max_concurrent = 2
2. Send 5 concurrent execute requests
3. Verify: first 2 accepted, remaining get 429
4. Verify: 429 response is valid ErrorResponse with code RATE_LIMITED
```

#### L3-05: Approval Gate
```
1. Submit task that produces a recommendation with approval: "required"
2. Verify workflow execution pauses (status: "pending_approval")
3. Approve via POST /v1/message to Lifecycle Agent (action: approve_recommendation)
4. Lifecycle Agent publishes workflow.approval.decision
5. Verify workflow resumes and completes
```

---

### Level 4: Interoperability

Levels 1 to 3 run one component against fixtures. Level 4 runs a component
against **the real orchestrator it will register with**, because a component can
satisfy every assertion about itself and still be unable to join a mesh.

This level exists because it was missing. The first time two independently
generated components of one tenant were asked to interoperate, the second could
not register — eight consecutive refusals, each a contract stated in a way that
cannot be implemented twice, and none of them visible to a suite that starts one
binary alone.

#### L4-01: Registers With A Real Orchestrator

Applies to: every component that registers — **not** the orchestrator itself.
```
1. Start a real orchestrator on an ephemeral port
2. Start the component with that orchestrator's URL
3. The component MUST reach a listening state and MUST NOT exit
4. GET /v1/health on the orchestrator MUST report agents >= 1
5. The component's health MUST report its registration as healthy
6. The component MUST hold an agent_id and a token
```

The order of 3 and 4 matters. A component that requires the orchestrator's
public key in order to construct its authenticator exits before it registers,
and can therefore never obtain the key it refused to start without. A component
MUST be able to listen before it has registered.

#### L4-02: Manifest Is Accepted On Its Own Terms

```
1. Register against a real orchestrator
2. Every capability name MUST be one protocol/types declares
3. Every subscription scope MUST be `self`, `*`, or an agent name
4. protocol_version MUST be the wire version, not the component's semver
5. The manifest MUST carry no field outside AgentManifest
6. Registration MUST NOT be refused with INVALID_REQUEST
```

#### L4-03: Signature Survives A Foreign Verifier

```
1. Sign a manifest that carries one field the verifier's type does not define
2. Register against a real orchestrator
3. Registration MUST succeed
```

A failure here is a canonicalization fault on one side or the other, not an
invalid key — see `protocol/spec` Signing input. It is asserted with an extra
field deliberately, because that is the case a verifier re-serializing its own
parse gets wrong, and the case a shared struct definition hides.

#### L4-04: Standalone Operation

Applies to: every component that registers.
```
1. Start the component with NO orchestrator URL
2. It MUST serve GET /v1/health unauthenticated and MUST NOT exit
3. Every protected endpoint MUST refuse with 401 and a structured ErrorResponse
4. Health MUST report degraded — never healthy, never unhealthy
```

A component that cannot verify a token MUST NOT accept one, and a component that
cannot be started alone cannot be conformance-tested at all.

---

## Running Tests

```bash
# Run full conformance suite against a running system
weblisk test conformance --orch http://localhost:9800

# Run specific level
weblisk test conformance --level 1

# Run single test
weblisk test conformance --test L1-03

# Run with verbose output
weblisk test conformance --verbose
```

## Implementation Notes

- Tests SHOULD be runnable against any implementation regardless of
  language — they exercise HTTP endpoints only.
- The test harness SHOULD be implemented as part of the Weblisk CLI
  (`weblisk test`), making it available to all implementors.
- Level 1 and 2 tests can run against a single agent or orchestrator.
  Level 3 tests require a full system (orchestrator + domain + agent).
- Mock components run on ports 19800 (mock orchestrator), 19700 (mock
  domain), 19710 (mock agent) to avoid conflicting with real instances.
- All test assertions include the test ID in failure messages for
  easy triage: `FAIL L1-03: agent_id must be 32 hex chars, got 28`.

## Verification Checklist
- [ ] Conformance sign-off requires Level 4 against a real orchestrator; the mock alone is never sufficient
- [ ] Every registering component passes L4-01: it listens, registers, and the orchestrator counts it
- [ ] A manifest carrying an extra field still registers (L4-03)
- [ ] Every registering component passes L4-04: it starts with no orchestrator, serves health, and refuses protected endpoints with 401

- [ ] All Level 1 tests pass (protocol compliance)
- [ ] All Level 2 tests pass (security compliance)
- [ ] All Level 3 tests pass (lifecycle compliance)
- [ ] Mock orchestrator can start and accept registrations
- [ ] Mock agent can respond to execute and message
- [ ] Test keys are deterministic and reproducible
- [ ] Tests run against HTTP endpoints only (black-box)

### A check that cannot read the artifact MUST say so

A conformance check reports on generated code it did not write. When it cannot
parse what it is looking at, the honest result is "I could not tell", and it
MUST NOT be reported as an absence in the artifact.

The route check accepted only a string literal as a mux pattern. Real generated
code registers from a table of named constants:

```go
{pattern: protocol.PathAdminOverview, methods: ...},
{pattern: agents + "/{name}", methods: ...},
```

It found no literals, recorded no routes, and refuted twenty-one correct
assertions with `no handler is registered for: GET /v1/health` — about a hub
that registers `/v1/health` correctly. Resolving constants, local aliases and
concatenation took the same artifact from **0 routes found to 17**, the complete
surface.

So a structural check MUST:

- Resolve the expressions real code is written in — named constants, qualified
  constants, local aliases and concatenation — not only literals.
- Record what it could not resolve, and report that as a limit of the check
  rather than as a finding about the artifact.
- Never invent a route, symbol or field from an expression it could not
  evaluate. A partial resolution is not an answer.

This is `patterns/scope`'s rule about confident zeroes, applied to tooling: a
check that reports absence when it means illegibility teaches an operator to
ignore its output, which costs more than the check was worth.

### A result that is not acted on is not a check

Conformance ran the generated component, found that it panicked at startup,
printed the stack trace, attempted two rounds of repair, reported
`the component does not run` — and the build **exited 0**.

The results were printed and discarded. Everything reading the exit status — a
script, a CI job, a control plane, an operator — was told a hub had been built,
and the hub did not start.

So a build MUST fail when:

- the component does not run, or
- any conformance test **failed**.

An **unrun** test MUST NOT fail the build. "We have not verified this" and "this
is wrong" are different facts, and conflating them makes the unrun count a
reason to reject a correct build — while still reporting unrun tests as what
they are, which is never passes.

The failure MUST be reported **last**, after the checklist and the model's own
verdicts. Returning at the point of detection hides the two reports where the
cause usually is.

A check whose result is discarded is indistinguishable from no check, except
that it costs time and looks like diligence.

### Level 0: it starts

Before any assertion about behaviour, the component MUST be started with **no
terminal attached** and MUST answer its health endpoint. Two separate faults
were caught only by doing this by hand:

- a mux pattern conflict that compiles, passes every structural check, and
  panics when the routes are registered
- a service that prompts for a key passphrase and dies on EOF

Neither is visible in source review, and both make every other level
unrunnable.
