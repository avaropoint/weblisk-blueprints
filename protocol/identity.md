<!-- blueprint
type: protocol
name: identity
version: 1.0.0
requires: [protocol/types]
platform: any
tier: free
-->

# Weblisk Identity & Security Specification

Cryptographic identity for all agents and orchestrators. Every entity
generates an Ed25519 key pair and uses it for signing, verification,
and token-based authentication.

## Overview

The Weblisk Identity specification defines how agents and orchestrators
establish cryptographic identity, sign messages, verify signatures,
and manage authentication tokens. Ed25519 is the sole signing algorithm.
Every entity generates a key pair on first run, uses it for registration
signature verification, and receives a Weblisk Token (WLT) for
subsequent authenticated requests. This specification is the single
source of truth for all identity and cryptographic operations in the
Weblisk framework.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, public_key]
        - name: RegisterRequest
          fields_used: [manifest, signature, timestamp]
        - name: AgentMessage
          fields_used: [from, to, action, payload, signature]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Conventions

- Algorithm: Ed25519 (RFC 8032) — the sole signing algorithm
- Key size: 32-byte public key, 64-byte private key
- Encoding: hex for protocol exchange (64 chars for public, 128 for private)
- JSON signing: RFC 8785 JSON Canonicalization Scheme (JCS) — mandatory
  for all JSON values that are signed
- Token format: `base64url(header).base64url(payload).base64url(signature)`
- All three token parts use base64url encoding WITHOUT padding (RFC 4648 §5)
- Algorithm agility: the token header `alg` field allows future swap to
  post-quantum algorithms (e.g., ML-DSA / FIPS 204) with zero protocol changes

## Key Management

### Generation
- Generate a fresh Ed25519 key pair on first run
- Use cryptographically secure random source (e.g., crypto/rand, Web Crypto API)
- NEVER hardcode or share private keys

### Storage
- Directory: `.weblisk/keys/` in the working directory
- Private key file: `.weblisk/keys/<name>.key` (file mode 0600)
- Public key file: `.weblisk/keys/<name>.pub` (hex-encoded, file mode 0644)
- Directory mode: 0700
- On startup: load existing keys if present, generate new ones if absent

### Private Key Format

Private keys are stored encrypted at rest. The file format is:

```
weblisk-key-v1
<algorithm>
<kdf>
<kdf-params>
<ciphertext>
```

| Field | Value | Description |
|-------|-------|-------------|
| Magic | `weblisk-key-v1` | Format identifier |
| Algorithm | `ed25519` | Key algorithm |
| KDF | `argon2id` or `none` | Key derivation function |
| KDF Params | Base64url JSON | `{salt, time, memory, parallelism}` or `{}` |
| Ciphertext | Base64url | AES-256-GCM encrypted private key (or plaintext hex if KDF = none) |

### Encryption Scheme

When `kdf = argon2id`:

```
1. passphrase → Argon2id(passphrase, salt, time=3, memory=65536, parallelism=4) → 32-byte key
2. AES-256-GCM(derived_key, nonce=first_12_bytes_of_salt, plaintext=private_key_hex) → ciphertext
3. Store ciphertext + tag as base64url
```

Decryption reverses the process — prompts for passphrase, derives key,
decrypts.

When `kdf = none`:
- The private key is stored as hex (no encryption)
- Used ONLY for automated service keys in environments where passphrase
  input is impossible (containers, CI, headless servers)
- File permissions (0600) are the sole protection layer

### Key Categories

| Category | KDF | Passphrase Source | Use Case |
|----------|-----|------------------|----------|
| **Operator keys** | `argon2id` | Interactive prompt | Human-operated CLI |
| **Service keys** (orchestrator, gateway, agent) | `argon2id` or `none` | Env var `WL_KEY_PASSPHRASE` or none | Automated processes |

**Rules:**
1. `weblisk operator init` MUST prompt for a passphrase. Cannot be
   skipped. Minimum 12 characters.
2. `weblisk server init` defaults to `kdf = none` but accepts
   `--encrypt-keys` to use Argon2id with passphrase from
   `WL_KEY_PASSPHRASE` env var.
