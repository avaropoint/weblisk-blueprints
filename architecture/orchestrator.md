<!-- blueprint
type: architecture
name: orchestrator
version: 2.21.2
requires: [protocol/identity, protocol/types, architecture/storage, architecture/observability, architecture/admin, patterns/scope]
platform: any
tier: free
-->

# Weblisk Orchestrator Blueprint

The orchestrator is the trust anchor and registry service. It manages
agent registration, identity verification, namespace ownership, service
directory distribution, and channel brokering.

The orchestrator does NOT execute agent logic, route tasks, manage
strategies, store observations, or handle approvals. Those concerns
belong to infrastructure agents (Workflow, Task, Lifecycle) that
register like any other agent.

---

## Overview

The orchestrator is a tenant's **trust anchor and directory**. It admits agents,
verifies who they are, records which namespaces they own, tells every agent what
else exists, brokers direct channels between them, and keeps the audit trail of
all of it.

It is deliberately small. It does not execute work, hold application data, serve
browsers or authenticate end users — those belong to agents, to storage, and to
the gateway. What it owns is the answer to one question: **who is here, what may
they do, and who says so.**

Exactly one runs per tenant. Everything else in a tenant registers with it, and
a tenant with no orchestrator has no way to know what it contains.

---

## Declaration

Everything a generator or validator reads about this component that was
previously scattered across headings, tables and YAML blocks in three different
shapes. The rest of this document is prose for a person.

Named `declaration` rather than `contract`: "contract" already means four
distinct things in this corpus — data contracts (`patterns/contract`), behaviour
contracts (`## Contracts`, in 43 blueprints), `contract_schema` in
change-management, and dependency contracts. A fifth meaning would be the
ambiguity this block exists to remove.

The `## Verification Checklist` stays in prose, here and in every blueprint. It
is the one surface that was never scattered.

See [`CONTRACT_BLOCK_PLAN.md`](../CONTRACT_BLOCK_PLAN.md) for why, and for what
this replaces.

```yaml
declaration:
  requires:
    - blueprint: protocol/identity
      version: ">=1.14.0 <2.0.0"
      bindings:
        types:
          - name: SigningKeyPair
            fields_used: [public_key, private_key]
          - name: SignatureVerification
            fields_used: [verify_signature, check_replay]
          - name: WLToken
            fields_used: [sub, iss, iat, exp, cap, cid, type, role, identity_id, record_keys, aud, act, identity_key, step_up_at]
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: protocol/types
      version: ">=1.17.0 <2.0.0"
      bindings:
        types:
          - name: RegisterRequest
            fields_used: [manifest, signature, timestamp]
          - name: RegisterResponse
            fields_used: [agent_id, token, expires_at, services]
          - name: ServiceDirectory
            fields_used: [services, routing_table, namespaces]
          # Each entry republishes what the registration recorded, the routes
          # at which the component admits a person's request on a pass included
          - name: ServiceEntry
            fields_used: [name, url, public_key, capabilities, status, address_provenance, pass_routes]
          - name: ChannelRequest
            fields_used: [from_agent, to_agent, purpose]
          - name: ChannelGrant
            fields_used: [channel_id, channel_token, target_url, target_pub_key]
          - name: AgentManifest
            fields_used: [name, type, version, url, public_key, capabilities, publishes, subscriptions, pass_routes]
          - name: AuditEntry
            fields_used: [id, timestamp, actor, action, target, detail, status]
          - name: ChannelEntry
            fields_used: [channel_id, from_agent, to_agent, expires_at]
          - name: Capability
            fields_used: [name, resources]
          - name: Operator
            fields_used: [name, public_key, identity_id, retired_keys, role, status, created_at]
          - name: RetiredKey
            fields_used: [public_key, retired_at]
          - name: TokenExchangeRequest
            fields_used: [subject_token, audience, scope]
          - name: TokenExchangeResponse
            fields_used: [issued, code, pass, expires_at, capabilities]
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: architecture/storage
      version: ">=1.0.0 <2.0.0"
      bindings:
        types:
          - name: AuditFilter
            fields_used: [actor, action, since, cursor, limit]
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: architecture/observability
      version: ">=1.0.0 <2.0.0"
      bindings:
        types:
          - name: HealthStatus
            fields_used: [status, name, version, uptime]
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: architecture/admin
      version: ">=2.33.0 <3.0.0"
      bindings:
        behaviors:
          - name: operator-registration
          - name: registration-signing-input
          - name: first-operator-claim
          - name: operator-approval
          - name: attestation-token-issuance
          - name: hub-proof
          - name: operator-credential-attestation
          - name: operator-token-issuance
          - name: token-status-on-use
          - name: operator-credential-revocation
          - name: operator-key-change
          - name: auth-route-rate-limit
          - name: operator-roles
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: patterns/scope
      version: ">=2.6.0 <3.0.0"
      bindings:
        types:
          # An enum: it declares values, not fields, so nothing is bound FROM it.
          - name: ScopeLevel
          - name: ProviderAgreement
            fields_used: [id, party, backends, models, component, agreement, agreement_digest, level, recorded_by, recorded_at, not_after, withdrawn_by, withdrawn_at]
          - name: ProviderCeiling
            fields_used: [backend, model, ceiling, agreement, not_after, address]
          - name: DestinationRefusal
            fields_used: [destination, ceiling, items]
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
  serves:
    - method: POST
      path: "/v1/register"
      operation: Register
      auth: "identity"
    - method: DELETE
      path: "/v1/register"
      operation: Deregister
      auth: "token"
    - method: GET
      path: "/v1/services"
      operation: Services
      auth: "token"
    - method: POST
      path: "/v1/channel"
      operation: Channel
      auth: "token"
    - method: POST
      path: "/v1/rotate-key"
      operation: RotateKey
      auth: "token"
    - method: POST
      path: "/v1/token/exchange"
      operation: TokenExchange
      auth: "token"
    - method: GET
      path: "/v1/health"
      operation: Health
      auth: "identity"
    - method: GET
      path: "/v1/audit"
      operation: Audit
      auth: "token"
    - method: POST
      path: "/v1/admin/operators/register"
      operation: OperatorRegister
      auth: "none"
    - method: POST
      path: "/v1/admin/operators/token"
      operation: OperatorToken
      auth: "none"
    - method: POST
      path: "/v1/admin/credentials/challenge"
      operation: CredentialChallenge
      auth: "none"
    - method: POST
      path: "/v1/admin/credentials/token"
      operation: CredentialToken
      auth: "none"
    - method: POST
      path: "/v1/admin/hub/proof"
      operation: HubProof
      auth: "none"
    - method: POST
      path: "/v1/admin/operators/{name}/key"
      operation: OperatorKeyChange
      auth: "none"
    - method: POST
      path: "/v1/admin/operators/{name}/credentials"
      operation: CredentialAttest
      auth: "token"
    - method: GET
      path: "/v1/admin/operators/{name}/credentials"
      operation: CredentialList
      auth: "admin:read"
    - method: DELETE
      path: "/v1/admin/operators/{name}/credentials/{cid}"
      operation: CredentialRevoke
      auth: "token"
    - method: GET
      path: "/v1/admin/operators"
      operation: OperatorList
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/operators/{name}"
      operation: OperatorGet
      auth: "admin:read"
    - method: DELETE
      path: "/v1/admin/operators/{name}"
      operation: OperatorDelete
      auth: "admin:*"
    - method: POST
      path: "/v1/admin/operators/{name}/approve"
      operation: OperatorApprove
      auth: "admin:*"
    - method: PUT
      path: "/v1/admin/operators/{name}/role"
      operation: OperatorRole
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/agents"
      operation: AdminAgentList
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/agents/{name}"
      operation: AdminAgentGet
      auth: "admin:read"
    - method: POST
      path: "/v1/admin/agents/{name}/deregister"
      operation: AdminAgentDeregister
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/overview"
      operation: AdminOverview
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/audit"
      operation: AdminAuditList
      auth: "admin:audit"
    - method: GET
      path: "/v1/admin/audit/export"
      operation: AdminAuditExport
      auth: "admin:audit"
    - method: GET
      path: "/v1/admin/model"
      operation: AdminModelGet
      auth: "admin:read"
      provided: platform
    - method: PUT
      path: "/v1/admin/model"
      operation: AdminModelPut
      auth: "admin:*"
      provided: platform
    - method: GET
      path: "/v1/admin/model/providers"
      operation: AdminModelProviders
      auth: "admin:read"
      provided: platform
    - method: POST
      path: "/v1/admin/complete"
      operation: AdminComplete
      auth: "admin:read"
      provided: platform
    - method: POST
      path: "/v1/admin/model/agreements"
      operation: AdminModelAgreementRecord
      auth: "model:attest"
      provided: platform
    - method: GET
      path: "/v1/admin/model/agreements"
      operation: AdminModelAgreementList
      auth: "admin:read"
      provided: platform
    - method: DELETE
      path: "/v1/admin/model/agreements/{id}"
      operation: AdminModelAgreementWithdraw
      auth: "model:attest"
      provided: platform
    - method: GET
      path: "/v1/admin/model/ceiling"
      operation: AdminModelCeiling
      auth: "admin:read"
      provided: platform
    - method: GET
      path: "/v1/model/ceiling"
      operation: ModelCeiling
      auth: "token"
      provided: platform
  checks:
    - check: no-path-literals
      subject: route registration
      why: Every routed path is a Path<Operation> constant, so a path is corrected in one place
    - check: no-method-less-pattern
      subject: route registration
      why: net/http panics at startup when a method-less pattern sits beside a wildcard sibling
    - check: endpoint-routed
      endpoint: POST /v1/register
    - check: endpoint-routed
      endpoint: POST /v1/admin/operators/token
    - check: endpoint-routed
      endpoint: POST /v1/admin/credentials/challenge
    - check: endpoint-routed
      endpoint: POST /v1/admin/credentials/token
    - check: endpoint-routed
      endpoint: POST /v1/admin/operators/{name}/key
    - check: endpoint-routed
      endpoint: POST /v1/admin/hub/proof
    - check: endpoint-routed
      endpoint: POST /v1/admin/operators/{name}/credentials
    - check: endpoint-routed
      endpoint: GET /v1/admin/operators/{name}/credentials
    - check: endpoint-routed
      endpoint: DELETE /v1/admin/operators/{name}/credentials/{cid}
    - check: endpoint-routed
      endpoint: GET /v1/admin/audit
    - check: endpoint-routed
      endpoint: GET /v1/admin/audit/export
    - check: endpoint-routed
      endpoint: POST /v1/token/exchange
    - check: endpoint-routed
      endpoint: GET /v1/health
    - check: type-has-keys
      type: RegisterResponse
      keys: [agent_id, token, expires_at, services, orchestrator, protocol_version]
    - check: type-has-keys
      type: ChannelGrant
      keys: [channel_id, channel_token, target_url, target_pub_key, expires_at]
    - check: error-codes-registered
      subject: the central error registry
      why: Every status lookup for an unregistered code falls through to 500
    - check: starts-unattended
      subject: the built binary
      why: A hub that prompts for a passphrase dies on EOF and never binds its port
```

