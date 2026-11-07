<!-- blueprint
type: architecture
name: testing
version: 2.7.0
requires: [protocol/identity, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
-->

# Weblisk Conformance Testing

A specification for verifying that an implementation of the Weblisk
Agent Protocol is correct. This document defines test fixtures, a mock
orchestrator, a mock agent, and the standard conformance flow that
every implementation MUST pass.

## Overview

Conformance testing verifies three things:

1. **Protocol compliance** — endpoints accept/return the right shapes
2. **Security compliance** — signatures, tokens, replay protection work
3. **Lifecycle compliance** — the full observe → recommend → approve →
   execute → feedback loop produces correct state transitions

Tests are black-box: they exercise HTTP endpoints and verify responses.
Implementations in any language can run the same test suite.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/identity
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: SigningKeyPair
          fields_used: [public_key, private_key, sign, verify]
        - name: SignatureVerification
          fields_used: [verify_signature, check_replay]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <7.0.0"
    bindings:
      types:
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: RegisterResponse
          fields_used: [agent_id, token, expires_at, services]
        - name: TaskRequest
          fields_used: [id, action, input]
        - name: TaskResult
          fields_used: [task_id, status, agent_name, output]
        - name: AgentManifest
          fields_used: [name, type, version, url, public_key, capabilities]
        - name: AgentMessage
          fields_used: [from, to, type, action, payload, signature]
        - name: ErrorResponse
          fields_used: [error, code]
        - name: ServiceDirectory
          fields_used: [services, routing_table, namespaces]
        - name: ChannelGrant
          fields_used: [channel_id, token, target_url]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=2.0.0 <4.0.0"
    bindings:
      types:
        - name: AgentEndpoints
          fields_used: [describe, execute, message, livez, readyz, services]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/domain
    version: ">=1.0.0 <4.0.0"
    bindings:
      types:
        - name: DomainManifest
          fields_used: [required_agents, workflows]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

Conformance testing verifies that an implementation does what its blueprints said,
using checks that could have failed.

```
   Blueprints ──► assertions ──► ┌──────────────────────┐
                                 │ TEST HARNESS         │
   Implementation ──────────────►│  reached / unreached │
                                 │  structural checks   │
                                 └──────────┬───────────┘
                                            ▼
                                   Conformance result
                              (names the checks it rests on)
```

**Responsibilities.** Deriving assertions from blueprints, running them against an
implementation, distinguishing a check that failed from one that never ran, reading
answers from an artifact's structure rather than its text, and producing a result
that names what it was based on.

**Not responsibilities.** Deciding what to build. Repairing an implementation, which
is generation's. Judging whether a blueprint's assertion is the right one.

---

## Responsibilities

### Owns
- Conformance test suite definition (Level 1: protocol, Level 2: security, Level 3: lifecycle)
- Test fixture definitions (deterministic ML-DSA-65 key pairs, manifest fixtures)
- Mock orchestrator specification and behavior contract
- Mock agent specification and configurable response contract
- Pass/fail criteria and assertion format for each test case

### Does NOT Own
- Implementation of the components under test (owned by platform documents)
- Running the suite: the engine's `test run` operation, which every front end
  renders ([`architecture/engine`](engine.md#the-one-conformance-suite))
- Production orchestrator or agent behavior (owned by their respective blueprints)
- Performance/load testing (out of scope — this is conformance testing only)
- Integration with external CI/CD systems (deployment-specific)

---

## Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| `test run` | Engine operation | Run the suite: against a tree, or its live-safe checks against a running component ([`architecture/engine`](engine.md#build-time-and-run-time)) |
| Mock Orchestrator: `POST /v1/register` | HTTP | Accept valid registrations, return token |
| Mock Orchestrator: `GET /livez`, `GET /readyz` | HTTP | Answer live and ready |
| Mock Orchestrator: `POST /v1/lease` | HTTP | Accept a renewal from a registered test agent, return its `Lease` |
| Mock Agent: `POST /v1/execute` | HTTP | Return configurable `TaskResult` |
| Mock Agent: `POST /v1/message` | HTTP | Return configurable response payload |

---

## Data Flow

1. Test harness starts mock orchestrator on port 19800
2. System under test (agent or orchestrator) is started on its configured port
3. Test harness builds a `RegisterRequest` with deterministic test keys
4. Test harness sends registration request and validates the `RegisterResponse`
5. Test harness sends task/message requests with valid tokens and verifies responses
6. For Level 2: test harness sends malformed signatures, expired tokens, and oversized payloads — verifies rejection
7. For Level 3: test harness starts full system (orchestrator + domain + agent) and executes end-to-end workflow
8. Workflow produces observations, recommendations, and feedback — test harness verifies state transitions
9. Test harness collects results and reports pass/fail per test ID
10. All assertions include test ID in failure messages for triage

---

## Test Fixtures

### Identity Fixtures

Fixed ML-DSA-65 key pairs for deterministic testing. These are TEST KEYS
ONLY — never use in production.

```
Test Orchestrator:
  name: "test-orchestrator"
  private_key: "0000000000000000000000000000000000000000000000000000000000000001" (test only)
  public_key:  derived from private key via ML-DSA-65

Test Agent (work):
  name: "test-agent"
  private_key: "0000000000000000000000000000000000000000000000000000000000000002" (test only)
  public_key:  derived from private key via ML-DSA-65

Test Domain:
  name: "test-domain"
  private_key: "0000000000000000000000000000000000000000000000000000000000000003" (test only)
  public_key:  derived from private key via ML-DSA-65
```

A component is started with one of these keys instead of a generated one by
the key file the harness writes before it starts it, as
[Starting a component with a fixture key](#starting-a-component-with-a-fixture-key)
says; it needs no flag of its own. This enables reproducible tests.

### Manifest Fixtures

**Test work agent manifest:**
```json
{
  "name": "test-agent",
  "type": "agent",
  "version": "1.0.0",
  "description": "Conformance test agent",
  "url": "http://localhost:9710",
  "public_key": "<derived from test key 2>",
  "capabilities": [
    {"name": "file:read", "resources": ["**/*.html"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [{"name": "files", "type": "file_list", "description": "Files to process"}],
  "outputs": [{"name": "report", "type": "json", "description": "Processing report"}],
  "max_concurrent": 5
}
```

**Test domain manifest:**
```json
{
  "name": "test-domain",
  "type": "domain",
  "version": "1.0.0",
  "description": "Conformance test domain",
  "url": "http://localhost:9700",
  "public_key": "<derived from test key 3>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "required_agents": ["test-agent"],
  "workflows": ["test-workflow"],
  "max_concurrent": 10
}
```

### Fixtures as data

The fixtures above, in the form a declared check reads them
([`schemas/blocks`](../schemas/blocks.md#checks), `${fixture/<name>/<pointer>}`).
An identity's `seed` is its ML-DSA-65 key-generation seed, and its
`public_key` is derived from it, base64url-encoded, never written here. These
are TEST KEYS ONLY.

```yaml
fixtures:
  test-orchestrator:
    seed: "0000000000000000000000000000000000000000000000000000000000000001"
  test-agent:
    seed: "0000000000000000000000000000000000000000000000000000000000000002"
    manifest:
      name: test-agent
      type: agent
      version: 1.0.0
      protocol_version: "1"
      description: Conformance test agent
      url: http://localhost:9710
      public_key: "${fixture/test-agent/public_key}"
      capabilities:
        - {name: "file:read", resources: ["**/*.html"]}
        - {name: "agent:message", resources: []}
      inputs: [{name: files, type: file_list, description: Files to process}]
      outputs: [{name: report, type: json, description: Processing report}]
      max_concurrent: 5
  test-domain:
    seed: "0000000000000000000000000000000000000000000000000000000000000003"
    manifest:
      name: test-domain
      type: domain
      version: 1.0.0
      protocol_version: "1"
      description: Conformance test domain
      url: http://localhost:9700
      public_key: "${fixture/test-domain/public_key}"
      capabilities:
        - {name: "agent:message", resources: []}
        - {name: "workflow:execute", resources: []}
      required_agents: [test-agent]
      workflows: [test-workflow]
      max_concurrent: 10
  test-gateway:
    seed: "0000000000000000000000000000000000000000000000000000000000000010"
  test-writer:
    seed: "0000000000000000000000000000000000000000000000000000000000000011"
    cap: ["content:read", "content:write", "content:describe", "content:declare", "content:establish", "content:propose"]
  test-proposer:
    seed: "0000000000000000000000000000000000000000000000000000000000000012"
    cap: ["content:read", "content:propose", "content:describe"]
  test-decider:
    seed: "0000000000000000000000000000000000000000000000000000000000000013"
    cap: ["content:read", "content:decide", "content:describe"]
  test-content-client:
    seed: "0000000000000000000000000000000000000000000000000000000000000014"
    manifest:
      name: test-content-client
      type: agent
      version: 1.0.0
      protocol_version: "1"
      description: Conformance client of a content service, holding only what a service may hold
      url: http://localhost:9711
      public_key: "${fixture/test-content-client/public_key}"
      capabilities:
        - {name: "content:describe", resources: []}
        - {name: "content:propose", resources: []}
      max_concurrent: 5
  test-operator:
    seed: "0000000000000000000000000000000000000000000000000000000000000016"
  test-overreach:
    seed: "0000000000000000000000000000000000000000000000000000000000000015"
    manifest:
      name: test-overreach
      type: agent
      version: 1.0.0
      protocol_version: "1"
      description: A component naming person-only capabilities no hub would grant it, for the tokens a hub that issued one by mistake would mint
      url: http://localhost:9712
      public_key: "${fixture/test-overreach/public_key}"
      capabilities:
        - {name: "content:read", resources: []}
        - {name: "content:write", resources: []}
        - {name: "content:decide", resources: []}
        - {name: "content:attest", resources: []}
        - {name: "content:request", resources: []}
        - {name: "content:comment", resources: []}
        - {name: "content:retain", resources: []}
        - {name: "content:hold", resources: []}
      max_concurrent: 5
  unverifiable-statement:
    signed_at: "${now}"
    attestation:
      identity_id: conformance-nobody
      identity_public_key: "${fixture/test-overreach/public_key}"
      credential_public_key: "${fixture/test-overreach/public_key}"
      hub_id: conformance-hub
      purpose: sign-records
      not_after: "2099-01-01T00:00:00.000Z"
      signature: AAAA
    signature: AAAA
  content-git:
    content:
      backends:
        - name: stores
          driver: git
          root: "${instance}/stores"
          options: {default_line: main, worktree: none, object_format: sha1}
      repositories:
        - id: docs
          scope_path: conformance/org
          placement: {backend: stores, locator: docs}
          custody: exclusive
        - id: opaque-docs
          scope_path: conformance/org
          placement: {backend: stores, locator: opaque-docs}
          custody: opaque
      reconcile_interval: 0s
      checkpoint_interval: 0s
  # The declared admin gateway is the test-gateway fixture. Its identity is
  # the fingerprint (protocol/identity, Key Fingerprint) of the public key
  # that fixture's seed derives, written out because no placeholder yields
  # a fingerprint.
  admin-gateway-declared:
    hub:
      name: conformance-hub
      version: 1.0.0
    orchestrator:
      admin_addresses: ["https://localhost:19443"]
      admin_gateway_identity: "384157d7e6a5d5839ac228be14e3b3386bba4f6b64cc5fdaae39991366049a74"
    admin_gateway:
      allowlist: ["127.0.0.1", "::1"]
  test-agent-sealed:
    key:
      identity: test-agent
      kdf: argon2id
      salt: "000102030405060708090a0b0c0d0e0f"
      passphrase: conformance-passphrase-1
  test-agent-next:
    key:
      identity: test-domain
      kdf: none
  conformance-passphrase:
    text: conformance-passphrase-1
  conformance-passphrase-wrong:
    text: conformance-passphrase-2
  sealed-key-agent-config:
    agents:
      - name: "${self/name}"
        key_passphrase: "file:${instance}/.weblisk/passphrase"
  orchestrator-gateway:
    orchestrator:
      admin_addresses: ["https://admin.conformance.invalid"]
      admin_gateway_identity: "${fixture/test-gateway/fingerprint}"
      admin_gateway_from: ["${harness/source}"]
  model-config:
    provider: conformance-backend
    model: conformance-model
    base_url: "${stood/model/address}"
  model-agreement:
    party: Conformance Model Party
    backends: [conformance-backend]
    models: [conformance-model]
    agreement: Conformance agreement 1
    agreement_digest: "sha256:0000000000000000000000000000000000000000000000000000000000000000"
    level: confidential
    not_after: "${now+30d}"
  document-family:
    text: |
      ---
      family: schemas/family@1
      version: 1.0.0
      kind: conformance-note
      noun: conformance note
      capabilities: [author, versioned]
      generates: none
      ---
      # Conformance note

      A document family a tenant declares for itself, for conformance checks.

      ## Header

      ```yaml
      header:
        schema:
          type: object
          properties:
            family: {const: documents/families/conformance-note@1}
            title: {type: string}
            uid: {type: string}
          required: [family, title]
      ```
  content-git-remote:
    content:
      backends:
        - name: stores
          driver: git
          root: "${instance}/stores"
          options: {default_line: main, worktree: none, object_format: sha1}
        - name: destination
          driver: git-remote
          root: "${stood/remote/root}"
          held_by: tenant
          options:
            host_keys: ["${stood/remote/host_key}"]
            read_addresses: []
      repositories:
        - id: docs
          scope_path: conformance/org
          placement: {backend: stores, locator: docs}
          custody: exclusive
      reconcile_interval: 0s
      checkpoint_interval: 0s
  # Content custody checks (architecture/content, Declared checks): a shared
  # repository whose configuration claims attestations a git store cannot
  # demonstrate, the person who may reconcile it, and an exclusive store
  # re-verified often enough that a copy reported out of band is seen within
  # a check, with the git configuration that reports one and the one that
  # does not.
  content-git-claims:
    content:
      backends:
        - name: shared-stores
          driver: git
          root: "${instance}/shared"
          options: {default_line: main, worktree: attached, object_format: sha1}
      repositories:
        - id: claims
          scope_path: conformance/org
          placement: {backend: shared-stores, locator: claims}
          custody: shared
          attestations: {enumerable_principals: true, attributable_writes: true, tamper_evident: true}
      reconcile_interval: 0s
      checkpoint_interval: 0s
  test-reconciler:
    seed: "0000000000000000000000000000000000000000000000000000000000000021"
    cap: ["content:read", "content:describe", "content:reconcile"]
  content-git-copy:
    content:
      backends:
        - name: stores
          driver: git
          root: "${instance}/stores"
          options: {default_line: main, worktree: none, object_format: sha1}
      repositories:
        - id: held
          scope_path: conformance/org
          placement: {backend: stores, locator: held}
          custody: exclusive
      reconcile_interval: 0s
      reverify_custody_interval: 1s
      checkpoint_interval: 0s
  git-config-copy:
    text: |
      [core]
          repositoryformatversion = 0
          filemode = true
          bare = true
      [remote "copy"]
          url = https://copy.conformance.invalid/held.git
          fetch = +refs/heads/*:refs/remotes/copy/*
  git-config-plain:
    text: |
      [core]
          repositoryformatversion = 0
          filemode = true
          bare = true
  task:
    id: conformance-task-1
    from: user
    action: execute
    payload: {}
    context:
      workspace_root: "."
      services: []
      trace_id: 4bf92f3577b34da6a3ce929d0e0e4736
      span_id: 00f067aa0ba902b7
      task_id: conformance-task-1
      agent_name: "${self/name}"
    token: "${token}"
    timestamp: "${now}"
  message:
    id: conformance-message-1
    from: test-agent
    to: "${self/name}"
    type: request
    action: conformance_probe
    payload: {}
    timestamp: "${now}"
    trace_id: 4bf92f3577b34da6a3ce929d0e0e4736
    span_id: 00f067aa0ba902b7
```

---


### Test tokens as data

The bearer tokens an `exchange` step's `token` names
([`schemas/blocks`](../schemas/blocks.md#definitions), `exchange-request`),
each as the harness mints it. Every one is a WLT
([`protocol/identity`](../protocol/identity.md#token-system)) with the header
`{"alg": "ML-DSA-65", "typ": "WLT"}`, signed by the `signed_by` fixture's key
over the token's first two parts, as Token Creation says. In a token's
`claims`, `<as>` is the step's `as` identity fixture, `<self>` the name the
component under test registers under, `<self id>` the identity id it registers
with (the fingerprint of the public key its manifest names), and `<cap>` the
capability names of the `as` fixture's manifest, in the manifest's order, or
its `cap` where it is a person's and has no manifest (an empty list where the
fixture has neither). `<fingerprint of F>` is the fingerprint of fixture F's
public key. `iat` and `exp` are seconds from the instant the
token is minted, written into the claims as NumericDates. A token `from`
another is that token with the fields it names replaced. A step whose `token`
is not `none` or `captured` and whose `as` is `anonymous` is a fault of the
check, reported as such, never sent with no token.

A step's `token_alter` changes the token its `token` names exactly as an
entry `from` another does, its claims and times before it is signed and its
signature after: `claims` replaces the
claims it names and removes those it gives `null`, `iat` and `exp` replace the
token's, and `signature` puts the signature in one of the `signature_forms`
below. So an expired pass, a work pass addressed to another component, an
operator token with no `cid` or carrying `step_up_at`, and a token whose
signature is a byte short are each a declared token altered, and none is a
new entry. `<fingerprint of F>` in a claim is `${fixture/F/fingerprint}`.

```yaml
test_tokens:
  signed_by: test-orchestrator
  signature_forms:
    last-byte-flipped: The decoded signature's last byte changed (exclusive-or 0x01), encoded again; the length is right and it does not verify
    truncated: The decoded signature without its last byte, encoded again; one byte shorter than ML-DSA-65's 3309
    extended: The decoded signature with one 0x00 byte appended, encoded again; one byte longer than 3309
    empty: No signature; the token's third part is empty
  tokens:
    own:
      means: The registration token the orchestrator issues the as identity
      claims: {sub: "<as>", iss: orchestrator, cap: "<cap>", identity_id: "<fingerprint of the as fixture's public key>"}
      iat: 0
      exp: 86400
    expired:
      means: own, past its exp
      from: own
      iat: -90000
      exp: -3600
    bad-signature:
      means: own, with the last byte of its decoded signature changed (exclusive-or 0x01) and the signature encoded again
      from: own
      signature: last-byte-flipped
    wrong-type:
      means: own, carrying a type no component route takes but an attestation submission
      from: own
      claims: {type: attestation}
    channel-self:
      means: A channel token for a channel from the as identity to the component under test
      claims: {sub: "<as>↔<self>", iss: orchestrator, cid: "00000000000000000000000000000001"}
      iat: 0
      exp: 3600
    channel-other:
      means: A channel token for a channel from the as identity to a component that is not the one under test
      claims: {sub: "<as>↔conformance-other", iss: orchestrator, cid: "00000000000000000000000000000002"}
      iat: 0
      exp: 3600
    pass:
      means: A person's pass for the as identity, addressed to the component under test, as protocol/identity's The pass shapes one, obtained by the test-gateway fixture
      claims: {type: pass, sub: "<as>", iss: orchestrator, aud: "<self id>", identity_id: "<fingerprint of the as fixture's public key>", cid: "00000000000000000000000000000003", act: {sub: test-gateway, identity_id: "<fingerprint of test-gateway>"}, cap: "<cap>", identity_key: "<fingerprint of the as fixture's public key>", record_keys: []}
      iat: 0
      exp: 30
    pass-other:
      means: pass, addressed to another component (the test-agent fixture) instead of the one under test
      from: pass
      claims: {aud: "<fingerprint of test-agent>"}
    operator:
      means: The as identity's operator token, as architecture/admin's Operator token shapes one; no component but the orchestrator and the admin gateway may be presented one
      claims: {type: operator, sub: "<as>", iss: orchestrator, identity_id: "<fingerprint of the as fixture's public key>", cid: "00000000000000000000000000000004", cap: "<cap>", record_keys: []}
      iat: 0
      exp: 900
    work:
      means: A work pass addressed to the component under test, on the as identity's authority, carried by the test-agent fixture, as protocol/identity's The work pass shapes one
      claims: {type: work, sub: "<as>", iss: orchestrator, aud: "<self id>", identity_id: "<fingerprint of the as fixture's public key>", cid: "00000000000000000000000000000005", act: {sub: test-agent, identity_id: "<fingerprint of test-agent>"}, definition: conformance-definition, run: conformance-run-1, cap: "<cap>"}
      iat: 0
      exp: 30
```

Every value of `token` that [`schemas/blocks`](../schemas/blocks.md#definitions)
declares, other than `none` and `captured`, MUST have exactly one entry here,
and a token MUST carry exactly the claims its entry gives and no other.
`checks/check-kinds.py` holds the first, and that every signature form a
token or a `token_alter` names is one `signature_forms` declares. <!-- wl:id test-tokens-declared -->

### Starting a component with a fixture key

A check's `start.keys` ([`schemas/blocks`](../schemas/blocks.md#definitions),
`check-start`) names an identity fixture. Before the harness starts the
component, it writes that fixture's key to the component's key file in the
scratch copy of the tree, `.weblisk/keys/<name>.key`, where `<name>` is the
name the component registers under ([`protocol/identity`](../protocol/identity.md#key-files)):
the key derived from the fixture's `seed`, in the `weblisk-key-v1` envelope
with `kdf = none` ([`protocol/identity`](../protocol/identity.md#private-key-format)),
mode 0600 under a `.weblisk/keys/` of mode 0700. The orchestrator's are
`orchestrator.key` and `hub.key`, both the fixture's key, with `hub.pub` its
public half, since a first start's token-signing key is its hub key. A key
with `kdf = none` is a development key ([`protocol/identity`](../protocol/identity.md#service-key-protection),
rule 6), so the component is started with `WL_DEV=1`, as every sealed start
is. <!-- wl:id fixture-key-written -->

A component that, given that file, does not load it, generates another, or
registers with any other key has failed the check that named `start.keys`; it
is never reported as having passed with the key it chose.

### Starting a component with a fixture configuration

A check's `start.config` ([`schemas/blocks`](../schemas/blocks.md#definitions),
`check-start`) names a fixture of the fixtures block whose value is a
configuration: what a tenant's `.weblisk/config.yaml` holds for the component
([`schemas/config`](../schemas/config.md)). Before the harness starts the
component, it writes that value, as YAML, to `.weblisk/config.yaml` in the
working directory it starts the component in, with every `${instance}` in it
replaced by that directory's absolute path, and creates nothing else. A
configuration fixture holds no secret and names no address outside that
directory but as the paragraph below allows, so a store it declares lives and dies with the run. <!-- wl:id fixture-config-written -->

A component that, given that file, does not read it, or reads another, has
failed the check that named `start.config`, as one that ignores `start.keys`
has.

### Bringing up accepted dependencies

A component's suite runs against the accepted builds of what it needs running
first ([`architecture/engine`](engine.md#the-test-environment),
`tested-against-accepted`). Before the component under test starts, the
harness brings each of them up the way a person brings up a hub: it starts
the orchestrator, claims it with a first operator, and starts every other
dependency pointed at it. Every value of that is declared here, and the
engine performs it as mechanics.

```yaml
bring_up:
  keys: test-orchestrator
  operator: test-operator
  steps:
    - id: bootstrap-secret
      read: {file: .weblisk/bootstrap, capture: bootstrap_secret, within: 10s}
    - id: register-first-operator
      as: test-operator
      request:
        method: POST
        path: /v1/admin/operators/register
        body:
          name: test-operator
          public_key: "${fixture/test-operator/public_key}"
          role: admin
          timestamp: "${now}"
          bootstrap_secret: "${bootstrap_secret}"
        sign: {over: "", members: [name, public_key, role, timestamp], into: /signature, timestamp: /timestamp}
      expect: {status: 200, equals: {/status: approved}, has: [/token, /hub_id, /identity_id]}
      capture: {attestation_token: /token, hub_id: /hub_id, operator_identity: /identity_id}
    - id: observer-registers
      as: test-agent
      request:
        method: POST
        path: /v1/register
        body: {manifest: {name: test-agent, type: agent, version: 1.0.0, protocol_version: "1", description: Conformance observer, url: "http://localhost:9710", public_key: "${fixture/test-agent/public_key}", capabilities: [{name: "agent:message", resources: []}]}}
        sign: {over: /manifest, into: /signature, timestamp: /timestamp}
      expect: {status: 200, has: [/token]}
      capture: {observer_token: /token}
  directory:
    request: {method: GET, path: /v1/services, headers: {Authorization: "Bearer ${observer_token}"}}
    entries: /services
    name: /name
    lease_state: /lease_state
    lease_expires_at: /lease_expires_at
    current: [ready, not_ready]
```

| Key | Means |
|---|---|
| `keys` | The identity fixture whose key the orchestrator is started with, written as [Starting a component with a fixture key](#starting-a-component-with-a-fixture-key) writes one, `hub.key` and `hub.pub` included. It is `test_tokens`' `signed_by`, so every token the harness mints for a dependant's checks verifies at the accepted orchestrator as at the mock |
| `operator` | The identity fixture the first operator is |
| `steps` | Run in order against the orchestrator once it listens. A step is an `exchange` step ([`schemas/blocks`](../schemas/blocks.md#definitions), `exchange-step`), or a `read` |
| `read` | Reads `file`, relative to the working directory the orchestrator was started in, once it exists and is not empty, waiting at most `within`; its contents, trimmed, are captured as `capture`. It is how the harness, as whoever started the orchestrator, reads what the orchestrator emitted only to them ([`architecture/admin`](admin.md#bootstrap-flow)) |
| `directory` | How the harness reads the accepted orchestrator's directory, as the registration `observer-registers` made for itself: the request, where its entries are, and in each entry the pointers to the registered name, the lease state and the lease's expiry; `current` are the lease states L4-01 reads as current. A `join` check's `registered`, `listed`, `lease-current`, `lease-renewed` and `readyz-agrees` are read through it ([`schemas/blocks`](../schemas/blocks.md#definitions), `check-join`) |

The steps' captures are held for the run: a dependant's check may name any of
them as `${name}`, and `attestation_token` is the first operator's
attestation token.

The harness MUST start a component's dependencies from their accepted builds,
in the services table's order, each in a working directory of its own with
`WL_DEV=1`: the orchestrator with `bring_up.keys`' key and no orchestrator address,
and every other dependency with the orchestrator's address and no fixture key,
so it registers as it would in a tenant. Each MUST be listening and answer its
`live` probe ([`protocol/spec`](../protocol/spec.md#get-livez-and-get-readyz))
before the next is started; whether each that registers is listed with a live
lease is L4-01's to judge, on the dependant's own run. <!-- wl:id dependencies-started-in-order -->

Once the orchestrator listens, the harness MUST run `bring_up.steps` against
it, in order, before any other dependency or the component under test starts.
A step that fails or cannot be read MUST end the bring-up, and the dependant's
run is unsettled, naming the step and why; the harness never continues with a
hub that has no first operator. <!-- wl:id first-operator-bootstrapped -->

The bootstrap secret MUST be read only from the file the orchestrator wrote
in its own working directory, and MUST NOT appear in any event, record,
evidence or log of the run. <!-- wl:id bootstrap-secret-kept-in-run -->

The first operator obtains operator tokens the way every operator does: it
attests a credential and mints with it ([`architecture/admin`](admin.md#obtaining-a-token)).
Those two acts are signed over fixed-form statements, which a step expresses
only once [`schemas/blocks`](../schemas/blocks.md#definitions) declares how a
step signs one. Until it does, they are not steps here, and a check that needs
an operator token the hub minted, rather than the `operator` test token, is
unread, naming the missing form; it is never run with a token the harness
made up.

The orchestrator a dependant's checks name as `orchestrator: built` is this
one: the accepted build, brought up as above. A component that *is* the
orchestrator, under test, is started as
[`schemas/blocks`](../schemas/blocks.md#checks) says for the orchestrator
under test, with `bring_up.keys`' key and no bring-up beneath it.
A configuration fixture may name an address only through a placeholder the
harness fills (`${harness/source}`, `${stood/<name>/<field>}`, `${address}`)
or under the reserved top-level name `invalid` (RFC 6761), which no resolver
answers, as `orchestrator-gateway`'s `admin_addresses` does. Its secrets are
pointers, as every configuration's are: `sealed-key-agent-config` names a
`file:` source under `${instance}`, which a check fills with `start.files`.
A check of another kind sets that kind's own `key_passphrase` the same way.

### Key fixtures

A fixture whose value is `key` is a key file, not an identity: `identity` names
the identity fixture whose seed it holds, and `kdf` how it is written in the
`weblisk-key-v1` envelope ([`protocol/identity`](../protocol/identity.md#private-key-format)).
`kdf: none` is the development key `start.keys` writes for an identity
fixture. `kdf: argon2id` is that key encrypted under `passphrase`, with the
`salt` given and the parameters Encryption Scheme fixes, so its bytes are the
same at every run; the passphrase reaches the component only by the source its
configuration names, never by the environment. A key fixture's public key and
fingerprint are its identity's. <!-- wl:id fixture-key-forms -->

So a sealed start is `start: {keys: test-agent-sealed, config:
sealed-key-agent-config, files: {.weblisk/passphrase: conformance-passphrase}}`,
and a start whose passphrase fails names `conformance-passphrase-wrong` there
instead and expects `refuses-start`. A topology act `read` of
`.weblisk/keys/<name>.key` reads the key file a process wrote, its mode and,
through `decodes-as: weblisk-key-v1`, its `kdf`.

### Placing files

A check's `start.files` (and a `drive` check's `files`) maps a path relative
to the working directory to a fixture. Before the component starts, the
harness writes each: a fixture whose value is `text` as that text, exactly;
any other value as JSON where the path ends `.json` and as YAML otherwise;
each with every placeholder filled, mode 0600, under directories of mode
0700. A topology act `place` writes one the same way while the component runs,
which is how a file arrives out of band. So `model-config` is placed at
`.weblisk/model.json`, a tenant's document family at
`documents/families/conformance-note.md`, and a passphrase at the path its
configuration names. A fixture that is a request body, such as
`model-agreement`, is sent, never placed: what a component records through
its own route is never written behind it. <!-- wl:id fixture-files-placed -->

### Harness roles

What the harness runs beside the component under test is a closed set, each
specified here and built from this specification, as the mocks are. Every
one records every request that reaches it, in order, as `{method, path,
headers, body}` (body parsed where it is JSON), and a step's
`expect.received` reads those records: `service: orchestrator` the
mock orchestrator's, `service: mock-agent` the mock agent's, and a stood service's by
its name. <!-- wl:id harness-records-received -->

| Role | Stood up by | Reached at | Does |
|---|---|---|---|
| mock orchestrator | `start.orchestrator: mock` | `${address/orchestrator}` | [Mock Orchestrator](#mock-orchestrator) |
| mock agent | `start.mock_agent` | `${address/mock-agent}` | [Mock Agent](#mock-agent) |
| `responder` | `start.stand_up`, `role: responder` | `${stood/<name>/address}`, an `http://127.0.0.1:<port>` origin, or `https://` with `${stood/<name>/certificate}` its certificate's PEM where `tls` is set | answers each request with the first of `answers` that matches it, and every other with 404 and an `ErrorResponse`. A model backend, a webhook target, a probe of an address's provenance, or a gateway a front end is driven against |
| `git-remote` | `start.stand_up`, `role: git-remote` | `${stood/<name>/root}`, an `ssh://127.0.0.1:<port>/<directory>/` root; `${stood/<name>/host_key}`, its host key's `known_hosts` line, made for the run | a git server over SSH that offers exactly the key exchange methods `kex` names, admits the keys `authorises` names, and holds `lines`. Its pushes are what `received` reads, each `{line, from, to, files}`; a topology act `remote` changes a line as another party would |
| probe agent | `start.probe` | the component under test's boundaries | [The probe agent](#the-probe-agent) |

`${harness/source}` is the IP address the harness's requests reach the
component from, and `${address}` the origin it reaches the component at, so a
check can say what a component must make of where a request came from, and
the `@address` capture names the origin a step dialled.

### The probe agent

The enforcement boundaries ([`architecture/enforcement`](enforcement.md#boundary-integration))
wrap an agent's own clients, so they are reached only by an agent behind them.
`start.probe` starts the mock agent as the identity fixture `as` names, with
that fixture's manifest, built in the component's language with the
component's enforcement package wrapping its message, storage, external and
response clients as Boundary Integration says. A step sent `from: probe`
carries `request.probe`: a boundary and the input its interface in
`architecture/enforcement` takes. The probe attempts that operation through
that boundary, and the step's response is the interface's output as JSON,
`{decision, correlation_id, violation}`, with the status the boundary's
refusal gives where it refuses. What reached the far side is read with
`received`. A component whose language declares no enforcement package to
link leaves every probe check **unread**. <!-- wl:id probe-agent-behind-enforcement -->

## Mock Orchestrator

A minimal orchestrator implementation for testing agents in isolation.
Implements only the endpoints agents call during their lifecycle.

### Endpoints

| Endpoint | Behavior |
|----------|----------|
| `POST /v1/register` | Accept any valid registration, return token + empty service directory |
| `GET /livez` | Return `{"live": true}` |
| `GET /readyz` | Return `{"ready": true}` |
| `POST /v1/lease` | Accept a renewal from a registered test agent and return its `Lease`; 404 `NOT_FOUND` for any other caller |
| `POST /v1/channel` | Return a channel grant with a test channel token |
| `GET /v1/services` | Return the current registered agents |

### Behavior

- Accepts all valid signatures (verifies format but uses the provided public key)
- Issues tokens with 24h TTL using test orchestrator keys
- Stores registrations in memory
- Records every request it receives, for `expect.received` ([Harness roles](#harness-roles))
- Does NOT forward tasks (mock only)

### What the mock cannot establish

The mock is deliberately permissive, which makes it useful for developing an
agent and useless for concluding that the agent can register. Reusing the
provided public key means a signature verifies whatever bytes were signed;
accepting any valid registration means the manifest is never judged against the
registry's vocabulary.

Every one of these passes against the mock and is refused by a real
orchestrator:

| Fault | Why the mock misses it |
|---|---|
| Signature over different bytes than the verifier canonicalizes | The mock verifies with the key the caller supplied, over the caller's own payload |
| A manifest field the registry's type does not define | The mock does not re-canonicalize a parse, so no asymmetry arises |
| A capability name outside `protocol/types` | The mock enforces no vocabulary |
| A subscription scope that is not `self`, `*` or an agent name | Not validated |
| `protocol_version` that is not the wire version | Not negotiated |
| Registering at a path the orchestrator does not serve | The mock is mounted wherever the test mounts it |

**A component MUST NOT be signed off as conformant on the strength of the mock
alone.** Level 4 is where registration is actually established, and until it
passes, "registers successfully" is an untested claim. The mock's value is that
it fails fast during development; it is not evidence.

### Usage

The tools carry no mock: it is built from this specification, like any other
component ([`ENGINE_PLAN.md`](../ENGINE_PLAN.md#2-the-engines-operations)), and
started by the test code that needs it.

```go
mockOrch := weblisk.NewMockOrchestrator(19800, testOrchestratorKey)
mockOrch.Start()
defer mockOrch.Stop()
```

---

## Mock Agent

A minimal agent for testing domain controllers and the orchestrator.
Responds to execute and message with configurable responses.

### Endpoints

| Endpoint | Behavior |
|----------|----------|
| `POST /v1/describe` | Return the test agent manifest |
| `POST /v1/execute` | Return a configurable `TaskResult` |
| `POST /v1/message` | Return a configurable response payload |
| `GET /livez` | Return `{"live": true}` |
| `GET /readyz` | Return a configurable `{"ready": ...}` |
| `POST /v1/services` | Accept and store |

### Configurable Responses

The mock agent supports pre-programmed responses:

```
mockAgent.OnExecute(func(task TaskRequest) TaskResult {
  return TaskResult{
    Status: "success",
    Summary: "processed",
    Observations: [...],
    Recommendations: [...],
  }
})

mockAgent.OnMessage("scan_html", func(payload map) map {
  return {"files": [...], "measurements": {...}}
})
```

---

## Conformance Test Suite

### Level 1: Protocol Compliance

These tests verify basic endpoint behavior. Every implementation MUST pass every
Level 1 test **that applies to it**.

Each test names the components it applies to. A test addressed to an agent is
not a failure of an orchestrator: they serve different endpoints, and running
every test against every component reports a correct implementation as broken —
the same fault the Verification Checklists had before their groups were read.

#### L1-01: Probes

Applies to: **orchestrator**, **agent** — every component serves the same two,
as `protocol/spec` says.

```
GET /livez   → 200, body {"live": true}
GET /readyz  → 200 {"ready": true}, or 503 {"ready": false}
No auth required.
Each body MUST carry `live` or `ready` and no other member
```

A probe that also answers a name, a version, an uptime or checks fails:
health is liveness and readiness only, and `protocol/types` (Health) is the
authority a test asserts, never the reverse.

#### L1-02: Describe

Applies to: **agent** only — the orchestrator does not serve `/v1/describe`.
```
POST /v1/describe → 200
Response MUST be a valid AgentManifest
Response MUST contain: name, version, url, public_key, capabilities
```

#### L1-03: Registration

Applies to: **orchestrator** only — it is the registry.
```
1. Build RegisterRequest with valid manifest + signature
2. POST /v1/register → 200
3. Response MUST contain: agent_id, token, expires_at, services
4. Token MUST be valid WLT format
5. agent_id MUST be 32 hex chars
```

#### L1-04: Registration Rejects Bad Signature

Applies to: **orchestrator** only.
```
1. Build RegisterRequest with wrong signature
2. POST /v1/register → 401
3. Response MUST contain error field
```

#### L1-05: Registration Rejects Stale Timestamp

Applies to: **orchestrator** only.
```
1. Build RegisterRequest with timestamp = now - 600 seconds
2. POST /v1/register → 401
3. Response.error MUST mention replay or timestamp
```

#### L1-06: Execute Task

Applies to: **agent** only.
```
1. Register agent (get token)
2. Build TaskRequest with valid token
3. POST /v1/execute → 200
4. Response MUST be valid TaskResult
5. Response.task_id MUST match request.id
6. Response.agent_name MUST match manifest.name
```

#### L1-07: Protected Endpoints Require Auth

Applies to: **orchestrator**, **agent** — against each component's own protected endpoints.
```
For each protected endpoint (/v1/services, /v1/execute, /v1/audit, etc.):
  1. Send request without token → 401
  2. Send request with expired token → 401
  3. Send request with valid token → not 401
```

#### L1-08: Message Handling

Applies to: **agent** only.
```
1. Register agent
2. Build AgentMessage: {from: "test", to: agent.name, type: "request", action: "scan_html", payload: {...}}
3. Sign message
4. POST /v1/message → 200
5. Response MUST be AgentMessage with type: "response"
6. Response.from MUST be agent.name
```

#### L1-09: Service Directory Update

Applies to: **agent** only — the orchestrator PUBLISHES the directory.
```
1. Register agent
2. POST /v1/services with ServiceDirectory → 200
3. Agent's internal service list MUST be updated
```

#### L1-10: Error Response Format

Applies to: **orchestrator**, **agent** — every component.
```
For any 4xx/5xx response:
  Body MUST be JSON
  Body MUST contain "error" field (string)
  Body SHOULD contain "code" field when applicable
```

### Level 2: Security Compliance

#### L2-01: Signature Verification on Messages
```
1. Send AgentMessage with invalid signature to agent
2. Agent MUST return 401
```

#### L2-02: Token Expiry Enforcement
```
1. Create token with exp = now - 1
2. Send request with expired token
3. Must receive 401
```

#### L2-03: Channel Token Scoping
```
1. Request channel between agent-A and agent-B
2. Use channel token to message agent-B → success
3. Use channel token to message agent-C → fail (wrong scope)
```

#### L2-04: Request Body Size Limits
```
1. Send registration body > 1 MB → must reject (413 or 400)
2. Send task body > 10 MB → must reject
3. Send message body > 1 MB → must reject
```

#### L2-05: Replay Protection
```
1. Record a valid registration request
2. Replay same request after 300+ seconds → 401
```

### Level 3: Lifecycle Compliance

Tests the full feedback loop. Requires orchestrator + domain + agent.

#### L3-01: Full Audit Workflow
```
1. Start orchestrator
2. Register domain (type: "domain", required_agents: ["test-agent"])
3. Domain's lease_state → "not_ready" (test-agent not registered yet)
4. Register test-agent
5. Domain's lease_state → "ready"
6. Submit task to domain targeting action "test-workflow"
7. Domain publishes workflow.trigger event:
   a. Workflow Agent resolves DAG
   b. Task Agent dispatches phase to test-agent via /v1/execute
   c. Workflow Agent aggregates results
   d. Publishes workflow.completed (scope: domain)
8. Lifecycle Agent captures observations from workflow.completed event
9. Lifecycle Agent stores recommendations
10. Approve recommendation (POST /v1/message to Lifecycle Agent, action: approve_recommendation)
11. Recommendation status transitions pending → accepted
12. Verify audit log contains: register (x4), event, approval entries
```

#### L3-02: Strategy Lifecycle
```
1. Create strategy (POST /v1/message to Lifecycle Agent, action: create_strategy)
2. Verify strategy stored (POST /v1/message to Lifecycle Agent, action: get_strategy)
3. Lifecycle Agent publishes workflow.trigger linked to strategy
4. Verify observations reference the strategy_id
5. After feedback, verify strategy target.progress is updated
```

#### L3-03: Workflow Error Handling
```
1. Configure mock agent to fail on "analyze" action
2. Submit task that triggers a workflow with on_error: "skip"
3. Verify: failed phase is skipped, dependent phases proceed
4. Verify: WorkflowExecution records the skipped phase

5. Configure mock agent to fail on "scan" action
6. Submit task with on_error: "fail"
7. Verify: entire workflow fails
8. Verify: TaskResult status = "failed"
```

#### L3-04: Concurrency Enforcement
```
1. Set mock agent max_concurrent = 2
2. Send 5 concurrent execute requests
3. Verify: first 2 accepted, remaining get 429
4. Verify: 429 response is valid ErrorResponse with code RATE_LIMITED
```

#### L3-05: Approval Gate
```
1. Submit task that produces a recommendation with approval: "required"
2. Verify workflow execution pauses (status: "pending_approval")
3. Approve via POST /v1/message to Lifecycle Agent (action: approve_recommendation)
4. Lifecycle Agent publishes workflow.approval.decision
5. Verify workflow resumes and completes
```

---

### Level 4: Interoperability

Levels 1 to 3 run one component against fixtures. Level 4 runs a component
against **the real orchestrator it will register with**, because a component can
satisfy every assertion about itself and still be unable to join a mesh.

This level exists because it was missing. The first time two independently
generated components of one tenant were asked to interoperate, the second could
not register — eight consecutive refusals, each a contract stated in a way that
cannot be implemented twice, and none of them visible to a suite that starts one
binary alone.

#### L4-01: Registers With A Real Orchestrator

Applies to: every component that registers — **not** the orchestrator itself.
```
1. Start a real orchestrator on an ephemeral port
2. Start the component with that orchestrator's URL
3. The component MUST reach a listening state and MUST NOT exit. An exit
   here fails this test; it is never reported as inconclusive
4. The orchestrator's directory (GET /v1/services, read under a registration
   the harness makes for itself) MUST list the component, and within one
   lease duration its lease_state MUST be current: `ready`, or `not_ready`
   where the component's own blueprint says it may serve not ready (content
   with a repository left establishing or declined), and never `unknown`
5. The component's GET /readyz MUST answer as its last renewal did
6. The component MUST hold an agent_id and a token, and MUST renew its lease
   at POST /v1/lease within a third of its duration
```

The order of 3 and 4 matters. A component that requires the orchestrator's
public key in order to construct its authenticator exits before it registers,
and can therefore never obtain the key it refused to start without. A component
MUST be able to listen before it has registered.

#### L4-02: Manifest Is Accepted On Its Own Terms

```
1. Register against a real orchestrator
2. Every capability name MUST be one protocol/types declares
3. Every subscription scope MUST be `self`, `*`, or an agent name
4. protocol_version MUST be the wire version, not the component's semver
5. The manifest MUST carry no field outside AgentManifest
6. Registration MUST NOT be refused with INVALID_REQUEST
```

#### L4-03: Signature Survives A Foreign Verifier

```
1. Sign a manifest that carries every field AgentManifest requires, and one
   field the verifier's type does not define
2. Register against a real orchestrator
3. Registration MUST succeed
```

A failure here is a canonicalization fault on one side or the other, not an
invalid key — see `protocol/spec` Signing input. It is asserted with an extra
field deliberately, because that is the case a verifier re-serializing its own
parse gets wrong, and the case a shared struct definition hides.

#### L4-04: Standalone Operation

Applies to: every component that registers.
```
1. Start the component with NO orchestrator URL
2. It MUST serve GET /livez and GET /readyz unauthenticated and MUST NOT exit
3. Every protected endpoint MUST refuse with 401 and a structured ErrorResponse
4. GET /livez MUST answer live, and GET /readyz MUST answer not ready, since
   the component can serve nothing a token protects
```

A component that cannot verify a token MUST NOT accept one, and a component that
cannot be started alone cannot be conformance-tested at all.

### The suite as data

The tests above are explanation. What runs is this block: each test written
as a check of a kind [`schemas/blocks`](../schemas/blocks.md#checks) declares,
addressed by `applies_to` to the components it applies to, and run by the
engine's interpreter for its kind, in any language. It replaces both
hand-written suites the CLI carried (`internal/dispatch`'s conformance and
interop runs, and `weblisk test conformance`), whose ids contradicted each
other and this document.

Where the vocabulary cannot yet say what a test needs, the check is
`translated`, and its assertion says what is missing: L1-09, whose effect on
the agent's internal list is seen only in what it does next, and L3-01 to L3-05, which need the
published workflow, task and lifecycle agents started beside a domain and an
observation of the events they publish. Each is unsettled until the
vocabulary grows or a translated test is promoted, never passed.

An exit during startup fails L4-01: `no-exit` is observed, and a component
that exits has failed it, not left it inconclusive.

```yaml
verifies:
  - id: l1-01-probes
    covers: ["protocol/spec:component-serves-get-livez-get-readyz", l1-01-refuses-probe-body-carrying, level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: GET /livez answers 200 with only live true, and GET /readyz answers 200 with ready true or 503 with ready false, each with no other member and no token.
    applies_to: [any]
    live: safe
    exchange:
      steps:
        - request: {method: GET, path: /livez}
          expect: {status: 200, json: true, only: [live], equals: {/live: true}}
        - request: {method: GET, path: /readyz}
          expect: {status: [200, 503], json: true, only: [ready]}

  - id: l1-02-describe
    covers: ["protocol/spec:agent-responds-post-v1-describe-valid", "architecture/agent:post-v1-describe-returns-agent-manifest", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: POST /v1/describe answers 200 with a manifest holding name, version, url, public_key and capabilities.
    applies_to: [agent, domain]
    live: safe
    exchange:
      steps:
        - request: {method: POST, path: /v1/describe, body: {}}
          expect: {status: 200, json: true, has: [/name, /version, /url, /public_key, /capabilities]}

  - id: l1-03-registration
    covers: ["architecture/orchestrator:post-v1-register-returns-registerresponse-agent", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: A registration signed over the manifest as sent is answered 200 with agent_id (32 lowercase hex), a token in three base64url parts, expires_at and services.
    applies_to: [orchestrator]
    exchange:
      steps:
        - as: test-agent
          request:
            method: POST
            path: /v1/register
            body: {manifest: "${fixture/test-agent/manifest}"}
            sign: {over: /manifest, into: /signature, timestamp: /timestamp}
          expect:
            status: 200
            has: [/agent_id, /token, /expires_at, /services]
            matches: {/agent_id: "^[0-9a-f]{32}$", /token: "^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$"}

  - id: l1-04-bad-signature
    covers: ["architecture/orchestrator:post-v1-register-verifies-ml-dsa", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: A registration whose signature is the right key's over other bytes is refused with 401 and an error member.
    applies_to: [orchestrator]
    exchange:
      steps:
        - as: test-agent
          request:
            method: POST
            path: /v1/register
            body: {manifest: "${fixture/test-agent/manifest}"}
            sign: {over: /manifest, into: /signature, timestamp: /timestamp, with: other-bytes}
          expect: {status: 401, json: true, has: [/error]}

  - id: l1-05-stale-timestamp
    covers: ["protocol/spec:orchestrator-post-v1-register-enforces-replay", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: A correctly signed registration whose timestamp is 600 seconds old is refused with 401, and its error names replay or the timestamp.
    applies_to: [orchestrator]
    exchange:
      steps:
        - as: test-agent
          request:
            method: POST
            path: /v1/register
            body: {manifest: "${fixture/test-agent/manifest}"}
            sign: {over: /manifest, into: /signature, timestamp: /timestamp, age: 600s}
          expect: {status: 401, mentions: [replay, timestamp, stale, expired]}

  - id: l1-06-execute-task
    covers: ["protocol/spec:agent-returns-signed-taskresult-post-v1", "architecture/agent:post-v1-execute-parses-taskrequest-calls", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: A TaskRequest carrying a valid token is answered 200 with a TaskResult whose task_id is the request's id, whose agent_name is the agent's name, and whose signature verifies, under Sign JSON over the result without its signature member, by the key the agent describes itself with.
    applies_to: [agent]
    exchange:
      start: {orchestrator: mock}
      steps:
        - as: test-orchestrator
          request: {method: POST, path: /v1/execute, token: own, body: "${fixture/task}"}
          expect:
            status: 200
            json: true
            has: [/signature]
            equals: {/task_id: conformance-task-1, /agent_name: "${self/name}"}
            assert:
              - verifies-under: {signature: /signature, key: "${self/public_key}", form: jcs, without: [signature]}

  - id: l1-07-protected-endpoints
    covers: ["protocol/spec:protected-endpoints-reject-requests", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: Every protected endpoint refuses a request with no token and one with an expired token with 401, and does not answer 401 to a valid token.
    applies_to: [any]
    live: safe
    exchange:
      start: {orchestrator: mock}
      for_each: protected-endpoint
      steps:
        - request: {endpoint: each, token: none}
          expect: {status: 401}
        - as: test-agent
          request: {endpoint: each, token: expired}
          expect: {status: 401}
        - as: test-agent
          request: {endpoint: each, token: own}
          expect: {status_not: [401]}

  - id: l1-08-message-handling
    covers: ["protocol/spec:agent-handles-post-v1-message-signature", "architecture/agent:post-v1-message-builds-signed-response", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: A signed AgentMessage of type request is answered 200 with an AgentMessage of type response from the agent itself.
    applies_to: [agent, domain]
    exchange:
      start: {orchestrator: mock}
      steps:
        - as: test-agent
          request:
            method: POST
            path: /v1/message
            token: own
            body: "${fixture/message}"
            sign: {over: "", members: [from, to, action, payload], into: /signature}
          expect: {status: 200, json: true, equals: {/type: response, /from: "${self/name}"}}

  - id: l1-09-service-directory-update
    covers: ["protocol/spec:agent-accepts-post-v1-services-updates", level-1-tests-pass-protocol-compliance]
    assertion: A directory pushed to POST /v1/services, signed by the orchestrator as protocol/spec gives, is answered 200 and replaces the agent's internal service list. Translated, because the internal list is observable only through what the agent does next; the signed push itself is now expressible, as test-orchestrator signing weblisk/directory/v2 with sign's fixed-form.
    applies_to: [agent, domain]

  - id: l1-10-error-response-format
    covers: ["protocol/spec:error-responses-use-errorresponse-format-error", level-1-tests-pass-protocol-compliance]
    check: exchange
    assertion: Every 4xx answer, an unmatched path and a protected endpoint without a token, is JSON carrying a string error member.
    applies_to: [any]
    live: safe
    exchange:
      for_each: protected-endpoint
      steps:
        - request: {method: GET, path: /v1/conformance-probe/no-such-route}
          expect: {status: 404, json: true, has: [/error], matches: {/error: "."}}
        - request: {endpoint: each, token: none}
          expect: {status: 401, json: true, has: [/error], matches: {/error: "."}}

  - id: l2-01-message-signature
    covers: ["architecture/agent:post-v1-message-verifies-senders-ml", level-2-tests-pass-security-compliance]
    check: exchange
    assertion: An AgentMessage signed by a key other than its sender's is refused with 401.
    applies_to: [agent, domain]
    exchange:
      start: {orchestrator: mock}
      steps:
        - as: test-agent
          request:
            method: POST
            path: /v1/message
            token: own
            body: "${fixture/message}"
            sign: {over: "", members: [from, to, action, payload], into: /signature, with: other-key}
          expect: {status: 401}

  - id: l2-02-token-expiry
    covers: ["protocol/identity:check-token-expiry-verification", level-2-tests-pass-security-compliance]
    check: exchange
    assertion: A token whose exp has passed is refused with 401 at every protected endpoint.
    applies_to: [any]
    live: safe
    exchange:
      start: {orchestrator: mock}
      for_each: protected-endpoint
      steps:
        - as: test-agent
          request: {endpoint: each, token: expired}
          expect: {status: 401}

  - id: l2-03-channel-scoping
    covers: [level-2-tests-pass-security-compliance]
    check: exchange
    assertion: A channel token scoped to this component is not refused at POST /v1/message, and one scoped to another target is refused with 401 or 403.
    applies_to: [agent, domain]
    exchange:
      start: {orchestrator: mock}
      steps:
        - as: test-agent
          request: {method: POST, path: /v1/message, token: channel-self, body: "${fixture/message}", sign: {over: "", members: [from, to, action, payload], into: /signature}}
          expect: {status_not: [401, 403]}
        - as: test-agent
          request: {method: POST, path: /v1/message, token: channel-other, body: "${fixture/message}", sign: {over: "", members: [from, to, action, payload], into: /signature}}
          expect: {status: [401, 403]}

  - id: l2-04-body-limits-orchestrator
    covers: [level-2-tests-pass-security-compliance]
    check: exchange
    assertion: A registration body larger than 1 MB is refused with 413 or 400.
    applies_to: [orchestrator]
    live: safe
    exchange:
      steps:
        - request: {method: POST, path: /v1/register, body_bytes: 1048577}
          expect: {status: [400, 413]}

  - id: l2-04-body-limits-agent
    covers: [level-2-tests-pass-security-compliance]
    check: exchange
    assertion: A task body larger than 10 MB and a message body larger than 1 MB are each refused with 413 or 400.
    applies_to: [agent, domain]
    exchange:
      start: {orchestrator: mock}
      steps:
        - as: test-orchestrator
          request: {method: POST, path: /v1/execute, token: own, body_bytes: 10485761}
          expect: {status: [400, 413]}
        - as: test-agent
          request: {method: POST, path: /v1/message, token: own, body_bytes: 1048577}
          expect: {status: [400, 413]}

  - id: l2-05-replay
    covers: ["protocol/identity:enforce-replay-protection-window-registration", level-2-tests-pass-security-compliance]
    check: exchange
    assertion: A registration accepted once is refused with 401 when its exact bytes are sent again, and a correctly signed one older than the window is refused with 401.
    applies_to: [orchestrator]
    exchange:
      steps:
        - id: first
          as: test-agent
          request:
            method: POST
            path: /v1/register
            body: {manifest: "${fixture/test-agent/manifest}"}
            sign: {over: /manifest, into: /signature, timestamp: /timestamp}
          expect: {status: 200}
        - request: {replay: first}
          expect: {status: 401}
        - as: test-agent
          request:
            method: POST
            path: /v1/register
            body: {manifest: "${fixture/test-agent/manifest}"}
            sign: {over: /manifest, into: /signature, timestamp: /timestamp, age: 301s}
          expect: {status: 401}

  - id: l3-01-full-audit-workflow
    covers: [level-3-tests-pass-lifecycle-compliance]
    assertion: The L3-01 workflow runs end to end and its audit log holds the registrations, the event and the approval. Translated, because it needs the workflow, task and lifecycle agents started beside the domain, and an observation of published events, which join and record do not yet express.
    applies_to: [domain]

  - id: l3-02-strategy-lifecycle
    covers: ["agents/lifecycle:strategies-created-via-create-strategy-message", level-3-tests-pass-lifecycle-compliance]
    assertion: A strategy created through the lifecycle agent is stored, triggers its workflow, and its progress follows feedback. Translated, for the reason l3-01-full-audit-workflow gives.
    applies_to: [domain]

  - id: l3-03-workflow-error-handling
    covers: ["agents/workflow:error-strategies-applied-handleevent-task-failed", level-3-tests-pass-lifecycle-compliance]
    assertion: A failed phase under on_error skip is skipped and recorded and its dependants proceed; under on_error fail the workflow fails and the TaskResult is failed. Translated, for the reason l3-01-full-audit-workflow gives; the mock agent's failing actions are already expressible as start.mock_agent.
    applies_to: [domain]

  - id: l3-04-concurrency
    covers: ["protocol/spec:agent-returns-429-rate-limited", level-3-tests-pass-lifecycle-compliance]
    assertion: With max_concurrent 2, of five concurrent execute requests two are accepted and three answered 429 with a valid ErrorResponse coded RATE_LIMITED. Translated, because the exchange vocabulary expects of each response alike and cannot yet say how many of a repeated request answer which way, nor set the component's own max_concurrent.
    applies_to: [agent]

  - id: l3-05-approval-gate
    covers: ["agents/workflow:approval-gates-pause-execution-until-workflow", level-3-tests-pass-lifecycle-compliance]
    assertion: A workflow whose recommendation requires approval pauses as pending_approval, and resumes and completes once approved. Translated, for the reason l3-01-full-audit-workflow gives.
    applies_to: [domain]

  - id: l4-01-registers-with-real-orchestrator
    covers: [registering-component-passes-l4-01-listens, "protocol/spec:registered-component-renews-lease-post-v1"]
    check: join
    assertion: Started beside a real orchestrator, the component listens and does not exit, registers, is listed with a current lease within one lease duration, renews within a third of it, and its /readyz agrees with its last renewal. An exit during startup is a failure, never an inconclusive result.
    applies_to: [registers]
    join:
      start: {orchestrator: built}
      observe: [listens, no-exit, registered, listed, lease-current, lease-renewed, readyz-agrees]
      within: lease

  - id: l4-02-manifest-accepted
    covers: ["protocol/spec:protocol-version-compared-equality-wire-version", "protocol/spec:subscription-scope-delivery-scope-never", level-1-tests-pass-protocol-compliance]
    check: join
    assertion: A real orchestrator accepts the component's own registration, so its capabilities, subscription scopes and protocol_version are what the orchestrator admits, and it is never refused INVALID_REQUEST. Whether the manifest carries a field outside AgentManifest is no part of what it covers, since an orchestrator preserves such a field.
    applies_to: [registers]
    join:
      start: {orchestrator: built}
      observe: [registered, listed]
      within: lease

  - id: l4-03-foreign-verifier
    covers: [manifest-carrying-extra-field-still-registers, "protocol/spec:manifest-carrying-field-verifiers-own-type"]
    check: exchange
    assertion: A manifest carrying one field AgentManifest does not define, signed over as sent, registers.
    applies_to: [orchestrator]
    exchange:
      steps:
        - as: test-agent
          request:
            method: POST
            path: /v1/register
            body:
              manifest:
                name: test-agent
                type: agent
                version: 1.0.0
                protocol_version: "1"
                description: Conformance test agent carrying one field AgentManifest does not define
                url: http://localhost:9710
                public_key: "${fixture/test-agent/public_key}"
                capabilities: [{name: "agent:message", resources: []}]
                x_unknown_to_the_verifier: true
            sign: {over: /manifest, into: /signature, timestamp: /timestamp}
          expect: {status: 200, has: [/agent_id]}

  - id: l4-04-standalone
    covers: [registering-component-passes-l4-04-starts, "protocol/spec:protected-endpoints-reject-requests"]
    check: exchange
    assertion: Started with no orchestrator, the component answers live and not ready, does not exit, and refuses every protected endpoint with 401 and a structured ErrorResponse.
    applies_to: [registers]
    exchange:
      start: {orchestrator: none}
      for_each: protected-endpoint
      steps:
        - request: {method: GET, path: /livez}
          expect: {status: 200, equals: {/live: true}}
        - request: {method: GET, path: /readyz}
          expect: {status: 503, equals: {/ready: false}}
        - request: {endpoint: each, token: none}
          expect: {status: 401, json: true, has: [/error]}
```

---

## Running Tests

The suite is run by the engine's `test run` operation, against a tree at
build time or, with `--live <url>`, its live-safe checks against a running
component ([`architecture/engine`](engine.md#build-time-and-run-time)). Its
parameters are the manifest's (`weblisk commands --json`), and no front end
runs a level or a single test of this document on its own.

## Security

```yaml
security:
  trust_model:
    description: |
      Conformance testing trusts only what it observed. A blueprint's claim, a
      generator's report and an implementation's self-description are all inputs
      to be checked rather than evidence. Its integrity rests on one property:
      a test that cannot fail proves nothing, so a check that cannot refute its
      own assertion is itself a fault.
  boundaries:
    - boundary: Implementation → Test harness. The implementation under test is
        untrusted; its output is evidence only where the harness observed it
    - boundary: Test fixture → Production data. No fixture reads or writes real
        tenant data
    - boundary: Test credential → Production authority. Credentials minted for a
        run carry no authority beyond it
    - boundary: Test result → Conformance claim. A claim is made only from checks
        that ran and could have failed
  enforcement:
    - rule: A check that did not run is reported as unreached, never as passed
      mechanism: Reached and unreached are distinct results; absence of a failure
        is not a pass
    - rule: A check derives its answer from the artifact's structure, not from a
        substring
      mechanism: Structural inspection of the parse tree; an artifact that does
        not parse contributes no structure
    - rule: A test never runs against production stores or credentials
      mechanism: Fixtures and credentials are scoped to the run and discarded
        with it
    - rule: A conformance claim names the checks it rests on
      mechanism: The result records which assertions were evaluated, so a claim
        is auditable rather than asserted
```

---

## Implementation Notes

- Tests SHOULD be runnable against any implementation regardless of
  language — they exercise HTTP endpoints only.
- The test harness SHOULD be implemented as part of the Weblisk CLI
  (`weblisk test`), making it available to all implementors.
- Level 1 and 2 tests can run against a single agent or orchestrator.
  Level 3 tests require a full system (orchestrator + domain + agent).
- Mock components run on ports 19800 (mock orchestrator), 19700 (mock
  domain), 19710 (mock agent) to avoid conflicting with real instances.
- All test assertions include the test ID in failure messages for
  easy triage: `FAIL L1-03: agent_id must be 32 hex chars, got 28`.

## Verification Checklist
- [ ] Conformance sign-off requires Level 4 against a real orchestrator; the mock alone is never sufficient ([What the mock cannot establish](#what-the-mock-cannot-establish), [Level 4: Interoperability](#level-4-interoperability)) <!-- wl:check conformance-sign-off-requires-level-4 -->
- [ ] Every registering component passes L4-01: it listens, registers, renews its lease, and the orchestrator's directory lists its lease current (`ready`, or `not_ready` where its blueprint allows), never `unknown` ([L4-01: Registers With A Real Orchestrator](#l4-01-registers-with-a-real-orchestrator)) <!-- wl:check registering-component-passes-l4-01-listens -->
- [ ] A manifest carrying an extra field still registers (L4-03) ([L4-03: Signature Survives A Foreign Verifier](#l4-03-signature-survives-a-foreign-verifier)) <!-- wl:check manifest-carrying-extra-field-still-registers -->
- [ ] Every registering component passes L4-04: it starts with no orchestrator, answers `GET /livez` live and `GET /readyz` not ready, and refuses protected endpoints with 401 ([L4-04: Standalone Operation](#l4-04-standalone-operation)) <!-- wl:check registering-component-passes-l4-04-starts -->

- [ ] All Level 1 tests pass (protocol compliance) ([Level 1: Protocol Compliance](#level-1-protocol-compliance)) <!-- wl:check level-1-tests-pass-protocol-compliance -->
- [ ] L1-01 refuses a probe body carrying any member but `live` or `ready` ([L1-01: Probes](#l1-01-probes)) <!-- wl:check l1-01-refuses-probe-body-carrying -->
- [ ] All Level 2 tests pass (security compliance) ([Level 2: Security Compliance](#level-2-security-compliance)) <!-- wl:check level-2-tests-pass-security-compliance -->
- [ ] All Level 3 tests pass (lifecycle compliance) ([Level 3: Lifecycle Compliance](#level-3-lifecycle-compliance)) <!-- wl:check level-3-tests-pass-lifecycle-compliance -->
- [ ] Mock orchestrator can start and accept registrations ([Mock Orchestrator](#mock-orchestrator)) <!-- wl:check mock-orchestrator-start-accept-registrations -->
- [ ] Mock agent can respond to execute and message ([Mock Agent](#mock-agent)) <!-- wl:check mock-agent-respond-execute-message -->
- [ ] Test keys are deterministic and reproducible ([Identity Fixtures](#identity-fixtures)) <!-- wl:check test-keys-deterministic-reproducible -->
- [ ] Each `token` value of an exchange step other than `none` and `captured` is minted as its `test_tokens` entry gives it, signed by the `test-orchestrator` fixture's key, with exactly that entry's claims ([Test tokens as data](#test-tokens-as-data)) <!-- wl:check test-tokens-minted covers test-tokens-declared -->
- [ ] A check naming `start.keys` starts the component with the fixture's key written as `.weblisk/keys/<name>.key`, `kdf = none`, mode 0600, under `WL_DEV=1`, and the component registers with that key's public half; one that registers with another key fails the check ([Starting a component with a fixture key](#starting-a-component-with-a-fixture-key)) <!-- wl:check fixture-key-start covers fixture-key-written -->
- [ ] A check naming `start.config` starts the component with the fixture's value written as `.weblisk/config.yaml` in its working directory, `${instance}` replaced by that directory's absolute path; a component that reads another configuration fails the check ([Starting a component with a fixture configuration](#starting-a-component-with-a-fixture-configuration)) <!-- wl:check fixture-config-start covers fixture-config-written -->
- [ ] A dependant's sealed run starts its dependencies from their accepted builds in the services table's order: the orchestrator with `bring_up.keys`' key and no orchestrator address, then each other dependency pointed at it, each listening and answering its `live` probe before the next starts ([Bringing up accepted dependencies](#bringing-up-accepted-dependencies)) <!-- wl:check dependencies-brought-up-in-order covers dependencies-started-in-order -->
- [ ] Before anything else starts beside it, the accepted orchestrator is claimed by `bring_up.operator` with the bootstrap secret read from its own working directory, and its attestation token is captured; a bring-up step that fails leaves the dependant's run unsettled naming the step, and the secret appears in no event, record, evidence or log ([Bringing up accepted dependencies](#bringing-up-accepted-dependencies)) <!-- wl:check first-operator-claims-accepted-hub covers first-operator-bootstrapped bootstrap-secret-kept-in-run -->
- [ ] A check naming a key fixture in `start.keys` starts the component with that fixture's key file as its `kdf` gives it, an `argon2id` key under its passphrase and fixed salt, the passphrase reaching it only by the source its configuration names ([Key fixtures](#key-fixtures)) <!-- wl:check key-fixture-start covers fixture-key-forms -->
- [ ] Each `start.files` entry is written before the component starts, a `text` fixture exactly and any other as JSON or YAML by its extension, mode 0600; an act `place` writes one the same way while it runs; a request-body fixture is sent and never placed ([Placing files](#placing-files)) <!-- wl:check files-placed covers fixture-files-placed -->
- [ ] The mock orchestrator, the mock agent and every stood service record each request that reaches them, in order, and a step's `expect.received` is judged over those records alone ([Harness roles](#harness-roles)) <!-- wl:check harness-records covers harness-records-received -->
- [ ] A step sent `from: probe` is attempted by the mock agent through the named boundary of the component's own enforcement package, and a component whose language names no such package leaves the check unread ([The probe agent](#the-probe-agent)) <!-- wl:check probe-behind-enforcement covers probe-agent-behind-enforcement -->
- [ ] Tests run against HTTP endpoints only (black-box) ([Overview](#overview), [Implementation Notes](#implementation-notes)) <!-- wl:check tests-run-against-http-endpoints-black -->

### A check that cannot read the artifact MUST say so

A conformance check reports on generated code it did not write. When it cannot
parse what it is looking at, the honest result is "I could not tell", and it
MUST NOT be reported as an absence in the artifact.

The route check accepted only a string literal as a mux pattern. Real generated
code registers from a table of named constants:

```go
{pattern: protocol.PathAdminOverview, methods: ...},
{pattern: agents + "/{name}", methods: ...},
```

It found no literals, recorded no routes, and refuted twenty-one correct
assertions with `no handler is registered for:` the health route of the day —
about a hub that registered that route correctly. Resolving constants, local aliases and
concatenation took the same artifact from **0 routes found to 17**, the complete
surface.

So a structural check MUST:

- Resolve the expressions real code is written in — named constants, qualified
  constants, local aliases and concatenation — not only literals.
- Record what it could not resolve, and report that as a limit of the check
  rather than as a finding about the artifact.
- Never invent a route, symbol or field from an expression it could not
  evaluate. A partial resolution is not an answer.

This is `patterns/scope`'s rule about confident zeroes, applied to tooling: a
check that reports absence when it means illegibility teaches an operator to
ignore its output, which costs more than the check was worth.

### A result that is not acted on is not a check

Conformance ran the generated component, found that it panicked at startup,
printed the stack trace, attempted two rounds of repair, reported
`the component does not run` — and the build **exited 0**.

The results were printed and discarded. Everything reading the exit status — a
script, a CI job, a control plane, an operator — was told a hub had been built,
and the hub did not start.

So a build MUST fail when:

- the component does not run, or
- any conformance test **failed**.

An **unrun** test MUST NOT fail the build. "We have not verified this" and "this
is wrong" are different facts, and conflating them makes the unrun count a
reason to reject a correct build — while still reporting unrun tests as what
they are, which is never passes.

The failure MUST be reported **last**, after the checklist and the model's own
verdicts. Returning at the point of detection hides the two reports where the
cause usually is.

A check whose result is discarded is indistinguishable from no check, except
that it costs time and looks like diligence.

### Level 0: it starts

Before any assertion about behaviour, the component MUST be started with **no
terminal attached** and MUST answer `GET /livez`. Two separate faults
were caught only by doing this by hand:

- a mux pattern conflict that compiles, passes every structural check, and
  panics when the routes are registered
- a service that prompts for a key passphrase and dies on EOF

Neither is visible in source review, and both make every other level
unrunnable.
