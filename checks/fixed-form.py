#!/usr/bin/env python3
"""Every vector in vectors/fixed-form-statements.json verifies with OpenSSL, an
ML-DSA implementation other than the one that made it, and fails with one byte
changed.

Usage: fixed-form.py [--file F] [--require-body PREFIX]...

For each key: OpenSSL derives the published public key from the published
seed, and the fingerprint is its SHA-256. For each vector: the prefix is in
protocol/identity's registry, the message is the prefix and fields joined by
0x00, the signature verifies over it under the signer's key, and the message
with its last byte changed does not. A vector that carries a body is checked
as its receiver checks it: the statement is rebuilt from the body alone, and
the signature must verify over that, so a one-byte change to the body fails.
--require-body fails unless some vector of PREFIX carries a body.

Needs OpenSSL 3.5 or later, as $OPENSSL or openssl on PATH. Without it the
check cannot run, and fails.
"""
import base64, hashlib, json, os, re, shutil, subprocess, sys, tempfile

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
args = sys.argv[1:]
path = os.path.join(root, "vectors/fixed-form-statements.json")
required = []
while args:
    a = args.pop(0)
    if a == "--file": path = args.pop(0)
    elif a == "--require-body": required.append(args.pop(0))
    else: sys.exit(f"unknown argument {a}")

openssl = os.environ.get("OPENSSL") or shutil.which("openssl")
ver = subprocess.run([openssl, "version"], capture_output=True, text=True).stdout.strip() if openssl else ""
m = re.match(r"OpenSSL (\d+)\.(\d+)", ver)
if not m or (int(m.group(1)), int(m.group(2))) < (3, 5):
    print(f"cannot run: needs OpenSSL 3.5 or later for ML-DSA, found {ver or 'none'}")
    sys.exit(2)

doc = json.load(open(path, encoding="utf-8"))
identity = open(os.path.join(root, "protocol/identity.md"), encoding="utf-8").read()
registered = set(re.findall(r"^\| `(weblisk/[a-z0-9-]+/v\d+)` \|", identity, re.M))
b64 = lambda s: base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))
# ML-DSA-65 (OID 2.16.840.1.101.3.4.3.18), wrapped as OpenSSL reads a raw key.
alg = bytes.fromhex("300b0609608648016503040312")
spki = lambda pk: bytes.fromhex("308207b2") + alg + bytes.fromhex("038207a100") + pk
pkcs8 = lambda seed: bytes.fromhex("3034020100") + alg + bytes.fromhex("04228020") + seed
found = []
tmp = tempfile.mkdtemp()


def ssl(*a):
    return subprocess.run([openssl, *a], capture_output=True)


def verifies(pub, msg, sig):
    mf, sf = os.path.join(tmp, "m"), os.path.join(tmp, "s")
    open(mf, "wb").write(msg); open(sf, "wb").write(sig)
    return ssl("pkeyutl", "-verify", "-pubin", "-inkey", pub, "-keyform", "DER", "-rawin", "-in", mf, "-sigfile", sf).returncode == 0


def jcs(v):
    """RFC 8785 for what a body holds here; anything it cannot place exactly is refused, not guessed."""
    if isinstance(v, bool) or v is None or isinstance(v, str): pass
    elif isinstance(v, int):
        if abs(v) > 2**53: raise ValueError(f"integer {v} is outside what RFC 8785 serialises exactly")
    elif isinstance(v, list): [jcs(x) for x in v]
    elif isinstance(v, dict):
        for k, x in v.items():
            if not k.isascii(): raise ValueError(f"key {k!r} is not ASCII; this check sorts by code point")
            jcs(x)
    else: raise ValueError(f"{type(v).__name__} is not canonicalised by this check")
    return json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


try:
    keys = {}
    for k in doc["keys"]:
        seed, pk = bytes.fromhex(k["seed"]), b64(k["public_key"])
        if seed != hashlib.sha256(("weblisk test vector key " + k["name"]).encode()).digest():
            found.append(f"key {k['name']}: seed is not the stated SHA-256")
        if hashlib.sha256(pk).hexdigest() != k["fingerprint"]:
            found.append(f"key {k['name']}: fingerprint is not the SHA-256 of the public key")
        priv, pub = os.path.join(tmp, k["name"] + ".p8"), os.path.join(tmp, k["name"] + ".spki")
        open(priv, "wb").write(pkcs8(seed)); open(pub, "wb").write(spki(pk))
        if ssl("pkey", "-in", priv, "-inform", "DER", "-pubout", "-outform", "DER").stdout != spki(pk):
            found.append(f"key {k['name']}: OpenSSL does not derive the published public key from the seed")
        keys[k["name"]] = pub
    bodies = set()
    for v in doc["vectors"]:
        vid, pub = v["id"], keys.get(v["signed_by"])
        if v["prefix"] not in registered:
            found.append(f"{vid}: prefix {v['prefix']} is not in protocol/identity's registry")
        if pub is None:
            found.append(f"{vid}: signed_by {v['signed_by']} is not a published key"); continue
        msg, sig = bytes.fromhex(v["message"]), b64(v["signature"])
        if msg != b"\0".join([v["prefix"].encode()] + [f["value"].encode() for f in v["fields"]]):
            found.append(f"{vid}: message is not the prefix and fields joined by 0x00")
        if not verifies(pub, msg, sig):
            found.append(f"{vid}: OpenSSL does not verify the signature")
        if verifies(pub, msg[:-1] + bytes([msg[-1] ^ 1]), sig):
            found.append(f"{vid}: the message with its last byte changed still verifies")
        if "body" not in v: continue
        bodies.add(v["prefix"])
        body = v["body"]
        if body.get("signature") != v["signature"]:
            found.append(f"{vid}: the body's signature is not the vector's")
        try:
            rest = jcs({k: x for k, x in body.items() if k != "signature"})
        except ValueError as e:
            found.append(f"{vid}: cannot canonicalise the body: {e}"); continue
        fields = {f["name"]: f["value"] for f in v["fields"]}
        if v["prefix"] != "weblisk/directory/v2":
            found.append(f"{vid}: this check rebuilds a body's statement only for weblisk/directory/v2"); continue
        rebuilt = b"\0".join([b"weblisk/directory/v2", str(body.get("updated_at")).encode(), b"sha256:" + hashlib.sha256(rest).hexdigest().encode()])
        if rebuilt != msg:
            found.append(f"{vid}: the statement rebuilt from the body is not the message (digest {fields.get('digest')}, body gives sha256:{hashlib.sha256(rest).hexdigest()})")
        if not verifies(pub, rebuilt, sig):
            found.append(f"{vid}: the signature does not verify over the statement rebuilt from the body")
    for p in required:
        if p not in bodies: found.append(f"no vector of {p} carries a body")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

if found: print("\n".join(found))
print(f"{ver}: {len(doc['keys'])} keys, {len(doc['vectors'])} vectors, {len(found)} findings")
sys.exit(1 if found else 0)
