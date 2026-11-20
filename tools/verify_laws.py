"""Detect pages where the old server returned another page's content (laws/ pages: URL slug vs slugs linked inside)."""
import os, re, sys
from collections import Counter

root = sys.argv[1]
bad, total = [], 0
for dp, _, fs in os.walk(os.path.join(root, "laws")):
    for f in fs:
        if not f.endswith(".html"):
            continue
        total += 1
        slug = f[:-5]
        slug = re.sub(r"-[0-9a-f]{6}$", "", slug)
        t = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
        # links to sibling law pages inside the page body (exclude the big nav menu: it links to act indexes with negative ids)
        inner = Counter(re.findall(r'href="(?:\.\./)+(?:laws/)?\d+/([^"/]+)\.html"', t))
        if not inner:
            continue
        top, n = inner.most_common(1)[0]
        if top.lower() != slug.lower() and inner.get(slug, 0) == 0:
            bad.append((os.path.relpath(os.path.join(dp, f), root), top, n))
print(f"law pages {total}, mismatched {len(bad)}")
for b in bad[:15]:
    print("  ", b)
