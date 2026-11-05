#!/usr/bin/env python3
"""Every criterion's acceptance class, derived from structure the corpus holds.

    checks/acceptance-classes.py                       print the distribution
    checks/acceptance-classes.py --json                print the register
    checks/acceptance-classes.py --write               write checks/acceptance-classes.json
    checks/acceptance-classes.py --check               fail when the register is not a fresh derivation
    checks/acceptance-classes.py --expect S=P,J=P,B=P,E=P,F=P --within PTS
                                                       fail when a class's share is outside P +/- PTS
    checks/acceptance-classes.py --credits REF         the criteria rule 1 credits through REF alone
    --threat-model FILE                                read the threat model from FILE
    --register FILE                                    read or write the register at FILE

The rules are architecture/generation's "How a criterion gets its class"
(ACCEPTANCE_PLAN, "How a requirement gets its class"), taken in order, the
first that matches giving the class. Nothing here lists a criterion by hand.

A criterion is what the engine's suite reads as one (engine/conform,
readFile): a checklist item outside a fence carrying a `wl:check` id, in any
markdown file of the corpus; a `wl:id` requirement; and an entry of a
`requirements` block. A `wl:id` written inside a fence (a contract
behaviour's rule) is classed too, so a lookup by its id succeeds. Its key is
`<file path without .md>:<id>`.

Where a criterion sits: its file; every heading above it (so a section
credits its subsections); every section it links to, with that section's
own enclosing headings; every requirement id it covers; and every contract
behaviour it sits in (its id is one of the behaviour's rules) or names (the
behaviour's name, written in the item).

1. S. A ref in architecture/threat-model's `Control refs` column names the
   criterion's file (`file`), a section it sits under or links to
   (`file#anchor`), or its id, a requirement it covers or a behaviour it sits
   in or names (`file:id`). Every ref must resolve: a file, a heading's
   anchor, or an id written as `wl:id`, `wl:check`, a requirements entry, a
   `verifies` entry or a behaviour's name. One that does not fails the check.
   `ThreatBoundary.controls` is a type in that file and holds no values, so
   no instance of it is read.
2. S. The item names a 401 or 403 status, or an error code that a
   protocol/types errors table (columns Code and HTTP, read by name) gives
   401 or 403.
3. J. It sits under or links to a registration section (the `registration`
   slot of schemas/architecture, by its heading and aliases), or it governs
   what another service of schemas/programme's services table binds: the
   binder's `## Dependencies` `requires` entry naming this file, whose
   `bindings` give `behaviors` (sat in or named), `endpoints` (the path
   written in the item), `types` (the type's name written in the item) and
   `events` (the topic written in the item). NOT read: a binding by a
   component outside the services table (domains, agents), a binding in a
   tenant's own blueprints, and `patterns` bindings, which name a pattern
   and no part of this file. "Another component in this tenant" is read as
   another service of the services table, the programme every tenant builds.
4. F. The file's header type is `language` or `platform` (or its family is
   schemas/language or schemas/platform), and the item names no route,
   status, error code, header, event or environment variable.
5. E. Its obligation is a record: it names AuditEntry or LogEntry, an audit
   entry or that an act is audited, a trace or span field (trace_id,
   span_id, traceparent, trace context), a log line, or an event emitted or
   published.
6. B. Anything else.
"""
import fnmatch, json, os, re, sys
import yaml  # PyYAML

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import criterion_ids  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, ".."))
REGISTER = os.path.join(HERE, "acceptance-classes.json")
RULES_REF = "architecture/generation#how-a-criterion-gets-its-class"
CLASSES = ["S", "J", "B", "E", "F"]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK = re.compile(r"\]\(([^)\s]*)\)")
WL_ID = re.compile(r"<!--\s*wl:id\s+([a-z0-9][a-z0-9-]*)\s*-->")
WL_CHECK = criterion_ids.WL_CHECK_ANY
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)")


def slug(title):
    """The anchor a GitHub-style renderer gives a heading (as checks/checklist-cites.py)."""
    parts = re.split(r"(`+[^`]*`+)", title)
    t = "".join(p if p.startswith("`") else re.sub(r"<[^>]+>", "", p) for p in parts)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = t.strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


