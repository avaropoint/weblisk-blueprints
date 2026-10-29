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
| **Examples** | Alerting, webhooks, email | Invoice processor, chat responder |
| **Deployed** | Once per hub | Per domain as needed |

## Agent Blueprints

| Blueprint | Purpose |
|-----------|---------|
| [workflow.md](workflow.md) | Workflow execution engine — DAG resolution, phase coordination. Superseded by [`architecture/execution`](../architecture/execution.md) and kept as the interim description |
| [task.md](task.md) | Task dispatch and tracking — priority queue, concurrency control. Superseded by [`architecture/execution`](../architecture/execution.md) and kept as the interim description |
| [lifecycle.md](lifecycle.md) | Continuous optimization — strategies, observations, approvals |
| [alerting.md](alerting.md) | Operational alert routing and delivery. Telling the people who hold a programme's positions is [`architecture/notification`](../architecture/notification.md)'s |
| [incident-response.md](incident-response.md) | Automated incident detection, runbooks, remediation |
| [health-monitor.md](health-monitor.md) | Retiring, and not what decides whether a component is live or present: liveness is the supervisor's, through [`GET /livez`](../protocol/spec.md#get-livez-and-get-readyz), and presence is the orchestrator's, through [leases](../architecture/orchestrator.md#presence) |
| [hub.md](hub.md) | Registry hub — indexing, search, metrics, verification |
| [sync.md](sync.md) | Background data sync (client ↔ server) |
| [cron.md](cron.md) | Scheduled task execution. Superseded by [`architecture/execution`](../architecture/execution.md) and kept as the interim description |
| [webhook.md](webhook.md) | Webhook processing (inbound + outbound) |
| [email-send.md](email-send.md) | Transactional email sending |

## Schema

All agent blueprints conform to [schemas/agent.md](../schemas/agent.md)
which defines 22 required sections. See [schemas/compliance.md](../schemas/compliance.md)
for validation and compliance levels.
