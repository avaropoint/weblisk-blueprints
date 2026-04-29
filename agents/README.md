# Infrastructure Agents

Infrastructure agents are system-level services that provide shared
capabilities to the hub. They are not domain-specific — they serve all
domains and work agents equally. Each blueprint in this directory
specifies a complete agent: its purpose, endpoints, events, storage,
configuration, and operational behavior.

## Relationship to Work Agents

| | Infrastructure Agents (this directory) | Work Agents (project-specific) |
|---|---|---|
| **Scope** | Hub-wide services | Domain-specific tasks |
| **Defined by** | These blueprints | Domain controller specs |
| **Examples** | Workflow engine, alerting, health | Invoice processor, chat responder |
| **Deployed** | Once per hub | Per domain as needed |

## Agent Blueprints

| Blueprint | Purpose |
|-----------|---------|
| [workflow.md](workflow.md) | Workflow execution engine — DAG resolution, phase coordination |
| [task.md](task.md) | Task dispatch and tracking — priority queue, concurrency control |
| [lifecycle.md](lifecycle.md) | Continuous optimization — strategies, observations, approvals |
| [alerting.md](alerting.md) | Notification routing and delivery |
| [incident-response.md](incident-response.md) | Automated incident detection, runbooks, remediation |
| [health-monitor.md](health-monitor.md) | Internal hub health — agent liveness, storage, gateway |
| [hub.md](hub.md) | Registry hub — indexing, search, metrics, verification |
| [sync.md](sync.md) | Background data sync (client ↔ server) |
| [cron.md](cron.md) | Scheduled task execution |
| [webhook.md](webhook.md) | Webhook processing (inbound + outbound) |
| [email-send.md](email-send.md) | Transactional email sending |

## Schema

All agent blueprints conform to [schemas/agent.md](../schemas/agent.md)
which defines 22 required sections. See [schemas/compliance.md](../schemas/compliance.md)
for validation and compliance levels.
