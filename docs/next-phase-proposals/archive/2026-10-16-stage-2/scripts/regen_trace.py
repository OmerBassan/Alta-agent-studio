"""1.8: regenerate only the rows of epics.md's Story Traceability table (intro kept, LF kept).
Usage: python -I regen_trace.py <root> <trace_epics.py>"""
import io
import subprocess
import sys
import tempfile
import os

root, tool = sys.argv[1], sys.argv[2]
path = f"{root}/_bmad-output/planning-artifacts/epics.md"
HEAD = "| ID | Stories | State |"
tmp = os.path.join(tempfile.mkdtemp(), "trace.md")
subprocess.run([sys.executable, "-I", tool, path, "--emit", tmp], check=True)
emitted = io.open(tmp, encoding="utf-8", newline="").read().replace("\r\n", "\n")
text = io.open(path, encoding="utf-8", newline="").read()
assert "\r\n" not in text
sec_start = text.index("\n## Story Traceability")
assert text.count(HEAD) == 1 and emitted.count(HEAD) == 1
i = text.index(HEAD, sec_start)
new = text[:i] + emitted[emitted.index(HEAD):].rstrip("\n") + "\n"
io.open(path, "w", encoding="utf-8", newline="").write(new)
print("table rows regenerated in", path)
