#!/usr/bin/env python3
"""`requires` is acyclic: no blueprint requires, through any chain, itself.

    checks/acyclic.py [--root DIR] [--known FILE]

The graph is every file in the corpus with a blueprint header, each `requires`
entry an edge; an entry naming no such file is not this check's business. An
edge lies on a cycle when both its ends are in one strongly connected
component. The edges that did are checks/acyclic.json's `known`, measured when
it was written; the check fails on a cyclic edge not in it, and on a known edge
that no longer lies on a cycle, so the list can only shrink. Which way a known
edge should go is an owner's decision, recorded beside it.
"""
import json, os, re, sys

root = os.path.normpath(sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
known_path = sys.argv[sys.argv.index("--known") + 1] if "--known" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "acyclic.json")

graph = {}
for d, subdirs, files in os.walk(root):
    subdirs[:] = sorted(s for s in subdirs if not s.startswith("."))
    for f in sorted(files):
        if not f.endswith(".md"):
            continue
        path = os.path.join(d, f)
        text = open(path, encoding="utf-8").read()
        if not text.startswith("<!-- blueprint"):
            continue
        m = re.search(r"^requires:\s*\[(.*?)\]", text.split("-->", 1)[0], re.M)
        graph[os.path.relpath(path, root)[:-3]] = [r.strip() for r in m.group(1).split(",") if r.strip()] if m else []
graph = {n: [r for r in req if r in graph] for n, req in graph.items()}

# Tarjan's strongly connected components, iteratively.
index, low, comp, stack, on, counter = {}, {}, {}, [], set(), [0]
for start in sorted(graph):
    if start in index:
        continue
    work = [(start, iter(graph[start]))]
    index[start] = low[start] = counter[0]
    counter[0] += 1
    stack.append(start)
    on.add(start)
    while work:
        v, it = work[-1]
        w = next(it, None)
        if w is not None:
            if w not in index:
                index[w] = low[w] = counter[0]
                counter[0] += 1
                stack.append(w)
                on.add(w)
                work.append((w, iter(graph[w])))
            elif w in on:
                low[v] = min(low[v], index[w])
            continue
        work.pop()
        if work:
            low[work[-1][0]] = min(low[work[-1][0]], low[v])
        if low[v] == index[v]:
            while True:
                w = stack.pop()
                on.discard(w)
                comp[w] = v
                if w == v:
                    break

cyclic = sorted((a, b) for a in graph for b in graph[a] if comp[a] == comp[b])
known = {tuple(e) for e in json.load(open(known_path, encoding="utf-8"))["known"]}
size = lambda n: sum(1 for m in graph if comp[m] == comp[n])
faults = [f"{a} requires {b}, and {b} leads back to {a} (a strongly connected component of {size(a)} blueprints): requires is acyclic"
          for a, b in cyclic if (a, b) not in known]
faults += [f"{a} -> {b} no longer lies on a cycle; remove it from checks/acyclic.json" for a, b in sorted(known - set(cyclic))]
groups = len({comp[a] for a, _ in cyclic})
print("\n".join(faults) or f"acyclic: {len(cyclic)} requires on a cycle, in {groups} strongly connected component{'s' if groups != 1 else ''}, each known, none new")
sys.exit(1 if faults else 0)
