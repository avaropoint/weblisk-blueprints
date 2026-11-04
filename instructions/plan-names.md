---
family: schemas/instruction@1
version: 1.0.0
in: [plan]
---
# Plan names

How a plan spells every name a blueprint declares, and what it does with a name no blueprint declares.

## Why

Told to *"name them from the nearest declared vocabulary"*, a planner
filled in names the corpus did not declare, and the build then carried a name
nobody specified into every file that used it
([`architecture/generation`](../architecture/generation.md#a-name-must-come-from-the-blueprint-that-declares-it)).
A missing name is a fault in the blueprints, reported as a gap, never filled
in.

## Text

```text
Spell every type, path constant, handler, request type, response type, store
operation, event topic and error code exactly as the blueprint that declares
it spells it, through the language's mapping. If the plan needs one of these
that no blueprint declares, do not make one up and do not use the closest
declared name: leave it out of every file and list it under gaps, with its
kind and the sentence of the requirement that needs it, quoted exactly.
Anything else you declare, such as an unexported helper, a receiver or a
local constant, you name yourself.
```
