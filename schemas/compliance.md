# Compliance Schema

Defines the compliance framework for all Weblisk blueprints. Every
blueprint is assigned a compliance level based on automated validation.
Non-compliant blueprints are flagged, restricted, or rejected depending
on severity. This is the enforcement layer that ensures no agent,
domain, protocol, or pattern operates outside the framework's security
and operational boundaries.

---

## Compliance Levels

Every blueprint receives a compliance level after validation. The level
determines what the blueprint is allowed to do in the framework.

```yaml
compliance_levels:
  certified:
    description: >
      Fully compliant. All required sections present, all fields valid,
      all security declarations complete, all dependency contracts resolved.
      Blueprint may be published, consumed by others, and listed in the
      marketplace.
    permissions:
      - register with orchestrator
      - publish to marketplace
      - consumed by other blueprints as dependency
      - inter-agent messaging (full)
      - event publishing and subscribing
      - storage access (declared tables)
      - scheduled execution
    badge: "✅ Certified"

  compliant:
    description: >
      Structurally valid. All required sections present, all critical
      fields valid. Minor issues exist (missing optional sections,
      incomplete test fixtures, missing examples). Blueprint may operate
      but cannot be published to the marketplace until issues are resolved.
    permissions:
      - register with orchestrator
      - inter-agent messaging (full)
      - event publishing and subscribing
      - storage access (declared tables)
      - scheduled execution
    restrictions:
      - cannot publish to marketplace
      - flagged in service directory as "compliant (not certified)"
    badge: "⚠️ Compliant"

  restricted:
    description: >
      Partially valid. Required sections present but with validation
      errors — missing fields, invalid version ranges, incomplete
      security declarations, or unresolved dependency references.
      Blueprint may operate in isolation but with restricted capabilities.
    permissions:
      - register with orchestrator
      - storage access (declared tables only)
    restrictions:
      - cannot publish to marketplace
      - cannot be consumed by other blueprints as dependency
      - inter-agent messaging limited to declared collaborators only
      - event publishing limited to own namespace only
      - event subscribing limited to system.* events only
      - flagged in service directory as "restricted"
      - health endpoint must report compliance status
    badge: "🟡 Restricted"

  non_compliant:
    description: >
      Failed critical validation. Missing required sections, invalid
      frontmatter, missing security declarations, or undeclared
      capabilities. Blueprint may operate in sandbox mode only —
      fully isolated from all other agents and system events.
    permissions:
      - register with orchestrator (sandbox mode)
      - storage access (own tables only, sandboxed database)
    restrictions:
      - cannot publish to marketplace
      - cannot be consumed by other blueprints
      - no inter-agent messaging
      - no event publishing or subscribing
      - no access to shared storage
      - sandboxed network — cannot reach other agents
      - flagged in service directory as "non-compliant"
      - health endpoint reports "non-compliant" status
    badge: "🔴 Non-Compliant"

  rejected:
    description: >
      Failed security validation. Missing security section, undeclared
      capabilities in use, missing access control, or attempted access
      beyond declared boundaries. Blueprint is rejected at registration.
      It cannot operate in any mode.
    permissions: []
    restrictions:
      - registration rejected by orchestrator
      - cannot operate in any mode
      - violation logged to system audit trail
    badge: "⛔ Rejected"
```

---

## Validation Pipeline

Every blueprint passes through this validation pipeline. Steps execute
in order. Failure at any step records the error and may terminate early
(for security violations) or continue (for structural issues) to collect
all violations in a single report.

### Phase 1 — Structural Validation

Validates the blueprint's structure against `common.md` and the
type-specific schema.

```yaml
structural_checks:
  - id: S001
    name: frontmatter-present
    description: Blueprint starts with <!-- blueprint ... --> comment
    severity: critical
    fails_to: non_compliant

  - id: S002
    name: frontmatter-fields
    description: All required fields present and correctly typed
    severity: critical
    fails_to: non_compliant

  - id: S003
    name: type-valid
    description: Type field is in the type registry
    severity: critical
    fails_to: non_compliant

  - id: S004
    name: name-matches-file
    description: Name field matches filename (without .md)
    severity: major
    fails_to: restricted

  - id: S005
    name: version-valid
    description: Version is valid semver
    severity: major
    fails_to: restricted

  - id: S006
    name: required-sections-present
    description: All required sections for this type exist
    severity: critical
    fails_to: non_compliant

  - id: S007
    name: section-ordering
    description: Sections appear in schema-defined order
    severity: minor
    fails_to: compliant

  - id: S008
    name: title-and-overview
    description: Level-1 title and Overview section present
    severity: major
    fails_to: restricted

  - id: S009
    name: yaml-blocks-valid
    description: All YAML code blocks parse without errors
    severity: critical
    fails_to: non_compliant

  - id: S010
    name: no-unknown-fields
    description: No unrecognized fields in frontmatter
    severity: minor
    fails_to: compliant
```

