# Languages

One blueprint per programming language: **what is essential if you build in it.**

A language blueprint says how this framework's requirements become concrete in
one language — dependency policy, project layout, error handling, concurrency,
and the primitives the standard library does and does not supply. It says nothing
about *what* is being built, and nothing about where it runs.

## Not a platform, and not a framework

| | Answers | Lives in |
|---|---|---|
| **language** | what is this written in, and in what style? | here |
| **platform** | what does it run on, and what does that offer? | [`platforms/`](../platforms/README.md) |
| **framework** | what is it built *with*? | [`frameworks/`](../frameworks/README.md) |

These are independent. TypeScript is a language whether it runs on Node or on
Cloudflare Workers; Cloudflare is a platform whatever you write for it; Astro is
a framework that constrains the first two without being either.

**A platform needs a language too.** Driving Microsoft 365 means writing a client
— in some language, against that platform's surface — so the axes hold for
governing a service exactly as they do for generating a tenant.

## Programming languages, not spoken ones

`language` here always means a programming language. Locale and spoken-language
constructs are [`intl/`](../intl/README.md), reserved for that purpose so this
word never has to be qualified.

## Why Go and Rust moved, and Node did not

`platforms/` held two programming languages, a runtime and a platform. Go and
Rust are languages whose runtime is a binary — there is no separate platform to
name. **Node is a runtime**, and Cloudflare Workers is another, both executing
the same language.

`platforms/node.md` stays where it is. An earlier version of this page said it was
misfiled too — mostly JavaScript conventions, with `platforms/cloudflare.md`
restating twelve of the same sections — and that the language content should become
`languages/typescript.md`. **Measured, that was wrong:** 31 identical substantial
lines out of 731, about four percent, and those are the schema's own explanation of
what a Primitive Mapping is rather than language conventions at all.

The twelve shared *headings* are shared because `schemas/platform.md` requires them.
Every platform blueprint answers the same questions; that is the schema working. The
content under them differs and should — `node:crypto` against Web Crypto, flat-file
JSONL against Durable Objects, a single-threaded event loop against V8 isolates.

A `languages/typescript.md` remains possible — conventions true of TypeScript wherever
it runs — but it would be **written rather than extracted**, and nothing needs it yet.
A blueprint written to justify a directory is worse than a directory with two files in
it.

One thing would have to change first, if it is ever written: a platform blueprint
cannot pull in a language blueprint by declaring it. A binding's `requires` are skipped
deliberately, because a binding's requirements describe every component type rather than
the one being built. Both bindings would have to reach generation, and the platform would
have to declare which language it runs.

See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md).
