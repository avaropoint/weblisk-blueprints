#!/usr/bin/env python3
"""Every finding code schemas/family.md declares has exactly one policy, and
every grammar vector's findings carry it (schemas/family.md, findings-closed):
the policy the `finding` definition fixes for the code, or, for the three
codes it leaves to the declaration, the one the vector's declaration gives.
Findings are in order of span start, then code.
    checks/findings.py                            check vectors/grammar/
    checks/findings.py --dir DIR --family FILE    check DIR, or another family.md"""
import glob, json, os, re, sys
import yaml  # PyYAML

def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
d, fam = arg("--dir", os.path.join(root, "vectors", "grammar")), arg("--family", os.path.join(root, "schemas", "family.md"))
def blocks(path):
    out = {}
    for m in re.finditer(r"^```yaml\n(.*?)^```", open(path, encoding="utf-8-sig").read(), re.S | re.M):
        v = yaml.safe_load(m.group(1))
        if isinstance(v, dict) and len(v) == 1: out.update(v)
    return out
defs = blocks(fam)["defs"]
codes, fixed, faults = defs["finding-code"]["enum"], {}, []
for rule in defs["finding"].get("allOf", []):
    for c in rule["if"]["properties"]["code"]["enum"]:
        fixed.setdefault(c, []).append(rule["then"]["properties"]["policy"]["const"])
DECLARED = {"legacy-key", "undeclared-slot", "missing-slot"}
for c in codes:
    n = len(fixed.get(c, [])) + (c in DECLARED)
    if n != 1: faults.append(f"{c}: {'no policy' if n == 0 else f'{n} policies'}")
faults += [f"{c}: a policy for a code finding-code does not declare" for c in sorted(set(fixed) - set(codes))]
def declared(code, subject, decl):
    if code == "legacy-key": return decl["header"].get("legacy", {}).get(subject)
    if code == "undeclared-slot": return decl["sections"].get("undeclared", {}).get("policy")
    req = next((s.get("required") for s in decl["sections"]["slots"] if s["slot"] == subject), None)
    return "report" if req == "report" else "refuse" if req else None
for pj in sorted(glob.glob(os.path.join(d, "*.projection.json"))):
    p, name = json.load(open(pj)), os.path.basename(pj)[:-len(".projection.json")]
    decl = blocks(os.path.join(root, p["family"].rsplit("@", 1)[0] + ".md"))  # a family is its declaration's ref
    for f in p["findings"]:
        want = declared(f["code"], f.get("subject"), decl) if f["code"] in DECLARED else (fixed.get(f["code"]) or [None])[0]
        if f["code"] not in codes: faults.append(f"{name}: {f['code']} is no declared finding code")
        elif f["policy"] != want: faults.append(f"{name}: {f['code']} is {f['policy']}, its policy is {want}")
    if [(f["span"][0], f["code"]) for f in p["findings"]] != sorted((f["span"][0], f["code"]) for f in p["findings"]):
        faults.append(f"{name}: findings not in order of span start, then code")
print("\n".join(faults) or f"findings: {len(codes)} codes, each with one policy, carried by every vector")
sys.exit(1 if faults else 0)
