<!-- blueprint
type: architecture
name: threat-model
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/federation, architecture/gateway, architecture/browser-session, architecture/data-security, architecture/admin, architecture/observability]
platform: any
-->

# Threat Model

Comprehensive attack surface analysis and mitigation strategy for
every boundary in the Weblisk architecture — from browser to gateway,
gateway to agent, agent to storage, and hub to hub.

## Overview

Weblisk has five trust boundaries. An attack surface exists at every
point where data crosses a boundary. This document catalogs every
known attack vector at every boundary, the mitigation in place, and
the residual risk.

```
┌────────────────────────────────────┐
│  BOUNDARY 1: Browser ↔ App Gateway │ ← Untrusted external clients
└──────────────────┬─────────────────┘
                   │
┌──────────────────▼─────────────────┐
│  BOUNDARY 2: App Gateway ↔ Agents  │ ← Internal network boundary
└──────────────────┬─────────────────┘
                   │
┌──────────────────▼─────────────────┐
│  BOUNDARY 3: Agents ↔ Storage      │ ← Data persistence boundary
└────────────────────────────────────┘

┌────────────────────────────────────┐
│  BOUNDARY 4: Operator ↔ Admin GW   │ ← Privileged access boundary
└────────────────────────────────────┘

┌────────────────────────────────────┐
│  BOUNDARY 5: Hub ↔ Hub (Federation)│ ← Cross-organization boundary
└────────────────────────────────────┘
```

## Design Principles

1. **Assume breach at every layer** — Each boundary enforces
   security independently. A compromised gateway does not give
   access to storage. A compromised agent does not give access to
   other agents.
2. **Deny by default** — Every request is denied unless an explicit
   policy allows it. No implicit trust between components.
3. **Least privilege everywhere** — Components have only the
   permissions they need. Agents cannot read other agents' data.
   Users cannot access other users' data. Operators cannot exceed
   their role.
4. **Audit everything, alert on anomalies** — Every security-relevant
   event is logged. Anomalous patterns trigger alerts before damage
   is done.
5. **Defense in depth** — Multiple independent controls at each
   boundary. No single point of failure in the security model.

---

## Boundary 1: Browser ↔ Application Gateway

This is the highest-risk boundary. The browser is untrusted, the
network is untrusted, and the attacker has full control of the
client.

### Attack Surface Map

#### Transport Layer

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.1 | **Eavesdropping** | Attacker intercepts HTTP traffic | TLS 1.2+ required; HSTS with includeSubDomains; preload list | Gateway TLS termination |
| 1.2 | **TLS downgrade** | Force client to older TLS version | `min_version: "1.2"` in gateway config; no SSLv3/TLS1.0/1.1 cipher suites | Gateway TLS config |
| 1.3 | **Certificate spoofing** | Fake certificate for MITM | Certificate Transparency logs; HSTS preload; CAA DNS records | DNS + CA policy |
| 1.4 | **Protocol confusion** | HTTP/2 desync, request smuggling | Strict HTTP parsing; reject ambiguous requests; no connection reuse to backends | Gateway request parser |

#### Authentication

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.5 | **Credential stuffing** | Automated login with leaked passwords | Rate limit auth endpoints (10/min/IP); account lockout after 5 failures; CAPTCHA after 3 failures | Gateway rate limiter |
| 1.6 | **Brute force** | Exhaustive password guessing | Same as 1.5 + progressive delays (1s, 2s, 4s, 8s); minimum password complexity; bcrypt/argon2id with high cost | Gateway + auth pattern |
| 1.7 | **Credential phishing** | Trick user into submitting credentials elsewhere | SameSite=Strict cookies; CSP prevents form action to external origins; FIDO2/WebAuthn as phishing-resistant MFA | Browser policy + MFA |
| 1.8 | **Password spray** | Try common passwords across many accounts | Per-IP rate limiting (not per-account); global auth failure monitoring; alert on distributed patterns | Gateway rate limiter + alerting agent |

