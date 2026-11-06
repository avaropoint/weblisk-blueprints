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
- `applies_to` or `except` names neither a component kind nor a selector, or
  `except` is written without `applies_to`;
- a `drive` check is addressed to anything but a client kind, or any other
  check to a client kind (schemas/kinds.md, "Client kinds");
- a placeholder is none the vocabulary declares (schemas/blocks.md, "Checks"):
  a capture the check makes, a fixture, `self`, `stood`, `address`,
  `harness/source`, `now` and its offsets, `token`, `instance`, `body`,
  `request` or a vector entry;
- a stood service it names (`${stood/<name>/...}`, `received.at`, an act
  `remote`) is not one the check stands up, or a field it reads is not one
  that service's role answers, or a fixture the check starts with reads a
  stood service the check does not stand up;
- `start.keys`, a signing `key`, an act's `fixture`, `start.files` or
  `place` names a fixture of the wrong form, or none;
- a token's or a `token_alter`'s signature is not a form test_tokens'
  `signature_forms` declares;
- a step sent `from: probe` is in a check that starts no probe, or the probe
  is started as an identity with no manifest;
- a declared check's assertion says it leaves part of what it covers
  unsettled (`check-proves-whole-criterion`): such a check covers a narrower
  criterion, or none.

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
from families import Core, errors, yaml_blocks, text_of  # noqa: E402
from criterion_ids import DIRS, CORPUS  # noqa: E402

BLOCKS = os.path.join(CORPUS, "schemas/blocks.md")
DEFS = yaml_blocks(BLOCKS)["defs"]
COMPONENT_KINDS = list(DEFS["check-kind-component"]["enum"])
CLIENT_KINDS = list(DEFS["check-kind-client"]["enum"])
CORPUS_KINDS = list(DEFS["check-kind-corpus"]["enum"])
DATA_KEYS = [k for k in COMPONENT_KINDS + CLIENT_KINDS if k != "translated"]
# What each harness role is reached at (architecture/testing.md, "Harness roles").
ROLE_FIELDS = {"responder": {"address", "certificate"}, "git-remote": {"root", "host_key"}}
# The placeholder heads schemas/blocks.md's Checks section declares, besides a capture's name.
PLACEHOLDER = re.compile(r"\$\{([^}]*)\}")
FIXED_HEADS = re.compile(r"^(now([+-][0-9]+[smhd])?|token|instance|address(/[a-z0-9-]+)?|harness/source|(self|body|request|v|registration)(/.*)?|(fixture|stood)/.+)$")
# Words with which an assertion says it settles only part of what it covers.
PARTIAL = re.compile(r"\b(is not settled here|not settled by this check|does not check|never checks|is not checked here)\b", re.I)
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


FIXTURE_BLOCK = yaml_blocks(os.path.join(CORPUS, "architecture/testing.md")).get("fixtures") or {}


def fixtures():
    """(identities, every fixture name): from architecture/testing.md's fixtures block."""
    b = FIXTURE_BLOCK
    ids = {k for k, v in b.items() if isinstance(v, dict) and "seed" in v}
    return ids | {"anonymous"}, set(b)


def key_fixtures():
    """Fixtures whose value is a key file (architecture/testing.md, "Key fixtures")."""
    return {k for k, v in FIXTURE_BLOCK.items() if isinstance(v, dict) and isinstance(v.get("key"), dict)}


def manifest_identities():
    return {k for k, v in FIXTURE_BLOCK.items() if isinstance(v, dict) and "seed" in v and isinstance(v.get("manifest"), dict)}


def signature_forms():
    """The signature forms architecture/testing.md's test_tokens block declares."""
    for m in FENCE.finditer(text_of(os.path.join(CORPUS, "architecture/testing.md"))):
        try:
            v = yaml.load(m.group(1), Loader=Core)
        except yaml.YAMLError:
            continue
        if isinstance(v, dict) and isinstance(v.get("test_tokens"), dict):
            return set((v["test_tokens"].get("signature_forms") or {}).keys())
    return set()


def component_selectors(block="component_kinds"):
    """Kinds and selectors one block of schemas/kinds.md declares, or None before it declares any."""
    b = yaml_blocks(os.path.join(CORPUS, "schemas/kinds.md")).get(block)
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


QUERIES, SELECTORS, CLIENTS = queries(), component_selectors(), component_selectors("client_kinds") or set()
FIXTURES, FIXTURE_NAMES = fixtures()
KEY_FIXTURES, MANIFESTS, SIGNATURE_FORMS = key_fixtures(), manifest_identities(), signature_forms()


