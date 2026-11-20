"""Repoint local links whose target exists only with different letter case (Windows hides this; Cloudflare doesn't)."""
import os, re, sys, posixpath, urllib.parse

root = sys.argv[1]
files, lower = set(), {}
for dp, _, fs in os.walk(root):
    for f in fs:
        r = os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")
        files.add(r)
        lower.setdefault(r.lower(), r)
REF = re.compile(r"""((?:href|src)\s*=\s*["'])([^"']+)(["'])""")
fixed = 0
for rel in sorted(files):
    if not rel.endswith(".html"):
        continue
    d = posixpath.dirname(rel)
    p = os.path.join(root, *rel.split("/"))
    t = open(p, encoding="utf-8", errors="replace").read()

    def sub(m):
        global fixed
        r = m.group(2)
        if r.startswith(("http:", "https:", "//", "#", "mailto:", "tel:", "javascript:", "data:")):
            return m.group(0)
        path, sep, frag = r.partition("#")
        q = urllib.parse.unquote(path.split("?")[0])
        if not q:
            return m.group(0)
        target = posixpath.normpath(posixpath.join(d, q))
        if target in files:
            return m.group(0)
        real = lower.get(target.lower())
        if not real:
            return m.group(0)
        fixed += 1
        return m.group(1) + posixpath.relpath(real, d or ".") + sep + frag + m.group(3)

    t2 = REF.sub(sub, t)
    if t2 != t:
        open(p, "w", encoding="utf-8").write(t2)
print("case-fixed links:", fixed)
