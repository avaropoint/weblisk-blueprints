#!/usr/bin/env python3
"""The signer fixtures of vectors/signer/ against the rules they exercise.

    checks/signer-vectors.py [--expected F] [--identity F] [--dir D]

Read from the corpus and nowhere else: the signer rules (each `wl:id` of
protocol/identity's section "A signer acting on a pointer") and its
pointer_operations table, architecture/engine's `signature-handoff-answer`,
the fixtures named in `wl:check` items of protocol/identity, architecture/admin
and architecture/engine, and the statement vectors of
vectors/fixed-form-statements.json. Reported:

- a fixture file not listed in expected.json, or listed twice, or listed and
  missing, or whose id is not its file's name;
- a rule a fixture names that no corpus file declares, and a signer rule no
  fixture exercises;
- a fixture a check names that expected.json does not list;
- a pointer whose operation the pointer table does not hold;
- an outcome outside signed, unsigned, refused and cancelled; a refusal with
  neither a code nor names_question; a signed outcome with no send, or with
  no read after its send (the read back);
- a statement vector that does not exist, is signed by another key than the
  fixture's sign-records key, or whose bytes are not the statement rebuilt
  from the owner's change as the fixture gives it.
"""
import json, os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import yaml  # noqa: E402

WL_ID = re.compile(r"<!--\s*wl:id\s+([a-z0-9-]+)\s*-->")
WL_CHECK_LINE = re.compile(r"^- \[[ xX]\] (.*<!--\s*wl:check\s+[a-z0-9-]+.*-->)\s*$", re.M)
FIXTURE_NAME = re.compile(r"`(handoff-[a-z0-9-]+)`")
SECTION = "### A signer acting on a pointer"
OUTCOMES = {"signed", "unsigned", "refused", "cancelled"}
DECISION = {"change-approve": "approve", "change-reject": "reject"}
PREFIX = "weblisk/change-decision/v1"


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def signer_section(text):
    i = text.find(SECTION)
    if i < 0:
        return ""
    j = text.find("\n### ", i + len(SECTION))
    return text[i: j if j > 0 else len(text)]


def pointer_operations(section):
    for m in re.finditer(r"^```yaml\n(.*?)^```", section, re.S | re.M):
        v = yaml.safe_load(m.group(1))
        if isinstance(v, dict) and "pointer_operations" in v:
            return {e["pointer"]: e for e in v["pointer_operations"]}
    return {}


def statement(fields):
    return (PREFIX + "".join("\x00" + f for f in fields)).encode("utf-8").hex()


def main():
    expected_p = arg("--expected", os.path.join(CORPUS, "vectors/signer/expected.json"))
    identity_p = arg("--identity", os.path.join(CORPUS, "protocol/identity.md"))
    fdir = arg("--dir", os.path.join(CORPUS, "vectors/signer"))
    faults = []

    identity = read(identity_p)
    section = signer_section(identity)
    if not section:
        print(f"signer-vectors: {identity_p} has no section '{SECTION[4:]}'")
        return 1
    signer_rules = set(WL_ID.findall(section))
    engine = read(os.path.join(CORPUS, "architecture/engine.md"))
    admin = read(os.path.join(CORPUS, "architecture/admin.md"))
    declared = set(WL_ID.findall(identity)) | set(WL_ID.findall(engine))
    handoff_rules = {"signature-handoff-answer"} & set(WL_ID.findall(engine))
    ops = pointer_operations(section)
    if not ops:
        faults.append("protocol/identity's signer section has no pointer_operations table")
    vectors = {v["id"]: v for v in json.load(open(os.path.join(CORPUS, "vectors/fixed-form-statements.json")))["vectors"]}

    exp = json.load(open(expected_p, encoding="utf-8"))
    listed = {}
    for e in exp.get("fixtures", []):
        if e["id"] in listed:
            faults.append(f"{e['id']}: listed twice")
        listed[e["id"]] = e
    files = {f[:-5] for f in os.listdir(fdir) if f.endswith(".json") and f != "expected.json"}
    for f in sorted(files - set(listed)):
        faults.append(f"{f}.json: a fixture expected.json does not list")
    for f in sorted(set(listed) - files):
        faults.append(f"{f}: listed, and no {f}.json is in the directory")

    exercised = set()
    for fid, e in sorted(listed.items()):
        if fid not in files:
            continue
        if e.get("file") != fid + ".json":
            faults.append(f"{fid}: its file is {e.get('file')!r}, not {fid}.json")
        fx = json.load(open(os.path.join(fdir, fid + ".json"), encoding="utf-8"))
        if fx.get("id") != fid:
            faults.append(f"{fid}.json: its id is {fx.get('id')!r}")
        g, x = fx.get("given", {}), e.get("expected", {})
        for r in e.get("rules", []):
            if r not in declared:
                faults.append(f"{fid}: names the rule {r}, which no corpus file declares")
            exercised.add(r)
        out = x.get("outcome")
        if out not in OUTCOMES:
            faults.append(f"{fid}: outcome {out!r} is not one of {sorted(OUTCOMES)}")
        if out == "refused" and not (x.get("code") or x.get("names_question")):
            faults.append(f"{fid}: a refusal with neither a code nor names_question")
        ptr = g.get("pointer") or (g.get("question", {}).get("pointer") or {})
        op = ptr[1] if isinstance(ptr, list) and len(ptr) > 1 else ptr.get("operation") if isinstance(ptr, dict) else None
        if op not in ops:
            faults.append(f"{fid}: the pointer's operation {op!r} is not in the pointer table")
        sends, reads = x.get("sends", []), x.get("reads", [])
        if out == "signed":
            if not sends:
                faults.append(f"{fid}: signed, and nothing was sent")
            elif len(reads) < 2:
                faults.append(f"{fid}: signed, and the record was not read back after the act")
        vid = x.get("statement_vector")
        if vid:
            v = vectors.get(vid)
            if v is None:
                faults.append(f"{fid}: statement_vector {vid} is not a vector of fixed-form-statements.json")
                continue
            if v.get("signed_by") != g.get("sign_records_key"):
                faults.append(f"{fid}: {vid} is signed by {v.get('signed_by')!r}, not the fixture's {g.get('sign_records_key')!r}")
            cid = ptr[2] if isinstance(ptr, list) and len(ptr) > 2 else ""
            change = next((c for c in g.get("owner", {}).get("changes", []) if c.get("id") == cid), None)
            if change is None:
                faults.append(f"{fid}: the owner holds no change {cid}")
                continue
            got = statement([cid, DECISION.get(op, ""), change.get("plan_digest", ""),
                             change.get("approver_position", ""), g.get("clock", "")])
            if got != v.get("message"):
                faults.append(f"{fid}: the statement rebuilt from the owner's change is not {vid}'s bytes")

    for r in sorted((signer_rules | handoff_rules) - exercised):
        faults.append(f"the rule {r} is exercised by no fixture")

    named = set()
    for text in (identity, admin, engine):
        for item in WL_CHECK_LINE.findall(text):
            named |= set(FIXTURE_NAME.findall(item))
    for n in sorted(named - set(listed)):
        faults.append(f"a check names the fixture {n}, which expected.json does not list")

    for f in faults:
        print(f)
    if faults:
        return 1
    print(f"signer-vectors: {len(listed)} fixtures, {len(signer_rules | handoff_rules)} rules each exercised, "
          f"{len(named)} named by checks, every statement rebuilt to its vector")
    return 0


if __name__ == "__main__":
    sys.exit(main())
