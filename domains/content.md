<!-- blueprint
type: domain
name: content
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
platform: any
-->

# Content Domain Controller

The content domain controller owns the content quality business
function. It receives tasks ("analyze this page's readability",
"check content structure", "validate metadata"), decomposes them
into multi-agent workflows, dispatches work to specialized agents,
aggregates results, and feeds outcomes back into the continuous
optimization lifecycle.

This domain does NOT perform content analysis itself. It directs
agents that do: the [content-analyzer](../agents/content-analyzer.md)
for readability and structure assessment and the
[meta-checker](../agents/meta-checker.md) for metadata validation
and completeness.

Content quality is the foundation that SEO, accessibility, and user
experience build on. This domain provides the baseline intelligence
that other domains consume.

## Domain Manifest

```json
{
  "name": "content",
  "type": "domain",
  "version": "1.0.0",
  "description": "Content quality — readability, structure, metadata validation",
  "url": "http://localhost:9710",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "target_files", "type": "file_list", "description": "HTML or markdown files to analyze"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated content quality report with scores and recommendations"}
  ],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["content-analyzer", "meta-checker"],
  "workflows": ["content-audit", "content-optimize"]
}
```

## Required Agents

| Agent | Kind | Role |
|-------|------|------|
| [content-analyzer](../agents/content-analyzer.md) | work | Readability scoring, structure analysis, word count, heading hierarchy, link density |
| [meta-checker](../agents/meta-checker.md) | work | Metadata validation — title, description, Open Graph, Twitter cards, structured data |

## Workflows

### content-audit

Full content quality assessment across all target files.

```
Phase 1: ANALYZE (parallel dispatch)
  ├── content-analyzer.execute(target_files)
  │   Returns: readability scores, structure findings, word counts
  └── meta-checker.execute(target_files)
      Returns: metadata completeness, missing fields, validation errors

Phase 2: AGGREGATE
  Domain controller merges results:
    - Per-file content score (0–100)
    - Readability grade (Flesch-Kincaid)
    - Structure score (heading hierarchy, section balance)
    - Metadata completeness score (0–100)
    - Overall content quality score (weighted average)

Phase 3: RECOMMEND
  Generate recommendations from findings:
    - Priority: critical (broken metadata) > high (poor readability) > medium (structure) > low (style)
    - Each recommendation links to the specific file + element
    - Recommendations include concrete suggested text where applicable

Phase 4: OBSERVE
  Record observations for the lifecycle:
    - Content scores over time (trending)
    - Readability changes between audits
    - Metadata coverage improvements
    - Recurring issues across audits

Phase 5: REPORT
  Return ContentDomainReport:
    - summary: overall scores and grade
    - files: per-file breakdown
    - findings: all issues with severity
    - recommendations: prioritized action items
    - observations: trend data for lifecycle
```

### content-optimize

Apply recommended changes to improve content quality.

```
Phase 1: PLAN
  Review current recommendations from the observation store.
  Select optimizations that are:
    - Approved by admin (approval: required)
    - Non-destructive (metadata additions, not content rewrites)
    - Within the agent's capability scope

Phase 2: EXECUTE (sequential, per-file)
  For each selected optimization:
    └── content-analyzer.handleMessage("apply_fix", {file, fix})
        or meta-checker.handleMessage("apply_fix", {file, fix})
  Fixes are limited to:
    - Adding missing meta tags (title, description, og:*)
    - Adding missing alt text placeholders
    - Fixing heading hierarchy (h1 → h2 → h3 order)

Phase 3: VERIFY
  Re-run content-audit on modified files.
  Compare before/after scores.
  If score decreased → revert change, log failure.

Phase 4: MEASURE
  Record metrics:
    - Optimizations attempted vs succeeded
    - Score delta per file
    - Time to completion
```

## Types

### ContentDomainReport

```json
{
  "domain": "content",
  "workflow": "content-audit",
  "timestamp": 1712160000,
  "summary": {
    "overall_score": 74,
    "readability_score": 68,
    "structure_score": 82,
    "metadata_score": 71,
    "files_analyzed": 12,
    "total_findings": 28,
    "critical": 3,
    "high": 8,
    "medium": 12,
    "low": 5
  },
  "files": [
    {
      "path": "index.html",
      "content_score": 81,
      "readability_grade": "8th Grade",
      "flesch_kincaid": 62.3,
      "word_count": 847,
      "structure_score": 90,
      "metadata_score": 75,
      "findings_count": 2
    }
  ],
  "findings": [
    {
      "file": "about.html",
      "severity": "high",
      "category": "readability",
      "element": "section.intro > p:nth-child(2)",
      "message": "Sentence too complex — 48 words, recommend splitting",
      "current": "The platform enables...",
      "suggested": null
    }
  ],
  "recommendations": [
    {
      "priority": "critical",
      "category": "metadata",
      "file": "pricing.html",
      "message": "Missing meta description — search engines will generate one automatically, usually poorly",
      "fix_type": "auto",
      "proposed": "<meta name=\"description\" content=\"...\">"
    }
  ]
}
```

### Scoring

| Metric | Weight | Measurement |
|--------|--------|------------|
| Readability | 30% | Flesch-Kincaid readability ease (target: 60–70 for general web content) |
| Structure | 30% | Heading hierarchy, section balance, paragraph length distribution |
| Metadata | 25% | Title, description, OG tags, Twitter cards, structured data presence |
| Link quality | 15% | Internal/external link ratio, broken link detection, anchor text quality |

### Finding Categories

| Category | What It Checks |
|----------|---------------|
| `readability` | Sentence complexity, passive voice, jargon density, reading level |
| `structure` | Heading hierarchy (h1→h2→h3), section length balance, list usage |
| `metadata` | Title length, description length, OG completeness, structured data validity |
| `links` | Broken links, orphan pages, excessive external links, missing anchor text |
| `formatting` | Image alt text, empty elements, inconsistent formatting |

## Strategy Alignment

The content domain connects to business strategy through the
lifecycle's Strategize phase:

| Business Objective | Content Strategy | Metric |
|--------------------|-----------------|--------|
| Improve user engagement | Increase readability scores | Avg Flesch-Kincaid > 60 |
| Improve search visibility | Complete metadata coverage | Metadata score > 90 |
| Reduce bounce rate | Improve content structure | Structure score > 85 |
| Support accessibility | Add missing alt text, heading hierarchy | Findings count decreasing |

## Verification Checklist

- [ ] Domain controller dispatches to content-analyzer and meta-checker
- [ ] Parallel dispatch in Phase 1 (both agents run concurrently)
- [ ] Aggregation produces per-file and overall scores
- [ ] Recommendations reference specific files and elements
- [ ] content-optimize only applies admin-approved fixes
- [ ] Verify phase re-audits modified files after optimization
- [ ] Score decreases trigger automatic revert
- [ ] Observations recorded for lifecycle trending
- [ ] Domain report includes all required fields
- [ ] Scoring weights are configurable but default to specified values
