#!/usr/bin/env python3
"""Requirement ids carried in comments, and the checklist items that cover them.

    checks/requirement-ids.py           every file in this corpus
    checks/requirement-ids.py --file F  one file, read from F

A requirement is marked `<!-- wl:id <id> -->`, in its sentence or, for a rule
in a YAML list, on a comment line directly above it. A checklist item that
verifies requirements carries `<!-- wl:check <id> covers <id> ... -->`.
Today's parsers skip both, and the corpus's migration turns them into its
requirement and `verifies` ids unchanged.

In every file: each id is kebab-case and is declared once, each wl:check
covers at least one id, and every id a covers names is a wl:id of that file.
In a file marked `<!-- wl:ids complete -->` also: every statement that says
MUST carries a wl:id, and every wl:id is covered by at least one wl:check.
A statement is a paragraph, a list item, a table row, a blockquote, or one
rule of a YAML list; code spans and comments are not read for MUST, and
checklist items are checks rather than statements.
"""
import os, re, sys

CORPUS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
WL_ID = re.compile(r"<!--\s*wl:id\s+(\S+)\s*-->")
WL_CHECK = re.compile(r"<!--\s*wl:check\s+(\S+)\s+covers\s+([^>]*?)\s*-->")
COMPLETE = "<!-- wl:ids complete -->"
MARKER = re.compile(r"^\s*(?:[-*+]\s|\d+\.\s|\|)")


def statements(text):
    """(line number, text, ids on comment lines just above it) per statement."""
    out, unit, start, own, pending, fence = [], [], 0, [], [], None

    def close():
        nonlocal unit, own
        if unit:
            out.append((start, "\n".join(unit), own))
        unit, own = [], []

    def begin(n, line):
        nonlocal start, unit, own, pending
        close()
        start, unit, own, pending = n, [line], pending, []

    for n, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if s.startswith("```"):
            close()
            pending = []
            fence = None if fence else s
            continue
        if fence:
            if s.startswith("#"):  # a YAML comment: an id here marks the rule below
                pending += WL_ID.findall(s)
            elif re.match(r"-\s", s):  # one rule, one line
                begin(n, line)
                close()
            else:
                close()
                pending = []
            continue
        if not s or s.startswith("#"):
            close()
            pending = []
        elif re.match(r"[-*+]\s\[[ xX]\]", s):  # a checklist item is a check
            close()
            pending = []
        elif re.fullmatch(r"<!--.*-->", s):  # an id on its own line marks what follows
            close()
            pending += WL_ID.findall(s)
        elif s.startswith(">"):
            if unit and unit[-1].lstrip().startswith(">"):
                unit.append(line)
            else:
                begin(n, line)
        elif (MARKER.match(line) and not line.startswith((" ", "\t"))) or not unit:
            begin(n, line)
        else:
            unit.append(line)
    close()
    return out


def is_complete(text):
    return re.search(r"^" + re.escape(COMPLETE) + r"$", text, re.M) is not None


def says_must(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "", text)
    return re.search(r"\bMUST\b", text) is not None


def check(name, text):
    faults = []
    ids = {}
    for n, line in enumerate(text.split("\n"), 1):
        for i in WL_ID.findall(line):
            if not KEBAB.fullmatch(i):
                faults.append(f"{name}:{n}: wl:id {i!r} is not kebab-case")
            if i in ids:
                faults.append(f"{name}:{n}: wl:id {i!r} is declared again (first at line {ids[i]})")
            ids.setdefault(i, n)
    checks, covered = {}, {}
    for n, line in enumerate(text.split("\n"), 1):
        for c, cov in WL_CHECK.findall(line):
            if not KEBAB.fullmatch(c):
                faults.append(f"{name}:{n}: wl:check {c!r} is not kebab-case")
            if c in checks:
                faults.append(f"{name}:{n}: wl:check {c!r} is declared again (first at line {checks[c]})")
            checks.setdefault(c, n)
            targets = cov.split()
            if not targets:
                faults.append(f"{name}:{n}: wl:check {c!r} covers nothing")
            for t in targets:
                if t not in ids:
                    faults.append(f"{name}:{n}: wl:check {c!r} covers {t!r}, which no wl:id in this file declares")
                covered.setdefault(t, n)
        if "<!-- wl:check" in line and not WL_CHECK.search(line):
            faults.append(f"{name}:{n}: a wl:check comment that does not read as 'wl:check <id> covers <id>...'")
    if is_complete(text):
        for n, body, above in statements(text):
            if says_must(body) and not WL_ID.search(body) and not above:
                first = body.strip().split("\n")[0][:90]
                faults.append(f"{name}:{n}: a MUST with no wl:id: {first}")
        for i, n in sorted(ids.items(), key=lambda kv: kv[1]):
            if i not in covered:
                faults.append(f"{name}:{n}: wl:id {i!r} is covered by no wl:check")
    return faults


def main():
    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
        files = [(path, path)]
    else:
        files = []
        for root, dirs, names in os.walk(CORPUS):
            dirs[:] = sorted(d for d in dirs if not d.startswith("."))
            for f in sorted(names):
                if f.endswith(".md"):
                    p = os.path.join(root, f)
                    files.append((os.path.relpath(p, CORPUS), p))
    faults, marked, total = [], 0, 0
    for name, path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if "<!-- wl:id" not in text and "<!-- wl:check" not in text:
            continue
        total += 1
        marked += is_complete(text)
        faults += check(name, text)
    print("\n".join(faults) or f"requirement-ids: {total} files carry ids, {marked} of them complete")
    sys.exit(1 if faults else 0)


if __name__ == "__main__":
    main()
