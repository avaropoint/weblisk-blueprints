---
name: tenants
description: Create and operate a Weblisk tenant with the CLI, and grow it past its first component. Use when standing up an organisation's hub, when asked to create, start or connect a tenant, or when asked what a tenant consists of.
---

# Tenants

A tenant is one organisation's deployment: **a set of components in one
module**, each registering with the one orchestrator it runs. The orchestrator
is its first component and its trust anchor — `architecture/orchestrator.md`,
whose "What a tenant consists of" section says why it is not the tenant, and
where the component set is actually declared.

This skill is the command that creates one.

## Default

```
weblisk tenant create "Acme Corp"
```

No `--provider`, no `--platform`, no prompt file. The CLI takes the
highest-weighted model on this machine, platform `go`, and generates the
orchestrator from its blueprints.

The passphrase is read from stdin, never from argv.

## Override

```
weblisk tenant create "Acme Corp" --provider grok --platform go --dir ./acme --port 9860
```

`--provider` pins a backend (`weblisk providers` lists what this machine
has). `--platform` is `go|cloudflare|node|rust` and chooses which platform
blueprint and skills the tenant is built from — each specifies its own
layout, build and run commands, and only the chosen one is built. `go` is
the fallback when none is given. `--dir` and `--port` place it. `--resume`
continues a partial generation.

## Then

```
weblisk server status
weblisk operator connect --orch http://localhost:9800
```

Do not generate the orchestrator by writing files. `weblisk tenant create`
is the operation; `weblisk server init` is the same generation without
start-and-claim.

## A created tenant is not a finished tenant

`tenant create` generates **one** component. Everything else a tenant needs —
the content service that lets it hold authored text, a gateway, agents, domain
controllers — is added afterwards, one at a time, into the same module.

```
weblisk component help                 # what this installation can add
weblisk component content init         # the content service
```

That is the `changes` skill's subject, and it is installed beside this one for
exactly that reason. Do not report a tenant as complete because `tenant create`
finished: ask `GET /v1/services` what is actually registered, and name what is
missing rather than answering as though nothing is.
