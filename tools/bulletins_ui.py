"""Wire the bulletin pages' controls to the static tab pages (usage: bulletins_ui.py <site_dir>). Idempotent.
Tab buttons go to the matching tab page (or show "No records" when that tab is empty on the old site too),
Search filters the listed items by date, the category list opens that category's bulletin, Back goes back."""
import json, os, posixpath, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = sys.argv[1]
res = json.load(open(os.path.join(HERE, "bulletins_result.json")))
tab_pages = res["tab_pages"]
TABS = {"notification": "btn_Notification", "circular": "btn_Circular", "press-release": "btn_PressRelease", "news": "btn_NEWSItem"}


def rel(a, b): return posixpath.relpath(b, posixpath.dirname(a) or ".")


# category name (as in the drop-down) -> bulletin page, matched on letters/digits only
def key(s): return re.sub(r"[^a-z0-9]", "", s.lower())
cat_pages = {}
for base in tab_pages:
    if base.startswith("resources/Bulletins/"):
        cat_pages[key(base.split("/")[2])] = base

JS = r"""// Bulletin pages: the old site switched tabs, searched by date and changed category on its server.
(function () {
  var ID = 'HomepagecontentControl_C_ctl00_';
  function el(x) { return document.getElementById(ID + x); }
  function parse(s) { var m = /(\d{1,2})\/(\d{1,2})\/(\d{4})/.exec(s || ''); return m ? new Date(+m[3], +m[2] - 1, +m[1]) : null; }
  document.addEventListener('DOMContentLoaded', function () {
    var cfg = document.querySelector('script[data-bulletin]');
    if (!cfg) return;
    var tabs = JSON.parse(cfg.getAttribute('data-tabs')), cats = JSON.parse(cfg.getAttribute('data-cats'));
    var current = cfg.getAttribute('data-current');
    var grid = el('GridView1'), tbody = grid ? grid.querySelector('table.rgMasterTable > tbody') : null;
    function setTotal(n) {
      document.querySelectorAll('span').forEach(function (s) { if (/^Total Search Found\s*:/.test(s.textContent.trim())) s.textContent = 'Total Search Found : ' + n; });
    }
    function empty() {
      if (tbody) tbody.innerHTML = '<tr class="rgNoRecords"><td colspan="3" style="text-align:left;"><div>No records to display.</div></td></tr>';
      setTotal(0);
    }
    Object.keys(tabs).forEach(function (t) {
      var b = el(tabs[t].btn); if (!b) return;
      b.removeAttribute('onclick');
      if (t === current) { b.style.fontWeight = 'bold'; b.style.textDecoration = 'underline'; }
      b.addEventListener('click', function () { if (tabs[t].href) location.href = tabs[t].href; else empty(); });
    });
    // date search: replace the server date pickers with the browser's own
    var dates = {};
    ['DateFrom', 'DateTo'].forEach(function (n) {
      var w = el('txt_' + n + '_wrapper'); if (!w) return;
      var inp = document.createElement('input'); inp.type = 'date'; inp.style.cssText = 'padding:2px 4px';
      w.style.display = 'none'; w.parentNode.insertBefore(inp, w); dates[n] = inp;
    });
    var cat = el('drp_Categry'), search = el('Button1'), back = el('btn_back');
    var startCat = cat ? cat.value : '';  // the page's own category is pre-selected
    if (back) { back.type = 'button'; back.onclick = function () { history.back(); }; }
    if (search) {
      search.type = 'button';
      search.addEventListener('click', function () {
        if (cat && cat.value && cat.value !== 'All' && cat.value !== startCat) {
          var k = cat.value.toLowerCase().replace(/[^a-z0-9]/g, '');
          for (var c in cats) if (c === k || c.indexOf(k) >= 0 || k.indexOf(c) >= 0) { location.href = cats[c]; return; }
        }
        var from = dates.DateFrom && dates.DateFrom.value ? new Date(dates.DateFrom.value + 'T00:00') : null;
        var to = dates.DateTo && dates.DateTo.value ? new Date(dates.DateTo.value + 'T00:00') : null;
        if (!tbody) return;
        var shown = 0;
        tbody.querySelectorAll('tr.rgRow, tr.rgAltRow').forEach(function (tr) {
          var d = parse(tr.cells[tr.cells.length - 1] ? tr.cells[tr.cells.length - 1].textContent : '');
          var ok = (!from || (d && d >= from)) && (!to || (d && d <= to));
          tr.style.display = ok ? '' : 'none'; if (ok) shown++;
        });
        setTotal(shown);
      });
    }
  });
})();
"""
open(os.path.join(SITE, "assets", "js", "bulletin.js"), "w", encoding="utf-8").write(JS)

done = 0
for base, tabs in tab_pages.items():
    pages = [(base, None)] + [(p, t) for t, p in tabs.items() if p]
    for page, current in pages:
        fp = os.path.join(SITE, *page.split("/"))
        s = open(fp, encoding="utf-8").read()
        tdata = {t: {"btn": TABS[t], "href": (rel(page, p)[:-5] if p else None)} for t, p in tabs.items()}
        cdata = {k: rel(page, p)[:-5] for k, p in cat_pages.items()}
        tag = (f"<script data-bulletin data-current=\"{current or ''}\" data-tabs='{json.dumps(tdata)}' "
               f"data-cats='{json.dumps(cdata)}' src=\"{rel(page, 'assets/js/bulletin.js')}\"></script>\n")
        s = re.sub(r"<script data-bulletin[^>]*></script>\n?", "", s)
        i = s.rfind("</body>")
        s = s[:i] + tag + s[i:]
        open(fp, "w", encoding="utf-8", newline="").write(s)
        done += 1
print("bulletin pages wired", done, "categories", len(cat_pages))
