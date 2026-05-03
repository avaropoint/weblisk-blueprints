<!-- blueprint
type: architecture
name: client
version: 1.0.0
requires: [protocol/types, protocol/identity, architecture/gateway, architecture/agent, patterns/scope]
platform: any
tier: free
-->

# Client Architecture

Universal specification for external entities that consume the Weblisk
framework — browsers, mobile applications, desktop clients, API
consumers, server-to-server integrations, and IoT devices. Defines
session contracts, identity binding, trust levels, data boundary
enforcement, and client capability declarations that apply regardless
of client type.

The framework does not dictate how clients operate internally. It
defines the contracts that every client MUST honour when exchanging
data with the framework boundary — and the guarantees the framework
provides in return.

## Overview

Every entity that communicates with a Weblisk application gateway from
outside the agent network is a **client**. Clients vary enormously in
capability, trust, and attack surface — a browser running JavaScript in
a user's tab is fundamentally different from a backend service calling
the API with mTLS. This architecture defines a unified model that
handles all client types through a common taxonomy, per-type session
contracts, trust classification, and data boundary rules.

This architecture ensures that:
- Every client type has a defined session contract and identity binding
- Trust levels are assigned by client capability, not assumption
- Data leaving the framework boundary carries scope and sovereignty rules
- Browser sessions remain cryptographically bound and hijack-proof
- Non-browser clients (mobile, desktop, API, IoT) have first-class support
- The gateway enforces all client contracts server-side — clients are never trusted to self-enforce

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
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

  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [tls, session_config, csrf_config, client_config]
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

  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ScopeLevel
          fields_used: [level, label]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │        Application Gateway          │
                        │  ┌───────────────────────────────┐  │
                        │  │     Client Contract Layer      │  │
                        │  │  - Type detection              │  │
                        │  │  - Trust classification        │  │
                        │  │  - Session dispatch            │  │
                        │  │  - Capability negotiation      │  │
                        │  └───────────────────────────────┘  │
                        │  ┌──────────┐ ┌──────────────────┐  │
                        │  │ Session  │ │ Data Boundary    │  │
                        │  │ Manager  │ │ Enforcer         │  │
                        │  │ (per-    │ │ - scope tagging  │  │
                        │  │  type)   │ │ - field filter   │  │
                        │  └──────────┘ │ - TTL injection  │  │
                        │               └──────────────────┘  │
                        └──────────┬──────────────────────────┘
                                   │
           ┌───────────┬───────────┼───────────┬───────────┐
           │           │           │           │           │
      ┌────▼───┐  ┌────▼───┐  ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
      │Browser │  │Mobile  │  │Desktop │ │API/    │ │IoT/   │
      │ (WLS)  │  │Native  │  │Client  │ │Server  │ │Device │
      │        │  │ (WLC)  │  │ (WLC)  │ │(mTLS)  │ │(cert) │
      └────────┘  └────────┘  └────────┘ └────────┘ └────────┘
