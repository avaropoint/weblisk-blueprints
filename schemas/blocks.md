---
family: schemas/family@1
version: 1.6.0
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
  - id: check-vocabulary-closed
    level: must
    text: >-
      A check's kind, an assertion operator, an act, a harness role, a token
      alteration and a placeholder are each a name this file or
      architecture/testing declares. A check written with any other is
      refused, never read as a new capability. The engine implements each
      once, as an interpreter, and holds no check of its own.
  - id: check-proves-whole-criterion
    level: must
    text: >-
      A declared check that covers a criterion proves every obligation the
      criterion states. A check whose assertion leaves part of a criterion
      unproved, or names that part as not settled here, does not cover it:
      it covers a narrower criterion, or the criterion stays unsettled. A
      check that settles part of a criterion is never counted as settling
      the whole.
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
| `topology` | a component | instances, what they share, and acts on them in order, steps among them (`check-topology`, `topology-act`) | arranges them, runs each act and each `send` in the order written, then runs any steps | `jti` across instances, durability across a restart, starting unattended, stored bytes altered, keys and stores made unreadable, files placed out of band, a key rotated, a destination's line moved |
| `structure` | a component's source | a query the language blueprint declares by name, and what it must find (`check-structure`) | runs the language's query over the parse tree | form; the code's shape; what the code never does |
| `drive` | a front end | operations of the engine's catalogue to invoke, the services to stand up in place of a hub, and what the operation and those services must show (`check-drive`) | stands them up, invokes each operation through the front end, compares | what a console or the CLI must and must not do |
| `walk-validates`, `walk-refuses`, `vectors-agree`, `corpus-check`, `neutrality-derived` | the corpus | an assertion | `checks/` or a walker | the corpus's own rules |

The fields every component check may carry:

