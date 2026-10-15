#!/usr/bin/env python3
"""Every `$ref` in a family declaration resolves (schemas/family.md,
schema-refs-resolve): `#/$defs/<name>` to an entry of the declaration's own
`defs` block, and `<ref>#/$defs/<name>` to one of the declaration whose ref is
<ref>, the file <ref>.md in this repository. Nothing else is a `$ref`.
    checks/refs.py              check every declaration in this repository
    checks/refs.py --scan DIR   check the declarations under DIR, resolving
                                cross-declaration refs against this repository"""
import os, re, sys
import yaml  # PyYAML

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
scan = sys.argv[sys.argv.index("--scan") + 1] if "--scan" in sys.argv else root
FAMILY = "schemas/family@1"
REF = re.compile(r"^(?:([A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.-]*)*))?#/\$defs/([a-z][a-z0-9-]*)$")

def text(path):
    return open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
def is_declaration(path):
    t = text(path)
    return t.startswith("---\n") and f"\nfamily: {FAMILY}\n" in t.split("\n---\n", 1)[0] + "\n"
def blocks(path):
    out = {}
    for m in re.finditer(r"^```yaml\n(.*?)^```", text(path), re.S | re.M):
        v = yaml.safe_load(m.group(1))
        if isinstance(v, dict) and len(v) == 1: out.update(v)
    return out
def refs(v, at=""):
    if isinstance(v, dict):
        for k, x in v.items():
            if k == "$ref": yield at + "/$ref", x
            else: yield from refs(x, f"{at}/{k}")
    elif isinstance(v, list):
        for i, x in enumerate(v): yield from refs(x, f"{at}/{i}")

defs_of = {}
def defs(path):
    if path not in defs_of: defs_of[path] = blocks(path).get("defs") or {}
    return defs_of[path]

faults, n, files = [], 0, 0
for d, subdirs, names in os.walk(scan):
    subdirs[:] = sorted(s for s in subdirs if not s.startswith("."))
    for name in sorted(names):
        path = os.path.join(d, name)
        if not name.endswith(".md") or not is_declaration(path): continue
        files += 1
        rel = os.path.relpath(path, scan)
        for key, value in blocks(path).items():
            for at, r in refs(value, key):
                n += 1
                m = REF.match(r) if isinstance(r, str) else None
                if not m:
                    faults.append(f"{rel}: {at}: {r!r} is neither #/$defs/<name> nor <ref>#/$defs/<name>")
                    continue
                target = path if m.group(1) is None else os.path.join(root, m.group(1) + ".md")
                if not os.path.isfile(target):
                    faults.append(f"{rel}: {at}: {r} names {m.group(1)}, which is no file of this repository")
                elif not is_declaration(target):
                    faults.append(f"{rel}: {at}: {r} names {m.group(1)}, which is not a family declaration")
                elif m.group(2) not in defs(target):
                    faults.append(f"{rel}: {at}: {r} names no definition of {os.path.relpath(target, root)}")
if not files: faults.append(f"no family declarations under {scan}")
print("\n".join(faults) or f"refs: {n} $ref in {files} declarations, each resolving to a definition")
sys.exit(1 if faults else 0)
