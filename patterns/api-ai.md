<!-- blueprint
type: pattern
name: api-ai
version: 2.4.2
requires: [protocol/types, patterns/scope, architecture/agent, architecture/gateway, architecture/orchestrator]
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
  - blueprint: protocol/types
    version: ">=1.13.0 <3.0.0"
    bindings:
      types:
        - name: AgentManifest
          fields_used: [name, type, version, capabilities]
        - name: ErrorResponse
          fields_used: [error, code, category, retryable]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/scope
    version: ">=2.6.0 <3.0.0"
    bindings:
      types:
        # An enum: it declares values, not fields, so nothing is bound FROM it.
        - name: ScopeLevel
        - name: ProviderCeiling
          fields_used: [backend, model, ceiling]
        - name: DestinationRefusal
          fields_used: [destination, ceiling, items]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/agent
    version: ">=1.0.0 <2.0.0"
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <3.0.0"
    bindings:
      types:
        - name: Route
          fields_used: [path, methods, rate_limit]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/orchestrator
    version: ">=2.14.0 <3.0.0"
    bindings:
      endpoints:
        # Read before every send. See Destination Ceilings
        - path: /v1/model/ceiling
          methods: [GET]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Provider-agnostic** — All intelligence access flows through a universal contract that abstracts provider-specific details. Switching between local and remote is a configuration change, not a code change.
