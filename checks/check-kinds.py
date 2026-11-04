#!/usr/bin/env python3
"""Every declared check is data of a kind schemas/blocks.md declares.

    checks/check-kinds.py                  every verifies block in the directories that hold blueprints
    checks/check-kinds.py --file F --as R  one file, read from F, as if it were R
    checks/check-kinds.py --vectors [DIR]  vectors/check-kinds/ (or DIR): every valid entry passes,
                                           and every invalid one is reported with exactly its fault

Read from the corpus and nowhere else: the `check` definition and the closed
vocabulary `check-kind` (schemas/blocks.md, "Checks"), the structure queries
each language blueprint declares (schemas/language.md, "The structure block"),
the identity fixtures architecture/testing.md names, and the component kinds
and selectors schemas/kinds.md declares. A check is refused when:

- it does not satisfy the `check` definition (its kind's data included);
- its `check` is not in the vocabulary, or it carries the data of another kind;
- a corpus kind carries `live` or `applies_to`;
- a `covers` entry names a part its file does not declare (a wl:id, a
  wl:check, a requirement or a check);
- a structure check names a query no language declares;
- a vector check names a file that does not exist;
- a step is made `as` an identity no fixture declares;
- `applies_to` names neither a component kind nor a selector.
"""
import glob, json, os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yaml  # noqa: E402
from families import Core, errors, yaml_blocks, text_of  # noqa: E402
from criterion_ids import DIRS, CORPUS  # noqa: E402

BLOCKS = os.path.join(CORPUS, "schemas/blocks.md")
DEFS = yaml_blocks(BLOCKS)["defs"]
COMPONENT_KINDS = list(DEFS["check-kind-component"]["enum"])
CORPUS_KINDS = list(DEFS["check-kind-corpus"]["enum"])
DATA_KEYS = [k for k in COMPONENT_KINDS if k != "translated"]
FENCE = re.compile(r"^```yaml\n(.*?)^```", re.S | re.M)
PART = re.compile(r"<!--\s*wl:(?:id|check)\s+([a-z0-9-]+)")


def verifies_blocks(text):
    for m in FENCE.finditer(text):
        try:
            v = yaml.load(m.group(1), Loader=Core)
        except yaml.YAMLError:
            continue
        if isinstance(v, dict) and list(v) == ["verifies"]:
            yield text.count("\n", 0, m.start()) + 2, v["verifies"]


def parts_of(text):
    """Every part id a file declares: wl:id, wl:check, and requirements and verifies entries."""
    out = set(PART.findall(text))
    for m in FENCE.finditer(text):
        try:
            v = yaml.load(m.group(1), Loader=Core)
        except yaml.YAMLError:
            continue
        if isinstance(v, dict) and len(v) == 1 and list(v)[0] in ("requirements", "verifies"):
            out |= {e.get("id") for e in (list(v.values())[0] or []) if isinstance(e, dict)}
    return out


_parts = {}


def parts_in(rel):
    if rel not in _parts:
        p = os.path.join(CORPUS, rel + ".md")
        _parts[rel] = parts_of(text_of(p)) if os.path.isfile(p) else None
    return _parts[rel]


def queries():
    """Every structure query any language or platform declares."""
    out = set()
    for p in sorted(glob.glob(os.path.join(CORPUS, "languages/*.md")) + glob.glob(os.path.join(CORPUS, "platforms/*.md"))):
        s = yaml_blocks(p).get("structure")
        if isinstance(s, dict):
            out |= set((s.get("queries") or {}).keys())
    return out


def fixtures():
    t = text_of(os.path.join(CORPUS, "architecture/testing.md"))
    sec = re.search(r"^### Identity Fixtures\n(.*?)^### ", t, re.S | re.M).group(1)
    return set(re.findall(r'^\s+name: "([a-z0-9-]+)"', sec, re.M)) | {"anonymous"}


def component_selectors():
    """Component kinds and selectors schemas/kinds.md declares, or None before it declares any."""
    b = yaml_blocks(os.path.join(CORPUS, "schemas/kinds.md")).get("component_kinds")
    if not isinstance(b, dict):
        return None
    return set((b.get("kinds") or {}).keys()) | set((b.get("selectors") or {}).keys())


QUERIES, FIXTURES, SELECTORS = queries(), fixtures(), component_selectors()


def steps_of(entry):
    """Every exchange step a check carries, wherever its kind keeps them."""
    for k in DATA_KEYS:
        d = entry.get(k)
        if not isinstance(d, dict):
            continue
        for s in d.get("steps") or []:
            yield s
        if isinstance(d.get("step"), dict):
            yield d["step"]