3. Production deployments SHOULD encrypt service keys with passphrase
   supplied via env var or secrets manager at startup.
4. The passphrase is NEVER stored on disk. It exists only in memory
   during the decrypt operation.
5. Failed passphrase attempts log `security.key_decrypt_failed` and
   exit with code 2 (auth error). No retry loop — the operator
   re-runs the command.

### Key Loading Flow
```
1. Check if .weblisk/keys/<name>.key exists
2. If yes:
   a. Parse file header — check magic line is "weblisk-key-v1"
   b. Read KDF field
   c. If kdf = argon2id:
      - Prompt for passphrase (interactive) or read WL_KEY_PASSPHRASE (env)
      - Derive decryption key via Argon2id with stored params
      - Decrypt ciphertext with AES-256-GCM
      - Decode hex → Ed25519 private key
   d. If kdf = none:
      - Decode hex directly → Ed25519 private key
   e. Derive public key from private key
3. If no: generate new key pair → encrypt → save both files → return
```

### Key Rotation

Operator keys can be rotated without losing hub access:

```
1. weblisk operator rotate
2. Prompts for current passphrase (decrypts existing key)
3. Generates new Ed25519 key pair
4. Prompts for new passphrase (encrypts new key)
5. Registers new public key with orchestrator (signed by old key)
6. Orchestrator validates old-key signature → stores new public key
7. Old key file moved to .weblisk/keys/<name>.key.revoked (kept for audit)
```

Service keys follow the same rotation protocol but use
`WL_KEY_PASSPHRASE` / `WL_KEY_PASSPHRASE_NEW` env vars instead of
interactive prompts.

### Key Recovery

If an operator loses their passphrase, the encrypted private key is
**unrecoverable by design**. There is no backdoor, no master key, and
no reset mechanism. This section defines the recovery procedures.

#### Recovery via Backup Operator

The primary recovery path is another registered operator:

```
1. Second operator (already registered, admin role) logs in
2. Runs: weblisk operator revoke <compromised-operator-name>
3. Orchestrator invalidates old operator's public key and token
4. Compromised operator runs: weblisk operator init (generates new key pair)
5. Compromised operator runs: weblisk operator register --orch <url>
6. Registration appears in approvals queue (not auto-approved)
7. Second operator runs: weblisk approvals accept <registration-id>
8. Access restored with new identity
```

**Requirement:** Every production deployment MUST have at least two
registered operators. A single-operator deployment has no recovery
path if the passphrase is lost.

#### Recovery via Bootstrap Reset

If ALL operator keys are lost (catastrophic scenario):

```
1. Stop the orchestrator
2. Delete the operator registry from orchestrator storage
3. Restart the orchestrator (enters bootstrap mode)
4. First operator to register becomes admin (same as initial setup)
5. All existing operator tokens are invalidated
```

This is destructive — it resets the entire operator trust chain.
Agent registrations and data are preserved, but all operator
permissions must be re-established.

#### Key Backup Policy

Operators SHOULD maintain an encrypted backup of their key file in a
separate secure location (hardware security key, printed paper key,
safety deposit box). The backup is the encrypted `.key` file itself —
never the raw private key or passphrase.

| Policy | Recommendation |
|--------|---------------|
| Minimum operators per deployment | 2 (production), 1 (development) |
| Key backup storage | Offline, physically separated from primary |
| Passphrase storage | Memory only — or written and stored in physical safe |
| Recovery test frequency | Quarterly (verify backup operator can revoke/re-register) |

## Message Signing

### Sign
```
input: data (bytes)
output: hex-encoded Ed25519 signature (128 hex chars)
process: sig = Ed25519.Sign(privateKey, data)
```

### Sign JSON
```
input: any JSON-serializable value
output: hex-encoded Ed25519 signature
process: data = canonicalize(value) → Sign(data)
```

**Canonical JSON (RFC 8785):** All JSON signing MUST use
[RFC 8785 JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785).
This guarantees identical byte output across all languages and platforms:

1. Object keys sorted lexicographically by Unicode code point
2. No insignificant whitespace
3. Numbers serialized per ES2015 `JSON.stringify` rules (no trailing zeros,
   no positive sign on exponent)
