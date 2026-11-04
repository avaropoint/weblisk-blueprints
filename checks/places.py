#!/usr/bin/env python3
"""Every place a standard names is a code of the shipped ISO 3166 list, and
the list is well formed.

    checks/places.py [--list FILE] [--standards DIR]

schemas/places/iso-3166.json is the list a standard's applies_in and an
organisation's operates_in are checked against (schemas/standard, applies_in;
architecture/orchestrator, operates_in). The check holds that the list names
its source, release and the digest of each file it was made from; that its
alpha-2 codes are two upper-case letters, sorted and unique; that every
subdivision code begins with its country's code and a hyphen and is listed
under that country; and that every applies_in entry of every standard under
standards/ is `international`, an alpha-2 code, an exceptionally reserved
code, or a subdivision code of the list, written by the rules schemas/standard
gives (`international` alone, ascending, no subdivision of a listed country).
"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, ".."))
lst = sys.argv[sys.argv.index("--list") + 1] if "--list" in sys.argv else os.path.join(CORPUS, "schemas/places/iso-3166.json")
sdir = sys.argv[sys.argv.index("--standards") + 1] if "--standards" in sys.argv else os.path.join(CORPUS, "standards")

d = json.load(open(lst, encoding="utf-8"))
faults = []
src = d.get("source") or {}
for k in ("url", "release", "commit", "files", "license", "fetched"):
    if not src.get(k):
        faults.append(f"the list names no source {k}")
for f, dg in (src.get("files") or {}).items():
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", dg or ""):
        faults.append(f"source file {f} has no sha256 digest")
alpha = d.get("alpha_2") or []
if alpha != sorted(set(alpha)) or not all(re.fullmatch(r"[A-Z]{2}", c) for c in alpha):
    faults.append("alpha_2 is not sorted, unique, two upper-case letters each")
subs = set()
for country, codes in (d.get("subdivisions") or {}).items():
    if country not in alpha:
        faults.append(f"subdivisions under {country}, which is no alpha-2 code")
    for c in codes:
        if not re.fullmatch(re.escape(country) + r"-[A-Z0-9]{1,3}", c):
            faults.append(f"subdivision {c} is not written {country}-<code>")
        subs.add(c)
places = set(alpha) | set(d.get("exceptionally_reserved") or {}) | subs

n = 0
for path in sorted(glob.glob(os.path.join(sdir, "*.json"))):
    s = json.load(open(path, encoding="utf-8"))
    if "applies_in" not in s:
        continue
    n += 1
    name, ai = os.path.basename(path), s["applies_in"]
    if "international" in ai and len(ai) > 1:
        faults.append(f"{name}: applies_in holds international beside a place")
    if ai != sorted(ai):
        faults.append(f"{name}: applies_in is not ascending")
    for c in ai:
        if c != "international" and c not in places:
            faults.append(f"{name}: applies_in names {c!r}, which is no ISO 3166 code of {src.get('release')}")
        if "-" in c and c.split("-")[0] in ai:
            faults.append(f"{name}: applies_in names {c} beside its country")
print("\n".join(faults) or f"places: {len(alpha)} countries and {len(subs)} subdivisions from iso-codes {src.get('release')}; "
      f"every applies_in of {n} standards names one")
sys.exit(1 if faults else 0)
