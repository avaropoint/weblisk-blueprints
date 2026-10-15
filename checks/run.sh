#!/bin/sh
# Runs the corpus's checks, each with the control that proves it reaches what
# it claims to. Exits 0 only when every check passes and every control fails.
# Needs python3 with PyYAML.
cd "$(dirname "$0")/.." || exit 2
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

[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
