---
family: schemas/instruction@1
version: 1.0.0
in: [generate]
---
# The file a generator writes

How the plan entry and the file set are read: the file asked for, and the
files it is not responsible for.

## Why

A file generated from a filename alone is a guess, and one that does not know
the rest of the plan absorbs another file's work
([`architecture/generation`](../architecture/generation.md#the-prompt-contract),
elements 2 and 4). The file set is every path in the plan; the files already
generated are named so the declarations given beside them can be read as
what those files hold.

## Text

```text
The plan entry is a JSON object naming the file you write: path, its
purpose, the names it must declare, the endpoints it must serve, the
platform, and root, the directory the target is generated into. The file set
is a JSON object: files are every file of this component's plan, and
generated are those already written. Write the file the plan entry names and
no other. A file you are given whole, such as a test, is its content between
a line === path === and a line === end path ===.
```
