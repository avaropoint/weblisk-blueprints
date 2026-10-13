<!-- blueprint
type: architecture
name: mcp
version: 1.4.6
requires: [protocol/types, protocol/identity, protocol/spec, architecture/agent, architecture/gateway, patterns/scope, patterns/safety, patterns/auth-oauth]
platform: any
tier: free
adoption: opt-in
-->

# Weblisk Model Context Protocol Surface

The surface through which an external AI agent reaches a hub's capabilities, using a
protocol it already speaks.

## Overview

`protocol/spec` defines how Weblisk agents reach each other. It does not help software
that is not a Weblisk agent. An external model — a coding assistant, a chat client, an
autonomous agent built on someone else's framework — has no way to discover what a hub
can do or to ask it to do anything.

The Model Context Protocol is the interoperability layer the wider ecosystem settled on
for that problem, and this blueprint specifies how a hub serves it.

**The surface is a projection, not a second system.** An MCP tool is a capability the
hub has already declared, rendered in MCP's vocabulary. A tool call becomes an agent
action that passes the same safety gate, the same scope, and the same audit as any other.
A capability reachable over MCP but not over the agent protocol would be a capability
outside the hub's governance, which is the failure this blueprint exists to prevent.

`adoption: opt-in`. A hub that exposes nothing to external agents serves none of this.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.15.0 <4.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
        # A tool projects a capability by its name. Capability carries no
        # description: a tool's is its ToolDefinition's own (Types)
        - name: Capability
          fields_used: [name]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/identity
    version: ">=1.14.4 <2.0.0"
    bindings:
      types:
        # Read only to recognise a person's operator token and refuse it
        # (The pass, rule 4); nothing here is authorised on one.
        - name: WLToken
          fields_used: [type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/spec
    version: ">=2.0.0 <4.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <3.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <3.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    # 2.1.0 is the first version that certainly holds DestinationRefusal and
    # DestinationItem: 2.0.0 named two states, the first without either
    version: ">=2.1.0 <3.0.0"
    bindings:
      types:
        # An enum: it declares values, not fields, so nothing is bound FROM it.
        - name: ScopeLevel
        - name: DestinationRefusal
          fields_used: [destination, ceiling, items]
        - name: DestinationItem
          fields_used: [ref, scope]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/safety
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        # The safety gate a tool call passes at step 5, on every invocation
        # and never cached across calls. The surface does not decide whether
        # an operation may proceed: the gate does
        - name: protection-gating
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-oauth
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        # What a tool call is admitted on, and what its audit entry names
        - name: ResolvedCredential
          fields_used: [principal, client, resource, scope]
      behaviors:
        - name: validate_credential
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
   External AI agent (not a Weblisk agent)
             │
             │  MCP over HTTP
             ▼
   ┌─────────────────────────────────────────┐
   │ MCP SURFACE                             │
   │                                         │
   │  discovery  ──► capabilities the caller │
   │                 is permitted to see     │
   │                                         │
   │  tool call  ──► authorize ──► resolve   │
   │                 scope ──► safety gate   │
   └──────────────────┬──────────────────────┘
                      │  becomes an agent action
                      ▼
   ┌─────────────────────────────────────────┐
   │ THE HUB — orchestrator, agents, domains │
   │ Same execution path as any other caller │
   └─────────────────────────────────────────┘
```

The surface **translates and admits**. It does not execute. Everything past the safety
gate is the hub's ordinary machinery, which is what keeps one governance model rather
than two.

Authorization is `patterns/auth-oauth`. This blueprint states where it is applied and
what the surface does with the result; it does not restate the flow.

---

## Responsibilities

**Owns**

- The MCP server surface: capability discovery and tool invocation
- The projection from a hub capability to an MCP tool definition
- Which capabilities are discoverable, and to whom
- Translating an MCP tool call into an agent action, and the result back
- Refusing a call that names anything the caller may not reach

**Does NOT own**

- Authorization — `patterns/auth-oauth`
- Whether an operation is permitted to proceed — `patterns/safety` and `patterns/policy`
- Execution — `architecture/agent` and the orchestrator
- What a capability is — `protocol/types`. A tool is a rendering of one, never a new one
- Agent-to-agent communication — `protocol/spec`, which external callers do not use

---

## Endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| GET | /.well-known/mcp | Capabilities | no | Server identity, protocol version, and publicly discoverable tools |
| POST | /.well-known/mcp | Invoke | yes | Tool listing and invocation |
| GET | /.well-known/oauth-protected-resource | ResourceMetadata | no | Where to authorize for this surface, per `patterns/auth-oauth` |

Discovery without credentials returns only what a hub has declared publicly
discoverable. A tool being discoverable does not make it callable: authorization is
evaluated on every invocation, never inferred from discovery.

---

## Interfaces

**Capabilities** returns the hub's identity, the protocol version it speaks, and the
tools the caller may see. An unauthenticated caller sees the publicly discoverable set;
an authenticated one sees what its grant permits.

**Invoke** carries a tool name and arguments. The surface resolves the tool to a declared
capability, constructs the corresponding agent action, and returns the result or a
structured error.

**Tool definitions are data.** They are declarations the hub holds, not code the surface
carries. An operator changes what is exposed by changing a declaration, and the surface
reflects it without redeployment.

---

## Data Flow

1. A caller requests capabilities. The surface answers from declarations, filtered by what
   the caller may see.
2. A caller invokes a tool, presenting a credential. The surface admits only one that
   [`patterns/auth-oauth`](../patterns/auth-oauth.md) issued for this surface
   (`validate_credential`), which names the person who consented, the client acting
   for them, this resource and the granted scope. A person's own token — an operator
   token, whatever its `cap` — is not one, and is refused with `PASS_REQUIRED` before
   any tool is resolved, and logged as a security event, as
   [`protocol/identity`](../protocol/identity.md#the-pass) requires of every component
   but the orchestrator and the admin gateway: the caller is a model, and no agent
   holds a person's token
   ([`architecture/admin`](admin.md#a-console-holds-a-credential-never-a-token)). What
   the caller may use is what the granted scope names, within what the person may use
   now, and never a capability [`protocol/types`](../protocol/types.md#capability)
   marks *person only*: the intersection
   [`patterns/principal-identity`](../patterns/principal-identity.md) requires of an
   agent acting for a person, so agents propose and people apply at this surface too.
   A deployment that issues no such credential admits no caller to invoke a tool, and
   serves discovery of the publicly discoverable set alone.
3. The surface resolves the tool name to a declared capability. An unknown name, or one
   outside the caller's scope or needing a capability step 2 left out, is refused — and
   these are refused identically, so the refusal does not disclose what exists.
4. Arguments are validated against the tool's declared input contract. Anything not
   declared is rejected rather than passed through.
5. The operation passes the safety gate, which may permit, require approval, or refuse.
6. The action executes as an agent action, under the caller's resolved scope.
7. The result passes the destination gate ([The destination gate](#the-destination-gate)).
   A result it refuses is not returned, in whole or in part.
8. The result is rendered back in MCP's vocabulary, and the call is audited with the
   person and the client the credential names, the tool, the outcome and the time, so
   the record names both whose authority was used and what used it.

> **Gap — nothing tells this surface what the person may use now.** Step 2 bounds a
> caller by what the person may use now, and no route answers that for this surface.
> It is presented a credential [`patterns/auth-oauth`](../patterns/auth-oauth.md)
> issued and never the person's operator token, so it has no token to have exchanged
> ([`protocol/identity`](../protocol/identity.md#the-pass)). No route answers a
> person's current capabilities for the principal a credential names, and nothing maps
> a granted scope to capabilities. Until one is specified, a person removed or lowered
> at the hub keeps what their client was granted here until `revoke_grant` withdraws
> the grant or `grant_lifetime_seconds` ends it, because removing or lowering a person
> at the hub withdraws no grant. This limit is stated here rather than left to be
> found.

### The destination gate

A tool result leaves the tenant. The caller is a model, or software that hands
what it is given to one, and a model is a destination with a ceiling
([`patterns/scope`](../patterns/scope.md#destination-ceilings)). The caller's
model provider is whoever the caller chose, and the hub cannot see who that is,
so no agreement can name it: **an MCP caller's ceiling is `internal`**, always,
whatever the caller's credential and whatever agreement the tenant has recorded
for its own model backends.

Before a result is returned, the surface applies
[`patterns/scope`](../patterns/scope.md#the-gate)'s gate to it with that
ceiling. The result's scope is the highest scope of everything it carries, as
the action reported it, never the surface's own reading of the text:

- **Undeclared.** A result that carries anything whose scope the action did
  not report is refused with `SCOPE_MISSING`.
- **Above the ceiling.** A result whose scope is above `internal`, and so every
  one that carries any part of a `restricted` or `critical` entry, is refused
  with `SCOPE_CEILING_EXCEEDED`.

Each refusal carries a `DestinationRefusal` naming the destination `mcp`, the
ceiling `internal`, and each item that set it off, and returns nothing of the
result. The surface never trims a result to fit, as the gate forbids. A
mutating tool's action has already run when its result is refused: the refusal
withholds what it returned, never what it did, and the audit records both.

---

## Design Principles

1. **A tool is a projection of a declared capability.** The surface exposes nothing the
   hub has not already declared. Two ways to reach one capability, never two capabilities.
2. **Scope is ambient.** The caller's scope is resolved from its credential and injected.
   No tool accepts a tenant, organisation, project or principal identifier as an argument,
   because an argument is something a model can be persuaded to change.
3. **Undeclared arguments are rejected, not ignored.** An argument the contract does not
   name is a caller doing something the contract did not anticipate.
4. **Discovery is not permission.** Every invocation is authorized on its own.
5. **Unknown and forbidden are indistinguishable.** A caller learns nothing about what it
   cannot reach.
6. **Reading is the default; acting is declared.** A capability that changes state is
   exposed only where an operator has declared it exposed, and passes the safety gate
   every time.
7. **The caller is untrusted input, and so is everything it was told.** An external agent
   may be relaying instructions from a document, a web page or another model. The surface
   trusts the credential, never the argument.
8. **What is returned has left.** A tool result reaches a model the hub did not choose,
   so it passes the same destination gate as anything sent to a model provider, at a
   ceiling no agreement raises. A credential that may read something does not make the
   caller a place it may be sent.

---

## Types

```yaml
types:
  ToolDefinition:
    description: A declared capability rendered as an MCP tool
    fields:
      name:
        name: Name
        type: string
        required: true
        description: "Tool name as callers address it"
      description:
        name: Description
        type: string
        required: true
        description: "What the tool does, written for a model to read"
      capability:
        name: Capability
        type: string
        required: true
        description: "The declared capability this projects"
      input_contract:
        name: InputContract
        type: map
        required: true
        description: "Declared argument names, types and constraints"
      mutates:
        name: Mutates
        type: bool
        required: true
        description: "Whether invoking it changes state"
      discoverable:
        name: Discoverable
        type: bool
        required: true
        description: "Whether it appears to an unauthenticated caller"

  ToolInvocation:
    description: A request to invoke a tool
    fields:
      tool:
        name: Tool
        type: string
        required: true
        description: "Tool name"
      arguments:
        name: Arguments
        type: map
        required: false
        description: "Arguments, validated against the tool's input contract"
      idempotency_key:
        name: IdempotencyKey
        type: string
        required: false
        description: "Required for a tool that mutates; a repeat returns the first result"

  ToolOutcome:
    description: The result of an invocation
    fields:
      status:
        name: Status
        type: string
        required: true
        description: "`ok`, `refused`, `pending_approval`, or `error`"
      content:
        name: Content
        type: map
        required: false
        description: "Result payload when the status is `ok`"
      reason:
        name: Reason
        type: string
        required: false
        description: "Why a call was refused or is pending, without disclosing what the caller may not see"
```

---

## Security

```yaml
security:
  trust_model:
    description: |
      The caller is an autonomous agent acting on instructions the hub cannot
      see. Those instructions may have come from a document, a web page, or
      another model, and may be hostile. The surface therefore trusts the
      credential and never the argument.

      This is the distinguishing property of this surface. Every other caller
      in the framework is a component whose behaviour is specified. An MCP
      caller's behaviour is determined by text that was not.

  boundaries:
    - boundary: External agent → MCP surface. The only boundary in the framework
        where the caller's instructions are unknown to the hub
    - boundary: MCP surface → Safety gate. Every invocation passes it; the
        surface does not decide whether an operation may proceed
    - boundary: MCP surface → Hub. A tool call becomes an ordinary agent action
        under the caller's resolved scope, with no elevated path
    - boundary: Caller scope → Everything else. Resolved from the credential and
        injected; never named by the caller

  enforcement:
    - rule: A scope identifier supplied as a tool argument is never used to
        select data
      mechanism: Scope resolved from the credential and injected as execution
        context; input contracts may not declare such an argument
    - rule: An argument the tool's input contract does not declare is rejected
      mechanism: Validation against the declared contract before dispatch,
        rejecting rather than ignoring unknown arguments
    - rule: A person's own token is never admitted
      mechanism: Only a credential patterns/auth-oauth validates for this
        resource resolves to a principal; an operator token, whatever its cap,
        is refused with PASS_REQUIRED and logged as a security event before
        any tool name is resolved (protocol/identity, The pass, rule 4)
    - rule: No action carries a person-only capability, whatever credential the
        caller presented
      mechanism: The caller's capabilities are resolved without every
        capability protocol/types marks person only, before the tool name is
        resolved, so a tool whose operation needs one is refused as an unknown
        one is
    - rule: An unknown tool and a forbidden tool are refused identically
      mechanism: A single refusal path with no distinguishing detail or timing
    - rule: Discovery returns nothing the caller may not reach
      mechanism: Declarations filtered by resolved scope before rendering
    - rule: A mutating tool executes only with an idempotency key and only where
        an operator has declared it exposed
      mechanism: Invocation refused when the key is absent; a repeat returns the
        first outcome rather than acting twice
    - rule: A mutating operation passes the safety gate on every invocation
      mechanism: patterns/safety evaluated per call, never cached across calls
    - rule: Every invocation is attributable
      mechanism: Audit records the person and the client the credential names,
        tool, arguments' declared names, outcome and time
    - rule: No tool result above internal, or with an undeclared scope, is
        returned to a caller
      mechanism: patterns/scope's destination gate applied to every result with
        the ceiling internal, refusing with SCOPE_MISSING or
        SCOPE_CEILING_EXCEEDED and returning nothing of the result
    - rule: An error discloses nothing about the hub's internals
      mechanism: Structured errors from the declared set; no internal identifier,
        query or stack detail crosses the boundary
```

---

## Implementation Notes

- **Render tools from declarations at request time.** A cached rendering is a second copy
  of the hub's capabilities, free to drift from what the hub will actually do.
- **Validate arguments before anything else.** It is the cheapest refusal and the one most
  likely to be exercised by a confused or hostile caller.
- **Write the audit entry before a mutating action, not after.** An action that fails
  after changing state is exactly the case the audit exists for.
- **Do not describe tools in terms of the hub's internals.** A description is read by a
  model deciding what to call. It should say what the tool achieves for the caller, and
  name nothing the caller cannot address.
- **Treat a refusal as a normal outcome.** Callers will attempt things they cannot do;
  that is discovery behaviour, not an incident, and logging it as an error buries the
  attempts that matter.

---

## Verification Checklist

- [ ] A tool's `input_contract` MUST NOT declare a tenant, organisation, project or principal identifier
- [ ] An argument not declared in `input_contract` MUST be rejected rather than ignored
- [ ] An unknown tool name and a tool outside the caller's scope MUST produce identical refusals
- [ ] A caller presenting a person's operator token, whatever its `cap`, is refused with `PASS_REQUIRED` before any tool is resolved, a security event is logged, and nothing is performed
- [ ] A caller whose credential `patterns/auth-oauth` issued for this surface, for a person whose role carries a capability [`protocol/types`](../protocol/types.md#capability) marks person only, invokes no tool whose operation needs one: the call is refused as an unknown name is, and nothing is performed
- [ ] Discovery without credentials MUST return only declarations marked discoverable
- [ ] An authenticated caller's discovery MUST return nothing outside its resolved scope
- [ ] A tool with `mutates: true` MUST be refused without an idempotency key
- [ ] A repeated invocation carrying the same idempotency key MUST return the first outcome without acting again
- [ ] Every invocation MUST pass the safety gate before execution
- [ ] Every invocation MUST produce an audit entry naming the person and the client its credential names, the tool, outcome and time
- [ ] An error response MUST NOT contain an internal identifier, query, or stack detail
- [ ] A read tool whose result carries a row of a `restricted` register is refused with `SCOPE_CEILING_EXCEEDED`, carrying a `DestinationRefusal` with ceiling `internal`, and returns no row of it, whatever the caller's credential may read
- [ ] A tool result that carries an entry whose scope the action did not report is refused with `SCOPE_MISSING`, and nothing of it is returned
- [ ] A tool result at `confidential` is refused although the tenant has recorded an agreement at `confidential` for its own model backend
- [ ] A mutating tool whose result is refused still records its action and its outcome in the audit, and returns nothing of the result
