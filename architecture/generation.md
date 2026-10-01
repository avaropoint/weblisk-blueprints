<!-- blueprint
type: architecture
name: generation
version: 1.2.0
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
    version: ">=2.0.0 <3.0.0"
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

languages/go.md: *"IF SQLite was chosen: WAL journal mode, `user_version` pragma
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
assertion is `failed`, and MUST stop when two rounds in a row fail to improve on
the best tree it has reached — see *A repair round is a transaction*. Building
and conforming MUST be ranked as separate stages, with every tree that builds
above every tree that does not. Errors falling to zero and assertions then
appearing is progress; a single counter reads it as a regression just when the
loop begins the more valuable half of its job.

#### A repair round is a transaction

A repair round rewrites several files against several requirements, and a repair
that is right for its own requirement can be wrong for the tree. A
content-service build reached a tree that compiled, ran, and satisfied 97
assertions with 69 unmet. One round then repaired fourteen files, each against
its own unmet assertion and each shown only its own source. One repair removed a
struct field that other files read; another left a helper with a signature that
five call sites did not match. The tree stopped compiling, the next round made it
worse, and the run ended on the broken tree. The working tree existed nowhere,
because nothing had kept it.

A generator MUST treat every repair round as a transaction:

1. **The tree the round starts from is kept**, with what was measured about it,
   so it can be put back exactly. Every repair in the round is asked for against
   that tree. None is kept, recorded as generation's output, or banked until the
   round is judged.

2. **Only a change is tried, and a repair is told what became of the last
   one.** A repair that returns its file unchanged MUST NOT be tried. A round
   left with nothing to try counts as a round without progress, and it is not
   measured. Measuring it reads the same tree again, and a reader can answer
   differently for one tree read twice: a luckier second reading of an
   unchanged tree became the best tree and reset the count of rounds without
   progress.

   The prompt for a file whose latest repair was not kept MUST say why. Where
   that repair was built, the prompt MUST also list the errors its build
   reported that the tree it was tried on did not; a long list may be cut short
   if it says how many were left out. A repair of the file that is kept clears
   this. An undone round puts back the tree it started on, so without this the
   next round's prompts are byte for byte the ones that produced the repair just
   undone, and a model that answers one prompt alike twice returns the same
   repair to be undone again.

3. **The round is judged against where it started.** After its repairs are
   applied, the tree is built and, if it builds, run and verified again. The
   round is **worse** when, against that tree:

   - dependency resolution that succeeded now fails;
   - a tree that built no longer builds;
   - a failing build got further from compiling. Either a package both builds
     show has more errors, however much another package improved; or a package
     the earlier build showed is one the later build hides; or the build now
     fails in a way whose distance from compiling cannot be read where before
     it could. See *Ranking failing builds* below;
   - a component that started no longer starts;
   - a conformance test that was holding now fails.

   A test is **holding** when its last answer on the line of kept trees was a
   pass. A test that passed and then gave no answer (it timed out, or the
   component stopped answering it) is still holding: an inconclusive outcome
   establishes nothing, so it does not clear the pass before it. Judged against
   the previous tree alone, one change can take a test from passing to
   unreachable, which is allowed, and the next can take it from unreachable to
   failing. Neither step then looks like a passing test broken.

   **Revealed or made, a package shown worse is worse.** A round, and each
   repair tried on its own in the retry (rule 4), MUST be undone when any
   package both builds show has more errors than it had on the tree the round
   started from. This holds even where the same change made an error in that
   package go and the new errors stand at lines it did not alter. No error is
   exempted as revealed rather than made.

   The type checker hides errors as a failing package hides its importers.
   Given `cfg := loadConfg()`, the compiler reports the undefined name and
   nothing about `cfg`, whose type it never learned, and fixing the typo
   reveals "cfg.Host undefined" and "cfg.Port undefined". No count of
   diagnostics tells an error a change revealed from one it made, and an
   exemption for the revealed kind let one package's improvement carry another
   package's regression into the best tree.

   The rule costs such a fix a round, not the fix. The prompt for the undone
   repair's file lists the errors its build reported (rule 2), so the next
   repair is shown them and can put them right along with the typo. Where what
   a fix reveals stands in a file the fix did not change, no repair of the
   fix's own file alone can be kept, and that package stays as the tree before
   showed it.

   **Losing sight of a package is not progress.** A package the earlier build
   showed, which the later build hides, MUST count as worse, never as
   unchanged. That holds when a round is judged, when a repair is tried on its
   own in the retry, and when two trees are ranked (see *Ranking failing
   builds* below). Hidden, its errors leave the count without one of them
   being fixed. Where it is hidden because a package it imports went from
   compiling to failing, that package is shown on both builds with more
   errors, and the round is undone for it already. But a change that adds an
   import of a package that already fails hides the importer, and every
   package that imports it in turn, while no package shown on both builds
   rises. Counted as unchanged, such a round could be kept for what it fixed
   elsewhere, and whatever it did to the packages it hid would reach the best
   tree unseen.

   More assertions read unmet also makes a round worse, but only when nothing
   observed shows the round did any good, that is, when no fewer conformance
   tests count against the tree. Such a round MUST be undone and MUST NOT be
   retried one file at a time. The retry judges only what is observed, so it
   would keep every repair and rebuild the tree the round was undone for. None
   of its repairs is kept, and the next round asks again from the tree the
   undone round started on.

