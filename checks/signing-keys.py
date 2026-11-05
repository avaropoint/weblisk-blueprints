#!/usr/bin/env python3
"""protocol/identity's Which key signs what agrees with its Fixed-Form
Statements registry, and the structure check that reads a component's source
for an unregistered prefix is given exactly the registry.

Usage: signing-keys.py [--file F]

- Every prefix the table's Form column names is one the registry lists, so the
  table can name no statement nobody may sign (an invented
  weblisk/register/v1 was one).
- A registering component's key has a row signing its registration manifest
  under Sign JSON, so no signer drawn from the table refuses a registration.
- A log key's rows sign weblisk/log-checkpoint/v2 and nothing else.
- Every verifies entry whose structure query is unregistered-statement-prefix
  carries args.registered equal to the registry, neither more nor fewer, so
  the check cannot pass a prefix the registry dropped nor fail one it added.
"""
import os, re, sys

import yaml

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
args = sys.argv[1:]
path = os.path.join(root, "protocol/identity.md")
while args:
    a = args.pop(0)
    if a == "--file":
        path = args.pop(0)
    else:
        sys.exit(f"unknown argument {a}")

text = open(path, encoding="utf-8").read()
registered = re.findall(r"^\| `(weblisk/[a-z0-9-]+/v\d+)` \|", text, re.M)
found = []
if not registered:
    found.append("the Fixed-Form Statements registry lists no prefix")

m = re.search(r"^### Which key signs what\n(.*?)^### ", text, re.S | re.M)
if not m:
    found.append("protocol/identity has no section Which key signs what")
    rows = []
else:
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("| ") or line.startswith("| Key |") or line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split(" | ")]
        if len(cells) != 5:
            found.append(f"a row of Which key signs what has {len(cells)} cells, not 5: {line[:80]}")
            continue
        rows.append(cells)
    if not rows:
        found.append("Which key signs what has no rows")

for key, _, signs, form, _ in rows:
    for p in re.findall(r"`(weblisk/[a-z0-9-]+/v\d+)`", form):
        if p not in registered:
            found.append(f"Which key signs what: {key!r} signs {p}, which the registry does not list")
if rows:
    comp = [r for r in rows if r[0].startswith("A registering component's key")]
    if not any("registration manifest" in r[2] and "Sign JSON" in r[3] for r in comp):
        found.append("Which key signs what: no row has a registering component's key sign its registration manifest under Sign JSON")
    log = [r for r in rows if r[0] == "A log key"]
    forms = {p for r in log for p in re.findall(r"`(weblisk/[a-z0-9-]+/v\d+)`", r[3])}
    if not log or forms != {"weblisk/log-checkpoint/v2"} or any("Sign JSON" in r[3] for r in log):
        found.append(f"Which key signs what: a log key signs {sorted(forms) or 'nothing'}, not weblisk/log-checkpoint/v2 alone")

seen = 0
for f in re.finditer(r"^```yaml\n(.*?)^```", text, re.S | re.M):
    try:
        v = yaml.safe_load(f.group(1))
    except yaml.YAMLError:
        continue
    if not isinstance(v, dict) or not isinstance(v.get("verifies"), list):
        continue
    for e in v["verifies"]:
        s = e.get("structure") if isinstance(e, dict) else None
        if not isinstance(s, dict) or s.get("query") != "unregistered-statement-prefix":
            continue
        seen += 1
        given = ((s.get("args") or {}).get("registered")) or []
        extra = sorted(set(given) - set(registered))
        missing = sorted(set(registered) - set(given))
        if extra:
            found.append(f"check {e.get('id')!r}: args.registered names {extra}, which the registry does not list")
        if missing:
            found.append(f"check {e.get('id')!r}: args.registered lacks {missing}, which the registry lists")
if not seen:
    found.append("no verifies entry runs unregistered-statement-prefix")

for x in found:
    print(x)
if found:
    sys.exit(1)
print(f"signing-keys: {len(rows)} rows, {len(registered)} registered prefixes, {seen} structure check(s) given exactly the registry")
