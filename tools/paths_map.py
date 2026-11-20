"""Write assets/data/paths.json: lower-case clean path -> real clean path for every page, used by the redirect
function to map old (case-insensitive) .aspx addresses. usage: paths_map.py <site_dir>"""
import glob, json, os, sys

SITE = sys.argv[1]
m = {}
for p in glob.glob("**/*.html", root_dir=SITE, recursive=True):
    p = p.replace(os.sep, "/")
    if p == "404.html": continue
    clean = "/" + p[:-5]
    if clean.endswith("/index"): clean = clean[:-5]
    m.setdefault(clean.lower(), clean)
    if clean.endswith("/") and clean != "/": m.setdefault(clean[:-1].lower() + "/index", clean)
os.makedirs(os.path.join(SITE, "assets", "data"), exist_ok=True)
json.dump(m, open(os.path.join(SITE, "assets", "data", "paths.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("paths", len(m))
