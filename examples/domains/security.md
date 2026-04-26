<!-- blueprint
type: domain
kind: domain
name: security
version: 1.1.0
port: 9703
extends: [patterns/domain-controller, patterns/observability, patterns/storage, patterns/workflow, patterns/data-contract, patterns/governance, patterns/security]
requires: [protocol/spec, protocol/identity, protocol/types, architecture/domain, architecture/lifecycle]
platform: any
tier: free
-->

# Security Domain Controller

The security domain controller owns the web application security
business function. It coordinates passive security scanning, OWASP
Top 10 analysis, dependency vulnerability auditing, CSP validation,
and security header checks across all monitored sites and applications.

This domain does NOT perform security scans itself. It directs the
[security-scanner](../agents/security-scanner.md) agent, which
performs all scan operations and returns structured findings.

## Domain Manifest

```json
{
  "name": "security",
  "type": "domain",
  "version": "1.0.0",
  "description": "Web application security — OWASP, CSP, headers, dependency auditing",
  "url": "http://localhost:9703",
  "public_key": "<hex Ed25519 public key>",
  "capabilities": [
    {"name": "agent:message", "resources": []},
    {"name": "workflow:execute", "resources": []}
  ],
  "inputs": [
    {"name": "target_urls", "type": "url_list", "description": "URLs to scan"},
    {"name": "dependency_files", "type": "file_list", "description": "Package manifests to audit"}
  ],
  "outputs": [
    {"name": "domain_report", "type": "json", "description": "Aggregated security report with scored findings"}
  ],
  "collaborators": [],
  "approval": "required",
  "required_agents": ["security-scanner"],
  "workflows": ["security-audit", "security-headers-check", "dependency-audit"]
}
```

## Required Agents

| Agent | Purpose | Dispatched For |
|-------|---------|----------------|
| security-scanner | HTTP header analysis, CSP parsing, dependency CVE lookup, OWASP static checks, behavioral fingerprint | All scan phases |

## Workflows

### security-audit

Full security audit. Runs all scan types, aggregates into a scored
report with prioritized findings and remediation recommendations.

Trigger: `task.action = "audit"`

```yaml
workflow: security-audit
phases:
  - name: headers
    agent: security-scanner
    action: scan-headers
    input:
      urls: $task.payload.urls
    output: header_results
    timeout: 60

  - name: csp
    agent: security-scanner
    action: scan-csp
    input:
      urls: $task.payload.urls
    output: csp_results
    timeout: 60

  - name: dependencies
    agent: security-scanner
    action: scan-dependencies
    input:
      files: $task.payload.dependency_files
    output: dep_results
    timeout: 120

  - name: owasp
    agent: security-scanner
    action: scan-owasp
    input:
      urls: $task.payload.urls
    output: owasp_results
    timeout: 180

  - name: aggregate
    agent: self
    action: aggregate_results
    input:
      headers: $phases.headers.output
      csp: $phases.csp.output
      dependencies: $phases.dependencies.output
      owasp: $phases.owasp.output
    output: aggregated
    depends_on: [headers, csp, dependencies, owasp]

  - name: score
    agent: self
    action: calculate_security_score
    input:
      aggregated: $phases.aggregate.output
    output: scored
    depends_on: [aggregate]

  - name: recommend
    agent: self
    action: generate_recommendations
    input:
      scored: $phases.score.output
    output: recommendations
    depends_on: [score]

  - name: observe
    agent: self
    action: record_observations
    input:
      scored: $phases.score.output
      recommendations: $phases.recommend.output
    output: observations
    depends_on: [recommend]

  - name: report
    agent: self
    action: compile_report
    input:
      scored: $phases.score.output
      recommendations: $phases.recommend.output
      observations: $phases.observe.output
    output: domain_report
    depends_on: [observe]
```

Phase dependency: headers + csp + dependencies + owasp (parallel) → aggregate → score → recommend → observe → report

### security-headers-check

Quick headers-only scan. Lightweight check suitable for frequent
scheduling.

Trigger: `task.action = "check-headers"`

```yaml
workflow: security-headers-check
phases:
  - name: headers
    agent: security-scanner
    action: scan-headers
    input:
      urls: $task.payload.urls
    output: header_results
    timeout: 60

  - name: evaluate
    agent: self
    action: evaluate_headers
    input:
      results: $phases.headers.output
    output: evaluation
    depends_on: [headers]
```

### dependency-audit

Dependency-only vulnerability check. Scans package manifests against
vulnerability databases.

Trigger: `task.action = "audit-dependencies"`

```yaml
workflow: dependency-audit
phases:
  - name: scan
    agent: security-scanner
    action: scan-dependencies
    input:
      files: $task.payload.dependency_files
    output: dep_results
    timeout: 120

  - name: evaluate
    agent: self
    action: evaluate_dependencies
    input:
      results: $phases.scan.output
    output: evaluation
    depends_on: [scan]
```

## Domain HandleMessage Actions

| Action | Source | Description |
|--------|--------|-------------|
| execute_workflow | Orchestrator | Primary entry point via POST /v1/execute |
| aggregate_results | Internal | Combine all scan type outputs |
| calculate_security_score | Internal | Weighted composite from scoring formula |
| generate_recommendations | Internal | Prioritize findings into remediation steps |
| record_observations | Internal | Feed results into lifecycle as observations |
| evaluate_headers | Internal | Quick header compliance check |
| evaluate_dependencies | Internal | Dependency vulnerability assessment |
| compile_report | Internal | Build SecurityDomainReport |
| get_status | Orchestrator/Admin | Domain health and agent availability |
| get_workflows | Orchestrator/Admin | Available workflow definitions |
| workflow_history | Admin | Recent workflow executions with results |

