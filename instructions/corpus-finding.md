---
family: schemas/instruction@1
version: 1.1.0
in: [plan, translate, generate, repair]
---
# Corpus finding

The one form in which a model reports a fault in the corpus in place of its answer.

## Why

A finding is only useful if it can be told apart from a file and checked
against what the model was given. One line in one form lets a generator accept
it only where each quoted passage appears in the blueprints the prompt carried
([`architecture/generation`](../architecture/generation.md#instructions-given-as-written)).
Kind `untestable` was added when the translate step was
([`architecture/engine`](../architecture/engine.md#the-build-steps)): a
criterion no test can settle is a fault in the criterion, and a test written
for it anyway would pass against nothing.

## Text

```text
A corpus finding is your whole answer, on one line: WL-CORPUS-FINDING
followed by a space and a JSON object with the keys kind, first, second and
why. kind is conflict, gap or untestable. For a conflict, first and second
are the two statements, each quoted exactly from the blueprints you were
given. For a gap, first is the sentence of the requirement that needs the
name, quoted exactly, second is the kind of name, and why says what the name
is for. For untestable, which only a test's translation may give, first is
the criterion, quoted exactly as you were given it, second is its id, and why
says what it would have to state for a test to settle it. Give a finding only
for a conflict, a gap or an untestable criterion; for anything else, answer
with the file.
```
