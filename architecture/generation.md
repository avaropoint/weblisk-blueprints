<!-- blueprint
type: architecture
name: generation
version: 1.0.0
requires: [protocol/spec, architecture/testing, schemas/platform]
platform: any
tier: free
-->

# Generation

How an implementation is produced from blueprints, and how it is gated before it
is called finished. Covers what a generator must be told, in what order it must
be verified, and what it must be forbidden from adding.

## Overview

The framework's premise is that blueprints drive the output: a specification is
sufficient to produce an implementation, and any model can produce one. That
holds only if the process around the model is specified as carefully as the
artifact it produces.

It was not. Blueprints stated *what* to build and *how to verify* it, and said
nothing about *how to instruct*. Every generator therefore invented its own
prompting, which meant two implementations of the framework could read identical
blueprints and produce materially different results — the exact
non-determinism the specification exists to remove.

This blueprint closes that. It defines the prompt contract, the generation loop,
and the verification gate. It does not define what to build; that remains
`protocol/spec.md`, the platform blueprint, and the manifest.

**Determinism here means behavioural equivalence, not identical source.** Two
models will name and structure things differently. What must not differ is what
a caller can observe: the files that exist, the symbols they expose, the
endpoints served, the properties asserted by every blueprint's Verification
Checklist, and the conformance result.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      endpoints:
        - name: orchestrator-endpoints
          fields_used: [method, path]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/testing
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        - name: conformance-suite
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: schemas/platform
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GenerationManifest
          fields_used: [files, build, conformance]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
  blueprints ──┐
               ├──▶ prompt assembly ──▶ model ──▶ candidate file
  manifest ────┤            ▲                          │
               │            │                          ▼
  checklists ──┘            └──── rejection ──── contract check
                                                       │ accepted
                                                       ▼
                                              accumulated declarations
                                                       │
                                    (all files) ───────┤
                                                       ▼
                                    structure → coherence → properties → behaviour
```

Four gates in ascending cost. Each is cheaper than the one after it and
localises a failure further, so a fault is diagnosed at the earliest layer that
can see it.

---

## Responsibilities

### Owns

- The prompt contract: what a generator MUST convey to a model
- The generation loop: one file per call, against a declared file set
- The verification gate and the order its layers run in
- Scope discipline: what a generated implementation must NOT contain

### Does NOT Own

- What to build. `protocol/spec.md` defines the wire contract; a platform
  blueprint defines the layout; the manifest declares the file set
- How to verify behaviour. `architecture/testing.md` owns conformance
- Prompt wording. This blueprint fixes what must be conveyed, never the phrasing
- Model selection. Any model that satisfies the contract is acceptable

---

## Interfaces

```yaml
interfaces:
  generate:
    description: Produce one target's files from blueprints
    inputs: [manifest_target, blueprints, platform_blueprint, checklists]
    outputs: [files, progress_stream]
  verify:
    description: Gate a generated target before it is called finished
    inputs: [files, manifest_target, checklists, protocol_spec]
    outputs: [layer_results, failures]
