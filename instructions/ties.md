---
family: schemas/instruction@1
version: 1.1.0
in: [plan, translate, generate, repair]
---
# Ties

What a model does where two statements in the blueprints cannot both hold.

## Why

Told to say a tie *"in a comment rather than choosing"*, a model settled
corpus contradictions in generated code where nobody would read them
([`architecture/generation`](../architecture/generation.md#how-a-blueprint-is-read)).
Two statements that cannot both hold are a corpus fault, and a person settles
it by changing the corpus.

## Text

```text
Where two statements in the blueprints cannot both hold, follow the more
specific: a component's own blueprint over a pattern it adopts, a pattern
over a schema's example. If neither is more specific, do not choose between
them, and do not write a comment about it: answer with a corpus finding of
kind conflict instead of the file, or, in a plan, instead of the plan.
```
