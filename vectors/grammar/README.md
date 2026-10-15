# Grammar vectors

Files walked by [grammar 1](../../schemas/family.md), each beside the
projection a walk of it must produce. A walker is bound by these, not by a
copy of the rules: walking `<name>.md` against the declaration its projection
names (`declaration`, or `schemas/<family>.md` when it names none) must give
exactly `<name>.projection.json`, compared as JSON values. A projection's
shape is [`schemas/family`](../../schemas/family.md#definitions)' `projection`.

[`checks/spans.py`](../../checks/spans.py) confirms that every vector here has
a projection and that each partitions its file at the file's own length and
`version_hash`. That is all a check outside a walker can confirm; everything
else in a projection is what a walker is tested against.

| Vector | What it exercises |
|---|---|
| `test-blueprint.md` | A family declaration, walked as a file of the family `family`. Every other vector here is written to it |
| `minimal.md` | A header with a `requires` entry and an unquoted date, which is read as a string; a title; one requirements and one verifies block |
| `crlf.md` | `minimal.md` with CRLF line ends. Its block and header digests are `minimal.md`'s, because a digest is over the value |
| `bom.md` | `minimal.md` after a UTF-8 byte-order mark, which belongs to the header's part |
| `nested-fences.md` | A fence inside a fence, a `## ` heading and a yaml block inside an example, and a longer fence holding a shorter one: none of them opens a slot or a block |
| `aliases-and-repeats.md` | A slot opened by its alias (`Data Types`), and a repeatable slot keyed by its `wl:explains` markers, one occurrence of which has none and is refused |
| `multi-root.md` | A yaml fence with a catalogued root key and a second one: no block, refused, and the slot's required block reported missing |
| `table.md` | An errors block written as a table, its columns in another order and one the catalogue does not name, which is reported |
| `table-as-yaml.md` | The same errors as a yaml block, with the same entry digests as `table.md` |
| `legacy.md` | A legacy header key reported, an old type spelling reported and read as the type it names, an unknown spelling refused, and a section no slot declares reported |

A file here is data. Its bytes are its point, so the repository keeps them as
written (`.gitattributes`); an edit to one is an edit to its projection too,
which `checks/spans.py` refuses until both agree.
