import os, re, sys, urllib.request, urllib.parse, posixpath

root = sys.argv[1]
got, fail, count = {}, [], [0]
PAT = re.compile(r'href="([^"]*?www\.webtel\.in[/\\]+Image[/\\]+([^"]+?))"', re.I)


def fetch_pdf(name):
    if name in got:
        return got[name]
    safe = re.sub(r"[^A-Za-z0-9._()-]+", "-", name).strip("-")
    out = "assets/docs/" + safe
    import subprocess
    os.makedirs(os.path.join(root, "assets", "docs"), exist_ok=True)
    dest = os.path.join(root, *out.split("/"))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        got[name] = out
        return out
    r = subprocess.run(["curl", "-sfL", "--max-time", "90", "-A", "Mozilla/5.0", "-o", dest,
                        "https://www.webtel.in/Image/" + urllib.parse.quote(name)], capture_output=True)
    if r.returncode == 0 and os.path.exists(dest) and os.path.getsize(dest) > 0:
        got[name] = out
    else:
        got[name] = None
        fail.append((name, "curl exit %d" % r.returncode))
        if os.path.exists(dest): os.remove(dest)
    print("pdf", name, "ok" if got[name] else "FAILED", flush=True)
    return got[name]


for dp, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith(".html"):
            continue
        p = os.path.join(dp, f)
        t = open(p, encoding="utf-8").read()
        if "webtel.in" not in t:
            continue
        relp = os.path.relpath(p, root).replace(os.sep, "/")

        def sub(m):
            name = urllib.parse.unquote(m.group(2)).strip().lstrip("$").strip()
            out = fetch_pdf(name)
            if not out:
                return m.group(0)
            count[0] += 1
            return 'href="%s"' % posixpath.relpath(out, posixpath.dirname(relp) or ".")

        t2 = PAT.sub(sub, t)
        if t2 != t:
            open(p, "w", encoding="utf-8").write(t2)

print("links fixed", count[0], "pdfs", sum(1 for v in got.values() if v), "failed", fail)
