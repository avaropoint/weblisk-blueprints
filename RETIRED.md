# Retired spellings

The names the corpus has stopped using, each listed once. A row gives the
retired spelling, the spelling that replaces it, the section that retired it,
and the only places the retired spelling may still appear; anywhere else in the
corpus it is a leftover to fix.

A row is added by the change that retires the spelling, and a place in its last
column is taken out by the change that rewrites that place.

| Retired | Replaced by | Retired by | May still appear in |
|---|---|---|---|
| `replica`, in any case and inside any name, for a copy of a content repository the content service keeps at a second place | `remote` | [`architecture/content`](architecture/content.md#remotes) 3.0.0, Remotes | The capability `content:replicate`, which is kept, wherever it is named. The word's other senses: an instance count (`replicas` in [`schemas/config`](schemas/config.md) and [`architecture/cli`](architecture/cli.md)), a scheduler's replicas ([`patterns/scheduling`](patterns/scheduling.md)), a state's backups and replicas ([`protocol/secret-source`](protocol/secret-source.md)), a production replica ([`patterns/migration`](patterns/migration.md)), a route to a replica ([`architecture/gateway`](architecture/gateway.md)), and replication ([`platforms/cloudflare`](platforms/cloudflare.md), [`patterns/deployment`](patterns/deployment.md)). This file |
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
| `telemetry:collect`, a name the design inputs used for the capability a component's signals reach telemetry under. No blueprint ever carried it, and it is listed so that none adopts it | `telemetry:push`, under which a component pushes its own signals | [`protocol/types`](protocol/types.md#capability) 2.0.0, Capability | This file |
