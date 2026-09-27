# Hub Configuration Schema

The `.weblisk/config.yaml` file defines the runtime topology of a Weblisk hub.
It declares which components exist, their ports, and their relationships. The
CLI reads this file to start, stop, and manage all hub components.

## Location

```
<project-root>/.weblisk/config.yaml
```

## Schema Definition

```yaml
# Required — hub identity
hub:
  name: string                     # Hub name (lowercase, alphanumeric + hyphens)
  version: string                  # Semver version of this hub configuration

# Required — orchestrator configuration
orchestrator:
  port: integer                    # Listen port (default: 9800)
  storage: enum                    # "memory" | "sqlite" | "postgres"
  storage_path: string             # Path for sqlite (default: .weblisk/data/orchestrator.db)
  token_ttl: duration              # WLT token lifetime (default: 24h)
  health_interval: duration        # Health probe interval (default: 30s)
  health_timeout: duration         # Health probe timeout (default: 5s)
  health_failures: integer         # Failures before deregistration (default: 3)

# Required — gateway configuration
gateway:
  port: integer                    # Listen port (default: 8080)
  tls: boolean                     # Enable TLS (default: true)
  tls_cert: string                 # Path to TLS certificate (if tls: true)
  tls_key: string                  # Path to TLS private key (if tls: true)
  static_dir: string               # Directory for static files (default: public)
  auth: enum                       # "none" | "session" | "token" | "both"
  rate_limit: string               # Rate limit expression (e.g., "100/min")
  cors_origins: list[string]       # Allowed CORS origins (default: [])

# Required — domain declarations
domains:
  - name: string                   # Domain name (matches domain blueprint)
    port: integer                  # Listen port (9700–9709 range)
    replicas: integer              # Instance count (default: 1)

# Required — agent declarations
agents:
  - name: string                   # Agent name (matches agent blueprint)
    type: enum                     # "work" | "infrastructure"
    domain: string                 # Parent domain (required for work agents)
    port: integer                  # Listen port (9710–9749 for work, 9750–9799 for infra)
    replicas: integer              # Instance count (default: 1)
    env: map[string, string]       # Additional environment variables

# Optional — the content service and its repositories
content:
  port: integer                    # Listen port (default: 9802)
  backends:                        # Stores this hub can reach. A placement names one
    - name: string                 # Backend name (lowercase, alphanumeric + hyphens)
                                   # Driver, root and credentials belong to the
                                   # platform blueprint that implements it
  repositories:                    # Stores brought under governance at startup
    - id: string                   # Stable repository id, unique within scope_path
      scope_path: string           # <tenant>/<org>[/<project>]
      placement:
        backend: string            # One of content.backends[].name
        locator: string            # Path relative to that backend's root
      custody: enum                # "exclusive" | "shared" | "opaque"
      attestations:
        enumerable_principals: boolean
        attributable_writes: boolean
        tamper_evident: boolean
  reconcile_interval: duration     # Shared custody only. 0 disables scheduled runs
  reverify_custody_interval: duration
  max_entry_bytes: integer         # Largest entry the service will write

# Optional — federation configuration
federation:
  enabled: boolean                 # Enable federation (default: false)
  port: integer                    # Federation listen port (default: 9801)
  peers: list[string]              # Peer hub URLs to connect on startup

# Optional — observability
observability:
  log_level: enum                  # "debug" | "info" | "warn" | "error" (default: info)
  log_format: enum                 # "json" | "text" (default: json)
  trace_enabled: boolean           # Enable distributed tracing (default: false)
  trace_sample_rate: float         # Sampling rate 0.0–1.0 (default: 1.0)
  metrics_enabled: boolean         # Expose /metrics endpoint (default: true)
  otlp_endpoint: string            # OTLP collector URL (optional)
```

## Field Details

### hub

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Unique hub identifier. Used in federation identity and audit logs. |
| `version` | string | yes | — | Semver version. Tracks configuration changes. |

