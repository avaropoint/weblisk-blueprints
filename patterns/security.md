<!-- blueprint
type: pattern
name: security
version: 1.0.0
requires: [protocol/spec, protocol/types, protocol/identity, patterns/observability]
platform: any
tier: free
-->

# Security Pattern

Centralized security baseline for all Weblisk agents, domains, and
infrastructure. Defines transport security, input validation, output
sanitization, security headers, zero-trust communication, and threat
classification. Every agent inherits these requirements.

## Overview

Security is currently spread across multiple files: `protocol/identity`
handles cryptographic identity, `patterns/secrets` handles credential
management, `patterns/rate-limiting` handles throughput control. This
pattern provides the foundational security layer that ALL agents must
conform to:

1. **Transport security** — TLS, certificate management
2. **Input validation** — request validation at system boundaries
3. **Output sanitization** — prevent information leakage
4. **Security headers** — standard HTTP security headers
5. **Zero-trust model** — verify every request, trust nothing
6. **Threat classification** — categorize and respond to threats
7. **Security events** — standardized security event logging

This pattern is extended by every agent. It works alongside (not
replacing) `protocol/identity` for crypto, `patterns/secrets` for
credential management, and `patterns/rate-limiting` for throughput.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, detail]
        - name: RequestLimits
          fields_used: [max_body_size, max_nesting_depth]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, retryable]
        - name: Token
          fields_used: [capabilities, expires_at, signature]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentIdentity
          fields_used: [public_key, name, capabilities]
        - name: MessageSignature
          fields_used: [algorithm, signature, key_id]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: LogEvent
          fields_used: [event_type, level, detail, timestamp]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Zero-trust by default** — Every request is verified regardless of network origin; agents on the same network receive no implicit trust.
2. **Defense in depth** — Multiple overlapping security layers (TLS, input validation, output sanitization, signature verification) ensure no single failure compromises the system.
3. **Fail closed** — When security checks encounter errors or ambiguity, requests are rejected rather than allowed through.
4. **Least privilege** — Agents receive only the capabilities they declare; token capabilities are checked against every requested operation.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: input-validation
      description: Validate all input crossing system boundaries against size, type, and format rules
      parameters:
        - name: max_body_size
          type: int
          required: true
          description: Maximum request body size in bytes
        - name: max_nesting_depth
          type: int
          required: true
          description: Maximum JSON nesting depth allowed
        - name: max_string_length
          type: int
          required: true
          description: Maximum string field length in characters
      inherits: Validation flow for all HTTP and message inputs
      overridable: true
      override_constraints: Cannot increase max_body_size beyond 10 MB
    - name: output-sanitization
      description: Strip sensitive data from all outgoing responses
      parameters:
        - name: environment
          type: enum(production, staging, development)
          required: true
          description: Controls sanitization strictness
      inherits: Response filtering pipeline for all agents
      overridable: false
      override_constraints: Cannot disable in production
    - name: threat-classification
      description: Classify and respond to security events by threat level
      parameters:
        - name: level
          type: enum(critical, high, medium, low, info)
          required: true
          description: Threat severity level
      inherits: Standardized threat levels and auto-response behavior
      overridable: true
      override_constraints: Critical and high levels cannot be downgraded
  types:
    - name: SecurityEvent
      description: Structured security event with threat level and classification
      inherited_by: Threat Classification section
    - name: TLSConfig
      description: TLS mode and certificate management configuration
      inherited_by: Transport Security section
    - name: CORSConfig
      description: Cross-origin resource sharing configuration
      inherited_by: Security Headers section
  events:
    - topic: security.invalid_signature
      description: Message signature verification failed
      payload: {source, target, detail, remote_addr, trace_id, timestamp}
    - topic: security.capability_violation
      description: Agent attempted an unauthorized operation
      payload: {source, target, capability, trace_id, timestamp}
    - topic: security.path_traversal_attempt
      description: File path traversal attack detected
      payload: {source, path, remote_addr, timestamp}
```

---

## Transport Security

### TLS Requirements

| Environment | Requirement |
|-------------|-------------|
| Production | TLS 1.2+ REQUIRED for all inter-agent communication |
| Staging | TLS 1.2+ REQUIRED |
| Development | TLS RECOMMENDED. Plain HTTP permitted on localhost only |

### Certificate Management

```yaml
tls:
  mode: auto | manual | platform
  min_version: "1.2"
  
  # auto mode: framework manages certificates
  auto:
    provider: letsencrypt | self-signed
    renewal_days_before: 30
  
  # manual mode: operator provides certificates
  manual:
    cert_path_env: WL_TLS_CERT_PATH
    key_path_env: WL_TLS_KEY_PATH
  
  # platform mode: TLS terminated by platform (Cloudflare, ALB)
  platform:
    trust_proxy_headers: true
    required_header: X-Forwarded-Proto
