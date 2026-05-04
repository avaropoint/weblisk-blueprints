# Style Blueprints

> Page-scoped style declarations that extend the base theme for
> specific routes or sections.

## Purpose

While `theme.yaml` defines the global design token system, individual
pages often need additional style rules that don't belong in the shared
theme. Style blueprints declare page-specific CSS requirements —
layout adjustments, section-specific spacing, custom component styling,
and responsive overrides — in a structured format the LLM uses to
generate scoped CSS.

## Relationship to Theme

```
global.yaml (brand.colors, brand.typography)
    ↓ extends
theme.yaml (scales, breakpoints, full token system)
    ↓ consumed by
styles/<page>.styles.yaml (page-specific additions)
    ↓ generates
css/<page>.css or scoped section within css/styles.css
```

Style blueprints MUST use tokens from `theme.yaml` where applicable.
Raw values are only permitted when no suitable token exists.

## Structure

```yaml
# blueprints/styles/home.styles.yaml
type: styles
name: home-styles
page: home
status: active
version: 1.0.0

theme: ../../.weblisk/theme.yaml

# Section-specific styles
hero:
  layout: flex-column-center
  padding: var(--space-8) var(--space-4)
  max_width: 800px
  margin: 0 auto

features_grid:
  layout: grid
  columns: 3
  gap: var(--space-6)
  responsive:
    md: { columns: 2 }
    sm: { columns: 1 }

cta_banner:
  background: var(--color-primary)
  color: var(--color-surface)
  padding: var(--space-8) var(--space-4)
  text_align: center
```

## Fields

### Top-Level

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `type` | `styles` | ✅ | Always "styles" |
| `name` | string | ✅ | Identifier for the style set |
| `page` | string | ✅ | Which page blueprint this extends |
| `theme` | path | — | Relative path to theme.yaml (for token reference) |

### Section Styles

Each top-level key (after metadata fields) corresponds to a named
section or component on the page. Keys should match section IDs from
the page blueprint.

#### Layout Properties

| Field | Values | Description |
|-------|--------|-------------|
| `layout` | `flex-row`, `flex-column`, `grid`, `flex-row-center`, `flex-column-center` | CSS layout model |
| `columns` | number | Grid column count |
| `gap` | token or value | Grid/flex gap |
| `max_width` | token or value | Maximum content width |
| `padding` | token or value | Section padding |
| `margin` | token or value | Section margin |

#### Responsive Overrides

Nest responsive adjustments under the `responsive` key using
breakpoint names from `theme.yaml`:

```yaml
section_name:
  columns: 3
  responsive:
    md: { columns: 2 }
    sm: { columns: 1, gap: var(--space-4) }
```

The LLM generates media queries using the direction specified in
`code.yaml` (`mobile-first` or `desktop-first`).

#### Component-Specific Styles

For styles that target a specific component within a section:

```yaml
hero_trust:
  layout: flex-row-center
  gap: 1.5rem
  wrap: true
  item:
    display: inline-flex
    align_items: center
    gap: 0.4rem
    font_size: 0.85rem
    color: var(--wl-text-muted)
```

Nested keys (like `item`) describe child elements within that section.

### Special Properties

| Field | Type | Description |
|-------|------|-------------|
| `type` (on icons) | `inline-svg`, `font-icon`, `sprite` | Icon rendering strategy |
| `accent_phrases` | number[] | Which child elements receive accent color |
| `hover_opacity` | number[] | [default, hover] opacity values |

## Dark Mode

Style blueprints do NOT duplicate dark mode overrides. Dark mode
tokens are defined in `theme.yaml` and applied automatically via
CSS custom properties. If a section needs dark-mode-specific behavior
beyond token swapping, declare it explicitly:

```yaml
hero:
  background: var(--color-surface)
  dark:
    background: var(--color-surface-elevated)
```

## Generated Output

From a style blueprint, the pipeline generates CSS that:
1. Uses custom properties from the theme
2. Scopes rules to page-specific selectors or section IDs
3. Applies responsive breakpoints in the configured direction
4. Respects `prefers-reduced-motion` for any animations
5. Integrates with the page's existing component styles

## Conventions

- Use theme tokens over raw values wherever possible
- One style blueprint per page (or per complex section)
- Name matches: `styles/<page>.styles.yaml` → corresponds to
  `pages/<page>.yaml`
- Section keys should match `id` fields from the page blueprint
- Raw pixel values are acceptable for one-off adjustments that
  don't map to the spacing scale