class Doc:
    """One corpus file: its lines, fences, headings, ids and yaml blocks."""

    def __init__(self, ref, text):
        self.ref = ref
        self.text = text.replace("\r\n", "\n")
        self.lines = self.text.split("\n")
        self.fenced, self.blocks = [], []
        fence, start, info = None, 0, ""
        for i, line in enumerate(self.lines):
            if fence:
                self.fenced.append(True)
                t = line.strip()
                if len(line) - len(line.lstrip(" ")) <= 3 and len(t) >= len(fence) and t.strip(fence[0]) == "":
                    if info == "yaml":
                        self.blocks.append((start, "\n".join(self.lines[start + 1 : i])))
                    fence = None
                continue
            m = FENCE_OPEN.match(line)
            if m:
                fence, start, info = m.group(1), i, m.group(2)
                self.fenced.append(True)
                continue
            self.fenced.append(False)
        self.headings, seen = [], {}
        for i, line in enumerate(self.lines):
            if self.fenced[i]:
                continue
            m = HEADING.match(line)
            if m:
                s = slug(m.group(2))
                n = seen.get(s, 0)
                seen[s] = n + 1
                self.headings.append((i, len(m.group(1)), s if n == 0 else f"{s}-{n}", m.group(2).strip()))
        self.anchors = {s: (i, lvl) for i, lvl, s, _ in self.headings}
        self.ids = set(WL_ID.findall(self.text))
        self.ids |= {m.group(1) for m in WL_CHECK.finditer(self.text)}
        self.values = []
        for _, src in self.blocks:
            try:
                v = yaml.safe_load(src)
            except Exception:
                continue
            if isinstance(v, dict) and len(v) == 1:
                self.values.append(v)
        self.behaviours = {}                    # name -> set of wl:id inside its rules
        for i0, src in self.blocks:
            self._behaviours(i0, src)
        for v in self.values:
            for key in ("requirements", "verifies"):
                for e in v.get(key) if isinstance(v.get(key), list) else []:
                    if isinstance(e, dict) and e.get("id"):
                        self.ids.add(str(e["id"]))
        self.ids |= set(self.behaviours)
        self.header = self._header()

    def _behaviours(self, i0, src):
        """Behaviours of a contracts block, each with the wl:id markers written in its entry."""
        try:
            v = yaml.safe_load(src)
        except Exception:
            return
        if not (isinstance(v, dict) and isinstance(v.get("contracts"), dict)):
            return
        names = [b.get("name") for b in v["contracts"].get("behaviors") or [] if isinstance(b, dict) and b.get("name")]
        if not names:
            return
        current = None
        for line in src.split("\n"):
            m = re.match(r"^\s*-\s*name:\s*['\"]?([A-Za-z0-9_.-]+)['\"]?\s*$", line)
            if m and m.group(1) in names:
                current = m.group(1)
                self.behaviours.setdefault(current, set())
                continue
            if current:
                self.behaviours[current] |= set(WL_ID.findall(line))

    def _header(self):
        m = re.match(r"---\n(.*?)\n---\n", self.text, re.S) or re.match(r"<!--\s*blueprint\n(.*?)-->", self.text, re.S)
        if not m:
            return {}
        try:
            h = yaml.safe_load(m.group(1))
        except Exception:
            return {}
        return h if isinstance(h, dict) else {}

    def kind(self):
        fam = str(self.header.get("family", ""))
        if fam.startswith("schemas/language@"):
            return "language"
        if fam.startswith("schemas/platform@"):
            return "platform"
        return str(self.header.get("type", ""))

    def enclosing(self, line):
        """The anchors of every heading above line, innermost last."""
        stack = []
        for i, lvl, s, _ in self.headings:
            if i > line:
                break
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, s))
        return [s for _, s in stack]

    def enclosing_titles(self, line):
        stack = []
        for i, lvl, _, title in self.headings:
            if i > line:
                break
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            stack.append((lvl, title))
        return stack


