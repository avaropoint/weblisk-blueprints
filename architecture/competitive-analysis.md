<!-- blueprint
type: architecture
name: competitive-analysis
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/federation]
platform: any
-->

# Competitive Landscape Analysis

How Weblisk positions against the current agent framework ecosystem —
and why it occupies a category of its own.

## Executive Summary

Every major platform vendor now ships an agent framework. They share a
common shape: a Python/TypeScript SDK that orchestrates LLM calls,
tool invocations, and multi-agent handoffs within a single runtime.
Weblisk is not that. Weblisk is a **protocol-first, implementation-
agnostic specification** that defines how autonomous agents declare
capabilities, communicate over HTTP+JSON, and collaborate across
trust boundaries — without depending on any vendor, language, SDK,
model, or runtime. The comparison is less "which framework is better"
and more "which layer of the stack does each address."

---

## The Landscape (as of April 2026)

### 1. OpenAI Agents SDK

**What it is.** A Python SDK that wraps the OpenAI Responses API with
an agent loop, tool dispatch, handoffs, guardrails, tracing, and
sessions. Ships sandbox agents (Docker/local) for isolated execution.

| Dimension | OpenAI Agents SDK |
|-----------|-------------------|
| Language | Python (primary) |
| Model lock-in | OpenAI by default; LiteLLM adapter for others |
| Runtime | Single-process Python; sandbox agents for isolation |
| Multi-agent | Handoffs (delegation) and agents-as-tools |
| State | Sessions (SQLite, SQLAlchemy, Redis, MongoDB) |
| Observability | Built-in tracing → OpenAI dashboard |
| Federation | None — single-tenant, single-process |
| Protocol | Proprietary (Responses API wire format) |
| Dependencies | `pip install openai-agents` + model API key |

**Where Weblisk differs:**
- OpenAI Agents SDK is a **runtime** — it executes agent logic.
  Weblisk is a **specification** — it defines what agents must do,
  not how they run.
- Handoffs are in-process function calls. Weblisk agents communicate
  over HTTP with Ed25519-signed messages across network boundaries.
- No federation concept. Every agent lives in one Python process.
  Weblisk hubs federate across organizations with cryptographic trust.
- Tightly coupled to OpenAI models. Weblisk is model-agnostic by
  design — local Ollama models are the default, remote providers are
  optional.

---

### 2. Google Agent Development Kit (ADK)

**What it is.** An open-source framework (Python, TypeScript, Go,
Java) for building agents with Gemini and other models. Features
multi-agent orchestration, workflow agents (sequential, loop,
parallel), graph-based workflows, A2A protocol support, and
deployment to Google Cloud (Agent Engine, Cloud Run, GKE).

| Dimension | Google ADK |
|-----------|------------|
| Language | Python, TypeScript, Go, Java |
| Model lock-in | Gemini primary; adapters for Claude, Ollama, LiteLLM |
| Runtime | Single-process with web UI; deploys to GCP |
| Multi-agent | Sequential, loop, parallel, custom agents |
| State | Sessions, memory, artifacts, context caching |
| Observability | Logging, evaluation framework |
| Federation | A2A protocol (agent-to-agent, separate spec) |
| Protocol | A2A (JSON-RPC over HTTP), MCP for tools |
| Dependencies | `pip install google-adk` + GCP for production |

**Where Weblisk differs:**
- ADK is a **framework with runtime** — it provides the execution
  engine. Weblisk provides the **specification** that any runtime
  implements.
- ADK's multi-language support is good but each language is a
  separate SDK with different maturity levels. Weblisk blueprints
  are language-independent — implement in Go, Rust, Zig, or
  anything that speaks HTTP+JSON.
- ADK integrates Google's A2A protocol for agent interop. Weblisk's
  federation protocol predates A2A and is more comprehensive:
  cryptographic identity, data contracts, trust boundaries,
  marketplace. A2A focuses on task delegation between agents;
  Weblisk federation handles organizational trust, data sovereignty,
  and economic exchange.
- GCP deployment is the golden path. Weblisk deploys anywhere — a
  Raspberry Pi, Cloudflare Workers, bare metal, or any cloud. No
  platform coupling.

---

### 3. Anthropic (Claude Managed Agents + MCP)

