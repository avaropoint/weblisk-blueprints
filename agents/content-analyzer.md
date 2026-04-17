<!-- blueprint
type: agent
name: content-analyzer
version: 1.0.0
kind: work
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: content
-->

# Content Analyzer Agent

Work agent that performs content quality analysis. Dispatched by the
content domain controller — never invoked directly by the orchestrator
or external clients. Scans HTML and markdown files, measures
readability, validates heading structure, checks paragraph balance,
and identifies quality issues.

## Capabilities

```json
{
  "capabilities": [
    {"name": "file:read", "resources": ["**/*.html", "**/*.md"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "target_files", "type": "file_list", "description": "HTML or markdown files to analyze"}
  ],
  "outputs": [
    {"name": "analysis", "type": "json", "description": "Readability scores, structure findings, and quality issues per file"}
  ],
  "collaborators": []
}
```

## HandleMessage Actions

| Action | Payload | Response |
|--------|---------|----------|
| `analyze` | `{files: string[]}` | `{results: FileAnalysis[]}` |
| `apply_fix` | `{file: string, fix: Fix}` | `{success: bool, diff: string}` |
| `score` | `{file: string}` | `{content_score: number, breakdown: ScoreBreakdown}` |

## Execute Workflow

```
1. RECEIVE task from content domain controller
   Input: {target_files: ["index.html", "about.html", ...]}

2. READ each file
   Extract text content (strip HTML tags for readability analysis)
   Parse document structure (heading hierarchy, sections, paragraphs)

3. ANALYZE readability per file:
   a. Flesch-Kincaid readability ease
   b. Average sentence length (words per sentence)
   c. Average word length (syllables per word)
   d. Passive voice percentage
   e. Complex word ratio (3+ syllables)

4. ANALYZE structure per file:
   a. Heading hierarchy — does h1 → h2 → h3 follow correct order?
   b. Heading count — is there exactly one h1?
   c. Section balance — are sections roughly similar length?
   d. Paragraph length — flag paragraphs > 150 words
   e. List usage — are there opportunities for lists in dense paragraphs?

5. ANALYZE quality signals:
   a. Word count (flag pages < 300 words as thin content)
   b. Link density — internal/external ratio
   c. Image-to-text ratio
   d. Empty elements (empty paragraphs, empty headings)
   e. Duplicate content detection (via text fingerprinting)

6. SCORE each file:
   readability_score = normalize(flesch_kincaid, 0, 100)
   structure_score = deductions from hierarchy/balance violations
   overall = weighted(readability: 0.5, structure: 0.3, quality: 0.2)

7. BUILD findings array:
   Each finding = {file, severity, category, element, message, suggested}

8. RETURN ContentAnalysis to domain controller
```

## Types

### FileAnalysis

```json
{
  "file": "about.html",
  "word_count": 1247,
  "readability": {
    "flesch_kincaid": 58.2,
    "grade_level": "10th Grade",
    "avg_sentence_length": 18.4,
    "avg_word_length": 1.6,
    "passive_voice_pct": 12.3,
    "complex_word_pct": 8.1
  },
  "structure": {
    "h1_count": 1,
    "heading_hierarchy_valid": true,
    "heading_order": ["h1", "h2", "h2", "h3", "h2"],
    "section_count": 4,
    "avg_section_length": 312,
    "max_paragraph_words": 142,
    "list_count": 2
  },
  "quality": {
    "internal_links": 8,
    "external_links": 3,
    "images": 2,
    "images_with_alt": 1,
    "empty_elements": 0,
    "duplicate_fingerprint": null
  },
  "content_score": 72,
  "findings": []
}
```

### Fix

```json
{
  "type": "heading_reorder",
  "file": "about.html",
  "element": "h3:nth-child(2)",
  "current": "<h3>Our Mission</h3>",
  "proposed": "<h2>Our Mission</h2>",
  "reason": "h3 follows h1 — missing h2 level"
}
```

## Implementation Notes

### Readability Calculation

Flesch-Kincaid readability ease:
```
206.835 - 1.015 × (total_words / total_sentences)
        - 84.6  × (total_syllables / total_words)
```

Score ranges:
- 90–100: Very easy (5th grade)
- 60–70: Standard (8th–9th grade) — target for web content
- 30–50: Difficult (college level)
- 0–30: Very difficult (graduate level)

### Syllable Counting

Use a dictionary-based approach with fallback heuristic:
1. Check a syllable dictionary first (covers common words)
2. Fallback: count vowel groups, subtract silent-e, add for
   -le/-les endings

### Structure Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| No h1 | critical | Every page needs exactly one h1 |
| Multiple h1 | high | Only one h1 per page |
| Skipped heading level | high | h1 → h3 (missing h2) |
| Paragraph > 150 words | medium | Consider splitting for readability |
| Section imbalance > 3x | medium | One section is 3x longer than the shortest |
| No lists in dense content | low | 3+ consecutive short sentences could be a list |

## Verification Checklist

- [ ] Agent registers with kind: work and domain: content
- [ ] Reads only file:read capability (no write access during analysis)
- [ ] Computes Flesch-Kincaid score for each file
- [ ] Validates heading hierarchy (h1 → h2 → h3 order)
- [ ] Flags pages with < 300 words as thin content
- [ ] Generates findings with severity levels
- [ ] apply_fix only modifies structure (never changes content text)
- [ ] Returns FileAnalysis per file with all required fields
- [ ] Content score is 0–100 scale
