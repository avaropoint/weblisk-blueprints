# Global Blueprint

> The project's identity and the single source of truth for anything
> cross-cutting.

## Purpose

`global.yaml` is loaded with every generation request. It provides the
LLM with project-wide context — brand, identity, policies, and
dependencies — so that every generated file is consistent without the
developer repeating declarations per-page.

## Structure

```yaml
# blueprints/global.yaml
name: "My Product"
domain: myproduct.com
locale: en-US
locales: [en-US]              # add more for i18n

brand:
  colors:
    primary: "#1a1a2e"
    accent: "#e94560"
    surface: "#ffffff"
    text: "#1a1a1a"
    error: "#dc2626"
    success: "#16a34a"
  typography:
    heading: { family: "Inter", weight: 700 }
    body: { family: "system-ui", weight: 400 }
    mono: { family: "JetBrains Mono", weight: 400 }
  spacing: 8px                # base unit (multiples: 8, 16, 24, 32...)
  radius: 4px                 # border-radius base
  logo: assets/logo.svg
  favicon: assets/favicon.svg

identity:
  tagline: "Short value proposition"
  description: "One paragraph describing the product"
  legal_name: "Company Inc."
  contact: hello@myproduct.com
  copyright_year: 2026

social:
  twitter: "@handle"
  github: "org/repo"
  linkedin: "company/name"
  og_default_image: assets/og-default.png

policies:
  accessibility: WCAG-2.2-AA
  seo: strict
  structured_data: required
  social_meta: required
  performance:
    lcp: 2500
    cls: 0.1
    inp: 200

dependencies: []
```

## Fields

### Top-Level

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `name` | string | ✅ | Project display name |
| `domain` | string | ✅ | Primary domain (used in canonical URLs, sitemap) |
| `locale` | string | ✅ | Default locale (BCP 47) |
| `locales` | string[] | — | All supported locales |

### Brand

| Field | Type | Description |
|-------|------|-------------|
| `colors` | map | Named color tokens. Keys are semantic (primary, accent, etc.) |
| `typography` | map | Font declarations. Keys: heading, body, mono |
| `spacing` | string | Base spacing unit. All spacing derives from multiples |
| `radius` | string | Base border-radius |
| `logo` | path | Path to logo file (relative to project root) |
| `favicon` | path | Source file for favicon generation |

### Policies

Policies are references to enforcement rules. When the LLM generates
code, it must satisfy all declared policies:

| Policy | Values | Effect |
|--------|--------|--------|
| `accessibility` | `WCAG-2.2-A`, `WCAG-2.2-AA`, `WCAG-2.2-AAA` | Generated HTML meets this level |
| `seo` | `strict`, `standard`, `minimal` | Controls meta, headings, semantics |
| `structured_data` | `required`, `recommended`, `none` | JSON-LD on every page |
| `social_meta` | `required`, `recommended`, `none` | OG + Twitter cards |
| `performance` | object | LCP, CLS, INP budgets — affects lazy loading, code splitting |

### Dependencies

External libraries. These are opt-in — only loaded where referenced:

```yaml
dependencies:
  - name: chart.js
    version: "^4.4"
    cdn: https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js
    scope: islands/dashboard    # only available in this island
  - name: mapbox-gl
    version: "^3.0"
    cdn: https://api.mapbox.com/mapbox-gl-js/v3.0.0/mapbox-gl.js
    scope: islands/map
```

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `name` | string | ✅ | Package name |
| `version` | string | ✅ | Semver range |
| `cdn` | URL | — | CDN URL (added to import map if present) |
| `scope` | string | — | Limits where this dependency is available |

## Inheritance

Every other blueprint inherits from `global.yaml` implicitly:

- Pages get `brand.colors` for themed generation
- Components get `brand.typography` for consistent text
- Islands get `policies.accessibility` for ARIA compliance
- All output gets `policies.seo` for meta tag generation

Developers never need to reference `global.yaml` explicitly. It's
always in context.
