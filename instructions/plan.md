---
family: schemas/instruction@1
version: 1.0.0
in: [plan]
---
# Plan

How a plan is written: inside the packages the language's layout fixes, with
`declares` holding top-level symbols only.

## Why

A planner told only "symbols this file will define" reasonably listed struct
fields, and a verifier cannot tell a field from an omission, so a run over
correct code was refused
([`architecture/generation`](../architecture/generation.md#what-a-plan-declares)).
Left to choose packages, the same ten blueprints gave plans that put all 48
library files in one package and three types in three packages each
([`architecture/generation`](../architecture/generation.md#why-the-packages-are-fixed-and-the-files-are-not)).

## Text

```text
Answer with the plan, in the shape you are given, and nothing else. The
packages, and the package each declared name lives in, are fixed by the
package plan you are given: put every file in one of its packages and every
declared name in the package it names, and do not add a package. Decide only
how each package's work is divided into files, what each file is called, what
its purpose says, and which files must be generated before it.

In declares, list the top-level symbols the file will define: types,
functions, methods, constants and package-level variables. Never list a
struct field, a local variable, or anything nested inside another
declaration. Name a method in receiver notation, (Type).Method.
```