```

The client contract layer sits within the application gateway and is
responsible for detecting the client type on each request, selecting
the appropriate session and binding strategy, enforcing data boundary
rules on outbound responses, and negotiating capabilities with clients
that support it.

---

## Responsibilities

### Owns

- Client type taxonomy and detection logic
- Per-type session token contracts (WLS for browsers, WLC for native clients)
- Client binding computation and validation across all client types
- Trust level classification (untrusted, semi-trusted, trusted)
- Client capability declaration and negotiation
- Data boundary enforcement on responses leaving the framework
- CSRF protection for browser clients
- Browser islands integration and concurrent request safety
- Session security levels (standard, elevated, critical) and transitions
- Anti-hijacking measures and anomaly detection
- Cookie specification for browser clients

### Does NOT Own

- User authentication flow (owned by gateway — session created after auth)
- Gateway routing or ABAC policy enforcement (owned by `architecture/gateway`)
- Agent-side session state (agents are stateless — gateway injects context)
- Operator/admin sessions (owned by `architecture/admin` using WLT tokens)
- MFA implementation (owned by auth patterns; session records MFA status)
- Client-side offline data persistence and encryption (owned by `patterns/offline`)
- Transport-level encryption (owned by `architecture/data-security`)

---

## Interfaces

The client architecture's API surface spans: [Client Taxonomy](#client-taxonomy)
(type detection and classification), [Session Contracts](#session-contracts)
(per-type token structures and lifecycle), [Client Binding](#client-binding)
(identity binding per client type), [Trust Levels](#trust-levels)
(capability-based trust classification), [Data Boundary](#data-boundary)
(scope enforcement on outbound data), and [Browser Contract](#browser-contract)
(browser-specific session, CSRF, and islands integration).

---

## Data Flow

1. Client sends request to the application gateway
2. Gateway detects client type from request characteristics (User-Agent, auth header type, TLS client certificate)
3. Gateway selects the appropriate session contract for the detected type
4. Gateway validates the session token using the type-specific binding and signature rules
5. Gateway classifies the client's trust level based on type and authentication strength
6. Gateway loads server-side session state and injects context headers for agents
7. Agents process the request statelessly and return a response
8. Gateway applies data boundary rules: scope-based field filtering, TTL injection, sovereignty tags
9. Response returned to client with only the fields permitted for that client's trust level and scope

---

## Client Taxonomy

### Client Types

| Type | Identifier | Session Token | Binding | Example |
|------|-----------|--------------|---------|---------|
| `browser` | User-Agent + cookie | WLS (Weblisk Session) | UA + Lang + IP/24 + TLS | Web application in Chrome, Firefox, Safari |
| `native-mobile` | X-Client-Type header | WLC (Weblisk Client) | Device ID + app signature | iOS/Android app |
| `native-desktop` | X-Client-Type header | WLC (Weblisk Client) | Machine ID + app signature | Electron, Tauri, native desktop app |
| `api-server` | mTLS client certificate | mTLS session | Certificate fingerprint | Backend service, partner integration |
| `iot-device` | X-Device-ID header + cert | Device certificate | Hardware attestation | Sensor, embedded device |

### Detection Logic

The gateway determines client type using the following precedence:

```
1. mTLS client certificate present → api-server (or iot-device if X-Device-ID set)
2. X-Client-Type: native-mobile → native-mobile
3. X-Client-Type: native-desktop → native-desktop
4. Cookie: wl_session present → browser
5. Authorization: Bearer <WLC> → native-mobile or native-desktop (from token claims)
6. None of the above → reject with 401
```

Client type is determined once at session creation and immutable for the
session's lifetime. A browser session cannot become a mobile session.

---

## Trust Levels

### Classification

| Level | Client Types | Basis | Implications |
|-------|-------------|-------|-------------|
| `untrusted` | browser | Runs arbitrary code (extensions, XSS risk), user-controlled environment | No client-side security enforcement; all rules server-side. No local storage of sensitive data (tokens, keys). All auth via HttpOnly cookies. |
| `semi-trusted` | native-mobile, native-desktop | App-signed binary, sandboxed storage, but user-controlled device | May hold encrypted tokens in secure storage (Keychain, Credential Manager). Device attestation accepted as weak identity signal. |
| `trusted` | api-server | Operator-controlled infrastructure, mTLS, no user interaction | May cache scoped data per contract. Certificate identity is strong. Long-lived sessions permitted. |
| `constrained` | iot-device | Limited compute, may lack secure enclave, physical access risk | Minimal data exposure. Short TTL sessions. Hardware attestation where available. |

### Trust Level Determines

- Which session contract applies
- What data fields are included in responses (scope filtering)
- Maximum session duration
- Whether offline data storage is permitted
- Required encryption level for any client-side persistence

---

## Session Contracts

### Browser Sessions (WLS)

Browser sessions use the WLS (Weblisk Session) token — a
cryptographically-bound, Ed25519-signed token carried in an HttpOnly
cookie.

#### Token Structure

```
base64url(header) . base64url(payload) . base64url(signature)
```

#### Header

```json
{
  "alg": "Ed25519",
  "typ": "WLS"
}
```

#### Payload (Claims)

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

#### Claim Definitions

| Claim | Type | Required | Description |
|-------|------|----------|-------------|
| sub | string | yes | User ID |
| iss | string | yes | Always `"gateway"` |
| iat | int64 | yes | Issued-at timestamp |
| exp | int64 | yes | Expiry timestamp |
| sid | string | yes | Session ID (links to server-side state) |
| roles | []string | yes | User's current roles |
| bind | string | yes | Client binding hash |
| csrf | string | yes | CSRF secret hash |
| sec | string | yes | Security level: `standard`, `elevated`, `critical` |
| mfa | bool | yes | Whether MFA has been completed this session |
| ren | int64 | yes | Next renewal timestamp (sliding window) |

#### Token Lifecycle

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

### Native Client Sessions (WLC)

Mobile and desktop clients use the WLC (Weblisk Client) token. Unlike
browser sessions, native clients can securely store tokens in
platform-specific secure storage.

#### Header

```json
{
  "alg": "Ed25519",
  "typ": "WLC"
}
```

#### Payload (Claims)

```json
{
  "sub": "user-a1b2c3d4",
  "iss": "gateway",
  "iat": 1712160000,
  "exp": 1712764800,
  "cid": "client-m1n2o3p4",
  "roles": ["editor", "user"],
  "bind": "sha256:device-binding...",
  "cap": ["offline", "push", "biometric"],
  "sec": "standard"
}
```

#### WLC Claim Definitions

| Claim | Type | Required | Description |
|-------|------|----------|-------------|
| sub | string | yes | User ID |
| iss | string | yes | Always `"gateway"` |
| iat | int64 | yes | Issued-at timestamp |
| exp | int64 | yes | Expiry timestamp (longer than WLS — default 7 days) |
| cid | string | yes | Client registration ID (links to server-side client record) |
| roles | []string | yes | User's current roles |
| bind | string | yes | Device binding hash |
| cap | []string | yes | Declared client capabilities |
| sec | string | yes | Security level: `standard`, `elevated`, `critical` |

#### WLC Token Lifecycle

```
1. REGISTRATION (one-time, per device)
   a. Client calls /auth/register-client with device attestation
   b. Gateway validates attestation (platform-specific)
   c. Gateway generates client ID and stores client record
   d. Gateway returns client registration confirmation

