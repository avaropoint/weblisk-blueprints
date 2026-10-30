"""Every change to a versioned file's bytes moves its version
(schemas/common.md, Versioning: "Every change to a blueprint's bytes moves its
version").

    version-bump.py [--root DIR] [--base REV]

A file is versioned when its copy at the base revision declares a
`version: MAJOR.MINOR.PATCH` in its header: the `<!-- blueprint` comment of the
older form, or the `---` YAML header of grammar 1 (blueprints, schemas,
programme maps and specs). Each one that differs between the base and the
working tree must declare a version greater than the base's. A file new since
the base, or unversioned there, has nothing to compare. Standards are not
covered: a standard's `version` is its publisher's edition (schemas/standard.md),
not a version of the file. Nor are `vectors/` and `checks/`, whose markdown is
test data.

The base is --base, else $VERSION_BASE, else the merge-base of HEAD with
origin/main, or HEAD~1 where that merge-base is HEAD itself (on main). Where
no base can be read (not a git repository, a shallow clone without it, no
origin/main and no parent) the check prints `version-bump: not run: <why>` and
exits 3: it never passes for want of something to compare.
"""
import os, re, subprocess, sys

root = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
base_arg = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else os.environ.get("VERSION_BASE", "")
SKIP = ("vectors/", "checks/", "standards/")
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
FIELD = re.compile(r"^version:[ \t]*[\"']?([^\"'\s#]*)", re.M)


def git(*args):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True)
    return r.returncode, r.stdout


def not_run(why):
    print(f"version-bump: not run: {why}")
    sys.exit(3)


def version(data):
    """The header's version: (tuple or None, as written); None, None when the
    file has no header version."""
    text = data.decode("utf-8", "replace")
    if text.startswith("<!-- blueprint"):
        head = text.split("-->", 1)[0]
    elif text.startswith("---\n"):
        head = text[4:].split("\n---", 1)[0]
    else:
        return None, None
    m = FIELD.search(head)
    if not m:
        return None, None
    v = SEMVER.match(m.group(1))
    return (tuple(int(x) for x in v.groups()) if v else None), m.group(1)


if git("rev-parse", "--git-dir")[0] != 0:
    not_run(f"{root} is not a git repository")
if base_arg:
    base = base_arg
else:
    code, out = git("merge-base", "HEAD", "origin/main")
    if code != 0:
        not_run("no merge-base with origin/main (set VERSION_BASE or pass --base)")
    base = out.decode().strip()
    if base == git("rev-parse", "HEAD")[1].decode().strip():
        base = "HEAD~1"
code, out = git("rev-parse", "--verify", "--quiet", base + "^{commit}")
if code != 0:
    shallow = git("rev-parse", "--is-shallow-repository")[1].decode().strip() == "true"
    not_run(f"base {base} cannot be read" + (" in this shallow clone (fetch with more depth)" if shallow else ""))
base_commit = out.decode().strip()

code, out = git("diff", "--name-status", "-z", "-M", base_commit, "--")
if code != 0:
    not_run(f"git diff against {base} failed")
fields = out.decode().split("\0")
faults, checked, i = [], 0, 0
while i < len(fields) and fields[i]:
    status = fields[i]
    if status[0] in "RC":
        old, new, i = fields[i + 1], fields[i + 2], i + 3
    else:
        old = new = fields[i + 1]
        i += 2
    if status[0] in "AD" or not new.endswith(".md") or new.startswith(SKIP):
        continue
    was_code, was = git("show", f"{base_commit}:{old}")
    if was_code != 0:
        continue
    before, before_text = version(was)
    if before is None:
        continue
    try:
        now = open(os.path.join(root, new), "rb").read()
    except OSError:
        continue
    if now == was:
        continue
    checked += 1
    after, after_text = version(now)
    if after is None:
        faults.append(f"{new}: changed since {base}, and its version {after_text or 'is gone'} is not MAJOR.MINOR.PATCH (was {before_text})")
    elif after <= before:
        faults.append(f"{new}: changed since {base} without its version moving: {before_text} -> {after_text}")
print("\n".join(faults) or f"version-bump: {checked} versioned file(s) changed since {base}, each with its version moved")
sys.exit(1 if faults else 0)
