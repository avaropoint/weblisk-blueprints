#!/usr/bin/env python3
"""A console's source holds no record statement and drives no signer
(architecture/admin, console-credential-use: console-hands-off-signing,
console-never-drives-signer; the checks console-builds-no-record-statement
and console-drives-no-signer).

    checks/console-signing.py --scan DIR     every source file under DIR

Read from the corpus and nowhere else: the prefixes protocol/identity's
Fixed-Form Statements registry says a person's sign-records credential signs,
and the pointer operations of its section "A signer acting on a pointer".
Reported, one line each, for every .go, .js, .mjs, .ts and .tsx file under DIR
that is not a test:

- console-builds-no-record-statement: a string literal equal to one of those
  prefixes;
- console-drives-no-signer: a string literal equal to a pointer operation of
  more than one word (one word, such as attest, only on a line that invokes
  the CLI); a line that invokes the CLI (it names `exec.Command`, `cliPath` or the string
  "weblisk") and holds the string "sign", or "change" with "approve" or
  "reject"; and the string "--yes" anywhere, or "--confirm" on such a line.

A structure check over text, not a parse: it finds literals and argv on one
line, which is the shape every CLI invocation in a console has today.
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import yaml  # noqa: E402

EXT = (".go", ".js", ".mjs", ".ts", ".tsx")
LIT = re.compile(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'|`([^`]*)`")
INVOKES = re.compile(r"exec\.Command|cliPath|[\"']weblisk[\"']")


def registry():
    text = open(os.path.join(CORPUS, "protocol/identity.md"), encoding="utf-8").read()
    prefixes = []
    for m in re.finditer(r"^\| `(weblisk/[^`]+)` \| ([^|]+) \|", text, re.M):
        if m.group(2).strip().startswith("A person's sign-records credential"):
            prefixes.append(m.group(1))
    i = text.find("### A signer acting on a pointer")
    ops = []
    for m in re.finditer(r"^```yaml\n(.*?)^```", text[i:], re.S | re.M):
        v = yaml.safe_load(m.group(1))
        if isinstance(v, dict) and "pointer_operations" in v:
            ops = [e["pointer"] for e in v["pointer_operations"]]
            break
    return prefixes, ops


def is_test(path):
    b = os.path.basename(path)
    return b.endswith("_test.go") or ".test." in b or ".spec." in b or "/tests/" in path.replace(os.sep, "/")


def scan(root, prefixes, ops):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in (".git", "node_modules", "vendor")]
        for f in sorted(files):
            p = os.path.join(d, f)
            if not f.endswith(EXT) or is_test(p):
                continue
            try:
                lines = open(p, encoding="utf-8").read().split("\n")
            except (UnicodeDecodeError, OSError):
                continue
            rel = os.path.relpath(p, root)
            for n, line in enumerate(lines, 1):
                lits = [next(g for g in m.groups() if g is not None) for m in LIT.finditer(line)]
                invokes = bool(INVOKES.search(line))
                for s in lits:
                    if s in prefixes:
                        out.append(f"{rel}:{n}: console-builds-no-record-statement: the literal {s!r}")
                    if s in ops and ("-" in s or invokes):
                        out.append(f"{rel}:{n}: console-drives-no-signer: the pointer operation {s!r}")
                    if s == "--yes" or (s == "--confirm" and invokes):
                        out.append(f"{rel}:{n}: console-drives-no-signer: the flag {s!r}")
                if invokes and ("sign" in lits or ("change" in lits and ({"approve", "reject"} & set(lits)))):
                    out.append(f"{rel}:{n}: console-drives-no-signer: an invocation of the CLI for an act that needs a signature")
    return out


def main():
    if "--scan" not in sys.argv:
        print("usage: console-signing.py --scan DIR")
        return 2
    root = sys.argv[sys.argv.index("--scan") + 1]
    prefixes, ops = registry()
    if not prefixes or not ops:
        print("console-signing: protocol/identity names no sign-records prefix or no pointer operation; nothing to hold a console to")
        return 1
    faults = scan(root, prefixes, ops)
    for f in faults:
        print(f)
    if faults:
        return 1
    print(f"console-signing: {root} holds none of {len(prefixes)} sign-records prefixes and drives no signer "
          f"({len(ops)} pointer operations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
