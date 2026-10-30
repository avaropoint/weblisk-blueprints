---
family: schemas/family@1
version: 1.2.0
kind: programme
noun: programme
match: [programmes/*/map.md]
capabilities: [author, versioned, depends, publishable, adoptable]
template: templates/programme-map.md
location: programmes/*/map.md
adopt: {mode: copy, record: adoption}
generates: none
---
# Programme Map Schema

The declaration of the family `schemas/programme-map`: a programme's map, one
file at the programme's own root. What each field means, what the loader
refuses and how a programme is adopted is
[`schemas/programme`](programme.md#the-programme-map)'s; this file is the
shape a walk holds a map to, and states no meaning of its own.

It is declared in **migration mode**, as
[`schemas/programme-spec`](programme-spec.md) is: a map's own `id:` is
reported, a missing `version:` is reported, and every other key the header
does not declare is refused. The strict variant is
[`schemas/strict/programme-map`](strict/programme-map.md).

## Header

```yaml
header:
  schema:
    type: object
    unevaluatedProperties: false
    properties:
      family:          {const: schemas/programme-map@1}
      version:         {$ref: "schemas/blocks#/$defs/version"}
      title:           {type: string}
      domains:         {type: array, items: {type: string}}
      conforms_to:     {type: array, items: {type: string}}
      optional_standards: {type: array, items: {type: string}}
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
    optional_standards: {use: depends, send: always}
    tiers:           {use: declares, send: always}
    artifacts:       {use: declares, send: always}
    operations:      {use: declares, send: always}
    workflows:       {use: declares, send: always}
    notices:         {use: declares, send: always}
    skills:          {use: declares, send: always}
    domain_services: {use: declares, send: always}
    depends_on:      {use: depends, send: always}
    overview:        {use: navigates, send: always}
  required:
    version: report
  legacy:
    id: report
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: false, count: {max: 1}, use: navigates}
```

A map's body is its overview, and its sections are the reasons the programme
is drawn as it is, which differ from one programme to the next; `undeclared`
is `allow` for that reason.

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

A tier's and a placement's `id` are not legacy: they are ids within the map,
which a walk reads as entries of it, not ids a file claims for itself.
