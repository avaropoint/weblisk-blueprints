---
family: schemas/architecture@2
version: 1.0.1
requires:
  - {ref: protocol/types, version: ">=4.0.0 <6.0.0"}
runs_with: [architecture/orchestrator]
cardinality: singleton
tier: free
retired: []
---
# Component name

One sentence: what this component is, and the one thing it is for.

## Overview

Two to five sentences on what the component owns and where its scope ends.
Every slot this template leaves out is declared in
[`schemas/architecture`](../schemas/architecture.md#sections); add one only when
the component has something to say in it.

## Requirements

```yaml
requirements:
  - id: example-request-answered
    level: must
    text: An example request is answered with an example response naming its subject.
    refs: [ExampleRequest, ExampleResponse]
  - id: example-refusal-coded
    level: must
    text: An example request that cannot be answered is refused with a declared error code.
    refs: [ExampleRequest]
```

## Architecture

A diagram of the component's parts and its place beside the components it
works with, then a sentence on each part.

## Responsibilities

### Owns

- What this component is answerable for.

### Does not own

- What it leaves to another component, and which one.

## Interface

```yaml
serves:
  - id: example
    request: ExampleRequest
    response: ExampleResponse
    http: {method: POST, path: /v1/example}
```

## Error Handling

```yaml
errors:
  - {code: EXAMPLE_REFUSED, http: 422, category: permanent, description: The request names no subject.}
```

## Data Flow

Where a request enters, each step with the part responsible for it, and what
leaves.

## Types

```yaml
types:
  ExampleRequest:
    description: A request the component answers.
    fields:
      subject: {type: string, description: What the request is about.}
  ExampleResponse:
    description: The answer to an ExampleRequest.
    fields:
      subject:  {type: string, description: The subject the request named.}
      answered: {type: timestamp, description: When the request was answered.}
```

## Configuration

```yaml
config:
  example_timeout: {type: duration, required: false, default: "30s", description: How long an example request may take before it is abandoned.}
```

## Security

Who may call each operation, what the component trusts and why, and the
boundaries it enforces.

## Verification

```yaml
verifies:
  - id: example-request-is-answered
    covers: [example-request-answered]
    check: endpoint-answers
    assertion: A POST to /v1/example naming a subject is answered with that subject.
  - id: example-without-subject-refused
    covers: [example-refusal-coded]
    check: endpoint-refuses
    assertion: A POST to /v1/example naming no subject is refused with EXAMPLE_REFUSED.
```

## Operation: example

<!-- wl:explains example-request-answered -->
Why the requirement it explains holds: the reason a reader needs to keep the
rule when the circumstances change. It states no rule of its own.

## Implementation Notes

- Practical guidance for whoever builds the component.
