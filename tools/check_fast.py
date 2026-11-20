import os, re, sys, posixpath, urllib.parse
from collections import Counter

root = sys.argv[1]
files = set()
for dp, _, fs in os.walk(root):
    for f in fs:
        files.add(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
REF = re.compile(r"""(?:href|src|data-src|poster)\s*=\s*["']([^"']+)["']|url\(\s*['"]?([^'")]+?)['"]?\s*\)""")
memo, broken, n = {}, Counter(), 0
example = {}
for rel in files:
    if not rel.endswith((".html", ".css")):
        continue
    d = posixpath.dirname(rel)
    t = open(os.path.join(root, *rel.split("/")), encoding="utf-8", errors="replace").read()
    for m in REF.finditer(t):
        r = (m.group(1) or m.group(2) or "").strip()
        if not r or r.startswith(("http://", "https://", "//", "#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        n += 1
        key = (d, r)
        if key not in memo:
            q = urllib.parse.unquote(r.split("#")[0].split("?")[0])
            if not q:
                memo[key] = True
            else:
                target = posixpath.normpath(posixpath.join(d, q)) if d else posixpath.normpath(q)
                memo[key] = target in files
                if not memo[key]:
                    example[key] = rel
        if not memo[key]:
            broken[posixpath.normpath(posixpath.join(d, urllib.parse.unquote(r.split("#")[0].split("?")[0])))] += 1
print("files", len(files), "local refs", n, "distinct broken targets", len(broken), "broken refs", sum(broken.values()))
for tgt, c in broken.most_common(40):
    print(f"{c:7d}  {tgt}")
