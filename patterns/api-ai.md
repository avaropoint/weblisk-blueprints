<!-- blueprint
type: pattern
name: api-ai
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent, architecture/gateway]
platform: any
tier: free
-->

# API AI Blueprint

AI-first communication pattern for interacting with language models,
embedding services, and intelligent agents. Define your intelligence
layer once and generate spec-compliant endpoints that unify any
provider — local or remote — behind a consistent interface.

## Overview

The `api-ai` pattern generates endpoints for conversational inference,
structured extraction, embedding generation, and tool-augmented
reasoning. It abstracts provider-specific details (OpenAI, Anthropic,
Ollama, Cloudflare Workers AI, etc.) behind a universal contract so
that agents, domains, and application code interact with intelligence
through a single interface.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [error, code, category, retryable]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Message
          fields_used: [role, content, tool_call_id]
        - name: Usage
          fields_used: [prompt_tokens, completion_tokens, total_tokens]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version, capabilities]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately

  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: GatewayRoute
          fields_used: [path, method, rate_limit]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Provider-agnostic** — All intelligence access flows through a universal contract that abstracts provider-specific details. Switching between local and remote is a configuration change, not a code change.
2. **Local-first** — The default configuration uses local models (Ollama) with no external API keys, no external dependencies, and no data leaving the deployment.
3. **Centralized gateway** — Rather than each agent implementing its own provider integration, the api-ai pattern provides a single gateway that enforces rate limits, tracks usage, and routes to the configured provider.
4. **Structured extraction** — Beyond free-form chat, the pattern supports schema-validated data extraction, ensuring AI outputs conform to expected shapes.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: conversational-inference
      description: Multi-turn chat with optional tool use
      parameters:
        - name: model
          type: string
          required: false
          description: Model name (uses default if omitted)
        - name: messages
          type: "[]Message"
          required: true
          description: Conversation history
        - name: temperature
          type: float
          required: false
          description: Sampling temperature (0.0–2.0)
      inherits: ChatRequest/ChatResponse shape
      overridable: true
      override_constraints: Must preserve Message schema and Usage reporting

    - name: structured-extraction
      description: Extract typed data from text using a JSON schema
      parameters:
        - name: input
          type: string
          required: true
          description: Text to extract from
        - name: schema
          type: object
          required: true
          description: JSON Schema defining output shape
      inherits: ExtractRequest/ExtractResponse shape
      overridable: true
      override_constraints: Must validate output against provided schema

  types:
    - name: ChatRequest
      description: Input for conversational inference
      inherited_by: Types section
    - name: ChatResponse
      description: Output from conversational inference
      inherited_by: Types section
    - name: ExtractRequest
      description: Input for structured data extraction
      inherited_by: Types section
    - name: EmbedRequest
      description: Input for embedding generation
      inherited_by: Types section

  endpoints:
    - path: /ai/chat
      description: Conversational inference (multi-turn)
      inherited_by: Specification section
    - path: /ai/complete
      description: Single-shot text completion
      inherited_by: Specification section
    - path: /ai/extract
      description: Structured data extraction from text
      inherited_by: Specification section
    - path: /ai/embed
      description: Generate embeddings for text
      inherited_by: Specification section
    - path: /ai/models
      description: List available models and providers
      inherited_by: Specification section
    - path: /ai/health
      description: Provider health and latency
      inherited_by: Specification section
```

---

This is the intelligence backbone of a Weblisk server — the way every
agent accesses LLM capabilities. Rather than each agent implementing
its own provider integration, the api-ai pattern provides a centralized
gateway that enforces rate limits, tracks usage, and routes to the
configured provider.

The default configuration uses **local models** (Ollama) — no external
API keys, no external dependencies, no data leaving the deployment.
Remote providers (OpenAI, Anthropic, etc.) are optional for teams
that want them. The provider abstraction means switching between
local and remote is a configuration change, not a code change.

## Specification

### Blueprint Format

```yaml
name: api-ai
version: 1.0.0
description: AI-first communication with language models and intelligence services

providers:
  ollama:
    type: local
    base_url: http://localhost:11434
    models: [llama3, codellama]

  openai:
    type: remote
    auth: bearer
    env_key: WL_AI_OPENAI_KEY
    models: [gpt-4o, gpt-4o-mini]

  anthropic:
    type: remote
    auth: x-api-key
    env_key: WL_AI_ANTHROPIC_KEY
    models: [claude-sonnet-4-20250514, claude-haiku-4-20250414]

  workers-ai:
    type: platform
    binding: AI
    models: ["@cf/meta/llama-3-8b-instruct"]

