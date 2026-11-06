# Signer fixtures

What a signer must do with a pointer
([`protocol/identity`](../../protocol/identity.md#a-signer-acting-on-a-pointer)),
and what the engine must do with a `handoff` answer
([`architecture/engine`](../../architecture/engine.md#questions)), case by case.
Each `*.json` here is one fixture's `given`; [`expected.json`](expected.json)
lists every fixture once, with the rules it exercises and what must follow.
A conformance test of any signer reads both.

The keys are vector keys of [`../fixed-form-statements.json`](../fixed-form-statements.json),
named there — `identity`, `sign-records` and `hub` — and are no one's identity.
The hub's `hub_id` is the `hub` key's fingerprint and the person's identity id
is the `identity` key's. Signing is deterministic, so a signer given
`handoff-change-approve` with its clock set to the fixture's makes the
signature of the vector `change-decision-approve` byte for byte.

The owner serves each change as `GET /v1/admin/changes/{id}` does, with its
`plan_digest` beside the change's own fields. That is the digest a decision is
bound to ([`architecture/change-service`](../../architecture/change-service.md#verifying-a-decision));
how it is computed from a plan is not yet specified anywhere, so a signer
reads it as served and never computes one
([`SIGNING_PLAN.md`](../../SIGNING_PLAN.md), Status).

`records` says how the owner records a decision: `as-sent`, with the
signature and attestation it was sent, or `without-signature`, answering the
request as recorded while keeping neither.

[`checks/signer-vectors.py`](../../checks/signer-vectors.py) holds this
directory to the rules: every fixture listed once, every signer rule
exercised, every fixture a check names present, and the statement each
signing fixture expects rebuilt from the owner's change to its vector's bytes.
