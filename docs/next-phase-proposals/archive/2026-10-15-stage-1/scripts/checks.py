"""Stage 1 checks (handoff §7). Usage: python -I checks.py <orig_root> <new_root> [--expect-lf]

Read-only. Compares the original planning files with their edited copies.
"""
import io
import re
import sys

orig, new = sys.argv[1], sys.argv[2]
EXPECT_LF = "--expect-lf" in sys.argv
PA = "_bmad-output/planning-artifacts"
FILES = {
    "prd": f"{PA}/prds/prd-AgentStudio-2026-10-08/prd.md",
    "exp": f"{PA}/ux-designs/ux-AgentStudio-2026-10-08/EXPERIENCE.md",
    "epics": f"{PA}/epics.md",
    "sprint": "_bmad-output/implementation-artifacts/sprint-status.yaml",
    "plan": "docs/next-phase-proposals/NEXT-PHASE-PLAN.md",
    "reg": "docs/next-phase-proposals/BMAD-DECISION-REGISTER.md",
    "handoff": "docs/next-phase-proposals/HANDOFF.md",
    "impl": "docs/next-phase-proposals/IMPLEMENTATION-STATE.md",
    "gate": "docs/next-phase-proposals/PROOF-GATE.md",
}
LF_UNDER_I1 = {"plan", "reg", "impl", "gate"}
ok = True


def fail(msg):
    global ok
    ok = False
    print("FAIL:", msg)


def rb(root, k):
    return open(f"{root}/{FILES[k]}", "rb").read()


def txt(root, k):
    return io.open(f"{root}/{FILES[k]}", encoding="utf-8", newline="").read().replace("\r\n", "\n")


# 1. Line endings: no mixed endings; original style kept (or LF for the four under I1)
print("== line endings")
for k in FILES:
    o, n = rb(orig, k), rb(new, k)
    crlf, lf_only = n.count(b"\r\n"), n.count(b"\n") - n.count(b"\r\n")
    o_style = "CRLF" if b"\r\n" in o else "LF"
    n_style = "mixed" if crlf and lf_only else ("CRLF" if crlf else "LF")
    want = "LF" if (EXPECT_LF and k in LF_UNDER_I1) else o_style
    flag = "ok" if n_style == want else "BAD"
    if flag == "BAD":
        fail(f"{k}: {n_style}, expected {want}")
    print(f"  {k:8} {o_style:4} -> {n_style:5} (want {want}) {flag}{'' if o != n else '  [byte-identical]'}")
    if o != n and txt(orig, k) == txt(new, k):
        print(f"           {k}: content identical, only line endings changed")

# 2. PRD: stripping every marker restores the original lines
print("== PRD marker strip")
po, pn = txt(orig, "prd"), txt(new, "prd")
MARK = re.compile(r" ?\*\[(?:Superseded for V1|superseded for V1|Narrowed for V1|Amended) — §14 A\d[^\]]*\]\*")
pn_body = pn.split("\n## 14. Amendments after finalization")[0]
stripped = MARK.sub("", pn_body)
ol, sl = po.rstrip("\n").split("\n"), stripped.rstrip("\n").split("\n")
missing = [l for l in ol if l not in sl]
added = [l for l in sl if l not in ol]
markers = MARK.findall(pn)
print(f"  inline markers: {len(markers)}")
print(f"  original lines not recovered: {len(missing)}")
for l in missing:
    fail(f"PRD original line lost: {l[:100]}")
print(f"  new non-marker lines before §14: {len(added)}")
for l in added:
    print("    +", l[:140])
sec14 = pn.split("\n## 14. Amendments after finalization")[1] if "## 14." in pn else ""
print(f"  §14 lines: {len(sec14.strip().splitlines())}")
ids = lambda s: set(re.findall(r"\*\*((?:FR|NFR|EX|O)\d+)\*\*", s))
io_, in_ = ids(po), ids(pn)
print(f"  bold FR/NFR/EX/O ids: {len(io_)} -> {len(in_)} {'equal' if io_ == in_ else 'DIFFER'}")
if io_ != in_:
    fail("PRD id sets differ")
for l in pn.split("\n"):
    if MARK.search(l) and l.startswith("|"):
        base = MARK.sub("", l)
        if l.count("|") != base.count("|"):
            fail(f"table row column count changed: {l[:80]}")
print("  frontmatter:", re.search(r"^---\n(.*?)\n---", pn, re.S).group(1).replace("\n", " | "))

# 3. status fields
print("== status")
for k in ("prd", "epics", "exp"):
    s = re.search(r"^status: (\w+)", txt(new, k), re.M).group(1)
    s0 = re.search(r"^status: (\w+)", txt(orig, k), re.M).group(1)
    print(f"  {k}: {s0} -> {s}")
    if s != s0:
        fail(f"{k} status changed")

# 4. forward dependencies in epics.md
print("== dependencies")
ep = txt(new, "epics")
order = re.findall(r"^### Story (\d+\.\d+):", ep, re.M)
pos = {s: i for i, s in enumerate(order)}
fwd = []
for block in re.split(r"^### Story ", ep, flags=re.M)[1:]:
    sid = block.split(":", 1)[0].strip()
    m = re.search(r"\*\*Depends on:\*\*(.*?)(?:· \*\*Verification|\n)", block)
    if not m:
        continue
    dep = m.group(1)
    dep = dep.split("recommended input, not a dependency")[0]
    dep = re.sub(r"§\s*\d+(\.\d+)*", "", dep)
    dep = re.sub(r"PRD [^·;]*", "", dep)
    for d in re.findall(r"\b(\d+\.\d+)\b", dep):
        if d in pos and pos[d] >= pos[sid]:
            fwd.append((sid, d))
print(f"  stories: {len(order)}; forward dependencies: {fwd or 'none'}")
if fwd:
    fail(f"forward dependencies: {fwd}")

# 5. statuses per story (for the record)
print("== story statuses changed")
eo = txt(orig, "epics")
st = lambda t: dict(re.findall(r"^### Story (\d+\.\d+):.*?\*\*Status:\*\* ([^\n]*)", t, re.M | re.S))
so, sn = st(eo), st(ep)
for s in order:
    if so.get(s) != sn.get(s):
        print(f"  {s}: {so.get(s)!r} -> {sn.get(s)!r}")

print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
