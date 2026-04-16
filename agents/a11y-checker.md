<!-- blueprint
type: agent
name: a11y-checker
version: 1.0.0
kind: work
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: seo
-->

# Accessibility Checker Agent

Work agent that evaluates HTML files for accessibility compliance.
Dispatched by domain controllers (primarily SEO) that need
accessibility input as part of their workflows.

## Capabilities

```json
{
  "capabilities": [
    {"name": "file:read", "resources": ["**/*.html"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "html_files", "type": "file_list", "description": "HTML files to check"},
    {"name": "images", "type": "json", "description": "Image data to check for alt text"}
  ],
  "outputs": [
    {"name": "a11y_report", "type": "json", "description": "Accessibility findings and recommendations"}
  ],
  "collaborators": []
}
```

## HandleMessage Actions

### check_images

Check images for alt text quality and ARIA compliance.

**Input:**
```json
{
  "images": [
    {"file": "app/index.html", "src": "/logo.png", "alt": ""},
    {"file": "app/index.html", "src": "/hero.jpg", "alt": "hero image"}
  ]
}
```

**Process:**
```
1. For each image:
   a. Check if alt text is present and non-empty
   b. Check if alt text is descriptive (not generic like "image", "photo", "banner")
   c. Check if decorative images use alt="" (intentionally empty is OK for decorative)
   d. Check alt text length (recommended: 10-150 characters)
2. Return findings for images with issues
```

**Output:**
```json
{
  "findings": [
    {"rule_id": "a11y-alt-missing", "severity": "critical", "element": "img", "current": "", "expected": "descriptive alt text", "message": "Image /logo.png has no alt text", "fixable": false},
    {"rule_id": "a11y-alt-generic", "severity": "warning", "element": "img", "current": "hero image", "expected": "specific description", "message": "Alt text 'hero image' is too generic", "fixable": false}
  ],
  "measurements": {
    "total_images": 2,
    "images_missing_alt": 1,
    "images_generic_alt": 1,
    "images_compliant": 0
  }
}
```

### check_full

Full accessibility audit of HTML files.

**Input:**
```json
{
  "html_files": ["app/index.html", "app/about.html"]
}
```

**Process:**
```
1. For each file, check:
   a. Images: alt text presence and quality (same as check_images)
   b. Headings: hierarchy must not skip levels (h1→h2→h3)
   c. Language: <html> must have lang attribute
   d. Landmarks: page should have <main>, <nav>, <header>, <footer>
   e. Links: anchor text must be descriptive (not "click here", "read more")
   f. Forms: inputs must have associated <label> elements
   g. Color contrast: flag if inline styles suggest low contrast
   h. Focus: interactive elements should be keyboard accessible
2. Score each category: compliant, partial, non-compliant
3. Return findings grouped by category
```

**Output:**
```json
{
  "files": [
    {
      "path": "app/index.html",
      "score": 60,
      "categories": {
        "images": {"status": "non-compliant", "issues": 3},
        "headings": {"status": "partial", "issues": 1},
        "language": {"status": "compliant", "issues": 0},
        "landmarks": {"status": "partial", "issues": 1},
        "links": {"status": "compliant", "issues": 0},
        "forms": {"status": "non-compliant", "issues": 2}
      }
    }
  ],
  "findings": [...],
  "observations": [
    {
      "target": "app/index.html",
      "measurements": {"a11y_score": 60, "total_issues": 7, "critical_issues": 3}
    }
  ]
}
```

### review_alt_text

Another agent sends alt text suggestions for accessibility review.

**Input:**
```json
{
  "suggestions": [
    {"file": "app/index.html", "src": "/logo.png", "proposed_alt": "Company logo"}
  ]
}
```

**Process:**
```
1. For each suggestion:
   a. Check proposed alt text is descriptive (not generic)
   b. Check length is reasonable (10-150 chars)
   c. Check it describes the image purpose, not just appearance
2. Return reviewed suggestions with approval/revision
```

**Output:**
```json
{
  "reviewed": [
    {"file": "app/index.html", "src": "/logo.png", "proposed_alt": "Company logo", "approved": true},
    {"file": "app/index.html", "src": "/hero.jpg", "proposed_alt": "A photo", "approved": false, "revision": "Team collaborating on a web project", "reason": "Alt text should describe the image content, not just say 'a photo'"}
  ]
}
```

## Validation Rules

| Category | Rule | Severity |
|----------|------|----------|
| Images | All `<img>` must have alt attribute | critical |
| Images | Alt text must not be generic ("image", "photo", "banner") | warning |
| Images | Alt text should be 10-150 characters | info |
| Headings | Page must have exactly one `<h1>` | critical |
| Headings | Heading levels must not skip (h1→h3 without h2) | warning |
| Language | `<html>` must have `lang` attribute | critical |
| Landmarks | Page should have `<main>` element | warning |
| Links | Link text must not be "click here" or "read more" | warning |
| Links | Links must be distinguishable (not just color) | warning |
| Forms | All `<input>` must have associated `<label>` | critical |
| Forms | Required fields must have `aria-required="true"` | warning |

## Port Assignment

a11y-checker: 9711

## Verification Checklist

- [ ] Checks all images for alt text presence
- [ ] Identifies generic alt text values
- [ ] Validates heading hierarchy
- [ ] Checks for lang attribute on `<html>`
- [ ] Identifies missing landmark elements
- [ ] Validates form label associations
- [ ] Scores each file by accessibility compliance
- [ ] Returns structured findings with severity
- [ ] review_alt_text action provides alt text quality feedback
- [ ] Returns observations with measurements for lifecycle tracking