2. AUTHENTICATION
   a. Client authenticates via /auth/login with credentials + client ID
   b. Gateway validates credentials and client registration
   c. Gateway computes device binding hash
   d. Gateway creates WLC token, signs with Ed25519 key
   e. Gateway returns token in response body (NOT a cookie)
   f. Client stores token in platform secure storage (Keychain/Credential Manager)

3. VALIDATION (on every request)
   a. Client sends token in Authorization: Bearer <WLC> header
   b. Gateway verifies Ed25519 signature
   c. Gateway checks expiry, device binding, client registration status
   d. If any check fails → 401

4. RENEWAL
   a. Client calls /auth/refresh with current token before expiry
   b. Gateway issues new token with updated timestamps
   c. Old token blacklisted (short TTL blacklist)

5. TERMINATION
   a. Client calls /auth/logout → server-side client session cleared
   b. Admin revocation → client record marked revoked
   c. Device wipe / app uninstall → client-side token destroyed
```

### API Server Sessions (mTLS)

Server-to-server integrations authenticate via mutual TLS. No session
token is issued — the TLS client certificate IS the identity.

```
1. ESTABLISHMENT
   a. Client presents TLS client certificate during handshake
   b. Gateway validates certificate against trusted CA chain
   c. Gateway extracts client identity from certificate subject/SAN
   d. Gateway loads client record by certificate fingerprint

