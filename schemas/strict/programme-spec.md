---
family: schemas/family@1
version: 2.0.0
kind: programme
noun: spec
capabilities: [author, versioned, depends, publishable]
template: templates/programme-spec.md
location: programmes/*/specs/*.md
generates: document
---
# Programme Spec Schema, Strict

The strict variant of [`schemas/programme-spec`](../programme-spec.md), written
ahead of the migration that needs it. Its header block is that declaration's
made strict and nothing else: the keys `header.legacy` names are refused rather
than reported, `version:` is required, and the family is the next major,
`schemas/programme-spec@2`. Its sections and definitions are that declaration's
unchanged, and [`checks/families.py`](../../checks/families.py) `--strict`
holds the two to exactly that difference.

It declares no `match`, so no file is walked against it while the files are
still in their older form. Once the migration (`v2-migrate`) has rewritten
every file `schemas/programme-spec` covers, lane `v2-families-strict` moves
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
      family:      {const: schemas/programme-spec@2}
      version:     {$ref: "schemas/blocks#/$defs/version"}
      kind:        {type: string}
      title:       {type: string}
      structure:   {type: string, description: "The id of a document family in documents/families/."}
      path:        {type: string}
      satisfies:   {type: array, items: {type: string}}
      requires:    {type: array, items: {type: string}}
      template:    {type: string}
      approved_by: {type: array, items: {type: string}}
      artifact_scope: {type: string}
      artifact_scope_metadata: {type: object}
      declares:
        type: object
        unevaluatedProperties: false
        properties:
          obligation: {$ref: "#/$defs/obligation"}
          register:   {$ref: "#/$defs/register"}
      register: {$ref: "#/$defs/register"}
      brief:    {type: string}
  uses:
    requires:    {use: depends, resolves: spec, send: always}
    structure:   {use: depends, resolves: specification, send: always}
    template:    {use: depends, send: always}
    satisfies:   {use: depends, resolves: control, send: always}
    approved_by: {use: binds, send: always}
    declares:    {use: declares, send: always}
    register:    {use: declares, send: always}
    brief:       {use: instructs, send: always}
  legacy:
    id: refuse
    declares.obligation.id: refuse
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: instructs, send: always}
  slots:
    - {slot: title, heading: {level: 1}, required: false, count: {max: 1}, use: navigates}
```

## Definitions

```yaml
defs:
  obligation:
    type: object
    required: [activity]
    unevaluatedProperties: false
    properties:
      activity:       {type: string, minLength: 1}
      cadence:        {type: string}
      authority:      {type: string}
      interval_basis: {type: string}
      responsible:    {type: string}
      applies_to:     {type: string}
      per:            {type: object}
      records:        {type: string}
      satisfies:      {type: array, items: {type: string}}
      for:            {type: object}
      escalate:       {type: object}
      creates:        {type: object}
  register:
    type: object
    required: [columns]
    unevaluatedProperties: false
    properties:
      title:          {type: string}
      note:           {type: string}
      columns:        {type: array, minItems: 1, items: {type: object}}
      layout:         {type: string}
      review:         {type: string}
      approvers:      {type: array, items: {type: string}}
      approval_order: {type: string}
      retention:      {type: object}
```
