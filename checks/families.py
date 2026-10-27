#!/usr/bin/env python3
"""The findings a walk gives (schemas/family.md), for files of the families
named, read from each family's declaration and from schemas/blocks.md alone.
It gives findings only, never a projection's spans or digests, and it refuses
to judge what it does not implement: a declaration or a file using one is
reported as not judged, with exit 2, and never passes.

    checks/families.py FAMILY...             walk the files each family's match covers
    checks/families.py FAMILY --against FILE walk FAMILY's files against the declaration in FILE
    checks/families.py FAMILY --file PATH... walk PATH against FAMILY
    checks/families.py --templates FAMILY... walk each family's template against it
    checks/families.py --vectors             every grammar vector against its projection's findings
    checks/families.py --strict MIGRATION STRICT
        STRICT is MIGRATION with every header.legacy key refused and every
        header.required key required, one major on, and nothing else changed
    --resolve KEY DIR   also: every walked header's KEY (a dotted path) names DIR/<value>.md, a declaration
    --distinct          also: no heading or alias, ignoring case, opens two of a family's slots
    --counts            print each code and subject with its count, not each finding
Exits 0 when no finding is refused, 1 when one is or a fault is found, 2 when
something could not be judged."""
import collections, glob, json, os, re, sys
import yaml  # PyYAML

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ids import parse as parse_ref  # noqa: E402  the one parser of the id grammar here

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FAMILY = "schemas/family@1"


class NotJudged(Exception):
    pass


# The YAML 1.2 core schema, as json-data-model reads a header or a block: an
# unquoted date stays a string, and only true and false are booleans.
class Core(yaml.SafeLoader):
    pass


Core.yaml_implicit_resolvers = {
    k: [(t, r) for t, r in v if t not in ("tag:yaml.org,2002:timestamp", "tag:yaml.org,2002:bool")]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
Core.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF"))


def yaml_feature(text):
    """The first anchor, alias, tag, merge key or second document, or None."""
    docs = 0
    for ev in yaml.parse(text, Loader=Core):
        if isinstance(ev, yaml.DocumentStartEvent):
            docs += 1
            if docs > 1: return "document"
        if isinstance(ev, yaml.AliasEvent): return "alias"
        if getattr(ev, "anchor", None): return "anchor"
        if getattr(ev, "tag", None): return "tag"
        if isinstance(ev, yaml.ScalarEvent) and ev.value == "<<" and ev.style is None: return "merge-key"
    return None


def read_yaml(text):
    """(value, refusal): refusal is ('yaml-feature', subject) or ('unparsed', None)."""
    try:
        f = yaml_feature(text)
        if f: return None, ("yaml-feature", f)
        return yaml.load(text, Loader=Core), None
    except yaml.YAMLError:
        return None, ("unparsed", None)


def text_of(path):
    return open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")


def yaml_blocks(path):
    out = {}
    for m in re.finditer(r"^```yaml\n(.*?)^```", text_of(path), re.S | re.M):
        v = yaml.safe_load(m.group(1))
        if isinstance(v, dict) and len(v) == 1: out.update(v)
    return out


def front(path):
    t = text_of(path)
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    return yaml.safe_load(m.group(1)) if m else None


def is_declaration(path):
    h = front(path) if path.endswith(".md") and os.path.isfile(path) else None
    return isinstance(h, dict) and h.get("family") == FAMILY


# What a ref may name: every kind schemas/kinds.md declares, and the families
# schemas/names.md's declaration adds (as checks/names.py reads them).
def ref_families():
    kinds = text_of(os.path.join(ROOT, "schemas/kinds.md"))
    sec = re.search(r"^## Declared kinds\n(.*?)(?=^## )", kinds, re.S | re.M).group(1)
    names = text_of(os.path.join(ROOT, "schemas/names.md"))
    decl = yaml.safe_load(re.search(r"^## Declaration\n+```yaml\n(.*?)```", names, re.S | re.M).group(1))
    return set(re.findall(r"^\| `([a-z][a-z0-9-]*)` \|", sec, re.M)) | set(decl["families"])


FAMILIES = ref_families()
VERSION = r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?"
SCALARS = None  # schemas/blocks' `scalar`, read on first use


def type_expr(s):
    global SCALARS
    if SCALARS is None:
        SCALARS = set(yaml_blocks(os.path.join(ROOT, "schemas/blocks.md"))["defs"]["scalar"]["enum"])
    if s in SCALARS: return True
    m = re.fullmatch(r"(list|map)<(.*)>", s)
    if m: return type_expr(m.group(2))
    return s.startswith("ref:") and parse_ref(s[4:], FAMILIES) is not None


FORMATS = {
    "weblisk-ref": lambda s: parse_ref(s, FAMILIES) is not None,
    "weblisk-version": lambda s: re.fullmatch(VERSION, s) is not None,
    "weblisk-citation": lambda s: "@" in s and parse_ref(s.rsplit("@", 1)[0], FAMILIES) is not None
        and re.fullmatch(VERSION, s.rsplit("@", 1)[1]) is not None,
    "weblisk-family-ref": lambda s: re.fullmatch(r"(.+)@\d+", s) is not None
        and parse_ref(s.rsplit("@", 1)[0], FAMILIES) is not None,
    "version-range": lambda s: re.fullmatch(rf"(?:(?:>=|<=|>|<|=)?{VERSION})(?: (?:>=|<=|>|<|=)?{VERSION})*", s) is not None,
    "type-expr": type_expr,
    "glob": lambda s: True,
    "date": lambda s: re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) is not None,
}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
ANNOTATIONS = {"description", "default", "$comment", "examples"}
KEYWORDS = {"type", "enum", "const", "properties", "required", "unevaluatedProperties", "additionalProperties",
            "items", "minItems", "maxItems", "minLength", "pattern", "minimum", "maximum", "minProperties",
            "maxProperties", "propertyNames", "oneOf", "anyOf", "allOf", "if", "then", "else", "$ref", "format"} | ANNOTATIONS


