<!-- blueprint
type: architecture
name: browser-session
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/gateway, architecture/agent, patterns/auth-session, patterns/auth-token]
platform: any
tier: free
-->

# Browser Session Architecture

Specification for cryptographically-bound browser sessions that
connect the Weblisk client framework (islands architecture) to the
server-side agent network. Sessions are unforgeable, replay-resistant,
hijack-proof, and survive agent restarts and partial outages without
requiring re-authentication.

## Overview

A Weblisk browser session is not a cookie with a random ID. It is a
cryptographic contract between the gateway and the browser that binds
the session to a specific client context, is signed by the gateway's
Ed25519 key, and carries enough state to route requests through the
agent network without any individual agent needing to maintain session
state.

This architecture ensures that:
- Sessions cannot be hijacked (bound to client fingerprint)
- Sessions cannot be replayed (nonce + timestamp validation)
- Sessions cannot be forged (Ed25519 signature verification)
- Sessions survive agent downtime (state lives in the gateway)
- Islands operate independently (each island has its own request
  lifecycle within the shared session)

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/health
          methods: [GET]
      types:
        - name: AgentManifest
          fields_used: [name, url, public_key]
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

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WLS
          fields_used: [sub, iss, iat, exp, sid, roles, bind, csrf, sec, mfa, ren]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [tls, session_config, csrf_config]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentContext
          fields_used: [identity, services, token]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/auth-session
    version: ">=1.0.0 <2.0.0"
    bindings:
      patterns:
        - behavior: session-lifecycle
          parameters: [creation, validation, renewal, termination]
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
```

---

## Responsibilities

### Owns

- WLS (Weblisk Session) token structure, signing, and verification
- Client binding computation and validation (UA, language, IP class, TLS)
- CSRF protection via enhanced Double Submit Cookie pattern
- Server-side session state lifecycle (creation, renewal, idle timeout, termination)
- Session security level management (standard, elevated, critical)
- Anti-hijacking measures and anomaly detection
- Islands integration — concurrent request handling within a shared session

### Does NOT Own

- User authentication flow (owned by the gateway — session is created after auth succeeds)
- Gateway routing or ABAC policy enforcement (owned by `architecture/gateway`)
- Agent-side session state (agents are stateless — gateway injects context per-request)
- Operator/admin sessions (owned by `architecture/admin` using WLT tokens)
- MFA implementation (owned by auth patterns; session records MFA status)

---

## Interfaces

The session component’s API surface is defined across the following
sections: [Session Token](#session-token) (WLS token structure and
claims), [Client Binding](#client-binding) (binding modes and validation),
[CSRF Protection](#csrf-protection) (Double Submit pattern),
[Server-Side Session State](#server-side-session-state) (session record
fields and storage), and [Session Security Levels](#session-security-levels)
(standard/elevated/critical escalation).

---

## Data Flow

1. User authenticates via `/auth/login` through the application gateway
2. Gateway generates session ID (32 random bytes), computes client binding hash, generates CSRF secret
3. Gateway creates WLS token with all claims and signs with its Ed25519 private key
4. Gateway stores server-side session state and sets HttpOnly cookie with token
5. On every subsequent request: gateway extracts token from cookie, verifies Ed25519 signature
6. Gateway checks expiry, renewal timestamp, and client binding match
7. Gateway loads server-side session state by `sid` and injects session context headers
8. Request forwarded to agents with `X-Gateway-Session`, `X-Gateway-User`, `X-Gateway-Roles` headers
9. Agents process request statelessly and return response
10. On renewal: gateway issues new token with updated timestamps, swaps cookie transparently
11. On termination: server-side state deleted, cookie cleared

---

## Design Principles

1. **Cryptographic binding over trust** — Sessions are proven valid
   by mathematics, not by trusting the client or the network.
2. **Server-authoritative** — The browser holds a signed token, but
   all session state lives server-side. The token is a key to the
   state, not the state itself.
3. **Agent-agnostic** — No agent stores session state. The gateway
   injects session context on every request. Agents process the
   request and return — stateless.
4. **Island-aware** — Each island on a page can make independent
   requests within the same session. Concurrent requests from
   different islands are safe and expected.
5. **Progressive security** — Basic sessions use device binding.
   Elevated sessions add MFA. Critical sessions add per-request
   signing.

---

## Session Token

### Token Structure

The session token is a WLT (Weblisk Token) issued by the gateway,
following the same format as agent tokens but with browser-specific
claims.

```
base64url(header) . base64url(payload) . base64url(signature)
```

### Header

```json
{
  "alg": "Ed25519",
  "typ": "WLS"
}
```

- `typ`: `"WLS"` — Weblisk Session (distinct from `"WLT"` agent tokens)

### Payload (Claims)

```json
{
  "sub": "user-a1b2c3d4",
  "iss": "gateway",
  "iat": 1712160000,
  "exp": 1712246400,
  "sid": "sess-d4e5f6g7h8i9",
  "roles": ["editor", "user"],
  "bind": "sha256:a1b2c3d4e5f6...",
  "csrf": "sha256:f6e5d4c3b2a1...",
  "sec": "standard",
  "mfa": false,
  "ren": 1712163600
}
```

### Claim Definitions

| Claim | Type | Required | Description |
|-------|------|----------|-------------|
| sub | string | yes | User ID |
| iss | string | yes | Always `"gateway"` |
| iat | int64 | yes | Issued-at timestamp |
| exp | int64 | yes | Expiry timestamp |
| sid | string | yes | Session ID (links to server-side state) |
| roles | []string | yes | User's current roles |
| bind | string | yes | Client binding hash (see Binding section) |
| csrf | string | yes | CSRF secret hash (for Double Submit validation) |
| sec | string | yes | Security level: `standard`, `elevated`, `critical` |
| mfa | bool | yes | Whether MFA has been completed this session |
| ren | int64 | yes | Next renewal timestamp (sliding window) |

### Token Lifecycle

```
1. CREATION (on successful authentication)
   a. User authenticates via /auth/login
   b. Gateway generates session ID (32 random bytes, hex)
   c. Gateway computes client binding hash
   d. Gateway generates CSRF secret (32 random bytes)
   e. Gateway creates WLS token with all claims
   f. Gateway signs token with its Ed25519 private key
   g. Gateway stores server-side session state
   h. Gateway sets HttpOnly cookie with token
   i. Gateway returns CSRF token in response body

