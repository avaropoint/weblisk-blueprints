#!/usr/bin/env python3
"""Component kinds and their cardinality are declared once, and agree with the
services table.

    checks/component-kinds.py [--kinds FILE] [--config FILE]

Reads the `component_kinds` block of schemas/kinds.md ("Component kinds") and
the services table of schemas/programme.md ("The services, in the order they
are built"). Holds that: every service the table names is a kind, and every
kind but agent, domain and gateway is a service the table names; every kind
has a count whose min is 0 or 1 and whose max, where given, is at least its
min; a runs_with names a kind that is itself declared and does not register;
`instances.max` is a positive integer; every selector's `where` names a
facet some kind holds; and schemas/config's `ports` block gives a port or a
range to every kind but one that runs with another, and to nothing that is
neither a kind nor `federation`.
"""
import os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from families import yaml_blocks, text_of  # noqa: E402

CORPUS = os.path.normpath(os.path.join(HERE, ".."))


def services():
    t = text_of(os.path.join(CORPUS, "schemas/programme.md"))
    sec = re.search(r"^### The services, in the order they are built\n(.*?)^### ", t, re.S | re.M).group(1)
    return {m.group(1) for m in re.finditer(r"^\| \d+ \| `([a-z][a-z0-9-]*)` \|", sec, re.M)}


def facet(kind, dotted):
    v = kind
    for k in dotted.split("."):
        if not isinstance(v, dict) or k not in v:
            return None
        v = v[k]
    return v


def main(argv):
    path = argv[argv.index("--kinds") + 1] if "--kinds" in argv else os.path.join(CORPUS, "schemas/kinds.md")
    block = yaml_blocks(path).get("component_kinds")
    if not isinstance(block, dict):
        print(f"{path}: no component_kinds block")
        sys.exit(1)
    kinds, faults = block.get("kinds") or {}, []
    table = services()
    for s in sorted(table - set(kinds)):
        faults.append(f"service {s!r} is in the services table and is no component kind")
    for k in sorted(set(kinds) - table):
        if not isinstance((kinds[k] or {}).get("blueprint"), str):
            faults.append(f"component kind {k!r} is no service of the services table and names no blueprint")
    for k in sorted(set(kinds) & table):
        if "blueprint" in (kinds[k] or {}):
            faults.append(f"component kind {k!r} names a blueprint, and the services table already names its own")
    for k, v in sorted(kinds.items()):
        c = (v or {}).get("count")
        if not isinstance(c, dict) or c.get("min") not in (0, 1):
            faults.append(f"component kind {k!r} has no count with a min of 0 or 1")
        elif "max" in c and (not isinstance(c["max"], int) or c["max"] < max(c["min"], 1)):
            faults.append(f"component kind {k!r} has a max below its min")
        if not isinstance((v or {}).get("registers"), bool):
            faults.append(f"component kind {k!r} does not say whether it registers")
        host = (v or {}).get("runs_with")
        if host is not None and (host not in kinds or kinds[host].get("registers")):
            faults.append(f"component kind {k!r} runs with {host!r}, which is not a declared kind that holds the directory")
    inst = (block.get("instances") or {}).get("max")
    if not isinstance(inst, int) or inst < 1:
        faults.append("instances.max is not a positive integer")
    for name, sel in sorted((block.get("selectors") or {}).items()):
        for key, want in ((sel or {}).get("where") or {}).items():
            if not any(facet(v, key) == want for v in kinds.values()):
                faults.append(f"selector {name!r} selects on {key} = {want!r}, which no kind holds")
    config = argv[argv.index("--config") + 1] if "--config" in argv else os.path.join(CORPUS, "schemas/config.md")
    ports = yaml_blocks(config).get("ports")
    if not isinstance(ports, list):
        faults.append("schemas/config.md has no ports block")
        ports = []
    listed = set()
    for row in ports:
        who = (row or {}).get("for")
        if who != "federation" and who not in kinds and who not in table:
            faults.append(f"schemas/config's ports block gives a port to {who!r}, which is no component kind")
        if not isinstance(row.get("port"), int) and not (isinstance(row.get("range"), list) and len(row["range"]) == 2):
            faults.append(f"schemas/config's ports row for {who!r} gives neither a port nor a range")
        listed.add(who)
    for k, v in sorted(kinds.items()):
        if k not in listed and not (v or {}).get("runs_with"):
            faults.append(f"component kind {k!r} listens on no port schemas/config's ports block gives")
    if faults:
        print("\n".join(faults))
        sys.exit(1)
    single = sorted(k for k, v in kinds.items() if v["count"].get("max") == 1)
    print(f"component-kinds: {len(kinds)} kinds agree with the services table; {len(single)} singletons "
          f"({', '.join(single)}); {inst} instance per component")


if __name__ == "__main__":
    main(sys.argv[1:])
