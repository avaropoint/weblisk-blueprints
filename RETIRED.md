# Retired spellings

The names the corpus has stopped using, each listed once. A row gives the
retired spelling, the spelling that replaces it, the section that retired it,
and the only places the retired spelling may still appear; anywhere else in the
corpus it is a leftover to fix.

A row is added by the change that retires the spelling, and a place in its last
column is taken out by the change that rewrites that place.

| Retired | Replaced by | Retired by | May still appear in |
|---|---|---|---|
| `replica`, in any case and inside any name, for a copy of a content repository the content service keeps at a second place | `remote` | [`architecture/content`](architecture/content.md#remotes) 3.0.0, Remotes | The words of [`protocol/types`](protocol/types.md#capability) §Capability and [`architecture/admin`](architecture/admin.md#operator-roles) §Operator Roles, until each is next revised. The capability `content:replicate`, which is kept, wherever it is named. The word's other senses: an instance count (`replicas` in [`schemas/config`](schemas/config.md) and [`architecture/cli`](architecture/cli.md)), a scheduler's replicas ([`patterns/scheduling`](patterns/scheduling.md)), a state's backups and replicas ([`protocol/secret-source`](protocol/secret-source.md)), a production replica ([`patterns/migration`](patterns/migration.md)), a route to a replica ([`architecture/gateway`](architecture/gateway.md)), and replication ([`platforms/cloudflare`](platforms/cloudflare.md), [`patterns/deployment`](patterns/deployment.md)). This file |
| `replicas`, in any case, the operation `Replicas` among them | `remotes`; the operation `Remotes` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints | As for `replica` |
| `ContentReplica` | `ContentRemote` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types | This file |
| `ReplicaCensus` | `RemoteCensus` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types | This file |
| `ReplicaDeclaration` | `RemoteDeclaration` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types | This file |
| `ReplicaEstablishment` | `RemoteEstablishment` | [`architecture/content`](architecture/content.md#types) 3.0.0, Types | This file |
| `DeclareReplica` | `DeclareRemote` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints and Interfaces | This file |
| `ListReplicas` | `ListRemotes` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces | This file |
| `RetireReplica` | `RetireRemote` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints and Interfaces | This file |
| `/v1/content/repositories/{repository}/replicas` | `/v1/content/repositories/{repository}/remotes` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints | This file |
| `/v1/content/repositories/{repository}/replicas/{replica}` | `/v1/content/repositories/{repository}/remotes/{remote}` | [`architecture/content`](architecture/content.md#endpoints) 3.0.0, Endpoints | This file |
| `CONTENT_REPLICA_UNSEEN` | `CONTENT_REMOTE_UNSEEN` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling | This file |
| `CONTENT_REPLICA_EXISTS` | `CONTENT_REMOTE_EXISTS` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling | This file |
| `CONTENT_REPLICA_UNKNOWN` | `CONTENT_REMOTE_UNKNOWN` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling | This file |
| `CONTENT_REPLICA_UNSUPPORTED` | `CONTENT_REMOTE_UNSUPPORTED` | [`architecture/content`](architecture/content.md#error-handling) 3.0.0, Error Handling | This file |
| `replica_retry_interval`, the key `content.replica_retry_interval` | `remote_retry_interval`, the key `content.remote_retry_interval` | [`architecture/content`](architecture/content.md#configuration) 3.0.0, Configuration, and [`schemas/config`](schemas/config.md#content) | This file |
| `content.replica_declared` | `content.remote_declared` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces | This file |
| `content.replica_state` | `content.remote_state` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces | This file |
| `content.replica_retired` | `content.remote_retired` | [`architecture/content`](architecture/content.md#interfaces) 3.0.0, Interfaces | This file |
| `Replica Sender` | `Remote Sender` | [`architecture/content`](architecture/content.md#architecture) 3.0.0, Architecture | This file |
| `architecture/content.md#replicas` | `architecture/content.md#remotes` | [`architecture/content`](architecture/content.md#remotes) 3.0.0, Remotes | This file |
| `architecture/content.md#replica-declaration-flow` | `architecture/content.md#remote-declaration-flow` | [`architecture/content`](architecture/content.md#remote-declaration-flow) 3.0.0, Remote Declaration Flow | This file |
| `architecture/content.md#replica-send-flow` | `architecture/content.md#remote-send-flow` | [`architecture/content`](architecture/content.md#remote-send-flow) 3.0.0, Remote Send Flow | This file |
| `architecture/content.md#a-replica-is-sent-to-and-never-read-from` | `architecture/content.md#a-remote-is-sent-to-and-never-read-from` | [`architecture/content`](architecture/content.md#a-remote-is-sent-to-and-never-read-from) 3.0.0, A remote is sent to, and never read from | This file |
| `architecture/content.md#declaring-a-replica` | `architecture/content.md#declaring-a-remote` | [`architecture/content`](architecture/content.md#declaring-a-remote) 3.0.0, Declaring a remote | This file |
| `architecture/content.md#who-may-declare-a-replica` | `architecture/content.md#who-may-declare-a-remote` | [`architecture/content`](architecture/content.md#who-may-declare-a-remote) 3.0.0, Who may declare a remote | This file |
| `architecture/content.md#retiring-a-replica` | `architecture/content.md#retiring-a-remote` | [`architecture/content`](architecture/content.md#retiring-a-remote) 3.0.0, Retiring a remote | This file |
| `GitReplicaCensusReport` | `GitRemoteCensusReport` | [`patterns/content-git`](patterns/content-git.md#types) 2.0.0, Types | This file |
| `GitReplicaReport` | `GitRemoteReport` | [`patterns/content-git`](patterns/content-git.md#types) 2.0.0, Types | This file |
| `git-replica-send` | `git-remote-send` | [`patterns/content-git`](patterns/content-git.md#contracts) 2.0.0, Contracts | This file |
| `git-replica-census` | `git-remote-census` | [`patterns/content-git`](patterns/content-git.md#contracts) 2.0.0, Contracts | This file |
| `remote` as a kind of `GitFinding`, for a remote configured in a store's own git configuration | `undeclared-remote` | [`patterns/content-git`](patterns/content-git.md#control-state) 2.0.0, Control State | Everywhere else, where `remote` is a current word: the content service's remote, which replaced `replica`, and git's own, as in a configured remote, `ls-remote` and the `git-remote` driver |
| `X-Trace-Id`, the HTTP header | `traceparent` (W3C Trace Context), and an envelope's `trace_id` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation | This file |
| `X-Span-Id`, the HTTP header | `traceparent`, and an envelope's `span_id` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation | This file |
| `X-Parent-Span-Id`, the HTTP header | `traceparent` read by the receiver, whose span records it as `parent_span_id` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation | This file |
| `protocol/spec.md#trace-id-propagation` | `protocol/spec.md#trace-propagation` | [`protocol/spec`](protocol/spec.md#trace-propagation) 3.0.0, Trace Propagation | This file |
| `lifecycle.startup`, `lifecycle.ready`, `lifecycle.shutdown`, `lifecycle.stopped`, `lifecycle.health_change`, `lifecycle.version_updated`, `lifecycle.version_rollback`, `lifecycle.version_retired`, `lifecycle.restored`, as log types | `process.startup`, `process.ready`, `process.shutdown`, `process.stopped`, `process.health_change`, `process.version_updated`, `process.version_rollback`, `process.version_retired`, `process.restored` | [`patterns/logging`](patterns/logging.md#log-types) 2.0.0, Log Types | The event topics of the lifecycle agent's namespace, which are events and not log types (`lifecycle.version_rollback` in [`patterns/versioning`](patterns/versioning.md) among them). This file |
| `task.received`, `task.completed`, `task.failed`, as log types | `execute.received`, `execute.completed`, `execute.failed` | [`patterns/logging`](patterns/logging.md#log-types) 2.0.0, Log Types | The event topics of the task agent's namespace, which keep these names as events. This file |
| `trace_id`, as a field of the `task.submit` payload (`TaskSubmission`) | the event envelope's `trace_id` and `span_id` | [`patterns/task-dispatch`](patterns/task-dispatch.md#types) 2.0.0, Types | This file |
| `log_format`, the key `observability.log_format`, and the `text` log format | nothing: records are JSON lines, and a tool renders them | [`patterns/logging`](patterns/logging.md#log-levels) 2.0.0, Log Levels, and [`schemas/config`](schemas/config.md) | This file |
| `Log output`, a log written to `stderr` or a file of the component's own | standard output, and OTLP where telemetry is deployed | [`patterns/logging`](patterns/logging.md#overview) 2.0.0, Overview and Log Rotation | This file |
| `log-rotation`, as a behaviour of `patterns/logging`, its `rotation` configuration (`max_size`, `max_files`), and `log-envelope` as a behaviour name | nothing for rotation, which is the runtime's that captures standard output; `structured-logging` and `trace-correlation` for the envelope | [`patterns/logging`](patterns/logging.md#log-rotation) 2.0.0, Log Rotation | This file |
| `fatal`, as a log level | `error` | [`protocol/types`](protocol/types.md#logentry) 2.0.0, LogEntry | This file |
| `app` and `access`, as `log_type` values | a type from [`patterns/logging`](patterns/logging.md#log-types)'s Log Types | [`protocol/types`](protocol/types.md#logentry) 2.0.0, LogEntry | This file |
| `start_time`, `end_time`, `duration_ms` and `events`, as fields of a span | `start` and `end`; nothing for `duration_ms`, which is `end` minus `start`, or for `events` | [`protocol/types`](protocol/types.md#span) 2.0.0, Span | `duration_ms` as a field of [`LogEntry`](protocol/types.md#logentry), wherever it is one. OpenTelemetry's own `start_time_unix_nano` and `end_time_unix_nano`. This file |
| `"type": "span"`, marking a span written as a log line | `log_type` `span` | [`architecture/observability`](architecture/observability.md#trace-export) 2.0.0, Trace Export | This file |
| `<component>.<operation>`, as the form of a span name | a name for what was done, from Span Names, with `component` saying who | [`architecture/observability`](architecture/observability.md#span-names) 2.0.0, Span Names | This file |
| A log line's `ts` as Unix epoch seconds, and its `timestamp` field | `ts` as an RFC 3339 UTC time with milliseconds | [`protocol/types`](protocol/types.md#logentry) 2.0.0, LogEntry | This file |
| `Owns`, the type [`architecture/observability`](architecture/observability.md) declared for a log line's required fields | [`LogEntry`](protocol/types.md#logentry) | [`architecture/observability`](architecture/observability.md#structured-logging) 2.0.0, Structured Logging | This file |
