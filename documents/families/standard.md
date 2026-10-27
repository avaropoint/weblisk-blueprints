---
family: schemas/family@1
version: 1.0.0
kind: standard
noun: standard
capabilities: [author, versioned, publishable, adoptable]
template: templates/standard.md
adopt: {mode: copy, record: extends}
generates: none
---
# Standard

An organisation's own standard: the measurable requirements that carry out one
of its policies. Not an industry standard — those are declared by
[`../standard.md`](../../schemas/standard.md) and adopted, never written in this shape.

The declaration of the document family `documents/families/standard`. What a
document family is, how a document comes to be checked against one, and whose
copy is checked are [`documents/families`](README.md)'s.

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:         {const: documents/families/standard@1}
      title:          {type: string}
      kind:           {type: string}
      structure:      {type: string}
      status:         {type: string}
      owner:          {type: [string, "null"]}
      version:        {$ref: "schemas/blocks#/$defs/version"}
      reference:      {type: string}
      scope:          {type: string}
      scope_metadata: {type: object}
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: false, count: {max: 1}, use: navigates}
    - {slot: overview, heading: Overview, aliases: [Purpose], required: report, use: explains,
       guidance: "What this standard governs and which policy it implements."}
    - {slot: requirements, heading: Requirements, required: report, use: binds,
       guidance: "The specific, measurable technical or process requirements."}
    - {slot: conformance, heading: Conformance, aliases: [Compliance], required: false, use: binds,
       guidance: "How conformance is measured and what non-conformance triggers."}
```
