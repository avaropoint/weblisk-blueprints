"""Every full type ref in this corpus's own namespace,
type://weblisk/<file>:<Name>, names a type that file declares: a `<Name>:` key
directly under a `types:` key in one of its YAML blocks (schemas/names.md,
Families). A ref that names nothing is reported once, where it is written.

  type-refs.py [--root DIR]
"""
import os, re, sys

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")
REF = re.compile(r"type://weblisk/([a-z0-9/-]+):([A-Za-z0-9_]+)")


def declared(rel):
    try:
        text = open(os.path.join(root, rel + ".md"), encoding="utf-8").read()
    except OSError:
        return None
    names = set()
    for block in re.findall(r"```yaml\n(.*?)```", text, re.S):
        indent = None
        for line in block.split("\n"):
            m = re.match(r"^(\s*)types:\s*$", line)
            if m:
                indent = len(m.group(1))
                continue
            if indent is None or not line.strip():
                continue
            lead = len(line) - len(line.lstrip())
            if lead <= indent:
                indent = None
            elif lead == indent + 2:
                k = re.match(r"^\s*([A-Za-z0-9_]+):", line)
                if k:
                    names.add(k.group(1))
    return names


faults, seen = [], 0
for d, subdirs, files in os.walk(root):
    subdirs[:] = sorted(s for s in subdirs if not s.startswith("."))
    for f in sorted(files):
        if not f.endswith((".md", ".json", ".yaml")):
            continue
        path = os.path.join(d, f)
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        for n, line in enumerate(open(path, encoding="utf-8").read().split("\n"), 1):
            for target, name in REF.findall(line):
                seen += 1
                names = declared(target)
                if names is None:
                    faults.append(f"{rel}:{n}: type://weblisk/{target}:{name} names {target}.md, which does not exist")
                elif name not in names:
                    faults.append(f"{rel}:{n}: type://weblisk/{target}:{name} names a type {target}.md does not declare")
print("\n".join(faults) or f"type-refs: {seen} type refs, each names a declared type")
sys.exit(1 if faults else 0)
