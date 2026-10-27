"""A type settled to one home is defined in exactly one file, its home.

A definition is a type with `fields` inside a ```yaml block that holds a
`types:` key, written either as a map key (`  Name:`) or as a list item
(`- name: Name`). A binding (`fields_used`) and a contract's listing of a type
(`inherited_by`) are not definitions. Every file that defines a settled type is
printed, so a second home names itself.

  type-home.py [--root DIR]
"""
import os, re, sys

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")
# Each type this corpus has settled, with its home (D27 for ApprovalRequest).
SETTLED = {"ApprovalRequest": "protocol/types.md"}


def defines(block, name):
    lines = block.split("\n")
    if not any(re.match(r"^\s*types:\s*$", l) for l in lines):
        return False
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)(?:" + name + r":|-\s+name:\s*" + name + r")\s*$", line)
        if not m:
            continue
        start = len(m.group(1))                 # the key's or the list dash's column
        for nxt in lines[i + 1:]:
            if not nxt.strip():
                continue
            if len(nxt) - len(nxt.lstrip()) <= start:
                break                           # the entry has ended
            if re.match(r"^\s*fields:", nxt):
                return True
    return False


found = {n: [] for n in SETTLED}
for d, subdirs, files in os.walk(root):
    subdirs[:] = sorted(s for s in subdirs if s != ".git")
    for f in sorted(files):
        if not f.endswith(".md"):
            continue
        path = os.path.join(d, f)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        text = open(path, encoding="utf-8").read()
        for block in re.findall(r"^```ya?ml\n(.*?)^```", text, re.M | re.S):
            for n in SETTLED:
                if defines(block, n) and rel not in found[n]:
                    found[n].append(rel)
faults = []
for n, home in SETTLED.items():
    for rel in found[n]:
        print(f"{rel}: defines {n}")
    if found[n] != [home]:
        faults.append(f"{n} is defined in {len(found[n])} files; want exactly one, {home}")
print("\n".join(faults) or "type-home: every settled type is defined in its home alone")
sys.exit(1 if faults else 0)
