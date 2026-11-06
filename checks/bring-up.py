#!/usr/bin/env python3
"""architecture/testing.md's bring_up block is data the engine can perform.

    checks/bring-up.py               the corpus's architecture/testing.md
    checks/bring-up.py --file F      F, read as architecture/testing.md

The block declares how a dependant's sealed run brings up the accepted builds
it needs running first ("Bringing up accepted dependencies"). It is refused
when:

- there is not exactly one bring_up block;
- hub.keys is not test_tokens' signed_by, or names no identity fixture: the
  harness mints every dependant's token with signed_by's key, and a hub
  started with another would refuse them all;
- operator names no identity fixture, or a step is made as one no fixture
  declares;
- a step is neither a read step nor an exchange step schemas/blocks'
  exchange-step admits;
- a read step's file is not a relative path inside the working directory,
  or its capture is not a name;
- a placeholder ${name} names nothing: not now, not a fixture, and no
  capture of an earlier step.
"""
import json, os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yaml  # noqa: E402
from families import Core, errors, yaml_blocks  # noqa: E402
from criterion_ids import CORPUS  # noqa: E402

BLOCKS = os.path.join(CORPUS, "schemas/blocks.md")
DEFS = yaml_blocks(BLOCKS)["defs"]
FENCE = re.compile(r"^```yaml\n(.*?)^```", re.S | re.M)
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
DURATION = re.compile(r"^[0-9]+(ms|s|m)$")
READ_KEYS = {"file", "capture", "within"}


def blocks(text, key):
    out = []
    for m in FENCE.finditer(text):
        try:
            v = yaml.load(m.group(1), Loader=Core)
        except yaml.YAMLError:
            continue
        if isinstance(v, dict) and key in v:
            out.append(v[key])
    return out


def judge(text):
    out = []
    fx = blocks(text, "fixtures")
    fixtures = fx[0] if len(fx) == 1 and isinstance(fx[0], dict) else {}
    identities = {k for k, v in fixtures.items() if isinstance(v, dict) and "seed" in v}
    tt = blocks(text, "test_tokens")
    signed_by = tt[0].get("signed_by") if len(tt) == 1 and isinstance(tt[0], dict) else None
    bu = blocks(text, "bring_up")
    if len(bu) != 1:
        return [f"architecture/testing: {len(bu)} bring_up blocks, where exactly one is declared"]
    b = bu[0]
    if not isinstance(b, dict):
        return ["architecture/testing: bring_up is not a mapping"]
    keys = (b.get("hub") or {}).get("keys") if isinstance(b.get("hub"), dict) else None
    if keys not in identities:
        out.append(f"bring_up: hub.keys {keys!r} names no identity fixture")
    elif keys != signed_by:
        out.append(f"bring_up: hub.keys {keys!r} is not test_tokens' signed_by {signed_by!r}, so no token the harness mints would verify at the hub")
    if b.get("operator") not in identities:
        out.append(f"bring_up: operator {b.get('operator')!r} names no identity fixture")
    steps = b.get("steps")
    if not isinstance(steps, list) or not steps:
        return out + ["bring_up: no steps"]
    captured = set()
    for i, st in enumerate(steps):
        where = f"bring_up step {i + 1} ({st.get('id', '?') if isinstance(st, dict) else '?'})"
        if not isinstance(st, dict):
            out.append(f"{where}: not a mapping")
            continue
        for name in re.findall(r"\$\{([^}]*)\}", json.dumps(st)):
            if name == "now" or name.startswith("fixture/"):
                fname = name.split("/")[1] if name.startswith("fixture/") else None
                if fname is not None and fname not in fixtures:
                    out.append(f"{where}: names fixture {fname!r}, which the fixtures block does not declare")
                continue
            if name not in captured:
                out.append(f"{where}: ${{{name}}} is captured by no earlier step")
        if "read" in st:
            r = st["read"]
            if set(st) - {"id", "read"} or not isinstance(r, dict) or set(r) - READ_KEYS:
                out.append(f"{where}: a read step holds only id and read, and read only {sorted(READ_KEYS)}")
                continue
            f = r.get("file")
            if not isinstance(f, str) or not f or f.startswith("/") or ".." in f.split("/"):
                out.append(f"{where}: read.file {f!r} is not a relative path inside the working directory")
            if not isinstance(r.get("capture"), str) or not NAME.match(r["capture"]):
                out.append(f"{where}: read.capture {r.get('capture')!r} is not a name")
            else:
                captured.add(r["capture"])
            if "within" in r and not (isinstance(r["within"], str) and DURATION.match(r["within"])):
                out.append(f"{where}: read.within {r['within']!r} is not a duration")
            continue
        bad = errors(st, DEFS["exchange-step"], BLOCKS)
        if bad:
            out.append(f"{where}: not an exchange step schemas/blocks admits, at {', '.join(p or '/' for p in bad)}")
        if "as" in st and st["as"] not in identities:
            out.append(f"{where}: made as {st['as']!r}, which no identity fixture declares")
        captured |= set((st.get("capture") or {}).keys())
    d = b.get("directory")
    if not isinstance(d, dict):
        out.append("bring_up: no directory, so no join check can read the orchestrator's view of a component")
    else:
        bad = errors(d.get("request"), DEFS["exchange-request"], BLOCKS)
        if bad:
            out.append(f"bring_up directory: its request is not one schemas/blocks admits, at {', '.join(p or '/' for p in bad)}")
        for k in ("entries", "name", "lease_state", "lease_expires_at"):
            if not (isinstance(d.get(k), str) and (d[k] == "" or d[k].startswith("/"))):
                out.append(f"bring_up directory: {k} is not a JSON pointer")
        if not (isinstance(d.get("current"), list) and d["current"]):
            out.append("bring_up directory: current names no lease state")
        for name in re.findall(r"\$\{([^}]*)\}", json.dumps(d)):
            if name != "now" and not name.startswith("fixture/") and name not in captured:
                out.append(f"bring_up directory: ${{{name}}} is captured by no step")
    return out


def main(argv):
    path = argv[argv.index("--file") + 1] if "--file" in argv else os.path.join(CORPUS, "architecture/testing.md")
    out = judge(open(path, encoding="utf-8").read())
    for line in out:
        print(line)
    if out:
        return 1
    print("bring-up: the bring_up block is data the engine can perform")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
