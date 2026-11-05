---
family: schemas/family@1
version: 1.5.0
noun: block
---
# Schema: Blocks

The block catalogue: every typed block a slot may hold, keyed by the root key
that names it, with the schema its value must satisfy, how its entries are
identified, and the closed vocabulary a declared type's fields are written in.

A slot names the blocks it holds ([`schemas/family`](family.md#the-grammar-keywords));
this file says what each one is. It declares no files of its own: it is a
library of definitions, cited as `schemas/blocks#/$defs/<name>`.

## Requirements

```yaml
requirements:
  - id: catalogue-closed
    level: must
    text: >-
      A block type is a root key this catalogue names. A yaml fence whose
      single root key it does not name is text, and a family adds a block
      type by adding it here.
  - id: entries-by-declaration
    level: must
    text: >-
      A block's entries are its mapping's keys when the catalogue says
      `entries: keys`, and its list items named by the field the catalogue
      gives in `entries: {by: <field>}` otherwise, in the order the block
      writes them. Where the catalogue names a ref `family`, each entry is a
      part id in that family, citable from outside the file. Where it names
      none (`header`, `sections`, `blocks`, `defs`, `events`, `config`,
      `errors`), an entry's id is named only within its block, as the
      block's own schema writes it (an error's code, a config key), and is
      never a ref. Two entries of one block with one id are refused.
  - id: tables-by-column-name
    level: must
    text: >-
      A block of form table is a GFM table whose header cells are matched to
      properties by the catalogue's `columns`, by name and in any order. A
      cell is trimmed, read without one enclosing pair of backticks, and read
      as an integer where its property's schema is integer. A column the
      catalogue does not name is reported; a missing column whose property is
      required is refused.
  - id: type-vocabulary-closed
    level: must
    text: >-
      A declared type's field has a `type` the type-expr grammar below
      accepts, and no other, and a description. An enum field lists its
      values. A field's other properties, and a type's constraints, are the
      `field` and `type` definitions', and no others.
  - id: legacy-type-spellings
    level: must
    text: >-
      In grammar 1 a spelling listed under "Older spellings" is rewritten in
      the block's projected value to what it names, before the schema is
      applied, and reported as legacy-spelling with the spelling as subject.
      Any other spelling fails the schema.
```

## Types

A field's `type` is one of these, or built from them:

```
type-expr = scalar / "list<" type-expr ">" / "map<" type-expr ">" / "ref:" ref
scalar    = <a value of the definition `scalar`>
```

The scalars are the definition `scalar` below, their one machine-readable
home; the grammar composes them, and a walker asserts the whole through the
format `type-expr`. `ref` is [`schemas/names`](names.md#the-grammar)' ref,
naming a declared type.

Where this differs from the closed set the analyses proposed (`list<T>`,
`map<K,V>`, `enum`, `ref:T` over the scalars), it differs for a stated reason:

- **`map<V>` takes one parameter.** A map is written as a JSON object, whose
  keys are strings, so a key type other than string has no written form.
- **`object` and `any` exist** because today's types and config blocks hold 55
  `object` fields and 4 `any` fields (protocol/, architecture/, patterns/ and
  agents/, measured 2026-10-15) whose shape no type declares yet. Without them
  a migration would have to invent a shape or drop the field. An `object` is a
  JSON object whose shape is not declared and `any` is any JSON value; both
  say that nothing checks the value, so a field that has a shape names a type
  instead. The older `json` reads as `any` because it meant any JSON value.
- **`date`** is below.

The wire form of `integer`, `timestamp`, `duration` and `uuid` is
[`protocol/conventions`](../protocol/conventions.md)' to state, and of `bytes`
[`protocol/types`](../protocol/types.md#conventions)'. `date` is a
calendar date with no time or zone, written as RFC 3339's `full-date`
(`2026-10-15`); it exists because a review date, an expiry or a due date is
not an instant, and writing one as a timestamp invents a time of day and a
zone nobody chose.

### Older spellings

Spellings that files written before grammar 1 use, of a type or of a field
property. A walk in grammar 1 reads each as what it names and reports it as
legacy-spelling. This table is how grammar 1 reads them, not a list of retired
spellings: when the migration (`v2-migrate`) has rewritten them, it retires
each in [`RETIRED.md`](../RETIRED.md), their one home from then on, and the
grammar that follows refuses them.

| Spelling | Reads as |
|---|---|
| `int` | `integer` |
| `int32` | `integer` |
| `int64` | `integer` |
| `bool` | `boolean` |
| `float` | `number` |
| `float64` | `number` |
| `double` | `number` |
| `datetime` | `timestamp` |
| `text` | `string` |
| `binary` | `bytes` |
| `json` | `any` |
| `list` | `list<any>` |
| `array` | `list<any>` |
| `[]T`, `T[]` | `list<T>` |
| `map` | `map<any>` |
| `map[string]T` | `map<T>` |
| `enum(a, b)` | `enum` with `values: [a, b]` |
| a bare PascalCase name `T`, as the `types` block's keys are written | `ref:T` |
| `type: list` or `array`, with `items: T` | `type: list<T>` |
| `optional: true`, with no `required` | `required: false` |
| `enum: [a, b]` | `values: [a, b]` |
| `max_length: n` | `max: n` |
| a field's `constraints: {...}` mapping | its properties, as properties of the field |
| `fields` as a list of items each with `name` | `fields` as a mapping by that name |

The properties are [`schemas/common`](common.md#field-constraint-properties)'
table, which grammar 1 carries whole except for `optional`, which said the
same as `required: false`, and `enum`, which `values` now names so that the
word `enum` means one thing, the type.

An `int64` that holds a time is read as `integer` here, as any `int64` is. A
field that holds an instant is declared `timestamp`
([`protocol/conventions`](../protocol/conventions.md#instant)); a walk never
decides that field by field.

## Formats

A walker asserts these `format` values; JSON Schema leaves an unknown format
unasserted, and these must not be.

| Format | Satisfied by |
|---|---|
| `weblisk-ref` | a string [`schemas/names`](names.md#the-grammar)' `ref` accepts |
| `weblisk-citation` | a string its `citation` accepts |
| `weblisk-version` | a string its `version` accepts |
| `weblisk-family-ref` | a string its `ref` accepts, then `@` and a major, as a file's `family:` is written ([`schemas/names`](names.md#three-separators-three-meanings)) |
| `version-range` | a range as [`schemas/common`](common.md#version-ranges) writes one |
| `type-expr` | a string the type-expr grammar above accepts |
| `glob` | a path pattern where `*` matches within one segment and `**` across segments |
| `date` | JSON Schema's own: RFC 3339 `full-date` |

## Blocks

```yaml
blocks:
  header:
    schema: {$ref: "schemas/family#/$defs/header-block"}
  sections:
    schema: {$ref: "schemas/family#/$defs/sections-block"}
  blocks:
    schema: {$ref: "#/$defs/catalogue"}
    entries: keys
  defs:
    schema: {type: object, additionalProperties: {type: object}}
    entries: keys
  requirements:
    schema: {type: array, minItems: 1, items: {$ref: "#/$defs/requirement"}}
    entries: {by: id}
    family: requirement
  verifies:
    schema: {type: array, minItems: 1, items: {$ref: "#/$defs/check"}}
    entries: {by: id}
    family: check
  types:
    schema: {type: object, minProperties: 1, propertyNames: {pattern: "^[A-Z][A-Za-z0-9]*$"},
             additionalProperties: {$ref: "#/$defs/type"}}
    entries: keys
    family: type
  serves:
    schema: {type: array, minItems: 1, items: {$ref: "#/$defs/operation"}}
    entries: {by: id}
    family: operation
  events:
    schema: {type: array, minItems: 1, items: {$ref: "#/$defs/event"}}
    entries: {by: id}
  config:
    schema: {type: object, minProperties: 1, additionalProperties: {$ref: "#/$defs/field"}}
    entries: keys
  errors:
    schema: {type: array, minItems: 1, items: {$ref: "#/$defs/error"}}
    entries: {by: code}
    forms: [yaml, table]
    columns: {Code: code, HTTP: http, Category: category, Description: description}
  rules:
    schema: {type: array, minItems: 1, items: {$ref: "schemas/mapping#/$defs/rule"}}
    entries: {by: id}
    family: mapping
```

## Checks

A `verifies` entry is a **check**: it names the criteria it settles (`covers`)
and how they are settled (`check`). A checklist item's `wl:check` comment is
today's spelling of one ([`schemas/common`](common.md#every-item-has-a-frozen-id)),
with its `check` left `translated`; a `verifies` entry with the same id, in
the same file, declares its kind and data.

`check` is a closed vocabulary, the definition `check-kind`. The engine
implements each kind once, as an interpreter, and holds no check of its own: a
kind is a contract with code, as a capability is ([`schemas/kinds`](kinds.md#the-model-open-kinds-closed-capabilities)).
The corpus writes every check of a kind as data, under the key that names the
kind, in the shape that kind's definition gives. A name the vocabulary does not
hold is refused by `checks/check-kinds.py`, not read as a new kind.

| Kind | Run against | The corpus writes | The executor | Fits |
|---|---|---|---|---|
| `translated` | a component | nothing beyond the criterion | runs the test the translate step wrote from the criterion alone, at the path and with the command the language declares | anything not yet written as data; the default |
| `exchange` | a component | requests in order, the identity and token each is made with, and what each answer must hold (`check-exchange`) | starts the component sealed, sends them, compares | refusals, scope, step-up, replay, routing |
| `vector` | a component | a published vector file, which entries, and the one request each entry is put through (`check-vector`) | sends the request once per entry, filled from it | signatures, canonical forms, fixed-form statements |
| `join` | a component | what to start beside it and what to observe (`check-join`) | starts them, observes registration, lease and readiness | joining a tenant; L4-01 to L4-04 |
| `record` | a component | an exchange, then the record that must follow it (`check-record`) | runs it, reads the audit route or the log lines | evidence |
| `topology` | a component | instances, what they share, and acts on them (`check-topology`) | arranges them, acts, then runs any steps | `jti` across instances, durability across a restart, starting unattended |
| `structure` | a component's source | a query the language blueprint declares by name, and what it must find (`check-structure`) | runs the language's query over the parse tree | form; the code's shape |
| `walk-validates`, `walk-refuses`, `vectors-agree`, `corpus-check`, `neutrality-derived` | the corpus | an assertion | `checks/` or a walker | the corpus's own rules |

Three fields every component check may carry:

- **`applies_to`** names the components it is run against: a component kind,
  or a selector, from the `component_kinds` block of
  [`schemas/kinds`](kinds.md#component-kinds). Absent, the check runs against
  every component that owes what it covers; present, it runs against exactly
  the components it names, which then owe it even where their blueprint does
  not require its file. Who owes what is
  [`architecture/engine`](../architecture/engine.md#what-a-component-owes)'s.
  A check addressed to an agent is never a failure of an orchestrator.
- **`live`** is `safe` where the check may run against a running tenant, and
  `sealed-only`, the default, where it changes state or needs fixtures only a
  build's sealed run has.
- **Placeholders.** A string in a request or an expectation may hold
  `${name}`: a value an earlier step captured; `${now}`; `${token}`, the token
  the step's `token` gives; `${self/<pointer>}`, the manifest the component
  under test describes itself with; a fixture of
  [`architecture/testing`](../architecture/testing.md#test-fixtures) as
  `${fixture/<name>/<pointer>}`, an identity's `public_key` derived from its
  seed; or, in a `vector` check, the entry as `${v/<pointer>}`. In a
  configuration fixture a check's `start.config` names, `${instance}` is the
  absolute path of the working directory the component is started in. A string that
  is one placeholder and nothing else is replaced by the value, whatever its
  type. A value that resolves to nothing is a fault of the check, reported as
  such, never sent empty.
- **The orchestrator under test.** `start.orchestrator: mock` starts the mock
  unless the component under test is of a kind that holds the directory
  ([`schemas/kinds`](kinds.md#component-kinds): it does not register and runs
  with nothing), which is instead started with the `test-orchestrator`
  fixture's key, so that a token the harness mints verifies at either.

A check whose executor cannot read what it must judge (a pattern it cannot
resolve, a query the language does not declare, a component that will not
start) reports **unread**, never passed and never failed
([`architecture/testing`](../architecture/testing.md), "A check that cannot
read the artifact MUST say so"). Examples of every kind, and one invalid
check per rule, are [`vectors/check-kinds/`](../vectors/check-kinds/README.md).

### Which endpoints are protected

Every endpoint a blueprint serves says what a request must carry to reach it,
as its `auth`: in a declaration's `serves` list, and in a `serves` block's
`http`. `auth` is a closed vocabulary, the definition `endpoint-auth`, and
`checks/check-kinds.py` refuses any other value.

| `auth` | A request must carry | Protected |
|---|---|---|
| `none` | nothing; anyone may reach it | no |
| `identity` | a signature by the caller's own key over what it sends, as a registration is signed ([`protocol/spec`](../protocol/spec.md#post-v1register)), and no bearer token | no |
| `token` | a bearer token of a kind the route takes, whatever its capabilities | yes |
| a capability, such as `admin:read` | a bearer token carrying that capability, a name [`protocol/types`](../protocol/types.md#capability) lists | yes |

`for_each: protected-endpoint` selects exactly the endpoints of the component's
own blueprint whose `auth` is `token` or a capability. An endpoint whose `auth`
is absent is not selected, and the check reports it **unread**, naming the
endpoint, rather than guessing either way.

## Definitions

```yaml
defs:
  ref: {type: string, format: weblisk-ref}
  citation: {type: string, format: weblisk-citation}
  version: {type: string, format: weblisk-version}
  date: {type: string, format: date}
  part-id: {type: string, pattern: "^[a-z0-9][a-z0-9-]*$"}
  scalar: {enum: [string, integer, number, boolean, timestamp, date, duration, uuid, bytes, enum, object, any]}
  catalogue:
    type: object
    additionalProperties:
      type: object
      required: [schema]
      unevaluatedProperties: false
      properties:
        schema: {type: object}
        entries:
          oneOf:
            - {const: keys}
            - type: object
              required: [by]
              unevaluatedProperties: false
              properties:
                by: {type: string}
        family: {type: string, description: "A ref family schemas/names declares."}
        forms: {type: array, items: {enum: [yaml, table]}, description: "Default [yaml]."}
        columns: {type: object, additionalProperties: {type: string}}
  requirement:
    type: object
    required: [id, level, text]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      level: {enum: [must, should, may]}
      text: {type: string, minLength: 1}
      refs: {type: array, items: {$ref: "#/$defs/ref"}}
  check:
    type: object
    required: [id, covers, assertion]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      covers: {type: array, minItems: 1, items: {$ref: "#/$defs/ref"}}
      check: {type: string, description: "The kind of check that proves it: a value of check-kind; translated when absent."}
      assertion: {type: string, minLength: 1}
      applies_to: {type: array, minItems: 1, items: {type: string, pattern: "^[a-z][a-z0-9-]*$"}, description: "The components it is run against: a component kind schemas/kinds declares, or a selector its component_kinds block declares. Every component the requirement is owed by, when absent (architecture/engine, What a component owes); present, exactly the components it names, who then owe it."}
      live: {enum: [safe, sealed-only], default: sealed-only, description: "Whether it may run against a running tenant (safe) or only in a build's sealed run."}
      exchange: {$ref: "#/$defs/check-exchange"}
      vector: {$ref: "#/$defs/check-vector"}
      join: {$ref: "#/$defs/check-join"}
      record: {$ref: "#/$defs/check-record"}
      topology: {$ref: "#/$defs/check-topology"}
      structure: {$ref: "#/$defs/check-structure"}
    allOf:
      - {if: {required: [check], properties: {check: {const: exchange}}}, then: {required: [exchange]}}
      - {if: {required: [check], properties: {check: {const: vector}}}, then: {required: [vector]}}
      - {if: {required: [check], properties: {check: {const: join}}}, then: {required: [join]}}
      - {if: {required: [check], properties: {check: {const: record}}}, then: {required: [record]}}
      - {if: {required: [check], properties: {check: {const: topology}}}, then: {required: [topology]}}
      - {if: {required: [check], properties: {check: {const: structure}}}, then: {required: [structure]}}
  check-kind:
    description: "The closed vocabulary of check kinds. Each is implemented once, by an interpreter in the engine, and the corpus writes every check of it as data."
    anyOf:
      - {$ref: "#/$defs/check-kind-component"}
      - {$ref: "#/$defs/check-kind-corpus"}
  check-kind-component:
    description: "Kinds run against a tenant's component. translated is settled by a test the translate step writes from the criterion alone; the rest by the data under the key of the kind's name."
    enum: [translated, exchange, vector, join, record, topology, structure]
  check-kind-corpus:
    description: "Kinds run against the corpus itself, by checks/ or a walker."
    enum: [walk-validates, walk-refuses, vectors-agree, corpus-check, neutrality-derived]
  duration-literal: {type: string, pattern: "^[0-9]+(ms|s|m)$"}
  json-pointer: {type: string, pattern: "^(/[^/]*)*$"}
  check-start:
    type: object
    description: "How the component under test is started. Absent: alone, sealed, with no orchestrator, standard input closed."
    unevaluatedProperties: false
    properties:
      orchestrator: {enum: [none, mock, built], default: none, description: "none; the mock architecture/testing specifies, built as a component; or the orchestrator tree this build is judged against."}
      with: {type: array, items: {$ref: "#/$defs/ref"}, description: "Other components started first, each from the tree it was accepted with, in the order the services table gives."}
      keys: {type: string, description: "An identity fixture of architecture/testing whose key the component is started with, in place of a generated one: written as its key file before it starts (architecture/testing, Starting a component with a fixture key)."}
      config: {type: string, description: "A configuration fixture of architecture/testing written as the component's .weblisk/config.yaml in its working directory before it starts, ${instance} in it naming that directory (architecture/testing, Starting a component with a fixture configuration)."}
      mock_agent: {type: object, additionalProperties: {}, description: "Responses the mock agent of architecture/testing gives, keyed by action; a value is the TaskResult or payload it answers."}
      env: {type: object, additionalProperties: {type: string}, description: "Variables added to the clean start environment."}
  exchange-request:
    type: object
    unevaluatedProperties: false
    anyOf: [{required: [method]}, {required: [endpoint]}, {required: [replay]}]
    properties:
      method: {enum: [GET, HEAD, POST, PUT, PATCH, DELETE]}
      endpoint: {const: each, description: "The method and path of each endpoint the check's for_each selects, its path parameters filled with conformance-probe."}
      replay: {$ref: "#/$defs/part-id", description: "Send again the exact bytes an earlier step with this id sent."}
      path: {type: string, pattern: "^/", description: "The path as sent; a placeholder ${name} is filled from an earlier capture or a fixture."}
      operation: {$ref: "#/$defs/ref", description: "An operation a serves block or Endpoints table declares; its method and path, in place of path."}
      listener: {enum: [public, admin], default: public}
      token: {enum: [none, own, expired, bad-signature, wrong-type, channel-self, channel-other, pass, pass-other, operator, work, captured], default: none, description: "The bearer token. none: no token; captured: the value an earlier step captured as token; every other value is minted as architecture/testing's test_tokens block declares it (Test tokens as data): own, a registration token for the as identity; expired, own past its exp; bad-signature, own with its signature broken; wrong-type, own carrying a type the route does not take; channel-self and channel-other, a channel token to the component under test or to another target; pass and pass-other, a person's pass for the as identity addressed to the component under test or to another component; operator, the as identity's operator token; work, a work pass addressed to the component under test on the as identity's authority."}
      headers: {type: object, additionalProperties: {type: string}}
      body: {description: "Any JSON value; strings may hold placeholders."}
      body_bytes: {type: integer, minimum: 0, description: "A body of this many bytes, in place of body."}
      sign:
        type: object
        required: [over, into]
        unevaluatedProperties: false
        description: "Sign part of the body with the as identity's key, as protocol/identity signs: over the canonical form of the value at over, encoded as the field at into declares."
        properties:
          over: {$ref: "#/$defs/json-pointer"}
          members: {type: array, minItems: 1, items: {type: string}, description: "Sign the object of only these members of the value at over."}
          into: {$ref: "#/$defs/json-pointer"}
          encoding: {enum: [base64url, hex], default: base64url}
          with: {enum: [own, other-key, other-bytes], default: own, description: "own key over those bytes; another fixture's key; or the own key over other bytes."}
          timestamp: {$ref: "#/$defs/json-pointer", description: "Where the signing instant is written."}
          age: {$ref: "#/$defs/duration-literal", description: "How long before now the timestamp says; 0s when absent."}
  exchange-expect:
    type: object
    unevaluatedProperties: false
    properties:
      status: {oneOf: [{type: integer}, {type: array, minItems: 1, items: {type: integer}}]}
      status_not: {type: array, minItems: 1, items: {type: integer}}
      code: {type: string, pattern: "^[A-Z][A-Z0-9_]*$", description: "The registered error code the body carries."}
      json: {type: boolean, description: "The body is JSON."}
      has: {type: array, items: {$ref: "#/$defs/json-pointer"}, description: "Members the body holds."}
      lacks: {type: array, items: {$ref: "#/$defs/json-pointer"}, description: "Members the body does not hold."}
      only: {type: array, items: {type: string}, description: "The body's top-level members are exactly these."}
      equals: {type: object, additionalProperties: {}, description: "JSON pointer to the value found there."}
      matches: {type: object, additionalProperties: {type: string}, description: "JSON pointer to a regular expression its string value matches."}
      mentions: {type: array, items: {type: string}, description: "The error member's text holds at least one of these words."}
  exchange-step:
    type: object
    required: [request, expect]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      as: {type: string, description: "An identity fixture of architecture/testing, or anonymous."}
      instance: {type: string, description: "The instance it is sent to, in a topology check; or a component started beside it, by name."}
      repeat: {type: integer, minimum: 1, description: "Sent this many times at once."}
      request: {$ref: "#/$defs/exchange-request"}
      expect: {$ref: "#/$defs/exchange-expect"}
      capture: {type: object, additionalProperties: {$ref: "#/$defs/json-pointer"}, description: "A name for a value of the response, by pointer, for later steps' placeholders."}
  check-exchange:
    type: object
    required: [steps]
    unevaluatedProperties: false
    properties:
      start: {$ref: "#/$defs/check-start"}
      for_each: {enum: [endpoint, protected-endpoint], description: "A step whose request says endpoint: each is sent once per endpoint the component's own blueprint serves, or per protected one: one whose endpoint-auth is token or a capability (Checks, Which endpoints are protected)."}
      steps: {type: array, minItems: 1, items: {$ref: "#/$defs/exchange-step"}}
  check-vector:
    type: object
    required: [file, entries, step]
    unevaluatedProperties: false
    properties:
      file: {type: string, pattern: "^vectors/", description: "A published vector file."}
      entries: {$ref: "#/$defs/json-pointer", description: "Where its list of entries is."}
      where: {type: object, additionalProperties: {}, description: "Only entries whose member at each pointer has this value."}
      start: {$ref: "#/$defs/check-start"}
      step: {$ref: "#/$defs/exchange-step", description: "Sent once per entry; ${v/<pointer>} reads the entry."}
  check-join:
    type: object
    required: [observe]
    unevaluatedProperties: false
    properties:
      start: {$ref: "#/$defs/check-start"}
      observe:
        type: array
        minItems: 1
        items: {enum: [listens, no-exit, registered, listed, lease-current, lease-renewed, readyz-agrees]}
        description: "listens: it binds its port; no-exit: it does not exit; registered: it holds an agent_id and a token; listed: the orchestrator's directory lists it; lease-current: its lease_state is ready, or not_ready where its blueprint allows, never unknown; lease-renewed: it renews within a third of its duration; readyz-agrees: its /readyz answers as its last renewal did."
      within: {oneOf: [{$ref: "#/$defs/duration-literal"}, {const: lease}], description: "How long each observation may take; lease is one lease duration: the orchestrator.lease_duration the started orchestrator's configuration sets, else the default schemas/config's config block declares."}
      steps: {type: array, items: {$ref: "#/$defs/exchange-step"}, description: "Sent once joined."}
  check-record:
    type: object
    required: [steps, record]
    unevaluatedProperties: false
    properties:
      start: {$ref: "#/$defs/check-start"}
      steps: {type: array, minItems: 1, items: {$ref: "#/$defs/exchange-step"}}
      record:
        type: object
        required: [source, match]
        unevaluatedProperties: false
        properties:
          source: {enum: [audit, log, event, trace]}
          read: {$ref: "#/$defs/exchange-request", description: "How the record is read where it is served (audit); a log is read from the process's standard output."}
          match: {type: object, additionalProperties: {}, description: "JSON pointer, in one record, to the value it must hold."}
          count: {type: integer, minimum: 0, description: "Exactly this many records match; at least one when absent."}
          within: {$ref: "#/$defs/duration-literal"}
  check-topology:
    type: object
    required: [instances, acts]
    unevaluatedProperties: false
    properties:
      instances:
        type: array
        minItems: 1
        items:
          type: object
          required: [name]
          unevaluatedProperties: false
          properties:
            name: {$ref: "#/$defs/part-id"}
            shares: {type: array, items: {type: string}, description: "Stores it shares with the instances that name the same store."}
            stdin: {enum: [closed, terminal], default: closed}
            env: {type: object, additionalProperties: {type: string}}
      acts:
        type: array
        minItems: 1
        items:
          type: object
          required: [act]
          unevaluatedProperties: false
          properties:
            act: {enum: [start, stop, restart, kill, make-unreadable, wait]}
            instance: {type: string}
            store: {type: string}
            for: {$ref: "#/$defs/duration-literal"}
            expect: {enum: [ready, live, exits, refuses-start], description: "What the act must lead to."}
            within: {$ref: "#/$defs/duration-literal"}
      steps: {type: array, items: {$ref: "#/$defs/exchange-step"}}
  check-structure:
    type: object
    required: [query, expect]
    unevaluatedProperties: false
    properties:
      query: {$ref: "#/$defs/part-id", description: "A query the language blueprint's structure block declares; a language that declares none leaves the check unsettled for that language."}
      args: {type: object, additionalProperties: {type: [string, array]}, description: "Values for the query's ${name} placeholders."}
      scope: {enum: [component, module, contract, outside-contract], default: component}
      expect:
        oneOf:
          - {enum: [none, some]}
          - type: object
            minProperties: 1
            maxProperties: 1
            unevaluatedProperties: false
            properties:
              includes: {type: array, minItems: 1, items: {type: string}, description: "The captured values include every one of these."}
              subset_of: {$ref: "#/$defs/part-id", description: "Every captured value is one another query captures."}
  field:
    type: object
    required: [type, description]
    unevaluatedProperties: false
    properties:
      type: {type: string, format: type-expr}
      description: {type: string, minLength: 1}
      required: {type: boolean, default: true}
      values: {type: array, minItems: 1, items: {type: [string, integer, number, boolean]}, description: "The values allowed."}
      default: {}
      unit: {type: string, description: "seconds, bytes, milliseconds..."}
      format: {type: string, description: "A hint to a reader or a generator, such as uuid-v7, base64url or semver. Open, and never asserted by a walk."}
      min: {type: number, description: "The least value, or the least length of a string or list."}
      max: {type: number, description: "The greatest value, or the greatest length of a string or list."}
      auto: {type: boolean, description: "Set by the system, never supplied."}
      references: {type: string, pattern: "^[A-Z][A-Za-z0-9]*\\.[a-z][a-z0-9_]*$", description: "The Type.field this field's value refers to, in this file or one it requires."}
      required_when: {type: string, description: "A condition on fields of the same type under which this one is required."}
      exclusive_with: {type: string, description: "A field of the same type; exactly one of the two is set."}
    if: {properties: {type: {const: enum}}}
    then: {required: [values]}
  type:
    type: object
    required: [fields]
    unevaluatedProperties: false
    properties:
      description: {type: string}
      fields: {type: object, additionalProperties: {$ref: "#/$defs/field"}}
      constraints:
        type: array
        items:
          type: object
          required: [name, type]
          unevaluatedProperties: false
          properties:
            name: {type: string, pattern: "^[a-z][a-z0-9_]*$"}
            type: {enum: [unique, check, foreign_key]}
            fields: {type: array, minItems: 1, items: {type: string}}
            expression: {type: string, description: "SQL-style; a check constraint's condition."}
            description: {type: string}
          if: {properties: {type: {const: check}}}
          then: {required: [expression]}
          else: {required: [fields]}
  operation:
    type: object
    required: [id, http]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      request: {$ref: "#/$defs/ref"}
      response: {$ref: "#/$defs/ref"}
      http:
        type: object
        description: "Required: HTTP is Weblisk's one transport, so every operation a blueprint serves has its HTTP binding."
        required: [method, path]
        unevaluatedProperties: false
        properties:
          method: {enum: [GET, HEAD, POST, PUT, PATCH, DELETE]}
          path: {type: string, pattern: "^/"}
          auth: {$ref: "#/$defs/endpoint-auth"}
  endpoint-auth:
    description: "What a request must carry to reach an endpoint: the auth of a serves entry, in a declaration's serves list or a serves block's http. A closed vocabulary (Checks, Which endpoints are protected)."
    anyOf:
      - enum: [none, identity, token]
      - {type: string, pattern: "^[a-z]+:([a-z][a-z-]*|\\*)$", description: "A capability protocol/types' Capability section lists: a bearer token carrying it."}
  event:
    type: object
    required: [id, direction, payload]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      direction: {enum: [publishes, subscribes]}
      payload: {$ref: "#/$defs/ref"}
  error:
    type: object
    required: [code, http, category]
    unevaluatedProperties: false
    properties:
      code: {type: string, pattern: "^[A-Z][A-Z0-9_]*$"}
      http: {type: integer, minimum: 100, maximum: 599}
      category: {enum: [transient, permanent]}
      description: {type: string}
  requires-entry:
    type: object
    required: [ref, version]
    unevaluatedProperties: false
    properties:
      ref: {$ref: "#/$defs/ref"}
      version: {type: string, format: version-range}
      bindings:
        type: array
        items:
          type: object
          minProperties: 1
          maxProperties: 1
          unevaluatedProperties: false
          properties:
            type: {$ref: "#/$defs/ref"}
            requirement: {$ref: "#/$defs/ref"}
            operation: {$ref: "#/$defs/ref"}
  retired:
    type: array
    items:
      type: object
      required: [id, version]
      unevaluatedProperties: false
      properties:
        id: {$ref: "#/$defs/part-id"}
        version: {$ref: "#/$defs/version"}
        replaced_by: {$ref: "#/$defs/ref"}
```

## Verification

```yaml
verifies:
  - id: blocks-walks-clean
    covers: [catalogue-closed]
    check: walk-validates
    assertion: Walking schemas/blocks.md as a file of the family schemas/family reports no finding whose policy is refuse.
  - id: table-read-by-name
    covers: [tables-by-column-name, entries-by-declaration]
    check: vectors-agree
    assertion: The table vector, whose columns are in another order and include one the catalogue does not name, projects the same entry digests as its rows written as yaml, and reports the extra column.
  - id: legacy-spelling-reported
    covers: [legacy-type-spellings, type-vocabulary-closed]
    check: vectors-agree
    assertion: The legacy vector's `int64` field is reported and read as integer, and its `int128` field is refused.
  - id: scalars-in-one-place
    covers: [type-vocabulary-closed]
    check: walk-validates
    assertion: The type-expr format accepts exactly the values of the definition `scalar` and their compositions, so removing `date` from `scalar` makes a field of type date fail block-schema.
```
