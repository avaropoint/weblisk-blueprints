---
family: schemas/family@1
version: 2.1.0
kind: programme
noun: programme
capabilities: [author, versioned, depends, publishable, adoptable]
template: templates/programme-map.md
location: programmes/*/map.md
adopt: {mode: copy, record: adoption}
generates: none
---
# Programme Map Schema, Strict

The strict variant of [`schemas/programme-map`](../programme-map.md), written
ahead of the migration that needs it. Its header block is that declaration's
made strict and nothing else: the keys `header.legacy` names are refused rather
than reported, `version:` is required, and the family is the next major,
`schemas/programme-map@2`. Its sections and definitions are that declaration's
unchanged, and [`checks/families.py`](../../checks/families.py) `--strict`
holds the two to exactly that difference.

It declares no `match`, so no file is walked against it while the files are
still in their older form. Once the migration (`v2-migrate`) has rewritten
every file `schemas/programme-map` covers, lane `v2-families-strict` moves this
file over that declaration, with its `match`, and the files walk with no
finding.

## Header

```yaml
header:
  schema:
    type: object
    required: [version]
    unevaluatedProperties: false
    properties:
      family:          {const: schemas/programme-map@2}
      version:         {$ref: "schemas/blocks#/$defs/version"}
      title:           {type: string}
      domains:         {type: array, items: {type: string}}
      conforms_to:     {type: array, items: {type: string}}
      tiers:           {type: array, items: {$ref: "#/$defs/tier"}}
      artifacts:       {type: array, items: {$ref: "#/$defs/placement"}}
      operations:      {type: array, items: {type: object}}
      workflows:       {type: array, items: {type: object}}
      notices:         {type: array, items: {type: object}}
      skills:          {type: array, items: {type: object}}
      domain_services: {type: array, items: {type: object}}
      depends_on:      {type: array, items: {$ref: "#/$defs/dependency"}}
      order:           {type: integer}
      overview:        {type: string}
  uses:
    domains:         {use: depends, send: always}
    conforms_to:     {use: depends, send: always}
    tiers:           {use: declares, send: always}
    artifacts:       {use: declares, send: always}
    operations:      {use: declares, send: always}
    workflows:       {use: declares, send: always}
    notices:         {use: declares, send: always}
    skills:          {use: declares, send: always}
    domain_services: {use: declares, send: always}
    depends_on:      {use: depends, send: always}
    overview:        {use: navigates, send: always}
  legacy:
    id: refuse
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: false, count: {max: 1}, use: navigates}
```

## Definitions

```yaml
defs:
  tier:
    type: object
    required: [id]
    unevaluatedProperties: false
    properties:
      id:        {type: string, minLength: 1}
      title:     {type: string}
      rationale: {type: string}
      requires:  {type: string}
  placement:
    type: object
    required: [id]
    unevaluatedProperties: false
    properties:
      id:   {type: string, minLength: 1}
      tier: {type: string}
  dependency:
    type: object
    required: [agent, why]
    unevaluatedProperties: false
    properties:
      agent: {type: string, minLength: 1}
      why:   {type: string, minLength: 1}
```
