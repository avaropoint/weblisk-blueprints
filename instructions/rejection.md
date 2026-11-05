---
family: schemas/instruction@1
version: 1.0.0
in: [plan, generate, repair]
---
# A refused answer

What a rejection given beside a request means: the previous answer to the
same request was refused, and why.

## Why

A refused answer is asked again with its reason
([`architecture/engine`](../architecture/engine.md#what-the-model-may-not-do)).
The reason is an input; what the model is to do with it is an instruction,
and a tool that wrote "your previous response was rejected" into its own
prompt was giving the model a sentence of its own, in three places, worded
three ways.

## Text

```text
When you are given a rejection, your previous answer to this same request was
refused, for the reasons it gives. Answer again, as these instructions say,
so that none of those reasons holds.
```
