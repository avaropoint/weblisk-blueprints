---
family: schemas/family@1
version: 1.0.0
kind: specification
noun: programme
---
# Test programme

A family declared only for the grammar vectors, in migration mode: the keys
older files carry are reported, a version they lack is reported, and every
other key is still refused. It is named in no repository's files but these.

## Header

```yaml
header:
  schema:
    type: object
    required: [family]
    unevaluatedProperties: false
    properties:
      family:  {const: vectors/grammar/test-programme@1}
      version: {$ref: "schemas/blocks#/$defs/version"}
      declares:
        type: object
        unevaluatedProperties: false
        properties:
          obligation:
            type: object
            unevaluatedProperties: false
            properties:
              title: {type: string, minLength: 1}
  uses:
    declares: {use: declares}
  required:
    version: report
  legacy:
    id: report
    declares.obligation.id: report
```

## Sections

```yaml
sections:
  undeclared: {policy: refuse}
  slots:
    - {slot: title, heading: {level: 1}, required: true, prose: required, use: navigates}
    - {slot: steps, heading: Steps, required: true, prose: required, use: instructs}
```
