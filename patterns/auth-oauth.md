<!-- blueprint
type: pattern
name: auth-oauth
version: 1.0.0
requires: [protocol/types, patterns/auth-token, patterns/principal-identity, patterns/scope]
platform: any
tier: free
adoption: opt-in
-->

# Delegated Authorization Pattern

Admitting a client that the deployment has never met, on behalf of a person who can be
asked, and binding the resulting credential to one resource.

## Overview

`patterns/auth-token` issues credentials to callers a deployment already knows.
`protocol/identity` admits Weblisk components, which prove possession of a registered
key. Neither admits **an arbitrary client acting for a person** — a client that was not
pre-registered, that discovered the resource moments ago, and whose operator wants to
grant it a bounded slice of their own access.

That is what an external agent reaching a hub looks like, and it is the case delegated
authorization exists for. The pattern is adopted from the OAuth 2.1 family: the resource
advertises where to authorize, the client obtains a credential through a flow the person
consents to, and the credential names the person, the client, and the single resource it
is good for.

**The binding to one resource is the part that matters here.** A deployment hosting many
independent resources — many hubs, many tenants — must be able to state that a credential
issued for one is invalid at another. When that is a property of how the credential is
constructed and validated, cross-resource access is not a check that can be omitted.

`adoption: opt-in`. A deployment admitting no external clients serves none of this.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-token
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/principal-identity
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **A credential names one resource.** It carries the identifier of the resource it was
   requested for, and a resource refuses a credential naming a different one. Where a
   deployment hosts many resources, this is what makes them separate.
2. **The resource advertises where to authorize; the client does not guess.** A client
   that discovered a resource must be able to learn how to authorize against it from the
   resource itself, without configuration.
3. **The person consents, not the client.** Authorization is granted by a human who is
   shown what is being requested. A client cannot widen its own grant.
4. **Interception must not be enough.** Possession of an intercepted authorization
   response must not yield a credential; the exchange is bound to a secret the requesting
   client holds and never transmits.
5. **A grant is the least that satisfies the request.** A client asks for what the current
   operation needs, and asks again if it later needs more, rather than requesting
   everything it might ever need.
6. **Every credential expires, and every grant is revocable.** Neither is a background
   task: expiry is checked on use, and revocation takes effect at the next use.
7. **What a credential grants is decided at use, not at issue.** It names a principal and
   a scope; what that principal may currently do is resolved when the operation runs.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: advertise_authorization
      description: A protected resource tells an unauthenticated caller where and how to authorize
      parameters:
        - name: resource_identifier
          type: string
          required: true
          description: The canonical identifier of this resource, which credentials will be bound to
        - name: authorization_servers
          type: list
          required: true
          description: Identifiers of the authorization servers that may issue credentials for it
        - name: scopes_supported
          type: list
          required: false
          description: The scopes a client may request, as a starting point
      inherits: An unauthenticated request receives a challenge naming where to authorize, and a metadata surface describing it
      overridable: true
      override_constraints: The resource identifier MUST be the one credentials are validated against; it cannot differ between advertisement and validation

    - name: obtain_grant
      description: A client obtains a credential for one resource, with a person's consent
      parameters:
        - name: resource_identifier
          type: string
          required: true
          description: The resource the credential is being requested for
        - name: requested_scope
          type: list
          required: false
          description: The scopes the current operation needs
        - name: proof_of_possession
          type: string
          required: true
          description: A per-request secret the client proves it holds when exchanging the authorization result
      inherits: An authorization flow that ends in a credential naming the principal, the client, the resource and the granted scope
      overridable: true
      override_constraints: proof_of_possession MUST NOT be omitted, and MUST NOT be transmitted in the authorization request itself

    - name: validate_credential
      description: A resource decides whether a presented credential is good for it
      parameters:
        - name: credential
          type: string
          required: true
          description: The credential presented by the caller
        - name: resource_identifier
          type: string
          required: true
          description: This resource's own canonical identifier
      inherits: A resolved principal and scope, or a refusal
      overridable: false
      override_constraints: Not overridable — a resource that accepts a credential naming another resource breaks the separation the pattern exists to provide

    - name: challenge_insufficient_scope
      description: A resource tells a caller which additional scopes an operation needs
      parameters:
        - name: required_scope
          type: list
          required: true
          description: The scopes needed for the attempted operation
      inherits: A refusal that names what would be sufficient, so the client can ask once rather than repeatedly
      overridable: true
      override_constraints: The challenge MUST name every scope the operation requires; challenging one at a time forces repeated consent for a single action

    - name: revoke_grant
      description: A person withdraws a client's access
      parameters:
        - name: grant_id
          type: string
          required: true
          description: The grant to withdraw
      inherits: Subsequent use of credentials from that grant is refused
      overridable: true
      override_constraints: Revocation MUST take effect at the next use; deferring it to expiry is not revocation

  types:
    - name: ResourceMetadata
      description: What a resource publishes so a client can authorize against it
      inherited_by: The adopting component's public metadata surface
    - name: Grant
      description: A person's authorization of one client for one resource
      inherited_by: The adopting component's grant store
    - name: ResolvedCredential
      description: What validating a credential yields
      inherited_by: The adopting component's request context
