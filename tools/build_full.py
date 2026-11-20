"""Full static replica of https://svad.org.in : main firm pages (clean names) + the entire Knowledge Bank library
(laws, rules, forms, bulletins, notifications, calculators, utilities, what's new, events), all sharing assets/.

usage: build_full.py <out_dir> <raw_cache_dir>
Resumable: every fetched response is cached in <raw_cache_dir>.
"""
import hashlib, os, posixpath, re, sys, threading, time, urllib.parse, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from bs4 import BeautifulSoup, Comment

SITE = "https://svad.org.in"
OUT, RAW = sys.argv[1], sys.argv[2]
# The old server returns OTHER pages' content when requests overlap (21/40 wrong at 8 parallel, 0/40 sequential),
# so pages are fetched strictly one at a time. Static files (images/css/js/pdf) are unaffected and may come from
# an earlier download (FALLBACK_RAW).
WORKERS = int(os.environ.get("WORKERS", "1"))
FALLBACK_RAW = os.environ.get("FALLBACK_RAW")
STATIC_EXT = re.compile(r"\.(css|js|png|jpe?g|gif|svg|webp|ico|bmp|woff2?|ttf|eot|otf|pdf|docx?|xlsx?|pptx?|zip|rar|txt|csv|axd)$", re.I)
LAW_PAGE = re.compile(r"^/laws/-?\d+/([^/]+)\.aspx$", re.I)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
FIRM_EMAIL = "admin@svad.org.in"

MAIN = {
    "/": "index.html", "/resource/home.aspx": "index.html", "/default.aspx": "index.html",
    "/resource/about_us.aspx": "about-us.html", "/resource/partners.aspx": "team.html",
    "/resource/clients.aspx": "clients.html", "/resource/career.aspx": "careers.html",
    "/resource/contact_us.aspx": "contact-us.html", "/resource/disclaimer.aspx": "disclaimer.html",
    "/newthemequerysheet.aspx": "query.html",
    "/resource/services/audit_assurance.aspx": "services/audit-assurance.html",
    "/resource/services/taxation.aspx": "services/taxation.html",
    "/resource/services/accounting_bookkeeping.aspx": "services/accounting-bookkeeping.html",
    "/resource/services/corporate_regulatory_compliances.aspx": "services/corporate-regulatory-compliances.html",
    "/resource/services/labour_law_statutory_compliance.aspx": "services/labour-law-statutory-compliance.html",
    "/resource/services/due_diligence_transaction_advisory.aspx": "services/due-diligence-transaction-advisory.html",
    "/resource/services/advisory_consultancy.aspx": "services/gst-international-tax-fema-advisory.html",
    "/resource/taxation.aspx": "services/taxation.html",
    "/resource/audit_assurance.aspx": "services/audit-assurance.html",
    "/resource/accounting_bookkeeping.aspx": "services/accounting-bookkeeping.html",
    "/resource/corporate_regulatory_compliances.aspx": "services/corporate-regulatory-compliances.html",
    "/resource/labour_law_statutory_compliance.aspx": "services/labour-law-statutory-compliance.html",
}
DROP_PAGES = re.compile(r"/(login|timesheet)\.aspx$", re.I)  # need the old server; cannot work statically
ASSET_DIR = {"css": "css", "js": "js", "woff": "fonts", "woff2": "fonts", "ttf": "fonts", "eot": "fonts", "otf": "fonts",
             "pdf": "docs", "doc": "docs", "docx": "docs", "xls": "docs", "xlsx": "docs", "ppt": "docs", "pptx": "docs",
             "zip": "docs", "rar": "docs", "txt": "docs", "csv": "docs"}
