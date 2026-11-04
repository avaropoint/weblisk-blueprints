---
family: schemas/instruction@1
version: 1.0.0
in: [generate, repair]
---
# File names

How a generated or repaired file spells every name the plan and the declarations give it.

## Why

The same fault as [`plan-names`](plan-names.md), one prompt later: a file
prompt that let the model take the closest declared name settled a corpus gap
in generated code, where nobody would read it
([`architecture/generation`](../architecture/generation.md#a-name-must-come-from-the-blueprint-that-declares-it)).

## Text

```text
Spell every type, path constant, handler, request type, response type, store
operation, event topic and error code exactly as the plan and the
declarations you are given spell it. If this file needs one of these that
neither gives you and no blueprint declares, do not make one up and do not
use the closest declared name: answer with a corpus finding of kind gap
instead of the file.
```