2. PER-REQUEST
   a. TLS layer validates certificate on every connection
   b. Gateway maps certificate identity to roles and permissions
   c. No session state — each request is independently authenticated

3. REVOCATION
   a. Certificate revocation via CRL or OCSP
   b. Admin removes client record → certificate rejected
```

### IoT Device Sessions

Constrained devices use short-lived device certificates with minimal
claims. Where hardware attestation is available, it supplements the
certificate identity.

```
1. PROVISIONING
   a. Device enrolled via secure provisioning flow (out of band)
   b. Device certificate installed during manufacturing or first boot
   c. Gateway registers device record with hardware attestation data

2. AUTHENTICATION
   a. Device presents certificate + X-Device-ID header
   b. Gateway validates certificate and matches device record
   c. Gateway issues short-lived session token (1 hour default)
   d. Token claims limited to device-permitted operations only

3. DATA CONSTRAINTS
   a. Responses include only fields explicitly permitted for device class
   b. No offline storage permitted unless device has secure enclave
   c. All data has aggressive TTL (default: session duration)
```

---

## Client Binding

Client binding prevents session tokens from being used by a different
client than the one that authenticated. Each client type has a
binding strategy matched to its capabilities.

### Binding Strategies by Type

| Client Type | Binding Components | Hash |
|-------------|-------------------|------|
| browser | UA + Accept-Language + IP/24 + TLS session hash | SHA-256 |
| native-mobile | Device ID + app signing certificate hash | SHA-256 |
| native-desktop | Machine ID + app signing certificate hash | SHA-256 |
| api-server | TLS client certificate fingerprint | — (cert IS the binding) |
| iot-device | Hardware attestation token + device certificate | SHA-256 |

### Browser Binding Computation

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

### Browser Binding Modes

| Mode | Strictness | Binding Components | Use Case |
|------|-----------|-------------------|----------|
| `strict` | High | UA + Lang + IP/24 + TLS | Production default |
| `standard` | Medium | UA + Lang + IP/16 | Mobile / roaming users |
| `relaxed` | Low | UA only | Development / testing |

### Native Client Binding Computation

```
binding_input = concatenate(
  device_id,                     # Platform device ID (IDFV on iOS, ANDROID_ID, etc.)
  app_signature_hash             # SHA-256 of the app signing certificate
)

binding_hash = SHA-256(binding_input)
token.bind = "sha256:" + hex(binding_hash)
```

### Binding Validation

On every request, regardless of client type:

```
1. Compute current binding hash from request context
2. Compare against token.bind claim (constant-time comparison)
3. If mismatch:
   a. Log: "Client binding mismatch" + client type + details
   b. Browser (strict mode) → 401, invalidate session
   c. Browser (standard mode) → allow if only IP changed within /16
   d. Native client → 401, invalidate session (device binding is immutable)
   e. Increment anomaly counter for this session
   f. If anomaly_count > threshold → force MFA step-up (browser/native)
      or revoke client record (IoT)
```

---

## CSRF Protection

CSRF protection applies only to browser clients. Native, API, and IoT
clients are not vulnerable to CSRF (no automatic cookie attachment).

### Double Submit Cookie Pattern (Enhanced)

```
1. On session creation:
   a. Generate CSRF secret: 32 random bytes
   b. Store CSRF secret hash in WLS token claim: csrf = SHA-256(secret)
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

---

## Server-Side Session State

### Session Record (All Client Types)

