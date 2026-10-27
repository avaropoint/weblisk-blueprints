// Command ml-dsa makes the corpus's ML-DSA-65 test vectors with Cloudflare's
// circl, and checks them with it. noble.mjs beside it checks the same files
// with @noble/post-quantum, and checks/statements.py with OpenSSL, so each
// vector is verified by three implementations, none of them a Weblisk tool.
//
//	go run . gen                write vectors/fixed-form-statements.json, and
//	                            sign every signature in vectors/namespace-registry.json
//	go run . check              make both again in memory: each must be the
//	                            committed file byte for byte, and every
//	                            signature in them must verify with circl and
//	                            fail with one byte of its message changed
//	go run . check --flip ID    the same, with one byte of vector ID's message
//	                            changed before it is verified: exactly ID fails
//	go run . check --flip all   every vector's message changed: every one fails
//
// Every key is derived from a published seed and every signature is FIPS 204's
// deterministic variant (rnd = 32 zero bytes), so running gen twice writes the
// same files byte for byte. A vector key is no one's identity: its seed is in
// the file it writes.
//
// The registry vectors' statements are authored in
// vectors/namespace-registry.json itself; what gen makes there is only each
// signature, from the statement's own fields and the key its `by` names. The
// one exception is a step whose verdict is NAMESPACE_SIGNATURE_INVALID: its
// signature is made with forgedWith, and must verify under that key and not
// under the key it names.
//
// Exit status 0 when everything holds, 1 when something does not, 2 when the
// check cannot run.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"

	"github.com/cloudflare/circl/sign/mldsa/mldsa65"
)

// seedLabel is the text every seed is the SHA-256 of, followed by the key's
// name. It deliberately does not begin "weblisk/", the start every registered
// fixed-form prefix has, so a seed's input is never mistaken for a statement.
const seedLabel = "weblisk test vector key "

// forgedWith is the key the registry vectors' one forged signature is made
// with, while its `by` names another.
const forgedWith = "holder-2"

const (
	fixedFile    = "vectors/fixed-form-statements.json"
	registryFile = "vectors/namespace-registry.json"
)

type key struct {
	Name        string `json:"name"`
	Plays       string `json:"plays"`
	Seed        string `json:"seed"`
	PublicKey   string `json:"public_key"`
	Fingerprint string `json:"fingerprint"`

	pk *mldsa65.PublicKey
	sk *mldsa65.PrivateKey
}

type field struct {
	Name  string `json:"name"`
	Value string `json:"value"`
}

type vector struct {
	ID        string  `json:"id"`
	Prefix    string  `json:"prefix"`
	Case      string  `json:"case"`
	Fields    []field `json:"fields"`
	Message   string  `json:"message"`
	SignedBy  string  `json:"signed_by"`
	Signature string  `json:"signature"`
	// Body is the JSON body a statement signs a digest of, as sent, with its
	// signature member; only a vector whose statement signs one carries it.
	Body map[string]any `json:"body,omitempty"`
}

type file struct {
	Format       string   `json:"format"`
	Algorithm    string   `json:"algorithm"`
	Signing      string   `json:"signing"`
	Encodings    string   `json:"encodings"`
	Seeds        string   `json:"seeds"`
	Bodies       string   `json:"bodies"`
	NoOnesKey    string   `json:"no_ones_key"`
	MadeWith     string   `json:"made_with"`
	VerifiedWith []string `json:"verified_with"`
	Keys         []*key   `json:"keys"`
	Vectors      []vector `json:"vectors"`
}

var b64 = base64.RawURLEncoding

func sha(s string) string { h := sha256.Sum256([]byte(s)); return hex.EncodeToString(h[:]) }

func newKey(name, plays string) *key {
	seed := sha256.Sum256([]byte(seedLabel + name))
	pk, sk := mldsa65.NewKeyFromSeed(&seed)
	raw, _ := pk.MarshalBinary()
	if len(raw) != 1952 {
		panic("public key size")
	}
	fp := sha256.Sum256(raw)
	return &key{Name: name, Plays: plays, Seed: hex.EncodeToString(seed[:]),
		PublicKey: b64.EncodeToString(raw), Fingerprint: hex.EncodeToString(fp[:]), pk: pk, sk: sk}
}

