<!-- blueprint
type: architecture
name: generation
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/testing]
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
`protocol/spec.md`, `protocol/types.md` and the platform blueprint.

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

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: protocol-types
          fields_used: [name, fields]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Architecture

```
  blueprints ──▶ requirements ──▶ model plans ──▶ plan validated
                (types,             (its own       (all requirements
                 endpoints,          file set       placed?)
                 assertions)         and order)          │
                                          ▲              │ accepted
                                          └── rejected ──┤
                                                         ▼
                       ┌────────── per file, in the plan's order ──────────┐
                       │                                                    │
                       ▼                                                    │
             prompt assembly ──▶ model ──▶ contract check ──▶ declarations ─┘
                       ▲                        │ rejected
                       └────────────────────────┘
                                                         │ all accepted
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

- What to build. `protocol/spec.md` defines the wire contract and the types; a
  platform blueprint gives language direction
- How to verify behaviour. `architecture/testing.md` owns conformance
- Prompt wording. This blueprint fixes what must be conveyed, never the phrasing
- Model selection. Any model that satisfies the contract is acceptable

---

## Interfaces

```yaml
interfaces:
  generate:
    description: Produce one target's files from blueprints
    inputs: [requirements, plan, blueprints, platform_blueprint, checklists]
    outputs: [files, progress_stream]
  verify:
    description: Gate a generated target before it is called finished
    inputs: [files, plan, checklists, protocol_spec]
    outputs: [layer_results, failures]
```

---

## Data Flow

1. **Requirements are extracted from the blueprints** — the types the protocol
   enumerates, the endpoints it defines, the assertions every Verification
   Checklist states. This is the specification, and it already exists; nothing
   is authored to restate it.
2. **The model proposes a plan** — which files it will write, what each contains,
   and in what order they must be generated. The structure is the MODEL's.
3. **The plan is validated against the requirements** — is every required type
   placed in some file? every endpoint served? Rejected plans are returned with
   what is missing, and re-planned.
4. For each file in the plan's order: assemble the prompt, call the model, check
   the response against the contract, retry with the specific complaint.
5. On acceptance, the file's top-level declarations are extracted and added to
   the accumulated declarations passed to every subsequent file.
6. When every file has succeeded, all are written together.
7. The gate runs: structure, coherence, properties, behaviour.
8. The plan is recorded with the output as provenance.

---

## The plan

A generator MUST NOT impose a file structure. It asks the model for one.

### Why the structure is the model's

A specification constrains BEHAVIOUR. What a caller can observe — the endpoints
served, the types exchanged, the properties asserted — is the contract. How that
is divided into files is an implementation decision, and a specification that
fixes it is asserting authority it does not have.

There is a practical cost too. A file list authored by hand is a guess, and a
guess encoded as law prevents a model from making a better decision: putting
fifty-five types in three files rather than one, or omitting a helpers file it
does not need. Worse, an authored list tends to be a SUBSET of what the
blueprints already enumerate — naming four required types where the protocol
defines fifty-five — and so narrows the specification while appearing to
sharpen it.

The blueprints already state what must exist. The plan states how this
implementation will arrange it.

### What a plan declares

```yaml
plan:
  target: orchestrator
  root: <dir>
  build: <command>          # from the platform blueprint's Build and Run
  files:
    - path: <relative>
      purpose: <text>
      declares: []          # TOP-LEVEL symbols only — see below
      serves: []            # "METHOD /path" this file will handle
      depends_on: []        # files that must be generated first
