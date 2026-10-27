#!/usr/bin/env python3
"""protocol/conventions, checked from outside every Weblisk tool.

Usage: conventions.py vectors|sites [--control] [--root DIR]
  vectors    each value in vectors/conventions.json is what the rule it names
             gives, computed here from the rule's text alone.
  sites      no specification file restates a rule protocol/conventions holds:
             a UUID version other than 7, a backoff formula, schedule or
             second algorithm, a retry limit counted in retries, a task
             timeout other than the rule's, a :name path parameter.
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
}
SEEDED = {"uuid": "id = UUID v4", "backoff": "delay = base × 2^attempt", "retries": "  max_retries: 3",
          "task-timeout": "| Task timeout | 30s | per task |", "path-param": "GET /v1/things/:id"}


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


def sites():
    found = []
    files = sorted(p for d in SPEC_DIRS for p in glob.glob(os.path.join(root, d, "**", "*.md"), recursive=True))
    texts = [(os.path.relpath(p, root), open(p, encoding="utf-8").read()) for p in files]
    if control: texts.append(("seeded.md", "\n".join(SEEDED.values())))
    for rel, text in texts:
        if rel == HOME: continue
        for n, l in site_lines(text):
            for rule, pats in SITES.items():
                if any(p.search(l) for p in pats): found.append(f"{rule}: {rel}:{n}: {l.strip()[:120]}")
    if control:
        seeded = [f for f in found if " seeded.md:" in f]
        return (seeded if len(seeded) == len(SEEDED) and found == seeded else found + ["control: the corpus is not clean, or a seeded line was missed"]), set(SEEDED)
    return found, set()


if mode == "vectors": found, seeded = vectors()
elif mode == "sites": found, seeded = sites()
else: sys.exit(__doc__)
if found: print("\n".join(found))
print(f"{mode}: {len(found)} reported")
if control: sys.exit(0 if found and {f.split(':', 1)[0] for f in found} == seeded else 1)
sys.exit(1 if found else 0)
