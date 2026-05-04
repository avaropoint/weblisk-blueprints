# Standard Schema

Schema governing project-level blueprint standards — the documents in
`standards/` that define how developers structure their YAML blueprints
(pages, components, islands, connections, assets, theme, code, global).

Standards are distinct from framework schemas: schemas enforce compliance
for framework-internal blueprints (agents, protocol, patterns); standards
provide guidance and structure for developer-authored project blueprints.

---

## Scope

This schema governs the `standards/` directory. It does NOT govern the
project-level YAML files themselves — those are validated against the
standard they declare (`extends: standards/pages`, etc.). This schema
governs the standard definitions.

---

## Type Registry

Standards define project-level blueprint types. Each standard declares
what fields are available, what structure is expected, and what
conventions apply to a given type.

| Standard | Type | Governs |
|----------|------|---------|
| `pages.md` | page | Route declarations, sections, SEO, styles |
| `components.md` | component | Reusable UI: props, slots, variants, accessibility, styles |
| `islands.md` | island | Interactive regions: agent binding, protocol, state |
| `global.md` | global | Project identity, brand, policies |
| `theme.md` | theme | Design tokens, scales, breakpoints |
| `code.md` | code | Code generation conventions |
| `assets.md` | assets | Static files, generated media |
| `connections.md` | connection | External integrations, protocols |
| `project-structure.md` | — | Directory layout conventions (not a type) |

---

## Required Structure

Every standard document MUST include these sections in order:

### 1. Title

Level-1 heading. Names the standard.

```markdown
# Page Blueprints
```

### 2. Summary

Blockquote immediately after the title. One sentence describing what
this standard covers.

```markdown
> Describing routes, layouts, sections, SEO, and structured data.
```

### 3. Purpose

`## Purpose` section. 2–5 sentences explaining what this standard
governs and why it exists.

### 4. Structure

`## Structure` section. Contains a complete YAML example showing
the standard's fields in context. This is the template developers
start from.

### 5. Fields

`## Fields` section. Documents every field using tables with at
minimum: Field, Type, Required, Description.

Field documentation MUST cover:
- Top-level metadata fields (type, name, route, etc.)
- Nested structural fields (sections, props, slots, etc.)
- Optional fields with their defaults

### 6. Type-Specific Sections

Additional `##` sections as needed for the standard. Examples:
- `## Styles` (pages, components)
- `## Variants` (components)
- `## Composition` (components)
- `## Dynamic Routes` (pages)
- `## Protocol Details` (islands)

### 7. Conventions (optional)

`## Conventions` section with principles or best practices.

---

## Field Documentation Format

Field tables MUST use this column structure:

```markdown
| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
```

For nested fields, use sub-headings:

```markdown
### Props
| Field | Type | Description |
|-------|------|-------------|
```

---

## Styles Field

Standards that govern visual blueprint types (pages, components) MUST
document the `styles:` field. The styles field allows project blueprints
to declare visual properties inline, co-located with the structure they
describe.

### Page Styles

Pages support styles at two levels:

1. **Page-level** — Top-level `styles:` key for page-wide properties
2. **Section-level** — `styles:` key within each section for
   section-specific layout and visual treatment

```yaml
type: page
styles:
  max_width: 1200px

sections:
  - id: hero
    type: hero
    styles:
      padding: var(--space-8)
      text_align: center
```

### Component Styles

Components support a top-level `styles:` key for structural properties
that don't change by variant:

```yaml
type: component
name: sidebar

styles:
  width: 280px
  padding: var(--space-4)
  responsive:
    md: { width: 240px }
```

### Style Principles

Standards documenting styles MUST state these principles:

1. Theme tokens first — reference `var(--token)` from theme.yaml
2. Minimal overrides — only structure, layout, and unique elements
3. Co-located — styles live in the same file as the thing they describe
4. Single output — pipeline collects all styles into one generated CSS

---

## Extends Field

Project blueprints reference standards via the `extends:` field:

```yaml
type: page
extends: standards/pages
```

This tells the generation pipeline and validators which standard
governs the blueprint. The standard defines what fields are valid,
what sections are expected, and what conventions apply.

### Validation

When a project blueprint declares `extends: standards/<name>`:
1. The standard must exist in the repository
2. Required fields from the standard must be present
3. Field types must match the standard's declarations
4. Unknown fields are allowed (standards are guidance, not enforcement)

---

## Versioning

Standards follow semver in documentation but are not versioned in
frontmatter (they are markdown guidance documents, not machine-parsed
blueprints). Version tracking is by git history.

Changes to standards:
- **Additive** (new optional fields, new sections): backward compatible
- **Restrictive** (required fields, removed fields): breaking — requires
  coordination with existing projects
- **Clarification** (rewording, examples): no version impact

---

## Validation Rules

1. Every standard MUST have: title, summary blockquote, Purpose, Structure, Fields
2. Structure example MUST be valid YAML
3. Field tables MUST document type and description for every field
4. Standards governing visual types MUST document the `styles:` field
5. Standards MUST NOT prescribe implementation technology (frameworks,
   languages, libraries) — only structure and semantics
6. Standards MUST NOT duplicate schema-level governance (no capability
   declarations, no security boundaries, no compliance levels)
