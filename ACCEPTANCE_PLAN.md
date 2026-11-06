# Accepting a generated component

> **Status: adopted by the owner on 2026-11-03, with the decisions recorded in
> [Decisions](#decisions).** It stays at the corpus root as the plan of work: a
> file under `architecture/` is a blueprint, and its MUST lines are read as
> requirements. Each part becomes normative only when it lands in the document
> [What changes where](#what-changes-where) names for it, and from then on
> that document, not this plan, is the authority.
>
> Written 2026-11-03, measured against the development tenant's rebuild in
> change `6f533b1a`, at corpus `70c923d`.
>
> **Landed (E3):** the five classes, their derivation and build acceptance in
> [`architecture/generation`](architecture/generation.md#acceptance), derived
> by [`checks/acceptance-classes.py`](checks/acceptance-classes.py) into the
> register the engine reads; the registration slot in
> [`schemas/architecture`](schemas/architecture.md#sections); `accepted` and
> per-class counts in [`schemas/run-statement`](schemas/run-statement.md#the-verdict-a-run-ends-with);
> outcome `accepted` and `repair` because `gaps` in [`schemas/change`](schemas/change.md#verdicts).
> Its first measure, of 3,206 criteria: S 463, J 70, B 2,527, E 89, F 57.

---

## The problem, measured

A generated component is kept as built only when every checklist assertion its
blueprints carry is read as met
([`schemas/run-statement`](schemas/run-statement.md#the-verdict-a-run-ends-with):
*"never kept as built"* unless conformance is `established`).

| | assertions | satisfied | unmet | unverifiable |
|---|---|---|---|---|
| orchestrator | 501 | 284 | 12 | 204 |
| content | 602 | 302 | 17 | 283 |

The rebuild ran about 10 hours of model time and 159 repair attempts, and both
components ended refused. So a fresh build of the tenant can never run.

Three things in that run matter more than the totals.

1. **The verdicts are a model's readings of code the same model wrote.** The
   loop's assertions are read by a model
   ([`architecture/generation`](architecture/generation.md#what-a-repair-round-reads-and-in-what-order)),
   and that reading decides the verdict. The model is builder and judge.
2. **The unmet list mixes severities with no order.** "Registration cannot
   succeed" sits beside "ISO codes checked by shape only" and "no OpenTelemetry
   export". The loop gave them equal weight. 10 of the 29 were left unmet
   because their latest repair broke the build, and several of those breaks
   were one class's repair landing in a shared file with another's (a trace
   change in `routes.go`, a key change in `run.go`).
3. **A declared test did see the worst fault, and it was not counted.**
   Content's Level 4 run against a real orchestrator reported
   `L4-01 Registers With A Real Orchestrator — inconclusive: the component
   exited during startup`. [`architecture/testing`](architecture/testing.md#l4-01-registers-with-a-real-orchestrator)
   step 3 says the component *MUST NOT exit*. An exit is that step failing.
   It was reported as no answer, so the one fault that keeps content off the
   hub reached the verdict only through a model's reading.

### How much of the corpus can be checked without a model

| | count |
|---|---|
| checklist items (`- [ ]`) in the corpus | 2,834 |
| items carrying a `wl:check` comment | 192 (6.8%) |
| of those, in `architecture/admin.md` | 164 |
| conformance tests the corpus declares ([`architecture/testing`](architecture/testing.md), L1 to L4) | 24 |
| `verifies:` blocks (v2), in specification files | 5 files, 19 checks, all about the corpus itself |

Per file, for the two components that were built:

| file | items | with `wl:check` |
|---|---|---|
| `architecture/admin.md` | 180 | 164 |
| `architecture/content.md` | 192 | 0 |
| `architecture/orchestrator.md` | 114 | 2 |
| `protocol/spec.md` | 51 | 5 |
| `protocol/identity.md` | 48 | 1 |
| `protocol/types.md` | 43 | 2 |
| `architecture/storage.md` | 39 | 0 |
| `patterns/scope.md` | 37 | 0 |
| `patterns/content-git.md` | 34 | 0 |
| `languages/go.md` | 26 | 0 |
| `patterns/secrets.md` | 19 | 0 |
| `patterns/logging.md` | 11 | 0 |

**A `wl:check` today is a name, not a procedure.** It says which requirement ids
a check covers. What runs is *"a test named by the covering check's id"*
([`architecture/generation`](architecture/generation.md#the-run-statement)),
and the generator writes that test. So even the 192 are, today, the model
grading itself under a name the corpus chose. What the corpus declares and
something other than the model executes is the 24 conformance tests, the
published vectors, and `checks/`, which checks the corpus and not a tenant.

---

## The owner's direction

- Order of importance is key, and it is why most things fail.
- The approach is documented in the blueprints, and builds follow it.
- Choosing what is critical per blueprint by hand would be very hard. The order
  already exists, in what each blueprint requires, extends and inherits.
- Say what is built, in what order, what is critical, and what is accepted, up
  to the point where a runtime environment exists.
- The greatest concern is what level of security this exposes.
- **The corpus drives all behaviour, with very clear instructions and tests.
  The model is never both builder and judge.**

---

## Four rules the rest follows from

1. **Only a check the corpus declares counts.** A requirement counts toward
   acceptance only when a check declared in the corpus settles it, run by an
   executor that is not the model that wrote the code. A model's reading of
   code never counts. It may still point a repair at a file.
2. **The CLI decides nothing.** It does not decide what is critical, and it
   does not decide what is accepted. It is the executor: it runs the declared
   checks, applies the corpus's class rules to the results, and writes what it
   found. The rules, the classes and the thresholds are corpus text, read at
   the pinned revision. A list of critical things, a severity table or a
   threshold compiled into the CLI is refused by this design.
3. **A requirement's class comes from structure the corpus already has**,
   decided where the requirement is declared and inherited everywhere it is
   owed. Nobody lists critical assertions by hand.
4. **A gap may be accepted only where it cannot widen exposure.** Security and
   contract requirements are met before any start, settled by declared checks
   only. Every other gap is recorded, shown, and either cannot be reached or
   is reached only on the person's own host.

---

## What already exists, and is reused

| Exists | Where | Used here for |
|---|---|---|
| Five Layer 3 outcomes (`verified`, `failed`, `necessary`, `not-applicable`, `unchecked`) and five model readings | [`architecture/generation`](architecture/generation.md#five-outcomes-never-three) | Only Layer 3 outcomes of declared checks count. Readings become advice |
| `IF premise: obligation`, settled by an explicit test or not at all | [`architecture/generation`](architecture/generation.md#conditional-assertions) | Premises the start already refuses (more than one instance; `WL_DEV`) |
| Four-layer gate, Layer 4 behaviour | [`architecture/generation`](architecture/generation.md#the-verification-gate) | The executor's layers |
| Conformance L1 to L4, with L4 against a real orchestrator | [`architecture/testing`](architecture/testing.md#level-4-interoperability) | Contract-class checks, first of all registration |
| `wl:id` and `wl:check … covers …`, checked by `requirement-ids.py` and `wl-ids.py` | [`checks/README`](checks/README.md) | The join between a requirement and its check |
| v2 `requirements` (`id`, `level`, `text`, `refs`) and `verifies` (`id`, `covers`, `check`, `assertion`) blocks | [`schemas/blocks`](schemas/blocks.md#definitions) | Where a declared check lives |
| Published vectors | [`vectors/`](vectors/README.md) | Checks that do not need a person to write code |
| `requires`, `extends`, `depends_on`; bindings to behaviours, endpoints, types and events | [`schemas/common`](schemas/common.md#dependencies-section) | How a class is inherited, and the contract class |
| Contract behaviours with names (`destructive-action-step-up`, `token-exchange`) | each blueprint's `## Contracts` | A unit the threat model can credit |
| The services, in the order they are built, with "needs running first" | [`schemas/programme`](schemas/programme.md#the-services-in-the-order-they-are-built) | Component order. Its one home |
| Six trust boundaries, a Control column in every attack table, `ThreatBoundary.controls`, a residual risk register that the operator must accept | [`architecture/threat-model`](architecture/threat-model.md) | What makes a requirement security class, and who accepts a residual |
| Environment profiles `development`, `staging`, `production`; default `production`; production never audit-only | [`patterns/scope`](patterns/scope.md#environment-profiles) | The environment a start is judged in |
| Trusted-network mode is loopback only; distributed is zero-trust only | [`architecture/threat-model`](architecture/threat-model.md#internal-network-model) | Exposure |
| Loopback defaults: admin allowlist `[127.0.0.1, ::1]`, internal listener on loopback, `https` unless loopback (rules 19, 22) | [`schemas/config`](schemas/config.md) | Deriving exposure from the tenant's own declaration |
| `WL_DEV=1` only on a build's own runs, in a scratch directory | [`architecture/cli`](architecture/cli.md#a-component-starts-with-a-clean-environment) | The sealed environment of build acceptance |
| `server start` order and "refused whole"; `replicas` above 1 refused | [`architecture/cli`](architecture/cli.md#weblisk-server-start) | Where runtime acceptance is enforced |
| D25: signed approval; self-approval only on a development tenant, recorded `development: true` | [`architecture/cli`](architecture/cli.md#who-may-approve-a-change) | Who decides runtime acceptance |
| Run statement verdict and counts; change outcomes; `unassessed`; `without_approval`; `established_by` | [`schemas/run-statement`](schemas/run-statement.md), [`schemas/change`](schemas/change.md) | Where gaps are recorded |
| `ADMIN_GROUP_UNAVAILABLE` for a route whose provider is absent | [`architecture/admin`](architecture/admin.md#changes-and-builds) | The model for a withheld route |

**Not reused, on purpose.** No checklist item carries a severity tag today.
`severity` in [`schemas/compliance`](schemas/compliance.md) grades programme
findings, and `criticality` in `patterns/safety` grades the target of an act.
Both classify other subjects, and borrowing either would give one word two
jobs.

### Found while measuring

1. **L4-01's exit is reported as no answer.** See the problem above. The fix is
   the CLI's, and the rule is already written.
2. **The development-tenant flag has no home.** It is used by D25, by
   `ApprovalRequest.development` and by a change's `approval.development`, and
   nothing declares where a tenant is flagged. Runtime acceptance needs it.
3. **`requires` is cyclic between architecture blueprints.** The orchestrator
   requires admin and admin requires the orchestrator; the orchestrator
   requires storage and storage requires the orchestrator. `requires` orders
   *reading*. It cannot order *building*. Component order already has its home
   in the services table.
4. **A likely corpus conflict the conflict reader did not find.**
   [`patterns/scope`](patterns/scope.md#propagation-rules) has every component
   emit `scope.violation`; [`protocol/spec`](protocol/spec.md#namespace-rules)
   says no two agents publish to one event namespace. Content's generated
   publisher refused `scope.violation` for exactly that reason. The two texts
   are in different files, so a reading given only the assertion's own
   governing text could not see it.
5. **The threat model's controls are prose.** Its attack tables have a Control
   column (`Admin auth middleware`, `Audit architecture`, `Bootstrap flow`),
   and only five contract names appear in the whole file. Its own rule, *"a
   mitigation is not credited until something enforces it"*, has nothing to
   point at.

---

## Classes

Five. The four in the brief, plus one that the measurement forced.

| Class | Unmet means | Example from the run |
|---|---|---|
| **S** security invariant | someone can do, read or sign what they should not; an identity, a signature, a scope, a custody rule or a secret does not hold | `jti` replay across instances; reserved paths pushed to a remote |
| **J** contract | the component cannot join, or another component cannot use what it binds | content's registration |
| **B** own behaviour | the component does the wrong thing inside access it grants correctly | `ZZ` accepted as a country code |
| **E** evidence | the act happens and its record is missing or incomplete | reads with no audit entry; no trace parent |
| **F** form | the code's shape is wrong; nothing a caller observes changes | path constants in the wrong package; a type defined twice |

F exists because fail-closed means nothing for it. There is no operation to
withhold when a constant sits in the wrong package, and four of the 29 are of
this kind.

### How a requirement gets its class

Taken in order. The first rule that matches gives the class. Every rule reads
something the corpus already holds. The class is decided where the requirement
is declared, and travels with it into every component whose `requires` or
`extends` closure owes it, so content inherits `patterns/scope`'s classes
exactly as it inherits its behaviours.

| # | Rule | Reads | Class |
|---|---|---|---|
| 1 | The requirement, the contract behaviour it sits in, its section or its blueprint is named as a **control** by the threat model | the threat model's Control cells and `ThreatBoundary.controls`, as refs | S |
| 2 | Its check requires a refusal at `401` or `403`, or a code the errors registry gives one of those statuses | [`protocol/types`](protocol/types.md) errors table | S |
| 3 | It sits in the component's **registration** section, or governs a behaviour, endpoint, type or event that another component *in this tenant* binds | a `registration` slot in [`schemas/architecture`](schemas/architecture.md); the binders' `## Dependencies` | J |
| 4 | Its home is a `language` or `platform` blueprint, and its check names no route, status, error code, header, event or environment variable | header `type`; the check's text | F |
| 5 | Its obligation is a record: an `AuditEntry`, a `LogEntry`, a trace or span field, an emitted event | the types it names (v2 `refs`) | E |
| 6 | anything else | — | B |

Three choices in that table need saying.

- **The one new annotation is in one file.** Rule 1 needs the threat model to
  name its controls by ref, not in prose. That is the threat model's own rule
  already. It puts the security decision in the document whose job is to be
  exhaustive about boundaries, owned by whoever reviews security, and not in
  2,834 checklist lines. A control may name a whole blueprint
  (`protocol/identity`), a behaviour (`destructive-action-step-up`), a section,
  or one requirement id.
- **A control is what prevents. A record of it is evidence.** The threat model
  already separates mitigations from controls. Rule 1 credits controls only. An
  audit trail that the residual register lists as a mitigation is E. The
  integrity of the audit log (vector 4.6, the hash chain) is S. Whether this
  holds where a behaviour mixes the two is open question 2.
- **The registration slot is one family-schema change.** Six blueprints already
  have the section under three headings (`Registration Flow`, `Registration and
  Standalone Operation`, `Registration and Dependency Verification`). One slot
  with those aliases classes every registration requirement with no per-item
  mark.

A check, proposed as `checks/acceptance-classes.py`, would read only those
sources. It gives every checklist item exactly one class and the rule that gave
it, holds the distribution the way `coverage.py` holds its share, and fails
when a control ref does not resolve. Its control: remove one control ref from
the threat model, and exactly the items it credited move class.

---

## Declared checks

### What counts

| Counts toward acceptance | Does not count |
|---|---|
| a conformance test the corpus declares, run by the CLI's harness | a model's reading of the source |
| a published vector, replayed against the component | a test the generator wrote, even named by a check id |
| a declared check of a kind the corpus defines, run by the CLI's executor for that kind | the CLI's own opinion, heuristic or threshold |
| an explicit premise test that makes an `IF` requirement not-applicable | guessing a premise false |

A model may still read the tree. Its readings point repairs at files and are
printed as advice, as Layer 3's mechanical check is printed today. They never
move a verdict, in either direction.

### What a declared check is

A check is **data in the corpus**, and its kind is a closed vocabulary the
corpus defines. The CLI implements each kind once, as an interpreter, and holds
no check of its own. The v2 `verifies` block already has the slot (`check:
<kind>`); its kinds today (`vectors-agree`, `walk-validates`) check the corpus.
These would check a tenant's component:

| Kind | What the corpus writes | What the executor does | Fits |
|---|---|---|---|
| `exchange` | requests, in order, with the expected status, code and fields; the identities and tokens they are made with, from the corpus's identity fixtures | starts the component sealed, sends them, compares | most S and B: refusals, scope, step-up, replay |
| `vector` | a ref to an entry in `vectors/` | puts the vector through the component's surface | signatures, canonical forms, fixed-form statements |
| `join` | the components to start beside it, from the services table | starts them, observes registration, lease, readiness | J; L4-01 to L4-04 are the first four |
| `record` | an `exchange`, then the record that must follow it | runs it, reads the audit route or the log lines | E |
| `topology` | instances, restarts, a store made unreadable | arranges them, then runs an `exchange` | `jti` across instances, durability across restart |
| `structure` | a query over the parse tree the language blueprint names | runs it on the tree | F; Layer 1 and 2 already do some |

A check names its requirement ids in `covers`, as now. A requirement whose
class is S or J and that no declared check covers is **unsettled**, and an
unsettled S or J requirement is unmet for acceptance. That is the honest gap:
the build says *"this security requirement has no check"*, not *"satisfied"*.

### Where checks live

Beside the requirement, in the blueprint that declares it, in its `verifies`
block, with any large fixture in `vectors/<blueprint>/`. A check written once
for `protocol/identity` is owed by every component that requires it, so
foundational checks pay for themselves across the tenant. Conformance tests
that span components stay in [`architecture/testing`](architecture/testing.md),
written as `join` and `exchange` data instead of prose steps.

### In what order they are written

1. **The 29 from the last run that are S or J**, so the next build can be
   judged at all. Content's registration first: L4-01 already exists and only
   needs its exit counted.
2. **S, then J, across the foundations**, deepest first in the `requires`
   graph with its cycles collapsed: `protocol/types`, `protocol/identity`,
   `protocol/conventions`, `patterns/scope`, `patterns/secrets`,
   `patterns/principal-identity`, then `architecture/storage`, then the
   orchestrator and admin together (they require each other), then content and
   `patterns/content-git`.
3. **The threat model's numbered vectors 1.1 to 6.8.** It already says each
   *"MUST have a corresponding test in the conformance test suite"*. Each one
   written is a declared S check.
4. **B, E and F**, in the same order, as the tenant needs them. They are never
   on the path to a start, so they need not hold up the first one.

How many requirements are S or J is not yet measured. It is the first output of
`acceptance-classes.py`, and the size of step 2 depends on it.

---

## Two gates

### Build acceptance: may this tree be kept as the component's code?

Decided by the corpus's rules, executed by the CLI, in a **sealed** run: a
scratch directory, `WL_DEV=1`, loopback only, no persistent store, removed
after. No person decides it and no person can vouch for it.

A tree is **build-accepted** when, on the tree the repair loop returns:

1. its dependencies resolve and it builds (Layers 1 and 2);
2. it starts in its sealed run, and no declared conformance test counts against
   it. That includes Level 4 against the trees its needs-first components were
   accepted with, and a component that exits during startup fails L4-01;
3. every S and J requirement it owes is settled by a declared check that passed,
   or is not-applicable by an explicit premise test. Unmet, unsettled,
   unverifiable, unanswered and in conflict all count as unmet;
4. every other requirement not settled as met is recorded as a gap with its
   class.

| Run statement `conformance` | When |
|---|---|
| `established` | every requirement settled as met by declared checks |
| `accepted` (new) | 1 to 3 hold; gaps of class B, E or F are recorded |
| `refuted` | any of 1 to 3 fails |
| `not-run` | as today |

A refuted tree is still banked in the cache as the best tree, as now. It is
never kept as built.

### The development exception

**Recorded by the owner on 2026-11-05: build the code first, and write the
full tests once the code is complete.** Rule 3 refutes every fresh build of a
tenant today, because most S and J criteria have no declared check yet and
some cannot be settled in a sealed run at all (about 95% of the admin
gateway's 126, for want of a first operator there). A hub that cannot be built
cannot be tested against, so nothing above the orchestrator was ever tested.

For a tenant whose `hub.environment` is `development`, and never elsewhere, a
layer is accepted when it compiles, every component starts, registers with the
accepted orchestrator, answers its declared probes and refuses an
unauthenticated request on its protected routes, and no declared check that
passed before now fails. Every other S and J criterion is recorded as a gap on
the run statement, and the verdict is `accepted`, never `established`.

**It ends** when every S and J criterion the services table's components owe
is settled by a declared check; the full gate then applies in development too,
and the exception is removed from where it is normative:
[`architecture/generation`](architecture/generation.md#the-development-gate).

### Runtime acceptance: may it start here, exposed to whom?

Decided by a **person**. The CLI (later the change service) computes a proposed
acceptance from corpus rules: the environment, the gaps, what they reach, and
an exposure statement. A person accepts it with a signed decision under D25:
signed by an operator identity, self-acceptance only on a development tenant
and recorded as such. The CLI never accepts on anyone's behalf.

It needs:

- the component build-accepted or established;
- every needs-first component runtime-accepted in the same environment;
- the environment's row in the table below satisfied for every gap;
- a decision that names the environment it was made for.

`weblisk server start` and `component start` then refuse, whole, a component
whose acceptance does not cover the environment the configuration describes
now. A configuration edit that widens exposure, such as an allowlist reaching
off the host, makes the earlier acceptance not cover it, and the start says so.
A configuration edit already belongs to a change, so the new acceptance rides
on that change.

### Environments

Derived from the tenant's own declaration, never asserted beside it. The
profile name is `patterns/scope`'s, whose default is `production`, so a tenant
that says nothing is judged as production.

| | how it is known | who can reach a listener |
|---|---|---|
| **sealed** | a build's own run | the build, on loopback, for the length of the run |
| **development** | profile `development`, and every listener, allowlist and `admin_addresses` entry on loopback, no federation peer, no remote destination confirmed | processes on the tenant's host |
| **network** | any listener, allowlist entry or address off loopback, whatever the profile | anyone the allowlist admits |
| **production** | profile `production` | as declared |

### What each environment allows

| Class | sealed | development | network | production |
|---|---|---|---|---|
| S | anything, recorded | met | met | met |
| J | anything, recorded | met | met | met |
| B | recorded | accepted and shown; withheld where its reach can be | withheld, or accepted by a person who records why it fails closed | withheld, or accepted into the residual risk register by a position holder other than the requester |
| E | recorded | accepted and shown | accepted and shown; every claim citing the record says it is incomplete | audit-log gaps block; other E gaps go into the residual risk register |
| F | recorded | accepted | accepted | accepted |

**S holds in development too.** The development tenant holds real repositories,
keys and signed change logs, and those outlive the environment. A signature
made wrong in development is still in the log when the tenant goes to
production.

### Fail closed: what it means for each class

| Class | An accepted gap fails closed when |
|---|---|
| B | the operations it reaches are **withheld**: the orchestrator mints no pass carrying the capability that guards them, and the admin gateway answers their routes with a registered refusal instead of routing them. A gap whose reach cannot be narrowed below the whole component cannot be withheld, and outside development it blocks unless a person records why its unmet state is itself a refusal |
| E | every claim that cites the record says it is incomplete: an audit export, an evidence chain, a conformance claim. The act is not refused. The claim about it is qualified |
| F | nothing to close. Recorded |

A gap's **reach** is read narrowest first: the operations its cited sections
govern (the Endpoints table and the capability that guards them), then the
operations served by the files answerable for it (the run statement's
`serves`), then the whole component. A wider reach is never less safe.

**Withholding does not exist yet.** It needs a capability the orchestrator
refuses to mint, a gateway answer for a withheld route (a new code, so Studio
can tell *withheld because of gap* from *provider absent*), and both are S
requirements of their own. Until they exist, B gaps in development are shown
and not withheld, and B gaps elsewhere block.

### What a person is exposed to

**In development, with accepted gaps:**

- Exposed to: wrong behaviour inside correct access, on their own host (an
  organisation saved with an unassigned country code); incomplete evidence
  (reads not audited, traces broken, error lines without codes); code-shape
  debt.
- Not exposed to: a forged or replayed identity, a token minted without
  verification, a signature that does not hold, a scope or custody rule not
  enforced, a secret pushed out, a record shown signed that was not. Those are
  S, and S is met. Nothing reaches a listener from off the host. The residual
  that remains is the one the threat model already lists: a second process on
  the same host.

**On a network:** the same S guarantee, now to anyone the allowlist admits. B
gaps are withheld or a person has written down why each one refuses rather
than half-works.

**In production:** the same, plus a complete audit log, and every residual
accepted into the deployment's risk register by a position holder, as the
threat model already requires.

---

## Order

### What is built, in what order

> **Landed:** normative in [`architecture/engine`](architecture/engine.md#build-order),
> Build order — the layers (contract, libraries by `requires`, components by
> what each needs running first), generate-compile-test within a layer, gating,
> the contract package built once per change, the test environment of accepted
> builds, the whole-hub integration run, and incremental change by layer; and
> how accepted dependencies are brought up, a first operator included, in
> [`architecture/testing`](architecture/testing.md#bringing-up-accepted-dependencies).
> Where this section and those disagree, those are right.

The services table in [`schemas/programme`](schemas/programme.md#the-services-in-the-order-they-are-built)
is the one home of component order: orchestrator; admin and content, which need
the orchestrator; then the rest. A component's build is judged against the
trees its needs-first components were accepted with: its Level 4 runs start
those trees, sealed, and never the tenant's live processes. A component whose
needs-first component is not build-accepted is not built. Its outcome is
`skipped`, naming what it waited for.

`requires` and `extends` decide what a component **owes**: the checklist
gathered from its closure, as now. Because the graph has cycles, the order *in*
it is taken after the cycles are collapsed, and is used only to rank repairs
and to sequence writing checks.

### Order of repair

The loop repairs by class: S, then J, then B, then E, then F. Within a class,
requirements from deeper blueprints come first. A round repairs one class only,
so a form repair never shares a round, or a shared file, with a security
repair. Trees are ranked first by fewer S and J unmet, then by the rest. Once a
tree is build-accepted, no later round may trade that away. The loop ends when
acceptance is reached and two rounds fail to improve the classes left, or as
today when it cannot be reached.

### How a gap propagates

| A gap in a needs-first component, of class | does this to the components that need it |
|---|---|
| S or J | the component is not accepted, so they are not built (`skipped`) |
| J, provider side, withheld | the dependant's operations that use the binding are withheld too |
| B or E that nothing binds | nothing. Shown on the provider |
| E that a dependant's claims cite | the dependant's claims say the record is incomplete |

---

## Gaps as records

### On the run statement

The run statement records facts about a tree. It gains `verdict.gaps` beside
the counts, and per-class counts. A count the gate did not take is absent,
never `0`.

| Field | Holds |
|---|---|
| `check` | the full ref of the check, or of the requirement where no check exists. The gap's identity; it does not move when a heading is renamed |
| `class`, `class_by` | the class, and the rule and ref that gave it |
| `covers` | the requirement ids |
| `result` | `unmet`, `unsettled` (no declared check), `failed` |
| `reason` | the executor's own reason, from the latest attempt |
| `files` | the files answerable for it |
| `reach` | operations and capabilities, or `component` |
| `premise` | the premise and the test that settles it, where it is `IF` |
| `reaches` | components in this tenant that bind what it governs |
| `advice` | the model's reading, labelled as advice; recorded as the criterion's `readings` ([`schemas/run-statement`](schemas/run-statement.md#criteria)), so a reading that says met is kept too |

### On the change

A change gains an `acceptance` block, the runtime decision: the environment,
its exposure, each component with the run it accepts and the gaps it accepts,
what is withheld, the exposure statement's digest, and the signed decision
(`by`, `position`, `signature`, `at`, `development`). An outcome's verdict gains
`accepted`. An adoption plan names a component whose latest run is `accepted`
`repair`, because `gaps`, so adopting is always the act that closes them; other
plans show it with its gaps and never as `keep` because `unchanged`.

### The exposure statement

Assembled from the class, the environment, the reach and the requirement's own
text. Never written by a model. For example: *"Reads at `/v1/audit`, operator
get and the lease lists write no audit entry. An audit export from this tenant
is incomplete for reads, and says so."*

### Closing a gap

| How | Recorded as |
|---|---|
| a later run's declared check passes | closed, by that run |
| its premise is settled false by an explicit test | not applicable, by that run |
| the corpus retires or rewrites the requirement | superseded, with the corpus revision |
| a person accepts it | **not closed.** Accepted, for one environment, on one change |

### How Studio shows it

Studio reads all of it through the tenant's API (`/v1/admin/build`,
`/v1/admin/changes/{id}`) and holds none of it.

- Each component's standing: established, accepted with gaps by class, refuted,
  unassessed. Accepted is never drawn as verified.
- Gaps grouped by class, S and J first, each with its exposure statement and
  the environment it was accepted for.
- A withheld feature is shown where the feature would be, naming the gap. It is
  never silently missing.
- A configuration change that would widen exposure is shown as needing a new
  acceptance before it is made.
- Counts by class always shown. A class nothing counted shows as not counted,
  never zero.

---

## Measured against the real run

The 29 items left unmet, plus the one conflict. *Shared* means the latest repair
broke the build and the best tree is still unmet. Under rule 1, none of these
readings would count either way: each S or J row below is also **unsettled**,
because no declared check covers it, and blocks for that reason alone until one
is written.

| # | Component | Requirement (short) | Home | Class | Build gate | Dev runtime |
|---|---|---|---|---|---|---|
| O1 | orch | destructive act and its refusals audited with `step_up_at` | admin · `destructive-action-step-up` | S (behaviour credited) | **blocks** | — |
| O2 | orch | error logs carry the error code | logging | E | gap | shown |
| O3 | orch | every operation writes an `AuditEntry`; reads write none | orchestrator · Audit Logging | E | gap | shown; blocks production |
| O4 | orch | `operates_in` codes checked by shape only | orchestrator · tenancy | B | gap | shown; withhold the organisation write when possible |
| O5 | orch | path constants not in `internal/protocol` | go | F | gap | — |
| O6 | orch | no type defined twice (shared) | go | F | gap | — |
| O7 | orch | trace carried between components (shared) | spec · Trace Propagation | E | gap | shown |
| O8 | orch | log lines carry `trace_id` and `span_id` (shared) | logging | E | gap | shown |
| O9 | orch | `hub_id` unchanged across key rotation (shared) | admin · identity signs only to attest | S | **blocks** | — |
| O10 | orch | OpenTelemetry export where deployed (shared) | logging | E, `IF` telemetry deployed | gap | not applicable while none is declared |
| O11 | orch | `jti` refused across instances | admin · `attestation-token-issuance` | S | **blocks** | — |
| O12 | orch | `jti` records shared by every instance | admin · stores | S | **blocks** | — |
| X1 | orch | every token exchange audited with the person's id (in conflict with the corpus) | orchestrator · `token-exchange` | S (behaviour credited) | **blocks until the corpus is corrected** | — |
| C1 | content | no type defined twice (shared) | go | F | gap | — |
| C2 | content | manifest declares no person-only capability, **and registration succeeds** | content · Registration | **S and J** | **blocks**; L4-01 also fails | — |
| C3 | content | path constants (shared) | go | F | gap | — |
| C4 | content | wrong method gives 405 with a registered code | go · HTTP Surface | B | gap | shown; already a refusal |
| C5 | content | `WL_DEV` audit in memory, not temp files | go · Development Mode | B, `IF WL_DEV=1` | gap | not applicable: no tenant start sets it |
| C6 | content | service key rotation appends a succession entry | content · Who signs | S | **blocks** | — |
| C7 | content | owner key rotation appends a succession entry | storage | S | **blocks** | — |
| C8 | content | trace carried between components | spec | E | gap | shown |
| C9 | content | remote changed by someone else becomes `diverged` (shared) | content · remotes | S | **blocks** | — |
| C10 | content | a verifying change statement is recorded | content · change statement | S | **blocks** | — |
| C11 | content | a decision's statement is recorded `signed` | content · change statement | S | **blocks** | — |
| C12 | content | moved destination line makes the remote `diverged` (shared) | content-git | S | **blocks** | — |
| C13 | content | a commit adding `.weblisk/secrets/x` holds the remote | content-git | S | **blocks** | — |
| C14 | content | `pii` above ceiling holds the remote | content-git | S | **blocks** | — |
| C15 | content | a work pass request recorded with actor, via, authorisation, run | identity · work pass | S (blueprint credited) | **blocks** | — |
| C16 | content | `scope.violation` emitted | scope · the gate | S (blueprint credited) | **blocks**; likely corpus conflict | — |
| C17 | content | each field's Go type per the type mapping (shared) | go | F (rule 4); in meaning B | gap | — |

**Content's registration is blocked**, by two independent things: its
requirement is S and J, and L4-01 observed the exit.

As written, 15 of the 29 block, plus the conflict: 4 in the orchestrator, 11 in
content. Three refinements would each narrow that, and each is the owner's to
decide (open questions 1 to 3):

| Refinement | Moves | Orchestrator blocks on | Content blocks on |
|---|---|---|---|
| as written | — | O1, O9, O11, O12, X1 | C2, C6, C7, C9 to C16 |
| R1: write the multi-instance clauses as `IF more than one instance answers for the hub`, which `server start` already refuses | O11, O12 to not-applicable | O1, O9, X1 | same |
| R2, with R1: a record of a credited act is E, not S | O1, X1, C15, C16 to E | O9 | C2, C6, C7, C9 to C14 |
| R3, with R1 and R2: an S gap whose whole reach is withheld by something outside the component may be accepted (`content:replicate` and `content:connect` withheld while content reports no remote; the CLI refuses a key rotation while a rotation gap is open) | O9, C6, C7, C9, C12, C13, C14 to accepted, withheld | none | **C2, C10, C11** |

With all three, the orchestrator is build-accepted with 11 recorded gaps, and
content is blocked by three requirements, all in signing: its signer refuses
the registration prefix, and its statement verification is never given the
attestation it needs. Those are the faults that matter, and they are the only
ones left blocking. Every one still needs a declared check before it can count
as met.

---

## What changes where

No code. Each a short list.

### Corpus

- [`architecture/generation`](architecture/generation.md): build acceptance as
  above; only declared checks count; model readings are advice; repair by class
  and depth; ranking; the stop rule; the five classes and their derivation.
- [`architecture/threat-model`](architecture/threat-model.md): Control cells and
  `ThreatBoundary.controls` become refs; controls separated from records.
- [`schemas/architecture`](schemas/architecture.md): a `registration` slot with
  the three existing headings as aliases.
- [`schemas/blocks`](schemas/blocks.md): the `check` kinds for a tenant's
  component (`exchange`, `vector`, `join`, `record`, `topology`,
  `structure`) and each kind's data shape.
- [`architecture/testing`](architecture/testing.md): L1 to L4 written as
  declared `join` and `exchange` checks; L4-01's exit counted as a failure.
- [`schemas/run-statement`](schemas/run-statement.md): `accepted`;
  `verdict.gaps`; per-class counts.
- [`schemas/change`](schemas/change.md): the `acceptance` block; outcome
  `accepted`; `repair` because `gaps`; rules and vectors in `vectors/change/`.
- [`schemas/config`](schemas/config.md): one home for the environment, which is
  also where a tenant is flagged as development.
- [`architecture/orchestrator`](architecture/orchestrator.md),
  [`architecture/admin`](architecture/admin.md),
  [`protocol/types`](protocol/types.md): withheld capabilities never minted;
  withheld routes answered with a registered code.
- [`architecture/admin`](architecture/admin.md): the `jti` multi-instance
  clauses as `IF` requirements (R1); the conflict X1 corrected.
- [`patterns/scope`](patterns/scope.md) and
  [`protocol/spec`](protocol/spec.md): settle who may publish
  `scope.violation`.
- [`architecture/cli`](architecture/cli.md): `server start` refuses a component
  whose acceptance does not cover the current environment; a verb to decide a
  runtime acceptance (`tenant-api`, signed); `server status` shows gaps.
- `checks/acceptance-classes.py`, with its control.
- `verifies` blocks, written in the order above.

### CLI

- Run declared checks as an interpreter of their kinds. Hold no check, list or
  threshold of its own.
- Count an exit during startup in L4-01 as a failure.
- Stop counting model readings toward any verdict; print them as advice.
- Judge a dependant against the accepted trees of its needs-first components.
- Write gaps on the run statement and the proposed acceptance on the change.
- Refuse a start the acceptance does not cover.

### Studio

- Render standing, gaps by class, exposure statements, withheld features and
  the environment each acceptance covers, all read from the tenant.
- Offer the runtime acceptance decision, signed by the person, through the
  tenant's API.
- Never draw accepted as verified, and never draw an uncounted class as zero.

---

## Decisions

Decided by the owner on 2026-11-03.

1. **R1: yes.** Multi-instance obligations are written as `IF` requirements,
   and `server start` refuses a second instance of a component.
2. **R2: security (S).** The audit record of a security act is what an
   auditor relies on, so it is security-class. This decides O1, X1, C15 and C16.
3. **R3: yes, conditionally.** A security gap may be accepted when its whole
   reach is withheld by something outside the component, and only where that
   withholding is itself settled by a declared check that passed.
4. **Withholding: yes.** Withholding by capability and gateway route is the
   fail-closed mechanism, and building it is security-class work.
5. **Who accepts in production:** a position holder other than the requester.
6. **E in production:** audit-log gaps block production. Every other E gap
   qualifies each claim that cites the record.
7. **Model readings: removed from every verdict.** Reporting far more
   unsettled than unmet until checks are written is the honest report, and is
   the one wanted.
8. **First tranche:** the S and J items from this run first, then the whole S
   and J set of the foundations, once `acceptance-classes.py` has measured it.
9. **Development exception (2026-11-05):** in `development` only, a layer is
   accepted on compile, start, registration, probes, refusing an
   unauthenticated request and no regression, with every other S and J
   criterion a recorded gap, until the S and J checks exist
   ([The development exception](#the-development-exception)).
