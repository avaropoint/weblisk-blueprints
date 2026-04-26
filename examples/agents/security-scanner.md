<!-- blueprint
type: agent
kind: work
name: security-scanner
version: 1.1.0
port: 9712
extends: [patterns/observability, patterns/security]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain, architecture/gateway]
platform: any
tier: free
domain: security
-->

# Security Scanner Agent

Work agent for the security domain. Performs HTTP header analysis,
Content Security Policy validation, dependency vulnerability
auditing, and OWASP Top 10 static checks. Produces structured
findings that the security domain controller converts into
observations and recommendations.

## Overview

The security-scanner is a passive analysis agent — it reads
configuration files, fetches HTTP headers, and cross-references
dependency versions against vulnerability databases. It does NOT
send attack payloads, fuzz inputs, or perform active exploitation.

## Specification

### Blueprint Format

```yaml
name: security-scanner
version: 1.0.0
description: Passive web security analysis

capabilities:
  - file:read    **/*.json
  - file:read    **/*.lock
  - file:read    **/*.toml
  - file:read    **/*.txt
  - file:read    **/*.mod
  - file:read    **/*.sum
  - http:get     *
  - llm:chat     *
```

### Protocol Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/health` | Health check |
| POST | `/describe` | Agent capabilities and manifest |
| POST | `/task` | Execute a security scan action |
| POST | `/message` | Receive messages from other agents |
| POST | `/governance` | Accept governance directives |

---

## Task Actions

### scan-headers

Fetch HTTP response headers for target URLs and check for security
headers.

**Input:**
```json
{
  "task_id": "task-001",
  "action": "scan-headers",
  "payload": {
    "urls": ["https://example.com", "https://example.com/api"]
  }
}
```

**Process:**
```
1. For each URL:
   a. Send HEAD request (follow redirects, max 5)
   b. Collect response headers
   c. Check each security header against expected values
   d. Generate finding for each missing/misconfigured header
2. Return findings array
```

**Output:**
```json
{
  "task_id": "task-001",
  "status": "completed",
  "output": {
    "urls_scanned": 2,
    "findings": [
      {
        "id": "hdr-hsts-001",
        "category": "headers",
        "severity": "high",
        "title": "HSTS header missing",
        "target": "https://example.com",
        "evidence": "Header not present in response",
        "remediation": "Add Strict-Transport-Security: max-age=31536000; includeSubDomains"
      }
    ],
    "score": 72
  }
}
```

### scan-csp

Parse and validate Content Security Policy headers.

**Input:**
```json
{
  "task_id": "task-002",
  "action": "scan-csp",
  "payload": {
    "urls": ["https://example.com"]
  }
}
```

**Process:**
```
1. For each URL:
   a. Fetch headers (GET request to capture CSP in meta tags too)
   b. Extract Content-Security-Policy header value
   c. Parse into directive map: {directive: [sources]}
   d. Run each CSP check:
      - unsafe-inline in script-src?
      - unsafe-eval in script-src?
      - wildcard * in script-src?
      - default-src present?
      - frame-ancestors present?
      - base-uri restricted?
      - form-action restricted?
      - report-uri / report-to configured?
   e. Generate finding for each failed check
2. Return findings array with CSP score
```

**Output:**
```json
{
  "task_id": "task-002",
  "status": "completed",
  "output": {
    "urls_scanned": 1,
    "csp_present": true,
    "directives_found": ["default-src", "script-src", "style-src"],
    "findings": [
      {
        "id": "csp-unsafe-inline-001",
        "category": "csp",
        "severity": "high",
        "title": "unsafe-inline in script-src",
        "target": "https://example.com",
        "evidence": "script-src 'self' 'unsafe-inline'",
        "remediation": "Remove 'unsafe-inline' and use nonce-based or hash-based CSP"
      }
    ],
    "score": 55
  }
}
```

### scan-dependencies

Read dependency manifests and check for known vulnerabilities.

**Input:**
```json
{
  "task_id": "task-003",
  "action": "scan-dependencies",
  "payload": {
    "manifest_paths": ["package.json", "package-lock.json"]
  }
}
```

If `manifest_paths` is omitted, the agent auto-detects by scanning
for known manifest filenames in the project root.

