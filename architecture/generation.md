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
6. A path belongs to another component of the same target — its module, its
   entry point, or a file another component's manifest claims.

Rejection returns the specific gap and asks for a revised plan. This costs one
call and saves generating a structure that could never satisfy the blueprints.

Rule 6 exists because a tenant root is the module root, so every component a
tenant grows is planned into the same tree. Asked for a content service, a
planner given only the blueprints planned `module weblisk-tenant` over a module
already called something else, re-implemented three packages the tenant had, and
put its entry point in the orchestrator's `cmd/` directory. Twelve of
thirty-two files duplicated existing packages and one would have replaced the
component that was running.

The plan was not wrong about the blueprints. It was answering *what does a
content service consist of* when the question is *what must this tenant grow in
order to have one*. Element 9 of the prompt contract is what lets a planner
answer the second; rule 6 is what happens when it does not, because an
instruction a model may decline is not a guard.

### Reconciling a target

Generation removes files a previous run of THE SAME COMPONENT wrote that the
current plan omits, and leaves everything else alone. Three distinctions are
required, and collapsing any two of them destroys work:

| The file is | Action |
|---|---|
| In this plan | Written |
| Written by a previous run of this component, and this plan drops it | Removed — the plan is a complete statement |
| Written by a previous run, and this plan was TOLD to omit it | **Kept.** Reported as retained |
| Written by nobody — hand-edited, or another component's | Kept. Reported as foreign |

The record of what a run wrote MUST be keyed by component, not by output
directory. Keying it by directory made two components of one tenant share one
record, and the second build read the first's files as stale and deleted the
module file.

The third row is the one that is easy to miss. Element 9 tells a planner not to
plan a file that already exists; the planner complies; and a reconciler that
knows only "previously written, now absent" reads that compliance as a deletion.
Both rules are correct and their conjunction deletes a working tenant.

### Surviving a provider outage

A build takes tens of minutes and depends on a service that is sometimes
unavailable. Five tenant builds were lost to that: twice to a stream that ended
without a stop reason, once at the provider reachability check, once at file 10
of 35, once at file 32 of 35. Every one of them had banked its completed files
in the cache, and every one still needed a person to notice and start it again.

Two layers, because they answer different questions.

**Inside a call**, a failure that says it is temporary is retried with growing
backoff. The window MUST be sized for the BUILD, not for an interactive
command: it was three attempts across ten seconds, so a thirty-second outage
discarded forty minutes of work after correctly identifying the error as
temporary. About six minutes is enough for an ordinary outage and still fails
in bounded time.

**Around the run**, a failure that is the provider's resumes the whole
operation. This is not a second retry of the same call — it is the observation
that a run which reached file 32 has banked 31, so re-running it costs only
what remains. Waits are longer than the inner window, because if six minutes of
retrying did not clear it, the outage is not measured in seconds.

Both layers MUST refuse to retry what is not transient:

- A build that will not compile, a plan that will not validate, a refusal to
  overwrite an edited file — these recur identically, and looping on them
  consumes the window a real outage needs.
- A session or quota limit is measured in hours. It arrives as a 429, so it
  MUST be checked BEFORE the retryable status codes, or it is mistaken for rate
  limiting and retried until the attempts run out.

The outer loop MUST be bounded. A process that never gives up cannot be
reasoned about, and a build that has been resumed five times across an hour is
telling the operator something they need to hear.

#### A retry decision MUST be made from structure, not from text

Both layers ask the same question — is this failure transient — and that
question MUST be answered from the fields a provider fills in, never by
searching its error text for words.

This is not a preference. The policy above was written, tested and documented,
and it never fired once. Retry was decided by substring: the permanent list was
checked first and contained `permission`, and every Claude Code result envelope
contains

```json
{ "permission_denials": [] }
```

so every failure matched `permission`, was classified permanent, and was
returned immediately. Five builds died to overloads that named themselves
temporary and asked to be retried. The tests passed throughout, because they
were written against hand-composed error strings that did not carry the field
that broke it.

A generator MUST therefore:

