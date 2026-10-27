---
family: schemas/family@1
version: 1.0.0
kind: specification
noun: mapping
capabilities: [author, versioned, publishable]
---
# Schema: Mappings

A mapping says how a neutral blueprint becomes something on one target: how a
declared type is spelled in a language, which runtime facility answers a
capability a blueprint requires, how a framework lays out a page, or which
generator writes an interface description. Every language, platform, framework
and interface binding is a file of this one family, and they differ only in
which concept classes they own.

A mapping is written as **rules**. Each rule answers one concept, carries its
own id, and is cited by what a build made with it, so changing one rule stales
exactly the outputs made with that rule and nothing a prose edit touches. The
concept names a rule answers are data, in [`schemas/concepts`](concepts.md);
the classes they belong to, and which axis owns each, are closed and below.

There are four axes and no others: language, platform, framework and
interface. HTTP, as [`protocol/spec`](../protocol/spec.md) specifies it, is
Weblisk's one transport, so no axis or rule selects another (D7).

## Requirements

```yaml
requirements:
  - id: file-names-family
    level: must
    text: >-
      A mapping file names this family in its header as `family:
      schemas/mapping@1`. This declaration has no `match`: the language,
      platform and framework files written before it are read as their own
      families until each is rewritten into rules, and one path covered by
      two families would be ambiguous.
  - id: one-axis-per-file
    level: must
    text: >-
      A mapping file declares one `axis` and the one name it `provides` on
      that axis. A platform states the languages it accepts in
      `accepts_languages`, and a framework the platforms it runs on in
      `requires_platforms`; a target pairing them otherwise is refused before
      any model call.
  - id: classes-closed
    level: must
    text: >-
      A concept class is one of the classes this file's `classes` block
      names, and a tool implements exactly those. A concept is `<class>/<name>`,
      where <name> is an entry schemas/concepts declares under that class.
      Adding a class is a new major of this file; adding a concept is a new
      entry in schemas/concepts.
  - id: one-owning-axis
    level: must
    text: >-
      Every concept has exactly one owning axis: its class's `owner`, or,
      where the class's owner is `per-concept`, the `owner` its entry in
      schemas/concepts names. A rule on a concept its file's axis does not
      own carries `refines`, naming the rule of the owning axis it narrows.
      Two rules on one concept in one target without a `refines` link
      between them are refused; nothing chooses between them by order.
  - id: rule-form-by-class
    level: must
    text: >-
      A rule that answers its concept carries exactly one of `produce`,
      `evaluate` or `extract`, the one its class's `form` names, and a class
      whose `verdict` is `required` also gives each rule a verdict. A rule
      whose verdict is UNFILLED or UNAVAILABLE carries a `reason` and none
      of the three.
  - id: unfilled-is-stated
    level: must
    text: >-
      A concept a mapping cannot answer is a rule with verdict UNFILLED and
      the reason, never an omission or an approximation. A generation for a
      target whose owning mapping leaves a concept the build needs UNFILLED,
      or answers it with no rule at all, is refused before any model call,
      naming the concept and the mapping.
  - id: coverage-report
    level: must
    text: >-
      A mapping's coverage report lists every class this file's `classes`
      block names, in that order, each with its owning axes, the ids of the
      file's rules in it, and a status: `filled` when at least one of those
      rules has a verdict other than UNFILLED, and `UNFILLED` otherwise, so a
      class the file says nothing about is listed as UNFILLED and never left
      out. A class whose only rules are UNAVAILABLE is `filled`:
      UNAVAILABLE is a stated answer, that the concept cannot exist on the
      target, not a missing one. The report is the `coverage` definition
      below.
  - id: one-verdict-vocabulary
    level: must
    text: >-
      A rule's verdict is one of PLATFORM, ADAPTER, IMPLEMENT, UNAVAILABLE and
      UNFILLED, with the meanings this file's verdict table gives, on every
      axis.
  - id: verify-by-vector
    level: must
    text: >-
      A rule's `verify` names vectors its output must satisfy, each a path
      under vectors/ and, after `#`, the key of one entry of that file. A
      vector that is named and fails, or that names a file or key that does
      not exist, fails the rule.
  - id: subject-facility-declared
    level: must
    text: >-
      A specification blueprint whose subject is a platform facility, such as
      running operating-system processes, declares it in its header as
      `subject_facility`, naming the concept and stating what holds where the
      facility is absent. The neutrality check permits in that blueprint the
      vocabulary the mappings give for that concept and no other, and a
      blueprint without the declaration has no exemption.
  - id: neutral-vocabulary-derived
    level: must
    text: >-
      The vocabulary a specification blueprint must not name is derived from
      the mappings: every `provides` value, every `reserved_terms` entry, and
      every `spelling`, `package` and first `argv` element a rule produces.
      Adding a mapping adds its vocabulary with no change to any tool.
