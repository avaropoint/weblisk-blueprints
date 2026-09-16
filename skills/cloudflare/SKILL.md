---
name: cloudflare
description: Cloudflare-Workers-only facts for a tenant generated with --platform cloudflare — per-Worker layout, the zero-runtime-dependency rule, which storage binding holds what, and where secrets go. Use before editing routing, storage, or wrangler.toml in a Cloudflare tenant.
---

# Cloudflare Workers

`platforms/cloudflare.md` is the specification. This skill is the facts
that fail a deploy or lose data, plus the layout the generator already
followed.

## Layout

**Each component is its own Worker.** `server/` holds the orchestrator
with its own `wrangler.toml`, `package.json` and `src/`; each
`agents/<name>/` and `domains/<name>/` is a Worker beside it with the
same shape. There is no shared module graph across Workers — each
carries its own copy of `protocol.js` and `identity.js`.

`src/index.js` is the entry point. It routes by pathname and delegates;
`fetch` does not decide anything itself.

## Rules that bite

**1. Zero runtime dependencies.** `package.json` has `devDependencies`
only — wrangler. A runtime dependency does not survive the Workers
sandbox.

**2. Secrets go through `wrangler secret put`.** Never in
`wrangler.toml`, never in source. `wrangler.toml` is committed; a private
key in it is published.

**3. Storage is chosen per question, and getting it wrong loses data:**

| What | Where | Why |
|---|---|---|
| Agent registry | Durable Object | strong consistency |
| Service directory cache | KV | eventually consistent, fast at the edge |
| Observations, audit, workflow runs | D1 | queryable |
| Entity context | KV | fast edge reads |

Every binding a component uses must be declared in its `wrangler.toml`.

**4. Channel TTL cleanup is a Durable Object alarm.** There is no
background timer in a Worker.

**5. No path literals reach routing.** Paths are exported
`PATH_<OPERATION>` constants in one module, dispatched from one
`{ method, path, handler }` table.

**6. Concurrency is coordinated in the Durable Object.** The
`acquireSlot`/`releaseSlot` pair respects an agent's `max_concurrent` —
a per-isolate counter counts nothing, because isolates are not shared.

## Before you say it works

```
npx wrangler deploy --dry-run
weblisk server verify
```