4. Strings use minimal \uXXXX escaping (only required characters)

Native `JSON.stringify` is NOT sufficient — key ordering varies across
languages (Go sorts by default, Python 3.7+ preserves insertion order,
JavaScript preserves insertion order). Implementations MUST use a
compliant JCS library or implement the RFC 8785 algorithm directly.

### Verify Signature
```
input: publicKeyHex (string), signatureHex (string), data (bytes)
output: boolean
process:
  1. Decode publicKeyHex to bytes (must be 32 bytes)
  2. Decode signatureHex to bytes (must be 64 bytes)
  3. Return Ed25519.Verify(publicKey, data, signature)
  4. Return false on any decode error
```

## Token System

Tokens are signed claims used for authentication between agents and
the orchestrator. They are self-contained — the verifier only needs
the issuer's public key.

### Token Format
```
base64url(header) . base64url(payload) . base64url(signature)
```

All three parts use base64url encoding WITHOUT padding (RFC 4648 §5).

### Header
```json
{"alg": "Ed25519", "typ": "WLT"}
```
- `alg`: signing algorithm (for algorithm agility)
- `typ`: token type identifier

### Payload (Claims)
```json
{
  "sub": "seo",
  "iss": "orchestrator",
  "iat": 1712160000,
  "exp": 1712246400,
  "cap": ["file:read", "llm:chat", "agent:message"],
  "cid": ""
}
```

Fields:
- `sub` (subject): agent name or identity
- `iss` (issuer): who created the token ("orchestrator" or agent name)
- `iat` (issued at): Unix timestamp
- `exp` (expires at): Unix timestamp (0 = no expiry)
- `cap` (capabilities): granted capability names (optional)
- `cid` (channel ID): for channel-scoped tokens (optional)

### Token Creation
```
1. Serialize header to JSON → base64url encode → headerB64
2. Serialize payload to JSON → base64url encode → payloadB64
3. signingInput = headerB64 + "." + payloadB64
4. signature = Ed25519.Sign(privateKey, bytes(signingInput))
5. token = signingInput + "." + base64url(signature)
```

### Token Verification
```
1. Split token on "." → must have exactly 3 parts
2. Decode header (parts[0]) → verify alg == "Ed25519"
3. signingInput = parts[0] + "." + parts[1]
4. Decode signature (parts[2])
5. Verify: Ed25519.Verify(issuerPublicKey, bytes(signingInput), signature)
6. Decode payload (parts[1]) → parse claims
7. If exp > 0 and current_time > exp → token expired
8. Return claims
```

### Token Lifetimes
- Agent auth tokens: 24 hours (TokenTTL)
- Channel tokens: 1 hour

### ID Generation
```
Generate 16 cryptographically random bytes → hex encode → 32-char string
```

## Types

