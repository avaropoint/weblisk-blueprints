---
name: operators
description: Create and use a Weblisk operator identity with the CLI — which identity signs, where it lives, and what holds its private half. Use when claiming a tenant, connecting Studio, or minting a token.
---

# Operators

Operator identity is `protocol/identity.md` and `architecture/admin.md`. This
skill is the command; `weblisk operator help` lists every flag. A passphrase is
never on argv: the CLI reads it from a prompt or stdin, and refuses it as a
flag.

## Default

```
weblisk operator init
weblisk operator connect --orch http://localhost:9800
```

One identity per account, reused for every tenant. With no identity named,
the key is an encrypted file in `~/.weblisk/keys/`, opened by a passphrase you
type. `tenant create` claims the first operator itself; every later one is held
at pending until an admitted operator runs `weblisk operator approve <name>`.

## Naming an identity

One machine may hold several identities, so name the one you mean:

```
weblisk operator init --identity alice --name alice
weblisk operator connect --identity alice --orch http://localhost:9800 --name alice
weblisk operator path --identity alice
```

A named identity lives in its own directory under `~/.weblisk/identities/`,
never in `~/.weblisk/keys/`. The CLI derives that directory from the label: do
not compute it, ask `operator path`. `--keys-dir <path>` names a location
outright and wins over `--identity`; with neither, `$WL_KEYS_DIR`, then
`~/.weblisk/keys/`.

`--identity` is which key signs; `--name` is what the hub records and other
operators see. They are often the same string and are not the same thing.
`weblisk tenant create --identity <label>` decides who administers that tenant,
permanently — a console serving several accounts must set it.

## What holds the private half

```
weblisk operator init --identity alice --holder <source> --holder-opt vault=<vault>
weblisk operator store --identity alice --holder <source> --reference <where>
```

`--holder` names a secret source to keep the private half instead of an
encrypted file; `--holder-opt key=value` (repeatable) is what that source needs,
and is never a secret, because it is on argv. `store` maps an identity a source
already holds. The sources this CLI reaches today are `file`, the default, and
`1password`. `--vault` and `--account` are one-release aliases for
`--holder 1password --holder-opt vault=…` and `--holder-opt account=…`.

An identity held by any source other than `file` keeps only `holder.json` and
`operator.pub` on disk, with no private key file. A source that keeps the
passphrase beside the key asks you for nothing. No source is allowed to store
an operator key unencrypted.

## Tokens

`connect`, `register` and `token --refresh` write the issued token beside the
identity. `--no-store` returns it instead, on stdout or in the `--json` result,
and writes nothing, for a caller that holds the token itself.

## Replacing

`init --force` makes a new identity, and every hub that attested the old one
must attest the new one. The replaced secret is left where it was, not
destroyed; retire it there once nothing depends on it. `operator rotate`
replaces the key pair in its source, and with `--orch` tells that hub.

Do not invent a second key store.
