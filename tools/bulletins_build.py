"""Add the bulletin tab views (Notification / Circular / Press Release / News Item) to the static site and make the
tab buttons, date search and Back button work in the browser. Linked pages that the copy does not have yet are
downloaded (one at a time) with the normal builder, plus the NIC page that was skipped.
usage: bulletins_build.py <site_dir> <raw_cache_dir>"""
import glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUILDER = r"C:\Users\spim\AppData\Local\Temp\claude\5ebb8f4d8abc9959\e42af655-3b16-4f17-b079-ebbaaa0a9e89\scratchpad\build_full.py"
SITE_DIR, RAW_DIR = sys.argv[1], sys.argv[2]
sys.argv = [BUILDER, SITE_DIR, RAW_DIR]
os.environ["WORKERS"] = "1"
src = open(BUILDER, encoding="utf-8").read().rsplit("\nmain()", 1)[0]
exec(compile(src, BUILDER, "exec"), globals())

TABS = {"notification": "btn_Notification", "circular": "btn_Circular", "press-release": "btn_PressRelease", "news": "btn_NEWSItem"}
TABDIR = os.path.join(HERE, "bulletin_tabs")
summary = json.load(open(os.path.join(HERE, "bulletin_summary.json")))

VIRTUAL = {}
_fetch = fetch
def fetch(url):  # noqa: F811  (build_page looks this name up at call time)
    if url in VIRTUAL: return VIRTUAL[url], "text/html; charset=utf-8"
    return _fetch(url)

ROW = re.compile(r'<tr class="rg(?:Alt)?Row" id="HomepagecontentControl_C_ctl00_GridView1_ctl00__\d+">.*?</tr>', re.S)


def combine(key, tab):
    first = open(os.path.join(TABDIR, f"{key}-{tab}.html"), encoding="utf-8").read()
    extra = []
    for fp in sorted(glob.glob(os.path.join(TABDIR, f"{key}-{tab}-p*.html")), key=lambda f: int(re.search(r"-p(\d+)\.html$", f).group(1))):
        extra += ROW.findall(open(fp, encoding="utf-8").read())
    rows = ROW.findall(first) + extra
    i = first.find('id="HomepagecontentControl_C_ctl00_GridView1"')
    j = first.find("</tbody>", i)
    html = first[:j] + "".join(extra) + first[j:] if extra else first
    # one static page holds every item, so the server's page slider is removed
    html = re.sub(r'<tr class="rgPager">.*?</tr>\s*</table></td>\s*</tr>', "", html, count=1, flags=re.S)
    total = int((re.search(r"Total Search Found\s*:\s*(\d+)", first) or [0, len(rows)])[1])
    # the old server's own paging of tab lists is broken (page 2+ returns a different list), so visitors only
    # ever saw the first page; say so instead of showing a pager that cannot work
    label = f"Showing all {len(rows)} items" if len(rows) >= total else f"Showing the latest {len(rows)} of {total} items"
    html = re.sub(r"You are viewing page\s*1\s*of\s*\d+", label, html, flags=re.S)
    return html, len(rows)


queue, seen_q = [], set()
def enqueue(u):
    k = ikey(u)
    if k not in seen_q and not DROP_PAGES.search(urllib.parse.urlsplit(u).path):
        seen_q.add(k); queue.append(u)


tab_pages = {}  # base page -> {tab: page or None}
for url, info in summary.items():
    base = page_path(url)
    assert os.path.exists(os.path.join(OUT, base)), base
    tab_pages[base] = {}
    for tab in TABS:
        n = info[tab]
        if not n:
            tab_pages[base][tab] = None; continue
        html, count = combine(info["key"], tab)
        assert count == n or count == 20, (url, tab, count, n)
        vurl = norm(url + "?svadtab=" + tab)
        out = base[:-5] + "-" + tab + ".html"
        page_of[ikey(vurl)] = out
        VIRTUAL[vurl] = html.encode("utf-8")
        build_page(vurl, enqueue)
        tab_pages[base][tab] = out
        print("tab page", out, count, flush=True)

# NIC page that the first crawl skipped (its link had a typo "Section-J. aspx")
enqueue(norm("https://svad.org.in/resources/Utilities/NIC/Division-67_Section-J.aspx"))

built, failed = [], []
while queue:
    u = queue.pop(0)
    out = page_path(u)
    if os.path.exists(os.path.join(OUT, out)): continue
    try:
        build_page(u, enqueue); built.append(out)
        if len(built) % 25 == 0: print("built", len(built), "queued", len(queue), flush=True)
    except Exception as e:
        failed.append((u, repr(e)[:150]))
print("new pages", len(built), "failed", len(failed))
for f in failed[:30]: print("  FAILED", f)
json.dump({"tab_pages": tab_pages, "built": built, "failed": failed}, open(os.path.join(HERE, "bulletins_result.json"), "w"), indent=1)
