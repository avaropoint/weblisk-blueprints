#!/bin/sh
# Runs the corpus's checks, each with the control that proves it reaches what
# it claims to. Exits 0 only when every check passes and every control fails.
# Needs python3 with PyYAML, and OpenSSL 3.5 or later (as $OPENSSL or on PATH);
# the circl and noble legs of the statement vectors also need Go and node with
# the pinned noble (checks/ml-dsa).
cd "$(dirname "$0")/.." || exit 2
# retired.py imports ids.py; leave no bytecode in the corpus.
export PYTHONDONTWRITEBYTECODE=1
fails=0
tmp=$(mktemp -d) || exit 2
trap 'rm -rf "$tmp"' EXIT

# expect <exit status> <description> <command...>
expect() {
	want=$1 what=$2
	shift 2
	"$@" >"$tmp/out" 2>&1
	got=$?
	if [ "$got" -eq "$want" ]; then
		echo "ok   $what"
	else
		echo "FAIL $what (exit $got, want $want)"
		sed 's/^/     /' "$tmp/out"
		fails=$((fails + 1))
	fi
}

# The id grammar against its vectors, and an accept-everything parser that
# must be reported on every invalid vector.
expect 0 "ids: every vector agrees with schemas/names.md" python3 checks/ids.py
expect 1 "ids control: an accept-everything parser fails" python3 checks/ids.py --stub
invalid=$(python3 -c 'import json; print(len(json.load(open("vectors/ids.json"))["invalid"]))')
reported=$(python3 checks/ids.py --stub | grep -c '^invalid ')
if [ "$reported" -eq "$invalid" ]; then
	echo "ok   ids control: all $invalid invalid vectors reported"
else
	echo "FAIL ids control: $reported of $invalid invalid vectors reported"
	fails=$((fails + 1))
fi

# The names check on this corpus, and on a fixture that names a namespace
# nobody reserved. The fixture's name is assembled here so that this file
# does not itself name it.
expect 0 "names: no unreserved namespace in this corpus" python3 checks/names.py
ns=ac
ns="${ns}me"
printf 'requires: [//%s/ohs/policy]\n' "$ns" >"$tmp/fixture.md"
expect 1 "names control: a fixture naming //$ns/ fails" python3 checks/names.py --scan "$tmp"
if [ "$(grep -c "namespace '$ns'" "$tmp/out")" -eq 1 ] && [ "$(wc -l <"$tmp/out")" -eq 1 ]; then
	echo "ok   names control: exactly one finding, naming $ns"
else
	echo "FAIL names control: want exactly one finding naming $ns"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# RETIRED.md's entries, read as a tool reads them; a copy missing its last
# entry, and a copy whose allowance has already ended, must each be reported.
expect 0 "retired: one well-formed entry per row" python3 checks/retired.py
python3 - "$tmp" <<'PY'
import re, sys
text = open("RETIRED.md", encoding="utf-8").read()
head, block = text.split("```yaml\n", 1)
entries = block.split("\n- retired:")
open(sys.argv[1] + "/short.md", "w").write(head + "```yaml\n" + "\n- retired:".join(entries[:-1]) + "\n```\n")
# The first allowance whose file is at 1.0.0 or above, cut back to end at
# 1.0.0. Derived, because a named allowance is taken out when its file moves.
def major(rel):
    m = re.search(r"^version:\s*['\"]?(\d+)\.", open(rel + ".md", encoding="utf-8").read(2000), re.M)
    return int(m.group(1)) if m else 0
end = next(m for m in re.finditer(r"until: ([\w/.-]+)@[\d.]+\}", text) if major(m.group(1)) >= 1)
open(sys.argv[1] + "/ended.md", "w").write(text[: end.start()] + "until: " + end.group(1) + "@1.0.0}" + text[end.end() :])
PY
expect 1 "retired control: a row without its entry fails" python3 checks/retired.py --file "$tmp/short.md"
grep -q "table rows and" "$tmp/out" || { echo "FAIL retired control: the missing entry was not what was reported"; fails=$((fails + 1)); }
expect 1 "retired control: an allowance its file has passed fails" python3 checks/retired.py --file "$tmp/ended.md"
grep -q "has reached it" "$tmp/out" || { echo "FAIL retired control: the ended allowance was not what was reported"; fails=$((fails + 1)); }

# Every mapping's wire timestamp against one vector, and a mapping changed to
# milliseconds that must be the one disagreement reported.
expect 0 "timestamp-wire: every mapping agrees with the vector" python3 checks/timestamp-wire.py
expect 0 "timestamp-wire control: a mapping in milliseconds is reported" python3 checks/timestamp-wire.py --control