def steps_of(entry):
    """Every exchange step a check carries, wherever its kind keeps them: an act send's among them."""
    for k in DATA_KEYS:
        d = entry.get(k)
        if not isinstance(d, dict):
            continue
        for s in d.get("steps") or []:
            yield s
        if isinstance(d.get("step"), dict):
            yield d["step"]
        for a in d.get("acts") or []:
            if isinstance(a, dict) and isinstance(a.get("step"), dict):
                yield a["step"]


def walk(x):
    """Every mapping in a value, depth first."""
    stack = [x]
    while stack:
        v = stack.pop()
        if isinstance(v, dict):
            yield v
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)


def starts_of(entry):
    """Every check-start-like mapping a check carries, and the stood services it stands up."""
    starts, stood = [], {}
    for k in DATA_KEYS:
        d = entry.get(k)
        if not isinstance(d, dict):
            continue
        if isinstance(d.get("start"), dict):
            starts.append(d["start"])
        if k == "drive":
            starts.append(d)
        if k == "topology":
            starts += [i for i in d.get("instances") or [] if isinstance(i, dict)]
    for st in starts:
        for n, sv in (st.get("stand_up") or {}).items():
            if isinstance(sv, dict):
                stood[n] = sv.get("role")
    return starts, stood


def captures_of(entry):
    """Every name a check captures: a step's capture, an operator's or an act's."""
    out = set()
    for m in walk(entry):
        if isinstance(m.get("capture"), dict):
            out |= set(m["capture"])
        elif isinstance(m.get("capture"), str):
            out.add(m["capture"])
    return out


def vocabulary(where, entry):
    """The rules of the vocabulary schemas/blocks.md 1.6.0 added, beyond the schema."""
    out = []
    starts, stood = starts_of(entry)
    caps = captures_of(entry)
    for ph in sorted(set(PLACEHOLDER.findall(json.dumps(entry)))):
        if ph not in caps and not FIXED_HEADS.match(ph):
            out.append(f"{where}: placeholder ${{{ph}}} is neither a capture the check makes nor one schemas/blocks declares")
            continue
        if ph.startswith("stood/"):
            parts = ph.split("/")
            if len(parts) < 3 or parts[1] not in stood:
                out.append(f"{where}: reads ${{{ph}}}, and the check stands up no service {parts[1]!r}")
            elif parts[2] not in ROLE_FIELDS.get(stood[parts[1]], set()):
                out.append(f"{where}: reads ${{{ph}}}, and a {stood[parts[1]]} answers no field {parts[2]!r}")
    for m in walk(entry):
        if isinstance(m.get("service"), str):
            if m["service"] not in ("orchestrator", "mock-agent") and m["service"] not in stood:
                out.append(f"{where}: received by {m['service']!r}, which is neither a mock nor a service the check stands up")
        if m.get("act") == "remote" and m.get("remote") not in stood:
            out.append(f"{where}: act remote on {m.get('remote')!r}, which the check does not stand up")
        if m.get("act") == "remote" and stood.get(m.get("remote")) not in (None, "git-remote"):
            out.append(f"{where}: act remote on {m.get('remote')!r}, which is no git-remote")
        if m.get("act") == "rotate-key" and m.get("fixture") not in KEY_FIXTURES:
            out.append(f"{where}: act rotate-key to {m.get('fixture')!r}, which is no key fixture")
        if m.get("act") == "place" and m.get("fixture") not in FIXTURE_NAMES:
            out.append(f"{where}: act place of {m.get('fixture')!r}, which architecture/testing does not declare")
        sig = (m.get("token_alter") or {}).get("signature") if isinstance(m.get("token_alter"), dict) else None
        if sig is not None and sig not in SIGNATURE_FORMS:
            out.append(f"{where}: token_alter signature {sig!r}, which test_tokens' signature_forms does not declare")
        if isinstance(m.get("into"), str) and "key" in m and m["key"] not in (FIXTURES | KEY_FIXTURES) - {"anonymous"}:
            out.append(f"{where}: signs with key {m['key']!r}, which is neither an identity nor a key fixture")
    for st in starts:
        k = st.get("keys")
        if k is not None and k not in (FIXTURES | KEY_FIXTURES) - {"anonymous"}:
            out.append(f"{where}: starts with keys {k!r}, which is neither an identity nor a key fixture")
        for path, f in (st.get("files") or {}).items():
            if f not in FIXTURE_NAMES:
                out.append(f"{where}: places {f!r} at {path}, which architecture/testing does not declare")
        for f in [st.get("config")] + list((st.get("files") or {}).values()):
            for ph in PLACEHOLDER.findall(json.dumps(FIXTURE_BLOCK.get(f))) if f in FIXTURE_BLOCK else []:
                if ph.startswith("stood/") and ph.split("/")[1] not in stood:
                    out.append(f"{where}: starts with fixture {f!r}, which reads ${{{ph}}}, and the check stands up no service {ph.split('/')[1]!r}")
        pr = st.get("probe")
        if isinstance(pr, dict) and pr.get("as") not in MANIFESTS:
            out.append(f"{where}: starts the probe as {pr.get('as')!r}, which is no identity fixture with a manifest")
    probed = any(isinstance(st.get("probe"), dict) for st in starts)
    for stp in steps_of(entry):
        if isinstance(stp, dict) and stp.get("from") == "probe" and not probed:
            out.append(f"{where}: a step sent from the probe, and the check starts no probe")
    if entry.get("check", "translated") != "translated" and PARTIAL.search(entry.get("assertion") or ""):
        out.append(f"{where}: its assertion leaves part of what it covers unsettled, so it does not cover it (check-proves-whole-criterion)")
    return out


