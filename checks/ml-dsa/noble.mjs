// The corpus's ML-DSA-65 test vectors, checked with @noble/post-quantum, an
// implementation independent of circl (main.go, which made them) and of
// OpenSSL (checks/statements.py).
//
//   node checks/ml-dsa/noble.mjs              check both vector files
//   node checks/ml-dsa/noble.mjs --flip ID    the same, with one byte of vector
//                                             ID's message changed: exactly ID fails
//   node checks/ml-dsa/noble.mjs --flip all   every vector's message changed:
//                                             every one fails
//
// What it holds, in vectors/fixed-form-statements.json: every key's public key
// is what noble derives from its seed; every message is its prefix and fields
// joined by 0x00; every signature verifies, is what noble's own deterministic
// signing makes, and fails with one byte of its message changed. In
// vectors/namespace-registry.json: every signature verifies under the key its
// `by` names, except the one a NAMESPACE_SIGNATURE_INVALID step carries, which
// must not.
//
// noble is pinned by package.json and package-lock.json here. It is read from
// NOBLE_DIR, a directory whose node_modules holds it, or else from this
// directory's own node_modules (npm ci --ignore-scripts). Without it the check
// cannot run, and says so with exit status 2.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const here = dirname(fileURLToPath(import.meta.url));
const corpus = join(here, '..', '..');
const pinned = JSON.parse(readFileSync(join(here, 'package.json'), 'utf8')).dependencies['@noble/post-quantum'];
const from = process.env.NOBLE_DIR || here;
let ml_dsa65, version;
try {
  const require = createRequire(join(from, 'package.json'));
  ({ ml_dsa65 } = require('@noble/post-quantum/ml-dsa.js'));
  version = JSON.parse(readFileSync(join(dirname(require.resolve('@noble/post-quantum/ml-dsa.js')), 'package.json'), 'utf8')).version;
} catch {
  console.log(`noble: not run: no @noble/post-quantum under ${from} (npm ci --ignore-scripts in checks/ml-dsa, or set NOBLE_DIR)`);
  process.exit(2);
}
if (version !== pinned) {
  console.log(`noble: not run: @noble/post-quantum ${version} under ${from}, and ${pinned} is pinned`);
  process.exit(2);
}

const args = process.argv.slice(2);
const flip = args[0] === '--flip' ? args[1] : null;
const fixed = JSON.parse(readFileSync(join(corpus, 'vectors/fixed-form-statements.json'), 'utf8'));
const registry = JSON.parse(readFileSync(join(corpus, 'vectors/namespace-registry.json'), 'utf8'));
if (flip && flip !== 'all' && !fixed.vectors.some((v) => v.id === flip)) {
  console.log(`noble: no vector '${flip}'`);
  process.exit(2);
}

const b64 = (s) => new Uint8Array(Buffer.from(s, 'base64url'));
const eq = (a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)) === 0;
const message = (prefix, fields) =>
  new Uint8Array(Buffer.concat([Buffer.from(prefix), ...fields.flatMap((f) => [Buffer.from([0]), Buffer.from(f.value, 'utf8')])]));
const changed = (m) => { const b = Uint8Array.from(m); b[b.length - 1] ^= 1; return b; };
const faults = [];

const keys = new Map();
for (const k of fixed.keys) {
  const seed = new Uint8Array(Buffer.from(k.seed, 'hex'));
  const pk = b64(k.public_key);
  const kp = ml_dsa65.keygen(seed);
  if (!eq(seed, createHash('sha256').update('weblisk test vector key ' + k.name).digest())
      || createHash('sha256').update(pk).digest('hex') !== k.fingerprint || !eq(kp.publicKey, pk)) {
    faults.push(`key ${k.name}: noble derives another public key from the seed`);
  }
  keys.set(k.name, { pk, sk: kp.secretKey });
}

for (const v of fixed.vectors) {
  const k = keys.get(v.signed_by);
  let msg = new Uint8Array(Buffer.from(v.message, 'hex'));
  const sig = b64(v.signature);
  if (!eq(msg, message(v.prefix, v.fields)) || v.fields.some((f) => f.value.includes('\u0000'))) {
    faults.push(`${v.id}: the message is not the prefix and fields joined by 0x00`);
  }
  if (k && sig.length === 3309 && !eq(ml_dsa65.sign(msg, k.sk, { extraEntropy: false }), sig)) {
    faults.push(`${v.id}: noble's deterministic signature is not the published one`);
  }
  if (flip === v.id || flip === 'all') msg = changed(msg);
  if (!k || sig.length !== 3309 || !ml_dsa65.verify(sig, msg, k.pk)) {
    faults.push(`${v.id}: noble does not verify the signature`);
    continue;
  }
  if (ml_dsa65.verify(sig, changed(msg), k.pk) || ml_dsa65.verify(sig, msg, k.pk, { context: new Uint8Array([0x78]) })) {
    faults.push(`${v.id}: noble verifies it with one byte of the message changed, or under a non-empty context`);
  }
}

let signatures = 0, forged = 0;
for (const q of registry.sequences) {
  q.steps.forEach((s, i) => {
    const st = s.statement || s.release;
    if (!st) return;
    const msg = message(st.prefix, st.fields);
    for (const g of st.signatures) {
      signatures++;
      const k = keys.get(g.by);
      const where = `${q.id} step ${i + 1}`;
      const good = !!k && ml_dsa65.verify(b64(g.signature), msg, k.pk);
      if (s.expect === 'NAMESPACE_SIGNATURE_INVALID') {
        forged++;
        if (good) faults.push(`${where}: the forged signature verifies under ${g.by}`);
      } else if (!good) {
        faults.push(`${where}: noble does not verify the signature by ${g.by}`);
      } else if (ml_dsa65.verify(b64(g.signature), changed(msg), k.pk)) {
        faults.push(`${where}: noble verifies the signature by ${g.by} with one byte of the message changed`);
      }
    }
  });
}
if (forged !== 1) faults.push(`vectors/namespace-registry.json: ${forged} forged signatures, want 1`);

console.log(faults.length ? faults.join('\n')
  : `noble: ${fixed.vectors.length} vectors, ${keys.size} keys and ${signatures} registry signatures verify with @noble/post-quantum ${version}`);
process.exit(faults.length ? 1 : 0);
