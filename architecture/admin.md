<!-- blueprint
type: architecture
name: admin
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/domain, architecture/lifecycle, architecture/gateway, architecture/browser-session, architecture/threat-model]
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
          methods: [GET]
      types:
        - name: AgentManifest
          fields_used: [name, version, capabilities, public_key]
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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/admin/*
          methods: [GET, POST, PUT, DELETE]
        - path: /v1/services
          methods: [GET]
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

  - blueprint: architecture/browser-session
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
- Browser session management (owned by `architecture/browser-session`)
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
| Auth model | User credentials → session cookie | Operator Ed25519 key → operator token |
| Session binding | Device fingerprint + IP/24 | Operator key + exact IP allowlist |
| MFA | Policy-driven (optional for standard routes) | Always required, no exceptions |
| Rate limits | High (accommodate user traffic) | Low (operators don't generate burst traffic) |
| Compromise impact | User data exposure | Full system control |
| Domain | `app.example.com` | `admin.example.com` (or `admin.internal:9443`) |
| TLS cert | Public CA certificate | Private CA or separate public cert |

### Architecture

```
┌──────────────────────────┐      ┌────────────────────────────┐
│  End-User Browser        │      │  Operator Browser          │
│  (app.example.com)       │      │  (admin.example.com)       │
│                          │      │  VPN / IP allowlist only    │
│  Islands → HTTP → Cookie │      │  SPA → HTTP → Ed25519 Token│
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
| Signing key | Gateway's Ed25519 key | Orchestrator's Ed25519 key |
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
2. **Ed25519 operator identity** — Operators authenticate using the
   same Ed25519 identity system as agents. The orchestrator issues
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

## Operator Identity

Operators are human users who manage the Weblisk deployment. They
use the same Ed25519 identity system as agents but with
operator-specific capabilities.

### Operator Registration

```
1. Operator generates Ed25519 key pair (via CLI: weblisk operator init)
2. CLI stores keys in ~/.weblisk/keys/operator.key and operator.pub
3. Operator registers with orchestrator:
   POST /v1/admin/operators/register
   {
     "name": "alice",
     "public_key": "<hex Ed25519 public key>",
     "role": "admin",
     "signature": "<signed registration payload>"
   }
4. Orchestrator verifies signature
5. If this is the FIRST operator → auto-approve (bootstrap)
6. If not first → requires approval from existing admin
7. Orchestrator issues operator token with admin capabilities
```

### Operator Roles

| Role | Capabilities | Description |
|------|-------------|-------------|
| **admin** | `admin:*` | Full access — manage operators, agents, federation, strategies |
| **operator** | `admin:read`, `admin:approve`, `admin:strategy` | Day-to-day operations — view everything, approve recommendations, manage strategies |
| **viewer** | `admin:read` | Read-only — view dashboards, logs, status. Cannot modify anything |
| **auditor** | `admin:read`, `admin:audit` | Read-only plus full audit log access with export capability |

### Operator Token

Operator tokens use the same WLT format as agent tokens with
operator-specific claims:

```json
{
  "sub": "alice",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712246400,
  "cap": ["admin:read", "admin:approve", "admin:strategy"],
  "role": "operator",
  "type": "operator"
}
```

Operator tokens have a 24-hour TTL. The CLI refreshes them
automatically on each command.

---

## Admin Endpoints

All admin endpoints are served under `/v1/admin/` and require a valid
operator token. These extend the orchestrator's existing endpoint set.

### Operator Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/operators/register` | POST | — | Register new operator (first is auto-approved) |
| `/v1/admin/operators` | GET | admin | List all operators |
| `/v1/admin/operators/:name` | GET | viewer+ | Get operator details |
| `/v1/admin/operators/:name` | DELETE | admin | Remove an operator |
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

| Field | Type | Description |
|-------|------|-------------|
| Name | string | Operator identifier |
| PublicKey | string | Hex-encoded Ed25519 public key |
| Role | string | `admin`, `operator`, `viewer`, `auditor` |
| Token | string | Current auth token |
| RegisteredAt | int64 | Unix epoch seconds |
| LastSeen | int64 | Last authenticated request |
| Status | string | `active`, `suspended` |

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

- [ ] Admin gateway is a separate process/listener from the application gateway with its own TLS certificate and domain
- [ ] Admin gateway rejects requests from IPs not in the operator allowlist before any processing (403, no body)
- [ ] Operator registration auto-approves the first operator as admin; subsequent operators require existing admin approval
- [ ] Admin sessions use WLT tokens with 4-hour TTL, 30-minute idle timeout, exact IP binding, and max 1 concurrent session
- [ ] MFA (TOTP or WebAuthn) is always required for admin session creation — no exceptions
- [ ] Role hierarchy admin > operator > auditor > viewer is enforced server-side on every /v1/admin/* endpoint
- [ ] Destructive actions (deregister agent, revoke federation, delete operator) require 4-eyes approval and X-Confirm HMAC
- [ ] Application gateway returns 404 for any request to /v1/admin/* paths
- [ ] GET /v1/admin/overview returns agent counts, domain status, workflow stats, approval counts, and health score
- [ ] All admin API responses include Cache-Control: no-store header
- [ ] Admin auth middleware verifies token.type == "operator" and checks role against endpoint minimum
- [ ] Bootstrap event (first operator registration) is permanently recorded in the audit log
- [ ] WebSocket /v1/admin/ws provides real-time status updates for agent changes, approvals, and workflow completions
- [ ] Admin gateway and application gateway share NO session state, cookie domain, or network listener
