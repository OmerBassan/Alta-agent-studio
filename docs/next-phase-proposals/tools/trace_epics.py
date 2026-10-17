"""Build the story-level traceability table from epics.md's **Traces:** lines.

Usage: python docs/next-phase-proposals/tools/trace_epics.py _bmad-output/planning-artifacts/epics.md [--emit <out.md>]
Prints coverage gaps; with --emit writes the markdown table section.
"""
import re
import sys
from collections import defaultdict

path = sys.argv[1]
text = open(path, encoding="utf-8").read()

stories = re.split(r"^### Story ", text, flags=re.M)[1:]
by_id: dict[str, list[tuple[str, str]]] = defaultdict(list)
status_of: dict[str, str] = {}

TOKEN = re.compile(r"\b(FR|NFR|UX-DR)(\d+)(?:\s*[–-]\s*(?:FR|NFR|UX-DR)?(\d+))?(\s*\(part[^)]*\))?")

for s in stories:
    sid = s.split(":", 1)[0].strip()
    m = re.search(r"\*\*Traces:\*\*(.*?)(?:\*\*Depends on|\n)", s, flags=re.S)
    st = re.search(r"\*\*Status:\*\* ([a-z]+)", s)
    status_of[sid] = st.group(1) if st else "?"
    if not m:
        print("NO TRACES:", sid)
        continue
    for kind, a, b, part in TOKEN.findall(m.group(1)):
        lo, hi = int(a), int(b) if b else int(a)
        for n in range(lo, hi + 1):
            by_id[f"{kind}{n}"].append((sid, "part" if part else "full"))

expected = [f"FR{n}" for n in range(1, 118)] + [f"NFR{n}" for n in range(1, 19)]
ux = [f"UX-DR{n}" for n in range(1, 31)]
missing = [i for i in expected if i not in by_id and i != "FR8"]
missing_ux = [i for i in ux if i not in by_id]
print("stories:", len(stories))
print("PRD ids traced:", sum(1 for i in expected if i in by_id), "/", len(expected), "(FR8 declined)")
print("missing PRD ids:", missing)
print("missing UX-DRs:", missing_ux)
only_part = [i for i in expected if i in by_id and all(k == "part" for _, k in by_id[i])]
print("ids traced only as (part):", only_part)

if "--emit" in sys.argv:
    out = sys.argv[sys.argv.index("--emit") + 1]

    def cell(i):
        if i == "FR8":
            return "— declined for V1 (`m-ux` 22 override; register B-06)", "n/a"
        refs = by_id[i]
        sids = []
        for sid, k in refs:
            label = f"{sid}{' (part)' if k == 'part' else ''}"
            if label not in sids:
                sids.append(label)
        sts = sorted({status_of[sid] for sid, _ in refs})
        state = "done" if sts == ["done"] else ("partly done" if "done" in sts else ("blocked" if sts == ["blocked"] else "open"))
        return ", ".join(sids), state

    lines = [
        "",
        "## Story Traceability",
        "",
        "Generated from each story's **Traces** line (`trace.py` over this file), so it cannot drift from the stories. "
        "**State** is derived from story statuses: *done* = every story delivering it is done and verified; "
        "*partly done* = some delivering story is done; *open* = none done yet; *blocked* = every delivering story waits on a decision gate. "
        "Acceptance criteria live only in the stories above; verification evidence for done stories is in `docs/next-phase-proposals/IMPLEMENTATION-STATE.md` §0.",
        "",
        "| ID | Stories | State |",
        "| --- | --- | --- |",
    ]
    for i in expected + ux:
        stories_cell, state = cell(i)
        lines.append(f"| {i} | {stories_cell} | {state} |")
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("wrote", out)
