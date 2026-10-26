#!/usr/bin/env python3
"""patterns/namespace's registry rules, run over vectors/namespace-registry.json.

One implementation of "Deciding a statement", outside every Weblisk tool. It
decides every step of every sequence, signatures verified by OpenSSL
(checks/statements.py), and reports each verdict and each final state that
differs from the vector's. It also holds the four statements the pattern
defines to protocol/identity's registry and to the published vectors.

    checks/namespace-registry.py                     check the vectors
    checks/namespace-registry.py --variant NAME      the same rules with one
        broken, which must be reported at exactly the steps that rule decides:
        accept-confusables, accept-one-sided, reclaim-retired,
        rotation-drops-grants
    checks/namespace-registry.py --pattern FILE      read the pattern's
        statements and routes from FILE instead of patterns/namespace.md
"""
import json, os, re, sys
import yaml
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.normpath(os.path.join(HERE, ".."))
spec = importlib.util.spec_from_file_location("statements", os.path.join(HERE, "statements.py"))
statements = importlib.util.module_from_spec(spec)
spec.loader.exec_module(statements)

CLAIM, GRANT, TRANSFER, RELEASE = (f"weblisk/{p}/v1" for p in ("namespace-claim", "namespace-grant", "namespace-transfer", "catalog-release"))
LAYOUT = {CLAIM: ["registry", "namespace", "holder", "issued_at"],
          GRANT: ["registry", "namespace", "grantee", "role", "issued_at"],
          TRANSFER: ["registry", "namespace", "from", "to", "kind", "issued_at"],
          RELEASE: ["namespace", "release", "index", "previous", "released_at"]}
HEX64, DEC = re.compile(r"[0-9a-f]{64}"), re.compile(r"0|[1-9][0-9]*")
DIGEST, NAME = re.compile(r"sha256:[0-9a-f]{64}"), re.compile(r"[a-z][a-z0-9-]{1,38}")
variant = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else None
PATTERN = sys.argv[sys.argv.index("--pattern") + 1] if "--pattern" in sys.argv else None


def read(rel): return open(os.path.join(CORPUS, rel), encoding="utf-8").read()


names = yaml.safe_load(re.search(r"## Declaration\n+```yaml\n(.*?)```", read("schemas/names.md"), re.S).group(1))
skeleton = lambda n: n.lower().replace("0", "o").replace("1", "l")
RESERVED = {r.lower() for r in names["reserved"]}


def well_formed(prefix, f):
    if prefix == RELEASE:
        return (DEC.fullmatch(f["release"]) and f["release"] != "0" and DIGEST.fullmatch(f["index"])
                and (f["previous"] == "" if f["release"] == "1" else DIGEST.fullmatch(f["previous"]))
                and DEC.fullmatch(f["released_at"]))
    ok = HEX64.fullmatch(f["registry"]) and DEC.fullmatch(f["issued_at"])
    if prefix == CLAIM: return ok and HEX64.fullmatch(f["holder"])
    if prefix == GRANT: return ok and HEX64.fullmatch(f["grantee"]) and f["role"] in ("publish", "none")
    return (ok and HEX64.fullmatch(f["from"]) and f["kind"] in ("transfer", "rotation", "retirement")
            and (f["to"] == "" if f["kind"] == "retirement" else HEX64.fullmatch(f["to"])))


class Registry:
    def __init__(self, vec, keys, ver):
        self.id, self.keys, self.ver = vec["registry"], keys, ver
        self.enrolled = {keys[n]["fp"]: kind for n, kind in vec["enrolled"].items()}
        self.never = {c.lower() for codes in vec["never_claimable"].values() for c in codes}
        self.log, self.ns = set(), {}

    def ruling(self, r):
        s = self.ns.get(r["namespace"])
        if not s: return "NAMESPACE_UNKNOWN"
        if s["status"] == "retired": return "NAMESPACE_RETIRED"
        if r["ruling"] == "freeze": s["status"] = "frozen"
        elif r["ruling"] == "unfreeze": s["status"] = "held"
        else:
            to = self.keys[r["to"]]["fp"]
            if self.enrolled.get(to) != "user": return "NAMESPACE_SERVICE_IDENTITY"
            s.update(holder=to, grants={})
        return "accepted"

    def decide(self, st, at, release=False):
        prefix, fields = st["prefix"], st["fields"]
        if prefix not in ((RELEASE,) if release else (CLAIM, GRANT, TRANSFER)) or [x["name"] for x in fields] != LAYOUT[prefix]:
            return "NAMESPACE_MALFORMED"
        f = {x["name"]: x["value"] for x in fields}
        if not well_formed(prefix, f): return "NAMESPACE_MALFORMED"
        if not release and f["registry"] != self.id: return "NAMESPACE_WRONG_REGISTRY"
        msg, signers = statements.message(prefix, fields), set()
        for s in st["signatures"]:
            k = self.keys.get(s["by"])
            if not k or not self.ver.verify(k["pk"], msg, statements.b64(s["signature"])): return "NAMESPACE_SIGNATURE_INVALID"
            signers.add(k["fp"])
        if not release:
            if abs(at - int(f["issued_at"])) > 300: return "NAMESPACE_STATEMENT_STALE"
            if msg in self.log: return "NAMESPACE_STATEMENT_REPLAYED"
        name = f["namespace"]
        if not NAME.fullmatch(name): return "NAMESPACE_INVALID"
        s = self.ns.get(name)
        if prefix == CLAIM:
            if s and s["status"] == "retired" and variant != "reclaim-retired": return "NAMESPACE_RETIRED"
            if name in RESERVED or name in self.never: return "NAMESPACE_RESERVED"
            if skeleton(name) in {skeleton(r) for r in RESERVED} and variant != "accept-confusables": return "NAMESPACE_CONFUSABLE"
            if s and s["status"] in ("held", "frozen"): return "NAMESPACE_HELD"
            v = self.who(f["holder"])
            if v: return v
            if f["holder"] not in signers: return "NAMESPACE_NOT_HOLDER"
            self.ns[name] = {"status": "held", "holder": f["holder"], "grants": {}}
            self.log.add(msg)
            return "accepted"
        if not s: return "NAMESPACE_UNKNOWN"
        if s["status"] == "retired": return "NAMESPACE_RETIRED"
        if s["status"] == "frozen": return "NAMESPACE_FROZEN"
        if release:
            if s["holder"] in signers or any(s["grants"].get(x) == "publish" for x in signers): return "accepted"
            return "NAMESPACE_NOT_PUBLISHER"
        if prefix == GRANT:
            if s["holder"] not in signers: return "NAMESPACE_NOT_HOLDER"
            v = self.who(f["grantee"], person=False)
            if v: return v
            if f["role"] == "publish": s["grants"][f["grantee"]] = "publish"
            else: s["grants"].pop(f["grantee"], None)
        else:
            if f["from"] != s["holder"] or f["from"] not in signers: return "NAMESPACE_NOT_HOLDER"
            if f["kind"] == "retirement":
                s.update(status="retired", holder=None, grants={})
            else:
                if f["to"] not in signers and variant != "accept-one-sided": return "NAMESPACE_TRANSFER_ONE_SIDED"
                v = self.who(f["to"])
                if v: return v
                keep = f["kind"] == "rotation" and variant != "rotation-drops-grants"
                s.update(holder=f["to"], grants=s["grants"] if keep else {})
        self.log.add(msg)
        return "accepted"

    def who(self, fp, person=True):
        if fp not in self.enrolled: return "NAMESPACE_IDENTITY_UNKNOWN"
        if person and self.enrolled[fp] != "user": return "NAMESPACE_SERVICE_IDENTITY"
        return None