#### Session Attacks

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.9 | **Session hijacking** | Steal session cookie via XSS or network interception | HttpOnly + Secure + SameSite=Strict cookie; Ed25519-signed session token; client binding hash (UA + IP/24 + TLS) | Browser session spec |
| 1.10 | **Session fixation** | Set a known session ID before victim authenticates | New session ID on every auth event (login, MFA, level upgrade); old session immediately invalidated | Browser session spec |
| 1.11 | **Session replay** | Reuse a captured session token | Token binding to TLS channel; short renewal window (1 hour); blacklist old tokens after renewal | Browser session spec |
| 1.12 | **Cookie theft via subdomain** | Attacker-controlled subdomain reads main domain cookies | `Domain` set to exact application domain; no wildcard domain cookies; separate domains for user content | Cookie policy |
| 1.13 | **CSRF** | Trick authenticated user into making unintended requests | SameSite=Strict + Double Submit Cookie (HMAC-based); CSRF token in X-CSRF-Token header; Origin/Referer validation | Gateway CSRF engine |

#### Injection

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.14 | **XSS (reflected)** | Inject script via URL parameters reflected in response | Gateway sets `Content-Security-Policy` with strict `script-src`; response sanitization strips inline scripts; `X-Content-Type-Options: nosniff` | Gateway response headers |
| 1.15 | **XSS (stored)** | Inject script via stored data rendered later | Input validation at gateway edge AND at agent; output encoding in responses; CSP prevents execution even if stored | Defense in depth |
| 1.16 | **XSS (DOM-based)** | Client-side script manipulation | Weblisk islands use server-rendered data, NOT client-side template interpolation; CSP `script-src 'self'` prevents inline execution | Islands architecture |
| 1.17 | **SQL injection** | Manipulate database queries via input | Gateway validates input structure; agents use parameterized queries only; no dynamic query construction from user input | Agent implementation |
| 1.18 | **Command injection** | Execute system commands via input | No shell execution from user input; agent tasks are pre-defined actions, not arbitrary commands | Agent protocol |
| 1.19 | **Path traversal** | Access files outside intended directory | Gateway validates URL paths (no `..`, no null bytes, no encoded traversal); file-serving routes use allowlists | Gateway request validation |
| 1.20 | **Header injection** | Inject HTTP headers via user input | Gateway strips CRLF from all user-controlled values before forwarding; no user input in response headers | Gateway sanitization |
| 1.21 | **JSON injection** | Malformed JSON payload manipulation | Strict JSON parser (reject duplicate keys, reject trailing commas); Content-Length validation; schema validation at agent | Gateway + agent validation |

#### Client-Side

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.22 | **Clickjacking** | Embed application in attacker's iframe | `X-Frame-Options: DENY`; `Content-Security-Policy: frame-ancestors 'none'` | Gateway response headers |
| 1.23 | **Open redirect** | Redirect user to attacker's site after login | Redirect URLs validated against allowlist; no user-controlled redirect targets without validation | Gateway auth flow |
| 1.24 | **MIME sniffing** | Browser interprets file as different type | `X-Content-Type-Options: nosniff` on every response | Gateway response headers |
| 1.25 | **Content injection** | Inject content via user-controlled data in page | Server-side rendering with strict output encoding; no raw user data in HTML context | Islands architecture |
| 1.26 | **Tabnabbing** | Opened link modifies opener page | `rel="noopener noreferrer"` on external links; `Cross-Origin-Opener-Policy: same-origin` | Gateway response headers |

