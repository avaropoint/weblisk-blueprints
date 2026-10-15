# Checks

Small checks the corpus runs on itself, for rules no tool checks yet. Each one
reads its rules from the corpus file that states them and keeps no copy, and
each runs with a control: a case the check must fail, so that a check which
reaches nothing cannot pass.

```
checks/run.sh
```

runs them all and exits 0 only when every check passes and every control
fails. They need Python 3 and PyYAML. A check that cannot run fails; it never
passes for want of something to read.

| Check | What it holds the corpus to | Control |
|---|---|---|
| [`ids.py`](ids.py) | Every ref in [`vectors/ids.json`](../vectors/ids.json) parses as [`schemas/names.md`](../schemas/names.md#the-grammar) says, and reads back from YAML unchanged | A parser that accepts everything is reported on every invalid vector |
| [`names.py`](names.py) | No file names a namespace that is neither reserved nor this repository's own ([`schemas/names.md`](../schemas/names.md#where-a-namespace-may-appear)), and the vectors' families are the declared ones | A fixture naming an unreserved namespace is reported, once |
| [`retired.py`](retired.py) | [`RETIRED.md`](../RETIRED.md)'s entries: one per table row, in order, naming only spellings the row names, with a closed `match` vocabulary, paths that exist, patterns that compile, and no allowance whose `until` its file has reached. `--scan` also lists every place a retired spelling remains where its entry does not allow it; it reports and does not gate | A copy missing its last entry, and a copy whose allowance has ended, are each reported |
| [`timestamp-wire.py`](timestamp-wire.py) | Each `languages/` and `platforms/` mapping's `timestamp` row, applied to the instant in [`vectors/timestamp-wire.json`](../vectors/timestamp-wire.json), gives the vector's wire value | `--control` rewrites `languages/go.md`'s row to milliseconds in memory and passes only if that one disagreement is reported |
| [`reach-depth.py`](reach-depth.py) | The fabric's reach depth is stated as data in exactly one place, requirement `reach-max-depth` in [`architecture/fabric.md`](../architecture/fabric.md#requirements) (D23), `architecture/change-management.md` cites it, and every citation of it names a requirement that exists. A depth key counts only where it or an enclosing key names a walk, so a queue's or a nesting depth is not this number | A copy of `architecture/` whose change-management states `depth_limit: 10` again is reported with exactly two places; a copy adding a queue and a nesting depth still passes; a copy adding a traversal `max_depth` is reported |
| [`fabric-ledger.py`](fabric-ledger.py) | [`vectors/fabric-ledger.json`](../vectors/fabric-ledger.json) chains as [`architecture/fabric.md`](../architecture/fabric.md#the-ledger) says, checked with SHA-256 and an RFC 8785 canonicaliser alone: each entry's canonical line has the recorded digest, `seq` runs from 1, and each `previous_digest` follows. Each claim's relation is one [`schemas/kinds.md`](../schemas/kinds.md#relations) declares between its kinds, and an end whose kind is not versioned cites a projection. Every field a `cited_version` carries is one `architecture/fabric.md` binds `ContentIdentity` with, so a fabric generated from that binding reads the `projection` it compares on | A copy whose third entry is altered is reported with exactly one fault, at that entry; a copy whose provider end cites a bare version, and one relating code to a mapping rule by an undeclared relation, are each reported at that entry; a copy of `fabric.md` bound without `projection` is reported with exactly that field |
| [`digest-spelling.py`](digest-spelling.py) | Every blueprint sentence describing a SHA-256 as hex without the `sha256:` prefix is in a file [`patterns/content-identity.md`](../patterns/content-identity.md)'s digest-spelling rule names as a gap, and every file the rule names still writes one, so the list grows with a new bare-hex field and shrinks when a blueprint adopts the spelling. A key fingerprint keeps its own form and is not counted | A copy whose rule forgets `protocol/types` is reported with exactly that file |

A check here is temporary by design: when a tool implements the rule, the
check moves there and leaves this directory.
