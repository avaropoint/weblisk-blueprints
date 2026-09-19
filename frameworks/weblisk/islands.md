# Island Blueprints

> Interactive regions: agent binding, real-time protocols, auth,
> computed logic, and state management.

## Purpose

Islands are the bridge between static pages and server-side
functionality. An island is a self-contained interactive region that
hydrates independently, binds to a server agent, and manages its own
state. This is where real-time behavior, computed forms, live data, and
authenticated interactions live.

## Structure

```yaml
# blueprints/islands/live-feed.yaml
type: island
name: live-feed

agent: content-stream
protocol: websocket
auth: session

data:
  format: json-stream
  schema:
    type: object
    properties:
      id: string
      content: string
      author: string
      timestamp: datetime

behavior:
  reconnect: exponential
  max_reconnect: 5
  heartbeat: 30s
  buffer: 50

ui:
  loading: skeleton
  empty: "No updates yet"
  error: "Connection lost. Reconnecting..."
  transition: slide-in
  max_items: 50
  virtualize: true

accessibility:
  aria_live: polite
  aria_label: "Live content feed"
  announce_new: true
```

## Fields

### Agent Binding

| Field | Type | Description |
|-------|------|-------------|
| `agent` | string | Server agent this island communicates with |
| `protocol` | `websocket`, `sse`, `polling`, `request` | Communication protocol |
| `auth` | `session`, `token`, `none` | Authentication requirement |
| `endpoint` | string | Override agent endpoint (default: derived from agent name) |

### Protocol Details

**WebSocket** — Persistent bidirectional connection:
```yaml
protocol: websocket
behavior:
  reconnect: exponential     # backoff: 1s, 2s, 4s, 8s...
  heartbeat: 30s             # keep-alive ping interval
  buffer: 50                 # max queued messages during reconnect
```

**Server-Sent Events** — One-way server push:
```yaml
protocol: sse
behavior:
  reconnect: immediate
  last_event_id: true        # resume from last received event
```

**Polling** — Periodic fetch:
```yaml
protocol: polling
behavior:
  interval: 5000             # ms between requests
  adaptive: true             # slow down when idle, speed up on activity
```

**Request** — One-shot request/response (forms, actions):
```yaml
protocol: request
behavior:
  method: post
  debounce: 300ms
  optimistic: true           # update UI before server confirms
```

### Data Schema

Declares the shape of data flowing between agent and island. The LLM
uses this to generate typed handlers:

```yaml
data:
  format: json               # or: json-stream, binary, text
  schema:
    type: object
    properties:
      id: string
      amount: number
      status: { type: string, enum: [pending, complete, failed] }
```

### Computed Logic

For islands with client-side calculations (forms, calculators,
configurators):

```yaml
# blueprints/islands/quote-calculator.yaml
type: island
name: quote-calculator
protocol: request
agent: pricing-engine

fields:
  - name: base_price
    type: number
    source: product.price
    readonly: true
  - name: quantity
    type: number
    min: 1
    max: 100
    default: 1
  - name: discount_code
    type: string
    validate: server          # validated by agent

computed:
  subtotal: "base_price * quantity"
  discount: "discount_code ? await validate(discount_code) : 0"
  shipping_cost:
    standard: 0
    express: 14.99
    overnight: 29.99
  tax: "(subtotal - discount) * tax_rate"
  total: "subtotal - discount + shipping_cost[selected_shipping] + tax"

behavior:
  recompute: on-change
  debounce: 300ms
  submit: agent:create-order
```

The `computed` block describes a reactive dependency graph. The LLM
generates signal-based JavaScript that updates derived values when
inputs change.

### State Machines

For multi-step interactions (wizards, checkout flows):

```yaml
# blueprints/islands/checkout.yaml
type: island
name: checkout
agent: order-service

state:
  type: machine
  initial: cart
  states:
    cart:
      transitions:
        proceed: { target: shipping, guard: "items.length > 0" }
    shipping:
      transitions:
        back: cart
        proceed: { target: payment, guard: "address != null" }
    payment:
      transitions:
        back: shipping
        submit: { target: confirming, action: "await agent:charge" }
    confirming:
      transitions:
        success: confirmed
        failure: { target: payment, action: "showError" }
    confirmed:
      final: true

ui:
  progress: steps            # show step indicator
  transition: slide-horizontal
```

### Inter-Island Communication

Islands are isolated by default but can communicate via events:

```yaml
# blueprints/islands/filter-bar.yaml
type: island
name: filter-bar
protocol: none               # no agent, client-only

emits:
  - event: filter-changed
    payload: { category: string, sort: string }

# blueprints/islands/product-grid.yaml
type: island
name: product-grid
agent: product-search

listens:
  - event: filter-changed
    action: refetch           # re-query agent with new filters
```

## UI Declarations

| Field | Values | Description |
|-------|--------|-------------|
| `loading` | `skeleton`, `spinner`, `none` | Pre-hydration state |
| `empty` | string | Message when no data |
| `error` | string | Message on failure |
| `transition` | `slide-in`, `fade`, `none` | Item entry animation |
| `virtualize` | boolean | Virtual scroll for large lists |
| `max_items` | number | Visible item cap |

## Accessibility

| Field | Values | Description |
|-------|--------|-------------|
| `aria_live` | `polite`, `assertive`, `off` | How updates are announced |
| `aria_label` | string | Accessible name for the region |
| `announce_new` | boolean | Screen reader announces new items |
| `focus_management` | `trap`, `roving`, `none` | Focus behavior within island |

## Escape Hatch

For logic too complex to declare:

```yaml
type: island
name: custom-visualizer
custom:
  src: src/islands/custom-viz.js
  managed: false
agent: data-source
```

The `custom.src` file is hand-written. The pipeline won't overwrite it.
It still connects to the declared agent and follows island hydration
rules — it just has a custom implementation.
