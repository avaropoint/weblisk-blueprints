---
family: schemas/family@1
version: 1.0.0
kind: guideline
noun: guideline
capabilities: [author, versioned, publishable, adoptable]
template: templates/guideline.md
adopt: {mode: copy, record: extends}
generates: none
---
# Guideline

Advice: what a person should consider, not what they must do. A guideline
counts as nobody's coverage of a control ([`../kinds.md`](../../schemas/kinds.md)), so its
sections ask for recommendations rather than rules.

The declaration of the document family `documents/families/guideline`. What a
document family is, how a document comes to be checked against one, and whose
copy is checked are [`documents/families`](README.md)'s.

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:         {const: documents/families/guideline@1}
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
    - {slot: overview, heading: Overview, required: report, use: explains,
       guidance: "What this guideline helps someone decide or do."}
    - {slot: recommendations, heading: Recommendations, aliases: [Guidance, Best Practices], required: report, use: explains,
       guidance: "Suggested practice, framed as advice rather than obligation."}
```
