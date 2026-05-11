<!-- blueprint
type: pattern
name: migration
version: 1.0.0
requires: [protocol/types, patterns/safety, patterns/approval, patterns/storage, patterns/versioning, patterns/state-machine, patterns/logging]
platform: any
tier: free
-->

# Migration Pattern

Contract-based governance for data migrations. Defines the safety
model, verification protocol, and lifecycle controls that prevent
unauthorized, unverified, or destructive data changes from reaching
production systems. This pattern answers "who can change what data,
under what conditions, with what proof" — not "how to run ALTER TABLE."

The implementation details — which ORM, which migration tool, which
database engine — are application-specific. This pattern defines the
*specification* that any implementation must satisfy to be compliant.

## Overview

Data migrations are the most dangerous operations in any system.
A single uncontrolled migration can corrupt databases, destroy audit
trails, violate regulatory requirements, or silently transform data
in ways that are discovered weeks later. Unlike code deployments,
data changes are often irreversible — you cannot "roll back" a column
that was dropped with its data.

The Weblisk migration pattern treats every data migration as a
**governed operation** subject to the full safety pipeline. Migrations
are not scripts that run automatically — they are contract-bound
artifacts that declare their intent, prove their safety, demonstrate
their reversibility, and require explicit authorization before
touching production data.

The migration governance pipeline has seven stages:

1. **Plan** — a migration plan is created as a signed, reviewable
   artifact describing exactly what will change, what data is
   affected, and what the blast radius is.
2. **Validate** — the plan is validated against the current schema
   state, dependency graph, and safety constraints. Invalid plans
   are rejected before any execution.
3. **Dry Run** — the migration is executed in simulation mode against
   a snapshot or shadow environment. The dry run produces an impact
   report — rows affected, data transformations previewed, integrity
   checksums computed — without committing any changes.
4. **Approve** — the migration plan and dry-run report are submitted
   for approval through `patterns/approval`. Destructive migrations
   require multi-party approval.
5. **Execute** — the approved migration runs within a controlled
   execution context with blast radius limits, progress tracking,
   and automatic rollback on failure.
6. **Verify** — post-execution integrity checks confirm that the
   migration produced the expected results. Checksums, row counts,
   constraint validation, and referential integrity are verified.
7. **Record** — the complete migration lifecycle is recorded in an
   append-only, tamper-evident migration history.

Every stage is required. Stages cannot be skipped. The state machine
enforces the order. A migration that bypasses any stage is a safety
violation subject to kill-switch enforcement.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, category]
        - name: AgentManifest
          fields_used: [name, version, type]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/safety
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: OperationClass
          fields_used: [modify, delete, destroy]
        - name: ResourceClass
          fields_used: [application, system, critical]
        - name: OperationIntent
          fields_used: [id, operation, resource_type, resource_id, resource_class, scope, environment, agent, justification]
        - name: IntentDecision
          fields_used: [intent_id, result, matched_policies, gate, decided_at]
      behaviors:
        - name: intent-declaration
          usage: Migration plans file a MigrationIntent (extends OperationIntent) before execution
        - name: protection-gating
          usage: Migration intents are evaluated through the standard gate matrix
        - name: kill-switch
          usage: Agents that bypass migration governance are kill-switched
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/approval
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        - name: approval-request
          usage: Migration plans are submitted as approval requests after dry-run validation
        - name: multi-party-approval
          usage: Destructive migrations require multi-party consensus
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/storage
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: MigrationStep
          fields_used: [action, type, field]
      behaviors:
        - name: schema-migration
          usage: Migration plan steps use the standard migration action format
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/versioning
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: BlueprintRevision
          fields_used: [revision_id, version, migration, blueprint_hash]
        - name: MigrationSpec
          fields_used: [required, steps, validation]
      behaviors:
        - name: version-migration
          usage: Migration governance wraps the versioning migration execution with safety controls
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/state-machine
    version: ">=1.0.0 <2.0.0"
    bindings:
      behaviors:
        - name: state-transition
          usage: Migration lifecycle is a state machine with enforced transition order
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: patterns/logging
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: LogEntry
          fields_used: [ts, level, log_type, msg, component]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Migrations are contracts, not scripts** — A migration is a
   declaration of intent with provable safety properties. It
   specifies what changes, what data is affected, what the blast
   radius is, and how to reverse it. The declaration is verified
   before any execution occurs. Running arbitrary SQL or ORM
   commands without a migration contract is a safety violation.

2. **Dry run before real run** — Every migration MUST execute in
   simulation mode first. The dry run produces an impact report
   with exact row counts, data samples, checksums, and constraint
   validation. No migration reaches production without a successful
   dry-run report that has been reviewed and approved.

3. **Blast radius is bounded** — Every migration declares the
   maximum number of rows it will affect, the tables it will touch,
   and the time budget it requires. If the actual execution exceeds
   any declared limit, the migration is automatically halted and
   rolled back. An agent cannot migrate "all rows in the database"
   without explicitly declaring that scope and receiving approval
   for it.

4. **Integrity is cryptographically verified** — Pre-migration and
   post-migration checksums are computed over affected data.
   Verification confirms that only the declared changes occurred —
   no silent data corruption, no unexpected side effects, no
   phantom modifications. Checksum mismatches halt the migration
   and trigger investigation.

5. **No implicit authority** — An agent's ability to *read* data
   does not grant it the ability to *migrate* data. Migration
   authority is explicitly granted through mutation contracts that
   specify which tables, which operations, and which row scopes
   the agent is authorized to modify. Authority is verified at
   every stage of the pipeline.

