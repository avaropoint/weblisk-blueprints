<!-- blueprint
type: architecture
name: data-security
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/federation, architecture/gateway, architecture/observability, patterns/scope, patterns/policy, patterns/privacy, architecture/enforcement]
platform: any
tier: free
-->

# Data Security Architecture

Specification for how the Weblisk framework secures data as it moves
between components — agents, orchestrators, gateways, and federated
peers. This defines the **transport and boundary security** that the
framework provides by default.

The Weblisk framework secures the **transport** — encrypted channels,
signed messages, authenticated identities, and audited operations.
For data-level concerns, the framework provides **opt-in primitives**:

- **Scope** (patterns/scope) — universal classification levels
  that travel with data and drive protections automatically
- **Policy** (patterns/policy) — declarative rules that constrain
  operations based on scope, identity, and context
- **Privacy** (patterns/privacy) — consent, masking, minimization,
  and erasure primitives that activate based on scope
- **Enforcement** (architecture/enforcement) — non-bypassable
  boundary inspection that validates scope and policy compliance

These primitives are opt-in. Agents that handle sensitive data
adopt the scope, policy, and privacy patterns to get framework-level
protection. Agents that don't need them operate with transport
security only.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /v1/message
          methods: [POST]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentMessage
          fields_used: [from, to, action, payload, signature]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Ed25519KeyPair
          fields_used: [public_key, private_key]
        - name: Signature
          fields_used: [algorithm, value]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/federation
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: DataContract
          fields_used: [fields, required, forbidden, permitted]
        - name: FederationPeer
          fields_used: [hub_name, public_key, trust_tier]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [tls, internal_headers, response_sanitization]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AuditEntry
          fields_used: [id, timestamp, actor, action, target]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

