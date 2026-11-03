#!/usr/bin/env python3
"""The closed `needs:` set is stated once, in schemas/programme.md's
`needs_set` block, and architecture/prompt-worker.md's `needs:` mapping has
exactly its words as keys, so a word cannot be added to one and not the other.

    checks/needs-set.py [--programme FILE] [--worker FILE]
"""
import os, re, sys
import yaml  # PyYAML

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
programme = sys.argv[sys.argv.index("--programme") + 1] if "--programme" in sys.argv else os.path.join(root, "schemas/programme.md")
worker = sys.argv[sys.argv.index("--worker") + 1] if "--worker" in sys.argv else os.path.join(root, "architecture/prompt-worker.md")


def block(path, key):
    found = []
    for m in re.finditer(r"^```yaml\n(.*?)^```", open(path, encoding="utf-8").read(), re.M | re.S):
        try:
            v = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            continue
        if isinstance(v, dict) and key in v:
            found.append(v[key])
    return found


faults = []
sets = block(programme, "needs_set")
if len(sets) != 1 or not isinstance(sets[0], list) or not sets[0]:
    faults.append(f"{programme}: want exactly one non-empty needs_set list, found {len(sets)}")
maps = block(worker, "needs")
if len(maps) != 1 or not isinstance(maps[0], dict):
    faults.append(f"{worker}: want exactly one needs: mapping, found {len(maps)}")
if not faults:
    words, keys = sets[0], list(maps[0])
    if len(set(words)) != len(words):
        faults.append(f"needs_set repeats a word: {words}")
    for w in words:
        if w not in keys:
            faults.append(f"{w}: in needs_set, and the prompt worker maps it to nothing")
    for k in keys:
        if k not in words:
            faults.append(f"{k}: mapped by the prompt worker, and not in needs_set")
print("\n".join(faults) or f"needs-set: {len(sets[0])} words, each mapped once by the prompt worker")
sys.exit(1 if faults else 0)