class Corpus:
    def __init__(self, root, threat_model=None):
        self.root = root
        self.docs = {}
        for d, subdirs, files in os.walk(root):
            subdirs[:] = sorted(s for s in subdirs if not s.startswith(".") and s != "node_modules")
            for f in sorted(files):
                if f.endswith(".md"):
                    p = os.path.join(d, f)
                    ref = os.path.relpath(p, root).replace(os.sep, "/")[:-3]
                    self.docs[ref] = Doc(ref, open(p, encoding="utf-8").read())
        if threat_model:
            self.docs["architecture/threat-model"] = Doc("architecture/threat-model", open(threat_model, encoding="utf-8").read())

    def resolve_link(self, ref, target):
        """A link's (file ref, anchor), or None for a URL or a non-markdown path."""
        if re.match(r"[a-z]+:", target):
            return None
        path, _, anchor = target.partition("#")
        if path and not path.endswith(".md"):
            return None
        other = os.path.normpath(os.path.join(os.path.dirname(ref), path[:-3])).replace(os.sep, "/") if path else ref
        return other, anchor


def table_rows(doc, want):
    """Each row of every table whose header has all of `want`, as a dict by column name, with its line."""
    out, i = [], 0
    lines = doc.lines
    while i < len(lines):
        if doc.fenced[i] or not lines[i].startswith("|"):
            i += 1
            continue
        head = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        if not all(w in head for w in want) or i + 1 >= len(lines) or not re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1]):
            i += 1
            continue
        j = i + 2
        while j < len(lines) and lines[j].startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", lines[j].strip().strip("|"))]
            if len(cells) == len(head):
                out.append((j, dict(zip(head, cells))))
            j += 1
        i = j
    return out


def controls(corpus):
    """(ref, vector, line) for every Control refs cell entry, and the faults of those that do not resolve."""
    tm = corpus.docs.get("architecture/threat-model")
    if tm is None:
        sys.exit("acceptance-classes: architecture/threat-model is not in the corpus")
    out, faults = [], []
    for line, row in table_rows(tm, ["#", "Control refs"]):
        vector = row["#"]
        for ref in re.findall(r"`([^`]+)`", row["Control refs"]):
            out.append((ref, vector, line + 1))
            f, why = resolve_control(corpus, ref)
            if why:
                faults.append(f"architecture/threat-model.md line {line + 1} (vector {vector}): control ref {ref} {why}")
    if not out:
        sys.exit("acceptance-classes: the threat model's attack tables give no Control refs, so rule 1 credits nothing")
    return out, faults


def resolve_control(corpus, ref):
    if "#" in ref:
        f, anchor = ref.split("#", 1)
    elif ":" in ref:
        f, anchor = ref.split(":", 1)
    else:
        f, anchor = ref, None
    doc = corpus.docs.get(f)
    if doc is None:
        return f, "names a file the corpus does not hold"
    if anchor is None:
        return f, ""
    if "#" in ref:
        return f, "" if anchor in doc.anchors else "names a heading the file does not have"
    return f, "" if anchor in doc.ids else "names an id the file does not write"


class Criterion:
    def __init__(self, doc, cid, line, text, covers, kind):
        self.doc, self.id, self.line, self.text, self.kind = doc, cid, line, text, kind
        self.key = f"{doc.ref}:{cid}"
        self.covers = []                        # (file ref, id)
        for c in covers:
            if ":" in c:
                f, i = c.split(":", 1)
                self.covers.append((f, i))
            else:
                self.covers.append((doc.ref, c))


def criteria(corpus):
    out = {}
    for ref, doc in corpus.docs.items():
        covered = set()
        for i, j, text in criterion_ids.criteria(doc.text):
            m = WL_CHECK.search(text)
            if not m:
                continue
            covers = (m.group(2) or "").split()
            covered |= set(covers)
            c = Criterion(doc, m.group(1), i, WL_CHECK.sub("", text).strip(), covers, "item")
            out.setdefault(c.key, c)
        for i, line in enumerate(doc.lines):
            for rid in WL_ID.findall(line):
                body = WL_ID.sub("", line).strip()
                if doc.fenced[i]:
                    # A rule inside a yaml fence: its text is the next list line
                    # when the marker is a comment above it.
                    nxt = doc.lines[i + 1].strip() if i + 1 < len(doc.lines) else ""
                    body = body.lstrip("#").strip() or nxt.lstrip("- ").strip()
                c = Criterion(doc, rid, i, body, [], "requirement")
                out.setdefault(c.key, c)
        for v in doc.values:
            if isinstance(v.get("requirements"), list):
                for e in v["requirements"]:
                    if isinstance(e, dict) and e.get("id"):
                        c = Criterion(doc, str(e["id"]), 0, str(e.get("text", "")), [], "requirement")
                        out.setdefault(c.key, c)
    return out