```yaml
types:
  Ed25519KeyPair:
    description: Cryptographic key pair for agent/orchestrator identity
    fields:
      public_key:
        type: string
        format: hex
        description: 32-byte Ed25519 public key, hex-encoded (64 chars)
        constraints:
          pattern: "^[0-9a-f]{64}$"
      private_key:
        type: string
        format: hex
        description: 64-byte Ed25519 expanded private key (32-byte seed + 32-byte public key), hex-encoded (128 chars)
        constraints:
          pattern: "^[0-9a-f]{128}$"

  WLToken:
    description: Weblisk Token — signed claims for authentication
    fields:
      header:
        type: object
        description: Token header with algorithm and type
        fields:
          alg:
            type: string
            description: Signing algorithm
            constraints:
              enum: [Ed25519]
          typ:
            type: string
            description: Token type identifier
            constraints:
              enum: [WLT]
      payload:
        type: object
        description: Token claims
        fields:
          sub:
            type: string
            description: Subject (agent name or identity)
          iss:
            type: string
            description: Issuer (orchestrator or agent name)
          iat:
            type: int64
            description: Issued at (Unix epoch seconds)
          exp:
            type: int64
            description: Expires at (Unix epoch seconds, 0 = no expiry)
          cap:
            type: "list<string>"
            description: Granted capability names
            required: false
          cid:
            type: string
            description: Channel ID for channel-scoped tokens
            required: false
      signature:
        type: string
        format: base64url
        description: Ed25519 signature over header.payload

  KeyRotationRequest:
    description: Request to rotate an agent or orchestrator key (dual-signed)
    fields:
      agent_id:
        type: string
        description: Agent identifier issued at registration
      new_public_key:
        type: string
        format: hex
        description: New Ed25519 public key (64 hex chars)
      current_signature:
        type: string
        format: hex
        description: Agent manifest signed with current private key (128 hex chars)
      new_signature:
        type: string
        format: hex
        description: Same agent manifest signed with new private key (128 hex chars)
      timestamp:
        type: int64
        description: Unix epoch seconds (replay window 300s)

  Signature:
    description: A detached Ed25519 signature over canonicalized content
    fields:
      algorithm:
        type: string
        description: Signing algorithm
        constraints:
          enum: [Ed25519]
      value:
        type: string
        format: hex
        description: 64-byte Ed25519 signature, hex-encoded (128 chars)
      signer:
        type: string
        description: Public key of the signer (hex)
        required: false

  SignatureVerification:
    description: Operations for verifying signed messages and preventing replay
    operations:
      verify_signature:
        input: [message_bytes, signature_hex, public_key_hex]
        output: bool
        description: Verify an Ed25519 signature against the signer's public key
      check_replay:
        input: [message_id, timestamp]
        output: bool
        description: Return true if message_id has been seen within the replay window (5 minutes)
```

---

## Authentication

```yaml
authentication:
  mechanism: token
  token_format:
    structure: base64url(header).base64url(payload).base64url(signature)
    fields: [sub, iss, iat, exp, cap, cid]
    signing: Ed25519
    expiry: 24 hours (agent auth), 1 hour (channel)
    verification: >
      Split on ".", decode header, verify alg == "Ed25519",
      verify signature against issuer public key, check expiry
  flow:
    - step: Agent generates Ed25519 key pair on first run
    - step: Agent signs manifest with private key
    - step: Orchestrator verifies signature with agent public key
    - step: Orchestrator issues WLT token with capabilities
    - step: Agent includes token in all subsequent requests
    - step: Token is verified on every protected endpoint
```

---

## Registration Signature Flow

When an agent registers with the orchestrator:

```
Agent side:
  1. manifest = AgentManifest{name, version, url, public_key, ...}
  2. manifestJSON = canonicalize(manifest)   // RFC 8785 JCS
  3. signature = Ed25519.Sign(agent_private_key, manifestJSON)
  4. Send: {manifest, signature, timestamp: now()}

Orchestrator side:
  1. Receive {manifest, signature, timestamp}
  2. Verify |now() - timestamp| < 300 seconds (replay protection)
  3. manifestJSON = canonicalize(manifest)   // RFC 8785 JCS
  4. Verify: Ed25519.Verify(manifest.public_key, signature, manifestJSON)
  5. If valid: issue token, register agent
  6. If invalid: reject with 401
```

## Agent-to-Agent Message Signing

When agents communicate directly:

```
Sender:
  1. payload = {from, to, action, payload}
  2. payloadJSON = canonicalize(payload)   // RFC 8785 JCS
  3. signature = Ed25519.Sign(sender_private_key, payloadJSON)
  4. Include signature in message

Receiver:
  1. Look up sender's public key from service directory
  2. payloadJSON = canonicalize({from, to, action, payload})   // RFC 8785 JCS
  3. Verify: Ed25519.Verify(sender_public_key, signature, payloadJSON)
  4. If invalid: reject with 401
```

## Key Rotation

Key rotation replaces an agent's Ed25519 key pair without
interrupting service. This is required when a key is compromised,
when operational policy mandates periodic rotation, or when an
agent migrates between hosts.

### Rotation Flow

