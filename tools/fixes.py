"""Offline fixes applied to the built svad replica (usage: fixes.py <site_dir>). Idempotent.
1. vendor calculator scripts/styles (ip.webtel.in/hra/...) -> local assets/vendor/hra/...
2. "Email Login" -> Zoho Mail (the firm's mail is on Zoho; mail.svad.org.in never resolved)
3. Careers form -> opens the visitor's email app with the application filled in
4. Income Tax calculator (computed on the old server) -> official Income Tax Department calculator
5. Compliance calendar: working "Pick Date" popup; server-only "Login with google" removed
6. Act search (Section / Content) on every Act & chapter page -> works in the browser from per-act indexes
"""
import glob, json, os, posixpath, re, sys

SITE = sys.argv[1]
FIRM_EMAIL = "admin@svad.org.in"
changed = {}


def rel(from_path, to_path):
    return posixpath.relpath(to_path, posixpath.dirname(from_path) or ".")


def read(p): return open(os.path.join(SITE, p), encoding="utf-8").read()


def save(p, s, why):
    old = read(p)
    if s != old:
        open(os.path.join(SITE, p), "w", encoding="utf-8", newline="").write(s)
        changed[why] = changed.get(why, 0) + 1


def inject(html, marker, block):
    """Insert block before </body> once (marker makes it idempotent)."""
    if marker in html: return html
    i = html.rfind("</body>")
    return html[:i] + block + html[i:] if i >= 0 else html + block


all_html = [p.replace(os.sep, "/") for p in glob.glob("**/*.html", root_dir=SITE, recursive=True)]

# 1 + 2 ---------------------------------------------------------------------------------------
VENDOR = re.compile(r'(href|src)="https?://ip\.webtel\.in/hra/((?:js|css|forms)/[^"?#]+)"')
for p in all_html:
    s = read(p)
    if "ip.webtel.in/hra/" not in s and "mail.svad.org.in" not in s: continue
    s2 = VENDOR.sub(lambda m: f'{m.group(1)}="{rel(p, "assets/vendor/hra/" + m.group(2))}"', s)
    s2 = s2.replace('href="http://mail.svad.org.in"', 'href="https://mail.zoho.in/"')
    save(p, s2, "vendor scripts / email link")

# 3 careers -------------------------------------------------------------------------------------
CAREERS_JS = """
<script id="careers-mail">
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.querySelector('input[name="skip_submit"]');
  if (!btn) return;
  btn.type = 'button';
  var note = document.createElement('p');
  note.style.cssText = 'margin-top:8px;font-size:14px;color:#555;text-align:center';
  note.textContent = 'Clicking "Send Application" opens your email app with the form filled in. Please attach your CV to that email before sending it.';
  btn.parentNode.appendChild(note);
  function v(name) { var el = document.querySelector('[name="' + name + '"]'); return el ? (el.value || '').trim() : ''; }
  function sel(name) { var el = document.querySelector('[name="' + name + '"]'); return el && el.selectedIndex > 0 ? el.options[el.selectedIndex].text : ''; }
  btn.addEventListener('click', function () {
    var first = v('First_Name'), last = v('Last_Name'), email = v('Email_Address'), phone = v('Phone');
    var gender = sel('HomepagecontentControl$C$ctl00$gender'), dob = v('dob');
    if (!first || !last || !email || !phone || !gender || !dob) { alert('Please fill in all required fields (name, email, phone, gender and date of birth).'); return; }
    if (!/^\\S+@\\S+\\.\\S+$/.test(email)) { alert('Please enter a valid email address.'); return; }
    var file = document.querySelector('input[type="file"]');
    var cv = file && file.files && file.files[0] ? file.files[0].name : '';
    var body = 'Name: ' + first + ' ' + last + '\\nEmail: ' + email + '\\nPhone: ' + phone + '\\nGender: ' + gender +
      '\\nDate of birth: ' + dob + '\\nPosition applied for: ' + v('Position') + '\\nQualification: ' + v('Qualification') +
      '\\nPortfolio / website: ' + v('Portfolio') + '\\nCurrent organization: ' + v('Organization') +
      '\\nExperience: ' + (sel('expyear') || '0') + ' year(s) ' + (sel('expmnth') || '0') + ' month(s)' +
      '\\n\\nReference / comments / questions:\\n' + v('Reference') +
      '\\n\\n' + (cv ? '(Please attach your CV: ' + cv + ')' : '(Please attach your CV)');
    window.location.href = 'mailto:%s?subject=' + encodeURIComponent('Job application: ' + (v('Position') || 'General') + ' - ' + first + ' ' + last) + '&body=' + encodeURIComponent(body);
  });
});
</script>
""" % FIRM_EMAIL
save("careers.html", inject(read("careers.html"), 'id="careers-mail"', CAREERS_JS), "careers form")

