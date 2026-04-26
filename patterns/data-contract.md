<!-- blueprint
type: pattern
name: data-contract
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/storage]
platform: any
tier: free
-->

# Data Contract Pattern

Structured format for defining, versioning, validating, and
discovering the input/output schemas that agents exchange. Every
agent declares its data contracts — what it accepts and what it
produces — so that consumers can validate compatibility at deploy
time, not runtime.

## Overview

The Weblisk protocol defines `IOSpec` as `{name, type, description}`
— a loose description of what an agent accepts. This is insufficient
for a platform where agents must compose reliably. This pattern
replaces loose descriptions with machine-checkable schemas:

1. **Schema declaration** — structured input/output definitions
2. **Versioning** — backward/forward compatibility rules
3. **Validation** — envelope format with schema enforcement
4. **Contract testing** — producer/consumer compatibility checks
5. **Discovery** — contracts are inspectable at runtime

---

## Contract Declaration

Every agent declares its input and output contracts in its blueprint:

```yaml
contracts:
  inputs:
    <contract-name>:
      version: <semver>
      description: <one-line>
      schema:
        <field>:
          type: <type>
          required: <bool>
          description: <one-line>
          constraints: <rules>

  outputs:
    <contract-name>:
      version: <semver>
      description: <one-line>
      schema:
        <field>:
          type: <type>
          required: <bool>
          description: <one-line>
```

### Schema Field Types

Uses the same type system as `patterns/storage`:

| Type | Description |
|------|-------------|
| `string` | UTF-8 text |
| `text` | Long-form text |
| `int` | 64-bit signed integer |
| `float` | 64-bit floating point |
| `boolean` | True/false |
| `timestamp` | Unix epoch seconds (int64) |
| `json` | Arbitrary JSON object |
| `[]<type>` | Array of type |
| `enum(<values>)` | Enumerated values |
| `uuid` | UUID string |
| `map` | Key-value map |

### Constraint Syntax

Inline constraints for schema fields:

| Constraint | Applies To | Example |
|------------|-----------|---------|
| `min:<n>` | int, float | `min:0` |
| `max:<n>` | int, float | `max:100` |
| `min_length:<n>` | string | `min_length:1` |
| `max_length:<n>` | string | `max_length:255` |
| `pattern:<regex>` | string | `pattern:^[a-z]+$` |
| `min_items:<n>` | array | `min_items:1` |
| `max_items:<n>` | array | `max_items:100` |
| `not_empty` | string, array | field must not be empty |

### Example

```yaml
contracts:
  inputs:
    scan_request:
      version: 1.0.0
      description: Files to scan for SEO issues
      schema:
        target_files:
          type: "[]string"
          required: true
          description: File paths or URLs to scan
          constraints: "min_items:1"
        scan_depth:
          type: enum(shallow,full)
          required: false
          description: How deeply to analyze each file
        max_issues:
          type: int
          required: false
          description: Cap on issues returned per file
          constraints: "min:1, max:1000"

  outputs:
    scan_result:
      version: 1.0.0
      description: SEO scan findings
      schema:
        files_scanned:
          type: int
          required: true
          description: Number of files analyzed
        findings:
          type: "[]json"
          required: true
          description: Array of Finding objects
        score:
          type: float
          required: true
          description: Composite score 0-100
          constraints: "min:0, max:100"
```

---

## Message Envelope

All inter-agent data exchange uses a standard envelope that
references the contract:

```json
{
  "contract": "<contract-name>",
  "version": "<semver>",
  "payload": { ... }
}
```

### Envelope Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| contract | string | yes | Contract name from declaration |
| version | string | yes | Schema version of this payload |
| payload | object | yes | The actual data conforming to the schema |

### Envelope Validation

When an agent receives a message with a contract envelope:

```
1. Look up contract by name in agent's declared inputs
2. If contract unknown → reject with DATA_CONTRACT_UNKNOWN
3. Check version compatibility (see Versioning)
4. Validate payload against schema:
   a. Check all required fields are present
   b. Check field types match declarations
   c. Check constraints are satisfied
5. If validation fails → reject with DATA_CONTRACT_VIOLATION
6. Pass validated payload to handler
```

---

## Versioning

Contracts follow semantic versioning with compatibility rules:

### Version Rules

