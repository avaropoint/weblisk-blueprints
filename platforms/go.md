<!-- blueprint
type: platform
name: go
version: 1.0.0
requires: [protocol/spec, protocol/identity, protocol/types, architecture/agent, architecture/orchestrator]
platform: go
-->

# Platform: Go Implementation

Guidance for generating Weblisk orchestrator and agent implementations
in Go, running as local processes. This is the default platform for
local development.

## Project Structure

### Orchestrator
```
server/
  go.mod              # module server; go 1.22
  main.go             # Entry point — configure and start orchestrator
  protocol.go         # All protocol types (AgentManifest, TaskRequest, etc.)
  identity.go         # Ed25519 key management, signing, tokens
  orchestrator.go     # HTTP server with registration, routing, channels, audit
  helpers.go          # JSON helpers, utility functions
```

Build: `cd server && go build -o orchestrator .`
Run: `./orchestrator --port 9800`

### Agent
```
agents/<name>/
  go.mod              # module weblisk-agent-<name>; go 1.22
  main.go             # Entry point — configure manifest, create agent, start
  protocol.go         # Same protocol types as orchestrator (shared contract)
  identity.go         # Same identity/crypto code
  agent.go            # Agent base framework (HTTP server, registration, messaging)
  <name>.go           # Domain-specific logic (Execute + HandleMessage)
  helpers.go          # Shared utility functions
```

Build: `cd agents/<name> && go build -o <name> .`
Run: `./agents/seo --port 9710 --orch http://localhost:9800`

## Go-Specific Requirements

### Dependencies
- Zero external dependencies. Use only Go standard library.
- `crypto/ed25519` for key generation and signing
- `crypto/rand` for secure random generation  
- `encoding/json` for JSON serialization
- `encoding/hex` for hex encoding
- `encoding/base64` for base64url encoding in tokens
- `net/http` for HTTP server and client
- `sync` for thread-safe concurrent access (RWMutex)
- `time` for timestamps and durations
- `io` for reading request bodies (with LimitReader for safety)
- `os` for environment variables and file I/O
- `path/filepath` for path operations
- `fmt` for formatting and printing

### Concurrency
- All registries (agents, channels) protected by `sync.RWMutex`
- Use `RLock` for reads, `Lock` for writes
- Service broadcasts are fire-and-forget goroutines
- HTTP handlers are inherently concurrent (net/http serves each in a goroutine)

### IO Safety
- Use `io.LimitReader` on all request body reads
  - Registration: 1 MB limit (`1 << 20`)
  - Task execution: 10 MB limit (`10 << 20`)
  - Messages: 1 MB limit
  - Channel requests: 64 KB limit (`1 << 16`)
  - Service updates: 1 MB limit

### Package Organization
- All files in a single Go package (`package main` for standalone binaries)
- Shared code (protocol.go, identity.go, helpers.go) is identical between
  orchestrator and agents — copy, don't import (keeps each binary standalone)

### Error Handling
- Return errors from functions, don't panic
- HTTP handlers write error JSON responses, don't crash
- Registration failures are fatal (agent can't operate without orchestrator)
- Service broadcast failures are logged and ignored

### Configuration
- Use environment variables (WL_AI_*, WL_ORCH_*) via os.Getenv
- Support command-line flags (--port, --orch) via manual arg parsing
- Load .env file from working directory if present

## Build Commands

```bash
# Build orchestrator
cd server && go build -o orchestrator .

# Build agent
cd agents/seo && go build -o seo .

# Run orchestrator
./server/orchestrator --port 9800

# Run agent (connects to orchestrator)
WL_AI_PROVIDER=ollama WL_AI_MODEL=llama3 ./agents/seo --orch http://localhost:9800
```

## Go Module File

```
module weblisk-server

go 1.22
```

No `require` statements needed — stdlib only.