```
Agent side:
  1. Generate new Ed25519 key pair
  2. Sign current manifest with CURRENT private key → current_signature
  3. Sign current manifest with NEW private key → new_signature
  4. Send POST /v1/rotate-key to orchestrator:
     {agent_id, new_public_key, current_signature, new_signature, timestamp}

Orchestrator side:
  1. Look up agent by agent_id
  2. Verify current_signature against agent's current public key
  3. Verify new_signature against new_public_key (proves possession)
  4. Verify |now() - timestamp| < 300 seconds (replay protection)
  5. Update agent's public key in service directory
  6. Broadcast updated service directory to all agents
  7. Respond with updated RegisterResponse (new WLT token)

Agent side (on success):
  1. Replace key files (.weblisk/keys/<name>.key and .pub)
  2. Begin using new key for all future signing
  3. Old key is no longer valid
```

### Rotation Rules

| Rule | Requirement |
|------|-------------|
| Authentication | Rotation request MUST be signed by current key |
| Atomicity | Directory update and token reissue are atomic |
| Propagation | All agents receive updated directory within 5 seconds |
| Replay protection | Same 300-second window as registration |
| Overlap | No overlap period — old key is invalid immediately |
| Revocation | Old key's tokens are invalidated on rotation |

### Federation Key Rotation

When a hub rotates its federation key, the rotation must be
communicated to all federation peers:

```
1. Hub generates new federation key pair
2. Hub signs rotation announcement with current key
3. Hub sends KeyRotation message to all connected peers
4. Peers verify announcement with hub's current key
5. Peers update their trust store with new public key
6. Hub switches to new key
```

See the Federation protocol spec for the full peer key rotation
handshake and trust store update procedure.

### Recommended Rotation Schedule

| Key Type | Recommended Interval | Mandatory |
|----------|--------------------|-----------|
| Agent keys | 90 days | On compromise |
| Orchestrator key | 90 days | On compromise |
| Federation keys | 180 days | On compromise |
| Channel tokens | 1 hour (automatic) | Built-in expiry |
| Auth tokens | 24 hours (automatic) | Built-in expiry |

---

## Multi-Key Scenarios

### Orchestrator High Availability

In a multi-instance orchestrator deployment, all instances MUST
share the same Ed25519 key pair. The key is loaded from shared
storage (not generated per instance).

### Agent Migration

When an agent moves to a new host:
1. Copy the existing key files to the new host
2. Start the new instance (it registers with the same key)
3. Stop the old instance
4. If key files cannot be copied, perform a key rotation instead

### Key Compromise Recovery

1. Generate new key pair on a clean system
2. Operator uses admin gateway to force-revoke the compromised key:
   `POST /v1/admin/agents/:name/revoke-key`
3. Agent re-registers with the new key
4. All tokens issued to the old key are invalidated
5. Admin reviews audit trail for unauthorized activity

---

## Standards Alignment: WLT and JWT

