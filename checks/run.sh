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
open(sys.argv[1] + "/ended.md", "w").write(text.replace("until: architecture/admin@4.0.0", "until: architecture/admin@1.0.0", 1))
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

[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
