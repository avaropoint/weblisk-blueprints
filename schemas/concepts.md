---
family: schemas/family@1
version: 1.0.0
noun: concept
---
# Schema: Concepts

The concepts a mapping rule answers, each named `<class>/<name>`. The classes
are closed and [`schemas/mapping`](mapping.md#classes) names them with their
owning axes; the names are data, here, so adding a concept a blueprint needs
is an entry in this file and no change to any tool. The same split
[`schemas/kinds`](kinds.md#the-model-open-kinds-closed-capabilities) makes
between kinds and capabilities.

A concept is not a ref and has no namespace: it is a word mappings and
blueprints share, as a kind is. What an output cites is the rule that answered
the concept, which has an id ([`schemas/kinds`](kinds.md), `mapping`).

## Requirements

```yaml
requirements:
  - id: concept-in-a-class
    level: must
    text: >-
      Every concept is declared once, under a class schemas/mapping names,
      with what it is. A concept whose class's owner is `per-concept` names
      its owner; any other concept names none, and takes its class's.
  - id: required-by-cited
    level: must
    text: >-
      A service or storage concept names, in `required_by`, the blueprints
      that require the capability, so a mapping answers a capability without
      restating which blueprints need it.
```

## Concepts

The entries are measured, not invented: the types are
[`schemas/blocks`](blocks.md#types)' vocabulary; the identity primitives,
checks and tests are the rows the language mappings' Primitive Mapping,
Evaluating a Declared Check and Testing sections already carry; the services
and stores are the union of the rows in the Node and Cloudflare Service
Mapping tables, with the blueprints those rows name; the UI units are the
documents under [`frameworks/weblisk/`](../frameworks/weblisk/README.md).

```yaml
# Read by tools: the concepts, by class.
concepts:
  type/string: {text: "A string."}
  type/integer: {text: "An integer."}
  type/number: {text: "A number."}
  type/boolean: {text: "A boolean."}
  type/timestamp: {text: "An instant."}
  type/date: {text: "A calendar date with no time or zone."}
  type/duration: {text: "A length of time."}
  type/uuid: {text: "A UUID."}
  type/bytes: {text: "A sequence of bytes."}
  type/enum: {text: "One of a field's listed values."}
  type/object: {text: "A JSON object whose shape no type declares."}
  type/any: {text: "Any JSON value."}
  type/list: {text: "list<T>."}
  type/map: {text: "map<T>, keyed by string."}
  type/ref: {text: "ref:T, a declared type."}

  identifier/field: {text: "A declared field key, as a member name and as its wire name."}
  identifier/type: {text: "A declared type name."}
  identifier/package: {text: "The unit code is grouped into, named after the blueprint that specifies it."}
  identifier/path-constant: {text: "The named constant an operation's path is reached through."}
  identifier/handler: {text: "The function that answers an operation."}
  identifier/request-type: {text: "An operation's request type."}
  identifier/response-type: {text: "An operation's response type."}

  identity-primitive/signature: {text: "The signature algorithm protocol/identity names."}
  identity-primitive/backup-signature: {text: "The backup signature algorithm protocol/identity names."}
  identity-primitive/key-derivation: {text: "The key-derivation function protocol/identity names."}
  identity-primitive/symmetric-encryption: {text: "The symmetric encryption protocol/identity names."}
  identity-primitive/random: {text: "The random source protocol/identity requires."}
  identity-primitive/passphrase-channel: {text: "A channel that reads a passphrase without echoing it."}
  identity-primitive/canonical-json: {text: "RFC 8785 canonical JSON, as protocol/identity requires for signing."}

  check/no-path-literals: {text: "A path reaches a route only through its declared constant."}
  check/no-method-less-pattern: {text: "Every route pattern names its method."}
  check/endpoint-routed: {text: "A declared endpoint is in the route table."}
  check/type-has-keys: {text: "A declared type carries the declared wire keys."}
  check/error-codes-registered: {text: "Every error code used is in the registry."}
  check/starts-unattended: {text: "The built component starts with no terminal and answers its liveness route."}

  symbol/declarations: {text: "The declarations in one file: names, kinds and byte spans."}

  test/unit: {text: "A test of one unit, named after the check it proves."}
  test/integration: {text: "A test across components."}
  test/vectors: {text: "A published vector run as a test (architecture/generation, Published test vectors)."}

  lifecycle/toolchain: {owner: language, text: "The tool that builds the language, its least version and how to probe it."}
  lifecycle/build: {owner: language, text: "Building a component."}
  lifecycle/run: {owner: platform, text: "Starting a component."}
  lifecycle/deploy: {owner: platform, text: "Putting a component where it runs."}

  component/layout: {owner: platform, text: "Where a component kind's files go."}
  component/entry-point: {owner: platform, text: "The file a component starts from."}
  component/module: {owner: language, text: "The module, crate or package manifest code is built from."}

  service/http: {text: "Serving and calling HTTP.", required_by: [protocol/spec]}
  service/invocation: {text: "Service-to-service invocation.", required_by: [protocol/spec]}
  service/process-execution: {text: "Operating-system process execution.", required_by: [patterns/command]}
  service/log-emission: {text: "Structured log emission.", required_by: [patterns/logging]}
  service/client-tls: {text: "Client TLS to third parties.", required_by: [patterns/security]}
  service/scheduling: {text: "Scheduled execution.", required_by: [patterns/scheduling, agents/cron]}
  service/realtime: {text: "Bidirectional realtime transport.", required_by: [patterns/realtime-chat]}
  service/task-dispatch: {text: "Asynchronous task dispatch.", required_by: [patterns/task-dispatch, agents/task]}
  service/workflow: {text: "Multi-phase execution with durable state.", required_by: [patterns/workflow, agents/workflow]}
  service/retry: {text: "Retry and backoff.", required_by: [patterns/retry]}
  service/rate-limiting: {text: "Rate limiting.", required_by: [patterns/rate-limiting, architecture/gateway]}
  service/vector-search: {text: "Vector storage and similarity search.", required_by: [patterns/api-ai]}
  service/inference: {text: "Inference and embedding generation.", required_by: [patterns/api-ai]}
  service/model-gateway: {text: "Model provider abstraction, response caching and cost attribution.", required_by: [patterns/api-ai]}
  service/image-transformation: {text: "Image transformation.", required_by: [patterns/file-upload]}
  service/browser-automation: {text: "Browser automation and page capture.", required_by: [patterns/webhook]}
  service/offline-reconciliation: {text: "Offline reconciliation.", required_by: [patterns/offline, agents/sync]}
  service/webhook-processing: {text: "Inbound webhook processing.", required_by: [patterns/webhook, agents/webhook]}
  service/email: {text: "Outbound email.", required_by: [patterns/notification, agents/email-send]}
  service/secret-storage: {text: "Secret storage.", required_by: [patterns/secrets]}
  service/metrics-traces: {text: "Metrics and traces.", required_by: [patterns/observability, architecture/observability]}
  service/egress-control: {text: "Egress control over a component's outbound calls.", required_by: [architecture/data-security, patterns/security]}
  service/tenant-isolation: {text: "Per-tenant code isolation.", required_by: [architecture/tenancy]}
  service/expression-evaluation: {text: "Runtime expression evaluation.", required_by: [patterns/expression]}

  storage/default-backend: {text: "The default backend architecture/storage names.", required_by: [architecture/storage]}
  storage/registry: {text: "A strongly consistent registry and coordination.", required_by: [architecture/orchestrator, architecture/storage]}
  storage/records: {text: "Queryable records, audit and observations.", required_by: [architecture/storage, patterns/storage]}
  storage/objects: {text: "Object and asset storage.", required_by: [patterns/file-upload, architecture/content]}
  storage/cache: {text: "A cache.", required_by: [patterns/caching]}

  ui-unit/page: {text: "A page."}
  ui-unit/component: {text: "A component."}
  ui-unit/island: {text: "An island."}
  ui-unit/asset: {text: "An asset."}

  interface/http-description: {text: "A description of the operations a component serves over HTTP."}
  interface/event-description: {text: "A description of the events a component publishes and subscribes to."}
```

One Cloudflare row has no concept: "Relational database access outside the
platform" names no blueprint that requires it, and a concept nobody requires
is a rule nothing reads.

## Definitions

```yaml
defs:
  entry:
    type: object
    required: [text]
    unevaluatedProperties: false
    properties:
      text: {type: string, minLength: 1}
      owner: {$ref: "schemas/mapping#/$defs/axis"}
      required_by: {type: array, minItems: 1, items: {$ref: "schemas/blocks#/$defs/ref"}}
```

## Verification

```yaml
verifies:
  - id: every-concept-placed
    covers: [concept-in-a-class]
    check: vectors-agree
    assertion: checks/mapping-coverage.py finds every concept here in a class schemas/mapping names, with an owner exactly where that class's owner is per-concept.
  - id: required-by-resolves
    covers: [required-by-cited]
    check: vectors-agree
    assertion: Every required_by entry names a blueprint file of this repository.
```
