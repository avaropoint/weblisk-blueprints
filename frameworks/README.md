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

## Status

**In progress.** `frameworks/weblisk` — the Weblisk client framework — is
currently described by [`standards/`](../standards/README.md), whose files
(`islands`, `components`, `pages`, `theme`) are that framework's own concepts
rather than general project standards. Moving them here makes the axis honestly
named and makes a third-party framework such as Astro an obvious peer rather
than a special case.

See [`../CORPUS_SHAPE.md`](../CORPUS_SHAPE.md) for the sequence and what it
touches.