The Weblisk Token (WLT) format is structurally identical to JSON Web
Tokens ([RFC 7519](https://www.rfc-editor.org/rfc/rfc7519)) and JSON
Web Signatures ([RFC 7515](https://www.rfc-editor.org/rfc/rfc7515)),
with deliberate deviations:

### What We Adopted from JWT/JWS

| Feature | JWT/JWS Reference | WLT Implementation |
|---------|-------------------|--------------------|
| Three-part structure | RFC 7515 §3 | `header.payload.signature` |
| Base64url encoding | RFC 4648 §5 | Same, no padding |
| Standard claims | RFC 7519 §4.1 | `sub`, `iss`, `iat`, `exp` — same semantics |
| Signature input | RFC 7515 §5.1 | `base64url(header) + "." + base64url(payload)` |

### What We Customized (and Why)

| Feature | JWT Standard | WLT Choice | Rationale |
|---------|-------------|------------|-----------|
| Token type | `"typ": "JWT"` | `"typ": "WLT"` | Distinguish from generic JWTs; prevent cross-system token confusion |
| Algorithm | RS256, ES256, etc. | `"alg": "Ed25519"` | Ed25519 is faster, simpler, and has no algorithm confusion. Single algorithm eliminates `alg` header attacks |
| Capabilities | Not in JWT | `"cap": [...]` claim | Core to Weblisk's capability-based auth model |
| Channel scoping | Not in JWT | `"cid": "..."` claim | Agent-to-agent channel tokens |
| Algorithm agility | Multiple algorithms | Single algorithm, header reserved for future swap | Prevents downgrade attacks while allowing post-quantum migration via `alg` field |

### Interoperability

WLT tokens are NOT valid JWTs and MUST NOT be sent to JWT-consuming
services. The `typ: WLT` header prevents accidental cross-system use.
For integration with external JWT-based systems (OAuth providers,
API gateways), the `patterns/auth-token` pattern handles JWT
issuance and validation separately.

---

## Error Handling

```yaml
error_codes:
  - code: INVALID_SIGNATURE
    status: 401
    description: Ed25519 signature verification failed
    retryable: false
  - code: TOKEN_EXPIRED
    status: 401
    description: Token past expiry — re-register to get a new one
    retryable: true
  - code: INVALID_REQUEST
    status: 400
    description: Malformed token, key, or rotation request
    retryable: false
  - code: KEY_DECODE_ERROR
    status: 400
    description: Public key or signature could not be hex-decoded
    retryable: false
```

---

## Security

```yaml
security:
  transport:
    - Private keys MUST be stored with restricted permissions (0600)
    - Key directory MUST have restricted permissions (0700)
    - Private keys MUST NOT be logged, exposed, or transmitted
  signing:
    algorithm: Ed25519
    key_type: 32-byte public / 64-byte private
    process: Ed25519.Sign(privateKey, data) → 64-byte signature
  verification:
    process: Ed25519.Verify(publicKey, data, signature) → boolean
  trust_model:
    description: >
      Self-sovereign identity. Each agent generates its own key pair.
      Trust is established through registration signature verification.
      The orchestrator is the root of trust — it issues tokens after
      verifying the agent's self-signed manifest.
  key_security:
    - Use cryptographically secure random source (crypto/rand, Web Crypto API)
    - NEVER hardcode or share private keys
    - Use constant-time comparison for signature verification
    - Validate public key length (32 bytes / 64 hex chars) before use
    - Validate signature length (64 bytes / 128 hex chars) before use
  replay_protection:
    window: 300 seconds
    applies_to: registration signatures, key rotation requests
```

---

## Implementation Notes

- Keys are stored in `.weblisk/keys/` relative to the working directory
- Key files use hex encoding for portability across platforms
- Token lifetimes are deliberately short (24h auth, 1h channel) to limit blast radius
- WLT is structurally similar to JWT but uses `typ: WLT` to prevent cross-system confusion
- Single-algorithm design (Ed25519 only) eliminates algorithm confusion attacks
- The `alg` header field is reserved for future post-quantum migration
- Key rotation is atomic — old key is invalid immediately after rotation
- Federation key rotation uses dual-signature (old + new) for zero-downtime transitions

---

## Verification Checklist

Implementation MUST:
- [ ] Generate keys with cryptographically secure random source
- [ ] Store private keys with restricted permissions (0600)
- [ ] Encrypt operator private keys with Argon2id + AES-256-GCM (passphrase required, min 12 chars)
- [ ] Support encrypted service keys via WL_KEY_PASSPHRASE env var
- [ ] Parse weblisk-key-v1 format correctly (magic, algorithm, kdf, params, ciphertext)
- [ ] Never store passphrase on disk — only hold in memory during decrypt
- [ ] Exit with code 2 on failed passphrase (no retry loop, no passphrase enumeration)
- [ ] Verify all signatures before trusting data
- [ ] Check token expiry on every verification
- [ ] Enforce replay protection window (300 seconds) on registration
- [ ] Validate public key length (32 bytes / 64 hex chars)
- [ ] Validate signature length (64 bytes / 128 hex chars)
- [ ] Use constant-time comparison for signature verification
- [ ] Never log or expose private keys
- [ ] Key rotation registers new public key signed by old key before revoking old key
- [ ] Revoked keys stored as .key.revoked for audit trail
- [ ] Production deployments have minimum 2 registered operators for recovery
- [ ] Backup operator can revoke and re-register a compromised operator
- [ ] Bootstrap reset (all keys lost) requires orchestrator restart and re-registration