```

### Inter-Agent TLS

When agents communicate directly (via `POST /v1/message`), they
MUST use TLS in production environments. The agent framework
handles certificate verification:

```
1. Agent resolves target URL from service directory
2. If URL scheme is https → verify server certificate
3. If URL scheme is http AND environment != development → reject
4. If certificate verification fails → reject with TLS_ERROR
```

---

## Input Validation

All input crossing a system boundary MUST be validated before
processing. System boundaries include:

- HTTP request bodies
- Message payloads from other agents
- File content read from disk
- External API responses
- Environment variable values

### Validation Rules

| Rule | Applies To | Requirement |
|------|-----------|-------------|
| Size limits | Request bodies | 1 MB default, 10 MB for task execution (per protocol/spec) |
| Content-Type | HTTP requests | MUST be application/json for all protocol endpoints |
| Field presence | Required fields | MUST return 400 if missing |
| Field types | All fields | MUST match declared type |
| String length | String fields | MUST enforce max length (default: 65,536 chars) |
| Array size | Array fields | MUST enforce max items (default: 10,000) |
| Object depth | Nested objects | MUST enforce max nesting depth (default: 20) |
| Character encoding | String fields | MUST be valid UTF-8. Reject invalid sequences |
| Numeric range | Integer/float | MUST enforce declared min/max constraints |
| Path traversal | File paths | MUST reject `..`, absolute paths, symlinks outside workspace |
| URL validation | URL fields | MUST validate scheme (http/https only) and reject javascript: |

### Validation Flow

```
1. Check Content-Type header
2. Check body size against limit
3. Parse JSON (reject on syntax error)
4. Check nesting depth
5. Validate required fields
6. Validate field types
7. Validate constraints (length, range, pattern)
8. Validate domain-specific rules
9. If any fail → return 400 with ErrorResponse listing violations
```

---

## Output Sanitization

Agents MUST sanitize outgoing responses to prevent information
leakage:

### Sanitization Rules

| Rule | Description |
|------|-------------|
| No stack traces | Error responses MUST NOT include stack traces in production |
| No internal paths | Absolute file paths MUST be stripped from responses |
| No secrets | Secrets MUST never appear in response bodies or logs |
| No agent internals | Internal state (config, policies, keys) MUST NOT be exposed |
| Error messages | Generic error messages for clients. Detailed errors logged server-side |
| Version details | Agent version is public (via describe). Runtime version is not |

### Response Filtering

```
Before sending any HTTP response:
1. Remove any field containing "password", "secret", "key", "token"
   (unless the field is explicitly declared as a response field)
2. Replace absolute file paths with relative paths
3. If environment = production:
   Strip "detail" from ErrorResponse unless error is DATA_CONTRACT_VIOLATION
4. Log the full unfiltered response at DEBUG level for diagnostics
```

---

## Security Headers

All HTTP responses from agents MUST include these headers:

### Required Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Request-ID` | `<uuid>` | Request correlation |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HSTS (production only) |
| `Cache-Control` | `no-store` | Prevent caching of API responses |
| `Content-Type` | `application/json; charset=utf-8` | Explicit content type |

### CORS Configuration

For agents that serve browser-facing endpoints:

```yaml
cors:
  enabled: false                    # disabled by default for agents
  allowed_origins: []               # explicit origin list, never "*" in production
  allowed_methods: [GET, POST]
  allowed_headers: [Content-Type, Authorization, X-CSRF-Token]
  max_age: 3600
```

CORS is disabled by default because agents communicate server-to-
server. Agents that serve browser-facing APIs (api-rest, auth-session)
MUST configure CORS explicitly.

---

## Zero-Trust Model

Weblisk follows a zero-trust security model where every request is
verified regardless of source:

### Trust Principles

| Principle | Implementation |
|-----------|---------------|
| Verify identity | Every request carries a signed token or signature |
| Verify capability | Check token capabilities against requested operation |
| Verify integrity | Message signatures verify payload hasn't been tampered |
| Least privilege | Agents receive only the capabilities they declared |
| No implicit trust | Agents on the same network are NOT implicitly trusted |
| Verify at every hop | Each agent verifies incoming signatures independently |