## Scoring

| Category | Weight | Source |
|----------|--------|--------|
| HTTP Headers | 25% | scan-headers |
| CSP | 20% | scan-csp |
| Dependencies | 25% | scan-dependencies |
| OWASP | 30% | scan-owasp |

Security score = (headers × 0.25) + (csp × 0.20) + (deps × 0.25) + (owasp × 0.30), clamped 0–100.

### Score Ranges

| Range | Grade | Description |
|-------|-------|-------------|
| 90–100 | Excellent | No critical or high findings |
| 75–89 | Good | Minor issues, no critical findings |
| 50–74 | Fair | Significant issues requiring attention |
| 25–49 | Poor | Critical issues present |
| 0–24 | Critical | Multiple critical vulnerabilities |

## HTTP Headers Checks

| Header | Expected | Severity if Missing |
|--------|----------|-------------------|
| Strict-Transport-Security | max-age≥31536000; includeSubDomains | High |
| X-Content-Type-Options | nosniff | Medium |
| X-Frame-Options | DENY or SAMEORIGIN | Medium |
| Content-Security-Policy | Present, no unsafe-inline in script-src | High |
| Referrer-Policy | strict-origin-when-cross-origin or stricter | Low |
| Permissions-Policy | Present | Low |
| Cross-Origin-Opener-Policy | same-origin | Medium |
| Cross-Origin-Resource-Policy | same-origin or same-site | Medium |

## CSP Validation Rules

| Rule | Severity |
|------|----------|
| No `unsafe-inline` in `script-src` | Critical |
| No `unsafe-eval` in `script-src` | Critical |
| No wildcard `*` in `script-src` | High |
| `default-src` is set | High |
| No `data:` in `script-src` | High |
| `frame-ancestors` is set | Medium |
| `base-uri` is restricted | Medium |
| `form-action` is restricted | Low |

## Dependency Audit

Supported package manifest formats:

| File | Ecosystem |
|------|-----------|
| package.json / package-lock.json | npm |
| go.mod / go.sum | Go |
| requirements.txt / Pipfile.lock | Python |
| Cargo.toml / Cargo.lock | Rust |

Vulnerability lookup uses the VulnDB abstract interface defined in
the security-scanner agent (local DB, OSV, GitHub Advisory, custom).

## OWASP Top 10 Checks

| ID | Category | Check Type |
|----|----------|------------|
| A01 | Broken Access Control | Static analysis — missing auth headers, open redirects |
| A02 | Cryptographic Failures | TLS version, cipher strength, mixed content |
| A03 | Injection | Input handling patterns, parameterized queries |
| A05 | Security Misconfiguration | Headers, default credentials, error disclosure |
| A06 | Vulnerable Components | Dependency audit cross-reference |
| A07 | Auth Failures | Session handling, password policy, brute force protection |
| A09 | Logging Failures | Security event logging presence |

A04 (Insecure Design), A08 (Software Integrity), A10 (SSRF) require
manual review or runtime analysis — flagged as "manual review required."

## Aggregation Rules

1. Merge findings: deduplicate by (check_type + target + element)
2. Sort by severity (critical → high → medium → low → info)
3. Group by OWASP category where applicable
4. Resolve conflicts: when the same issue is found by multiple scan
   types (e.g., headers scan and OWASP scan both flag missing HSTS),
   keep the more specific finding and merge context from both
5. Dependency findings include CVE IDs and CVSS scores when available

## Observability

| Metric | Type | Description |
|--------|------|-------------|
| domain_workflow_duration_seconds | histogram | Time to complete a workflow |
| domain_workflow_total | counter | Workflow executions by name and status |
| domain_agent_dispatch_total | counter | Dispatches by target agent and action |
| domain_agent_dispatch_duration_seconds | histogram | Time waiting for agent response |
| domain_security_score | gauge | Latest security score (0–100) |
| domain_findings_total | counter | Findings by category and severity |
| domain_vulnerabilities_total | counter | Known vulnerabilities by ecosystem and severity |

## Error Handling

| Error | Handling |
|-------|---------|
| Agent unavailable | Domain status → degraded. Retry dispatch up to 3 times. If all fail, workflow fails with partial results. |
| Agent timeout | Cancel timed-out scan phase. Continue with available results. Mark missing categories in report. |
| VulnDB unavailable | Fall back to local database. Flag results as potentially incomplete. |
| Target unreachable | Mark URL as unreachable in findings. Continue scanning other targets. |
| All agents unavailable | Domain status → offline. Reject new workflows with 503. |

## Verification Checklist

- [ ] Domain registers with orchestrator and receives WLT token
- [ ] Domain status reflects agent availability (online/degraded/offline)
- [ ] security-audit workflow executes all 4 scan phases in parallel
- [ ] Scoring formula produces 0–100 clamped result matching weight table
- [ ] security-headers-check workflow runs independently of full audit
- [ ] dependency-audit workflow handles all 4 supported manifest formats
- [ ] OWASP checks map to correct category IDs
- [ ] Conflict resolution deduplicates cross-scan findings
- [ ] Observations feed into lifecycle store
- [ ] Workflow history is queryable via workflow_history action
- [ ] Metrics emit for all workflow executions and agent dispatches
- [ ] Partial results returned when individual scan phases fail

Port: 9703
