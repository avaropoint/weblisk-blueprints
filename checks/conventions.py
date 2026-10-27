#!/usr/bin/env python3
"""protocol/conventions, checked from outside every Weblisk tool.

Usage: conventions.py vectors|time-fields|sites [--control] [--root DIR]
  vectors    each value in vectors/conventions.json is what the rule it names
             gives, computed here from the rule's text alone.
  time-fields  every field a specification declares that holds an instant is
             typed timestamp. An instant is a field named as one (*_at,
             timestamp, since, until, last_seen ...) or described by an epoch,
             Unix time, RFC 3339 or ISO 8601; a field whose description cites
             an RFC 7519 NumericDate keeps the form that RFC fixes. Fields are
             read in every shape the corpus writes one: name: {type: X}, a
             type: key under the name, name: X  # description, an inline
             {name: X} signature, a Go-style (name X) parameter list and a
             table row | name | X | description |.
  sites      no specification file restates a rule protocol/conventions holds:
             a UUID version other than 7, a backoff formula, schedule or
             second algorithm, a retry limit counted in retries, a task
             timeout other than the rule's, a :name path parameter, an instant
             described in epoch or Unix units in any spelling (unix-epoch,
             <unix-timestamp> ...), or an example that writes an instant as
             an epoch integer (a NumericDate or OpenMetrics timestamp, whose
             form an external authority fixes, excepted), or a length of time
             held as a bare number of a unit outside the files RETIRED.md
             still allows to hold one.
--control runs the mode with a seeded fault and passes only if exactly the
seeded fault is reported. --root reads another corpus checkout.
"""
import datetime, glob, json, os, re, sys

argv = sys.argv[1:]
root = argv[argv.index("--root") + 1] if "--root" in argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
mode = argv[0] if argv else ""
control = "--control" in argv

INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z")
UUID7 = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
DURATION = re.compile(r"(?:(\d+)h)?(?:(\d+)m(?!s))?(?:(\d+)s)?(?:(\d+)ms)?")
INTEGER = re.compile(r"-?(?:0|[1-9]\d*)")


