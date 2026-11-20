"""For every bulletin tab view with more than one page (20 rows per page), fetch pages 2..N, one request at a time:
GET the bulletin, click the tab, then jump straight to each page with the grid's FireCommand Page postback.
Saves bulletin_tabs/<key>-<tab>-p<N>.html (resumable)."""
import hashlib, json, os, re, sys, time, urllib.parse
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "postback.py"), encoding="utf-8").read().split("if __name__")[0])
OUT = os.path.join(HERE, "bulletin_tabs")
P = "HomepagecontentControl$C$ctl00$"
GRID = P + "GridView1"
TABS = {"notification": "btn_Notification", "circular": "btn_Circular", "press-release": "btn_PressRelease", "news": "btn_NEWSItem"}


def npages(d):
    m = re.search(r"You are viewing page\s*\d+\s*of\s*(\d+)", re.sub(r"<[^>]+>", " ", d))
    return int(m.group(1)) if m else 1


def cur(d):
    m = re.search(r"You are viewing page\s*(\d+)", re.sub(r"<[^>]+>", " ", d))
    return int(m.group(1)) if m else None


def post(url, d, fields):
    f = hidden(d); f.update(fields)
    for attempt in range(4):
        try:
            return get(url, urllib.parse.urlencode(f).encode())[0]
        except Exception as e:
            print("  retry", e, flush=True); time.sleep(5 * (attempt + 1))
    raise SystemExit("POST failed")


summary = json.load(open(os.path.join(HERE, "bulletin_summary.json")))
for url, info in summary.items():
    key = info["key"]
    for t, btn in TABS.items():
        first = open(os.path.join(OUT, f"{key}-{t}.html"), encoding="utf-8").read()
        n = npages(first)
        if n <= 1: continue
        todo = [p for p in range(2, n + 1) if not os.path.exists(os.path.join(OUT, f"{key}-{t}-p{p}.html"))]
        print(url, t, "pages", n, "todo", len(todo), flush=True)
        if not todo: continue
        d, final = get(url)
        d = post(final, d, {"__EVENTTARGET": P + btn, "__EVENTARGUMENT": ""})
        for p in todo:
            for attempt in range(3):
                d2 = post(final, d, {"__EVENTTARGET": GRID, "__EVENTARGUMENT": f"FireCommand:{GRID}$ctl00;Page;{p}"})
                if cur(d2) == p: break
                print("  wrong page", p, cur(d2), flush=True); time.sleep(3)
            else:
                print(f"BROKEN ON SERVER: page {p} of {url} {t} - skipping this tab", flush=True)
                break
            open(os.path.join(OUT, f"{key}-{t}-p{p}.html"), "w", encoding="utf-8").write(d2)
print("DONE")
