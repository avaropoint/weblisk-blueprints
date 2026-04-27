<!-- blueprint
type: pattern
name: rate-limiting
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/gateway, architecture/agent]
platform: any
tier: free
-->

# Rate Limiting Pattern

Unified rate limiting for the Weblisk framework. Defines algorithms,
configuration, enforcement points, and response behavior for
controlling request throughput at the gateway and agent levels.

Rate limiting is enforced at two layers:

1. **Gateway** — Protects the system from external abuse. Applied
   before any agent receives the request.
2. **Agent** — Protects individual agents from overload. Applied by
   agents that need finer-grained control beyond gateway limits.

## Overview

The gateway is the primary enforcement point. It applies rate limits
per route, per user, per IP, or per API key before forwarding
requests to agents. Agents MAY apply their own limits for
domain-specific throttling (e.g., external API call budgets).

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category, retryable]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RateLimitConfig
          fields_used: [algorithm, storage, defaults, routes]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [rate_limiting, routes, trusted_proxies]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentConfig
          fields_used: [agent_rate_limits]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Gateway-first enforcement** — rate limits are checked before authentication, catching abuse early with minimal resource cost.
2. **Multiple algorithms** — token bucket, sliding window, and fixed window are available per-route based on precision needs and overhead tolerance.
3. **Layered limits** — the gateway protects the system from external abuse; agents optionally protect themselves with domain-specific throttling for external API budgets.
4. **Observable by default** — every rate limit check emits metrics and response headers, giving both clients and operators full visibility into limit status.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: rate-limit-enforcement
      description: Check request against configured limits and allow or reject with 429
      parameters:
        - name: algorithm
          type: string
          required: true
          description: Rate limiting algorithm — token_bucket, sliding_window, fixed_window
        - name: key_type
          type: string
          required: true
          description: Identification key — ip, user, api_key, route, composite
        - name: requests
          type: int
          required: true
          description: Maximum requests per window
        - name: window
          type: int
          required: true
          description: Time window in seconds
      inherits: Algorithm implementations, identification key extraction, response headers
      overridable: true
      override_constraints: Must return 429 with Retry-After header when limit exceeded

  types:
    - name: RateLimitConfig
      description: Configuration for algorithm, storage, defaults, and per-route overrides
      inherited_by: Configuration section
    - name: RateLimitStatus
      description: Current counter state with remaining tokens and reset timestamp
      inherited_by: Response Behavior section

  endpoints:
    - path: /v1/admin/rate-limits
      description: View and update rate limit configuration (hot-reload)
      inherited_by: Admin Operations section
    - path: /v1/admin/rate-limits/status
      description: Current counters and usage statistics
      inherited_by: Admin Operations section
    - path: /v1/admin/rate-limits/reset
      description: Reset counters for a specific key
      inherited_by: Admin Operations section