def write_instant(ms):
    d = datetime.datetime.fromtimestamp(ms // 1000, datetime.timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%S") + (".%03dZ" % (ms % 1000) if not control else "Z")


def read_instant(s):
    if not INSTANT.fullmatch(s): return None
    try: d = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError: return None
    return int(d.timestamp()) * 1000 + d.microsecond // 1000


def read_uuid(s):
    return int(s.replace("-", "")[:12], 16) if UUID7.fullmatch(s) else None


def read_duration(s):
    m = DURATION.fullmatch(s)
    if not s or not m or not any(m.groups()): return None
    h, mi, se, ms = (int(g or 0) for g in m.groups())
    return ((h * 60 + mi) * 60 + se) * 1000 + ms


def read_integer(s):
    return int(s) if INTEGER.fullmatch(s) and -2**63 <= int(s) < 2**63 else None


def cap(base_ms, max_ms, n):
    return min(base_ms * 2 ** (n if control else n - 1), max_ms)


def vectors():
    v = json.load(open(os.path.join(root, "vectors/conventions.json")))
    found = []
    def bad(section, what): found.append(f"{section}: {what}")
    i = v["instant"]
    for c in i["cases"] + [i["binding"]]:
        if write_instant(c["unix_ms"]) != c["wire"]: bad("instant", f"{c['unix_ms']} is written {write_instant(c['unix_ms'])}, the vector says {c['wire']}")
        if read_instant(c["wire"]) != c["unix_ms"]: bad("instant", f"{c['wire']} does not read back as {c['unix_ms']}")
    for s in i["invalid"]:
        if read_instant(s) is not None: bad("instant", f"{s!r} is read, the vector says refuse it")
    for c in v["uuid"]["cases"]:
        if read_uuid(c["value"]) != c["unix_ms"]: bad("uuid", f"{c['value']} does not read as version 7 at {c['unix_ms']}")
    for s in v["uuid"]["invalid"]:
        if read_uuid(s) is not None: bad("uuid", f"{s!r} is read, the vector says refuse it")
    for c in v["duration"]["cases"]:
        if read_duration(c["value"]) != c["ms"]: bad("duration", f"{c['value']!r} reads as {read_duration(c['value'])}, the vector says {c['ms']}")
    for s in v["duration"]["invalid"]:
        if read_duration(s) is not None: bad("duration", f"{s!r} is read, the vector says refuse it")
    for s in v["integer"]["cases"]:
        if read_integer(s) is None: bad("integer", f"{s} is refused")
    for s in v["integer"]["invalid"]:
        if read_integer(s) is not None: bad("integer", f"{s} is read, the vector says refuse it")
    a = v["max_attempts"]
    if a["default"] != 3: bad("max_attempts", f"default {a['default']}, the rule says 3")
    for c in a["cases"]:
        if c["attempts"] != c["max_attempts"] or c["retries"] != c["max_attempts"] - 1: bad("max_attempts", f"{c} does not count the first attempt")
    b = v["backoff"]
    base, mx = read_duration(b["base"]), read_duration(b["max"])
    if (base, mx) != (1000, 30000): bad("backoff", f"base {b['base']} max {b['max']}, the rule says 1s and 30s")
    for c in b["caps"]:
        if cap(base, mx, c["after_attempt"]) != c["cap_ms"]: bad("backoff", f"after attempt {c['after_attempt']} the cap is {cap(base, mx, c['after_attempt'])}, the vector says {c['cap_ms']}")
    return found, {"instant", "backoff"}


SPEC_DIRS = ["protocol", "patterns", "architecture", "agents", "languages", "platforms", "frameworks", "schemas", "skills", "templates"]
HOME = "protocol/conventions.md"
SITES = {
    "uuid": [re.compile(r"(?i)uuid[ -]?v4|uuid4|v4 uuid")],
    "backoff": [re.compile(r"2\s*\^\s*\(?\s*(?:attempt|retry|n)\b|\bbase\w*\s*[×x*]\s*2\b"),
                re.compile(r"(?i)(?=.*(?:backoff|retr|exponential)).*\b\d+[ -]?(?:ms|s|m|h|sec(?:ond)?s?|min(?:ute)?s?)\b\s*,\s*\d+[ -]?(?:ms|s|m|h|sec(?:ond)?s?|min(?:ute)?s?)\b"),
                re.compile(r"(?i)backoff\w*\b.*\b(?:linear|fixed)\b")],
    "retries": [re.compile(r"\bmax_retries\b|\bretry_count\b|\bMaxRetries\b|(?i:\bretr(?:y|ies) (?:up to )?\d+ ?x\b|\b\d+ retries\b|\bretr(?:y|ies) \d+ times\b)")],
    "task-timeout": [re.compile(r"(?i)\|\s*(?:agent → agent \(task\)|task timeout)\s*\|\s*(?!300\s*s)\d+\s*s\s*\|")],
    "path-param": [re.compile(r"/:[a-z_][a-z0-9_]*")],
    "instant": [re.compile(r"^(?!.*(?:NumericDate|OpenMetrics))(?i:.*(?:unix[-_ ]epoch|epoch[-_ ]seconds|unix[-_ ]seconds|unix[-_ ]timestamp|unix[-_ ]ms\b|epoch[-_ ]milli|decimal unix|unix[-_ ]time\b|<epoch\b|seconds since (?:the )?epoch))")],
    "duration": [re.compile(r"(?<![\w.])(?!(?:allowed|quiet)_hours\b)[a-z][a-z0-9_]*_(?:ms|seconds|secs|minutes|hours|days)\??\s*:|\bunit:\s*(?:seconds|milliseconds|minutes|hours|days)\b")],
    "epoch-literal": [re.compile(r"^(?!.*NumericDate)(?!.*[\"'\s{,](?:iat|exp|nbf|ren)[\"']?\s*:).*[\"']?\b[A-Za-z_]\w*[\"']?\s*(?::|=|<=?|>=?)\s*1[5-9]\d{8}(?:\d{3})?\b(?![.\d])")],
}
SEEDED = {"uuid": "id = UUID v4", "backoff": "delay = base × 2^attempt", "retries": "  max_retries: 3",
          "task-timeout": "| Task timeout | 30s | per task |", "path-param": "GET /v1/things/:id",
          "instant": "| created_at | int64 | Unix epoch seconds |", "duration": "  lease_ttl_seconds: 30", "epoch-literal": '  "last_check": 1712160000,'}


INSTANT_NAME = re.compile(r"(?:^|_)(?:at|timestamp)$|^(?:ts|time|since|until|deadline|expiry|expires|not_after|not_before|iat|exp|created|updated|start|end|last_updated)$|^(?:last|next|first)_(?:seen|check|active|verified|refreshed|retry|fire|attempt|updated|rotated|renewal)$")
INSTANT_DESC = re.compile(r"(?i)\bepoch\b|\bunix\b|RFC ?3339|ISO ?8601|\btimestamp\b")
NOT_INSTANT = re.compile(r"(?i)\bseq\b|\bcount\b|ISO 8601 date\b|\bcursor\b|version vector|\bnumber of\b|NumericDate|\bthe column\b|and when it leaves\b")
TYPE_ROWS = {"timestamp", "iso8601"}  # a type-mapping table's row names a type, not a field
SCALARS = {"int64", "integer", "int", "int32", "number", "datetime", "string", "*int64", "timestamp", "time.Time"}
NOT_INSTANT_NAMES = {"last_error", "next_cursor", "depends_on", "updated", "broken_at", "terminates_at"}


SCALAR = r"(?:\*?int64|integer|int32|int|number|datetime|string|timestamp|time\.Time)"
INLINE = re.compile(r"([A-Za-z_]\w*)\??:\s*(" + SCALAR + r")\b(?!\.)")
GOPARAM = re.compile(r"([A-Za-z_]\w*) (" + SCALAR + r")\b")


def declared_fields(text):
    """(line, name, type, description) for each field a specification declares,
    in every shape one is written: `name: {type: X}`, a `type:` key under the
    name, the shorthand `name: X  # description`, an inline `{name: X, ...}`
    signature, a Go-style `(name X, ...)` parameter list, and a table row
    `| name | X | description |`."""
    lines, inside = text.split("\n"), False
    for i, l in enumerate(lines):
        if re.match(r"^\s*```", l): inside = not inside; continue
        for seg in re.findall(r"\{([^{}]*)\}", l):
            for name, typ in INLINE.findall(seg):
                if name != "type": yield i + 1, name, typ, ""
        for seg in re.findall(r"\(([^()]*)\)", l):
            for name, typ in GOPARAM.findall(seg):
                yield i + 1, name, typ, ""
        t = re.match(r"^\|\s*`?([A-Za-z_]\w*)\??`?\s*\|\s*`?(" + SCALAR + r")`?\s*\|(.*)\|\s*$", l)
        if t and not inside and t.group(1) not in TYPE_ROWS:
            yield i + 1, t.group(1), t.group(2), t.group(3)
            continue
        if not inside: continue
        m = re.match(r"^\s*(?:-\s+)?([A-Za-z_]\w*)\??:\s*(" + SCALAR + r")\s*(?:#\s*(.*))?$", l)
        if m and m.group(1) not in ("type", "format"):
            yield i + 1, m.group(1), m.group(2), m.group(3) or ""
            continue
        m = re.match(r"^\s*([A-Za-z_]\w*):\s*\{type:\s*([^,}\s]+)(.*)\}\s*$", l)
        if m:
            d = re.search(r"description:\s*(.*)$", m.group(3))
            yield i + 1, m.group(1), m.group(2), d.group(1) if d else ""
            continue
        m = re.match(r"^(\s*)type:\s*([^\s#]+)", l)
        if not m: continue
        ind, name, start = len(m.group(1)), None, i
        for j in range(i - 1, max(i - 8, -1), -1):
            k = re.match(r"^(\s*)(?:- name:\s*([A-Za-z_]\w*)|([A-Za-z_]\w*):)\s*$", lines[j])
            if k and len(k.group(1)) < ind or k and k.group(2) and len(k.group(1)) + 2 == ind:
                name, start = k.group(2) or k.group(3), j; break
        if not name: continue
        desc = ""
        for j in list(range(start + 1, i)) + list(range(i + 1, min(i + 8, len(lines)))):
            if j > i and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) < ind): break
            d = re.match(r"^\s*description:\s*(.*)$", lines[j])
            if d: desc = d.group(1)
        yield i + 1, name, m.group(2).strip("'\""), desc


