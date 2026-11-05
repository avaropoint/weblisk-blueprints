---
family: schemas/instruction@1
version: 1.0.0
in: [plan]
---
# The shape of a plan

The one JSON object a plan answer is, its keys, and the rules a plan is
refused for breaking, told before it is asked rather than after.

## Why

A plan is read by a tool, and a convention requested in prose is honoured
differently by different models
([`architecture/generation`](../architecture/generation.md#the-prompt-contract),
element 1). Each key's rule was learned from a plan that broke it: a plan that
left out its build command produced "Generated N files" having compiled
nothing, because the whole verification chain was guarded on that command; a
plan with no run command started nothing on every platform but one, after the
whole generation had been paid for; a run command written as a shell line was
stopped by signalling the shell and left the component running. Each was then
refused by plan validation and asked again, at the cost of a planning round
that one sentence here saves.

## Text

```text
Your plan is one JSON object and nothing else: the first character of your
answer is {. Its keys are root, prepare, build, run, files and gaps.

root is the directory the component is generated into, relative to the
tenant root, and is "." unless the platform blueprint says otherwise. prepare
is the platform blueprint's dependency-resolution command, or "" where it
declares none. build is the command the platform blueprint gives to compile
this component, or "none" exactly where that blueprint says the platform has
no build step; a plan without a build is refused. run is the command the
platform blueprint's Run line gives to start the component, without any
--port or --orch flag, which are appended for the operator, and with the
separator a runner needs before forwarded flags. run is one command, never a
shell line: no &&, no pipe and no redirection, because the process it starts
is the component.

Each entry of files has path, purpose, declares, serves and depends_on.
serves lists endpoints as METHOD /path. depends_on names only files of this
plan, never forms a cycle, and every file comes after the files it depends
on, so an entry point comes last. Every type the requirements list is
declared by exactly one file, every endpoint they list is served by exactly
one file, and no symbol is declared by two files.

gaps lists each name the plan needs and no blueprint declares, as an object
with kind and sentence, the sentence of the requirement that needs it quoted
exactly; it is [] when there is none.
```
