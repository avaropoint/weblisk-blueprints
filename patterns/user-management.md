<!-- blueprint
type: pattern
name: user-management
version: 1.0.0
requires: [protocol/spec, protocol/types, patterns/auth-session, patterns/auth-token, architecture/gateway]
platform: any
tier: free
-->

# User Management Blueprint

Complete user lifecycle management with CRUD operations, roles,
permissions, password reset, email verification, and OAuth social
login. This pattern builds on top of the auth-session and auth-token
patterns to provide the full identity layer that applications need.

## Overview

The auth patterns (`auth-session`, `auth-token`) handle
authentication — proving who you are. This pattern handles identity
management — creating accounts, assigning roles, recovering access,
and linking external identity providers. Together, they form the
complete user system for a Weblisk application.

---

## Dependencies

```yaml
requires:
  - blueprint: protocol/spec
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: ErrorResponse
          fields_used: [code, message, detail]
        - name: PaginatedResponse
          fields_used: [data, pagination]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: protocol/types
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: TypeDefinition
          fields_used: [name, fields]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-session
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: Session
          fields_used: [user_id, expires_at, csrf_token]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: patterns/auth-token
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RefreshToken
          fields_used: [user_id, token, expires_at]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
  - blueprint: architecture/gateway
    version: ">=1.0.0 <2.0.0"
    bindings:
      types:
        - name: RouteConfig
          fields_used: [path, auth, rate_limit]
    on_change:
      compatible: validate-and-adopt
      breaking: version-bump
      removed: halt-immediately
```

---

## Design Principles

1. **Authentication is separate from identity** — Auth patterns handle proving who you are; this pattern handles creating accounts, assigning roles, and managing the user lifecycle.
2. **Never reveal existence** — Endpoints like forgot-password return the same response whether the email exists or not, preventing enumeration attacks.
3. **Least privilege by default** — New users receive the lowest-privilege role; role escalation requires explicit admin action.
4. **Soft-delete for auditability** — User records are never physically deleted; soft-delete preserves the audit trail and prevents email re-registration.

---

## Contracts

```yaml
contracts:
  behaviors:
    - name: user-lifecycle
      description: Full CRUD operations for user accounts with role-based access control
      parameters:
        - name: default_role
          type: string
          required: true
          description: Role assigned to newly created users
        - name: require_email_verification
          type: boolean
          required: true
          description: Whether new accounts must verify email before full access
      inherits: User CRUD, role management, and soft-delete behavior
      overridable: true
      override_constraints: Must preserve admin-only restrictions on DELETE and role changes
    - name: password-reset
      description: Secure password reset via time-limited single-use tokens
      parameters:
        - name: password_reset_ttl
          type: int
          required: true
          description: Token validity period in seconds
      inherits: Token generation, email delivery, and session invalidation on reset
      overridable: true
      override_constraints: Must invalidate all sessions on successful reset
    - name: oauth-social-login
      description: OAuth 2.0 authorization code flow for external identity providers
      parameters:
        - name: oauth_providers
          type: array
          required: false
          description: List of enabled OAuth providers (github, google, etc.)
      inherits: OAuth initiate/callback flow with CSRF protection
      overridable: true
      override_constraints: Must validate state parameter; must not auto-merge by email
  types:
    - name: User
      description: User record with profile, role, status, and OAuth links
      inherited_by: User Model section
    - name: OAuthLink
      description: Linked OAuth provider with provider ID and email
      inherited_by: User Model section
  endpoints:
    - path: /users
      description: List and manage user accounts
      inherited_by: Specification section
    - path: /auth/forgot-password
      description: Initiate password reset flow
      inherited_by: Password Reset section
    - path: /auth/reset-password
      description: Complete password reset with token
      inherited_by: Password Reset section
    - path: /auth/verify-email
      description: Verify email address with token
      inherited_by: Email Verification section
    - path: /auth/oauth/:provider
      description: Initiate OAuth authorization flow
      inherited_by: OAuth Social Login section
    - path: /auth/oauth/:provider/callback
      description: Handle OAuth provider callback
      inherited_by: OAuth Social Login section
```

---

## Specification

### Blueprint Format