4. **A worse round is undone, then retried one file at a time.** The kept tree
   is restored, and the round's repairs are applied one at a time. These are the
   same responses, with no new model call. Each repair MUST be judged against
   the tree the retry has kept so far, and kept only if that tree is no worse
   for it. In particular, no conformance test that was holding at the start of
   the round, or on any repair kept since, may fail. A repair that fails this is
   discarded, and its requirement is reported as unrepaired, with the reason.

5. **A repair MUST be shown the uses of what its file declares.** For each
   package-level name a Go file declares (type, field, function, method,
   variable, constant), and each export of a JavaScript or TypeScript file (the
   forms below), the repair is given every place another file uses it. Being
   shown the uses gives a single-file repair no authority over them. Where a
   build of the trial shows its change breaking them, the repair is discarded,
   and the change belongs to a repair across those files — see *Repairing a
   disagreement between files*.

   A break no build shows is not caught. A Go change whose broken uses sit in
   an importer that a failing package hides, on the tree before and on the
   trial alike, moves no count, and nothing undoes its round for it. A later
   round that lets the build reach those uses, without touching the importer,
   is not charged with them either: they stand in a package the build before
   it hid, and its own change did not make them (see *Ranking failing builds*
   below).

   What a file in any other language declares is not read. Such a file is shown
   no uses, no change to it is refused before a trial, and no error is charged
   to its change as one the change made.

   **An error is charged across files only through a dependency.** An error
   that stands in one file MUST be charged to a change in another file only
   through a dependency the generator establishes from the source. The file
   holding the error imports the changed file or its package, or is in the
   same Go package, and the error's line uses, through that import or package,
   a declaration the change removed or re-signed. A word on the line that
   matches the name MUST NOT be enough. The same word can be a field of
   another type, a local variable, or a name another file declares, and an
   error there is not the change's. A language whose imports the generator
   cannot read MUST charge nothing across files, and an import it cannot
   place, such as a path alias or a package name, establishes nothing. What a
   charge does to the count is in *Ranking failing builds* below.

   Some builds do not check where another file uses a name. Here that means
   JavaScript and TypeScript, whose build may bundle or may not exist. For those
   languages a repair MUST be refused before any trial when either of these
   holds:

   - it removes an export another file uses;
   - it imports, from another planned file, a name that file does not export,
     unless the tree before already had that same import of that same missing
     name.

   The refusal MUST name the export or import and where it is used. Each repair
   MUST be judged twice:

   - alone, against the tree the round started on;
   - against that tree with every repair already kept this round applied.

   A repair that clashes with an earlier one is refused, and the earlier one
   stands. Every prompt in a round is built from the same tree, so one repair
   naturally leans on a name another removes. It is judged alone as well because
   an undone round retries its repairs on whatever subset was kept.

   The export forms read are:

   - declarations: function, class, interface, type, enum, namespace, written on
     one line or across lines;
   - every name a const, let or var export binds, destructured patterns
     included;
   - export lists and re-exports;
   - `export * as ns from`;
   - CommonJS `exports.a =`, `module.exports.a =`, `exports['a'] =` and
     `module.exports = { … }`;
   - the default export, however written (`export default`,
     `export { x as default }`, `export =`, `module.exports = x`). It is used
     wherever an importer binds the default (`import d from`,
     `export { default } from`) or takes the whole module, which means
     `require(…)` and `import(…)`;
   - `export * from`, which is used wherever an importer binds names. A
     namespace import (`import * as ns from`) binds names; it does not take the
     whole module.

   These are not read, and an implementation MUST NOT claim them:

   - an export made by a call: `Object.assign(module.exports, …)`,
     `Object.defineProperty(exports, …)`;
   - a use through an import this pipeline cannot place: a path alias or a
     package name;
   - the default read through a namespace import as `ns.default`. A repair that
     removes `export default` while an importer reads `ns.default` is not
     refused;
   - the default a CommonJS module is to an importer (below). It is not an
     export a repair can be refused for removing, so a repair that rewrites
     such a module as an ES module with no default is not refused.

   A named import is never said to be missing from a file whose exports cannot
   be closed: one that has `export * from`, an export made by a call, or
   `module.exports` assigned anything but an object literal. A default import
   is said to be missing only from an ES module, meaning a file with an
   `export` statement, that has no default and no CommonJS export. A CommonJS
   module is its own default, so a default import of one is never said to be
   missing, and neither is a default import of a file that exports nothing.
   `export * from` does not pass on a default, so a file that has it and no
   default of its own lacks one like any other ES module. A changed signature
   is not detected in these languages.

