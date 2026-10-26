#!/usr/bin/env python3
"""A mapping file's coverage report, produced as schemas/mapping says and
compared with the expected report beside it (coverage-report). On the way it
holds the file to the rules a report depends on: the header's axis and the
keys its axis may carry, each rule's concept declared in schemas/concepts
under a class schemas/mapping names, each rule in the form its class gives,
an UNFILLED or UNAVAILABLE rule with its reason, a rule on a concept its axis
does not own carrying `refines`, and every `verify` naming a vector entry that
exists. The classes, axes, verdicts and concepts are read from those two
files; nothing here lists them.

  mapping-coverage.py [--file MAPPING] [--expect REPORT] [--report]
      default: vectors/mapping/fake-language.md against the .coverage.json
      beside it; --report prints the report produced instead of comparing"""
import json, os, re, sys
import yaml  # PyYAML

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
arg = lambda f, d: sys.argv[sys.argv.index(f) + 1] if f in sys.argv else d
mapping = arg("--file", os.path.join(root, "vectors", "mapping", "fake-language.md"))
expect = arg("--expect", re.sub(r"\.md$", ".coverage.json", mapping))
faults = []


def text(p):
    try:
        return open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")
    except OSError as e:
        print(f"{os.path.relpath(p, root)}: unreadable: {e.strerror}")
        sys.exit(1)


def fences(t):
    """Every top-level yaml fence's value, in order."""
    return [yaml.safe_load(m.group(1)) for m in re.finditer(r"^```yaml\n(.*?)^```", t, re.S | re.M)]


def single(t, key):
    found = [v[key] for v in fences(t) if isinstance(v, dict) and list(v) == [key]]
    return found[0] if len(found) == 1 else None


def header(t):
    if not t.startswith("---\n") or "\n---\n" not in t[3:]:
        return None
    return yaml.safe_load(t[4 : t.index("\n---\n", 3) + 1])


# The two closed lists and the open one.
spec = text(os.path.join(root, "schemas", "mapping.md"))
defs, classes = single(spec, "defs") or {}, single(spec, "classes") or {}
axes = (defs.get("axis") or {}).get("enum") or []
rule_props = set(((defs.get("rule") or {}).get("properties") or {}))
head_props = set(((single(spec, "header") or {}).get("schema") or {}).get("properties") or {})
concepts = single(text(os.path.join(root, "schemas", "concepts.md")), "concepts") or {}
if not (axes and classes and rule_props and head_props and concepts):
    print("schemas/mapping.md or schemas/concepts.md: the axes, classes, rule and header definitions and concepts must all be readable")
    sys.exit(1)
for c, d in classes.items():
    if d.get("owner") not in axes + ["per-concept"]:
        faults.append(f"class {c}: owner {d.get('owner')!r} is no axis")
    if d.get("form") not in ("produce", "evaluate", "extract"):
        faults.append(f"class {c}: form {d.get('form')!r} is not produce, evaluate or extract")


def owner(concept):
    cls = classes[concept.split("/", 1)[0]]
    return concepts[concept].get("owner") if cls["owner"] == "per-concept" else cls["owner"]


for name, e in concepts.items():
    cls = name.split("/", 1)[0]
    if cls not in classes:
        faults.append(f"concept {name}: class {cls} is not one schemas/mapping names")
        continue
    per = classes[cls]["owner"] == "per-concept"
    if per and e.get("owner") not in axes:
        faults.append(f"concept {name}: its class's owner is per-concept and it names no axis")
    if not per and "owner" in e:
        faults.append(f"concept {name}: names an owner its class already fixes")
    for r in e.get("required_by", []):
        if not os.path.isfile(os.path.join(root, r + ".md")):
            faults.append(f"concept {name}: required_by {r}, which is no blueprint of this repository")

# The mapping file.
rel = os.path.relpath(mapping, root)
t = text(mapping)
h = header(t) or {}
axis = h.get("axis")
if h.get("family") != "schemas/mapping@1":
    faults.append(f"{rel}: family is {h.get('family')!r}, not schemas/mapping@1")
if axis not in axes:
    faults.append(f"{rel}: axis {axis!r} is not one of {axes}")
for k in sorted(set(h) - head_props):
    faults.append(f"{rel}: header key {k} is not one schemas/mapping declares")
for k, a in (("accepts_languages", "platform"), ("requires_platforms", "framework")):
    if k in h and axis != a:
        faults.append(f"{rel}: {k} is a {a}'s, and this file's axis is {axis}")
