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
- Private key file: `.weblisk/keys/<name>.key` (hex-encoded, file mode 0600)
- Public key file: `.weblisk/keys/<name>.pub` (hex-encoded, file mode 0644)
- Directory mode: 0700
- On startup: load existing keys if present, generate new ones if absent

### Key Loading Flow
```
1. Check if .weblisk/keys/<name>.key exists
2. If yes: read and decode hex → Ed25519 private key → derive public key
3. If no: generate new key pair → save both files → return
```

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
process: data = JSON.stringify(value) → Sign(data)
```

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
        description: 64-byte Ed25519 private key, hex-encoded (128 chars)
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
    description: Request to rotate an agent or orchestrator key
    fields:
      agent_name:
        type: string
        description: Name of the entity rotating keys
      old_public_key:
        type: string
        format: hex
        description: Current public key (64 hex chars)
      new_public_key:
        type: string
        format: hex
        description: New public key (64 hex chars)
      timestamp:
        type: int64
        description: Unix epoch seconds
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
  2. manifestJSON = JSON.stringify(manifest)
  3. signature = Ed25519.Sign(agent_private_key, manifestJSON)
  4. Send: {manifest, signature, timestamp: now()}

Orchestrator side:
  1. Receive {manifest, signature, timestamp}
  2. Verify |now() - timestamp| < 300 seconds (replay protection)
  3. manifestJSON = JSON.stringify(manifest)
  4. Verify: Ed25519.Verify(manifest.public_key, signature, manifestJSON)
  5. If valid: issue token, register agent
  6. If invalid: reject with 401
```

## Agent-to-Agent Message Signing

When agents communicate directly:

```
Sender:
  1. payload = {from, to, action, payload}
  2. payloadJSON = JSON.stringify(payload)
  3. signature = Ed25519.Sign(sender_private_key, payloadJSON)
  4. Include signature in message

Receiver:
  1. Look up sender's public key from service directory
  2. payloadJSON = JSON.stringify({from, to, action, payload})
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
  2. Sign rotation request with CURRENT private key:
     {agent_name, old_public_key, new_public_key, timestamp}
  3. Send POST /v1/rotate-key to orchestrator

Orchestrator side:
  1. Verify rotation request signature with agent's current public key
  2. Verify |now() - timestamp| < 300 seconds (replay protection)
  3. Update agent's public key in service directory
  4. Broadcast updated service directory to all agents
  5. Respond with new WLT token signed with orchestrator's key

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
- [ ] Verify all signatures before trusting data
- [ ] Check token expiry on every verification
- [ ] Enforce replay protection window (300 seconds) on registration
- [ ] Validate public key length (32 bytes / 64 hex chars)
- [ ] Validate signature length (64 bytes / 128 hex chars)
- [ ] Use constant-time comparison for signature verification
- [ ] Never log or expose private keys
