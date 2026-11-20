// Act search: the old site searched an Act by section/rule number or by words on its server.
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