```

## Header

```yaml
header:
  schema:
    type: object
    required: [family, version, axis, provides]
    unevaluatedProperties: false
    properties:
      family:   {const: schemas/mapping@1}
      version:  {$ref: "schemas/blocks#/$defs/version"}
      axis:     {$ref: "#/$defs/axis"}
      provides: {$ref: "#/$defs/target-name"}
      accepts_languages:
        type: array
        minItems: 1
        items: {$ref: "#/$defs/target-name"}
        description: "On a platform: the languages, by what their mappings provide, a component on it may be written in."
      requires_platforms:
        type: array
        minItems: 1
        items: {$ref: "#/$defs/target-name"}
        description: "On a framework: the platforms, by what their mappings provide, it runs on. Not `requires`, which names the blueprints a file reads."
      reserved_terms:
        type: array
        items: {type: string, minLength: 1}
        description: "Words that belong to this target and to no neutral blueprint, beyond what its rules already spell."
      requires: {type: array, items: {$ref: "schemas/blocks#/$defs/requires-entry"}}
      retired:  {$ref: "schemas/blocks#/$defs/retired"}
    allOf:
      - if: {required: [accepts_languages]}
        then: {properties: {axis: {const: platform}}}
      - if: {required: [requires_platforms]}
        then: {properties: {axis: {const: framework}}}
  uses:
    requires: {use: depends, resolves: specification, send: always}
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1},
       prose: required, content: {max_paragraphs: 4}, use: navigates}
    - {slot: rules, heading: Rules, required: true, count: {min: 1, max: 1},
       blocks: [{type: rules, count: {min: 1}}], use: binds}
    - {slot: verifies, heading: Verification, required: false, count: {max: 1},
       blocks: [{type: verifies, count: {min: 1, max: 1}}], prose: forbidden,
       use: verifies, produces: [code.test]}
```

The Rules slot may hold several `rules` blocks, each under its own deeper
heading, with the prose that explains them between: a rule's reason is
explanation and never part of the rule, so rewording it changes no rule's
digest. A level-2 heading the slots do not name is explanation too.

## Classes

```yaml
# Read by tools. The closed set of concept classes, each with its owning axis
# and the form of the rule that answers one of its concepts.
classes:
  type:               {owner: language, form: produce, binds: "a field's type, in schemas/blocks' type vocabulary"}
  identifier:         {owner: language, form: produce, binds: "a declared key, type name, operation or package, spelled"}
  identity-primitive: {owner: language, form: produce, binds: "a primitive protocol/identity or protocol/types requires"}
  check:              {owner: language, form: evaluate, binds: "a check a blueprint declares, by its name"}
  symbol:             {owner: language, form: extract, binds: "the declarations in a generated file: names, kinds and byte spans"}
  test:               {owner: language, form: produce, binds: "a verifies entry, or a published vector, as a test"}
  lifecycle:          {owner: per-concept, form: produce, binds: "how a component is built, run and deployed, and the tool that does it"}
  component:          {owner: per-concept, form: produce, binds: "a component kind's layout, entry point and module"}
  service:            {owner: platform, form: produce, verdict: required, binds: "a capability a blueprint requires"}
  storage:            {owner: platform, form: produce, verdict: required, binds: "a store architecture/storage specifies"}
  ui-unit:            {owner: framework, form: produce, binds: "a page, component, island or asset a framework builds"}
  interface:          {owner: interface, form: produce, binds: "a description of an interface, written by a generator"}
