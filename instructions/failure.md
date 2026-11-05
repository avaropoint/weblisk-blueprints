---
family: schemas/instruction@1
version: 1.0.0
in: [repair]
---
# What failed

How the failure input is read: its kind says what failed, and each kind says
what a repair of it changes and what it leaves alone.

## Why

The repair kinds are not yet declared
([`ENGINE_PLAN.md`](../ENGINE_PLAN.md#4-what-the-model-may-and-may-not-do)),
so the kinds are told apart by the failure itself. Each kind's sentence was
learned from a repair that went wrong without it. A disagreement between an
interface in one file and its implementer in another was repaired one side
per round, and the same three errors stood on rounds 3, 4 and 5
([`architecture/generation`](../architecture/generation.md#repairing-a-disagreement-between-files)).
A wrong import is a one-token fault, and inviting a rewrite of an otherwise
correct file turns a repair into a regression. A repair undone puts back the
tree it started on, so the next round's prompt is byte for byte the one that
produced it, and a model returns the same repair until the run stops: what an
earlier attempt broke is what the next one needs to know. Seven of one
rebuild's twenty-nine unrepaired requirements were repairs right in intent
and undone every round, because each had authority over one side of the
change
([`architecture/generation`](../architecture/generation.md#a-repair-that-needs-another-file-is-completed-across-it)).

## Text

```text
The failure is a JSON object, and its kind says what failed.

build: errors are the compiler's errors naming the files you may change, and
other is build output they may have caused. Change the files so the
implementation builds.

disagreement: the compiler reports a disagreement between the files you may
change, such as an interface and its implementer, one symbol declared twice,
or two package clauses in one directory. Changing either side alone cannot
resolve it, since the other still disagrees. Decide which side is correct,
make the other match it, and answer for every file.

import: the dependency resolver rejected an import, in the output given. The
import path does not exist; the platform blueprint's Primitive Mapping table
gives the exact path for every required module. Correct the imports, and
change nothing else: every declaration, signature and line of logic stays as
it is.

assertions: the files compile and do not satisfy the assertions given, each
quoted from its blueprint, with what was found. Change the files so every
assertion holds, and keep everything else as it is.

startup: the component compiles, was started, and failed, with the output
given. This is a logic fault, two requirements implemented in two places
without agreeing: correct whichever side is wrong.

completion: a repair of the files named in repaired, made for the requirements in
wanted, breaks the build on its own, for the reason why gives: diagnostics
are what its build reports that the build without it did not, and changed
are names it changed that other files use. Complete it: keep what it was for,
declare what it uses that does not exist yet, and bring every use of what it
changed into line. It is built and judged with your edits as one change, and
undone with them if the tree is worse. Answer only for the files you change;
you may amend the repaired files too.

tried, where given, lists repairs of these files already tried and not kept,
each with why and the errors its build reported that the current tree's does
not. Do not repeat one: make a repair that fixes the failure without what
they broke.
```