| Change | Version Bump | Compatibility |
|--------|-------------|---------------|
| Add optional field | MINOR | Backward compatible |
| Add new constraint to optional field | MINOR | Backward compatible |
| Relax a constraint | MINOR | Backward compatible |
| Remove optional field | MAJOR | Breaking |
| Add required field | MAJOR | Breaking |
| Change field type | MAJOR | Breaking |
| Tighten a constraint | MAJOR | Breaking |
| Rename a field | MAJOR | Breaking |

### Compatibility Check

A consumer at version X can accept a producer at version Y if:

```
Major(X) == Major(Y) AND Minor(Y) >= Minor(X)
```

The consumer declares the minimum version it supports. The producer
advertises its current version. If the major versions don't match,
the exchange is rejected.

### Version Negotiation

During workflow phase dispatch, the engine checks contract
compatibility:

```
1. Producer declares output contract version
2. Consumer declares expected input contract version
3. If compatible → proceed
4. If incompatible → fail phase with DATA_CONTRACT_VERSION_MISMATCH
```

---

## Contract Testing

Contracts are testable at deploy time without running the agents:

### Static Validation

```
For each agent in the deployment:
  For each workflow that references this agent:
    For each phase that dispatches to this agent:
      1. Resolve the phase's input references (structurally)
      2. Match resolved structure against agent's input contract
      3. Match agent's output contract against downstream consumers
      4. Report mismatches as deployment errors
```

### Contract Compatibility Matrix

For a deployment with agents A and B where A produces output
consumed by B:

| Check | Validates |
|-------|-----------|
| A.outputs.X exists | Producer declares the contract |
| B.inputs.Y exists | Consumer declares the contract |
| A.outputs.X.version compatible with B.inputs.Y.version | Versions align |
| A.outputs.X.schema covers B.inputs.Y.schema required fields | Required fields present |
| Field types match | Type safety |

---

## Runtime Discovery

Contracts are discoverable via the agent's describe endpoint.
The manifest includes contract declarations:

```json
{
  "name": "seo-analyzer",
  "contracts": {
    "inputs": {
      "scan_request": {
        "version": "1.0.0",
        "schema": { ... }
      }
    },
    "outputs": {
      "scan_result": {
        "version": "1.0.0",
        "schema": { ... }
      }
    }
  }
}
```

This extends the existing `AgentManifest` with structured contract
information. The `inputs` and `outputs` IOSpec fields remain for
human-readable descriptions; the `contracts` field adds machine-
checkable schemas.

---

## Standard Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| DATA_CONTRACT_UNKNOWN | 400 | Referenced contract not declared by agent |
| DATA_CONTRACT_VIOLATION | 422 | Payload fails schema validation |
| DATA_CONTRACT_VERSION_MISMATCH | 409 | Incompatible contract versions |

Error responses MUST use the standard `ErrorResponse` format with
`detail` containing the specific validation failures:

```json
{
  "error": "Data contract violation: scan_request v1.0.0",
  "code": "DATA_CONTRACT_VIOLATION",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "contract": "scan_request",
    "version": "1.0.0",
    "violations": [
      {"field": "target_files", "rule": "required", "message": "field is required"},
      {"field": "max_issues", "rule": "min:1", "message": "value 0 is below minimum 1"}
    ]
  }
}
```

---

## Implementation Notes

- Contract validation happens at the receiving agent, not the sender.
  The sender constructs the envelope; the receiver validates it.
- Validation MUST happen before any processing logic executes.
- When an agent does not declare contracts (legacy agents), the
  envelope validation step is skipped — raw payloads are accepted.
  This preserves backward compatibility.
- Contract schemas are intentionally simpler than JSON Schema. They
  use the same type system as `patterns/storage` for consistency.
- The `contracts` field in the manifest is optional. Agents that
  declare it get schema enforcement. Agents that don't continue to
  work as before.

---

## Verification Checklist

- [ ] Agent declares input and output contracts in blueprint
- [ ] Contracts include version, description, and schema
- [ ] Schema fields have type, required flag, and description
- [ ] Constraint syntax validates correctly for all supported types
- [ ] Message envelope includes contract name and version
- [ ] Unknown contracts are rejected with DATA_CONTRACT_UNKNOWN
- [ ] Schema violations are rejected with DATA_CONTRACT_VIOLATION
- [ ] Version compatibility check follows semver rules
- [ ] Incompatible versions reject with DATA_CONTRACT_VERSION_MISMATCH
- [ ] Error responses include specific validation failure details
- [ ] Contracts are discoverable via describe endpoint
- [ ] Static contract testing can validate deployment compatibility
- [ ] Legacy agents without contracts continue to function
