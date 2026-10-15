# Test vectors

Data, not specification. Each file here is something every implementation
tests against, and no blueprint requires one, so no build's prompt carries it.

| File | What it holds |
|---|---|
| [`fixed-form-statements.json`](fixed-form-statements.json) | For each prefix that has them, the field values, the exact signed bytes, the key and the signature of a [fixed-form statement](../protocol/identity.md#fixed-form-statements). The file's own `format`, `encodings` and `seeds` say how to read it |
| [`timestamp-wire.json`](timestamp-wire.json) | One instant and the value a protocol timestamp carries on the wire for it, by the convention in [`protocol/types`](../protocol/types.md#conventions). [`checks/timestamp-wire.py`](../checks/timestamp-wire.py) applies every language and platform mapping's `timestamp` row to it |
| [`ids.json`](ids.json) | Refs the [id grammar](../schemas/names.md#the-grammar) accepts, each with the fields it parses to, and refs it refuses, each with why. The file's own `format` says how to read it; [`checks/ids.py`](../checks/ids.py) is one implementation bound by it |
| [`grammar/`](grammar/README.md) | Files walked by [grammar 1](../schemas/family.md), each with the projection a walk of it must produce. [`checks/spans.py`](../checks/spans.py) confirms each projection partitions its file; a walker is bound by the rest |

What a vector key is, and that it is no one's identity, is stated once, in
[`protocol/identity`](../protocol/identity.md#fixed-form-statements). How a
build receives these files as test data is
[`architecture/generation`](../architecture/generation.md#published-test-vectors).