### Request Verification Chain

```
Inbound request arrives at agent:
  1. Verify TLS (production: reject non-TLS)
  2. Check request size limits
  3. If protocol endpoint (execute/message):
     a. Extract token from body
     b. Verify token signature against issuer's public key
     c. Verify token is not expired
     d. Verify token capabilities cover the requested operation
  4. If message endpoint:
     a. Verify message signature against sender's public key
        (from service directory)
     b. Verify sender is in service directory (known agent)
  5. If governance endpoint:
     a. Verify directive signature against orchestrator's public key
  6. If all checks pass → process request
  7. If any check fails → reject with appropriate error code
```

---

## Threat Classification

Security events are classified by threat level to drive response:

### Threat Levels

| Level | Description | Auto-Response |
|-------|-------------|---------------|
| `critical` | Active exploitation attempt | Block source, alert admin immediately |
| `high` | Likely attack or compromise indicator | Block source, alert operator |
| `medium` | Suspicious activity | Log, rate-limit source, alert if repeated |
| `low` | Policy violation or anomaly | Log only |
| `info` | Security-relevant event (not a threat) | Log only |

### Standard Security Events

| Event | Level | Trigger |
|-------|-------|---------|
| `invalid_signature` | high | Message signature verification fails |
| `expired_token` | medium | Token past expiry is used |
| `unknown_agent` | medium | Message from agent not in service directory |
| `capability_violation` | high | Agent attempts unauthorized operation |
| `rate_limit_exceeded` | medium | Agent exceeds rate limit |
| `path_traversal_attempt` | critical | File path contains `..` or escape |
| `oversized_request` | medium | Request body exceeds size limit |
| `replay_attempt` | high | Registration timestamp outside window |
| `tls_violation` | high | Non-TLS request in production |
| `governance_violation` | high | Agent violates governance policy |
| `key_rotation` | info | Agent or orchestrator rotates keys |
| `registration` | info | Agent registers or deregisters |

### Security Event Format

```json
{
  "event_type": "security",
  "level": "high",
  "event": "invalid_signature",
  "source": "orchestrator",
  "target": "seo-analyzer",
  "detail": "Message signature verification failed for action: scan_html",
  "remote_addr": "10.0.1.5",
  "trace_id": "abc123",
  "timestamp": 1713264000
}
```

Security events flow through the messaging bus on topic
`security.<event-name>`. The alerting agent subscribes to
security events and routes notifications per severity.

---

## Implementation Notes

- Security is defense-in-depth — no single layer is sufficient alone
- Input validation runs before any business logic; output sanitization runs after
- TLS enforcement applies to production only — localhost communication is permitted in development
- The zero-trust model means every request is authenticated, even between co-located agents
- Security events should be emitted for all threat classification matches, not just blocks
- The OWASP Top 10 alignment is a minimum — implementations should consider domain-specific threats

---

## Verification Checklist

Every agent MUST meet these security requirements. This checklist
is inherited and extends the agent-specific verification checklist.

### Transport

- [ ] TLS 1.2+ enforced in production environments
- [ ] Non-TLS requests rejected in production (except /health)
- [ ] Certificate validation enabled for outbound HTTPS requests

### Input

- [ ] Request body size limits enforced (1 MB default)
- [ ] Content-Type validated as application/json
- [ ] All required fields validated before processing
- [ ] String length limits enforced
- [ ] Array size limits enforced
- [ ] JSON nesting depth limited to 20 levels
- [ ] File paths validated against traversal attacks
- [ ] URLs validated (http/https scheme only)

### Output

- [ ] Stack traces never included in production responses
- [ ] Absolute paths stripped from responses
- [ ] Secrets never appear in response bodies
- [ ] Error messages are generic (detailed errors logged server-side)

### Headers

- [ ] X-Content-Type-Options: nosniff on all responses
- [ ] X-Frame-Options: DENY on all responses
- [ ] X-Request-ID on all responses
- [ ] HSTS header in production
- [ ] Cache-Control: no-store on all API responses

### Identity

- [ ] Token signature verified on all protected endpoints
- [ ] Token expiry checked on every request
- [ ] Message signatures verified when sender public key is known
- [ ] Governance directive signatures verified against orchestrator key

### Monitoring

- [ ] Security events emitted for all threat classifications
- [ ] Critical security events trigger immediate alerts
- [ ] Failed auth attempts logged with source information
