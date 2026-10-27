#!/usr/bin/env python3
"""Requirement and check ids carried in today's files as HTML comments, which
today's parsers skip and the migration to verifies blocks keeps.

Usage: wl-ids.py [--require FILE:CHECK]... [FILE...]

A requirement is marked <!-- wl:id <id> -->, and a check
<!-- wl:check <id> covers <id>... -->. In each file: no id is marked twice,
every check covers at least one id, every id a check covers is marked in that
file, and every marked id is covered by some check. --require fails unless
FILE marks a check CHECK. With no FILE, every .md file in the corpus is read.
"""
import glob, os, re, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
args, required, files = sys.argv[1:], [], []
while args:
    a = args.pop(0)
    if a == "--require": required.append(args.pop(0).split(":", 1))
    else: files.append(a)
if not files:
    files = sorted(p for p in glob.glob(os.path.join(root, "**/*.md"), recursive=True) if "/node_modules/" not in p)

ID = r"[a-z0-9]+(?:-[a-z0-9]+)*"
found, marked_checks, total = [], {}, 0
for path in files:
    rel = os.path.relpath(path, root) if os.path.abspath(path).startswith(os.path.abspath(root)) else path
    text = open(path, encoding="utf-8").read()
    ids, checks = {}, {}
    for m in re.finditer(r"<!--\s*wl:(id|check)\b(.*?)-->", text, re.S):
        line = text.count("\n", 0, m.start()) + 1
        kind, rest = m.group(1), m.group(2).split()
        if kind == "id":
            if len(rest) != 1 or not re.fullmatch(ID, rest[0]):
                found.append(f"{rel}:{line}: unreadable wl:id {m.group(0)}"); continue
            if rest[0] in ids: found.append(f"{rel}:{line}: wl:id {rest[0]} is also marked at line {ids[rest[0]]}")
            ids.setdefault(rest[0], line)
        else:
            if len(rest) < 1 or not re.fullmatch(ID, rest[0]) or (len(rest) > 1 and rest[1] != "covers") or not all(re.fullmatch(ID, c) for c in rest[2:]):
                found.append(f"{rel}:{line}: unreadable wl:check {m.group(0)}"); continue
            if rest[0] in checks: found.append(f"{rel}:{line}: wl:check {rest[0]} is also marked at line {checks[rest[0]][0]}")
            if len(rest) < 3: found.append(f"{rel}:{line}: wl:check {rest[0]} covers nothing")
            checks.setdefault(rest[0], (line, rest[2:]))
    total += len(ids) + len(checks)
    covered = set()
    for c, (line, covers) in checks.items():
        for i in covers:
            covered.add(i)
            if i not in ids: found.append(f"{rel}:{line}: wl:check {c} covers {i}, which this file does not mark")
    for i, line in ids.items():
        if i not in covered: found.append(f"{rel}:{line}: wl:id {i} is covered by no wl:check")
    marked_checks[rel] = set(checks)
for f, c in required:
    if c not in marked_checks.get(f, set()): found.append(f"{f}: marks no wl:check {c}")

if found: print("\n".join(found))
print(f"{len(files)} files, {total} ids and checks, {len(found)} findings")
sys.exit(1 if found else 0)
