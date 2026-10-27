#!/usr/bin/env python3
"""Each mapping's `timestamp` row, applied to vectors/conventions.json's instant binding, must give its wire value.
Usage: timestamp-wire.py [corpus-root] [--control]. --control first puts languages/go.md's row back in the older encoding, epoch seconds, in memory, and passes only if exactly that one disagreement is reported."""
import datetime, glob, json, os, re, sys
args = [a for a in sys.argv[1:] if a != "--control"]; control = "--control" in sys.argv
root = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
vec = json.load(open(os.path.join(root, "vectors/conventions.json")))["instant"]["binding"]
ms = vec["unix_ms"]
scale = {"seconds": 1, "milliseconds": 1000, "microseconds": 10**6, "nanoseconds": 10**9}


def wire(row):
    """The value a row's stated encoding gives the vector's instant, or None if it states none."""
    if re.search(r"RFC 3339 UTC with milliseconds", row):
        d = datetime.datetime.fromtimestamp(ms // 1000, datetime.timezone.utc)
        return d.strftime("%Y-%m-%dT%H:%M:%S") + ".%03dZ" % (ms % 1000)
    m = re.search(r"epoch (seconds|milliseconds|microseconds|nanoseconds)", row)
    return ms * scale[m.group(1)] // 1000 if m else None


found = []
for path in sorted(glob.glob(os.path.join(root, "languages/*.md")) + glob.glob(os.path.join(root, "platforms/*.md"))):
    rel = os.path.relpath(path, root); lines = open(path).read().split("\n")
    if rel.endswith("README.md"): continue
    if control and rel == "languages/go.md":
        lines = ["| `timestamp` | `int64` | Unix epoch seconds via `time.Now().Unix()` |" if l.startswith("| `timestamp` |") else l for l in lines]
    rows = [(i + 1, l) for i, l in enumerate(lines) if l.startswith("| `timestamp` |")]
    if not rows: found.append(f"{rel}: no `timestamp` row, so nothing says what it puts on the wire"); continue
    for n, row in rows:
        w = wire(row)
        if w is None: found.append(f"{rel}:{n}: unreadable, names no encoding: {row}"); continue
        if w != vec["wire"]: found.append(f"{rel}:{n}: gives {w!r}, the vector says {vec['wire']!r}")
if found: print("\n".join(found))
print(f"disagreements: {len(found)}")
if control: sys.exit(0 if len(found) == 1 and found[0].startswith("languages/go.md:") else 1)
sys.exit(1 if found else 0)
