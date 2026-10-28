"""A checklist line names only what the rule it checks names.

    checklist-cites.py [--root DIR] [--known FILE]

Every `- [ ]` line outside a fence, in the directories that hold blueprints, is
read as schemas/common.md's "A line cites the rule it checks" says:

- A line that links to a section (`[...](#anchor)`, `[...](file.md#anchor)`)
  or to a whole file (`[...](file.md)`) cites it. Each anchor must resolve, by
  the slugs a markdown renderer gives headings, and every error-code token and
  every 4xx or 5xx status the line names must appear in the text of at least
  one section it cites, from its heading to the next heading of the same or a
  higher level.
- A line that cites nothing is its rule's own home. Every error-code token it
  names must be a registered code, and must also appear in its own file
  outside the checklist.

An error-code token is a code a registry declares, or an UPPER_SNAKE token
(at least one underscore) in a refusal's place: after `with`, `answered`,
`refused`, `code` and their kin, after a 4xx or 5xx status, or in a list that
began there. So `WL_DEV=1` and `CARGO_HOME` are not codes, and a token a line
is refused with is one whether or not anything registers it. A registered code
is one a registry declares, in any blueprint: a table row giving a backticked
code an HTTP status, or the first cell of a table row or a yaml `code:` key
inside a section whose heading names errors or codes.

The lines found today are checks/checklist-cites.json's `known`, measured when
it was written: the check fails on any finding not in it and on any entry that
no longer finds anything, so the list can only shrink.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
root = os.path.normpath(sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(HERE, ".."))
known_path = sys.argv[sys.argv.index("--known") + 1] if "--known" in sys.argv else os.path.join(HERE, "checklist-cites.json")
DIRS = ["agents", "architecture", "languages", "patterns", "platforms", "protocol", "schemas"]

CHECK = re.compile(r"^\s*[-*+] \[[ xX]\] ")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LINK = re.compile(r"\]\(([^)\s]*)\)")
SNAKE = re.compile(r"(?<![A-Za-z0-9_./:-])[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+(?![A-Za-z0-9_])")
WORD = re.compile(r"(?<![A-Za-z0-9_./:-])[A-Z]{3,}(?![A-Za-z0-9_])")
STATUS = re.compile(r"(?<![\w.:/-])[45]\d\d(?![\w.:%/-])")
REGISTRY_HEADING = re.compile(r"error|codes", re.I)


def slug(title):
    """The anchor a GitHub-style renderer gives a heading."""
    t = re.sub(r"<[^>]+>", "", title)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = t.strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


class Doc:
    def __init__(self, rel, text):
        self.rel, self.text = rel, text
        self.lines = text.split("\n")
        self.fenced = []                        # per line: inside a fence
        fence = None
        for line in self.lines:
            s = line.strip()
            if fence:
                self.fenced.append(True)
                if s.startswith(fence):
                    fence = None
                continue
            m = re.match(r"(`{3,}|~{3,})", s)
            if m:
                fence = m.group(1)
                self.fenced.append(True)
                continue
            self.fenced.append(False)
        self.headings = []                      # (line index, level, slug)
        seen = {}
        for i, line in enumerate(self.lines):
            if self.fenced[i]:
                continue
            m = HEADING.match(line)
            if m:
                s = slug(m.group(2))
                n = seen.get(s, 0)
                seen[s] = n + 1
                self.headings.append((i, len(m.group(1)), s if n == 0 else f"{s}-{n}"))
        self.anchors = {s: (i, lvl) for i, lvl, s in self.headings}

    def section(self, anchor):
        """The text from the anchor's heading to the next heading at its level or higher, or None."""
        if anchor not in self.anchors:
            return None
        start, level = self.anchors[anchor]
        end = len(self.lines)
        for i, lvl, _ in self.headings:
            if i > start and lvl <= level:
                end = i
                break
        return "\n".join(self.lines[start:end])

    def sections(self, title_re):
        for idx, (i, level, _) in enumerate(self.headings):
            if title_re.search(self.lines[i]):
                end = next((j for j, l, _ in self.headings[idx + 1:] if l <= level), len(self.lines))
                yield i, end


docs = {}
for d in DIRS:
    for dirpath, subdirs, files in os.walk(os.path.join(root, d)):
        subdirs[:] = sorted(s for s in subdirs if s != ".git")
        for f in sorted(files):
            if f.endswith(".md"):
                p = os.path.join(dirpath, f)
                rel = os.path.relpath(p, root).replace(os.sep, "/")
                docs[rel] = Doc(rel, open(p, encoding="utf-8").read())


def load(rel):
    if rel not in docs:
        p = os.path.join(root, rel)
        docs[rel] = Doc(rel, open(p, encoding="utf-8").read()) if os.path.isfile(p) else None
    return docs[rel]