IMG_EXT = {"png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "avif"}
CT_EXT = {"text/css": "css", "application/javascript": "js", "text/javascript": "js", "application/x-javascript": "js",
          "image/png": "png", "image/jpeg": "jpg", "image/gif": "gif", "image/svg+xml": "svg", "image/webp": "webp",
          "image/x-icon": "ico", "image/vnd.microsoft.icon": "ico", "font/woff2": "woff2", "font/woff": "woff",
          "application/pdf": "pdf", "application/msword": "doc", "application/vnd.ms-excel": "xls", "application/zip": "zip"}
KEEP_FONT_AWESOME = True  # assets/css/font-awesome.min.css + assets/fonts are the fixed cdnjs 4.7.0 copies

lock = threading.Lock()
nonhtml_pages = {}  # .html path that links were pointed at -> asset path of the file it really is (e.g. a PDF)
asset_of, used_names, page_of, seen = {}, set(), {}, set()
missing, dropped = [], set()
stats = {"pages": 0, "assets": 0}


def fetch(url):
    key = hashlib.md5(url.encode()).hexdigest()
    fp = os.path.join(RAW, key[:2], key)
    if FALLBACK_RAW and STATIC_EXT.search(urllib.parse.urlsplit(url).path):
        fb = os.path.join(FALLBACK_RAW, key[:2], key)
        if os.path.exists(fb + ".ct") and not os.path.exists(fp + ".ct"):
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fb, "rb") as a, open(fp, "wb") as b: b.write(a.read())
            with open(fb + ".ct", encoding="utf-8") as a, open(fp + ".ct", "w", encoding="utf-8") as b: b.write(a.read())
    if os.path.exists(fp + ".ct"):
        with open(fp, "rb") as f: data = f.read()
        with open(fp + ".ct", encoding="utf-8") as f: ct = f.read()
        if ct.startswith("ERR "): raise RuntimeError(ct)
        return data, ct
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last = None
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data, ct, final = r.read(), r.headers.get("Content-Type", ""), r.geturl()
            if "/error" in final.lower() or final.lower().rstrip("/").endswith("svad.org.in") and urllib.parse.urlsplit(url).path not in ("", "/"):
                raise urllib.error.HTTPError(url, 404, "redirected to " + final, None, None)
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            with open(fp, "wb") as f: f.write(data)
            with open(fp + ".ct", "w", encoding="utf-8") as f: f.write(ct)
            return data, ct
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 404, 410):
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                open(fp, "wb").close()
                with open(fp + ".ct", "w", encoding="utf-8") as f: f.write(f"ERR {e.code} {e.msg}")
                break
        except Exception as e:
            last = e
        time.sleep(3 * (i + 1))
    raise last


def norm(u):
    p = urllib.parse.urlsplit(u)
    return urllib.parse.urlunsplit(("https", "svad.org.in", p.path or "/", p.query, ""))


def ikey(u):
    """Identity key: the old IIS server is case-insensitive, so URLs differing only in case are the same resource."""
    p = urllib.parse.urlsplit(u)
    return (p.path.lower(), p.query.lower())


def same_site(u):
    return urllib.parse.urlsplit(u).netloc.lower() in ("svad.org.in", "www.svad.org.in")


def absolute(base, ref):
    ref = (ref or "").strip()
    if not ref or ref.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "whatsapp:", "sms:")):
        return None
    try:
        return urllib.parse.urljoin(base, ref)
    except ValueError:
        return None


def rel(from_path, to_path):
    return posixpath.relpath(to_path, posixpath.dirname(from_path) or ".")


def write(path, data):
    fp = os.path.join(OUT, *path.split("/"))
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "wb") as f: f.write(data)


def page_path(u):
    """Output path for a same-site page URL (main pages get clean names, library keeps its URL structure)."""
    u = norm(u)
    key = ikey(u)
    with lock:
        if key in page_of: return page_of[key]
        p = urllib.parse.urlsplit(u)
        path = urllib.parse.unquote(p.path) or "/"
        main = MAIN.get(path.lower()) if not p.query else None
        if main:
            out = main
        else:
            path = path.lstrip("/") or "index"
            if path.endswith("/"): path += "index"
            path = re.sub(r'[<>:"|?*\\#%]', "_", path)
            path = "/".join((seg.strip(" .") or "_") for seg in path.split("/"))
            root, _ = posixpath.splitext(path)
            if p.query: root += "-" + hashlib.md5(p.query.encode()).hexdigest()[:10]
            out = root + ".html"
            if out.lower() in used_names:  # a different page whose name differs only in case
                out = root + "-" + hashlib.md5(u.encode()).hexdigest()[:6] + ".html"
            used_names.add(out.lower())
        page_of[key] = out
        return out


asset_done = {}  # key -> threading.Event, so concurrent requests for the same asset wait for the first one


def asset(url, referer=None):
    u = norm(urllib.parse.urldefrag(url)[0])
    key = ikey(u)
    with lock:
        ev = asset_done.get(key)
        owner = ev is None
        if owner:
            ev = asset_done[key] = threading.Event()
    if not owner:
        if key in asset_of:  # path already assigned (also covers CSS that references itself)
            return asset_of[key]
        ev.wait(300)
        return asset_of.get(key)
    try:
        return _asset(u, key, referer)
    finally:
        ev.set()


