#!/usr/bin/env python3
"""The engine holds no corpus knowledge (architecture/engine.md, Neutrality).

Reads the tools' source at the commit checks/engine-neutrality.json pins, from
the repository's objects and never its working tree, and lists every string
literal equal to a name the corpus declares. Each name is read from the corpus
file that declares it, and none is copied here:

  route        a METHOD /path pair, or a `path:` key, in architecture/,
               protocol/, patterns/ or agents/
  code         an error code a table row gives an HTTP status, anywhere
  component    an architecture blueprint's name (architecture/<name>.md)
  language     a language or platform blueprint's name
  noun         a family declaration's noun:
  heading      a slot heading a family declaration's sections block names,
               as "## <heading>", or bare when it is more than one word
  instruction  a sentence of an instruction's text (instructions/), found
               inside a literal, whitespace aside

The findings must be exactly the `known` list of engine-neutrality.json, which
can only shrink: a finding not on it is new knowledge in the tools, and an
entry that finds nothing has been moved out and must be removed from the list.

When the tools' repository or the pinned commit cannot be read, the check
prints NOT RUN and exits 3, never 0. REQUIRE_ALL_VERIFIERS=1 in checks/run.sh
makes that a failure.

  engine-neutrality.py [--tools DIR] [--dir DIR] [--known FILE] [--root DIR]

--tools names the tools' repository (default: $WEBLISK_TOOLS, else
../weblisk-tools, else ../weblisk-cli beside the corpus). --dir scans a plain
directory instead of a commit, which is how the control adds a name to a copy.
"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]


def opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


root = opt("--root", os.path.normpath(os.path.join(HERE, "..")))
known_path = opt("--known", os.path.join(HERE, "engine-neutrality.json"))
pin = json.load(open(os.path.join(HERE, "engine-neutrality.json"), encoding="utf-8"))
known_doc = json.load(open(known_path, encoding="utf-8")) if os.path.isfile(known_path) else {"known": []}


def notrun(why):
    print(f"engine-neutrality: NOT RUN: {why}")
    sys.exit(3)


def read(rel):
    return open(os.path.join(root, rel), encoding="utf-8").read()


def corpus_md(*dirs):
    out = []
    for d in dirs:
        out += sorted(glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True))
    return out


# ---- the names the corpus declares, each read where it is declared ----------
names = {}  # literal -> set of categories


def add(cat, value):
    if value and len(value) > 1:
        names.setdefault(value, set()).add(cat)


for p in corpus_md("architecture", "protocol", "patterns", "agents"):
    t = open(p, encoding="utf-8").read()
    for m in re.finditer(r"`(?:GET|POST|PUT|PATCH|DELETE|HEAD) (/[^`\s?]+)", t):
        add("route", m.group(1))
    for m in re.finditer(r"^\s*-?\s*path:\s*['\"]?(/[^\s'\"?]+)", t, re.M):
        add("route", m.group(1))
for p in corpus_md("."):
    if "/checks/" in p or "/node_modules/" in p or "/vectors/" in p:
        continue
    for m in re.finditer(r"^\|\s*`([A-Z][A-Z0-9_]*[A-Z0-9])`\s*\|\s*[1-5]\d\d\s*\|", open(p, encoding="utf-8").read(), re.M):
        add("code", m.group(1))
for p in glob.glob(os.path.join(root, "architecture", "*.md")):
    if os.path.basename(p) != "README.md":
        add("component", os.path.basename(p)[:-3])
for d in ("languages", "platforms"):
    for p in glob.glob(os.path.join(root, d, "*.md")):
        if os.path.basename(p) != "README.md":
            add("language", os.path.basename(p)[:-3])
for p in corpus_md("schemas", "documents"):
    t = open(p, encoding="utf-8").read()
    head = re.match(r"---\n(.*?)\n---\n", t, re.S)
    if not head or "family: schemas/family@" not in head.group(1):
        continue
    m = re.search(r"^noun:\s*([a-z][a-z-]*)\s*$", head.group(1), re.M)
    if m:
        add("noun", m.group(1))
    for block in re.findall(r"^```yaml\n(sections:\n.*?)^```", t, re.M | re.S):
        for h in re.findall(r"heading:\s*(?:\"([^\"]+)\"|([A-Z][^,}\n]*?))\s*[,}]", block):
            h = (h[0] or h[1]).strip()
            add("heading", "## " + h)
            if " " in h:
                add("heading", h)


def instruction_sentences():
    out = []
    for p in sorted(glob.glob(os.path.join(root, "instructions", "**", "*.md"), recursive=True)):
        if os.path.basename(p) == "README.md":
            continue
        t = open(p, encoding="utf-8").read()
        m = re.search(r"^## Text\n.*?^```text\n(.*?)^```", t, re.M | re.S)
        if not m:
            continue
        text = " ".join(m.group(1).split())
        for s in re.split(r"(?<=[.:;])\s+", text):
            if len(s.split()) >= 6:
                out.append(s)
    return out


sentences = instruction_sentences()


# ---- the tools' source --------------------------------------------------------
def go_literals(src):
    """Every string literal of a Go file: interpreted "..." and raw `...`,
    skipping comments and runes. Values are returned as written in the source,
    with the common escapes undone."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
        elif c == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            i = j + 1
        elif c == "`":
            j = src.find("`", i + 1)
            j = n if j < 0 else j
            out.append(src[i + 1 : j])
            i = j + 1
        elif c == '"':
            j, buf = i + 1, []
            while j < n and src[j] != '"' and src[j] != "\n":
                if src[j] == "\\" and j + 1 < n:
                    buf.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(src[j + 1], "\\" + src[j + 1]))
                    j += 2
                else:
                    buf.append(src[j])
                    j += 1
            out.append("".join(buf))
            i = j + 1
        else:
            i += 1
    return out


