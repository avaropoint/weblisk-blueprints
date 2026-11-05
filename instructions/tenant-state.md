---
family: schemas/instruction@1
version: 1.0.0
in: [plan, generate]
---
# What the tenant already has

How the tenant state input is read: a statement of fact about the tenant a
component is added to, and what the plan and the file do with it.

## Why

A component is almost never the first thing in a tenant
([`architecture/generation`](../architecture/generation.md#the-prompt-contract),
element 9). Without the tenant's state a generator re-declares what it could
import and names the module something the tenant is not. A name without its
signature is not enough to call: an orchestrator told only that the tenant's
passphrase package exports ReadInjected called it with one argument where it
takes two. A re-derived plan that was told nothing about the names its
component declared last time renamed them at random, and ten correct files
were rebuilt for it; a plan that was told the module's manifest existed, and
planned it anyway, renamed the module under every package in the tenant.

## Text

```text
The tenant state is a JSON object saying what the tenant already has: you are
adding one component to a tenant that is already built and running, not
creating a project. module is its module path: import the tenant's own
packages by it, and do not plan the module's manifest, which exists. packages
are the packages it provides, each with its directory, its package name, the
component that owns it, its import path, its exported names, and the
signature of each exported function and method: import them rather than
declaring again what they export, spell each name exactly as given, call each
function as its signature says, and plan no file in their directories. names
are the names this component declared in its last build: that code is what
this build replaces and may be restructured, but keep a name where the
requirement behind it has not changed. owned are files that belong to another
component, each with its owner, and a plan naming one is refused.
```
