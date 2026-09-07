<!-- blueprint
type: architecture
name: admin
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/domain, architecture/lifecycle, architecture/gateway, architecture/client, architecture/threat-model]
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
    version: ">=1.0.0 <2.0.0"
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
        - name: SigningKeyPair
          fields_used: [public_key, private_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WLT
          fields_used: [sub, iss, iat, exp, cap, role, type]
        - name: AgentManifest
          fields_used: [name, version, capabilities, public_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
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
    bindings:
      types:
        - name: Strategy
          fields_used: [id, name, targets, status, priority]
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

## Responsibilities

### Owns

- Admin gateway process (separate listener, TLS, and domain from application gateway)
- Operator identity lifecycle (registration, role assignment, suspension)
- Admin dashboard SPA (overview, agents, approvals, workflows, federation, audit)
- Admin API endpoints under `/v1/admin/*`
- Operator token model (WLT with 4-hour TTL, exact IP binding, mandatory MFA)
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

## Data Flow

1. Operator browser sends request to admin gateway (`admin.example.com:9443`)
2. Admin gateway runs IP allowlist check — reject if not allowed
3. TLS termination with admin-specific certificate
4. Rate limiting applied (per-operator read/write limits)
5. Operator token (WLT) extracted and verified against orchestrator's public key
6. MFA validation enforced (always required)
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
| Auth model | User credentials → session cookie | Operator ML-DSA-65 key → operator token |
| Session binding | Device fingerprint + IP/24 | Operator key + exact IP allowlist |
| MFA | Policy-driven (optional for standard routes) | Always required, no exceptions |
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
   ├── Auth endpoints: 5/min (very restrictive)
   └── Export endpoints: 5/min

4. OPERATOR AUTHENTICATION
   ├── Extract token from Authorization: Bearer <WLT>
   ├── Verify WLT signature against orchestrator's public key
   ├── Verify token.type == "operator"
   ├── Verify token expiry (4-hour TTL, not 24-hour)
   ├── Verify operator IP matches token's bound IP
   └── 401 Unauthorized if any check fails

5. MFA VALIDATION (always required, not policy-optional)
   ├── Verify token.mfa == true
   ├── If false → 403 with X-MFA-Required: true
   └── MFA must be TOTP or WebAuthn (no SMS)
       (a WebAuthn passkey MAY instead be the primary credential —
        see patterns/principal-identity)

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
| TTL | 24 hours | 4 hours |
| Idle timeout | 1 hour | 30 minutes |
| IP binding | /24 subnet (allows roaming) | Exact IP (no roaming) |
| MFA | Optional per policy | Always required |
| Cookie | HttpOnly, Secure, SameSite=Strict | HttpOnly, Secure, SameSite=Strict |
| Cookie domain | `app.example.com` | `admin.example.com` |
| Concurrent sessions | Up to 5 per user | 1 per operator (new login kills old) |
| Renewal | Silent sliding window | Explicit re-auth after TTL |

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
2. **ML-DSA-65 operator identity** — Operators authenticate using the
   same ML-DSA-65 identity system as agents. The orchestrator issues
   operator tokens with admin-scoped capabilities.
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

    - name: first-operator-auto-approval
      description: How the first operator of a hub is admitted
      required: true
      rules:
        - A hub with no operators MUST approve its first registration and issue a token
        - Every later registration MUST require an existing admin and MUST NOT return a token
        - A refusal for want of an admin MUST be distinguishable from a refusal for a bad signature
        - The response MUST state which case occurred, so a caller does not wait for an approval nobody needs to give

    - name: operator-approval
      description: How an operator after the first is admitted
      required: true
      rules:
        - The route `POST /v1/admin/operators/{name}/approve` MUST exist — without it a registration that is not the first can never be completed by anybody
        - It MUST require the `admin` role, because it grants authority
        - The list at `GET /v1/admin/operators` MUST report every operator including `pending` ones, so an admin can see who is waiting
        - Approving an operator already `approved` MUST succeed and change nothing, so a retried approval is not an error
        - Approval MUST NOT return a token — the approved operator obtains their own from `POST /v1/admin/operators/token`
        - Approval MUST be audited with the name of the operator who granted it

    - name: operator-token-issuance
      description: Issue a short-lived operator token
      required: true
      rules:
        - The endpoint MUST require no bearer token — it is what issues them
        - The signed payload MUST be canonicalize({name, timestamp})
        - The signature MUST be verified against the STORED public key for that operator
        - Role and capabilities MUST come from the stored record, never from the request
        - An unknown or unapproved operator MUST be refused and audited

    - name: operator-roles
      description: The role names and what each may do
      required: true
      rules:
        - The role names are exactly `viewer`, `auditor`, `operator` and `admin`
        - Capabilities MUST be derived from the role, never stored per operator
        - The `operator` role MUST carry `admin:read`, `admin:approve` and `admin:strategy` — it is the role every `operator+` endpoint in this document is gated on
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
identity and a separate credential attested by each hub — the registration below
is then how one of those credentials is established, not how the subject's
identity is created. See
[patterns/principal-identity](../patterns/principal-identity.md).

Two consequences worth stating here, because this file is where operators are
defined:

- **Creating a hub grants nothing beyond that hub.** The first-operator
  auto-approval below is a grant recorded in the orchestrator it was made
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
2. CLI stores keys in ~/.weblisk/keys/operator.key and operator.pub
3. Operator registers with orchestrator:
   POST /v1/admin/operators/register
   {
     "name": "alice",
     "public_key": "<ML-DSA-65 public key (base64url)>",
     "role": "admin",
     "signature": "<sign(canonicalize({name, public_key, role, timestamp}))>"
   }
4. Orchestrator verifies signature

#### The registration signing input

The signature is over `canonicalize({name, public_key, role, timestamp})` —
**the whole payload**, not the `{name, timestamp}` challenge the token request
uses. RFC 8785 (JCS), as `protocol/spec` specifies for every signed payload.

This MUST be stated exactly, and it was not: this step read
`"<signed registration payload>"` while the token request two sections below
read `"<sign(canonicalize({name, timestamp}))>"`. A generated orchestrator
signed and verified the four-field form; a client signed the two-field form;
the registration was refused with `operator signature verification failed` and
neither side was wrong about anything it had been told.

The four-field form is the correct one and the reason is not symmetry. The
signature must **bind the public key to the name**. Over `{name, timestamp}`
alone the key is unsigned data in a signed request, so anyone able to reach the
endpoint could submit their own public key under any name — and at a hub with no
operators yet, the first such registration is auto-approved as its bootstrap
admin. `role` is included for the same reason: it is a privilege claim and it
must not be substitutable in flight.

The timestamp MUST be the one sent in the payload. A client that reads the clock
once to sign and again to build the request produces a signature over a payload
the orchestrator never sees, and it verifies only when both reads land in the
same second — which is a fault that passes locally and fails under load.
5. If this is the FIRST operator → auto-approve (bootstrap)
6. If not first → requires approval from existing admin
7. Orchestrator issues operator token with admin capabilities
```

### Obtaining a token

Registration establishes an operator. It does not keep them signed in: tokens
expire in four hours, so there MUST be a way to obtain a new one that does not
require registering again.

`POST /v1/admin/operators/token` is that way, and it is **unauthenticated by
token because it is what issues them**. The operator's private key is the
credential:

```
POST /v1/admin/operators/token
{
  "name": "alice",
  "timestamp": 1712160000,
  "signature": "<sign(canonicalize({name, timestamp}))>"
}
```

The orchestrator MUST:

1. Look up the operator by `name` in its OWN records — never in a directory.
2. Verify the signature against the public key in that record, over
   `canonicalize({name, timestamp})` as received, per
   [`protocol/spec`](../protocol/spec.md#signing-input).
3. Refuse a `timestamp` outside the 300-second replay window.
4. Refuse an operator whose status is not approved, with `403` — a registered
   but unapproved operator is a different fact from an unknown one.
5. Issue a token carrying that operator's role and capabilities.

```
200 {
  "token": "<WLT>",
  "expires_at": 1712174400,
  "role": "operator",
  "capabilities": ["admin:read", "admin:approve", "admin:strategy"]
}
```

Refresh is the same call. A separate refresh endpoint would need a valid token
to obtain a token, which fails exactly when it is needed — after expiry.

### The registration response

`POST /v1/admin/operators/register` returns the operator record, and a token
**only when registration also approved the operator** — the first-operator
bootstrap. Otherwise there is no token to give, and the response says so:

```
200 { "operator": {...}, "status": "approved", "token": "<WLT>", "expires_at": ... }
200 { "operator": {...}, "status": "pending" }
```

Stated because it was not, and the omission broke the chain in a way that looked
like success. A generated orchestrator returned the operator record alone; the
CLI stored a token only if the response carried one, so it printed
`[ok] Registered` and saved nothing; `operator token` then reported no token;
and every `/v1/admin/*` call answered `401`. Each component behaved correctly
against what it had been told, and the deployment could not be administered.

**A client MUST NOT infer a token from a successful registration.** It reads
`status`, and calls the token endpoint when none was issued.

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
200 { "operator": {...}, "status": "approved", "approved_by": "lloyd", "approved_at": ... }
```

The approved operator obtains their own token by signing the challenge at
`POST /v1/admin/operators/token`, as any operator does. Handing a token back
here would issue a credential to whoever ran the approval rather than to its
subject.

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
| **admin** | `admin:*` | Full access — manage operators, agents, federation, strategies |
| **operator** | `admin:read`, `admin:approve`, `admin:strategy` | Day-to-day operations — view everything, approve recommendations, manage strategies |
| **viewer** | `admin:read` | Read-only — view dashboards, logs, status. Cannot modify anything |
| **auditor** | `admin:read`, `admin:audit` | Read-only plus full audit log access with export capability |

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

Operator tokens use the same WLT format as agent tokens with
operator-specific claims:

```json
{
  "sub": "alice",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712174400,
  "cap": ["admin:read", "admin:approve", "admin:strategy"],
  "role": "operator",
  "type": "operator"
}
```

Operator tokens have a 4-hour TTL. The CLI refreshes them
automatically on each command.

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
| `/v1/admin/operators/register` | POST | — | Register new operator (first is auto-approved) |
| `/v1/admin/operators/token` | POST | — | Obtain an operator token by signing a challenge |
| `/v1/admin/operators` | GET | admin | List all operators |
| `/v1/admin/operators/:name` | GET | viewer+ | Get operator details |
| `/v1/admin/operators/:name` | DELETE | admin | Remove an operator |
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
| DeleteOperator | `(name string) → error` | Remove operator |
| ListOperators | `() → ([]Operator, error)` | List all operators |

### Operator Record

```yaml
types:
  Architecture:
    fields:
      name:
        name: Name
        type: string
        description: "Operator identifier"
      public_key:
        name: PublicKey
        type: string
        description: "base64url-encoded ML-DSA-65 public key"
      role:
        name: Role
        type: string
        description: "`admin`, `operator`, `viewer`, `auditor`"
      token:
        name: Token
        type: string
        description: "Current auth token"
      registered_at:
        name: RegisteredAt
        type: int64
        description: "Unix epoch seconds"
      last_seen:
        name: LastSeen
        type: int64
        description: "Last authenticated request"
      status:
        name: Status
        type: string
        description: "`active`, `suspended`"
```

---

## Bootstrap Flow

When an orchestrator starts with no registered operators:

```
1. Orchestrator starts and detects empty operator store
2. Orchestrator prints to console:
   "No operators registered. The first operator to register
    will be auto-approved as admin."
   "Run: weblisk operator init && weblisk operator register"
3. First POST /v1/admin/operators/register is auto-approved
4. Operator receives admin token
5. Subsequent operator registrations require admin approval
```

This is secure because:
- The orchestrator is typically on a private network during initial setup
- The first operator MUST have physical/network access to the machine
- All subsequent operators require explicit admin approval
- The bootstrap event is permanently recorded in the audit log

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
| **pending approval** | the hub knows this operator, or refuses to register a new one unauthenticated, and will not issue a token | **not a failure.** The first operator of a hub is auto-approved; every later one requires an existing admin. Somebody joining an established hub waits, and the report MUST name who can act |
| **unreachable** | nothing answered, or the hub does not serve the token endpoint | a fault, and the report MUST distinguish "no hub there" from "a hub that cannot issue tokens" |

The last row matters. A hub that predates
`POST /v1/admin/operators/token` answers `404` or `405`, and reporting that as
"pending approval" tells somebody to wait for an approval that is never coming.
An implementation MUST NOT collapse a missing endpoint into an authorisation
state.

**Asking for a token before attempting registration is required, not an
optimisation.** A hub that already knows the operator needs no registration —
and registering first against a hub with NO operators would silently make the
caller's identity the bootstrap admin of a tenant somebody else runs.

### Bootstrap without a shell

Step 2 above tells a person to run two commands. A console provisioning a
tenant on behalf of a signed-in user has no shell to run them in, and
[`protocol/identity`](../protocol/identity.md) already names this case: *"a
runtime without [a terminal] cannot, and a specification that says prompt has
excluded it."*

The same steps MAY therefore be driven by one gated action instead of a person.
Nothing about the trust model changes: the first operator is still
auto-approved, every later one still requires an existing admin, and the
bootstrap is still recorded in the audit log. What changes is who types.

Four rules govern it, and each exists because its absence is a disclosure:

1. **The passphrase MUST NOT be a command-line argument.** `argv` is readable by
   every process on the machine — `ps` shows it, `/proc/<pid>/cmdline` shows it,
   and a shell usually records it. It arrives on a channel that does not echo,
   persist or log it; a password field over TLS is such a channel, and stdin is
   how it reaches the process.

2. **The operator key location MUST be parameterisable.** One machine may serve
   several operator identities, and a console with more than one signed-in
   account cannot share a single key file: the second account would use the
   first account's identity or overwrite it. An identity belongs to a subject,
   not to a machine and not to a tenant.

3. **Provisioning MUST reuse an existing identity rather than replace one.** A
   subject holds one identity and a separate credential attested by each hub, so
   minting a new key while provisioning a second tenant would silently orphan
   the grant every earlier tenant recorded. A passphrase that does not open an
   existing identity is an error, not a reason to generate another.

4. **Provisioning MUST be re-runnable.** A console retrying after a network
   error must not be told the tenant is broken by the step that already
   succeeded. Already-registered is reported as already-registered, and the
   action proceeds to obtain a token.

A token is the only thing that persists. The passphrase is discarded with the
process, per [`protocol/identity`](../protocol/identity.md) rule 4.

---

## Security

### Auth Middleware

All `/v1/admin/*` endpoints (except operator registration) go through
admin auth middleware:

```
1. Extract token from Authorization: Bearer <token>
2. Verify token against orchestrator's public key
3. Check token.type == "operator"
4. Check token.role against endpoint's minimum role requirement
5. On failure → 401 or 403
6. On success → pass operator claims to handler
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
- [ ] The passphrase is never written to disk; only the token is
- [ ] `POST /v1/admin/operators/token` issues a token to an approved operator who signs `{name, timestamp}` with their private key
- [ ] The signature is verified against the public key in the orchestrator's OWN operator record, never a directory
- [ ] A token request outside the 300-second replay window is refused
- [ ] A token request for a pending operator is refused with 403, distinctly from an unknown operator
- [ ] Registration that also approves returns a token and `status: approved`; registration that does not returns `status: pending` and no token
- [ ] A four-hour-old token can be replaced without re-registering

- [ ] Admin gateway is a separate process/listener from the application gateway with its own TLS certificate and domain
- [ ] Admin gateway rejects requests from IPs not in the operator allowlist before any processing (403, no body)
- [ ] Operator registration auto-approves the first operator as admin; subsequent operators require existing admin approval
- [ ] Admin sessions use WLT tokens with 4-hour TTL, 30-minute idle timeout, exact IP binding, and max 1 concurrent session
- [ ] MFA (TOTP or WebAuthn) is always required for admin session creation — no exceptions
- [ ] Role hierarchy admin > operator > auditor > viewer is enforced server-side on every /v1/admin/* endpoint
- [ ] Destructive actions (deregister agent, revoke federation, delete operator) require 4-eyes approval and X-Confirm HMAC
- [ ] Application gateway returns 404 for any request to /v1/admin/* paths
- [ ] `GET /v1/admin/overview` returns agent counts, domain status, workflow stats, approval counts, and health score — with any figure whose provider is not deployed reported as unavailable rather than zero
- [ ] Each admin endpoint group is served by the component that owns its state; the admin service composes them and owns none of them
- [ ] An admin endpoint whose provider is not deployed reports itself unavailable and never returns an empty result
- [ ] All admin API responses include Cache-Control: no-store header
- [ ] Admin auth middleware verifies token.type == "operator" and checks role against endpoint minimum
- [ ] Bootstrap event (first operator registration) is permanently recorded in the audit log
- [ ] WebSocket /v1/admin/ws provides real-time status updates for agent changes, approvals, and workflow completions
- [ ] Admin gateway and application gateway share NO session state, cookie domain, or network listener
