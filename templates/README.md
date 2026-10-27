# Templates

The starting file of each family that names one. A family declaration's
`template:` ([`schemas/family`](../schemas/family.md#the-grammar-keywords))
points here, and a new file of that family is begun from a copy. A template is
a file of its family like any other: it walks against the declaration with no
finding ([`checks/families.py`](../checks/families.py) `--templates` holds each
to that), and where a copy of it is in [`vectors/grammar/`](../vectors/grammar/README.md),
that copy holds the projection a walk of it gives.

| Template | Family |
|---|---|
| [`architecture.md`](architecture.md) | [`schemas/architecture`](../schemas/architecture.md), architecture blueprints |
| [`programme-map.md`](programme-map.md) | [`schemas/programme-map`](../schemas/programme-map.md), a programme's map |
| [`programme-spec.md`](programme-spec.md) | [`schemas/programme-spec`](../schemas/programme-spec.md), a programme's artifact specifications |
| [`programme-template.md`](programme-template.md) | [`schemas/programme-template`](../schemas/programme-template.md), a programme's blank forms |
| [`policy.md`](policy.md) | [`documents/families/policy`](../documents/families/policy.md), an organisation's policies |
| [`procedure.md`](procedure.md) | [`documents/families/procedure`](../documents/families/procedure.md), an organisation's procedures |
| [`standard.md`](standard.md) | [`documents/families/standard`](../documents/families/standard.md), an organisation's own standards |
| [`guideline.md`](guideline.md) | [`documents/families/guideline`](../documents/families/guideline.md), an organisation's guidelines |
| [`protocol.md`](protocol.md) | [`schemas/protocol`](../schemas/protocol.md), protocol blueprints |
| [`pattern.md`](pattern.md) | [`schemas/pattern`](../schemas/pattern.md), pattern blueprints |
| [`agent.md`](agent.md) | [`schemas/agent`](../schemas/agent.md), agent blueprints |
| [`domain.md`](domain.md) | [`schemas/domain`](../schemas/domain.md), domain controller blueprints |
| [`position.md`](position.md) | [`schemas/position`](../schemas/position.md), position guides |
| [`policy-domain.md`](policy-domain.md) | [`schemas/policy-domain`](../schemas/policy-domain.md), policy domain commentary |

The language, platform and framework families have no template: they declare
the older form their files are read as until each is rewritten into rules, and
a new file of any of the three is written to
[`schemas/mapping`](../schemas/mapping.md).
