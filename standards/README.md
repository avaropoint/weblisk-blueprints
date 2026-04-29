# Weblisk Project Standards

> **These are best practices, not hard requirements.** Standards guide
> developers toward proven structures for blueprint-driven projects.
> They are recommendations — not enforced by the framework.

## What Are Standards?

Standards document how to structure a Weblisk project so that:

1. **Blueprints are the source of truth** — Every aspect of the site is
   declared in YAML. The generated output is a build artifact.
2. **Generation is repeatable** — Same blueprints produce the same code.
   Conventions are declared, not assumed.
3. **Complexity is managed** — Real-time behavior, computed logic,
   protocols, and integrations all have declarative patterns.
4. **The DX is simple** — Implement what you need. Nothing more.

## Standards vs. Schemas

| | Schemas (`schemas/`) | Standards (`standards/`) |
|---|---|---|
| **Nature** | Enforced specification | Best practice guidance |
| **Scope** | Framework internals | Developer projects |
| **Validation** | Machine-checked | Developer judgment |
| **Target** | Blueprint authors (framework) | Project authors (users) |

Schemas govern how the framework itself is built. Standards guide how
developers build *with* the framework.

## How Blueprint-Driven Development Works

```
Developer writes YAML → LLM generates code → Output serves directly
         ↑                                            |
         └────── Change blueprint, regenerate ────────┘
```

There is no traditional build step. The LLM is the compiler. YAML is the
source code. HTML, CSS, and JS are the compiled output.

### The Generation Pipeline

1. **global.yaml** — Project identity, brand, policies (loaded first, always)
2. **code.yaml** — Code conventions (loaded second, constrains all output)
3. **theme.yaml** — Design tokens derived from global brand
4. **Individual blueprints** — Pages, components, islands, etc.

The LLM receives: `global + code + theme + target blueprint + patterns`
and produces: files that conform to all constraints simultaneously.

### Three Project Modes

| Mode | What You Describe | What You Get |
|------|-------------------|--------------|
| **Client-only** | global + code + pages | Static HTML/CSS/JS, CDN import map |
| **Client + Islands** | Above + islands | Static site + interactive regions bound to agents |
| **Full stack** | Above + domains + agents | Complete hub with client and server |

A developer picks their complexity. A portfolio is 3 blueprints. A SaaS
app is 30. The structure scales because each blueprint is self-contained.

## Standards Index

| Standard | Covers |
|----------|--------|
| [project-structure.md](project-structure.md) | How to organize a blueprint-driven project |
| [global.md](global.md) | Project identity, brand, policies, dependencies |
| [code.md](code.md) | Code generation conventions and repeatability |
| [theme.md](theme.md) | Design tokens, typography, spacing, breakpoints |
| [pages.md](pages.md) | Describing routes, layouts, sections, SEO, structured data |
| [components.md](components.md) | Reusable UI: props, slots, variants, accessibility |
| [islands.md](islands.md) | Interactive regions: agent binding, real-time, auth |
| [assets.md](assets.md) | Static files, generated media, references |
| [connections.md](connections.md) | External integrations, protocols, data sources |

## Guiding Principles

1. **Describe intent, not implementation.** YAML says what you want. The
   LLM decides how to build it. Patterns constrain the how.

2. **Everything inherits from global.** Brand colors, a11y level, SEO
   policy — declared once, applied everywhere.

3. **Escape hatches exist.** If something can't be declared, write code
   directly and mark it `managed: false` so generation skips it.

4. **Zero ambiguity is the goal.** A new developer should read
   `blueprints/` and understand the entire project without looking at
   generated code.

5. **Composability over complexity.** Many small blueprints > one giant
   blueprint. Each file has a single concern.
