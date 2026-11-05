#!/usr/bin/env python3
"""The framework requires the patterns; a pattern never requires the framework.

    checks/layering.py [--root DIR] [--known FILE]

A pattern is a file under patterns/ with a blueprint header; the framework is
every blueprint under architecture/, agents/ and domains/ (schemas/common.md,
Field Constraints, `requires`). Each `requires` entry of a pattern's header
that names the framework is a layering fault. The faults found are
checks/layering.json's `known`, measured when it was written; the check fails
on a fault not in it, and on a known entry that is no longer a fault, so the
list can only shrink.
"""
import glob, json, os, re, sys

root = os.path.normpath(sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
known_path = sys.argv[sys.argv.index("--known") + 1] if "--known" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "layering.json")
FRAMEWORK = ("architecture/", "agents/", "domains/")


def requires(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("<!-- blueprint"):
        return None
    m = re.search(r"^requires:\s*\[(.*?)\]", text.split("-->", 1)[0], re.M)
    return [r.strip() for r in m.group(1).split(",") if r.strip()] if m else []


found = {}
for p in sorted(glob.glob(os.path.join(root, "patterns", "*.md"))):
    req = requires(p)
    if req is None:
        continue
    bad = sorted(r for r in req if r.startswith(FRAMEWORK))
    if bad:
        found["patterns/" + os.path.basename(p)[:-3]] = bad

known = json.load(open(known_path, encoding="utf-8"))["known"]
faults = []
for f, bad in sorted(found.items()):
    k = sorted(known.get(f, []))
    for r in bad:
        if r not in k:
            faults.append(f"{f} requires {r}: a pattern never requires the framework")
    for r in k:
        if r not in bad:
            faults.append(f"{f} no longer requires {r}; remove it from checks/layering.json")
for f in sorted(set(known) - set(found)):
    for r in sorted(known[f]):
        faults.append(f"{f} no longer requires {r}; remove it from checks/layering.json")
n = sum(len(v) for v in found.values())
print("\n".join(faults) or f"layering: {n} requires of the framework in {len(found)} patterns, each known, none new")
sys.exit(1 if faults else 0)
