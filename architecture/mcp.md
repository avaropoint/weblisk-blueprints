<!-- blueprint
type: architecture
name: mcp
version: 1.0.0
requires: [protocol/types, protocol/spec, architecture/agent, architecture/gateway, patterns/scope, patterns/safety]
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
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable, detail]
        - name: Capability
          fields_used: [name, description]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
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
  - blueprint: patterns/safety
    version: ">=1.0.0 <2.0.0"
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
2. A caller invokes a tool, presenting a credential. Authorization resolves it to a
   principal and a scope.
3. The surface resolves the tool name to a declared capability. An unknown name, or one
   outside the caller's scope, is refused — and the two are refused identically, so the
   refusal does not disclose what exists.
4. Arguments are validated against the tool's declared input contract. Anything not
   declared is rejected rather than passed through.
5. The operation passes the safety gate, which may permit, require approval, or refuse.
6. The action executes as an agent action, under the caller's resolved scope.
7. The result is rendered back in MCP's vocabulary, and the call is audited with the
   principal, the tool, the outcome and the time.

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
      mechanism: Audit records principal, tool, arguments' declared names,
        outcome and time
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
- [ ] Discovery without credentials MUST return only declarations marked discoverable
- [ ] An authenticated caller's discovery MUST return nothing outside its resolved scope
- [ ] A tool with `mutates: true` MUST be refused without an idempotency key
- [ ] A repeated invocation carrying the same idempotency key MUST return the first outcome without acting again
- [ ] Every invocation MUST pass the safety gate before execution
- [ ] Every invocation MUST produce an audit entry naming principal, tool, outcome and time
- [ ] An error response MUST NOT contain an internal identifier, query, or stack detail