def is_type(v, t):
    if t == "integer": return isinstance(v, int) and not isinstance(v, bool)
    if t == "number": return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t not in TYPES: raise NotJudged(f"type {t!r}")
    return isinstance(v, TYPES[t])


def resolve(ref, base):
    m = re.fullmatch(r"(?:([^#]+))?#/\$defs/([a-z][a-z0-9-]*)", ref)
    if not m: raise NotJudged(f"$ref {ref!r}")
    target = base if m.group(1) is None else os.path.join(ROOT, m.group(1) + ".md")
    defs = yaml_blocks(target).get("defs") or {}
    if m.group(2) not in defs: raise NotJudged(f"$ref {ref!r} resolves to nothing")
    return defs[m.group(2)], target


def errors(v, s, base, at=""):
    """The JSON pointers of the values in v that schema s refuses."""
    if s is True or s == {}: return []
    if s is False: return [at]
    unknown = set(s) - KEYWORDS
    if unknown: raise NotJudged(f"schema keyword {sorted(unknown)[0]!r}")
    out = []
    if "$ref" in s:
        sub, b = resolve(s["$ref"], base)
        out += errors(v, sub, b, at)
    if "type" in s:
        ts = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(is_type(v, t) for t in ts): return out + [at]
    if "enum" in s and v not in s["enum"]: out.append(at)
    if "const" in s and v != s["const"]: out.append(at)
    if "format" in s and isinstance(v, str):
        if s["format"] not in FORMATS: raise NotJudged(f"format {s['format']!r}")
        if not FORMATS[s["format"]](v): out.append(at)
    if isinstance(v, str):
        if "minLength" in s and len(v) < s["minLength"]: out.append(at)
        if "pattern" in s and not re.search(s["pattern"], v): out.append(at)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if "minimum" in s and v < s["minimum"]: out.append(at)
        if "maximum" in s and v > s["maximum"]: out.append(at)
    if isinstance(v, list):
        if "minItems" in s and len(v) < s["minItems"]: out.append(at)
        if "maxItems" in s and len(v) > s["maxItems"]: out.append(at)
        if "items" in s:
            for i, x in enumerate(v): out += errors(x, s["items"], base, f"{at}/{i}")
    if isinstance(v, dict):
        props = s.get("properties", {})
        for k in s.get("required", []):
            if k not in v: out.append(f"{at}/{k}")
        if "minProperties" in s and len(v) < s["minProperties"]: out.append(at)
        if "maxProperties" in s and len(v) > s["maxProperties"]: out.append(at)
        for k, x in v.items():
            if "propertyNames" in s and errors(k, s["propertyNames"], base, at): out.append(f"{at}/{k}")
            if k in props: out += errors(x, props[k], base, f"{at}/{k}")
            else:
                rest = s.get("unevaluatedProperties", s.get("additionalProperties", True))
                out += errors(x, rest, base, f"{at}/{k}")
    for key in ("allOf",):
        for sub in s.get(key, []): out += errors(v, sub, base, at)
    if "anyOf" in s and not any(not errors(v, sub, base, at) for sub in s["anyOf"]): out.append(at)
    if "oneOf" in s and sum(not errors(v, sub, base, at) for sub in s["oneOf"]) != 1: out.append(at)
    if "if" in s:
        branch = s.get("then") if not errors(v, s["if"], base, at) else s.get("else")
        if branch is not None: out += errors(v, branch, base, at)
    return out