**Process:**
```
1. Read manifest files via file:read capability
2. Parse dependency tree with locked versions
3. For each dependency:
   a. Query vulnerability database via the VulnDB interface
   b. Match version against affected ranges
   c. If vulnerable → create finding with CVE, CVSS, fix version
4. Calculate dependency score
5. Return findings array
```

### Vulnerability Database Interface

The security-scanner accesses vulnerability data through an abstract
`VulnDB` interface — the data source is a deployment choice, not a
framework requirement:

| Backend | Configuration | Use Case |
|---------|--------------|----------|
| Local snapshot | `WL_VULNDB=file://vulndb.json` | Offline, air-gapped, zero-dependency |
| OSV API | `WL_VULNDB=https://api.osv.dev` | Google's open vulnerability DB (free) |
| GitHub Advisory DB | `WL_VULNDB=ghsa://` | Via `weblisk-cli` GitHub token |
| Custom | `WL_VULNDB=https://your-api.com` | Enterprise internal DB |

The weblisk-cli ships a bundled snapshot of the OSV database that
can be used offline. It updates the snapshot on `weblisk update`.
This ensures the security-scanner works with zero network
dependencies by default.

```
VulnDB Interface:
  Query(ecosystem string, package string, version string)
    → []Vulnerability{CVE, CVSS, affected_ranges, fixed_version, references}
```

**Output:**
```json
{
  "task_id": "task-003",
  "status": "completed",
  "output": {
    "manifests_scanned": ["package.json", "package-lock.json"],
    "total_dependencies": 142,
    "vulnerable": 3,
    "findings": [
      {
        "id": "dep-CVE-2024-1234",
        "category": "dependencies",
        "severity": "critical",
        "title": "CVE-2024-1234 in lodash@4.17.20",
        "target": "lodash@4.17.20",
        "evidence": "Installed: 4.17.20, Fixed in: 4.17.21",
        "remediation": "Update lodash to >=4.17.21",
        "references": ["https://nvd.nist.gov/vuln/detail/CVE-2024-1234"],
        "cwe": "CWE-1321",
        "cvss": 9.8
      }
    ],
    "score": 60
  }
}
```

### scan-owasp

Static checks for OWASP Top 10 categories.

**Input:**
```json
{
  "task_id": "task-004",
  "action": "scan-owasp",
  "payload": {
    "urls": ["https://example.com"],
    "check_categories": ["A01", "A02", "A05", "A07"]
  }
}
```

If `check_categories` is omitted, all automatable categories are
checked.

**Process:**
```
For each URL:
  A01 — Broken Access Control:
    - Check CORS headers (Access-Control-Allow-Origin)
    - Check for directory listing (GET common paths, check for index)
    - Check for sensitive path exposure (/admin, /.env, /.git)

  A02 — Cryptographic Failures:
    - Check TLS version (must be ≥1.2)
    - Check for mixed content (HTTP resources on HTTPS page)
    - Check cookie Secure flag

  A05 — Security Misconfiguration:
    - Check for server version disclosure (Server header)
    - Check for default error pages (trigger 404, inspect body)
    - Check for debug information disclosure (X-Powered-By, etc.)

  A07 — Auth Failures:
    - Check cookie HttpOnly flag
    - Check cookie SameSite attribute
    - Check session ID entropy (if observable)
```

**Output:**
```json
{
  "task_id": "task-004",
  "status": "completed",
  "output": {
    "categories_checked": ["A01", "A02", "A05", "A07"],
    "findings": [
      {
        "id": "owasp-A05-server-disclosure",
        "category": "owasp",
        "severity": "low",
        "title": "Server version disclosed",
        "target": "https://example.com",
        "evidence": "Server: nginx/1.24.0",
        "remediation": "Remove or obfuscate the Server header",
        "cwe": "CWE-200"
      }
    ],
    "manual_review": ["A04", "A08", "A10"],
    "score": 85
  }
}
```

### compile-report

Aggregate findings from all scan phases into a single security report.

**Input:**
```json
{
  "task_id": "task-005",
  "action": "compile-report",
  "payload": {
    "phase_results": [
      {"phase": "headers", "findings": [...], "score": 72},
      {"phase": "csp", "findings": [...], "score": 55},
      {"phase": "dependencies", "findings": [...], "score": 60},
      {"phase": "owasp", "findings": [...], "score": 85}
    ]
  }
}
```

