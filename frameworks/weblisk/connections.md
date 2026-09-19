# Connection Blueprints

> External integrations, protocols, and data sources.

## Purpose

Connections declare how the project communicates with external services.
They define the protocol, authentication, agent binding, and client-side
behavior for third-party integrations — without embedding API keys or
implementation details in page blueprints.

## Structure

```yaml
# blueprints/connections/analytics.yaml
type: connection
name: analytics
provider: plausible

config:
  domain: myproduct.com
  api_host: https://plausible.io

client:
  script: https://plausible.io/js/script.js
  loading: async
  position: head
  events:
    - name: signup
      trigger: form-submit
    - name: pricing-click
      trigger: click
      selector: "[data-track='pricing']"
```

## Fields

### Top-Level

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `type` | `connection` | ✅ | Always "connection" |
| `name` | string | ✅ | Identifier |
| `provider` | string | — | Named provider (for LLM context) |
| `protocol` | string | — | `https`, `websocket`, `grpc`, `graphql` |
| `auth` | string | — | Auth method: `api-key`, `oauth`, `token`, `none` |
| `agent` | string | — | Server agent that proxies this connection |

### Client-Side Connections

For services that load directly in the browser (analytics, maps, chat
widgets):

```yaml
client:
  script: URL                 # external script to load
  loading: async | defer      # script loading strategy
  position: head | body-end   # where to inject
  consent: required           # needs cookie consent first
  events: []                  # custom event tracking
```

### Server-Side Connections (via Agent)

For services that require secrets or server-side logic:

```yaml
# blueprints/connections/stripe.yaml
type: connection
name: stripe
provider: stripe
protocol: https
auth: api-key
agent: payment-handler

endpoints:
  checkout:
    method: post
    path: /create-checkout-session
    response: { url: string }
  webhook:
    events:
      - checkout.session.completed
      - payment_intent.failed

client:
  redirect: stripe-hosted
  success: /order/confirmed
  cancel: /cart
```

The agent handles the actual Stripe API calls. The island that triggers
checkout communicates with the agent, not directly with Stripe.

### Database / Data Source

```yaml
# blueprints/connections/content-api.yaml
type: connection
name: content-api
protocol: https
auth: token
agent: content-proxy

data:
  format: json
  cache: 300s
  endpoints:
    posts:
      path: /api/posts
      method: get
      paginated: true
    post:
      path: /api/posts/{slug}
      method: get
```

### WebSocket Streams

```yaml
# blueprints/connections/market-data.yaml
type: connection
name: market-data
protocol: websocket
auth: token
agent: market-feed

stream:
  subscribe: { symbols: ["AAPL", "GOOG"] }
  format: json
  heartbeat: 10s
  reconnect: exponential

schema:
  type: object
  properties:
    symbol: string
    price: number
    change: number
    timestamp: datetime
```

## Security Model

Connections follow these rules:

1. **Secrets never in blueprints.** API keys live in `.weblisk/config.yaml`
   or environment variables. The blueprint declares *that* auth is needed,
   not the credentials.

2. **Client-side connections are limited.** Only public/consent-gated
   scripts (analytics, maps, fonts). Anything requiring secrets goes
   through an agent.

3. **Agent proxies all authenticated calls.** The island talks to the
   local agent. The agent talks to the external service. Credentials
   stay server-side.

## Relationship to Islands

An island's `agent` field often points to an agent that uses a
connection:

```
Island (quote-calculator)
  → Agent (pricing-engine)
    → Connection (stripe)
```

The island blueprint declares the UX. The connection blueprint declares
the integration. The agent blueprint declares the logic between them.
