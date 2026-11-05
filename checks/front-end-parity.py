#!/usr/bin/env python3
"""The two front ends present one engine's operations (architecture/engine.md,
Parity). Replaces command-surface.py, whose check is its second leg.

1. The catalogue. architecture/engine.md's `operations:` block: no operation
   is listed twice, every executor is one schemas/change.md declares, every
   event type is one engine.md's Events declares, and every operation is
   driven by corpus files that exist, or says why it is not (`undriven`).
2. Today's CLI. architecture/cli.md's `command_surface:` block against the
   commands the CLI builds at the commit checks/cli-verbs.json names: the
   drift, each command specified and not built and each built and not
   specified, is exactly that file's expected_drift, and every row's executor
   is one schemas/change.md declares.
3. Parity (--parity). Each front end's manifest, at the commit
   checks/front-ends.json pins, lists the same operations as the other, and
   each operation is one of the catalogue's; every catalogue operation that is
   not a template is in each. A front end with no pinned manifest makes this
   leg NOT RUN (exit 3), never ok. --manifests A B compares two manifest files
   instead, which is how the control runs it.

   A manifest is read in either shape: entries carrying `operation`, as
   architecture/engine.md's manifest block writes it, or `noun` and `verb`, as
   the engine publishes it today; and either whole (Studio's operations route)
   or as the `operations` of `weblisk commands --json`, which carries its
   front-end-only commands beside them. --executors E,F (or the pins'
   `executors`) holds the leg to the operations of those executors, in the
   catalogue and in each manifest: a phase is done for the executors it
   covers (ENGINE_PLAN S1: local and tenant-api). With pinned manifests, what
   the leg finds is held to the pins' `expected_gaps`, exactly, as
   cli-verbs.json holds the CLI's drift: an entry leaves the list when its gap
   closes, and a new gap fails.

  front-end-parity.py [--root DIR]
  front-end-parity.py --parity [--manifests A.json B.json] [--executors E,F] [--root DIR]
"""
import json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
root = argv[argv.index("--root") + 1] if "--root" in argv else os.path.join(HERE, "..")


def read(rel):
    return open(os.path.join(root, rel), encoding="utf-8").read()


def executors():
    change = read("schemas/change.md")
    return set(re.findall(r"^\| `([a-z-]+)` \|", change.split("## Executors", 1)[1].split("\n## ", 1)[0], re.M))


def catalogue():
    """The operations block of architecture/engine.md, and the event types its
    Events section declares (both tables of the section)."""
    text = read("architecture/engine.md")
    blocks = [b for b in re.findall(r"^```yaml\n(.*?)^```", text, re.M | re.S) if b.startswith("operations:")]
    if len(blocks) != 1:
        print(f"architecture/engine.md has {len(blocks)} operations blocks; want exactly one")
        sys.exit(1)
    events = re.search(r"^### Events\n(.*?)(?=^### )", text, re.M | re.S).group(1)
    types = set(re.findall(r"^\| `([a-z-]+)` \|", events, re.M))
    return yaml.safe_load(blocks[0])["operations"], types


def check_catalogue():
    rows, types = catalogue()
    execs, faults, seen = executors(), [], {}
    for r in rows:
        for op in r["ops"]:
            if op in seen:
                faults.append(f"{op}: listed more than once in the catalogue")
            seen[op] = r
        ex = r.get("executor")
        for e in ex if isinstance(ex, list) else [ex]:
            if e not in execs:
                faults.append(f"{r['ops'][0]}: executor {e!r} is not one schemas/change.md declares")
        for t in r.get("events") or []:
            if t not in types:
                faults.append(f"{r['ops'][0]}: event type {t!r} is not one architecture/engine.md declares")
        drivers = r.get("driven_by") or []
        if not drivers and not r.get("undriven"):
            faults.append(f"{r['ops'][0]}: driven by nothing, and says no reason")
        for d in drivers:
            path = d if d.endswith(".md") else d + ".md"
            if not os.path.isfile(os.path.join(root, path)):
                faults.append(f"{r['ops'][0]}: driven by {d}, which is no file of the corpus")
    return seen, faults


