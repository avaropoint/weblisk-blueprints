# Schema: Resource

What a tenant holds or runs that a person may see and operate, declared once,
in the blueprint of the component that owns it.

A **resource** is one item of a kind a component holds or runs — an agent's
registration, a lease, a run, one step of a run. A component's blueprint
declares each kind it owns in a **Resources** block: what an item is, how it is
named, which of its fields a person may see and set, which operations and
verbs a person may perform on it, on what authority, and what it announces when
it changes. Generation builds the handlers from the block
([`architecture/generation`](../architecture/generation.md#resources)), the
admin gateway serves every kind at one address
([`architecture/admin`](../architecture/admin.md#resources-one-api-for-every-kind)),
and the CLI and every console are two clients of that one API
([`architecture/cli`](../architecture/cli.md#resource-commands)).

This file says what a Resources block holds and when one is well formed. It
does not restate the wire: the routes, the catalogue, the feed and the refusals
are `architecture/admin`'s, and the wire types are
[`protocol/types`](../protocol/types.md#resources)'.

---

## Why it exists

Every administrative route in the corpus was specified one at a time, each with
its own path, its own answer shape and its own idea of what a person may do to
it. A client therefore had to be taught each one — Studio read seven named
views of a tenant and made one write — and a thing a tenant held that nobody
had written a route for could not be seen at all. Operator actions were worse:
they were free-form `manual_actions` lists in each agent's
`## Manual Overrides`, a name and a sentence, with no capability, no
precondition and no route, so none of them existed on the wire.

The same question — *what is this, who may see it, who may change it, how* —
has one answer per kind, and the answer belongs in the blueprint of the
component that owns the kind, as a declared name belongs in the blueprint that
declares it ([`schemas/common`](common.md#declared-names)). Declared once, it is
generated into the owner, served by the gateway, listed in the catalogue and
rendered by every client, and nothing restates it.

---

## Where it is declared

**In the owner's blueprint, once.** The block's root key is `resources:`. A
blueprint that carries a `## Declaration` holds it as that declaration's
`resources:` key, beside `serves:`, because a declaration is everything a
generator reads in one block
([`schemas/architecture`](architecture.md#-declaration-supersedes--dependencies)).
Any other blueprint holds it in a `## Resources` section of form
`yaml:resources`, placed after `## Types`
([`schemas/common`](common.md#resources-section)). A blueprint carries one or
the other, never both.

**The owner is the component that holds the state.** A kind is declared by the
blueprint of the component that holds its items, and by no other, for the
reason [`architecture/admin`](../architecture/admin.md#the-admin-api-is-an-aggregate)
gives for routes: each group is served by the component that owns the state.

**An owner whose blueprint is not written yet.** Where the corpus names a
kind's owner and no blueprint specifies that owner, the kind is declared in the
blueprint that is the declared home of the contract that owner is handed — as
[`architecture/programme-service`](../architecture/programme-service.md#the-services-it-hands-work-to)
was execution's until [`architecture/execution`](../architecture/execution.md)
was written — with `owner` naming the unwritten component and
`unavailable` naming the reason. It is `declared-unavailable` in every tenant
until the owner's blueprint is written, which **moves** the block into that
blueprint and never copies it.

---

## The kind is a kind

A resource's `kind` is a kind [`schemas/kinds`](kinds.md#declared-kinds)
declares. There is one vocabulary of what sorts of thing exist; a second one,
for the things a person may operate, would be the fault kinds.md was written to
remove. A kind that is not declared there is declared there first, which is
data and changes no code.

So the kind's **identity** is the one kinds.md gives it, and the block names
the field that carries it. Two forms exist:

| form | the field holds | example |
|---|---|---|
| `minted` | an id the owner mints when the item is made: 32 lowercase hex characters ([`protocol/types`](../protocol/types.md#conventions)), never reused, never changed | a run |
| `declared-name` | a name the item was declared with, which kinds.md already makes its identity | an agent: `tenant + agent name` |

A display label is never identity. A kind whose items a person names freely
mints an id and keeps the name as a field.

**A kind is unique in a tenant.** One component owns it. Where two registered
components declare the same kind, neither is its owner, and the kind is
unavailable until one of them stops declaring it
([`architecture/admin`](../architecture/admin.md#the-catalogue)).

---

## Shape

```yaml
resources:
  - kind: <a kind schemas/kinds declares>
    owner: <the owning component's name>
    type: <a type the blueprint, or one it requires, declares; what get answers>
    list_type: <optional; the type of one list item, where it differs from type>
    identity: {field: <field path>, form: minted | declared-name}
    label: <optional; the field a client shows as the item's name; never identity>
    fields:
      - name: <field path into type>
        access: read-only | create | settable
        present: <a presentation, below>
        sensitive: <optional, true when never returned>
        volatile: <optional, true when it changes by observation, outside the ETag>
        kind: <where present is reference, the kind of the item it names>
    operations:
      <operation>:
        capability: <a capability protocol/types lists>
        step_up: <optional, true for a destructive act>
        approval: <optional; who must approve it, below>
        binds: <optional; an Operation this blueprint's endpoints declare>
        filters: <list only, optional; fields a list may be narrowed by>
        items: <list only, with binds, the member of the bound answer holding the items>
    verbs:
      - name: <kebab-case>
        capability: <a capability protocol/types lists>
        step_up: <optional, true>
        approval: <optional>
        binds: <optional; an Operation this blueprint's endpoints declare>
        transition: <optional; the transition of states this verb fires>
        body: <optional; the type of the request body; absent, the body is empty>
        preconditions: [<a testable statement>, …]
        in_flight: {handling: <none, drains, cancels or continues>, says: <statement>}
        effect: <statement>
        reversible: <false, or {by, another verb of this kind}>
    states: <optional; one state machine, as patterns/state-machine declares one>
    events: [<event>, …]
    relations:
      - {relation: <a relation schemas/kinds declares>, to: <kind>, field: <field path>}
    unavailable: {reason: <optional; owner-unspecified>, says: <statement>}
```

### Fields

`fields` lists every field of `type` a client may render or set. A field not
listed is still answered, and is read-only, rendered as its value.

| `access` | a person may |
|---|---|
| `read-only` | read it. Nothing a person sends sets it |
| `create` | set it on `create`, and never after |
| `settable` | set it on `create` and change it on `update` |

**`sensitive: true` means never returned.** Not masked, not truncated: absent
from every answer, every list and every event. A sensitive field a person may
set is presented `secret`, which is write-only; a read-only sensitive field is
presented nothing at all. An operator token's `token` on an agent's entry is the
case: the orchestrator holds it and answers it to nobody.

**`volatile: true` means it changes without anybody acting** — a `last_seen`,
a lease's `expires_at`. The ETag that guards a write is taken over the item
without its volatile fields, so a person acting on what they read is not
refused because the thing they read was observed again.

### Presentations

A closed set. Each is a contract a client implements, so a presentation a
client does not implement would be a label nothing renders, which is worse than
not offering it ([`schemas/kinds`](kinds.md#the-model-open-kinds-closed-capabilities)
makes the same argument for capabilities). A field whose type no presentation
fits is listed without `present`, and every client renders it read-only, as its
value.

```yaml
presentations:
  text:      {types: [string, text, uuid], says: a line or a block of text}
  number:    {types: [int, int64, integer, float], says: a number, in the field's unit where it declares one}
  boolean:   {types: [bool], says: true or false}
  choice:    {types: [string], says: one of the values the field's enum declares, and no other}
  reference: {types: [string], says: the identity of an item of the field's kind, rendered as a link to it}
  list:      {types: [list], says: an ordered list of values}
  duration:  {types: [int, int64, integer, string], says: a length of time, in the field's unit or as protocol/conventions writes one}
  schedule:  {types: [string], says: a cron expression, format cron}
  secret:    {types: [string], says: write-only; never answered, never shown, set by a person and judged only by the owner}
  instant:   {types: [timestamp], says: an instant, as protocol/conventions writes one}
```

`instant` is in the set because nearly every kind carries one, and an instant
rendered as text loses the one thing a reader needs from it.

### Operations

A closed set: `list`, `get`, `create`, `update`, `delete`. A kind declares the
ones it serves; **an operation it does not declare does not exist on the wire**.

```yaml
operations: [list, get, create, update, delete]
```

`update` changes the `settable` fields a request names and nothing else.
`delete` removes the item; an item whose removal is recorded rather than done —
an operator, whose record stays `revoked` — declares a verb instead, because
`delete` that leaves the item behind is a second meaning for one word.

`binds` names an `Operation` the blueprint's own endpoint table already
declares. **The existing route is the implementation of the operation**, and
the declaration adds no second rule for the same act: the gateway carries the
uniform address to that route and relays what it answers. An operation that
binds nothing is served by the owner at the uniform address itself
([`architecture/admin`](../architecture/admin.md#resources-one-api-for-every-kind)).
A bound `list` names, in `items`, the member of the bound answer that holds the
items, since the bound route answers its own shape.

### Verbs

A verb is an act on one item that is not plain CRUD: cancel a run, deregister
an agent. It is what `## Manual Overrides`' `manual_actions` were meant to be
([`schemas/agent`](agent.md#manual-overrides--manual-overrides)), declared fully
enough to exist on the wire. **An undeclared verb does not exist.**

Every verb states:

| key | says |
|---|---|
| `name` | kebab-case, not an operation and not a word the CLI reserves (below) |
| `capability` | what a person's request must be able to use. A verb whose act is in a capability family its owner holds names that family's capability; any other names `action:invoke`, which [`protocol/types`](../protocol/types.md#capability) gives exactly that meaning |
| `preconditions` | each a testable statement the owner checks before acting. A verb that fires a `transition` has that transition's `from` states as a precondition without restating them |
| `in_flight` | what happens to work under way: `none` (there is none), `drains` (finishes what started, starts nothing new), `cancels` (stops it), `continues` (unaffected), and a statement of how |
| `effect` | what is true once it is answered |
| `reversible` | `false`, or the verb of this kind that undoes it |

**A verb's body is described from its type.** `body` names a type, and the
block lists none of its fields: they are that type's, declared once there. Its
wire form carries them as `body_fields`
([`protocol/types`](../protocol/types.md#resourcedeclaration)), each with the
type, `required` and `enum` its declaration gives, `access` `create` (a person
sets it in the request that carries it), and the one presentation its type
selects, in this order: `choice` where it declares an `enum`, `schedule` where
its format is `cron`, `instant` for `timestamp`, and otherwise the
first presentation in the set above whose `types` list its type, which makes a
string `text` and an integer `number`. A field no
presentation fits is carried without one, and a client asks for it as text.
The same declaration supplies the `type`, `required` and `enum` every listed
field of `type` carries on the wire, so a `choice` field's values are always
the enum its type declares and never a second list here.

```yaml
reserved_verbs: [list, show, get, create, update, delete, watch, describe]
verb_name: "[a-z][a-z0-9]*(-[a-z0-9]+)*"
in_flight: [none, drains, cancels, continues]
```

### Authority

Each operation and verb names one `capability` from
[`protocol/types`](../protocol/types.md#capability). The request must be able
to use it, as [`architecture/admin`](../architecture/admin.md#auth-middleware)
judges every administrative request — the orchestrator on its own routes and
at the exchange for every other owner — and nothing in this block widens it.

**`step_up: true` marks the act destructive.** Declaring it is naming
[`architecture/admin`](../architecture/admin.md#contracts)'s
`destructive-action-step-up`, which then governs the act exactly as it governs
every act it lists; this file restates none of it.

**`approval`** declares that the act takes effect only once people other than
the requester have approved it:

```yaml
approval:
  positions: [<a position a programme declares>, …]   # or
  roles: [<a role architecture/admin's table names>, …]
  min: <how many must approve, at least 1>
  ordered: <optional, true when they approve in the order positions lists>
```

The request is then recorded as an
[`ApprovalRequest`](../protocol/types.md#approvalrequest), held by the owner,
listed in the decision inbox and decided at the owner, and the shape of the
decision is [`patterns/approval`](../patterns/approval.md)'s. Nothing is applied
until the last approval it needs, and the act is applied while answering that
approval, on the pass that carried it, never afterwards on anybody's behalf
([`architecture/admin`](../architecture/admin.md#contracts),
`admin-gateway-authorization`: work that outlives a request has no authority
yet). So the approver whose decision completes it must be able to use the
act's own capability as well. `ordered` approvers is not yet a
`patterns/approval` form, and is recorded here so that the declaration has a
place for it; until a route decides one, an act declaring `approval` is
unavailable at the uniform address
([`architecture/admin`](../architecture/admin.md#writes-and-what-guards-them)).

### States

A kind whose items have a lifecycle declares one state machine in
[`patterns/state-machine`](../patterns/state-machine.md#state-declaration)'s
form, inline, its `entity_type` the block's `type` and its `state_field` the
field that holds the state. Its transitions with `trigger: manual` are the
only ones a person fires, each through the verb that names it in `transition`.
A transition a person may fire with no verb naming it does not exist on the
wire.

### Events

What the owner announces when an item changes, each a name from:

```yaml
lifecycle_events: [created, updated, deleted]
```

or a verb's name (the verb was performed), or a state's name (the item entered
that state). The feed carries each as the event type
`weblisk.<kind>.<event>`, its subject the item's identity, its data the fields
that changed and are not sensitive
([`architecture/admin`](../architecture/admin.md#the-feed)). A change the block
names no event for is not announced, and a client that wants it reads the item
again.

### Relations

Each relation names a relation [`schemas/kinds`](kinds.md#relations) declares
from this kind to `to`, and the `field` of this kind's type that holds the
target's identity. A pairing that table does not permit is not a relation, and
is declared there first or not at all.

### When a kind is unavailable

The catalogue reports every declared kind, available or not, and an
unavailable one with a reason, never as absent and never as empty:

```yaml
unavailable_reasons:
  owner-unspecified: no blueprint specifies the owner yet; the block is held where its contract is
  owner-not-declared: the tenant does not declare the owning component
  owner-not-registered: the tenant declares it and it is not registered now
  owner-ambiguous: more than one registered component declares the kind
  owner-address-unverified: the owner is on another host and its address is only self-asserted
  approval-undecidable: the act takes approval and no route decides one yet
```

A block declares `unavailable` itself only for `owner-unspecified`. Every
other reason is a fact about one tenant, which the gateway reports.

---

## Rules

Each rule has an id; [`checks/resources.py`](../checks/resources.py) holds
every Resources block in the corpus to them, and its
[vectors](../vectors/resources/README.md) cite them.

```yaml
rules:
  - id: resource-kind-declared
    rule: kind is a kind schemas/kinds declares
  - id: resource-kind-once
    rule: no two blocks in the corpus declare the same kind
  - id: resource-keys
    rule: kind, owner, type, identity, fields and operations are present, and no key the Shape does not name is used
  - id: resource-type-declared
    rule: type, and list_type where present, is a type a types block in the corpus declares
  - id: resource-identity
    rule: identity names a field of type, and its form is minted or declared-name
  - id: resource-field-of-type
    rule: every fields entry, relations field and filter names a field of type, a dotted path resolving through the declared types of the fields it passes
  - id: resource-field-access
    rule: every fields entry has an access of read-only, create or settable
  - id: resource-presentation
    rule: present, where given, is a presentation this file declares, and the field's declared type is one it lists; reference names a declared kind
  - id: resource-sensitive
    rule: a sensitive field is presented secret where its access lets a person set it, and is presented nothing where it is read-only
  - id: resource-operations-closed
    rule: every key of operations is list, get, create, update or delete
  - id: resource-capability
    rule: every operation and verb names one capability protocol/types lists
  - id: resource-binds
    rule: binds names an Operation the same blueprint declares, and a bound list names items
  - id: resource-verb-name
    rule: a verb's name is kebab-case, unique in its kind, and neither an operation nor a reserved verb
  - id: resource-verb-complete
    rule: every verb states capability, preconditions, in_flight with a handling this file declares, effect and reversible, and reversible is false or names another verb of the kind
  - id: resource-transition
    rule: a verb's transition names a transition of the kind's states whose trigger is manual, and every manual transition is named by a verb
  - id: resource-states
    rule: states, where present, has initial_state, states and transitions, and every from, to and initial_state is a declared state
  - id: resource-events
    rule: every event is a lifecycle event, a verb of the kind or a state of the kind
  - id: resource-relation-declared
    rule: every relation is one schemas/kinds declares from this kind, or from any, to the kind it names
  - id: resource-unavailable
    rule: unavailable, where a block declares it, names owner-unspecified and says why
```

---

## Reading one

[`architecture/orchestrator`](../architecture/orchestrator.md#declaration)
declares `agent` and `lease`;
[`architecture/execution`](../architecture/execution.md#resources) declares
`run`, `run-step`, `tool-call`, `wait`, `timer`, `schedule` and
`workflow-definition`. They are the worked examples; this file keeps none of its
own, so that no example here can drift from the declarations it describes.
