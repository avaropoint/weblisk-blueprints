---
family: schemas/family@1
version: 1.0.0
kind: programme
noun: form
match: [programmes/*/templates/*.md]
capabilities: [author, versioned, publishable]
template: templates/programme-template.md
location: programmes/*/templates/*.md
generates: document
---
# Programme Template Schema

The declaration of the family `schemas/programme-template`: the blank forms a
programme brings, one file each under `templates/`. A form's `frontmatter:`
is what the document created from it opens with, as
[`schemas/programme`](programme.md#a-forms-frontmatter) says; its body is the
document's starting text. This file is the shape a walk holds a form to, and
states no meaning of its own.

It is declared in **migration mode**, as
[`schemas/programme-spec`](programme-spec.md) is: a form's own `id:` is
reported, a missing `version:` is reported, and every other key the header
does not declare is refused. The strict variant is
[`schemas/strict/programme-template`](strict/programme-template.md).

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:      {const: schemas/programme-template@1}
      version:     {$ref: "schemas/blocks#/$defs/version"}
      label:       {type: string}
      description: {type: string}
      path:        {type: string}
      template:    {const: true, description: "Marks the file as a form, for the readers that list forms."}
      kind:        {type: string}
      order:       {type: integer}
      frontmatter: {type: object, description: "The created document's own header; its keys are the document family's."}
  uses:
    frontmatter: {use: declares, send: always}
  required:
    version: report
  legacy:
    id: report
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: instructs, send: always}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1}, use: navigates}
```

A form's sections are the document's own, which differ from one form to the
next, so `undeclared` is `allow`; the document family a created document is
written to is what holds its sections to a shape.
