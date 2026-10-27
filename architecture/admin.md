<!-- blueprint
type: architecture
name: admin
version: 4.1.2
requires: [protocol/spec, protocol/identity, protocol/types, patterns/principal-identity, architecture/orchestrator, architecture/observability, patterns/logging, architecture/domain, architecture/gateway, architecture/client, architecture/threat-model]
platform: any
tier: free
-->
<!-- wl:ids complete -->

# Weblisk Platform Admin

The operational management layer for a Weblisk deployment. Defines
operator identity, operator roles, and the API surface through which
people monitor, manage, and interact with the orchestrator, agents,
domains, workflows, and federation peers. It serves no user interface
of its own: a person uses a client, the CLI or a console that holds
their credential.

This is the **platform admin** — it manages the Weblisk infrastructure
itself (orchestrator, agents, domains, federation, programmes). It is
completely separate from any admin features that applications built
on Weblisk may define for their own purposes.

Applications built on the framework may have their own admin portals
(e.g. a CMS content manager, an e-commerce product dashboard, a
customer support panel). Those are application-level features — they
run through the application gateway as normal routes with appropriate
ABAC policies. They have nothing to do with this blueprint.

Without a platform admin interface, the Weblisk system is a black
box. This blueprint turns it into an observable, manageable system
that operators can confidently run in production.

## Overview