**What it is.** Two distinct offerings: (1) Claude Managed Agents —
server-managed stateful agents with Anthropic-hosted tool execution,
persistent configs, and per-session containers. (2) Model Context
Protocol (MCP) — an open standard for connecting AI applications to
external data sources and tools.

| Dimension | Claude/MCP |
|-----------|------------|
| Language | Python, TypeScript, + 5 more for Messages API |
| Model lock-in | Claude only for Managed Agents; MCP is model-agnostic |
| Runtime | Anthropic-hosted containers (Managed Agents) |
| Multi-agent | Single agent per session; multi via orchestration layer |
| State | Per-session containers, environments, vaults |
| Observability | Via API responses; no built-in distributed tracing |
| Federation | None — MCP connects tools to a single model |
| Protocol | MCP (JSON-RPC, stdio/SSE transport) for tools |
| Dependencies | Anthropic API key; hosted infrastructure |

**Where Weblisk differs:**
- Managed Agents run on Anthropic's infrastructure. Weblisk hubs are
  self-sovereign — you own the compute, the data, and the keys.
- MCP solves a different problem: connecting an LLM to tools (file
  systems, databases, APIs). Weblisk's protocol solves agent-to-
  agent communication, orchestration, domain decomposition, and
  cross-organization federation. MCP is tool-facing; Weblisk is
  agent-facing.
- MCP could be used **inside** a Weblisk agent as a tool integration
  layer — the two are complementary, not competitive.
- No concept of domains, workflows, governance, or compliance. Each
  agent is an island with API access. Weblisk agents exist within
  an architectural hierarchy with explicit authority, policies, and
  behavioral boundaries.

---

### 4. Microsoft AutoGen / Semantic Kernel Agent Framework

**What it is.** Two complementary frameworks: (1) AutoGen — an
event-driven Python framework for multi-agent systems with AgentChat
(conversational) and Core (scalable distributed) layers.
(2) Semantic Kernel Agent Framework — C#/Python/Java SDK for building
agents within the Semantic Kernel ecosystem with orchestration
patterns and Azure integration.

| Dimension | AutoGen / SK Agents |
|-----------|---------------------|
| Language | Python (AutoGen), C#/Python/Java (SK) |
| Model lock-in | OpenAI primary; extensible to others |
| Runtime | Single-process (AgentChat), distributed via gRPC (Core) |
| Multi-agent | Conversational, event-driven, orchestrated |
| State | Conversation history, shared context |
| Observability | Event-driven tracing in Core |
| Federation | None natively; gRPC for distribution |
| Protocol | Internal message passing; gRPC for distributed |
| Dependencies | Multiple NuGet/pip packages + model API keys |

**Where Weblisk differs:**
- AutoGen Core's distributed agents via gRPC are the closest analog
  to Weblisk's architecture, but they require a shared runtime
  environment and trusted network. Weblisk federates across trust
  boundaries with cryptographic identity.
- Semantic Kernel is deeply integrated with Azure. Weblisk has zero
  platform affinity.
- Neither framework addresses domain decomposition, marketplace
  economics, compliance profiles, or data sovereignty. These are
  first-class concepts in Weblisk.
- Agent definitions in AutoGen/SK are imperative code. Weblisk
  agents are declarative blueprints that can be implemented in any
  language — or generated by AI from the specification.

---

### 5. CrewAI

**What it is.** An open-source Python framework for orchestrating
autonomous AI agent teams. Architecture separates Flows (stateful
workflow backbone) from Crews (collaborative agent teams). 100K+
developers certified.

| Dimension | CrewAI |
|-----------|--------|
| Language | Python |
| Model lock-in | Model-agnostic (via LiteLLM) |
| Runtime | Single-process Python |
| Multi-agent | Role-playing agents in crews, managed by flows |
| State | Flow state management, persistence |
| Observability | Logging, execution traces |
| Federation | None |
| Protocol | Internal Python method calls |
| Dependencies | `pip install crewai` + model API key |

**Where Weblisk differs:**
- CrewAI's Flows↔Crews separation is conceptually similar to
  Weblisk's Orchestrator→Domain→Agent hierarchy, but implemented
  entirely in Python runtime code. Weblisk defines the hierarchy as
  a protocol that any implementation follows.
- CrewAI agents are "role-playing" LLM personas within a single
  process. Weblisk agents are independent processes with their own
  ports, identity keys, storage, and network addresses.
