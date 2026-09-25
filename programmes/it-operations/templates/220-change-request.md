---
id: change-request
label: Change Request
description: A proposed change to a production system — what is changing, why, what could go wrong, and how it is undone.
path: records/changes/untitled-change.md
template: true
kind: reference
order: 220
frontmatter:
  title: Change Request
  kind: evidence
  status: draft
  reference:
  raised_on:
  type:
---

# Change Request

> [!NOTE]
> **An emergency change still gets one of these** — written immediately
> afterwards, marked as emergency, and reviewed like any other. An emergency
> process with no retrospective record becomes the normal process within a
> quarter.

## What is changing

- **Reference:**  **Raised on:**  **Raised by:**
- **System or service:**
- **Type:** standard / normal / emergency

*What is being changed, in enough detail that somebody else could tell whether
it was done.*

## Why

*What happens if it is not made. A change with no stated reason cannot be
prioritised or refused.*

## Risk

- **Risk if it goes wrong:** low / medium / high
- **Who is affected:**
- **Window and expected duration:**

## Security and privacy impact

| | Yes / No |
|---|---|
| Does it change who can reach what? |  |
| Does it open a network path or expose a service? |  |
| Does it move, copy or newly collect personal information? |  |
| Does it involve a new supplier or service? |  |

> [!IMPORTANT]
> Any yes means this change needs the information security lead's agreement
> before approval, and a yes on personal information means a privacy impact
> screening. Approval is the only moment anybody will notice.

## How it is backed out

> [!WARNING]
> "Restore from backup" is only a backout plan if somebody has restored from
> that backup recently. If that is the plan, say when the last successful
> restore test was.

## Testing

*What was tested, where, and by whom. If it was not tested, say so — that is a
risk being accepted, and the approver should be accepting it knowingly.*

## Approval

- **Approved by:**  **Date:**
- **Conditions:**

## After implementation

- **Implemented on:**  **By:**
- **Outcome:** successful / partially successful / backed out / failed
- **Did it cause an incident or degradation:**
- **Documentation and asset register updated:**
