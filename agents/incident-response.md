<!-- blueprint
type: agent
kind: infrastructure
name: incident-response
version: 1.1.0
extends: [patterns/observability, patterns/storage, patterns/state-machine, patterns/messaging, patterns/notification, patterns/security, patterns/governance]
requires: [protocol/spec, protocol/types, architecture/agent, agents/alerting]
platform: any
tier: free
port: 9760
-->

# Incident Response Agent

Infrastructure agent that provides automated incident detection,
runbook execution, remediation steps, and post-incident reporting.
Works alongside the alerting agent — alerting handles notification
routing, incident-response handles what to do about it.

## Overview

The incident-response agent receives alert events and system health
signals, correlates them into incidents, executes predefined runbooks,
and tracks resolution. It bridges the gap between "something is wrong"
(alerting) and "here's how to fix it" (remediation).

This agent does NOT replace human operators for critical decisions.
It automates triage, executes safe remediation steps, and escalates
to operators when human judgment is required.

## Capabilities

`agent:message`, `storage:read`, `storage:write`

## HandleMessage Actions

| Action | Input | Output | Description |
|--------|-------|--------|-------------|
| process_alert | AlertEvent | IncidentAction | Receive alert, correlate, and determine response |
| execute_runbook | RunbookRequest | RunbookResult | Execute a specific runbook for an incident |
| get_incidents | IncidentQuery | IncidentList | Query active and resolved incidents |
| get_incident | {incident_id} | Incident | Get full incident details with timeline |
| acknowledge | {incident_id, operator} | Incident | Operator acknowledges incident |
| resolve | {incident_id, operator, resolution} | Incident | Operator resolves incident |
| escalate | {incident_id, reason} | Incident | Escalate incident to next tier |
| get_runbooks | {} | RunbookList | List available runbooks |

## Incident Lifecycle

```
DETECTED → TRIAGING → RUNBOOK_EXECUTING → AWAITING_OPERATOR → RESOLVED
                                        → AUTO_RESOLVED
                     → ESCALATED → AWAITING_OPERATOR → RESOLVED
```

| State | Description |
|-------|-------------|
| DETECTED | Alert received, incident created |
| TRIAGING | Correlating with other alerts and system state |
| RUNBOOK_EXECUTING | Automated runbook in progress |
| AUTO_RESOLVED | Runbook resolved the issue without human intervention |
| ESCALATED | Automated remediation insufficient, operator needed |
| AWAITING_OPERATOR | Waiting for human acknowledgment or action |
| RESOLVED | Incident closed by operator or auto-resolution confirmed |

## Alert Correlation

When an alert arrives, the agent correlates it with existing
incidents to avoid duplicate incident creation:

```
1. Hash alert (source + type + target)
2. Search active incidents for matching hash
3. If match found:
   a. Add alert to existing incident timeline
   b. Update severity if new alert is higher
   c. Skip runbook (already in progress)
4. If no match:
   a. Create new incident
   b. Look up matching runbook
   c. Begin triage
```

### Correlation Window

Alerts within a configurable window (default: 5 minutes) for the
same source and type are grouped into a single incident.

## Runbooks

Runbooks are predefined remediation procedures. Each runbook has
conditions (when to execute), steps (what to do), and escalation
criteria (when to give up and call a human).

### Runbook Structure

```yaml
runbook:
  name: agent-offline
  description: Remediate an offline agent
  trigger:
    alert_type: agent_offline
    severity: [critical, high]
  
  steps:
    - name: verify
      action: check_agent_health
      description: Confirm agent is actually offline (not a false alarm)
      timeout: 10
      on_success: next
      on_failure: escalate

    - name: check_dependencies
      action: check_agent_dependencies
      description: Verify storage, network, and upstream services
      timeout: 15
      on_success: next
      on_failure: escalate

    - name: restart
      action: request_agent_restart
      description: Request orchestrator to restart the agent
      timeout: 30
      requires_approval: false    # Safe automated action
      on_success: verify_recovery
      on_failure: escalate

    - name: verify_recovery
      action: check_agent_health
      description: Confirm agent recovered after restart
      timeout: 30
      retry: 3
      retry_delay: 10
      on_success: auto_resolve
      on_failure: escalate

  escalation:
    message: "Agent {agent_name} failed to recover after automated restart"
    severity: critical
    notify: [on-call, platform-admin]
```

### Built-in Runbooks

| Runbook | Trigger | Automated Steps | Escalation |
|---------|---------|----------------|------------|
| agent-offline | Agent unreachable | Health check → dependency check → restart request → verify | Agent won't recover |
| agent-degraded | Agent responding slowly | Health check → check load → check dependencies | Persistent degradation |
| workflow-failed | Domain workflow failure | Check agent status → check inputs → retry workflow | Repeated failures |
| site-unreachable | Uptime check failure | DNS check → TLS check → alternate path check | Confirmed outage |
| performance-regression | Performance threshold breach | Check recent deployments → check resource usage | Sustained regression |
| tls-expiring | TLS certificate <7 days | Check auto-renewal status → alert operator | <3 days remaining |
| federation-peer-down | Federation peer unreachable | Check peer health endpoint → check network → notify operator | Peer unresponsive |
| storage-failure | Storage write/read errors | Check disk space → check connections → failover check | Persistent errors |
| approval-backlog | Pending approvals exceed threshold | Notify approvers → escalate to admin | Backlog growing |