```yaml
name: user-management
version: 1.0.0
description: User lifecycle — profiles, roles, password reset, OAuth

config:
  require_email_verification: true
  password_reset_ttl: 3600         # 1 hour
  verification_ttl: 86400          # 24 hours
  max_login_attempts: 5
  lockout_duration: 900            # 15 minutes
  default_role: user
  roles:
    - admin
    - user
    - editor
  oauth_providers:
    - github
    - google
```

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users` | admin | List users with pagination, filtering |
| GET | `/users/:id` | self or admin | Get user profile |
| PUT | `/users/:id` | self or admin | Update user profile |
| DELETE | `/users/:id` | admin | Soft-delete a user |
| PUT | `/users/:id/role` | admin | Change user role |
| POST | `/auth/forgot-password` | none | Request password reset email |
| POST | `/auth/reset-password` | none | Set new password with reset token |
| POST | `/auth/verify-email` | none | Verify email with token |
| POST | `/auth/resend-verification` | authenticated | Resend verification email |
| GET | `/auth/oauth/:provider` | none | Initiate OAuth flow |
| GET | `/auth/oauth/:provider/callback` | none | OAuth callback handler |
| POST | `/auth/oauth/:provider/link` | authenticated | Link OAuth to existing account |
| DELETE | `/auth/oauth/:provider/link` | authenticated | Unlink OAuth from account |

---

## User Model

### User Record

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| ID | string | `id` | yes | UUID, auto-generated |
| Email | string | `email` | yes | Unique, validated format |
| Name | string | `name` | yes | Display name |
| PasswordHash | string | — | yes | Never returned in API responses |
| Role | string | `role` | yes | User role (from config.roles) |
| EmailVerified | bool | `email_verified` | yes | Whether email is confirmed |
| AvatarURL | string | `avatar_url` | no | Profile image URL |
| Metadata | map | `metadata` | no | Application-specific key/value data |
| OAuthLinks | []OAuthLink | `oauth_links` | no | Linked OAuth providers |
| Status | string | `status` | yes | `active`, `suspended`, `deleted` |
| LoginAttempts | int | — | no | Failed login counter (internal) |
| LockedUntil | int64 | — | no | Lockout expiry (internal) |
| CreatedAt | int64 | `created_at` | yes | Unix epoch seconds |
| UpdatedAt | int64 | `updated_at` | yes | Unix epoch seconds |

### OAuthLink

| Field | Type | JSON Key | Required | Description |
|-------|------|----------|----------|-------------|
| Provider | string | `provider` | yes | `github`, `google`, etc. |
| ProviderID | string | `provider_id` | yes | User ID from the OAuth provider |
| Email | string | `email` | no | Email from OAuth (may differ from primary) |
| LinkedAt | int64 | `linked_at` | yes | Unix epoch seconds |

---

## User CRUD

### List Users (GET /users)

Admin only. Returns paginated user list.

**Query parameters:**
- `limit` — Items per page (default: 20, max: 100)
- `cursor` — Pagination cursor
- `role` — Filter by role
- `status` — Filter by status (`active`, `suspended`, `deleted`)
- `search` — Search by name or email (prefix match)
- `sort` — `created_at:desc` (default), `name:asc`, `email:asc`

**Response:**
```json
{
  "data": [
    {
      "id": "a1b2c3d4...",
      "email": "alice@example.com",
      "name": "Alice",
      "role": "admin",
      "email_verified": true,
      "status": "active",
      "created_at": 1712160000,
      "updated_at": 1712160000
    }
  ],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true
  }
}
```

Passwords, login attempts, and lockout fields are NEVER returned.

### Get User (GET /users/:id)

Authenticated users can view their own profile. Admins can view any
user. Non-admin viewing another user → 403.

**Response:** Single user object (same shape as list item, plus
`metadata`, `oauth_links`, `avatar_url`).

### Update User (PUT /users/:id)

Users can update their own name, avatar, and metadata. Admins can
update any user's fields except password (use reset flow).

**Request:**
```json
{
  "name": "Alice Smith",
  "avatar_url": "https://example.com/avatar.jpg",
  "metadata": {"company": "Acme Corp"}
}
```

**Rules:**
- `email` changes require re-verification (send verification email)
- `role` changes MUST use the dedicated `/users/:id/role` endpoint
- `password` changes MUST use the reset flow or a dedicated
  change-password endpoint

### Delete User (DELETE /users/:id)

Admin only. Soft-delete — sets `status` to `"deleted"`. The user
record is retained for audit purposes but the account cannot
authenticate.

**Response:** 204 No Content

### Change Role (PUT /users/:id/role)

Admin only.

**Request:**
```json
{
  "role": "editor"
}
```

**Rules:**
- Role MUST be in the configured roles list
- Admin cannot demote themselves (prevents lockout)
- Role change is logged in the audit trail

---

## Password Reset

### Request Reset (POST /auth/forgot-password)

```json
{
  "email": "alice@example.com"
}
```

**Process:**
```
1. Look up user by email
2. If not found → return 200 OK anyway (prevent email enumeration)
3. Generate 32-byte random token → hex encode
4. Store reset token with expiry (config.password_reset_ttl)
5. Send password reset email via email agent:
   Subject: "Password Reset"
   Body: link to /auth/reset-password?token=<token>
