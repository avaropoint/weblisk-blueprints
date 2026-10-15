# Schema: Names

How anything the corpus or a tenant holds is named, so that a name written in
one place means the same thing everywhere it is read.

This file is the one home of the id grammar. Its test vectors are
[`vectors/ids.json`](../vectors/ids.json), and every implementation of the
grammar, in any repository or language, is bound by them rather than by a copy
of the rules below. Which sorts of thing exist is
[`schemas/kinds`](kinds.md)'s; this file says only how one of them is named.

---

## The grammar

```
citation  = ref "@" version
ref       = [ family ":" ] [ "//" namespace "/" ] local [ ":" part ] [ "#" anchor ]

family    = lower *( lower / DIGIT / "-" )             ; a declared family, below
namespace = lower 1*38( lower / DIGIT / "-" )           ; 2 to 39 characters
local     = segment *( "/" segment )                    ; the family's own path
segment   = ( ALPHA / DIGIT / "_" ) *( ALPHA / DIGIT / "_" / "." / "-" )
part      = ( ALPHA / DIGIT ) *( ALPHA / DIGIT / "." / "-" / "(" / ")" )
anchor    = ( lower / DIGIT ) *( lower / DIGIT / "_" / "-" )
version   = 1*DIGIT "." 1*DIGIT "." 1*DIGIT [ "-" 1*( ALPHA / DIGIT / "." / "-" ) ]
lower     = %x61-7A
```

Three further rules a grammar line cannot carry:

1. **A ref begins with a letter or with `//`.** A digit, `@`, `.` or any other
   character first is refused. This is what makes every ref a plain scalar in
   YAML, block and flow alike, read back as the same string: `@` is a YAML
   indicator, and a leading digit is how a YAML reader comes to see a number or
   a date.
