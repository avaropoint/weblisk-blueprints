# Asset Blueprints

> Static files, generated media, and references.

## Purpose

Assets are the physical media of a project — images, fonts, videos,
icons. Asset blueprints declare what exists, how it's used, and what
should be generated from source files (responsive variants, favicon
sets, sprite sheets).

## Physical vs. Declared Assets

| Location | Nature | Examples |
|----------|--------|----------|
| `assets/` (root) | Physical files in the repo | logo.svg, photo.webp, fonts/ |
| `blueprints/assets/` | Declarations of how to use/generate | brand.yaml, icons.yaml |

Physical files are things the LLM can't produce — photographs, licensed
fonts, brand logos created by designers. The blueprint declares how
they're referenced, what derivatives to produce, and where they appear.

## Structure

```yaml
# blueprints/assets/brand.yaml
type: assets
name: brand

logo:
  source: assets/logo.svg
  variants:
    - name: full
      width: 200
      context: header
    - name: icon
      width: 32
      context: favicon
    - name: dark
      filter: invert
      context: dark-mode

favicon:
  source: assets/favicon.svg
  generate:
    - size: 16x16
      format: ico
    - size: 32x32
      format: png
    - size: 180x180
      format: png
      purpose: apple-touch-icon
    - size: 512x512
      format: png
      purpose: pwa-icon

og_images:
  default: assets/og-default.png
  dimensions: 1200x630
  generate_per_page: false     # or true to auto-generate per page

fonts:
  - family: Inter
    source: assets/fonts/inter-var.woff2
    weight: 100 900
    display: swap
  - family: JetBrains Mono
    source: assets/fonts/jetbrains-mono.woff2
    weight: 400 700
    display: swap
```

## Fields

### Logo

| Field | Type | Description |
|-------|------|-------------|
| `source` | path | Path to source logo file |
| `variants` | array | Different sizes/styles for different contexts |
| `variants[].context` | string | Where this variant is used |
| `variants[].width` | number | Target width in pixels |
| `variants[].filter` | string | CSS filter to apply (for dark mode variants) |

### Favicon

| Field | Type | Description |
|-------|------|-------------|
| `source` | path | Source SVG or high-res PNG |
| `generate` | array | Sizes to produce |
| `generate[].purpose` | string | `apple-touch-icon`, `pwa-icon`, etc. |

The pipeline generates all favicon variants and the corresponding
`<link>` tags in the HTML head.

### Fonts

| Field | Type | Description |
|-------|------|-------------|
| `family` | string | Font family name (matches theme declarations) |
| `source` | path | Path to font file |
| `weight` | string | Weight range (variable) or specific weight |
| `display` | `swap`, `block`, `fallback`, `optional` | font-display value |

The LLM generates the `@font-face` declarations and preload links.

## Generated Assets

Some assets CAN be generated:

```yaml
# blueprints/assets/icons.yaml
type: assets
name: icons
generate: true

icon_set:
  style: outline              # outline, solid, duo-tone
  size: 24
  stroke: 2
  icons:
    - name: menu
    - name: close
    - name: search
    - name: arrow-right
    - name: check
    - name: warning
```

The LLM generates SVG icons matching the declared style. For standard
icons, this avoids importing an entire icon library for 5 icons.

## Responsive Images

```yaml
# blueprints/assets/images.yaml
type: assets
name: responsive

rules:
  hero:
    breakpoints:
      sm: { width: 640, format: webp, quality: 80 }
      md: { width: 1024, format: webp, quality: 85 }
      lg: { width: 1920, format: webp, quality: 90 }
    fallback: jpg
    lazy: false               # hero images load eagerly

  content:
    breakpoints:
      sm: { width: 400, format: webp }
      md: { width: 800, format: webp }
    lazy: true
    placeholder: blur          # low-quality image placeholder
```

When a page blueprint references an image, the generation pipeline
applies these rules to produce the correct `<picture>` element with
srcset and sizes attributes.