6. Return 200 OK: {"message": "If that email exists, a reset link has been sent"}
```

**Security:**
- MUST NOT reveal whether the email exists
- Token is single-use — consumed on successful reset
- Token expires after TTL (default: 1 hour)
- Only the most recent token is valid (previous tokens invalidated)
- Rate limit: 3 requests per email per hour

### Complete Reset (POST /auth/reset-password)

```json
{
  "token": "a1b2c3d4...",
  "password": "newsecurepassword"
}
```

**Process:**
```
1. Look up reset token
2. If not found or expired → 400 "Invalid or expired reset token"
3. Validate new password (minimum length, not same as email)
4. Hash new password with bcrypt (cost ≥ 12) or argon2id
5. Update user record
6. Delete reset token
7. Invalidate all existing sessions/refresh tokens for this user
8. Return 200 OK
```

---

## Email Verification

### Initial Verification

When `config.require_email_verification` is `true`:

```
1. User registers via POST /auth/register
2. Account created with email_verified = false
3. Generate 32-byte random verification token
4. Store token with expiry (config.verification_ttl)
5. Send verification email via email agent:
   Subject: "Verify your email"
   Body: link to /auth/verify-email?token=<token>
6. User can authenticate but SHOULD see a banner prompting verification
```

### Verify (POST /auth/verify-email)

```json
{
  "token": "a1b2c3d4..."
}
```

**Process:**
```
1. Look up verification token
2. If not found or expired → 400 "Invalid or expired verification token"
3. Set user.email_verified = true
4. Delete verification token
5. Return 200 OK: {"verified": true}
```

### Resend (POST /auth/resend-verification)

Requires authentication. Generates a new token and sends a new email.
Rate limit: 1 request per 5 minutes.

---

## OAuth Social Login

### Supported Providers

| Provider | Auth URL | Token URL | User Info URL |
|----------|----------|-----------|---------------|
| GitHub | `https://github.com/login/oauth/authorize` | `https://github.com/login/oauth/access_token` | `https://api.github.com/user` |
| Google | `https://accounts.google.com/o/oauth2/v2/auth` | `https://oauth2.googleapis.com/token` | `https://www.googleapis.com/oauth2/v2/userinfo` |

Providers are configured via environment variables:
- `WL_OAUTH_GITHUB_CLIENT_ID`, `WL_OAUTH_GITHUB_CLIENT_SECRET`
- `WL_OAUTH_GOOGLE_CLIENT_ID`, `WL_OAUTH_GOOGLE_CLIENT_SECRET`

### OAuth Flow

#### Initiate (GET /auth/oauth/:provider)

```
1. Validate provider is configured
2. Generate 32-byte random state parameter
3. Store state in server-side session (or signed cookie) with 10-minute TTL
4. Redirect to provider's authorization URL:
   ?client_id=<id>
   &redirect_uri=<callback_url>
   &scope=<provider_scopes>
   &state=<state>
   &response_type=code
```

#### Callback (GET /auth/oauth/:provider/callback)

```
1. Validate state parameter matches stored state (CSRF protection)
2. Exchange authorization code for access token:
   POST to provider's token URL
3. Use access token to fetch user profile from provider
4. Look up OAuthLink by provider + provider_id:

   If found → existing user:
     a. Load user record
     b. Create session/token (same as login)
     c. Return or redirect to app

   If not found → new user:
     a. Check if email from OAuth matches existing user
     b. If email match → prompt to link account (don't auto-merge)
     c. If no match → create new user:
        - name from OAuth profile
        - email from OAuth (marked as verified if provider verified it)
        - random password (user can set via reset flow)
        - role = config.default_role
        - oauth_links = [{provider, provider_id}]
     d. Create session/token
     e. Return or redirect to app
```

**Security:**
- MUST validate state parameter (CSRF protection)
- MUST use HTTPS for callback URLs in production
- MUST NOT auto-merge accounts by email — require explicit linking
- Access tokens from OAuth providers are used once and discarded
  (not stored)

#### Link Account (POST /auth/oauth/:provider/link)

Authenticated user links an OAuth provider to their existing account.
Initiates the same OAuth flow but on callback, adds an OAuthLink to
the current user rather than creating a new account.

#### Unlink Account (DELETE /auth/oauth/:provider/link)

Remove an OAuth link. User MUST have either a password or at least
one remaining OAuth link (cannot remove all auth methods).

---

## Account Security

### Login Attempt Tracking

```
On failed login:
  1. Increment user.login_attempts
  2. If login_attempts >= config.max_login_attempts:
     a. Set user.locked_until = now + config.lockout_duration
     b. Log: "Account locked due to repeated failed attempts"
  3. Return 401 with generic message

On successful login:
  1. Reset user.login_attempts to 0
  2. Clear user.locked_until

On login attempt for locked account:
  1. If now < user.locked_until → 429 "Account temporarily locked"
  2. If lockout expired → allow attempt (reset counter)
```

### Password Requirements

