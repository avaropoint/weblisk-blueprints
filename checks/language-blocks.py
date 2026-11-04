#!/usr/bin/env python3
"""Every language blueprint declares how it is laid out, built, read and
tested, and its grammars read what its toolchain really writes.

    checks/language-blocks.py                     every file in languages/
    checks/language-blocks.py --file F --as NAME  one file, read from F, as the language NAME
    checks/language-blocks.py --vectors DIR       read the toolchain vectors from DIR

For each language (schemas/language.md, "The layout block", "the module
block", "The toolchain block", "The diagnostics block", "The tests block"):

- each of layout, module, toolchain, diagnostics and tests is declared;
- the layout names its manifest, contract, packages and entry, and its rules
  have unique ids;
- every toolchain command is a list of strings, and a placeholder in one is
  {service}, {package}, {module_root}, {criterion} or {test};
- every regular expression compiles; a text diagnostics line names the groups
  file, line and message; a text test result line names test and outcome;
- the language's vectors (vectors/languages/expected.json), read with its
  own diagnostics and test-result grammar, give exactly the findings and
  outcomes expected.

The reading below is the interpreter an engine would have: it knows the
block's keys and nothing about any language.
"""
import json, os, re, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from families import yaml_blocks  # noqa: E402

CORPUS = os.path.normpath(os.path.join(HERE, ".."))
BLOCKS = ["layout", "module", "toolchain", "diagnostics", "tests"]
PLACEHOLDERS = {"service", "package", "module_root", "criterion", "test", "path"}


def pointer(obj, p):
    for k in [x for x in p.split("/")[1:]]:
        if isinstance(obj, list):
            k = int(k)
        elif not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def read_build(d, text):
    """Findings, read from a build's output by the diagnostics block alone."""
    found = []
    if d["format"] == "text":
        cur = None
        for line in text.split("\n"):
            if any(re.search(x, line) for x in d.get("drop", [])):
                continue
            if d.get("reset") and re.search(d["reset"], line):
                cur = None
                continue
            if cur is not None and d.get("continuation") and re.search(d["continuation"], line):
                cur["message"] += "\n" + line.strip()
                continue
            m = re.search(d["line"], line)
            if m:
                g = m.groupdict()
                cur = {"file": g["file"], "line": int(g["line"]), "col": int(g["col"]) if g.get("col") else None,
                       "message": g["message"]}
                found.append(cur)
    else:
        for line in text.splitlines():
            if not line.strip():
                continue
            o = json.loads(line)
            if any(pointer(o, p) != v for p, v in (d.get("select") or {}).items()):
                continue
            f = {k: pointer(o, p) for k, p in d["fields"].items()}
            sp = d.get("span")
            if sp:
                for s in pointer(o, sp["list"]) or []:
                    if all(pointer(s, p) == v for p, v in (sp.get("where") or {}).items()):
                        for k in ("file", "line", "col"):
                            if k in sp:
                                f[k] = pointer(s, sp[k])
                        break
            found.append(f)
    for f in found:
        f["symbol"] = f["kind"] = None
        for s in d.get("symbols", []):
            m = re.search(s["pattern"], f.get("message") or "", re.M)
            if m:
                f["symbol"], f["kind"] = m.group("symbol"), s["kind"]
                break
    return [{k: f.get(k) for k in ("file", "line", "col", "symbol", "kind")} for f in found]


def read_tests(r, text):
    """{test: pass|fail|skip}, read from a test run's output by the result block alone."""
    out, word = {}, {r["pass"]: "pass", r["fail"]: "fail", r["skip"]: "skip"}
    for line in text.splitlines():
        if r["format"] == "json-lines":
            if not line.strip():
                continue
            o = json.loads(line)
            t, oc = pointer(o, r["test"]), pointer(o, r["outcome"])
        else:
            m = re.search(r["line"], line)
            if not m:
                continue
            t, oc = m.group(r["test"]), m.group(r["outcome"])
        if t and oc in word:
            out[t] = word[oc]
    return out


