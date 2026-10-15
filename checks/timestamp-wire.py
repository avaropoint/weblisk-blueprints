#!/usr/bin/env python3
"""Each mapping's `timestamp` row, applied to vectors/timestamp-wire.json's instant, must give its wire value.
Usage: timestamp-wire.py [corpus-root] [--control]. --control first rewrites languages/go.md's row to milliseconds, in memory, and passes only if exactly that one disagreement is reported."""
import datetime, glob, json, os, re, sys
args = [a for a in sys.argv[1:] if a != "--control"]; control = "--control" in sys.argv
root = args[0] if args else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
vec = json.load(open(os.path.join(root, "vectors/timestamp-wire.json")))
t = datetime.datetime.fromisoformat(vec["instant"].replace("Z", "+00:00")).timestamp()
scale = {"seconds": 1, "milliseconds": 1000, "microseconds": 10**6, "nanoseconds": 10**9}
found = []
for path in sorted(glob.glob(os.path.join(root, "languages/*.md")) + glob.glob(os.path.join(root, "platforms/*.md"))):
    rel = os.path.relpath(path, root); lines = open(path).read().split("\n")
    if rel.endswith("README.md"): continue
    if control and rel == "languages/go.md": lines = [l.replace("epoch seconds", "epoch milliseconds") if l.startswith("| `timestamp` |") else l for l in lines]
    rows = [(i + 1, l) for i, l in enumerate(lines) if l.startswith("| `timestamp` |")]
    if not rows: found.append(f"{rel}: no `timestamp` row, so nothing says what it puts on the wire"); continue
    for n, row in rows:
        m = re.search(r"epoch (seconds|milliseconds|microseconds|nanoseconds)", row)
        if not m: found.append(f"{rel}:{n}: unreadable, names no epoch unit: {row}"); continue
        if int(t * scale[m.group(1)]) != vec["wire"]: found.append(f"{rel}:{n}: gives {int(t * scale[m.group(1)])} ({m.group(1)}), the vector says {vec['wire']}")
if found: print("\n".join(found))
print(f"disagreements: {len(found)}")
if control: sys.exit(0 if len(found) == 1 and found[0].startswith("languages/go.md:") else 1)
sys.exit(1 if found else 0)
