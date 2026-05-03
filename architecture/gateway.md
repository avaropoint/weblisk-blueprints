<!-- blueprint
type: architecture
name: gateway
version: 1.0.0
requires: [protocol/identity, protocol/types, architecture/agent, architecture/admin, patterns/auth-session, patterns/auth-token, patterns/user-management, patterns/rate-limiting, patterns/api-ai]
platform: any
tier: free
-->

# Weblisk Application Gateway

The application gateway is the security boundary between end-user
browsers and the Weblisk agent network. It replaces the traditional
centralized web server with a cryptographically-secured, policy-driven
edge agent that handles authentication, authorization, route
protection, request mediation, and session lifecycle — while
maintaining the fully distributed nature of the architecture.

This is the APPLICATION gateway — it serves end users. Operator
admin access is handled by the completely separate **admin gateway**
(see Admin Interface blueprint). The two gateways share NO session
state, NO authentication flow, NO network listener, and NO cookie
domain. If this gateway is compromised, the admin gateway is
unreachable.

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
        - name: AgentManifest
          fields_used: [name, type, url, public_key, capabilities]
        - name: TaskRequest
          fields_used: [id, action, input]
        - name: TaskResult
          fields_used: [task_id, status, output]
        - name: ServiceDirectory
          fields_used: [agents, routing_table, namespaces]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentEndpoints
          fields_used: [execute, message, health, describe]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/admin
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: admin-separation
          parameters: [separation_model, operator_auth]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-session
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: session-lifecycle
          parameters: [creation, validation, renewal, termination, csrf_binding]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-token
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: token-signing
          parameters: [algorithm, claims, verification]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/user-management
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: user-lookup
          parameters: [user_id, roles, groups, email_verified]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/rate-limiting
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: rate-enforcement
          parameters: [per_ip, per_session, endpoint_limits]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Why Not a Web Server

Traditional web applications couple authentication, business logic,
and rendering into a single server process. If that server goes down,
everything goes down. If it needs to scale, everything scales together.
If it has a vulnerability, the entire application is exposed.

Weblisk inverts this. The gateway is a thin, hardened edge that does
exactly three things:

1. **Authenticate** — Prove who the requester is
2. **Authorize** — Decide if the requester can access the resource
3. **Mediate** — Route the request to the correct agent and return
   the response

The gateway does NOT execute business logic. It does NOT render pages.
It does NOT manage data. It is a security-focused routing layer that
ensures every request entering the agent network is authenticated,
authorized, and audited.

## Design Principles

1. **Agent-native, not server-shaped** — The gateway IS an agent. It
   has an Ed25519 identity, registers with the orchestrator, and
   follows the protocol. It just happens to face the browser instead
   of other agents.
2. **Defense in depth** — Authentication at the edge, authorization
   at the route, validation at the agent. Three independent checks
   that must ALL pass.
3. **Cryptographic session binding** — Sessions are not just random
   cookies. They are Ed25519-signed tokens bound to the client
   context, resistant to replay, hijacking, and fixation.
4. **Survive anything** — Browser sessions survive agent restarts,
   deployments, and partial outages. The session contract is between
   the browser and the gateway, not between the browser and any
   individual agent.
5. **Zero client assumptions** — The browser sends standard HTTP
   requests to pre-defined URLs. No client-side SDKs, no build
   steps, no dependencies. All security is enforced server-side.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (Weblisk Client Framework — Islands)               │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Island A  │  │ Island B  │  │ Island C  │  │ Island D  │  │
