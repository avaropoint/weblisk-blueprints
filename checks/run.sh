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

# protocol/conventions' worked values, each computed here from the rule; an
# implementation that writes instants without milliseconds and backs off from
# 2^n must be reported in exactly those two rules.
expect 0 "conventions: every vector is what its rule gives" python3 checks/conventions.py vectors
expect 0 "conventions control: a second-precision instant and a 2^n backoff are reported" python3 checks/conventions.py vectors --control
# No specification restates a rule protocol/conventions holds; a seeded file
# with one restatement of each kind must be reported, and nothing else.
expect 0 "conventions sites: no file restates a convention" python3 checks/conventions.py sites
expect 0 "conventions sites control: one seeded restatement of each kind is reported" python3 checks/conventions.py sites --control

# Every mapping's wire timestamp against the conventions vector, and a mapping
# left in epoch seconds that must be the one disagreement reported; every
# field that holds an instant typed timestamp, and a seeded int64 one reported.
expect 0 "timestamp-wire: every mapping agrees with the vector" python3 checks/timestamp-wire.py
expect 0 "timestamp-wire control: a mapping left in epoch seconds is reported" python3 checks/timestamp-wire.py --control
expect 0 "conventions time-fields: every instant field is a timestamp" python3 checks/conventions.py time-fields
expect 0 "conventions time-fields control: a seeded int64 instant is reported" python3 checks/conventions.py time-fields --control

# The fixed-form statement vectors against OpenSSL, which did not make them;
# the signed directory push must have one. Copies whose push body differs by
# one byte, and whose push is signed by another key, must each fail.
expect 0 "fixed-form: every vector verifies with OpenSSL, and the directory push has one" python3 checks/fixed-form.py --require-body weblisk/directory/v2
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
# schema left undeclared, measured at corpus 3fc8d6a before any family existed,
# 51% once the checklist sweep and its rulings had grown the Verification
# Checklists (a slot) by their citations, and 48% once execution,
# notification, the prompt worker and the model service were written whole in
# content.md's sectioned shape (most of their bytes in slots): a family or a
# walker that reads the files differently lands far from it. A
# copy of the declaration without its Dependencies slot must, and a
# declaration with no sections cannot be measured at all.
expect 0 "coverage: architecture's bytes in no slot are within 2 points of 48%" python3 checks/coverage.py schemas/architecture --expect 48 --within 2
awk '/slot: dependencies,/ { skip = 2 } skip-- > 0 { next } 1' schemas/architecture.md >"$tmp/architecture.md"
expect 1 "coverage control: a declaration without its Dependencies slot fails" python3 checks/coverage.py schemas/architecture --decl "$tmp/architecture.md" --expect 48 --within 2
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

# A walk's findings, from a family declaration and schemas/blocks.md alone
# (checks/families.py). Before it says anything of the corpus it must give
# every grammar vector exactly the findings that vector's projection holds.
expect 0 "families: every grammar vector's findings agree" python3 checks/families.py --vectors

# The programme families in migration mode (schemas/programme-*): every
# programme file walks with nothing refused, and the findings are exactly one
# legacy-key per id: and per declares.obligation.id and one missing-key per
# file with no version:, as counted here from the files themselves.
progs="schemas/programme-map schemas/programme-spec schemas/programme-template"
expect 0 "families: every programme file walks in migration mode" python3 checks/families.py $progs
python3 checks/families.py $progs --counts >"$tmp/walked" 2>&1
python3 - >"$tmp/counted" <<'PY'
import glob, re, yaml
ids = obl = nover = 0
for f in glob.glob("programmes/*/map.md") + glob.glob("programmes/*/specs/*.md") + glob.glob("programmes/*/templates/*.md"):
    h = yaml.safe_load(re.match(r"---\n(.*?)\n---\n", open(f, encoding="utf-8").read(), re.S).group(1))
    ob = (h.get("declares") or {}).get("obligation")
    ids, obl, nover = ids + ("id" in h), obl + (isinstance(ob, dict) and "id" in ob), nover + ("version" not in h)
print(f"{obl} legacy-key report declares.obligation.id\n{ids} legacy-key report id\n{nover} missing-key report version")
PY
if cmp -s "$tmp/walked" "$tmp/counted" && [ "$(wc -l <"$tmp/counted")" -eq 3 ]; then
	echo "ok   families: exactly the counted legacy keys and missing versions ($(paste -sd, - <"$tmp/counted"))"
else
	echo "FAIL families: the findings are not exactly the counted legacy keys and missing versions"
	diff "$tmp/counted" "$tmp/walked" | sed 's/^/     /'
	fails=$((fails + 1))
fi
# Not loose: a spec with a key the family does not declare is refused, once.
sed 's/^structure:/structre:/' programmes/ohs/specs/ohs.certificate-renewal.md >"$tmp/structre.md"
expect 1 "families control: a spec with an undeclared key fails" python3 checks/families.py schemas/programme-spec --file "$tmp/structre.md"
[ "$(grep -c ' refuse ' "$tmp/out")" -eq 1 ] && grep -q ': header-schema refuse /structre$' "$tmp/out" || { echo "FAIL families control: want exactly one refusal, of /structre"; fails=$((fails + 1)); }
# The strict variants are the migration declarations made strict and nothing
# else, and refuse every programme file today; a strict copy that still only
# reports a legacy key fails the comparison.
for f in map spec template; do
	expect 0 "families: schemas/strict/programme-$f is programme-$f made strict" python3 checks/families.py --strict schemas/programme-$f.md schemas/strict/programme-$f.md
	expect 1 "families control: the strict programme-$f refuses programme files" python3 checks/families.py schemas/programme-$f --against schemas/strict/programme-$f.md
	all=$(python3 checks/families.py schemas/programme-$f --counts | sed -n 's/^\([0-9]*\) legacy-key report id$/\1/p')
	refused=$(grep ' refuse' "$tmp/out" | cut -d: -f1 | sort -u | wc -l | tr -d ' ')
	[ -n "$all" ] && [ "$refused" -eq "$all" ] && echo "ok   families control: all $all programme-$f files refused" || { echo "FAIL families control: $refused of ${all:-?} programme-$f files refused"; fails=$((fails + 1)); }