def judge(name, path, vectors):
    faults, b = [], yaml_blocks(path)
    for k in BLOCKS:
        if not isinstance(b.get(k), dict):
            faults.append(f"{name}: no {k} block")
    if faults:
        return faults
    lay = b["layout"]
    for k in ("manifest", "contract", "packages", "entry", "imports", "rules"):
        if k not in lay:
            faults.append(f"{name}: layout names no {k}")
    ids = [r.get("id") for r in lay.get("rules") or []]
    if len(ids) != len(set(ids)):
        faults.append(f"{name}: layout rule ids repeat")
    if b["module"].get("manifest") != lay.get("manifest"):
        faults.append(f"{name}: module manifest is not the layout's")
    tc = b["toolchain"]
    for k in ("version", "probe", "build", "build_component", "run"):
        if k not in tc:
            faults.append(f"{name}: toolchain names no {k}")
    cmds = [tc.get(k) for k in ("build", "build_component", "run", "vet")] + list(tc.get("prepare") or []) \
        + [(tc.get("probe") or {}).get("command"), b["tests"].get("command")] \
        + list((b["diagnostics"].get("dependency_fault") or {}).get("fix") or [])
    for c in cmds:
        if c is None:
            continue
        if not isinstance(c, list) or not all(isinstance(a, str) for a in c):
            faults.append(f"{name}: a command that is not a list of strings: {c!r}")
            continue
        for a in c:
            for ph in re.findall(r"\{([a-z_]+)\}", a):
                if ph not in PLACEHOLDERS:
                    faults.append(f"{name}: command placeholder {{{ph}}} is not one schemas/language names")
    d = b["diagnostics"]
    pats = [d.get("line"), d.get("continuation"), d.get("reset"), d.get("mechanism_failure"), (tc.get("probe") or {}).get("version")] \
        + list(d.get("drop") or []) + [s.get("pattern") for s in d.get("symbols") or []] + [b["tests"]["result"].get("line")]
    for p in pats:
        if p is None:
            continue
        try:
            re.compile(p)
        except re.error as e:
            faults.append(f"{name}: a pattern that does not compile ({e}): {p!r}")
    if d.get("format") == "text":
        groups = set(re.compile(d.get("line") or "").groupindex)
        for g in ("file", "line", "message"):
            if g not in groups:
                faults.append(f"{name}: diagnostics line names no group {g!r}")
    elif d.get("format") == "json-lines":
        if "message" not in (d.get("fields") or {}):
            faults.append(f"{name}: diagnostics fields name no message")
    else:
        faults.append(f"{name}: diagnostics format is neither text nor json-lines")
    for s in d.get("symbols") or []:
        if "symbol" not in re.compile(s.get("pattern", "")).groupindex:
            faults.append(f"{name}: symbol pattern {s.get('pattern')!r} names no group 'symbol'")
    r = b["tests"].get("result") or {}
    if r.get("format") == "text":
        groups = set(re.compile(r.get("line") or "").groupindex)
        if not {r.get("test"), r.get("outcome")} <= groups:
            faults.append(f"{name}: test result line names no group for its test or outcome")
    if faults or vectors is None:
        return faults
    exp = vectors["expected"].get(name)
    if exp is None:
        return [f"{name}: no toolchain vectors in vectors/languages/expected.json"]
    got = read_build(d, open(os.path.join(vectors["dir"], exp["build"]), encoding="utf-8").read())
    if got != exp["findings"]:
        faults.append(f"{name}: diagnostics read {got} from {exp['build']}, expected {exp['findings']}")
    got = read_tests(r, open(os.path.join(vectors["dir"], exp["test"]), encoding="utf-8").read())
    if got != exp["outcomes"]:
        faults.append(f"{name}: test results read {got} from {exp['test']}, expected {exp['outcomes']}")
    return faults


def main(argv):
    vdir = argv[argv.index("--vectors") + 1] if "--vectors" in argv else os.path.join(CORPUS, "vectors/languages")
    vectors = {"dir": vdir, "expected": json.load(open(os.path.join(vdir, "expected.json"), encoding="utf-8"))}
    if "--file" in argv:
        files = [(argv[argv.index("--as") + 1], argv[argv.index("--file") + 1])]
    else:
        files = [(f[:-3], os.path.join(CORPUS, "languages", f)) for f in sorted(os.listdir(os.path.join(CORPUS, "languages")))
                 if f.endswith(".md") and f != "README.md"]
    faults = []
    for name, path in files:
        faults += judge(name, path, vectors)
    if faults:
        print("\n".join(faults))
        sys.exit(1)
    print(f"language-blocks: {len(files)} languages declare layout, module, toolchain, diagnostics and tests, "
          "and each reads its own toolchain's vectors as expected")


if __name__ == "__main__":
    main(sys.argv[1:])