│  │ (nav)     │  │ (content) │  │ (sidebar) │  │ (chat)    │  │
│  └─────┬─────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘   │
│        │              │              │              │        │
│        └──────────────┴──────────────┴──────────────┘        │
│                          │                                   │
│              Standard HTTP (pre-defined URLs)                │
│              + Session Token (HttpOnly cookie)               │
│              + CSRF Token (header)                           │
└──────────────────────────┼───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  GATEWAY AGENT (Edge Security Boundary)                      │
│                                                              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ TLS        │→ │ Session      │→ │ Policy Engine        │ │
│  │ Termination│  │ Validation   │  │ (ABAC + Route Rules) │ │
│  └────────────┘  └──────────────┘  └──────────┬───────────┘ │
│                                               │              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────▼───────────┐ │
│  │ Response   │← │ Response     │← │ Request Mediation    │ │
│  │ Middleware │  │ Sanitization │  │ (Route → Agent Map)  │ │
│  └────────────┘  └──────────────┘  └──────────────────────┘ │
│                                                              │
│  Ed25519 Identity  │  Session Store  │  Policy Store         │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│  ORCHESTRATOR + AGENT NETWORK                                │
│                                                              │
│  Orchestrator ──→ Domain Controllers ──→ Work Agents         │
│       │                                                      │
│       └──→ Infrastructure Agents                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Gateway Identity

The gateway is an infrastructure agent with elevated privileges.

```json
{
  "name": "gateway",
  "type": "infrastructure",
  "version": "1.0.0",
  "description": "Edge security gateway for browser-to-agent mediation",
  "url": "https://app.example.com",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": ["*"]},
    {"name": "http:proxy", "resources": ["*"]}
  ],
  "gateway_config": {
    "external_port": 443,
    "tls": true,
    "session_store": "encrypted",
    "policy_engine": "abac"
  }
}
```

The gateway registers with the orchestrator like any agent but serves
external HTTP traffic on port 443 (or 80 with redirect). It is the
ONLY component that accepts unauthenticated external requests.

---

## Request Lifecycle

Every browser request follows this exact sequence. No shortcuts. No
bypasses.

```
1. TLS TERMINATION
   ├── HTTPS required in production (HTTP → 301 to HTTPS)
   ├── TLS 1.2+ only (1.3 preferred)
   ├── HSTS header on every response
   └── Certificate validation

2. PATH BLOCKING (before any processing)
   ├── Reject paths containing /.weblisk/ → 404 Not Found
   ├── Reject paths to any dotfile/dotfolder (/.[a-z]*) → 404 Not Found
   ├── Reject path traversal sequences (../) → 400 Bad Request
   └── This check is non-bypassable and runs before auth/session

3. RATE LIMITING
   ├── Per-IP rate limit (default: 100 req/min)
   ├── Per-session rate limit (default: 300 req/min)
   ├── Endpoint-specific limits (auth endpoints: 10 req/min)
   └── 429 Too Many Requests on breach

4. REQUEST VALIDATION
   ├── Method allowed for route?
   ├── Content-Type valid?
   ├── Content-Length within limit?
   ├── Request body parseable?
   └── 400 Bad Request on failure

5. SESSION RESOLUTION
   ├── Extract session token from cookie
   ├── If no token → anonymous context (limited routes)
   ├── Validate token signature (Ed25519)
   ├── Validate token expiry
   ├── Validate client binding (see Browser Session spec)
   ├── Load session state from session store
   └── 401 Unauthorized if session invalid

6. CSRF VALIDATION (state-changing requests only)
   ├── Extract CSRF token from X-CSRF-Token header
   ├── Validate against session's CSRF secret
   └── 403 Forbidden if CSRF check fails

7. AUTHORIZATION (Policy Engine)
   ├── Resolve user attributes (role, groups, permissions)
   ├── Resolve resource attributes (route, method, sensitivity)
   ├── Resolve context attributes (time, IP, device)
   ├── Evaluate ABAC policy rules
   ├── Log authorization decision (allow or deny + reason)
   └── 403 Forbidden if denied

8. REQUEST MEDIATION
   ├── Map route to target agent via route table
   ├── Strip browser-specific headers
   ├── Inject internal headers:
   │   ├── X-Gateway-Session: <session_id>
   │   ├── X-Gateway-User: <user_id>
   │   ├── X-Gateway-Roles: <comma-separated roles>
   │   ├── X-Trace-Id: <trace_id>
   │   └── Authorization: Bearer <internal agent token>
   ├── Forward request to agent via orchestrator or direct
   └── 502 Bad Gateway if agent unreachable

9. RESPONSE PROCESSING
   ├── Validate response from agent
   ├── Apply response sanitization (strip internal headers/errors)
   ├── Apply application-configured response middleware (if any)
   ├── Set security headers on response
   ├── Log response metadata to audit trail
   └── Return response to browser

10. SECURITY HEADERS (on EVERY response)
   ├── Strict-Transport-Security: max-age=31536000; includeSubDomains
   ├── X-Content-Type-Options: nosniff
   ├── X-Frame-Options: DENY
   ├── Content-Security-Policy: <per-route policy>
   ├── Referrer-Policy: strict-origin-when-cross-origin
   ├── Permissions-Policy: <restrictive>
   ├── Cross-Origin-Opener-Policy: same-origin
   └── Cache-Control: <per-route policy>
```

