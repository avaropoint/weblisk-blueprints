<!-- blueprint
type: pattern
name: deployment
version: 1.0.0
requires: [protocol/types, architecture/orchestrator]
platform: any
tier: free
-->

# Deployment Blueprint

CI/CD pipeline patterns, containerization, environment promotion,
secrets management, and deployment strategies for Weblisk
applications. Covers the path from local development to production
with repeatable, automated deployments.

## Overview

A Weblisk deployment includes multiple components — orchestrator,
domain controllers, and agents — that must be built, configured,
and deployed together. This pattern defines how to containerize the
stack, manage configuration across environments, handle secrets
safely, and automate the build-test-deploy pipeline.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: OrchestratorConfig
          fields_used: [port, env, log_level, storage_dsn]
        - name: HealthStatus
          fields_used: [status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Build once, deploy anywhere** — Container images are immutable.
   Environment-specific configuration is injected at runtime.
2. **Secrets never in code** — All secrets are loaded from environment
   variables or a secrets manager. Never committed to version control.
3. **Progressive delivery** — Changes flow from dev → staging →
   production with validation gates at each step.
4. **Rollback-ready** — Every deployment can be rolled back to the
   previous version within seconds.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: containerization
      description: Multi-stage Docker build with minimal runtime image
      parameters:
        - name: base_image
          type: string
          required: true
          description: Runtime base image (alpine for minimal attack surface)
        - name: user
          type: string
          required: true
          description: Non-root user for container (weblisk, UID 1000)
      inherits: Dockerfile template, image tagging convention, compose setup
      overridable: true
      override_constraints: Must use non-root user and multi-stage build

    - name: deployment-strategy
      description: Rolling update, blue-green, or canary deployment with health checks
      parameters:
        - name: strategy
          type: string
          required: true
          description: Deployment strategy (rolling, blue-green, canary)
        - name: error_rate_threshold
          type: float
          required: false
          description: Error rate threshold for automatic rollback
      inherits: Health check integration, rollback automation
      overridable: true
      override_constraints: Must include health check verification before routing traffic

    - name: environment-management
      description: Configuration resolution across environment tiers
      parameters:
        - name: tier
          type: string
          required: true
          description: Environment tier (local, dev, staging, production)
      inherits: Config hierarchy, secrets management, environment variable conventions
      overridable: true
      override_constraints: Secrets must never appear in source code, images, or build logs

  types:
    - name: EnvironmentConfig
      description: Configuration resolution order and environment variable conventions
      inherited_by: Environment Management section
    - name: DeploymentStrategy
      description: Rolling, blue-green, or canary deployment specification
      inherited_by: Deployment Strategies section

  endpoints:
    - path: /health
      description: Deployment health check for startup, readiness, and liveness
      inherited_by: Health Checks section
```

---

## Containerization

### Dockerfile (Multi-stage)

```dockerfile
# Build stage
FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o weblisk-server ./cmd/server

# Runtime stage
FROM alpine:3.19
RUN apk --no-cache add ca-certificates
RUN adduser -D -u 1000 weblisk
USER weblisk
WORKDIR /app
COPY --from=build /app/weblisk-server .
COPY --from=build /app/agents/ ./agents/
EXPOSE 9800
ENTRYPOINT ["./weblisk-server"]
```

### Image Conventions

- Base image: `alpine` for minimal attack surface
- Non-root user: `weblisk` (UID 1000)
- Single binary + agent definitions (no build tools in runtime image)
- Tag format: `weblisk/server:<semver>-<git-sha-short>`
  - Example: `weblisk/server:1.2.0-abc1234`
- Latest tag points to the most recent stable release

### Docker Compose (Development)

```yaml
version: "3.9"
services:
  orchestrator:
    build: .
    ports:
      - "9800:9800"
    environment:
      - WL_ENV=development
      - WL_LOG_FORMAT=text
      - WL_LOG_LEVEL=debug
    volumes:
      - ./data:/app/data
      - ./agents:/app/agents

  # Individual agents can be added for isolated development:
  # seo-analyzer:
  #   build:
  #     context: .
  #     dockerfile: agents/seo-analyzer/Dockerfile
  #   ports:
  #     - "9710:9710"
```

---

## Environment Management

### Environment Tiers

| Environment | Purpose | Data | Access |
|-------------|---------|------|--------|
| local | Developer machines | Synthetic/seed data | Developer |
| dev | Shared development | Synthetic data | Team |
| staging | Pre-production validation | Sanitized prod copy | Team |
| production | Live traffic | Real data | Ops team |

### Configuration Hierarchy

Configuration is resolved in order (later overrides earlier):

```
1. Built-in defaults (compiled into binary)
2. Config file: weblisk.yaml (committed, non-secret)
3. Environment-specific file: weblisk.staging.yaml (committed)
4. Environment variables: WL_* (injected at runtime)
5. Secrets manager (runtime fetch)
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `WL_ENV` | Environment tier | `production` |
| `WL_PORT` | Orchestrator port | `9800` |
| `WL_LOG_LEVEL` | Log level | `info` |
| `WL_LOG_FORMAT` | Log format | `json` |
| `WL_STORAGE_DSN` | Database connection string | `sqlite:///app/data/wl.db` |
| `WL_IDENTITY_KEY` | Server Ed25519 private key (base64) | `...` |

### Secrets

Secrets MUST NOT appear in:
- Source code or config files
- Docker images or build logs
- CI/CD pipeline definitions (use secret variables)

Secrets SHOULD be provided via:
- **Environment variables** — injected by the deployment platform
- **Secrets manager** — AWS Secrets Manager, Vault, Doppler
- **Mounted files** — Kubernetes secrets mounted as volumes

| Secret | Variable | Description |
|--------|----------|-------------|
| Server identity key | `WL_IDENTITY_KEY` | Ed25519 private key |
| OAuth client secrets | `WL_OAUTH_*_CLIENT_SECRET` | Per-provider |
| Webhook secrets | `WL_ALERT_WEBHOOK_SECRET` | HMAC signing key |
| Database credentials | `WL_STORAGE_DSN` | Connection string with creds |

---

## CI/CD Pipeline

### Pipeline Stages

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Lint &   │ →  │  Build   │ →  │  Test    │ →  │  Deploy  │
│  Check    │    │  Image   │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### Stage 1: Lint & Check

```yaml
lint:
  - go vet ./...
  - golangci-lint run
  - weblisk validate            # validate blueprint schemas
```

### Stage 2: Build Image

```yaml
build:
  - docker build -t weblisk/server:$TAG .
  - docker push weblisk/server:$TAG
```

### Stage 3: Test

```yaml
test:
  unit:
    - go test ./... -race -cover
  integration:
    - docker compose -f docker-compose.test.yaml up -d
    - go test ./tests/integration/... -tags=integration
    - docker compose -f docker-compose.test.yaml down
  security:
    - weblisk agents describe security-scanner    # if available
    - trivy image weblisk/server:$TAG
```

### Stage 4: Deploy

```yaml
deploy:
  staging:
    trigger: push to main
    steps:
      - deploy weblisk/server:$TAG to staging
      - run smoke tests against staging URL
      - notify team on success/failure

  production:
    trigger: manual approval (or tag push)
    steps:
      - deploy weblisk/server:$TAG to production
      - monitor error rate for 5 minutes
      - if error rate > threshold → auto-rollback
      - notify team on success/failure
```

### GitHub Actions Example

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - name: Lint
        run: |
          go vet ./...
          golangci-lint run

      - name: Test
        run: go test ./... -race -cover

      - name: Build image
        run: |
          TAG="${{ github.sha }}"
          docker build -t registry.example.com/weblisk:$TAG .

      - name: Push image
        run: |
          echo "${{ secrets.REGISTRY_TOKEN }}" | docker login registry.example.com -u ${{ secrets.REGISTRY_USER }} --password-stdin
          docker push registry.example.com/weblisk:$TAG

      - name: Deploy to staging
        run: |
          # Platform-specific deploy command
          # kubectl set image deployment/weblisk server=registry.example.com/weblisk:$TAG
          # OR: fly deploy --image registry.example.com/weblisk:$TAG
          echo "Deploy to staging"
```

---

## Deployment Strategies

### Rolling Update (Default)

Replace instances one at a time. Zero downtime.

```
Instance 1: v1 → v2 (healthy) → route traffic
Instance 2: v1 → v2 (healthy) → route traffic
Instance 3: v1 → v2 (healthy) → done
```

- Health check must pass before routing traffic to new instance
- If health check fails → stop rollout, keep remaining on v1

### Blue-Green

Run two identical environments. Switch traffic atomically.

```
Blue  (v1): serving traffic
Green (v2): deployed, health-checked

Switch: route all traffic to Green
Verify: monitor for errors
Rollback: route back to Blue (instant)
```

- Higher cost (2x infrastructure during deployment)
- Instant rollback
- Good for critical deployments

### Canary

Route a small percentage of traffic to the new version.

```
v1: 95% of traffic
v2:  5% of traffic → monitor error rate

If error rate is acceptable:
  v2: 25% → 50% → 100%

If error rate spikes:
  Rollback: v1: 100%
```

---

## Health Checks

### Deployment Health Check

The orchestrator's `/health` endpoint is the primary health check
target for deployment platforms:

```
GET /health HTTP/1.1

200 OK — healthy, route traffic
503 Service Unavailable — unhealthy, do not route traffic
```

### Startup vs Readiness

| Check | Purpose | Endpoint | Timing |
|-------|---------|----------|--------|
| Startup | Has the process started? | `/health` | On boot, with timeout |
| Readiness | Can it serve traffic? | `/health` (status=healthy) | Continuous |
| Liveness | Is the process stuck? | `/health` | Continuous, less frequent |

### Kubernetes Probes

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 9800
  initialDelaySeconds: 10
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health
    port: 9800
  initialDelaySeconds: 5
  periodSeconds: 10

startupProbe:
  httpGet:
    path: /health
    port: 9800
  failureThreshold: 30
  periodSeconds: 2
```

---

## Database Migrations

### Migration File Convention

```
migrations/
  001_initial_schema.sql
  002_add_user_roles.sql
  003_add_federation_peers.sql
```

### Migration Process

```
1. On server start (before accepting traffic):
   a. Check current migration version in database
   b. Apply any pending migrations in order
   c. If migration fails → abort startup, log error
   d. If all migrations pass → mark ready, accept traffic

2. Rollback:
   a. Each migration file has an UP and DOWN section
   b. Rolling back applies DOWN in reverse order
   c. Rollback is manual — not automatic on deployment failure
      (data migrations may not be reversible)
```

### Zero-Downtime Migrations

For production with rolling updates:
- **Additive only** — add columns, add tables, add indexes
- **Never remove** columns in the same release that stops using them
- Use a two-phase approach:
  1. Release N: add new column, write to both old and new
  2. Release N+1: read from new column, stop writing to old
  3. Release N+2: remove old column

---

## Rollback

### Automatic Rollback

The deployment platform monitors error rate after deploy:

```
1. Deploy new version
2. Wait 60 seconds for startup
3. Monitor error rate for 5 minutes:
   - If error_rate > 5% → trigger rollback
   - If no anomaly → deployment complete
4. Rollback: redeploy previous image tag
```

### Manual Rollback

```bash
# Rollback to previous version
weblisk deploy rollback --env production

# Rollback to specific version
weblisk deploy rollback --env production --version 1.1.0
```

---

## Implementation Notes

- Container images MUST NOT contain secrets, .env files, or private
  keys — these are injected at runtime
- Build images in CI, not on developer machines — ensures
  reproducibility
- Pin base image versions (e.g., `golang:1.22-alpine`, not
  `golang:latest`)
- Run container security scanning (Trivy, Snyk) in CI before push
- Database migrations run as part of server startup, not as a
  separate job — this keeps the deployment atomic
- For multi-region deployments, database replication and conflict
  resolution are out of scope for this pattern (handled by the
  storage layer)

## Verification Checklist

- [ ] Dockerfile uses multi-stage build with `alpine` base, non-root `weblisk` user (UID 1000), and no build tools in the runtime image
- [ ] Image tag follows `<name>:<semver>-<git-sha-short>` format (e.g., `weblisk/server:1.2.0-abc1234`)
- [ ] Secrets never appear in source code, config files, Docker images, build logs, or CI pipeline definitions
- [ ] Configuration resolves in order: built-in defaults → weblisk.yaml → env-specific yaml → WL_* environment variables → secrets manager
- [ ] CI pipeline executes four stages in order: lint & check → build image → test (unit + integration + security) → deploy
- [ ] Rolling update verifies health check passes on each new instance before routing traffic; failed health check stops rollout
- [ ] Automatic rollback triggers when error rate exceeds 5% during the 5-minute post-deploy monitoring window
- [ ] Database migrations run on server startup before accepting traffic; failed migration aborts startup
- [ ] Zero-downtime migrations are additive only — column removal uses a two-phase (or three-release) approach
- [ ] Base images are pinned to specific versions (e.g., `golang:1.22-alpine`, not `golang:latest`)
- [ ] Container security scanning (Trivy or equivalent) runs in CI before image push
- [ ] Health endpoint returns 200 for healthy and 503 for unhealthy; Kubernetes probes (liveness, readiness, startup) are configured
