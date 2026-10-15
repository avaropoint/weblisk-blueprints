#!/usr/bin/env python3
"""The id grammar of schemas/names.md, checked against vectors/ids.json.
An implementation outside every Weblisk tool. --stub swaps the parser for one
that accepts everything; it must be reported on every invalid vector."""
import json, os, re, sys
import yaml  # PyYAML: the round-trip is the claim, so without it this check cannot run

SEG, PART = r"[A-Za-z0-9_][A-Za-z0-9_.-]*", r"[A-Za-z0-9][A-Za-z0-9.()-]*"
REF = re.compile(rf"(?://(?P<namespace>[a-z][a-z0-9-]{{1,38}})/)?(?P<local>{SEG}(?:/{SEG})*)"
                 rf"(?::(?P<part>{PART}))?(?:#(?P<anchor>[a-z0-9][a-z0-9_-]*))?"
                 r"(?:@(?P<version>\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?))?")
YAML_WORDS = {"y", "yes", "n", "no", "true", "false", "on", "off", "null"}

def parse(ref, families):
    if not re.match(r"[A-Za-z]|//", ref): return None              # rule 1
    head, colon, rest = ref.partition(":")
    family = head if colon and head in families else None           # rule 2
    m = REF.fullmatch(rest if family else ref)
    if not m: return None
    if not family and m.group(0) == m["local"] and "/" not in ref and ref.lower() in YAML_WORDS: return None  # rule 3
    return {"family": family, **m.groupdict()}

def same_in_yaml(r):
    try: return all(yaml.safe_load(d) == w for d, w in ((f"- {r}", [r]), (f"[{r}]", [r]), (f"k: {r}", {"k": r})))
    except yaml.YAMLError: return False

def main():
    v = json.load(open(os.path.join(os.path.dirname(__file__), "..", "vectors", "ids.json")))
    p = (lambda r, f: dict.fromkeys(v["fields"])) if "--stub" in sys.argv else parse
    fams, faults = set(v["families"]), []
    for c in v["valid"]:
        got, want = p(c["ref"], fams), {k: c[k] for k in v["fields"]}
        if got != want: faults.append(f"valid {c['ref']!r}: parsed {got}, want {want}")
        if not same_in_yaml(c["ref"]): faults.append(f"valid {c['ref']!r}: does not read back from YAML")
    for c in v["invalid"]:
        if p(c["ref"], fams) is not None: faults.append(f"invalid {c['ref']!r} accepted ({c['why']})")
        if c.get("yaml_unsafe") and same_in_yaml(c["ref"]): faults.append(f"invalid {c['ref']!r} marked yaml_unsafe reads back from YAML")
    print("\n".join(faults) or f"ids: {len(v['valid'])} valid and {len(v['invalid'])} invalid vectors agree")
    sys.exit(1 if faults else 0)

if __name__ == "__main__":
    main()
