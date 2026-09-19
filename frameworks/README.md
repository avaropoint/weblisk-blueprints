# Frameworks

One blueprint per framework: **what building *with* it requires.**

A framework constrains a language, and often a platform, without being either.
Astro implies JavaScript or TypeScript and can target several runtimes; the
Weblisk client framework has its own components, islands, pages and theme model.
Neither says what you are building.

## Not a language, and not a platform

| | Answers | Lives in |
|---|---|---|
| **language** | what is this written in, and in what style? | [`languages/`](../languages/README.md) |
| **platform** | what does it run on, and what does that offer? | [`platforms/`](../platforms/README.md) |
| **framework** | what is it built *with*? | here |

## What is here

| | |
|---|---|
| [weblisk](weblisk/README.md) | the Weblisk client framework — pages, components, islands, theme |

A third-party framework — Astro, Next — would sit beside it as a peer, declaring
the same kinds of thing for its own model.

`frameworks/weblisk` was previously `standards/`: its files are one framework's
own concepts rather than general project standards, and the word `standards` is
needed for what it means to the people this framework serves — ISO 27001, SOC 2,
NIST. See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md).
