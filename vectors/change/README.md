# Change and lock vectors

Changes ([`schemas/change`](../../schemas/change.md)) and build locks
([`schemas/build-lock`](../../schemas/build-lock.md)) as an implementation reads
them. [`expected.json`](expected.json) gives each file the schema it is read
against, whether it is valid, and for an invalid one the one rule it breaks;
every other rule holds in every file. `invalid-lock-roots.yaml` is the lock that
records roots, which only a run statement may.

Identity ids, run ids and digests here are shapes, not real keys or files, and
`example` is the namespace of the tenant they belong to.
[`checks/change-vectors.py`](../../checks/change-vectors.py) is one
implementation bound by these files; `weblisk validate` is to be the other
(lane `v2-cli-validate`).
