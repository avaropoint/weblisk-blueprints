---
family: schemas/instruction@1
version: 1.0.0
in: [plan, generate, repair]
---
# Corpus finding

The one form in which a model reports a fault in the corpus in place of its answer.

## Why

A finding is only useful if it can be told apart from a file and checked
against what the model was given. One line in one form lets a generator accept
it only where each quoted passage appears in the blueprints the prompt carried
([`architecture/generation`](../architecture/generation.md#instructions-given-as-written)).

## Text

```text
A corpus finding is your whole answer, on one line: WL-CORPUS-FINDING
followed by a space and a JSON object with the keys kind, first, second and
why. kind is conflict or gap. For a conflict, first and second are the two
statements, each quoted exactly from the blueprints you were given. For a
gap, first is the sentence of the requirement that needs the name, quoted
exactly, second is the kind of name, and why says what the name is for. Give
a finding only for a conflict or a gap; for anything else, answer with the
file.
```
