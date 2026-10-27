#!/usr/bin/env python3
"""patterns/namespace's registry rules, run over vectors/namespace-registry.json.

One implementation of "Deciding a statement" and of verifying a catalog
release, outside every Weblisk tool. It decides every step of every sequence,
signatures verified by OpenSSL (checks/statements.py), and reports each
verdict and each final state that differs from the vector's. It also holds the
four statements the pattern defines to protocol/identity's registry and to the
published vectors, the pattern to D11's layering, and the place and issuer
codes the vectors use to the corpus's own: a place code is one some standard's
applies_in names, and an issuer code begins some standard's id. The vectors
hold only a sample of each; a registry refuses every such code.

A verifier here decides a release from the same log the registry keeps, so
it re-decides nothing the registry did not: a release verifies when its form,
index and signature hold and the log holds its exact bytes signed by the same
key.

    checks/namespace-registry.py                     check the vectors
    checks/namespace-registry.py --variant NAME      the same rules with one
        broken, which must be reported at exactly the steps that rule decides:
        accept-confusables, accept-one-sided, reclaim-retired,
        rotation-drops-grants, rotation-any-identity (a rotation to another
        identity's key), release-signer-time (a release judged at the time its
        signer wrote, not the registry's clock), release-unchained (no release
        held to the one before it), release-unanchored (a verifier that accepts
        a release its registry's log does not hold), release-ignores-revocation
        (a release by a grantee whose identity the hub revoked),
        holder-ignores-revocation (a grant, transfer, rotation or retirement
        signed by a holder whose identity the hub revoked)
    checks/namespace-registry.py --pattern FILE      read the pattern's
        statements, routes and requires from FILE instead of
        patterns/namespace.md
    checks/namespace-registry.py --vectors FILE      read the registry
        vectors from FILE instead of vectors/namespace-registry.json
"""
import copy, hashlib, json, os, re, sys
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
          RELEASE: ["registry", "namespace", "release", "index", "previous", "issued_at"]}
HEX64, DEC = re.compile(r"[0-9a-f]{64}"), re.compile(r"0|[1-9][0-9]*")
INDEX_LINE = re.compile(r"(\S+) (sha256:[0-9a-f]{64}|retired)")
DIGEST, NAME = re.compile(r"sha256:[0-9a-f]{64}"), re.compile(r"[a-z][a-z0-9-]{1,38}")
variant = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else None
PATTERN = sys.argv[sys.argv.index("--pattern") + 1] if "--pattern" in sys.argv else None
VECTORS = sys.argv[sys.argv.index("--vectors") + 1] if "--vectors" in sys.argv else None


def read(rel): return open(os.path.join(CORPUS, rel), encoding="utf-8").read()


names = yaml.safe_load(re.search(r"## Declaration\n+```yaml\n(.*?)```", read("schemas/names.md"), re.S).group(1))
skeleton = lambda n: n.lower().replace("0", "o").replace("1", "l")
RESERVED = {r.lower() for r in names["reserved"]}
# The replay window has one home, protocol/identity's Security block.
WINDOW = int(re.search(r"^  replay_protection:\n    window: (\d+) seconds$", read("protocol/identity.md"), re.M).group(1))


def well_formed(prefix, f):
    ok = HEX64.fullmatch(f["registry"]) and DEC.fullmatch(f["issued_at"])
    if prefix == RELEASE:
        return (ok and DEC.fullmatch(f["release"]) and f["release"] != "0" and DIGEST.fullmatch(f["index"])
                and (f["previous"] == "" if f["release"] == "1" else DIGEST.fullmatch(f["previous"])))
    if prefix == CLAIM: return ok and HEX64.fullmatch(f["holder"])
    if prefix == GRANT: return ok and HEX64.fullmatch(f["grantee"]) and f["role"] in ("publish", "none")
    return (ok and HEX64.fullmatch(f["from"]) and f["kind"] in ("transfer", "rotation", "retirement")
            and (f["to"] == "" if f["kind"] == "retirement" else HEX64.fullmatch(f["to"])))


