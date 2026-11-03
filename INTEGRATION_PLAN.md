# A tenant's connections to other systems

> **Status: proposed, 2026-11-03. Version 0.1.0.** Nothing here is normative.
> It stays at the corpus root as a plan, because a file under `architecture/`
> is a blueprint and its MUST lines are read as requirements. Each part becomes
> normative only when it lands in the document [What changes where](#what-changes-where)
> names for it, and from then on that document, not this plan, is the
> authority. The YAML below is written in the shape
> [`schemas/resource`](schemas/resource.md) gives a Resources block, under the
> root `proposed:` rather than `resources:`, so that no check or generator
> reads it as declared.
>
> Written from Weblisk Studio's rebuild of Operations → Integrations, against
> corpus `42ccc8d`.

---

## The problem, measured

A tenant is connected to systems it does not run: a git host, a cloud account,
an identity provider, a monitor, a chat workspace, a model vendor, the stores
its content lives on. Each connection holds a third party's credential and
decides what crosses the boundary. Those are facts about the customer's
organisation, and the tenant is their system of record.

The corpus says what an integration is and nothing about how a tenant holds
one:

| | Measured, corpus `42ccc8d` | Where |
|---|---|---|
| 1 | `integration` is a declared kind — durable connection id, `observed`, no capabilities — with relations `reached_through` (provider → integration), `exchanges_with`, `carries` and `consumes` | [`schemas/kinds`](schemas/kinds.md#declared-kinds) |
| 2 | **No blueprint owns it.** No Resources block declares `integration`, no route reads or writes one, and no type describes one | grep of every `kind:` in `agents`, `architecture`, `patterns`, `protocol`, `schemas` |
| 3 | A model backend that needs a key is listed and is never available: *"no blueprint yet gives the model gateway another place to take one from"* | [`architecture/orchestrator`](architecture/orchestrator.md#the-tenants-model) |
| 4 | Content backends and their drivers are configuration only. `content.backends` names each backend's `driver`, `root` and `held_by`; no route lists, adds or tests one | [`architecture/content`](architecture/content.md#configuration) |
| 5 | A webhook is specified as a pattern a component may use, with no component that receives a third party's deliveries for the tenant | [`patterns/webhook`](patterns/webhook.md) |

So a console had nothing to call. Studio filled the gap in itself: a catalogue
of fourteen third-party providers, each with its own field list, kept in
Studio's per-project state with Studio receiving their webhooks — and calling
none of them. Studio retired that catalogue on 2026-11-03 and now refuses to
connect anything but a folder or working tree it reads itself; Operations →
Integrations reads the tenant's `integration` kind where the tenant serves one
and says "not offered" where it does not. This plan is what would let a tenant
serve one.

---

## The rule this follows

**What an integration IS is published content; a connection is the tenant's
record.** The kinds of system a tenant can connect to, the fields each takes,
the purposes a connection may serve and the drivers a content store may use
are the corpus's to declare, delivered into the tenant like any other
published content. A connection to one of them — this account, this key, this
scope, these purposes — is the tenant's, recorded by the tenant's own service,
and changed only through it. A client renders both from the tenant's resource
catalogue and holds neither.

---

## A. The integration service — a new `architecture/integration.md`

A tenant component, `integration`, that holds the tenant's connections to
other systems, keeps their credentials in the tenant's secret store, checks
them on request, and receives what they deliver.

### What it holds

| | What | Whose |
|---|---|---|
| **connector** | one kind of system a tenant can connect to: what it is, which provider it reaches (`provider` kind), the fields a connection to it takes with their presentations, the credential it needs (by name and presentation, never a value), the purposes it can serve, and how a check of it is made | published: authored in the corpus, delivered into the tenant |
| **integration** | one connection: the connector it is an instance of, its scope (`scope_path`, as content repositories carry one), its settable fields, its credential (write-only), the purposes it serves for this tenant, and its last check | the tenant's |

The **purposes** are a closed vocabulary declared once, as an enum of the
`IntegrationPurpose` type, so that every client reads the same words from the
catalogue's field enum and none keeps its own:

| purpose | what crosses the boundary |
|---|---|
| `knowledge-in` | documents the tenant's content service may read from the other system |
| `evidence-in` | records the other system produces that the tenant keeps as evidence |
| `events-in` | deliveries the other system sends, filed as events |
| `config-out` | configuration the tenant pushes to the other system, derived from its policies |
| `notify-out` | messages the tenant sends through it |
| `model` | completions the tenant's model gateway runs on it |

A connector declares which of these it can serve; a connection names which it
does. One connection serving several purposes is one record, never one per
purpose.

### Credentials

A connection's credential is held in the tenant's secret store
([`patterns/secrets`](patterns/secrets.md)), named by the connection's id, and
is never answered: the field is `sensitive`, presented `secret`, settable on
`create` and `update`, and omitted from every read, every event and the ETag.
Rotating it is an `update` of that field. Removing a connection deletes its
secret in the same act.

### Checking a connection

`check` is a verb: the service makes the connector's declared check against the
other system, records `status` (`connected`, `failing`, `unverified` where the
connector declares no check) and `checked_at`, and answers the item. A status
is a measurement with a time; nothing sets one but a check.

### Receiving deliveries

A connection serving `events-in` is given a delivery address at the tenant's
public edge and a signing secret, verified as [`patterns/webhook`](patterns/webhook.md)
says, and each verified delivery is filed as an event naming the connection.
This replaces any client receiving a third party's deliveries for the tenant.

### Resources (proposed)

```yaml
proposed:
  - kind: connector
    owner: integration
    type: Connector
    identity: {field: id, form: declared-name}
    label: name
    fields:
      - {name: id, access: read-only, present: text}
      - {name: name, access: read-only, present: text}
      - {name: provider, access: read-only, present: reference, kind: provider}
      - {name: describes, access: read-only, present: text}
      - {name: purposes, access: read-only, present: list}
      - {name: fields, access: read-only, present: list}
      - {name: credential, access: read-only, present: text}
    operations:
      list: {capability: "integration:read"}
      get: {capability: "integration:read"}

  - kind: integration
    owner: integration
    type: Integration
    identity: {field: id, form: minted}
    label: name
    fields:
      - {name: id, access: read-only, present: text}
      - {name: name, access: settable, present: text}
      - {name: connector, access: create, present: reference, kind: connector}
      - {name: scope_path, access: create, present: text}
      - {name: purposes, access: settable, present: list}
      - {name: settings, access: settable}
      - {name: credential, access: settable, present: secret, sensitive: true}
      - {name: status, access: read-only, present: choice}
      - {name: checked_at, access: read-only, present: instant}
      - {name: check_says, access: read-only, present: text}
      - {name: created_at, access: read-only, present: instant}
    operations:
      list: {capability: "integration:read", filters: [connector, status]}
      get: {capability: "integration:read"}
      create: {capability: "integration:connect"}
      update: {capability: "integration:connect"}
      delete: {capability: "integration:connect", step_up: true}
    verbs:
      - name: check
        capability: "integration:check"
        preconditions: [the integration exists]
        effect: status and checked_at say what the connector's check found just now
        reversible: "false"
    states:
      initial_state: unverified
      entity_type: Integration
      state_field: status
      states:
        unverified: {description: no check has been made, or the connector declares none}
        connected: {description: the last check was answered}
        failing: {description: the last check was refused or not answered}
      transitions:
        - {name: answered, from: [unverified, connected, failing], to: connected, trigger: a check is answered, description: it works now}
        - {name: refused, from: [unverified, connected, failing], to: failing, trigger: a check is refused or times out, description: it does not work now}
    events: [created, updated, deleted, check]
```

`settings` carries the connector's own fields, judged against the connector's
`fields` declaration by the service; it has no presentation here because its
shape is the connector's, and a client renders it from the connector it reads.

### Capabilities

`integration:read`, `integration:connect` and `integration:check`, added to
[`protocol/types`](protocol/types.md) — Capability. Connecting is neither
reading nor checking: a credential that may check a connection must not be
able to point it somewhere else.

---

## B. Content backends, listed — `architecture/content.md`

Add a read-only `content-backend` kind owned by `content`: each backend the
service holds for a `scope_path`, its `driver` (the blueprint that specifies
it, by the driver name that blueprint declares — `file`, or
[`patterns/content-git`](patterns/content-git.md)'s), `held_by`, and the
repositories placed on it. `root` and `options` stay configuration and are not
answered: a root is a coordinate on the tenant's host. Declaring a new backend
stays a configuration change until a decision below says otherwise.

```yaml
proposed:
  - kind: content-backend
    owner: content
    type: ContentBackend
    identity: {field: name, form: declared-name}
    label: name
    fields:
      - {name: name, access: read-only, present: text}
      - {name: driver, access: read-only, present: text}
      - {name: held_by, access: read-only, present: choice}
      - {name: scope_paths, access: read-only, present: list}
      - {name: repositories, access: read-only, present: list}
    operations:
      list: {capability: "content:describe"}
      get: {capability: "content:describe"}
```

---

## C. The model gateway's key — `architecture/orchestrator.md`

A model backend that needs a key takes it from an integration serving the
`model` purpose whose connector reaches that backend's provider: the gateway
asks the integration service for the credential by the connection's id, on its
own registration, at completion time, and holds it no longer than the
completion. `ModelConfig` names the connection, never a key or an environment
variable. Until then the gap in "The tenant's model" stands as written.

---

## What changes where

| Part | Lands in | Also touches |
|---|---|---|
| A | `architecture/integration.md` (new), with `connector` added to [`schemas/kinds`](schemas/kinds.md) | `protocol/types` (Capability, `Integration`, `Connector`, `IntegrationPurpose`), `architecture/admin` (the group in the aggregate), `architecture/generation` (delivering connectors), [`patterns/webhook`](patterns/webhook.md) (who receives) |
| B | [`architecture/content`](architecture/content.md), Resources | `schemas/kinds` (`content-backend`) |
| C | [`architecture/orchestrator`](architecture/orchestrator.md), "The tenant's model" | `architecture/model-service` |

A client needs nothing new: the resource catalogue already carries every
field's presentation, enum and authority, and Studio's Operations →
Integrations already renders a served `integration` kind from it.

---

## Decisions

| | Decision | Why it cannot be decided here |
|---|---|---|
| D1 | Where connectors are authored: a new file family (`integrations/<connector>.md`) beside `standards/` and `programmes/`, or one declaration per provider inside `policy-domains/` | A new family is a change to the corpus's shape ([`CORPUS_SHAPE.md`](CORPUS_SHAPE.md)) |
| D2 | Whether a client may ever `create` a content backend, or a backend stays configuration | Creating one names a root on the tenant's host from a request, which is the "edit the config and restart" line drawn the other way |
| D3 | Whether `events-in` deliveries land at the integration service or at a separate edge component | The tenant's public edge does not exist as a component yet |
| D4 | Whether the model gateway may hold a vendor key at all (C), given it runs beside the hub's keys | [`architecture/orchestrator`](architecture/orchestrator.md#the-tenants-model)'s reason for reading no key is a security argument, and C answers it only by narrowing how long the key is held |
