<!-- blueprint
type: architecture
name: cli
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/orchestrator, architecture/admin, patterns/command]
platform: any
tier: free
-->

# Weblisk CLI

Specification for CLI commands that interrogate and manage a running
Weblisk server. These commands extend the `weblisk-cli` beyond
scaffolding and code generation into operational management — giving
developers and operators direct terminal access to their deployment.

## Overview

The CLI operations commands communicate with the orchestrator's admin
API endpoints using the operator's Ed25519 identity for authentication.
Every command that reads or modifies the system requires a valid
operator identity stored in `~/.weblisk/keys/`.

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
          methods: [GET]
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
          methods: [GET]
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

---

## Interfaces

The CLI’s public interface is the set of terminal commands documented in
the sections below: [Identity Commands](#identity-commands),
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

## Identity Commands

### `weblisk operator init`

Generate an operator Ed25519 key pair.

```bash
$ weblisk operator init
Generated operator key pair:
  Private: ~/.weblisk/keys/operator.key
  Public:  ~/.weblisk/keys/operator.pub
  Key ID:  a1b2c3d4e5f6...

Keep your private key safe. It is your identity.
```

- Generates keys in `~/.weblisk/keys/` (mode 0700 directory, 0600 key)
- If keys already exist, prints the public key and exits (no overwrite)
- `--force` to regenerate (prints warning about identity change)
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

- [ ] `weblisk operator init` generates Ed25519 keys in ~/.weblisk/keys/ with 0700 directory and 0600 file permissions
- [ ] `weblisk operator init` does not overwrite existing keys without --force flag
- [ ] `weblisk operator register` signs the registration payload with the operator's private key and stores the returned token
- [ ] `weblisk operator token` auto-refreshes the token when less than 1 hour remaining before expiry
- [ ] All commands output human-readable tables by default and structured JSON with --json flag
- [ ] Destructive commands (agents deregister, federation revoke) require --confirm or interactive name-confirmation
- [ ] `weblisk approvals reject` requires a --reason argument for every rejection
- [ ] `weblisk status` calls GET /v1/admin/overview and displays agents, domains, workflows, approvals, federation, and health score
- [ ] Exit codes are 0=success, 1=general error, 2=auth error, 3=connection error, 4=not found, 5=permission denied
- [ ] Config resolution order: command-line flags > WL_ORCH env var > .weblisk/config.json (project) > ~/.weblisk/config.json (user)
- [ ] Commands fail fast with a clear message and non-zero exit code when the orchestrator is unreachable
- [ ] Authentication flow retries once on 401 by refreshing the token; prints re-register message if refresh also fails