---

## Route Table

The gateway maps external URLs to internal agent endpoints. This is
the "pre-defined URL" abstraction — the browser knows routes, not
agents.

### Route Definition

```yaml
routes:
  # Public routes (no auth required)
  - path: /auth/*
    target: gateway:internal        # Handled by gateway itself
    auth: none
    rate_limit: 10/min
    csrf: false

  - path: /health
    target: gateway:internal
    auth: none

  # Protected routes (auth required)
  - path: /api/seo/*
    target: domain:seo
    auth: required
    roles: [user, editor, admin]
    rate_limit: 60/min
    sensitivity: standard

  - path: /api/content/*
    target: domain:content
    auth: required
    roles: [editor, admin]
    rate_limit: 60/min
    sensitivity: standard

  # APPLICATION-SPECIFIC admin routes are normal application routes.
  # Customers may define their own /api/admin/* paths for their
  # business logic (CMS admin, product management, etc.). These are
  # application features governed by ABAC policies like any route.
  #
  # Example — a customer's e-commerce admin panel:
  # - path: /api/admin/*
  #   target: domain:commerce
  #   auth: required
  #   roles: [shop-admin]
  #   rate_limit: 60/min
  #   sensitivity: elevated
  #
  # WEBLISK PLATFORM admin routes (/v1/admin/*) are NEVER served
  # here. Platform administration (orchestrator, agents, federation)
  # goes through the separate admin gateway. Requests to /v1/admin/*
  # on this gateway return 404.

  - path: /api/users/*
    target: gateway:user-management
    auth: required
    roles: [user, editor, admin]
    sensitivity: pii
    data_masking: user-profile

  # Static assets (public, cacheable)
  - path: /assets/*
    target: static:filesystem
    auth: none
    cache: immutable
    dotfiles: deny               # NEVER serve dotfiles from filesystem
```

---

## Attribute-Based Access Control (ABAC)

RBAC (role-based) is the floor, not the ceiling. The gateway
implements full ABAC for fine-grained authorization decisions.

### Attributes

**Subject attributes** (who is requesting):
| Attribute | Type | Source |
|-----------|------|--------|
| user_id | string | Session |
| roles | []string | Session / User record |
| groups | []string | User record |
| email_verified | bool | User record |
| mfa_verified | bool | Session |
| ip_address | string | Request |
| device_fingerprint | string | Session binding |
| session_age_seconds | int | Computed |

**Resource attributes** (what is being accessed):
| Attribute | Type | Source |
|-----------|------|--------|
| route | string | Request path |
| method | string | HTTP method |
| sensitivity | string | Route table (standard/elevated/pii/critical) |
| owner_id | string | Resource record |
| domain | string | Route table |

**Context attributes** (environmental conditions):
| Attribute | Type | Source |
|-----------|------|--------|
| time_of_day | string | Server clock |
| day_of_week | string | Server clock |
| request_origin | string | Origin header |
| risk_score | float | Computed from anomalies |

