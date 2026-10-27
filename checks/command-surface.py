"""architecture/cli.md's Command Surface against the commands the CLI builds.

Reads the `command_surface:` block of architecture/cli.md and the CLI's
commands at the commit checks/cli-verbs.json names, and prints each command
specified and not built, and each built and not specified. Passes only when
that drift is exactly the file's expected_drift: a row removed, a command
built or a spelling changed on either side is a change to the drift, and is
reported. Every row's executor must be one schemas/change.md declares.

  command-surface.py [--root DIR]
"""
import json, os, re, sys
import yaml

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(__file__), "..")
text = open(os.path.join(root, "architecture", "cli.md"), encoding="utf-8").read()
blocks = [b for b in re.findall(r"^```yaml\n(.*?)^```", text, re.M | re.S) if b.startswith("command_surface:")]
faults = []
if len(blocks) != 1:
    print(f"architecture/cli.md has {len(blocks)} command_surface blocks; want exactly one")
    sys.exit(1)
rows = yaml.safe_load(blocks[0])["command_surface"]
change = open(os.path.join(root, "schemas", "change.md"), encoding="utf-8").read()
executors = set(re.findall(r"^\| `([a-z-]+)` \|", change.split("## Executors", 1)[1].split("\n## ", 1)[0], re.M))
spec = []
for r in rows:
    spec.append(f"{r['noun']} {r['verb']}".strip())
    if r.get("executor") not in executors:
        faults.append(f"{spec[-1]}: executor {r.get('executor')!r} is not one schemas/change.md declares")
cli = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cli-verbs.json"), encoding="utf-8"))
built = [f"{c['noun']} {c['verb']}".strip() for c in cli["commands"]]
for name, items in (("Command Surface", spec), (f"CLI {cli['cli_commit']}", built)):
    for d in sorted({i for i in items if items.count(i) > 1}):
        faults.append(f"{d}: listed more than once in the {name}")
drift = [f"specified, not built: {c}" for c in sorted(set(spec) - set(built))] + \
        [f"built, not specified: {c}" for c in sorted(set(built) - set(spec))]
print("\n".join(drift))
want = cli["expected_drift"]
if drift != want:
    for line in sorted(set(drift) - set(want)):
        faults.append(f"unexpected drift: {line}")
    for line in sorted(set(want) - set(drift)):
        faults.append(f"expected drift gone: {line}")
print("\n".join(faults) or f"command-surface: {len(spec)} rows; the drift against CLI {cli['cli_commit']} is the {len(want)} expected")
sys.exit(1 if faults else 0)
