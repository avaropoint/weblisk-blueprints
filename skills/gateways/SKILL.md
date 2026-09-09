---
name: gateways
description: Create and start the Weblisk application gateway with the CLI. Use when adding the end-user edge to a tenant, or when asked how the gateway is generated.
---

# Gateways

What the application gateway must do is `architecture/gateway.md`. This
skill is the command.

## Default

```
weblisk gateway create
```

Platform defaults to `go`. One gateway per tenant.

## Override

```
weblisk gateway create --platform go
weblisk gateway start
```

Do not write the gateway by hand. The command reads the gateway blueprint
and assembles the prompt.