**Process:**
```
1. Merge all findings, deduplicate by ID
2. Calculate composite score:
   composite = (headers × 0.25) + (csp × 0.20) + (deps × 0.25) + (owasp × 0.30)
3. Sort findings by severity (critical → info)
4. Generate executive summary (using LLM if available)
5. Return complete report
```

**Output:**
```json
{
  "task_id": "task-005",
  "status": "completed",
  "output": {
    "security_score": 69,
    "grade": "Fair",
    "summary": "3 critical and 5 high-severity findings require immediate attention. Dependency vulnerabilities and missing CSP directives are the primary concerns.",
    "category_scores": {
      "headers": 72,
      "csp": 55,
      "dependencies": 60,
      "owasp": 85
    },
    "findings_count": {
      "critical": 3,
      "high": 5,
      "medium": 8,
      "low": 4,
      "info": 2
    },
    "findings": [...],
    "recommendations": [
      {
        "priority": 1,
        "action": "Update 3 vulnerable dependencies",
        "impact": "Fixes critical CVEs, +20 dependency score"
      },
      {
        "priority": 2,
        "action": "Remove unsafe-inline from CSP",
        "impact": "Mitigates XSS, +25 CSP score"
      }
    ]
  }
}
```

---

## Behavioral Fingerprint

### Manifest

```json
{
  "name": "security-scanner",
  "version": "1.0.0",
  "capabilities": ["file:read", "http:get", "llm:chat"],
  "actions": ["scan-headers", "scan-csp", "scan-dependencies", "scan-owasp", "compile-report"],
  "resource_limits": {
    "max_urls_per_scan": 50,
    "max_dependencies": 5000,
    "http_timeout_seconds": 30
  }
}
```

### Resource Constraints

- HTTP requests: max 50 concurrent, 30-second timeout each
- Dependency parsing: max 5000 packages per manifest
- LLM calls: only for report summary generation (optional)
- File reads: only manifest/lock files matching configured globs

---

## Implementation Notes

- HTTP header checks use HEAD requests where possible (faster, less
  data) but fall back to GET for servers that don't support HEAD
- CSP parsing must handle both header-based and meta-tag-based
  policies, and should merge them correctly per the CSP spec
- Dependency database lookups should be batched (not one HTTP request
  per package) — use bulk query APIs where available
- The compile-report LLM call is optional — if no LLM capability is
  available, the agent generates a template-based summary
- All HTTP requests made by this agent MUST include a
  `User-Agent: Weblisk-Security-Scanner/1.0` header
- The agent MUST NOT follow redirects to non-HTTPS URLs
- Scan results are deterministic for the same input — running the
  same scan twice should produce identical findings (modulo
  vulnerability database updates)

## Verification Checklist

- [ ] Agent exposes all 6 protocol endpoints: /health, /describe, /execute, /message, /services, /event
- [ ] Agent is passive — it reads files and fetches headers but does NOT send attack payloads, fuzz inputs, or perform active exploitation
- [ ] scan-headers uses HEAD requests with GET fallback; checks all standard security headers and returns per-header findings
- [ ] scan-csp detects `unsafe-inline`, `unsafe-eval`, wildcard `*` in script-src, missing `default-src`, `frame-ancestors`, and `base-uri`
- [ ] scan-dependencies auto-detects manifest files when `manifest_paths` is omitted; queries VulnDB and returns CVE, CVSS, and fix version per finding
- [ ] scan-owasp checks all automatable categories when `check_categories` is omitted; returns `manual_review` list for non-automatable categories
- [ ] compile-report uses weighted score formula: `(headers × 0.25) + (csp × 0.20) + (deps × 0.25) + (owasp × 0.30)` and deduplicates findings by ID
- [ ] All outbound HTTP requests include `User-Agent: Weblisk-Security-Scanner/1.0` header
- [ ] Agent does NOT follow redirects to non-HTTPS URLs
- [ ] Scan results are deterministic for the same input (modulo vulnerability database updates)
- [ ] HTTP requests are limited to max 50 concurrent with 30-second timeout; dependency parsing caps at 5000 packages per manifest
- [ ] LLM call for report summary is optional — agent generates a template-based summary when no LLM capability is available
- [ ] Each finding includes `id`, `category`, `severity`, `title`, `target`, `evidence`, and `remediation` fields