2. **Local-first** — The default configuration uses local models (Ollama) with no external API keys, no external dependencies, and no data leaving the deployment.
3. **Centralized gateway** — Rather than each agent implementing its own provider integration, the api-ai pattern provides a single gateway that enforces rate limits, tracks usage, applies the destination gate, and routes to the configured provider.
4. **Structured extraction** — Beyond free-form chat, the pattern supports schema-validated data extraction, ensuring AI outputs conform to expected shapes.
5. **A provider is a destination** — Every provider is a model provider with a ceiling ([`patterns/scope`](scope.md#model-providers)). Nothing reaches a provider above its ceiling, and no routing decision — resolution, failover or override — moves a request to one whose ceiling is below it. See [Destination Ceilings](#destination-ceilings).
6. **A model is never swapped** — A request runs the model it names, or the one a person chose in the configuration, or, where neither names one, whatever the provider runs when asked for none. A model that cannot run is an error, never a reason to run another: no routing decision, failure or budget moves a request to a different model. Nothing in this pattern names a default model, and the model a response reports is the one the provider's answer says ran. See [Model Routing](#model-routing).

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
          description: The model to run. Omitted, the one a person chose in the configuration, else whatever the provider runs when asked for none. A model that cannot run is refused, never replaced
        - name: messages
          type: "[]Message"
          required: true
          description: Conversation history
        - name: scope
          type: ScopeLevel
          required: false
          description: The highest scope of what the request carries. Absent is refused with SCOPE_MISSING — see Destination Ceilings
        - name: temperature
          type: float
          required: false
          description: Sampling temperature (0.0–2.0)
      inherits: ChatRequest/ChatResponse shape, and the destination gate on every provider it reaches
      overridable: true
      override_constraints: Must preserve Message schema and Usage reporting. The destination gate is not overridable

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
        - name: scope
          type: ScopeLevel
          required: false
          description: As for conversational-inference
      inherits: ExtractRequest/ExtractResponse shape, and the destination gate on every provider it reaches
      overridable: true
      override_constraints: Must validate output against provided schema. The destination gate is not overridable

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
version: 2.1.0
description: AI-first communication with language models and intelligence services

providers:
  ollama:
    type: local
    base_url: http://localhost:11434

  openai:
    type: remote
    auth: bearer
    key: <configured via secrets>
    models: [<a model a person chose from this provider's own list>]

  anthropic:
    type: remote
    auth: x-api-key
    key: <configured via secrets>
    models: [<a model a person chose from this provider's own list>]

  workers-ai:
    type: platform
    binding: AI
    models: [<a model a person chose from this platform's own catalogue>]

defaults:
  provider: ollama
  model: <a model a person chose from that provider's own list; absent, the provider decides>
  temperature: 0.7
  max_tokens: 4096
  timeout: 120
```

A provider's models are what its own list answers, asked by the endpoint and
never written down here: a local model server's loaded and loadable models, a
vendor API's model list. `models:` narrows a provider to those a person chose
from that list, and absent it offers all of them. `defaults.model` is the one
a request that names none runs, and it too is a person's choice. Where nobody
chose one, the provider decides: a local model server runs the first model it
reports loaded, and a provider that runs nothing unless a model is named
refuses the request. The values above are placeholders, and no model name is
a default of this pattern.

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

The request names no model, so it runs the one the configuration chose, or
the provider's own choice.

```json
{
  "scope": "internal",
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
  "model": "<the model the provider's answer says ran>",
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
  "scope": "public",
  "prompt": "Write a Go function that validates an ML-DSA-65 signature:",
  "temperature": 0.3,
  "max_tokens": 1024,
  "stop": ["\n\n"]
}
```

**Response:**

```json
{
  "id": "cpl-def456",
  "model": "<the model the provider's answer says ran>",
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
  "model": "<a model GET /ai/models lists for openai>",
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
  "model": "<the model the provider's answer says ran>",
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
  "model": "<an embedding model GET /ai/models lists>",
  "input": ["SEO audit report for index.html", "Accessibility findings"],
  "dimensions": 768
}
```

**Response:**

```json
{
  "id": "emb-jkl012",
  "model": "<the model the provider's answer says ran>",
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

List available models across all configured providers: what each provider's
own list answered when the endpoint last asked it, narrowed to a provider's
`models:` where it has one. Nothing here is written down in advance.

**Response:**

```json
{
  "models": [
    {"name": "<a model the ollama server lists>", "provider": "ollama", "type": "chat", "status": "available"},
    {"name": "<a model the openai list holds, chosen in models:>", "provider": "openai", "type": "chat", "status": "available"},
    {"name": "<an embedding model the ollama server lists>", "provider": "ollama", "type": "embedding", "status": "available"}
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

```yaml
types:
  ChatRequest:
    fields:
      model:
        type: string
        required: false
        description: "The model to run. Absent: the one a person chose in the configuration, else whatever the provider runs when asked for none. A model that cannot run is refused, never replaced by another (Model Routing)"
      scope:
        type: ScopeLevel
        required: false
        description: "The highest scope of what the request carries, as the tenant reported it to the caller. Absent when any of it is undeclared, and then refused with SCOPE_MISSING. A request carrying nothing the tenant holds says public. See Destination Ceilings"
      messages:
        type: "[]Message"
        required: true
        description: "Conversation history"
      temperature:
        type: float
        required: false
        description: "Sampling temperature (0.0–2.0, default: 0.7)"
      max_tokens:
        type: int
        required: false
        description: "Max response tokens (default: 4096)"
      tools:
        type: "[]ToolDef"
        required: false
        description: "Available tools for function calling"
      stream:
        type: bool
        required: false
        description: "Stream response tokens (default: false)"
      trace_id:
        type: string
        required: false
        description: "Correlation ID for tracing"
```

### Message

```yaml
types:
  Message:
    fields:
      role:
        type: string
        required: true
        description: "`system`, `user`, `assistant`, or `tool`"
      content:
        type: string
        required: true
        description: "Message content"
      tool_call_id:
        type: string
        required: false
        description: "ID of the tool call this message responds to"
```

### ChatResponse

```yaml
types:
  ChatResponse:
    fields:
      id:
        type: string
        required: true
        description: "Response identifier"
      model:
        type: string
        required: false
        description: "The model the provider's own answer says ran, spelt as it spells it, so a moving alias the request or the configuration gave is reported as the model it reached. Absent where the provider's answer names none: the endpoint never reports the name it asked for as the one that ran"
      provider:
        type: string
        required: true
        description: "The provider that ran it, which names a failover"
      message:
        type: Message
        required: true
        description: "Assistant response"
      tool_calls:
        type: "[]ToolCall"
        required: false
        description: "Tool invocations requested by model"
      usage:
        type: Usage
        required: true
        description: "Token usage"
      latency_ms:
        type: int
        required: true
        description: "End-to-end latency"
      trace_id:
        type: string
        required: false
        description: "Correlation ID"
```

### ExtractRequest

```yaml
types:
  ExtractRequest:
    fields:
      model:
        type: string
        required: false
        description: "As on ChatRequest"
      scope:
        type: ScopeLevel
        required: false
        description: "As on ChatRequest"
      input:
        type: string
        required: true
        description: "Text to extract from"
      schema:
        type: object
        required: true
        description: "JSON Schema for output shape"
      instructions:
        type: string
        required: false
        description: "Additional extraction guidance"
```

### EmbedRequest

```yaml
types:
  EmbedRequest:
    fields:
      model:
        type: string
        required: false
        description: "The embedding model, as on ChatRequest"
      scope:
        type: ScopeLevel
        required: false
        description: "As on ChatRequest"
      input:
        type: "[]string"
        required: true
        description: "Texts to embed"
      dimensions:
        type: int
        required: false
        description: "Output dimensions (if model supports it)"
```

### Usage

```yaml
types:
  Usage:
    fields:
      prompt_tokens:
        type: int
        required: true
        description: "Input tokens consumed"
      completion_tokens:
        type: int
        required: false
        description: "Output tokens generated"
      total_tokens:
        type: int
        required: true
        description: "Total tokens"
```

### ToolDef

```yaml
types:
  ToolDef:
    fields:
      name:
        type: string
        required: true
        description: "Tool identifier"
      description:
        type: string
        required: true
        description: "What the tool does"
      parameters:
        type: object
        required: true
        description: "JSON Schema for tool parameters"
```

### ToolCall

```yaml
types:
  ToolCall:
    fields:
      id:
        type: string
        required: true
        description: "Call identifier (for matching responses)"
      name:
        type: string
        required: true
        description: "Tool name"
      arguments:
        type: object
        required: true
        description: "Parsed arguments"
```

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

The AI provider is configured via runtime settings:

```yaml
ai:
  provider: ollama              # The provider a request that names none runs on
  model: <a model a person chose from that provider's own list; absent, the provider decides>
  keys:
    openai: <configured via secrets>
    anthropic: <configured via secrets>
  rate_limit: 60                 # requests per minute
  max_concurrent: 5              # concurrent inference requests
  timeout: 120                   # seconds per request
  retry_count: 2                 # retries on transient failure
```

## Model Routing

When an agent requests a model by name, the api-ai endpoint resolves
which provider runs it, so the agent needs no provider knowledge. It
resolves a provider for a model and never a model for a request: the model
a request runs is the one it names, or the one a person chose, or the
provider's own choice where nobody chose one.

### Resolution Order

```
1. A request that names a model runs that model: on the provider the
   request names (Request-Level Override), else on the provider whose
   own list holds that name exactly, routing.overrides choosing where
   two providers list it
2. A request that names none runs defaults.model on the default
   provider, and where nobody chose one, whatever that provider runs
   when asked for none. A provider that runs nothing unless a model is
   named refuses the request
3. A model no provider's list holds is refused with 404. No other model
   runs in its place
```

### Routing Table

The routing table maps model names to providers. It is built at
startup from what each provider's own list answers, and rebuilt when GET
`/ai/health` detects provider changes. It maps a name to a provider and
never to another name.

```yaml
routing:
  # Which provider runs a model name that two providers both list
  overrides:
    "<a model name two providers both list>": openai
```

### Request-Level Override

Callers MAY specify both `model` and `provider` to bypass routing:

```json
{
  "model": "<a model GET /ai/models lists for openai>",
  "provider": "openai",
  "messages": [...]
}
```

When `provider` is specified, the router skips resolution and sends
directly to that provider. If the model is not available on the
specified provider, return 404. The destination gate still applies, to
the named provider and the named model together: where the ceiling the
tenant gives that provider for that model is below the request's `scope`,
the request is refused, and the router never sends it to another provider
or model instead ([Destination Ceilings](#destination-ceilings)).

### Provider Health-Aware Routing

The router tracks provider health from GET `/ai/health` responses.
When a provider is unhealthy:

1. Remove its models from the active routing table.
2. Route a request for one of those models to another provider whose
   own list holds the same model under the same name and whose ceiling
   covers the request's `scope`. Where no other provider lists it,
   refuse it with 503 `MODEL_UNAVAILABLE`, naming the model and its
   provider; where every one that lists it is below the request's
   `scope`, refuse it with `SCOPE_CEILING_EXCEEDED`
   ([Destination Ceilings](#destination-ceilings)). Never run a
   different model instead.
3. Re-check the provider on the next health poll interval (default:
   60s).
4. Restore routing when the provider returns to healthy.

### Token Budget Routing

For cost-sensitive deployments, the router MAY enforce per-agent
token budgets:

```yaml
# Monthly token budget per agent (0 = unlimited)
ai_token_budget: 1000000

# Action when budget exceeded: block | alert
ai_budget_action: block
```

When `block` is configured and an agent exceeds its budget, return 429
with `TOKEN_BUDGET_EXCEEDED`. When `alert` is configured, the request runs
as asked and the endpoint raises an alert. Neither moves a request to
another model: a budget limits use, and is never a reason to run a model
other than the one asked for.

### Destination Ceilings

A component that serves these endpoints declares `model:route` in its
manifest ([`protocol/types`](../protocol/types.md)): it is the tenant's model
route, and the external boundary admits a call to a provider's address from
nothing that does not declare it
([`architecture/enforcement`](../architecture/enforcement.md#external-proxy)).

Every provider this endpoint reaches is a model provider
([`patterns/scope`](scope.md#model-providers)), and its ceiling is the
one the tenant gives the provider's key under `providers:` and the model
the request would ask it for, the one it names or else `defaults.model`, as
`GET /v1/model/ceiling?backend=<key>&model=<model>` answers it
([`architecture/orchestrator`](../architecture/orchestrator.md#a-model-is-a-destination)).
Where neither names one, the request names no model and its ceiling is
`internal`, whatever the provider then runs, a local model server's first
loaded model included
([`patterns/scope`](scope.md#model-providers), why an agreement lists models).
That route takes this endpoint's own registration token; the administrative
route of the same name takes only a person's. It answers every key and model with a
`ProviderCeiling`, whether or not the tenant's model configuration names
them: a provider key no current agreement lists, and a model the agreement
listing the key does not list, has the ceiling `internal`. The ceiling is the
model's as well as the key's, because at an aggregator or a gateway the model
chooses who runs it, so each step the router weighs below is a key and a
model, and is gated as one. It
refuses only a token it does not accept, with a code
[`protocol/types`](../protocol/types.md#errorresponse) registers, and an
endpoint that cannot learn a ceiling uses `internal`.

Before any request is sent, this endpoint applies the destination gate
([`patterns/scope`](scope.md#the-gate)) to the request's `scope` and
the chosen provider's ceiling:

- **No scope** — refused with `SCOPE_MISSING`.
- **`restricted` or above** — refused with `SCOPE_CEILING_EXCEEDED`,
  whatever any provider's ceiling.
- **Above the chosen provider's ceiling** — the router may choose only
  among providers whose ceiling covers `scope`, and only among those that
  list the same model: in resolution, a failover and an override alike.
  When none does, the request is refused with `SCOPE_CEILING_EXCEEDED`.

Each refusal carries one `DestinationRefusal`, naming the provider the
router chose first, by resolution or the caller's override, and that
provider's ceiling. Where the router considered others, none of them covered
`scope` either, and the refusal does not list them. It sends nothing. The gate is never
audit-only, in any environment profile. A request is never moved to a
provider whose ceiling is below its `scope`, and never with its
content cut down to fit. When a request is served by a provider other
than the one first chosen, the response's `provider` says so.

## Implementation Notes

- **Provider failover**: If the primary provider returns a 5xx or
  times out, the endpoint MAY send the request to another provider whose
  own list holds the same model under the same name and whose ceiling
  covers the request's `scope` (see
  [Destination Ceilings](#destination-ceilings)). Otherwise it refuses,
  as [Provider Health-Aware Routing](#provider-health-aware-routing)
  says. It never sends the request for a different model. The response's `provider` names the provider that ran
  the request, and its `model` the model that provider reported.
- **Streaming**: When `stream: true`, the response MUST use
  Server-Sent Events (SSE). Each event contains a partial
  `ChatResponse` with incremental `message.content`.
  If the requested model or provider does not support streaming, the
  endpoint MUST return `406 Not Acceptable` with an `ErrorResponse`:
  `{"error": "Streaming not supported", "code": "STREAMING_UNSUPPORTED", "category": "client", "retryable": false, "detail": "Model '<model>' on provider '<provider>' does not support streaming. Retry with stream: false."}`
  Agents MUST NOT silently fall back to a non-streaming response when
  `stream: true` is explicitly requested — the caller may depend on
  SSE framing for incremental rendering.
- **Token tracking**: Usage data MUST be tracked per-agent (using
  `trace_id` to attribute to the calling agent) for cost attribution.
- **Schema validation**: The `/ai/extract` endpoint MUST validate
  extracted JSON against the provided schema before returning. Invalid
  extractions trigger one retry with an error-correction prompt.
- **Model routing**: If the requested model is not available on the
  configured provider, the endpoint SHOULD look for the same name in
  the lists of the other providers whose ceiling covers the request's
  `scope` before returning 404, and never runs another model instead.
- **The model that ran**: Every response's `model` is the one the
  provider's own answer names, never the name the request or the
  configuration gave where the provider reports another, and absent
  where the provider's answer names none.
- **Input limits**: Request body MUST be capped at 1 MB. Prompts
  exceeding the model's context window SHOULD return 400 with
  `INVALID_REQUEST` and the model's token limit in `detail`.
- **Response caching**: Deterministic responses (temperature = 0) and
  embeddings MAY be cached per [patterns/caching](caching.md).

## Verification Checklist

- [ ] POST `/ai/chat` returns valid `ChatResponse` with usage data
- [ ] POST `/ai/complete` returns completion text with `finish_reason`
- [ ] POST `/ai/extract` returns JSON matching the provided schema
- [ ] POST `/ai/extract` retries once on schema validation failure
- [ ] POST `/ai/embed` returns embeddings with correct dimensions
- [ ] GET `/ai/models` lists all configured providers and models
- [ ] GET `/ai/health` reports per-provider status and latency
- [ ] A request naming a model no provider's list holds is refused with 404 and a helpful error, and runs no other model
- [ ] Provider failover goes only to a provider whose own list holds the same model under the same name and whose ceiling covers the request's `scope`, is refused with `MODEL_UNAVAILABLE` where no other provider lists the model and with `SCOPE_CEILING_EXCEEDED` where every one that does is below the request's `scope`, and the response's `provider` names the provider that ran it
- [ ] A request that names no model where `defaults.model` is absent is gated at `internal`, even where the provider's first loaded model is one a current agreement lists, so a `confidential` one is refused with `SCOPE_CEILING_EXCEEDED`
- [ ] A request that names no model runs `defaults.model`, and where nobody chose one, a local model server's first loaded model; a provider that runs nothing unless a model is named refuses it
- [ ] Every response's `model` is the model the provider's answer names, absent where it names none, and never the name the request or the configuration gave where the provider reports another
- [ ] A request with no `scope` is refused with `SCOPE_MISSING`, and one at `restricted` with `SCOPE_CEILING_EXCEEDED`, whatever any provider's ceiling, and neither reaches a provider
- [ ] A provider key that no current agreement lists, whether or not the tenant's model configuration names it, gets the ceiling `internal` from `GET /v1/model/ceiling?backend=<key>`, and a `confidential` request to it is refused with `SCOPE_CEILING_EXCEEDED`
- [ ] A request whose `scope` is `confidential` goes only to a provider and a model a current agreement lists both of at `confidential`, through resolution, a failover and a request-level `provider` and `model` override alike
- [ ] A request-level override naming a provider a current agreement lists at `confidential` and a model that agreement does not list is gated at `internal`, the ceiling `GET /v1/model/ceiling?backend=<key>&model=<model>` answers, so a `confidential` request is refused with `SCOPE_CEILING_EXCEEDED` and sent nowhere else
- [ ] Token usage is tracked per request with `trace_id` attribution
- [ ] Streaming responses use SSE format
- [ ] Streaming request to a non-streaming model returns 406 Not Acceptable
- [ ] Request body is capped at 1 MB
- [ ] Rate limiting returns 429 with Retry-After header
- [ ] All responses include `latency_ms` for observability
- [ ] Tool calling works across providers that support it
- [ ] Provider-specific formats are fully normalised
- [ ] A model the default provider does not list runs on another provider whose list holds the same name, and never as another model
- [ ] A request for a model whose provider is unhealthy runs on another provider that lists the same model, or is refused with 503 `MODEL_UNAVAILABLE`, and never runs another model
- [ ] Request-level provider override bypasses routing
- [ ] Token budget enforcement works in `block` and `alert` modes, and neither runs a model other than the one asked for
