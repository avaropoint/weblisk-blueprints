# Mapping vectors

Mapping files that exist only as fixtures, each with the coverage report
[`schemas/mapping`](../../schemas/mapping.md#coverage) says it must produce.
Their namespace is `test`, so no rule here is cited by anything a build makes.

| File | What it holds |
|---|---|
| [`fake-language.md`](fake-language.md) | A language mapping with rules in nine of the twelve concept classes: one rule refines a platform's, one is stated UNFILLED in a class another rule fills, and service, ui-unit and interface have none |
| [`fake-language.coverage.json`](fake-language.coverage.json) | Its coverage report: all twelve classes, exactly service, ui-unit and interface UNFILLED |

[`checks/mapping-coverage.py`](../../checks/mapping-coverage.py) produces the
report and compares it; `v2-cli-mapping` is bound by the same pair.

The fixture's `refines` target, `//test/platforms/fake:storage-default-backend`,
deliberately resolves to nothing. Coverage is a property of one file, so the
check asks only that a rule on a concept another axis owns carries `refines`;
whether the rule it names exists is a property of a target's composed
mappings, which no single-file fixture can show.

The fixture is here and not at `languages/fake.md`, where the plan first named
it: under `languages/` it would be published content, read by builds and held
to the neutral vocabulary, which a fake language is not.
