<!-- blueprint
type: pattern
name: secrets
version: 1.0.0
requires: [protocol/types, protocol/identity, architecture/agent, architecture/storage]
platform: any
tier: free
-->

# Secrets Pattern

Secure storage, access, rotation, and audit of sensitive credentials
used by Weblisk agents. Defines how agents declare, retrieve, and
manage API keys, integration tokens, connection strings, and other
secrets without exposing them in blueprints, logs, or inter-agent
communication.

## Overview

Agents that integrate with external services (SMTP servers, LLM
providers, analytics APIs, payment gateways) need credentials. This
pattern defines the standard interface for managing those credentials
so that:

- Secrets are never stored in blueprint files
- Secrets are never logged or transmitted in event payloads
- Each agent can only access secrets it has declared
- Secret rotation happens without agent restart
- Every secret access is audited

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/identity
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentIdentity
          fields_used: [name, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
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
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentConfig
          fields_used: [name, secrets]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: StoreInterface
          fields_used: [get, put, delete]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Declaration before access** — Agents declare what secrets they
   need in their blueprint. The framework rejects access to
   undeclared secrets.
2. **Least privilege** — An agent can only read secrets it has
   declared. Cross-agent secret access is forbidden.
3. **No plaintext in transit** — Secrets are resolved at the agent
   process level. They never appear in event payloads, direct
   messages, or API responses.
4. **Rotation without restart** — Secrets can be updated while agents
   are running. Agents MUST re-read secrets on use, not cache
   indefinitely.
5. **Zero-dependency storage** — The default secret store is
   file-based (`.weblisk/secrets/`). Implementations MAY integrate
   external vaults but MUST NOT require them.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: secret-access
      description: Secure retrieval of declared secrets scoped to the requesting agent
      parameters:
        - name: key
          type: string
          required: true
          description: Secret key in UPPER_SNAKE_CASE format
      inherits: Agent-scoped secret isolation and audit logging
      overridable: false
      override_constraints: Agents cannot bypass scoping or audit
    - name: secret-rotation
      description: Update secret values without agent restart
      parameters:
        - name: key
          type: string
          required: true
          description: Secret key to rotate
        - name: method
          type: enum(manual, scheduled, automatic)
          required: true
          description: Rotation trigger method
      inherits: Zero-downtime rotation with cache invalidation
      overridable: true
      override_constraints: Must emit security.secret_rotated event
  types:
    - name: SecretDeclaration
      description: Agent secret requirement with key, description, and rotation policy
      inherited_by: Types section
    - name: SecretMetadata
      description: Secret lifecycle metadata including creation, rotation, and expiry
      inherited_by: Types section
  endpoints:
    - path: /v1/agent/{name}/rotate-secret
      description: Trigger manual secret rotation for a specific key
      inherited_by: Secret Rotation section
  events:
    - topic: security.secret.rotated
      description: Emitted when a secret value is rotated
      payload: {key, method, rotated_by, timestamp}
    - topic: security.secret_accessed
      description: Audit log event for every secret retrieval
      payload: {key, agent, timestamp}
    - topic: security.secret_denied
      description: Emitted when an agent attempts unauthorized secret access
      payload: {key, requesting_agent, owning_agent, timestamp}
```

---

## Secret Declaration

Agents declare their required secrets in the blueprint:

```markdown
## Configuration

### Secrets
| Secret Key | Description | Required | Rotation |
|-----------|-------------|----------|----------|
| SMTP_PASSWORD | SMTP server password for email delivery | yes | manual |
| SMTP_API_KEY | Alternative: SMTP API key (mutually exclusive with SMTP_PASSWORD) | no | manual |
| LLM_API_KEY | API key for LLM provider | no | manual |
```

### Declaration Rules

- Secret keys MUST be UPPER_SNAKE_CASE
- Secret keys MUST be prefixed with the integration name
  (e.g., `SMTP_PASSWORD`, not `PASSWORD`)
- Each secret key MUST have a description explaining its purpose
- `required: yes` means the agent MUST NOT start without this secret
- `rotation` indicates how the secret is rotated: `manual`, `scheduled`,
  or `automatic`

---

## Secret Storage

### Default: File-Based Store

```
.weblisk/
  secrets/
    cron/              # Secrets scoped to cron agent
    email-send/        # Secrets scoped to email-send agent
      SMTP_PASSWORD    # One file per secret, contains value only
      SMTP_API_KEY
    seo-analyzer/
      LLM_API_KEY
```

Each secret is a single file containing only the secret value (no
newlines, no metadata). File permissions MUST be `0600` (owner
read/write only).

### Secret Metadata

Secret metadata (rotation schedule, last rotated, created by) is
stored separately from the secret value:

```json
// .weblisk/secrets/_metadata.json
{
  "email-send/SMTP_PASSWORD": {
    "created_at": "2026-04-01T00:00:00Z",
    "created_by": "operator:admin",
    "last_rotated": "2026-04-20T00:00:00Z",
    "rotation_schedule": null,
    "expires_at": null,
    "description": "SMTP server password"
  }
}
```

### Alternative Stores

Implementations MAY support external secret stores:

| Store | Configuration |
|-------|--------------|
| Environment variables | `WL_SECRET_STORE=env` — secrets read from env vars prefixed with `WL_SECRET_` |
| HashiCorp Vault | `WL_SECRET_STORE=vault` — requires `WL_VAULT_ADDR` and `WL_VAULT_TOKEN` |
| AWS Secrets Manager | `WL_SECRET_STORE=aws-sm` — requires AWS credentials |
| Azure Key Vault | `WL_SECRET_STORE=azure-kv` — requires `WL_AZURE_KV_URL` |
| Cloudflare Secrets | `WL_SECRET_STORE=cf-secrets` — for Cloudflare Workers |

The agent code is identical regardless of store. The framework's
secret client abstracts the backend.

---

## Secret Access API

Agents access secrets through the framework's secret client:

```
secrets.get(key) → string | error
secrets.exists(key) → bool
```

### Access Rules

| Rule | Enforcement |
|------|------------|
| Agent can only access its own declared secrets | Framework rejects undeclared key access |
| Secret values are strings | Binary secrets must be base64-encoded |
| Secrets are not cached by the framework | Each `get()` reads from store (implementations MAY cache with short TTL) |
| Secret access is audited | Every `get()` emits a `security.secret_accessed` log event |

### Access During Startup

Required secrets are validated during agent startup:

```
1. Read blueprint secret declarations
2. For each required secret:
   a. Attempt secrets.get(key)
   b. If missing → log error, abort startup
3. For each optional secret:
   a. Attempt secrets.get(key)
   b. If missing → log info, continue (feature disabled)
4. Agent startup proceeds
```

---

## Secret Rotation

### Manual Rotation

```
1. Operator updates secret value in store
   (file, vault, environment variable)
2. Operator sends rotation signal:
   POST /v1/agent/{name}/rotate-secret
   { "key": "SMTP_PASSWORD" }
3. Agent receives signal → clears any cached value
4. Next secrets.get() reads new value
5. Log: security.secret_rotated with {key, rotated_by}
6. Emit event: security.secret.rotated
```

### Scheduled Rotation

For secrets with `rotation: scheduled`:

```json
{
  "key": "LLM_API_KEY",
  "rotation_schedule": "0 0 1 * *",
  "rotation_handler": "generate_new_key"
}
```

The framework invokes the rotation handler on schedule:

```
1. Cron triggers rotation check
2. For each secret with due rotation:
   a. Call rotation_handler (agent-defined function)
   b. Handler generates/fetches new secret value
   c. Framework writes new value to store
   d. Framework signals agent to clear cache
   e. Log: security.secret_rotated with {key, method: "scheduled"}
```

### Automatic Rotation

For secrets that support API-based rotation (e.g., API keys that can
be regenerated via the provider's API):

```
1. Agent detects auth failure with current secret
2. Agent calls rotation_handler
3. Handler uses provider API to generate new key
4. New key written to store
5. Retry original operation with new key
6. Log: security.secret_rotated with {key, method: "automatic", trigger: "auth_failure"}
```

---

## Secret Scoping

### Per-Agent Isolation

Secrets are scoped to the declaring agent. Agent A cannot read
Agent B's secrets, even if they have the same key name.

```
email-send/SMTP_PASSWORD  ← only email-send can read
alerting/SMTP_PASSWORD     ← only alerting can read (different value)
```

### Shared Secrets

When multiple agents need the same credential:

1. Each agent declares the secret in its blueprint independently
2. The operator provisions the same value under each agent's scope
3. OR: the operator uses `WL_SECRET_SHARED_PREFIX` to define a shared
   scope that multiple agents can read from

```
.weblisk/secrets/
  _shared/
    LLM_API_KEY         # Shared by any agent that declares it
  email-send/
    SMTP_PASSWORD       # Agent-specific
```

Shared secrets are only accessible to agents that declare the key.
The `_shared` scope is a storage optimization, not a permission bypass.

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WL_SECRET_STORE` | `file` | Secret backend: `file`, `env`, `vault`, `aws-sm`, `azure-kv`, `cf-secrets` |
| `WL_SECRET_PATH` | `.weblisk/secrets` | File store path |
| `WL_SECRET_CACHE_TTL` | `0` | Cache TTL in seconds (0 = no cache) |
| `WL_SECRET_SHARED_PREFIX` | `_shared` | Shared secrets directory name |
| `WL_VAULT_ADDR` | — | HashiCorp Vault address |
| `WL_VAULT_TOKEN` | — | HashiCorp Vault token |

---

## Audit Trail

Every secret operation is logged:

| Event | Log Type | Level | Details |
|-------|----------|-------|---------|
| Secret accessed | `security.secret_accessed` | debug | `{key, agent}` |
| Secret not found | `security.secret_missing` | warn | `{key, agent, required}` |
| Secret rotated | `security.secret_rotated` | info | `{key, method, rotated_by}` |
| Unauthorized access | `security.secret_denied` | warn | `{key, requesting_agent, owning_agent}` |
| Secret expired | `security.secret_expired` | warn | `{key, expired_at}` |

---

## Types

### SecretDeclaration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | yes | Secret key (UPPER_SNAKE_CASE) |
| description | string | yes | Purpose of this secret |
| required | bool | yes | Whether agent cannot start without it |
| rotation | string | yes | `manual`, `scheduled`, `automatic` |
| rotation_schedule | string | no | Cron expression (when rotation = scheduled) |
| rotation_handler | string | no | Handler function name (when rotation ≠ manual) |

### SecretMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key | string | yes | Secret key |
| created_at | string | yes | ISO 8601 creation timestamp |
| created_by | string | yes | Identity of creator |
| last_rotated | string | no | Last rotation timestamp |
| rotation_schedule | string | no | Cron expression |
| expires_at | string | no | Expiration timestamp (null = no expiry) |
| description | string | yes | Purpose |

---

## Deployment Secret Delivery

Secrets must reach production environments without passing through
source control, CI logs, or build artifacts. This section defines how
secrets flow from operator to running deployment.

### Delivery Models

| Model | Flow | Best For |
|-------|------|----------|
| **Direct provision** | Operator runs `weblisk secrets set` on production host | Single-server, VPS |
| **Environment injection** | Platform injects env vars at deploy time | PaaS (Cloudflare, Railway, Fly) |
| **Vault sync** | CI pulls from vault → sets env vars / writes files | Enterprise, multi-service |
| **Sealed secrets** | Encrypted secret committed to repo, decrypted at deploy | Kubernetes, GitOps |

### Direct Provision (File Store)

For file-based deployments, the operator provisions secrets before
first start:

```bash
# On production host
$ weblisk secrets set email-send SMTP_PASSWORD
Enter value: ********
✓ Written to .weblisk/secrets/email-send/SMTP_PASSWORD (0600)

$ weblisk server start
✓ All required secrets present. Starting...
```

### Environment Injection (PaaS)

When `WL_SECRET_STORE=env`, the framework reads secrets from
environment variables. The CI/CD pipeline sets these from the
platform's secret store:

```yaml
# Example: GitHub Actions → Cloudflare Workers
deploy:
  steps:
    - run: wrangler secret put SMTP_PASSWORD <<< "${{ secrets.SMTP_PASSWORD }}"
    - run: wrangler secret put LLM_API_KEY <<< "${{ secrets.LLM_API_KEY }}"
```

**Rules for CI/CD pipelines:**
1. Secrets are injected from the platform's secret store (GitHub Secrets,
   Cloudflare Secrets, etc.) — never from repository files