- Represent a provider failure as a **value with named fields** — upstream
  status, terminal reason, subtype, and the human message — not as a formatted
  string. The envelope MUST be retained for diagnostics and MUST NOT appear in
  the error's own text, because anything in that text can decide a retry.
- Decide from the **status code** where one was given. A status the provider
  named that is not a declared transient status is the request's problem, and
  asking again changes nothing.
- Recognise a stream that ended without a stop reason by its **terminal
  reason**, since it carries no status at all.
- Fall back to matching words ONLY when the provider gave nothing structural,
  and then match the **human message alone**.
- Test the classifier against **captured real failures**, kept as fixtures in
  the shape the provider actually sends — including every field nobody thought
  about. A retry policy proven only against invented strings is not proven.

The declared transient statuses are 408, 409, 425, 429, 500, 502, 503 and 504,
together with 529 for overload. A session or quota limit is settled from the
message before this table is consulted, as stated above.

---

### A rebuild input MUST NOT be something the build changes

The plan is cached on the inputs that determine it. One of those inputs was the
tenant's *shape*, which included each package's export count — and generating
files changes export counts. So:

```
build → files written → export counts change → shape changes →
plan cache misses → the model re-plans → it names things differently →
every file declaring the old names is non-compliant → regenerate → repeat
```

The plan cache could never hit after the first successful build, and a rebuild
that should have cost nothing cost twenty files. One measured run regenerated
ten files whose only fault was that the plan had been re-derived since they
were written.

A generator MUST therefore key a plan only on inputs the build does not
produce: the requirements, the target, the platform, the platform blueprint and
the instructions.

**The test to apply to a candidate key input is not "is it structural?" but
"can a build produce it?"** Anything a build can produce is a feedback loop
whatever else it is.

Applying the wrong test cost two rounds. The export count went first, and the
module path was left — and the build writes `go.mod`, so the first run saw no
module, the second saw one, and the plan was re-derived on the second run of
every tenant that had ever been built. Measured directly: `""` then
`"tenant-v7"`.

Neither is a plan input in any case. A plan decides which files exist, what each
declares, what each serves, and in what order. The module path decides **import
statements**, which is file content — and a file is keyed on its whole rendered
prompt, so a module rename already invalidates every file precisely, without
disturbing a plan that was correct before it.

What remains is the package directories, their names, and who owns them. Those
change only when something has really moved.

Tenant exports still reach the per-file prompts, where the names matter.

This is the difference between an incremental build and a build that merely
starts from a cache: an input that the output perturbs is a feedback loop, not a
key.

### A name MUST come from the blueprint that declares it

The plan chooses the symbols every generated file then depends on, so a name
changed between two generations of the same blueprints makes every dependent
file stale and rebuilds work that was correct. One measured orchestrator build
regenerated ten compliant files for this reason.

