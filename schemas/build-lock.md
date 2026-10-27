# Schema: Build Lock

Which version of each input a tenant's builds resolved, and nothing else.

There is one lock per tenant, `.weblisk/build.lock`, written by the change
service when a change is applied and read by every plan
([`architecture/generation`](../architecture/generation.md#resolving-a-request-of-many-roots)).
An upgrade happens only through a change (`change plan --upgrade`, or an
explicit `@version`), so the lock moves only when a change is applied.

**It holds resolved versions only: no roots and no reasons.** Why an output
exists, and which roots it traces to, is its run statement's
([`schemas/run-statement`](run-statement.md)); `change plan --upgrade` takes
its roots from the latest statement of each component. A second record of roots
is a second home that drifts from the first.

---

## Shape

YAML, entries sorted by `ref`, one key order, so that two locks that resolve
the same versions are the same bytes and a diff shows only what moved.

```yaml
lock: 1
corpus: <revision the entries were resolved at>
blueprints:
  - ref: <blueprint ref>
    version: <resolved version>
    digest: sha256:<hex>
    source: <the source it was read from>
mappings:                       # each mapping rule in use
  - ref: <mapping rule ref>
    version: <version of its mapping file>
    digest: sha256:<hex>
adopted:                        # each adopted programme and standard transcription
  - ref: <ref>
    version: <version>
    digest: sha256:<hex>
```

## Rules

```yaml
rules:
  - id: lock-keys
    rule: the top-level keys are lock, corpus, blueprints, mappings and adopted, and an entry's keys are those its list shows; roots, why, reason and any other key are refused
  - id: lock-version
    rule: lock is 1
  - id: lock-entry
    rule: every entry has a ref in the grammar of schemas/names.md with no version, a version, and a digest written sha256:<hex>; a blueprint entry also has source
  - id: lock-unique
    rule: a ref appears once in its list
  - id: lock-sorted
    rule: each list is sorted by ref, by code point
```
