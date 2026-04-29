# Component Blueprints

> Reusable UI elements: props, slots, variants, and accessibility
> contracts.

## Purpose

Components are reusable building blocks referenced by pages and other
components. Each component blueprint declares its interface (props,
slots), behavior, variants, and accessibility requirements. The LLM
generates the implementation.

## Structure

```yaml
# blueprints/components/card.yaml
type: component
name: card

props:
  title: { type: string, required: true }
  description: { type: string }
  image: { type: string }
  href: { type: string }
  variant: { type: string, default: "default", enum: [default, featured, compact] }

slots:
  - name: header
  - name: body
    default: true
  - name: footer

variants:
  default:
    padding: 4
    radius: md
    shadow: sm
  featured:
    padding: 6
    radius: lg
    shadow: md
    border: accent
  compact:
    padding: 2
    radius: sm
    shadow: none

accessibility:
  role: article
  aria_label: "{title}"
  focus: true
  keyboard: enter-activates
```

## Fields

### Props

Input values the component accepts:

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | `string`, `number`, `boolean`, `array`, `object` |
| `required` | boolean | Whether the prop must be provided |
| `default` | any | Default value if not provided |
| `enum` | string[] | Allowed values |

### Slots

Named insertion points for child content:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Slot identifier |
| `default` | boolean | Receives unslotted children |
| `multiple` | boolean | Accepts multiple elements (repeat) |

### Variants

Named style presets. The `variant` prop selects which set of design
tokens applies. Each variant maps to theme tokens:

```yaml
variants:
  danger:
    background: error
    text: surface
    border: error
```

### Accessibility

Accessibility contract that the generated code MUST satisfy:

| Field | Values | Description |
|-------|--------|-------------|
| `role` | ARIA role | Semantic role for assistive tech |
| `aria_label` | template string | Computed accessible name |
| `focus` | boolean | Whether the component is focusable |
| `keyboard` | string | Keyboard interaction pattern |
| `live` | `polite`, `assertive` | ARIA live region behavior |

## Complex Components

### Data Table

```yaml
# blueprints/components/data-table.yaml
type: component
name: data-table

props:
  columns: { type: array, required: true }
  data: { type: array, required: true }
  sortable: { type: boolean, default: true }
  filterable: { type: boolean, default: true }
  paginate: { type: number, default: 25 }
  selectable: { type: boolean, default: false }

behavior:
  sort: client
  filter: debounced-300ms
  pagination: client
  keyboard: grid-navigation
  empty: "No results found"

accessibility:
  role: grid
  aria_sort: true
  aria_live: polite
  focus_trap: false
```

### Form

```yaml
# blueprints/components/form.yaml
type: component
name: form

props:
  action: { type: string, required: true }
  method: { type: string, default: "post", enum: [get, post] }
  validate: { type: string, default: "on-blur" }

slots:
  - name: fields
    default: true
  - name: actions

behavior:
  validation: on-blur
  submit: prevent-default
  error_display: inline
  success: redirect-or-message
  loading: disable-submit

accessibility:
  role: form
  aria_describedby: true
  error_announcement: assertive
  required_indicator: "(required)"
```

## Composition

Components can reference other components:

```yaml
# blueprints/components/pricing-card.yaml
type: component
name: pricing-card
uses:
  - components/card
  - components/button

props:
  plan: { type: object, required: true }
  highlighted: { type: boolean, default: false }

template:
  component: card
  variant: "{highlighted ? 'featured' : 'default'}"
  slots:
    header: "{plan.name} - {plan.price}/mo"
    body: "{plan.features}"
    footer:
      component: button
      text: "Choose {plan.name}"
      href: "/signup?plan={plan.id}"
```

The LLM resolves the composition tree and generates a single component
that incorporates both card and button patterns.
