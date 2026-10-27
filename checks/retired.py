#!/usr/bin/env python3
"""RETIRED.md's entries, read as a tool reads them.

    checks/retired.py              the entries' form, against the table and the corpus
    checks/retired.py --file F     the same, for a copy of RETIRED.md at F
    checks/retired.py --scan       also: every place a retired spelling still appears
                                   where its entry does not allow it

The form is checked every time: one entry per table row, in order, naming
only spellings its row names; a closed `match` vocabulary; every path present;
every pattern compiling; every `until` a citation (schemas/names.md) of a file
that has not yet reached it. --scan reports leftovers; it is not a gate.
"""
import os, re, subprocess, sys
sys.dont_write_bytecode = True  # importing ids.py leaves no bytecode in the corpus
import yaml

CORPUS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(CORPUS, "checks"))
from ids import parse  # noqa: E402  the one parser of the id grammar here

MATCH = {"exact", "any-case", "sense"}
FIELDS = {"retired": {"spelling", "match"}, "allow": {"path", "why", "until"}, "other_senses": {"path", "pattern", "sense"}}
REQUIRED = {"retired": {"spelling", "match"}, "allow": {"path", "why"}, "other_senses": {"sense"}}

def version_of(rel):
    try:
        with open(os.path.join(CORPUS, rel), encoding="utf-8") as f:
            head = f.read(2000)
    except FileNotFoundError:
        return None
    m = re.search(r"^version:\s*['\"]?(\d+)\.(\d+)\.(\d+)", head, re.M)
    return tuple(map(int, m.groups())) if m else (0, 0, 0)

def entries_and_rows(text):
    m = re.search(r"^## Entries\n.*?```yaml\n(.*?)```", text, re.S | re.M)
    if not m:
        sys.exit("retired: no '## Entries' yaml block, so there is nothing to read")
    table = text[: text.index("## Entries")]
    rows = [l for l in table.splitlines() if l.startswith("| ") and not l.startswith("| Retired |")]
    firsts = [re.split(r"(?<!\\)\|", r)[1].replace("\\|", "|") for r in rows]
    return yaml.safe_load(m.group(1)) or [], firsts

def form(entries, firsts):
    faults = []
    if len(entries) != len(firsts):
        faults.append(f"{len(firsts)} table rows and {len(entries)} entries: each row has exactly one entry")
    for n, (e, first) in enumerate(zip(entries, firsts), 1):
        at = f"entry {n}"
        if not isinstance(e, dict) or not e.get("retired") or set(e) - set(FIELDS):
            faults.append(f"{at}: wants `retired` and only {sorted(FIELDS)}")
            continue
        for key, items in e.items():
            for item in items:
                if set(item) - FIELDS[key] or REQUIRED[key] - set(item):
                    faults.append(f"{at}: {key} item {item} wants {sorted(REQUIRED[key])}, may have {sorted(FIELDS[key])}")
                    continue
                if key == "retired" and f"`{item['spelling']}`" not in first:
                    faults.append(f"{at}: {item['spelling']!r} is not a spelling its row names")
                if key == "retired" and item["match"] not in MATCH:
                    faults.append(f"{at}: match {item['match']!r} is not one of {sorted(MATCH)}")
                if "path" in item and not os.path.exists(os.path.join(CORPUS, item["path"])):
                    faults.append(f"{at}: {item['path']} does not exist")
                if "pattern" in item:
                    try:
                        re.compile(item["pattern"])
                    except re.error as err:
                        faults.append(f"{at}: pattern {item['pattern']!r}: {err}")
                if "until" in item:
                    ref = parse(item["until"], set())
                    have = ref and ref["version"] and version_of(ref["local"] + ".md")
                    if not have:
                        faults.append(f"{at}: until {item['until']!r} is not a citation of a file here")
                    elif have >= tuple(map(int, ref["version"].split("-")[0].split("."))):
                        faults.append(f"{at}: {item['path']} is allowed until {item['until']}, and that file has reached it")
    return faults

def scan(entries):
    out = subprocess.run(["git", "-C", CORPUS, "ls-files", "-z"], capture_output=True, check=True).stdout
    texts = {}
    for rel in out.decode().split("\0"):
        if rel and rel != "RETIRED.md":
            try:
                with open(os.path.join(CORPUS, rel), encoding="utf-8") as f:
                    texts[rel] = f.read()
            except (UnicodeDecodeError, FileNotFoundError):
                pass
    # One pass per file: an alternation of every exact spelling, longest first,
    # and one search per any-case spelling. Each hit is then judged against
    # every entry that retires that spelling.
    by = {}
    for n, e in enumerate(entries):
        for s in e["retired"]:
            if s["match"] != "sense":  # current in another sense: no text search can tell them apart
                by.setdefault((s["match"], s["spelling"]), []).append(n)
    exact = sorted((sp for m, sp in by if m == "exact"), key=len, reverse=True)
    searches = [(re.compile(r"(?<![\w.-])(" + "|".join(map(re.escape, exact)) + r")(?![\w-])"), None)]
    searches += [(re.compile("(" + re.escape(sp) + ")", re.I), sp) for m, sp in by if m == "any-case"]
    skip = [{i["path"] for k in ("allow", "other_senses") for i in e.get(k, []) if "path" in i} for e in entries]
    kept = [[re.compile(i["pattern"]) for i in e.get("other_senses", []) if "pattern" in i] for e in entries]
    found = []
    for rel, t in texts.items():
        for rx, any_case in searches:
            for m in rx.finditer(t):
                for n in by[("any-case", any_case) if any_case else ("exact", m.group(1))]:
                    if rel in skip[n] or any(a <= m.start() < b for p in kept[n] for a, b in (x.span() for x in p.finditer(t))):
                        continue
                    found.append(f"{rel}:{t.count(chr(10), 0, m.start()) + 1}: {m.group(1)}")
    return found

if __name__ == "__main__":
    path = sys.argv[sys.argv.index("--file") + 1] if "--file" in sys.argv else os.path.join(CORPUS, "RETIRED.md")
    with open(path, encoding="utf-8") as f:
        entries, firsts = entries_and_rows(f.read())
    faults = form(entries, firsts)
    if "--scan" in sys.argv and not faults:
        faults = scan(entries)
    print("\n".join(faults) or f"retired: {len(entries)} entries agree with {len(firsts)} rows")
    sys.exit(1 if faults else 0)