- Minimum length: `config.password_min_length` (default: 8)
- MUST NOT be identical to the user's email
- SHOULD be checked against a list of common passwords (top 10,000)
- Passwords MUST be hashed with bcrypt (cost ≥ 12) or argon2id
- Passwords MUST NOT be logged, cached, or stored in plaintext

---

## Roles and Permissions

### Role-Based Access Control

Roles are simple string labels. Permission checking is done at the
endpoint level:

```
Endpoint defines: minimum_role
Request has: user.role
Check: role_hierarchy[user.role] >= role_hierarchy[minimum_role]
```

### Default Role Hierarchy

```
admin (3) > editor (2) > user (1)
```

Applications MAY define custom roles and hierarchy via configuration.

### Permission Checks by Endpoint

| Endpoint | Minimum Role | Additional Rules |
|----------|-------------|------------------|
| `GET /users` | admin | — |
| `GET /users/:id` | user | Self or admin |
| `PUT /users/:id` | user | Self (limited fields) or admin (all fields) |
| `DELETE /users/:id` | admin | Cannot delete self |
| `PUT /users/:id/role` | admin | Cannot demote self |
| `POST /auth/forgot-password` | none | Rate limited |
| `POST /auth/reset-password` | none | Valid token required |
| `POST /auth/verify-email` | none | Valid token required |
| `GET /auth/oauth/:provider` | none | — |

---

## User Storage

### Store: Users

| Operation | Signature | Description |
|-----------|-----------|-------------|
| CreateUser | `(user User) → error` | Create new user |
| GetUser | `(id string) → (User, error)` | Get by ID |
| GetUserByEmail | `(email string) → (User, error)` | Get by email |
| UpdateUser | `(id string, fields map) → error` | Partial update |
| ListUsers | `(filter UserFilter) → ([]User, error)` | Paginated list |
| DeleteUser | `(id string) → error` | Soft delete |

### Store: Reset Tokens

| Operation | Signature | Description |
|-----------|-----------|-------------|
| StoreResetToken | `(email string, token string, expiry int64) → error` | Store reset token |
| ConsumeResetToken | `(token string) → (email string, error)` | Retrieve and delete |

### Store: Verification Tokens

| Operation | Signature | Description |
|-----------|-----------|-------------|
| StoreVerificationToken | `(email string, token string, expiry int64) → error` | Store verification token |
| ConsumeVerificationToken | `(token string) → (email string, error)` | Retrieve and delete |

### Store: OAuth Links

| Operation | Signature | Description |
|-----------|-----------|-------------|
| LinkOAuth | `(userID string, link OAuthLink) → error` | Add OAuth link |
| UnlinkOAuth | `(userID string, provider string) → error` | Remove OAuth link |
| GetByOAuth | `(provider string, providerID string) → (User, error)` | Look up by OAuth |

---

## Implementation Notes

- Password reset and verification tokens MUST be generated with
  `crypto/rand` (not `math/rand`)
- All token lookups MUST be constant-time to prevent timing attacks
- Email sending is delegated to the email-send infrastructure agent —
  the user management pattern does not send email directly
- OAuth state parameters MUST be server-side (not solely in cookies)
  to prevent CSRF in the OAuth flow
- Soft-deleted users retain their email in the database to prevent
  re-registration with the same email (unless explicitly purged)
- User search (`?search=`) MUST use prefix matching only (not
  substring) to avoid full-table scans

## Verification Checklist

- [ ] GET /users is admin-only and returns paginated results with `cursor`, `limit` (max 100), `role`, `status`, `search`, and `sort` query params
- [ ] PasswordHash, LoginAttempts, and LockedUntil are never returned in any API response
- [ ] DELETE /users/:id performs soft-delete (sets status to `deleted`); admin cannot delete self
- [ ] PUT /users/:id/role validates role against configured roles list and prevents admin from demoting themselves
- [ ] POST /auth/forgot-password returns 200 OK regardless of whether the email exists (prevents email enumeration)
- [ ] Password reset tokens are single-use, expire after configured TTL, and only the most recent token per email is valid
- [ ] Successful password reset invalidates all existing sessions and refresh tokens for the user
- [ ] Passwords are hashed with bcrypt (cost ≥ 12) or argon2id and are never logged, cached, or stored in plaintext
- [ ] Login lockout activates after `max_login_attempts` consecutive failures; locked account returns 429 until `lockout_duration` expires
- [ ] OAuth callback validates the `state` parameter server-side for CSRF protection and does not auto-merge accounts by email
- [ ] Unlinking an OAuth provider is rejected if the user has no password and no remaining OAuth links
- [ ] Email changes require re-verification; resend-verification is rate-limited to 1 request per 5 minutes
- [ ] User search (`?search=`) uses prefix matching only — not substring — to avoid full-table scans
- [ ] All tokens (reset, verification, OAuth state) are generated with `crypto/rand`, and token lookups use constant-time comparison
