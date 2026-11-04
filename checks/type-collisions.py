#!/usr/bin/env python3
"""No type name is declared by two blueprints, except those still listed.

    checks/type-collisions.py [--root DIR] [--known FILE]

A declaration is a key of a `types:` block (a ```yaml fence whose root holds
`types:`), in a file outside schemas/, templates/ and vectors/, whose root key
is `types`. Every name declared in more than one file, or twice in one file,
is a collision (schemas/common.md, "Declared Names": a type name is declared
by one blueprint in the whole corpus). The collisions found are
checks/type-collisions.json's `known`, measured when it was written; the check
fails on a collision not in it, and on a known entry whose files no longer
collide, so the list can only shrink.
"""
import collections, json, os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yaml  # noqa: E402
from families import Core  # noqa: E402

root = os.path.normpath(sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(HERE, ".."))
known_path = sys.argv[sys.argv.index("--known") + 1] if "--known" in sys.argv else os.path.join(HERE, "type-collisions.json")
SKIP = ("schemas/", "templates/", "vectors/", "checks/")

homes = collections.defaultdict(list)
for d, subdirs, files in os.walk(root):
    subdirs[:] = sorted(s for s in subdirs if not s.startswith(".") and s != "node_modules")
    for f in sorted(files):
        if not f.endswith(".md"):
            continue
        rel = os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/")
        if rel.startswith(SKIP):
            continue
        text = open(os.path.join(d, f), encoding="utf-8").read()
        for m in re.finditer(r"^```yaml\n(.*?)^```", text, re.S | re.M):
            try:
                v = yaml.load(m.group(1), Loader=Core)
            except yaml.YAMLError:
                continue
            if isinstance(v, dict) and isinstance(v.get("types"), dict):
                for name in v["types"]:
                    homes[str(name)].append(rel)

found = {n: sorted(fs) for n, fs in homes.items() if len(fs) > 1}
known = json.load(open(known_path, encoding="utf-8"))["known"]
faults = []
for n, fs in sorted(found.items()):
    if n not in known:
        faults.append(f"type {n} is declared in {', '.join(fs)}; a type name is declared by one blueprint")
    elif fs != sorted(known[n]):
        faults.append(f"type {n} is now declared in {', '.join(fs)}; checks/type-collisions.json lists {', '.join(sorted(known[n]))}")
for n in sorted(set(known) - set(found)):
    faults.append(f"type {n} no longer collides; remove it from checks/type-collisions.json")
print("\n".join(faults) or f"type-collisions: {len(found)} type names still declared more than once, each known, none new")
sys.exit(1 if faults else 0)