---

## What a tenant consists of, and where that is declared

The orchestrator is a tenant's **first** component. It is not the tenant, and
this section exists because the two were read as the same thing for long enough
that a fully specified sibling — [`architecture/content`](content.md) — had
never been generated into one.

**A tenant's components are siblings, not dependencies.** The content service,
a gateway, each agent and each domain controller are separate components in one
module, generated one at a time, each registering with this orchestrator on
start.

**The `requires:` list below is what the orchestrator is built from, not what a
tenant contains.** Adding a sibling to it would be wrong in three separate
ways, and each matters:

1. **It means something else.** A `requires` entry is a statement that this
   component binds types or behaviours from that blueprint at build time. The
   orchestrator binds nothing from the content service. It learns that one
   exists when it registers, at runtime, like every other member.
2. **It would make an optional component mandatory.** A tenant that governs no
   documents legitimately runs an orchestrator and no content service. A
   `requires` entry cannot express *may have*.
3. **It would enlarge every orchestrator build.** Requirements are resolved
   into the generation prompt, so a sibling in this list puts that sibling's
   whole graph in front of the model that is writing the trust anchor —
   `architecture/generation.md`, "Scope discipline".

**Two different facts, two homes, and they must not be confused.**

| Question | Home | Why there |
|---|---|---|
| What is this tenant running, right now? | `GET /v1/services` | Derived from registration. A component that is not running is not in it, and no file can claim otherwise |
| What should this tenant build and start? | `.weblisk/config.yaml`, per [`schemas/config`](../schemas/config.md) | An operator's intent, which is a declared fact and belongs in a declared file |
| Where may a component legitimately be? | the same declared file, republished per entry as `ServiceEntry.address_provenance` | A component's address is part of the operator's intent. A registrant asserting one is making a claim, and the registry must be able to say which it is holding |

The first is what a client asks. Treating the second as the answer is how a
tenant comes to report a component it has never started, and the specification
of the second is `schemas/config.md`'s, not this document's.

### Composing a tenant

Composition is a sequence of acts, each recorded, with nothing to restart:

```
weblisk tenant create "Acme Corp"      # the orchestrator, started and claimed
weblisk component content init         # the content service, into the same module
```

`architecture/cli.md` specifies the verbs. `architecture/generation.md`
specifies how a second component is generated into a tenant that already holds
code — which is the part with the interesting failures, because the planner
must be told what is already there.

### A tenant that lacks a component MUST say so

A client asking a tenant for content, when no content service is registered,
MUST be able to tell that apart from a tenant whose content service holds
nothing. The directory answers it: `content` is absent from `namespaces`, and
no member claims the `content.*` namespace.

An empty list returned for a capability the tenant does not have is a confident
zero, and it is the worst answer available — it is indistinguishable from a
true one, and the caller's next act is to report that the tenant governs
nothing.

### A tenant's components may be distributed

Nothing requires a tenant's siblings to share a host. A tenant may put its
content service on the file server that already holds the documents, its
gateway at an edge, and its fabric beside the records it appends. That is a
legitimate tenant, not a misconfigured one, and a client that treats it as
broken is wrong about the tenant rather than careful about itself.

