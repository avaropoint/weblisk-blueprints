<!-- blueprint
type: pattern
name: development
version: 1.0.0
requires: [protocol/types, patterns/security, patterns/observability]
platform: any
tier: free
-->

# Development Server Pattern

Platform-agnostic specification for local development servers that
mirror production routing, security headers, and API behavior. Each
project extends this specification to build a native development
server in its target language and framework.

## Overview

The development server is a critical piece of the Weblisk developer
experience. It provides a local HTTP server that mirrors production
behavior — routing, security headers, blueprint serving, and live
reload — without requiring production infrastructure or platform-
specific tooling.

This specification defines **what** a development server must do.
Platform guides (Go, Node, Rust, Cloudflare) define **how** to
implement it in each environment. Projects generate a platform-
specific configuration file (e.g., `dev-server.yaml`) from this
specification for their chosen stack.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/security
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: SecurityEvent
          fields_used: [event_type, level, event]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/observability
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: HealthResponse
          fields_used: [name, status, mode]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Dev/prod parity** — The development server reproduces production
   routing rules, security headers, and API contracts. Code that works
   in dev works in production without surprises.
2. **Platform-native implementation** — Each language/framework builds
   its own development server using native HTTP libraries. No cross-
   platform runtime or shim layer is required.
3. **Zero external dependencies** — The development server uses only
   standard library capabilities and the project's chosen HTTP
   framework. No additional tooling (e.g., wrangler, docker) required
   for basic development.
4. **Instant feedback** — File changes are detected and pushed to the
   browser via live reload. Sub-second feedback loops for HTML, CSS,
   and JavaScript changes.
