# Test vectors

Data, not specification. Each file here is something every implementation
tests against, and no blueprint requires one, so no build's prompt carries it.

| File | What it holds |
|---|---|
| [`fixed-form-statements.json`](fixed-form-statements.json) | For each prefix that has them, the field values, the exact signed bytes, the key and the signature of a [fixed-form statement](../protocol/identity.md#fixed-form-statements). The file's own `format`, `encodings` and `seeds` say how to read it. [`checks/ml-dsa`](../checks/ml-dsa/main.go) makes it with circl, and every signature is verified with OpenSSL ([`checks/statements.py`](../checks/statements.py)), circl and `@noble/post-quantum` ([`checks/ml-dsa`](../checks/ml-dsa/noble.mjs)) |
| [`timestamp-wire.json`](timestamp-wire.json) | One instant and the value a protocol timestamp carries on the wire for it, by the convention in [`protocol/types`](../protocol/types.md#conventions). [`checks/timestamp-wire.py`](../checks/timestamp-wire.py) applies every language and platform mapping's `timestamp` row to it |
| [`ids.json`](ids.json) | Refs the [id grammar](../schemas/names.md#the-grammar) accepts, each with the fields it parses to, and refs it refuses, each with why. The file's own `format` says how to read it; [`checks/ids.py`](../checks/ids.py) is one implementation bound by it |
| [`grammar/`](grammar/README.md) | Files walked by [grammar 1](../schemas/family.md), each with the projection a walk of it must produce. [`checks/spans.py`](../checks/spans.py) confirms each projection partitions its file; a walker is bound by the rest |
| [`namespace-registry.json`](namespace-registry.json) | Sequences of claims, grants, transfers, catalog releases, rulings and revocations at one [namespace registry](../patterns/namespace.md#deciding-a-statement), and verifications of releases against its log ([Verifying a release](../patterns/namespace.md#verifying-a-release)), each step with its verdict and each sequence with the state it leaves; its keys are `fixed-form-statements.json`'s, and its signatures are made by [`checks/ml-dsa`](../checks/ml-dsa/main.go) from each statement's own fields. The file's own `format` says how to read it; [`checks/namespace-registry.py`](../checks/namespace-registry.py) is one implementation bound by it |
| [`fabric-ledger.json`](fabric-ledger.json) | A four-entry fabric ledger in the example namespace — a run statement's declared edges, an observed provider edge citing the projection digest of its configuration, and a person's confirmation — with the SHA-256 of each entry's RFC 8785 line, so any implementation of [the ledger](../architecture/fabric.md#the-ledger) can check its chain against it. The file's own `format` says how to verify it; [`checks/fabric-ledger.py`](../checks/fabric-ledger.py) is one implementation bound by it |

What a vector key is, and that it is no one's identity, is stated once, in
[`protocol/identity`](../protocol/identity.md#fixed-form-statements). How a
build receives these files as test data is
[`architecture/generation`](../architecture/generation.md#published-test-vectors).