6. **Append-only history** — Every migration plan, dry-run report,
   approval decision, execution result, and verification outcome
   is recorded in a tamper-evident, append-only migration log.
   The history cannot be edited or deleted. It is the compliance
   record for regulatory audit.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: migration-plan
      description: Create a signed, reviewable migration plan with blast radius declaration
      parameters:
        - name: plan
          type: MigrationPlan
          required: true
          description: Complete migration plan artifact
      inherits: Plan validation, dependency checking, blast radius verification
      overridable: true
      override_constraints: Must include all required fields; blast radius MUST be declared

    - name: migration-validate
      description: Validate a migration plan against current schema state and safety constraints
      parameters:
        - name: plan_id
          type: string
          required: true
          description: ID of the plan to validate
      inherits: Schema compatibility check, dependency graph validation, safety gate evaluation
      overridable: false
      override_constraints: Validation is not overridable — invalid plans cannot proceed

    - name: migration-dry-run
      description: Execute migration in simulation mode and produce impact report
      parameters:
        - name: plan_id
          type: string
          required: true
          description: ID of the validated plan to simulate
        - name: target
          type: enum(snapshot, shadow, clone)
          required: true
          description: Dry-run execution target — snapshot (read-only analysis), shadow (copy-on-write), clone (full copy)
      inherits: Simulation execution, impact analysis, checksum computation, report generation
      overridable: true
      override_constraints: Dry run MUST NOT modify production data under any circumstances

    - name: migration-approve
      description: Submit migration plan and dry-run report for approval
      parameters:
        - name: plan_id
          type: string
          required: true
          description: ID of the plan with successful dry-run
        - name: dry_run_report_id
          type: string
          required: true
          description: ID of the dry-run impact report
      inherits: Approval routing via patterns/approval, authority-matches-risk
      overridable: false
      override_constraints: Approval is mandatory for all migrations in staging and production

    - name: migration-execute
      description: Execute an approved migration with blast radius enforcement and progress tracking
      parameters:
        - name: plan_id
          type: string
          required: true
          description: ID of the approved plan
        - name: approval_id
          type: string
          required: true
          description: ID of the approval decision authorizing execution
      inherits: Controlled execution, blast radius monitoring, automatic rollback on limit breach
      overridable: false
      override_constraints: Execution requires valid approval; expired approvals are rejected

    - name: migration-verify
      description: Run post-migration integrity checks and produce verification report
      parameters:
        - name: execution_id
          type: string
          required: true
          description: ID of the completed migration execution
      inherits: Checksum comparison, row count validation, constraint verification, referential integrity
      overridable: false
      override_constraints: Verification failure triggers automatic rollback

    - name: migration-rollback
      description: Reverse a migration using its declared rollback steps
      parameters:
        - name: execution_id
          type: string
          required: true
          description: ID of the migration execution to reverse
        - name: reason
          type: string
          required: true
          description: Why the rollback is being performed
      inherits: Reverse step execution, integrity re-verification, state machine transition
      overridable: false
      override_constraints: Rollback is always permitted — no approval required for rollback

  types:
    - name: MigrationPlan
      description: Signed migration plan artifact with blast radius and reversibility proof
      inherited_by: Types section
    - name: MutationContract
      description: Explicit grant of mutation authority over specific tables and operations
      inherited_by: Types section
    - name: BlastRadius
      description: Declared bounds on migration scope — rows, tables, duration
      inherited_by: Types section
    - name: DryRunReport
      description: Impact analysis from simulation execution
      inherited_by: Types section
    - name: IntegrityCheckpoint
      description: Cryptographic snapshot of data state for pre/post comparison
      inherited_by: Types section
    - name: MigrationExecution
      description: Runtime state of a migration in progress
      inherited_by: Types section
    - name: MigrationRecord
      description: Immutable record in the append-only migration history
      inherited_by: Types section
    - name: MigrationIntent
      description: Specialized OperationIntent for migration operations
      inherited_by: Types section

  events:
    - topic: migration.plan.created
      description: A new migration plan has been created and is pending validation
      payload: {plan_id, agent, tables, operation_class, blast_radius, created_at}
    - topic: migration.plan.validated
      description: A migration plan passed validation checks
      payload: {plan_id, schema_compatible, safety_gate, validated_at}
    - topic: migration.plan.rejected
      description: A migration plan failed validation
      payload: {plan_id, rejection_reasons, rejected_at}
    - topic: migration.dry_run.started
      description: Dry-run simulation has begun
      payload: {plan_id, dry_run_id, target, started_at}
    - topic: migration.dry_run.completed
      description: Dry-run simulation finished — impact report available
      payload: {plan_id, dry_run_id, report_id, rows_affected, duration_ms, completed_at}
    - topic: migration.dry_run.failed
      description: Dry-run simulation failed — migration cannot proceed
      payload: {plan_id, dry_run_id, error, failed_at}
    - topic: migration.approved
      description: Migration plan approved for execution
      payload: {plan_id, approval_id, approvers, approved_at}
    - topic: migration.execution.started
      description: Migration execution has begun
      payload: {plan_id, execution_id, approval_id, started_at}
    - topic: migration.execution.progress
      description: Migration execution progress update
      payload: {execution_id, step_index, total_steps, rows_processed, elapsed_ms}
    - topic: migration.execution.completed
      description: Migration execution finished — pending verification
      payload: {execution_id, steps_completed, rows_affected, duration_ms, completed_at}
    - topic: migration.execution.failed
      description: Migration execution failed — automatic rollback initiated
      payload: {execution_id, failed_step, error, rollback_initiated, failed_at}
    - topic: migration.verified
      description: Post-migration integrity verification passed
      payload: {execution_id, verification_id, checksums_matched, row_counts_matched, verified_at}
    - topic: migration.verification_failed
      description: Post-migration integrity check failed — rollback initiated
      payload: {execution_id, verification_id, mismatches, rollback_initiated, failed_at}
    - topic: migration.rollback.completed
      description: Migration rollback finished — data restored to pre-migration state
      payload: {execution_id, rollback_reason, rollback_duration_ms, integrity_restored, completed_at}
    - topic: migration.recorded
      description: Migration lifecycle recorded in append-only history
      payload: {record_id, plan_id, execution_id, outcome, recorded_at}
```

---

## Migration Lifecycle State Machine

Every migration follows a strict state machine. The state machine
is declared using `patterns/state-machine` format and enforced at
runtime. No transitions outside this machine are valid.

```yaml
state_machine:
  name: migration_lifecycle
  entity_type: MigrationPlan
  state_field: status
  initial_state: draft

  states:
    draft:
      description: Plan created, not yet validated
      terminal: false
    validating:
      description: Validation checks in progress
      terminal: false
    validated:
      description: Plan passed all validation checks
      terminal: false
    validation_failed:
      description: Plan failed validation — must be revised
      terminal: false
    dry_running:
      description: Simulation execution in progress
      terminal: false
    dry_run_complete:
      description: Dry run finished — impact report available for review
      terminal: false
    dry_run_failed:
      description: Dry run failed — plan must be revised
      terminal: false
    pending_approval:
      description: Awaiting operator/multi-party approval
      terminal: false
    approved:
      description: Approved for execution — time-limited
      terminal: false
    rejected:
      description: Approval denied — plan must be revised or abandoned
      terminal: false
    executing:
      description: Migration running against target data
      terminal: false
    executed:
      description: Migration steps completed — pending verification
      terminal: false
    execution_failed:
      description: Execution failed — rollback in progress or complete
      terminal: false
    verifying:
      description: Post-migration integrity checks in progress
      terminal: false
    verified:
      description: Integrity checks passed — migration successful
      terminal: true
    verification_failed:
      description: Integrity checks failed — rollback in progress
      terminal: false
    rolling_back:
      description: Rollback in progress — reversing migration steps
      terminal: false
    rolled_back:
      description: Rollback complete — data restored to pre-migration state
      terminal: true
    abandoned:
      description: Plan abandoned — no execution occurred
      terminal: true

  transitions:
    - from: draft
      to: validating
      trigger: submit_for_validation
      guard: "plan.steps.length > 0 AND plan.blast_radius IS NOT NULL"
      effect: run_validation_checks

    - from: validating
      to: validated
      trigger: validation_passed
      guard: "all_checks_passed == true"
      effect: emit_event(migration.plan.validated)

    - from: validating
      to: validation_failed
      trigger: validation_failed
      effect: emit_event(migration.plan.rejected)

    - from: validation_failed
      to: draft
      trigger: revise_plan
      effect: clear_validation_results

    - from: validated
      to: dry_running
      trigger: start_dry_run
      guard: "dry_run_target IS NOT NULL"
      effect: execute_simulation

    - from: dry_running
      to: dry_run_complete
      trigger: dry_run_succeeded
      guard: "report.errors.length == 0"
      effect: emit_event(migration.dry_run.completed)

    - from: dry_running
      to: dry_run_failed
      trigger: dry_run_errored
      effect: emit_event(migration.dry_run.failed)

    - from: dry_run_failed
      to: draft
      trigger: revise_plan
      effect: clear_dry_run_results

    - from: dry_run_complete
      to: pending_approval
      trigger: submit_for_approval
      guard: "environment IN ['staging', 'production']"
      effect: create_approval_request

    - from: dry_run_complete
      to: approved
      trigger: auto_approve
      guard: "environment == 'development' AND operation_class.ordinal <= 2"
      effect: log_auto_approval

    - from: pending_approval
      to: approved
      trigger: approval_granted
      guard: "approval.decision == 'approved' AND approval.expired == false"
      effect: emit_event(migration.approved)

    - from: pending_approval
      to: rejected
      trigger: approval_denied
      effect: log_rejection_reason

    - from: rejected
      to: draft
      trigger: revise_plan
      effect: clear_approval_state

    - from: approved
      to: executing
      trigger: begin_execution
      guard: "approval.expires_at > now() AND mutation_contract.valid == true"
      effect: [create_integrity_checkpoint, start_execution]
      timeout:
        duration: 3600
        transition: abandoned
        reason: "Approval expired — migration was not executed within the approval window"

    - from: executing
      to: executed
      trigger: all_steps_completed
      guard: "blast_radius_limits_respected == true"
      effect: emit_event(migration.execution.completed)

    - from: executing
      to: execution_failed
      trigger: step_failed_or_limit_exceeded
      effect: [emit_event(migration.execution.failed), initiate_rollback]

    - from: executed
      to: verifying
      trigger: start_verification
      effect: run_integrity_checks

    - from: verifying
      to: verified
      trigger: integrity_confirmed
      guard: "all_checksums_match == true AND all_counts_match == true"
      effect: [emit_event(migration.verified), record_migration]

    - from: verifying
      to: verification_failed
      trigger: integrity_mismatch
      effect: [emit_event(migration.verification_failed), initiate_rollback]

    - from: [execution_failed, verification_failed]
      to: rolling_back
      trigger: rollback_started
      effect: execute_rollback_steps

    - from: rolling_back
      to: rolled_back
      trigger: rollback_completed
      guard: "rollback_integrity_verified == true"
      effect: [emit_event(migration.rollback.completed), record_migration]

    - from: [draft, validated, dry_run_complete, rejected]
      to: abandoned
      trigger: abandon
      effect: record_abandonment