### orchestrator

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `port` | integer | no | `9800` | HTTP listen port |
| `storage` | enum | no | `memory` | Backing store for registry, audit log, event history |
| `storage_path` | string | no | `.weblisk/data/orchestrator.db` | File path when storage is `sqlite` |
| `token_ttl` | duration | no | `24h` | WLT token lifetime. Agents must re-register before expiry. |
| `health_interval` | duration | no | `30s` | How often to probe registered agents |
| `health_timeout` | duration | no | `5s` | Max wait for health response |
| `health_failures` | integer | no | `3` | Consecutive failures before auto-deregistration |

### gateway

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `port` | integer | no | `8080` | HTTP listen port |
| `tls` | boolean | no | `true` | Enable HTTPS. Set `false` for local development. |
| `tls_cert` | string | cond | — | Required when `tls: true` |
| `tls_key` | string | cond | — | Required when `tls: true` |
| `static_dir` | string | no | `public` | Directory served at `/` for static HTML/CSS/JS |
| `auth` | enum | no | `session` | Authentication mode |
| `rate_limit` | string | no | `100/min` | Global rate limit (format: `<count>/<window>`) |
| `cors_origins` | list | no | `[]` | CORS allowed origins. Empty = same-origin only. |

### domains[]

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Must match a domain blueprint name |
| `port` | integer | no | auto | Listen port (auto-assigned from 9700–9709) |
| `replicas` | integer | no | `1` | Number of instances to start |

### agents[]

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Must match an agent blueprint name |
| `type` | enum | yes | — | `"work"` or `"infrastructure"` |
| `domain` | string | cond | — | Required for work agents. References a domain name. |
| `port` | integer | no | auto | Listen port (auto-assigned from range by type) |
| `replicas` | integer | no | `1` | Number of instances to start |
| `env` | map | no | `{}` | Extra env vars passed to the agent process |

### content

`content` is optional: a hub that governs no authored text declares none of it.
Its presence is what declares the content service as one of this hub's
components; an absent or null `content` declares none. Where it is present, the keys and types are as below — but what a value
**means** is [`architecture/content`](../architecture/content.md), which is the
authority and is not restated here. In particular, that a configured repository
is processed as `establish`, that `establish` creates the store, what the
backend owes once it exists, and what is refused, all live there.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `port` | integer | no | `9802` | Listen port of the content service |
| `backends` | list | cond | `[]` | Stores this hub can reach. Required when `repositories` is non-empty |
| `repositories` | list | no | `[]` | Stores declared at startup |
| `reconcile_interval` | duration | no | `15m` | Out-of-band change detection for shared-custody repositories. `0` disables |
| `reverify_custody_interval` | duration | no | `24h` | How often attestations are re-demonstrated |
| `max_entry_bytes` | integer | no | `10485760` | Largest entry the service will write |

#### content.backends[]

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | What a placement names. Unique within the hub. Its driver, root and credentials are the platform blueprint's, not this file's |

#### content.repositories[]

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | yes | — | Stable repository id. Unique within `scope_path`. Survives rename and re-placement |
| `scope_path` | string | yes | — | `<tenant>/<org>[/<project>]`. Also the resource scope the declaration is authorised on |
| `placement` | object | yes | — | Which backend, and where within it |
| `custody` | enum | no | `opaque` | `"exclusive"`, `"shared"` or `"opaque"`. A **claim**, demonstrated before it takes effect |
| `attestations` | object | no | all `false` | Claims about what the backend can demonstrate. An undemonstrated claim resolves to `false` |

#### content.repositories[].placement

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `backend` | string | yes | — | Must match a `content.backends[].name` declared in this file |
| `locator` | string | yes | — | Path **relative** to that backend's root. Absolute paths, URLs and `..` segments are refused |

**A repository is never given a location, only a backend and a locator inside
it.** The root is named once, in `backends`, where an operator sets it
deliberately; a repository entry names that backend. A file that could give a
locator without a backend would be a file that writes anywhere, read at boot,
with no caller and no capability to check against.

**Neither `ceiling` nor `verified_at` is configurable.** Both are derived from
what the service demonstrates at startup, and a configured ceiling would be a
protection level nobody verified.

### federation

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | no | `false` | Whether this hub participates in federation |
| `port` | integer | no | `9801` | Federation protocol listen port |
| `peers` | list | no | `[]` | Peer hub URLs to initiate connection with on startup |

