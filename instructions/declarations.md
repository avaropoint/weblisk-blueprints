---
family: schemas/instruction@1
version: 1.0.0
in: [generate, repair]
---
# Declarations that already exist

How the declarations input is read: the module path, what other files declare,
and what other files use, each a fact the file must agree with.

## Why

Naming which files exist tells a model nothing about what is in them: 36 of
the first real run's 73 errors were symbols declared twice or called and never
written
([`architecture/generation`](../architecture/generation.md#the-prompt-contract),
element 3). With one package there were no import paths; with several, the
module path is a fact every file needs, and in one run go.mod said "module
weblisk" while all fifty-two other files imported "weblisk-server/internal/…",
consistent with each other and wrong. A repair of one file fixed its own two
errors and dropped two helpers four other files called, and six errors became
eleven. A round of fourteen repairs, each shown only its own source, removed a
field and re-signed a helper that other files used.

## Text

```text
The declarations are a JSON object of facts about the code. module is the
module path: every import of the project's own packages begins with it, and
the module's manifest declares exactly it. existing lists, by file, the
top-level symbols other files already declare, with their signatures: do not
declare them again, and call them exactly as listed. package lists, by file,
the symbols other files in this file's package will declare: do not declare
them, and use them without an import. consumes lists the types this
component's blueprint declares it consumes, each with the blueprint it is
from and the fields it uses: implement each with those fields, and follow one
marked behaviour rather than defining it. current lists what each file you
may change declares now, which other files call: keep every one unless the
failure says to remove it. used lists, by file and name, the lines of other
files that use a name that file declares: do not remove the name or change
its signature unless a requirement cannot be met without it, and where one
cannot, make the change, which is built with those uses and completed across
them as one repair. If a file needs a helper that none of these provides and
its plan entry does not name, declare it in that file, unexported and
specific to it, so a file written at the same time cannot choose the same
name.
```
