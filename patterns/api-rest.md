<!-- blueprint
type: pattern
name: api-rest
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# API REST Blueprint

Standard REST API with CRUD operations, pagination, filtering, and
sorting. Define your data models once and generate spec-compliant
endpoints automatically on any Weblisk server implementation.

## Overview

The `api-rest` blueprint generates a complete set of REST endpoints for
each model defined in the blueprint file. Every generated endpoint follows
the Weblisk protocol conventions: JSON bodies, consistent error shapes,
and deterministic URL patterns. Pagination, filtering, and sorting are
built-in — not bolted on.

## Specification

### Blueprint Format

```yaml
name: api-rest
version: 1.0.0
description: Standard REST API with CRUD operations

models:
  Task:
    fields:
      id:        uuid
      title:     string, required, max:255
      done:      boolean, default:false
      created:   timestamp, auto
      updated:   timestamp, auto

  Project:
    fields:
      id:        uuid
      name:      string, required, max:255
      owner_id:  uuid, required
      created:   timestamp, auto
```

### Generated Endpoints (per model)

For each model `M`, the following 5 endpoints MUST be generated:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/M` | List resources with pagination, filtering, sorting |
| POST | `/M` | Create a new resource |
| GET | `/M/:id` | Read a single resource by ID |
| PUT | `/M/:id` | Update (full replace) a resource by ID |
| DELETE | `/M/:id` | Delete a resource by ID |

Model names in URLs are lowercased and pluralised (e.g. `Task` → `/tasks`).

### Pagination

List endpoints MUST support cursor-based pagination:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Items per page (max 100) |
| `cursor` | string | – | Opaque cursor from previous response |

Response shape:

```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true
  }
}
```

### Filtering

List endpoints MUST support field-level filtering via query parameters:

```
GET /tasks?done=false&owner_id=abc123
```

Only fields defined in the model are valid filter keys. Unknown filter
keys MUST be ignored.

### Sorting

List endpoints MUST support sorting via the `sort` query parameter:

```
GET /tasks?sort=created:desc
GET /tasks?sort=title:asc,created:desc
```

Format: `field:direction` (comma-separated for multi-field sort).
Direction is `asc` (default) or `desc`. Only defined fields are valid
sort keys.

### Field Types

| Type | JSON Type | Description |
|------|-----------|-------------|
| `uuid` | string | UUID v4, auto-generated if `auto` |
| `string` | string | Text value |
| `boolean` | boolean | True/false |
| `integer` | number | 64-bit signed integer |
| `float` | number | 64-bit floating point |
| `timestamp` | number | Unix epoch seconds, auto-set if `auto` |

### Field Modifiers

| Modifier | Description |
|----------|-------------|
| `required` | Field MUST be present on create |
| `max:N` | String max length in characters |
| `min:N` | String min length or number min value |
| `default:V` | Default value when not provided |
| `auto` | Auto-generated (e.g. timestamps, UUIDs) |

### Request/Response Shapes

**Create (POST /tasks)**

Request:
```json
{
  "title": "Ship v1",
  "done": false
}
```

Response (201 Created):
```json
{
  "id": "a1b2c3d4-...",
  "title": "Ship v1",
  "done": false,
  "created": 1713264000,
  "updated": 1713264000
}
```

**Read (GET /tasks/:id)**

Response (200 OK): full resource object.

**Update (PUT /tasks/:id)**

Request: full resource body (partial updates are NOT supported in base
api-rest — use PATCH semantics via a custom extension if needed).

Response (200 OK): updated resource object.

**Delete (DELETE /tasks/:id)**

Response (204 No Content): empty body.

### Error Responses

All errors MUST follow this shape:

```json
{
  "error": "human-readable message",
  "code": "NOT_FOUND",
  "field": "title"
}
```

| HTTP Status | Code | When |
|-------------|------|------|
| 400 | `VALIDATION_ERROR` | Required field missing, constraint violated |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Duplicate resource (if unique constraints defined) |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

## Types

### BlueprintModel

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| fields | map[string]string | yes | Field definitions (name → type + modifiers) |

### PaginatedResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| data | []object | yes | Array of resources |
| pagination | PaginationMeta | yes | Cursor and has_more flag |

### PaginationMeta

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| next_cursor | string | no | Opaque cursor for next page |
| has_more | boolean | yes | Whether more results exist |

### ErrorResponse (API Pattern)

Error shape for generated REST API endpoints. This extends the protocol
`ErrorResponse` (see [types.md](../protocol/types.md)) with a `field`
attribute for validation errors. Implementations SHOULD include `category`
and `retryable` from the protocol type when applicable.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| error | string | yes | Human-readable message |
| code | string | yes | Machine-readable error code |
| field | string | no | Field that caused the error (validation errors) |
| category | string | no | `"permanent"` or `"transient"` (per protocol ErrorResponse) |
| retryable | boolean | no | Whether the caller SHOULD retry |

## Implementation Notes

- **ID generation**: Use UUID v4 (crypto-random). Never expose internal
  database IDs.
- **Timestamps**: Always store and return as Unix epoch seconds. Set
  `created` on insert, update `updated` on every write.
- **Cursor encoding**: Cursors SHOULD be opaque base64-encoded strings
  containing the sort key value and ID. Clients MUST NOT parse them.
- **Input validation**: Validate all field constraints before persisting.
  Return 400 with the violating field name.
- **Content-Type**: All requests and responses use `application/json`.
  Reject requests with incorrect Content-Type with 415.
- **CORS**: Implementations SHOULD include configurable CORS headers.

## Verification Checklist

- [ ] All 5 CRUD endpoints are generated for each model
- [ ] List endpoint supports `limit` and `cursor` pagination
- [ ] List endpoint supports field-level filtering
- [ ] List endpoint supports `sort` parameter with asc/desc
- [ ] Create endpoint returns 201 with the created resource
- [ ] Create validates required fields and constraints
- [ ] Read returns 404 for unknown IDs
- [ ] Update replaces the full resource (not partial)
- [ ] Delete returns 204 with empty body
- [ ] Error responses follow the standard shape
- [ ] Auto fields (uuid, timestamp) are set server-side
- [ ] Unknown filter/sort keys are handled gracefully
