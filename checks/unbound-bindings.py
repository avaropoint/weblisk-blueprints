#!/usr/bin/env python3
"""Every binding names something the blueprint it binds declares.

    checks/unbound-bindings.py [--root DIR] [--markdown]

A binding is a `requires` entry's `bindings`, in a blueprint's Dependencies
section or nested in its Declaration: a type (`types: - name:`), a
behaviour (`behaviors: - name:`) or a pattern behaviour (`patterns: -
behavior:`). It is unbound when the blueprint it names exists in this corpus
and declares no type or behaviour by that name. UNBOUND_BINDINGS.md is this
script's output; it reports, and holds nothing.

What a blueprint declares is read as `weblisk validate` reads it
(weblisk-cli engine/dispatch/validate_corpus.go, declaredNames): a `### Name`
heading, a key directly under a ```yaml block that opens `types:`, and every
`- name:` inside a ```yaml block that opens `contracts:`. The CLI's rule reads
the types and `behaviors:` forms only; the `patterns: - behavior:` form, which
most framework blueprints use to bind a pattern, is counted here too and kept
apart, so the two can be compared.

With --markdown, prints the tables UNBOUND_BINDINGS.md holds; otherwise one
line per unbound binding and a count.
"""
import difflib, glob, os, re, sys

import yaml

root = os.path.normpath(sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# The families `weblisk validate` loads, schemas aside: their yaml is example.
FAMILIES = ("protocol", "architecture", "patterns", "agents", "languages", "platforms", "frameworks", "intl", "domains", "standards")
HEADING = re.compile(r"(?m)^###\s+([A-Z][A-Za-z0-9]*)\s*$")
TYPES_BLOCK = re.compile(r"(?s)```yaml\ntypes:\n(.*?)```")
TYPE_KEY = re.compile(r"(?m)^  ([A-Z][A-Za-z0-9]*):\s*$")
CONTRACTS_BLOCK = re.compile(r"(?s)```yaml\ncontracts:\n(.*?)```")
CONTRACT_NAME = re.compile(r"(?m)^\s*-\s*name:\s*([A-Za-z][\w-]*)\s*$")

corpus = {}
for fam in FAMILIES:
    for p in sorted(glob.glob(os.path.join(root, fam, "*.md"))):
        if os.path.basename(p) != "README.md":
            corpus[fam + "/" + os.path.basename(p)[:-3]] = open(p, encoding="utf-8").read()


def declared(text):
    names = set(HEADING.findall(text))
    for block in TYPES_BLOCK.findall(text):
        names.update(TYPE_KEY.findall(block))
    for block in CONTRACTS_BLOCK.findall(text):
        names.update(CONTRACT_NAME.findall(block))
    return names


def requires_entries(node):
    """Every `requires:` list of blueprint entries, at any depth of a block."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "requires" and isinstance(v, list) and any(isinstance(e, dict) and "blueprint" in e for e in v):
                yield from (e for e in v if isinstance(e, dict) and "blueprint" in e)
            else:
                yield from requires_entries(v)
    elif isinstance(node, list):
        for v in node:
            yield from requires_entries(v)


def sections(text):
    """The Dependencies section, where a blueprint states what it binds, and
    the Declaration section, which carries the same requires nested. A yaml
    block elsewhere is an example, as change-management's dependency contract
    example is, and binds nothing."""
    for m in re.finditer(r"(?m)^## (Dependencies|Declaration)\s*$", text):
        end = re.search(r"(?m)^## ", text[m.end():])
        yield text[m.end(): m.end() + end.start()] if end else text[m.end():]


def bindings(text):
    for block in (b for s in sections(text) for b in re.findall(r"```yaml\n(.*?)```", s, re.S)):
        try:
            doc = yaml.safe_load(block)
        except yaml.YAMLError:
            continue
        for e in requires_entries(doc):
            b = e.get("bindings") or {}
            if not isinstance(b, dict):
                continue
            for t in b.get("types") or []:
                if isinstance(t, dict) and t.get("name"):
                    yield e["blueprint"], "type", t["name"]
            for t in b.get("behaviors") or []:
                if isinstance(t, dict) and t.get("name"):
                    yield e["blueprint"], "behaviour", t["name"]
            for t in b.get("patterns") or []:
                if isinstance(t, dict) and t.get("behavior"):
                    yield e["blueprint"], "pattern behaviour", t["behavior"]


declares = {k: declared(v) for k, v in corpus.items()}
unbound = []
for name in sorted(corpus):
    seen = set()
    for target, kind, what in bindings(corpus[name]):
        if target not in declares or what in declares[target] or (target, kind, what) in seen:
            continue
        seen.add((target, kind, what))
        # A type is offered a type, a behaviour a behaviour: PascalCase or not.
        alike = sorted(n for n in declares[target] if n[:1].isupper() == (kind == "type"))
        near = difflib.get_close_matches(what, alike, n=2, cutoff=0.6)
        unbound.append((name, kind, what, target, near))

if "--markdown" not in sys.argv:
    for name, kind, what, target, near in unbound:
        print(f"{name}: binds {kind} {what} from {target}, which does not declare it" + (f" (declares {', '.join(near)})" if near else ""))
    print(f"unbound-bindings: {len(unbound)}")
    sys.exit(0)

GROUPS = [("type", "Types"), ("behaviour", "Behaviours"), ("pattern behaviour", "Pattern behaviours")]
for kind, title in GROUPS:
    rows = [u for u in unbound if u[1] == kind]
    rename = [u for u in rows if u[4]]
    author = [u for u in rows if not u[4]]
    print(f"## {title} — probably a rename ({len(rename)})\n")
    if rename:
        print("| Binder | Binds | From | Target declares |\n|---|---|---|---|")
        for name, _, what, target, near in rename:
            print(f"| `{name}.md` | `{what}` | `{target}` | {', '.join('`' + n + '`' for n in near)} |")
        print()
    print(f"## {title} — needs authoring ({len(author)})\n")
    if author:
        print("| Binder | Binds | From |\n|---|---|---|")
        for name, _, what, target, _ in author:
            print(f"| `{name}.md` | `{what}` | `{target}` |")
        print()
print(f"{len(unbound)} unbound: " + ", ".join(f"{sum(1 for u in unbound if u[1] == k)} {t.lower()}" for k, t in GROUPS))
