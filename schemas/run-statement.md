# Schema: Run Statement

What one generation run read and wrote, and what each output traces to, in one
immutable file the tenant holds.

A run statement is the declared source of every edge a build creates in the
fabric ([`architecture/fabric`](../architecture/fabric.md#declared-at-write-time),
`declared-at-write-time`). It is written when the files are written, so it
exists on the first build, offline, before any fabric runs; the fabric's
`generation-statements` producer ingests it later. How a run is planned and
gated is [`architecture/generation`](../architecture/generation.md#the-run-statement)'s;
this file says only what the statement holds and how it is read.

---

## Where it lives

One file per run, at `provenance/runs/<run id>.json` in the tenant repository,
written once and never edited. A run that is repeated is a new run with a new
statement. Nothing else records run facts: the fabric's ledger names a run by
its id and statement digest (`RunCitation`), and the build lock holds resolved
versions and no roots.

## Shape

The statement is an [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md)
whose predicate is [SLSA Provenance v1](https://slsa.dev/spec/v1.0/provenance),
so a general tool reads it without knowing Weblisk. What Weblisk adds sits in
the places those specifications leave for a build type's own parameters and for
annotations on a resource. The statement's type is `RunStatement`, declared in
the `types` block below, and its build type is that type's full ref,
`type://weblisk/schemas/run-statement:RunStatement`.

Each subject carries the record [`architecture/generation`](../architecture/generation.md#deciding-whether-a-file-must-be-rebuilt)
requires for every file it writes — its plan entry, its digest as written, the
digest of each blueprint it was generated from, and what it is answerable for —
so the rebuild decision reads its per-file inputs here and nowhere else.

```yaml
run_statement:
  _type: https://in-toto.io/Statement/v1
  predicateType: https://slsa.dev/provenance/v1
  subject:                         # one per output file the run wrote
    - name: <path in the tenant repository>
      digest: {sha256: <hex>}
      annotations:
        roots: [<ref>]             # the roots this output traces to: which of the
                                   # run's requested roots it was generated for
        plan_entry:                # the plan entry that produced it; its path is `name`
          purpose: <text>
          declares: [<symbol>]
          serves: [<operation ref>]
        implements: [<requirement ref>]  # from its plan entry
        generated_from: [<requirement, mapping rule or control ref>]
        blueprints:                # each blueprint this file was generated from,
          - uri: <full ref>        # at the digest the run read it
            digest: {sha256: <hex>}
        answerable_for:            # what a change must reach to make it a rebuild
          bindings: [<type or operation ref it binds>]
          assertions: [<check ref>]
  predicate:
    buildDefinition:
      buildType: type://weblisk/schemas/run-statement:RunStatement
      externalParameters:
        component: <component kind>
        roots: [<ref>]             # what the run was asked to build from
        plan_digest: sha256:<hex>
      internalParameters:
        tool: {name: weblisk, version: <cli version>}
        backend: <the backend the run used>
        model: <the id the backend reported at run time, or unreported>
        prompt_digests: [sha256:<hex>]
        on_behalf_of: <identity id of the operator who asked for the run>
      resolvedDependencies:        # every blueprint and mapping rule read
        - uri: <full ref>
          digest: {sha256: <hex>}
          annotations: {version: <resolved version>}
    runDetails:
      builder: {id: <full ref of the tenant's generation service>}
      metadata:
        invocationId: <run id>
        startedOn: <RFC 3339>
        finishedOn: <RFC 3339>
```

```yaml
types:
  RunStatement:
    description: One generation run's statement, an in-toto Statement v1 with a
      SLSA Provenance v1 predicate, in the shape above. Its fields are those
      specifications' own; this file adds only the subject annotations and the
      build parameters the shape shows
    fields:
      _type:
        type: string
        description: https://in-toto.io/Statement/v1
      predicateType:
        type: string
        description: https://slsa.dev/provenance/v1
      subject:
        type: list
        description: One entry per output file the run wrote, each with its
          name, digest and the annotations the shape shows
      predicate:
        type: object
        description: The SLSA Provenance v1 predicate, whose buildType is this
          type's full ref
```

## Rules

1. **`model` is what the backend reported, never what was configured.** It is
   the model id the backend returned for this run, at run time. A configured
   name is a request, and the backend may have served something else under it.
   A backend that reports none gives `model: unreported`, and what that does to
   caching is [`architecture/generation`](../architecture/generation.md#the-run-statement)'s
   to say.
2. **`roots` is per output.** A run of several roots records, on each subject,
   which of them that file was generated for. `change plan --upgrade` takes its
   roots from the latest statement of each component; the lock never holds them.
3. **`implements` is per planned file**, copied from the plan entry that
   produced it ([`architecture/generation`](../architecture/generation.md#what-a-plan-declares)).
   No marker is written into the generated code. Verification confirms each
   claim through a test named by the check id that covers the requirement, which
   the language's symbol extractor finds; where no extractor exists the
   confirmation is file-level and says so.
4. **Every digest is written as `patterns/content-identity` spells it**:
   `sha256:<hex>` as one string, `{sha256: <hex>}` where in-toto's digest set is
   the field.
5. **Every ref is a full ref** in the grammar of [`names.md`](names.md), because
   a statement is read without the file that named it.
6. **The file is always a DSSE envelope, stored as RFC 8785 canonical bytes**
   (Signing, below), signed or not, so the statement digest an entry cites is
   the SHA-256 of the file as stored, recomputable with `sha256sum`, and does
   not change form when signing begins.
7. **A subject's `blueprints` are a subset of `resolvedDependencies`, at the
   same digests.** The run's list is everything it read; a subject's is what
   that file was made from.

## Signing

Every statement is stored in a [DSSE](https://github.com/secure-systems-lab/dsse)
envelope: `payloadType` `application/vnd.in-toto+json`, `payload` the base64
of the statement's RFC 8785 bytes, and `signatures`. A signature is ML-DSA-65
([`protocol/identity`](../protocol/identity.md)) over DSSE's pre-authentication
encoding, `PAE(payloadType, payload)` with the payload's decoded bytes — never
over the envelope or the statement's JSON as serialised — made by the tenant's
`generation` service credential, admitted once by a person, with `keyid` its
identity id. The statement records `on_behalf_of` the operator.

That credential is part of the credential layer (identity, credential,
grant), which does not exist yet. **Until it does, the envelope's `signatures`
is empty**, the statement is read as unsigned, and the fabric records each entry's run citation
with `signed: false`. A person's identity key never signs a statement in the
credential's place; that would make a person the author of every file a model
wrote.

## Reading one

- A statement whose `_type` or `predicateType` is not the one above is not a
  run statement, and is reported, not guessed at.
- A subject whose file is absent or whose digest differs is reported as such:
  the statement says what was written, and the file says what is there now. An
  edited output is refused for regeneration
  ([`architecture/generation`](../architecture/generation.md#deciding-whether-a-file-must-be-rebuilt)).
- A statement is never rewritten to correct it. A correction is a new run.