**What bounds the distribution is the tenant's own declaration, never a
client's guess.** A client that infers the boundary — *the same hostname I
connected to* — has moved a rule the tenant owns into the tooling, which is the
fault [`adoption`](../schemas/common.md#adoption) exists to prevent, one layer
down. The tenant declares where its components are, this orchestrator publishes
that declaration, and a client reads it. Nothing in the chain guesses.

Whether a given component *may* be placed away from its siblings is a fact its
own blueprint already carries, and it needs no new field to state it: **a
component's `## Endpoints` table is the whole of its remote surface.** A
sibling that needs only what that table serves may be wherever the tenant puts
it. A component that declares a coupling the table cannot carry — a shared
filesystem, a shared process, a store opened directly — MUST be co-located, and
the sentence declaring the coupling is the declaration.
[`architecture/fabric`](fabric.md) states its own case in exactly that form: "A
component that needs the filesystem of the thing it describes is not a client
of it."

Where a component may be placed does not decide what it may be sent there. A
component on another host has, as yet, no ceiling of its own: the rule that
it takes one from the custody its host demonstrates, never from
`address_provenance`, waits on a way to demonstrate it
([`patterns/scope`](../patterns/scope.md#destination-ceilings), the gap note).

### What the directory attests, and what it does not

`manifest.url` is supplied by the registrant. The registration contract in
[`protocol/spec`](../protocol/spec.md) validates it non-empty and nothing more,
so the registration signature proves that the key holder **asserted** an
address. It does not prove the tenant chose that address, and it does not prove
anything the tenant owns answers there.

The directory therefore says *this orchestrator accepted these registrations* —
the names, the keys, the capabilities, and the addresses as claimed. It says
so only to a reader that has it from this orchestrator: one that read it by
[`GET /v1/services`](../protocol/spec.md#get-v1services) over a connection it
opened to its anchor, the orchestrator address it registered at (below).
Nothing else makes it this orchestrator's. `ServiceDirectory.signature` has no
signing input yet and nothing verifies one, so a body pushed to an agent's
`POST /v1/services` is whatever the party that reached that listener sent, and
says nothing about this orchestrator
([`protocol/spec`](../protocol/spec.md#post-v1services), the gap there). Read
from the anchor, the directory is an authenticity statement about the
registry. It is not an authorisation statement about the addresses inside it,
and the two are easy to conflate precisely because both halves are true.

Publishing a self-asserted address without saying that it is self-asserted is
what makes the conflation invisible. So an entry MUST say how this orchestrator came
to hold its address. The field is `ServiceEntry.address_provenance` in
[`protocol/types`](../protocol/types.md), and an absent value means
`self-asserted`: an orchestrator that does not say how it knows has not
verified.

| `address_provenance` | What the orchestrator is saying | Set when |
|---|---|---|
| `self-asserted` | A registrant claimed this address and nothing has confirmed it | Always, absent one of the rungs below. The default, including when the field itself is absent |
| `declared` | The tenant declared this component at this address, and the registrant's claim matched it | The registered `url` equals the address the tenant's declared configuration gives that component |
| `verified` | `declared`, and the registered key answered at that address | The orchestrator has a round trip to the address, answered and signed by the key the registry holds for that component |

The ladder is monotone, and the two upper rungs answer different questions.
`declared` is **authorisation** — the tenant meant the component to be there.
`verified` is **authentication** — something holding the right key is there.
Neither substitutes for the other: a declared address whose name has been
repointed is authorised and wrong, and a verified address nobody declared is
authentic and unchosen. A client that needs to trust an address needs the
first; it is better off with both.

**A registrant whose claimed address contradicts the declaration is a conflict,
not a correction.** The orchestrator MUST refuse that registration with `409
ADDRESS_CONFLICT` rather than publish a contradiction, for the same reason it
refuses `NAMESPACE_CONFLICT`: the registry is the tenant's statement about
itself, and it cannot hold both answers at once.

> **Gap — the declaration has nowhere to live.** `declared` compares the
> registered `url` against the address the tenant declared for that component,
> and [`schemas/config`](../schemas/config.md) gives a component a `port` and no
> address. Until it carries one, every entry is `self-asserted` and every
> foreign address is out of bounds by the rule below. The field is that schema's
> to add; this document states only what the orchestrator does with it once it
> exists.

> **Gap — nothing can currently reach `verified`.** `GET /v1/health` is
> unauthenticated, so a probe that answers proves something is listening, which
> is not the claim. `verified` needs a probe the registered key signs over a
> nonce the orchestrator chose, and no endpoint in this document provides one.
> Until one does, `declared` is the strongest rung a tenant can occupy — which
> is enough to authorise, and is honest about what it did not prove.

### Presenting a credential to a component

A client reads an address out of the directory in order to use it, and using it
means sending a credential. The rule is about the credential rather than the
address, because that is where the loss happens:

> **A client MUST NOT present a credential at an address that credential is not
> bound to.**

A credential's **anchor** is the address the client presented an identity at in
order to obtain it — the hub address a person typed into an operator console,
or the orchestrator address a registered component was configured with. An
anchor is a fact that arrived from a person or a deployment, never one that
arrived in a response body; that is what stops the rule recursing into whatever
the last answer happened to say.

| The client holds | Same host as the anchor | Foreign host, `self-asserted` | Foreign host, `declared` or `verified` |
|---|---|---|---|
| Its anchor credential | Present it | **Refuse** — the address is not one the tenant declared | **Do not present it** — the credential is bound to the anchor, and a second host is a second place it can be taken from |
| A grant naming that exact address | Present it | Never issued — see below | Present the grant's token, and only it |
| A pass, held by the admin gateway for the one request it carries | Present it at its audience's address | **Refuse**, naming the undeclared address; the gateway answers `ADMIN_GROUP_UNAVAILABLE` | Present it at its audience's address, and nowhere else |
| None of these | — | Refuse, naming the undeclared address | Refuse, naming the credential it does not hold |

Every refusal names **which fact was missing**, and the two are different
remedies: an undeclared address is fixed in the tenant's configuration, and a
missing grant is fixed by obtaining one. A client that collapses them into
"unavailable" has reported a state nobody can act on.

Same-host is not a special case in the rule; it is the rule. The credential is
already at that host, so presenting it on another port there tells no new party
anything. What that does assume is that a second process on the anchor's host is
not a separate adversary, which is the trusted-network position
[`architecture/threat-model`](threat-model.md) Boundary 2 already takes and
records as residual. It is not an additional claim made here.

**The orchestrator MUST NOT place an address in a grant that it would not
publish as `declared`.** A grant carries the orchestrator's signature over
`target_url`, which is the orchestrator vouching for the address rather than
repeating a claim — and vouching for an address nobody declared is exactly the
conflation this section exists to stop, moved into a stronger envelope.

**A grant narrows and never widens.** Its capabilities MUST be the intersection
of what the requester holds and what the target's registered manifest declares,
and no `resources` glob in it may be wider than either side's.

A capability means the same thing at any distance. `content:read` held by a
component on another host is `content:read` — a capability names what the
holder may do, and a name that meant less at a distance would be one word doing
two jobs. What distance changes is not the meaning but the **containment**: a
grant is for one target, at one address, for the capabilities that target
declares, and it expires, because a credential's blast radius on theft is
everything it authorises and a second host is a second place to lose it from.

> **Gap — an external client cannot obtain a grant.** `POST /v1/channel`
> already has the right shape: `ChannelGrant` carries `target_url` and
> `target_pub_key` inside the orchestrator's signature with a scoped, expiring
> token. But it verifies `from_agent` against `token.sub` and requires
> `agent:message`, so it serves one registered component addressing another and
> nothing else. An operator console holding an operator token has no path to a
> grant, and needs none: it presents that token at the tenant's admin gateway
> alone, which carries each request inward on a pass
> ([`protocol/identity`](../protocol/identity.md#the-pass)), so it MUST refuse
> every foreign address regardless of its `address_provenance`. A pass is not a
> grant: it carries one person's request to one component for at most 30
> seconds, and names no address, so the table above says where the gateway
> may present one: at its audience's own address, on the anchor's host or at
> an address the tenant declared, because a pass sent to a `self-asserted`
> address on another host can be replayed to its audience, with any body its
> `cap` admits, until it expires. A client that must reach a component at a
> foreign address in its own right is what widening `/v1/channel` would serve;
> inventing a second grant type for that act is not the change that lifts it.

---

## Architecture

```
                        ┌─────────────────────────────┐
   agents ──register──▶ │        Orchestrator         │
          ──services──▶ │                             │
          ──channel───▶ │  ┌───────────────────────┐  │
                        │  │ Auth middleware       │  │  every endpoint but
   operators ─token───▶ │  │  token → capabilities │  │  those Auth Middleware
             ─admin ──▶ │  └───────────┬───────────┘  │  lists
                        │              │              │
                        │  ┌───────────▼───────────┐  │
                        │  │ Registry              │  │  agents, namespaces,
                        │  │  identity · ownership │  │  routing table
                        │  └───────────┬───────────┘  │
                        │  ┌───────────▼───────────┐  │
                        │  │ Publisher             │  │  system.* events,
                        │  │  topic → subscribers  │  │  directory broadcast
                        │  └───────────┬───────────┘  │
                        │  ┌───────────▼───────────┐  │
                        │  │ Audit log (chained)   │  │
                        │  └───────────────────────┘  │
                        └──────────────┬──────────────┘
                                       │
                              ┌────────▼────────┐
                              │ Storage         │   architecture/storage
                              │  the stores it  │   — only the stores this
                              │  owns, and no   │     component owns
                              │  others         │
                              └─────────────────┘
```

**Auth middleware** resolves a token to capabilities and refuses a request the
endpoint's declared capability does not permit. It sits in front of every route
but the ones [Auth Middleware](#auth-middleware) lists, each of which is
authenticated by something other than a token or is asked before the caller
can hold one. That list is the one statement of which routes those are; this
paragraph does not repeat it. For an operator token it also looks up the
operator and the credential the token names, in this orchestrator's own
records, on every request — `token-status-on-use` in
[`architecture/admin`](admin.md#contracts).

**Registry** holds agent records, namespace ownership and the routing table. It
records; it does not decide policy. Whether a claim is permitted is the
registration flow's decision, so that the orchestrator can claim `system.*`
through the same store that refuses it to an agent.

**Publisher** resolves a topic to subscribers by pattern and scope, delivers by
`POST /v1/event` with backoff, and dead-letters on exhaustion. Delivery is
fire-and-forget: a failure is logged and never blocks the operation that
emitted the event.

**Audit log** chains each entry to the digest of the previous one.

The orchestrator owns exactly the stores `architecture/storage` assigns it —
agent registry, audit log, channels and namespace registry — and implements no
others. An orchestrator that grew an agent's persistence layer would put a
component's data behind the trust anchor's identity.

---

## Responsibilities

1. **Agent Registration** — accept agents, verify identity, issue tokens,
   enforce namespace ownership
2. **Service Directory** — maintain and broadcast the registry of live
   agents, the routing table, and the namespace map
3. **Namespace Control** — enforce exclusive namespace ownership at
   registration, reserve `system.*` for itself
4. **Channel Brokering** — establish secure direct connections between agents
5. **Auth Enforcement** — verify tokens on all protected endpoints
6. **Audit Logging** — record every operation in an append-only log
7. **Health Aggregation** — report overall system health
8. **System Events** — publish to `system.*` namespace (agent lifecycle events)

See [Protocol Specification](../protocol/spec.md) for the authoritative
endpoint contracts.
See [Agent Architecture](agent.md) for the 6-endpoint agent protocol.
See [Lifecycle](lifecycle.md) for the continuous optimization loop.

## Endpoints

### Protocol endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| POST | /v1/register | Register | no* | Agent registration (identity-verified) |
| DELETE | /v1/register | Deregister | yes | Agent deregistration |
| GET | /v1/services | Services | yes | Service directory (routing table + namespaces) |
| POST | /v1/channel | Channel | yes | Request direct agent-to-agent channel |
| POST | /v1/rotate-key | RotateKey | yes | Rotate an agent's ML-DSA-65 key pair. Dual-signed with the current and the new key, which proves possession of both; the caller's existing token still authenticates the request |
| GET | /v1/health | Health | no | Orchestrator and hub health |
| GET | /v1/audit | Audit | yes | Query audit log |
| POST | /v1/token/exchange | TokenExchange | yes | Exchange the operator token a person has just presented to the admin gateway for a pass addressed to one component, for the admin gateway's registration and no other — see [Token Exchange](#token-exchange-post-v1tokenexchange) |
| GET | /v1/model/ceiling | ModelCeiling | yes | What a model backend may be sent now, and where it is reached, for a registered component (platform-provided — see [A model is a destination](#a-model-is-a-destination)) |

\* Registration uses ML-DSA-65 identity verification instead of tokens — there is
no token to present before an agent is registered. Key rotation is different: it
is dual-signed AND token-authenticated, because the agent already holds a valid
token when it rotates. Auth values here match
[`protocol/types`](../protocol/types.md#protocol-paths), which is the single
source of truth for them.

### Administrative endpoints

The orchestrator is the trust anchor and it holds the operator and agent
records and its own audit log, so it serves the administrative endpoints
backed by that state, beside the tenant's model surface the CLI installs.
It serves **only** those. Strategies, approvals and observations belong to the
Lifecycle Agent, workflows to domain controllers, and peers to the federation
layer; each provider specifies and serves its own, and
[`architecture/admin`](admin.md) composes them behind one operator surface.

Every endpoint here requires the stated capability from
[`protocol/types`](../protocol/types.md), carried in the caller's token: an
`admin:` capability, or, for recording and withdrawing a model provider
agreement, `model:attest`. A request can use a capability only when the
operator's role carries it now and the token's `cap` names it
([`architecture/admin`](admin.md), `token-status-on-use`), so a token whose
`cap` leaves out the capability a route requires does not reach that route,
a route only the named operator may use included.
Administration is a capability like any other: a route checks the capability
the token carries, never a position in the deployment. On these routes the
capability arrives on an operator's token, which is a person's, and on no other
kind (Auth Middleware, step 6). It arrives through the tenant's admin gateway,
which sends a request for a group this orchestrator provides on the person's
own token, for this orchestrator to judge itself, and a pass is refused on every
route here ([`protocol/identity`](../protocol/identity.md#the-pass)). A registered component reaches what it needs of
the tenant's model through `GET /v1/model/ceiling`, which is not an
administrative route ([A model is a destination](#a-model-is-a-destination)).

| Method | Path | Operation | Capability | Purpose |
|--------|------|-----------|-----------|---------|
| POST | /v1/admin/operators/register | OperatorRegister | — | Register an operator. The first presents the bootstrap secret this orchestrator emitted; every later one requires `admin:*`. Returns a token ONLY when registration also approved — see [`architecture/admin`](admin.md#the-registration-response) |
| POST | /v1/admin/operators/token | OperatorToken | — | Issue an attestation token to a caller who signs `{hub_id, name, timestamp}`, naming this hub, with the private key matching this orchestrator's record. Unauthenticated by token, because it is what issues them. Deprecated as a way to an operator token — see [`architecture/admin`](admin.md#the-identity-signs-only-to-attest) |
| POST | /v1/admin/credentials/challenge | CredentialChallenge | — | Issue a single-use nonce for a credential |
| POST | /v1/admin/credentials/token | CredentialToken | — | Issue an operator token to a credential that signed the nonce. The ordinary way to an operator token |
| POST | /v1/admin/hub/proof | HubProof | — | Sign, with the key `hub_id` names, that this hub is reached at one of its admin addresses. Unauthenticated by token, because a client asks it before it holds anything here. Answered `501` `HUB_PROOF_UNAVAILABLE` until `weblisk/hub-proof/v1` has test vectors — see [`architecture/admin`](admin.md#proving-the-hub-at-an-address) |
| POST | /v1/admin/operators/{name}/key | OperatorKeyChange | — | Change an operator's identity key, signed by the current key and the new one. Unauthenticated by token, because the two signatures authenticate it and the operator may hold no live credential — see [`architecture/admin`](admin.md#changing-an-identity-key) |
| POST | /v1/admin/operators/{name}/credentials | CredentialAttest | the operator's own token, able to use `admin:read`, or an attestation token for them | Attest a credential for that operator |
| GET | /v1/admin/operators/{name}/credentials | CredentialList | `admin:read` | That operator's credentials, revoked included |
| DELETE | /v1/admin/operators/{name}/credentials/{cid} | CredentialRevoke | the operator, able to use `admin:read`, or `admin:*` | Revoke one credential |
| GET | /v1/admin/operators | OperatorList | `admin:*` | List operators |
| GET | /v1/admin/operators/{name} | OperatorGet | `admin:read` | Operator detail |
| DELETE | /v1/admin/operators/{name} | OperatorDelete | `admin:*` | Remove an operator |
| POST | /v1/admin/operators/{name}/approve | OperatorApprove | `admin:*` | Admit a registered operator |
| PUT | /v1/admin/operators/{name}/role | OperatorRole | `admin:*` | Change an operator's role |
| GET | /v1/admin/agents | AdminAgentList | `admin:read` | Agents with status, type and metrics |
| GET | /v1/admin/agents/{name} | AdminAgentGet | `admin:read` | Agent detail — manifest, metrics, recent tasks |
| POST | /v1/admin/agents/{name}/deregister | AdminAgentDeregister | `admin:*` | Force-deregister an agent |
| GET | /v1/admin/overview | AdminOverview | `admin:read` | Summary of the state this orchestrator holds |
| GET | /v1/admin/audit | AdminAuditList | `admin:audit` | This orchestrator's audit log, with the query parameters and the answer of `GET /v1/audit` ([`protocol/spec`](../protocol/spec.md#get-v1audit)). The route a person reads it at; `GET /v1/audit` is a registered component's |
| GET | /v1/admin/audit/export | AdminAuditExport | `admin:audit` | The entries `AdminAuditList` would answer for the same filters, unpaged, as `format=json`, an array of `AuditEntry`, or `format=csv`, a header row naming `AuditEntry`'s fields and one row for each entry |
| GET | /v1/admin/model | AdminModelGet | `admin:read` | This tenant's model backend — Studio is a client of it (platform-provided) |
| PUT | /v1/admin/model | AdminModelPut | `admin:*` | Set this tenant's model backend (platform-provided) |
| GET | /v1/admin/model/providers | AdminModelProviders | `admin:read` | Discovery on **this hub's host** (platform-provided) |
| POST | /v1/admin/complete | AdminComplete | `admin:read` | Run a completion under this tenant's model policy, behind the destination gate (platform-provided) |
| POST | /v1/admin/model/agreements | AdminModelAgreementRecord | `model:attest` | Record a model provider agreement (platform-provided) |
| GET | /v1/admin/model/agreements | AdminModelAgreementList | `admin:read` | Every agreement, withdrawn and lapsed ones included (platform-provided) |
| DELETE | /v1/admin/model/agreements/{id} | AdminModelAgreementWithdraw | `model:attest` | Withdraw an agreement (platform-provided) |
| GET | /v1/admin/model/ceiling | AdminModelCeiling | `admin:read` | What a model backend may be sent now (platform-provided) |

The model routes are marked `provided: platform` in the declaration. They are
NOT generated: the CLI installs them after generation, and they intercept their
own paths ahead of the generated router. A hub MUST serve all of them as this
section specifies; today's CLI serves four, authorised as the table says and
with no destination gate
([A model is a destination](#a-model-is-a-destination), the gap note).

They are the tenant's model surface. The CLI installs them because they read
the tenant's model configuration, discover which provider binaries are on the
hub's host, and run a completion through them, and a generated component
cannot do that without reproducing the CLI's provider catalogue. The CLI
chooses a model of its own only where no tenant's model applies: when it
creates a tenant, and for work a person starts outside any tenant.

**Every one of them is authorised by the orchestrator.** The code the CLI
installs to serve them, inside the orchestrator's own process and called the
model gateway there, is neither the tenant's admin gateway nor its
application gateway. It has the orchestrator judge the caller's token on each
request, by
the middleware that guards every route under the same prefix: every step of
[Auth Middleware](#auth-middleware) under `/v1/admin/`, step 6 included, and
every step but 6 for `/v1/model/ceiling`. It never accepts a token on its
shape, and a request it cannot get a judgement on is refused.
Asking a model for them produced four handlers against an unspecified
contract, all of them shadowed the moment the model gateway was installed. So this
document specifies one thing about them and nothing else of their behaviour:
what a model destination requires, below.

### A model is a destination

A completion sends what it carries to a model provider, which is a destination
with a ceiling ([`patterns/scope`](../patterns/scope.md#destination-ceilings)).
The model routes are where the tenant applies that gate, holds the agreements
that raise a ceiling, and answers what a ceiling is.

**`POST /v1/admin/complete` applies the gate before it runs anything.** Its
request carries `scope`: the highest scope of what the prompt carries, as the
tenant reported it to the caller. A caller whose prompt carries nothing the
tenant holds says `public`. The route finds the ceiling of the backend it would
run and the model it would ask it for, as `GET /v1/admin/model/ceiling`
answers it, and refuses:

- with `SCOPE_MISSING` when `scope` is absent;
- with `SCOPE_CEILING_EXCEEDED` when `scope` is above the ceiling, or is
  `restricted` or above whatever the ceiling.

Each refusal carries a `DestinationRefusal` naming the backend and its ceiling,
and runs nothing. The route never runs another backend instead. It cannot see
where the text in a prompt came from, so `scope` is the caller's statement and
the gate here is as good as the caller: that is why
[`patterns/scope`](../patterns/scope.md#the-gate) binds every sender, a client
included.

> **Gap — the CLI's gateway serves four of these nine routes, with no
> destination gate.** The model gateway the CLI installs today serves `GET` and
> `PUT /v1/admin/model`, `GET /v1/admin/model/providers` and
> `POST /v1/admin/complete`. It does not serve the three agreement routes,
> `GET /v1/admin/model/ceiling` or `GET /v1/model/ceiling`, and being
> `provided: platform` they are not generated either, so a request to any of
> them falls through to the generated router and is answered `404`. Its
> `POST /v1/admin/complete` reads no `scope` and runs with none of the gate
> above: it never refuses `SCOPE_MISSING` or `SCOPE_CEILING_EXCEEDED`, and runs
> whatever it is sent, `restricted` included. Until a hub serves all nine and
> gates `complete`:
>
> - a client MUST NOT read a `404` from either ceiling route as a ceiling. It
>   cannot learn one, so it uses `internal`, the ceiling a provider has with
>   nothing attested, as an api-ai endpoint that cannot learn a ceiling does
>   ([`patterns/api-ai`](../patterns/api-ai.md#destination-ceilings));
> - a client MUST apply the gate itself before it sends to `complete`, with
>   that ceiling, and MUST NOT rely on the hub to refuse anything: nothing
>   undeclared and nothing above `internal` is sent
>   ([`patterns/scope`](../patterns/scope.md#the-gate), every sender);
> - no agreement can be recorded, so no provider's ceiling is above
>   `internal` at any tenant.
>
> Closing it is the CLI's: serve the agreement and ceiling routes, and gate
> `complete` on `scope`, as this section specifies.

**Agreements.** A `ProviderAgreement`
([`patterns/scope`](../patterns/scope.md#model-providers)) is recorded only on
a person's operator token holding `model:attest`, which
[`protocol/types`](../protocol/types.md) marks *person only*, and withdrawn on
that token by `DELETE /v1/admin/model/agreements/{id}`. The one other
withdrawal is the side effect of `PUT /v1/admin/model` below, which
`admin:*` reaches: it only ever withdraws, so it only ever lowers a ceiling,
and it records `withdrawn_by` from that request's token.

- `POST /v1/admin/model/agreements` takes the agreement's `party`, `backends`,
  `models`, `component` where there is one, `agreement`, `agreement_digest`,
  `level` and `not_after`. The route sets `id`, `recorded_by` from the token's
  `identity_id`, and `recorded_at`, and never takes them from the body. It
  returns the agreement as recorded.
- `DELETE /v1/admin/model/agreements/{id}` withdraws it, setting
  `withdrawn_by` and `withdrawn_at` the same way. Withdrawing one already
  withdrawn changes nothing and returns it as recorded.
- `GET /v1/admin/model/agreements` lists every agreement, withdrawn and lapsed
  ones included, so a person can see what was attested and when it ended.
- **`PUT /v1/admin/model` withdraws what it could carry past an agreement.**
  An agreement covers the names and the models it lists, never what a name
  reaches ([`patterns/scope`](../patterns/scope.md#model-providers)). So a
  request that sets a name a current agreement lists withdraws that
  agreement in the same write, unless the configuration held that same name
  before the write and the request changes nothing of it but the model. It
  sets `withdrawn_by` from the request's token and `withdrawn_at`, and its
  answer names each one withdrawn. A request that changes only the model
  withdraws nothing, because a ceiling is a model's as well as a name's: the
  model it sets has the agreement's level only where the agreement lists it,
  and `internal` otherwise. This is the one rule for what the request
  withdraws. Without it, a token narrowed for administration, carrying
  `admin:*` and not `model:attest`, could point a listed name at a party
  nobody attested and raise that party to the agreement's level; and without
  the ceiling being the model's, it could do the same by changing only the
  model, at a backend whose model chooses who runs it.
- `GET /v1/admin/model/ceiling` returns a `ProviderCeiling` for the backend
  and the model `GET /v1/admin/model` reports, or for the name `?backend=`
  gives and the model `?model=` gives. It is what a client reads before it
  sends.
- **Either ceiling route answers every name and model.** A name no current
  agreement lists has the ceiling `internal`, whether or not the tenant's
  model configuration names it, and so does a model the agreement listing
  the name does not list, and a request that names no model. A name and a
  model one current agreement lists both of have that agreement's level. The
  routes never refuse a name or a model as unknown: an api-ai
  endpoint asks by its own `providers:` keys
  ([`patterns/api-ai`](../patterns/api-ai.md#destination-ceilings)), which are
  configured where these routes cannot see them, and a name nobody listed is
  given `internal` and nothing more. `address` is present only for the
  tenant's model backend, the one whose address these routes know.
- `GET /v1/model/ceiling` returns the same `ProviderCeiling` to a registered
  component, on its own registration token. It is not an administrative
  route, so step 6 of Auth Middleware does not refuse that token, and an
  attestation token is refused there as everywhere but `CredentialAttest`. It
  is how an api-ai endpoint takes each provider's ceiling
  ([`patterns/api-ai`](../patterns/api-ai.md#destination-ceilings)) and how the
  external boundary of [`architecture/enforcement`](enforcement.md) recognises
  the tenant's model backend by its `address`. It discloses no agreement's
  terms and no credential.

| Code | HTTP | When |
|---|---|---|
| `CREDENTIAL_REQUIRED` | 401 | The token is not a person's operator token ([`protocol/types`](../protocol/types.md#errorresponse)) |
| `FORBIDDEN` | 403 | The request cannot use `model:attest`: the operator's role does not carry it now, or the token's `cap` does not name it (Auth Middleware, step 8; [`protocol/types`](../protocol/types.md#error-handling)) |
| `INVALID_REQUEST` | 400 | A required field is missing, `backends` or `models` is empty, or `agreement_digest` is not `sha256:` and 64 lowercase hex characters |
| `MODEL_AGREEMENT_LEVEL_REFUSED` | 400 | `level` is not `internal` or `confidential` |
| `MODEL_AGREEMENT_LAPSE_INVALID` | 400 | `not_after` is not in the future, or is more than 90 days after the request |
| `MODEL_AGREEMENT_EXISTS` | 409 | A model in `models`, at a name in `backends`, is already covered by an agreement that is current. The response names that agreement |
| `NOT_FOUND` | 404 | No agreement of that `id` |

Recording one publishes `system.model.agreement_recorded`, and withdrawing one
`system.model.agreement_withdrawn`. Each is audited, recording who acted by
identity id.

`/v1/admin/overview` reports what the orchestrator holds — agent counts,
namespace count, audit depth, health — and nothing else, in the members and
shapes [`architecture/admin`](admin.md#get-v1adminoverview) names, which are
stated there alone. It asks no other
component for a figure: the orchestrator never presents a token it received to
anyone ([`protocol/identity`](../protocol/identity.md#the-pass)). The System
overview an operator sees is composed by the admin gateway, which asks each
other figure of the component that holds it, on a pass addressed to that
component, and reports unavailable, never zero, every figure no component here
may be asked for ([`architecture/admin`](admin.md#the-admin-api-is-an-aggregate)).
An empty workflow list and an absent workflow engine are different facts, and a
console that renders them identically tells an operator the system is quiet
when it is simply not there.

---

## Interfaces

What other components consume, beyond the HTTP surface declared above.

**Consumed by every agent** — registration, the service directory, and channel
brokering. An agent needs no other interface to participate: it registers, is
told what exists, and reaches its peers directly.

**Consumed by the administrative surface** — operator records, agent detail,
the audit trail, and the token exchange, which the admin gateway alone calls.
`architecture/admin` composes these behind one operator console and adds none
of its own state.

**Published as events** — the `system.*` namespace, which the orchestrator owns
exclusively. An agent learns that another registered, deregistered or rotated a
key by subscribing, never by polling.

**Not offered:** no query interface over another component's data, no execution
interface, and no interface that returns a credential belonging to somebody
else.

---

## Data Flow

```
REGISTRATION          agent → POST /v1/register
                        → verify signature over the manifest as received
                        → check replay window
                        → refuse reserved namespaces, refuse conflicts
                        → store agent, claim namespaces, build routes
                        → audit, mint token
                        → publish system.agent.registered
                        → broadcast the directory to every agent

DISCOVERY             agent → GET /v1/services
                        → auth middleware resolves token to capabilities
                        → directory filtered to what the caller may see
                        → routing table and namespace ownership returned

EXCHANGE              admin gateway → POST /v1/token/exchange
                        → its own registration token, declaring token:exchange
                        → judge the person's token as on an operator route
                        → mint a pass for one audience, carrying the scope
                        → audit, return the pass
                        → the gateway sends the person's request on it

CHANNEL               agent → POST /v1/channel
                        → verify from_agent matches the token subject
                        → require agent:message
                        → mint a scoped channel token
                        → audit, return the grant
                        → the two agents then talk DIRECTLY, not through here

EVENT                 orchestrator → POST /v1/event on each subscriber
                        → topic matched against the routing table
                        → scope filtered per subscription
                        → delivered with backoff, dead-lettered on exhaustion
                        → failure is logged, never blocking the emitter
```

Every path that changes state writes an audit entry chained to the previous
one, and no path returns data the caller's capabilities do not permit.

---

## Contracts

What the admin gateway may rely on when it has this orchestrator exchange a
person's operator token for a pass. A blueprint whose component calls the
exchange binds this behaviour, by name, from its dependency on this blueprint
([`schemas/common`](../schemas/common.md#binding-types)). The prose is under
[Token Exchange](#token-exchange-post-v1tokenexchange), and it says why.

```yaml
contracts:
  behaviors:
    - name: token-exchange
      description: Exchange the operator token a person has just presented to the admin gateway for a pass addressed to one component
      required: true
      rules:
        - The route POST /v1/token/exchange MUST take a TokenExchangeRequest and answer every judgement of its subject_token with 200 and a TokenExchangeResponse (protocol/types)
        - It MUST read the caller's token from the Authorization header alone (Auth Middleware step 2), so nothing in the body, the token it exchanges included, authenticates the request. A request with no Authorization header MUST be refused with 401, as on any other route
        - It MUST admit only a registration token, one with no type and no cid, whose sub is a component registered here now, whose identity_id is that registration's (protocol/identity), and whose registration declares token:exchange (protocol/types). Every other token Auth Middleware lets through MUST be refused with FORBIDDEN, disclosing nothing about subject_token - an operator token, a channel token, a registration token whose registration does not declare token:exchange, and one whose component has deregistered or whose identity_id is no longer its registration's, as after POST /v1/rotate-key (protocol/spec). An attestation token and a pass are refused before this, at Auth Middleware step 5, a pass with PASS_AUDIENCE_MISMATCH
        - A body with no subject_token or no audience, or whose scope names no capability or a name protocol/types does not list, MUST be refused with 400 INVALID_REQUEST. An audience that is not the identity id of a component registered here now, other than the caller, MUST be refused with 404 NOT_FOUND. Neither mints anything
        - It MUST judge subject_token as Auth Middleware judges a token on an operator route - its signature and expiry, that it is an operator token carrying cid, and token-status-on-use (architecture/admin) - and answer issued false with the code it would refuse that token with on its own routes. A pass, a registration token, a channel token and an attestation token are each refused with CREDENTIAL_REQUIRED, so a pass is never exchanged again. A token it cannot judge MUST NOT be exchanged
        - The pass's cap MUST be the intersection of scope and what the person may use now - what the operator's role carries now, never beyond the token's cap, read as Auth Middleware step 8 reads a role and a cap - keeping each name scope gives only where the person may use it, and admin:* only where they may use every capability of the admin family by name. Where the intersection is empty it MUST mint nothing and answer issued false with FORBIDDEN
        - The pass MUST carry what protocol/identity's The pass gives it, with aud the audience, act the caller and cap that intersection, and the answer MUST carry it with expires_at and capabilities
        - It MUST mint nothing but a pass, and MUST NOT keep, cache or present subject_token anywhere
        - Each exchange MUST be audited, refused or not, with the identity id of the operator subject_token names where it names one, the caller's identity id, the audience and the scope
```

---

## Startup Sequence

```
1. Load or generate ML-DSA-65 identity (name: "orchestrator"), the key that
   signs tokens. A first start records the hub_id, the fingerprint of that
   first key, with its own state. Once the key has rotated, also load the
   first key, which is kept to sign the hub proof and nothing else
   (architecture/admin, Proving the hub at an address)
2. Initialize empty agent registry, namespace map, routing table, audit log
3. Reserve "system" namespace for orchestrator
4. Register HTTP routes for every endpoint the declaration lists, the
   protocol endpoints, the token exchange and the administrative endpoints;
   the platform-provided model routes are installed by the CLI ahead of the
   generated router (Administrative endpoints)
5. Start HTTP server on configured port
6. Print startup info (URL, public key, hub_id, how to register agents)
7. Block and serve requests
```

---

## Registration Flow (POST /v1/register)

See [Protocol Specification — POST /v1/register](../protocol/spec.md)
for the authoritative registration contract.

**Orchestrator implementation notes:**

```
1.  Parse and validate per spec.md contract. A manifest whose capabilities
    name one protocol/types marks person only → 403 CAPABILITY_PERSON_ONLY,
    before anything is recorded. Its pass_routes are not read for this: a
    pass route names what the component checks on a person's pass, never
    what it holds, and none of it reaches the token of step 5. They are
    read for two things, each → 400 INVALID_REQUEST before anything is
    recorded: a pass route naming a capability protocol/types does not
    list, in its capabilities or in a body requirement; and two pass routes
    that can match one request, which are two with the same method whose
    paths have as many segments, each pair of segments equal or one of
    them a {name} segment. So no exchange the admin gateway asks names a
    capability that does not exist, and a request matches at most one of
    a component's pass routes
2.  Verify signature and replay protection (see protocol/identity.md)
3.  Validate namespace claims:
    a. For each namespace in manifest.publishes:
       - Check: is namespace already owned by another agent?
         → 409 NAMESPACE_CONFLICT {"conflict": "<owner-name>"}
       - Check: is namespace in reserved list (system.*)?
         → 403 NAMESPACE_RESERVED
       - If clear → grant ownership: namespace_map[namespace] = agent_name
    b. No publishes declared → agent is subscription-only (no conflict possible)
4.  Validate subscription scopes:
    a. For each subscription in manifest.subscriptions:
       - scope "self" → always allowed
       - scope "*" → check agent has "event:observe" capability → 403 if missing
       - scope "<name>" → check collaborator relationship → 403 if unauthorized
5.  Generate agent ID and auth token (WLT format — see
    [protocol/identity.md Token System](../protocol/identity.md#token-system)):
    - Token type: WLT (Weblisk Token) with ML-DSA-65 signature
    - Claims: sub=agent_name, iss="orchestrator", cap=manifest.capabilities,
      identity_id=fingerprint(manifest.public_key)
    - Expiry: 24 hours (configurable via token TTL setting)
6.  Store agent in registry:
    {manifest, agentID, token, registeredAt, lastSeen, status: "online"}
    Its ServiceEntry carries manifest.pass_routes unchanged, which is where
    the admin gateway learns what a person's request may reach on this
    component and what each needs (protocol/types, PassRoute)
7.  Build routing table entries for this agent's subscriptions:
    For each subscription → add RouteEntry to routing_table[pattern]
8.  Log audit entry: actor=orchestrator, action=register, target=agent_name
9.  Respond with RegisterResponse (includes agent_id, token, service directory)
10. Publish system.agent.registered event (scope: "*")
11. Asynchronously broadcast updated ServiceDirectory to ALL OTHER agents
    via POST /v1/services (includes routing_table and namespaces)
```

### Namespace Enforcement Rules

| Condition | Response |
|-----------|----------|
| Namespace unclaimed | Grant ownership, add to namespace_map |
| Namespace already owned by same agent (re-registration) | Allow (idempotent) |
| Namespace owned by different agent | 409 NAMESPACE_CONFLICT |
| Namespace is `system` or `system.*` | 403 NAMESPACE_RESERVED |
| Agent re-registers with FEWER namespaces | Release dropped namespaces |

### Domain Dependency Tracking

When `manifest.type = "domain"`, the orchestrator tracks whether the
domain's `required_agents` are all registered:

```
1. Extract required_agents from manifest
2. Check each against current registry
3. Store domain dependency status:
   - "ready": all required agents registered
   - "degraded": some missing (log which)
4. Include dependency status in ServiceDirectory
5. On future registrations: re-evaluate all domains that list the
   newly-registered agent in required_agents
```

---

## Deregistration Flow (DELETE /v1/register)

```
1. Authenticate request (extract and verify token)
2. Remove agent matching token.sub from registry
3. Release all namespaces owned by the agent:
   For each namespace where namespace_map[ns] == agent_name:
     delete namespace_map[ns]
4. Remove all routing table entries for this agent
5. Log audit entry
6. Publish system.agent.deregistered event (scope: "*")
7. Broadcast updated ServiceDirectory to all remaining agents
8. Respond: {"status": "deregistered"}
```

---

## Service Directory (GET /v1/services)

Returns the complete service directory including the routing table
and namespace map:

```json
{
  "agents": [
    {
      "name": "seo-analyzer",
      "url": "http://localhost:9801",
      "capabilities": ["task:execute", "agent:message"],
      "type": "agent",
      "domain": "seo",
      "status": "online"
    }
  ],
  "routing_table": {
    "workflow.completed": [
      {"agent": "seo", "url": "http://localhost:9805/v1/event", "group": "seo", "scope": "self"},
      {"agent": "lifecycle", "url": "http://localhost:9810/v1/event", "group": "lifecycle", "scope": "*"}
    ],
    "task.complete": [
      {"agent": "workflow", "url": "http://localhost:9808/v1/event", "group": "workflow", "scope": "self"}
    ]
  },
  "namespaces": {
    "system": "orchestrator",
    "workflow": "workflow",
    "task": "task",
    "lifecycle": "lifecycle",
    "seo": "seo",
    "content": "content",
    "health": "health"
  }
}
```

### Routing Table Structure

The routing table maps topic patterns to subscriber entries. Each
entry includes the subscriber's event endpoint URL, consumer group,
and scope filter.

When a topic is subscribed with a wildcard pattern (`*` or `#`),
the orchestrator stores the pattern as-is. Publishing agents resolve
matches locally using the pattern matching rules from
[patterns/messaging](../patterns/messaging.md).

### Service Broadcasting

After any registration or deregistration, the orchestrator
asynchronously pushes the current `ServiceDirectory` to every other
registered agent via `POST /v1/services`. Failures are logged but
never block.

---

## Channel Brokering (POST /v1/channel)

```
1. Authenticate request
2. Parse ChannelRequest from body
3. Verify from_agent matches token.sub (can't request channels for others)
4. Verify token has "agent:message" capability → 403 if missing
5. Look up to_agent in registry → 404 if not found
6. Generate channel ID (32 hex chars)
7. Create channel token:
   - sub: "from_agent↔to_agent"
   - iss: "orchestrator"
   - iat: now
   - exp: now + 1 hour
   - cid: channelID
8. Store active channel: {channelID, from, to, purpose, createdAt, expiresAt}
9. Log audit entry
10. Build ChannelGrant with target URL, target public key, channel token
11. Sign the grant with orchestrator's private key
12. Respond with ChannelGrant
```

---

## Auth Middleware

Applied to all endpoints except `/v1/health`, `POST /v1/register`, the four
operator routes that establish or issue tokens — `OperatorRegister`,
`OperatorToken`, `CredentialChallenge` and `CredentialToken` — `HubProof`,
which a client asks before it holds anything here, and `OperatorKeyChange`,
which the operator's current and new identity keys authenticate (see
[Administrative endpoints](#administrative-endpoints)). Each of those six
administrative routes is limited per source before any signature is verified
or made. A request from an address `orchestrator.admin_gateway_from` lists is
counted by the client the admin gateway names in `X-Forwarded-For`, never by
the gateway's own address, and any other request by its connection's address,
so where the configuration names no such address the gateway's clients share
one count ([`architecture/admin`](admin.md#contracts),
`auth-route-rate-limit`):

```
1. Check Authorization header for "Bearer <token>"
2. If no header, check request body for "token" field — except on
   TokenExchange and every /v1/admin/* route, whose token is read from the
   header alone
3. Verify token against orchestrator's signing key
4. Check expiry
5. Refuse a token whose type is "pass" with PASS_AUDIENCE_MISMATCH, on every
   route, and log it as a security event: this orchestrator is the audience
   of no pass (protocol/identity, The pass). Refuse a token whose type is
   "attestation" with CREDENTIAL_REQUIRED, on every route but
   CredentialAttest. On CredentialAttest, refuse it with
   OPERATOR_SUBJECT_MISMATCH unless its sub is the operator the path names
6. On every /v1/admin/* route, refuse a token whose type is not "operator"
   with CREDENTIAL_REQUIRED. CredentialAttest also takes the attestation
   token step 5 let through. An agent token and a channel token carry no type,
   so neither reaches an administrative handler
7. For an operator token, check the operator and the credential it names are
   live in this orchestrator's own records (architecture/admin,
   token-status-on-use)
8. On every /v1/admin/* route, check that the request can use the capability
   the route requires: the auth its declaration names, or, for a route
   architecture/admin's tables give a minimum role, the capability that
   minimum stands for. The request can use a capability when the operator's
   role carries it now and the token's cap names it, admin:* being read as
   each admin: capability by name. An operator token whose cap is absent or
   empty names none. Otherwise FORBIDDEN, whatever the role
   (architecture/admin, Auth Middleware)
9. On failure → 401: INVALID_SIGNATURE from step 3, malformed tokens
   included, TOKEN_EXPIRED from step 4, PASS_AUDIENCE_MISMATCH from step 5,
   and {"error": "valid token required — register first"} where no token was
   presented; 403 FORBIDDEN from step 8; or the operator code
   architecture/admin's Error Handling names
10. On success → pass TokenClaims to handler
```

This is the one sequence for every route this orchestrator serves, the
`/v1/admin/*` routes included, and the platform-provided model routes judged by
it ([Administrative endpoints](#administrative-endpoints)).
[`architecture/admin`](admin.md#auth-middleware) says which capability each
administrative minimum stands for, and how a token's `cap` narrows a role.

Steps 5 and 6 run before any handler, because a route's `auth: "token"` in the
declaration accepts any token this orchestrator signed. Without them, an
attestation token, obtained with nothing but an identity signature, would read
the audit log and broker channels, which is the login by identity key that
[`patterns/principal-identity`](../patterns/principal-identity.md) forbids. And
an agent token whose `sub` happened to match an operator's name would reach that
operator's credentials.

---

## Token Exchange (POST /v1/token/exchange)

A WLT is self-contained, and only this orchestrator holds the operator,
credential and grant an operator token rests on. The admin gateway therefore
has a person's token exchanged here for each request it carries to a component
other than this orchestrator, and sends that request on the pass it is given
([`protocol/identity`](../protocol/identity.md#the-pass)):

```
POST /v1/token/exchange
Authorization: Bearer <the admin gateway's own registration token>
{ "subject_token": "<the operator token the person presented>",
  "audience": "<identity id of the component the request goes to>",
  "scope": ["content:read"] }

200 { "issued": true, "pass": "<WLT, type pass>", "expires_at": 1712160030, "capabilities": ["content:read"] }
200 { "issued": false, "code": "OPERATOR_REVOKED" }
```

`token-exchange` in [Contracts](#contracts) is the rule. The body is a
`TokenExchangeRequest` and the answer a `TokenExchangeResponse`, both
[`protocol/types`](../protocol/types.md#tokenexchangerequest)'s. The shape is
OAuth 2.0 Token Exchange's ([RFC 8693](https://www.rfc-editor.org/rfc/rfc8693)):
the person's token is the subject token, and the gateway, authenticated by its
own registration token, is the actor.

The caller's own token comes from the `Authorization` header and nowhere else.
`subject_token` is never step 2's `token` field: were step 2 to read a body
here, a request with no header whose body carried the person's token under
`token` as well would be authenticated by that very token, and the route would
no longer need the gateway's registration.

The judgement is the one this orchestrator's middleware makes on an operator
route, made while the person's request is being carried, so a component that
holds a pass acts on a person's token exactly as far as this orchestrator would
act on it then, and asks nothing again. Every answer about the person's token is
a 200, so a status other than 200 judged the gateway's own request, and the
gateway never relays its code as the person's.

**No route tells a component whether an operator token is live.** No component
is presented one ([`protocol/identity`](../protocol/identity.md#the-pass)), so
none has one to ask about. What such a route would answer, the exchange answers
once, before the component is reached.

---

## System Events

The orchestrator owns the `system.*` namespace and publishes lifecycle
events that all agents may subscribe to:

| Topic | Scope | Published When |
|-------|-------|----------------|
| `system.agent.registered` | `*` | New agent successfully registered |
| `system.agent.deregistered` | `*` | Agent deregistered |
| `system.model.agreement_recorded` | `*` | A person recorded a model provider agreement. Carries its `id`, `party`, `backends`, `models`, `level`, `not_after` and `recorded_by` |
| `system.model.agreement_withdrawn` | `*` | A person withdrew one. Carries its `id`, `backends` and `withdrawn_by` |
| `system.shutdown` | `*` | Orchestrator is shutting down gracefully |

System events are published via the same HTTP-based pub/sub mechanism.
The orchestrator resolves subscribers from its own routing table and
delivers via `POST /v1/event`.

---

## Audit Logging

Every operation creates an AuditEntry:

```json
{
  "id": "<generated>",
  "timestamp": 1712160000,
  "actor": "orchestrator",
  "action": "register",
  "target": "seo-analyzer",
  "detail": "Agent registered, namespace 'seo' granted",
  "status": "ok"
}
```

### Audit Actions

| Action | Description |
|--------|-------------|
| `register` | Agent registered |
| `deregister` | Agent deregistered |
| `channel` | Channel brokered |
| `namespace_grant` | Namespace ownership granted |
| `namespace_release` | Namespace ownership released |
| `event` | System event published |
| `model_agreement_record` | A model provider agreement recorded |
| `model_agreement_withdraw` | A model provider agreement withdrawn |

Log to stderr in real-time AND persist to append-only flat-file
storage (JSONL).

Format: `[audit] HH:MM:SS actor → target: detail [status]`

---

## Health (GET /v1/health)

No auth. Returns:

```json
{
  "name": "orchestrator",
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 3600,
  "metrics": {
    "agents": 8,
    "domains": 3,
    "channels": 2,
    "namespaces": 7
  }
}
```

---

## Data Structures

See [Storage](storage.md) for the canonical abstract store interfaces
and [protocol/types.md](../protocol/types.md) for type definitions.

**Key implementation notes:**

- **Agent Registry** — Thread-safe map of agent name → registered agent
  info. Entries include `manifest.type` for domain dependency tracking.
- **Namespace Map** — Map of namespace → owner agent name. Thread-safe.
  Mutations only at registration/deregistration.
- **Routing Table** — Map of topic pattern → []RouteEntry. Rebuilt from
  agent subscriptions at registration. Distributed as part of the
  service directory.
- **Domain Dependency Map** — Map of domain name → `{required_agents: [], status}`.
  Recalculated on every registration/deregistration.
- **Channel Registry** — Map of channel ID → active channel info, with
  1-hour TTL. Expired channels cleaned up periodically.
- **Audit Log** — Append-only flat-file (JSONL). In-memory buffer for
  recent entries, flushed periodically.

---

## Configuration

| Setting | Flag | Default |
|---------|------|---------|
| Port | `--port` | `9800` |
| Identity key path | `--keys` | Implementation-defined |
| Audit log path | `--audit` | Implementation-defined |
| Channel TTL | — | `3600` (1 hour) |
| Admin addresses, the origins the admin gateway is reached at | `orchestrator.admin_addresses` ([`schemas/config`](../schemas/config.md#orchestrator)) | none |
| The addresses the admin gateway's requests arrive from | `orchestrator.admin_gateway_from` ([`schemas/config`](../schemas/config.md#orchestrator)) | none |

---

## Types

### AgentEntry

An entry in the orchestrator's agent registry, as
[Registration Flow](#registration-flow-post-v1register) step 6 stores it. The
orchestrator owns it, and [`architecture/storage`](storage.md#store-agent-registry)
binds it for the store that keeps it; it is defined here alone.

```yaml
types:
  AgentEntry:
    fields:
      manifest:
        name: Manifest
        type: AgentManifest
        required: true
        description: "The manifest the agent registered with"
      agent_id:
        name: AgentID
        type: string
        required: true
        description: "Assigned agent identifier (32 hex chars)"
      token:
        name: Token
        type: string
        required: true
        description: "Current auth token"
      registered_at:
        name: RegisteredAt
        type: int64
        required: true
        description: "Unix epoch seconds of registration"
      last_seen:
        name: LastSeen
        type: int64
        required: true
        description: "Unix epoch seconds of the last health check or request"
      status:
        name: Status
        type: string
        required: true
        description: "`online`, `offline` or `degraded`"
```

---

## Types

```yaml
types:

  OrchestratorConfig:
    description: What an orchestrator is told at start-up
    fields:
      port:
        type: int
        description: Port the orchestrator listens on
      env:
        type: string
        description: Deployment environment
        constraints:
          enum: [development, staging, production]
      log_level:
        type: string
        description: Minimum level emitted
      storage_dsn:
        type: string
        description: Where the orchestrator's stores live. Carries no credential — key and secret material is supplied per protocol/identity, not through configuration
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      The orchestrator is the tenant's trust anchor. It decides which agents
      exist, what capabilities they hold and which namespaces they own, so a
      compromise here is not a data exposure — it is control of the tenant.
      It trusts nothing it has not verified: an agent is a signature over a
      manifest, an operator is a signature over a payload, and a caller is a
      token it issued. It holds no user credentials and no user sessions;
      those belong to the application gateway, which is a separate listener
      with a separate threat profile.

  boundaries:
    - boundary: Agent → Orchestrator. Identity is established by ML-DSA-65
        signature over the manifest before any record is written; see
        protocol/identity
    - boundary: Operator → Orchestrator, through the admin gateway.
        Registration and token issuance are signed and verified per
        architecture/admin; the orchestrator never authenticates an end user
    - boundary: Admin gateway → Orchestrator. A person's token is meant to
        arrive only from the admin gateway, to be judged on a route here or
        exchanged for a pass addressed to one other component
        (protocol/identity, The pass). Nothing here enforces that yet, which
        is a gap. The orchestrator serves /v1/admin/* on the listener
        components reach, to any caller, so a token a client sends here
        directly, as its own blueprint forbids, is judged by the same Auth
        Middleware as one the gateway forwarded. What such a request escapes
        is the gateway's own network controls, its operator IP allowlist
        among them, never the judgement of the token. Serving the
        administrative routes on a listener only the admin gateway reaches is
        what would enforce the boundary
    - boundary: Orchestrator → Agent. Events reach the URL a verified manifest
        declared, never a URL supplied in a request
    - boundary: Orchestrator → Storage. Only the stores architecture/storage
        assigns to this component; an agent's data stays behind that agent's
        identity
    - boundary: Signing key → everything. The private key is the tenant's most
        sensitive material and never leaves the process that loaded it

  enforcement:
    - rule: An unverified identity establishes nothing
      mechanism: Signature verification over the manifest canonicalized as
        received, then the replay window, both per protocol/identity — before
        any record is written
    - rule: The system namespace is not claimable by an agent
      mechanism: The registration flow refuses a match with 403
        NAMESPACE_RESERVED. The store records claims and decides nothing, so
        the orchestrator can hold the namespace through the store that refuses
        it to others
    - rule: A capability is never taken from a request
      mechanism: Role and capabilities are read from the stored record when a
        token is minted, and again on every request that bears one; the request
        body supplies neither
    - rule: Administration is a capability, not a position
      mechanism: Every admin endpoint states which capability it requires,
        and Auth Middleware checks that the request can use it, on an
        operator's token alone (step 6). So no address, host or deployment
        position confers it, and an administrative interface holds no grant
        of its own; the admin gateway carries a person's token here as it
        arrived
    - rule: A token this orchestrator receives goes no further
      mechanism: It calls no component on a token it was presented, and a
        person's request reaches another component only on a pass the token
        exchange mints for that component alone, so no component holds a
        token it could present elsewhere
    - rule: A deletion from the audit log is detectable
      mechanism: Each entry carries the digest of the previous one
    - rule: The orchestrator serves no user-facing surface
      mechanism: Every declared endpoint is the protocol's or administrative;
        architecture/gateway is what browsers reach
```

**What a compromise reaches.** An agent's key reaches that agent's namespaces
and capabilities, and no other agent's key. An operator's credential reaches
the capabilities of that operator's role until it is revoked or its attestation
expires, and an operator's identity key reaches the right to attest new
credentials. The orchestrator's signing key reaches
every token it has issued and the ability to issue more — but not the data
agents hold, which is theirs.

---

## Implementation Notes

- The orchestrator is the single entry point for agent registration; it must be the first component started
- Namespace ownership is exclusive — once claimed, a namespace is locked to the registering agent
- Service directory broadcasts are pushed to all agents after every registration or deregistration change
- Channel brokering creates short-lived tokens scoped to a specific agent pair
- Auth middleware validates ML-DSA-65 signatures and WLT tokens on every request but the routes [Auth Middleware](#auth-middleware) names, which carry none
- The orchestrator should be stateless where possible — registry data can be backed by the storage engine

---

## Verification Checklist
- [ ] `POST /v1/admin/operators/token` issues a token to an approved operator whose signature verifies against the stored public key — an attestation token, per `architecture/admin`
- [ ] `POST /v1/admin/operators/token` requires no bearer token — it is the endpoint that issues them
- [ ] An operator token carries the role and capabilities from the orchestrator's own record, never from the request
- [ ] `POST /v1/admin/credentials/challenge` and `POST /v1/admin/credentials/token` require no bearer token, and every other operator route refuses a token whose operator or credential is no longer live
- [ ] The credential routes are served with the Operation names declared above: `CredentialChallenge`, `CredentialToken`, `CredentialAttest`, `CredentialList` and `CredentialRevoke`
- [ ] `POST /v1/admin/operators/{name}/key` is served as `OperatorKeyChange`, requires no bearer token, and keeps the operator's `identity_id` while revoking its credentials (`architecture/admin`, `operator-key-change`)
- [ ] `POST /v1/admin/hub/proof` is served as `HubProof` and requires no bearer token: a request carrying none reaches its handler, and is never answered `401` `valid token required` (`architecture/admin`, `hub-proof`)
- [ ] A token with `type` `attestation` is refused with `CREDENTIAL_REQUIRED` on every route but `CredentialAttest`, `GET /v1/audit` and `POST /v1/channel` included, and on `CredentialAttest` for any operator but its `sub`
- [ ] A token whose `type` is not `operator`, an agent token included, is refused with `CREDENTIAL_REQUIRED` on every `/v1/admin/*` route that requires a token, before the handler runs

- [ ] `POST /v1/register` verifies ML-DSA-65 signature and replay protection
- [ ] `POST /v1/register` enforces exclusive namespace ownership (409 on conflict)
- [ ] `POST /v1/register` rejects reserved namespace claims (403)
- [ ] `POST /v1/register` refuses a manifest naming any capability `protocol/types` marks person only — `content:write`, `content:decide`, `content:replicate`, `content:connect`, `content:declassify`, `model:attest` or `fabric:attest` — with 403 `CAPABILITY_PERSON_ONLY`, records no agent and issues no token
- [ ] A registration token carries `identity_id`, the fingerprint of `manifest.public_key`
- [ ] `POST /v1/register` validates subscription scopes (event:observe for "*")
- [ ] `POST /v1/register` returns `RegisterResponse` with agent ID, token, and service directory
- [ ] `DELETE /v1/register` releases owned namespaces and routing table entries
- [ ] Service directory includes `routing_table` and namespaces map
- [ ] A `ServiceEntry` carries the `pass_routes` its manifest declared, unchanged, and a registration whose `pass_routes` name `content:write` or another person-only capability is not refused for it, while one whose `capabilities` names one still is with `CAPABILITY_PERSON_ONLY`
- [ ] `POST /v1/register` refuses with 400 `INVALID_REQUEST`, recording nothing, a manifest with a pass route naming a capability `protocol/types` does not list, in `capabilities` or a body requirement, and one with two pass routes that can match one request, such as `GET /v1/x/{id}` and `GET /v1/x/special`
- [ ] A sixth request within a minute from one source to any one of the six administrative routes served without a token is refused before any signature is verified or made, the source being the `X-Forwarded-For` address only on a request from an address `orchestrator.admin_gateway_from` names, and the connection's address on every other, whatever `X-Forwarded-For` it carries (`auth-route-rate-limit`)
- [ ] Service directory broadcast to ALL agents after every registration/deregistration
- [ ] `POST /v1/register` refuses with `409 ADDRESS_CONFLICT` when the registered `url` contradicts the address the tenant declared for that component
- [ ] Every `ServiceEntry` carries `address_provenance`, and an entry the orchestrator has not matched against the tenant's declaration reports `self-asserted` rather than omitting the field
- [ ] `address_provenance` is never reported as `verified` on the strength of an unauthenticated `GET /v1/health` probe
- [ ] A `ChannelGrant` names a `target_url` only where the orchestrator would publish that address as `declared`
- [ ] A `ChannelGrant`'s capabilities are the intersection of the requester's and the target's registered manifest, and no wider on either side
- [ ] `POST /v1/channel` verifies `from_agent` matches token.sub
- [ ] `POST /v1/channel` requires agent:message capability (403 if missing)
- [ ] Channel tokens expire after configured TTL
- [ ] Auth middleware rejects unauthenticated requests on protected endpoints
- [ ] On a `/v1/admin/*` route, Auth Middleware refuses with `FORBIDDEN`, before any handler, an operator token whose role carries the route's capability but whose `cap` does not name it, and reads a token only from the `Authorization` header
- [ ] `GET /v1/health` returns 200 without auth with agent/domain/channel/namespace counts
- [ ] system.agent.registered event published after successful registration
- [ ] system.agent.deregistered event published after deregistration
- [ ] Every operation creates an `AuditEntry` logged to stderr and persisted to JSONL
- [ ] Domain dependency status recalculated on registration/deregistration
- [ ] Orchestrator does NOT handle tasks, strategies, context, observations, or approvals
- [ ] Administrative endpoints are gated on the capability each declares — an `admin:` capability, or `model:attest` — carried in the caller's token, not on a separate role model
- [ ] An admin's token whose `cap` names only `content:` capabilities is refused with `FORBIDDEN` at `OperatorApprove`, `OperatorRole`, `OperatorDelete`, `AdminAgentDeregister` and `CredentialRevoke`, its own credential included, and at `CredentialAttest` for the admin
- [ ] The orchestrator serves only the administrative endpoints backed by state it owns — operators, agents, its audit log, its own overview, and the tenant's model surface the CLI installs
- [ ] `GET /v1/admin/audit` and `GET /v1/admin/audit/export` answer a request that can use `admin:audit` and refuse any other with `FORBIDDEN`, an agent token with `CREDENTIAL_REQUIRED`; the export answers the entries the list would for the same filters, as JSON or CSV by `format`
- [ ] `/v1/admin/overview` reports only figures this orchestrator holds, and never reports a figure another component owns, as zero or otherwise
- [ ] `POST /v1/admin/complete` with no `scope` is refused with `SCOPE_MISSING`, one above the ceiling `GET /v1/admin/model/ceiling` reports for the backend and model it would run is refused with `SCOPE_CEILING_EXCEEDED`, and one at `restricted` is refused whatever the ceiling; none of them runs a backend
- [ ] `POST /v1/admin/model/agreements` and `DELETE /v1/admin/model/agreements/{id}` refuse a token without `model:attest` with `FORBIDDEN`, including one holding `admin:*`, and a service's or an agent's token with `CREDENTIAL_REQUIRED`
- [ ] A `PUT /v1/admin/model` on a token carrying `admin:*` and not `model:attest` that sets a name a current agreement lists, and changes anything of it but the model or held another name before, withdraws that agreement, names it in its answer, and `GET /v1/admin/model/ceiling` then answers that name `internal`
- [ ] A `PUT /v1/admin/model` that keeps a listed name and changes only its model to one the agreement does not list withdraws nothing, and `GET /v1/admin/model/ceiling` then answers `internal` for that name and model, so a `confidential` `POST /v1/admin/complete` is refused with `SCOPE_CEILING_EXCEEDED`; changing it back to a listed model answers the agreement's level again
- [ ] A recorded agreement's `recorded_by` is the token's `identity_id`, whatever the body says
- [ ] An agreement whose `level` is `restricted` is refused with `MODEL_AGREEMENT_LEVEL_REFUSED`, one whose `not_after` is 91 days ahead with `MODEL_AGREEMENT_LAPSE_INVALID`, one with no `models` with `INVALID_REQUEST`, and one listing a model at a backend a current agreement covers for that model with `MODEL_AGREEMENT_EXISTS`
- [ ] `GET /v1/admin/model/ceiling` answers `internal` for a backend no current agreement lists, for a model the agreement listing the backend does not list, and for a backend asked for no model, and `internal` again once the agreement that listed it lapses or is withdrawn
- [ ] Either ceiling route answers a `?backend=` name the tenant's model configuration does not name, such as an api-ai endpoint's `providers:` key, with `internal` and no `address` where no current agreement lists it, and with the agreement's level where one does, and never with `NOT_FOUND`
- [ ] `GET /v1/model/ceiling` answers a registered component's token with the `ProviderCeiling` `GET /v1/admin/model/ceiling` gives an operator for the same backend, `address` included where the backend has one, and refuses an attestation token with `CREDENTIAL_REQUIRED`
- [ ] Every platform-provided model route is authorised by the orchestrator's own judgement of the caller's token, and a `/v1/admin/*` one refuses an agent token with `CREDENTIAL_REQUIRED`
- [ ] `POST /v1/token/exchange` reads the caller's token from its `Authorization` header only: with no header it answers 401 whatever the body holds, and a body with no `subject_token` or no `audience` is refused with 400 `INVALID_REQUEST`
- [ ] `POST /v1/token/exchange` answers `issued: false` with `OPERATOR_REVOKED` for a token minted before its operator was removed, with `CREDENTIAL_REVOKED` after its credential was revoked, and with `TOKEN_EXPIRED` past its `exp`, each as a 200, and mints no pass
- [ ] `POST /v1/token/exchange` called with an operator token, a channel token, or the registration token of a component whose registration does not declare `token:exchange`, in its `Authorization` header, is refused with `FORBIDDEN`, with a pass with `PASS_AUDIENCE_MISMATCH` and a security event, and with an attestation token with `CREDENTIAL_REQUIRED`, and discloses nothing about `subject_token`
- [ ] `POST /v1/token/exchange` called with the registration token of a component that has since deregistered, or whose identity id `POST /v1/rotate-key` has since changed, is refused with `FORBIDDEN`
- [ ] `POST /v1/token/exchange` asked to exchange a pass, a registration token or a channel token answers `issued: false` with `CREDENTIAL_REQUIRED`, so a pass is never exchanged again
- [ ] `POST /v1/token/exchange` with an `audience` that is not the identity id of a component registered here now, or that is the caller's own, is refused with 404 `NOT_FOUND`, and mints nothing
- [ ] `POST /v1/token/exchange` asked for `scope` `[content:read]` on an admin's token answers with a pass whose `cap` is `[content:read]` alone, whose `aud` is the audience, whose `act` names the gateway, and whose `exp` is no more than 30 seconds after its `iat`; asked for `[content:decide]` on a `viewer`'s token, or on an admin's token minted with `cap` `[content:read]`, it answers `issued: false` with `FORBIDDEN`
- [ ] `POST /v1/token/exchange` asked for `scope` `[content:read, content:decide]` on a `viewer`'s token answers with a pass whose `cap` is `[content:read]` alone, and asked for `[admin:*]` on an `operator`'s token, whose role carries three of the four `admin:` capabilities, answers `issued: false` with `FORBIDDEN`
- [ ] An operator token whose `cap` is the empty list, as a `viewer` gets asking for `cap` `[fabric:attest]`, or that carries no `cap` claim, is refused with `FORBIDDEN` at every `/v1/admin/*` route Auth Middleware step 8 covers, and `POST /v1/token/exchange` answers it `issued: false` with `FORBIDDEN` for any `scope`
- [ ] Every exchange is audited, refused or not, with the person's identity id, the gateway's identity id, the audience and the scope, and `subject_token` is never kept or presented anywhere
- [ ] A pass presented at any route of the orchestrator is refused with `PASS_AUDIENCE_MISMATCH` and logged as a security event
- [ ] The orchestrator presents no token it received to any party: `GET /v1/admin/overview` asks no other component for a figure
- [ ] A token whose signature does not verify is refused with 401 `INVALID_SIGNATURE`, and one past `exp` with 401 `TOKEN_EXPIRED`, on every route Auth Middleware covers
