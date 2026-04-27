<!-- blueprint
type: pattern
name: caching
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, patterns/storage]
platform: any
tier: free
-->

# Caching Pattern

In-process caching for agents that repeatedly access the same data
within or across task executions. Agents `extends: patterns/caching`
to inherit the cache interface and eviction semantics described here.

## Overview

Every Weblisk agent runs as an independent process with its own memory
space. There is no shared cache server — caching is local, embedded,
and zero-dependency. This pattern defines a standard interface so that
agents cache consistently and tools can instrument cache behaviour
uniformly.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: FieldType
          fields_used: [int64, string, boolean]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, capabilities]
        - name: HealthResponse
          fields_used: [status, cache]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: FieldType
          fields_used: [string, int, float, boolean, timestamp, json]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Local and zero-dependency** — Caching is in-process, embedded in each agent. There is no shared cache server, no distributed state, and no serialization overhead.
2. **Namespaced isolation** — Cache keys are always namespaced to prevent collisions between different data types within the same agent.
3. **Cache-aside correctness** — The cache is never the source of truth. Agents always fall back to the primary data source on miss, and explicit invalidation takes priority over TTL.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: cache-interface
      description: Standard Get/Set/Delete/Clear/Stats operations for agent caches
      parameters:
        - name: max_size
          type: int
          required: true
          description: Maximum number of cache entries
        - name: default_ttl
          type: int
          required: true
          description: Default time-to-live in seconds
      inherits: Cache Get, Set, Delete, Clear, Stats operations
      overridable: true
      override_constraints: Must preserve LRU eviction semantics and TTL expiry

    - name: event-invalidation
      description: Cache invalidation on service directory and lifecycle events
      parameters:
        - name: event
          type: string
          required: true
          description: Event type triggering invalidation
      inherits: Namespace-scoped invalidation rules
      overridable: true
      override_constraints: Service directory push must always clear service and route namespaces

  types:
    - name: CacheStats
      description: Hit/miss/eviction counters and memory usage
      inherited_by: Cache Interface section
    - name: CacheEntry
      description: Namespaced key-value with TTL metadata
      inherited_by: Cache Namespaces section

  endpoints:
    - path: /v1/health (cache field)
      description: Cache metrics exposed in agent health response
      inherited_by: Observability section
```

---

**What this pattern is NOT:**

- Not a distributed cache (agents don't share memory)
- Not a CDN or edge cache (that's the gateway's concern)
- Not a response cache (HTTP caching headers are handled by the gateway)

## Cache Interface

Every agent that extends this pattern MUST implement the following
interface:

| Operation | Signature | Description |
|-----------|-----------|-------------|
| Get | `(key string) → (value any, hit bool)` | Retrieve cached value |
| Set | `(key string, value any, ttl Duration) → void` | Store with time-to-live |
| Delete | `(key string) → void` | Explicitly remove entry |
| Clear | `(namespace string) → void` | Remove all entries for a namespace |
| Stats | `() → CacheStats` | Hit/miss/eviction counters |

### CacheStats

| Field | Type | Description |
|-------|------|-------------|
| hits | int64 | Total cache hits since startup |
| misses | int64 | Total cache misses since startup |
| evictions | int64 | Total evictions (TTL + capacity) |
| size | int | Current number of entries |
| max_size | int | Configured maximum entries |
| memory_bytes | int64 | Estimated memory consumption |

## Cache Namespaces

Cache keys MUST be namespaced to prevent collisions between different
data types cached by the same agent.

```
<namespace>:<key>

Examples:
  service:seo-analyzer          # Cached service directory entry
  route:content.*               # Cached routing table lookup
  task:abc123                   # Cached task result
  ai:embed:sha256(input)        # Cached embedding
