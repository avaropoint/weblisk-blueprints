---
family: test-blueprint@1
version: 1.0.0
---
# Nested fences

Fences inside fences, and headings inside examples, open nothing.

## Requirements

```yaml
requirements:
  - id: keep-examples-inert
    level: must
    text: An example's contents are never read as the file's own.
```

## Verification

```yaml
verifies:
  - id: example-opens-nothing
    covers: [keep-examples-inert]
    assertion: The example below adds no slot and no block.
```

## Notes

A blueprint written to this family looks like this:

~~~markdown
## Types

```yaml
requirements:
  - id: not-a-requirement
    level: must
    text: Inside an example, so nobody's requirement.
```
~~~

A longer fence holds a shorter one of the same character:

````text
```
## Interface
```
````
