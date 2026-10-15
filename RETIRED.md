# Retired spellings

The names the corpus has stopped using, each listed once. A row gives the
retired spelling, the spelling that replaces it, and the section that retired
it. Where the retired spelling may still appear is the row's entry under
[Entries](#entries), which a tool reads; anywhere else in the corpus it is a
leftover to fix.

A row and its entry are added together, by the change that retires the
spelling, and a place in an entry's `allow` is taken out by the change that
rewrites that place.

| Retired | Replaced by | Retired by |
|---|---|---|
| `replica`, in any case and inside any name, for a copy of a content repository the content service keeps at a second place | `remote` | [`architecture/content`](architecture/content.md#remotes) 3.0.0, Remotes |
| `replicas`, in any case, the operation `Replicas` among them | `remotes`; the operation `Remotes` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints |
| `ContentReplica` | `ContentRemote` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types |
| `ReplicaCensus` | `RemoteCensus` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types |
| `ReplicaDeclaration` | `RemoteDeclaration` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types |
| `ReplicaEstablishment` | `RemoteEstablishment` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types |
| `DeclareReplica` | `DeclareRemote` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints and Interfaces |
| `ListReplicas` | `ListRemotes` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces |
| `RetireReplica` | `RetireRemote` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints and Interfaces |
| `/v1/content/repositories/{repository}/replicas` | `/v1/content/repositories/{repository}/remotes` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints |
| `/v1/content/repositories/{repository}/replicas/{replica}` | `/v1/content/repositories/{repository}/remotes/{remote}` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints |
| `CONTENT_REPLICA_UNSEEN` | `CONTENT_REMOTE_UNSEEN` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling |
| `CONTENT_REPLICA_EXISTS` | `CONTENT_REMOTE_EXISTS` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling |
| `CONTENT_REPLICA_UNKNOWN` | `CONTENT_REMOTE_UNKNOWN` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling |
| `CONTENT_REPLICA_UNSUPPORTED` | `CONTENT_REMOTE_UNSUPPORTED` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling |
| `replica_retry_interval`, the key `content.replica_retry_interval` | `remote_retry_interval`, the key `content.remote_retry_interval` | [`architecture/content`](architecture/content.md#configuration) 3.0.0, Configuration, and [`schemas/config`](schemas/config.md#content) |
| `content.replica_declared` | `content.remote_declared` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces |
| `content.replica_state` | `content.remote_state` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces |
| `content.replica_retired` | `content.remote_retired` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces |
| `Replica Sender` | `Remote Sender` | [`architecture/content`](architecture/content.md#architecture) 3.0.0, Architecture |
| `architecture/content.md#replicas` | `architecture/content.md#remotes` | [`architecture/content`](architecture/content.md#remotes) 3.0.0, Remotes |
| `architecture/content.md#replica-declaration-flow` | `architecture/content.md#remote-declaration-flow` | [`architecture/content`](architecture/content.md#remote-declaration-flow) 3.0.0, Remote Declaration Flow |
| `architecture/content.md#replica-send-flow` | `architecture/content.md#remote-send-flow` | [`architecture/content`](architecture/content.md#remote-send-flow) 3.0.0, Remote Send Flow |
| `architecture/content.md#a-replica-is-sent-to-and-never-read-from` | `architecture/content.md#a-remote-is-sent-to-and-never-read-from` | [`architecture/content`](architecture/content.md#a-remote-is-sent-to-and-never-read-from) 3.0.0, A remote is sent to, and never read from |
| `architecture/content.md#declaring-a-replica` | `architecture/content.md#declaring-a-remote` | [`architecture/content`](architecture/content.md#declaring-a-remote) 3.0.0, Declaring a remote |
| `architecture/content.md#who-may-declare-a-replica` | `architecture/content.md#who-may-declare-a-remote` | [`architecture/content`](architecture/content.md#who-may-declare-a-remote) 3.0.0, Who may declare a remote |
| `architecture/content.md#retiring-a-replica` | `architecture/content.md#retiring-a-remote` | [`architecture/content`](architecture/content.md#retiring-a-remote) 3.0.0, Retiring a remote |
| `GitReplicaCensusReport` | `GitRemoteCensusReport` | [`patterns/content-git`](patterns/content-git.md#types) 2.0.0, Types |
| `GitReplicaReport` | `GitRemoteReport` | [`patterns/content-git`](patterns/content-git.md#types) 2.0.0, Types |
| `git-replica-send` | `git-remote-send` | [`patterns/content-git`](patterns/content-git.md#contracts) 2.0.0, Contracts |
| `git-replica-census` | `git-remote-census` | [`patterns/content-git`](patterns/content-git.md#contracts) 2.0.0, Contracts |
| `remote` as a kind of `GitFinding`, for a remote configured in a store's own git configuration | `undeclared-remote` | [`patterns/content-git`](patterns/content-git.md#control-state) 2.0.0, Control State |
| `{hub_id, name, timestamp}`, as the payload an attestation-token request signs | `{hub_id, jti, name, timestamp}` | [`architecture/admin`](architecture/admin.md#contracts) 3.0.0, `attestation-token-issuance` |
| `X-Trace-Id`, the HTTP header | `traceparent` (W3C Trace Context), and an envelope's `trace_id` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation |
| `X-Span-Id`, the HTTP header | `traceparent`, and an envelope's `span_id` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation |
| `X-Parent-Span-Id`, the HTTP header | `traceparent` read by the receiver, whose span records it as `parent_span_id` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation |
| `protocol/spec.md#trace-id-propagation` | `protocol/spec.md#trace-propagation` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation |
| `lifecycle.startup`, `lifecycle.ready`, `lifecycle.shutdown`, `lifecycle.stopped`, `lifecycle.health_change`, `lifecycle.version_updated`, `lifecycle.version_rollback`, `lifecycle.version_retired`, `lifecycle.restored`, as log types | `process.startup`, `process.ready`, `process.shutdown`, `process.stopped`, `process.health_change`, `process.version_updated`, `process.version_rollback`, `process.version_retired`, `process.restored` | [`patterns/logging`](patterns/logging.md#log-types) 2.0.0, Log Types |
| `task.received`, `task.completed`, `task.failed`, as log types | `execute.received`, `execute.completed`, `execute.failed` | [`patterns/logging`](patterns/logging.md#log-types) 2.0.0, Log Types |
| `trace_id`, as a field of the `task.submit` payload (`TaskSubmission`) | the event envelope's `trace_id` and `span_id` | [`patterns/task-dispatch`](patterns/task-dispatch.md#types) 2.0.0, Types |
| `log_format`, the key `observability.log_format`, and the `text` log format | nothing: records are JSON lines, and a tool renders them | [`patterns/logging`](patterns/logging.md#log-levels) 2.0.0, Log Levels, and [`schemas/config`](schemas/config.md) |
| `Log output`, a log written to `stderr` or a file of the component's own | standard output, and OTLP where telemetry is deployed | [`patterns/logging`](patterns/logging.md#overview) 2.0.0, Overview and Log Rotation |
| `log-rotation`, as a behaviour of `patterns/logging`, its `rotation` configuration (`max_size`, `max_files`), and `log-envelope` as a behaviour name | nothing for rotation, which is the runtime's that captures standard output; `structured-logging` and `trace-correlation` for the envelope | [`patterns/logging`](patterns/logging.md#log-rotation) 2.0.0, Log Rotation |
| `logging.level` and `logging.level_overrides`, as log level configuration | `observability.log_level` | [`schemas/config`](schemas/config.md) and [`patterns/logging`](patterns/logging.md#level-configuration) 2.0.0, Level Configuration |
| `fatal`, as a log level | `error` | [`protocol/types`](protocol/types.md#logentry) 3.0.0, LogEntry |
| `app` and `access`, as `log_type` values | a type from [`patterns/logging`](patterns/logging.md#log-types)'s Log Types | [`protocol/types`](protocol/types.md#logentry) 3.0.0, LogEntry |
| `start_time`, `end_time`, `duration_ms` and `events`, as fields of a span | `start` and `end`; nothing for `duration_ms`, which is `end` minus `start`, or for `events` | [`protocol/types`](protocol/types.md#span) 3.0.0, Span |
| `"type": "span"`, marking a span written as a log line | `log_type` `span` | [`architecture/observability`](architecture/observability.md#trace-export) 2.0.0, Trace Export |
| `<component>.<operation>`, as the form of a span name | a name for what was done, from Span Names, with `component` saying who | [`architecture/observability`](architecture/observability.md#span-names) 2.0.0, Span Names |
| A log line's `ts` as Unix epoch seconds, and its `timestamp` field | `ts` as an RFC 3339 UTC time with milliseconds | [`protocol/types`](protocol/types.md#logentry) 3.0.0, LogEntry |
| `Owns`, the type [`architecture/observability`](architecture/observability.md) declared for a log line's required fields | [`LogEntry`](protocol/types.md#logentry) | [`architecture/observability`](architecture/observability.md#structured-logging) 2.0.0, Structured Logging |
| `security.auth_success`, `security.auth_failure`, `security.permission_denied`, `security.override`, as log types | `auth.success`, `auth.failure`, `auth.denied`, `auth.override` | [`patterns/logging`](patterns/logging.md#log-types) 2.0.0, Log Types |
| `security.secret_accessed`, `security.secret_missing`, `security.secret_rotated`, `security.secret_denied`, `security.secret_expired`, as log types | `secrets.accessed`, `secrets.missing`, `secrets.rotated`, `secrets.denied`, `secrets.expired` | [`patterns/secrets`](patterns/secrets.md#audit-trail) 2.0.0, Audit Trail |
| `security.key_decrypt_failed`, as a log type | `identity.key_decrypt_failed` | [`protocol/identity`](protocol/identity.md#key-categories) 2.0.0, Key Categories |
| `trace_id`, as a field of `ChatRequest` and `ChatResponse` | `traceparent` on the request ([`protocol/spec`](protocol/spec.md#trace-propagation)) | [`patterns/api-ai`](patterns/api-ai.md#types) 3.0.0, Types |
| `blueprint_sources`, in lower case, as a configuration key naming blueprint sources | `WL_BLUEPRINT_SOURCES`, the environment variable, comma-separated | [`architecture/cli`](architecture/cli.md#where-blueprints-come-from) 2.20.0, Where blueprints come from |
| `<address>@<ref>`, a blueprint source pinned to a branch or tag by a ref after `@`, as in `https://github.com/org/repo.git@v2.0` | Nothing: an entry is given whole to `git clone`, and a source is read at its `HEAD` | [`architecture/cli`](architecture/cli.md#where-blueprints-come-from) 2.20.0, Where blueprints come from |
| `telemetry:collect`, a name the design inputs used for the capability a component's signals reach telemetry under. No blueprint ever carried it, and it is listed so that none adopts it | `telemetry:push`, under which a component pushes its own signals | [`protocol/types`](protocol/types.md#capability) 2.0.0, Capability |
| `/v1/health`, served `POST` by an agent and `GET` by the orchestrator | `GET /livez` (liveness) and `GET /readyz` (readiness), served by every component outside `/v1`; a registered component's presence is the lease it renews at `POST /v1/lease` | [`protocol/types`](protocol/types.md#health) 3.0.0, Health and Protocol Paths; [`protocol/spec`](protocol/spec.md#get-livez-and-get-readyz) 3.0.0 |
| `GET /health`, the gateway's, a deployment platform's and observability's health route | `GET /livez` and `GET /readyz` | [`architecture/gateway`](architecture/gateway.md#interfaces) 2.0.0; [`patterns/deployment`](patterns/deployment.md#health-checks) 2.0.0; [`architecture/observability`](architecture/observability.md#health-endpoint) 2.0.0 |
| `/api/health`, the dev server's health route | `GET /livez` | [`patterns/development`](patterns/development.md#liveness) 2.0.0 |
| `HealthStatus` | `Liveness`, `Readiness` and, for what a component reports of itself to the orchestrator, `LeaseRenewal` | [`protocol/types`](protocol/types.md#health) 3.0.0, Health |
| `Health`, the operation of the health route | `Livez` and `Readyz` | [`protocol/types`](protocol/types.md#protocol-paths) 3.0.0, Protocol Paths, and every `## Endpoints` table that served it |
| `online`, `offline` and `degraded`, as a component's health or presence state | `ready`, `not_ready` and `unknown`, the lease states | [`protocol/types`](protocol/types.md#leasestate) 3.0.0, LeaseState |
| `healthy`, `degraded` and `unhealthy`, as a health status and as the keys of an agent's `health:` block | `ready` and `not_ready`; `degraded` has no successor state: a component that still serves, short of something, is `ready`, and its lease's `checks` name the subsystem `not_ready` | [`protocol/types`](protocol/types.md#health) 3.0.0; [`schemas/agent`](schemas/agent.md#health) |
| `status` on `ServiceEntry` | `lease_state` and `lease_expires_at` | [`protocol/types`](protocol/types.md#serviceentry) 3.0.0, ServiceEntry |
| `status` on `AgentEntry` | `lease` and `last_renewal` | [`architecture/orchestrator`](architecture/orchestrator.md#agententry) 3.0.0, AgentEntry |
| `last_health_check` on `AgentState` | `lease_expires_at` | [`architecture/agent`](architecture/agent.md#agentstate) 2.0.0, AgentState |
| `health` on `AgentEndpoints` | `livez` and `readyz` | [`architecture/agent`](architecture/agent.md#agentendpoints) 2.0.0, AgentEndpoints |
| `health_interval`, `health_timeout` and `health_failures`, the keys `orchestrator.health_*`; and `health_timeout_seconds`, the orchestrator timeout key of Task Execution Timeouts | `lease_duration`, the key `orchestrator.lease_duration`; nothing replaces the timeout or the failure count, since nothing probes | [`schemas/config`](schemas/config.md#orchestrator); [`architecture/orchestrator`](architecture/orchestrator.md#configuration) 3.0.0, Configuration; [`protocol/spec`](protocol/spec.md#task-execution-timeouts) 3.0.0, Task Execution Timeouts |
| `online`, `degraded` and `offline`, the members of the overview's `agents` | `ready`, `not_ready` and `unknown` | [`architecture/admin`](architecture/admin.md#get-v1adminoverview) 3.0.0, GET /v1/admin/overview |
| `state-tracking`, `ComponentState` and `component.state_change`, a component state machine and its event | nothing: a component's state is its lease state | [`patterns/observability`](patterns/observability.md#component-state-machine) 2.0.0, Contracts and Component State Machine |
| `Response`, the health response type of `patterns/observability`, with `uptime_seconds` and `metrics_snapshot` | `Liveness` and `Readiness` | [`patterns/observability`](patterns/observability.md#health-endpoint) 2.0.0, Health Endpoint |
| `agent_state`, the gauge | `agent_ready` | [`patterns/observability`](patterns/observability.md#agent-metrics) 2.0.0, Base Metrics |
| `health.probe`, the span of a health probe, with `target` and `result` | `lease.renew`, the span of a lease renewal: nothing probes another component | [`architecture/observability`](architecture/observability.md#span-names) 2.0.0, Span Names |
| `framework_healthy` | `framework_ready` | [`patterns/interop`](patterns/interop.md#contracts) 2.0.0, Contracts |
| `agent-offline`, the runbook, and `agent_offline`, its alert type | `agent-lease-lapsed` and `agent_lease_lapsed` | [`agents/incident-response`](agents/incident-response.md#built-in-runbooks) 2.0.0, Built-in Runbooks |
| `agent-degraded`, the runbook | `agent-not-ready` | [`agents/incident-response`](agents/incident-response.md#built-in-runbooks) 2.0.0, Built-in Runbooks |
| `check_agent_health`, the runbook action | `check_agent_lease` | [`agents/incident-response`](agents/incident-response.md#runbook-actions) 2.0.0, Runbook Actions |
| `--status <online\|degraded\|offline>`, the filter of `weblisk agents list` | `--lease <ready\|not_ready\|unknown>` | [`architecture/cli`](architecture/cli.md#weblisk-agents-list) 3.0.0 |

## Entries

One entry per row of the table above, in the same order. An entry says how a
tool finds each retired spelling and where it may still appear; this file
itself is always allowed.

- `retired`: each spelling the row retires, exactly as written, with its
  `match`:
  - `exact`: the spelling as written, not inside a longer name;
  - `any-case`: in any case, and inside any longer name;
  - `sense`: the spelling is current in another sense, and only its stated
    sense is retired. No text search can tell the two apart, so a tool reads
    the place the row names under *Retired by*.
- `allow`: a file where the spelling may still appear, and `why`. An allowance
  that ends carries `until`, a citation ([`schemas/names`](schemas/names.md#the-grammar)):
  once the file it names reaches that version, the allowance no longer holds.
  An allowance in a file that has no version yet cites the first one, `1.0.0`.
- `other_senses`: where the same spelling means something else and is kept:
  a `path`, a `pattern` (a regular expression whose matches are kept), or
  neither, and the `sense` in words.

[`checks/retired.py`](checks/retired.py) reads the entries as a tool does.

```yaml
- retired:
  - {spelling: replica, match: any-case}
  other_senses: &replica-senses
  - {pattern: 'content:replicate', sense: 'the capability content:replicate, which is kept, wherever it is named'}
  - {path: schemas/config.md, sense: an instance count}
  - {path: architecture/cli.md, sense: an instance count}
  - {path: patterns/scheduling.md, sense: a scheduler's replicas}
  - {path: protocol/secret-source.md, sense: a state's backups and replicas}
  - {path: patterns/migration.md, sense: a production replica}
  - {path: architecture/gateway.md, sense: a route to a replica}
  - {path: platforms/cloudflare.md, sense: replication}
  - {path: patterns/deployment.md, sense: replication}
- retired:
  - {spelling: replicas, match: any-case}
  - {spelling: Replicas, match: exact}
  other_senses: *replica-senses
- retired:
  - {spelling: ContentReplica, match: exact}
- retired:
  - {spelling: ReplicaCensus, match: exact}
- retired:
  - {spelling: ReplicaDeclaration, match: exact}
- retired:
  - {spelling: ReplicaEstablishment, match: exact}
- retired:
  - {spelling: DeclareReplica, match: exact}
- retired:
  - {spelling: ListReplicas, match: exact}
- retired:
  - {spelling: RetireReplica, match: exact}
- retired:
  - {spelling: '/v1/content/repositories/{repository}/replicas', match: exact}
- retired:
  - {spelling: '/v1/content/repositories/{repository}/replicas/{replica}', match: exact}
- retired:
  - {spelling: CONTENT_REPLICA_UNSEEN, match: exact}
- retired:
  - {spelling: CONTENT_REPLICA_EXISTS, match: exact}
- retired:
  - {spelling: CONTENT_REPLICA_UNKNOWN, match: exact}
- retired:
  - {spelling: CONTENT_REPLICA_UNSUPPORTED, match: exact}
- retired:
  - {spelling: replica_retry_interval, match: exact}
  - {spelling: content.replica_retry_interval, match: exact}
- retired:
  - {spelling: content.replica_declared, match: exact}
- retired:
  - {spelling: content.replica_state, match: exact}
- retired:
  - {spelling: content.replica_retired, match: exact}
- retired:
  - {spelling: Replica Sender, match: exact}
- retired:
  - {spelling: architecture/content.md#replicas, match: exact}
- retired:
  - {spelling: architecture/content.md#replica-declaration-flow, match: exact}
- retired:
  - {spelling: architecture/content.md#replica-send-flow, match: exact}
- retired:
  - {spelling: architecture/content.md#a-replica-is-sent-to-and-never-read-from, match: exact}
- retired:
  - {spelling: architecture/content.md#declaring-a-replica, match: exact}
- retired:
  - {spelling: architecture/content.md#who-may-declare-a-replica, match: exact}
- retired:
  - {spelling: architecture/content.md#retiring-a-replica, match: exact}
- retired:
  - {spelling: GitReplicaCensusReport, match: exact}
- retired:
  - {spelling: GitReplicaReport, match: exact}
- retired:
  - {spelling: git-replica-send, match: exact}
- retired:
  - {spelling: git-replica-census, match: exact}
- retired:
  - {spelling: remote, match: sense}
  other_senses:
  - {sense: 'everywhere else, where remote is a current word: the content service''s remote, which replaced replica, and git''s own, as in a configured remote, ls-remote and the git-remote driver'}
- retired:
  - {spelling: '{hub_id, name, timestamp}', match: exact}
  allow:
  - {path: architecture/admin.md, why: a Verification Checklist row that names it as a form refused or never signed}
  - {path: architecture/cli.md, why: a Verification Checklist row that names it as a form refused or never signed}
- retired:
  - {spelling: X-Trace-Id, match: exact}
- retired:
  - {spelling: X-Span-Id, match: exact}
- retired:
  - {spelling: X-Parent-Span-Id, match: exact}
- retired:
  - {spelling: protocol/spec.md#trace-id-propagation, match: exact}
- retired:
  - {spelling: lifecycle.startup, match: sense}
  - {spelling: lifecycle.ready, match: sense}
  - {spelling: lifecycle.shutdown, match: sense}
  - {spelling: lifecycle.stopped, match: sense}
  - {spelling: lifecycle.health_change, match: sense}
  - {spelling: lifecycle.version_updated, match: sense}
  - {spelling: lifecycle.version_rollback, match: sense}
  - {spelling: lifecycle.version_retired, match: sense}
  - {spelling: lifecycle.restored, match: sense}
  other_senses:
  - {sense: 'the event topics of the lifecycle agent''s event namespace, which are events and not log types (lifecycle.version_rollback in patterns/versioning among them)'}
- retired:
  - {spelling: task.received, match: sense}
  - {spelling: task.completed, match: sense}
  - {spelling: task.failed, match: sense}
  other_senses:
  - {sense: 'the event topics of the task agent''s event namespace, which keep these names as events'}
- retired:
  - {spelling: trace_id, match: sense}
- retired:
  - {spelling: log_format, match: exact}
  - {spelling: observability.log_format, match: exact}
  - {spelling: text, match: sense}
- retired:
  - {spelling: Log output, match: sense}
- retired:
  - {spelling: log-rotation, match: exact}
  - {spelling: rotation, match: sense}
  - {spelling: max_size, match: sense}
  - {spelling: max_files, match: sense}
  - {spelling: log-envelope, match: exact}
- retired:
  - {spelling: logging.level, match: exact}
  - {spelling: logging.level_overrides, match: exact}
- retired:
  - {spelling: fatal, match: sense}
- retired:
  - {spelling: app, match: sense}
  - {spelling: access, match: sense}
- retired:
  - {spelling: start_time, match: exact}
  - {spelling: end_time, match: exact}
  - {spelling: duration_ms, match: sense}
  - {spelling: events, match: sense}
  other_senses:
  - {sense: 'duration_ms as a field of LogEntry, wherever it is one'}
  - {sense: 'OpenTelemetry''s own start_time_unix_nano and end_time_unix_nano, which are longer names'}
- retired:
  - {spelling: '"type": "span"', match: exact}
- retired:
  - {spelling: <component>.<operation>, match: exact}
- retired:
  - {spelling: ts, match: sense}
  - {spelling: timestamp, match: sense}
- retired:
  - {spelling: Owns, match: sense}
- retired:
  - {spelling: security.auth_success, match: exact}
  - {spelling: security.auth_failure, match: exact}
  - {spelling: security.permission_denied, match: exact}
  - {spelling: security.override, match: exact}
- retired:
  - {spelling: security.secret_accessed, match: exact}
  - {spelling: security.secret_missing, match: exact}
  - {spelling: security.secret_rotated, match: exact}
  - {spelling: security.secret_denied, match: exact}
  - {spelling: security.secret_expired, match: exact}
  other_senses:
  - {path: patterns/secrets.md, sense: 'the event topics of patterns/secrets, which are not log types'}
- retired:
  - {spelling: security.key_decrypt_failed, match: exact}
- retired:
  - {spelling: trace_id, match: sense}
- retired:
  - {spelling: blueprint_sources, match: exact}
- retired:
  - {spelling: <address>@<ref>, match: exact}
  other_senses:
  - {sense: 'an address''s own @, as in the SSH form git@github.com:org/repo.git, which is no ref and is not retired'}
- retired:
  - {spelling: 'telemetry:collect', match: exact}
- retired:
  - {spelling: /v1/health, match: exact}
  allow:
  - {path: skills/hubs/SKILL.md, why: until skills/ is next revised, until: skills/hubs/SKILL@1.0.0}
- retired:
  - {spelling: GET /health, match: exact}
- retired:
  - {spelling: /api/health, match: exact}
- retired:
  - {spelling: HealthStatus, match: exact}
  allow:
  - {path: skills/rust/SKILL.md, why: until skills/ is next revised, until: skills/rust/SKILL@1.0.0}
  - {path: UNBOUND_BINDINGS.md, why: a record of a past measurement}
- retired:
  - {spelling: Health, match: sense}
- retired:
  - {spelling: online, match: sense}
  - {spelling: offline, match: sense}
  - {spelling: degraded, match: sense}
  allow:
  - {path: agents/health-monitor.md, why: it retires whole, until: agents/health-monitor@3.0.0}
  - {path: architecture/admin.md, why: 'the admin dashboard, until g3-door-admin strikes it whole (decision 16)', until: architecture/admin@4.0.0}
  - {path: protocol/types.md, why: the note at LeaseState that says the words are gone}
  - {path: patterns/observability.md, why: the note at Component State Machine that says the words are gone}
  - {path: architecture/observability.md, why: 'the requires: comment that says the words are gone'}
  other_senses:
  - {path: patterns/offline.md, sense: an offline client or store}
  - {path: agents/sync.md, sense: an offline client or store}
  - {path: architecture/client.md, sense: an offline client or store}
  - {sense: offline verification}
  - {pattern: WL_BLUEPRINT_OFFLINE, sense: 'the CLI''s blueprint refreshes switched off, WL_BLUEPRINT_OFFLINE'}
  - {sense: a person online in a chat}
  - {sense: a provider or federation peer going offline}
  - {sense: an agent's own degraded lifecycle state in its state machine}
  - {pattern: content\.custody_degraded, sense: the custody event}
  - {sense: a score label}
- retired:
  - {spelling: healthy, match: sense}
  - {spelling: degraded, match: sense}
  - {spelling: unhealthy, match: sense}
  allow:
  - {path: agents/health-monitor.md, why: it retires whole, until: agents/health-monitor@3.0.0}
  - {path: architecture/admin.md, why: 'the admin dashboard, until g3-door-admin strikes it whole (decision 16)', until: architecture/admin@4.0.0}
  other_senses:
  - {path: patterns/api-ai.md, sense: 'an external model provider''s status at GET /ai/health, which is not a component of the tenant'}
  - {path: architecture/storage.md, sense: 'a past incident quoted as it was observed, in the Namespace Registry store'}
- retired:
  - {spelling: status, match: sense}
- retired:
  - {spelling: status, match: sense}
- retired:
  - {spelling: last_health_check, match: exact}
- retired:
  - {spelling: health, match: sense}
- retired:
  - {spelling: health_interval, match: exact}
  - {spelling: health_timeout, match: exact}
  - {spelling: health_failures, match: exact}
  - {spelling: orchestrator.health_*, match: exact}
  - {spelling: health_timeout_seconds, match: exact}
- retired:
  - {spelling: online, match: sense}
  - {spelling: degraded, match: sense}
  - {spelling: offline, match: sense}
- retired:
  - {spelling: state-tracking, match: exact}
  - {spelling: ComponentState, match: exact}
  - {spelling: component.state_change, match: exact}
- retired:
  - {spelling: Response, match: sense}
  - {spelling: uptime_seconds, match: exact}
  - {spelling: metrics_snapshot, match: exact}
- retired:
  - {spelling: agent_state, match: exact}
- retired:
  - {spelling: health.probe, match: exact}
  - {spelling: target, match: sense}
  - {spelling: result, match: sense}
- retired:
  - {spelling: framework_healthy, match: exact}
- retired:
  - {spelling: agent-offline, match: exact}
  - {spelling: agent_offline, match: exact}
- retired:
  - {spelling: agent-degraded, match: exact}
- retired:
  - {spelling: check_agent_health, match: exact}
- retired:
  - {spelling: --status <online|degraded|offline>, match: exact}
```
