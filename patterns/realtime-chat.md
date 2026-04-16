<!-- blueprint
type: pattern
name: realtime-chat
version: 1.0.0
requires: [protocol/spec, protocol/types]
platform: any
tier: free
-->

# Realtime Chat Blueprint

WebSocket-based real-time messaging with channels, presence tracking,
and message history. Define channels once and generate a complete
messaging backend on any Weblisk server implementation.

## Overview

The `realtime-chat` blueprint provides a real-time messaging system
built on WebSockets. It supports named channels, presence awareness
(who is online), and persistent message history. The HTTP endpoints
handle channel management and history retrieval, while the WebSocket
connection handles live messaging and presence.

## Specification

### Blueprint Format

```yaml
name: realtime-chat
version: 1.0.0
description: WebSocket-based real-time messaging channels

channels:
  general:
    description: Default public channel
    max_members: 1000
    history_limit: 500
    auth: none

  team:
    description: Authenticated team channel
    max_members: 100
    history_limit: 1000
    auth: token
```

### HTTP Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/channels` | List available channels |
| GET | `/channels/:name` | Get channel details and presence |
| GET | `/channels/:name/history` | Retrieve message history |
| POST | `/channels/:name/send` | Send a message (HTTP fallback) |

### WebSocket Endpoint

```
WS /ws?channel=general&token=...
```

The WebSocket connection is the primary interface for real-time
messaging. After connection, the server sends a `connected` frame
and the client can send and receive messages.

### WebSocket Frame Types

All frames are JSON objects with a `type` field:

**Client → Server:**

| Type | Fields | Description |
|------|--------|-------------|
| `message` | `content`, `metadata` | Send a message to the channel |
| `typing` | – | Indicate the user is typing |
| `ping` | – | Keep-alive ping |

**Server → Client:**

| Type | Fields | Description |
|------|--------|-------------|
| `connected` | `channel`, `members`, `history` | Initial connection payload |
| `message` | `id`, `from`, `content`, `timestamp`, `metadata` | New message |
| `typing` | `from` | Another user is typing |
| `presence` | `user`, `status` | User joined or left |
| `pong` | – | Keep-alive response |
| `error` | `message` | Error notification |

### Message Format

```json
{
  "id": "a1b2c3d4e5f6...",
  "channel": "general",
  "from": "user-id-or-name",
  "content": "Hello, world!",
  "timestamp": 1713264000,
  "metadata": {}
}
```

### Presence

The server MUST track which users are connected to each channel.
Presence updates are broadcast to all channel members when a user
joins or leaves.

```json
{
  "type": "presence",
  "user": "alice",
  "status": "joined"
}
```

Presence list is returned in the `connected` frame and via
`GET /channels/:name`.

### History

Message history is stored server-side and retrievable via HTTP:

```
GET /channels/general/history?limit=50&before=cursor123
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 50 | Messages to return (max 100) |
| `before` | string | – | Cursor for older messages |

Response:

```json
{
  "messages": [...],
  "pagination": {
    "next_cursor": "abc123",
    "has_more": true
  }
}
```

### Channel Auth Modes

| Mode | Description |
|------|-------------|
| `none` | Public — anyone can connect |
| `token` | Requires valid auth token (from auth-session or auth-token blueprint) |

### Connection Lifecycle

```
1. Client opens WebSocket to /ws?channel=general&token=...
2. Server validates channel exists and auth (if required)
3. Server adds user to channel presence
4. Server sends "connected" frame with members list and recent history
5. Server broadcasts "presence" (joined) to other members
6. Client sends "message" frames, server broadcasts to all members
7. On disconnect: server removes from presence, broadcasts "presence" (left)
```

### Rate Limiting

Implementations SHOULD enforce per-connection rate limits:

- Messages: 10 per second per connection
- Typing indicators: 1 per 3 seconds per connection

Exceeding limits SHOULD result in an `error` frame, not disconnection.

## Types

### Channel

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | yes | Channel identifier |
| description | string | no | Human-readable description |
| max_members | int | yes | Maximum concurrent connections |
| history_limit | int | yes | Max stored messages |
| auth | string | yes | Auth mode: `none` or `token` |
| members | []string | no | Currently connected user IDs |

### ChatMessage

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | yes | Unique message ID (hex) |
| channel | string | yes | Channel name |
| from | string | yes | Sender identifier |
| content | string | yes | Message body |
| timestamp | int64 | yes | Unix epoch seconds |
| metadata | object | no | Arbitrary key-value data |

### WebSocketFrame

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | Frame type identifier |
| (varies) | – | – | Additional fields per frame type |

## Implementation Notes

- **WebSocket library**: Use the platform's native WebSocket support
  (e.g. `gorilla/websocket` for Go, native WebSocket API for Cloudflare).
- **Presence storage**: In-memory for single-instance deployments.
  For multi-instance, use a shared store (e.g. KV, Redis).
- **Message persistence**: Store messages in the server's configured
  data store. Respect `history_limit` — evict oldest when exceeded.
- **Heartbeat**: Implementations SHOULD send ping frames every 30
  seconds and close connections that miss 2 consecutive pongs.
- **Content sanitization**: Message content MUST be treated as
  untrusted. Implementations MUST NOT execute or render HTML from
  message content.
- **Max message size**: Reject WebSocket frames larger than 64 KB.

## Verification Checklist

- [ ] WebSocket endpoint accepts connections with channel parameter
- [ ] Connected frame includes member list and recent history
- [ ] Messages are broadcast to all channel members
- [ ] Presence join/leave events are broadcast correctly
- [ ] History endpoint returns paginated messages
- [ ] Channel auth modes (none, token) are enforced
- [ ] Rate limiting prevents message flooding
- [ ] Disconnected clients are cleaned up from presence
- [ ] Messages are persisted up to history_limit
- [ ] Invalid frames return error frames (not disconnection)