The admin surface is the operator API the admin gateway composes from the
administrative groups
([The admin API is an aggregate](#the-admin-api-is-an-aggregate)): the
orchestrator's own, and each other provider's once its blueprint specifies
routes a pass may reach. A person reaches it through a client: the CLI
([`architecture/cli`](cli.md)), or a console that holds their credential
([A console holds a credential, never a token](#a-console-holds-a-credential-never-a-token)).
The admin gateway serves no console of its own.

The admin gateway is built from this blueprint, as the component kind `admin`,
with every tenant ([The Admin Gateway as a Component](#the-admin-gateway-as-a-component)).

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=3.0.0 <5.0.0"
    bindings:
      endpoints:
        # The admin gateway registers like any component, and serves the
        # seven agent endpoints on its own listener (admin-gateway-authorization):
        # describe, the two probes and services as protocol/spec says, the
        # last only as a prompt to read the directory, and execute, message
        # and event each refused with FORBIDDEN; and it renews its lease
        - path: /v1/register
          methods: [POST]
        - path: /v1/describe
          methods: [POST]
        - path: /livez
          methods: [GET]
        - path: /readyz
          methods: [GET]
        - path: /v1/lease
          methods: [POST]
        - path: /v1/services
          methods: [POST]
        - path: /v1/execute
          methods: [POST]
        - path: /v1/message
          methods: [POST]
        - path: /v1/event
          methods: [POST]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    # 2.2.0 is where step_up_at is set through a re-confirmation and
    # weblisk/step-up/v1 is registered
    version: ">=2.2.0 <4.0.0"
    bindings:
      types:
        - name: WLToken
          fields_used: [sub, iss, iat, exp, cap, cid, role, type, identity_id, record_keys, aud, act, step_up_at]
        - name: SigningKeyPair
          fields_used: [public_key, private_key]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/principal-identity
    # 1.9.0 is where an attestation's purpose may be step-up, naming rp_id
    # and origin
    version: ">=1.9.0 <2.0.0"
    bindings:
      types:
        - name: Attestation
          fields_used: [identity_id, identity_public_key, credential_public_key, hub_id, purpose, rp_id, origin, device_label, not_after, signature]
        - name: Credential
          fields_used: [credential_public_key, algorithm, form, device_bound, identity_id, attestation, status, last_used_at]
      behaviors:
        - name: credential-attestation
        - name: authentication
        - name: revocation
        # A sign-records credential is recorded, revoked and named in tokens
        # here, never mints one, and a console never holds one
        - name: record-signing
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    # 4.0.0 is where token:exchange, the one capability the gateway's
    # registration declares, is admitted for the tenant's declared admin
    # gateway alone; STEP_UP_REQUIRED, which Error Handling refuses a
    # destructive act with, exists from 3.1.0
    version: ">=4.0.0 <5.0.0"
    bindings:
      types:
        # The admin gateway serves the two probes and renews its lease
        # (protocol/types, Health and Presence)
        - name: Liveness
          fields_used: [live]
        - name: Readiness
          fields_used: [ready]
        - name: LeaseRenewal
          fields_used: [ready, checks, timestamp]
        # Every refusal Error Handling names, with the category and
        # retryable it gives each code: retry_after on ADMIN_TOKEN_UNCHECKED,
        # and detail.address on ADMIN_GROUP_UNAVAILABLE for a provider whose
        # only address is self-asserted on another host
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, retry_after, detail]
        # What the admin gateway asks the orchestrator for each request it
        # carries to a provider other than the orchestrator, and what it
        # sends that request on (admin-gateway-authorization)
        - name: TokenExchangeRequest
          fields_used: [subject_token, audience, scope]
        - name: TokenExchangeResponse
          fields_used: [issued, code, pass, capabilities]
        # Where a pass may go, to whom, and what it carries: the directory
        # entry's address and how the orchestrator came to hold it, its key,
        # and the routes it declares a person's request may reach
        - name: ServiceEntry
          fields_used: [name, url, public_key, address_provenance, pass_routes]
        - name: PassRoute
          fields_used: [method, path, capabilities, body]
        - name: BodyRequirement
          fields_used: [field, equals, capabilities]
        # The gateway's own manifest, which declares none of these routes
        - name: AgentManifest
          fields_used: [name, type, version, description, url, capabilities, public_key, publishes, subscriptions, pass_routes]
        # The operator lifecycle this document specifies, across a change of
        # identity key
        - name: Operator
          fields_used: [name, public_key, identity_id, retired_keys, role, status]
        - name: RetiredKey
          fields_used: [public_key, retired_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    # 3.0.0 is where the registry holds each agent's lease; the overview's
    # lease-state counts and the agents' lease_state, lease and
    # last_renewal are read from it, and a 2.x orchestrator holds none
    version: ">=3.0.0 <4.0.0"
    bindings:
      behaviors:
        # Called by the admin gateway for each request it carries to a
        # provider other than the orchestrator. See admin-gateway-authorization
        - name: token-exchange
          usage: Relied on, never served here. The admin gateway sends a request to a provider other than the orchestrator only on the pass it answers
      endpoints:
        # The orchestrator-provided groups only: every route under
        # /v1/admin/ that architecture/orchestrator's Administrative
        # endpoints lists but POST /v1/admin/model/audit, its model
        # gateway's alone, which the admin gateway forwards on the person's
        # own token (admin-gateway-authorization). Programme objectives,
        # decisions, workflows and federation would be bound from their own providers,
        # and none specifies its routes yet — see the gap under "The admin
        # API is an aggregate".
        - path: /v1/admin/operators
        - path: /v1/admin/credentials
        - path: /v1/admin/hub/proof
          methods: [POST]
        - path: /v1/admin/agents
        - path: /v1/admin/audit
          methods: [GET]
        - path: /v1/admin/model
        - path: /v1/admin/complete
          methods: [POST]
        - path: /v1/admin/overview
          methods: [GET]
        # Read by GET alone, at the gateway's anchor. POST /v1/services is an
        # endpoint each agent serves, bound above from protocol/spec
        - path: /v1/services
          methods: [GET]
        - path: /v1/token/exchange
          methods: [POST]
          request_type: TokenExchangeRequest
          response_fields: [issued, code, pass, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/observability
    version: ">=2.0.0 <3.0.0"
    bindings:
      behaviors:
        # The gateway carries each request's trace to the provider it
        # sends it to (Admin Gateway Request Lifecycle, step 7)
        - name: trace-propagation
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/logging
    version: ">=2.0.0 <3.0.0"
    bindings:
      behaviors:
        # Its logs, Confidential and kept apart from the application
        # gateway's (Implementation Notes), never hold a token or a pass
        - name: structured-logging
        - name: redaction-at-emission
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: DomainManifest
          fields_used: [name, type, workflows, required_agents]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: GatewayConfig
          fields_used: [routes, tls, rate_limits]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/client
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        - name: WLS
          fields_used: [sub, sid, roles, sec, mfa]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/threat-model
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ThreatBoundary
          fields_used: [boundary, controls, mitigations]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

The admin interface is a **separate listener** from the application gateway, with
its own TLS entry point and its own domain.

```
   A person's client (the CLI, a console)
         │  separate listener, separate TLS
         ▼
   ┌──────────────────────────┐
   │ ADMIN GATEWAY            │
   │  identity → MFA → role   │
   │  → step-up → audit       │
   └───────────┬──────────────┘
               │ reads the orchestrator's own endpoints
               ▼
   ┌──────────────────────────┐
   │ ORCHESTRATOR             │
   │ services · audit · leases│
   └──────────────────────────┘
```

**Responsibilities.** Operator identity lifecycle, multi-factor authentication
without exception, the role hierarchy, the step-up a destructive action needs
(`destructive-action-step-up`), and the audit trail of every operator action.

**Not responsibilities.** Serving end users — that is `architecture/gateway`, which
shares nothing with this listener. Executing tasks, which is the agents'. Deciding
policy, which is `patterns/policy`.

---

## Responsibilities

### Owns

- Admin gateway process (separate listener, TLS, and domain from application gateway)
- Operator identity lifecycle (registration, role assignment, suspension)
- Operator credentials: one per operator, client and hub, attested by the operator's identity, checked on every request
- Admin API endpoints under `/v1/admin/*`
- Operator token model (WLT with a one-hour TTL, minted with a credential, two factors required where each key is opened, behind the admin gateway's IP allowlist)
- Admin rate limiting and IP allowlist enforcement
- Step-up for destructive actions: the person's own re-confirmation, never a second person (`destructive-action-step-up`)
- The one decision inbox, composed from each owner's own decisions ([Decision Inbox](#decision-inbox))

### Does NOT Own

- Orchestrator internals (admin reads orchestrator state via API, does not manage it directly)
- Agent logic or agent lifecycle (admin can deregister, but agents self-govern)
- Application-level admin features (those use the application gateway)
- Client session management (owned by `architecture/client`)
- A user interface: a person uses the CLI or a console holding their credential
- Federation trust establishment (owned by `protocol/federation`; admin only approves/revokes)

---

## Endpoints

What the admin gateway serves, on its two listeners
([Two listeners](#two-listeners)). The admin listener carries people's
requests: what it does with each is `admin-gateway-authorization` and the
[Admin Gateway Request Lifecycle](#admin-gateway-request-lifecycle), and the
`Carry` rows are that rule for every route it does not answer itself. The
internal listener serves [`protocol/spec`](../protocol/spec.md#agent-endpoints)'s
agent endpoints to the orchestrator. The routes the gateway carries are their
providers' and are specified there: the orchestrator's under
[Admin Endpoints](#admin-endpoints), and any other in the blueprint whose
component declares it as a pass route.

| Method | Path | Operation | Listener | Auth | Purpose |
|--------|------|-----------|----------|------|---------|
| GET | /v1/admin/overview | Overview | admin | yes | The System overview, composed from the orchestrator's and reporting every other group unavailable |
| GET | /v1/admin/approvals | DecisionInbox | admin | carried | The decision inbox, answered `ADMIN_GROUP_UNAVAILABLE` while no pass route can name its group |
| POST | /v1/admin/model/audit | ModelAuditRefused | admin | none | Answered as `admin-gateway-authorization` says of this route |
| GET | /v1/* | CarryGet | admin | carried | Any other route, to its provider: the orchestrator on the operator token, another on a pass, or `ADMIN_GROUP_UNAVAILABLE` |
| POST | /v1/* | CarryPost | admin | carried | As `CarryGet` |
| PUT | /v1/* | CarryPut | admin | carried | As `CarryGet` |
| PATCH | /v1/* | CarryPatch | admin | carried | As `CarryGet` |
| DELETE | /v1/* | CarryDelete | admin | carried | As `CarryGet` |
| POST | /v1/describe | Describe | internal | no | The gateway's manifest |
| GET | /livez | Livez | internal | no | Liveness, for the supervisor that restarts it |
| GET | /readyz | Readyz | internal | no | Readiness, as [Registration, lease and identity](#registration-lease-and-identity) says |
| POST | /v1/services | ServicesPush | internal | no | A prompt to read the directory, as `admin-gateway-authorization` says |
| POST | /v1/execute | Execute | internal | no | Refused, as `admin-gateway-authorization` says |
| POST | /v1/message | Message | internal | no | As `Execute` |
| POST | /v1/event | Event | internal | no | As `Execute` |

`carried` is the provider's own requirement, judged by the orchestrator or by
the provider and never by the gateway. `/v1/*` names every path under `/v1/`
that no other row names, a prefix and not a literal `*`: Go's `ServeMux`
writes it `/v1/`, and the more specific rows win over it. A listener MUST NOT serve a row of the
other's. <!-- wl:id listeners-disjoint -->

The internal rows read `no` where [`architecture/agent`](agent.md#endpoints)'s
rows for the same endpoints read `yes`, and the two agree. An agent acts on a
request to `/v1/execute`, `/v1/message` or `/v1/event`, so it verifies the
sender first. The gateway acts on none of them: it refuses the first three
whoever sends them, and takes a push to `/v1/services` only as a prompt to
read the directory from its anchor on its own token, never as the directory
itself. No request to the internal listener changes what the gateway does,
so it has nothing to verify a sender for.

---

## Interfaces

The admin component's public API surface is defined in detail in
[Admin Endpoints](#admin-endpoints) (operator management, system overview,
agent management, domain/workflow management, programme objectives,
the decision inbox, federation management, audit) and
[Admin API Response Shapes](#admin-api-response-shapes).

---

## Error Handling

The operator and credential routes answer with these codes, in `ErrorResponse`
([`protocol/types`](../protocol/types.md#errorresponse)). A route another
component provides is answered by the admin gateway with
`ADMIN_TOKEN_UNCHECKED` where it could not have the person's token exchanged,
and with `ADMIN_GROUP_UNAVAILABLE` where no provider here may be sent it
(`admin-gateway-authorization`). Each says what the
client does next, so a client acts on the code and never on the message text.
Where the last column names a
[`patterns/principal-identity`](../patterns/principal-identity.md#error-handling)
code, this is its wire form at this surface, and that pattern holds the rule.

The codes the token exchange can refuse a person's token with are the ones
`TokenExchangeResponse.code` names
([`protocol/types`](../protocol/types.md#tokenexchangeresponse)): the eight
operator token codes — `CREDENTIAL_REQUIRED`, `OPERATOR_UNKNOWN`,
`OPERATOR_NOT_APPROVED`, `OPERATOR_REVOKED`, `CREDENTIAL_UNKNOWN`,
`CREDENTIAL_OPERATOR_MISMATCH`, `CREDENTIAL_REVOKED` and `CREDENTIAL_EXPIRED`
— and `INVALID_SIGNATURE`, `TOKEN_EXPIRED` and `FORBIDDEN`. Each is registered
with its HTTP status in [`protocol/types`](../protocol/types.md#errorresponse),
because the orchestrator answers them on its own routes and the admin gateway
answers them for every other provider, and the HTTP column here names that
registry for the eight it lists. `TOKEN_REQUEST_REPLAYED` is registered there
too, as a code a client of `POST /v1/admin/operators/token` acts on, and the
HTTP column names that registry for it as well. So is `STEP_UP_REQUIRED`,
which every component that serves a destructive act answers. An orchestrator
enters every code in its central error registry with its HTTP status, from
there for those thirteen and from here for the rest, which is what `architecture/orchestrator`'s
`error-codes-registered` check looks for. The Category column classes the
fault, as `architecture/content` and `architecture/fabric` do. It is not
`ErrorResponse.category`: there, each of these is `permanent` and not
`retryable`, because the client acts on the code rather than repeating the
request, except `ADMIN_TOKEN_UNCHECKED`, which is `transient` and `retryable`,
because nothing was judged.

| Code | HTTP | Category | When | Behaviour | principal-identity |
|---|---|---|---|---|---|
| `OPERATOR_BOOTSTRAP_REFUSED` | 403 | auth | A registration at a hub with no operator carried no bootstrap secret, or a wrong one | Refuse, write nothing, audit. The caller needs the secret the orchestrator emitted | — |
| `OPERATOR_UNKNOWN` | [types](../protocol/types.md#errorresponse) | auth | No operator of that name here: never registered, or lost with a hub regenerated without its records | Refuse. The client reports it and names the person's own registration (`weblisk operator register`), and never registers to answer it; retrying changes nothing | `identity_unknown` |
| `OPERATOR_NOT_APPROVED` | [types](../protocol/types.md#errorresponse) | auth | The operator is registered and pending | Refuse. Not a failure: the client reports that an admin must approve | — |
| `OPERATOR_REVOKED` | [types](../protocol/types.md#errorresponse) | auth | The operator was removed. A removed operator keeps its record with status `revoked` ([`protocol/types`](../protocol/types.md#operatorstatus)), so removal is never mistaken for a name the hub has not seen | Refuse. Every credential and token resting on it ended with it | — |
| `CREDENTIAL_REQUIRED` | [types](../protocol/types.md#errorresponse) | auth | A route that needs an operator token carrying a `cid` got something else: an operator token with no `cid`, an attestation token anywhere but the attestation route, or an agent or channel token on a `/v1/admin/*` route | Refuse. The client mints an operator token with a credential | — |
| `OPERATOR_SUBJECT_MISMATCH` | 403 | auth | The token's `sub` is not the operator the path names, on a route only that operator may use: an attestation token on another operator's attestation route, or a token without the admin role revoking another operator's credential | Refuse. Log an attestation token's attempt as a security event | — |
| `CREDENTIAL_UNKNOWN` | [types](../protocol/types.md#errorresponse) | auth | The hub holds no credential with this id | Refuse. The client attests a credential | `identity_unknown` |
| `CREDENTIAL_OPERATOR_MISMATCH` | [types](../protocol/types.md#errorresponse) | auth | The credential the token's `cid` names is held by an operator other than the token's `sub` | Refuse. Log as a security event: this hub never issues such a token | — |
| `CREDENTIAL_REVOKED` | [types](../protocol/types.md#errorresponse) | auth | The credential was revoked, by its operator, by an admin, with its operator, or by a change of identity key | Refuse at once, not at the token's expiry. The client attests a new key | `credential_revoked`, `token_credential_revoked` |
| `CREDENTIAL_EXPIRED` | [types](../protocol/types.md#errorresponse) | auth | The attestation's `not_after` has passed | Refuse. The client re-attests, which needs the identity | `attestation_expired` |
| `CREDENTIAL_CHALLENGE_INVALID` | 401 | auth | The nonce was not issued for this credential, was already used or has expired, or the signature does not verify | Refuse and spend the nonce. Log a signature failure as a security event | `replay_detected` |
| `CREDENTIAL_ATTESTATION_INVALID` | 400 | validation | The attestation's signature does not verify under ML-DSA-65 against the operator's recorded key, or the attestation names another identity key, or an `identity_id` that is not the operator's at this hub | Refuse. Log as a security event | `attestation_invalid`, `algorithm_not_permitted` |
| `CREDENTIAL_FORM_UNSUPPORTED` | 400 | validation | The credential key is not an ML-DSA-65 public key, the one form these routes carry, or, under `purpose` `step-up`, a passkey's COSE key ([Re-confirming for a destructive act](#re-confirming-for-a-destructive-act)) | Refuse. A form principal-identity permits beside them is admitted only by a route that declares its own registration and challenge | — |
| `TOKEN_REQUEST_REPLAYED` | [types](../protocol/types.md#errorresponse) | auth | An attestation-token request whose `jti` this hub has recorded for that operator inside the replay window: the same signed request seen again (`attestation-token-issuance`) | Refuse, issue no token, log as a security event. Not a reason to register and not a key mismatch: the client signs a new request with a fresh `jti` | `replay_detected` |
| `CREDENTIAL_FOREIGN_HUB` | 400 | validation | The `hub_id` an attestation, an attestation-token request or a key-change request names is not this hub's | Refuse. Log as a security event | `credential_foreign_hub` |
| `HUB_ADDRESS_FOREIGN` | 400 | validation | A hub proof was asked for an address that is not one of this hub's admin addresses (`hub-proof`) | Refuse and sign nothing. Log as a security event: a hub asked to name another hub's address is being relayed through | — |
| `HUB_PROOF_UNAVAILABLE` | 501 | io | A hub proof was asked before `weblisk/hub-proof/v1` has test vectors, or of a hub built before they were published (`hub-proof`) | Refuse and sign nothing, whatever the request carries. Not a refusal of the address: before the vectors the client records the registration answer's `hub_id` as it is given, and from then it treats the hub as one that does not answer the proof ([`architecture/cli`](cli.md#a-credential-for-each-hub)) | — |
| `CREDENTIAL_IS_IDENTITY_KEY` | 400 | validation | The credential's public key is the operator's identity key, current or retired | Refuse. Log as a security event | `identity_key_as_credential` |
| `CREDENTIAL_PURPOSE_REFUSED` | 400 | validation | The attestation names one purpose for a key this hub holds, or held, under another; or a challenge or token request names a sign-records or step-up credential, which never signs anybody in | Refuse. Log as a security event. The client attests a separate key for each purpose | `credential_purpose_mismatch` |
| `CREDENTIAL_LIFETIME_INVALID` | 400 | validation | `not_after` is not in the future, or is more than 90 days after the hub receives the attestation | Refuse, naming the cap | `attestation_expired`, where `not_after` has passed |
| `CREDENTIAL_PREVIOUSLY_REVOKED` | 409 | conflict | The key was revoked here before | Refuse permanently. Log as a security event | `credential_previously_revoked` |
| `CREDENTIAL_KEY_BOUND` | 409 | conflict | The credential key is, or was, a credential of another operator at this hub, or is another operator's identity key, current or retired | Refuse permanently, naming no operator. Log as a security event: an operator attested a key it can see in another's credential list | `credential_key_bound` |
| `OPERATOR_KEY_CHANGE_INVALID` | 401 | auth | A change of identity key whose `current_signature` does not verify under the operator's recorded key, whose `new_signature` does not verify under `new_public_key`, whose `new_public_key` is not an ML-DSA-65 key, or whose timestamp is outside the 300-second window or was seen before | Refuse and change nothing. Log as a security event | `replay_detected`, where the timestamp is the fault |
| `OPERATOR_KEY_REUSED` | 409 | conflict | A registration or a change of identity key offers a key this hub records, or recorded, as any operator's identity key, current or retired, or as any credential | Refuse permanently, naming no operator. The client generates a new key | — |
| `OPERATOR_LAST_ADMINISTRATOR` | 409 | conflict | A request to revoke would end the last active authenticate credential of the last active admin. A sign-records credential signs nobody in and a step-up credential only re-confirms, so neither is counted. A change of that admin's identity key is not refused | Refuse | `last_administrator` |
| `ADMIN_TOKEN_UNCHECKED` | 503 | io | A request for a route another component provides reached the admin gateway, and the orchestrator could not be asked to exchange its operator token, or answered anything but 200 with a `TokenExchangeResponse` or the `404` `NOT_FOUND` that says the provider is not registered now, which is `ADMIN_GROUP_UNAVAILABLE`; or the provider refused, with a `401` other than `STEP_UP_REQUIRED`, the pass the gateway sent it | Refuse and forward nothing more, with `retry_after` 5. The request may be repeated once the orchestrator answers. Never forward on the person's token, and never relay the code that answer or that refusal carried, which judged the gateway's own request or its pass, never the person's token | — |
| `STEP_UP_REQUIRED` | [types](../protocol/types.md#errorresponse) | auth | A destructive act arrived on an operator token or a pass whose `step_up_at` is absent or more than 300 seconds old (`destructive-action-step-up`) | Refuse, change nothing, audit. The answer carries RFC 9470's challenge and names the act in `detail.control`; the client has its person re-confirm, mints through that re-confirmation and retries once. The admin gateway returns it as the provider gave it | — |
| `ADMIN_GROUP_UNAVAILABLE` | 503 | io | A request reached the admin gateway for a route no provider here may be sent: none is deployed, the one deployed is not registered now, no directory entry declares the route among its `pass_routes` or more than one does, which is so wherever the provider's blueprint does not specify both the route and that it accepts a pass for it, or its directory address is on another host than the orchestrator's and only `self-asserted`, which the answer names in `detail.address` (`admin-gateway-authorization`) | Refuse and forward nothing. Never answer with an empty result: an absent provider and an empty one are different facts | — |

`TOKEN_EXPIRED` ([`protocol/types`](../protocol/types.md#error-handling)) still
answers a token past its `exp`. The client mints another with its credential,
which does not ask the identity.

---

## Data Flow

1. A person's client, the CLI or a console holding their credential, sends a
   request to the admin gateway (`admin.example.com:9443`)
2. Admin gateway runs IP allowlist check — reject if not allowed
3. TLS termination with admin-specific certificate
4. Rate limiting applied (per-operator read/write limits)
5. Operator token (WLT) extracted. It goes to the orchestrator and to no
   other component: with the request, for a group the orchestrator provides,
   or in a token exchange, for a route another component provides. Either way
   the orchestrator checks the operator, credential and grant it rests on live
   ([Every request checks what its token rests on](#every-request-checks-what-its-token-rests-on))
6. No factor is re-checked here: two were required where the credential was
   attested and where its key was opened to mint this token
   ([Where the second factor is](#where-the-second-factor-is))
7. Request forwarded to the provider of the route, with a `traceparent`
   header: to the orchestrator on the operator token as it arrived, and to any
   other provider on a pass the orchestrator exchanged that token for,
   addressed to that provider alone and carrying only the capabilities the
   provider's blueprint requires for that request, its body's included, never
   on the operator token. Answered `ADMIN_GROUP_UNAVAILABLE`
   where no provider here may be sent it, and `ADMIN_TOKEN_UNCHECKED` where the
   token could not be exchanged (`admin-gateway-authorization`)
8. Capability authorization, by the orchestrator's judgement whichever
   component provides the route: the request must be able to use every
   capability it requires — for a route the endpoint tables give a minimum,
   the capability that minimum stands for, and for any other provider's
   route, every capability its provider requires for that request, its
   body's included — never the token's role claim
   alone. The orchestrator judges it in its Auth Middleware when a request for
   its own group arrives, and at the exchange, before anything is forwarded,
   for any other provider, which acts on the pass's `cap` alone
   ([Admin Gateway Request Lifecycle](#admin-gateway-request-lifecycle), step 6)
9. The provider processes request and returns response
10. Admin gateway returns the response to the client (with `Cache-Control: no-store`)
11. A destructive act is admitted by the component that serves it only on a
    token or pass whose `step_up_at` is no more than 300 seconds old, and is
    otherwise refused `STEP_UP_REQUIRED` with RFC 9470's challenge, which the
    gateway returns as it came. No second person is asked
    (`destructive-action-step-up`)

---

## Admin Gateway Separation

The gateway as a running component, its listeners, addresses, registration
and certificate, is [The Admin Gateway as a Component](#the-admin-gateway-as-a-component).

The admin gateway is a **completely separate entry point** from the
application gateway. It is NOT an extension of the application
gateway. It is NOT served under the same domain. It does NOT share
session state, authentication flows, or network paths with the
application.

### Why Separate

The application gateway and admin gateway have fundamentally
different threat profiles:

| Concern | Application Gateway | Admin Gateway |
|---------|-------------------|---------------|
| Audience | End users (untrusted, high volume) | Operators (trusted, low volume) |
| Network | Public internet | Private network, VPN, or IP-restricted |
| Auth model | User credentials → session cookie | Operator credential, attested by the operator's ML-DSA-65 identity → operator token |
| Session binding | Device fingerprint + IP/24 | Operator credential + exact IP allowlist |
| MFA | Policy-driven (optional for standard routes) | Always required, no exceptions: at attestation and at every mint, never as a claim in a token |
| Rate limits | High (accommodate user traffic) | Low (operators don't generate burst traffic) |
| Compromise impact | User data exposure | Full system control |
| Domain | `app.example.com` | `admin.example.com` (or `admin.internal:9443`) |
| TLS cert | Public CA certificate | Private CA or separate public cert |

#### Separate access points, shared services

The table above is about **attack surface**, and only about attack surface. It
is not two authentication systems, and it MUST NOT become two. <!-- wl:id auth-not-duplicated -->

This blueprint requires [`architecture/gateway`](gateway.md), which requires
`patterns/auth-session`, `patterns/auth-token` and
`patterns/user-management`. OIDC, password verification, credential storage
and token minting are specified once and used by both. An
implementation MUST NOT write a second one of any of them for the admin path.
The admin path issues no session: it serves no console of its own, and a
person's client presents an operator token ([Admin Session Model](#admin-session-model)). <!-- wl:id auth-stack-shared -->

What is separate is the **exposure**: a distinct listener, a distinct domain and
a distinct certificate. That
separation exists so that capability reachable by an operator is not reachable
from a public surface at all — not authorised-and-refused, but absent. A
compromise of the application gateway reaches user data; it does not reach a
listener that is not bound to the public internet.

Stated because the two halves pull in opposite directions and a reader who sees
only one half does the wrong thing with it. Read as "these are different
systems", an implementation duplicates the auth stack and the two copies drift
on the thing that matters most. Read as "these are the same system", an
implementation serves both from one listener and the separation that motivated
the whole design is gone.

**Authorization is also not duplicated, and is also not shared.** The
application gateway evaluates ABAC over a tenant's users and a tenant's
resources. This gateway evaluates operator capabilities over the platform.
Different subjects, different resources, deliberately non-overlapping: a grant
held in a tenant MUST NOT project onto platform administration. Two models
because there are two authorization domains, not because there are two
implementations of one. <!-- wl:id tenant-grant-not-platform -->

### Architecture

```
┌──────────────────────────┐      ┌────────────────────────────┐
│  End-User Browser        │      │  A person's client           │
│  (app.example.com)       │      │  (CLI, console)              │
│                          │      │  VPN / IP allowlist only     │
│  Islands → HTTP → Cookie │      │  HTTPS → operator token (WLT)│
└────────────┬─────────────┘      └──────────────┬─────────────┘
             │                                    │
             ▼                                    ▼
┌────────────────────────┐      ┌──────────────────────────────┐
│  APPLICATION GATEWAY   │      │  ADMIN GATEWAY               │
│  Port 443              │      │  Port 9443 (or separate 443) │
│  Public internet       │      │  Private / IP-restricted     │
│  User sessions (WLS)   │      │  Operator tokens (WLT)       │
│  ABAC policies         │      │  Capabilities + MFA always   │
│  Data masking          │      │  Full audit trail            │
└────────────┬───────────┘      └──────────────┬───────────────┘
             │                                  │
             │     ┌────────────────────┐       │
             └────►│  ORCHESTRATOR +    │◄──────┘
                   │  AGENT NETWORK     │
                   └────────────────────┘
```

Critical rules:
- The application gateway has NO routes to admin endpoints.
- The admin gateway has NO routes to application endpoints.
- They share the same orchestrator and agent network, but enter
  through different doors with different keys.
- If the application gateway is compromised, the admin gateway is
  unreachable — different network path, different credentials.
- If the admin gateway is compromised, the application continues
  serving users — they are operationally independent.

### Admin Gateway Request Lifecycle

```
1. IP ALLOWLIST CHECK (before any processing)
   ├── Client IP in operator allowlist?
   ├── If not → 403 Forbidden (no response body, no hint)
   └── Log: blocked IP attempt with source address

2. TLS TERMINATION
   ├── Separate TLS certificate from application gateway
   ├── TLS 1.3 alone, hybrid ML-KEM key agreement offered (Certificate,
   │   under The Admin Gateway as a Component)
   └── Client certificate validation (optional, for mTLS deployments)

3. RATE LIMITING
   ├── Per-operator: 60 read/min, 20 write/min
   ├── Auth endpoints: 5/min (very restrictive) — the four routes that
   │   issue tokens, credentials/challenge included, since it answers
   │   anyone who names a credential and holds each nonce until it expires,
   │   operators/{name}/key, which verifies two ML-DSA-65 signatures
   │   for anyone who names an operator, and hub/proof, which signs for
   │   anyone who names an address (Rate Limiting, below)
   └── Export endpoints: 5/min

4. OPERATOR AUTHENTICATION
   ├── Skipped for the four routes that issue tokens, which carry none:
   │   operators/register, operators/token, credentials/challenge and
   │   credentials/token, for hub/proof, which a client asks before it
   │   holds anything here, and for operators/{name}/key, which the current
   │   and new identity keys sign. They pass to the orchestrator as they
   │   arrived
   ├── Extract token from Authorization: Bearer <WLT>
   ├── Verify WLT signature against orchestrator's public key
   ├── Verify token.type == "operator" — or, on
   │   POST /v1/admin/operators/{name}/credentials alone, "attestation"
   │   with sub equal to {name} (Auth Middleware, below)
   ├── Verify token expiry
   ├── The orchestrator checks the operator, the credential named by
   │   token.cid and the grant are live — its records, not the token's word:
   │   when the request reaches it, for a group it provides, and at the
   │   exchange of step 6, for a route another component provides
   └── Refused if any check fails, with the code that says which, at the
       status protocol/types registers for it

5. SECOND FACTOR (always required, never checked per request)
   ├── Required where each key is opened: at attestation, and at every
   │   mint (Where the second factor is). A token carries no claim of it,
   │   and the gateway looks for none
   └── A console's AAL2 session is opened with a one-time code or WebAuthn,
       never a code sent by SMS

6. CAPABILITY AUTHORIZATION (the orchestrator's judgement, never the
   gateway's own; admin-gateway-authorization is the rule)
   ├── The request must be able to use every capability it requires — on
   │   an administrative route, the one the endpoint's minimum stands for —
   │   each one the operator's role carries now and the token's cap names
   │   (Auth Middleware, below). token.role is the role at mint and
   │   ignores cap, so it is never the judgement
   ├── A group the orchestrator provides: its Auth Middleware judges the
   │   token when the request arrives
   ├── A route another component provides: the gateway has the orchestrator
   │   exchange the token for a pass addressed to that component, asking for
   │   every capability the provider's blueprint requires for that request,
   │   those its body calls for included, as the pass route the component's
   │   directory entry declares names them (POST /v1/token/exchange, on the
   │   gateway's own registration token). The gateway judges nothing itself
   └── Refused by the exchange → the code it names, FORBIDDEN for a person
       who may not use the capability, whatever the role; the exchange
       answering 404 NOT_FOUND, because the provider is not registered now
       → 503 ADMIN_GROUP_UNAVAILABLE; the orchestrator not answering, or
       answering anything else but a TokenExchangeResponse → 503
       ADMIN_TOKEN_UNCHECKED. Nothing is forwarded

7. REQUEST FORWARDING
   ├── To the provider of the route (The admin API is an aggregate): the
   │   orchestrator on the operator token as it arrived, any other provider
   │   on the pass of step 6 and never on the operator token. The gateway
   │   calls no provider on its own registration token
   ├── A route no provider here may be sent → 503 ADMIN_GROUP_UNAVAILABLE,
   │   and nothing is forwarded
   ├── POST /v1/admin/model/audit, the orchestrator's route for its model
   │   gateway alone → 404 NOT_FOUND, and nothing is forwarded or exchanged
   ├── Internal header: traceparent
   └── Response returned to the client

8. DESTRUCTIVE ACTION STEP-UP (destructive-action-step-up)
   ├── Judged by the component that serves the act, on the step_up_at the
   │   operator token or the pass carries, never by the gateway
   ├── Absent, or more than 300 seconds old → 401 STEP_UP_REQUIRED, with
   │   RFC 9470's challenge, which the gateway returns as it came
   ├── No second person. A tenant that wants one declares it
   │   (patterns/approval, multi-party). Not asked of an operator's change
   │   of its own identity key, which its two signatures authorise
   └── Every act audited, with operator, target and step_up_at, before
       it takes effect
```

### Admin Session Model

The admin surface keeps no session. A person's client presents an operator
token (WLT), with stricter controls than an application session (WLS):

| Property | Application Session (WLS) | Admin Session (WLT) |
|----------|--------------------------|---------------------|
| Token type | `WLS` (Weblisk Session) | `WLT` (Weblisk Token) |
| Signing key | Gateway's ML-DSA-65 key | Orchestrator's ML-DSA-65 key |
| TTL | 24 hours | 1 hour |
| Idle timeout | 1 hour | None at the hub, where nothing tells use from idle. A console ends a person's tokens when that person's session with it goes idle (`console-credential-use`) |
| IP binding | /24 subnet (allows roaming) | None in the token: a WLT carries no address, and a hub stores nothing it issues, so there is nothing to bind one to. The IP allowlist (step 1) is the network control |
| MFA | Optional per policy | Always required, at attestation and at every mint ([Where the second factor is](#where-the-second-factor-is)) |
| Step-up | The session's `sec` level ([`architecture/client`](client.md)) | `step_up_at`, set only on a token minted through a re-confirmation, and admitting a destructive act for 300 seconds (`destructive-action-step-up`) |
| Concurrent sessions | Up to 5 per user | One credential per operator per client, each minting its own tokens. Revoking a credential ends every token it minted, at the next request |
| Renewal | Silent sliding window | A new token minted with the credential; the identity is not asked |

### Admin Network Deployment Options

| Mode | Description | Security Level |
|------|------------|----------------|
| **VPN-only** | Admin gateway accessible only through VPN tunnel | Highest — gateway invisible to public internet |
| **IP allowlist** | Admin gateway on public IP but rejects all non-allowlisted sources | High — requires IP management |
| **mTLS** | Admin gateway requires client certificate in addition to operator token | Highest — two-factor at transport layer |
| **Private network** | Admin gateway on internal network only (10.x.x.x) | High — requires network access |

Production deployments SHOULD use VPN-only or mTLS. IP allowlist is
acceptable for small teams with stable IPs. Private network is
acceptable for single-host deployments.

## The Admin Gateway as a Component

Every tenant has an admin gateway, built from this blueprint as the component
kind `admin`. [`weblisk tenant create`](cli.md#weblisk-tenant-create-name)
builds and starts it with the orchestrator, and
[`weblisk component admin init`](cli.md#weblisk-component-name-init) builds it
into a tenant that has none. What it does is the
[Admin Gateway Request Lifecycle](#admin-gateway-request-lifecycle),
`admin-gateway-authorization` and `destructive-action-step-up`, and is not
restated here. This section says what makes it a running component: its
listeners, its addresses, its registration and its certificate. Its settings
are [`schemas/config`](../schemas/config.md#admin_gateway)'s.

### Two listeners

| Listener | Serves | Reached by | Settings |
|---|---|---|---|
| admin | the `admin` rows of [Endpoints](#endpoints) | people's clients: the CLI, a console | `admin_gateway.port` (9443), `tls_cert`, `tls_key`, `allowlist` |
| internal | the `internal` rows: [`protocol/spec`](../protocol/spec.md#agent-endpoints)'s agent endpoints | the orchestrator | `admin_gateway.internal_port` (9803), `internal_address` |

The admin listener MUST serve HTTPS alone and MUST refuse a request from an
address `admin_gateway.allowlist` does not name, as step 1 of the lifecycle
says. <!-- wl:id admin-listener-guarded --> The allowlist names addresses and
CIDR ranges. Absent, it names the loopback addresses `127.0.0.1` and `::1`;
empty, it admits no one. The internal listener is the `url` the gateway's
manifest names (`admin-gateway-authorization`), and only the orchestrator
needs to reach it. It binds the loopback address alone; where the orchestrator
runs on another host, it reaches the listener through a TLS terminator on the
gateway's host, at `admin_gateway.internal_address`.

### Addresses

| Address | What it is | Where it is set |
|---|---|---|
| Each origin the admin listener is reached at | Where a person's client connects, and the address the CLI records for the hub (`orchestrator_url`, [`architecture/cli`](cli.md#configuration)) | `orchestrator.admin_addresses`, for which the orchestrator signs a hub proof ([Proving the hub at an address](#proving-the-hub-at-an-address)). For a gateway it stands up, the CLI writes `https://localhost:<port>` |
| The internal listener's address | What the gateway registers as its manifest's `url` | `admin_gateway.internal_address`. Absent, `http://127.0.0.1:<internal_port>`, for an orchestrator on the gateway's own host; an orchestrator on another host needs it set ([`schemas/config`](../schemas/config.md#validation-rules), rule 22) |
| The orchestrator's address | Its anchor: where it registers, renews its lease and reads the directory | `admin_gateway.orchestrator`. Absent, the orchestrator on the gateway's own host at `orchestrator.port` |
| Where its requests reach the orchestrator from | The address the orchestrator trusts `X-Forwarded-For` from (`auth-route-rate-limit`) | `orchestrator.admin_gateway_from`, which a gateway whose allowlist admits only loopback leaves empty: every client then arrives from loopback, so counting each by its own address gains nothing, and listing loopback would let any process on that host name its own source |

### Registration, lease and identity

The gateway registers as `admin-gateway`, with the manifest
`admin-gateway-authorization` gives it, and renews its lease as every
registrant does ([`protocol/spec`](../protocol/spec.md#post-v1lease)). It is
ready, at `GET /readyz` and in each renewal, once its admin listener is bound
and it has read the directory from its anchor.

Its registration key is how a tenant says which registration is its admin
gateway. The command that stands the gateway up makes the key, on the
gateway's host, before the orchestrator first starts, keeps it at
`.weblisk/keys/admin-gateway.key`, and writes its fingerprint
([`protocol/identity`](../protocol/identity.md#key-fingerprint)) to
`orchestrator.admin_gateway_identity`. The key is still the gateway's own, as
[`protocol/identity`](../protocol/identity.md)'s trust model asks: it is made
where the gateway runs and leaves nowhere. It is made by the command and not
the process so that it can be declared before the orchestrator starts. The
orchestrator admits `token:exchange` for that registration alone
([`protocol/types`](../protocol/types.md#capability), the exchange
capability). The gateway MUST register with that key and no other.
<!-- wl:id gateway-registers-declared-key --> Changing the key is a change to
the tenant's declaration, made by a person: a new key, its fingerprint written
there, and the orchestrator and the gateway restarted. That is the only way it
changes: the orchestrator refuses the gateway's registration token at
`POST /v1/rotate-key` ([`architecture/orchestrator`](orchestrator.md#auth-middleware),
step 6), so the gateway cannot rotate its own key. The orchestrator reads
`orchestrator.admin_gateway_identity` when it starts, so a gateway that
`weblisk component admin init` adds to a running tenant is admitted once the
orchestrator is restarted, as after a change of key.

Whoever holds this key can register as the gateway and exchange a stolen
person's token for passes outside the gateway's network controls
([`architecture/threat-model`](threat-model.md#residual-risk-register)), and
whoever holds the TLS key below can answer as the gateway at its address. So
the command that writes either key MUST first make `.weblisk/keys/` mode 0700
and confirm that the tenant's `.gitignore` excludes it, writing or amending the
`.gitignore` as [`weblisk tenant create`](cli.md#weblisk-tenant-create-name)
does where it does not, and MUST write each key mode 0600; it refuses, writing
neither key, where it cannot set those modes, or where a key's path lies in
the tenant's tree and no entry of the tenant's `.gitignore` excludes it, which
it judges from that file and not by asking git, because a tenant need not be a
repository. That holds for `weblisk component admin init` into
a tenant made before it as for `create`, and for a key file named elsewhere by
`admin_gateway.tls_key`: one inside the tenant's tree must be ignored by git
([`schemas/config`](../schemas/config.md#validation-rules), rule 21). <!-- wl:id gateway-keys-kept -->

The gateway holds a key the operator supplies to the same mode. At start it
MUST refuse to run, naming the file, where its registration key, or the TLS
key `admin_gateway.tls_key` names or defaults to, can be read or written by an
account other than its owner: any group or other permission bit set.
<!-- wl:id gateway-refuses-open-key --> A key at
`/etc/weblisk/keys/admin.key` that any account on the host can read is a key
anyone on that host can answer as the gateway with.

### Certificate

This section is the one home of when a certificate is made. Where the
tenant's configuration sets `admin_gateway.tls_cert` and `tls_key`, the admin
listener serves that certificate as it is, and the CLI MUST NOT make, renew
or replace it or its key; a file either names that is missing is a fault the
gateway reports at start, never a prompt to make one. <!-- wl:id given-certificate-served --> Where the configuration
sets neither, so both take their defaults
([`schemas/config`](../schemas/config.md#admin_gateway)), the command that
stands the gateway up makes them, once, where they are absent. Where the
certificate is absent and the key is there, it makes the certificate from that
key, so the pin holds. Where the key is absent and the certificate is there, it
MUST refuse, naming the missing key, and make neither: a new key is a new pin,
and a key made in silence would fail every recorded pin as a pin that did not
match with nothing to say why. The operator who means a new key removes the
certificate too and gives each person the new pin, as below. <!-- wl:id lone-certificate-refused -->
What it makes:

- **The key** is a new ECDSA P-256 key at `.weblisk/keys/admin-gateway-tls.key`,
  kept as `gateway-keys-kept` says. It is never printed, copied or sent.
- **The certificate** is self-signed, names `localhost`, `127.0.0.1` and `::1`,
  is valid for a year, and is kept at `.weblisk/tls/admin-gateway.crt`, which
  holds nothing secret. [`weblisk server start`](cli.md#weblisk-server-start)
  makes a new one from the same key once fewer than 30 days remain, so the pin
  below still holds. It renews only this certificate, the one the CLI made.
- **The pin** is `sha256:` and the lowercase hexadecimal SHA-256 digest of the
  certificate's DER-encoded SubjectPublicKeyInfo. `weblisk tenant create`
  reports it as `tls_pin` beside the hub's `address`, and the CLI records it
  with that address. It reports and records the pin of an operator-supplied
  certificate too, computed the same way, so the registration `create` makes
  always records a pin, whichever the certificate is. A registration records
  none only where `weblisk operator register` made it without `--tls-pin`, at
  an address whose certificate the system's roots verify.

A pin read from the gateway's host is read from a certificate file, which
holds nothing secret but is what every later connection is verified against,
so its integrity is guarded as the keys' secrecy is. The command that makes
the certificate makes `.weblisk/tls/` mode 0755 and the certificate mode 0644.
A command that reads a pin from a certificate file, `weblisk tenant accept`
and `weblisk server provision` among them, MUST refuse, naming the file and
reading no pin, where that file or the directory holding it can be written by
an account other than its owner: any group or other write bit set.
<!-- wl:id pin-source-guarded --> A certificate anyone on the host could
replace is a pin anyone on the host could choose.

A client learns a pin from one of three places, each reached over something
other than the connection it is about to verify: `create`'s result; the
tenant's operator, who reads it from the certificate on the gateway's host
(`.weblisk/tls/admin-gateway.crt`, or the file `tls_cert` names); or a
registration the CLI already records for the address, which
[`weblisk operator connect`](cli.md#weblisk-operator-connect) and
[`weblisk operator register`](cli.md#weblisk-operator-register) report as
`tls_pin` beside the `address` where the registration records one. A console
that makes its own requests to the gateway, rather than through the CLI, is a
client like any other, verifying as `client-pins-gateway-key` below says.
What is its own is keeping: where the registration it was given records a
pin, it MUST keep that pin with the address it keeps, so that every later
connection to that address is verified against it; where the registration
records none, it records no pin of its own. <!-- wl:id console-keeps-pin -->

The listener MUST negotiate TLS 1.3 alone and offer the hybrid key agreement
X25519MLKEM768, preferring it. <!-- wl:id admin-listener-tls13 -->
A client MUST refuse an admin gateway address whose scheme is not `https`,
before it sends anything to it, at a loopback address too: an `http://`
address presents no certificate to verify, so a registration, an attestation
or a token sent to it goes in clear to whoever answers. A client that holds a pin for an address MUST refuse a certificate whose key
does not match it, and MUST NOT fall back to the system's roots, to skipping
verification, or to HTTP, at a loopback address too. It reports that refusal
as a pin that did not match, never as an address that did not answer: a key
other than the recorded one at a gateway's address is what an interception
looks like. A client that holds no pin refuses a certificate its roots do not
verify, and says where a pin comes from: `create`'s result, or the tenant's
operator, who reads it from the certificate on the gateway's host. It has no
recorded registration to name, the third place, because holding none is why
it holds no pin. It MUST NOT
print, offer or record the pin of the certificate it was just shown as one to
trust: that key arrived over the connection it could not verify, and taking
it is trusting the first key that answers. <!-- wl:id client-pins-gateway-key -->
A client holding a pin verifies the certificate's key against it, and neither
the certificate's names nor its dates: a pin already binds one key to one
address, and a key that must be replaced is replaced by giving a new pin, not
by waiting for a date. The CLI still renews the certificate it made, so that a
client that also checks dates, as most TLS libraries do by default, keeps
working.

A new pin is needed whenever the key behind the certificate changes: the TLS
key is replaced after a compromise, or an operator-supplied certificate is
renewed with a new key, as ACME clients do by default. Nothing re-pins on its
own, because a client that took a new key on the gateway's word would be
trusting the first key that answers. The operator makes the new key and
certificate, reads the new pin from the certificate on the gateway's host, and
gives it to each person, who records it with
`weblisk operator register --tls-pin`; until then every client refuses the
gateway as a pin that did not match. An operator who renews a certificate of
their own keeps its key, where their tooling allows, so the pin holds.

A pin, and not a certificate authority the tenant makes, because an
authority's key can sign for any name: its loss is every listener's, and a
client that trusts it trusts it for everything it signs. A pin trusts one key
at one address. The certificate's key is ECDSA and not ML-DSA because no TLS
implementation the platform blueprints build on accepts an ML-DSA certificate
yet. It authenticates the handshake as it happens; what a person may do is
authorised by their ML-DSA-65 token, and the ML-KEM key agreement protects
what an eavesdropper records today.

### A start, and a build's own run

The CLI starts the gateway as it starts every component
([A component starts with a clean environment](cli.md#a-component-starts-with-a-clean-environment)),
passing one port as `--port` and `WL_PORT`. That port is the internal
listener's, and overrides `admin_gateway.internal_port`: the internal
listener is where [`protocol/spec`](../protocol/spec.md#agent-endpoints)'s
probes are, so a start waits on it as it waits on any component's port. Where
`admin_gateway.internal_address` is absent, its default,
`http://127.0.0.1:<internal_port>`, follows the overriding `--port`, so the
`url` the gateway registers and the port it binds never disagree. The
admin listener's port is `admin_gateway.port` alone. <!-- wl:id gateway-port-is-internal -->

A build's own runs, its conformance and interoperability runs, start the
gateway from its tree alone with `WL_DEV=1`, with no orchestrator, and while
the tenant's own gateway may hold `admin_gateway.port`. In that run the
gateway MUST bind the admin listener to an unused loopback port rather than
`admin_gateway.port`, and where `admin_gateway.tls_cert` and `tls_key` are
unset and the default files are absent, MUST make a certificate and key for
that run alone, held in memory and never written, as the start environment's
`WL_DEV=1` holds no persistent store. It MUST print, before it serves, one
line `[dev] admin listener https://127.0.0.1:<port> tls_pin sha256:<hex>`,
where the run reads the admin listener's address and the pin it verifies that
listener against: the line reaches the run over the process's own output, not
over the connection it verifies. Its registration key is likewise made for the
run and never written, and with no orchestrator it reports not ready at
`/readyz`, never refusing to start. <!-- wl:id dev-run-admin-listener --> A
`WL_DEV=1` start never makes, renews or writes a file the
[Certificate](#certificate) section makes, and is never how a tenant's
gateway runs: a real start without its certificate is the fault that section
names.

## Design Principles

1. **Read-heavy, write-light** — Most admin interactions are
   observation: viewing agents, reading logs, monitoring workflows.
   Writes are limited to decisions, operator management and
   configuration.
2. **ML-DSA-65 operator identity, kept cold** — Operators are identified
   by the same ML-DSA-65 identity system as agents. At a hub the identity
   signs to register, to obtain the attestation token that lets it attest,
   to attest a credential, to change its own key and to re-confirm for a
   destructive act, and nothing else.
   Elsewhere it signs only the fixed-form statements
   [`protocol/identity`](../protocol/identity.md#fixed-form-statements)
   registers for an identity. Tokens, with admin-scoped capabilities, are
   minted with the credential.
3. **Non-destructive defaults** — A destructive action needs the
   person's own re-confirmation within the last 300 seconds, never a
   second person, and is logged in the audit trail before it takes
   effect (`destructive-action-step-up`).
4. **Complete isolation** — The platform admin gateway shares no
   network path, no session state, and no authentication flow with
   the application gateway. Application-specific admin features
   built by customers are unrelated — they use the application
   gateway like any other route.

---

## Contracts

The operator flows are declared as behaviours, because what an implementation
must get right about them is a **sequence and a signing input**, not a field
list. A component that serves the operator surface binds these — see
`architecture/orchestrator`, which serves them and until now bound nothing from
this blueprint at all.

```yaml
contracts:
  behaviors:
    - name: operator-registration
      description: Establish an operator record from a signed request
      required: true
      rules:
        # <!-- wl:id registration-fields -->
        - The request MUST carry name, public_key, role, timestamp and signature
        # <!-- wl:id registration-verifies-submitted-key -->
        - The signature MUST be verified against the SUBMITTED public key before any record is written
        # <!-- wl:id registration-identity-id -->
        - The record MUST carry identity_id, the fingerprint (protocol/identity) of the submitted public_key, which no later change alters (Operator Identity)
        # <!-- wl:id registration-repeat -->
        - A request whose name is an operator's and whose public_key is that operator's current identity key is a repeat of its registration. Once its signature verifies it MUST be answered 200 with hub_id and identity_id alone, carrying no record, role, status or token, whatever the operator's status, revoked included, and changing nothing. It is how a client that registered from another device records this hub's hub_id (attestation-token-issuance), and the operator's status is told only to a request signed for this hub. A registration names no hub, so another hub can relay one here, and a repeat tells it that this name and key are an operator's here, as a 409 to the same request always did, with those two identifiers and nothing else (The identity signs only to attest, the gap there)
        # <!-- wl:id registration-name-held -->
        - Any other request whose name is already held MUST be refused with 409 and the existing record left untouched
        # <!-- wl:id registration-key-reused -->
        - Any other request whose public_key this hub records, or recorded, as any operator's identity key, current or retired, or as any credential MUST be refused with OPERATOR_KEY_REUSED, so no two operators share an identity id
        # <!-- wl:id registration-answer -->
        - Every other answer that is not a refusal MUST carry the operator's record, its status, hub_id and its identity_id, a pending registration's included, and a token only where registration also approved the operator (first-operator-claim)
        # <!-- wl:id registration-replay -->
        - The timestamp MUST be inside the replay window, and the message MUST be refused on replay
        # <!-- wl:id registration-audited -->
        - Registration MUST be audited whether it succeeds or is refused

    - name: registration-signing-input
      description: What an operator signs when registering
      required: true
      rules:
        # <!-- wl:id registration-signed-payload -->
        - The signed payload MUST be canonicalize({name, public_key, role, timestamp}) per RFC 8785
        # <!-- wl:id registration-payload-distinct -->
        - It MUST NOT be the {hub_id, jti, name, timestamp} payload the attestation-token request signs (attestation-token-issuance). Their key sets differ - only a registration's carries public_key and role, only a token request's hub_id and jti, and each side refuses a request missing its own - so a signature over one is never accepted as the other
        # <!-- wl:id registration-signs-key -->
        - The public key MUST be inside the signature, so a key cannot be substituted in flight
        # <!-- wl:id registration-signs-role -->
        - The role MUST be inside the signature, because it is a privilege claim
        # <!-- wl:id registration-timestamp-signed -->
        - The timestamp sent MUST be the timestamp signed — a second clock read produces a signature over a payload the server never sees

    - name: first-operator-claim
      description: How the first operator of a hub is admitted — by a secret, never by arriving first
      required: true
      rules:
        # <!-- wl:id bootstrap-secret-generated -->
        - An orchestrator whose operator store is empty MUST generate a bootstrap secret of at least 256 bits from a cryptographically secure random source, and emit it once, where only whoever started the orchestrator can read it
        # <!-- wl:id bootstrap-secret-written -->
        - It MUST write the secret to .weblisk/bootstrap, readable only by the user the orchestrator runs as, and MAY show it on a terminal only when its standard error is one. It MUST NOT write the secret to a log file, a system journal, or any output stream that is not a terminal, because an orchestrator started detached or by a boot unit has its output captured where others can read it, and kept after the secret is claimed
        # <!-- wl:id bootstrap-secret-never-shown -->
        - The bootstrap secret MUST NOT appear in an audit entry or in any response
        # <!-- wl:id bootstrap-secret-presented -->
        - A registration at a hub whose operator store is empty MUST carry the bootstrap secret as bootstrap_secret, and the orchestrator MUST compare it in constant time
        # <!-- wl:id bootstrap-refused -->
        - A registration there with no bootstrap secret, or a wrong one, MUST be refused with OPERATOR_BOOTSTRAP_REFUSED, write no record, and be audited
        # <!-- wl:id bootstrap-claims-admin -->
        - The registration that presents the secret MUST be approved with the admin role, whatever role it asked for
        # <!-- wl:id bootstrap-answer -->
        - Its response MUST carry an attestation token, hub_id and the operator's identity_id, and never an operator token. The first operator obtains operator tokens the way every operator does, with a credential
        # <!-- wl:id bootstrap-secret-destroyed -->
        - The secret MUST be destroyed when it is claimed, and MUST NOT be issued again while the operator store holds any record. The bootstrap reset in protocol/identity is the one way back
        # <!-- wl:id bootstrap-claim-atomic -->
        - The claim MUST be atomic. Of registrations that present the secret concurrently, exactly one is approved, and every other is refused with OPERATOR_BOOTSTRAP_REFUSED
        # <!-- wl:id bootstrap-secret-replaced -->
        - An orchestrator that restarts while its operator store is still empty MUST generate a new secret and emit it in place of the last, so a secret read from an earlier start admits nothing
        # <!-- wl:id later-registration-needs-admin -->
        - Every later registration MUST require an existing admin and MUST NOT return a token
        # <!-- wl:id bootstrap-refusals-distinct -->
        - A refusal for want of an admin MUST be distinguishable from a refusal for a bad signature, and from a refusal for a missing or wrong bootstrap secret
        # <!-- wl:id bootstrap-refusal-named -->
        - The response MUST state which case occurred, so a caller does not wait for an approval nobody needs to give

    - name: operator-approval
      description: How an operator after the first is admitted
      required: true
      rules:
        # <!-- wl:id approve-route -->
        - The route `POST /v1/admin/operators/{name}/approve` MUST exist — without it a registration that is not the first can never be completed by anybody
        # <!-- wl:id approve-admin-only -->
        - It MUST require the `admin` role, because it grants authority
        # <!-- wl:id operators-list-pending-rule -->
        - The list at `GET /v1/admin/operators` MUST report every operator including `pending` ones, so an admin can see who is waiting
        # <!-- wl:id approve-idempotent-rule -->
        - Approving an operator already `approved` MUST succeed and change nothing, so a retried approval is not an error
        # <!-- wl:id approve-no-token -->
        - Approval MUST NOT return a token — the approved operator attests a credential of their own and mints tokens with it
        # <!-- wl:id approve-audited -->
        - Approval MUST be audited with the name of the operator who granted it
        # <!-- wl:id operator-is-person -->
        - An operator is a person (protocol/types, Operator). An admin approving a registration vouches that its subject is one, and a service MUST NOT be approved as an operator; a service reaches a hub as a registered component (protocol/spec, POST /v1/register)

    - name: attestation-token-issuance
      description: What an operator's identity signature obtains — the right to attest, and nothing else
      required: true
      rules:
        # <!-- wl:id attestation-route-no-token -->
        - The route `POST /v1/admin/operators/token` MUST require no bearer token
        # <!-- wl:id attestation-request-signed -->
        - The request MUST carry hub_id, jti, name, timestamp and signature, and the signed payload MUST be canonicalize({hub_id, jti, name, timestamp}), verified against the STORED public key for that operator, with the timestamp inside the 300-second replay window. hub_id is the one the client recorded for this hub from a registration answer (operator-registration). A request without jti MUST be refused with INVALID_REQUEST before any signature is checked
        # <!-- wl:id attestation-jti-form -->
        - jti MUST be base64url text without padding (RFC 4648 section 5) that decodes to between 16 and 64 bytes. A client MUST draw it from a cryptographically secure random source, at least 128 bits, for each request alone, and MUST NOT send a jti it has sent before, a retry of an unanswered request included - a retry is a new request. A hub MUST refuse a request whose jti is present and is not that form with INVALID_REQUEST before any signature is checked, as it refuses one with no jti. So two requests from one identity never sign the same bytes, however close together, even where the identity signs deterministically, which a secret source may (protocol/secret-source)
        # <!-- wl:id attestation-replay -->
        - The request MUST be refused on replay. Once its signature has verified, the hub MUST record the operator's identity_id with the jti until the request's timestamp is outside the replay window, and a request whose jti is recorded for that operator MUST be refused with TOKEN_REQUEST_REPLAYED, issue no token and be logged as a security event. The check and the record MUST be one atomic step, so of concurrent requests carrying one jti exactly one proceeds. The record MUST survive a restart of the orchestrator and be shared by every instance that answers for this hub, so a replay inside the window is refused wherever and whenever it arrives at this hub. Where the record cannot be read or written, the request MUST be refused with STORAGE_ERROR, which protocol/types registers as transient, and no token issued, so a hub that cannot check a jti never answers as though it had. A record is written only for a request whose signature verifies under a stored operator key, and every such request is held to auth-route-rate-limit, so one source can make the hub hold at most the jtis of 5 requests a minute for as long as each record lives - at most 600 seconds, a timestamp 300 seconds ahead of the hub's clock plus the window - which is 50 records per source; an operator's records are bounded by the sources that operator's key signs from, and an orchestrator MAY further limit token requests per operator. Replay is keyed on the jti, never on the signature's bytes, so a signature that differs over the same payload is refused as well. A record is written for every request whose signature verifies, whatever it is then answered, and only for those, so a request nobody signed cannot use up an operator's jti. The jti is checked and recorded once the signature verifies and before hub_id and the operator's status are judged, so a replay of a request this hub has recorded is answered TOKEN_REQUEST_REPLAYED by this hub, whatever it first answered, CREDENTIAL_FOREIGN_HUB, OPERATOR_NOT_APPROVED and OPERATOR_REVOKED included. The record is this hub's alone. A request refused here with CREDENTIAL_FOREIGN_HUB names another hub's hub_id, and that hub has no record of it, so the jti does not protect against relaying it there inside the window - that relay is the case the hub_id rule and hub-proof answer, not this one. A TOKEN_REQUEST_REPLAYED answer is never a reason for a client to register, since another request from the same identity was answered first
        # <!-- wl:id attestation-foreign-hub -->
        - A request whose signature verifies over a hub_id other than this hub's MUST be refused with CREDENTIAL_FOREIGN_HUB and logged as a security event - the identity signed it for another hub, and it was relayed here
        # <!-- wl:id attestation-client-hub-id -->
        - A client MUST send this request only to a hub whose hub_id it has recorded, signing that hub_id, and MUST NOT sign a payload that names no hub for any hub, so neither an attestation token nor the deprecated operator token below is obtained with a signature good at every hub. That hub_id is the one a registration answer named, and which hub gave that answer only hub-proof settles, so until hub-proof has test vectors a hub that relays a first registration can have a client record another hub's hub_id at its address (The identity signs only to attest, the gap there). Where a client has recorded none for a hub, the person registers there first, by their own act (`weblisk operator register`), which a hub that already knows the operator answers as a repeat; a client never registers on its own initiative (architecture/cli, One approval vouches for every hub)
        # <!-- wl:id attestation-status-after-signature -->
        - An operator with no record MUST be refused with OPERATOR_UNKNOWN, since there is no stored key to verify against. Only once the signature has verified may the hub disclose the operator's status - a signature that does not verify MUST be refused with INVALID_SIGNATURE whatever that status is, and then a pending operator with OPERATOR_NOT_APPROVED and a revoked one with OPERATOR_REVOKED. Each refusal MUST be audited
        # <!-- wl:id attestation-token-form -->
        - The token it issues MUST have type attestation, carry no capability and no cid, and expire within 300 seconds
        # <!-- wl:id attestation-token-scope -->
        - An attestation token MUST be accepted by `POST /v1/admin/operators/{name}/credentials` for its own subject, refused there for any other operator with OPERATOR_SUBJECT_MISMATCH, and refused by every other route with CREDENTIAL_REQUIRED
        # <!-- wl:id attestation-answer-ids -->
        - The response MUST carry hub_id and the operator's identity_id at this hub, so the client can name this hub and this operator in the attestation it is about to have signed. The attestation a client submits MUST name the identity_id this answer carries, and a client MUST never compute it from the identity key - a hub keeps it across a change of identity key, so after one it is not the current key's fingerprint. A client that built the attestation beforehand, from the identity_id its registration answer named, submits it only where the two agree
        - It is the way to a first credential, and is deprecated as a way to an operator token. A hub built before the credential routes issues an operator token here, and a client MAY use one only from a hub that answers the credential routes with 404 or 405

    - name: hub-proof
      description: How a hub shows that it holds the key its hub_id names, at an address a client reached it at
      required: true
      rules:
        # <!-- wl:id hub-proof-route -->
        - The route `POST /v1/admin/hub/proof` MUST require no bearer token. Once weblisk/hub-proof/v1 has test vectors (the last rule), it MUST take address and challenge, and answer 200 with hub_id, public_key, address and signature
        # <!-- wl:id hub-proof-address-form -->
        - The address MUST be an origin in the ASCII serialisation of RFC 6454 section 6.2 - the scheme, "://", the host in lowercase, and ":" and the port only where the port is not the scheme's default, with no path, query, fragment or trailing "/" - and the challenge MUST be base64url text without padding (RFC 4648 section 5) that decodes to between 16 and 64 bytes. Once those vectors are published, any other request MUST be refused with 400 INVALID_REQUEST, signing nothing
        # <!-- wl:id hub-proof-admin-addresses -->
        - The orchestrator MUST sign only an address that is, byte for byte, one of its admin addresses, the origins its admin gateway is reached at, which the hub's configuration lists (schemas/config, orchestrator.admin_addresses). It MUST NOT take an address from the request's Host header, from a forwarding header or from the connection, all of which a hub that relays the request controls. Once those vectors are published, any other address MUST be refused with HUB_ADDRESS_FOREIGN, signing nothing, and logged as a security event
        # <!-- wl:id hub-proof-statement -->
        - The signature MUST be the fixed-form statement weblisk/hub-proof/v1 (protocol/identity, Fixed-Form Statements) whose fields are this hub's hub_id as 64 lowercase hexadecimal characters, the address, and the challenge as the text it arrived, built by the orchestrator itself and never from bytes a caller supplies, and made by the private key whose fingerprint is hub_id. public_key MUST be that key's public half
        # <!-- wl:id hub-proof-key-kept -->
        - The orchestrator MUST keep the private key its hub_id names for as long as it keeps that hub_id, protected as a service key (protocol/identity, Key Categories). Once it signs tokens with another key, the first key, whose fingerprint is hub_id, MUST sign this statement and nothing else, so the proof survives a rotation as hub_id does
        # <!-- wl:id hub-proof-vectors-first -->
        - No implementation may sign it before this corpus publishes its test vectors (protocol/identity, Test vectors come before a signer). Until they are published, the route MUST answer every request 501 HUB_PROOF_UNAVAILABLE, signing nothing, so a client tells a hub that cannot prove yet from one that refused the address. Once they are published, a hub MUST answer this route, and a client MUST hold a hub_id at an address no registration names only where a proof it asked for there, on a challenge it made, verifies for the address it reached (architecture/cli, A credential for each hub)

    - name: operator-credential-attestation
      description: Bind a client's credential to an operator's identity at this hub
      required: true
      rules:
        # <!-- wl:id credentials-route-tokens -->
        - The route `POST /v1/admin/operators/{name}/credentials` MUST accept an attestation token or an operator token whose subject is the operator named in the path, and nothing else. A token for another operator is refused with OPERATOR_SUBJECT_MISMATCH, and any other kind of token with CREDENTIAL_REQUIRED. An operator token MUST also be able to use admin:read (token-status-on-use), or it is refused with FORBIDDEN
        # <!-- wl:id attestation-verifies-own-key -->
        - The attestation MUST verify under ML-DSA-65 against the public key in that operator's OWN record, and its identity_public_key MUST equal that key, or it is refused with CREDENTIAL_ATTESTATION_INVALID. Registration is how this surface records the key principal-identity takes from an invitation
        # <!-- wl:id attestation-names-identity -->
        - Its identity_id MUST be that operator's identity id at this hub (Operator Identity), which is the fingerprint of that key until the operator's first change of identity key and is kept across it, or it is refused with CREDENTIAL_ATTESTATION_INVALID. Its hub_id MUST be this hub's hub_id. A different hub_id MUST be refused with CREDENTIAL_FOREIGN_HUB and logged as a security event
        # <!-- wl:id attestation-key-form -->
        - Its credential_public_key MUST be an ML-DSA-65 public key, or, under purpose step-up alone, a passkey's COSE key, or it is refused with CREDENTIAL_FORM_UNSUPPORTED. These routes carry an ML-DSA-65 key-file credential, and a step-up passkey, and no other form. Any other form principal-identity permits beside them has its own registration and challenge, and a hub admits it only through a route that declares them
        # <!-- wl:id credential-not-identity-key -->
        - Its credential_public_key MUST NOT be the operator's identity public key, current or retired, or it is refused with CREDENTIAL_IS_IDENTITY_KEY and logged as a security event
        # <!-- wl:id attestation-purposes -->
        - Its purpose is authenticate, when it is absent, sign-records or step-up. A sign-records credential is recorded, capped, revoked and listed as any credential is, and never obtains a challenge or a token (operator-token-issuance). Its key signs records for this hub and signs nobody in (patterns/principal-identity, record-signing). A step-up credential is recorded, capped, revoked and listed the same way, never obtains a challenge or a token, is never counted by OPERATOR_LAST_ADMINISTRATOR, and does nothing but answer a step-up (operator-token-issuance). Its attestation MUST name rp_id and origin, the relying party and the origin of the console where the passkey was registered with user verification required, and an attestation naming them under any other purpose, or a step-up attestation naming neither, is refused with CREDENTIAL_ATTESTATION_INVALID
        # <!-- wl:id credential-one-purpose -->
        - A key this hub holds, or ever held, under one purpose MUST be refused under any other with CREDENTIAL_PURPOSE_REFUSED, and logged as a security event. One key serves one purpose, so the key a client signs in with is never one that signs a record
        # <!-- wl:id credential-lifetime -->
        - Its not_after MUST be in the future and no more than 90 days after the hub receives it, or it is refused with CREDENTIAL_LIFETIME_INVALID
        # <!-- wl:id credential-previously-revoked -->
        - A key that was ever revoked at this hub MUST be refused with CREDENTIAL_PREVIOUSLY_REVOKED
        # <!-- wl:id credential-key-bound -->
        - A credential_public_key this hub holds, or ever held, as a credential of another operator, or that is another operator's identity key, current or retired, MUST be refused with CREDENTIAL_KEY_BOUND and logged as a security event. A credential's id is its key's fingerprint, so accepting it would rebind that credential, and every token minted with it, to the operator who attested it. A key is bound to the first operator this hub recorded it for, and to no other, ever
        # <!-- wl:id credential-reattest -->
        - An attestation for a key the same operator already holds as an active credential MUST replace that credential's attestation and keep its id. That is re-attestation
        # <!-- wl:id credential-stored-form -->
        - The hub MUST store the credential with algorithm ml-dsa-65, form key-file, device_bound false (a key file can be copied, and no authenticator says otherwise) and status active, or, for a step-up passkey, with the algorithm its COSE key names (es256 for -7, eddsa for -8, and any other refused with CREDENTIAL_FORM_UNSUPPORTED), form passkey and device_bound false, since the hub saw no registration ceremony, and return it with its id, the fingerprint of its public key
        # <!-- wl:id credential-attestation-audited -->
        - Every attestation MUST be audited with the operator, the credential id, its purpose and the device_label

    - name: operator-token-issuance
      description: Issue an operator token to a live credential — the ordinary way, and the only way to one
      required: true
      rules:
        # <!-- wl:id credential-routes-no-token -->
        - The routes `POST /v1/admin/credentials/challenge` and `POST /v1/admin/credentials/token` MUST require no bearer token — they are what issue them
        # <!-- wl:id challenge-refusals -->
        - A challenge for a cid this hub holds no credential for MUST be refused with CREDENTIAL_UNKNOWN, and one for a sign-records credential with CREDENTIAL_PURPOSE_REFUSED, before any nonce is issued. Its purpose is not a secret its key protects, and a key that signs records never signs a proof of a session. For any authenticate credential it does hold, whatever its status, it MUST answer with a nonce of at least 128 bits from a cryptographically secure random source, single-use, bound to that cid, expiring within 300 seconds, and this hub's hub_id
        # <!-- wl:id credential-answer-bytes -->
        - The token request MUST carry cid, nonce and signature, and the signature MUST verify under the credential's STORED algorithm and public key over exactly these bytes, and never over the nonce alone. The UTF-8 bytes of weblisk/credential-auth/v1, one 0x00 byte, the 64 lowercase hexadecimal characters of hub_id as ASCII, one 0x00 byte, and the nonce's base64url text exactly as the challenge returned it, as ASCII. The nonce is signed as text, never as the bytes it decodes to
        # <!-- wl:id nonce-spent -->
        - The nonce MUST be one this hub issued for that cid, unexpired and unused, and the attempt MUST spend it whether or not the signature verifies. Otherwise CREDENTIAL_CHALLENGE_INVALID
        # <!-- wl:id token-request-unknown-cid -->
        - A token request naming a cid this hub holds no credential for MUST be refused with CREDENTIAL_UNKNOWN, and one naming a sign-records credential with CREDENTIAL_PURPOSE_REFUSED
        # <!-- wl:id credential-status-after-signature -->
        - Only once the signature has verified may the hub disclose the credential's status or its operator's. The credential MUST be active (else CREDENTIAL_REVOKED) and its attestation's not_after in the future (else CREDENTIAL_EXPIRED), and its operator MUST be approved (else OPERATOR_NOT_APPROVED, or OPERATOR_REVOKED for a removed one)
        - The token request MAY carry cap, a list of capability names. The token then carries each capability the operator's role carries that cap names, and no other. A name the role does not carry is left out, never refused, so cap only ever narrows a token, and a cap that names nothing the role carries gives a token whose cap is empty. With no cap in the request, the token carries every capability the role carries
        # <!-- wl:id admin-wildcard-by-name -->
        - admin:* MUST be read as each capability in the admin family by name, both in a role and in cap. A role carrying admin:* carries admin:read, admin:approve, admin:strategy and admin:audit, so cap [admin:read] gives an admin a token carrying admin:read; and cap [admin:*] names each of them, so a role carrying only some capabilities of the admin family keeps those. A token carries admin:* itself only where the role carries it and the request's cap names it or the request carries none
        # <!-- wl:id operator-token-claims -->
        - The token MUST have type operator, carry cid, the identity_id of the credential cid names, the operator's role and the capabilities that role carries, narrowed by cap where the request carries one, and record_keys naming every sign-records credential the operator holds here that is active and whose attestation's not_after is in the future, and expire one hour after issue and never after the attestation's not_after
        # <!-- wl:id operator-token-cap-always -->
        - An operator token MUST carry its cap claim always, an empty list included. Its cap is the most it may use, so a verifier MUST read an operator token whose cap is absent or empty as naming no capability, never as carrying its role's full set. A serialiser that leaves an empty list out therefore narrows nothing away - the token it sends reaches no route that requires a capability (protocol/identity)
        # <!-- wl:id role-from-record -->
        - Role and capabilities MUST come from the stored record, never from the request
        # <!-- wl:id token-answer-not-after -->
        - The response MUST carry the attestation's not_after, so the client can warn before it passes
        # <!-- wl:id credential-last-used -->
        - The credential's last_used_at MUST be updated
        # <!-- wl:id client-signs-credential-hub-id -->
        - A client MUST sign with the hub_id its credential was attested for, and MUST treat a challenge that answers a different hub_id as a hub it holds no credential for
        # <!-- wl:id step-up-request -->
        - The token request MAY carry step_up, the person's re-confirmation for a destructive act - control, the act that asked as a STEP_UP_REQUIRED refusal's detail.control names it, non-empty ASCII with no 0x00 byte; form, identity or passkey; and that form's proof - over these bytes. The UTF-8 bytes of weblisk/step-up/v1, one 0x00 byte, the 64 lowercase hexadecimal characters of hub_id as ASCII, one 0x00 byte, the nonce's base64url text exactly as the challenge returned it, one 0x00 byte, and control (protocol/identity, Fixed-Form Statements). The nonce is the one the same request's credential signature spends, so a step-up is never made without a live credential and is never presented twice
        # <!-- wl:id step-up-identity-form -->
        - Under form identity, step_up carries signature, the operator's identity signature over those bytes, which MUST verify under ML-DSA-65 against the identity public key in the operator's OWN record. It is the form the CLI uses, and always available
        # <!-- wl:id step-up-passkey-form -->
        - Under form passkey, step_up carries credential, the id of an active, unexpired step-up credential of the same operator (operator-credential-attestation), and authenticator_data, client_data_json and signature, a WebAuthn assertion, each base64url. The hub MUST check that client_data_json's type is webauthn.get, its challenge is the base64url without padding of those bytes, and its origin is the origin that credential's attestation names; that authenticator_data's rpIdHash is the SHA-256 of the attestation's rp_id and both its user-present and user-verified flags are set; and that signature verifies, under the credential's stored key and algorithm, over authenticator_data followed by the SHA-256 of client_data_json as sent
        # <!-- wl:id step-up-refused -->
        - The credential's own answer is judged first, as on any token request. A step_up that then fails any check above, or names another form, MUST be refused with INVALID_SIGNATURE, issue no token and be logged as a security event; the nonce is spent either way
        # <!-- wl:id step-up-sets-claim -->
        - A token minted on a request whose step_up verifies MUST carry step_up_at, its time of issue (protocol/identity), and a token minted on any other request MUST NOT. Nothing else sets it: not a token's age, and not a credential's answer alone, however recent, which a keychain gives without asking anybody, so a silent renewal is never a step-up. Such a mint MUST be audited with its control, its form and, under form passkey, the step-up credential's id

    - name: token-status-on-use
      description: Every request re-checks what its token rests on
      required: true
      rules:
        # <!-- wl:id status-checked-on-use -->
        - On every request bearing an operator token, the orchestrator MUST look up the operator named by sub and the credential named by cid in its OWN records before the handler runs
        # <!-- wl:id cid-required -->
        - An operator token without a cid MUST be refused with CREDENTIAL_REQUIRED
        # <!-- wl:id status-refusals -->
        - The request MUST be refused when the operator has no record (OPERATOR_UNKNOWN), is pending (OPERATOR_NOT_APPROVED) or is revoked (OPERATOR_REVOKED), and when the credential is not that operator's (CREDENTIAL_OPERATOR_MISMATCH), is revoked (CREDENTIAL_REVOKED) or its attestation has expired (CREDENTIAL_EXPIRED)
        # <!-- wl:id role-now-narrowed-by-cap -->
        - The request MUST be authorised against the capabilities the operator's role carries now, and never beyond the token's cap - what it may use is the capabilities of both. A role changed since the token was issued takes effect on the next request
        # <!-- wl:id route-capability-forbidden -->
        - An administrative route MUST refuse with FORBIDDEN a request that cannot use the capability its minimum stands for (Auth Middleware), whatever role the operator holds. A route only a named operator may use, alone or beside an admin, needs admin:read from that operator. So a token whose cap leaves out a route's capability reaches no such route, an admin's included, whichever component provides it - the orchestrator refuses it on its own routes, and for any other provider the exchange mints a pass naming only what the token may use, which that provider refuses with FORBIDDEN, or mints none and answers FORBIDDEN where nothing the request needs is left (admin-gateway-authorization; architecture/orchestrator, token-exchange)
        - Removing an operator, revoking a credential or rotating an operator's identity key therefore ends every token resting on it at its next request, not when the token expires - at the orchestrator when that request arrives, and for every other component at the exchange, which mints no pass on it (architecture/orchestrator, token-exchange). A pass minted before lives at most 30 seconds (protocol/identity, The pass)
        # <!-- wl:id gateway-no-stand-in -->
        - An admin gateway in front of the orchestrator MUST NOT stand in for this check. The orchestrator holds the records, and a signature check alone proves only that a token was once issued

    - name: admin-gateway-authorization
      description: How the admin gateway carries a person's request inward, on what, and who judges it
      required: true
      rules:
        - The admin gateway is the tenant's one door for people. A client presents a person's operator token there and nowhere else, and the gateway presents it to the orchestrator and to nothing else (protocol/identity, The pass)
        # <!-- wl:id gateway-judged-by-orchestrator -->
        - Every request it carries on a person's token MUST be authorised by the orchestrator's judgement of that token against every capability the request requires (Auth Middleware), as token-status-on-use authorises a request - what the operator's role carries now, never beyond the token's cap, admin:* read as each capability of the admin family by its own name - whichever component provides the route. The gateway MUST NOT authorise by the token's role claim, which is the role at mint and ignores cap, and judges nothing itself
        # <!-- wl:id gateway-forwards-orchestrator-groups -->
        - A request for a group the orchestrator provides MUST be forwarded to the orchestrator with the operator token as it arrived, in the Authorization header, and is judged by its Auth Middleware when it arrives. So is a request to a route that issues tokens, which carries none, a request for a hub proof (hub-proof), which carries none either, and one carrying an attestation token to the attestation route. The orchestrator's routes are those architecture/orchestrator's Administrative endpoints lists, every one under /v1/admin/ and none outside it, which this document's dependency contract binds - Operator management, Agent management, Audit, the Model routes and its overview (The admin API is an aggregate) - but POST /v1/admin/model/audit. The orchestrator serves that route for the model gateway inside its own process alone (architecture/orchestrator, Recording what the model routes do), so the gateway MUST answer a request for it 404 NOT_FOUND, forwarding nothing and exchanging nothing, whatever the service directory declares, as the model gateway answers one that reaches it from outside the process. The gateway forwards no other path to the orchestrator
        # <!-- wl:id gateway-carries-on-pass -->
        - A request for a route any other component provides - an administrative group's (The admin API is an aggregate), or a route of a service whose blueprint admits a person's request on a pass, as architecture/content's and architecture/fabric's do - MUST be sent on a pass, and never on the operator token. The gateway learns such a route, which component provides it and what it requires from the service directory alone, never from a blueprint it was not generated from - it is a route that is not one of the orchestrator's and that exactly one directory entry declares among its pass_routes (protocol/types, PassRoute), matched by method and by path. For each such request the gateway MUST have the orchestrator exchange the token presented with it (architecture/orchestrator, token-exchange), naming as audience the identity id of that entry's component, the fingerprint of the public key the entry carries, and as scope what the next rule names, and MUST send the request on the pass it is answered with, in the Authorization header, with its body as it arrived, at that entry's url and nowhere else
        # <!-- wl:id gateway-pass-address-bound -->
        - The gateway MUST send a pass only where architecture/orchestrator's Presenting a credential to a component allows one - at an address on the orchestrator's host, or at one whose address_provenance is declared or verified. A request whose provider's directory address is on another host and only self-asserted MUST be answered ADMIN_GROUP_UNAVAILABLE, naming that address in the ErrorResponse's detail.address, and nothing is exchanged or sent
        # <!-- wl:id gateway-exchange-scope -->
        - The scope of that exchange MUST name every capability the provider's blueprint requires for the request being carried, and nothing more, as the entry's pass route declares it - every capability in its capabilities, and those of each of its body requirements the request's body meets, which the gateway reads from the body for this alone - architecture/content's pass route for POST /v1/content/repositories, for one, declares content:establish beside content:declare for disposition establish, and content:decide beside it for a declaration carrying scope_floor or self_decision_ceiling, and its route for remotes declares content:replicate with content:connect. The provider judges the pass's cap against the body as it reads it, so a body the gateway read otherwise is refused there with FORBIDDEN, and nothing is carried beyond what the pass names
        # <!-- wl:id gateway-exchange-refusals -->
        - An exchange answered issued false MUST be answered with the code it names, at the status protocol/types registers for it, FORBIDDEN included, whatever the role. An exchange answered 404 NOT_FOUND, because the provider is not registered now, MUST be answered ADMIN_GROUP_UNAVAILABLE. Where the orchestrator cannot be asked, or answers anything else, the request MUST be refused with ADMIN_TOKEN_UNCHECKED, never with the code that answer carried, which judged the gateway's own request. None of these refusals forwards anything
        # <!-- wl:id gateway-relays-step-up -->
        - A provider's 401 refusal of the pass the gateway sent it - PASS_AUDIENCE_MISMATCH, as after the provider's key changed, TOKEN_EXPIRED, as for a pass that arrived after it expired, INVALID_SIGNATURE or PASS_REQUIRED - judged that pass and not the person's token, and MUST be answered ADMIN_TOKEN_UNCHECKED, never with that code or with 401, so a client does not refresh a token nothing refused. STEP_UP_REQUIRED judged the person's re-confirmation, which the pass carries unchanged, and MUST be relayed as it is, its WWW-Authenticate header included (destructive-action-step-up). A provider's answer that judged the request, FORBIDDEN for a cap that does not name what the body requires included, MUST be relayed as it is
        # <!-- wl:id gateway-own-registration -->
        - The gateway MUST hold a registration of its own (protocol/spec, POST /v1/register) whose manifest declares token:exchange and no other capability (protocol/types). It reads the service directory with it, and exchanges a token a person has just presented, and does nothing else with it. It MUST NOT call a provider on its registration token, exchange a token presented with any request but the one it is carrying, or keep a person's token or a pass once that request is answered. It holds no standing access to data
        # <!-- wl:id gateway-manifest-and-listener -->
        - Its manifest (protocol/types, AgentManifest) MUST have type infrastructure, no subscriptions, no publishes and no pass_routes, so it owns no namespace and no person's request is ever carried to it, and a url naming a listener of its own that the orchestrator can reach, never the admin listener, which the operator IP allowlist guards (Admin Gateway Request Lifecycle, step 1). On that listener it MUST serve protocol/spec's seven agent endpoints - POST /v1/describe, GET /livez and GET /readyz as every registrant does, POST /v1/services, answered 200 and taken only as a prompt to read the directory as the next rule says, and POST /v1/execute, POST /v1/message and POST /v1/event, each answered FORBIDDEN, doing nothing, because it takes no task, message or event. It serves nothing else there, and none of the admin routes
        # <!-- wl:id gateway-reads-directory -->
        - The gateway MUST read the service directory only by GET /v1/services, on its registration token, at the orchestrator address it was configured with to register, which is its anchor (architecture/orchestrator, Presenting a credential to a component), over a connection it opened - when it starts, again after each POST /v1/services it receives, again whenever the exchange answers 404 for an audience its directory names, and at least once every 60 seconds besides, with no more than one such read in flight. That bound is this gateway's own - protocol/spec's Implementation Notes require every agent to refresh periodically and only recommend 60 seconds. The orchestrator's pushes are best effort, so without the periodic read a failed push could leave the gateway sending a pass to an address a component has left, until the next push. It MUST NOT take a pushed body as the directory, signed or not, and MUST NOT let anything in one choose a provider, an audience, a url, an address_provenance or a pass route. A signed push proves only that the orchestrator once published that directory (protocol/spec, POST /v1/services, the signed push), and any party that reaches this listener can replay one the orchestrator has since replaced, naming an address a component has given up, and so choose where a person's pass is sent and replay the pass at its real audience within its lifetime. A read at the anchor answers the directory as it is now. So everything that decides where a pass goes arrives from the orchestrator, by that read
        # <!-- wl:id provider-accepts-pass -->
        - A provider other than the orchestrator MUST, on every request for an administrative route, accept a person's request only on a pass addressed to it, as protocol/identity's The pass requires, and refuse with FORBIDDEN a pass whose cap does not name every capability the request requires and any token that is neither a pass nor an operator token. It MUST record who acted as The pass requires, by the pass's identity_id with the gateway's act.identity_id beside it, never by sub or by a header
        - Work a request starts at a provider runs while that request is answered, on the pass that carried it. Work that outlives the request, executing an approved decision included, needs an authority on the approver's behalf that no blueprint specifies yet (architecture/programme-service, Known Gaps, how execution proves it is firing an owner's definition), so no provider performs any on a person's behalf after the request the gateway carried on a pass is answered. Work a provider performs as its own, on no approver's authority, rests on no pass and on no approval the gateway carried, which is that gap
        # <!-- wl:id overview-composed -->
        - The System overview is composed by the gateway, from the orchestrator's GET /v1/admin/overview, forwarded as any request for its groups is, and from each group another component holds, asked of that component on a pass addressed to it as the rules above carry any request, once a pass route can name the overview group it answers. None can yet (protocol/types, PassRoute, which has no such field), so the gateway asks no component for one and MUST report every such group unavailable, never zero. The orchestrator asks no component for any
        - The decision inbox, GET /v1/admin/approvals, is composed by the gateway from each owner's own open decisions, each asked of its owner on a pass addressed to it as the rules above carry any request, once a pass route can name the inbox group it answers. None can yet (protocol/types, PassRoute, which has no such field), so the gateway asks no owner, hard-codes no owner's route, and MUST answer the inbox ADMIN_GROUP_UNAVAILABLE, never an empty list. It serves no route that decides <!-- wl:id inbox-composed-by-pass-route -->
        # <!-- wl:id gateway-unknown-route-unavailable -->
        - The gateway MUST answer with ADMIN_GROUP_UNAVAILABLE, and forward nothing, a request for a route that is not one of the orchestrator's, is not the decision inbox the rule above governs, and that no directory entry declares among its pass_routes, or that more than one declares, since the directory then names no one provider. A component declares a pass route only where its blueprint specifies both the route and that it accepts a pass for it (protocol/types, PassRoute), so a route whose provider is not deployed, or whose provider's blueprint specifies no pass for it, is answered so. It MUST NOT carry such a request as a POST /v1/message action, which checks no operator token (protocol/spec)

    - name: destructive-action-step-up
      description: A destructive act needs the person's own re-confirmation within 300 seconds, and never a second person
      required: true
      rules:
        # <!-- wl:id destructive-acts -->
        - These acts are destructive. Removing an operator (DELETE /v1/admin/operators/{name}), admitting one (POST /v1/admin/operators/{name}/approve), changing one's role (PUT /v1/admin/operators/{name}/role), force-deregistering an agent (POST /v1/admin/agents/{name}/deregister) and revoking a federation peer (POST /v1/admin/federation/peers/{name}/revoke), and each act another blueprint marks destructive by naming this behaviour. Rotating the orchestrator's own key and force-revoking an agent's key (protocol/identity, Key Compromise Recovery, POST /v1/admin/agents/{name}/revoke-key) are destructive too, from the moment architecture/orchestrator specifies a route for either; it specifies neither yet, so nothing serves them
        # <!-- wl:id credential-revocation-not-destructive -->
        - Revoking a credential (DELETE /v1/admin/operators/{name}/credentials/{cid}, one or each of an operator's, operator-credential-revocation) is NOT destructive and MUST be served without a step-up, by an admin on another operator as by an operator on its own. It is how a compromised key is cut off, and incident response must not wait on a re-confirmation the compromised person may be unable to give; it takes nothing the operator cannot regain by attesting a new credential, and it is audited as every revocation is. Removing the operator, which ends their access, is the destructive act above
        # <!-- wl:id step-up-required -->
        - The component that serves a destructive act MUST refuse it with STEP_UP_REQUIRED, and change nothing, unless the operator token or pass it arrived on carries step_up_at (protocol/identity) no more than 300 seconds before the request. It judges this after token-status-on-use and the capability check have passed
        # <!-- wl:id step-up-challenge -->
        - The refusal MUST name the act in detail.control, as its method and route template separated by one space, and carry RFC 9470's challenge, WWW-Authenticate Bearer with error insufficient_user_authentication, an error_description naming the act and max_age 300. A client answers it as architecture/cli's Authentication Flow says
        # <!-- wl:id step-up-is-the-claim -->
        - step_up_at is the only evidence of a step-up, and the orchestrator sets it only on a token minted through a re-confirmation it verified (operator-token-issuance). A token's age is never a step-up
        # <!-- wl:id no-second-person -->
        - The platform requires no second person for any act. A tenant that wants one declares it, as content's per-repository self_decision_ceiling (architecture/content) or a decision its blueprint routes to patterns/approval's multi-party, and that rule runs beside the step-up, never in its place
        # <!-- wl:id destructive-act-audited -->
        - A destructive act MUST be audited with the operator's identity_id, its target and the step_up_at it was admitted on before it takes effect, and a refusal MUST be audited as well
        # <!-- wl:id step-up-one-home -->
        - This is the one statement of when a destructive act needs a step-up. Every other blueprint points here and restates none of it

    - name: operator-credential-revocation
      description: Withdraw one credential, or every credential an operator holds
      required: true
      rules:
        # <!-- wl:id credential-revocation-route -->
        - The route `DELETE /v1/admin/operators/{name}/credentials/{cid}` MUST be permitted to the operator named in the path on a request that can use admin:read, and to an admin on one that can use admin:*, and to nobody else. Another operator is refused with OPERATOR_SUBJECT_MISMATCH, and a request that can use neither with FORBIDDEN
        # <!-- wl:id revoked-credential-kept -->
        - A revoked credential MUST keep its record with status revoked, and its key MUST never be accepted again
        # <!-- wl:id operator-removal-revokes -->
        - Removing an operator MUST set its status to revoked and keep its record, and MUST revoke every credential it holds
        # <!-- wl:id key-change-revokes-credentials -->
        - A change of an operator's identity public key (operator-key-change) MUST revoke every credential the old key attested
        - A sign-records credential is revoked by the same route, and drops out of the record_keys of every token minted afterwards
        # <!-- wl:id last-admin-credential -->
        - A request to revoke the last active authenticate credential of the last active admin MUST be refused with OPERATOR_LAST_ADMINISTRATOR. A sign-records credential is not counted, because it signs nobody in, and neither is a step-up credential, which only re-confirms
        # <!-- wl:id last-admin-key-change -->
        - A change of that admin's identity key MUST NOT be refused on that ground, and revokes the credential all the same (patterns/principal-identity, revocation)
        # <!-- wl:id revocation-audited -->
        - Every revocation MUST be audited with the actor, the credential id and the reason

    - name: operator-key-change
      description: Replace an operator's identity key, keeping the operator, its grant and its identity id
      required: true
      rules:
        # <!-- wl:id key-change-route -->
        - The route `POST /v1/admin/operators/{name}/key` MUST require no bearer token. The two signatures in the request authenticate it, and an operator changing a key may hold no live credential
        # <!-- wl:id key-change-request -->
        - The request MUST carry new_public_key, hub_id, timestamp, current_signature and new_signature. Both signatures MUST be over canonicalize({hub_id, name, new_public_key, timestamp}) per RFC 8785, name being the operator the path names
        # <!-- wl:id key-change-unknown -->
        - The operator MUST have a record here (else OPERATOR_UNKNOWN)
        # <!-- wl:id key-change-foreign-hub -->
        - hub_id MUST be this hub's (else CREDENTIAL_FOREIGN_HUB, logged as a security event), so a request signed for one hub is refused at every other
        # <!-- wl:id key-change-invalid -->
        - The timestamp MUST be inside the 300-second replay window and the request MUST NOT have been seen before, current_signature MUST verify under the public key in the operator's OWN record, new_signature under new_public_key, and new_public_key MUST be an ML-DSA-65 public key. Otherwise OPERATOR_KEY_CHANGE_INVALID, logged as a security event
        # <!-- wl:id key-change-repeat -->
        - A repeat of the change the hub last accepted for the operator MUST be answered as that change was. Where new_public_key is already the operator's public_key, current_signature verifies under the key that change moved to retired_keys, new_signature verifies under new_public_key, and the timestamp is inside the replay window and unseen, the hub MUST answer 200, unless the operator is revoked (OPERATOR_REVOKED, as below), with the operator record, its identity_id and hub_id, change nothing, revoke nothing, and audit it as a repeat of that change. This is the one request current_signature may verify under a retired key for, and it hands nothing on - both keys signed it, and the operator already holds the new one. It is checked before OPERATOR_KEY_REUSED, which would otherwise refuse the operator's own current key, so a client whose answer to an accepted change was lost learns that the change stands
        - Only once both signatures have verified may the hub disclose the operator's status - a revoked operator is then refused with OPERATOR_REVOKED. A pending operator may change its key and stays pending
        # <!-- wl:id key-change-key-reused -->
        - new_public_key MUST NOT be a key this hub records, or recorded, as any operator's identity key, current or retired, or as any credential (else OPERATOR_KEY_REUSED)
        # <!-- wl:id key-change-write -->
        - On success, in one durable write, the new key MUST become the operator's public_key, the old key MUST be added to its retired_keys with the time of the change as its retired_at, and name, role, status and identity_id MUST be kept. Every credential the operator holds, sign-records ones included, MUST be revoked with the reason that the identity key changed, so every token resting on one is refused at its next request
        # <!-- wl:id key-change-not-last-admin -->
        - It MUST NOT be refused with OPERATOR_LAST_ADMINISTRATOR, although it revokes the last admin's credentials - the new key attests a new one (patterns/principal-identity, revocation and identity-rotation)
        # <!-- wl:id key-change-answer -->
        - The response MUST carry the operator record, its identity_id and hub_id, and MUST NOT carry a token. The operator obtains an attestation token with the new key and attests a credential
        # <!-- wl:id key-change-audited -->
        - The change MUST be audited with the operator's identity id and the fingerprints of the old and new keys

    - name: auth-route-rate-limit
      description: How the routes served without a token are limited, at the admin gateway and at the orchestrator, and by whose address
      required: true
      rules:
        # <!-- wl:id auth-routes-limited -->
        - The routes Auth Middleware lists as served without a token, the four that issue tokens, POST /v1/admin/operators/{name}/key and POST /v1/admin/hub/proof, MUST each be limited to 5 requests a minute per source, each route counted on its own, before any signature is verified or made
        - A source is the client's IP address as patterns/rate-limiting derives the IP key, the connection's address or, only where the connection comes from a proxy the component is configured to trust, the address that proxy names in X-Forwarded-For. It is never a name, cid or key in the request, which whoever sends it chooses
        # <!-- wl:id gateway-limits-and-forwards-source -->
        - The admin gateway MUST apply the limit before it forwards anything, and MUST send each request it forwards to the orchestrator with X-Forwarded-For naming the source it counted, in place of any value the request arrived with
        # <!-- wl:id orchestrator-trusts-declared-gateway -->
        - The orchestrator MUST apply the limit to every request for those routes, trusting X-Forwarded-For from the addresses its configuration names as the admin gateway's (schemas/config, orchestrator.admin_gateway_from) and from no other address. So it counts a request the gateway forwarded by its client, never by the gateway's address, which every client of the gateway shares, and a request from any other address by that address, whatever X-Forwarded-For it carries
        - An orchestrator whose configuration names no such address counts every request by its connection's address, so the clients of an admin gateway it was not told of share one count there, and one of them reaching the limit refuses the rest until the minute passes
        - Where the admin gateway's address is one other callers share, as on one host, the orchestrator trusts every caller there to name its own source, so each of them chooses the count it is held to. That is the same-host position architecture/threat-model records as residual, and no wider

    - name: console-credential-use
      description: How a console that acts for signed-in people holds and uses their credentials
      required: true
      rules:
        # <!-- wl:id console-credential-per-account -->
        - A console MUST hold a separate credential for each account at each hub, generate its key pair itself, and have it attested by that account's operator identity through the CLI, never by holding the identity itself
        # <!-- wl:id console-credential-lifetime -->
        - It MUST ask for not_after 30 days ahead unless the person chooses another value within the 90-day cap, and MUST warn the person when fewer than 7 days remain
        # <!-- wl:id console-credential-live-session -->
        - It MUST use a person's credential only while that person holds a live session with the console at AAL2, and MUST NOT mint a token with it at any other time
        # <!-- wl:id console-no-unattended-work -->
        - Work no signed-in person is present for, such as a schedule or a background job, MUST NOT use a person's credential. It needs the console's own service identity at the hub, and this contract specifies no route that admits a console as one (A console holds a credential, never a token), so until one is specified a console does no such work at a hub
        # <!-- wl:id console-not-a-component -->
        - A console MUST NOT register itself, or any key it holds, as a component through POST /v1/register. That route admits any component on its signed manifest alone (protocol/spec, the enrolment gap), so a console could obtain a registration token there with content read, propose and model capabilities and run the unattended work the rule above withholds. A hub cannot tell a console's registration from a component's, so this rule binds the console, and a console that registered is in breach of it
        # <!-- wl:id console-no-agent-token -->
        - It MUST NOT give an agent a token minted with a person's credential, narrowed by cap or not. The console holds the token and sends every request itself. A token's cap names what it keeps, and however little it names the token is still the person's - the hub records what it is used for as the person's own act, cannot tell the agent's requests from the person's, and could end the run only by revoking the person's credential. A cap naming every capability but the person-only ones keeps the rest of the role, admin:* for an admin, which admits operators and sets their roles
        - While the person who started a run holds a live AAL2 session with it, a console MAY send, for that run, reads of the tenant's content and completions through the tenant's model route, and nothing else. Each is the person's request, sent to the tenant's admin gateway on that person's token, which the gateway carries to the content service on a pass naming content:read or content:describe, and to the orchestrator's model route as it arrived (admin-gateway-authorization), where a completion is admitted only for a person whose role carries llm:chat (operator-roles). Neither changes anything at a hub beyond the audit entries recording it, a completion's two model_complete entries among them (architecture/orchestrator, Recording what the model routes do), which is why they are admitted before agent-delegation has a route and nothing that changes more is. They stop when the person's session ends
        - No write, removal, proposal, decision, declaration, act on a remote or other administrative request that an agent chose is sent for it. What an agent prepares reaches a hub only in a request the person submits, under their own token, as their own act, naming the agent and the run on a proposal
        - An agent acts at a hub in its own right only under patterns/principal-identity's agent-delegation, as the intersection of the person's grant, the agent's declared capabilities and an authorisation of that agent the hub holds, or under the console's own service identity. This contract specifies a route for neither, so until one is specified no agent a console runs acts at a hub in its own right, and none continues once its person's session ends
        # <!-- wl:id console-token-at-gateway -->
        - It MUST present a person's token at the tenant's admin gateway and nowhere else, as protocol/identity requires of every holder of an operator token (The pass)
        # <!-- wl:id console-no-sign-records -->
        - It MUST NOT generate, hold or ask an identity to attest a sign-records credential, for anyone. A signature on a record means the person signed it, and a key a console holds signs whenever the console does (patterns/principal-identity, record-signing)
        # <!-- wl:id console-token-in-memory -->
        - It MUST hold an operator token in memory only and never write one anywhere, encrypted or not. What it keeps at rest is the credential key, as an installation secret
        # <!-- wl:id console-discards-tokens -->
        - It MUST discard a person's tokens when that person's session ends, by sign-out, idle or absolute expiry, or the account's revocation, even where exp is later
        # <!-- wl:id console-removal-deletes-keys -->
        - Removing an account from the console MUST delete that account's credential keys. Before it does, it MUST revoke each credential at its hub where it can, with a token minted for a person signed in to the console at AAL2 whom that hub permits to revoke it — the account's own person, or one holding the admin role there
        # <!-- wl:id console-removal-reports -->
        - Where no such person is signed in, it MUST still delete the key, and MUST report for each hub that the credential stays live there until its not_after unless an admin of that hub revokes it
        # <!-- wl:id console-no-store -->
        - When it drives the CLI to connect, register or mint, it MUST pass --no-store and MUST NOT pass --store, so the CLI writes no token file whether or not its mint asks the identity's holder (architecture/cli, Where a token is kept)

    - name: operator-roles
      description: The role names and what each may do
      required: true
      rules:
        - The role names are exactly `viewer`, `auditor`, `operator` and `admin`
        # <!-- wl:id capabilities-from-role -->
        - Capabilities MUST be derived from the role, never stored per operator
        # <!-- wl:id operator-role-admin-family -->
        - The `operator` role MUST carry `admin:read`, `admin:approve` and `admin:strategy` — it is the role every `operator+` endpoint in this document is gated on
        # <!-- wl:id capability-roles-table -->
        - Each `content:` and `programme:` capability, `integration:read`, `integration:manage`, `llm:chat`, `model:attest`, `fabric:read`, `fabric:attest`, `telemetry:read`, `action:invoke` and `scope:admit` MUST be carried by the roles the Operator Roles table gives it, and by no other. Roles are held by operators, who are people, and by nothing else, so a role may carry a capability `protocol/types` marks person only
        # <!-- wl:id admin-wildcard-excludes -->
        - The wildcard `admin:*` MUST NOT be read as carrying `model:attest`, `telemetry:read`, `action:invoke` or `scope:admit`, which are outside the `admin` family
        # <!-- wl:id every-capability-held -->
        - Every capability this document names for a person's token to carry MUST be carried by some role; a capability no role holds is a constant, not a permission. token:exchange, which this document names as what the admin gateway's registration declares, is a component's and not a person's, and no role carries it (protocol/types, Exchange capability); nor does any role carry integration:use or telemetry:push
        # <!-- wl:id last-admin-kept -->
        - The last active admin MUST NOT be removable or demotable
        # <!-- wl:id role-change-audited -->
        - A role change MUST be audited with the previous and new role
```

---

## Operator Identity

Operators are human users who manage the Weblisk deployment. They
use the same ML-DSA-65 identity system as agents but with
operator-specific capabilities.

**Scope: this deployment.** The registration flow below binds an operator to ONE
orchestrator. A subject who operates several hubs holds one self-generated
identity, is registered at each hub, and holds a separate credential at each,
attested by that identity. Registration records the identity and its grant at
this hub. It does not create the identity, and it is not a credential. See
[patterns/principal-identity](../patterns/principal-identity.md).

**An operator's identity id** at this hub is the fingerprint
([`protocol/identity`](../protocol/identity.md#key-fingerprint)) of the
identity public key its registration recorded. The hub records it on the
operator (`Operator.identity_id`) and keeps it across every change of identity
key it accepts ([Changing an identity key](#changing-an-identity-key)), as it
keeps `hub_id` across a rotation of its own key. It is what every token, every
credential and every record that names the operator carries, and never the
name. A new registration is a new identity id, and none is ever reused.

Two consequences worth stating here, because this file is where operators are
defined:

- **Creating a hub grants nothing beyond that hub.** The first-operator
  claim below is a grant recorded in the orchestrator it was made
  against. It is revocable, including revoking the creator, and it confers no
  standing at any other hub. A control plane that provisions hubs therefore
  accumulates grants, not privilege.
- **A directory never authenticates.** Where an external directory or control
  plane lists operators, an orchestrator MUST still verify signatures against the
  public key in its OWN records. Consulting a directory at authentication time
  would make that directory a skeleton key for every deployment trusting it. <!-- wl:id directory-never-authenticates -->

### Operator Registration

```
1. Operator generates ML-DSA-65 key pair (via CLI: weblisk operator init)
2. CLI stores the identity where it resolves that identity to live (rule 2 of
   "Bootstrap without a shell", below): the public key, and the private half
   either as a passphrase-encrypted file or held by a secret source
   (protocol/secret-source)
3. Operator registers with orchestrator:
   POST /v1/admin/operators/register
   {
     "name": "alice",
     "public_key": "<ML-DSA-65 public key (base64url)>",
     "role": "admin",
     "timestamp": "2024-04-03T16:00:00.000Z",
     "signature": "<sign(canonicalize({name, public_key, role, timestamp}))>",
     "bootstrap_secret": "<only at a hub with no operator yet>"
   }
4. Orchestrator verifies signature
5. At a hub with no operator, the registration that presents the bootstrap
   secret is approved as admin (Bootstrap Flow, below)
6. Any other registration is pending until an existing admin approves it
7. The operator attests a credential and mints tokens with it (Obtaining a token)
```

#### The registration signing input

The signature is over `canonicalize({name, public_key, role, timestamp})` —
**the whole payload**, not the `{hub_id, jti, name, timestamp}` the attestation
token request signs. RFC 8785 (JCS), as `protocol/spec` specifies for every
signed payload. `bootstrap_secret` travels beside the signed fields and is not
among them: whoever holds it may claim the hub, which is what it is for.

This MUST be stated exactly, and it was not: this step read
`"<signed registration payload>"` while the token request two sections below
read `"<sign(canonicalize({name, timestamp}))>"`. A generated orchestrator
signed and verified the four-field form; a client signed the two-field form;
the registration was refused with `operator signature verification failed` and
neither side was wrong about anything it had been told. <!-- wl:id registration-input-stated-exactly -->

The four-field form is the correct one and the reason is not symmetry. The
signature must **bind the public key to the name**. Over `{name, timestamp}`
alone the key is unsigned data in a signed request, so anyone able to reach the
endpoint could submit their own public key under any name — and a key
substituted in flight on the registration that presents the bootstrap secret
would take the whole hub. `role` is included for the same reason: it is a
privilege claim and it must not be substitutable in flight.

The timestamp MUST be the one sent in the payload. A client that reads the clock
once to sign and again to build the request produces a signature over a payload
the orchestrator never sees, and it verifies only when both reads land in the
same second — which is a fault that passes locally and fails under load. <!-- wl:id timestamp-sent-is-signed -->

### Obtaining a token

Registration establishes an operator. It does not keep them signed in: tokens
expire in an hour, so there MUST be a way to obtain a new one that does not
require registering again, and that way MUST NOT be the operator's identity. <!-- wl:id renewal-without-identity -->

A client reaches a hub with a **credential**: an ML-DSA-65 key pair the client
generates for that hub alone, bound to the operator's identity by an
attestation the identity signs once
([`patterns/principal-identity`](../patterns/principal-identity.md)). The
identity key is cold. It signs to register, to attest, to change itself and,
where a person re-confirms for a destructive act, a step-up
([Re-confirming for a destructive act](#re-confirming-for-a-destructive-act)),
and nothing it signs is a login. Tokens come from the credential, at a challenge the hub issues, and
the identity is not asked.

```
When a client holds no live credential at a hub — the only steps that need the identity
  client ── sign {hub_id, jti, name, timestamp}, its recorded hub_id, a fresh jti ─▶ POST /v1/admin/operators/token
         ◀── attestation token (type attestation, 300 s), hub_id, identity_id
  client ── Attestation, signed by the identity ───────▶ POST /v1/admin/operators/{name}/credentials
         ◀── the credential, and its id

Whenever a token is needed — the identity is not asked
  client ── cid ───────────────────────────────────────▶ POST /v1/admin/credentials/challenge
         ◀── nonce, hub_id, expires_at
  client ── cid, nonce, signature by the credential ───▶ POST /v1/admin/credentials/token
         ◀── operator token (type operator, carries cid, one hour)
```

The behaviours that bind all of this are `attestation-token-issuance`,
`operator-credential-attestation`, `operator-token-issuance`,
`token-status-on-use` and `operator-credential-revocation`, in
[Contracts](#contracts). What follows is the wire form.

#### The identity signs only to attest

Of the requests by which an operator obtains a token, the identity's
signature authenticates only this one: it also signs a registration, a change
of its own key and a step-up ([Re-confirming for a destructive
act](#re-confirming-for-a-destructive-act)), and none of those signs anybody
in. `POST /v1/admin/operators/token` is unauthenticated by token because it is how
an operator with no credential here starts. The identity signs the request:

```
POST /v1/admin/operators/token
{
  "hub_id": "<the hub_id the client recorded for this hub>",
  "jti": "<at least 128 random bits, base64url, fresh for this request>",
  "name": "alice",
  "timestamp": "2024-04-03T16:00:00.000Z",
  "signature": "<sign(canonicalize({hub_id, jti, name, timestamp}))>"
}
```

The orchestrator looks the operator up by `name` in its OWN records, never in a
directory, and verifies the signature against the public key there, over
`canonicalize({hub_id, jti, name, timestamp})` as received, per
[`protocol/spec`](../protocol/spec.md#signing-input). It refuses a `timestamp`
outside the 300-second replay window, a `hub_id` that is not its own with
`CREDENTIAL_FOREIGN_HUB`, logged as a security event, a `jti` it has recorded
for this operator with `TOKEN_REQUEST_REPLAYED`, and an operator who is
not approved — a registered but unapproved operator is a different fact from
an unknown one. The `jti` is judged first, once the signature verifies and
before the `hub_id` and the operator's status, so a request this hub has
already recorded is answered `TOKEN_REQUEST_REPLAYED` whatever it was first
answered, and a hub that cannot read or write that record refuses with
`STORAGE_ERROR` and issues nothing. The signature names the hub, so it is
refused at every hub but the one whose `hub_id` the client recorded. The client signs the `hub_id`
it recorded from a [registration answer](#the-registration-response), never
one it is told in the same exchange, and makes no such request to a hub it has
recorded none for. Which hub gave that answer is a separate question, which
[Proving the hub at an address](#proving-the-hub-at-an-address) answers once
its test vectors are published, and the gap below says how far it is settled
until then.

**Why a `jti` the client chooses, and not a nonce the hub issues.** An
identity may sign deterministically, as a secret source is free to
([`protocol/secret-source`](../protocol/secret-source.md)), so a payload of `hub_id`, `name` and a
whole-second `timestamp` repeats whenever one identity asks twice in a second,
and a hub that refused the second as a replay refused a request nobody had
replayed. A random `jti` in the signed payload makes every request's bytes its
own, and lets the hub key replay on the `jti`, not on the signature. It costs
no round trip: a nonce the hub issued would need a route that answers anybody
before any signature is checked, and a request that waits on it, while this
request already carries a timestamp the hub bounds to 300 seconds. So the hub
keeps what a replay needs, a `jti` per operator until the request's timestamp
leaves the replay window, which for a request stamped ahead of the hub's clock
is longer than 300 seconds after it arrives, and nothing for a request whose
signature did not verify (`attestation-token-issuance`).

```
200 {
  "token": "<WLT, type attestation>",
  "expires_at": "2024-04-03T16:05:00.000Z",
  "hub_id": "<fingerprint of the orchestrator's first public key>",
  "identity_id": "<alice's identity id at this hub>"
}
```

`identity_id` is what the attestation names the operator by. The attestation
the client submits names the one this answer carries, which the client may
already hold from its registration answer, and it never computes one from the
identity key: the hub keeps it across a change of identity key
([Changing an identity key](#changing-an-identity-key)), so after one it is
not the fingerprint of the key that signed this request. A client attesting
at several hubs in one approval of the identity builds each attestation
beforehand and submits it only where this answer agrees
([`architecture/cli`](cli.md#one-approval-vouches-for-every-hub)).

The token does one thing: it submits an attestation for this operator. Every
other route refuses it. So this endpoint is not the authentication by identity
key that [`patterns/principal-identity`](../patterns/principal-identity.md)
forbids: an identity signature here obtains the right to attest, which is the
one thing an identity is for.

> **Gap — until a hub proves it, a recorded `hub_id` is what the answer
> said.** A client records a hub's `hub_id` from a registration answer. A
> registration names no hub (`registration-signing-input`), so a hub the
> person registers at can relay it, inside the replay window, to
> another hub the person belongs to, which answers it as a repeat with its own
> `hub_id`. A client that has that `hub_id` recorded at another address
> refuses to move it there
> ([`architecture/cli`](cli.md#a-credential-for-each-hub)). A client that has
> it recorded nowhere, as on a new device, records the other hub's `hub_id` at
> the relaying hub's address, and every signature it then makes there for
> that `hub_id` — the attestation-token request, the `Attestation`, the
> credential's answer to a challenge — is good at the other hub, through the
> relaying one, which receives the operator token the other hub issues. HTTPS
> does not stop it: the client is talking to the relaying hub's own address.
> [Proving the hub at an address](#proving-the-hub-at-an-address) closes it,
> because the other hub signs only its own addresses, so no proof it gives
> names the one the client reached. That proof is a fixed-form statement,
> which no implementation signs before its test vectors are published
> ([`protocol/identity`](../protocol/identity.md#fixed-form-statements)), and
> none are, so until they are a person relies on the hub at the address they
> gave not to relay. A registration a client recorded before then is proven
> at its next contact once they are published
> ([`architecture/cli`](cli.md#a-credential-for-each-hub)), so one recorded
> through a relay is used until then and held from then, never moved on an
> answer. The proof does not stop the relay of the registration
> itself: the relaying hub still learns whether the person is an operator at
> the other hub, with that hub's `hub_id` and the person's `identity_id`
> there, and where the person is not one, leaves a pending registration in
> their name there, because a registration names no hub.

**Obtaining an operator token here is deprecated.** A hub built before the
credential routes issues one here. A client MUST use the credential routes
wherever a hub serves them, and MAY accept an operator token from this endpoint
only from a hub that answers `POST /v1/admin/credentials/challenge` with `404`
or `405`. No hub built from this corpus issues one here: it issues operator
tokens only through its credential routes
([Minting a token with the credential](#minting-a-token-with-the-credential)),
whose statement has test vectors. <!-- wl:id client-uses-credential-routes -->

`hub_id` names this hub as an [`Attestation`](../patterns/principal-identity.md#types)
does: the fingerprint ([`protocol/identity`](../protocol/identity.md#key-fingerprint))
of the first public key the orchestrator signed tokens with. The orchestrator
records it with its own state when it first generates that key, and keeps it
when it rotates the key. So a hub that moves or rotates its key keeps its
hub_id and every credential attested for it, and a client tells a rotation from
a different hub by hub_id alone. A hub regenerated without its state has a new
hub_id and holds no credentials.

#### Proving the hub at an address

A registration answer names a `hub_id`, and nothing in the answer shows that
the hub the client reached holds the key that `hub_id` is the fingerprint of.
A hub shows it by signing a
[fixed-form statement](../protocol/identity.md#fixed-form-statements) over the
address it was reached at and a challenge the client makes for that request:

```
"weblisk/hub-proof/v1" 0x00 <hub_id> 0x00 <address> 0x00 <challenge>

<hub_id>     this hub's hub_id, as 64 lowercase hexadecimal characters
<address>    the origin the client reached the hub at, in the ASCII
             serialisation of RFC 6454 section 6.2: the scheme, "://", the
             host in lowercase, and ":" and the port only where the port is
             not the scheme's default. No path, query or trailing "/"
<challenge>  the client's challenge, as the text it sent
```

```
POST /v1/admin/hub/proof
{
  "address": "https://admin.example.org",
  "challenge": "<base64url, 16 to 64 bytes from a cryptographically secure random source>"
}

200 {
  "hub_id": "<fingerprint of public_key>",
  "public_key": "<the public half of the key hub_id names>",
  "address": "https://admin.example.org",
  "signature": "<the statement above, signed by that key>"
}
```

**The hub names no address but its own.** The orchestrator signs only an
address its configuration lists as one of its **admin addresses**, the
origins its admin gateway is reached at
([`schemas/config`](../schemas/config.md#orchestrator), `admin_addresses`), and
refuses any other with `HUB_ADDRESS_FOREIGN`. It never takes the address from
the request's `Host` header, a forwarding header or the connection, because a
hub that relays the request controls all three. So a hub that relays a client's
request for a proof to another hub gets back a refusal, or a proof naming the
other hub's own address, and a client that checks the proof against the
origin it dialled refuses either.

**A proof is only as specific as the origin it names.** An origin more than
one hub can list, such as a loopback address (`https://localhost:9443`), a
private address, or the local end of an SSH tunnel, which
[`schemas/config`](../schemas/config.md#orchestrator) requires to be listed
wherever the gateway is reached through one, names no one hub. A relay
listening at that origin on the client's machine can pass back the proof of
any hub that lists it, and the client cannot tell. At such an origin the proof
shows that the hub answering holds the key its `hub_id` names, and nothing
about what sits between the client and that hub: the tunnel or local route
the person set up is what they rely on there.

**The key is the one `hub_id` names.** The orchestrator signs with the private
key whose fingerprint is its `hub_id`, the first key it signed tokens with,
and keeps that key for as long as it keeps the `hub_id`. Once it signs tokens
with another key, the first signs this statement and nothing else, so the
proof survives a rotation as `hub_id` does.

**No rotation ends a compromise of that key.** Whoever holds it can prove
this hub at any address they serve, for as long as the hub keeps its
`hub_id`, and nothing replaces the key while it does
([`protocol/identity`](../protocol/identity.md#recommended-rotation-schedule)
keeps it out of an orchestrator's rotation). Only a hub regenerated without its state ends
it: that hub has a new `hub_id` and holds no credentials, and every person
registers there again as at any new hub.

The behaviour is `hub-proof`, in [Contracts](#contracts), and the client's
side is [`architecture/cli`](cli.md#a-credential-for-each-hub)'s. No
implementation signs it before its test vectors are published
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)): until
they are, the route answers every request `501` `HUB_PROOF_UNAVAILABLE`, and the gap under
[The identity signs only to attest](#the-identity-signs-only-to-attest)
stands.

#### Attesting a credential

The client generates an ML-DSA-65 key pair for this hub and has the identity sign
an [`Attestation`](../patterns/principal-identity.md#types) for its public half.
The identity signs a typed statement the signer builds itself, never bytes a
caller supplies — [`architecture/cli`](cli.md) gives a console that verb.

```
POST /v1/admin/operators/alice/credentials
Authorization: Bearer <attestation token, or alice's operator token>
{
  "identity_id": "<alice's identity id at this hub>",
  "identity_public_key": "<alice's identity public key>",
  "credential_public_key": "<ML-DSA-65 public key>",
  "hub_id": "<this hub's hub_id>",
  "device_label": "<for people reading a list of credentials>",
  "not_after": 1714752000,
  "signature": "<identity signature over the canonical form of every other field>"
}

200 { "credential": { ... }, "cid": "<fingerprint of credential_public_key>" }
```

**`not_after` is 30 days after attesting by default, is capped at 90, and a
client warns its person when fewer than 7 remain.** The cap is the rotation
interval [`protocol/identity`](../protocol/identity.md#recommended-rotation-schedule)
recommends, and a hub refuses anything longer. The attestation lifetime is the
revocation window for every verifier that is not this hub, so it is kept short.

Re-attesting a key the operator already holds here replaces its attestation and
keeps its id. A key that is, or was, another operator's credential or identity
key is refused with `CREDENTIAL_KEY_BOUND`: every operator's credential keys
are listed to any `viewer`, and a key's fingerprint is its credential's id, so
accepting one would hand that credential, and the tokens it mints, to whoever
attested it second. It may be submitted with that operator's own operator token, so a
client whose credential is still live re-attests with one identity signature and
no attestation token.

**A step-up passkey is attested the same way**, with `purpose` `step-up`,
its COSE key as `credential_public_key`, and `rp_id` and `origin` naming the
console where it was registered with user verification required, never this
hub. The identity attests it through the CLI, since a console never holds the
identity. It never obtains a challenge or a token, and answers nothing but a
re-confirmation
([Re-confirming for a destructive act](#re-confirming-for-a-destructive-act)).

**A key that signs records is attested the same way**, with `purpose`
`sign-records`, from the device where its person signs
([`patterns/principal-identity`](../patterns/principal-identity.md),
`record-signing`). The hub records it under the same checks and the same cap,
lists it, and lets it be revoked, so a lost one can be withdrawn and the people
able to sign records can be counted. It never obtains a challenge or a token.
Instead, every operator token the hub mints for that operator names it in
`record_keys`, and that is how a service that receives a signed record learns
the key is live here. A key serves one purpose at this hub: one recorded to
sign in is refused for signing records, and the reverse.

#### Minting a token with the credential

```
POST /v1/admin/credentials/challenge
{ "cid": "<credential id>" }

200 { "nonce": "<base64url>", "hub_id": "<this hub's hub_id>", "expires_at": "2024-04-03T16:05:00.000Z" }
```

A challenge for a credential the hub does not hold is refused with
`CREDENTIAL_UNKNOWN`, so a client learns at once that it must attest. For one it
does hold, revoked or expired included, the hub issues a nonce: whether a
credential is still live is told only to its key, at the token request.

```
POST /v1/admin/credentials/token
{
  "cid": "<credential id>",
  "nonce": "<the nonce>",
  "signature": "<credential signature over the bytes below>"
}

    "weblisk/credential-auth/v1" 0x00 <hub_id> 0x00 <nonce>

    <hub_id> is its 64 hex characters and <nonce> its base64url text as the
    challenge returned it, both as ASCII (operator-token-issuance)

200 {
  "token": "<WLT, type operator, carries cid, identity_id and record_keys>",
  "expires_at": "2024-04-03T17:00:00.000Z",
  "role": "operator",
  "capabilities": ["admin:read", "admin:approve", "admin:strategy",
                   "content:read", "content:describe", "content:write",
                   "content:propose", "content:decide", "content:reconcile",
                   "programme:read", "programme:install",
                   "programme:operate", "programme:switch",
                   "integration:read", "fabric:read", "fabric:attest"],
  "not_after": 1714752000
}
```

The request carries no `cap`, so the token and its `capabilities` carry every
capability the `operator` role carries ([Operator Roles](#operator-roles)).

A token request may also carry `cap`, a list of capability names, and the
token then carries only those of them the operator's role carries
(`operator-token-issuance`). It only narrows, for a client that needs less
than the role carries, such as a script. It is not what keeps a token from a
component: a person's token goes to the tenant's admin gateway and no further,
narrowed or not, and every component is reached on a pass
([`protocol/identity`](../protocol/identity.md#the-pass)). A narrowed token
is still the person's, and never one to give an agent. It is not signed,
because nothing it can do widens what the credential already reaches.

The signed bytes are fixed and domain-separated. A credential never signs a
caller's bytes, and a signature made here cannot be presented as a signature
over a JSON payload, which begins with `{`. The client signs with the `hub_id`
its credential was attested for. A challenge that answers with a different one
is a hub the client holds no credential for.

Neither the challenge nor its `hub_id` is signed by the hub. `hub_id` in the
signed bytes stops a signature made for one hub from being spent at another. It
does not stop an impostor at the hub's address from relaying this hub's
challenge to the client. The transport stops that: HTTPS to the hub's address,
with its certificate verified, which this surface requires everywhere
([Implementation Notes](#implementation-notes)). HTTPS does not stop a hub
the client reaches at that hub's own address from relaying another hub's
challenge. A challenge naming a `hub_id` other than the one recorded at the
address the client reached is refused
([`architecture/cli`](cli.md#a-credential-for-each-hub)), so that relay works
only where a registration answer recorded the other hub's `hub_id` at the
relaying address: the gap under
[The identity signs only to attest](#the-identity-signs-only-to-attest),
which the hub proof closes.

Refresh is the same pair of calls. A separate refresh endpoint would need a
valid token to obtain a token, which fails exactly when it is needed — after
expiry. So is a re-confirmation: the same token request, carrying `step_up`
beside the credential's answer
([Re-confirming for a destructive act](#re-confirming-for-a-destructive-act)).

**A credential's answer has test vectors.** It is a fixed-form statement, and
this corpus publishes vectors for `weblisk/credential-auth/v1`
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)), whose
`hub_id` is a vector key's fingerprint. A client that signs a credential's
answer and a hub that verifies it each test against them. A hub built from this
corpus issues an operator token to a credential alone, never on the identity's
signature, which [`patterns/principal-identity`](../patterns/principal-identity.md)
forbids a hub to accept as authentication. Only a hub built before the
credential routes, which answers the challenge with `404` or `405`, issues one
by the deprecated path under
[The identity signs only to attest](#the-identity-signs-only-to-attest).

#### Where the second factor is

The admin surface requires two factors, without exception. A hub verifies
signatures. It cannot see what opened a key, as no verifier of a key-based
authenticator can, so the rule sits where each key is opened, and the hub rests
on it:

- **Attesting.** A person's identity key never rests unencrypted
  ([`protocol/identity`](../protocol/identity.md) rule 1). It signs only once a
  passphrase opens its envelope, or once the secret source that holds it
  answers the person's unlock. An attestation is a key the person has, opened
  by something they know or unlock. It is the multi-factor act a credential
  rests on.
- **Minting.** A credential's signature proves possession of the credential key
  and nothing more. A client MUST keep a person's credential key where it signs
  only after that person's own act: in the `weblisk-key-v1` envelope with `kdf`
  `argon2id`, opened by a passphrase the person types or one a secret source
  they unlock remembers; in a secret source they unlock; in the platform
  keychain source, where the act that unlocks it is the person's own login to
  the machine, and it releases the key without a prompt while that session is
  unlocked ([`architecture/cli`](cli.md#a-credential-for-each-hub)); or, in a
  console, released only while the person holds a live AAL2 session with it
  (`console-credential-use`). The keychain's cost is accepted, and stated: its
  key is protected by the machine login, not by the identity's holder, so
  while the session is unlocked any program running as the person can mint
  with it. A key in the clear, under `kdf` `none`, or behind a source nobody
  unlocks, such as `file:`, is not a person's credential. <!-- wl:id credential-key-behind-act -->
- **Not per request.** A token proves that a live credential minted it within
  the hour, and every request re-checks that credential (below). A token
  carries no claim that a factor was presented, and a gateway MUST NOT look for
  one. The hub could not verify such a claim, so it would be set true on every
  token and would prove nothing. <!-- wl:id no-factor-claim -->
- **Re-confirming.** A destructive act asks for more than a live credential: a
  proof, made within the last 300 seconds, that the person was asked and
  answered. The hub verifies that proof itself when it mints, and records
  only the time it did, below.

#### Re-confirming for a destructive act

A destructive act is admitted only on a token, or a pass, whose `step_up_at`
is no more than 300 seconds old, and never needs a second person
(`destructive-action-step-up`, which names the acts). `step_up_at`
([`protocol/identity`](../protocol/identity.md#payload-claims)) is set by the
orchestrator alone, on a token it mints through a re-confirmation it verified
itself, and a pass carries it unchanged. A credential's answer alone never
sets it, however recent: a keychain releases that key without asking anybody,
so a silent renewal is never a step-up. A component refusing an act answers
`STEP_UP_REQUIRED` with RFC 9470's challenge and the act's name:

```
401 WWW-Authenticate: Bearer error="insufficient_user_authentication",
      error_description="DELETE /v1/admin/operators/{name} needs a step-up",
      max_age=300
{ "error": "...", "code": "STEP_UP_REQUIRED",
  "detail": { "control": "DELETE /v1/admin/operators/{name}" } }
```

A re-confirmation is a token request carrying `step_up`, over the nonce the
same request's credential signature spends:

```
POST /v1/admin/credentials/token
{
  "cid": "<credential id>", "nonce": "<the nonce>", "signature": "<as above>",
  "step_up": {
    "control": "DELETE /v1/admin/operators/{name}",
    "form": "identity",
    "signature": "<identity signature over the bytes below>"
  }
}

    "weblisk/step-up/v1" 0x00 <hub_id> 0x00 <nonce> 0x00 <control>
```

It takes one of two forms (`operator-token-issuance`):

- **`identity`, the identity signs.** One vault approval, or one passphrase,
  over the bytes above, verified against the identity key in the operator's
  own record. It is always available, and it is the CLI's form. It signs in
  nobody: the credential's answer beside it is what authenticates the request,
  and the identity's signature adds `step_up_at` to the token it obtains.
- **`passkey`, one touch.** A user-verified passkey the person registered
  with a console, attested by their identity to this hub with `purpose`
  `step-up` ([Attesting a credential](#attesting-a-credential)), its
  attestation naming the console's `rp_id` and `origin`. The console asks
  the authenticator for an assertion whose challenge is the bytes above, and
  sends `credential`, `authenticator_data`, `client_data_json` and
  `signature` in `step_up`. The hub checks the assertion against the attested
  key, `rp_id` and `origin`, with user verification required, so a console
  cannot make one without its person. A passkey is ES256 or EdDSA, and it
  re-confirms a person a post-quantum credential has already authenticated:
  alone it admits nothing
  ([`patterns/principal-identity`](../patterns/principal-identity.md) Design
  Principle 6).

The control names what the person was shown and the audit records; the token
carries only the time. Any destructive act the person makes in the next 300
seconds is admitted on it, as RFC 9470's `max_age` reads.
`weblisk/step-up/v1` has test vectors
([`protocol/identity`](../protocol/identity.md#fixed-form-statements)): a
client that signs one and a hub that verifies one each test against them.

#### Every request checks what its token rests on

A WLT is self-contained: once issued, nothing about it can be recalled. The
orchestrator holds the operator record, the credential and the grant, so it is
the one party that can end a token before `exp`, and
[`patterns/principal-identity`](../patterns/principal-identity.md) requires it
to. On every request bearing an operator token it looks up the operator named
by `sub` and the credential named by `cid` in its own records before the handler
runs, and authorises against what the operator's role carries **now**.

Removing an operator, revoking a credential or rotating an operator's identity
therefore takes effect on the person's next request, not an hour later. No
other component receives the token: the admin gateway has it exchanged for a
pass for each request it carries elsewhere, and the exchange makes this same
judgement before it mints one
([`architecture/orchestrator`](orchestrator.md#token-exchange-post-v1tokenexchange)).
A pass already minted lives at most 30 seconds. A client told why
([Error Handling](#error-handling)) knows what to do: attest again, wait for an
approval, or stop.

#### Revoking a credential

`DELETE /v1/admin/operators/{name}/credentials/{cid}?reason=<text>` revokes one
credential. The operator it belongs to may revoke it, and so may an admin. The
identity, the grant and the operator's other credentials are untouched. Removing
an operator revokes all of theirs, and so does a change of their identity key.

A hub refuses a request to revoke the last active authenticate credential of
its last active admin, because that would leave nobody able to mint. A
sign-records credential is never counted: it signs nobody in. It does not refuse a
change of that admin's identity key, although that revokes the same credential:
the new identity asks for an attestation token and attests a new one. The
identity is the recovery path for every credential a subject holds
([`patterns/principal-identity`](../patterns/principal-identity.md)).

### Changing an identity key

An operator replaces the identity key it registered with through
`POST /v1/admin/operators/{name}/key`, operation `OperatorKeyChange`, signed by
the key it replaces and by the one replacing it. This is
[`patterns/principal-identity`](../patterns/principal-identity.md)'s
`identity-rotation` at this hub, and [`protocol/identity`](../protocol/identity.md#key-rotation)'s
operator key rotation on the wire:

```
POST /v1/admin/operators/alice/key
{
  "new_public_key": "<ML-DSA-65 public key>",
  "hub_id": "<this hub's hub_id>",
  "timestamp": "2024-04-03T16:00:00.000Z",
  "current_signature": "<the current identity key's signature over the input below>",
  "new_signature": "<the new identity key's signature over the same input>"
}

    canonicalize({hub_id, name, new_public_key, timestamp})

200 { "operator": {...}, "identity_id": "<unchanged>", "hub_id": "<this hub's hub_id>" }
```

The current key's signature is the continuity: only whoever held the key the
hub recorded can hand the operator on. The new key's signature proves it is
held. `hub_id` in the signed input stops a request made for one hub from being
spent at another where the same identity is registered.

**A change whose answer was lost is answered again.** The hub applies a change
in one durable write, so a client whose connection dropped before the `200`
arrived cannot tell whether the change stands, and sending it again with the
old key as `current_signature` no longer verifies under the operator's record.
So a request whose `new_public_key` is already the operator's key, signed by
the key the last change retired and by that new key, over a fresh timestamp,
is answered `200` exactly as the change was, and changes nothing. Both keys
signed it, so it proves nothing a retired key could not prove alone: the
operator holds the new key already.

**What changes, and what does not.** The operator keeps its name, role,
status and **identity id**. The old key moves to `retired_keys`, with the time
of the change as its `retired_at`, and is never accepted again as anybody's
identity key or credential, the operator's own included. Every credential the
old key attested is revoked, so the operator is signed out everywhere at its
next request, and signs in again by attesting a new credential with the new
key. Because the identity id is kept, a record made before the change and one
made after name the same operator: a person who proposed a change and then
changed their key is still its requester
([`architecture/content`](content.md#separation-of-duties)).

**A key that is lost cannot be changed.** Nothing but the key the hub
recorded can sign the continuity. An operator who has lost it is removed by an
admin and registers again under a new name, as a new identity id: a removed
operator's name stays with its revoked record and is never reused
([`protocol/identity`](../protocol/identity.md#recovery-via-backup-operator)).

`operator-key-change` in [Contracts](#contracts) is the rule.

### The registration response

`POST /v1/admin/operators/register` returns the operator record, and a token
**only when registration also approved the operator** — the first-operator
claim. That token is an attestation token. Otherwise there is no token to give,
and the response says so:

```
200 { "operator": {...}, "status": "approved", "token": "<WLT, type attestation>", "expires_at": ..., "hub_id": ..., "identity_id": ... }
200 { "operator": {...}, "status": "pending", "hub_id": ..., "identity_id": ... }
200 { "hub_id": ..., "identity_id": ... }
```

Every answer names the hub and the operator, because the client signs that
`hub_id` to obtain an attestation token
([The identity signs only to attest](#the-identity-signs-only-to-attest)): a
pending operator learns it here and asks once approved. A registration that
repeats an operator's own, the same name and the operator's current key, is
answered as the third line is, and changes nothing, so a person who
registered from another device records the hub's `hub_id` by registering
again (`operator-registration`), and, once the hub proof has test vectors,
holds it only where the hub at that address proves it
([Proving the hub at an address](#proving-the-hub-at-an-address)). It carries no record, role or status,
whatever the operator's status: a registration names no hub, so a hub it was
relayed from learns from the answer only what a `409` already told it, and
those two identifiers
([The identity signs only to attest](#the-identity-signs-only-to-attest), the
gap there). The operator's status is told to a request signed for this hub.

Stated because it was not, and the omission broke the chain in a way that looked
like success. A generated orchestrator returned the operator record alone; the
CLI stored a token only if the response carried one, so it printed
`[ok] Registered` and saved nothing; `operator token` then reported no token;
and every `/v1/admin/*` call answered `401`. Each component behaved correctly
against what it had been told, and the deployment could not be administered.

**A client MUST NOT infer a token from a successful registration.** It reads
`status`, and asks for an attestation token when none was issued. <!-- wl:id client-reads-status -->

### Admitting the operators after the first

The registration flow above ends a second operator at `status: "pending"`, and
says an existing admin must approve them. For a long time nothing said **how**,
and so nothing did: the capability `admin:approve` existed, the status
`approved` existed, and there was no route, no command and no screen that moved
an operator from one to the other. Every generated orchestrator was therefore a
deployment exactly one person could ever administer, and it reported no fault
at any point — registration succeeded, and the operator was told to wait for
something nobody could do.

```
POST /v1/admin/operators/alice/approve
Authorization: Bearer <admin token>
```

The orchestrator MUST: <!-- wl:id approve-orchestrator-steps -->

1. Require the `admin` role. Approval grants authority, so it is not an
   `operator` action, and `admin:approve` is not the capability that carries it
   — that one is an `operator`'s.
2. Look up the operator by name and refuse an unknown one with `404`.
3. If the operator is already `approved`, succeed and change nothing. Approval
   is a state, not an event, and a retried call MUST NOT fail. <!-- wl:id approve-idempotent -->
4. Otherwise set status to `approved` and record who approved it.
5. Return the operator record, **and no token**:

```
200 { "operator": {...}, "status": "approved", "approved_by": "bob", "approved_at": ... }
```

The approved operator attests a credential of their own and mints tokens with
it, as any operator does ([Obtaining a token](#obtaining-a-token)). Handing a
token back here would issue a credential to whoever ran the approval rather
than to its subject.

**Refusal is `DELETE /v1/admin/operators/{name}`**, which already exists. There
is no separate reject verb, because a rejected registration and a removed
operator leave the deployment in the same state, and two routes to one state
drift.

`GET /v1/admin/operators` MUST list `pending` operators alongside approved
ones. An admin who cannot see who is waiting cannot approve them, and a list
that quietly filters to approved operators makes a waiting colleague look like
a failed registration. <!-- wl:id operators-list-pending -->

### Operator Roles

| Role | Capabilities | Description |
|------|-------------|-------------|
| **admin** | `admin:*`, `llm:chat`, `model:attest`, every `content:` and `programme:` capability, `content:declassify` and `programme:switch` among them, `integration:read`, `integration:manage`, `fabric:read`, `fabric:attest`, `telemetry:read`, `action:invoke` and `scope:admit` | Full access — manage operators, agents, federation, strategies, declare and establish content repositories, declare their remotes, ask the tenant's model, record model provider agreements, confirm or reject relationships, install and switch programmes, make and bind integrations, read the tenant's runtime, invoke operator actions, and admit a component's operational scope. The only role that carries `content:declassify`, `llm:chat`, `integration:manage`, `telemetry:read`, `action:invoke` or `scope:admit` |
| **operator** | `admin:read`, `admin:approve`, `admin:strategy`, `content:read`, `content:describe`, `content:write`, `content:propose`, `content:decide`, `content:reconcile`, every `programme:` capability, `integration:read`, `fabric:read`, `fabric:attest` | Day-to-day operations — view everything, approve recommendations, manage strategies, write documents, decide proposals, run programmes, and confirm or reject relationships |
| **viewer** | `admin:read`, `content:read`, `content:describe`, `programme:read`, `integration:read`, `fabric:read` | Read-only — view dashboards, logs, status, documents, programmes, integrations and relationships. Cannot modify anything |
| **auditor** | `admin:read`, `admin:audit`, `content:read`, `content:describe`, `programme:read`, `integration:read`, `fabric:read` | Read-only plus full audit log access with export capability |

A role is held by an operator, and an operator is always a person
([`protocol/types`](../protocol/types.md#operator)), so a role may carry a
capability `protocol/types` marks *person only*. Every such capability reaches
a person this way and reaches a service by no route: a service subject holds
no role, and a registered component is refused one in its manifest
([`patterns/principal-identity`](../patterns/principal-identity.md),
`service-subject-constraints`).

`content:declassify` is person only, and `admin` carries it and no other role
does: lowering a recorded scope decides what may then leave the tenant, as
raising a model's ceiling does. No route admits it yet. The content service
refuses every lowering until the tenant's approval queue can route the request
to a second person
([`architecture/content`](content.md#a-scope-only-rises), the gap there).

`llm:chat` asks the tenant's model for a completion
([`architecture/orchestrator`](orchestrator.md#administrative-endpoints)),
which spends what the tenant pays for its model and sends what it carries to
a model provider. Nothing yet limits what one person's completions may use,
so `admin` carries it and no other role does, and a role that reads
everything through `admin:read` asks the model nothing.

`programme:switch` decides whether a programme's operations reach people, so
it is person only; `operator` carries it with the rest of the `programme:`
family because running the tenant's programmes is day-to-day work, as deciding
a proposal is. `integration:manage` and `content:connect` together decide which
outside account the tenant acts as and where its content goes, and `admin`
holds both by default. A person delegates only their own account, and an
integration they delegated lapses when they leave or this table stops giving
their role the grant it was made under. `integration:read` shows no secret, so
every role reads integrations.

`telemetry:read`, `action:invoke` and `scope:admit` are outside the `admin`
family ([`protocol/types`](../protocol/types.md#capability)), so `admin:*` does
not carry them, and this table gives them to `admin` alone. The roles carrying
`telemetry:read` change only through the change cycle, never by a grant at run
time. `integration:use`, `telemetry:push` and `token:exchange` are a
component's, and no role carries them.

`fabric:attest` is the person-only capability the fabric's person routes
require ([`architecture/fabric`](fabric.md#registration-and-standalone-operation)):
only a person confirms or rejects a relationship, so this table is the one way
it reaches anybody. `auditor` reads relationships and confirms none, because an
auditor who confirmed a relationship would then be auditing their own claim.

`operator` sits between `auditor` and `admin` deliberately: it is the role that
does the day-to-day work — approving recommendations and managing strategies —
without the authority to admit, remove or re-role other operators. Every
endpoint above marked `operator+` means this role.

This table once disagreed with the `operator-roles` behaviour block, which
listed three roles and omitted `operator`. A generated orchestrator resolved the
contradiction the defensible way — it followed the contract block, wrote down
that it had, and produced a three-value enum. The result was that
`admin:approve` and `admin:strategy` were declared as constants and granted to
**no role whatsoever**, so every `operator+` route was reachable only by a full
admin, and the middle tier of the permission model existed on paper only.
Nothing failed; the deployment simply had one fewer role than it was designed
to have. Contradicting yourself in a specification does not produce an error —
it produces confident, well-commented, wrong code.

### Operator Token

Operator tokens use the same WLT format as agent tokens, with the `cid`,
`identity_id`, `type`, `role` and `record_keys` claims
[`protocol/identity`](../protocol/identity.md#payload-claims) declares:

```json
{
  "sub": "alice",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712163600,
  "cap": ["admin:read", "admin:approve", "admin:strategy",
          "content:read", "content:describe", "content:write",
          "content:propose", "content:decide", "content:reconcile",
          "programme:read", "programme:install", "programme:operate",
          "programme:switch", "integration:read",
          "fabric:read", "fabric:attest"],
  "cid": "<id of the credential that obtained it>",
  "identity_id": "<alice's identity id at this hub>",
  "record_keys": [],
  "role": "operator",
  "type": "operator"
}
```

This token was minted with no `cap`, so its `cap` is the operator role's full
set. Its operator holds no sign-records credential here, so `record_keys` is
the empty list; one who holds a live one has its id there. One minted with `cap` `[admin:*]` would carry only `admin:read`,
`admin:approve` and `admin:strategy` (`operator-token-issuance`).

**Operator tokens have a one-hour TTL,** and never outlive the attestation of the
credential that obtained them. A client mints the next one with that credential,
and the identity is not asked. `cid` names the credential, which is what lets
the orchestrator end the token early
([Every request checks what its token rests on](#every-request-checks-what-its-token-rests-on)).
`identity_id` is the identity that credential was attested by. A component that
records who acted records it, never `sub`, which is the operator's name.

`type` is `operator` for a token that administers, and `attestation` for the
one an identity signature obtains. An attestation token carries `sub`, `iss`,
`iat`, `exp` and `type`, no `cap` and no `cid`, and lives at most 300 seconds.
`role` records the role at issue. A request is authorised against what the
role the operator holds when it arrives carries, never beyond the token's
`cap` (`token-status-on-use`).

### A console holds a credential, never a token

A **console** is a client that acts for people who sign in to it rather than
for the person at a terminal — Studio is one. It holds credentials for many
people at many hubs, and that is exactly what makes a token at rest in it
dangerous: an operator token carries `admin:*` for an admin, and whoever holds
it may replay it. So a console keeps the thing that can **ask**, and never the
**answer**.

- **One credential per account per hub.** The console generates the key pair and
  has the account's operator identity attest it through the CLI
  ([`architecture/cli`](cli.md), `weblisk operator attest`). The console never
  holds the identity: [`protocol/secret-source`](../protocol/secret-source.md#a-console-never-holds-the-secrets-of-an-identity-it-acts-for)
  says so, and says how the console keeps the credential's key at rest.
- **Only while the person is there.** A person's credential is used only while
  that person has a live session with the console at AAL2 — NIST SP 800-63B
  authenticator assurance level 2, proof of two distinct factors such as a
  password and a one-time code. A token is discarded when the session that
  minted it ends, even if its `exp` is later.
- **Nobody present means no person's credential.** A schedule or a background
  job never uses a person's credential. It would need the console's own
  service identity at the hub: a service subject under
  [`patterns/principal-identity`](../patterns/principal-identity.md), with a
  named human owner, vouched for by a holder of the authority to issue
  grants, with an expiry. That authority is principal-identity's `grant:issue`,
  and at a hub it is `admin:*`.
  This contract has no route that admits a console's service subject, grants
  it and mints it a token. The operator routes admit people only, and
  `POST /v1/register` admits a mesh component on its manifest alone
  ([`protocol/spec`](../protocol/spec.md#post-v1register)), with nothing
  that could tell a console from a component, so a console MUST NOT register
  itself there (`console-credential-use`). Until a route is specified, a
  console does no unattended work at a hub, and work that runs whether or
  not anybody is present belongs to the tenant's own services. <!-- wl:id console-not-registered -->
- **An agent a console runs never holds a person's token.** This binds a
  console. A token a person's own CLI stores on their machine is outside it,
  and any program that person runs can read that file, an agent among them,
  which [`architecture/cli`](cli.md#weblisk-operator-token) states: where a
  mint asks the identity's holder it writes one by default unless the person
  passes `--no-store`, and where a mint is silent only where they pass
  `--store`. A token's `cap` names the
  capabilities it keeps, and however little it names, the token is still the
  person's. The hub records whatever it is used for as the person's own act,
  cannot tell an agent's request from the person's, and could end the run
  only by revoking the person's credential. And a token narrowed only of
  the person-only capabilities is hardly narrowed: a `cap` naming everything
  but those keeps the rest of the role, which for an admin is `admin:*`, and
  an agent holding that could register an operator with a key of its own,
  approve it, give it a role, and through it decide the person's own
  proposal as somebody independent. No person would have vouched for that
  operator. An agent acts at a hub under
  [`patterns/principal-identity`](../patterns/principal-identity.md)'s
  `agent-delegation` — the intersection of the person's grant, the agent's
  declared capabilities and an authorisation of that agent which the hub
  holds, which expires and which the person can revoke alone — or under the
  console's own service identity. This contract has a route for neither.
- **An attended run reads and asks the model, and nothing else.** While the
  person who started a run is signed in to the console at AAL2, the console
  may send, for that run, reads of the tenant's content and completions
  through the tenant's model route
  ([`architecture/orchestrator`](orchestrator.md#a-model-is-a-destination)).
  Each is the person's own request, sent by the console to the tenant's
  admin gateway on the person's token: the gateway carries a read to the
  content service on a pass naming `content:read` or `content:describe`, and
  a completion to the orchestrator's model route as it arrived, where it is
  admitted only for a person whose role carries `llm:chat`
  ([Operator Roles](#operator-roles)). Neither changes anything at the hub
  beyond the audit entries recording it, two `model_complete` entries for a
  completion
  ([`architecture/orchestrator`](orchestrator.md#recording-what-the-model-routes-do)),
  which is why they are admitted before agent-delegation has a route.
  The hub records them as the person's and cannot attribute them to the run,
  a limit stated here rather than left to be found. They stop when
  the person's session ends. Nothing an agent chose that would change
  anything is sent for it — no write, proposal, decision, declaration,
  act on a remote or other administrative request. What it prepares reaches the
  hub only when the person submits it, under their own token, as their own
  act, naming the agent and the run on a proposal
  ([`architecture/content`](content.md#who-a-change-was-for)). No agent a
  console runs acts at a hub in its own right, and none continues once its
  person's session ends, until one of the two routes above is specified.
- **A token goes to the admin gateway and no further.** A console presents a
  person's token at the tenant's admin gateway and nowhere else, as every
  holder of an operator token must
  ([`protocol/identity`](../protocol/identity.md#the-pass)). The content
  service, the fabric and every other component are sent the person's
  request on a pass addressed to them alone, carrying only what that request
  needs, so none of them holds anything it could present elsewhere: a pass
  carries `admin:*` only to the provider of a route whose minimum is `admin`,
  for that one request, and is refused everywhere but there.
- **Tokens stay in memory.** A console never writes an operator token anywhere,
  encrypted or not. A console that drives the CLI always passes
  `--no-store` and never `--store`, so the CLI stores none either.

`console-credential-use` in [Contracts](#contracts) is the rule.

---

## Admin Endpoints

All admin endpoints are served under `/v1/admin/` and require a valid
operator token, whichever component serves them (`admin-gateway-authorization`),
except the six that carry none: the four routes that issue tokens, the hub
proof and the change of an identity key ([Auth Middleware](#auth-middleware)).
The attestation route also takes an attestation token for the operator it
names.

### The admin API is an aggregate

Each group below is **served by the component that owns the state**, and its
routes belong in that component's blueprint, which for every group but the
orchestrator's specifies none yet, or none a pass may reach (the gap below). The admin gateway composes one
operator surface from them. It forwards a request for the orchestrator's groups
on the person's own token, and sends one for any other provider's on a pass the
orchestrator exchanged that token for, addressed to that provider alone; its
own registration exchanges and reads the directory, and reaches no data
(`admin-gateway-authorization`). It is not the owner of the data and it is not
co-located with any single provider. The System overview is composed by the
gateway: the orchestrator's `GET /v1/admin/overview` reports what the
orchestrator holds, and each figure another component holds is asked of that
component on a pass. A figure no provider here may be asked for is reported
unavailable. The orchestrator asks no component for a figure, because it never
presents a token it received
([`protocol/identity`](../protocol/identity.md#the-pass)).

| Group | Provider | Present when |
|---|---|---|
| Operator management | Orchestrator | always — it is the trust anchor and holds operator records |
| Agent management | Orchestrator | always |
| Audit | Orchestrator | always |
| Model | Orchestrator, on the platform-provided routes the CLI installs: `/v1/admin/model` (GET and PUT), `/v1/admin/model/providers` (GET), `/v1/admin/complete` (POST), `/v1/admin/model/agreements` (POST and GET), `/v1/admin/model/agreements/{id}` (DELETE) and `/v1/admin/model/ceiling` (GET) ([`architecture/orchestrator`](orchestrator.md#administrative-endpoints)) | always |
| System overview | composed by the admin gateway | always, with absent providers reported absent |
| Decision inbox: `/v1/admin/approvals` | composed by the admin gateway from each owner's own open decisions ([`patterns/approval`](../patterns/approval.md)); each is decided at its owner ([Decision Inbox](#decision-inbox)) | once a `PassRoute` can name the inbox group a route answers, with an owner that cannot be asked reported absent. None can yet, so the gateway answers it `ADMIN_GROUP_UNAVAILABLE` |
| Health | the orchestrator's leases, in the agent list and the overview; and telemetry's SLO status, which no blueprint specifies yet: telemetry's is written in the second step of the tenant service plan | the leases always; SLO status once a telemetry component's blueprint specifies it on a pass |
| Domains | Domain controllers | a domain controller is deployed |
| Workflow runs: `/v1/admin/workflows` and `/v1/admin/workflows/{id}` | Execution, which holds every run, a programme's and a domain's ([`architecture/programme-service`](programme-service.md#execution)) | an execution component whose blueprint specifies both routes and a pass for them is deployed. No blueprint does yet |
| Programme objectives | The programme service ([`architecture/programme-service`](programme-service.md)), whose objectives retire strategies | a programme service whose blueprint specifies its objectives and a pass for them is deployed. None does yet |
| Federation | Federation layer | the deployment federates |
| Alerts | Alerting agent ([`agents/alerting`](../agents/alerting.md)) | the alerting agent is deployed |
| Runbooks | Execution, into which incident runbooks merge ([`architecture/programme-service`](programme-service.md#execution)) | an execution component whose blueprint specifies the routes and a pass for them is deployed. None does yet; [`agents/incident-response`](../agents/incident-response.md) specifies them today and accepts no pass for them (the gap below) |
| Rate limits | The component applying [`patterns/rate-limiting`](../patterns/rate-limiting.md) | that component is deployed |

**An endpoint whose provider is not deployed MUST report itself unavailable, and
MUST NOT return an empty result.** An empty decision inbox and an owner that
could not be asked are different facts, and a console that renders them identically tells an
operator the system is quiet when it is simply not there. <!-- wl:id provider-absent-unavailable -->

> **Gap — no provider but the orchestrator serves its group on a pass yet.**
> No blueprint specifies the administrative routes of the Domains,
> Programme objectives or Federation groups, telemetry's SLO status, or
> `/v1/admin/metrics` and `/v1/admin/agents/{name}/metrics`.
> [`architecture/programme-service`](programme-service.md#execution) names
> execution as the provider of the two workflow routes, on a pass carrying
> `admin:read`, and no execution blueprint specifies them yet. Of the owners
> whose decisions the inbox would list, content alone specifies a list a pass
> may reach, and no `PassRoute` can yet name the inbox group that list answers
> ([`protocol/types`](../protocol/types.md#passroute)), so the inbox is
> answered `ADMIN_GROUP_UNAVAILABLE` until one can. [`protocol/federation`](../protocol/federation.md) declares no `/v1/admin/`
> route. Three blueprints do specify routes under `/v1/admin/` that another
> component serves: `GET /v1/admin/alerts`, `/v1/admin/alerts/{id}` and
> `/v1/admin/alerts/stats` in [`agents/alerting`](../agents/alerting.md), the
> five `/v1/admin/runbooks` routes in
> [`agents/incident-response`](../agents/incident-response.md), and the four
> `/v1/admin/rate-limits` routes in
> [`patterns/rate-limiting`](../patterns/rate-limiting.md). Each says that its
> provider refuses a person's operator token with `PASS_REQUIRED`, and none
> that it accepts a pass or checks one's `aud`. Until a provider's blueprint specifies both a
> route and that it accepts a pass for it, and so declares it among its
> manifest's `pass_routes` ([`protocol/types`](../protocol/types.md#passroute)),
> as `admin-gateway-authorization` requires, the gateway answers that route
> `ADMIN_GROUP_UNAVAILABLE`, as it answers one whose provider is not deployed,
> those twelve routes included. A route with the minimum `admin` needs no exception once it is
> specified: its pass carries `admin:*` to that provider alone, which reaches
> no route of the orchestrator's
> ([`protocol/identity`](../protocol/identity.md#the-pass)).

> **Gap — any registrant can make a route unavailable to people.** A route
> two directory entries declare among their `pass_routes` names no one
> provider, so the gateway answers it `ADMIN_GROUP_UNAVAILABLE` and sends no
> pass for it (`admin-gateway-authorization`). A registration is not an
> enrolment ([`protocol/spec`](../protocol/spec.md#post-v1register)), so any
> registrant can declare a route another component's blueprint specifies,
> `architecture/content`'s or `architecture/fabric`'s among them, and cut every
> person off from that route for as long as it stays registered. While the
> component whose blueprint specifies the route is registered, that denial is
> all it gains. While that component is not registered, because it is not
> deployed, is restarting or was deregistered, the squatter's entry is the only
> one declaring the route, so the gateway exchanges passes addressed to the
> squatter and sends it people's requests for that route: a write's bytes, a
> decision, a read it can answer with documents of its own
> ([`architecture/threat-model`](threat-model.md), vectors 2.12 and 2.13). A
> pass addressed to it reaches no other component. The gateway sends one only
> to an address on the orchestrator's host or one the tenant declared, and no
> address can be declared yet
> ([`architecture/orchestrator`](orchestrator.md#what-the-directory-attests-and-what-it-does-not),
> the gap there), so the squatter must listen on the orchestrator's host: the
> same-host position the threat model records as residual, and no wider.
> Binding each route to the one component the tenant declares for it closes
> this, and waits on the tenant being able to declare its components.
> Refusing the second declaration at registration would only move the denial
> to whoever registers first.

### Operator Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/operators/register` | POST | — | Register new operator (the first presents the bootstrap secret) |
| `/v1/admin/operators/token` | POST | — | Obtain an attestation token by signing `{hub_id, jti, name, timestamp}` with the identity, `hub_id` the one the client recorded and `jti` fresh for each request. Deprecated as a way to an operator token |
| `/v1/admin/credentials/challenge` | POST | — | Issue a single-use nonce for a credential |
| `/v1/admin/credentials/token` | POST | — | Obtain an operator token by signing the nonce with the credential |
| `/v1/admin/operators/{name}/key` | POST | — | Change the operator's identity key, signed by the current key and the new one. Keeps the operator and its identity id, and revokes its credentials |
| `/v1/admin/hub/proof` | POST | — | Prove, by a signature under the key `hub_id` names, that this hub is reached at one of its admin addresses ([Proving the hub at an address](#proving-the-hub-at-an-address)) |
| `/v1/admin/operators/{name}/credentials` | POST | the operator | Attest a credential (an attestation token, or the operator's own token) |
| `/v1/admin/operators/{name}/credentials` | GET | viewer+ | List an operator's credentials, revoked included |
| `/v1/admin/operators/{name}/credentials/{cid}` | DELETE | the operator, or admin | Revoke one credential |
| `/v1/admin/operators` | GET | admin | List all operators |
| `/v1/admin/operators/{name}` | GET | viewer+ | Get operator details |
| `/v1/admin/operators/{name}` | DELETE | admin | Remove an operator: its status becomes `revoked`, its record stays, and its credentials are revoked. After step-up (`destructive-action-step-up`) |
| `/v1/admin/operators/{name}/approve` | POST | admin | Admit a registered operator (see *Admitting the operators after the first*). After step-up |
| `/v1/admin/operators/{name}/role` | PUT | admin | Change operator role. After step-up |

### System Overview

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/overview` | GET | viewer+ | System summary — the orchestrator's agents, namespaces and audit depth, and every other group from its provider or reported unavailable ([GET /v1/admin/overview](#get-v1adminoverview)) |
| `/v1/admin/metrics` | GET | viewer+ | Aggregated system metrics. No provider's blueprint specifies it, so the gateway answers it `ADMIN_GROUP_UNAVAILABLE` (the gap under [The admin API is an aggregate](#the-admin-api-is-an-aggregate)) |

### Agent Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/agents` | GET | viewer+ | List all agents with what the orchestrator's registry holds of each: name, type, version, `lease_state`, `registered_at` and `last_seen`. No metrics: they are another component's (below), and the orchestrator reports no figure it does not hold |
| `/v1/admin/agents/{name}` | GET | viewer+ | Agent detail — the orchestrator's registry entry for it without its token: `manifest`, `agent_id`, `lease`, `last_renewal`, `registered_at` and `last_seen` ([below](#get-v1adminagentsname)). No metrics and no recent tasks: the orchestrator holds neither and handles no task |
| `/v1/admin/agents/{name}/deregister` | POST | admin | Force-deregister an agent, after step-up (`destructive-action-step-up`) |
| `/v1/admin/agents/{name}/metrics` | GET | viewer+ | Agent performance metrics history. A component's runtime signal is telemetry's, not the orchestrator's, and no blueprint specifies this route, so the gateway answers it `ADMIN_GROUP_UNAVAILABLE` |

### Domain & Workflow Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/domains` | GET | viewer+ | List domains with status, required agent availability |
| `/v1/admin/domains/{name}` | GET | viewer+ | Domain detail — workflows, agents, recent executions |
| `/v1/admin/workflows` | GET | viewer+ | List all workflow executions (paginated) |
| `/v1/admin/workflows/{id}` | GET | viewer+ | Workflow execution detail — phases, timing, output |

### Programme Objectives

A strategy is retired: what a tenant aims at is a programme's objective, held
by the programme service with the programme that declares it. No blueprint
specifies objectives or a route for them yet, so this surface has none, and
the overview reports them unavailable. They will be the programme service's
routes, reached on a pass like any provider's.

### Decision Inbox

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/approvals` | GET | viewer+ | The one decision inbox: every decision a person may make, from each owner that holds one open, composed by the admin gateway |

**Each owner serves its own decisions, and the gateway composes one inbox from
them** ([`architecture/programme-service`](programme-service.md#the-decision-inbox)).
There is no approval service and no recommendation queue. The gateway learns
which route lists an owner's open decisions from the service directory alone,
as it learns every route it carries (`admin-gateway-authorization`), and asks
each owner on a pass, as it would ask for an overview figure: content's open
proposals at `GET /v1/content/proposals` on a pass naming `content:read`, and
execution's waiting steps once its blueprint specifies them. That needs a
`PassRoute` that can name the inbox group a route answers, and none can yet
([`protocol/types`](../protocol/types.md#passroute)), so a conforming gateway
asks no owner and answers the inbox `ADMIN_GROUP_UNAVAILABLE` (the gap under
[The admin API is an aggregate](#the-admin-api-is-an-aggregate)). Once one can,
the answer carries `items`, each with its `owner`, `record`, the record the
owner returned for that decision, unchanged (for content a `ContentProposal`
without bytes), and `decide`, the method and route at which it is decided;
`withheld`, each owner's own count of the decisions it omitted because this
person may not read them (content's `ProposalPage.withheld`); and
`unavailable`, naming each owner the gateway could not ask with the code it
would answer for that owner's route. The gateway writes no summary of its own:
a client renders an item from its owner's record, as the CLI renders a
content proposal's `change`. A list the gateway could not complete, or from
which an owner withheld any decision, MUST NOT be reported as empty or
complete. <!-- wl:id inbox-never-quietly-empty -->

**A decision is made at its owner, never here.** The gateway MUST serve no
route that decides. <!-- wl:id inbox-decides-nothing --> A person decides on their own
pass at the route `decide` names, such as content's
`POST /v1/content/proposals/{id}/decision` with `content:decide`, and the
owner records it. The shape of a decision is
[`patterns/approval`](../patterns/approval.md)'s. Where a tenant declares that a
decision needs more than one person, by `patterns/approval`'s multi-party or
content's `self_decision_ceiling`, the owner holds it open until that rule is
met, and the inbox lists it to each person who may still decide it. The
platform asks no second person of its own.

### Federation Management

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/federation/peers` | GET | viewer+ | List federation peers with trust tier, status |
| `/v1/admin/federation/peers/{name}` | GET | viewer+ | Peer detail — capabilities, data contracts, metrics |
| `/v1/admin/federation/peers/{name}/revoke` | POST | admin | Revoke trust relationship, after step-up (`destructive-action-step-up`) |
| `/v1/admin/federation/pending` | GET | operator+ | List pending peering requests |
| `/v1/admin/federation/pending/{id}` | POST | admin | Accept or reject peering request |
| `/v1/admin/federation/contracts` | GET | viewer+ | List active data contracts |

### Audit

| Path | Method | Role | Purpose |
|------|--------|------|---------|
| `/v1/admin/audit` | GET | auditor+ | Full audit log with filtering |
| `/v1/admin/audit/export` | GET | auditor | Export audit log as JSON or CSV |

Observations are retired as a word and as a store: the runtime signal is
telemetry's, and what a programme measures is its objective.

---

## Admin API Response Shapes

### GET /v1/admin/overview

The admin gateway answers this route with the System overview it composes
(`admin-gateway-authorization`). The members the orchestrator holds come from
its own `GET /v1/admin/overview`, which the gateway forwards as it forwards any
request for the orchestrator's groups: `deployment`, `version`, `uptime`,
`agents` (how many are registered, by lease state — `ready`, `not_ready`
and `unknown`, [`protocol/types`](../protocol/types.md#leasestate) — and in `by_type` by the
manifest's `type`, an absent `type` counted as `agent`), `namespaces` (how
many namespaces are owned) and `audit.depth` (how many entries its audit log
holds). The orchestrator answers its
own route with these members and no other, each named and shaped as the
example below gives it, and this section is the one statement of their names
and shapes ([`architecture/orchestrator`](orchestrator.md#administrative-endpoints)
says only that it reports what it holds). A refusal of that request is the
answer, as on any route of the orchestrator's groups.

Every other member but `timestamp` is a group another component holds:
`domains`, `workflows`, `approvals`, the decision inbox's count of open
decisions ([Decision Inbox](#decision-inbox)), `federation`, and `objectives`,
the programme service's programme objectives. Each is
either the figures that component's blueprint specifies for it, asked of it on
a pass, or, where the gateway may not ask or the asking fails, an object
carrying `unavailable` alone, whose value is the code the gateway would answer
a request for that group's route with. A figure the gateway cannot report is
never a number, so a client cannot render it as zero, and an absent provider is
never shown as a quiet one. No blueprint yet specifies a figure for one of
those groups on a pass, content's open proposals included, which it lists and
never counts (the gap under
[The admin API is an aggregate](#the-admin-api-is-an-aggregate)), and no
`PassRoute` can yet name the group a route answers
([`protocol/types`](../protocol/types.md#passroute)), so a conforming gateway
asks no component and answers each of them unavailable. `timestamp` is the
gateway's own: when it composed the answer. The
orchestrator's answer carries none:

```json
{
  "deployment": "acme-corp",
  "version": "1.0.0",
  "uptime": 86400,
  "agents": {
    "total": 8,
    "ready": 7,
    "not_ready": 1,
    "unknown": 0,
    "by_type": {"domain": 3, "agent": 3, "infrastructure": 2}
  },
  "namespaces": 6,
  "audit": {"depth": 18342},
  "domains": {"unavailable": "ADMIN_GROUP_UNAVAILABLE"},
  "workflows": {"unavailable": "ADMIN_GROUP_UNAVAILABLE"},
  "approvals": {"unavailable": "ADMIN_GROUP_UNAVAILABLE"},
  "federation": {"unavailable": "ADMIN_GROUP_UNAVAILABLE"},
  "objectives": {"unavailable": "ADMIN_GROUP_UNAVAILABLE"},
  "timestamp": "2024-04-03T16:00:00.000Z"
}
```

### GET /v1/admin/agents

```json
{
  "agents": [
    {
      "name": "seo-analyzer",
      "type": "agent",
      "version": "1.0.0",
      "lease_state": "ready",
      "registered_at": "2024-04-02T16:00:00.000Z",
      "last_seen": "2024-04-03T15:58:20.000Z"
    }
  ],
  "pagination": {
    "next_cursor": "",
    "has_more": false
  }
}
```

### GET /v1/admin/agents/{name}

The orchestrator's registry entry for the agent
([`architecture/orchestrator`](orchestrator.md#agententry), `AgentEntry`),
never with its `token`:

```json
{
  "manifest": {
    "name": "seo-analyzer",
    "type": "agent",
    "version": "1.0.0",
    "description": "Analyses HTML pages for search engine optimisation",
    "url": "http://localhost:9801",
    "public_key": "<ML-DSA-65 public key (base64url)>",
    "capabilities": [
      {"name": "file:read", "resources": ["**/*.html"]},
      {"name": "llm:chat", "resources": []}
    ]
  },
  "agent_id": "3f9a1c2e7b4d4e0f8a6b5c1d2e3f4a5b",
  "lease": {
    "agent_id": "3f9a1c2e7b4d4e0f8a6b5c1d2e3f4a5b",
    "duration": 30,
    "renewed_at": "2024-04-03T15:58:10.000Z",
    "expires_at": "2024-04-03T15:58:40.000Z"
  },
  "last_renewal": {"ready": true, "timestamp": "2024-04-03T15:58:10.000Z"},
  "registered_at": "2024-04-02T16:00:00.000Z",
  "last_seen": "2024-04-03T15:58:20.000Z"
}
```

### GET /v1/admin/workflows

```json
{
  "executions": [
    {
      "id": "exec-a1b2c3",
      "workflow_name": "seo-audit",
      "domain_name": "seo",
      "task_id": "task-d4e5f6",
      "status": "completed",
      "phases": [
        {"phase_name": "scan", "agent_name": "seo-analyzer", "status": "completed", "duration_ms": 1200},
        {"phase_name": "analyze", "agent_name": "seo-analyzer", "status": "completed", "duration_ms": 3800},
        {"phase_name": "accessibility", "agent_name": "a11y-checker", "status": "completed", "duration_ms": 1500},
        {"phase_name": "report", "agent_name": "seo-analyzer", "status": "completed", "duration_ms": 2000}
      ],
      "started_at": "2024-04-03T15:50:00.000Z",
      "completed_at": "2024-04-03T15:50:09.000Z",
      "duration_ms": 8500
    }
  ],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true
  }
}
```

### GET /v1/admin/operators/{name}/credentials

Every credential the operator's identity attested at this hub, revoked and
expired included, so a person can tell which device a credential is before
revoking it. Each entry is the stored
[`Credential`](../patterns/principal-identity.md#types) with its `cid`, and the
attestation's `device_label`, `purpose` and `not_after` lifted out for reading.
A sign-records credential is listed beside the ones that sign in, with its
`purpose`, and never has a `last_used_at`, because it never mints.

```json
{
  "credentials": [
    {
      "cid": "<fingerprint of credential_public_key>",
      "device_label": "console on build-01",
      "purpose": "authenticate",
      "algorithm": "ml-dsa-65",
      "form": "key-file",
      "device_bound": false,
      "status": "active",
      "not_after": 1714752000,
      "last_used_at": "2024-04-03T16:00:00.000Z"
    }
  ]
}
```

---

## Operator Storage

The orchestrator stores operator records alongside agent records:

### Store: Operators

**Owner:** Orchestrator
**Durability:** MUST survive restarts <!-- wl:id store-operators-durable -->

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutOperator | `(op Operator) → error` | Create or update operator |
| GetOperator | `(name string) → (Operator, error)` | Retrieve by name |
| RevokeOperator | `(name string) → error` | Set status `revoked`, keeping the record. The name is not reused |
| ListOperators | `() → ([]Operator, error)` | List all operators, revoked included |

### Store: Credentials

**Owner:** Orchestrator
**Durability:** MUST survive restarts. A revoked credential is kept, so its key
is never accepted again <!-- wl:id store-credentials-durable -->

| Operation | Signature | Description |
|-----------|-----------|-------------|
| PutCredential | `(c Credential) → error` | Create a credential, or replace an active one's attestation |
| GetCredential | `(id string) → (Credential, error)` | Retrieve by id, the fingerprint of its public key |
| ListCredentials | `(identityID string) → ([]Credential, error)` | Every credential one identity attested here, revoked included |
| RevokeCredential | `(id string) → error` | Set status revoked, keeping the record |

`Credential` is [`patterns/principal-identity`](../patterns/principal-identity.md)'s
type.

### Store: Token request jtis

**Owner:** Orchestrator
**Durability:** MUST survive restarts and be shared by every instance that
answers for this hub. A record lives until its request's `timestamp` leaves
the 300-second replay window, at most 600 seconds, and is then deleted <!-- wl:id store-jti-durable -->

| Operation | Signature | Description |
|-----------|-----------|-------------|
| RecordTokenRequest | `(identityID string, jti string, until time) → (recorded bool, error)` | One atomic check-and-put: `false` where the pair is already recorded and unexpired, which is `TOKEN_REQUEST_REPLAYED`. An error refuses the request with `STORAGE_ERROR` and issues no token |
| ExpireTokenRequests | `(now time) → error` | Delete every record whose `until` has passed |

The rules are `attestation-token-issuance`'s, in [Contracts](#contracts),
including the bound `auth-route-rate-limit` puts on what one source can make
this store hold.

A challenge nonce is not stored here: it lives at most 300 seconds, and an
orchestrator MAY keep it in memory only, so a restart discards the outstanding
ones and a client asks again.

### Operator Record

The record is [`protocol/types`](../protocol/types.md#operator)'s `Operator`,
and its status is `pending`, `approved` or `revoked`
([`OperatorStatus`](../protocol/types.md#operatorstatus)). It holds no token:
nothing a hub issues is stored by the hub, and a credential is a record of its
own, above.

---

## Bootstrap Flow

When an orchestrator starts with no registered operators:

```
1. Orchestrator starts and detects empty operator store
2. It generates a bootstrap secret and emits it once, where only whoever
   started it can read it: in .weblisk/bootstrap, readable only by the user
   it runs as, and on its terminal when its standard error is one. Never in
   a log file, a journal or captured output, which outlive the claim
3. It prints how to claim it:
   "Run: weblisk operator init && weblisk operator register --bootstrap <file>"
4. The first POST /v1/admin/operators/register that carries the secret is
   approved as admin, and the secret is destroyed
5. That operator receives an attestation token, attests a credential, and mints
   operator tokens with it
6. Subsequent operator registrations require admin approval
```

This is secure because:
- Reaching the endpoint first confers nothing. Only the secret admits, and it
  was emitted only to whoever started the orchestrator
  ([`patterns/principal-identity`](../patterns/principal-identity.md), *Bootstrap
  is trust-on-first-use*, is the rule this satisfies)
- The window closes when the secret is claimed, and does not reopen while any
  operator record exists
- All subsequent operators require explicit admin approval
- The bootstrap event is permanently recorded in the audit log

`first-operator-claim` in [Contracts](#contracts) is the rule. A tool that
starts the orchestrator itself, as `weblisk tenant create` does, reads the
secret from where it was emitted and claims it in the same action.

### Bootstrapping and connecting are different acts

They were conflated once, and the conflation is worth naming because it reads
as a small thing and is not.

**Bootstrap** creates a hub: generate it, build it, start it, and establish its
first operator. It needs the tenant's filesystem, because it is producing the
tenant. It is necessarily local to wherever that tenant is being built.

**Connect** presents a credential to a hub that is already running. It needs an
ADDRESS and an operator identity, and nothing else — no workspace selected, no
project directory on the caller's machine, no run state some tool happened to
record. A hub on another host, in a container, or started by something other
than the tool now connecting to it MUST be reachable on exactly the same terms
as one in the next directory. <!-- wl:id connect-address-only -->

A console that required a local project directory in order to connect made
"connect" mean "connect to a hub I built here". That inverts the relationship
the whole architecture rests on: a console is a CLIENT of a hub, over the hub's
own services, and a client that needs the server's filesystem is not a client.

Connecting therefore has outcomes that MUST be told apart.
[`architecture/cli`](cli.md#weblisk-operator-connect) names them all, and this
document does not restate them. Two matter to the hub: a hub that will not
issue a token yet leaves the operator **pending approval**, which is not a
failure — the first operator of a hub is admitted by the bootstrap secret,
every later one requires an existing admin, and the report MUST name who can
act — and a hub that does not serve the token endpoint is **unreachable**,
never pending. <!-- wl:id connect-outcomes-distinct -->

The second matters most. A hub that predates
`POST /v1/admin/operators/token` answers `404` or `405`, and reporting that as
"pending approval" tells somebody to wait for an approval that is never coming.
An implementation MUST NOT collapse a missing endpoint into an authorisation
state. <!-- wl:id missing-endpoint-not-pending -->

**Asking for a token before attempting registration is required, not an
optimisation.** A client that holds a credential at the hub mints with it; one
that holds none, where this device has recorded a registration for that
address, asks for an attestation token, and the answer says whether the hub
knows this operator. There, a hub that already knows the operator needs no
registration; a device that has recorded none for the address asks for no
token, and needs a registration, which a hub that knows the operator answers as
a repeat. Connecting never sends one: registering is its own act
([`architecture/cli`](cli.md#weblisk-operator-register)), so connecting never
claims a hub. At a hub with no operators, a registration without the bootstrap
secret is refused; only presenting the secret claims one.

### Bootstrap without a shell

Step 3 above tells a person to run two commands. A console provisioning a
tenant on behalf of a signed-in user has no shell to run them in, and
[`protocol/identity`](../protocol/identity.md) already names this case: *"a
runtime without [a terminal] cannot, and a specification that says prompt has
excluded it."*

The same steps MAY therefore be driven by one gated action instead of a person.
Nothing about the trust model changes: the first operator is still admitted
by presenting the bootstrap secret, every later one still requires an existing
admin, and the bootstrap is still recorded in the audit log. What changes is
who types.

Four rules govern it, and each exists because its absence is a disclosure:

1. **The passphrase MUST NOT be a command-line argument.** `argv` is readable by
   every process on the machine — `ps` shows it, `/proc/<pid>/cmdline` shows it,
   and a shell usually records it. It arrives on a channel that does not echo,
   persist or log it; a password field over TLS is such a channel, and stdin is
   how it reaches the process. <!-- wl:id passphrase-not-argv -->

2. **The operator key location MUST be parameterisable, and MUST be derived
   from the subject by ONE mechanism.** One machine may serve several operator
   identities, and a console with more than one signed-in account cannot share a
   single key file: the second account would use the first account's identity or
   overwrite it. An identity belongs to a subject, not to a machine and not to a
   tenant. <!-- wl:id key-location-parameterised -->

   Parameterising it is not enough on its own. A location is a path, and if
   every caller works out its own path then the rule exists in as many places as
   there are callers — a console derived one privately, and anything else
   driving the CLI had to reproduce it by hand. The CLI MUST accept an identity
   by label and resolve the location itself, and MUST be able to report where a
   given identity lives, so a caller can ask instead of deriving. An explicit
   path remains accepted and outranks the label, because an operator who gives
   one means it. <!-- wl:id identity-by-label -->

   That label is NOT the operator's name, and the two MUST NOT be collapsed
   into one argument. The name is hub-facing — recorded in the orchestrator's
   audit log and shown to other operators — while the label selects which key on
   this machine signs. A console signs in an account whose id may be an email
   and registers it on a hub under a chosen display name; merging them forces
   one to become the other. `architecture/cli` names the first `--name` and the
   explicit path `--keys-dir`. <!-- wl:id label-not-name -->

   The label MUST NOT appear verbatim in the path: an account id may be an
   email, and an email in a directory name is a disclosure to anything that can
   list the parent. <!-- wl:id label-not-in-path -->

3. **Provisioning MUST reuse an existing identity rather than replace one.** A
   subject holds one identity and a separate credential at each hub, attested by
   that identity, so minting a new key while provisioning a second tenant would
   silently orphan
   the grant every earlier tenant recorded. A passphrase that does not open an
   existing identity is an error, not a reason to generate another. <!-- wl:id provision-reuses-identity -->

4. **Provisioning MUST be re-runnable.** A console retrying after a network
   error must not be told the tenant is broken by the step that already
   succeeded. Already-registered is reported as already-registered, and the
   action proceeds to obtain a token. <!-- wl:id provision-rerunnable -->

Nothing it obtains persists except a credential's key. The passphrase is
discarded with the process, per [`protocol/identity`](../protocol/identity.md)
rule 4, and a console holds its tokens in memory
([A console holds a credential, never a token](#a-console-holds-a-credential-never-a-token)).

---

## Types

```yaml
types:

  OperatorAuth:
    description: The conditions under which an operator may authenticate to the admin surface
    fields:
      operator_key:
        type: string
        format: base64url
        description: The operator's identity public key, against which registration and attestations are verified. Tokens are minted with credentials, never with this key
      mfa_required:
        type: bool
        description: Whether a second factor is required. The admin surface requires one without exception, where each key is opened — see Where the second factor is — and never as a claim in a token
      ip_allowlist:
        type: array
        items: string
        description: Networks the operator may authenticate from. An empty list means no network restriction, which is a decision rather than a default
```

---

## Security


```yaml
security:
  trust_model:
    description: |
      The admin surface is a separate listener from the application gateway,
      sharing no listener, domain or certificate, so compromising one does not
      reach the other. Every request is authenticated by a token minted with a
      credential the operator's identity attested, re-checked against the
      orchestrator's records, and authorised against what the operator's role
      carries now, never beyond the token's cap; multi-factor
      authentication is required without exception, where the identity key
      and the credential key are opened, because an operator credential is the
      most valuable one in a deployment. The identity key signs to register, to
      attest, to change itself and to re-confirm for a destructive act, and is
      never a login.

  boundaries:
    - boundary: A person's client → Admin gateway. A separate TLS entry point,
        authenticated per request against the orchestrator's key
    - boundary: Admin gateway → Providers. Forwards a request for the
        orchestrator's groups on the person's own token, and sends one for any
        other provider on a pass addressed to that provider alone; its own
        registration exchanges and reads the directory, and it does not reach
        past a provider into a store
    - boundary: Operator capability → Action. Every endpoint declares a minimum
        role, which stands for a capability the request must be able to use,
        judged by the orchestrator before any handler runs, whichever
        component serves it
    - boundary: Destructive action → Effect. Crossed only on the person's own
        re-confirmation within 300 seconds, judged by the component that serves
        the act (destructive-action-step-up)

  enforcement:
    - rule: Every admin endpoint requires a verified operator token, whichever
        component serves it, except registration, the attestation token
        request, the two credential routes that issue tokens, the hub proof,
        which a client asks before it holds anything, and the change of an
        operator's identity key, which its two signatures authenticate.
        Attesting a credential also accepts an attestation token for the same
        operator
      mechanism: The orchestrator's Auth Middleware verifies the token against
        its own public key and checks `type == operator` before dispatch; any
        other provider acts only on a pass addressed to it, which the token
        exchange mints for a verified, live operator token alone
        (admin-gateway-authorization)
    - rule: A token is refused as soon as what it rests on is withdrawn
      mechanism: The orchestrator looks up the operator and the credential named
        by the token on every request, and authorises against what the role the
        operator holds now carries, narrowed by the token's cap
    - rule: An endpoint is refused to a request that cannot use the capability
        its declared minimum stands for, whatever the role
      mechanism: The orchestrator's judgement, in its Auth Middleware or at the
        token exchange, which mints no pass for a capability the person may not
        use (admin-gateway-authorization); 403 rather than a partial result
    - rule: The auditor role cannot approve or mutate
      mechanism: Auditor carries viewer permissions plus audit read, and no
        approval or management capability — it is a branch of the hierarchy
        rather than a rank within it
    - rule: Multi-factor authentication cannot be disabled
      mechanism: An identity key signs only once its passphrase or its secret
        source opens it (protocol/identity rule 1), and a client keeps a
        credential key only where it signs after the person's own act. No
        configuration removes either
    - rule: A destructive action requires the person's own step-up, never a
        second person
      mechanism: The component that serves the act refuses it with
        STEP_UP_REQUIRED unless the token or pass carries a step_up_at no more
        than 300 seconds old, which the orchestrator sets only on a token
        minted through a re-confirmation it verified (destructive-action-step-up)
    - rule: Every admin action is attributable
      mechanism: Audit records operator, action, target and time before the
        action takes effect
```
### Auth Middleware

Every `/v1/admin/*` endpoint the orchestrator provides passes its
[Auth Middleware](orchestrator.md#auth-middleware), which is the one sequence
for them, except `POST /v1/admin/operators/register`,
`POST /v1/admin/operators/token`, `POST /v1/admin/credentials/challenge`,
`POST /v1/admin/credentials/token`, `POST /v1/admin/hub/proof`, which a client
asks before it holds anything here, and `POST /v1/admin/operators/{name}/key`,
which the operator's current and new identity keys sign. That sequence reads
the token from the `Authorization` header alone, verifies it and its expiry,
admits an operator token (and an attestation token on the attestation route
only, for the operator the path names), checks that the operator and
credential it names are live (token-status-on-use), and then checks the
capability, which is this document's to define. An endpoint another component
provides never reaches that sequence. The orchestrator makes the same
judgement at the token exchange, before the admin gateway sends the request
there on a pass, and that component acts on the pass's `cap` alone
(`admin-gateway-authorization` in [Contracts](#contracts)). Either way, for an
administrative route, the rule is this one, and a route of a service such as
`architecture/content`'s is judged the same way against every capability its
provider requires for the request, its body's included:

**The request must be able to use the capability the endpoint's minimum stands
for** (the table below): one the operator's role carries now and the token's
`cap` names. Otherwise `FORBIDDEN`, whatever the role. An operator token whose
`cap` is absent or empty names no capability, so it can use none of these
endpoints, and never stands for its role's full set. `admin:*` stands for
every `admin:` capability by name, on both sides: a role carrying `admin:*`
carries `admin:read`, `admin:approve`, `admin:strategy` and `admin:audit`, so
an admin's token whose `cap` names only `admin:read` can use `admin:read`; and
a `cap` naming `admin:*` names each of them, so it keeps whichever the role
carries ([operator-token-issuance](#contracts)). A request can use `admin:*`
when it can use every capability of the `admin` family by name: a token whose
`cap` names `admin:read`, `admin:approve`, `admin:strategy` and `admin:audit`
can use it as one whose `cap` names `admin:*` can. The token exchange reads a
`scope` naming `admin:*` the same way, and a pass carries `admin:*` only where
the person may use all four.

A role in the endpoint tables names the least role, and stands for a
capability ([`protocol/types`](../protocol/types.md), Administrative
capabilities). The request must be able to use that capability, so a token
whose `cap` leaves it out reaches none of these routes, an admin's included,
and a pass carries every capability its request requires and nothing more
([A console holds a credential, never a token](#a-console-holds-a-credential-never-a-token)):

| Minimum | The request must be able to use |
|---|---|
| `viewer+` | `admin:read` |
| `auditor+`, `auditor` | `admin:audit` |
| `operator+` | `admin:approve`. Programme Objectives specifies no route, so `admin:strategy` gates none here |
| `admin` | `admin:*` |
| the operator | `admin:read`, on a token whose `sub` is the operator the path names. An attestation token, which carries no capability, is admitted only where Operator Management says so |
| the operator, or admin | `admin:read` on the named operator's own token, or `admin:*` |

### Role Hierarchy

```
admin > operator > auditor > viewer
```

An admin can do everything an operator can do, and so on. The `auditor`
role is a special branch — it has viewer permissions plus full audit
log access, but cannot decide or manage anything.

### Audit Trail

Every admin action is logged:

```json
{
  "id": "audit-abc123",
  "timestamp": "2024-04-03T16:00:00.000Z",
  "actor": "<the operator's identity_id>",
  "actor_type": "operator",
  "action": "deregister",
  "target": "seo-analyzer",
  "detail": "Force-deregistered on a step-up 42 seconds old",
  "ip": "192.168.1.100"
}
```

### Rate Limiting

The auth endpoints MUST be rate-limited before any signature is verified or
made, at 5 requests a minute per source for each of the routes served without
a token, none of which carries an operator token to count against. Each
verifies or makes an ML-DSA-65 signature, and the key-change and proof routes
admit a request with no token at all, so an unlimited one is an oracle and a
cost anybody can impose. Each route is counted on its own, so a person
minting a token is never refused for having changed a key. A **source** is the
client's IP address, as
[`patterns/rate-limiting`](../patterns/rate-limiting.md#identification-keys)
derives the IP key, never a name, `cid` or key in the request. <!-- wl:id auth-endpoints-limited -->

The admin gateway applies the limit at step 3 of the
[Admin Gateway Request Lifecycle](#admin-gateway-request-lifecycle), before
it forwards anything, and the orchestrator applies it again. Every request
the gateway forwards reaches the orchestrator from the gateway's own address,
which all its clients share, so the gateway names the client's address in
`X-Forwarded-For`, and the orchestrator trusts that header from the addresses
its configuration names as the gateway's and from nobody else. The behaviour
is `auth-route-rate-limit`, in [Contracts](#contracts), which says what an
orchestrator told of no such address does, and what sharing the gateway's
address with other callers costs.

The rest SHOULD be:
- Read endpoints: 60 requests/minute per operator
- Write endpoints: 20 requests/minute per operator
- Export endpoints: 5 requests/minute per operator

---

## Implementation Notes

- The admin gateway is a separate process from the application
  gateway. In Go deployments, it is a separate binary. In
  Cloudflare deployments, it is a separate Worker.
- A WebSocket at `/v1/admin/ws` for real-time status updates (agent status
  changes, new decisions, workflow completions) is a gap. The gateway holds
  no subscription and no standing access to data
  (`admin-gateway-authorization`), so it has nothing to feed one from, and
  no provider's blueprint specifies the feed or a pass for it. Until one
  does, the gateway answers a request for it as it answers any route that
  is not the orchestrator's and that no pass route declares, with
  `ADMIN_GROUP_UNAVAILABLE`, and a console refreshes by asking again
- All admin API responses include `Cache-Control: no-store` to prevent
  caching of sensitive operational data
- The admin interface MUST work over HTTPS in production. HTTP is
  NEVER permitted, even in development (use self-signed certs). <!-- wl:id admin-https-only -->
- The admin gateway and application gateway MUST NOT share a TLS
  certificate, a domain or a network listener. <!-- wl:id no-shared-tls -->
- Admin gateway logs are classified as Confidential (level 2) and
  are stored separately from application gateway logs.
- No header a gateway adds authorises anything or names who acted.
  The orchestrator authorises an administrative request by its operator
  token, and every other provider by the pass it arrived on, and each
  records who acted by the identity id that token or pass carries. An
  `X-Operator-*` or `X-Gateway-*` header on an administrative request
  is never read as either, and the admin gateway sends neither.

## Verification Checklist
- [ ] Authentication services — OIDC, password verification, credential storage, token minting — are used from `patterns/auth-*` and `patterns/user-management` and are not reimplemented for the admin path <!-- wl:check auth-services-reused covers auth-not-duplicated auth-stack-shared -->
- [ ] The admin listener, domain and certificate are all distinct from the application gateway's; nothing is shared between them <!-- wl:check listeners-separate covers no-shared-tls -->
- [ ] A grant held within a tenant confers no platform administrative capability <!-- wl:check tenant-grant-confers-nothing covers tenant-grant-not-platform -->
- [ ] Connecting to a hub requires only its address and an operator identity — no local project directory and no recorded run state <!-- wl:check connect-needs-address covers connect-address-only -->
- [ ] A token is requested BEFORE any registration is attempted, and connecting never sends a registration: registering is its own act (`architecture/cli`, `weblisk operator register`)
- [ ] A hub that refuses to register a new operator unauthenticated is reported as pending approval, naming who can act, and not as a failure <!-- wl:check connect-pending-reported covers connect-outcomes-distinct -->
- [ ] A hub that does not serve the token endpoint is reported as such, never as pending approval <!-- wl:check connect-missing-endpoint covers connect-outcomes-distinct missing-endpoint-not-pending -->
- [ ] Connecting is idempotent: where this device has recorded a registration for that address, running it against a hub that already knows the operator issues a token and changes nothing else
- [ ] A passphrase supplied as a command-line argument is REFUSED, and the refusal names stdin as the alternative <!-- wl:check passphrase-refused-in-argv covers passphrase-not-argv -->
- [ ] The operator key location is parameterisable, so two signed-in accounts on one machine hold separate identities <!-- wl:check key-location-separate covers key-location-parameterised -->
- [ ] Provisioning against an existing identity reuses it; a passphrase that does not open it is an error and no new key is generated <!-- wl:check provision-reuses covers provision-reuses-identity -->
- [ ] Provisioning is re-runnable: an already-registered operator proceeds to obtain a token rather than failing <!-- wl:check provision-reruns covers provision-rerunnable -->
- [ ] The passphrase is never written to disk, and a console never writes an operator token anywhere <!-- wl:check passphrase-and-token-unwritten covers console-token-in-memory -->
- [ ] A console that drives the CLI to connect, register or mint passes `--no-store` and never `--store`, and no token file is written, including where the CLI's mint asks the identity's holder <!-- wl:check console-passes-no-store covers console-no-store -->
- [ ] `POST /v1/admin/operators/token` issues an attestation token (`type` `attestation`, no `cap`, no `cid`, at most 300 seconds, with `hub_id` and the operator's `identity_id`) to an approved operator who signs `{hub_id, jti, name, timestamp}` with their identity key, and every route but `POST /v1/admin/operators/{name}/credentials` refuses that token with `CREDENTIAL_REQUIRED` <!-- wl:check attestation-token-issued covers attestation-route-no-token attestation-request-signed attestation-token-form attestation-token-scope attestation-answer-ids -->
- [ ] The signature is verified against the public key in the orchestrator's OWN operator record, never a directory <!-- wl:check signature-against-own-record covers directory-never-authenticates -->
- [ ] A token request outside the 300-second replay window is refused <!-- wl:check token-request-window covers attestation-request-signed -->
- [ ] A token request with no `jti`, or one that does not decode to between 16 and 64 bytes, is refused with `400` `INVALID_REQUEST` before its signature is checked; the same signed request sent twice is answered once and then refused with `TOKEN_REQUEST_REPLAYED`, issuing no token, and logged as a security event; of two concurrent requests carrying one `jti` exactly one is answered; a request whose signature does not verify records no `jti`, so the operator's own request with that `jti` is still answered <!-- wl:check token-request-jti covers attestation-jti-form attestation-replay -->
- [ ] A token request whose signature verifies, at a hub whose `jti` record cannot be read or written, is refused with `500` `STORAGE_ERROR` and issues no token; the record survives a restart of the orchestrator, and a request answered by one instance is refused as a replay by another instance answering for the same hub <!-- wl:check jti-record-durable covers attestation-replay store-jti-durable -->
- [ ] Two token requests from one identity in the same second carry different `jti`s and so different signed bytes, and both are answered <!-- wl:check jti-per-request covers attestation-jti-form -->
- [ ] A signed token request first refused with `CREDENTIAL_FOREIGN_HUB`, `OPERATOR_NOT_APPROVED` or `OPERATOR_REVOKED`, sent again to the same hub inside the replay window, is refused with `TOKEN_REQUEST_REPLAYED` <!-- wl:check refused-request-replayed covers attestation-replay -->
- [ ] A token request for a pending operator is refused with 403 `OPERATOR_NOT_APPROVED`, distinctly from an unknown operator (`OPERATOR_UNKNOWN`) <!-- wl:check pending-distinct-from-unknown covers attestation-status-after-signature -->
- [ ] Registration that also approves returns an attestation token, `hub_id`, `identity_id` and `status: approved`; registration that does not returns `status: pending`, `hub_id` and `identity_id`, and no token <!-- wl:check registration-answers covers registration-answer bootstrap-answer later-registration-needs-admin -->
- [ ] A registration repeating an operator's name and current identity key, with a fresh timestamp, is answered `200` with `hub_id` and `identity_id` alone, carrying no record, role, status or token and changing nothing, for a pending, an approved and a revoked operator alike; the same name with another key is refused with 409 <!-- wl:check registration-repeats covers registration-repeat registration-name-held -->
- [ ] `POST /v1/admin/operators/token` signed by an approved operator over another hub's `hub_id` is refused with `CREDENTIAL_FOREIGN_HUB`, issues no token and is logged as a security event, and one that carries a `jti` but whose signature is over `{name, timestamp}` or `{hub_id, name, timestamp}` is refused with `INVALID_SIGNATURE` <!-- wl:check token-request-foreign-hub covers attestation-request-signed attestation-foreign-hub registration-input-stated-exactly -->
- [ ] Until `weblisk/hub-proof/v1` has test vectors, every request to `POST /v1/admin/hub/proof` is answered `501` `HUB_PROOF_UNAVAILABLE`, and none with a signature. Once it has them, `POST /v1/admin/hub/proof` with no token, for an address `orchestrator.admin_addresses` lists and a challenge decoding to between 16 and 64 bytes, answers `200` with `hub_id`, a `public_key` whose fingerprint is `hub_id`, the address, and a signature by that key that verifies over `weblisk/hub-proof/v1`, `0x00`, `hub_id`, `0x00`, the address, `0x00` and the challenge <!-- wl:check hub-proof-answers covers hub-proof-route hub-proof-statement hub-proof-vectors-first -->
- [ ] Once `weblisk/hub-proof/v1` has test vectors, `POST /v1/admin/hub/proof` for an address `orchestrator.admin_addresses` does not list is refused with `HUB_ADDRESS_FOREIGN`, signs nothing and is logged as a security event, also where the request's `Host` or `X-Forwarded-Host` header names a listed address; an address with a path or a trailing `/`, and a challenge that is padded, not base64url, or decodes to fewer than 16 or more than 64 bytes, are refused with `400` `INVALID_REQUEST` and sign nothing <!-- wl:check hub-proof-foreign-address covers hub-proof-address-form hub-proof-admin-addresses -->
- [ ] Once `weblisk/hub-proof/v1` has test vectors, and after the orchestrator signs tokens with a key other than its first, `POST /v1/admin/hub/proof` still answers under the key whose fingerprint is its `hub_id`, and that key signs no token <!-- wl:check hub-proof-first-key covers hub-proof-key-kept -->
- [ ] A registered operator's `identity_id` is the fingerprint of the `public_key` its registration carried, and stays that value through every later change of identity key <!-- wl:check identity-id-is-first-key covers registration-identity-id -->
- [ ] After a change of identity key, `POST /v1/admin/operators/token` signed with the new key answers the operator's kept `identity_id`; an attestation naming that `identity_id` is accepted, and one naming the new key's fingerprint instead is refused with `CREDENTIAL_ATTESTATION_INVALID` <!-- wl:check identity-id-kept covers attestation-answer-ids attestation-names-identity -->
- [ ] Once `weblisk/credential-auth/v1` has test vectors, an expired operator token is replaced by a new challenge answered with the credential, without re-registering and without the identity <!-- wl:check token-renewed-by-credential covers renewal-without-identity client-uses-credential-routes -->
- [ ] Once `weblisk/credential-auth/v1` has test vectors, `POST /v1/admin/credentials/token` issues an operator token carrying `cid`, expiring one hour after issue and never after the attestation's `not_after`, only for a signature by the stored credential key over `weblisk/credential-auth/v1`, 0x00, `hub_id` as its 64 hex characters, 0x00 and the base64url text of a nonce this hub issued for that credential <!-- wl:check operator-token-from-credential covers credential-routes-no-token credential-answer-bytes operator-token-claims -->
- [ ] For every vector in [`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json) under `weblisk/credential-auth/v1`, the hub, which verifies a credential's answer and does not sign one, passes the test [`architecture/generation`](generation.md#published-test-vectors) gives for a component that verifies <!-- wl:check credential-auth-vectors covers credential-answer-bytes -->
- [ ] `POST /v1/admin/operators/token` never issues an operator token, whatever its request carries <!-- wl:check no-operator-token-from-identity covers client-uses-credential-routes -->
- [ ] A hub that rotates its orchestrator key answers every challenge with the `hub_id` it had before, and, once `weblisk/credential-auth/v1` has test vectors, every credential attested for that `hub_id` still mints
- [ ] A nonce from `POST /v1/admin/credentials/challenge` is spent by the first token request that presents it, whether or not the signature verifies, and a revoked or expired credential's status is disclosed only after its signature verifies <!-- wl:check nonce-spent-once covers nonce-spent credential-status-after-signature -->
- [ ] An attestation whose `hub_id` is not this hub's, whose credential key is not an ML-DSA-65 key, whose credential key is the identity key, whose `not_after` has passed or is more than 90 days away, or whose key was revoked here before is refused with `CREDENTIAL_FOREIGN_HUB`, `CREDENTIAL_FORM_UNSUPPORTED`, `CREDENTIAL_IS_IDENTITY_KEY`, `CREDENTIAL_LIFETIME_INVALID` or `CREDENTIAL_PREVIOUSLY_REVOKED` <!-- wl:check attestation-refusals covers credential-not-identity-key credential-lifetime credential-previously-revoked revoked-credential-kept -->
- [ ] An attestation with `purpose` `sign-records` is recorded under the same checks and 90-day cap as any other, appears in the operator's credential list, and can be revoked; a challenge or token request for its key is refused with `CREDENTIAL_PURPOSE_REFUSED` and no nonce is issued <!-- wl:check sign-records-attested covers challenge-refusals token-request-unknown-cid -->
- [ ] An attestation naming one purpose for a key this hub holds, or held and revoked, under the other is refused with `CREDENTIAL_PURPOSE_REFUSED` <!-- wl:check purpose-refused covers credential-one-purpose -->
- [ ] An operator attesting a key that is another operator's active, expired or revoked credential, or another operator's identity key, is refused with `CREDENTIAL_KEY_BOUND`; the other operator's credential keeps its operator and its attestation, and, once `weblisk/credential-auth/v1` has test vectors, their next token is minted for them <!-- wl:check key-bound-refused covers credential-key-bound -->
- [ ] Every operator token names in `record_keys` each active, unexpired sign-records credential its operator holds here, and a token minted after one is revoked does not name it <!-- wl:check record-keys-named covers operator-token-claims -->
- [ ] Revoking the last authenticate credential of the last active admin is refused with `OPERATOR_LAST_ADMINISTRATOR` whatever sign-records credentials that admin holds <!-- wl:check last-admin-credential-refused covers last-admin-credential -->
- [ ] A console holds no key attested with `purpose` `sign-records`, for any account <!-- wl:check console-holds-no-sign-records covers console-no-sign-records -->
- [ ] Removing an operator, or revoking one of its credentials, refuses its next request with `OPERATOR_REVOKED` or `CREDENTIAL_REVOKED` without waiting for its token to expire <!-- wl:check revocation-ends-tokens covers status-checked-on-use status-refusals revoked-credential-kept operator-removal-revokes -->
- [ ] A removed operator keeps its record with status `revoked`, and a request naming it is refused with `OPERATOR_REVOKED`, never `OPERATOR_UNKNOWN` <!-- wl:check removed-operator-kept covers status-refusals operator-removal-revokes -->
- [ ] The sole admin's change of identity key revokes their credentials and is not refused with `OPERATOR_LAST_ADMINISTRATOR`; the new identity then attests a credential and, once `weblisk/credential-auth/v1` has test vectors, mints <!-- wl:check sole-admin-key-change covers last-admin-key-change key-change-not-last-admin -->
- [ ] `POST /v1/admin/operators/{name}/key` signed by the recorded key and the new key over `canonicalize({hub_id, name, new_public_key, timestamp})` keeps the operator's name, role, status and `identity_id`, moves the old key to `retired_keys` with the time of the change as its `retired_at`, and revokes every credential; one whose `current_signature` is by any other key, apart from the repeat below, or that is replayed, is refused with `OPERATOR_KEY_CHANGE_INVALID` and changes nothing; one naming another hub's `hub_id` is refused with `CREDENTIAL_FOREIGN_HUB` <!-- wl:check key-change-applied covers key-change-revokes-credentials key-change-route key-change-request key-change-invalid key-change-write -->
- [ ] After a key change the hub accepted, the same change sent again with a fresh timestamp, signed by the key it retired and by the new key, is answered `200` with the same operator record, `identity_id` and `hub_id`, revokes nothing, leaves `retired_keys` as it was, and is audited as a repeat; with a `new_signature` that does not verify, or signed by a key retired before that change, it is refused with `OPERATOR_KEY_CHANGE_INVALID` <!-- wl:check key-change-repeated covers key-change-repeat -->
- [ ] A registration or a change of identity key offering a key this hub records or recorded as any identity key or credential is refused with `OPERATOR_KEY_REUSED` <!-- wl:check key-reuse-refused covers registration-key-reused key-change-key-reused -->
- [ ] An attestation whose credential key is one of the operator's own retired identity keys is refused with `CREDENTIAL_IS_IDENTITY_KEY` <!-- wl:check retired-key-not-credential covers credential-not-identity-key -->
- [ ] A change of identity key for a revoked operator whose signatures do not verify is refused with `OPERATOR_KEY_CHANGE_INVALID`, never `OPERATOR_REVOKED`; one whose signatures verify is refused with `OPERATOR_REVOKED` <!-- wl:check revoked-key-change covers key-change-invalid -->
- [ ] More than five requests a minute from one source to `POST /v1/admin/operators/{name}/key`, to `POST /v1/admin/hub/proof`, or to any of the four routes that issue tokens, are refused before any signature is verified or made <!-- wl:check auth-routes-five-a-minute covers auth-routes-limited auth-endpoints-limited -->
- [ ] `POST /v1/admin/hub/proof` with no bearer token passes the admin gateway's step 4 and the orchestrator's Auth Middleware to its handler, and is never refused for carrying no token
- [ ] A token minted after a change of identity key carries the same `identity_id` as one minted before it
- [ ] A role lowered after a token was issued limits that token from its next request <!-- wl:check lowered-role-limits-token covers role-now-narrowed-by-cap capabilities-from-role role-from-record -->
- [ ] An operator token without `cid` is refused with `CREDENTIAL_REQUIRED` <!-- wl:check cid-required-refused covers cid-required -->
- [ ] An admin's token minted with `cap` naming only `content:read`, `content:write` and `content:decide` is refused with `FORBIDDEN` at `POST /v1/admin/operators/{name}/approve`, `PUT /v1/admin/operators/{name}/role`, `DELETE /v1/admin/operators/{name}/credentials/{cid}` for another operator's credential and for the admin's own, `POST /v1/admin/operators/{name}/credentials` for the admin, and, at a provider that serves one, every `operator+` route, although the admin's role reaches each <!-- wl:check cap-narrows-admin covers route-capability-forbidden -->
- [ ] Every administrative route authorises against the capabilities the operator's role carries now narrowed to the token's `cap`, never against the role alone <!-- wl:check role-now-and-cap covers role-now-narrowed-by-cap -->
- [ ] `POST /v1/admin/operators/token` with a signature that does not verify is refused with `INVALID_SIGNATURE` for a pending or a revoked operator, and only a request whose signature verifies is told `OPERATOR_NOT_APPROVED` or `OPERATOR_REVOKED`
- [ ] The bootstrap secret is written to `.weblisk/bootstrap` readable only by the user the orchestrator runs as; an orchestrator whose standard error is not a terminal, such as one started detached or by a boot unit, writes it to no log, journal or output stream <!-- wl:check bootstrap-written-privately covers bootstrap-secret-written -->
- [ ] A console uses a person's credential only while that person has a live AAL2 session with it, never for work nobody is present for, and discards a person's tokens when their session ends <!-- wl:check console-session-bound covers console-credential-live-session console-no-unattended-work console-discards-tokens -->
- [ ] A console gives no agent a token minted with a person's credential, with or without `cap`. For a run whose person holds a live AAL2 session it sends only reads of the tenant's content and completions through the model route, each to the tenant's admin gateway on that person's token; it sends nothing for the run once that session ends; and a write, proposal or decision an agent prepared reaches a hub only in a request the person submits <!-- wl:check console-no-agent-token covers console-no-agent-token -->
- [ ] A console presents a person's token to the tenant's admin gateway alone. The content service receives a console's read on a pass whose `aud` is the content service and whose `cap` names only `content:read` or `content:describe`, never on the person's token, and never carrying an `admin:` capability <!-- wl:check console-token-to-gateway covers console-token-at-gateway -->
- [ ] A token request carrying `cap` receives a token carrying exactly the named capabilities its operator's role carries; a name the role does not carry is left out, and a request with no `cap` receives the role's full set <!-- wl:check cap-narrows-token covers role-from-record -->
- [ ] A token request whose `cap` names nothing the operator's role carries, such as a `viewer`'s or an `auditor`'s with `cap` `[fabric:attest]`, receives a token whose `cap` is the empty list. That token, and an operator token that carries no `cap` claim at all, is refused with `FORBIDDEN` at every route that requires a capability, and the token exchange answers it `issued: false` with `FORBIDDEN` for any `scope`, never minting a pass that carries the role's full set <!-- wl:check empty-cap-reaches-nothing covers operator-token-cap-always route-capability-forbidden -->
- [ ] An operator token carries `identity_id`, the `identity_id` of the credential its `cid` names <!-- wl:check token-identity-id covers operator-token-claims -->
- [ ] A `viewer` token carries `content:read` and `content:describe` and no other `content:` capability, and an `operator` token carries `content:write` and `content:decide` <!-- wl:check viewer-operator-content covers capability-roles-table -->
- [ ] Every capability this document names for a person's token is carried by at least one role in the Operator Roles table, and no role carries `token:exchange`, so no operator token's `cap` reaches it whatever it names <!-- wl:check every-capability-in-a-role covers every-capability-held -->
- [ ] An `operator` or `admin` token carries `fabric:read` and `fabric:attest`, a `viewer` or `auditor` token carries `fabric:read` and not `fabric:attest` <!-- wl:check fabric-by-role covers capability-roles-table -->
- [ ] An `admin` token carries `content:replicate` and `content:connect`, an `operator` token carries neither, and no token minted for a service subject carries either <!-- wl:check replicate-by-role covers capability-roles-table -->
- [ ] An `admin` token carries `content:declassify`, and an `operator`, `auditor` or `viewer` token, and every token minted for a service subject, does not <!-- wl:check declassify-by-role covers capability-roles-table -->
- [ ] Removing an account from a console deletes its credential keys, revokes each credential first with the token of a signed-in person that hub permits to revoke it where there is one, and otherwise reports each credential live at its hub until its `not_after` <!-- wl:check console-removal covers console-removal-deletes-keys console-removal-reports -->

- [ ] Admin gateway is a separate process/listener from the application gateway with its own TLS certificate and domain <!-- wl:check gateway-separate-process covers no-shared-tls -->
- [ ] Admin gateway rejects requests from IPs not in the operator allowlist before any processing (403, no body) <!-- wl:check allowlist-first covers admin-listener-guarded -->
- [ ] The first operator is approved as admin only on presenting the bootstrap secret; a registration at an empty hub without it, or with a wrong one, is refused with `OPERATOR_BOOTSTRAP_REFUSED` and writes nothing; subsequent operators require existing admin approval <!-- wl:check bootstrap-claims-first covers bootstrap-secret-presented bootstrap-refused bootstrap-claims-admin later-registration-needs-admin -->
- [ ] The bootstrap secret is destroyed when claimed, never appears in a response or an audit entry, and is not issued again while any operator record exists <!-- wl:check bootstrap-destroyed covers bootstrap-secret-never-shown bootstrap-secret-destroyed -->
- [ ] Two registrations presenting the bootstrap secret at once admit exactly one admin, and a restart before the claim replaces the emitted secret <!-- wl:check bootstrap-claimed-once covers bootstrap-claim-atomic bootstrap-secret-replaced -->
- [ ] Admin tokens are WLTs with a one-hour TTL, and a console ends a person's tokens when that person's session with it goes idle <!-- wl:check tokens-one-hour covers console-discards-tokens -->
- [ ] Two factors are required with no exception, where each key is opened: an identity key signs only once its passphrase or its secret source opens it, and a client keeps a credential key only in the `weblisk-key-v1` envelope, in a secret source, in the platform keychain source released only while the person's machine session is unlocked, or behind a console session at AAL2, never in the clear. No gateway checks a factor claim in a token <!-- wl:check two-factors covers credential-key-behind-act no-factor-claim -->
- [ ] Role hierarchy admin > operator > auditor > viewer is enforced server-side on every /v1/admin/* endpoint <!-- wl:check role-hierarchy covers approve-admin-only -->
- [ ] Each act `destructive-action-step-up` names is refused `401` `STEP_UP_REQUIRED`, changing nothing, on a token whose `step_up_at` is absent or more than 300 seconds old, with `detail.control` naming the act and a `WWW-Authenticate` header carrying `insufficient_user_authentication` and `max_age=300`; on a token whose `step_up_at` is 300 seconds old or less it is admitted, and no other person is asked <!-- wl:check step-up-refuses-stale covers destructive-acts step-up-required step-up-challenge no-second-person -->
- [ ] A token minted without `step_up`, however recent, carries no `step_up_at`; one minted with a `step_up` of form `identity` whose signature verifies over `weblisk/step-up/v1`, the `hub_id`, the request's nonce and its control carries `step_up_at` equal to its `iat`; and a `step_up` whose signature does not verify, or was made over another nonce, `hub_id` or control, is refused `INVALID_SIGNATURE`, issues no token and spends the nonce <!-- wl:check step-up-minted-only-on-proof covers step-up-request step-up-identity-form step-up-refused step-up-sets-claim step-up-is-the-claim -->
- [ ] For every vector in [`vectors/fixed-form-statements.json`](../vectors/fixed-form-statements.json) under `weblisk/step-up/v1`, the hub, which verifies a step-up and does not sign one, passes the test [`architecture/generation`](generation.md#published-test-vectors) gives for a verifier <!-- wl:check step-up-vectors covers step-up-identity-form -->
- [ ] A `step_up` of form `passkey` is admitted only for an active, unexpired step-up credential of the same operator, with `client_data_json` of type `webauthn.get` whose challenge is the base64url of the statement's bytes and whose origin is the attestation's `origin`, an `rpIdHash` of its `rp_id`, and both the user-present and user-verified flags set; with the user-verified flag clear, or a challenge over another nonce, it is refused `INVALID_SIGNATURE` <!-- wl:check step-up-passkey-checked covers step-up-passkey-form -->
- [ ] An attestation with `purpose` `step-up`, an ES256 or EdDSA COSE key, `rp_id` and `origin` is recorded with `form` `passkey`, listed and revocable; a challenge or token request naming it is refused `CREDENTIAL_PURPOSE_REFUSED`, it is not counted by `OPERATOR_LAST_ADMINISTRATOR`, and a step-up attestation naming neither `rp_id` nor `origin`, or any other attestation naming them, is refused `CREDENTIAL_ATTESTATION_INVALID` <!-- wl:check step-up-passkey-attested covers attestation-key-form attestation-purposes -->
- [ ] A provider's `401` `STEP_UP_REQUIRED` is returned to the client by the admin gateway with its status, code, `detail` and `WWW-Authenticate` header unchanged, never as `ADMIN_TOKEN_UNCHECKED` <!-- wl:check gateway-returns-step-up covers gateway-relays-step-up -->
- [ ] Every destructive act, and every refusal of one, is in the audit log with the operator's `identity_id`, the target and the `step_up_at` it was judged on, written before the act takes effect <!-- wl:check destructive-act-in-audit covers destructive-act-audited -->
- [ ] An admin revokes another operator's credential, and an operator its own, on a token carrying no `step_up_at`, and the revocation is served and audited <!-- wl:check revocation-without-step-up covers credential-revocation-not-destructive credential-revocation-route revocation-audited -->
- [ ] No other blueprint states when a destructive act needs a step-up, or asks a second person for one; each points to `destructive-action-step-up` <!-- wl:check step-up-stated-once covers step-up-one-home no-second-person -->
- [ ] Application gateway returns 404 for any request to /v1/admin/* paths
- [ ] The System overview the admin gateway composes shows the orchestrator's figures from its `GET /v1/admin/overview`, agent counts, namespaces and audit depth, and no health score, and, while no `PassRoute` can name the overview group a route answers, every other group carried as an object whose one member, `unavailable`, holds the code the gateway would answer that group's route with, and never as a number <!-- wl:check overview-composed-check covers overview-composed -->
- [ ] `GET /v1/admin/agents/{name}` shows no `token` member: an agent's registration token is never answered to an operator, a `viewer` included, whatever the orchestrator's `AgentEntry` holds
- [ ] Each admin endpoint group is served by the component that owns its state; the admin service composes them and owns none of them
- [ ] An admin endpoint whose provider is not deployed reports itself unavailable and never returns an empty result <!-- wl:check absent-provider-unavailable covers provider-absent-unavailable -->
- [ ] Through the admin gateway, an admin's token minted with `cap` `[admin:*]` reaches `PUT /v1/admin/operators/{name}/role` and changes the role, and the same request on the same admin's token minted with `cap` `[content:read, content:describe]` is refused there with `FORBIDDEN`, by the orchestrator's Auth Middleware <!-- wl:check orchestrator-judges-carried covers gateway-judged-by-orchestrator gateway-no-stand-in -->
- [ ] An admin's token minted with `cap` `[admin:read, admin:approve, admin:strategy, admin:audit]` reaches `PUT /v1/admin/operators/{name}/role` as one minted with `cap` `[admin:*]` does, and one naming only three of the four is refused there with `FORBIDDEN` <!-- wl:check admin-family-by-name covers admin-wildcard-by-name -->
- [ ] The admin gateway holds a registration whose manifest declares `token:exchange` and no other capability, calls no provider on its registration token, and adds no `X-Operator` header; the orchestrator receives the operator token the client sent, and every other provider receives a pass addressed to it, never that operator token <!-- wl:check gateway-registration-only-exchanges covers gateway-forwards-orchestrator-groups gateway-own-registration -->
- [ ] The admin gateway's manifest has `type` `infrastructure`, no `subscriptions` and no `publishes`, and a `url` on a listener other than its admin listener; on that listener `POST /v1/describe`, `GET /livez`, `GET /readyz` and `POST /v1/services` are answered as protocol/spec says, `POST /v1/execute`, `POST /v1/message` and `POST /v1/event` are answered `FORBIDDEN` and do nothing, and no `/v1/admin/*` route is served <!-- wl:check gateway-manifest covers gateway-manifest-and-listener -->
- [ ] A `ServiceDirectory` pushed to the admin gateway's `POST /v1/services`, signed or unsigned, by the orchestrator or by any other party, changes nothing the gateway sends: an entry, a pass route, a `url` or an `address_provenance` in it that the orchestrator's `GET /v1/services` does not answer is never used, no pass is sent to a `url` only it names, and the push prompts one read of `GET /v1/services` at the gateway's configured orchestrator address <!-- wl:check push-changes-nothing covers gateway-reads-directory -->
- [ ] With every push to the admin gateway lost, a component that registers again at a new address on the orchestrator's host is sent passes at the new address within 60 seconds, and an exchange answered `404` for an audience the gateway's directory names prompts one read of `GET /v1/services` <!-- wl:check directory-read-periodically covers gateway-reads-directory -->
- [ ] For a request to a route another component provides, the admin gateway sends `POST /v1/token/exchange` on its registration token with the person's token as `subject_token`, the provider's identity id as `audience` and as `scope` every capability the provider's blueprint requires for that request and no other, sends the request on the pass it is answered with, and keeps neither the person's token nor the pass once the request is answered <!-- wl:check exchange-scope-per-request covers gateway-carries-on-pass gateway-exchange-scope -->
- [ ] A provider that refuses the pass the admin gateway sent it with `401` `PASS_AUDIENCE_MISMATCH`, because its key changed after the gateway read the directory, or with `401` `TOKEN_EXPIRED`, because the pass arrived late, is answered to the client with `503` `ADMIN_TOKEN_UNCHECKED` and never with `401`, so the CLI does not refresh its token; the same provider's `403` `FORBIDDEN` for a pass whose `cap` lacks what the body requires is relayed as `403` `FORBIDDEN` <!-- wl:check pass-refusal-unchecked covers gateway-exchange-refusals -->
- [ ] A request for a route whose provider's directory entry names an address on another host than the orchestrator's, with `address_provenance` `self-asserted`, is answered `503` `ADMIN_GROUP_UNAVAILABLE` naming that address in `detail.address`, and the gateway exchanges nothing and sends nothing there; once the tenant declares that address, the same request is carried on a pass to it <!-- wl:check self-asserted-elsewhere-unavailable covers gateway-pass-address-bound -->
- [ ] Through the admin gateway, an admin's `POST /v1/content/repositories` carrying neither `scope_floor` nor `self_decision_ceiling`, and no `disposition: establish`, is exchanged with `scope` `[content:declare]` alone, and the content service records the repository <!-- wl:check exchange-declare covers gateway-exchange-scope -->
- [ ] Through the admin gateway, an admin's `POST /v1/content/repositories` with `disposition: establish` is exchanged with `scope` `[content:declare, content:establish]`, reaches the content service on a pass whose `cap` names both, and the store is established <!-- wl:check exchange-establish covers gateway-exchange-scope -->
- [ ] Through the admin gateway, an admin's `POST /v1/content/repositories` carrying `scope_floor`, as every adoption of a git store does, or `self_decision_ceiling` is exchanged with `scope` `[content:declare, content:decide]`, reaches the content service on a pass whose `cap` names both, and the declaration is recorded with that floor or ceiling <!-- wl:check exchange-decide covers gateway-exchange-scope -->
- [ ] Through the admin gateway, an admin's `POST /v1/content/repositories/{repository}/remotes` is exchanged with `scope` `[content:replicate, content:connect]`, reaches the content service on a pass whose `cap` names both, and the remote is declared <!-- wl:check exchange-remote covers gateway-exchange-scope -->
- [ ] Through the admin gateway, an `operator`'s `POST /v1/content/repositories` carrying `scope_floor` reaches the content service on a pass whose `cap` names `content:decide` alone, the one capability of the two that role carries, and is refused there with `FORBIDDEN`, recording no repository <!-- wl:check exchange-operator-decide covers gateway-exchange-scope -->
- [ ] With the content service and the fabric registered, a gateway built from this document alone exchanges an operator's `GET /v1/content/entry` with `scope` `[content:read]`, `POST /v1/content/proposals/{id}/decision` with `[content:decide]` and `POST /v1/fabric/attestations` with `[fabric:attest]`, each read from the `pass_routes` of the provider's directory entry, and sends each to that entry's `url` <!-- wl:check pass-routes-from-directory covers gateway-carries-on-pass -->
- [ ] A request for a route no directory entry declares among its `pass_routes`, or two entries declare, is answered 503 `ADMIN_GROUP_UNAVAILABLE` and nothing is exchanged or sent; a pass route an entry declares for a route of the orchestrator's own is never used, and that request is forwarded to the orchestrator on the operator token <!-- wl:check undeclared-route-unavailable covers gateway-carries-on-pass gateway-unknown-route-unavailable -->
- [ ] Every route `architecture/orchestrator`'s Administrative endpoints lists but `POST /v1/admin/model/audit` is forwarded to the orchestrator on the operator token as it arrived, `GET /v1/admin/model`, `POST /v1/admin/complete`, `GET /v1/admin/model/ceiling`, the agreement routes and `GET /v1/admin/audit` and `GET /v1/admin/audit/export` included, and never answered `ADMIN_GROUP_UNAVAILABLE`; a request for `POST /v1/admin/model/audit` is answered 404 `NOT_FOUND`, whatever the service directory declares, and nothing is forwarded or exchanged; a request for a path outside `/v1/admin/`, such as `GET /v1/audit`, is never forwarded to the orchestrator <!-- wl:check orchestrator-routes-forwarded covers gateway-forwards-orchestrator-groups -->
- [ ] An exchange answered `issued: false` is answered to the client with the code it names, at the status `protocol/types` registers for it, and one answered 404 because the provider is not registered now is answered `ADMIN_GROUP_UNAVAILABLE`; neither forwards anything <!-- wl:check exchange-code-relayed covers gateway-exchange-refusals -->
- [ ] While no deployed component's blueprint specifies the route, a request for `/v1/admin/domains`, `/v1/admin/workflows`, `/v1/admin/federation/peers`, `/v1/admin/metrics` or `/v1/admin/agents/{name}/metrics` is answered 503 `ADMIN_GROUP_UNAVAILABLE`, never with an empty result, and nothing is forwarded or sent as a `POST /v1/message` action <!-- wl:check unspecified-groups-unavailable covers gateway-unknown-route-unavailable -->
- [ ] While their blueprints do not say that they accept a pass, a request for `/v1/admin/alerts`, `/v1/admin/runbooks` or `/v1/admin/rate-limits`, or any route under them, is answered 503 `ADMIN_GROUP_UNAVAILABLE` even where the alerting agent, the incident-response agent or the component applying `patterns/rate-limiting` is deployed, and nothing is forwarded, on a pass or on the operator token <!-- wl:check passless-groups-unavailable covers gateway-unknown-route-unavailable -->
- [ ] A request for a route whose minimum is `admin` and whose provider is not the orchestrator, such as `POST /v1/admin/federation/peers/{name}/revoke`, is answered `ADMIN_GROUP_UNAVAILABLE` while that provider's blueprint specifies no such route, and once one does reaches that provider only on a pass addressed to it carrying `admin:*`, never on an operator token <!-- wl:check admin-route-elsewhere covers provider-accepts-pass -->
- [ ] A component other than the orchestrator that serves an administrative route acts only on a pass addressed to it whose `cap` names every capability the request requires: an `operator`'s approval carried on a pass naming `admin:approve` is recorded under the pass's `identity_id`, with the gateway's `act.identity_id` beside it, while an operator token is refused with `PASS_REQUIRED`, a pass addressed to another component with `PASS_AUDIENCE_MISMATCH`, and an agent's or a channel's token with `FORBIDDEN`, none of these refusals performing anything <!-- wl:check provider-acts-on-pass covers provider-accepts-pass -->
- [ ] Through the admin gateway, a request for a route another component provides is refused by the exchange with `OPERATOR_REVOKED` on the token of an operator removed since it was minted, and with `FORBIDDEN` on the token of an operator since lowered to `viewer`; while the orchestrator cannot be asked it is refused with 503 `ADMIN_TOKEN_UNCHECKED` carrying `retry_after`; where the exchange answers `404` `NOT_FOUND` because the provider is not registered now it is refused with 503 `ADMIN_GROUP_UNAVAILABLE`, never `ADMIN_TOKEN_UNCHECKED`; in none of these is anything forwarded <!-- wl:check exchange-refuses-revoked covers gateway-judged-by-orchestrator gateway-exchange-refusals -->
- [ ] All admin API responses include Cache-Control: no-store header
- [ ] Admin auth middleware verifies `type` is `operator`, checks that the operator and credential the token names are live, and checks that the request can use the capability the endpoint's minimum stands for, from the role the operator holds now narrowed to the token's `cap` <!-- wl:check auth-middleware-checks covers status-checked-on-use -->
- [ ] An admin's token minted with `cap` `[admin:read]` carries `admin:read`, reaches a `viewer+` route, and is refused with `FORBIDDEN` at `POST /v1/admin/complete`, which needs `llm:chat`, and on an `admin` route such as `PUT /v1/admin/operators/{name}/role` <!-- wl:check admin-read-reach covers route-capability-forbidden -->
- [ ] Only the `admin` role carries `llm:chat`: an `operator`, a `viewer` or an `auditor` is refused with `FORBIDDEN` at `POST /v1/admin/complete`, and an admin's token whose `cap` names `llm:chat` reaches it
- [ ] An operator-role token minted with `cap` `[admin:*]` carries `admin:read`, `admin:approve` and `admin:strategy`, and not `admin:*` or `admin:audit` <!-- wl:check operator-role-admin-names covers admin-wildcard-by-name operator-role-admin-family -->
- [ ] A token presented in the request body rather than the `Authorization` header is refused on every `/v1/admin/*` route
- [ ] A console holds no registration at any hub: it never sends `POST /v1/register` with its own key or any key it holds, and does no work at a hub while no signed-in person is present <!-- wl:check console-not-registered-check covers console-not-a-component console-no-unattended-work console-not-registered -->
- [ ] A sixth `POST /v1/admin/credentials/token` within a minute from one client address is refused before its signature is verified, whatever `cid` each names, while requests from another address, and to `POST /v1/admin/operators/{name}/key` from the same one, are not <!-- wl:check credential-token-limited covers auth-routes-limited -->
- [ ] The admin gateway forwards each request for a route served without a token with `X-Forwarded-For` naming the client address it counted, replacing any the request carried; the orchestrator counts such a request by that header only where it arrives from an address `orchestrator.admin_gateway_from` names, and a request from any other address by that address, so a sixth from one client through the gateway is refused at both and a first from another client is not <!-- wl:check forwarded-source-trusted covers gateway-limits-and-forwards-source orchestrator-trusts-declared-gateway -->
- [ ] Bootstrap event (first operator registration) is permanently recorded in the audit log
- [ ] While no provider's blueprint specifies `/v1/admin/ws`, a request for it is answered 503 `ADMIN_GROUP_UNAVAILABLE`, and the gateway opens no subscription and holds no connection to serve it
- [ ] The admin gateway serves no page, script or static file of its own, and keeps no session or cookie: a person reaches it through the CLI or a console holding their credential
- [ ] While no `PassRoute` can name the inbox group a route answers, `GET /v1/admin/approvals` at the admin gateway is answered 503 `ADMIN_GROUP_UNAVAILABLE` with content registered or not, the gateway asks no owner and sends nothing, and it is never answered as an empty list; the gateway serves no route that decides, and a decision reaches its owner only at the owner's own route <!-- wl:check inbox-composed covers inbox-composed-by-pass-route inbox-never-quietly-empty inbox-decides-nothing -->
- [ ] A registration missing `name`, `public_key`, `role`, `timestamp` or `signature`, or whose signature does not verify under the `public_key` it submits, is refused and writes no record; one outside the replay window, or seen before, is refused; and every registration, admitted or refused, is audited <!-- wl:check registration-checked covers registration-fields registration-verifies-submitted-key registration-replay registration-audited -->
- [ ] A registration verifies only over `canonicalize({name, public_key, role, timestamp})` with the timestamp it sent; one whose signature is over the token request's payload, or that leaves out its key or role, is refused <!-- wl:check registration-input-exact covers registration-signed-payload registration-payload-distinct registration-signs-key registration-signs-role registration-timestamp-signed registration-input-stated-exactly timestamp-sent-is-signed -->
- [ ] An orchestrator with an empty operator store emits one bootstrap secret of at least 256 random bits, and compares a presented secret in constant time <!-- wl:check bootstrap-secret-strong covers bootstrap-secret-generated bootstrap-secret-presented -->
- [ ] A registration refused for want of an admin, for a signature that does not verify, and for a missing or wrong bootstrap secret is answered with three different codes, each naming its case <!-- wl:check bootstrap-refusals-told-apart covers bootstrap-refusals-distinct bootstrap-refusal-named -->
- [ ] `POST /v1/admin/operators/{name}/approve` by an admin approves a pending operator, answers success and changes nothing for one already approved, returns no token, and is audited with the approver's name; `GET /v1/admin/operators` lists pending operators beside approved ones <!-- wl:check approval-served covers approve-route operators-list-pending-rule approve-idempotent-rule approve-no-token approve-audited approve-orchestrator-steps approve-idempotent operators-list-pending -->
- [ ] No component, and no console, registers or is approved as an operator: a service reaches a hub only through `POST /v1/register` <!-- wl:check operators-are-people covers operator-is-person -->
- [ ] A client signs a token request, or a credential's answer, only for a `hub_id` it recorded from a registration answer or attested its credential for, never a payload naming no hub, and treats a challenge naming another `hub_id` as a hub it holds no credential for <!-- wl:check client-signs-recorded-hub covers attestation-client-hub-id client-signs-credential-hub-id -->
- [ ] `POST /v1/admin/operators/{name}/credentials` accepts an attestation token or an operator token for the operator the path names, refuses another operator's with `OPERATOR_SUBJECT_MISMATCH` and any other token with `CREDENTIAL_REQUIRED`, and refuses with `CREDENTIAL_ATTESTATION_INVALID` an attestation that does not verify under the operator's own recorded key or names another `identity_id` <!-- wl:check credentials-route-subject covers credentials-route-tokens attestation-verifies-own-key attestation-names-identity -->
- [ ] An attestation for a key the operator already holds as an active credential replaces its attestation and keeps its id; a stored credential has the algorithm, form, `device_bound` and status its form is given; every attestation is audited with the operator, the credential id, its purpose and the device label <!-- wl:check credential-reattested covers credential-reattest credential-stored-form credential-attestation-audited -->
- [ ] A challenge or a token request naming a `cid` this hub holds no credential for is refused with `CREDENTIAL_UNKNOWN`, and no nonce is issued <!-- wl:check unknown-cid-refused covers challenge-refusals token-request-unknown-cid -->
- [ ] The answer to a credential's token request carries the attestation's `not_after`, and the credential's `last_used_at` is updated <!-- wl:check token-answer-and-use covers token-answer-not-after credential-last-used -->
- [ ] A change of identity key for an operator with no record is refused with `OPERATOR_UNKNOWN`, and one over another hub's `hub_id` with `CREDENTIAL_FOREIGN_HUB`, logged as a security event <!-- wl:check key-change-unknown-or-foreign covers key-change-unknown key-change-foreign-hub -->
- [ ] The answer to a change of identity key carries the operator record, its `identity_id` and `hub_id` and no token, and the change is audited with the operator's identity id and both keys' fingerprints <!-- wl:check key-change-answered covers key-change-answer key-change-audited -->
- [ ] A console holds one credential per account per hub, whose key it generated and had attested through the CLI, asks for a `not_after` 30 days ahead unless the person chooses another within 90, and warns when fewer than 7 days remain <!-- wl:check console-credential-made covers console-credential-per-account console-credential-lifetime -->
- [ ] A role carrying `admin:*` does not thereby carry `model:attest`, `telemetry:read`, `action:invoke` or `scope:admit` <!-- wl:check admin-wildcard-bounded covers admin-wildcard-excludes -->
- [ ] Removing or demoting the last active admin is refused, and every role change is audited with the previous and new role <!-- wl:check last-admin-protected covers last-admin-kept role-change-audited -->
- [ ] A client that registers reads the answer's `status`, asks for an attestation token only for an approved operator, and reports a pending registration as pending, never as connected <!-- wl:check registration-status-read covers client-reads-status -->
- [ ] Operator records, credentials and token-request `jti` records survive a restart of the orchestrator, and the `jti` records are shared by every instance answering for the hub <!-- wl:check operator-stores-durable covers store-operators-durable store-credentials-durable store-jti-durable -->
- [ ] The CLI accepts an identity by a label and resolves and reports its location itself; the label is never the operator's name and never appears verbatim in the path <!-- wl:check identity-label covers identity-by-label label-not-name label-not-in-path -->
- [ ] A client holding a pin for the admin gateway's address refuses a certificate with another key, reports it as a pin that did not match and not as unreachable, and never falls back to the system's roots, to unverified TLS or to HTTP, at a loopback address too; given an admin gateway address whose scheme is not `https`, a client refuses it before sending anything, at a loopback address too; one holding no pin refuses a certificate its roots do not verify, names `create`'s result, and the tenant's operator reading it from the certificate on the gateway's host, as where a pin comes from, and never prints, offers or records the presented certificate's pin <!-- wl:check gateway-pin-held covers client-pins-gateway-key -->
- [ ] `weblisk operator connect --json` and `weblisk operator register --json` carry the `tls_pin` the registration records for the address, and no `tls_pin` where it records none; a console that makes its own requests to the gateway and was given a `tls_pin` verifies every connection to that address against it and refuses another key, and one given none verifies under the system's roots, refuses a certificate they do not verify, and records no pin from the connection <!-- wl:check console-pin-kept covers console-keeps-pin -->

### Admin gateway

- [ ] Started with its registration key or its TLS key readable or writable by its group or by other accounts, the admin gateway refuses to run and names the file, for a key the operator supplied as for one the CLI made <!-- wl:check gateway-open-key-refused covers gateway-refuses-open-key -->
- [ ] Each of the admin gateway's listeners serves exactly the rows [Endpoints](#endpoints) gives it: the internal listener answers no admin route, and the admin listener none of the agent endpoints <!-- wl:check listeners-serve-their-rows covers listeners-disjoint gateway-manifest-and-listener -->
- [ ] The admin listener answers no plain-HTTP request, negotiates TLS 1.3 alone and offers X25519MLKEM768, preferring it, and a TLS 1.2 client is refused the handshake <!-- wl:check admin-listener-tls covers admin-listener-guarded admin-listener-tls13 admin-https-only -->
- [ ] `weblisk tenant create` and `weblisk component admin init` leave `.weblisk/keys/` mode 0700 and `admin-gateway.key` and `admin-gateway-tls.key` mode 0600, with the tenant's `.gitignore` excluding `.weblisk/keys/`; run in a tenant whose `.gitignore` lacks that entry they add it before writing either key, and given a `tls_key` inside the tenant's tree that no `.gitignore` entry excludes they refuse, writing neither key <!-- wl:check gateway-keys-mode covers gateway-keys-kept -->
- [ ] With `admin_gateway.tls_cert` and `tls_key` set, the CLI makes, renews and replaces no certificate or key: `weblisk server start` serves the configured certificate with fewer than 30 days left unchanged, and a missing configured file is reported, not made <!-- wl:check given-certificate-kept covers given-certificate-served -->
- [ ] The admin gateway registers with the key whose fingerprint is `orchestrator.admin_gateway_identity`; started with any other key, its registration is refused `CAPABILITY_GATEWAY_ONLY` and it exchanges nothing <!-- wl:check gateway-declared-key covers gateway-registers-declared-key -->
- [ ] Started with `--port` and `WL_PORT` naming a port, the admin gateway serves its internal listener, with `/livez` and `/readyz`, on that port, and its admin listener on `admin_gateway.port`; with `admin_gateway.internal_address` unset, the `url` it registers names that port and not `admin_gateway.internal_port` <!-- wl:check gateway-port-internal covers gateway-port-is-internal -->
- [ ] Given a certificate file, or a directory holding it, with a group or other write bit set, `weblisk tenant accept` and `weblisk server provision` refuse, naming the file, and read no pin from it; the certificate the CLI makes is mode 0644 in a `.weblisk/tls/` of mode 0755 <!-- wl:check pin-source-checked covers pin-source-guarded -->
- [ ] Started with `WL_DEV=1` from its tree alone, with no orchestrator and no certificate files, the admin gateway starts, answers `/readyz` not ready, binds its admin listener to an unused loopback port over TLS, prints `[dev] admin listener https://127.0.0.1:<port> tls_pin sha256:<hex>` before serving, the pin matching the certificate it serves, and writes no key or certificate file <!-- wl:check dev-run-listener covers dev-run-admin-listener -->
- [ ] With the default certificate absent and `admin-gateway-tls.key` present, the command that stands the gateway up makes the certificate from that key and the pin is unchanged; with the key absent and the certificate present, it refuses, naming the key, and makes neither <!-- wl:check lone-certificate covers lone-certificate-refused -->
