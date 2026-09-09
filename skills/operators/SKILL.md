---
name: operators
description: Create and use a Weblisk operator identity with the CLI. Use when claiming a tenant, connecting Studio, or minting a token.
---

# Operators

Operator identity is `protocol/identity.md` and `architecture/admin.md`. This
skill is the command. The passphrase is never on argv.

## Default

```
weblisk operator init
weblisk operator connect --orch http://localhost:9800
```

One identity per account, reused for every tenant. `tenant create` claims
the first operator itself; later operators register and wait for admission.

## Override

```
weblisk operator init --name lloyd --force
weblisk operator connect --orch http://localhost:9800 --name lloyd
weblisk operator register --orch http://localhost:9800
weblisk operator token
```

`--force` regenerates the key and prints an identity-change warning. Do not
invent a second key store; keys live in `~/.weblisk/keys/`.