def ancestors(doc, anchor):
    if doc is None or anchor not in doc.anchors:
        return [anchor] if anchor else []
    return doc.enclosing(doc.anchors[anchor][0])


def where(corpus, c):
    """What a criterion sits in: sections (file, anchor), ids (file, id), behaviours (file, name)."""
    doc = c.doc
    sections = {(doc.ref, a) for a in doc.enclosing(c.line)} if c.line or c.kind == "item" else set()
    for target in LINK.findall(c.text):
        r = corpus.resolve_link(doc.ref, target)
        if not r:
            continue
        f, anchor = r
        if anchor:
            sections |= {(f, a) for a in ancestors(corpus.docs.get(f), anchor)}
    ids = {(doc.ref, c.id)} | set(c.covers)
    behaviours = set()
    for f, d in [(doc.ref, doc)] + [(f, corpus.docs.get(f)) for f, _ in c.covers]:
        if d is None:
            continue
        for name, rules in d.behaviours.items():
            if any((f, i) in ids for i in rules):
                behaviours.add((f, name))
    for name in doc.behaviours:
        if re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", c.text):
            behaviours.add((doc.ref, name))
    # A covered requirement sits where its marker is written.
    for f, i in c.covers:
        d = corpus.docs.get(f)
        if d is None:
            continue
        for n, line in enumerate(d.lines):
            if f"wl:id {i} " in line or f"wl:id {i}-->" in line:
                sections |= {(f, a) for a in d.enclosing(n)}
                break
    return sections, ids, behaviours


def error_statuses(corpus):
    types = corpus.docs.get("protocol/types")
    out = {}
    if types is None:
        return out
    for _, row in table_rows(types, ["Code", "HTTP"]):
        m = re.fullmatch(r"`?([A-Z][A-Z0-9_]*)`?", row["Code"])
        s = re.match(r"\d{3}", row["HTTP"])
        if m and s:
            out[m.group(1)] = int(s.group(0))
    return out


STATUS_4013 = re.compile(r"(?<![\w.:/-])40[13](?![\w.:%/-])")
CODE = re.compile(r"(?<![A-Za-z0-9_])[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+(?![A-Za-z0-9_])")
ROUTE = re.compile(r"(?<![\w.])/(?:v\d+|livez|readyz|\.well-known)\b|\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+`?/")
STATUS = re.compile(r"(?<![\w.:/-])[1-5]\d\d(?![\w.:%/-])")
HEADER = re.compile(r"\b(?:[A-Z][A-Za-z]*-)+[A-Z][A-Za-z]+\b|\bheaders?\b")
EVENT = re.compile(r"`[a-z][a-z0-9_]*(?:\.[a-z0-9_*]+){2,}`|\bevents?\b|\bemit|\bpublish")
RECORD = re.compile(
    r"\bAuditEntry\b|\bLogEntry\b|\baudit (?:entry|entries|record|trail)\b|\baudited\b|\bwrites? (?:an? )?audit\b"
    r"|\btrace_id\b|\bspan_id\b|\btraceparent\b|\btrace (?:context|parent|propagation)\b|\bspans?\b"
    r"|\blog (?:line|lines|entry|entries)\b|\blogged\b"
    r"|\b(?:emit|emits|emitted|publish|publishes|published)\b[^.;]*\bevents?\b|\bevents?\b[^.;]*\b(?:emitted|published)\b")
REG_HEADINGS = None