def check_surface():
    text = read("architecture/cli.md")
    blocks = [b for b in re.findall(r"^```yaml\n(.*?)^```", text, re.M | re.S) if b.startswith("command_surface:")]
    if len(blocks) != 1:
        return [f"architecture/cli.md has {len(blocks)} command_surface blocks; want exactly one"], ""
    rows = yaml.safe_load(blocks[0])["command_surface"]
    execs, faults, spec = executors(), [], []
    for r in rows:
        spec.append(f"{r['noun']} {r['verb']}".strip())
        if r.get("executor") not in execs:
            faults.append(f"{spec[-1]}: executor {r.get('executor')!r} is not one schemas/change.md declares")
    cli = json.load(open(os.path.join(HERE, "cli-verbs.json"), encoding="utf-8"))
    built = [f"{c['noun']} {c['verb']}".strip() for c in cli["commands"]]
    for name, items in (("Command Surface", spec), (f"CLI {cli['cli_commit']}", built)):
        for d in sorted({i for i in items if items.count(i) > 1}):
            faults.append(f"{d}: listed more than once in the {name}")
    drift = [f"specified, not built: {c}" for c in sorted(set(spec) - set(built))] + \
            [f"built, not specified: {c}" for c in sorted(set(built) - set(spec))]
    print("\n".join(drift))
    want = cli["expected_drift"]
    if drift != want:
        for line in sorted(set(drift) - set(want)):
            faults.append(f"unexpected drift: {line}")
        for line in sorted(set(want) - set(drift)):
            faults.append(f"expected drift gone: {line}")
    return faults, f"{len(spec)} rows; the drift against CLI {cli['cli_commit']} is the {len(want)} expected"


def matches(op, template):
    a, b = op.split(), template.split()
    return len(a) == len(b) and all(t.startswith("<") and t.endswith(">") or t == w for w, t in zip(a, b))


def op_name(o):
    if o.get("operation"):
        return o["operation"]
    return f"{o['noun']} {o['verb']}".strip() if o.get("verb") else o["noun"]


def row_executors(row):
    ex = row.get("executor")
    return set(ex if isinstance(ex, list) else [ex])


def check_parity(ops):
    pins, expected = None, None
    if "--manifests" in argv:
        i = argv.index("--manifests")
        manifests = {os.path.basename(p): json.load(open(p, encoding="utf-8")) for p in argv[i + 1 : i + 3]}
    else:
        pins = json.load(open(os.path.join(HERE, "front-ends.json"), encoding="utf-8"))
        missing = [f for f, pin in pins["front_ends"].items() if not pin.get("manifest")]
        if missing:
            print(f"front-end-parity: NOT RUN: no manifest pinned for {', '.join(missing)} "
                  f"(checks/front-ends.json); parity cannot be said until each front end publishes one")
            sys.exit(3)
        manifests = {f: json.load(open(os.path.join(HERE, pin["manifest"]), encoding="utf-8"))
                     for f, pin in pins["front_ends"].items()}
        expected = pins.get("expected_gaps")
    scope = None
    if "--executors" in argv:
        scope = set(argv[argv.index("--executors") + 1].split(","))
    elif pins and pins.get("executors"):
        scope = set(pins["executors"])
    in_scope = {t: r for t, r in ops.items() if scope is None or row_executors(r) & scope}
    faults, sets = [], {}
    for name, m in manifests.items():
        entries = m["operations"] if "operations" in m else m["manifest"]["operations"]
        sets[name] = {op_name(o) for o in entries if scope is None or "executor" not in o or o["executor"] in scope}
        for o in sorted(sets[name]):
            if not any(matches(o, t) for t in ops):
                faults.append(f"{name}: {o} is not an operation of the catalogue")
        for t in sorted(in_scope):
            if "<" not in t and t not in sets[name]:
                faults.append(f"{name}: the catalogue's {t} is missing")
    names = sorted(sets)
    for a in names:
        for b in names:
            if a < b:
                for o in sorted(sets[a] - sets[b]):
                    faults.append(f"{a} has {o}, which {b} lacks")
                for o in sorted(sets[b] - sets[a]):
                    faults.append(f"{b} has {o}, which {a} lacks")
    if expected is None:
        return faults, ""
    print("\n".join(faults))
    held = []
    for line in sorted(set(faults) - set(expected)):
        held.append(f"unexpected gap: {line}")
    for line in sorted(set(expected) - set(faults)):
        held.append(f"expected gap gone: {line}")
    return held, f"the manifests agree with each other; their gaps from the catalogue{' for ' + ', '.join(sorted(scope)) if scope else ''} are the {len(expected)} expected (checks/front-ends.json)"


ops, faults = check_catalogue()
if "--parity" in argv:
    held, said = check_parity(ops)
    faults += held
    print("\n".join(faults) or f"front-end-parity: {len(ops)} catalogue operations; " + (said or "the manifests agree"))
    sys.exit(1 if faults else 0)
surface, said = check_surface()
faults += surface
print("\n".join(faults) or f"front-end-parity: the catalogue's {len(ops)} operations are well formed; the Command Surface has {said}")
sys.exit(1 if faults else 0)
