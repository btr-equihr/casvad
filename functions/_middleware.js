// Old svad.org.in addresses (ASP.NET, ending in .aspx, often with a query string) -> the static page that
// replaced them, with a permanent (301) redirect so bookmarks and search results keep working.
// The mapping mirrors build_full.py page_path(): firm pages have clean names, library pages keep their path
// with .aspx removed, and a query string becomes "-" + first 10 hex chars of md5(query).
// The old server ignored letter case, so the final lookup is case-insensitive via assets/data/paths.json.

const MAIN = {
  "/": "/", "/resource/home.aspx": "/", "/default.aspx": "/",
  "/resource/about_us.aspx": "/about-us", "/resource/partners.aspx": "/team",
  "/resource/clients.aspx": "/clients", "/resource/career.aspx": "/careers",
  "/resource/contact_us.aspx": "/contact-us", "/resource/disclaimer.aspx": "/disclaimer",
  "/newthemequerysheet.aspx": "/query",
  "/resource/services/audit_assurance.aspx": "/services/audit-assurance",
  "/resource/services/taxation.aspx": "/services/taxation",
  "/resource/services/accounting_bookkeeping.aspx": "/services/accounting-bookkeeping",
  "/resource/services/corporate_regulatory_compliances.aspx": "/services/corporate-regulatory-compliances",
  "/resource/services/labour_law_statutory_compliance.aspx": "/services/labour-law-statutory-compliance",
  "/resource/services/due_diligence_transaction_advisory.aspx": "/services/due-diligence-transaction-advisory",
  "/resource/services/advisory_consultancy.aspx": "/services/gst-international-tax-fema-advisory",
  "/resource/taxation.aspx": "/services/taxation",
  "/resource/audit_assurance.aspx": "/services/audit-assurance",
  "/resource/accounting_bookkeeping.aspx": "/services/accounting-bookkeeping",
  "/resource/corporate_regulatory_compliances.aspx": "/services/corporate-regulatory-compliances",
  "/resource/labour_law_statutory_compliance.aspx": "/services/labour-law-statutory-compliance",
  "/resource/login.aspx": "/", "/resource/timesheet.aspx": "/",
};

let PATHS = null; // lower-case clean path -> real clean path

async function paths(env, url) {
  if (!PATHS) {
    const r = await env.ASSETS.fetch(new URL("/assets/data/paths.json", url));
    PATHS = r.ok ? await r.json() : {};
  }
  return PATHS;
}

async function md5hex(s) {
  const buf = await crypto.subtle.digest("MD5", new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function cleanPath(path) {
  // same sanitising as page_path(): reserved characters -> "_", segments trimmed of spaces and dots
  path = path.replace(/^\/+/, "") || "index";
  if (path.endsWith("/")) path += "index";
  path = path.replace(/[<>:"|?*\\#%]/g, "_");
  path = path.split("/").map((seg) => seg.replace(/^[ .]+|[ .]+$/g, "") || "_").join("/");
  const slash = path.lastIndexOf("/"), dot = path.lastIndexOf(".");
  if (dot > slash + 1) path = path.slice(0, dot);
  return path;
}

async function notFound(context, url) {
  const r = await context.env.ASSETS.fetch(new URL("/404", url));
  return new Response(r.body, { status: 404, headers: { "content-type": "text/html; charset=utf-8" } });
}

export async function onRequest(context) {
  const url = new URL(context.request.url);
  let raw = url.pathname;
  if (!/\.(aspx|ashx|asmx)$/i.test(raw)) return context.next();
  let path;
  try { path = decodeURIComponent(raw); } catch { path = raw; }
  const query = url.search.replace(/^\?/, "");

  let target = !query && MAIN[path.toLowerCase()];
  if (!target) {
    let root = cleanPath(path);
    if (query) root += "-" + (await md5hex(query)).slice(0, 10);
    const map = await paths(context.env, url);
    target = map[("/" + root).toLowerCase()];
  }
  if (!target) return notFound(context, url);
  return Response.redirect(new URL(target, url).toString(), 301);
}
