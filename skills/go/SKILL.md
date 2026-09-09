---
name: go
description: Go-only facts for a tenant generated with --platform go — module layout and the two mux rules that panic at startup. Use before editing routing, handlers, or anything under internal/protocol in a Go tenant.
---

# Go

`platforms/go.md` is the specification. This skill is the two facts that
panic at process start if broken, plus the module layout the generator
already followed.

## Layout

The tenant is **one module**, rooted at the tenant directory. Shared code
lives once in `internal/` and is imported. Packages are named after the
blueprint that specifies them.

There is no `server/` package: the artifact is an *orchestrator*.

## Two rules that panic at startup

`net/http`'s router enforces these at registration time.

**1. No method-less pattern beside a wildcard sibling.**

```go
mux.HandleFunc("/v1/admin/operators/{name}", h)   // wildcard sibling
mux.HandleFunc("/v1/admin/operators", h)          // PANICS: no method
mux.HandleFunc("GET /v1/admin/operators", h)      // correct
```

Always register with an explicit method.

`wrapModelGateway` already serves `GET/PUT /v1/admin/model`,
`GET /v1/admin/model/providers` and `POST /v1/admin/complete`. Do not
register those paths again.

**2. No path literals reach routing.**

Paths come from `protocol.Path*` constants, never from a `"/v1/..."` string
at the call site.

## Before you say it works

```
go build ./... && go vet ./... && gofmt -l .
weblisk server verify
```

`gofmt -l` returning any filename is a failure.
