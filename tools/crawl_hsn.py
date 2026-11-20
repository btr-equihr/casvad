"""Download every page of the HSN GST rate grid (Telerik RadGrid) strictly one request at a time.
The grid's own Next button stalls at page 11 on the server, so each page is requested directly with the
RadGrid "FireCommand:...;Page;N" postback. Resumable (hsn_pages.json). Writes hsn_rows.json."""
import json, os, re, sys, time, html as H, urllib.parse
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(HERE, "postback.py"), encoding="utf-8").read().split("if __name__")[0])

URL = "https://svad.org.in/resources/Utilities/HSN_RATE_LIST/HSN_RATE_LIST.aspx"
GRID = "HomepagecontentControl$C$ctl00$RadGrid1"
STATE = os.path.join(HERE, "hsn_pages.json")


def rows(d):
    out = []
    for tr in re.findall(r'<tr[^>]*class="rg(?:Alt)?Row"[^>]*>(.*?)</tr>', d, re.S):
        out.append([re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                    for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)])
    return out


def current_page(d):
    m = re.search(r'class="rgCurrentPage"[^>]*><span>(\d+)</span>', d)
    return int(m.group(1)) if m else None


def last_page(d):
    return max(int(x) for x in re.findall(r"<span>(\d+)</span>", d) or ["1"])


pages = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
d, final = get(URL)
pages["1"] = rows(d)
f = hidden(d)
f["__EVENTTARGET"] = GRID; f["__EVENTARGUMENT"] = f"FireCommand:{GRID}$ctl00;Page;99999"
d_last, _ = get(final, urllib.parse.urlencode(f).encode())
LAST = current_page(d_last)
print("last page", LAST, flush=True)
for n in range(2, LAST + 1):
    if str(n) in pages: continue
    for attempt in range(5):
        f = hidden(d)
        f["__EVENTTARGET"] = GRID; f["__EVENTARGUMENT"] = f"FireCommand:{GRID}$ctl00;Page;{n}"
        try:
            d2, _ = get(final, urllib.parse.urlencode(f).encode())
            if current_page(d2) == n and rows(d2): break
            print("  wrong page", n, current_page(d2), flush=True)
        except Exception as e:
            print("  retry", n, e, flush=True)
        time.sleep(4 * (attempt + 1))
    else:
        raise SystemExit(f"could not fetch page {n}")
    pages[str(n)] = rows(d2)
    if n % 10 == 0:
        json.dump(pages, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
        print("page", n, flush=True)
json.dump(pages, open(STATE, "w", encoding="utf-8"), ensure_ascii=False)
assert sorted(map(int, pages)) == list(range(1, LAST + 1))
all_rows = [r for n in range(1, LAST + 1) for r in pages[str(n)]]
json.dump(all_rows, open(os.path.join(HERE, "hsn_rows.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("TOTAL", len(all_rows), "pages", LAST)
