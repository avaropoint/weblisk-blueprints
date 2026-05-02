<!-- blueprint
type: architecture
name: cli
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/admin, patterns/command]
platform: any
tier: free
-->

# Weblisk CLI Specification

> **This is the authoritative specification for the
> [weblisk-cli](https://github.com/avaropoint/weblisk-cli) project.**
> Every command documented here MUST be implemented in weblisk-cli.
> The CLI itself is ultra-lightweight — it resolves templates from
> [weblisk-templates](https://github.com/avaropoint/weblisk-templates),
> reads blueprints from this repository, and dispatches to the
> configured LLM for code generation. The CLI carries minimal logic;
> the LLM does the heavy lifting.

Specification for CLI commands that manage the complete Weblisk
development and operational lifecycle — from project creation through
scaffolding, code generation, dev server, production build, blueprint
management, and runtime operations.

## Overview

The CLI has two command surfaces:

1. **Development commands** — project scaffolding, code generation, dev
   server, production builds (`weblisk new`, `weblisk dev`, `weblisk build`,
   `weblisk server init`, `weblisk agent create`)
2. **Operations commands** — interrogate and manage a running hub via the
   orchestrator's admin API (`weblisk status`, `weblisk agents`,
   `weblisk domains`, `weblisk audit`, `weblisk federation`)

Operations commands use the operator's Ed25519 identity stored in
`~/.weblisk/keys/` for authentication.

Commands follow a `weblisk <noun> <verb>` pattern and output
structured, human-readable tables by default, with `--json` for
machine-readable output.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /v1/health
          methods: [POST]
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
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: WLT
          fields_used: [sub, iss, iat, exp, cap, role]
        - name: AgentManifest
          fields_used: [name, version, type, url, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/admin/*
          methods: [GET, POST, PUT, DELETE]
        - path: /v1/services
          methods: [POST]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/admin
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - path: /v1/admin/operators/register
          methods: [POST]
        - path: /v1/admin/overview
          methods: [GET]
        - path: /v1/admin/agents
          methods: [GET]
        - path: /v1/admin/approvals
          methods: [GET, POST]
      types:
        - name: OperatorRecord
          fields_used: [name, public_key, role, status]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Responsibilities

### Owns

- CLI command structure (`weblisk <noun> <verb>` pattern)
- Project scaffolding from templates (`weblisk new`)
- Code generation via LLM dispatch (`weblisk server init`, `weblisk agent create`)
- Blueprint and template resolution (local → custom sources → core)
- Dev server with file watching (`weblisk dev`)
- Production builds (`weblisk build`)
- Static framework vendoring (`weblisk vendor`)
- Operator Ed25519 key pair generation and local key storage (`~/.weblisk/keys/`)
- Operator registration and token management (`~/.weblisk/token`)
- Human-readable table output and `--json` machine-readable output formatting
- Interactive confirmation for destructive actions
- Connection management to orchestrator's admin API

### Does NOT Own

- Admin API endpoints (owned by `architecture/admin`)
- Orchestrator state or agent lifecycle (CLI reads/writes via API)
- Admin dashboard SPA (owned by `architecture/admin`)
- Operator authentication model (owned by `architecture/admin`; CLI consumes it)
- Workflow or task execution (CLI triggers actions via API)
- Template contents (owned by `weblisk-templates`)
- Client framework (owned by `weblisk`)
- Blueprint specifications (owned by this repository — `weblisk-blueprints`)

---

## Interfaces

The CLI’s public interface is the set of terminal commands documented in
the sections below: [Project Commands](#project-commands),
[Server Commands](#server-commands),
[Blueprint Commands](#blueprint-commands),
[Identity Commands](#identity-commands),
[Status Commands](#status-commands), [Agent Commands](#agent-commands),
[Domain Commands](#domain-commands), [Workflow Commands](#workflow-commands),
[Approval Commands](#approval-commands), [Strategy Commands](#strategy-commands),
[Federation Commands](#federation-commands), and
[Audit Commands](#audit-commands).

---

## Data Flow

1. Operator runs a CLI command (e.g., `weblisk agents list`)
2. CLI loads operator identity from `~/.weblisk/keys/operator.key`
3. CLI loads auth token from `~/.weblisk/token` (refreshes if near expiry)
4. CLI constructs HTTP request to orchestrator admin API endpoint
5. Request signed with operator's Ed25519 key, token included in `Authorization: Bearer` header
6. Orchestrator validates token, checks operator role against endpoint minimum
7. Orchestrator returns JSON response
8. CLI formats response as human-readable table (or raw JSON with `--json`)
9. For write operations: CLI prompts for interactive confirmation before sending
10. Exit code set based on success/failure (0 = success, 1 = error, 2 = auth failure)

---

## Design Principles

1. **Ed25519 identity, not passwords** — The CLI uses the same
   cryptographic identity system as agents. No passwords, no session
   cookies.
2. **Read by default, write with flags** — Destructive commands require
   explicit `--confirm` or interactive confirmation.
3. **Consistent output** — All commands output tables for humans, JSON
   with `--json` for scripts and piping.
4. **Offline-aware** — If the orchestrator is unreachable, commands
   fail fast with a clear message and non-zero exit code.

---

## Project Commands

### `weblisk new`

Create a new project from a template.

```bash
$ weblisk new my-app
$ weblisk new my-app --template client/blog
$ weblisk new my-app --template server/starter
$ weblisk new my-app --template client/blog --template server/starter
```

Templates are resolved from
[weblisk-templates](https://github.com/avaropoint/weblisk-templates) in
priority order: local `./templates/` → `WL_TEMPLATE_SOURCES` → core.

When multiple `--template` flags are specified, files are merged — client
templates provide pages and islands, server templates provide hub
configuration and agent specs.

**Security:** Every scaffolded project MUST include a `.gitignore` with
entries for `.weblisk/secrets/`, `.weblisk/keys/`, `.weblisk/token`,
`.env`, and `.env.*`. This is non-configurable and always generated.

| Flag | Description |
|------|-------------|
| `--template <path>` | Template to scaffold (default: `client/default`) |
| `--local` | Use local framework files instead of CDN |
| `--lib <path>` | Custom framework directory (default: `lib/weblisk`) |

### `weblisk dev`

Start the development server with file watching and live reload.

```bash
$ weblisk dev
$ weblisk dev --port 3000
```

For client-only projects, serves static files with live reload. For
server projects, builds and runs the hub with automatic restart on file
changes.

| Flag | Description |
|------|-------------|
| `--port <n>` | Dev server port (default: from `WL_PORT` or 3000) |

### `weblisk build`

Build for production — minify, fingerprint, and optimize.

```bash
$ weblisk build
$ weblisk build --minify --fingerprint
```

| Flag | Description |
|------|-------------|
| `--minify` | Minify HTML, CSS, and JS |
| `--fingerprint` | Add content hashes to filenames for cache busting |

### `weblisk vendor`

Copy the Weblisk client framework into the project for offline use.

```bash
$ weblisk vendor
$ weblisk vendor --dest js/vendor
```

| Flag | Description |
|------|-------------|
| `--dest <path>` | Destination directory (default: `lib/weblisk`) |

### `weblisk version`

Print the CLI version.

```bash
$ weblisk version
weblisk v1.1.0
```

### `weblisk doctor`

Validate project health and configuration.

```bash
$ weblisk doctor
```

Checks performed:

| Check | Severity | Description |
|-------|----------|-------------|
| `.gitignore` exists | error | Project must have a `.gitignore` |
| `.gitignore` excludes secrets | error | Must contain `.weblisk/secrets/`, `.weblisk/keys/`, `.weblisk/token` |
| `.gitignore` excludes `.env` | warn | Should exclude `.env` and `.env.*` |
| `.weblisk/config.yaml` valid | error | Config must parse and pass schema validation |
| Blueprint YAML valid | error | All blueprints must parse without errors |
| Secret declarations complete | warn | Declared secrets should have values in `.weblisk/secrets/` |
| File permissions | warn | `.weblisk/secrets/` files should be 0600, directories 0700 |

Exit codes: 0 = all pass, 1 = errors found, 2 = warnings only.

### `weblisk secrets`

Manage secrets for the project. All operations are local — secrets
live in `.weblisk/secrets/` and are never transmitted.

```bash
$ weblisk secrets list
$ weblisk secrets set email-send SMTP_PASSWORD
$ weblisk secrets set _shared LLM_API_KEY
$ weblisk secrets get email-send SMTP_PASSWORD
$ weblisk secrets delete email-send SMTP_PASSWORD
$ weblisk secrets rotate email-send SMTP_PASSWORD
```

| Subcommand | Description |
|------------|-------------|
| `list` | Show all declared secrets and their status (set/missing) |
| `set <agent> <key>` | Set a secret value (prompts for value, never in args) |
| `get <agent> <key>` | Print secret value (for debugging only, warns on use) |
| `delete <agent> <key>` | Remove a secret value |
| `rotate <agent> <key>` | Trigger rotation (prompts for new value or runs handler) |

**Security rules:**
- `set` prompts for the value interactively — it is NEVER passed as a
  CLI argument (which would leak into shell history).
- `get` prints a warning that secret values should not be displayed in
  shared terminals. Requires `--confirm` flag.
- All operations write to `.weblisk/secrets/{agent}/{KEY}` with 0600
  permissions.
- The `list` subcommand cross-references agent blueprint declarations
  with stored values to show which secrets are missing.

---

## Server Commands

### `weblisk server init`

Generate the server implementation from blueprint specs. The CLI reads
`.weblisk/config.yaml`, `domains/*/domain.yaml`, and
`agents/*/agent.yaml`, then dispatches to the configured LLM along
with the platform blueprint to generate the implementation.

```bash
$ weblisk server init --platform go
$ weblisk server init --platform cloudflare
```

| Flag | Description |
|------|-------------|
| `--platform <p>` | Target platform: `go`, `cloudflare` (default: `go`) |

### `weblisk server start`

Build (if needed) and start all hub components.

```bash
$ weblisk server start
```

Reads `.weblisk/config.yaml` to determine which components to build
and start (orchestrator, gateway, domains, agents).

### `weblisk server verify`

Verify the server is running and healthy.

```bash
$ weblisk server verify
$ weblisk server verify --url http://localhost:9800
```

| Flag | Description |
|------|-------------|
| `--url <url>` | Orchestrator URL (default: `http://localhost:9800`) |

### `weblisk agent create`

Generate an agent implementation from its blueprint spec.

```bash
$ weblisk agent create seo --platform go
$ weblisk agent create forecaster --platform cloudflare
```

| Flag | Description |
|------|-------------|
| `--platform <p>` | Target platform (default: `go`) |

### `weblisk agent start`

Build and run a single agent.

```bash
$ weblisk agent start seo
$ weblisk agent start seo --orch http://localhost:9800 --port 9710
```

| Flag | Description |
|------|-------------|
| `--orch <url>` | Orchestrator URL |
| `--port <n>` | Listen port (default: auto-assigned) |

### `weblisk agent verify`

Run protocol conformance checks against a running agent.

```bash
$ weblisk agent verify --url http://localhost:9710
```

### `weblisk agent list`

List locally scaffolded agents.

```bash
$ weblisk agent list
```

### `weblisk domain create`

Generate a domain controller implementation from its spec.

```bash
$ weblisk domain create seo --platform go
```

| Flag | Description |
|------|-------------|
| `--platform <p>` | Target platform (default: `go`) |

### `weblisk domain start`

Build and run a single domain controller.

```bash
$ weblisk domain start seo
```

### `weblisk gateway create`

Generate the application gateway from hub configuration.

```bash
$ weblisk gateway create --platform go
```

| Flag | Description |
|------|-------------|
| `--platform <p>` | Target platform (default: `go`) |

### `weblisk gateway start`

Build and run the application gateway.

```bash
$ weblisk gateway start
```

---

## Blueprint Commands

### `weblisk blueprints update`

Force re-fetch all blueprint sources.

```bash
$ weblisk blueprints update
```

Performs `git pull` on each cached source in `~/.weblisk/blueprints/`.
If a source is unreachable, uses the last cached version.

### `weblisk validate`

Validate blueprint compliance for the current project.

```bash
$ weblisk validate
$ weblisk validate agents/seo-analyzer.yaml
```

Checks frontmatter, required sections, type definitions, dependency
resolution, and compliance level assignment.

### `weblisk pattern apply`

Apply a cross-cutting pattern to a resource.

```bash
$ weblisk pattern apply auth-session --resource gateway
$ weblisk pattern apply webhook-inbound --resource domain:seo
```

Reads the pattern blueprint, dispatches to the LLM with the target
resource context, and generates the pattern implementation.

---

## Identity Commands

### `weblisk operator init`

Generate an operator Ed25519 key pair, encrypted with a passphrase.

```bash
$ weblisk operator init
Enter passphrase (min 12 characters): ********
Confirm passphrase: ********
Generated operator key pair:
  Private: ~/.weblisk/keys/operator.key (encrypted, argon2id + AES-256-GCM)
  Public:  ~/.weblisk/keys/operator.pub
  Key ID:  a1b2c3d4e5f6...

Keep your private key safe. It is your identity.
The passphrase is NOT stored — you must remember it.
```

- Generates keys in `~/.weblisk/keys/` (mode 0700 directory, 0600 key)
- ALWAYS prompts for passphrase — cannot be skipped or supplied via flag
- Minimum passphrase length: 12 characters (enforced)
- Private key stored in `weblisk-key-v1` format (Argon2id KDF + AES-256-GCM)
- Passphrase is never written to disk, never in shell history
- If keys already exist, prints the public key and exits (no overwrite)
- `--force` to regenerate (prompts for new passphrase, prints identity change warning)
- `--name <name>` to set operator name (default: system username)

### `weblisk operator register`

Register with a running orchestrator.

```bash
$ weblisk operator register --orch http://localhost:9800
Registering operator 'alice' with http://localhost:9800...
✓ Registered as admin (first operator — auto-approved)
  Token stored: ~/.weblisk/token
  Expires: 2026-04-26T10:00:00Z
```

- Signs the registration payload with the operator's private key
- Stores the returned token in `~/.weblisk/token`
- If not the first operator, prints "Registration pending admin approval"
- `--role <role>` to request a specific role (admin may override)

### `weblisk operator token`

Refresh or inspect the current operator token.

```bash
$ weblisk operator token
Operator: alice
Role:     admin
Expires:  2026-04-26T10:00:00Z (23h remaining)
Orch:     http://localhost:9800

$ weblisk operator token --refresh
✓ Token refreshed. Expires: 2026-04-27T10:00:00Z
```

### `weblisk operator revoke`

Revoke another operator's access (admin only).

```bash
$ weblisk operator revoke bob
Revoking operator 'bob'...
Type operator name to confirm: bob
✓ Operator 'bob' revoked. Public key invalidated, token expired.
```

- Requires admin role
- Invalidates the target operator's public key and all active tokens
- The revoked operator must re-run `operator init` + `operator register`
  to regain access (pending approval from remaining admin)
- Cannot revoke yourself (prevents lockout)
- Cannot revoke the last admin (system requires at least one)

### `weblisk operator list`

List all registered operators and their status.

```bash
$ weblisk operator list
NAME    ROLE     STATUS    REGISTERED
alice   admin    active    2026-01-15T09:00:00Z
bob     viewer   revoked   2026-02-20T14:30:00Z
carol   admin    active    2026-03-01T11:00:00Z
```

---

## Status Commands

### `weblisk status`

System overview — the CLI equivalent of the admin dashboard landing page.

```bash
$ weblisk status
Weblisk — acme-corp (http://localhost:9800)
Protocol: v1    Uptime: 2d 14h 32m

Agents:     8 online, 1 degraded, 0 offline
Domains:    3 online (seo, content, health)
Workflows:  12 today (10 ✓, 2 ✗)
Approvals:  5 pending
Federation: 2 peers, 1 pending request
Health:     94/100 ▲

Strategies:
  Improve organic traffic    ██████████░░  67%  active
  Reduce page load time      ████████████░  82%  active
```

- Calls `GET /v1/admin/overview`
- `--json` for machine-readable output
- `--watch` to refresh every 5 seconds (like `watch`)

---

## Agent Commands

### `weblisk agents list`

List all registered agents.

```bash
$ weblisk agents list
NAME              TYPE            STATUS    VERSION   TASKS(24h)  AVG LATENCY
seo-analyzer      work            online    1.0.0     45          2.3s
a11y-checker      work            online    1.0.0     23          1.1s
content-analyzer  work            online    1.0.0     18          3.4s
meta-checker      work            online    1.0.0     18          1.8s
uptime-checker    work            online    1.0.0     288         0.4s
perf-auditor      work            online    1.0.0     12          8.2s
cron              infrastructure  online    1.0.0     —           —
email-send        infrastructure  degraded  1.0.0     5           1.2s

8 agents (7 online, 1 degraded)
```

- `--type <domain|work|infrastructure>` to filter
- `--status <online|degraded|offline>` to filter
- `--json` for machine-readable output

### `weblisk agents describe <name>`

Full detail for a single agent.

```bash
$ weblisk agents describe seo-analyzer
Agent: seo-analyzer
Type:  work    Domain: seo    Version: 1.0.0
URL:   http://localhost:9710
Status: online    Uptime: 2d 14h

Capabilities:
  file:read     **/*.html
  llm:chat      *
  agent:message *

Metrics (24h):
  Tasks:          45
  Success rate:   97.8%
  Avg latency:    2.3s
  P95 latency:    5.1s
  Observations:   120
  Recommendations: 38

Recent Tasks:
  TIME        STATUS     DURATION  SUMMARY
  10:30:01    success    2.1s      Scanned 3 files
  10:25:12    success    3.4s      Analyzed metadata for 5 files
  09:15:00    failed     0.8s      File not found: missing.html

Behavioral Fingerprint:
  Manifest hash: a1b2c3...  (unchanged since registration)
  Last change: none
```

- `--json` for machine-readable output
- `--metrics-range <1h|24h|7d|30d>` to change metrics window

### `weblisk agents deregister <name>`

Force-deregister an agent (admin only).

```bash
$ weblisk agents deregister email-send
⚠ This will deregister agent 'email-send' and remove it from all workflows.
  Type agent name to confirm: email-send
✓ Agent 'email-send' deregistered.
```

- Requires `--confirm` or interactive confirmation
- Logs the deregistration in the audit trail

---

## Domain Commands

### `weblisk domains list`

List domain controllers and their status.

```bash
$ weblisk domains list
NAME      STATUS    AGENTS              WORKFLOWS            LAST ACTIVITY
seo       online    2/2 required        seo-audit, seo-opt   10m ago
content   online    2/2 required        content-audit, ...   25m ago
health    online    2/2 required        health-check, ...    5m ago
```

### `weblisk domains describe <name>`

```bash
$ weblisk domains describe seo
Domain: seo
Version: 1.0.0    Status: online    Port: 9700

Required Agents:
  NAME            STATUS
  seo-analyzer    online ●
  a11y-checker    online ●

Workflows:
  NAME          TRIGGER        EXECUTIONS(24h)  SUCCESS RATE
  seo-audit     action=audit   8                87.5%
  seo-optimize  action=optimize 3               100%

Recent Executions:
  ID            WORKFLOW     STATUS     DURATION  TIME
  exec-a1b2c3   seo-audit    completed  8.5s      10:30
  exec-d4e5f6   seo-audit    failed     3.2s      09:15
```

---

## Workflow Commands

### `weblisk workflows list`

List recent workflow executions.

```bash
$ weblisk workflows list
ID            WORKFLOW        DOMAIN   STATUS     DURATION  TIME
exec-a1b2c3   seo-audit       seo      completed  8.5s      10:30
exec-g7h8i9   content-audit   content  completed  12.1s     10:25
exec-j0k1l2   health-check    health   completed  2.3s      10:25
exec-d4e5f6   seo-audit       seo      failed     3.2s      09:15
```

- `--domain <name>` to filter by domain
- `--status <completed|failed|running>` to filter
- `--limit <n>` to control results (default: 20)

### `weblisk workflows describe <id>`

```bash
$ weblisk workflows describe exec-a1b2c3
Workflow: seo-audit
Domain:   seo
Task:     task-d4e5f6
Status:   completed
Duration: 8.5s
Started:  2026-04-25 10:30:00

Phases:
  PHASE          AGENT           STATUS     DURATION
  scan           seo-analyzer    completed  1.2s
  analyze        seo-analyzer    completed  3.8s
  accessibility  a11y-checker    completed  1.5s
  report         seo-analyzer    completed  2.0s

Output:
  Files scanned: 3
  Findings: 12 (3 critical, 5 high, 4 medium)
  Recommendations: 5 (pending approval)
```

---

## Approval Commands

### `weblisk approvals list`

List pending recommendations.

```bash
$ weblisk approvals list
ID        PRIORITY   AGENT           TARGET            SUMMARY
rec-001   critical   seo-analyzer    index.html        Update title tag
rec-002   critical   seo-analyzer    index.html        Add meta description
rec-003   high       a11y-checker    index.html        Add alt text to logo
rec-004   high       meta-checker    about.html        Add og:site_name
rec-005   medium     content-analyzer pricing.html     Split long paragraph

5 pending recommendations
```

- `--priority <critical|high|medium|low>` to filter
- `--agent <name>` to filter by recommending agent

### `weblisk approvals show <id>`

```bash
$ weblisk approvals show rec-001
Recommendation: rec-001
Agent:    seo-analyzer
Priority: critical
Target:   index.html
Element:  title

Current:  <title>Home</title>
Proposed: <title>Weblisk — Modern Web Framework</title>
Reason:   Title too short — include primary keywords for search visibility

Impact estimate: 0.8
Strategy: strat-001 (Improve organic traffic)
```

### `weblisk approvals accept <id...>`

```bash
$ weblisk approvals accept rec-001 rec-002
✓ Accepted rec-001: Update title tag (index.html)
✓ Accepted rec-002: Add meta description (index.html)
```

- Accepts one or more recommendation IDs
- `--all` to accept all pending (requires `--confirm`)
- `--priority critical` to accept all critical (requires `--confirm`)

### `weblisk approvals reject <id> --reason <reason>`

```bash
$ weblisk approvals reject rec-005 --reason "Paragraph is fine as-is"
✓ Rejected rec-005: Split long paragraph (pricing.html)
```

- Reason is required for rejections

---

## Strategy Commands

### `weblisk strategies list`

```bash
$ weblisk strategies list
ID         NAME                        PRIORITY  STATUS   PROGRESS
strat-001  Improve organic traffic     1         active   67%
strat-002  Reduce page load time       2         active   82%
strat-003  Fix compliance gaps         3         completed 100%
```

### `weblisk strategies create`

Interactive strategy creation.

```bash
$ weblisk strategies create
Name: Improve content quality
Objective: Increase average content score from 68 to 85
Target metric: content_score
Current value: 68
Goal value: 85
Deadline (YYYY-MM-DD): 2026-09-30
Priority (1-5): 2

✓ Created strategy strat-004: Improve content quality
```

- `--json` to accept strategy as JSON on stdin (for scripting)

### `weblisk strategies describe <id>`

```bash
$ weblisk strategies describe strat-001
Strategy: strat-001
Name:     Improve organic traffic
Status:   active
Priority: 1

Targets:
  METRIC            CURRENT  GOAL     PROGRESS  DEADLINE
  organic_sessions  14200    16800    67%       2026-09-30

Linked Observations: 120
Linked Recommendations: 38 (12 applied, 5 pending, 21 rejected)
```

---

## Federation Commands

### `weblisk federation peers`

```bash
$ weblisk federation peers
NAME           TIER      JURISDICTION  STATUS   CAPABILITIES      EXPIRES
partner-corp   partner   US            active   seo:audit         2026-07-15
acme-eu        private   EU            active   content:analyze   2026-06-20
```

### `weblisk federation pending`

```bash
$ weblisk federation pending
ID       FROM            CAPABILITIES REQUESTED     RECEIVED
req-001  supplier-inc    logistics:track             2026-04-25 09:00
```

### `weblisk federation accept <id>` / `weblisk federation reject <id>`

```bash
$ weblisk federation accept req-001
✓ Accepted peering request from supplier-inc
  Granted: logistics:track
  Tier: partner
  Expires: 2026-07-25
```

### `weblisk federation revoke <peer>`

```bash
$ weblisk federation revoke partner-corp
⚠ This will revoke all trust with 'partner-corp' and terminate active tasks.
  Type peer name to confirm: partner-corp
✓ Trust revoked for partner-corp.
```

---

## Audit Commands

### `weblisk audit`

Stream or query the audit log.

```bash
$ weblisk audit
TIME        ACTOR           ACTION      TARGET          DETAIL
10:30:01    orchestrator    task        seo-analyzer    Forwarded seo-audit task
10:30:00    alice           approve     rec-001         Accepted: Update title tag
10:25:12    orchestrator    task        content-analyzer Forwarded content-audit task
10:15:00    orchestrator    register    perf-auditor    Agent registered
```

- `--follow` to tail the log in real time (like `tail -f`)
- `--actor <name>` to filter by actor
- `--action <type>` to filter by action type
- `--since <duration>` to filter by time (e.g., `--since 1h`)
- `--limit <n>` to control results
- `--export <json|csv>` to export

---

## Configuration

The CLI reads orchestrator connection details from (in priority order):

1. Command-line flags: `--orch http://localhost:9800`
2. Environment variable: `WL_ORCH=http://localhost:9800`
3. Project config: `.weblisk/config.json` in the working directory
4. User config: `~/.weblisk/config.json`

### Config File

```json
{
  "orchestrator_url": "http://localhost:9800",
  "operator_name": "alice",
  "default_format": "table"
}
```

### Authentication Flow

Every command that calls the orchestrator:

```
1. Load operator private key from ~/.weblisk/keys/operator.key
2. Load token from ~/.weblisk/token
3. Check token expiry — if < 1 hour remaining, auto-refresh
4. Set Authorization: Bearer <token> on request
5. If 401 response → attempt token refresh → retry once
6. If refresh fails → print "Session expired. Run: weblisk operator register"
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid arguments, missing config) |
| 2 | Authentication error (no keys, expired token, rejected) |
| 3 | Connection error (orchestrator unreachable) |
| 4 | Not found (agent, workflow, strategy not found) |
| 5 | Permission denied (role insufficient) |

---

## Implementation Notes

- All commands share a common `AdminClient` that handles auth,
  connection, and response parsing
- Table output uses fixed-width columns aligned to terminal width
- `--json` output is one JSON object per line (for piping to `jq`)
- `--watch` mode uses `GET` polling at 5-second intervals (not
  WebSocket — keeps the CLI simple)
- Commands that accept multiple IDs (approvals) can also read from
  stdin for piping: `weblisk approvals list --json | jq -r '.[] | select(.priority == "critical") | .id' | weblisk approvals accept --stdin`

## Verification Checklist

### Project & Development
- [ ] `weblisk new` scaffolds a project from weblisk-templates with correct name replacement
- [ ] `weblisk new` always generates `.gitignore` with `.weblisk/secrets/`, `.weblisk/keys/`, `.weblisk/token`, `.env`, `.env.*`
- [ ] `weblisk new --template client/blog --template server/starter` merges both template sets
- [ ] `weblisk dev` starts a file-watching dev server with live reload for client projects
- [ ] `weblisk dev` builds and runs the hub with restart-on-change for server projects
- [ ] `weblisk build --minify --fingerprint` produces production-ready output
- [ ] `weblisk vendor` copies the Weblisk client framework to the specified directory
- [ ] Template resolution follows priority: local → WL_TEMPLATE_SOURCES → core
- [ ] `weblisk doctor` validates .gitignore contains required secret exclusion entries
- [ ] `weblisk doctor` validates .weblisk/secrets/ file permissions are 0600
- [ ] `weblisk doctor` cross-references secret declarations with stored values

### Secrets Management
- [ ] `weblisk secrets list` shows all declared secrets and their set/missing status
- [ ] `weblisk secrets set` prompts interactively for value (never passed as CLI argument)
- [ ] `weblisk secrets set` writes to `.weblisk/secrets/{agent}/{KEY}` with 0600 permissions
- [ ] `weblisk secrets get` requires --confirm flag and prints a terminal-sharing warning
- [ ] `weblisk secrets delete` removes the secret file
- [ ] `weblisk secrets rotate` triggers the rotation handler or prompts for new value

### Server & Code Generation
- [ ] `weblisk server init` reads YAML specs and dispatches to the configured LLM for code generation
- [ ] `weblisk server start` reads .weblisk/config.yaml and builds+starts all declared components
- [ ] `weblisk server verify` confirms orchestrator health and all registered components
- [ ] `weblisk agent create` generates agent code from agent.yaml spec via LLM dispatch
- [ ] `weblisk agent start` builds and runs a single agent with --orch and --port flags
- [ ] `weblisk agent list` lists all locally scaffolded agents
- [ ] `weblisk domain create` generates domain controller code from domain.yaml spec via LLM dispatch
- [ ] `weblisk domain start` builds and runs a single domain controller
- [ ] `weblisk gateway create` generates gateway code from hub configuration
- [ ] `weblisk gateway start` builds and runs the application gateway

### Blueprint Management
- [ ] `weblisk blueprints update` re-fetches all cached blueprint sources
- [ ] `weblisk validate` checks blueprint compliance (frontmatter, sections, types, deps)
- [ ] `weblisk pattern apply` reads pattern blueprint, dispatches to LLM with target context
- [ ] Blueprint resolution follows priority: local → WL_BLUEPRINT_SOURCES → core

### Identity & Operations
- [ ] `weblisk operator init` generates Ed25519 keys in ~/.weblisk/keys/ with 0700 directory and 0600 file permissions
- [ ] `weblisk operator init` prompts for passphrase (min 12 chars), encrypts private key with Argon2id + AES-256-GCM
- [ ] `weblisk operator init` passphrase cannot be skipped or supplied as CLI argument
- [ ] `weblisk operator init` does not overwrite existing keys without --force flag
- [ ] `weblisk operator register` signs the registration payload with the operator's private key and stores the returned token
- [ ] `weblisk operator token` auto-refreshes the token when less than 1 hour remaining before expiry
- [ ] `weblisk operator revoke` invalidates target operator's public key and tokens (admin only)
- [ ] `weblisk operator revoke` prevents self-revocation and revoking the last admin
- [ ] `weblisk operator list` shows all registered operators with name, role, status, and registration date
- [ ] All commands output human-readable tables by default and structured JSON with --json flag
- [ ] Destructive commands (agents deregister, federation revoke) require --confirm or interactive name-confirmation
- [ ] `weblisk approvals reject` requires a --reason argument for every rejection
- [ ] `weblisk status` calls GET /v1/admin/overview and displays agents, domains, workflows, approvals, federation, and health score
- [ ] Exit codes are 0=success, 1=general error, 2=auth error, 3=connection error, 4=not found, 5=permission denied
- [ ] Config resolution order: command-line flags > WL_ORCH env var > .weblisk/config.json (project) > ~/.weblisk/config.json (user)
- [ ] Commands fail fast with a clear message and non-zero exit code when the orchestrator is unreachable
- [ ] Authentication flow retries once on 401 by refreshing the token; prints re-register message if refresh also fails
