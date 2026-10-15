# Test vectors

Data, not specification. Each file here is something every implementation
tests against, and no blueprint requires one, so no build's prompt carries it.

| File | What it holds |
|---|---|
| [`fixed-form-statements.json`](fixed-form-statements.json) | For each prefix that has them, the field values, the exact signed bytes, the key and the signature of a [fixed-form statement](../protocol/identity.md#fixed-form-statements). The file's own `format`, `encodings` and `seeds` say how to read it |

What a vector key is, and that it is no one's identity, is stated once, in
[`protocol/identity`](../protocol/identity.md#fixed-form-statements). How a
build receives these files as test data is
[`architecture/generation`](../architecture/generation.md#published-test-vectors).