### Phase 2 — Dependency Validation

Validates all dependency declarations against the repository.

```yaml
dependency_checks:
  - id: D001
    name: dependencies-section-present
    description: Dependencies section exists if requires/extends declared
    severity: critical
    fails_to: non_compliant

  - id: D002
    name: requires-resolved
    description: Every requires entry references an existing blueprint
    severity: critical
    fails_to: non_compliant

  - id: D003
    name: extends-are-patterns
    description: Every extends entry references a pattern blueprint
    severity: major
    fails_to: restricted

  - id: D004
    name: version-ranges-valid
    description: All version ranges are valid semver range expressions
    severity: major
    fails_to: restricted

  - id: D005
    name: bindings-present
    description: Every dependency has at least one binding category
    severity: major
    fails_to: restricted

  - id: D006
    name: bindings-resolve
    description: All binding references exist in the dependency blueprint
    severity: major
    fails_to: restricted

  - id: D007
    name: on-change-complete
    description: All three on_change levels declared for every dependency
    severity: major
    fails_to: restricted

  - id: D008
    name: on-change-valid
    description: All on_change actions are from the allowed actions list
    severity: minor
    fails_to: compliant

  - id: D009
    name: depends-on-present
    description: depends_on declared for agent/domain types
    severity: major
    fails_to: restricted

  - id: D010
    name: no-circular-deps
    description: No circular dependency chains exist
    severity: critical
    fails_to: non_compliant
```

### Phase 3 — Type Validation

Validates all type definitions against the type system rules.

```yaml
type_checks:
  - id: T001
    name: types-yaml-format
    description: Types declared in YAML format (not markdown tables)
    severity: major
    fails_to: restricted

  - id: T002
    name: types-pascal-case
    description: All type names are PascalCase
    severity: minor
    fails_to: compliant

  - id: T003
    name: fields-have-type
    description: Every field declares a scalar type
    severity: critical
    fails_to: non_compliant

  - id: T004
    name: fields-have-description
    description: Every field has a description
    severity: minor
    fails_to: compliant

  - id: T005
    name: references-resolve
    description: All references point to valid TypeName.field_name
    severity: major
    fails_to: restricted

  - id: T006
    name: constraints-valid
    description: All constraints reference valid fields
    severity: major
    fails_to: restricted

  - id: T007
    name: enum-matches-type
    description: Enum values match the declared field type
    severity: major
    fails_to: restricted

  - id: T008
    name: required-when-valid
    description: required_when expressions reference fields in same type
    severity: major
    fails_to: restricted

  - id: T009
    name: exclusive-with-valid
    description: exclusive_with references a field in the same type
    severity: major
    fails_to: restricted
```

### Phase 4 — Security Validation

Validates security declarations. This is the most critical phase —
security failures can result in immediate rejection.

```yaml
security_checks:
  - id: SEC001
    name: security-section-present
    description: Security section exists (required for agent and domain types)
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC002
    name: permissions-declared
    description: All capabilities/permissions explicitly declared
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC003
    name: access-control-defined
    description: Access control rules defined for all actions
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC004
    name: data-sensitivity-classified
    description: All data types classified by sensitivity
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: SEC005
    name: no-undeclared-capabilities
    description: >
      Blueprint does not reference capabilities beyond what is declared
      in the security.permissions section
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC006
    name: no-wildcard-resources
    description: >
      Permissions do not use wildcard resources unless explicitly justified.
      Each wildcard must have a justification comment.
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: SEC007
    name: storage-access-scoped
    description: >
      Storage permissions are limited to tables declared in the Storage section.
      No cross-agent storage access without explicit federation contract.
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC008
    name: event-namespace-owned
    description: >
      Published events use namespaces owned by this blueprint only.
      No publishing to another agent's namespace.
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC009
    name: constraints-section-present
    description: Constraints section exists with blast radius and forbidden actions
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: SEC010
    name: blast-radius-bounded
    description: >
      Blast radius constraints prevent the agent from affecting data,
      storage, events, or operations owned by other agents
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]

  - id: SEC011
    name: resource-limits-declared
    description: Resource limits (memory, rows, connections, rate) declared
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: SEC012
    name: unauthenticated-access-blocked
    description: >
      Access control explicitly blocks unauthenticated callers.
      No action is available without a valid auth token.
    severity: critical
    fails_to: rejected
    applies_to: [agent, domain]
```

### Phase 5 — Completeness Validation