| Field | Type | Description |
|-------|------|-------------|
| session_id | string | Unique session identifier |
| client_type | string | `browser`, `native-mobile`, `native-desktop`, `api-server`, `iot-device` |
| user_id | string | Authenticated user (or service identity for api-server) |
| client_id | string | Client registration ID (WLC/IoT) or null (browser/mTLS) |
| roles | []string | Roles at session creation |
| groups | []string | Groups at session creation |
| capabilities | []string | Declared client capabilities |
| trust_level | string | `untrusted`, `semi-trusted`, `trusted`, `constrained` |
| csrf_secret | bytes | CSRF secret — browser sessions only (encrypted at rest) |
| binding_hash | string | Client binding hash |
| security_level | string | `standard`, `elevated`, `critical` |
| mfa_verified | bool | MFA completed this session |
| mfa_method | string | Which MFA method was used |
| created_at | int64 | Session creation time |
| last_active | int64 | Last request timestamp |
| expires_at | int64 | Absolute session expiry |
| idle_expires_at | int64 | Idle timeout expiry |
| ip_address | string | Client IP at creation |
| user_agent | string | Client UA at creation (browser) or app identifier (native) |
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
| ListClientSessions | `(clientID string) → ([]Session, error)` | All sessions for a registered client |
| RevokeClientSessions | `(clientID string) → error` | Kill all sessions for a client registration |

---

## Data Boundary

When data leaves the framework boundary in a response to any client,
the gateway enforces data boundary rules based on the client's trust
level and the data's scope classification.

### Outbound Response Filtering

```
For each field in the response:
  1. Resolve the field's scope classification (from scope pattern)
  2. Check the client's trust level against the scope's permitted audiences
  3. If not permitted → strip the field from the response
  4. If permitted → include the field, attach metadata:
     - X-Data-Scope: <scope level>
     - X-Data-TTL: <maximum client-side retention in seconds>
     - X-Data-Offline: true|false (whether client may persist this offline)
```

### Scope-to-Trust Matrix

| Scope Level | untrusted (browser) | semi-trusted (native) | trusted (api-server) | constrained (IoT) |
|-------------|--------------------|-----------------------|---------------------|--------------------|
| `public` | include | include | include | include |
| `internal` | include (no persist) | include | include | exclude |
| `confidential` | include (no persist, no cache) | include (encrypted persist only) | include | exclude |
| `restricted` | exclude | exclude (unless elevated session) | include (contract-bound) | exclude |

### TTL Rules

Data leaving the framework carries a TTL that the client MUST honour:

| Trust Level | Default TTL | Maximum TTL |
|-------------|-------------|-------------|
| untrusted | 0 (no caching) | 300 seconds |
| semi-trusted | 3600 seconds | 86400 seconds |
| trusted | 86400 seconds | 604800 seconds |
| constrained | 0 (session only) | 3600 seconds |

---

## Browser Contract

### Islands Integration

The Weblisk client framework renders pages as compositions of
independent islands. Each island is a self-contained UI component
that fetches its own data from the server via standard API routes.

```
Page: /dashboard
┌────────────────────────────────────────────┐
│  ┌──────────────────┐  ┌────────────────┐ │
│  │  Navigation       │  │  User Menu     │ │
│  │  (static island)  │  │  GET /api/     │ │
│  │                   │  │  users/me      │ │
│  │                   │  │                │ │
│  └──────────────────┘  └────────────────┘ │
│  ┌──────────────────┐  ┌────────────────┐ │
│  │  Metrics Panel    │  │  Alert Feed    │ │
│  │  GET /api/        │  │  GET /api/     │ │
│  │  health/metrics   │  │  alerts/       │ │
│  │                   │  │  recent        │ │
│  └──────────────────┘  └────────────────┘ │
│  ┌─────────────────────────────────────┐  │
│  │  Strategy Progress                  │  │
│  │  GET /api/strategies/active         │  │
│  └─────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

#### Request Pattern

Every island request carries the same session cookie. The gateway:

1. Validates the session once per request (not once per page)
2. Authorizes each API route independently
3. Routes each request to the appropriate agent/domain
4. Returns the response directly to the island

#### Concurrent Safety

Multiple islands on the same page fire requests concurrently:

- Session validation is read-only (no writes during validation)
- `last_active` updates are debounced (once per 60 seconds)
- CSRF tokens are per-session, not per-request
- Token renewal sets the new cookie on the first response; subsequent
  concurrent responses carry the new cookie too (idempotent set)

#### Island Error Isolation

If one island's agent is down:

```
GET /api/health/metrics     → 200 OK (health domain responding)
GET /api/alerts/recent      → 503 (alerting agent down)
GET /api/strategies/active  → 200 OK (orchestrator responding)
```

The browser renders the page with the failing island showing a loading
or error state. All other islands render normally.

### Zero-Dependency Client Contract

The browser-side contract requires ZERO client libraries, ZERO build
tools, and ZERO framework dependencies:

#### What the Browser Does

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
5. All security enforcement is server-side
```

