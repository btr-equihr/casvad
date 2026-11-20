"""Turn the HSN GST rate page into a working static page: all rows in assets/data/hsn.json, with the grid's own
filter boxes, page numbers and page-size box working in the browser. usage: hsn_page.py <site_dir> <hsn_rows.json>"""
import json, os, re, sys

SITE, ROWS = sys.argv[1], sys.argv[2]
PAGE = "resources/Utilities/HSN_RATE_LIST/HSN_RATE_LIST.html"
rows = json.load(open(ROWS, encoding="utf-8"))
assert len(rows) > 10000 and all(len(r) == 4 for r in rows)
os.makedirs(os.path.join(SITE, "assets", "data"), exist_ok=True)
json.dump(rows, open(os.path.join(SITE, "assets", "data", "hsn.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

JS = r"""// HSN GST rate list: the old page loaded each page of 100 rows from the server. All rows are now in
// assets/data/hsn.json and the grid's filter boxes, page numbers and page size work in the browser.
(function () {
  var G = 'HomepagecontentControl_C_ctl00_RadGrid1', data = [], view = [], page = 0, size = 100;
  var FILTERS = ['ProductGroupHeadings', 'ProductGroupCode', 'Productgroupname', 'HSNRate']; // column order in the grid
  function $(sel, root) { return (root || document).querySelector(sel); }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }
  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById(G);
    if (!grid) return;
    var tbody = $('table.rgMasterTable > tbody', grid), pagerCell = $('.rgPagerCell', grid), num = $('.rgNumPart', grid);
    var boxes = FILTERS.map(function (f) { return grid.querySelector('input[id$="FilterTextBox_' + f + '"]'); });
    grid.querySelectorAll('input[id*="_Filter_"], input[name*="$Filter_"]').forEach(function (b) { b.style.display = 'none'; });
    var menu = document.getElementById(G + '_rfltMenu'); if (menu) menu.style.display = 'none';
    // page size: replace the server combobox with a plain select
    var combo = grid.querySelector('.RadComboBox');
    var sel = document.createElement('select');
    [10, 20, 50, 100].forEach(function (n) { var o = document.createElement('option'); o.value = n; o.textContent = n; if (n === size) o.selected = true; sel.appendChild(o); });
    if (combo) combo.parentNode.replaceChild(sel, combo);
    var info = document.createElement('div'); info.className = 'rgWrap rgInfoPart'; info.style.cssText = 'float:right;padding:4px 8px';
    pagerCell.appendChild(info);
    function btn(cls) { var b = grid.querySelector('input.' + cls); if (b) { b.type = 'button'; b.removeAttribute('onclick'); } return b; }
    var first = btn('rgPageFirst'), prev = btn('rgPagePrev'), next = btn('rgPageNext'), last = btn('rgPageLast');
    function pages() { return Math.max(1, Math.ceil(view.length / size)); }
    function render() {
      var start = page * size, h = '';
      view.slice(start, start + size).forEach(function (r, i) {
        h += '<tr class="' + (i % 2 ? 'rgAltRow' : 'rgRow') + '"><td style="width:12%;">' + esc(r[0]) + '</td><td style="width:15%;">' + esc(r[1]) +
             '</td><td style="width:67%;">' + esc(r[2]) + '</td><td style="width:5%;">' + esc(r[3]) + '</td></tr>';
      });
      tbody.innerHTML = h || '<tr class="rgNoRecords"><td colspan="4" style="text-align:left;">No records to display.</td></tr>';
      var n = pages(), from = Math.floor(page / 10) * 10, links = '';
      if (from > 0) links += '<a href="#" data-p="' + (from - 1) + '" title="Previous Pages"><span>...</span></a>';
      for (var p = from; p < Math.min(n, from + 10); p++)
        links += '<a href="#" data-p="' + p + '"' + (p === page ? ' class="rgCurrentPage"' : '') + '><span>' + (p + 1) + '</span></a>';
      if (from + 10 < n) links += '<a href="#" data-p="' + (from + 10) + '" title="Next Pages"><span>...</span></a>';
      num.innerHTML = links;
      info.textContent = view.length + ' items in ' + n + ' pages';
    }
    function go(p) { page = Math.min(Math.max(0, p), pages() - 1); render(); }
    function filter() {
      var q = boxes.map(function (b) { return b ? b.value.trim().toLowerCase() : ''; });
      view = data.filter(function (r) { for (var i = 0; i < 4; i++) if (q[i] && String(r[i]).toLowerCase().indexOf(q[i]) < 0) return false; return true; });
      go(0);
    }
    num.addEventListener('click', function (e) { var a = e.target.closest('a[data-p]'); if (a) { e.preventDefault(); go(+a.getAttribute('data-p')); } });
    if (first) first.onclick = function () { go(0); };
    if (prev) prev.onclick = function () { go(page - 1); };
    if (next) next.onclick = function () { go(page + 1); };
    if (last) last.onclick = function () { go(pages() - 1); };
    sel.onchange = function () { size = +sel.value; go(0); };
    var t; boxes.forEach(function (b) {
      if (!b) return;
      b.placeholder = 'Filter...';
      b.addEventListener('input', function () { clearTimeout(t); t = setTimeout(filter, 200); });
      b.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });
    });
    fetch(document.querySelector('script[data-hsn]').getAttribute('data-hsn')).then(function (r) { return r.json(); })
      .then(function (j) { data = j; filter(); });
  });
})();
"""
open(os.path.join(SITE, "assets", "js", "hsn-list.js"), "w", encoding="utf-8").write(JS)
fp = os.path.join(SITE, *PAGE.split("/"))
s = open(fp, encoding="utf-8").read()
tag = '<script data-hsn="../../../assets/data/hsn.json" src="../../../assets/js/hsn-list.js"></script>\n'
if "data-hsn=" not in s:
    i = s.rfind("</body>")
    s = s[:i] + tag + s[i:]
s = re.sub(r"href=\"javascript:__doPostBack\('HomepagecontentControl\$C\$ctl00\$RadGrid1[^\"]*\"", 'href="#"', s)
open(fp, "w", encoding="utf-8", newline="").write(s)
print("hsn rows", len(rows))