def judge(rel, line, entry, own_parts):
    where = f"{rel}:{line}: check {entry.get('id', '?')!r}"
    out = []
    bad = errors(entry, DEFS["check"], BLOCKS)
    if bad:
        out.append(f"{where}: does not satisfy the check definition at {', '.join(sorted(set(b or '/' for b in bad)))}")
    kind = entry.get("check", "translated")
    if kind not in COMPONENT_KINDS + CORPUS_KINDS:
        out.append(f"{where}: kind {kind!r} is not in schemas/blocks' check-kind")
    for k in DATA_KEYS:
        if k in entry and k != kind:
            out.append(f"{where}: carries {k!r} data but its kind is {kind!r}")
    if kind in CORPUS_KINDS:
        for k in ("live", "applies_to"):
            if k in entry:
                out.append(f"{where}: {k!r} on a check of the corpus")
    for c in entry.get("covers") or []:
        if not isinstance(c, str):
            continue
        if ":" in c and "//" not in c:
            f, part = c.split(":", 1)
            known = parts_in(f)
            if known is None:
                out.append(f"{where}: covers {c!r}, and {f}.md does not exist")
            elif part not in known:
                out.append(f"{where}: covers {c!r}, which {f}.md does not declare")
        elif "/" not in c and "#" not in c and c not in own_parts:
            out.append(f"{where}: covers {c!r}, which this file does not declare")
    s = entry.get("structure") if kind == "structure" else None
    if isinstance(s, dict):
        for q in [s.get("query")] + ([s["expect"].get("subset_of")] if isinstance(s.get("expect"), dict) else []):
            if q and q not in QUERIES:
                out.append(f"{where}: names structure query {q!r}, which no language declares")
    v = entry.get("vector") if kind == "vector" else None
    if isinstance(v, dict) and isinstance(v.get("file"), str) and not os.path.isfile(os.path.join(CORPUS, v["file"])):
        out.append(f"{where}: names vector file {v['file']!r}, which does not exist")
    for st in steps_of(entry):
        if isinstance(st, dict) and "as" in st and st["as"] not in FIXTURES:
            out.append(f"{where}: a step made as {st['as']!r}, which no identity fixture declares")
    if SELECTORS is not None:
        for a in entry.get("applies_to") or []:
            if a not in SELECTORS:
                out.append(f"{where}: applies_to {a!r}, which schemas/kinds declares as neither a component kind nor a selector")
    return out


def judge_file(rel, text):
    out, n, kinds = [], 0, {}
    own = parts_of(text)
    for line, entries in verifies_blocks(text):
        for e in entries or []:
            if not isinstance(e, dict):
                out.append(f"{rel}:{line}: a verifies entry that is not a mapping")
                continue
            n += 1
            k = e.get("check", "translated")
            kinds[k] = kinds.get(k, 0) + 1
            out += judge(rel, line, e, own)
    return out, n, kinds


def language_blocks():
    """Each declared structure block is well formed."""
    out = []
    for p in sorted(glob.glob(os.path.join(CORPUS, "languages/*.md")) + glob.glob(os.path.join(CORPUS, "platforms/*.md"))):
        rel = os.path.relpath(p, CORPUS)
        s = yaml_blocks(p).get("structure")
        if s is None:
            continue
        if not isinstance(s.get("parser"), dict) or not {"grammar", "version"} <= set(s["parser"]):
            out.append(f"{rel}: structure block names no parser grammar and version")
        for name, q in (s.get("queries") or {}).items():
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
                out.append(f"{rel}: structure query {name!r} is not a part id")
            if not isinstance(q, dict) or not q.get("text") or not q.get("query"):
                out.append(f"{rel}: structure query {name!r} lacks its text or its query")
            elif "@value" not in q["query"] and "@unread" not in q["query"]:
                out.append(f"{rel}: structure query {name!r} captures no @value")
            if isinstance(q, dict) and "value" in q:
                try:
                    if re.compile(q["value"]).groups != 1:
                        out.append(f"{rel}: structure query {name!r}'s value has not exactly one group")
                except re.error:
                    out.append(f"{rel}: structure query {name!r}'s value does not compile")
    return out


def vectors(d):
    faults = []
    valid = yaml.safe_load(open(os.path.join(d, "valid.yaml"), encoding="utf-8"))
    for e in valid["verifies"]:
        faults += judge("valid.yaml", 0, e, set(valid.get("parts", [])))
    seen = {e.get("check", "translated") for e in valid["verifies"]}
    for k in COMPONENT_KINDS:
        if k not in seen:
            faults.append(f"valid.yaml: no example of kind {k!r}")
    inv = yaml.safe_load(open(os.path.join(d, "invalid.yaml"), encoding="utf-8"))
    for case in inv["cases"]:
        got = judge("invalid.yaml", 0, case["check"], set(inv.get("parts", [])))
        if len(got) != 1 or case["fault"] not in got[0]:
            faults.append(f"invalid.yaml: case {case['id']!r} wants exactly one fault naming {case['fault']!r}, got {got}")
    if not faults:
        print(f"check-kinds vectors: {len(valid['verifies'])} valid, {len(inv['cases'])} invalid, each as expected")
    return faults


def main(argv):
    if "--vectors" in argv:
        i = argv.index("--vectors")
        d = argv[i + 1] if len(argv) > i + 1 else os.path.join(CORPUS, "vectors/check-kinds")
        faults = vectors(d)
        print("\n".join(faults))
        sys.exit(1 if faults else 0)
    if "--file" in argv:
        path = argv[argv.index("--file") + 1]
        rel = argv[argv.index("--as") + 1] if "--as" in argv else path
        files = [(rel, path)]
    else:
        files = []
        for d in DIRS:
            for p in sorted(glob.glob(os.path.join(CORPUS, d, "**/*.md"), recursive=True)):
                files.append((os.path.relpath(p, CORPUS), p))
    faults, total, kinds, nfiles = language_blocks() if "--file" not in argv else [], 0, {}, 0
    for rel, path in files:
        f, n, k = judge_file(rel, text_of(path))
        faults += f
        total += n
        nfiles += bool(n)
        for a, b in k.items():
            kinds[a] = kinds.get(a, 0) + b
    if faults:
        print("\n".join(faults))
        sys.exit(1)
    print(f"check-kinds: {total} checks in {nfiles} files, each of a declared kind ("
          + ", ".join(f"{k} {kinds[k]}" for k in sorted(kinds)) + f"); {len(QUERIES)} structure queries declared")


if __name__ == "__main__":
    main(sys.argv[1:])
