# Grammar vectors

Files walked by [grammar 1](../../schemas/family.md), each beside the
projection a walk of it must produce. A walker is bound by these, not by a
copy of the rules: walking `<name>.md` against the declaration its `family:`
names (`vectors/grammar/test-blueprint`, `vectors/grammar/test-programme`,
`schemas/architecture`, or `schemas/family` for a declaration) must give exactly
`<name>.projection.json`, compared as JSON values. A projection's shape is
[`schemas/family`](../../schemas/family.md#definitions)' `projection`.

[`checks/spans.py`](../../checks/spans.py) confirms that every vector here has
a projection and that each partitions its file at the file's own length and
`version_hash`, and [`checks/findings.py`](../../checks/findings.py) that
every finding carries the policy its code has. That is all a check outside a
walker can confirm; everything else in a projection is what a walker is tested
against.

| Vector | What it exercises |
|---|---|
| `test-blueprint.md` | A family declaration, walked as a file of the family `schemas/family`. Every vector here but the programme and architecture ones is written to it, as `vectors/grammar/test-blueprint@1` |
| `test-programme.md` | A family declared in migration mode: two legacy header keys, one a dotted path, reported; a missing `version` reported through `header.required`. `migration.md` is written to it, as `vectors/grammar/test-programme@1` |
| `minimal.md` | A header with a `requires` entry and an unquoted date, which is read as a string; a title; one requirements and one verifies block |
| `crlf.md` | `minimal.md` with CRLF line ends. Its block and header digests are `minimal.md`'s, because a digest is over the value |
| `bom.md` | `minimal.md` after a UTF-8 byte-order mark, which belongs to the header's part |
| `nested-fences.md` | A fence inside a fence, a `## ` heading and a yaml block inside an example, and a longer fence holding a shorter one: none of them opens a slot or a block |
| `aliases-and-repeats.md` | A slot opened by its alias (`Data Types`), and a repeatable slot keyed by its `wl:explains` markers, one occurrence of which has none and is refused |
| `multi-root.md` | A yaml fence with a catalogued root key and a second one: no block and no part of its own, but text of its slot, refused as multi-root and not also as prose in a slot that forbids it; the slot's required block is reported missing |
| `table.md` | An errors block written as a table, its columns in another order and one the catalogue does not name, which is reported |
| `table-as-yaml.md` | The same errors as a yaml block, with the same entry digests as `table.md` |
| `legacy.md` | A legacy header key reported, an old type spelling reported and read as the type it names, an unknown spelling refused, and a section no slot declares reported |
| `migration.md` | A file of the migration-mode family with its own id, an obligation id and no version: three findings, each reported, and nothing refused |
| `header-schema.md` | A header key the family does not declare: refused once as header-schema, with the JSON pointer of the key as subject, and still an entry of the header |
| `slot-order.md` | Verification written before the requirements it covers: both slots read, and slot-order reported on the slot written early |
| `unclosed-fence.md` | A fence in the last slot never closed: it runs to the end of the file, the `## ` heading inside it opens nothing, and it is refused as unclosed-fence |
| `yaml-feature.md` | A requirements block using an anchor and an alias: a block whose value is not read, digested over its bytes with no entries, and refused once, with `anchor` as subject |
| `architecture.md` | A copy of [`schemas/architecture.md`](../../schemas/architecture.md), the first real family declaration, walked as a file of `schemas/family`: its Header and Sections blocks, and the older form's prose as undeclared parts, which a declaration allows |
| `architecture-template.md` | A copy of [`templates/architecture.md`](../../templates/architecture.md), walked against the real `schemas/architecture@2`: every block type a blueprint holds, an `Operation:` slot keyed by its marker, and no finding |
| `inert-headings.md` | A setext heading, a heading indented four spaces, a `#` with no space and a heading inside a multi-line comment: all text of the notes slot, with no finding |

The two architecture vectors are exact copies of the files they are named
for, and [`checks/run.sh`](../../checks/run.sh) refuses a copy that differs, so
a change to the declaration or the template is a change to its expected
projection in the same commit.

A file here is data. Its bytes are its point, so the repository keeps them as
written (`.gitattributes`); an edit to one is an edit to its projection too,
which `checks/spans.py` refuses until both agree.
