#!/usr/bin/env python3
"""Every Resources block in the corpus, against schemas/resource.md.

    checks/resources.py                       every block in the corpus
    checks/resources.py --file F              the blocks in F alone; F's own
                                              types and operations join the
                                              corpus's
    checks/resources.py --file F --expect E   F must give exactly the findings
                                              E lists, and E must exercise
                                              every rule resource.md declares
    checks/resources.py --root DIR            read the corpus from DIR

A Resources block is a fenced yaml block whose root is `resources:`, or the
`resources:` key of a `declaration:` block (schemas/resource.md, "Where it is
declared"). The check keeps no copy of any rule: the rule ids, the shape's
keys, the closed vocabularies and the presentations' types are read from
schemas/resource.md; the kinds and the relations from schemas/kinds.md; the
capabilities from protocol/types.md's Capability section; every type from the
`types:` blocks of the corpus; and the operations a block may bind from its
own file's endpoint tables and `serves:` entries.

A finding is `<file>: <kind>: <rule id>: <what>`. Exit 0 when there is none
(or, with --expect, when the findings are exactly the expected ones), 1
otherwise, and 2 when something it must read cannot be read: a check that
cannot read its rules has refuted nothing.
"""
import argparse, glob, json, os, re, sys

try:
    import yaml
except ImportError:
    print("resources: PyYAML is required")
    sys.exit(2)

DIRS = ["agents", "architecture", "patterns", "protocol", "schemas"]
SCALAR_LIST = re.compile(r"^(\[\]|list|array)")


def blocks(text):
    """(line, parsed) for every fenced yaml block that parses."""
    out = []
    for m in re.finditer(r"^```yaml[^\n]*\n(.*?)^```", text, re.S | re.M):
        try:
            out.append((text[: m.start()].count("\n") + 1, yaml.safe_load(m.group(1))))
        except yaml.YAMLError:
            pass
    return out


def die(msg):
    print("resources: " + msg)
    sys.exit(2)


def read(root, rel):
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        die("cannot read " + rel)
    return open(p, encoding="utf-8").read()


def schema(root):
    """What schemas/resource.md declares: rules, shape keys, vocabularies."""
    text = read(root, "schemas/resource.md")
    got = {}
    for _, b in blocks(text):
        if not isinstance(b, dict):
            continue
        vocab = {"rules", "presentations", "operations", "reserved_verbs", "verb_name",
                 "in_flight", "lifecycle_events", "unavailable_reasons"}
        if set(b) <= vocab:
            got.update(b)
        if "resources" in b and isinstance(b["resources"], list) and b["resources"]:
            got["shape"] = b["resources"][0]
    missing = [k for k in ("rules", "presentations", "operations", "reserved_verbs", "verb_name",
                           "in_flight", "lifecycle_events", "unavailable_reasons", "shape") if k not in got]
    if missing:
        die("schemas/resource.md declares no " + ", ".join(missing))
    got["rule_ids"] = [r["id"] for r in got["rules"]]
    got["keys"] = set(got["shape"].keys())
    return got


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def names(cell):
    return [re.sub(r"[`*]", "", n).strip() for n in cell.split(",") if n.strip()]


def kinds(root):
    """Declared kinds, and the relation rows, from schemas/kinds.md."""
    text = read(root, "schemas/kinds.md")
    declared, relations, section = set(), [], None
    for line in text.split("\n"):
        if line.startswith("## "):
            section = line[3:].strip()
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        c = cells(line)
        if section == "Declared kinds" and c[0].startswith("`"):
            declared.add(c[0].strip("`"))
        if section == "Relations" and c[0].startswith("`") and len(c) >= 4:
            relations.append((names(c[0]), c[1], c[2]))
    if not declared or not relations:
        die("schemas/kinds.md declares no kinds or no relations")
    return declared, relations


def relation_allowed(rows, relation, frm, to):
    for rels, fcell, tcell in rows:
        if relation not in rels:
            continue
        fs, ts = names(fcell), names(tcell)
        from_ok = frm in fs or fcell.startswith("any")
        to_ok = to in ts or (tcell == "the same kind" and to == frm)
        if from_ok and to_ok:
            return True
    return False