```

---

## Algorithms

### Token Bucket (Default)

The default algorithm for gateway rate limiting. Allows bursts up to
the bucket capacity while maintaining a steady refill rate.

```
bucket_capacity = max_burst
refill_rate = requests_per_window / window_seconds
```

| Parameter | Description |
|-----------|-------------|
| capacity | Maximum tokens (burst size) |
| refill_rate | Tokens added per second |
| tokens | Current available tokens |

On each request:
1. Calculate tokens added since last request
2. Add tokens (capped at capacity)
3. If tokens ≥ 1: consume 1 token, allow request
4. If tokens < 1: reject with 429

### Sliding Window

Alternative algorithm for strict per-window limits. Better for APIs
that need exact count guarantees within a time window.

```
window_size = 60 seconds (configurable)
max_requests = limit per window
```

On each request:
1. Count requests in current window
2. Weight previous window's count by overlap percentage
3. If weighted_count + current_count < max_requests: allow
4. Else: reject with 429

### Fixed Window

Simplest algorithm. Resets counter at fixed intervals. Susceptible to
burst at window boundaries but lowest overhead.

```
window_size = 60 seconds (configurable)
max_requests = limit per window
```

On each request:
1. Get current window key (timestamp / window_size)
2. Increment counter for window
3. If counter ≤ max_requests: allow
4. Else: reject with 429

---

## Configuration

### Gateway Rate Limit Configuration

```yaml
rate_limiting:
  enabled: true
  algorithm: token_bucket    # token_bucket | sliding_window | fixed_window
  storage: memory            # memory | agent_store

  # Default limits (applied to all routes unless overridden)
  defaults:
    per_ip:
      requests: 100
      window: 60              # seconds
      burst: 20               # token_bucket only
    per_user:
      requests: 200
      window: 60
      burst: 40
    per_api_key:
      requests: 1000
      window: 60
      burst: 100

  # Per-route overrides
  routes:
    - match: /v1/auth/login
      per_ip:
        requests: 5
        window: 300            # 5 requests per 5 minutes
        burst: 5
    - match: /v1/auth/register
      per_ip:
        requests: 3
        window: 3600           # 3 per hour
        burst: 3
    - match: /v1/auth/password-reset
      per_ip:
        requests: 3
        window: 3600
        burst: 3
    - match: /v1/files/upload
      per_user:
        requests: 10
        window: 60
        burst: 5
    - match: /v1/ai/*
      per_user:
        requests: 30
        window: 60
        burst: 10
    - match: /v1/webhooks/inbound/*
      per_ip:
        requests: 50
        window: 60
        burst: 20
```

### Agent-Level Rate Limiting

Agents that call external services SHOULD implement their own rate
limits to respect upstream API quotas:

```yaml
# Example: AI agent external API budget
agent_rate_limits:
  openai_api:
    requests: 60
    window: 60
    burst: 10
  ollama_local:
    requests: 0              # 0 = unlimited
```

Agent rate limits are configured in the agent's own configuration,
not in the gateway. The gateway does not manage agent-to-external
rate limits.

---

## Enforcement

### Gateway Enforcement Flow

Rate limit checking occurs at step 3 of the gateway's 9-step request
lifecycle (see gateway.md), after TLS termination and before
authentication:

```
1. TLS termination
2. Request parsing
3. Rate limit check ← HERE
4. Session/token validation
5. ABAC policy evaluation
6. Route resolution
7. Request forwarding
8. Response processing
9. Response delivery
```

Checking before authentication means:
- Unauthenticated abuse is caught early (no wasted auth lookups)
- Per-IP limits apply to all requests
- Per-user and per-API-key limits apply after auth (step 4 re-checks)

### Identification Keys

| Key Type | Source | Use Case |
|----------|--------|----------|
| IP address | `X-Forwarded-For` (trusted proxy) or connection IP | Anonymous/unauthenticated requests |
| User ID | `X-Gateway-User` header (post-auth) | Authenticated user limits |
| API key | `Authorization: Bearer` or `X-API-Key` header | Service-to-service limits |
| Route | Request path matched against route patterns | Per-endpoint limits |
| Composite | IP + route, user + route | Fine-grained per-route limits |

### Priority Order

When multiple limits apply to a request, ALL are checked. The most
restrictive limit wins:

1. Per-route per-IP (if configured)
2. Per-route per-user (if authenticated)
3. Global per-IP
4. Global per-user (if authenticated)
5. Global per-API-key (if applicable)

If ANY limit is exceeded, the request is rejected.

---

## Response Behavior

### 429 Too Many Requests

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "category": "transient",
    "retryable": true,
    "details": {
      "limit": 100,
      "window": 60,
      "retry_after": 12
    }
  }
}
```

### Response Headers

Every response includes rate limit headers (successful or rejected):

| Header | Value | Description |
|--------|-------|-------------|
| `X-RateLimit-Limit` | 100 | Maximum requests in window |
| `X-RateLimit-Remaining` | 42 | Requests remaining in window |
| `X-RateLimit-Reset` | 1714060800 | Unix timestamp when window resets |
| `Retry-After` | 12 | Seconds until retry (429 only) |

### Retry Guidance

The `Retry-After` header tells clients exactly when to retry. Clients
SHOULD implement exponential backoff with jitter when receiving 429s.
See the retry pattern for client-side retry behavior.

---

## Storage

### In-Memory (Default)

Rate limit counters are stored in-memory on the gateway process.
Suitable for single-instance deployments.

- Fastest option (no I/O)
- Counters lost on restart (acceptable — limits reset)
- Not shared across gateway instances

### Agent Store

For multi-instance gateway deployments, rate limit counters can be
stored in the gateway agent's storage (see storage.md). This provides
shared state across instances at the cost of a storage lookup per
request.

- Shared across gateway instances
- Survives gateway restarts
- Adds ~1ms latency per request

---

## Admin Operations

Rate limits are manageable via the admin gateway:

| Endpoint | Method | Description |
|----------|--------|-------------|
| /v1/admin/rate-limits | GET | Current rate limit configuration |
| /v1/admin/rate-limits | PUT | Update rate limit configuration (hot-reload) |
| /v1/admin/rate-limits/status | GET | Current counters and usage stats |
| /v1/admin/rate-limits/reset | POST | Reset counters for a specific key |

Configuration changes via the admin API take effect immediately
without gateway restart.

---

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| gateway_ratelimit_total | counter | Requests checked, by result (allowed/rejected) |
| gateway_ratelimit_rejected_total | counter | Rejected requests by route, key_type |
| gateway_ratelimit_remaining | gauge | Remaining tokens/requests by route |
| gateway_ratelimit_check_duration_seconds | histogram | Time spent checking rate limits |

---

## Implementation Notes

- The gateway is the primary enforcement point. Agent-level rate
  limiting is optional and handles domain-specific concerns (external
  API budgets, resource-intensive operations).
- Rate limit configuration supports hot-reload via admin API or CLI.
  No gateway restart required.
- For development environments, rate limiting can be disabled entirely
  (`rate_limiting.enabled: false`).
- Trusted proxy configuration is required for correct IP extraction
  from `X-Forwarded-For`. Without it, the gateway uses the connection
  IP, which may be the proxy's address.
- Rate limit counters are lightweight. Even at 100K concurrent keys,
  in-memory storage uses <10MB.
- The framework provides the rate limiting mechanism. The specific
  limits (requests per window, burst sizes) are application-configured.

## Verification Checklist

- [ ] Gateway rejects requests exceeding per-IP limits with 429
- [ ] Gateway rejects requests exceeding per-user limits with 429
- [ ] Gateway rejects requests exceeding per-route limits with 429
- [ ] `X-RateLimit-*` headers present on all responses
- [ ] `Retry-After` header present on 429 responses
- [ ] Token bucket allows burst up to capacity
- [ ] Sliding window correctly weights previous window
- [ ] Per-route overrides take precedence over defaults
- [ ] Rate limit configuration hot-reloads without restart
- [ ] Admin API returns current counters and configuration
- [ ] Metrics emit for allowed and rejected requests
- [ ] Auth endpoints have stricter limits than general routes
