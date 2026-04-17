<!-- blueprint
type: agent
name: meta-checker
version: 1.0.0
kind: work
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: content
-->

# Meta Checker Agent

Work agent that validates HTML metadata completeness and correctness.
Dispatched by the content domain controller. Checks `<head>` elements
including title, description, Open Graph tags, Twitter cards, canonical
URLs, structured data (JSON-LD), and favicon references.

## Capabilities

```json
{
  "capabilities": [
    {"name": "file:read", "resources": ["**/*.html"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "target_files", "type": "file_list", "description": "HTML files to validate metadata"}
  ],
  "outputs": [
    {"name": "meta_report", "type": "json", "description": "Metadata completeness and issues per file"}
  ],
  "collaborators": []
}
```

## HandleMessage Actions

| Action | Payload | Response |
|--------|---------|----------|
| `check` | `{files: string[]}` | `{results: MetaReport[]}` |
| `apply_fix` | `{file: string, fix: MetaFix}` | `{success: bool, diff: string}` |
| `validate_structured_data` | `{file: string}` | `{valid: bool, errors: string[]}` |

## Execute Workflow

```
1. RECEIVE task from content domain controller
   Input: {target_files: ["index.html", "about.html", ...]}

2. PARSE each HTML file — extract <head> section

3. CHECK required meta tags per file:
   a. <title> — exists, length 30–60 chars, unique across site
   b. <meta name="description"> — exists, length 120–160 chars
   c. <meta name="viewport"> — exists
   d. <link rel="canonical"> — exists, valid URL
   e. <html lang=""> — language attribute set

4. CHECK Open Graph tags:
   a. og:title — exists, matches or extends <title>
   b. og:description — exists, matches or extends meta description
   c. og:image — exists, absolute URL, dimensions ≥ 1200×630
   d. og:url — exists, matches canonical
   e. og:type — exists (website/article/product)
   f. og:site_name — exists

5. CHECK Twitter Card tags:
   a. twitter:card — summary or summary_large_image
   b. twitter:title — exists
   c. twitter:description — exists
   d. twitter:image — exists, absolute URL

6. CHECK structured data (JSON-LD):
   a. At least one <script type="application/ld+json"> block
   b. Valid JSON syntax
   c. @type present and recognized
   d. Required properties for the declared @type
   e. No conflicting data between JSON-LD and meta tags

7. CHECK additional metadata:
   a. <link rel="icon"> or <link rel="shortcut icon"> — exists
   b. <meta name="robots"> — if present, validate content
   c. <meta charset="utf-8"> — exists
   d. <link rel="alternate" hreflang=""> — if multilingual

8. SCORE completeness:
   required_tags = 5        → weight 0.4
   open_graph = 6 tags      → weight 0.25
   twitter_card = 4 tags    → weight 0.15
   structured_data = valid   → weight 0.1
   additional = 4 tags      → weight 0.1

9. BUILD findings array per file

10. RETURN MetaReport[] to domain controller
```

## Types

### MetaReport

```json
{
  "file": "index.html",
  "meta_score": 84,
  "required": {
    "title": {"present": true, "value": "Weblisk — Modern Web Framework", "length": 33, "valid": true},
    "description": {"present": true, "value": "Build for the web...", "length": 142, "valid": true},
    "viewport": {"present": true, "valid": true},
    "canonical": {"present": true, "value": "https://weblisk.dev/", "valid": true},
    "lang": {"present": true, "value": "en", "valid": true}
  },
  "open_graph": {
    "og:title": {"present": true, "valid": true},
    "og:description": {"present": true, "valid": true},
    "og:image": {"present": true, "valid": true, "url": "https://weblisk.dev/og.png"},
    "og:url": {"present": true, "valid": true},
    "og:type": {"present": true, "value": "website"},
    "og:site_name": {"present": false, "valid": false}
  },
  "twitter_card": {
    "twitter:card": {"present": true, "value": "summary_large_image"},
    "twitter:title": {"present": true, "valid": true},
    "twitter:description": {"present": true, "valid": true},
    "twitter:image": {"present": true, "valid": true}
  },
  "structured_data": {
    "present": true,
    "valid": true,
    "types": ["WebSite"],
    "errors": []
  },
  "additional": {
    "favicon": {"present": true},
    "charset": {"present": true},
    "robots": {"present": false},
    "hreflang": {"present": false}
  },
  "findings": []
}
```

### MetaFix

```json
{
  "type": "add_meta",
  "file": "about.html",
  "tag": "og:site_name",
  "proposed": "<meta property=\"og:site_name\" content=\"Weblisk\">",
  "reason": "Missing og:site_name — required for social sharing"
}
```

## Validation Rules

| Tag | Severity | Validation |
|-----|----------|------------|
| title | critical | Must exist, 30–60 chars |
| meta description | critical | Must exist, 120–160 chars |
| viewport | high | Must exist |
| canonical | high | Must exist, valid absolute URL |
| og:title | medium | Must exist for social sharing |
| og:description | medium | Must exist for social sharing |
| og:image | medium | Must exist, absolute URL |
| twitter:card | medium | Must exist for Twitter previews |
| JSON-LD | medium | Must be valid JSON, correct @type |
| charset | low | Should be utf-8 |
| favicon | low | Should exist for browser tabs |
| robots | info | Validate if present (no accidental noindex) |

## Length Constraints

| Tag | Min | Max | Optimal |
|-----|-----|-----|---------|
| title | 30 | 60 | 50–60 |
| meta description | 120 | 160 | 150–160 |
| og:title | 30 | 60 | 50–60 |
| og:description | 55 | 200 | 120–160 |
| twitter:title | 30 | 70 | 50–60 |
| twitter:description | 55 | 200 | 120–160 |

## Verification Checklist

- [ ] Agent registers with kind: work and domain: content
- [ ] Reads only HTML files (file:read capability)
- [ ] Validates all 5 required meta tag categories
- [ ] Checks Open Graph completeness (6 tags)
- [ ] Checks Twitter Card completeness (4 tags)
- [ ] Validates JSON-LD syntax and required @type properties
- [ ] Scores metadata completeness on 0–100 scale
- [ ] apply_fix inserts missing tags into <head> section correctly
- [ ] Findings include severity levels matching validation table
- [ ] Does not modify existing tag content — only flags and suggests
