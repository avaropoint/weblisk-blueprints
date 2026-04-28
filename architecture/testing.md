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
        - name: Ed25519KeyPair
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
          fields_used: [agents, routing_table, namespaces]
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
- Test fixture definitions (deterministic Ed25519 key pairs, manifest fixtures)
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

Fixed Ed25519 key pairs for deterministic testing. These are TEST KEYS
ONLY — never use in production.

```
Test Orchestrator:
  name: "test-orchestrator"
  private_key: "0000000000000000000000000000000000000000000000000000000000000001" (test only)
  public_key:  derived from private key via Ed25519

Test Agent (work):
  name: "test-agent"
  private_key: "0000000000000000000000000000000000000000000000000000000000000002" (test only)
  public_key:  derived from private key via Ed25519

Test Domain:
  name: "test-domain"
  private_key: "0000000000000000000000000000000000000000000000000000000000000003" (test only)
  public_key:  derived from private key via Ed25519
```

Implementations MUST support a `--test-keys` flag or `WL_TEST_KEYS=1`
environment variable that loads these deterministic keys instead of
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

These tests verify basic endpoint behavior. Every implementation
MUST pass all Level 1 tests.

#### L1-01: Health Check
```
POST /v1/health → 200
Response MUST contain: name, state, version, uptime_seconds
state MUST be "online"
```

#### L1-02: Describe
```
POST /v1/describe → 200
Response MUST be a valid AgentManifest
Response MUST contain: name, version, url, public_key, capabilities
```

#### L1-03: Registration
```
1. Build RegisterRequest with valid manifest + signature
2. POST /v1/register → 200
3. Response MUST contain: agent_id, token, expires_at, services
4. Token MUST be valid WLT format
5. agent_id MUST be 32 hex chars
```

#### L1-04: Registration Rejects Bad Signature
```
1. Build RegisterRequest with wrong signature
2. POST /v1/register → 401
3. Response MUST contain error field
```

#### L1-05: Registration Rejects Stale Timestamp
```
1. Build RegisterRequest with timestamp = now - 600 seconds
2. POST /v1/register → 401
3. Response.error MUST mention replay or timestamp
```

#### L1-06: Execute Task
```
1. Register agent (get token)
2. Build TaskRequest with valid token
3. POST /v1/execute → 200
4. Response MUST be valid TaskResult
5. Response.task_id MUST match request.id
6. Response.agent_name MUST match manifest.name
```

#### L1-07: Protected Endpoints Require Auth
```
For each protected endpoint (/v1/services, /v1/execute, /v1/audit, etc.):
  1. Send request without token → 401
  2. Send request with expired token → 401
  3. Send request with valid token → not 401
```

#### L1-08: Message Handling
```
1. Register agent
2. Build AgentMessage: {from: "test", to: agent.name, type: "request", action: "scan_html", payload: {...}}
3. Sign message
4. POST /v1/message → 200
5. Response MUST be AgentMessage with type: "response"
6. Response.from MUST be agent.name
```

#### L1-09: Service Directory Update
```
1. Register agent
2. POST /v1/services with ServiceDirectory → 200
3. Agent's internal service list MUST be updated
```

#### L1-10: Error Response Format
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

- [ ] All Level 1 tests pass (protocol compliance)
- [ ] All Level 2 tests pass (security compliance)
- [ ] All Level 3 tests pass (lifecycle compliance)
- [ ] Mock orchestrator can start and accept registrations
- [ ] Mock agent can respond to execute and message
- [ ] Test keys are deterministic and reproducible
- [ ] Tests run against HTTP endpoints only (black-box)
