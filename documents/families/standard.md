---
family: schemas/family@1
version: 1.1.0
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
      uid:            {type: string, description: "The document's own identity, minted by the client that created it and never changed."}
      approver:       {type: [string, "null"]}
      approved_by:    {type: [string, "null"]}
      effective:      {type: [string, "null"]}
      effective_date: {type: [string, "null"]}
      review_cycle:   {type: [string, "null"]}
      last_reviewed:  {type: [string, "null"]}
      last_review:    {type: [string, "null"]}
      classification: {type: [string, "null"]}
      frameworks:     {type: [array, string, "null"]}
```

The header is open: it is the organisation's own, and a key this family does
not type is carried, never refused. The keys typed here are the ones a client
reads from a document header ([`documents/families`](README.md#the-header)).

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
