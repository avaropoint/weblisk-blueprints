# Signing from a console

> **Status: proposal, awaiting the owner's decision. Nothing here is adopted.**
> No blueprint, schema, check, vector or tool follows it yet. It sits at the
> corpus root, beside [`ACCEPTANCE_PLAN.md`](ACCEPTANCE_PLAN.md), and not under
> `architecture/` or `protocol/`, because a file there is a blueprint and its
> MUST lines are read as requirements: a proposal placed there would be
> normative by placement. Where each part would live once decided is
> [What changes where](#what-changes-where), and the choices that are the
> owner's are [Decisions](#decisions).
>
> Written 2026-11-05 at corpus `5164201`.

---

## The gap

A person's decision on a change is a `weblisk/change-decision/v1` statement
signed by their **sign-records credential**
([`architecture/change-service`](architecture/change-service.md#verifying-a-decision)).
A content change and an entry attestation may carry the same kind of signature
([`architecture/content`](architecture/content.md#the-change-statement),
[Entry attestations](architecture/content.md#entry-attestations)). And a console
— Studio — may never hold one
([`architecture/admin`](architecture/admin.md#contracts), `console-no-sign-records`).

What that breaks today, act by act:

| Act | At the CLI | At Studio today | Why |
|---|---|---|---|
| `change approve`, `change reject` | signed | **cannot be made** | An unsigned decision is no decision (change-service, Approval) |
| content proposal decision (`approval accept`) | signed or witnessed | witnessed only | A statement is optional; without one the approver is `witnessed` |
| content direct write | signed or witnessed | witnessed only | as above |
| `attest` | witnessed | witnessed | `weblisk/content-attestation/v1` has no test vectors, so **nobody** may sign one yet |

So the hard break of front-end parity
([`architecture/engine`](architecture/engine.md#parity-the-cli-and-studio-are-interchangeable),
`front-end-parity`) is the change decision. The other three are a difference
in evidence, not in reach: Studio can make them, but only as `witnessed`. This
plan closes all four the same way.

---

## The three questions

Every mechanism below is judged by what it answers. A signature on a record is
worth exactly the answers it gives to these three, and to no others.

1. **Whose key made it?** Only the person's own, generated where they sign and
   held by nothing that acts for other people (principal-identity,
   `record-signing`). A key a console holds signs whenever the console does.
2. **Who chose the bytes?** The person, looking at what will be signed on a
   surface the console cannot draw. A signature over bytes the person never saw
   proves that their key was used, not that they decided anything. This is the
   question the corpus already answers for programs — *nothing offers to sign
   a caller's bytes* ([`protocol/identity`](protocol/identity.md#fixed-form-statements))
   — and it has to be answered for the person too.
3. **Does it outlast its algorithm?** A record is read for years. A signature
   that anyone can forge once its curve falls is evidence only until then
   (principal-identity Design Principle 6; content, *Design Principle 6,
   strictly*).

And of the console, which carries the person's request: **can it forge,
alter, replay or quietly drop a signature?**

---

## What already exists

Nothing below is new. The design is built from it.

| Piece | Where | What it answers |
|---|---|---|
| sign-records credential: ML-DSA-65 key file, attested by the identity, capped at 90 days, revocable, never authenticates | principal-identity `record-signing`; admin `operator-credential-attestation` | Q1 and Q3 |
| `record_keys` on every operator token, and check 4: the signing key is one the token names and not its `cid` | admin `operator-token-issuance`; content checks 1–6; change-service checks 1–6 | the hub vouches the key is live *now*; revocation reaches a verifier through tokens |
| The service rebuilds the statement and never takes one | content, change-service | a signature never attaches to bytes its signer did not sign |
| Nothing offers to sign a caller's bytes | protocol/identity | a signer is not an oracle for whoever can reach it |
| Step-up passkey: a WebAuthn assertion whose challenge is a fixed-form statement | admin `step-up-passkey-form` | presence of the person, for a session; signs nothing kept |
| The engine's `question` of kind `signature`, answered in the CLI's pane or Studio's dialog | engine, Questions | how an operation asks for a signature in both front ends |
| A client that sent a statement checks the record carries it | content, The change statement | a dropped statement is reported, not silently witnessed |

---

## The options

| | Q1 whose key | Q2 who chose the bytes | Q3 outlasts its algorithm | Console can … |
|---|---|---|---|---|
| **(a)** Passkey assertion over the statement | the person's authenticator | **the console** — it is the relying party and supplies the challenge | **no** — ES256 / EdDSA | not forge; can choose what one touch signs |
| **(b1)** Device signer; console relays the signature | the person's | the signer, if it resolves the fields itself | yes — ML-DSA-65 | not forge; **can drop** a content statement and send the act unsigned |
| **(b2)** Device signer acts; console hands off and watches — **proposed** | the person's | the signer, which reads every field from the owner and shows it | yes — ML-DSA-65 | not forge, alter, replay or drop: it never carries the signature |
| (c1) ML-DSA key in the browser, wrapped by a passkey's PRF output | the console's, in substance | the console | yes | **sign** — it serves the JavaScript that unwraps the key |
| (c2) Remote signing: the hub holds a per-person key, a passkey unlocks it | the hub's | the hub | yes | — but the hub signs whenever it chooses to |
| (c3) A passkey whose COSE key is ML-DSA-65 | the person's authenticator | the console, as (a) | yes | as (a) |

**(c1) and (c2) are refused by rules the corpus already has.** Each is a key
held by a party that acts for people who sign in to it, which `record-signing`
forbids and `console-no-sign-records` forbids for a console. A wrapped key is
still held: the console serves the code that unwraps it, so a compromised
console serves code that keeps it. Remote signing is how some legal regimes
build server-side qualified signatures, and it works there because a certified
custodian is trusted to sign only when asked. The corpus's model has no such
custodian and does not want one: the hub is the party whose word `witnessed`
already is, and a signature it can make adds nothing to that word.

**(c3) is the future of (a), not a fix for it.** ML-DSA has a draft COSE
registration and few authenticators implement it. When they do, a passkey
answers Q3, and Q2 stays as it is in (a): an authenticator shows which site is
asking, never what it is being asked to sign.

### (a) in full, because it is the obvious one

The step-up passkey already makes a WebAuthn assertion whose challenge is a
fixed-form statement's bytes, so a passkey-signed decision is one line away.
This is what such a record would prove, and what it would not.

**What the record would carry**, for an offline verifier: the statement's
fields; the passkey's COSE public key and its algorithm; `rp_id` and `origin`;
`authenticator_data`, `client_data_json` and `signature`; and the identity's
ML-DSA attestation binding that COSE key to the person, with `purpose` naming
it. The verifier rebuilds the statement, checks that `client_data_json`'s
`challenge` is its base64url, its `type` is `webauthn.get` and its `origin` is
the attested one; that `authenticator_data`'s `rpIdHash` is the SHA-256 of
`rp_id` with user-present and user-verified set; and that `signature` verifies
over `authenticator_data ‖ SHA-256(client_data_json)`.

**What a verified ES256 or Ed25519 assertion proves, today:** an authenticator
holding the private half of a key the person's identity bound to them, which
reported verifying its user, produced these bytes for a page at the console's
origin. The binding is ML-DSA, so nobody can bind a new key to the person.

**What it does not prove:**

- **That the person saw the statement.** The challenge is opaque to the person.
  The authenticator's prompt names the site, and the page around it is the
  console's own. A console that shows *approve change A* and asks for an
  assertion over *approve change B* gets one, with the person's touch. The
  passkey answers "was the person there?" and not "what did they decide?".
  That is why the corpus uses it for step-up, where the token carries only a
  time, and nowhere else.
- **That it is still unforgeable once its curve falls.** The COSE public key is
  listed to every viewer. Whoever can solve ECDLP for it can make assertions
  over any statement, with any `signed_at`. Inside a sealed log the entry is
  protected by the log's ML-DSA seal: a forged assertion cannot be inserted at
  a past position. Outside the log — an export, an audit package, a copy of a
  change file — nothing tells a genuine assertion from a forged one. The record
  is then as strong as the seal of the service that kept it, which is exactly
  what `witnessed` already means.
- **That only one device holds the key.** A synced passkey exists on every
  device its account syncs to; the hub saw no registration ceremony, so it
  records `device_bound: false` (admin).
- **Which authenticator it was.** No attestation statement reaches the hub, so
  the user-verified flag is the authenticator's own report.

**Its weight as evidence.** The corpus's standings are evidentiary, not legal.
`signed` means a party other than the service can check that the person's key
made the signature over these bytes; `witnessed` means the service says so,
under its seal ([`architecture/content`](architecture/content.md#verifying-a-log-without-this-service)).
A passkey assertion would be neither: stronger than `witnessed` against a
dishonest *service* until its curve falls, no stronger against a dishonest
*console*, and no stronger than `witnessed` afterwards. Whether any of these is
an electronic signature with legal effect is a question for the places the
tenant's standards bind in (`applies_in`) and for the tenant's counsel, and the
corpus asserts no legal status for any of them. Two properties that regimes
grading signatures commonly ask for — sole control of the means of signing, and
that a later change to the data is detectable — are met by (b2) for as long as
ML-DSA holds, and by (a) only until its curve falls. Neither is a qualified
signature: that needs a qualified certificate and device the corpus does not
specify.

So (a) would weaken Q2 and Q3 to give the console a one-touch flow. Admitting
it as `signed` contradicts Design Principle 6 and content's *strictly*, which
says a passkey assertion *"never makes a party `signed`"*. Whether to admit it
as something else is [decision D1](#decisions).

---

## The design: the person's signer acts, the console hands off

**One sentence:** the console never builds, carries or sends a record
statement; it shows the person a pointer to the act, the person's own signer
reads everything the statement holds from the tenant, shows it, signs it with a
sign-records key on that device and submits the act itself, and the console
watches the tenant's record for the result.

```
 console (Studio)                    signer (the CLI, on the person's device)        owner (change-service / content)
 ────────────────                    ────────────────────────────────────────        ───────────────────────────────
 engine: change approve <id>
   └ question: signature
 dialog shows the pointer  ──────►  person runs / opens it
   weblisk sign <hub_id>             resolve hub_id → its recorded registration
     change-approve <change id>      GET the change on its OWN token  ─────────────►  the change, its plan_digest
                                     show: title, roots, entries, plan_digest,
                                           position, decision
                                     person confirms HERE
                                     build weblisk/change-decision/v1 itself
                                     sign with the sign-records key on this device
                                     POST …/decision on its own token  ────────────►  rebuild bytes, checks 1–6, record
                                     read back: the record carries the signature ◄──  200, the change
 watch the feed / re-read  ◄───────────────────────────────────────────────────────  change: approved, by, signature
 answer the question: handoff → engine reads the record → finished
```

### The signer

A **signer** is a program on the person's own device that holds that person's
sign-records credential for one hub and makes the acts that need it. The CLI is
the first. A desktop or phone signer is another, held to the same rules; none
is specified here.

- **S1. It holds its own credentials.** It generates its sign-records key on
  the device, has the person's identity attest it, and keeps it as the CLI
  keeps an authenticate credential (keychain, else the `weblisk-key-v1`
  envelope or the identity's secret source). It also holds its own authenticate
  credential at the hub, so it reads and acts on its own token, never on a
  token or a body the console hands it.
- **S2. It takes a pointer, never bytes.** What it is given names an
  operation of the engine's catalogue and that operation's arguments: the
  hub, the operation, and the ids of what it acts on. Never a digest, a
  statement, a signature, a plan or a document's bytes.
- **S3. It reads every field from the owner.** `plan_digest`, `before`,
  `after`, `version`, `covers_digest`, `approver_position` — each is read on
  the signer's own token from the service that holds it, or chosen by the
  person at the signer (the decision, a rejection's reason, an attestation's
  words). `signed_at` is the signer's clock. This is `protocol/identity`'s
  *nothing offers to sign a caller's bytes*, applied to the person: the bytes
  are built from what the signer itself read and showed.
- **S4. The person confirms on the signer's own surface.** Before signing it
  shows what it read — for a change, its title, roots, entries and
  `plan_digest` (short form), and the decision and position — and signs only
  on the person's answer there. A key unlock that shows nothing, such as a
  keychain item or a vault approval, is presence, not this confirmation; it may
  follow it, never replace it.
- **S5. It is never driven.** It MUST NOT take a `signature` answer, a
  confirmation or a key unlock from the program that started it: not from
  stdin under `--json`, not from a pseudo-terminal another program holds, not
  from an environment variable or a flag such as `--yes`. Its confirmation is
  read from the terminal or window the person sees. (The parity harness runs
  the CLI under a pseudo-terminal with vector keys, which are no one's
  identity; a vector key is never accepted outside tests, as `protocol/identity`
  already requires.)
- **S6. It submits, and checks.** It sends the act to the owner itself, on its
  own token, and reads back that the record carries its signature. Where it
  does not — content may record the act `witnessed` — it says so to the person.
  This is the rule content already gives *a client that sent a statement*; the
  signer is now the only client that does.
- **S7. It refuses a hub it does not know.** The pointer's `hub_id` must be a
  registration the signer recorded. A pointer for any other hub is refused
  `not_registered`, never followed to an address the pointer names.

### The pointer

```
weblisk sign <hub_id> <operation> <argument>...

  <hub_id>     the hub's hub_id, 64 lowercase hex
  <operation>  an operation of the engine's catalogue that needs a signature,
               its words joined by '-': change-approve, change-reject,
               approval-accept, approval-reject, attest
  <argument>   that operation's arguments as the manifest names them: a change
               id, a decision id, an entry path, version and span
```

The same text is offered as a `weblisk://sign/<hub_id>/<operation>/<argument>...`
link for a signer that registers the scheme, and as a QR code of that link for
a signer on another device. All three are the same pointer. A pointer is not a
secret and authorises nothing: whoever holds one can only make the signer
*show* something to its person.

### What the console does

- **K1.** On an engine `question` of kind `signature`, it shows the pointer for
  that operation and nothing it could sign. Beside it, it shows the short form
  of what the signer will show — the change id and `plan_digest` prefixes — so
  the person can compare the two screens.
- **K2.** It never builds, holds, carries or sends a statement whose *Signed
  by* is a person's sign-records credential, and never sends the act that
  carries one. Its source holds none of those prefixes (a declared check).
- **K3.** It never starts a signer non-interactively, and never drives one
  through a pseudo-terminal, a pipe or a flag (S5, bound on the console as
  `console-not-a-component` binds it).
- **K4.** It watches the owner's feed, or re-reads the record, for the act by
  this person on this subject. On seeing it, it answers its invocation's
  `question` with `handoff` and the record's ref. If the person declines, or
  cancels in the dialog, the question is unanswered and the operation ends
  refused naming it (engine, `unanswered-is-refused`).
- **K5.** For a content write the person wants signed, it files a proposal
  instead, and hands off its decision. A direct write from the console stays
  `witnessed` ([D6](#decisions)).

### The engine

The `signature` question gains one answer form, `handoff`: *the act was made by
the person's signer, and here is the owner's record of it.* The engine does not
take the answer's word. It reads the record at its owner, on the console's
token, and ends the operation `finished` with that record only where the record
is of the operation and subject the question was `about`, its signer is the
pass's `identity_id`, and its standing is `signed` — for a change, an
`approval` or `rejection` whose `signature` and `attestation` are present.
Otherwise the operation ends refused naming the question. The `records` of the
finished event are the same in both front ends, which is what parity compares.

### What the record carries

**Nothing changes.** The record is the one the signer's act makes, exactly as
the CLI makes it today: on a change, `approval` or `rejection` with `by`,
`signature`, `plan_digest`, `at` and the `attestation` (schemas/change); on
content, the `ChangeStatement` or `AttestationSignature` with its attestation.
An offline verifier checks it as content's *Verifying a log without this
service* and change-service's six checks already say: the attestation's
identity signature and `purpose` `sign-records`, its `not_after` against the
record's time, its `hub_id` against the tenant's, and the ML-DSA-65 signature
over the statement it rebuilds. A record made through a console is
indistinguishable from one made at the CLI, because it *is* one made at the CLI.

### Registration

- The signer generates one ML-DSA-65 sign-records key per hub, on the device,
  the first time it is asked to sign for that hub, or at `operator connect`
  where the person asks for one there.
- The person's identity attests it through the existing route with `purpose`
  `sign-records` (admin, *Attesting a credential*), in the same approval as the
  device's authenticate credential where both are new (`operator attest
  --batch`). Default `not_after` 30 days, cap 90, warn at 7, as every
  credential. The hub records `form` `key-file`, `device_bound` `false`.
- From then on every operator token the hub mints for the person — the
  console's included — names it in `record_keys`, which is how the owner learns
  it is live. The console learns that the person *can* sign, never the key.
- More than one signer per person is allowed: each device has its own key, and
  `record_keys` lists them all.

### Revocation and loss

- Revoking a signer's key is the existing credential revocation (admin,
  *Revoking a credential*). It drops out of every token minted afterwards, so
  check 4 refuses it within an hour, and an offline verifier has `not_after`
  as its window (record-signing). Nothing already recorded changes.
- A lost device costs its two credentials, authenticate and sign-records, at
  each hub. The person, or an admin, revokes both from the console or from
  another device. The sign-records one is never counted by
  `OPERATOR_LAST_ADMINISTRATOR`; the authenticate one is, as today.
- A changed identity key revokes every credential the operator holds, sign-records
  ones included (admin `operator-key-change`), so every signer re-attests.

### How `console-no-sign-records` stays true

It is true trivially and checkably. The console generates no sign-records
key (S1 puts generation on the signer), holds none (K2: it never even holds a
signature), and never asks an identity to attest one (the signer's own
identity approval does, on the signer's device). The rule needs no change; the
plan adds K2 and K3 beside it, because a console that drove a signer silently
would sign whenever the console did — the very thing the rule exists to stop —
while holding no key at all.

### What it costs, honestly

- **Two screens.** The person confirms on the signer, not in the console. That
  is the point (Q2), and it is a step more than a passkey touch.
- **The defence is only as good as the person's reading of the signer.** A
  pointer to the wrong change is caught only if they read what the signer
  shows. K1's short-form comparison helps an honest mistake; against a
  dishonest console the signer's own display is the defence, and it is.
- **The key is a file, not a chip.** A sign-records key file is unlocked by the
  vault or passphrase that protects it, and malware on an unlocked device can
  sign with it. A passkey would resist that better. No common secure element
  holds ML-DSA-65 today; when one does, the signer can keep its key there with
  no change to the record ([D7](#decisions)).
- **No unattended signing.** A schedule or an agent can never make a signed
  act. That is already the corpus's rule (admin `console-no-unattended-work`;
  an agent is never a principal), and this plan keeps it.

---

## Threats

Proposed rows for [`architecture/threat-model`](architecture/threat-model.md),
Admin-Specific Threats, numbered after 4.9.

| # | Attack | Mitigation | Residual |
|---|---|---|---|
| 4.10 | **Console substitutes what is signed** — shows change A, asks for change B | The signer takes a pointer, reads B from the owner and shows B (S2–S4); the console carries no bytes to substitute | A person who confirms without reading the signer's screen approves B |
| 4.11 | **Console downgrades a signed act to witnessed** — drops the statement and sends the act unsigned | The console never carries the statement or sends the act (K2); the signer submits and reads back (S6) | none at the console; a dishonest content service could still record `witnessed`, which the signer reports |
| 4.12 | **Console drives the signer** — starts it with `--yes`, answers its prompt through a pseudo-terminal | The signer reads its confirmation only from the person's own surface (S5); a console that drives one breaches K3, and its source is checked for it | A console with full control of the person's desktop session can type into a terminal; that is the device, not the console, compromised |
| 4.13 | **Pointer phishing** — a link or QR pointing at an act the person did not mean | A pointer authorises nothing; the signer shows what it read and refuses an unknown hub (S7) | as 4.10 |
| 4.14 | **Sign-records key file theft** | Encrypted at rest under the person's vault or passphrase; 90-day cap; revocation drops it from `record_keys`; listed at the hub so a key nobody recognises is visible | A thief with the key and its unlock signs as the person until revocation; each act is audited and attributed |
| 4.15 | **Retroactive forgery after a classical break** | Every record signature is ML-DSA-65; no passkey assertion is ever a record signature | none from this mechanism |

---

## Vectors and fixtures

No new statement is proposed, so no new prefix and no new ML-DSA vector is
needed for (b2). What it needs, with ids minted here:

**Statement vectors** (`vectors/fixed-form-statements.json`, made by
`checks/ml-dsa` `go run . gen`, verified by circl, OpenSSL and noble):

| id | what |
|---|---|
| `content-attestation-entry` | `weblisk/content-attestation/v1` covering a whole entry, no request |
| `content-attestation-span-answering-request` | the same covering a span, answering an attestation request, two statement words sorted |

These are the vectors whose absence makes every attestation `witnessed` today,
at the CLI as well. They wait on [D5](#decisions): the `<statements>` field's
words have no corpus home yet (engine catalogue, `attest`, *undriven*), and a
vector pins a layout for good.

**Signer fixtures**, a new `vectors/signer/` directory with an `expected.json`,
read by a conformance test of any signer:

| id | given | expected |
|---|---|---|
| `handoff-change-approve` | a pointer for a planned change at a registered hub | the signer reads the change, shows its `plan_digest`, and the statement it signs rebuilds from the change as the hub holds it |
| `handoff-pointer-carries-digest` | a pointer with an extra `plan_digest` argument | refused: a pointer carries no digest (S2) |
| `handoff-unknown-hub` | a pointer naming a `hub_id` with no recorded registration | refused `not_registered`, nothing read or sent (S7) |
| `handoff-driven-confirmation` | the confirmation supplied on stdin under `--json` | refused; nothing signed (S5) |
| `handoff-recorded-witnessed` | an owner that records the act without the statement | the signer reports the act unsigned (S6) |
| `handoff-answer-wrong-subject` | a `handoff` answer whose record is another change's | the console's operation ends refused naming the question |

**If D1 admits passkeys** in any form, it needs its own vectors, which are not
ML-DSA and so are not made by `checks/ml-dsa`: `change-decision-passkey-es256`
and `change-decision-passkey-eddsa`, each a fixed seed, the statement bytes, a
`client_data_json`, `authenticator_data` and signature, verified with OpenSSL.

---

## Declared checks

Proposed, with ids minted. Each names the requirement ids it covers, which are
minted with it.

| check id | kind | assertion | covers |
|---|---|---|---|
| `console-builds-no-record-statement` | structure, over the console's source | No string literal equals a prefix whose *Signed by* in protocol/identity's registry is a person's sign-records credential (`weblisk/content-change/v2`, `weblisk/content-attestation/v1`, `weblisk/change-decision/v1`), the list read from the registry, never copied | `console-hands-off-signing`, `console-no-sign-records` |
| `console-drives-no-signer` | structure, over the console's source | No invocation of the CLI names an operation that needs a signature, and none passes a confirmation flag | `console-never-drives-signer` |
| `signer-reads-every-field` | test, against the signer fixtures | `handoff-change-approve` and `handoff-pointer-carries-digest` | `signer-takes-a-pointer`, `signer-builds-from-what-it-read` |
| `signer-own-surface` | test | `handoff-driven-confirmation` | `signer-never-driven` |
| `signer-known-hub` | test | `handoff-unknown-hub` | `signer-known-hub` |
| `signer-checks-record` | test | `handoff-recorded-witnessed` | `signer-submits-and-checks` |
| `handoff-answer-verified` | test, both front ends | `handoff-answer-wrong-subject`; a correct `handoff` ends with the same `records` as the CLI's run | `signature-handoff-answer`, `front-end-parity` |
| `console-holds-no-sign-records` | existing (admin) | unchanged | `console-no-sign-records` |

---

## What changes where

| Where | Change |
|---|---|
| `protocol/identity` | A new section, **A signer acting on a pointer**, with S1–S7 as rules and ids `signer-takes-a-pointer`, `signer-builds-from-what-it-read`, `signer-own-surface-confirms`, `signer-never-driven`, `signer-submits-and-checks`, `signer-known-hub`; the pointer grammar. The two attestation vectors once D5 is settled, and the list of prefixes with vectors updated |
| `architecture/admin` | `console-credential-use` gains `console-hands-off-signing` (K1, K2, K4) and `console-never-drives-signer` (K3), beside `console-no-sign-records`, which is unchanged; the two console checks |
| `architecture/engine` | The `signature` question's `handoff` answer and how the engine verifies it (`signature-handoff-answer`); the parity test scripts a `handoff` for Studio |
| `architecture/change-service` | Known Gaps: the console item is replaced by a pointer to the handoff. *"How Studio carries that signature is Studio's to specify"* goes: it is the corpus's, because the CLI and every signer must agree on it |
| `architecture/content` | The client that checks a statement was recorded is named as the signer; *Design Principle 6, strictly* unchanged unless D1 says otherwise |
| `architecture/cli` | `weblisk sign` as the pointer's entry point, dispatching to the existing `change approve`/`reject`, `approvals accept`/`reject` and `attest`; sign-records key generation and keeping (S1), which the CLI does not specify today |
| `architecture/threat-model` | rows 4.10–4.15 |
| `vectors/signer/`, `checks/` | the fixtures and a check that every fixture is listed and every rule has one, as `change-vectors.py` does |
| Studio | the dialog for a `signature` question (pointer, link, QR, short-form comparison), watching the feed, the `handoff` answer |

---

## Decisions

Each is the owner's. The recommendation follows each.

**D1. Do passkeys ever sign a record?** Options: (i) never — Design Principle 6
stays as written; (ii) a passkey assertion is admitted as a new basis,
`confirmed`, between `signed` and `witnessed`, never counted as `signed`; (iii)
admitted as `signed`.
*Recommend (i).* (iii) breaks Q2 and Q3 and the corpus's own principle. (ii)
adds a fourth basis that is stronger than `witnessed` only against a dishonest
service, and only until the curve falls, while letting the console choose what
one touch signs. Revisit when ML-DSA passkeys exist (c3), and even then only
for acts where presence is what is wanted.

**D2. Who submits the act: the signer, or the console relaying the
signature?** *Recommend the signer (b2).* It is the only option in which the
console cannot drop a content statement and record the act `witnessed` in its
place, and it adds no relay channel to secure. Relay (b1) is safe against
forgery and is the fallback if a signer cannot reach the hub itself.

**D3. Which signers, in what order?** *Recommend the CLI only, now.* Every
person who uses a console already ran the CLI to attest the console's
credential (admin, `console-credential-per-account`), so it adds no install.
A desktop or phone signer comes later under the same S1–S7.

**D4. How does the pointer travel?** Options: shown text and a `weblisk://`
link and QR (no new route); or a hub-held *signing request* mailbox the signer
lists and the console posts to (a new admin route and short-lived state).
*Recommend the text, link and QR.* The decision inbox already lists what awaits
the person, so a mailbox would duplicate it; reconsider only for a phone signer
that should be told, not asked.

**D5. The attestation statement's words.** `weblisk/content-attestation/v1`
cannot have vectors until `<statements>` has a vocabulary with a corpus home.
*Recommend settling the vocabulary in `architecture/content` first, then
publishing `content-attestation-entry` and
`content-attestation-span-answering-request`.* Until then `attest` is
`witnessed` in both front ends, which is parity, not a gap of this plan.

**D6. A signed write from a console.** Options: a direct write from the
console stays `witnessed`, and a signed one goes as a proposal whose decision
the signer makes (K5); or the signer takes the console's edited bytes through a
pointer to a draft. *Recommend the proposal.* It keeps S2 (a pointer carries no
bytes) without a draft store, and the proposal is where the person's bytes
already live. Where the change is the person's own, content's self-decision
ceiling decides whether they may apply it themselves.

**D7. Where the signer keeps its key.** *Recommend the platform keychain with a
user-presence access control where the platform offers one, else the
`weblisk-key-v1` envelope*, and a secure element once one holds ML-DSA-65 — a
change to the signer only, never to the record.