# 4 income tax calculator ----------------------------------------------------------------------
ITC = "resources/Calculators/Tax_Calculator/cal_Income_Tax.html"
OFFICIAL = "https://www.incometax.gov.in/iec/foportal/income-tax-calculator"
ITC_JS = """
<script id="itc-official">
document.addEventListener('DOMContentLoaded', function () {
  var btn = document.getElementById('Calculate');
  if (!btn) return;
  var box = document.createElement('div');
  box.style.cssText = 'margin:10px auto;max-width:720px;padding:12px 16px;border:1px solid #f0c36d;background:#fff8e1;border-radius:6px;font-size:15px;text-align:left';
  box.innerHTML = 'This income tax calculator used to run on our previous website server. For an up-to-date calculation (old and new regime), ' +
    'please use the <a href="%s" target="_blank" rel="noopener">official Income Tax Department calculator</a>.';
  var table = btn.closest('table');
  (table && table.parentNode ? table.parentNode : document.body).insertBefore(box, table || null);
  btn.value = 'Calculate on incometax.gov.in';
  btn.style.width = 'auto';
  btn.addEventListener('click', function (e) {
    e.preventDefault(); e.stopImmediatePropagation();
    window.open('%s', '_blank', 'noopener');
  }, true);
});
</script>
""" % (OFFICIAL, OFFICIAL)
save(ITC, inject(read(ITC), 'id="itc-official"', ITC_JS), "income tax calculator")

# 5 compliance calendar ------------------------------------------------------------------------
CAL = "allevent.html"
s = read(CAL)
s = re.sub(r'<a class="modal-trigger-btn login-with-google"[^>]*>.*?</a>', "", s, flags=re.S)
s = s.replace('href="javascript:__doPostBack(\'HomepagecontentControl$C$ctl00$btnShowCalendar\',\'\')"', 'href="#"')
CAL_JS = """
<script id="pick-date">
// "Pick Date": the old page opened a server-side (Telerik) calendar window; this shows the same calendar locally.
function showCalendar() {
  var pop = document.getElementById('HomepagecontentControl_C_ctl00_CalendarPopup');
  if (!pop) return false;
  if (!pop.dataset.ready) {
    pop.dataset.ready = '1';
    pop.style.cssText = 'display:none;position:fixed;z-index:10000;left:50%;top:50%;transform:translate(-50%,-50%);background:#fff;padding:12px 12px 8px;border-radius:8px;box-shadow:0 10px 40px rgba(0,0,0,.35)';
    var close = document.createElement('button');
    close.type = 'button'; close.textContent = '\\u00d7'; close.title = 'Close';
    close.style.cssText = 'position:absolute;right:6px;top:2px;border:0;background:none;font-size:22px;cursor:pointer';
    close.onclick = function () { pop.style.display = 'none'; };
    pop.appendChild(close);
    pop.querySelectorAll('.rcTitlebar a, a.rcFastPrev, a.rcPrev, a.rcNext, a.rcFastNext').forEach(function (a) { a.style.visibility = 'hidden'; });
    pop.querySelectorAll('td[title] a').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        var d = new Date(a.parentNode.getAttribute('title'));
        if (isNaN(d)) return;
        var iso = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        var f = document.getElementById('dateFrom'), t = document.getElementById('dateTo');
        if (f && t && typeof applyCustomDates === 'function') { f.value = iso; t.value = iso; applyCustomDates(); }
        pop.style.display = 'none';
      });
    });
  }
  pop.style.display = 'block';
  return false;
}
</script>
"""
s = inject(s, 'id="pick-date"', CAL_JS)
save(CAL, s, "calendar")

