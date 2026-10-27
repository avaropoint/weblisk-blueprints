---
family: schemas/family@1
version: 1.0.0
kind: policy
noun: policy
capabilities: [author, versioned, publishable, adoptable]
template: templates/policy.md
adopt: {mode: copy, record: extends}
generates: none
---
# Policy

What an organisation commits to, and who is held to it. A policy states intent
and rules; how a rule is carried out belongs in a procedure, and the measurable
detail in a standard.

The declaration of the document family `documents/families/policy`. What a
document family is, how a document comes to be checked against one, and whose
copy is checked are [`documents/families`](README.md)'s.

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:         {const: documents/families/policy@1}
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
    - {slot: purpose, heading: Purpose, required: report, use: explains,
       guidance: "Why this policy exists and what outcome it protects. One paragraph."}
    - {slot: scope, heading: Scope, required: report, use: binds,
       guidance: "Who and what it applies to — people, systems, locations, data. State exclusions explicitly."}
    - {slot: statements, heading: Policy Statements, aliases: [Statements, Requirements], required: report, use: binds,
       guidance: "The rules themselves, as numbered obligations. Each should be testable."}
    - {slot: roles, heading: Roles & Responsibilities, aliases: [Roles, Responsibilities], required: false, use: binds,
       guidance: "Who is accountable for each obligation, by position rather than by name."}
    - {slot: exceptions, heading: Exceptions, required: false, use: binds,
       guidance: "How a documented exception is requested, approved and time-boxed."}
    - {slot: references, heading: References, aliases: [Related Documents], required: false, use: navigates,
       guidance: "Standards, procedures and records this policy depends on."}
```