2. **A leading word followed by `:` is a family exactly when it is declared**
   (below). It is never inferred from shape, so `orchestrator:register` is the
   part `register` of the local id `orchestrator`, while `control:5.1` is the
   control `5.1`. This is [`schemas/kinds`](kinds.md#naming-a-targets-kind)'s
   first-colon rule, which keeps every existing kind-qualified reference valid.
3. **A ref that is a single bare word is never one a YAML 1.1 reader takes as
   something else**: `y`, `yes`, `n`, `no`, `true`, `false`, `on`, `off`,
   `null`, in any case. Written bare, such a ref is refused; written with its
   family or its file, it is an ordinary ref.

## Three separators, three meanings

- **`/` crosses files.** The local id is a path inside its namespace's root.
- **`:` enters a file.** It names a part with an identity of its own: a
  requirement, a check, a type, an operation, a control, an obligation or a
  block uid. Our own part ids are kebab-case; an issuer's clause number is kept
  as the issuer writes it (`A.5.15`, `9(33)`).
- **`#` is a coordinate, never an identity.** It marks a heading anchor or a
  section slot, which move when a heading is reworded (six anchors already
  retired that way are in [`RETIRED.md`](../RETIRED.md)). Nothing joins on one,
  and the fabric never records one as a node's identity.

**A version is never part of an id.** A citation is a ref and a version
(`ohs/policy@1.1.0`), or, in a data field, the pair of a ref and a digest.

## Three written forms

| Form | Example | Used |
|---|---|---|
| Short | `register-claims-namespace`, `RegisterRequest`, `ISO/27001:A.5.15` | In a field whose family is declared, naming something in this file or this namespace's imports |
| Namespace-qualified | `//example/ohs/policy` | A reference into another namespace |
| Full | `requirement://weblisk/architecture/orchestrator:register-claims-namespace` | Anywhere without a typed field: the fabric's ledger, a run statement, an export, a prompt's manifest |

## Families

A family says what sort of thing a ref names. Every kind
[`schemas/kinds`](kinds.md#declared-kinds) declares is a family, so adding a
kind adds a family and nothing here changes. The block below declares the
families that name something which is not a kind of node: a part of a file, or
a file's own sort. A tool reads the two together and keeps no list of its own.

## Namespaces

A namespace is the authority under which a local id is unique. A repository
declares its own once, in a `catalog.yaml` at its root (this corpus's is
[`catalog.yaml`](../catalog.yaml), `namespace: weblisk`), and **no file states
its own id**: a file's id is its path under that root. A tenant's namespace is
chosen when the tenant is created and appears only in that tenant's own files.

**Reserved names** are declared below. They can never be claimed, and they are
the only namespaces, besides a repository's own, that may appear in a
repository Weblisk publishes. `example` and `test` exist for that reason: a
fixture that needs a second namespace uses one of them, so no file names a
person's or a customer's organisation.

Also never claimable, and enforced where namespaces are claimed rather than
here:

- every place code, as [`applies_in`](standard.md#applies_in--where-a-standard-has-force)
  writes it, and every issuer code a standard work's id begins with (`iso`,
  `nist`, `ca-on`), compared without case;
- any name whose **skeleton** equals a reserved name's. The skeleton is the
  name in lower case with `0` read as `o` and `1` read as `l`, so `examp1e` and
  `web1isk` are refused.

**Standard works are not namespaced.** `ISO/27001` is the issuer's code, an
authority of its own. A transcription of it is a file someone wrote, and is
namespaced: `standard://weblisk/ISO/27001`. A tenant's generated standard is
`standard://<its namespace>/ISO/27001`, extending the published one at its
digest.

**Retired is never reused.** A namespace that is given up, and a part id that
is retired from its file, stay retired; neither is issued again to anything
else.

## How a short ref resolves

1. this file's parts;
2. this namespace;
3. the namespaces this repository imports, declared once in its
   `catalog.yaml`, limited to what this file `requires`.

**Two matches is an error that asks for qualification.** The first match never
wins, and an override is an explicit `extends`.

## Declaration

```yaml
# Read by tools. Families here are the ones that are not kinds; every
# kind in schemas/kinds.md is a family as well.
families:
  - type        # a declared type:              type://weblisk/protocol/types:RegisterRequest
  - operation   # an operation a blueprint serves: operation://weblisk/architecture/orchestrator:register
  - spec        # a programme's artifact specification: spec://weblisk/ohs/policy
  - programme   # a programme map:                programme://weblisk/ohs
  - doc         # a tenant document by its uid:   doc://example/3f9c1e0a2b4d
reserved:
  - weblisk     # this corpus, and everything Weblisk publishes
  - system      # also the reserved event namespace (protocol/spec, Namespace Control)
  - local       # never leaves the installation that wrote it
  - example     # fixtures and examples
  - test        # fixtures and tests
  - core
  - tenant
# The grammar's own vectors, whose namespaces are boundary strings
# (two and thirty-nine characters) rather than anybody's name.
names_check_exempt:
  - vectors/ids.json
```

## Where a namespace may appear

A Weblisk repository names no namespace but its own and the reserved ones. A
name in a fixture or an example is a name in a file, and a real organisation's
is not ours to publish. The corpus checks this in
[`checks/names.py`](../checks/names.py), which also confirms that the vectors'
families are exactly the declared ones.

## Verification Checklist

- [ ] Every ref in [`vectors/ids.json`](../vectors/ids.json)'s `valid` set parses to exactly its listed fields, and every ref in its `invalid` set is refused ([`checks/ids.py`](../checks/ids.py))
- [ ] Every valid ref reads back as the same string from YAML as a block-list item, a flow-list item and a mapping value
- [ ] Every invalid ref marked `yaml_unsafe` does not read back as the same string, so the rule that refuses it answers a real fault
- [ ] An accept-everything parser is reported on every invalid vector, so the check reaches what it claims to
- [ ] The vectors' `families` are exactly the kinds of `schemas/kinds` and the families declared above
- [ ] No file in this repository names a namespace that is neither reserved nor this repository's own, and a fixture naming another is reported ([`checks/names.py`](../checks/names.py))
- [ ] A leading word is a family only when it is declared; nothing infers one from shape
- [ ] Nothing records a `#` anchor as an identity
