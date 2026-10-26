#!/usr/bin/env python3
"""vectors/types.json holds what its own `format` says (schemas/mapping,
verify-by-vector): every entry has exactly one of `cases`, `see` or `pending`;
a `see` names a vector file of this repository; a `pending` entry names its
lane and gives no value; and every canonical-json case canonicalises, by RFC
8785 as written here, to the serialisation the vector records. A fault is
reported once, naming the entry or case.

The canonicaliser below is RFC 8785's own: keys sorted by UTF-16 code units,
numbers as IEEE 754 doubles written the way ECMAScript writes them, strings
escaped only where JSON requires. Python's repr gives the shortest digits that
round-trip, as ECMAScript does; the layout around them is section 3.2.2.3's.

  types-vectors.py [--file PATH]"""
import decimal, json, math, os, struct, sys

root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
path = sys.argv[sys.argv.index("--file") + 1] if "--file" in sys.argv else os.path.join(root, "vectors", "types.json")


def number(x):
    if math.isnan(x) or math.isinf(x):
        raise ValueError("NaN and infinity have no JSON form")
    if x == 0:
        return "0"
    sign = "-" if x < 0 else ""
    _, digits, exp = decimal.Decimal(repr(abs(x))).normalize().as_tuple()
    d = "".join(map(str, digits))
    k, n = len(d), exp + len(d)
    if k <= n <= 21:
        return sign + d + "0" * (n - k)
    if 0 < n <= 21:
        return sign + d[:n] + "." + d[n:]
    if -6 < n <= 0:
        return sign + "0." + "0" * -n + d
    e = n - 1
    return sign + d[0] + ("." + d[1:] if k > 1 else "") + "e" + ("+" if e >= 0 else "-") + str(abs(e))


def string(s):
    out = []
    for ch in s:
        c = ord(ch)
        if ch in '"\\':
            out.append("\\" + ch)
        elif ch in "\b\t\n\f\r":
            out.append({"\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}[ch])
        elif c < 0x20:
            out.append("\\u%04x" % c)
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def canon(v):
    if v is None or isinstance(v, bool):
        return json.dumps(v)
    if isinstance(v, (int, float)):
        return number(float(v))
    if isinstance(v, str):
        return string(v)
    if isinstance(v, list):
        return "[" + ",".join(canon(x) for x in v) + "]"
    if isinstance(v, dict):
        keys = sorted(v, key=lambda k: k.encode("utf-16-be", "surrogatepass"))
        return "{" + ",".join(string(k) + ":" + canon(v[k]) for k in keys) + "}"
    raise ValueError(f"{type(v).__name__} has no JSON form")


def surrogates(s):
    """json.loads leaves an escaped surrogate pair as two code points; join them."""
    return s.encode("utf-16-be", "surrogatepass").decode("utf-16-be")


def fix(v):
    if isinstance(v, str):
        return surrogates(v)
    if isinstance(v, list):
        return [fix(x) for x in v]
    if isinstance(v, dict):
        return {surrogates(k): fix(x) for k, x in v.items()}
    return v


faults = []
try:
    vec = json.load(open(path, encoding="utf-8"))
except (OSError, ValueError) as e:
    print(f"{os.path.relpath(path, root)}: unreadable: {e}")
    sys.exit(1)
entries = vec.get("entries") or {}
if not entries:
    faults.append("no entries")
cases = 0
for key, e in entries.items():
    held = [k for k in ("cases", "see", "pending") if k in e]
    if len(held) != 1:
        faults.append(f"{key}: holds {held or 'none'} of cases, see and pending; want exactly one")
        continue
    if "see" in e and not os.path.isfile(os.path.join(root, e["see"])):
        faults.append(f"{key}: sees {e['see']}, which is no file of this repository")
    if "pending" in e and not e.get("why"):
        faults.append(f"{key}: pending on {e['pending']} with no why")
    for c in e.get("cases", []):
        cases += 1
        try:
            if "ieee754" in c:
                got = number(struct.unpack(">d", bytes.fromhex(c["ieee754"]))[0])
            else:
                got = canon(fix(json.loads(c["input"], parse_int=float)))
        except ValueError as err:
            faults.append(f"{key}: {c.get('id')}: {err}")
            continue
        if got != c["canonical"]:
            faults.append(f"{key}: {c.get('id')}: canonicalises to {got}, the vector says {c['canonical']}")
print("\n".join(faults) or f"types-vectors: {len(entries)} entries, {cases} canonical-json cases agree")
sys.exit(1 if faults else 0)
