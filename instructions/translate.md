---
family: schemas/instruction@1
version: 1.0.0
in: [translate]
slots: [criterion, contract, plan-names, language-test]
---
# Translate a criterion into a test

How one criterion becomes one executable test, written from the criterion
and the declared contract alone, before any implementation exists.

## Why

A test the generator wrote beside its own code proves only that the two
agree. On the development tenant's last rebuild, 10 of its 12 test files
tested code that regeneration had since replaced, and a model's reading
settled at least 281 of 284 "satisfied" checklist items with nothing run
([`ENGINE_PLAN.md`](../ENGINE_PLAN.md#the-problem-measured)). A test counts
only when it was written apart from the code and fails against nothing
([`architecture/engine`](../architecture/engine.md#what-makes-a-translated-test-count)),
so this instruction gives the model the criterion and the contract and no
implementation, and forbids it from inventing one.

## Text

```text
Write one test for one criterion, before any implementation of it exists.
You are given the criterion, the contract it is stated against, the names the
plan fixes, and how a test is written in this language. You are given no
implementation, and you must not assume one beyond what these declare.

The criterion: {{criterion}}

The contract: {{contract}}

The names the plan fixes: {{plan-names}}

How a test is written in this language, and where this one goes:
{{language-test}}

The test passes exactly when what the criterion states holds, and fails when
it does not. Test what the criterion states and nothing else: do not weaken
it, do not add to it, and where it is silent do not decide what an
implementation would do. Use only the names the contract and the plan give
you. Begin the test with the header the language declares, carrying the
criterion's id and digest exactly as given. Answer with the test file alone:
no prose before or after it, and no code fence around it.

If no test can settle the criterion from what you are given, because it
states nothing a test can observe, do not write a test that passes anyway:
answer with a corpus finding of kind untestable instead of the test.
```
