---
name: kinds
description: What sorts of thing the platform can talk about — kinds are declared data, capabilities are code, and nothing switches on a kind. Use when classifying content, relating one thing to another, scoring coverage, or adding a new sort of thing.
---

# Kinds and capabilities

`schemas/kinds.md` declares them. This skill is how to work with them.

## The one rule

**Never switch on a kind. Ask what it can do.**

    if reg.Can(k, "chain-member") { ... }     // right
    switch kind { case "policy": ... }        // wrong

A `switch` over kind names is a closed set written in the wrong place. Five
independent vocabularies grew that way and disagreed; `code` existed in three of
them and not the fourth, so the code the platform generated could not appear in
an evidence chain at all.

## Kinds are data, capabilities are code

| | | |
|---|---|---|
| Kinds | **open** | declared in `schemas/kinds.md`, extended freely |
| Capabilities | **closed** | each is a contract with an implementation |

**Adding a kind is declaring it** — no code changes, in any tool. **Adding a
capability is deliberate**, because something has to honour it. A capability
nothing implements is a label nothing consumes, which is worse than not offering
it: it looks like configuration and does nothing.

## There is no default

A kind either declares a capability or does not have it, and **not having it is
an answer**. An undeclared kind is representable, reported as undeclared, and
granted nothing.

This replaced three separate `default:` arms that placed unrecognised kinds into
an evidence chain — one as `standard`, one as `blueprint`, one as `reference`.
All three scored unknown documents as compliance.

## The two capabilities most often got wrong

`counts-as-coverage` and `opens-gap` are **separate**. A guideline has **neither**:
not following advice is not a finding, and following it is not compliance. One
"mandatory" flag cannot express that, and collapsing them is what let advisory
material be scored as standard-level evidence.

## Kinds specialise

`sop` specialises `procedure`; `blueprint` specialises `specification`. A
specialisation **adds** capabilities and never removes them, so logic written for
a parent applies to a child unchanged — ask for procedures and you get SOPs.

If a child needs to drop a capability, the parent was wrong.

## Classification

One implementation, from declared stems. **Directories outrank filenames** — a
directory says what kind of thing lives here, a filename says what this one is
about — and the **nearest directory wins**. So `patterns/policy.md` is a
blueprint about policy, and `standards/policies/acceptable-use.md` is a policy.

Nothing matching means `document`: **unclassified**, contributing nothing.

Content signals are the next-weakest evidence and are also declared — words and
weights in the schema, scoring in the tool.

## Relations

A relation is meaningful only between the kinds the schema pairs. One asserted
outside that table is a fault in the producer, not a new relation.

A declared target may name its kind — `implements: [control:A.5.15]` — because an
identifier alone cannot say what it is, and **guessing from its shape is how a
platform asserts something an author never said**. Unqualified means a blueprint,
as before; a prefix is a qualifier only when it names a declared kind, so a URL
is left whole.

## platform, provider, integration — three things, three words

One word was doing two jobs; this is the ambiguity the taxonomy exists to remove.

| | Answers | Examples |
|---|---|---|
| **platform** | what is this written in, and where does it execute? | Go, Node, Rust, Cloudflare Workers |
| **provider** | whose service is this, and does its configuration satisfy our policy? | Microsoft 365, Google Workspace, AWS, Cloudflare |
| **integration** | what data crosses this boundary, under what contract? | the connection to any of them |

**`platform` is NOT a kind.** It is the language-and-runtime binding a component
is generated for — `platforms/go.md`, `--platform cloudflare`. Nothing in
`schemas/kinds.md` declares it.

**One vendor may be both.** Cloudflare is a platform when you build Workers for
it and a provider when you govern the account. Two relationships with one
company, two questions — which is why they need two words.

**Display labels are not identifiers.** A view may head a column "Platforms"
over provider nodes if that is what its readers call them. The identifier is what
tools join on and must mean one thing.

## Adding a sort of thing

1. Declare it in `schemas/kinds.md` with its identity rule, origin and
   capabilities.
2. Give it a `specializes` parent if an existing kind already describes most of
   it.
3. Add stems if a path should classify into it.
4. Add it to the relation table wherever it may legitimately appear.
5. **Write no code.** If you needed to, a capability is missing — add that
   instead, deliberately, with the implementation that honours it.