# The older spellings blocks.md lists, of a type: each is read as what it names
# and reported. Older spellings of a field property are not judged here.
OLD_TYPES = None


def old_types():
    global OLD_TYPES
    if OLD_TYPES is None:
        sec = re.search(r"^### Older spellings\n(.*?)(?=^#)", text_of(os.path.join(ROOT, "schemas/blocks.md")), re.S | re.M).group(1)
        OLD_TYPES = {a: b for a, b in re.findall(r"^\| `([a-z0-9]+)` \| `([^`]+)` \|$", sec, re.M)}
    return OLD_TYPES


def respell_types(value, found):
    for t in (value or {}).values() if isinstance(value, dict) else []:
        for f in ((t or {}).get("fields") or {}).values() if isinstance(t, dict) else []:
            if not isinstance(f, dict): continue
            for prop in ("optional", "enum", "max_length", "constraints"):
                if prop in f: raise NotJudged(f"the older field property {prop!r}")
            ty = f.get("type")
            if isinstance(ty, str) and ty in old_types():
                found.append(ty)
                f["type"] = old_types()[ty]
            elif isinstance(ty, str) and re.fullmatch(r"\[\].+|.+\[\]|map\[string\].+|enum\(.*\)|[A-Z][A-Za-z0-9]*", ty):
                raise NotJudged(f"the older spelling {ty!r}")


