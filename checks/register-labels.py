"""Every register column in a programme file reads back as its author wrote it
(schemas/programme.md, Columns: a label or an option holding a comma
is quoted). A column is a YAML flow
mapping, where a comma ends a plain value: `label: Rate applied, and why` is
read as the label `Rate applied` and a stray key `and why` with no value, and
`options: [Slip, trip or fall]` as two options. Nothing refuses either; the
label is simply shorter than the one written, and a select offers a choice
nobody meant.

For every map, artifact specification and form under programmes/, the
frontmatter must parse, and in every `columns` list each column must hold only
the fields schemas/programme.md's Columns table declares, each once and each
with a value. A key it does not declare is the tail of a value cut at a comma.
An option that begins in lower case is reported too: it is what the tail of a
cut option looks like, and no option in the corpus begins so on purpose. That
one is a heuristic, and says so.

  register-labels.py [--root DIR]
"""
import glob, os, re, sys
import yaml

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")


def declared_fields():
    text = open(os.path.join(root, "schemas/programme.md"), encoding="utf-8").read()
    m = re.search(r"^### Columns\n(.*?)(?=^### |^## )", text, re.S | re.M)
    if not m:
        sys.exit("register-labels: schemas/programme.md has no Columns section to read the column fields from")
    fields = re.findall(r"^\| `([a-z_]+)` \|", m.group(1), re.M)
    if not fields:
        sys.exit("register-labels: the Columns section declares no fields")
    return set(fields)


class Loader(yaml.SafeLoader):
    pass


def mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    pairs, seen, dup = [], set(), []
    for k, v in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in seen:
            dup.append(key)
        seen.add(key)
        pairs.append((key, loader.construct_object(v, deep=deep)))
    d = dict(pairs)
    if dup:
        d["\0duplicate"] = dup
    return d


Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)

FIELDS = declared_fields()
faults, columns = [], 0


def judge(col, where):
    label = col.get("label", col.get("key"))
    for k, v in col.items():
        if k == "\0duplicate":
            for d in v:
                faults.append(f"{where}: column {col.get('key')!r} holds {d!r} twice")
        elif k not in FIELDS:
            faults.append(f"{where}: column {col.get('key')!r}: label {label!r} does not round-trip: {k!r} is read as a key, the tail of a value cut at a comma")
        elif v is None:
            faults.append(f"{where}: column {col.get('key')!r}: {k!r} holds no value")
    for o in col.get("options") or []:
        if isinstance(o, str) and o[:1].islower():
            faults.append(f"{where}: column {col.get('key')!r}: option {o!r} begins in lower case, which is the tail of an option cut at a comma (heuristic)")


def walk(o, where):
    global columns
    if isinstance(o, dict):
        for k, v in o.items():
            if k == "columns" and isinstance(v, list):
                for c in v:
                    if isinstance(c, dict):
                        columns += 1
                        judge(c, where)
            walk(v, where)
    elif isinstance(o, list):
        for x in o:
            walk(x, where)


files = sorted(
    glob.glob(os.path.join(root, "programmes/*/map.md"))
    + glob.glob(os.path.join(root, "programmes/*/specs/*.md"))
    + glob.glob(os.path.join(root, "programmes/*/templates/*.md"))
)
if not files:
    sys.exit("register-labels: no programme files to read")
for path in files:
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        continue
    end = text.find("\n---", 3)
    if end < 0:
        faults.append(f"{rel}: frontmatter is not closed")
        continue
    try:
        data = yaml.load(text[4:end], Loader=Loader)
    except yaml.YAMLError as e:
        faults.append(f"{rel}: frontmatter does not parse: {str(e).splitlines()[0]}")
        continue
    walk(data, rel)

print("\n".join(faults) or f"register-labels: {columns} columns in {len(files)} programme files, each reading back as written")
sys.exit(1 if faults else 0)