2. Secret values MUST NOT appear in pipeline logs. Use `::add-mask::`
   or equivalent log masking
3. Secret env vars are scoped to the deploy step only — not available
   in build/test steps unless explicitly required
4. Pipeline configuration files (`.github/workflows/*.yml`) commit to
   the repo but reference secret names, never values

### Vault Sync

For vault-backed deployments (`WL_SECRET_STORE=vault`):

```bash
# CI pipeline fetches secrets from vault and provisions them
export VAULT_TOKEN=$(vault login -method=approle ...)
vault kv get -field=value secret/weblisk/email-send/SMTP_PASSWORD | \
  weblisk secrets set email-send SMTP_PASSWORD --stdin
```

### Sealed Secrets (Kubernetes / GitOps)

For Kubernetes deployments, secrets can be encrypted and committed:

```bash
# Encrypt secret for cluster (only cluster can decrypt)
$ kubeseal --format=yaml < secret.yaml > sealed-secret.yaml
$ git add sealed-secret.yaml  # Safe to commit — encrypted
```

The sealed secret is decrypted by the cluster controller at deploy
time and mounted as files or env vars in the pod.

### What MUST NOT Be in CI/CD Pipelines

| Never Do This | Why | Alternative |
|--------------|-----|-------------|
| Hardcode secrets in workflow files | Plain text in repo | Use platform secret store |
| Echo/print secret values for debugging | Appears in logs | Use `weblisk secrets list` to verify presence |
| Pass secrets as CLI arguments | Shell history, process list | Use `--stdin` flag or interactive prompt |
| Store secrets in build artifacts | Artifacts are downloadable | Inject at runtime only |
| Use same secrets across environments | Blast radius | Separate secret sets per environment |

