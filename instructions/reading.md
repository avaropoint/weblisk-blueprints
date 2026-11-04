---
family: schemas/instruction@1
version: 1.0.0
in: [plan, translate, generate, repair]
---
# How a blueprint is read

Which parts of a blueprint bind, which illustrate, and how each form is read,
told to the model rather than left for it to infer.

## Why

A generator that sends a specification without saying how it is structured
has asked the model to infer the document's own rules from the document, and
it infers differently each time
([`architecture/generation`](../architecture/generation.md#how-a-blueprint-is-read),
element 10). A normative sentence in a body paragraph reaches the model as
one line in seventy thousand tokens of context; "The audit log MUST be
chained" is in no table, and is still the specification.

## Text

```text
Read the blueprints you are given by these rules. A yaml block whose root key
is the one its section declares is the contract: every key in it is required.
A table's every row is required, and its columns are read by their names,
never their positions. Prose explains, except that a sentence containing
MUST, MUST NOT or SHALL binds wherever it appears, in a note or a parenthesis
as much as in a section of its own.

These do not bind: a fenced block with no root key in a section whose form is
a yaml block, which is an example; a path, name or value inside a narrative
example, unless a table or a yaml block also declares it; and a section
marked optional, which is not required by its absence.
```
