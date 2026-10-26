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
