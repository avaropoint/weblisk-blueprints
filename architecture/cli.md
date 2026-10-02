<!-- blueprint
type: architecture
name: cli
version: 2.9.2
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
2. **Operations commands** — interrogate and manage a running hub via the
   orchestrator's admin API (`weblisk status`, `weblisk agents`,
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
    version: ">=2.0.0 <3.0.0"
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
    version: ">=1.11.0 <2.0.0"
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
    version: ">=1.2.0 <2.0.0"
    bindings:
      types:
        - name: HolderReference
          fields_used: [version, source, reference, options, holds]
        - name: SecretSourceRequest
          fields_used: [version, action, reference, field, fields, label, alg, message, options]
        - name: SecretSourceResponse
          fields_used: [value, reference, actions, sign_algs, named_fields, withheld_fields, signature, error]
        - name: SecretSourceError
          fields_used: [code, message]
        - name: SecretSourceRegistryEntry
          fields_used: [command, timeout_s, interactive_timeout_s]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.6.0 <2.0.0"
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
    version: ">=2.0.0 <3.0.0"
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
    version: ">=2.13.0 <3.0.0"
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
        - path: /v1/admin/operators/{name}/credentials
          methods: [POST]
        - path: /v1/admin/operators/{name}/key
          methods: [POST]
        - path: /v1/admin/overview
          methods: [GET]
        - path: /v1/admin/agents
          methods: [GET]
        - path: /v1/admin/approvals
          methods: [GET, POST]
      types:
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
   Identity holder        Orchestrator
   (a secret source,      (over a transport
    or a key file)         the operator named)
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
- Blueprint and template resolution (local → custom sources → core)
- Dev server with file watching (`weblisk dev`)
- Production builds (`weblisk build`)
- Static framework vendoring (`weblisk vendor`)
- Operator ML-DSA-65 identity creation, and resolving where a named identity
  lives — an encrypted key file, or a holder reference naming the secret source
  that holds the private half ([Where an identity lives](#where-an-identity-lives))
- Operator registration and token management (the token is stored beside the
  identity that obtained it, unless the caller asks for it not to be —
  `--no-store`)
- One credential per identity per hub, attested once by that identity and kept
  beside it ([A credential for each hub](#a-credential-for-each-hub))
- Attesting a credential another program holds, so a console never holds the
  identity that attests it (`weblisk operator attest`)
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
2. CLI resolves which identity acts — `--keys-dir`, else `--identity <label>`, else the unnamed default
3. CLI loads the auth token stored beside that identity (refreshes if near expiry)
4. CLI constructs HTTP request to the orchestrator's admin API endpoint, for a
   group the orchestrator provides. A command for any other group is not sent
   there (below)
5. Token included in the `Authorization: Bearer` header
6. Orchestrator validates token, and checks the request can use the capability the endpoint's minimum stands for: what the operator's role carries now, never beyond the token's `cap` ([`architecture/admin`](admin.md#auth-middleware), Auth Middleware)
7. Orchestrator returns JSON response
8. CLI formats response as human-readable table (or raw JSON with `--json`)
9. For write operations: CLI prompts for interactive confirmation before sending
10. Exit code set based on success/failure (0 = success, 1 = error, 2 = auth failure)

**A group another component provides is not reached on the stored token.**
The domain, workflow, approval, strategy and federation commands address
groups [`architecture/admin`](admin.md#the-admin-api-is-an-aggregate) gives to
a component other than the orchestrator. The token the CLI stores carries the
role's full set, so it goes to the orchestrator alone
([`protocol/identity`](../protocol/identity.md#a-token-names-no-audience)), and
no such component's blueprint specifies an administrative route yet
([`architecture/admin`](admin.md#the-admin-api-is-an-aggregate), the gap there).
Each of these commands therefore reports its group unavailable, sends nothing
and exits 1. Once a group's provider specifies a route, the command goes to it on
a token minted with `--cap` naming only the capability that route requires,
never on the stored one; a route whose minimum is `admin` stays unavailable,
as `architecture/admin` says.

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

Exit codes: 0 = all pass, 1 = errors found, 2 = warnings only.

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
| `--dir <path>` | Where to create it (default: `./<name>`) |
| `--platform <p>` | Which platform blueprint, skills and layout the tenant is built from. Default `go` |
| `--provider <p>` | Model backend. Omitted means the highest-weighted one this machine actually has |
| `--model <m>` | Model name, where the provider takes one |
| `--operator <name>` | Who the first operator IS, as the hub records them |
| `--identity <label>` | Which identity SIGNS. Decides who may administer this tenant, permanently |
| `--keys-dir <path>` | Which identity signs, by location. Wins over `--identity` |
| `--port <n>` | Orchestrator port |
| `--resume` | Continue into a directory that already holds generated code |
| `--json` | One progress object per line, for a GUI |

The steps are a contract, because both front ends render them and a GUI that
cannot show progress during a minutes-long generation grows its own
implementation to get it:

    provider · directory · generate · skills · provision · accept · done

**`create` produces the orchestrator and nothing else.** A tenant is a set of
components in one module; every other one is added afterwards with `weblisk
component <name> init` or the matching `create` verb. See
[`architecture/orchestrator`](orchestrator.md), "What a tenant consists of",
for the two homes a tenant's components have: what it is running, which
`GET /v1/services` answers and no file can, and what it declares it should run,
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
$ weblisk tenant accept --url http://localhost:9800 --json
```

The same pass `create` ends with, so it can be re-run. Probes are
unauthenticated on purpose: the question is not *may I do this* but *does this
tenant serve this*, and the auth middleware answers that first — `401` is a
pass, `404` means the route is absent, `405` means the client and the tenant
disagree about the method.

A failed non-essential check does not fail the tenant. It is a capability that
tenant does not have, and **saying so is the point** — "created" must not mean
only that the generator returned without an error.

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
installation supports.

The tenant root is the module root, so every component is generated into the
same tree. Generation therefore reads what the tenant already contains — module
path, packages present with their exported names, and which component owns which
file — and REFUSES a plan that names another component's files. See
[`architecture/generation`](generation.md#deciding-whether-a-file-must-be-rebuilt).

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
| `--orch <url>` | Orchestrator to register with. Omitted: the one this CLI has running for the tenant |

A kind a tenant may hold several of takes the instance's name after the verb.
With no orchestrator named and none running, the component is started without
one and the command says so: [`architecture/content`](content.md) requires the
content service to start standalone and report itself `degraded`, and an
invented address would have it register with nothing and exit.

**Started means answering.** A detached start waits until `GET /v1/health`
answers, and a component that exits or never answers is reported with what it
last wrote — a process id alone is not a started component.

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
alone: the file is an operator's declaration, never a precondition.

- **Order.** The orchestrator first, and each sibling only once the
  orchestrator answers, passed `--orch` with the address it actually bound.
  Then the content service, domains, agents, and the gateway last.
- **Refused whole.** A declaration this command cannot carry out — two
  components on one port or one name, `replicas` above 1, an agent with no
  `type` — is refused with every reason before anything starts. Starting part
  of a declaration leaves a tenant in a state nobody declared.
- **Named, not skipped.** A declared component that has not been generated is
  reported with the command that generates it, the rest start, and the command
  exits non-zero. A tenant running less than it declares is not started.
- **Foreground** stays attached to what it started, each component's output
  prefixed with its name. Interrupting it stops them in reverse order; a
  component that exits ends the session and stops the rest.

`weblisk server stop` with no `--component` stops every component this CLI has
a record of, siblings before the orchestrator, so nothing is left registered
with a registry that has gone.

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
| `--platform <p>` | Target platform: `go`, `cloudflare`, `node`, `rust` (default: `go`) |

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
  token issued, expires 2026-09-03T18:00:00Z

  Connected to http://127.0.0.1:9800 as alice
```

This is BOOTSTRAP, not connect. It is local by necessity — it reads the run
state of a hub this CLI started, and the bootstrap secret that hub emitted — and
it is the one path that establishes a hub's first operator. To reach a hub
that already runs, use [`weblisk operator connect`](#weblisk-operator-connect),
which needs only an address.

Generation is deliberately not folded in. It takes tens of minutes, streams
progress and is resumable; wrapping it in a call that also handles a credential
would make one action out of two very different failure modes, and would hold a
passphrase in memory for the length of a build.

---

## Blueprint Commands

### `weblisk blueprint update`

Force re-fetch all blueprint sources.

```bash
$ weblisk blueprint update
```

Performs `git pull` on each cached source in `~/.weblisk/blueprints/`.
If a source is unreachable, uses the last cached version.

### `weblisk validate`

Validate blueprint compliance for the current project.

```bash
$ weblisk validate
$ weblisk validate agents/seo-analyzer.yaml
$ weblisk validate --deps
$ weblisk validate --security-overrides
```

| Flag | Description |
|------|-------------|
| `--deps` | Check dependency lockfile integrity and known vulnerabilities |
| `--security-overrides` | Validate any security override declarations |

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

The identity signs to register, to attest and to change its own key
([`weblisk operator rotate`](#weblisk-operator-rotate)), and nothing else at a
hub. Tokens come
from a credential ([`architecture/admin`](admin.md#obtaining-a-token)), and the
CLI holds one for each identity at each hub:

- **Made once.** The first time `connect` or `register` obtains a token for an
  identity at a hub, the CLI generates an ML-DSA-65 key pair for that hub, has
  the identity attest it through an attestation token, and keeps it. Every
  later token for that identity at that hub is minted with it, and the
  identity is not asked. The attestation is built as
  [`weblisk operator attest`](#weblisk-operator-attest) builds it, naming the
  `hub_id` and `identity_id` the hub answered with.
- **Named by the hub, never by its address.** Each credential is kept under the
  `hub_id` it was attested for. A challenge that answers with another `hub_id`
  is a hub this identity holds no credential for, and `connect` attests one
  there.
- **Each hub it is registered at is remembered.** Beside the identity, the
  CLI keeps one **registration** for each hub the identity registered or
  connected at: that hub's `hub_id`, the operator name the hub recorded, the
  `identity_id` it answered with, and the address it was last reached at.
  `register` and `connect` write it, and update the address whenever they
  reach the hub at another. The `hub_id` names the hub; the address is only
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
- **Kept as the identity is.** The private key sits beside the identity it
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
- **Kept apart where the source cannot keep it.** `store` is optional
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
  and asks the identity once
  ([`architecture/admin`](admin.md#attesting-a-credential)). When it answers
  `CREDENTIAL_UNKNOWN` or `CREDENTIAL_REVOKED`, the CLI discards that
  credential, and the next `connect` attests a new one. Before `not_after`,
  the CLI gives the warning `architecture/admin` requires.

`--no-store` is about the token. The credential is kept either way, because
keeping it is what spares the identity.

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
  the selected identity, once a signature made through the reference verifies
  against that key. The private half stays in the source
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

Register with a running orchestrator.

```bash
$ weblisk operator register --orch http://localhost:9800 --bootstrap ./acme/.weblisk/bootstrap
Registering operator 'alice' with http://localhost:9800...
✓ Registered as admin (first operator — bootstrap secret accepted)
  Token stored: ~/.weblisk/keys/token
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
  stored beside the identity that signed. `--no-store` returns it instead
  (stdout, or the `--json` result) and writes no token
- If not the first operator, prints "Registration pending admin approval"
- `--role <role>` to request a specific role (admin may override)

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
repeatedly. It asks for a token FIRST: a hub that already knows the operator
needs no registration. A hub with no operators refuses a registration that
does not present its bootstrap secret, so connecting never claims a hub.
`connect` obtains its token as the [Authentication Flow](#authentication-flow)
says, and attests a credential first where this identity holds none the hub
accepts ([A credential for each hub](#a-credential-for-each-hub)).

Five outcomes, and they are told apart:

| State | Meaning |
|---|---|
| `connected` | a token was issued, and stored beside the identity unless `--no-store` was given |
| `pending_approval` | the hub will not issue one yet. **Not a failure** — the first operator of a hub is admitted by its bootstrap secret and every later one needs an existing admin. The message names who can act |
| `refused` | the hub answered and said no in a way no approval changes, such as the operator name being registered to a different key |
| `identity_unavailable` | this machine could not sign: the key file did not open, or the secret source holding the identity did not answer. Nothing is wrong with the hub. Where a source did not answer, `--json` output carries its name as `source` and its code as `code` ([`protocol/secret-source`](../protocol/secret-source.md#reporting-a-source-that-did-not-answer)) |
| `unreachable` | nothing answered, or the hub does not serve `POST /v1/admin/operators/token` — reported distinctly, because telling somebody to await an approval that is never coming is worse than saying the hub is too old |

Flags:

| Flag | Purpose |
|---|---|
| `--orch <url>` | the hub's address. Required |
| `--name <name>` | the operator, as the hub will record them. Defaults to the stored identity's name |
| `--identity <label>` | which identity signs, by label. The CLI resolves where it lives — see `architecture/admin` rule 2 |
| `--keys-dir <path>` | which identity signs, by location. Outranks `--identity` |
| `--json` | machine-readable result, for a console driving this |
| `--no-store` | return the token — on stdout, or in the `--json` result — and write no token file |
| `--cap <name,...>` | mint the token with `cap` naming only these capabilities, those the operator's role carries (`architecture/admin`, operator-token-issuance). For a token that will be presented to a component other than the orchestrator |
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
Orch:     http://localhost:9800

$ weblisk operator token --refresh
✓ Token refreshed. Expires: 2026-04-26T11:00:00Z
```

**Where a token is kept.** `connect`, `register` and `token --refresh` store
the token they obtain beside the identity that obtained it, mode 0600, so the
next command can use it. The token is a bearer credential: whoever holds the
file may use it until it expires. It carries every capability the operator's
role carries, `admin:*` and every person-only capability for an admin, and
mode 0600 keeps it from other users, never from another program the same
user runs, an agent included. `architecture/admin`'s rule that no agent holds
a person's token binds a console
([`console-credential-use`](admin.md#a-console-holds-a-credential-never-a-token)),
and a stored file is outside it: a person who runs agents under their own
account passes `--no-store`. **`--no-store` writes no token file.** The
token goes to stdout, or into the `--json` result, and nowhere else. A caller
that holds the token itself passes it — a console does, because a console
never writes an operator token anywhere
([`architecture/admin`](admin.md#a-console-holds-a-credential-never-a-token)).

**A token goes to the orchestrator unless it was narrowed.** One minted with
no `--cap` carries the role's full set and is presented to the orchestrator
that issued it alone. A caller that will present a token to another
component, the content service or the fabric, has `connect` or
`token --refresh` mint it with `--cap` naming only what its requests there
need, as every holder of an operator token must
([`protocol/identity`](../protocol/identity.md#a-token-names-no-audience)). A
narrowed token is never stored, so `--cap` requires `--no-store`, and the
token the next command uses keeps the role's full set.

### `weblisk operator attest`

Have an identity attest a credential that another program holds, at one hub.

```bash
$ weblisk operator attest --orch https://hub.example.com --identity alice \
    --credential-key ./credential.pub --device-label "console on build-01" --json
```

For a console. The console generates the credential's key pair and keeps it;
this verb is how the account's operator identity attests the public half
without the console ever holding the identity
([`protocol/secret-source`](../protocol/secret-source.md#a-console-never-holds-the-secrets-of-an-identity-it-acts-for)).
The steps are [`architecture/admin`](admin.md#obtaining-a-token)'s:

- Reads the credential's public key from the file `--credential-key` names
- Asks the hub for an attestation token, signing `{name, timestamp}` with the
  identity, and takes `hub_id` and `identity_id` from the answer
- Builds the `Attestation` itself — the `identity_id` the hub answered with,
  the identity's public key, the credential public key, `hub_id`,
  `--device-label` and `not_after` — and signs its canonical form. It never
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

Its outcomes are `attested`, and `pending_approval`, `refused`,
`identity_unavailable` and `unreachable` as `connect` reports them. With
`--json`, a refusal carries the hub's error code as `code`. `--orch`, `--name`,
`--identity` and `--keys-dir` mean what they mean for `connect`.

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
  `unreachable`.
- **Never with nowhere to send.** With no registrations, or while the
  identity holds a credential kept under a `hub_id` it has no registration
  for, `rotate` is refused and names each such `hub_id`. An identity that
  registered before the CLI kept registrations is still recorded by those
  hubs under the old key, and a rotation that finished would destroy the
  only key they accept. `connect` to each hub writes its registration. A
  person sure the identity is registered at no hub confirms it when asked;
  under `--json` or with no terminal the refusal stands.
- **While a rotation is pending, the identity's key is the new one.**
  `operator.pub` holds the new public key from the moment the record is
  written, and every signature the identity makes is made with the new key,
  a registration at a new hub included. The old key signs one thing only: the
  continuity of a key change at a hub still `pending`, which records the old
  key and nothing else. So `connect` and `attest` to a `pending` hub first
  send it the key change, whether or not a credential there is still live,
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
  `changed`. With `connect` and
  `attest` doing the same, a hub that was unreachable during the rotation
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

### `weblisk approvals describe <id>`

```bash
$ weblisk approvals describe rec-001
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

### `weblisk strategies update <id>`

Update strategy targets or priority.

```bash
$ weblisk strategies update strat-001 --priority 2
✓ Strategy strat-001 updated: priority 1 → 2

$ weblisk strategies update strat-001 --deadline 2026-12-31
✓ Strategy strat-001 updated: deadline extended to 2026-12-31
```

| Flag | Description |
|------|-------------|
| `--priority <n>` | New priority (1–5) |
| `--deadline <date>` | New deadline (YYYY-MM-DD) |
| `--json` | Accept full strategy update as JSON on stdin |

### `weblisk strategies delete <id>`

Archive a strategy (admin only).

```bash
$ weblisk strategies delete strat-003
⚠ This will archive strategy 'strat-003' (Fix compliance gaps).
  Type strategy ID to confirm: strat-003
✓ Strategy strat-003 archived.
```

- Archived strategies remain queryable but stop generating workflows
- Linked observations and recommendations are preserved

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

## Observation Commands

### `weblisk observations list`

Browse observation history from the lifecycle loop.

```bash
$ weblisk observations list
TIME        AGENT           STRATEGY    TARGET          FINDING
10:30:01    seo-analyzer    strat-001   /about.html     Missing meta description
10:25:12    content-analyzer strat-004  /blog/post-1    Readability score 42 (below target 60)
09:15:00    perf-auditor    strat-002   /products       LCP 4.2s (above 2.5s threshold)
```

- `--strategy <id>` to filter by strategy
- `--agent <name>` to filter by source agent
- `--since <duration>` to filter by time
- `--limit <n>` to control results
- `--json` for machine-readable output

### `weblisk observations trends`

View trend data for strategy metrics over time.

```bash
$ weblisk observations trends --strategy strat-001
Strategy: strat-001 (Improve organic traffic)

METRIC            7d AGO    CURRENT   TREND     GOAL
organic_sessions  13800     14200     +2.9%     16800
bounce_rate       0.45      0.42      -6.7%     0.35
avg_session_dur   1m 20s    1m 35s    +18.8%    2m 00s
```

| Flag | Description |
|------|-------------|
| `--strategy <id>` | Strategy to show trends for (required) |
| `--range <7d\|30d\|90d>` | Time range (default: `30d`) |
| `--json` | Machine-readable output |

---

## Test Commands

### `weblisk test conformance`

Run protocol conformance tests against a running system.

```bash
$ weblisk test conformance --orch http://localhost:9800
Running conformance suite against http://localhost:9800...

Level 1 — Protocol Basics (12 tests)
  ✓ L1-01  POST /v1/register accepts valid manifest
  ✓ L1-02  POST /v1/register rejects unsigned request
  ✓ L1-03  agent_id is 32 hex chars
  ...
  ✓ L1-12  GET /v1/health returns status

Level 2 — Behavior (18 tests)
  ✓ L2-01  Events delivered to scoped subscribers
  ...

Level 3 — Integration (8 tests)
  ✓ L3-01  Full workflow execution end-to-end
  ...

Results: 38/38 passed (0 failed, 0 skipped)
```

| Flag | Description |
|------|-------------|
| `--orch <url>` | Orchestrator URL to test against |
| `--level <n>` | Run specific level only (1, 2, or 3) |
| `--test <id>` | Run a single test by ID (e.g., `L1-03`) |
| `--verbose` | Show request/response details for each test |
| `--json` | Machine-readable test results |

- Level 1: Protocol basics — registration, auth, health, service directory
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
| Command-line flag | 1 — highest | `--orch http://localhost:9800` |
| Environment variable | 2 | Implementation-defined |
| Project config | 3 | `.weblisk/config.json` in the working directory |
| User config | 4 — lowest | `~/.weblisk/config.json` |

| Key | Type | Description |
|---|---|---|
| `orchestrator_url` | string | Which orchestrator commands act against |
| `operator_name` | string | Which identity to resolve; never a key or a passphrase |
| `default_format` | string | Output shape — `table` or `json` |
The CLI reads orchestrator connection details from (in priority order):

1. Command-line flags: `--orch http://localhost:9800`
2. Environment variable (implementation-defined)
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
1. Resolve which identity acts: --keys-dir, else --identity <label>, else the unnamed default
2. Load the token stored beside that identity
3. If it has expired, or less than a fifth of its lifetime remains, obtain a
   new one as architecture/admin's "Obtaining a token" says: the credential
   this identity holds for that hub (A credential for each hub) answers a
   challenge. The identity's holder (the encrypted key file, or a secret
   source) signs only to attest a credential where there is none the hub
   accepts. A hub that does not serve the credential routes still answers the
   identity-signed request with an operator token, and that path is deprecated
4. Set Authorization: Bearer <token> on request
5. If 401 response → attempt token refresh → retry once
6. If the hub refused the credential → print that the identity must attest a
   new one: "Run: weblisk operator connect". Otherwise print the hub's code
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
      may never be extractable, signs only to register and to attest.
  boundaries:
    - boundary: Operator → CLI. The operator's identity authorises every
        privileged operation; the CLI holds no standing authority
    - boundary: CLI → Identity holder. A secret source that can sign keeps the
        private half and returns a signature. From one that cannot, the CLI gets
        the encrypted private half and its passphrase, decrypts it in memory,
        signs, and zeroises both (protocol/secret-source). An encrypted key file
        is decrypted in memory for one invocation, with the passphrase a person
        typed or a secret source remembers, and never written back in the clear
    - boundary: CLI → Orchestrator. Authenticated per request with a short-lived
        token minted with the credential for that hub, over a transport the
        operator named
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
        Kept beside the identity, mode 0600, or with --no-store not written at
        all
    - rule: A credential key is never in the clear
      mechanism: Kept in the weblisk-key-v1 envelope or by a secret source, and
        opened as the identity's own key is
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
- Commands that accept multiple IDs (approvals) can also read from
  stdin for piping: `weblisk approvals list --json | jq -r '.[] | select(.priority == "critical") | .id' | weblisk approvals accept --stdin`

## Verification Checklist
- [ ] Provenance is written into the tenant's own state — time, each blueprint source with its revision, and the model the provider reported — not only printed
- [ ] A blueprint source with uncommitted or untracked changes records a `-dirty` revision, and the run says so before generating

### Project & Development
- [ ] `weblisk new` scaffolds a project from weblisk-templates with correct name replacement
- [ ] `weblisk new` always generates `.gitignore` with `.weblisk/secrets/`, `.weblisk/keys/`, `.weblisk/token`, `.env`, `.env.*`
- [ ] `weblisk new --template client/blog --template server/starter` merges both template sets
- [ ] `weblisk dev` starts a file-watching dev server with live reload for client projects
- [ ] `weblisk dev` builds and runs the hub with restart-on-change for server projects
- [ ] `weblisk build --minify --fingerprint` produces production-ready output
- [ ] `weblisk vendor` copies the Weblisk client framework to the specified directory
- [ ] Template resolution follows priority: local → configured template sources → core
- [ ] `weblisk doctor` validates .gitignore contains required secret exclusion entries
- [ ] `weblisk doctor` validates .weblisk/secrets/ file permissions are 0600
- [ ] `weblisk doctor` cross-references secret declarations with stored values

### Secrets Management
- [ ] `weblisk secret list` shows all declared secrets and their set/missing status
- [ ] `weblisk secret set` prompts interactively for value (never passed as CLI argument)
- [ ] `weblisk secret set` writes to `.weblisk/secrets/{agent}/{KEY}` with 0600 permissions
- [ ] `weblisk secret get` requires --confirm flag and prints a terminal-sharing warning
- [ ] `weblisk secret delete` removes the secret file
- [ ] `weblisk secret rotate` triggers the rotation handler or prompts for new value

### Server & Code Generation
- [ ] `weblisk tenant create` ends with a hub running, a first grant issued, and an address to connect to
- [ ] `weblisk tenant create` writes a `.gitignore` excluding `.weblisk/keys/`, `.weblisk/secrets/`, `.weblisk/token`, `.env` and `.env.*`, so the directory it just put a private key in is not one `git init` from committing it
- [ ] `weblisk tenant create` emits the steps `provider · directory · generate · skills · provision · accept · done`, and renaming one breaks both front ends at once
- [ ] `weblisk tenant create` generates the orchestrator only; every other component is added afterwards and the command does not claim otherwise
- [ ] `weblisk tenant accept` reports a `404` as an absent route and a `401` as a pass, and a failed non-essential check does not fail the tenant
- [ ] `weblisk component help` lists a component only when the pipeline will read that component's own blueprint, so a listed kind is never generated from the protocol alone
- [ ] `weblisk server init` reads YAML specs and dispatches to the configured LLM for code generation
- [ ] `weblisk server start` reads .weblisk/config.yaml and builds+starts all declared components
- [ ] `weblisk server start` starts the orchestrator alone when `.weblisk/config.yaml` is absent, and refuses a declaration it cannot carry out before starting anything
- [ ] `weblisk server stop` with no `--component` stops every recorded component, the orchestrator last
- [ ] `weblisk component <name> start|stop|status|logs` runs any component the tenant has generated, and a detached start reports started only once the component answers
- [ ] `weblisk tenant create` writes its `.gitignore` before generation, amends one already present, and does not `git init`
- [ ] `weblisk server verify` confirms orchestrator health and all registered components
- [ ] `weblisk agent create` generates agent code from agent.yaml spec via LLM dispatch
- [ ] `weblisk agent start` builds and runs a single agent with --orch and --port flags
- [ ] `weblisk agent list` lists all locally scaffolded agents
- [ ] `weblisk domain create` generates domain controller code from domain.yaml spec via LLM dispatch
- [ ] `weblisk domain start` builds and runs a single domain controller
- [ ] `weblisk gateway create` generates gateway code from hub configuration
- [ ] `weblisk gateway start` builds and runs the application gateway

### Blueprint Management
- [ ] `weblisk blueprint update` re-fetches all cached blueprint sources
- [ ] `weblisk validate` checks blueprint compliance (frontmatter, sections, types, deps)
- [ ] `weblisk pattern apply` reads pattern blueprint, dispatches to LLM with target context
- [ ] Blueprint resolution follows priority: local → configured blueprint sources → core

### Identity & Operations
- [ ] `weblisk operator init` creates the identity that `--keys-dir`, `--identity` or the unnamed default `~/.weblisk/keys/` selects, with 0700 directory and 0600 file permissions
- [ ] `weblisk operator init` without `--holder` prompts for passphrase (min 12 chars), encrypts private key with Argon2id + AES-256-GCM
- [ ] `weblisk operator init` passphrase cannot be skipped or supplied as CLI argument
- [ ] `weblisk operator init --holder <source>` writes no private key beside the identity and asks for no passphrase
- [ ] `weblisk operator init --vault <vault>` behaves exactly as `--holder 1password --holder-opt vault=<vault>`
- [ ] `weblisk operator store --holder <source>:<reference>` writes `operator.pub` and `holder.json` and no private key, and only once a signature made through the reference verifies against the public key
- [ ] `weblisk operator init --holder <source> --remember-passphrase` writes an encrypted `operator.key`, asks for the passphrase, and has the source keep only that passphrase; `holder.json` records `holds: ["passphrase"]`
- [ ] `weblisk operator store --holder <source> --remember-passphrase` keeps the existing key file, and has the source keep its passphrase only after checking that it opens the key
- [ ] `--identity <label>` resolves to the same location on every run, and `weblisk operator path --identity <label>` reports it
- [ ] `--keys-dir` outranks `--identity` when both are given
- [ ] `weblisk operator connect` asks for no passphrase when a secret source holds the identity's passphrase
- [ ] `weblisk operator connect` reports `connected`, `pending_approval`, `refused`, `identity_unavailable` or `unreachable`, and with `--json` an `identity_unavailable` result carries `source` and `code`
- [ ] `weblisk operator init` does not overwrite existing keys without --force flag
- [ ] `weblisk operator register` signs the registration payload with the operator's private key and stores the token it obtains
- [ ] `weblisk operator register --bootstrap <path>` sends the bootstrap secret read from that file, and the secret is never accepted as an argument
- [ ] `weblisk operator token` refreshes the token when it has expired or less than a fifth of its lifetime remains, without asking the identity to sign anything but an attestation
- [ ] `--no-store` on `weblisk operator connect`, `weblisk operator register` and `weblisk operator token --refresh` returns the token on stdout or in the `--json` result, and writes no token file
- [ ] `--cap content:read,content:describe` on `weblisk operator connect` or `weblisk operator token --refresh` returns a token whose `cap` names those two alone, and is refused without `--no-store`
- [ ] `weblisk operator attest` signs only an `Attestation` it builds itself, refuses a `--days` beyond admin's cap, submits it, reports the credential's `cid` and `not_after`, and writes nothing to disk
- [ ] Every `Attestation` the CLI builds names the `identity_id` the hub's attestation-token answer carries, never one computed from the identity key, so an identity that changed its key still attests at every hub that accepted the change
- [ ] `connect` and `register` generate one ML-DSA-65 credential per identity per hub the first time they reach it, have the identity attest it once, keep its private key only in the `weblisk-key-v1` envelope or a secret source, and mint every later token with it without asking the identity
- [ ] For an identity held by a secret source whose `capabilities` do not list `store`, `connect` keeps the new credential key beside the identity in its own `weblisk-key-v1` envelope with `kdf` `argon2id`, under a passphrase the person chose for it, and never in the clear or under `kdf` `none`
- [ ] For an identity held by a source that lists `store` but answers `named_fields` false, or names `private_key` in `withheld_fields`, `connect` keeps the credential key in its own envelope beside the identity, never in that source, and signs every later challenge with it
- [ ] `connect --remember-passphrase` for such an identity has a source that lists `store` keep the envelope's passphrase, and is refused, keeping nothing, when neither the identity's source nor one named with `--passphrase-holder` lists `store`
- [ ] `register` and `connect` record a registration for each hub, naming its `hub_id`, the operator name it recorded, the `identity_id` it answered and the address it was reached at; discarding a credential after `CREDENTIAL_UNKNOWN` keeps the registration, and `OPERATOR_REVOKED` or `OPERATOR_UNKNOWN` is reported and removes it only when the person confirms; under `--json` it is kept
- [ ] `weblisk operator rotate` writes the next key and a rotation record listing every registration `pending` before it sends anything, then sends `POST /v1/admin/operators/{name}/key` to each registration with its own name and `hub_id`, signed by the old key and the new, a hub whose credential was discarded included
- [ ] With one of three hubs unreachable, `rotate` marks two `changed` and one `pending`, keeps the old key, and exits non-zero naming the pending hub; `operator.pub` holds the new key, and a `register` at a fourth hub signs with the new key
- [ ] `weblisk operator rotate --resume` against the hub left `pending` signs the change with the old key it still records and the new key, the hub answers `200` with the same `identity_id`, and only then is the old private key destroyed and its public half kept as `operator.pub.retired`
- [ ] `weblisk operator connect` to a hub left `pending` by a rotation sends that hub the key change before it attests, and attests with the new key; when the change is refused it signs nothing there
- [ ] `weblisk operator rotate` while a rotation is pending is refused without `--resume`, and generates no second key
- [ ] `weblisk operator rotate --abandon <hub_id>` asks for confirmation, removes that hub and its registration from the rotation, and the rotation then finishes with the old private key destroyed when no other hub is still pending; with one still pending, the old private key is kept
- [ ] A hub that applied a key change and whose `200` was lost is left `pending`; `rotate --resume`, or `connect` to it, sends the change again over a fresh timestamp, the hub answers `200` as a repeat, the hub is marked `changed`, and the rotation finishes
- [ ] During a rotation, a hub that answers `OPERATOR_UNKNOWN` stays `pending` with its registration kept, and the rotation does not finish until the person abandons it with confirmation
- [ ] `--abandon` accepts a `refused` hub, and the rotation then finishes
- [ ] `weblisk operator rotate` with no registrations, or with a credential kept under a `hub_id` that has no registration, is refused naming each such `hub_id`, generates no key, and with `--json` stays refused
- [ ] While an encrypted-file rotation is pending, a signature the identity makes verifies under `operator.pub` and was made with `operator.key.next`, and `weblisk operator path` names `operator.key.next` as the key that signs
- [ ] For an identity held by a source that signs and withholds `private_key`, `weblisk operator rotate` without `--new-holder` is refused and says why; with `--new-holder <source>:<reference>` it maps that key only once a signature through it verifies, and never asks the source to create one
- [ ] For an identity held whole by a source, `rotate` stores the new key in that source with `store`, and on finishing points `holder.json` at it and `erase`s the old reference, reporting a source that does not list `erase`
- [ ] `weblisk operators revoke` invalidates target operator's public key and tokens (admin only)
- [ ] `weblisk operators revoke` prevents self-revocation and revoking the last admin
- [ ] `weblisk operators list` shows all registered operators with name, role, status, and registration date
- [ ] `weblisk operators describe` shows full detail for a single operator
- [ ] `weblisk operators role` changes operator role (admin only, cannot demote self)
- [ ] All commands output human-readable tables by default and structured JSON with --json flag
- [ ] Destructive commands (agents deregister, federations revoke) require --confirm or interactive name-confirmation
- [ ] `weblisk approvals reject` requires a --reason argument for every rejection
- [ ] `weblisk approvals list`, `weblisk strategies list`, `weblisk federations peers`, `weblisk domains list` and `weblisk workflows list` report their group unavailable and exit 1 while no component other than the orchestrator serves its route, and send nothing, the stored token included, to any component
- [ ] `weblisk status` calls GET /v1/admin/overview and displays agents, domains, workflows, approvals, federation, and health score
- [ ] Exit codes are 0=success, 1=general error, 2=auth error, 3=connection error, 4=not found, 5=permission denied
- [ ] Config resolution order: command-line flags > environment variable > .weblisk/config.json (project) > ~/.weblisk/config.json (user)
- [ ] Commands fail fast with a clear message and non-zero exit code when the orchestrator is unreachable
- [ ] Authentication flow retries once on 401 by refreshing the token; prints re-register message if refresh also fails

### Testing
- [ ] `weblisk test conformance` runs protocol conformance tests against a running system
- [ ] `weblisk test conformance --level` filters to specific level (1, 2, or 3)
- [ ] `weblisk test conformance --test` runs a single test by ID
- [ ] `weblisk test mock-orchestrator` starts a lightweight mock for local development
- [ ] Mock orchestrator accepts valid registrations but does not forward tasks or events

### Deployment
- [ ] `weblisk deploy rollback` redeploys previous container image tag
- [ ] `weblisk deploy rollback --version` targets a specific version
- [ ] Rollback logs an audit entry

### Dependencies & Security
- [ ] `weblisk deps audit` checks lockfile integrity and queries OSV for vulnerabilities
- [ ] `weblisk deps audit <package>` audits a specific dependency (license, activity, CVEs)
- [ ] `weblisk validate --deps` runs lockfile integrity as part of validation
- [ ] `weblisk server init --verify-signatures` validates signed commits before generation
      — NOT MET. The flag is refused; blueprint commits are not consistently signed and
      no allowed-signers file is configured, so there is nothing to verify against yet.
- [ ] `weblisk policy validate` checks gateway policy file for syntax and semantic errors
- [ ] `weblisk policy test` runs policy assertions from policies_test.yaml

### Strategies
- [ ] `weblisk strategies update` modifies priority, deadline, or targets of an existing strategy
- [ ] `weblisk strategies delete` archives a strategy (admin only, requires confirmation)

### Observations
- [ ] `weblisk observations list` shows observation history with strategy/agent filters
- [ ] `weblisk observations trends` displays metric trend data for a strategy

### Federation
- [ ] `weblisk federations describe` shows full peer detail including data contract and metrics
- [ ] `weblisk federations contracts` lists all active data contracts across peers

### Marketplace
- [ ] `weblisk marketplace search` queries the marketplace with text search
- [ ] `weblisk marketplace describe` shows full listing detail including data contract
- [ ] `weblisk marketplace buy` purchases a listing (interactive contract/pricing review by default)
- [ ] `weblisk marketplace install` downloads and places installable asset blueprints
- [ ] `weblisk marketplace publish` publishes a capability or asset with listing config
- [ ] `weblisk marketplace list` shows active purchases and subscriptions
- [ ] `weblisk marketplace terminate` initiates collaboration termination with grace period
