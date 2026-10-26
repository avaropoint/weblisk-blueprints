---
family: schemas/mapping@1
version: 1.0.0
axis: language
provides: fake
reserved_terms: [fakec, fake.toml]
---
# Language: Fake

A language mapping that exists only as a fixture. It has rules in nine of the
twelve concept classes and none in service, ui-unit or interface, so its
coverage report names exactly those three as UNFILLED.

## Rules

### Types

```yaml
rules:
  - id: type-integer
    concept: type/integer
    produce: {via: model, spelling: int64}
  - id: type-timestamp
    concept: type/timestamp
    produce: {via: model, spelling: int64, encode: epoch seconds}
    verify: [vectors/types.json#timestamp]
```

### Names and primitives

The backup signature has no answer yet, which is stated rather than left out;
the class is still filled, because its other rule answers.

```yaml
rules:
  - id: ident-field
    concept: identifier/field
    produce: {via: model, case: PascalCase}
  - id: primitive-canonical-json
    concept: identity-primitive/canonical-json
    produce: {via: model, package: fake/jcs, source: stdlib}
    verify: [vectors/types.json#canonical-json]
  - id: primitive-backup-signature
    concept: identity-primitive/backup-signature
    verdict: UNFILLED
    reason: No reviewed implementation has been named for this fixture.
```

### Checks, symbols and tests

```yaml
rules:
  - id: check-endpoint-routed
    concept: check/endpoint-routed
    evaluate: {argv: [fakec, check, --routes], parse: sarif}
  - id: extract-symbols
    concept: symbol/declarations
    extract: {argv: [fakec, symbols, --json], parse: json-lines}
  - id: test-unit
    concept: test/unit
    produce: {via: model, template: "test_{check}.fake"}
```

### Building

```yaml
rules:
  - id: lifecycle-build
    concept: lifecycle/build
    produce: {via: model, argv: [fakec, build]}
  - id: component-module
    concept: component/module
    produce: {via: generator, generator: fake/manifest, entry: fake.toml}
  - id: storage-default-backend
    concept: storage/default-backend
    verdict: IMPLEMENT
    refines: //test/platforms/fake:storage-default-backend
    produce: {via: model, package: fake/fs, source: stdlib}
```