#### What the Browser NEVER Does

```
- Store tokens in localStorage or sessionStorage (XSS risk)
- Include sensitive data in URLs (leaks via Referer, logs)
- Make decisions about authorization (server-authoritative)
- Direct-connect to agents (only talks to gateway)
- Include any SDK, build step, or dependency for security
```

#### Cookie Specification

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

## Session Security Levels

Sessions across all client types support security levels that
determine what resources can be accessed without additional
verification.

### Levels

| Level | Grants Access To | Requires | Upgrades To |
|-------|-----------------|----------|-------------|
| `standard` | Normal app routes, read operations | Credentials | `elevated` via MFA |
| `elevated` | Admin routes, write operations on sensitive data | Credentials + MFA | `critical` via re-auth + MFA |
| `critical` | Destructive operations, security settings, key rotation | Recent credentials + MFA + per-request confirmation | — |

### Level Transitions

```
standard → elevated:
  User/client completes MFA challenge
  Session claim updated: sec="elevated"
  Level persists for session duration (or configurable TTL)

elevated → critical:
  User/client re-authenticates (even if session is valid)
  MFA challenge completed
  Session claim updated: sec="critical"
  Level has short TTL (default: 15 minutes)
  After TTL → drops back to elevated

Any → standard:
  MFA timeout or explicit downgrade
  Session claim updated: sec="standard"
```

### Per-Request Confirmation (Critical Level)

For destructive operations, even a `critical` session requires
per-request confirmation:

```
Browser:
  X-Confirm: HMAC-SHA256(csrf_secret, method + path + timestamp)

Native client:
  X-Confirm: HMAC-SHA256(device_secret, method + path + timestamp)

Gateway validates HMAC and timestamp freshness (< 30 seconds)
```

---

## Anti-Hijacking Measures

### Session Fixation Prevention

```
- New session ID generated on every authentication event
  (login, MFA, level upgrade, device re-registration)
- Old session ID immediately invalidated
- Server-side state migrated to new ID atomically
```

### Token Replay Prevention

```
- Token includes iat (issued-at) claim
- Renewal generates a new token; old token is blacklisted
- Blacklist TTL = token's remaining lifetime (short, auto-cleanup)
- Concurrent requests during renewal grace period (5 seconds)
  accept both old and new token
```

### Anomaly Detection

The gateway tracks per-session anomalies:

| Anomaly | Action | Threshold |
|---------|--------|-----------|
| Binding hash mismatch | Log + increment counter | 3 → force MFA |
| Rapid IP changes (browser) | Log + increment counter | 5 in 1 minute → invalidate |
| Concurrent sessions from different /16 subnets | Alert | 1 → alert admin |
| Request above session's role level | Log (potential probing) | 10 → temporary IP block |
| CSRF validation failure (browser) | Log | 3 → invalidate session |
| Device binding change (native) | Immediate invalidation | 1 → revoke |
| Certificate mismatch (IoT) | Immediate invalidation | 1 → revoke device |

### Forced Invalidation Triggers

