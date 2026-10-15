#!/bin/sh
# Runs the corpus's checks, each with the control that proves it reaches what
# it claims to. Exits 0 only when every check passes and every control fails.
# Needs python3 with PyYAML, and OpenSSL 3.5 or later (as $OPENSSL or on PATH).
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

[ "$fails" -eq 0 ] && echo "checks: all pass" || echo "checks: $fails failed"
[ "$fails" -eq 0 ]
