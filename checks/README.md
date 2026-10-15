# Checks

Small committed checks over the corpus that `weblisk validate` does not yet
make. Each reads the corpus from the directory it is given (default: this
repository), prints what disagrees, and exits non-zero when anything does.
None is specification, and no build's prompt carries one.

| Check | What it compares | Control |
|---|---|---|
| [`timestamp-wire.py`](timestamp-wire.py) | each `languages/` and `platforms/` mapping's `timestamp` row, applied to the instant in [`vectors/timestamp-wire.json`](../vectors/timestamp-wire.json), against the vector's wire value | `--control` rewrites `languages/go.md`'s row to milliseconds in memory and passes only if that one disagreement is reported |
