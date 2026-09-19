# Client Code Conventions

> Declares how generated CLIENT code should be written — the HTML, CSS and
> JavaScript a browser receives. Makes generation repeatable: same blueprints,
> same output.

**Scope.** Every convention here is about client output. Server-side components —
an orchestrator, an agent, a domain controller — take their conventions from
[`platforms/<language>`](../platforms/) instead, because naming, file size,
imports and structure are properties of the language.

`file_naming: kebab-case` below is the clearest illustration: correct for a
stylesheet, wrong for Go, where files are lowercase and a hyphen is not valid in
an identifier. A server generator that read this document as its convention would
produce non-idiomatic code from a specification that was never describing it.

## Purpose

`code.yaml` eliminates the "LLM generates different code every time"
problem. It is sent with every CLIENT generation request and constrains the
style, patterns and conventions of that output.

## Structure

```yaml
# blueprints/code.yaml
framework: weblisk
version: "1.0"

html:
  doctype: html5
  charset: utf-8
  viewport: "width=device-width, initial-scale=1"
  indent: 2
  semantic: strict
  attributes_order: [id, class, data-*, aria-*, role]

css:
  methodology: utility-first
  custom_properties: true
  nesting: native
  media_queries: mobile-first
  units: { spacing: rem, font: rem, layout: fr }
  dark_mode: prefers-color-scheme
  animations: reduced-motion-safe

javascript:
  target: es2022
  modules: esm
  style: functional
  naming: camelCase
  async: async-await
  error_handling: boundary
  state: signals
  no_globals: true

islands:
  hydration: lazy
  loading: intersection
  fallback: skeleton
  error: graceful
  communication: events

generation:
  deterministic: true
  comments: minimal
  file_naming: kebab-case
  component_naming: PascalCase
  max_file_lines: 300
  imports: explicit
```

## Fields

### HTML

| Field | Values | Effect |
|-------|--------|--------|
| `semantic` | `strict`, `standard` | `strict` = no generic divs where semantic elements apply |
| `indent` | number | Spaces per indent level |
| `attributes_order` | string[] | Consistent attribute ordering in generated HTML |

### CSS

| Field | Values | Effect |
|-------|--------|--------|
| `methodology` | `utility-first`, `BEM`, `component-scoped` | How classes are named/organized |
| `custom_properties` | boolean | Use CSS variables from theme tokens |
| `nesting` | `native`, `flat` | Whether to use CSS nesting |
| `media_queries` | `mobile-first`, `desktop-first` | Breakpoint direction |
| `dark_mode` | `prefers-color-scheme`, `class-toggle`, `none` | Dark mode strategy |
| `animations` | `reduced-motion-safe`, `always`, `none` | Respects `prefers-reduced-motion` |

### JavaScript

| Field | Values | Effect |
|-------|--------|--------|
| `target` | `es2022`, `es2020`, etc. | Which JS features are available |
| `modules` | `esm` | Always ES modules (import/export) |
| `style` | `functional`, `class-based` | Prefer pure functions or classes |
| `async` | `async-await`, `promises` | Async pattern |
| `error_handling` | `boundary` | Errors caught at island/component boundaries |
| `state` | `signals`, `store`, `minimal` | Reactivity model |
| `no_globals` | boolean | No window.* pollution |

### Islands

| Field | Values | Effect |
|-------|--------|--------|
| `hydration` | `lazy`, `eager`, `idle` | When island JS loads |
| `loading` | `intersection`, `immediate`, `idle` | What triggers hydration |
| `fallback` | `skeleton`, `spinner`, `none` | What shows before hydration |
| `error` | `graceful`, `retry`, `hide` | What happens when an island fails |
| `communication` | `events`, `signals`, `none` | How islands talk to each other |

### Generation

| Field | Values | Effect |
|-------|--------|--------|
| `deterministic` | boolean | Same input → same output (no random IDs, timestamps) |
| `comments` | `minimal`, `verbose`, `none` | Code comment density |
| `file_naming` | `kebab-case`, `camelCase`, `snake_case` | Generated file names |
| `component_naming` | `PascalCase`, `camelCase` | Component identifiers |
| `max_file_lines` | number | Split files exceeding this threshold |
| `imports` | `explicit`, `wildcard` | Import style |

## Why This Matters

Without `code.yaml`, two generations of the same page might produce:
- Different variable names
- Different indentation
- Classes vs. functions
- Inconsistent CSS approaches

With `code.yaml`, the LLM has a fixed contract. The generated code is
predictable, reviewable, and diffable between regenerations.

## Extending

For project-specific conventions not covered above, add a `custom` block:

```yaml
custom:
  naming:
    pages: "page-{slug}"
    islands: "island-{name}"
  patterns:
    forms: validate-on-blur
    tables: virtualize-above-100
    images: lazy-load-below-fold
```

Custom fields are passed to the LLM as additional constraints. They're
project-specific and not standardized.