2. VALIDATION (on every request)
   a. Extract token from cookie
   b. Verify Ed25519 signature (gateway's public key)
   c. Check exp > now (not expired)
   d. Check ren — if now > ren, trigger silent renewal
   e. Verify bind claim matches current client context
   f. Load server-side session state by sid
   g. If any check fails → 401 (clear cookie, force re-auth)

3. RENEWAL (sliding window)
   a. When ren timestamp is reached (default: 1 hour)
   b. Gateway issues new token with:
      - Same sid (session continues)
      - Updated iat, exp, ren
      - Fresh bind computation
      - Same csrf secret
   c. Set new cookie, old token immediately invalid
   d. Transparent to client (cookie swap on response)

4. TERMINATION
   a. Explicit logout → delete server-side state, clear cookie
   b. Expiry → server-side state cleaned up by background job
   c. Idle timeout → if no requests within idle window, state expires
   d. Forced invalidation → admin or security event triggers kill
```

---

## Client Binding

Client binding prevents session tokens from being used by a different
browser or device than the one that authenticated.

### Binding Hash Computation

```
binding_input = concatenate(
  user_agent,                    # Browser User-Agent string
  accept_language,               # Accept-Language header
  client_ip_class,               # /24 subnet (not exact IP — allows NAT roaming)
  tls_session_hash               # TLS session binding (RFC 5929 channel binding)
)

binding_hash = SHA-256(binding_input)
token.bind = "sha256:" + hex(binding_hash)
```

### Binding Modes

| Mode | Strictness | Binding Components | Use Case |
|------|-----------|-------------------|----------|
| `strict` | High | UA + Lang + IP/24 + TLS | Production default |
| `standard` | Medium | UA + Lang + IP/16 | Mobile / roaming users |
| `relaxed` | Low | UA only | Development / testing |

### Binding Validation

On every request:

```
1. Compute current binding hash from request context
2. Compare against token.bind claim
3. If mismatch:
   a. Log: "Session binding mismatch" + details
   b. If strict mode → 401, invalidate session
   c. If standard mode → allow if only IP changed within /16,
      otherwise 401
   d. Increment anomaly counter for this session
   e. If anomaly_count > threshold → force MFA step-up
```

### Why Not Exact IP?

Users behind NAT, corporate proxies, and mobile networks change IP
addresses frequently. Binding to the exact IP would cause constant
re-authentication. Binding to the /24 subnet allows roaming within
a network while detecting cross-network session theft.

---

## CSRF Protection

### Double Submit Cookie Pattern (Enhanced)

The gateway uses a cryptographically-strengthened Double Submit
pattern:

```
1. On session creation:
   a. Generate CSRF secret: 32 random bytes
   b. Store CSRF secret hash in token claim: csrf = SHA-256(secret)
   c. Return CSRF token to client in response body:
      csrf_token = HMAC-SHA256(csrf_secret, session_id + user_id)

2. Client includes CSRF token in X-CSRF-Token header on
   state-changing requests (POST, PUT, DELETE)

3. Gateway validates:
   a. Extract csrf claim from session token
   b. Recompute expected CSRF token from server-side secret
   c. Compare submitted token with expected (constant-time)
   d. If mismatch → 403 Forbidden
```

### Why Not Synchronizer Token?

The synchronizer token pattern requires server-side token storage
per-form. The HMAC-based approach derives the expected token from
the session's CSRF secret, making it stateless per-request while
remaining unforgeable.

---

## Server-Side Session State

### Session Record

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | Unique session identifier |
| user_id | string | Authenticated user |
| roles | []string | User's roles at session creation |
| groups | []string | User's groups at session creation |
| csrf_secret | bytes | CSRF secret (encrypted at rest) |
| binding_hash | string | Client binding hash |
| security_level | string | `standard`, `elevated`, `critical` |
| mfa_verified | bool | MFA completed this session |
| mfa_method | string | Which MFA method was used |
| created_at | int64 | Session creation time |
| last_active | int64 | Last request timestamp |
| expires_at | int64 | Absolute session expiry |
| idle_expires_at | int64 | Idle timeout expiry |
| ip_address | string | Client IP at creation |
| user_agent | string | Client UA at creation |
| anomaly_count | int | Binding mismatches detected |
| revoked | bool | Whether session has been force-killed |
| metadata | json | Application-specific session data |

### Session Storage

Sessions are stored encrypted in the gateway's storage backend:

```
Encryption: AES-256-GCM
Key derivation: HKDF(gateway_ed25519_private_key, "session-encryption", salt)
Salt: unique per session (stored alongside ciphertext)
```

### Storage Operations

| Operation | Signature | Description |
|-----------|-----------|-------------|
| CreateSession | `(session Session) → error` | Store new session |
| GetSession | `(id string) → (Session, error)` | Load session by ID |
| UpdateActivity | `(id string, ts int64) → error` | Update last_active |
| RevokeSession | `(id string) → error` | Mark as revoked |
| CleanExpired | `() → (int, error)` | Purge expired sessions |
| ListUserSessions | `(userID string) → ([]Session, error)` | All sessions for user |
| RevokeAllUserSessions | `(userID string) → error` | Kill all sessions |

---

## Islands Integration

### How Islands Communicate

The Weblisk client framework renders pages as compositions of
independent islands. Each island is a self-contained UI component
that fetches its own data from the server.

```
Page: /dashboard
┌────────────────────────────────────────────┐
│  ┌──────────────────┐  ┌────────────────┐ │
│  │  Navigation       │  │  User Menu     │ │
│  │  (static island)  │  │  GET /islands/ │ │
│  │                   │  │  dashboard/    │ │
│  │                   │  │  user-menu     │ │
│  └──────────────────┘  └────────────────┘ │
│  ┌──────────────────┐  ┌────────────────┐ │
│  │  Metrics Panel    │  │  Alert Feed    │ │
│  │  GET /islands/    │  │  GET /islands/ │ │
│  │  dashboard/       │  │  dashboard/    │ │
│  │  metrics          │  │  alerts        │ │
│  └──────────────────┘  └────────────────┘ │
│  ┌─────────────────────────────────────┐  │
│  │  Strategy Progress                  │  │
│  │  GET /islands/dashboard/strategies  │  │
│  └─────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

### Request Pattern

Every island request carries the same session cookie. The gateway:

1. Validates the session once per request (not once per page)
2. Authorizes each island route independently (different islands can
   have different role requirements)
3. Routes each island to the appropriate agent/domain
4. Returns the response directly to the island

### Concurrent Safety

Multiple islands on the same page fire requests concurrently. The
session system handles this safely:

- Session validation is read-only (no writes during validation)
- `last_active` updates are debounced (once per 60 seconds, not
  per-request)
- CSRF tokens are per-session, not per-request — concurrent POSTs
  from different islands use the same token
- Token renewal sets the new cookie on the first response; subsequent
  concurrent responses carry the new cookie too (idempotent set)

### Island Error Isolation

If one island's agent is down:

```
GET /islands/dashboard/metrics  → 200 OK (health domain responding)
GET /islands/dashboard/alerts   → 503 (alerting agent down)
GET /islands/dashboard/strategies → 200 OK (orchestrator responding)
```

The browser renders the page with the alerts island showing a loading
or error state. All other islands render normally. When the alerting
agent recovers, the island can retry automatically.

---

## Session Security Levels

Sessions have a security level that determines what resources can
be accessed without additional verification.

### Levels

| Level | Grants Access To | Requires | Upgrades To |
|-------|-----------------|----------|-------------|
| `standard` | Normal app routes, read operations | Credentials | `elevated` via MFA |
| `elevated` | Admin routes, write operations on sensitive data | Credentials + MFA | `critical` via re-auth + MFA |
| `critical` | Destructive operations, security settings, key rotation | Recent credentials + MFA + per-request confirmation | — |

### Level Transitions

```
standard → elevated:
  User completes MFA challenge
  Session claim updated: sec="elevated", mfa=true
  Level persists for session duration (or configurable TTL)

elevated → critical:
  User re-enters credentials (even if session is valid)
  User completes MFA challenge
  Session claim updated: sec="critical"
  Level has short TTL (default: 15 minutes)
  After TTL → drops back to elevated

Any → standard:
  MFA timeout or explicit downgrade
  Session claim updated: sec="standard", mfa=false
```

### Per-Request Confirmation (Critical Level)

For destructive operations (delete user, revoke keys, change security
settings), even a `critical` session requires per-request
confirmation:

```
1. Client sends request with X-Confirm: <HMAC> header
2. HMAC = HMAC-SHA256(csrf_secret, request_method + request_path + timestamp)
3. Gateway validates HMAC and timestamp freshness (< 30 seconds)
4. If valid → proceed
5. If missing/invalid → 403 with X-Confirmation-Required: true
```

---

## Anti-Hijacking Measures

### Session Fixation Prevention

```
- New session ID generated on every authentication (login, MFA, level upgrade)
- Old session ID immediately invalidated
- Server-side state migrated to new ID atomically
- Cookie path set to / (prevents scope fixation)
```

### Token Replay Prevention

```
- Token includes iat (issued-at) claim
- Renewal generates a new token; old token is blacklisted
- Blacklist TTL = token's remaining lifetime (short, auto-cleanup)
- Concurrent requests during renewal grace period (5 seconds) accept
  both old and new token
```

### Anomaly Detection

The gateway tracks per-session anomalies:

| Anomaly | Action | Threshold |
|---------|--------|-----------|
| Binding hash mismatch | Log + increment counter | 3 → force MFA |
| Rapid IP changes | Log + increment counter | 5 in 1 minute → invalidate |
| Concurrent sessions from different /16 subnets | Alert | 1 → alert admin |
| Request to route above session's role level | Log (potential probing) | 10 → temporary IP block |
| CSRF validation failure | Log | 3 → invalidate session |

### Forced Invalidation Triggers

The gateway or admin can kill sessions immediately:

```
- User changes password → revoke ALL sessions
- Admin deactivates user → revoke ALL sessions
- Security alert triggers → revoke sessions matching criteria
- User explicitly revokes a session → revoke that session
- Too many anomalies → revoke that session
```

---

## Zero-Dependency Client Contract

The browser-side contract requires ZERO client libraries, ZERO build
tools, and ZERO framework dependencies:

### What the Browser Does

```
1. User navigates to the application URL (standard HTTP)
2. Server returns HTML with Weblisk islands markup
3. Weblisk client framework (single <script> tag, zero deps):
   a. Discovers islands in the DOM
   b. Each island fetches its data endpoint:
      - Includes session cookie (automatic, HttpOnly)
      - Includes CSRF token header (stored in memory from login response)
   c. Renders response data into the island's DOM region
4. User interactions trigger standard HTTP requests (forms, fetch)
5. All security enforcement is server-side — the client sends
   standard requests and the gateway handles everything
```

### What the Browser NEVER Does

```
- Store tokens in localStorage or sessionStorage (XSS risk)
- Include sensitive data in URLs (leaks via Referer, logs)
- Make decisions about authorization (server-authoritative)
- Direct-connect to agents (only talks to gateway)
- Include any SDK, build step, or dependency for security
```

### Cookie Specification

```
Set-Cookie: wl_session=<WLS token>;
  HttpOnly;
  Secure;
  SameSite=Strict;
  Path=/;
  Max-Age=86400;
  Domain=app.example.com
```

| Attribute | Value | Purpose |
|-----------|-------|---------|
| HttpOnly | always | Prevents JavaScript access (XSS protection) |
| Secure | always (prod) | HTTPS only |
| SameSite | Strict | Prevents cross-site request attachment |
| Path | / | Consistent across all routes |
| Max-Age | Session TTL | Browser-managed expiry |
| Domain | Application domain | Scoped to the application |

---

## Implementation Notes

- Session token signing MUST use the gateway's Ed25519 key — not a
  shared secret. This allows any party holding the gateway's public
  key to verify a session token without possessing the signing key.
- Client binding hashes MUST be computed from raw header values, not
  parsed/normalized versions, to prevent bypass via header manipulation.
- The TLS channel binding component requires access to the TLS
  session — in Go, use `tls.ConnectionState().TLSUnique`; in Node.js,
  use `socket.getTLSTicket()`.
- Session cleanup (purging expired sessions) MUST run as a background
  task, not inline with request processing.
- The anomaly detection thresholds are defaults. Production deployments
  SHOULD tune them based on observed traffic patterns.
- CSRF tokens are valid for the lifetime of the session. They do NOT
  rotate per-request (to support concurrent island requests).
- The 5-second renewal grace period prevents race conditions when
  multiple islands send concurrent requests during token renewal.

## Verification Checklist

- [ ] Session token uses WLS type (distinct from WLT), signed by gateway's Ed25519 key, with all required claims (sub, iss, iat, exp, sid, roles, bind, csrf, sec, mfa, ren)
- [ ] Client binding hash is SHA-256 of concatenated user_agent + accept_language + client_ip_class(/24) + tls_session_hash
- [ ] Binding mismatch in strict mode returns 401 and invalidates the session immediately
- [ ] CSRF token is HMAC-SHA256(csrf_secret, session_id + user_id) and validated via constant-time comparison
- [ ] Session renewal issues a new token with same sid, updated iat/exp/ren, and fresh binding — old token is immediately invalid
- [ ] Session cookie is set with HttpOnly, Secure, SameSite=Strict, Path=/, and scoped to the application domain
- [ ] New session ID is generated on every authentication event (login, MFA, level upgrade) to prevent fixation
- [ ] Security level transitions: standard → elevated (via MFA), elevated → critical (via re-auth + MFA with 15-minute TTL)
- [ ] Per-request HMAC confirmation (X-Confirm header) is required for critical-level destructive operations
- [ ] Password change or admin deactivation revokes ALL sessions for that user immediately
- [ ] Anomaly detection increments counter on binding mismatch and forces MFA step-up after 3 anomalies
- [ ] Concurrent island requests are safe: last_active debounced to 60s, CSRF tokens are per-session, 5-second renewal grace period
- [ ] Sessions are stored encrypted at rest using AES-256-GCM with HKDF-derived key and unique per-session salt
