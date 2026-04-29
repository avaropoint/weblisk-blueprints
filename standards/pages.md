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
