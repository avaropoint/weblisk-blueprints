# Check kinds

Examples of every check kind [`schemas/blocks`](../../schemas/blocks.md#checks)
declares for a component, and one invalid check for each rule
[`checks/check-kinds.py`](../../checks/check-kinds.py) holds.

| File | Holds |
|---|---|
| `valid.yaml` | One `verifies` entry of each component and client kind, `translated` included, and examples that between them use every assertion operator, act, harness role and expectation the vocabulary declares, each of which the check passes. `parts` names the requirement ids the examples cover, as if declared in their file |
| `invalid.yaml` | Cases, each a check and the fault it must be reported with, exactly once |

They are data, not a blueprint: nothing here is owed by a tenant. A kind, an
assertion operator, an act or a harness role added to the vocabulary without
an example in `valid.yaml` is reported.
