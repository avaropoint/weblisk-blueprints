# One Contract Block Per Blueprint

> A change to how a blueprint declares what a machine reads. Prose stays for
> people; everything a generator, validator or auditor needs moves into a single
> declared block.

---

## Why

Ten different parsers read a blueprint today:

| Parser | Reads |
|---|---|
| `DeclaredRequires` | frontmatter |
| `ExtractBindings` | `## Dependencies` YAML |
| `ExtractTypes` | `### TypeName` headings |
| `declaredNames` | …and `TypeName:` keys, and `- name:` entries — **three forms** |
| `ExtractEndpoints` | `### METHOD /path` headings in `protocol/spec` |
| `ExtractTableEndpoints` | the `## Endpoints` table |
| `ExtractEndpointOperations` | **the same table, a second reader** |
| `ExtractStoreContracts` | the `## Interfaces` store table |
| `ExtractChecklist` | `## Verification Checklist` prose |
| `DeclaredComponentGroups` | **an English sentence, by regex** |

Each fact lives in a different shape, so each needs its own parser, and each
parser needs its own calibration against forms nobody wrote down. One rule —
"does this binding resolve" — took **six** attempts and reported 389, then 134,
then 74, purely because the corpus declares a type in three ways.

That is the complexity. It is not in the blueprints; it is in the fact that a
blueprint's structure is **implied by convention rather than stated**.

Two of those parsers read the same table, which is the fault this corpus
explicitly forbids: one question, one implementation.

---

## The change

Every blueprint carries **one `contract:` block**. It holds everything a
machine reads. Nothing else in the document is parsed.

```yaml
contract:
  requires:
    - blueprint: protocol/identity
      version: ">=1.0.0 <2.0.0"
      bindings:
        types:
          - name: SigningKeyPair
            fields_used: [public_key, private_key]
        behaviors:
          - name: key-rotation
      on_change:
        compatible: validate-and-adopt
        breaking: version-bump
        removed: halt-immediately

  declares:
    types:
      HealthStatus:
        status:  { type: string, required: true }
        uptime:  { type: int64,  required: true }
    behaviors:
      - name: durable-records
        rules:
          - Every write survives a process restart
    operations: [PutAgent, GetAgent, DeleteAgent, ListAgents]

  serves:
    - { method: POST, path: /v1/register, operation: Register, auth: none }
    - { method: GET,  path: /v1/health,   operation: Health,   auth: none }

  verifies:
    - assertion: Every operation writes an audit entry chained to the previous one
    - assertion: Domain controllers dispatch phases in parallel
      group: Domain Controllers
```

**The rest of the document is prose.** Diagrams, rationale, worked examples,
flow descriptions — all of it for a human reader, none of it parsed.

---

## What this removes

| Today | After |
|---|---|
| 10 parsers | **1** |
| 3 ways to declare a type | **1** |
| A `Form` column per section | unnecessary — the body is narrative by definition |
| "Read the blueprint IN FULL; a MUST anywhere binds" | unnecessary — the contract is complete |
| Validator rules for section form, declared constructs, declared names, binding resolution | **one**: does the contract match the schema |
| Two readers of the endpoints table | one |

---

## What it costs, stated plainly

**Prose stops being normative.** Today a MUST in a paragraph binds. After this,
a rule that matters to an implementation must be IN the contract. Migration is
therefore an editorial pass, not only a mechanical one: every MUST is either
promoted into the contract or acknowledged as commentary.

**Two places describe one thing.** The contract declares `Register`; the prose
explains it. That is the OpenAPI shape — spec plus documentation — and it is the
trade for machine-readability. The validator checks the prose does not
contradict the contract, which is a far easier question than the ones it asks
today.

**~90 files.** Largely mechanical, because the facts already exist and are
merely scattered. It still needs review rather than blind generation.

---

## Sequence

No flag day. A blueprint with a `contract:` block is read from it; a blueprint
without one is read the old way. `weblisk validate` reports how many still rely
on scattered parsing, and that count ratchets down.

| Phase | Scope | Exit condition |
|---|---|---|
| **1 — Prototype** | `architecture/orchestrator` and one agent | The contract is generated from what those blueprints already declare, and produces the same requirements the old parsers did |
| **2 — Prove** | Build a hub from them | Generation, build, conformance no worse than the last clean run |
| **3 — The build set** | The eight blueprints the orchestrator reads | `weblisk validate` clean on that set |
| **4 — The rest** | ~80 remaining | Scattered-parsing count reaches zero; the old parsers are deleted |

**Phase 1 stops the work if it fails.** If the contract does not reproduce the
old requirements exactly, the idea is wrong and it has cost two files.

---

## CLI changes

