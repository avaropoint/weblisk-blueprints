"""The fabric's reach depth is stated in exactly one place: the requirement
reach-max-depth in architecture/fabric.md (D23). Every statement of a walk's
depth bound as data is listed: a YAML key whose name contains `depth`, with an
integer value, where that key or a key enclosing it names a walk (reach,
traversal, dependency, transitive, cascade, impact, propagation), and a
requirement whose id contains `depth` with a `value`. A depth that bounds no
walk, such as a queue's or a nesting limit, is not this number.
Every citation of the requirement must name one that exists.

  reach-depth.py [--root DIR]
"""
import os, re, sys

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")
HOME, REQ = "architecture/fabric.md", "reach-max-depth"
CITE = "requirement://weblisk/architecture/fabric:"
key = re.compile(r"^(\s*)(?:-\s*)?((?=[A-Za-z_])[\w-]*depth[\w-]*)\s*:\s*(\d+)\s*(?:#.*)?$")
anykey = re.compile(r"^(\s*)(?:-\s*)?([A-Za-z_][\w-]*)\s*:")
WALK = re.compile(r"reach|travers|dependen|transitive|cascade|impact|propagat|walk", re.I)
rid = re.compile(r"^(\s*)-\s*id:\s*([\w.-]*depth[\w.-]*)\s*$")
places, cites, ids = [], [], set()
for d, subdirs, files in os.walk(root):
    subdirs[:] = sorted(s for s in subdirs if s != ".git")
    for f in sorted(files):
        if not f.endswith(".md"):
            continue
        path = os.path.join(d, f)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        lines = open(path, encoding="utf-8").read().split("\n")
        stack = []                                      # (indent, key) of enclosing keys
        for n, line in enumerate(lines, 1):
            a = anykey.match(line)
            if a:
                ind = len(a.group(1))
                while stack and stack[-1][0] >= ind:
                    stack.pop()
            m = key.match(line)
            if m and any(WALK.search(k) for k in [m.group(2)] + [k for _, k in stack]):
                places.append((rel, n, m.group(2), m.group(3)))
            if a:
                stack.append((len(a.group(1)), a.group(2)))
            m = rid.match(line)
            if m:
                ids.add((rel, m.group(2)))
                indent = len(m.group(1)) + 2
                for k in range(n, len(lines)):          # the item's own keys
                    nxt = lines[k]
                    if nxt.strip() and (len(nxt) - len(nxt.lstrip())) < indent or nxt.lstrip().startswith("- "):
                        break
                    v = re.match(r"^\s*value:\s*(\d+)\s*$", nxt)
                    if v:
                        places.append((rel, n, "requirement " + m.group(2), v.group(1)))
            for c in re.findall(re.escape(CITE) + r"([\w.-]+)", line):
                cites.append((rel, n, c))
faults = []
for rel, n, c in cites:
    if (HOME, c) not in ids and not (rel == HOME):
        faults.append(f"{rel}:{n}: cites {CITE}{c}, which {HOME} does not declare")
if not any(rel == "architecture/change-management.md" and c == REQ for rel, n, c in cites):
    faults.append(f"architecture/change-management.md does not cite {CITE}{REQ}")
for p in places:
    print(f"{p[0]}:{p[1]}: {p[2]} = {p[3]}")
if len(places) != 1 or places[0][0] != HOME or places[0][2] != "requirement " + REQ:
    faults.append(f"{len(places)} places state a depth bound; want exactly one, {HOME} requirement {REQ}")
print("\n".join(faults) or f"reach-depth: one home, {len(cites)} citations resolve")
sys.exit(1 if faults else 0)
