---
name: hubs
description: How to generate, run, and verify a Weblisk hub (the orchestrator a tenant runs). Use when creating a server, starting or stopping it, checking health, or claiming a hub works.
---

# Hubs

A **tenant** is one organisation's deployment. The **orchestrator** it runs is
the hub's trust anchor. The **hub** in the federation sense is specified by
`architecture/hub.md` and is not a synonym for the orchestrator.

What the orchestrator must do is `architecture/orchestrator.md` and
`protocol/spec.md`. This skill is the CLI verb.

## Generate

```
weblisk server init --platform go
weblisk tenant create "Acme Corp"    # generate, start, claim — one command
```

Do not write an orchestrator by hand. The command reads the blueprints and
assembles the prompt.

## Run

```
weblisk server start --detach
weblisk server status
weblisk server logs --follow
weblisk server stop
```

`--detach` records where it bound. A binary started by hand has no run
record, so `status`, `logs` and `stop` all report "not started" while it
serves.

`server start` starts what `.weblisk/config.yaml` declares — the orchestrator
alone when there is no file — and `server stop` stops everything it recorded.
One component at a time is `weblisk component <name> start|stop|status|logs`.
A start that exits non-zero has said which declared component is not running;
read that line rather than retrying.

## Verify

```
weblisk server verify --url http://localhost:9800
```

`GET /v1/health` is the only unauthenticated route. Everything else needs a
token. The full endpoint list and the conformance levels live in the
blueprints above — do not copy them here.

`GET /v1/admin/overview` reports `chain_checked` and `chain_valid` separately.
A chain that has not been checked is not a chain that passed.

When something is unavailable the hub names **why**. Keep that sentence.