def judge(rel, line, entry, own_parts):
    where = f"{rel}:{line}: check {entry.get('id', '?')!r}"
    out = []
    bad = errors(entry, DEFS["check"], BLOCKS)
    if bad:
        out.append(f"{where}: does not satisfy the check definition at {', '.join(sorted(set(b or '/' for b in bad)))}")
    kind = entry.get("check", "translated")
    if kind not in COMPONENT_KINDS + CLIENT_KINDS + CORPUS_KINDS:
        out.append(f"{where}: kind {kind!r} is not in schemas/blocks' check-kind")
    for k in DATA_KEYS:
        if k in entry and k != kind:
            out.append(f"{where}: carries {k!r} data but its kind is {kind!r}")
    if kind in CORPUS_KINDS:
        for k in ("live", "applies_to", "except"):
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
        for field in ("applies_to", "except"):
            for a in entry.get(field) or []:
                if kind in CLIENT_KINDS and a not in CLIENTS:
                    out.append(f"{where}: a {kind} check {field} {a!r}, which schemas/kinds declares as no client kind")
                elif kind not in CLIENT_KINDS and a in CLIENTS:
                    out.append(f"{where}: {field} the client kind {a!r}, and only a drive check is run against a client")
                elif a not in SELECTORS and a not in CLIENTS:
                    out.append(f"{where}: {field} {a!r}, which schemas/kinds declares as neither a component kind nor a selector")
    return out + vocabulary(where, entry)


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
    forms = set((b.get("signature_forms") or {}).keys())
    for k, e in sorted(b["tokens"].items()):
        if isinstance(e, dict) and e.get("from") is not None and e["from"] not in got:
            out.append(f"{rel}: token {k!r} is from {e['from']!r}, which test_tokens does not declare")
        if isinstance(e, dict) and e.get("signature") is not None and e["signature"] not in forms:
            out.append(f"{rel}: token {k!r} has signature {e['signature']!r}, which test_tokens' signature_forms does not declare")
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
    out, n, kinds = suite(rel, text) + serves_auth(rel, text), 0, {}
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
    for k in COMPONENT_KINDS + CLIENT_KINDS:
        if k not in seen:
            faults.append(f"valid.yaml: no example of kind {k!r}")
    # One example of every construct the vocabulary declares: each operator,
    # act, harness role and signing form, read from schemas/blocks.md.
    text = json.dumps(valid["verifies"])
    want = {f"operator {o}": f'"{o}":' for o in DEFS["assertion-op"]["properties"]}
    want.update({f"act {a}": f'"act": "{a}"' for a in DEFS["topology-act"]["properties"]["act"]["enum"]})
    want.update({f"role {r}": f'"role": "{r}"' for r in DEFS["stood-service"]["properties"]["role"]["enum"]})
    for k in ("headers", "headers_lack", "empty", "frames", "received", "includes", "excludes", "length"):
        want[f"expectation {k}"] = f'"{k}":'
    for k in ("token_alter", "bearer", "websocket", "probe", "except", "lacks_text", "matches", "manifest", "files"):
        want[f"field {k}"] = f'"{k}":'
    want["fixed-form signing"] = '"form": "fixed-form"'
    want["capture @address"] = '"@address"'
    for name, needle in sorted(want.items()):
        if needle not in text:
            faults.append(f"valid.yaml: no example of {name}")
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
