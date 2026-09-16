---
name: changes
description: How a tenant changes after it exists — adding a component, deciding what rebuilds, and what must pass before a change is accepted. Use when adding a component to a tenant, when a blueprint has moved and a tenant must catch up, or when a build regenerated more (or less) than expected.
---

# Changing a tenant that already exists

A tenant is not generated once. It adopts blueprints, grows components, and is
rebuilt. Creating one is `tenants`; this skill is everything after that.

Rules, names and tables live in
`architecture/generation.md`. This skill says
which verb to run and which section to read.

## Add a component

```
weblisk component <kind> init [--platform go]
```

Buildable kinds come from this installation's blueprints; the command lists
them when the name is wrong. A tenant's second component is where the
interesting failures live — the planner must be told about the tenant, not just
the blueprints, or it plans a fresh module over an existing one.

`--resume` continues a run that died on a provider limit. Only `server init`
and `component <kind> init` are resumable; do not suggest it for other verbs.

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

**A wrong check is more persuasive than no check.** Every defect found in this
pipeline so far has been in a checking layer rather than in a model's output or
a blueprint's content, and each produced a confident, specific, correctly
formatted rejection of work that was fine. Test a check against real generated
output, not only against fixtures — a fixture written by the check's own author
inherits its assumptions.
