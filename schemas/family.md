---
family: family@1
version: 1.0.0
kind: specification
noun: family
capabilities: [author, versioned]
---
# Schema: Families

A family says how a file of one sort is written: its header, its sections, the
typed blocks each section holds, and what each part of the file is for. A
**family declaration** is a markdown file of the family `family`, and this file
is the declaration of that family, so it validates against itself.

A file family is not a ref family. A ref family ([`schemas/names`](names.md#families))
says what sort of thing a ref names; a file family says how a file is written.
A declaration's `kind` names the kind ([`schemas/kinds`](kinds.md#declared-kinds))
its files are, and so the ref family they are named in.

The typed blocks a slot may hold, and the closed vocabulary their fields are
written in, are [`schemas/blocks`](blocks.md)'s. This file says how a file is
divided into parts; that one says what a block in a part may contain. Test
vectors for both are in [`vectors/grammar/`](../vectors/grammar/README.md).

## Requirements

```yaml
requirements:
  - id: family-names-declaration
    level: must
    text: >-
      A file's header names the family it is written to as `family:
      <name>@<major>`, where <name> is the declaration's file name under
      schemas/ and <major> is the major of that declaration's version.
      A file with no `family:` is read as the family whose `match` covers its
      path, and a path two families match is a finding.
  - id: declaration-validates-itself
    level: must
    text: >-
      This file walks as a file of the family it declares, with no finding a
      policy refuses.
  - id: spans-partition
    level: must
    text: >-
      A walk divides the file's bytes into parts whose spans are sorted,
      contiguous and cover [0, length) exactly. A span is a pair of byte
      offsets, end exclusive. The walker never rewrites a byte.
  - id: part-boundaries
    level: must
    text: >-
      Parts begin at offset 0 and at these points only: the end of the header's
      closing line; the start of a level-1 or level-2 heading line outside a
      fence; the start of a block's opening line or first table row; the end of
      a block's closing line or last table row. Each part ends where the next
      begins.
  - id: bytes-as-written
    level: must
    text: >-
      A UTF-8 byte-order mark at offset 0 belongs to the first part and is not
      content. A line ends at LF, and a CR before that LF belongs to the line.
      Headings, fences and the header are recognised identically with either
      line end.
  - id: fences-are-opaque
    level: must
    text: >-
      A fence opens with a line of three or more backticks or tildes, indented
      by at most three spaces, and closes with a line of the same character at
      least as long and nothing else. Every line inside a fence is content: a
      heading, a fence of the other character or a shorter one, or a block
      inside it opens nothing.
  - id: slots-by-heading
    level: must
    text: >-
      The level-1 heading opens the slot whose heading is {level: 1}. Each
      level-2 heading opens the first slot whose heading, alias or starts_with
      it matches, compared after trimming and collapsing spaces; deeper
      headings stay inside the slot that holds them. A level-2 heading that
      matches no slot opens an undeclared part under the `undeclared` policy.
  - id: blocks-by-root-key
    level: must
    text: >-
      A fence whose info string is `yaml`, outside any other fence, whose value
      is a mapping with exactly one root key that blocks.md catalogues, is a
      block of that type. A table in a slot that lists a catalogued block of
      form table is a block of that type, read by column name. Any other fence
      or table is text of its slot.
  - id: json-data-model
    level: must
    text: >-
      A header or block is read as YAML into the JSON data model only. An
      anchor, alias, tag, merge key or second document is refused, and a scalar
      that is not quoted keeps the type the YAML 1.2 core schema gives it, so
      an unquoted date is a string.
  - id: legacy-before-schema
    level: must
    text: >-
      Each key header.legacy names is removed before header.schema is applied,
      and is a finding under its own policy, never a second finding from the
      schema.
  - id: parts-carry-use
    level: must
    text: >-
      Every part carries its slot, use and send. The header's part, an
      undeclared part and text before the first slot have slot null; the
      header's part is navigates and always, and each of its entries takes the
      use and send header.uses gives its key, or navigates and always when it
      gives none. A slot's `send` defaults by
      its `use` as the use table states, and a part of a slot whose use is
      explains is sent `cited` when it carries a `wl:explains` marker and
      `on-request` otherwise.
  - id: digests-by-value
    level: must
    text: >-
      A header's or block's digest, and each of its entries' digests, is
      sha256 over the RFC 8785 serialisation of its value. A text part's
      digest is sha256 over its bytes. Every digest is written sha256:<hex>.
  - id: findings-closed
    level: must
    text: >-
      A finding's code is one of the codes declared in this file's
      definitions, and carries the policy that decides it. A file validates
      when no finding's policy is refuse.
  - id: repeatable-slot-key
    level: must
    text: >-
      A slot whose count allows more than one takes each occurrence's key from
      its `key`: the first `wl:explains` marker in it for marker, the heading
      text after starts_with for heading. Two occurrences with one key, or an
      occurrence with none, is refused.
```

## Header

```yaml
header:
  schema:
    type: object
    required: [family, version]
    unevaluatedProperties: false
    properties:
      family:       {const: family@1}
      version:      {$ref: "blocks#/$defs/version"}
      kind:         {type: string, description: "A kind schemas/kinds declares: what the family's files are."}
      match:        {type: array, items: {type: string, format: glob}}
      extends:      {$ref: "#/$defs/family-name"}
      noun:         {type: string, pattern: "^[a-z][a-z-]*$"}
      capabilities: {type: array, items: {enum: [author, versioned, depends, generates, publishable, adoptable]}}
      template:     {type: string, description: "A corpus path."}
      location:     {type: string, format: glob}
      adopt:
        type: object
        unevaluatedProperties: false
        properties:
          mode:   {enum: [link, copy]}
          record: {type: string}
      generates:    {enum: [code, document, none]}
  uses:
    extends: {use: depends, resolves: family, send: always}
    template: {use: navigates, send: on-request}
```

## Sections

```yaml
sections:
  undeclared: {policy: allow, use: explains, send: on-request}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1},
       prose: required, content: {max_paragraphs: 4}, use: navigates}
    - {slot: requirements, heading: Requirements, required: false, count: {max: 1},
       blocks: [{type: requirements, count: {min: 1, max: 1}}], prose: forbidden,
       use: binds, produces: [code.behaviour]}
    - {slot: header, heading: Header, required: {when: {header_present: kind}},
       count: {max: 1}, blocks: [{type: header, count: {min: 1, max: 1}}],
       use: shapes, produces: [schema.json]}
    - {slot: sections, heading: Sections, required: {when: {header_present: kind}},
       count: {max: 1}, blocks: [{type: sections, count: {min: 1, max: 1}}],
       use: shapes, produces: [schema.json]}
    - {slot: catalogue, heading: Blocks, required: false, count: {max: 1},
       blocks: [{type: blocks, count: {min: 1, max: 1}}], use: shapes,
       produces: [schema.json]}
    - {slot: definitions, heading: Definitions, required: false, count: {max: 1},
       blocks: [{type: defs, count: {min: 1, max: 1}}], use: shapes,
       produces: [schema.json]}
    - {slot: verifies, heading: Verification, required: {when: {block_present: requirements}},
       count: {max: 1}, blocks: [{type: verifies, count: {min: 1, max: 1}}],
       prose: forbidden, use: verifies, produces: [code.test, check]}
```

A declaration with a `kind` declares files and has a Header and a Sections
slot. One without is a library of definitions other declarations cite, as
[`schemas/blocks`](blocks.md) is. Every other heading in a declaration is
explanation, which is why `undeclared` here is `allow`: a declaration's prose
stays where it is, as the reason for what its blocks say.

## The grammar keywords

The keywords are closed and implemented in code; adding one is a change to
this file and to every walker. Their shapes are this file's definitions, and
what each means is below.

| Keyword | Where | Meaning |
|---|---|---|
| `match`, `kind`, `extends` | header | Which paths the family covers when a file names no family, which kind its files are, and the family it inherits slots and header properties from |
| `noun`, `capabilities`, `template`, `location`, `adopt`, `generates` | header | What the verbs acting on the family need: the word a person reads, which verbs apply, the starting file, where new files go, how an adoption is recorded, and what a build makes from one |
| `header.schema` | header block | JSON Schema 2020-12 for the frontmatter, with unknown keys refused |
| `header.uses` | header block | Per field: its `use`, the ref family it `resolves` to, and its `send` |
| `header.legacy` | header block | Keys still found in older files, each `report` or `refuse`. Used only while files are migrated |
| `slot`, `heading`, `aliases` | slot | The slot's stable key, and the heading text that opens it. Heading text is never identity |
| `required` | slot | `true`, `false`, `report`, or `{when: {header_present: <key>}}` or `{when: {block_present: <type>}}` |
| `count`, `key` | slot | How many times the slot may occur, and where a repeatable slot's key comes from |
| `blocks` | slot | Which catalogued block types the slot holds, each with its own count |
| `prose` | slot | `required`, `allowed` or `forbidden`: whether text other than the heading and blank lines may appear |
| `content` | slot | Closed predicates on the slot's text: `min_items`, `max_paragraphs`, `no_rfc2119`, `mentions` |
| `guidance`, `authority` | slot | A judged requirement and the ref whose text the judgement cites. Reported apart, never a build failure |
| `undeclared` | sections block | `report`, `allow` or `refuse` for a level-2 heading no slot matches, with the `use` and `send` its part takes |
| `use`, `send`, `produces` | slot, header field | What the part is for, when a prompt receives it, and what a build makes from it |

`use` and `send` are closed and live in code; `produces` is open and lives in
data, the same split [`schemas/kinds`](kinds.md#the-model-open-kinds-closed-capabilities)
uses. A `produces` value no mapping binds is reported as unproduced, never
dropped.

| `use` | Binding | Default `send` |
|---|---|---|
| `navigates` | no | `always` |
| `depends` | yes | `always` |
| `binds` | yes | `cited` |
| `shapes` | yes | `referenced` |
| `exposes`, `emits`, `configures` | yes | `cited` |
| `verifies` | yes | `cited` |
| `declares` | yes | `always` |
| `instructs` | no | `always` |
| `explains` | never | `cited` through `wl:explains`, otherwise `on-request` |
| `illustrates` | never | `on-request` |

The `capabilities` here are the verbs a person may use on a family's files.
They are not [`schemas/kinds`](kinds.md#capabilities)' capabilities, which say
what a kind of node drives.

## The projection

A walk's output is a **projection**, whose shape is `projection` below. It
lists every part of the file in order, so a reader that never parses markdown
still sees that everything exists, and can be sent only the parts its task
selects.

<!-- wl:explains spans-partition -->
Spans partition the file so that a byte is never in two parts, which would be
sent twice and digested twice, and never in none, which would be content no
reader could be shown. The partition is what makes "the model was sent
everything this task needs" checkable: every byte has an address.

<!-- wl:explains digests-by-value -->
A block's digest is over its value, not its bytes, so re-indenting a block or
reordering a mapping's keys changes the file's `version_hash` and leaves every
block's digest, and so everything that cites one, unchanged. A text part has
no value but its bytes.

## Definitions

```yaml
defs:
  family-name: {type: string, pattern: "^[a-z][a-z0-9-]*$"}
  family-ref:
    type: string
    pattern: "^[a-z][a-z0-9-]*@[1-9][0-9]*$"
    description: "<name>@<major>: the family a file is written to."
  use: {enum: [navigates, depends, binds, shapes, exposes, emits, configures, verifies, declares, instructs, explains, illustrates]}
  send: {enum: [always, cited, referenced, on-request]}
  policy: {enum: [report, allow, refuse]}
  count:
    type: object
    description: "Absent, a slot occurs at most once and a block any number of times; a count with no max is unbounded."
    unevaluatedProperties: false
    properties:
      min: {type: integer, minimum: 0}
      max: {type: integer, minimum: 1}
  required:
    oneOf:
      - {type: boolean}
      - {const: report}
      - type: object
        required: [when]
        unevaluatedProperties: false
        properties:
          when:
            type: object
            minProperties: 1
            maxProperties: 1
            unevaluatedProperties: false
            properties:
              header_present: {type: string}
              block_present: {type: string}
  heading:
    oneOf:
      - {type: string}
      - type: object
        unevaluatedProperties: false
        minProperties: 1
        maxProperties: 1
        properties:
          level: {const: 1}
          starts_with: {type: string}
  content:
    type: object
    unevaluatedProperties: false
    properties:
      min_items: {type: integer, minimum: 1}
      max_paragraphs: {type: integer, minimum: 1}
      no_rfc2119: {type: boolean}
      mentions: {type: array, items: {type: string}}
  slot:
    type: object
    required: [slot, heading, use]
    unevaluatedProperties: false
    properties:
      slot: {$ref: "#/$defs/family-name"}
      heading: {$ref: "#/$defs/heading"}
      aliases: {type: array, items: {type: string}}
      required: {$ref: "#/$defs/required"}
      count: {$ref: "#/$defs/count"}
      key: {enum: [marker, heading]}
      blocks:
        type: array
        items:
          type: object
          required: [type]
          unevaluatedProperties: false
          properties:
            type: {type: string}
            count: {$ref: "#/$defs/count"}
      prose: {enum: [required, allowed, forbidden]}
      content: {$ref: "#/$defs/content"}
      use: {$ref: "#/$defs/use"}
      send: {$ref: "#/$defs/send"}
      produces: {type: array, items: {type: string}}
      guidance: {type: string}
      authority: {$ref: "blocks#/$defs/ref"}
  header-block:
    type: object
    required: [schema]
    unevaluatedProperties: false
    properties:
      schema: {type: object, description: "JSON Schema 2020-12 for the frontmatter."}
      uses:
        type: object
        additionalProperties:
          type: object
          required: [use]
          unevaluatedProperties: false
          properties:
            use: {$ref: "#/$defs/use"}
            resolves: {type: string, description: "A ref family schemas/names declares."}
            send: {$ref: "#/$defs/send"}
      legacy:
        type: object
        description: "A key, or a dotted path to one, still found in older files."
        additionalProperties: {enum: [report, refuse]}
  sections-block:
    type: object
    required: [slots]
    unevaluatedProperties: false
    properties:
      undeclared:
        type: object
        required: [policy]
        unevaluatedProperties: false
        properties:
          policy: {$ref: "#/$defs/policy"}
          use: {$ref: "#/$defs/use"}
          send: {$ref: "#/$defs/send"}
      slots: {type: array, minItems: 1, items: {$ref: "#/$defs/slot"}}
  finding-code:
    enum:
      - missing-header      # no header, and no family matches the path
      - unknown-family      # family: names no declaration, or a major it does not have
      - match-ambiguous     # two families' match cover the path
      - header-schema       # the header fails header.schema; subject is the JSON pointer
      - legacy-key          # a key header.legacy names; subject is the key
      - legacy-spelling     # a field type blocks.md reads in report mode; subject is the spelling
      - yaml-feature        # an anchor, alias, tag, merge key or second document
      - unclosed-fence      # a fence runs to the end of the file
      - missing-slot        # a required slot does not occur; subject is the slot
      - slot-count          # a slot occurs more often than its count allows
      - slot-order          # a slot occurs before one declared ahead of it
      - undeclared-slot     # a level-2 heading no slot matches; subject is its text
      - slot-key-missing    # an occurrence of a repeatable slot has no key
      - duplicate-key       # two occurrences of a repeatable slot share a key
      - prose-forbidden     # text in a slot whose prose is forbidden
      - prose-required      # no text in a slot whose prose is required
      - content             # a content predicate fails; subject is the predicate
      - block-not-allowed   # a block of a type the slot does not list
      - block-count         # a block type occurs outside its count in a slot
      - block-missing       # a block type with count min 1 does not occur
      - multi-root          # a yaml fence with a catalogued root key and another
      - block-unparsed      # a block that does not parse
      - block-schema        # a block fails its type's schema; subject is the JSON pointer
      - duplicate-entry     # two entries of one block share an id
      - unknown-column      # a table column the block type does not name
      - missing-column      # a required column a table does not have
  digest: {type: string, pattern: "^sha256:[0-9a-f]{64}$"}
  span:
    type: array
    minItems: 2
    maxItems: 2
    items: {type: integer, minimum: 0}
  finding:
    type: object
    required: [code, policy, span]
    unevaluatedProperties: false
    properties:
      code: {$ref: "#/$defs/finding-code"}
      policy: {$ref: "#/$defs/policy"}
      span: {$ref: "#/$defs/span", description: "The span of the part it was found in; for something absent from the file, the slot's first part, or [length, length] when the slot itself is absent."}
      subject: {type: string}
  entry:
    type: object
    required: [id, digest]
    unevaluatedProperties: false
    properties:
      id: {type: string, description: "The entry's part id, or a header key."}
      use: {$ref: "#/$defs/use"}
      send: {$ref: "#/$defs/send"}
      digest: {$ref: "#/$defs/digest"}
  part:
    type: object
    required: [span, part, slot, use, send, digest]
    unevaluatedProperties: false
    properties:
      span: {$ref: "#/$defs/span"}
      part: {enum: [header, text, block]}
      slot: {oneOf: [{$ref: "#/$defs/family-name"}, {type: "null"}]}
      key: {type: string, description: "A repeatable slot's key, on each of its parts."}
      block: {type: string, description: "A block's catalogued type."}
      family: {type: string, description: "The ref family the block's entries are named in."}
      use: {$ref: "#/$defs/use"}
      send: {$ref: "#/$defs/send"}
      explains: {type: array, items: {type: string}, description: "The ids its wl:explains markers name."}
      digest: {$ref: "#/$defs/digest"}
      entries: {type: array, items: {$ref: "#/$defs/entry"}}
  projection:
    type: object
    required: [file, family, length, version_hash, parts, findings]
    unevaluatedProperties: false
    properties:
      file: {type: string}
      family: {$ref: "#/$defs/family-ref"}
      declaration: {type: string, description: "The declaration walked against, when it is not schemas/<name>.md."}
      length: {type: integer, minimum: 0}
      version_hash: {$ref: "#/$defs/digest"}
      parts: {type: array, items: {$ref: "#/$defs/part"}}
      findings: {type: array, items: {$ref: "#/$defs/finding"}, description: "In order of span start, then code."}
```

Every entry of `finding-code` carries the policy that decides it in the
finding itself: `header-schema`, `yaml-feature`, `block-schema` and the
cardinality codes are `refuse`; `legacy-key`, `undeclared-slot` and
`missing-slot` take the policy their declaration gives; `slot-order` and
`legacy-spelling` are `report` in grammar 1 and become `refuse` once migration
is done.

## Verification

```yaml
verifies:
  - id: family-walks-itself
    covers: [declaration-validates-itself, family-names-declaration]
    check: walk-validates
    assertion: Walking schemas/family.md against itself reports no finding whose policy is refuse.
  - id: family-self-mutation-refused
    covers: [declaration-validates-itself]
    check: walk-refuses
    assertion: A copy of schemas/family.md whose sections block names a slot key `Title` is refused with block-schema.
  - id: projections-partition
    covers: [spans-partition, part-boundaries]
    check: vectors-agree
    assertion: Every vector's expected projection has sorted, contiguous spans covering its file, and a projection with a one-byte gap is reported.
  - id: walker-matches-vectors
    covers: [part-boundaries, bytes-as-written, fences-are-opaque, slots-by-heading, blocks-by-root-key, json-data-model, legacy-before-schema, parts-carry-use, digests-by-value, findings-closed, repeatable-slot-key]
    check: vectors-agree
    assertion: Walking each file in vectors/grammar/ against the declaration its projection names gives exactly that projection.
```
