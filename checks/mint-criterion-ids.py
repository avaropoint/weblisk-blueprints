#!/usr/bin/env python3
"""Give every criterion that has no id a permanent one, and register it.

    checks/mint-criterion-ids.py                 mint ids for every criterion that lacks one, write
                                                 them into its file, and add them to the register
    checks/mint-criterion-ids.py --dry-run       print what would be minted, and change nothing
    checks/mint-criterion-ids.py --register-only add ids already written in the files to the register
    checks/mint-criterion-ids.py --retire FILE:ID
                                                 move a registered id to the file's retired list,
                                                 after its item has been removed

A criterion is what checks/criterion_ids.py says (ENGINE_PLAN.md, section 5,
"The unit is a criterion"; decision 9). Its id is minted ONCE, from its text at
the time of minting: the first content words of the item, in kebab-case, made
unique within its file. It is then frozen. Nothing ever derives it again: an
edit to the item's text keeps its id, and requirement-ids.py refuses an id
that changes, disappears without being retired, or is given again.

The id is written as `<!-- wl:check <id> -->` at the end of the item's last
line, the spelling a `wl:check` already has, so an item that verifies marked
requirements keeps `covers` and one that does not is its own criterion.
"""
import os, re, sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from criterion_ids import CORPUS, WL_CHECK_ANY, criteria, files, load_register, save_register  # noqa: E402

WL_ID = re.compile(r"<!--\s*wl:id\s+(\S+)\s*-->")
# Words that carry no meaning in an id. Negations stay: "refused" and "not
# refused" must not mint the same id.
STOP = set("""
a an the is are be been being was were of to in on at by for from with as into onto upon
and or but if then than that which who whom whose this these those it its it's there their
each every any all some both either neither one same such so also only just
has have had do does did can may must should shall will would could
""".split())
MAX_WORDS, MAX_LEN = 6, 48
# A word that only joins the claim to what follows; an id does not end on one.
TRAIL = set("not no when while whether rather per without until after before unless because where".split())


def words(item):
    t = re.sub(r"^\s*[-*+] \[[ xX]\] ", "", item)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)       # a link reads as its text
    t = re.sub(r"\s\(([^()]*)\)\s*$", " ", t.strip())    # a trailing citation is not the claim
    t = t.lower().replace("'", "")
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return [w for w in t.split() if w not in STOP]


def mint(item, taken):
    ws = words(item) or ["criterion"]
    n = min(MAX_WORDS, len(ws))
    while True:
        base = "-".join(ws[:n])
        while len(base) > MAX_LEN and "-" in base:
            base = base.rsplit("-", 1)[0]
        while "-" in base and base.rsplit("-", 1)[1] in TRAIL:
            base = base.rsplit("-", 1)[0]
        if base not in taken:
            return base
        if n >= len(ws) or n >= MAX_WORDS + 3:
            break
        n += 1
    k = 2
    while f"{base}-{k}" in taken:
        k += 1
    return f"{base}-{k}"


def main(argv):
    dry = "--dry-run" in argv
    reg = load_register()
    if "--retire" in argv:
        rel, cid = argv[argv.index("--retire") + 1].split(":", 1)
        if cid not in reg["files"].get(rel, []):
            sys.exit(f"{rel}: {cid} is not a registered id of that file")
        text = open(os.path.join(CORPUS, rel), encoding="utf-8").read()
        if any(m.group(1) == cid for m in WL_CHECK_ANY.finditer(text)):
            sys.exit(f"{rel}: {cid} is still written in the file; remove its item first")
        reg["files"][rel].remove(cid)
        reg.setdefault("retired", {}).setdefault(rel, []).append(cid)
        save_register(reg)
        print(f"{rel}: {cid} retired; it is never given again")
        return
    minted = registered = 0
    for rel in files():
        path = os.path.join(CORPUS, rel)
        text = open(path, encoding="utf-8").read()
        lines = text.split("\n")
        known = list(reg["files"].get(rel, []))
        taken = set(known) | set(reg.get("retired", {}).get(rel, []))
        taken |= {m.group(1) for m in WL_CHECK_ANY.finditer(text)} | set(WL_ID.findall(text))
        changed = False
        for first, last, item in criteria(text):
            have = WL_CHECK_ANY.findall(item)
            if have:
                for cid, _ in have:
                    if cid not in known:
                        known.append(cid)
                        registered += 1
                continue
            if "--register-only" in argv:
                continue
            cid = mint(item, taken)
            taken.add(cid)
            known.append(cid)
            minted += 1
            if dry:
                print(f"{rel}:{first + 1}: {cid}")
            lines[last] = lines[last].rstrip() + f" <!-- wl:check {cid} -->"
            changed = True
        for m in WL_CHECK_ANY.finditer(text):  # a check written outside a checklist item
            if m.group(1) not in known:
                known.append(m.group(1))
                registered += 1
        if known:
            reg["files"][rel] = known
        if changed and not dry:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
    if not dry:
        save_register(reg)
    print(f"mint-criterion-ids: {minted} minted, {registered} already written and registered"
          + (" (dry run, nothing written)" if dry else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