defaults:
  provider: ollama
  model: llama3
  temperature: 0.7
  max_tokens: 4096
  timeout: 120
```

### Generated Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/chat` | Conversational inference (multi-turn) |
| POST | `/ai/complete` | Single-shot text completion |
| POST | `/ai/extract` | Structured data extraction from text |
| POST | `/ai/embed` | Generate embeddings for text |
| GET | `/ai/models` | List available models and providers |
| GET | `/ai/health` | Provider health and latency |

### POST /ai/chat

Multi-turn conversational inference with optional tool use.

**Request:**

```json
{
  "model": "llama3",
  "messages": [
    {"role": "system", "content": "You are an SEO expert."},
    {"role": "user", "content": "Analyze this title tag: <title>Home</title>"}
  ],
  "temperature": 0.7,
  "max_tokens": 2048,
  "tools": [],
  "stream": false,
  "trace_id": "a1b2c3..."
}
```

**Response:**

```json
{
  "id": "chat-abc123",
  "model": "llama3",
  "provider": "ollama",
  "message": {
    "role": "assistant",
    "content": "The title 'Home' is too generic and short for SEO..."
  },
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 156,
    "total_tokens": 198
  },
  "latency_ms": 1200,
  "trace_id": "a1b2c3..."
}
```

**Tool use:** When `tools` are provided, the model MAY return a
`tool_calls` array instead of `content`. The caller executes the
tools and sends a follow-up with `role: "tool"` messages containing
the results. The api-ai endpoint handles provider-specific tool
calling formats transparently.

```json
{
  "tools": [
    {
      "name": "read_file",
      "description": "Read contents of a file",
      "parameters": {
        "type": "object",
        "properties": {
          "path": {"type": "string", "description": "File path"}
        },
        "required": ["path"]
      }
    }
  ]
}
```

### POST /ai/complete

Single-shot completion without conversation history.

**Request:**

```json
{
  "model": "codellama",
  "prompt": "Write a Go function that validates an Ed25519 signature:",
  "temperature": 0.3,
  "max_tokens": 1024,
  "stop": ["\n\n"]
}
```

**Response:**

```json
{
  "id": "cpl-def456",
  "model": "codellama",
  "provider": "ollama",
  "text": "func verifySignature(pubKeyHex, sigHex string, data []byte) bool {\n...",
  "usage": {
    "prompt_tokens": 18,
    "completion_tokens": 95,
    "total_tokens": 113
  },
  "finish_reason": "stop",
  "latency_ms": 800
}
```

### POST /ai/extract

Structured data extraction using a JSON schema. The endpoint
instructs the model to return valid JSON matching the schema.

**Request:**

```json
{
  "model": "gpt-4o-mini",
  "input": "<html><head><title>Home</title></head><body><h1>Welcome</h1><img src='logo.png'></body></html>",
  "schema": {
    "type": "object",
    "properties": {
      "title": {"type": "string"},
      "h1_count": {"type": "integer"},
      "images_missing_alt": {"type": "integer"}
    },
    "required": ["title", "h1_count", "images_missing_alt"]
  },
  "instructions": "Extract SEO metadata from the HTML"
}
```

**Response:**

```json
{
  "id": "ext-ghi789",
  "model": "gpt-4o-mini",
  "provider": "openai",
  "data": {
    "title": "Home",
    "h1_count": 1,
    "images_missing_alt": 1
  },
  "usage": {
    "prompt_tokens": 85,
    "completion_tokens": 32,
    "total_tokens": 117
  },
  "latency_ms": 650
}
```

Extraction MUST validate the returned JSON against the provided schema.
If validation fails, the endpoint SHOULD retry once with a corrective
prompt before returning an error.

### POST /ai/embed

Generate vector embeddings for text.

**Request:**

```json
{
  "model": "nomic-embed-text",
  "input": ["SEO audit report for index.html", "Accessibility findings"],
  "dimensions": 768
}
```

**Response:**

```json
{
  "id": "emb-jkl012",
  "model": "nomic-embed-text",
  "provider": "ollama",
  "embeddings": [
    {"index": 0, "values": [0.023, -0.451, ...]},
    {"index": 1, "values": [0.112, -0.089, ...]}
  ],
  "usage": {
    "total_tokens": 14
  }
}
```