// statement is protocol/identity's fixed form: prefix, then each field, each
// preceded by one 0x00 byte, and nothing after the last.
func statement(prefix string, fields []field) []byte {
	var b bytes.Buffer
	b.WriteString(prefix)
	for _, f := range fields {
		if bytes.IndexByte([]byte(f.Value), 0) >= 0 {
			panic("a field holds 0x00")
		}
		b.WriteByte(0)
		b.WriteString(f.Value)
	}
	return b.Bytes()
}

func sign(k *key, msg []byte) []byte {
	sig := make([]byte, mldsa65.SignatureSize)
	if err := mldsa65.SignTo(k.sk, msg, nil, false, sig); err != nil {
		panic(err)
	}
	return sig
}

// canonicalDigest is the lowercase hex SHA-256 of body's RFC 8785 form. The
// bodies here hold only ASCII keys and strings and integers well inside 2^53,
// for which encoding/json's sorted, compact, unescaped output is that form.
func canonicalDigest(body map[string]any) string {
	var b bytes.Buffer
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(body); err != nil {
		panic(err)
	}
	h := sha256.Sum256(bytes.TrimSuffix(b.Bytes(), []byte("\n")))
	return hex.EncodeToString(h[:])
}

func flipped(msg []byte) []byte {
	bad := append([]byte(nil), msg...)
	bad[len(bad)-1] ^= 1
	return bad
}

