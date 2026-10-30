"""No register specification carries `satisfies:`.

schemas/kinds.md, Relations: `implements` onto a control may be asserted only
by the kinds its row names (blueprint, policy, procedure). A register is the
evidence that work happened, not the document that answers a control, so a
register's citation can never be recorded as answering: it sits at
`present_uncited` permanently and caps its tier's readiness at a number no
work can move. The claim belongs on the policy or procedure that answers it.

The rule is read, not restated: the kinds allowed to assert `implements` are
taken from the Relations table, and the check fails if that row cannot be read
or if it admits `register` — in which case this check is wrong, not the corpus.
Every artifact specification under programmes/*/specs/ with `kind: register`
must then carry no `satisfies:`, at its top level or under
`declares.obligation`.

  register-satisfies.py [--root DIR]
"""
import glob, os, re, sys
import yaml

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")


def implementing_kinds():
    text = open(os.path.join(root, "schemas/kinds.md"), encoding="utf-8").read()
    m = re.search(r"^## Relations\n(.*?)(?=^## )", text, re.S | re.M)
    if not m:
        sys.exit("register-satisfies: schemas/kinds.md has no Relations section")
    row = re.search(r"^\| `implements` \| ([^|]+) \|", m.group(1), re.M)
    if not row:
        sys.exit("register-satisfies: the Relations table has no `implements` row")
    return {k.strip() for k in row.group(1).split(",")}


kinds = implementing_kinds()
if "register" in kinds:
    sys.exit("register-satisfies: schemas/kinds.md now lets a register assert `implements`; this check no longer holds and must be revisited")

faults, registers = [], 0
for f in sorted(glob.glob(os.path.join(root, "programmes/*/specs/*.md"))):
    m = re.match(r"---\n(.*?)\n---\n", open(f, encoding="utf-8").read(), re.S)
    if not m:
        continue
    h = yaml.safe_load(m.group(1)) or {}
    if h.get("kind") != "register":
        continue
    registers += 1
    where = os.path.relpath(f, root)
    if h.get("satisfies"):
        faults.append(f"{where}: a register carries satisfies {h['satisfies']}; only {', '.join(sorted(kinds))} may assert implements (schemas/kinds.md, Relations)")
    ob = (h.get("declares") or {}).get("obligation") or {}
    if ob.get("satisfies"):
        faults.append(f"{where}: a register's obligation carries satisfies {ob['satisfies']}; only {', '.join(sorted(kinds))} may assert implements (schemas/kinds.md, Relations)")

for x in faults:
    print(x)
if faults:
    sys.exit(1)
print(f"register-satisfies: {registers} register specifications, none carrying satisfies")
