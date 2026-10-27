#!/usr/bin/env python3
"""Every slot of a family that holds a block of TYPE lists VALUE in its
`produces`, and at least one slot holds it. A `produces` value no mapping binds
is reported as unproduced by the build that reads the mapping
(schemas/family.md); a value missing from the declaration leaves nothing to
report, so until a mapping binds each pair the pairs are held here.
    checks/produces.py FAMILY TYPE VALUE [--decl FILE]   e.g. schemas/architecture events api.asyncapi"""
import os, re, sys
import yaml  # PyYAML

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
family, btype, value = sys.argv[1:4]
text = open(arg("--decl", os.path.join(root, family + ".md")), encoding="utf-8-sig").read().replace("\r\n", "\n")
blocks = [yaml.safe_load(m.group(1)) for m in re.finditer(r"^```yaml\n(.*?)^```", text, re.S | re.M)]
sections = next((b["sections"] for b in blocks if isinstance(b, dict) and list(b) == ["sections"]), None)
if not sections: sys.exit(f"produces: {family} declares no sections")
holding = [s for s in sections["slots"] if any(b.get("type") == btype for b in s.get("blocks", []))]
if not holding: sys.exit(f"produces: no slot of {family} holds a {btype} block")
bad = [s["slot"] for s in holding if value not in s.get("produces", [])]
for slot in bad: print(f"{family}: slot {slot} holds {btype} and does not produce {value}")
if bad: sys.exit(1)
print(f"{family}: {', '.join(s['slot'] for s in holding)} holds {btype} and produces {value}")