// makeFixed builds vectors/fixed-form-statements.json. verifiedWith is carried
// into the file as given: it names the implementations other than circl that
// verified this content, which this program cannot know.
func makeFixed(verifiedWith []string) ([]byte, map[string]*key, []vector) {
	identity := newKey("identity", "an identity key, proving that it holds its key (weblisk/auth/v1) and re-confirming for a destructive act (weblisk/step-up/v1)")
	hub := newKey("hub", "a hub's first orchestrator key; its fingerprint is the hub_id the credential signs")
	credential := newKey("credential", "an operator's credential, answering a hub's challenge (weblisk/credential-auth/v1)")
	owner1 := newKey("log-owner-1", "a log owner's long-lived key, the log's first authority")
	owner2 := newKey("log-owner-2", "the same owner's next long-lived key, the authority after the succession")
	logKey := newKey("log-key-1", "a log key the first authority introduces, which signs checkpoints")
	records := newKey("sign-records", "a person's sign-records credential (weblisk/content-change/v2)")
	orchestrator := newKey("orchestrator", "an orchestrator's current signing key, which signs the service directory it pushes (weblisk/directory/v2)")
	component := newKey("component", "a registered component's key, as the pushed directory names it; it signs nothing here")
	holder1 := newKey("holder-1", "a person's identity that claims a namespace and signs as its holder (patterns/namespace)")
	holder1Next := newKey("holder-1-next", "the same person's next key, the incoming key of a rotation")
	holder2 := newKey("holder-2", "another person's identity, the incoming holder of a transfer")
	service := newKey("service", "a service identity, which a holder may grant publish and which never holds a namespace")
	keys := []*key{identity, hub, credential, owner1, owner2, logKey, records, orchestrator, component, holder1, holder1Next, holder2, service}

	// Every other value is a stated constant or the SHA-256 of a stated text,
	// so a reader can rebuild it. A fingerprint field is always a real
	// fingerprint of a key above.
	logID := sha("weblisk test vector log: the first entry's stored line")
	contentLogID := sha("weblisk test vector log: a content repository's change log")
	tip := sha("weblisk test vector log: the stored line of entry 42")
	before := "sha256:" + sha("weblisk test vector entry: the bytes before")
	after := "sha256:" + sha("weblisk test vector entry: the bytes after")
	created := "sha256:" + sha("weblisk test vector entry: the bytes created")
	// Each apply decides its own proposal: a proposal id is never reused.
	proposalModify := sha("weblisk test vector proposal: modify")[:32]
	proposalCreate := sha("weblisk test vector proposal: create")[:32]
	proposalDelete := sha("weblisk test vector proposal: delete")[:32]
	credNonce := b64.EncodeToString(mustHex(sha("weblisk test vector credential challenge")))
	authNonce := b64.EncodeToString(mustHex(sha("weblisk test vector auth challenge"))[:16])
	// The namespace registry's log id, the one vectors/namespace-registry.json
	// names as `registry`, a stated constant.
	registry := "051d89f50429c33375260edf33167e397e1e2701ed833ae8230279032e7989a9"
	// Two release indexes (patterns/namespace, The index), the same texts
	// vectors/namespace-registry.json carries for its releases 1 and 2. Each
	// line's digest is the SHA-256 of a stated text naming the ref and the
	// release that set it.
	ns := "vector-one"
	policy, hazards, stopWork := "blueprint://"+ns+"/ohs/policy",
		"requirement://"+ns+"/ohs/policy:report-hazards", "requirement://"+ns+"/ohs/policy:stop-work"
	at := func(ref string, n int) string {
		return "sha256:" + sha(fmt.Sprintf("weblisk test vector entry: %s at release %d", ref, n))
	}
	index1 := "sha256:" + sha(policy+" "+at(policy, 1)+"\n"+hazards+" "+at(hazards, 1)+"\n")
	index2 := "sha256:" + sha(policy+" "+at(policy, 2)+"\n"+hazards+" retired\n"+stopWork+" "+at(stopWork, 2)+"\n")

	cc := func(role, path, op, bef, aft, scope, prop string) []field {
		return []field{{"log id", contentLogID}, {"role", role}, {"path", path}, {"operation", op},
			{"before", bef}, {"after", aft}, {"scope", scope}, {"proposal", prop}, {"signed_at", "2026-01-01T00:00:00.000Z"}}
	}
	claim := func(holder *key, at string) []field {
		return []field{{"registry", registry}, {"namespace", ns}, {"holder", holder.Fingerprint}, {"issued_at", at}}
	}
	grant := func(grantee *key, role, at string) []field {
		return []field{{"registry", registry}, {"namespace", ns}, {"grantee", grantee.Fingerprint}, {"role", role}, {"issued_at", at}}
	}
	transfer := func(from *key, to, kind, at string) []field {
		return []field{{"registry", registry}, {"namespace", ns}, {"from", from.Fingerprint}, {"to", to}, {"kind", kind}, {"issued_at", at}}
	}
	release := func(n, index, previous, at string) []field {
		return []field{{"registry", registry}, {"namespace", ns}, {"release", n}, {"index", index}, {"previous", previous}, {"issued_at", at}}
	}

	type spec struct {
		id, prefix, cse string
		fields          []field
		by              *key
		body            map[string]any
	}
	// The service directory an orchestrator pushes to a component
	// (protocol/spec, POST /v1/services), naming the component's key. Its
	// statement's fields are filled from it below, as a receiver rebuilds them.
	directory := map[string]any{
		"namespaces": map[string]any{"content": "content-analyzer"},
		"routing_table": map[string]any{"content.*": []any{map[string]any{
			"agent": "content-analyzer", "scope": "self", "url": "http://content-analyzer.example:9710/v1/event"}}},
		"services": []any{map[string]any{
			"address_provenance": "self-asserted", "capabilities": []any{"agent:message"},
			"lease_expires_at": "2026-01-01T00:01:00.000Z", "lease_state": "ready", "name": "content-analyzer",
			"public_key": component.PublicKey, "url": "http://content-analyzer.example:9710"}},
		"updated_at": "2026-01-01T00:00:00.000Z",
	}
	const claimP, grantP, transferP, releaseP = "weblisk/namespace-claim/v2", "weblisk/namespace-grant/v2", "weblisk/namespace-transfer/v2", "weblisk/catalog-release/v2"
	specs := []spec{
		{"auth-1", "weblisk/auth/v1", "an identity answers a service's challenge",
			[]field{{"audience", "console.example/link-identity"}, {"nonce", authNonce}}, identity, nil},
		{"credential-auth-1", "weblisk/credential-auth/v1", "a credential answers a hub's challenge; hub_id is the hub key's fingerprint",
			[]field{{"hub_id", hub.Fingerprint}, {"nonce", credNonce}}, credential, nil},
		{"step-up-1", "weblisk/step-up/v1", "an identity re-confirms for a destructive act, over the nonce the same token request's credential answers; hub_id is the hub key's fingerprint",
			[]field{{"hub_id", hub.Fingerprint}, {"nonce", credNonce}, {"control", "DELETE /v1/admin/operators/{name}"}}, identity, nil},
		{"log-key-1", "weblisk/log-key/v2", "the authority introduces a log key; key id is that key's fingerprint",
			[]field{{"log id", logID}, {"key id", logKey.Fingerprint}, {"not_after", "2026-01-01T23:59:59.999Z"}, {"key_protection", "secrets-manager"}}, owner1, nil},
		{"log-checkpoint-1", "weblisk/log-checkpoint/v2", "the log key seals the log at entry 42",
			[]field{{"log id", logID}, {"seq", "42"}, {"tip", tip}, {"issued_at", "2026-01-01T00:00:00.000Z"}}, logKey, nil},
		{"log-succession-outgoing", "weblisk/log-succession/v1", "the outgoing authority hands the log over",
			[]field{{"log id", logID}, {"outgoing", owner1.Fingerprint}, {"incoming", owner2.Fingerprint}}, owner1, nil},
		{"log-succession-incoming", "weblisk/log-succession/v1", "the incoming authority takes the log on: the same bytes, its own signature",
			[]field{{"log id", logID}, {"outgoing", owner1.Fingerprint}, {"incoming", owner2.Fingerprint}}, owner2, nil},
		{"content-change-write-create", "weblisk/content-change/v2", "a person writes a new entry: before and proposal are empty",
			cc("write", "policies/acceptable-use.md", "create", "", created, "internal", ""), records, nil},
		{"content-change-write-modify", "weblisk/content-change/v2", "a person rewrites an entry and the change declares no scope: scope and proposal are empty",
			cc("write", "policies/acceptable-use.md", "modify", before, after, "", ""), records, nil},
		{"content-change-write-delete", "weblisk/content-change/v2", "a person removes an entry: after, scope and proposal are empty",
			cc("write", "policies/acceptable-use.md", "delete", after, "", "", ""), records, nil},
		{"content-change-apply-modify", "weblisk/content-change/v2", "a person decides to apply a proposal that rewrites an entry",
			cc("apply", "procedures/access-review.md", "modify", before, after, "confidential", proposalModify), records, nil},
		{"content-change-apply-create", "weblisk/content-change/v2", "a person decides to apply a proposal that creates an entry: before is empty and proposal is not",
			cc("apply", "procedures/incident-response.md", "create", "", created, "confidential", proposalCreate), records, nil},
		{"content-change-apply-delete", "weblisk/content-change/v2", "a person decides to apply a proposal that removes an entry: after and scope are empty",
			cc("apply", "procedures/access-review.md", "delete", before, "", "", proposalDelete), records, nil},
		{"directory-push-1", "weblisk/directory/v2", "the orchestrator pushes a component its service directory; digest is sha256: and the SHA-256 of the RFC 8785 form of body without its signature member, and body's signature is this signature",
			nil, orchestrator, directory},
		{"namespace-claim-1", claimP, "a person claims an unheld namespace at one registry; holder is the claimant's fingerprint and the claim is signed by that key",
			claim(holder1, "2026-01-01T00:00:00.000Z"), holder1, nil},
		{"namespace-grant-publish", grantP, "the holder grants a service identity publish",
			grant(service, "publish", "2026-01-01T00:01:00.000Z"), holder1, nil},
		{"namespace-grant-withdraw", grantP, "the holder withdraws that grant: role none",
			grant(service, "none", "2026-01-01T00:02:00.000Z"), holder1, nil},
		{"namespace-transfer-outgoing", transferP, "the outgoing holder hands the namespace to another person",
			transfer(holder1, holder2.Fingerprint, "transfer", "2026-01-01T00:03:00.000Z"), holder1, nil},
		{"namespace-transfer-incoming", transferP, "the incoming holder takes it on: the same bytes, its own signature",
			transfer(holder1, holder2.Fingerprint, "transfer", "2026-01-01T00:03:00.000Z"), holder2, nil},
		{"namespace-rotation-outgoing", transferP, "the holder's outgoing key signs a rotation to its incoming key",
			transfer(holder1, holder1Next.Fingerprint, "rotation", "2026-01-01T00:04:00.000Z"), holder1, nil},
		{"namespace-rotation-incoming", transferP, "the holder's incoming key signs the same rotation",
			transfer(holder1, holder1Next.Fingerprint, "rotation", "2026-01-01T00:04:00.000Z"), holder1Next, nil},
		{"namespace-retirement", transferP, "the holder retires the namespace: to is empty and only the outgoing holder signs",
			transfer(holder1, "", "retirement", "2026-01-01T00:05:00.000Z"), holder1, nil},
		{"catalog-release-1", releaseP, "the holder publishes release 1 at one registry: previous is empty",
			release("1", index1, "", "2026-01-01T00:06:00.000Z"), holder1, nil},
		{"catalog-release-2", releaseP, "a publish grantee publishes release 2, naming release 1's index as previous",
			release("2", index2, index1, "2026-01-01T00:07:00.000Z"), service, nil},
	}

	out := file{
		Format:       "Test vectors for the fixed-form statements protocol/identity registers. Each vector's message is the exact bytes signed, as lowercase hex: the prefix, then each field in the order given, each preceded by one 0x00 byte.",
		Algorithm:    "ML-DSA-65, FIPS 204 ML-DSA.Sign (pure, never HashML-DSA), with an empty context string",
		Signing:      "FIPS 204's deterministic variant: rnd is 32 zero bytes. What a signer that cannot sign deterministically tests instead is stated in protocol/identity, Fixed-Form Statements",
		Encodings:    "seed and message lowercase hex; public_key and signature base64url without padding (1,952 and 3,309 bytes decoded); fingerprint the lowercase hex SHA-256 of the decoded public key",
		Seeds:        "each key is FIPS 204 ML-DSA.KeyGen_internal from a 32-byte seed, the SHA-256 of the ASCII text 'weblisk test vector key ' followed by the key's name",
		Bodies:       "A vector whose statement signs a digest of a JSON body carries that body, as sent, in body. Its digest field is 'sha256:' and the lowercase hex SHA-256 of the RFC 8785 canonical form of body without its signature member, and body's signature is the vector's signature",
		NoOnesKey:    "Every key here is a vector key. What that means, and what no implementation may do with one, is stated once, in protocol/identity, Fixed-Form Statements",
		MadeWith:     "github.com/cloudflare/circl v1.6.5",
		VerifiedWith: verifiedWith,
		Keys:         keys,
	}
	for _, s := range specs {
		if s.body != nil {
			s.fields = []field{{"updated_at", fmt.Sprint(s.body["updated_at"])}, {"digest", "sha256:" + canonicalDigest(s.body)}}
		}
		msg := statement(s.prefix, s.fields)
		sig := b64.EncodeToString(sign(s.by, msg))
		v := vector{ID: s.id, Prefix: s.prefix, Case: s.cse, Fields: s.fields,
			Message: hex.EncodeToString(msg), SignedBy: s.by.Name, Signature: sig}
		if s.body != nil {
			v.Body = map[string]any{"signature": sig}
			for k, x := range s.body {
				v.Body[k] = x
			}
		}
		out.Vectors = append(out.Vectors, v)
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetIndent("", "  ")
	enc.SetEscapeHTML(false)
	if err := enc.Encode(out); err != nil {
		panic(err)
	}
	byName := map[string]*key{}
	for _, k := range keys {
		byName[k.Name] = k
	}
	return buf.Bytes(), byName, out.Vectors
}

type signature struct {
	By        string `json:"by"`
	Signature string `json:"signature"`
}

type signed struct {
	Prefix     string      `json:"prefix"`
	Fields     []field     `json:"fields"`
	Signatures []signature `json:"signatures"`
}

type step struct {
	Statement *signed `json:"statement"`
	Verify    *signed `json:"verify"`
	Expect    string  `json:"expect"`
}

type registryDoc struct {
	Sequences []struct {
		ID    string `json:"id"`
		Steps []step `json:"steps"`
	} `json:"sequences"`
}

// regSig is one signature in the registry vectors, in the file's order.
type regSig struct {
	where  string
	msg    []byte
	by     string
	forged bool
	old    string
}

func registrySigs(raw []byte) ([]regSig, error) {
	var doc registryDoc
	if err := json.Unmarshal(raw, &doc); err != nil {
		return nil, err
	}
	var out []regSig
	for _, q := range doc.Sequences {
		for i, s := range q.Steps {
			st := s.Statement
			if st == nil {
				st = s.Verify
			}
			if st == nil {
				continue
			}
			msg := statement(st.Prefix, st.Fields)
			for _, g := range st.Signatures {
				out = append(out, regSig{where: fmt.Sprintf("%s step %d", q.ID, i+1), msg: msg, by: g.By,
					forged: s.Expect == "NAMESPACE_SIGNATURE_INVALID", old: g.Signature})
			}
		}
	}
	return out, nil
}

var sigRE = regexp.MustCompile(`"signature": "([A-Za-z0-9_-]*)"`)

// makeRegistry returns the registry vectors with every signature made again
// from its statement, and nothing else changed.
func makeRegistry(raw []byte, keys map[string]*key) ([]byte, []regSig, error) {
	sigs, err := registrySigs(raw)
	if err != nil {
		return nil, nil, err
	}
	locs := sigRE.FindAllSubmatchIndex(raw, -1)
	if len(locs) != len(sigs) {
		return nil, nil, fmt.Errorf("%s: %d signature fields in the text, %d in the sequences", registryFile, len(locs), len(sigs))
	}
	var out bytes.Buffer
	last := 0
	for i, s := range sigs {
		name := s.by
		if s.forged {
			name = forgedWith
		}
		k, ok := keys[name]
		if !ok {
			return nil, nil, fmt.Errorf("%s: signed by %q, which is no vector key", s.where, name)
		}
		out.Write(raw[last:locs[i][2]])
		out.WriteString(b64.EncodeToString(sign(k, s.msg)))
		last = locs[i][3]
	}
	out.Write(raw[last:])
	return out.Bytes(), sigs, nil
}

func mustHex(s string) []byte {
	b, err := hex.DecodeString(s)
	if err != nil {
		panic(err)
	}
	return b
}

func committedVerifiedWith(root string) []string {
	var f struct {
		VerifiedWith []string `json:"verified_with"`
	}
	if raw, err := os.ReadFile(filepath.Join(root, fixedFile)); err == nil {
		_ = json.Unmarshal(raw, &f)
	}
	return f.VerifiedWith
}

func main() {
	args := os.Args[1:]
	root := "../.."
	if len(args) >= 2 && args[0] == "--root" {
		root, args = args[1], args[2:]
	}
	if len(args) == 0 {
		fmt.Fprintln(os.Stderr, "usage: go run . [--root DIR] gen | check [--flip ID|all]")
		os.Exit(2)
	}
	switch args[0] {
	case "gen":
		verified := committedVerifiedWith(root)
		if v := os.Getenv("VERIFIED_WITH"); v != "" {
			if err := json.Unmarshal([]byte(v), &verified); err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(2)
			}
		}
		fixed, keys, _ := makeFixed(verified)
		raw, err := os.ReadFile(filepath.Join(root, registryFile))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(2)
		}
		reg, _, err := makeRegistry(raw, keys)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		for name, data := range map[string][]byte{fixedFile: fixed, registryFile: reg} {
			if err := os.WriteFile(filepath.Join(root, name), data, 0o644); err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(2)
			}
		}
		fmt.Printf("wrote %s and %s\n", fixedFile, registryFile)
	case "check":
		flip := ""
		if len(args) == 3 && args[1] == "--flip" {
			flip = args[2]
		} else if len(args) != 1 {
			fmt.Fprintln(os.Stderr, "usage: go run . check [--flip ID|all]")
			os.Exit(2)
		}
		os.Exit(check(root, flip))
	default:
		fmt.Fprintln(os.Stderr, "usage: go run . [--root DIR] gen | check [--flip ID|all]")
		os.Exit(2)
	}
}