### GET /ai/models

List available models across all configured providers.

**Response:**

```json
{
  "models": [
    {"name": "llama3", "provider": "ollama", "type": "chat", "status": "available"},
    {"name": "gpt-4o", "provider": "openai", "type": "chat", "status": "available"},
    {"name": "nomic-embed-text", "provider": "ollama", "type": "embedding", "status": "available"}
  ]
}
```

### GET /ai/health

Provider connectivity and latency.

**Response:**

```json
{
  "providers": [
    {"name": "ollama", "status": "healthy", "latency_ms": 12, "models_available": 3},
    {"name": "openai", "status": "healthy", "latency_ms": 180, "models_available": 2}
  ]
}
```

## Types

### ChatRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model | string | no | Model name (uses default if omitted) |
| messages | []Message | yes | Conversation history |
| temperature | float | no | Sampling temperature (0.0–2.0, default: 0.7) |
| max_tokens | int | no | Max response tokens (default: 4096) |
| tools | []ToolDef | no | Available tools for function calling |
| stream | bool | no | Stream response tokens (default: false) |
| trace_id | string | no | Correlation ID for tracing |

### Message

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| role | string | yes | `system`, `user`, `assistant`, or `tool` |
| content | string | yes | Message content |
| tool_call_id | string | no | ID of the tool call this message responds to |

### ChatResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Response identifier |
| model | string | yes | Model used |
| provider | string | yes | Provider used |
| message | Message | yes | Assistant response |
| tool_calls | []ToolCall | no | Tool invocations requested by model |
| usage | Usage | yes | Token usage |
| latency_ms | int | yes | End-to-end latency |
| trace_id | string | no | Correlation ID |

### ExtractRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model | string | no | Model name |
| input | string | yes | Text to extract from |
| schema | object | yes | JSON Schema for output shape |
| instructions | string | no | Additional extraction guidance |

### EmbedRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| model | string | no | Embedding model name |
| input | []string | yes | Texts to embed |
| dimensions | int | no | Output dimensions (if model supports it) |

### Usage

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| prompt_tokens | int | yes | Input tokens consumed |
| completion_tokens | int | no | Output tokens generated |
| total_tokens | int | yes | Total tokens |

### ToolDef

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Tool identifier |
| description | string | yes | What the tool does |
| parameters | object | yes | JSON Schema for tool parameters |

### ToolCall

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Call identifier (for matching responses) |
| name | string | yes | Tool name |
| arguments | object | yes | Parsed arguments |

## Provider Abstraction

Implementations MUST normalise provider-specific formats into the
universal contract above. Provider differences are hidden entirely:

| Feature | OpenAI | Anthropic | Ollama | Workers AI |
|---------|--------|-----------|--------|------------|
| Chat format | `messages` array | `messages` array | `messages` array | `messages` array |
| Tool calling | `tools` + `tool_choice` | `tools` + `tool_use` | `tools` (v0.5+) | Not supported |
| Streaming | SSE `data:` lines | SSE `event:` lines | Newline-delimited JSON | SSE `data:` lines |
| Auth | `Authorization: Bearer` | `x-api-key` header | None (local) | Worker binding |
| Embeddings | `/v1/embeddings` | Not supported | `/api/embeddings` | Binding call |

The api-ai endpoint translates between the universal contract and
each provider's format. Agents never see provider-specific payloads.

## Configuration

```bash
# Default provider and model
WL_AI_PROVIDER=ollama
WL_AI_MODEL=llama3

# Provider-specific keys
WL_AI_OPENAI_KEY=sk-...
WL_AI_ANTHROPIC_KEY=sk-ant-...

# Rate limits
WL_AI_RATE_LIMIT=60          # requests per minute
WL_AI_MAX_CONCURRENT=5       # concurrent inference requests

# Timeouts
WL_AI_TIMEOUT=120             # seconds per request
WL_AI_RETRY_COUNT=2           # retries on transient failure
```

## Model Routing

When an agent requests a model by name, the api-ai endpoint resolves
which provider to use. This decouples agents from provider knowledge —
agents request capabilities, the router finds the best match.

### Resolution Order

```
1. Exact match — model name matches a configured provider's model list
2. Cross-provider search — check all providers for the model name
3. Capability fallback — if no exact match, select the best model
   for the request type (chat, embed, extract) from the default provider
4. 404 — no suitable model found
```