6. **A package clash is repaired where it is.** The toolchain reports two
   package clauses in one directory at the line that imports that directory, so
   it names a file that cannot fix it. "found packages A (f1) and B (f2) in DIR"
   MUST be asked of `DIR/f1` and `DIR/f2` together (of whichever of them the
   plan holds), and each must be shown what package every file in the directory
   declares. An importer blamed only for such a clash is not asked. A clash left
   unrepaired is listed against its files.

7. **The run ends on the best tree it reached, never on the last.** Trees are
   ranked in this order:

   - one whose dependencies resolve beats one whose do not;
   - one that builds beats one that does not;
   - when neither builds, the build that is further along — see *Ranking
     failing builds* below;
   - one that starts beats one that does not;
   - then fewer conformance tests count against it. That means those that fail
     on it, and those the other tree answered and it does not. Silencing a
     failing test ties with failing it, and silencing a passing one loses to
     passing it;
   - then, only between two trees whose assertions were both read, fewer
     assertions reported unmet, and then more assertions satisfied. Where
     either tree's assertions were not read, the two tie here. A reading that
     failed reports nothing unmet. Counted, it would outrank a read tree with
     unmet assertions, become the best tree, and end the run inconclusive where
     the read tree ends it refuted.

   A tie is not an improvement. Progress is measured against the best tree, not
   the previous round. Counting against the previous round read a tree that
   built, then one with ten errors, then one with twenty, as a stall rather than
   the regression it was. Two rounds in a row that do not improve on the best
   tree end the run.

   A round that is not worse is kept and becomes the base for the next round,
   whether or not it beat the best tree. A tree that reads nothing left to
   repair but is not the best MUST NOT end the run as complete. The best tree is
   put back and the loop repairs from there, bounded by the stall count and the
   round ceiling. A component that stopped answering every test can read with
   every assertion met.

   Unmet ranks before satisfied. The satisfied count moves with what the reader
   left unverifiable or unanswered, so ranked first it would prefer the same
   code read more decisively, with more of it refuted.

