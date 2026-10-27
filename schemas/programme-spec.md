---
family: schemas/family@1
version: 1.0.0
kind: programme
noun: spec
match: [programmes/*/specs/*.md]
capabilities: [author, versioned, depends, publishable]
template: templates/programme-spec.md
location: programmes/*/specs/*.md
generates: document
---
# Programme Spec Schema

The declaration of the family `schemas/programme-spec`: a programme's
artifact specifications, one file per artifact under `specs/`. What each field
means, and what the loader refuses, is
[`schemas/programme`](programme.md#the-artifact-specification)'s; this file is
the shape a walk holds a spec to, and states no meaning of its own.

It is declared in **migration mode**. A spec written before corpus v2 carries
its own `id:`, and an obligation's `id:` under `declares.obligation`, and most
carry no `version:`. A walk reports each of those as one finding
(`legacy-key`, `missing-key`) and refuses every other key the header does not
declare, so every spec walks with no edit and the family is not loose
([`schemas/family`](family.md#definitions), migration mode). The strict variant,
which refuses both keys and requires `version:`, is
[`schemas/strict/programme-spec`](strict/programme-spec.md); it replaces this
declaration once the migration (`v2-migrate`) has rewritten the specs.

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:      {const: schemas/programme-spec@1}
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
  required:
    version: report
  legacy:
    id: report
    declares.obligation.id: report
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: instructs, send: always}
  slots:
    - {slot: title, heading: {level: 1}, required: false, count: {max: 1}, use: navigates}
```

A spec's body is its brief, and a heading in it is part of the brief, which is
why `undeclared` is `allow`: no spec has a section the family could name.

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

The definitions hold the keys an obligation and a register may carry, and
nothing of what their values may say: each closed vocabulary keeps its one
home in [`schemas/programme`](programme.md#the-closed-vocabularies), whose
loader refuses or reports a value outside it as that section states.