def _asset(u, key, referer):
    try:
        data, ct = fetch(u)
    except Exception as e:
        with lock:
            missing.append(f"{u} (from {referer}): {e}")
            asset_of[key] = None
        return None
    p = urllib.parse.urlsplit(u)
    name = posixpath.basename(urllib.parse.unquote(p.path)) or "file"
    stem, ext = posixpath.splitext(name)
    ext = ext.lstrip(".").lower()
    ct_ext = CT_EXT.get(ct.split(";")[0].strip().lower())
    if ext in ("axd", "ashx", "aspx", "") and ct_ext: ext = ct_ext
    if p.query: stem += "-" + hashlib.md5(p.query.encode()).hexdigest()[:8]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("-") or "file"
    kind = "images" if ext in IMG_EXT else ASSET_DIR.get(ext, "misc")
    with lock:
        out = f"assets/{kind}/{stem}.{ext}"
        if out.lower() in used_names:
            out = f"assets/{kind}/{stem}-{hashlib.md5(u.encode()).hexdigest()[:6]}.{ext}"
        used_names.add(out.lower())
        stats["assets"] += 1
    if KEEP_FONT_AWESOME and out == "assets/css/font-awesome.min.css" and os.path.exists(os.path.join(OUT, "assets", "css", "font-awesome.min.css")):
        with lock: asset_of[key] = out
        return out
    with lock: asset_of[key] = out  # set before CSS recursion so self/cyclic references resolve
    if ext == "css":
        data = rewrite_css(data.decode("utf-8", errors="replace"), u, out).encode("utf-8")
        data = re.sub(rb"background-image:url\(https://carajeev\.com[^)]*\);?", b"", data)
    write(out, data)
    return out


URL_RE = re.compile(r"""url\(\s*(['"]?)([^'")]+?)\1\s*\)""", re.I)
IMPORT_RE = re.compile(r"""@import\s+(['"])([^'"]+)\1""", re.I)


def rewrite_css(css, base_url, out_path):
    def sub(m):
        a = absolute(base_url, m.group(2))
        if not a or not same_site(a): return m.group(0)
        o = asset(a, base_url)
        if not o: return m.group(0)
        frag = "#" + m.group(2).split("#", 1)[1] if "#" in m.group(2) else ""
        return f"url({m.group(1)}{rel(out_path, o)}{frag}{m.group(1)})"
    css = URL_RE.sub(sub, css)
    def imp(m):
        a = absolute(base_url, m.group(2))
        o = asset(a, base_url) if a and same_site(a) else None
        return f"@import {m.group(1)}{rel(out_path, o)}{m.group(1)}" if o else m.group(0)
    return IMPORT_RE.sub(imp, css)


ASP_SCRIPT = re.compile(r"ASP\.NET Ajax|typeof\(Sys\)|Sys\.(WebForms|Application)|theForm|__doPostBack|WebForm_|Telerik|RadScriptManager")

QUERY_JS = """
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('query-submit');
  if (!btn) return;
  btn.addEventListener('click', function (e) {
    e.preventDefault();
    function v(id) { var el = document.getElementById(id); return el ? (el.value || '').trim() : ''; }
    var name = v('q_name'), email = v('q_email'), query = v('q_query');
    if (!name || !email || !query) { alert('Please fill in your name, email address and query.'); return; }
    var s = document.getElementById('q_subject');
    var subject = s && s.selectedIndex > 0 ? s.options[s.selectedIndex].text : 'General';
    var body = 'Name: ' + name + '\\nDesignation: ' + v('q_designation') + '\\nOrganization: ' + v('q_organization') +
      '\\nOffice Address: ' + v('q_address') + '\\nCity: ' + v('q_city') + '\\nEmail: ' + email +
      '\\nTelephone: ' + v('q_phone') + '\\nMobile: ' + v('q_mobile') + '\\nSubject: ' + subject + '\\n\\nQuery:\\n' + query;
    window.location.href = 'mailto:%s?subject=' + encodeURIComponent('Website query: ' + subject) + '&body=' + encodeURIComponent(body);
  });
});
""" % FIRM_EMAIL
QUERY_IDS = {"txt_name": "q_name", "txt_designation": "q_designation", "txt_organization": "q_organization",
             "txt_officeaddress": "q_address", "txt_city": "q_city", "txt_emailaddress": "q_email",
             "txt_telephoneno": "q_phone", "txt_mobile": "q_mobile", "drp_subjectofquery": "q_subject", "txt_Query": "q_query"}