- No federation, no trust boundaries, no marketplace. CrewAI is a
  single-team tool; Weblisk is a multi-organization platform.

---

### 6. LangGraph (LangChain)

**What it is.** A Python/TypeScript library for building stateful,
multi-actor applications using graph-based workflows with cycles,
controllability, and persistence. Part of the LangChain ecosystem.

| Dimension | LangGraph |
|-----------|-----------|
| Language | Python, TypeScript |
| Model lock-in | Model-agnostic (via LangChain integrations) |
| Runtime | Single-process with optional LangGraph Cloud |
| Multi-agent | Graph nodes as agents, edges as transitions |
| State | Graph state (checkpointed, persistent) |
| Observability | LangSmith integration |
| Federation | None |
| Protocol | Internal graph execution |
| Dependencies | LangChain ecosystem + model providers |

**Where Weblisk differs:**
- LangGraph's state machine / graph model is powerful for single-
  application workflows. Weblisk's `patterns/workflow.md` and
  `patterns/state-machine.md` define equivalent workflow primitives
  but as cross-boundary specifications, not in-process graph code.
- LangGraph depends on the LangChain ecosystem (prompts, chains,
  retrievers). Weblisk has zero dependencies.
- No concept of organizational boundaries, data contracts, or
  cryptographic identity between graph nodes. All nodes share the
  same trust context and memory space.

---

## The Protocols Layer

Three interoperability protocols are emerging alongside these
frameworks. Weblisk's protocol predates all three and is more
comprehensive, but understanding the relationship matters.

### MCP (Model Context Protocol)

- **Scope:** Connects an LLM to tools (databases, files, APIs)
- **Transport:** JSON-RPC over stdio or SSE
- **Direction:** Model → Tool (one-way capability exposure)
- **Identity:** None — trust is implicit in the connection
- **Weblisk relationship:** MCP could serve as a tool integration
  layer inside a Weblisk agent. An agent that needs to query a
  database could use an MCP server internally. The two protocols
  operate at different layers: MCP is tool-facing, Weblisk is
  agent-facing and organization-facing.

### A2A (Agent-to-Agent Protocol)

- **Scope:** Task delegation between agents
- **Transport:** JSON-RPC over HTTP
- **Direction:** Agent ↔ Agent (bidirectional task exchange)
- **Identity:** Agent Cards with capability declarations
- **Weblisk relationship:** A2A's Agent Cards are comparable to
  Weblisk's agent manifests. A2A focuses on task-level interop;
  Weblisk's federation protocol adds trust establishment,
  data contracts, compliance verification, and economic exchange.
  A Weblisk hub could expose an A2A-compatible interface as a
  gateway adapter for interop with A2A-native agents.

### Weblisk Protocol

- **Scope:** Full agent lifecycle — identity, communication,
  orchestration, federation, governance, marketplace
- **Transport:** HTTP + JSON with Ed25519 signatures
- **Direction:** Orchestrator → Domain → Agent (hierarchical) +
  Hub ↔ Hub (federated)
- **Identity:** Ed25519 keypairs, WLT tokens, key rotation, trust
  establishment
- **Unique capabilities:** Domain decomposition, workflow execution,
  compliance profiles, data contracts, marketplace economics, threat
  model, zero-dependency philosophy

---

## Comparison Matrix

