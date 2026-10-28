# Fixture: a component that declares two kinds

## Endpoints

| Method | Path | Operation | Auth | Purpose |
|--------|------|-----------|------|---------|
| GET | /v1/admin/fixtures | FixtureList | yes | The fixture's own list route |

## Types

```yaml
types:
  FixtureItem:
    fields:
      uid:
        type: string
        description: Its id
      title:
        type: string
        description: Its title
      state:
        type: string
        description: Where it is
        enum: [open, closed]
      secret_value:
        type: string
        description: A secret a person sets
      owner_name:
        type: string
        description: The agent that holds it
      opened_at:
        type: timestamp
        description: When it opened
  FixturePart:
    fields:
      uid:
        type: string
        description: Its id
      run:
        type: string
        description: The run it is part of
```

## Resources

```yaml
resources:
  - kind: integration
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    label: title
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: title, access: settable, present: text}
      - {name: state, access: read-only, present: choice}
      - {name: secret_value, access: settable, present: secret, sensitive: true}
      - {name: owner_name, access: create, present: reference, kind: agent}
      - {name: opened_at, access: read-only, present: instant, volatile: true}
    operations:
      list: {capability: "admin:read", binds: FixtureList, items: fixtures, filters: [state]}
      get: {capability: "admin:read"}
      create: {capability: "admin:*"}
      update: {capability: "admin:*"}
    verbs:
      - name: close
        capability: "action:invoke"
        step_up: true
        transition: close
        preconditions: [the item is open]
        in_flight: {handling: drains, says: work under way finishes and nothing new starts}
        effect: the item is closed
        reversible: {by: reopen}
      - name: reopen
        capability: "action:invoke"
        transition: reopen
        preconditions: [the item is closed]
        in_flight: {handling: none, says: a closed item has no work under way}
        effect: the item is open
        reversible: {by: close}
    states:
      initial_state: open
      entity_type: FixtureItem
      state_field: state
      states:
        open: {description: open}
        closed: {description: closed}
      transitions:
        - {name: close, from: open, to: closed, trigger: manual, description: a person closes it}
        - {name: reopen, from: closed, to: open, trigger: manual, description: a person reopens it}
    events: [created, updated, close, reopen, open, closed]
    relations: []
  - kind: run-step
    owner: fixture
    type: FixturePart
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: run, access: read-only, present: reference, kind: run}
    operations:
      get: {capability: "admin:read"}
    events: [created]
    relations:
      - {relation: part_of, to: run, field: run}
    unavailable: {reason: owner-unspecified, says: the fixture's owner has no blueprint}
```