```

### Lifecycle Diagram

```
                    ┌─────────┐
                    │  DRAFT  │◄──── revise ────┐
                    └────┬────┘                 │
                         │ submit               │
                         ▼                      │
                  ┌──────────────┐              │
                  │  VALIDATING  │              │
                  └──────┬───────┘              │
                    ┌────┴─────┐                │
                    ▼          ▼                │
            ┌───────────┐  ┌───────────────┐    │
            │ VALIDATED │  │ VALID. FAILED ├────┘
            └─────┬─────┘  └───────────────┘
                  │ start dry run
                  ▼
            ┌─────────────┐
            │ DRY RUNNING │
            └──────┬──────┘
              ┌────┴─────┐
              ▼          ▼
    ┌────────────────┐ ┌──────────────┐
    │ DRY RUN DONE   │ │ DRY RUN FAIL ├──► revise
    └───────┬────────┘ └──────────────┘
            │ submit for approval
            ▼
    ┌───────────────────┐
    │ PENDING APPROVAL  │
    └────────┬──────────┘
        ┌────┴────┐
        ▼         ▼
  ┌──────────┐ ┌──────────┐
  │ APPROVED │ │ REJECTED ├──► revise
  └────┬─────┘ └──────────┘
       │ begin execution
       ▼
  ┌───────────┐
  │ EXECUTING │
  └─────┬─────┘
   ┌────┴─────┐
   ▼          ▼
┌──────────┐ ┌──────────────┐
│ EXECUTED │ │ EXEC. FAILED │──┐
└────┬─────┘ └──────────────┘  │
     │ verify                   │
     ▼                          │
┌───────────┐                   │
│ VERIFYING │                   │
└─────┬─────┘                   │
 ┌────┴─────┐                  │
 ▼          ▼                  │
┌──────────┐ ┌──────────────┐  │
│ VERIFIED │ │ VERIF. FAILED│──┤
└──────────┘ └──────────────┘  │
   (done)                      │
                               ▼
                       ┌──────────────┐
                       │ ROLLING BACK │
                       └──────┬───────┘
                              ▼
                       ┌─────────────┐
                       │ ROLLED BACK │
                       └─────────────┘
                          (done)
```

---

## Types

### Migration Plan

The migration plan is the central artifact. It is a signed, immutable
declaration of what will change, how, and within what bounds.

```yaml
MigrationPlan:
  description: >
    Signed migration plan artifact declaring intent, steps,
    blast radius, reversibility, and mutation contract.
    Immutable once submitted for validation.
  fields:
    - name: id
      type: string
      required: true
      description: Unique plan identifier (e.g., "mig-20260511-001")
    - name: name
      type: string
      required: true
      description: Human-readable migration name (e.g., "add-priority-to-tasks")
    - name: description
      type: text
      required: true
      description: What this migration does and why it is necessary
    - name: status
      type: enum(draft, validating, validated, validation_failed, dry_running, dry_run_complete, dry_run_failed, pending_approval, approved, rejected, executing, executed, execution_failed, verifying, verified, verification_failed, rolling_back, rolled_back, abandoned)
      required: true
      default: draft
      description: Current lifecycle state — governed by migration_lifecycle state machine
    - name: agent
      type: string
      required: true
      description: Agent or component that owns this migration
    - name: triggered_by
      type: enum(blueprint_update, operator, dependency_change, policy_change)
      required: true
      description: What caused this migration to be created
    - name: source_revision
      type: string
      required: false
      description: BlueprintRevision ID that triggered this migration (if blueprint_update)
    - name: environment
      type: string
      required: true
      description: Target environment — development, staging, production
    - name: operation_class
      type: OperationClass
      required: true
      description: >
        Safety classification of the most dangerous step in this migration.
        A plan with any destroy step is classified as destroy. Classification
        follows the most-dangerous-interpretation rule from patterns/safety.
    - name: tables
      type: "[]string"
      required: true
      description: All tables affected by this migration — used for scope validation
    - name: steps
      type: "[]MigrationStep"
      required: true
      description: Ordered list of migration steps using patterns/storage action format
    - name: rollback_steps
      type: "[]MigrationStep"
      required: true
      description: Ordered list of reverse steps — MUST reverse every forward step
    - name: blast_radius
      type: BlastRadius
      required: true
      description: Declared bounds on what this migration will affect
    - name: mutation_contract
      type: MutationContract
      required: true
      description: Explicit grant of mutation authority for this migration
    - name: pre_conditions
      type: "[]string"
      required: false
      description: Conditions that must be true before execution (e.g., "users table exists", "no active transactions")
    - name: post_conditions
      type: "[]string"
      required: false
      description: Conditions that must be true after execution (e.g., "all rows have priority field")
    - name: integrity_checkpoint_id
      type: string
      required: false
      description: Pre-migration integrity checkpoint — set when execution begins
    - name: plan_hash
      type: string
      required: true
      description: SHA-256 hash of the plan content (steps + rollback_steps + blast_radius) — tamper detection
    - name: created_by
      type: string
      required: true
      description: Identity of who created the plan (operator, agent, system)
    - name: created_at
      type: int64
      required: true
      description: Unix epoch seconds when the plan was created
    - name: updated_at
      type: int64
      required: true
      description: Unix epoch seconds of last status change
