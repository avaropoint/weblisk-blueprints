# Fixture: one declared kind per rule, each breaking that rule alone

Every kind below is one declared kind with one fault. The first `document`
is well formed, so the second is the one whose finding is `resource-kind-once`.

## Types

```yaml
types:
  FixtureItem:
    fields:
      uid: {type: string, description: Its id}
      title: {type: string, description: Its title}
      secret_value: {type: string, description: A secret a person sets}
      owner_name: {type: string, description: The agent that holds it}
```

## Resources

```yaml
resources:
  - kind: not-a-kind
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
  - kind: document
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
  - kind: document
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
  - kind: policy
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    colour: blue
  - kind: standard
    owner: fixture
    type: NoSuchType
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
  - kind: procedure
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: random}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
  - kind: sop
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: nonexistent, access: read-only}
    operations:
      get: {capability: "admin:read"}
  - kind: guideline
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: writable, present: text}
    operations:
      get: {capability: "admin:read"}
  - kind: reference
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: title, access: read-only, present: colour-wheel}
    operations:
      get: {capability: "admin:read"}
  - kind: specification
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
      - {name: secret_value, access: settable, present: text, sensitive: true}
    operations:
      get: {capability: "admin:read"}
  - kind: blueprint
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
      purge: {capability: "admin:*"}
  - kind: code
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:everything"}
  - kind: evidence
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
      list: {capability: "admin:read", binds: NoSuchOperation, items: things}
  - kind: provider
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    verbs:
      - name: delete
        capability: "action:invoke"
        preconditions: [the item exists]
        in_flight: {handling: none, says: nothing is under way}
        effect: it is gone
        reversible: false
  - kind: partner
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    verbs:
      - name: nudge
        capability: "action:invoke"
        preconditions: [the item exists]
        in_flight: {handling: none, says: nothing is under way}
        reversible: false
  - kind: component
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    states:
      initial_state: open
      states: {open: {description: open}, closed: {description: closed}}
      transitions:
        - {name: close, from: open, to: closed, trigger: manual, description: a person closes it}
  - kind: obligation
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    states:
      initial_state: nowhere
      states: {open: {description: open}}
      transitions: []
  - kind: register
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    events: [exploded]
  - kind: skill
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    relations:
      - {relation: run_by, to: agent, field: owner_name}
  - kind: workflow
    owner: fixture
    type: FixtureItem
    identity: {field: uid, form: minted}
    fields:
      - {name: uid, access: read-only, present: text}
    operations:
      get: {capability: "admin:read"}
    unavailable: {reason: owner-not-registered, says: it is not running}
```
