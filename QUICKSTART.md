# Quickstart Guide

Get a Weblisk hub running from scratch — one orchestrator, one domain
controller, one work agent, and the infrastructure to support them.

## Prerequisites

- Go 1.22+, Node.js 20+, or a Cloudflare Workers account
- [weblisk-cli](https://github.com/avaropoint/weblisk-cli) installed
- A terminal

## 1. Install the CLI

```bash
# macOS / Linux
curl -fsSL https://weblisk.dev/install.sh | sh

# Or via Go
go install github.com/avaropoint/weblisk-cli@latest

# Verify installation
weblisk version
```

The CLI automatically clones the blueprints repository on first use.

## 2. Initialize a Project

```bash
mkdir my-hub && cd my-hub
weblisk server init --platform go
```

This creates:

```
my-hub/
  .weblisk/
    keys/              # Ed25519 keys (generated on first run)
    config.yaml        # Hub configuration
  cmd/
    orchestrator/      # Orchestrator entry point
  internal/
    protocol/          # Protocol implementation
    storage/           # Storage interface (SQLite)
  go.mod
  go.sum
```

For Node.js: `weblisk server init --platform node`
For Cloudflare: `weblisk server init --platform cloudflare`

## 3. Start the Orchestrator

```bash
weblisk server start
```

The orchestrator starts on port 9800 and waits for agents to register.

```
[INFO] Orchestrator started on :9800
[INFO] Identity: generated new Ed25519 key pair
[INFO] Storage: SQLite initialized at .weblisk/data/orchestrator.db
[INFO] Waiting for agent registrations...
```

Verify it's running:

```bash
curl http://localhost:9800/v1/health
# {"status": "ok", "agents": 0, "domains": 0}
```

## 4. Create a Domain Controller

Pick a domain. We'll use the SEO domain as an example:

```bash
weblisk domain create seo --platform go
```

This generates a domain controller with the following structure:

```
internal/
  domains/
    seo/
      controller.go    # Domain controller with workflow execution
      workflows.go     # seo-audit, seo-optimize workflow definitions
      scoring.go       # Aggregation rules and scoring formula
```

Start the domain:

```bash
weblisk domain start seo
```

```
[INFO] SEO domain controller started on :9700
[INFO] Registered with orchestrator (status: degraded)
[INFO] Missing required agents: [seo-analyzer, a11y-checker]
```

The domain registers but starts in **degraded** status because its
required work agents aren't running yet.

## 5. Create Work Agents

```bash
weblisk agent create seo-analyzer --platform go
weblisk agent create a11y-checker --platform go
```

Start the agents:

```bash
weblisk agent start seo-analyzer
weblisk agent start a11y-checker
```

```
[INFO] seo-analyzer started on :9710, registered with orchestrator
[INFO] a11y-checker started on :9711, registered with orchestrator
[INFO] SEO domain status updated: degraded → online
```

Once all required agents register, the domain transitions to **online**.

## 6. Create Infrastructure Agents

Infrastructure agents provide system-level services. Start with the
essentials:

```bash
weblisk agent create alerting --platform go
weblisk agent create cron --platform go
```

```bash
weblisk agent start alerting
weblisk agent start cron
```

These enable notification routing and scheduled task execution for
all domains.

## 7. Add the Application Gateway

```bash
weblisk gateway create --platform go
```

```bash
weblisk gateway start
```

```
[INFO] Application gateway started on :8080
[INFO] Routes loaded: 12 endpoints across 1 domain
[INFO] ABAC policies: default (allow authenticated)
[INFO] Rate limiting: enabled (100 req/min per IP)
```

The gateway is now the entry point for end users. It handles TLS
termination, session management, ABAC authorization, and rate
limiting.

## 8. Run a Workflow

Trigger an SEO audit through the gateway:

```bash
curl -X POST http://localhost:8080/v1/domains/seo/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{
    "action": "audit",
    "payload": {
      "files": ["index.html", "about.html"]
    }
  }'
```

Response:

```json
{
  "task_id": "task-a1b2c3d4",
  "status": "accepted",
  "workflow": "seo-audit",
  "phases": ["scan", "analyze", "accessibility", "report"]
}
```

Check the result:

```bash
curl http://localhost:8080/v1/tasks/task-a1b2c3d4 \
  -H "Authorization: Bearer <your-token>"
```

## 9. Check System Status

```bash
# CLI status
weblisk status

# Output:
# Orchestrator:  online (port 9800)
# Gateway:       online (port 8080)
# Domains:
#   seo          online (2/2 agents)
# Agents:
#   seo-analyzer work       online (port 9710)
#   a11y-checker work       online (port 9711)
#   alerting     infra      online (port 9752)
#   cron         infra      online (port 9750)
```

## 10. Explore and Extend

### Add more domains

```bash
weblisk domain create content --platform go
weblisk agent create content-analyzer --platform go
weblisk agent create meta-checker --platform go
```

### Add patterns

```bash
# Add REST API endpoints
weblisk pattern apply api-rest --resource posts

# Add authentication
weblisk pattern apply auth-session

# Add user management
weblisk pattern apply user-management
```

### Use custom blueprints

```bash
# Add a custom blueprint source
echo 'WL_BLUEPRINT_SOURCES=https://github.com/your-org/your-blueprints.git' >> .env

# Create a domain from your custom blueprints
weblisk domain create checkout --platform go
```

### Enable federation

```bash
# Initialize federation
weblisk federation init

# Connect to a peer hub
weblisk federation peer add https://partner-hub.example.com
```

---

## What's Running

After completing this quickstart, you have:

```
┌─────────────────────────────────────────────┐
│                 Your Hub                     │
│                                              │
│  Gateway (:8080)                            │
│    ├── TLS, sessions, ABAC, rate limiting   │
│    └── Routes → domains                     │
│                                              │
│  Orchestrator (:9800)                       │
│    ├── Agent registry                       │
│    ├── Task routing                         │
│    └── Security (Ed25519, tokens)           │
│                                              │
│  SEO Domain (:9700)                         │
│    ├── seo-analyzer (:9710)                 │
│    └── a11y-checker (:9711)                 │
│                                              │
│  Infrastructure                              │
│    ├── cron (:9750)                         │
│    └── alerting (:9752)                     │
└─────────────────────────────────────────────┘
```

## Next Steps

- Read the [Architecture Overview](architecture/orchestrator.md) to
  understand how components interact
- Review the [Domain Controller Architecture](architecture/domain.md)
  to build custom domains
- Explore the [hello-world template](examples/templates/hello-world.md)
  for a complete working example
- Set up the [Admin Gateway](architecture/admin.md) for production
  operations
- Review the [Threat Model](architecture/threat-model.md) before
  deploying to production
- Configure [Observability](architecture/observability.md) for
  logging, tracing, and metrics
