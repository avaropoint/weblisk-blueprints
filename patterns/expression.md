<!-- blueprint
type: pattern
name: expression
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Expression Language

Standard expression language for guards, conditions, constraints, and
policy rules across the Weblisk framework. Provides a safe, sandboxed
subset of boolean and comparison operations — no side effects, no
function calls, no variable assignment.

## Overview

Multiple blueprints need to evaluate expressions at runtime:

- **State machine guards**: transition conditions (`attempts < max_retries`)
- **Workflow phase conditions**: skip logic (`$phases.scan.status == "success"`)
- **Storage constraints**: check constraints, partial index conditions
- **ABAC policy rules**: authorization decisions
- **Safety rules**: operation classification

This pattern defines the shared grammar, evaluation rules, and type
system so that all expression consumers use identical semantics. The
language is intentionally minimal — it evaluates to a boolean or a
scalar value, never mutates state, and never performs I/O.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TypeDefinition
          fields_used: [name, fields]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Grammar

Expressions are UTF-8 strings evaluated against a context object.
The grammar is defined in EBNF:

```ebnf
expression     = or_expr ;
or_expr        = and_expr { "OR" and_expr } ;
and_expr       = not_expr { "AND" not_expr } ;
not_expr       = [ "NOT" ] comparison ;
comparison     = addition [ comp_op addition ] ;
addition       = multiplication { ( "+" | "-" ) multiplication } ;
multiplication = unary { ( "*" | "/" | "%" ) unary } ;
unary          = [ "-" ] primary ;
primary        = literal
               | path
               | "(" expression ")"
               | "null" ;

path           = identifier { "." identifier } ;
identifier     = letter { letter | digit | "_" } ;

comp_op        = "==" | "!=" | "<" | ">" | "<=" | ">="
               | "IN" | "NOT IN"
               | "CONTAINS" | "STARTS_WITH" | "ENDS_WITH"
               | "MATCHES" ;

literal        = string_lit | number_lit | bool_lit | array_lit ;
string_lit     = '"' { char } '"' ;
number_lit     = [ "-" ] digit { digit } [ "." digit { digit } ] ;
bool_lit       = "true" | "false" ;
array_lit      = "[" [ expression { "," expression } ] "]" ;
```

### Operator Precedence (highest to lowest)

| Precedence | Operators | Associativity |
|-----------|-----------|---------------|
| 1 | `-` (unary) | right |
| 2 | `*`, `/`, `%` | left |
| 3 | `+`, `-` | left |
| 4 | `==`, `!=`, `<`, `>`, `<=`, `>=`, `IN`, `NOT IN`, `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`, `MATCHES` | none |
| 5 | `NOT` | right |
| 6 | `AND` | left |
| 7 | `OR` | left |

### Reserved Words

`AND`, `OR`, `NOT`, `IN`, `CONTAINS`, `STARTS_WITH`, `ENDS_WITH`,
`MATCHES`, `true`, `false`, `null`

Reserved words are case-sensitive and MUST be uppercase (except
`true`, `false`, `null` which are lowercase).

---

## Type System

Expressions operate on five value types:

| Type | Examples | Notes |
|------|----------|-------|
| string | `"hello"`, `"pending"` | UTF-8, double-quoted |
| number | `42`, `3.14`, `-1` | IEEE 754 double (same as JSON) |
| boolean | `true`, `false` | Result of comparisons and logical operators |
| null | `null` | Missing or undefined values |
| array | `["a", "b"]`, `[1, 2, 3]` | Homogeneous, used with `IN` operator |

### Type Coercion Rules

Expressions use **strict typing with no implicit coercion**:

- Comparing different types (except null) is a runtime error
- Arithmetic on non-numbers is a runtime error
- `null == null` is `true`
- `null != <anything non-null>` is `true`
- `null` compared with `<`, `>`, `<=`, `>=` is a runtime error

---

## Path Resolution

Paths resolve against a **context object** provided by the calling
blueprint. Each consumer defines its own context roots:

### State Machine Context

| Root | Resolves To |
|------|-------------|
| `entity` | Current entity state fields |
| `transition` | Transition metadata: `from`, `to`, `trigger` |
| `now` | Current Unix epoch seconds (int64) |

Example: `entity.attempts < entity.max_retries AND entity.status != "cancelled"`

### Workflow Phase Context

| Root | Resolves To |
|------|-------------|
| `$task` | Original task request fields |
| `$phases` | Map of completed phase names → PhaseResult |
| `$entity` | Domain entity context |
| `$config` | Domain configuration (from trigger payload `config` field) |

Example: `$phases.scan.status == "success" AND $task.payload.force != true`

### ABAC Policy Context

| Root | Resolves To |
|------|-------------|
| `subject` | Authenticated user/agent attributes (roles, groups, email_verified) |
| `resource` | Target resource attributes (sensitivity, owner, type) |
| `context` | Request context (ip, time, method, path) |
| `environment` | Environment attributes (name, tier) |

Example: `subject.email_verified == true AND resource.sensitivity != "pii"`

### Storage Constraint Context

| Root | Resolves To |
|------|-------------|
| `row` | The record being validated |

Example: `row.priority IN ["critical", "high", "normal", "low"]`

---

## Operator Semantics

### Comparison Operators