def capabilities(root):
    text = read(root, "protocol/types.md")
    m = re.search(r"^### Capability\n(.*?)^### ", text, re.S | re.M)
    if not m:
        die("protocol/types.md has no Capability section")
    caps = set(re.findall(r"^- `([a-z]+:[a-z*]+)`", m.group(1), re.M))
    if not caps:
        die("protocol/types.md's Capability section lists no capability")
    return caps


def corpus_files(root):
    out = []
    for d in DIRS:
        out += sorted(glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True))
    return out


def types_in(text, index):
    for _, b in blocks(text):
        if isinstance(b, dict) and isinstance(b.get("types"), dict):
            for name, t in b["types"].items():
                if not isinstance(t, dict):
                    continue
                fields = t.get("fields")
                if isinstance(fields, list):
                    fields = {f.get("name"): f for f in fields if isinstance(f, dict)}
                if isinstance(fields, dict):
                    index.setdefault(name, fields)


def operations_in(text):
    ops = set()
    header = None
    for line in text.split("\n"):
        if line.startswith("|"):
            c = cells(line)
            if "Operation" in c:
                header = c.index("Operation")
                continue
            if line.startswith("|---") or line.startswith("| ---"):
                continue
            if header is not None and header < len(c):
                ops.add(c[header].strip("`"))
        else:
            header = None
    for _, b in blocks(text):
        if isinstance(b, dict):
            decl = b.get("declaration", b)
            for e in (decl.get("serves") or []) if isinstance(decl, dict) else []:
                if isinstance(e, dict) and e.get("operation"):
                    ops.add(e["operation"])
    return ops


def resource_blocks(text):
    out = []
    for line, b in blocks(text):
        if not isinstance(b, dict):
            continue
        if isinstance(b.get("resources"), list):
            out += [(line, r) for r in b["resources"]]
        decl = b.get("declaration")
        if isinstance(decl, dict) and isinstance(decl.get("resources"), list):
            out += [(line, r) for r in decl["resources"]]
    return out


def field_type(fdef):
    t = str(fdef.get("type", "")).strip()
    if SCALAR_LIST.match(t):
        return "list"
    return t


def enum_of(fdef):
    c = fdef.get("constraints") if isinstance(fdef.get("constraints"), dict) else {}
    return fdef.get("enum") or fdef.get("values") or c.get("enum")


def resolve(index, tname, path):
    """The field definition a dotted path names in tname, or None."""
    fields = index.get(tname)
    fdef = None
    for i, seg in enumerate(path.split(".")):
        if not isinstance(fields, dict) or seg not in fields:
            return None
        fdef = fields[seg]
        if not isinstance(fdef, dict):
            return None
        if i < len(path.split(".")) - 1:
            inner = re.sub(r"^\[\]", "", str(fdef.get("type", "")))
            fields = index.get(inner)
    return fdef