- **`applies_to`** names the components it is run against: a component kind,
  or a selector, from the `component_kinds` block of
  [`schemas/kinds`](kinds.md#component-kinds), or, for a `drive` check, a
  client kind from its `client_kinds` block, which a `drive` check must name.
  **`except`** takes kinds or selectors out of what `applies_to` names, so
  `applies_to: [any]` with `except: [orchestrator]` is every kind but the
  orchestrator; it is never written alone. Absent, the check runs against
  every component that owes what it covers; present, it runs against exactly
  the components it names, which then owe it even where their blueprint does
  not require its file. Who owes what is
  [`architecture/engine`](../architecture/engine.md#what-a-component-owes)'s.
  A check addressed to an agent is never a failure of an orchestrator.
- **`live`** is `safe` where the check may run against a running tenant, and
  `sealed-only`, the default, where it changes state or needs fixtures only a
  build's sealed run has.
- **Placeholders.** A string in a request or an expectation may hold
  `${name}`: a value an earlier step captured; `${now}`, and `${now+<n><unit>}`
  or `${now-<n><unit>}` (`s`, `m`, `h` or `d`), an instant that far from it; `${token}`, the token
  the step's `token` gives; `${self/<pointer>}`, the manifest the component
  under test describes itself with; a fixture of
  [`architecture/testing`](../architecture/testing.md#test-fixtures) as
  `${fixture/<name>/<pointer>}`, an identity's `public_key` derived from its
  seed and its `fingerprint` from that key
  ([`protocol/identity`](../protocol/identity.md#key-fingerprint)), never
  written by hand; `${address}`, the origin the component under test listens
  at, `${address/<instance>}` an instance's in a topology check;
  `${harness/source}`, the IP address the harness's requests reach the
  component from; `${stood/<name>/<field>}`, what a service the harness stood
  up is reached at ([`architecture/testing`](../architecture/testing.md#harness-roles));
  in a statement field, `${body/<pointer>}`, the body being sent; or, in a
  `vector` check, the entry as `${v/<pointer>}`. In a fixture a check's
  `start.config` or `start.files` names, `${instance}` is the
  absolute path of the working directory the component is started in. A string that
  is one placeholder and nothing else is replaced by the value, whatever its
  type. A value that resolves to nothing is a fault of the check, reported as
  such, never sent empty.
- **The orchestrator under test.** `start.orchestrator: mock` starts the mock
  unless the component under test is of a kind that holds the directory
  ([`schemas/kinds`](kinds.md#component-kinds): it does not register and runs
  with nothing), which is instead started with the `test-orchestrator`
  fixture's key, so that a token the harness mints verifies at either.

### Assertions, acts and observations

What a check can judge is a closed set of generic capabilities, each
implemented once by the engine and named here; none is a particular check
(`check-vocabulary-closed`).

| Capability | Written as | What it does |
|---|---|---|
| response headers, an empty body | `expect.headers`, `headers_lack`, `empty` | a header's value by regular expression, in any case of its name; a header the answer does not carry; a zero-byte body |
| values in a list | `includes`, `excludes`, `length`, a `*` pointer segment | every value found at a pointer, wherever it is in a list or object |
| a token's claims, a key file, a statement | `assert: [{decodes-as}]` | decodes a WLT, a key file, base64url, hex, JSON lines or a fixed-form statement, then judges it as a body is judged |
| a digest | `assert: [{digest-of}]` | the SHA-256 of exact bytes, a stored line or a canonical form, equal to (or differing from) another value |
| a signature | `assert: [{verifies-under}]` | verifies a signature under a key over Sign JSON, raw bytes or a fixed-form statement rebuilt from its fields |
| a hash chain | `assert: [{chain-links}]` | each stored line links to the digest of the line before it, from a genesis value |
| what reached a service the harness runs | `expect.received` | the requests the mock orchestrator, the mock agent or a stood service received after the step: how many (0 proves nothing was forwarded, exchanged or sent) and what each held |
| a record, beyond equality | `record.matches`, `record.lacks_text` | a record's member by regular expression; no record's text holding a value, such as a captured token |
| a WebSocket | `request.websocket`, `expect.frames` | frames sent, and the frames received judged in order |
| a token variant | `request.token_alter` | any minted token with claims replaced or removed, its times moved, or its signature in another declared form |
| a second bearer | `request.bearer` | the bearer is a captured token while `${token}` in the body is the minted one |
| a statement signed as a fixture | `request.sign` with `form: fixed-form`, `key` | a fixed-form statement built from its prefix and fields and signed by a fixture identity; several signings over one body |
| the address a step reached | `capture: {name: "@address"}` | the origin dialled, and `@status`, `@body`, `@header/<name>` |
| what the code never does | `structure.expect.excludes` | no captured value is one listed; a query capturing `@paired` yields `<value>=<paired>` pairs, such as a code and its status |
| the manifest it registered | `join.manifest` | the manifest the orchestrator lists for it |
| an operation behind enforcement | `start.probe`, a step `from: probe` | the probe agent attempts an operation through a named boundary of the component under test |
| acts on a running topology | `topology-act` | below |

**Acts run in the order written.** A topology check's `acts` are run one after
another, and an act `send` sends its `step` at that point, so a request can
come between a stop and a start, or after bytes are altered and before the
component restarts. The `steps` after the acts are run last, as before.
The acts are: `start`, `stop`, `restart`, `kill`, `wait`; `make-unreadable`, a
store or a path, such as a key file; `alter`, a store's or a file's stored
bytes, by one of five changes; `remove`, a file; `place`, a fixture written at
a path out of band, while the instance runs or before it starts; `read`, a file
the process wrote, with its mode and any assertion over its text;
`rotate-key`, the instance's registered key rotated to a key fixture by the
rotation its blueprint declares; and `remote`, a change to a stood git
remote's line made by another party. An act on what an instance's blueprint
does not declare (a store it has no path for, a rotation it declares no way
to start) is **unread**.

**A logged security event** is a log record of the shape
[`patterns/logging`](../patterns/logging.md#security-events) declares, so a
`record` check matches one as `{source: log, match: {/log_type: security,
/error_code: <the refusal's code>}}`, with `/details/event` where the event's
name matters.

A check covers a criterion only when it proves all of it
(`check-proves-whole-criterion`). A part it cannot express is written as its
own criterion, or the criterion stays unsettled; a check never settles the
whole of what it proves in part.

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
      applies_to: {type: array, minItems: 1, items: {type: string, pattern: "^[a-z][a-z0-9-]*$"}, description: "The components it is run against: a component kind schemas/kinds declares, or a selector its component_kinds block declares; for a drive check, a client kind its client_kinds block declares. Every component the requirement is owed by, when absent (architecture/engine, What a component owes); present, exactly the components it names, who then owe it."}
      except: {type: array, minItems: 1, items: {type: string, pattern: "^[a-z][a-z0-9-]*$"}, description: "Component or client kinds, or selectors, taken out of what applies_to names: applies_to [any] with except [orchestrator] is every kind but the orchestrator. Never on its own: a check with except carries applies_to."}
      live: {enum: [safe, sealed-only], default: sealed-only, description: "Whether it may run against a running tenant (safe) or only in a build's sealed run."}
      exchange: {$ref: "#/$defs/check-exchange"}
      vector: {$ref: "#/$defs/check-vector"}
      join: {$ref: "#/$defs/check-join"}
      record: {$ref: "#/$defs/check-record"}
      topology: {$ref: "#/$defs/check-topology"}
      structure: {$ref: "#/$defs/check-structure"}
      drive: {$ref: "#/$defs/check-drive"}
    allOf:
      - {if: {required: [except]}, then: {required: [applies_to]}}
      - {if: {required: [check], properties: {check: {const: exchange}}}, then: {required: [exchange]}}
      - {if: {required: [check], properties: {check: {const: vector}}}, then: {required: [vector]}}
      - {if: {required: [check], properties: {check: {const: join}}}, then: {required: [join]}}
      - {if: {required: [check], properties: {check: {const: record}}}, then: {required: [record]}}
      - {if: {required: [check], properties: {check: {const: topology}}}, then: {required: [topology]}}
      - {if: {required: [check], properties: {check: {const: structure}}}, then: {required: [structure]}}
      - {if: {required: [check], properties: {check: {const: drive}}}, then: {required: [drive, applies_to]}}
  check-kind:
    description: "The closed vocabulary of check kinds. Each is implemented once, by an interpreter in the engine, and the corpus writes every check of it as data."
    anyOf:
      - {$ref: "#/$defs/check-kind-component"}
      - {$ref: "#/$defs/check-kind-client"}
      - {$ref: "#/$defs/check-kind-corpus"}
  check-kind-client:
    description: "Kinds run against a front end of the engine (schemas/kinds, Client kinds): drive invokes its operations against services the harness stands up, and judges what it did and what reached them."
    enum: [drive]
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
      keys: {type: string, description: "An identity fixture, or a key fixture, of architecture/testing whose key the component is started with, in place of a generated one: written as its key file before it starts, with kdf none for an identity fixture and as the key fixture declares for a key fixture (architecture/testing, Starting a component with a fixture key)."}
      config: {type: string, description: "A configuration fixture of architecture/testing written as the component's .weblisk/config.yaml in its working directory before it starts, ${instance} in it naming that directory (architecture/testing, Starting a component with a fixture configuration)."}
      files: {type: object, propertyNames: {pattern: "^[^/]"}, additionalProperties: {type: string}, description: "Files written into the working directory before the component starts: a path relative to it, to the fixture whose value is written there (architecture/testing, Placing files). How the model configuration, an agreement or a tenant's document family reaches a component under test."}
      stand_up: {type: object, propertyNames: {$ref: "#/$defs/part-id"}, additionalProperties: {$ref: "#/$defs/stood-service"}, description: "Services the harness stands up before the component starts, by name, each of a role architecture/testing's Harness roles declares; ${stood/<name>/<field>} reads what it is reached at."}
      probe: {$ref: "#/$defs/probe-agent"}
      mock_agent: {type: object, additionalProperties: {}, description: "Responses the mock agent of architecture/testing gives, keyed by action; a value is the TaskResult or payload it answers."}
      env: {type: object, additionalProperties: {type: string}, description: "Variables added to the clean start environment."}
  stood-service:
    type: object
    required: [role]
    unevaluatedProperties: false
    description: "One service the harness stands up for a check, of a closed role (architecture/testing, Harness roles). Every one records what reaches it, which a received expectation reads."
    properties:
      role: {enum: [responder, git-remote], description: "responder: an HTTP listener answering as answers says; git-remote: a git server over ssh holding the lines lines says."}
      answers:
        type: array
        description: "responder: the first entry whose method and path match a request answers it; a request none matches is answered 404 with an ErrorResponse."
        items:
          type: object
          required: [path]
          unevaluatedProperties: false
          properties:
            method: {enum: [GET, HEAD, POST, PUT, PATCH, DELETE]}
            path: {type: string, pattern: "^/", description: "A path, where a final * matches any rest."}
            status: {type: integer, minimum: 100, maximum: 599, default: 200}
            headers: {type: object, additionalProperties: {type: string}}
            body: {description: "Any JSON value; strings may hold placeholders, ${request/<pointer>} reading the request answered."}
      tls: {type: boolean, default: false, description: "responder: served over TLS under a certificate the harness makes, its PEM at ${stood/<name>/certificate}."}
      kex: {type: array, minItems: 1, items: {type: string}, description: "git-remote: the key exchange methods it offers, and no other, by their OpenSSH names (mlkem768x25519-sha256)."}
      authorises: {type: array, items: {type: string}, description: "git-remote: the key fixtures, or identity fixtures, whose public key it admits; any key the component presents, when absent."}
      lines:
        type: object
        additionalProperties:
          type: object
          unevaluatedProperties: false
          properties:
            files: {type: object, additionalProperties: {type: string}, description: "A path in the line, to the fixture whose value it holds, all in one first commit."}
        description: "git-remote: the lines it holds before the component starts, by name; one empty main line, when absent."
  probe-agent:
    type: object
    required: [as]
    unevaluatedProperties: false
    description: "The probe (architecture/testing, The probe agent): the mock agent, started as the identity fixture as names and with its manifest, behind the component's enforcement boundaries, so a step sent from: probe is an operation that agent attempts through one of them."
    properties:
      as: {type: string, description: "An identity fixture with a manifest."}
      boundaries: {type: array, minItems: 1, items: {enum: [message, storage, external, response]}, description: "The boundaries its operations pass through; all four when absent."}
  operand:
    type: string
    description: "What an assertion or a value expectation is read over: a JSON pointer into the value it is judged against (this step's response body; a received request; a record), or a string holding placeholders, such as a capture ${name}. A pointer segment * matches every member or item, and the expectation must hold for every value it finds."
  value-expect:
    type: object
    unevaluatedProperties: false
    description: "What a JSON value must hold: a response body, a decoded value, a received request, a websocket frame."
    properties:
      has: {type: array, items: {$ref: "#/$defs/operand"}, description: "Members it holds."}
      lacks: {type: array, items: {$ref: "#/$defs/operand"}, description: "Members it does not hold."}
      only: {type: array, items: {type: string}, description: "Its top-level members are exactly these."}
      equals: {type: object, additionalProperties: {}, description: "JSON pointer to the value found there."}
      matches: {type: object, additionalProperties: {type: string}, description: "JSON pointer to a regular expression its string value matches."}
      includes: {type: object, additionalProperties: {type: array, minItems: 1}, description: "JSON pointer, which may hold *, to values that are all among those found there."}
      excludes: {type: object, additionalProperties: {type: array, minItems: 1}, description: "JSON pointer, which may hold *, to values none of those found there is."}
      length: {type: object, additionalProperties: {type: integer, minimum: 0}, description: "JSON pointer to the number of items of a list, members of an object, or bytes of a string, found there."}
  assertion-op:
    type: object
    minProperties: 1
    maxProperties: 1
    unevaluatedProperties: false
    description: "One operator of the closed set an expectation may compute over captured and answered values (Checks, Assertions). Each names its operands and what must follow."
    properties:
      decodes-as:
        type: object
        required: [value, as]
        unevaluatedProperties: false
        description: "The value decodes in the form as names, and the decoded value holds what expect says. wlt: a token's {header, claims, signature}, signature as its decoded bytes' length; base64url, hex: bytes, read as UTF-8 JSON where they are; json: a string holding one JSON value; jsonl: a text of lines, each one JSON value, as a list; weblisk-key-v1: a key file's {magic, algorithm, kdf, kdf_params, ciphertext}, kdf_params decoded; fixed-form: a statement's {prefix, fields}."
        properties:
          value: {$ref: "#/$defs/operand"}
          as: {enum: [wlt, base64url, hex, json, jsonl, weblisk-key-v1, fixed-form]}
          expect: {$ref: "#/$defs/value-expect"}
          capture: {$ref: "#/$defs/part-id", description: "A name for the decoded value, for later placeholders."}
      digest-of:
        type: object
        required: [value, equals]
        unevaluatedProperties: false
        description: "The SHA-256 of value, taken in form, written in encoding, equals equals (or differs from it, where differs is true)."
        properties:
          value: {$ref: "#/$defs/operand"}
          form: {enum: [bytes, jcs, line], default: bytes, description: "bytes: the value's exact bytes, as stored or answered; jcs: the RFC 8785 canonical form of the JSON value, its without members left out; line: one stored line, without its line ending."}
          without: {type: array, items: {type: string}, description: "jcs: top-level members left out first."}
          encoding: {enum: [hex, sha256-hex, base64url], default: sha256-hex, description: "hex: 64 lowercase hex; sha256-hex: sha256: and the hex, as patterns/content-identity writes a digest; base64url."}
          equals: {$ref: "#/$defs/operand"}
          differs: {type: boolean, default: false}
      verifies-under:
        type: object
        required: [signature, key]
        unevaluatedProperties: false
        description: "The signature verifies under key, as protocol/identity's Verify Signature does, over the bytes form builds (or fails to, where verifies is false)."
        properties:
          signature: {$ref: "#/$defs/operand"}
          key: {$ref: "#/$defs/operand", description: "A base64url ML-DSA-65 public key: ${self/public_key}, ${fixture/<name>/public_key}, or a value answered or captured."}
          form: {enum: [jcs, bytes, fixed-form], default: jcs, description: "jcs: Sign JSON over the canonical form of over, its without members left out; bytes: over's exact bytes; fixed-form: the statement prefix and fields build (protocol/identity, Fixed-Form Statements)."}
          over: {$ref: "#/$defs/operand", description: "jcs and bytes: what was signed; the whole value judged, when absent."}
          without: {type: array, items: {type: string}}
          members: {type: array, minItems: 1, items: {type: string}, description: "jcs: the object of only these members of over."}
          prefix: {type: string, pattern: "^weblisk/", description: "fixed-form: a prefix the registry lists."}
          fields: {type: array, items: {$ref: "#/$defs/statement-field"}, description: "fixed-form: each field, in order."}
          encoding: {enum: [base64url, hex], default: base64url, description: "How signature is written."}
          verifies: {type: boolean, default: true}
      chain-links:
        type: object
        required: [lines]
        unevaluatedProperties: false
        description: "A hash chain holds: the first line's seq is 1 and its link is genesis; each later line's seq is one more than the one before it, and its link is the digest of that line's stored bytes, as architecture/storage's Verifying a sealed log step 1 reads one."
        properties:
          lines: {$ref: "#/$defs/operand", description: "A list of stored lines, or a text split at each line ending, exactly as stored."}
          seq: {$ref: "#/$defs/json-pointer", default: /seq}
          link: {$ref: "#/$defs/json-pointer", default: /previous_digest}
          genesis: {type: string, default: "0000000000000000000000000000000000000000000000000000000000000000"}
          encoding: {enum: [hex, sha256-hex], default: hex}
          holds: {type: boolean, default: true, description: "false: the chain breaks, at the line at breaks where it is given."}
          breaks: {type: integer, minimum: 1}
  statement-field:
    description: "One field of a fixed-form statement: a string, which may hold placeholders and ${body/<pointer>}, the body being sent or judged; or a digest computed as digest-of computes one, with no equals."
    oneOf:
      - {type: string}
      - type: object
        required: [digest-of]
        unevaluatedProperties: false
        properties:
          digest-of:
            type: object
            required: [value]
            unevaluatedProperties: false
            properties:
              value: {$ref: "#/$defs/operand"}
              form: {enum: [bytes, jcs, line], default: bytes}
              without: {type: array, items: {type: string}}
              encoding: {enum: [hex, sha256-hex, base64url], default: sha256-hex}
  signing:
    type: object
    required: [into]
    unevaluatedProperties: false
    description: "Sign part of the body, as protocol/identity signs: with the as identity's key, or key's, under Sign JSON over the canonical form of the value at over, or over the fixed-form statement prefix and fields build; encoded as the field at into declares."
    properties:
      over: {$ref: "#/$defs/json-pointer"}
      members: {type: array, minItems: 1, items: {type: string}, description: "Sign the object of only these members of the value at over."}
      without: {type: array, items: {type: string}, description: "Top-level members of the value at over left out before it is canonicalised; into is left out always."}
      form: {enum: [jcs, fixed-form], default: jcs}
      prefix: {type: string, pattern: "^weblisk/", description: "fixed-form: a prefix the Fixed-Form Statements registry lists."}
      fields: {type: array, items: {$ref: "#/$defs/statement-field"}}
      into: {$ref: "#/$defs/json-pointer"}
      encoding: {enum: [base64url, hex], default: base64url}
      key: {type: string, description: "An identity fixture, or a key fixture, whose key signs in place of the as identity's; so two signings of one body, one by the current key and one by the next, prove possession of both."}
      with: {enum: [own, other-key, other-bytes], default: own, description: "own key over those bytes; another fixture's key; or the own key over other bytes."}
      timestamp: {$ref: "#/$defs/json-pointer", description: "Where the signing instant is written."}
      age: {$ref: "#/$defs/duration-literal", description: "How long before now the timestamp says; 0s when absent."}
    allOf:
      - {if: {properties: {form: {const: fixed-form}}, required: [form]}, then: {required: [prefix, fields]}, else: {required: [over]}}
  token-alter:
    type: object
    unevaluatedProperties: false
    minProperties: 1
    description: "The minted token changed before it is sent, as architecture/testing's test_tokens says a token from another is: claims replaced (null removes one), iat and exp moved, its signature put in one of test_tokens' signature_forms. So an expired pass is token pass with exp -60, a work pass to another component is token work with claims aud another's fingerprint, and an operator token with no cid is claims cid null."
    properties:
      claims: {type: object, additionalProperties: {}}
      iat: {type: integer, description: "Seconds from the instant of minting, written into the claims as a NumericDate."}
      exp: {type: integer, description: "Seconds from the instant of minting, written into the claims as a NumericDate."}
      signature: {type: string, description: "A form test_tokens' signature_forms declares."}
  exchange-request:
    type: object
    unevaluatedProperties: false
    anyOf: [{required: [method]}, {required: [endpoint]}, {required: [replay]}, {required: [probe]}]
    properties:
      method: {enum: [GET, HEAD, POST, PUT, PATCH, DELETE]}
      endpoint: {const: each, description: "The method and path of each endpoint the check's for_each selects, its path parameters filled with conformance-probe."}
      replay: {$ref: "#/$defs/part-id", description: "Send again the exact bytes an earlier step with this id sent."}
      path: {type: string, pattern: "^/", description: "The path as sent; a placeholder ${name} is filled from an earlier capture or a fixture."}
      operation: {$ref: "#/$defs/ref", description: "An operation a serves block or Endpoints table declares; its method and path, in place of path."}
      listener: {enum: [public, admin], default: public}
      token: {enum: [none, own, expired, bad-signature, wrong-type, channel-self, channel-other, pass, pass-other, operator, work, captured], default: none, description: "The bearer token. none: no token; captured: the value an earlier step captured as token; every other value is minted as architecture/testing's test_tokens block declares it (Test tokens as data): own, a registration token for the as identity; expired, own past its exp; bad-signature, own with its signature broken; wrong-type, own carrying a type the route does not take; channel-self and channel-other, a channel token to the component under test or to another target; pass and pass-other, a person's pass for the as identity addressed to the component under test or to another component; operator, the as identity's operator token; work, a work pass addressed to the component under test on the as identity's authority."}
      token_alter: {$ref: "#/$defs/token-alter"}
      bearer: {type: string, description: "The Authorization bearer, in place of the token token names: none, or the name of an earlier capture. ${token} still reads the token token names, so a body can carry one token while another is the bearer."}
      headers: {type: object, additionalProperties: {type: string}}
      body: {description: "Any JSON value; strings may hold placeholders."}
      body_bytes: {type: integer, minimum: 0, description: "A body of this many bytes, in place of body."}
      sign:
        description: "One signing, or several applied in order, each into its own member: a key change carries the current key's signature and the next key's over one body."
        oneOf:
          - {$ref: "#/$defs/signing"}
          - {type: array, minItems: 2, items: {$ref: "#/$defs/signing"}}
      websocket:
        type: object
        unevaluatedProperties: false
        description: "Open the path as a WebSocket (RFC 6455), with the step's token as the upgrade's bearer, send each of send as one text frame, and read frames until receive have arrived or within has passed; expect.frames judges them."
        properties:
          send: {type: array, items: {}}
          receive: {type: integer, minimum: 0, default: 1}
          within: {$ref: "#/$defs/duration-literal"}
      probe:
        type: object
        required: [boundary, input]
        unevaluatedProperties: false
        description: "Sent from the probe agent (check-start probe): the operation it attempts through boundary, as that boundary's interface in architecture/enforcement takes it; the response is that interface's output, as JSON."
        properties:
          boundary: {enum: [message, storage, external, response]}
          input: {type: object, additionalProperties: {}}
  received-expect:
    type: object
    required: [service]
    unevaluatedProperties: false
    description: "What reached a service the harness runs, judged after the step: the mock orchestrator, the mock agent, or a stood service. Each received request is the value {method, path, headers, body}, body parsed where it is JSON; a git-remote's are its pushes, {line, from, to, files}."
    properties:
      service: {type: string, description: "orchestrator (the mock), mock-agent, or a stood service's name."}
      method: {enum: [GET, HEAD, POST, PUT, PATCH, DELETE]}
      path: {type: string, pattern: "^/"}
      count: {type: integer, minimum: 0, description: "Exactly this many matching requests reached it; at least one when absent. 0 proves nothing was forwarded, exchanged or sent."}
      expect: {$ref: "#/$defs/value-expect", description: "Each matching request holds this."}
      within: {$ref: "#/$defs/duration-literal", description: "How long after the step's answer requests are counted; 2s when absent."}
  exchange-expect:
    type: object
    unevaluatedProperties: false
    properties:
      status: {oneOf: [{type: integer}, {type: array, minItems: 1, items: {type: integer}}]}
      status_not: {type: array, minItems: 1, items: {type: integer}}
      code: {type: string, pattern: "^[A-Z][A-Z0-9_]*$", description: "The registered error code the body carries."}
      json: {type: boolean, description: "The body is JSON."}
      empty: {type: boolean, description: "The body is zero bytes."}
      has: {type: array, items: {$ref: "#/$defs/json-pointer"}, description: "Members the body holds."}
      lacks: {type: array, items: {$ref: "#/$defs/json-pointer"}, description: "Members the body does not hold."}
      only: {type: array, items: {type: string}, description: "The body's top-level members are exactly these."}
      equals: {type: object, additionalProperties: {}, description: "JSON pointer to the value found there."}
      matches: {type: object, additionalProperties: {type: string}, description: "JSON pointer to a regular expression its string value matches."}
      includes: {type: object, additionalProperties: {type: array, minItems: 1}, description: "As value-expect's."}
      excludes: {type: object, additionalProperties: {type: array, minItems: 1}, description: "As value-expect's."}
      mentions: {type: array, items: {type: string}, description: "The error member's text holds at least one of these words."}
      headers: {type: object, additionalProperties: {type: string}, description: "A response header, by name in any case, to a regular expression its value matches (WWW-Authenticate, Allow, ETag, Retry-After, Set-Cookie). A header sent more than once matches when one of its values does."}
      headers_lack: {type: array, minItems: 1, items: {type: string}, description: "Response headers the answer does not carry."}
      frames: {type: array, items: {$ref: "#/$defs/value-expect"}, description: "websocket: the frames received, in order, each a JSON value holding what its entry says."}
      assert: {type: array, minItems: 1, items: {$ref: "#/$defs/assertion-op"}, description: "Operators computed over the answer and earlier captures, each of which must hold."}
      received: {type: array, minItems: 1, items: {$ref: "#/$defs/received-expect"}}
  exchange-step:
    type: object
    required: [request, expect]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      as: {type: string, description: "An identity fixture of architecture/testing, or anonymous."}
      from: {const: probe, description: "Sent by the probe agent through the boundary request.probe names, in place of by the harness."}
      instance: {type: string, description: "The instance it is sent to, in a topology check; or a component started beside it, by name."}
      repeat: {type: integer, minimum: 1, description: "Sent this many times at once."}
      request: {$ref: "#/$defs/exchange-request"}
      expect: {$ref: "#/$defs/exchange-expect"}
      capture:
        type: object
        additionalProperties:
          anyOf:
            - {$ref: "#/$defs/json-pointer"}
            - {type: string, pattern: "^@(status|address|body|header/[A-Za-z0-9-]+)$"}
        description: "A name for a value of the response, for later steps' placeholders: by JSON pointer into the body; @status; @body, its exact bytes; @header/<name>; or @address, the address the request reached, as the harness dialled it."
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
      manifest: {$ref: "#/$defs/value-expect", description: "What the manifest the orchestrator's directory lists for the component holds, once it is listed: the manifest it registered."}
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
        required: [source]
        anyOf: [{required: [match]}, {required: [matches]}, {required: [lacks_text]}]
        unevaluatedProperties: false
        properties:
          source: {enum: [audit, log, event, trace]}
          read: {$ref: "#/$defs/exchange-request", description: "How the record is read where it is served (audit); a log is read from the process's standard output."}
          match: {type: object, additionalProperties: {}, description: "JSON pointer, in one record, to the value it must hold."}
          matches: {type: object, additionalProperties: {type: string}, description: "JSON pointer, in the same record, to a regular expression its string value matches."}
          count: {type: integer, minimum: 0, description: "Exactly this many records match; at least one when absent."}
          lacks_text: {type: array, minItems: 1, items: {type: string}, description: "No record's text, as written, holds any of these, each a string that may be one placeholder (a captured token, a passphrase): searched over every record of source, matched or not. ${token} here is the token the last step sent."}
          within: {$ref: "#/$defs/duration-literal"}
  topology-act:
    type: object
    required: [act]
    unevaluatedProperties: false
    description: "One act, run in the order acts gives them (Checks, Acts). Paths are relative to the instance's working directory."
    properties:
      act: {enum: [start, stop, restart, kill, wait, send, make-unreadable, alter, remove, place, read, rotate-key, remote]}
      instance: {type: string}
      store: {type: string, description: "make-unreadable, alter, remove: a store the instance's blueprint declares, by name, at the path its configuration gives it."}
      path: {type: string, pattern: "^[^/]", description: "make-unreadable, alter, remove, place, read: a file or directory, such as .weblisk/keys/content.key."}
      alter: {enum: [flip-byte, truncate, append-line, drop-line, swap-lines], description: "alter: flip-byte changes one byte of the last line; truncate removes its last byte; append-line adds a line copied from the one before; drop-line removes line at; swap-lines exchanges line at and the one after."}
      at: {type: integer, minimum: 1, description: "alter: the number of the line acted on; the last when absent."}
      fixture: {type: string, description: "place: the fixture written at path, out of band; rotate-key: the key fixture the instance's key rotates to."}
      capture: {$ref: "#/$defs/part-id", description: "read: a name for the file's exact text, for later placeholders and assert."}
      mode: {type: string, pattern: "^0[0-7]{3}$", description: "read: the file's permission bits must be these."}
      assert: {type: array, minItems: 1, items: {$ref: "#/$defs/assertion-op"}, description: "read: operators over what was read, as ${<capture>}."}
      step: {$ref: "#/$defs/exchange-step", description: "send: the step sent at this point in the acts."}
      remote: {type: string, description: "remote: a stood git-remote."}
      line: {type: string, description: "remote: the line acted on; main when absent."}
      change: {enum: [commit, move-back, drop-tip], description: "remote: commit adds a commit by another party holding files; move-back points the line at its tip's parent; drop-tip rewrites the line without its tip, as a force-push would."}
      files: {type: object, additionalProperties: {type: string}, description: "remote commit: a path in the line, to the fixture it holds."}
      for: {$ref: "#/$defs/duration-literal"}
      expect: {enum: [ready, live, exits, refuses-start], description: "What the act must lead to."}
      within: {$ref: "#/$defs/duration-literal"}
    allOf:
      - {if: {properties: {act: {const: send}}}, then: {required: [step]}}
      - {if: {properties: {act: {const: alter}}}, then: {required: [alter]}}
      - {if: {properties: {act: {const: place}}}, then: {required: [path, fixture]}}
      - {if: {properties: {act: {const: read}}}, then: {required: [path, capture]}}
      - {if: {properties: {act: {const: rotate-key}}}, then: {required: [instance, fixture]}}
      - {if: {properties: {act: {const: remote}}}, then: {required: [remote, change]}}
  check-topology:
    type: object
    required: [instances, acts]
    unevaluatedProperties: false
    properties:
      start: {$ref: "#/$defs/check-start", description: "How every instance is started, and what the harness stands up for them."}
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
            keys: {type: string, description: "As check-start's, for this instance."}
            config: {type: string, description: "As check-start's, for this instance."}
            env: {type: object, additionalProperties: {type: string}}
      acts: {type: array, minItems: 1, items: {$ref: "#/$defs/topology-act"}}
      steps: {type: array, items: {$ref: "#/$defs/exchange-step"}, description: "Sent after every act; a step that must come between two acts is an act send."}
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
              excludes: {type: array, minItems: 1, items: {type: string}, description: "No captured value is one of these."}
              subset_of: {$ref: "#/$defs/part-id", description: "Every captured value is one another query captures."}
  check-drive:
    type: object
    required: [invoke]
    unevaluatedProperties: false
    description: "A front end driven through its operations (schemas/kinds, Client kinds; architecture/engine, Parity: the CLI and Studio are interchangeable), against services the harness stands up in place of a hub, a gateway or a signer."
    properties:
      stand_up: {type: object, propertyNames: {$ref: "#/$defs/part-id"}, additionalProperties: {$ref: "#/$defs/stood-service"}}
      files: {type: object, additionalProperties: {type: string}, description: "Files written into the front end's working directory first, as check-start's."}
      invoke:
        type: array
        minItems: 1
        items:
          type: object
          required: [operation, expect]
          unevaluatedProperties: false
          properties:
            id: {$ref: "#/$defs/part-id"}
            operation: {type: string, description: "An operation of the engine's catalogue, as a front end's manifest names it (tenant new, operator rotate)."}
            parameters: {type: object, additionalProperties: {}, description: "Its parameters, by the names the manifest gives; strings may hold placeholders."}
            as: {type: string, description: "The identity fixture the front end holds as its operator, written where its blueprint keeps one."}
            expect:
              type: object
              unevaluatedProperties: false
              properties:
                outcome: {enum: [ok, refused, failed]}
                code: {type: string, pattern: "^[A-Z][A-Z0-9_]*$"}
                result: {$ref: "#/$defs/value-expect", description: "The operation's result, as the envelope the manifest names carries it."}
                assert: {type: array, minItems: 1, items: {$ref: "#/$defs/assertion-op"}}
                received: {type: array, minItems: 1, items: {$ref: "#/$defs/received-expect"}}
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
  - id: check-vocabulary-held
    covers: [check-vocabulary-closed, check-proves-whole-criterion]
    check: vectors-agree
    assertion: Every example of vectors/check-kinds/valid.yaml, one for each kind and each construct the vocabulary declares, passes checks/check-kinds.py, and each case of invalid.yaml, among them an undeclared operator, act, harness role, signature form and client kind, and a declared check whose assertion leaves part of what it covers unsettled, is reported with exactly its one fault.
  - id: scalars-in-one-place
    covers: [type-vocabulary-closed]
    check: walk-validates
    assertion: The type-expr format accepts exactly the values of the definition `scalar` and their compositions, so removing `date` from `scalar` makes a field of type date fail block-schema.
```
