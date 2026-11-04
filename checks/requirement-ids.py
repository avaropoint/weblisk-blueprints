#!/usr/bin/env python3
"""Requirement ids carried in comments, criterion ids on checklist items, and
the register that freezes them.

    checks/requirement-ids.py                       every file in this corpus
    checks/requirement-ids.py --file F [--as REL]   one file, read from F, held to the register as REL
    checks/requirement-ids.py --register R          hold the files to register R instead of
                                                    checks/criterion-ids.json

A requirement is marked `<!-- wl:id <id> -->`, in its sentence or, for a rule
in a YAML list, on a comment line directly above it. A checklist item is a
criterion (ENGINE_PLAN.md, section 5) and carries its id as
`<!-- wl:check <id> -->`, or `<!-- wl:check <id> covers <id> ... -->` where it
verifies marked requirements. That comment is today's spelling of a `verifies`
entry (schemas/blocks.md, "Checks"): its id, and its `covers`; its `check` is
`translated` unless a `verifies` entry of the same id declares a kind.

In every file: each id is kebab-case and is declared once, a wl:check that
says `covers` covers at least one id, and every id a covers names is a wl:id
of that file. In a file marked `<!-- wl:ids complete -->` also: every
statement that says MUST carries a wl:id, and every wl:id is covered by at
least one wl:check. A statement is a paragraph, a list item, a table row, a
blockquote, or one rule of a YAML list; code spans and comments are not read
for MUST, and checklist items are checks rather than statements.

In every file under the directories that hold blueprints
(checks/criterion_ids.py): every criterion carries exactly one wl:check, and
the ids are frozen by checks/criterion-ids.json (decision 9). Every id the
register gives a file is still written in it, every wl:check written is in the
register, and no id the register has retired is written again. So an id can be
neither changed, dropped nor reused; checks/mint-criterion-ids.py mints and
registers new ones, and `--retire FILE:ID` retires one whose item was removed.
"""
import os, re, sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from criterion_ids import WL_CHECK_ANY, criteria, in_scope, load_register  # noqa: E402

CORPUS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
WL_ID = re.compile(r"<!--\s*wl:id\s+(\S+)\s*-->")
WL_CHECK = re.compile(r"<!--\s*wl:check\s+(\S+)(\s+covers\b)?\s*([^>]*?)\s*-->")
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
        for c, says_covers, cov in WL_CHECK.findall(line):
            if not KEBAB.fullmatch(c):
                faults.append(f"{name}:{n}: wl:check {c!r} is not kebab-case")
            if c in checks:
                faults.append(f"{name}:{n}: wl:check {c!r} is declared again (first at line {checks[c]})")
            checks.setdefault(c, n)
            targets = cov.split()
            if cov and not says_covers:
                faults.append(f"{name}:{n}: wl:check {c!r} is followed by {cov!r}, not by 'covers'")
                targets = []
            elif says_covers and not targets:
                faults.append(f"{name}:{n}: wl:check {c!r} covers nothing")
            for t in targets:
                if t not in ids:
                    faults.append(f"{name}:{n}: wl:check {c!r} covers {t!r}, which no wl:id in this file declares")
                covered.setdefault(t, n)
        if "<!-- wl:check" in line and not WL_CHECK.search(line):
            faults.append(f"{name}:{n}: a wl:check comment that does not read as 'wl:check <id> [covers <id>...]'")
    if is_complete(text):
        for n, body, above in statements(text):
            if says_must(body) and not WL_ID.search(body) and not above:
                first = body.strip().split("\n")[0][:90]
                faults.append(f"{name}:{n}: a MUST with no wl:id: {first}")
        for i, n in sorted(ids.items(), key=lambda kv: kv[1]):
            if i not in covered:
                faults.append(f"{name}:{n}: wl:id {i!r} is covered by no wl:check")
    return faults


def frozen(name, text, register):
    """The criterion rules: one wl:check per item, and the register's ids held."""
    faults = []
    for first, _, item in criteria(text):
        n = len(WL_CHECK_ANY.findall(item))
        if n != 1:
            what = "no id" if n == 0 else f"{n} ids"
            faults.append(f"{name}:{first + 1}: a checklist item with {what}: {item.strip()[:80]}")
    written = {}
    for n, line in enumerate(text.split("\n"), 1):
        for m in WL_CHECK_ANY.finditer(line):
            written.setdefault(m.group(1), n)
    given = register.get("files", {}).get(name, [])
    retired = set(register.get("retired", {}).get(name, []))
    for i in given:
        if i not in written:
            faults.append(f"{name}: registered id {i!r} is no longer written; an id never changes, "
                          "and a removed item's id is retired (mint-criterion-ids.py --retire)")
    for i, n in sorted(written.items(), key=lambda kv: kv[1]):
        if i in retired:
            faults.append(f"{name}:{n}: id {i!r} was retired and is never given again")
        elif i not in given:
            faults.append(f"{name}:{n}: id {i!r} is not in the register (mint-criterion-ids.py registers it)")
    return faults


def main():
    register = load_register(sys.argv[sys.argv.index("--register") + 1]) if "--register" in sys.argv else load_register()
    if "--file" in sys.argv:
        path = sys.argv[sys.argv.index("--file") + 1]
        name = sys.argv[sys.argv.index("--as") + 1] if "--as" in sys.argv else path
        files = [(name, path)]
    else:
        files = []
        for root, dirs, names in os.walk(CORPUS):
            dirs[:] = sorted(d for d in dirs if not d.startswith("."))
            for f in sorted(names):
                if f.endswith(".md"):
                    p = os.path.join(root, f)
                    files.append((os.path.relpath(p, CORPUS), p))
    faults, marked, total, held = [], 0, 0, 0
    for name, path in files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if in_scope(name):
            held += len(criteria(text))
            faults += frozen(name, text, register)
        if "<!-- wl:id" not in text and "<!-- wl:check" not in text:
            continue
        total += 1
        marked += is_complete(text)
        faults += check(name, text)
    print("\n".join(faults) or f"requirement-ids: {total} files carry ids, {marked} of them complete; {held} criteria, each with a frozen id")
    sys.exit(1 if faults else 0)


if __name__ == "__main__":
    main()