---

## Implementation Notes

- The file-based store is the default and works for all deployment
  models. External vault integration is an optimization for
  enterprise deployments, not a requirement.
- Secret files MUST NOT be committed to version control. Add
  `.weblisk/secrets/` to `.gitignore`.
- When using environment variables as the store, secret keys are
  prefixed with `WL_SECRET_` and scoped by agent name:
  `WL_SECRET_EMAIL_SEND_SMTP_PASSWORD`.
- Cache TTL should be short (30-60 seconds max) to ensure rotation
  takes effect quickly. For most agents, no cache (TTL=0) is
  acceptable.
- Secrets MUST be read synchronously during request processing, not
  pre-loaded into memory at startup (except for required validation).
  This ensures rotation takes effect immediately.
- In multi-instance deployments, all instances read from the same
  secret store. Rotation signals should be broadcast to all instances.

## Verification Checklist

- [ ] Agents declare required secrets in their blueprint
- [ ] Agent startup fails if a required secret is missing
- [ ] Agent startup succeeds with optional secrets missing
- [ ] Agents can only access their own declared secrets
- [ ] Cross-agent secret access is rejected with security.secret_denied log
- [ ] Secret values never appear in logs (any level)
- [ ] Secret values never appear in event payloads
- [ ] Secret values never appear in API responses
- [ ] Manual rotation updates the value without agent restart
- [ ] Scheduled rotation executes on cron schedule
- [ ] Automatic rotation triggers on auth failure
- [ ] Every secret access is audit-logged
- [ ] File-based store uses 0600 permissions
- [ ] Secret metadata tracks creation, rotation, and expiry
- [ ] Shared secrets are accessible only to declaring agents
- [ ] CI/CD pipelines inject secrets from platform secret stores, never from repo files
- [ ] Secret values never appear in CI/CD logs (log masking enforced)
- [ ] Secrets are scoped per-environment (dev/staging/prod use different values)
- [ ] `weblisk secrets set` uses interactive prompt or --stdin, never CLI arguments
