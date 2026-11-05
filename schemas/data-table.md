# Schema: Data tables (`wl:table`)

How structured data is carried inside an organisation's own document: a
register, a risk table, a form and its submitted records. The schema sits in a
fenced block whose language is `wl:table`, and the rows sit in a plain GFM
table directly below it.

````markdown
```wl:table
id: risk-register
columns:
  - {key: risk, label: Risk, type: text}
  - {key: like, label: Likelihood, type: int}
  - {key: imp, label: Impact, type: int}
  - {key: score, label: Score, type: formula, expr: "like * imp"}
sort: -score
```

| Risk | Likelihood | Impact | Score |
| --- | ---: | ---: | ---: |
| Credential stuffing | 4 | 5 | 20 |
| Stale vendor access | 3 | 3 | 9 |
````

A data table is part of an entry's bytes, so it is content
([`architecture/content`](../architecture/content.md#overview)). No tenant
service interprets it. A client renders it, edits it and submits records to
it, and every client reads the same bytes the same way, because this file is
the one statement of what they mean. A programme's register declares its
columns in this vocabulary
([`schemas/programme`](programme.md#columns)), and a programme's templates
carry `wl:table` blocks
([`schemas/programme-template`](programme-template.md)).

---

## Why it is shaped this way

A table in a governance document has two audiences, and neither can be traded
for the other. A client needs types, formulas and validation. Everyone
downstream needs the *data* in a form they can read without that client:
`git diff`, a reviewer, `grep`, an export, an auditor with a printout.

So the schema and the rows are carried separately, each in a construct the
host format already understands:

- **Editing one cell is a one-line diff**, on the line that visibly holds the
  cell.
- **Every existing reader already works.** An export renders the table it
  already knows how to render, search indexes real words, and a forge renders a
  table.
- **A plain editor degrades it to a readable table** and a small block of
  configuration, never to an opaque blob.
- **Computed cells are written out**, not left blank for a client to fill in.
  A printed risk register whose Score column is empty is a defect.

An entry's digest is over its bytes, and every signature over it is made
against that digest
([`patterns/content-identity`](../patterns/content-identity.md)). So the
round-trip rules below are what keep a signature meaning what it meant.

---

## The block

A data table is a fenced block whose info string is exactly `wl:table`,
followed by a GFM table. A blank line may separate them. The fence holds the
**schema**; the table holds the **rows**.

A fence with no table after it is a table with no rows. A table with no fence
before it is an ordinary GFM table, not a data table.

### The schema

The fence body is a small subset of YAML: top-level `key: value` scalars, one
`columns:` list, and flow maps and flow lists as values. It is small on
purpose: a client must be able to write back every schema it can read, byte for
byte, or opening a document would rewrite it.

| key | holds |
|---|---|
| `uid` | the block's own identity: a UUIDv7, minted once and never edited. Records of the block are keyed by it |
| `id` | the author's code for the block, lowercase, freely renamed. What a relation's `target` and an outbound payload cite |
| `title` | what a person reads above it |
| `columns` | the columns, in order. See [Columns](#columns) |
| `layout` | `form` presents the block one record at a time. Anything else, or absent, is a grid |
| `review` | `required`: a submitted record waits for approval before it lands |
| `approvers` | who must approve a submission: identity ids, or position ids resolved to their holders ([`schemas/position`](position.md#resolving-a-position-to-its-holders)) |
| `approval_order` | `sequential` asks `approvers` one at a time, in the order listed. Anything else, or absent, asks them all at once |
| `sort` | a column key, prefixed with `-` for descending. See [Rows](#rows) |
| `totals` | per-column aggregates for a footer row: `{score: sum, cost: avg}`. A bare list, `[score, cost]`, means `sum` for each. The aggregates are `sum`, `avg`, `count`, `min` and `max` |

A key not in this table is ignored and kept. A key's name is read
case-insensitively. A line starting with `#` is a comment.

**The canonical form.** When a client writes a schema it has changed, it
writes the keys in the order `uid`, `id`, `title`, `columns`, `layout`,
`review`, `approvers`, `approval_order`, `sort`, `totals`, one column per line
as a flow map. `approval_order` is written only beside `approvers`, and only
when it is `sequential`. When the schema it would write parses to the same
configuration as the author's text, it writes the author's text back instead.

### Columns

Each item under `columns:` is one column, in any of three shapes, because all
three are what people write:

```yaml
columns:
  - {key: score, label: Score, type: number}   # flow map: the canonical form
  - owner                                      # a bare key: every property defaults
  - key: due                                   # a block map, continued by any line
    label: Due                                 # indented deeper than its dash
    type: date
```

| property | holds |
|---|---|
| `key` | **required.** The column's identity within the block, lowercase. What a formula, a condition and a record cite. A programme that declares two columns with one key is refused ([`schemas/programme`](programme.md#columns)); in a document, the second is read as a distinct key (`score-2`) so no cell is unreachable |
| `label` | the header a person reads. Defaults to `key`, words capitalised |
| `type` | one of [the column types](#column-types). Absent, or not one of them, is `text` |
| `required` | `true`: the field must be answered |
| `help` | a sentence shown beside the field |
| `width` | a display width in pixels, from 40 to 900 |
| `visible_if` | a [condition](#conditions) for showing the field on a form |
| `min` | for a multi-valued column, the fewest entries that count as answered |
| `bands` | the [readings](#bands) a numeric value falls into |
| `default` | an [expression](#defaults) that fills a new record's field once |
| the type's own | the properties [its type owns](#column-types) |

A label or an option holding a comma, a colon, a bracket or a brace, or
starting with a YAML indicator, is written in double quotes. Unquoted, a comma
ends a flow value, and the header a person reads is not the one written.

**Alignment is not a column property.** It is the table's delimiter row, which
is the one place it is kept.

**A property another type owns is removed when a column changes type.** A
stale `expr` on a text column would revive a formula its author deleted the day
the column became a formula again.

### Column types

| type | owns | the cell holds | numeric | computed | on a form |
|---|---|---|---|---|---|
| `text` | — | text | | | yes |
| `longtext` | — | text, on one line | | | yes |
| `number` | `decimals`, `group` | a number | yes | | yes |
| `int` | `group` | an integer | yes | | yes |
| `currency` | `symbol`, `decimals`, `group` | a number | yes | | yes |
| `percent` | `decimals` | a number | yes | | yes |
| `date` | — | `YYYY-MM-DD` | | | yes |
| `bool` | — | `Yes` or `No`; `true` and `false` are read the same | | | yes |
| `select` | `options` | one of `options`, matched case-insensitively | | | yes |
| `link` | — | a URL | | | yes |
| `user` | — | a person's identity id, never their name | | | yes |
| `signature` | — | who acknowledged the record, as [signature entries](#signatures) | | | yes |
| `attachment` | — | asset paths, comma-separated | | | yes |
| `formula` | `expr`, `format`, `decimals`, `symbol`, `group` | the value `expr` computes, written out | when `format` is | yes | yes, read-only |
| `relation` | `target`, `display`, `keyfield`, `multi` | the keys of rows in another table, comma-separated | | | yes |
| `rollup` | `via`, `field`, `agg` | the fold of a field across a relation, written out | | yes | no |

- `decimals` is 0 to 10. `group: true` writes thousands separators, which are
  off unless asked for. `symbol` is a currency's symbol.
- `format` on a formula names the numeric type its value is formatted as.
- `multi` is `true` unless written `false`. `signature`, `attachment` and a
  multi `relation` are **multi-valued**.
- An attachment's path names a content-addressed asset, so replacing the file
  changes the name, and an old reference stops resolving visibly rather than
  pointing at different bytes.
- A cell holding text a column's type refuses is kept as written and reported
  on the field. A type never destroys what somebody typed.

---

## Rows

The table's **header cells bind to columns by position**. The schema is the
authority for keys, types and formulas, and the table for how many columns
there are:

- a table wider than its schema gains `text` columns, keyed from their header
  cells, and no cell is dropped;
- a header cell that differs from a column's label is the author renaming it in
  the table, and that label is the one read.

Each row after the delimiter row is one record. A cell is trimmed, and `|`
inside it is written `\|`. A blank cell is unanswered, which is never zero.

**`sort`** orders the rows a client writes when it writes the table. A numeric
column, or a formula whose values are all numbers, sorts numerically. Equal
rows keep their order, so writing an already sorted table moves nothing.

**The footer.** When `totals` is declared, a client writes one footer row
after the records. Its first cell is `**Total**`, and each other cell is its
column's aggregate, or blank. A row whose first cell is `**Total**` is the
footer only where `totals` is declared. Otherwise it is a record.

---

## Computed values

A `formula` cell and a `rollup` cell are written out, so a reader without a
client sees the value.

**Except what the clock decides.** A formula that reads `TODAY()` or `NOW()`,
or reads a column that does, is written blank. Written out, it would change
the entry's bytes every day nobody edited it.

**An error is a value.** A cell that cannot be computed is written as its
sentinel, so a reader sees that it did not compute rather than an empty cell
that reads as nothing to report:

| sentinel | means |
|---|---|
| `#ERR` | the value could not be computed |
| `#DIV/0` | a division or remainder by zero |
| `#CYCLE` | the formula depends on itself |
| `#NAME?` | a column or function it names does not exist |
| `#SYNTAX` | the expression cannot be parsed |

An error anywhere in a column makes that column's aggregate an error too. A
total that quietly left out the broken row is a wrong answer presented as a
right one.

### The expression language

```
expr    := ternary
ternary := or ('?' expr ':' expr)?
or      := and ('||' and)*
and     := cmp ('&&' cmp)*
cmp     := add (('=='|'!='|'<='|'>='|'<'|'>') add)*
add     := mul (('+'|'-') mul)*
mul     := unary (('*'|'/'|'%') unary)*
unary   := ('-'|'!') unary | primary
primary := NUMBER | STRING | IDENT | CALL | '(' expr ')'
```

An identifier names a column of the same row. It may contain dots. An
expression has no access to anything outside the table: it is evaluated by an
interpreter, never by the host language's own evaluator, because the document
is content from a repository and is rendered for other people.

| functions | |
|---|---|
| on values | `IF` (evaluates only the branch it takes), `IFBLANK`, `COALESCE`, `NOT`, `ROUND`, `FLOOR`, `CEILING`, `ABS`, `MIN`, `MAX`, `POW`, `SQRT`, `NUMBER`, `CONCAT`, `TEXT`, `UPPER`, `LOWER`, `TRIM`, `LEN`, `CONTAINS`, `BLANK`, `DAYS`, `YEAR` |
| over a column | `SUM`, `AVG`, `COUNT`, `COUNTA`, `MINCOL`, `MAXCOL`, each taking a bare column name |
| of the table | `ROW()`, `ROWS()` |
| of the clock | `TODAY()`, `NOW()` |
| of the context | `ME()`, `SCOPE(kind)`, `LAST()`, which have values only in a [default](#defaults) |

`MIN(a, b)` is the smaller of two values and `MINCOL(a)` the smallest in a
column. They are two names because the call site cannot tell the two meanings
apart, and guessing wrong in a financial table cannot be recovered from.

---

## Relations and rollups

A **relation** column points at rows of another data table:

- `target` is `<path>#<id>`, the entry's path and the target block's `id`. An
  empty path means a block in the same entry.
- The cell holds the target rows' **keys**, never their rendered values. A
  relation is a set: duplicates collapse and blank entries are dropped.
- `keyfield` names the target column holding each row's key, and `display` the
  one shown. Both default to the target's first column.
- A target entry that cannot be read, a block that is not there, and a key
  that names no row are each **reported as broken**, never dropped.

Storing the key is what keeps a signature meaning what it meant. Renaming the
displayed value changes the target's bytes and nothing else, so no document
citing it changes digest.

A **rollup** folds a field of the rows a relation resolved to. `via` names the
relation column of this table, `field` the target column, and `agg` the fold:
`sum`, `avg`, `min`, `max`, `count`, `counta` or `list`. An `agg` outside that
set is refused where it is declared, because it would fold to an empty cell
forever. An empty relation rolls up to blank, except under `count` and
`counta`. A rollup over references some of which are broken reports how many
were not counted, beside its value.

---

## Forms

A block with `layout: form` is the same table presented one record at a time.
Each submission appends one row. It is not another format.

- A form renders every type except `rollup`, which is an aggregate a single
  record does not have.
- With `review: required`, a submission is a proposal that lands only when
  approved ([`architecture/content`](../architecture/content.md#proposals)).
  `approvers` and `approval_order` say who approves it and in what order.
- A form's records are keyed by the block's `uid`. A client never mints a
  `uid` when it opens a document. It mints one when it first writes a
  submission into a block that has none, and when it creates a block.

### Conditions

`visible_if` is one of `<key> = <value>`, `<key> != <value>`, or a bare
`<key>`, meaning that field has any answer. Values compare case-insensitively.
A value holding `=` is quoted.

**A field whose condition cannot be read is shown.** So is one whose condition
names a column the record does not have. A hidden required field is a question
nobody was asked and nobody can see was skipped.

### `min`

On a multi-valued column, `min` is the fewest entries that answer it: at least
one photo, at least two signatures. On a single-valued column it means only
that the field is required.

### Bands

`bands` turns a number into a reading. Each entry is
`<threshold> <label> <role>`, for example `10 High act`. The highest threshold
at or below the value wins, so the entries need not be written in order. The
role is one of a closed set:

| role | says |
|---|---|
| `act` | act now |
| `review` | look soon |
| `settled` | nothing to do |
| `inform` | for information |
| `none` | no reading |

An entry naming any other role is dropped, never coerced. A typo read as
`settled` would show a high risk as resolved. A blank value, or one below
every threshold, has no band. A blank is not a zero.

### Defaults

`default` is an expression a client evaluates once, when a **new** record is
started and the field is empty. Its value is written at submission into the
bytes a typed answer would occupy.

- It is never re-evaluated for a record that exists. Opening an old record does
  not change it.
- `ME()` is the submitting person's identity id. `SCOPE(kind)` is the slug of
  the scope the record is made at (`project` when no kind is given). `LAST()`
  is this column's value in the most recent existing record. Each resolves to a
  stored identifier, never to a display string.
- A default that cannot be resolved leaves the field empty and says why. A
  record defaulted to nobody is a false statement somebody may sign.

`default` is not `expr`. A formula recomputes for ever, and one that reads the
clock is written blank. A default writes once.

### Signatures

A `signature` cell records who acknowledged the record, in order, as entries
joined by `; `. Each entry is a name, then ` — `, then the time the signing
device gave:

```
Pat Roe — 2026-11-05T06:52Z; Sam Lee — 2026-11-05T06:54Z
```

A signature is appended, never edited in place, and a second entry with a name
already present is refused.

**What it establishes, and what it does not.** It establishes who
acknowledged, in what order, as part of the record's content, carried into the
version the submission creates, which the change log attributes
([`architecture/content`](../architecture/content.md#the-change-log)). The
time beside a name is the device's, and it is evidence of order within the
record, not of the moment. The entry's own time is the content service's. A
signature cell is not a key-backed signature. Where one is needed, an entry
attestation is
([`architecture/content`](../architecture/content.md#entry-attestations)).

---

## Round-trip rules

These hold for every client that writes a document holding a data table.

1. **Opening a document changes nothing.** A client never writes a `uid`, a
   computed value, a canonical schema or a sorted order into a document
   because it opened it. Each is written on the next real edit.
2. **What was typed stays as typed.** A cell in a non-computed column is
   written back exactly as read.
3. **The author's schema text survives** wherever it means the same as the
   canonical form ([The schema](#the-schema)).
4. **An unchanged table is written back byte for byte.**

---

## What this file does not declare

- `wl:view`, a block that shows another table's rows as a report, and the
  `wl:section` comments that mark an entry's sections. Each is in-band
  structure of its own, and neither is declared in the corpus yet.
- How a client lays a table out, which controls it offers, and how it formats
  a number for display.

## Known gaps

**One implementation.** The only reader and writer today is Weblisk Studio's
editor (`ui/dist/js/core/doc/data-block.js` with `data-formula.js`,
`data-relation.js` and `data-default.js`). The CLI neither reads nor writes a
data table. Nothing yet holds that implementation to this file, and no vectors
are published.

**`approvers` mixes two kinds of name.** A published template names
positions, and a block a person makes in a client names identity ids. A client
cannot tell which an entry is except by trying to resolve it as a position.

**The schema subset is not declared as a grammar.** Which YAML a client must
read is stated in [The schema](#the-schema) by example, not as a grammar a
parser could be checked against.

---

## Verification Checklist

- [ ] A fenced block whose info string is `wl:table` followed by a GFM table is read as one data table, and a GFM table with no such fence before it is not ([The block](#the-block)) <!-- wl:check fenced-block-info-string-wl-table -->
- [ ] Opening a document holding a data table and saving it unchanged leaves its digest unchanged, and no `uid`, computed value, canonical schema or sort order is written because it was opened ([Round-trip rules](#round-trip-rules)) <!-- wl:check opening-document-holding-data-table-saving -->
- [ ] A column whose `type` is absent or not one of the column types is read as `text` ([Columns](#columns)) <!-- wl:check column-type-absent-not-column-types -->
- [ ] Header cells bind to columns by position; a table wider than its schema gains `text` columns and drops no cell ([Rows](#rows)) <!-- wl:check header-cells-bind-columns-position-table -->
- [ ] A formula or rollup cell is written out, a formula that reads the clock is written blank, and a cell that cannot be computed is written as its sentinel ([Computed values](#computed-values)) <!-- wl:check formula-rollup-cell-written-out-formula -->
- [ ] An error anywhere in a column makes that column's aggregate an error ([Computed values](#computed-values)) <!-- wl:check error-anywhere-column-makes-columns-aggregate -->
- [ ] A relation cell holds the target rows' keys, never their rendered values, and a target entry, block or row that cannot be found is reported broken ([Relations and rollups](#relations-and-rollups)) <!-- wl:check relation-cell-holds-target-rows-keys -->
- [ ] An `agg` outside `sum`, `avg`, `min`, `max`, `count`, `counta` and `list` is refused where it is declared, and an empty relation rolls up to blank except under `count` and `counta` ([Relations and rollups](#relations-and-rollups)) <!-- wl:check agg-outside-sum-avg-min-max -->
- [ ] A field whose `visible_if` cannot be read, or names a column the record does not have, is shown ([Conditions](#conditions)) <!-- wl:check field-visible-cannot-read-names-column -->
- [ ] A `bands` entry naming a role outside the closed set is dropped, and a blank value has no band ([Bands](#bands)) <!-- wl:check bands-entry-naming-role-outside-closed -->
- [ ] A `default` is evaluated only for a new record, and one that cannot be resolved leaves the field empty with its reason ([Defaults](#defaults)) <!-- wl:check default-evaluated-new-record-cannot-resolved -->
- [ ] A signature is appended, never edited in place, and a second entry with a name already present is refused ([Signatures](#signatures)) <!-- wl:check signature-appended-never-edited-place-second -->
- [ ] A row whose first cell is `**Total**` is read as the footer only where `totals` is declared ([Rows](#rows)) <!-- wl:check row-first-cell-total-read-footer -->