| Change | Detail |
|---|---|
| `ExtractContract` | One parser. Reads `contract:`, returns requires, declares, serves, verifies |
| `GatherRequirements` | Prefers the contract when present, falls back to the existing parsers |
| `weblisk validate` | Gains "does the contract match the schema"; loses form, construct and declared-name rules as blueprints migrate |
| Deletions, at phase 4 | `ExtractTableEndpoints`, `ExtractEndpointOperations`, `ExtractTypes`, `ExtractStoreContracts`, `declaredNames`, `SchemaSections`, `SectionConstructs`, the `Form` column |

The old parsers are **kept until phase 4** so a partially migrated corpus still
builds.

---

## Studio changes — major

Studio reads blueprints to render governance, coverage and impact. Those views
are built on the scattered shapes and will need reworking.

| Area | Impact |
|---|---|
| Blueprint rendering | A contract block is structured data, not prose — it should render as a table, not a fenced block |
| Coverage and impact analysis | Currently infers relationships from headings and tables; would read `contract.requires` and `contract.declares` directly, which is simpler and correct |
| The editor | Needs to treat `contract:` as a structured region — validated on save, not free text |
| Governance views | Endpoint, type and operation inventories come from one block instead of several extractors |
| Search and relationships | `internal/relate` edges can be built from contracts instead of text matching |

**None of this is required for phases 1–3.** Studio keeps working because the
old parsers remain. It becomes a real project at phase 4, and it is a
simplification there rather than an addition.

---

## The measure of success

Not "the corpus validates". The measure is that **a rule can be added without
being calibrated** — because there is one shape to read, and it was declared
rather than discovered.

---

## Findings from phase 2

Recorded as they were found, because each is a thing the design got wrong and a
build surfaced.

| # | Finding | Resolution |
|---|---|---|
| 1 | The contract path **appended** endpoints instead of replacing them, reporting 24 where there are 17 — `protocol/spec`'s seven were counted twice | The contract SEEDS the set; `protocol/spec` becomes a cross-check |
| 2 | Merging would let a contract missing an endpoint be silently completed by the sections it replaced | An omission is REPORTED. "A contract completed by what it replaced is not a contract" |
| 3 | A malformed contract could fall back to the old sections while the author believed the contract was in force | A malformed contract stops the run |
| 4 | `{name}` opens a flow mapping in YAML — the compact `serves` form did not parse | Block form, quoted paths |
| 5 | The first generator reported every endpoint as `auth: none` — wrong map key, and the admin table uses a `Capability` column | Auth read by COLUMN NAME from both tables |
| 6 | **`contract.verifies` is declared and never read.** The checklist still comes from prose, so the contract states assertions nothing uses | Open — see below |

### Open: the Verification Checklist

`verifies` is in the contract and unread. That is the worst of both — a declared
field nothing consumes will drift from the prose that is actually used.

Two coherent answers:

- **Wire it.** The contract becomes the single source for a migrated blueprint;
  `ExtractChecklist` serves only unmigrated ones. Consistent with the design,
  and the checklist stops being a second surface.
- **Remove it.** `## Verification Checklist` is the ONE surface that is already
  100% consistent — prose in all 79 blueprints that have it — and it parses
  reliably. The contract exists to fix SCATTERED facts, and this is not one.

**Resolved: wired.** The target's assertions now come from its contract; every
other blueprint's still come from its prose checklist, and the target's prose
checklist is skipped so nothing is graded twice. 24 assertions, no duplicates.

Fixing it exposed a second fault in the same field. `verifies` was a list of
STRINGS, and a prose checklist scopes an assertion with a `###` subheading —
15 of the corpus's 87 use one. A flat list would have silently addressed every
assertion to every component. It is now a uniform mapping with an optional
`group`, rather than "a string OR a mapping", because two accepted forms is the
ambiguity this block exists to remove.

### Finding 8: a declaration must REPLACE what it supersedes

`architecture/orchestrator` carries a `## Declaration` **and** the
`## Dependencies` section it was generated from. Two statements of the same
dependencies, and the migration has therefore ADDED a surface rather than
removed one — the opposite of the point.

It is worse than redundant. The generator reproduces faithfully, so the
declaration inherited the section's faults: `ChannelEntry` bound from
`architecture/storage`, which does not declare it — `protocol/types` does.
Fixing one copy leaves the other wrong, and the validator reads both.

**A migrated blueprint's `## Declaration` replaces `## Dependencies`.** The
sections that remain are the ones a declaration does not carry: `## Endpoints`
stays because it is the human-readable HTTP surface and the declaration's
`serves:` is the machine-readable one — but they must agree, and the validator
checks that they do.

The rule for every migration: **remove the section the declaration supersedes,
in the same edit that adds the declaration.** A migration that leaves both is
not half-done, it is worse than not started.

### Finding 9: generation reproduces faults

The prototype declaration was generated from the existing sections, so it
carries every mis-sourced binding they had. That is correct behaviour — the
exit test requires the declaration to reproduce the parsers exactly — but it
means **migration is not a correction**. The corpus's 88 unresolved bindings
move into declarations unchanged and must be fixed as their own piece of work.
