# Policy domains

Everything the corpus says about a **subject area of governance** — access
control, incident response, occupational health and safety. A programme
declares which of these it operates in.

Governed by [`../schemas/policy-domain.md`](../schemas/policy-domain.md).

| | |
|---|---|
| [`catalogue/`](catalogue/README.md) | the **declaration**: which domains exist, and the keywords that classify a document into one. JSON, read by the classifier |
| `<domain-id>.md` | the **commentary**: what the domain covers, where it stops, what a programme claiming it must provide. Markdown, read by the completeness report |

A third body of fact — which programmes claim a domain, which artifacts answer
it, who is responsible — is derived on read and never written down here.

## Not `domains/`, and not a declaration

`domain` already means a **domain controller** in this corpus — an agent
process that owns a business function, holds a port, and has a `weblisk domain`
verb behind it. [`../schemas/common.md`](../schemas/common.md) gives those
specs a directory called `domains/`. Two unrelated things in two directories of
the same name is the fault that `platform`/`provider`/`integration` was split
to fix, so this family takes the product's own existing word: a **policy
domain**.

**A `.md` here does not declare that a domain exists.**
[`catalogue/`](catalogue/README.md) does that, and an installation extends it
the way it extends standards. A file here for a domain the catalogue does not
declare is reported as an orphan.

## What is hand-written, and what is never

Which programmes claim a domain, which artifacts answer it, what those
artifacts are, what work they raise, who is responsible and what is kept — all
of that is already in `../programmes/`, and it is **computed rather than
copied**. A second copy drifts the first time a programme changes, and the
drift is invisible because both halves look right on their own.

What is written here is the part no derivation reaches:

- **where the domain stops** — `access_control`, `hr_security` and
  `physical_security` all touch a person arriving with a badge and a laptop,
  and somebody has to draw the line. `boundaries:` draws it, and a boundary
  declared on one side only is reported.
- **what a programme claiming it must provide** — `requires:`, from a closed
  vocabulary of seven things the engine can actually check.

## The requirement vocabulary earned its place

Each of the seven discriminates against the corpus as it stands — measured over
the 71 programme-domain claims the 12 shipped programmes currently make:
`register` 70, `procedure` 67, `triggered-work` 47, `approval` 42, `policy` 31,
`retention` 15, `template` 12.

Four further candidates were rejected for being **always true**: an obligation
existing, its cadence, its responsible position and its escalation are each
present in 70 of 71 claims, and the single exception is the same claim every
time — one nothing attributes to at all, which is already its own finding. A
requirement that cannot fail is not a requirement.

## What is here

`catalogue/core.json`, declaring twenty-five domains, and twenty-five `.md`
files, one for each. Twenty-two are claimed by a programme today; `encryption`,
`secure_development` and `quality_management` are declared, described and not
yet claimed by anything, which is a legitimate state and not a gap.

Adding a domain is two files and no release: an entry in the catalogue, and a
`.md` beside it. It used to be a code change in the product, which made an
industry programme impossible by definition.