#### Denial of Service

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.27 | **HTTP flood** | Overwhelm server with requests | Per-IP rate limiting; global rate limiting; connection limits; request queuing with backpressure | Gateway rate limiter |
| 1.28 | **Slowloris** | Hold connections open with slow headers | Connection timeout (30s for headers); minimum data rate enforcement; max concurrent connections per IP | Gateway connection management |
| 1.29 | **Large payload** | Send huge request bodies | `Content-Length` limit per route (default 1MB, file uploads: configurable); reject before reading full body | Gateway request validation |
| 1.30 | **Regex DoS (ReDoS)** | Craft input that causes catastrophic regex backtracking | No user input in regex evaluation; pre-compiled regex patterns; timeout on pattern matching (100ms) | Agent implementation |
| 1.31 | **Hash collision DoS** | Exploit hash table collision behavior | Use hash-DoS-resistant hash functions (SipHash); limit query parameter count; limit JSON object depth | Gateway + runtime |
| 1.32 | **Compression bomb** | Send compressed body that expands to huge size | Limit decompressed body size; decompress incrementally with size tracking; reject if decompressed > 10x compressed | Gateway decompression |

#### Information Disclosure

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 1.33 | **Error message leakage** | Stack traces, internal paths in error responses | Generic error messages to browser (500 with request_id only); full errors logged server-side | Gateway response sanitization |
| 1.34 | **Server identification** | Server header reveals technology stack | Strip `Server`, `X-Powered-By`, `X-AspNet-Version` from all responses | Gateway response sanitization |
| 1.35 | **Directory listing** | Access file listings via path guessing | Static file routes use explicit allowlists; no directory listing; 404 for unlisted paths | Gateway route table |
| 1.36 | **Timing side-channel** | Infer valid usernames from login timing | Constant-time comparison for credentials; same response time for valid/invalid usernames; bcrypt always runs | Auth implementation |
| 1.37 | **Version disclosure** | API version headers reveal deployment details | Version headers only in internal responses; stripped at gateway before reaching browser | Gateway response sanitization |
| 1.38 | **Source map exposure** | JavaScript source maps reveal code structure | No source maps in production; CSP prevents source map fetching if accidentally deployed | Deployment config |

---

## Boundary 2: Application Gateway ↔ Agent Network

This is an internal boundary but is NOT implicitly trusted. The
gateway authenticates to agents, and agents validate the gateway's
identity on every request.

### Attack Surface Map

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 2.1 | **Rogue gateway** | Attacker deploys fake gateway that claims to be legitimate | Agents verify `Authorization` header contains valid WLT signed by registered gateway's Ed25519 key; orchestrator validates gateway registration | Protocol identity |
| 2.2 | **Header spoofing** | Attacker injects `X-Gateway-*` headers from non-gateway source | Agents ONLY accept `X-Gateway-*` headers from the registered gateway IP/identity; orchestrator strips these headers from non-gateway requests | Agent validation |
| 2.3 | **Privilege escalation via header** | Gateway sends `X-Gateway-Roles: admin` for non-admin user | Gateway's role injection is validated against session state (server-side, not from browser); agents can verify via orchestrator callback for critical operations | Defense in depth |
| 2.4 | **Agent impersonation** | Attacker poses as a legitimate agent | Every agent has unique Ed25519 key pair; orchestrator verifies agent identity on registration and health checks; behavioral fingerprinting detects drift | Protocol identity + lifecycle |
| 2.5 | **Man-in-the-middle (internal)** | Intercept gateway-to-agent traffic | mTLS between gateway and agents (zero-trust mode); or TLS + trusted network isolation; Ed25519-signed messages provide additional integrity | Network + protocol |
| 2.6 | **SSRF via gateway** | Trick gateway into making requests to internal services | Route table uses allowlisted agent targets only; no user-controlled URLs in forwarding; gateway resolves targets from orchestrator registry, not from request input | Gateway route table |
| 2.7 | **Agent overload** | Route excessive traffic to a single agent | Per-agent rate limiting at gateway; circuit breaker (3 failures → open for 30s); orchestrator redistributes if agent reports degraded | Gateway + orchestrator |
| 2.8 | **Data exfiltration via agent** | Compromised agent sends data to external endpoint | Agents have no outbound network access except to orchestrator and configured storage; egress firewall rules; agent behavioral monitoring | Network policy + monitoring |
| 2.9 | **Deserialization attack** | Malicious payload in agent request/response | JSON-only protocol (no binary serialization); strict schema validation on all messages; no arbitrary object deserialization | Protocol spec |
| 2.10 | **Replay attack (internal)** | Replay a valid gateway-to-agent request | Request includes `X-Request-Id` (UUID) + `X-Trace-Id`; agents track recent request IDs; duplicate requests rejected within replay window (300 seconds) | Protocol spec |

