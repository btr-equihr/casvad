"""Does the old server mix up pages only under concurrent requests? Fetch act index pages and check the slug inside."""
import re, sys, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

home = urllib.request.urlopen(urllib.request.Request("https://svad.org.in/", headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "replace")
acts = sorted(set(re.findall(r'href="(/laws/-\d+/[^"]+\.aspx)"', home)))[:40]


def check(path):
    slug = path.rsplit("/", 1)[1][:-5]
    t = urllib.request.urlopen(urllib.request.Request("https://svad.org.in" + path, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode("utf-8", "replace")
    inner = Counter(re.findall(r'href="/laws/\d+/([^"/]+)\.aspx"', t))
    if not inner:
        return None
    top = inner.most_common(1)[0][0]
    return top.lower() == slug.lower() or inner.get(slug, 0) > 0


for workers in (1, 8):
    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(check, acts))
    ok = sum(1 for r in res if r is True); bad = sum(1 for r in res if r is False)
    print(f"workers={workers}: correct={ok} WRONG={bad} (no chapter links={res.count(None)}) in {time.time()-t0:.0f}s", flush=True)