```

`declares` means top-level symbols: types, functions, methods, constants and
package-level variables. It MUST NOT list struct fields, local variables, or
anything nested inside another declaration — a verifier cannot distinguish those
from an omission, and rejecting on one has ended a run over correct code.

A method MUST be named in receiver notation, `(Type).Method`, so that identity is
unambiguous both when checking the file and when detecting collisions between
files. A generator MUST state these rules when asking for a plan; a planner told
only "symbols this file will define" will reasonably list fields.

### Validating a plan

A plan is checked against the extracted requirements BEFORE any file is
generated. It MUST be rejected, with what is missing, when:

1. A type the protocol enumerates is placed in no file.
2. An endpoint the protocol defines for this target is served by no file.
3. A symbol is declared by more than one file.
4. `depends_on` contains a cycle, or names a file not in the plan.
5. A file has no purpose.

Rejection returns the specific gap and asks for a revised plan. This costs one
call and saves generating a structure that could never satisfy the blueprints.

### Generation order comes from the plan

Files are generated in dependency order, derived from `depends_on`. This is not
cosmetic: an entry point generated before the component it constructs cannot know
that component's signature, however complete the declarations passed to it. The
first real run of this pipeline failed exactly there — an entry point written
second called a constructor written fifth.

A reader's order and a generator's order are different. A layout in a platform
blueprint is written for a person, entry point first; a plan is ordered for
production, dependencies first.

---

## The prompt contract

A generator MUST convey all of the following. Wording is the implementation's
choice; content is not.

| # | Element | Why it is required |
|---|---------|--------------------|
| 1 | **Output contract** — exactly one file, no prose, no fences, first character is the file's first character | A convention requested in prose is honoured differently by different models. This is the single largest source of unusable output |
| 2 | **The file's obligations** — its `path`, `purpose`, `declares`, `serves`, from the plan | A file generated from a filename alone is a guess |
| 3 | **Accumulated declarations** — the actual top-level symbols already defined by previously generated files | Naming the FILES is not enough. A generator told only that `helpers.go` exists will redeclare its symbols, or invent helpers that were never written |
| 4 | **The complete file set** — every path in the plan | So a file knows what it is NOT responsible for, and does not absorb another file's work |
| 5 | **Platform constraints** — language, dependency policy, idioms | From the platform blueprint |
| 6 | **Verification Checklists** — as explicit acceptance criteria, not buried in the blueprint body | A checklist present as context is complied with by luck. Present as criteria, it is complied with on purpose |
| 7 | **Scope prohibition** — build the declared obligations and nothing else | Below |
| 8 | **The blueprints themselves** | The specification being implemented |

### Scope discipline

A generator MUST instruct the model to produce ONLY what the plan declares for
that file. It MUST NOT invite, and SHOULD explicitly forbid:

- endpoints, routes or handlers not named in the plan for this file
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

Every file in the plan exists; every symbol it said it would declare appears;
every endpoint it said it would serve appears. Answerable in milliseconds, and
localises a failure to one file.

**Layer 1 is a pre-filter, not the authority. Layer 2 is.** The costs are
asymmetric: a false rejection here discards the file and spends the retry budget,
and a run has died at eleven of twelve files over one — while a false acceptance
is caught by the build minutes later. So Layer 1 SHOULD be permissive and MUST
NOT reject on ambiguity.

Concretely, a required symbol is satisfied when it appears as a parsed top-level
declaration OR anywhere in the file. A plan may legitimately name something the
implementation expresses as a struct field, a constant inside a block, or a
member of a type — none of which a top-level parse can see, and all of which are
correct.

The exception is a symbol named in method notation. `(Type).Method` states a
receiver and is therefore unambiguous, so it MUST be verified by parsing: a
substring match would accept `Method` declared on some other type, which is a
different promise from the one the plan made.

### Layer 2 — Coherence

The files agree with each other:

- every symbol is declared exactly **once** across the target
- every call site matches the declared signature
- the target builds with the plan's `build` command

**Symbol identity is receiver-qualified where the language namespaces by
receiver.** In Go, `func (s *SQLiteStore) Load()` and `func (m *MemStore) Load()`
are different methods, and two types implementing an interface both declare its
methods. Comparing bare names reports that legal arrangement as a redeclaration —
which stopped a run in which all files had generated correctly.

Layer 2 exists because a target can pass Layer 1 completely and not compile —
each file individually correct, collectively contradictory. This is the most
common failure of per-file generation and it is invisible to every other layer.

### A note on checking layers

Every defect found in this pipeline so far has been in the checking layers rather
than in a model's output or a blueprint's content, and each produced a confident,
specific, correctly formatted rejection of work that was fine.

That is the characteristic failure mode of verification: a wrong check is more
persuasive than no check. Implementations SHOULD test checking layers against
real generated output rather than fixtures alone — a fixture written by the same
author as the check inherits its assumptions, and none of these four were
reachable by a test that author would have thought to write.

### Layer 3 — Properties

The Verification Checklist of every blueprint the target was generated from.
Those assertions are the blueprint's own statement of what a correct
implementation looks like; a generator that reads a blueprint and ignores its
checklist has used half the document.

Implementations MUST check every mechanically checkable assertion and MUST
report the remainder as unchecked rather than passed. An assertion nobody
verified is not a satisfied one.

### Layer 4 — Behaviour

`architecture/testing.md` conformance, at the levels the platform blueprint names.

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

- [ ] A generator asks the model for a plan and does not impose a file structure
- [ ] A plan omitting a type the protocol enumerates is rejected, naming the type
- [ ] A plan omitting an endpoint the protocol defines is rejected, naming the endpoint
- [ ] A plan declaring one symbol in two files is rejected
- [ ] Files are generated in the plan's dependency order, dependencies first
- [ ] A generator produces exactly the files the plan declares — no more, no fewer
- [ ] A response containing prose before the file content is rejected and retried with that reason
- [ ] A wrapping code fence is stripped; a response with prose around a fence is rejected
- [ ] Each file's prompt includes the top-level declarations of every previously accepted file
- [ ] Each file's prompt includes the Verification Checklist assertions of the blueprints being implemented
- [ ] Each file's prompt forbids endpoints, configuration and dependencies not declared for it
- [ ] No file is written to disk until every file in the target has been accepted
- [ ] Layer 1 failure names the file and the missing symbol or endpoint
- [ ] Layer 1 accepts a required symbol the implementation expresses as a struct field
- [ ] Layer 1 rejects a method named in receiver notation but declared on another type
- [ ] Layer 2 detects a symbol declared in two files, and a call site disagreeing with its declaration
- [ ] Layer 2 does NOT report two methods of the same name on different receivers as a collision
- [ ] A plan naming a struct field in `declares` is corrected by the planning instructions rather than tolerated by the checker
- [ ] Layer 3 evaluates every mechanically checkable checklist assertion and reports the rest as unchecked
- [ ] A failure at any layer prevents later layers from reporting a result
- [ ] Generated file paths are validated for containment before any write
- [ ] The model, blueprint versions and the plan used are recorded with the output
