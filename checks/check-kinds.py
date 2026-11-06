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
- a step is made `as` an identity no fixture declares, or a placeholder names
  a fixture architecture/testing.md's fixtures block does not declare;
- `applies_to` names neither a component kind nor a selector.

A block the engine reads checks or fixtures from (`verifies`, `fixtures`,
`test_tokens`) is refused, naming its file and line, where it uses a YAML
feature the engine's grammar refuses (schemas/family.md, json-data-model):
an anchor, an alias, a tag, a merge key or a second document, or a key
written twice. The engine refuses such a block whole, so every check in it
would otherwise be read as none.

Every endpoint a file serves (a declaration's `serves` list, or a `serves`
block's `http`) names its `auth` in the closed vocabulary `endpoint-auth`:
`none`, `identity`, `token`, or a capability protocol/types' Capability
section lists (schemas/blocks.md, "Which endpoints are protected").
"""
import glob, json, os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import yaml  # noqa: E402
from families import Core, errors, yaml_blocks, text_of, yaml_feature  # noqa: E402
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


# The blocks the engine reads checks and fixtures from.
CHECK_BLOCKS = ("verifies", "fixtures", "test_tokens")
ROOT_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):")


class _Unique(Core):
    """Core, refusing a key written twice in one mapping, as the engine's grammar does."""


def _unique_mapping(loader, node, deep=False):
    seen = set()
    for k, _ in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"a key written twice, {key!r}", k.start_mark)
        seen.add(key)
    return Core.construct_mapping(loader, node, deep)


_Unique.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def refused_blocks(rel, text):
    """Each block of checks or fixtures the engine's YAML grammar would refuse, with why."""
    out = []
    for m in FENCE.finditer(text):
        src = m.group(1)
        first = next((ln for ln in src.split("\n") if ln.strip() and not ln.strip().startswith("#")), "")
        k = ROOT_KEY.match(first)
        if not k or k.group(1) not in CHECK_BLOCKS:
            continue
        line = text.count("\n", 0, m.start()) + 2
        why = None
        try:
            f = yaml_feature(src)
            if f:
                why = f"a YAML {f}"
            else:
                yaml.load(src, Loader=_Unique)
        except yaml.YAMLError as e:
            why = str(e).splitlines()[0] if "written twice" not in str(e) else next(
                ln for ln in str(e).splitlines() if "written twice" in ln)
        if why:
            out.append(f"{rel}:{line}: the {k.group(1)} block uses {why}, which the engine's YAML grammar refuses "
                       f"(schemas/family json-data-model), so none of what it declares would be read")
    return out


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
    """(identities, every fixture name): from architecture/testing.md's fixtures block."""
    b = yaml_blocks(os.path.join(CORPUS, "architecture/testing.md")).get("fixtures") or {}
    ids = {k for k, v in b.items() if isinstance(v, dict) and "seed" in v}
    return ids | {"anonymous"}, set(b)


def component_selectors():
    """Component kinds and selectors schemas/kinds.md declares, or None before it declares any."""
    b = yaml_blocks(os.path.join(CORPUS, "schemas/kinds.md")).get("component_kinds")
    if not isinstance(b, dict):
        return None
    return set((b.get("kinds") or {}).keys()) | set((b.get("selectors") or {}).keys())


def capabilities():
    """Every capability name protocol/types.md's Capability section lists."""
    text = text_of(os.path.join(CORPUS, "protocol/types.md"))
    m = re.search(r"^### Capability\n(.*?)^### ", text, re.S | re.M)
    return set(re.findall(r"^- `([a-z]+:[a-z*]+)`", m.group(1), re.M)) if m else set()


AUTH_WORDS = set(DEFS["endpoint-auth"]["anyOf"][0]["enum"])
CAPABILITIES = capabilities()


def serves_auth(rel, text):
    """Each served endpoint's auth is a word of endpoint-auth or a declared capability."""
    out = []
    for m in FENCE.finditer(text):
        try:
            v = yaml.load(m.group(1), Loader=Core)
        except yaml.YAMLError:
            continue
        line = text.count("\n", 0, m.start()) + 2
        stack = [v]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack.extend(x)
                continue
            if not isinstance(x, dict):
                continue
            stack.extend(x.values())
            if not isinstance(x.get("serves"), list):
                continue
            for e in x["serves"]:
                if not isinstance(e, dict):
                    continue
                http = e.get("http") if isinstance(e.get("http"), dict) else e
                if "auth" not in http:
                    continue
                a = http["auth"]
                if a not in AUTH_WORDS and a not in CAPABILITIES:
                    name = e.get("operation") or e.get("id") or http.get("path")
                    out.append(f"{rel}:{line}: endpoint {name!r} has auth {a!r}, which is neither a word of endpoint-auth nor a capability protocol/types lists")
    return out


QUERIES, SELECTORS = queries(), component_selectors()
FIXTURES, FIXTURE_NAMES = fixtures()


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
    for name in re.findall(r"\$\{fixture/([a-z0-9-]+)", json.dumps(entry)):
        if name not in FIXTURE_NAMES:
            out.append(f"{where}: names fixture {name!r}, which architecture/testing does not declare")
    if SELECTORS is not None:
        for a in entry.get("applies_to") or []:
            if a not in SELECTORS:
                out.append(f"{where}: applies_to {a!r}, which schemas/kinds declares as neither a component kind nor a selector")
    return out


def test_tokens(rel, text):
    """architecture/testing.md: test_tokens declares exactly the minted values of exchange-request's token."""
    want = set(DEFS["exchange-request"]["properties"]["token"]["enum"]) - {"none", "captured"}
    b = None
    for m in FENCE.finditer(text):
        try:
            v = yaml.load(m.group(1), Loader=Core)
        except yaml.YAMLError:
            continue
        if isinstance(v, dict) and "test_tokens" in v:
            b = v["test_tokens"]
    if not isinstance(b, dict) or not isinstance(b.get("tokens"), dict):
        return [f"{rel}: no test_tokens block declaring the tokens a step may name"]
    got, out = set(b["tokens"]), []
    if b.get("signed_by") not in FIXTURES:
        out.append(f"{rel}: test_tokens are signed by {b.get('signed_by')!r}, which no identity fixture declares")
    out += [f"{rel}: token {k!r} is a value of exchange-request's token and test_tokens does not declare it" for k in sorted(want - got)]
    out += [f"{rel}: test_tokens declares {k!r}, which is no value of exchange-request's token" for k in sorted(got - want)]
    for k, e in sorted(b["tokens"].items()):
        if isinstance(e, dict) and e.get("from") is not None and e["from"] not in got:
            out.append(f"{rel}: token {k!r} is from {e['from']!r}, which test_tokens does not declare")
    return out


def suite(rel, text):
    """architecture/testing.md: every conformance test heading has its check, and every minted token is declared."""
    if rel != "architecture/testing.md":
        return []
    tokens = test_tokens(rel, text)
    tests = re.findall(r"^#### (L[0-9]-[0-9]{2}):", text, re.M)
    ids = {e.get("id", "") for _, es in verifies_blocks(text) for e in es or [] if isinstance(e, dict)}
    out = [f"{rel}: conformance test {tid} has no check in the suite's data"
           for tid in tests if not any(i.startswith(tid.lower() + "-") for i in ids)]
    if not tests:
        out.append(f"{rel}: no conformance test headings found")
    return out + tokens


def judge_file(rel, text):
    out, n, kinds = refused_blocks(rel, text) + suite(rel, text) + serves_auth(rel, text), 0, {}
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
