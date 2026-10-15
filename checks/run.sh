#!/bin/sh
# Runs the corpus's checks, each with the control that proves it reaches what
# it claims to. Exits 0 only when every check passes and every control fails.
# Needs python3 with PyYAML.
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

[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
