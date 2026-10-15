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
| [`spans.py`](spans.py) | Every file in [`vectors/grammar/`](../vectors/grammar/README.md) has an expected projection, and each projection partitions its file: spans sorted, contiguous and covering `[0, length)`, at the file's own length and `version_hash` ([`schemas/family`](../schemas/family.md), `spans-partition`) | A copy whose projection leaves a one-byte gap is reported, once; a copy with a vector and no projection is reported; a directory with no vectors is reported |
| [`findings.py`](findings.py) | Every finding code [`schemas/family`](../schemas/family.md#definitions) declares has exactly one policy, fixed by its `finding` definition or left to the declaration, and every vector's findings carry that policy, in order of span start, then code, then subject (`findings-closed`); a declaration with CRLF line ends reads the same | A copy whose multi-root finding is only reported is reported, once; a copy whose missing-key finding is refused is reported, once; a copy of `family.md` that gives `multi-root` no policy is reported |
| [`refs.py`](refs.py) | Every `$ref` in a family declaration is `#/$defs/<name>` or `<ref>#/$defs/<name>` and resolves to an entry of that declaration's `defs` block ([`schemas/family`](../schemas/family.md), `schema-refs-resolve`) | A copy of the test declaration citing `blocks#/$defs/`, which names no file, is reported once per ref |

A check here is temporary by design: when a tool implements the rule, the
check moves there and leaves this directory.