def source_files():
    """(path, text) of every non-test Go source file, and every embedded Go
    source file (*.go.txt), at the pinned commit or in --dir."""
    want = lambda p: (p.endswith(".go") and not p.endswith("_test.go") or p.endswith(".go.txt")) and "/testdata/" not in "/" + p
    if "--dir" in argv:
        d = opt("--dir")
        for p in sorted(glob.glob(os.path.join(d, "**", "*"), recursive=True)):
            rel = os.path.relpath(p, d).replace(os.sep, "/")
            if os.path.isfile(p) and want(rel):
                yield rel, open(p, encoding="utf-8", errors="replace").read()
        return
    tools = opt("--tools") or os.environ.get("WEBLISK_TOOLS")
    if not tools:
        for cand in ("weblisk-tools", "weblisk-cli"):
            c = os.path.join(root, "..", cand)
            if os.path.isdir(os.path.join(c, ".git")) or os.path.isfile(os.path.join(c, ".git")):
                tools = c
                break
    if not tools or not os.path.exists(tools):
        notrun("the tools' repository is not found (--tools, $WEBLISK_TOOLS, ../weblisk-tools or ../weblisk-cli)")
    commit = pin["commit"]
    git = lambda *a: subprocess.run(["git", "-C", tools, *a], capture_output=True, text=True)
    if git("cat-file", "-e", commit + "^{commit}").returncode != 0:
        notrun(f"commit {commit} is not in {tools}")
    ls = git("ls-tree", "-r", "--name-only", commit)
    if ls.returncode != 0:
        notrun(f"cannot list {commit} in {tools}")
    for rel in ls.stdout.splitlines():
        if want(rel):
            show = git("show", f"{commit}:{rel}")
            if show.returncode != 0:
                notrun(f"cannot read {rel} at {commit}")
            yield rel, show.stdout


findings = set()
scanned = 0
for rel, src in source_files():
    scanned += 1
    for lit in go_literals(src):
        for cat in names.get(lit, ()):
            findings.add(f"{rel}: {cat} {lit}")
        if len(lit) > 30:
            flat = " ".join(lit.split())
            for s in sentences:
                if s in flat:
                    findings.add(f"{rel}: instruction {s[:60]}")
if scanned == 0:
    notrun("no source file was read")

known = {k["finding"] for k in known_doc["known"]}
new = sorted(findings - known)
gone = sorted(known - findings)
for f in new:
    print(f"new: {f}")
for f in gone:
    print(f"known finding gone: {f} (remove it from the known list)")
where = opt("--dir") or pin["commit"][:7]
print(f"engine-neutrality: {scanned} source files at {where}, {len(names)} declared names, "
      f"{len(findings)} findings, {len(known)} known, {len(new)} new, {len(gone)} gone")
sys.exit(1 if new or gone else 0)