def fix_query_form(soup):
    for f in soup.find_all(["input", "select", "textarea"]):
        fid = f.get("id", "")
        for suf, new in QUERY_IDS.items():
            if fid.endswith("_" + suf):
                f["id"] = f["name"] = new
                for lab in soup.find_all("label", attrs={"for": fid}): lab["for"] = new
        for a in [a for a in f.attrs if a.startswith("on")]: del f.attrs[a]
    cap = soup.find("input", id=re.compile("txtCaptha", re.I))
    if cap: (cap.find_parent("tr") or cap.parent).decompose()
    for img in soup.find_all("img", src=re.compile("captcha|Handler\\.ashx", re.I)): (img.find_parent("tr") or img).decompose()
    for b in soup.find_all("input", attrs={"type": "submit"}):
        if b.get("id", "").endswith("btn_submit"):
            b["id"] = "query-submit"; b["type"] = "button"; b.attrs.pop("name", None)
        elif b.get("id", "").endswith("btn_Back"):
            b["type"] = "button"; b["onclick"] = "history.back();"; b.attrs.pop("name", None)
    for s in soup.find_all("script"):
        if s.string and ("check_QuerySheet" in s.string or "RefreshCaptcha" in s.string): s.decompose()
    d = soup.find(id="div_msg")
    if d: d.decompose()
    s = soup.new_tag("script"); s.string = QUERY_JS
    (soup.body or soup).append(s)


def law_page_ok(path, data):
    """A law index/chapter page must link to its own act's pages (catches the server returning another act)."""
    m = LAW_PAGE.match(path)
    if not m:
        return True
    slug = urllib.parse.unquote(m.group(1)).lower()
    t = data.decode("utf-8", "replace")
    inner = [urllib.parse.unquote(s).lower() for s in re.findall(r'href="/laws/\d+/([^"/]+)\.aspx"', t)]
    if not inner:
        return True
    return slug in inner or max(set(inner), key=inner.count) == slug


def build_page(u, enqueue):
    out = page_path(u)
    data, ct = fetch(u)
    path = urllib.parse.unquote(urllib.parse.urlsplit(u).path)
    for attempt in range(4):
        if law_page_ok(path, data):
            break
        key = hashlib.md5(u.encode()).hexdigest()
        fp = os.path.join(RAW, key[:2], key)
        for x in (fp, fp + ".ct"):
            if os.path.exists(x): os.remove(x)
        time.sleep(2 + attempt * 3)
        data, ct = fetch(u)
    else:
        with lock: missing.append(f"WRONG-CONTENT {u}: server kept returning another act's page")
    if "html" not in ct.lower():  # an .aspx link that actually returns a file
        asset(u, u)  # saved under assets/; links already written point at the .html path, fixed in post-pass
        with lock: nonhtml_pages[out] = asset_of.get(ikey(norm(u)))
        return
    soup = BeautifulSoup(data.decode("utf-8", errors="replace"), "html.parser")

    for inp in soup.find_all("input", attrs={"type": "hidden"}):
        if re.match(r"(__|RadScriptManager)", inp.get("name", "") or inp.get("id", "")): inp.decompose()
    for s in soup.find_all("script"):
        src = s.get("src", "")
        if re.search(r"(WebResource|ScriptResource|Telerik\.Web\.UI)\.axd|jquery\.marquee", src, re.I) or (not src and s.string and ASP_SCRIPT.search(s.string)):
            s.decompose()
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)): c.extract()
    for form in soup.find_all("form"):
        if form.get("id") == "form1" or "aspx" in (form.get("action") or ""):
            form.name = "div"
            for a in ("method", "action", "name", "enctype", "onsubmit"): form.attrs.pop(a, None)
    for a in soup.find_all("a", href=re.compile(r"webtel\.in", re.I)):
        if "display:none" in (a.get("style") or "").replace(" ", ""): a.decompose()
    for m in soup.find_all("meta", attrs={"http-equiv": re.compile("content-type", re.I)}): m.decompose()

    for a in list(soup.find_all("a", href=True)):
        if getattr(a, "decomposed", False) or a.attrs is None: continue
        href = a.get("href")
        if href is None: continue
        absu = absolute(u, href)
        if not absu or not same_site(absu): continue
        frag = "#" + href.split("#", 1)[1] if "#" in href else ""
        path = urllib.parse.urlsplit(absu).path
        if DROP_PAGES.search(path):
            with lock: dropped.add(path)
            (a.find_parent("li") or a).decompose(); continue
        ext = posixpath.splitext(path)[1].lower().lstrip(".")
        if ext in IMG_EXT or ext in ASSET_DIR:
            o = asset(absu, u)
            if o: a["href"] = rel(out, o)
            continue
        a["href"] = rel(out, page_path(absu)) + frag
        enqueue(norm(absu))

    for tag, attr in (("img", "src"), ("img", "data-src"), ("script", "src"), ("link", "href"), ("source", "src"),
                      ("video", "src"), ("video", "poster"), ("audio", "src"), ("input", "src"), ("embed", "src"),
                      ("iframe", "src"), ("object", "data")):
        for t in soup.find_all(tag, attrs={attr: True}):
            absu = absolute(u, t[attr])
            if not absu or not same_site(absu): continue
            if tag == "link" and not re.search(r"stylesheet|icon|preload|manifest", " ".join(t.get("rel", []))): continue
            if tag == "iframe":
                t[attr] = rel(out, page_path(absu)); enqueue(norm(absu)); continue
            o = asset(absu, u)
            if o: t[attr] = rel(out, o)
    for t in soup.find_all(srcset=True):
        parts = []
        for item in t["srcset"].split(","):
            bits = item.strip().split()
            if bits:
                absu = absolute(u, bits[0])
                if absu and same_site(absu):
                    o = asset(absu, u)
                    if o: bits[0] = rel(out, o)
            parts.append(" ".join(bits))
        t["srcset"] = ", ".join(parts)
    for t in soup.find_all(style=True):
        st = re.sub(r"behavior\s*:\s*url\([^)]*\)\s*;?", "", t["style"])
        st = re.sub(r"background-image\s*:\s*url\(None\)\s*;?", "", st)
        t["style"] = rewrite_css(st, u, out)
    for st in soup.find_all("style"):
        if st.string: st.string = rewrite_css(st.string, u, out)

    clean = "https://svad.org.in/" + ("" if out == "index.html" else out[:-5] if out.endswith(".html") else out)
    for m in soup.find_all("meta", attrs={"property": "og:url"}): m["content"] = clean
    for m in soup.find_all("meta", attrs={"property": "og:description"}):
        if "svad.org.in," in m.get("content", ""): m["content"] = "S V A D and Associates - Chartered Accountants"
    if out == "query.html": fix_query_form(soup)

    html = str(soup)
    html = re.sub(r"<head([^>]*)>", r'<head\1>\n<meta charset="utf-8"/>', html, count=1)
    if not html.lstrip().lower().startswith("<!doctype"): html = "<!DOCTYPE html>\n" + html
    html = html.replace("\xa0", "&nbsp;")
    write(out, html.encode("utf-8"))
    with lock: stats["pages"] += 1


