---
family: schemas/family@1
version: 1.0.0
kind: specification
noun: blueprint
---
# Test blueprint

A family declared only for the grammar vectors. It is shaped like an
architecture blueprint, so every keyword a walker reads in one is exercised,
and it is named in no repository's files but these.

## Header

```yaml
header:
  schema:
    type: object
    required: [family, version]
    unevaluatedProperties: false
    properties:
      family:   {const: vectors/grammar/test-blueprint@1}
      version:  {$ref: "blocks#/$defs/version"}
      requires: {type: array, items: {$ref: "blocks#/$defs/requires-entry"}}
      review:   {$ref: "blocks#/$defs/date"}
      retired:  {$ref: "blocks#/$defs/retired"}
  uses:
    requires: {use: depends, resolves: blueprint, send: always}
  legacy:
    id: report
    name: refuse
```

## Sections

```yaml
sections:
  undeclared: {policy: report, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: true, prose: required,
       content: {max_paragraphs: 2}, use: navigates}
    - {slot: requirements, heading: Requirements, required: true,
       blocks: [{type: requirements, count: {min: 1, max: 1}}], prose: forbidden,
       use: binds, produces: [code.behaviour]}
    - {slot: types, heading: Types, aliases: [Data Types], required: false,
       blocks: [{type: types}], use: shapes, produces: [code.type]}
    - {slot: interface, heading: Interface, required: false,
       blocks: [{type: serves}, {type: events}], use: exposes, produces: [code.route]}
    - {slot: errors, heading: Errors, required: false,
       blocks: [{type: errors, count: {max: 1}}], use: shapes}
    - {slot: verifies, heading: Verification, required: true,
       blocks: [{type: verifies, count: {min: 1, max: 1}}], prose: forbidden,
       use: verifies, produces: [code.test]}
    - {slot: operation, heading: {starts_with: "Operation:"}, count: {min: 0},
       key: marker, prose: required, content: {no_rfc2119: true}, use: explains}
    - {slot: notes, heading: Notes, required: false, use: explains}
```
