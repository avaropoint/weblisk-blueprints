# Weblisk Blueprints

The specification, architecture, and domain knowledge for the
[Weblisk](https://github.com/avaropoint/weblisk) agent framework.

Blueprints are implementation-agnostic specifications. They describe
**what** agents and orchestrators must do — not **how** they do it in
any particular language. Server implementations (Go, Node, Cloudflare,
Rust, etc.) build from these blueprints.

## Structure

```
protocol/           Wire protocol specifications
  spec.md             Full protocol specification v1
  identity.md         Ed25519 crypto, tokens, signing
  types.md            Canonical type definitions (all JSON shapes)

architecture/       System architecture patterns
  orchestrator.md     How the orchestrator works
  agent.md            How agents work

platforms/          Implementation guidance per runtime
  go.md               Go (stdlib only, local processes)
  cloudflare.md       Cloudflare Workers (Durable Objects, KV)

domains/            Domain expertise for specific agents
  seo.md              SEO analysis and optimization
```

## Usage

### With the Weblisk CLI

The CLI supports multiple blueprint sources. This repository serves as the
**core** source — always available as a fallback. Custom, partner, and
customer-owned blueprint repos can be added alongside it.

```bash
# The CLI clones this repo automatically on first use
weblisk server init --platform go

# Generate an agent from a domain blueprint
weblisk agent create seo --platform go

# Force re-fetch all blueprint sources
weblisk blueprints update
```

### Multiple Blueprint Sources

The CLI resolves blueprints in priority order:

1. **Local project** — `./blueprints/` in the user's project
2. **Custom sources** — additional repos via `WL_BLUEPRINT_SOURCES`
3. **Core** — this repository (always present)

Custom sources override core blueprints with the same path. For example,
a customer's `domains/checkout.md` takes precedence over the core version.

```bash
# .env — add additional blueprint repositories
WL_BLUEPRINT_SOURCES=https://github.com/acme-corp/acme-blueprints.git
```

This supports multiple distribution models:

| Source Type | Example | Typical Access |
|---|---|---|
| Core (open source) | `avaropoint/weblisk-blueprints` | Public, always available |
| Vertical/partner | `avaropoint/weblisk-blueprints-ecommerce` | Granted per-customer |
| Customer-owned | `acme-corp/acme-blueprints` | Customer's own repo |
| Local project | `./blueprints/` | Project-scoped, checked in |

Access control is handled entirely by Git — private repos require the
user's existing credentials (SSH key or GitHub CLI auth).

### Building Your Own

1. Read the [Blueprint Schema](SCHEMA.md) for the standard structure
2. Create a domain blueprint for your agent's expertise
3. Reference the protocol and architecture blueprints
4. Use the Weblisk CLI or your preferred AI model to generate the implementation

## Blueprint Schema

Every blueprint follows a [standard schema](SCHEMA.md) with required sections:
metadata header, overview, specification, types, implementation notes,
and verification checklist. See the schema file for details.

## Creating Domain Blueprints

Domain blueprints define an agent's specific expertise. They MUST include:

1. **Capabilities** — What the agent can do (file:read, llm:chat, etc.)
2. **Execute Workflow** — Step-by-step process for task execution
3. **Message Handlers** — Actions the agent responds to
4. **Validation Rules** — Domain-specific constraints
5. **LLM Prompts** — System prompts for AI-assisted analysis (if applicable)

See [domains/seo.md](domains/seo.md) for a complete example.

## Server Implementations

These blueprints are used by the following server implementations:

- [weblisk-server](https://github.com/avaropoint/weblisk-server) — Go reference implementation

## License

MIT
