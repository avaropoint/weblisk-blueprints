---
family: schemas/family@1
version: 1.0.0
kind: instruction
noun: instruction
match: [instructions/*.md]
capabilities: [author, versioned, publishable]
template: templates/instruction.md
location: instructions/*.md
generates: none
---
# Instruction Schema

The family of the files in [`instructions/`](../instructions/README.md): every
sentence a build gives a model, written once, in the corpus, and passed to the
model as written. An instruction is one file. Its path is its id, its text is
what the model is given, and its digest is what the record cites
([`architecture/engine`](../architecture/engine.md#instructions)).

An instruction is not a skill. A skill ([`skills/`](../skills/README.md)) is a
guide a coding agent reads at its own discretion; a programme's `skills:` are
what a tenant's agents are given at run time
([`schemas/programme`](programme.md#skills--files-the-programme-brings)). An
instruction is what the engine gives a model inside one build step, and the
engine gives a model no sentence that is not an instruction's
([`architecture/engine`](../architecture/engine.md#instructions)).

## Requirements

```yaml
requirements:
  - id: instruction-path-is-id
    level: must
    text: An instruction's id is its path under instructions/ without .md. It states no id of its own, and is cited as instructions/<id>.
  - id: instruction-in-declared
    level: must
    text: Every step in an instruction's in is one architecture/engine declares, and one whose model is called.
  - id: instruction-slots-placed
    level: must
    text: Every slot an instruction declares is an input of every step in its in, and is written in its text exactly once as {{name}}; the text writes no {{name}} it does not declare.
  - id: instruction-one-text
    level: must
    text: The Text section holds exactly one fence, whose info string is text, and no other prose.
  - id: instruction-every-step
    level: must
    text: Every step architecture/engine declares with a model call is named in the in of at least one instruction.
  - id: instruction-verbatim
    level: must
    text: An instruction is given to the model as its folded text, unchanged. A tool may place other inputs beside it, and never rewords, shortens or leaves out any of it.
```

## Header

The family `schemas/instruction`, strict from its first file: a key the header
does not declare is refused, and `version` and `in` are required.

```yaml
header:
  schema:
    type: object
    required: [family, version, in]
    unevaluatedProperties: false
    properties:
      family:  {const: schemas/instruction@1}
      version: {$ref: "schemas/blocks#/$defs/version"}
      in:      {type: array, minItems: 1, items: {type: string, pattern: "^[a-z][a-z-]*$"}}
      slots:   {type: array, items: {type: string, pattern: "^[a-z][a-z-]*$"}}
```

| Key | Means |
|---|---|
| `in` | the build steps whose model prompt carries this instruction, each a step id [`architecture/engine`](../architecture/engine.md#the-build-steps) declares with a model call |
| `slots` | the inputs this instruction's text places, each an input every step in `in` declares. A slot is written in the text as `{{name}}`, and the engine puts the input there and nowhere else. Absent, the text places none, and the step's inputs follow the instructions in the prompt, labelled with their names |

## Sections

```yaml
sections:
  undeclared: {policy: refuse}
  slots:
    - {slot: title, heading: {level: 1}, required: true, count: {min: 1, max: 1},
       prose: required, content: {max_paragraphs: 2}, use: navigates}
    - {slot: why, heading: Why, required: true, count: {min: 1, max: 1},
       prose: required, use: explains}
    - {slot: text, heading: Text, required: true, count: {min: 1, max: 1},
       prose: required, use: instructs}
```

**Why** says what went wrong without this instruction, measured where it was
measured, so the next person to reword it knows what the wording is holding
off. It is never sent to a model.

**Text** holds the instruction as one fence whose info string is `text`, and
nothing else. What the model is given is that fence's lines, folded as a
YAML `>-` scalar folds: trailing spaces are dropped, consecutive lines are
joined by one space, a blank line between two lines is one line feed, and the
text has no final line feed. Nothing else in the file is sent.

## How the requirements are held

[`checks/instructions.py`](../checks/instructions.py) holds the first five
over every file in `instructions/`, reading the steps from
[`architecture/engine`](../architecture/engine.md#the-build-steps).
`instruction-verbatim` binds the engine, and
[`checks/engine-neutrality.py`](../checks/engine-neutrality.py) finds a
sentence of an instruction held in the tools' own source.

## Versions and digests

An instruction is versioned as every corpus file is
([`schemas/common`](common.md#blueprint-versions)): a change to its bytes moves
its `version`. A change to its Text is a new instruction for every record that
cites it: the engine records, on every model action, the instruction's ref,
its version and the SHA-256 of the file's bytes as read
([`schemas/run-statement`](run-statement.md#actions)), and an action is reused
only under the same digest ([`architecture/engine`](../architecture/engine.md#the-record)).

A test translated under an earlier revision of an instruction is not
re-translated because the instruction moved; it is marked translated under an
older instruction, and translating it again is a change somebody makes on
purpose ([`architecture/engine`](../architecture/engine.md#the-record)).

## Verification

```yaml
verifies:
  - id: instructions-hold
    covers: [instruction-path-is-id, instruction-in-declared, instruction-slots-placed, instruction-one-text, instruction-every-step]
    check: corpus-check
    assertion: checks/instructions.py reports nothing over instructions/; a copy with a placeholder its header does not declare, and an engine step list with a model step no instruction names, are each reported.
  - id: instructions-not-in-tools
    covers: [instruction-verbatim]
    check: corpus-check
    assertion: checks/engine-neutrality.py reports a sentence of an instruction's text found in a string literal of the tools' source.
```
