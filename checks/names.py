#!/usr/bin/env python3
"""The names check (schemas/names.md, "Where a namespace may appear").

Reports every namespace a file names that is neither reserved nor this
repository's own, and any difference between the families vectors/ids.json
parses with and the families the corpus declares. Every list it uses is read
from the corpus: the reserved names and families from schemas/names.md's
Declaration, the kinds from schemas/kinds.md, the repository's own namespace
from catalog.yaml.

    checks/names.py              check this repository
    checks/names.py --scan DIR   check DIR's files against this corpus's names
"""
import json, os, re, subprocess, sys
import yaml

CORPUS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def read(rel):
    with open(os.path.join(CORPUS, rel), encoding="utf-8") as f:
        return f.read()

def section(text, heading):
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        sys.exit(f"names: no '## {heading}' section, so there is nothing to check against")
    return m.group(1)

declaration = yaml.safe_load(re.search(r"```yaml\n(.*?)```", section(read("schemas/names.md"), "Declaration"), re.S).group(1))
kinds = set(re.findall(r"^\| `([a-z][a-z0-9-]*)` \|", section(read("schemas/kinds.md"), "Declared kinds"), re.M))
own = yaml.safe_load(read("catalog.yaml"))["namespace"]
families = kinds | set(declaration["families"])
allowed = set(declaration["reserved"]) | {own}

faults = []
vectors = json.loads(read("vectors/ids.json"))
for f in sorted(set(vectors["families"]) ^ families):
    where = "vectors/ids.json" if f in vectors["families"] else "the declarations"
    faults.append(f"family {f!r} is only in {where}")

# A namespace is named after `//`, either at the start of a ref or after a
# declared family's `:`. A URL's `https://host/` is neither.
NAMED = re.compile(r"(?:(?P<family>[a-z][a-z0-9-]*):|(?<![A-Za-z0-9:/.]))//(?P<ns>[A-Za-z][A-Za-z0-9-]{1,38})/")
exempt = set(declaration.get("names_check_exempt", []))

def files(root):
    try:
        out = subprocess.run(["git", "-C", root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, check=True).stdout
        return [p for p in out.decode().split("\0") if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return [os.path.relpath(os.path.join(d, n), root) for d, _, ns in os.walk(root) for n in ns]

root = sys.argv[sys.argv.index("--scan") + 1] if "--scan" in sys.argv else CORPUS
scanned = 0
for rel in sorted(files(root)):
    if rel in exempt and root == CORPUS:
        continue
    try:
        with open(os.path.join(root, rel), encoding="utf-8") as f:
            text = f.read()
    except (UnicodeDecodeError, IsADirectoryError, FileNotFoundError):
        continue
    scanned += 1
    for n, line in enumerate(text.splitlines(), 1):
        for m in NAMED.finditer(line):
            if m["family"] and m["family"] not in families:
                continue
            if m["ns"].lower() not in allowed:
                faults.append(f"{rel}:{n}: namespace {m['ns']!r} is neither reserved nor {own!r}")

print("\n".join(faults) or f"names: 0 findings in {scanned} files; {len(families)} families agree")
sys.exit(1 if faults else 0)
