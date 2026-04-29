# Wire Protocol

The protocol specifications define how Weblisk components communicate
over the network — message formats, identity verification, endpoint
contracts, and federation mechanics. Every agent, orchestrator, and
gateway implements these specs regardless of platform or language.

## Protocol Specifications

| Spec | Purpose |
|------|---------|
| [spec.md](spec.md) | Full protocol specification — 6 agent + 6 orchestrator endpoints |
| [identity.md](identity.md) | Ed25519 cryptography, tokens, signing, key rotation |
| [types.md](types.md) | Canonical type definitions — all JSON shapes |
| [federation.md](federation.md) | Multi-orchestrator federation and data boundaries |

## Key Design Decisions

- **HTTP + JSON** — No binary protocols. Every message is inspectable.
- **Ed25519 signatures** — All registration and inter-hub communication
  is cryptographically signed. No shared secrets.
- **Stateless tokens** — Agents authenticate with short-lived tokens
  issued by the orchestrator. No session state on the server.
- **Federation by consent** — Hubs connect only through explicit mutual
  agreement. No implicit trust.

## Reading Order

1. Start with [types.md](types.md) for the data shapes
2. Read [spec.md](spec.md) for the endpoint contracts
3. Read [identity.md](identity.md) for the auth/crypto model
4. Read [federation.md](federation.md) for multi-hub connectivity

## Schema

Protocol specifications conform to [schemas/protocol.md](../schemas/protocol.md).