def check(rel, r, ctx):
    """Findings for one declared kind."""
    sch, declared, rels, caps, index, ops = ctx["schema"], ctx["kinds"], ctx["relations"], ctx["caps"], ctx["types"], ctx["ops"]
    kind = r.get("kind", "?") if isinstance(r, dict) else "?"
    found = []

    def f(rule, what):
        found.append((rel, kind, rule, what))

    if not isinstance(r, dict):
        f("resource-keys", "is not a mapping")
        return found
    if kind not in declared:
        f("resource-kind-declared", "schemas/kinds declares no kind %s" % kind)
    for k in ("kind", "owner", "type", "identity", "fields", "operations"):
        if k not in r:
            f("resource-keys", "has no %s" % k)
    for k in r:
        if k not in sch["keys"]:
            f("resource-keys", "uses %s, which the Shape does not name" % k)
    tname = r.get("type")
    for key in ("type", "list_type"):
        if key in r and r[key] not in index:
            f("resource-type-declared", "%s %s is declared by no types block" % (key, r[key]))
    known_type = tname in index

    ident = r.get("identity") or {}
    if not isinstance(ident, dict) or ident.get("form") not in ("minted", "declared-name") or (
            known_type and resolve(index, tname, str(ident.get("field"))) is None):
        f("resource-identity", "identity %s is not a field of %s with form minted or declared-name" % (ident, tname))

    pres = sch["presentations"]
    for fd in r.get("fields") or []:
        if not isinstance(fd, dict):
            f("resource-field-access", "a fields entry is not a mapping")
            continue
        name = str(fd.get("name"))
        fdef = resolve(index, tname, name) if known_type else {}
        if known_type and fdef is None:
            f("resource-field-of-type", "field %s is not a field of %s" % (name, tname))
            fdef = {}
        if fd.get("access") not in ("read-only", "create", "settable"):
            f("resource-field-access", "field %s has access %s" % (name, fd.get("access")))
        p = fd.get("present")
        if p is not None:
            if p not in pres:
                f("resource-presentation", "field %s is presented %s, which is no presentation" % (name, p))
            elif fdef and field_type(fdef) not in pres[p]["types"]:
                f("resource-presentation", "field %s of type %s cannot be presented %s" % (name, fdef.get("type"), p))
            elif p == "choice" and fdef and not enum_of(fdef):
                f("resource-presentation", "field %s is presented choice and declares no values" % name)
            elif p == "reference" and fd.get("kind") not in declared:
                f("resource-presentation", "field %s is a reference to %s, which is no declared kind" % (name, fd.get("kind")))
        if fd.get("sensitive"):
            if fd.get("access") in ("create", "settable") and p != "secret":
                f("resource-sensitive", "settable sensitive field %s is not presented secret" % name)
            if fd.get("access") == "read-only" and p is not None:
                f("resource-sensitive", "read-only sensitive field %s is presented %s" % (name, p))
        elif p == "secret":
            f("resource-sensitive", "field %s is presented secret and is not sensitive" % name)

    for rl in r.get("relations") or []:
        if known_type and isinstance(rl, dict) and resolve(index, tname, str(rl.get("field"))) is None:
            f("resource-field-of-type", "relation field %s is not a field of %s" % (rl.get("field"), tname))

    operations = r.get("operations") or {}
    if not isinstance(operations, dict):
        f("resource-operations-closed", "operations is not a mapping")
        operations = {}
    for op, od in operations.items():
        if op not in sch["operations"]:
            f("resource-operations-closed", "operation %s is not one of %s" % (op, sch["operations"]))
        od = od if isinstance(od, dict) else {}
        if od.get("capability") not in caps:
            f("resource-capability", "operation %s names capability %s" % (op, od.get("capability")))
        if "binds" in od and od["binds"] not in ops:
            f("resource-binds", "operation %s binds %s, which this file declares no operation of" % (op, od["binds"]))
        if op == "list" and "binds" in od and not od.get("items"):
            f("resource-binds", "a bound list names no items")
        for flt in od.get("filters") or []:
            if known_type and resolve(index, r.get("list_type") or tname, str(flt)) is None and resolve(index, tname, str(flt)) is None:
                f("resource-field-of-type", "filter %s is not a field of %s" % (flt, tname))

    states = r.get("states")
    state_names, manual = set(), set()
    transitions = {}
    if states is not None:
        ok = isinstance(states, dict) and {"initial_state", "states", "transitions"} <= set(states)
        if ok:
            state_names = set(states["states"] or {})
            if states["initial_state"] not in state_names:
                ok = False
            for t in states["transitions"] or []:
                frm = t.get("from")
                frm = frm if isinstance(frm, list) else [frm]
                if not set(frm) <= state_names or t.get("to") not in state_names:
                    ok = False
                transitions[t.get("name")] = t
                if t.get("trigger") == "manual":
                    manual.add(t.get("name"))
        if not ok:
            f("resource-states", "states is not a machine whose every from, to and initial_state is declared")

    verbs = r.get("verbs") or []
    vnames = [v.get("name") for v in verbs if isinstance(v, dict)]
    fired = set()
    for v in verbs:
        if not isinstance(v, dict):
            f("resource-verb-complete", "a verb is not a mapping")
            continue
        n = v.get("name")
        if (not isinstance(n, str) or not re.fullmatch(sch["verb_name"], n) or n in sch["reserved_verbs"]
                or n in sch["operations"] or vnames.count(n) > 1):
            f("resource-verb-name", "verb %s" % n)
        if v.get("capability") not in caps:
            f("resource-capability", "verb %s names capability %s" % (n, v.get("capability")))
        if "binds" in v and v["binds"] not in ops:
            f("resource-binds", "verb %s binds %s, which this file declares no operation of" % (n, v["binds"]))
        inf = v.get("in_flight")
        rev = v.get("reversible")
        complete = (v.get("preconditions") and isinstance(inf, dict) and inf.get("handling") in sch["in_flight"]
                    and inf.get("says") and v.get("effect") and "reversible" in v
                    and (rev is False or (isinstance(rev, dict) and rev.get("by") in vnames and rev.get("by") != n)))
        if not complete:
            f("resource-verb-complete", "verb %s does not state every key, or states one outside its vocabulary" % n)
        if "transition" in v:
            fired.add(v["transition"])
            if v["transition"] not in manual:
                f("resource-transition", "verb %s fires %s, which is no manual transition of the kind's states" % (n, v["transition"]))
    for t in sorted(manual - fired):
        f("resource-transition", "manual transition %s is named by no verb" % t)

    allowed = set(sch["lifecycle_events"]) | set(vnames) | state_names
    for e in r.get("events") or []:
        if e not in allowed:
            f("resource-events", "event %s is no lifecycle event, verb or state of the kind" % e)

    for rl in r.get("relations") or []:
        rl = rl if isinstance(rl, dict) else {}
        if not relation_allowed(rels, rl.get("relation"), kind, rl.get("to")):
            f("resource-relation-declared", "schemas/kinds declares no %s from %s to %s" % (rl.get("relation"), kind, rl.get("to")))

    un = r.get("unavailable")
    if un is not None and not (isinstance(un, dict) and un.get("reason") == "owner-unspecified" and un.get("says")
                               and "owner-unspecified" in sch["unavailable_reasons"]):
        f("resource-unavailable", "unavailable %s" % un)
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))
    ap.add_argument("--file")
    ap.add_argument("--expect")
    a = ap.parse_args()
    root = a.root
    declared, relations = kinds(root)
    ctx = {"schema": schema(root), "kinds": declared, "relations": relations, "caps": capabilities(root), "types": {}}
    files = corpus_files(root)
    for p in files:
        types_in(open(p, encoding="utf-8").read(), ctx["types"])
    targets = [a.file] if a.file else [p for p in files if os.path.relpath(p, root) != os.path.join("schemas", "resource.md")]
    if a.file:
        if not os.path.exists(a.file):
            die("cannot read " + a.file)
        types_in(open(a.file, encoding="utf-8").read(), ctx["types"])
    findings, seen, nblocks = [], {}, 0
    for p in targets:
        text = open(p, encoding="utf-8").read()
        rel = os.path.relpath(p, root) if not a.file else os.path.basename(p)
        ctx["ops"] = operations_in(text)
        for line, r in resource_blocks(text):
            nblocks += 1
            findings += check(rel, r, ctx)
            k = r.get("kind") if isinstance(r, dict) else None
            if k in seen:
                findings.append((rel, k, "resource-kind-once", "also declared in %s" % seen[k]))
            else:
                seen[k] = rel
    if nblocks == 0:
        print("resources: no Resources block in %s" % (a.file or "the corpus"))
        return 1
    if a.expect:
        want = {(e["kind"], e["rule"]) for e in json.load(open(a.expect, encoding="utf-8"))["findings"]}
        got = {(k, rule) for _, k, rule, _ in findings}
        bad = 0
        for k, rule in sorted(got - want):
            print("unexpected: %s: %s" % (k, rule)); bad += 1
        for k, rule in sorted(want - got):
            print("missing: %s: %s" % (k, rule)); bad += 1
        for rule in ctx["schema"]["rule_ids"]:
            if rule not in {r for _, r in want}:
                print("unexercised: rule %s has no expected finding" % rule); bad += 1
        for _, rule in sorted(want):
            if rule not in ctx["schema"]["rule_ids"]:
                print("undeclared: %s is no rule schemas/resource.md declares" % rule); bad += 1
        if bad:
            return 1
        print("resources: %s gives exactly its %d expected findings, every rule exercised" % (a.file, len(want)))
        return 0
    for rel, k, rule, what in findings:
        print("%s: %s: %s: %s" % (rel, k, rule, what))
    for rule in {r for _, _, r, _ in findings}:
        if rule not in ctx["schema"]["rule_ids"]:
            die("a finding names %s, which schemas/resource.md does not declare" % rule)
    if findings:
        return 1
    print("resources: %d declared kinds in %d file(s), every one well formed" % (nblocks, len(set(seen.values()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
