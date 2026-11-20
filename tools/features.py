"""Inventory every server-side / interactive feature in the original svad.org.in raw HTML cache."""
import os, re, sys, collections
RAW = sys.argv[1]
feat = collections.defaultdict(collections.Counter)   # feature -> {detail: count}
sample = {}
form_action = re.compile(rb'<form[^>]*action="([^"]*)"', re.I)
postback = re.compile(rb"__doPostBack\(\s*(?:&#39;|')([^'&]*)", re.I)
inputs = re.compile(rb'<(input|select|textarea)\b([^>]*)>', re.I)
attr = lambda a, n: (re.search(rb'\b' + n + rb'\s*=\s*"([^"]*)"', a, re.I) or [None, b''])[1]
endpoints = re.compile(rb'["\']([^"\'\s<>]*\.(?:ashx|asmx|svc)[^"\'\s<>]*)', re.I)
ajax = re.compile(rb'(PageMethods\.\w+|\$\.(?:ajax|post|get|getJSON)\s*\(\s*[{"\'][^)]{0,120})', re.I)
iframe = re.compile(rb'<iframe[^>]*src="([^"]*)"', re.I)
ext_script = re.compile(rb'<script[^>]*src="(https?://[^"]*)"', re.I)
ext_link = re.compile(rb'href="(https?://(?!(?:www\.)?svad\.org\.in)[^"/]*)', re.I)
mailto = re.compile(rb'href="mailto:([^"?]*)', re.I)
onclick = re.compile(rb'on(?:click|change)="([^"]{0,80})', re.I)
n = 0
for root, _, files in os.walk(RAW):
    for f in files:
        if f.endswith('.ct'): continue
        p = os.path.join(root, f)
        try: ct = open(p + '.ct', encoding='utf-8').read()
        except OSError: continue
        if 'html' not in ct: continue
        d = open(p, 'rb').read(); n += 1
        fa = form_action.search(d); page = fa.group(1).decode(errors='replace') if fa else f
        def add(k, v):
            v = v.decode(errors='replace') if isinstance(v, bytes) else v
            feat[k][v] += 1; sample.setdefault((k, v), page)
        for m in postback.findall(d): add('postback', re.sub(rb'\$\d+|ctl\d+', b'#', m))
        for t, a in inputs.findall(d):
            typ = attr(a, rb'type').lower() or t.lower()
            if typ in (b'hidden',): continue
            add('input', t.lower() + b':' + typ + b':' + re.sub(rb'\$\d+|ctl\d+|\d{2,}', b'#', attr(a, rb'name') or attr(a, rb'id')))
        for m in endpoints.findall(d): add('endpoint', m.split(b'?')[0])
        for m in ajax.findall(d): add('ajax', m[:80])
        for m in iframe.findall(d): add('iframe', m[:100])
        for m in ext_script.findall(d): add('ext_script', m.split(b'?')[0])
        for m in ext_link.findall(d): add('ext_domain', m.lower())
        for m in mailto.findall(d): add('mailto', m.lower())
        for m in onclick.findall(d): add('onclick', re.sub(rb'\d+', b'#', m)[:60])
print('html files', n)
for k in feat:
    print(f'\n== {k} ({len(feat[k])} distinct)')
    for v, c in feat[k].most_common(60): print(f'  {c:6} {v}   [e.g. {sample[(k, v)]}]')
