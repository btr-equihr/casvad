# casvad - S V A D and Associates website

Static replica of https://svad.org.in (rebuilt Nov 2026 after the hosting credentials were lost).
Plain HTML/CSS/JS, no server code. Live copy: https://svad-org-in-spimproject.pages.dev (Cloudflare Pages).

## Layout

| Path | What it is |
|---|---|
| `site/` | The website: firm pages, `laws/`, `detail/`, `resources/`, `notificationsearch/`, `allevent.html`, `404.html`, and `assets/` (css, js, images, fonts, docs, vendor, data) |
| `functions/_middleware.js` | Cloudflare Pages Function: redirects old `.aspx` addresses to the new pages |
| `tools/` | The scripts that crawled the old site and applied the fixes, plus the crawled data in `tools/data/` |

Not included in this repository: the `notificationdetail-*.html` pages (notification detail pages that the old site addressed by encrypted query strings).
Links to them in other pages will not resolve until those files are added back.

## Deploy (Cloudflare Pages)

Run from the repository root so `functions/` is picked up:

```
npx wrangler pages deploy site --project-name svad-org-in-spimproject --branch main
```

Use `--branch preview` first to test. The free plan allows 20,000 files per deployment; the full site is 19,413 files.

## Important notes

- The old vendor server (Webtel) returns other pages' content when it receives parallel requests. When crawling it, fetch ONE page at a time (see `tools/build_full.py`).
- Company email runs on Zoho. When connecting the domain svad.org.in, keep the Zoho MX records (`mx.zoho.in` 10, `mx2.zoho.in` 20, `mx3.zoho.in` 50) and the SPF / zoho-verification TXT records, or email stops.
- `site/README.txt` has the full list of differences from the original site.