def time_fields():
    found = []
    files = sorted(p for d in SPEC_DIRS for p in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True))
    texts = [(os.path.relpath(p, root), open(p, encoding="utf-8").read()) for p in files]
    seeded_shapes = ["```yaml\nSeeded:\n  fields:\n    created_at:\n      type: int64\n      description: Unix epoch seconds\n```",
                     "```yaml\nSeeded:\n  updated_at: {type: integer}\n```",
                     "```yaml\nHold:\n  expires_at: int64         # When the hold expires\n```",
                     "**Input:** `{since: int64, limit?: int}`",
                     "| Verify | `(until int64) → error` | |",
                     "\n| last_seen | int64 | yes | When the peer was last heard from |\n"]
    if control: texts.append(("seeded.md", "\n".join(seeded_shapes) + "\n"))
    for rel, text in texts:
        for n, name, typ, desc in declared_fields(text):
            if typ == "timestamp" or typ not in SCALARS or name in NOT_INSTANT_NAMES or NOT_INSTANT.search(desc): continue
            if INSTANT_NAME.search(name) or INSTANT_DESC.search(desc):
                found.append(f"time-fields: {rel}:{n}: {name} is {typ}, not timestamp")
    if control:
        seeded = [f for f in found if " seeded.md:" in f]
        return (seeded if len(seeded) == len(seeded_shapes) and found == seeded else found + ["control: the corpus is not clean, or a seeded shape was missed"]), {"time-fields"}
    return found, set()