### Policy Rules

```yaml
policies:
  # Basic role check
  - name: require-admin-for-admin-routes
    effect: deny
    condition: resource.sensitivity == "elevated" AND "admin" NOT IN subject.roles

  # PII requires verified email
  - name: verified-email-for-pii
    effect: deny
    condition: resource.sensitivity == "pii" AND subject.email_verified == false

  # MFA required for critical operations
  - name: mfa-for-critical
    effect: deny
    condition: resource.sensitivity == "critical" AND subject.mfa_verified == false

  # Owners can access their own resources
  - name: owner-access
    effect: allow
    condition: resource.owner_id == subject.user_id

  # Time-based restriction (admin actions during business hours only)
  - name: admin-business-hours
    effect: deny
    condition: >
      resource.sensitivity == "elevated"
      AND context.day_of_week IN ["Saturday", "Sunday"]
      AND subject.roles == ["admin"]
      AND NOT subject.roles CONTAINS "superadmin"

  # Anomaly-based step-up
  - name: step-up-on-anomaly
    effect: deny
    condition: context.risk_score > 0.7 AND subject.mfa_verified == false
    message: "Elevated risk detected — MFA required"
```

### Policy Evaluation

```
1. Collect all applicable policies for the request
2. Evaluate each policy's condition against attributes
3. Resolution order:
   a. Any explicit DENY → request denied
   b. At least one explicit ALLOW → request allowed
   c. No matching policy → request denied (deny by default)
4. Log: {decision, policies_matched, attributes_evaluated, reason}
```

---

## Multi-Factor Authentication

The gateway supports MFA as a session-level attribute that policies
can require for sensitive operations.

### MFA Flow

```
1. User authenticates with credentials → session created (mfa_verified: false)
2. If route policy requires MFA:
   a. Gateway returns 403 with X-MFA-Required: true header
   b. Client redirects to MFA challenge
3. User completes MFA challenge:
   POST /auth/mfa/verify {code: "123456"}
4. Gateway validates:
   - TOTP: validate against user's shared secret
   - WebAuthn: validate authenticator assertion
5. Session updated: mfa_verified = true
6. Redirect back to original route
```

### Supported MFA Methods

| Method | Standard | Storage |
|--------|----------|---------|
| TOTP | RFC 6238 | User's shared secret (encrypted) |
| WebAuthn | W3C WebAuthn L2 | User's credential public key |

---

## Agent Failover and Session Continuity

The gateway guarantees session continuity even when agents restart,
redeploy, or fail.

### How It Works

```
1. Session state lives in the GATEWAY's storage, not in agents
2. Agents are stateless request handlers — they receive context
   from the gateway on every request
3. If an agent goes offline:
   a. Gateway detects via health check failure
   b. Requests to that agent return 503 with Retry-After header
   c. Gateway can route to a replica if available
   d. Session remains valid — user does not need to re-authenticate
4. When agent comes back online:
   a. Gateway detects via health check recovery
   b. Requests resume automatically
   c. Session context is injected on the next request — agent
      doesn't need to "remember" anything
```

### What the Browser Sees

```
Normal request:
  GET /api/seo/score → 200 OK (2.3s)

Agent temporarily down:
  GET /api/seo/score → 503 Service Unavailable
  Retry-After: 5
  Body: {"error": "Service temporarily unavailable", "retry_after": 5}

Agent recovered:
  GET /api/seo/score → 200 OK (2.5s)  ← same session, no re-auth
```

The Weblisk client framework's islands handle this gracefully —
each island manages its own loading/error states independently.
If the SEO island's agent is down, the content island and navigation
still work.

---

## Request Mediation

### Internal Headers