### Routing Table

The routing table maps model names to providers. It is built at
startup from provider configuration and updated when GET `/ai/health`
detects provider changes.

```yaml
routing:
  # Explicit model → provider mapping (overrides auto-discovery)
  overrides:
    "gpt-4o": openai
    "claude-sonnet-4-20250514": anthropic
    "llama3": ollama

  # Capability-based fallback chains (used when model is omitted)
  fallback:
    chat: [ollama/llama3, openai/gpt-4o-mini, anthropic/claude-haiku-4-20250414]
    embed: [ollama/nomic-embed-text, openai/text-embedding-3-small]
    extract: [openai/gpt-4o-mini, ollama/llama3]

  # Cost-aware routing — prefer cheaper models when quality is sufficient
  cost_preference: lowest  # lowest | balanced | highest_quality
```

### Request-Level Override

Callers MAY specify both `model` and `provider` to bypass routing:

```json
{
  "model": "gpt-4o",
  "provider": "openai",
  "messages": [...]
}
```

When `provider` is specified, the router skips resolution and sends
directly to that provider. If the model is not available on the
specified provider, return 404.

### Provider Health-Aware Routing

The router tracks provider health from GET `/ai/health` responses.
When a provider is unhealthy:

1. Remove its models from the active routing table.
2. Route requests for those models to the next provider in the
   fallback chain.
3. Re-check the provider on the next health poll interval (default:
   60s).
4. Restore routing when the provider returns to healthy.

### Token Budget Routing

For cost-sensitive deployments, the router MAY enforce per-agent
token budgets:

```bash
# Monthly token budget per agent (0 = unlimited)
WL_AI_TOKEN_BUDGET=1000000

# Action when budget exceeded: block | downgrade | alert
WL_AI_BUDGET_ACTION=downgrade
```

When `downgrade` is configured and an agent exceeds its budget, the
router automatically selects a cheaper model from the fallback chain
(e.g., gpt-4o → gpt-4o-mini → llama3). When `block` is configured,
return 429 with `TOKEN_BUDGET_EXCEEDED`.

## Implementation Notes

- **Provider failover**: If the primary provider returns a 5xx or
  times out, the endpoint SHOULD fall back to a secondary provider
  if configured. Failover is transparent to the caller.
- **Streaming**: When `stream: true`, the response MUST use
  Server-Sent Events (SSE). Each event contains a partial
  `ChatResponse` with incremental `message.content`.
- **Token tracking**: Usage data MUST be tracked per-agent (using
  `trace_id` to attribute to the calling agent) for cost attribution.
- **Schema validation**: The `/ai/extract` endpoint MUST validate
  extracted JSON against the provided schema before returning. Invalid
  extractions trigger one retry with an error-correction prompt.
- **Model routing**: If the requested model is not available on the
  configured provider, the endpoint SHOULD check other providers
  before returning 404.
- **Input limits**: Request body MUST be capped at 1 MB. Prompts
  exceeding the model's context window SHOULD return 400 with
  `INVALID_REQUEST` and the model's token limit in `detail`.
- **Response caching**: Deterministic responses (temperature = 0) and
  embeddings MAY be cached per [patterns/caching](caching.md).

## Verification Checklist

- [ ] POST `/ai/chat` returns valid `ChatResponse` with usage data
- [ ] POST `/ai/complete` returns completion text with finish_reason
- [ ] POST `/ai/extract` returns JSON matching the provided schema
- [ ] POST `/ai/extract` retries once on schema validation failure
- [ ] POST `/ai/embed` returns embeddings with correct dimensions
- [ ] GET `/ai/models` lists all configured providers and models
- [ ] GET `/ai/health` reports per-provider status and latency
- [ ] Unknown model returns 404 with helpful error
- [ ] Provider failover is transparent to the caller
- [ ] Token usage is tracked per request with trace_id attribution
- [ ] Streaming responses use SSE format
- [ ] Request body is capped at 1 MB
- [ ] Rate limiting returns 429 with Retry-After header
- [ ] All responses include `latency_ms` for observability
- [ ] Tool calling works across providers that support it
- [ ] Provider-specific formats are fully normalised
- [ ] Model routing resolves across providers when model not on default
- [ ] Fallback chain activates when provider is unhealthy
- [ ] Request-level provider override bypasses routing
- [ ] Token budget enforcement works in block and downgrade modes