```

---

## Types

```yaml
types:
  ResourceMetadata:
    description: Published by a protected resource so a client can learn how to authorize
    fields:
      resource:
        name: Resource
        type: string
        required: true
        description: "Canonical identifier of this resource; credentials are bound to it"
      authorization_servers:
        name: AuthorizationServers
        type: list
        required: true
        description: "Identifiers of servers that may issue credentials for this resource"
      scopes_supported:
        name: ScopesSupported
        type: list
        required: false
        description: "Scopes a client may request"

  Grant:
    description: One person's authorization of one client against one resource
    fields:
      grant_id:
        name: GrantID
        type: string
        required: true
        description: "Unique identifier"
      principal:
        name: Principal
        type: string
        required: true
        description: "The person who consented"
      client:
        name: Client
        type: string
        required: true
        description: "The client the grant was issued to"
      resource:
        name: Resource
        type: string
        required: true
        description: "The single resource this grant is good for"
      scope:
        name: Scope
        type: list
        required: true
        description: "Granted scopes"
      expires_at:
        name: ExpiresAt
        type: string
        required: true
        description: "RFC 3339 timestamp after which credentials from this grant are refused"
      revoked_at:
        name: RevokedAt
        type: string
        required: false
        description: "When the grant was withdrawn, if it was"

  ResolvedCredential:
    description: The result of validating a presented credential
    fields:
      principal:
        name: Principal
        type: string
        required: true
        description: "Who the caller is acting for"
      client:
        name: Client
        type: string
        required: true
        description: "What is acting"
      resource:
        name: Resource
        type: string
        required: true
        description: "The resource the credential named"
      scope:
        name: Scope
        type: list
        required: true
        description: "Granted scopes"
```

---

## Configuration

```yaml
config:
  credential_lifetime_seconds:
    type: int
    default: 3600
    overridable: true
    min: 300
    max: 86400
    description: How long an issued credential remains valid
  grant_lifetime_seconds:
    type: int
    default: 7776000
    overridable: true
    description: How long a grant may issue credentials before the person must consent again
  require_proof_of_possession:
    type: bool
    default: true
    overridable: false
    description: Whether the credential exchange must be bound to a client-held secret
```

---

## Error Handling

| Condition | Response | Carries |
|---|---|---|
| No credential presented | Refusal, with a challenge | Where to authorize, and the scopes the operation needs |
| Credential names a different resource | Refusal | Nothing about the other resource |
| Credential expired | Refusal, with a challenge | That re-authorization is required |
| Grant revoked | Refusal, with a challenge | That re-authorization is required |
| Scope insufficient | Refusal, with a challenge | Every scope the operation requires |
| Malformed request | Refusal | Which part was malformed, naming no internal detail |

---

## Implementation Notes

- **Validate the resource binding before anything else.** It is the cheapest check and the
  one whose omission is most consequential.
- **A refusal for a credential naming another resource must disclose nothing about that
  resource.** Including whether it exists.
- **Publish metadata at a stable, unauthenticated location.** A client that cannot read it
  without a credential cannot obtain one.
- **Expect the scope challenge to be the common path**, not the exception. A client asking
  for the least it needs will be challenged often, and that is the pattern working.
- **Do not reuse a grant across resources by widening it.** Two resources means two grants,
  which is what makes revoking one leave the other alone.
- **A deployment hosting many resources issues from one authorization server, not many.**
  The separation comes from the resource binding on each credential, not from running a
  server per resource.

---

## Verification Checklist

- [ ] An unauthenticated request to a protected surface MUST return a challenge naming where to authorize
- [ ] Published resource metadata MUST be readable without a credential
- [ ] A credential naming a different resource MUST be refused
- [ ] A refusal for a credential naming another resource MUST disclose nothing about that resource
- [ ] The credential exchange MUST be bound to a secret the client holds and does not transmit in the authorization request
- [ ] An expired credential MUST be refused at use, not merely at issue
- [ ] A revoked grant MUST be refused at the next use
- [ ] An insufficient-scope refusal MUST name every scope the attempted operation requires
- [ ] A resolved credential MUST yield a principal, a client, a resource and a scope
- [ ] The resource identifier advertised in metadata MUST be the one credentials are validated against
