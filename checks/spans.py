#!/usr/bin/env python3
"""Every grammar vector has an expected projection, and each projection
partitions its file (schemas/family.md, requirement spans-partition): spans
sorted, contiguous and covering [0, length), at the file's own length and hash.
    checks/spans.py            check vectors/grammar/
    checks/spans.py --dir DIR  check DIR's vectors and projections instead"""
import glob, hashlib, json, os, sys

d = sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vectors", "grammar")
vectors = {p[:-3] for p in glob.glob(os.path.join(d, "*.md")) if not p.endswith("README.md")}
projections = {p[:-len(".projection.json")] for p in glob.glob(os.path.join(d, "*.projection.json"))}
faults = [f"{os.path.basename(v)}.md: no expected projection" for v in sorted(vectors - projections)]
faults += [f"{os.path.basename(p)}.projection.json: no vector" for p in sorted(projections - vectors)]
for base in sorted(vectors & projections):
    data, p, name = open(base + ".md", "rb").read(), json.load(open(base + ".projection.json")), os.path.basename(base)
    if os.path.basename(p["file"]) != name + ".md": faults.append(f"{name}: projection is of {p['file']}")
    if p["length"] != len(data): faults.append(f"{name}: length {p['length']}, file has {len(data)} bytes")
    if p["version_hash"] != "sha256:" + hashlib.sha256(data).hexdigest(): faults.append(f"{name}: version_hash is not the file's")
    at = 0
    for s, e in (q["span"] for q in p["parts"]):
        if s != at: faults.append(f"{name}: {'gap' if s > at else 'overlap'} at byte {min(s, at)}, part starts at {s}")
        if e <= s: faults.append(f"{name}: empty or reversed span [{s}, {e})")
        at = max(at, e)
    if at != len(data): faults.append(f"{name}: parts end at {at}, file at {len(data)}")
    faults += [f"{name}: finding {f['code']} outside the file" for f in p["findings"] if not 0 <= f["span"][0] <= f["span"][1] <= len(data)]
print("\n".join(faults) or f"spans: {len(vectors)} vectors, each partitioned by its projection")
sys.exit(1 if faults or not vectors else 0)