done
sed 's/^    id: refuse$/    id: report/' schemas/strict/programme-spec.md >"$tmp/loose.md"
expect 1 "families control: a strict variant that reports id fails" python3 checks/families.py --strict schemas/programme-spec.md "$tmp/loose.md"
# Every structure a spec or a form names is a document family, every family's
# template walks against it with nothing refused, and no heading opens two of
# a family's slots. A spec naming a structure nobody declares, and a family
# whose Purpose slot takes Scope as an alias, are each reported.
docs="documents/families/policy documents/families/procedure documents/families/standard documents/families/guideline"
expect 0 "families: every spec's structure is a document family" python3 checks/families.py schemas/programme-spec --resolve structure documents/families
expect 0 "families: every form's structure is a document family" python3 checks/families.py schemas/programme-template --resolve frontmatter.structure documents/families
expect 0 "families: every family's template walks against it" python3 checks/families.py --distinct --templates $progs $docs \
	schemas/protocol schemas/pattern schemas/agent schemas/domain schemas/position schemas/policy-domain schemas/instruction
[ -s "$tmp/out" ] && { echo "FAIL families: a template walks with a finding, and each must walk with none"; sed 's/^/     /' "$tmp/out"; fails=$((fails + 1)); }
# A document's header is the organisation's own: a policy carrying uid:, the
# keys a client reads from a header, and a key no family types walks with
# nothing refused. A uid: that is not a string is still refused, once.
awk '{ print } /^kind: policy$/ { print "uid: 0192f3a4-7b1c-7d2e-8f3a-4b5c6d7e8f90"; print "effective_date: 2026-01-01"; print "classification: internal"; print "review_cycle: annual"; print "approved_by: Head of Operations"; print "department: operations" }' templates/policy.md >"$tmp/uid.md"
expect 0 "families: a policy whose header carries uid: walks with nothing refused" python3 checks/families.py documents/families/policy --file "$tmp/uid.md"
sed 's/^uid: .*$/uid: [not, a, string]/' "$tmp/uid.md" >"$tmp/uid-list.md"
expect 1 "families control: a uid: that is not a string is refused" python3 checks/families.py documents/families/policy --file "$tmp/uid-list.md"
[ "$(grep -c ' refuse ' "$tmp/out")" -eq 1 ] && grep -q ': header-schema refuse /uid$' "$tmp/out" || { echo "FAIL families control: want exactly one refusal, of /uid"; fails=$((fails + 1)); }
sed 's/^structure: procedure$/structure: nonesuch/' programmes/ohs/specs/ohs.certificate-renewal.md >"$tmp/nonesuch.md"
expect 1 "families control: a structure no family declares fails" python3 checks/families.py schemas/programme-spec --resolve structure documents/families --file "$tmp/nonesuch.md"
grep -q 'structure: nonesuch names no declaration' "$tmp/out" || { echo "FAIL families control: the unknown structure was not what was reported"; fails=$((fails + 1)); }
sed 's/^    - {slot: purpose, heading: Purpose,/    - {slot: purpose, heading: Purpose, aliases: [scope],/' documents/families/policy.md >"$tmp/policy.md"
expect 1 "families control: a heading opening two slots fails" python3 checks/families.py --distinct --templates documents/families/policy --against "$tmp/policy.md"
grep -q "the heading 'Scope' opens both purpose and scope" "$tmp/out" || { echo "FAIL families control: the shared heading was not what was reported"; fails=$((fails + 1)); }
# Every declaration walks against schemas/family. The families whose files
# are written today in the form they declare walk the files their match
# covers with nothing refused: positions and policy domains in migration mode,
# and the older language, platform and framework files their families read
# until they are rewritten into mapping rules. A match never covers a
# directory's README.md (family-names-declaration); positions/README.md walked
# as a position is refused, so that rule is what these walks rest on. An empty
# --file list is a fault, never a walk of nothing.
expect 0 "families: every declaration walks against schemas/family" python3 checks/families.py --declarations
for fam in position policy-domain language platform framework instruction; do
	expect 0 "families: today's files walk against schemas/$fam by its match" python3 checks/families.py schemas/$fam
done
# An instruction is written to a strict family from its first file: one
# carrying a key the header does not declare is refused, once.
sed 's/^in: \[plan\]$/in: [plan]\nid: plan-names/' instructions/plan-names.md >"$tmp/instruction-id.md"
expect 1 "families control: an instruction stating its own id is refused" python3 checks/families.py schemas/instruction --file "$tmp/instruction-id.md"
[ "$(grep -c ' refuse ' "$tmp/out")" -eq 1 ] && grep -q ': header-schema refuse /id$' "$tmp/out" || { echo "FAIL families control: want exactly one refusal, of /id"; fails=$((fails + 1)); }
expect 1 "families control: positions/README.md walked as a position is refused" python3 checks/families.py schemas/position --file positions/README.md
expect 1 "families control: an empty --file list fails" python3 checks/families.py schemas/position --file

# Every instruction against schemas/instruction.md's requirements, with the
# build steps read from architecture/engine.md (checks/instructions.py). A
# copy with a placeholder its header does not declare, and an engine whose
# accept step calls a model no instruction names, are each reported once.
expect 0 "instructions: every instruction is declared, placed and in a model step" python3 checks/instructions.py
mkdir -p "$tmp/in/architecture" && cp -R instructions "$tmp/in/" && cp architecture/engine.md "$tmp/in/architecture/"
sed 's/^The contract: {{contract}}$/The contract: {{contract}} {{implementation}}/' instructions/translate.md >"$tmp/in/instructions/translate.md"
expect 1 "instructions control: an undeclared placeholder fails" python3 checks/instructions.py --root "$tmp/in"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^instructions/translate.md: instruction-slots-placed: {{implementation}} is written and not declared$' "$tmp/out"; then
	echo "ok   instructions control: exactly one finding, the undeclared placeholder"
else
	echo "FAIL instructions control: want exactly one finding, {{implementation}}"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
cp instructions/translate.md "$tmp/in/instructions/translate.md" && rm "$tmp/in/instructions/advise.md"
expect 1 "instructions control: a model step no instruction names fails" python3 checks/instructions.py --root "$tmp/in"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^architecture/engine.md: instruction-every-step: step accept calls a model, and no instruction names it$' "$tmp/out"; then
	echo "ok   instructions control: exactly one finding, the accept step"
else
	echo "FAIL instructions control: want exactly one finding, the accept step"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi


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