Validates that the blueprint is complete enough for implementation.

```yaml
completeness_checks:
  - id: C001
    name: verification-checklist-present
    description: Verification Checklist section exists
    severity: major
    fails_to: restricted

  - id: C002
    name: verification-minimum-items
    description: Minimum checklist items met (10 for agent/domain, 5 for others)
    severity: minor
    fails_to: compliant

  - id: C003
    name: implementation-notes-present
    description: Implementation Notes section exists
    severity: major
    fails_to: restricted

  - id: C004
    name: test-fixtures-present
    description: Test Fixtures section exists (agent and domain types)
    severity: minor
    fails_to: compliant
    applies_to: [agent, domain]

  - id: C005
    name: test-fixtures-coverage
    description: Test fixtures cover happy path, error cases, and edge cases
    severity: minor
    fails_to: compliant
    applies_to: [agent, domain]

  - id: C006
    name: error-handling-complete
    description: Error Handling section declares permanent and transient errors
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: C007
    name: observability-declared
    description: Observability section declares logs, metrics, and alerts
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: C008
    name: lifecycle-complete
    description: Lifecycle section declares startup and shutdown sequences
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: C009
    name: actions-documented
    description: Every action has input, processing, output, errors, side effects
    severity: major
    fails_to: restricted
    applies_to: [agent, domain]

  - id: C010
    name: one-shot-implementable
    description: >
      Blueprint is detailed enough that a developer or AI model can build
      a compliant implementation without follow-up questions
    severity: minor
    fails_to: compliant
```

---

## Compliance Report

The validation pipeline produces a compliance report for every blueprint.

```yaml
compliance_report:
  blueprint: <type/name>
  version: <semver>
  validated_at: <ISO8601>
  schema_version: <schema-system-version>
  level: certified|compliant|restricted|non_compliant|rejected
  checks:
    passed: <count>
    failed: <count>
    skipped: <count>
    total: <count>
  violations:
    - check_id: <id>
      name: <check-name>
      severity: critical|major|minor
      message: <human-readable description>
      location: <file:line or section reference>
      fix_hint: <suggested remediation>
  security_summary:
    capabilities_declared: [list]
    storage_tables: [list]
    event_namespaces: [list]
    access_control: present|missing
    blast_radius: bounded|unbounded
  recommendation: >
    Human-readable summary of what needs to change to reach the
    next compliance level.
```

---

## Enforcement Points

### Registration (Orchestrator)

When an agent or domain controller registers with the orchestrator:

1. Orchestrator retrieves the blueprint from the repository
2. Orchestrator runs the full validation pipeline
3. Compliance level is computed
4. Registration decision:

```yaml
registration_enforcement:
  certified:
    action: register
    mode: full
    service_directory_flag: "certified"

  compliant:
    action: register
    mode: full
    service_directory_flag: "compliant"

  restricted:
    action: register
    mode: restricted
    service_directory_flag: "restricted"
    runtime_restrictions:
      - messaging limited to declared collaborators
      - event publishing limited to own namespace
      - event subscribing limited to system.* only
      - cannot be listed as dependency by other blueprints

  non_compliant:
    action: register
    mode: sandbox
    service_directory_flag: "non-compliant"
    runtime_restrictions:
      - sandboxed storage (separate database)
      - no inter-agent messaging
      - no event publishing or subscribing
      - isolated network (cannot reach other agents)
      - health endpoint must report "non-compliant"

  rejected:
    action: reject
    response:
      error: "BLUEPRINT_REJECTED"
      message: "Blueprint failed security validation"
      violations: [list of SEC-prefixed check failures]
    audit: Rejection logged to system audit trail
```

### Runtime Monitoring

Running agents are periodically audited for compliance drift:

```yaml
runtime_monitoring:
  frequency: every health check cycle
  checks:
    - Agent health endpoint returns declared structure
    - Published events stay within declared namespaces
    - Storage writes stay within declared tables
    - Capabilities in use match declared capabilities
    - Resource usage within declared limits
  on_violation:
    first_occurrence:
      action: log warning
      notification: alerting agent
    repeated:
      action: escalate to restricted mode
      notification: alerting agent + operator
    critical:
      action: immediate isolation (sandbox mode)
      notification: alerting agent + operator + incident-response
```

### Marketplace Publishing

Blueprints submitted to the marketplace require `certified` level:

```yaml
marketplace_requirements:
  minimum_level: certified
  additional_checks:
    - All optional sections recommended by type schema are present
    - Test fixtures cover >= 80% of declared actions
    - No security wildcards without justification
    - Documentation quality assessed (Overview is meaningful, not placeholder)
    - Verified against latest schema version
  review_process:
    automated: Full validation pipeline
    manual: Security review for agents with elevated capabilities
```