```
- User changes password → revoke ALL sessions (all client types)
- Admin deactivates user → revoke ALL sessions
- Security alert → revoke sessions matching criteria
- User explicitly revokes a session → revoke that session
- Too many anomalies → revoke that session
- Device reported stolen → revoke all sessions for that client ID
- Certificate revoked → reject all connections with that cert
```

---

## Types

### ClientType

Enumeration of supported client types.

| Value | Description |
|-------|-------------|
| `browser` | Web browser with cookie-based session (WLS) |
| `native-mobile` | Mobile application with secure storage (WLC) |
| `native-desktop` | Desktop application with secure storage (WLC) |
| `api-server` | Server-to-server with mTLS |
| `iot-device` | Constrained device with device certificate |

### TrustLevel

Enumeration of trust classifications.

| Value | Description |
|-------|-------------|
| `untrusted` | User-controlled, XSS-vulnerable environment (browsers) |
| `semi-trusted` | App-signed, sandboxed but user-controlled (native apps) |
| `trusted` | Operator-controlled infrastructure (mTLS servers) |
| `constrained` | Limited capability, physical access risk (IoT) |

### ClientCapability

Enumeration of capabilities a client may declare.

| Value | Description |
|-------|-------------|
| `offline` | Client supports offline operation and local persistence |
| `push` | Client supports push notifications |
| `biometric` | Client has biometric authentication hardware |
| `secure-enclave` | Client has hardware-backed secure storage |
| `attestation` | Client supports device/app attestation |

### ClientRecord

Server-side registration for non-browser clients.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| client_id | string | yes | Unique client registration ID |
| client_type | ClientType | yes | Type of client |
| user_id | string | yes | Owning user |
| device_name | string | no | Human-readable device name |
| binding_hash | string | yes | Device/app binding hash at registration |
| capabilities | []ClientCapability | yes | Declared capabilities |
| trust_level | TrustLevel | yes | Assigned trust classification |
| registered_at | int64 | yes | Registration timestamp |
| last_seen | int64 | yes | Last successful authentication |
| revoked | bool | yes | Whether registration has been revoked |
| revoked_reason | string | no | Reason for revocation |
| attestation | object | no | Platform attestation data |

### DataBoundaryTag

Metadata attached to outbound response fields.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| scope | string | yes | Scope classification level |
| ttl | int | yes | Maximum client-side retention in seconds |
| offline_permitted | bool | yes | Whether client may persist this data offline |
| encryption_required | string | no | Required encryption level for persistence (`none`, `aes-256-gcm`, `hardware-backed`) |

---

## Configuration

```yaml
config:
  session_ttl_browser:
    type: int
    default: 86400
    min: 3600
    max: 604800
    description: Browser session TTL in seconds (default 24 hours)

  session_ttl_native:
    type: int
    default: 604800
    min: 86400
    max: 2592000
    description: Native client session TTL in seconds (default 7 days)

  session_ttl_iot:
    type: int
    default: 3600
    min: 300
    max: 86400
    description: IoT device session TTL in seconds (default 1 hour)

  binding_mode:
    type: enum
    default: strict
    values: [strict, standard, relaxed]
    description: Browser client binding strictness

  idle_timeout:
    type: int
    default: 1800
    min: 300
    max: 86400
    description: Idle session timeout in seconds (default 30 minutes)

  renewal_interval:
    type: int
    default: 3600
    min: 300
    max: 43200
    description: Token renewal interval in seconds (default 1 hour)

  anomaly_mfa_threshold:
    type: int
    default: 3
    min: 1
    max: 10
    description: Binding mismatches before forcing MFA step-up

  critical_level_ttl:
    type: int
    default: 900
    min: 60
    max: 3600
    description: Critical security level TTL in seconds (default 15 minutes)

  renewal_grace_period:
    type: int
    default: 5
    min: 1
    max: 30
    description: Seconds during which both old and new tokens are accepted
```

---

## Implementation Notes

- Session token signing MUST use the gateway's Ed25519 key — not a
  shared secret. This allows any party holding the gateway's public
  key to verify a session token without possessing the signing key.
