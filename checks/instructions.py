#!/usr/bin/env python3
"""Every instruction in instructions/ against schemas/instruction.md's
requirements, reading the build steps from architecture/engine.md's steps
block and keeping no copy of either:

  instruction-path-is-id    every instruction is a file instructions/<id>.md
  instruction-in-declared   each step in `in` is declared, with its model called
  instruction-slots-placed  each slot is an input of every step in `in`, and is
                            written {{name}} exactly once; no {{name}} is undeclared
  instruction-one-text      the Text section is one ```text fence and nothing else
  instruction-every-step    every step whose model is called is in some `in`

The header and the sections are walked by checks/families.py; this check
holds what a walk of one file cannot see.

  instructions.py [--root DIR]
"""
import glob, os, re, sys
import yaml

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
engine = open(os.path.join(root, "architecture", "engine.md"), encoding="utf-8").read()
blocks = [b for b in re.findall(r"^```yaml\n(.*?)^```", engine, re.M | re.S) if b.startswith("steps:")]
if len(blocks) != 1:
    print(f"architecture/engine.md has {len(blocks)} steps blocks; want exactly one")
    sys.exit(1)
steps = {s["id"]: s for s in yaml.safe_load(blocks[0])["steps"]}
called = {i for i, s in steps.items() if s.get("model") == "called"}

findings, named, count = [], set(), 0
for p in sorted(glob.glob(os.path.join(root, "instructions", "**", "*.md"), recursive=True)):
    rel = os.path.relpath(p, root).replace(os.sep, "/")
    if os.path.basename(p) == "README.md":
        continue
    count += 1
    if os.path.dirname(rel) != "instructions":
        findings.append(f"{rel}: instruction-path-is-id: not a file instructions/<id>.md, so no family covers it")
        continue
    text = open(p, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    head = yaml.safe_load(m.group(1)) if m else None
    if not isinstance(head, dict):
        findings.append(f"{rel}: no header")
        continue
    ins, slots = head.get("in") or [], head.get("slots") or []
    for s in ins:
        if s not in steps:
            findings.append(f"{rel}: instruction-in-declared: in names {s}, which architecture/engine declares no step")
        elif s not in called:
            findings.append(f"{rel}: instruction-in-declared: in names {s}, whose model is not called")
        named.add(s)
    sec = re.search(r"^## Text\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    body = sec.group(1) if sec else ""
    fences = re.findall(r"^```text\n(.*?)^```\n?", body, re.M | re.S)
    rest = re.sub(r"^```text\n.*?^```\n?", "", body, flags=re.M | re.S)
    if len(fences) != 1 or rest.strip() or len(re.findall(r"^```", body, re.M)) != 2:
        findings.append(f"{rel}: instruction-one-text: the Text section is not exactly one text fence")
        continue
    placed = re.findall(r"\{\{([^}]*)\}\}", fences[0])
    for s in slots:
        if placed.count(s) != 1:
            findings.append(f"{rel}: instruction-slots-placed: slot {s} is written {placed.count(s)} times, not once")
        for st in ins:
            if st in steps and s not in (steps[st].get("inputs") or []):
                findings.append(f"{rel}: instruction-slots-placed: slot {s} is not an input of step {st}")
    for s in sorted(set(placed) - set(slots)):
        findings.append(f"{rel}: instruction-slots-placed: {{{{{s}}}}} is written and not declared")
for s in sorted(called - named):
    findings.append(f"architecture/engine.md: instruction-every-step: step {s} calls a model, and no instruction names it")
if count == 0:
    findings.append("instructions/: no instruction read")
print("\n".join(findings) or f"instructions: {count} instructions against {len(steps)} steps, {len(called)} of them calling a model")
sys.exit(1 if findings else 0)