# Criterion ids are frozen by checks/criterion-ids.json. A copy of
# languages/go.md with its first item's id removed, one with that id renamed,
# and the register with that id retired while the file still writes it, must
# each be reported with exactly the faults that change makes.
first=$(python3 -c '
import re, sys
t = open("languages/go.md", encoding="utf-8").read()
print(re.search(r"^- \[ \] .*<!-- wl:check ([a-z0-9-]+) -->$", t, re.M).group(1))')
python3 - "$tmp" "$first" <<'PY'
import json, sys
tmp, cid = sys.argv[1], sys.argv[2]
t = open("languages/go.md", encoding="utf-8").read()
mark = f" <!-- wl:check {cid} -->"
assert t.count(mark) == 1
open(tmp + "/go-noid.md", "w", encoding="utf-8").write(t.replace(mark, ""))
open(tmp + "/go-renamed.md", "w", encoding="utf-8").write(t.replace(mark, f" <!-- wl:check {cid}-x -->"))
r = json.load(open("checks/criterion-ids.json", encoding="utf-8"))
r["files"]["languages/go.md"].remove(cid)
r.setdefault("retired", {}).setdefault("languages/go.md", []).append(cid)
json.dump(r, open(tmp + "/register-retired.json", "w", encoding="utf-8"))
PY
expect 1 "requirement-ids control: an item whose id was removed fails" python3 checks/requirement-ids.py --file "$tmp/go-noid.md" --as languages/go.md
if [ "$(wc -l <"$tmp/out")" -eq 2 ] && grep -q "a checklist item with no id" "$tmp/out" && grep -q "registered id '$first' is no longer written" "$tmp/out"; then
	echo "ok   requirement-ids control: exactly the item and its lost id"
else
	echo "FAIL requirement-ids control: want exactly the item with no id and its lost id"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 1 "requirement-ids control: an id renamed in place fails" python3 checks/requirement-ids.py --file "$tmp/go-renamed.md" --as languages/go.md
if [ "$(wc -l <"$tmp/out")" -eq 2 ] && grep -q "registered id '$first' is no longer written" "$tmp/out" && grep -q "id '$first-x' is not in the register" "$tmp/out"; then
	echo "ok   requirement-ids control: exactly the old id lost and the new one unregistered"
else
	echo "FAIL requirement-ids control: want exactly the old id lost and the new one unregistered"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 1 "requirement-ids control: a retired id written again fails" python3 checks/requirement-ids.py --file languages/go.md --as languages/go.md --register "$tmp/register-retired.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "id '$first' was retired and is never given again" "$tmp/out"; then
	echo "ok   requirement-ids control: exactly the reused id"
else
	echo "FAIL requirement-ids control: want exactly the reused id"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Component kinds and their cardinality, declared once in schemas/kinds.md,
# against the services table; a copy without fabric-service must be reported
# with exactly that service.
expect 0 "component-kinds: every service is a kind with a count" python3 checks/component-kinds.py
grep -v '^    fabric-service: ' schemas/kinds.md >"$tmp/kinds.md"
expect 1 "component-kinds control: a kinds.md without fabric-service fails" python3 checks/component-kinds.py --kinds "$tmp/kinds.md"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "service 'fabric-service' is in the services table and is no component kind" "$tmp/out"; then
	echo "ok   component-kinds control: exactly one finding, fabric-service"
else
	echo "FAIL component-kinds control: want exactly one finding, fabric-service"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every declared check is data of a kind schemas/blocks declares; the kind
# vectors each give exactly their fault. A copy of the orchestrator naming a
# structure query no language declares, and a copy of the valid vectors with
# no topology example, must each be reported with exactly that one finding.
expect 0 "check-kinds: every verifies entry is a declared kind with valid data" python3 checks/check-kinds.py
expect 0 "check-kinds vectors: every example passes and every invalid case gives its fault" python3 checks/check-kinds.py --vectors
sed 's/structure: {query: path-literal, /structure: {query: path-literals, /' architecture/orchestrator.md >"$tmp/orchestrator.md"
expect 1 "check-kinds control: a check naming an undeclared query fails" python3 checks/check-kinds.py --file "$tmp/orchestrator.md" --as architecture/orchestrator.md
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "names structure query 'path-literals', which no language declares" "$tmp/out"; then
	echo "ok   check-kinds control: exactly one finding, the undeclared query"
else
	echo "FAIL check-kinds control: want exactly one finding, the undeclared query"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
# The endpoint-auth vocabulary is closed: a copy of the orchestrator whose
# Audit endpoint says auth "bearer" must be reported with exactly it.
python3 - "$tmp/orch-auth.md" <<'PY'
import sys
t = open("architecture/orchestrator.md", encoding="utf-8").read()
old = 'operation: Audit\n      auth: "token"'
assert t.count(old) == 1
open(sys.argv[1], "w", encoding="utf-8").write(t.replace(old, 'operation: Audit\n      auth: "bearer"'))
PY
expect 1 "check-kinds control: an endpoint auth outside endpoint-auth fails" python3 checks/check-kinds.py --file "$tmp/orch-auth.md" --as architecture/orchestrator.md
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "endpoint 'Audit' has auth 'bearer'" "$tmp/out"; then
	echo "ok   check-kinds control: exactly one finding, the Audit endpoint's auth"
else
	echo "FAIL check-kinds control: want exactly one finding, the Audit endpoint's auth"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
python3 - "$tmp/testing.md" <<'PY'
import re, sys
t = open("architecture/testing.md", encoding="utf-8").read()
m = re.search(r"^  - id: l4-04-standalone\n.*?(?=^  - id: |^```)", t, re.S | re.M)
open(sys.argv[1], "w", encoding="utf-8").write(t[: m.start()] + t[m.end() :])
PY
expect 1 "check-kinds control: a suite without L4-04's check fails" python3 checks/check-kinds.py --file "$tmp/testing.md" --as architecture/testing.md
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "conformance test L4-04 has no check" "$tmp/out"; then
	echo "ok   check-kinds control: exactly one finding, L4-04"
else
	echo "FAIL check-kinds control: want exactly one finding, L4-04"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
mkdir -p "$tmp/ck" && cp vectors/check-kinds/invalid.yaml "$tmp/ck/"
python3 - "$tmp/ck/valid.yaml" <<'PY'
import sys, yaml
v = yaml.safe_load(open("vectors/check-kinds/valid.yaml", encoding="utf-8"))
v["verifies"] = [e for e in v["verifies"] if e.get("check") != "topology"]
yaml.safe_dump(v, open(sys.argv[1], "w", encoding="utf-8"))
PY
expect 1 "check-kinds control: vectors with no topology example fail" python3 checks/check-kinds.py --vectors "$tmp/ck"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "no example of kind 'topology'" "$tmp/out"; then
	echo "ok   check-kinds control: exactly one finding, the missing kind"
else
	echo "FAIL check-kinds control: want exactly one finding, the missing kind"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every language declares its layout, module, toolchain, diagnostics and
# tests, and reads its own toolchain's real output as vectors/languages
# expects. A copy of rust.md without its diagnostics block, and a copy of
# go.md that has lost its pattern for an undefined name, must each be
# reported with exactly that one finding.
expect 0 "language-blocks: every language declares how it is built, read and tested" python3 checks/language-blocks.py
python3 - "$tmp/rust.md" <<'PY'
import re, sys
t = open("languages/rust.md", encoding="utf-8").read()
m = re.search(r"^```yaml\ndiagnostics:\n.*?^```\n", t, re.S | re.M)
open(sys.argv[1], "w", encoding="utf-8").write(t[: m.start()] + t[m.end() :])
PY
expect 1 "language-blocks control: a language without diagnostics fails" python3 checks/language-blocks.py --file "$tmp/rust.md" --as rust
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^rust: no diagnostics block$" "$tmp/out"; then
	echo "ok   language-blocks control: exactly one finding, rust's diagnostics"
else
	echo "FAIL language-blocks control: want exactly one finding, rust's diagnostics"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
grep -v "kind: undefined, pattern: 'undefined:" languages/go.md >"$tmp/go.md"
expect 1 "language-blocks control: a grammar that misreads its vectors fails" python3 checks/language-blocks.py --file "$tmp/go.md" --as go
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^go: diagnostics read " "$tmp/out"; then
	echo "ok   language-blocks control: exactly one finding, go's diagnostics"
else
	echo "FAIL language-blocks control: want exactly one finding, go's diagnostics"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# No type name is declared by two blueprints beyond the known list, which can
# only shrink; a known list without User must report exactly User, and one
# naming a type that no longer collides must report exactly it.
expect 0 "type-collisions: every type name declared twice is known, none new" python3 checks/type-collisions.py
python3 - "$tmp" <<'PY'
import json, sys
k = json.load(open("checks/type-collisions.json", encoding="utf-8"))
k["known"].pop("User")
json.dump(k, open(sys.argv[1] + "/tc-new.json", "w"))
k = json.load(open("checks/type-collisions.json", encoding="utf-8"))
k["known"]["WorkflowPhase"] = ["patterns/workflow.md", "protocol/types.md"]
json.dump(k, open(sys.argv[1] + "/tc-gone.json", "w"))
PY
expect 1 "type-collisions control: a collision not in the list fails" python3 checks/type-collisions.py --known "$tmp/tc-new.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^type User is declared in " "$tmp/out"; then
	echo "ok   type-collisions control: exactly one finding, User"
else
	echo "FAIL type-collisions control: want exactly one finding, User"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 1 "type-collisions control: a settled collision still listed fails" python3 checks/type-collisions.py --known "$tmp/tc-gone.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^type WorkflowPhase no longer collides" "$tmp/out"; then
	echo "ok   type-collisions control: exactly one finding, WorkflowPhase"
else
	echo "FAIL type-collisions control: want exactly one finding, WorkflowPhase"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# No pattern requires the framework, beyond the known list, which can only
# shrink; a list missing command's requirement of architecture/agent must
# report exactly it, and one still naming retry's, removed, exactly that.
expect 0 "layering: every pattern that requires the framework is known, none new" python3 checks/layering.py
python3 - "$tmp" <<'PY'
import json, sys
k = json.load(open("checks/layering.json", encoding="utf-8"))
k["known"].pop("patterns/command")
json.dump(k, open(sys.argv[1] + "/lay-new.json", "w"))
k = json.load(open("checks/layering.json", encoding="utf-8"))
k["known"]["patterns/retry"] = ["architecture/agent"]
json.dump(k, open(sys.argv[1] + "/lay-gone.json", "w"))
PY
expect 1 "layering control: a requirement not in the list fails" python3 checks/layering.py --known "$tmp/lay-new.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^patterns/command requires architecture/agent" "$tmp/out"; then
	echo "ok   layering control: exactly one finding, patterns/command"
else
	echo "FAIL layering control: want exactly one finding, patterns/command"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 1 "layering control: a removed requirement still listed fails" python3 checks/layering.py --known "$tmp/lay-gone.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^patterns/retry no longer requires architecture/agent" "$tmp/out"; then
	echo "ok   layering control: exactly one finding, patterns/retry"
else
	echo "FAIL layering control: want exactly one finding, patterns/retry"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every standard's applies_in names a code of the shipped ISO 3166 list; a
# copy of the standards where one names ZZ must be reported with exactly it.
expect 0 "places: every applies_in names an ISO 3166 code of the shipped list" python3 checks/places.py
mkdir -p "$tmp/std" && cp standards/*.json "$tmp/std/"
python3 - "$tmp/std" <<'PY'
import glob, json, sys
p = next(p for p in sorted(glob.glob(sys.argv[1] + "/*.json")) if json.load(open(p)).get("applies_in", ["international"]) != ["international"])
d = json.load(open(p)); d["applies_in"] = ["ZZ"]; json.dump(d, open(p, "w"))
PY
expect 1 "places control: a standard naming ZZ fails" python3 checks/places.py --standards "$tmp/std"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "applies_in names 'ZZ', which is no ISO 3166 code" "$tmp/out"; then
	echo "ok   places control: exactly one finding, ZZ"
else
	echo "FAIL places control: want exactly one finding, ZZ"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

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

# The change and lock fixtures get their expected results under the rules
# schemas/change.md and schemas/build-lock.md declare, and a lock carrying
# roots is among the invalid ones. A copy expecting that lock to be valid, and
# a copy of change.md without the rule a fixture names, must each report
# exactly that fixture.
expect 0 "change-vectors: every fixture gets its expected result" python3 checks/change-vectors.py
python3 -c 'import json,sys; e={f["file"]:f for f in json.load(open("vectors/change/expected.json"))["fixtures"]}["invalid-lock-roots.yaml"]; sys.exit(0 if (e["valid"],e["rule"])==(False,"lock-keys") else 1)' \
	&& echo "ok   change-vectors: a lock carrying roots is invalid, by lock-keys" \
	|| { echo "FAIL change-vectors: a lock carrying roots is not an invalid fixture"; fails=$((fails + 1)); }
mkdir -p "$tmp/cv" && cp -R schemas vectors "$tmp/cv/"
python3 - "$tmp/cv/vectors/change/expected.json" <<'PY2'
import json, sys
d = json.load(open(sys.argv[1]))
for f in d["fixtures"]:
    if f["file"] == "invalid-lock-roots.yaml":
        f["valid"] = True
        del f["rule"]
json.dump(d, open(sys.argv[1], "w"), indent=2)
PY2
expect 1 "change-vectors control: a lock with roots expected valid fails" python3 checks/change-vectors.py --root "$tmp/cv"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^invalid-lock-roots.yaml: breaks \['lock-keys'\]; expected nothing$" "$tmp/out"; then
	echo "ok   change-vectors control: exactly one finding, the lock with roots"
else
	echo "FAIL change-vectors control: want exactly one finding, the lock with roots"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
mkdir -p "$tmp/cr" && cp -R schemas vectors "$tmp/cr/"
grep -v -e '^  - id: approval-self$' -e '^    rule: approval.by equals requested_by' schemas/change.md >"$tmp/cr/schemas/change.md"
expect 1 "change-vectors control: a fixture naming an undeclared rule fails" python3 checks/change-vectors.py --root "$tmp/cr"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^invalid-self-approval.json: names rule approval-self, which" "$tmp/out"; then
	echo "ok   change-vectors control: exactly one finding, the self-approval fixture"
else
	echo "FAIL change-vectors control: want exactly one finding, the self-approval fixture"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
# The verdicts are read from change.md's Verdicts table, not copied into the
# check: a copy of change.md without the regenerate row must report exactly
# the two fixtures that use it.
mkdir -p "$tmp/cvd" && cp -R schemas vectors "$tmp/cvd/"
grep -v '^| `regenerate` |' schemas/change.md >"$tmp/cvd/schemas/change.md"
expect 1 "change-vectors control: a Verdicts table without regenerate fails" python3 checks/change-vectors.py --root "$tmp/cvd"
if [ "$(wc -l <"$tmp/out")" -eq 2 ] && grep -q "^valid-upgrade-mixed-verdicts.json: breaks \['plan-verdict'\]; expected nothing$" "$tmp/out" &&
	grep -q "^valid-upgrade-applied-without-approval.json: breaks \['plan-verdict'\]; expected nothing$" "$tmp/out"; then
	echo "ok   change-vectors control: exactly two findings, the fixtures that regenerate"
else
	echo "FAIL change-vectors control: want exactly two findings, the fixtures that regenerate"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# The run statement's actions and criteria against vectors/run-statement/,
# under the rules schemas/run-statement.md declares and the steps
# architecture/engine.md declares, and the worked criterion digests. A rule
# added with no fixture, a fixture that breaks test-counts listed as valid,
# and digests computed without sorting the cites are each reported, alone.
expect 0 "run-statement-vectors: every fixture breaks exactly its rule, and every criterion digest agrees" python3 checks/run-statement-vectors.py
mkdir -p "$tmp/rsv/architecture" "$tmp/rsv/vectors" && cp -R schemas "$tmp/rsv/" && cp architecture/engine.md "$tmp/rsv/architecture/" && cp -R vectors/ids.json vectors/run-statement "$tmp/rsv/vectors/"
sed 's/^  - id: verdict-result$/  - id: action-unvectored\n    rule: a rule no fixture breaks\n  - id: verdict-result/' schemas/run-statement.md >"$tmp/rsv/schemas/run-statement.md"
expect 1 "run-statement-vectors control: a rule with no fixture fails" python3 checks/run-statement-vectors.py --root "$tmp/rsv"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^rule action-unvectored: no fixture breaks it$' "$tmp/out"; then
	echo "ok   run-statement-vectors control: exactly one finding, the unvectored rule"
else
	echo "FAIL run-statement-vectors control: want exactly one finding, the unvectored rule"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
cp schemas/run-statement.md "$tmp/rsv/schemas/run-statement.md"
python3 -c 'import json,sys; p=sys.argv[1]; d=json.load(open(p)); [f.update({"valid": True, "breaks": None}) or f.pop("breaks") for f in d["fixtures"] if f["file"]=="invalid-test-counts.json"]; json.dump(d,open(p,"w"))' "$tmp/rsv/vectors/run-statement/expected.json"
expect 1 "run-statement-vectors control: a fixture breaking test-counts listed as valid fails" python3 checks/run-statement-vectors.py --root "$tmp/rsv"
if grep -q "^invalid-test-counts.json: breaks \['test-counts'\]; expected nothing$" "$tmp/out" && grep -q '^rule test-counts: no fixture breaks it$' "$tmp/out" && [ "$(wc -l <"$tmp/out")" -eq 2 ]; then
	echo "ok   run-statement-vectors control: exactly the mislabelled fixture, and its rule left unexercised"
else
	echo "FAIL run-statement-vectors control: want exactly the mislabelled fixture and its rule"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 1 "run-statement-vectors control: criterion digests without sorted cites fail" python3 checks/run-statement-vectors.py --unsorted
if [ "$(grep -c '^criterion-digest ' "$tmp/out")" -eq 2 ] && grep -q '^criterion-digest cites: ' "$tmp/out" && grep -q '^criterion-digest cited-definition-moved: ' "$tmp/out" && [ "$(wc -l <"$tmp/out")" -eq 2 ]; then
	echo "ok   run-statement-vectors control: exactly the two cases that cite"
else
	echo "FAIL run-statement-vectors control: want exactly the two cases that cite"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every change to a versioned file's bytes moves its version (schemas/common.md,
# Versioning), against the base version-bump.py names. With no base to read
# (a shallow or new clone) it says NOT RUN, never ok, and
# REQUIRE_ALL_VERIFIERS=1 makes that a failure. The control is a repository of
# three real headers: one changed without a bump, one changed with a bump and
# one unchanged, and exactly the first must be reported.
python3 checks/version-bump.py >"$tmp/out" 2>&1
got=$?
if [ "$got" -eq 3 ]; then
	echo "NOT RUN $(head -1 "$tmp/out")"
	notrun=$((notrun + 1))
	[ "${REQUIRE_ALL_VERIFIERS:-0}" = 1 ] && fails=$((fails + 1))
elif [ "$got" -eq 0 ]; then
	echo "ok   version-bump: every versioned file changed since the base moved its version"
else
	echo "FAIL version-bump (exit $got, want 0)"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
vb="$tmp/vb"
mkdir -p "$vb/patterns" "$vb/schemas" "$vb/programmes"
cp patterns/content-git.md "$vb/patterns/"
cp schemas/pattern.md "$vb/schemas/"
cp programmes/fleet-safety-ca/specs/fleet.compliance-review.md "$vb/programmes/"
vbgit() { git -C "$vb" -c user.name=check -c user.email=check@example.invalid -c commit.gpgsign=false "$@"; }
vbgit init -q && vbgit add -A && vbgit commit -qm base
echo "An edit nobody bumped for." >>"$vb/patterns/content-git.md"
echo "An edit with its bump." >>"$vb/schemas/pattern.md"
sed -i.bak '1,5s/^version: .*/version: 99.0.0/' "$vb/schemas/pattern.md" && rm "$vb/schemas/pattern.md.bak"
expect 1 "version-bump control: a file changed without a bump fails" python3 checks/version-bump.py --root "$vb" --base HEAD
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^patterns/content-git.md: changed since HEAD without its version moving" "$tmp/out"; then
	echo "ok   version-bump control: exactly one finding, the file nobody bumped"
else
	echo "FAIL version-bump control: want exactly one finding, the file nobody bumped"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
expect 3 "version-bump control: a base that cannot be read is NOT RUN, never ok" python3 checks/version-bump.py --root "$vb" --base no-such-base

# The engine's operation catalogue and today's CLI (checks/front-end-parity.py,
# which replaces command-surface.py). The catalogue in architecture/engine.md
# is well formed, and cli.md's Command Surface against the commands CLI
# 7a75d54 builds (checks/cli-verbs.json) drifts by exactly the measured list.
# A copy of cli.md without one row must report exactly one more drift, a row
# with an executor schemas/change.md does not declare must be reported, and a
# catalogue row repeating an operation or naming an undeclared event type must
# be reported.
expect 0 "front-end-parity: the catalogue is well formed and the CLI's drift is the measured list" python3 checks/front-end-parity.py
mkdir -p "$tmp/cs" && cp -R schemas architecture patterns protocol documents RETIRED.md ACCEPTANCE_PLAN.md "$tmp/cs/"
grep -v '^  - {noun: secret, verb: list, executor: local}$' architecture/cli.md >"$tmp/cs/architecture/cli.md"
expect 1 "front-end-parity control: a Command Surface row deleted fails" python3 checks/front-end-parity.py --root "$tmp/cs"
if [ "$(grep -c '^unexpected drift\|^expected drift' "$tmp/out")" -eq 1 ] && grep -q '^unexpected drift: built, not specified: secret list$' "$tmp/out"; then
	echo "ok   front-end-parity control: exactly one more, the deleted row"
else
	echo "FAIL front-end-parity control: want exactly one more drift, secret list"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
sed 's/^  - {noun: doctor, verb: "", executor: local}$/  - {noun: doctor, verb: "", executor: studio}/' architecture/cli.md >"$tmp/cs/architecture/cli.md"
expect 1 "front-end-parity control: an undeclared executor fails" python3 checks/front-end-parity.py --root "$tmp/cs"
grep -q "^doctor: executor 'studio' is not one schemas/change.md declares$" "$tmp/out" || { echo "FAIL front-end-parity control: the undeclared executor was not what was reported"; fails=$((fails + 1)); }
cp architecture/cli.md "$tmp/cs/architecture/cli.md"
sed 's/^  - ops: \[run status\]$/  - ops: [run status, audit]/; s/^    events: \[check, verdict\]$/    events: [check, verdict, ruling]/' architecture/engine.md >"$tmp/cs/architecture/engine.md"
expect 1 "front-end-parity control: a repeated operation and an undeclared event type fail" python3 checks/front-end-parity.py --root "$tmp/cs"
if [ "$(grep -c 'more than once in the catalogue\|is not one architecture/engine.md declares' "$tmp/out")" -eq 2 ] && grep -q '^audit: listed more than once in the catalogue$' "$tmp/out" && grep -q "^change verify: event type 'ruling' is not one architecture/engine.md declares$" "$tmp/out"; then
	echo "ok   front-end-parity control: exactly the repeated audit and the event type ruling"
else
	echo "FAIL front-end-parity control: want the repeated audit and the event type ruling, and nothing else"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
# Parity between the front ends' manifests. No front end publishes one yet,
# so the leg says NOT RUN, never ok, and REQUIRE_ALL_VERIFIERS=1 makes that a
# failure. Its control: two manifests of the catalogue agree, and one missing
# an operation and holding one of its own is reported, both ways.
python3 checks/front-end-parity.py --parity >"$tmp/out" 2>&1
got=$?
if [ "$got" -eq 3 ]; then
	echo "NOT RUN $(head -1 "$tmp/out")"
	notrun=$((notrun + 1))
	[ "${REQUIRE_ALL_VERIFIERS:-0}" = 1 ] && fails=$((fails + 1))
elif [ "$got" -eq 0 ]; then
	echo "ok   front-end-parity: the front ends' manifests agree"
else
	echo "FAIL front-end-parity --parity (exit $got, want 0)"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
python3 - "$tmp/cli.json" "$tmp/studio.json" <<'MANIFESTS'
import json, re, sys, yaml
text = open("architecture/engine.md", encoding="utf-8").read()
block = [b for b in re.findall(r"^```yaml\n(.*?)^```", text, re.M | re.S) if b.startswith("operations:")][0]
ops = [o for r in yaml.safe_load(block)["operations"] for o in r["ops"] if "<" not in o] + ["policy validate"]
json.dump({"operations": [{"operation": o} for o in ops]}, open(sys.argv[1], "w"))
ops = [o for o in ops if o != "audit"] + ["posture threshold set"]
json.dump({"operations": [{"operation": o} for o in ops]}, open(sys.argv[2], "w"))
MANIFESTS
cp "$tmp/cli.json" "$tmp/cli2.json"
expect 0 "front-end-parity control: two manifests of the catalogue agree" python3 checks/front-end-parity.py --parity --manifests "$tmp/cli.json" "$tmp/cli2.json"
expect 1 "front-end-parity control: a front end missing one operation and holding its own fails" python3 checks/front-end-parity.py --parity --manifests "$tmp/cli.json" "$tmp/studio.json"
if [ "$(wc -l <"$tmp/out")" -eq 4 ] && grep -q '^studio.json: posture threshold set is not an operation of the catalogue$' "$tmp/out" && grep -q "^studio.json: the catalogue's audit is missing$" "$tmp/out" \
	&& grep -q '^cli.json has audit, which studio.json lacks$' "$tmp/out" && grep -q '^studio.json has posture threshold set, which cli.json lacks$' "$tmp/out"; then
	echo "ok   front-end-parity control: exactly the missing audit and the extra posture threshold set"
else
	echo "FAIL front-end-parity control: want exactly the missing audit and the extra posture threshold set"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# The engine holds no corpus knowledge (checks/engine-neutrality.py): the
# literals in the tools' source at the pinned commit that equal a name the
# corpus declares are exactly the known list. Without the tools' repository
# it says NOT RUN, never ok. Its controls run on plain directories: a source
# naming nothing passes; one with a declared route and a sentence of an
# instruction added reports exactly those two; a known entry that finds
# nothing is reported.
python3 checks/engine-neutrality.py >"$tmp/out" 2>&1
got=$?
if [ "$got" -eq 3 ]; then
	echo "NOT RUN $(head -1 "$tmp/out")"
	notrun=$((notrun + 1))
	[ "${REQUIRE_ALL_VERIFIERS:-0}" = 1 ] && fails=$((fails + 1))
elif [ "$got" -eq 0 ]; then
	echo "ok   engine-neutrality: the tools' corpus names are exactly the known list"
else
	echo "FAIL engine-neutrality (exit $got, want 0)"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
mkdir -p "$tmp/en/internal"
printf 'package internal\n\n// A literal that names nothing the corpus declares.\nvar greeting = "hello"\n' >"$tmp/en/internal/clean.go"
expect 0 "engine-neutrality control: a source naming nothing passes" python3 checks/engine-neutrality.py --dir "$tmp/en" --known "$tmp/none.json"
sentence=$(python3 -c 'import re; t=open("instructions/scope.md").read(); print(" ".join(re.search(r"```text\n(.*?)```", t, re.S).group(1).split()).split(". ")[0] + ".")')
printf 'package internal\n\nconst route = "/v1/register"\nconst prompt = "%s"\n' "$sentence" >"$tmp/en/internal/leak.go"
expect 1 "engine-neutrality control: a declared route and an instruction sentence added fail" python3 checks/engine-neutrality.py --dir "$tmp/en" --known "$tmp/none.json"
if [ "$(grep -c '^new: ' "$tmp/out")" -eq 2 ] && grep -q '^new: internal/leak.go: route /v1/register$' "$tmp/out" && grep -q '^new: internal/leak.go: instruction ' "$tmp/out"; then
	echo "ok   engine-neutrality control: exactly the route and the instruction sentence"
else
	echo "FAIL engine-neutrality control: want exactly the route and the instruction sentence"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
rm "$tmp/en/internal/leak.go"
printf '{"known": [{"finding": "internal/clean.go: route /v1/register", "audit": "control"}]}\n' >"$tmp/en-known.json"
expect 1 "engine-neutrality control: a known entry that finds nothing fails" python3 checks/engine-neutrality.py --dir "$tmp/en" --known "$tmp/en-known.json"
grep -q '^known finding gone: internal/clean.go: route /v1/register' "$tmp/out" || { echo "FAIL engine-neutrality control: the stale entry was not what was reported"; fails=$((fails + 1)); }
expect 3 "engine-neutrality control: no tools repository is NOT RUN, never ok" python3 checks/engine-neutrality.py --tools "$tmp/no-such-tools"

# Every checklist line against the rule it cites, or, citing nothing, against
# the registries and its own file; the findings are the measured list. Three
# fixtures: a cited section that lacks the line's code, and a line naming a
# code nothing registers, must each be reported exactly once; a clean one, and
# the corpus with a known entry that finds nothing, are told apart.
expect 0 "checklist-cites: the findings are the measured list" python3 checks/checklist-cites.py
mkdir -p "$tmp/cc-cited/architecture" "$tmp/cc-orphan/architecture" "$tmp/cc-clean/architecture"
cat >"$tmp/cc-clean/architecture/x.md" <<'MD'
# X

## Refusing

A bad request is refused with 409 `X_CONFLICT`.

## Error Handling

| Code | HTTP | Description |
|---|---|---|
| `X_CONFLICT` | 409 | The request conflicts |
| `X_GONE` | 410 | The thing was removed |

A removed thing is answered `X_GONE`.

### `x create <name>`

Creating a name already held is refused with 409 `X_CONFLICT`.

## Verification Checklist

- [ ] A bad request is refused with 409 `X_CONFLICT` ([Refusing](#refusing))
- [ ] A removed thing is answered `X_GONE`
- [ ] A held name is refused ([`x create <name>`](#x-create-name))
MD
sed 's/^- \[ \] A bad request is refused with 409 `X_CONFLICT` (\[Refusing\](#refusing))$/- [ ] A bad request is refused with 409 `X_GONE` ([Refusing](#refusing))/' "$tmp/cc-clean/architecture/x.md" >"$tmp/cc-cited/architecture/x.md"
sed 's/^- \[ \] A removed thing is answered `X_GONE`$/- [ ] A removed thing is answered `X_VANISHED`/' "$tmp/cc-clean/architecture/x.md" >"$tmp/cc-orphan/architecture/x.md"
expect 0 "checklist-cites control: a clean fixture passes" python3 checks/checklist-cites.py --root "$tmp/cc-clean" --known "$tmp/none.json"
expect 1 "checklist-cites control: a cited section without the line's code fails" python3 checks/checklist-cites.py --root "$tmp/cc-cited" --known "$tmp/none.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^architecture/x.md:22: names X_GONE, which no section it cites (#refusing) names$' "$tmp/out"; then
	echo "ok   checklist-cites control: exactly one finding, X_GONE against #refusing"
else
	echo "FAIL checklist-cites control: want exactly one finding, X_GONE against #refusing"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
# A heading's slug keeps the text inside backticks, as GitHub's does: the
# clean fixture cites #x-create-name, and the slug that drops <name> as a tag
# names no heading.
mkdir -p "$tmp/cc-slug/architecture"
sed 's/(#x-create-name)/(#x-create-)/' "$tmp/cc-clean/architecture/x.md" >"$tmp/cc-slug/architecture/x.md"
expect 1 "checklist-cites control: a slug that drops backticked <name> fails" python3 checks/checklist-cites.py --root "$tmp/cc-slug" --known "$tmp/none.json"
grep -q '^architecture/x.md:[0-9]*: links #x-create-, whose anchor no heading of architecture/x.md gives$' "$tmp/out" || { echo "FAIL checklist-cites control: the dropped-<name> slug was not what was reported"; fails=$((fails + 1)); }
expect 1 "checklist-cites control: an uncited unregistered code fails" python3 checks/checklist-cites.py --root "$tmp/cc-orphan" --known "$tmp/none.json"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^architecture/x.md:23: names X_VANISHED, which no registry declares and which cites nothing$' "$tmp/out"; then
	echo "ok   checklist-cites control: exactly one finding, the orphan X_VANISHED"
else
	echo "FAIL checklist-cites control: want exactly one finding, the orphan X_VANISHED"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
python3 - "$tmp/cc-known.json" <<'PY'
import json, sys
d = json.load(open("checks/checklist-cites.json", encoding="utf-8"))
d["known"].append({"finding": "architecture/orchestrator.md: names NOT_A_CODE, which no registry declares and which cites nothing", "why": "control"})
json.dump(d, open(sys.argv[1], "w"))
PY
expect 1 "checklist-cites control: a known entry that finds nothing fails" python3 checks/checklist-cites.py --known "$tmp/cc-known.json"
grep -q "^known finding gone (0 of 1 remain)" "$tmp/out" || { echo "FAIL checklist-cites control: the stale entry was not what was reported"; fails=$((fails + 1)); }

# Every Resources block against schemas/resource.md, whose rules, shape and
# vocabularies the check reads and keeps no copy of: the corpus's blocks and
# the valid vector give no finding, and the invalid vector gives exactly one
# finding per rule. A copy of the expected findings missing one entry must be
# reported; a copy of resource.md without the instant presentation must turn
# every instant field in the corpus into a finding, and only those; and a
# rule added to resource.md with no vector must be reported unexercised.
expect 0 "resources: every Resources block in the corpus is well formed" python3 checks/resources.py
expect 0 "resources: the valid vector gives no finding" python3 checks/resources.py --file vectors/resources/valid.md
expect 0 "resources: the invalid vector gives exactly its findings, every rule exercised" python3 checks/resources.py --file vectors/resources/invalid.md --expect vectors/resources/invalid.expected.json
python3 -c 'import json,sys; d=json.load(open("vectors/resources/invalid.expected.json")); d["findings"]=[f for f in d["findings"] if f["rule"]!="resource-events"]; json.dump(d,open(sys.argv[1],"w"))' "$tmp/res-expect.json"
expect 1 "resources control: expected findings missing one entry fail" python3 checks/resources.py --file vectors/resources/invalid.md --expect "$tmp/res-expect.json"
grep -q '^unexpected: register: resource-events$' "$tmp/out" && grep -q '^unexercised: rule resource-events has no expected finding$' "$tmp/out" \
	&& echo "ok   resources control: the dropped entry is what was reported" \
	|| { echo "FAIL resources control: the dropped entry was not what was reported"; sed 's/^/     /' "$tmp/out"; fails=$((fails + 1)); }
mkdir -p "$tmp/res" && cp -R agents architecture patterns protocol schemas "$tmp/res/"
grep -v '^  instant: ' schemas/resource.md >"$tmp/res/schemas/resource.md"
expect 1 "resources control: a resource.md without the instant presentation fails" python3 checks/resources.py --root "$tmp/res"
if grep -q 'is presented instant, which is no presentation$' "$tmp/out" && ! grep -v 'is presented instant, which is no presentation$' "$tmp/out" | grep -q .; then
	echo "ok   resources control: only the instant fields were reported"
else
	echo "FAIL resources control: want only the instant fields reported"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
mkdir -p "$tmp/res2" && cp -R agents architecture patterns protocol schemas "$tmp/res2/"
sed 's/^  - id: resource-unavailable$/  - id: resource-unvectored\n    rule: a rule no vector exercises\n  - id: resource-unavailable/' schemas/resource.md >"$tmp/res2/schemas/resource.md"
expect 1 "resources control: a rule with no vector fails" python3 checks/resources.py --root "$tmp/res2" --file vectors/resources/invalid.md --expect vectors/resources/invalid.expected.json
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^unexercised: rule resource-unvectored has no expected finding$' "$tmp/out"; then
	echo "ok   resources control: exactly one finding, the unvectored rule"
else
	echo "FAIL resources control: want exactly one finding, the unvectored rule"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# Every register column in a programme file reads back as written; a copy with
# one comma-holding label unquoted again must report exactly that label.
expect 0 "register-labels: every programme column reads back as written" python3 checks/register-labels.py
mkdir -p "$tmp/rl" && cp -R programmes schemas "$tmp/rl/"
sed 's/label: "Underlying cause, detail"/label: Underlying cause, detail/' programmes/construction-ohs-ca/specs/cohs.incident-reporting.md >"$tmp/rl/programmes/construction-ohs-ca/specs/cohs.incident-reporting.md"
expect 1 "register-labels control: an unquoted comma in a label fails" python3 checks/register-labels.py --root "$tmp/rl"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "cohs.incident-reporting.md: column 'root_cause': label 'Underlying cause' does not round-trip: 'detail' is read as a key" "$tmp/out"; then
	echo "ok   register-labels control: exactly one finding, the cut label"
else
	echo "FAIL register-labels control: want exactly one finding, the cut label"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

# No register specification carries satisfies (schemas/kinds.md, Relations:
# only the kinds the implements row names may assert it). A copy with one
# claim put back on a register must report exactly that register, and a
# kinds.md whose implements row admits register must stop the check.
expect 0 "register-satisfies: no register carries satisfies" python3 checks/register-satisfies.py
mkdir -p "$tmp/rs" && cp -R programmes schemas "$tmp/rs/"
sed 's/^requires: \[cohs.notifiable-events, cohs.incidents\]$/satisfies: [cor_2020:COR-18]\nrequires: [cohs.notifiable-events, cohs.incidents]/' programmes/construction-ohs-ca/specs/cohs.safety-statistics.md >"$tmp/rs/programmes/construction-ohs-ca/specs/cohs.safety-statistics.md"
expect 1 "register-satisfies control: a register carrying satisfies fails" python3 checks/register-satisfies.py --root "$tmp/rs"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q "^programmes/construction-ohs-ca/specs/cohs.safety-statistics.md: a register carries satisfies \['cor_2020:COR-18'\]" "$tmp/out"; then
	echo "ok   register-satisfies control: exactly one finding, the register given a claim"
else
	echo "FAIL register-satisfies control: want exactly one finding, the register given a claim"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi
mkdir -p "$tmp/rk" && cp -R programmes schemas "$tmp/rk/"
sed 's/^| `implements` | blueprint, policy, procedure |/| `implements` | blueprint, policy, procedure, register |/' schemas/kinds.md >"$tmp/rk/schemas/kinds.md"
expect 1 "register-satisfies control: an implements row admitting register stops the check" python3 checks/register-satisfies.py --root "$tmp/rk"

# The closed needs: set is stated once, in schemas/programme.md, and the
# prompt worker maps exactly its words. A copy of the prompt worker that maps
# a word the set does not hold must report exactly that word.
expect 0 "needs-set: the prompt worker maps exactly the closed set" python3 checks/needs-set.py
sed 's/^  notify:$/  notify:\n  escalate:\n    capabilities: [content:read]\n    tools: []/' architecture/prompt-worker.md >"$tmp/pw.md"
expect 1 "needs-set control: a word mapped outside the set fails" python3 checks/needs-set.py --worker "$tmp/pw.md"
if [ "$(wc -l <"$tmp/out")" -eq 1 ] && grep -q '^escalate: mapped by the prompt worker, and not in needs_set$' "$tmp/out"; then
	echo "ok   needs-set control: exactly one finding, the unlisted word"
else
	echo "FAIL needs-set control: want exactly one finding, escalate"
	sed 's/^/     /' "$tmp/out"
	fails=$((fails + 1))
fi

[ "$notrun" -gt 0 ] && echo "checks: $notrun verifier leg(s) NOT RUN (see above)"
[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