The boundary between framework and application security is detailed in
[What the Framework Secures](#what-the-framework-secures) and
[What the Framework Does NOT Do](#what-the-framework-does-not-do).

### Owns

- TLS termination and encryption-in-transit across all component boundaries
- Ed25519 message signing and verification for agent-to-agent communication
- Internal header trust model (`X-Gateway-*` injection and validation)
- Federation data contract enforcement (forbidden field stripping at boundaries)
- Append-only audit trail for inter-component operations
- Response sanitization (stripping internal headers, server identification)

### Does NOT Own

- Application-specific data models — the framework classifies via scope levels, not data types
- Encryption-at-rest key hierarchy — application/agent responsibility
- Regulatory interpretation — the framework provides compliance primitives (patterns/governance), not legal advice

### Enables (via opt-in patterns)

- Data classification — via patterns/scope (5-level universal scope)
- Field-level masking — via patterns/privacy (scope-driven masking rules)
- Data retention and deletion — via patterns/privacy (erasure cascade, retention policies)
- Policy enforcement — via patterns/policy + architecture/enforcement (boundary inspection)

---

## Interfaces

The data security component does not expose standalone endpoints. Its
interfaces are enforcement points integrated into other components:
- Gateway: TLS termination, header injection, response sanitization
  (see [Transport Security](#transport-security) and [Response Sanitization](#response-sanitization))
- Agent-to-agent: Ed25519 message signing covering `{from, to, action, payload}`
  (see [Authentication Boundaries](#authentication-boundaries))
- Federation: data contract enforcement at hub boundaries
  (see [Federation Data Boundaries](#federation-data-boundaries))

---

## Data Flow

1. Browser sends request to application gateway over TLS 1.2+ (1.3 preferred)
2. Gateway terminates TLS and authenticates user (session or token)
3. Gateway injects trusted headers (`X-Gateway-Session`, `X-Gateway-User`, `X-Gateway-Roles`)
4. Request forwarded to target agent over TLS (or mTLS in zero-trust)
5. Agent verifies request originates from registered gateway (header validation)
6. Agent processes request; response returned to gateway
7. Gateway sanitizes response (strips internal headers, server identification)
8. For agent-to-agent: sender signs `{from, to, action, payload}` with Ed25519; recipient verifies
9. For federation: sending gateway strips forbidden fields per data contract before transmission
10. Receiving hub independently validates incoming data against its own contract
11. All operations logged to append-only audit trail with tamper-detection hashing

---

## What the Framework Secures

| Boundary | What the Framework Does |
|----------|------------------------|
| Browser ↔ Gateway | TLS termination, session binding, CSRF, ABAC |
| Gateway ↔ Agents | Authenticated message routing, header injection, response sanitization |
| Agent ↔ Agent | Ed25519-signed messages, channel-based direct communication |
| Agent ↔ Orchestrator | Mutual authentication, signed registration, token-based auth |
| Hub ↔ Hub (federation) | TLS + Ed25519 message signing, data contracts |

## What the Framework Provides via Opt-in Patterns

| Concern | Pattern | How It Works |
|---------|---------|-------------|
| Data classification | patterns/scope | 5-level scope (public → critical) travels with data |
| Field-level masking | patterns/privacy | Scope-driven masking at enforcement boundaries |
| Consent management | patterns/privacy | Purpose-bound consent records with revocation |
| Data retention / erasure | patterns/privacy | Lineage-tracked cascading erasure |
| Operation gating | patterns/safety | Protection gates based on scope × operation × environment |
| Policy enforcement | patterns/policy + architecture/enforcement | Declarative rules enforced at boundaries |
| Compliance reporting | patterns/governance | Evidence collection and profile-scoped reports |

These are opt-in. The framework provides the primitives; agents
adopt the ones they need. The framework doesn't impose a specific
data model — scope levels are universal and type-agnostic.

---

## Transport Security

### Encryption in Transit

| Boundary | Protocol | Minimum |
|----------|----------|---------|
| Browser ↔ Gateway | TLS 1.2+ (1.3 preferred) | Required in production |
| Gateway ↔ Agents | TLS or mTLS | TLS required; mTLS for zero-trust |
| Agent ↔ Agent (direct) | TLS + Ed25519 message signing | Required |
| Agent ↔ Agent (federation) | TLS + Ed25519 message signing | Required |
| Agent ↔ Storage | Local socket or encrypted connection | Platform-specific |

All inter-component communication uses TLS in production. Development
environments MAY use plaintext HTTP on localhost only.

### Message Integrity

Every message between agents is signed with the sender's Ed25519
private key and verified by the recipient using the sender's public
key (obtained during registration). This ensures:

1. **Authenticity** — The message came from the claimed sender
2. **Integrity** — The message was not modified in transit
3. **Non-repudiation** — The sender cannot deny sending the message

Signing covers the message fields `{from, to, action, payload}`.
The signature is included as a header on every inter-agent request.

### Internal Header Trust

The gateway injects trusted headers when forwarding requests to
agents:

| Header | Content |
|--------|---------|
| `X-Gateway-Session` | Session ID |
| `X-Gateway-User` | Authenticated user ID |
| `X-Gateway-Roles` | User's roles |
| `X-Gateway-Sensitivity` | Route sensitivity level |
| `X-Trace-Id` | Distributed trace correlation |
| `Authorization` | Internal WLT bearer token |

Agents MUST NOT trust these headers from any source other than the
registered gateway. The orchestrator validates that only the gateway
agent sets `X-Gateway-*` headers — any other agent attempting to set
them is rejected.

---

## Authentication Boundaries

### Agent Registration

Agents register with the orchestrator using Ed25519 signed manifests.
The orchestrator:

1. Verifies the manifest signature against the agent's public key
2. Issues a time-limited WLT authentication token
3. Records the agent in the service directory
4. Distributes the agent's public key to other agents that need it

Unregistered agents cannot communicate with any component.

### Gateway Authentication

The application gateway authenticates end users via sessions or
tokens (see auth-session and auth-token patterns). Once authenticated,
the user's identity is injected into requests via internal headers —
agents never see raw credentials.

The admin gateway (see Admin Interface blueprint) uses a completely
separate authentication flow with operator Ed25519 keys and mandatory
MFA.

### Federation Authentication

Hub-to-hub communication requires mutual TLS plus Ed25519 message
signing. Federation peers exchange public keys during a trust
establishment handshake. See the Federation protocol spec for the
full trust model.

---

## Federation Data Boundaries

When messages cross federation boundaries (between Weblisk hubs),
the framework enforces data contracts at the transport level.

### Data Contracts

Federation data contracts (defined in the Federation protocol spec)
control which fields cross boundaries:

```yaml
data_contract:
  user_profile:
    fields:
      display_name: required       # Must be included
      email: forbidden             # Must NOT be transmitted
      avatar_url: permitted        # May be included
      user_id: required
      roles: forbidden             # Internal-only
```

### Cross-Boundary Rules

| Rule | Enforcement |
|------|-------------|
| Forbidden fields stripped before transmission | Sending gateway |
| Receiving hub applies its own validation | Independent check |
| Unrecognized fields are dropped | Protocol-level |

Data contracts are the framework's mechanism for controlling what
crosses trust boundaries. How data is classified *within* a hub is
up to the applications running on that hub.

---

## Audit Trail

The framework provides a built-in audit trail for inter-component
communication:

### What Gets Logged

| Event | Logged By | Detail Level |
|-------|-----------|-------------|
| Agent registration / deregistration | Orchestrator | Full manifest |
| Task dispatch | Domain controller | Task ID, target agent, action |
| Task completion / failure | Domain controller | Task ID, status, duration |
| Gateway route decisions | Gateway | Route, auth decision, user context |
| Federation message send / receive | Gateway | Peer, contract, field list |
| Admin operations | Admin gateway | Operator, action, target, 4-eyes approval |

### What Does NOT Get Logged by the Framework

The framework logs *operations*, not *data content*. Request and
response bodies are NOT included in the audit trail by default.
Agents that need content-level auditing (e.g., logging which user
records were accessed) implement that in their own audit layer.

### Audit Storage

- Audit entries are stored in append-only storage
- Entries include the hash of the previous entry (tamper detection)
- Retained for at least 90 days (configurable)
- Accessible only by admin and auditor roles
- The framework's audit log covers *framework operations* — agents
  add their own application-level audit entries as needed

---

## Response Sanitization

The gateway sanitizes all responses before they reach the browser:

1. Strip internal headers (`X-Gateway-*`, `X-Agent-*`)
2. Strip server identification headers (`Server`, `X-Powered-By`)
3. Ensure no raw error messages leak internal details
4. Set security headers on every response (HSTS, CSP, etc.)

Application-level response filtering (e.g., masking fields based on
user roles) is implemented by the agents or gateway middleware that
the application configures — not by the framework core.

---

## Implementation Notes

- The framework provides two tiers of data security: (1) **transport
  security** (TLS, Ed25519 signing, header trust) which is always on,
  and (2) **data-level security** (scope, policy, privacy, enforcement)
  which is opt-in via the corresponding patterns.
- Agents that handle sensitive data SHOULD adopt patterns/scope to
  classify their data, patterns/privacy for masking and erasure, and
  patterns/policy for access rules. The enforcement architecture
  validates these at boundaries automatically.
- Agents that handle sensitive data SHOULD implement their own
  encryption-at-rest using the Ed25519 key hierarchy (HKDF-derived
  keys) provided by the identity protocol. The framework provides the
  cryptographic primitives; agents decide what to encrypt.
- Federation data contracts (patterns/contract) carry scope metadata.
  When data crosses federation boundaries, the enforcement layer
  validates scope compliance in addition to field-level contracts.
- Error responses from agents are sanitized by the gateway to prevent
  internal details from leaking. Agents SHOULD still avoid including
  sensitive data in error messages as defense in depth.

---

## Types

### EncryptionPolicy

Policy governing encryption-at-rest for agents handling sensitive data.
Agents that opt into data-level security declare this in their config.

```yaml
EncryptionPolicy:
  description: Encryption-at-rest policy for agent-managed data
  fields:
    algorithm:
      type: string
      description: Symmetric encryption algorithm for data at rest
      constraints:
        enum: [aes-256-gcm, xchacha20-poly1305]
        default: aes-256-gcm
    key_derivation:
      type: string
      description: How the encryption key is derived from the agent's Ed25519 key
      constraints:
        enum: [hkdf-sha256, hkdf-sha512]
        default: hkdf-sha256
    classification:
      type: string
      description: Minimum data classification that triggers encryption
      constraints:
        enum: [public, internal, confidential, restricted]
        default: confidential
```

## Configuration

```yaml
data_security:
  tls:
    min_version: "1.3"
    require_in_production: true
    allow_plaintext_localhost: true
  signing:
    algorithm: ed25519
    fields_covered: [from, to, action, payload]
  encryption_at_rest:
    algorithm: aes-256-gcm
    key_derivation: hkdf-sha256
    classification: confidential
  audit:
    retention_days: 90
    tamper_detection: hash-chain
    append_only: true
  response_sanitization:
    strip_headers: ["X-Gateway-*", "X-Agent-*", "Server", "X-Powered-By"]
    strip_raw_errors: true
```

## Verification Checklist

- [ ] All inter-component communication uses TLS in production; plaintext HTTP permitted only on localhost in development
- [ ] Every agent-to-agent message is signed with the sender's Ed25519 key covering {from, to, action, payload}
- [ ] Gateway injects X-Gateway-* headers on forwarded requests and agents reject these headers from any non-gateway source
- [ ] Orchestrator validates that only the registered gateway agent sets X-Gateway-* headers; other agents are rejected
- [ ] Unregistered agents cannot communicate with any component in the system
- [ ] Federation data contracts strip forbidden fields before transmission at the sending gateway
- [ ] Receiving hub independently validates incoming federated data against its own data contract rules
- [ ] Audit entries are stored in append-only storage with hash of previous entry for tamper detection
- [ ] Audit trail is retained for at least 90 days and accessible only by admin and auditor roles
- [ ] Response sanitization strips internal headers (X-Gateway-*, X-Agent-*, Server, X-Powered-By) and raw error messages before reaching the browser
- [ ] Framework audit log records operations (registration, task dispatch, route decisions) but does NOT include request/response body content by default
