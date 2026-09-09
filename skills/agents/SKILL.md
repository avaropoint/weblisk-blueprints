---
name: agents
description: Create, start, and list Weblisk agents with the CLI. Use when adding a work agent or an infrastructure agent to a tenant, or when asked how an agent is generated.
---

# Agents

What an agent must do is `architecture/agent.md`. Infrastructure agents
(workflow, task, lifecycle, …) have their own files under `agents/`. This
skill is the command.

## Default

```
weblisk agent create seo
```

Platform defaults to `go`. The model is the one already chosen for this
tenant, or the highest-weighted on the machine.

## Override

```
weblisk agent create seo --platform go
weblisk agent start seo --orch http://localhost:9800 --port 9710
weblisk agent list
weblisk agent verify --url http://localhost:9710
```

Do not write an agent by hand and do not invent endpoints the agent
blueprint does not serve. Generate from the blueprint; start against the
orchestrator.