```

---

## Data Flow

1. The manifest for the target is read; its file list is the file set. A
   generator MUST NOT add to it or omit from it.
2. Verification Checklists are extracted from every blueprint being read and
   carried as explicit acceptance criteria.
3. For each file in order: assemble the prompt, call the model, check the
   response against the contract, retry with the specific complaint on failure.
4. On acceptance, the file's top-level declarations are extracted and added to
   the accumulated declarations passed to every subsequent file.
5. When every file has succeeded, all are written together.
6. The gate runs: structure, coherence, properties, behaviour.

---

## The prompt contract

A generator MUST convey all of the following. Wording is the implementation's
choice; content is not.

| # | Element | Why it is required |
|---|---------|--------------------|
| 1 | **Output contract** — exactly one file, no prose, no fences, first character is the file's first character | A convention requested in prose is honoured differently by different models. This is the single largest source of unusable output |
| 2 | **The file's obligations** — its `path`, `purpose`, `must_define`, `must_serve` | A file generated from a filename alone is a guess |
| 3 | **Accumulated declarations** — the actual top-level symbols already defined by previously generated files | Naming the FILES is not enough. A generator told only that `helpers.go` exists will redeclare its symbols, or invent helpers that were never written |
| 4 | **The complete file set** — every path in the target | So a file knows what it is NOT responsible for, and does not absorb another file's work |
| 5 | **Platform constraints** — language, dependency policy, idioms | From the platform blueprint |
| 6 | **Verification Checklists** — as explicit acceptance criteria, not buried in the blueprint body | A checklist present as context is complied with by luck. Present as criteria, it is complied with on purpose |
| 7 | **Scope prohibition** — build the declared obligations and nothing else | Below |
| 8 | **The blueprints themselves** | The specification being implemented |

### Scope discipline

A generator MUST instruct the model to produce ONLY what the manifest declares
for that file. It MUST NOT invite, and SHOULD explicitly forbid:

- endpoints, routes or handlers not named in `must_serve`
- configuration, metrics, dashboards, health pages or admin surfaces not
  specified by a blueprint
- dependencies beyond the platform's stated policy
- "helpful" additions of any kind

A model asked to build an orchestrator will build a generous one. Every
unrequested addition is code nobody specified, nobody reviewed, and somebody
must read before it can be trusted — and in a bootstrapped hub it is code that
enlarges the attack surface of the component holding the tenant's keys.

---

## The verification gate

Four layers, run in order, cheapest first. A failure at any layer stops the run:
a later layer's result is meaningless once an earlier one has failed.

### Layer 1 — Structure

Every file in the manifest exists; every `must_define` symbol appears; every
`must_serve` endpoint appears. Answerable in milliseconds, and localises a
failure to one file.

### Layer 2 — Coherence

The files agree with each other:

- every top-level symbol is declared exactly **once** across the target
- every call site matches the declared signature
- the target builds with the manifest's `build` command

Layer 2 exists because a target can pass Layer 1 completely and not compile —
each file individually correct, collectively contradictory. This is the most
common failure of per-file generation and it is invisible to every other layer.

### Layer 3 — Properties

The Verification Checklist of every blueprint the target was generated from.
Those assertions are the blueprint's own statement of what a correct
implementation looks like; a generator that reads a blueprint and ignores its
checklist has used half the document.

Implementations MUST check every mechanically checkable assertion and MUST
report the remainder as unchecked rather than passed. An assertion nobody
verified is not a satisfied one.

### Layer 4 — Behaviour

`architecture/testing.md` conformance, at the levels the manifest names.

---

## Security

- **Generated output is untrusted.** File paths in a model response are
  attacker-influenced input where any blueprint came from a marketplace. Paths
  MUST be validated for containment before any file is written; see
  `architecture/cli.md`.
- **The generator receives no secrets.** Blueprints and a platform specification
  are the inputs. Key material, tenant content and instance state are not.
- **The generator holds no filesystem tools.** It returns text; the caller
  writes files. A generator that can write directly has no boundary between
  generating an implementation and doing anything else to the machine.
- **Nothing is written until every file succeeds.** A partially written target
  invites somebody to repair it by hand, which silently converts a reproducible
  artifact into an unreviewed one.
- **Provenance is recorded.** Which model, at which blueprint versions, produced
  a given target. See `patterns/content-identity`.

---

## Implementation Notes

**Pass declarations, not filenames.** The difference is the single largest cause
of incoherent output. Extracting top-level declarations from an accepted file is
mechanical in every language the framework targets, and cheap.

**Retry with the specific complaint.** "Regenerate this file" wastes a call.
"`protocol.go` must define `AgentManifest`, which does not appear" is usually
corrected on the next attempt. Bound retries — three is enough for a model that
drifted and not enough to spend an afternoon on one that cannot comply.

**Strip a wrapping code fence rather than rejecting it.** Models fence code by
reflex. Failing an otherwise-correct file over formatting fails for the wrong
reason. A fence in the MIDDLE of a response is different: prose surrounds it,
and the response should be rejected.

**Report progress per file.** Generation is minutes long. A caller that cannot
show progress will grow its own implementation to obtain it, and then there are
two.

**Do not conflate an unrun check with a passed one.** Where the protocol spec,
a checklist item or a conformance level cannot be evaluated, report it as
unchecked. This is the difference between "this implementation is conformant"
and "nothing contradicted it".

---

## Verification Checklist

- [ ] A generator produces exactly the files the manifest declares — no more, no fewer
- [ ] A response containing prose before the file content is rejected and retried with that reason
- [ ] A wrapping code fence is stripped; a response with prose around a fence is rejected
- [ ] Each file's prompt includes the top-level declarations of every previously accepted file
- [ ] Each file's prompt includes the Verification Checklist assertions of the blueprints being implemented
- [ ] Each file's prompt forbids endpoints, configuration and dependencies not declared for it
- [ ] No file is written to disk until every file in the target has been accepted
- [ ] Layer 1 failure names the file and the missing symbol or endpoint
- [ ] Layer 2 detects a symbol declared in two files, and a call site disagreeing with its declaration
- [ ] Layer 3 evaluates every mechanically checkable checklist assertion and reports the rest as unchecked
- [ ] A failure at any layer prevents later layers from reporting a result
- [ ] Generated file paths are validated for containment before any write
- [ ] The model, blueprint versions and manifest version used are recorded with the output