- Browser client binding hashes MUST be computed from raw header
  values, not parsed/normalized versions, to prevent bypass via
  header manipulation.
- The TLS channel binding component (browser sessions) requires
  access to the TLS session — in Go, use
  `tls.ConnectionState().TLSUnique`; in Node.js, use
  `socket.getTLSTicket()`.
- Session cleanup (purging expired sessions) MUST run as a background
  task, not inline with request processing.
- Anomaly detection thresholds are defaults — production deployments
  SHOULD tune them based on observed traffic patterns.
- Browser CSRF tokens are valid for the session's lifetime. They do
  NOT rotate per-request (to support concurrent island requests).
- The 5-second renewal grace period prevents race conditions when
  multiple islands send concurrent requests during token renewal.
- Native client token storage MUST use platform secure storage:
  iOS Keychain, Android EncryptedSharedPreferences / Keystore,
  macOS Keychain, Windows Credential Manager.
- The `cap` (capabilities) claim in WLC tokens is self-declared by
  the client at registration. The server uses capabilities to
  determine what data and operations to permit — but NEVER trusts
  the client to enforce restrictions based on its own capabilities.
- API server (mTLS) sessions have no idle timeout. The TLS connection
  lifetime is the session lifetime. Certificate revocation is the
  only termination mechanism beyond explicit deregistration.
- Data boundary filtering happens at the gateway response layer,
  AFTER agent processing. Agents return full data; the gateway strips
  fields that exceed the client's permitted scope.

---

## Verification Checklist

- [ ] Browser session token uses WLS type (distinct from WLT), signed by gateway's Ed25519 key, with all required claims (sub, iss, iat, exp, sid, roles, bind, csrf, sec, mfa, ren)
- [ ] Native client token uses WLC type with required claims (sub, iss, iat, exp, cid, roles, bind, cap, sec) and is stored in platform secure storage
- [ ] Client type detection follows the defined precedence (mTLS → X-Client-Type → cookie → Bearer → reject)
- [ ] Browser binding hash is SHA-256 of concatenated UA + Accept-Language + IP/24 + TLS session hash
- [ ] Native client binding hash is SHA-256 of device ID + app signature hash
- [ ] Binding mismatch in strict mode (browser) returns 401 and invalidates session immediately
- [ ] Native client binding mismatch immediately invalidates session (device binding is immutable)
- [ ] CSRF protection applies only to browser clients; CSRF token is HMAC-SHA256(csrf_secret, session_id + user_id)
- [ ] Session renewal issues a new token with same sid/cid, updated timestamps — old token blacklisted
- [ ] Browser cookie is set with HttpOnly, Secure, SameSite=Strict, Path=/, scoped to application domain
- [ ] New session ID generated on every authentication event (login, MFA, level upgrade) to prevent fixation
- [ ] Security level transitions: standard → elevated (MFA), elevated → critical (re-auth + MFA, 15-min TTL)
- [ ] Per-request HMAC confirmation required for critical-level destructive operations (all client types)
- [ ] Password change or admin deactivation revokes ALL sessions across ALL client types for that user
- [ ] Anomaly detection thresholds enforce MFA step-up (browser/native) or immediate revocation (IoT) on binding anomalies
- [ ] Concurrent browser island requests are safe: last_active debounced, CSRF per-session, 5-second renewal grace
- [ ] Sessions stored encrypted at rest (AES-256-GCM, HKDF-derived key, per-session salt)
- [ ] Data boundary filtering strips response fields that exceed the client's trust level and scope permissions
- [ ] Outbound responses carry X-Data-Scope, X-Data-TTL, and X-Data-Offline headers for client-side enforcement
- [ ] API server (mTLS) has no session token — certificate IS the identity; revocation via CRL/OCSP
- [ ] IoT devices receive only explicitly permitted fields with aggressive TTL (default: session duration)