# The fixed-form statement vectors against OpenSSL, which did not make them;
# the signed directory push must have one. Copies whose push body differs by
# one byte, and whose push is signed by another key, must each fail.
expect 0 "fixed-form: every vector verifies with OpenSSL, and the directory push has one" python3 checks/fixed-form.py --require-body weblisk/directory/v1
python3 - "$tmp" <<'PY'
import json, sys
p = "vectors/fixed-form-statements.json"
t = open(p, encoding="utf-8").read()
body = '"http://content-analyzer.example:9710"'
assert t.count(body) == 1
open(sys.argv[1] + "/byte.json", "w", encoding="utf-8").write(t.replace(body, body.replace("9710", "9711")))
d = json.loads(t)
push = next(v for v in d["vectors"] if v["id"] == "directory-push-1")
other = next(v for v in d["vectors"] if v["signed_by"] != push["signed_by"])
push["signature"] = push["body"]["signature"] = other["signature"]
open(sys.argv[1] + "/key.json", "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False))
PY
expect 1 "fixed-form control: a push body one byte changed fails" python3 checks/fixed-form.py --file "$tmp/byte.json"
grep -q "^directory-push-1: the signature does not verify over the statement rebuilt from the body" "$tmp/out" || { echo "FAIL fixed-form control: the changed body was not what was reported"; fails=$((fails + 1)); }
expect 1 "fixed-form control: a push signed by another key fails" python3 checks/fixed-form.py --file "$tmp/key.json"
grep -q "^directory-push-1: OpenSSL does not verify the signature" "$tmp/out" || { echo "FAIL fixed-form control: the wrong key was not what was reported"; fails=$((fails + 1)); }

# Requirement and check ids carried as comments: every id covered, and the
# push's refusal of an unsigned body has its check. A copy with one check's
# covers removed must fail, naming the id it left uncovered.
expect 0 "wl-ids: every marked requirement is covered, and an unsigned push is refused" python3 checks/wl-ids.py --require protocol/spec.md:unsigned-push-refused
sed 's/wl:check stale-push-refused covers directory-push-refuse-stale/wl:check stale-push-refused covers directory-push-refuse-unsigned/' protocol/spec.md >"$tmp/spec.md"
expect 1 "wl-ids control: a requirement no check covers fails" python3 checks/wl-ids.py "$tmp/spec.md"
if grep -q "wl:id directory-push-refuse-stale is covered by no wl:check" "$tmp/out" && [ "$(grep -c ': wl:' "$tmp/out")" -eq 1 ]; then
	echo "ok   wl-ids control: exactly one finding, naming directory-push-refuse-stale"
else
	echo "FAIL wl-ids control: want exactly one finding naming directory-push-refuse-stale"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# No text says the directory push is unauthenticated, now that it is signed.
# A copy of client.md that says so again, across a line break, must fail.
expect 0 "push-claims: no text says the directory push is unauthenticated" python3 checks/push-claims.py
sed 's/^`POST \/v1\/services` with a signature that verifies under the orchestrator.s key$/`POST \/v1\/services` is unauthenticated/' architecture/client.md >"$tmp/client.md"
expect 1 "push-claims control: a copy of client.md calling the push unauthenticated fails" python3 checks/push-claims.py "$tmp/client.md"

# Every grammar vector against its expected projection; a copy whose
# projection leaves a one-byte gap, and a copy missing a projection, must each
# be reported, once.
expect 0 "spans: every grammar vector is partitioned by its projection" python3 checks/spans.py
mkdir "$tmp/gap" "$tmp/lone"
cp vectors/grammar/minimal.md vectors/grammar/minimal.projection.json "$tmp/gap/"
python3 - "$tmp/gap/minimal.projection.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
p["parts"][1]["span"][0] += 1
json.dump(p, open(sys.argv[1], "w"))
PY
expect 1 "spans control: a projection with a one-byte gap fails" python3 checks/spans.py --dir "$tmp/gap"
if [ "$(grep -c '^minimal: gap at byte' "$tmp/out")" -eq 1 ] && [ "$(wc -l <"$tmp/out")" -eq 1 ]; then
	echo "ok   spans control: exactly one finding, the gap"
else
	echo "FAIL spans control: want exactly one finding, the gap"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
cp vectors/grammar/minimal.md vectors/grammar/minimal.projection.json vectors/grammar/crlf.md "$tmp/lone/"
expect 1 "spans control: a vector without a projection fails" python3 checks/spans.py --dir "$tmp/lone"
grep -q '^crlf.md: no expected projection$' "$tmp/out" || { echo "FAIL spans control: the missing projection was not what was reported"; fails=$((fails + 1)); }
mkdir "$tmp/none"
expect 1 "spans control: a directory with no vectors fails" python3 checks/spans.py --dir "$tmp/none"
grep -q '^no grammar vectors in ' "$tmp/out" || { echo "FAIL spans control: the empty directory was not what was reported"; fails=$((fails + 1)); }

# Every finding code's policy, and the policy each vector's findings carry; a
# vector whose multi-root finding is only reported, and a family.md that gives
# multi-root no policy, must each be reported, once.
expect 0 "findings: every code has one policy, and every vector carries it" python3 checks/findings.py
mkdir "$tmp/lax"
cp vectors/grammar/multi-root.md vectors/grammar/multi-root.projection.json "$tmp/lax/"
python3 - "$tmp/lax/multi-root.projection.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
next(f for f in p["findings"] if f["code"] == "multi-root")["policy"] = "report"
json.dump(p, open(sys.argv[1], "w"))
PY
expect 1 "findings control: a multi-root finding that is only reported fails" python3 checks/findings.py --dir "$tmp/lax"
if [ "$(grep -c '^multi-root: multi-root is report, its policy is refuse$' "$tmp/out")" -eq 1 ] && [ "$(wc -l <"$tmp/out")" -eq 1 ]; then
	echo "ok   findings control: exactly one finding, the policy"
else
	echo "FAIL findings control: want exactly one finding, the policy"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
sed 's/ block-missing, multi-root,/ block-missing,/' schemas/family.md >"$tmp/family.md"
expect 1 "findings control: a code with no policy fails" python3 checks/findings.py --family "$tmp/family.md" --dir "$tmp/none"
grep -q '^multi-root: no policy$' "$tmp/out" || { echo "FAIL findings control: the code with no policy was not what was reported"; fails=$((fails + 1)); }
# A missing key header.required names is only ever reported; a migration
# vector that refuses it must be reported, once. A declaration with CRLF line
# ends reads as the same declaration.
mkdir "$tmp/strict"
cp vectors/grammar/migration.md vectors/grammar/migration.projection.json "$tmp/strict/"
python3 - "$tmp/strict/migration.projection.json" <<'PY'
import json, sys
p = json.load(open(sys.argv[1]))
next(f for f in p["findings"] if f["code"] == "missing-key")["policy"] = "refuse"
json.dump(p, open(sys.argv[1], "w"))
PY
expect 1 "findings control: a missing-key finding that is refused fails" python3 checks/findings.py --dir "$tmp/strict"
grep -q '^migration: missing-key is refuse, its policy is report$' "$tmp/out" && [ "$(wc -l <"$tmp/out")" -eq 1 ] || { echo "FAIL findings control: the refused missing-key was not the one finding"; fails=$((fails + 1)); }
python3 -c 'import sys; d = open(sys.argv[1], "rb").read(); open(sys.argv[2], "wb").write(d.replace(b"\n", b"\r\n"))' schemas/family.md "$tmp/family-crlf.md"
expect 0 "findings: a CRLF copy of family.md reads as the same declaration" python3 checks/findings.py --family "$tmp/family-crlf.md"

# Every $ref in a family declaration resolves to a definition; a copy of the
# test declaration citing the short form, which names no file, must be
# reported, once for each of its four refs and for nothing else.
expect 0 "refs: every \$ref in a declaration resolves" python3 checks/refs.py
mkdir "$tmp/short"
sed 's|"schemas/blocks#/|"blocks#/|' vectors/grammar/test-blueprint.md >"$tmp/short/test-blueprint.md"
expect 1 "refs control: a declaration citing blocks#/\$defs/ fails" python3 checks/refs.py --scan "$tmp/short"
if [ "$(grep -c 'names blocks, which is no file of this repository$' "$tmp/out")" -eq 4 ] && [ "$(wc -l <"$tmp/out")" -eq 4 ]; then
	echo "ok   refs control: exactly the four short refs"
else
	echo "FAIL refs control: want exactly the four short refs"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# The architecture family's declaration and template are grammar vectors, each
# an exact copy of the file it pins, so changing either changes the projection
# a walker is held to; a copy one byte off must be reported.
for pair in "schemas/architecture.md architecture" "templates/architecture.md architecture-template"; do
	set -- $pair
	expect 0 "vectors: vectors/grammar/$2.md is the copy of $1" cmp "$1" "vectors/grammar/$2.md"
done
cp templates/architecture.md "$tmp/template.md" && printf '\n' >>"$tmp/template.md"
expect 1 "vectors control: a copy one byte longer than its template fails" cmp templates/architecture.md "$tmp/template.md"

# The share of architecture's bytes no slot declares, against the 53% its older
# schema left undeclared, measured at corpus 3fc8d6a before any family existed:
# a family or a walker that reads the files differently lands far from it. A
# copy of the declaration without its Dependencies slot must, and a
# declaration with no sections cannot be measured at all.
expect 0 "coverage: architecture's bytes in no slot are within 2 points of 53%" python3 checks/coverage.py schemas/architecture --expect 53 --within 2
awk '/slot: dependencies,/ { skip = 2 } skip-- > 0 { next } 1' schemas/architecture.md >"$tmp/architecture.md"
expect 1 "coverage control: a declaration without its Dependencies slot fails" python3 checks/coverage.py schemas/architecture --decl "$tmp/architecture.md" --expect 53 --within 2
grep -q '% in no slot' "$tmp/out" && grep -q '^dependencies ' "$tmp/out" && { echo "FAIL coverage control: the Dependencies slot was not what was removed"; fails=$((fails + 1)); }
expect 1 "coverage control: a declaration with no sections fails" python3 checks/coverage.py schemas/architecture --decl schemas/names.md
grep -q 'declares no sections' "$tmp/out" || { echo "FAIL coverage control: the missing sections were not what was reported"; fails=$((fails + 1)); }

# A slot that holds an interface block produces that interface's file: serves
# an OpenAPI document, events an AsyncAPI one (plan section 1.2). A value the
# declaration drops leaves the build's unproduced report nothing to report, so
# the pairs are held here until a mapping binds them. A copy of the declaration
# without api.asyncapi must fail, naming the interface slot.
expect 0 "produces: architecture's serves slot produces api.openapi" python3 checks/produces.py schemas/architecture serves api.openapi
expect 0 "produces: architecture's events slot produces api.asyncapi" python3 checks/produces.py schemas/architecture events api.asyncapi
sed 's/produces: \[code.route, api.openapi, api.asyncapi\]/produces: [code.route, api.openapi]/' schemas/architecture.md >"$tmp/noasync.md"
expect 1 "produces control: a declaration without api.asyncapi fails" python3 checks/produces.py schemas/architecture events api.asyncapi --decl "$tmp/noasync.md"
grep -q '^schemas/architecture: slot interface holds events and does not produce api.asyncapi$' "$tmp/out" || { echo "FAIL produces control: the interface slot was not what was reported"; fails=$((fails + 1)); }

# The fabric's reach depth has one home (D23); a copy of architecture/ in which
# change-management states its own depth again must report exactly two places.
expect 0 "reach-depth: one home, every citation resolves" python3 checks/reach-depth.py
mkdir -p "$tmp/rd" && cp -R architecture "$tmp/rd/"
sed 's|^  depth_limit: requirement://weblisk/architecture/fabric:reach-max-depth$|  depth_limit: 10|' architecture/change-management.md >"$tmp/rd/architecture/change-management.md"
expect 1 "reach-depth control: a second stated depth fails" python3 checks/reach-depth.py --root "$tmp/rd"
if [ "$(grep -c ' = ' "$tmp/out")" -eq 2 ] && grep -q '^architecture/change-management.md:[0-9]*: depth_limit = 10$' "$tmp/out"; then
	echo "ok   reach-depth control: exactly two places, the restored one among them"
else
	echo "FAIL reach-depth control: want exactly two places, change-management's depth_limit among them"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# A depth that bounds no walk is not the reach depth: a copy with a queue
# depth and a nesting depth added still has one home, and a copy that adds a
# traversal block's max_depth again has two.
mkdir -p "$tmp/rq" && cp -R architecture "$tmp/rq/"
printf '```yaml\nlimits:\n  max_queue_depth: 1000\n  max_nesting_depth: 20\n```\n' >"$tmp/rq/architecture/queue-fixture.md"
expect 0 "reach-depth control: a queue or nesting depth is not a second home" python3 checks/reach-depth.py --root "$tmp/rq"
printf '```yaml\nfabric:\n  traversal:\n    max_depth: 6\n```\n' >"$tmp/rq/architecture/queue-fixture.md"
expect 1 "reach-depth control: a traversal max_depth is a second home" python3 checks/reach-depth.py --root "$tmp/rq"
grep -q '^architecture/queue-fixture.md:4: max_depth = 6$' "$tmp/out" || { echo "FAIL reach-depth control: the traversal max_depth was not what was reported"; fails=$((fails + 1)); }

# fabric.md's own citations resolve too: a copy citing a misspelt fabric
# requirement from inside fabric.md must report exactly that citation.
mkdir -p "$tmp/rf" && cp -R architecture "$tmp/rf/"
printf '\nSee requirement://weblisk/architecture/fabric:reach-max-dept.\n' >>"$tmp/rf/architecture/fabric.md"
expect 1 "reach-depth control: a misspelt citation inside fabric.md fails" python3 checks/reach-depth.py --root "$tmp/rf"
grep -q '^architecture/fabric.md:[0-9]*: cites requirement://weblisk/architecture/fabric:reach-max-dept,' "$tmp/out" || { echo "FAIL reach-depth control: the misspelt citation was not what was reported"; fails=$((fails + 1)); }

# The relation table is read as kinds.md writes it: a row naming several
# relations declares each, "any content kind" is the any fallback, and
# "the same kind" relates a kind only to itself.
expect 0 "fabric-ledger relations: supersedes from blueprint to blueprint is declared" python3 checks/fabric-ledger.py --relation supersedes blueprint blueprint
expect 0 "fabric-ledger relations: mentions from policy to control is declared" python3 checks/fabric-ledger.py --relation mentions policy control
expect 0 "fabric-ledger relations: copied_from from policy to policy is declared" python3 checks/fabric-ledger.py --relation copied_from policy policy
expect 1 "fabric-ledger relations control: copied_from from policy to procedure is not" python3 checks/fabric-ledger.py --relation copied_from policy procedure

# The fabric ledger vector chains; a copy with one entry altered must fail at
# exactly that entry and nowhere else.
expect 0 "fabric-ledger: the vector's chain verifies" python3 checks/fabric-ledger.py
python3 - "$tmp/ledger.json" <<'PY'
import json, sys
v = json.load(open("vectors/fabric-ledger.json", encoding="utf-8"))
v["entries"][2]["claim"]["basis"] += "."
json.dump(v, open(sys.argv[1], "w", encoding="utf-8"))
PY
expect 1 "fabric-ledger control: a copy with entry 3 altered fails" python3 checks/fabric-ledger.py --file "$tmp/ledger.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^seq 3: ' "$tmp/out"; then
	echo "ok   fabric-ledger control: exactly one fault, at seq 3"
else
	echo "FAIL fabric-ledger control: want exactly one fault, at seq 3"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Each claim in the vector is a relation schemas/kinds.md declares, and an
# end whose kind is not versioned cites a projection. A copy whose provider
# end cites a bare version, and a copy relating code to a mapping rule by a
# relation kinds.md does not declare, must each fail at that entry.
python3 - "$tmp" <<'PY'
import json, sys
v = json.load(open("vectors/fabric-ledger.json", encoding="utf-8"))
del v["entries"][2]["claim"]["identity"]["to"]["cited_version"]["projection"]
json.dump(v, open(sys.argv[1] + "/bare.json", "w", encoding="utf-8"))
v = json.load(open("vectors/fabric-ledger.json", encoding="utf-8"))
v["entries"][1]["claim"]["identity"]["relation"] = "verifies"
json.dump(v, open(sys.argv[1] + "/undeclared.json", "w", encoding="utf-8"))
PY
expect 1 "fabric-ledger control: a provider end citing a bare version fails" python3 checks/fabric-ledger.py --file "$tmp/bare.json"
grep -q '^seq 3: .*provider end cites a version its kind does not have' "$tmp/out" || { echo "FAIL fabric-ledger control: the bare provider version was not what was reported"; fails=$((fails + 1)); }
expect 1 "fabric-ledger control: an undeclared relation fails" python3 checks/fabric-ledger.py --file "$tmp/undeclared.json"
grep -q '^seq 2: .*verifies from code to mapping is not a relation' "$tmp/out" || { echo "FAIL fabric-ledger control: the undeclared relation was not what was reported"; fails=$((fails + 1)); }

# A cited_version field the fabric's ContentIdentity binding lacks is one a
# generated fabric would never read; a copy of fabric.md bound without
# projection must report exactly that field.
mkdir -p "$tmp/fb" && sed 's/fields_used: \[algorithm, digest, size, projection\]/fields_used: [algorithm, digest, size]/' architecture/fabric.md >"$tmp/fb/fabric.md"
expect 1 "fabric-ledger control: a ContentIdentity binding without projection fails" python3 checks/fabric-ledger.py --fabric "$tmp/fb/fabric.md"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^cited_version field projection .* is not in' "$tmp/out"; then
	echo "ok   fabric-ledger control: exactly one fault, the unbound projection"
else
	echo "FAIL fabric-ledger control: want exactly one fault, the unbound projection"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every place bare hex is still written is named as a gap by
# content-identity's digest-spelling rule, and nothing else; a copy whose rule
# forgets protocol/types must report exactly protocol/types.
expect 0 "digest-spelling: every bare-hex digest is a named gap" python3 checks/digest-spelling.py
mkdir -p "$tmp/ds" && cp -R architecture protocol patterns schemas "$tmp/ds/"
sed "s/; and protocol\/types AuditEntry's \`previous_hash\`//" patterns/content-identity.md >"$tmp/ds/patterns/content-identity.md"
expect 1 "digest-spelling control: a gap the rule forgets fails" python3 checks/digest-spelling.py --root "$tmp/ds"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^protocol/types.md: writes a bare-hex SHA-256' "$tmp/out"; then
	echo "ok   digest-spelling control: exactly one finding, protocol/types"
else
	echo "FAIL digest-spelling control: want exactly one finding, protocol/types"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every type ref in the weblisk namespace names a declared type; a copy that
# misspells the run statement's build type must report exactly that ref.
expect 0 "type-refs: every type ref names a declared type" python3 checks/type-refs.py
mkdir -p "$tmp/tr" && cp -R schemas protocol "$tmp/tr/"
sed 's|run-statement:RunStatement$|run-statement:RunStatment|' schemas/run-statement.md >"$tmp/tr/schemas/run-statement.md"
expect 1 "type-refs control: a misspelt type ref fails" python3 checks/type-refs.py --root "$tmp/tr"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^schemas/run-statement.md:[0-9]*: type://weblisk/schemas/run-statement:RunStatment names a type' "$tmp/out"; then
	echo "ok   type-refs control: exactly one finding, the misspelt build type"
else
	echo "FAIL type-refs control: want exactly one finding, the misspelt build type"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Requirement ids in comments, and a copy of the one complete file with its
# last wl:check removed: each id only that check covered must be reported.
expect 0 "requirement-ids: every id declared once and every covers resolved" python3 checks/requirement-ids.py
complete=$(grep -rlx --include='*.md' -- '<!-- wl:ids complete -->' . | head -1)
lost=$(python3 - "$complete" "$tmp/uncovered.md" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
checks = list(re.finditer(r" ?<!-- wl:check (\S+) covers ([^>]*?) -->", text))
last = checks[-1]
others = {i for c in checks[:-1] for i in c.group(2).split()}
open(sys.argv[2], "w", encoding="utf-8").write(text[: last.start()] + text[last.end() :])
print(" ".join(i for i in last.group(2).split() if i not in others))
PY
)
expect 1 "requirement-ids control: a check removed from $complete fails" python3 checks/requirement-ids.py --file "$tmp/uncovered.md"
for id in $lost; do
	grep -q "wl:id '$id' is covered by no wl:check" "$tmp/out" || { echo "FAIL requirement-ids control: $id was not reported"; fails=$((fails + 1)); }
done
[ -n "$lost" ] || { echo "FAIL requirement-ids control: the removed check covered nothing only it covers"; fails=$((fails + 1)); }

# The type vectors: every canonical-json case canonicalises, by RFC 8785, to
# what the vector records; a copy whose key-order case is sorted by code point
# instead of UTF-16 code unit, and a copy whose timestamp entry sees a file
# that does not exist, must each be reported, once.
expect 0 "types-vectors: every entry is well formed and every case agrees" python3 checks/types-vectors.py
python3 - "$tmp" <<'PY'
import json, sys
v = json.load(open("vectors/types.json", encoding="utf-8"))
case = next(c for c in v["entries"]["canonical-json"]["cases"] if c["id"] == "rfc8785-3-2-3")
case["canonical"] = "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + json.dumps(x, ensure_ascii=False)
                                   for k, x in sorted(json.loads(case["input"]).items())) + "}"
