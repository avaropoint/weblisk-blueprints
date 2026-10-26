#!/usr/bin/env python3
"""No text says the service directory push is unauthenticated.

Usage: push-claims.py [FILE...]

protocol/spec POST /v1/services signs the push and has an agent verify it, so
a sentence saying the directory's signature has no signing input, that nothing
authenticates a push, or that a pushed body is whatever its sender sent, is a
false statement about the spec, and its pointer to "the gap there" names a gap
that is now about a task's context.services. Whitespace, line breaks and
markdown backticks are ignored, so a sentence wrapped across lines is found.
With no FILE, every .md file in the corpus outside checks/ is read.
"""
import glob, os, re, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# checks/ is left out: its README names the claims this check refuses.
files = sys.argv[1:] or sorted(p for p in glob.glob(os.path.join(root, "**/*.md"), recursive=True)
                               if "/node_modules/" not in p and os.path.relpath(p, root).split(os.sep)[0] != "checks")

CLAIMS = [
    r"has no signing input",
    r"no signing input yet",
    r"nothing authenticates a push",
    r"pushed to (?:its|the \w+'s|an agent's) POST /v1/services is (?:unauthenticated|whatever)",
    r"push(?:ed)? (?:body )?is unauthenticated",
]
found = []
for path in files:
    rel = os.path.relpath(path, root) if os.path.abspath(path).startswith(os.path.abspath(root)) else path
    raw = open(path, encoding="utf-8").read()
    flat, where = [], []
    for i, ch in enumerate(raw):
        if ch == "`": continue
        c = " " if ch.isspace() else ch
        if c == " " and flat and flat[-1] == " ": continue
        flat.append(c); where.append(i)
    text = "".join(flat)
    for claim in CLAIMS:
        for m in re.finditer(claim, text, re.I):
            line = raw.count("\n", 0, where[m.start()]) + 1
            found.append(f"{rel}:{line}: says the directory push is unauthenticated: {m.group(0)!r}")
if found: print("\n".join(found))
print(f"{len(files)} files, {len(found)} findings")
sys.exit(1 if found else 0)
