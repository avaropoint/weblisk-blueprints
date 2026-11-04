---
family: schemas/instruction@1
version: 1.0.0
in: [repair]
---
# Repair

How a repair answers: edits to the files it is given, as they stand, and to
no other file, test or fixed name.

## Why

A build repair asked for a 2,649-line file "rewritten so the implementation
builds", showing its errors and never the file; both rounds ended with the
model unable to return the file, and nothing was tried
([`architecture/generation`](../architecture/generation.md#a-repair-is-an-edit-to-the-file-as-it-stands)).
A repair that may edit a test, or a name the plan fixes, can make a failure
disappear without fixing it.

## Text

```text
You are given a failure, the section of the blueprints that governs it, and
the current content of every file you may change. Fix the failure by editing
those files as they stand. Each edit is an exact span of the current text, in
whole lines, and what it becomes; a span must occur exactly once in its file.
You may instead answer with a whole file.

Change no file you were not given. Do not edit a test, and do not rename or
move a name the plan fixes. If the failure cannot be fixed without one of
these, answer with the edits you can make, and the failure will be reported.
```
