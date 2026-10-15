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
| [`requirement-ids.py`](requirement-ids.py) | Requirement ids carried in `wl:id` comments, and the checklist items whose `wl:check` comments cover them: each id declared once in its file and every covers naming one of them; in a file marked `wl:ids complete`, every statement saying MUST carries an id and every id is covered. The corpus's migration turns both into requirement and `verifies` ids unchanged | The complete file with its last `wl:check` removed is reported, naming each id only that check covered |
| [`timestamp-wire.py`](timestamp-wire.py) | Each `languages/` and `platforms/` mapping's `timestamp` row, applied to the instant in [`vectors/timestamp-wire.json`](../vectors/timestamp-wire.json), gives the vector's wire value | `--control` rewrites `languages/go.md`'s row to milliseconds in memory and passes only if that one disagreement is reported |

A check here is temporary by design: when a tool implements the rule, the
check moves there and leaves this directory.