def main():
    os.makedirs(OUT, exist_ok=True)
    pending, futures = [], {}
    def enqueue(u):
        with lock:
            k = ikey(u)
            if k in seen or DROP_PAGES.search(urllib.parse.urlsplit(u).path): return
            seen.add(k); pending.append(u)
    for start in ["/", "/resource/About_Us.aspx", "/resource/Partners.aspx", "/resource/Clients.aspx", "/resource/Career.aspx",
                  "/resource/Contact_Us.aspx", "/resource/Disclaimer.aspx", "/NewThemeQuerysheet.aspx"]:
        enqueue(norm(SITE + start))
    pool = ThreadPoolExecutor(WORKERS)
    last, failed = time.time(), []
    while True:
        with lock:
            while pending and len(futures) < WORKERS * 3:
                u = pending.pop()  # depth-first keeps the queue small
                futures[pool.submit(build_page, u, enqueue)] = u
        if not futures: break
        done, _ = wait(list(futures), timeout=10, return_when=FIRST_COMPLETED)
        for f in done:
            u = futures.pop(f)
            try: f.result()
            except Exception as e: failed.append((u, repr(e)[:200]))
        if time.time() - last > 30:
            last = time.time()
            print(f"{time.strftime('%H:%M:%S')} pages={stats['pages']} assets={stats['assets']} queued={len(pending)} failed={len(failed)}", flush=True)
    pool.shutdown()
    for html_path, real in nonhtml_pages.items():  # .aspx links that were really files (PDF etc.)
        if real:
            target = rel(html_path, real)
            write(html_path, (f'<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={target}">'
                              f'<link rel="canonical" href="{target}"><a href="{target}">Open file</a>').encode("utf-8"))
    with open(os.path.join(os.path.dirname(OUT.rstrip('/\\')), "build_report.txt"), "w", encoding="utf-8") as f:
        f.write(f"pages={stats['pages']} assets={stats['assets']} failed={len(failed)}\n\nFAILED PAGES (also broken on the live site if 404)\n")
        for u, e in sorted(failed): f.write(f"  {u}  {e}\n")
        f.write("\nMISSING ASSETS\n" + "".join(f"  {m}\n" for m in missing))
        f.write("\nDROPPED (server-only)\n" + "".join(f"  {d}\n" for d in sorted(dropped)))
    # pages that failed: point their links somewhere sane is handled by the post-check
    print(f"DONE pages={stats['pages']} assets={stats['assets']} failed={len(failed)}", flush=True)


main()
