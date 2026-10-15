"""vectors/fabric-ledger.json verifies as architecture/fabric.md's ledger says:
each entry's stored line is its RFC 8785 bytes, `seq` runs from 1, each
`previous_digest` is the SHA-256 of the stored line before it (the first is
the sha256 prefix and 64 zeros), and each line's SHA-256 is the one the vector
records. A fault is reported once, at the entry whose bytes do not hold.

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
    if why:
        faults[seq] = f"seq {seq}: " + "; ".join(why)
for seq in sorted(faults):
    print(faults[seq])
if not faults:
    print(f"fabric-ledger: {len(entries)} entries chain, the last at {recorded[-1]}")
sys.exit(1 if faults else 0)