When forwarding to agents, the gateway strips all browser headers and
injects a clean set:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Gateway-Session` | Session ID | Identifies the user session |
| `X-Gateway-User` | User ID | Authenticated user identity |
| `X-Gateway-Roles` | Comma-separated roles | User's authorization roles |
| `X-Gateway-Groups` | Comma-separated groups | User's group memberships |
| `X-Gateway-Sensitivity` | Route sensitivity level | Tells agent what data masking to apply |
| `X-Trace-Id` | Trace ID | Distributed tracing correlation |
| `Authorization` | `Bearer <token>` | Internal WLT token for agent auth |
| `X-Request-Id` | Request UUID | Unique request identifier |

Agents MUST NOT trust any `X-Gateway-*` header that doesn't come
from the gateway. The orchestrator validates that these headers are
only set by the registered gateway agent.

### Response Sanitization

Before returning to the browser, the gateway:

```
1. Strip internal headers (X-Gateway-*, X-Agent-*)
2. Strip server identification headers (Server, X-Powered-By)
3. Apply application-configured response middleware (if any)
4. Set Content-Security-Policy per route configuration
5. Set Cache-Control per route configuration
6. Ensure no raw error messages leak internal details:
   - Agent errors → generic 500 with request_id for correlation
   - Stack traces → never exposed (logged server-side only)
   - Internal URLs → never exposed
```

---

## Configuration

### Gateway Config

```yaml
gateway:
  external_url: https://app.example.com
  tls:
    cert: /etc/ssl/certs/app.pem
    key: /etc/ssl/private/app.key
    min_version: "1.2"

  session:
    token_ttl: 86400              # 24 hours
    idle_timeout: 3600            # 1 hour of inactivity
    max_per_user: 5
    binding: strict               # strict | standard
    store: encrypted              # encrypted | plain

  rate_limits:
    global: 1000/min
    per_ip: 100/min
    per_session: 300/min
    auth_endpoints: 10/min

  security:
    policy_engine: abac
    mfa_required_sensitivity: critical
    cors:
      allowed_origins: ["https://app.example.com"]
      allowed_methods: ["GET", "POST", "PUT", "DELETE"]
      allowed_headers: ["Content-Type", "X-CSRF-Token"]
      max_age: 86400

  audit:
    log_all_requests: true
    log_request_body: false       # Only for elevated/critical routes
    log_response_body: false
    retention_days: 90
```

---

## Async Result Delivery

When a browser request triggers a domain workflow, the domain returns
an immediate `202 Accepted` response. The workflow executes
asynchronously via the Workflow Agent and Task Agent. The gateway
provides two mechanisms for delivering results to the browser:

### Polling (Default)

The `202 Accepted` response includes a `Location` header pointing to
a status endpoint:

```
HTTP/1.1 202 Accepted
Location: /api/<domain>/status/<execution-id>
Content-Type: application/json

{
  "execution_id": "wf-exec-001",
  "status": "pending",
  "poll_url": "/api/<domain>/status/<execution-id>",
  "poll_interval": 2
}
```

The client polls `GET /api/<domain>/status/<execution-id>` until the
workflow completes:

```json
{
  "execution_id": "wf-exec-001",
  "status": "completed",
  "result": { ... },
  "completed_at": 1712160300
}
```

Status values: `pending`, `running`, `completed`, `failed`.

The gateway routes `/api/<domain>/status/:id` to the owning domain's
`HandleMessage` with action `get_status`. The domain queries the
Workflow Agent's execution store via `POST /v1/message` (action:
`get_status`) and returns the current state.

### Server-Sent Events (SSE) — Optional

For real-time delivery, the gateway MAY expose an SSE endpoint:

```
GET /api/<domain>/stream/<execution-id>
Accept: text/event-stream
```

The gateway subscribes to `workflow.phase_completed` and
`workflow.completed` events scoped to the execution's correlation ID
and streams them to the client:

```
event: phase_completed
data: {"phase": "scan", "status": "success"}