8. **Only the best tree is banked, and only a tree the loop accepted is
   recorded.** A repair is remembered because the tree it belongs to was the
   best measured, not because it was received. The cache holds the best tree's
   files, so a re-run, a resumed run included, starts from it.

   The record of what generation wrote MUST move only when the disk holds a tree
   the loop accepted:

   - a round that was kept;
   - a repair the retry kept;
   - the tree a round started from, put back after an undo;
   - the best tree, put back during the run or at its end.

   A prepare step that rewrites a file the pipeline wrote (`go mod tidy`
   rewriting `go.mod`) records that rewrite and nothing else. So an interrupt
   while a trial is on disk leaves the trial's files refused as changed since
   generation wrote them. An interrupt anywhere else leaves the record
   describing the tree on disk.

9. **What was not repaired is said.** The run MUST list every requirement still
   unmet on the best tree, with a reason:

   - dependency resolution that fails;
   - build errors, a package clash against its files;
   - a startup failure;
   - each conformance test that fails on it;
   - each test that failed on an earlier tree and has given it no answer since
     ("owed");
   - each test that passed on an earlier tree and has given it no answer since;
   - each assertion still read unmet.

   Where the latest repair aimed at a requirement was discarded or refused, the
   reason is what decided that: the build error it caused, the test it broke,
   the shared name it changed or the missing name it imports and where that name
   is used, that it returned its file unchanged, or that its round was read
   worse and undone whole. The reason given for a requirement MUST come from the
   latest attempt at it, so a repair kept in a later round clears the reason an
   earlier attempt was discarded.

10. **Whatever ends the loop, the best tree is what it leaves.** That includes
    completion, no progress over two rounds, the round ceiling, a failure no
    repair can be aimed at, assertions that cannot be read, and an error such as
    a provider failure or a failed write. The loop MUST leave on disk the best
    tree it reached, return it, record it, and describe it in the verdict. When
    the one-file-at-a-time retry ends on an error after keeping repairs, the
    tree it kept has been measured, and it MUST be considered for best before
    the loop ends.

    When the last build was of another tree, the best tree MUST be built again
    once it is back on disk and before the loop returns. The build directory and
    the verdict then both reflect an observation of the tree returned.

    - Where the rebuild stops at a different stage than the tree was measured at
      (dependencies, build, start), the rebuild is the answer, in either
      direction. A tree that was built, started and died is refuted, because
      that was observed. Any other disagreement is unchecked, because nothing
      was read against the tree as it now stands.
    - Where it stops at the same stage, what the rebuild observed (the
      diagnostics, the startup failure, the conformance tests) is the answer for
      everything it observed. The assertions, which a rebuild does not read, are
      kept from the measurement. A test that failed when the tree was measured
      and gives the rebuild no answer is still owed.

    The list of what is unrepaired is derived from the same observation.

    A write that fails part-way leaves neither tree on disk, and the loop MUST
    NOT treat the tree it last wrote successfully as the tree on disk. Where the
    loop cannot put the best tree back, its error MUST say so. No file the disk
    holds differently from what the loop returns may be recorded as generation's
    output, with one exception: a file a prepare step rewrote while the disk
    held the tree returned, whose rewrite is recorded as item 8 says. The loop
    returns `go.mod` as the pipeline wrote it, and the disk and the record hold
    what `go mod tidy` made of it. Where the disk does not hold the tree
    returned, a prepare step's last rewrite was of another tree, and the
    exception does not apply.

    The verdict MUST say what became of each undone round: for a retried round,
    how many of its repairs were kept.

