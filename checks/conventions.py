#!/usr/bin/env python3
"""protocol/conventions, checked from outside every Weblisk tool.

Usage: conventions.py vectors [--control]
  vectors    each value in vectors/conventions.json is what the rule it names
             gives, computed here from the rule's text alone.
--control runs the mode with a seeded fault and passes only if exactly the
seeded fault is reported.
"""
import datetime, json, os, re, sys

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
mode = sys.argv[1] if len(sys.argv) > 1 else ""
control = "--control" in sys.argv[2:]

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


if mode == "vectors": found, seeded = vectors()
else: sys.exit(__doc__)
if found: print("\n".join(found))
print(f"{mode}: {len(found)} reported")
if control: sys.exit(0 if found and {f.split(':', 1)[0] for f in found} == seeded else 1)
sys.exit(1 if found else 0)
