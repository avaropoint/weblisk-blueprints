#!/usr/bin/env python3
"""The share of a family's bytes that no slot declares, over the files written
to it: those its `match` covers whose header names it, or which are still in
the older form (a first line opening `<!-- blueprint`). A byte is in the slot
whose heading opens the part of the file holding it (schemas/family.md,
slots-by-heading); bytes before the first heading, and under a level-2 heading
no slot matches, are in none. Fences and comments are opaque (fences-are-opaque).
    checks/coverage.py FAMILY                          e.g. schemas/architecture
    checks/coverage.py FAMILY --decl FILE              read the declaration from FILE
    checks/coverage.py FAMILY --expect PCT --within PTS  fail outside PCT +/- PTS"""
import glob, os, re, sys
import yaml  # PyYAML

def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default
root = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
family = sys.argv[1]
text = open(arg("--decl", os.path.join(root, family + ".md")), encoding="utf-8-sig").read().replace("\r\n", "\n")
blocks = [yaml.safe_load(m.group(1)) for m in re.finditer(r"^```yaml\n(.*?)^```", text, re.S | re.M)]
sections = next((b["sections"] for b in blocks if isinstance(b, dict) and list(b) == ["sections"]), None)
head = re.match(r"---\n(.*?)\n---\n", text, re.S)
if not sections or not head: sys.exit(f"coverage: {family} declares no sections, so nothing can be measured")
decl = yaml.safe_load(head.group(1))
name = f"{family}@{decl['version'].split('.')[0]}"
norm = lambda s: " ".join(s.split())
def slot_of(level, h):
    for s in sections["slots"]:
        want = s["heading"]
        if level == 1: hit = isinstance(want, dict) and want.get("level") == 1
        else: hit = (isinstance(want, str) and norm(want) == h) or h in map(norm, s.get("aliases", [])) \
              or (isinstance(want, dict) and "starts_with" in want and h.startswith(norm(want["starts_with"])))
        if hit: return s["slot"]
    return None
files = sorted({f for pat in decl["match"] for f in glob.glob(os.path.join(root, pat), recursive=True)})
counts, total, skipped = {}, 0, []
for f in files:
    data = open(f, "rb").read()
    lines = data.splitlines(keepends=True)
    first = lines[0].lstrip(b"\xef\xbb\xbf").rstrip(b"\r\n") if lines else b""
    hdr = first == b"---" and next((i for i in range(1, len(lines)) if lines[i].rstrip(b"\r\n") == b"---"), None)
    if not (hdr and re.search(rb"(?m)^family: *" + re.escape(name.encode()) + rb"\r?$", b"".join(lines[:hdr]))) \
            and not first.startswith(b"<!-- blueprint"):
        skipped.append(os.path.relpath(f, root)); continue
    slot, fence, comment = None, None, False
    for i, ln in enumerate(lines):
        s = ln.decode("utf-8").rstrip("\r\n")
        if hdr and i <= hdr: pass
        elif fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{%d,}[ \t]*" % len(fence), s): fence = None
        elif comment: comment = "-->" not in s
        elif m := re.match(r" {0,3}(`{3,}|~{3,})(.*)", s):
            if not (m.group(1)[0] == "`" and "`" in m.group(2)): fence = m.group(1)
        elif re.match(r" {0,3}<!--", s): comment = "-->" not in s[s.index("<!--") + 4:]
        elif m := re.fullmatch(r" {0,3}(#{1,2}) (.*)", s): slot = slot_of(len(m.group(1)), norm(m.group(2)))
        counts[slot] = counts.get(slot, 0) + len(ln)
    total += len(data)
share = 100 * counts.get(None, 0) / total if total else 0
for s, n in sorted(counts.items(), key=lambda x: -x[1]): print(f"{str(s or '(no slot)'):24} {n:9} {100 * n / total:5.1f}%")
print(f"coverage: {len(files) - len(skipped)} files of {name}, {total} bytes, {share:.1f}% in no slot" + (f"; not written to it: {', '.join(skipped)}" if skipped else ""))
if not total: sys.exit(f"coverage: no file is written to {name}")
if "--expect" in sys.argv and abs(share - float(arg("--expect"))) > float(arg("--within")):
    print(f"coverage: {share:.1f}% is not within {arg('--within')} points of {arg('--expect')}%"); sys.exit(1)