11. **The verdict follows the conformance tests too.** The verdict on the best
    tree MUST NOT be verified while a conformance test fails on it, or failed on
    an earlier tree and has given it no answer since. Either one refutes the
    tree, whatever the assertions read, met or unreadable, and the verdict names
    the tests. Read from the assertions alone, a repair that made a failing
    test's handler stop answering was read as meeting the assertion that test
    checks. The run ended "verified", and the component's own conformance run,
    seeing that test inconclusive rather than failing, let the command succeed.

12. **A build is bounded and interruptible.** A build's timeout MUST stop
    everything its build line started. An interrupt, termination request or
    hangup that stops the CLI MUST stop the build the CLI is running. A timeout
    that stops only the shell leaves the compiler holding the output open, so
    the bound bounds nothing. A build that outlives an interrupted CLI writes
    into the tenant after the command that started it has gone.

    `weblisk` does not yet meet the first of these on Windows, where it is
    released. There a timeout ends the shell that runs the build line
    (`cmd /C …`) and nothing that shell started, so the compiler runs on past
    the bound, and the CLI stops waiting for its output rather than stopping it.
    Ending the whole tree there takes a Job Object, which the CLI does not
    create. Everywhere else the build line runs in a process group of its own,
    and the timeout kills the group.

**Ranking failing builds: what hides what.** A failing build is ranked by what
hides what, not by its error count. A compiler does not report everything wrong
with a tree; it reports what it reached.