class Registry:
    def __init__(self, vec, keys, ver):
        self.id, self.keys, self.ver = vec["registry"], keys, ver
        # Each enrolled key's kind and identity: a rotation keeps the identity.
        self.enrolled = {keys[n]["fp"]: e for n, e in vec["enrolled"].items()}
        self.revoked = set()
        self.never = {c.lower() for codes in vec["never_claimable"].values() for c in codes}
        self.log, self.ns = set(), {}
        # Each recorded release's bytes with each key that signed them there.
        self.recorded = set()
        # Every change to a namespace's state, as (at, state after), read only
        # by the release-signer-time variant; and the releases the log records,
        # by namespace, in order.
        self.history, self.releases = {}, {}

    def record(self, name, at):
        self.history.setdefault(name, []).append((at, copy.deepcopy(self.ns[name])))

    def state_at(self, name, t):
        past = [st for at, st in self.history.get(name, []) if at <= t]
        return past[-1] if past else None

    def revoke(self, name):
        """The hub revokes an identity's enrolment; the registry records nothing."""
        self.revoked.add(self.keys[name]["fp"])
        return "accepted"

    def ruling(self, r, at):
        s = self.ns.get(r["namespace"])
        if not s: return "NAMESPACE_UNKNOWN"
        if s["status"] == "retired": return "NAMESPACE_RETIRED"
        if r["ruling"] == "freeze": s["status"] = "frozen"
        elif r["ruling"] == "unfreeze": s["status"] = "held"
        else:
            to = self.keys[r["to"]]["fp"]
            v = self.who(to)
            if v: return v
            # A reassignment changes the holder and ends the grants; a frozen
            # namespace stays frozen.
            s.update(holder=to, grants={})
        self.record(r["namespace"], at)
        return "accepted"

    def form(self, st, index):
        """Step 1, and step 3's signatures: (fields, message, signers), or a refusal."""
        prefix, fields = st["prefix"], st["fields"]
        if prefix not in LAYOUT or [x["name"] for x in fields] != LAYOUT[prefix]:
            return "NAMESPACE_MALFORMED"
        f = {x["name"]: x["value"] for x in fields}
        if not well_formed(prefix, f): return "NAMESPACE_MALFORMED"
        lines = None
        if prefix == RELEASE:
            lines = index_lines(index, f["index"])
            if lines is None: return "NAMESPACE_MALFORMED"
        return f, lines, statements.message(prefix, fields)

    def signed(self, st, msg):
        signers = set()
        for s in st["signatures"]:
            k = self.keys.get(s["by"])
            if not k or not self.ver.verify(k["pk"], msg, statements.b64(s["signature"])): return None
            signers.add(k["fp"])
        return signers

    def decide(self, st, at, index=None):
        got = self.form(st, index)
        if isinstance(got, str): return got
        (f, lines, msg), prefix = got, st["prefix"]
        if f["registry"] != self.id: return "NAMESPACE_WRONG_REGISTRY"
        signers = self.signed(st, msg)
        if signers is None: return "NAMESPACE_SIGNATURE_INVALID"
        if abs(at - int(f["issued_at"])) > WINDOW: return "NAMESPACE_STATEMENT_STALE"
        if msg in self.log: return "NAMESPACE_STATEMENT_REPLAYED"
        name = f["namespace"]
        if not NAME.fullmatch(name): return "NAMESPACE_INVALID"
        if prefix == RELEASE:
            v = self.release(name, f, lines, signers, at)
            if v == "accepted":
                self.log.add(msg)
                self.recorded.update((msg, x) for x in signers)
            return v
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
            self.record(name, at)
            return "accepted"
        if not s: return "NAMESPACE_UNKNOWN"
        if s["status"] == "retired": return "NAMESPACE_RETIRED"
        if s["status"] == "frozen": return "NAMESPACE_FROZEN"
        if prefix == GRANT:
            if s["holder"] not in signers: return "NAMESPACE_NOT_HOLDER"
            v = self.holder_acts(s["holder"]) or self.who(f["grantee"], person=False)
            if v: return v
            if f["role"] == "publish": s["grants"][f["grantee"]] = "publish"
            else: s["grants"].pop(f["grantee"], None)
        else:
            if f["from"] != s["holder"] or f["from"] not in signers: return "NAMESPACE_NOT_HOLDER"
            v = self.holder_acts(s["holder"])
            if v: return v
            if f["kind"] == "retirement":
                s.update(status="retired", holder=None, grants={})
            else:
                if f["to"] not in signers and variant != "accept-one-sided": return "NAMESPACE_TRANSFER_ONE_SIDED"
                v = self.who(f["to"])
                if v: return v
                if (f["kind"] == "rotation" and variant != "rotation-any-identity"
                        and self.enrolled[f["to"]]["identity"] != self.enrolled.get(f["from"], {}).get("identity")):
                    return "NAMESPACE_ROTATION_OTHER_IDENTITY"
                keep = f["kind"] == "rotation" and variant != "rotation-drops-grants"
                s.update(holder=f["to"], grants=s["grants"] if keep else {})
        self.log.add(msg)
        self.record(name, at)
        return "accepted"

    def release(self, name, f, lines, signers, at):
        """Step 8: a catalog release, at the registry's own clock, continuing
        the latest release the log records for the namespace."""
        s = self.state_at(name, int(f["issued_at"])) if variant == "release-signer-time" else self.ns.get(name)
        if not s: return "NAMESPACE_UNKNOWN"
        if s["status"] == "retired": return "NAMESPACE_RETIRED"
        if s["status"] == "frozen": return "NAMESPACE_FROZEN"
        publishers = {x for x in signers if x == s["holder"] or s["grants"].get(x) == "publish"}
        if not publishers: return "NAMESPACE_NOT_PUBLISHER"
        if variant != "release-ignores-revocation" and not any(x in self.enrolled and x not in self.revoked for x in publishers):
            return "NAMESPACE_IDENTITY_UNKNOWN"
        held, n = self.releases.setdefault(name, []), int(f["release"])
        if variant != "release-unchained":
            if n != len(held) + 1: return "NAMESPACE_RELEASE_BROKEN"
            if held:
                prev = held[-1]
                if f["previous"] != prev["index"]: return "NAMESPACE_RELEASE_BROKEN"
                for ref, d in prev["lines"].items():
                    if ref not in lines or (d == "retired" and lines[ref] != "retired"):
                        return "NAMESPACE_RELEASE_BROKEN"
        held.append({"index": f["index"], "lines": lines})
        return "accepted"

    def verify(self, st, index):
        """A verifier's decision on a release offered to it: its form, index
        and signature, then the registry's log holding its exact bytes."""
        got = self.form(st, index)
        if isinstance(got, str): return got
        if st["prefix"] != RELEASE: return "NAMESPACE_MALFORMED"
        f, lines, msg = got
        signers = self.signed(st, msg)
        if signers is None: return "NAMESPACE_SIGNATURE_INVALID"
        if not NAME.fullmatch(f["namespace"]): return "NAMESPACE_INVALID"
        if not any((msg, x) in self.recorded for x in signers) and variant != "release-unanchored":
            return "NAMESPACE_RELEASE_UNRECORDED"
        return "accepted"

    def holder_acts(self, fp):
        """Step 7: the holder signing a grant, transfer, rotation or retirement
        is still enrolled and not revoked."""
        return None if variant == "holder-ignores-revocation" else self.who(fp, person=False)

    def who(self, fp, person=True):
        if fp not in self.enrolled or fp in self.revoked: return "NAMESPACE_IDENTITY_UNKNOWN"
        if person and self.enrolled[fp]["kind"] != "user": return "NAMESPACE_SERVICE_IDENTITY"
        return None