def site_lines(text):
    """Each line, and the YAML key a list of backoff values sits under."""
    lines = text.split("\n")
    for i, l in enumerate(lines):
        yield i + 1, l
        if re.match(r"^\s*(?:values|enum):\s*\[.*\b(?:linear|fixed)\b", l) and any(re.match(r"^\s*\w*backoff\w*:\s*$", p) for p in lines[max(0, i - 4):i]):
            yield i + 1, "backoff: " + l.strip()
        m = re.match(r"^\s*task_timeout:\s*$", l)
        if m:
            for p in lines[i + 1:i + 7]:
                d = re.match(r"^\s*default:\s*(\d+)\s*$", p)
                if d and d.group(1) != "300": yield i + 1, f"| Task timeout | {d.group(1)}s |"


def duration_allowed():
    """The files RETIRED.md still allows to hold a bare-number duration."""
    import yaml
    text = open(os.path.join(root, "RETIRED.md"), encoding="utf-8").read()
    entries = yaml.safe_load(re.search(r"^## Entries\n.*?```yaml\n(.*?)```", text, re.S | re.M).group(1))
    for e in entries:
        if any(r["spelling"] == "unit: seconds" for r in e["retired"]):
            return {a["path"] for a in e.get("allow", [])}
    return set()


def sites():
    found = []
    allowed = duration_allowed()
    files = sorted(p for d in SPEC_DIRS for p in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True))
    texts = [(os.path.relpath(p, root), open(p, encoding="utf-8").read()) for p in files]
    if control: texts.append(("seeded.md", "\n".join(SEEDED.values())))
    for rel, text in texts:
        if rel == HOME: continue
        for n, l in site_lines(text):
            for rule, pats in SITES.items():
                if rule == "duration" and rel in allowed: continue
                if any(p.search(l) for p in pats): found.append(f"{rule}: {rel}:{n}: {l.strip()[:120]}")
    if control:
        seeded = [f for f in found if " seeded.md:" in f]
        return (seeded if len(seeded) == len(SEEDED) and found == seeded else found + ["control: the corpus is not clean, or a seeded line was missed"]), set(SEEDED)
    return found, set()


if mode == "vectors": found, seeded = vectors()
elif mode == "sites": found, seeded = sites()
elif mode == "time-fields": found, seeded = time_fields()
else: sys.exit(__doc__)
if found: print("\n".join(found))
print(f"{mode}: {len(found)} reported")
if control: sys.exit(0 if found and {f.split(':', 1)[0] for f in found} == seeded else 1)
sys.exit(1 if found else 0)
