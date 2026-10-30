"""The change and build-lock fixtures get the results vectors/change/expected.json
gives them, under the rules schemas/change.md and schemas/build-lock.md declare:
a valid fixture breaks no rule, and an invalid one breaks exactly the rule it
names. Every fixture in the directory is listed once, and every rule a fixture
names is declared. v2-cli-validate is the tool these rules move to.

  change-vectors.py [--root DIR]
"""
import json, os, re, sys
import yaml

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ids import parse  # the id grammar of schemas/names.md

HEX32, DIGEST = re.compile(r"^[0-9a-f]{32}$"), re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")  # a full git commit, SHA-1 or SHA-256
APPLIED = ("applied", "verified", "failed")
# An ML-DSA-65 signature is 3309 bytes: 4412 characters of unpadded base64url.
SIGNATURE = re.compile(r"^[A-Za-z0-9_-]{4412}$")


def verdicts():
    """The Verdicts table of schemas/change.md, read, never copied: each
    verdict and the reasons its row allows, up to the row's first '('."""
    text = open(os.path.join(root, "schemas", "change.md"), encoding="utf-8").read()
    table = re.search(r"^\| `verdict` \| `because` may be \|\n\|[-|]+\|\n((?:\|.*\n)+)", text, re.M).group(1)
    out = {}
    for row in table.splitlines():
        verdict, because = [c.strip() for c in row.strip("|").split("|")]
        out[verdict.strip("`")] = set(re.findall(r"`([^`]+)`", because.split("(")[0]))
    return out


def declared(schema):
    text = open(os.path.join(root, "schemas", schema + ".md"), encoding="utf-8").read()
    block = re.search(r"```yaml\n(rules:\n.*?)```", text, re.S).group(1)
    return {r["id"] for r in yaml.safe_load(block)["rules"]}


FAMILIES = set(json.load(open(os.path.join(root, "vectors", "ids.json"), encoding="utf-8"))["families"])


def ref_ok(s, versioned):
    r = parse(s, FAMILIES) if isinstance(s, str) else None
    return r is not None and (versioned or r["version"] is None)


def signed(d, keys):
    return all(d.get(k) for k in keys) and SIGNATURE.match(str(d.get("signature", ""))) and DIGEST.match(str(d.get("plan_digest", "")))


def change_broken(c):
    b, st, a = set(), c.get("state"), c.get("approval")
    if not HEX32.match(str(c.get("id", ""))): b.add("change-id")
    if c.get("kind") not in ("adopt", "upgrade", "remove", "revert"): b.add("change-kind")
    if not c.get("request") or not all(ref_ok(r, True) and not r.startswith((".", "/")) for r in c["request"]): b.add("change-request")
    if ("reverts" in c) != (c.get("kind") == "revert"): b.add("change-reverts")
    base = c.get("base", {})
    if not base.get("corpus") or not DIGEST.match(str(base.get("lock", ""))) or base.get("fabric_tip", "unreported") != "unreported" and not DIGEST.match(base["fabric_tip"]):
        b.add("change-base")
    pins = base.get("pins")
    if not isinstance(pins, list) or not pins or not all(
            isinstance(p, dict) and p.get("kind") in ("project", "custom", "core") and p.get("origin")
            and COMMIT.match(str(p.get("revision", ""))) for p in pins) or base.get("corpus") != pins[0].get("revision"):
        b.add("base-pins")
    if "lock_of" in base and not (isinstance(base["lock_of"], str) and base["lock_of"].strip()): b.add("base-lock-of")
    plan = c.get("plan") or []
    if not plan: b.add("plan-not-empty")
    for e in plan:
        if ("unit" in e) == ("output" in e): b.add("plan-target")
        if e.get("because") not in VERDICTS.get(e.get("verdict"), set()): b.add("plan-verdict")
        if e.get("phase") == "F" and "output" not in e: b.add("plan-phase-f")
    units = {e.get("unit") for e in plan if "unit" in e}
    for u in c.get("unassessed") or []:
        if not u.get("unit") or not u.get("detail") or "verdict" in u or "because" in u or u.get("unit") in units:
            b.add("unassessed-entry")
    unapproved = c.get("without_approval") is True and st in APPLIED
    if (a is not None) != (st in ("approved",) + APPLIED and not unapproved) and st != "superseded": b.add("approval-present")
    if "without_approval" in c and (c["without_approval"] is not True or st not in APPLIED): b.add("without-approval")
    pos = c.get("approver_position")
    if a is not None and (a.get("position") != pos if pos is not None else "position" in a): b.add("approval-position")
    r = c.get("rejection")
    if (r is not None) != (st == "rejected") or r is not None and not signed(r, ("by", "reason", "at")): b.add("rejection-present")
    if a is not None:
        if not signed(a, ("by", "at")): b.add("approval-signed")
        if a.get("by") == c.get("requested_by") and a.get("development") is not True: b.add("approval-self")
        found = c.get("resolution", {}).get("conflicts", {}).get("found", [])
        if any(f["code"] != "C2" or c.get("strict", True) for f in found): b.add("approval-conflicts")
    if ("applied_run" in c) != (st in APPLIED): b.add("applied-run")
    if "outcomes" in c and (st not in APPLIED or not all(
            o.get("component") and o.get("result") in ("built", "failed", "refused", "skipped")
            and (o.get("verdict") or {}).get("outcome") in ("verified", "failed", "inconclusive", "unchecked")
            for o in c["outcomes"])):
        b.add("outcomes-present")
    return b


def lock_broken(l):
    b, lists = set(), ("blueprints", "mappings", "adopted")
    if set(l) != {"lock", "corpus"} | set(lists): b.add("lock-keys")
    if l.get("lock") != 1: b.add("lock-version")
    for k in lists:
        es = l.get(k) or []
        keys = {"ref", "version", "digest"} | ({"source"} if k == "blueprints" else set())
        for e in es:
            if set(e) - keys: b.add("lock-keys")
            if keys - set(e) or not ref_ok(e["ref"], False) or not DIGEST.match(str(e["digest"])): b.add("lock-entry")
        refs = [e.get("ref", "") for e in es]
        if len(set(refs)) != len(refs): b.add("lock-unique")
        if refs != sorted(refs): b.add("lock-sorted")
    return b


d = os.path.join(root, "vectors", "change")
exp = json.load(open(os.path.join(d, "expected.json"), encoding="utf-8"))["fixtures"]
rules = {"change": declared("change"), "build-lock": declared("build-lock")}
VERDICTS = verdicts()
faults, listed = [], [e["file"] for e in exp]
for f in sorted(set(os.listdir(d)) - {"expected.json", "README.md"}):
    if listed.count(f) != 1:
        faults.append(f"{f}: listed {listed.count(f)} times in expected.json; want once")
for e in exp:
    path = os.path.join(d, e["file"])
    if not os.path.exists(path):
        faults.append(f"{e['file']}: listed and absent"); continue
    if not e["valid"] and e.get("rule") not in rules[e["schema"]]:
        faults.append(f"{e['file']}: names rule {e.get('rule')}, which schemas/{e['schema']}.md does not declare")
    text = open(path, encoding="utf-8").read()
    broken = change_broken(json.loads(text)) if e["schema"] == "change" else lock_broken(yaml.safe_load(text))
    want = set() if e["valid"] else {e.get("rule")}
    if broken != want:
        faults.append(f"{e['file']}: breaks {sorted(broken) or 'nothing'}; expected {sorted(want) or 'nothing'}")
print("\n".join(faults) or f"change-vectors: {len(exp)} fixtures agree with their expected results")
sys.exit(1 if faults else 0)