def registration_headings(corpus):
    """The registration slot's heading and aliases, and the file refs its family's match covers."""
    arch = corpus.docs.get("schemas/architecture")
    out, files = set(), set()
    if arch is None:
        return out, files
    for pat in arch.header.get("match") or []:
        files |= {r for r in corpus.docs if fnmatch.fnmatchcase(r + ".md", pat)}
    for v in arch.values:
        sec = v.get("sections")
        if isinstance(sec, dict):
            for s in sec.get("slots") or []:
                if s.get("slot") == "registration":
                    if isinstance(s.get("heading"), str):
                        out.add(" ".join(s["heading"].split()))
                    out |= {" ".join(a.split()) for a in s.get("aliases") or []}
    return out, files


def services(corpus):
    """The blueprint refs of schemas/programme's services table, read by column name."""
    prog = corpus.docs.get("schemas/programme")
    out = []
    if prog is None:
        return out
    for _, row in table_rows(prog, ["service", "blueprint", "needs running first"]):
        m = re.search(r"\(([^)]+\.md)\)", row["blueprint"])
        if m:
            r = corpus.resolve_link("schemas/programme", m.group(1))
            if r:
                out.append(r[0])
    return out


def bindings(corpus, svc):
    """For each service blueprint, what other services bind of it: {file: {kind: set(names), ...}}."""
    out = {}
    for binder in svc:
        d = corpus.docs.get(binder)
        if d is None:
            continue
        for v in d.values:
            if not isinstance(v.get("requires"), list):
                continue
            for e in v["requires"]:
                if not isinstance(e, dict) or e.get("blueprint") not in svc or e.get("blueprint") == binder:
                    continue
                b = e.get("bindings") or {}
                got = out.setdefault(e["blueprint"], {"behaviors": set(), "endpoints": set(), "types": set(), "events": set()})
                for x in b.get("behaviors") or []:
                    got["behaviors"].add(x.get("name") if isinstance(x, dict) else x)
                for x in b.get("endpoints") or []:
                    if isinstance(x, dict) and x.get("path"):
                        got["endpoints"].add(x["path"])
                for x in b.get("types") or []:
                    got["types"].add(x.get("name") if isinstance(x, dict) else x)
                for x in b.get("events") or []:
                    if isinstance(x, dict) and x.get("topic"):
                        got["events"].add(x["topic"])
    return out


def classify(corpus, ctrl):
    crits = criteria(corpus)
    statuses = error_statuses(corpus)
    reg, reg_files = registration_headings(corpus)
    binds = bindings(corpus, services(corpus))
    result, credits = {}, {}
    for key in sorted(crits):
        c = crits[key]
        sections, ids, behaviours = where(corpus, c)
        text = re.sub(r"<!--.*?-->", "", c.text)
        plain = LINK.sub("]", text)
        # Rule 1: credited by a control ref.
        hit = []
        for ref, vector, _ in ctrl:
            if "#" in ref:
                f, a = ref.split("#", 1)
                ok = (f, a) in sections
            elif ":" in ref:
                f, i = ref.split(":", 1)
                ok = (f, i) in ids or (f, i) in behaviours
            else:
                ok = c.doc.ref == ref
            if ok:
                hit.append((ref, vector))
        if hit:
            credits[key] = sorted({r for r, _ in hit})
            ref, vector = hit[0]
            result[key] = ("S", f"rule 1: control ref {ref} (architecture/threat-model, vector {vector})")
            continue
        # Rule 2: a refusal at 401 or 403.
        m = STATUS_4013.search(plain)
        if m:
            result[key] = ("S", f"rule 2: refused at {m.group(0)}")
            continue
        code = next((x for x in CODE.findall(plain) if statuses.get(x) in (401, 403)), None)
        if code:
            result[key] = ("S", f"rule 2: {code}, which protocol/types gives {statuses[code]}")
            continue
        # Rule 3: registration, or bound by another service.
        titles = [" ".join(t.split()) for _, t in c.doc.enclosing_titles(c.line)] if c.kind == "item" or c.line else []
        linked_reg = None
        for f, a in sections:
            d = corpus.docs.get(f)
            if d and f in reg_files and a in d.anchors:
                t = next(t for i, lvl, s, t in d.headings if s == a)
                if " ".join(t.split()) in reg:
                    linked_reg = f"{f}#{a}"
                    break
        reg_here = next((t for t in titles if t in reg), None) if c.doc.ref in reg_files else None
        if reg_here or linked_reg:
            result[key] = ("J", f"rule 3: registration section {linked_reg or c.doc.ref + '#' + slug(reg_here)}")
            continue
        b = binds.get(c.doc.ref)
        bound = None
        if b:
            for name in sorted(b["behaviors"]):
                if (c.doc.ref, name) in behaviours:
                    bound = f"behaviour {name}"
                    break
            if not bound:
                for p in sorted(b["endpoints"]):
                    if re.search(re.escape(p) + r"(?![\w/-])", plain):
                        bound = f"endpoint {p}"
                        break
            if not bound:
                for t in sorted(b["types"]):
                    if re.search(r"(?<![\w])" + re.escape(t) + r"(?![\w])", plain):
                        bound = f"type {t}"
                        break
            if not bound:
                for t in sorted(b["events"]):
                    if t in plain:
                        bound = f"event {t}"
                        break
        if bound:
            result[key] = ("J", f"rule 3: {bound}, bound by another service of schemas/programme")
            continue
        # Rule 4: form, in a language or platform blueprint.
        if c.doc.kind() in ("language", "platform") and not (
                ROUTE.search(plain) or STATUS.search(plain) or CODE.search(plain) or HEADER.search(plain) or EVENT.search(plain)):
            result[key] = ("F", f"rule 4: a {c.doc.kind()} blueprint, naming no route, status, code, header, event or variable")
            continue
        # Rule 5: a record.
        m = RECORD.search(plain)
        if m:
            result[key] = ("E", f"rule 5: a record ({m.group(0)})")
            continue
        result[key] = ("B", "rule 6: nothing above matched")
    return result, credits


