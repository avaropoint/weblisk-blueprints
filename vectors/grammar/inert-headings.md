---
family: vectors/grammar/test-blueprint@1
version: 1.0.0
---
# Inert headings

Lines that look like headings but are not ones: none of them opens a slot.

## Requirements

```yaml
requirements:
  - id: only-atx-headings
    level: must
    text: Only an ATX heading outside a fence or comment opens a slot.
```

## Verification

```yaml
verifies:
  - id: inert-lines-stay-notes
    covers: [only-atx-headings]
    assertion: Every line below stays in the notes slot.
```

## Notes

A setext heading is text.

Requirements
------------

    ## Requirements

##Requirements

<!--
## Verification
-->

The comment above holds a heading line, and it opens nothing.