```

Standard namespaces:

| Namespace | Purpose | Default TTL | Typical Source |
|-----------|---------|-------------|----------------|
| `service` | Service directory entries | 60s | POST /v1/services |
| `route` | Routing table lookups | 60s | Service directory push |
| `ai` | LLM/embedding responses | 300s | POST /ai/* |
| `task` | Completed task results | 120s | POST /v1/execute |
| `config` | Configuration values | 600s | Environment / files |

Agents MAY define custom namespaces for domain-specific data (e.g.,
`html`, `score`, `report`).

## Eviction Policy

All caches use **LRU (Least Recently Used)** eviction with TTL expiry:

1. **TTL expiry** — entries are removed after their time-to-live
   expires. Expired entries are evicted lazily on access or eagerly
   by a background sweep (implementation choice).
2. **Capacity eviction** — when the cache reaches `max_size`, the
   least recently accessed entry is evicted to make room.
3. **Explicit invalidation** — agents MUST clear cached service
   directory entries when they receive a POST /v1/services push.

**Priority order:** TTL expiry > explicit invalidation > LRU eviction.

## Cache-Aside Pattern

Agents use cache-aside (lazy-loading). The cache is not the source
of truth — it sits alongside the primary data source.

```
1. Check cache for key
2. If HIT → return cached value
3. If MISS → fetch from source (file, HTTP, compute)
4. Store result in cache with TTL
5. Return value
```

The agent MUST NOT serve stale data after an explicit invalidation.
When the service directory is updated (POST /v1/services), the agent
MUST clear the `service` and `route` namespaces before processing
the new directory.

## Event-Driven Invalidation

Agents subscribed to events that affect cached data SHOULD invalidate
on receipt:

| Event | Invalidation Action |
|-------|-------------------|
| Service directory push (POST /v1/services) | Clear `service:*` and `route:*` |
| system.agent.registered | Clear `service:<agent_name>` |
| system.agent.deregistered | Clear `service:<agent_name>` |
| Configuration reload | Clear `config:*` |

## AI Response Caching

Agents that use the [api-ai](api-ai.md) pattern SHOULD cache
deterministic responses (temperature = 0) and embeddings:

- **Embeddings** — cache by `sha256(model + input)`, TTL 24h.
  Embeddings are deterministic and expensive to recompute.
- **Extractions** — cache by `sha256(model + input + schema)`, TTL 1h.
  Same input + schema produces same extraction.
- **Chat/completions** — cache ONLY if `temperature = 0`, by
  `sha256(model + messages)`, TTL 5m. Non-deterministic responses
  (temperature > 0) MUST NOT be cached.

## Configuration

```bash
# Maximum entries per agent cache (default: 10000)
WL_CACHE_MAX_SIZE=10000

# Default TTL in seconds when not specified per-entry (default: 300)
WL_CACHE_DEFAULT_TTL=300

# Enable cache stats in health response (default: true)
WL_CACHE_STATS_ENABLED=true

# Background sweep interval in seconds (default: 60)
WL_CACHE_SWEEP_INTERVAL=60
```

## Observability

Agents that extend this pattern SHOULD expose cache metrics in their
health response (POST /v1/health):

```json
{
  "status": "healthy",
  "cache": {
    "hits": 15420,
    "misses": 892,
    "hit_rate": 0.945,
    "evictions": 203,
    "size": 4210,
    "max_size": 10000,
    "memory_bytes": 8421376
  }
}
```

Prometheus-format metrics (if patterns/observability is extended):

```
wl_cache_hits_total{agent="seo-analyzer", namespace="ai"} 8420
wl_cache_misses_total{agent="seo-analyzer", namespace="ai"} 312
wl_cache_evictions_total{agent="seo-analyzer", namespace="service"} 15
wl_cache_size{agent="seo-analyzer"} 4210
wl_cache_memory_bytes{agent="seo-analyzer"} 8421376
```

## Implementation Notes

- **Thread safety** — cache operations MUST be safe for concurrent
  access. Use sync.RWMutex (Go), Map with locks (Node), or platform
  equivalents.
- **Memory limits** — agents SHOULD monitor `memory_bytes` and reduce
  `max_size` if memory pressure is detected. A conservative default
  is 10,000 entries.
- **Serialization** — cached values are stored in-process as native
  objects (no serialization overhead). This is not a distributed cache.
- **Cold start** — caches start empty on agent restart. Agents MUST
  NOT depend on cached data being present. The cache-aside pattern
  ensures correctness on cold start.
- **No persistence** — caches are in-memory only. Persistent data
  belongs in the store (see [patterns/storage](storage.md)).

## Verification Checklist

- [ ] Cache Get/Set/Delete/Clear operations work correctly
- [ ] TTL expiry removes entries after configured duration
- [ ] LRU eviction triggers when max_size is reached
- [ ] Service directory push clears service + route namespaces
- [ ] Cache stats are exposed in POST /v1/health response
- [ ] Concurrent access is safe (no data races)
- [ ] Cache keys are namespaced (no collisions)
- [ ] AI embedding cache uses content-hash keys
- [ ] Non-deterministic AI responses (temperature > 0) are NOT cached
- [ ] Cold start works correctly (empty cache, no errors)
