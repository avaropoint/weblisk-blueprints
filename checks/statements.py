#!/usr/bin/env python3
"""The fixed-form statement vectors (protocol/identity, Fixed-Form Statements),
checked with OpenSSL 3.5 or later, an ML-DSA implementation outside every
Weblisk tool.

- every prefix the registry table registers has vectors, except the prefixes
  the section names as having none yet, and the section's list of prefixes
  with vectors is exactly the prefixes that have them;
- every key's seed is the stated SHA-256, its fingerprint the SHA-256 of its
  public key, and OpenSSL derives that public key from the seed;
- every vector's message is its prefix and fields joined by 0x00, and OpenSSL
  verifies its signature under the key it names.

    checks/statements.py              check vectors/fixed-form-statements.json
    checks/statements.py --flip ID    the same, with one byte of vector ID's
                                      message changed: exactly ID must fail

Without OpenSSL 3.5 the check cannot run, and says so with exit status 2.
Set OPENSSL to choose the binary.
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, base64

CORPUS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ML-DSA-65's OID, 2.16.840.1.101.3.4.3.18, around a raw public key and a seed.
ALG = bytes.fromhex("300b0609608648016503040312")
def spki(pk): return bytes.fromhex("308207b2") + ALG + bytes.fromhex("038207a100") + pk
def pkcs8_seed(seed): return bytes.fromhex("3034020100") + ALG + bytes.fromhex("04228020") + seed
def b64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def openssl():
    for c in (os.environ.get("OPENSSL"), shutil.which("openssl"), "/opt/homebrew/bin/openssl", "/usr/local/bin/openssl"):
        if not c or not os.path.exists(c):
            continue
        v = subprocess.run([c, "version"], capture_output=True, text=True).stdout
        m = re.match(r"OpenSSL (\d+)\.(\d+)", v)
        if m and (int(m[1]), int(m[2])) >= (3, 5):
            return c
    print("statements: not run: no OpenSSL 3.5 or later (set OPENSSL)")
    sys.exit(2)


class Verifier:
    """ML-DSA-65 verification by OpenSSL, through files in a directory it removes."""
    def __init__(self):
        self.bin, self.dir, self.n = openssl(), tempfile.mkdtemp(), 0
    def close(self): shutil.rmtree(self.dir, ignore_errors=True)
    def _file(self, data):
        self.n += 1
        p = os.path.join(self.dir, str(self.n))
        open(p, "wb").write(data)
        return p
    def verify(self, pk, msg, sig):
        r = subprocess.run([self.bin, "pkeyutl", "-verify", "-pubin", "-inkey", self._file(spki(pk)), "-keyform", "DER",
                            "-rawin", "-in", self._file(msg), "-sigfile", self._file(sig)], capture_output=True)
        return r.returncode == 0
    def public_key(self, seed):
        r = subprocess.run([self.bin, "pkey", "-in", self._file(pkcs8_seed(seed)), "-inform", "DER", "-pubout", "-outform", "DER"],
                           capture_output=True)
        return r.stdout if r.returncode == 0 else None


def message(prefix, fields):
    return prefix.encode() + b"".join(b"\0" + f["value"].encode() for f in fields)


def registry():
    """The prefixes protocol/identity registers, those it says have no vectors
    yet, and those it says have them."""
    text = open(os.path.join(CORPUS, "protocol/identity.md"), encoding="utf-8").read()
    sec = re.search(r"^### Fixed-Form Statements\n(.*?)(?=^### )", text, re.S | re.M).group(1)
    registered = re.findall(r"^\| `(weblisk/[a-z0-9-]+/v\d+)` \|", sec, re.M)
    flat = re.sub(r"\s+", " ", sec)
    none_yet = re.search(r"None is published yet for (.*?), so no implementation", flat)
    holds = re.search(r"It holds vectors for (.*?)\. None", flat)
    pick = lambda m: set(re.findall(r"`(weblisk/[a-z0-9-]+/v\d+)`", m.group(1))) if m else set()
    return registered, pick(none_yet), pick(holds)


def main():
    flip = sys.argv[sys.argv.index("--flip") + 1] if "--flip" in sys.argv else None
    doc = json.load(open(os.path.join(CORPUS, "vectors/fixed-form-statements.json"), encoding="utf-8"))
    registered, none_yet, holds = registry()
    have = {v["prefix"] for v in doc["vectors"]}
    faults = []
    for p in sorted(set(registered) - have - none_yet):
        faults.append(f"{p}: registered, with no vectors and not named as having none yet")
    for p in sorted(have - set(registered)):
        faults.append(f"{p}: has vectors and is not registered")
    for p in sorted(none_yet & have):
        faults.append(f"{p}: named as having no vectors yet, and has them")
    for p in sorted(holds ^ have):
        faults.append(f"{p}: {'listed as holding vectors, and has none' if p in holds else 'has vectors, and the list of prefixes with vectors omits it'}")
    if flip and flip not in {v["id"] for v in doc["vectors"]}:
        sys.exit(f"statements: no vector {flip!r}")

    ver = Verifier()
    try:
        keys = {}
        for k in doc["keys"]:
            seed, pk = bytes.fromhex(k["seed"]), b64(k["public_key"])
            if seed != hashlib.sha256(("weblisk test vector key " + k["name"]).encode()).digest():
                faults.append(f"key {k['name']}: the seed is not the stated SHA-256")
            if hashlib.sha256(pk).hexdigest() != k["fingerprint"] or len(pk) != 1952:
                faults.append(f"key {k['name']}: the fingerprint is not the SHA-256 of a 1,952-byte public key")
            if ver.public_key(seed) != spki(pk):
                faults.append(f"key {k['name']}: OpenSSL derives another public key from the seed")
            keys[k["name"]] = pk
        for v in doc["vectors"]:
            msg, sig = message(v["prefix"], v["fields"]), b64(v["signature"])
            if any("\0" in f["value"] for f in v["fields"]) or msg.hex() != v["message"]:
                faults.append(f"{v['id']}: the message is not the prefix and fields joined by 0x00")
            if v["id"] == flip:
                msg = msg[:-1] + bytes([msg[-1] ^ 1])
            if len(sig) != 3309 or v["signed_by"] not in keys or not ver.verify(keys[v["signed_by"]], msg, sig):
                faults.append(f"{v['id']}: OpenSSL does not verify the signature")
    finally:
        ver.close()
    print("\n".join(faults) or f"statements: {len(doc['vectors'])} vectors under {len(have)} prefixes and {len(doc['keys'])} keys verify with OpenSSL")
    sys.exit(1 if faults else 0)


if __name__ == "__main__":
    main()
