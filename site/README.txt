S V A D AND ASSOCIATES - WEBSITE (full static replica of https://svad.org.in)
============================================================================

Rebuilt 12-Nov-2026, re-crawled and verified 13-Nov-2026 from the live site, then
completed the same day with everything that used to need the old server.
Plain HTML/CSS/JS - no server code, no database, no ASP.NET. Runs on ANY host
(the old-link redirects need Cloudflare Pages - see below).

IMPORTANT - why it was re-crawled: the old vendor server returns OTHER pages'
content when it receives several requests at once (21 of 40 law pages came
back wrong in a parallel test, 0 of 40 when fetched one at a time). The
13-Nov copy was fetched strictly one page at a time and every law index /
chapter page was checked against its title (1,202 checked, 0 wrong).
If you ever re-download the site, fetch ONE page at a time.

LIVE COPY:  https://svad-org-in-spimproject.pages.dev
            (Cloudflare Pages project: svad-org-in-spimproject)

SIZE: 15,352 pages + assets = 19,413 files, ~1.1 GB.
(Cloudflare Pages free plan allows up to 20,000 files per deployment.)

FOLDER STRUCTURE
----------------
Firm pages (clean names):
  index.html, about-us.html, team.html, clients.html, careers.html,
  contact-us.html, disclaimer.html, query.html, 404.html (page not found)
  services/   7 service pages

Knowledge Bank library (same URL structure as the old site, .aspx -> .html):
  laws/            Acts & Rules - index pages and chapter pages
  detail/          individual sections, rules and notification texts
  resources/       Bulletins, Forms, Calculators, Utilities, Links
  notificationsearch/   Notifications & Circulars
  allevent.html    Event / Compliance Calendar
  NewThemebulletin.html   What's New
  *-notification / -circular / -press-release .html
                   the bulletin tabs (the old site loaded them from its server)

Shared assets:
  assets/css  assets/js  assets/images  assets/fonts
  assets/docs      PDFs/forms linked from the library (incl. ~150 notification
                   PDFs that the old site loaded from the vendor's server)
  assets/vendor/hra  calculator scripts that used to load from the vendor's
                   server (ip.webtel.in) - now part of the site
  assets/data      acts/*.json (Act search), hsn.json (all 16,678 HSN rates),
                   paths.json (used by the old-link redirects)

FEATURES THAT USED THE OLD SERVER - NOW WORKING IN THE BROWSER
---------------------------------------------------------------
- Old links: any old address (e.g. /laws/-26/Income_Tax_Act.aspx,
  /resource/About_Us.aspx, notificationdetail.aspx?acturl=...) redirects to
  the right page, so Google results and bookmarks keep working. Unknown
  addresses show a proper "Page not found" page.
  This is done by a Cloudflare Pages Function: ..\svad-cloudflare-redirects\
  functions\_middleware.js. To redeploy, run from that folder:
    npx wrangler pages deploy "<path to svad-website>" --project-name svad-org-in-spimproject --branch main
- Act search (Section / Rule number, or words) on all 1,202 Act pages.
- HSN GST rate list: all 167 pages (16,678 rows) with the filter boxes,
  page numbers and page size working.
- Bulletins: the Notification / Circular / Press Release / News tabs, date
  search, category list and Back button.
- Compliance Calendar "Pick Date".
- Careers form: opens the applicant's email app addressed to
  admin@svad.org.in with the application filled in (they attach their CV).
- Query form: same, opens the visitor's email app.
- "Email Login" now opens Zoho Mail (the firm's email is on Zoho;
  mail.svad.org.in never existed).

WHAT IS DIFFERENT FROM THE OLD SITE (and why)
---------------------------------------------
1. Admin menu: "Login" and "Time Sheet" removed, and "Login with google" on
   the calendar - they ran on the old vendor's server.
2. Income Tax calculator: it calculated on the old server, so its Calculate
   button now opens the official Income Tax Department calculator
   (incometax.gov.in). All other calculators work as before.
3. Compliance calendar and What's New are snapshots (November 2026). Webtel
   used to update them every month; they no longer change by themselves.
4. Bulletin tab lists longer than 20 items show the latest 20: on the old
   server the page-2 button of those lists is broken (it returns a different
   list), so visitors there could only see the first 20 too.
5. The "Times Visited" counter in the footer is frozen.
6. Fixed bugs that also exist on the live site: blank Font Awesome icons,
   broken menu characters, script errors, a hidden vendor backlink, a popup
   loading images from another firm's website, and a NIC page that the old
   site linked with a typo.
7. ~340 links (about 0.07%) are broken on the old site too - mistakes in the
   vendor's content such as links to a staff member's desktop
   ("file:/C:/Users/..."). They were left as they are.

CONNECTING THE DOMAIN svad.org.in - KEEP THE EMAIL WORKING
-----------------------------------------------------------
The domain's DNS is at the registrar's "orderbox-dns" nameservers (you need
the REGISTRAR login - different from the lost hosting login).
Company email runs on Zoho. When the DNS changes, these records MUST be kept
or email stops:
  MX   svad.org.in   mx.zoho.in   (priority 10)
  MX   svad.org.in   mx2.zoho.in  (priority 20)
  MX   svad.org.in   mx3.zoho.in  (priority 50)
  TXT  svad.org.in   v=spf1 include:zoho.in ~all
  TXT  svad.org.in   zoho-verification=zb80748988.zmverify.zoho.in
Then add svad.org.in (and www) as Custom Domains on the Pages project.

NOT RECOVERABLE FROM OUTSIDE
----------------------------
Anything that lived only on the old server: the admin panel, the database,
submitted queries, job applications and staff timesheets. Ask the old
website vendor (Webtel, webtel.in) for an export of that data if you need it.
