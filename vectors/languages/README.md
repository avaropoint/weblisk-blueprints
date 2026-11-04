# Language vectors

Real output of each language's toolchain, captured from the versions its
blueprint names (Go 1.27, Rust 1.93) on a two-error source and a two-test
file, with every path made relative to the tenant. `expected.json` is what
each language's declared `diagnostics` and `tests.result`
([`schemas/language`](../../schemas/language.md#the-diagnostics-block)) must
read from them: the findings, with file, line, column, symbol and kind, in
order, and each test's outcome. [`checks/language-blocks.py`](../../checks/language-blocks.py)
holds the grammars to them, so a grammar that drifts from what the toolchain
writes is reported here rather than in a repair loop.
