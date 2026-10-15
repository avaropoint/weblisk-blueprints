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

[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
