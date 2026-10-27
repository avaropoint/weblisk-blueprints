---
family: schemas/family@1
version: 1.0.0
kind: procedure
noun: procedure
capabilities: [author, versioned, publishable, adoptable]
template: templates/procedure.md
adopt: {mode: copy, record: extends}
generates: none
---
# Procedure

How a piece of work is done, step by step, by somebody who was not in the room
when it was designed. A plan shares this shape
([why `structure` is not `kind`](../../schemas/programme.md#structure-need-not-be-the-same-word-as-kind)).

The declaration of the document family `documents/families/procedure`. What a
document family is, how a document comes to be checked against one, and whose
copy is checked are [`documents/families`](README.md)'s.

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:         {const: documents/families/procedure@1}
      title:          {type: string}
      kind:           {type: string}
      structure:      {type: string}
      status:         {type: string}
      owner:          {type: [string, "null"]}
      version:        {$ref: "schemas/blocks#/$defs/version"}
      reference:      {type: string}
      task:           {type: string, description: "What a safe job procedure is for, as its form writes it."}
      scope:          {type: string}
      scope_metadata: {type: object}
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: false, count: {max: 1}, use: navigates}
    - {slot: prerequisites, heading: Prerequisites, aliases: [Preconditions], required: false, use: binds,
       guidance: "Access, tools, approvals and conditions needed before starting."}
    - {slot: steps, heading: Steps, aliases: [Procedure, Process], required: report, use: binds,
       guidance: "Numbered actions in order, each one thing a person does."}
    - {slot: verification, heading: Verification, aliases: [Validation], required: false, use: binds,
       guidance: "How the person carrying it out confirms it worked, with the expected result."}
    - {slot: rollback, heading: Rollback, aliases: [Recovery], required: false, use: binds,
       guidance: "How to undo it safely if a step fails part-way."}
```
