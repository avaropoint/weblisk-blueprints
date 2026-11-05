---
family: schemas/instruction@1
version: 1.0.0
in: [plan]
---
# The requirements a plan places

How the requirements input is read: what each key holds, and what placing it
in a plan means.

## Why

The requirements are extracted from the blueprints and elevated into the plan
prompt, because a requirement left inside seventy thousand tokens of
specification is placed by luck
([`architecture/generation`](../architecture/generation.md#how-a-blueprint-is-read)).
Extracted, each needs its meaning said once. Store operations were sent and
not said to be names: the blueprint declared PutAgent, GetAgent, DeleteAgent
and ListAgents, a plan used Get, Put and List, and no file was wrong while
every file was stale. An endpoint named from its path is named differently on
every run. A plan built from a graph that carried an opt-in blueprint, and was
not told the tenant adopted it, called its drivers "not configured by this
tenant".

## Text

```text
The requirements are a JSON object, and every requirement in it must be
placed in your plan. component is the kind of component you plan, name the
instance where it has one, and platform what it is built for. consumes are the types this component's
blueprint declares it consumes, each with the blueprint it is from and the
fields it uses; one marked behaviour is behaviour to follow, not a type to
define. types are the types it consumes where no binding names them. endpoints
are what it serves, each with its method, its path and the operation its
blueprint declares: spell every symbol for an endpoint from its operation,
through the platform blueprint's mapping, and never from its path. unnamed
are endpoints whose blueprint declares no operation, and each is a gap.
operations are the store operations the component owns, named as
architecture/storage declares them, and used exactly as named. criteria are
the Verification Checklist items the implementation must satisfy, each with
the blueprint it is from. adopted are opt-in blueprints this tenant's
configuration adopts, each with the setting that adopts it: their surface is
part of this component, and is built.
```