### Internal Network Model

```
ZERO-TRUST MODE (recommended for production):
  Gateway ──mTLS──→ Orchestrator ──mTLS──→ Agents
  Every hop is encrypted and mutually authenticated.
  No implicit trust based on network position.

TRUSTED NETWORK MODE (acceptable for single-host deployments):
  Gateway ──TLS──→ Orchestrator ──HTTP──→ Agents (localhost only)
  TLS at the gateway; plain HTTP on loopback interface.
  Agents bind to 127.0.0.1 only — unreachable from external network.
```

---

## Boundary 3: Agents ↔ Storage

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 3.1 | **SQL injection (agent-side)** | Agent constructs queries from task input | Parameterized queries only; no string concatenation for SQL; ORM or query builder with auto-parameterization | Agent implementation |
| 3.2 | **Unencrypted storage** | Data at rest readable by filesystem access | AES-256-GCM encryption for stored data; agents responsible for encryption-at-rest of their own data; HKDF-derived keys from Ed25519 identity; encrypted backups | Agent implementation |
| 3.3 | **Key compromise** | Encryption key stolen from agent process | Keys loaded into memory only at startup; not written to disk as plaintext; keys derived via HKDF from root key; root key in secure enclave or HSM where available | Key management |
| 3.4 | **Backup exposure** | Unencrypted database backup accessed | Backups encrypted at same level as primary storage; backup access logged and restricted | Agent implementation |
| 3.5 | **Connection string leakage** | Database credentials in logs or config files | Connection strings from environment variables only (never in config files); masked in logs; rotated on schedule | Observability + deployment |
| 3.6 | **Excessive data access** | Agent reads more data than needed for task | Agents scoped to their own storage namespace; cross-agent data access goes through orchestrator (never direct); query result size limits | Storage spec |
| 3.7 | **Data tampering** | Unauthorized modification of stored data | Write operations require valid task context (task_id from orchestrator); audit trail on all writes; integrity checksums on critical records | Orchestrator + audit |
| 3.8 | **Log injection** | Malicious data written to logs that is later rendered or parsed | Structured JSON logging only (no string interpolation); log field values are escaped; log viewer treats all fields as data, not markup | Observability spec |

---

## Boundary 4: Operator ↔ Admin Gateway

The Weblisk platform admin portal is a **completely separate entry
point** from the application gateway. It has its own domain, its own
TLS certificate, its own session model, and its own threat profile.

This boundary covers the platform admin only — the management of
orchestrators, agents, domains, federation, and strategies. Application-
specific admin features (e.g. a CMS dashboard, a product manager) are
normal application routes that go through the application gateway and
are covered by Boundary 1.

See the **Platform Admin** blueprint for the full separation
architecture. The key difference: platform admin traffic NEVER flows
through the application gateway.

### Why Separate