### Custom Runbooks

Operators can add custom runbooks via the admin gateway:

```
POST /v1/admin/runbooks
PUT /v1/admin/runbooks/:name
DELETE /v1/admin/runbooks/:name
GET /v1/admin/runbooks
GET /v1/admin/runbooks/:name
```

Custom runbooks follow the same YAML structure and can reference any
action the incident-response agent supports.

## Runbook Actions

Actions are the atomic operations a runbook step can perform:

| Action | Description | Approval Required |
|--------|-------------|------------------|
| check_agent_health | Query agent's /v1/health endpoint | No |
| check_agent_dependencies | Verify agent's required services | No |
| request_agent_restart | Ask orchestrator to restart an agent | No (safe) |
| check_dns | Resolve hostname and verify | No |
| check_tls | Verify TLS certificate status | No |
| retry_workflow | Re-dispatch a failed workflow | No |
| notify_operator | Send notification to operator | No |
| run_diagnostic | Execute diagnostic commands via CLI | No |
| request_failover | Request storage or service failover | Yes |
| request_rollback | Request deployment rollback | Yes |
| modify_rate_limits | Temporarily adjust rate limits | Yes |

Actions marked "Approval Required" pause the runbook and wait for
operator confirmation before proceeding.

## Incident Timeline

Every incident maintains a chronological timeline of events:

```json
{
  "incident_id": "inc_20260425_001",
  "severity": "critical",
  "state": "runbook_executing",
  "created_at": "2026-04-25T10:00:00Z",
  "source": {
    "alert_type": "agent_offline",
    "agent": "seo-analyzer",
    "domain": "seo"
  },
  "timeline": [
    {"time": "2026-04-25T10:00:00Z", "event": "incident_created", "detail": "Alert: seo-analyzer offline"},
    {"time": "2026-04-25T10:00:01Z", "event": "runbook_started", "detail": "Executing: agent-offline"},
    {"time": "2026-04-25T10:00:02Z", "event": "step_completed", "detail": "verify: confirmed offline"},
    {"time": "2026-04-25T10:00:05Z", "event": "step_completed", "detail": "check_dependencies: all healthy"},
    {"time": "2026-04-25T10:00:06Z", "event": "step_started", "detail": "restart: requesting restart"}
  ],
  "runbook": "agent-offline",
  "current_step": "restart",
  "alerts": ["alert_001", "alert_002"]
}
```

## Post-Incident Report

When an incident is resolved, the agent generates a post-incident
report:

```json
{
  "incident_id": "inc_20260425_001",
  "severity": "critical",
  "duration_seconds": 180,
  "root_cause": "Agent process crashed due to OOM",
  "resolution": "auto_resolved",
  "runbook_used": "agent-offline",
  "steps_executed": 4,
  "steps_succeeded": 4,
  "timeline_summary": "Detected → verified → dependencies OK → restarted → recovered",
  "recommendations": [
    "Increase agent memory limit",
    "Add memory usage alerting threshold"
  ]
}
```

Reports are stored and accessible via the admin gateway for trend
analysis and process improvement.

## Configuration

```yaml
incident_response:
  correlation_window: 300      # seconds — group related alerts
  auto_resolve_timeout: 600    # seconds — auto-close if stable after resolution
  max_runbook_duration: 300    # seconds — max time for a runbook to complete
  escalation_timeout: 900      # seconds — escalate if no operator response
  history_retention: 90        # days — keep resolved incidents
```

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| incident_total | counter | Incidents by severity, state, and runbook |
| incident_duration_seconds | histogram | Time from detection to resolution |
| incident_active | gauge | Currently active incidents by severity |
| runbook_execution_total | counter | Runbook executions by name and result |
| runbook_step_duration_seconds | histogram | Time per runbook step |
| runbook_auto_resolve_total | counter | Incidents auto-resolved without human |
| runbook_escalation_total | counter | Incidents escalated to operators |

## Error Handling

| Error | Handling |
|-------|---------|
| Runbook step fails | Move to on_failure path (usually escalate) |
| Runbook timeout | Cancel remaining steps, escalate to operator |
| Alerting agent unavailable | Queue notifications, retry when available |
| Storage unavailable | Continue operation in-memory, persist when storage recovers |
| Concurrent runbooks for same target | Queue second runbook, execute after first completes |

## Verification Checklist

- [ ] Agent registers with orchestrator and receives WLT token
- [ ] Alert events are received and correlated into incidents
- [ ] Duplicate alerts within correlation window join existing incidents
- [ ] Runbooks execute steps in sequence with correct timeout handling
- [ ] Failed steps follow on_failure path (next or escalate)
- [ ] Approval-required steps pause and wait for operator
- [ ] Auto-resolved incidents confirm stability before closing
- [ ] Post-incident reports generate for all resolved incidents
- [ ] Custom runbooks can be added via admin API
- [ ] Incident timeline records all events chronologically
- [ ] Metrics emit for incidents, runbooks, and escalations
- [ ] Graceful degradation when alerting agent or storage is unavailable

Port: 9760
