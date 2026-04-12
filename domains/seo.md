<!-- blueprint
type: domain
name: seo
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/agent]
platform: any
-->

# SEO Agent Domain Knowledge

Domain-specific intelligence for the SEO agent. This agent scans HTML
files, extracts SEO metadata, analyzes quality via LLM, validates
suggestions, collaborates with other agents, and proposes file changes.

## Capabilities

```json
{
  "capabilities": [
    {"name": "file:read", "resources": ["app/**/*.html"]},
    {"name": "file:write", "resources": ["app/**/*.html"]},
    {"name": "llm:chat", "resources": []},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "html_files", "type": "file_list", "description": "HTML files to analyze"}
  ],
  "outputs": [
    {"name": "seo_report", "type": "json", "description": "SEO analysis with proposed changes"}
  ],
  "collaborators": ["a11y"]
}
```

## Execute Workflow

```
Phase 1 — Scan:
  Scan app/**/*.html for all HTML files.
  Skip if no files found (return success, no changes).

Phase 2 — Extract metadata:
  For each HTML file, extract:
  - title (from <title> tag, strip inner HTML)
  - meta_description (from <meta name="description"> content)
  - lang (from <html lang="X">)
  - canonical (from <link rel="canonical">)
  - og:title, og:description, og:image (from Open Graph meta tags)
  - headings (level + text for all h1-h6)
  - images (src + alt for all <img> tags)

Phase 3 — Analyze with LLM:
  Send extracted metadata to the configured LLM with the SEO system prompt.
  Parse response as JSON array of suggestions.

Phase 4 — Validate:
  Filter suggestions:
  - Reject if file, element, or suggested value is empty
  - Reject titles outside 10-80 characters
  - Reject descriptions outside 50-200 characters
  - Reject if current == suggested (no change)

Phase 5 — Collaborate:
  If "a11y" agent is online in service directory:
  - Collect all img_alt suggestions
  - Send to a11y agent via POST /v1/message action:"review_alt_text"
  - Incorporate a11y feedback into suggestions  

Phase 6 — Build changes:
  Group validated suggestions by file.
  For each file, apply all suggestions to generate modified content.
  Create ProposedChange with original, modified, and diffs.
  Return with status "pending_approval".
```

## HandleMessage Actions

### review_seo
Another agent asks for SEO review of specific content.
- Input: `payload.content` (HTML string)
- Process: extract metadata, identify issues (without LLM)
- Output: `{meta: {...}, issues: [...]}`

### get_capabilities
Returns what this agent can analyze and optimize.
- Output:
```json
{
  "can_analyze": ["title", "meta_description", "headings", "alt_text", "og_tags", "lang", "canonical"],
  "can_optimize": ["title", "meta_description", "og_title", "og_description", "canonical", "lang"]
}
```

## HTML Metadata Extraction

Regex patterns (case-insensitive, dotall where needed):

| Element | Pattern |
|---------|---------|
| title | `<title[^>]*>(.*?)</title>` (strip inner HTML tags) |
| meta description | `<meta\s+name=["']description["']\s+content=["'](.*?)["']` |
| meta description (alt) | `<meta\s+content=["'](.*?)["']\s+name=["']description["']` |
| lang | `<html[^>]*\slang=["'](.*?)["']` |
| canonical | `<link[^>]*rel=["']canonical["'][^>]*href=["'](.*?)["']` |
| og:title | `<meta\s+property=["']og:title["']\s+content=["'](.*?)["']` |
| og:description | `<meta\s+property=["']og:description["']\s+content=["'](.*?)["']` |
| og:image | `<meta\s+property=["']og:image["']\s+content=["'](.*?)["']` |
| headings | `<(h[1-6])[^>]*>(.*?)</h[1-6]>` (level from tag, strip inner HTML) |
| images | `<img\s[^>]*>` then extract `src=["'](.*?)["']` and `alt=["'](.*?)["']` |

## SEO Validation Rules

| Element | Constraint |
|---------|-----------|
| title | 30-60 characters optimal, reject < 10 or > 80 |
| meta_description | 120-160 characters optimal, reject < 50 or > 200 |
| lang | must be present on `<html>` tag |
| h1 | exactly one per page |
| heading hierarchy | must not skip levels (h1→h2→h3, never h1→h3) |
| images | all `<img>` must have non-empty alt text |
| og:title | should be present |
| og:description | should be present |
| canonical | should be present |

## LLM System Prompt

```
You are an SEO optimization agent for a web project.
Analyze the provided HTML file metadata and suggest concrete improvements.

Rules:
- Page titles: 30-60 characters, include primary keywords, unique per page
- Meta descriptions: 120-160 characters, compelling, action-oriented, unique per page
- Every page MUST have exactly one <h1> tag
- Heading hierarchy must not skip levels (h1 → h2 → h3, never h1 → h3)
- All <img> tags must have descriptive, non-empty alt text
- Pages should declare lang attribute on <html>
- Canonical URLs should be present
- Open Graph tags (og:title, og:description) should be present for social sharing

Respond with a JSON array of suggestions. Each item:
{
  "file": "relative/path.html",
  "element": "title|meta_description|h1|heading_hierarchy|img_alt|lang|canonical|og_title|og_description|og_image",
  "current": "current value or empty string",
  "suggested": "the improved value",
  "reason": "brief explanation",
  "priority": "high|medium|low"
}

Only suggest changes that would GENUINELY improve SEO.
Do NOT suggest changes where the current value is already good.
Respond ONLY with the JSON array — no markdown fences, no explanation.
```

## HTML Modification Rules

How to apply each type of change:

| Element | Strategy |
|---------|----------|
| title | Replace `<title>...</title>` content, or insert before `</head>` |
| meta_description | Replace content attr in existing meta tag, or insert before `</head>` |
| og_title | Replace content attr in existing og:title, or insert before `</head>` |
| og_description | Replace content attr in existing og:description, or insert before `</head>` |
| lang | Replace lang attr on `<html>`, or add `lang="X"` to existing `<html>` tag |
| canonical | Replace href in existing canonical link, or insert before `</head>` |

General rule: if the element exists, replace in-place. If absent, insert
new tag before `</head>` with 4-space indentation.
