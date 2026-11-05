---
family: schemas/instruction@1
version: 1.0.0
in: [repair]
---
# The files a repair may change

How the repair set input is read: which files may be changed, what each owes,
and the content each edit is made to.

## Why

A repair asked for a 2,649-line file and was shown its errors and never the
file; it could not return the file, and nothing was tried
([`architecture/generation`](../architecture/generation.md#a-repair-is-an-edit-to-the-file-as-it-stands)).
Content is given between lines that name it, not inside a quoted string,
because an edit's span is copied from it exactly and an escaped copy is not
the file. A file of a package other components import may only be added to,
because the component's build does not compile those components
([`architecture/generation`](../architecture/generation.md#a-repair-that-needs-another-file-is-completed-across-it)).

## Text

```text
The repair set is every file you may change. It begins with a JSON array
giving each file's path, its purpose, the names it must still declare, the
endpoints it must still serve, why it is in the set, and whether it is
shared. Then each file's current content follows, between a line === path ===
and a line === end path ===. A shared file is in a package other components
import, and this build does not compile them: you may add declarations to it,
and must not remove or change anything it already has. A file whose content
is empty has none yet: answer for it with the whole file.
```
