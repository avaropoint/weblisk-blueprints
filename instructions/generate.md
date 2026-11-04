---
family: schemas/instruction@1
version: 1.0.0
in: [generate]
---
# Generate a file

The output contract of a generated file: exactly one file and nothing else,
written to its plan entry, beside tests it may read and never write.

## Why

A convention requested in prose is honoured differently by different models,
and was the single largest source of unusable output
([`architecture/generation`](../architecture/generation.md#the-prompt-contract),
element 1). The tests are written before the code from the criteria alone
([`architecture/engine`](../architecture/engine.md#what-makes-a-translated-test-count));
a generator that may edit them can make any test pass.

## Text

```text
Answer with exactly one file: the file's content and nothing else. Write no
prose before or after it and no code fence around it; the first character of
your answer is the first character of the file. Write the file this plan
entry names, declaring and serving what the entry gives it.

The tests already written for this component are given to you to read. Do
not write a test, edit one, or change what one expects; if the file cannot
meet a test as it stands, write the file as the blueprints require.
```