```

### Mutation Contract

A mutation contract is an explicit, scoped grant of authority for a
specific migration to modify specific data. Without a valid mutation
contract, no migration can execute — even if the agent normally has
write access to the affected tables.

Mutation contracts prevent the scenario where an agent that can
normally insert rows into a table uses that access to run an
unauthorized bulk delete. The contract binds the migration to a
specific set of allowed operations on specific tables with specific
row-level constraints.

```yaml
MutationContract:
  description: >
    Explicit grant of mutation authority for a migration.
    Binds allowed operations to specific tables with row-level
    constraints and time bounds. Verified at every execution step.
  fields:
    - name: id
      type: string
      required: true
      description: Unique contract identifier
    - name: plan_id
      type: string
      required: true
      description: Migration plan this contract authorizes
    - name: grants
      type: "[]MutationGrant"
      required: true
      description: List of specific mutation grants — one per table/operation combination
    - name: denied_operations
      type: "[]string"
      required: false
      description: >
        Explicit deny list — operations the agent MUST NOT perform during this
        migration, even if the grant would allow it (e.g., "DROP TABLE",
        "TRUNCATE", "DELETE without WHERE clause")
    - name: time_bound
      type: int
      required: true
      description: >
        Maximum seconds the contract is valid from execution start.
        If execution exceeds this bound, the contract expires and
        execution is halted with automatic rollback.
    - name: issued_by
      type: string
      required: true
      description: Identity that issued the contract (system, operator)
    - name: issued_at
      type: int64
      required: true
      description: Unix epoch seconds when the contract was issued
    - name: expires_at
      type: int64
      required: true
      description: Unix epoch seconds when the contract expires — absolute deadline
    - name: revoked
      type: boolean
      required: true
      default: false
      description: Whether the contract has been revoked (operator can revoke mid-execution)
    - name: revoked_reason
      type: string
      required: false
      description: Why the contract was revoked
```

#### Mutation Grant

```yaml
MutationGrant:
  description: >
    Single grant of mutation authority over a specific table
    with a specific operation and optional row-level constraint.
  fields:
    - name: table
      type: string
      required: true
      description: Table name this grant applies to
    - name: operation
      type: enum(add_field, drop_field, alter_field, rename_field, add_index, drop_index, add_constraint, drop_constraint, add_type, drop_type, backfill, transform)
      required: true
      description: Specific migration action permitted — maps to patterns/storage migration actions
    - name: row_constraint
      type: string
      required: false
      description: >
        Row-level filter for backfill/transform operations
        (e.g., "status = 'inactive' AND created_at < 1713264000").
        If specified, the operation MUST only affect rows matching
        this constraint. Violation triggers automatic rollback.
    - name: max_rows
      type: int
      required: false
      description: >
        Maximum rows this grant permits to be affected.
        For schema operations (add_field, add_index, etc.) this is
        not applicable. For data operations (backfill, transform),
        exceeding this limit halts execution.
```

### Blast Radius

Every migration declares its expected blast radius before execution.
The blast radius is a hard limit — if actual execution exceeds any
declared dimension, the migration is automatically halted.

```yaml
BlastRadius:
  description: >
    Declared bounds on migration impact. Acts as a circuit breaker —
    exceeding any limit triggers automatic rollback.
  fields:
    - name: tables_affected
      type: "[]string"
      required: true
      description: >
        Exact list of tables that will be modified. If the migration
        attempts to modify a table not in this list, execution halts.
    - name: max_rows_affected
      type: int
      required: true
      description: >
        Maximum total rows affected across all tables. Set to 0 for
        schema-only changes (e.g., add column with default). Set to
        the expected count for data migrations. The system verifies
        this limit before committing.
    - name: max_duration_seconds
      type: int
      required: true
      description: >
        Maximum wall-clock seconds the migration may run. Migrations
        that exceed this duration are halted and rolled back.
    - name: data_loss_risk
      type: enum(none, recoverable, permanent)
      required: true
      description: >
        Declares whether data loss is possible:
        - none: additive only (add column, add index)
        - recoverable: data modified but reversible (rename, alter type with safe cast)
        - permanent: data will be irreversibly lost (drop column, drop table, transform without backup)
    - name: requires_backup
      type: boolean
      required: true
      description: >
        Whether a backup checkpoint must be created before execution.
        Automatically true when data_loss_risk is "permanent".
        Implementations define backup mechanics (platform-specific).
    - name: estimated_duration_seconds
      type: int
      required: false
      description: Expected duration — used for progress reporting, not enforcement
```

### Dry-Run Report

The dry-run report is the evidence that a migration will do what it
claims. It is produced by simulation execution and is a required
input to the approval process.

```yaml
DryRunReport:
  description: >
    Impact analysis from simulation execution. Documents what would
    happen if the migration were executed for real. Required input
    for approval decisions.
  fields:
    - name: id
      type: string
      required: true
      description: Unique report identifier
    - name: plan_id
      type: string
      required: true
      description: Migration plan that was simulated
    - name: target
      type: enum(snapshot, shadow, clone)
      required: true
      description: >
        How the simulation was executed:
        - snapshot: read-only analysis — counts and schema checks without any writes
        - shadow: copy-on-write execution — runs steps against a shadow copy
        - clone: full database clone — runs steps against a complete copy
    - name: steps_simulated
      type: int
      required: true
      description: Number of migration steps that were simulated
    - name: steps_succeeded
      type: int
      required: true
      description: Number of steps that completed without error in simulation
    - name: rows_that_would_be_affected
      type: int
      required: true
      description: Total rows that would be modified if migration executed for real
    - name: per_table_impact
      type: "[]TableImpact"
      required: true
      description: Breakdown of impact per affected table
    - name: schema_changes_preview
      type: "[]string"
      required: true
      description: Human-readable description of each schema change that would occur
    - name: data_samples
      type: json
      required: false
      description: >
        Sample of before/after data for transform/backfill steps.
        Limited to configurable sample size (default 10 rows per step).
        Sensitive fields are masked per patterns/privacy.
    - name: pre_checksums
      type: "[]IntegrityCheckpoint"
      required: true
      description: Checksums computed over affected data before simulation
    - name: post_checksums
      type: "[]IntegrityCheckpoint"
      required: false
      description: Checksums computed after simulation (for shadow/clone targets only)
    - name: constraint_violations
      type: "[]string"
      required: false
      description: Any constraint violations detected during simulation
    - name: warnings
      type: "[]string"
      required: false
      description: Non-fatal issues detected (e.g., "backfill would affect 50,000 rows — consider batching")
    - name: errors
      type: "[]string"
      required: false
      description: Fatal issues that would prevent real execution
    - name: duration_ms
      type: int
      required: true
      description: How long the simulation took — used for duration estimate in real execution
    - name: simulated_at
      type: int64
      required: true
      description: Unix epoch seconds when the simulation completed
```

#### Table Impact

```yaml
TableImpact:
  description: Per-table impact breakdown from dry-run simulation
  fields:
    - name: table
      type: string
      required: true
      description: Table name
    - name: operation
      type: string
      required: true
      description: Migration action applied to this table
    - name: rows_affected
      type: int
      required: true
      description: Number of rows that would be affected
    - name: total_rows
      type: int
      required: true
      description: Total rows in the table (for context)
    - name: percentage_affected
      type: float
      required: true
      description: Percentage of table rows affected
    - name: size_change_bytes
      type: int
      required: false
      description: Estimated change in storage size (positive = growth, negative = shrink)
```

### Integrity Checkpoint

Integrity checkpoints are cryptographic snapshots of data state.
They are computed before and after migration execution and compared
to verify that only declared changes occurred.

```yaml
IntegrityCheckpoint:
  description: >
    Cryptographic snapshot of data state at a point in time.
    Used for pre/post migration comparison.
  fields:
    - name: id
      type: string
      required: true
      description: Unique checkpoint identifier
    - name: table
      type: string
      required: true
      description: Table this checkpoint covers
    - name: row_count
      type: int
      required: true
      description: Total rows in the table at checkpoint time
    - name: checksum
      type: string
      required: true
      description: >
        SHA-256 hash computed over the table's data. The checksum
        algorithm is: sort rows by primary key, concatenate all
        field values as UTF-8 strings, compute SHA-256. This is
        deterministic and reproducible.
    - name: schema_hash
      type: string
      required: true
      description: SHA-256 hash of the table's schema definition (column names, types, constraints)
    - name: scope_filter
      type: string
      required: false
      description: >
        If only a subset of rows were checksummed (for large tables),
        the filter expression used (e.g., "created_at > 1713264000").
        If null, the entire table was checksummed.
    - name: captured_at
      type: int64
      required: true
      description: Unix epoch seconds when the checkpoint was captured
