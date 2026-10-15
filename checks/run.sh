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

[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