# The registry: a table row giving a code its HTTP status, anywhere, and a code
# declared in a section about errors or codes.
registered = set()
for doc in list(docs.values()):
    for i, line in enumerate(doc.lines):
        m = re.match(r"^\|\s*`([A-Z][A-Z0-9_]*[A-Z0-9])`\s*\|\s*[1-5]\d\d\s*\|", line)
        if m and not doc.fenced[i]:
            registered.add(m.group(1))
    for start, end in doc.sections(REGISTRY_HEADING):
        for i in range(start, end):
            line = doc.lines[i]
            m = re.match(r"^\|\s*`?([A-Z][A-Z0-9_]*[A-Z0-9])`?\s*\|", line)
            if m and not doc.fenced[i]:
                registered.add(m.group(1))
            m = re.match(r"^\s*-?\s*code:\s*['\"]?([A-Z][A-Z0-9_]*[A-Z0-9])['\"]?\s*$", line)
            if m and doc.fenced[i]:
                registered.add(m.group(1))


REFUSAL = {"with", "answers", "answered", "answering", "refuses", "refused", "refusing", "code", "codes",
           "error", "errors", "returns", "returned", "returning", "rejects", "rejected", "fails", "failing"}


def codes(text):
    """Error-code tokens: a registered code anywhere, or an UPPER_SNAKE token in a refusal's place."""
    plain = LINK.sub("]", text)
    found = []
    tokens = list(re.finditer(r"`?([A-Za-z0-9_][A-Za-z0-9_./:=-]*)`?|[,/]", plain))
    chained = False
    for k, m in enumerate(tokens):
        word = m.group(1)
        if word is None:                        # a comma or slash continues a list
            continue
        prev = next((t.group(1) or t.group(0) for t in reversed(tokens[:k])), "")
        shaped = SNAKE.fullmatch(word) or (WORD.fullmatch(word) and word in registered)
        if not shaped:
            if word not in ("or", "and"):
                chained = False
            continue
        place = prev.lower() in REFUSAL or STATUS.fullmatch(prev) or (chained and prev in (",", "/", "or", "and"))
        if word in registered or place:
            found.append(word)
            chained = True
        else:
            chained = False
    return list(dict.fromkeys(found))


def statuses(text):
    return list(dict.fromkeys(STATUS.findall(LINK.sub("]", re.sub(r"<!--.*?-->", "", text)))))


findings, lines_read, lines_citing = [], 0, 0
for rel in sorted(docs):
    doc = docs[rel]
    if doc is None or rel.split("/")[0] not in DIRS:
        continue
    checklist = {i for i, l in enumerate(doc.lines) if not doc.fenced[i] and CHECK.match(l)}
    outside = "\n".join(l for i, l in enumerate(doc.lines) if i not in checklist)
    for i in sorted(checklist):
        lines_read += 1
        line = re.sub(r"<!--.*?-->", "", doc.lines[i])
        cited, where = [], []
        for target in LINK.findall(line):
            if re.match(r"[a-z]+:", target):
                continue                        # a URL is not a section of this corpus
            path, _, anchor = target.partition("#")
            if path and not path.endswith(".md"):
                continue                        # a vector or a directory is not a section
            other = load(os.path.normpath(os.path.join(os.path.dirname(rel), path)).replace(os.sep, "/")) if path else doc
            if other is None:
                findings.append(f"{rel}:{i + 1}: links {target}, which names no file")
                continue
            text = other.section(anchor) if anchor else other.text
            if text is None:
                findings.append(f"{rel}:{i + 1}: links {target}, whose anchor no heading of {other.rel} gives")
                continue
            cited.append(text)
            where.append(target)
        if where:
            lines_citing += 1
            for c in codes(line):
                if not any(re.search(r"(?<![A-Z0-9_])" + c + r"(?![A-Z0-9_])", t) for t in cited):
                    findings.append(f"{rel}:{i + 1}: names {c}, which no section it cites ({', '.join(where)}) names")
            for s in statuses(line):
                if not any(re.search(r"(?<!\d)" + s + r"(?!\d)", t) for t in cited):
                    findings.append(f"{rel}:{i + 1}: names {s}, which no section it cites ({', '.join(where)}) names")
        else:
            for c in codes(line):
                if c not in registered:
                    findings.append(f"{rel}:{i + 1}: names {c}, which no registry declares and which cites nothing")
                elif not re.search(r"(?<![A-Z0-9_])" + c + r"(?![A-Z0-9_])", outside):
                    findings.append(f"{rel}:{i + 1}: names {c}, which its file names nowhere outside the checklist")

# A finding is known by its file and what it says, not its line number, so an
# edit above it does not make it new.
known = json.load(open(known_path, encoding="utf-8"))["known"] if os.path.isfile(known_path) else []
want = {}
for k in known:
    want[k["finding"]] = want.get(k["finding"], 0) + k.get("count", 1)
got = {}
for f in findings:
    key = re.sub(r"^([^:]+):\d+:", r"\1:", f)
    got[key] = got.get(key, 0) + 1
faults = []
for f in findings:
    key = re.sub(r"^([^:]+):\d+:", r"\1:", f)
    if got[key] > want.get(key, 0):
        faults.append(f)
for key, n in sorted(want.items()):
    if got.get(key, 0) < n:
        faults.append(f"known finding gone ({got.get(key, 0)} of {n} remain), take it out of {os.path.basename(known_path)}: {key}")
print("\n".join(faults) or f"checklist-cites: {lines_read} checklist lines, {lines_citing} citing a section; "
      f"the findings are the {sum(want.values())} known")
sys.exit(1 if faults else 0)