---

## Security Boundaries

### Capability Model

The Weblisk capability model is **deny-by-default**. An agent has zero
capabilities unless explicitly declared in its blueprint's Security section.

```yaml
capability_model:
  principle: deny-by-default
  enforcement: orchestrator + runtime monitor

  capability_categories:
    - name: agent:message
      description: Send direct messages to other agents
      resources: [agent names or "*" with justification]

    - name: database:read
      description: Read from storage tables
      resources: [table names — must match Storage section]

    - name: database:write
      description: Write to storage tables
      resources: [table names — must match Storage section]

    - name: event:publish
      description: Publish events to topics
      resources: [namespace patterns — must be owned by this agent]

    - name: event:subscribe
      description: Subscribe to event topics
      resources: [topic patterns — must be declared in Dependencies]

    - name: realtime:publish
      description: Push to real-time channels
      resources: [channel patterns]

    - name: http:outbound
      description: Make outbound HTTP requests
      resources: [URL patterns or domains]

    - name: file:read
      description: Read files from workspace
      resources: [path patterns]

    - name: file:write
      description: Write files to workspace
      resources: [path patterns]

  enforcement_rules:
    - Capabilities not declared are not available — runtime requests are denied
    - Wildcard resources ("*") require justification in the security section
    - Resource patterns are validated against actual resources at registration
    - Capability escalation (adding capabilities at runtime) is forbidden
    - Capability inheritance via extends is limited to what the pattern declares
```

### Isolation Model

Agents are isolated by default. Communication paths must be explicitly
declared.

```yaml
isolation_model:
  default: fully isolated
  communication_paths:
    - path: orchestrator → agent
      always_available: true
      purpose: lifecycle management, health checks

    - path: agent → orchestrator
      always_available: true
      purpose: registration, service directory, event routing

    - path: agent → agent (via message bus)
      requires: agent:message capability + declared collaborator
      purpose: direct messaging for synchronous operations

    - path: agent → agent (via events)
      requires: event:publish + event:subscribe capabilities
      purpose: asynchronous coordination

    - path: agent → storage
      requires: database:read and/or database:write capability
      scope: declared tables only
      purpose: persistent data management

    - path: agent → external
      requires: http:outbound capability
      scope: declared URL patterns only
      purpose: external integrations (webhooks, APIs)

  boundary_violations:
    - Reading another agent's storage tables → rejected
    - Publishing to another agent's event namespace → rejected
    - Sending messages to undeclared agents → rejected
    - Making outbound HTTP to undeclared URLs → rejected
    - Accessing files outside declared paths → rejected
```

### Data Protection

```yaml
data_protection:
  classification_levels:
    - level: low
      description: Non-sensitive operational data (agent names, schedules)
      handling: May be logged freely, stored without encryption

    - level: medium
      description: Business data (content, reports, analysis results)
      handling: Encrypted at rest, logged as summary only

    - level: high
      description: User data, credentials, authentication material
      handling: Encrypted at rest and in transit, never logged, access audited

    - level: critical
      description: Private keys, tokens, secrets
      handling: >
        Encrypted at rest with key isolation, never logged, never included
        in backups, access audited, auto-rotated per patterns/secrets

  enforcement:
    - Every type field that holds data above "low" must declare data_sensitivity
    - Storage tables inherit the highest classification of their fields
    - Log output must not contain fields classified "high" or above
    - Backup files must respect classification-appropriate encryption
    - Event payloads must not contain fields classified "high" or above
      unless the event is scoped to a specific authorized recipient
```

---

## Compliance Checklist for Blueprint Authors

Before submitting a blueprint, verify:

- [ ] Frontmatter has all required fields for this blueprint type
- [ ] `name` matches filename
- [ ] All `requires` and `extends` entries resolve to existing blueprints
- [ ] `## Dependencies` section has full YAML with bindings and on_change for every dependency
- [ ] Types are in YAML format with descriptions, types, and constraints
- [ ] Security section declares all capabilities with specific resources
- [ ] Access control blocks unauthenticated callers
- [ ] Constraints section declares blast radius and forbidden actions
- [ ] Resource limits are declared and reasonable
- [ ] Data sensitivity is classified for all stored data
- [ ] Event namespaces are owned by this blueprint only
- [ ] Storage tables reference types from the Types section
- [ ] Verification checklist has concrete, testable assertions
- [ ] Implementation notes cover pitfalls, performance, security, testing
- [ ] Test fixtures cover happy path, errors, and edge cases
- [ ] Blueprint is implementable from this document alone (no follow-up questions needed)
