<!-- blueprint
type: pattern
name: api-ai
version: 1.0.0
requires: [protocol/spec, protocol/types, architecture/agent]
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

This is the intelligence backbone of a Weblisk server — the way every
agent accesses LLM capabilities. Rather than each agent implementing
its own provider integration, the api-ai pattern provides a centralised
gateway that enforces rate limits, tracks usage, and routes to the
configured provider.

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
