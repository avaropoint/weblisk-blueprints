"""vectors/fabric-ledger.json verifies as architecture/fabric.md's ledger says:
each entry is stored as its RFC 8785 bytes and one line feed, `seq` runs from
1, each `previous_digest` is the SHA-256 of the line before it without its
line feed (the first is the sha256 prefix and 64 zeros), and each line's
SHA-256 is the one the vector records. Each claim's relation is one
schemas/kinds.md declares between its two kinds, and an end whose kind is not
versioned cites a projection or nothing (architecture/fabric.md, Health). A
fault is reported once, at the entry that does not hold.

Nothing here but SHA-256 and a canonicaliser: the canonicaliser below is RFC
8785 for the values the vector holds (objects, arrays, strings, integers,
booleans, null), and refuses anything else rather than guessing.

  fabric-ledger.py [--file PATH]
"""
import hashlib, json, os, sys

path = sys.argv[sys.argv.index("--file") + 1] if "--file" in sys.argv else os.path.join(os.path.dirname(__file__), "..", "vectors", "fabric-ledger.json")


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
for seq in sorted(faults):
    print(faults[seq])
if not faults:
    print(f"fabric-ledger: {len(entries)} entries chain, the last at {recorded[-1]}")
sys.exit(1 if faults else 0)
