---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# Unclosed fence

A fence never closed runs to the end of the file, and nothing after its
opening line opens a slot.

## Requirements

```yaml
requirements:
  - id: fences-close
    level: must
    text: Every fence closes.
```

## Verification

```yaml
verifies:
  - id: unclosed-refused
    covers: [fences-close]
    assertion: The fence in the notes is refused as unclosed.
```

## Notes

```text
An example that was never closed.

## Operation: hidden

This heading is inside the fence, so it opens nothing.
