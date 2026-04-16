<!-- blueprint
type: pattern
name: auth-token
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Auth Token Blueprint

JWT and API key authentication with refresh tokens and scoped
permissions. Define your auth requirements once and generate a
complete token-based auth system on any Weblisk server implementation.

## Overview

The `auth-token` blueprint provides stateless authentication using
JWTs for short-lived access and opaque refresh tokens for session
continuity. API keys are also supported for service-to-service
communication. Permissions are scoped — each token declares exactly
what it can access.

## Specification

### Blueprint Format

```yaml
name: auth-token
version: 1.0.0
description: JWT and API key authentication

config:
  access_token_duration: 900     # 15 minutes
  refresh_token_duration: 604800 # 7 days
  issuer: weblisk
  scopes:
    - read
    - write
    - admin
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/token` | Exchange credentials for token pair |
| POST | `/auth/refresh` | Exchange refresh token for new access token |
| DELETE | `/auth/token` | Revoke refresh token |
| POST | `/auth/apikey` | Create an API key with scoped permissions |

### Token Exchange (POST /auth/token)

Request:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "scopes": ["read", "write"]
}
```

Response (200 OK):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "opaque-random-token",
  "token_type": "Bearer",
  "expires_in": 900,
  "scopes": ["read", "write"]
}
```

- `access_token`: JWT signed with server secret (HS256) or key pair (ES256)
- `refresh_token`: Opaque random string stored server-side
- Requested scopes MUST be a subset of the user's allowed scopes

### JWT Claims

```json
{
  "sub": "user-id",
  "iss": "weblisk",
  "iat": 1713264000,
  "exp": 1713264900,
  "scopes": ["read", "write"]
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User ID |
| `iss` | Issuer (from config) |
| `iat` | Issued-at timestamp |
| `exp` | Expiration timestamp |
| `scopes` | Granted permission scopes |

### Token Refresh (POST /auth/refresh)

Request:
```json
{
  "refresh_token": "opaque-random-token"
}
```

Response (200 OK): same shape as token exchange (new access + refresh token pair).

The old refresh token MUST be invalidated (rotation). This prevents
replay attacks if a refresh token is compromised.

### Token Revocation (DELETE /auth/token)

Request:
```json
{
  "refresh_token": "opaque-random-token"
}
```

Response: 204 No Content.

Revokes the refresh token. The associated access token remains valid
until it expires (stateless JWTs cannot be revoked without a blocklist).

### API Keys (POST /auth/apikey)

Requires valid access token with `admin` scope.

Request:
```json
{
  "name": "CI Pipeline",
  "scopes": ["read"],
  "expires_in": 2592000
}
```

Response (201 Created):
```json
{
  "key": "wl_key_a1b2c3d4...",
  "name": "CI Pipeline",
  "scopes": ["read"],
  "expires_at": 1715856000,
  "created": 1713264000
}
```

The full key is returned ONLY on creation. Subsequent lookups show
only a prefix. API keys are transmitted via the `Authorization` header
using the `Bearer` scheme, same as JWTs.

### Authentication Flow

For protected endpoints:

```
1. Extract Authorization header: "Bearer <token>"
2. If token starts with "wl_key_" → API key path:
   a. Look up API key in store
   b. Validate not expired and not revoked
   c. Check scopes against endpoint requirements
3. Else → JWT path:
   a. Verify JWT signature
   b. Check exp claim (reject if expired)
   c. Check iss claim matches config
   d. Check scopes against endpoint requirements
4. If valid → attach user context to request
5. If invalid → 401 Unauthorized
```

### Scope Enforcement

Endpoints declare required scopes. The token's scopes MUST be a
superset of the required scopes.

```
GET /tasks       → requires: [read]
POST /tasks      → requires: [write]
DELETE /tasks/:id → requires: [write]
POST /auth/apikey → requires: [admin]
```

Insufficient scopes → 403 Forbidden (not 401).

## Types

### TokenPair

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| access_token | string | yes | Signed JWT |
| refresh_token | string | yes | Opaque refresh token |
| token_type | string | yes | Always "Bearer" |
| expires_in | int | yes | Access token lifetime in seconds |
| scopes | []string | yes | Granted scopes |

### RefreshToken (server-side)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| token_hash | string | yes | SHA-256 hash of the token |
| user_id | string | yes | Associated user ID |
| scopes | []string | yes | Granted scopes |
| created_at | int64 | yes | Creation timestamp |
| expires_at | int64 | yes | Expiration timestamp |
| revoked | boolean | yes | Whether token has been revoked |

### APIKey (server-side)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| key_hash | string | yes | SHA-256 hash of the full key |
| key_prefix | string | yes | First 8 chars for display |
| name | string | yes | Human-readable label |
| user_id | string | yes | Owner user ID |
| scopes | []string | yes | Granted scopes |
| created_at | int64 | yes | Creation timestamp |
| expires_at | int64 | yes | Expiration timestamp |
| revoked | boolean | yes | Whether key has been revoked |

## Implementation Notes

- **JWT signing**: Use HS256 (shared secret) for single-server
  deployments and ES256 (ECDSA P-256) for distributed systems where
  services verify but don't issue tokens.
- **Refresh token storage**: Store only the SHA-256 hash. Never store
  the raw token. Compare by hashing the presented token.
- **API key storage**: Same as refresh tokens — store the hash, return
  the raw key only once on creation.
- **Token rotation**: On refresh, always issue a NEW refresh token and
  invalidate the old one. This limits the window for stolen tokens.
- **Clock skew**: Allow up to 30 seconds of clock skew when validating
  JWT expiration.
- **Scope validation**: Check scopes on every request. Never trust
  scopes from the client — derive them from the token.
- **Rate limiting**: Rate-limit the token endpoint (e.g. 10 requests
  per minute per IP) to mitigate credential stuffing.

## Verification Checklist

- [ ] Token endpoint returns JWT + refresh token on valid credentials
- [ ] JWT contains correct sub, iss, iat, exp, scopes claims
- [ ] JWT signature is verified on every protected request
- [ ] Expired JWTs are rejected
- [ ] Refresh endpoint issues new token pair and invalidates the old refresh token
- [ ] Revoked refresh tokens cannot be used
- [ ] API keys authenticate via the same Authorization header
- [ ] Scope enforcement returns 403 for insufficient permissions
- [ ] Refresh tokens are stored as hashes, not plaintext
- [ ] API keys are returned in full only on creation
- [ ] Token endpoint is rate-limited