def corpus_codes(vec):
    """The vectors' place and issuer codes, each held to where the corpus
    states it: a place code some standard's applies_in names, an issuer code
    that begins some standard's id."""
    import glob
    places, issuers = set(), set()
    for path in glob.glob(os.path.join(CORPUS, "standards", "*.json")):
        d = json.load(open(path, encoding="utf-8"))
        places.update(c.lower() for c in d.get("applies_in", []))
        issuers.add(d["id"].split("_")[0].lower())
    faults = []
    for c in vec["never_claimable"].get("place_codes", []):
        if c.lower() not in places: faults.append(f"never_claimable: place code {c!r} is in no standard's applies_in")
    for c in vec["never_claimable"].get("issuer_codes", []):
        if c.lower() not in issuers: faults.append(f"never_claimable: issuer code {c!r} begins no standard's id")
    return faults


def index_lines(text, digest):
    """The index a release names, as {ref: digest or 'retired'}, or None when
    the text is not that digest's or not in the index's form."""
    if text is None or "sha256:" + hashlib.sha256(text.encode()).hexdigest() != digest:
        return None
    if not text.endswith("\n"): return None
    lines = [INDEX_LINE.fullmatch(l) for l in text[:-1].split("\n")]
    if not all(lines): return None
    refs = [m.group(1) for m in lines]
    if refs != sorted(refs, key=lambda r: r.encode()) or len(set(refs)) != len(refs): return None
    return {m.group(1): m.group(2) for m in lines}


def defined_here():
    """The four prefixes patterns/namespace defines, each registered by
    protocol/identity and vectored in vectors/fixed-form-statements.json."""
    faults = []
    try:
        pattern = open(PATTERN, encoding="utf-8").read() if PATTERN else read("patterns/namespace.md")
    except FileNotFoundError:
        return ["patterns/namespace.md: missing, so no statement is defined"]
    # D11: a pattern requires nothing above its layer. An architecture
    # blueprint it cites is related:, in its header and in no requires block.
    head = re.search(r"^requires: \[(.*?)\]$", pattern, re.M)
    up = [r.strip() for r in (head.group(1).split(",") if head else []) if r.strip().startswith(("architecture/", "agents/"))]
    up += re.findall(r"^  - blueprint: ((?:architecture|agents)/[a-z0-9-]+)$", pattern, re.M)
    for r in sorted(set(up)):
        faults.append(f"patterns/namespace.md: requires {r}, a blueprint above the pattern layer (D11); make it related:")
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
        vec = json.loads(open(VECTORS, encoding="utf-8").read() if VECTORS else read("vectors/namespace-registry.json"))
    except FileNotFoundError:
        print("\n".join(faults + ["vectors/namespace-registry.json: missing"]))
        sys.exit(1)
    keys = {k["name"]: {"pk": statements.b64(k["public_key"]), "fp": k["fingerprint"]}
            for k in json.loads(read("vectors/fixed-form-statements.json"))["keys"]}
    byfp = {k["fp"]: n for n, k in keys.items()}
    faults += corpus_codes(vec)
    ver, steps = statements.Verifier(), 0
    try:
        for seq in vec["sequences"]:
            reg = Registry(vec, keys, ver)
            for i, step in enumerate(seq["steps"], 1):
                steps += 1
                if "ruling" in step: got = reg.ruling(step["ruling"], step["at"])
                elif "revoke" in step: got = reg.revoke(step["revoke"])
                elif "verify" in step: got = reg.verify(step["verify"], step.get("index"))
                else: got = reg.decide(step["statement"], step["at"], step.get("index"))
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