```

A language owns what is true of the language wherever it runs; a platform
owns what the runtime offers and how a component is laid out and started on
it. Where one class holds both, as building and running a component do, its
owner is `per-concept` and each concept in [`schemas/concepts`](concepts.md)
names its own: `lifecycle/build` is the language's, `lifecycle/deploy` the
platform's. Ownership is still one axis per concept, so two answers to one
concept are always a refusal or a declared refinement, never a precedence.

A Go module or a Rust crate is the language's however a platform runs it,
which is why `component/module` is the language's while `component/layout` is
the platform's.

## Verdicts

The one verdict vocabulary, on every axis. It is the one platform mappings
have used since their Service Mapping tables, and a rule on any axis may use
it.

| Verdict | Meaning |
|---|---|
| `PLATFORM` | The target provides the concept. A generator MUST NOT implement it |
| `ADAPTER` | The target provides the mechanism; the component supplies the blueprint's contract over it |
| `IMPLEMENT` | The target provides nothing. Build it as the blueprint specifies |
| `UNAVAILABLE` | The concept cannot exist on this target. A blueprint depending on it states so, by `subject_facility` where the facility is its subject |
| `UNFILLED` | Nobody has written this rule yet. It is a stated gap, and a build that needs it is refused |

<!-- wl:explains unfilled-is-stated -->
A capability or primitive the target provides and the mapping omits is
indistinguishable from one it does not, so an omission would let a generator
guess. An UNFILLED rule turns the guess into a refusal that names what is
missing, and a coverage report that lists every class makes the omission
itself visible: a class the file says nothing about is UNFILLED, not absent.

## Coverage

A coverage report is produced from one mapping file and the two closed
lists, never from a build. It answers "what does this file say", and says
nothing about whether a target needs a class: whether a target's mappings
together answer every concept its blueprints use is the composition's
question, asked over the target's owning mappings when a build is planned.

[`vectors/mapping/`](../vectors/mapping/README.md) holds a language mapping
with rules in nine of the twelve classes and the coverage report it must
produce, naming exactly the other three as UNFILLED;
[`checks/mapping-coverage.py`](../checks/mapping-coverage.py) produces the
report the same way, and `v2-cli-mapping` is bound by the vector.

## Subject facility

`subject_facility` is the declared form of [`schemas/common`](common.md#platform-neutrality)'
exception for a blueprint whose subject is a platform facility. It is a header
field of a specification blueprint, defined here because what it permits is
read from the mappings: the blueprint may name the vocabulary the mappings
give for that one concept, and the statement it carries is the one a generator
for a target whose mapping answers the concept UNAVAILABLE reads. Each family
that admits it adds it to its header schema as
`{$ref: "schemas/mapping#/$defs/subject-facility"}`.

## Definitions

```yaml
defs:
  axis: {enum: [language, platform, framework, interface]}
  target-name: {type: string, pattern: "^[a-z][a-z0-9-]*$"}
  concept: {type: string, pattern: "^[a-z][a-z-]*/[a-z0-9][a-z0-9-]*$", description: "<class>/<name>: a class of this file's classes block and a name schemas/concepts declares under it."}
  verdict: {enum: [PLATFORM, ADAPTER, IMPLEMENT, UNAVAILABLE, UNFILLED]}
  vector-ref: {type: string, pattern: "^vectors/[A-Za-z0-9_./-]+\\.json#[a-z0-9][a-z0-9-]*$"}
  command:
    type: object
    description: "How a rule runs: a named evaluator a tool ships, or a command it runs, never both."
    unevaluatedProperties: false
    properties:
      evaluator: {type: string, pattern: "^[a-z0-9-]+/[a-z0-9-]+$"}
      argv: {type: array, minItems: 1, items: {type: string}}
      parse: {enum: [exit-status, sarif, json-lines]}
    oneOf:
      - {required: [evaluator]}
      - {required: [argv, parse]}
  produce:
    type: object
    required: [via]
    unevaluatedProperties: false
    properties:
      via: {enum: [model, generator]}
      generator: {type: string, description: "With via generator: the deterministic generator that writes the output."}
      spelling: {type: string, description: "How the concept is written in the target."}
      package: {type: string, description: "The module, package or crate that supplies it, exactly as it is imported."}
      source: {enum: [stdlib, dependency, runtime], description: "Where what package names comes from."}
      encode: {type: string, description: "The wire encoding, where it is not the spelling."}
      case: {enum: [PascalCase, camelCase, snake_case, kebab-case, SCREAMING_SNAKE_CASE]}
      template: {type: string, description: "A spelling built from the declared name, such as Path{Operation}."}
      argv: {type: array, minItems: 1, items: {type: string}}
      dirs: {type: array, minItems: 1, items: {type: string}}
      entry: {type: string}
      version: {type: string, description: "The least version of the tool or package."}
      text: {type: string, description: "What a model is told, where no field above says it."}
    if: {properties: {via: {const: generator}}}
    then: {required: [generator]}
  rule:
    type: object
    required: [id, concept]
    unevaluatedProperties: false
    properties:
      id: {$ref: "schemas/blocks#/$defs/part-id"}
      concept: {$ref: "#/$defs/concept"}
      verdict: {$ref: "#/$defs/verdict"}
      produce: {$ref: "#/$defs/produce"}
      evaluate: {$ref: "#/$defs/command"}
      extract: {$ref: "#/$defs/command"}
      refines: {$ref: "schemas/blocks#/$defs/ref", description: "The rule of the owning axis this one narrows."}
      verify: {type: array, minItems: 1, items: {$ref: "#/$defs/vector-ref"}}
      reason: {type: string, minLength: 1, description: "Why the concept is UNFILLED or UNAVAILABLE here."}
    if: {required: [verdict], properties: {verdict: {enum: [UNFILLED, UNAVAILABLE]}}}
    then:
      required: [reason]
      not: {anyOf: [{required: [produce]}, {required: [evaluate]}, {required: [extract]}]}
    else:
      oneOf:
        - {required: [produce]}
        - {required: [evaluate]}
        - {required: [extract]}
  subject-facility:
    type: object
    required: [concept, unavailable]
    unevaluatedProperties: false
    properties:
      concept: {$ref: "#/$defs/concept"}
      unavailable: {type: string, minLength: 1, description: "What holds on a target whose mapping answers the concept UNAVAILABLE."}
  coverage:
    type: object
    required: [file, axis, provides, classes]
    unevaluatedProperties: false
    properties:
      file: {type: string}
      axis: {$ref: "#/$defs/axis"}
      provides: {$ref: "#/$defs/target-name"}
      classes:
        type: array
        description: "Every class, in the order the classes block names them."
        items:
          type: object
          required: [class, owners, status, rules]
          unevaluatedProperties: false
          properties:
            class: {type: string}
            owners: {type: array, minItems: 1, items: {$ref: "#/$defs/axis"}}
            status: {enum: [filled, UNFILLED]}
            rules: {type: array, items: {$ref: "schemas/blocks#/$defs/part-id"}}
