"""patterns/content-identity's digest-spelling rule says every digest written as
one string reads sha256:<hex>, and names each place bare hex is still written
as a gap. This holds that list to the corpus both ways:

- every sentence in a blueprint that describes a SHA-256 as hex without the
  sha256: prefix is in a file the gap rule names, so a new bare-hex field
  cannot arrive unnamed;
- every file the gap rule names still has such a sentence, so the list
  shrinks when a blueprint adopts the spelling.

A key fingerprint is protocol/identity's identity id and keeps its own form
(the same rule says so); a sentence that names a fingerprint is not a digest.

  digest-spelling.py [--root DIR]
"""
import os, re, sys

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")
RULE = "patterns/content-identity.md"
BLUEPRINT = re.compile(r"\b((?:architecture|protocol|patterns|schemas|domains|agents)/[a-z0-9-]+)\b")
BARE = re.compile(r"SHA-256[^.;|]{0,80}?\bhex\b|\bhex\b[^.;|]{0,30}?SHA-256")


def gap_files():
    text = open(os.path.join(root, RULE), encoding="utf-8").read()
    rule = [line for line in text.split("\n") if "Bare hex is still written" in line]
    if len(rule) != 1:
        sys.exit(f"{RULE}: want exactly one gap rule ('Bare hex is still written'), found {len(rule)}")
    return {m + ".md" for m in BLUEPRINT.findall(rule[0]) if not m.startswith("patterns/content-identity")}


def bare_sentences():
    found = {}
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for name in files:
            if not name.endswith(".md"):
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if rel == RULE:
                continue
            text = re.sub(r"\s+", " ", open(full, encoding="utf-8").read())
            for m in BARE.finditer(text):
                window = text[max(0, m.start() - 40):m.end() + 40]
                if "sha256:" in window or "fingerprint" in window:
                    continue
                found.setdefault(rel, []).append(m.group(0))
    return found


named, found = gap_files(), bare_sentences()
faults = []
for rel in sorted(set(found) - named):
    faults.append(f"{rel}: writes a bare-hex SHA-256 ({found[rel][0]!r}) that {RULE}'s gap rule does not name")
for rel in sorted(named - set(found)):
    faults.append(f"{rel}: named in {RULE}'s gap rule, but describes no bare-hex SHA-256")
for f in faults:
    print(f)
if not faults:
    print(f"digest-spelling: bare hex is written in {len(named)} files, each named as a gap")
sys.exit(1 if faults else 0)
