<!-- blueprint
type: agent
name: seo-analyzer
version: 1.0.0
kind: work
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: seo
-->

# SEO Analyzer Agent

Work agent that performs the technical SEO analysis. Dispatched by the
SEO domain controller — never invoked directly by the orchestrator or
external clients. Scans HTML files, extracts metadata, analyzes quality
via LLM, validates findings, and proposes changes.

## Capabilities

```json
{
  "capabilities": [
    {"name": "file:read", "resources": ["**/*.html"]},
    {"name": "llm:chat", "resources": []},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "html_files", "type": "file_list", "description": "HTML files to scan"},
    {"name": "metadata", "type": "json", "description": "Pre-extracted metadata to analyze"}
  ],
  "outputs": [
    {"name": "scan_results", "type": "json", "description": "Extracted metadata per file"},
    {"name": "analysis", "type": "json", "description": "Findings and recommendations"}
  ],
  "collaborators": []
}
```

## HandleMessage Actions

### scan_html

Scan HTML files and extract SEO-relevant metadata.

**Input:**
```json
{
  "html_files": ["app/index.html", "app/about.html"]
}
```

**Process:**
```
1. For each file in html_files:
   a. Read file content
   b. Extract metadata (see Extraction Rules below)
   c. Record measurements: title_length, description_length, h1_count,
      heading_count, image_count, images_missing_alt
2. Identify findings against validation rules (see Validation Rules)
3. Return scan results
```

**Output:**
```json
{
  "files": [
    {
      "path": "app/index.html",
      "metadata": {
        "title": "Home",
        "meta_description": "",
        "lang": "en",
        "canonical": "",
        "og_title": "",
        "og_description": "",
        "og_image": "",
        "headings": [{"level": 2, "text": "Welcome"}],
        "images": [{"src": "/logo.png", "alt": ""}]
      },
      "measurements": {
        "title_length": 4,
        "description_length": 0,
        "h1_count": 0,
        "image_count": 1,
        "images_missing_alt": 1
      }
    }
  ],
  "findings": [
    {"rule_id": "seo-title-short", "severity": "critical", "element": "title", "current": "Home", "expected": "30-60 characters", "message": "Title too short for SEO", "fixable": true, "fix": ""}
  ]
}
```

### analyze_metadata

Analyze extracted metadata using LLM and produce recommendations.

**Input:**
```json
{
  "metadata": [
    {"path": "app/index.html", "title": "Home", "meta_description": "", ...}
  ],
  "entity": {
    "name": "Weblisk",
    "industry": "technology",
    "keywords": ["web framework", "javascript"],
    "tone": "professional"
  }
}
```

**Process:**
```
1. Build LLM prompt with entity context and extracted metadata
2. Send to configured LLM provider
3. Parse LLM response as JSON array of suggestions
4. Validate each suggestion:
   - Reject if file, element, or suggested value is empty
   - Reject titles outside 10–80 characters
   - Reject descriptions outside 50–200 characters
   - Reject if current == suggested (no change)
5. Convert validated suggestions to Recommendation entries
6. Return analysis results
```

**Output:**
```json
{
  "recommendations": [
    {
      "target": "app/index.html",
      "element": "title",
      "current": "Home",
      "proposed": "Weblisk — Modern Web Framework",
      "reason": "Title too short — include primary keywords for search visibility",
      "priority": "critical",
      "impact": 0.8
    }
  ],
  "observations": [
    {
      "target": "app/index.html",
      "measurements": {"title_length": 4, "description_length": 0},
      "findings": [...]
    }
  ]
}
```

### generate_report

Produce a unified SEO report from analysis and accessibility results.

**Input:**
```json
{
  "analysis": { ... },
  "a11y": { ... }
}
```

**Output:**
```json
{
  "score": 45,
  "summary": "5 files scanned, 12 issues found (3 critical, 5 high, 4 medium)",
  "recommendations": [...],
  "proposed_changes": [
    {
      "path": "app/index.html",
      "action": "modify",
      "original": "<title>Home</title>",
      "modified": "<title>Weblisk — Modern Web Framework</title>",
      "diffs": [{"element": "title", "before": "Home", "after": "Weblisk — Modern Web Framework", "reason": "Title too short"}]
    }
  ]
}
```

### review_seo

Another agent asks for a quick SEO review of specific content (no LLM).

**Input:** `{"content": "<html>..."}` (raw HTML string)
**Output:** `{"metadata": {...}, "findings": [...]}`

## Metadata Extraction Rules

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

## Validation Rules

| Element | Constraint |
|---------|-----------|
| title | 30–60 characters optimal, reject < 10 or > 80 |
| meta_description | 120–160 characters optimal, reject < 50 or > 200 |
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
| meta_description | Replace content attr in existing meta, or insert before `</head>` |
| og_title | Replace content attr in existing og:title, or insert before `</head>` |
| og_description | Replace content attr, or insert before `</head>` |
| lang | Replace lang attr on `<html>`, or add `lang="X"` to existing tag |
| canonical | Replace href in existing canonical link, or insert before `</head>` |

General rule: if the element exists, replace in-place. If absent, insert
new tag before `</head>` with 4-space indentation.

## Port Assignment

seo-analyzer: 9710

## Verification Checklist

- [ ] Scans HTML files and extracts all metadata fields
- [ ] Validates findings against all constraint rules
- [ ] Sends extracted metadata to LLM for analysis
- [ ] Parses LLM response and validates suggestions
- [ ] Returns structured Observations with measurements
- [ ] Returns structured Recommendations with priority and impact
- [ ] Generates ProposedChange entries with full diffs
- [ ] Handles review_seo action without LLM
- [ ] Respects entity context (keywords, tone) in LLM prompts