| Concern | Application Gateway | Admin Gateway |
|---------|-------------------|---------------|
| Audience | End users (untrusted, high volume) | Operators (trusted, low volume) |
| Auth model | User credentials → session cookie | Operator Ed25519 key → operator token |
| Session binding | Device fingerprint + IP/24 | Operator key + IP allowlist |
| Network exposure | Public internet | Private network or VPN + IP allowlist |
| MFA | Optional (policy-driven) | Always required |
| Rate limits | High (accommodate user traffic) | Low (operators don't need burst) |
| Attack surface | Broad (supports all user interactions) | Narrow (read-heavy, few writes) |
| Compromise impact | User data exposure | Full system control |

### Admin-Specific Threats

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 4.1 | **Operator key theft** | Attacker steals Ed25519 private key | Key stored encrypted on disk (passphrase-protected); MFA required even with valid key; key revocation via another admin | Operator identity + MFA |
| 4.2 | **Admin portal discovery** | Attacker finds admin URL and probes it | Admin gateway on separate domain/port; not linked from application; IP allowlist rejects unknown sources before any processing | Network isolation |
| 4.3 | **Privilege escalation** | Lower-role operator gains admin access | Role hierarchy enforced server-side; role changes require admin approval + audit log entry; no client-side role checks | Admin auth middleware |
| 4.4 | **Admin session hijacking** | Steal admin session cookie | Admin sessions use strict IP binding (exact IP, not /24); sessions expire in 4 hours (not 24); MFA required for session creation | Admin session policy |
| 4.5 | **Destructive action abuse** | Compromised admin deletes agents or federation peers | Destructive actions require per-request HMAC confirmation; critical actions require two-operator approval (4-eyes principle); all actions in immutable audit log | Admin API + audit |
| 4.6 | **Audit log tampering** | Attacker covers tracks by modifying audit log | Append-only storage; hash chain integrity (each entry includes hash of previous); external audit log shipping (cannot tamper remote copy) | Audit architecture |
| 4.7 | **Bootstrap attack** | Attacker registers as first operator before legitimate admin | Bootstrap window logged prominently; bootstrap requires physical/console access; operator registration event fires alert to all configured channels | Bootstrap flow |
| 4.8 | **Internal network lateral movement** | Attacker who compromised app gateway reaches admin gateway | Admin gateway and app gateway share NO network path; admin gateway binds to separate interface/VLAN; firewall rules prevent cross-gateway traffic | Network segmentation |

---

## Boundary 5: Hub ↔ Hub (Federation)

| # | Attack Vector | Description | Mitigation | Control |
|---|--------------|-------------|------------|---------|
| 5.1 | **Hub impersonation** | Fake hub claims to be a trusted peer | Mutual Ed25519 authentication; hub identity verified against known public key from peering ceremony; manifest signature validation | Federation protocol |
| 5.2 | **Data contract violation** | Peer sends forbidden fields or omits required fields | Receiving hub validates every response against data contract; violations logged + alert; trust tier downgrade on repeated violations | Federation data contracts |
| 5.3 | **Key rotation race** | Attacker uses old key during rotation window | Grace period accepts both old and new key; old key has strict expiry; key rotation ceremony requires both sides to acknowledge | Federation key rotation |
| 5.4 | **Cross-boundary data leak** | Sensitive data leaves jurisdiction | Federation data contracts control which fields cross boundaries; forbidden fields stripped by sending gateway; receiving hub independently validates | Federation data contracts |
| 5.5 | **Federation amplification** | Peer sends task that triggers expensive computation | Per-peer rate limiting; task quotas per trust tier; circuit breaker on peer overuse | Orchestrator |
| 5.6 | **Supply chain via federation** | Compromised peer sends poisoned data | All federated data treated as untrusted input; full validation + sanitization; data quarantine for first-time data types | Agent validation |
| 5.7 | **Trust tier abuse** | Peer with partner-level access acts like private peer | Trust tier enforced per-request; capabilities scoped to tier; tier downgrade on violation | Federation protocol |
| 5.8 | **Metadata leakage** | Hub topology/capabilities exposed to unauthorized peers | Capability discovery requires authenticated peering; public hubs expose only their published listing; internal topology never exposed | Hub protocol |

---

## OWASP Top 10 Coverage

Cross-reference of OWASP 2021 Top 10 against Weblisk controls:

| OWASP | Category | Primary Controls | Vectors |
|-------|----------|-----------------|---------|
| A01 | Broken Access Control | ABAC policy engine; deny-by-default; role hierarchy; owner-based access; data masking by classification | 1.13, 2.3, 4.3 |
| A02 | Cryptographic Failures | AES-256-GCM at rest; TLS 1.2+ in transit; Ed25519 for identity; HKDF key derivation; no hardcoded secrets | 1.1, 1.2, 3.2, 3.3 |
| A03 | Injection | Parameterized queries; input validation at gateway + agent; JSON-only protocol; no shell execution from input | 1.17, 1.18, 1.19, 1.20, 1.21, 3.1 |
| A04 | Insecure Design | Threat model (this document); zero-trust internal network; defense in depth; classification-first data model | All boundaries |
| A05 | Security Misconfiguration | Secure defaults (deny-by-default, TLS required, MFA for admin); no debug mode in production; stripped server headers | 1.33, 1.34, 1.38 |
| A06 | Vulnerable Components | Security scanner agent audits dependencies; security domain scores component freshness; agent behavioral fingerprinting detects drift | 2.4, 5.6 |
| A07 | Identification and Authentication Failures | Ed25519 cryptographic identity; bcrypt/argon2id passwords; MFA support; session binding; account lockout | 1.5-1.12, 4.1 |
| A08 | Software and Data Integrity Failures | Ed25519 signed messages; hash chain audit logs; agent registration verification; federation manifest signatures | 2.1, 2.4, 3.7, 4.6, 5.1 |
| A09 | Security Logging and Monitoring Failures | Structured logging; full audit trail; anomaly detection; alerting agent; distributed tracing | All boundaries |
| A10 | Server-Side Request Forgery | Route table allowlists; no user-controlled URLs in agent forwarding; agent egress firewall | 2.6, 2.8 |

---

## Attack Chains

Individual attack vectors are concerning. Attack chains — sequences
of exploits that compound — are dangerous. These are the chains we
specifically design against:

### Chain 1: XSS → Session Theft → Account Takeover

```
Attack:    Stored XSS injects script → script reads session → attacker uses session
Broken at: CSP prevents script execution (1.15) AND HttpOnly prevents cookie access
           (1.9) AND session binding rejects different client context (1.9)
Layers:    3 independent controls must ALL be bypassed
```

### Chain 2: Credential Stuff → Admin Probe → Privilege Escalation

```
Attack:    Leaked creds → login → discover admin paths → access admin functions
Broken at: Rate limiting blocks credential stuffing (1.5) AND admin is on separate
           domain/port (4.2) AND admin requires Ed25519 key + MFA (4.1)
Layers:    4 independent controls (rate limit, domain separation, key auth, MFA)
```

### Chain 3: SSRF → Internal Service → Data Exfiltration

```
Attack:    Trick gateway into calling internal service → read internal data → exfil
Broken at: Route table uses allowlisted targets only (2.6) AND agents have no
           outbound internet (2.8) AND data masking strips classified data (1.14)
Layers:    3 independent controls
```

### Chain 4: Compromised Agent → Lateral Movement → Storage Access

```
Attack:    Exploit agent vulnerability → access other agents → read all storage
Broken at: Agents scoped to own storage namespace (3.6) AND cross-agent access
           requires orchestrator routing (2.4) AND mTLS prevents network lateral
           movement (2.5)
Layers:    3 independent controls
```

### Chain 5: Federation Peer Compromise → Data Leak → Compliance Violation

```
Attack:    Compromised peer sends query → receives data beyond contract → data
           leaves jurisdiction
Broken at: Data contracts enforce field-level filtering (5.2) AND Restricted data
           never crosses federation (5.4) AND jurisdiction check before transmission
           (5.4)
Layers:    3 independent controls
```

---

## Security Testing Requirements

### Per Boundary

| Boundary | Required Tests |
|----------|---------------|
| Browser ↔ App Gateway | OWASP ZAP scan; TLS configuration audit; CSP validator; rate limit verification; session management tests |
| App Gateway ↔ Agents | mTLS validation; header spoofing tests; SSRF tests; replay detection tests |
| Agents ↔ Storage | SQL injection scan; encryption-at-rest verification; key rotation test |
| Operator ↔ Admin Gateway | IP allowlist enforcement; MFA bypass attempts; role escalation tests; destructive action confirmation tests |
| Hub ↔ Hub | Identity verification; data contract enforcement; key rotation ceremony; trust tier boundary tests |

### Continuous

| Check | Frequency | Tool/Agent |
|-------|-----------|------------|
| Dependency vulnerability scan | Every deploy + daily | security-scanner agent |
| TLS certificate expiry | Daily | uptime-checker agent |
| OWASP baseline scan | Weekly | External scanner or security-scanner agent |
| Penetration test | Quarterly | External engagement |
| Audit log integrity (hash chain) | Daily | Observability system |
| Key rotation compliance | Daily | Admin API health check |
| Rate limiter effectiveness | On deploy | Load test suite |

---

## Residual Risk Register

After all mitigations, these residual risks remain:

| Risk | Likelihood | Impact | Mitigation Status | Notes |
|------|-----------|--------|-------------------|-------|
| Zero-day in TLS implementation | Low | High | Monitor CVEs; patch within 24h of disclosure | Depends on runtime TLS library |
| Operator key compromise via physical access | Low | Critical | MFA + key passphrase; revocation by other admin | Human factor — cannot fully eliminate |
| Side-channel attacks on Ed25519 | Very Low | High | Use constant-time implementations only | Validated by library choice |
| DDoS beyond rate limiter capacity | Medium | Medium | External DDoS protection (CDN/WAF) recommended for high-traffic deployments | Out of scope for application layer |
| Social engineering of operators | Low | Critical | Security training; 4-eyes for destructive actions; audit trail | Human factor |
| Supply chain attack on dependencies | Low | High | Dependency scanning; lockfile pinning; minimal dependency count | Weblisk itself is zero-dependency on client side |

---

## Implementation Notes

- This threat model MUST be reviewed and updated when new features
  are added, new boundaries are introduced, or new attack techniques
  are published.
- Every numbered vector (1.1 through 5.8) MUST have a corresponding
  test in the conformance test suite.
- The attack chain analysis MUST be validated during penetration
  testing — testers should attempt each chain and verify that all
  stated controls hold.
- Residual risks MUST be accepted by the deployment operator and
  documented in the deployment's risk register.
- The OWASP Top 10 mapping SHOULD be updated when new OWASP releases
  are published (next expected: 2025/2026).

## Verification Checklist

- [ ] Auth endpoints enforce rate limit of 10 requests/min/IP with account lockout after 5 failures and CAPTCHA after 3
- [ ] Session cookies are HttpOnly + Secure + SameSite=Strict with Ed25519-signed tokens and client binding hash
- [ ] CSP with strict script-src is set on every response; X-Frame-Options: DENY prevents clickjacking
- [ ] Gateway route table uses allowlisted agent targets only — no user-controlled URLs in forwarding (SSRF prevention)
- [ ] Internal replay detection rejects duplicate X-Request-Id values within a 300-second window
- [ ] Agents in zero-trust mode use mTLS for all inter-component communication; trusted mode agents bind to 127.0.0.1 only
- [ ] Admin gateway is on a separate domain/port, unreachable from the application gateway's network path
- [ ] Destructive admin actions require per-request HMAC confirmation and 4-eyes approval with immutable audit logging
- [ ] Federation data contracts enforce field-level filtering; forbidden fields stripped by sender, independently validated by receiver
- [ ] Every numbered attack vector (1.1–5.8) has a corresponding test in the conformance test suite
- [ ] Attack chains 1–5 are validated during penetration testing to confirm all stated control layers hold
- [ ] Continuous security checks run at specified frequencies: dependency scan on every deploy, TLS expiry daily, OWASP baseline weekly
- [ ] Residual risks are documented and accepted by the deployment operator in the deployment's risk register
