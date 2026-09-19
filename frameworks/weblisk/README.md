# The Weblisk client framework

What building *with* Weblisk requires: its component model, its routing, its
theming, and the conventions its generated client output follows.

| | |
|---|---|
| [pages](pages.md) | routes, layouts, sections, SEO, structured data |
| [components](components.md) | reusable UI elements — props, slots, variants, accessibility |
| [islands](islands.md) | interactive regions — agent binding, real-time, auth, state |
| [theme](theme.md) | design tokens, derived from brand declarations in `global.yaml` |
| [global](global.md) | project-wide declarations |
| [assets](assets.md) | images, fonts and what happens to them |
| [connections](connections.md) | how a project communicates with external services |
| [code](code.md) | how generated CLIENT code is written — the HTML, CSS and JavaScript a browser receives |
| [project-structure](project-structure.md) | how to organise a blueprint-driven project |

Governed by [`schemas/framework.md`](../../schemas/framework.md).

## Why these were called standards

They lived in `standards/`, described as *"best practice guidance for developer
projects"*. But pages, components, islands and theme are not general project
standards — they are **one framework's own concepts**, the kind Astro and Next
each define differently. The framework axis existed in this corpus without being
called one.

And `standards` means something specific to the people this framework serves: ISO
27001, SOC 2, NIST, CSA. Spending the word on a component model left the
industry-standard sense homeless.

Moving them makes the axis honestly named and a third-party framework an obvious
peer rather than a special case. See [`../../CORPUS_SHAPE.md`](../../CORPUS_SHAPE.md).

## Still guidance, not enforcement

Unchanged by the move: these are recommendations. A project that structures
itself differently is unconventional, not non-conforming. What IS enforced lives
in `schemas/`, and the distinction is the one `standards/README.md` drew and this
inherits.
