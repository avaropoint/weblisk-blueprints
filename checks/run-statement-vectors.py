#!/usr/bin/env python3
"""The run statement's actions and criteria (schemas/run-statement.md, Actions,
Criteria, Rules for actions and criteria) against vectors/run-statement/.

Each fixture gets the result vectors/run-statement/expected.json gives it: a
valid fixture breaks no rule, and an invalid one breaks exactly the rule it
names. Every fixture in the directory is listed once, every rule a fixture
names is declared, and every declared rule is broken by some fixture. The
steps, and whether each calls a model, are read from architecture/engine.md.

It also recomputes every criterion digest in
vectors/run-statement/criterion-digest.json: the SHA-256 of the RFC 8785
bytes of {text, cites}, the text with its id marker removed and its
whitespace collapsed, the cites sorted by ref (architecture/engine.md, The
unit is a criterion). --unsorted computes them without sorting the cites,
which is how the control proves the vector reaches the sort.

  run-statement-vectors.py [--root DIR] [--unsorted]
"""
import glob, hashlib, json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ids import parse  # noqa: E402  the id grammar of schemas/names.md

argv = sys.argv[1:]
root = argv[argv.index("--root") + 1] if "--root" in argv else os.path.join(HERE, "..")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def read(rel):
    return open(os.path.join(root, rel), encoding="utf-8").read()


def declared():
    text = read("schemas/run-statement.md").split("## Rules for actions and criteria", 1)[1]
    block = re.search(r"```yaml\n(rules:\n.*?)```", text, re.S).group(1)
    return [r["id"] for r in yaml.safe_load(block)["rules"]]


def steps():
    text = read("architecture/engine.md")
    block = [b for b in re.findall(r"^```yaml\n(.*?)^```", text, re.M | re.S) if b.startswith("steps:")][0]
    return {s["id"]: s.get("model") for s in yaml.safe_load(block)["steps"]}


STEPS = steps()
FAMILIES = set(json.load(open(os.path.join(root, "vectors", "ids.json"), encoding="utf-8"))["families"])


def broken(s):
    b = set()
    ip = s["predicate"]["buildDefinition"]["internalParameters"]
    run = s["predicate"]["runDetails"]["metadata"]["invocationId"]
    acts, crits = ip.get("actions", []), ip.get("criteria", [])
    byproducts = {"sha256:" + p["digest"]["sha256"] for p in s["predicate"]["runDetails"].get("byproducts", [])}
    seen, index = set(), {}
    for n, a in enumerate(acts):
        if not ID.match(str(a.get("id", ""))) or a.get("id") in seen: b.add("action-id")
        seen.add(a.get("id")); index.setdefault(a.get("id"), n)
        if a.get("step") not in STEPS: b.add("action-step")
        if a.get("kind") == "model":
            if STEPS.get(a.get("step")) != "called" or not a.get("instructions") or not a.get("model"): b.add("action-model")
        elif a.get("kind") == "deterministic":
            if a.get("instructions") or a.get("model") or a.get("transcript"): b.add("action-model")
        else:
            b.add("action-model")
        for io in a.get("inputs", []) + a.get("outputs", []):
            if not DIGEST.match(str(io.get("digest", ""))): b.add("action-digests")
        for i in a.get("instructions") or []:
            r = parse(i.get("ref", ""), FAMILIES) if isinstance(i.get("ref"), str) else None
            if not r or r["family"] != "instruction" or not i.get("version") or not DIGEST.match(str(i.get("digest", ""))): b.add("action-digests")
        if a.get("kind") == "model" and "reused_from" not in a and a.get("transcript") not in byproducts: b.add("action-transcript")
        if "reused_from" in a:
            if "transcript" in a: b.add("action-reuse")
            ref = a["reused_from"]
            if ref.get("run") == run:
                k = index.get(ref.get("action"))
                o = acts[k] if k is not None and k < n else None
                key = lambda x: (x.get("step"), [i.get("digest") for i in x.get("instructions") or []],
                                 [i.get("digest") for i in x.get("inputs", [])], [i.get("digest") for i in x.get("outputs", [])])
                if o is None or key(o) != key(a): b.add("action-reuse")
    order = [a.get("step") for a in acts]
    if "generate" in order and "translate" in order[order.index("generate"):]: b.add("translate-first")
    made = {o.get("digest") for a in acts if a.get("step") in ("generate", "repair") for o in a.get("outputs", [])}
    for a in acts:
        if a.get("step") == "translate" and any(i.get("digest") in made for i in a.get("inputs", [])): b.add("translate-apart")
    test_paths = {t.get("path") for c in crits for t in c.get("tests") or []}
    for a in acts:
        if a.get("step") in ("generate", "repair") and any(o.get("name") in test_paths for o in a.get("outputs", [])): b.add("test-not-written")
    ids = set()
    for c in crits:
        if not c.get("id") or c.get("id") in ids or not DIGEST.match(str(c.get("digest", ""))): b.add("criterion-id")
        ids.add(c.get("id"))
        sb, tests = c.get("settled_by"), c.get("tests") or []
        if sb == "translated":
            if not tests or c.get("check"): b.add("criterion-settled")
        elif sb in ("declared", "vector"):
            if tests or not c.get("check"): b.add("criterion-settled")
        elif sb == "unsettled":
            why = (c.get("unsettled") or {}).get("why")
            if tests or c.get("check") or why not in ("untestable", "model-finding", "unresolved-cite", "no-check"): b.add("criterion-settled")
            if (c.get("verdict") or {}).get("result") != "not-run" or (c.get("gap") or {}).get("result") != "unsettled": b.add("unsettled-not-passed")
        else:
            b.add("criterion-settled")
        for r in c.get("readings") or []:
            k = index.get(r.get("action"))
            if k is None or acts[k].get("kind") != "model" or acts[k].get("step") != "accept" or r.get("says") not in ("met", "unmet", "unsure"): b.add("reading-action")
        for t in tests:
            tb = t.get("translated_by") or {}
            if tb.get("run") == run:
                k = index.get(tb.get("action"))
                if k is None or acts[k].get("step") != "translate" or acts[k].get("criterion") != c.get("id"): b.add("test-translated-by")
            elif not tb.get("run") or not tb.get("action"):
                b.add("test-translated-by")
        v = c.get("verdict") or {}
        if v.get("result") not in ("pass", "fail", "error", "not-run"): b.add("verdict-result")
        if "gap" in c and c["gap"].get("result") not in ("unmet", "unsettled", "failed"): b.add("verdict-result")
        if sb == "translated" and v.get("result") == "pass" and any(t.get("stub") != "failed" for t in tests): b.add("test-counts")
    verdict = ip.get("verdict")
    if verdict is not None:
        conf, classes = verdict.get("conformance"), verdict.get("classes")
        if conf not in ("established", "accepted", "refuted", "not-run"): b.add("verdict-classes")
        if classes is not None:
            want = {}
            for c in crits:
                res = (c.get("verdict") or {}).get("result")
                n = want.setdefault(c.get("class"), {"met": 0, "unmet": 0, "unsettled": 0})
                n["met" if res == "pass" else "unmet" if res in ("fail", "error") else "unsettled"] += 1
            if set(classes) - {"S", "J", "B", "E", "F"} or classes != want: b.add("verdict-classes")
            if conf == "accepted" and any(classes.get(k, {}).get(x) for k in ("S", "J") for x in ("unmet", "unsettled")): b.add("verdict-classes")
            if conf == "established" and any(n.get("unmet") or n.get("unsettled") for n in classes.values()): b.add("verdict-classes")
    return b