```

## Verification

```yaml
verifies:
  - id: coverage-names-every-class
    covers: [coverage-report, classes-closed, unfilled-is-stated]
    check: vectors-agree
    assertion: The coverage report of vectors/mapping/fake-language.md equals vectors/mapping/fake-language.coverage.json, which lists all twelve classes and names exactly service, ui-unit and interface as UNFILLED; a copy with one more class's rules removed names four.
  - id: refinement-required
    covers: [one-owning-axis]
    check: vectors-agree
    assertion: A copy of the fixture whose storage rule drops its refines is refused, naming that rule and the platform that owns its concept.
  - id: rule-form-checked
    covers: [rule-form-by-class, one-verdict-vocabulary]
    check: vectors-agree
    assertion: A check rule that carries produce instead of evaluate, and an UNFILLED rule with no reason, are each refused, naming the rule.
  - id: concepts-declared
    covers: [classes-closed, one-owning-axis]
    check: vectors-agree
    assertion: Every concept schemas/concepts declares is in a class this file names, carries an owner exactly when its class's owner is per-concept, and every rule in the fixture names a declared concept.
  - id: verify-names-resolve
    covers: [verify-by-vector]
    check: vectors-agree
    assertion: Every verify entry in the fixture names a vector file and an entry key that exist, and a copy naming a missing key is refused.
  - id: one-axis-checked
    covers: [one-axis-per-file, file-names-family]
    check: walk-validates
    assertion: A language mapping that declares accepts_languages fails header.schema.
  - id: neutral-vocabulary
    covers: [neutral-vocabulary-derived, subject-facility-declared]
    check: neutrality-derived
    assertion: Adding a mapping with a reserved term makes that term a finding in a specification blueprint that names it, and not in one whose subject_facility is the concept the term answers.
```
