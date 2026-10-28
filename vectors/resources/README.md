# Resource vectors

Fixtures for [`checks/resources.py`](../../checks/resources.py), which holds
every Resources block to [`schemas/resource`](../../schemas/resource.md#rules).

| File | What it is |
|---|---|
| [`valid.md`](valid.md) | A small component declaring two kinds with every key the Shape names, binding one operation to its own endpoint table, with a state machine, a verb that fires its manual transition, and a relation. It gives no finding |
| [`invalid.md`](invalid.md) | One declared kind per rule, each breaking that rule and no other, so each finding names the rule it is for |
| [`invalid.expected.json`](invalid.expected.json) | The findings `invalid.md` gives, as kind and rule. The check also requires that every rule `schemas/resource` declares appears here, so a rule added without a vector fails |

The kinds are kinds [`schemas/kinds`](../../schemas/kinds.md#declared-kinds)
declares, used here only as names: nothing in these files is a declaration of
any of them.
