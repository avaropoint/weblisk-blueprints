<!-- blueprint
type: pattern
name: auth-session
version: 1.0.0
requires: [protocol/spec, protocol/types, protocol/identity, architecture/gateway, architecture/browser-session]
platform: any
tier: free
-->

# Auth Session Blueprint

Session-based authentication with secure cookies, CSRF protection,
and logout. Define your user model and get a complete session auth
system on any Weblisk server implementation.

## Overview

The `auth-session` blueprint generates a server-side session
authentication system. Users authenticate with credentials, receive
a secure HTTP-only cookie, and subsequent requests are authenticated
via that cookie. CSRF protection is included by default for all
state-changing operations.

## Specification

### Blueprint Format

```yaml
name: auth-session
version: 1.0.0
description: Session-based authentication with secure cookies

config:
  session_duration: 86400       # 24 hours in seconds
  cookie_name: wl_session
  csrf_header: X-CSRF-Token
  max_sessions_per_user: 5
  password_min_length: 8
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Authenticate and create session |
| POST | `/auth/logout` | Destroy current session |
| GET | `/auth/me` | Get current authenticated user |

### Registration (POST /auth/register)

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "Alice"
}
```

Response (201 Created):
```json
{
  "id": "a1b2c3d4...",
  "email": "user@example.com",
  "name": "Alice",
  "created": 1713264000
}
```

Validation:
- `email` MUST be a valid email format and unique
- `password` MUST meet minimum length (default 8)
- Passwords MUST be hashed with bcrypt (cost ≥ 12) or argon2id

### Login (POST /auth/login)

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

Response (200 OK):
```json
{
  "user": {
    "id": "a1b2c3d4...",
    "email": "user@example.com",
    "name": "Alice"
  },
  "csrf_token": "random-csrf-token"
}
```

On success:
1. Create a new session record server-side
2. Set `Set-Cookie` header with session ID:
   - `HttpOnly` — not accessible via JavaScript
   - `Secure` — sent only over HTTPS
   - `SameSite=Lax` — CSRF protection for top-level navigations
   - `Path=/`
   - `Max-Age` per config

On failure (invalid credentials): return 401 with generic message.
MUST NOT reveal whether the email exists.

### Logout (POST /auth/logout)

Requires valid session cookie.

1. Delete the session record server-side
2. Clear the session cookie
3. Return 204 No Content

### Get Current User (GET /auth/me)

Requires valid session cookie.

Response (200 OK):
```json
{
  "id": "a1b2c3d4...",
  "email": "user@example.com",
  "name": "Alice",
  "created": 1713264000
}
```

Returns 401 if no valid session.

### CSRF Protection

All state-changing endpoints (POST, PUT, DELETE) MUST require a valid
CSRF token in addition to the session cookie.

Flow:
1. On login, server generates a CSRF token and returns it in the
   response body
2. Client stores the token and includes it in the configured header
   (default `X-CSRF-Token`) on all state-changing requests
3. Server validates the CSRF token matches the session's stored token
4. Invalid or missing CSRF token → 403 Forbidden

CSRF validation applies to all endpoints except `/auth/login` and
`/auth/register`.

### Session Storage

Sessions are stored server-side. Each session record contains:

| Field | Description |
|-------|-------------|
| session_id | Random 32-byte hex string |
| user_id | Associated user ID |
| csrf_token | Random 32-byte hex string |
| created_at | Unix timestamp |
| expires_at | Unix timestamp |
| ip_address | Client IP at creation |
| user_agent | Client User-Agent at creation |

When `max_sessions_per_user` is exceeded, the oldest session MUST be
evicted.

### Password Storage

Passwords MUST be hashed before storage. Acceptable algorithms:
- **bcrypt** with cost ≥ 12
- **argon2id** with recommended parameters

Plaintext passwords MUST NEVER be stored or logged.

## Types

### User

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique user ID (UUID) |
| email | string | yes | User's email address |
| name | string | yes | Display name |
| password_hash | string | yes | Hashed password (never returned in API) |
| created | int64 | yes | Account creation timestamp |

### Session

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_id | string | yes | Random session identifier |
| user_id | string | yes | Associated user ID |
| csrf_token | string | yes | CSRF protection token |
| created_at | int64 | yes | Creation timestamp |
| expires_at | int64 | yes | Expiration timestamp |
| ip_address | string | no | Client IP at creation |
| user_agent | string | no | Client User-Agent at creation |

### AuthConfig

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| session_duration | int | yes | Session lifetime in seconds |
| cookie_name | string | yes | Session cookie name |
| csrf_header | string | yes | CSRF token header name |
| max_sessions_per_user | int | yes | Max concurrent sessions |
| password_min_length | int | yes | Minimum password length |

## Implementation Notes

- **Timing attacks**: Use constant-time comparison for session IDs
  and CSRF tokens.
- **Session ID entropy**: Use crypto-random 32 bytes (256 bits). Never
  use sequential or predictable IDs.
- **Cookie flags**: Always set HttpOnly, Secure (in production),
  SameSite=Lax. Never expose session IDs to JavaScript.
- **Login throttling**: Implementations SHOULD rate-limit login attempts
  per IP (e.g. 10 attempts per minute) to mitigate brute force.
- **Error messages**: Authentication failures MUST return generic
  messages (e.g. "invalid credentials"). Never reveal whether an email
  is registered.
- **Session cleanup**: Implementations SHOULD periodically purge
  expired sessions from storage.

## Verification Checklist

- [ ] Registration creates user with hashed password
- [ ] Registration rejects duplicate emails
- [ ] Login sets HttpOnly, Secure, SameSite=Lax cookie
- [ ] Login returns CSRF token in response body
- [ ] Logout destroys session and clears cookie
- [ ] GET /auth/me returns user for valid session, 401 otherwise
- [ ] CSRF token is required on all state-changing endpoints
- [ ] Invalid CSRF token returns 403
- [ ] Expired sessions are rejected
- [ ] Passwords are never returned in any API response
- [ ] Failed login does not reveal whether email exists
- [ ] Session IDs use crypto-random 256-bit values