event: completed
data: {"execution_id": "wf-exec-001", "status": "completed", "result": {...}}
```

The SSE connection is authenticated via the session cookie. The
gateway MUST verify the requesting user has access to the execution's
domain before streaming events. Connection timeout: 5 minutes
(client reconnects with `Last-Event-ID`).

### Implementation Requirements

1. The gateway MUST support polling (it is the default mechanism)
2. SSE is OPTIONAL — hubs that need real-time updates enable it
3. Both mechanisms use the same ABAC policy evaluation
4. Execution status endpoints are rate-limited per-session
5. Results are available for 24 hours after completion (configurable
   via `WL_RESULT_RETENTION`)

---

## Types

### RouteTable

Local routing configuration mapping external paths to internal agents.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Routes | []Route | `routes` | yes | Ordered list of route rules |
| UpdatedAt | int64 | `updated_at` | yes | Unix epoch of last route table refresh |

### Route

A single routing rule mapping an external path to an internal agent.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Path | string | `path` | yes | External URL path pattern (e.g., `/api/seo/*`) |
| Agent | string | `agent` | yes | Target agent name |
| Domain | string | `domain` | no | Domain controller name (for domain-scoped routes) |
| Methods | []string | `methods` | no | Allowed HTTP methods (default: all) |
| RateLimit | string | `rate_limit` | no | Rate limit policy name to apply |

### GatewayConfig

Top-level gateway configuration.

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| TLS | TLSConfig | `tls` | yes | TLS termination settings |
| Session | SessionConfig | `session` | yes | Session cookie configuration |
| CSRF | CSRFConfig | `csrf` | yes | CSRF protection settings |
| RateLimits | map[string]RateLimitConfig | `rate_limits` | yes | Named rate limit policies |
| Client | ClientConfig | `client` | no | Client-facing behavior settings |

---

## Implementation Notes

- The gateway MUST be the ONLY externally-reachable component for
  end-user traffic. All other agents, domains, and the orchestrator
  listen on internal addresses only. The admin gateway is a separate
  external-facing component on a different domain/port (see Admin
  Interface blueprint).
- TLS termination happens at the gateway. Internal communication
  between gateway and agents MAY use plain HTTP on a trusted network,
  or mutual TLS for zero-trust internal networks.
- The gateway SHOULD be stateless except for the session store. This
  allows horizontal scaling behind a load balancer.
- Session store encryption uses AES-256-GCM with a key derived from
  the gateway's Ed25519 private key via HKDF.
- ABAC policies are loaded from a YAML file (`policies.yaml` by
  default, configurable via `WL_POLICY_FILE` env var). On startup,
  the gateway compiles policies into decision trees for microsecond
  evaluation. The gateway watches the policy file for changes and
  hot-reloads on modification — no restart required. During reload,
  in-flight requests complete with the old policy set; new requests
  use the updated policies. The weblisk-cli generates a default
  policy file during project scaffolding and provides
  `weblisk policy validate` and `weblisk policy test` commands.
- Failed authorization attempts are rate-limited separately from
  normal requests to prevent authorization probing.
- The gateway MUST NOT forward raw user input to agents without
  validation. Input validation happens at the gateway edge AND at
  the receiving agent (defense in depth).
- CORS is enforced at the gateway. Agents do not set CORS headers.
- The gateway MUST reject any request to `/v1/admin/*` (the Weblisk
  platform admin API) with a `404 Not Found` (not `403`, to avoid
  confirming the path exists). Platform administration goes through
  the admin gateway on a completely separate domain. Application-
  specific admin routes (e.g. `/api/admin/*` for a customer's CMS)
  are normal application routes and are fine on this gateway.
- The gateway MUST NOT accept `X-Operator-*` headers from any source.
  If present, they MUST be stripped before forwarding. Only the admin
  gateway may inject operator context headers.
- The gateway emits structured logs and traces following the
  observability blueprint, with additional fields for the external
  request context (client IP, user agent, geolocation if available).

---

## Responsibilities

### Owns
- TLS termination and HTTPS enforcement for all end-user traffic
- Session lifecycle management (creation, validation, renewal, revocation)
- CSRF validation on state-changing requests
- ABAC policy evaluation for every request (see [ABAC section](#attribute-based-access-control-abac))
- Rate limiting at per-IP, per-session, and per-endpoint levels
- Request mediation: mapping browser routes to internal agent endpoints
- Response sanitization: stripping internal headers/errors before reaching the browser
- Security header injection on every response
- MFA challenge orchestration

### Does NOT Own
- Business logic execution (delegated to domain agents)
- Page rendering (delegated to the islands architecture)
- Data storage for application data (delegated to agents and storage layer)
- Agent registration or orchestration (owned by orchestrator)
- Platform administration (owned by the separate admin gateway)

---

## Interfaces

The gateway's public API surface is defined by its **Route Table**
(see [Route Table section](#route-table)) and its internal authentication
endpoints. Summary:

| Interface | Type | Description |
|-----------|------|-------------|
| `GET/POST/PUT/DELETE /api/*` | HTTP (external) | Application routes — proxied to domain agents per route table |
| `POST /auth/*` | HTTP (external) | Authentication endpoints (login, logout, MFA) — handled internally |
| `GET /health` | HTTP (external) | Gateway health status |
| `GET /assets/*` | HTTP (external) | Static asset serving (public, cacheable) |
| `POST /v1/register` | HTTP (internal) | Gateway registers itself with the orchestrator as an infrastructure agent |
| `POST /v1/services` | HTTP (internal) | Receives service directory updates from the orchestrator |

See [Route Definition](#route-definition) for the full route configuration schema.

---

## Data Flow

The gateway's request lifecycle is fully documented in the
[Request Lifecycle section](#request-lifecycle). Summary sequence:

1. Browser sends HTTPS request to the gateway's external URL
2. Gateway terminates TLS and enforces HSTS
3. Rate limiter checks per-IP and per-session thresholds
4. Request validation: method, content-type, content-length, body parsing
5. Session resolution: extract/validate Ed25519-signed session token from cookie
6. CSRF validation on state-changing requests (POST/PUT/DELETE)
7. ABAC policy engine evaluates subject, resource, and context attributes
8. Request mediation: map route to target agent, inject internal headers
9. Forward request to agent via orchestrator or direct channel
10. Response processing: validate, sanitize, apply security headers
11. Return response to browser

---

## Verification Checklist

- [ ] Gateway registers with orchestrator as an infrastructure agent with its own Ed25519 identity
- [ ] HTTP requests in production redirect to HTTPS (301) and every response includes HSTS header
- [ ] Path blocking rejects requests to /.weblisk/, any dotfile/dotfolder, and path traversal sequences before any other processing
- [ ] Rate limits enforce per-IP (100/min), per-session (300/min), and auth endpoint (10/min) thresholds with 429 on breach
- [ ] Session token is validated on every request: Ed25519 signature, expiry, client binding, and server-side state lookup
- [ ] CSRF validation via X-CSRF-Token header is enforced on all state-changing requests (POST, PUT, DELETE)
- [ ] ABAC policy engine evaluates subject, resource, and context attributes with deny-by-default resolution
- [ ] Request mediation injects X-Gateway-Session, X-Gateway-User, X-Gateway-Roles, X-Trace-Id, and Authorization headers
- [ ] Response sanitization strips X-Gateway-*, X-Agent-*, Server, and X-Powered-By headers before reaching the browser
- [ ] Security headers set on every response: X-Content-Type-Options: nosniff, X-Frame-Options: DENY, CSP, Referrer-Policy, COOP
- [ ] Requests to /v1/admin/* return 404 (platform admin routes are never served by the application gateway)
- [ ] Agent failover returns 503 with Retry-After when agent is offline; session remains valid without re-authentication
- [ ] Session store encryption uses AES-256-GCM with key derived from gateway's Ed25519 private key via HKDF
