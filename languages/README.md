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

`platforms/node.md` is therefore still misfiled in a different way: most of its
894 lines are JavaScript conventions, and `platforms/cloudflare.md` restates
twelve of the same sections because there is nowhere shared to put them. The
language content becomes `languages/typescript.md`; what stays is what is true of
the runtime. See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md).