- A Go package with a parse error ("syntax error:" in cmd/compile's words) is
  never type-checked, so only its syntax errors are seen. A scanner error (an
  unterminated string, an invalid character, an unterminated comment, an unknown
  escape) is not a parse error. The package is type-checked, its type errors are
  reported beside it, and they are counted with it.
- A Go package that does not compile hides every error in the packages that
  import it, directly or through another.

So each package is judged by what its own build could show of it, and two builds
are compared package by package. What hides what is read for Go only; a build in
any other language is compared as *Other builds* below says.

- A package both show is compared with itself: every error when both show every
  error, and its syntax errors when either shows only those.
- A package the earlier build hid, which the change did not touch, goes
  uncounted: a fix that let it be seen is not charged with what it revealed.
- A package the earlier build hid, which the change touched, is charged with
  every error the later build shows there, the most the change can have done.
  Where the later build cannot count it either, the later tree is not nearer
  compiling, whatever else improved.
- A package the later build shows less of than the earlier build did makes the
  later tree further from compiling, whatever else improved and whether or not
  the change touched it. That includes a package the later build hides
  entirely: losing sight of a package is not progress (rule 3).
- An error on the later tree at a use of a name that the change removed or
  re-signed was not revealed; the change made it. It counts against the package
  whose change made it. Only the tree a change made is charged with what the
  change made, and only a use established through a dependency is charged,
  never a word that matches (rule 5).

The ranking sums these comparisons. Undoing a round does not: one package shown
worse is a regression however much another improved, and whether the change
revealed its new errors or made them, as one holding test that now fails is. A
package the later build hides counts as worse too, whether or not a package it
imports rose to hide it (rule 3).

**Other builds.** A build in any other language is not read for what hides
what. No directory hides another, and nothing in a directory is hidden behind
a syntax error, so two of its failing builds are compared directory by
directory, each on the plain count of the diagnostics that name a planned file
there. A fix that lets such a build reach errors in another directory has them
counted against that directory, and its round is undone for them.

A diagnostic names a file only when its line begins with the file's path and
line, as `path:line: message` or `path:line:col: message`, which is how Go's
tools write it. Measured 2026-10-01 on real output, neither of the corpus's
other compilers writes that. cargo, the build in
[`languages/rust`](../languages/rust.md), puts the position on a line of its
own beneath the message (`--> server/src/main.rs:2:13`). `tsc`, which
[`platforms/node`](../platforms/node.md) builds with, writes
`src/a.ts(1,7): error TS2322: …` when its output is piped. Each of their failing
builds therefore names no file the plan owns. It ranks with the failures below,
and a loop whose current tree fails that way stops, because no repair can be
aimed at it.

A failure whose distance from compiling cannot be read ranks below every failure
that can, and two such failures tie. These are:

- a package-loading failure, wherever the toolchain attributes it;
- a failure that names no file the plan owns;
- a dependency fault;
- a build stopped at its timeout.

A Go package-loading failure MUST be recognised by where the toolchain reports
it, not by its words. The compiler reports every error under a "# importpath"
line naming the package. The go command's loader reports before any package is
compiled, under no such line. A Go diagnostic under no such line is a load
failure when it stands at a line the loader reads:

- a file's package clause and imports;
- any line of a file whose header does not parse;
- a `//go:embed` directive;
- or any line of a file the plan does not hold.

A load failure that names no position ("found packages … in DIR", "import cycle
not allowed") is recognised by its words. The words are matched on every line
of a build's output, positioned or not and under a "# importpath" line or not,
so a compile error that quotes them is read as a load failure too, and its
build ranks as one whose distance from compiling cannot be read. Measured with
go1.27.1, `cannot use "no Go files in" (untyped string constant) as int value
in variable declaration`, standing under its package's "# importpath" line, is
read that way.

Words alone do not find the rest. Measured with go1.27.1, each of the following
names a planned file and line, hides every type error in the build, and was
missed by a list of phrases:

- "use of internal package … not allowed";
- "case-insensitive import collision";
- "pattern P: no matching files found";
- go/build's "expected ';', found …" in an import block.

`go vet` also prints its findings under no header. A finding in a function body
is no line the loader reads, and is counted as the finding it is. The plan's
build line is what is run, so this has to hold for any line a platform blueprint
may give.

**The counts must be whole.** A compiler that stops at ten errors in a
dependency package pins every comparison at ten. The `have` and `want` lines
printed beneath a mismatched call are one error, not three. Error counts used to
judge a round MUST be uncapped, in every package the build compiles, and MUST
count each diagnostic once. Output naming no file beside real diagnostics is the
build commenting on them, and is not counted.

**Assertions judged by a model are the least reliable of these readings**,
because the same tree read twice can differ, so they rank last. The
one-file-at-a-time retry is judged only on what is observed: the build, the
running component and its conformance tests.

### Layer 4 — Behaviour

`architecture/testing.md` conformance, at the levels the platform blueprint names.

---

## Security


```yaml
security:
  trust_model:
    description: |
      A model's output is untrusted input. Where a blueprint came from a
      marketplace, the file paths in a response are attacker-influenced, so
      generation treats what it receives as data to validate rather than
      instructions to follow. The generator is given a specification and nothing
      else: no key material, no tenant content, no instance state.

  boundaries:
    - boundary: Blueprint corpus → Generator. The specification and the platform
        binding are the only inputs
    - boundary: Generator → Filesystem. None. The generator returns text and the
        caller writes files
    - boundary: Model response → Written artifact. Every path is validated for
        containment before anything is written
    - boundary: Partial result → Target directory. Not crossed — nothing is
        written until every file succeeds

  enforcement:
    - rule: A file path in a model response is validated for containment before
        any write
      mechanism: Path resolution and containment check per `architecture/cli`,
        refusing rather than normalising a path that escapes the target
    - rule: The generator receives no secrets
      mechanism: Inputs are blueprints and a platform specification; key
        material, tenant content and instance state are not passed
    - rule: The generator holds no filesystem tools
      mechanism: It returns text. A generator able to write directly has no
        boundary between generating an implementation and doing anything else to
        the machine
    - rule: Nothing is written until every file succeeds
      mechanism: Writes are staged and committed together. A partially written
        target invites a hand repair, which converts a reproducible artifact into
        an unreviewed one
    - rule: Provenance is recorded for every target
      mechanism: Which model, at which blueprint versions, per
        `patterns/content-identity`
```
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
- [ ] The loop continues while any assertion is `failed` and stops after two rounds that do not improve on the best tree reached
- [ ] Building and conforming are ranked as separate stages; every tree that builds ranks above every tree that does not
- [ ] Assertions rank two trees only when both trees' assertions were read; otherwise the two tie on them
- [ ] Every repair round starts from a kept copy of the tree, and every repair in it is asked for against that tree
- [ ] A repair that returns its file unchanged is not tried, and a round with nothing to try is not measured
- [ ] The next repair of a file is told why its last repair was not kept and what that attempt's build reported; a kept repair clears it
- [ ] A round is worse when resolution, the build or the start stops working, a package a failing build shows has more errors, a package the earlier failing build showed is hidden on the later one, a failing build becomes one whose distance from compiling cannot be read, or a holding conformance test fails — and a worse round is undone
- [ ] A conformance test that passed and has given no answer since is still held to passing, in the retry and in later rounds
- [ ] A round, or a repair tried alone in the retry, that leaves any package both builds show with more errors is undone, even where the same change fixed an error in that package and the new errors stand at lines it did not alter
- [ ] A package the earlier failing build showed and the later one hides counts as worse, never as unchanged, when a round is judged, when a repair is tried alone, and when trees are ranked, including where what hid it is an added import of a package that already failed
- [ ] An error is charged to a change in another file only where the file holding it imports the changed file or its package, or shares its Go package, and the line uses a declaration the change removed or re-signed; a matching word charges nothing, and a language whose imports cannot be read charges nothing across files
- [ ] A round read worse, and not observed worse, is undone and not retried
- [ ] An undone round's responses are retried one file at a time with no new model call, each kept only if the tree is no worse and no holding test fails
- [ ] Every repair of a Go, JavaScript or TypeScript file is shown each other file's uses of the names its file declares; where the build cannot detect a broken use, a repair that removes a used export or imports a name not exported is refused before it is tried, judged alone and together with the round's earlier kept repairs
- [ ] A default import is said to be missing only from an ES module with no default and no CommonJS export; a namespace import binds names, and only `require` and `import()` take the whole module
- [ ] A package clash is asked of the two files that declare the packages, not of the importer the toolchain reports it at
- [ ] A failing Go build is ranked by what hides what: only a parse error hides a package's type errors, a package hides its importers, packages are compared one by one, and an error at a use of a name a change removed counts against that change; a failing build in any other language is compared directory by directory on its plain count
- [ ] A failing build that is a package-loading failure (one standing under no compile header at a line the loader reads, or one whose words on any line say so), names no planned file, is a dependency fault, or was stopped at its timeout never ranks above a failure that can be counted
- [ ] A tree that reads nothing left to repair but is not the best does not end the run; the best tree is put back and repaired from
- [ ] The run ends on the best tree reached, whatever ended it; that tree is on disk, is built again once put back when the last build was of another tree, is what is recorded, and is what the verdict describes; where the rebuild disagrees, the rebuild is the answer
- [ ] A write that fails part-way ends on the best tree or says it could not, and no file the disk holds differently from what is returned is recorded, except a prepare step's rewrite made while the disk held the tree returned
- [ ] The record of generation's output moves only when the disk holds a tree the loop accepted
- [ ] Only the best tree's files are banked; no repair is banked before its tree is measured
- [ ] The run names every requirement left unrepaired, including tests that failed or passed and then went quiet, and for each discarded or refused repair, why
- [ ] The verdict is never verified while a conformance test fails on the best tree or failed earlier and has given it no answer since
- [ ] Build error counts are uncapped and count each diagnostic once
- [ ] A build is stopped at its timeout with everything its line started, and stops when the CLI is interrupted
- [ ] A failure at any layer prevents later layers from reporting a result
- [ ] Generated file paths are validated for containment before any write
- [ ] The model, blueprint versions and the plan used are recorded with the output