json.dump(v, open(sys.argv[1] + "/codepoint.json", "w", encoding="utf-8"), ensure_ascii=False)
v = json.load(open("vectors/types.json", encoding="utf-8"))
v["entries"]["timestamp"]["see"] = "vectors/timestamp-missing.json"
json.dump(v, open(sys.argv[1] + "/unseen.json", "w", encoding="utf-8"), ensure_ascii=False)
PY
expect 1 "types-vectors control: keys sorted by code point fail" python3 checks/types-vectors.py --file "$tmp/codepoint.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^canonical-json: rfc8785-3-2-3: ' "$tmp/out"; then
	echo "ok   types-vectors control: exactly one fault, the key-order case"
else
	echo "FAIL types-vectors control: want exactly one fault, the key-order case"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 1 "types-vectors control: a see naming no file fails" python3 checks/types-vectors.py --file "$tmp/unseen.json"
[ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^timestamp: sees vectors/timestamp-missing.json' "$tmp/out" || { echo "FAIL types-vectors control: the missing file was not the one fault"; fails=$((fails + 1)); }

# The mapping fixture's coverage report names all twelve classes and exactly
# three UNFILLED. Each copy below breaks one thing and must be reported for
# exactly that: one more class emptied, one more class filled, a refinement
# dropped, a rule in the wrong form, an UNFILLED rule with no reason, a
# verify naming no entry, and a language claiming a platform's header key.
expect 0 "mapping-coverage: the fixture's report agrees with its expected report" python3 checks/mapping-coverage.py
# The expected report is a file the fixture's author also edits, so agreeing
# with it proves nothing about the count. The three UNFILLED classes are the
# plan's, asserted here on the produced report whatever the expected file says.
mapthree() { # mapthree <what> ; reads $tmp/out, a passing run's summary line
	grep -qx 'mapping-coverage: .* classes filled; UNFILLED: service, ui-unit, interface' "$tmp/out"
}
if mapthree; then
	echo "ok   mapping-coverage: the fixture names exactly service, ui-unit and interface UNFILLED"
else
	echo "FAIL mapping-coverage: the fixture does not name exactly service, ui-unit and interface UNFILLED"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
mkdir "$tmp/map"
fx=vectors/mapping/fake-language.md
mapctl() { # mapctl <name> <python edit of t> ; writes $tmp/map/<name>.md
	python3 - "$fx" "$tmp/map/$1.md" "$2" <<'PY'
import sys
t = open(sys.argv[1], encoding="utf-8").read()
exec(sys.argv[3])
open(sys.argv[2], "w", encoding="utf-8").write(t)
PY
}
mapctl emptied 'i = t.index("  - id: component-module"); j = t.index("  - id: storage-default-backend"); t = t[:i] + t[j:]'
mapctl filled 't = t.replace("```yaml\nrules:\n  - id: lifecycle-build", "```yaml\nrules:\n  - id: page\n    concept: ui-unit/page\n    refines: //test/frameworks/fake:page\n    produce: {via: model, template: \"{name}.page\"}\n  - id: lifecycle-build", 1)'
mapctl unrefined 't = t.replace("    refines: //test/platforms/fake:storage-default-backend\n", "", 1)'
mapctl wrongform 't = t.replace("    evaluate: {argv: [fakec, check, --routes], parse: sarif}", "    produce: {via: model, text: routed}", 1)'
mapctl noreason 't = t.replace("    reason: No reviewed implementation has been named for this fixture.\n", "", 1)'
mapctl nokey 't = t.replace("vectors/types.json#canonical-json", "vectors/types.json#canonical-jsn", 1)'
mapctl platformkey 't = t.replace("provides: fake\n", "provides: fake\naccepts_languages: [fake]\n", 1)'
# identity-primitive is the language's own class, so a language rule on one
# that names a rule it refines claims to narrow an answer its own axis gives.
mapctl selfrefine 't = t.replace("    concept: identity-primitive/canonical-json\n", "    concept: identity-primitive/canonical-json\n    refines: //test/platforms/fake:primitive-canonical-json\n", 1)'
# A class whose only rule is UNAVAILABLE is filled: UNAVAILABLE is a stated
# answer, so the report is unchanged and the expected report still agrees.
mapctl unavailable 't = t.replace("    evaluate: {argv: [fakec, check, --routes], parse: sarif}\n", "    verdict: UNAVAILABLE\n    reason: The fake runtime serves no routes.\n", 1)'
mapexp=vectors/mapping/fake-language.coverage.json
# mapone <name> <description> <pattern the one finding must match>
mapone() {
	expect 1 "mapping-coverage control: $2" python3 checks/mapping-coverage.py --file "$tmp/map/$1.md" --expect "$mapexp"
	if [ "$(grep -cv '^file: ' "$tmp/out")" -eq 1 ] && grep -v '^file: ' "$tmp/out" | grep -q -- "$3"; then
		echo "ok   mapping-coverage control: exactly one finding, $1"
	else
		echo "FAIL mapping-coverage control: want exactly one finding matching $3"
		sed 's/^/     /' "$tmp/out"
		fails=$((fails + 1))
	fi
}
mapone emptied "a fourth class emptied fails" "^component: status 'UNFILLED' (expected 'filled')"
mapone filled "a ninth class filled fails" "^ui-unit: status 'filled' (expected 'UNFILLED')"
mapone unrefined "a storage rule without refines fails" "rule storage-default-backend: storage/default-backend is owned by the platform axis"
mapone wrongform "a check rule that produces fails" "rule check-endpoint-routed: a check rule carries evaluate"
mapone noreason "an UNFILLED rule with no reason fails" "rule primitive-backup-signature: UNFILLED with no reason"
mapone nokey "a verify naming no entry fails" "rule primitive-canonical-json: verify vectors/types.json#canonical-jsn names no entry"
mapone platformkey "a language with accepts_languages fails" "accepts_languages is a platform's"
mapone selfrefine "a language identity-primitive rule with refines fails" "rule primitive-canonical-json: refines //test/platforms/fake:primitive-canonical-json, but its axis owns identity-primitive/canonical-json"
expect 0 "mapping-coverage control: a class whose only rule is UNAVAILABLE reports" python3 checks/mapping-coverage.py --file "$tmp/map/unavailable.md" --report
if python3 -c 'import json,sys; c={x["class"]:x for x in json.load(open(sys.argv[1]))["classes"]}["check"]; sys.exit(0 if c["status"]=="filled" and c["rules"]==["check-endpoint-routed"] else 1)' "$tmp/out"; then
	echo "ok   mapping-coverage control: a class whose only rule is UNAVAILABLE is filled"
else
	echo "FAIL mapping-coverage control: a class whose only rule is UNAVAILABLE is not filled"
	fails=$((fails + 1))
fi
# A fixture and expected report edited together to a fourth UNFILLED class
# agree with each other; the count assertion must still refuse them.
python3 checks/mapping-coverage.py --file "$tmp/map/emptied.md" --report >"$tmp/map/emptied.coverage.json" 2>/dev/null
expect 0 "mapping-coverage control: a fourth UNFILLED class agrees with an expected report edited to match" python3 checks/mapping-coverage.py --file "$tmp/map/emptied.md" --expect "$tmp/map/emptied.coverage.json"
if mapthree; then
	echo "FAIL mapping-coverage control: four UNFILLED classes passed the count assertion"
	fails=$((fails + 1))
else
	echo "ok   mapping-coverage control: four UNFILLED classes fail the count assertion"
fi

# Every fixed-form statement vector verifies with three ML-DSA
# implementations outside every Weblisk tool: OpenSSL (statements.py), circl
# (ml-dsa/main.go, which also makes both vector files again and must write
# them byte for byte) and @noble/post-quantum (ml-dsa/noble.mjs). In each, one
# byte changed in one vector's message must fail exactly that vector, and one
# byte changed in every vector's message must fail every one. statements.py
# also holds every registered prefix to having vectors or being named as
# having none yet. OpenSSL is not optional: a leg that cannot run fails, as
# every check here does. circl and noble are the exception, and only for want
# of the tool: with no go on PATH, or no pinned noble installed, the leg says
# NOT RUN, never ok, and REQUIRE_ALL_VERIFIERS=1 makes that a failure. A go
# that is there and cannot build the generator, from a compile error or a
# module cache without circl, is a failure, never NOT RUN.
nvec=$(python3 -c 'import json; print(len(json.load(open("vectors/fixed-form-statements.json"))["vectors"]))')
notrun=0
built=0
if command -v go >/dev/null 2>&1; then
	if (cd checks/ml-dsa && GOPROXY=off GOFLAGS=-mod=readonly go build -o "$tmp/ml-dsa" .) >"$tmp/circl-build" 2>&1; then
		built=1
	else
		echo "FAIL statements (circl): go is on PATH and the generator does not build"
		sed 's/^/     /' "$tmp/circl-build"
		fails=$((fails + 1))
	fi
fi
for leg in openssl circl noble; do
	case $leg in
	openssl) set -- python3 checks/statements.py ;;
	circl) set -- "$tmp/ml-dsa" --root . check ;;
	noble) set -- node checks/ml-dsa/noble.mjs ;;
	esac
	why=
	if [ "$leg" = circl ]; then
		if ! command -v go >/dev/null 2>&1; then why="no go on PATH"; elif [ "$built" = 0 ]; then continue; fi
	elif [ "$leg" = noble ]; then
		if ! command -v node >/dev/null 2>&1; then
			why="no node on PATH"
		elif ! "$@" >"$tmp/out" 2>&1 && grep -q '^noble: not run: ' "$tmp/out"; then
			why=$(head -1 "$tmp/out")
		fi
	fi
	if [ -n "$why" ]; then
		echo "NOT RUN statements ($leg): $why"
		notrun=$((notrun + 1))
		[ "${REQUIRE_ALL_VERIFIERS:-0}" = 1 ] && fails=$((fails + 1))
		continue
	fi
	expect 0 "statements ($leg): every vector verifies" "$@"
	expect 1 "statements control ($leg): one byte changed in namespace-claim-1 fails" "$@" --flip namespace-claim-1
	if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^namespace-claim-1: .* does not verify' "$tmp/out"; then
		echo "ok   statements control ($leg): exactly one finding, namespace-claim-1"
	else
		echo "FAIL statements control ($leg): want exactly one finding, namespace-claim-1"
		sed 's/^/     /' "$tmp/out"
		fails=$((fails + 1))
	fi
	expect 1 "statements control ($leg): one byte changed in every vector fails" "$@" --flip all
	got=$(grep ': .* does not verify' "$tmp/out" | cut -d: -f1 | sort -u | wc -l | tr -d ' ')
	if [ "$got" -eq "$nvec" ] && [ "$(wc -l <"$tmp/out")" -eq "$nvec" ]; then
		echo "ok   statements control ($leg): all $nvec vectors reported"
	else
		echo "FAIL statements control ($leg): $got of $nvec vectors reported"
		fails=$((fails + 1))
	fi
