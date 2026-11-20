"""Fetch the four tab views (Notification / Circular / Press Release / News Item) of every bulletin page,
one request at a time, and store them as html files in bulletin_tabs/ (resumable). Prints a count summary."""
import hashlib, json, os, re, sys, time, urllib.parse
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "postback.py"), encoding="utf-8").read().split("if __name__")[0])

OUT = os.path.join(HERE, "bulletin_tabs")
os.makedirs(OUT, exist_ok=True)
P = "HomepagecontentControl$C$ctl00$"
TABS = {"notification": "btn_Notification", "circular": "btn_Circular", "press-release": "btn_PressRelease", "news": "btn_NEWSItem"}
URLS = [l.strip() for l in open(os.path.join(HERE, "bulletin_urls.txt"), encoding="utf-8") if l.strip()]


def total(d):
    m = re.search(r"Total Search Found\s*:\s*(?:<[^>]+>\s*)*(\d+)", d)
    return int(m.group(1)) if m else -1


summary = {}
for url in URLS:
    key = hashlib.md5(url.encode()).hexdigest()[:10]
    res = {}
    need = [t for t in TABS if not os.path.exists(os.path.join(OUT, f"{key}-{t}.html"))]
    if need:
        for attempt in range(4):
            try:
                d, final = get(url); break
            except Exception as e:
                print("  retry GET", url, e, flush=True); time.sleep(5 * (attempt + 1))
        else:
            raise SystemExit("GET failed " + url)
        open(os.path.join(OUT, f"{key}-default.html"), "w", encoding="utf-8").write(d)
        for t in need:
            for attempt in range(4):
                f = hidden(d)
                f["__EVENTTARGET"] = P + TABS[t]; f["__EVENTARGUMENT"] = ""
                try:
                    d2, _ = get(final, urllib.parse.urlencode(f).encode()); break
                except Exception as e:
                    print("  retry", t, url, e, flush=True); time.sleep(5 * (attempt + 1))
            else:
                raise SystemExit("POST failed " + url + " " + t)
            open(os.path.join(OUT, f"{key}-{t}.html"), "w", encoding="utf-8").write(d2)
    for t in ["default"] + list(TABS):
        fp = os.path.join(OUT, f"{key}-{t}.html")
        res[t] = total(open(fp, encoding="utf-8").read()) if os.path.exists(fp) else None
    summary[url] = {"key": key, **res}
    print(url, res, flush=True)
json.dump(summary, open(os.path.join(HERE, "bulletin_summary.json"), "w"), indent=1)
print("DONE")
