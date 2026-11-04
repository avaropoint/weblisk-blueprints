---
family: schemas/instruction@1
version: 1.0.0
in: [generate, repair]
---
# Scope

What a generated or repaired file may contain: what its plan entry declares and serves, and nothing else.

## Why

A file prompt with the scope prohibition removed left element 7 of the
prompt contract unconveyed, and a model asked to build a component builds a
generous one: every unrequested addition is code nobody specified or reviewed
([`architecture/generation`](../architecture/generation.md#scope-discipline)).

## Text

```text
Write only what this file's plan entry declares and serves. Do not add an
endpoint, route or handler the entry does not name; configuration, a metric,
a dashboard, a health page or an admin surface no blueprint specifies; a
dependency the language blueprint does not admit; or anything else nobody
asked for, however helpful it looks. If you believe the file needs more than
its entry gives it, write the file without it.
```
