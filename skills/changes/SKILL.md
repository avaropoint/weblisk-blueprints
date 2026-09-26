---
name: changes
description: How a tenant changes after it exists — adding a component such as the content service, deciding what rebuilds, and what must pass before a change is accepted. Use when adding a component to a tenant, when a tenant needs to hold content, when a blueprint has moved and a tenant must catch up, or when a build regenerated more (or less) than expected.
---

# Changing a tenant that already exists

A tenant is not generated once. It adopts blueprints, grows components, and is
rebuilt. Creating one is `tenants`; this skill is everything after that.

Rules, names and tables live in
`architecture/generation.md`. This skill says
which verb to run and which section to read.

## Add a component

```
weblisk component help                   # what this installation can build
weblisk component <kind> init [--platform go]
```

**An orchestrator is a tenant's first component, not the tenant.** A tenant is
a set of siblings in one module, each registering with the orchestrator on
start. `architecture/orchestrator.md`, "What a tenant consists of", says where
that set is declared — and it is `GET /v1/services`, not a file.

Buildable kinds come from this installation's blueprints; the command lists
them when the name is wrong. A tenant's second component is where the
interesting failures live — the planner must be told about the tenant, not just
the blueprints, or it plans a fresh module over an existing one.

`--resume` continues a run that died on a provider limit. Only `server init`
and `component <kind> init` are resumable; do not suggest it for other verbs.

### Check the listed kind has a blueprint to generate from

`component help` lists a kind when its architecture blueprint states an
`## Endpoints` table and declares bindings. Whether the pipeline then *reads*
that blueprint is a second question, and the two sets are not the same.

Before running `component <kind> init` for a kind you have not built before,
run it and read the announced blueprint list. **If the component's own
blueprint is not in it, stop.** The run will otherwise plan from the protocol
and the platform alone, produce a plausible file set, and pass its own checks —
a component generated against nothing, reported as generated.

### Content

`weblisk component content init` builds the tenant's content service —
the thing that lets a tenant hold authored text rather than only run code.
What it serves, what custody means, and what declaring a repository requires
are all `architecture/content.md`; none of it is repeated here.

Two things about it are operational rather than specified, and are what an
agent gets wrong:

- **Generating it is not the end.** A content service with no repository
  declared holds nothing, and a tenant that has one must still be told which
  stores it governs.
- **The first adoption call is meant to fail.** Adopting a store that already
  holds bytes is two calls: the first returns a census and refuses, the second
  passes that census digest back as `if_match`. Treat the first refusal as the
  answer, not as an error to retry or work around — see `architecture/content.md`,
  "Declaring a Repository".

## Decide before you build

The rebuild decision is **per file**, and the default answer is KEEP.
`architecture/generation.md`, "Deciding whether a file must be rebuilt",
declares the conditions; first match wins.

Two of them are **refusals, not instructions**:

- a file that differs from what generation wrote
- a file generation cannot show it wrote

Neither regenerates. They are reported apart because the remedy differs: one
sends somebody looking for their own edit, the other is what is true after a
manifest is lost or a run was interrupted before recording.

**Never treat a refusal as "rebuild".** Doing so overwrites the edit the verdict
exists to protect.

A blueprint change does not regenerate a component. It is assessed against each
file, and a file the change does not reach is left alone. One digest over the
whole prompt cannot make that distinction — it answers "did anything change" and
never "did anything I depend on change".

## What must pass

`architecture/generation.md`, "The verification gate",
declares four layers, run in order, cheapest first. A failure at any layer stops
the run, because a later layer's result is meaningless once an earlier one failed.

Then, over HTTP against the running thing:

```
weblisk test conformance [--level <n>] [--test L1-03]
```

Black-box, so an implementation in any language can run the same suite.
`architecture/testing.md` specifies the test IDs. **`unrun` is not `pass`** — a
level with no harness must be reported as having no harness, never counted.

Finally, acceptance asks the finished tenant whether it *works*, over HTTP, the
way its clients will. "Generated without an error" is not the same claim.

## Before trusting any build or check

Read the announced source list and revision that generation prints **before** it
starts, and look for `-dirty`.

The blueprint cache is a clone of the **remote**. Committed-but-unpushed work
never arrives; a source pointing at a working tree is cloned at HEAD, so
uncommitted edits do not arrive either. In both cases the revision printed is
accurate and the conclusion drawn from it is wrong.

To build against in-flight blueprint work: put a `blueprints/` checkout in the
tenant, or set `WL_BLUEPRINT_SOURCES`, or push.

## Two things that are true and surprising

**Generation is not repeatable.** Two builds from the same blueprint revision
produce different file sets, different file names and different conformance
verdicts. Do not chase determinism — it is model-driven and variance is the
medium. What follows is that **conformance is a per-build fact**: you cannot
infer one tenant's correctness from another's, so the checks run every time.

**A component a tenant does not have must be reported as absent, not as
empty.** Ask the directory before you ask the capability. A tenant with no
content service and a tenant whose content service is empty return the same
thing to a caller that only asked for content, and the second answer is the one
that gets written down.

**A wrong check is more persuasive than no check.** Every defect found in this
pipeline so far has been in a checking layer rather than in a model's output or
a blueprint's content, and each produced a confident, specific, correctly
formatted rejection of work that was fine. Test a check against real generated
output, not only against fixtures — a fixture written by the check's own author
inherits its assumptions.
