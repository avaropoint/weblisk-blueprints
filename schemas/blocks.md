---
family: family@1
version: 1.0.0
noun: block
---
# Schema: Blocks

The block catalogue: every typed block a slot may hold, keyed by the root key
that names it, with the schema its value must satisfy, how its entries are
identified, and the closed vocabulary a declared type's fields are written in.

A slot names the blocks it holds ([`schemas/family`](family.md#the-grammar-keywords));
this file says what each one is. It declares no files of its own: it is a
library of definitions, cited as `blocks#/$defs/<name>`.

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
      gives in `entries: {by: <field>}` otherwise. Each entry is a part id in
      the ref family the catalogue names, and two entries of one block with
      one id are refused.
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
      accepts, and no other. An enum field lists its values.
  - id: legacy-type-spellings
    level: must
    text: >-
      In grammar 1 a spelling listed under "Spellings read in report mode" is
      rewritten in the block's projected value to the type it names, before
      the schema is applied, and reported as legacy-spelling. Any other
      spelling fails the schema. Once migration is done the listed spellings
      are refused too.
```

## Types

A field's `type` is one of these, or built from them:

```
type-expr = scalar / "list<" type-expr ">" / "map<" type-expr ">" / "ref:" ref
scalar    = "string" / "integer" / "number" / "boolean"
          / "timestamp" / "date" / "duration" / "uuid" / "bytes"
          / "enum" / "object" / "any"
```

`ref` is [`schemas/names`](names.md#the-grammar)' ref, naming a declared type.
A `map` is keyed by string. An `object` is a JSON object whose shape is not
declared, and `any` is any JSON value; both say that nothing checks the value,
so a field that has a shape names a type instead.

The wire form of `integer`, `timestamp`, `duration`, `uuid` and `bytes` is
[`protocol/types`](../protocol/types.md#conventions)' to state. `date` is a
calendar date with no time or zone, written as RFC 3339's `full-date`
(`2026-10-15`); it exists because a review date, an expiry or a due date is
not an instant, and writing one as a timestamp invents a time of day and a
zone nobody chose.

### Spellings read in report mode

Spellings that files written before grammar 1 use. A walk in report mode reads
each as the type it names and reports it; the migration rewrites it.

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
| `[]T`, `T[]`, `list<T>` | `list<T>` |
| `map` | `map<any>` |
| `map[string]T` | `map<T>` |
| `enum(a, b)` | `enum` with `values: [a, b]` |
| a bare type name `T` | `ref:T` |

An `int64` that holds a time is read as `integer` here; whether it becomes a
`timestamp` is a convention, decided once for every field by the lane that
owns the wire conventions, never field by field in a walk.

## Formats

A walker asserts these `format` values; JSON Schema leaves an unknown format
unasserted, and these must not be.

| Format | Satisfied by |
|---|---|
| `weblisk-ref` | a string [`schemas/names`](names.md#the-grammar)' `ref` accepts |
| `weblisk-citation` | a string its `citation` accepts |
| `weblisk-version` | a string its `version` accepts |
| `version-range` | a range as [`schemas/common`](common.md#version-ranges) writes one |
| `type-expr` | a string the type-expr grammar above accepts |
| `glob` | a path pattern where `*` matches within one segment and `**` across segments |
| `date` | JSON Schema's own: RFC 3339 `full-date` |

## Blocks

```yaml
blocks:
  header:
    schema: {$ref: "family#/$defs/header-block"}
  sections:
    schema: {$ref: "family#/$defs/sections-block"}
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
    schema: {type: object, minProperties: 1, additionalProperties: {$ref: "#/$defs/type"}}
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
```

## Definitions

```yaml
defs:
  ref: {type: string, format: weblisk-ref}
  citation: {type: string, format: weblisk-citation}
  version: {type: string, format: weblisk-version}
  date: {type: string, format: date}
  part-id: {type: string, pattern: "^[a-z0-9][a-z0-9-]*$"}
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
      check: {type: string, description: "The kind of check that proves it."}
      assertion: {type: string, minLength: 1}
  field:
    type: object
    required: [type]
    unevaluatedProperties: false
    properties:
      type: {type: string, format: type-expr}
      required: {type: boolean}
      description: {type: string}
      values: {type: array, minItems: 1, items: {type: string}}
      default: {}
      unit: {type: string}
    if: {properties: {type: {const: enum}}}
    then: {required: [values]}
  type:
    type: object
    required: [fields]
    unevaluatedProperties: false
    properties:
      description: {type: string}
      fields: {type: object, additionalProperties: {$ref: "#/$defs/field"}}
  operation:
    type: object
    required: [id]
    unevaluatedProperties: false
    properties:
      id: {$ref: "#/$defs/part-id"}
      request: {$ref: "#/$defs/ref"}
      response: {$ref: "#/$defs/ref"}
      http:
        type: object
        required: [method, path]
        unevaluatedProperties: false
        properties:
          method: {enum: [GET, HEAD, POST, PUT, PATCH, DELETE]}
          path: {type: string, pattern: "^/"}
          auth: {type: string}
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
    assertion: Walking schemas/blocks.md as a file of the family family reports no finding whose policy is refuse.
  - id: table-read-by-name
    covers: [tables-by-column-name, entries-by-declaration]
    check: vectors-agree
    assertion: The table vector, whose columns are in another order and include one the catalogue does not name, projects the same entry digests as its rows written as yaml, and reports the extra column.
  - id: legacy-spelling-reported
    covers: [legacy-type-spellings, type-vocabulary-closed]
    check: vectors-agree
    assertion: The legacy vector's `int64` field is reported and read as integer, and its `int128` field is refused.
```