# 6 act search -----------------------------------------------------------------------------------
os.makedirs(os.path.join(SITE, "assets", "data", "acts"), exist_ok=True)
LINK = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>')
acts = {}
for idx in sorted(glob.glob("laws/-*/*.html", root_dir=SITE)):
    idx = idx.replace(os.sep, "/")
    slug = posixpath.basename(idx)[:-5]
    d = read(idx)
    title = (re.search(r"<title>\s*([^<]*?)\s*</title>", d) or [None, slug])[1]
    items, chapters = [], []
    for href, text in LINK.findall(d):
        target = posixpath.normpath(posixpath.join(posixpath.dirname(idx), href.split("#")[0]))
        if re.match(r"laws/[0-9.]+/", target): chapters.append(target)
        elif target.startswith("detail/"): items.append([re.sub(r"\s+", " ", text).strip(), target])
    for ch in dict.fromkeys(chapters):
        if not os.path.exists(os.path.join(SITE, ch)): continue
        for href, text in LINK.findall(read(ch)):
            target = posixpath.normpath(posixpath.join(posixpath.dirname(ch), href.split("#")[0]))
            if target.startswith("detail/"): items.append([re.sub(r"\s+", " ", text).strip(), target])
    seen, uniq = set(), []
    for it in items:
        if it[0] and tuple(it) not in seen: seen.add(tuple(it)); uniq.append(it)
    acts[slug] = {"index": idx, "chapters": list(dict.fromkeys(chapters))}
    json.dump({"title": title, "items": uniq}, open(os.path.join(SITE, "assets", "data", "acts", slug + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))

ACT_JS = r"""// Act search: the old site searched an Act by section/rule number or by words on its server.
// This does the same in the browser using a small per-Act index (assets/data/acts/<act>.json).
(function () {
  var ID = 'HomepagecontentControl_C_ctl00_';
  function norm(s) {
    return (s || '').toLowerCase().replace(/[ _\-]+/g, ' ').replace(/^\s*(part\s+[ivx]+\s*)?(section|rule|regulation|article|clause)\s*/, '').trim();
  }
  function number(s) { return norm(s).split(/\s+/)[0].replace(/[.:,;)]+$/, ''); }
  document.addEventListener('DOMContentLoaded', function () {
    var sec = document.getElementById(ID + 'txt_SectionID'), txt = document.getElementById(ID + 'txt_Content');
    var go = document.getElementById(ID + 'btn_Search'), home = document.getElementById(ID + 'btn_Home');
    var script = document.querySelector('script[data-act-index]');
    if (!sec || !txt || !go || !script) return;
    var root = script.getAttribute('data-root'), indexUrl = script.getAttribute('data-act-index');
    var actHome = script.getAttribute('data-act-home');
    go.type = 'button';
    if (home) { home.type = 'button'; home.onclick = function () { location.href = actHome; }; }
    window.select_section = function () { txt.value = ''; };
    window.select_content = function () { sec.value = ''; };
    var box = document.createElement('div');
    box.style.cssText = 'display:none;margin:10px auto;max-width:96%;text-align:left;border:1px solid #ddd;border-radius:6px;padding:10px 14px;background:#fafafa';
    var bar = go.parentNode; bar.parentNode.insertBefore(box, bar.nextSibling);
    var data = null;
    function load(cb) {
      if (data) return cb(data);
      fetch(indexUrl).then(function (r) { return r.json(); }).then(function (j) { data = j; cb(j); })
        .catch(function () { alert('Search is not available right now. Please browse the chapters below.'); });
    }
    function show(list, label) {
      box.style.display = 'block';
      if (!list.length) { box.innerHTML = '<b>No matching section found</b> for ' + label + '.'; return; }
      var h = '<b>' + list.length + ' result' + (list.length > 1 ? 's' : '') + '</b> for ' + label + ':<ol style="margin:6px 0 0 18px;padding:0">';
      list.slice(0, 200).forEach(function (it) {
        h += '<li style="margin:3px 0"><a href="' + root + it[1].replace(/\.html$/, '') + '">' + it[0].replace(/[<>&]/g, '') + '</a></li>';
      });
      box.innerHTML = h + '</ol>' + (list.length > 200 ? '<p>Showing the first 200 - add more words to narrow the search.</p>' : '');
    }
    function esc(s) { return s.replace(/[<>&"]/g, ''); }
    function run() {
      var q = sec.value.trim(), w = txt.value.trim();
      if (!q && !w) { alert('Please Enter Section NO/Content ...'); return; }
      load(function (j) {
        var res;
        if (q) {
          var n = number(q);
          res = j.items.filter(function (it) { return number(it[0]) === n; });
          if (res.length === 1) { location.href = root + res[0][1].replace(/\.html$/, ''); return; }
          show(res, 'section / rule "' + esc(q) + '"');
        } else {
          var words = norm(w).split(/\s+/).filter(Boolean);
          res = j.items.filter(function (it) { var t = norm(it[0]); return words.every(function (x) { return t.indexOf(x) >= 0; }); });
          show(res, '"' + esc(w) + '"');
        }
      });
    }
    go.addEventListener('click', function (e) { e.preventDefault(); run(); });
    [sec, txt].forEach(function (el) { el.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); run(); } }); });
  });
})();
"""
os.makedirs(os.path.join(SITE, "assets", "js"), exist_ok=True)
open(os.path.join(SITE, "assets", "js", "act-search.js"), "w", encoding="utf-8").write(ACT_JS)
pages = {}
for slug, a in acts.items():
    for p in [a["index"]] + a["chapters"]: pages.setdefault(p, (slug, a["index"]))
for p in all_html:  # chapter pages not linked from an index still belong to the act with the same file name
    if re.match(r"laws/[0-9.]+/", p) and p not in pages:
        slug = posixpath.basename(p)[:-5]
        if slug in acts: pages[p] = (slug, acts[slug]["index"])
missing_index = [p for p in all_html if p.startswith("laws/") and p not in pages]
for p, (slug, idx) in pages.items():
    if not os.path.exists(os.path.join(SITE, p)): continue
    s = read(p)
    if "txt_SectionID" not in s: continue
    tag = (f'<script data-act-index="{rel(p, "assets/data/acts/" + slug + ".json")}" data-root="{rel(p, "x")[:-1]}" '
           f'data-act-home="{rel(p, idx)[:-5]}" src="{rel(p, "assets/js/act-search.js")}"></script>\n')
    s = re.sub(r'<script data-act-index="[^"]*"[^>]*></script>\n?', "", s)
    save(p, inject(s, "data-act-index", tag), "act search")
print(json.dumps(changed, indent=1))
print("acts", len(acts), "items", sum(len(json.load(open(os.path.join(SITE, "assets/data/acts", s + ".json"), encoding="utf-8"))["items"]) for s in acts))
print("law pages without an act index:", missing_index[:10], len(missing_index))
