"""vectors/fabric-ledger.json verifies as architecture/fabric.md's ledger says:
each entry is stored as its RFC 8785 bytes and one line feed, `seq` runs from
1, each `previous_digest` is the SHA-256 of the line before it without its
line feed (the first is the sha256 prefix and 64 zeros), and each line's
SHA-256 is the one the vector records. Each claim's relation is one
schemas/kinds.md declares between its two kinds, and an end whose kind is not
versioned cites a projection or nothing (architecture/fabric.md, Health). A
fault is reported once, at the entry that does not hold. Every field a
cited_version carries is one architecture/fabric.md binds ContentIdentity
with, so a fabric generated from that binding reads the projection it compares
on; a field the binding lacks is reported once, as seq 0.

Nothing here but SHA-256 and a canonicaliser: the canonicaliser below is RFC
8785 for the values the vector holds (objects, arrays, strings, integers,
booleans, null), and refuses anything else rather than guessing.

  fabric-ledger.py [--file PATH] [--fabric PATH]
"""
import hashlib, json, os, sys

path = sys.argv[sys.argv.index("--file") + 1] if "--file" in sys.argv else os.path.join(os.path.dirname(__file__), "..", "vectors", "fabric-ledger.json")
fabric = sys.argv[sys.argv.index("--fabric") + 1] if "--fabric" in sys.argv else os.path.join(os.path.dirname(__file__), "..", "architecture", "fabric.md")


def bound_fields():
    """The fields architecture/fabric.md binds patterns/content-identity's ContentIdentity with."""
    import yaml
    text = open(fabric, encoding="utf-8").read()
    block = text.split("## Dependencies", 1)[1].split("```yaml\n", 1)[1].split("```", 1)[0]
    for dep in yaml.safe_load(block).get("requires", []):
        if dep.get("blueprint") == "patterns/content-identity":
            for ty in dep.get("bindings", {}).get("types", []):
                if ty.get("name") == "ContentIdentity":
                    return set(ty.get("fields_used", []))
    return set()


def canon(v):
    if isinstance(v, bool) or v is None:
        return json.dumps(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ",".join(canon(x) for x in v) + "]"
    if isinstance(v, dict):
        if any(not k.isascii() for k in v):
            raise ValueError("a non-ASCII key: UTF-16 ordering is not implemented here")
        return "{" + ",".join(json.dumps(k) + ":" + canon(v[k]) for k in sorted(v)) + "}"
    raise ValueError(f"{type(v).__name__} is outside what this canonicaliser handles")


def sha(b):
    return "sha256:" + hashlib.sha256(b).hexdigest()


def kinds_table():
    """The relation rows and the versioned kinds, as schemas/kinds.md declares them."""
    text = open(os.path.join(os.path.dirname(__file__), "..", "schemas", "kinds.md"), encoding="utf-8").read()
    words = lambda cell: {w.strip(" `*") for w in cell.split(",")}
    rel, versioned, parent, section = set(), set(), {}, None
    for line in text.split("\n"):
        if line.startswith("## "):
            section = line[3:].strip()
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("| `") else []
        if section == "Declared kinds" and len(cells) == 6:
            parent[cells[0].strip("`")] = cells[1].strip("`")
            if "versioned" in words(cells[5]):
                versioned.add(cells[0].strip("`"))
        if section == "Relations" and len(cells) == 4:
            for f in words(cells[1]):
                for t in words(cells[2]):
                    rel.add((cells[0].strip("`"), f, t))
    for k in parent:                                   # a specialisation inherits
        p = parent[k]
        while p in parent and k not in versioned:
            if p in versioned:
                versioned.add(k)
            p = parent[p]
    return rel, versioned


RELATIONS, VERSIONED = kinds_table()


def claim_faults(e):
    ident = e.get("claim", {}).get("identity", {})
    fr, to, r = ident.get("from", {}), ident.get("to", {}), ident.get("relation")
    why = []
    if (r, fr.get("kind"), to.get("kind")) not in RELATIONS and (r, "any", to.get("kind")) not in RELATIONS:
        why.append(f"{r} from {fr.get('kind')} to {to.get('kind')} is not a relation schemas/kinds.md declares")
    for end in (fr, to):
        cv = end.get("cited_version")
        if cv and end.get("kind") not in VERSIONED and not cv.get("projection"):
            why.append(f"its {end.get('kind')} end cites a version its kind does not have and names no projection")
    return why


vec = json.load(open(path, encoding="utf-8"))
entries, recorded = vec["entries"], vec["line_sha256"]
faults = {}
if len(entries) != len(recorded) or not entries:
    faults[0] = f"{len(entries)} entries and {len(recorded)} recorded line digests"
for k, e in enumerate(entries):
    seq, why = k + 1, []
    try:
        line = canon(e).encode("utf-8")
    except ValueError as err:
        faults[seq] = f"seq {seq}: unreadable: {err}"
        continue
    if k < len(recorded) and sha(line) != recorded[k]:
        why.append("its stored line is not the one recorded")
    if e.get("seq") != seq:
        why.append(f"seq is {e.get('seq')!r}")
    want = "sha256:" + "0" * 64 if k == 0 else recorded[k - 1] if k - 1 < len(recorded) else None
    if e.get("previous_digest") != want:
        why.append("previous_digest does not follow")
    why += claim_faults(e)
    if why:
        faults[seq] = f"seq {seq}: " + "; ".join(why)
cited = {}
for k, e in enumerate(entries):
    ident = e.get("claim", {}).get("identity", {})
    for end in (ident.get("from", {}), ident.get("to", {})):
        for f in (end.get("cited_version") or {}):
            cited.setdefault(f, []).append(k + 1)
unbound = sorted(set(cited) - bound_fields())
if unbound:
    faults[0] = "; ".join(f"cited_version field {f} (seq {', '.join(str(s) for s in sorted(set(cited[f])))}) is not in architecture/fabric.md's ContentIdentity fields_used" for f in unbound)
for seq in sorted(faults):
    print(faults[seq])
if not faults:
    print(f"fabric-ledger: {len(entries)} entries chain, the last at {recorded[-1]}")
sys.exit(1 if faults else 0)