def canon(v):
    if isinstance(v, bool) or v is None:
        return json.dumps(v)
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ",".join(canon(x) for x in v) + "]"
    if isinstance(v, dict):
        if any(not k.isascii() for k in v):
            raise ValueError("a non-ASCII key: UTF-16 ordering is not implemented here")
        return "{" + ",".join(json.dumps(k) + ":" + canon(v[k]) for k in sorted(v)) + "}"
    raise ValueError(f"{type(v).__name__} is outside what this canonicaliser handles")


def criterion_digest(text, cites):
    text = " ".join(re.sub(r"<!--\s*wl:[^>]*-->", " ", text).split())
    cites = list(cites) if "--unsorted" in argv else sorted(cites, key=lambda c: c["ref"])
    return "sha256:" + hashlib.sha256(canon({"text": text, "cites": cites}).encode("utf-8")).hexdigest()


vdir = os.path.join(root, "vectors", "run-statement")
faults = []
rules = declared()
exp = json.load(open(os.path.join(vdir, "expected.json"), encoding="utf-8"))
listed = [f["file"] for f in exp["fixtures"]]
files = sorted(os.path.basename(p) for p in glob.glob(os.path.join(vdir, "*valid-*.json")))
for f in sorted(set(files) - set(listed)): faults.append(f"{f}: in the directory and not in expected.json")
for f in sorted({x for x in listed if listed.count(x) > 1}): faults.append(f"{f}: listed more than once")
exercised = set()
for f in exp["fixtures"]:
    if f.get("breaks") and f["breaks"] not in rules: faults.append(f"{f['file']}: names rule {f['breaks']}, which schemas/run-statement.md does not declare")
    b = broken(json.load(open(os.path.join(vdir, f["file"]), encoding="utf-8")))
    want = set() if f["valid"] else {f.get("breaks")}
    exercised |= want
    if b != want: faults.append(f"{f['file']}: breaks {sorted(b)}; expected {sorted(want) or 'nothing'}")
for r in rules:
    if r not in exercised: faults.append(f"rule {r}: no fixture breaks it")
cd = json.load(open(os.path.join(vdir, "criterion-digest.json"), encoding="utf-8"))
for c in cd["cases"]:
    got = criterion_digest(c["text"], c["cites"])
    if got != c["digest"]: faults.append(f"criterion-digest {c['name']}: computed {got}, the vector says {c['digest']}")
for a, bname in cd.get("equal", []):
    da, db = [next(c["digest"] for c in cd["cases"] if c["name"] == n) for n in (a, bname)]
    if da != db: faults.append(f"criterion-digest: {a} and {bname} must be equal")
for a, bname in cd.get("differ", []):
    da, db = [next(c["digest"] for c in cd["cases"] if c["name"] == n) for n in (a, bname)]
    if da == db: faults.append(f"criterion-digest: {a} and {bname} must differ")
print("\n".join(faults) or f"run-statement-vectors: {len(listed)} fixtures under {len(rules)} rules, every rule exercised; {len(cd['cases'])} criterion digests agree")
sys.exit(1 if faults else 0)