### observability

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `log_level` | enum | no | `info` | Minimum log level |
| `log_format` | enum | no | `json` | Output format. Use `text` for local development. |
| `trace_enabled` | boolean | no | `false` | Enable span emission and X-Trace-Id propagation |
| `trace_sample_rate` | float | no | `1.0` | Fraction of requests to trace |
| `metrics_enabled` | boolean | no | `true` | Expose structured metrics at `/metrics` on each component |
| `trace_export_endpoint` | string | no | — | Send traces/metrics to an external collector |

## Port Conventions

| Range | Assignment |
|-------|-----------|
| 8080 | Gateway |
| 9800 | Orchestrator |
| 9801 | Federation |
| 9802 | Content service |
| 9700–9709 | Domain controllers |
| 9710–9749 | Work agents |
| 9750–9799 | Infrastructure agents |

When `port` is omitted, the CLI auto-assigns from the appropriate range,
incrementing from the base for each additional component of that type.

## Duration Format

Duration fields accept Go-style duration strings: `30s`, `5m`, `24h`, `1h30m`.

## Minimal Example

```yaml
hub:
  name: starter
  version: 1.0.0

orchestrator:
  port: 9800
  storage: memory

gateway:
  port: 8080
  tls: false
  static_dir: public
  auth: none
  rate_limit: 100/min

domains:
  - name: greeting
    port: 9700

agents:
  - name: greeter
    type: work
    domain: greeting
    port: 9710
```

## Production Example

```yaml
hub:
  name: acme-platform
  version: 2.1.0

orchestrator:
  port: 9800
  storage: sqlite
  storage_path: /var/lib/weblisk/orchestrator.db
  token_ttl: 12h
  health_interval: 15s

gateway:
  port: 8080
  tls: true
  tls_cert: /etc/weblisk/tls/cert.pem
  tls_key: /etc/weblisk/tls/key.pem
  static_dir: /var/www/weblisk/public
  auth: session
  rate_limit: 1000/min
  cors_origins:
    - https://app.acme.com
    - https://admin.acme.com

domains:
  - name: inventory
    port: 9700
    replicas: 2
  - name: analytics
    port: 9701

agents:
  - name: stock-checker
    type: work
    domain: inventory
    port: 9710
    replicas: 3
    env:
      ai_provider: openai
      ai_model: gpt-4o
  - name: forecaster
    type: work
    domain: analytics
    port: 9711
  - name: health-monitor
    type: infrastructure
    port: 9750

content:
  backends:
    - name: governed
  repositories:
    - id: policies
      scope_path: acme/corporate
      placement:
        backend: governed
        locator: corporate/policies
      custody: exclusive
    - id: evidence
      scope_path: acme/corporate
      placement:
        backend: governed
        locator: corporate/evidence
      custody: shared
      attestations:
        enumerable_principals: true
        attributable_writes: true
        tamper_evident: false
  reconcile_interval: 15m

federation:
  enabled: true
  port: 9801
  peers:
    - https://partner-hub.example.com:9801

observability:
  log_level: info
  log_format: json
  trace_enabled: true
  trace_sample_rate: 0.1
  metrics_enabled: true
  otlp_endpoint: http://otel-collector:4317
```

## Validation Rules

1. `hub.name` must be lowercase alphanumeric with hyphens, 1–63 characters
2. `hub.version` must be valid semver
3. All declared ports must be unique across the configuration
4. Work agents must reference a domain that exists in the `domains` list
5. Domain names must be unique
6. Agent names must be unique
7. Port values must be in valid range (1024–65535)
8. When `tls: true`, both `tls_cert` and `tls_key` must be specified
9. `rate_limit` format: `<positive-integer>/<window>` where window is `sec`, `min`, or `hour`
10. `trace_sample_rate` must be between 0.0 and 1.0 inclusive
11. `content.backends[].name` must be unique within the hub
12. Every `content.repositories[].placement.backend` must match a declared `content.backends[].name`
13. `content.repositories[].placement.locator` must be relative — no leading separator, no scheme, no authority, no `..` segment
14. `content.repositories[].id` must be unique within its `scope_path`
15. No two `content.repositories[]` may name placements where one equals, contains or sits inside another
