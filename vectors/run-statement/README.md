# Run statement vectors

Run statements as an implementation reads them, for the actions and criteria
[`schemas/run-statement`](../../schemas/run-statement.md#actions) adds. Each
fixture is a statement as decoded from its DSSE envelope.
[`expected.json`](expected.json) gives each fixture whether it is valid and,
for an invalid one, the one rule of
[Rules for actions and criteria](../../schemas/run-statement.md#rules-for-actions-and-criteria)
it breaks; every other rule holds in every fixture.
[`criterion-digest.json`](criterion-digest.json) holds worked criterion
digests ([`architecture/engine`](../../architecture/engine.md#the-unit-is-a-criterion)).

Run ids, digests and model ids here are shapes, not real runs or files, and
`example` is the namespace of the tenant they belong to.
[`checks/run-statement-vectors.py`](../../checks/run-statement-vectors.py) is
one implementation bound by these files; the engine's record writer is to be
the other.
