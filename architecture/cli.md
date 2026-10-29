<!-- blueprint
type: architecture
name: cli
version: 4.4.0
requires: [protocol/spec, protocol/identity, protocol/secret-source, protocol/types, architecture/orchestrator, architecture/admin, patterns/command]
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
2. **Operations commands** — interrogate and manage a running hub through
   its admin gateway, which carries each request to the provider of the
   admin API group it addresses (`weblisk status`, `weblisk agents`,
   `weblisk domains`, `weblisk audit`, `weblisk federations`)

Operations commands authenticate with an operator's ML-DSA-65 identity — the
one `--identity <label>` names, or the unnamed default.
[Where an identity lives](#where-an-identity-lives) says where that is, and
whether its private half is an encrypted file or held by a secret source.

### The binary is named `weblisk`

Stated explicitly because it was only ever implied. Every example here invokes
`weblisk`, and nothing said that the installed executable MUST carry that name —
so a Go implementation whose module path ends in `weblisk-cli` installed as
`weblisk-cli`, and Studio, which resolves the CLI by the name this blueprint
uses, reported "the weblisk CLI is not on PATH" on a machine where it was
installed and working.

The invocation name is part of the interface. Anything that shells out to this
CLI — a control plane, a CI job, an operator's script, this blueprint's own
examples — resolves it as `weblisk`, so an implementation MUST install it under
that name regardless of what its module, crate or package is called.

A consumer MUST NOT accumulate a list of alternative spellings to try. That
turns one interface into several and hides the fault in whichever build produced
the wrong name.

#### Resolving it, and why PATH alone is not enough

A consumer MUST resolve `weblisk` by searching the usual install locations **as
well as** `PATH`, and MUST honour an explicit override.

This is the same requirement this blueprint already states for a local AI
backend, and it applies to resolving this CLI for the same reason: a process
started by launchd, systemd, a double-click or an editor does not inherit a
login shell's `PATH`. Go installs to `$GOBIN` or `$(go env GOPATH)/bin`, which
is on `PATH` only because a shell profile puts it there — so a control plane
started outside a terminal reports "the weblisk CLI is not on PATH" on a machine
where it is installed and an operator is using it in another window. That is a
diagnosis nobody can act on.

The locations to search, in addition to `PATH`:

| Location | Why |
|---|---|
| `$WL_CLI` | an explicit path, honoured exactly as given and never second-guessed |
| `~/.weblisk/bin` | where a published CLI installs itself — see below |
| `$GOBIN`, `$(go env GOPATH)/bin` | where `go build -o` and `go install` put it |
| `~/.local/bin` | the convention for a user-scoped install |
| `/opt/homebrew/bin`, `/usr/local/bin` | Homebrew on Apple silicon and Intel |

`~/.weblisk/bin` is where a build from source SHOULD install, and where a
published binary SHOULD land.

`~/.weblisk` is already this product's own directory: it holds the blueprint
cache, the operator identity, and a console's per-account identities. The CLI
belongs beside them, and for a reason that outlives convenience — a CLI
downloaded from a CDN cannot install to `$(go env GOPATH)/bin`, because a
machine that never had Go has no GOPATH and no `go` to ask. Making the Go
toolchain's output directory the primary home ties distribution to a build
system most consumers will not have.

The Go locations remain in the search order, because `go install` is how a
contributor gets one and silently not finding that build would be worse than
finding it.

A refusal MUST name every location searched. "Not installed" without the list
cannot be acted on; "looked on PATH and in these five places" can.

Commands follow a `weblisk <noun> <verb>` pattern and output
structured, human-readable tables by default, with `--json` for
machine-readable output.

**Conventions:**
- Singular nouns act on a single resource (`agent create`, `secret set`)
- Plural nouns query collections (`agents list`, `domains describe`)
- `list` — enumerate resources (always supports `--json`)
- `describe` — full detail for a single resource by name or ID
- `create` — scaffold or provision a new resource
- `delete` — remove a local resource (secrets, files)
- `deregister` — remove a remote registration (agents)
- `revoke` — invalidate trust or access (operators, federation peers)
- `--json` — machine-readable output (available on all read commands)
- `--confirm` — required for destructive operations (or interactive prompt)

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=3.0.0 <5.0.0"
    bindings:
      endpoints:
        - path: /v1/register
          methods: [POST]
        - path: /livez
          methods: [GET]
        - path: /readyz
          methods: [GET]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    # 2.2.0 is where weblisk/step-up/v1, the statement a destructive
    # command's re-confirmation signs, is registered and step_up_at is set
    # only through one (Authentication Flow). The CLI never reads step_up_at:
    # it obtains a token carrying it and presents it
    version: ">=2.2.0 <3.0.0"
    bindings:
      types:
        - name: WLToken
          fields_used: [sub, iss, iat, exp, cap, role]
        - name: SigningKeyPair
          fields_used: [public_key, private_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/secret-source
    version: ">=1.7.0 <2.0.0"
    bindings:
      types:
        - name: HolderReference
          fields_used: [version, source, reference, options, holds]
        - name: SecretSourceRequest
          fields_used: [version, action, reference, field, fields, label, alg, message, messages, options]
        - name: SecretSourceResponse
          fields_used: [value, reference, actions, sign_algs, sign_batch, named_fields, withheld_fields, signature, signatures, error]
        - name: SecretSourceError
          fields_used: [code, message]
        - name: SecretSourceRegistryEntry
          fields_used: [command, timeout_s, interactive_timeout_s]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    # the lower bound is where STEP_UP_REQUIRED, the code a destructive
    # command re-confirms and retries on (Authentication Flow), exists;
    # TOKEN_REQUEST_REPLAYED, the code a replayed token request is refused
    # with, exists there too. No command reads a directory
    # entry's lease state: server verify and status read lease states from
    # the admin API (architecture/admin below)
    version: ">=3.1.0 <6.0.0"
    bindings:
      types:
        - name: Operator
          fields_used: [name, public_key, role, status]
        - name: AgentManifest
          fields_used: [name, version, type, url, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    # 3.0.0 is where the directory holds leases and the orchestrator
    # serves /livez and /readyz; a 2.x orchestrator answers neither
    version: ">=3.0.0 <5.0.0"
    bindings:
      endpoints:
        - path: /v1/admin/*
          methods: [GET, POST, PUT, DELETE]
        # weblisk test conformance reads the directory on its test agent's
        # registration token; POST /v1/services is each agent's endpoint
        - path: /v1/services
          methods: [GET]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/admin
    # 4.0.0 is where a destructive act needs a step-up, /v1/admin/approvals
    # is the decision inbox and strategies and observations are gone
    version: ">=4.0.0 <6.0.0"
    bindings:
      endpoints:
        - path: /v1/admin/operators/register
          methods: [POST]
        - path: /v1/admin/operators/token
          methods: [POST]
        - path: /v1/admin/credentials/challenge
          methods: [POST]
        - path: /v1/admin/credentials/token
          methods: [POST]
        - path: /v1/admin/hub/proof
          methods: [POST]
        - path: /v1/admin/operators/{name}/credentials
          methods: [POST]
        - path: /v1/admin/operators/{name}/key
          methods: [POST]
        - path: /v1/admin/overview
          methods: [GET]
        - path: /v1/admin/agents
          methods: [GET]
        - path: /v1/admin/agents/{name}
          methods: [GET]
        - path: /v1/admin/agents/{name}/metrics
          methods: [GET]
        - path: /v1/admin/approvals
          methods: [GET]
      behaviors:
        - name: operator-registration
        - name: registration-signing-input
        # weblisk operator register reports an approved first registration
        # and a pending one, and weblisk operators approve and role drive
        # the admission and the roles
        - name: first-operator-claim
        - name: operator-approval
        - name: operator-roles
        # A destructive command answers STEP_UP_REQUIRED by re-confirming
        # its person (Authentication Flow)
        - name: destructive-action-step-up
        - name: attestation-token-issuance
        - name: hub-proof
        - name: operator-credential-attestation
        - name: operator-token-issuance
        - name: operator-key-change
        - name: admin-gateway-authorization
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

The CLI has two command surfaces against one identity: **project** commands that
act on local files, and **operator** commands that act on a running hub.

```
   Operator (a person)
         │
         ▼
   ┌────────────────────────────────────┐
   │ CLI                                │
   │  project: scaffold · build · serve │
   │  operator: init · connect · token  │
   │  generation: dispatch · verify     │
   └────┬──────────────────────┬────────┘
        │ signs through it     │ authenticated per request
        ▼                      ▼
   Identity holder        Admin gateway
   (a secret source,      (the hub's one door, over
    or a key file)         a transport the operator named)
```

**Responsibilities.** Scaffolding and building projects, generating components from
blueprints and gating them on conformance, resolving where an identity lives,
getting signatures from wherever the identity is held — a private key is in its
memory only when that holder cannot sign — and minting short-lived tokens with
a credential the identity attested once for each hub.

**Not responsibilities.** Holding a long-lived secret of its own. Deciding what a
blueprint requires — it reads the corpus. Administering a hub's data, which is
Studio's and the orchestrator's own surfaces.

---

## Responsibilities

### Owns

- CLI command structure (`weblisk <noun> <verb>` pattern)
- Project scaffolding from templates (`weblisk new`)
- Code generation via LLM dispatch (`weblisk server init`, `weblisk agent create`)
- Blueprint resolution ([Where blueprints come from](#where-blueprints-come-from)),
  and template resolution (local → custom sources → core)
- Dev server with file watching (`weblisk dev`)
- Production builds (`weblisk build`)
- Static framework vendoring (`weblisk vendor`)
- Operator ML-DSA-65 identity creation, and resolving where a named identity
  lives — an encrypted key file, or a holder reference naming the secret source
  that holds the private half ([Where an identity lives](#where-an-identity-lives))
- Operator registration and token management (which commands keep the token
  they obtain, and where: [`weblisk operator token`](#weblisk-operator-token))
- One credential per identity per hub, attested once by that identity and kept
  in the platform keychain, or beside the identity where no keychain exists
  ([A credential for each hub](#a-credential-for-each-hub))
- Attesting a credential another program holds, so a console never holds the
  identity that attests it (`weblisk operator attest`)
- Human-readable table output and `--json` machine-readable output formatting
- Interactive confirmation for destructive actions
- Connection management to a hub's admin gateway

### Does NOT Own

- Admin API endpoints (owned by `architecture/admin`)
- Orchestrator state or agent lifecycle (CLI reads/writes via API)
- Operator authentication model (owned by `architecture/admin`; CLI consumes it)
- Workflow or task execution (CLI triggers actions via API)
- Template contents (owned by `weblisk-templates`)
- Client framework (owned by `weblisk`)
- Blueprint specifications (owned by this repository — `weblisk-blueprints`)
- What a repository outside any tenant may be used for, and how what it holds
  reaches a tenant (owned by `architecture/content` —
  [Repositories Outside a Tenant](content.md#repositories-outside-a-tenant)).
  Every blueprint source no tenant has declared is one, the core corpus among
  them

---

## Interfaces

The CLI’s public interface is the set of terminal commands documented in
the sections below: [Project Commands](#project-commands),
[Server Commands](#server-commands),
[Blueprint Commands](#blueprint-commands),
[Identity Commands](#identity-commands),
[Status Commands](#status-commands), [Agent Commands](#agent-commands),
[Domain Commands](#domain-commands), [Workflow Commands](#workflow-commands),
[Approval Commands](#approval-commands), [Objective Commands](#objective-commands),
[Federation Commands](#federation-commands),
[Audit Commands](#audit-commands), and the
[Resource commands](#resource-commands), whose nouns and verbs are read from
the tenant.

---

## Data Flow

1. Operator runs a CLI command (e.g., `weblisk agents list`)
2. CLI resolves which identity acts — `--keys-dir`, else `--identity <label>`, else the unnamed default
3. CLI loads the token stored beside that identity where one is kept
   ([Where a token is kept](#weblisk-operator-token)),
   and otherwise obtains one for this command and holds it in memory, as the
   [Authentication Flow](#authentication-flow) says (renewing one near expiry)
4. CLI constructs an HTTP request to the hub's admin gateway, the tenant's one
   door for people, whatever group the command addresses
   ([`protocol/identity`](../protocol/identity.md#the-pass))
5. Token included in the `Authorization: Bearer` header
6. The gateway carries the request to the provider of its group: to the
   orchestrator on the token as it arrived, where the orchestrator validates
   it and checks the request can use the capability the endpoint's minimum
   stands for, what the operator's role carries now, never beyond the token's
   `cap` ([`architecture/admin`](admin.md#auth-middleware), Auth Middleware);
   to any other provider on a pass the orchestrator exchanged the token for
   ([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`)
7. The provider returns a JSON response, through the gateway
8. CLI formats response as human-readable table (or raw JSON with `--json`)
9. For write operations: CLI prompts for interactive confirmation before
   sending, and a destructive act also needs its person's step-up
   ([Authentication Flow](#authentication-flow))
10. Exit code set based on success/failure (0 = success, 1 = error, 2 = auth failure)

**A group another component provides is reached on a pass, never on the
stored token.** The domain, workflow, approval, objective and
federation commands address groups
[`architecture/admin`](admin.md#the-admin-api-is-an-aggregate) gives to a
component other than the orchestrator. The CLI sends them to the admin
gateway as it sends every command, and the gateway, not the CLI, has the
token exchanged for a pass addressed to that component alone. No such
component's blueprint specifies an administrative route yet
([`architecture/admin`](admin.md#the-admin-api-is-an-aggregate), the gap
there), so the gateway answers each of these commands
`ADMIN_GROUP_UNAVAILABLE`, and the command reports its group unavailable and
exits 1. The approval commands read the decision inbox the gateway composes
from each owner it may ask, and it may ask none until a `PassRoute` can name
the inbox group ([`architecture/admin`](admin.md#decision-inbox)), so they
report the inbox unavailable and exit 1 too.

---

## Design Principles

1. **ML-DSA-65 identity, not passwords** — The CLI uses the same
   cryptographic identity system as agents. No passwords, no session
   cookies.
2. **Read by default, write with flags** — Destructive commands require
   explicit `--confirm` or interactive confirmation.
3. **Consistent output** — All commands output tables for humans, JSON
   with `--json` for scripts and piping.
4. **Offline-aware** — If the orchestrator is unreachable, commands
   fail fast with a clear message and non-zero exit code.

---

## Command Grammar

What follows is the shape every command takes. The sections after it specify
today's commands one by one; [The Command Surface](#the-command-surface) lists
them, and [Renamed commands](#renamed-commands) says what each becomes.

### The grammar

`weblisk <noun> <verb> [ref…]`.

- **Family nouns are data.** Each family declaration ([`schemas/family`](../schemas/family.md))
  is a noun: `blueprint`, `standard`, `programme`, `spec`, `template`, `skill`,
  `position`, `policy-domain`, `language`, `platform`, `framework`,
  `interface`. Adding a family adds its noun, with no change to the CLI.
- **Verbs are a closed set in code**, each gated by a capability the family
  declares. A family that lacks the capability has no such verb.
- **A tenant's resource kinds are nouns, read from the tenant.** Each kind the
  tenant's catalogue declares is a noun, with the verbs its declaration
  serves ([Resource commands](#resource-commands)). A kind the tenant adds
  adds its noun, with no change to the CLI.
- **Operational nouns are code**: `knowledge`, `component`, `agent`,
  `workflow`, `tenant`, `change`, `run`, `fabric`, `namespace`, `catalog`, `id`,
  `identity`, `operator`, `approval`, `secret`, `provider`, `cache`,
  `marketplace`, `gateway`, `app`.
- **One manifest.** `weblisk commands --json` lists every command with its
  parameters, capability and executor. Help is rendered from it, Studio is
  driven by it, and the per-family command list is generated from it and never
  written by hand.
- **Every command declares its executor** — `local`, `tenant-api` or
  `cli-in-tenant` — whose meaning is [`schemas/change`](../schemas/change.md#executors)'s
  (D24). Studio runs only `local` commands on its own host; for a tenant it
  calls `tenant-api` routes, and never runs a command on its host that acts on
  a tenant.

### Verbs

| Verb | Capability | Executor | What it does |
|---|---|---|---|
| `new <id>` | `author` | `local` | template, fill, write, validate: a new file starts valid |
| `validate [<ref>\|<dir>]` | always | `local` | the corpus rules over a file or a repository |
| `walk <file>` | always | `local` | the projection a walk of the file produces |
| `show <ref>` · `list` | always | `local` | one item, or the family's items |
| `deps <ref>…` | `depends` | `local` | both closures for one or more refs |
| `diff <ref>@a <ref>@b` | `versioned` | `local` | by part id; a prose-only change is marked as such |
| `release <ref>` | `versioned` | `local` | proposes a major, minor or patch version from the diff; the author confirms |
| `rename <ref> <new>` · `retire <ref>` | `author` | `local` | writes `formerly` or `retired` |
| `impact <ref>[@a..@b]` | `versioned` | `tenant-api` | a fabric read; with no tenant reachable, says it cannot know |
| `build <ref>… --out <dir>` | `generates` | `local` | a scratch build outside any tenant, which records a run |
| `adopt` · `upgrade` · `remove` | `adoptable` | `tenant-api` | each creates a change and prints its plan |
| `status [<ref>]` | `adoptable` | `tenant-api` | what the tenant has adopted, at which version |

`build` outside a tenant and `change apply` inside one are never synonyms.

### Changes

`weblisk change plan --adopt|--upgrade|--remove <ref>… [--strict] [--resolve-only] [--json]`,
then `change list`, `show`, `approve`, `reject`, `apply`, `verify` and
`revert`, against [`/v1/admin/changes`](admin.md#changes-and-builds). Where
each runs, and so where its act happens, is [`schemas/change`](../schemas/change.md#executors)'s
table, as is what a change holds; how it is
resolved is [`architecture/generation`](generation.md#resolving-a-request-of-many-roots)'s.
`change apply` runs in the tenant, never on the client (D26). A plan with no
entries is rendered as a fault, never as clean.

### Who may approve a change

The rules of D25, which the change service enforces and a client only renders:

1. **A change is approved by a signed operator identity**, over the plan's
   digest, on a pass to the change service. An unsigned approval is no approval.
2. **A knowledge change is approved by a holder of the position its spec
   names**, recorded as the approval's `position`.
3. **Self-approval** — the requester approving their own change — **is allowed
   only on a tenant flagged as a development tenant**, and is recorded with
   `development: true` and shown as such wherever the change is shown.
4. **The approval queue is the change queue.** A change awaiting approval is an
   [`ApprovalRequest`](../protocol/types.md#approvalrequest) held by the change
   service, listed in the decision inbox with every other decision, so
   `change approve` is a form of `approval accept`.
5. **A change with a refusing conflict is never approved** ([`schemas/change`](../schemas/change.md#rules), `approval-conflicts`).

### Resource commands

`weblisk <kind> <verb> [<uid>] [flags]`, for every kind the connected tenant's
catalogue declares ([`architecture/admin`](admin.md#resources-one-api-for-every-kind)),
and `weblisk resource list` and `weblisk resource show <kind>` for the
catalogue itself. The CLI and Studio are two clients of the one API: the CLI
learns every noun, verb, field and refusal here from the catalogue, at the
tenant, and holds no list of its own. Each is `tenant-api`.

| Command | Calls | What it does |
|---|---|---|
| `resource list` | `GET /v1/admin/resources` | Every declared kind, each `available` or `declared-unavailable` with its reason, which is printed and never left out |
| `resource show <kind>` | `GET /v1/admin/resources` | One kind's declaration: its fields and how each may be set, its operations and verbs with the capability each needs, whether it takes a step-up, its states and events |
| `<kind> list` | `GET /v1/admin/r/{kind}` | The items, a page at a time; `--where <field>=<value>` for each filter the kind declares, `--all` to read every page |
| `<kind> show <uid>` | `GET /v1/admin/r/{kind}/{uid}` | One item, with its `ETag` |
| `<kind> create` | `POST /v1/admin/r/{kind}` | `--set <field>=<value>` for each field it may set, or `--from <file>` |
| `<kind> update <uid>` | `PATCH /v1/admin/r/{kind}/{uid}` | `--set`, `--from`; `If-Match` is the `ETag` of the read it makes first, or `--if-match` |
| `<kind> delete <uid>` | `DELETE /v1/admin/r/{kind}/{uid}` | With `If-Match` as `update` takes it |
| `<kind> <verb> <uid>` | `POST /v1/admin/r/{kind}/{uid}/{verb}` | Prints the verb's preconditions, in-flight handling, effect and whether it can be undone, then asks; `--yes` skips the question |
| `<kind> watch [<uid>]` | `GET /v1/admin/ws` | Prints each event as it arrives; `--after <position>` to resume |

- **Only what the declaration serves exists.** A verb or operation the kind
  does not declare is not offered, and if a stale catalogue offers one the
  tenant's `RESOURCE_OPERATION_UNDECLARED` is printed as it came.
- **A field is set only as its declaration allows.** `secret` fields are read
  from a prompt or a secret source, never from the command line, and never
  printed; a field outside the presentations is printed as its value and never
  offered for setting ([`schemas/resource`](../schemas/resource.md#presentations)).
- **A destructive act asks for its person's step-up** as every destructive act
  does ([Authentication Flow](#authentication-flow)), and an act the tenant
  answers `RESOURCE_PRECONDITION_FAILED` is never retried with a fresh
  `If-Match`: the item changed, and the person is shown it again.
- **An unavailable kind says why.** `<kind> list` for a `declared-unavailable`
  kind prints its reason, as `ADMIN_GROUP_UNAVAILABLE` carries it, and exits
  non-zero; it never prints an empty list.
- **`--json`** prints what the tenant answered, unchanged.

A noun that is both a resource kind and an operational noun of today's
surface takes the kind's verbs for what the tenant holds: `weblisk agents
list`, `describe` and `deregister` are `agent list`, `agent show` and
`agent deregister` ([Renamed commands](#renamed-commands)). Today's
`agent list`, which lists agents scaffolded on this machine, is the one
spelling that collides, and is renamed with the scaffolding commands by
`v2-cli-cmdtree`.

`server start`, `stop` and `restart`, and `component <name> start` and `stop`,
are unchanged: starting and stopping a process is the supervisor's on the
tenant's host, never an act on a resource.

### The Command Surface

Every command the sections after this one specify, each with its executor:
today's commands, from before the grammar. The grammar's own commands (the
[Verbs](#verbs) table and the [change verbs](#changes)) are not rows here, so
the check below does not count them as specified and not built;
`v2-cli-cmdtree` builds them, and its `weblisk commands --json` is where they
are first listed. A renamed command is a row under the name it has today
([Renamed commands](#renamed-commands)): `identity attest` is the row
`operator attest`. `checks/command-surface.py`
in the corpus holds this block against the commands the CLI builds, and reports
each one specified and not built, and each built and not specified, so the
drift between the two is a measured list rather than a surprise. The list is
replaced by `weblisk commands --json` when that command is built.

```yaml
command_surface:
  - {noun: new, verb: "", executor: local}
  - {noun: dev, verb: "", executor: local}
  - {noun: build, verb: "", executor: local}
  - {noun: vendor, verb: "", executor: local}
  - {noun: version, verb: "", executor: local}
  - {noun: doctor, verb: "", executor: local}
  - {noun: secret, verb: list, executor: local}
  - {noun: secret, verb: set, executor: local}
  - {noun: secret, verb: get, executor: local}
  - {noun: secret, verb: delete, executor: local}
  - {noun: secret, verb: rotate, executor: local}
  - {noun: tenant, verb: create, executor: cli-in-tenant}
  - {noun: tenant, verb: accept, executor: cli-in-tenant}
  - {noun: tenant, verb: export, executor: cli-in-tenant}
  - {noun: tenant, verb: rebuild, executor: cli-in-tenant}
  - {noun: providers, verb: "", executor: local}
  - {noun: component, verb: init, executor: cli-in-tenant}
  - {noun: component, verb: start, executor: cli-in-tenant}
  - {noun: component, verb: stop, executor: cli-in-tenant}
  - {noun: component, verb: status, executor: cli-in-tenant}
  - {noun: component, verb: logs, executor: cli-in-tenant}
  - {noun: server, verb: init, executor: cli-in-tenant}
  - {noun: server, verb: start, executor: cli-in-tenant}
  - {noun: server, verb: stop, executor: cli-in-tenant}
  - {noun: server, verb: verify, executor: cli-in-tenant}
  - {noun: server, verb: provision, executor: cli-in-tenant}
  - {noun: agent, verb: create, executor: cli-in-tenant}
  - {noun: agent, verb: start, executor: cli-in-tenant}
  - {noun: agent, verb: verify, executor: cli-in-tenant}
  - {noun: agent, verb: list, executor: cli-in-tenant}
  - {noun: domain, verb: create, executor: cli-in-tenant}
  - {noun: domain, verb: start, executor: cli-in-tenant}
  - {noun: gateway, verb: create, executor: cli-in-tenant}
  - {noun: gateway, verb: start, executor: cli-in-tenant}
  - {noun: blueprint, verb: sources, executor: local}
  - {noun: blueprint, verb: update, executor: local}
  - {noun: validate, verb: "", executor: local}
  - {noun: pattern, verb: apply, executor: cli-in-tenant}
  - {noun: operator, verb: init, executor: local}
  - {noun: operator, verb: store, executor: local}
  - {noun: operator, verb: path, executor: local}
  - {noun: operator, verb: register, executor: tenant-api}
  - {noun: operator, verb: connect, executor: tenant-api}
  - {noun: operator, verb: token, executor: tenant-api}
  - {noun: operator, verb: attest, executor: tenant-api}
  - {noun: operator, verb: rotate, executor: tenant-api}
  - {noun: status, verb: "", executor: tenant-api}
  - {noun: agents, verb: list, executor: tenant-api}
  - {noun: agents, verb: describe, executor: tenant-api}
  - {noun: agents, verb: deregister, executor: tenant-api}
  - {noun: domains, verb: list, executor: tenant-api}
  - {noun: domains, verb: describe, executor: tenant-api}
  - {noun: workflows, verb: list, executor: tenant-api}
  - {noun: workflows, verb: describe, executor: tenant-api}
  - {noun: approvals, verb: list, executor: tenant-api}
  - {noun: approvals, verb: describe, executor: tenant-api}
  - {noun: approvals, verb: accept, executor: tenant-api}
  - {noun: approvals, verb: reject, executor: tenant-api}
  - {noun: objectives, verb: list, executor: tenant-api}
  - {noun: objectives, verb: describe, executor: tenant-api}
  - {noun: federations, verb: peers, executor: tenant-api}
  - {noun: federations, verb: pending, executor: tenant-api}
  - {noun: federations, verb: accept, executor: tenant-api}
  - {noun: federations, verb: reject, executor: tenant-api}
  - {noun: federations, verb: revoke, executor: tenant-api}
  - {noun: federations, verb: describe, executor: tenant-api}
  - {noun: federations, verb: contracts, executor: tenant-api}
  - {noun: operators, verb: revoke, executor: tenant-api}
  - {noun: operators, verb: approve, executor: tenant-api}
  - {noun: operators, verb: list, executor: tenant-api}
  - {noun: operators, verb: describe, executor: tenant-api}
  - {noun: operators, verb: role, executor: tenant-api}
  - {noun: audit, verb: "", executor: tenant-api}
  - {noun: test, verb: conformance, executor: tenant-api}
  - {noun: test, verb: mock-orchestrator, executor: local}
  - {noun: deploy, verb: rollback, executor: cli-in-tenant}
  - {noun: deps, verb: audit, executor: local}
  - {noun: policy, verb: validate, executor: local}
  - {noun: policy, verb: test, executor: local}
  - {noun: marketplace, verb: search, executor: local}
  - {noun: marketplace, verb: describe, executor: local}
  - {noun: marketplace, verb: buy, executor: local}
  - {noun: marketplace, verb: install, executor: local}
  - {noun: marketplace, verb: list, executor: local}
  - {noun: marketplace, verb: publish, executor: local}
  - {noun: marketplace, verb: update, executor: local}
  - {noun: marketplace, verb: delist, executor: local}
  - {noun: marketplace, verb: dashboard, executor: local}
  - {noun: marketplace, verb: reviews, executor: local}
  - {noun: marketplace, verb: review, executor: local}
  - {noun: marketplace, verb: collaborations, executor: local}
  - {noun: marketplace, verb: usage, executor: local}
  - {noun: marketplace, verb: terminate, executor: local}
```

### Renamed commands

Each old spelling lives for one release as an alias that prints the new form,
and an alias that stands for a one-ref `change plan` produces a plan byte for
byte identical to it.

| Today | Becomes |
|---|---|
| `new`, `dev`, `build`, `vendor` (an application) | `app new`, `app dev`, `app build`, `app vendor` |
| `build status` | `run status` |
| `server init`, `component <kind> init`, `agent create`, `domain create`, `gateway create` | one path: `tenant new`, or `component new --from <ref>…`, which is a change |
| `tenant create`, `tenant accept` | `tenant new`, `tenant verify` |
| `pattern apply` | `blueprint adopt patterns/<name> --into component:<name>` |
| `deploy rollback` | `change revert` |
| `operator` (the identity on this machine: `init`, `store`, `path`, `connect`, `token`, `rotate`, `sign`, `pubkey`, `attest`) | `identity`; so `operator attest` is `identity attest` |
| `operators` (a hub's operators) | `operator` |
| `approvals` | `approval`; `change approve` is a form of `approval accept` |
| `agents list`, `agents describe <name>`, `agents deregister <name>` | `agent list`, `agent show <name>`, `agent deregister <name>`, the resource commands for the `agent` kind ([Resource commands](#resource-commands)) |
| `policy validate`, `policy test` (the gateway's policy file) | `gateway policy validate`, `gateway policy test` |
| `programme <id> init` | `programme adopt <id>` |

The CLI's hard-coded platform lists and its `go` defaults are removed: a target
is declared, never assumed.

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
priority order: local `./templates/` → configured template sources → core.

When multiple `--template` flags are specified, files are merged — client
templates provide pages and islands, server templates provide hub
configuration and agent specs.

The name given replaces the template's project name everywhere the template
carries it, in file contents and file names alike.

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
| `--port <n>` | Dev server port (default: 3000, configurable) |

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

Exit codes, from the ones [Exit Codes](#exit-codes) declares: 0 = all pass,
or warnings only, which are printed; 1 = errors found.

### `weblisk secret`

Manage secrets for the project. All operations are local — secrets
live in `.weblisk/secrets/` and are never transmitted.

```bash
$ weblisk secret list
$ weblisk secret set email-send SMTP_PASSWORD
$ weblisk secret set _shared LLM_API_KEY
$ weblisk secret get email-send SMTP_PASSWORD
$ weblisk secret delete email-send SMTP_PASSWORD
$ weblisk secret rotate email-send SMTP_PASSWORD
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
- `set --stdin` reads the value from stdin (for piping from a vault
  or secrets manager in CI/CD — never from a shell argument).
- `get` prints a warning that secret values should not be displayed in
  shared terminals. Requires `--confirm` flag.
- All operations write to `.weblisk/secrets/{agent}/{KEY}` with 0600
  permissions.
- The `list` subcommand cross-references agent blueprint declarations
  with stored values to show which secrets are missing.

---

## Server Commands

### `weblisk tenant create <name>`

Turn a name into a running tenant with its first operator admitted, in one
command.

```bash
$ weblisk tenant create "Acme Corp"
$ weblisk tenant create "Acme Corp" --platform go --dir ./acme --port 9860
```

| Flag | Description |
|------|-------------|
| `--dir <path>` | Where to create it. Default: `./<slug>`, the name lowercased with each run of characters other than `a`–`z` and `0`–`9` made one `-`, none at either end (`Acme Corp` → `./acme-corp`). Its blueprints are resolved from there, not from the working directory ([Where blueprints come from](#where-blueprints-come-from)) |
| `--platform <p>` | Which platform blueprint, skills and layout the tenant is built from. Default `go` |
| `--provider <p>` | Model backend. Omitted means the one [`weblisk providers`](#weblisk-providers) marks as its default and, where nothing named that one, the next in its ranking when it cannot answer |
| `--model <m>` | Model name, where the provider takes one |
| `--operator <name>` | Who the first operator IS, as the hub records them |
| `--identity <label>` | Which identity SIGNS. Decides who may administer this tenant, permanently |
| `--keys-dir <path>` | Which identity signs, by location. Wins over `--identity` |
| `--port <n>` | Orchestrator port. `0` picks a free one and the result reports it. Omitted: the orchestrator's conventional port ([`schemas/config`](../schemas/config.md#port-conventions)) |
| `--resume` | Continue into a directory that already holds generated code |
| `--json` | One progress object per line, for a GUI |

The steps are a contract, because both front ends render them and a GUI that
cannot show progress during a minutes-long generation grows its own
implementation to get it:

    provider · directory · generate · skills · provision · accept · done

The admin gateway is stood up inside those steps, so the contract does not
change for it. `generate` builds the orchestrator and then the admin gateway
([`architecture/admin`](admin.md#the-admin-gateway-as-a-component)).
`provision` makes the gateway's registration key and, where none is
configured, its certificate and key, writes `.weblisk/config.yaml`'s
`admin_gateway` section with `orchestrator.admin_addresses` and
`orchestrator.admin_gateway_identity`, all before it starts the orchestrator,
then starts the orchestrator and, once it answers ready, the gateway, and
admits the first operator. <!-- wl:id cli-create-stands-up-gateway -->
`accept` probes through the gateway ([`weblisk tenant accept`](#weblisk-tenant-accept)).

**Nothing the corpus can refuse waits for a model.** Settling a provider when
nobody named one asks the backend it would start with to answer once, a real
model call ([`weblisk providers`](#weblisk-providers)), so everything knowable
from the blueprints is asked before any provider is settled: that the
orchestrator's own blueprint resolves, that every blueprint in the resolved
corpus parses, and that this machine has the toolchain the platform blueprint
asks for. A run with no corpus to build from used to pay for a provider and
then be refused. A refusal there is reported under `provider`, the step that
would otherwise have spent the call, and says that no provider was asked.

**`--port 0` picks a free port**, chosen when the orchestrator is started rather
than at second zero: a port that was free before an hour of generation is not a
port anybody reserved. The result reports the port it took. A console building a
tenant beside one that is already running passes `0`, because a fixed default is
a collision the moment one tenant is up. The port is this run's: as for any
`--port`, `create` declares it nowhere in the tenant's configuration, so a later
start does not find it there. With `--port 0` the admin gateway's two listeners
take free ports too, and those `create` does write, into `admin_gateway`,
because `orchestrator.admin_addresses` names the admin listener's origin and
the two must agree. The gateway is started with `--orch` naming the address
the orchestrator bound, as an IP literal such as `http://127.0.0.1:<port>` and
never `localhost`: the gateway judges it by rule 19 of
[`schemas/config`](../schemas/config.md#validation-rules), as it judges
`admin_gateway.orchestrator`, and refuses a plain `http` address whose host
is a name. A console that starts the orchestrator again on
the port the result reported passes it to
[`weblisk component orchestrator start --port`](#weblisk-component-name-start--stop--status--logs).

**`create` writes no token down, and prints none for a person.** With
`--json`, the last object carries `result`: `root`, `name`, `port`, `operator`,
`provider`; `model`, only where `--model` named one, because a model name the
CLI filled in would read as a choice nobody made; the `skills` the tenant
carries; what acceptance asked (`checks`); and the hub's `address`, the admin
gateway's origin, for a console to connect to, with the `tls_pin` its
certificate is verified against
([`architecture/admin`](admin.md#certificate)), the first operator's `token`
there and `token_expires_at` (`protocol/conventions:instant`). That object is the only
place a token may go: `create` writes no token file, and what it prints
without `--json` names the address and the pin for a person to connect
at with [`weblisk operator connect`](#weblisk-operator-connect), and never a
token. The stream is addressed to the program that started the command, which
holds the token in memory as it holds the passphrase it sent; a caller that
copies the stream to a file has written a bearer credential to disk.

**`create` produces the orchestrator and the admin gateway, and nothing
else.** A tenant is a set of components in one module, and those two are the
set every tenant has: without the gateway no person's request reaches it.
Every other is added afterwards with `weblisk component <name> init` or the
matching `create` verb. See
[`architecture/orchestrator`](orchestrator.md), "What a tenant consists of",
for the two homes a tenant's components have: what it is running, which the
orchestrator's registry answers and no file can, and which the CLI reads at
`GET /v1/admin/agents` through the admin gateway, and what it declares it should run,
which `.weblisk/config.yaml` states and [`weblisk server start`](#weblisk-server-start)
reads.

**The first operator is admitted by presenting the bootstrap secret the new
orchestrator emitted, and every later one needs that first one's approval**, per
[`architecture/admin`](admin.md#bootstrap-flow). `create` started the
orchestrator, so it reads the secret from where it was emitted and claims it in
the same action; nobody else can, because reaching the endpoint first confers
nothing.

**Security:** a tenant directory holds `.weblisk/keys/`, and creating one MUST
write the same `.gitignore` `weblisk new` writes — `.weblisk/secrets/`,
`.weblisk/keys/`, `.weblisk/token`, `.env`, `.env.*`. The rule was stated for
the scaffolder and not for the operation that produces the directory holding
the hub's ML-DSA private key, which is the one that needs it most. A tenant
with no `.gitignore` is one `git init` away from a committed private key, and
`weblisk doctor` correctly reports it as an error.

A tenant's `.gitignore` also excludes the runtime state a scaffolded application
never has: `.weblisk/bootstrap`, `.weblisk/data/` — which holds the gateway's
sessions, per [`architecture/storage`](storage.md) — `.weblisk/run/`,
`.weblisk/logs/` and `bin/`. It is written before generation, and a `.gitignore`
already present is amended, never replaced.

**Creating a tenant does not create a repository.** The ignore file is the
control: it makes the next `git init` safe, and it governs its own directory
just as well inside a repository that already encloses the tenant. A repository
adds no protection the file does not. What it would add is a decision that is
the operator's — where a tenant's source is versioned, and whether something
already versions it, in which case `git init` turns the tenant into a gitlink
and drops its files from the repository that was holding them.

The passphrase is read from stdin and never from argv, which every process on
the machine can read.

### `weblisk tenant accept`

Ask a running tenant whether it works, over HTTP, the way its clients will.

```bash
$ weblisk tenant accept
$ weblisk tenant accept --url http://localhost:9800 --gateway https://localhost:9443 --json
```

The same pass `create` ends with, so it can be re-run. Probes are
unauthenticated on purpose: the question is not *may I do this* but *does this
tenant serve this*, and the auth middleware answers that first — `401` is a
pass, `404` means the route is absent, `405` means the client and the tenant
disagree about the method. The first two probes are the orchestrator's
`GET /livez` and then its `GET /readyz`, which need no token and pass only on
`200`. The third is through the admin gateway, at the first origin
`orchestrator.admin_addresses` lists, or the one `--gateway` names:
`GET /v1/admin/overview` with no token, over
TLS verified against the pin `create` recorded, or, run in the tenant's
directory, the pin of the certificate the tenant's configuration names.
Where neither is to hand, run elsewhere against a gateway with no recorded
pin, it verifies under the system's roots and records nothing, as
`client-pins-gateway-key` in
[`architecture/admin`](admin.md#certificate) says, and an origin whose scheme
is not `https` it refuses before sending anything. It passes on `401`, the orchestrator's refusal carried back through the gateway,
and a certificate that does not match the pin fails it as a pin that did not
match, sending nothing over that connection, never as a refused connection. <!-- wl:id cli-accept-through-gateway --> Accept probes no
other component and reads no lease: whether each
registered component is present is a question for an operator's token, which
[`weblisk server verify`](#weblisk-server-verify) and
[`weblisk status`](#weblisk-status) ask.

A failed non-essential check does not fail the tenant. It is a capability that
tenant does not have, and **saying so is the point** — "created" must not mean
only that the generator returned without an error.

### `weblisk tenant export`

Write what this tenant is rebuilt from into a bundle. What that is, who holds
each part and why nothing else is in it is
[`architecture/tenancy`](tenancy.md#rebuilding-a-tenant)'s, and is not
restated here.

```bash
$ weblisk tenant export --out ../bundles/2026-10-29
```

| Flag | Description |
|------|-------------|
| `--dir <path>` | The tenant's directory. Default: the working directory |
| `--out <path>` | The bundle's directory. It must not exist |
| `--json` | One progress object per line, the last carrying the manifest's path and digest |

It runs on the tenant's host, with the tenant running, on the person's
operator token, which must carry the `admin` role
([`architecture/admin`](admin.md#operator-roles)): the bundle holds every
record the tenant keeps. It reads the configuration, the lock and the run
statements from the directory; the live components, the operators and every
repository with its log head through the admin gateway; runs
[`weblisk test conformance`](#weblisk-test-conformance) for the verdict at each
level; and captures each record store last, so that nothing the manifest names
is newer than what the bundle holds. It writes `manifest.json` last of all,
and a directory without one is not a bundle.

It never copies a private key, a passphrase, a store or a file generation
wrote. A key held only in `.weblisk/keys/`, and every generated file a person
edited, is named in `TenantManifest.unheld` and printed: the export succeeds,
and says what a rebuild from it will not bring back.

### `weblisk tenant rebuild`

Stand a tenant up again from a bundle, in the order
[`architecture/tenancy`](tenancy.md#the-rebuild-in-order) gives.

```bash
$ weblisk tenant rebuild ../bundles/2026-10-29 --dir ./tenant
```

| Flag | Description |
|------|-------------|
| `--dir <path>` | Where to rebuild it. It must be empty or absent |
| `--root <backend>=<path>` | A backend's root on this host, where it is not the one the configuration names. Repeatable. A placement never changes |
| `--keys <path>` | A directory holding the person's own copy of each key whose holder is `tenant-directory` |
| `--port <n>` | As [`weblisk tenant create`](#weblisk-tenant-create-name) takes it |
| `--json` | One progress object per line, one per step, the last carrying the comparison |

Its steps are a contract its progress objects name, as `create`'s are:

    bundle · corpus · files · keys · stores · records · generate · start · accept · done

Each step completes or the command stops there, refused, with nothing
started. `generate` builds each component as `create` and
[`weblisk component <name> init`](#weblisk-component-name-init) do, from the
blueprints at that component's pin, read from a clone at that revision and
never from a source's `HEAD`; the refresh rules of
[Where blueprints come from](#where-blueprints-come-from) do not move it.
`accept` exports the rebuilt tenant and compares the two manifests
([`architecture/tenancy`](tenancy.md#a-rebuild-is-accepted-when)), and only a
comparison that finds nothing ends in `done`.

Every passphrase is read as `create` reads one, from stdin and never from
argv.

#### Tenant export and rebuild codes

Both commands refuse with these, printing the code and, with `--json`, giving
it as the last object's `code`. Each exits with the status in
[Exit Codes](#exit-codes) that its row gives.

| Code | Exit | Refused when |
|------|------|--------------|
| `TENANT_BUNDLE_EXISTS` | 1 | `export`'s `--out` already exists. Nothing is written |
| `TENANT_PIN_DIRTY` | 1 | `export` finds a component built from a corpus revision carrying `-dirty`, which no commit reproduces ([`weblisk server init`](#weblisk-server-init)). It names the component |
| `TENANT_RECORDS_UNCAPTURED` | 1 | `export` cannot capture a service's record store at a consistent point, because the store does not offer `backup-restore` ([`architecture/storage`](storage.md#contracts)). It names the service |
| `TENANT_MANIFEST_INVALID` | 1 | `rebuild` finds no manifest, one that is not a `TenantManifest`, or a bundle file whose digest is not the manifest's |
| `TENANT_REBUILD_NOT_EMPTY` | 1 | `rebuild`'s `--dir` holds anything |
| `TENANT_PIN_UNAVAILABLE` | 3 | A source a pin names cannot be reached, or does not hold the revision |
| `TENANT_KEY_UNAVAILABLE` | 1 | A key the manifest names is not at its holder, or its fingerprint is not the manifest's. No key is minted in its place |
| `TENANT_STORE_MISMATCH` | 1 | A repository's store is absent at its placement, is not on its line, or its line is not at the manifest's head. No store is adopted in its place |
| `TENANT_RECORDS_UNRESTORED` | 1 | A record store cannot be restored from the bundle |
| `TENANT_REBUILD_DIFFERS` | 1 | The rebuilt tenant's manifest differs from the bundle's in a row the comparison holds. Each row is printed with both values, and the tenant is left as it is |

### `weblisk providers`

List the model backends this machine offers for the CLI's own model, which
[`architecture/orchestrator`](orchestrator.md#administrative-endpoints) bounds,
and say which one it would start with. It neither reports nor changes a
tenant's model.

```bash
$ weblisk providers
$ weblisk providers --json
```

**A listing, not a test.** It asks no backend to generate. A mark means the
backend can be tried — its binary runs, its server answers or is configured, or
the key it needs is present — and that is all it can mean: a coding-agent CLI
that is not logged in prints its version as readily as one that is. When nobody
named a backend, a build settles it by asking the one it starts with to answer
once before anything is generated, and moves down the ranking past one that
cannot — see [`weblisk tenant create`](#weblisk-tenant-create-name). A backend
somebody named, with `--provider` or `WL_AI_PROVIDER`, is asked nothing first
and is never passed over for another.

`--json` prints an array, one object per backend:

| Field | Meaning |
|---|---|
| `kind` | the backend, spelled as `--provider` and `WL_AI_PROVIDER` take it |
| `label` | what a person calls it |
| `available` | it can be tried, as above. Never a statement that it will generate |
| `detail` | how it was found, or what is missing. Never empty: an unavailable backend with no reason cannot be acted on |
| `path` | the resolved binary, for a backend that is a program on this machine |
| `needs_key` | for a keyed backend, the environment variable it names for its key. `WL_AI_KEY` also serves, and outranks it, and a vendor that spells its variable two ways has the second read too |
| `local` | `true` only for a model server on this machine's loopback address, judged from the address's host and never from its text. A coding-agent CLI runs here and sends the work to its vendor, a `WL_AI_COMMAND` tool is not known either way, and an Ollama or an OpenAI-compatible server at another host is another machine — all `false`. It is what a person deciding where their data may go reads, so it is never claimed on a guess. It says where the server answers, not whether that server passes a model on to another host |
| `default` | `true` on the one backend the CLI's own model would start with, with `why` beside it. At most one object carries it, and none does when there would be nothing to start with |

**The default is marked by the CLI, never inferred by the caller.** A console
that picks "the first available one" from the list has reimplemented the ranking,
and two rankings agree only until one of them changes. When `WL_AI_PROVIDER`
names a backend, that backend is the one marked — or none is, if it is not
available — because the CLI takes it and falls back to nothing. Otherwise the
mark is on the highest-weighted backend available here, the first of the
ranking a build moves down.

### `weblisk component <name> init`

Generate one component into a tenant that already exists.

```bash
$ weblisk component content init
  Weblisk Component Init — content
  Mode:      amending an existing tenant
```

Which components exist is read from the installation's blueprints, not compiled
in: an architecture blueprint that states an `## Endpoints` table and declares
its bindings IS a buildable component. `weblisk component help` lists what this
installation supports, and `admin`, the admin gateway
([`architecture/admin`](admin.md#the-admin-gateway-as-a-component)), is among
them: `tenant create` builds it, and `weblisk component admin init` builds it
into a tenant that has none, making `.weblisk/keys/` and the gateway's two
keys as `gateway-keys-kept` says, the tenant's `.gitignore` written or amended
first ([`architecture/admin`](admin.md#registration-lease-and-identity)). Into
a running tenant, it reports that the orchestrator admits the gateway once
restarted, because the orchestrator reads the gateway's identity when it
starts.

The tenant root is the module root, so every component is generated into the
same tree. Generation therefore reads what the tenant already contains — module
path, packages present with their exported names, and which component owns which
file — and REFUSES a plan that names another component's files. See
[`architecture/generation`](generation.md#deciding-whether-a-file-must-be-rebuilt).

A build that repairs ends on the best tree it reached, as
[`architecture/generation`](generation.md#a-repair-round-is-a-transaction)
specifies, which also says where `weblisk` does not yet rank or judge a tree as
it specifies. What is the command's: when the repair loop ends without an
error of its own, it prints the verdict on that tree first, that it does not
build, with the build's output, or what conformance established, and then each
requirement left unrepaired and why, cutting the list for each source short at
twelve with a count of the rest. When the loop ends on an error, such as a
provider failure or a failed write, or ends on a best tree whose dependencies
do not resolve, it prints that list and the error and no verdict. A provider
failure the run can outlast is resumed rather than ended
([`architecture/generation`](generation.md#surviving-a-provider-outage)), and
a resumed run that finishes prints its verdict.

### `weblisk component <name> start` · `stop` · `status` · `logs`

Run one component of a tenant — any kind the tenant has generated, not only the
four that have verbs of their own.

```bash
$ weblisk component content start --detach
$ weblisk component agent start billing --detach --port 9720
$ weblisk component content status --json
$ weblisk component content stop
```

| Flag | Description |
|------|-------------|
| `--detach` | Run in the background and record it, as `server start --detach` does, so `status`, `logs` and `stop` find it |
| `--port <n>` | Listen port. Omitted: what `.weblisk/config.yaml` declares for this component, else the convention [`schemas/config`](../schemas/config.md) gives it. A kind with a range rather than a port — an agent, a domain — must be given one |
| `--orch <url>` | The orchestrator's own address, to register with, never the admin gateway ([Configuration](#configuration)). Omitted: the one this CLI has running for the tenant |

A kind a tenant may hold several of takes the instance's name after the verb.
With no orchestrator named and none running, the component is started without
one and the command says so: [`architecture/content`](content.md) requires the
content service to start standalone and answer `GET /readyz` not ready, and an
invented address would have it register with nothing and exit.

**Started means answering.** A detached start waits until the component's
`GET /livez` answers live, and then until its `GET /readyz` answers ready
([`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz)). A component
that exits or never answers live is reported with what it last wrote — a
process id alone is not a started component — and one that is live and never
ready is reported as started and not ready, with its `/readyz` answer, since
a component may be not ready by design: the content service started with no
orchestrator is ([`architecture/content`](content.md)).

#### A component starts with a clean environment

This rule has one home, here, and covers every path by which the CLI starts a
tenant component: this command,
[`weblisk server start`](#weblisk-server-start), the orchestrator that
[`weblisk tenant create`](#weblisk-tenant-create-name) starts,
[`weblisk agent start`](#weblisk-agent-start),
[`weblisk domain start`](#weblisk-domain-start),
[`weblisk gateway start`](#weblisk-gateway-start), and
[`weblisk dev`](#weblisk-dev) running a hub, both its first run and each
restart it makes. That restart is the CLI's only one: there is no restart
command, and one added later is a start under this rule. It covers the starts a
build makes of a component it has just generated as well, a repair round's
among them: the run that conformance-tests a tree
([`architecture/generation`](generation.md#what-a-repair-round-reads-and-in-what-order))
and the run beside a real orchestrator
([`architecture/testing`](testing.md#level-4-interoperability)). A tested start
is therefore made as a real one is, and a component that works only because it
inherited something fails its tests instead of passing them. What a coding-agent
provider does inside its own tool loop is not one of these: where a provider
CLI builds or runs the tree it is writing, it does so with the environment the
provider CLI has ([Security](#security), CLI → Provider CLI), which this rule
does not govern. The tested start this rule makes equal to a real one is the
CLI's own.

**Nothing is inherited.** The environment is built from nothing, never by
removing names from the starter's. Who started the CLI — a person's shell,
Studio, a service manager — and what they hold reach no component. The CLI
gives a component exactly the names below; a run command that is itself a
program, as npm is, may add its own (a start through npm, below):

1. **The allow-list below**, each name copied from the CLI's environment where
   it is set there, and no other name copied.
2. **The values the CLI sets for that run**, computed and never copied:
   `WL_PORT`, the port it passes; for a component other than the
   orchestrator, where an orchestrator is named by `--orch` or recorded in
   the tenant's run state as running, `WL_ORCH_URL`, that orchestrator's own
   address, which the component registers with, passed as well as `--orch`
   in its arguments, so a component reading either finds it
   ([`languages/go`](../languages/go.md#environment-variables)). Where none
   is named or running, neither `WL_ORCH_URL` nor `--orch` is set on a real
   start: the component starts without one, as
   [`weblisk component <name> start`](#weblisk-component-name-start--stop--status--logs)
   says. A conformance run of a tree alone names no real orchestrator
   either, and for a component that, given none, registers with none, it is
   such a start. A component whose configuration gives the address it
   registers at a default, as
   [`schemas/config`](../schemas/config.md#schema-definition) gives
   `admin_gateway.orchestrator` one, has an orchestrator even when none is
   named: started with neither, it registers at that default, which on the
   host a tenant is built on is the tenant's own, and a build's test run
   would hold a namespace the tenant's real component is then refused. On a
   build's own runs, such a component, with no orchestrator of the run's
   own, is given in both `WL_ORCH_URL` and `--orch` a loopback address the
   CLI binds for the length of the run, holds until the component has
   exited, and answers no request at, closing each connection, so what the
   component meets is the transport failure its default gives it where no
   orchestrator runs and never the tenant's orchestrator. A component that
   registers with none is given no such address: its registration would
   fail, which [`languages/go`](../languages/go.md#error-handling) makes
   fatal, and it would exit before it was tested. And, on a
   build's own runs only, `WL_DEV=1`, which starts a fresh component with no
   persistent store and has it say so. That one value is the only difference
   between a tested start's environment and a real one's. A tested start
   differs in one other thing, where it runs: a build's own runs start the
   component in an empty working directory made for that run and removed
   after it, never the tenant's root, so what a fresh component writes on its
   first start — a development-only key, a development store — never lands
   beside the tenant's own state, where a production start would find a key
   it must refuse. An address is not a secret: it
   names where to register, and registering proves identity separately
   ([`protocol/identity`](../protocol/identity.md)). It stays one: an
   `--orch` that carries a user or a password before its host
   (`http://user:password@host`) is refused before anything is built or
   started, and the address the run state records is the CLI's own, which
   carries neither. And, for a component whose run command is npm's,
   `npm_config_userconfig` and `npm_config_globalconfig`, as a start
   through npm (below) says.
3. **What is declared for that component**: its entry's `env` in
   `.weblisk/config.yaml`, which today only an agent has
   ([`schemas/config`](../schemas/config.md#agents)) and which may hold no
   secret. A variable a blueprint documents for its component, such as a
   language blueprint's environment table, gets a value only from that
   declaration, never from whoever started it.

**No file puts back what the start left out.** A component generated
before [`languages/go`](../languages/go.md#configuration) and
[`languages/rust`](../languages/rust.md#configuration) 2.0.0 may load a
`.env` file from its working directory, which neither now asks of it;
common loaders on the node platform read `.env` and also `.env.local`,
`.env.development` and their like; and `wrangler dev`, which a cloudflare start runs
([`platforms/cloudflare`](../platforms/cloudflare.md)), gives the Worker the
variables in `.dev.vars` and the `[vars]` of its wrangler configuration,
never the process environment. A component the CLI starts works in its
tenant's root, where such a file is expected to sit (the `.gitignore`
[`weblisk tenant create`](#weblisk-tenant-create-name) writes excludes
`.env` and `.env.*`). So every start above, and each of a build's own runs,
is refused, naming the file, while the directory the component would start
in holds `.env`, any `.env.*` but `.env.example` (which holds names and no
values, as [`architecture/data-security`](data-security.md) exempts it), or,
on the cloudflare platform, `.dev.vars` or any `.dev.vars.*`; and a
cloudflare start is refused, naming each entry, where its wrangler
configuration's `[vars]` holds one that rule 16 of
[`schemas/config`](../schemas/config.md#validation-rules) recognises as a
secret, judged as an `agents[].env` entry is. Otherwise a vendor key written
there reaches the orchestrator after all. Move what such a file holds into a
declaration, or into the tenant's secret store. A cloudflare component
started by this CLI therefore has no Workers Secret, which `wrangler dev`
supplies only from `.dev.vars`; one it needs reaches it on a hosted
deployment, below.

**`HOME` is absent, and nothing replaces it.** Neither it, nor `USERPROFILE`,
`APPDATA` or `LOCALAPPDATA`, its Windows counterparts, is on the list. A
generated component must not depend on finding a home directory: Go's
`os.UserHomeDir`, `os.UserConfigDir` and `os.UserCacheDir` read only those
variables and return an error without them, and a runtime that falls back to
the operating system's user database, as Node's `os.homedir()` does, reads
the account the component runs as, which is not inheritance but is not the
component's state either. A component's state lives under its tenant's root.
Setting `HOME` to make a run command work puts it back on the list, which
only a change to the table below may do. npm sets it itself for a component
it runs, as a start through npm (below) says; the CLI does not.

**A start through npm gets npm's configuration from the tenant.** A node
component's run command is `npm start`
([`platforms/node`](../platforms/node.md)), so npm runs between the CLI and
the component, and npm reads configuration from files the environment does
not name. With `HOME` absent it still finds the starting account's `~/.npmrc`
through Node's `os.homedir()`, which falls back to the account's entry in the
user database, and it reads the global `npmrc` under Node's install prefix;
and it exports what it reads into the component's environment, as
`npm_config_*` names, among them a proxy with its user and password, and
turns a `node-options` entry into `NODE_OPTIONS`, which can load any code
into the component. So a start whose run command is npm's, and each of a
build's own runs of one, is also given `npm_config_userconfig` and
`npm_config_globalconfig`, computed and never copied, each naming a file under
the tenant's root that the tenant owns and nothing has written to — the same
two a build of it is given (below). Neither the account's `~/.npmrc` nor the
global `npmrc` then reaches the component.

npm still reads two files those do not name: the `npmrc` inside npm's own
install, which is the toolchain's and not the starter's, and the `.npmrc` in
the component's own directory, which is generated output like the rest of
the tree. And npm adds names of its own that the table below does not list:
`npm_config_*` for the configuration it holds, `npm_package_*` from the
package's `package.json`, `npm_lifecycle_event`, `npm_lifecycle_script`,
`npm_command`, `npm_execpath`, `npm_node_execpath`, `INIT_CWD`, `NODE` and
`EDITOR` among others, and `node_modules/.bin` at the front of `PATH`. npm computes each from its
defaults, those files, the package and the directory, some of them paths
under the account's home that npm finds as it found `~/.npmrc` (its cache
among them); none is copied from the environment of whoever started the
CLI. One of them is `HOME`: npm always sets it for the script it runs, to
the `HOME` it was given or, with none, to Node's `os.homedir()`, so a node
component started through npm has `HOME` naming the home of the account the
CLI runs as, though the CLI gave it none. That is the account's directory,
found as a build finds it (below), not a value of the starter's environment,
and it is the one name on the "off it on purpose" list below that a
component can hold; a component's state still lives under its tenant's
root, not there. For a node component, "nothing is inherited" means exactly
that: npm's names reach it, and the starter's do not.

**Building is not starting, and gets the same environment.** Every build
the CLI makes of a tenant component's code is under this rule, whichever
command makes it: the build a start above makes before it runs the
component, the orchestrator's and the admin gateway's builds in
`weblisk tenant create`, each build
`weblisk dev` makes, and generation's own build of a target, in
[Layer 2](generation.md#layer-2--coherence) and in every repair round.
Generated output is
untrusted ([Generated output is untrusted](#generated-output-is-untrusted)),
and a build runs some of it (a `build.rs`, an install script), so every such
build gets the allow-list below and the run's values too, never the CLI's
environment, plus the toolchain's own directories. Go refuses to build with
neither `GOCACHE` nor a home. Two of those directories are always computed
under the tenant's root and never copied, because each is where a toolchain
reads a registry's tokens through the account's home even with `HOME`
absent: `CARGO_HOME`, where cargo keeps `credentials.toml`, and
`npm_config_userconfig`, the `.npmrc` npm otherwise finds through Node's
`os.homedir()`, which falls back to the account's entry in the user
database. `npm_config_globalconfig` is computed there too, for the global
`npmrc` npm otherwise reads under Node's install prefix. Each names a
directory or file the tenant owns and nothing has written to, so cargo and
npm start a build with no registry token. The rest
are a default install's: `GOCACHE`, `GOMODCACHE` and `GOPATH` for Go,
`RUSTUP_HOME` for Rust and `npm_config_cache` for npm are each copied from
the CLI's environment where set there, and otherwise computed where that
toolchain computes its own default, from the home directory of the account
the CLI runs as (its `HOME`, `USERPROFILE` on Windows, else the user
database): `GOPATH` is `<home>/go`, `GOMODCACHE` is `<GOPATH>/pkg/mod`,
`GOCACHE` is `go-build` under the user cache directory Go's
`os.UserCacheDir` names, `RUSTUP_HOME` is `<home>/.rustup`, and
`npm_config_cache` is `<home>/.npm` (`npm-cache` under `LOCALAPPDATA` on
Windows). The home itself is never passed. `RUSTUP_HOME` in particular is
not a cache: it holds the installed toolchains and the default one, so an
empty one stops every Rust build on a default rustup install. Each of those
holds build output, downloaded modules or installed toolchains and no
credential: Go reads a module host's credentials from `.netrc` under `HOME`
or from `GOAUTH` and `NETRC`, none of which is passed, and rustup keeps no
token. They reach the build step and never the component it builds.

What this does not prevent, said plainly: it governs the environment, not
the filesystem. A build runs as the account that started the CLI and reads
and writes what that account can — `~/.npmrc`, `~/.cargo/credentials.toml`
and the shared toolchain directories above among them — if code it runs
opens them by path. Cargo also reads `.cargo/config.toml` from every
directory above the one it builds in, so a tenant root under a home
directory reads that home's `.cargo/config.toml`; a token belongs in
`credentials.toml`, which only `CARGO_HOME` locates. npm still reads the
`npmrc` inside its own install and the component's own `.npmrc`, as a
start through npm (above) says. Keeping a build away from the
account's files is a matter of the account it runs as, which this section
does not change.

| Name | Why its value carries no secret | Why a component needs it |
|---|---|---|
| `PATH` | a list of directories | a run command such as `npm start` ([`platforms/node`](../platforms/node.md)) is found through it |
| `LANG`, `LC_ALL`, `LC_COLLATE`, `LC_CTYPE`, `LC_MESSAGES`, `LC_MONETARY`, `LC_NUMERIC`, `LC_TIME` | a locale name, such as `en_CA.UTF-8` | text encoding and formatting; without them a runtime falls back to the `C` locale. Each is named, never `LC_*`, so a variable that only begins with `LC_` is not passed |
| `TZ` | a time-zone name | the zone the host's clock is read in |
| `TMPDIR` | a directory path | where a runtime writes temporary files |
| `SystemRoot`, `TEMP`, `TMP`, `PATHEXT` (Windows only, matched without regard to case, as Windows matches them) | directory paths, and a list of file extensions | Go's runtime and network stack need `SystemRoot` on Windows; the others are `TMPDIR` and `PATH`'s counterparts there |

The list is closed: a name joins it by a change to this table that says why
its value can carry no secret, never by a setting. A name a component does not
need stays off it, secret or not. Some are off it on purpose:

- **Every vendor key variable, for every component, the orchestrator
  included**: `WL_AI_KEY` and each variable a model backend names for its key
  (`needs_key`, [`weblisk providers`](#weblisk-providers)). No tenant component
  starts holding one, so a backend that needs a key does not run in a tenant
  the CLI starts, which the model gateway already says of itself
  ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)). A
  declaration that names one is refused (below).
- **`WL_AI_PROVIDER`, `WL_AI_MODEL` and `WL_AI_COMMAND`.** They choose the
  CLI's own model ([`weblisk providers`](#weblisk-providers)). A tenant's
  model is the tenant's configuration
  ([`architecture/orchestrator`](orchestrator.md#the-tenants-model)), kept in
  the hub's `.weblisk/model.json` and never in the environment of whoever
  started it. No language or platform file has a component read a
  provider, a model name or a key from its own environment.
- **`HOME`, `XDG_CONFIG_HOME` and every other name for the starter's own
  directories.** They lead to where that person's identities, logins and
  cloud credentials are kept. A component's state lives under its tenant's
  root.
- **`SSH_AUTH_SOCK` and every other agent socket.** The value is a path, but
  what answers there signs as the person.
- **`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` and `NO_PROXY`, in either case.**
  A proxy address may carry a user and password. A component that must reach
  out through a proxy has it declared.
- **`SSL_CERT_FILE`, `SSL_CERT_DIR` and `NODE_EXTRA_CA_CERTS`.** Their values
  are paths and carry no secret, but they replace or extend what a component
  trusts, and that is not the starter's to choose: whoever started the CLI
  could have every component accept a certificate they issued. A host with a
  private certificate authority installs it in the host's trust store, which
  every runtime reads with no variable set; a component that must use another
  bundle has it declared.

A declared `env` entry that rule 16 recognises as a secret — by its name, by
a published vendor key prefix, or by a value shaped as a credential — is
refused, with every entry that does, before anything is generated or started: by the commands that generate a
component from the declaration, and by every start above
([`schemas/config`](../schemas/config.md#validation-rules) rule 16). A component
that needs a secret reads it through its secret client from the tenant's store
([`patterns/secrets`](../patterns/secrets.md#secret-access-api)), never from an
environment the CLI gives it, which every process it starts inherits and which
crash dumps and `/proc` expose ([`protocol/identity`](../protocol/identity.md)
rule 9). A component this CLI starts therefore has no secret in its
environment for the `environment` backend of
[`patterns/secrets`](../patterns/secrets.md) to read. A platform that starts a component itself, on a hosted deployment, is
not a start by this CLI, and what it may inject is stated in
[`patterns/secrets`](../patterns/secrets.md#deployment-secret-delivery).

---

### `weblisk server init`

Generate the server implementation from blueprint specs. The CLI reads
`.weblisk/config.yaml`, `domains/*/domain.yaml`, and
`agents/*/agent.yaml`, then dispatches to the configured LLM along
with the platform blueprint to generate the implementation.

**Generation MUST NOT require a hosted account.** Standing up a first hub is the
entry point to the whole framework, and putting a paid API key in front of it
makes the framework unusable to anyone evaluating it, unusable offline, and
unusable where data policy forbids sending source to a third party. The provider
set therefore includes backends that run entirely on the operator's machine:

| `WL_AI_PROVIDER` | Transport | Requires |
|------------------|-----------|----------|
| `claude-code` | local subprocess | Claude Code installed; uses its own login |
| `ollama` | local HTTP | Ollama running |
| `local-cli` | local subprocess | any tool, via `WL_AI_COMMAND` |
| `openai`, `anthropic`, `cloudflare` | hosted HTTP | `WL_AI_KEY` |

Local CLI backends are a subprocess, not an endpoint: there is no base URL and no
key, and the credential is whatever the tool is already authenticated with.
Implementations MUST resolve such a binary by searching the usual install
locations as well as `PATH` — a process started by launchd, systemd or an editor
does not inherit a login shell's PATH, and reporting "not installed" for a tool
the operator is using in another window is a diagnosis nobody can act on.

The provider that generated a hub, and the blueprint version it generated from,
are part of that hub's provenance and MUST be recorded.

**Recorded, not printed.** It was printed, so a generated hub carried no
statement of what governed it and the question had to be reconstructed from a
terminal scrollback. Provenance MUST be written into the artifact's own state —
alongside the record of which files were generated — and MUST carry the time,
each blueprint source with its revision, and the model the provider reported
using.

**A revision MUST say when the corpus was not clean.** A tenant was generated
from a working tree with thousands of uncommitted lines and the run recorded
`@79a5280` — a commit the content did not come from. An auditor who checks that
commit out gets a different corpus and cannot reproduce the artifact, which is
the one thing a provenance record exists to make possible.

Uncommitted tracked changes and untracked files both count: a blueprint nobody
has added yet still reached the model. The revision MUST carry a `-dirty`
suffix in that case, and the run MUST say so where it prints the source, before
generating rather than after.

A revision that is wrong is worse than a revision that is absent, because it is
acted on.

**The model MUST be recorded as the provider reported it, not as configured.**
An unset model means "the tool's default", and a tool's default is not a
constant — so the only trustworthy answer comes from the response. Where the
provider said nothing, the field is empty: "the provider did not say" and
"nobody asked" are different facts.

#### Generated output is untrusted

A model's response is data, not instruction, and **the file paths inside it are
attacker-influenced input**. Blueprints are the generator's instructions and a
hub adopts them from a marketplace, so an untrusted blueprint is untrusted input
to a code generator: prompt injection there is a file-write primitive, and a
write to a VCS hook directory or a shell profile is code execution on the
operator's machine. A merely mistaken path is no better — it destroys a key store
just as thoroughly.

Implementations MUST therefore:

1. Reject any generated path that is absolute, or that contains a `..` segment.
2. Verify the resolved path lies inside the target directory, comparing cleaned
   absolute paths with a separator appended so that `server-old` is not treated
   as inside `server`.
3. Refuse any path naming a location that carries authority — `.git`, `secrets`,
   `keys`, `.ssh`, `.env`, `.weblisk` — even when it is nominally inside the
   target.
4. Re-check containment after directory creation, because a symlinked directory
   inside the target can point anywhere.
5. Validate EVERY path in a response before writing ANY file. A generation that
   attempted to escape must not be partially applied.

The generator MUST NOT be given filesystem tools, the operator's MCP servers, or
session state. It receives blueprints and returns text; the CLI writes the files.
A generator that can write directly has no boundary between "generate a hub" and
"do anything to this machine".

The generator MUST NOT be given secrets, key material, or tenant content. It
needs blueprints and a platform specification, and nothing in `.weblisk/secrets/`,
`.weblisk/keys/` or a tenant's documents is an input to generating a hub.

```bash
$ weblisk server init --platform go
$ weblisk server init --platform cloudflare
$ weblisk server init --platform node
```

| Flag | Description | Status |
|------|-------------|--------|
| `--platform <p>` | Target platform: `go`, `cloudflare`, `node`, `rust` (default: `go`) | implemented |
| `--verify-signatures` | Require all blueprint files to be from signed Git commits | refused — see below |
| `--allowed-signers <file>` | Path to allowed signers file (SSH) or keyring (GPG) | inert without the above |
| `--encrypt-keys` | Encrypt generated service keys at rest | refused — see below |
| `--verify-only` | Report blueprint changes without generating (for CI) | refused — see below |

> **Not implemented.** The CLI refuses `--verify-signatures`, `--verify-only`
> and `--encrypt-keys` rather than accepting them. All three were parsed,
> discarded, and followed by a line claiming the work had been done —
> `--verify-signatures` printed "✓ Blueprint signatures verified" after
> ignoring its own result, `--verify-only` printed "✓ No breaking changes
> detected" without reading a blueprint, and the banner said "Keys:
> encrypted at rest" while `--encrypt-keys` reached nothing.
>
> The signatures flag is why this is a refusal and not a TODO: of 86
> blueprint commits 50 carry an SSH signature and none is verifiable,
> because no allowed_signers file exists and `gpg.ssh.allowedSignersFile`
> is unset at every scope. Git reports an uncheckable SSH signature as
> "N", which is indistinguishable from unsigned. A governance product
> cannot ship a control that reports success without performing it.
>
> The requirement below stands. What is removed is the claim that it is
> already met.

### `weblisk server start`

Build (if needed) and start all hub components.

```bash
$ weblisk server start
$ weblisk server start --detach
$ weblisk server stop
```

Reads `.weblisk/config.yaml` to determine which components to build and start,
per [`schemas/config`](../schemas/config.md). A section that is present
declares its component — `content:` declares the content service — and an
absent or null one declares none. With no file it starts the orchestrator
alone: the file is an operator's declaration, never a precondition. That is a
hub with no door, not a tenant, whose minimum set is the orchestrator and the
admin gateway ([`architecture/tenancy`](tenancy.md#data-flow)), and start says so: no person's client reaches it until a
configuration declares the admin gateway rule 20 of
[`schemas/config`](../schemas/config.md#validation-rules) requires, which
`weblisk component admin init` writes. A file that is present and fails rule
20, having no `admin_gateway` section, is a declaration start cannot carry
out, and is refused whole as below, naming `weblisk component admin init`:
the orchestrator alone is what an absent file means, never what a present one
that omits the door means.

- **Order.** The orchestrator first, and each sibling only once the
  orchestrator's `GET /livez` answers live and then its `GET /readyz` answers
  ready, passed `--orch` with the address it actually bound, as an IP
  literal and never `localhost`, which the admin gateway would refuse
  (rule 19 of [`schemas/config`](../schemas/config.md#validation-rules)).
  The admin gateway next, which `admin_gateway` declares, passed its
  internal listener's port as `--port` and `WL_PORT` and waited on there
  ([`architecture/admin`](admin.md#a-start-and-a-builds-own-run),
  `gateway-port-is-internal`). Then the content
  service, domains, agents, and the application gateway last.
- **Certificate.** Before it starts the admin gateway, it makes a new
  certificate from the gateway's own TLS key where the certificate the CLI
  made has fewer than 30 days left, so its pin holds. A certificate the
  configuration names it serves as it is, and never renews
  ([`architecture/admin`](admin.md#certificate), `given-certificate-served`).
- **Refused whole.** A declaration this command cannot carry out — two
  components on one port or one name, `replicas` above 1, an agent with no
  `type`, a file with no `admin_gateway` section, an agent `env` entry that rule 16 of
  [`schemas/config`](../schemas/config.md#validation-rules) recognises as a
  secret, a variables file where a component would start ([A component starts
  with a clean environment](#a-component-starts-with-a-clean-environment)) — is refused with every reason
  before anything starts. Starting part
  of a declaration leaves a tenant in a state nobody declared.
- **Named, not skipped.** A declared component that has not been generated is
  reported with the command that generates it, the rest start, and the command
  exits non-zero. A tenant running less than it declares is not started.
- **Passphrase.** A component whose section names `key_passphrase`
  ([`schemas/config`](../schemas/config.md#service-key-passphrases)) is given
  its key's passphrase on its standard input when it starts, as one line ended
  by a line feed, and its standard input is then closed. The CLI gets it from
  the named source with `get` — `field: "passphrase"` where the source lists
  `named_fields`, and no field otherwise
  ([`protocol/secret-source`](../protocol/secret-source.md#actions)) — once for
  each distinct reference, before anything starts, so a source that asks a
  person asks once. It is never placed in an argument, an environment variable
  or a file, and is zeroised once every component that needed it has read it
  ([`protocol/identity`](../protocol/identity.md#key-categories) rules 4, 9 and
  10). A source that does not answer refuses the start whole, as above,
  reported as [`protocol/secret-source`](../protocol/secret-source.md#reporting-a-source-that-did-not-answer)
  says; nothing is started with a passphrase missing. A component with no
  `key_passphrase` is given nothing on its standard input. The same holds for
  every start of a component this document lists under
  [A component starts with a clean environment](#a-component-starts-with-a-clean-environment). <!-- wl:id start-injects-passphrase -->
- **Clean.** Each component, the orchestrator first among them, starts with
  the environment [A component starts with a clean
  environment](#a-component-starts-with-a-clean-environment) gives it and
  nothing of whoever ran this command, attached or detached alike.
- **Foreground** stays attached to what it started, each component's output
  prefixed with its name. Interrupting it stops them in reverse order; a
  component that exits ends the session and stops the rest.

`weblisk server stop` with no `--component` stops every component this CLI has
a record of, siblings before the orchestrator, so nothing is left registered
with a registry that has gone.

### `weblisk server verify`

Verify the server is running: the orchestrator's `GET /livez` answers live and
its `GET /readyz` ready. Those two decide the verdict, and no other component
is probed. Every registered component's lease state is then read from
`GET /v1/admin/agents` on the operator's token (each entry's `lease_state`,
[`architecture/admin`](admin.md#agent-management)) and reported beside the
verdict, and none of them fails it: a lease reading
`not_ready` is reported as not ready, since a component may be not ready
by design ([`weblisk component <name> start`](#weblisk-component-name-start--stop--status--logs)),
and one reading `unknown` is reported as unknown, never as down. Run with no
operator token, or one the admin API refuses, verify still gives its verdict
and says the lease states were not read, never that there are none.

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
| `--platform <p>` | Target platform: `go`, `cloudflare`, `node`, `rust` (default: `go`) |

### `weblisk agent start`

Build and run a single agent.

```bash
$ weblisk agent start seo
$ weblisk agent start seo --orch http://localhost:9800 --port 9710
```

| Flag | Description |
|------|-------------|
| `--orch <url>` | The orchestrator's own address, which the agent registers with — never the admin gateway an operator command's `--orch` names ([Configuration](#configuration)) |
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
$ weblisk domain create seo --from marketplace
```

| Flag | Description |
|------|-------------|
| `--platform <p>` | Target platform: `go`, `cloudflare`, `node`, `rust` (default: `go`) |
| `--from marketplace` | Generate from a purchased marketplace asset |

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
| `--platform <p>` | Target platform: `go`, `cloudflare`, `node`, `rust` (default: `go`) |

### `weblisk gateway start`

Build and run the application gateway.

```bash
$ weblisk gateway start
```

---

### `weblisk server provision`

Establish a tenant's FIRST operator against a hub this CLI started.

```bash
$ weblisk server provision --operator alice
  Operator passphrase: ********

  orchestrator running at http://127.0.0.1:9800
  operator identity created for alice
  operator registered — bootstrap secret claimed, first operator is admin
  registered at the admin gateway https://localhost:9443 (pin sha256:4b1f…)
```

This is BOOTSTRAP, not connect. It is local by necessity — it reads the run
state of a hub this CLI started, and the bootstrap secret that hub emitted — and
it is the one path that establishes a hub's first operator. It registers that
operator at the orchestrator's own address, the one the run state names,
presenting the bootstrap secret, which is no token. It keeps no token and
records nothing for that address: it discards the attestation token the
first registration answers with, because every request that would use one
goes to the hub's admin gateway, and the address the CLI records for a hub is
that gateway's, never the orchestrator's (`orchestrator_url`). It then
registers at the admin gateway, at its origin in
`orchestrator.admin_addresses`, verifying its certificate against the pin of
the certificate the tenant's configuration names (`admin_gateway.tls_cert`, or
its default), read from this host's disk as
[`weblisk tenant accept`](#weblisk-tenant-accept) reads it and never from the
connection, as [`weblisk operator register`](#weblisk-operator-register)
does: the hub already knows the operator, so it answers the registration as a
repeat, and the CLI records the registration, with the pin, at the gateway's
address alone. <!-- wl:id cli-provision-registers-at-gateway --> A
configuration with no `admin_gateway` section fails rule 20 of
[`schemas/config`](../schemas/config.md#validation-rules): provision reports
that the hub has no door to connect at, and records nothing.

Generation is deliberately not folded in. It takes tens of minutes, streams
progress and is resumable; wrapping it in a call that also handles a credential
would make one action out of two very different failure modes, and would hold a
passphrase in memory for the length of a build.

---

## Blueprint Commands

### Where blueprints come from

Every command that reads blueprints resolves them from one ordered list of
sources, judged from the directory the command works in, and the first source
that holds a file is the one read. That directory is the working directory,
except for a command that works in a directory of its own, as
[`weblisk tenant create`](#weblisk-tenant-create-name) works in the tenant's
(`--dir`):

| Order | Source | Read from |
|---|---|---|
| 0 | **A corpus** — the directory the command works in, when it holds `schemas/common.md` and at least one of `architecture/`, `protocol/`, `patterns/` or `agents/` | the working tree, in place |
| 1 | **The project's own** `blueprints/` directory, in the directory the command works in | the working tree, in place |
| 2 | **Custom sources** — the repositories `WL_BLUEPRINT_SOURCES` names, comma-separated, in that order: each entry an address or a path that `git clone` is given whole, and read at its `HEAD` | a clone in `~/.weblisk/blueprints/` |
| 3 | **Core** — this repository, always present as the fallback | a clone in `~/.weblisk/blueprints/` |

**Step 0 exists because without it the CLI checked somebody else's work.**
`weblisk validate` run inside a blueprint repository examined the cache — a clone
of the remote — and not the files in front of it: an edit that added a binding
was in the working tree and not in what was validated, and the finding count
was the same before and after the edit. The detection is narrow on purpose.
`schemas/common.md` is this corpus's own root document, while a lone
`architecture/` directory is a shape plenty of unrelated repositories have, and
reading a stranger's markdown as a specification is worse than reading none.

**Standing in a corpus checkout does not make `tenant create` read it.** Steps 0
and 1 are judged in the tenant's directory, and a new one holds neither, so a
new tenant is built from the custom sources and core. To build one from a
corpus checkout, name the checkout's path in `WL_BLUEPRINT_SOURCES`: it is then
a custom source, read from a clone of the commit the checkout was at when the
clone was made or last refreshed. A commit made in the checkout after that is
read only once the clone is next refreshed, under the rules below for every
clone. Uncommitted changes are never read, since a clone carries commits only,
and a build says so when the checkout has any — where the entry is a plain
path: one with `://` or `@` in it is taken for an address, which has no working
tree to look at.

**A source read in place is never refreshed.** It is a working tree, not a copy,
and fetching over it would be a cache eating somebody's edits.

**A command refreshes a clone before reading it once the clone is a day old.** A
refresh that fails keeps the cached copy and says so, is tried again a day after
the attempt rather than on every command, and does not make the copy any
younger: a clone is as old as the last refresh that worked, and that is the age
every report gives. `WL_BLUEPRINT_OFFLINE` switches refreshes off, and this
refresh is held while the directory the command works in has any generated work
banked in `.weblisk/generation/`, because moving the corpus under a resume
invalidates every banked file.
[`weblisk blueprint update`](#weblisk-blueprint-update) does not wait for a
clone to be a day old. A clone that has never been made is made when it is
first needed, even while refreshes are off or held.

A build names every source it read before it generates, and records each with
its revision — see [`weblisk server init`](#weblisk-server-init).
[`weblisk blueprint sources`](#weblisk-blueprint-sources) answers the same
question for the working directory, without building anything.

### `weblisk blueprint sources`

Say which blueprints a command working in this directory would read, from where,
and how current each copy is. A `tenant create` works in the tenant's directory
instead ([Where blueprints come from](#where-blueprints-come-from)).

```bash
$ weblisk blueprint sources
$ weblisk blueprint sources --json
```

The answer belongs to the resolver. A console that finds the corpus itself — a
sibling directory, an environment variable, the cache's layout — is a second
resolver that agrees with this one by luck, and says nothing when they part.

**A question, not a refresh.** It clones nothing and fetches nothing. A clone
that is due a refresh is reported `stale`, and one that has never been made is
reported absent. [Where blueprints come from](#where-blueprints-come-from) says
what changes either, and when. Nor does it write in a working tree it reads —
not even the index `git status` refreshes, whose lock a commit in that tree
would meet. So a console can ask it every time it shows the corpus. It takes
`--json` and no other argument.

`--json` prints one object:

| Field | Meaning |
|---|---|
| `root` | the directory resolution was asked from: the working directory |
| `offline` | `true` when `WL_BLUEPRINT_OFFLINE` switches refreshes off, so nothing is refreshed however stale |
| `sources` | every source, in precedence order |

Each source:

| Field | Meaning |
|---|---|
| `kind` | `project` — [step 0 or 1](#where-blueprints-come-from); `custom`; or `core` |
| `from` | `checkout` — a working tree read in place and never refreshed; `cache` — a clone this CLI keeps |
| `dir` | where it is read from |
| `origin` | for a clone, the repository it is a clone of |
| `present` | `false` for a clone not yet made: a build would make it first |
| `revision` | the short commit, with `-dirty` when the tree has uncommitted or untracked changes. Empty when it is not a git checkout |
| `fetched_at` | for a clone, when it last refreshed successfully. A refresh that failed does not move it. Absent when that is not known |
| `stale` | for a clone, `true` when its last successful refresh is a day old or more, or is not known. Always `false` for a checkout. A build tries to refresh a stale clone before reading it, at most once a day, unless refreshes are off or held ([Where blueprints come from](#where-blueprints-come-from)) |

### `weblisk blueprint update`

Force re-fetch all blueprint sources.

```bash
$ weblisk blueprint update
```

Fetches each source the CLI keeps a clone of in `~/.weblisk/blueprints/` from
the repository it is a clone of, and resets the clone to the commit fetched. A
reset, not a merge: the clone then holds the source's files as they are at that
commit, and an edit made to one of them in the clone does not survive. If a
source is unreachable, its clone keeps the last version fetched, and the command
says so.

### `weblisk validate`

Validate blueprint compliance for the current project, or report what one
repository holds.

```bash
$ weblisk validate
$ weblisk validate agents/seo-analyzer.yaml
$ weblisk validate --deps
$ weblisk validate --security-overrides
$ weblisk validate ../acme-standards --json
```

| Flag | Description |
|------|-------------|
| `--deps` | Check dependency lockfile integrity and known vulnerabilities |
| `--security-overrides` | Validate any security override declarations |
| `--json` | With a directory: the report as one JSON object. Refused without one |

Checks frontmatter, required sections, type definitions, dependency
resolution, and compliance level assignment.

#### One repository: `weblisk validate <dir>`

Given a directory rather than a file, `validate` reports on **that repository's
files and no others**: which families it holds, and what is wrong with them.
This is how a console reads what a
[repository outside any tenant](content.md#repositories-outside-a-tenant) holds
— read from the files, never declared beside them. `--deps` and
`--security-overrides` check a project, and are refused with a directory.

- **Only the repository's own files are findings.** The project around it, a
  configured source and the cache are never validated in its place. Were they, a
  blueprint deleted from the repository would still be found in the cache, and
  the report would describe a union nobody holds. A file the repository holds
  is the one checked even when it does not parse, its failure to parse the
  finding: another source's file of the same name is never read in its place.
- **A corpus is checked on its own.** A repository that
  [step 0](#where-blueprints-come-from) would recognise as a corpus is checked
  against its own schemas, and a reference to a document it lacks is a finding.
  **Anything else is checked against the sources a build run from the working
  directory would read**, resolved as a build resolves them, so a clone among
  them that is due a refresh is refreshed first: the rules for its families come
  from there, and a reference to a document the repository does not hold
  resolves there. A standard or a programme authored outside the corpus is
  checked against its family's schema, and a reference that resolves in those
  sources is not a fault in the repository that makes it.
- **A family is what a schema says it governs.** The families are the
  directories named in the Applies To column of
  [`schemas/README`](../schemas/README.md#schema-files)'s Schema Files table,
  read by column name, plus a programme at the repository's root, which
  [`schemas/programme`](../schemas/programme.md) allows. A repository in which
  none is recognised holds no family and says so, and one for which no
  `schemas/README.md` can be found, in it or in a source behind it, is refused.
  Nothing is guessed.
- **Every family is reported, and each says how much of it was checked.** A
  family this CLI has no checks for is listed with its file count and nothing
  checked. Listing only what was checked would make an unchecked family look
  absent.
- **Programmes are checked for these rules of
  [`schemas/programme`](../schemas/programme.md), and only these:** a
  declaration that parses; an `id` on every map and spec, no two maps and no two
  specs sharing one; a `version` that is `MAJOR.MINOR.PATCH` where one is given;
  no `pack`, `source`, `builtin` or `derived_from`; every `satisfies` citation,
  on a spec and on its obligations, in the form `framework:control`; tiers that
  each have an `id`, are declared once and require only declared tiers, exactly
  one of them requiring nothing, with no cycle; every artifact placed at a
  declared tier; and no spec that requires itself or sits in a cycle. Every
  other refusal in
  [the schema's table](../schemas/programme.md#which-mistakes-stop-the-file-and-which-do-not)
  is left to the loader, which is the authority on them — a second
  implementation here would be a second copy of a rule that drifts — so a
  programme with no findings can still be refused when it is loaded. An
  artifact a map places that no spec in the repository defines is a warning,
  because another repository may supply it. A blank form under `templates/` is
  counted and not checked, and a map or spec with no `version` is counted as
  unversioned and never read as `1.0.0`.
  Two of those checks step aside for a map with an `extends`, a field this
  command reads and does not check: a map whose `extends` names its own `id` is
  not counted as a second map of that id, and a map with any `extends` has its
  tiers and placements left unjudged, because its base may be in another
  repository and half a chain shows faults the whole chain does not have.

`--json` prints one object:

| Field | Meaning |
|---|---|
| `dir` | the repository, absolute |
| `revision` | its short commit, with `-dirty` when it has uncommitted or untracked changes. Empty when it is not a git checkout. Read as [`blueprint sources`](#weblisk-blueprint-sources) reads one, writing nothing in the repository |
| `corpus` | `true` when it is a corpus, checked on its own |
| `checked_against` | the sources that supplied rules and references, each as [`weblisk blueprint sources`](#weblisk-blueprint-sources) describes one. Empty when `corpus` is true |
| `families` | each family recognised: `family`, the `schema` that governs it, `files`, `checked` — how many of those files a check read — and, for programmes, `programmes` and `unversioned` |
| `findings` | each finding: `file`, relative to `dir`; `rule`; `detail`; `authority`, the schema that states the rule; and `severity`, `fault` or `warning` |
| `faults`, `warnings` | how many findings of each severity |

The command exits non-zero when there is a fault, and prints the JSON either
way.

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

### Where an identity lives

An identity belongs to a subject, not to a machine or a tenant, and one machine
may hold several — [`architecture/admin`](admin.md) rule 2. The operator
commands select one this way, and every other command that takes these flags
means the same by them:

| Flag | Selects |
|---|---|
| `--keys-dir <path>` | the identity at an explicit location. Outranks `--identity` |
| `--identity <label>` | the identity with this label. The CLI resolves where it lives, and `weblisk operator path` reports it — a caller asks rather than deriving a path |
| neither | the unnamed default, `~/.weblisk/keys/` |

`--identity` is local: it chooses which key on this machine signs. It is not
`--name`, the operator as a hub records them, and admin rule 2 forbids merging
the two into one argument.

The private half is held in one of three ways:

| Holder | On disk beside the identity | Passphrase |
|---|---|---|
| Encrypted file | `operator.key` in `weblisk-key-v1` format (Argon2id KDF + AES-256-GCM), and `operator.pub` | Required. The CLI never writes it down; it is the only thing protecting the key |
| Encrypted file, its passphrase remembered by a secret source | `operator.key`, `operator.pub`, and `holder.json` recording `holds: ["passphrase"]` | None to type. The source remembers the passphrase the person chose, and the key file still opens without the source. Only on request: `--remember-passphrase` |
| A secret source — a keychain, a vault, a hardware token, or any store a helper speaks for | `operator.pub` and `holder.json`, the holder reference. No private key | None to type. The source holds what unlocks the private half, or signs with it and never releases it |

[`protocol/secret-source`](../protocol/secret-source.md) is how the CLI finds a
source and speaks to it, which sources it carries built in, what a holder
reference records, and what a source holds for an identity.

A secret source is optional and always will be. `protocol/identity` rule 8 ranks
a managed secret above an encrypted file, and that is a preference, not a
requirement: a machine with no vault or keychain must still be able to hold an
identity.

### A credential for each hub

The identity signs to register, to attest, to change its own key
([`weblisk operator rotate`](#weblisk-operator-rotate)) and to re-confirm its
person for a destructive act ([Authentication Flow](#authentication-flow)), and
nothing else at a hub. Tokens come
from a credential ([`architecture/admin`](admin.md#obtaining-a-token)), and the
CLI holds one for each identity at each hub:

- **Made once.** The first time `connect` or `register` obtains a token for an
  identity at a hub, the CLI generates an ML-DSA-65 key pair for that hub, has
  the identity attest it through an attestation token, and keeps it. Every
  later token for that identity at that hub is minted with it, and the
  identity is not asked. The attestation is built as
  [`weblisk operator attest`](#weblisk-operator-attest) builds it, naming the
  `hub_id` recorded for that hub and the `identity_id` the hub answered with.
- **Tested against the published vectors.** A credential's answer to a
  challenge is signed under `weblisk/credential-auth/v1`, which has test
  vectors ([`protocol/identity`](../protocol/identity.md#fixed-form-statements)),
  and the CLI's builder of those bytes tests against every one of them. It
  obtains an operator token by the deprecated identity-signed path only from
  a hub that answers `POST /v1/admin/credentials/challenge` with `404` or
  `405`, and so from no hub built from this corpus
  ([`architecture/admin`](admin.md#minting-a-token-with-the-credential)).
- **Named by the hub, never by its address.** Each credential is kept under the
  `hub_id` it was attested for. A hub at a recorded address whose challenge
  names another `hub_id`, or that refuses the recorded one with
  `CREDENTIAL_FOREIGN_HUB`, is refused: the CLI reports both, and signs
  nothing more for it. Where it really is another hub, the
  person registers there with `weblisk operator register`, which records that
  hub's own registration.
- **Each hub it is registered at is remembered.** Beside the identity, the
  CLI keeps one **registration** for each hub the identity registered or
  connected at: that hub's `hub_id`, the operator name the hub recorded, the
  `identity_id` it answered with, the address it was last reached at, the
  pin its certificate is verified against where it has one, and whether
  that address has proven the `hub_id` (the hub proof below).
  Only a registration answer writes one, approved, pending or a repeat
  ([`architecture/admin`](admin.md#the-registration-response)). `register`
  sends one, and nothing else does: `connect`, `attest` and `attest --batch`
  never register ([`weblisk operator register`](#weblisk-operator-register)).
  A hub that already knows the operator answers a registration as a repeat,
  which is how a device that has not met that hub records its `hub_id`. An address is held by one registration at a time, and no answer
  moves one. An address no registration names that answers with a `hub_id`
  recorded at another address is refused: the CLI reports both addresses and
  signs nothing more there, because a hub can relay a registration to another
  hub and pass back its answer. The registration moves to that address only
  when the person confirms at a terminal that the hub has moved there, and,
  once the hub proof below has test vectors, only where that address proves
  the recorded `hub_id`, never with `--json` or `--batch` or with no
  terminal. A move keeps no pin: a pin trusts one key at one address
  ([`architecture/admin`](admin.md#certificate)), so the moved registration
  is verified at its new address against a pin the person gives with
  `--tls-pin`, learned where that section says one is, or against the system's
  roots, and never against the pin of the address it left. The recorded
  `hub_id` is the only `hub_id` the identity ever signs to ask for an attestation token, so a
  signature it makes is refused at every hub but the one whose answer
  recorded it. Which hub gave that answer is proven by the hub proof below
  alone, and until it has test vectors it is not proven where the CLI
  recorded it first, as on a new device
  ([`architecture/admin`](admin.md#the-identity-signs-only-to-attest), the gap
  there).
  The `hub_id` names the hub; the address is only
  where to find it, so a hub reached there that answers another `hub_id` is
  not that hub. A registration outlives its credential: it is kept when the
  credential is discarded, and removed only when the person confirms it. A
  hub that answers `OPERATOR_REVOKED` or `OPERATOR_UNKNOWN` for the operator
  is reported with the address that answered, and the CLI asks; under
  `--json` or with no terminal it keeps the registration. Neither answer
  shows that it came from the hub the registration names: no refusal carries
  a `hub_id`, and a key change is answered `OPERATOR_UNKNOWN` before any
  signature is checked ([`architecture/admin`](admin.md#changing-an-identity-key)),
  so whatever answers at the hub's last address could produce it. A
  registration dropped on such an answer would let a rotation finish and
  destroy the one key the real hub still accepts. It holds nothing secret. It is what
  [`weblisk operator rotate`](#weblisk-operator-rotate) sends a key change to.
- **A hub proves its `hub_id` where it is reached.** Once
  `weblisk/hub-proof/v1` has test vectors
  ([`architecture/admin`](admin.md#proving-the-hub-at-an-address)), the CLI
  sends nothing that needs the identity to an address no registration names
  until the hub there proves its `hub_id`. Before the registration, it asks
  `POST /v1/admin/hub/proof` with the origin of the address it dialled and a
  challenge of 32 bytes from a cryptographically secure random source, made
  for that request alone, and accepts the answer only where the fingerprint
  of its `public_key` is its `hub_id` and its signature verifies over the
  statement the CLI builds itself from that `hub_id`, that origin and its own
  challenge. The registration answer must then name the same `hub_id`. A hub
  that does not answer the proof, one built before the vectors that answers
  `HUB_PROOF_UNAVAILABLE` included, or whose proof or answer fails any of
  these, is reported with the address, and nothing is recorded or signed
  there. A `hub_id` the CLI holds at an address is then one the hub there
  holds the key for. Until those vectors are published no hub may sign the
  proof, and the CLI records the answer's `hub_id` as it is given.
- **A registration recorded before the vectors is proven at its next
  contact.** Once they are published, the first time the CLI contacts the
  address of a registration that address has not proven, it asks the hub
  proof there as above, before it signs anything there with the identity or
  with a credential, and records that the address proved the `hub_id`. Where
  the proof fails in any of the ways above, the address is reported and
  nothing more is signed there. The registration is kept, and moves only as
  any registration moves: on the person's confirmation, to an address that
  proves its `hub_id`. So a registration recorded through a relay before the
  vectors is held from then, never used. A hub built before the vectors
  answers `HUB_PROOF_UNAVAILABLE`, which fails the proof, so once the CLI has
  the vectors it signs nothing more at such a hub until that hub is built
  again from a corpus that has them.
- **Kept in the platform's keychain.** The CLI keeps each hub credential's
  private key in the platform keychain source, apart from the identity's
  holder: as an item of its own, whatever holds the identity, an encrypted
  key file, a vault or any other source, the keychain itself included. How
  the keychain releases it is the source's
  ([`protocol/secret-source`](../protocol/secret-source.md#the-built-in-sources)):
  without a prompt while the person's session on the machine is unlocked. So
  once the credential answers a challenge
  ([Authentication Flow](#authentication-flow)), minting a token there asks
  nobody, and the identity's holder is asked only to register, to attest, to
  change its key and to re-confirm its person for a destructive act. What protects it is the machine session: while it is
  unlocked, any program running as the person can have the CLI mint with it,
  as it can read a stored token. The identity's holder keeps it, as the next
  two items say, only where no keychain exists: on a platform the CLI carries
  no keychain source for, or where that source answers `not_installed`. There
  every mint asks the holder, and a token is stored by default
  ([Where a token is kept](#weblisk-operator-token)).
- **Where no keychain exists, kept as the identity is.** The private key sits beside the identity it
  belongs to, encrypted in the `weblisk-key-v1` envelope with `kdf` `argon2id`
  under the identity's own passphrase, or held by the secret source that
  holds the identity, and it is opened the way the identity's own key is: by
  that passphrase, typed by the person or remembered by a source they unlock,
  or by that source ([Where an identity lives](#where-an-identity-lives)).
  One passphrase, because the two keys sit together and a second one would
  guard nothing the first does not. It is never in the
  clear and never under `kdf` `none`
  ([`architecture/admin`](admin.md#where-the-second-factor-is)). Its public half
  and its `cid` sit beside it.
- **Where no keychain exists, kept apart where the source cannot keep it.** `store` is optional
  ([`protocol/secret-source`](../protocol/secret-source.md#the-source-contract)),
  and a source that signs with an identity's key and never releases it holds
  no passphrase for it either. So the CLI asks the source that holds the
  identity for its `capabilities`. Only a source that could hold an identity
  **whole** can hold the credential that way
  ([`protocol/secret-source`](../protocol/secret-source.md#an-identity-held-by-a-source)):
  one whose `capabilities` list `store`, answer `named_fields` true, and do
  not name `private_key` in `withheld_fields`, because the CLI must read the
  key back with `get` to sign a challenge. There the credential is stored as
  an identity created in a source is. Anywhere else, the credential key is
  written beside the identity in its own `weblisk-key-v1` envelope with `kdf`
  `argon2id`, under a passphrase the person chooses for it when it is made.
  That is then the one passphrase, because the identity has none to type. It
  is typed by the person, or, only on request (`--remember-passphrase`),
  remembered by a source as an identity's passphrase is: one that lists
  `store`, which may be the identity's own source where it lists `store`
  without holding keys whole, or another the person names with
  `--passphrase-holder <source>`. The envelope's `holder.json` records
  `holds: ["passphrase"]` and that source. With neither, it is typed.
- **Re-attested when it expires, replaced when the hub refuses it.** When the
  hub answers `CREDENTIAL_EXPIRED`, the key is sound and only its attestation
  lapsed, so the next `connect` re-attests the same key, which keeps its `cid`
  ([`architecture/admin`](admin.md#attesting-a-credential)). When it answers
  `CREDENTIAL_UNKNOWN` or `CREDENTIAL_REVOKED`, the CLI discards that
  credential, and the next `connect` attests a new one. Either way it attests
  as [One approval vouches for every hub](#one-approval-vouches-for-every-hub)
  says, with every other attestation on this device that is due.

`--store` and `--no-store` are about the token. The credential is kept
either way, because keeping it is what spares the identity.

### One approval vouches for every hub

Of what the identity signs at a hub (it signs to register, to attest, to
change its own key and to step up), only attestation is repeated for every
hub, and the CLI asks it to attest as seldom as that allows: **once on this device for every hub the identity is registered at**,
never once for each hub.

- **A separate attestation for each hub.** Each hub is sent an
  [`Attestation`](../patterns/principal-identity.md#types) naming its own
  `hub_id`, the `identity_id` that hub recorded, and the credential key made
  for it, and nothing about any other hub. The CLI never signs one attestation
  naming several hubs: every hub it was presented to would learn the person's
  other tenants.
- **Signed in one approval.** Whenever it attests, at a first `connect` or
  `register`, at a renewal, or for `weblisk operator attest`, the CLI attests
  together every credential on this device that is due: a new one, and every
  one whose attestation has lapsed or has fewer than 7 days left, at every hub
  it has a registration for. It opens the identity once, by one passphrase
  or one unlock of the source that remembers it or holds the key, and signs
  everything the batch needs while it is open: each hub's attestation-token
  request, `{hub_id, jti, name, timestamp}` with a `jti` drawn for that request
  alone ([`architecture/admin`](admin.md#contracts),
  `attestation-token-issuance`), and each hub's `Attestation`, built
  with the `identity_id` that hub's registration recorded. A source that signs
  and never releases the key is sent all of them in one `sign` request, where
  it lists `sign_batch`, so it asks its person once
  ([`protocol/secret-source`](../protocol/secret-source.md#actions)). One that
  does not is asked once for each, and the CLI says how many approvals that
  will take before it asks for the first.
- **A hub not yet registered on this device is not attested.** An
  attestation-token request names the `hub_id` a registration answer
  recorded, and a batch never registers
  ([`weblisk operator register`](#weblisk-operator-register)). So where the
  batch includes a hub this device has no registration for, the CLI signs
  nothing for that hub, reports it `not_registered` with its address, and
  attests the rest. The person registers there, which is its own act, and
  the next batch includes it. So no list registers the identity at a hub,
  and every batch takes one approval.
- **Each hub is told only its own.** The attestation-token requests are sent
  first, each to its own hub, inside the replay window, and each once: a
  request a hub did not answer is not sent again, and the hub is attested at
  the next batch, under a new `jti`. A hub's `Attestation`
  is submitted only where its attestation-token answer names the
  `identity_id` the CLI built it with. A hub that answers another is reported
  and sent nothing more, and a hub that does not answer keeps the attestation
  it had until the next batch.
- **Renewed together.** A renewal asks for `not_after` 30 days ahead for
  every attestation in it, within the 90-day cap
  ([`architecture/admin`](admin.md#attesting-a-credential)), re-attesting
  each key, which keeps its `cid`. A credential attested between renewals
  takes the `not_after` the device's other attestations share, so all of them
  fall due together; where fewer than 7 days of it remain, the batch renews
  every attestation on the device instead. Once fewer than 7 days remain,
  every command that mints a token warns the person, and the next `connect`
  renews them all. So the person approves once in each 30 days, whatever the
  number of hubs.
- **Daily use asks the identity nothing.** Connecting, switching from one hub
  to another and refreshing a token use the credential the CLI holds for that
  hub ([Authentication Flow](#authentication-flow)). A console that drives the
  CLI holds its own credential for each account at each hub, and mints with
  it, asking nothing, while that account's person holds a live AAL2 session
  with it ([`architecture/admin`](admin.md#a-console-holds-a-credential-never-a-token),
  `console-credential-use`). It asks the CLI only to attest, for every hub at
  once, with `weblisk operator attest --batch`.

### `weblisk operator init`

Create an operator ML-DSA-65 identity — in an encrypted file protected by a
passphrase, or with `--holder`, in a secret source.

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

- Creates the identity where `--keys-dir`, `--identity` or the default selects
  (mode 0700 directory, 0600 key) — see [Where an identity lives](#where-an-identity-lives)
- Without `--holder`, or with `--remember-passphrase`, prompts for a
  passphrase, which cannot be skipped or supplied via flag. Minimum length 12
  characters (enforced). The private key is stored in `weblisk-key-v1` format,
  and the passphrase is never written to disk and never in shell history
- `--holder <source>`, without `--remember-passphrase`, keeps the private half
  in that secret source instead: no private key is written beside the identity
  and no passphrase is asked for.
  What the source then holds is
  [`protocol/secret-source`](../protocol/secret-source.md#an-identity-held-by-a-source)'s
  to say
- `--remember-passphrase`, with `--holder <source>`, writes the encrypted key
  file as without `--holder`, and has the source keep only the passphrase the
  person typed. `holder.json` then records `holds: ["passphrase"]`
- `--holder-opt <key>=<value>` passes an option to the source and records it in
  the holder reference — which vault, which account. Repeatable. An option is
  never a secret
- `--vault <vault>` means `--holder 1password --holder-opt vault=<vault>`, and
  `--account <account>` with it means `--holder-opt account=<account>`. Both are
  deprecated aliases
- Never overwrites an identity that already exists there without `--force`
- `--force` to regenerate (prints identity change warning; the new identity must be re-registered)
- `--name <name>` sets the operator name a hub will record (default: system
  username). It does not choose where the identity lives — `--identity` does
- `--json` prints the result as one object, for a console that creates an
  identity for a person and links it in the same act: `name`, the operator name
  a hub will record; `keys_dir`, where the identity lives, as
  [`weblisk operator path`](#weblisk-operator-path) reports it; `public_key`,
  base64url, as `operator.pub` holds it; `holder`, the identity's holder
  reference, read from its `holder.json` as
  [`protocol/secret-source`](../protocol/secret-source.md#the-holder-reference)
  reads one, `holds` included where it is recorded, and `null` for an identity
  with no `holder.json` — an encrypted key file whose passphrase a person types,
  for which no source is asked; and `created`, which is
  `false` when an identity already existed there and was left as it was, so the
  console links the one that exists rather than minting a second. **It carries
  no secret**: no private key, no passphrase, and nothing a secret source keeps
  for the identity. Under `--json` a passphrase, where one is needed, is read
  once from stdin with no prompt and no confirmation — the console that
  collected it has confirmed it — and stdout carries the result and nothing else

### `weblisk operator store`

Map an identity to a secret source, rather than creating one: an identity whose
private half is already in the source, or, with `--remember-passphrase`, one
whose encrypted key file is here and whose passphrase the source is to remember.

```bash
$ weblisk operator store --identity alice --holder <source>:<reference>
$ weblisk operator store --identity alice --holder <source> --remember-passphrase
```

- `--holder <source>:<reference>` is the holder reference in its flag form
  ([`protocol/secret-source`](../protocol/secret-source.md#the-holder-reference))
- Writes the public key, read from the source, and the holder reference beside
  the selected identity, once a probe signed through the reference verifies
  against that key. Before the probe has test vectors it writes them unproven
  and says so. Every signature it later gets through the reference, the first
  included, is verified against that key before it is used, as every
  signature through a holder reference is
  ([`protocol/secret-source`](../protocol/secret-source.md#an-identity-held-by-a-source),
  the gap there). The private half stays in the source
- Refuses where the selected location already holds a private key on disk: a
  subject holds one identity, and mapping over it would strand that one.
  `--remember-passphrase` is the exception, because the key file is what it
  keeps
- `--remember-passphrase`, with `--holder <source>`, is for an identity already
  in an encrypted key file at the selected location. Asks for its passphrase on
  stdin, checks that it opens the key, has the source keep it, and writes
  `holder.json` recording `holds: ["passphrase"]`
- `--holder-opt <key>=<value>` as for `operator init`
- `--reference <reference>` means `--holder 1password:<reference>`, and
  `--account` is as for `operator init`. Both are deprecated aliases

`init` creates, `store` maps and `path` reports; no verb does two of those.

### `weblisk operator path`

Print where an identity lives.

```bash
$ weblisk operator path --identity alice
```

So a caller can ask where an identity lives instead of deriving the path. A
console or script that derives it is a second implementation of admin rule 2,
kept in step by luck. `--json` for machine-readable output. While a rotation
is pending it also names the rotation record and the file holding the key
that signs, `operator.key.next` for an encrypted file
([`weblisk operator rotate`](#weblisk-operator-rotate)).

### `weblisk operator register`

Register at a hub, through its admin gateway, which carries the registration
to the orchestrator that keeps operator records
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`).
`--orch` names the gateway, as it does for every operator command.

**Registering is its own act, and this is the one command that does it.**
`connect`, `attest` and `attest --batch` never register. Each reports
`not_registered` and names this command where registering is what is
missing: where this device has not met the hub, so no registration names its
address, or where the hub does not know the person (`OPERATOR_UNKNOWN`). A
hub that already knows the person answers a registration at once, as a repeat
([`architecture/admin`](admin.md#the-registration-response)), so registering
from a second device costs one approval and waits on nobody.

```bash
$ weblisk operator register --orch https://hub.example.com --bootstrap ./acme/.weblisk/bootstrap
Registering operator 'alice' with https://hub.example.com...
✓ Registered as admin (first operator — bootstrap secret accepted)
  Expires: 2026-04-26T10:00:00Z
```

- Signs the registration payload with the operator's private key
- At a hub with no operator, sends the bootstrap secret read from the file
  `--bootstrap <path>` names. The secret is never an argument, which every
  process on the machine can read. Without it, such a hub refuses the
  registration ([`architecture/admin`](admin.md#bootstrap-flow))
- Once approved, attests a credential for this hub
  ([A credential for each hub](#a-credential-for-each-hub)) and obtains a token
  with it, as the [Authentication Flow](#authentication-flow) says. The token is
  returned (stdout, or the `--json` result), and written beside the identity
  as [Where a token is kept](#weblisk-operator-token) says: only with `--store`
  where a later command can mint its own without asking anybody, and otherwise
  unless `--no-store` is given
- If not the first operator, prints "Registration pending admin approval".
  Either way it records the registration the answer names: the hub's
  `hub_id`, the operator's `identity_id` and the address. A repeat's answer
  names no status, so `register` then asks for an attestation token, as
  `connect` does, and reports what that answer says
- `--role <role>` to request a specific role (admin may override)
- `--tls-pin <pin>` names the pin the gateway's certificate is verified
  against, where the system's roots do not verify it
  ([`architecture/admin`](admin.md#certificate)); `create` reports it. The
  registration records it, and every later request to that address is
  verified against it. The `--json` result carries the `address` and, where
  the registration records one, the `tls_pin`; without `--tls-pin`, against a
  gateway whose certificate the system's roots verify, it records none and the
  result carries none. A console that makes its own requests keeps a pin only
  where it was given one, as [`architecture/admin`](admin.md#certificate)
  says (`console-keeps-pin`, `client-pins-gateway-key`)

### `weblisk operator connect`

Obtain an operator token from a hub that is already running.

```bash
$ weblisk operator connect --orch https://hub.example.com
  Passphrase: ********

  existing operator identity unlocked
  token issued — this hub already knows this operator

  [ok] Connected to https://hub.example.com as alice
```

**Needs an address and an identity, and nothing else.** No project directory,
no recorded run state, no access to the hub's files. A hub on another host, in
a container, or started by something other than this CLI is reachable on
exactly the same terms as one in the next directory — see
[`architecture/admin`](admin.md#bootstrapping-and-connecting-are-different-acts)
for why that separation matters.

Idempotent, because it is the ordinary way to connect and will be run
repeatedly. **It never registers, never creates an identity and never claims
a hub.** Where a registration names the address, it asks for a token. Where
none does, it sends nothing that needs the identity: it reports
`not_registered` with the address and names
[`weblisk operator register`](#weblisk-operator-register), the act that
records a hub's `hub_id` ([A credential for each hub](#a-credential-for-each-hub)),
and it never asks for an attestation token without one. A hub that answers
`OPERATOR_UNKNOWN` is reported the same way. Where no identity is held, it
reports `identity_unavailable` and names `weblisk operator init`, and makes
none. It never sends a registration, so it never presents a bootstrap secret
and never claims a hub. `--no-register` is still accepted, and changes
nothing, so a console that passes it, or checks that `connect` lists it,
keeps working.
`connect` obtains its token as the [Authentication Flow](#authentication-flow)
says, and attests a credential first where this identity holds none the hub
accepts ([A credential for each hub](#a-credential-for-each-hub)).

Seven outcomes, and they are told apart. The `--json` result carries the
`address` and, where the registration records one, the `tls_pin` the
gateway's certificate was verified against; where it records none, no
`tls_pin`. A console that makes its own requests to the gateway keeps a pin
only where it was given one, as
[`architecture/admin`](admin.md#certificate) says (`console-keeps-pin`):

| State | Meaning |
|---|---|
| `connected` | a token was issued: returned, and stored beside the identity as [Where a token is kept](#weblisk-operator-token) says |
| `not_registered` | registering is what is missing: no registration names this address, or the hub does not know the operator. Nothing was registered; the message names `weblisk operator register` and the address |
| `pending_approval` | the hub will not issue one yet. **Not a failure** — the first operator of a hub is admitted by its bootstrap secret and every later one needs an existing admin. The message names who can act |
| `refused` | the hub answered and said no in a way no approval changes, such as the operator name being registered to a different key |
| `identity_unavailable` | this machine could not sign: the key file did not open, or the secret source holding the identity did not answer. Nothing is wrong with the hub. Where a source did not answer, `--json` output carries its name as `source` and its code as `code` ([`protocol/secret-source`](../protocol/secret-source.md#reporting-a-source-that-did-not-answer)) |
| `unreachable` | nothing answered, or the hub does not serve `POST /v1/admin/operators/token` — reported distinctly, because telling somebody to await an approval that is never coming is worse than saying the hub is too old |
| `pin_mismatch` | something answered at the address with a certificate whose key is not the pin the registration records: what an interception looks like, so nothing is sent over that connection, and the message names the recorded pin and where a new one comes from, never the presented certificate's ([`architecture/admin`](admin.md#certificate)) |

Flags:

| Flag | Purpose |
|---|---|
| `--orch <url>` | the hub's address: its admin gateway, where the CLI sends every request it makes at the hub. Required |
| `--name <name>` | the operator, as the hub will record them. Defaults to the stored identity's name |
| `--identity <label>` | which identity signs, by label. The CLI resolves where it lives — see `architecture/admin` rule 2 |
| `--keys-dir <path>` | which identity signs, by location. Outranks `--identity` |
| `--json` | machine-readable result, for a console driving this |
| `--store` | also write the token beside the identity, mode 0600, for later commands to use, where the default writes none ([Where a token is kept](#weblisk-operator-token)) |
| `--no-store` | write no token file, where the default writes one: where a mint asks the identity's holder ([Where a token is kept](#weblisk-operator-token)). Elsewhere it changes nothing |
| `--no-register` | accepted, and changes nothing: `connect` never registers |
| `--cap <name,...>` | mint the token with `cap` naming only these capabilities, those the operator's role carries (`architecture/admin`, operator-token-issuance). For a caller that needs less than the role carries, such as a script |
| `--remember-passphrase` | where the credential key is kept in its own envelope ([A credential for each hub](#a-credential-for-each-hub)), have a source remember the passphrase chosen for it. Refused, keeping nothing, where no source that lists `store` is available |
| `--passphrase-holder <source>` | with `--remember-passphrase`, the source that remembers it, where it is not the identity's own |

**The passphrase arrives on stdin and never in argv.** A passphrase in a
command-line argument is readable by every process on the machine, so one is
refused rather than accepted with a warning. An identity whose passphrase a
secret source holds is not asked for one.

### `weblisk operator token`

Refresh or inspect the current operator token.

```bash
$ weblisk operator token
Operator: alice
Role:     admin
Expires:  2026-04-26T10:00:00Z (52m remaining)
Hub:      https://hub.example.com

$ weblisk operator token --refresh
✓ Token refreshed. Expires: 2026-04-26T11:00:00Z
```

**Where a token is kept depends on whether a mint asks anybody.** A mint is
*silent* where the credential this identity holds for that hub
([A credential for each hub](#a-credential-for-each-hub)) is kept by the
platform keychain source and answers the hub's challenge: the keychain
releases it while the person's session on the machine is unlocked, so minting
asks nobody. Anywhere else a mint asks the identity's holder: where no
keychain exists, the credential is opened as the identity's own key is, by a
passphrase typed or a source approving; and until `weblisk/credential-auth/v1`
has test vectors, only the deprecated identity-signed path yields a token,
which the identity's holder signs. Those vectors are published
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)), so a
credential mints.

- **Where a mint is silent: nowhere, by default.** Every command that needs
  a token mints a fresh one and holds it in memory for that command alone.
  `connect`, `register` and `token --refresh` return the token they obtain,
  on stdout or in the `--json` result, and write no token file. **`--store`
  opts in, per command:** with it, they also write the token beside the
  identity that obtained it, mode 0600, and a later command uses that file
  until the token is due for refresh. `--no-store` changes nothing there.
- **Where a mint asks the identity's holder: beside the identity, by
  default.** `connect`, `register` and `token --refresh` write the token
  they obtain beside the identity, mode 0600, and a later command uses that
  file until the token is due for refresh, so the holder is asked about once
  a token lifetime rather than by every command. **`--no-store` writes no
  token file:** the token goes to stdout, or into the `--json` result, and
  every later command that needs one asks the identity's holder again.
  `--store` changes nothing there.

**A token carrying `step_up_at` is minted by the command that needs it, and
only through a re-confirmation.** No mint above sets it, silent or not, and
`--refresh` never does: a token the CLI renews carries no `step_up_at`,
whatever its age. A destructive command obtains one when the hub answers it
`401` `STEP_UP_REQUIRED`: the CLI asks its person to re-confirm the act the
answer names, at the terminal or through a holder that itself asks the
person, such as a vault approval, mints a token whose request carries
`step_up` of form `identity`, and retries once; a command run with
`--step-up` re-confirms before its first request
([Authentication Flow](#authentication-flow)). That token is never stored,
by either rule above: it is held for the command that asked, and
`weblisk operator token` never reports it.
<!-- wl:id cli-step-up-token-held -->

A stored token is a bearer credential: whoever holds the file may use it
until it expires. It carries every capability the operator's role carries,
`admin:*` and every person-only capability for an admin, and mode 0600 keeps
it from other users, never from another program the same user runs, an agent
included. `architecture/admin`'s rule that no agent holds a person's token
binds a console
([`console-credential-use`](admin.md#a-console-holds-a-credential-never-a-token)),
and a stored file is outside it, which is why none is written where a mint
can be silent, and why a person who runs agents under their own account
passes `--no-store` where one would be. A console never passes `--store` and
always passes `--no-store`, because a console never writes an operator token
anywhere
([`architecture/admin`](admin.md#a-console-holds-a-credential-never-a-token)).

**With no token file, `weblisk operator token` says so.** Plain `weblisk
operator token` reports the token a stored file holds. Where none is stored,
it reports `no stored token`, with the operator, the hub and whether a mint
there would be silent or would ask the identity's holder, and mints nothing;
`--refresh` mints one.

**A token goes to the hub's admin gateway and nowhere else.** The CLI, and a
caller it hands a token to, presents it at the hub's admin gateway alone, as
every holder of an operator token must
([`protocol/identity`](../protocol/identity.md#the-pass)). The content
service, the fabric and every other component are reached through the
gateway, on a pass addressed to them alone, so a token minted with no `--cap`,
which carries the role's full set, reaches no component but the orchestrator
that issued it. `--cap` narrows a token for a caller that needs less than the
role carries. A narrowed token is never stored, so `--cap` is refused with
`--store`, and, where a mint asks the identity's holder, requires
`--no-store`; a stored token keeps the role's full set.

### `weblisk operator attest`

Have an identity attest credentials that another program holds, at one hub,
or at several in one approval.

Not built yet. It is specified here under today's noun and is built as
`weblisk identity attest` ([Renamed commands](#renamed-commands)).

```bash
$ weblisk operator attest --orch https://hub.example.com --identity alice \
    --credential-key ./credential.pub --device-label "console on build-01" --json
$ weblisk operator attest --identity alice --batch ./attest.json --json
```

For a console. The console generates the credential's key pair and keeps it;
this verb is how the account's operator identity attests the public half
without the console ever holding the identity
([`protocol/secret-source`](../protocol/secret-source.md#a-console-never-holds-the-secrets-of-an-identity-it-acts-for)).
Once `weblisk/credential-auth/v1` has test vectors, and not before (they are
published: [`protocol/identity`](../protocol/identity.md#fixed-form-statements)),
the steps are [`architecture/admin`](admin.md#obtaining-a-token)'s:

- Reads the credential's public key from the file `--credential-key` names
- Asks the hub for an attestation token, signing `{hub_id, jti, name, timestamp}`
  with the identity, with the `hub_id` of the registration recorded for that
  hub and a `jti` of at least 128 random bits drawn for that request alone
  ([`architecture/admin`](admin.md#contracts), `attestation-token-issuance`),
  and takes `identity_id` from the answer. A request is sent once; one the
  hub refuses with `TOKEN_REQUEST_REPLAYED` is reported, never a reason to
  register. Where no registration is recorded for the hub, it registers
  nothing, signs nothing and reports `not_registered`, as `connect` does
- Builds the `Attestation` itself — the `identity_id` the registration
  recorded for that hub, the identity's public key, the credential public
  key, `hub_id`, `--device-label` and `not_after` — signs its canonical form,
  and submits it only where the attestation-token answer names that same
  `identity_id`. It never
  computes the identity id from the key: a hub keeps an operator's identity id
  across a change of identity key
  ([`architecture/admin`](admin.md#changing-an-identity-key)), so after one it
  is not the key's fingerprint. It never signs bytes a caller supplies, so it
  is not a way to get the identity's signature over anything else
- `--days <n>` sets `not_after` that many days ahead, within the default and the
  cap [`architecture/admin`](admin.md#attesting-a-credential) states, and is
  refused beyond the cap
- Submits the attestation and prints the credential's id and its `not_after`.
  `--json` gives them as `cid` and `not_after`
- Writes nothing to disk, and unlocks the identity once for both signatures
- `--batch <path>` names a JSON file listing several credentials, each entry
  an object with `orch`, `credential_key` and `device_label`, in place of
  `--orch`, `--credential-key` and `--device-label`. It attests them all as
  [One approval vouches for every hub](#one-approval-vouches-for-every-hub)
  says, a separate attestation for each hub in one approval of the identity,
  registering nowhere: an entry whose `orch` no registration names is
  answered `not_registered` and sent nothing. With `--json` it answers an
  array in the order of the entries, each with `orch` and either `cid` and
  `not_after` or `code`

Its outcomes are `attested`, and `pending_approval`, `not_registered`,
`refused`, `identity_unavailable`, `unreachable` and `pin_mismatch` as
`connect` reports them. With
`--json`, a refusal carries the hub's error code as `code`. `--orch`, `--name`,
`--identity` and `--keys-dir` mean what they mean for `connect`.

**The credential's answer has test vectors.** A credential is used only to
answer a hub's challenge, under `weblisk/credential-auth/v1`, whose test
vectors this corpus publishes
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)). So a
credential this verb vouches for can mint at the hub it was attested for, as
soon as the program holding it signs as those vectors test.

### `weblisk operator rotate`

Change the identity's ML-DSA-65 key at every hub it is registered at, keeping
its name, role and identity id at each.

```bash
$ weblisk operator rotate
Enter current passphrase: ********
Generating new key pair...
Enter new passphrase (min 12 characters): ********
Confirm new passphrase: ********
Sending the new public key to 3 hubs (signed by the old key and the new)...
  ✓ 7c1e…  changed
  ✓ 0b9d…  changed
  ✗ 4f2a…  unreachable — still pending
Rotation pending at 1 hub. The old key is kept until it finishes:
  weblisk operator rotate --resume
```

- **Where it sends.** To every hub in the identity's registrations
  ([A credential for each hub](#a-credential-for-each-hub)), at the address
  each was last reached at, through `POST /v1/admin/operators/{name}/key` with
  the name and `hub_id` the registration records, signed by the old key for
  continuity and by the new key for possession
  ([`architecture/admin`](admin.md#changing-an-identity-key)). A hub whose
  credential lapsed and was discarded is still registered, so it is sent the
  change too. Rotate takes no `--orch` or `--name`: a key belongs to the
  identity, and a change made at some of its hubs and not others is exactly
  the state below.
- **Recorded before anything is sent.** The CLI generates the new key, keeps
  it beside the identity as the **next** key, in the holder's form below, and
  writes a rotation record listing every registration as `pending`. Each hub
  that answers `200` with the registration's `identity_id` is marked
  `changed`, whether it applied the change then or answers a repeat of a
  change it applied before, whose answer was lost
  ([`architecture/admin`](admin.md#changing-an-identity-key)). One that
  answers `200` with another `identity_id` is marked `refused` and reported:
  it took the new key, for an operator this registration does not name.
  `OPERATOR_REVOKED` and `OPERATOR_UNKNOWN` are reported, and the hub stays
  `pending`, with its registration kept until the person confirms its
  removal ([A credential for each hub](#a-credential-for-each-hub)). Any
  other refusal, and a hub that cannot be reached or answers another
  `hub_id`, leaves it `pending`, reported with its code or as
  `unreachable`. A run that leaves any hub `pending` exits non-zero and names
  each one.
- **Never with nowhere to send.** With no registrations, or while the
  identity holds a credential kept under a `hub_id` it has no registration
  for, `rotate` is refused and names each such `hub_id`. An identity that
  registered before the CLI kept registrations is still recorded by those
  hubs under the old key, and a rotation that finished would destroy the
  only key they accept. `weblisk operator register` at each hub writes its
  registration, which a hub that knows the operator answers as a repeat. A
  person sure the identity is registered at no hub confirms it when asked;
  under `--json` or with no terminal the refusal stands.
- **While a rotation is pending, the identity's key is the new one.**
  `operator.pub` holds the new public key from the moment the record is
  written, and every signature the identity makes is made with the new key,
  a registration at a new hub included. The old key signs one thing only: the
  continuity of a key change at a hub still `pending`, which records the old
  key and nothing else. So `connect` to a `pending` hub, and `attest` once it
  sends anything ([`weblisk operator attest`](#weblisk-operator-attest)),
  first send it the key change, whether or not a credential there is still live,
  and the identity signs there with the new key once the change is accepted.
  A refusal leaves the hub `pending`, and the command has the identity sign
  nothing there and reports the code. For an encrypted file the key that
  signs is `operator.key.next`: `operator.key` still holds the old key, and
  signs only that continuity, so nothing pairs `operator.key` with
  `operator.pub` while a rotation record exists.
  [`weblisk operator path`](#weblisk-operator-path) names the file that
  signs, so a caller that reads the files never has to know this.
- **Resumed, never started again.** `weblisk operator rotate --resume` sends
  the change to every hub still `pending`, signed by the old key and the new
  over a fresh timestamp: a hub refuses a request it has seen and one outside
  its 300-second window, so no attempt reuses another's bytes. The old key is
  the one a hub that never applied the change still records, so it is the one
  that can hand the operator on. A hub that applied the change and whose
  answer was lost answers the same request as a repeat, `200`, and is marked
  `changed`. With `connect`, and `attest` once it sends anything, doing the
  same, a hub that was unreachable during the rotation
  finishes it the next time it is reached. `rotate` without `--resume` while a
  rotation is pending is refused, so a second new key never strands the
  first.
- **Finished when nothing is pending.** When every registration is `changed`,
  or has been removed by the person, the old private key is destroyed in the holder's form
  below, its public half is kept beside the identity as
  `operator.pub.retired` with the time the rotation finished, for audit, and
  the rotation record is deleted. Once no hub records the old key, nothing
  may be signed with it, and a private key that is kept is one more copy of a
  key to protect, kept for no use. Its public half is all an auditor needs.
- **Abandoning a hub.** `weblisk operator rotate --abandon <hub_id>` removes
  one `pending` or `refused` hub from the rotation, and its registration with
  it, and asks for confirmation first. It is the only way out for a hub that
  answered `OPERATOR_REVOKED` or `OPERATOR_UNKNOWN`, or `refused`, and the
  person's confirmation is what removes the registration. A `refused` hub
  already holds the new key, so abandoning it loses only the registration. A
  `pending` hub that never applied the change keeps the old key as the
  operator's identity key, and once the rotation finishes nothing on this
  machine can sign for it there: that is the lost-key case, and the operator
  is removed by an admin there and registers again as a new identity id
  ([`architecture/admin`](admin.md#changing-an-identity-key)). Before it asks,
  the CLI sends the change to that hub once more, so a hub that did apply it
  and is reachable is marked `changed` instead.
- **Credentials.** Each hub that accepts revokes every credential the old key
  attested, so the CLI discards its credential for that hub, and the next
  `connect` attests a new one with the new key. The hub answers the same
  `identity_id` as before, and the attestation names it.

**For each holder** ([Where an identity lives](#where-an-identity-lives)):

| Holder | The next key | When the rotation finishes |
|---|---|---|
| Encrypted file | Generated by the CLI and written beside the identity as `operator.key.next`, in `weblisk-key-v1` with `kdf` `argon2id`, under a new passphrase the person types twice. The current passphrase opens the old key | `operator.key.next` replaces `operator.key`, and the old envelope is overwritten and removed |
| Encrypted file, passphrase remembered by a source | As the encrypted file, and the source is asked to `store` the new passphrase, under a reference the rotation record keeps | `holder.json` names the new reference, and the old passphrase is `erase`d from the source |
| A source holding it whole | Generated by the CLI and stored in the same source with `store`, as an identity created there is ([`protocol/secret-source`](../protocol/secret-source.md#an-identity-held-by-a-source)), under a reference the rotation record keeps | `holder.json` names the new reference, and the old one is `erase`d. A source that does not list `erase` is reported, and the person erases it with the source's own tool |
| A source that signs and never releases the key | Not generated by the CLI: no action of `protocol/secret-source` creates a key in such a source. The person creates it with the source's own tool and names it with `--new-holder <source>:<reference>`, which the CLI maps as `weblisk operator store` maps one, once a signature through it verifies against the public key it reads. Without `--new-holder`, rotate is refused for this holder and says why | `holder.json` names the new reference. The CLI cannot destroy the old key, and tells the person to with the source's own tool |

The passphrase of an encrypted file is never a flag and never in shell history,
as for `operator init`.

---

## Status Commands

### `weblisk status`

System overview, as the admin gateway composes it.

```bash
$ weblisk status
Weblisk — acme-corp (https://hub.example.com)
Protocol: v1    Uptime: 2d 14h 32m

Agents:     8 registered: 7 ready, 1 not ready, 0 unknown
Domains:    unavailable — no provider here serves them (ADMIN_GROUP_UNAVAILABLE)
Workflows:  unavailable — no provider here serves them (ADMIN_GROUP_UNAVAILABLE)
Approvals:  unavailable — no provider here serves them (ADMIN_GROUP_UNAVAILABLE)
Federation: unavailable — no provider here serves them (ADMIN_GROUP_UNAVAILABLE)
Objectives: unavailable — no provider here serves them (ADMIN_GROUP_UNAVAILABLE)
```

- Calls `GET /v1/admin/overview` at the hub's admin gateway, which composes
  the overview: the orchestrator's figures, and each other group asked of
  the component that holds it on a pass, or carried as an object whose one
  member, `unavailable`, holds a code, as `{"unavailable": "ADMIN_GROUP_UNAVAILABLE"}`
  ([`architecture/admin`](admin.md#get-v1adminoverview)). A group carried
  that way is shown as unavailable with its code, never as zero, and until
  a provider's blueprint specifies its group on a pass every group but the
  orchestrator's is shown that way
- Shows no health score: the overview carries none, and one number would
  stand in for figures that may be unavailable
- `--json` for machine-readable output
- `--watch` to refresh every 5 seconds (like `watch`)

---

## Agent Commands

### `weblisk agents list`

List all registered agents.

```bash
$ weblisk agents list
NAME              TYPE            LEASE      VERSION   LAST SEEN
seo-analyzer      agent           ready      1.0.0     10s ago
a11y-checker      agent           ready      1.0.0     12s ago
content-analyzer  agent           ready      1.0.0     8s ago
meta-checker      agent           ready      1.0.0     15s ago
uptime-checker    agent           ready      1.0.0     3s ago
perf-auditor      agent           ready      1.0.0     21s ago
cron              infrastructure  ready      1.0.0     5s ago
email-send        infrastructure  not_ready  1.0.0     4s ago

8 agents (7 ready, 1 not ready, 0 unknown)
```

- Shows what the orchestrator's registry holds of each agent, from
  `GET /v1/admin/agents`, and no metrics, which no component serves to a
  person yet ([`architecture/admin`](admin.md#agent-management))
- `--type <domain|agent|infrastructure>` to filter, by the manifest's `type`, an absent one read as `agent`
- `--lease <ready|not_ready|unknown>` to filter, by `lease_state`
- `--json` for machine-readable output

### `weblisk agents describe <name>`

Full detail for a single agent.

```bash
$ weblisk agents describe seo-analyzer
Agent: seo-analyzer
Type:  agent    Version: 1.0.0
URL:   http://localhost:9710
Lease: ready    Registered: 2d 14h ago

Capabilities:
  file:read     **/*.html
  llm:chat      *
  agent:message *

Metrics:    unavailable — no provider here serves them (ADMIN_GROUP_UNAVAILABLE)

Behavioral Fingerprint: unavailable — no component serves it or its change history
```

- Reads the agent from `GET /v1/admin/agents/{name}`, and its metrics from
  `GET /v1/admin/agents/{name}/metrics`, which the admin gateway answers
  `ADMIN_GROUP_UNAVAILABLE` while no blueprint specifies that route
  ([`architecture/admin`](admin.md#agent-management)). Metrics are then shown
  as unavailable with that code, never as zero. No recent tasks are shown:
  the orchestrator handles none, and no component serves them to a person.
  The behavioural fingerprint and its change history are shown unavailable,
  as admin's Agent Detail shows them, while no component serves them to a
  person: no figure stands in for one, and no change history reads as none
- `--json` for machine-readable output
- `--metrics-range <1h|24h|7d|30d>` to change the metrics window, once a
  provider serves them

### `weblisk agents deregister <name>`

Force-deregister an agent (admin only).

```bash
$ weblisk agents deregister email-send
⚠ This will deregister agent 'email-send' and remove it from all workflows.
  Type agent name to confirm: email-send
✓ Agent 'email-send' deregistered.
```

- Requires `--confirm` or interactive confirmation
- A destructive act: it needs its person's step-up
  ([Authentication Flow](#authentication-flow);
  [`architecture/admin`](admin.md#contracts), `destructive-action-step-up`)
- Logs the deregistration in the audit trail

---

## Domain Commands

### `weblisk domains list`

List domain controllers and their status.

```bash
$ weblisk domains list
NAME      LEASE     AGENTS              WORKFLOWS            LAST ACTIVITY
seo       ready     2/2 ready           seo-audit, seo-opt   10m ago
content   ready     2/2 ready           content-audit, ...   25m ago
health    ready     2/2 ready           health-check, ...    5m ago
```

### `weblisk domains describe <name>`

```bash
$ weblisk domains describe seo
Domain: seo
Version: 1.0.0    Lease: ready    Port: 9700

Required Agents:
  NAME            LEASE
  seo-analyzer    ready ●
  a11y-checker    ready ●

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
```

---

## Approval Commands

The decision inbox: every decision a person may make, from each owner that
holds one open, composed by the admin gateway
([`architecture/admin`](admin.md#decision-inbox)). Each decision is made at
its owner, never at the gateway.

### `weblisk approvals list`

```bash
$ weblisk approvals list
OWNER     ID                                 SUMMARY
content   9b2f61c0d4e8a7b3c5f1e6d2a8b4c7e0   Modify procedures/access-review.md
content   1e7d3a9c5b2f8e4a6d0c3b7f9a1e5d2c   Create policies/remote-work.md

2 open
Unavailable: none
```

- Calls `GET /v1/admin/approvals` at the admin gateway. Until a `PassRoute`
  can name the inbox group, the gateway answers it `ADMIN_GROUP_UNAVAILABLE`,
  and the command says the inbox is unavailable and exits 1; the listing above
  is what it shows once owners can be asked
- SUMMARY is rendered by the CLI from the owner's own record: for content, the
  proposal's `change`, its action and path. The gateway writes none
- `--owner <name>` to filter by owner
- An owner the gateway names under `unavailable` is shown with its code, never
  as having nothing open, and an owner's `withheld` count is shown when it is
  not zero; the command exits 1 when any owner is unavailable

### `weblisk approvals describe <id>`

Reads the decision at its owner, through the gateway: for content, the
proposal with the bytes it proposes (`GET /v1/content/proposals/{id}`).

### `weblisk approvals accept <id>` / `weblisk approvals reject <id> --reason <reason>`

```bash
$ weblisk approvals accept 9b2f61c0d4e8a7b3c5f1e6d2a8b4c7e0
✓ Applied at content: procedures/access-review.md
```

- Sends the person's decision, through the gateway, to the route the item's
  `decide` names, with the body that owner specifies: for content,
  `POST /v1/content/proposals/{id}/decision` with `decision` `apply`, and the
  change statement the person's sign-records credential signs, or `reject`
  with the reason ([`architecture/content`](content.md#who-may-move-an-entry))
- One decision at a time. Nothing is accepted in bulk, by filter or by priority
- Where the tenant declares that a decision needs more than one person, the
  owner records this person's and holds the item open until its rule is met
- Reason is required for rejections

---

## Objective Commands

A programme's objective is what a strategy was: what a tenant aims at,
held by the programme service with the programme that declares it
([`architecture/admin`](admin.md#programme-objectives)). It changes when the
adopted programme does, so these commands read and write nothing else.

### `weblisk objectives list`

Lists the objectives of the programmes adopted in scope, with their progress.

### `weblisk objectives describe <id>`

One objective, with its targets and what has been measured against them.

- Both address the programme service through the admin gateway. No blueprint
  specifies its objectives or a route for them yet, so the gateway answers
  `ADMIN_GROUP_UNAVAILABLE`, and each command reports objectives unavailable
  and exits 1

---

## Federation Commands

### `weblisk federations peers`

```bash
$ weblisk federations peers
NAME           TIER      JURISDICTION  STATUS   CAPABILITIES      EXPIRES
partner-corp   partner   US            active   seo:audit         2026-07-15
acme-eu        private   EU            active   content:analyze   2026-06-20
```

### `weblisk federations pending`

```bash
$ weblisk federations pending
ID       FROM            CAPABILITIES REQUESTED     RECEIVED
req-001  supplier-inc    logistics:track             2026-04-25 09:00
```

### `weblisk federations accept <id>` / `weblisk federations reject <id>`

```bash
$ weblisk federations accept req-001
✓ Accepted peering request from supplier-inc
  Granted: logistics:track
  Tier: partner
  Expires: 2026-07-25
```

### `weblisk federations revoke <name>`

```bash
$ weblisk federations revoke partner-corp
⚠ This will revoke all trust with 'partner-corp' and terminate active tasks.
  Type peer name to confirm: partner-corp
✓ Trust revoked for partner-corp.
```

- A destructive act: it needs its person's step-up
  ([Authentication Flow](#authentication-flow))

### `weblisk federations describe <name>`

Full detail for a federation peer.

```bash
$ weblisk federations describe partner-corp
Peer: partner-corp
Tier:         partner
Jurisdiction: US
Status:       active
Expires:      2026-07-15

Capabilities:
  seo:audit (inbound)

Data Contract:
  Inbound:   url, title, meta_description
  Outbound:  score, findings[], recommendations[]
  Forbidden: user_data, analytics, revenue
  Retention: 24h

Metrics (30d):
  Requests:    340
  Avg latency: 1.2s
  Error rate:  0.3%
```

### `weblisk federations contracts`

List all active data contracts across federation peers.

```bash
$ weblisk federations contracts
PEER            CAPABILITY       INBOUND FIELDS     OUTBOUND FIELDS    JURISDICTION  RETENTION
partner-corp    seo:audit        url,title,meta     score,findings     US            24h
acme-eu         content:analyze  url,body           quality_score      EU            12h
```

---

## Operator Commands

### `weblisk operators revoke <name>`

Revoke another operator's access (admin only).

```bash
$ weblisk operators revoke bob
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
- A destructive act: it needs its person's step-up
  ([Authentication Flow](#authentication-flow))

### `weblisk operators approve <name>`

Admit an operator whose registration is pending (admin only).

```bash
$ weblisk operators approve bob
✓ Operator 'bob' approved. They attest a credential of their own with: weblisk operator connect
```

- Calls `POST /v1/admin/operators/{name}/approve` at the admin gateway
  ([`architecture/admin`](admin.md#admitting-the-operators-after-the-first),
  `operator-approval`). Approving an operator already approved succeeds and
  changes nothing
- Prints no token and writes none: the approval returns none, and the
  approved person mints their own <!-- wl:id cli-operators-approve-no-token -->
- A destructive act, because it grants authority: it needs its person's
  step-up ([Authentication Flow](#authentication-flow))
- Refusing a registration is `weblisk operators revoke <name>`; there is no
  separate reject command

### `weblisk operators list`

List all registered operators and their status.

```bash
$ weblisk operators list
NAME    ROLE     STATUS    REGISTERED
alice   admin    active    2026-01-15T09:00:00Z
bob     viewer   revoked   2026-02-20T14:30:00Z
carol   admin    active    2026-03-01T11:00:00Z
```

### `weblisk operators describe <name>`

Full detail for a single operator.

```bash
$ weblisk operators describe alice
Operator: alice
Role:     admin
Status:   active
Registered: 2026-01-15T09:00:00Z
Last active: 2026-04-25T14:30:00Z
Key ID:      a1b2c3d4e5f6...
```

### `weblisk operators role <name> <role>`

Change an operator's role (admin only).

```bash
$ weblisk operators role bob operator
✓ Operator 'bob' role changed: viewer → operator
```

- Requires admin role
- Valid roles: `admin`, `operator`, `auditor`, `viewer`
- Cannot demote yourself (prevents accidental lockout)
- A destructive act: it needs its person's step-up
  ([Authentication Flow](#authentication-flow))

---

## Audit Commands

### `weblisk audit`

Stream or query the audit log.

```bash
$ weblisk audit
TIME        ACTOR           ACTION      TARGET          DETAIL
10:30:01    orchestrator    task        seo-analyzer    Forwarded seo-audit task
10:30:00    alice           decide      9b2f61c0d4e8    Applied procedures/access-review.md
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

## Test Commands

### `weblisk test conformance`

Run protocol conformance tests against a running system.

```bash
$ weblisk test conformance --orch http://localhost:9800
Running conformance suite against http://localhost:9800...

Level 1 — Protocol Basics (10 tests)
  ✓ L1-01  GET /livez and GET /readyz answer live and ready alone
  ✓ L1-03  POST /v1/register accepts valid manifest
  ✓ L1-04  POST /v1/register rejects bad signature
  ...
  ✓ L1-10  Errors answer in the protocol's error format

Level 2 — Behavior (18 tests)
  ✓ L2-01  Events delivered to scoped subscribers
  ...

Level 3 — Integration (8 tests)
  ✓ L3-01  Full workflow execution end-to-end
  ...

Results: 36/36 passed (0 failed, 0 skipped)
```

| Flag | Description |
|------|-------------|
| `--orch <url>` | The orchestrator's own address to test against, which is sent no person's token ([Configuration](#configuration)) |
| `--level <n>` | Run specific level only (1, 2, or 3) |
| `--test <id>` | Run a single test by ID (e.g., `L1-03`) |
| `--verbose` | Show request/response details for each test |
| `--json` | Machine-readable test results |

- Level 1: Protocol basics — registration, auth, the two probes, service directory
- Level 2: Behavior — event delivery, scoping, namespace enforcement
- Level 3: Integration — full lifecycle loop with real agents

### `weblisk test mock-orchestrator`

Start a lightweight mock orchestrator for local testing.

```bash
$ weblisk test mock-orchestrator --port 19800
Mock orchestrator running on http://localhost:19800
  - Accepts all valid registrations
  - Issues test tokens (24h TTL)
  - Stores registrations in memory
  Press Ctrl+C to stop.
```

| Flag | Description |
|------|-------------|
| `--port <n>` | Port to listen on (default: `19800`) |

- Verifies signature format but accepts any valid ML-DSA-65 signature
- Useful for agent development without a full hub running
- Does NOT forward tasks or events (registration and discovery only)

---

## Deploy Commands

### `weblisk deploy rollback`

Roll back a deployed environment to a previous version.

```bash
$ weblisk deploy rollback --env production
Rolling back production to previous version (v1.1.0 → v1.0.9)...
✓ Rollback complete. Current version: v1.0.9

$ weblisk deploy rollback --env production --version 1.1.0
Rolling back production to v1.1.0...
✓ Rollback complete. Current version: v1.1.0
```

| Flag | Description |
|------|-------------|
| `--env <name>` | Target environment (required) |
| `--version <v>` | Specific version to roll back to (default: previous) |

- Rollback redeploys the previous container image tag
- Audit entry is logged for the rollback event
- Auto-rollback is triggered if error rate exceeds 5% within 5
  minutes of a deploy (see patterns/deployment.md)

---

## Dependency Commands

### `weblisk deps audit`

Audit project dependencies for security vulnerabilities and policy
compliance.

```bash
$ weblisk deps audit
Checking dependency integrity...
✓ go.sum matches go.mod (47 dependencies, all pinned)
✓ No known vulnerabilities (checked against OSV database)
✓ No new dependencies since last audit

$ weblisk deps audit github.com/example/lib
Auditing github.com/example/lib v1.2.3...
  License:       MIT ✓
  Last release:  2026-03-15 (47 days ago) ✓
  Maintainers:   3 active ✓
  CVEs:          none ✓
  Dependents:    1,204 packages
  Verdict:       APPROVED
```

| Flag | Description |
|------|-------------|
| `--json` | Machine-readable output |

- Checks lockfile integrity (go.sum, package-lock.json, etc.)
- Queries the OSV database for known vulnerabilities
- Flags any new dependencies added since the last audit
- Per-package audit shows license, activity, and CVE history

---

## Policy Commands

### `weblisk policy validate`

Validate the gateway policy file for syntax and semantic errors.

```bash
$ weblisk policy validate
Validating policies.yaml...
✓ 12 policies parsed successfully
✓ No conflicting rules
✓ All referenced roles exist
✓ No unreachable rules detected
```

- Loads `policies.yaml` (or configured policy file path)
- Checks for syntax errors, conflicting rules, unreachable policies
- Validates that referenced roles and resources exist in the project

### `weblisk policy test`

Run policy assertions against sample requests.

```bash
$ weblisk policy test
Running policy test suite (policies_test.yaml)...
  ✓ admin can access /api/admin/users
  ✓ viewer cannot POST /api/admin/users
  ✓ unauthenticated blocked from /api/*
  ✓ rate limit applies to /api/public/*

4/4 assertions passed.
```

- Reads test cases from `policies_test.yaml`
- Each test case specifies a request (role, method, path) and
  expected outcome (allow/deny)
- Exit code 1 if any assertion fails

---

## Marketplace Commands

### `weblisk marketplace search <query>`

Search the marketplace for capabilities, blueprints, and agents.

```bash
$ weblisk marketplace search "demand forecasting"
ID        NAME                        TYPE          SELLER        PRICE     RATING
mkt-001   Demand Forecasting Agent    capability    acme-ai       $0.02/req  4.8★
mkt-002   Supply Chain Optimizer      capability    logicorp      $0.05/req  4.5★
mkt-003   Inventory Predictor         installable   predict-co    $99/mo     4.2★
```

### `weblisk marketplace describe <id>`

Full detail for a marketplace listing.

```bash
$ weblisk marketplace describe mkt-001
Listing: mkt-001
Name:     Demand Forecasting Agent
Type:     capability (live service)
Seller:   acme-ai
Price:    $0.02 per request
Rating:   4.8★ (142 reviews)

Description:
  ML-powered demand forecasting with 94% accuracy on retail data.
  Supports weekly and monthly prediction horizons.

Capabilities:
  forecast:demand (inbound: sku, history[])
                  (outbound: prediction, confidence, horizon)

Data Contract:
  Jurisdiction: US
  Retention:    none (stateless)
  Forbidden:    customer_pii, payment_data
```

### `weblisk marketplace buy <id>`

Purchase a marketplace capability or asset.

```bash
$ weblisk marketplace buy mkt-001 --accept-contract --accept-pricing
Purchasing 'Demand Forecasting Agent' from acme-ai...
✓ Purchase confirmed.
  Type:   live capability
  Access: federation peering initiated with acme-ai
  Status: Active — capability available in workflows
```

| Flag | Description |
|------|-------------|
| `--accept-contract` | Accept the data contract without interactive review |
| `--accept-pricing` | Accept the pricing terms without interactive review |

- Without flags, displays contract and pricing for interactive review
- For live capabilities: initiates federation peering automatically
- For installable assets: downloads the asset blueprint

### `weblisk marketplace install <id>`

Download and generate a purchased installable asset.

```bash
$ weblisk marketplace install mkt-003
Downloading 'Inventory Predictor' blueprint...
✓ Blueprint downloaded to agents/inventory-predictor/
  Run: weblisk agent create inventory-predictor --platform go
```

- Only works for installable-type purchases (not live capabilities)
- Downloads blueprint files and places them in the correct directory

### `weblisk marketplace list`

List active purchases and subscriptions.

```bash
$ weblisk marketplace list
ID        NAME                       TYPE          STATUS    COST(30d)
mkt-001   Demand Forecasting Agent   capability    active    $12.40
mkt-003   Inventory Predictor        installable   installed $99.00
```

### `weblisk marketplace publish`

Publish a capability or asset to the marketplace.

```bash
$ weblisk marketplace publish --type capability --config listing.yaml
Validating listing...
✓ Listing validated
✓ Data contract parsed
✓ Pricing terms set
Publishing to marketplace...
✓ Published as mkt-xxx: Demand Forecasting Agent
```

| Flag | Description |
|------|-------------|
| `--type <t>` | Listing type: `capability`, `installable` |
| `--config <file>` | Path to listing configuration YAML |

### `weblisk marketplace update <id>`

Update a published listing's pricing or metadata.

```bash
$ weblisk marketplace update mkt-xxx --price 0.03
✓ Listing mkt-xxx price updated: $0.02 → $0.03/req
```

### `weblisk marketplace delist <id>`

Remove a listing from the marketplace.

```bash
$ weblisk marketplace delist mkt-xxx --reason "end of life"
⚠ Active buyers will be notified. Existing contracts honored until expiry.
  Type listing ID to confirm: mkt-xxx
✓ Listing mkt-xxx delisted.
```

| Flag | Description |
|------|-------------|
| `--reason <text>` | Reason for delisting (required) |

### `weblisk marketplace dashboard`

View seller metrics for your published listings.

```bash
$ weblisk marketplace dashboard
LISTING     REVENUE(30d)  REQUESTS(30d)  ACTIVE BUYERS  RATING
mkt-xxx     $1,240.00     62,000         8              4.8★
mkt-yyy     $340.00       3,400          2              4.5★

Total revenue (30d): $1,580.00
```

### `weblisk marketplace reviews <id>`

View reviews for a listing you own.

```bash
$ weblisk marketplace reviews mkt-xxx
RATING  DATE        BUYER         TITLE
5★      2026-04-20  logicorp      Excellent accuracy
4★      2026-04-15  retailco      Good but slow on large datasets
5★      2026-04-10  supplier-inc  Perfect for our use case
```

### `weblisk marketplace review <id>`

Leave a review for a purchased listing.

```bash
$ weblisk marketplace review mkt-001 --rating 5 --title "Excellent accuracy"
✓ Review submitted for mkt-001.
```

| Flag | Description |
|------|-------------|
| `--rating <1-5>` | Star rating (required) |
| `--title <text>` | Review title (required) |

### `weblisk marketplace collaborations`

List all active marketplace collaborations (live capability connections).

```bash
$ weblisk marketplace collaborations
ID       PEER         CAPABILITY         STATUS    REQUESTS(30d)  COST(30d)
col-001  acme-ai      forecast:demand    active    620            $12.40
col-002  logicorp     logistics:track    active    1,200          $60.00
```

### `weblisk marketplace usage <id>`

View usage metrics for a specific collaboration.

```bash
$ weblisk marketplace usage mkt-001
Collaboration: col-001 (acme-ai / forecast:demand)
Period: 30 days

  Requests:       620
  Avg latency:    340ms
  Error rate:     0.2%
  Total cost:     $12.40
  Avg cost/req:   $0.02
```

### `weblisk marketplace terminate <id>`

Initiate termination of a marketplace collaboration.

```bash
$ weblisk marketplace terminate mkt-001
⚠ This will terminate the collaboration with acme-ai (forecast:demand).
  Active workflows using this capability will fail.
  Type listing ID to confirm: mkt-001
✓ Termination initiated. Grace period: 7 days.
```

---

## Configuration


| Source | Precedence | Location |
|---|---|---|
| Command-line flag | 1 — highest | `--orch https://hub.example.com` |
| Environment variable | 2 | Implementation-defined |
| Project config | 3 | `.weblisk/config.json` in the working directory |
| User config | 4 — lowest | `~/.weblisk/config.json` |

| Key | Type | Description |
|---|---|---|
| `orchestrator_url` | string | The hub's address an operator command uses when `--orch` is omitted: its admin gateway, where every request carrying the person's token goes, and never the orchestrator's own address. The key keeps the name it had before the admin gateway was the hub's one door |
| `operator_name` | string | Which identity to resolve; never a key or a passphrase |
| `default_format` | string | Output shape — `table` or `json` |
The CLI reads the hub's address, its admin gateway, from (in priority order):

1. Command-line flags: `--orch https://hub.example.com`
2. Environment variable (implementation-defined)
3. Project config: `.weblisk/config.json` in the working directory
4. User config: `~/.weblisk/config.json`

**`--orch` names one of two addresses, by command.** On an operator command,
one a person runs against a hub — every `weblisk operator` command and every
command that calls the hub's administrative routes — it is the hub's admin
gateway, and the sources above supply it when the flag is omitted. On a
command that runs, registers or tests a component —
[`weblisk component <name> init`](#weblisk-component-name-init),
[`weblisk agent start`](#weblisk-agent-start),
[`weblisk test conformance`](#weblisk-test-conformance), and the address
[`weblisk server start`](#weblisk-server-start) passes each sibling — it is
the orchestrator's own address, which a component registers with, and the
sources above are never read for it. Only the first is ever sent a person's
token.

### Config File

```json
{
  "orchestrator_url": "https://hub.example.com",
  "operator_name": "alice",
  "default_format": "table"
}
```

### Authentication Flow

Every command that calls the hub's admin gateway:

```
1. Resolve which identity acts: --keys-dir, else --identity <label>, else the unnamed default
2. Load the token stored beside that identity, where one is kept. With
   none, obtain one as step 3 says, and hold it in memory for this command
3. If it has expired, or less than a fifth of its lifetime remains, obtain a
   new one as architecture/admin's "Obtaining a token" says: the credential
   this identity holds for that hub (A credential for each hub) answers a
   challenge. The identity's holder (the encrypted key file, or a secret
   source) signs only to attest a credential where there is none the hub
   accepts. A hub that does not serve the credential routes still answers the
   identity-signed request with an operator token, and that path is deprecated.
   The identity-signed request names the recorded hub_id whichever path
   answers it, and is never sent to a hub with no registration recorded
4. Set Authorization: Bearer <token> on request
5. If 401 STEP_UP_REQUIRED → re-confirm the person, below → retry once.
   Never a refresh: a renewed token carries no step_up_at
6. If any other 401 response → attempt token refresh → retry once
7. If the hub refused the credential → print that the identity must attest a
   new one: "Run: weblisk operator connect". Otherwise print the hub's code
```

**A destructive act is re-confirmed by its person, and never by a renewal.**
A hub answers a destructive act on a token without a recent enough
`step_up_at` with `401` `STEP_UP_REQUIRED`, the challenge and the act in
`detail.control`, as [`architecture/admin`](admin.md#contracts)'s
`destructive-action-step-up` states, which this section does not restate.
The CLI then:

1. Asks the person to re-confirm that act, naming it: at a terminal, by the
   identity's passphrase typed there, or through an identity holder that itself
   asks the person, such as a vault's approval. A holder that releases the
   identity without asking anybody, such as one that remembered its passphrase,
   is not a re-confirmation, and the CLI never uses one for this
2. Mints a token through that re-confirmation: a challenge answered by the
   credential, its token request carrying `step_up` of form `identity`, the
   identity's signature over `weblisk/step-up/v1`, the `hub_id`, that nonce and
   the control (`operator-token-issuance`)
3. Holds that token for this command alone. It is never written to a token
   file, `--store` or not, and never handed to another program
4. Retries the act once. A second `STEP_UP_REQUIRED` is reported, not retried

Where nothing can ask the person, no terminal and no holder that asks, the
command fails with exit 2 and the challenge's `error_description`, and mints
nothing. A token the CLI renews silently never carries `step_up_at`, whatever
its age. <!-- wl:id cli-step-up-reconfirms -->

**A script re-confirms only when its command says so.** A destructive command
accepts `--step-up`: the identity's passphrase then arrives on stdin, as every
passphrase does, and the CLI makes the re-confirmation before it sends the act,
so the first request already carries a fresh `step_up_at`. The control it signs
is built from the command's own method and route template, the one the act's
provider would name in `detail.control`, never from an argument, so a script
cannot sign a control for any act but the one its command makes. The CLI
cannot tell a passphrase a person handed over for this run from one a script
read from storage, a CI secret included, and the hub cannot either: under form
`identity` what is proved is possession of the opened identity key, which
stands in for the person. A stored passphrase is therefore a standing step-up
for whoever holds it, as `architecture/threat-model` concedes for a thief of
the key and its passphrase, and storing one is the operator's own choice to
accept that. The flag records that the command was told to re-confirm, and
the audit records the act and the control; without the flag a script that
meets `STEP_UP_REQUIRED` fails as above. A holder
that releases the identity without asking anybody never re-confirms, with
`--step-up` or without. A test harness re-confirms this way, with a throwaway
identity held in a file and its passphrase written to stdin. <!-- wl:id cli-step-up-scripted -->

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid arguments, missing config) |
| 2 | Authentication error (no keys, expired token, rejected) |
| 3 | Connection error (the hub unreachable at the address the command uses) |
| 4 | Not found (agent, workflow, objective not found) |
| 5 | Permission denied (role insufficient) |

---

## Security

```yaml
security:
  trust_model:
    description: |
      The CLI runs with the full authority of the person invoking it, on their
      machine, and is therefore the most dangerous component in the framework to
      get wrong. It holds no secret of its own. Beside each identity it keeps
      one credential for each hub that identity attested, never in the clear,
      and mints short-lived tokens with it. The identity, whose private half
      may never be extractable, signs only to register, to attest, to change
      its own key and to re-confirm its person for a destructive act.
  boundaries:
    - boundary: Operator → CLI. The operator's identity authorises every
        privileged operation; the CLI holds no standing authority
    - boundary: CLI → Identity holder. A secret source that can sign keeps the
        private half and returns a signature. From one that cannot, the CLI gets
        the encrypted private half and its passphrase, decrypts it in memory,
        signs, and zeroises both (protocol/secret-source). An encrypted key file
        is decrypted in memory for one invocation, with the passphrase a person
        typed or a secret source remembers, and never written back in the clear
    - boundary: CLI → Admin gateway. Every operator command, authenticated per
        request with a short-lived token minted with the credential for that
        hub, over a transport the operator named. The person's token is
        presented there and nowhere else (protocol/identity, The pass)
    - boundary: CLI → Orchestrator. Only a command that runs, registers or
        tests a component, which acts as that component, and the first
        operator's registration at provision, which presents the bootstrap
        secret. Neither sends a person's token
    - boundary: CLI → Tenant component. The CLI runs with the person's
        authority and a component it starts receives none of it. Every start,
        a build's own runs of a generated component included, gives the
        component a closed allow-list of non-secret names, the values the CLI
        sets for that run, and what the tenant declares for it, in which a
        secret the CLI recognises is refused; no .env, .env.* (but
        .env.example) or, on cloudflare, .dev.vars file in the directory it
        starts in is tolerated; every build the CLI makes of a component's
        code, generation's included, gets the same environment and its
        toolchain's directories, with CARGO_HOME, npm_config_userconfig and
        npm_config_globalconfig always under the tenant's root; a start
        through npm gets those two npm files as well, and what npm itself adds
        it computes from them, its own install, the package, the directory
        and the account's home, HOME among them; an --orch carrying a user
        or password is refused; nothing else of the person or program that
        started the CLI reaches it, and no vendor key variable reaches any
        component, the orchestrator included (A component starts with a
        clean environment)
    - boundary: CLI → Provider CLI. A key the CLI reads from a holder or from
        standard input stays in the CLI's own process, which makes the call
        it is for. It is never exported into a provider CLI's environment, or
        any other child's, so such a key never substitutes for a provider
        CLI's own login. A vendor key variable already in the CLI's own
        environment when it was started is the starter's, and what a provider
        CLI inherits of it is not decided here. Nor is the environment of a
        build or run a coding-agent provider makes of the tree inside its own
        tool loop, which is the provider CLI's and outside the clean-start
        rule, which governs the CLI's own builds and starts
    - boundary: CLI → Local filesystem. Confined to the project and the
        operator's own configuration directory
  enforcement:
    - rule: A passphrase is never supplied on the command line or through the
        environment
      mechanism: Read from a non-echoing channel; protocol/identity states why
    - rule: A key or passphrase is never written to a log, a crash report or a
        cache
      mechanism: Redaction at the boundary of every diagnostic path
    - rule: A token is short-lived, and never minted with the identity
      mechanism: Minted with the credential for that hub and lasting an hour.
        Where a mint is silent, written nowhere by default and with --store
        kept beside the identity, mode 0600; where a mint asks the identity's
        holder, kept there by default and with --no-store written nowhere
    - rule: A credential key is never in the clear
      mechanism: Kept by the platform keychain source, apart from the
        identity's holder; where no keychain exists, in the weblisk-key-v1
        envelope or by a secret source, opened as the identity's own key is
    - rule: A tenant component inherits nothing from whoever started the CLI
      mechanism: Its environment is built from nothing on every start path,
        a build's own runs included, out of the closed allow-list, the run's
        own values and its declaration (A component starts with a clean
        environment); no vendor key variable is on the list
    - rule: A declaration never puts a secret the CLI can recognise into a
        component's environment
      mechanism: An agents[].env entry rule 16 recognises as a secret, by its
        name, a published vendor key prefix or a credential-shaped value, is
        refused, the whole declaration with it, when a component is generated
        and when one is started (schemas/config Validation Rules, rule 16)
    - rule: No file in a component's working directory puts back what its
        start left out
      mechanism: Every start, and each of a build's own runs, is refused
        while the directory the component starts in holds .env, any .env.*
        but .env.example, or on cloudflare .dev.vars or any .dev.vars.*; a
        cloudflare start is refused while its wrangler configuration's [vars]
        holds an entry rule 16 recognises as a secret
    - rule: Generated code a build runs inherits nothing from whoever started
        the CLI
      mechanism: Every build the CLI makes of a tenant component's code, a
        start's, tenant create's, weblisk dev's and generation's in Layer 2
        and its repair rounds alike, gets the component's clean environment
        plus its toolchain's own directories, and never the CLI's
        environment. CARGO_HOME, npm_config_userconfig and
        npm_config_globalconfig are always computed under the tenant's root,
        and a start through npm is given the same two npm files, so cargo and
        npm read no registry token
        through the account's home; the environment is all this governs, and
        a build still reads the account's files by path
    - rule: A key the CLI reads from a holder or from standard input never
        leaves the CLI's process
      mechanism: Held in memory and handed only to the call that uses it;
        never set in a child process's environment, a provider CLI's included
    - rule: A destructive operation requires explicit confirmation
      mechanism: Confirmation is a distinct argument, never a default, and never
        satisfied by a non-interactive invocation unless declared
```

---

## Implementation Notes

- All commands share a common `AdminClient` that handles auth,
  connection, and response parsing
- Table output uses fixed-width columns aligned to terminal width
- `--json` output is one JSON object per line (for piping to `jq`)
- `--watch` mode uses `GET` polling at 5-second intervals (not
  WebSocket — keeps the CLI simple)

## Verification Checklist
- [ ] Provenance is written into the tenant's own state, carrying what [`weblisk server init`](#weblisk-server-init) says it carries, not only printed
- [ ] A blueprint source with uncommitted or untracked changes records a `-dirty` revision, and the run says so before generating ([`weblisk server init`](#weblisk-server-init))

### Project & Development
- [ ] `weblisk new` scaffolds a project from weblisk-templates with correct name replacement ([`weblisk new`](#weblisk-new))
- [ ] `weblisk new` always generates the `.gitignore` [`weblisk new`](#weblisk-new) requires
- [ ] `weblisk new --template client/blog --template server/starter` merges both template sets ([`weblisk new`](#weblisk-new))
- [ ] `weblisk dev` starts a file-watching dev server with live reload for client projects ([`weblisk dev`](#weblisk-dev))
- [ ] `weblisk dev` builds and runs the hub with restart-on-change for server projects ([`weblisk dev`](#weblisk-dev))
- [ ] `weblisk build --minify --fingerprint` produces production-ready output ([`weblisk build`](#weblisk-build))
- [ ] `weblisk vendor` copies the Weblisk client framework to the specified directory ([`weblisk vendor`](#weblisk-vendor))
- [ ] Template resolution follows the priority [`weblisk new`](#weblisk-new) gives
- [ ] `weblisk doctor` validates .gitignore contains required secret exclusion entries ([`weblisk doctor`](#weblisk-doctor))
- [ ] `weblisk doctor` validates .weblisk/secrets/ file permissions are 0600 ([`weblisk doctor`](#weblisk-doctor))
- [ ] `weblisk doctor` cross-references secret declarations with stored values ([`weblisk doctor`](#weblisk-doctor))

### Secrets Management
- [ ] `weblisk secret list` shows all declared secrets and their set/missing status ([`weblisk secret`](#weblisk-secret))
- [ ] `weblisk secret set` prompts interactively for value (never passed as CLI argument) ([`weblisk secret`](#weblisk-secret))
- [ ] `weblisk secret set` writes to the path, and with the permissions, [`weblisk secret`](#weblisk-secret) gives
- [ ] `weblisk secret get` requires --confirm flag and prints a terminal-sharing warning ([`weblisk secret`](#weblisk-secret))
- [ ] `weblisk secret delete` removes the secret file ([`weblisk secret`](#weblisk-secret))
- [ ] `weblisk secret rotate` triggers the rotation handler or prompts for new value ([`weblisk secret`](#weblisk-secret))

### Server & Code Generation
- [ ] `weblisk tenant create` ends with the orchestrator and the admin gateway running and its first operator registered at the gateway, and its result's `address` is the gateway's origin with its `tls_pin`, which the registration it records keeps whether the CLI made the certificate or the operator supplied it, never the orchestrator's own address ([`weblisk tenant create <name>`](#weblisk-tenant-create-name), [`weblisk server provision`](#weblisk-server-provision)) <!-- wl:check cli-create-gateway covers cli-create-stands-up-gateway -->
- [ ] Before it starts the orchestrator, `weblisk tenant create` has written `admin_gateway`, `orchestrator.admin_addresses` naming the gateway's origin and `orchestrator.admin_gateway_identity` naming the fingerprint of `.weblisk/keys/admin-gateway.key`, and with `--port 0` the gateway's ports are free ones and are the ports those name ([`weblisk tenant create <name>`](#weblisk-tenant-create-name), [`architecture/admin`](admin.md#registration-lease-and-identity)) <!-- wl:check cli-create-declares-gateway covers cli-create-stands-up-gateway -->
- [ ] `weblisk server provision` registers the first operator with the bootstrap secret at the orchestrator's own address and keeps no token, then registers at the admin gateway's origin and records the registration, with the pin, at that address alone; no operator command afterwards sends a request, a token among it, to the orchestrator's own address ([`weblisk server provision`](#weblisk-server-provision), [Configuration](#configuration)) <!-- wl:check cli-provision-gateway covers cli-provision-registers-at-gateway -->
- [ ] `weblisk tenant create` writes the `.gitignore` `weblisk new` writes ([`weblisk tenant create <name>`](#weblisk-tenant-create-name)), so the directory it just put a private key in is not one `git init` from committing it
- [ ] `weblisk tenant create` emits the steps `provider · directory · generate · skills · provision · accept · done`, and renaming one breaks both front ends at once ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk tenant create` generates the orchestrator and the admin gateway only; every other component is added afterwards, and the command does not claim otherwise ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk tenant accept` reports a `404` as an absent route and a `401` as a pass, and a failed non-essential check does not fail the tenant ([`weblisk tenant accept`](#weblisk-tenant-accept))
- [ ] `weblisk tenant accept` probes `GET /v1/admin/overview` at the admin gateway's origin with no token and passes on `401`; against a gateway whose certificate does not match the pin it fails, sending nothing over that connection ([`weblisk tenant accept`](#weblisk-tenant-accept)) <!-- wl:check cli-accept-gateway covers cli-accept-through-gateway -->
- [ ] `weblisk tenant create` asks no model provider anything until the orchestrator's blueprint resolves, the resolved corpus parses and the platform's toolchain is present ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk tenant create --port 0` starts the orchestrator on a free port chosen when it is started, and the result reports that port ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk tenant create` declares the port it started the orchestrator on nowhere in the tenant's configuration ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk tenant create` writes no token to a file and prints none without `--json`; the `--json` result is the only place a token may go, and while `create` makes no address to connect to, it carries none ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk tenant create --json`'s result carries `model` only where `--model` named one ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk providers --json` marks at most one backend `default`, the one the CLI's own model would start with, and marks none when there would be nothing to start with ([`weblisk providers`](#weblisk-providers))
- [ ] `weblisk providers --json` says `local` only for a model server on this machine's loopback address, judged from the address's host — never for a coding-agent CLI, a `WL_AI_COMMAND` tool, or a server at another host ([`weblisk providers`](#weblisk-providers))
- [ ] `weblisk component help` lists a component only when the pipeline will read that component's own blueprint, so a listed kind is never generated from the protocol alone ([`weblisk component <name> init`](#weblisk-component-name-init))
- [ ] `weblisk component <name> init` ends on the best tree it reached and never a worse one — on an error too — names the requirements it left unrepaired, and a re-run starts from that tree ([`weblisk component <name> init`](#weblisk-component-name-init), [`architecture/generation`](generation.md#a-repair-round-is-a-transaction))
- [ ] `weblisk server init` reads YAML specs and dispatches to the configured LLM for code generation ([`weblisk server init`](#weblisk-server-init))
- [ ] `weblisk server start` reads .weblisk/config.yaml and builds+starts all declared components ([`weblisk server start`](#weblisk-server-start))
- [ ] A component whose section names `key_passphrase` receives the passphrase the named source returns as one line on its standard input, and in no argument, environment variable or file; one reference is asked once for every component naming it; a source that does not answer starts nothing; a component with no `key_passphrase` receives nothing on its standard input ([`weblisk server start`](#weblisk-server-start), [`schemas/config`](../schemas/config.md#service-key-passphrases)) <!-- wl:check start-passphrase-stdin covers start-injects-passphrase -->
- [ ] `weblisk server start` starts the orchestrator alone when `.weblisk/config.yaml` is absent, reporting it as a hub with no admin gateway, refuses a present file with no `admin_gateway` section before starting anything, naming `weblisk component admin init`, and refuses a declaration it cannot carry out before starting anything ([`weblisk server start`](#weblisk-server-start))
- [ ] `weblisk server stop` with no `--component` stops every recorded component, the orchestrator last ([`weblisk server start`](#weblisk-server-start))
- [ ] `weblisk component <name> start|stop|status|logs` runs any component the tenant has generated, and a detached start reports started only once the component's `GET /livez` answers live, then waits on its `GET /readyz` and reports a component that never becomes ready as not ready ([`weblisk component <name> start`](#weblisk-component-name-start--stop--status--logs))
- [ ] Every start of a tenant component — `weblisk server start` attached or detached, `weblisk component <name> start`, the orchestrator `weblisk tenant create` starts, `weblisk agent start`, `weblisk domain start`, `weblisk gateway start`, and the first run and each restart `weblisk dev` makes of a hub — gives it an environment built from nothing: the names in the allow-list of [A component starts with a clean environment](#a-component-starts-with-a-clean-environment) that are set in the CLI's own, `WL_PORT`, `WL_ORCH_URL` where an orchestrator is named or running and the component is not it, `npm_config_userconfig` and `npm_config_globalconfig` where its run command is npm's, and its declared `env`, and no other name of the CLI's environment
- [ ] No vendor key variable — `WL_AI_KEY`, or any variable a model backend names for its key — is in any started component's environment, the orchestrator's included, even when the CLI's own environment holds it ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] A build's own runs of a generated component, its conformance run and its interoperability run, give it the same environment a real start does, with `WL_DEV=1` the only addition ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] A component other than the orchestrator, started while an orchestrator is named by `--orch` or recorded as running for the tenant, has `WL_ORCH_URL` set to that orchestrator's own address and the same address in `--orch` among its arguments; started with none named or running, it has neither, on a real start and on a build's own runs alike, except as the next line says ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] On each of a build's own runs with no orchestrator of the run's own, a component whose configuration gives its orchestrator address a default is given `WL_ORCH_URL` and `--orch` as item 2 of [A component starts with a clean environment](#a-component-starts-with-a-clean-environment) says, and an orchestrator listening at that default receives no request from it; a component with no such default is given neither
- [ ] Every start, and each of a build's own runs, is refused, naming the file, while the directory the component would start in holds `.env`, any `.env.*` other than `.env.example`, or, on the cloudflare platform, `.dev.vars` or any `.dev.vars.*` ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] A cloudflare start is refused, naming each entry, while its wrangler configuration's `[vars]` holds an entry rule 16 of [`schemas/config`](../schemas/config.md#validation-rules) recognises as a secret
- [ ] Each of a build's own runs of a component — the conformance run and the interoperability run, repair rounds included — starts it in an empty working directory made for that run and removed after it, never the tenant's root, and after the run the tenant's root holds nothing the run wrote ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] Every build the CLI makes of a tenant component's code — before `weblisk agent start`, `domain start`, `gateway start`, `server start` or `component <name> start` runs it, the orchestrator's in `weblisk tenant create`, each `weblisk dev` makes, and generation's in Layer 2 and in every repair round — gets the component's clean environment plus only `GOCACHE`, `GOMODCACHE` and `GOPATH`, `CARGO_HOME` and `RUSTUP_HOME`, or `npm_config_cache`, `npm_config_userconfig` and `npm_config_globalconfig`, as its toolchain uses, and no vendor key variable; `CARGO_HOME`, `npm_config_userconfig` and `npm_config_globalconfig` are always under the tenant's root and never the CLI's, and every other one the CLI's environment does not set is the toolchain's own default under the home of the account the CLI runs as (so `RUSTUP_HOME` is `<home>/.rustup`), which a build on a default toolchain install finds, while the home itself is never passed ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] A start whose run command is npm's, and each of a build's own runs of one, has `npm_config_userconfig` and `npm_config_globalconfig` each naming an empty file under the tenant's root, so neither the starting account's `~/.npmrc` nor the global `npmrc` under Node's install prefix reaches the component as `npm_config_*` or `NODE_OPTIONS` ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] An `--orch` that carries a user or a password before its host is refused before anything is built or started ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] The CLI gives no started component `HOME`, `USERPROFILE`, `APPDATA` or `LOCALAPPDATA`, and none is in any started component's environment except the `HOME` npm itself sets for a component whose run command is npm's ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] No started component's environment holds `SSL_CERT_FILE`, `SSL_CERT_DIR`, `NODE_EXTRA_CA_CERTS` or a proxy variable, in either case, that the CLI's environment holds, unless that component's own declaration names it ([A component starts with a clean environment](#a-component-starts-with-a-clean-environment))
- [ ] An `agents[].env` entry that [`schemas/config`](../schemas/config.md#validation-rules) rule 16 recognises as a secret — by its name, by a published vendor key prefix, or by a PEM block or a URL with a user or password — is refused, naming every such entry, by the commands that generate a component and by every start, before anything is generated or started
- [ ] A key the CLI reads from a holder or from standard input is used in the CLI's own process and is in no child process's environment, a provider CLI's included ([Security](#security))
- [ ] `weblisk tenant create` writes its `.gitignore` before generation, amends one already present, and does not `git init` ([`weblisk tenant create <name>`](#weblisk-tenant-create-name))
- [ ] `weblisk server verify` passes or fails on the orchestrator's `GET /livez` and `GET /readyz` alone, reads every registered component's lease state from `GET /v1/admin/agents` on the operator's token, says the lease states were not read when it holds no token the admin API accepts, probes no other component, and reports a lease reading `not_ready` as not ready and one reading `unknown` as unknown, neither failing the verify ([`weblisk server verify`](#weblisk-server-verify))
- [ ] `weblisk agent create` generates agent code from agent.yaml spec via LLM dispatch ([`weblisk agent create`](#weblisk-agent-create), [`weblisk server init`](#weblisk-server-init))
- [ ] `weblisk agent start` builds and runs a single agent with --orch and --port flags ([`weblisk agent start`](#weblisk-agent-start))
- [ ] `weblisk agent list` lists all locally scaffolded agents ([`weblisk agent list`](#weblisk-agent-list))
- [ ] `weblisk domain create` generates domain controller code from domain.yaml spec via LLM dispatch ([`weblisk domain create`](#weblisk-domain-create))
- [ ] `weblisk domain start` builds and runs a single domain controller ([`weblisk domain start`](#weblisk-domain-start))
- [ ] `weblisk gateway create` generates gateway code from hub configuration ([`weblisk gateway create`](#weblisk-gateway-create))
- [ ] `weblisk gateway start` builds and runs the application gateway ([`weblisk gateway start`](#weblisk-gateway-start))
- [ ] `weblisk tenant export` refuses an existing `--out` with `TENANT_BUNDLE_EXISTS`, a component built from a `-dirty` revision with `TENANT_PIN_DIRTY`, and a record store without `backup-restore` with `TENANT_RECORDS_UNCAPTURED`, each writing no `manifest.json` ([Tenant export and rebuild codes](#tenant-export-and-rebuild-codes))
- [ ] `weblisk tenant export` writes no private key, passphrase, store or generated file into the bundle, and writes `manifest.json` last ([`weblisk tenant export`](#weblisk-tenant-export))
- [ ] `weblisk tenant rebuild` refuses a non-empty `--dir` with `TENANT_REBUILD_NOT_EMPTY` and a bundle file whose digest is not the manifest's with `TENANT_MANIFEST_INVALID`, before anything is written ([Tenant export and rebuild codes](#tenant-export-and-rebuild-codes))
- [ ] `weblisk tenant rebuild` reads each component's blueprints from a clone at its pinned revision, never from a source's `HEAD`, and exits 3 with `TENANT_PIN_UNAVAILABLE` where the revision cannot be read ([`weblisk tenant rebuild`](#weblisk-tenant-rebuild), [Tenant export and rebuild codes](#tenant-export-and-rebuild-codes))
- [ ] `weblisk tenant rebuild` refuses a missing or mismatched key with `TENANT_KEY_UNAVAILABLE` and a store not at its head with `TENANT_STORE_MISMATCH`, minting no key and adopting no store ([Tenant export and rebuild codes](#tenant-export-and-rebuild-codes))
- [ ] `weblisk tenant rebuild` ends in `done` only where the comparison of the two manifests finds nothing, and otherwise exits 1 with `TENANT_REBUILD_DIFFERS`, printing each differing row with both values ([Tenant export and rebuild codes](#tenant-export-and-rebuild-codes))

### Blueprint Management
- [ ] `weblisk blueprint update` re-fetches all cached blueprint sources and resets each clone to the commit fetched, so an edit made in a clone to a file its source holds does not survive; a source it cannot reach keeps the last version fetched, and the command says so ([`weblisk blueprint update`](#weblisk-blueprint-update))
- [ ] `weblisk validate` checks blueprint compliance (frontmatter, sections, types, deps) ([`weblisk validate`](#weblisk-validate))
- [ ] `weblisk pattern apply` reads pattern blueprint, dispatches to LLM with target context ([`weblisk pattern apply`](#weblisk-pattern-apply))
- [ ] Blueprint resolution follows the order of [Where blueprints come from](#where-blueprints-come-from), judged in the directory a command works in
- [ ] `weblisk tenant create` judges steps 0 and 1 in the tenant's directory, so standing in a corpus checkout does not make it read that checkout ([Where blueprints come from](#where-blueprints-come-from))
- [ ] A source read in place — step 0 or the project's `blueprints/` — is never refreshed, and every command but `weblisk blueprint update` refreshes a clone before reading it only once the clone is a day old ([Where blueprints come from](#where-blueprints-come-from))
- [ ] A command other than `weblisk blueprint update` holds its refresh while the directory it works in has generated work banked ([Where blueprints come from](#where-blueprints-come-from))
- [ ] `weblisk blueprint sources --json` lists every source in precedence order with `kind`, `from`, `dir`, `revision`, and for a clone `origin`, `present`, `fetched_at` and `stale` — and clones and fetches nothing ([`weblisk blueprint sources`](#weblisk-blueprint-sources))
- [ ] A failed refresh of a clone is not tried again for a day by any command but `weblisk blueprint update`, which does not wait, and a refresh that fails, `weblisk blueprint update`'s included, leaves the clone's `fetched_at`, and the age a build prints for it, at the last refresh that worked ([Where blueprints come from](#where-blueprints-come-from), [`weblisk blueprint sources`](#weblisk-blueprint-sources))
- [ ] `weblisk validate <dir>` reports only that directory's files as findings, and a corpus directory is checked against nothing but itself ([`weblisk validate <dir>`](#one-repository-weblisk-validate-dir))
- [ ] A file the repository holds is the copy `weblisk validate <dir>` checks, even when it does not parse: another source's file of the same name is never read in its place ([`weblisk validate <dir>`](#one-repository-weblisk-validate-dir))
- [ ] `weblisk blueprint sources` and `weblisk validate <dir>` read a working tree's revision without writing to it or taking its index lock ([`weblisk blueprint sources`](#weblisk-blueprint-sources), [`weblisk validate <dir>`](#one-repository-weblisk-validate-dir))
- [ ] `weblisk validate <dir>` reports every family the schemas declare that the directory holds, with how many of its files were checked, and a directory holding none says so ([`weblisk validate <dir>`](#one-repository-weblisk-validate-dir))
- [ ] `weblisk validate <dir>` checks programmes for each rule [`weblisk validate <dir>`](#one-repository-weblisk-validate-dir) lists for them, a fault wherever one fails; warns of a placed artifact that no spec in the repository defines; and checks programmes for nothing else
- [ ] `weblisk validate --json` without a directory is refused, and with one prints the report and exits non-zero when there is a fault ([`weblisk validate`](#weblisk-validate))

### Identity & Operations
- [ ] `weblisk operator init` creates the identity that `--keys-dir`, `--identity` or the unnamed default `~/.weblisk/keys/` selects, with 0700 directory and 0600 file permissions ([`weblisk operator init`](#weblisk-operator-init), [Where an identity lives](#where-an-identity-lives))
- [ ] `weblisk operator init` without `--holder` prompts for passphrase (min 12 chars), encrypts private key with Argon2id + AES-256-GCM ([`weblisk operator init`](#weblisk-operator-init), [Where an identity lives](#where-an-identity-lives))
- [ ] `weblisk operator init` passphrase cannot be skipped or supplied as CLI argument ([`weblisk operator init`](#weblisk-operator-init))
- [ ] `weblisk operator init --holder <source>` writes no private key beside the identity and asks for no passphrase ([`weblisk operator init`](#weblisk-operator-init))
- [ ] `weblisk operator init --vault <vault>` behaves exactly as `--holder 1password --holder-opt vault=<vault>` ([`weblisk operator init`](#weblisk-operator-init))
- [ ] `weblisk operator store --holder <source>:<reference>` writes `operator.pub` and `holder.json` and no private key, and only once a probe signed through the reference verifies against the public key; before `weblisk/holder-probe/v1` has test vectors it writes them unproven, says so, and refuses any signature through the reference that does not verify against that key, in this command or a later one, never sending it ([`weblisk operator store`](#weblisk-operator-store))
- [ ] `weblisk operator init --holder <source> --remember-passphrase` writes an encrypted `operator.key`, asks for the passphrase, and has the source keep only that passphrase; `holder.json` records `holds: ["passphrase"]` ([`weblisk operator init`](#weblisk-operator-init))
- [ ] `weblisk operator store --holder <source> --remember-passphrase` keeps the existing key file, and has the source keep its passphrase only after checking that it opens the key ([`weblisk operator store`](#weblisk-operator-store))
- [ ] `--identity <label>` resolves to the same location on every run, and `weblisk operator path --identity <label>` reports it ([Where an identity lives](#where-an-identity-lives), [`weblisk operator path`](#weblisk-operator-path))
- [ ] `weblisk operator init --json` prints `name`, `keys_dir`, `public_key`, `holder` and `created`, carries no private key and no passphrase, and writes nothing else to stdout; `holder` is the holder reference `holder.json` records, `holds` included, and `null` where there is no `holder.json` ([`weblisk operator init`](#weblisk-operator-init))
- [ ] `--keys-dir` outranks `--identity` when both are given ([Where an identity lives](#where-an-identity-lives))
- [ ] `weblisk operator connect` asks for no passphrase when a secret source holds the identity's passphrase ([`weblisk operator connect`](#weblisk-operator-connect))
- [ ] `weblisk operator connect` reports `connected`, `pending_approval`, `not_registered`, `refused`, `identity_unavailable`, `unreachable` or `pin_mismatch`, and with `--json` an `identity_unavailable` result carries `source` and `code`, and every result carries the `address`, and the `tls_pin` where its registration records one ([`weblisk operator connect`](#weblisk-operator-connect))
- [ ] `weblisk operator connect`, `weblisk operator attest` and `weblisk operator attest --batch` never send a registration: at an address no registration names, or a hub that answers `OPERATOR_UNKNOWN`, each reports `not_registered` naming `weblisk operator register` and the address, and against a test hub with no operators none of them sends a bootstrap secret or claims the hub ([`weblisk operator register`](#weblisk-operator-register), [`weblisk operator connect`](#weblisk-operator-connect))
- [ ] `weblisk operator connect` with no identity held reports `identity_unavailable`, names `weblisk operator init` and creates no key; `connect --no-register` is accepted and behaves exactly as `connect` ([`weblisk operator connect`](#weblisk-operator-connect))
- [ ] `weblisk operator init` does not overwrite existing keys without --force flag ([`weblisk operator init`](#weblisk-operator-init))
- [ ] `weblisk operator register` signs the registration payload with the operator's private key and returns the token it obtains, writing it beside the identity as [Where a token is kept](#weblisk-operator-token) says
- [ ] `weblisk operator register --bootstrap <path>` sends the bootstrap secret read from that file, and the secret is never accepted as an argument ([`weblisk operator register`](#weblisk-operator-register))
- [ ] `weblisk operator token` refreshes the token when it has expired or less than a fifth of its lifetime remains, without asking the identity to sign anything but an attestation ([Authentication Flow](#authentication-flow) step 3)
- [ ] Where the credential for the hub is kept by the keychain source and answers the hub's challenge, `weblisk operator connect`, `weblisk operator register` and `weblisk operator token --refresh` without `--store` return the token on stdout or in the `--json` result and write no token file, and a later command mints its own without asking the person or the identity's holder; with `--store` they also write it beside the identity, mode 0600 ([`weblisk operator token`](#weblisk-operator-token))
- [ ] Where a mint asks the identity's holder (no keychain source, the keychain source answering `not_installed`, or only the identity-signed path yielding a token), `weblisk operator connect`, `weblisk operator register` and `weblisk operator token --refresh` write the token beside the identity, mode 0600, and a later command uses it without asking the holder until it is due for refresh; with `--no-store` they return it on stdout or in the `--json` result and write no token file ([`weblisk operator token`](#weblisk-operator-token))
- [ ] With no stored token, plain `weblisk operator token` reports `no stored token`, the operator, the hub and whether a mint there is silent, and mints nothing ([`weblisk operator token`](#weblisk-operator-token))
- [ ] `--cap content:read,content:describe` on `weblisk operator connect` or `weblisk operator token --refresh` returns a token whose `cap` names those two alone, and is refused with `--store`, and, where a mint asks the identity's holder, without `--no-store` ([`weblisk operator token`](#weblisk-operator-token), [`weblisk operator connect`](#weblisk-operator-connect))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, `weblisk operator attest` signs only an `Attestation` it builds itself, refuses a `--days` beyond admin's cap, submits it, reports the credential's `cid` and `not_after`, and writes nothing to disk ([`weblisk operator attest`](#weblisk-operator-attest))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, attesting at several hubs asks the identity once: one passphrase for an encrypted key file, or, for a source that lists `sign_batch`, one `sign` request carrying every hub's attestation-token request and `Attestation`; a source that does not list it is asked once for each, after the CLI has said how many approvals that takes ([One approval vouches for every hub](#one-approval-vouches-for-every-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, each hub is sent an `Attestation` naming only its own `hub_id`, its recorded `identity_id` and the credential key made for it, no `Attestation` names more than one hub, and one is submitted only where that hub's attestation-token answer names the same `identity_id` ([One approval vouches for every hub](#one-approval-vouches-for-every-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, a credential attested between renewals takes the `not_after` the device's other attestations share; once one has fewer than 7 days left every command that mints a token warns, and the next `connect` renews every attestation on the device in one approval, each with `not_after` 30 days ahead and its `cid` unchanged ([One approval vouches for every hub](#one-approval-vouches-for-every-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, `weblisk operator attest --batch <path>` attests every entry in one approval of the identity and, with `--json`, answers an array in the order of the entries, each with `orch` and either `cid` and `not_after` or `code` ([`weblisk operator attest`](#weblisk-operator-attest))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, connecting, switching from one hub to another and refreshing a token ask the identity to sign nothing while this device holds an attested credential at that hub that is not due ([One approval vouches for every hub](#one-approval-vouches-for-every-hub))
- [ ] Every `Attestation` the CLI builds names the `identity_id` the hub's attestation-token answer carries, never one computed from the identity key, so an identity that changed its key still attests at every hub that accepted the change ([`weblisk operator attest`](#weblisk-operator-attest))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, `connect` and `register` generate one ML-DSA-65 credential per identity per hub the first time they reach it, have the identity attest it once, keep its private key in the platform keychain source apart from the identity's holder, or, only where no keychain exists, in the `weblisk-key-v1` envelope or the identity's secret source, and mint every later token with it without the identity signing ([A credential for each hub](#a-credential-for-each-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, on a platform with a keychain source, the credential key of an identity held by an encrypted key file or by a vault is written to the keychain and not beside the identity or in the vault, and a token is minted with it while the session is unlocked with no passphrase typed and no vault approval asked ([A credential for each hub](#a-credential-for-each-hub))
- [ ] `connect`, `register` and `operator token` take the deprecated identity-signed path only at a hub that answers `POST /v1/admin/credentials/challenge` `404` or `405`, and at a hub that serves it obtain every operator token with a credential ([A credential for each hub](#a-credential-for-each-hub))
- [ ] For every vector in [`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json) under a prefix the CLI signs, `weblisk/auth/v1` and `weblisk/credential-auth/v1`, the CLI, which signs those statements and verifies neither, passes the test [`architecture/generation`](generation.md#published-test-vectors) gives for a component that signs
- [ ] Once `weblisk/credential-auth/v1` has test vectors, where no keychain exists, for an identity held by a secret source whose `capabilities` do not list `store`, `connect` keeps the new credential key beside the identity in its own `weblisk-key-v1` envelope with `kdf` `argon2id`, under a passphrase the person chose for it, and never in the clear or under `kdf` `none` ([A credential for each hub](#a-credential-for-each-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, where no keychain exists, for an identity held by a source that lists `store` but answers `named_fields` false, or names `private_key` in `withheld_fields`, `connect` keeps the credential key in its own envelope beside the identity, never in that source, and signs every later challenge with it ([A credential for each hub](#a-credential-for-each-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, `connect --remember-passphrase` for such an identity has a source that lists `store` keep the envelope's passphrase, and is refused, keeping nothing, when neither the identity's source nor one named with `--passphrase-holder` lists `store` ([A credential for each hub](#a-credential-for-each-hub), [`weblisk operator connect`](#weblisk-operator-connect))
- [ ] `register`, and nothing else, records a registration from the registration answer, approved, pending or a repeat, naming its `hub_id`, the operator name it recorded, the `identity_id` it answered and the address it was reached at; discarding a credential after `CREDENTIAL_UNKNOWN` keeps the registration, and `OPERATOR_REVOKED` or `OPERATOR_UNKNOWN` is reported and removes it only when the person confirms; under `--json` it is kept ([A credential for each hub](#a-credential-for-each-hub))
- [ ] The CLI asks for an attestation token only by signing `{hub_id, jti, name, timestamp}` with the `hub_id` of a recorded registration and a `jti` of at least 128 random bits drawn for that request, never `{name, timestamp}` or `{hub_id, name, timestamp}`; two requests from one identity in the same second carry different `jti`s; a request is never sent twice; `TOKEN_REQUEST_REPLAYED` is reported and never leads to a registration; and at an address no registration names it asks for none, so an operator registered from another device records the hub's `hub_id` by `weblisk operator register`, which the hub answers as a repeat ([`weblisk operator attest`](#weblisk-operator-attest), [One approval vouches for every hub](#one-approval-vouches-for-every-hub), [A credential for each hub](#a-credential-for-each-hub))
- [ ] A registration answer from an address no registration names, naming a `hub_id` recorded at another address, moves nothing: the CLI reports both addresses and signs nothing more there, and moves the registration only when the person confirms at a terminal, never with `--json`, `--batch` or no terminal ([A credential for each hub](#a-credential-for-each-hub))
- [ ] Once `weblisk/hub-proof/v1` has test vectors, `register` at an address no registration names asks `POST /v1/admin/hub/proof` there with the origin dialled and a fresh challenge before it sends a registration, and records nothing and signs nothing more there where the proof is refused or absent, names another origin, carries a `public_key` whose fingerprint is not its `hub_id`, does not verify, or names a `hub_id` the registration answer does not; a test hub that relays both requests to a second hub, which lists only its own address, leaves no registration recorded ([A credential for each hub](#a-credential-for-each-hub))
- [ ] Once `weblisk/hub-proof/v1` has test vectors, a registration recorded before them through a test hub that relays to a second hub is proven at its next contact, before any identity or credential signature is sent there, and the CLI then signs nothing more at that address and reports it; a registration whose address proves its `hub_id` is recorded as proven and not asked again ([A credential for each hub](#a-credential-for-each-hub))
- [ ] Once `weblisk/credential-auth/v1` has test vectors, `weblisk operator attest --batch` whose entries include hubs this device has no registration for answers each of those entries `not_registered`, signs and sends nothing for it, registers nowhere, and attests the other entries asking a source that lists `sign_batch` and never releases the key once, whatever the number of hubs ([One approval vouches for every hub](#one-approval-vouches-for-every-hub), [`weblisk operator attest`](#weblisk-operator-attest))
- [ ] A hub at a recorded address whose challenge names a `hub_id` other than the recorded one, or that refuses the recorded one with `CREDENTIAL_FOREIGN_HUB`, is reported naming both, and the CLI signs nothing more for it until `weblisk operator register` there records that hub's own registration ([A credential for each hub](#a-credential-for-each-hub))
- [ ] `weblisk operator rotate` writes the next key and a rotation record listing every registration `pending` before it sends anything, then sends `POST /v1/admin/operators/{name}/key` to each registration with its own name and `hub_id`, signed by the old key and the new, a hub whose credential was discarded included ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] With one of three hubs unreachable, `rotate` marks two `changed` and one `pending`, keeps the old key, and exits non-zero naming the pending hub; `operator.pub` holds the new key, and a `register` at a fourth hub signs with the new key ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `weblisk operator rotate --resume` against the hub left `pending` signs the change with the old key it still records and the new key, the hub answers `200` with the same `identity_id`, and only then is the old private key destroyed and its public half kept as `operator.pub.retired` ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `weblisk operator connect` to a hub left `pending` by a rotation sends that hub the key change before it attests, and attests with the new key; when the change is refused it signs nothing there ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `weblisk operator rotate` while a rotation is pending is refused without `--resume`, and generates no second key ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `weblisk operator rotate --abandon <hub_id>` asks for confirmation, removes that hub and its registration from the rotation, and the rotation then finishes with the old private key destroyed when no other hub is still pending; with one still pending, the old private key is kept ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] A hub that applied a key change and whose `200` was lost is left `pending`; `rotate --resume`, or `connect` to it, sends the change again over a fresh timestamp, the hub answers `200` as a repeat, the hub is marked `changed`, and the rotation finishes ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] During a rotation, a hub that answers `OPERATOR_UNKNOWN` stays `pending` with its registration kept, and the rotation does not finish until the person abandons it with confirmation ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `--abandon` accepts a `refused` hub, and the rotation then finishes ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `weblisk operator rotate` with no registrations, or with a credential kept under a `hub_id` that has no registration, is refused naming each such `hub_id`, generates no key, and with `--json` stays refused ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] While an encrypted-file rotation is pending, a signature the identity makes verifies under `operator.pub` and was made with `operator.key.next`, and `weblisk operator path` names `operator.key.next` as the key that signs ([`weblisk operator rotate`](#weblisk-operator-rotate), [`weblisk operator path`](#weblisk-operator-path))
- [ ] For an identity held by a source that signs and withholds `private_key`, `weblisk operator rotate` without `--new-holder` is refused and says why; with `--new-holder <source>:<reference>` it maps that key only once a signature through it verifies, and never asks the source to create one ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] For an identity held whole by a source, `rotate` stores the new key in that source with `store`, and on finishing points `holder.json` at it and `erase`s the old reference, reporting a source that does not list `erase` ([`weblisk operator rotate`](#weblisk-operator-rotate))
- [ ] `weblisk operators revoke` invalidates target operator's public key and tokens (admin only) ([`weblisk operators revoke <name>`](#weblisk-operators-revoke-name))
- [ ] `weblisk operators revoke` prevents self-revocation and revoking the last admin ([`weblisk operators revoke <name>`](#weblisk-operators-revoke-name))
- [ ] `weblisk operators list` shows all registered operators with name, role, status, and registration date ([`weblisk operators list`](#weblisk-operators-list))
- [ ] `weblisk operators describe` shows full detail for a single operator ([`weblisk operators describe <name>`](#weblisk-operators-describe-name))
- [ ] `weblisk operators role` changes operator role (admin only, cannot demote self) ([`weblisk operators role <name> <role>`](#weblisk-operators-role-name-role))
- [ ] `weblisk operators approve <name>` sends `POST /v1/admin/operators/{name}/approve` to the hub's admin gateway, reports success for an operator already approved, and prints and writes no token ([`weblisk operators approve <name>`](#weblisk-operators-approve-name)) <!-- wl:check cli-operators-approve covers cli-operators-approve-no-token -->
- [ ] All commands output human-readable tables by default and structured JSON with --json flag ([Design Principles](#design-principles) 3)
- [ ] Destructive commands (agents deregister, federations revoke) require --confirm or interactive name-confirmation ([Design Principles](#design-principles) 2)
- [ ] `weblisk approvals reject` requires a --reason argument for every rejection ([`weblisk approvals reject`](#weblisk-approvals-accept-id--weblisk-approvals-reject-id---reason-reason))
- [ ] `weblisk approvals list` calls `GET /v1/admin/approvals`, reports the inbox unavailable and exits 1 when the gateway answers `ADMIN_GROUP_UNAVAILABLE`, shows each owner the gateway names under `unavailable` with its code and exits 1 when any is, and shows each owner's non-zero `withheld` count; `weblisk approvals accept` and `reject` send one decision to the route the item's `decide` names, never in bulk, and no `weblisk observations` or `weblisk strategies` command exists ([Approval Commands](#approval-commands), [The Command Surface](#the-command-surface))
- [ ] `weblisk objectives list`, `weblisk federations peers`, `weblisk federations describe`, `weblisk federations contracts`, `weblisk domains list` and `weblisk workflows list` are sent to the hub's admin gateway, and report their group unavailable and exit 1 when it answers `ADMIN_GROUP_UNAVAILABLE`, as it does while no provider's blueprint specifies the route; the stored token is sent nowhere but the admin gateway ([Data Flow](#data-flow), [`weblisk operator token`](#weblisk-operator-token))
- [ ] `weblisk status` calls `GET /v1/admin/overview` at the hub's admin gateway and displays agents, domains, workflows, approvals, federation and objectives, showing as unavailable, never as zero, each figure the gateway reports unavailable, and shows no health score ([`weblisk status`](#weblisk-status))
- [ ] Every command exits with a code [Exit Codes](#exit-codes) declares, in the meaning it gives that code, and `weblisk doctor` exits as [`weblisk doctor`](#weblisk-doctor) says
- [ ] Config resolution follows the precedence [Configuration](#configuration) gives
- [ ] Commands fail fast with a clear message and non-zero exit code when the orchestrator is unreachable ([Design Principles](#design-principles) 4)
- [ ] Authentication flow retries once on 401 by refreshing the token, except on `STEP_UP_REQUIRED`, which it never answers with a refresh; when the hub refused the credential it tells the person to attest a new one with `weblisk operator connect` ([Authentication Flow](#authentication-flow) steps 5–7)
- [ ] On `401` `STEP_UP_REQUIRED`, a command asks its person to re-confirm the act `detail.control` names, at the terminal or through a holder that asks, mints a token whose request carries `step_up` of form `identity`, retries once, and stores that token nowhere; a renewed token is never sent as a re-confirmation; with nothing that can ask, it fails with exit 2 and the challenge's `error_description` ([Authentication Flow](#authentication-flow)) <!-- wl:check cli-step-up-flow covers cli-step-up-reconfirms cli-step-up-token-held -->
- [ ] A destructive command run with `--step-up` reads the identity's passphrase from stdin and sends its first request on a token carrying `step_up_at`; without `--step-up` and with no terminal, it fails on `STEP_UP_REQUIRED`; and a holder that releases the identity without asking anybody is never used to re-confirm ([Authentication Flow](#authentication-flow)) <!-- wl:check cli-step-up-script covers cli-step-up-scripted -->

### Testing
- [ ] `weblisk test conformance` runs protocol conformance tests against a running system ([`weblisk test conformance`](#weblisk-test-conformance))
- [ ] `weblisk test conformance --level` filters to specific level (1, 2, or 3) ([`weblisk test conformance`](#weblisk-test-conformance))
- [ ] `weblisk test conformance --test` runs a single test by ID ([`weblisk test conformance`](#weblisk-test-conformance))
- [ ] `weblisk test mock-orchestrator` starts a lightweight mock for local development ([`weblisk test mock-orchestrator`](#weblisk-test-mock-orchestrator))
- [ ] Mock orchestrator accepts valid registrations but does not forward tasks or events ([`weblisk test mock-orchestrator`](#weblisk-test-mock-orchestrator))

### Deployment
- [ ] `weblisk deploy rollback` redeploys previous container image tag ([`weblisk deploy rollback`](#weblisk-deploy-rollback))
- [ ] `weblisk deploy rollback --version` targets a specific version ([`weblisk deploy rollback`](#weblisk-deploy-rollback))
- [ ] Rollback logs an audit entry ([`weblisk deploy rollback`](#weblisk-deploy-rollback))

### Dependencies & Security
- [ ] `weblisk deps audit` checks lockfile integrity and queries OSV for vulnerabilities ([`weblisk deps audit`](#weblisk-deps-audit))
- [ ] `weblisk deps audit <package>` audits a specific dependency (license, activity, CVEs) ([`weblisk deps audit`](#weblisk-deps-audit))
- [ ] `weblisk validate --deps` runs lockfile integrity as part of validation ([`weblisk validate`](#weblisk-validate))
- [ ] `weblisk server init --verify-signatures` validates signed commits before generation ([`weblisk server init`](#weblisk-server-init))
      — NOT MET. The flag is refused; blueprint commits are not consistently signed and
      no allowed-signers file is configured, so there is nothing to verify against yet.
- [ ] `weblisk policy validate` checks gateway policy file for syntax and semantic errors ([`weblisk policy validate`](#weblisk-policy-validate))
- [ ] `weblisk policy test` runs policy assertions from policies_test.yaml ([`weblisk policy test`](#weblisk-policy-test))

### Objectives
- [ ] Once the programme service's blueprint specifies the route, `weblisk objectives describe` shows one objective with its targets and what has been measured against them ([Objective Commands](#objective-commands))

### Federation
- [ ] Once the federation layer's blueprint specifies the route, `weblisk federations describe` shows full peer detail including data contract and metrics ([`weblisk federations describe <name>`](#weblisk-federations-describe-name))
- [ ] Once the federation layer's blueprint specifies the route, `weblisk federations contracts` lists all active data contracts across peers ([`weblisk federations contracts`](#weblisk-federations-contracts))

### Marketplace
- [ ] `weblisk marketplace search` queries the marketplace with text search ([`weblisk marketplace search <query>`](#weblisk-marketplace-search-query))
- [ ] `weblisk marketplace describe` shows full listing detail including data contract ([`weblisk marketplace describe <id>`](#weblisk-marketplace-describe-id))
- [ ] `weblisk marketplace buy` purchases a listing (interactive contract/pricing review by default) ([`weblisk marketplace buy <id>`](#weblisk-marketplace-buy-id))
- [ ] `weblisk marketplace install` downloads and places installable asset blueprints ([`weblisk marketplace install <id>`](#weblisk-marketplace-install-id))
- [ ] `weblisk marketplace publish` publishes a capability or asset with listing config ([`weblisk marketplace publish`](#weblisk-marketplace-publish))
- [ ] `weblisk marketplace list` shows active purchases and subscriptions ([`weblisk marketplace list`](#weblisk-marketplace-list))
- [ ] `weblisk marketplace terminate` initiates collaboration termination with grace period ([`weblisk marketplace terminate <id>`](#weblisk-marketplace-terminate-id))

### Resources
- [ ] `weblisk resource list` prints every kind the tenant's catalogue answers, each `declared-unavailable` one with its reason, and `weblisk <kind> list` for such a kind prints the reason `ADMIN_GROUP_UNAVAILABLE` carries and exits non-zero, never printing an empty list ([Resource commands](#resource-commands))
- [ ] The CLI offers for a kind exactly the operations and verbs its catalogue entry declares, and holds no list of nouns or verbs of its own for them ([Resource commands](#resource-commands))
- [ ] `weblisk <kind> <verb> <uid>` prints the verb's preconditions, in-flight handling, effect and reversibility before asking, sends the `ETag` of the read it made as `If-Match`, and on `RESOURCE_PRECONDITION_FAILED` shows the item again and does not retry ([Resource commands](#resource-commands))
- [ ] A field presented `secret` is never read from the command line and never printed ([Resource commands](#resource-commands))
