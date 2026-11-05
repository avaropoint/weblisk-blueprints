---
family: schemas/instruction@1
version: 1.0.0
in: [plan]
---
# Where a component's files go

How the package plan input is read: which directories are the component's,
which are another's, and where shared code lives.

## Why

Where a component goes was first stated only inside the tenant's state, so a
component generated into an empty directory, where there is no state, was told
nothing about where its files belonged. A guard that refuses a plan naming
another component's directory, when the prompt never named that directory,
costs a planning round to teach what one sentence teaches here; replacing a
directory under a component family replaces a running component.

## Text

```text
The package plan is a JSON object saying where this component's files go.
Every path in a plan is relative to the tenant root. directories are this
component's own directories. entry is its entry point, which the build
command must build. families are the directories other components live under,
beside this one: no directory under them that is not one of this component's
is yours to write, since replacing one replaces a running component. others
are paths that belong to a specific other component and are never yours.
When contained is true, the platform gives each component its own build
manifest, and you plan this component's inside its first directory, not at
the tenant root. When it is false, the code every component shares lives
outside these directories, in the packages the layout names.
```
