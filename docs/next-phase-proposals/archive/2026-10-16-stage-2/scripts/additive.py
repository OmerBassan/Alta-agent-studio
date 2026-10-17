"""Pass iff, per file, every edit is an insertion: line-level diff, then char-level within replaced lines.
Frontmatter updated:/amended: lines exempt. Usage: python -I additive.py <orig_root> <new_root> <relpath>..."""
import difflib, io, re, sys
o_root, n_root, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
bad = 0
for p in paths:
    rd = lambda r: [l for l in io.open(f"{r}/{p}", encoding="utf-8", newline="").read().replace("\r\n", "\n").split("\n")
                    if not re.match(r"^(updated|amended): ", l)]
    a, b = rd(o_root), rd(n_root)
    ins = rep = 0; problems = []
    for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if t == "insert": ins += j2 - j1
        elif t == "delete": problems.append(("deleted", a[i1:i2]))
        elif t == "replace":
            olds, news = "\n".join(a[i1:i2]), "\n".join(b[j1:j2])
            ops = difflib.SequenceMatcher(None, olds, news, autojunk=False).get_opcodes()
            if any(o[0] in ("delete", "replace") for o in ops): problems.append(("changed", a[i1:i2]))
            else: rep += i2 - i1
    print(f"{'ok ' if not problems else 'BAD'} {p.split('/')[-1]:22} new lines={ins} lines extended in place={rep}")
    for kind, ls in problems:
        bad += 1; print("    ", kind, [l[:100] for l in ls][:3])
sys.exit(1 if bad else 0)
