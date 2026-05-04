# Shell Blueprint

> Client-side application shell: the entry point that bootstraps
> island hydration, registers services, and coordinates startup.

## Purpose

The shell is the single JavaScript entry point that initializes a
Weblisk client application. It's responsible for hydrating islands,
registering service workers, setting up global event listeners, and
deferring non-critical initialization. The shell itself is not an
island — it's the orchestrator that brings islands to life.

## Structure

```yaml
# Referenced in server or page blueprints
client:
  shell:
    module: js/islands/shell.js
    type: module

    responsibilities:
      - Hydrate all islands via import map
      - Register service worker
      - Defer non-critical init (security, a11y, perf, clipboard)

    hydration:
      strategy: import-map
      module: weblisk/core/hydrate.js
      strategies: [load, idle, visible, media, event, never]

    deferred:
      - name: security
        timing: idle
        description: CSP violation reporting, integrity checks
      - name: accessibility
        timing: idle
        description: Focus management, skip links, announcements
      - name: performance
        timing: idle
        description: Web Vitals collection, beacon reporting
      - name: clipboard
        timing: event
        trigger: user-interaction
        description: Copy-to-clipboard handlers

    service_worker:
      path: /sw.js
      scope: /
      registration: deferred
      update: on-navigate
```

## Fields

### Top-Level

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `module` | path | ✅ | Entry point file (relative to project root) |
| `type` | `module` | ✅ | Always ES module |
| `responsibilities` | string[] | ✅ | What the shell does (documentation for humans + LLMs) |

### Hydration

Declares how the shell discovers and hydrates islands:

| Field | Type | Description |
|-------|------|-------------|
| `strategy` | `import-map`, `dynamic-import`, `inline` | How island modules are resolved |
| `module` | string | Hydration runtime (from CDN or local) |
| `strategies` | string[] | Available hydration timing strategies |

Hydration strategies (applied per-island via `data-hydrate` or
blueprint `hydrate:` field):

| Strategy | Trigger | Use Case |
|----------|---------|----------|
| `load` | Immediately on page load | Critical UI (nav, auth) |
| `idle` | `requestIdleCallback` | Below-fold interactive content |
| `visible` | `IntersectionObserver` | Lazy content (carousels, feeds) |
| `media` | Media query match | Responsive-only interactivity |
| `event` | User interaction (click, hover, focus) | On-demand features |
| `never` | Not hydrated | Static HTML with no JS |

### Deferred Initialization

Non-critical modules loaded after the main paint:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Module identifier |
| `timing` | `idle`, `event`, `visible`, `timeout` | When to initialize |
| `trigger` | string | For event-based: what triggers initialization |
| `description` | string | What this deferred module does |

### Service Worker

| Field | Type | Description |
|-------|------|-------------|
| `path` | string | Service worker file path |
| `scope` | string | SW scope (usually `/`) |
| `registration` | `immediate`, `deferred`, `idle` | When to register |
| `update` | `on-navigate`, `on-focus`, `periodic` | Update check strategy |

## Conventions

### Startup Order

The shell MUST follow this initialization order:

1. **Hydrate critical islands** — `load` strategy islands first
2. **Register service worker** — after first paint
3. **Hydrate deferred islands** — `idle` strategy islands
4. **Initialize deferred modules** — non-critical features
5. **Hydrate lazy islands** — `visible`/`event` as triggered

### Import Maps

When using `strategy: import-map`, the HTML document MUST contain
an `<script type="importmap">` block that maps bare specifiers to
CDN URLs:

```html
<script type="importmap">
{
  "imports": {
    "weblisk": "https://cdn.weblisk.dev/weblisk.js",
    "weblisk/": "https://cdn.weblisk.dev/"
  }
}
</script>
```

The shell then imports from bare specifiers:
```javascript
import { hydrate } from 'weblisk/core/hydrate.js';
```

### Error Boundaries

The shell MUST NOT crash if an individual island fails to hydrate.
Each island hydration is wrapped in a try/catch. Failed islands log
the error and leave the static HTML in place (graceful degradation).

### No Global State

The shell does NOT manage application state. State is handled by
individual islands via signals (see `standards/islands.md`). The
shell only coordinates timing and initialization.

## Generated Output

From the shell declaration, the pipeline generates:

```javascript
// js/islands/shell.js
import { hydrate } from 'weblisk/core/hydrate.js';

// 1. Hydrate all islands
hydrate();

// 2. Register service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

// 3. Deferred initialization
requestIdleCallback(() => {
  // security, accessibility, performance modules
});
```

The exact implementation varies based on the declared responsibilities
and deferred modules.