```

### Migration Execution

Runtime state of a migration being executed.

```yaml
MigrationExecution:
  description: Runtime state and progress of a migration execution
  fields:
    - name: id
      type: string
      required: true
      description: Unique execution identifier
    - name: plan_id
      type: string
      required: true
      description: Migration plan being executed
    - name: approval_id
      type: string
      required: true
      description: Approval that authorized this execution
    - name: contract_id
      type: string
      required: true
      description: Mutation contract governing this execution
    - name: pre_checkpoint_id
      type: string
      required: true
      description: Integrity checkpoint taken before execution started
    - name: post_checkpoint_id
      type: string
      required: false
      description: Integrity checkpoint taken after execution completed (before verification)
    - name: current_step
      type: int
      required: true
      description: Index of the currently executing step (0-based)
    - name: total_steps
      type: int
      required: true
      description: Total number of steps in the migration
    - name: rows_processed
      type: int
      required: true
      default: 0
      description: Total rows processed so far across all steps
    - name: status
      type: enum(running, completed, failed, rolling_back, rolled_back)
      required: true
      description: Execution status
    - name: step_results
      type: "[]StepResult"
      required: false
      description: Result of each completed step
    - name: started_at
      type: int64
      required: true
      description: Unix epoch seconds when execution began
    - name: completed_at
      type: int64
      required: false
      description: Unix epoch seconds when execution finished (null if still running)
    - name: error
      type: string
      required: false
      description: Error message if execution failed
```

#### Step Result

```yaml
StepResult:
  description: Result of executing a single migration step
  fields:
    - name: step_index
      type: int
      required: true
      description: Index of this step in the plan
    - name: action
      type: string
      required: true
      description: Migration action that was executed
    - name: table
      type: string
      required: true
      description: Table affected by this step
    - name: rows_affected
      type: int
      required: true
      description: Rows affected by this step
    - name: duration_ms
      type: int
      required: true
      description: How long this step took
    - name: success
      type: boolean
      required: true
      description: Whether the step completed successfully
    - name: error
      type: string
      required: false
      description: Error message if the step failed
```

### Migration Intent

A specialized `OperationIntent` (from `patterns/safety`) for
migration operations. Extends the base intent with migration-specific
fields that the safety pipeline uses for gate evaluation.

```yaml
MigrationIntent:
  description: >
    Specialized OperationIntent for migration operations. Extends
    the base intent with blast radius, affected tables, and data
    loss risk so the safety pipeline can make informed gate decisions.
  extends: OperationIntent
  additional_fields:
    - name: plan_id
      type: string
      required: true
      description: Migration plan this intent corresponds to
    - name: tables_affected
      type: "[]string"
      required: true
      description: All tables this migration will touch
    - name: estimated_rows
      type: int
      required: true
      description: Expected number of rows to be affected
    - name: data_loss_risk
      type: enum(none, recoverable, permanent)
      required: true
      description: Data loss classification from the blast radius declaration
    - name: has_dry_run_report
      type: boolean
      required: true
      description: Whether a successful dry-run report exists
    - name: dry_run_report_id
      type: string
      required: false
      description: ID of the dry-run report (if has_dry_run_report is true)
    - name: reversibility_proof
      type: boolean
      required: true
      description: Whether rollback steps exist for every forward step
```

### Migration Record

Immutable record in the append-only migration history. Once written,
a migration record cannot be modified or deleted.

```yaml
MigrationRecord:
  description: >
    Immutable, tamper-evident record in the migration history log.
    Records the complete lifecycle of a migration for compliance
    audit. Hash-chained to detect tampering.
  fields:
    - name: id
      type: string
      required: true
      description: Unique record identifier
    - name: plan_id
      type: string
      required: true
      description: Migration plan this record documents
    - name: plan_hash
      type: string
      required: true
      description: SHA-256 of the plan at execution time — detects post-hoc plan modification
    - name: execution_id
      type: string
      required: false
      description: Execution ID (null if migration was abandoned before execution)
    - name: outcome
      type: enum(verified, rolled_back, abandoned)
      required: true
      description: Final outcome of the migration
    - name: agent
      type: string
      required: true
      description: Agent that performed the migration
    - name: environment
      type: string
      required: true
      description: Environment where the migration ran
    - name: tables_affected
      type: "[]string"
      required: true
      description: Tables that were actually modified
    - name: rows_affected
      type: int
      required: true
      description: Total rows actually affected (0 for schema-only or abandoned)
    - name: operation_class
      type: OperationClass
      required: true
      description: Safety classification
    - name: approval_id
      type: string
      required: false
      description: Approval that authorized execution (null if auto-approved or abandoned)
    - name: approvers
      type: "[]string"
      required: false
      description: Identities that approved the migration
    - name: dry_run_report_id
      type: string
      required: false
      description: Dry-run report (null if abandoned before dry run)
    - name: pre_checkpoint
      type: IntegrityCheckpoint
      required: false
      description: Pre-migration integrity state
    - name: post_checkpoint
      type: IntegrityCheckpoint
      required: false
      description: Post-migration integrity state
    - name: rollback_reason
      type: string
      required: false
      description: Why the migration was rolled back (if outcome is rolled_back)
    - name: duration_ms
      type: int
      required: false
      description: Total execution duration including verification
    - name: previous_record_hash
      type: string
      required: true
      description: SHA-256 of the previous MigrationRecord — hash chain for tamper detection
    - name: record_hash
      type: string
      required: true
      description: SHA-256 of this record (all fields except record_hash itself)
    - name: recorded_at
      type: int64
      required: true
      description: Unix epoch seconds when this record was written
```

---

## Migration Plan Validation

When a plan transitions from `draft` to `validating`, the following
checks run. All checks must pass for the plan to reach `validated`.

### Validation Checks

```yaml
validation_checks:
  - name: schema_compatibility
    description: >
      Verify that forward steps are compatible with the current schema.
      An add_field step must target a table that exists. A drop_field
      step must target a field that exists. An alter_field step must
      specify valid type conversions.
    fatal: true

  - name: rollback_completeness
    description: >
      Every forward step MUST have a corresponding rollback step.
      The rollback steps must reverse the forward steps in correct
      order. Missing rollback steps fail validation.
    fatal: true

  - name: blast_radius_plausibility
    description: >
      The declared blast radius must be plausible. max_rows_affected
      cannot be 0 for a backfill step. tables_affected must include
      every table referenced in the steps. max_duration_seconds must
      be greater than 0.
    fatal: true

  - name: mutation_contract_coverage
    description: >
      The mutation contract must grant authority for every step in
      the plan. A step that modifies a table not covered by a grant
      fails validation. A step that performs an operation not granted
      fails validation.
    fatal: true

  - name: dependency_safety
    description: >
      If the migration modifies a table that is referenced by another
      agent's source_type annotation, warn that downstream agents may
      be affected. If the migration drops a table with active foreign
      key references, fail validation.
    fatal: true

  - name: operation_class_accuracy
    description: >
      The plan's operation_class must match or exceed the most
      dangerous step. A plan classified as "modify" that contains
      a "drop_field" step (which is "delete") fails validation.
    fatal: true

  - name: pre_condition_checkable
    description: >
      All declared pre-conditions must be verifiable expressions.
      Conditions that reference non-existent tables or fields fail
      validation.
    fatal: false

  - name: idempotency_check
    description: >
      Warn if the migration is not idempotent (re-running it would
      fail). Schema operations are inherently non-idempotent (can't
      add a field twice), but the plan should account for this in
      pre-conditions (e.g., "field does not exist").
    fatal: false
