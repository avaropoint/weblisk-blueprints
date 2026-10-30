<!-- blueprint
type: architecture
name: orchestrator
version: 4.4.0
requires: [protocol/identity, protocol/types, architecture/storage, architecture/admin, patterns/scope, patterns/logging]
platform: any
tier: free
-->

# Weblisk Orchestrator Blueprint

The orchestrator is the trust anchor and registry service. It manages
agent registration, identity verification, namespace ownership, service
directory distribution, and channel brokering.

The orchestrator does NOT execute agent logic, route tasks, hold a
programme's objectives, or hold a decision queue: it records a person's
decision it is handed (an operator's approval or role), and never makes one. Work is
execution's, objectives are the programme service's, and each decision is
its owner's, composed into one inbox by the admin gateway
([`architecture/admin`](admin.md#decision-inbox)). Each registers like any
other component.

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
      # 3.1.0 is where the work pass this orchestrator mints is specified
      version: ">=3.1.0 <4.0.0"
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
      # 4.0.0 is where token:exchange is admitted for the declared admin
      # gateway alone (Registration Flow, step 1); the work pass's types are
      # 6.2.0's, and SCOPE_NAME_TAKEN and GRANT_SELF_REFUSED 6.3.0's
      version: ">=6.3.0 <7.0.0"
      bindings:
        types:
          - name: RegisterRequest
            fields_used: [manifest, signature, timestamp]
          - name: RegisterResponse
            fields_used: [agent_id, token, expires_at, services, lease]
          - name: ServiceDirectory
            fields_used: [services, routing_table, namespaces]
          # Each entry republishes what the registration recorded, the routes
          # at which the component admits a person's request on a pass included
          - name: ServiceEntry
            fields_used: [name, url, public_key, capabilities, lease_state, lease_expires_at, address_provenance, pass_routes]
          # A component's presence is the lease it renews; the orchestrator
          # grants it, records its readiness and never probes for it
          - name: Lease
            fields_used: [agent_id, duration, renewed_at, expires_at]
          - name: LeaseRenewal
            fields_used: [ready, checks, timestamp]
          - name: Liveness
            fields_used: [live]
          - name: Readiness
            fields_used: [ready]
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
          # The work pass: a person's authorisation of unattended work, and
          # the exchange an actor mints a work pass at (Work Exchange)
          - name: WorkAuthorisation
            fields_used: [id, owner, definition, actors, capabilities, authorised_by, created_at, not_after, status, revoked_at, revoked_by, reason]
          - name: WorkAuthorisationRequest
            fields_used: [owner, definitions, actors, not_after]
          - name: WorkDefinitionCeiling
            fields_used: [definition, capabilities]
          - name: WorkExchangeRequest
            fields_used: [authorisation, audience, scope, run]
          - name: WorkExchangeResponse
            fields_used: [issued, code, pass, expires_at, capabilities]
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: architecture/storage
      # 2.1.0 is where backup-restore names the snapshot route
      version: ">=2.1.0 <3.0.0"
      bindings:
        types:
          - name: AuditFilter
            fields_used: [actor, action, since, cursor, limit]
          - name: RecordSnapshot
            fields_used: [snapshot, service, taken_at, store_format, files]
        behaviors:
          - name: backup-restore
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: architecture/admin
      # 4.0.0 is where a destructive act needs a step-up, never a second person
      version: ">=4.0.0 <6.0.0"
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
          - name: destructive-action-step-up
          - name: operator-credential-revocation
          - name: operator-key-change
          - name: auth-route-rate-limit
          - name: operator-roles
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately
    - blueprint: patterns/scope
      version: ">=2.6.0 <4.0.0"
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
    - blueprint: patterns/logging
      version: ">=2.0.0 <3.0.0"
      bindings:
        behaviors:
          - name: structured-logging
          - name: redaction-at-emission
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
    - method: POST
      path: "/v1/token/work"
      operation: WorkExchange
      auth: "token"
    - method: GET
      path: "/v1/work/authorisations"
      operation: WorkAuthorisationsHeld
      auth: "token"
    - method: DELETE
      path: "/v1/work/authorisations/{id}"
      operation: WorkAuthorisationWithdraw
      auth: "token"
    - method: POST
      path: "/v1/lease"
      operation: Lease
      auth: "token"
    - method: GET
      path: "/livez"
      operation: Livez
      auth: "none"
    - method: GET
      path: "/readyz"
      operation: Readyz
      auth: "none"
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
    - method: POST
      path: "/v1/admin/work-authorisations"
      operation: WorkAuthorise
      auth: "work:authorise"
    - method: GET
      path: "/v1/admin/work-authorisations"
      operation: WorkAuthorisationList
      auth: "admin:read"
    - method: POST
      path: "/v1/admin/work-authorisations/{id}/renew"
      operation: WorkAuthorisationRenew
      auth: "work:authorise"
    - method: DELETE
      path: "/v1/admin/work-authorisations/{id}"
      operation: WorkAuthorisationRevoke
      auth: "token"
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
      path: "/v1/admin/records/orchestrator/snapshot"
      operation: AdminRecordSnapshot
      auth: "admin:*"
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
      auth: "llm:chat"
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
    # Generated, not platform-provided: the model gateway records through it
    # in process. "token" admits any operator token; the capability judged is
    # the one its body's action names (Auth Middleware, step 8)
    - method: POST
      path: "/v1/admin/model/audit"
      operation: AdminModelAudit
      auth: "token"
    # Generated, not platform-provided: the model gateway records a
    # registered component's completion through it in process. "token" admits
    # a registration token; the capability judged is llm:chat (Auth
    # Middleware, step 8)
    - method: POST
      path: "/v1/model/audit"
      operation: ModelAudit
      auth: "token"
    # The resource API's part this orchestrator serves (Resources this
    # orchestrator owns): its kinds in the catalogue, the lease reads, and
    # the feed of each kind it owns
    - method: GET
      path: "/v1/admin/resources"
      operation: AdminResourceCatalogue
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/r/lease"
      operation: AdminLeaseList
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/r/lease/{name}"
      operation: AdminLeaseGet
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/events/agent"
      operation: AdminAgentEvents
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/events/lease"
      operation: AdminLeaseEvents
      auth: "admin:read"
    # The tenant's organisations, projects and the roles operators hold at
    # them (The tenant's organisations and projects; A role held at an
    # organisation or a project), each served at the uniform address
    - method: GET
      path: "/v1/admin/r/organisation"
      operation: AdminOrganisationList
      auth: "admin:read"
    - method: POST
      path: "/v1/admin/r/organisation"
      operation: AdminOrganisationCreate
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/r/organisation/{uid}"
      operation: AdminOrganisationGet
      auth: "admin:read"
    - method: PATCH
      path: "/v1/admin/r/organisation/{uid}"
      operation: AdminOrganisationUpdate
      auth: "admin:*"
    - method: POST
      path: "/v1/admin/r/organisation/{uid}/retire"
      operation: AdminOrganisationRetire
      auth: "admin:*"
    - method: POST
      path: "/v1/admin/r/organisation/{uid}/restore"
      operation: AdminOrganisationRestore
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/events/organisation"
      operation: AdminOrganisationEvents
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/r/project"
      operation: AdminProjectList
      auth: "admin:read"
    - method: POST
      path: "/v1/admin/r/project"
      operation: AdminProjectCreate
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/r/project/{uid}"
      operation: AdminProjectGet
      auth: "admin:read"
    - method: PATCH
      path: "/v1/admin/r/project/{uid}"
      operation: AdminProjectUpdate
      auth: "admin:*"
    - method: POST
      path: "/v1/admin/r/project/{uid}/retire"
      operation: AdminProjectRetire
      auth: "admin:*"
    - method: POST
      path: "/v1/admin/r/project/{uid}/restore"
      operation: AdminProjectRestore
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/events/project"
      operation: AdminProjectEvents
      auth: "admin:read"
    - method: GET
      path: "/v1/admin/r/grant"
      operation: AdminGrantList
      auth: "admin:read"
    - method: POST
      path: "/v1/admin/r/grant"
      operation: AdminGrantCreate
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/r/grant/{uid}"
      operation: AdminGrantGet
      auth: "admin:read"
    - method: POST
      path: "/v1/admin/r/grant/{uid}/revoke"
      operation: AdminGrantRevoke
      auth: "admin:*"
    - method: GET
      path: "/v1/admin/events/grant"
      operation: AdminGrantEvents
      auth: "admin:read"
  # The kinds a person sees and operates here (schemas/resource). Each
  # operation that binds an Operation above is served at that route; the
  # others at the uniform address, as architecture/admin's Resources says
  resources:
    - kind: agent
      owner: orchestrator
      type: AgentEntry
      list_type: AgentSummary
      identity: {field: manifest.name, form: declared-name}
      label: manifest.name
      fields:
        - {name: manifest.name, access: read-only, present: text}
        - {name: manifest.type, access: read-only, present: text}
        - {name: manifest.version, access: read-only, present: text}
        - {name: manifest.description, access: read-only, present: text}
        - {name: manifest.url, access: read-only, present: text}
        - {name: manifest.capabilities, access: read-only, present: list}
        - {name: manifest.pass_routes, access: read-only, present: list}
        - {name: agent_id, access: read-only, present: text}
        - {name: registered_at, access: read-only, present: instant}
        - {name: last_seen, access: read-only, present: instant, volatile: true}
        - {name: lease, access: read-only, volatile: true}
        - {name: last_renewal, access: read-only, volatile: true}
        - {name: token, access: read-only, sensitive: true}
      operations:
        list: {capability: "admin:read", binds: AdminAgentList, items: agents}
        get: {capability: "admin:read", binds: AdminAgentGet}
      verbs:
        - name: deregister
          capability: "admin:*"
          step_up: true
          binds: AdminAgentDeregister
          preconditions:
            - the agent is registered here now
          in_flight:
            handling: continues
            says: this orchestrator holds none of the agent's work; work the agent has under way runs on until it next needs this orchestrator, which no longer knows its registration
          effect: the agent's entry, namespaces and routes are removed as the Deregistration Flow removes them, system.agent.deregistered is published and the directory is broadcast without it
          reversible: false
      events: [created, updated, deleted, deregister]
      relations: []
    - kind: lease
      owner: orchestrator
      type: AgentLease
      identity: {field: agent, form: declared-name}
      label: agent
      fields:
        - {name: agent, access: read-only, present: reference, kind: agent}
        - {name: lease_state, access: read-only, present: choice}
        - {name: ready, access: read-only, present: boolean}
        - {name: checks, access: read-only}
        - {name: duration, access: read-only, present: duration}
        - {name: renewed_at, access: read-only, present: instant, volatile: true}
        - {name: expires_at, access: read-only, present: instant, volatile: true}
      operations:
        list: {capability: "admin:read"}
        get: {capability: "admin:read"}
      events: [created, updated]
      relations:
        - {relation: held_by, to: agent, field: agent}
    - kind: organisation
      owner: orchestrator
      type: Organisation
      identity: {field: id, form: minted}
      label: display_name
      fields:
        - {name: id, access: read-only, present: text}
        - {name: name, access: create, present: text}
        - {name: display_name, access: settable, present: text}
        - {name: operates_in, access: settable, present: list}
        - {name: state, access: read-only, present: choice}
        - {name: created_by, access: read-only, present: text}
        - {name: created_at, access: read-only, present: instant}
        - {name: retired_at, access: read-only, present: instant}
      operations:
        list: {capability: "admin:read", filters: [state, name]}
        get: {capability: "admin:read"}
        create: {capability: "admin:*"}
        update: {capability: "admin:*"}
      verbs:
        - name: retire
          capability: "admin:*"
          transition: retire
          preconditions:
            - every project in the organisation is retired
          in_flight:
            handling: continues
            says: this orchestrator holds none of the organisation's content, adoptions or work; each runs on where it is held, and nothing it holds is changed by the retirement
          effect: the organisation is retired and retired_at is set; its id and name stay recorded, and nothing that names it is changed or removed
          reversible: {by: restore}
        - name: restore
          capability: "admin:*"
          transition: restore
          preconditions:
            - the organisation is retired
          in_flight:
            handling: none
            says: a retired organisation has no work this orchestrator holds
          effect: the organisation is active again and retired_at is cleared
          reversible: {by: retire}
      states:
        initial_state: active
        entity_type: Organisation
        state_field: state
        states:
          active: {description: in use}
          retired: {description: no longer in use; kept so that every record naming it still resolves}
        transitions:
          - {name: retire, from: active, to: retired, trigger: manual, description: a person retires it}
          - {name: restore, from: retired, to: active, trigger: manual, description: a person returns it to use}
      events: [created, updated, retire, restore]
      relations: []
    - kind: project
      owner: orchestrator
      type: Project
      identity: {field: id, form: minted}
      label: display_name
      fields:
        - {name: id, access: read-only, present: text}
        - {name: organisation, access: create, present: reference, kind: organisation}
        - {name: name, access: create, present: text}
        - {name: display_name, access: settable, present: text}
        - {name: state, access: read-only, present: choice}
        - {name: created_by, access: read-only, present: text}
        - {name: created_at, access: read-only, present: instant}
        - {name: retired_at, access: read-only, present: instant}
      operations:
        list: {capability: "admin:read", filters: [organisation, state, name]}
        get: {capability: "admin:read"}
        create: {capability: "admin:*"}
        update: {capability: "admin:*"}
      verbs:
        - name: retire
          capability: "admin:*"
          transition: retire
          preconditions:
            - the project is active
          in_flight:
            handling: continues
            says: this orchestrator holds none of the project's content or work; each runs on where it is held, and nothing it holds is changed by the retirement
          effect: the project is retired and retired_at is set; its id and name stay recorded, and nothing that names it is changed or removed
          reversible: {by: restore}
        - name: restore
          capability: "admin:*"
          transition: restore
          preconditions:
            - the project's organisation is active
          in_flight:
            handling: none
            says: a retired project has no work this orchestrator holds
          effect: the project is active again and retired_at is cleared
          reversible: {by: retire}
      states:
        initial_state: active
        entity_type: Project
        state_field: state
        states:
          active: {description: in use}
          retired: {description: no longer in use; kept so that every record naming it still resolves}
        transitions:
          - {name: retire, from: active, to: retired, trigger: manual, description: a person retires it}
          - {name: restore, from: retired, to: active, trigger: manual, description: a person returns it to use}
      events: [created, updated, retire, restore]
      relations:
        - {relation: part_of, to: organisation, field: organisation}
    - kind: grant
      owner: orchestrator
      type: RoleGrant
      identity: {field: id, form: minted}
      label: role
      fields:
        - {name: id, access: read-only, present: text}
        - {name: identity_id, access: create, present: text}
        - {name: role, access: create, present: choice}
        - {name: organisation, access: create, present: reference, kind: organisation}
        - {name: project, access: create, present: reference, kind: project}
        - {name: status, access: read-only, present: choice}
        - {name: granted_by, access: read-only, present: text}
        - {name: granted_at, access: read-only, present: instant}
        - {name: revoked_by, access: read-only, present: text}
        - {name: revoked_at, access: read-only, present: instant}
      operations:
        list: {capability: "admin:read", filters: [identity_id, organisation, project, status]}
        get: {capability: "admin:read"}
        create: {capability: "admin:*", step_up: true}
      verbs:
        - name: revoke
          capability: "admin:*"
          step_up: true
          transition: revoke
          preconditions:
            - the grant does not name the person revoking it
          in_flight:
            handling: continues
            says: a grant is judged on each request; a request already admitted runs to its end, and the next is judged without it
          effect: the grant is revoked, revoked_by and revoked_at are set, and the record stays; where it was the operator's last active grant, the operator is no longer confined and acts with their role across the tenant
          reversible: false
      states:
        initial_state: active
        entity_type: RoleGrant
        state_field: status
        states:
          active: {description: held}
          revoked: {description: no longer held; kept so that what was done under it can be checked against who held what, terminal: true}
        transitions:
          - {name: revoke, from: active, to: revoked, trigger: manual, description: a person revokes it}
      events: [created, revoke]
      relations:
        - {relation: held_at, to: organisation, field: organisation}
        - {relation: held_at, to: project, field: project}
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
      endpoint: GET /v1/admin/records/orchestrator/snapshot
    - check: endpoint-routed
      endpoint: POST /v1/admin/model/audit
    - check: endpoint-routed
      endpoint: POST /v1/model/audit
    - check: endpoint-routed
      endpoint: POST /v1/token/exchange
    - check: endpoint-routed
      endpoint: POST /v1/token/work
    - check: endpoint-routed
      endpoint: GET /v1/work/authorisations
    - check: endpoint-routed
      endpoint: DELETE /v1/work/authorisations/{id}
    - check: endpoint-routed
      endpoint: POST /v1/admin/work-authorisations
    - check: endpoint-routed
      endpoint: GET /v1/admin/work-authorisations
    - check: endpoint-routed
      endpoint: POST /v1/admin/work-authorisations/{id}/renew
    - check: endpoint-routed
      endpoint: DELETE /v1/admin/work-authorisations/{id}
    - check: endpoint-routed
      endpoint: POST /v1/lease
    - check: endpoint-routed
      endpoint: GET /livez
    - check: endpoint-routed
      endpoint: GET /readyz
    - check: type-has-keys
      type: RegisterResponse
      keys: [agent_id, token, expires_at, services, lease, orchestrator, protocol_version]
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

The orchestrator is a tenant's **first** component, and its admin gateway
([`architecture/admin`](admin.md#the-admin-gateway-as-a-component)) the
second: every tenant has both, because without the gateway no person's
request reaches it. It is not the tenant, and
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
| What is this tenant running, right now? | This orchestrator's registry: `GET /v1/services` for a registered component, and `GET /v1/admin/agents`, through the admin gateway, for a person | Derived from registration. A component that is not running is not in it, and no file can claim otherwise |
| What should this tenant build and start? | `.weblisk/config.yaml`, per [`schemas/config`](../schemas/config.md) | An operator's intent, which is a declared fact and belongs in a declared file |
| Where may a component legitimately be? | the same declared file, republished per entry as `ServiceEntry.address_provenance` | A component's address is part of the operator's intent. A registrant asserting one is making a claim, and the registry must be able to say which it is holding |

The first is what a client asks: a person's client at `GET /v1/admin/agents`,
since a person's token reaches no route a component uses
([Auth Middleware](#auth-middleware), step 6). Treating the second as the
answer is how a tenant comes to report a component it has never started, and the specification
of the second is `schemas/config.md`'s, not this document's.

### Composing a tenant

Composition is a sequence of acts, each recorded, with nothing to restart:

```
weblisk tenant create "Acme Corp"      # the orchestrator and the admin gateway, started and claimed
weblisk component content init         # the content service, into the same module
```

One act is the exception: an admin gateway that `weblisk component admin init`
adds to a tenant made before it is admitted once the orchestrator restarts,
because the orchestrator reads `orchestrator.admin_gateway_identity` when it
starts ([`architecture/admin`](admin.md#registration-lease-and-identity)).

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
opened to its anchor, the orchestrator address it registered at (below), or
one that verified its `signature` under this orchestrator's key
([`protocol/spec`](../protocol/spec.md#post-v1services), the signed push). A
pushed body that does not verify says nothing about this orchestrator. Read
from the anchor or verified, the directory is an authenticity statement about
the registry. It is not an authorisation statement about the addresses inside it,
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
> exists. One registration is declared already, by its key rather than its
> address: the admin gateway's, whose fingerprint is
> `orchestrator.admin_gateway_identity`, and for which alone this
> orchestrator admits `token:exchange` ([Registration Flow](#registration-flow-post-v1register),
> step 1).

> **Gap — nothing can currently reach `verified`.** `GET /livez` and
> `GET /readyz` are unauthenticated, so a probe that answers proves something is
> listening, which is not the claim. `verified` needs a probe the registered key signs over a
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
| Its anchor credential | Present it — except a person's operator token, which a console, the CLI or a script presents at the admin gateway alone, and the gateway at the orchestrator alone, at no other address on that host either ([`protocol/identity`](../protocol/identity.md#the-pass)) | **Refuse** — the address is not one the tenant declared | **Do not present it** — the credential is bound to the anchor, and a second host is a second place it can be taken from |
| A grant naming that exact address | Present it | Never issued — see below | Present the grant's token, and only it |
| A pass, held by the admin gateway for the one request it carries | Present it at its audience's address | **Refuse**, naming the undeclared address; the gateway answers `ADMIN_GROUP_UNAVAILABLE` | Present it at its audience's address, and nowhere else |
| None of these | — | Refuse, naming the undeclared address | Refuse, naming the credential it does not hold |

Every refusal names **which fact was missing**, and the two are different
remedies: an undeclared address is fixed in the tenant's configuration, and a
missing grant is fixed by obtaining one. A client that collapses them into
"unavailable" has reported a state nobody can act on.

**Two hosts are compared as text, never by resolving them.** A client compares
the host of the address it would send to with its anchor's host after
lowercasing both, writing an IPv4 literal in dotted decimal and an IPv6
literal in the form RFC 5952 gives it, and taking `localhost` and every
loopback literal, in `127.0.0.0/8` or `::1`, as one host. Any other pair that
differs as text is two hosts, a name and an address it resolves to included,
so a deployment names each component on the anchor's host as the anchor names
that host. The client then sends the credential, or a person's pass, only on a
connection to the host it compared. Comparing by resolution would let a
registrant whose `url` names a host it controls resolve it to the anchor's
address when the check is made and rebind it afterwards, sending what is bound
to the anchor's host off it.

Same-host is not a special case in the rule; it is the rule. The credential is
already at that host, so presenting it on another port there tells no new party
anything. What that does assume is that a second process on the anchor's host is
not a separate adversary, which is the trusted-network position
[`architecture/threat-model`](threat-model.md) Boundary 2 already takes and
records as residual. It is not an additional claim made here. A person's
operator token is excepted for a reason that is not about the host: it reaches
furthest, so no component but the admin gateway, and from it the orchestrator
that issued it, is ever given one, whatever host it shares with the gateway.

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
admin gateway ─token──▶ │  │  token → capabilities │  │  those Auth Middleware
 (operators) ─admin ──▶ │  └───────────┬───────────┘  │  lists
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
2. **Service Directory** — maintain and broadcast the registry of
   registered agents with each one's lease state, the routing table, and the
   namespace map
3. **Namespace Control** — enforce exclusive namespace ownership at
   registration, reserve `system.*` for itself
4. **Channel Brokering** — establish secure direct connections between agents
5. **Auth Enforcement** — verify tokens on all protected endpoints
6. **Audit Logging** — record every operation in an append-only log
7. **Presence** — grant each registered component a lease, record the
   readiness each renewal carries, and read a lapsed lease as `unknown`
   ([Presence](#presence))
8. **System Events** — publish to `system.*` namespace (agent lifecycle events)

See [Protocol Specification](../protocol/spec.md) for the authoritative
endpoint contracts.
See [Agent Architecture](agent.md) for the 7-endpoint agent protocol.

## Endpoints

### Protocol endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| POST | /v1/register | Register | no* | Agent registration (identity-verified) |
| DELETE | /v1/register | Deregister | yes | Agent deregistration |
| GET | /v1/services | Services | yes | Service directory (routing table + namespaces) |
| POST | /v1/channel | Channel | yes | Request direct agent-to-agent channel |
| POST | /v1/rotate-key | RotateKey | yes | Rotate an agent's ML-DSA-65 key pair. Dual-signed with the current and the new key, which proves possession of both; the caller's existing token still authenticates the request |
| POST | /v1/lease | Lease | yes | Renew the caller's lease, carrying its readiness — see [Presence](#presence) |
| GET | /livez | Livez | no | The orchestrator's own liveness, for the supervisor that restarts it |
| GET | /readyz | Readyz | no | The orchestrator's own readiness, for the supervisor waiting on its start and the probe of the orchestrator, which holds no lease |
| GET | /v1/audit | Audit | yes | Query audit log |
| POST | /v1/token/exchange | TokenExchange | yes | Exchange the operator token a person has just presented to the admin gateway for a pass addressed to one component, for the admin gateway's registration and no other — see [Token Exchange](#token-exchange-post-v1tokenexchange) |
| GET | /v1/model/ceiling | ModelCeiling | yes | What a model backend may be sent now, and where it is reached, for a registered component (platform-provided — see [A model is a destination](#a-model-is-a-destination)) |
| POST | /v1/token/work | WorkExchange | yes | Mint a work pass, for an actor a work authorisation names, under that authorisation — see [Work Exchange](#work-exchange-post-v1tokenwork) |
| GET | /v1/work/authorisations | WorkAuthorisationsHeld | yes | The work authorisations that name the caller's registration as owner or actor, revoked ones included, each a `WorkAuthorisation`. An actor finds the authorisation for a definition here; an owner reports from it which of its definitions are authorised |
| DELETE | /v1/work/authorisations/{id} | WorkAuthorisationWithdraw | yes | Revoke a work authorisation whose owner is the caller's registration, as its owner withdraws the work it covers. Narrows only; refused with `FORBIDDEN` for any other caller |
| POST | /v1/model/audit | ModelAudit | yes | Append a registered component's completion's entry to this orchestrator's audit log, for the model gateway inside its own process alone ([Recording what the model routes do](#recording-what-the-model-routes-do)). Generated, and not platform-provided |

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
It serves **only** those. Every other group belongs to the provider
[`architecture/admin`](admin.md#the-admin-api-is-an-aggregate)'s provider
table names for it; each provider specifies and serves its own, and
[`architecture/admin`](admin.md) composes them behind one operator surface.

Every endpoint here requires the stated capability from
[`protocol/types`](../protocol/types.md), carried in the caller's token: an
`admin:` capability; `llm:chat`, for asking the tenant's model for a
completion; or, for recording and withdrawing a model provider agreement,
`model:attest`. A completion spends what the tenant pays for its model and
sends what it carries to a model provider, so it is not a read, and no
`admin:` capability reaches it. A request can use a capability only when the
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
administrative route ([A model is a destination](#a-model-is-a-destination)),
and asks it for a completion at `POST /v1/model/complete`, the model
service's route, which the same model gateway serves
([`architecture/model-service`](model-service.md)).

| Method | Path | Operation | Capability | Purpose |
|--------|------|-----------|-----------|---------|
| POST | /v1/admin/operators/register | OperatorRegister | — | Register an operator, with no token. The first presents the bootstrap secret this orchestrator emitted and is admitted as admin; every later one is recorded pending until an operator whose request can use `admin:*` approves it (`OperatorApprove`). Returns a token ONLY when registration also approved — see [`architecture/admin`](admin.md#the-registration-response) |
| POST | /v1/admin/operators/token | OperatorToken | — | Issue an attestation token to a caller who signs `{hub_id, jti, name, timestamp}`, naming this hub, with the private key matching this orchestrator's record, refusing a `jti` already recorded for that operator with `TOKEN_REQUEST_REPLAYED`. Unauthenticated by token, because it is what issues them. Deprecated as a way to an operator token — see [`architecture/admin`](admin.md#the-identity-signs-only-to-attest) |
| POST | /v1/admin/credentials/challenge | CredentialChallenge | — | Issue a single-use nonce for a credential |
| POST | /v1/admin/credentials/token | CredentialToken | — | Issue an operator token to a credential that signed the nonce. The ordinary way to an operator token |
| POST | /v1/admin/hub/proof | HubProof | — | Sign, with the key `hub_id` names, that this hub is reached at one of its admin addresses. Unauthenticated by token, because a client asks it before it holds anything here. Answered `501` `HUB_PROOF_UNAVAILABLE` until `weblisk/hub-proof/v1` has test vectors — see [`architecture/admin`](admin.md#proving-the-hub-at-an-address) |
| POST | /v1/admin/operators/{name}/key | OperatorKeyChange | — | Change an operator's identity key, signed by the current key and the new one. Unauthenticated by token, because the two signatures authenticate it and the operator may hold no live credential — see [`architecture/admin`](admin.md#changing-an-identity-key) |
| POST | /v1/admin/operators/{name}/credentials | CredentialAttest | the operator's own token, able to use `admin:read`, or an attestation token for them | Attest a credential for that operator |
| GET | /v1/admin/operators/{name}/credentials | CredentialList | `admin:read` | That operator's credentials, revoked included |
| DELETE | /v1/admin/operators/{name}/credentials/{cid} | CredentialRevoke | the operator, able to use `admin:read`, or `admin:*` | Revoke one credential |
| GET | /v1/admin/operators | OperatorList | `admin:*`; with `identity_id`, `admin:read` | List operators; with `identity_id`, that one operator's `name` and `identity_id` alone, to a role carrying `content:read` ([`architecture/admin`](admin.md#admitting-the-operators-after-the-first)) |
| GET | /v1/admin/operators/{name} | OperatorGet | `admin:read` | Operator detail |
| DELETE | /v1/admin/operators/{name} | OperatorDelete | `admin:*` | Remove an operator, after step-up (`destructive-action-step-up`) |
| POST | /v1/admin/operators/{name}/approve | OperatorApprove | `admin:*` | Admit a registered operator, after step-up |
| PUT | /v1/admin/operators/{name}/role | OperatorRole | `admin:*` | Change an operator's role, after step-up |
| POST | /v1/admin/work-authorisations | WorkAuthorise | `work:authorise` | Make one work authorisation for each definition a `WorkAuthorisationRequest` names, in one act, or none — see [Work Exchange](#work-exchange-post-v1tokenwork) |
| GET | /v1/admin/work-authorisations | WorkAuthorisationList | `admin:read` | Every work authorisation, revoked and expired ones included, filtered by the query parameters `owner`, `actor` and `authorised_by` where given |
| POST | /v1/admin/work-authorisations/{id}/renew | WorkAuthorisationRenew | `work:authorise` | Set a new `not_after`, no more than 90 days ahead, judging its `capabilities` against the renewing person as at its making |
| DELETE | /v1/admin/work-authorisations/{id} | WorkAuthorisationRevoke | `work:authorise` for the person who made or last renewed it, or `admin:*` | Revoke it, with a reason |
| GET | /v1/admin/agents | AdminAgentList | `admin:read` | Agents with what the registry holds of each: name, type, version, `lease_state`, `registered_at` and `last_seen`, and no metrics, which another component holds ([`architecture/admin`](admin.md#get-v1adminagents)) |
| GET | /v1/admin/agents/{name} | AdminAgentGet | `admin:read` | Agent detail — its [AgentEntry](#agententry) without the token: `manifest`, `agent_id`, `lease`, `last_renewal`, `registered_at` and `last_seen` ([`architecture/admin`](admin.md#get-v1adminagentsname)), and no metrics or recent tasks, which this orchestrator neither holds nor handles. The entry's `token` is never answered |
| POST | /v1/admin/agents/{name}/deregister | AdminAgentDeregister | `admin:*` | Force-deregister an agent, after step-up (`destructive-action-step-up`) |
| GET | /v1/admin/overview | AdminOverview | `admin:read` | Summary of the state this orchestrator holds |
| GET | /v1/admin/audit | AdminAuditList | `admin:audit` | This orchestrator's audit log, with the query parameters and the answer of `GET /v1/audit` ([`protocol/spec`](../protocol/spec.md#get-v1audit)). The route a person reads it at; `GET /v1/audit` is a registered component's, and refuses a person's token ([Auth Middleware](#auth-middleware), step 6) |
| GET | /v1/admin/audit/export | AdminAuditExport | `admin:audit` | The entries `AdminAuditList` would answer for the same filters, unpaged. `format=json`, the default where `format` is absent, answers an array of `AuditEntry`. `format=csv` answers `text/csv` as RFC 4180 writes it: a header row naming `AuditEntry`'s fields in the order [`protocol/types`](../protocol/types.md) declares them, then one row for each entry, each field its value as text and an absent field empty. A field whose text begins with `=`, `+`, `-`, `@`, a tab or a carriage return has a single quote (`'`) put before it, before it is quoted as RFC 4180 requires, so a spreadsheet that opens the file evaluates no field as a formula: `AuditEntry`'s `target` and `detail` can carry text a registrant chose. Any other `format` is refused with 400 `INVALID_REQUEST` |
| GET | /v1/admin/records/orchestrator/snapshot | AdminRecordSnapshot | `admin:*` | Every store this orchestrator owns at one instant between writes, as a ustar archive led by a `RecordSnapshot`, for `weblisk tenant export` ([`architecture/storage`](storage.md#the-snapshot-route)). A second request while one is being written is answered `409` `RECORDS_SNAPSHOT_BUSY`, and each snapshot is recorded in the audit log. No route restores this store ([`architecture/storage`](storage.md#putting-a-store-back)) |
| GET | /v1/admin/model | AdminModelGet | `admin:read` | The tenant's model configuration, a `ModelConfig` ([The tenant's model](#the-tenants-model)), which every client reads here (platform-provided) |
| PUT | /v1/admin/model | AdminModelPut | `admin:*` | Replace it, refusing a backend this hub cannot run now, and record the change (platform-provided) |
| GET | /v1/admin/model/providers | AdminModelProviders | `admin:read` | Each backend this hub knows how to drive, whether it can run it now, and the models the backend's own list answers on **this hub's host** (platform-provided) |
| POST | /v1/admin/complete | AdminComplete | `llm:chat` | Run a completion on the tenant's model, behind the destination gate, and say which model ran (platform-provided) |
| POST | /v1/admin/model/agreements | AdminModelAgreementRecord | `model:attest` | Record a model provider agreement (platform-provided) |
| GET | /v1/admin/model/agreements | AdminModelAgreementList | `admin:read` | Every agreement, withdrawn and lapsed ones included (platform-provided) |
| DELETE | /v1/admin/model/agreements/{id} | AdminModelAgreementWithdraw | `model:attest` | Withdraw an agreement (platform-provided) |
| GET | /v1/admin/model/ceiling | AdminModelCeiling | `admin:read` | What a model backend may be sent now (platform-provided) |
| POST | /v1/admin/model/audit | AdminModelAudit | the one its `action` names | Append a model route's entry to this orchestrator's audit log, for the model gateway inside its own process alone ([Recording what the model routes do](#recording-what-the-model-routes-do)). Generated, and not platform-provided |
| GET | /v1/admin/resources | AdminResourceCatalogue | `admin:read` | The kinds this orchestrator owns, each a `CatalogueEntry`, for the admin gateway to compose the tenant's catalogue from ([Resources this orchestrator owns](#resources-this-orchestrator-owns)) |
| GET | /v1/admin/r/lease | AdminLeaseList | `admin:read` | Every agent's lease, each an `AgentLease`, as a `ResourceList` |
| GET | /v1/admin/r/lease/{name} | AdminLeaseGet | `admin:read` | One agent's lease, with its ETag |
| GET | /v1/admin/events/agent | AdminAgentEvents | `admin:read` | The `agent` events after a position, as a `ResourceEventPage` ([`architecture/admin`](admin.md#the-feed)) |
| GET | /v1/admin/events/lease | AdminLeaseEvents | `admin:read` | The `lease` events after a position, as a `ResourceEventPage` |
| GET | /v1/admin/r/organisation | AdminOrganisationList | `admin:read` | Every organisation the tenant records, retired ones included, each an `Organisation`, as a `ResourceList` |
| POST | /v1/admin/r/organisation | AdminOrganisationCreate | `admin:*` | Record a new organisation, minting its `id` ([The tenant's organisations and projects](#the-tenants-organisations-and-projects)) |
| GET | /v1/admin/r/organisation/{uid} | AdminOrganisationGet | `admin:read` | One organisation, with its ETag |
| PATCH | /v1/admin/r/organisation/{uid} | AdminOrganisationUpdate | `admin:*` | Change its `display_name` or `operates_in` |
| POST | /v1/admin/r/organisation/{uid}/retire | AdminOrganisationRetire | `admin:*` | Retire it, once every project in it is retired |
| POST | /v1/admin/r/organisation/{uid}/restore | AdminOrganisationRestore | `admin:*` | Return a retired organisation to use |
| GET | /v1/admin/events/organisation | AdminOrganisationEvents | `admin:read` | The `organisation` events after a position, as a `ResourceEventPage` |
| GET | /v1/admin/r/project | AdminProjectList | `admin:read` | Every project the tenant records, retired ones included, each a `Project`, as a `ResourceList` |
| POST | /v1/admin/r/project | AdminProjectCreate | `admin:*` | Record a new project in an active organisation, minting its `id` |
| GET | /v1/admin/r/project/{uid} | AdminProjectGet | `admin:read` | One project, with its ETag |
| PATCH | /v1/admin/r/project/{uid} | AdminProjectUpdate | `admin:*` | Change its `display_name` |
| POST | /v1/admin/r/project/{uid}/retire | AdminProjectRetire | `admin:*` | Retire it |
| POST | /v1/admin/r/project/{uid}/restore | AdminProjectRestore | `admin:*` | Return a retired project to use, in an organisation that is not retired |
| GET | /v1/admin/events/project | AdminProjectEvents | `admin:read` | The `project` events after a position, as a `ResourceEventPage` |
| GET | /v1/admin/r/grant | AdminGrantList | `admin:read` | Every grant, revoked ones included, each a `RoleGrant`, as a `ResourceList` |
| POST | /v1/admin/r/grant | AdminGrantCreate | `admin:*` | Record a role one operator holds at one organisation or project, after step-up ([A role held at an organisation or a project](#a-role-held-at-an-organisation-or-a-project)) |
| GET | /v1/admin/r/grant/{uid} | AdminGrantGet | `admin:read` | One grant, with its ETag |
| POST | /v1/admin/r/grant/{uid}/revoke | AdminGrantRevoke | `admin:*` | Revoke a grant, after step-up |
| GET | /v1/admin/events/grant | AdminGrantEvents | `admin:read` | The `grant` events after a position, as a `ResourceEventPage` |

The six routes marked "after step-up" MUST be served as
[`architecture/admin`](admin.md#contracts)'s `destructive-action-step-up` says,
and `CredentialToken` MUST set `step_up_at` only as its
`operator-token-issuance` says; this document restates neither.
<!-- wl:id orchestrator-step-up -->

The model routes are marked `provided: platform` in the declaration. They are
NOT generated: the CLI installs them after generation, and they intercept their
own paths ahead of the generated router. A hub MUST serve all of them as this
section specifies; today's CLI serves four, and none of them as specified
([The tenant's model](#the-tenants-model), the gap note).

They are the tenant's model surface, and the model is the tenant's. Which
backend runs a completion, and which model it asks for, is the tenant's own
configuration, changed by a person at `PUT /v1/admin/model` and recorded in
this orchestrator's audit log ([The tenant's model](#the-tenants-model)).
Every client, the CLI and every console included, reads it here and keeps no
choice of its own for the tenant's work. The CLI installs the routes because
they find which backends the hub's host can run and run a completion through
one, which a generated component cannot do without reproducing the CLI's
provider catalogue. So the code is the CLI's and what it does is this
document's. The CLI chooses a model of its own only where no tenant's model
applies: when it creates a tenant, and for work a person starts outside any
tenant.

**Every one of them is authorised by the orchestrator.** The code the CLI
installs to serve them, inside the orchestrator's own process and called the
model gateway there, is neither the tenant's admin gateway nor its
application gateway. It has the orchestrator judge the caller's token on each
request, by
the middleware that guards every route under the same prefix: every step of
[Auth Middleware](#auth-middleware), step 6 included, which admits an
operator token alone under `/v1/admin/` and a registration token alone at
`/v1/model/ceiling`. It never accepts a token on its
shape, and a request it cannot get a judgement on is refused.
Asking a model for them produced four handlers against an unspecified
contract, all of them shadowed the moment the model gateway was installed.
That is why the marker exists, and all it changes is who writes them
([`schemas/architecture`](../schemas/architecture.md)). What they do is
specified below, in [The tenant's model](#the-tenants-model),
[Recording what the model routes do](#recording-what-the-model-routes-do) and
[A model is a destination](#a-model-is-a-destination), and the CLI's gateway is
held to it as generated code is held to its blueprint.

### Resources this orchestrator owns

What a person sees and operates of this orchestrator's state is declared once,
in the `resources:` key of the [Declaration](#declaration), as
[`schemas/resource`](../schemas/resource.md) says: the kinds `agent`, an entry
of the registry, and `lease`, the presence that entry holds. The admin gateway
serves both at the one address every kind is served at
([`architecture/admin`](admin.md#resources-one-api-for-every-kind)), and
forwards each request for them here on the person's operator token, as it
forwards every request for a group this orchestrator provides.

**An agent's operations are the routes that already serve them.** `list`,
`get` and the verb `deregister` bind `AdminAgentList`, `AdminAgentGet` and
`AdminAgentDeregister`, and nothing about those routes changes but two
additions: `AdminAgentGet` answers an `ETag` taken over the entry without its
volatile fields and without `token`, and `AdminAgentDeregister` compares an
`If-Match` it is given with that ETag and refuses a mismatch with
`RESOURCE_PRECONDITION_FAILED` ([`protocol/types`](../protocol/types.md#errorresponse)),
before the step-up is judged. A request at the route's own path that carries
no `If-Match` is served as it was; the uniform address is where one is
required. An agent is created and removed by its own registration, never by a
person, so the kind declares neither `create` nor `delete`; a person removes
one by `deregister`.

**A lease is read, never written by a person.** The orchestrator grants it at
registration and the holder renews it ([Presence](#presence)), so `lease`
declares `list` and `get` alone, served at the uniform address by
`AdminLeaseList` and `AdminLeaseGet`. An `AgentLease` is the entry's lease and
last renewal with the state derived as `GET /v1/admin/agents` derives it.

**What each kind announces.** An `agent` is `created` by a registration that
finds no entry, `updated` by one that changes the manifest, and `deleted` by a
deregistration the agent asked for itself; a forced one announces
`deregister`. These are the same acts that publish `system.agent.registered`
and `system.agent.deregistered` ([System Events](#system-events)), seen by a
person rather than by an agent. A `lease` is `created` when a registration
grants one and `updated` when a renewal changes what the lease says is ready;
a renewal that changes nothing announces nothing. **A lapse is not an event**,
here as on the directory: nothing acts when a lease lapses, and a client that
watches leases reads `expires_at` from the last event and shows the lease
`unknown` once it has passed, as this orchestrator would answer it.

`AdminAgentEvents` and `AdminLeaseEvents` answer what
[`architecture/admin`](admin.md#the-feed) asks of every owner's feed, as
`AdminOrganisationEvents`, `AdminProjectEvents` and `AdminGrantEvents` do for
the three kinds below, and `AdminResourceCatalogue` answers this
orchestrator's five `CatalogueEntry` values, each `available`, for the admin
gateway to compose the tenant's catalogue from.

### The tenant's organisations and projects

A tenant holds organisations, and an organisation holds projects
([`architecture/tenancy`](tenancy.md#architecture)). Which of them exist, what
each is called, which organisation a project is in, and the id a record joins
on are facts about the customer's organisation. So the tenant holds them, and
this orchestrator is where: it is the one component every tenant runs
([What a tenant consists of](#what-a-tenant-consists-of-and-where-that-is-declared)),
and the grants below are judged where operators are. No client and no host
holds them: a client reads them here, and a host's control plane keeps no
registry of them ([`architecture/tenancy`](tenancy.md#endpoints)). They are
the `organisation` and `project` kinds of the [Declaration](#declaration)'s
`resources:`, each an `Organisation` or a `Project`, held
in this orchestrator's own store beside its operators, so a tenant's rebuild
restores them with that store
([`architecture/tenancy`](tenancy.md#what-a-tenant-is-rebuilt-from)).

**The id is what a record joins on.** Each carries an `id`, 32 lowercase hex
characters minted when a person creates it, never changed and never reused. A
record that names an organisation or a project, whoever keeps it, names it by
this id and never by its name.

**The name is what a `scope_path` spells.** `name` is the segment the item
holds in every `scope_path` a content repository is declared at
([`architecture/content`](content.md#types)): `<tenant>/<organisation>` for an
organisation and `<tenant>/<organisation>/<project>` for a project, each by
its `name`. It is kebab-case, `[a-z][a-z0-9]*(-[a-z0-9]+)*`, set at creation
and never changed, because every repository declared at a `scope_path` was
declared at that name. No two organisations, and no two projects of one
organisation, ever hold one name, retired ones included, so a `scope_path`
never comes to name something else. A name already held is refused with
`SCOPE_NAME_TAKEN`, and one outside the grammar with `INVALID_REQUEST`. What a
person sees, and may change whenever they like, is `display_name`.

**A project is in one organisation for good.** `organisation` is set at
creation and never changed, so a project's records and its `scope_path` agree
for as long as it exists. A project is made only in an active organisation; one
asked for in a retired organisation is refused with `INVALID_STATE`.

**Retired, never deleted.** Neither kind declares `delete`, because a record
naming an id must still resolve. `retire` records that an item is no longer in
use and changes nothing that names it — no repository, adoption, record or
grant — and `restore` returns it to use. An organisation is retired only once
every project in it is, and a project restored only into an active
organisation; either asked for otherwise is refused with `INVALID_STATE`.

**Where an organisation operates.** `operates_in` lists the places it operates
in, in the grammar a standard's `applies_in` is written in
([`schemas/standard`](../schemas/standard.md#applies_in--where-a-standard-has-force)):
ISO 3166-1 alpha-2 and ISO 3166-2 codes, ascending, with no subdivision of a
country it already lists, and never `international`, which is a standard's
reach and nobody's place. A list outside that grammar is refused with
`INVALID_REQUEST`. **Absent means nobody has said**, and narrows nothing; it
is never read as everywhere or as nowhere. A client compares it with each
standard's `applies_in` to suggest what an organisation might adopt. It is
never an adoption, never hides a standard already adopted, and is never data
residency, which is the `jurisdiction` of
[`protocol/federation`](../protocol/federation.md) and a different question
([`schemas/standard`](../schemas/standard.md#it-is-not-jurisdiction-and-not-by-accident)).

**Who may change them.** Reading is `admin:read`; creating, updating, retiring
and restoring is `admin:*`. Each write is audited in this orchestrator's audit
log, admitted or refused, as every write at the uniform address is
([`architecture/admin`](admin.md#writes-and-what-guards-them)). Each kind
announces `created`, `updated`, `retire` and `restore`, so a client showing a
`display_name` reads it again on the event rather than keeping its own.

> **Gap — content does not check a `scope_path` against these records.** A
> repository may still be declared at a `scope_path` whose segments name no
> recorded organisation or project, or a retired one, and nothing refuses it
> ([`architecture/content`](content.md#declaration-flow)). Until content
> reads these records, a client reports such a repository as held at a scope
> the tenant does not record, and never invents an organisation for it.

### A role held at an organisation or a project

An operator's `role` holds across the tenant
([`architecture/admin`](admin.md#operator-roles)). A `RoleGrant` is
the record that an operator holds a role at one organisation, or at one project
of it: the `grant` kind of the [Declaration](#declaration)'s `resources:`, held
in this orchestrator's own store beside the operators it names. Every person
the tenant records is an operator ([`protocol/types`](../protocol/types.md#operator)):
a person who acts at the tenant registers and is admitted, and a grant names
that operator by `identity_id`. A person no operator record holds has no grant.

What a grant means, once something judges it (the gap below):

1. An operator with no active grant acts with their role across the tenant,
   as every operator does today.
2. An operator with one or more active grants is **confined**. At an
   organisation or a project they act with the role of the most specific
   active grant covering it — a project's grant over its organisation's — and
   where no active grant covers it, not at all. A grant at an organisation
   covers it and every project in it.
3. A grant never raises an operator above their own role. What they may use
   at a scope is what both the grant's role and their own role carry, judged
   on each request, so lowering an operator's role lowers every grant they
   hold.
4. What is held at no organisation — agents, the model, operators, audit — is
   judged on the operator's own role, confined or not.

**Nobody grants or revokes for themselves.** A create naming the person making
it, or a `revoke` of a grant naming the person revoking it, is refused with
`GRANT_SELF_REFUSED` and changes nothing, whatever their role: a confined
admin who could revoke their own last grant would release themselves.

**A grant is made and revoked, never changed.** `create` and `revoke` take
`admin:*` and a step-up, as changing an operator's role does
([`architecture/admin`](admin.md#contracts), `destructive-action-step-up`).
A role changed at a scope is a revoke and a new grant, so the records say who
held what, where, and when. A revoked grant is kept and its `id` never reused.
A grant naming an operator that is not `approved`, an organisation or project
that is not active, or a project that is not in the organisation it names is
refused with `INVALID_STATE`. **Revoking an operator's last active grant ends
their confinement**: the `revoke` verb says so in its effect, and a client
says so before a person confirms it. Each grant announces `created` and
`revoke`.

> **Gap — nothing judges a grant yet.** This orchestrator judges a person's
> capabilities from their role, on its own routes and at the exchange for a
> pass, and neither knows the organisation or project a request reaches: a
> pass names a route and its capabilities
> ([`protocol/identity`](../protocol/identity.md#the-pass)), and the owner
> that knows a request's `scope_path` is given capabilities, not grants. So a
> grant is recorded, listed and announced, and confines nobody. A client may
> narrow what it shows a person by their grants, and says that the tenant
> does not enforce it; it never presents that narrowing as the tenant's
> refusal. Closing this is carrying a confined operator's grants on the pass,
> and having the owner judge them against the scope of the request.

### The tenant's model

The tenant's model configuration is a [`ModelConfig`](#modelconfig): the
backend completions run on (`provider`), the model a person chose for it
(`model`), where a backend reached over HTTP listens (`base_url`), and a model
for each role a person gave one (`roles`). The hub keeps it as
`.weblisk/model.json` under its root. It holds no secret and names none: no
key, and no environment variable to read one from. `PUT /v1/admin/model` is
the one way it changes and the one way a change is recorded. An edit made to
the file by any other means is recorded nowhere.

**Nothing names a default model.** Where the configuration names no model,
the backend decides. A local model server is asked what it has loaded, as
its kind is asked, on every completion, and runs the first model it reports
loaded; a server that reports none is refused, and nothing is loaded on the
tenant's behalf. A person may choose a moving alias the backend lists, which
then moves with the backend. No model name is written as a default into the
CLI's gateway, a hub or this corpus, and the model that ran is taken from the
backend's answer, never from what was asked for.

**`GET /v1/admin/model`** answers the configuration as the hub holds it, and
`{}` where it holds none.

**`PUT /v1/admin/model`** replaces the configuration with its body. It is
refused, and changes nothing:

- with `INVALID_REQUEST` where the body is not a `ModelConfig`: `provider` is
  absent, a member `ModelConfig` does not declare is present, `api_key_env`
  among them, or a `roles` key is not a role name;
- with `MODEL_BACKEND_UNAVAILABLE` where the backend it names is not one this
  hub can run now, judged as `GET /v1/admin/model/providers` judges it and at
  the body's `base_url` where it has one;
- with `MODEL_NOT_LISTED` where `model`, or a model `roles` names, is not one
  that backend's own list answers just then, spelt as the list spells it. A
  backend whose list is empty takes neither, and decides.

It records the change before it makes it, and makes no change it cannot
record ([Recording what the model routes do](#recording-what-the-model-routes-do)).
It answers `{"config": <the ModelConfig as recorded>, "withdrawn": [<id>, ...]}`,
where `withdrawn` lists each agreement the change withdrew
([A model is a destination](#a-model-is-a-destination), Agreements) and is
empty where it withdrew none.

**`GET /v1/admin/model/providers`** answers, for each kind of backend this hub
knows how to drive, a [`ModelBackend`](#modelbackend): whether this hub can run
it now, why not where it cannot, and `models`, what the backend's own list
answered when this request asked it, on this hub's host. No entry names a
default model, and a list the backend did not answer is empty, never filled
in. A backend is available only where all three of these hold:

- **It answers here.** Its program is installed where the hub can run it, or a
  server answers at its address.
- **It needs no key.** The model gateway reads no key from its environment,
  because a key there reaches everything that process runs, and no blueprint
  yet gives the model gateway another place to take one from. A backend that
  needs a key is listed, and is not available.
- **It only answers.** A coding agent's command-line tool reads files and runs
  commands as well as answering. Run by the gateway as it is, it would act
  beside the hub's keys with nothing to confine it. One is available only where
  the gateway runs it answer-only and its own help advertises every flag that
  relies on ([Running a tool answer-only](#running-a-tool-answer-only)); any
  other is listed, and is not available.

`PUT /v1/admin/model` accepts only a backend this route would report
available, and `POST /v1/admin/complete` runs only one.

**`POST /v1/admin/complete`** runs one completion on the tenant's backend. Its
body is a [`CompletionRequest`](#completionrequest): the conversation, and the
`role` it is for and the `scope` it carries where it has them. It names no
backend and no model. The configuration chooses, and a request carrying
`provider` or `model` is refused with `INVALID_REQUEST`, so a client that
believed it was choosing learns that it was not. The model is the one `roles`
gives the request's `role`, else `model`, else the backend's choice. Once it
has read the body, the route records the completion before anything else,
and again when it ends
([Recording what the model routes do](#recording-what-the-model-routes-do)),
and keeps a `Completion` for it, with `route` `admin`, as for every
completion the tenant's model runs
([`architecture/model-service`](model-service.md#the-completion-record)).
It applies the destination gate before it runs anything
([A model is a destination](#a-model-is-a-destination)), and is refused:

- with `MODEL_NOT_CONFIGURED` where the hub holds no configuration;
- with `MODEL_BACKEND_UNAVAILABLE` where its backend is not one this hub can
  run now;
- with `MODEL_NONE_LOADED` where the configuration names no model for the
  request's role and the backend, a local model server, reports none loaded;
- with `MODEL_BACKEND_LIMITED` where the backend refuses under its own rate
  or quota limit, with `retry_after` only where the backend reported when its
  window resets
  ([`architecture/model-service`](model-service.md#limits));
- with `MODEL_BACKEND_FAILED` where the backend fails, or refuses the model it
  was asked for.

Nothing runs in place of what was refused or failed: no other backend, and no
other model. The route answers a [`CompletionResponse`](#completionresponse):
the answer, the backend that ran it, and `model`, the model the backend's own
answer says ran. Where the backend reports a model other than the one it was
asked for, as a moving alias does, `model` is the one it reports. Where its
answer names none, `model` is absent, so no client reads the name it asked
for as the one that ran.

| Code | HTTP | When |
|---|---|---|
| `INVALID_REQUEST` | 400 | `PUT /v1/admin/model`'s body is not a `ModelConfig`; `POST /v1/admin/complete`'s carries no message, or names `provider` or `model` |
| `MODEL_BACKEND_UNAVAILABLE` | 409 | The backend `PUT /v1/admin/model` names, or the one the configuration names at `POST /v1/admin/complete`, is not one this hub can run now. `detail` carries its `kind` and `detail` as `GET /v1/admin/model/providers` reports them |
| `MODEL_NOT_LISTED` | 409 | A model `PUT /v1/admin/model` names is not in its backend's own list just then |
| `MODEL_NOT_CONFIGURED` | 409 | `POST /v1/admin/complete` at a hub that holds no configuration |
| `MODEL_NONE_LOADED` | 409 | At `POST /v1/admin/complete`, the configuration names no model for the request's role and its backend, a local model server, reports none loaded. Nothing is loaded on the tenant's behalf |
| `MODEL_BACKEND_FAILED` | 502 | The backend failed to answer, or refused the model it was asked for. Nothing else was run |
| `MODEL_BACKEND_LIMITED` | 429 | The backend refused under its own rate or quota limit. `retry_after` is given only where the backend reported its reset. Nothing else was run |
| `MODEL_UNRECORDED` | 503 | The route could not record what it was about to do, so it did not do it, or what it did, so it does not answer with it |

> **Gap — the CLI's gateway serves four of the nine routes, and none of them
> as specified.** The model gateway the CLI installs today serves `GET` and
> `PUT /v1/admin/model`, `GET /v1/admin/model/providers` and
> `POST /v1/admin/complete`. It does not serve the three agreement routes,
> `GET /v1/admin/model/ceiling` or `GET /v1/model/ceiling`, and being
> `provided: platform` they are not generated either, so a request to any of
> them falls through to the generated router and is answered `404`. Of the
> four it serves:
>
> - `PUT /v1/admin/model` takes any `provider`, any `model` and an
>   `api_key_env`, asks no backend anything, and records nothing;
> - `GET /v1/admin/model/providers` gives each backend at most one model, from
>   a table the CLI wrote, and asks no backend for its list;
> - `POST /v1/admin/complete` is judged on `admin:read`, takes `model` from the
>   request, and where neither the request nor the configuration names one
>   asks for a model from that table, or for an empty name; it reports the
>   model it asked for as the one that ran; it records nothing; and it reads no
>   `scope` and applies none of the gate
>   ([A model is a destination](#a-model-is-a-destination)): it never refuses
>   `SCOPE_MISSING` or `SCOPE_CEILING_EXCEEDED`, and runs whatever it is sent,
>   `restricted` included.
>
> No hub serves `POST /v1/admin/model/audit` yet, and the CLI's gateway neither
> records through it nor intercepts it, so nothing a model route does is
> recorded at any tenant, and a hub generated with the route answers it from
> the network ([Recording what the model routes do](#recording-what-the-model-routes-do)).
> Until a hub serves all nine as specified:
>
> - a client MUST NOT read a `404` from either ceiling route as a ceiling. It
>   cannot learn one, so it uses `internal`, the ceiling a provider has with
>   nothing attested, as an api-ai endpoint that cannot learn a ceiling does
>   ([`patterns/api-ai`](../patterns/api-ai.md#destination-ceilings));
> - a client MUST apply the gate itself before it sends to `complete`, with
>   that ceiling, and MUST NOT rely on the hub to refuse anything: nothing
>   undeclared and nothing above `internal` is sent
>   ([`patterns/scope`](../patterns/scope.md#the-gate), every sender);
> - a client MUST NOT read the `model` of `complete`'s answer as the model that
>   ran, nor the one model `GET /v1/admin/model/providers` gives a backend as
>   what that backend lists;
> - no agreement can be recorded, so no provider's ceiling is above
>   `internal` at any tenant.
>
> Closing it is the CLI's: serve all nine routes as this document specifies
> them, and record through `POST /v1/admin/model/audit` once the orchestrator
> serves it.

### Running a tool answer-only

A coding agent's command-line tool is a backend only as the model gateway runs
it here: **answer-only**, so that what runs takes a prompt and gives an answer,
and the tool's own flags have taken away everything else it could do. For each
completion the gateway:

1. **Runs it once, non-interactively**, in its print mode, which answers and
   exits.
2. **Takes away every tool**: its built-in tools are an empty list, and a tool
   it would still ask permission for is refused, never waited on.
3. **Loads no MCP server**: only those its command line names, and it names
   none.
4. **Loads nothing a person or a project configured**: no settings file, hook,
   plugin, skill, slash command, custom agent or instruction file, from any
   user, project or local location. Any of them could give a tool back, or act
   in the tool's name.
5. **Keeps no session**: nothing is written that could be resumed.
6. **Runs it in an empty directory outside the tenant**, made for that
   completion, outside the hub's root, and removed when it ends.
7. **Gives it an environment of its own**, holding only what the tool needs to
   find its own sign-in: the home directory, the user's name, a temporary
   directory, and a search path naming the tool's own directory and the
   system's. Nothing else comes from the hub's environment: no `WL_` variable,
   no key, and no variable naming one.
8. **Sends the prompt on standard input**, the system prompt with it, and never
   as an argument, which every process on the host can read.
9. **Bounds it.** It reads at most a fixed amount of output, and refuses an
   answer longer than that rather than cutting it short. At the completion's
   deadline it kills the tool and every process the tool started, as one
   process group.

**Proved before it is offered.** A tool is available only where the gateway
has read its own `--help`, run as in 6 and 7 and bounded as in 9, and that help
advertises every flag 1 to 5 rely on, with the words a flag's meaning rests on
where it rests on a value: that `--tools ""` disables every tool, for one. A
tool whose help lacks any of them is listed, and is not available, its
`detail` naming what is missing. The proof is read again whenever the program
at that path changes. A host where the gateway cannot give the tool a process
group of its own cannot meet 9, and the tool is not available there.

**Signed in as itself.** The tool authenticates with its own sign-in on this
host, a person's subscription held where the tool keeps it. No key enters the
tenant: the gateway passes none and reads none, and a tool that would answer
only with a key in its environment needs a key, so is not available. Each
completion is spent against, and attributed by the vendor to, whoever signed
the tool in.

| Kind | Run answer-only | The flags it relies on |
|---|---|---|
| `claude-code` | Where its help advertises each flag | `--print`, `--output-format json`, `--tools ""`, `--strict-mcp-config`, `--safe-mode`, `--restricted`, `--disable-slash-commands`, `--no-session-persistence`, `--permission-mode dontAsk`, and `--model` where a model is named |
| `grok` | No: it ignores an empty `--tools`, measured, and no flag it offers is known to leave it none | |
| `codex` | No: no flag removes its tools, and `--sandbox read-only` still lets it read | |
| `opencode` | No: no flag removes its tools | |
| `local-cli` | No: it names no one tool | |

The gateway's proof decides, not this table: a row here is what the gateway
asks a tool's help for, and the gateway is held to it.

**What answer-only does not protect against.** It is a property of how the
tool is run, and no more than that:

- **The vendor sees the prompt and the answer**, as it does for any hosted
  model. The tool is a destination like any other, and the gate applies to
  it ([A model is a destination](#a-model-is-a-destination)).
- **It rests on the tool honouring flags it advertises.** Help proves that a
  flag is offered, not that it works, and one tool has been measured ignoring
  a flag it offers. It is not an operating-system sandbox: the tool runs as
  the hub's user, and a tool that ignored its flags could read and do what
  that user can.
- **Settings an administrator manages for the host still apply**, because the
  tool loads them whatever it is told.
- **The tool may update itself and send its own telemetry.** Neither is the
  gateway's to stop.
- **The sign-in is a person's.** A completion spends their subscription and is
  theirs to the vendor, not the tenant's.

### Recording what the model routes do

Every change `PUT /v1/admin/model` makes, every completion
`POST /v1/admin/complete` runs, and every agreement recorded or withdrawn is
an entry in this orchestrator's audit log. The model gateway cannot append one
itself: the log is this orchestrator's hash chain
([`architecture/storage`](storage.md#hash-chain-integrity)), and the gateway
can call nothing a generated orchestrator names. So the orchestrator serves
`POST /v1/admin/model/audit` (`AdminModelAudit`) for it, and the gateway
dispatches to it inside the process, with the token of the request it
records, as it already has the orchestrator judge every token. The gateway
intercepts that path ahead of the generated router, as it does the routes it
serves, and answers `404` to a request for it that arrives from outside the
process.

The route takes `action`, `target`, `detail` and `status`. `action` is one of
a closed set, each judged as the route it records is:

| `action` | Records | The request must be able to use |
|---|---|---|
| `model_set` | A change `PUT /v1/admin/model` is about to make: the configuration before and after, and each agreement it withdraws | `admin:*` |
| `model_complete` | A completion, twice. First, once its body is read and before anything else: the `role`, the `scope`, the backend, and the model it will ask for or that the backend chooses. Then, when it ends: the model the backend reported running or that it reported none, and how it ended, as below | `llm:chat` |
| `model_agreement_record` | An agreement recorded | `model:attest` |
| `model_agreement_withdraw` | An agreement withdrawn at `DELETE /v1/admin/model/agreements/{id}` | `model:attest` |

The orchestrator judges the token by [Auth Middleware](#auth-middleware), step
8 requiring the capability the action's row names, and appends an `AuditEntry`
with that `action`, `target`, `detail` and `status`, whose `actor` is the
token's `identity_id`. It answers `201` with the entry. It refuses an `action`
outside the set, and a `status` other than `ok`, `failed` or `denied`, with
`INVALID_REQUEST`. `target` names the backend or the agreement, and `detail`
says what changed or what ran and never carries a prompt, an answer or a key.

Every entry has `status` `ok` but a completion's second: each is appended
before its route acts, and says what the route is about to do, not how that
ends. A completion's second entry says how it ended: `ok` where the backend
answered; `denied` where the gate refused it, with `SCOPE_MISSING` or
`SCOPE_CEILING_EXCEEDED`; and `failed` where anything else ended it after its
first entry: its backend failing or refusing the model, a refusal with
`MODEL_NOT_CONFIGURED`, `MODEL_BACKEND_UNAVAILABLE` or `MODEL_NONE_LOADED`,
and a body that is not a `CompletionRequest`, refused with `INVALID_REQUEST`.
Its `detail` names the code it ended with, and the first entry for such a body
names what the body carried of `role` and `scope`.

A model route acts only on a `201`. `PUT /v1/admin/model` records before it
writes the configuration, and a completion's first entry is appended once
its body is read, before the gate or anything else, which is where its
`llm:chat` is judged. Its answer, or its refusal, goes back only once its
second entry is appended. A route that cannot record answers
`MODEL_UNRECORDED`, and a refusal of the token is relayed as the
orchestrator gave it.

The admin gateway carries no request for the path, and answers each `404`
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`).
From the network the route is reached only by a token sent to this
orchestrator directly, the gap at the boundary from the admin gateway
([Security](#security)). Where no model gateway intercepts the path, because
the platform installs none or installs one that does not know the route, as
the CLI's does not today (the gap note under
[The tenant's model](#the-tenants-model)), such a request reaches it, and a
person whose token can use an action's capability can append that action's
entry. It names them as its actor, so it records nothing in anyone else's
name.

**A registered component's completion is recorded at `POST /v1/model/audit`
(`ModelAudit`).** The model gateway also serves `POST /v1/model/complete`, the
model service's route for a registered component asking the tenant's model
on its own registration token
([`architecture/model-service`](model-service.md#asking-the-model-unattended)).
`AdminModelAudit` is under `/v1/admin/` and takes a person's operator token
alone, so the gateway records such a completion here instead, in the same
way: inside the process, with the token of the request it records, and
answering `404` to a request for the path from outside the process.
`ModelAudit` takes the same body, and admits one `action`, `model_complete`,
whose entries are written as the table above says, with the `run` and `phase`
the component stated named in the first entry's `detail`. The orchestrator
judges the token by [Auth Middleware](#auth-middleware): step 6 admits a
registration token alone, and step 8 requires that its `cap` name `llm:chat`.
It appends the entry, whose `actor` is the token's `identity_id`, and answers
`201` with it. It refuses an `action` other than `model_complete`, and a
`status` other than `ok`, `failed` or `denied`, with `INVALID_REQUEST`. The
admin gateway forwards nothing outside `/v1/admin/` to this orchestrator, so
it carries no request for the path. Where no model gateway intercepts the
path, a registered component whose token names `llm:chat` can append a
`model_complete` entry here, and it names that component as its actor.

### A model is a destination

A completion sends what it carries to a model provider, which is a destination
with a ceiling ([`patterns/scope`](../patterns/scope.md#destination-ceilings)).
The model routes are where the tenant applies that gate, holds the agreements
that raise a ceiling, and answers what a ceiling is.

**`POST /v1/admin/complete` applies the gate before it runs anything.** Its
request carries `scope`: the highest scope of what the prompt carries, as the
tenant reported it to the caller. A caller whose prompt carries nothing the
tenant holds says `public`. The route finds the ceiling of the backend it would
run and the model the configuration gives the request's role, its `roles`
entry or else `model`, as `GET /v1/admin/model/ceiling` answers it for that
backend and model. Where the configuration names neither, the backend's
choice runs, which no agreement can name, so the ceiling is the one a request
naming no model has, `internal`
([`patterns/scope`](../patterns/scope.md#model-providers)), even where the
model a local model server reports loaded first is one an agreement lists.
The route refuses:

- with `SCOPE_MISSING` when `scope` is absent;
- with `SCOPE_CEILING_EXCEEDED` when `scope` is above the ceiling, or is
  `restricted` or above whatever the ceiling.

Each refusal carries a `DestinationRefusal` naming the backend and its ceiling,
and runs nothing. The route never runs another backend instead. It cannot see
where the text in a prompt came from, so `scope` is the caller's statement and
the gate here is as good as the caller: that is why
[`patterns/scope`](../patterns/scope.md#the-gate) binds every sender, a client
included.

The CLI's gateway applies none of this gate today, and serves none of the
agreement or ceiling routes: what a client does until it does is the gap note
under [The tenant's model](#the-tenants-model).

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
  before the write and the request changes nothing of it but its models:
  `model`, and the model `roles` gives each role. It sets `withdrawn_by` from
  the request's token and `withdrawn_at`, and its answer names each one
  withdrawn. A request that changes only models, a role's included,
  withdraws nothing, because a ceiling is a model's as well as a name's:
  each model it sets has the agreement's level only where the agreement
  lists it, and `internal` otherwise. This is the one rule for what the
  request withdraws. Without it, a token narrowed for administration,
  carrying `admin:*` and not `model:attest`, could point a listed name at a
  party nobody attested and raise that party to the agreement's level; and
  without the ceiling being the model's, it could do the same by changing
  only a model, at a backend whose model chooses who runs it.
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
  route, so step 6 of Auth Middleware admits that token there and refuses an
  operator token, a channel token and the admin gateway's registration token,
  and an attestation token is refused there as everywhere but
  `CredentialAttest`. It
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
identity id ([Recording what the model routes do](#recording-what-the-model-routes-do)).

`/v1/admin/overview` reports what the orchestrator holds — agent counts,
namespace count and audit depth — and nothing else, in the members and
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
                        → publish system.agent.registered (unless a token renewal: step 10)
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
    - name: work-exchange
      description: Mint a work pass, for an actor a work authorisation names, under that authorisation (protocol/identity, The work pass)
      required: true
      rules:
        - The route POST /v1/token/work MUST take a WorkExchangeRequest and answer every judgement of the authorisation it names with 200 and a WorkExchangeResponse (protocol/types)
        - It MUST read the caller's token from the Authorization header alone, and admit only a registration token, one with no type and no cid, whose sub is a component registered here now, whose identity_id is that registration's, and whose registration declares work:exchange. Every other token MUST be refused with FORBIDDEN, disclosing nothing about the authorisation
        - A body missing authorisation, audience or run, or whose scope names a name protocol/types does not list, or names none while the audience is not the authorisation's owner, MUST be refused with 400 INVALID_REQUEST. An audience that is not the identity id of a component registered here now MUST be refused with 404 NOT_FOUND. Neither mints anything
        - It MUST answer issued false with WORK_AUTHORISATION_UNKNOWN for an authorisation it does not hold and for one whose actors do not name the caller's identity id, alike; WORK_AUTHORISATION_REVOKED for a revoked one; WORK_AUTHORISATION_EXPIRED for one past its not_after; and WORK_OWNER_UNREGISTERED where no component is registered here now under the identity id its owner names
        - The work pass's cap MUST be the intersection of scope, the authorisation's capabilities, and the capabilities the owner's, the caller's and the audience's registered manifests each declare. Where that intersection is empty it MUST mint nothing and answer issued false with FORBIDDEN, unless the audience is the authorisation's owner, to which it MUST mint a work pass with an empty cap (protocol/identity, The work pass, rule 11)
        - The work pass MUST carry what protocol/identity's The work pass gives it, with aud the audience, sub and identity_id the owner's, act the caller, cid the authorisation's id, definition the authorisation's and run the request's, and MUST carry no identity_key, record_keys, step_up_at or role
        - It MUST mint nothing but a work pass, and MUST NOT keep or cache one
        - Each request MUST be audited, refused or not, as work_exchange, with the authorisation's id, the run, the caller's identity id, the audience and the capabilities minted
    - name: work-authorisation
      description: Make, renew, revoke and surface a work authorisation (protocol/identity, The work pass, rules 1 to 6)
      required: true
      rules:
        - WorkAuthorise and WorkAuthorisationRenew MUST be admitted only on a person's operator token that can use work:authorise, and judge every capability an authorisation names against what that person may use at that moment - their role now and their token's cap. A capability they may not use MUST be refused with FORBIDDEN, a person-only one with CAPABILITY_PERSON_ONLY, and an admin capability, token:exchange, work:exchange or work:authorise with INVALID_REQUEST. A request any one of whose definitions is refused makes none
        - A request whose owner or any actor is not the identity id of a component registered here now MUST be refused with 404 NOT_FOUND, and one whose not_after is not in the future or is more than 90 days ahead with INVALID_REQUEST
        - Each authorisation MUST be recorded with authorised_by the person's identity_id, and audited as work_authorise or work_authorisation_renew with its owner, definition, actors, capabilities and not_after
        - WorkAuthorisationRevoke MUST admit the person who made or last renewed the authorisation, on a token that can use work:authorise, and a person whose token can use admin:*, and WorkAuthorisationWithdraw MUST admit only the registration its owner names. Each MUST record revoked_at, revoked_by and the reason given, keep the record, and audit it as work_authorisation_revoke. Nothing un-revokes an authorisation
        - OperatorDelete MUST revoke no work authorisation, and MUST name in its audit entry each live one the removed operator made or last renewed
        - A verified POST /v1/rotate-key MUST replace the rotating component's identity id with its new one in every authorisation that names it as owner or actor, auditing each as work_authorisation_rekey
        - A registration token, a pass and a work pass MUST NOT make, renew or widen an authorisation
    - name: token-exchange
      description: Exchange the operator token a person has just presented to the admin gateway for a pass addressed to one component
      required: true
      rules:
        - The route POST /v1/token/exchange MUST take a TokenExchangeRequest and answer every judgement of its subject_token with 200 and a TokenExchangeResponse (protocol/types)
        - It MUST read the caller's token from the Authorization header alone (Auth Middleware step 2), so nothing in the body, the token it exchanges included, authenticates the request. A request with no Authorization header MUST be refused with 401, as on any other route
        # <!-- wl:id exchange-declared-gateway-only -->
        - It MUST admit only a registration token, one with no type and no cid, whose sub is a component registered here now, whose identity_id is that registration's (protocol/identity), and whose registration declares token:exchange (protocol/types) and whose identity_id is orchestrator.admin_gateway_identity (schemas/config). Every other token Auth Middleware lets through MUST be refused with FORBIDDEN, disclosing nothing about subject_token - a registration token whose registration does not declare token:exchange, and one whose component has deregistered or whose identity_id is no longer its registration's, as after POST /v1/rotate-key (protocol/spec). An attestation token and a pass are refused before this, at Auth Middleware step 5, a pass with PASS_AUDIENCE_MISMATCH, and an operator token and a channel token at step 6, with FORBIDDEN
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
    name one protocol/types does not list → 400 INVALID_REQUEST, one whose
    capabilities name one protocol/types marks person only → 403
    CAPABILITY_PERSON_ONLY, one whose capabilities name token:exchange,
    which protocol/types marks admin gateway only, and whose public key's
    fingerprint is not orchestrator.admin_gateway_identity, or where that
    key is absent → 403 CAPABILITY_GATEWAY_ONLY, and one whose url
    contradicts the address the tenant declared for that component → 409
    ADDRESS_CONFLICT (What the directory attests), each before anything is
    recorded. Its
    pass_routes are not read for the second: a pass route names what the
    component checks on a person's pass, never what it holds, and none of
    it reaches the token of step 5. They are read for two things, each →
    400 INVALID_REQUEST before anything is recorded: a pass route naming a
    capability protocol/types does not list, in its capabilities or in a
    body requirement; and two pass routes that can match one request,
    which are two with the same method whose paths have as many segments,
    each pair of segments equal or one of them a {name} segment. So
    neither the token of step 5 nor an exchange the admin gateway asks
    names a capability that does not exist, and a request matches at most
    one of a component's pass routes
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
6.  Store agent in registry ({manifest, agentID, token, registeredAt,
    lastSeen} and its lease, as an AgentEntry). The lease is granted, or on
    a re-registration carried over, as protocol/spec §POST /v1/register
    step 8 says, and nowhere else
    Its ServiceEntry carries manifest.pass_routes unchanged, which is where
    the admin gateway learns what a person's request may reach on this
    component and what each needs (protocol/types, PassRoute)
7.  Build routing table entries for this agent's subscriptions:
    For each subscription → add RouteEntry to routing_table[pattern]
8.  Log audit entry: actor=orchestrator, action=register, target=agent_name
9.  Respond with RegisterResponse (includes agent_id, token, service directory
    and the lease)
10. Publish system.agent.registered (scope: "*") unless the agent
    re-registered with an unchanged manifest over a lease that is still
    current. So a first registration, a changed manifest, and a
    re-registration that step 6 grants a fresh lease (over a lapsed lease,
    or over one from before this orchestrator last started) each publish,
    and a token renewal publishes nothing. A component restarted with an
    unchanged manifest before its lease lapsed cannot be told from a token
    renewal here: it publishes nothing, and the renewal it sends as soon as
    its registration is answered carries its readiness
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

When `manifest.type = "domain"`, the orchestrator records the domain's
`required_agents` with its manifest and computes nothing from them. Whether a
domain can serve is its own readiness, carried on its own lease
([Presence](#presence)): it renews `ready: false`, its `checks` naming each
required agent whose lease does not read `ready` in the directory it holds,
until all of them do. A second domain status kept here would be a second
presence fact that could disagree with the lease.

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

Returns the complete service directory, a `ServiceDirectory`
([`protocol/types`](../protocol/types.md#servicedirectory)), including the
routing table and namespace map:

```json
{
  "services": [
    {
      "name": "seo-analyzer",
      "url": "http://localhost:9801",
      "public_key": "<ML-DSA-65 public key (base64url)>",
      "capabilities": ["file:read", "agent:message"],
      "lease_state": "ready",
      "lease_expires_at": "2024-04-03T16:00:30.000Z",
      "address_provenance": "self-asserted"
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
  },
  "updated_at": "2024-04-03T16:00:00.000Z"
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
registered agent via `POST /v1/services`, signed as
[`protocol/spec`](../protocol/spec.md#post-v1services) states, each with an
`updated_at` greater than the last it signed. It keeps that last `updated_at`
in its storage, so a restart, or a clock that steps back, never makes it sign
a lower one, which every agent would refuse as stale. Failures are logged but
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

Applied to all endpoints except `GET /livez`, `GET /readyz`, `POST /v1/register`, the four
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
   TokenExchange, WorkExchange and every /v1/admin/* route, whose token is
   read from the header alone
3. Verify token against orchestrator's signing key
4. Check expiry
5. Refuse a token whose type is "pass" or "work" with PASS_AUDIENCE_MISMATCH,
   on every route, and log it as a security event: this orchestrator is the
   audience of no pass and no work pass (protocol/identity, The pass and The
   work pass). Refuse a token whose type is
   "attestation" with CREDENTIAL_REQUIRED, on every route but
   CredentialAttest. On CredentialAttest, refuse it with
   OPERATOR_SUBJECT_MISMATCH unless its sub is the operator the path names
6. On every /v1/admin/* route, refuse a token whose type is not "operator"
   with CREDENTIAL_REQUIRED. CredentialAttest also takes the attestation
   token step 5 let through. An agent token and a channel token carry no type,
   so neither reaches an administrative handler.
   On every other route, each of them a registered component's, admit only a
   registration token, one with no type and no cid: refuse an operator token
   and a channel token with FORBIDDEN, and log a refused operator token as a
   security event that names it by its claims and never by the token
   (protocol/identity, The pass, rule 7). A registration token whose cap names
   token:exchange, or whose sub's registration declares it, as the admin
   gateway's does, is admitted at GET /v1/services, POST /v1/lease and
   TokenExchange alone, and refused with FORBIDDEN at every other such route,
   POST /v1/rotate-key among them: the gateway's key is changed only by
   the tenant's declaration (architecture/admin, Registration, lease and
   identity)
7. For an operator token, check the operator and the credential it names are
   live in this orchestrator's own records (architecture/admin,
   token-status-on-use)
8. On every /v1/admin/* route, check that the request can use the capability
   the route requires: the auth its declaration names; for a route
   architecture/admin's tables give a minimum role, the capability that
   minimum stands for; and for AdminModelAudit, whose declaration names
   "token", the capability its body's action requires (Recording what the
   model routes do), a body whose action is outside that set being refused
   with INVALID_REQUEST and judged no further. The request can use a
   capability when the operator's role carries it now and the token's cap
   names it, admin:* being read as each admin: capability by name. An
   operator token whose cap is absent or empty names none. Otherwise
   FORBIDDEN, whatever the role (architecture/admin, Auth Middleware).
   On ModelAudit, the one route outside /v1/admin/ judged here, refuse a body
   whose action is not model_complete with INVALID_REQUEST, judged no
   further, and a registration token whose cap does not name llm:chat with
   FORBIDDEN (Recording what the model routes do)
9. On failure → 401: INVALID_SIGNATURE from step 3, malformed tokens
   included, TOKEN_EXPIRED from step 4, PASS_AUDIENCE_MISMATCH from step 5,
   and {"error": "valid token required — register first"} where no token was
   presented; 403 FORBIDDEN from steps 6 and 8; 400 INVALID_REQUEST from
   step 8, for AdminModelAudit and ModelAudit alone; or the operator code
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
operator's credentials. In the other direction, a person's operator token
presented here directly would read the whole audit log at `GET /v1/audit`,
which `AdminAuditList` answers only a request that can use `admin:audit`, and
would deregister the agent its `sub` names at `DELETE /v1/register`, which
`AdminAgentDeregister` leaves to `admin:*`. A person's token reaches this
orchestrator only for a route under `/v1/admin/*` and as the subject of an
exchange ([`protocol/identity`](../protocol/identity.md#the-pass)), so no
route a component uses takes one. The admin gateway's registration reads the
service directory and exchanges, and does nothing else
([`architecture/admin`](admin.md#contracts), `admin-gateway-authorization`),
so step 6 admits its token at those two routes alone, and the audit log,
channels and a model's ceiling are refused it.

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

200 { "issued": true, "pass": "<WLT, type pass>", "expires_at": "2024-04-03T16:00:30.000Z", "capabilities": ["content:read"] }
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

## Work Exchange (POST /v1/token/work)

Work nobody is present for runs on its definition's owner's authority, as far
as a person allowed it, and is carried to each component on a work pass
([`protocol/identity`](../protocol/identity.md#the-work-pass)). This
orchestrator holds the record a work pass rests on, the work authorisation,
and is the one party that mints work passes, as it is the one that mints
passes.

```
POST /v1/token/work
Authorization: Bearer <the actor's own registration token>
{ "authorisation": "<work authorisation id>",
  "audience": "<identity id of the component the request goes to>",
  "scope": ["content:propose"],
  "run": "<the run's id>" }

200 { "issued": true, "pass": "<WLT, type work>", "expires_at": "2024-04-03T16:00:30.000Z", "capabilities": ["content:propose"] }
200 { "issued": false, "code": "WORK_AUTHORISATION_EXPIRED" }
```

`work-exchange` and `work-authorisation` in [Contracts](#contracts) are the
rules. The body is a `WorkExchangeRequest` and the answer a
`WorkExchangeResponse`, both [`protocol/types`](../protocol/types.md#workexchangerequest)'s.
Its shape follows the token exchange's: the actor, authenticated by its own
registration token, asks, and what it asks under is a record this orchestrator
holds rather than a token presented to it.

**A person makes the authorisation; nothing else can.** A person's client asks
for it at `POST /v1/admin/work-authorisations`, on the person's own token,
through the admin gateway, after the owner has installed the definitions it
covers and before any of them can run. The person sees each definition's
ceiling and the actors before they allow it
([`architecture/admin`](admin.md#work-authorisations)). A definition installed
with no authorisation is the owner's to report as not authorised, never as
running.

**Each answer about the authorisation is a 200**, so a status other than 200
judged the actor's own request, and the actor reports the run it could not
carry out by the code it was given: an expired authorisation is renewed by a
person, a revoked one is not, and an unregistered owner is a component to
start.

**A rotation carries the authorisations with it.** A component's identity id
is the fingerprint of its current key ([`protocol/spec`](../protocol/spec.md#post-v1rotate-key)),
so a key rotation would otherwise orphan every authorisation that names it.
The rotation is signed by the old key and the new one, which is continuity
enough to rename the component in each authorisation, and each renaming is
audited. A component that registers afresh under a new key has no such proof,
and no authorisation names it.

**Removing a person stops none of their authorisations.** The authority used
was never theirs. `OperatorDelete` names each live authorisation the person
made in its audit entry, and `WorkAuthorisationList` filters by
`authorised_by`, so the work they allowed is surfaced for another person to
renew or revoke.

---

## System Events

The orchestrator owns the `system.*` namespace and publishes lifecycle
events that all agents may subscribe to:

| Topic | Scope | Published When |
|-------|-------|----------------|
| `system.agent.registered` | `*` | An agent registered, except a re-registration with an unchanged manifest over a lease still current, such as a token renewal (Registration Flow, step 10) |
| `system.agent.deregistered` | `*` | Agent deregistered |
| `system.model.agreement_recorded` | `*` | A person recorded a model provider agreement. Carries its `id`, `party`, `backends`, `models`, `level`, `not_after` and `recorded_by` |
| `system.model.agreement_withdrawn` | `*` | A person withdrew one. Carries its `id`, `backends` and `withdrawn_by` |
| `system.shutdown` | `*` | Orchestrator is shutting down gracefully |

`system.agent.registered` and `system.agent.deregistered` are also the tenant's
**deploy markers**: a component that is upgraded or reconfigured registers a
changed manifest, one that starts after it deregistered registers with no
stored entry, one that starts after its lease lapsed (a crash, a kill, a long
stop) is granted a fresh lease, and one that stops cleanly deregisters, so
telemetry places these two on the investigator's timeline and needs no other
record of a deployment. A token renewal publishes nothing, so it is not a
deployment. One start is not marked: a restart with an unchanged manifest
quicker than the lease lapses, which registration cannot tell from a token
renewal (Registration Flow, step 10). A lease that lapses or recovers is not
an event: it is the entry's `lease_state`, carried by the next directory
broadcast.

System events are published via the same HTTP-based pub/sub mechanism.
The orchestrator resolves subscribers from its own routing table and
delivers via `POST /v1/event`.

---

## Audit Logging

Every operation creates an AuditEntry:

```json
{
  "id": "<generated>",
  "timestamp": "2024-04-03T16:00:00.000Z",
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
| `model_set` | The tenant's model configuration about to be changed, before and after |
| `model_complete` | A completion: what it will ask, before anything else, and what ran, when it ends |
| `work_authorise` | A work authorisation made, by whom, for which owner, definition, actors and capabilities, until when |
| `work_authorisation_renew` | A work authorisation's `not_after` moved, by whom |
| `work_authorisation_revoke` | A work authorisation revoked, by which person or owner, and why |
| `work_authorisation_rekey` | A component's identity id replaced in a work authorisation after its key rotation |
| `work_exchange` | A work pass asked for: the authorisation, the run, the actor, the audience and what was minted, or the code it was refused with |

Each entry is persisted to append-only flat-file storage (JSONL), which is the
record, and echoed to standard output as one log line whose `log_type` is
`audit` ([`patterns/logging`](../patterns/logging.md)).

---

## Presence

A registered component is present for as long as it holds a current lease, and
ready when its last renewal said so. The types and the three states are
[`protocol/types`](../protocol/types.md#presence)'; the route is
[`protocol/spec`](../protocol/spec.md#post-v1lease)'s. Leases follow the
Kubernetes model: the holder renews, and nobody probes.

What the orchestrator MUST do when a registration grants a lease, a renewal
arrives or a lease lapses is [`protocol/spec`](../protocol/spec.md#post-v1register)'s
(§POST /v1/register, §POST /v1/lease); how an entry reads is
[`protocol/types`](../protocol/types.md#leasestate)'s. Its lease lasts
`lease_duration` ([Configuration](#configuration)), and a deregistration ends
it with the registration. What is the orchestrator's own is below.

The orchestrator **never probes** a registered component for its presence or
readiness, and keeps no timer that calls one for them: a lapsed lease reads `unknown` and stays in the directory,
neither removed nor reported as failed, until the component renews or
deregisters. Restarting a component that stopped answering is the supervisor's
on its host, which reads `GET /livez`; judging whether a component is serving
its users well is telemetry's. **The directory and its leases are the one
authority for what is running and present**, so every reader asks the
directory and none keeps a second record of presence.

The orchestrator holds no lease of its own. It serves `GET /livez` and
`GET /readyz` like every component ([`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz)),
and it is ready once its registry, namespace map and audit log are loaded and
its listener is open (Startup Sequence, step 5). It is the one internal
component telemetry probes, since it cannot report itself to itself; no
registered component is polled for its presence or readiness by telemetry
either.

An orchestrator that restarts reads every lease it holds as `unknown` until
each component renews: it heard nothing while it was down, and says so. A
component that registers again after the restart first reads `not_ready`
until it renews (protocol/spec §POST /v1/register, step 8).

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
- **Leases** — per agent, the lease and its last renewal, held on the
  registry's entry ([AgentEntry](#agententry)). Its state is derived when read,
  never stored, because it changes with the clock.
- **Channel Registry** — Map of channel ID → active channel info, with
  1-hour TTL. Expired channels cleaned up periodically.
- **Audit Log** — Append-only flat-file (JSONL). In-memory buffer for
  recent entries, flushed periodically.
- **Work Authorisations** — Map of id → `WorkAuthorisation`, persisted, with
  revoked ones kept and no id reused ([Work Exchange](#work-exchange-post-v1tokenwork)).
  Nothing about a work pass is stored: each is minted and forgotten.
- **Organisations, projects and grants** — Maps of id → `Organisation`,
  `Project` and `RoleGrant`, persisted and surviving restarts, with retired and
  revoked ones kept, no id reused and no name held twice
  ([The tenant's organisations and projects](#the-tenants-organisations-and-projects),
  [A role held at an organisation or a project](#a-role-held-at-an-organisation-or-a-project)).

---

## Configuration

| Setting | Flag | Configuration key | Default |
|---------|------|-------------------|---------|
| Port | `--port` | `orchestrator.port` | `9800` |
| Identity key path | `--keys` | — | Implementation-defined |
| Audit log path | `--audit` | — | Implementation-defined |
| Channel TTL | — | — | `3600` (1 hour) |
| Lease duration, how long a lease lasts from each renewal | — | `orchestrator.lease_duration` ([`schemas/config`](../schemas/config.md#orchestrator)) | `30s` |
| Admin addresses, the origins the admin gateway is reached at | — | `orchestrator.admin_addresses` ([`schemas/config`](../schemas/config.md#orchestrator)) | none |
| The addresses the admin gateway's requests arrive from | — | `orchestrator.admin_gateway_from` ([`schemas/config`](../schemas/config.md#orchestrator)) | none |
| The admin gateway's identity, the one registration admitted `token:exchange` | — | `orchestrator.admin_gateway_identity` ([`schemas/config`](../schemas/config.md#orchestrator)) | none, so no registration is |

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
        type: timestamp
        required: true
        description: "The instant of registration"
      last_seen:
        name: LastSeen
        type: timestamp
        required: true
        description: "The instant of the last request received from the agent"
      lease:
        name: Lease
        type: Lease
        required: true
        description: "The agent's current lease (protocol/types, Lease). Past its `expires_at` the entry reads `unknown`"
      last_renewal:
        name: LastRenewal
        type: LeaseRenewal
        required: false
        description: "The last renewal received (protocol/types, LeaseRenewal). Absent until the first renewal, when the entry reads `not_ready`"
```

### ModelConfig

The tenant's model configuration
([The tenant's model](#the-tenants-model)). The hub keeps it as
`.weblisk/model.json`. `GET /v1/admin/model` answers it and
`PUT /v1/admin/model` replaces it. It holds no secret and names none.

```yaml
types:
  ModelConfig:
    fields:
      provider:
        name: Provider
        type: string
        required: false
        description: "The backend completions run on: a `kind` `GET /v1/admin/model/providers` lists, lower-case. `PUT /v1/admin/model` requires it. Only the answer of `GET /v1/admin/model` at a hub that holds no configuration, `{}`, lacks it"
      model:
        name: Model
        type: string
        required: false
        description: "The model a person chose for `provider`, as the backend's own list spelt it when it was chosen. Absent: the backend decides, and a local model server runs the first model it reports loaded, asked on each completion"
      base_url:
        name: BaseURL
        type: string
        required: false
        description: "Where `provider` listens, for a backend reached over HTTP. Absent: where that kind of backend listens by default on this hub's host"
      roles:
        name: Roles
        type: "map[string]string"
        required: false
        description: "A model for each role a person gave one, on `provider`. Each key is a role a completion may state (`CompletionRequest.role`), made of lower-case letters, digits and `-`; each value a model, as `model` is. A role it does not name runs `model`"
```

### ModelBackend

One kind of backend this hub knows how to drive, as
`GET /v1/admin/model/providers` answers it
([The tenant's model](#the-tenants-model)).

```yaml
types:
  ModelBackend:
    fields:
      kind:
        name: Kind
        type: string
        required: true
        description: "The backend, as `ModelConfig.provider` names it"
      label:
        name: Label
        type: string
        required: true
        description: "Its name for a person"
      local:
        name: Local
        type: bool
        required: true
        description: "True where it runs on this hub's host: a program here, or a server at an address on it"
      available:
        name: Available
        type: bool
        required: true
        description: "True where this hub can run it now: it answers here, needs no key and only answers"
      detail:
        name: Detail
        type: string
        required: true
        description: "In a sentence, why it is or is not available: where it was found, or what is missing"
      models:
        name: Models
        type: "[]string"
        required: true
        description: "What the backend's own list answered when this request asked it, on this hub's host, spelt as it spells them: for a local model server, the models it has loaded and those it can load. Empty where it lists nothing, cannot list, or is not available. Never a name written down in advance"
      loaded:
        name: Loaded
        type: "[]string"
        required: false
        description: "Of `models`, those a local model server reports loaded now, in its own order. With no model chosen, the first of them runs. Absent for a backend that does not say what it has loaded"
```

### CompletionRequest

The body of `POST /v1/admin/complete`
([The tenant's model](#the-tenants-model)). It names no backend and no model.

```yaml
types:
  CompletionRequest:
    fields:
      messages:
        name: Messages
        type: "[]CompletionMessage"
        required: true
        description: "The conversation, oldest first. At least one"
      system:
        name: System
        type: string
        required: false
        description: "Instructions put before the conversation"
      role:
        name: Role
        type: string
        required: false
        description: "The role the completion is for. Its model is the one `ModelConfig.roles` gives it, else `ModelConfig.model`"
      scope:
        name: Scope
        type: ScopeLevel
        required: false
        description: "The highest scope of what the prompt carries, as the tenant reported it to the caller. Absent is refused with `SCOPE_MISSING` (A model is a destination)"
  CompletionMessage:
    fields:
      role:
        name: Role
        type: string
        required: true
        description: "`system`, `user` or `assistant`"
      content:
        name: Content
        type: string
        required: true
        description: "The message, as text"
```

### CompletionResponse

The answer of `POST /v1/admin/complete`
([The tenant's model](#the-tenants-model)).

```yaml
types:
  CompletionResponse:
    fields:
      content:
        name: Content
        type: string
        required: true
        description: "The answer, as text"
      provider:
        name: Provider
        type: string
        required: true
        description: "The backend that ran it, as `ModelConfig.provider` names it"
      model:
        name: Model
        type: string
        required: false
        description: "The model the backend's own answer says ran, spelt as it spells it, so a moving alias is reported as the model it reached. Absent where the backend's answer names none, and never filled in with the model it was asked for"
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

  AgentSummary:
    description: One agent as GET /v1/admin/agents lists it, and the agent kind's list item
    fields:
      name:
        type: string
        description: The manifest's name
      type:
        type: string
        description: The manifest's type, an absent one read as agent
      version:
        type: string
        description: The manifest's version
      lease_state:
        type: string
        description: What the lease says now (protocol/types, LeaseState)
        constraints:
          enum: [ready, not_ready, unknown]
      registered_at:
        type: timestamp
        description: The instant of registration
      last_seen:
        type: timestamp
        description: The instant of the last request received from the agent

  AgentLease:
    description: The lease an agent's entry holds, as the lease kind answers it
    fields:
      agent:
        type: string
        description: The name of the agent that holds it
      lease_state:
        type: string
        description: What the lease says now, derived when read (protocol/types, LeaseState)
        constraints:
          enum: [ready, not_ready, unknown]
      ready:
        type: bool
        description: What the last renewal said, false until the first
      checks:
        type: map
        description: The last renewal's checks, where it carried any (protocol/types, LeaseRenewal)
      duration:
        type: int64
        description: Seconds the lease lasts from each renewal, as Lease's duration counts them (protocol/types, Lease)
      renewed_at:
        type: timestamp
        description: The instant of the registration or renewal that set it
      expires_at:
        type: timestamp
        description: The instant at which it lapses unless renewed

  Organisation:
    description: One organisation of the tenant, as the organisation kind answers it (The tenant's organisations and projects)
    fields:
      id:
        type: string
        required: true
        description: 32 lowercase hex characters, minted at creation, never changed and never reused. What a record names the organisation by
      name:
        type: string
        required: true
        description: Its segment of every scope_path, kebab-case. Set at creation, never changed, and never held by a second organisation
      display_name:
        type: string
        required: true
        description: What a person sees. Changed freely
      operates_in:
        type: "[]string"
        required: false
        description: The places it operates in, ISO 3166-1 alpha-2 or ISO 3166-2 codes, ascending, as schemas/standard writes applies_in, never international. Absent means nobody has said
      state:
        type: string
        required: true
        description: Whether it is in use
        constraints:
          enum: [active, retired]
      created_by:
        type: string
        required: true
        description: The identity id of the person who created it
      created_at:
        type: timestamp
        required: true
      retired_at:
        type: timestamp
        required: false
        description: Present while it is retired

  Project:
    description: One project of an organisation, as the project kind answers it (The tenant's organisations and projects)
    fields:
      id:
        type: string
        required: true
        description: 32 lowercase hex characters, minted at creation, never changed and never reused. What a record names the project by
      organisation:
        type: string
        required: true
        description: The id of the organisation it is in. Set at creation and never changed
      name:
        type: string
        required: true
        description: Its segment of every scope_path, kebab-case. Set at creation, never changed, and never held by a second project of its organisation
      display_name:
        type: string
        required: true
        description: What a person sees. Changed freely
      state:
        type: string
        required: true
        description: Whether it is in use
        constraints:
          enum: [active, retired]
      created_by:
        type: string
        required: true
        description: The identity id of the person who created it
      created_at:
        type: timestamp
        required: true
      retired_at:
        type: timestamp
        required: false
        description: Present while it is retired

  RoleGrant:
    description: A role one operator holds at one organisation or one project of it, as the grant kind answers it (A role held at an organisation or a project)
    fields:
      id:
        type: string
        required: true
        description: 32 lowercase hex characters, minted at creation, never reused
      identity_id:
        type: string
        required: true
        description: The operator's identity id (protocol/types, Operator)
      role:
        type: string
        required: true
        description: The role held there, an OperatorRole (protocol/types)
        constraints:
          enum: [viewer, auditor, operator, admin]
      organisation:
        type: string
        required: true
        description: The id of the organisation it is held at
      project:
        type: string
        required: false
        description: The id of the one project of that organisation it is held at. Absent, it is held at the whole organisation
      status:
        type: string
        required: true
        description: Whether it is held
        constraints:
          enum: [active, revoked]
      granted_by:
        type: string
        required: true
        description: The identity id of the person who made it, never the operator it names
      granted_at:
        type: timestamp
        required: true
      revoked_by:
        type: string
        required: false
        description: The identity id of the person who revoked it, never the operator it names
      revoked_at:
        type: timestamp
        required: false
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
    - boundary: Operator → Orchestrator, through the admin gateway, but for
        the first operator's registration at provision, which the CLI sends
        to the orchestrator's own address with the bootstrap secret and no
        token (architecture/cli, weblisk server provision). Registration and
        token issuance are signed and verified per architecture/admin; the
        orchestrator never authenticates an end user
    - boundary: Admin gateway → Orchestrator. A person's token is meant to
        arrive only from the admin gateway, to be judged on a route under
        /v1/admin/* or exchanged for a pass addressed to one other component
        (protocol/identity, The pass). Auth Middleware refuses it on every
        other route here (step 6), so it reaches no route a component uses.
        Nothing here enforces that it arrives from the gateway, which is a
        gap. The orchestrator serves /v1/admin/* on the listener components
        reach, to any caller, so a token a client sends there directly, as its
        own blueprint forbids, is judged by the same Auth Middleware as one
        the gateway forwarded, and can use there what it could have used
        through the gateway and nothing more. What such a request escapes is
        what the gateway checks before it forwards anything, its operator IP
        allowlist and its per-operator rate limits (architecture/admin, Admin
        Gateway Request Lifecycle), and nothing more, never the judgement of
        the token, and never the step-up a destructive act needs, which the
        orchestrator judges from the token's step_up_at itself, as the
        component that serves the act (architecture/admin,
        destructive-action-step-up). architecture/threat-model records
        it as residual. Serving the administrative routes on a listener only
        the admin gateway reaches is what would enforce the boundary
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
- [ ] `POST /v1/admin/operators/token` issues a token to an approved operator whose signature verifies against the stored public key — an attestation token, per [`architecture/admin`](admin.md#contracts)'s `attestation-token-issuance`
- [ ] `POST /v1/admin/operators/token` requires no bearer token — it is the endpoint that issues them ([`architecture/admin`](admin.md#contracts)'s `attestation-token-issuance`, [Auth Middleware](#auth-middleware))
- [ ] `POST /v1/admin/operators/token` refuses a request with no `jti` with `INVALID_REQUEST`, and one whose `jti` it has recorded for that operator with `TOKEN_REQUEST_REPLAYED`, as [`architecture/admin`](admin.md#contracts)'s `attestation-token-issuance` states
- [ ] An operator token carries the role and capabilities from the orchestrator's own record, never from the request ([Security](#security))
- [ ] `POST /v1/admin/credentials/challenge` and `POST /v1/admin/credentials/token` require no bearer token, and every other operator route refuses a token whose operator or credential is no longer live ([Auth Middleware](#auth-middleware) step 7, [`architecture/admin`](admin.md#contracts)'s `token-status-on-use`)
- [ ] The credential routes are served with the Operation names declared above: `CredentialChallenge`, `CredentialToken`, `CredentialAttest`, `CredentialList` and `CredentialRevoke` ([Administrative endpoints](#administrative-endpoints))
- [ ] `POST /v1/admin/operators/{name}/key` is served as `OperatorKeyChange`, requires no bearer token, and keeps the operator's `identity_id` while revoking its credentials ([`architecture/admin`](admin.md#contracts), `operator-key-change`)
- [ ] `POST /v1/admin/hub/proof` is served as `HubProof` and requires no bearer token: a request carrying none reaches its handler, and is never answered `401` `valid token required` ([`architecture/admin`](admin.md#contracts), `hub-proof`; [Auth Middleware](#auth-middleware))
- [ ] A token with `type` `attestation` is refused as [Auth Middleware](#auth-middleware) step 5 says, on every route but `CredentialAttest` (`GET /v1/audit` and `POST /v1/channel` included) and on `CredentialAttest` for any operator but its `sub`
- [ ] A token whose `type` is not `operator`, an agent token included, is refused with `CREDENTIAL_REQUIRED` on every `/v1/admin/*` route that requires a token, before the handler runs ([Auth Middleware](#auth-middleware) step 6)

- [ ] `POST /v1/register` verifies ML-DSA-65 signature and replay protection ([Registration Flow](#registration-flow-post-v1register) step 2)
- [ ] `POST /v1/register` enforces exclusive namespace ownership (409 on conflict) ([Namespace Enforcement Rules](#namespace-enforcement-rules))
- [ ] `POST /v1/register` rejects reserved namespace claims (403) ([Namespace Enforcement Rules](#namespace-enforcement-rules))
- [ ] `POST /v1/register` refuses a manifest naming any capability [`protocol/types`](../protocol/types.md#capability) marks person only, whichever it is, read from that list rather than from a copy of it, with 403 `CAPABILITY_PERSON_ONLY` ([Error Handling](../protocol/types.md#error-handling)), records no agent and issues no token
- [ ] A registration token carries `identity_id`, the fingerprint of `manifest.public_key` ([Registration Flow](#registration-flow-post-v1register) step 5)
- [ ] `POST /v1/register` validates subscription scopes (event:observe for "*") ([Registration Flow](#registration-flow-post-v1register) step 4)
- [ ] `POST /v1/register` returns `RegisterResponse` with agent ID, token, and service directory ([Registration Flow](#registration-flow-post-v1register) step 9)
- [ ] `DELETE /v1/register` releases owned namespaces and routing table entries ([Deregistration Flow](#deregistration-flow-delete-v1register))
- [ ] Service directory includes `routing_table` and namespaces map ([Service Directory](#service-directory-get-v1services))
- [ ] A `ServiceEntry` carries the `pass_routes` its manifest declared, unchanged, and a registration whose `pass_routes` name `content:write` or another person-only capability is not refused for it, while one whose `capabilities` names one still is with `CAPABILITY_PERSON_ONLY` ([Registration Flow](#registration-flow-post-v1register) steps 1 and 6)
- [ ] `POST /v1/register` refuses with 400 `INVALID_REQUEST`, recording nothing, a manifest naming a capability `protocol/types` does not list, in its `capabilities` or in a pass route's `capabilities` or body requirement, and one with two pass routes that can match one request, such as `GET /v1/x/{id}` and `GET /v1/x/special` ([Registration Flow](#registration-flow-post-v1register) step 1)
- [ ] A sixth request within a minute from one source to any one of the six administrative routes served without a token is refused before any signature is verified or made, the source being the `X-Forwarded-For` address only on a request from an address `orchestrator.admin_gateway_from` names, and the connection's address on every other, whatever `X-Forwarded-For` it carries ([Auth Middleware](#auth-middleware); [`architecture/admin`](admin.md#contracts), `auth-route-rate-limit`)
- [ ] Service directory broadcast to every other registered agent after every registration or deregistration ([Service Broadcasting](#service-broadcasting))
- [ ] `POST /v1/register` refuses with `409 ADDRESS_CONFLICT` when the registered `url` contradicts the address the tenant declared for that component ([What the directory attests, and what it does not](#what-the-directory-attests-and-what-it-does-not))
- [ ] Every `ServiceEntry` carries `address_provenance`, and an entry the orchestrator has not matched against the tenant's declaration reports `self-asserted` rather than omitting the field ([What the directory attests, and what it does not](#what-the-directory-attests-and-what-it-does-not))
- [ ] `address_provenance` is never reported as `verified` on the strength of an unauthenticated `GET /livez` or `GET /readyz` probe ([What the directory attests, and what it does not](#what-the-directory-attests-and-what-it-does-not))
- [ ] A `ChannelGrant` names a `target_url` only where the orchestrator would publish that address as `declared` ([Presenting a credential to a component](#presenting-a-credential-to-a-component))
- [ ] A `ChannelGrant`'s capabilities are the intersection of the requester's and the target's registered manifest, and no wider on either side ([Presenting a credential to a component](#presenting-a-credential-to-a-component))
- [ ] `POST /v1/channel` verifies `from_agent` matches token.sub ([Channel Brokering](#channel-brokering-post-v1channel) step 3)
- [ ] `POST /v1/channel` requires agent:message capability (403 if missing) ([Channel Brokering](#channel-brokering-post-v1channel) step 4)
- [ ] Channel tokens expire after the channel TTL ([Channel Brokering](#channel-brokering-post-v1channel) step 7, [Configuration](#configuration))
- [ ] Auth middleware rejects unauthenticated requests on protected endpoints ([Auth Middleware](#auth-middleware))
- [ ] On a `/v1/admin/*` route, Auth Middleware refuses with `FORBIDDEN`, before any handler, an operator token whose role carries the route's capability but whose `cap` does not name it, and reads a token only from the `Authorization` header ([Auth Middleware](#auth-middleware) steps 2 and 8)
- [ ] `GET /livez` and `GET /readyz` answer without auth with `live` or `ready` alone, and no count, version or name ([`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz))
- [ ] A first `POST /v1/register` grants a `Lease` of `orchestrator.lease_duration`, and the entry reads `not_ready` until the first renewal; a re-registration with an unchanged manifest over a current lease leaves its last renewal and `expires_at` unchanged, and one with a changed manifest, over a lapsed lease or over a lease from before the orchestrator's last start is granted a fresh lease that reads `not_ready` until the first renewal ([`protocol/spec`](../protocol/spec.md#post-v1register) step 8, [Presence](#presence))
- [ ] An entry whose lease is past `expires_at` reads `lease_state` `unknown`, stays in the directory, and is never reported `ready` ([Presence](#presence), [`protocol/types`](../protocol/types.md#leasestate))
- [ ] A renewal at `POST /v1/lease` after a lapse restores the lease without a new registration ([`protocol/spec`](../protocol/spec.md#post-v1lease) step 2)
- [ ] The orchestrator sends no request to a registered component to learn its presence or readiness, and has no setting that times, bounds or counts such a request ([Presence](#presence))
- [ ] A change of an entry's `lease_state` is followed by a `ServiceDirectory` broadcast ([`protocol/spec`](../protocol/spec.md#post-v1lease) step 3)
- [ ] system.agent.registered published after every registration except a re-registration with an unchanged manifest over a current lease, which publishes nothing ([Registration Flow](#registration-flow-post-v1register) step 10, [System Events](#system-events))
- [ ] system.agent.deregistered event published after deregistration ([Deregistration Flow](#deregistration-flow-delete-v1register) step 6)
- [ ] Every operation creates an `AuditEntry`, persisted to JSONL and echoed to stdout as an `audit` log line ([Audit Logging](#audit-logging))
- [ ] The orchestrator keeps no domain status of its own: a domain's readiness is its lease ([Domain Dependency Tracking](#domain-dependency-tracking))
- [ ] Orchestrator does NOT handle tasks, programme objectives or context, and holds no decision queue (it records, never makes, a person's decision); it serves neither the decision inbox nor any route for objectives ([Weblisk Orchestrator Blueprint](#weblisk-orchestrator-blueprint), its opening paragraphs)
- [ ] `DELETE /v1/admin/operators/{name}`, `POST /v1/admin/operators/{name}/approve`, `PUT /v1/admin/operators/{name}/role` and `POST /v1/admin/agents/{name}/deregister` are refused `STEP_UP_REQUIRED` on a token without a `step_up_at` recent enough for [`architecture/admin`](admin.md#contracts)'s `destructive-action-step-up`, and a token request whose `step_up` verifies mints a token carrying `step_up_at` <!-- wl:check orchestrator-serves-step-up covers orchestrator-step-up -->
- [ ] Administrative endpoints are gated on the capability each declares — an `admin:` capability, `llm:chat` or `model:attest` — carried in the caller's token, not on a separate role model ([Administrative endpoints](#administrative-endpoints))
- [ ] `POST /v1/admin/complete` refuses with `FORBIDDEN` a token that cannot use `llm:chat`, one carrying `admin:read` or `admin:*` without it included, and sends nothing to a backend ([Administrative endpoints](#administrative-endpoints), [Auth Middleware](#auth-middleware) step 8)
- [ ] `GET /v1/admin/model` answers the hub's `ModelConfig`, and `{}` at a hub that holds none ([The tenant's model](#the-tenants-model))
- [ ] `PUT /v1/admin/model` naming a backend `GET /v1/admin/model/providers` reports unavailable is refused with `MODEL_BACKEND_UNAVAILABLE`, one naming a `model` or a `roles` model the backend's own list does not hold with `MODEL_NOT_LISTED`, and one carrying `api_key_env` with `INVALID_REQUEST`; none of them changes `.weblisk/model.json` or appends a `model_set` entry ([The tenant's model](#the-tenants-model), [Recording what the model routes do](#recording-what-the-model-routes-do))
- [ ] An accepted `PUT /v1/admin/model` appends a `model_set` entry naming the configuration before and after before it writes anything, answers `config` and `withdrawn`, and changes nothing, answering `MODEL_UNRECORDED`, where `POST /v1/admin/model/audit` does not answer `201` ([The tenant's model](#the-tenants-model), [Recording what the model routes do](#recording-what-the-model-routes-do))
- [ ] `GET /v1/admin/model/providers` gives each `ModelBackend` the `models` its backend's own list answered for that request, names no default model, and reports `available` false for a backend that needs a key and for a coding agent's command-line tool the gateway does not run answer-only ([The tenant's model](#the-tenants-model), [Running a tool answer-only](#running-a-tool-answer-only))
- [ ] A coding agent's command-line tool whose own `--help` does not advertise every flag answer-only relies on is reported `available` false with a `detail` naming what is missing, and `PUT /v1/admin/model` naming it is refused with `MODEL_BACKEND_UNAVAILABLE` ([Running a tool answer-only](#running-a-tool-answer-only), [The tenant's model](#the-tenants-model))
- [ ] A completion on a coding agent's command-line tool runs it with every flag answer-only relies on and no prompt among its arguments, the prompt on its standard input, in a new empty directory outside the hub's root that is gone when it ends, with no `WL_` variable and no key in its environment, and kills it with every process it started at its deadline ([Running a tool answer-only](#running-a-tool-answer-only))
- [ ] `POST /v1/admin/complete` refuses a body naming `provider` or `model` with `INVALID_REQUEST`, runs the model `roles` gives the request's `role` and `model` otherwise, and answers a `CompletionResponse` whose `model` is the one the backend's answer names, absent where it names none ([The tenant's model](#the-tenants-model))
- [ ] A completion for which the configuration names no model, neither in `roles` for its `role` nor as `model`, at a local model server whose first loaded model a current agreement lists at `confidential`, is gated at `internal`, so a `confidential` one is refused with `SCOPE_CEILING_EXCEEDED` and runs nothing ([A model is a destination](#a-model-is-a-destination))
- [ ] A completion whose backend refuses under its own limit is answered `MODEL_BACKEND_LIMITED`, with `retry_after` only where the backend reported its reset, runs no other backend, and is kept as a `Completion` with `route` `admin` and `ended` `failed` ([The tenant's model](#the-tenants-model))
- [ ] A completion whose backend fails, or refuses its model, is answered `MODEL_BACKEND_FAILED` and runs no other backend or model, and one with no model chosen at a local model server that reports none loaded is answered `MODEL_NONE_LOADED` and loads nothing ([The tenant's model](#the-tenants-model))
- [ ] A completion appends a `model_complete` entry with `status` `ok` once its body is read and before the gate or anything else, and a second when it ends, with `status` `ok` where the backend answered, `denied` where the gate refused it, and `failed` for every other refusal or failure after the first, a body refused with `INVALID_REQUEST` included, its `detail` naming the code; and returns no answer or refusal whose second entry was not appended ([Recording what the model routes do](#recording-what-the-model-routes-do))
- [ ] `POST /v1/admin/model/audit` from outside the process is answered `404` where the model gateway is installed; dispatched in process, it judges the token on the capability its `action` names, refusing with `FORBIDDEN` a `model_complete` on a token that cannot use `llm:chat` and a `model_set` on one that cannot use `admin:*`, appends an `AuditEntry` whose `actor` is the token's `identity_id`, and refuses an `action` outside its set with `INVALID_REQUEST` before it judges any capability ([Recording what the model routes do](#recording-what-the-model-routes-do), [Auth Middleware](#auth-middleware) step 8)
- [ ] `POST /v1/model/audit` from outside the process is answered `404` where the model gateway is installed; dispatched in process, it refuses an operator token with `FORBIDDEN`, a registration token whose `cap` does not name `llm:chat` with `FORBIDDEN`, and an `action` other than `model_complete` with `INVALID_REQUEST`, and otherwise appends an `AuditEntry` whose `actor` is the token's `identity_id` ([Recording what the model routes do](#recording-what-the-model-routes-do), [Auth Middleware](#auth-middleware) steps 6 and 8)
- [ ] An admin's token whose `cap` names only `content:` capabilities is refused with `FORBIDDEN` at `OperatorApprove`, `OperatorRole`, `OperatorDelete`, `AdminAgentDeregister` and `CredentialRevoke`, its own credential included, and at `CredentialAttest` for the admin ([Administrative endpoints](#administrative-endpoints), [Auth Middleware](#auth-middleware) step 8)
- [ ] The orchestrator serves only the administrative endpoints backed by state it owns — operators, agents, its audit log, its own overview, and the tenant's model surface the CLI installs ([Administrative endpoints](#administrative-endpoints))
- [ ] `GET /v1/admin/audit` and `GET /v1/admin/audit/export` answer a request that can use `admin:audit` and refuse any other with `FORBIDDEN`, an agent token with `CREDENTIAL_REQUIRED`; the export answers the entries the list would for the same filters, as JSON where `format` is `json` or absent and as RFC 4180 CSV with a header row where it is `csv`, a field beginning with `=`, `+`, `-`, `@`, a tab or a carriage return written with a single quote before it, and refuses any other `format` with 400 `INVALID_REQUEST` ([Administrative endpoints](#administrative-endpoints), [Auth Middleware](#auth-middleware) steps 6 and 8)
- [ ] `/v1/admin/overview` reports only figures this orchestrator holds, and never reports a figure another component owns, as zero or otherwise ([A model is a destination](#a-model-is-a-destination), its closing paragraph on `/v1/admin/overview`, [`architecture/admin`](admin.md#get-v1adminoverview))
- [ ] `GET /v1/admin/agents/{name}` answers the agent's `manifest`, `agent_id`, `lease`, `last_renewal`, `registered_at` and `last_seen`, and no `status` or `token` member, so the registration token its `AgentEntry` holds, live for up to 24 hours and carrying the agent's capabilities, reaches no operator ([Administrative endpoints](#administrative-endpoints), [AgentEntry](#agententry), [Registration Flow](#registration-flow-post-v1register) step 5)
- [ ] `POST /v1/admin/complete` with no `scope` is refused with `SCOPE_MISSING`, one above the ceiling `GET /v1/admin/model/ceiling` reports for the backend and model it would run is refused with `SCOPE_CEILING_EXCEEDED`, and one at `restricted` is refused whatever the ceiling; none of them runs a backend ([A model is a destination](#a-model-is-a-destination))
- [ ] `POST /v1/admin/model/agreements` and `DELETE /v1/admin/model/agreements/{id}` refuse a token without `model:attest` with `FORBIDDEN`, including one holding `admin:*`, and a service's or an agent's token with `CREDENTIAL_REQUIRED` ([A model is a destination](#a-model-is-a-destination))
- [ ] A `PUT /v1/admin/model` on a token carrying `admin:*` and not `model:attest` that sets a name a current agreement lists, and changes anything of it but its models, `model` and the models `roles` gives, or held another name before, withdraws that agreement, names it in its answer, and `GET /v1/admin/model/ceiling` then answers that name `internal` ([A model is a destination](#a-model-is-a-destination))
- [ ] A `PUT /v1/admin/model` that keeps a listed name and changes only its model to one the agreement does not list withdraws nothing, and `GET /v1/admin/model/ceiling` then answers `internal` for that name and model, so a `confidential` `POST /v1/admin/complete` is refused with `SCOPE_CEILING_EXCEEDED`; changing it back to a listed model answers the agreement's level again ([A model is a destination](#a-model-is-a-destination))
- [ ] A `PUT /v1/admin/model` that keeps a listed name and changes only a `roles` entry withdraws nothing, and a completion stating that role is gated at the ceiling of the role's model: `internal` where the agreement does not list it, so a `confidential` one is refused with `SCOPE_CEILING_EXCEEDED`, and the agreement's level where it does ([A model is a destination](#a-model-is-a-destination))
- [ ] A recorded agreement's `recorded_by` is the token's `identity_id`, whatever the body says ([A model is a destination](#a-model-is-a-destination))
- [ ] An agreement whose `level` is `restricted` is refused with `MODEL_AGREEMENT_LEVEL_REFUSED`, one whose `not_after` is 91 days ahead with `MODEL_AGREEMENT_LAPSE_INVALID`, one with no `models` with `INVALID_REQUEST`, and one listing a model at a backend a current agreement covers for that model with `MODEL_AGREEMENT_EXISTS` ([A model is a destination](#a-model-is-a-destination))
- [ ] `GET /v1/admin/model/ceiling` answers `internal` for a backend no current agreement lists, for a model the agreement listing the backend does not list, and for a backend asked for no model, and `internal` again once the agreement that listed it lapses or is withdrawn ([A model is a destination](#a-model-is-a-destination))
- [ ] Either ceiling route answers a `?backend=` name the tenant's model configuration does not name, such as an api-ai endpoint's `providers:` key, with `internal` and no `address` where no current agreement lists it, and with the agreement's level where one does, and never with `NOT_FOUND` ([A model is a destination](#a-model-is-a-destination))
- [ ] `GET /v1/model/ceiling` answers a registered component's token with the `ProviderCeiling` `GET /v1/admin/model/ceiling` gives an operator for the same backend, `address` included where the backend has one, refuses an attestation token with `CREDENTIAL_REQUIRED`, and refuses an operator token, a channel token and the admin gateway's registration token with `FORBIDDEN` ([A model is a destination](#a-model-is-a-destination), [Auth Middleware](#auth-middleware) steps 5 and 6)
- [ ] Every platform-provided model route is authorised by the orchestrator's own judgement of the caller's token, and a `/v1/admin/*` one refuses an agent token with `CREDENTIAL_REQUIRED` ([Administrative endpoints](#administrative-endpoints), [Auth Middleware](#auth-middleware) step 6)
- [ ] `POST /v1/token/exchange` reads the caller's token from its `Authorization` header only: with no header it answers 401 whatever the body holds, and a body with no `subject_token` or no `audience` is refused with 400 `INVALID_REQUEST` ([Contracts](#contracts), `token-exchange`)
- [ ] `POST /v1/token/exchange` answers `issued: false` with `OPERATOR_REVOKED` for a token minted before its operator was removed, with `CREDENTIAL_REVOKED` after its credential was revoked, and with `TOKEN_EXPIRED` past its `exp`, each as a 200 ([Token Exchange](#token-exchange-post-v1tokenexchange), [`TokenExchangeResponse`](../protocol/types.md#tokenexchangeresponse)), and mints no pass
- [ ] `POST /v1/token/exchange` called with an operator token, a channel token, or the registration token of a component whose registration does not declare `token:exchange`, in its `Authorization` header, is refused with `FORBIDDEN`, with a pass with `PASS_AUDIENCE_MISMATCH` and a security event, and with an attestation token with `CREDENTIAL_REQUIRED`, and discloses nothing about `subject_token` ([Contracts](#contracts), `token-exchange`, [Auth Middleware](#auth-middleware) steps 5 and 6)
- [ ] `POST /v1/register` refuses a manifest naming `token:exchange` with 403 `CAPABILITY_GATEWAY_ONLY`, recording nothing, where its key's fingerprint is not `orchestrator.admin_gateway_identity` or none is configured, and admits it under the declared key; `POST /v1/token/exchange` refuses with `FORBIDDEN` a registration token whose `identity_id` is not that fingerprint ([Registration Flow](#registration-flow-post-v1register) step 1, [Contracts](#contracts), `token-exchange`) <!-- wl:check exchange-only-declared-gateway covers exchange-declared-gateway-only -->
- [ ] `POST /v1/token/exchange` called with the registration token of a component that has since deregistered, or whose identity id `POST /v1/rotate-key` has since changed, is refused with `FORBIDDEN` ([Contracts](#contracts), `token-exchange`)
- [ ] `POST /v1/token/exchange` asked to exchange a pass, a registration token or a channel token answers `issued: false` with `CREDENTIAL_REQUIRED`, so a pass is never exchanged again ([Contracts](#contracts), `token-exchange`)
- [ ] `POST /v1/token/exchange` with an `audience` that is not the identity id of a component registered here now, or that is the caller's own, is refused with 404 `NOT_FOUND`, and mints nothing ([Contracts](#contracts), `token-exchange`)
- [ ] `POST /v1/token/exchange` asked for `scope` `[content:read]` on an admin's token answers with a pass whose `cap` is `[content:read]` alone, whose `aud` is the audience, whose `act` names the gateway, and whose `exp` is no more than 30 seconds after its `iat`; asked for `[content:decide]` on a `viewer`'s token, or on an admin's token minted with `cap` `[content:read]`, it answers `issued: false` with `FORBIDDEN` ([Contracts](#contracts), `token-exchange`, [`protocol/identity`](../protocol/identity.md#the-pass))
- [ ] `POST /v1/token/exchange` asked for `scope` `[content:read, content:decide]` on a `viewer`'s token answers with a pass whose `cap` is `[content:read]` alone, and asked for `[admin:*]` on an `operator`'s token, whose role carries three of the four `admin:` capabilities, answers `issued: false` with `FORBIDDEN` ([Contracts](#contracts), `token-exchange`)
- [ ] An operator token whose `cap` is the empty list, as a `viewer` gets asking for `cap` `[fabric:attest]`, or that carries no `cap` claim, is refused with `FORBIDDEN` at every `/v1/admin/*` route Auth Middleware step 8 covers, and `POST /v1/token/exchange` answers it `issued: false` with `FORBIDDEN` for any `scope` ([Auth Middleware](#auth-middleware) step 8, [Contracts](#contracts), `token-exchange`)
- [ ] Every exchange is audited, refused or not, with the person's identity id, the gateway's identity id, the audience and the scope, and `subject_token` is never kept or presented anywhere ([Contracts](#contracts), `token-exchange`)
- [ ] A pass or a work pass presented at any route of the orchestrator is refused with `PASS_AUDIENCE_MISMATCH` and logged as a security event ([Auth Middleware](#auth-middleware) step 5)
- [ ] `POST /v1/token/work` admits only a live registration token whose registration declares `work:exchange`, answers `WORK_AUTHORISATION_UNKNOWN` alike for an unknown authorisation and one that does not name the caller, `WORK_AUTHORISATION_REVOKED`, `WORK_AUTHORISATION_EXPIRED` and `WORK_OWNER_UNREGISTERED` as their rule says, each in a 200 with `issued: false` ([Contracts](#contracts), `work-exchange`)
- [ ] A work pass's `cap` is the intersection of `scope`, the authorisation's `capabilities` and what the owner's, the actor's and the audience's manifests declare; an empty intersection mints nothing and answers `FORBIDDEN`, except for a work pass addressed to the authorisation's owner, which is minted with an empty `cap` ([Contracts](#contracts), `work-exchange`)
- [ ] A work pass carries `type` `work`, the audience as `aud`, the owner as `sub` and `identity_id`, the actor as `act`, the authorisation as `cid`, its `definition` and the request's `run`, expires no more than 30 seconds after it was issued, and carries no `identity_key`, `record_keys`, `step_up_at` or `role` ([Contracts](#contracts), `work-exchange`; [`protocol/identity`](../protocol/identity.md#the-work-pass))
- [ ] `POST /v1/admin/work-authorisations` admits only a person's operator token able to use `work:authorise`, refuses a capability the person may not use with `FORBIDDEN`, a person-only one with `CAPABILITY_PERSON_ONLY`, an admin or exchange capability with `INVALID_REQUEST`, a `not_after` more than 90 days ahead with `INVALID_REQUEST`, and makes none of a request any part of which is refused ([Contracts](#contracts), `work-authorisation`)
- [ ] A registration token, a pass and a work pass cannot make, renew or widen a work authorisation; an owner's registration can revoke one naming it as owner at `DELETE /v1/work/authorisations/{id}`, and any other caller is refused with `FORBIDDEN` ([Contracts](#contracts), `work-authorisation`; [Endpoints](#endpoints))
- [ ] `OperatorDelete` revokes no work authorisation and names each live one the removed operator made in its audit entry, and a verified key rotation renames the component in every authorisation naming it ([Contracts](#contracts), `work-authorisation`)
- [ ] Every work exchange and every making, renewal, revocation and renaming of a work authorisation is audited with the action [Audit Actions](#audit-actions) names for it ([Contracts](#contracts), `work-exchange`, `work-authorisation`)
- [ ] An operator token is refused with `FORBIDDEN`, before any handler, at every route outside `/v1/admin/*` that requires a token, and logged as a security event that names it by its claims and records no part of its bytes: a `viewer`'s token gets no entry from `GET /v1/audit`, and `DELETE /v1/register` on an operator token whose `sub` is a registered agent's name leaves that agent registered ([Auth Middleware](#auth-middleware) step 6)
- [ ] A channel token is refused with `FORBIDDEN` at every route outside `/v1/admin/*` that requires a token, and with `CREDENTIAL_REQUIRED` under it ([Auth Middleware](#auth-middleware) step 6)
- [ ] The admin gateway's registration token, whose `cap` names `token:exchange`, is answered at `GET /v1/services`, `POST /v1/lease` and `POST /v1/token/exchange`, and refused with `FORBIDDEN` at `GET /v1/audit`, `POST /v1/channel`, `GET /v1/model/ceiling`, `DELETE /v1/register` and `POST /v1/rotate-key` ([Auth Middleware](#auth-middleware) step 6)
- [ ] The orchestrator presents no token it received to any party: `GET /v1/admin/overview` asks no other component for a figure ([Security](#security), [A model is a destination](#a-model-is-a-destination), its closing paragraph on `/v1/admin/overview`)
- [ ] A token whose signature does not verify is refused with 401 `INVALID_SIGNATURE`, and one past `exp` with 401 `TOKEN_EXPIRED`, on every route Auth Middleware covers ([Auth Middleware](#auth-middleware) step 9)
- [ ] `GET /v1/admin/resources` answers `agent`, `lease`, `organisation`, `project` and `grant`, each `available`, with the declarations the [Declaration](#declaration)'s `resources:` holds, and no other kind ([Resources this orchestrator owns](#resources-this-orchestrator-owns))
- [ ] `AdminOrganisationCreate` and `AdminProjectCreate` mint an `id` of 32 lowercase hex characters that no item has held, and refuse a `name` an organisation, or a project of the same organisation, has ever held, retired ones included, with `SCOPE_NAME_TAKEN` ([The tenant's organisations and projects](#the-tenants-organisations-and-projects))
- [ ] A `PATCH` of an organisation or a project naming `id`, `name` or a project's `organisation` changes nothing and is refused as a field not settable there ([The tenant's organisations and projects](#the-tenants-organisations-and-projects); [`architecture/admin`](admin.md#writes-and-what-guards-them))
- [ ] An `operates_in` holding `international`, a code outside ISO 3166-1 alpha-2 and ISO 3166-2, a subdivision of a country it also lists, or codes out of ascending order is refused with `INVALID_REQUEST`; an organisation that has none answers no `operates_in`, never an empty list taken to mean everywhere ([The tenant's organisations and projects](#the-tenants-organisations-and-projects))
- [ ] `AdminOrganisationRetire` with an active project in the organisation, `AdminProjectCreate` or `AdminProjectRestore` in a retired organisation, and `AdminGrantCreate` naming an operator that is not `approved` or a scope that is not active, are each refused with `INVALID_STATE` and change nothing ([The tenant's organisations and projects](#the-tenants-organisations-and-projects), [A role held at an organisation or a project](#a-role-held-at-an-organisation-or-a-project))
- [ ] Neither `organisation`, `project` nor `grant` is answered at `DELETE`; a retired organisation or project and a revoked grant are still answered by `get` with their `id` ([The tenant's organisations and projects](#the-tenants-organisations-and-projects), [A role held at an organisation or a project](#a-role-held-at-an-organisation-or-a-project))
- [ ] `AdminGrantCreate` naming the person making it, and `AdminGrantRevoke` of a grant naming the person revoking it, are refused with `GRANT_SELF_REFUSED`, whatever that person's role, and change nothing ([A role held at an organisation or a project](#a-role-held-at-an-organisation-or-a-project))
- [ ] `AdminGrantCreate` and `AdminGrantRevoke` are refused without a recent re-confirmation, as `AdminAgentDeregister` is ([A role held at an organisation or a project](#a-role-held-at-an-organisation-or-a-project); [`architecture/admin`](admin.md#contracts), `destructive-action-step-up`)
- [ ] `AdminAgentGet` answers an `ETag` that does not change when only the agent's `last_seen`, `lease` or `last_renewal` changes, and `AdminAgentDeregister` given an `If-Match` that is not that `ETag` is refused `RESOURCE_PRECONDITION_FAILED` and deregisters nothing ([Resources this orchestrator owns](#resources-this-orchestrator-owns))
- [ ] `AdminLeaseEvents` announces `updated` for a renewal that changes `ready`, nothing for a renewal that changes nothing, and nothing when a lease lapses; `AdminAgentEvents` announces `created` for a first registration, `deleted` for a deregistration the agent asked for, and `deregister` for `AdminAgentDeregister` ([Resources this orchestrator owns](#resources-this-orchestrator-owns), [System Events](#system-events))
- [ ] `GET /v1/admin/records/orchestrator/snapshot` answers a request that can use `admin:*` with every store this orchestrator owns at one instant between writes, as [`architecture/storage`](storage.md#the-snapshot-route) gives it, refuses any other with `FORBIDDEN` and an agent token with `CREDENTIAL_REQUIRED`, appends an `AuditEntry` for each snapshot it answers, and no route restores the store ([Administrative endpoints](#administrative-endpoints), [Auth Middleware](#auth-middleware) steps 6 and 8, [`architecture/storage`](storage.md#putting-a-store-back))
