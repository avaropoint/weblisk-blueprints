<!-- blueprint
type: agent
name: perf-auditor
version: 1.0.0
kind: work
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: health
-->

# Performance Auditor Agent

Work agent that measures page load performance, resource efficiency,
and Core Web Vitals. Dispatched by the health domain controller during
the `health-report` workflow. Produces per-page performance scores
with actionable recommendations.

## Capabilities

```json
{
  "capabilities": [
    {"name": "net:http", "resources": ["*"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "urls", "type": "string[]", "description": "URLs to audit for performance"}
  ],
  "outputs": [
    {"name": "results", "type": "json", "description": "Performance metrics and findings per URL"}
  ],
  "collaborators": []
}
```

## HandleMessage Actions

| Action | Payload | Response |
|--------|---------|----------|
| `audit` | `{urls: string[]}` | `{results: PerfResult[]}` |
| `audit_resources` | `{url: string}` | `{resources: ResourceBreakdown}` |

## Execute Workflow

```
1. RECEIVE URL list from health domain controller
   Input: {urls: ["https://example.com", "https://example.com/about"]}

2. FOR EACH URL:

   a. Load & Timing
      → Fetch the page and all sub-resources
      → Record timing milestones:
        - DNS lookup time
        - TCP connection time
        - TLS handshake time
        - Time to First Byte (TTFB)
        - First Contentful Paint (FCP)
        - Largest Contentful Paint (LCP)
        - DOM Content Loaded
        - Full page load time

   b. Core Web Vitals Assessment
      → LCP: Should be ≤ 2.5s (good), 2.5–4s (needs improvement), > 4s (poor)
      → FID/INP: Estimated from script execution time
      → CLS: Computed from layout-shifting elements (images without dimensions,
              late-loading fonts, dynamically injected content)

   c. Resource Analysis
      → Catalog all loaded resources (HTML, CSS, JS, images, fonts)
      → Record: count, total size, compressed size, cache headers
      → Flag uncompressed resources (missing gzip/brotli)
      → Flag resources without cache headers
      → Flag unused CSS/JS if detectable

   d. Performance Budget Check
      → Total page weight vs budget (default: 1MB)
      → JavaScript budget (default: 300KB)
      → Image budget (default: 500KB)
      → Request count budget (default: 50 requests)

   e. Optimization Opportunities
      → Images: missing width/height, unoptimized formats (PNG → WebP)
      → Fonts: not preloaded, too many font files
      → Scripts: render-blocking, not deferred/async
      → CSS: render-blocking, not critical-path optimized

3. SCORE each page:
   performance_score = weighted(
     lcp: 0.25, fcp: 0.15, ttfb: 0.15,
     cls: 0.15, page_weight: 0.15, request_count: 0.15
   )

4. BUILD findings array with severity and recommendations

5. RETURN PerfResult[] to health domain controller
```

## Types

### PerfResult

```json
{
  "url": "https://example.com",
  "performance_score": 87,
  "timing": {
    "dns_ms": 12,
    "tcp_ms": 28,
    "tls_ms": 35,
    "ttfb_ms": 85,
    "fcp_ms": 420,
    "lcp_ms": 1200,
    "dom_content_loaded_ms": 650,
    "full_load_ms": 1800
  },
  "core_web_vitals": {
    "lcp": {"value_ms": 1200, "rating": "good"},
    "fid_estimate": {"value_ms": 45, "rating": "good"},
    "cls": {"value": 0.02, "rating": "good"}
  },
  "resources": {
    "total_count": 28,
    "total_size_bytes": 456000,
    "total_compressed_bytes": 189000,
    "by_type": {
      "html": {"count": 1, "size": 24000},
      "css": {"count": 3, "size": 45000},
      "js": {"count": 8, "size": 180000},
      "image": {"count": 12, "size": 195000},
      "font": {"count": 4, "size": 12000}
    }
  },
  "budget": {
    "total_weight": {"budget": 1048576, "actual": 456000, "pass": true},
    "js_weight": {"budget": 307200, "actual": 180000, "pass": true},
    "image_weight": {"budget": 512000, "actual": 195000, "pass": true},
    "request_count": {"budget": 50, "actual": 28, "pass": true}
  },
  "findings": []
}
```

### ResourceBreakdown

```json
{
  "url": "https://example.com",
  "resources": [
    {
      "url": "https://example.com/styles.css",
      "type": "css",
      "size_bytes": 15000,
      "compressed_bytes": 4500,
      "compression": "brotli",
      "cache_control": "public, max-age=31536000",
      "render_blocking": true
    }
  ]
}
```

## Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP | ≤ 2500ms | 2500–4000ms | > 4000ms |
| FID/INP | ≤ 100ms | 100–300ms | > 300ms |
| CLS | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| TTFB | ≤ 800ms | 800–1800ms | > 1800ms |
| FCP | ≤ 1800ms | 1800–3000ms | > 3000ms |

## Performance Budget Defaults

| Resource | Budget | Severity if exceeded |
|----------|--------|---------------------|
| Total page weight | 1 MB | high |
| JavaScript | 300 KB | high |
| Images | 500 KB | medium |
| CSS | 100 KB | medium |
| Fonts | 200 KB | low |
| Total requests | 50 | medium |

## Verification Checklist

- [ ] Agent registers with kind: work and domain: health
- [ ] Uses net:http capability (no file system access)
- [ ] Measures TTFB, FCP, LCP, and CLS
- [ ] Catalogs all page resources by type and size
- [ ] Checks resource compression (gzip/brotli)
- [ ] Evaluates performance budgets
- [ ] Identifies render-blocking resources
- [ ] Flags images without dimensions (CLS contributors)
- [ ] Scores pages on 0–100 scale with weighted components
- [ ] Returns PerfResult per URL with all required fields
