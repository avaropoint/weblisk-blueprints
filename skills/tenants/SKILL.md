---
name: tenants
description: Create and operate a Weblisk tenant with the CLI. Use when standing up an organisation's hub, or when asked to create, start, or connect a tenant.
---

# Tenants

A tenant is one organisation's deployment. What it must be is
`architecture/orchestrator.md`. This skill is the command.

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
has). `--platform` is `go` — this command builds, starts and probes what it
generates, and Go is the only platform it can start, so it refuses the
others up front rather than after a generation that runs for over an hour.
To generate for another platform, use `weblisk server init --platform <p>`.
`--dir` and `--port` place it. `--resume` continues a partial generation.

## Then

```
weblisk server status
weblisk operator connect --orch http://localhost:9800
```

Do not generate the orchestrator by writing files. `weblisk tenant create`
is the operation; `weblisk server init` is the same generation without
start-and-claim.
