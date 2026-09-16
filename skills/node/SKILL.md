---
name: node
description: Node-only facts for a tenant generated with --platform node — project layout, the module and routing rules that fail at startup, and how the process must shut down. Use before editing routing, handlers, or anything under src/protocol in a Node tenant.
---

# Node

`platforms/node.md` is the specification. This skill is the facts that
break at process start or in production, plus the layout the generator
already followed.

## Layout

**One project, one `src/`.** Shared code lives once under `src/protocol`
and is imported — it is never copied into a component. The entry point is
`src/server.ts`, which sits outside `src/orchestrator/`.

Components own their own subtree: `src/agents/<name>/`,
`src/domains/<name>/`. Nothing registers itself from inside another
component's directory.

## Rules that bite

**1. ES modules, not CommonJS.** `package.json` carries
`"type": "module"`. A `require()` in a file the generator wrote is a file
that will not load.

**2. No path literals reach routing.** Paths come from exported
`PATH_<OPERATION>` constants in one module — never a `"/v1/..."` string at
a registration site, in a client, or in a test.

**3. One `registerRoutes(app)`.** Every route is declared there. A module
that registers its own routes beside its handlers is the arrangement the
blueprint exists to prevent, because it makes the HTTP surface
unreadable without executing it.

**4. The router matches the method, not the handler.** Use Fastify's
method-specific helpers and read parameters from `request.params`. A
handler branching on `request.method` is two handlers sharing a name.

**5. SIGTERM must shut down in order.** Fastify closes, storage closes,
then the process exits. The CLI sends SIGTERM and waits — a process that
ignores it is killed, and whatever it was holding is lost.

**6. Never trust `request.body`.** Every payload is validated with a zod
schema.

## Before you say it works

```
npm run build && npm test
weblisk server verify
```