func check(root, flip string) int {
	var faults []string
	fault := func(f string, a ...any) { faults = append(faults, fmt.Sprintf(f, a...)) }

	committed, err := os.ReadFile(filepath.Join(root, fixedFile))
	if err != nil {
		fmt.Println(err)
		return 2
	}
	fixed, keys, vectors := makeFixed(committedVerifiedWith(root))
	if !bytes.Equal(fixed, committed) {
		fault("%s: a rerun of gen writes other bytes", fixedFile)
	}
	var doc file
	if err := json.Unmarshal(committed, &doc); err != nil {
		fmt.Println(err)
		return 1
	}
	if flip != "" && flip != "all" {
		found := false
		for _, v := range doc.Vectors {
			found = found || v.ID == flip
		}
		if !found {
			fmt.Printf("ml-dsa: no vector %q\n", flip)
			return 2
		}
	}
	// The committed file's own vectors, not the ones made again, so a file
	// that differs is still checked for what it says.
	for _, v := range doc.Vectors {
		k, ok := keys[v.SignedBy]
		msg, err1 := hex.DecodeString(v.Message)
		sig, err2 := b64.DecodeString(v.Signature)
		if !ok || err1 != nil || err2 != nil || len(sig) != mldsa65.SignatureSize {
			fault("%s: circl does not verify the signature", v.ID)
			continue
		}
		if !bytes.Equal(msg, statement(v.Prefix, v.Fields)) {
			fault("%s: the message is not the prefix and fields joined by 0x00", v.ID)
		}
		if flip == v.ID || flip == "all" {
			msg = flipped(msg)
		}
		if !mldsa65.Verify(k.pk, msg, nil, sig) {
			fault("%s: circl does not verify the signature", v.ID)
			continue
		}
		if mldsa65.Verify(k.pk, flipped(msg), nil, sig) || mldsa65.Verify(k.pk, msg, []byte("x"), sig) {
			fault("%s: circl verifies it with one byte of the message changed, or under a non-empty context", v.ID)
		}
	}
	for _, k := range doc.Keys {
		mine, ok := keys[k.Name]
		if !ok || mine.Seed != k.Seed || mine.PublicKey != k.PublicKey || mine.Fingerprint != k.Fingerprint {
			fault("key %s: circl derives another public key from the seed", k.Name)
		}
	}

	raw, err := os.ReadFile(filepath.Join(root, registryFile))
	if err != nil {
		fmt.Println(err)
		return 2
	}
	reg, sigs, err := makeRegistry(raw, keys)
	if err != nil {
		fault("%v", err)
	} else if !bytes.Equal(reg, raw) {
		fault("%s: a rerun of gen signs other bytes", registryFile)
	}
	forged := 0
	for _, s := range sigs {
		k, ok := keys[s.by]
		sig, err := b64.DecodeString(s.old)
		if !ok || err != nil {
			fault("%s: a signature by %q circl cannot read", s.where, s.by)
			continue
		}
		good := mldsa65.Verify(k.pk, s.msg, nil, sig)
		if s.forged {
			forged++
			if good || !mldsa65.Verify(keys[forgedWith].pk, s.msg, nil, sig) {
				fault("%s: the forged signature is not %s's signature under the key %s names", s.where, forgedWith, s.by)
			}
			continue
		}
		if !good {
			fault("%s: circl does not verify the signature by %s", s.where, s.by)
		} else if mldsa65.Verify(k.pk, flipped(s.msg), nil, sig) {
			fault("%s: circl verifies the signature by %s with one byte of the message changed", s.where, s.by)
		}
	}
	if forged != 1 {
		fault("%s: %d forged signatures, want 1", registryFile, forged)
	}
	if len(faults) > 0 {
		for _, f := range faults {
			fmt.Println(f)
		}
		return 1
	}
	fmt.Printf("ml-dsa: %d vectors, %d keys and %d registry signatures verify with circl, and a rerun of gen writes both files byte for byte\n",
		len(vectors), len(keys), len(sigs))
	return 0
}
