<!-- blueprint
type: agent
name: uptime-checker
version: 1.1.0
kind: work
port: 9730
extends: [patterns/observability, patterns/security]
requires: [protocol/spec, protocol/types, architecture/agent, architecture/domain]
platform: any
tier: free
domain: health
-->

# Uptime Checker Agent

Work agent that checks endpoint availability, response time, HTTP
status codes, TLS certificate status, and DNS resolution. Dispatched
by the health domain controller — never invoked directly. Designed to
be lightweight enough to run on a 5-minute schedule.

## Capabilities

```json
{
  "capabilities": [
    {"name": "net:http", "resources": ["*"]},
    {"name": "net:dns", "resources": ["*"]},
    {"name": "net:tls", "resources": ["*"]},
    {"name": "agent:message", "resources": []}
  ],
  "inputs": [
    {"name": "endpoints", "type": "endpoint_config[]", "description": "Endpoints to check with thresholds"}
  ],
  "outputs": [
    {"name": "results", "type": "json", "description": "Availability and TLS status per endpoint"}
  ],
  "collaborators": []
}
```

## HandleMessage Actions

| Action | Payload | Response |
|--------|---------|----------|
| `check` | `{endpoints: EndpointConfig[]}` | `{results: UptimeResult[]}` |
| `check_tls` | `{host: string, port: number}` | `{tls: TlsResult}` |
| `check_dns` | `{hostname: string}` | `{dns: DnsResult}` |

## Execute Workflow

```
1. RECEIVE endpoint list from health domain controller
   Input: {endpoints: [{url, timeout_ms, expected_status, thresholds}]}

2. FOR EACH endpoint (parallel where possible):

   a. DNS Resolution
      → Resolve hostname to IP addresses
      → Record resolution time in ms
      → Flag if resolution fails or takes > 500ms

   b. TLS Check (if HTTPS):
      → Connect and validate certificate chain
      → Record certificate expiry date
      → Check for weak ciphers or protocol versions
      → Grade: A (> 30d), B (14-30d), C (7-14d), F (< 7d or expired)

   c. HTTP Request
      → Send GET request with configured timeout
      → Record: status code, TTFB, total response time, response size
      → Follow redirects (record redirect chain)
      → Validate status matches expected_status

   d. Threshold Evaluation
      → Compare response time against warning/critical thresholds
      → Compare TLS expiry against warning/critical days
      → Set endpoint status: healthy | degraded | down

3. BUILD UptimeResult per endpoint

4. RETURN results to health domain controller
```

## Types

### UptimeResult

```json
{
  "url": "https://example.com",
  "status": "healthy",
  "checked_at": "2025-01-15T10:30:00Z",
  "dns": {
    "resolved": true,
    "resolution_ms": 12,
    "addresses": ["93.184.216.34"]
  },
  "tls": {
    "valid": true,
    "issuer": "Let's Encrypt",
    "expiry": "2025-04-15T00:00:00Z",
    "expiry_days": 90,
    "grade": "A",
    "protocol": "TLSv1.3",
    "cipher": "TLS_AES_256_GCM_SHA384"
  },
  "http": {
    "status_code": 200,
    "status_match": true,
    "ttfb_ms": 85,
    "response_time_ms": 142,
    "response_size_bytes": 24576,
    "redirects": []
  },
  "findings": []
}
```

### DnsResult

```json
{
  "hostname": "example.com",
  "resolved": true,
  "resolution_ms": 12,
  "addresses": ["93.184.216.34"],
  "nameservers": ["ns1.example.com", "ns2.example.com"]
}
```

### TlsResult

```json
{
  "valid": true,
  "issuer": "Let's Encrypt",
  "subject": "example.com",
  "san": ["example.com", "www.example.com"],
  "expiry": "2025-04-15T00:00:00Z",
  "expiry_days": 90,
  "grade": "A",
  "protocol": "TLSv1.3",
  "cipher": "TLS_AES_256_GCM_SHA384",
  "chain_valid": true,
  "chain_length": 3
}
```

## Threshold Rules

| Check | Warning | Critical |
|-------|---------|----------|
| Response time | > 2000ms | > 5000ms |
| DNS resolution | > 500ms | Failure |
| TLS expiry | < 14 days | < 7 days |
| TLS protocol | TLSv1.2 | TLSv1.1 or lower |
| Status code | Non-matching | Connection refused |

## Verification Checklist

- [ ] Agent registers with kind: work and domain: health
- [ ] Uses net:http, net:dns, net:tls capabilities (no file system access)
- [ ] Checks DNS resolution time and records addresses
- [ ] Validates full TLS certificate chain
- [ ] Grades TLS status (A/B/C/F based on expiry)
- [ ] Records HTTP status, TTFB, and total response time
- [ ] Follows and records redirect chains
- [ ] Evaluates thresholds to set endpoint status
- [ ] Runs within configured timeout per endpoint
- [ ] Returns UptimeResult per endpoint with all required fields