def register(result):
    counts = {k: 0 for k in CLASSES}
    for cls, _ in result.values():
        counts[cls] += 1
    return {"derived_by": "checks/acceptance-classes.py", "rules": RULES_REF, "counts": counts,
            "criteria": {k: {"class": cls, "class_by": by} for k, (cls, by) in sorted(result.items())}}


def dump(reg):
    return json.dumps(reg, indent=1, ensure_ascii=False, sort_keys=False) + "\n"


def main():
    root = os.path.normpath(arg("--root", ROOT))
    corpus = Corpus(root, arg("--threat-model"))
    ctrl, faults = controls(corpus)
    if faults:
        for f in faults:
            print(f)
        sys.exit(1)
    result, credits = classify(corpus, ctrl)
    reg = register(result)
    path = arg("--register", REGISTER)
    if "--credits" in sys.argv:
        ref = arg("--credits")
        for k in sorted(credits):
            if credits[k] == [ref]:
                print(k)
        return
    if "--json" in sys.argv:
        sys.stdout.write(dump(reg))
        return
    if "--write" in sys.argv:
        with open(path, "w", encoding="utf-8") as f:
            f.write(dump(reg))
    total = len(result)
    for k in CLASSES:
        n = reg["counts"][k]
        print(f"{k} {n:6} {100 * n / total:5.1f}%")
    print(f"acceptance-classes: {total} criteria, {len(ctrl)} control refs")
    if "--check" in sys.argv:
        try:
            held = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError) as e:
            print(f"acceptance-classes: the register {os.path.relpath(path, root)} cannot be read: {e}")
            sys.exit(1)
        if held != reg:
            a, b = held.get("criteria", {}), reg["criteria"]
            diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
            print(f"acceptance-classes: the register is not a fresh derivation; {len(diff)} criteria differ, "
                  f"first {', '.join(diff[:5]) or '(the header)'}: run checks/acceptance-classes.py --write")
            sys.exit(1)
    if "--expect" in sys.argv:
        within = float(arg("--within", "0"))
        bad = []
        for part in arg("--expect").split(","):
            k, v = part.split("=")
            share = 100 * reg["counts"][k] / total
            if abs(share - float(v)) > within:
                bad.append(f"{k} is {share:.1f}%, not within {within:g} points of {v}%")
        if bad:
            print("acceptance-classes: " + "; ".join(bad))
            sys.exit(1)


if __name__ == "__main__":
    main()