| Operator | Types | Behavior |
|----------|-------|----------|
| `==` | any | Structural equality; `null == null` is true |
| `!=` | any | Inverse of `==` |
| `<`, `>`, `<=`, `>=` | number, string | Numbers: numeric order. Strings: lexicographic (Unicode code point) |
| `IN` | scalar, array | Left operand exists in right operand array |
| `NOT IN` | scalar, array | Left operand does not exist in right operand array |
| `CONTAINS` | string, string | Left string contains right string as substring |
| `STARTS_WITH` | string, string | Left string starts with right string |
| `ENDS_WITH` | string, string | Left string ends with right string |
| `MATCHES` | string, string | Left string matches right string as regex (RE2 syntax, no backtracking) |

### Logical Operators

| Operator | Behavior |
|----------|----------|
| `AND` | Short-circuit: if left is false, right is not evaluated |
| `OR` | Short-circuit: if left is true, right is not evaluated |
| `NOT` | Logical negation; operand must be boolean |

### Arithmetic Operators

| Operator | Types | Behavior |
|----------|-------|----------|
| `+` | number | Addition |
| `-` | number | Subtraction |
| `*` | number | Multiplication |
| `/` | number | Division (runtime error on divide by zero) |
| `%` | number | Modulo (runtime error on divide by zero) |

---

## Evaluation Rules

1. **No side effects** — expressions MUST NOT modify state, perform I/O,
   or call external functions
2. **Deterministic** — the same expression with the same context MUST
   always produce the same result
3. **Bounded execution** — implementations MUST limit expression depth
   (recommended: 32 levels) and path resolution depth (recommended: 16
   segments) to prevent resource exhaustion
4. **Missing paths resolve to null** — accessing a path that doesn't
   exist in the context returns `null`, not an error
5. **Short-circuit evaluation** — `AND` and `OR` MUST short-circuit
6. **MATCHES regex safety** — the `MATCHES` operator MUST use RE2 or
   equivalent non-backtracking regex engine to prevent ReDoS. Maximum
   regex length: 256 characters

---

## Error Handling

Expression evaluation errors are categorized:

| Error | Cause | Behavior |
|-------|-------|----------|
| `EXPR_PARSE_ERROR` | Malformed expression syntax | Reject at load/validation time |
| `EXPR_TYPE_ERROR` | Type mismatch (e.g., `"hello" > 5`) | Evaluate to `false` with warning log |
| `EXPR_DIVIDE_ZERO` | Division or modulo by zero | Evaluate to `false` with warning log |
| `EXPR_DEPTH_EXCEEDED` | Expression nesting exceeds limit | Evaluate to `false` with error log |
| `EXPR_REGEX_INVALID` | Invalid or unsafe regex pattern | Reject at load/validation time |

**Design principle:** Runtime evaluation errors default to `false`
(deny/skip) rather than throwing exceptions. This ensures that a
malformed guard doesn't crash the state machine or workflow engine.
Parse-time errors (syntax, invalid regex) MUST be caught at blueprint
load time.

---

## Security

```yaml
security:
  injection:
    - Expressions are parsed, not evaluated as code — no eval() or equivalent
    - String literals cannot contain expression syntax that would be re-parsed
    - Path resolution is bounded and cannot traverse outside the context object
  denial_of_service:
    - MATCHES uses RE2 (non-backtracking) to prevent ReDoS
    - Expression depth is bounded (32 levels)
    - Array literals are bounded (max 100 elements)
    - String literals are bounded (max 4096 characters)
  data_exposure:
    - Expressions cannot access system environment, file system, or network
    - Path resolution is scoped to the provided context only
```

---

## Implementation Notes

- **Compilation**: Expressions SHOULD be compiled to an AST at blueprint
  load time and evaluated against contexts at runtime. Re-parsing on
  every evaluation is wasteful but acceptable for low-volume paths.
- **Libraries**: Go implementations MAY use `expr-lang/expr` or
  `antonmedv/expr` (configure to disable function calls). Node.js
  MAY use `jsep` for parsing. Rust MAY use `pest` or hand-written
  recursive descent. Custom implementations are straightforward
  given the minimal grammar.
- **Testing**: Blueprint authors SHOULD test expressions with edge
  cases: null paths, empty strings, zero values, boundary conditions.
  The `weblisk-cli` provides `weblisk expr eval <expression> <context.json>`
  for interactive testing.
- **Backwards compatibility**: New operators may be added in minor
  versions. Existing operators will not change semantics.

---

## Verification Checklist

- [ ] All reserved words are case-sensitive (AND/OR/NOT uppercase, true/false/null lowercase)
- [ ] Operator precedence matches the table — parentheses override all precedence
- [ ] Path resolution returns null for missing paths instead of erroring
- [ ] Type mismatches in comparisons evaluate to false with a warning, not an exception
- [ ] `MATCHES` uses a non-backtracking regex engine (RE2 or equivalent)
- [ ] Expression depth is bounded at 32 levels; deeper expressions are rejected
- [ ] Array literals are bounded at 100 elements
- [ ] Division by zero evaluates to false with a warning
- [ ] Short-circuit evaluation: `false AND <error>` returns false without evaluating right side
- [ ] Parse errors are caught at blueprint load time, not at runtime
- [ ] Expressions cannot access state outside the provided context object
