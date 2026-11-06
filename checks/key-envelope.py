#!/usr/bin/env python3
"""The weblisk-key-v1 envelope with kdf none (protocol/identity, Private Key
Format), checked against vectors/key-envelope.json with OpenSSL 3.5 or later,
an ML-DSA implementation outside every Weblisk tool.

- the vector key's seed is the stated SHA-256, and OpenSSL derives its public
  key and its 4,032-byte private key from that seed;
- the envelope is exactly what the rule writes for that key: five lines, each
  ended by a line feed, `weblisk-key-v1`, `ml-dsa-65`, `none`, `e30` (the
  base64url of `{}`), and the base64url without padding of the ASCII text of
  the private key in lowercase hex;
- a reader that keeps the rule opens the valid envelope to that private key,
  and refuses every invalid one (hex written unencoded, the raw key bytes
  encoded, padding, uppercase hex).

    checks/key-envelope.py           check the vectors
    checks/key-envelope.py --stub    the same with a reader that accepts every
                                     envelope: every invalid one is reported
    checks/key-envelope.py --write   write the vectors from the seed

Without OpenSSL 3.5 the check cannot run, and says so with exit status 2.
Set OPENSSL to choose the binary.
"""
import base64, hashlib, json, os, re, shutil, subprocess, sys, tempfile

CORPUS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
VECTORS = os.path.join(CORPUS, "vectors", "key-envelope.json")
ALG = bytes.fromhex("300b0609608648016503040312")   # ML-DSA-65, 2.16.840.1.101.3.4.3.18
NAME = "key-envelope"


