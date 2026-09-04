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
          fields_used: [code, error, detail]
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

Implementations MAY support external secret stores in addition to
the default file-based store. The framework's secret client abstracts
the backend — agent code is identical regardless of store.

Alternative store backends MUST:
- Implement the same `secrets.get(key)` / `secrets.exists(key)` interface
- Support the same per-agent isolation model
- Integrate with the rotation lifecycle
- Emit the same audit trail events

The store backend is selected via runtime configuration. Platform
guides (`platforms/*.md`) document specific backend integrations.

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
3. OR: the operator defines a shared scope (via the configured shared
   prefix) that multiple agents can read from

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

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| Secret store backend | `file` | Backend type (file-based, environment, or external vault) |
| Secret store path | Implementation-defined | File store location |
| Cache TTL | `0` | Cache TTL in seconds (0 = no cache) |
| Shared prefix | `_shared` | Shared secrets namespace |

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

```yaml
types:
  SecretDeclaration:
    fields:
      key:
        type: string
        required: true
        description: "Secret key (UPPER_SNAKE_CASE)"
      description:
        type: string
        required: true
        description: "Purpose of this secret"
      required:
        type: bool
        required: true
        description: "Whether agent cannot start without it"
      rotation:
        type: string
        required: true
        description: "`manual`, `scheduled`, `automatic`"
      rotation_schedule:
        type: string
        required: false
        description: "Cron expression (when rotation = scheduled)"
      rotation_handler:
        type: string
        required: false
        description: "Handler function name (when rotation ≠ manual)"
```

### SecretMetadata

```yaml
types:
  SecretMetadata:
    fields:
      key:
        type: string
        required: true
        description: "Secret key"
      created_at:
        type: string
        required: true
        description: "ISO 8601 creation timestamp"
      created_by:
        type: string
        required: true
        description: "Identity of creator"
      last_rotated:
        type: string
        required: false
        description: "Last rotation timestamp"
      rotation_schedule:
        type: string
        required: false
        description: "Cron expression"
      expires_at:
        type: string
        required: false
        description: "Expiration timestamp (null = no expiry)"
      description:
        type: string
        required: true
        description: "Purpose"
```

---

## Deployment Secret Delivery

Secrets must reach production environments without passing through
source control, CI logs, or build artifacts. This section defines how
secrets flow from operator to running deployment.

### Delivery Models

| Model | Flow | Best For |
|-------|------|----------|
| **Direct provision** | Operator runs `weblisk secret set` on production host | Single-server, VPS |
| **Environment injection** | Platform injects env vars at deploy time | PaaS (Cloudflare, Railway, Fly) |
| **Vault sync** | CI pulls from vault → sets env vars / writes files | Enterprise, multi-service |
| **Sealed secrets** | Encrypted secret committed to repo, decrypted at deploy | Kubernetes, GitOps |

### Direct Provision (File Store)

For file-based deployments, the operator provisions secrets before
first start:

```bash
# On production host
$ weblisk secret set email-send SMTP_PASSWORD
Enter value: ********
✓ Written to .weblisk/secrets/email-send/SMTP_PASSWORD (0600)

$ weblisk server start
✓ All required secrets present. Starting...
```

### Environment Injection (PaaS)

When using environment variables as the secret backend, the
framework reads secrets from environment variables. The CI/CD
pipeline sets these from the platform's secret store.

**Rules for CI/CD pipelines:**
1. Secrets are injected from the platform's secret store — never
   from repository files
2. Secret values MUST NOT appear in pipeline logs
3. Secret env vars are scoped to the deploy step only — not available
   in build/test steps unless explicitly required
4. Pipeline configuration files commit to the repo but reference
   secret names, never values

### External Vault Sync

For vault-backed deployments, the CI pipeline fetches secrets from
the external vault and provisions them into the framework's secret
store. The specific vault CLI commands are platform-dependent.

### Sealed Secrets (Kubernetes / GitOps)

For Kubernetes deployments, secrets can be encrypted and committed
to version control. The cluster controller decrypts them at deploy
time. The specific sealing mechanism is platform-dependent.

### What MUST NOT Be in CI/CD Pipelines

| Never Do This | Why | Alternative |
|--------------|-----|-------------|
| Hardcode secrets in workflow files | Plain text in repo | Use platform secret store |
| Echo/print secret values for debugging | Appears in logs | Verify presence without revealing values |
| Pass secrets as CLI arguments | Shell history, process list | Use stdin or interactive prompt |
| Store secrets in build artifacts | Artifacts are downloadable | Inject at runtime only |
| Use same secrets across environments | Blast radius | Separate secret sets per environment |

---

## Implementation Notes

- The file-based store is the default and works for all deployment
  models. External vault integration is an optimization for
  enterprise deployments, not a requirement.
- Secret files MUST NOT be committed to version control. Add
  the secrets directory to `.gitignore`.
- When using environment variables as the store, secret keys are
  prefixed with a framework-specific prefix and scoped by agent name.
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
- [ ] `weblisk secret set` uses interactive prompt or --stdin, never CLI arguments
