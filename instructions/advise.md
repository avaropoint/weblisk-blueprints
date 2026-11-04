---
family: schemas/instruction@1
version: 1.0.0
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

## Text

```text
Read the tree you are given against the criterion you are given, and say
whether it appears to meet it, quoting the lines you rely on. Your reading is
advice to a person. It does not decide whether the criterion is met; a test
or a declared check decides that. Do not say a criterion is met or unmet as a
verdict, and do not propose edits.
```
