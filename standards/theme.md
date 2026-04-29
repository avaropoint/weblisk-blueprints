# Theme Blueprint

> Design tokens that derive from brand declarations in `global.yaml` and
> expand into a full design system.

## Purpose

`theme.yaml` bridges brand identity and implementation. It takes the
high-level brand colors and typography from `global.yaml` and produces a
complete token system — scales, breakpoints, component-level variables.

## Structure

```yaml
# blueprints/theme.yaml
extends: global.brand

scales:
  spacing: [0, 4, 8, 12, 16, 24, 32, 48, 64, 96, 128]
  font_size: [12, 14, 16, 18, 20, 24, 30, 36, 48, 60]
  line_height: [1, 1.25, 1.375, 1.5, 1.625, 2]
  font_weight: [400, 500, 600, 700]

breakpoints:
  sm: 640px
  md: 768px
  lg: 1024px
  xl: 1280px

layout:
  max_width: 1200px
  gutter: 16px
  columns: 12

shadows:
  sm: "0 1px 2px rgba(0,0,0,0.05)"
  md: "0 4px 6px rgba(0,0,0,0.07)"
  lg: "0 10px 15px rgba(0,0,0,0.1)"

transitions:
  fast: 150ms ease
  normal: 250ms ease
  slow: 400ms ease

dark:
  colors:
    surface: "#0f0f0f"
    text: "#e5e5e5"
    primary: "#e94560"
    accent: "#ff6b6b"
```

## Fields

### Scales

Numeric scales that the LLM uses to pick values consistently. Instead of
arbitrary pixel values, generated code uses scale indices:

```css
/* spacing scale index 4 = 16px = 1rem */
.card { padding: var(--space-4); }
```

### Breakpoints

Responsive breakpoints. The LLM generates media queries using these
values in the direction specified by `code.yaml` (`mobile-first` or
`desktop-first`).

### Dark Mode

Override tokens for dark mode. Only declare what changes — everything
else inherits from the light theme (global.brand.colors).

## Relationship to Global

```
global.yaml (brand.colors, brand.typography)
    ↓ extends
theme.yaml (scales, breakpoints, full token system)
    ↓ consumed by
Every generated CSS file
```

`global.yaml` declares the brand. `theme.yaml` operationalizes it into
a design system. If you only need basic theming, `global.yaml` alone is
sufficient — `theme.yaml` is for projects that need fine-grained control.

## Generated Output

From this blueprint, the pipeline generates:

```css
:root {
  --color-primary: #1a1a2e;
  --color-accent: #e94560;
  --color-surface: #ffffff;
  --color-text: #1a1a1a;
  --font-heading: 'Inter', sans-serif;
  --font-body: system-ui, sans-serif;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  /* ... full scale */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --transition-fast: 150ms ease;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-surface: #0f0f0f;
    --color-text: #e5e5e5;
  }
}
```

All generated components reference these variables. Changing a token in
`theme.yaml` and regenerating updates the entire site.