```

---

## Dry-Run Execution

Dry runs execute the migration in simulation mode. The goal is to
produce an accurate impact report without modifying production data.

### Dry-Run Targets

| Target | How It Works | Accuracy | Cost |
|--------|-------------|----------|------|
| `snapshot` | Read-only analysis: count matching rows, validate schema changes, check constraints — no writes executed | Medium — counts and schema validated but data transformations not tested | Lowest — no extra storage or compute |
| `shadow` | Copy-on-write: migration steps execute against a transient shadow of affected tables; changes discarded after analysis | High — actual step execution observed | Moderate — temporary storage for shadow tables |
| `clone` | Full database clone: migration steps execute against a complete copy of the database | Highest — exact production replica | Highest — full database copy required |

### Dry-Run Requirements

```
1. Dry run MUST NOT modify production data — this is a hard invariant.
   Violation of this invariant is a critical safety violation.
2. Dry run MUST compute pre-checksums over all affected tables.
3. For shadow/clone targets, dry run MUST compute post-checksums
   and compare them to validate expected changes.
4. Dry run MUST report exact row counts that would be affected
   per table per step.
5. Dry run MUST detect and report constraint violations that would
   occur during real execution.
6. Dry run SHOULD sample before/after data for transform steps
   (limited to configured sample size, sensitive fields masked).
7. Dry run MUST complete within the blast radius max_duration_seconds —
   if simulation exceeds the time budget, real execution will too.
```

### Dry-Run Flow

```
dry_run(plan, target):
  # 1. Validate plan is in "validated" state
  ASSERT plan.status == "validated"

  # 2. Transition plan to "dry_running"
  transition(plan, "dry_running")
  EMIT event("migration.dry_run.started", {plan.id, target})

  # 3. Compute pre-checksums
  pre_checksums = []
  FOR EACH table IN plan.blast_radius.tables_affected:
    checkpoint = compute_integrity_checkpoint(table)
    pre_checksums.APPEND(checkpoint)

  # 4. Execute simulation based on target type
  IF target == "snapshot":
    results = analyze_steps_read_only(plan.steps)
  ELSE IF target == "shadow":
    shadow = create_shadow_copy(plan.blast_radius.tables_affected)
    results = execute_steps_on(shadow, plan.steps)
    post_checksums = compute_checksums(shadow)
    discard_shadow(shadow)
  ELSE IF target == "clone":
    clone = create_full_clone()
    results = execute_steps_on(clone, plan.steps)
    post_checksums = compute_checksums(clone)
    discard_clone(clone)

  # 5. Build impact report
  report = DryRunReport(
    plan_id:        plan.id,
    target:         target,
    pre_checksums:  pre_checksums,
    post_checksums: post_checksums IF target != "snapshot" ELSE null,
    per_table_impact: compute_per_table_impact(results),
    rows_that_would_be_affected: sum(results.rows_affected),
    ...
  )

  # 6. Evaluate results
  IF report.errors.length > 0:
    transition(plan, "dry_run_failed")
    EMIT event("migration.dry_run.failed", {plan.id, report.errors})
  ELSE:
    transition(plan, "dry_run_complete")
    EMIT event("migration.dry_run.completed", {plan.id, report.id})

  RETURN report
```

---

## Approval Integration

Migrations integrate with `patterns/approval` for authorization.
The approval routing is determined by the migration's operation class,
environment, and data loss risk.

### Approval Routing

| Environment | Operation Class | Data Loss Risk | Approval Required |
|-------------|----------------|----------------|-------------------|
| development | read, create, modify | any | Auto-approved |
| development | delete, destroy | any | Single operator |
| staging | read, create | any | Auto-approved |
| staging | modify | none, recoverable | Single operator |
| staging | modify | permanent | Two operators |
| staging | delete, destroy | any | Two operators |
| production | read, create | any | Single operator |
| production | modify | none | Single operator |
| production | modify | recoverable | Two operators |
| production | modify | permanent | Two operators + admin |
| production | delete | any | Two operators + admin |
| production | destroy | any | Three operators + admin (4-eyes) |

### Approval Request Content

When a migration is submitted for approval, the approval request
includes:

```yaml
migration_approval_request:
  type: migration
  plan_id: "{plan.id}"
  plan_name: "{plan.name}"
  plan_description: "{plan.description}"
  operation_class: "{plan.operation_class}"
  environment: "{plan.environment}"
  data_loss_risk: "{plan.blast_radius.data_loss_risk}"
  tables_affected: "{plan.tables}"
  estimated_rows: "{dry_run_report.rows_that_would_be_affected}"
  dry_run_report_id: "{dry_run_report.id}"
  blast_radius: "{plan.blast_radius}"
  per_table_impact: "{dry_run_report.per_table_impact}"
  warnings: "{dry_run_report.warnings}"
  requested_by: "{plan.agent}"
  justification: "{plan.description}"
```

Approvers MUST have access to the full dry-run report before making
a decision. The approval system does not permit approval without
a successful dry-run report.

### Approval Expiration

Approved migrations have a time-limited execution window:

```yaml
approval_expiration:
  development: 86400     # 24 hours
  staging: 14400         # 4 hours
  production: 3600       # 1 hour
```

If the migration is not executed within the approval window, the
approval expires and the migration must be re-submitted. This
prevents "approve now, execute weeks later" scenarios where the
database state may have changed.

---

## Execution Protocol

### Pre-Execution Checks

Before any migration step runs, the execution engine validates:

```
pre_execution_validate(plan, approval, contract):
  # 1. Approval is valid and not expired
  ASSERT approval.decision == "approved"
  ASSERT approval.expires_at > now()

  # 2. Mutation contract is valid and not revoked
  ASSERT contract.revoked == false
  ASSERT contract.expires_at > now()

  # 3. Plan has not been modified since approval
  ASSERT hash(plan.steps + plan.rollback_steps + plan.blast_radius) == plan.plan_hash

  # 4. Pre-conditions are met
  FOR EACH condition IN plan.pre_conditions:
    ASSERT evaluate(condition) == true

  # 5. Create pre-execution integrity checkpoint
  checkpoint = create_integrity_checkpoint(plan.blast_radius.tables_affected)
  plan.integrity_checkpoint_id = checkpoint.id

  # 6. File migration intent with safety pipeline
  intent = MigrationIntent(
    operation:            plan.operation_class,
    resource_type:        "database_migration",
    resource_id:          plan.id,
    resource_class:       classify_tables(plan.tables),
    scope:                resolve_scope(plan.tables),
    environment:          plan.environment,
    agent:                plan.agent,
    justification:        plan.description,
    plan_id:              plan.id,
    tables_affected:      plan.tables,
    estimated_rows:       plan.blast_radius.max_rows_affected,
    data_loss_risk:       plan.blast_radius.data_loss_risk,
    has_dry_run_report:   true,
    dry_run_report_id:    plan.dry_run_report_id,
    reversibility_proof:  plan.rollback_steps.length > 0
  )
  decision = intent_evaluate(intent)
  ASSERT decision.result IN ["allow", "audit"]
