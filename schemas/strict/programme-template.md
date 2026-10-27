---
family: schemas/family@1
version: 2.0.0
kind: programme
noun: form
capabilities: [author, versioned, publishable]
template: templates/programme-template.md
location: programmes/*/templates/*.md
generates: document
---
# Programme Template Schema, Strict

The strict variant of [`schemas/programme-template`](../programme-template.md),
written ahead of the migration that needs it. Its header block is that
declaration's made strict and nothing else: the keys `header.legacy` names are
refused rather than reported, `version:` is required, and the family is the
next major, `schemas/programme-template@2`. Its sections are that declaration's
unchanged, and [`checks/families.py`](../../checks/families.py) `--strict`
holds the two to exactly that difference.

It declares no `match`, so no file is walked against it while the files are
still in their older form. Once the migration (`v2-migrate`) has rewritten
every file `schemas/programme-template` covers, lane `v2-families-strict` moves
this file over that declaration, with its `match`, and the files walk with no
finding.

## Header

```yaml
header:
  schema:
    type: object
    required: [version]
    unevaluatedProperties: false
    properties:
      family:      {const: schemas/programme-template@2}
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
  legacy:
    id: refuse
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: instructs, send: always}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1}, use: navigates}
```
