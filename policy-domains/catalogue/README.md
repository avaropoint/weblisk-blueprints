# The policy-domain catalogue

The **declaration** half of this family: the JSON the classifier reads, which
says which policy domains exist at all.

Governed by [`../../schemas/policy-domain.md`](../../schemas/policy-domain.md)
§ *The catalogue half*.

## Two halves, two jobs

| | this directory | [`../`](../README.md) |
|---|---|---|
| holds | `*.json` | `<domain-id>.md` |
| says | **that** a domain exists, and what words classify a document into it | **what** the domain covers, where it stops, what claiming it requires |
| read by | the classifier and the framework loader | the completeness report |
| audience | a matcher | a person |

A domain must be declared **here** before a file in `../` means anything: a
`.md` for a domain the catalogue does not declare is reported as an `orphan`,
and a programme claiming one is reported as `unknown`. The two are never merged
— the `.md` half is prose nobody can compile a matcher from, and this half is a
vocabulary nobody can review as a boundary statement.

## `keywords` lives here and only here

`keywords` is the classifier's matching vocabulary. A copy of it in the `.md`
half would drift, and the drift would **silently reclassify documents** — the
symptom is evidence attaching to the wrong subject with nothing to notice. So
`../` deliberately has no `keywords`, no `name`, no `description` and no
`category`: all four are fields of the declaration, and the declaration is here.

## Order is part of the contract

Ties break on declaration order: the classifier picks the **first**
highest-scoring domain. So a catalogue is an ordered list within a file, files
load in filename order, and an installation's own file overrides an entry **in
place** rather than appending — otherwise installing a pack would reclassify
documents that have nothing to do with it.

## How it reaches an installation

The same way a blueprint does, plus a floor:

1. **embedded** — Weblisk Studio compiles `core.json` in byte-for-byte, so an
   installation with no corpus checkout still classifies. A drift guard fails
   the build if the embedded copy and this one disagree.
2. **seeded** — on first start it is materialised into
   `<root>/.weblisk/content/domains`, so it is visible and editable rather than
   overridable-in-principle. Nothing there is ever overwritten.
3. **overridden** — any `*.json` in that directory adds domains, or replaces a
   shipped one of the same id, with no code change and no release.

That third step is the whole point. Onboarding an industry that needs a subject
nobody declared — clinical governance, food safety, flight operations — is
dropping a file in a directory. When it required a code change, an industry
programme was impossible by definition.

## Adding a domain

```json
{
  "version": "1",
  "domains": [
    {
      "id": "clinical_governance",
      "name": "Clinical Governance",
      "description": "Care quality, incidents, mortality review",
      "category": "operational",
      "requires_policy": true,
      "requires_procedure": true,
      "requires_technical": false,
      "requires_evidence": true,
      "keywords": ["clinical", "care quality", "mortality review", "never event"]
    }
  ]
}
```

Then write `../clinical_governance.md` to say what it covers and what claiming
it requires. A domain declared and never described is reported as
`undescribed`: claimable, with no stated boundary and no requirements — which
is a legitimate state to pass through and not one to stay in.
