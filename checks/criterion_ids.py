"""What a criterion is, where its id is written, and the register that freezes it.

Shared by checks/mint-criterion-ids.py, which mints ids, and
checks/requirement-ids.py, which holds them. Kept in one module so that the
two can never disagree about which lines are criteria.

A criterion is a checklist item (`- [ ]`) outside a fence, in a file under one
of DIRS, whose text is not a template placeholder (`<Testable assertion>`).
Its id is the one `wl:check` comment on the item: `<!-- wl:check <id> -->`, or
`<!-- wl:check <id> covers <id>... -->` where it verifies marked requirements.
The register, checks/criterion-ids.json, lists every id each file has ever
been given; an id in it never changes and is never given again.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, ".."))
REGISTER = os.path.join(HERE, "criterion-ids.json")
# The directories that hold blueprints, as checks/checklist-cites.py reads them.
DIRS = ["agents", "architecture", "languages", "patterns", "platforms", "protocol", "schemas"]

ITEM = re.compile(r"^(\s*)[-*+] \[[ xX]\] (.*)$")
PLACEHOLDER = re.compile(r"^<[^>]*>\s*$")
FENCE = re.compile(r"(`{3,}|~{3,})")
WL_CHECK_ANY = re.compile(r"<!--\s*wl:check\s+(\S+)(?:\s+covers\s+([^>]*?))?\s*-->")


def files():
    """Corpus-relative paths of every markdown file in DIRS, sorted."""
    out = []
    for d in DIRS:
        for root, dirs, names in os.walk(os.path.join(CORPUS, d)):
            dirs[:] = sorted(x for x in dirs if not x.startswith("."))
            out += [os.path.relpath(os.path.join(root, n), CORPUS) for n in sorted(names) if n.endswith(".md")]
    return sorted(out)


def in_scope(rel):
    rel = rel.replace(os.sep, "/")
    return rel.split("/", 1)[0] in DIRS and rel.endswith(".md")


def criteria(text):
    """[(first line index, last line index, item text)] for every criterion.

    An item runs from its `- [ ]` line over the lines indented under it, up to
    a blank line, a heading, or the next item."""
    lines = text.split("\n")
    out, fence, i = [], None, 0
    while i < len(lines):
        line, s = lines[i], lines[i].strip()
        if fence:
            if s.startswith(fence):
                fence = None
            i += 1
            continue
        m = FENCE.match(s)
        if m:
            fence = m.group(1)
            i += 1
            continue
        m = ITEM.match(line)
        if not m or PLACEHOLDER.match(m.group(2)):
            i += 1
            continue
        indent, j = len(m.group(1)), i
        while j + 1 < len(lines):
            nxt = lines[j + 1]
            if not nxt.strip() or ITEM.match(nxt) or nxt.lstrip().startswith("#") or FENCE.match(nxt.strip()):
                break
            if len(nxt) - len(nxt.lstrip()) <= indent and re.match(r"\s*([-*+]|\d+\.)\s", nxt):
                break
            j += 1
        out.append((i, j, "\n".join(lines[i : j + 1])))
        i = j + 1
    return out


def load_register(path=REGISTER):
    if not os.path.exists(path):
        return {"files": {}, "retired": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_register(reg, path=REGISTER):
    reg["files"] = {k: reg["files"][k] for k in sorted(reg["files"])}
    reg["retired"] = {k: sorted(v) for k, v in sorted(reg.get("retired", {}).items()) if v}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=1, ensure_ascii=False)
        f.write("\n")