def pkcs8_seed(seed): return bytes.fromhex("3034020100") + ALG + bytes.fromhex("04228020") + seed
def b64e(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def b64d_strict(s):
    if not re.fullmatch(r"[A-Za-z0-9_-]*", s) or len(s) % 4 == 1:
        raise ValueError("not base64url without padding")
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def openssl():
    for c in (os.environ.get("OPENSSL"), shutil.which("openssl"), "/opt/homebrew/bin/openssl", "/usr/local/bin/openssl"):
        if not c or not os.path.exists(c):
            continue
        v = subprocess.run([c, "version"], capture_output=True, text=True).stdout
        m = re.match(r"OpenSSL (\d+)\.(\d+)", v)
        if m and (int(m[1]), int(m[2])) >= (3, 5):
            return c
    print("key-envelope: not run: no OpenSSL 3.5 or later (set OPENSSL)")
    sys.exit(2)


def derive(seed):
    """The public key and the FIPS 204 private key encoding OpenSSL derives
    from a seed."""
    ob, d = openssl(), tempfile.mkdtemp()
    try:
        p = os.path.join(d, "seed.der")
        open(p, "wb").write(pkcs8_seed(seed))
        pub = subprocess.run([ob, "pkey", "-in", p, "-inform", "DER", "-pubout", "-outform", "DER"], capture_output=True)
        priv = subprocess.run([ob, "pkey", "-in", p, "-inform", "DER", "-outform", "DER",
                               "-provparam", "ml-dsa.output_formats=priv-only"], capture_output=True)
        if pub.returncode or priv.returncode:
            sys.exit("key-envelope: OpenSSL could not derive the vector key")
        return pub.stdout[-1952:], priv.stdout[-4032:]
    finally:
        shutil.rmtree(d, ignore_errors=True)


def write_envelope(priv):
    return "\n".join(["weblisk-key-v1", "ml-dsa-65", "none", b64e(b"{}"), b64e(priv.hex().encode())]) + "\n"


def read_envelope(text):
    """The private key a kdf-none envelope holds, as the rule reads it."""
    if not text.endswith("\n"):
        raise ValueError("the last line is not ended by a line feed")
    lines = text[:-1].split("\n")
    if len(lines) != 5 or lines[:3] != ["weblisk-key-v1", "ml-dsa-65", "none"]:
        raise ValueError("not five lines of a kdf-none ml-dsa-65 envelope")
    if json.loads(b64d_strict(lines[3])) != {}:
        raise ValueError("kdf params are not {}")
    plain = b64d_strict(lines[4])
    if not re.fullmatch(rb"[0-9a-f]{8064}", plain):
        raise ValueError("the decoded field is not 8,064 lowercase hex digits")
    return bytes.fromhex(plain.decode())


def make():
    seed = hashlib.sha256(("weblisk test vector key " + NAME).encode()).digest()
    pub, priv = derive(seed)
    good = write_envelope(priv)
    lines = good[:-1].split("\n")
    def swap(field): return "\n".join(lines[:4] + [field]) + "\n"
    return {
        "about": "The weblisk-key-v1 envelope with kdf none, protocol/identity's Private Key Format. A vector key is no one's identity: its seed is here.",
        "rule": "Five lines, each ended by a line feed: weblisk-key-v1, ml-dsa-65, none, e30 (base64url of {}), and the base64url without padding (RFC 4648 section 5) of the ASCII text of the 4,032-byte FIPS 204 ML-DSA-65 private key encoding written in lowercase hex (8,064 characters). With kdf argon2id the same text is the AES-256-GCM plaintext.",
        "encodings": "seed lowercase hex; public_key base64url without padding; private_key_sha256 the lowercase hex SHA-256 of the 4,032 private key bytes",
        "seeds": "the key is FIPS 204 ML-DSA.KeyGen_internal from a 32-byte seed, the SHA-256 of the ASCII text 'weblisk test vector key ' followed by its name",
        "key": {"name": NAME, "seed": seed.hex(), "public_key": b64e(pub),
                "private_key_sha256": hashlib.sha256(priv).hexdigest()},
        "valid": [{"id": "kdf-none", "envelope": good}],
        "invalid": [
            {"id": "hex-unencoded", "why": "the hex text written as the field, not its base64url", "envelope": swap(priv.hex())},
            {"id": "raw-bytes-encoded", "why": "the base64url of the key bytes rather than of their hex text", "envelope": swap(b64e(priv))},
            {"id": "padded", "why": "base64url with padding", "envelope": swap(lines[4] + "==")},
            {"id": "uppercase-hex", "why": "the hex text in uppercase", "envelope": swap(b64e(priv.hex().upper().encode()))},
        ],
    }


def main():
    if "--write" in sys.argv:
        json.dump(make(), open(VECTORS, "w", encoding="utf-8"), indent=1)
        open(VECTORS, "a").write("\n")
        print(f"key-envelope: wrote {os.path.relpath(VECTORS, CORPUS)}")
        return 0
    stub = "--stub" in sys.argv
    doc = json.load(open(VECTORS, encoding="utf-8"))
    faults = []
    k = doc["key"]
    seed = bytes.fromhex(k["seed"])
    if seed != hashlib.sha256(("weblisk test vector key " + k["name"]).encode()).digest():
        faults.append("the seed is not the stated SHA-256")
    pub, priv = derive(seed)
    if b64e(pub) != k["public_key"]:
        faults.append("OpenSSL derives another public key from the seed")
    if hashlib.sha256(priv).hexdigest() != k["private_key_sha256"]:
        faults.append("OpenSSL derives another private key from the seed")
    for v in doc["valid"]:
        if v["envelope"] != write_envelope(priv):
            faults.append(f"{v['id']}: not the envelope the rule writes for the vector key")
        try:
            if not stub and read_envelope(v["envelope"]) != priv:
                faults.append(f"{v['id']}: opens to another key")
        except ValueError as e:
            faults.append(f"{v['id']}: refused: {e}")
    for v in doc["invalid"]:
        try:
            if not stub:
                read_envelope(v["envelope"])
            faults.append(f"invalid {v['id']}: accepted ({v['why']})")
        except ValueError:
            pass
    for f in faults:
        print(f)
    if faults:
        return 1
    print(f"key-envelope: {len(doc['valid'])} valid and {len(doc['invalid'])} invalid envelopes agree with the rule")
    return 0


if __name__ == "__main__":
    sys.exit(main())