def defined_here():
    """The four prefixes patterns/namespace defines, each registered by
    protocol/identity and vectored in vectors/fixed-form-statements.json."""
    faults = []
    try:
        pattern = open(PATTERN, encoding="utf-8").read() if PATTERN else read("patterns/namespace.md")
    except FileNotFoundError:
        return ["patterns/namespace.md: missing, so no statement is defined"]
    defined = set(re.findall(r'^"(weblisk/[a-z0-9-]+/v\d+)" 0x00', pattern, re.M))
    if defined != {CLAIM, GRANT, TRANSFER, RELEASE}:
        faults.append(f"patterns/namespace.md defines {sorted(defined)}, not the four statements")
    # A fixed path segment where {namespace} sits is a name someone can claim,
    # and then two routes answer the same path.
    routes = re.findall(r"^\| *[A-Z]+ *\| *(/v1/namespaces/[^ |]*) *\|", pattern, re.M)
    if not routes:
        faults.append("patterns/namespace.md: no /v1/namespaces/ route in its Endpoints")
    for path in routes:
        seg = path.split("/")[3]
        if not seg.startswith("{") and NAME.fullmatch(seg):
            faults.append(f"patterns/namespace.md: {path} is also /v1/namespaces/{{namespace}} for the claimable name {seg!r}")
    registered, _, _ = statements.registry()
    vectored = {v["prefix"] for v in json.loads(read("vectors/fixed-form-statements.json"))["vectors"]}
    for p in sorted(defined):
        if p not in registered: faults.append(f"{p}: not registered in protocol/identity")
        if p not in vectored: faults.append(f"{p}: no vectors in vectors/fixed-form-statements.json")
    return faults


def main():
    faults = defined_here()
    try:
        vec = json.loads(read("vectors/namespace-registry.json"))
    except FileNotFoundError:
        print("\n".join(faults + ["vectors/namespace-registry.json: missing"]))
        sys.exit(1)
    keys = {k["name"]: {"pk": statements.b64(k["public_key"]), "fp": k["fingerprint"]}
            for k in json.loads(read("vectors/fixed-form-statements.json"))["keys"]}
    byfp = {k["fp"]: n for n, k in keys.items()}
    ver, steps = statements.Verifier(), 0
    try:
        for seq in vec["sequences"]:
            reg = Registry(vec, keys, ver)
            for i, step in enumerate(seq["steps"], 1):
                steps += 1
                if "ruling" in step: got = reg.ruling(step["ruling"])
                elif "release" in step: got = reg.decide(step["release"], step["at"], release=True)
                else: got = reg.decide(step["statement"], step["at"])
                if got != step["expect"]:
                    faults.append(f"{seq['id']} step {i}: got {got}, want {step['expect']}")
            for name, want in seq["state"].items():
                s = reg.ns.get(name, {"status": "unheld", "holder": None, "grants": {}})
                got = {"status": s["status"], "holder": byfp.get(s["holder"]), "grants": {byfp[k]: v for k, v in s["grants"].items()}}
                if got != {"status": want["status"], "holder": want.get("holder"), "grants": want.get("grants", {})}:
                    faults.append(f"{seq['id']} state {name}: got {got}, want {want}")
    finally:
        ver.close()
    print("\n".join(faults) or f"namespace-registry: {steps} steps in {len(vec['sequences'])} sequences get their stated verdicts")
    sys.exit(1 if faults else 0)


if __name__ == "__main__":
    main()