done

# circl's leg also makes the files again: a copy of the vectors as a generator
# without the namespace statements would write them must be reported as not
# what a rerun writes.
if [ -x "$tmp/ml-dsa" ]; then
	mkdir -p "$tmp/old/vectors" && cp vectors/namespace-registry.json "$tmp/old/vectors/"
	python3 - "$tmp/old/vectors/fixed-form-statements.json" <<'PY'
import json, sys
d = json.load(open("vectors/fixed-form-statements.json", encoding="utf-8"))
d["vectors"] = [v for v in d["vectors"] if not v["prefix"].startswith(("weblisk/namespace-", "weblisk/catalog-release/"))]
d["keys"] = [k for k in d["keys"] if not k["name"].startswith(("holder-", "service"))]
open(sys.argv[1], "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
	expect 1 "statements control (circl): vectors without the namespace statements are not what gen writes" "$tmp/ml-dsa" --root "$tmp/old" check
	grep -qx 'vectors/fixed-form-statements.json: a rerun of gen writes other bytes' "$tmp/out" || { echo "FAIL statements control (circl): the shortened file was not what was reported"; fails=$((fails + 1)); }
fi

# The namespace registry's rules over its vectors; a registry that accepts
# confusable names, one that accepts a one-sided transfer, one that accepts a
# rotation to another identity's key, one that holds no release to the one
# before it, and a verifier that accepts a release its registry's log does not
# hold, must each be reported at exactly the steps the vectors refuse for that
# reason.
expect 0 "namespace-registry: every step gets its stated verdict" python3 checks/namespace-registry.py
for v in accept-confusables:NAMESPACE_CONFUSABLE accept-one-sided:NAMESPACE_TRANSFER_ONE_SIDED rotation-any-identity:NAMESPACE_ROTATION_OTHER_IDENTITY release-unchained:NAMESPACE_RELEASE_BROKEN release-unanchored:NAMESPACE_RELEASE_UNRECORDED; do
	variant=${v%%:*} code=${v#*:}
	# expect() sets $want, so the count has a name of its own.
	steps=$(python3 -c 'import json, sys; print(sum(s["expect"] == sys.argv[1] for q in json.load(open("vectors/namespace-registry.json"))["sequences"] for s in q["steps"]))' "$code")
	expect 1 "namespace-registry control: a registry that does $variant fails" python3 checks/namespace-registry.py --variant "$variant"
	got=$(grep -c " step [0-9]*: got .*, want $code\$" "$tmp/out")
	if [ "$steps" -gt 0 ] && [ "$got" -eq "$steps" ]; then
		echo "ok   namespace-registry control: all $steps $code steps reported"
	else
		echo "FAIL namespace-registry control: $got of $steps $code steps reported"
		fails=$((fails + 1))
	fi
done

# A fixed route segment where {namespace} sits collides with a claimable name:
# a copy of the pattern serving its log at /v1/namespaces/log must report
# exactly that route.
sed 's|/v1/namespace-log |/v1/namespaces/log |' patterns/namespace.md >"$tmp/namespace.md"
expect 1 "namespace-registry control: a route that is also a claimable name fails" python3 checks/namespace-registry.py --pattern "$tmp/namespace.md"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^patterns/namespace.md: /v1/namespaces/log is also /v1/namespaces/{namespace} for the claimable name 'log'$" "$tmp/out"; then
	echo "ok   namespace-registry control: exactly one finding, the log route"
else
	echo "FAIL namespace-registry control: want exactly one finding, the log route"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# A pattern requires nothing above its layer (D11): a copy of the pattern
# that requires architecture/storage again must report exactly that edge.
sed 's|^requires: \[protocol/types, |requires: [protocol/types, architecture/storage, |' patterns/namespace.md >"$tmp/namespace.md"
expect 1 "namespace-registry control: a pattern that requires an architecture blueprint fails" python3 checks/namespace-registry.py --pattern "$tmp/namespace.md"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^patterns/namespace.md: requires architecture/storage, a blueprint above the pattern layer" "$tmp/out"; then
	echo "ok   namespace-registry control: exactly one finding, the architecture/storage edge"
else
	echo "FAIL namespace-registry control: want exactly one finding, the architecture/storage edge"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Four more of the rules broken, each reported only in the sequence that
# exercises it, at its first bite: a registry that lets a retired name be
# claimed again, at the first re-claim; one whose rotation drops the grants, at
# the first act a kept grant allows; one that judges a release at the time its
# signer wrote rather than at its own clock, at the release the holder's
# rotated-out key dates back into its own time; and one that lets a revoked
# grantee release, at that release.
for v in "reclaim-retired:retired-never-returns:step 4: got accepted, want NAMESPACE_RETIRED" \
	"rotation-drops-grants:rotation-keeps-the-binding:step 6: got NAMESPACE_NOT_PUBLISHER, want accepted" \
	"release-signer-time:release-is-recorded:step 5: got accepted, want NAMESPACE_NOT_PUBLISHER" \
	"release-ignores-revocation:release-authority:step 12: got accepted, want NAMESPACE_IDENTITY_UNKNOWN"; do
	# variant:sequence[+other sequences it may also reach]:first bite
	variant=${v%%:*} rest=${v#*:}
	seqs=${rest%%:*} seq=${seqs%%+*} line="$seq ${rest#*:}"
	expect 1 "namespace-registry control: a registry that does $variant fails" python3 checks/namespace-registry.py --variant "$variant"
	if grep -qxF "$line" "$tmp/out" && [ "$(grep -Evc "^($(echo "$seqs" | tr + '|')) " "$tmp/out")" -eq 0 ]; then
		echo "ok   namespace-registry control: $variant is reported in $seqs alone, $seq ${rest#*:} among it"
	else
		echo "FAIL namespace-registry control: want '$line', and nothing outside $seqs"
		sed 's/^/     /' "$tmp/out"
		fails=$((fails + 1))
	fi
done

# A holder whose identity the hub revoked signs nothing more: a registry that
# lets the revoked holder grant, transfer, rotate or retire must be reported
# at exactly those four steps of holder-revoked, and nowhere else.
expect 1 "namespace-registry control: a registry that does holder-ignores-revocation fails" python3 checks/namespace-registry.py --variant holder-ignores-revocation
if [ "$(grep -c '^holder-revoked step [3456]: got ' "$tmp/out")" -eq 4 ] && [ "$(wc -l <"$tmp/out")" -eq 4 ]; then
	echo "ok   namespace-registry control: holder-ignores-revocation is reported at the revoked holder's grant, transfer, rotation and retirement alone"
else
	echo "FAIL namespace-registry control: want holder-revoked steps 3 to 6, and nothing else"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# The place and issuer codes the vectors use are the corpus's own: a copy of
# the vectors adding a place code no standard's applies_in names must report
# exactly that code.
python3 - "$tmp/registry.json" <<'PY'
import json, sys
d = json.load(open("vectors/namespace-registry.json", encoding="utf-8"))
d["never_claimable"]["place_codes"].append("zz")
open(sys.argv[1], "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
expect 1 "namespace-registry control: a place code no standard names fails" python3 checks/namespace-registry.py --vectors "$tmp/registry.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^never_claimable: place code 'zz' is in no standard's applies_in$" "$tmp/out"; then
	echo "ok   namespace-registry control: exactly one finding, the place code"
else
	echo "FAIL namespace-registry control: want exactly one finding, the place code"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# ApprovalRequest has one home, protocol/types (D27); the bindings to it in
# other files are not definitions. A copy of patterns/ that defines it again
# must report exactly the two files.
expect 0 "type-home: every settled type is defined in its home alone" python3 checks/type-home.py
mkdir -p "$tmp/th" && cp -R protocol patterns "$tmp/th/"
printf '\n```yaml\ntypes:\n  - name: ApprovalRequest\n    fields:\n      - name: id\n```\n' >>"$tmp/th/patterns/approval.md"
expect 1 "type-home control: a second definition fails" python3 checks/type-home.py --root "$tmp/th"
if [ "$(grep -c ': defines ApprovalRequest$' "$tmp/out")" -eq 2 ] && grep -q '^patterns/approval.md: defines ApprovalRequest$' "$tmp/out"; then
	echo "ok   type-home control: exactly two files, the second home among them"
else
	echo "FAIL type-home control: want exactly two files, patterns/approval.md among them"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

[ "$notrun" -gt 0 ] && echo "checks: $notrun verifier leg(s) NOT RUN (see above)"
[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