**This pipeline holds no naming convention of its own.** Names are declared in
the blueprint that specifies the thing, and the rules are in
[`schemas/common`](../schemas/common.md#declared-names):

| What | Declared in |
|---|---|
| A type | the `## Types` section of its blueprint |
| An endpoint | the `Operation` column of the serving component's `## Endpoints` table |
| A store operation | the store contract's operations list |
| An event topic | the topic table of the publishing blueprint |
| An error code | the central code registry |
| The spelling of any of these in a language | that platform's `### The HTTP Surface` mapping table |

A generator MUST read those declarations and pass them to the model as
requirements, and MUST validate the plan declares them. It MUST NOT restate them
here in different words.

This section previously did restate them, and got it wrong: it said a store
operation should be named "the noun is the type and the verb is the operation —
`Get`, `Put`, `List`, `Delete`", while
[`architecture/storage`](storage.md#interfaces) had all along declared
`GetAgent`, `PutAgent`, `ListAgents`. The pipeline had acquired a naming opinion
that contradicted the specification, and a plan following either one was
non-compliant with the other. A rule copied into a second place is a rule that
will disagree with itself.

Where a name cannot be found in any blueprint, that is a gap **in the
blueprint**. It MUST be reported as one and MUST NOT be filled in.

### A coherence fault MUST be caught where it is created

A symbol may be declared by exactly one file. That was checked after every file
had been generated — so a thirty-one-file build completed and was then discarded
whole, because file nine and file ten both declared `EncodePublicKey`.

The per-file contract check **caused** the collision the final check could not
see:

1. The plan assigned `EncodePublicKey` to `sign.go`.
2. `keys.go` was generated first and declared it anyway. Nothing objected —
   the check only asked whether a file declared what its OWN entry named.
3. `sign.go` was generated correctly, without it, and was **rejected** for not
   declaring what its plan entry requires.
4. The retry complied. Both files now declared it.
5. Thirty minutes later the coherence check reported the duplicate and the run
   was thrown away.

Every step behaved as specified and the result was a guard manufacturing the
fault it was too late to catch.

So a generator MUST check, as each file is produced, that it declares no symbol
belonging to another file — from the plan for a file not yet written, and from
what has been written for a symbol the plan did not name. The complaint MUST
name the owning file, so the retry has somewhere to import from rather than a
prohibition it can only guess at.

The final check stays. It is the backstop, and a backstop that fires means the
per-file check has a hole; it must not be the first thing to notice.

More generally: **a check MUST run at the point where its fault can still be
repaired cheaply.** A correct answer delivered after the work is discarded is
worth less than a wrong one delivered early, because the early one is retried
and the late one is not.

### One question MUST have one implementation

"Does this file still declare what the plan says it declares" was answered in
two places. The generation-time check resolved method notation properly —
`(*Registry).Load` against a declaration parsed as name `Load` with receiver
`Registry`. The rebuild decision re-implemented it by indexing bare names and
looking up the plan's spelling directly, so **every method in every plan read as
missing**. On one orchestrator build, nine of one file's twenty-two reported
gaps were present in the file, and eight other files failed the same way.

Where two code paths ask the same question of the same artifact, they MUST share
one implementation. The wrong second copy is invisible: it produces a plausible
answer, and the correct copy passing its tests says nothing about it.

---

### Deciding whether a file must be rebuilt

A rebuild is not "generate everything again". It is a decision made per file,
and the default answer is KEEP. Regenerating a file that still satisfies its
obligations costs a model call, produces bytes nobody needed, and hides the
files that did change among the ones that did not.

A generator MUST record, for each file it writes: the plan entry that produced it
(`path`, `purpose`, `declares`, `serves`), the digest of the file as written, the
digest of each blueprint the file was generated from, and the bindings and
checklist assertions that file is answerable for. One digest over a whole prompt
is not sufficient — it can answer *did anything change* and cannot answer *did
anything I depend on change*, which is the only question worth asking.

The decision, in order, and the first matching row wins:

| Condition | Action |
|---|---|
| The file is absent | **Generate** |
| Its digest differs from the recorded digest | **Refuse.** It was edited outside generation. Report it and generate nothing |
| It no longer declares every symbol its plan entry declares, or no longer serves every endpoint it is assigned | **Generate** — it is out of compliance with the blueprints regardless of what changed |
| A blueprint it was generated from changed, AND the change touches a binding or an assertion this file is answerable for | **Generate** |
| A blueprint it was generated from changed, and the change touches nothing this file is answerable for | **Keep**, and report that it was assessed and kept |
| Nothing changed | **Keep** |

Row two is not a nicety. A file generation wrote and a person then edited is
invisible to a reconciler that only knows "written previously, absent now" —
so without this rule a rebuild silently destroys hand work and reports success.
An edited file is reported and left alone; adopting the edit or discarding it is
a decision for whoever made it, and the generator's job is to make sure they are
asked.

Row three is what makes KEEP safe. A file is not kept because its inputs look
unchanged; it is kept because it was inspected and still meets its obligations.
Provenance says a file *should* still be right. Only the file says whether it is.

Rows four and five are [`architecture/change-management`](change-management.md)'s
impact assessment applied to generation: a blueprint diff is mapped onto the
declared bindings of each dependent, and only what the diff actually reaches is
regenerated. This is why bindings are declared at field granularity, and why a
dependency present in `requires:` and absent from the Dependencies block breaks
more than tidiness — a file answerable for a binding nobody declared cannot be
assessed, so it must be conservatively regenerated every time.

Until the cascade is implemented, an implementation MAY treat any change to a
blueprint a file was generated from as reaching it. That is sound and blunt: it
never keeps a file it should have rebuilt, and it rebuilds many it should have
kept. It MUST NOT be described as incremental.

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
| 9 | **The tenant's existing state** — module path, the packages already present with their exported names, and which component owns which file | A component is almost never the first thing in a tenant. Without this a generator re-declares what it could import, and names the module something the tenant is not |

| 10 | **How a blueprint is read** — which sections bind, which are illustrative, and how each is parsed | A generator that sends a specification without saying how it is structured has asked the model to infer the document's own rules from the document. It infers differently each time |

### How a blueprint is read

A blueprint is not prose with some structure in it. Every section has a
**form**, declared by the schema that governs its type — see
[`schemas/common`](../schemas/common.md#section-form) — and a generator MUST
convey what each form means:

| Form | What it is | How it binds |
|---|---|---|
| `yaml:<root>` / `yaml` | the contract, in a fenced block | **Every key is required output.** The prose around it explains; the block specifies |
| `table` | uniform rows, columns named in the header | **Every row is required output.** Columns are read by NAME — a column's position carries no meaning |
| `narrative` | prose | context, EXCEPT as below |

And the rule that catches what the forms do not:

> **A sentence containing MUST, MUST NOT or SHALL is binding wherever it
> appears** — including inside a narrative section, a note, or a parenthesis.

That rule exists because the machine-readable parts are extracted and elevated
into the prompt — types as bindings, endpoints as obligations, the Verification
Checklist as acceptance criteria — while a normative sentence in a body
paragraph reaches the model only as one line in seventy thousand tokens of
context. "The audit log MUST be chained" is not in any table. It is still the
specification.

A generator MUST also convey what is NOT binding, or a model treats an
illustration as a requirement:

- A fenced block with **no root key** in a section whose form is `yaml:<root>`
  is an example. The block carrying the declared root is the contract.
- A path, name or value inside a narrative example is illustrative unless a
  table or a `yaml` block also declares it.
- A section a blueprint marks Optional is not required by its absence.

**Where two statements disagree, the more specific document wins**: a
component's own blueprint over a pattern it adopts, a pattern over the schema's
example. If neither is more specific, that is a corpus fault and MUST be
reported rather than resolved by the model — see "A name MUST come from the
blueprint that declares it".

Element 9 is a statement of FACT, not of policy — what exists, not what is
allowed. That distinction is why it belongs in a prompt at all: the blueprints
cannot know what a given tenant contains, and everything else in this table is
derived from them.

It carries a cost that is worth stating. Exported names belong in the invariant
prefix, so a run pays for them once rather than per file; and the PLAN's cache
key must be derived from the tenant's shape — module, package directories,
owners — and not from the export text, or every component in a tenant re-plans
whenever any other one gains a constant.

A component MUST NOT be shown its own previous output as existing state. That
output is what the run replaces, and presenting it tells a regeneration its own
types already exist somewhere it must not re-declare them.

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

### Repairing a disagreement between files

A build failure names a file. The fix does not always live in it.

    internal/storage/store.go:143:9: cannot use p (variable of type
    *jsonlPersister) as persister value in assignment: *jsonlPersister does
    not implement persister (wrong type for method load)

The interface is in `store.go`; the method that does not match is in
`jsonl.go`. A generator asked to rewrite `store.go` alone can only change the
interface to match whatever it believes the implementer looks like — and asked
next round to rewrite `jsonl.go`, it changes the method to match the interface
it just saw. Each rewrite is locally reasonable and the pair never agrees. A
real build reported the same three errors on rounds 3, 4 and 5 and stopped.

**A contract between files MUST be repaired across those files in one
response.** A generator MUST therefore:

1. **Resolve an error to every file it implicates**, not only the file it names.
   An unsatisfied interface implicates the file declaring the interface and the
   file declaring the concrete type. A symbol declared twice implicates both
   declaring files. An undefined symbol implicates whichever file owes it —
   which is usually not the file that called it.

2. **Ask for those files together**, each complete, in one response.

3. **Reject a partial answer.** A group repair exists so the files agree
   afterwards; applying half of one leaves exactly the disagreement it was meant
   to resolve.

4. **Never implicate a file the plan does not own.** Generation may rewrite only
   what it wrote.

Sending more CONTEXT does not substitute. The single-file prompt already carried
the other files' declarations, names and signatures included, and it was not
enough — the generator was being shown the conflict and given authority over one
side of it.

A single-file error MUST remain a single-file repair. Grouping liberally sends
the whole target every round, and a group is a claim that these files disagree
with each other rather than that they are all broken.

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

The checklist MUST be gathered from **exactly** the blueprints the target was
generated from — the same set, resolved once. A generator that plans from one
list, prompts from a second and grades against a third is planning against one
specification, building against another and grading against a third, and no
result it reports means anything.

Implementations MUST check every mechanically checkable assertion and MUST
report the remainder as unchecked rather than passed. An assertion nobody
verified is not a satisfied one.

#### Five outcomes, never three

Assertions are not uniformly checkable, and the interesting ones are only
**partly** checkable. "POST /v1/register enforces exclusive namespace ownership
(409 on conflict)" contains a structural claim a parser settles — is a handler
routed there — and a behavioural claim it cannot. Reporting the assertion as
passed because the route exists is a confident wrong answer, which is worse than
an honest gap. Reporting it as unchecked discards a cheap detection of a definite
fault.

So a check MAY be **one-way**: it tests a necessary condition, so failure is
conclusive and success is not. Every implementation MUST report five outcomes:

| Outcome | Meaning |
|---|---|
| `verified` | a check settles the assertion, and it holds |
| `failed` | a check settles it against the artifact, or a necessary condition is unmet |
| `necessary` | a necessary condition holds; the assertion is NOT established |
| `not-applicable` | the assertion is conditional and its premise is established false |
| `unchecked` | nothing mechanical applies |

`necessary` MUST NOT be counted as `verified`, and MUST NOT be folded into
`unchecked` — the first is the fault this layer exists to prevent, the second
discards a real result. Only `failed` may drive a repair.

`not-applicable` MUST NOT be folded into `unchecked` either. They call for
different things: an unchecked assertion needs a human to look at it and an
inapplicable one needs nobody, so folding them inflates the review queue with
work that does not exist.

#### Conditional assertions

An assertion whose obligation depends on a choice MUST be written `IF premise:
obligation` and MUST be evaluated only when the premise holds.

platforms/go.md: *"IF SQLite was chosen: WAL journal mode, `user_version` pragma
for migrations, tables created with `CREATE TABLE IF NOT EXISTS`"*. Evaluated
unconditionally, that assertion fails every implementation that took the JSONL
default the same blueprint recommends — a failure for making the recommended
choice.

A premise MUST be settled by an explicit test or not at all. Where nothing
settles it, the assertion MUST be reported `unchecked` **with the premise
quoted**, never `not-applicable`: guessing that a premise is false is how a
checking layer begins silently forgiving requirements, which is worse than the
false failure it would be avoiding.

#### The specification is the authority, not a copy of it

A check that compares an artifact against a table, a code registry or an enum
MUST read that table from the blueprint. It MUST NOT carry its own transcription.

protocol/types.md lists every protocol error code with its HTTP status and
category. A checker holding a second copy of that table has created a second
thing to keep right, and the two disagree the moment either moves — at which
point the tooling is grading implementations against a specification nobody
maintains. Reading the blueprint means a corrected table corrects every check
that depends on it.

#### Structure, not substrings

A check MUST derive its answer from the artifact's structure — its parse tree,
its module manifest — and MUST NOT rely on a substring search where structure is
available. A search for `Retry-After` passes on a comment mentioning
`Retry-After`; a search for `/v1/audit` passes on an error message quoting it.
Where only a substring check exists, it MUST be treated as one-way.

An artifact that does not parse MUST contribute no structure. Inventing structure
from broken source makes Layer 3 disagree with Layer 2, and Layer 2 is the
authority.

#### A failing assertion names its file

A check that refutes an assertion MUST report which artifacts the failure is
about, and that attribution MUST come from the check itself — the only thing that
knows why it failed. A separate attribution pass is a second answer to the same
question, free to drift from the first.

An assertion that names no generated artifact MUST be reported rather than
assigned to a plausible one. A repair aimed at the wrong file edits correct code
to satisfy something it does not control.

#### The loop ends when verification passes

Layer 2 succeeding is not completion. A generator MUST continue while any
assertion is `failed`, and MUST stop when the count of failures stops falling.
Build errors and failing assertions MUST be counted separately: errors falling to
zero and assertions then appearing is progress, and one counter reads it as a
regression precisely when the loop begins doing the more valuable half of its job.

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
- [ ] A transient provider failure inside a call is retried across a window measured in minutes, not seconds
- [ ] A transient failure of the run resumes it, reusing every completed file from cache
- [ ] A session or quota limit is never retried, and is recognised before the retryable status codes
- [ ] A build, plan or refusal failure is returned rather than retried
- [ ] The outer resume is bounded, and says how many attempts it made
- [ ] An unsatisfied interface implicates the file declaring the interface and the file declaring the concrete type
- [ ] A symbol declared twice implicates both declaring files
- [ ] An undefined symbol implicates the file that owes it, not only the caller
- [ ] Files implicated together are asked for in ONE response and a partial answer is rejected
- [ ] A file the plan does not own is never implicated
- [ ] An ordinary single-file error is repaired as a single file, not as a group
- [ ] A file whose digest differs from the recorded digest is reported and NOT overwritten
- [ ] A file that no longer declares its assigned symbols is regenerated even when no input changed
- [ ] A file whose blueprints are unchanged and whose obligations are met is kept, and reported as assessed
- [ ] The per-file record carries the digest of each blueprint the file was generated from, not one digest over the whole prompt
- [ ] An implementation that regenerates on any blueprint change does not describe itself as incremental
- [ ] A plan naming another component's module file, entry point or owned file is rejected, and the rejection names the owning component
- [ ] A plan is judged against the CALLER's target, never a target the model declared in its own output
- [ ] A file a previous run wrote and this plan was instructed to omit survives reconciliation and is reported as retained
- [ ] A file a previous run wrote and this plan genuinely dropped is removed
- [ ] The record of what a run wrote is keyed by component; two components in one tenant never share one record
- [ ] A generation prompt states the tenant's module path and the exported names of packages already present
- [ ] A component is not shown its own previous output as existing tenant state
- [ ] A plan is not re-made because an unrelated component gained an exported name

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
- [ ] The checklist is gathered from exactly the blueprint set the target was generated from
- [ ] Five outcomes are reported: `verified`, `failed`, `necessary`, `not-applicable`, `unchecked` — `necessary` and `not-applicable` are folded into none of the others
- [ ] A conditional assertion is evaluated only when its premise holds; an unsettled premise leaves the assertion unchecked with the premise quoted
- [ ] Checks that compare against a table, registry or enum read it from the blueprint rather than from a transcription
- [ ] Structural checks read the artifact's parse tree; substring checks are treated as one-way
- [ ] An artifact that does not parse contributes no structure to any check
- [ ] Each refuted assertion names the artifacts it is about, attributed by the check that refuted it
- [ ] The loop continues while any assertion is `failed` and stops when the failure count stops falling
- [ ] Build errors and failing assertions are counted separately for progress
- [ ] A failure at any layer prevents later layers from reporting a result
- [ ] Generated file paths are validated for containment before any write
- [ ] The model, blueprint versions and the plan used are recorded with the output