rules = [r for v in fences(t) if isinstance(v, dict) and list(v) == ["rules"] for r in v["rules"]]
seen, by_class = set(), {c: [] for c in classes}
for r in rules:
    rid, concept = r.get("id"), r.get("concept", "")
    if rid in seen:
        faults.append(f"{rel}: rule {rid}: declared twice")
    seen.add(rid)
    for k in sorted(set(r) - rule_props):
        faults.append(f"{rel}: rule {rid}: {k} is not a rule property")
    if concept not in concepts:
        faults.append(f"{rel}: rule {rid}: concept {concept} is not one schemas/concepts declares")
        continue
    cls = concept.split("/", 1)[0]
    by_class[cls].append(r)
    verdict = r.get("verdict")
    forms = [k for k in ("produce", "evaluate", "extract") if k in r]
    if verdict in ("UNFILLED", "UNAVAILABLE"):
        if not r.get("reason"):
            faults.append(f"{rel}: rule {rid}: {verdict} with no reason")
        if forms:
            faults.append(f"{rel}: rule {rid}: {verdict} and also {forms[0]}")
    else:
        if verdict is not None and verdict not in (defs.get("verdict") or {}).get("enum", []):
            faults.append(f"{rel}: rule {rid}: verdict {verdict} is not in the vocabulary")
        if forms != [classes[cls]["form"]]:
            faults.append(f"{rel}: rule {rid}: a {cls} rule carries {classes[cls]['form']}, and this one carries {forms or 'none'}")
        if classes[cls].get("verdict") == "required" and verdict is None:
            faults.append(f"{rel}: rule {rid}: a {cls} rule carries a verdict")
    own = owner(concept)
    if own != axis and "refines" not in r:
        faults.append(f"{rel}: rule {rid}: {concept} is owned by the {own} axis, and the rule names no rule of it that it refines")
    if own == axis and "refines" in r:
        faults.append(f"{rel}: rule {rid}: refines {r['refines']}, but its axis owns {concept}")
    for v in r.get("verify", []):
        f, _, key = v.partition("#")
        try:
            held = json.load(open(os.path.join(root, f), encoding="utf-8")).get("entries") or {}
        except (OSError, ValueError):
            faults.append(f"{rel}: rule {rid}: verify {v} names no readable vector file")
            continue
        if key not in held:
            faults.append(f"{rel}: rule {rid}: verify {v} names no entry of {f}")

report = {
    "file": rel,
    "axis": axis,
    "provides": h.get("provides"),
    "classes": [
        {
            "class": c,
            "owners": [a for a in axes if a == d["owner"] or (d["owner"] == "per-concept" and any(
                e.get("owner") == a for n, e in concepts.items() if n.startswith(c + "/")))],
            "status": "filled" if any(r.get("verdict") != "UNFILLED" for r in by_class[c]) else "UNFILLED",
            "rules": [r["id"] for r in by_class[c]],
        }
        for c, d in classes.items()
    ],
}
if "--report" in sys.argv:
    print(json.dumps(report, indent=2))
    sys.exit(1 if faults else 0)
try:
    want = json.load(open(expect, encoding="utf-8"))
except (OSError, ValueError) as e:
    faults.append(f"{os.path.relpath(expect, root)}: no expected report: {e}")
    want = None
if want is not None:
    for k in ("file", "axis", "provides"):
        if want.get(k) != report[k]:
            faults.append(f"{k}: produced {report[k]!r}, expected {want.get(k)!r}")
    got = {c["class"]: c for c in report["classes"]}
    exp = {c["class"]: c for c in want.get("classes", [])}
    if list(got) != list(exp):
        faults.append(f"classes: produced {list(got)}, expected {list(exp)}")
    for c in got:
        if c in exp and got[c] != exp[c]:
            diff = ", ".join(f"{k} {got[c][k]!r} (expected {exp[c].get(k)!r})" for k in got[c] if got[c][k] != exp[c].get(k))
            faults.append(f"{c}: {diff}")
unfilled = [c["class"] for c in report["classes"] if c["status"] == "UNFILLED"]
print("\n".join(faults) or f"mapping-coverage: {rel} has {len(report['classes']) - len(unfilled)} of {len(report['classes'])} classes filled; UNFILLED: {', '.join(unfilled)}")
sys.exit(1 if faults else 0)
