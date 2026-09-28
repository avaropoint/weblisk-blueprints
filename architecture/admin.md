<!-- blueprint
type: architecture
name: admin
version: 2.7.0
requires: [protocol/spec, protocol/identity, protocol/types, patterns/principal-identity, architecture/orchestrator, architecture/domain, architecture/lifecycle, architecture/gateway, architecture/client, architecture/threat-model]
platform: any
tier: free
-->

# Weblisk Platform Admin

The operational management layer for a Weblisk deployment. Defines
the admin dashboard, operator roles, and the API surface that enables
humans to monitor, manage, and interact with the orchestrator, agents,
domains, workflows, and federation peers.

This is the **platform admin** — it manages the Weblisk infrastructure
itself (orchestrator, agents, domains, federation, strategies). It is
completely separate from any admin features that applications built
on Weblisk may define for their own purposes.

Applications built on the framework may have their own admin portals
(e.g. a CMS content manager, an e-commerce product dashboard, a
customer support panel). Those are application-level features — they
run through the application gateway as normal routes with appropriate
ABAC policies. They have nothing to do with this blueprint.

Without a platform admin interface, the Weblisk system is a black
box. This blueprint turns it into an observable, manageable system
that operators can confidently run in production.

## Overview

The admin interface is a web-based dashboard that consumes the
orchestrator's existing endpoints (`/v1/services`, `/v1/audit`,
`/v1/approve`, `/v1/strategy`, `/v1/health`) plus new admin-specific
endpoints defined in this blueprint. It provides real-time visibility
into the entire system and is the primary tool for human operators
interacting with a Weblisk deployment.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=2.0.0 <3.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /v1/health
          methods: [POST]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WLToken
          fields_used: [sub, iss, iat, exp, cap, cid, role, type]
        - name: SigningKeyPair
          fields_used: [public_key, private_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/principal-identity
    version: ">=1.6.0 <2.0.0"
    bindings:
      types:
        - name: Attestation
          fields_used: [identity_id, identity_public_key, credential_public_key, hub_id, purpose, device_label, not_after, signature]
        - name: Credential
          fields_used: [credential_public_key, algorithm, form, device_bound, identity_id, attestation, status, last_used_at]
      behaviors:
        - name: credential-attestation
        - name: authentication
        - name: revocation
        # Only for what it refuses: a sign-records credential is never one of
        # a hub's, and a console never holds one
        - name: record-signing
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Strategy
          fields_used: [id, name, targets, status, priority]
        - name: AgentManifest
          fields_used: [name, version, capabilities, public_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=2.0.0 <3.0.0"
    bindings:
      endpoints:
        # The orchestrator-provided groups only. Strategies, approvals,
        # workflows and federation are bound from their own providers — see
        # "The admin API is an aggregate".
        - path: /v1/admin/operators
        - path: /v1/admin/agents
        - path: /v1/admin/overview
          methods: [GET, POST, PUT, DELETE]
        - path: /v1/services
          methods: [POST]
        - path: /v1/audit
          methods: [GET]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: DomainManifest
          fields_used: [name, type, workflows, required_agents]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/lifecycle
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [routes, tls, rate_limits]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/client
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WLS
          fields_used: [sub, sid, roles, sec, mfa]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/threat-model
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ThreatBoundary
          fields_used: [boundary, controls, mitigations]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

The admin interface is a **separate listener** from the application gateway, with
its own TLS entry point, its own session store and its own cookie domain.

```
   Operator browser
         │  separate listener, separate TLS
         ▼
   ┌──────────────────────────┐
   │ ADMIN GATEWAY            │
   │  identity → MFA → role   │
   │  → change gate → audit   │
   └───────────┬──────────────┘
               │ reads the orchestrator's own endpoints
               ▼
   ┌──────────────────────────┐
   │ ORCHESTRATOR             │
   │ services · audit · health│
   └──────────────────────────┘
```

**Responsibilities.** Operator identity lifecycle, multi-factor authentication
without exception, the role hierarchy, the four-eyes change gate for destructive
actions, and the audit trail of every operator action.

**Not responsibilities.** Serving end users — that is `architecture/gateway`, which
shares nothing with this listener. Executing tasks, which is the agents'. Deciding
policy, which is `patterns/policy`.

---

## Responsibilities

### Owns

- Admin gateway process (separate listener, TLS, and domain from application gateway)
- Operator identity lifecycle (registration, role assignment, suspension)
- Operator credentials: one per operator, client and hub, attested by the operator's identity, checked on every request
- Admin dashboard SPA (overview, agents, approvals, workflows, federation, audit)
- Admin API endpoints under `/v1/admin/*`
- Operator token model (WLT with a one-hour TTL, minted with a credential, exact IP binding, two factors required where each key is opened)
- Admin rate limiting and IP allowlist enforcement
- 4-eyes approval for destructive actions

### Does NOT Own

- Orchestrator internals (admin reads orchestrator state via API, does not manage it directly)
- Agent logic or agent lifecycle (admin can deregister, but agents self-govern)
- Application-level admin features (those use the application gateway)
- Client session management (owned by `architecture/client`)
- Federation trust establishment (owned by `protocol/federation`; admin only approves/revokes)

---

## Interfaces

The admin component's public API surface is defined in detail in
[Admin Endpoints](#admin-endpoints) (operator management, system overview,
agent management, domain/workflow management, strategy management,
approval queue, federation management, audit/observability) and
[Admin API Response Shapes](#admin-api-response-shapes).

---

## Error Handling

The operator and credential routes answer with these codes, in `ErrorResponse`
([`protocol/types`](../protocol/types.md#errorresponse)). Each says what the
client does next, so a client acts on the code and never on the message text.
Where the last column names a
[`patterns/principal-identity`](../patterns/principal-identity.md#error-handling)
code, this is its wire form at this surface, and that pattern holds the rule.

An orchestrator enters each code in its central error registry with the HTTP
status given here, which is what `architecture/orchestrator`'s
`error-codes-registered` check looks for. The Category column classes the fault,
as `architecture/content` and `architecture/fabric` do. It is not
`ErrorResponse.category`: there, each of these is `permanent` and not
`retryable`, because the client acts on the code rather than repeating the
request.

| Code | HTTP | Category | When | Behaviour | principal-identity |
|---|---|---|---|---|---|
| `OPERATOR_BOOTSTRAP_REFUSED` | 403 | auth | A registration at a hub with no operator carried no bootstrap secret, or a wrong one | Refuse, write nothing, audit. The caller needs the secret the orchestrator emitted | — |
| `OPERATOR_UNKNOWN` | 401 | auth | No operator of that name here: never registered, or lost with a hub regenerated without its records | Refuse. The client registers again or stops; retrying changes nothing | `identity_unknown` |
| `OPERATOR_NOT_APPROVED` | 403 | auth | The operator is registered and pending | Refuse. Not a failure: the client reports that an admin must approve | — |
| `OPERATOR_REVOKED` | 401 | auth | The operator was removed. A removed operator keeps its record with status `revoked` ([`protocol/types`](../protocol/types.md#operatorstatus)), so removal is never mistaken for a name the hub has not seen | Refuse. Every credential and token resting on it ended with it | — |
| `CREDENTIAL_REQUIRED` | 401 | auth | A route that needs an operator token carrying a `cid` got something else: an operator token with no `cid`, an attestation token anywhere but the attestation route, or an agent or channel token on a `/v1/admin/*` route | Refuse. The client mints an operator token with a credential | — |
| `OPERATOR_SUBJECT_MISMATCH` | 403 | auth | The token's `sub` is not the operator the path names, on a route only that operator may use: an attestation token on another operator's attestation route, or a token without the admin role revoking another operator's credential | Refuse. Log an attestation token's attempt as a security event | — |
| `CREDENTIAL_UNKNOWN` | 401 | auth | The hub holds no credential with this id | Refuse. The client attests a credential | `identity_unknown` |
| `CREDENTIAL_OPERATOR_MISMATCH` | 401 | auth | The credential the token's `cid` names is held by an operator other than the token's `sub` | Refuse. Log as a security event: this hub never issues such a token | — |
| `CREDENTIAL_REVOKED` | 401 | auth | The credential was revoked, by its operator, by an admin, with its operator, or by a change of identity key | Refuse at once, not at the token's expiry. The client attests a new key | `credential_revoked`, `token_credential_revoked` |
| `CREDENTIAL_EXPIRED` | 401 | auth | The attestation's `not_after` has passed | Refuse. The client re-attests, which needs the identity | `attestation_expired` |
| `CREDENTIAL_CHALLENGE_INVALID` | 401 | auth | The nonce was not issued for this credential, was already used or has expired, or the signature does not verify | Refuse and spend the nonce. Log a signature failure as a security event | `replay_detected` |
| `CREDENTIAL_ATTESTATION_INVALID` | 400 | validation | The attestation's signature does not verify under ML-DSA-65 against the operator's recorded key, or the attestation names another identity key | Refuse. Log as a security event | `attestation_invalid`, `algorithm_not_permitted` |
| `CREDENTIAL_FORM_UNSUPPORTED` | 400 | validation | The credential key is not an ML-DSA-65 public key, the one form these routes carry | Refuse. A form principal-identity permits beside it is admitted only by a route that declares its own registration and challenge | — |
| `CREDENTIAL_FOREIGN_HUB` | 400 | validation | The attestation's `hub_id` is not this hub's | Refuse. Log as a security event | `credential_foreign_hub` |
| `CREDENTIAL_IS_IDENTITY_KEY` | 400 | validation | The credential's public key is the operator's identity key | Refuse. Log as a security event | `identity_key_as_credential` |
| `CREDENTIAL_PURPOSE_REFUSED` | 400 | validation | The attestation's `purpose` is `sign-records`. A key that signs records is never a credential a hub mints tokens with | Refuse. Log as a security event. The client attests a separate key to sign in | `credential_purpose_mismatch` |
| `CREDENTIAL_LIFETIME_INVALID` | 400 | validation | `not_after` is not in the future, or is more than 90 days after the hub receives the attestation | Refuse, naming the cap | `attestation_expired`, where `not_after` has passed |
| `CREDENTIAL_PREVIOUSLY_REVOKED` | 409 | conflict | The key was revoked here before | Refuse permanently. Log as a security event | `credential_previously_revoked` |
| `OPERATOR_LAST_ADMINISTRATOR` | 409 | conflict | A request to revoke would end the last active credential of the last active admin. A change of that admin's identity key is not refused | Refuse | `last_administrator` |

`TOKEN_EXPIRED` ([`protocol/types`](../protocol/types.md#error-handling)) still
answers a token past its `exp`. The client mints another with its credential,
which does not ask the identity.

---

## Data Flow

1. Operator browser sends request to admin gateway (`admin.example.com:9443`)
2. Admin gateway runs IP allowlist check — reject if not allowed
3. TLS termination with admin-specific certificate
4. Rate limiting applied (per-operator read/write limits)
5. Operator token (WLT) extracted and verified against orchestrator's public key,
   and the operator, credential and grant it rests on checked live by the
   orchestrator ([Every request checks what its token rests on](#every-request-checks-what-its-token-rests-on))
6. No factor is re-checked here: two were required where the credential was
   attested and where its key was opened to mint this token
   ([Where the second factor is](#where-the-second-factor-is))
7. Role authorization checked against endpoint minimum role
8. Request forwarded to orchestrator's admin API with `X-Operator` and `X-Trace-Id` headers
9. Orchestrator processes request and returns response
10. Admin gateway returns response to operator browser (with `Cache-Control: no-store`)
11. For destructive actions: additional HMAC confirmation and 4-eyes approval before step 8

---

## Admin Gateway Separation

The admin portal is a **completely separate entry point** from the
application gateway. It is NOT an extension of the application
gateway. It is NOT served under the same domain. It does NOT share
session state, authentication flows, or network paths with the
application.

### Why Separate

The application gateway and admin gateway have fundamentally
different threat profiles:

| Concern | Application Gateway | Admin Gateway |
|---------|-------------------|---------------|
| Audience | End users (untrusted, high volume) | Operators (trusted, low volume) |
| Network | Public internet | Private network, VPN, or IP-restricted |
| Auth model | User credentials → session cookie | Operator credential, attested by the operator's ML-DSA-65 identity → operator token |
| Session binding | Device fingerprint + IP/24 | Operator credential + exact IP allowlist |
| MFA | Policy-driven (optional for standard routes) | Always required, no exceptions: at attestation and at every mint, never as a claim in a token |
| Rate limits | High (accommodate user traffic) | Low (operators don't generate burst traffic) |
| Compromise impact | User data exposure | Full system control |
| Domain | `app.example.com` | `admin.example.com` (or `admin.internal:9443`) |
| TLS cert | Public CA certificate | Private CA or separate public cert |

#### Separate access points, shared services

The table above is about **attack surface**, and only about attack surface. It
is not two authentication systems, and it MUST NOT become two.

This blueprint requires [`architecture/gateway`](gateway.md), which requires
`patterns/auth-session`, `patterns/auth-token` and
`patterns/user-management`. OIDC, password verification, credential storage,
session issuance and token minting are specified once and used by both. An
implementation MUST NOT write a second one of any of them for the admin path.

What is separate is the **exposure**: a distinct listener, a distinct domain, a
distinct certificate, no shared cookie domain and no shared session state. That
separation exists so that capability reachable by an operator is not reachable
from a public surface at all — not authorised-and-refused, but absent. A
compromise of the application gateway reaches user data; it does not reach a
listener that is not bound to the public internet.

Stated because the two halves pull in opposite directions and a reader who sees
only one half does the wrong thing with it. Read as "these are different
systems", an implementation duplicates the auth stack and the two copies drift
on the thing that matters most. Read as "these are the same system", an
implementation serves both from one listener and the separation that motivated
the whole design is gone.

**Authorization is also not duplicated, and is also not shared.** The
application gateway evaluates ABAC over a tenant's users and a tenant's
resources. This gateway evaluates operator capabilities over the platform.
Different subjects, different resources, deliberately non-overlapping: a grant
held in a tenant MUST NOT project onto platform administration. Two models
because there are two authorization domains, not because there are two
implementations of one.

### Architecture

```
┌──────────────────────────┐      ┌────────────────────────────┐
│  End-User Browser        │      │  Operator Browser          │
│  (app.example.com)       │      │  (admin.example.com)       │
│                          │      │  VPN / IP allowlist only    │
│  Islands → HTTP → Cookie │      │  SPA → HTTP → ML-DSA-65 Token│
└────────────┬─────────────┘      └──────────────┬─────────────┘
             │                                    │
             ▼                                    ▼
┌────────────────────────┐      ┌──────────────────────────────┐
│  APPLICATION GATEWAY   │      │  ADMIN GATEWAY               │
│  Port 443              │      │  Port 9443 (or separate 443) │
│  Public internet       │      │  Private / IP-restricted     │
│  User sessions (WLS)   │      │  Operator tokens (WLT)       │
│  ABAC policies         │      │  Role hierarchy + MFA always │
│  Data masking          │      │  Full audit trail            │
└────────────┬───────────┘      └──────────────┬───────────────┘
             │                                  │
             │     ┌────────────────────┐       │
             └────►│  ORCHESTRATOR +    │◄──────┘
                   │  AGENT NETWORK     │
                   └────────────────────┘
```

Critical rules:
- The application gateway has NO routes to admin endpoints.
- The admin gateway has NO routes to application endpoints.
- They share the same orchestrator and agent network, but enter
  through different doors with different keys.
- If the application gateway is compromised, the admin gateway is
  unreachable — different network path, different credentials,
  different session model.
- If the admin gateway is compromised, the application continues
  serving users — they are operationally independent.

### Admin Gateway Request Lifecycle

```
1. IP ALLOWLIST CHECK (before any processing)
   ├── Client IP in operator allowlist?
   ├── If not → 403 Forbidden (no response body, no hint)
   └── Log: blocked IP attempt with source address

2. TLS TERMINATION
   ├── Separate TLS certificate from application gateway
   ├── TLS 1.3 preferred (1.2 minimum)
   └── Client certificate validation (optional, for mTLS deployments)

3. RATE LIMITING
   ├── Per-operator: 60 read/min, 20 write/min
   ├── Auth endpoints: 5/min (very restrictive) — the four routes that
   │   issue tokens, credentials/challenge included, since it answers
   │   anyone who names a credential and holds each nonce until it expires
   └── Export endpoints: 5/min

4. OPERATOR AUTHENTICATION
   ├── Skipped for the four routes that issue tokens, which carry none:
   │   operators/register, operators/token, credentials/challenge and
   │   credentials/token. They pass to the orchestrator as they arrived
   ├── Extract token from Authorization: Bearer <WLT>
   ├── Verify WLT signature against orchestrator's public key
   ├── Verify token.type == "operator" — or, on
   │   POST /v1/admin/operators/{name}/credentials alone, "attestation"
   │   with sub equal to {name} (Auth Middleware, below)
   ├── Verify token expiry
   ├── Verify operator IP matches token's bound IP
   ├── The orchestrator checks the operator, the credential named by
   │   token.cid and the grant are live — its records, not the token's word
   └── 401 Unauthorized if any check fails, with the code that says which

5. SECOND FACTOR (always required, never checked per request)
   ├── Required where each key is opened: at attestation, and at every
   │   mint (Where the second factor is). A token carries no claim of it,
   │   and the gateway looks for none
   └── A console's AAL2 session is opened with a one-time code or WebAuthn,
       never a code sent by SMS

6. ROLE AUTHORIZATION
   ├── Check token.role against endpoint's minimum role
   ├── Role hierarchy: admin > operator > auditor > viewer
   └── 403 Forbidden if role insufficient

7. REQUEST FORWARDING
   ├── Forward to orchestrator's admin API
   ├── Internal headers: X-Operator, X-Operator-Role, X-Trace-Id
   └── Response returned to operator browser

8. DESTRUCTIVE ACTION CONFIRMATION (for critical writes)
   ├── Per-request HMAC confirmation (X-Confirm header)
   ├── 4-eyes approval for: deregister agent, revoke federation,
   │   delete operator, key rotation
   └── All actions logged to immutable audit trail
```

### Admin Session Model

Admin sessions are NOT browser sessions (WLS tokens). They use
operator tokens (WLT) with stricter controls:

| Property | Application Session (WLS) | Admin Session (WLT) |
|----------|--------------------------|---------------------|
| Token type | `WLS` (Weblisk Session) | `WLT` (Weblisk Token) |
| Signing key | Gateway's ML-DSA-65 key | Orchestrator's ML-DSA-65 key |
| TTL | 24 hours | 1 hour |
| Idle timeout | 1 hour | None at the hub, where nothing tells use from idle. A console ends a person's tokens when that person's session with it goes idle (`console-credential-use`) |
| IP binding | /24 subnet (allows roaming) | Exact IP (no roaming) |
| MFA | Optional per policy | Always required, at attestation and at every mint ([Where the second factor is](#where-the-second-factor-is)) |
| Cookie | HttpOnly, Secure, SameSite=Strict | HttpOnly, Secure, SameSite=Strict |
| Cookie domain | `app.example.com` | `admin.example.com` |
| Concurrent sessions | Up to 5 per user | One credential per operator per client, each minting its own tokens. Revoking a credential ends every token it minted, at the next request |
| Renewal | Silent sliding window | A new token minted with the credential; the identity is not asked |

### Admin Network Deployment Options

| Mode | Description | Security Level |
|------|------------|----------------|
| **VPN-only** | Admin gateway accessible only through VPN tunnel | Highest — gateway invisible to public internet |
| **IP allowlist** | Admin gateway on public IP but rejects all non-allowlisted sources | High — requires IP management |
| **mTLS** | Admin gateway requires client certificate in addition to operator token | Highest — two-factor at transport layer |
| **Private network** | Admin gateway on internal network only (10.x.x.x) | High — requires network access |

Production deployments SHOULD use VPN-only or mTLS. IP allowlist is
acceptable for small teams with stable IPs. Private network is
acceptable for single-host deployments.

## Design Principles

1. **Read-heavy, write-light** — Most admin interactions are
   observation: viewing agents, reading logs, monitoring workflows.
   Writes are limited to approvals, strategy management, and
   configuration.
2. **ML-DSA-65 operator identity, kept cold** — Operators are identified
   by the same ML-DSA-65 identity system as agents. The identity signs to
   register and to attest a credential, and nothing else. Tokens, with
   admin-scoped capabilities, are minted with the credential.
3. **Offline-capable** — The dashboard is a static SPA that works
   even when the orchestrator is degraded. It shows stale data with
   timestamps rather than failing entirely.
4. **Non-destructive defaults** — Destructive actions (deregister
   agent, revoke federation peer, delete strategy) require
   confirmation, 4-eyes approval, and are logged in the audit trail.
5. **Complete isolation** — The platform admin portal shares no
   network path, no session state, and no authentication flow with
   the application gateway. Application-specific admin features
   built by customers are unrelated — they use the application
   gateway like any other route.

---

## Contracts

The operator flows are declared as behaviours, because what an implementation
must get right about them is a **sequence and a signing input**, not a field
list. A component that serves the operator surface binds these — see
`architecture/orchestrator`, which serves them and until now bound nothing from
this blueprint at all.

```yaml
contracts:
  behaviors:
    - name: operator-registration
      description: Establish an operator record from a signed request
      required: true
      rules:
        - The request MUST carry name, public_key, role, timestamp and signature
        - The signature MUST be verified against the SUBMITTED public key before any record is written
        - A name already held MUST be refused with 409 and the existing record left untouched
        - The timestamp MUST be inside the replay window, and the message MUST be refused on replay
        - Registration MUST be audited whether it succeeds or is refused

    - name: registration-signing-input
      description: What an operator signs when registering
      required: true
      rules:
        - The signed payload MUST be canonicalize({name, public_key, role, timestamp}) per RFC 8785
        - It MUST NOT be the {name, timestamp} challenge the token request uses
        - The public key MUST be inside the signature, so a key cannot be substituted in flight
        - The role MUST be inside the signature, because it is a privilege claim
        - The timestamp sent MUST be the timestamp signed — a second clock read produces a signature over a payload the server never sees

    - name: first-operator-claim
      description: How the first operator of a hub is admitted — by a secret, never by arriving first
      required: true
      rules:
        - An orchestrator whose operator store is empty MUST generate a bootstrap secret of at least 256 bits from a cryptographically secure random source, and emit it once, where only whoever started the orchestrator can read it
        - The bootstrap secret MUST NOT appear in an audit entry or in any response
        - A registration at a hub whose operator store is empty MUST carry the bootstrap secret as bootstrap_secret, and the orchestrator MUST compare it in constant time
        - A registration there with no bootstrap secret, or a wrong one, MUST be refused with OPERATOR_BOOTSTRAP_REFUSED, write no record, and be audited
        - The registration that presents the secret MUST be approved with the admin role, whatever role it asked for
        - Its response MUST carry an attestation token and hub_id, and never an operator token. The first operator obtains operator tokens the way every operator does, with a credential
        - The secret MUST be destroyed when it is claimed, and MUST NOT be issued again while the operator store holds any record. The bootstrap reset in protocol/identity is the one way back
        - The claim MUST be atomic. Of registrations that present the secret concurrently, exactly one is approved, and every other is refused with OPERATOR_BOOTSTRAP_REFUSED
        - An orchestrator that restarts while its operator store is still empty MUST generate a new secret and emit it in place of the last, so a secret read from an earlier start admits nothing
        - Every later registration MUST require an existing admin and MUST NOT return a token
        - A refusal for want of an admin MUST be distinguishable from a refusal for a bad signature, and from a refusal for a missing or wrong bootstrap secret
        - The response MUST state which case occurred, so a caller does not wait for an approval nobody needs to give

    - name: operator-approval
      description: How an operator after the first is admitted
      required: true
      rules:
        - The route `POST /v1/admin/operators/{name}/approve` MUST exist — without it a registration that is not the first can never be completed by anybody
        - It MUST require the `admin` role, because it grants authority
        - The list at `GET /v1/admin/operators` MUST report every operator including `pending` ones, so an admin can see who is waiting
        - Approving an operator already `approved` MUST succeed and change nothing, so a retried approval is not an error
        - Approval MUST NOT return a token — the approved operator attests a credential of their own and mints tokens with it
        - Approval MUST be audited with the name of the operator who granted it

    - name: attestation-token-issuance
      description: What an operator's identity signature obtains — the right to attest, and nothing else
      required: true
      rules:
        - The route `POST /v1/admin/operators/token` MUST require no bearer token
        - The signed payload MUST be canonicalize({name, timestamp}), verified against the STORED public key for that operator, with the timestamp inside the 300-second replay window
        - An operator with no record MUST be refused with OPERATOR_UNKNOWN, a pending one with OPERATOR_NOT_APPROVED and a revoked one with OPERATOR_REVOKED, and each refusal MUST be audited
        - The token it issues MUST have type attestation, carry no capability and no cid, and expire within 300 seconds
        - An attestation token MUST be accepted by `POST /v1/admin/operators/{name}/credentials` for its own subject, refused there for any other operator with OPERATOR_SUBJECT_MISMATCH, and refused by every other route with CREDENTIAL_REQUIRED
        - The response MUST carry hub_id, so the client can name this hub in the attestation it is about to have signed
        - It is the way to a first credential, and is deprecated as a way to an operator token. A hub built before the credential routes issues an operator token here, and a client MAY use one only from a hub that answers the credential routes with 404 or 405

    - name: operator-credential-attestation
      description: Bind a client's credential to an operator's identity at this hub
      required: true
      rules:
        - The route `POST /v1/admin/operators/{name}/credentials` MUST accept an attestation token or an operator token whose subject is the operator named in the path, and nothing else. A token for another operator is refused with OPERATOR_SUBJECT_MISMATCH, and any other kind of token with CREDENTIAL_REQUIRED
        - The attestation MUST verify under ML-DSA-65 against the public key in that operator's OWN record, and its identity_public_key MUST equal that key, or it is refused with CREDENTIAL_ATTESTATION_INVALID. Registration is how this surface records the key principal-identity takes from an invitation
        - Its identity_id MUST be the fingerprint of that key, and its hub_id this hub's hub_id. A different hub_id MUST be refused with CREDENTIAL_FOREIGN_HUB and logged as a security event
        - Its credential_public_key MUST be an ML-DSA-65 public key, or it is refused with CREDENTIAL_FORM_UNSUPPORTED. These routes carry an ML-DSA-65 key-file credential and no other form. A form principal-identity permits beside it, such as a passkey, has its own registration and challenge, and a hub admits it only through a route that declares them
        - Its credential_public_key MUST NOT be the identity public key, or it is refused with CREDENTIAL_IS_IDENTITY_KEY and logged as a security event
        - Its purpose MUST be absent or authenticate. An attestation whose purpose is sign-records MUST be refused with CREDENTIAL_PURPOSE_REFUSED and logged as a security event. A key that signs records never mints a token (patterns/principal-identity, record-signing)
        - Its not_after MUST be in the future and no more than 90 days after the hub receives it, or it is refused with CREDENTIAL_LIFETIME_INVALID
        - A key that was ever revoked at this hub MUST be refused with CREDENTIAL_PREVIOUSLY_REVOKED
        - An attestation for a key the operator already holds as an active credential MUST replace that credential's attestation and keep its id. That is re-attestation
        - The hub MUST store the credential with algorithm ml-dsa-65, form key-file, device_bound false (a key file can be copied, and no authenticator says otherwise) and status active, and return it with its id, the fingerprint of its public key
        - Every attestation MUST be audited with the operator, the credential id and the device_label

    - name: operator-token-issuance
      description: Issue an operator token to a live credential — the ordinary way, and the only way to one
      required: true
      rules:
        - The routes `POST /v1/admin/credentials/challenge` and `POST /v1/admin/credentials/token` MUST require no bearer token — they are what issue them
        - A challenge for a cid this hub holds no credential for MUST be refused with CREDENTIAL_UNKNOWN. For any credential it does hold, whatever its status, it MUST answer with a nonce of at least 128 bits from a cryptographically secure random source, single-use, bound to that cid, expiring within 300 seconds, and this hub's hub_id
        - The token request MUST carry cid, nonce and signature, and the signature MUST verify under the credential's STORED algorithm and public key over exactly these bytes, and never over the nonce alone. The UTF-8 bytes of weblisk/credential-auth/v1, one 0x00 byte, the 64 lowercase hexadecimal characters of hub_id as ASCII, one 0x00 byte, and the nonce's base64url text exactly as the challenge returned it, as ASCII. The nonce is signed as text, never as the bytes it decodes to
        - The nonce MUST be one this hub issued for that cid, unexpired and unused, and the attempt MUST spend it whether or not the signature verifies. Otherwise CREDENTIAL_CHALLENGE_INVALID
        - A token request naming a cid this hub holds no credential for MUST be refused with CREDENTIAL_UNKNOWN
        - Only once the signature has verified may the hub disclose the credential's status or its operator's. The credential MUST be active (else CREDENTIAL_REVOKED) and its attestation's not_after in the future (else CREDENTIAL_EXPIRED), and its operator MUST be approved (else OPERATOR_NOT_APPROVED, or OPERATOR_REVOKED for a removed one)
        - The token MUST have type operator, carry cid, the identity_id of the credential cid names, the operator's role and the capabilities that role carries, and expire one hour after issue and never after the attestation's not_after
        - Role and capabilities MUST come from the stored record, never from the request
        - The response MUST carry the attestation's not_after, so the client can warn before it passes
        - The credential's last_used_at MUST be updated
        - A client MUST sign with the hub_id its credential was attested for, and MUST treat a challenge that answers a different hub_id as a hub it holds no credential for

    - name: token-status-on-use
      description: Every request re-checks what its token rests on
      required: true
      rules:
        - On every request bearing an operator token, the orchestrator MUST look up the operator named by sub and the credential named by cid in its OWN records before the handler runs
        - An operator token without a cid MUST be refused with CREDENTIAL_REQUIRED
        - The request MUST be refused when the operator has no record (OPERATOR_UNKNOWN), is pending (OPERATOR_NOT_APPROVED) or is revoked (OPERATOR_REVOKED), and when the credential is not that operator's (CREDENTIAL_OPERATOR_MISMATCH), is revoked (CREDENTIAL_REVOKED) or its attestation has expired (CREDENTIAL_EXPIRED)
        - The request MUST be authorised against the capabilities the operator's role carries now, and never beyond the token's cap. A role changed since the token was issued takes effect on the next request
        - Removing an operator, revoking a credential or rotating an operator's identity key therefore ends every token resting on it at the next request, not when the token expires
        - An admin gateway in front of the orchestrator MUST NOT stand in for this check. The orchestrator holds the records, and a signature check alone proves only that a token was once issued

    - name: operator-credential-revocation
      description: Withdraw one credential, or every credential an operator holds
      required: true
      rules:
        - The route `DELETE /v1/admin/operators/{name}/credentials/{cid}` MUST be permitted to the operator named in the path and to an admin, and to nobody else. Another operator is refused with OPERATOR_SUBJECT_MISMATCH
        - A revoked credential MUST keep its record with status revoked, and its key MUST never be accepted again
        - Removing an operator MUST set its status to revoked and keep its record, and MUST revoke every credential it holds
        - A change of an operator's identity public key MUST revoke every credential the old key attested
        - A request to revoke the last active credential of the last active admin MUST be refused with OPERATOR_LAST_ADMINISTRATOR
        - A change of that admin's identity key MUST NOT be refused on that ground, and revokes the credential all the same (patterns/principal-identity, revocation)
        - Every revocation MUST be audited with the actor, the credential id and the reason

    - name: console-credential-use
      description: How a console that acts for signed-in people holds and uses their credentials
      required: true
      rules:
        - A console MUST hold a separate credential for each account at each hub, generate its key pair itself, and have it attested by that account's operator identity through the CLI, never by holding the identity itself
        - It MUST ask for not_after 30 days ahead unless the person chooses another value within the 90-day cap, and MUST warn the person when fewer than 7 days remain
        - It MUST use a person's credential only while that person holds a live session with the console at AAL2, and MUST NOT mint a token with it at any other time
        - Work no signed-in person is present for, such as a schedule or a background job, MUST use the console's own service identity and never a person's credential
        - Every agent run MUST use the console's own service identity, whether or not a signed-in person is watching it, and never a person's credential. A credential that runs agents holds no person-only capability (architecture/content, Who may move an entry)
        - It MUST NOT generate, hold or ask an identity to attest a sign-records credential, for anyone. A signature on a record means the person signed it, and a key a console holds signs whenever the console does (patterns/principal-identity, record-signing)
        - It MUST hold an operator token in memory only and never write one anywhere, encrypted or not. What it keeps at rest is the credential key, as an installation secret
        - It MUST discard a person's tokens when that person's session ends, by sign-out, idle or absolute expiry, or the account's revocation, even where exp is later
        - Removing an account from the console MUST delete that account's credential keys. Before it does, it MUST revoke each credential at its hub where it can, with a token minted for a person signed in to the console at AAL2 whom that hub permits to revoke it — the account's own person, or one holding the admin role there
        - Where no such person is signed in, it MUST still delete the key, and MUST report for each hub that the credential stays live there until its not_after unless an admin of that hub revokes it
        - When it drives the CLI to connect, it MUST ask the CLI not to store the token

    - name: operator-roles
      description: The role names and what each may do
      required: true
      rules:
        - The role names are exactly `viewer`, `auditor`, `operator` and `admin`
        - Capabilities MUST be derived from the role, never stored per operator
        - The `operator` role MUST carry `admin:read`, `admin:approve` and `admin:strategy` — it is the role every `operator+` endpoint in this document is gated on
        - Each `content:` capability MUST be carried by the roles the Operator Roles table gives it, and a capability `protocol/types` marks person only by no role a service subject holds
        - Every capability this document names MUST be carried by some role; a capability no role holds is a constant, not a permission
        - The last active admin MUST NOT be removable or demotable
        - A role change MUST be audited with the previous and new role
```

---

## Operator Identity

Operators are human users who manage the Weblisk deployment. They
use the same ML-DSA-65 identity system as agents but with
operator-specific capabilities.

**Scope: this deployment.** The registration flow below binds an operator to ONE
orchestrator. A subject who operates several hubs holds one self-generated
identity, is registered at each hub, and holds a separate credential at each,
attested by that identity. Registration records the identity and its grant at
this hub. It does not create the identity, and it is not a credential. See
[patterns/principal-identity](../patterns/principal-identity.md).

Two consequences worth stating here, because this file is where operators are
defined:

- **Creating a hub grants nothing beyond that hub.** The first-operator
  claim below is a grant recorded in the orchestrator it was made
  against. It is revocable, including revoking the creator, and it confers no
  standing at any other hub. A control plane that provisions hubs therefore
  accumulates grants, not privilege.
- **A directory never authenticates.** Where an external directory or control
  plane lists operators, an orchestrator MUST still verify signatures against the
  public key in its OWN records. Consulting a directory at authentication time
  would make that directory a skeleton key for every deployment trusting it.

### Operator Registration

```
1. Operator generates ML-DSA-65 key pair (via CLI: weblisk operator init)
2. CLI stores the identity where it resolves that identity to live (rule 2 of
   "Bootstrap without a shell", below): the public key, and the private half
   either as a passphrase-encrypted file or held by a secret source
   (protocol/secret-source)
3. Operator registers with orchestrator:
   POST /v1/admin/operators/register
   {
     "name": "alice",
     "public_key": "<ML-DSA-65 public key (base64url)>",
     "role": "admin",
     "timestamp": 1712160000,
     "signature": "<sign(canonicalize({name, public_key, role, timestamp}))>",
     "bootstrap_secret": "<only at a hub with no operator yet>"
   }
4. Orchestrator verifies signature
5. At a hub with no operator, the registration that presents the bootstrap
   secret is approved as admin (Bootstrap Flow, below)
6. Any other registration is pending until an existing admin approves it
7. The operator attests a credential and mints tokens with it (Obtaining a token)
```

#### The registration signing input

The signature is over `canonicalize({name, public_key, role, timestamp})` —
**the whole payload**, not the `{name, timestamp}` challenge the attestation
token request uses. RFC 8785 (JCS), as `protocol/spec` specifies for every
signed payload. `bootstrap_secret` travels beside the signed fields and is not
among them: whoever holds it may claim the hub, which is what it is for.

This MUST be stated exactly, and it was not: this step read
`"<signed registration payload>"` while the token request two sections below
read `"<sign(canonicalize({name, timestamp}))>"`. A generated orchestrator
signed and verified the four-field form; a client signed the two-field form;
the registration was refused with `operator signature verification failed` and
neither side was wrong about anything it had been told.

The four-field form is the correct one and the reason is not symmetry. The
signature must **bind the public key to the name**. Over `{name, timestamp}`
alone the key is unsigned data in a signed request, so anyone able to reach the
endpoint could submit their own public key under any name — and a key
substituted in flight on the registration that presents the bootstrap secret
would take the whole hub. `role` is included for the same reason: it is a
privilege claim and it must not be substitutable in flight.

The timestamp MUST be the one sent in the payload. A client that reads the clock
once to sign and again to build the request produces a signature over a payload
the orchestrator never sees, and it verifies only when both reads land in the
same second — which is a fault that passes locally and fails under load.

### Obtaining a token

Registration establishes an operator. It does not keep them signed in: tokens
expire in an hour, so there MUST be a way to obtain a new one that does not
require registering again, and that way MUST NOT be the operator's identity.

A client reaches a hub with a **credential**: an ML-DSA-65 key pair the client
generates for that hub alone, bound to the operator's identity by an
attestation the identity signs once
([`patterns/principal-identity`](../patterns/principal-identity.md)). The
identity key is cold. It signs to register and to attest, and nothing it signs
is a login. Tokens come from the credential, at a challenge the hub issues, and
the identity is not asked.

```
When a client holds no live credential at a hub — the only steps that need the identity
  client ── sign {name, timestamp} with the identity ──▶ POST /v1/admin/operators/token
         ◀── attestation token (type attestation, 300 s), hub_id
  client ── Attestation, signed by the identity ───────▶ POST /v1/admin/operators/{name}/credentials
         ◀── the credential, and its id

Whenever a token is needed — the identity is not asked
  client ── cid ───────────────────────────────────────▶ POST /v1/admin/credentials/challenge
         ◀── nonce, hub_id, expires_at
  client ── cid, nonce, signature by the credential ───▶ POST /v1/admin/credentials/token
         ◀── operator token (type operator, carries cid, one hour)
```

The behaviours that bind all of this are `attestation-token-issuance`,
`operator-credential-attestation`, `operator-token-issuance`,
`token-status-on-use` and `operator-credential-revocation`, in
[Contracts](#contracts). What follows is the wire form.

#### The identity signs only to attest

`POST /v1/admin/operators/token` is unauthenticated by token because it is how
an operator with no credential here starts. The identity signs the request:

```
POST /v1/admin/operators/token
{
  "name": "alice",
  "timestamp": 1712160000,
  "signature": "<sign(canonicalize({name, timestamp}))>"
}
```

The orchestrator looks the operator up by `name` in its OWN records, never in a
directory, and verifies the signature against the public key there, over
`canonicalize({name, timestamp})` as received, per
[`protocol/spec`](../protocol/spec.md#signing-input). It refuses a `timestamp`
outside the 300-second replay window, and an operator who is not approved — a
registered but unapproved operator is a different fact from an unknown one.

```
200 {
  "token": "<WLT, type attestation>",
  "expires_at": 1712160300,
  "hub_id": "<fingerprint of the orchestrator's first public key>"
}
```

The token does one thing: it submits an attestation for this operator. Every
other route refuses it. So this endpoint is not the authentication by identity
key that [`patterns/principal-identity`](../patterns/principal-identity.md)
forbids: an identity signature here obtains the right to attest, which is the
one thing an identity is for.

**Obtaining an operator token here is deprecated.** A hub built before the
credential routes issues one here. A client MUST use the credential routes
wherever a hub serves them, and MAY accept an operator token from this endpoint
only from a hub that answers `POST /v1/admin/credentials/challenge` with `404`
or `405`.

`hub_id` names this hub as an [`Attestation`](../patterns/principal-identity.md#types)
does: the fingerprint ([`protocol/identity`](../protocol/identity.md#key-fingerprint))
of the first public key the orchestrator signed tokens with. The orchestrator
records it with its own state when it first generates that key, and keeps it
when it rotates the key. So a hub that moves or rotates its key keeps its
hub_id and every credential attested for it, and a client tells a rotation from
a different hub by hub_id alone. A hub regenerated without its state has a new
hub_id and holds no credentials.

#### Attesting a credential

The client generates an ML-DSA-65 key pair for this hub and has the identity sign
an [`Attestation`](../patterns/principal-identity.md#types) for its public half.
The identity signs a typed statement the signer builds itself, never bytes a
caller supplies — [`architecture/cli`](cli.md) gives a console that verb.

```
POST /v1/admin/operators/alice/credentials
Authorization: Bearer <attestation token, or alice's operator token>
{
  "identity_id": "<fingerprint of alice's identity public key>",
  "identity_public_key": "<alice's identity public key>",
  "credential_public_key": "<ML-DSA-65 public key>",
  "hub_id": "<this hub's hub_id>",
  "device_label": "<for people reading a list of credentials>",
  "not_after": 1714752000,
  "signature": "<identity signature over the canonical form of every other field>"
}

200 { "credential": { ... }, "cid": "<fingerprint of credential_public_key>" }
```

**`not_after` is 30 days after attesting by default, is capped at 90, and a
client warns its person when fewer than 7 remain.** The cap is the rotation
interval [`protocol/identity`](../protocol/identity.md#recommended-rotation-schedule)
recommends, and a hub refuses anything longer. The attestation lifetime is the
revocation window for every verifier that is not this hub, so it is kept short.

Re-attesting a key the operator already holds here replaces its attestation and
keeps its id. It may be submitted with that operator's own operator token, so a
client whose credential is still live re-attests with one identity signature and
no attestation token.

#### Minting a token with the credential

```
POST /v1/admin/credentials/challenge
{ "cid": "<credential id>" }

200 { "nonce": "<base64url>", "hub_id": "<this hub's hub_id>", "expires_at": 1712160300 }
```

A challenge for a credential the hub does not hold is refused with
`CREDENTIAL_UNKNOWN`, so a client learns at once that it must attest. For one it
does hold, revoked or expired included, the hub issues a nonce: whether a
credential is still live is told only to its key, at the token request.

```
POST /v1/admin/credentials/token
{
  "cid": "<credential id>",
  "nonce": "<the nonce>",
  "signature": "<credential signature over the bytes below>"
}

    "weblisk/credential-auth/v1" 0x00 <hub_id> 0x00 <nonce>

    <hub_id> is its 64 hex characters and <nonce> its base64url text as the
    challenge returned it, both as ASCII (operator-token-issuance)

200 {
  "token": "<WLT, type operator, carries cid and identity_id>",
  "expires_at": 1712163600,
  "role": "operator",
  "capabilities": ["admin:read", "admin:approve", "admin:strategy"],
  "not_after": 1714752000
}
```

The signed bytes are fixed and domain-separated. A credential never signs a
caller's bytes, and a signature made here cannot be presented as a signature
over a JSON payload, which begins with `{`. The client signs with the `hub_id`
its credential was attested for. A challenge that answers with a different one
is a hub the client holds no credential for.

Neither the challenge nor its `hub_id` is signed by the hub. `hub_id` in the
signed bytes stops a signature made for one hub from being spent at another. It
does not stop an impostor at the hub's address from relaying this hub's
challenge to the client. The transport stops that: HTTPS to the hub's address,
with its certificate verified, which this surface requires everywhere
([Implementation Notes](#implementation-notes)).

Refresh is the same pair of calls. A separate refresh endpoint would need a
valid token to obtain a token, which fails exactly when it is needed — after
expiry.

#### Where the second factor is

The admin surface requires two factors, without exception. A hub verifies
signatures. It cannot see what opened a key, as no verifier of a key-based
authenticator can, so the rule sits where each key is opened, and the hub rests
on it:

- **Attesting.** A person's identity key never rests unencrypted
  ([`protocol/identity`](../protocol/identity.md) rule 1). It signs only once a
  passphrase opens its envelope, or once the secret source that holds it
  answers the person's unlock. An attestation is a key the person has, opened
  by something they know or unlock. It is the multi-factor act a credential
  rests on.
- **Minting.** A credential's signature proves possession of the credential key
  and nothing more. A client MUST keep a person's credential key where it signs
  only after that person's own act: in the `weblisk-key-v1` envelope with `kdf`
  `argon2id`, opened by a passphrase the person types or one a secret source
  they unlock remembers; in a secret source they unlock; or, in a console,
  released only while the person holds a live AAL2 session with it
  (`console-credential-use`). A key in the clear, under `kdf` `none`, or behind
  a source nobody unlocks, such as `file:`, is not a person's credential.
- **Not per request.** A token proves that a live credential minted it within
  the hour, and every request re-checks that credential (below). A token
  carries no claim that a factor was presented, and a gateway MUST NOT look for
  one. The hub could not verify such a claim, so it would be set true on every
  token and would prove nothing.

#### Every request checks what its token rests on

A WLT is self-contained: once issued, nothing about it can be recalled. The
orchestrator holds the operator record, the credential and the grant, so it is
the one party that can end a token before `exp`, and
[`patterns/principal-identity`](../patterns/principal-identity.md) requires it
to. On every request bearing an operator token it looks up the operator named
by `sub` and the credential named by `cid` in its own records before the handler
runs, and authorises against what the operator's role carries **now**.

Removing an operator, revoking a credential or rotating an operator's identity
therefore takes effect on the next request, not an hour later. A client told why
([Error Handling](#error-handling)) knows what to do: attest again, wait for an
approval, or stop.

#### Revoking a credential

`DELETE /v1/admin/operators/{name}/credentials/{cid}?reason=<text>` revokes one
credential. The operator it belongs to may revoke it, and so may an admin. The
identity, the grant and the operator's other credentials are untouched. Removing
an operator revokes all of theirs, and so does a change of their identity key.

A hub refuses a request to revoke the last active credential of its last
active admin, because that would leave nobody able to mint. It does not refuse a
change of that admin's identity key, although that revokes the same credential:
the new identity asks for an attestation token and attests a new one. The
identity is the recovery path for every credential a subject holds
([`patterns/principal-identity`](../patterns/principal-identity.md)).

### The registration response

`POST /v1/admin/operators/register` returns the operator record, and a token
**only when registration also approved the operator** — the first-operator
claim. That token is an attestation token. Otherwise there is no token to give,
and the response says so:

```
200 { "operator": {...}, "status": "approved", "token": "<WLT, type attestation>", "expires_at": ..., "hub_id": ... }
200 { "operator": {...}, "status": "pending" }
```

Stated because it was not, and the omission broke the chain in a way that looked
like success. A generated orchestrator returned the operator record alone; the
CLI stored a token only if the response carried one, so it printed
`[ok] Registered` and saved nothing; `operator token` then reported no token;
and every `/v1/admin/*` call answered `401`. Each component behaved correctly
against what it had been told, and the deployment could not be administered.

**A client MUST NOT infer a token from a successful registration.** It reads
`status`, and asks for an attestation token when none was issued.

### Admitting the operators after the first

The registration flow above ends a second operator at `status: "pending"`, and
says an existing admin must approve them. For a long time nothing said **how**,
and so nothing did: the capability `admin:approve` existed, the status
`approved` existed, and there was no route, no command and no screen that moved
an operator from one to the other. Every generated orchestrator was therefore a
deployment exactly one person could ever administer, and it reported no fault
at any point — registration succeeded, and the operator was told to wait for
something nobody could do.

```
POST /v1/admin/operators/alice/approve
Authorization: Bearer <admin token>
```

The orchestrator MUST:

1. Require the `admin` role. Approval grants authority, so it is not an
   `operator` action, and `admin:approve` is not the capability that carries it
   — that one is for the recommendation queue.
2. Look up the operator by name and refuse an unknown one with `404`.
3. If the operator is already `approved`, succeed and change nothing. Approval
   is a state, not an event, and a retried call MUST NOT fail.
4. Otherwise set status to `approved` and record who approved it.
5. Return the operator record, **and no token**:

```
200 { "operator": {...}, "status": "approved", "approved_by": "bob", "approved_at": ... }
```

The approved operator attests a credential of their own and mints tokens with
it, as any operator does ([Obtaining a token](#obtaining-a-token)). Handing a
token back here would issue a credential to whoever ran the approval rather
than to its subject.

**Refusal is `DELETE /v1/admin/operators/:name`**, which already exists. There
is no separate reject verb, because a rejected registration and a removed
operator leave the deployment in the same state, and two routes to one state
drift.

`GET /v1/admin/operators` MUST list `pending` operators alongside approved
ones. An admin who cannot see who is waiting cannot approve them, and a list
that quietly filters to approved operators makes a waiting colleague look like
a failed registration.

### Operator Roles

| Role | Capabilities | Description |
|------|-------------|-------------|
| **admin** | `admin:*`, and every `content:` capability | Full access — manage operators, agents, federation, strategies, declare and establish content repositories, and declare their replicas |
| **operator** | `admin:read`, `admin:approve`, `admin:strategy`, `content:read`, `content:describe`, `content:write`, `content:propose`, `content:decide`, `content:reconcile` | Day-to-day operations — view everything, approve recommendations, manage strategies, write documents and decide proposals |
| **viewer** | `admin:read`, `content:read`, `content:describe` | Read-only — view dashboards, logs, status and documents. Cannot modify anything |
| **auditor** | `admin:read`, `admin:audit`, `content:read`, `content:describe` | Read-only plus full audit log access with export capability |

A role is held by an operator, and an operator is a person, so a role may carry
a capability [`protocol/types`](../protocol/types.md) marks *person only*.
`content:write`, `content:decide`, `content:replicate` and `content:connect`
reach a person this way and reach a service by no route: a service subject is
granted no role that carries one
([`patterns/principal-identity`](../patterns/principal-identity.md),
`service-subject-constraints`).

`operator` sits between `auditor` and `admin` deliberately: it is the role that
does the day-to-day work — approving recommendations and managing strategies —
without the authority to admit, remove or re-role other operators. Every
endpoint above marked `operator+` means this role.

This table once disagreed with the `operator-roles` behaviour block, which
listed three roles and omitted `operator`. A generated orchestrator resolved the
contradiction the defensible way — it followed the contract block, wrote down
that it had, and produced a three-value enum. The result was that
`admin:approve` and `admin:strategy` were declared as constants and granted to
**no role whatsoever**, so every `operator+` route was reachable only by a full
admin, and the middle tier of the permission model existed on paper only.
Nothing failed; the deployment simply had one fewer role than it was designed
to have. Contradicting yourself in a specification does not produce an error —
it produces confident, well-commented, wrong code.

### Operator Token

Operator tokens use the same WLT format as agent tokens, with the `cid`,
`identity_id`, `type` and `role` claims
[`protocol/identity`](../protocol/identity.md#payload-claims) declares:

```json
{
  "sub": "alice",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712163600,
  "cap": ["admin:read", "admin:approve", "admin:strategy"],
  "cid": "<id of the credential that obtained it>",
  "identity_id": "<fingerprint of alice's identity public key>",
  "role": "operator",
  "type": "operator"
}
```

**Operator tokens have a one-hour TTL,** and never outlive the attestation of the
credential that obtained them. A client mints the next one with that credential,
and the identity is not asked. `cid` names the credential, which is what lets
the orchestrator end the token early
([Every request checks what its token rests on](#every-request-checks-what-its-token-rests-on)).
`identity_id` is the identity that credential was attested by. A component that
records who acted records it, never `sub`, which is the operator's name.

`type` is `operator` for a token that administers, and `attestation` for the
one an identity signature obtains. An attestation token carries `sub`, `iss`,
`iat`, `exp` and `type`, no `cap` and no `cid`, and lives at most 300 seconds.
`role` records the role at issue. A request is authorised against the role the
operator holds when it arrives (`token-status-on-use`).

### A console holds a credential, never a token

A **console** is a client that acts for people who sign in to it rather than
for the person at a terminal — Studio is one. It holds credentials for many
people at many hubs, and that is exactly what makes a token at rest in it
dangerous: an operator token carries `admin:*` for an admin, and whoever holds
it may replay it. So a console keeps the thing that can **ask**, and never the
**answer**.

- **One credential per account per hub.** The console generates the key pair and
  has the account's operator identity attest it through the CLI
  ([`architecture/cli`](cli.md), `weblisk operator attest`). The console never
  holds the identity: [`protocol/secret-source`](../protocol/secret-source.md#a-console-never-holds-the-secrets-of-an-identity-it-acts-for)
  says so, and says how the console keeps the credential's key at rest.
- **Only while the person is there.** A person's credential is used only while
  that person has a live session with the console at AAL2 — NIST SP 800-63B
  authenticator assurance level 2, proof of two distinct factors such as a
  password and a one-time code. A token is discarded when the session that
  minted it ends, even if its `exp` is later.
- **Nobody present means a service.** A schedule or a background job uses the
  console's own service identity, a service subject under
  [`patterns/principal-identity`](../patterns/principal-identity.md), and never a
  person's credential.
- **An agent always runs as a service.** Every agent run uses the console's own
  service identity, whether or not anybody is watching it. A credential that
  runs agents holds no capability `protocol/types` marks *person only*, so an
  agent's change to a document reaches the tenant as a proposal a person
  decides ([`architecture/content`](content.md#who-may-move-an-entry)). A person
  who dispatched the run is named on it as the person it acted for, never by
  lending it their credential.
- **Tokens stay in memory.** A console never writes an operator token anywhere,
  encrypted or not. A console that drives the CLI to connect asks it not to
  store one either (`--no-store`).

`console-credential-use` in [Contracts](#contracts) is the rule.

---

## Admin Endpoints

All admin endpoints are served under `/v1/admin/` and require a valid
operator token.

### The admin API is an aggregate

Each group below is **specified and served by the component that owns the
state**. The admin service holds `admin:` capabilities, calls those endpoints,
and composes one operator surface behind its own enforcement. It is not the owner
of the data and it is not co-located with any single provider.

| Group | Provider | Present when |
|---|---|---|
| Operator management | Orchestrator | always — it is the trust anchor and holds operator records |
| Agent management | Orchestrator | always |
| Audit | Orchestrator | always |
| System overview | aggregate | always, with absent providers reported absent |
| Domain & workflow | Domain controllers | a domain controller is deployed |
| Strategies, approvals, observations | Lifecycle Agent | the lifecycle agent is deployed |
| Federation | Federation layer | the deployment federates |

An earlier version of this section read *"These extend the orchestrator's
existing endpoint set"*, which cannot be satisfied.
[`architecture/lifecycle`](lifecycle.md) states that *"Strategies, approvals, and
feedback are managed entirely by the Lifecycle Agent — not the orchestrator"*,
and workflows belong to domain controllers. An orchestrator asked to serve
`/v1/admin/strategies` would have to own state another component owns.

**An endpoint whose provider is not deployed MUST report itself unavailable, and
MUST NOT return an empty result.** An empty approval queue and an absent approval
system are different facts, and a console that renders them identically tells an
operator the system is quiet when it is simply not there.

### Operator Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/operators/register` | POST | — | Register new operator (the first presents the bootstrap secret) |
| `/v1/admin/operators/token` | POST | — | Obtain an attestation token by signing `{name, timestamp}` with the identity. Deprecated as a way to an operator token |
| `/v1/admin/credentials/challenge` | POST | — | Issue a single-use nonce for a credential |
| `/v1/admin/credentials/token` | POST | — | Obtain an operator token by signing the nonce with the credential |
| `/v1/admin/operators/:name/credentials` | POST | the operator | Attest a credential (an attestation token, or the operator's own token) |
| `/v1/admin/operators/:name/credentials` | GET | viewer+ | List an operator's credentials, revoked included |
| `/v1/admin/operators/:name/credentials/:cid` | DELETE | the operator, or admin | Revoke one credential |
| `/v1/admin/operators` | GET | admin | List all operators |
| `/v1/admin/operators/:name` | GET | viewer+ | Get operator details |
| `/v1/admin/operators/:name` | DELETE | admin | Remove an operator: its status becomes `revoked`, its record stays, and its credentials are revoked |
| `/v1/admin/operators/:name/approve` | POST | admin | Admit a registered operator (see *Admitting the operators after the first*) |
| `/v1/admin/operators/:name/role` | PUT | admin | Change operator role |

### System Overview

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/overview` | GET | viewer+ | System summary — agents, domains, workflows, health |
| `/v1/admin/metrics` | GET | viewer+ | Aggregated system metrics |

### Agent Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/agents` | GET | viewer+ | List all agents with status, type, metrics |
| `/v1/admin/agents/:name` | GET | viewer+ | Full agent detail — manifest, metrics, recent tasks |
| `/v1/admin/agents/:name/deregister` | POST | admin | Force-deregister an agent |
| `/v1/admin/agents/:name/metrics` | GET | viewer+ | Agent performance metrics history |

### Domain & Workflow Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/domains` | GET | viewer+ | List domains with status, required agent availability |
| `/v1/admin/domains/:name` | GET | viewer+ | Domain detail — workflows, agents, recent executions |
| `/v1/admin/workflows` | GET | viewer+ | List all workflow executions (paginated) |
| `/v1/admin/workflows/:id` | GET | viewer+ | Workflow execution detail — phases, timing, output |

### Strategy Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/strategies` | GET | viewer+ | List strategies with progress |
| `/v1/admin/strategies` | POST | operator+ | Create a new strategy |
| `/v1/admin/strategies/:id` | GET | viewer+ | Strategy detail with linked observations |
| `/v1/admin/strategies/:id` | PUT | operator+ | Update strategy targets or priority |
| `/v1/admin/strategies/:id` | DELETE | admin | Archive a strategy |

### Approval Queue

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/approvals` | GET | viewer+ | List pending recommendations |
| `/v1/admin/approvals/batch` | POST | operator+ | Approve or reject multiple recommendations |
| `/v1/admin/approvals/:id` | GET | viewer+ | Recommendation detail with diff preview |
| `/v1/admin/approvals/:id` | POST | operator+ | Approve or reject single recommendation |

### Federation Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/federation/peers` | GET | viewer+ | List federation peers with trust tier, status |
| `/v1/admin/federation/peers/:name` | GET | viewer+ | Peer detail — capabilities, data contracts, metrics |
| `/v1/admin/federation/peers/:name/revoke` | POST | admin | Revoke trust relationship |
| `/v1/admin/federation/pending` | GET | operator+ | List pending peering requests |
| `/v1/admin/federation/pending/:id` | POST | admin | Accept or reject peering request |
| `/v1/admin/federation/contracts` | GET | viewer+ | List active data contracts |

### Audit & Observability

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/audit` | GET | auditor+ | Full audit log with filtering |
| `/v1/admin/audit/export` | GET | auditor | Export audit log as JSON or CSV |
| `/v1/admin/observations` | GET | viewer+ | Browse observation history |
| `/v1/admin/observations/trends` | GET | viewer+ | Trend data for strategy metrics |

---

## Admin Dashboard

The dashboard is a static single-page application served by the
admin gateway at the admin domain root (`/`). It is built with the
Weblisk client-side framework and communicates exclusively through
the admin API endpoints. The dashboard is NOT served by the
orchestrator or the application gateway — it is served by the
admin gateway process.

### Dashboard Pages

#### Overview (`/admin/`)

The landing page shows system health at a glance:

```
┌─────────────────────────────────────────────────────────┐
│  Weblisk Admin — acme-corp                              │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Agents  │  Domains │ Workflows│ Approval │  Federation │
│   8 ● ●  │   3 ●    │  12 today│  5 pending│  2 peers   │
│  online  │  online  │  2 failed│          │  1 pending  │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                                                         │
│  System Health: 94/100  ████████████████████░░  ▲ +2    │
│                                                         │
│  Active Strategies                                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Improve organic traffic    ██████████░░  67%    │    │
│  │ Reduce page load time      ████████████░  82%   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  Recent Activity                                        │
│  10:30  seo-audit completed — 3 recommendations         │
│  10:25  health-check — all endpoints healthy            │
│  10:15  content-audit — 5 files analyzed                │
│  09:45  peering request from partner-corp (pending)     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Agents (`/admin/agents`)

Table of all registered agents with real-time status:

| Column | Description |
|--------|-------------|
| Name | Agent name (linked to detail) |
| Type | `domain`, `work`, `infrastructure` |
| Status | `online` ●, `degraded` ●, `offline` ● |
| Version | Agent version |
| Uptime | Time since last registration |
| Tasks (24h) | Task count in last 24 hours |
| Avg Latency | Average task execution time |
| Last Seen | Timestamp of last health check |

#### Agent Detail (`/admin/agents/:name`)

- Full manifest display
- Performance metrics graph (tasks/hour, latency p50/p95/p99)
- Recent task execution history
- Error log
- Behavioral fingerprint + change history
- Deregister button (admin only, with confirmation)

#### Approval Queue (`/admin/approvals`)

List of pending recommendations with inline approve/reject:

| Column | Description |
|--------|-------------|
| Priority | `critical` 🔴, `high` 🟠, `medium` 🟡, `low` 🟢 |
| Agent | Recommending agent |
| Target | File or resource |
| Summary | One-line description |
| Diff | Preview of proposed change |
| Actions | Approve / Reject buttons |

Supports batch operations: select multiple → approve all / reject all.

#### Workflows (`/admin/workflows`)

Workflow execution history with phase-level detail:

```
Workflow: seo-audit (execution exec-a1b2c3)
Status: completed ✓
Duration: 8.5s
Started: 2026-04-25 10:30:00

Phases:
  scan          ████████████████  1.2s  ✓  seo-analyzer
  analyze       ████████████████  3.8s  ✓  seo-analyzer
  accessibility ████████████████  1.5s  ✓  a11y-checker
  report        ████████████████  2.0s  ✓  seo-analyzer

Output: 12 findings, 5 recommendations
```

#### Federation (`/admin/federation`)

- Peer list with trust tier, jurisdiction, capabilities, expiry
- Pending peering requests with approve/reject
- Data contract viewer
- Cross-boundary audit trail
- Key rotation history

#### Audit Log (`/admin/audit`)

Filterable, searchable audit log:

| Filter | Options |
|--------|---------|
| Actor | Any agent, operator, or `orchestrator` |
| Action | `register`, `deregister`, `task`, `channel`, `approve`, `strategy`, `federation` |
| Time range | Last hour, 24h, 7d, 30d, custom |
| Target | Agent name or resource |

Supports export to JSON and CSV for compliance.

---

## Admin API Response Shapes

### GET /v1/admin/overview

```json
{
  "deployment": "acme-corp",
  "version": "1.0.0",
  "uptime": 86400,
  "agents": {
    "total": 8,
    "online": 7,
    "degraded": 1,
    "offline": 0,
    "by_type": {"domain": 3, "work": 3, "infrastructure": 2}
  },
  "domains": {
    "total": 3,
    "online": 3,
    "degraded": 0
  },
  "workflows": {
    "today": 12,
    "succeeded": 10,
    "failed": 2,
    "running": 0
  },
  "approvals": {
    "pending": 5,
    "accepted_24h": 12,
    "rejected_24h": 2
  },
  "federation": {
    "peers": 2,
    "pending_requests": 1,
    "federated_tasks_24h": 34
  },
  "strategies": {
    "active": 2,
    "completed": 1
  },
  "health_score": 94,
  "timestamp": 1712160000
}
```

### GET /v1/admin/agents

```json
{
  "agents": [
    {
      "name": "seo-analyzer",
      "type": "agent",
      "version": "1.0.0",
      "status": "online",
      "registered_at": 1712073600,
      "last_seen": 1712159900,
      "metrics": {
        "tasks_24h": 45,
        "avg_latency_ms": 2300,
        "error_rate": 0.02,
        "observations": 120,
        "recommendations": 38
      }
    }
  ],
  "pagination": {
    "next_cursor": "",
    "has_more": false
  }
}
```

### GET /v1/admin/workflows

```json
{
  "executions": [
    {
      "id": "exec-a1b2c3",
      "workflow_name": "seo-audit",
      "domain_name": "seo",
      "task_id": "task-d4e5f6",
      "status": "completed",
      "phases": [
        {"phase_name": "scan", "agent_name": "seo-analyzer", "status": "completed", "duration_ms": 1200},
        {"phase_name": "analyze", "agent_name": "seo-analyzer", "status": "completed", "duration_ms": 3800},
        {"phase_name": "accessibility", "agent_name": "a11y-checker", "status": "completed", "duration_ms": 1500},
        {"phase_name": "report", "agent_name": "seo-analyzer", "status": "completed", "duration_ms": 2000}
      ],
      "started_at": 1712159400,
      "completed_at": 1712159409,
      "duration_ms": 8500
    }
  ],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true
  }
}
```

### GET /v1/admin/operators/{name}/credentials

Every credential the operator's identity attested at this hub, revoked and
expired included, so a person can tell which device a credential is before
revoking it. Each entry is the stored
[`Credential`](../patterns/principal-identity.md#types) with its `cid`, and the
attestation's `device_label` and `not_after` lifted out for reading.

```json
{
  "credentials": [
    {
      "cid": "<fingerprint of credential_public_key>",
      "device_label": "console on build-01",
      "algorithm": "ml-dsa-65",
      "form": "key-file",
      "device_bound": false,
      "status": "active",
      "not_after": 1714752000,
      "last_used_at": 1712160000
    }
  ]
}
```

---

## Operator Storage

The orchestrator stores operator records alongside agent records:

### Store: Operators

**Owner:** Orchestrator
**Durability:** MUST survive restarts

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutOperator | `(op Operator) → error` | Create or update operator |
| GetOperator | `(name string) → (Operator, error)` | Retrieve by name |
| RevokeOperator | `(name string) → error` | Set status `revoked`, keeping the record. The name is not reused |
| ListOperators | `() → ([]Operator, error)` | List all operators, revoked included |

### Store: Credentials

**Owner:** Orchestrator
**Durability:** MUST survive restarts. A revoked credential is kept, so its key
is never accepted again

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutCredential | `(c Credential) → error` | Create a credential, or replace an active one's attestation |
| GetCredential | `(id string) → (Credential, error)` | Retrieve by id, the fingerprint of its public key |
| ListCredentials | `(identityID string) → ([]Credential, error)` | Every credential one identity attested here, revoked included |
| RevokeCredential | `(id string) → error` | Set status revoked, keeping the record |

`Credential` is [`patterns/principal-identity`](../patterns/principal-identity.md)'s
type. A challenge nonce is not stored here: it lives at most 300 seconds, and an
orchestrator MAY keep it in memory only, so a restart discards the outstanding
ones and a client asks again.

### Operator Record

The record is [`protocol/types`](../protocol/types.md#operator)'s `Operator`,
and its status is `pending`, `approved` or `revoked`
([`OperatorStatus`](../protocol/types.md#operatorstatus)). It holds no token:
nothing a hub issues is stored by the hub, and a credential is a record of its
own, above.

---

## Bootstrap Flow

When an orchestrator starts with no registered operators:

```
1. Orchestrator starts and detects empty operator store
2. It generates a bootstrap secret and emits it once, where only whoever
   started it can read it: on its console, and on a host in
   .weblisk/bootstrap, readable only by the user it runs as
3. It prints how to claim it:
   "Run: weblisk operator init && weblisk operator register --bootstrap <file>"
4. The first POST /v1/admin/operators/register that carries the secret is
   approved as admin, and the secret is destroyed
5. That operator receives an attestation token, attests a credential, and mints
   operator tokens with it
6. Subsequent operator registrations require admin approval
```

This is secure because:
- Reaching the endpoint first confers nothing. Only the secret admits, and it
  was emitted only to whoever started the orchestrator
  ([`patterns/principal-identity`](../patterns/principal-identity.md), *Bootstrap
  is trust-on-first-use*, is the rule this satisfies)
- The window closes when the secret is claimed, and does not reopen while any
  operator record exists
- All subsequent operators require explicit admin approval
- The bootstrap event is permanently recorded in the audit log

`first-operator-claim` in [Contracts](#contracts) is the rule. A tool that
starts the orchestrator itself, as `weblisk tenant create` does, reads the
secret from where it was emitted and claims it in the same action.

### Bootstrapping and connecting are different acts

They were conflated once, and the conflation is worth naming because it reads
as a small thing and is not.

**Bootstrap** creates a hub: generate it, build it, start it, and establish its
first operator. It needs the tenant's filesystem, because it is producing the
tenant. It is necessarily local to wherever that tenant is being built.

**Connect** presents a credential to a hub that is already running. It needs an
ADDRESS and an operator identity, and nothing else — no workspace selected, no
project directory on the caller's machine, no run state some tool happened to
record. A hub on another host, in a container, or started by something other
than the tool now connecting to it MUST be reachable on exactly the same terms
as one in the next directory.

A console that required a local project directory in order to connect made
"connect" mean "connect to a hub I built here". That inverts the relationship
the whole architecture rests on: a console is a CLIENT of a hub, over the hub's
own services, and a client that needs the server's filesystem is not a client.

Connecting therefore has three outcomes, and they MUST be told apart:

| Outcome | When | What it means |
|---|---|---|
| **connected** | a token was issued | proceed |
| **pending approval** | the hub knows this operator, or refuses to register a new one unauthenticated, and will not issue a token | **not a failure.** The first operator of a hub is admitted by the bootstrap secret; every later one requires an existing admin. Somebody joining an established hub waits, and the report MUST name who can act |
| **unreachable** | nothing answered, or the hub does not serve the token endpoint | a fault, and the report MUST distinguish "no hub there" from "a hub that cannot issue tokens" |

The last row matters. A hub that predates
`POST /v1/admin/operators/token` answers `404` or `405`, and reporting that as
"pending approval" tells somebody to wait for an approval that is never coming.
An implementation MUST NOT collapse a missing endpoint into an authorisation
state.

**Asking for a token before attempting registration is required, not an
optimisation.** A client that holds a credential at the hub mints with it; one
that holds none asks for an attestation token, and the answer says whether the
hub knows this operator. A hub that already knows the operator needs no
registration. At a hub with no operators, a registration without the bootstrap
secret is refused, so connecting never claims a hub; only presenting the secret
does.

### Bootstrap without a shell

Step 3 above tells a person to run two commands. A console provisioning a
tenant on behalf of a signed-in user has no shell to run them in, and
[`protocol/identity`](../protocol/identity.md) already names this case: *"a
runtime without [a terminal] cannot, and a specification that says prompt has
excluded it."*

The same steps MAY therefore be driven by one gated action instead of a person.
Nothing about the trust model changes: the first operator is still admitted
by presenting the bootstrap secret, every later one still requires an existing
admin, and the bootstrap is still recorded in the audit log. What changes is
who types.

Four rules govern it, and each exists because its absence is a disclosure:

1. **The passphrase MUST NOT be a command-line argument.** `argv` is readable by
   every process on the machine — `ps` shows it, `/proc/<pid>/cmdline` shows it,
   and a shell usually records it. It arrives on a channel that does not echo,
   persist or log it; a password field over TLS is such a channel, and stdin is
   how it reaches the process.

2. **The operator key location MUST be parameterisable, and MUST be derived
   from the subject by ONE mechanism.** One machine may serve several operator
   identities, and a console with more than one signed-in account cannot share a
   single key file: the second account would use the first account's identity or
   overwrite it. An identity belongs to a subject, not to a machine and not to a
   tenant.

   Parameterising it is not enough on its own. A location is a path, and if
   every caller works out its own path then the rule exists in as many places as
   there are callers — a console derived one privately, and anything else
   driving the CLI had to reproduce it by hand. The CLI MUST accept an identity
   by label and resolve the location itself, and MUST be able to report where a
   given identity lives, so a caller can ask instead of deriving. An explicit
   path remains accepted and outranks the label, because an operator who gives
   one means it.

   That label is NOT the operator's name, and the two MUST NOT be collapsed
   into one argument. The name is hub-facing — recorded in the orchestrator's
   audit log and shown to other operators — while the label selects which key on
   this machine signs. A console signs in an account whose id may be an email
   and registers it on a hub under a chosen display name; merging them forces
   one to become the other. `architecture/cli` names the first `--name` and the
   explicit path `--keys-dir`.

   The label MUST NOT appear verbatim in the path: an account id may be an
   email, and an email in a directory name is a disclosure to anything that can
   list the parent.

3. **Provisioning MUST reuse an existing identity rather than replace one.** A
   subject holds one identity and a separate credential at each hub, attested by
   that identity, so minting a new key while provisioning a second tenant would
   silently orphan
   the grant every earlier tenant recorded. A passphrase that does not open an
   existing identity is an error, not a reason to generate another.

4. **Provisioning MUST be re-runnable.** A console retrying after a network
   error must not be told the tenant is broken by the step that already
   succeeded. Already-registered is reported as already-registered, and the
   action proceeds to obtain a token.

Nothing it obtains persists except a credential's key. The passphrase is
discarded with the process, per [`protocol/identity`](../protocol/identity.md)
rule 4, and a console holds its tokens in memory
([A console holds a credential, never a token](#a-console-holds-a-credential-never-a-token)).

---

## Types

```yaml
types:

  OperatorAuth:
    description: The conditions under which an operator may authenticate to the admin surface
    fields:
      operator_key:
        type: string
        format: base64url
        description: The operator's identity public key, against which registration and attestations are verified. Tokens are minted with credentials, never with this key
      mfa_required:
        type: bool
        description: Whether a second factor is required. The admin surface requires one without exception, where each key is opened — see Where the second factor is — and never as a claim in a token
      ip_allowlist:
        type: array
        items: string
        description: Networks the operator may authenticate from. An empty list means no network restriction, which is a decision rather than a default
```

---

## Security


```yaml
security:
  trust_model:
    description: |
      The admin surface is a separate listener from the application gateway,
      sharing no session store and no cookie domain, so compromising one does not
      reach the other. Every request is authenticated by a token minted with a
      credential the operator's identity attested, re-checked against the
      orchestrator's records, and authorised against a role; multi-factor
      authentication is required without exception, where the identity key
      and the credential key are opened, because an operator credential is the
      most valuable one in a deployment. The identity key signs to register and
      to attest, and is never a login.

  boundaries:
    - boundary: Operator browser → Admin gateway. A separate TLS entry point,
        authenticated per request against the orchestrator's key
    - boundary: Admin gateway → Orchestrator. Reads the orchestrator's own
        endpoints; it does not reach past them into an agent or a store
    - boundary: Operator role → Action. Every endpoint declares a minimum role,
        checked before the handler runs
    - boundary: Destructive action → Effect. Crossed only through the change
        gate, by approvers who are distinct principals

  enforcement:
    - rule: Every admin endpoint requires a verified operator token, except
        registration, the attestation token request and the two credential
        routes that issue tokens. Attesting a credential also accepts an
        attestation token for the same operator
      mechanism: Admin auth middleware verifies the token against the
        orchestrator's public key and checks `type == operator` before dispatch
    - rule: A token is refused as soon as what it rests on is withdrawn
      mechanism: The orchestrator looks up the operator and the credential named
        by the token on every request, and authorises against the role the
        operator holds now
    - rule: An endpoint is refused to a role below its declared minimum
      mechanism: Role compared against the endpoint's requirement; 403 rather
        than a partial result
    - rule: The auditor role cannot approve or mutate
      mechanism: Auditor carries viewer permissions plus audit read, and no
        approval or management capability — it is a branch of the hierarchy
        rather than a rank within it
    - rule: Multi-factor authentication cannot be disabled
      mechanism: An identity key signs only once its passphrase or its secret
        source opens it (protocol/identity rule 1), and a client keeps a
        credential key only where it signs after the person's own act. No
        configuration removes either
    - rule: A destructive action requires a second approver
      mechanism: The change gate holds the action pending, with ordered
        approvers who must differ from the requester
    - rule: Every admin action is attributable
      mechanism: Audit records operator, action, target and time before the
        action takes effect
```
### Auth Middleware

All `/v1/admin/*` endpoints go through admin auth middleware, except
`POST /v1/admin/operators/register`, `POST /v1/admin/operators/token`,
`POST /v1/admin/credentials/challenge` and `POST /v1/admin/credentials/token`:

```
1. Extract token from Authorization: Bearer <token>
2. Verify token against orchestrator's public key
3. Check token.type == "operator" — or, on the attestation route only,
   "attestation" for the operator named in the path. Any other type, or none,
   is CREDENTIAL_REQUIRED, and an attestation token for another operator is
   OPERATOR_SUBJECT_MISMATCH
4. Check the operator named by sub and the credential named by cid are live
   in the orchestrator's own records (token-status-on-use)
5. Check the role the operator holds now against the endpoint's minimum
6. On failure → 401 or 403, with the code from Error Handling
7. On success → pass operator claims to handler
```

### Role Hierarchy

```
admin > operator > auditor > viewer
```

An admin can do everything an operator can do, and so on. The `auditor`
role is a special branch — it has viewer permissions plus full audit
log access, but cannot approve recommendations or manage strategies.

### Audit Trail

Every admin action is logged:

```json
{
  "id": "audit-abc123",
  "timestamp": 1712160000,
  "actor": "alice",
  "actor_type": "operator",
  "action": "approve",
  "target": "rec-001",
  "detail": "Approved recommendation: update title tag on index.html",
  "ip": "192.168.1.100"
}
```

### Rate Limiting

Admin endpoints SHOULD be rate-limited:
- Read endpoints: 60 requests/minute per operator
- Write endpoints: 20 requests/minute per operator
- Export endpoints: 5 requests/minute per operator

---

## Implementation Notes

- The admin SPA is served as static files embedded in the admin
  gateway binary (or from a KV store on Cloudflare). It is NOT
  served by the orchestrator or the application gateway.
- The admin gateway is a separate process from the application
  gateway. In Go deployments, it is a separate binary. In
  Cloudflare deployments, it is a separate Worker.
- The SPA uses the Weblisk client-side framework for UI components
- WebSocket connection to `/v1/admin/ws` for real-time status updates
  (agent status changes, new approvals, workflow completions)
- All admin API responses include `Cache-Control: no-store` to prevent
  caching of sensitive operational data
- The admin interface MUST work over HTTPS in production. HTTP is
  NEVER permitted, even in development (use self-signed certs).
- The admin gateway and application gateway MUST NOT share a TLS
  certificate, cookie domain, session store, or network listener.
- Admin gateway logs are classified as Confidential (level 2) and
  are stored separately from application gateway logs.
- The orchestrator distinguishes between requests from the
  application gateway (X-Gateway-* headers) and requests from the
  admin gateway (X-Operator-* headers). It MUST reject
  X-Operator-* headers from the application gateway and
  X-Gateway-* headers from the admin gateway.

## Verification Checklist
- [ ] Authentication services — OIDC, password verification, credential storage, session issuance, token minting — are used from `patterns/auth-*` and `patterns/user-management` and are not reimplemented for the admin path
- [ ] The admin listener, domain, certificate, cookie domain and session store are all distinct from the application gateway's; nothing is shared between them
- [ ] A grant held within a tenant confers no platform administrative capability
- [ ] Connecting to a hub requires only its address and an operator identity — no local project directory and no recorded run state
- [ ] A token is requested BEFORE any registration is attempted
- [ ] A hub that refuses to register a new operator unauthenticated is reported as pending approval, naming who can act, and not as a failure
- [ ] A hub that does not serve the token endpoint is reported as such, never as pending approval
- [ ] Connecting is idempotent: running it against a hub that already knows the operator issues a token and changes nothing else
- [ ] A passphrase supplied as a command-line argument is REFUSED, and the refusal names stdin as the alternative
- [ ] The operator key location is parameterisable, so two signed-in accounts on one machine hold separate identities
- [ ] Provisioning against an existing identity reuses it; a passphrase that does not open it is an error and no new key is generated
- [ ] Provisioning is re-runnable: an already-registered operator proceeds to obtain a token rather than failing
- [ ] The passphrase is never written to disk, and a console never writes an operator token anywhere
- [ ] `POST /v1/admin/operators/token` issues an attestation token (`type` `attestation`, no `cap`, no `cid`, at most 300 seconds, with `hub_id`) to an approved operator who signs `{name, timestamp}` with their identity key, and every route but `POST /v1/admin/operators/{name}/credentials` refuses that token with `CREDENTIAL_REQUIRED`
- [ ] The signature is verified against the public key in the orchestrator's OWN operator record, never a directory
- [ ] A token request outside the 300-second replay window is refused
- [ ] A token request for a pending operator is refused with 403 `OPERATOR_NOT_APPROVED`, distinctly from an unknown operator (`OPERATOR_UNKNOWN`)
- [ ] Registration that also approves returns an attestation token, `hub_id` and `status: approved`; registration that does not returns `status: pending` and no token
- [ ] An expired operator token is replaced by a new challenge answered with the credential, without re-registering and without the identity
- [ ] `POST /v1/admin/credentials/token` issues an operator token carrying `cid`, expiring one hour after issue and never after the attestation's `not_after`, only for a signature by the stored credential key over `weblisk/credential-auth/v1`, 0x00, `hub_id` as its 64 hex characters, 0x00 and the base64url text of a nonce this hub issued for that credential
- [ ] A hub that rotates its orchestrator key answers every challenge with the `hub_id` it had before, and every credential attested for that `hub_id` still mints
- [ ] A nonce from `POST /v1/admin/credentials/challenge` is spent by the first token request that presents it, whether or not the signature verifies, and a revoked or expired credential's status is disclosed only after its signature verifies
- [ ] An attestation whose `hub_id` is not this hub's, whose credential key is not an ML-DSA-65 key, whose credential key is the identity key, whose `not_after` has passed or is more than 90 days away, or whose key was revoked here before is refused with `CREDENTIAL_FOREIGN_HUB`, `CREDENTIAL_FORM_UNSUPPORTED`, `CREDENTIAL_IS_IDENTITY_KEY`, `CREDENTIAL_LIFETIME_INVALID` or `CREDENTIAL_PREVIOUSLY_REVOKED`
- [ ] An attestation with `purpose` `sign-records` is refused with `CREDENTIAL_PURPOSE_REFUSED`, is stored as no credential, and a challenge for its key answers `CREDENTIAL_UNKNOWN`
- [ ] A console holds no key attested with `purpose` `sign-records`, for any account
- [ ] Removing an operator, or revoking one of its credentials, refuses its next request with `OPERATOR_REVOKED` or `CREDENTIAL_REVOKED` without waiting for its token to expire
- [ ] A removed operator keeps its record with status `revoked`, and a request naming it is refused with `OPERATOR_REVOKED`, never `OPERATOR_UNKNOWN`
- [ ] The sole admin's change of identity key revokes their credentials and is not refused with `OPERATOR_LAST_ADMINISTRATOR`; the new identity then attests a credential and mints
- [ ] A role lowered after a token was issued limits that token from its next request
- [ ] An operator token without `cid` is refused with `CREDENTIAL_REQUIRED`
- [ ] A console uses a person's credential only while that person has a live AAL2 session with it, uses its own service identity for work nobody is present for, and discards a person's tokens when their session ends
- [ ] A console runs every agent under its own service identity, including a run a signed-in person is watching, and never under a person's credential
- [ ] An operator token carries `identity_id`, the `identity_id` of the credential its `cid` names
- [ ] A `viewer` token carries `content:read` and `content:describe` and no other `content:` capability, and an `operator` token carries `content:write` and `content:decide`
- [ ] An `admin` token carries `content:replicate` and `content:connect`, an `operator` token carries neither, and no token minted for a service subject carries either
- [ ] Removing an account from a console deletes its credential keys, revokes each credential first with the token of a signed-in person that hub permits to revoke it where there is one, and otherwise reports each credential live at its hub until its `not_after`

- [ ] Admin gateway is a separate process/listener from the application gateway with its own TLS certificate and domain
- [ ] Admin gateway rejects requests from IPs not in the operator allowlist before any processing (403, no body)
- [ ] The first operator is approved as admin only on presenting the bootstrap secret; a registration at an empty hub without it, or with a wrong one, is refused with `OPERATOR_BOOTSTRAP_REFUSED` and writes nothing; subsequent operators require existing admin approval
- [ ] The bootstrap secret is destroyed when claimed, never appears in a response or an audit entry, and is not issued again while any operator record exists
- [ ] Two registrations presenting the bootstrap secret at once admit exactly one admin, and a restart before the claim replaces the emitted secret
- [ ] Admin tokens are WLTs with a one-hour TTL and exact IP binding, and a console ends a person's tokens when that person's session with it goes idle
- [ ] Two factors are required with no exception, where each key is opened: an identity key signs only once its passphrase or its secret source opens it, and a client keeps a credential key only in the `weblisk-key-v1` envelope, in a secret source, or behind a console session at AAL2, never in the clear. No gateway checks a factor claim in a token
- [ ] Role hierarchy admin > operator > auditor > viewer is enforced server-side on every /v1/admin/* endpoint
- [ ] Destructive actions (deregister agent, revoke federation, delete operator) require 4-eyes approval and X-Confirm HMAC
- [ ] Application gateway returns 404 for any request to /v1/admin/* paths
- [ ] `GET /v1/admin/overview` returns agent counts, domain status, workflow stats, approval counts, and health score — with any figure whose provider is not deployed reported as unavailable rather than zero
- [ ] Each admin endpoint group is served by the component that owns its state; the admin service composes them and owns none of them
- [ ] An admin endpoint whose provider is not deployed reports itself unavailable and never returns an empty result
- [ ] All admin API responses include Cache-Control: no-store header
- [ ] Admin auth middleware verifies `type` is `operator`, checks that the operator and credential the token names are live, and checks the role the operator holds now against the endpoint minimum
- [ ] Bootstrap event (first operator registration) is permanently recorded in the audit log
- [ ] WebSocket /v1/admin/ws provides real-time status updates for agent changes, approvals, and workflow completions
- [ ] Admin gateway and application gateway share NO session state, cookie domain, or network listener
