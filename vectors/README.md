# Test vectors

Data, not specification. Each file here is something every implementation
tests against, and no blueprint requires one, so no build's prompt carries it.

| File | What it holds |
|---|---|
| [`fixed-form-statements.json`](fixed-form-statements.json) | For each prefix that has them, the field values, the exact signed bytes, the key and the signature of a [fixed-form statement](../protocol/identity.md#fixed-form-statements). The file's own `format`, `encodings`, `seeds` and `bodies` say how to read it, and [`checks/fixed-form.py`](../checks/fixed-form.py) verifies every one with OpenSSL |
| [`timestamp-wire.json`](timestamp-wire.json) | One instant and the value a protocol timestamp carries on the wire for it, by the convention in [`protocol/types`](../protocol/types.md#conventions). [`checks/timestamp-wire.py`](../checks/timestamp-wire.py) applies every language and platform mapping's `timestamp` row to it |
| [`ids.json`](ids.json) | Refs the [id grammar](../schemas/names.md#the-grammar) accepts, each with the fields it parses to, and refs it refuses, each with why. The file's own `format` says how to read it; [`checks/ids.py`](../checks/ids.py) is one implementation bound by it |
| [`types.json`](types.json) | What a mapping's rules must give for the type vocabulary of [`schemas/blocks`](../schemas/blocks.md#types) and for canonical JSON: RFC 8785's own cases, a pointer to the one file holding the timestamp, and the entries whose value [`protocol/types`](../protocol/types.md#conventions) has not stated yet, marked pending. The file's own `format` says how to read it; [`checks/types-vectors.py`](../checks/types-vectors.py) is one implementation bound by it |
| [`mapping/`](mapping/README.md) | Mapping files that exist only as fixtures, each with the coverage report [`schemas/mapping`](../schemas/mapping.md#coverage) says it must produce |
| [`grammar/`](grammar/README.md) | Files walked by [grammar 1](../schemas/family.md), each with the projection a walk of it must produce. [`checks/spans.py`](../checks/spans.py) confirms each projection partitions its file; a walker is bound by the rest |
| [`fabric-ledger.json`](fabric-ledger.json) | A four-entry fabric ledger in the example namespace — a run statement's declared edges, an observed provider edge citing the projection digest of its configuration, and a person's confirmation — with the SHA-256 of each entry's RFC 8785 line, so any implementation of [the ledger](../architecture/fabric.md#the-ledger) can check its chain against it. The file's own `format` says how to verify it; [`checks/fabric-ledger.py`](../checks/fabric-ledger.py) is one implementation bound by it |

What a vector key is, and that it is no one's identity, is stated once, in
[`protocol/identity`](../protocol/identity.md#fixed-form-statements). How a
build receives these files as test data is
[`architecture/generation`](../architecture/generation.md#published-test-vectors).
