<!-- blueprint
type: architecture
name: data-security
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/federation, architecture/gateway, architecture/observability]
platform: any
-->

# Data Security Architecture

Specification for how the Weblisk framework secures data as it moves
between components — agents, orchestrators, gateways, and federated
peers. This defines the **transport and boundary security** that the
framework provides by default.

The Weblisk framework itself does not capture, store, or process
personal data, payment information, health records, or any other
application-specific sensitive data. The framework moves messages
between agents. What those messages *contain* — and how that content
is classified, masked, encrypted, or governed — is the responsibility
of the agents and applications built on the platform.

Agents that handle sensitive data (PII, PCI-DSS, HIPAA, etc.) are
responsible for their own data classification, field-level masking,
compliance controls, and encryption-at-rest strategies. The framework
provides the secure transport; applications provide the data handling.

## What the Framework Secures

| Boundary | What the Framework Does |
|----------|------------------------|
| Browser ↔ Gateway | TLS termination, session binding, CSRF, ABAC |
| Gateway ↔ Agents | Authenticated message routing, header injection, response sanitization |
| Agent ↔ Agent | Ed25519-signed messages, channel-based direct communication |
| Agent ↔ Orchestrator | Mutual authentication, signed registration, token-based auth |
| Hub ↔ Hub (federation) | TLS + Ed25519 message signing, data contracts |

## What the Framework Does NOT Do

| Concern | Responsibility |
|---------|---------------|
| Data classification (PII, financial, health) | Application / agents |
| Field-level masking or redaction | Application / agents |
| Encryption-at-rest key hierarchy | Application / agents |
| GDPR, CCPA, HIPAA, PCI-DSS compliance | Application / agents |
| Data retention and deletion policies | Application / agents |
| Data residency and jurisdiction rules | Application / agents |

These are application-layer concerns. Agents that need them implement
them. The framework doesn't impose a classification scheme because
different applications have fundamentally different data models.

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

- The framework secures the *transport* — encrypted channels, signed
  messages, authenticated identities, audited operations. Applications
  secure the *data* — classification, masking, compliance, retention.
- Agents that handle sensitive data SHOULD implement their own
  encryption-at-rest using the Ed25519 key hierarchy (HKDF-derived
  keys) provided by the identity protocol. The framework provides the
  cryptographic primitives; agents decide what to encrypt.
- The gateway's ABAC policy engine can be used by applications to
  implement role-based data access rules, but the policies themselves
  are application-defined, not framework-defined.
- Federation data contracts are enforced by both the sending and
  receiving gateways — defense in depth at trust boundaries.
- Error responses from agents are sanitized by the gateway to prevent
  internal details from leaking. Agents SHOULD still avoid including
  sensitive data in error messages as defense in depth.

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
