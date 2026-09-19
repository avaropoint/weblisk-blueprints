# Page Blueprints

> Describing routes, layouts, sections, SEO, and structured data.

## Purpose

Each page blueprint declares a single route. It describes what the page
contains, how it's structured, and what metadata accompanies it. The LLM
generates the complete HTML file from this declaration.

## Structure

```yaml
# blueprints/pages/home.yaml
type: page
route: /
title: "Home"
layout: hero-split

sections:
  - type: hero
    heading: "Build faster with Weblisk"
    subheading: "Blueprint-driven development for the AI era"
    cta:
      text: "Get Started"
      href: /docs
    background: assets/hero.webp

  - type: features
    heading: "Why Weblisk"
    source: content/features.yaml
    columns: 3
    icon_style: outline

  - type: testimonials
    source: content/testimonials.yaml
    layout: carousel
    auto_advance: 5000

  - type: cta-banner
    heading: "Ready to build?"
    cta:
      text: "Start Free"
      href: /signup

seo:
  title: "Weblisk — Blueprint-Driven Development"
  description: "Build web applications by describing what you want."
  canonical: https://weblisk.dev

structured_data:
  type: SoftwareApplication
  name: Weblisk
  category: DeveloperApplication
  offers:
    type: Offer
    price: "0"
    priceCurrency: USD

social:
  og_image: assets/og-home.png
  twitter_card: summary_large_image
```

## Fields

### Top-Level

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `type` | `page` | ✅ | Always "page" |
| `route` | string | ✅ | URL path (e.g., `/`, `/about`, `/blog/:slug`) |
| `title` | string | ✅ | Page title (used in nav, breadcrumbs) |
| `layout` | string | — | Layout variant: `default`, `hero-split`, `sidebar`, `full-width` |

### Sections

Sections are ordered blocks that compose the page. Each has a `type`
that maps to a generation pattern:

| Section Type | Generates |
|-------------|-----------|
| `hero` | Full-width hero with heading, CTA, optional background |
| `features` | Grid of feature cards (icon + title + description) |
| `testimonials` | Quote blocks with attribution |
| `cta-banner` | Call-to-action strip |
| `content` | Prose content from markdown or content blueprint |
| `grid` | Generic grid of items |
| `island` | Embeds an island blueprint (interactive region) |
| `custom` | References a component blueprint |

Sections can reference external content via `source`:

```yaml
- type: features
  source: content/features.yaml    # loads structured content
```

### SEO

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | `<title>` and `og:title` (overrides page title) |
| `description` | string | Meta description and `og:description` |
| `canonical` | URL | Canonical URL |
| `noindex` | boolean | Exclude from search engines |
| `priority` | number | Sitemap priority (0.0–1.0) |

### Structured Data (JSON-LD)

Declare using schema.org vocabulary. The LLM generates the `<script
type="application/ld+json">` block:

```yaml
structured_data:
  type: Article
  headline: "How Blueprints Replace Code"
  author:
    type: Person
    name: "Jane Developer"
  datePublished: 2026-04-01
```

If `global.yaml` has `policies.structured_data: required`, every page
MUST include this field.

### Social Meta

| Field | Type | Description |
|-------|------|-------------|
| `og_image` | path | Open Graph image |
| `twitter_card` | `summary`, `summary_large_image` | Twitter card type |
| `og_type` | string | OG type (default: `website`) |

## Dynamic Routes

For pages generated from data (blog posts, product pages):

```yaml
# blueprints/pages/blog-post.yaml
type: page
route: /blog/:slug
title: "{post.title}"
source: content/posts
layout: article

sections:
  - type: article-header
    title: "{post.title}"
    date: "{post.date}"
    author: "{post.author}"
  - type: content
    body: "{post.body}"
  - type: related
    source: content/posts
    filter: "category == post.category"
    limit: 3
```

The `{post.*}` syntax references fields from the content source. The
pipeline generates one HTML file per entry in `content/posts`.

## Embedding Islands

To add interactivity to a page section:

```yaml
sections:
  - type: island
    blueprint: islands/contact-form
    position: after-features
```

This inserts the contact-form island into the page. The island's own
blueprint defines its behavior, agent binding, and UI.

## Styles

Page blueprints can declare styles inline. These are scoped to the page
and describe layout, spacing, and any section-specific visual treatment
that goes beyond the global theme tokens.

Styles live with the thing they describe — not in separate files.
This keeps change management simple: when a section changes, its
style declaration is in the same blueprint.

### Section-Level Styles

Each section can include a `styles:` key:

```yaml
sections:
  - id: hero
    type: hero
    heading: "Welcome"
    styles:
      padding: var(--space-8) var(--space-4)
      max_width: 800px
      text_align: center

  - id: features
    type: features
    columns: 3
    styles:
      gap: var(--space-6)
      responsive:
        md: { columns: 2 }
        sm: { columns: 1 }
```

### Page-Level Styles

For styles that apply to the entire page (not a specific section),
use a top-level `styles:` key:

```yaml
type: page
route: /
styles:
  max_width: 1200px
  background: var(--color-surface)
```

### Principles

1. **Theme tokens first** — Use `var(--token)` references from
   `theme.yaml` wherever possible. Raw values only when no token exists.
2. **Minimal overrides** — Page styles should only cover
   structure, layout, and unique elements. Shared visual patterns
   belong in the theme or component variants.
3. **Co-located** — Styles live in the same file as the thing they
   describe. No separate style-only blueprints.
4. **Single CSS output** — The pipeline collects theme tokens,
   component variants, and page styles into one generated CSS file.