```

### Step Execution

```
execute_migration(plan, approval, contract):
  execution = MigrationExecution(
    plan_id:     plan.id,
    approval_id: approval.id,
    contract_id: contract.id,
    ...
  )

  transition(plan, "executing")
  EMIT event("migration.execution.started", {plan.id, execution.id})

  FOR EACH step AT index IN plan.steps:
    # Validate contract covers this step
    grant = find_grant(contract, step.table, step.action)
    IF grant IS NULL:
      FAIL("Step {index} not covered by mutation contract")

    # Check blast radius limits
    IF execution.rows_processed + step.estimated_rows > plan.blast_radius.max_rows_affected:
      FAIL("Blast radius exceeded: {execution.rows_processed} + {step.estimated_rows} > {plan.blast_radius.max_rows_affected}")

    # Check time budget
    IF elapsed(execution.started_at) > plan.blast_radius.max_duration_seconds:
      FAIL("Time budget exceeded")

    # Check contract not revoked mid-execution
    IF contract.revoked:
      FAIL("Mutation contract revoked: {contract.revoked_reason}")

    # Execute the step
    result = execute_step(step)

    IF result.success == false:
      transition(plan, "execution_failed")
      EMIT event("migration.execution.failed", {execution.id, index, result.error})
      initiate_rollback(execution, plan.rollback_steps, "Step {index} failed: {result.error}")
      RETURN

    # Validate row constraint if applicable
    IF grant.max_rows IS NOT NULL AND result.rows_affected > grant.max_rows:
      transition(plan, "execution_failed")
      EMIT event("migration.execution.failed", {execution.id, index, "Row limit exceeded"})
      initiate_rollback(execution, plan.rollback_steps, "Grant row limit exceeded")
      RETURN

    execution.rows_processed += result.rows_affected
    execution.current_step = index + 1
    EMIT event("migration.execution.progress", {execution.id, index, plan.steps.length, execution.rows_processed})

  # All steps completed
  transition(plan, "executed")
  EMIT event("migration.execution.completed", {execution.id})
```

### Automatic Rollback

Rollback is triggered automatically on:
- Step execution failure
- Blast radius limit exceeded (rows or duration)
- Mutation contract revoked during execution
- Grant row constraint violated
- Post-execution verification failure

```
initiate_rollback(execution, rollback_steps, reason):
  transition(plan, "rolling_back")

  FOR EACH step IN REVERSE(rollback_steps[0..execution.current_step]):
    result = execute_step(step)
    IF result.success == false:
      # Rollback failure is a critical incident
      EMIT alert(critical, "Migration rollback failed — manual intervention required")
      BREAK

  # Verify rollback restored data
  post_rollback_checkpoint = create_integrity_checkpoint(plan.blast_radius.tables_affected)
  IF matches(execution.pre_checkpoint_id, post_rollback_checkpoint):
    transition(plan, "rolled_back")
    EMIT event("migration.rollback.completed", {execution.id, reason, integrity_restored: true})
  ELSE:
    EMIT alert(critical, "Rollback integrity verification failed — data may be inconsistent")
    transition(plan, "rolled_back")
    EMIT event("migration.rollback.completed", {execution.id, reason, integrity_restored: false})

  record_migration(plan, execution, outcome: "rolled_back", rollback_reason: reason)
```

---

## Post-Migration Verification

After execution completes, integrity verification confirms the
migration produced only the expected changes.

### Verification Checks

```
verify_migration(execution, plan):
  transition(plan, "verifying")

  # 1. Compute post-execution checksums
  post_checkpoint = create_integrity_checkpoint(plan.blast_radius.tables_affected)
  execution.post_checkpoint_id = post_checkpoint.id

  # 2. Row count validation
  FOR EACH table IN plan.blast_radius.tables_affected:
    pre_count  = get_checkpoint_count(execution.pre_checkpoint_id, table)
    post_count = get_checkpoint_count(post_checkpoint.id, table)
    expected_delta = compute_expected_delta(plan.steps, table)

    IF (post_count - pre_count) != expected_delta:
      FAIL("Row count mismatch for {table}: expected delta {expected_delta}, got {post_count - pre_count}")

  # 3. Schema verification
  FOR EACH table IN plan.blast_radius.tables_affected:
    actual_schema = get_current_schema(table)
    expected_schema = compute_expected_schema(plan.steps, table)
    IF actual_schema != expected_schema:
      FAIL("Schema mismatch for {table}")

  # 4. Post-condition validation
  FOR EACH condition IN plan.post_conditions:
    IF NOT evaluate(condition):
      FAIL("Post-condition failed: {condition}")

  # 5. Referential integrity
  FOR EACH table IN plan.blast_radius.tables_affected:
    fk_violations = check_foreign_key_integrity(table)
    IF fk_violations.length > 0:
      FAIL("Referential integrity violated: {fk_violations}")

  # 6. Unmodified table verification
  # Tables NOT in the blast radius must be unchanged
  FOR EACH checkpoint IN execution.pre_checkpoint:
    IF checkpoint.table NOT IN plan.blast_radius.tables_affected:
      current = compute_integrity_checkpoint(checkpoint.table)
      IF current.checksum != checkpoint.checksum:
        FAIL("Unaffected table {checkpoint.table} was modified — possible data corruption")

  transition(plan, "verified")
  EMIT event("migration.verified", {execution.id, post_checkpoint.id})
  record_migration(plan, execution, outcome: "verified")
```

---

## Migration History

All migration records are stored in an append-only, hash-chained
table. The hash chain provides tamper detection — modifying any
historical record invalidates all subsequent hashes.

### Table: migration_history

```yaml
storage:
  tables:
    - type: MigrationRecord
      retention: null     # Never purged — permanent compliance record
      indexes:
        - name: idx_migration_plan
          fields: [plan_id]
        - name: idx_migration_agent
          fields: [agent]
        - name: idx_migration_environment
          fields: [environment]
        - name: idx_migration_outcome
          fields: [outcome]
        - name: idx_migration_recorded
          fields: [recorded_at]
```

### Hash Chain Integrity

```
record_migration(plan, execution, outcome, ...):
  previous = get_latest_record()
  previous_hash = previous.record_hash IF previous EXISTS ELSE "genesis"

  record = MigrationRecord(
    id:                   generate_id(),
    plan_id:              plan.id,
    plan_hash:            plan.plan_hash,
    execution_id:         execution.id IF execution EXISTS ELSE null,
    outcome:              outcome,
    ...
    previous_record_hash: previous_hash,
    recorded_at:          now()
  )

  # Compute record hash over all fields
  record.record_hash = sha256(serialize(record, exclude=["record_hash"]))

  # Append — INSERT only, no UPDATE, no DELETE
  INSERT record INTO migration_history

  EMIT event("migration.recorded", {record.id, plan.id, outcome})
```

### Tamper Detection

The hash chain is validated periodically and on-demand:

```
validate_migration_history():
  records = SELECT * FROM migration_history ORDER BY recorded_at ASC
  expected_previous = "genesis"

  FOR EACH record IN records:
    # Verify chain link
    IF record.previous_record_hash != expected_previous:
      ALERT(critical, "Migration history tampered: record {record.id} chain broken")
      RETURN false

    # Verify record integrity
    computed = sha256(serialize(record, exclude=["record_hash"]))
    IF computed != record.record_hash:
      ALERT(critical, "Migration history tampered: record {record.id} content modified")
      RETURN false

    expected_previous = record.record_hash

  RETURN true