5. **Secure by default** — Even in development, the server applies
   security headers, blocks dotfile access, and prevents path
   traversal. Developers see the same security behavior they'll get
   in production.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: static-serving
      description: Serve static files from the public directory with security headers matching production
      parameters:
        - name: public_dir
          type: string
          required: true
          description: Directory containing static assets to serve
      inherits: File serving with security header injection
      overridable: true
      override_constraints: Cannot disable security headers or dotfile blocking
    - name: blueprint-api
      description: Serve blueprint YAML files via HTTP API for runtime consumption
      parameters:
        - name: blueprint_dir
          type: string
          required: true
          description: Directory containing blueprint YAML files
      inherits: Blueprint serving with path validation
      overridable: true
      override_constraints: Path validation cannot be weakened
    - name: live-reload
      description: Push file change notifications to connected browsers via SSE
      parameters:
        - name: watch_extensions
          type: "list<string>"
          required: true
          description: File extensions to watch for changes
      inherits: File watching and SSE notification
      overridable: true
      override_constraints: Must use SSE (not polling)
  types:
    - name: DevServerConfig
      description: Development server configuration with routes, security, and watch settings
      inherited_by: Configuration section
    - name: RouteDefinition
      description: Route matching rule with path, methods, and behavior
      inherited_by: Routes section
  endpoints:
    - path: /*
      description: Static file serving from public directory
      inherited_by: Routes section
    - path: /api/blueprint/{path}
      description: Blueprint YAML file serving
      inherited_by: Routes section
    - path: /api/health
      description: Health check endpoint
      inherited_by: Routes section
    - path: /__livereload
      description: Server-Sent Events stream for live reload
      inherited_by: Routes section
  events:
    - topic: dev.file_changed
      description: Emitted when a watched file is modified
      payload: {path, extension, timestamp}
    - topic: dev.server_started
      description: Emitted when the development server starts
      payload: {port, public_dir, blueprint_dir, timestamp}
```

---

## Routes

### Static File Serving

| Property | Value |
|----------|-------|
| Path | `/*` |
| Methods | `GET`, `HEAD` |
| Source | `{public_dir}/` (configurable, default: `public`) |

**Behavior:**

1. Resolve the request path relative to the public directory
2. Inject live-reload script into HTML responses before `</body>`
3. Set security headers matching production CSP (see Security Headers)
4. Block dotfile access — any path segment starting with `.` returns 404
5. Block path traversal — any path containing `..` returns 404
6. Set `Cache-Control: no-cache` for all responses
7. Return 404 (not 403) for blocked paths — never confirm existence

### Blueprint API

| Property | Value |
|----------|-------|
| Path | `/api/blueprint/{path}` |
| Methods | `GET`, `HEAD` |
| Content-Type | `text/yaml; charset=utf-8` |

**Behavior:**

1. Validate `{path}` starts with an allowed prefix (configurable)
2. Validate `{path}` ends with `.yaml` or `.yml`
3. Reject paths containing `..` or `//` — return 400 with ErrorResponse
4. Resolve path relative to `{blueprint_dir}/`
5. Return file contents with `text/yaml; charset=utf-8`
6. Return 400 for invalid paths, 404 for missing files

**Default allowed prefixes:**

```yaml
allowed_prefixes:
  - pages/
  - components/
```

### Health Check

| Property | Value |
|----------|-------|
| Path | `/api/health` |
| Methods | `GET` |
| Content-Type | `application/json` |

**Response:**

```json
{
  "name": "weblisk-dev",
  "status": "healthy",
  "mode": "development"
}
```

### Live Reload

| Property | Value |
|----------|-------|
| Path | `/__livereload` |
| Methods | `GET` |
| Protocol | Server-Sent Events (SSE) |

**Behavior:**

1. Open an SSE stream (`Content-Type: text/event-stream`)
2. Watch configured directories for file changes
3. When a watched file changes, send `data: reload\n\n` to all connected clients
4. Maintain keep-alive with periodic `:ping\n\n` comments (every 30 seconds)

**Default watch configuration:**

```yaml
watch:
  directories:
    - "{public_dir}/"
    - "{blueprint_dir}/"
    - ".weblisk/"
  extensions:
    - .html
    - .css
    - .js
    - .mjs
    - .yaml
    - .yml
    - .json
    - .svg
```

---

## Security Headers

All responses from the development server MUST include security
headers that match the production gateway configuration. This ensures
developers encounter CSP violations and other security issues during
development, not after deployment.

### All Responses

| Header | Value |
|--------|-------|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()` |
| `X-DNS-Prefetch-Control` | `off` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |

### HTML Responses Only

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | See CSP policy below |

**Default CSP:**

```
default-src 'self';
script-src 'self' 'unsafe-inline' https:;
style-src 'self' 'unsafe-inline';
img-src 'self' data: blob:;
connect-src 'self' https: ws: wss:;
worker-src 'self' blob:;
manifest-src 'self';
frame-ancestors 'none';
base-uri 'self';
form-action 'self'
```

> **Note:** `'unsafe-inline'` for scripts is permitted in development
> to support the injected live-reload script. Production CSP SHOULD
> remove `'unsafe-inline'` and use nonces or hashes instead.

---

## Configuration

The development server is configured via environment variables and
CLI arguments. Implementations MAY also support a project-level
configuration file.

### Configuration Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `port` | int | `3000` | HTTP listen port |
| `host` | string | `127.0.0.1` | Listen address (localhost only in dev) |
| `public_dir` | string | `public` | Directory containing static assets |
| `blueprint_dir` | string | `blueprints` | Directory containing blueprint YAML files |
| `watch_interval` | duration | `500ms` | File system polling interval (if not using native FS events) |

### Configuration Precedence

```
1. CLI arguments (highest priority)
2. Environment variables
3. Project config file (if supported)
4. Defaults (lowest priority)
```

### CLI Interface

The development server is launched via the Weblisk CLI:

```
weblisk dev [root] [--port PORT] [--host HOST]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `root` | positional | `.` | Project root directory |
| `--port` | int | `3000` | Override listen port |
| `--host` | string | `127.0.0.1` | Override listen address |

---

## Blueprint Path Validation

The blueprint API enforces strict path validation to prevent
directory traversal and unauthorized file access:

### Validation Rules

| Rule | Check | Response |
|------|-------|----------|
| Allowed prefix | Path starts with a configured prefix | 400 if not |
| Allowed extension | Path ends with `.yaml` or `.yml` | 400 if not |
| No traversal | Path does not contain `..` | 400 if present |
| No double slash | Path does not contain `//` | 400 if present |
| No absolute path | Path does not start with `/` | 400 if present |
| File exists | Resolved file exists on disk | 404 if not |

---

## Platform Extension

Each platform guide defines how to implement this specification
using native tools. The implementation MUST conform to all contracts
above while using idiomatic language and framework patterns.

### What Platform Guides Define

| Concern | Platform Responsibility |
|---------|----------------------|
| HTTP server | Native HTTP library or framework (e.g., `net/http`, Fastify, Actix) |
| File watching | Native FS events (e.g., `fsnotify`, `chokidar`, `notify`) or polling |
| SSE implementation | Native SSE or manual chunked transfer encoding |
| Static file serving | Native static file middleware or manual implementation |
| HTML injection | Response stream interception for live-reload script |
| Configuration loading | Language-appropriate config parsing (YAML, TOML, env) |

### Project-Level Configuration File

Projects MAY generate a `dev-server.yaml` from this specification
tailored to their platform and project structure:

```yaml
# Example: Generated dev-server.yaml for a Node.js project
extends: patterns/development
platform: node

server:
  port: 3000
  host: 127.0.0.1

directories:
  public: public
  blueprints: blueprints

blueprint_api:
  allowed_prefixes:
    - pages/
    - components/
    - layouts/          # project-specific addition

watch:
  extensions:
    - .html
    - .css
    - .js
    - .mjs
    - .ts              # project-specific addition
    - .yaml
    - .yml
    - .json
    - .svg
```

---

## Error Handling

### Error Responses

All error responses from the development server follow the standard
ErrorResponse format:

```json
{
  "code": "INVALID_PATH",
  "message": "Blueprint path must start with an allowed prefix",
  "detail": "Path 'secrets/db.yaml' does not match allowed prefixes: pages/, components/"
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `INVALID_PATH` | 400 | Blueprint path fails validation rules |
| `NOT_FOUND` | 404 | Requested file does not exist |
| `SERVER_ERROR` | 500 | Unexpected server error (logged, not detailed to client) |

> **Development mode exception:** In development, `SERVER_ERROR`
> responses MAY include stack traces and detailed error information
> to aid debugging. This MUST be stripped in production (per
> `patterns/security` output sanitization rules).

---

## Observability

The development server emits structured log entries for all requests:

```json
{
  "ts": 1713264000,
  "level": "info",
  "component": "dev-server",
  "msg": "request",
  "method": "GET",
  "path": "/index.html",
  "status": 200,
  "duration_ms": 3
}
```

Security-relevant events (dotfile access attempts, path traversal
attempts) are logged at `warn` level with the standard security
event format from `patterns/security`.

---

## Verification Checklist

Implementation MUST:
- [ ] Serve static files from the configured public directory
- [ ] Inject live-reload `<script>` tag into HTML responses before `</body>`
- [ ] Set all required security headers on every response (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, X-DNS-Prefetch-Control, COOP, CORP)
- [ ] Set CSP header on HTML responses only
- [ ] Block dotfile access — paths containing `/.` return 404 (not 403)
- [ ] Block path traversal — paths containing `..` return 404
- [ ] Serve blueprint YAML files via `/api/blueprint/{path}` with path validation
- [ ] Validate blueprint paths against allowed prefixes and extensions
- [ ] Return 400 (not 404) for invalid blueprint paths with ErrorResponse body
- [ ] Provide health check at `/api/health` returning JSON with status and mode
- [ ] Implement SSE-based live reload at `/__livereload`
- [ ] Watch configured directories and extensions for file changes
- [ ] Send `data: reload\n\n` SSE event on file change
- [ ] Support configurable port via environment or CLI flag
- [ ] Support `--port` CLI flag that overrides environment variable
- [ ] Listen on localhost only by default (not `0.0.0.0`)
- [ ] Set `Cache-Control: no-cache` on all responses
- [ ] Log all requests with structured JSON logging
- [ ] Log security events (dotfile, traversal) at warn level
- [ ] Use native language/framework HTTP server (no cross-platform shims)
- [ ] Work without any external tooling (no Docker, no platform CLI)