| Capability | Weblisk | OpenAI SDK | Google ADK | Claude/MCP | AutoGen/SK | CrewAI | LangGraph |
|------------|---------|------------|------------|------------|------------|--------|-----------|
| **Category** | Protocol + Spec | Runtime SDK | Runtime SDK | Hosted + Protocol | Runtime SDK | Runtime SDK | Runtime SDK |
| **Language independence** | Any (HTTP+JSON) | Python | 4 languages | 8 languages | Python/C#/Java | Python | Python/TS |
| **Model independence** | Full | Limited | Partial | None (MA) / Full (MCP) | Partial | Full | Full |
| **Platform independence** | Full | Limited | GCP-oriented | Anthropic-hosted (MA) | Azure-oriented | Full | LangChain Cloud |
| **Zero dependencies** | Yes | No | No | No | No | No | No |
| **Cryptographic identity** | Ed25519 native | None | None | None | None | None | None |
| **Multi-org federation** | Yes (protocol-level) | None | A2A (separate) | None | gRPC (same org) | None | None |
| **Domain decomposition** | Yes (first-class) | None | None | None | None | None | None |
| **Workflow engine** | Declarative spec | Agent loop | Graph workflows | Session-based | Event-driven | Flows | Graph |
| **Governance / compliance** | Profiles + evidence | Guardrails | Safety | None | None | None | None |
| **Data contracts** | Versioned schemas | None | None | None | None | None | None |
| **Marketplace** | Built-in | None | None | None | Extensions | None | None |
| **Threat model** | 5-boundary OWASP | None | Safety docs | None | None | None | None |
| **Self-sovereign** | Yes | No | No | No | No | Partial | Partial |
| **MCP compatible** | Adapter layer | Built-in | Built-in | Native | Built-in | Via tools | Via tools |
| **A2A compatible** | Adapter layer | None | Native | None | None | None | None |

---

## Weblisk's Unique Position

### What Weblisk Is

1. **A protocol** — not a framework, not an SDK, not a runtime. It
   defines how agents identify themselves, communicate, form trust,
   execute workflows, enforce governance, and transact — over plain
   HTTP+JSON with Ed25519 cryptography.

2. **Implementation-agnostic specifications** — 73 blueprints across
   protocol, architecture, patterns, agents, and domains. Any
   language, any runtime, any platform can implement them. The CLI
   generates Go, Node.js, or Cloudflare Workers from the same specs.

3. **An opt-in architecture** — nothing in Weblisk requires adoption
   of the entire stack. Use the auth patterns without the workflow
   engine. Use the observability pattern without federation. Use
   federation without the marketplace. Every piece works standalone.

4. **A zero-dependency philosophy** — the only external dependency
   in the entire architecture is AI models (by necessity). Everything
   else — identity, storage, messaging, observability — is built on
   standard HTTP, JSON, and Ed25519. No vendor SDKs, no databases,
   no message brokers, no runtime packages.

### What Weblisk Is Not

1. **Not a competitor to SDKs** — OpenAI Agents SDK, Google ADK,
   CrewAI, and LangGraph are execution environments. A Weblisk agent
   could be *built with* any of these internally. The SDK runs the
   agent; the Weblisk protocol governs how that agent participates
   in a larger ecosystem.

2. **Not a model wrapper** — Weblisk doesn't wrap LLM calls or
   manage prompt chains. It defines the organizational and
   communication structure that AI-powered agents operate within.

3. **Not a cloud service** — There is no Weblisk cloud. Every hub
   is self-sovereign. You can run it on localhost, a Raspberry Pi,
   Cloudflare Workers, AWS, GCP, Azure, or bare metal. The protocol
   doesn't know or care.

### The Interoperability Story

Weblisk's zero-dependency, protocol-first approach makes it naturally
interoperable:

```
┌─────────────────────────────────────────────────────┐
│                   Weblisk Hub                        │
│                                                      │
│  Orchestrator ─── Domain Controllers ─── Agents      │
│       │                                    │         │
│       │              ┌─────────────────────┤         │
│       │              │                     │         │
│       ▼              ▼                     ▼         │
│  ┌─────────┐   ┌──────────┐   ┌───────────────────┐ │
│  │ MCP     │   │ A2A      │   │ Internal agents   │ │
│  │ Adapter │   │ Adapter  │   │ (any framework)   │ │
│  │         │   │          │   │                   │ │
│  │ Expose  │   │ Expose   │   │ Built with:       │ │
│  │ tools   │   │ tasks to │   │ - OpenAI SDK      │ │
│  │ to MCP  │   │ A2A      │   │ - Google ADK      │ │
│  │ clients │   │ agents   │   │ - AutoGen         │ │
│  │         │   │          │   │ - CrewAI          │ │
│  └─────────┘   └──────────┘   │ - LangGraph       │ │
│                                │ - Raw HTTP        │ │
│                                │ - Anything else   │ │
│                                └───────────────────┘ │
│                                                      │
│  Federation ←──→ Other Weblisk Hubs                  │
│  A2A Gateway ←──→ Google ADK / A2A agents            │
│  MCP Server  ←──→ Claude / ChatGPT / Copilot         │
└─────────────────────────────────────────────────────┘
```

