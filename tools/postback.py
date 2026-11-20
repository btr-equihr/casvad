"""Probe an ASP.NET postback on svad.org.in (one request at a time) and summarise the result."""
import sys, re, html, urllib.request, urllib.parse, http.cookiejar
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Referer": url})
    with op.open(req, timeout=120) as r:
        return r.read().decode("utf-8", "replace"), r.geturl()

def hidden(d):
    return {html.unescape(n): html.unescape(v) for n, v in re.findall(
        r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', d)}

def summary(d, label):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", d, flags=re.S)
    txt = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", t)))
    m = re.search(r"Total Search Found : \d+.{0,80}", txt)
    nd = len(set(re.findall(r'notificationdetail\.aspx\?[^"\']+', d, re.I)))
    print(f"[{label}] len={len(d)} notifdetail-links={nd} :: {m.group(0) if m else txt[:200]}")

if __name__ == "__main__":
    url = sys.argv[1]
    d, final = get(url)
    summary(d, "GET")
    for target in sys.argv[2:]:
        f = hidden(d)
        f["__EVENTTARGET"] = target; f["__EVENTARGUMENT"] = ""
        # a submit button is sent as name=value instead of event target
        if target.startswith("submit:"):
            name = target[7:]; f["__EVENTTARGET"] = ""; f[name] = "Search"
        d2, _ = get(final, urllib.parse.urlencode(f).encode())
        summary(d2, target)
        open(sys.argv[0] + "." + re.sub(r"\W", "_", target)[-30:] + ".html", "w", encoding="utf-8").write(d2)