```

---

## Environment-Specific Behavior

### Development

```yaml
development:
  dry_run_target: snapshot           # Lightweight — read-only analysis
  auto_approve: true                 # For modify and below
  auto_approve_max_class: modify     # delete/destroy still require approval
  approval_expiration: 86400         # 24 hours
  blast_radius_enforcement: warn     # Log but don't halt on limit breach
  integrity_checkpoints: optional    # Checksums computed but mismatch is warning, not failure
  rollback_on_verify_fail: false     # Log warning instead of rolling back
```

### Staging

```yaml
staging:
  dry_run_target: shadow             # Copy-on-write simulation
  auto_approve: false                # All migrations require approval
  approval_expiration: 14400         # 4 hours
  blast_radius_enforcement: enforce  # Halt on limit breach
  integrity_checkpoints: required    # Checksum mismatch fails verification
  rollback_on_verify_fail: true      # Automatic rollback on verification failure
```

### Production

```yaml
production:
  dry_run_target: clone              # Full clone for maximum accuracy
  auto_approve: false                # All migrations require approval
  approval_expiration: 3600          # 1 hour
  blast_radius_enforcement: enforce  # Halt on limit breach — no exceptions
  integrity_checkpoints: required    # Checksum mismatch triggers rollback
  rollback_on_verify_fail: true      # Automatic rollback on verification failure
  require_backup: true               # Backup checkpoint before any migration
  contract_time_bound_max: 3600      # Mutation contracts expire after 1 hour max
```

---

## Safety Integration

### Migration Operations in the Safety Pipeline

Migrations integrate with `patterns/safety` through the
`MigrationIntent` type. When a migration files an intent, the
safety pipeline evaluates it using the standard gate matrix with
additional migration-specific context.

### Gate Evaluation for Migrations

The safety pipeline uses the migration's `data_loss_risk` and
`has_dry_run_report` fields to modify gate decisions:

```yaml
migration_gate_modifiers:
  # Migrations without dry-run reports are denied in staging/production
  - condition: "has_dry_run_report == false AND environment IN ['staging', 'production']"
    override: deny
    reason: "Migrations require successful dry-run before execution in non-development environments"

  # Permanent data loss migrations are escalated one level
  - condition: "data_loss_risk == 'permanent'"
    amplification: 1
    reason: "Permanent data loss requires elevated authorization"

  # Migrations without reversibility proof are escalated
  - condition: "reversibility_proof == false"
    amplification: 1
    reason: "Irreversible migrations require elevated authorization"
```

### Safety Violations

The following migration actions are safety violations subject to
kill-switch enforcement:

```yaml
migration_safety_violations:
  - executing a migration without a valid plan (bypassing the state machine)
  - executing a migration without a successful dry run (in staging/production)
  - executing a migration without approval (in staging/production)
  - executing a migration with an expired approval
  - executing a migration with a revoked mutation contract
  - modifying a table not declared in the blast radius
  - exceeding declared blast radius limits without halt
  - modifying migration history records (append-only violation)
  - executing migration steps outside the mutation contract grants
```

---

## Error Handling

### Error Codes

| Code | Category | Description |
|------|----------|-------------|
| `MIGRATION_PLAN_INVALID` | permanent | Plan failed validation — see rejection_reasons |
| `MIGRATION_DRY_RUN_FAILED` | transient | Dry-run simulation failed — may be retried after plan revision |
| `MIGRATION_NOT_APPROVED` | permanent | Migration lacks required approval |
| `MIGRATION_APPROVAL_EXPIRED` | permanent | Approval window has elapsed — re-submit |
| `MIGRATION_CONTRACT_REVOKED` | permanent | Mutation contract revoked — cannot proceed |
| `MIGRATION_CONTRACT_EXPIRED` | permanent | Mutation contract time bound exceeded |
| `MIGRATION_BLAST_RADIUS_EXCEEDED` | permanent | Execution exceeded declared limits — rolled back |
| `MIGRATION_VERIFICATION_FAILED` | permanent | Post-migration integrity check failed — rolled back |
| `MIGRATION_ROLLBACK_FAILED` | permanent | Rollback failed — manual intervention required |
| `MIGRATION_HISTORY_TAMPERED` | permanent | Hash chain integrity violation detected |
| `MIGRATION_GRANT_VIOLATED` | permanent | Step attempted operation not covered by contract |
| `MIGRATION_STATE_INVALID` | permanent | Attempted invalid state transition |

### Error Response Format

All migration errors follow the standard `ErrorResponse` from
`protocol/types`:

```json
{
  "error": "Migration plan validation failed",
  "code": "MIGRATION_PLAN_INVALID",
  "category": "permanent",
  "retryable": false,
  "detail": {
    "plan_id": "mig-20260511-001",
    "rejection_reasons": [
      "Rollback step missing for forward step 3 (drop_field)",
      "Blast radius max_rows_affected is 0 but step 2 is a backfill"
    ]
  }
}
```

---

## Implementation Notes

- **Platform-specific execution**: The *how* of executing migration
  steps (which SQL dialect, which ORM, which migration tool) is
  defined by the platform (`platforms/node.md`, `platforms/go.md`,
  etc.). This pattern defines the governance model, not the DDL.

- **Checksum computation**: The SHA-256 checksum algorithm (sort by
  PK, concatenate, hash) is a specification-level definition. Large
  tables may use sampling with a declared `scope_filter` to keep
  checksum computation within time budgets.

- **Backup mechanics**: The `requires_backup` flag triggers a
  backup, but the backup format and storage location are
  platform-specific. This pattern requires that a backup exists and
  can be restored — it does not prescribe how.

- **Batch execution**: For large data migrations (millions of rows),
  implementations SHOULD batch operations to avoid long-running
  transactions. Each batch is a separate step in the migration plan
  with its own row count limit in the mutation grant.

- **Concurrent migration prevention**: Only one migration may
  execute against the same table at the same time. The execution
  engine MUST acquire a table-level advisory lock before proceeding.
  Concurrent attempts return `MIGRATION_STATE_INVALID`.

- **AI agent guardrails**: AI agents are subject to the same
  migration governance as any other component. An AI agent that
  needs to modify data MUST create a migration plan, pass dry-run
  validation, receive approval, and execute within its mutation
  contract. The AI agent cannot bypass the state machine or self-
  approve its own migrations in staging or production.

---

## Verification Checklist

- [ ] Every data migration has a formal MigrationPlan with all required fields
- [ ] Every plan declares a BlastRadius with explicit row, table, and time limits
- [ ] Every plan has a MutationContract with grants covering all steps
- [ ] Rollback steps exist for every forward step
- [ ] Dry run completes successfully before approval is requested
- [ ] DryRunReport is available to approvers before they make a decision
- [ ] Approval routing matches the operation class × environment × data loss risk matrix
- [ ] Approved migrations execute within the approval expiration window
- [ ] Blast radius limits are enforced during execution — limit breach triggers rollback
- [ ] Mutation contract is verified at every step — unauthorized operations are rejected
- [ ] Pre-migration and post-migration integrity checkpoints are computed and compared
- [ ] Row count deltas match expected values per table
- [ ] Schema state matches expected state after migration
- [ ] Referential integrity is verified post-migration
- [ ] Tables outside the blast radius are verified unchanged
- [ ] Migration lifecycle follows the state machine — no stage is skipped
- [ ] Migration record is appended to hash-chained history — no records modified
- [ ] Hash chain integrity is validated periodically
- [ ] AI agents cannot self-approve migrations in staging or production
- [ ] Safety violations trigger kill-switch enforcement per patterns/safety
