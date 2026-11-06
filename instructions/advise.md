---
family: schemas/instruction@1
version: 1.1.0
in: [accept]
---
# Advise

What a model's reading of a tree is for: advice a person reads, which never
moves a verdict.

## Why

A model's reading was the verdict: every checklist item was read as
satisfied, unmet or unverifiable by a model, and on the last orchestrator
build 41% of assertions were "unverifiable"
([`ENGINE_PLAN.md`](../ENGINE_PLAN.md#the-problem-measured)). Model readings
are removed from every verdict (ACCEPTANCE_PLAN decision 7); what is left of
them is advice, and the model is told so.

The advice still has a form, because the record keeps it beside the verdict: a
reading's first word is its `says` (`met`, `unmet` or `unsure`) and its reasons
are its `reason` ([`schemas/run-statement`](../schemas/run-statement.md#criteria)),
so a shadow run can set what the model said against what the suite found, a
reading that says `met` included. The word is the model's reading, never a
verdict: nothing that decides acceptance reads it.

## Text

```text
Read the tree you are given against the criterion you are given. Begin your
answer with one line that is one word, met, unmet or unsure, saying how the
tree appears to you against it; then give your reasons, quoting the lines you
rely on. That word is your reading and nothing more: advice to a person, kept
beside the verdict. It does not decide whether the criterion is met; a test
or a declared check decides that, and your reading never moves it. Do not
propose edits.
```