# Lines, fences and comments (fences-are-opaque, headings-are-atx).
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^ {0,3}(#{1,2}) (.*)$")


def scan(body):
    """Events in the body: ('heading', level, text, line), ('fence', info, lines, line, closed),
    ('table', rows, line), ('text', line, raw) for any other non-blank line."""
    lines, i, out = body.split("\n"), 0, []
    while i < len(lines):
        ln = lines[i]
        m = FENCE.match(ln)
        if m:
            mark, j = m.group(1), i + 1
            while j < len(lines) and not re.fullmatch(rf" {{0,3}}{mark[0]}{{{len(mark)},}}\s*", lines[j]): j += 1
            out.append(("fence", m.group(2).strip(), lines[i + 1:j], i, j < len(lines)))
            i = j + 1
            continue
        if re.match(r"^ {0,3}<!--", ln):
            j = i
            while j < len(lines) and "-->" not in lines[j]: j += 1
            out.append(("comment", "\n".join(lines[i:j + 1]), i, j < len(lines)))
            i = j + 1
            continue
        h = HEADING.match(ln)
        if h:
            out.append(("heading", len(h.group(1)), " ".join(h.group(2).split()), i))
        elif ln.lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"): j += 1
            out.append(("table", lines[i:j], i))
            i = j
            continue
        elif ln.strip():
            out.append(("text", i, ln))
        i += 1
    return out


def cells(row):
    """A row's cells; a cell that is one code span is read as its text."""
    out = [c.strip() for c in row.strip().strip("|").split("|")]
    return [c[1:-1] if re.fullmatch(r"`[^`]+`", c) else c for c in out]


class Decl:
    def __init__(self, path):
        self.path = path
        self.head = front(path)
        b = yaml_blocks(path)
        if "header" not in b or "sections" not in b: raise NotJudged(f"{rel(path)} has no header or sections block")
        self.header, self.sections = b["header"], b["sections"]
        for s in self.sections["slots"]:
            for k in ("guidance", "authority"):
                s.pop(k, None)  # judged requirements: never a walk finding
            c = s.get("content") or {}
            for p in c:
                if p not in ("max_paragraphs", "no_rfc2119"): raise NotJudged(f"content predicate {p!r}")

    def slot_of(self, level, h):
        for n, s in enumerate(self.sections["slots"]):
            want = s["heading"]
            if level == 1: hit = isinstance(want, dict) and want.get("level") == 1
            else: hit = (isinstance(want, str) and " ".join(want.split()) == h) \
                or h in [" ".join(a.split()) for a in s.get("aliases", [])] \
                or (isinstance(want, dict) and "starts_with" in want and h.startswith(" ".join(want["starts_with"].split())))
            if hit: return n, s
        return None, None


CATALOGUE = None


def catalogue():
    global CATALOGUE
    if CATALOGUE is None: CATALOGUE = yaml_blocks(os.path.join(ROOT, "schemas/blocks.md"))["blocks"]
    return CATALOGUE


def walk(path, decl):
    """[(code, policy, subject)] for one file."""
    t = text_of(path)
    found = []
    add = lambda code, policy, subject=None: found.append((code, policy, subject))
    lines = t.split("\n")
    header, body = {}, t
    if lines[0] == "---":
        close = next((i for i in range(1, len(lines)) if lines[i] == "---"), None)
        if close is None: return [("header-unparsed", "refuse", None)]
        value, refused = read_yaml("\n".join(lines[1:close]) + "\n")
        if refused and refused[0] == "yaml-feature": return [("yaml-feature", "refuse", refused[1])]
        if refused or not isinstance(value, dict): return [("header-unparsed", "refuse", None)]
        header, body = value, "\n".join(lines[close + 1:])
    h = decl.header
    for key, policy in (h.get("legacy") or {}).items():  # legacy-before-schema
        node, parts = header, key.split(".")
        for p in parts[:-1]: node = node.get(p) if isinstance(node, dict) else None
        if isinstance(node, dict) and parts[-1] in node:
            del node[parts[-1]]
            add("legacy-key", policy, key)
    for key in (h.get("required") or {}):  # header-required-reported
        if key not in header: add("missing-key", "report", key)
    for at in errors(header, h["schema"], decl.path):
        add("header-schema", "refuse", at)

    slots, sec = decl.sections["slots"], decl.sections
    undeclared = sec.get("undeclared", {}).get("policy", "report")
    occ = []  # [slot index or None, slot, heading text, events]
    for ev in scan(body):
        if ev[0] == "heading":
            n, s = decl.slot_of(ev[1], ev[2])
            if s is None and ev[1] == 2 and undeclared != "allow": add("undeclared-slot", undeclared, ev[2])
            if s is not None or ev[1] == 2: occ.append([n, s, ev[2], []])
            elif occ: occ[-1][3].append(("text", ev[3], ev[2]))
            else: occ.append([None, None, None, [("text", ev[3], ev[2])]])
            continue
        if not occ: occ.append([None, None, None, []])
        occ[-1][3].append(ev)
        if ev[0] in ("fence", "comment") and not ev[-1]: add("unclosed-fence", "refuse")

    present, blocks_seen, early = collections.Counter(), set(), {}
    for n, s, heading, evs in occ:
        if s is None: continue
        present[s["slot"]] += 1
        for m, name in sorted(early.items()):  # a slot written before one declared ahead of it
            if m > n and name:
                add("slot-order", "report", name)
                early[m] = None
        early.setdefault(n, s["slot"])
        allowed = {b["type"]: b for b in s.get("blocks", [])}
        counts, prose = collections.Counter(), []
        for ev in evs:
            if ev[0] == "fence" and ev[1] == "yaml":
                src = "\n".join(ev[2]) + "\n"
                first = next((l for l in ev[2] if l.strip() and not l.lstrip().startswith("#")), "")
                root = re.match(r"^([A-Za-z_][\w-]*):", first)
                typ = root.group(1) if root and root.group(1) in catalogue() else None
                value, refused = read_yaml(src)
                if typ is None and isinstance(value, dict) and len(value) == 1 and next(iter(value)) in catalogue():
                    typ = next(iter(value))
                if typ is None:
                    prose.append(ev)
                    continue
                if isinstance(value, dict) and len(value) > 1:
                    add("multi-root", "refuse", typ)
                    continue
                blocks_seen.add(typ)
                counts[typ] += 1
                if typ not in allowed: add("block-not-allowed", "refuse", typ)
                if refused:
                    add("yaml-feature" if refused[0] == "yaml-feature" else "block-unparsed", "refuse", refused[1])
                    continue
                block(typ, value[typ], add)
            elif ev[0] == "table" and any("table" in (catalogue()[b].get("forms") or []) for b in allowed):
                typ = next(b for b in allowed if "table" in (catalogue()[b].get("forms") or []))
                blocks_seen.add(typ)
                counts[typ] += 1
                table(typ, ev[1], add)
            else:
                prose.append(ev)
        for typ, b in allowed.items():
            c = b.get("count") or {}
            if counts[typ] < c.get("min", 0) and counts[typ] == 0: add("block-missing", "refuse", typ)
            elif counts[typ] < c.get("min", 0) or counts[typ] > c.get("max", counts[typ]): add("block-count", "refuse", typ)
        text = prose
        policy = s.get("prose", "allowed")
        if policy == "forbidden" and text: add("prose-forbidden", "refuse", s["slot"])
        if policy == "required" and not text: add("prose-required", "refuse", s["slot"])
        content = s.get("content") or {}
        if "max_paragraphs" in content:
            runs, last = 0, None  # a paragraph is a run of text lines with no blank line between
            for e in prose:
                if e[0] != "text": continue
                if last is None or e[1] != last + 1: runs += 1
                last = e[1]
            if runs > content["max_paragraphs"]: add("content", "refuse", "max_paragraphs")
        if content.get("no_rfc2119") and any(re.search(r"\b(MUST|SHALL|SHOULD|REQUIRED|MAY|RECOMMENDED|OPTIONAL)\b", e[2])
                                             for e in prose if e[0] == "text"):
            add("content", "refuse", "no_rfc2119")
    keys = collections.defaultdict(list)
    for n, s, heading, evs in occ:
        if s is None: continue
        c = s.get("count") or {}
        if c.get("max", 1) > 1 or ("max" not in c and "min" in c):
            k = None
            if s.get("key") == "marker":
                m = next((re.search(r"wl:explains\s+(\S+)", e[1]) for e in evs if e[0] == "comment" and "wl:explains" in e[1]), None)
                k = m.group(1) if m else None
            elif s.get("key") == "heading":
                k = heading[len(" ".join(s["heading"]["starts_with"].split())):].strip() or None
            elif "key" not in s:
                raise NotJudged(f"repeatable slot {s['slot']!r} with no key")
            if k is None: add("slot-key-missing", "refuse", s["slot"])
            elif k in keys[s["slot"]]: add("duplicate-key", "refuse", s["slot"])
            else: keys[s["slot"]].append(k)
    for s in slots:
        c = s.get("count") or {"max": 1}
        if "max" in c and present[s["slot"]] > c["max"]: add("slot-count", "refuse", s["slot"])
        req = s.get("required", False)
        if isinstance(req, dict):
            w = req["when"]
            req = ("header_present" in w and w["header_present"] in header) or ("block_present" in w and w["block_present"] in blocks_seen)
        if req and not present[s["slot"]]: add("missing-slot", "report" if req == "report" else "refuse", s["slot"])
    return found


def block(typ, value, add):
    spec = catalogue()[typ]
    if typ == "types":
        old = []
        respell_types(value, old)
        for o in old: add("legacy-spelling", "report", o)
    for at in errors(value, spec["schema"], os.path.join(ROOT, "schemas/blocks.md")):
        add("block-schema", "refuse", at)
    by = (spec.get("entries") or {}).get("by") if isinstance(spec.get("entries"), dict) else None
    if by and isinstance(value, list):
        ids = [e.get(by) for e in value if isinstance(e, dict)]
        for d in sorted({i for i in ids if ids.count(i) > 1 and i is not None}): add("duplicate-entry", "refuse", str(d))


def table(typ, rows, add):
    spec = catalogue()[typ]
    columns = spec.get("columns") or {}
    head = cells(rows[0])
    item = spec["schema"].get("items") or {}
    if "$ref" in item: item, _ = resolve(item["$ref"], os.path.join(ROOT, "schemas/blocks.md"))
    for c in head:
        if c not in columns: add("unknown-column", "report", c)
    for c, field in columns.items():
        if field in item.get("required", []) and c not in head: add("missing-column", "refuse", c)
    value = []
    for r in rows[2:]:
        v = {}
        for c, x in zip(head, cells(r)):
            if c in columns: v[columns[c]] = int(x) if re.fullmatch(r"-?\d+", x) else x
        value.append(v)
    block(typ, value, add)


def rel(p):
    return os.path.relpath(p, ROOT)


def covered(decl_path):
    head = front(decl_path)
    return sorted({f for pat in head.get("match") or [] for f in glob.glob(os.path.join(ROOT, pat), recursive=True)})


def report(results, counts):
    """results: [(path, [(code, policy, subject)])]. Returns the exit status."""
    refused = False
    tally = collections.Counter()
    for path, found in results:
        for code, policy, subject in found:
            refused |= policy == "refuse"
            tally[(code, policy, subject)] += 1
            if not counts: print(f"{rel(path)}: {code} {policy} {subject or ''}".rstrip())
    if counts:
        for (code, policy, subject), n in sorted(tally.items(), key=lambda x: (x[0][0], x[0][2] or "")):
            print(f"{n} {code} {policy} {subject or ''}".rstrip())
    return 1 if refused else 0


def strict_of(migration, strict):
    """Faults where STRICT is not MIGRATION made strict."""
    m, s = Decl(migration), Decl(strict)
    mh, sh = front(migration), front(strict)
    faults = []
    want = json.loads(json.dumps(m.header))
    legacy, required = want.pop("legacy", {}), want.pop("required", {})
    want["legacy"] = {k: "refuse" for k in legacy}
    want["schema"]["required"] = sorted(set(want["schema"].get("required", [])) | set(required))
    old = f"{rel(migration)[:-3]}@{mh['version'].split('.')[0]}"
    new = f"{rel(migration)[:-3]}@{int(mh['version'].split('.')[0]) + 1}"
    if want["schema"]["properties"].get("family", {}).get("const") == old:
        want["schema"]["properties"]["family"]["const"] = new
    got = json.loads(json.dumps(s.header))
    got["schema"]["required"] = sorted(got["schema"].get("required", []))
    if got != want: faults.append(f"{rel(strict)}: its header block is not {rel(migration)}'s made strict")
    if s.sections != m.sections: faults.append(f"{rel(strict)}: its sections block differs from {rel(migration)}'s")
    if int(sh["version"].split(".")[0]) != int(mh["version"].split(".")[0]) + 1:
        faults.append(f"{rel(strict)}: version {sh['version']} is not one major on from {mh['version']}")
    if sh.get("match"): faults.append(f"{rel(strict)}: a strict variant declares no match until it replaces {rel(migration)}")
    if {k: v for k, v in sh.items() if k not in ("version", "match")} != {k: v for k, v in mh.items() if k not in ("version", "match")}:
        faults.append(f"{rel(strict)}: its front matter differs from {rel(migration)}'s beyond version and match")
    return faults


def main(argv):
    def arg(name):
        if name not in argv: return None
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    counts = "--counts" in argv
    if counts: argv.remove("--counts")
    resolve_key = None
    if "--resolve" in argv:
        i = argv.index("--resolve")
        resolve_key = (argv[i + 1], argv[i + 2])
        del argv[i:i + 3]
    try:
        if "--strict" in argv:
            i = argv.index("--strict")
            faults = strict_of(os.path.join(ROOT, argv[i + 1]), os.path.join(ROOT, argv[i + 2]))
            for f in faults: print(f)
            return 1 if faults else 0
        if "--vectors" in argv:
            bad = 0
            for md in sorted(glob.glob(os.path.join(ROOT, "vectors/grammar/*.md"))):
                if md.endswith("README.md"): continue
                pj = json.load(open(md[:-3] + ".projection.json"))
                want = sorted((f["code"], f["policy"], f.get("subject")) for f in pj["findings"])
                try:
                    got = sorted(walk(md, Decl(os.path.join(ROOT, pj["family"].rsplit("@", 1)[0] + ".md"))), key=str)
                except NotJudged as e:
                    print(f"not judged {rel(md)}: {e}")
                    bad = max(bad, 2) if bad != 1 else 1
                    continue
                if sorted(got, key=str) != sorted(want, key=str):
                    print(f"differs {rel(md)}: walked {got}, projection {want}")
                    bad = 1
                else:
                    print(f"agrees {rel(md)}")
            return bad
        against = arg("--against")
        files = None
        if "--file" in argv:
            i = argv.index("--file")
            files, argv = [os.path.abspath(f) for f in argv[i + 1:]], argv[:i]
        distinct = "--distinct" in argv
        if distinct: argv.remove("--distinct")
        templates = "--templates" in argv
        if templates: argv.remove("--templates")
        if not argv: raise NotJudged("no family named")
        results, faults = [], []
        for fam in argv:
            path = os.path.join(ROOT, fam + ".md")
            if not is_declaration(path):
                print(f"{fam}: no declaration at {fam}.md")
                return 1
            decl = Decl(os.path.join(ROOT, against) if against else path)
            if distinct:
                seen = {}
                for sl in decl.sections["slots"]:
                    for h in ([sl["heading"]] if isinstance(sl["heading"], str) else []) + sl.get("aliases", []):
                        k = " ".join(h.split()).lower()
                        if k in seen and seen[k] != sl["slot"]:
                            faults.append(f"{fam}: the heading {h!r} opens both {seen[k]} and {sl['slot']}")
                        seen.setdefault(k, sl["slot"])
            if templates:
                t = front(path).get("template")
                if not t or not os.path.isfile(os.path.join(ROOT, t)):
                    faults.append(f"{fam}: no template at {t!r}")
                    continue
                walked = [os.path.join(ROOT, t)]
            else:
                walked = files if files is not None else covered(path)
                if not walked: faults.append(f"{fam}: its match covers no file")
            for f in walked:
                results.append((f, walk(f, decl)))
                if resolve_key:
                    key, d = resolve_key
                    v = front(f) or {}
                    for k in key.split("."): v = v.get(k) if isinstance(v, dict) else None
                    if v is not None and not is_declaration(os.path.join(ROOT, d, f"{v}.md")):
                        faults.append(f"{rel(f)}: {key}: {v} names no declaration at {d}/{v}.md")
        for f in faults: print(f)
        return max(report(results, counts), 1 if faults else 0)
    except NotJudged as e:
        print(f"not judged: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