A Weblisk hub can simultaneously:
- Run agents built with OpenAI Agents SDK, Google ADK, or any other
  framework internally
- Expose capabilities to MCP clients (Claude, ChatGPT, VS Code)
- Participate in A2A task delegation with Google ADK agents
- Federate with other Weblisk hubs for cross-org collaboration
- Operate as a standalone system with zero external connections

This is not theoretical — it follows directly from the protocol
design. If your agent speaks HTTP+JSON and signs with Ed25519, it's
a Weblisk agent regardless of what runtime it uses internally.

---

## Why This Matters

The current agent ecosystem has a fragmentation problem:

- **OpenAI Agents SDK** locks you into Python + OpenAI models
- **Google ADK** steers you toward GCP + Gemini
- **Claude Managed Agents** runs only on Anthropic infrastructure
- **AutoGen/SK** gravitates toward Azure + OpenAI
- **CrewAI** is Python-only, single-process
- **LangGraph** depends on the LangChain ecosystem

Each framework solves the "how do I make an LLM do things" problem
well. None of them solve:

- How do agents from different organizations trust each other?
- How do you enforce governance policies across autonomous agents?
- How do you ensure data sovereignty when agents cross boundaries?
- How do you build a marketplace for agent capabilities?
- How do you do all of this without depending on any vendor?

Weblisk answers these questions at the protocol level, making it the
**connective tissue** between agent frameworks rather than another
framework competing for the same space.

### The Analogy

If agent frameworks are **web application frameworks** (Rails, Django,
Express, Spring), then Weblisk is **HTTP + DNS + TLS** — the
protocol layer that lets them all interoperate. You don't choose
between HTTP and Rails. You use Rails over HTTP. Similarly, you don't
choose between Weblisk and Google ADK. You can run ADK agents that
participate in the Weblisk protocol.

---

## Interoperability Roadmap

### MCP Integration (adapter layer)

A Weblisk agent's capabilities can be exposed as MCP tools, making
any Weblisk hub accessible to Claude, ChatGPT, Copilot, Cursor, and
other MCP-compatible clients.

```yaml
# Example: Expose a Weblisk domain as MCP tools
adapter: mcp-server
source: domain/seo
expose:
  - name: seo_audit
    maps_to: workflow/seo-audit
  - name: seo_optimize
    maps_to: workflow/seo-optimize
transport: stdio  # or sse
```

### A2A Integration (gateway adapter)

A Weblisk hub can expose A2A-compatible Agent Cards and accept
A2A task requests, enabling interop with Google ADK agents and any
other A2A-compatible framework.

```yaml
# Example: Expose Weblisk agents as A2A agents
adapter: a2a-gateway
agents:
  - weblisk_agent: seo-analyzer
    a2a_card:
      name: seo-analyzer
      description: "Technical SEO analysis"
      capabilities:
        - name: analyze
          input_schema: { ... }
```

### Framework-Internal Agents

Any agent framework can implement a Weblisk agent. The contract is:

1. Listen on an assigned port
2. Respond to `POST /v1/health`
3. Respond to `POST /v1/execute`
4. Respond to `POST /v1/event` (for pub/sub)
5. Sign messages with Ed25519
6. Declare capabilities in a manifest

What happens inside the agent — whether it uses OpenAI SDK, Google
ADK, CrewAI, raw Python, or hand-written assembly — is entirely up
to the implementer. The protocol doesn't know or care.

---

## Summary

| Question | Answer |
|----------|--------|
| Is Weblisk another agent framework? | No. It's a protocol and specification. |
| Does Weblisk compete with OpenAI/Google/Anthropic? | No. It operates at a different layer. |
| Can I use OpenAI SDK inside a Weblisk agent? | Yes. Any framework works internally. |
| Can Weblisk agents talk to MCP clients? | Yes, via an adapter layer. |
| Can Weblisk agents talk to A2A agents? | Yes, via a gateway adapter. |
| What does Weblisk provide that others don't? | Cryptographic identity, multi-org federation, governance, data contracts, marketplace, zero dependencies, full language/platform independence. |
| What do others provide that Weblisk doesn't? | Ready-to-run execution environments, built-in LLM orchestration, turn-key model integrations. |
| How should I think about it? | Frameworks are apps. Weblisk is the internet they run on. |
